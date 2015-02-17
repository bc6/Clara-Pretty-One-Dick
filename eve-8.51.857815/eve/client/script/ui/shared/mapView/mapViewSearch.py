#Embedded file name: eve/client/script/ui/shared/mapView\mapViewSearch.py
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from eve.client.script.ui.control.searchinput import SearchInput
from eve.client.script.ui.util.searchUtil import Search
import weakref

class MapViewSearchControl(Container):
    default_align = uiconst.TOPLEFT
    default_width = 160
    default_height = 20
    searchInput = None
    searchResult = None
    searchFor = None
    mapView = None
    scrollListResult = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        if attributes.mapView:
            self.mapView = weakref.ref(attributes.mapView)
        self.searchFor = [const.searchResultConstellation,
         const.searchResultSolarSystem,
         const.searchResultRegion,
         const.searchResultStation]
        searchInput = SearchInput(name='MapViewSearchEdit', parent=self, width=self.width, maxLength=64, GetSearchEntries=self.GetSearchData, OnSearchEntrySelected=self.OnSearchEntrySelected, OnReturn=self.OnSearchInputConfirm, hinttext='Search')
        searchInput.searchResultVisibleEntries = 20
        searchInput.SetHistoryVisibility(False)
        self.searchInput = searchInput

    def GetSearchData(self, searchString):
        self.scrollListResult = []
        searchString = searchString.lstrip()
        if len(searchString) >= 3:
            self.searchInput.SetValue(searchString, docallback=False)
            results = Search(searchString, self.searchFor, getWindow=False)
            self.scrollListResult = self.PrepareResultScrollEntries(results)
        return self.scrollListResult

    def PrepareResultScrollEntries(self, results, *args):
        scrollList = []
        import listentry
        for groupEntry in results:
            entryType, typeList = groupEntry['groupItems']
            for entryData in typeList:
                scrollList.append(listentry.Get(entryType, entryData))

        return scrollList

    def OnSearchInputConfirm(self, *args, **kwds):
        if self.scrollListResult and len(self.scrollListResult) == 1:
            self.OnSearchEntrySelected(self.scrollListResult)

    def OnSearchEntrySelected(self, selectedDataList, *args, **kwds):
        self.delaySelectionTimer = AutoTimer(500, self._OnSearchEntrySelectedDelayed, selectedDataList)

    def _OnSearchEntrySelectedDelayed(self, selectedDataList, *args, **kwds):
        self.delaySelectionTimer = None
        if self.mapView:
            mapView = self.mapView()
            mapView.LoadSearchResult(selectedDataList)
