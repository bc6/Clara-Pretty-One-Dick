#Embedded file name: eve/client/script/ui/shared/neocom/neocom\neocomPanelEntries.py
"""
Classes that represent neocom panel entries. Each panel entry type is tied to a btnData
instance, managed by the neocomSvc.
"""
import math
import carbonui.const as uiconst
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import SpriteThemeColored
import uiprimitives
import uicontrols
import uthread
import localization
import trinity
from eve.client.script.ui.shared.neocom.neocom.neocomButtons import ButtonBase
from . import neocomCommon

class PanelEntryBase(uiprimitives.Container):
    """
    An abstract panel entry that others inherit from
    """
    __guid__ = 'neocom.PanelEntryBase'
    __notifyevents__ = ['ProcessNeocomBlinkPulse']
    isDragObject = True
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOTOP
    default_icon = None
    default_height = 42

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.btnData = attributes.btnData
        if hasattr(self.btnData, 'panelEntryHeight'):
            self.height = self.btnData.panelEntryHeight
        self.blinkThread = None
        self._openNeocomPanel = None
        self.main = uiprimitives.Container(parent=self, name='main')
        self.hoverBG = uicontrols.Frame(bgParent=self.main, texturePath='res:/UI/Texture/classes/Neocom/panelEntryBG.png', opacity=0.0)
        size = self.height - 4
        self.icon = GlowSprite(parent=self.main, name='icon', state=uiconst.UI_DISABLED, texturePath=self.GetIconPath(), pos=(10,
         2,
         size,
         size), iconOpacity=0.75)
        self.label = uicontrols.Label(parent=self.main, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, text=self.GetLabel(), autowidth=True, autoheight=True, left=self.icon.left + self.icon.width + 8)
        if settings.char.ui.Get('neocomAlign', uiconst.TOLEFT) == uiconst.TOLEFT:
            rotation = 0.0
        else:
            rotation = math.pi
        self.expanderIcon = uicontrols.Icon(parent=self, name='expanderIcon', align=uiconst.CENTERRIGHT, left=10, icon='ui_38_16_228', rotation=rotation)
        self.SetExpanderState()
        self.blinkSprite = uiprimitives.Sprite(bgParent=self, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/panelEntryBG.png', state=uiconst.UI_HIDDEN, opacity=1.0)

    def GetIconPath(self):
        return self.btnData.iconPath or neocomCommon.ICONPATH_DEFAULT

    def PrepareDrag(self, dragContainer, dragSource):
        dragContainer.width = dragContainer.height = 48
        icon = uicontrols.Icon(parent=dragContainer, name='icon', state=uiconst.UI_DISABLED, icon=self.GetIconPath(), size=48, ignoreSize=True)
        Frame(parent=dragContainer, name='baseFrame', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/buttonDOT.png', color=(1.0, 1.0, 1.0, 1.0), cornerSize=8, spriteEffect=trinity.TR2_SFX_DOT, blendMode=trinity.TR2_SBM_ADD)
        Frame(parent=dragContainer, offset=-9, cornerSize=13, name='shadow', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/bigButtonShadow.png')
        return (0, 0)

    def HasOpenPanel(self):
        return self._openNeocomPanel is not None and not self._openNeocomPanel.destroyed

    def SetExpanderState(self):
        self.HideExpander()

    def ShowExpander(self):
        self.expanderIcon.state = uiconst.UI_DISABLED

    def HideExpander(self):
        self.expanderIcon.state = uiconst.UI_HIDDEN

    def OnClick(self, *args):
        self.btnData.CheckContinueBlinking()
        self.OnClickCommand()
        sm.GetService('neocom').CloseAllPanels()

    def OnClickCommand(self):
        """
        Overriden by subclasses
        """
        pass

    def GetLabel(self):
        label = None
        if self.btnData.cmdName:
            cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
            if cmd and cmd.callback:
                label = cmd.GetName()
        return label or self.btnData.label

    def GetRequiredWidth(self):
        return self.label.width + self.icon.width + 35

    def GetMenu(self):
        return self.btnData.GetMenu()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric3ColumnTemplate()
        if getattr(self.btnData, 'cmdName', None):
            cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
            tooltipPanel.AddCommandTooltip(cmd)
            ButtonBase.LoadTooltipPanelDetails(self, tooltipPanel, self.btnData)

    def GetTooltipPointer(self):
        return uiconst.POINT_LEFT_2

    def OnMouseEnter(self, *args):
        sm.GetService('neocom').CloseChildrenPanels(self.btnData.parent)
        uicore.animations.FadeIn(self.hoverBG, duration=0.3)
        self.icon.OnMouseEnter()

    def OnMouseExit(self, *args):
        uicore.animations.FadeOut(self.hoverBG, duration=0.3)
        self.icon.OnMouseExit()

    def GetDragData(self, *args):
        if self.btnData.isDraggable:
            return [self.btnData]

    def BlinkOnce(self):
        self.blinkSprite.Show()
        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi, duration=1.0)

    def ProcessNeocomBlinkPulse(self):
        if self.btnData.isBlinking:
            self.BlinkOnce()


class PanelEntryCmd(PanelEntryBase):
    """
    A panel entry tied to a command defined in eveCommands.py (usually opening a window)
    """
    __guid__ = 'neocom.PanelEntryCmd'
    default_name = 'PanelEntryCmd'

    def ApplyAttributes(self, attributes):
        PanelEntryBase.ApplyAttributes(self, attributes)
        self.func = attributes.func

    def OnClickCommand(self, *args):
        self.func()


class PanelEntryBookmarks(PanelEntryBase):
    """
    A panel entry which shows all bookmarked browser URLs
    """
    __guid__ = 'neocom.PanelEntryBookmarks'
    default_name = 'PanelEntryBookmarks'

    def OnClick(self, *args):
        if not self.HasOpenPanel():
            self.ToggleNeocomPanel()

    def ToggleNeocomPanel(self):
        from .neocomPanels import PanelGroup
        sm.GetService('neocom').CloseChildrenPanels(self.btnData.parent)
        if self.HasOpenPanel():
            self._openNeocomPanel = None
        else:
            self._openNeocomPanel = sm.GetService('neocom').ShowPanel(self, PanelGroup, neocomCommon.PANEL_SHOWONSIDE, parent=uicore.layer.abovemain, btnData=self.btnData)

    def OnMouseEnter(self, *args):
        PanelEntryBase.OnMouseEnter(self, *args)
        if uicore.uilib.mouseOver == self and not self.HasOpenPanel():
            uthread.new(self.ToggleNeocomPanel)

    def SetExpanderState(self):
        self.ShowExpander()


class PanelEntryBookmark(PanelEntryBase):
    """
    A panel entry that represent a single bookmarked browser URL and opens it on click
    """
    __guid__ = 'neocom.PanelEntryBookmark'
    default_name = 'PanelEntryBookmark'
    default_height = 25

    def ApplyAttributes(self, attributes):
        self.bookmark = attributes.btnData.bookmark
        PanelEntryBase.ApplyAttributes(self, attributes)

    def OnClickCommand(self, *args):
        uicore.cmd.OpenBrowser(url=self.bookmark.url, newTab=True)

    def GetLabel(self):
        return self.bookmark.name


class PanelEntryText(uiprimitives.Container):
    """
    A panel entry that is just dumb text. Does nothing on click.
    """
    __guid__ = 'neocom.PanelEntryText'
    default_name = 'PanelEntryText'
    default_height = 42
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        label = attributes.label
        self.label = uicontrols.Label(parent=self, state=uiconst.UI_DISABLED, text=label, align=uiconst.CENTERLEFT, left=10)

    def GetRequiredWidth(self):
        return self.label.width + 35


class PanelEntryGroup(PanelEntryBase):
    """
    A panel entry representing a neocom group. Opens up a neocom.PanelGroup representing
    it's btnData.children on click.
    """
    __guid__ = 'neocom.PanelEntryGroup'
    default_name = 'PanelEntryGroup'
    default_icon = neocomCommon.ICONPATH_GROUP

    def ApplyAttributes(self, attributes):
        PanelEntryBase.ApplyAttributes(self, attributes)
        if self.btnData.labelAbbrev:
            label = uicontrols.Label(parent=self.main, align=uiconst.CENTERLEFT, text='<b><color=0xFF203d3d>' + self.btnData.labelAbbrev, fontsize=16, opacity=0.75, letterspace=-1, idx=0, left=self.height / 2)

    def OnClick(self, *args):
        if not self.HasOpenPanel():
            self.ToggleNeocomPanel()

    def OnMouseEnter(self, *args):
        PanelEntryBase.OnMouseEnter(self, *args)
        if uicore.uilib.mouseOver == self and not self.HasOpenPanel():
            uthread.new(self.ToggleNeocomPanel)

    def OnDropData(self, source, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        btnData = dropData[0]
        if btnData.btnType not in neocomCommon.FIXED_PARENT_BTNTYPES:
            btnData.MoveTo(self.btnData)

    def ToggleNeocomPanel(self):
        from .neocomPanels import PanelGroup
        if self.HasOpenPanel():
            self._openNeocomPanel = None
            sm.GetService('neocom').CloseChildrenPanels(self.btnData.parent)
        else:
            sm.GetService('neocom').CloseChildrenPanels(self.btnData.parent)
            self._openNeocomPanel = sm.GetService('neocom').ShowPanel(self, PanelGroup, neocomCommon.PANEL_SHOWONSIDE, parent=uicore.layer.abovemain, btnData=self.btnData, align=uiconst.TOPLEFT)

    def SetExpanderState(self):
        self.ShowExpander()


class PanelEntryWindow(PanelEntryBase):
    """
    A panel entry tied to an instance of uicontrols.Window that is not already represented
    by a BtnCmd. More than one window instances of the same class will be grouped and 
    rather than toggling the window, a neocom.PanelGroup will be shown on click in 
    those cases.
    """
    __guid__ = 'neocom.PanelEntryWindow'
    default_name = 'PanelEntryWindow'

    def GetLabel(self):
        if self.IsSingleWindow():
            wnd = self.GetWindow()
            if wnd and not wnd.destroyed:
                return wnd.GetCaption()
        if self.btnData.label:
            return self.btnData.label
        if self.btnData.cmdName:
            cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
            if cmd:
                return cmd.GetName()
        if self.btnData.children:
            return self.btnData.children[0].wnd.GetNeocomGroupLabel()

    def GetWindow(self):
        if hasattr(self.btnData, 'wnd'):
            return self.btnData.wnd
        if self.btnData.children:
            btnData = self.btnData.children[0]
            return btnData.wnd

    def GetIconPath(self):
        wnd = self.GetWindow()
        if wnd and self.IsSingleWindow():
            return wnd.iconNum
        if len(self.btnData.children) > 1:
            return self.btnData.children[0].wnd.GetNeocomGroupIcon()
        return PanelEntryBase.GetIconPath(self)

    def IsSingleWindow(self):
        """Is there a single, open window associated with this button?"""
        return hasattr(self.btnData, 'wnd') or len(self.btnData.children) == 1

    def OnClick(self, *args):
        if hasattr(self.btnData, 'wnd'):
            self.btnData.wnd.Show()
        elif len(self.btnData.children) <= 1:
            self.btnData.children[0].wnd.Show()
        else:
            if self.btnData.children:
                self.ToggleNeocomPanel()
                return
            if hasattr(self.btnData, 'cmdName'):
                cmd = uicore.cmd.commandMap.GetCommandByName(self.btnData.cmdName)
                cmd.callback()
        sm.GetService('neocom').CloseAllPanels()

    def ToggleNeocomPanel(self):
        from .neocomPanels import PanelGroup
        if self.HasOpenPanel():
            sm.GetService('neocom').ClosePanel(self._openNeocomPanel)
            self._openNeocomPanel = None
        else:
            self._openNeocomPanel = sm.GetService('neocom').ShowPanel(triggerCont=self, panelClass=PanelGroup, panelAlign=neocomCommon.PANEL_SHOWONSIDE, parent=uicore.layer.abovemain, btnData=self.btnData)

    def OnDragEnter(self, panelEntry, nodes):
        self.OnMouseEnter()

    def OnDragExit(self, *args):
        self.OnMouseExit()

    def OnDropData(self, source, nodes):
        wnd = getattr(self.btnData, 'wnd', None)
        if wnd and hasattr(wnd, 'OnDropData'):
            wnd.OnDropData(source, nodes)
            sm.GetService('neocom').CloseAllPanels()

    def SetExpanderState(self):
        if len(self.btnData.children) > 1:
            self.ShowExpander()
        else:
            self.HideExpander()

    def GetMenu(self):
        return None


class PanelChatChannel(PanelEntryWindow):
    """
    Represents a chat channel
    """
    __guid__ = 'neocom.PanelEntryChatChannel'
    default_name = 'PanelEntryChatChannel'
    default_height = 25
