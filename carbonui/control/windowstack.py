#Embedded file name: carbonui/control\windowstack.py
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.window import WindowCore
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.themeColored import FillThemeColored
import uthread
import carbonui.const as uiconst
import log
from carbonui.control.menuLabel import MenuLabel
from carbonui.util.bunch import Bunch

class WindowStackCore(Window):
    __guid__ = 'uicontrols.WindowStackCore'

    @classmethod
    def Reload(cls, instance):
        pass

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.sr.tabs = ContainerAutoSize(parent=self.sr.maincontainer, name='__tabs', align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, idx=0)
        self._detaching = 0
        self._inserting = 0

    def Prepare_LoadingIndicator_(self):
        self.sr.loadingIndicator = None
        self.sr.loadingBlock = None

    def Prepare_ScaleAreas_(self):
        Window.Prepare_ScaleAreas_(self)
        for wnd in self.GetWindows():
            wnd.Prepare_ScaleAreas_()

    def Prepare_Header_(self):
        self.headerFill = None
        self.sr.captionParent = None
        self.sr.caption = None

    def UpdateCaption(self):
        self.SetCaption(self.GetCaption())

    def GetCaption(self, update = 1):
        caption = ''
        for wnd in self.GetWindows():
            if wnd is not None and not wnd.destroyed:
                caption = '%s%s-' % (caption, wnd.GetCaption(update))

        if caption != '':
            return caption[:-1]
        return caption

    def GetCollapsedHeight(self):
        return 26

    def OnCollapsed(self, *args):
        self.sr.content.display = False
        for wnd in self.GetWindows():
            wnd.OnCollapsed(*args)

    def OnExpanded(self, *args):
        self.sr.content.display = True
        for wnd in self.GetWindows():
            wnd.OnExpanded(*args)

    def CloseByUser(self, *args, **kwds):
        for wnd in self.GetWindows()[:]:
            wnd.CloseByUser()

        Window.CloseByUser(self, *args, **kwds)

    def OnEndScale_(self, *args):
        for wnd in self.GetWindows():
            if wnd.state == uiconst.UI_PICKCHILDREN:
                wnd.OnEndScale_(wnd)

    def InsertWnd(self, wnd, adjustlocation = 1, show = 0, hilite = 0):
        windowID = getattr(wnd, 'windowID', None)
        preferredIdx = self.GetAndRegisterPreferredIdxInStack(self.windowID, windowID)
        self._inserting = True
        l, t, mywidth, myheight = self.GetAbsolute()
        if not len(self.GetWindows()) and adjustlocation:
            log.LogInfo('WindowStack initing, taking size from', wnd.windowID, wnd.left, 'l,t,w,h', wnd.top, wnd.width, wnd.height)
            self.width = wnd.width
            if not self.IsCollapsed():
                self.height = wnd.height
            self.left = wnd.left
            self.top = wnd.top
        if wnd.IsCollapsed():
            wnd.Expand()
        wnd.SetParent(self.sr.content, idx=preferredIdx)
        wnd.align = uiconst.TOALL
        wnd.startingup = True
        wnd.left = wnd.top = wnd.width = wnd.height = 0
        wnd.startingup = False
        wnd.sr.stack = self
        wnd._stack_cacheContents = wnd.cacheContents
        wnd.cacheContents = False
        wnd.state = uiconst.UI_HIDDEN
        wnd.sr.loadingIndicator.Stop()
        self.Check(0, show != 1)
        if show:
            self.ShowWnd(wnd, hilite)
        wnd.CloseHeaderButtons(destroy=True)
        wnd.RegisterStackID(self)
        self.CleanupParent('snapIndicator')
        self._inserting = False
        if self.IsMinimized():
            self.Maximize()
        wnd.Prepare_ScaleAreas_()

    def SetMinWH(self):
        allMinW = 0
        allMinH = 0
        for each in self.GetWindows():
            allMinW = max(allMinW, each.minsize[0])
            allMinH = max(allMinH, each.minsize[1])

        if self.IsCollapsed():
            self.minsize = [allMinW, allMinH]
        else:
            self.SetMinSize([allMinW, allMinH])

    def ShowWnd(self, wnd, hilite = 0):
        if not self.sr.tabs.children:
            return
        tabparent = self.sr.tabs.children[0]
        if wnd not in self.GetWindows() or wnd is None or wnd.destroyed:
            return
        if tabparent is None or tabparent.destroyed:
            return
        tabparent.ShowPanel(wnd, hilite)

    def GetActiveWindow(self):
        if len(self.sr.tabs.children):
            tabparent = self.sr.tabs.children[0]
            if tabparent is None or tabparent.destroyed:
                return
            return tabparent.GetVisible()

    def IsResizeable(self):
        for wnd in self.GetWindows():
            if not wnd.IsResizeable():
                return False

        return True

    def IsMinimizable(self):
        for wnd in self.GetWindows():
            if not wnd.IsMinimizable():
                return False

        return True

    def IsKillable(self):
        for wnd in self.GetWindows():
            if not wnd.IsKillable():
                return False

        return True

    def IsCompactable(self):
        for wnd in self.GetWindows():
            if not wnd.IsCompactable():
                return False

        return True

    def IsCompact(self):
        for wnd in self.GetWindows():
            if not wnd.IsCompact():
                return False

        return True

    def Compact(self):
        for wnd in self.GetWindows():
            wnd.Compact()

        self.RefreshHeaderButtonsIfVisible()

    def UnCompact(self):
        for wnd in self.GetWindows():
            wnd.UnCompact()

        self.RefreshHeaderButtonsIfVisible()

    def IsLocked(self):
        for wnd in self.GetWindows():
            if wnd.IsLocked():
                return True

    def Detach(self, wnd, grab):
        if self.IsLocked():
            return False
        if wnd is not None and not wnd.destroyed and not getattr(wnd, '_detaching', 0):
            self._detaching = True
            self.RemoveWnd(wnd, grab, 1, 0, 1)
            if not self.destroyed:
                self._detaching = False
            return 1

    def RemoveWnd(self, wnd, grab, correctpos = 1, idx = 0, dragging = 0, check = 1):
        if wnd.parent != self.sr.content:
            return
        if hasattr(wnd, 'OnTabSelect'):
            uthread.worker('WindowStack::RemoveWnd', wnd.OnTabSelect)
        wnd._detaching = True
        wnd.SetParent(self.parent, idx)
        if hasattr(wnd, '_stack_cacheContents'):
            wnd.cacheContents = wnd._stack_cacheContents
        wnd.sr.stack = None
        wnd.sr.tab = None
        wnd.align = uiconst.TOPLEFT
        wnd.state = uiconst.UI_NORMAL
        wnd.grab = grab
        wnd.dragMousePosition = (uicore.uilib.x, uicore.uilib.y)
        wnd.width = wnd._fixedWidth or self.width
        wnd.height = wnd._fixedHeight or self.height
        if dragging:
            uicore.uilib.SetMouseCapture(wnd)
            uthread.new(wnd._BeginDrag)
        wnd.ShowHeader()
        wnd.ShowBackground()
        if correctpos:
            wnd.left = uicore.uilib.x - grab[0]
            wnd.top = uicore.uilib.y - grab[1]
        if check:
            self.Check()
        wnd.RegisterStackID()
        wnd._detaching = False
        wnd._dragging = dragging
        myWindows = self.GetWindows()
        if len(myWindows) == 1 and not self.IsCollapsed():
            w = myWindows[0]
            aL, aT, aW, aH = self.GetAbsolute()
            x, y = aL, aT
            self.RemoveWnd(w, (0, 0), 1, 1, check=0)
            w.left, w.top = x, y
            return
        if len(self.GetWindows()) == 0:
            self.Close()

    def Check(self, updatewnd = 0, autoselecttab = 1, checknone = 0):
        if self is None or self.destroyed:
            return
        myWindows = self.GetWindows()
        if checknone and len(myWindows) == 0:
            self.Close()
            return
        self.SetMinWH()
        tabs = []
        label = ''
        for wnd in myWindows:
            if wnd is None or wnd.destroyed:
                continue
            tabData = Bunch()
            tabData.label = wnd.GetCaption() or wnd.windowID or '-'
            tabData.panel = wnd
            tabData.code = self
            tabData.args = wnd
            tabs.append(tabData)
            wnd.HideHeader()
            wnd.HideBackground()
            wnd.state = uiconst.UI_PICKCHILDREN
            label = label + wnd.GetCaption() + '-'

        if len(tabs):
            if len(label):
                label = label[:-1]
            self.sr.tabs.Flush()
            maintabs = self.GetTabGroupClass()(parent=self.sr.tabs, name='tabparent')
            maintabs.LoadTabs(tabs, autoselecttab)
            allTabs = maintabs.GetTabs()
            if allTabs:
                for i in xrange(len(allTabs)):
                    tab = allTabs[i]
                    wnd = myWindows[i]
                    tab.GetMenu = getattr(wnd, 'GetMenu', None)
                    tab.SetIcon(wnd.headerIconNo, getattr(wnd.sr.headerIcon, 'hint', ''), getattr(wnd.sr.headerIcon, 'GetMenu', None))
                    if wnd.isBlinking:
                        tab.Blink()

            self.SetCaption(label)

    def GetTabGroupClass(self):
        from eve.client.script.ui.control.tabGroup import TabGroup
        return TabGroup

    def GetMenu(self):
        menu = []
        if self.IsKillable():
            menu.append((MenuLabel('/Carbon/UI/Controls/Window/CloseWindowStack'), self.CloseByUser))
        if not self.sr.stack and self.IsMinimizable():
            if self.state == uiconst.UI_NORMAL:
                menu.append((MenuLabel('/Carbon/UI/Controls/Window/MinimizeWindowStack'), self.ToggleVis))
            else:
                menu.append((MenuLabel('/Carbon/UI/Controls/Window/MaximizeWindowStack'), self.ToggleVis))
        return menu

    def Load(self, wnd):
        if self.IsCollapsed() and not self._detaching and not self._inserting:
            self.Expand()
        for _wnd in self.GetWindows():
            if _wnd is not wnd:
                _wnd.state = uiconst.UI_HIDDEN

        wnd.state = uiconst.UI_PICKCHILDREN

    def GetMinWidth(self, checkgroup = 1):
        trueMinWidth = self.minsize[0]
        for wnd in self.GetWindows():
            trueMinWidth = max(wnd.GetMinWidth(), trueMinWidth)

        return trueMinWidth

    def GetMinHeight(self):
        trueMinHeight = self.minsize[1]
        for wnd in self.GetWindows():
            trueMinHeight = max(wnd.GetMinHeight(), trueMinHeight)

        return trueMinHeight

    def OnStartMaximize_(self, *args):
        for wnd in self.GetWindows():
            wnd.OnStartMaximize_(wnd)

    def OnEndMaximize_(self, *args):
        for wnd in self.GetWindows():
            wnd.OnEndMaximize_(wnd)

    def OnStartMinimize_(self, *args):
        for wnd in self.GetWindows():
            wnd.OnStartMinimize_(wnd)

    def OnEndMinimize_(self, *args):
        for wnd in self.GetWindows():
            wnd.OnEndMinimize_(wnd)

    def OnResize_(self, *args):
        for wnd in self.GetWindows():
            wnd._OnResize()

    def GetWindows(self):
        return [ each for each in self.sr.content.children if isinstance(each, WindowCore) ]

    def RegisterPreferredIdxInStack(self, stackID, windowID, idx = -1):
        allPreferred = settings.char.windows.Get('preferredIdxInStack', {})
        stackInfo = allPreferred.get(stackID, {})
        stackInfo[windowID] = idx
        allPreferred[stackID] = stackInfo
        settings.char.windows.Set('preferredIdxInStack', allPreferred)

    def GetAndRegisterPreferredIdxInStack(self, stackID, windowID):
        allPreferred = settings.char.windows.Get('preferredIdxInStack', {})
        stackInfo = allPreferred.get(stackID, {})
        preferredIdx = stackInfo.get(windowID, -1)
        if preferredIdx < 0:
            if len(self.sr.content.children) < 1:
                preferredIdx = 0
            else:
                preferredIdx = len(self.sr.content.children)
            self.RegisterPreferredIdxInStack(stackID, windowID, preferredIdx)
        return preferredIdx

    def RemovePreferredIdx(self, stackID, windowID):
        allPreferred = settings.char.windows.Get('preferredIdxInStack', {})
        stackInfo = allPreferred.get(stackID, {})
        stackInfo.pop(windowID, None)
        if not stackInfo:
            allPreferred.pop(stackID, None)
        else:
            allPreferred[stackID] = stackInfo
        settings.char.windows.Set('preferredIdxInStack', allPreferred)


class WindowStackCoreOverride(WindowStackCore):
    pass
