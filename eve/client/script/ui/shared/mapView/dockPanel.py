#Embedded file name: eve/client/script/ui/shared/mapView\dockPanel.py
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.base import Base
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.layoutGrid import LayoutGrid, LayoutGridRow
from eve.client.script.ui.control.buttons import Button, ButtonIcon
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveWindowUnderlay import WindowUnderlay
from eve.client.script.ui.control.eveLabel import EveLabelLarge, EveLabelMedium
import carbonui.const as uiconst
import blue
from eve.client.script.ui.control.themeColored import FrameThemeColored, FillThemeColored, StretchSpriteHorizontalThemeColored
import localization
import uthread
MINWIDTH = 300
MINHEIGHT = 300
TOOLBARWIDTH_FULLSCREEN = 400
TOOLBARHEIGHT = 26
SETTINGSKEY = 'dockPanel_%s'
BUTTON_FULLSCREEN = 1
BUTTON_DOCKLEFT = 2
BUTTON_DOCKRIGHT = 3
BUTTON_FLOAT = 4
BUTTON_DATA_BY_ID = {BUTTON_FULLSCREEN: ('res:/UI/Texture/classes/DockPanel/fullscreenButton.png', 'Fullscreen'),
 BUTTON_DOCKLEFT: ('res:/UI/Texture/classes/DockPanel/dockLeftButton.png', 'Dock left'),
 BUTTON_DOCKRIGHT: ('res:/UI/Texture/classes/DockPanel/dockRightButton.png', 'Dock right'),
 BUTTON_FLOAT: ('res:/UI/Texture/classes/DockPanel/floatButton.png', 'Floating')}

def GetPanelSettings(panelID):
    defaultSettings = {'align': uiconst.TOPLEFT,
     'positionX': 0.5,
     'positionY': 0.5,
     'widthProportion': 0.8,
     'heightProportion': 0.8,
     'widthProportion_docked': 0.5,
     'heightProportion_docked': 1.0}
    if panelID:
        registered = settings.user.ui.Get(SETTINGSKEY % panelID, {})
        defaultSettings.update(registered)
    return defaultSettings


class DockablePanelManager(object):
    __notifyevents__ = ['OnSetDevice', 'OnShowUI', 'OnHideUI']
    panels = {}

    def __init__(self):
        sm.RegisterNotify(self)

    def OnViewStateClosed(self):
        """
        Callback from the DockPanelView when its being closed,
        if we have panel in FullScreen state we need to close it.
        """
        for panel in self.panels.values():
            if panel.IsFullscreen():
                uthread.new(panel.Close)

    def GetPanel(self, panelID):
        panel = self.panels.get(panelID, None)
        if panel and not panel.destroyed:
            return panel

    def HasPanel(self, panelID):
        return bool(self.GetPanel(panelID))

    def RegisterPanel(self, dockPanel):
        if dockPanel.panelID in self.panels:
            prevPanel = self.panels[dockPanel.panelID]
            if not prevPanel.destroyed:
                prevPanel.Close()
        self.panels[dockPanel.panelID] = dockPanel

    def UnregisterPanel(self, dockPanel):
        if dockPanel.panelID in self.panels:
            del self.panels[dockPanel.panelID]
        self.CheckViewState()

    def CheckViewState(self):
        haveFullscreenPanel = False
        for panel in self.panels.values():
            if panel.IsFullscreen():
                haveFullscreenPanel = True
                break

        if not haveFullscreenPanel:
            sm.GetService('viewState').CloseSecondaryView('dockpanelview')
        self.UpdateCameraCenter()

    def UpdateCameraCenter(self):
        haveDockedPanel = False
        for panel in self.panels.values():
            if panel.IsDockedLeft() or panel.IsDockedRight():
                haveDockedPanel = True
                break

        if haveDockedPanel and eve.hiddenUIState is None:
            pLeft, pRight = uicore.layer.sidePanels.GetSideOffset()
            viewCenter = pLeft + (uicore.desktop.width - pLeft - pRight) / 2
            viewCenterProportion = viewCenter / float(uicore.desktop.width)
            sm.GetService('sceneManager').SetCameraOffsetOverride(-100 + int(200 * viewCenterProportion))
        else:
            sm.GetService('sceneManager').SetCameraOffsetOverride(None)

    def OnSetDevice(self, *args, **kwds):
        for panel in self.panels.values():
            if not panel.IsFullscreen():
                panel.InitDockPanelPosition()

    def OnHideUI(self, *args):
        self.UpdateCameraCenter()

    def OnShowUI(self, *args):
        self.UpdateCameraCenter()


class DockablePanelHeaderButton(ButtonIcon):
    default_width = 16
    default_height = 16

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)

    def GetTooltipPointer(self):
        return uiconst.POINT_TOP_1

    def GetTooltipDelay(self):
        return 5

    def GetTooltipPositionFallbacks(self, *args, **kwds):
        return [uiconst.POINT_TOP_2,
         uiconst.POINT_TOP_1,
         uiconst.POINT_TOP_3,
         uiconst.POINT_BOTTOM_2,
         uiconst.POINT_BOTTOM_1,
         uiconst.POINT_BOTTOM_3]


class DockablePanelHeaderButtonMenu(DockablePanelHeaderButton):
    callback = None
    tooltipPanelMenu = None

    def ApplyAttributes(self, attributes):
        DockablePanelHeaderButton.ApplyAttributes(self, attributes)
        self.panelID = attributes.panelID
        self.callback = attributes.dockViewModeCallback
        self.UpdateButtonState()

    def Close(self, *args, **kwds):
        DockablePanelHeaderButton.Close(self, *args, **kwds)
        self.callback = None
        self.tooltipPanelMenu = None

    def UpdateButtonState(self):
        currentSetting = GetPanelSettings(self.panelID)
        align = currentSetting['align']
        if align == uiconst.TOALL:
            buttonID = BUTTON_FULLSCREEN
        elif align == uiconst.TOLEFT:
            buttonID = BUTTON_DOCKLEFT
        elif align == uiconst.TORIGHT:
            buttonID = BUTTON_DOCKRIGHT
        else:
            buttonID = BUTTON_FLOAT
        texturePath, label = BUTTON_DATA_BY_ID[buttonID]
        self.SetTexturePath(texturePath)

    def GetTooltipPointer(self):
        return uiconst.POINT_TOP_1

    def GetTooltipDelay(self):
        return 5

    def GetTooltipPositionFallbacks(self, *args, **kwds):
        return [uiconst.POINT_TOP_2,
         uiconst.POINT_TOP_1,
         uiconst.POINT_TOP_3,
         uiconst.POINT_BOTTOM_2,
         uiconst.POINT_BOTTOM_1,
         uiconst.POINT_BOTTOM_3]

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.columns = 2
        tooltipPanel.margin = 4
        for buttonID in (BUTTON_FULLSCREEN,
         BUTTON_DOCKLEFT,
         BUTTON_DOCKRIGHT,
         BUTTON_FLOAT):
            texturePath, label = BUTTON_DATA_BY_ID[buttonID]
            tooltipPanel.AddRow(rowClass=ButtonTooltipRow, buttonID=buttonID, texturePath=texturePath, label=label, callback=self._LocalCallback)

        tooltipPanel.state = uiconst.UI_NORMAL
        self.tooltipPanelMenu = tooltipPanel

    def _LocalCallback(self, buttonID):
        if self.tooltipPanelMenu and not self.tooltipPanelMenu.destroyed:
            self.tooltipPanelMenu.state = uiconst.UI_HIDDEN
        if self.callback:
            self.callback(buttonID)
        self.UpdateButtonState()


class ButtonTooltipRow(LayoutGridRow):
    default_state = uiconst.UI_NORMAL
    callback = None
    buttonID = None

    def ApplyAttributes(self, attributes):
        LayoutGridRow.ApplyAttributes(self, attributes)
        self.callback = attributes.callback
        self.buttonID = attributes.buttonID
        self.icon = ButtonIcon(pos=(0, 0, 16, 16), texturePath=attributes.texturePath, state=uiconst.UI_DISABLED)
        self.AddCell(cellObject=self.icon, cellPadding=(3, 2, 3, 2))
        label = EveLabelMedium(text=attributes.label, align=uiconst.CENTERLEFT)
        self.AddCell(cellObject=label, cellPadding=(0, 1, 6, 1))
        self.highLight = Fill(bgParent=self, color=(1, 1, 1, 0.1), state=uiconst.UI_HIDDEN)

    def Close(self, *args):
        LayoutGridRow.Close(self, *args)
        self.callback = None

    def OnMouseEnter(self, *args):
        self.icon.OnMouseEnter()
        self.highLight.display = True

    def OnMouseExit(self, *args):
        self.icon.OnMouseExit()
        self.highLight.display = False

    def OnClick(self, *args):
        if self.callback:
            self.callback(self.buttonID)


class DockablePanel(Window):
    __guid__ = 'form.DockablePanel'
    default_captionLabelPath = None
    default_isStackable = False
    panelSize = (500, 500)
    panelID = None
    toolbarContainer = None

    def ApplyAttributes(self, attributes):
        attributes.windowID = attributes.panelID or self.panelID
        Window.ApplyAttributes(self, attributes)
        if getattr(uicore, 'dockablePanelManager', None) is None:
            uicore.dockablePanelManager = DockablePanelManager()
        self.MakeUnMinimizable()
        self.MakeUnpinable()
        self.SetTopparentHeight(0)
        mainArea = self.GetMainArea()
        mainArea.padding = 2
        self.CreateToolbar()
        captionLabelPath = attributes.captionLabelPath or self.default_captionLabelPath
        if captionLabelPath:
            self.SetCaption(localization.GetByLabel(captionLabelPath))
        self.panelID = attributes.panelID or self.panelID
        uicore.dockablePanelManager.RegisterPanel(self)

    def InitializeStatesAndPosition(self, *args, **kw):
        self.InitDockPanelPosition()

    def InitDockPanelPosition(self):
        current = self.GetPanelSettings()
        if current['align'] == uiconst.TOPLEFT:
            self.UnDock()
        elif current['align'] == uiconst.TOLEFT:
            self.DockOnLeft()
        elif current['align'] == uiconst.TORIGHT:
            self.DockOnRight()
        elif current['align'] == uiconst.TOALL:
            self.DockFullscreen()
        self.state = uiconst.UI_NORMAL
        neocom = sm.GetService('neocom').neocom
        if neocom:
            neocom.SetOrder(0)

    def GetAbsolutePosition(self):
        stack = self.GetStack()
        if stack:
            return stack.sr.content.GetAbsolutePosition()
        return Base.GetAbsolutePosition(self)

    def InitializeSize(self, *args, **kwds):
        pass

    def RegisterPositionAndSize(self, *args, **kwds):
        pass

    def Prepare_HeaderButtons_(self, *args, **kwds):
        pass

    def OnDblClick(self, *args, **kwds):
        pass

    def ToggleCollapse(self, *args, **kwds):
        pass

    def Collapse(self, *args, **kwds):
        pass

    def Minimize(self, *args, **kwds):
        pass

    def Maximize(self, *args, **kwds):
        pass

    def GetMinWidth(self):
        return MINWIDTH

    def GetMinHeight(self):
        return MINHEIGHT

    def Prepare_Header_(self):
        if self.sr.headerParent:
            self.sr.headerParent.Close()
        self.sr.headerParent = Container(parent=self.sr.maincontainer, name='__headerParent', state=uiconst.UI_NORMAL, align=uiconst.TOTOP_NOPUSH, clipChildren=True, pos=(0,
         0,
         0,
         TOOLBARHEIGHT + 2), padding=2, idx=0)
        self.headerParent = self.sr.headerParent
        self.headerParent.DelegateEvents(self)

    @classmethod
    def ClosePanel(cls, *args, **kwds):
        if getattr(uicore, 'dockablePanelManager', None) is None:
            uicore.dockablePanelManager = DockablePanelManager()
        panel = uicore.dockablePanelManager.GetPanel(cls.panelID)
        if panel:
            panel.Close()
            return True
        return False

    @classmethod
    def OpenPanel(cls, *args, **kwds):
        if getattr(uicore, 'dockablePanelManager', None) is None:
            uicore.dockablePanelManager = DockablePanelManager()
        panel = uicore.dockablePanelManager.GetPanel(cls.panelID)
        if panel is None:
            return cls(*args, **kwds)

    def CreateToolbar(self):
        self.toolbarContainer = Container(parent=self.headerParent, align=uiconst.CENTERTOP, width=TOOLBARWIDTH_FULLSCREEN, height=TOOLBARHEIGHT)
        self.caption = EveLabelMedium(parent=self.toolbarContainer, align=uiconst.CENTER, bold=True)
        FillThemeColored(bgParent=self.toolbarContainer, opacity=0.9, padding=(1, 1, 1, 0))
        grid = LayoutGrid(parent=self.toolbarContainer, columns=5, cellPadding=2, align=uiconst.CENTERRIGHT, left=6, opacity=0.6)
        dockViewMode = DockablePanelHeaderButtonMenu(parent=grid, dockViewModeCallback=self.ChangeViewMode, panelID=self.panelID)
        closeButton = DockablePanelHeaderButton(parent=grid, hint='Close', texturePath='res:/UI/Texture/classes/DockPanel/closeButton.png', func=self.CloseByUser)
        tOutline = StretchSpriteHorizontalThemeColored(texturePath='res:/UI/Texture/classes/MapView/toolbarLine.png', colorType=uiconst.COLORTYPE_UIHILIGHT, opacity=uiconst.OPACITY_FRAME, leftEdgeSize=64, rightEdgeSize=64, parent=self.toolbarContainer, align=uiconst.TOBOTTOM_NOPUSH, padding=(-48, 0, -48, -15), height=64)
        tFill = StretchSpriteHorizontalThemeColored(texturePath='res:/UI/Texture/classes/MapView/toolbarFill.png', colorType=uiconst.COLORTYPE_UIBASE, leftEdgeSize=64, rightEdgeSize=64, parent=self.toolbarContainer, align=uiconst.TOBOTTOM_NOPUSH, padding=(-48, 0, -48, -15), height=64)

    def Close(self, *args):
        Window.Close(self, *args)
        if self.toolbarContainer and not self.toolbarContainer.destroyed:
            self.toolbarContainer.Close()
        self.monitorMouseOver = None
        uicore.dockablePanelManager.UnregisterPanel(self)

    def ChangeViewMode(self, buttonID, *args, **kwds):
        if buttonID == BUTTON_FULLSCREEN:
            if not self.IsFullscreen():
                self.DockFullscreen()
        elif buttonID == BUTTON_DOCKLEFT:
            self.DockOnLeft()
        elif buttonID == BUTTON_DOCKRIGHT:
            self.DockOnRight()
        else:
            self.UnDock()

    def SetCaption(self, captionText, *args, **kwds):
        self.caption.text = captionText
        self._caption = captionText

    def GetCaption(self, *args, **kwds):
        return self.caption.text

    def IsFullscreen(self):
        return self.align == uiconst.TOALL

    def IsDockedLeft(self):
        return self.align == uiconst.TOLEFT

    def IsDockedRight(self):
        return self.align == uiconst.TORIGHT

    @apply
    def displayRect():
        fget = Container.displayRect.fget

        def fset(self, value):
            Container.displayRect.fset(self, value)
            uicore.dockablePanelManager.UpdateCameraCenter()

        return property(**locals())

    def GetPanelSettings(self):
        return GetPanelSettings(self.panelID)

    def RegisterPanelSettings(self):
        if not self.panelID:
            return
        current = self.GetPanelSettings()
        current['align'] = self.align
        if self.align == uiconst.TOPLEFT:
            current['positionX'] = (self.left + self.width / 2) / float(uicore.desktop.width)
            current['positionY'] = (self.top + self.height / 2) / float(uicore.desktop.height)
            current['heightProportion'] = self.height / float(uicore.desktop.height)
            current['widthProportion'] = self.width / float(uicore.desktop.width)
        elif self.align in (uiconst.TOLEFT, uiconst.TORIGHT):
            current['widthProportion_docked'] = self.width / float(uicore.desktop.width)
            current['heightProportion_docked'] = 1.0
        settings.user.ui.Set(SETTINGSKEY % self.panelID, current)

    def LoadPanelSettings(self):
        current = self.GetPanelSettings()
        if current['align'] == uiconst.TOPLEFT:
            self.UnDock()
        elif current['align'] == uiconst.TOLEFT:
            self.DockOnLeft()
        elif current['align'] == uiconst.TORIGHT:
            self.DockOnRight()
        elif current['align'] == uiconst.TOALL:
            self.DockFullscreen()

    def CloseByUser(self, *args):
        uthread.new(self.Close)

    def StartScale(self, sender, btn, *args):
        if self.align == uiconst.TOALL:
            return
        self.scaleData = (self.left,
         self.top,
         self.width,
         self.height)
        scalerName = sender.name
        if 'Left' in scalerName and self.align != uiconst.TOLEFT:
            modX = -1
        elif 'Right' in scalerName and self.align != uiconst.TORIGHT:
            modX = 1
        else:
            modX = 0
        if 'Top' in scalerName:
            modY = -1
        elif 'Bottom' in scalerName:
            modY = 1
        else:
            modY = 0
        if not (modX or modY):
            return
        self.scaleModifiers = (modX, modY)
        self._scaling = True
        uthread.new(self.OnScale, uicore.uilib.x, uicore.uilib.y)

    def OnScale(self, initMouseX, initMouseY):
        while self._scaling and uicore.uilib.leftbtn and not self.destroyed:
            mouseX, mouseY = uicore.uilib.x, uicore.uilib.y
            dX = mouseX - initMouseX
            dY = mouseY - initMouseY
            l, t, w, h = self.scaleData
            widthMod, heightMod = self.scaleModifiers
            if widthMod:
                newWidth = max(MINWIDTH, w - dX * -widthMod)
                if self.align in (uiconst.TOLEFT, uiconst.TORIGHT):
                    newWidth = min(uicore.desktop.width / 2, newWidth)
                self.width = newWidth
                if widthMod < 0 and self.align == uiconst.TOPLEFT:
                    self.left = l + w - newWidth
            if heightMod and self.align == uiconst.TOPLEFT:
                newHeight = max(MINHEIGHT, h - dY * -heightMod)
                self.height = newHeight
                if heightMod < 0:
                    self.top = t + h - newHeight
            self.RegisterPanelSettings()
            blue.pyos.synchro.SleepWallclock(1)

    def OnScaleMove(self, dX, dY, scaleModifiers):
        if self.align == uiconst.TOALL:
            return
        l, t, w, h = self.scaleData
        widthMod, heightMod = self.scaleModifiers
        if widthMod:
            newWidth = max(MINWIDTH, w - dX * -widthMod)
            self.width = newWidth
            if widthMod < 0 and self.align == uiconst.TOPLEFT:
                self.left = l + w - newWidth
        if heightMod and self.align == uiconst.TOPLEFT:
            newHeight = max(MINHEIGHT, h - dY * -heightMod)
            self.height = newHeight
            if heightMod < 0:
                self.top = t + h - newHeight
        self.RegisterPanelSettings()

    def DockFullscreen(self, *args):
        sm.GetService('viewState').ToggleSecondaryView('dockpanelview')
        if self.destroyed:
            return
        self.SetParent(sm.GetService('viewState').GetView('dockpanelview').layer, idx=0)
        self.toolbarContainer.align = uiconst.CENTERTOP
        desktopIndex = uicore.desktop.children.index(uicore.layer.menu) + 1
        self.toolbarContainer.SetParent(uicore.desktop, idx=desktopIndex)
        self.align = uiconst.TOALL
        self.width = 0
        self.height = 0
        self.left = 0
        self.top = 0
        self.dragEnabled = False
        self.RegisterPanelSettings()
        uicore.dockablePanelManager.CheckViewState()
        self.OnDockModeChanged(self)

    def DockOnRight(self, *args):
        self._DockOnSide(align=uiconst.TORIGHT)

    def DockOnLeft(self, *args):
        self._DockOnSide(align=uiconst.TOLEFT)

    def _DockOnSide(self, align):
        current = self.GetPanelSettings()
        self.SetParent(uicore.layer.sidePanels, idx=0)
        self.toolbarContainer.align = uiconst.TOTOP_NOPUSH
        self.toolbarContainer.SetParent(self.headerParent, idx=0)
        self.align = align
        self.width = max(MINWIDTH, int(current['widthProportion_docked'] * uicore.desktop.width))
        self.height = 0
        self.left = 0
        self.top = 0
        self.RegisterPanelSettings()
        uicore.dockablePanelManager.CheckViewState()
        self.OnDockModeChanged(self)
        neocom = sm.GetService('neocom').neocom
        if neocom:
            neocom.SetOrder(0)

    def UnDock(self, *args):
        current = self.GetPanelSettings()
        self.SetParent(uicore.layer.main, idx=0)
        self.toolbarContainer.align = uiconst.TOTOP_NOPUSH
        self.toolbarContainer.SetParent(self.headerParent, idx=0)
        self.align = uiconst.TOPLEFT
        self.width = max(MINWIDTH, int(current['widthProportion'] * uicore.desktop.width))
        self.height = max(MINHEIGHT, int(current['heightProportion'] * uicore.desktop.height))
        self.left = int(uicore.desktop.width * current['positionX']) - self.width / 2
        self.top = int(uicore.desktop.height * current['positionY']) - self.height / 2
        self.RegisterPanelSettings()
        uicore.dockablePanelManager.CheckViewState()
        self.OnDockModeChanged(self)

    def OnDockModeChanged(self, *args, **kwds):
        pass

    def OnDragTick(self, *args, **kwds):
        self.RegisterPanelSettings()
