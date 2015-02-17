#Embedded file name: eve/client/script/parklife\scanSvc.py
"""
Service wrapping interaction to exporation scan probes implemented as part of TEX Wormole project
"""
import service
import util
import blue
import functools
from eve.client.script.ui.inflight.scanner import Scanner
import localization
import uthread
import carbonui.const as uiconst
import uiutil
import mapcommon
import probescanning.probeTracker as probeTracker
import probescanning.scanHandler as scanHandler
import probescanning.resultFilter as resultFilter
import probescanning.customFormations as customFormations
import geo2
from probescanning.util import IsExplorationSite
RECONNECT_DELAY_MINUTES = 1

def UserErrorIfScanning(action, *args, **kwargs):
    """
    decorator checking if we are curerntly scanning and raising a UserError if so
    """

    @functools.wraps(action)
    def wrapper(*args, **kwargs):
        if sm.StartService('scanSvc').IsScanning():
            raise UserError('ScanInProgressGeneric')
        return action(*args, **kwargs)

    return wrapper


class ScanSvc(service.Service):
    """
    Service wrapping client interaction with conversation brains possesed by some entities.
    Mostly interacts with brainMgr and htmlTemlateSvc.
    """
    __guid__ = 'svc.scanSvc'
    __servicename__ = 'svc.scanSvc'
    __displayname__ = 'Scanner Probe Service'
    __notifyevents__ = ['OnSessionChanged',
     'OnSystemScanStarted',
     'OnSystemScanStopped',
     'OnProbeWarpStart',
     'OnProbesIdle',
     'OnProbeStateChanged',
     'OnNewProbe',
     'OnRemoveProbe',
     'OnScannerInfoRemoved',
     'DoSimClockRebase']
    __dependencies__ = ['michelle', 'godma', 'audio']
    __uthreads__ = []
    __exportedcalls__ = {'SetProbeDestination': [service.ROLE_ANY],
     'SetProbeRangeStep': [service.ROLE_ANY],
     'GetProbeData': [service.ROLE_ANY],
     'GetScanResults': [service.ROLE_ANY],
     'RequestScans': [service.ROLE_ANY],
     'RecoverProbe': [service.ROLE_ANY],
     'RecoverProbes': [service.ROLE_ANY],
     'ReconnectToLostProbes': [service.ROLE_ANY],
     'DestroyProbe': [service.ROLE_ANY],
     'GetScanRangeStepsByTypeID': [service.ROLE_ANY]}

    def __init__(self):
        service.Service.__init__(self)

    def Run(self, ms):
        self.lastResults = None
        self.probeLabels = {}
        self.lastReconnection = None
        self.lastRangeStepUsed = 5
        self.remoteObject = None
        self.probeTracker = probeTracker.ProbeTracker(self, sm.ScatterEvent)
        self.resultFilter = resultFilter.ResultFilter(settings.user.ui.Get, settings.user.ui.Set, localization.GetByLabel)
        self.scanHandler = scanHandler.ScanHandler(self, sm.ScatterEvent, self.resultFilter)
        self.scanGroups = {}
        self.scanGroups[const.probeScanGroupAnomalies] = localization.GetByLabel('UI/Inflight/Scanner/CosmicAnomaly')
        self.scanGroups[const.probeScanGroupSignatures] = localization.GetByLabel('UI/Inflight/Scanner/CosmicSignature')
        self.scanGroups[const.probeScanGroupShips] = localization.GetByLabel('UI/Inflight/Scanner/Ship')
        self.scanGroups[const.probeScanGroupStructures] = localization.GetByLabel('UI/Inflight/Scanner/Structure')
        self.scanGroups[const.probeScanGroupDronesAndProbes] = localization.GetByLabel('UI/Inflight/Scanner/DroneAndProbe')

    def GetScanMan(self):
        if self.remoteObject is None:
            self.remoteObject = sm.RemoteSvc('scanMgr').GetSystemScanMgr()
        return self.remoteObject

    def OnNewProbe(self, probe):
        """
        Event handler for new probes launched. 
        Notification comes from park. New probes are set to IDLE and notification is sent to 
        scanner window if it has been created so it can add graphics and stuff.
        """
        self.probeTracker.AddProbe(probe)

    def OnRemoveProbe(self, probeID):
        """
        Event handler for probes removed. 
        Probe is removed from local cache.
        A second local event is scattered to notify the scanner window if active.
        """
        self.probeTracker.RemoveProbe(probeID)

    def DoSimClockRebase(self, times):
        """ Event handler that gets called when the simulation time base changes."""
        if not self.lastReconnection:
            return
        oldSimTime, newSimTime = times
        self.lastReconnection += newSimTime - oldSimTime

    def GetActiveProbes(self):
        """ Returnes the ID of all probes who are not disabled. """
        return self.probeTracker.GetActiveProbes()

    def HasAvailableProbes(self):
        return self.probeTracker.HasAvailableProbes()

    def GetProbeState(self, probeID):
        """ Returnes the current state of probeID. """
        return self.probeTracker.GetProbeState(probeID)

    def IsProbeActive(self, probeID):
        return self.probeTracker.IsProbeActive(probeID)

    def GetProbeData(self):
        return self.probeTracker.GetProbeData()

    def GetScaledProbes(self, point, probeIDs):
        return self.probeTracker.GetScaledProbes(point, probeIDs, mapcommon.SYSTEMMAP_SCALE)

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid' in change or 'shipid' in change:
            self.FlushScannerState(reinjectSites='solarsystemid' not in change)
            scanner = Scanner.GetIfOpen()
            if scanner:
                scanner.LoadResultList()

    def SetProbeDestination(self, probeID, location):
        """
        Sets the desired position of the probe; probe will be moved to that location before scanning
        once the user initiates scan.
        location => tuple
        """
        self.probeTracker.SetProbeDestination(probeID, location)

    def SetProbeRangeStep(self, probeID, rangeStep):
        """
        Set the active range step for a core scanner probe
        only values between 1 and const.scanProbeNumberOfRangeSteps (should be 8)
        """
        self.probeTracker.SetProbeRangeStep(probeID, rangeStep)

    def SetProbeActiveState(self, probeID, state):
        """ 
        Disables or enables the probe. 
        You are only allowed to disable IDLE probes and enable INACTIVE probes
        """
        self.probeTracker.SetProbeActiveState(probeID, state)

    def RequestScans(self):
        """
        Scan with all idle probes. If no such probes exist, scan with onboard scanner.
        Server method returns a list of the probes that were unavailable or failed early
        """
        probes = self.probeTracker.GetProbesForScanning()
        self.GetScanMan().RequestScans(probes)
        probeIDs = probes.keys() if probes is not None else [session.shipid]
        self.scanHandler.SetProbesAsScanning(probeIDs)
        self.probeTracker.SetProbesAsMoving(probes)

    def OnProbeStateChanged(self, probeID, probeState):
        self.probeTracker.OnProbeStateChanged(probeID, probeState)

    def GetScanningProbes(self):
        return self.scanHandler.GetScanningProbes()

    def GetScanResults(self):
        return self.scanHandler.GetScanResults()

    def GetCurrentScan(self):
        return self.scanHandler.GetCurrentScan()

    def GetIgnoredResults(self):
        return self.scanHandler.GetIgnoredResults()

    def GetIgnoredResultsDesc(self):
        resultIDs = self.GetIgnoredResults()
        descList = []
        for id in resultIDs:
            descList.append((id, self.GetDisplayName(self.scanHandler.resultsHistory.GetResult(id))))

        return descList

    def OnProbeWarpStart(self, probeID, fromPos, toPos, startTime, duration):
        self.LogInfo('OnProbeWarpStart', probeID)

    def OnProbesIdle(self, probes):
        self.probeTracker.OnProbesIdle(probes)

    def UpdateProbeState(self, probeID, state, caller = None, notify = True):
        self.probeTracker.UpdateProbeState(probeID, state, caller=None, notify=True)

    def UpdateProbePosition(self, probeID, position):
        self.probeTracker.UpdateProbePosition(probeID, position)

    def OnSystemScanStarted(self, startTime, durationMs, probes):
        self.scanHandler.OnSystemScanStarted(startTime, durationMs, probes)
        sm.ScatterEvent('OnSystemScanBegun')
        self.audio.SendUIEvent(unicode('wise:/msg_scanner_moving_stop'))
        self.audio.SendUIEvent(unicode('wise:/msg_scanner_analyzing_play'))

    def OnSystemScanStopped(self, probes, results, absentTargets):
        self.audio.SendUIEvent(unicode('wise:/msg_scanner_moving_stop'))
        self.audio.SendUIEvent(unicode('wise:/msg_scanner_analyzing_stop'))
        if not results:
            self.audio.SendUIEvent(unicode('wise:/msg_scanner_negative_play'))
            eve.Message('ScnNoResults')
        self.scanHandler.OnSystemScanStopped(probes, results, absentTargets)
        sm.ScatterEvent('OnSystemScanDone')

    def GetScanRangeStepsByTypeID(self, typeID):
        return self.probeTracker.GetScanRangeStepsByTypeID(typeID)

    def DestroyProbe(self, probeID):
        self.probeTracker.DestroyProbe(probeID, self.GetScanMan().DestroyProbe)

    def ConeScan(self, scanangle, scanRange, x, y, z):
        return self.GetScanMan().ConeScan(scanangle, scanRange, x, y, z)

    def ReconnectToLostProbes(self):
        if not session.solarsystemid2:
            return
        ship = sm.StartService('michelle').GetItem(eve.session.shipid)
        if ship and ship.groupID == const.groupCapsule:
            raise UserError('ScnProbeRecoverToPod')
        if self.CanClaimProbes():
            self.lastReconnection = blue.os.GetSimTime()
            try:
                self.probeTracker.ClearLastFormation()
                self.lastReconnection = blue.os.GetSimTime()
                self.GetScanMan().ReconnectToLostProbes()
            finally:
                uthread.new(self.Thread_ShowReconnectToProbesAvailable, self.lastReconnection)

        else:
            seconds = RECONNECT_DELAY_MINUTES * const.MIN - (blue.os.GetSimTime() - self.lastReconnection)
            raise UserError('ScannerProbeReconnectWait', {'when': (const.UE_TIMESHRT, seconds)})

    def Thread_ShowReconnectToProbesAvailable(self, lastReconnection):
        snooze = (RECONNECT_DELAY_MINUTES * const.MIN - (blue.os.GetSimTime() - self.lastReconnection)) / const.MSEC
        while snooze > 0:
            blue.pyos.synchro.SleepSim(snooze)
            if self.lastReconnection is None:
                break
            snooze = (RECONNECT_DELAY_MINUTES * const.MIN - (blue.os.GetSimTime() - self.lastReconnection)) / const.MSEC

        sm.ScatterEvent('OnReconnectToProbesAvailable')

    def CanClaimProbes(self):
        if self.HasOnlineProbeLauncher() and (self.lastReconnection is None or blue.os.GetSimTime() - self.lastReconnection > RECONNECT_DELAY_MINUTES * const.MIN):
            return True
        return False

    def HasOnlineProbeLauncher(self):
        shipItem = sm.GetService('godma').GetStateManager().GetItem(session.shipid)
        if shipItem is not None:
            for module in shipItem.modules:
                if module.groupID == const.groupScanProbeLauncher and module.isOnline:
                    return True

        return False

    def GetProbeLabel(self, probeID):
        if probeID in self.probeLabels:
            return self.probeLabels[probeID]
        newlabel = localization.GetByLabel('UI/Inflight/Scanner/ProbeLabel', probeIndex=len(self.probeLabels) + 1)
        self.probeLabels[probeID] = newlabel
        return newlabel

    def RecoverProbe(self, probeID):
        self.RecoverProbes([probeID])

    def RecoverProbes(self, probeIDs):
        ship = sm.StartService('michelle').GetItem(eve.session.shipid)
        if ship and ship.groupID == const.groupCapsule:
            raise UserError('ScnProbeRecoverToPod')
        self.probeTracker.RecoverProbes(probeIDs, self.AskServerToRecallProbes)

    def AskServerToRecallProbes(self, probeIDs):
        return self.GetScanMan().RecoverProbes(probeIDs)

    def OnScannerInfoRemoved(self):
        """
        When scanMgr clears the scannerInfo we get this message.
        We should clear all probe data and results and request update from scanner UI.
        """
        self.LogInfo('OnScannerInfoRemoved received: flushing scanner state')
        self.FlushScannerState()

    def FlushScannerState(self, reinjectSites = True):
        """
        Flush scanner data
        - probe data
        - results
        - scan meta data
        - moniker to remote object
        
        end by scattering an event to refresh UI
        """
        self.LogInfo('FlushScannerState: resetting state and scattering OnScannerDisconnected')
        self.probeTracker.Refresh()
        self.scanHandler = scanHandler.ScanHandler(self, sm.ScatterEvent, self.resultFilter)
        if reinjectSites:
            with util.ExceptionEater('Failure Reinjecting Anomalies'):
                self.InjectSitesAsScanResults(sm.GetService('sensorSuite').probeScannerController.GetAllSites())
        self.remoteObject = None
        sm.StartService('audio').SendUIEvent(unicode('wise:/msg_scanner_moving_stop'))
        sm.StartService('audio').SendUIEvent(unicode('wise:/msg_scanner_analyzing_stop'))
        sm.ScatterEvent('OnScannerDisconnected')

    def IsScanning(self):
        self.scanHandler.IsScanning()

    def GetProbeMenu(self, probeID, probeIDs = None, *args):
        menu = []
        if probeID == eve.session.shipid:
            return menu
        bp = sm.StartService('michelle').GetBallpark(doWait=True)
        if bp is None:
            return menu
        probeIDs = probeIDs or [probeID]
        if probeID not in probeIDs:
            probeIDs.append(probeID)
        if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            menu.append(('CopyID', self._GMCopyID, (probeID,)))
            menu.append(None)
        if self.IsProbeActive(probeID):
            menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/DeactivateProbe'), self.SetProbeActiveStateOff_Check, (probeID, probeIDs)))
        else:
            menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/ActivateProbe'), self.SetProbeActiveStateOn_Check, (probeID, probeIDs)))
        probes = self.GetProbeData()
        if probeID in probes:
            probe = probes[probeID]
            scanRanges = self.GetScanRangeStepsByTypeID(probe.typeID)
            menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/ScanRange'), [ (util.FmtDist(range), self.SetScanRange_Check, (probeID,
               probeIDs,
               range,
               index + 1)) for index, range in enumerate(scanRanges) ]))
        menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/RecoverProbe'), self.RecoverProbe_Check, (probeID, probeIDs)))
        menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/DestroyProbe'), self.DestroyProbe_Check, (probeID, probeIDs)))
        return menu

    def _GMCopyID(self, id):
        blue.pyos.SetClipboardData(str(id))

    @UserErrorIfScanning
    def SetScanRange_Check(self, probeID, probeIDs, range, rangeStep):
        for _probeID in probeIDs:
            probe = self.GetProbeData()[_probeID]
            self.SetProbeRangeStep(_probeID, rangeStep)

    @UserErrorIfScanning
    def RecoverProbe_Check(self, probeID, probeIDs):
        for _probeID in probeIDs:
            self.RecoverProbe(_probeID)

    @UserErrorIfScanning
    def SetProbeActiveStateOn_Check(self, probeID, probeIDs):
        for _probeID in probeIDs:
            self.GetScanMan().SetActivityState(probeIDs, True)
            self.SetProbeActiveState(_probeID, True)

    @UserErrorIfScanning
    def SetProbeActiveStateOff_Check(self, probeID, probeIDs):
        for _probeID in probeIDs:
            self.GetScanMan().SetActivityState(probeIDs, False)
            self.SetProbeActiveState(_probeID, False)

    @UserErrorIfScanning
    def DestroyProbe_Check(self, probeID, probeIDs):
        if probeIDs and eve.Message('DestroySelectedProbes', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            for _probeID in probeIDs:
                self.DestroyProbe(_probeID)

    def IgnoreResult(self, *targets):
        self.scanHandler.IgnoreResult(*targets)

    def ClearIgnoredResults(self):
        self.scanHandler.ClearIgnoredResults()

    def ClearResults(self, *targets):
        self.scanHandler.ClearResults(*targets)

    def AlignToPosition(self, position):
        ballpark = self.michelle.GetBallpark()
        myBall = self.michelle.GetBall(ballpark.ego)
        myPosition = (myBall.x, myBall.y, myBall.z)
        directionalVector = geo2.Vec3SubtractD(position, myPosition)
        rbp = self.michelle.GetRemotePark()
        rbp.CmdGotoDirection(directionalVector[0], directionalVector[1], directionalVector[2])

    def IgnoreOtherResults(self, *targets):
        self.scanHandler.IgnoreOtherResults(*targets)

    def ShowIgnoredResult(self, targetID):
        self.scanHandler.ShowIgnoredResult(targetID)

    def GetProbeLauncher(self):
        ship = self.godma.GetItem(session.shipid)
        for module in ship.modules:
            if not module.isOnline:
                continue
            if module.groupID == const.groupScanProbeLauncher:
                return module

    def FindModuleAndLaunchProbes(self, numProbes):
        ship = self.godma.GetItem(session.shipid)
        module = self.GetProbeLauncher()
        if any((s.locationID == session.shipid and s.flagID == module.flagID for s in ship.sublocations)):
            for effect in module.effects.itervalues():
                if effect.isDefault:
                    dogmaLM = self.godma.GetStateManager().GetDogmaLM()
                    dogmaLM.LaunchProbes(module.itemID, numProbes)
                    return

    def GetChargesInProbeLauncher(self):
        launcher = self.GetProbeLauncher()
        if launcher is None:
            return 0
        flagID = launcher.flagID
        charge = self.godma.GetStateManager().GetSubLocation(session.shipid, flagID)
        if charge is None:
            return 0
        return charge.quantity

    def CanLaunchFormation(self, formationID):
        charges = self.GetChargesInProbeLauncher()
        return self.probeTracker.CanCreateFormation(formationID, charges)

    def MoveProbesToFormation(self, formationID):
        self.probeTracker.MoveProbesToFormation(formationID, self.FindModuleAndLaunchProbes, self.GetChargesInProbeLauncher())

    def GetProbeTracker(self):
        return self.probeTracker

    def SetProbesAsScanning(self, probes):
        return self.probeTracker.SetProbesAsScanning(probes)

    def ProbeControlSelect(self):
        uicore.layer.systemmapBrackets.state = uiconst.UI_DISABLED

    def ProbeControlDeselected(self):
        uicore.layer.systemmapBrackets.state = uiconst.UI_PICKCHILDREN

    def FocusOnProbe(self, probeID):
        try:
            probeID = int(probeID)
        except ValueError:
            uicore.layer.systemmap.FocusOnPoint(self.probeTracker.GetCenterOfActiveProbes())
        else:
            uicore.layer.systemmap.FocusOnPoint(self.probeTracker.GetProbe(probeID).destination)

    def GetFilterOptions(self):
        return self.resultFilter.GetFilters()

    def GetActiveFilter(self):
        return self.resultFilter.GetActiveFilter()

    def GetActiveFilterID(self):
        return self.resultFilter.GetActiveFilterID()

    def SetActiveFilter(self, filterID):
        self.resultFilter.SetActiveFilter(filterID)

    def DeleteCurrentFilter(self):
        self.resultFilter.DeleteActiveFilter()

    def GetResults(self):
        results, ignored, filtered, anomalies = self.scanHandler.GetResults()
        results = [ util.KeyVal(**r) for r in results ]
        return (results,
         ignored,
         filtered,
         anomalies)

    def GetResultFilter(self, filterID):
        return self.resultFilter.GetFilter(filterID)

    def CreateResultFilter(self, name, groups):
        self.resultFilter.CreateFilter(name, groups)

    def EditResultFilter(self, filterID, name, groups):
        self.resultFilter.EditFilter(filterID, name, groups)

    def GetDisplayName(self, result):
        displayName = ''
        if result.typeID:
            displayName = self.GetTypeName(result)
        if not displayName and result.groupID:
            displayName = self.GetGroupName(result)
        if not displayName:
            displayName = self.GetScanGroupName(result)
        return displayName

    def GetTypeName(self, result):
        if IsExplorationSite(result):
            if result.dungeonNameID is not None:
                return localization.GetByMessageID(result.dungeonNameID)
            return ''
        elif result.typeID is not None:
            return cfg.invtypes.Get(result.typeID).name
        else:
            return ''

    def GetGroupName(self, result):
        if IsExplorationSite(result):
            if result.strengthAttributeID is not None:
                return self.GetExplorationSiteType(result.strengthAttributeID)
            return ''
        elif result.groupID is not None:
            return cfg.invgroups.Get(result.groupID).name
        else:
            return ''

    def GetExplorationSiteType(self, attributeID):
        """
        returns the type name of exploration sites from based on the attribureID of it's strongest
        scan strength.
        defaults to empty string
        """
        label = const.EXPLORATION_SITE_TYPES[attributeID]
        return localization.GetByLabel(label)

    def GetScanGroupName(self, result):
        return self.scanGroups[result.scanGroupID]

    def GetMasterGroupsForActiveFilter(self):
        return self.resultFilter.GetMasterGroupsForActiveFilter()

    def RestoreProbesFromBackup(self):
        self.probeTracker.RestoreProbesFromBackup()

    def StartMoveMode(self):
        self.probeTracker.StartMoveMode()

    def PurgeBackupData(self):
        self.probeTracker.PurgeBackupData()

    def GetResultForTargetID(self, targetID):
        return self.scanHandler.resultsHistory.GetResultAsDict(targetID)

    def GetIgnoreResultMenu(self, targetID, scanGroupID = None):
        menu = []
        menu.append(None)
        menuSvc = sm.GetService('menu')
        menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/IngoreResult'), self.IgnoreResult, (targetID,)))
        menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/IgnoreOtherResults'), self.IgnoreOtherResults, (targetID,)))
        if scanGroupID != const.probeScanGroupAnomalies:
            menu.append((uiutil.MenuLabel('UI/Inflight/Scanner/ClearResult'), self.ClearResults, (targetID,)))
        return menu

    def GetAccurateScannedDownMenu(self, scanResult):
        menu = []
        if scanResult.IsAccurate():
            menu.extend(self.GetScannedDownMenu(scanResult))
        return menu

    def GetScanResultMenuWithIgnore(self, scanResult, scanGroupId):
        menu = []
        menu.extend(self.GetAccurateScannedDownMenu(scanResult))
        menu.extend(self.GetIgnoreResultMenu(scanResult.targetID, scanGroupId))
        return menu

    def GetScanResultMenuWithoutIgnore(self, scanResult):
        return self.GetAccurateScannedDownMenu(scanResult)

    def GetScannedDownMenu(self, scanResult):
        menu = []
        if self.michelle.IsPositionWithinWarpDistance(scanResult.position):
            menu.extend(sm.GetService('menu').SolarsystemScanMenu(scanResult.targetID))
            menu.append(None)
        menu.extend(self.GetAlignToMenu(scanResult.position))
        bookmarkData = util.KeyVal(id=scanResult.targetID, position=scanResult.position, name=localization.GetByMessageID(scanResult.dungeonNameID))
        menu.append((uiutil.MenuLabel('UI/Inflight/BookmarkLocation'), sm.GetService('addressbook').BookmarkLocationPopup, (session.solarsystemid,
          None,
          None,
          None,
          bookmarkData)))
        return menu

    def GetAlignToMenu(self, position):
        return [(uiutil.MenuLabel('UI/Inflight/AlignTo'), self.AlignToPosition, (position,))]

    def InjectSitesAsScanResults(self, sites):
        self.scanHandler.InjectResults(sites)

    def ShowAnomalies(self):
        self.resultFilter.ShowAnomalies()

    def StopShowingAnomalies(self):
        self.resultFilter.StopShowingAnomalies()

    def ClickLink(self, action):
        if action == 'ShowAnomalies':
            self.resultFilter.ShowAnomalies()
        elif action == 'HideAnomalies':
            self.resultFilter.StopShowingAnomalies()
        elif action == 'ClearFiltered':
            self.resultFilter.SetActiveFilter(0)
        elif action == 'ClearIgnored':
            self.scanHandler.ClearIgnoredResults()
        else:
            raise RuntimeError('scanSvc::ClickLink - Not supported action (%s)' % action)
        wnd = Scanner.GetIfOpen()
        if wnd is not None:
            wnd.LoadFilterOptionsAndResults()

    def IsShowingAnomalies(self):
        return self.resultFilter.IsShowingAnomalies()

    def PersistCurrentFormation(self, name):
        probeInfo = self.probeTracker.GetProbePositionAndRangeInfo()
        customFormations.PersistFormation(name, probeInfo.values())
