#Embedded file name: eve/client/script/ui/control\searchinput.py
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.container import Container
from carbonui.primitives.frame import Frame
from carbonui.util.various_unsorted import IsUnder, GetWindowAbove
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.eveScroll import Scroll
import weakref
import uthread
import carbonui.const as uiconst

class SearchInput(SinglelineEdit):
    scrollPosition = None
    searchString = None
    searchResultMenu = None
    searchResultVisibleEntries = 5
    OnSearchEntrySelected = None
    blockSelection = False

    def ApplyAttributes(self, attributes):
        SinglelineEdit.ApplyAttributes(self, attributes)
        self.OnChange = self.OnSearchInputChange
        self.GetSearchEntries = attributes.GetSearchEntries
        self.OnSearchEntrySelected = attributes.OnSearchEntrySelected
        uicore.uilib.RegisterForTriuiEvents([uiconst.UI_MOUSEDOWN], self.OnGlobalMouseDown)

    def Close(self, *args, **kwds):
        self.OnSearchEntrySelected = None
        self.GetSearchEntries = None
        self.OnInsert = None
        self.searchThread = None
        self.CloseResultMenu()
        SinglelineEdit.Close(self, *args, **kwds)

    def CloseResultMenu(self):
        if self.searchResultMenu:
            searchResultMenu = self.searchResultMenu()
            if searchResultMenu and not searchResultMenu.destroyed:
                self.scrollPosition = (self.searchString, searchResultMenu.searchScroll.GetScrollProportion())
                searchResultMenu.Close()
            self.searchResultMenu = None

    def OnSearchInputChange(self, *args, **kwds):
        if not self.GetValue():
            self.searchThread = None
            self.SearchForData()
        else:
            self.searchThread = AutoTimer(280, self.SearchForData)

    def SearchForData(self):
        self.searchThread = None
        if self.GetSearchEntries:
            searchString = self.GetValue()
            self.searchString = searchString
            valid = self.GetSearchEntries(searchString)
            self.ShowSearchResult(valid)

    def ShowSearchResult(self, result):
        searchResultMenu = None
        if self.searchResultMenu:
            searchResultMenu = self.searchResultMenu()
            if searchResultMenu and searchResultMenu.destroyed:
                searchResultMenu = None
        if not result:
            self.CloseResultMenu()
            return
        if not searchResultMenu:
            l, t, w, h = self.GetAbsolute()
            searchResultMenu = Container(name='resultMenuParent', parent=uicore.layer.utilmenu, pos=(l,
             t + h + 1,
             max(w, 200),
             300), align=uiconst.TOPLEFT, opacity=0.0)
            searchResultMenu.searchScroll = Scroll(parent=searchResultMenu, align=uiconst.TOALL)
            searchResultMenu.searchScroll.sr.underlay.opacity = 0.0
            if self.OnSearchEntrySelected:
                searchResultMenu.searchScroll.OnSelectionChange = self.OnSelectionChanged
            Frame(bgParent=searchResultMenu, frameConst=uiconst.FRAME_BORDER1_CORNER0, color=(1.0, 1.0, 1.0, 0.2))
            Frame(bgParent=searchResultMenu, frameConst=uiconst.FRAME_FILLED_CORNER0, color=(0.0, 0.0, 0.0, 0.75))
            self.searchResultMenu = weakref.ref(searchResultMenu)
            self.updateThread = AutoTimer(1, self.UpdateDropdownState)
            startHeight = 0
        else:
            startHeight = searchResultMenu.height
        if self.scrollPosition and self.searchString == self.scrollPosition[0]:
            scrollTo = self.scrollPosition[1]
        else:
            scrollTo = 0.0
        self.scrollTo = scrollTo
        searchResultMenu.searchScroll.LoadContent(contentList=result, scrollTo=scrollTo)
        visibleEntriesHeight = sum([ node.height for node in searchResultMenu.searchScroll.sr.nodes[:self.searchResultVisibleEntries] ])
        endHeight = min(searchResultMenu.searchScroll.GetContentHeight(), visibleEntriesHeight) + 2
        uicore.animations.MorphScalar(searchResultMenu, 'height', startVal=startHeight, endVal=endHeight, duration=0.25, callback=self.SetScrollPosition)
        uicore.animations.FadeTo(searchResultMenu, startVal=searchResultMenu.opacity, endVal=1.0, duration=0.5)

    def SetScrollPosition(self, *args, **kwds):
        if self.searchResultMenu:
            searchResultMenu = self.searchResultMenu()
            if searchResultMenu and not searchResultMenu.destroyed:
                uthread.new(searchResultMenu.searchScroll.ScrollToProportion, self.scrollTo)

    def UpdateDropdownState(self):
        if self.destroyed:
            self.updateThread = None
            return
        if not (self.searchResultMenu and self.searchResultMenu()):
            self.updateThread = None
            return
        wnd = GetWindowAbove(self)
        activeWindow = uicore.registry.GetActive()
        if wnd and wnd is not activeWindow and activeWindow is not uicore.desktop:
            self.CloseResultMenu()
            return

    def GetSearchEntriesDemo(self, searchString):
        if not searchString:
            return []
        import listentry
        import random
        entries = []
        for i in xrange(random.choice([0,
         2,
         4,
         8,
         16])):
            entries.append(listentry.Get('User', {'charID': session.charid}))

        return entries

    def OnSelectionChanged(self, *args, **kwds):
        if not self.blockSelection and self.OnSearchEntrySelected:
            self.OnSearchEntrySelected(*args, **kwds)

    def OnMouseDown(self, *args, **kwds):
        SinglelineEdit.OnMouseDown(self, *args, **kwds)
        uthread.new(self.SearchForData)

    def OnGlobalMouseDown(self, *args):
        if self.destroyed:
            return False
        self.blockSelection = False
        searchResultMenu = self.searchResultMenu
        if searchResultMenu and searchResultMenu():
            for layer in (uicore.layer.utilmenu, uicore.layer.menu):
                if IsUnder(uicore.uilib.mouseOver, layer):
                    if uicore.uilib.rightbtn:
                        self.blockSelection = True
                    return True

            self.CloseResultMenu()
        return True

    def OnKeyDown(self, vkey, flag):
        if vkey in (uiconst.VK_DOWN, uiconst.VK_UP):
            if self.searchResultMenu:
                searchResultMenu = self.searchResultMenu()
                if searchResultMenu and not searchResultMenu.destroyed:
                    if vkey == uiconst.VK_UP:
                        searchResultMenu.searchScroll.OnUp()
                    else:
                        searchResultMenu.searchScroll.OnDown()
        SinglelineEdit.OnKeyDown(self, vkey, flag)
