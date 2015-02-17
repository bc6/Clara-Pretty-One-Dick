#Embedded file name: sensorsuite/overlay\gfxhandler.py
import math
from carbon.common.lib.const import SEC, MSEC
from sensorsuite.overlay.const import SWEEP_START_GRACE_TIME, SWEEP_CYCLE_TIME, SUPPRESS_GFX_WARPING
import uthread
import logging
from sensorsuite.error import InvalidClientStateError
from sensorsuite.overlay.sitetype import SIGNATURE
import geo2
import blue
logger = logging.getLogger(__name__)

class GfxHandler:

    def __init__(self, sensorSuiteService, sceneManager, michelle):
        self.sensorSuiteService = sensorSuiteService
        self.sceneManager = sceneManager
        self.michelle = michelle
        self.gfxSensorSwipe = None
        self.gfxActiveSensorResults = {}
        self.suppressGfxReasons = set()
        self.gfxSwipeThread = None
        self._gfxResultDeleteCounter = 0

    def Reset(self):
        self.gfxSensorSwipe = None
        self.gfxActiveSensorResults = {}
        self.suppressGfxReasons.discard(SUPPRESS_GFX_WARPING)
        self.gfxSwipeThread = None
        self._gfxResultDeleteCounter = 0

    def DelGfxResultFromScene(self, uniqueName):
        if uniqueName not in self.gfxActiveSensorResults:
            return
        self._gfxResultDeleteCounter += 1
        uthread.new(self._DelGfxResultFromScene, uniqueName)

    def _DelGfxResultFromScene(self, uniqueName):
        try:
            if uniqueName not in self.gfxActiveSensorResults:
                return
            delMe = self.gfxActiveSensorResults[uniqueName]
            fadeOutTime = 0.25
            for cs in delMe.curveSets:
                if cs.name == 'Play':
                    fadeOutTime = cs.GetMaxCurveDuration()
                    cs.scale = -1.0
                    cs.PlayFrom(fadeOutTime)
                    break

            blue.pyos.synchro.SleepWallclock(fadeOutTime * 1000)
            if uniqueName not in self.gfxActiveSensorResults:
                return
            delMe = self.gfxActiveSensorResults.pop(uniqueName)
            scene = self.sceneManager.GetRegisteredScene('default')
            if scene is not None:
                if delMe in scene.objects:
                    scene.objects.remove(delMe)
        finally:
            self._gfxResultDeleteCounter -= 1

    def DeleteAllGfxResults(self):
        fxToDel = self.gfxActiveSensorResults.keys()
        for fxName in fxToDel:
            self.DelGfxResultFromScene(fxName)

    def WaitForDeletionToComplete(self):
        timeout = blue.os.GetWallclockTime() + SEC
        while self._gfxResultDeleteCounter > 0 and blue.os.GetWallclockTime() < timeout:
            blue.synchro.SleepWallclock(100)

    def StopGfxSwipe(self):
        if self.gfxSensorSwipe is None:
            return
        uthread.new(self._StopGfxSwipe)

    def _StopGfxSwipe(self):
        if self.gfxSensorSwipe is None:
            return
        fadeOutTime = 0.25
        for cs in self.gfxSensorSwipe.curveSets:
            if cs.name == 'Play':
                fadeOutTime = cs.GetMaxCurveDuration()
                cs.scale = -1.0
                cs.PlayFrom(fadeOutTime)
                break

        blue.pyos.synchro.SleepWallclock(fadeOutTime * 1000)
        if self.gfxSensorSwipe is None:
            return
        self.gfxSensorSwipe.display = False
        scene = self.sceneManager.GetRegisteredScene('default')
        if scene is not None:
            if self.gfxSensorSwipe in scene.objects:
                scene.objects.fremove(self.gfxSensorSwipe)
        self.gfxSensorSwipe = None

    def StopSwipeThread(self):
        if self.gfxSwipeThread is not None:
            self.gfxSwipeThread.kill()
            self.gfxSwipeThread = None

    def StartGfxSwipeThread(self, viewAngleInPlane = None):
        if viewAngleInPlane is None:
            viewAngleInPlane = self.GetViewAngleInPlane()
        if self.gfxSwipeThread is not None:
            return
        self.gfxSwipeThread = uthread.worker('sensorSuite::_GfxSwipeThread', self._GfxSwipeThread, viewAngleInPlane)

    def _GfxSwipeThread(self, viewAngleInPlane):
        """
        A thread that start and stops the sweep effect 1 every 5 cycles
        viewAngleInPlane: The initial view angle
        """
        try:
            blue.pyos.synchro.SleepWallclock(SWEEP_START_GRACE_TIME / MSEC)
            while self.sensorSuiteService.IsOverlayActive() or self.sensorSuiteService.sensorSweepActive:
                logger.debug('triggering a gfx swipe')
                self.StartGfxSwipe(viewAngleInPlane)
                blue.pyos.synchro.SleepWallclock(SWEEP_CYCLE_TIME / MSEC)
                self.StopGfxSwipe()
                blue.pyos.synchro.SleepWallclock(4 * SWEEP_CYCLE_TIME / MSEC)
                viewAngleInPlane = self.GetViewAngleInPlane()

        except InvalidClientStateError:
            pass
        finally:
            logger.debug('exiting gfx swipe thread')
            self.gfxSwipeThread = None

    def StartGfxSwipe(self, viewAngleInPlane):
        if self.suppressGfxReasons:
            return
        if self.gfxSensorSwipe is None:
            self.gfxSensorSwipe = blue.recycler.RecycleOrLoad('res:/fisfx/scanner/background.red')
        adjustedViewAngleInPlane = viewAngleInPlane + math.pi
        for child in self.gfxSensorSwipe.children:
            if child.mesh is not None:
                for area in list(child.mesh.transparentAreas) + list(child.mesh.additiveAreas):
                    if area.effect is not None:
                        for param in area.effect.parameters:
                            if param.name == 'SwipeData':
                                param.value = (param.value[0],
                                 adjustedViewAngleInPlane / (2.0 * math.pi),
                                 param.value[2],
                                 param.value[3])

        self.gfxSensorSwipe.display = True
        scene = self.sceneManager.GetRegisteredScene('default')
        if scene is not None:
            if self.gfxSensorSwipe not in scene.objects:
                scene.objects.append(self.gfxSensorSwipe)
            for cs in self.gfxSensorSwipe.curveSets:
                if cs.name == 'Rotater':
                    for c in cs.curves:
                        if c.name == 'Speed':
                            c.length = float(SWEEP_CYCLE_TIME) / SEC

                    cs.scale = 1.0
                    cs.Play()
                elif cs.name == 'Play':
                    cs.scale = 1.0
                    cs.Play()

    def AddGfxResultToScene(self, uniqueName, direction, size):
        gfxSensorResult = blue.recycler.RecycleOrLoad('res:/fisfx/scanner/result.red')
        size = min(size, 0.4)
        gfxSensorResult.centerNormal = direction
        gfxSensorResult.pinRadius = size
        gfxSensorResult.pinMaxRadius = size
        gfxSensorResult.display = True
        for cs in gfxSensorResult.curveSets:
            if cs.name == 'Play':
                cs.scale = 1.0
                cs.Play()

        self.gfxActiveSensorResults[uniqueName] = gfxSensorResult
        scene = self.sceneManager.GetRegisteredScene('default')
        if scene is not None:
            scene.objects.append(gfxSensorResult)

    def GetViewAngleInPlane(self):
        camera = self.sceneManager.GetRegisteredCamera('default')
        if camera is None:
            raise InvalidClientStateError('No camera found')
        viewAngleInPlane = math.atan2(camera.viewVec[0], camera.viewVec[2])
        return viewAngleInPlane

    def DisableGfx(self, reason):
        self.suppressGfxReasons.add(reason)
        self.StopGfxSwipe()
        self.DeleteAllGfxResults()

    def AddGfxResult(self, siteData, myPos):
        if self.suppressGfxReasons:
            return
        if not self.sensorSuiteService.siteController.IsSiteVisible(siteData):
            return
        if siteData.signalStrength >= 1.0:
            return
        if siteData.targetID in self.gfxActiveSensorResults:
            return
        direction = geo2.Vec3SubtractD(siteData.position, myPos)
        distToSite = geo2.Vec3LengthD(direction)
        deviation = siteData.deviation * 0.5
        a = min(distToSite, deviation)
        b = max(distToSite, deviation)
        tanA = a / b
        angle = math.atan(tanA)
        normalizedDir = geo2.Vec3NormalizeD(direction)
        self.AddGfxResultToScene(siteData.targetID, normalizedDir, angle)

    def AddGfxResults(self):
        logger.debug('AddGfxResults')
        if self.suppressGfxReasons:
            return
        if not self.sensorSuiteService.IsOverlayActive():
            self.DeleteAllGfxResults()
            return
        sigHandler = self.sensorSuiteService.siteController.GetSiteHandler(SIGNATURE)
        if not sigHandler.IsFilterEnabled():
            return
        ballpark = self.michelle.GetBallpark()
        if ballpark is None:
            return
        myBall = ballpark.GetBall(ballpark.ego)
        if myBall is None:
            return
        for siteData in self.sensorSuiteService.siteController.siteMaps.IterSitesByKey(SIGNATURE):
            if not sigHandler.IsVisible(siteData):
                continue
            self.AddGfxResult(siteData, (myBall.x, myBall.y, myBall.z))

    def EnableGfx(self, reason):
        self.suppressGfxReasons.discard(reason)
        if not self.sensorSuiteService.IsOverlayActive():
            return
        if self.sensorSuiteService.sensorSweepActive:
            return
        if self.suppressGfxReasons:
            return
        try:
            self.StartGfxSwipeThread()
            self.AddGfxResults()
        except InvalidClientStateError:
            pass

    def WaitForSceneReady(self):
        scene = self.sceneManager.GetRegisteredScene('default')
        startTime = blue.os.GetSimTime()
        while scene is None and startTime + SEC * 15 < blue.os.GetSimTime():
            blue.pyos.synchro.SleepWallclock(250)
            if session.solarsystemid is None:
                raise InvalidClientStateError('Solarsystemid is None in session')
            scene = self.sceneManager.GetRegisteredScene('default')

        if scene is None:
            raise InvalidClientStateError('Failed to find the default space scene')
