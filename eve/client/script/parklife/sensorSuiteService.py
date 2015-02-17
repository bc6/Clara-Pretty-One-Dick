#Embedded file name: eve/client/script/parklife\sensorSuiteService.py
import math
from brennivin.threadutils import Signal
from carbon.common.lib import telemetry
from carbon.common.lib.const import SEC, MSEC
from carbon.common.script.sys import service
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.uianimations import animations
from eve.common.lib.appConst import AU
from sensorsuite.overlay.const import SWEEP_CYCLE_TIME, SWEEP_START_GRACE_TIME_SEC, SWEEP_START_GRACE_TIME, SUPPRESS_GFX_WARPING, SUPPRESS_GFX_NO_UI
from sensorsuite.overlay.gfxhandler import GfxHandler
from sensorsuite.overlay.sitetype import *
from sensorsuite.overlay.anomalies import AnomalyHandler
from sensorsuite.overlay.bookmarks import BookmarkHandler, CorpBookmarkHandler
from sensorsuite.overlay.spacesitecontroller import SpaceSiteController
from sensorsuite.overlay.staticsites import StaticSiteHandler
from sensorsuite.overlay.controllers.probescanner import ProbeScannerController
from sensorsuite.overlay.missions import MissionHandler
from sensorsuite.overlay.signatures import SignatureHandler
import uthread
import blue
import carbonui.const as uiconst
import log
import audio2
import trinity
import uiutil
from sensorsuite import common
from sensorsuite.error import InvalidClientStateError
SENSOR_SUITE_ENABLED = 'sensorSuiteEnabled'
MAX_MOUSEOVER_RANGE = 40.0
MAX_MOUSEOVER_RANGE_SQUARED = MAX_MOUSEOVER_RANGE ** 2
MAX_OVERLAPPING_RANGE_SQUARED = 900.0
MAX_RTPC_VALUE = 99
AUDIO_STATE_BY_DIFFICULTY = {common.SITE_DIFFICULTY_EASY: 'ui_scanner_state_difficulty_easy',
 common.SITE_DIFFICULTY_MEDIUM: 'ui_scanner_state_difficulty_medium',
 common.SITE_DIFFICULTY_HARD: 'ui_scanner_state_difficulty_hard'}
BRACKET_OVERLAP_DISTANCE = 8

class SensorSuiteService(service.Service):
    __guid__ = 'svc.sensorSuite'
    __notifyevents__ = ['OnSessionChanged',
     'OnSignalTrackerFullState',
     'OnSignalTrackerAnomalyUpdate',
     'OnSignalTrackerSignatureUpdate',
     'OnUpdateWindowPosition',
     'OnReleaseBallpark',
     'DoBallClear',
     'OnWarpStarted',
     'OnWarpFinished',
     'OnSystemScanDone',
     'OnSpecialFX',
     'OnShowUI',
     'OnHideUI',
     'OnRefreshBookmarks',
     'OnAgentMissionChanged']
    __dependencies__ = ['sceneManager',
     'michelle',
     'audio',
     'scanSvc',
     'viewState',
     'bookmarkSvc']
    __startupdependencies__ = []

    def Run(self, *args):
        service.Service.Run(self)
        self.isOverlayActive = True
        self.gfxHandler = GfxHandler(self, self.sceneManager, self.michelle)
        self.siteController = SpaceSiteController(self, self.michelle)
        self.siteController.AddSiteHandler(ANOMALY, AnomalyHandler())
        self.siteController.AddSiteHandler(SIGNATURE, SignatureHandler())
        self.siteController.AddSiteHandler(STATIC_SITE, StaticSiteHandler())
        self.siteController.AddSiteHandler(BOOKMARK, BookmarkHandler(self, self.bookmarkSvc))
        self.siteController.AddSiteHandler(CORP_BOOKMARK, CorpBookmarkHandler(self, self.bookmarkSvc))
        self.siteController.AddSiteHandler(MISSION, MissionHandler(self.bookmarkSvc))
        self.onSweepStartedObservers = Signal()
        self.onSweepEndedObservers = Signal()
        self.AddSiteObserver(self.OnSiteChanged)
        self.Initialize()

    def IsSweepDone(self):
        return self.systemReadyTime and not self.sensorSweepActive

    def IsSolarSystemReady(self):
        return self.systemReadyTime is not None

    def AddSiteObserver(self, onSiteChangedCallback):
        self.siteController.AddSiteObserver(onSiteChangedCallback)

    def RemoveSiteObserver(self, onSiteChangedCallback):
        self.siteController.RemoveSiteObserver(onSiteChangedCallback)

    def AddSweepObserver(self, onSweepStartedObserver, onSweepEndedObserver):
        self.LogInfo('AddSweepObserver', onSweepStartedObserver, onSweepEndedObserver)
        if self.onSweepStartedObservers:
            self.onSweepStartedObservers.connect(onSweepStartedObserver)
            if self.sweepStartedData is not None:
                uthread.new(onSweepStartedObserver, *self.sweepStartedData)
        if onSweepEndedObserver:
            self.onSweepEndedObservers.connect(onSweepEndedObserver)

    def RemoveSweepObserver(self, onSweepStartedObserver, onSweepEndedObserver):
        try:
            self.onSweepStartedObservers.disconnect(onSweepStartedObserver)
        except ValueError:
            pass

        try:
            self.onSweepEndedObservers.disconnect(onSweepEndedObserver)
        except ValueError:
            pass

    def Initialize(self):
        self.siteController.Clear()
        self.probeScannerController = ProbeScannerController(self.scanSvc, self.michelle, self.siteController)
        self.locatorFadeInTimeSec = 0.25
        self.doMouseTrackingUpdates = False
        self.systemReadyTime = None
        self.sitesUnderCursor = set()
        leftPush, rightPush = uicore.layer.sidePanels.GetSideOffset()
        self.OnUpdateWindowPosition(leftPush, rightPush)
        self.sensorSweepActive = False
        self.sweepStartedData = None

    def OnSiteChanged(self, siteData):
        if siteData.GetSiteType() is SIGNATURE:
            if not self.siteController.IsSiteVisible(siteData) or siteData.IsAccurate():
                self.gfxHandler.DelGfxResultFromScene(siteData.targetID)

    def UpdateScanner(self, removedSites):
        targetIDs = []
        for siteData in removedSites:
            if siteData.GetSiteType() in (ANOMALY, SIGNATURE):
                targetIDs.append(siteData.targetID)

        if targetIDs:
            self.scanSvc.ClearResults(*targetIDs)

    def InjectScannerResults(self, siteType):
        sitesById = self.siteController.siteMaps.GetSiteMapByKey(siteType)
        self.probeScannerController.InjectSiteScanResults(sitesById.itervalues())

    def OnSpecialFX(self, shipID, moduleID, moduleTypeID, targetID, otherTypeID, guid, *args, **kw):
        if shipID == session.shipid:
            if guid is not None and 'effects.JumpOut' in guid:
                self.LogInfo('Jumping out, hiding the overlay')
                self._Hide()

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid' in change:
            self.Reset()
            oldSolarSystemID, newSolarSystemID = change['solarsystemid']
            if newSolarSystemID is not None:
                self.Initialize()
                self._SetOverlayActive(settings.char.ui.Get(SENSOR_SUITE_ENABLED, True))
                self.LogInfo('Entered new system', newSolarSystemID)
                sm.RemoteSvc('scanMgr').SignalTrackerRegister()
                for siteType in (BOOKMARK, CORP_BOOKMARK, MISSION):
                    self.siteController.GetSiteHandler(siteType).LoadSites(newSolarSystemID)

    def OnReleaseBallpark(self):
        """Lets make sure we are not keeping stuff alive when the ballpark gets cleared"""
        self.Reset()

    def DoBallClear(self, _):
        self.LogInfo('Ballpark is ready so we start the sweep timer')
        self.systemReadyTime = blue.os.GetSimTime()
        self.StartSensorSweep()

    def Reset(self):
        self.siteController.ClearFromBallpark()
        self.siteController.Clear()
        uicore.layer.sensorSuite.Flush()
        self.gfxHandler.DeleteAllGfxResults()
        self.gfxHandler.StopGfxSwipe()
        self.gfxHandler.StopSwipeThread()

    def IsOverlayActive(self):
        return self.isOverlayActive

    def ToggleOverlay(self):
        uthread.Lock('sensorSuite::ToggleOverlay')
        try:
            if self.IsOverlayActive():
                self.DisableSensorOverlay()
            else:
                self.EnableSensorOverlay()
        finally:
            uthread.UnLock('sensorSuite::ToggleOverlay')

    def DisableSensorOverlay(self):
        if self.IsOverlayActive():
            self._SetOverlayActive(False)
            if not self.sensorSweepActive:
                self._Hide()

    def EnableSensorOverlay(self):
        if not self.IsOverlayActive():
            self._SetOverlayActive(True)
            if not self.sensorSweepActive:
                self._Show()

    def _SetOverlayActive(self, isActive):
        self.isOverlayActive = isActive
        settings.char.ui.Set(SENSOR_SUITE_ENABLED, isActive)

    def _Show(self):
        self.LogInfo('Showing overlay')
        self.gfxHandler.WaitForDeletionToComplete()
        try:
            if not self.sensorSweepActive:
                self.UpdateVisibleSites()
                self.audio.SendUIEvent('ui_scanner_stop')
                self.EnableMouseTracking()
                self.gfxHandler.StartGfxSwipeThread()
                self.gfxHandler.AddGfxResults()
        except InvalidClientStateError:
            pass

    def _Hide(self):
        self.LogInfo('Hiding overlay')
        self.gfxHandler.StopGfxSwipe()
        self.UpdateVisibleSites()
        self.gfxHandler.DeleteAllGfxResults()
        self.audio.SendUIEvent('ui_scanner_stop')
        self.doMouseTrackingUpdates = False

    def EnableMouseTracking(self):
        if not self.doMouseTrackingUpdates:
            self.doMouseTrackingUpdates = True
            uthread.new(self.UpdateMouseTracking).context = 'sensorSuite::UpdateMouseTracking'

    def StartSensorSweep(self):
        uthread.new(self._DoSystemEnterScan)

    def TryFadeOutBracketAndReturnCurveSet(self, curveSet, points, siteData, totalDuration):
        try:
            locatorData = self.siteController.spaceLocations.GetBySiteID(siteData.siteID)
            curveSet = animations.FadeTo(locatorData.bracket, startVal=0.0, endVal=1.0, duration=totalDuration, curveType=points, curveSet=curveSet)
        except KeyError:
            pass

        return curveSet

    def _DoSystemEnterScan(self):
        self.LogInfo('_DoSystemEnterScan entered')
        if session.solarsystemid is None:
            return
        self.sensorSweepActive = True
        try:
            self.CreateResults()
            viewAngleInPlane = self.gfxHandler.GetViewAngleInPlane()
        except InvalidClientStateError:
            self.sensorSweepActive = False
            return

        ballpark = self.michelle.GetBallpark()
        if ballpark is None:
            return
        myBall = ballpark.GetBall(ballpark.ego)
        mx, mz = myBall.x, myBall.z
        curveSet = None
        sitesOrdered = []
        pi2 = math.pi * 2
        sweepCycleTimeSec = float(SWEEP_CYCLE_TIME) / SEC
        self.LogInfo('Sensor sweep stating from angle', viewAngleInPlane)
        for siteData in self.siteController.GetVisibleSites():
            self.LogInfo('checking site', siteData.siteID)
            if IsSiteInstantlyAccessible(siteData):
                sitesOrdered.append((0, siteData))
                continue
            x, y, z = siteData.position
            dx, dz = x - mx, z - mz
            angle = math.atan2(-dz, dx) - viewAngleInPlane
            angle %= pi2
            ratioOfCircle = angle / pi2
            delay = SWEEP_START_GRACE_TIME_SEC + sweepCycleTimeSec * ratioOfCircle
            sitesOrdered.append((delay, siteData))

        sitesOrdered.sort()
        for delay, siteData in sitesOrdered:
            points, totalDuration = self.GetLocationFlashCurve(delay)
            curveSet = self.TryFadeOutBracketAndReturnCurveSet(curveSet, points, siteData, totalDuration)

        self.gfxHandler.StartGfxSwipeThread(viewAngleInPlane=viewAngleInPlane)
        self.audio.SendUIEvent('ui_scanner_start')
        uthread.new(self.PlayResultEffects, sitesOrdered)
        self.LogInfo('Sweep started observers notified')
        self.sweepStartedData = (self.systemReadyTime,
         sweepCycleTimeSec,
         viewAngleInPlane,
         sitesOrdered,
         SWEEP_START_GRACE_TIME_SEC)
        self.onSweepStartedObservers.emit(*self.sweepStartedData)

    @telemetry.ZONE_METHOD
    def ShowSiteDuringSweep(self, ballpark, locatorData, scene, siteData, sleepTimeMSec, soundLocators, vectorCurve):
        audio = audio2.AudEmitter('sensor_overlay_site_%s' % str(siteData.siteID))
        obs = trinity.TriObserverLocal()
        obs.front = (0.0, -1.0, 0.0)
        obs.observer = audio
        vectorSequencer = trinity.TriVectorSequencer()
        vectorSequencer.operator = trinity.TRIOP_MULTIPLY
        vectorSequencer.functions.append(locatorData.ballRef())
        vectorSequencer.functions.append(vectorCurve)
        tr = trinity.EveRootTransform()
        tr.name = 'sensorSuiteSoundLocator_%s' % str(siteData.siteID)
        tr.translationCurve = vectorSequencer
        tr.observers.append(obs)
        scene.objects.append(tr)
        soundLocators.append(tr)
        blue.pyos.synchro.SleepSim(sleepTimeMSec)
        if siteData.GetSiteType() == ANOMALY:
            audio.SendEvent('ui_scanner_result_anomaly')
        elif siteData.GetSiteType() == SIGNATURE:
            audio.SendEvent('ui_scanner_result_signature')
            myBall = ballpark.GetBall(ballpark.ego)
            if myBall is None:
                raise InvalidClientStateError("We don't have an ego ball anymore")
            myPos = (myBall.x, myBall.y, myBall.z)
            self.gfxHandler.AddGfxResult(siteData, myPos)
        locatorData.bracket.DoEntryAnimation(enable=False)
        locatorData.bracket.state = uiconst.UI_DISABLED

    @telemetry.ZONE_METHOD
    def PlayResultEffects(self, sitesOrdered):
        """
        This takes the calculated delay times and the result data and sequences the result sound effectStates
        Different effects can be triggered based on the siteData if needed.
        """
        self.LogInfo('PlayResultEffects')
        ballpark = self.michelle.GetBallpark()
        scene = self.sceneManager.GetRegisteredScene('default')
        soundLocators = []
        invAU = 1.0 / AU
        vectorCurve = trinity.TriVectorCurve()
        vectorCurve.value = (invAU, invAU, invAU)
        self.EnableMouseTracking()
        try:
            startTimeMSec = (self.systemReadyTime + SWEEP_START_GRACE_TIME) / MSEC
            lastPlayTimeMSec = startTimeMSec
            for delaySec, siteData in sitesOrdered:
                locatorData = self.siteController.spaceLocations.GetBySiteID(siteData.siteID)
                if IsSiteInstantlyAccessible(siteData):
                    locatorData.bracket.state = uiconst.UI_NORMAL
                    locatorData.bracket.DoEntryAnimation(enable=True)
                    continue
                playTimeMSec = startTimeMSec + delaySec * 1000
                sleepTimeMSec = playTimeMSec - lastPlayTimeMSec
                lastPlayTimeMSec = playTimeMSec
                self.ShowSiteDuringSweep(ballpark, locatorData, scene, siteData, sleepTimeMSec, soundLocators, vectorCurve)

            currentTimeMSec = blue.os.GetSimTime() / MSEC
            endTimeMSec = startTimeMSec + (SWEEP_CYCLE_TIME + SEC) / MSEC
            timeLeftMSec = endTimeMSec - currentTimeMSec
            if timeLeftMSec > 0:
                blue.pyos.synchro.SleepSim(timeLeftMSec)
            self.audio.SendUIEvent('ui_scanner_stop')
            self.sensorSweepActive = False
            if not self.IsOverlayActive():
                self._Hide()
            else:
                for locatorData in self.siteController.spaceLocations.IterLocations():
                    if not IsSiteInstantlyAccessible(locatorData.siteData):
                        locatorData.bracket.DoEnableAnimation()
                        locatorData.bracket.state = uiconst.UI_NORMAL

            blue.pyos.synchro.SleepSim(1000)
            self.DoScanEnded(sitesOrdered)
        except (InvalidClientStateError, KeyError):
            pass
        finally:
            self.sensorSweepActive = False
            if scene is not None:
                for tr in soundLocators:
                    if tr in scene.objects:
                        scene.objects.remove(tr)

            self.audio.SendUIEvent('ui_scanner_stop')
            self.onSweepEndedObservers.emit()

        self.UpdateVisibleSites()

    def DoScanEnded(self, sitesOrdered):
        self.LogInfo('DoScanEnded')
        if len(sitesOrdered) > 0:
            self.audio.SendUIEvent('ui_scanner_result_positive')
        else:
            self.audio.SendUIEvent('ui_scanner_result_negative')

    def CreateResults(self):
        self.LogInfo('CreateResults')
        self.gfxHandler.WaitForSceneReady()
        for siteData in self.siteController.GetVisibleSites():
            self.siteController.AddSiteToSpace(siteData, animate=False)

    def GetLocationFlashCurve(self, delay):
        totalDuration = delay + self.locatorFadeInTimeSec
        points = []
        totalTime = 0
        for keyDuration, keyValue in ((delay, 0.0), (self.locatorFadeInTimeSec, 1.0)):
            totalTime += keyDuration
            points.append((totalTime / totalDuration, keyValue))

        return (points, totalDuration)

    def GetBracketByBallID(self, ballID):
        return self.siteController.spaceLocations.GetBracketByBallID(ballID)

    def GetBracketBySiteID(self, siteID):
        return self.siteController.spaceLocations.GetBracketBySiteID(siteID)

    def OnRefreshBookmarks(self):
        self.LogInfo('OnRefreshBookmarks')
        for siteType in (BOOKMARK, CORP_BOOKMARK):
            self.siteController.GetSiteHandler(siteType).UpdateSites(session.solarsystemid)

    def OnAgentMissionChanged(self, *args, **kwargs):
        self.siteController.GetSiteHandler(MISSION).UpdateSites(session.solarsystemid)

    def OnSignalTrackerFullState(self, solarSystemID, fullState):
        self.LogInfo('OnSignalTrackerFullState', solarSystemID, fullState)
        anomalies, signatures, staticSites = fullState
        for siteType, rawSites in ((ANOMALY, anomalies), (SIGNATURE, signatures), (STATIC_SITE, staticSites)):
            self.siteController.GetSiteHandler(siteType).ProcessSiteUpdate(rawSites, set())

        self.probeScannerController.InjectSiteScanResults(self.siteController.siteMaps.IterSitesByKeys(ANOMALY, SIGNATURE))
        self.gfxHandler.AddGfxResults()

    def OnSignalTrackerAnomalyUpdate(self, solarSystemID, addedAnomalies, removedAnomalies):
        self.LogInfo('OnSignalTrackerAnomalyUpdate', solarSystemID, addedAnomalies, removedAnomalies)
        self.siteController.GetSiteHandler(ANOMALY).ProcessSiteUpdate(addedAnomalies, removedAnomalies)

    def OnSignalTrackerSignatureUpdate(self, solarSystemID, addedSignatures, removedSignatures):
        self.LogInfo('OnSignalTrackerSignatureUpdate', solarSystemID, addedSignatures, removedSignatures)
        self.siteController.GetSiteHandler(SIGNATURE).ProcessSiteUpdate(addedSignatures, removedSignatures)
        self.gfxHandler.AddGfxResults()

    def OnUpdateWindowPosition(self, leftPush, rightPush):
        """The neocom may have updated and we need to correct for the layer offset"""
        uicore.layer.sensorsuite.padLeft = -leftPush
        uicore.layer.sensorsuite.padRight = -rightPush

    def IsMouseInSpaceView(self):
        """Check if the space view is active and that mouse is actually over view related objects"""
        if self.viewState.IsViewActive('inflight'):
            mouseOver = uicore.uilib.mouseOver
            for uiContainer in (uicore.layer.inflight, uicore.layer.sensorsuite, uicore.layer.bracket):
                if mouseOver is uiContainer or uiutil.IsUnder(mouseOver, uiContainer):
                    return True

        return False

    @telemetry.ZONE_METHOD
    def UpdateMouseHoverSound(self, activeBracket, bestProximity, closestBracket, lastSoundStrength):
        soundStrength = bestProximity or 0
        if closestBracket is not None:
            if soundStrength != 0 or lastSoundStrength != 0:
                if lastSoundStrength == 0 or activeBracket != closestBracket:
                    signalStrength = MAX_RTPC_VALUE
                    difficulty = common.SITE_DIFFICULTY_EASY
                    self.audio.SendUIEvent(closestBracket.data.hoverSoundEvent)
                    self.audio.SetGlobalRTPC('scanner_signal_strength', min(signalStrength, MAX_RTPC_VALUE))
                    self.audio.SendUIEvent(AUDIO_STATE_BY_DIFFICULTY[difficulty])
                    self.audio.SendUIEvent('ui_scanner_mouseover')
                    activeBracket = closestBracket
                self.audio.SetGlobalRTPC('scanner_mouseover', soundStrength)
        elif soundStrength == 0 and lastSoundStrength > 0:
            self.DisableMouseOverSound()
            activeBracket = None
        lastSoundStrength = soundStrength
        return (activeBracket, lastSoundStrength)

    @telemetry.ZONE_METHOD
    def UpdateMouseTracking(self):
        self.LogInfo('Mouse tracking update thread started')
        lastSoundStrength = 0.0
        activeBracket = None
        self.sitesUnderCursor = set()
        self.audio.SetGlobalRTPC('scanner_mouseover', 0)
        while self.doMouseTrackingUpdates:
            try:
                if not self.IsMouseInSpaceView():
                    if activeBracket is not None:
                        self.DisableMouseOverSound()
                        activeBracket = None
                        lastSoundStrength = 0.0
                    continue
                desktopWidth = uicore.desktop.width
                desktopHeight = uicore.desktop.height
                mouseX = uicore.uilib.x
                mouseY = uicore.uilib.y
                self.currentOverlapCoordinates = (mouseX, mouseY)
                closestBracket = None
                bestProximity = None
                for data in self.siteController.spaceLocations.IterLocations():
                    self.sitesUnderCursor.discard(data.siteData)
                    bracket = data.bracket
                    if bracket is None or bracket.destroyed:
                        continue
                    if bracket.state == uiconst.UI_DISABLED:
                        continue
                    centerX = bracket.left + bracket.width / 2
                    centerY = bracket.top + bracket.height / 2
                    if centerX < 0:
                        continue
                    if centerX > desktopWidth:
                        continue
                    if centerY < 0:
                        continue
                    if centerY > desktopHeight:
                        continue
                    if mouseX < centerX - MAX_MOUSEOVER_RANGE:
                        continue
                    if mouseX > centerX + MAX_MOUSEOVER_RANGE:
                        continue
                    if mouseY < centerY - MAX_MOUSEOVER_RANGE:
                        continue
                    if mouseY > centerY + MAX_MOUSEOVER_RANGE:
                        continue
                    dx = centerX - mouseX
                    dy = centerY - mouseY
                    if -BRACKET_OVERLAP_DISTANCE <= dx <= BRACKET_OVERLAP_DISTANCE and -BRACKET_OVERLAP_DISTANCE <= dy <= BRACKET_OVERLAP_DISTANCE:
                        self.sitesUnderCursor.add(data.siteData)
                    if data.siteData.hoverSoundEvent is None:
                        continue
                    distanceSquared = dx * dx + dy * dy
                    if distanceSquared >= MAX_MOUSEOVER_RANGE_SQUARED:
                        continue
                    proximity = MAX_RTPC_VALUE - distanceSquared / MAX_MOUSEOVER_RANGE_SQUARED * MAX_RTPC_VALUE
                    if closestBracket is not None:
                        if proximity < bestProximity:
                            closestBracket = bracket
                            bestProximity = proximity
                    else:
                        closestBracket = bracket
                        bestProximity = proximity

                activeBracket, lastSoundStrength = self.UpdateMouseHoverSound(activeBracket, bestProximity, closestBracket, lastSoundStrength)
            except ValueError:
                pass
            except Exception:
                log.LogException('The sound update loop errored out')
            finally:
                blue.pyos.synchro.SleepWallclock(25)

        if activeBracket is not None:
            self.DisableMouseOverSound()
        self.LogInfo('Mouse tracking update thread ended')

    def DisableMouseOverSound(self):
        self.audio.SendUIEvent('ui_scanner_mouseover_stop')
        self.audio.SetGlobalRTPC('scanner_mouseover', 0)

    def OnWarpStarted(self):
        self.LogInfo('OnWarpStarted hiding the sweep gfx')
        self.gfxHandler.DisableGfx(SUPPRESS_GFX_WARPING)

    def OnWarpFinished(self):
        self.LogInfo('OnWarpFinished showing the sweep gfx')
        self.gfxHandler.EnableGfx(SUPPRESS_GFX_WARPING)

    def OnShowUI(self):
        self.LogInfo('OnShowUI showing the sweep gfx')
        uicore.layer.sensorsuite.display = True
        self.gfxHandler.EnableGfx(SUPPRESS_GFX_NO_UI)

    def OnHideUI(self):
        self.LogInfo('OnHideUI hiding the sweep gfx')
        uicore.layer.sensorsuite.display = False
        self.gfxHandler.DisableGfx(SUPPRESS_GFX_NO_UI)

    def OnSystemScanDone(self):
        self.probeScannerController.UpdateProbeResultBrackets()

    def GetOverlappingSites(self):
        overlappingBrackets = []
        for siteData in self.sitesUnderCursor:
            bracket = self.siteController.spaceLocations.GetBracketBySiteID(siteData.siteID)
            if bracket:
                overlappingBrackets.append(bracket)

        return overlappingBrackets

    def GetCosmicAnomalyItemIDFromTargetID(self, targetID):
        return self.probeScannerController.GetCosmicAnomalyItemIDFromTargetID(targetID)

    def SetSiteFilter(self, siteType, enabled):
        handler = self.siteController.GetSiteHandler(siteType)
        handler.SetFilterEnabled(enabled)
        self.UpdateVisibleSites()

    def UpdateVisibleSites(self):
        setattr(self, 'updateVisibleSitesTimerThread', AutoTimer(200, self._UpdateVisibleSites))

    @telemetry.ZONE_METHOD
    def _UpdateVisibleSites(self):
        self.LogInfo('UpdateVisibleSites')
        try:
            if session.solarsystemid is None:
                return
            if not self.IsSolarSystemReady():
                return
            self.siteController.UpdateSiteVisibility()
            self.gfxHandler.AddGfxResults()
        finally:
            self.updateVisibleSitesTimerThread = None
