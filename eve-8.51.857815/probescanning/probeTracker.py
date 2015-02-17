#Embedded file name: probescanning\probeTracker.py
import logging
import geo2
import math
import probescanning.formations as formations
import probescanning.formationTracker as formationTracker
import probescanning.const
from probescanning.util import GetCenter, GetRangeStepAndSizeFromScanRange
import dogma.const
from eveexceptions import UserError

class ProbeTracker(object):
    """
    Keeps track of probes. Where they are and whether they are scanning or not
    """

    def __init__(self, scanSvc, ScatterEvent):
        self.logger = logging.getLogger('probescanning-probeTracker')
        self.scanSvc = scanSvc
        self.ScatterEvent = ScatterEvent
        self.lastRangeStepUsed = 0
        self.probeData = {}
        self.scanRangeByTypeID = {}
        self.scalingPoint = None
        self.backupProbeData = None
        self.formationTracker = formationTracker.FormationTracker(probescanning.const.AU, self.ProbeGoToPoint)
        self.formationTracker.CreateFormation(formations.SPREAD_FORMATION)

    def Refresh(self):
        self.probeData = {}
        self.scalingPoint = None
        self.backupProbeData = None
        self.formationTracker.Refresh()

    def AddProbe(self, probe):
        self.probeData[probe.probeID] = probe
        probe.rangeStep = self.lastRangeStepUsed
        probe.scanRange = self.GetScanRangeStepsByTypeID(probe.typeID)[self.lastRangeStepUsed - 1]
        probe.destination = probe.pos
        self.UpdateProbeState(probe.probeID, probescanning.const.probeStateIdle, 'OnNewProbe')
        self.formationTracker.AddProbeToFormation(probe.probeID)
        self.ScatterEvent('OnProbeAdded', probe)

    def PersistProbeFormation(self):
        probeInfo = self.GetProbePositionAndRangeInfo()
        self.formationTracker.UpdateCurrentFormation(probeInfo)

    def ClearLastFormation(self):
        self.formationTracker.ClearCurrentFormation()

    def RemoveProbe(self, probeID):
        if probeID in self.probeData:
            del self.probeData[probeID]
        self.formationTracker.RemoveProbeFromFormation(probeID)
        self.ScatterEvent('OnProbeRemoved', probeID)

    def GetActiveProbes(self):
        """ Returnes the ID of all probes who are not disabled. """
        return [ kv.probeID for kv in self.probeData.values() if kv.state != probescanning.const.probeStateInactive ]

    def HasAvailableProbes(self):
        return any((probe.state == probescanning.const.probeStateIdle for probe in self.probeData.itervalues()))

    def GetProbeState(self, probeID):
        """ Returnes the current state of probeID. """
        if probeID in self.probeData:
            return self.probeData[probeID].state

    def IsProbeActive(self, probeID):
        return bool(probeID in self.probeData and self.probeData[probeID].state)

    def GetProbeData(self):
        return self.probeData

    def GetProbe(self, probeID):
        return self.probeData[probeID]

    def SetProbeDestination(self, probeID, location):
        """
        Sets the desired position of the probe; probe will be moved to that location before scanning
        once the user initiates scan.
        location => tuple
        """
        self.probeData[probeID].destination = location

    def SetProbeRangeStep(self, probeID, rangeStep):
        """
        Set the active range step for a core scanner probe
        only values between 1 and const.scanProbeNumberOfRangeSteps (should be 8)
        """
        if 1 <= rangeStep <= probescanning.const.scanProbeNumberOfRangeSteps:
            self.lastRangeStepUsed = rangeStep
            probe = self.probeData[probeID]
            probe.rangeStep = rangeStep
            rangeSteps = self.GetScanRangeStepsByTypeID(probe.typeID)
            scanRange = rangeSteps[rangeStep - 1]
            probe.scanRange = scanRange
            self.ScatterEvent('OnProbeRangeUpdated', probeID, probe.scanRange)

    def SetProbeActiveState(self, probeID, state):
        """
        Disables or enables the probe.
        You are only allowed to disable IDLE probes and enable INACTIVE probes
        """
        if probeID in self.probeData:
            if (self.probeData[probeID].state, int(state)) in [(probescanning.const.probeStateIdle, probescanning.const.probeStateInactive), (probescanning.const.probeStateInactive, probescanning.const.probeStateIdle)]:
                self.UpdateProbeState(probeID, int(state), 'SetProbeActiveState')

    def OnProbeStateChanged(self, probeID, probeState):
        self.logger.debug('OnProbeStateChanged %d, %d', probeID, probeState)
        self.UpdateProbeState(probeID, probeState, 'OnProbeStateChanged')

    def OnProbesIdle(self, probes):
        for probe in probes:
            self.UpdateProbeState(probe.probeID, probescanning.const.probeStateIdle, caller='OnProbesIdle')
            self.SetProbeDestination(probe.probeID, probe.destination)

    def UpdateProbeState(self, probeID, state, caller = None, notify = True):
        """
        Registers new probe state and delegates in through OnProbeStateUpdated
        It verifies if the probeID is valid and returns if not
        notify: False if we want to suppress event scattering,
        """
        if probeID not in self.probeData:
            self.logger.warning('UpdateProbeState: probe %d not in my list of probes. Called by %s', probeID, caller)
            return
        self.probeData[probeID].state = state
        if notify:
            self.ScatterEvent('OnProbeStateUpdated', probeID, state)

    def UpdateProbePosition(self, probeID, position):
        probeData = self.probeData[probeID]
        distSq = geo2.Vec3LengthSq(position)
        if distSq > probescanning.const.MAX_PROBE_DIST_FROM_SUN_SQUARED:
            scale = probescanning.const.MAX_PROBE_DIST_FROM_SUN_SQUARED / distSq
            position = geo2.Vec3Scale(position, scale)
        probeData.pos = probeData.destination = position
        return position

    def DestroyProbe(self, probeID, func):
        if probeID not in self.probeData:
            return
        if self.probeData[probeID].state in (probescanning.const.probeStateIdle, probescanning.const.probeStateInactive):
            func(probeID)
            del self.probeData[probeID]

    def ProbeGoToPoint(self, probeID, destination, size):
        probe = self.probeData[probeID]
        if probe.state != probescanning.const.probeStateIdle:
            self.logger.debug('ProbeGoToPoint - ignored as probe %d is not idle', probeID)
            return
        probe.destination = destination
        probe.rangeStep, probe.scanRange = GetRangeStepAndSizeFromScanRange(size, self.GetScanRangeStepsByTypeID(probe.typeID))
        self.logger.debug('ProbeGoToPoint %d -> %s - step = %d, size= %s', probeID, destination, probe.rangeStep, probe.scanRange / probescanning.const.AU)
        self.ScatterEvent('OnProbePositionsUpdated')

    def CanCreateFormation(self, formationID, availableProbes):
        minProbesNeeded = formations.GetNumberOfProbesInFormation(formationID)
        return len(self.probeData) + availableProbes >= minProbesNeeded

    def CheckCanCreateFormation(self, formationID, availableProbes):
        minProbesNeeded = formations.GetNumberOfProbesInFormation(formationID)
        if len(self.probeData) + availableProbes < minProbesNeeded:
            raise UserError('NotEnoughProbesToFormFormation', {'minProbes': minProbesNeeded})

    def MoveProbesToFormation(self, formationID, LaunchProbes, availableProbes = 0):
        self.CheckCanCreateFormation(formationID, availableProbes)
        excessProbeIDs = self.formationTracker.CreateFormation(formationID, self.probeData.keys(), initialPosition=self.GetCenterOfActiveProbes())
        if excessProbeIDs:
            self.RecoverProbes(excessProbeIDs, self.scanSvc.AskServerToRecallProbes)
            return
        probesNeeded = formations.GetNumberOfProbesInFormation(formationID)
        probes = len(self.GetActiveProbes())
        if len(self.probeData) < probesNeeded:
            LaunchProbes(probesNeeded - probes)

    def _RecallExcessProbes(self, probesNeeded):
        activeProbeIDs = self.GetActiveProbes()
        excessProbes = len(activeProbeIDs) - probesNeeded
        if excessProbes > 0:
            self.RecoverProbes(activeProbeIDs[:excessProbes], self.scanSvc.AskServerToRecallProbes)

    def RecoverProbes(self, probeIDs, RecoverProbes):
        successProbeIDs = RecoverProbes(probeIDs)
        for pID in successProbeIDs:
            self.UpdateProbeState(pID, probescanning.const.probeStateMoving, 'RecoverProbes')

        if len(successProbeIDs) < len(probeIDs):
            raise UserError('NotAllProbesReturnedSuccessfully')

    def GetScanRangeStepsByTypeID(self, typeID):
        """
        Returns a list with all ranges available to probes of specific type.
        Results are computed lazily and cached in scanSvc.
        """
        if typeID not in self.scanRangeByTypeID:
            baseScanRange = self.scanSvc.godma.GetTypeAttribute(typeID, dogma.const.attributeBaseScanRange)
            baseFactor = self.scanSvc.godma.GetTypeAttribute(typeID, dogma.const.attributeRangeFactor)
            steps = []
            for i in xrange(probescanning.const.scanProbeNumberOfRangeSteps):
                factor = baseFactor ** i
                scanRange = baseScanRange * factor * probescanning.const.AU
                steps.append(scanRange)

            self.scanRangeByTypeID[typeID] = steps
            return steps
        return self.scanRangeByTypeID[typeID]

    def IsInFormation(self):
        return self.formationTracker.IsInFormation()

    def GetFormationCenter(self):
        return self.formationTracker.GetCenter()

    def ShiftAllProbes(self, translation):
        probeInfo = []
        for probeID, probe in self.probeData.iteritems():
            if probe.state != probescanning.const.probeStateIdle:
                continue
            destination = geo2.Vec3Add(probe.destination, translation)
            pos = self.UpdateProbePosition(probeID, destination)
            probeInfo.append((probeID, pos))

        self.PersistProbeFormation()
        return probeInfo

    def ShiftProbe(self, probeID, translation):
        probe = self.probeData[probeID]
        destination = geo2.Vec3Add(probe.destination, translation)
        finalDest = self.UpdateProbePosition(probeID, destination)
        self.PersistProbeFormation()
        return [(probeID, finalDest)]

    def BreakFormation(self):
        self.formationTracker.BreakFormation()
        self.ScatterEvent('OnProbePositionsUpdated')

    def HasProbesInFormation(self):
        return self.formationTracker.HasProbesInFormation()

    def SetProbesAsMoving(self, probes):
        if probes:
            for pID in probes:
                self.UpdateProbeState(pID, probescanning.const.probeStateMoving, 'RequestScans')

            self.scanSvc.audio.SendUIEvent(unicode('wise:/msg_scanner_moving_play'))

    def GetProbesForScanning(self):
        """
        Returns all probes that are idle. If none are launched then it returns None which means
        Ship scanning
        """
        if len(self.probeData) > 0:
            probes = {p.probeID:p for p in self.probeData.itervalues() if p.state == probescanning.const.probeStateIdle}
            if not probes:
                return
        else:
            probes = None
        return probes

    def SetProbesAsScanning(self, probes):
        validProbeIDs = []
        for probeID, probe in probes.iteritems():
            self.UpdateProbeState(probeID, probescanning.const.probeStateScanning, 'OnSystemScanStarted', notify=False)
            try:
                self.UpdateProbePosition(probeID, probe.pos)
            except KeyError:
                self.logger.error('probe %d not in my list of probes', probeID)
                continue

            validProbeIDs.append(probeID)

        return validProbeIDs

    def SetAsScaling(self, point):
        self.scalingPoint = point

    def UnsetAsScaling(self):
        self.scalingPoint = None

    def GetCenterOfActiveProbes(self):
        return GetCenter([ p.destination for p in self.probeData.itervalues() if p.state == probescanning.const.probeStateIdle ])

    def GetScaledProbes(self, point, probeIDs, systemMapScale):
        if self.scalingPoint is None:
            self.logger.error("Trying to scale probes but scalingPoint hasn't been set %s", probeIDs)
            return
        centerPoint = self.GetCenterOfActiveProbes()
        translationCenterPoint = geo2.Vec3Scale(centerPoint, systemMapScale)

        def DistSqFromCenter(v):
            return geo2.Vec3LengthSq(geo2.Vec3Subtract(v, translationCenterPoint))

        scale = math.sqrt(DistSqFromCenter(point) / DistSqFromCenter(self.scalingPoint))
        probeInfo = []
        for probeID, newPoint, newScanRange in self._ScaleFromCenterIterator(scale, probeIDs):
            probe = self.probeData[probeID]
            if probe.state != probescanning.const.probeStateIdle:
                continue
            probeInfo.append((probeID, newPoint, newScanRange))

        return probeInfo

    def GetRangeStepForType(self, typeID, scanRange):
        rangeSteps = self.GetScanRangeStepsByTypeID(typeID)
        return min(((rangeStep + 1, _scanRange) for rangeStep, _scanRange in enumerate(rangeSteps)), key=lambda x: abs(x[1] - scanRange))

    def _ScaleFromCenterIterator(self, scale, probeIDs):
        centerPoint = self.GetCenterOfActiveProbes()
        for probeID in probeIDs:
            probe = self.probeData[probeID]
            if probe.state != probescanning.const.probeStateIdle:
                continue
            newScanRange = probe.scanRange * scale
            vec1 = geo2.Vec3Scale(geo2.Vec3Subtract(probe.destination, centerPoint), scale)
            newPoint = geo2.Vec3Add(centerPoint, vec1)
            yield (probeID, newPoint, newScanRange)

    def ScaleAllProbes(self, scale):
        probeIDs = self.probeData.keys()
        for probeID, newPoint, newScanRange in self._ScaleFromCenterIterator(scale, probeIDs):
            self.UpdateProbePosition(probeID, newPoint)
            rangeStep, _ = self.GetRangeStepForType(self.probeData[probeID].typeID, newScanRange)
            self.SetProbeRangeStep(probeID, rangeStep)

        self.PersistProbeFormation()
        self.ScatterEvent('OnProbePositionsUpdated')

    def StartMoveMode(self):
        if self.backupProbeData is not None:
            self.logger.error('StartMoveMode - already a backed up data for this, ignoring this call')
            return
        self.backupProbeData = self.GetProbePositionAndRangeStepInfo()

    def PurgeBackupData(self):
        self.backupProbeData = None

    def GetProbePositionAndRangeStepInfo(self):
        return {probeID:(probe.destination, probe.rangeStep) for probeID, probe in self.probeData.iteritems()}

    def GetProbePositionAndRangeInfo(self):
        return {probeID:(probe.destination, probe.scanRange) for probeID, probe in self.probeData.iteritems()}

    def RestoreProbesFromBackup(self):
        if self.backupProbeData is not None:
            self.RestoreProbePositionAndRange(self.backupProbeData)
            self.backupProbeData = None

    def RestoreProbePositionAndRange(self, probeData):
        for probeID, (position, rangeStep) in probeData.iteritems():
            self.UpdateProbePosition(probeID, position)
            self.SetProbeRangeStep(probeID, rangeStep)
