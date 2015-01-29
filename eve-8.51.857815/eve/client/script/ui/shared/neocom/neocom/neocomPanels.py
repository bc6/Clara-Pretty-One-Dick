#Embedded file name: eve/client/script/ui/shared/neocom/neocom\neocomPanels.py
"""
Classes that represent neocom panels that house panel entries that trigger actions
"""
import carbonui.const as uiconst
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay, GradientUnderlay, BlurredSceneUnderlay
import uiprimitives
import uicontrols
import util
import neocomPanelEntries
import localization
import blue
import trinity
from math import pi
from carbonui.util.mouseTargetObject import MouseTargetObject
from . import neocomCommon
COLOR_PANEL_BG = (0.0, 0.0, 0.0, 0.85)

class PanelBase(uiprimitives.Container):
    """
    An abstract panel that others inherit from
    """
    __guid__ = 'neocom.PanelBase'
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.btnData = attributes.btnData
        self.ConstructLayout()

    def ConstructLayout(self):
        self.main = uiprimitives.Container(parent=self, align=uiconst.TOALL)
        FillUnderlay(parent=self, colorType=uiconst.COLORTYPE_UIBASE, opacity=0.8)
        BlurredSceneUnderlay(bgParent=self, isPinned=True)

    def EntryAnimation(self):
        uicore.animations.FadeIn(self, duration=0.3)
        for c in self.main.children:
            c.opacity = 0.0

        sleepTime = 100.0 / len(self.main.children)
        for c in self.main.children:
            uicore.animations.FadeTo(c, 0.0, 1.0, duration=0.3)
            blue.synchro.SleepWallclock(sleepTime)


class PanelGroup(PanelBase):
    """
    A panel representing a group of panel entries. The standard panel. 
    """
    __guid__ = 'neocom.PanelGroup'
    default_name = 'PanelGroup'

    def ApplyAttributes(self, attributes):
        PanelBase.ApplyAttributes(self, attributes)
        btnDataList = self.GetButtonDataList()
        self.ConstructButtons(btnDataList)
        self.SetPanelHeight(btnDataList)
        self.SetPanelWidth()
        MouseTargetObject(self)

    def ConstructButtons(self, btnDataList):
        if btnDataList:
            for btnData in btnDataList:
                if btnData.btnType in neocomCommon.COMMAND_BTNTYPES:
                    cmdName = btnData.cmdName
                    cmd = uicore.cmd.commandMap.GetCommandByName(cmdName)
                    neocomPanelEntries.PanelEntryCmd(parent=self.main, func=cmd.callback, btnData=btnData)
                elif btnData.btnType in (neocomCommon.BTNTYPE_GROUP, neocomCommon.BTNTYPE_CHAT):
                    neocomPanelEntries.PanelEntryGroup(parent=self.main, btnData=btnData)
                elif btnData.btnType == neocomCommon.BTNTYPE_CHATCHANNEL:
                    neocomPanelEntries.PanelChatChannel(parent=self.main, btnData=btnData)
                elif btnData.btnType == neocomCommon.BTNTYPE_WINDOW:
                    neocomPanelEntries.PanelEntryWindow(parent=self.main, btnData=btnData)
                elif btnData.btnType == neocomCommon.BTNTYPE_BOOKMARKS:
                    neocomPanelEntries.PanelEntryBookmarks(parent=self.main, btnData=btnData)
                elif btnData.btnType == neocomCommon.BTNTYPE_BOOKMARK:
                    neocomPanelEntries.PanelEntryBookmark(parent=self.main, btnData=btnData)

        else:
            neocomPanelEntries.PanelEntryText(parent=self.main, label=localization.GetByLabel('UI/Neocom/GroupEmpty'))

    def SetPanelHeight(self, btnDataList):
        height = 0
        for child in self.main.children:
            height += child.height

        self.height = max(height, neocomPanelEntries.PanelEntryBase.default_height)

    def SetPanelWidth(self):
        maxWidth = 220
        for panel in self.main.children:
            if hasattr(panel, 'GetRequiredWidth'):
                maxWidth = max(panel.GetRequiredWidth(), maxWidth)

        self.width = maxWidth

    def GetButtonDataList(self):
        return [ btnData for btnData in self.btnData.children if sm.GetService('neocom').IsButtonInScope(btnData) ]


class PanelOverflow(PanelGroup):
    """
    A panel that represents neocom buttons that don't fit due to lack of screen space
    """
    __guid__ = 'neocom.PanelOverflow'
    default_name = 'PanelOverflow'

    def ApplyAttributes(self, attributes):
        self.overflowButtons = attributes.overflowButtons
        PanelGroup.ApplyAttributes(self, attributes)

    def GetButtonDataList(self):
        return sm.GetService('neocom').neocom.overflowButtons


class PanelEveMenu(PanelGroup):
    """
    The EVE menu
    """
    __guid__ = 'neocom.PanelEveMenu'
    default_name = 'PanelEveMenu'
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        PanelGroup.ApplyAttributes(self, attributes)
        sm.ScatterEvent('OnEveMenuOpened')

    def ConstructLayout(self):
        self.topFill = uiprimitives.Container(parent=self, name='topFill', align=uiconst.TOTOP, height=30)
        BlurredSceneUnderlay(bgParent=self.topFill)
        self.topBG = uiprimitives.Sprite(parent=self.topFill, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Neocom/eveButtonBg.png', blendMode=trinity.TR2_SBM_ADD)
        self.main = uiprimitives.Container(name='main', parent=self, padTop=3)
        self.bgFill = FillUnderlay(parent=self, align=uiconst.TOTOP, colorType=uiconst.COLORTYPE_UIBASE, opacity=0.8)
        GradientUnderlay(parent=self, align=uiconst.TOALL, colorType=uiconst.COLORTYPE_UIBASE, rgbData=[(0.0, (1.0, 1.0, 1.0))], alphaData=[(0.0, 0.8), (0.4, 0.3), (1.0, 0.1)], rotation=-pi / 2)
        BlurredSceneUnderlay(bgParent=self, isPinned=True, opacity=0.8)

    def SetPanelHeight(self, btnDataList):
        height = 0
        for child in self.main.children:
            height += child.height

        self.bgFill.height = max(height, neocomPanelEntries.PanelEntryBase.default_height)
        self.height = uicore.desktop.height

    def Close(self, *args):
        sm.ScatterEvent('OnEveMenuClosed')
        PanelGroup.Close(self, *args)

    def EntryAnimation(self):
        uicore.animations.MorphScalar(self.topBG, 'padRight', self.width, 0.0, duration=0.2)
        PanelGroup.EntryAnimation(self)
