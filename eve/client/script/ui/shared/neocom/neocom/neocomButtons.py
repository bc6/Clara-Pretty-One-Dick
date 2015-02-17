#Embedded file name: eve/client/script/ui/shared/neocom/neocom\neocomButtons.py
"""
Classes that represent the buttons of the neocom. Each button is tied to a btnData
instance, managed by the neocomSvc.
"""
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import SpriteThemeColored, FrameThemeColored, LabelThemeColored
import uiprimitives
import uicontrols
from eve.client.script.ui.tooltips.tooltipUtil import RefreshTooltipForOwner
import util
import uthread
import math
import blue
import log
import localization
import trinity
import uix
import uiutil
import neocomPanels
import neocomCommon
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.shared.neocom.neocom.neocomCommon import BTNTYPE_WINDOW
import carbonui.const as uiconst

class ButtonBase(uiprimitives.Container):
    """
    An abstract button that others inherit from
    """
    __guid__ = 'neocom.ButtonBase'
    __notifyevents__ = ['ProcessNeocomBlinkPulse']
    default_name = 'ButtonBase'
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_isDraggable = True
    PADHORIZONTAL = 6
    PADVERTICAL = 4
    ACTIVEFILL_DEFAULTALPHA = 0.5
    ACTIVEFILL_HOVERALPHA = 0.8

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.btnData = attributes.btnData
        self.btnNum = attributes.btnNum
        self.width = attributes.width
        self._isDraggable = attributes.get('isDraggable', self.default_isDraggable)
        self._openNeocomPanel = None
        self.height = self.width
        self.top = self.height * self.btnNum
        self.panel = None
        self.blinkThread = None
        self.realTop = self.top
        self.dragEventCookie = None
        self.disableClick = False
        self.iconSize = self.height - 2 * self.PADVERTICAL
        self.iconTransform = uiprimitives.Transform(name='iconTransform', parent=self, align=uiconst.TOALL, scalingCenter=(0.5, 0.5))
        self.iconLabelCont = None
        if self.btnData.id == 'map_beta':
            Sprite(parent=self.iconTransform, align=uiconst.TOPLEFT, pos=(0, 0, 11, 29), texturePath='res:/UI/Texture/Shared/betaTag.png', state=uiconst.UI_DISABLED)
        self.icon = GlowSprite(parent=self.iconTransform, name='icon', state=uiconst.UI_DISABLED, align=uiconst.CENTER, width=self.iconSize, height=self.iconSize, iconOpacity=1.0)
        self.UpdateIcon()
        PAD = 1
        self.blinkSprite = SpriteThemeColored(bgParent=self, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonBlink.png', state=uiconst.UI_HIDDEN, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)
        self.activeFrame = FrameThemeColored(bgParent=self, name='hoverFill', texturePath='res:/UI/Texture/classes/Neocom/buttonActive.png', cornerSize=5, state=uiconst.UI_HIDDEN, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)
        self.CheckIfActive()
        self.dropFrame = uicontrols.Frame(parent=self, name='hoverFrame', color=util.Color.GetGrayRGBA(1.0, 0.5), state=uiconst.UI_HIDDEN)
        sm.RegisterNotify(self)

    def UpdateIcon(self):
        texturePath = self._GetPathFromIconNum(self.btnData.iconPath)
        self.icon.SetTexturePath(texturePath)

    def CheckIfActive(self):
        if self.btnData.isActive:
            self.activeFrame.Show()
        else:
            self.activeFrame.Hide()

    def GetIconPath(self):
        return self._GetPathFromIconNum(self.btnData.iconPath)

    def _GetPathFromIconNum(self, iconNum):
        if iconNum.startswith('res:/'):
            return iconNum
        parts = iconNum.split('_')
        if len(parts) == 2:
            sheet, iconNum = parts
            iconSize = uix.GetIconSize(sheet)
            return 'res:/ui/texture/icons/%s_%s_%s.png' % (int(sheet), int(iconSize), int(iconNum))
        elif len(parts) == 4:
            root, sheet, iconSize, iconNum = parts
            if root == 'ui':
                root = 'icons'
            return 'res:/ui/texture/%s/%s_%s_%s.png' % (root,
             int(sheet),
             int(iconSize),
             int(iconNum))
        else:
            return neocomCommon.ICONPATH_DEFAULT

    def IsDraggable(self):
        return self._isDraggable

    def SetDraggable(self, isDraggable):
        self._isDraggable = isDraggable

    def GetMenu(self):
        return self.btnData.GetMenu()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        if isOpen:
            return
        tooltipPanel.LoadGeneric3ColumnTemplate()
        blinkHintStr = None
        if getattr(self.btnData, 'cmdName', None):
            cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
            tooltipPanel.AddCommandTooltip(cmd)
            blinkHintStr = self.btnData.blinkHint
        else:
            label = None
            if self.IsSingleWindow():
                wnd = self.GetWindow()
                if not wnd.destroyed:
                    label = wnd.GetCaption()
            elif self.btnData.children:
                label = self.btnData.children[0].wnd.GetNeocomGroupLabel()
            mainStr = label or self.btnData.label
            tooltipPanel.AddLabelMedium(text=mainStr)
        self.LoadTooltipPanelDetails(tooltipPanel, self.btnData)
        if blinkHintStr:
            tooltipPanel.AddLabelMedium(text=blinkHintStr, width=200, colSpan=tooltipPanel.columns)

    def LoadTooltipPanelDetails(cls, tooltipPanel, btnData):
        if btnData.id == 'wallet':
            showFractions = settings.char.ui.Get('walletShowCents', False)
            personalWealth = util.FmtISK(sm.GetService('wallet').GetWealth(), showFractions)
            tooltipPanel.AddLabelValue(label=localization.GetByLabel('Tooltips/Neocom/Balance'), value=personalWealth)
            canAccess = sm.GetService('wallet').HaveReadAccessToCorpWalletDivision(session.corpAccountKey)
            if canAccess:
                corpWealth = util.FmtISK(sm.GetService('wallet').GetCorpWealthCached1Min(session.corpAccountKey), showFractions)
                tooltipPanel.AddLabelValue(label=localization.GetByLabel('Tooltips/Neocom/CorporationBalance'), value=corpWealth)

    def GetTooltipPointer(self):
        return uiconst.POINT_LEFT_2

    def IsSingleWindow(self):
        return False

    def OnMouseEnter(self, *args):
        self.btnData.SetBlinkingOff()
        self.icon.OnMouseEnter()

    def OnMouseExit(self, *args):
        self.icon.OnMouseExit()

    def OnMouseDown(self, *args):
        if not self.IsDraggable():
            return
        if not uicore.uilib.leftbtn:
            return
        self.isDragging = False
        self.mouseDownY = uicore.uilib.y
        if self.dragEventCookie is not None:
            uicore.event.UnregisterForTriuiEvents(self.dragEventCookie)
        self.dragEventCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEMOVE, self.OnDrag)
        uicore.animations.Tr2DScaleTo(self.iconTransform, self.iconTransform.scale, (0.95, 0.95), duration=0.1)
        self.icon.OnMouseDown()

    def OnMouseUp(self, *args):
        if uicore.uilib.mouseOver == self:
            uicore.animations.Tr2DScaleTo(self.iconTransform, self.iconTransform.scale, (1.0, 1.0), duration=0.1)
        if self.dragEventCookie is not None:
            uicore.event.UnregisterForTriuiEvents(self.dragEventCookie)
            self.dragEventCookie = None
        self.icon.OnMouseUp()

    def OnDragEnd(self, *args):
        uicore.event.UnregisterForTriuiEvents(self.dragEventCookie)
        self.dragEventCookie = None
        self.isDragging = False
        sm.GetService('neocom').OnButtonDragEnd(self)
        self.CheckIfActive()

    def OnDrag(self, *args):
        if math.fabs(self.mouseDownY - uicore.uilib.y) > 5 or self.isDragging:
            if not self.isDragging:
                uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnDragEnd)
            self.disableClick = True
            self.isDragging = True
            sm.GetService('neocom').OnButtonDragged(self)
        return True

    def OnClick(self, *args):
        if not self or self.destroyed:
            return
        self.btnData.CheckContinueBlinking()
        if not self.disableClick:
            self.OnClickCommand()
        if not self or self.destroyed:
            return
        self.disableClick = False
        if self.dragEventCookie:
            uicore.event.UnregisterForTriuiEvents(self.dragEventCookie)

    def OnDblClick(self, *args):
        """ Swallow double click event so that we don't get two OnClick events """
        pass

    def OnClickCommand(self):
        """
        Overridden by subclasses
        """
        pass

    def OnSwitched(self):
        uicore.effect.MorphUIMassSpringDamper(item=self, attrname='opacity', float=1, newVal=1.0, minVal=0, maxVal=2.0, dampRatio=0.45, frequency=15.0, initSpeed=0, maxTime=4.0, callback=None, initVal=0.0)
        self.isDragging = False
        self.disableClick = False

    def GetDragData(self, *args):
        if self.btnData.isDraggable:
            return [self.btnData]

    def BlinkOnce(self, duration = 0.7):
        self.blinkSprite.Show()
        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi * 0.75, duration=duration)

    def ProcessNeocomBlinkPulse(self):
        if self.btnData.isBlinking:
            self.BlinkOnce()

    def OnDropData(self, source, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        index = self.btnData.parent.children.index(self.btnData)
        sm.GetService('neocom').OnBtnDataDropped(dropData[0], index)

    def OnDragEnter(self, panelEntry, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        sm.GetService('neocom').OnButtonDragEnter(self.btnData, dropData[0])
        uthread.new(self.ShowPanelOnMouseHoverThread)

    def OnDragExit(self, *args):
        sm.GetService('neocom').OnButtonDragExit(self.btnData, args)

    def ToggleNeocomPanel(self):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        sm.GetService('neocom').CloseAllPanels()
        if isOpen:
            self._openNeocomPanel = None
        else:
            self._openNeocomPanel = sm.GetService('neocom').ShowPanel(triggerCont=self, panelClass=self.GetPanelClass(), panelAlign=neocomCommon.PANEL_SHOWONSIDE, parent=uicore.layer.abovemain, btnData=self.btnData)
        RefreshTooltipForOwner(self)

    def ShowPanelOnMouseHoverThread(self):
        if len(self.btnData.children) <= 1:
            return
        blue.pyos.synchro.Sleep(500)
        if not self or self.destroyed:
            return
        if uicore.uilib.mouseOver == self:
            self.ToggleNeocomPanel()

    def GetPanelClass(self):
        return neocomPanels.PanelGroup

    def SetAsActive(self):
        self.btnData.isActive = True
        self.activeFrame.state = uiconst.UI_DISABLED

    def SetAsInactive(self):
        self.btnData.isActive = False
        self.activeFrame.state = uiconst.UI_HIDDEN


class ButtonWindow(ButtonBase):
    """
    A button tied to an instance of uicontrols.Window that is not already represented by a
    BtnCmd. More than one window instances of the same class will be grouped and rather 
    than toggling the window, a neocom.PanelGroup will be shown on click in those cases.
    """
    __guid__ = 'neocom.ButtonWindow'
    default_name = 'ButtonWindow'

    def OnClickCommand(self):
        if self.IsSingleWindow():
            if not getattr(self.GetWindow(), 'isImplanted', False):
                uicore.cmd.TryLogWindowOpenedFromMinimize(self.GetWindow())
                uthread.new(self.GetWindow().ToggleMinimize)
            else:
                cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
                uicore.cmd.ExecuteCommand(cmd)
        elif self.btnData.children:
            self.ToggleNeocomPanel()
        elif hasattr(self.btnData, 'cmdName'):
            cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
            uicore.cmd.ExecuteCommand(cmd)

    def IsSingleWindow(self):
        """Is there a single, open window associated with this button?"""
        return len(self.btnData.children) == 1

    def GetWindow(self):
        if self.btnData.children:
            btnData = self.btnData.children[0]
            return btnData.wnd

    def GetAllWindows(self):
        wnds = []
        for btnData in self.btnData.children:
            wnds.append(btnData.wnd)

        return wnds

    def GetMenu(self):
        if self.IsSingleWindow():
            wnd = self.GetWindow()
            if wnd and wnd.GetMenu:
                return wnd.GetMenu()
        else:
            if self.btnData.children:
                for wnd in self.GetAllWindows():
                    if not wnd.IsKillable():
                        return None

                return [(uiutil.MenuLabel('/Carbon/UI/Commands/CmdCloseAllWindows'), self.CloseAllWindows)]
            if self.btnData.btnType in neocomCommon.COMMAND_BTNTYPES:
                return ButtonBase.GetMenu(self)

    def CloseAllWindows(self):
        for wnd in self.GetAllWindows():
            wnd.CloseByUser()

    def OnDragEnter(self, panelEntry, nodes):
        if sm.GetService('neocom').IsValidDropData(nodes):
            ButtonBase.OnDragEnter(self, panelEntry, nodes)
        elif self.btnData.btnType == neocomCommon.BTNTYPE_WINDOW:
            self.dropFrame.state = uiconst.UI_DISABLED
            self.OnMouseEnter()
            uthread.new(self.ShowPanelOnMouseHoverThread)

    def OnDragExit(self, *args):
        self.dropFrame.state = uiconst.UI_HIDDEN
        self.OnMouseExit()

    def OnDropData(self, source, nodes):
        if sm.GetService('neocom').IsValidDropData(nodes):
            index = self.btnData.parent.children.index(self.btnData)
            sm.GetService('neocom').OnBtnDataDropped(nodes[0], index)
        elif self.IsSingleWindow():
            wnd = self.GetWindow()
            if hasattr(wnd, 'OnDropData'):
                if wnd.OnDropData(source, nodes):
                    self.BlinkOnce(0.3)
        elif not self.GetAllWindows():
            wndCls = self.btnData.wndCls
            if wndCls and hasattr(wndCls, 'OnDropDataCls'):
                if wndCls.OnDropDataCls(source, nodes):
                    self.BlinkOnce(0.3)
        self.dropFrame.state = uiconst.UI_HIDDEN

    def UpdateIcon(self):
        """ Update button icon, depending on if the window represents no, one or multiple open windows """
        if self.iconLabelCont:
            self.iconLabelCont.Close()
        wnd = self.GetWindow()
        if not wnd:
            iconNum = self.btnData.iconPath
        elif self.IsSingleWindow():
            iconNum = wnd.iconNum
        else:
            wnds = self.GetAllWindows()
            iconNum = wnds[0].GetNeocomGroupIcon()
            self.iconLabelCont = uiprimitives.Container(parent=self.iconTransform, align=uiconst.TOPRIGHT, pos=(1, 1, 13, 13), idx=0, bgColor=util.Color.GetGrayRGBA(0.7, 0.2))
            uicontrols.Label(parent=self.iconLabelCont, align=uiconst.CENTER, text='<b>%s' % len(wnds), fontsize=10, letterspace=-1)
        self.icon.SetTexturePath(self._GetPathFromIconNum(iconNum))


class ButtonInventory(ButtonWindow):
    """
    A button tied to an inventory location
    """
    __guid__ = 'neocom.ButtonInventory'
    default_name = 'ButtonInventory'

    def OnDragEnter(self, panelEntry, nodes):
        if not self._IsValidDropData(nodes):
            return
        self.dropFrame.state = uiconst.UI_DISABLED
        self.OnMouseEnter()

    def OnDragExit(self, *args):
        self.dropFrame.state = uiconst.UI_HIDDEN
        self.OnMouseExit()

    def OnDropData(self, source, nodes):
        if not self._IsValidDropData(nodes):
            return
        inv = []
        for node in nodes:
            if node.Get('__guid__', None) in ('xtriui.InvItem', 'listentry.InvItem'):
                inv.append(node.itemID)
                locationID = node.rec.locationID

        if inv:
            sm.GetService('invCache').GetInventoryFromId(self.btnData.invLocationID).MultiAdd(inv, locationID, flag=self.btnData.invFlagID)
        self.dropFrame.state = uiconst.UI_HIDDEN

    def _IsValidDropData(self, nodes):
        if not nodes:
            return False
        for node in nodes:
            if node.Get('__guid__', None) in ('xtriui.InvItem', 'listentry.InvItem'):
                return True

        return False


class ButtonTwitch(ButtonWindow):
    default_name = 'ButtonTwitch'
    __notifyevents__ = ('OnTwitchStreamingStateChange',)

    def ApplyAttributes(self, attributes):
        ButtonWindow.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)

    def UpdateIcon(self):
        import twitch
        if twitch.is_streaming():
            self.icon.SetTexturePath('res:/UI/Texture/windowIcons/twitch_recording.png')
        else:
            self.icon.SetTexturePath('res:/UI/Texture/windowIcons/twitch.png')

    def OnTwitchStreamingStateChange(self, *args):
        self.UpdateIcon()


class ButtonGroup(ButtonBase):
    """
    A button representing a neocom group. Opens up a neocom.PanelGroup representing
    it's btnData.children on click.
    """
    __guid__ = 'neocom.ButtonGroup'
    default_name = 'ButtonGroup'

    def ApplyAttributes(self, attributes):
        ButtonBase.ApplyAttributes(self, attributes)
        if self.btnData.labelAbbrev:
            label = LabelThemeColored(parent=self.iconTransform, align=uiconst.CENTERBOTTOM, text=self.btnData.labelAbbrev, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, fontsize=13, opacity=1.0, top=6, idx=0, bold=True)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        if isOpen:
            return
        tooltipPanel.LoadGeneric1ColumnTemplate()
        tooltipPanel.AddLabelMedium(text=self.btnData.label)

    def OnClickCommand(self):
        self.ToggleNeocomPanel()

    def OnMouseEnter(self, *args):
        self.icon.OnMouseEnter()

    def OnDragEnter(self, source, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        self.dropFrame.state = uiconst.UI_DISABLED
        self.OnMouseEnter()
        uthread.new(self.ShowPanelOnMouseHoverThread)

    def OnDragExit(self, *args):
        self.dropFrame.state = uiconst.UI_HIDDEN
        self.OnMouseExit()

    def OnDropData(self, source, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        btnData = dropData[0]
        oldHeadNode = btnData.GetHeadNode()
        btnData.MoveTo(self.btnData)
        if oldHeadNode == sm.GetService('neocom').eveMenuBtnData:
            btnData.isRemovable = True
        sm.GetService('neocom').ResetEveMenuBtnData()


class ButtonChat(ButtonBase):
    """
    A special button that toggles a neocom.PanelChat which shows all open chat channels
    """
    __guid__ = 'neocom.ButtonChat'
    __notifyevents__ = ['ProcessNeocomBlinkPulse']
    default_name = 'ButtonChat'

    def ApplyAttributes(self, attributes):
        sm.RegisterNotify(self)
        ButtonBase.ApplyAttributes(self, attributes)
        self.activeFrame.state = uiconst.UI_DISABLED

    def OnClickCommand(self):
        uthread.new(self.ToggleNeocomPanel)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        if isOpen:
            return
        tooltipPanel.LoadGeneric3ColumnTemplate()
        cmd = uicore.cmd.commandMap.GetCommandByName('OpenChannels')
        tooltipPanel.AddCommandTooltip(cmd)

    def CheckIfActive(self):
        """ Always show chat button as active as we always have chat channels open """
        pass

    def SetAsInactive(self):
        """ Always show chat button as active as we always have chat channels open """
        pass


class ButtonBookmarks(ButtonBase):
    """
    A button which shows all bookmarked browser URLs
    """
    __guid__ = 'neocom.ButtonBookmarks'
    default_name = 'ButtonBookmarks'

    def OnClickCommand(self):
        self.ToggleNeocomPanel()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        if isOpen:
            return
        tooltipPanel.LoadGeneric1ColumnTemplate()
        tooltipPanel.AddLabelMedium(text=self.btnData.label)


class OverflowButton(uiprimitives.Container):
    """
    A button that toggles all buttons that are not visible in the neocom due to lack 
    of screen space
    """
    __guid__ = 'neocom.OverflowButton'
    __notifyevents__ = ['OnNeocomPanelsClosed', 'ProcessNeocomBlinkPulse']
    default_state = uiconst.UI_HIDDEN
    default_name = 'overflowButtonCont'
    default_pos = (0, 0, 20, 0)

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self._openNeocomPanel = None
        self.isBlinking = False
        self.hoverSprite = uiprimitives.Sprite(bgParent=self, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Neocom/buttonHover.png', blendMode=trinity.TR2_SBM_ADD, state=uiconst.UI_HIDDEN)
        self.blinkSprite = uiprimitives.Sprite(bgParent=self, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonBlink.png', state=uiconst.UI_HIDDEN)
        self.icon = uiprimitives.Sprite(parent=self, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', width=7, height=7, align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.UpdateIconRotation()

    def UpdateIconRotation(self):
        if settings.char.ui.Get('neocomAlign', uiconst.TOLEFT) == uiconst.TOLEFT:
            self.icon.rotation = math.pi / 2
        else:
            self.icon.rotation = -math.pi / 2

    def OnMouseEnter(self, *args):
        self.hoverSprite.state = uiconst.UI_DISABLED
        uicore.animations.SpMaskIn(self.hoverSprite, duration=0.5)

    def OnMouseExit(self, *args):
        uicore.animations.SpMaskOut(self.hoverSprite, duration=0.5)

    def OnMouseDown(self, *args):
        self.icon.opacity = 1.0

    def OnClick(self, *args):
        self.ToggleNeocomPanel()

    def OnDblClick(self, *args):
        """ Swallow double click event so that we don't get two OnClick events """
        pass

    def ToggleNeocomPanel(self):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        sm.GetService('neocom').CloseAllPanels()
        if isOpen:
            self._openNeocomPanel = None
        else:
            self._openNeocomPanel = sm.GetService('neocom').ShowPanel(self, neocomPanels.PanelOverflow, neocomCommon.PANEL_SHOWONSIDE, parent=uicore.layer.abovemain, btnData=None)
        RefreshTooltipForOwner(self)

    def BlinkOnce(self):
        self.blinkSprite.state = uiconst.UI_DISABLED
        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi, duration=0.7)

    def ProcessNeocomBlinkPulse(self):
        for btnData in sm.GetService('neocom').neocom.overflowButtons:
            if btnData.isBlinking:
                self.BlinkOnce()
                return


class WrapperButton(uiprimitives.Container):
    """
    Adds button functionality to clock and character containers
    """
    __guid__ = 'neocom.WrapperButton'
    __notifyevents__ = ['ProcessNeocomBlinkPulse']
    default_name = 'WrapperButton'
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.cmdName = attributes.cmdName
        self._openNeocomPanel = None
        self.cmd = uicore.cmd.commandMap.GetCommandByName(attributes.cmdName)
        self.blinkThread = None
        self.isBlinking = False
        self.mouseHoverSprite = SpriteThemeColored(parent=self, name='mouseHoverSprite', align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Neocom/eveButtonBg.png', blendMode=trinity.TR2_SBM_ADD, state=uiconst.UI_HIDDEN, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)
        self.mouseHoverSprite.Hide()
        self.blinkSprite = SpriteThemeColored(parent=self, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonBlink.png', state=uiconst.UI_HIDDEN, align=uiconst.TOALL, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)

    def OnClick(self, *args):
        self.cmd.callback()
        self.DisableBlink()

    def OnDblClick(self, *args):
        """ Swallow double click event so that we don't get two OnClick events """
        pass

    def OnMouseEnter(self, *args):
        self.DisableBlink()
        self.mouseHoverSprite.state = uiconst.UI_DISABLED
        uicore.animations.SpMaskIn(self.mouseHoverSprite, duration=0.5)

    def OnMouseExit(self, *args):
        uicore.animations.SpMaskOut(self.mouseHoverSprite, duration=0.5, callback=self.mouseHoverSprite.Hide)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        if isOpen:
            return
        tooltipPanel.LoadGeneric3ColumnTemplate()
        tooltipPanel.AddCommandTooltip(self.cmd)
        if self.cmdName == 'OpenCalendar':
            timeLabel = localization.formatters.FormatDateTime(blue.os.GetTime(), dateFormat='full', timeFormat=None)
            tooltipPanel.AddLabelMedium(text=timeLabel, colSpan=tooltipPanel.columns)
        elif self.cmdName == 'OpenSkillQueueWindow':
            trainingHintLabel = tooltipPanel.AddLabelMedium(text='', colSpan=tooltipPanel.columns)
            tooltipPanel.trainingHintLabel = trainingHintLabel
            self.UpdateSkillQueueTooltip_thread(tooltipPanel)
            self._skillqueueTooltipUpdate = AutoTimer(1000, self.UpdateSkillQueueTooltip_thread, tooltipPanel)

    def UpdateSkillQueueTooltip_thread(self, tooltipPanel):
        if tooltipPanel.destroyed:
            self._skillqueueTooltipUpdate = None
            return
        skill = sm.GetService('skills').SkillInTraining()
        if skill is None or skill.skillTrainingEnd is None:
            trainingHint = localization.GetByLabel('UI/Neocom/NoSkillHint')
        else:
            secUntilDone = max(0L, long(skill.skillTrainingEnd) - blue.os.GetTime())
            trainingHint = localization.GetByLabel('UI/Neocom/SkillTrainingHint', skillName=skill.name, skillLevel=skill.skillLevel + 1, time=secUntilDone)
        tooltipPanel.trainingHintLabel.text = trainingHint

    def EnableBlink(self):
        self.isBlinking = True

    def DisableBlink(self):
        self.isBlinking = False

    def BlinkOnce(self):
        self.blinkSprite.state = uiconst.UI_DISABLED
        uicore.animations.SpSwoopBlink(self.blinkSprite, duration=0.7)

    def ProcessNeocomBlinkPulse(self):
        if self.isBlinking:
            self.BlinkOnce()

    def GetMenu(self):
        return sm.GetService('neocom').GetMenu()


class ButtonEveMenu(WrapperButton):
    __guid__ = 'neocom.ButtonEveMenu'

    def ApplyAttributes(self, attributes):
        WrapperButton.ApplyAttributes(self, attributes)
        self.btnData = attributes.btnData
        GlowSprite(parent=self, name='EVEMenuIcon', align=uiconst.CENTER, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Icons/79_64_11.png', width=20, height=20, idx=0)
        SpriteThemeColored(bgParent=self, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Neocom/panelEntryBG.png', colorType=uiconst.COLORTYPE_UIHILIGHT)

    def OnClick(self, *args):
        self.ToggleNeocomPanel()
        self.btnData.CheckContinueBlinking()

    def ToggleNeocomPanel(self):
        isOpen = self._openNeocomPanel and not self._openNeocomPanel.destroyed
        sm.GetService('neocom').CloseAllPanels()
        if isOpen:
            self._openNeocomPanel = None
        else:
            self._openNeocomPanel = sm.GetService('neocom').ShowEveMenu()
        RefreshTooltipForOwner(self)

    def BlinkOnce(self):
        self.blinkSprite.state = uiconst.UI_DISABLED
        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi, duration=0.7)

    def ProcessNeocomBlinkPulse(self):
        if self.btnData.isBlinking:
            self.BlinkOnce()


def GetBtnClassByBtnType(btnData):
    if btnData.btnType == BTNTYPE_WINDOW and btnData.children:
        btnType = btnData.children[0].btnType
    else:
        btnType = btnData.btnType
    btnsByTypeID = {neocomCommon.BTNTYPE_CMD: ButtonWindow,
     neocomCommon.BTNTYPE_WINDOW: ButtonWindow,
     neocomCommon.BTNTYPE_GROUP: ButtonGroup,
     neocomCommon.BTNTYPE_CHAT: ButtonChat,
     neocomCommon.BTNTYPE_BOOKMARKS: ButtonBookmarks,
     neocomCommon.BTNTYPE_INVENTORY: ButtonInventory,
     neocomCommon.BTNTYPE_TWITCH: ButtonTwitch}
    if btnType not in btnsByTypeID:
        log.LogError('No neocom button Class defined for button type')
    return btnsByTypeID[btnType]


exports = {'neocom.GetBtnClassByBtnType': GetBtnClassByBtnType}
