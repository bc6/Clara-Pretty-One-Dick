#Embedded file name: probescanning\formationTracker.py
import logging
import geo2
import probescanning.formations as formations
from probescanning.formations import MIN_PROBES_NEEDED

class FormationTracker(object):

    def __init__(self, unitSize, GoToPoint):
        self.logger = logging.getLogger('probescanning-formationTracker')
        self.GoToPoint = GoToPoint
        self.unitSize = unitSize
        self.formationID = None
        self.centerPosition = None
        self.currentFormation = None
        self.probes = [None] * MIN_PROBES_NEEDED

    def Refresh(self):
        self.probes = [None] * MIN_PROBES_NEEDED
        if self.currentFormation is not None:
            for idx, (_, pos, scanRange) in enumerate(self.currentFormation):
                self.currentFormation[idx] = (None, pos, scanRange)

    def CreateFormation(self, formationID, probeIDs = None, initialPosition = (0, 0, 0), formationSize = None):
        self.ClearCurrentFormation()
        self.formationID = formationID
        if initialPosition is not None:
            self.centerPosition = initialPosition
        minProbesNeeded = formations.GetNumberOfProbesInFormation(formationID)
        self.probes = [None] * minProbesNeeded
        if probeIDs is None:
            return []
        for probeID in probeIDs[:minProbesNeeded]:
            self.AddProbeToFormation(probeID)

        return probeIDs[minProbesNeeded:]

    def PlaceProbeInFormation(self, probeID):
        if self.currentFormation is None:
            return False
        for idx, (otherProbeID, position, scanRange) in enumerate(self.currentFormation):
            if probeID == otherProbeID:
                self.logger.error('probe already in currentFormation %d', probeID)
                return False
            if otherProbeID is None:
                self.currentFormation[idx] = (probeID, position, scanRange)
                self.GoToPoint(probeID, position, scanRange)
                return True

        return False

    def AddProbeToFormation(self, probeID):
        if self.PlaceProbeInFormation(probeID):
            return
        if self.probes is None:
            return
        if self.formationID is None:
            return
        index = self._FindAvailableSpotForProbe()
        if index is None:
            raise RuntimeError('Available position not found')
        self.probes[index] = probeID
        self._PlaceProbe(probeID, index)

    def _FindAvailableSpotForProbe(self):
        for i, probe in enumerate(self.probes):
            if probe is None:
                return i

    def GetActiveProbes(self):
        return filter(lambda x: x is not None, self.probes)

    def RemoveProbeFromFormation(self, probeToBeRemovedID):
        for i, probeID in enumerate(self.probes):
            if probeID == probeToBeRemovedID:
                self.probes[i] = None
                break

        if self.currentFormation is not None:
            for idx, (probeID, pos, scanRange) in enumerate(self.currentFormation):
                if probeID == probeToBeRemovedID:
                    self.currentFormation[idx] = (None, pos, scanRange)

    def GetPositionAndSize(self, index):
        position, scanRange = formations.GetProbeInfoInFormation(self.formationID, index)
        position = geo2.Vec3Add(position, self.centerPosition)
        return (position, scanRange)

    def _PlaceProbe(self, probeID, index):
        newPosition, scanRange = self.GetPositionAndSize(index)
        self.GoToPoint(probeID, newPosition, scanRange)

    def IsInFormation(self):
        return self.formationID is not None

    def HasProbesInFormation(self):
        if self.formationID is not None:
            return any(self.probes)
        return False

    def GetCenter(self):
        return self.centerPosition

    def BreakFormation(self):
        self.formationID = None

    def UpdateCurrentFormation(self, probeInfo):
        self.currentFormation = []
        for probeID, (position, scanRange) in probeInfo.iteritems():
            self.currentFormation.append((probeID, position, scanRange))

    def ClearCurrentFormation(self):
        self.currentFormation = []
        self.formationID = None
