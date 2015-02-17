#Embedded file name: eve/client/script/ui/control\tabGroup.py
from carbonui.primitives.line import Line
from eve.client.script.ui.control.eveFrame import Frame
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import Label, EveLabelSmall
from carbonui.primitives.container import Container
from carbonui.primitives.dragdrop import DragDropObject
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay, RaisedUnderlay, TabUnderlay, LineUnderlay, LabelUnderlay
import log
import uthread
import uiutil
import carbonui.const as uiconst
import trinity
import sys
import const
import telemetry
MAINCOLOR = (1.0,
 1.0,
 1.0,
 0.5)

class TabGroup(Container):
    """ A group of tabs used to divide windows into panels, one visible at a time """
    __guid__ = 'uicontrols.TabGroup'
    __notifyevents__ = ('OnUIScalingChange',)
    default_name = 'tabgroup'
    default_align = uiconst.TOTOP
    default_height = 20
    default_clipChildren = True
    default_state = uiconst.UI_PICKCHILDREN
    default_leftMargin = 8
    default_rightMargin = 20
    default_minTabsize = 32
    default_groupID = None
    default_labelPadding = 6
    default_callback = None
    default_padLeft = 2
    default_padRight = 2
    default_padTop = 1

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self._inited = 0
        self._iconOnly = False
        self.leftMargin = attributes.get('leftMargin', self.default_leftMargin)
        self.rightMargin = attributes.get('rightMargin', self.default_rightMargin)
        self.minTabsize = attributes.get('minTabsize', self.default_minTabsize)
        self.labelPadding = attributes.get('labelPadding', self.default_labelPadding)
        self.callback = attributes.get('callback', self.default_callback)
        self.sr.tabsmenu = None
        self.sr.tabs = []
        self.sr.mytabs = []
        self._resizing = 0
        self.totalTabWidth = 0
        self._settingsID = None
        self.sr.linkedrows = []
        tabs = attributes.tabs
        groupID = attributes.get('groupID', self.default_groupID)
        autoselecttab = attributes.get('autoselecttab', True)
        UIIDPrefix = attributes.UIIDPrefix
        silently = attributes.get('silently', False)
        if tabs:
            self.Startup(tabs, groupID=groupID, autoselecttab=autoselecttab, UIIDPrefix=UIIDPrefix, silently=silently)
        sm.RegisterNotify(self)

    @telemetry.ZONE_METHOD
    def Startup(self, tabs, groupID = None, _notUsed_callback = None, _notUsed_isSub = 0, _notUsed_detachable = 0, autoselecttab = 1, UIIDPrefix = None, silently = False):
        loadtabs = []
        for each in tabs:
            panelparent = None
            hint = None
            uiID = 'tab'
            if len(each) == 4:
                label, panel, code, args = each
            elif len(each) == 5:
                label, panel, code, args, panelparent = each
            elif len(each) == 6:
                label, panel, code, args, panelparent, hint = each
            if isinstance(label, tuple):
                name, label = label
            else:
                name = label
            if UIIDPrefix is not None:
                secondPart = name.replace(' ', '')
                secondPart = secondPart.capitalize()
                uiID = '%s%s' % (UIIDPrefix, secondPart)
            tabData = uiutil.Bunch()
            tabData.label = label
            tabData.code = code
            tabData.args = args
            tabData.panel = panel
            tabData.panelparent = panelparent
            tabData.hint = hint
            tabData.name = uiID
            loadtabs.append(tabData)

        self.LoadTabs(loadtabs, autoselecttab, settingsID=groupID, silently=silently)

    def OnUIScalingChange(self, *args):
        if not self.destroyed:
            self.UpdateSizes()

    @telemetry.ZONE_METHOD
    def Prepare_Tabsmenu_(self):
        from carbonui.control.imagebutton import ImageButtonCore as ImageButton
        tri = ImageButton(icon='ui_1_16_14', parent=self, align=uiconst.BOTTOMLEFT, idx=0, state=uiconst.UI_NORMAL, pos=(0, 2, 16, 16), idleIcon='ui_1_16_14', mouseoverIcon='ui_1_16_30', mousedownIcon='ui_1_16_46', getmenu=self.GetTabLinks, expandonleft=True)
        self.sr.tabsmenu = tri

    @telemetry.ZONE_METHOD
    def LoadTabs(self, tabs, autoselecttab = 1, settingsID = None, iconOnly = False, silently = False):
        self._iconOnly = iconOnly
        self.sr.tabs = []
        self.sr.mytabs = []
        self.sr.tabsmenu = None
        self.Flush()
        LineUnderlay(parent=self, align=uiconst.TOBOTTOM)
        maxTextHeight = 0
        for data in tabs:
            newtab = Tab(parent=self, labelPadding=self.labelPadding)
            self.sr.mytabs.append(newtab)
            newtab.Startup(self, data)
            newtab.align = uiconst.TOLEFT
            self.sr.Set('%s_tab' % data.label, newtab)
            self.sr.tabs.append(newtab)
            maxTextHeight = max(maxTextHeight, newtab.sr.label.textheight)
            if newtab.sr.icon:
                maxTextHeight = max(maxTextHeight, newtab.sr.icon.height)

        self.height = max(self.height, int(maxTextHeight * 1.7))
        self._inited = 1
        self._settingsID = settingsID
        self.UpdateSizes()
        if autoselecttab:
            self.AutoSelect(silently)

    def GetTabLinks(self):
        return [ (each.sr.label.text, self.SelectByIdx, (self.sr.tabs.index(each),)) for each in self.sr.tabs ]

    def _OnSizeChange_NoBlock(self, width, height):
        Container._OnSizeChange_NoBlock(self, width, height)
        self.UpdateSizes((width, height))

    @telemetry.ZONE_METHOD
    def UpdateSizes(self, absSize = None):
        if not self._inited:
            return
        if not (self.sr and self.sr.mytabs):
            return
        if self._resizing:
            return
        self._resizing = 1
        if not uiutil.IsUnder(self, uicore.desktop):
            self._resizing = 0
            return
        if absSize:
            mw, _ = absSize
        else:
            mw, _ = self.GetAbsoluteSize()
        if self.destroyed:
            return
        for tab in self.sr.mytabs:
            tab.UpdateTabSize()

        totalTabWidth = sum([ each.sr.width for each in self.sr.mytabs ])
        totalSpace = mw - self.leftMargin - self.rightMargin
        needToShrink = max(0, totalTabWidth - totalSpace)
        totalShrunk = 0
        allMin = 1
        for each in self.sr.mytabs:
            portionOfFull = each.sr.width / float(totalTabWidth)
            each.portionOfFull = portionOfFull
            each.width = min(each.sr.width, max(self.minTabsize, each.sr.width - int(needToShrink * portionOfFull)))
            if each.width > self.minTabsize:
                allMin = 0
            totalShrunk += each.sr.width - each.width

        needMore = max(0, needToShrink - totalShrunk)
        while needMore and not allMin:
            _allMin = 1
            for each in self.sr.mytabs:
                if each.width > self.minTabsize and needMore > 0:
                    each.width -= 1
                    needMore = max(0, needMore - 1)
                if each.width > self.minTabsize:
                    _allMin = 0

            allMin = _allMin

        allMin = 1
        for each in self.sr.mytabs:
            if each.width != self.minTabsize:
                allMin = 0

        if self.sr.tabsmenu:
            self.sr.tabsmenu.Close()
            self.sr.tabsmenu = None
        active = self.GetVisible(1)
        i = 0
        i2 = 0
        totalWidth = 0
        totalVisible = 0
        hidden = 0
        countActive = None
        startHiddenIdx = None
        for each in self.sr.mytabs:
            if allMin and (hidden or totalWidth + each.width > totalSpace):
                if each == active:
                    countActive = i2
                each.state = uiconst.UI_HIDDEN
                if hidden == 0:
                    startHiddenIdx = i
                hidden = 1
                i2 += 1
            else:
                each.state = uiconst.UI_NORMAL
                totalWidth += each.width
                totalVisible += 1
            i += 1

        if allMin:
            if countActive is not None and startHiddenIdx is not None:
                totalWidth = 0
                totalVisible = 0
                i = 0
                for each in self.sr.mytabs:
                    if i <= countActive:
                        each.state = uiconst.UI_HIDDEN
                    elif startHiddenIdx <= i <= startHiddenIdx + countActive:
                        each.state = uiconst.UI_NORMAL
                    if each.state == uiconst.UI_NORMAL:
                        totalWidth += each.width
                        totalVisible += 1
                    i += 1

        self.totalTabWidth = totalWidth
        totalVisibleWidth = self.leftMargin
        leftover = max(0, totalSpace - totalWidth)
        for each in self.sr.mytabs:
            if each.state == uiconst.UI_NORMAL:
                each.width = min(each.sr.width, max(self.minTabsize, each.width + leftover / totalVisible))
                totalVisibleWidth += each.width

        if hidden:
            self.Prepare_Tabsmenu_()
            self.sr.tabsmenu.left = totalVisibleWidth
            self.sr.tabsmenu.state = uiconst.UI_NORMAL
        for tabgroup in self.sr.linkedrows:
            if tabgroup != self:
                tabgroup.UpdateSizes()

        self._resizing = 0

    def GetTabs(self):
        if not self.destroyed:
            return self.sr.tabs

    def GetTotalWidth(self):
        tw = sum([ each.sr.width for each in self.sr.mytabs ])
        return tw + self.leftMargin + self.rightMargin

    def AddRow(self, tabgroup):
        for tab in tabgroup.sr.tabs:
            tab.sr.tabgroup = self
            self.sr.tabs.append(tab)

        self.sr.linkedrows.append(tabgroup)
        if self not in self.sr.linkedrows:
            self.sr.linkedrows.append(self)
        tabgroup.UpdateSizes()

    @telemetry.ZONE_METHOD
    def AutoSelect(self, silently = 0):
        if self.destroyed:
            return
        idx = 0
        if self._settingsID:
            idx = settings.user.tabgroups.Get(self._settingsID, 0)
        uthread.new(self.sr.tabs[min(len(self.sr.tabs) - 1, idx)].Select, silently=silently)

    def SelectByIdx(self, idx, silent = 1):
        if len(self.sr.tabs) > idx:
            self.sr.tabs[idx].Select(silent)

    def SelectPrev(self):
        idx = self.GetSelectedIdx()
        if idx is None:
            return
        idx -= 1
        if idx < 0:
            idx = len(self.sr.tabs) - 1
        self.SelectByIdx(idx, silent=False)

    def SelectNext(self):
        idx = self.GetSelectedIdx()
        if idx is None:
            return
        idx += 1
        if idx > len(self.sr.tabs) - 1:
            idx = 0
        self.SelectByIdx(idx, silent=False)

    def GetSelectedIdx(self):
        for idx, tab in enumerate(self.sr.tabs):
            if tab.IsSelected():
                return idx

    def ShowPanel(self, panel, *args):
        for tab in self.sr.tabs:
            if tab.sr.panel == panel:
                tab.Select(1)

    def ShowPanelByName(self, panelname, blink = 1):
        if panelname:
            tab = self.sr.Get('%s_tab' % panelname, None)
            if tab:
                tab.Select(1)
        else:
            log.LogWarn('Trying to show panel', panelname)

    def BlinkPanelByName(self, panelname, blink = 1):
        if panelname:
            tab = self.sr.Get('%s_tab' % panelname, None)
            if tab:
                tab.Blink(blink)
        else:
            log.LogWarn('Trying to blink panel', panelname)

    def _OnClose(self, *args):
        self.sr.callback = None
        self.sr.linkedrows = []
        for each in self.sr.tabs:
            if each is not None and not each.destroyed:
                each.Close()

        self.sr.tabs = None
        self.btns = []
        Container._OnClose(self, *args)

    def GetVisible(self, retTab = 0):
        if self is None or self.destroyed:
            return
        for tab in self.sr.tabs:
            if tab.IsSelected():
                if retTab:
                    return tab
                return tab.sr.panel

    def ReloadVisible(self):
        tab = self.GetVisible(1)
        if tab:
            tab.Select(1)

    def GetSelectedArgs(self):
        for tab in self.sr.tabs:
            if tab.IsSelected():
                return tab.sr.args


class Tab(Container):
    default_align = uiconst.TOPLEFT
    default_fontsize = 10
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None
    default_labelPadding = 6
    default_padLeft = 1
    OPACITY_SELECTED = 1.0
    OPACITY_IDLE = 0.0
    OPACITY_HOVER = 0.125

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.labelPadding = attributes.get('labelPadding', self.default_labelPadding)
        self.ignoreWndDrag = 1
        self.selecting = 0
        self.sr.icon = None
        self.sr.LoadTabCallback = None
        self.isTabStop = True
        self._detachallowed = False
        self.Prepare_()
        if self.sr.label:
            self.sr.label.Close()
        self.sr.label = LabelUnderlay(parent=self.sr.clipper, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, name='tabLabel', fontsize=10)
        self.isTabStop = False

    @telemetry.ZONE_METHOD
    def Prepare_(self):
        self.sr.clipper = Container(parent=self, align=uiconst.TOALL, padding=(self.labelPadding,
         1,
         6,
         1), clipChildren=True, state=uiconst.UI_PICKCHILDREN, name='labelClipper')
        self.sr.label = LabelUnderlay(parent=self.sr.clipper, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize, letterspace=1, uppercase=1, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, name='tabLabel', colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)
        self.selectedBG = TabUnderlay(name='underlay', bgParent=self, isGlowEdgeRotated=True)

    @telemetry.ZONE_METHOD
    def Startup(self, tabgroup, data):
        from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
        self.blinkDrop = StretchSpriteHorizontal(parent=self, align=uiconst.TOTOP_NOPUSH, color=(0.5, 0.5, 0.5, 0.0), name='blinkDrop', height=11, leftEdgeSize=6, rightEdgeSize=6, offset=-2, blendMode=trinity.TR2_SBM_ADD, texturePath='res:/UI/Texture/Lines/BLUR4.png')
        self.sr.args = data.get('args', None)
        self.sr.grab = [0, 0]
        self.sr.tabgroup = tabgroup
        self._selected = False
        self.sr.panel = data.get('panel', None)
        self.sr.panelparent = data.get('panelparent', None)
        self.sr.code = data.get('code', None)
        self.sr.LoadTabCallback = data.get('LoadTabCallback', None)
        self.SetLabel(data.get('label', None))
        self.SetIcon(data.get('icon', None))
        self.Deselect(False)
        self.hint = data.get('hint', None)
        if hasattr(self.sr.code, 'GetTabMenu'):
            self.GetMenu = lambda : self.sr.code.GetTabMenu(self)
        if hasattr(self.sr.panel, 'sr'):
            self.sr.panel.sr.tab = self
        self.name = data.name or data.label

    def Confirm(self, *args):
        self.OnClick()

    def OnSetFocus(self, *args):
        pass

    def OnKillFocus(self, *etc):
        pass

    def SetLabel(self, label, hint = None):
        if self.destroyed:
            return
        if self.sr.tabgroup._iconOnly:
            self.sr.label.text = ''
        else:
            self.sr.label.text = label
            self.UpdateTabSize()
        self.sr.label.hint = hint
        self.hint = hint
        self.sr.tabgroup.UpdateSizes()

    def UpdateTabSize(self):
        self.sr.width = self.sr.label.width + self.sr.label.left + self.sr.label.parent.padLeft * 2

    def OnDropData(self, dragObj, nodes):
        if hasattr(self, 'OnTabDropData'):
            if self.OnTabDropData(dragObj, nodes):
                self.BlinkOnDrop()
        elif isinstance(self.sr.panel, DragDropObject) and hasattr(self.sr.panel, 'OnDropData'):
            if self.sr.panel.OnDropData(dragObj, nodes):
                self.BlinkOnDrop()

    def Blink(self, onoff = 1):
        if onoff:
            self.selectedBG.Blink(uiconst.ANIM_REPEAT)
        else:
            self.selectedBG.StopBlink()
        self.blinking = onoff

    def BlinkOnDrop(self):
        uicore.animations.FadeTo(self.blinkDrop, 0.0, 1.0, duration=0.25, curveType=uiconst.ANIM_WAVE, loops=2)

    def SetUtilMenu(self, utilMenuFunc):
        from eve.client.script.ui.control.utilMenu import UtilMenu
        self.sr.label.left = 14
        UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self, align=uiconst.TOPLEFT, GetUtilMenu=utilMenuFunc, texturePath='res:/UI/Texture/Icons/73_16_50.png', pos=(const.defaultPadding,
         const.defaultPadding,
         14,
         14))
        self.UpdateTabSize()
        self.sr.tabgroup.UpdateSizes()

    def SetIcon(self, iconNo, shiftLabel = 14, hint = None, menufunc = None):
        if self.sr.icon:
            self.sr.icon.Close()
        self.sr.hint = hint
        if iconNo is None:
            if self.sr.label:
                self.sr.label.left = 0
        else:
            self.sr.icon = Icon(icon=iconNo, parent=self, pos=(2, 3, 16, 16), align=uiconst.TOPLEFT, idx=0, state=uiconst.UI_DISABLED)
            if self.sr.label:
                self.sr.label.left = shiftLabel
            if menufunc:
                self.sr.icon.GetMenu = menufunc
                self.sr.icon.expandOnLeft = 1
                self.sr.icon.state = uiconst.UI_NORMAL
        self.sr.hint = hint
        self.UpdateTabSize()
        self.sr.tabgroup.UpdateSizes()

    def OnClick(self, *args):
        if self.selecting:
            return
        uicore.registry.SetFocus(self)
        self.sr.tabgroup.state = uiconst.UI_DISABLED
        try:
            self.Select()
        finally:
            self.sr.tabgroup.state = uiconst.UI_PICKCHILDREN

    def IsSelected(self):
        return self._selected

    @telemetry.ZONE_METHOD
    def Deselect(self, notify = True):
        self._selected = False
        self.ShowDeselected_()
        if self.sr.panel:
            self.sr.panel.state = uiconst.UI_HIDDEN
            if notify:
                if hasattr(self.sr.panel, 'OnTabDeselect'):
                    self.sr.panel.OnTabDeselect()
        if self.sr.panelparent:
            self.sr.panelparent.state = uiconst.UI_HIDDEN
            if notify:
                if hasattr(self.sr.panelparent, 'OnTabDeselect'):
                    self.sr.panelparent.OnTabDeselect()

    @telemetry.ZONE_METHOD
    def ShowDeselected_(self):
        self.selectedBG.Deselect()
        self.sr.label.opacity = 0.75

    @telemetry.ZONE_METHOD
    def ShowSelected_(self):
        self.selectedBG.Select()
        self.sr.label.opacity = 1.5

    @telemetry.ZONE_METHOD
    def Select(self, silently = 0):
        if self.destroyed:
            return
        self.selecting = 1
        self.Blink(0)
        if self is None or self.destroyed:
            self.selecting = 0
            self.sr.tabgroup.state = uiconst.UI_PICKCHILDREN
            return
        if len(self.sr.tabgroup.sr.linkedrows):
            for tabgroup in self.sr.tabgroup.sr.linkedrows:
                if self in tabgroup.sr.mytabs:
                    continue
                uiutil.SetOrder(tabgroup, 0)

        for each in self.sr.tabgroup.sr.tabs:
            if each.IsSelected():
                if hasattr(self.sr.code, 'UnloadTabPanel'):
                    self.sr.code.UnloadTabPanel(each.sr.args, each.sr.panel, each.sr.tabgroup)
            if each == self:
                continue
            notify = True
            if each.sr.panel and each.sr.panel is self.sr.panel or each.sr.panelparent and each.sr.panelparent is self.sr.panelparent:
                notify = False
            each.Deselect(notify)

        self._selected = True
        self.ShowSelected_()
        if self.sr.panelparent:
            self.sr.panelparent.state = uiconst.UI_PICKCHILDREN
            if hasattr(self.sr.panelparent, 'OnTabSelect'):
                self.sr.panelparent.OnTabSelect()
        if self.sr.panel:
            self.sr.panel.state = uiconst.UI_PICKCHILDREN
            if hasattr(self.sr.panel, 'OnTabSelect'):
                self.sr.panel.OnTabSelect()
        if self.sr.tabgroup.callback:
            self.sr.tabgroup.callback(self.sr.tabgroup.GetSelectedIdx())
        err = None
        if self.sr.LoadTabCallback:
            try:
                self.sr.LoadTabCallback(self.sr.args, self.sr.panel, self.sr.tabgroup)
            finally:
                self.selecting = 0

        elif hasattr(self.sr.code, 'LoadTabPanel'):
            try:
                self.sr.code.LoadTabPanel(self.sr.args, self.sr.panel, self.sr.tabgroup)
            finally:
                self.selecting = 0

        elif getattr(self.sr.code, 'Load', None):
            try:
                self.sr.code.Load(self.sr.args)
            except (StandardError,) as err:
                log.LogException(toMsgWindow=0)
                sys.exc_clear()
                if self.destroyed:
                    return
                wnd = uiutil.GetWindowAbove(self)
                if wnd and not wnd.destroyed:
                    wnd.HideLoad()

        if not silently:
            par = self.sr.panelparent or self.sr.panel
            wnd = uiutil.GetWindowAbove(self)
            if par and wnd and wnd == uicore.registry.GetActive():
                uthread.new(uicore.registry.SetFocus, par)
        if self.destroyed:
            return
        if self.sr.tabgroup._settingsID:
            settings.user.tabgroups.Set(self.sr.tabgroup._settingsID, self.sr.tabgroup.sr.tabs.index(self))
        if self and not self.destroyed:
            self.sr.tabgroup.UpdateSizes()
            self.selecting = 0
        if err and isinstance(err, UserError):
            raise err

    def OnMouseDown(self, *args):
        self._detachallowed = 1
        aL, aT, aW, aH = self.GetAbsolute()
        self.sr.grab = [uicore.uilib.x - aL, uicore.uilib.y - aT]
        self.selectedBG.OnMouseDown()

    def OnMouseUp(self, *args):
        self._detachallowed = 0
        self.selectedBG.OnMouseUp()

    def OnMouseMove(self, *args):
        if self._detachallowed and uicore.uilib.mouseTravel > 24 and hasattr(self.sr.code, 'Detach'):
            uthread.new(self.DoDetach)

    def OnMouseEnter(self, *args):
        if self._selected:
            return
        self.selectedBG.OnMouseEnter()
        uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, 1.5, duration=0.1)

    def OnMouseExit(self, *args):
        self.selectedBG.OnMouseExit()
        if self._selected:
            uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, 1.5, duration=0.1)
        else:
            uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, 0.75, duration=0.1)

    def DoDetach(self, *args):
        if self is not None and not self.destroyed:
            if self.sr.code.Detach(self.sr.panel, self.sr.grab):
                if self is not None and not self.destroyed:
                    self.Close()
            else:
                self._detachallowed = 0
