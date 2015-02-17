#Embedded file name: probescanning\resultFilter.py
import probescanning.const
import inventorycommon.const
_defaultFilters = {0: ('UI/Common/Show all', None),
 -1: ('UI/Inflight/Scanner/CosmicSignature', probescanning.const.GetCosmicSignatureGroups()),
 -2: ('UI/Inflight/Scanner/Drones', probescanning.const.GetDroneGroups()),
 -3: ('UI/Inflight/Scanner/Ships', probescanning.const.GetShipGroups()),
 -4: ('UI/Inflight/Scanner/Structures', probescanning.const.GetStructureGroups())}

class ResultFilter(object):

    def __init__(self, getSetting, saveSetting, getByLabel):
        self.GetSetting = getSetting
        self.SaveSetting = saveSetting
        self.GetByLabel = getByLabel
        self.PrimePersistedFilters()

    def GetNewFilterID(self):
        try:
            return max(self.filters.keys()) + 1
        except ValueError:
            return 1

    def CreateFilter(self, filterName, groups):
        filterID = self.GetNewFilterID()
        self.filters[filterID] = (filterName, groups)
        self._PersistFilters()
        self.SetActiveFilter(filterID)
        return filterID

    def EditFilter(self, filterID, name, groups):
        if filterID == 0:
            raise RuntimeError("Can't Edit Show all Filter")
        if filterID < 0:
            self.DeleteFilter(filterID)
            filterID = self.CreateFilter(name, groups)
            self.SetActiveFilter(filterID)
        else:
            self.filters[filterID] = (name, groups)
        self._PersistFilters()
        return filterID

    def GetMasterGroupsForActiveFilter(self):
        _, groups = self.GetFilter(self.activeFilter)
        if groups is None:
            return probescanning.const.probeScanGroups.keys()
        masterGroups = set()
        for groupID in groups:
            for scanGroupID, scanGroup in probescanning.const.probeScanGroups.iteritems():
                if isinstance(groupID, tuple):
                    groupID = groupID[0]
                if groupID in scanGroup:
                    masterGroups.add(scanGroupID)

        return masterGroups

    def GetFilters(self):
        defaultFilters = [ (self.GetByLabel(label), filterID) for filterID, (label, _) in _defaultFilters.iteritems() if filterID not in self.deletedFilters ]
        myFilters = [ (label, filterID) for filterID, (label, _) in self.filters.iteritems() ]
        return defaultFilters + myFilters

    def GetFilter(self, filterID):
        if filterID <= 0:
            label, groups = _defaultFilters[filterID]
            return (self.GetByLabel(label), groups)
        else:
            return self.filters[filterID]

    def DeleteFilter(self, filterID):
        if filterID < 0:
            self.deletedFilters.add(filterID)
        if filterID > 0:
            del self.filters[filterID]
        self._PersistFilters()

    def GetActiveFilter(self):
        return self.GetFilter(self.activeFilter)

    def GetActiveFilterID(self):
        return self.activeFilter

    def SetActiveFilter(self, filterID):
        self.activeFilter = filterID
        self._PersistActiveFilter()

    def DeleteActiveFilter(self):
        self.DeleteFilter(self.activeFilter)
        self.SetActiveFilter(0)

    def PrimePersistedFilters(self):
        filterInfo = self.GetSetting('probeScannerFilters', None)
        if filterInfo is not None:
            self.filters = {}
            self.deletedFilters = set()
            self.activeFilter = 0
            for name, groups in filterInfo.iteritems():
                self.CreateFilter(name, groups)
                self.SaveSetting('probeScannerFilters', None)

        else:
            self.filters = self.GetSetting('probescanning.resultFilter.filters', {})
            self.deletedFilters = self.GetSetting('probescanning.resultFilter.deletedFilters', set())
            self.activeFilter = self.GetSetting('probescanning.resultFilter.activeFilter', 0)
        self.showingAnomalies = self.GetSetting('probescanning.resultFilter.showingAnomalies', True)

    def IsFiltered(self, result):
        masterGroups = self.GetMasterGroupsForActiveFilter()
        _, currentFilter = self.GetActiveFilter()
        if currentFilter is None:
            return False
        if currentFilter:
            if result['certainty'] >= probescanning.const.probeResultGood:
                if result['groupID'] == inventorycommon.const.groupCosmicSignature:
                    if (result['groupID'], result['strengthAttributeID']) not in currentFilter:
                        return True
                elif result['groupID'] not in currentFilter:
                    return True
            elif result['scanGroupID'] not in masterGroups:
                return True
        return False

    def IsShowingAnomalies(self):
        return self.showingAnomalies

    def ShowAnomalies(self):
        self.showingAnomalies = True

    def StopShowingAnomalies(self):
        self.showingAnomalies = False

    def _PersistFilters(self):
        self.SaveSetting('probescanning.resultFilter.filters', self.filters)
        self.SaveSetting('probescanning.resultFilter.deletedFilters', self.deletedFilters)

    def _PersistActiveFilter(self):
        self.SaveSetting('probescanning.resultFilter.activeFilter', self.activeFilter)

    def _PersistShowingAnomalies(self):
        self.SaveSetting('probescanning.resultFilter.showingAnomalies', self.showingAnomalies)
