#Embedded file name: eve/client/script/ui/control\treeViewEntry.py
from math import pi
import blue
from carbonui.control.scrollentries import OPACITY_HOVER, OPACITY_SELECTED
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.sprite import Sprite
from carbon.common.lib import telemetry
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay, GradientUnderlay
import localization
import service
import carbonui.const as uiconst
import util
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite

class TreeViewEntry(ContainerAutoSize):
    default_name = 'TreeViewEntry'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_settingsID = ''
    LEFTPUSH = 10
    default_height = 22
    isDragObject = True
    noAccessColor = (0.33, 0.33, 0.33, 1.0)
    iconColor = util.Color.WHITE

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.level = attributes.get('level', 0)
        self.data = attributes.get('data')
        self.eventListener = attributes.get('eventListener', None)
        self.parentEntry = attributes.get('parentEntry', None)
        self.settingsID = attributes.get('settingsID', self.default_settingsID)
        self.defaultExpanded = attributes.get('defaultExpanded', self.level < 1)
        self.childrenInitialized = False
        self.isToggling = False
        self.canAccess = True
        self.isSelected = False
        self.childSelectedBG = False
        self.icon = None
        self.childCont = None
        self.topRightCont = Container(name='topCont', parent=self, align=uiconst.TOTOP, height=self.default_height)
        self.topRightCont.GetDragData = self.GetDragData
        left = self.GetSpacerContWidth()
        if self.data.IsRemovable():
            removeBtn = Sprite(texturePath='res:/UI/Texture/icons/73_16_210.png', parent=self.topRightCont, align=uiconst.CENTERLEFT, width=16, height=16, left=left, hint=localization.GetByLabel('UI/Common/Buttons/Close'))
            left += 20
            removeBtn.OnClick = self.Remove
        icon = self.data.GetIcon()
        if icon:
            iconSize = self.height - 2
            self.icon = Icon(icon=icon, parent=self.topRightCont, pos=(left,
             0,
             iconSize,
             iconSize), align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, ignoreSize=True)
            left += iconSize
        self.label = Label(parent=self.topRightCont, align=uiconst.CENTERLEFT, text=self.data.GetLabel(), left=left + 4)
        self.UpdateLabel()
        self.hoverBG = None
        self.selectedBG = None
        self.blinkBG = None
        if self.data.HasChildren():
            self.spacerCont = Container(name='spacerCont', parent=self.topRightCont, align=uiconst.TOLEFT, width=self.GetSpacerContWidth())
            self.toggleBtn = Container(name='toggleBtn', parent=self.spacerCont, align=uiconst.CENTERRIGHT, width=16, height=16, state=uiconst.UI_HIDDEN)
            self.toggleBtn.OnClick = self.OnToggleBtnClick
            self.toggleBtn.OnDblClick = lambda : None
            self.toggleBtnSprite = Sprite(bgParent=self.toggleBtn, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', rotation=pi / 2, padding=(4, 4, 5, 5))
            expandChildren = False
            if not self.data.IsForceCollapsed():
                toggleSettingsDict = settings.user.ui.Get('invTreeViewEntryToggle_%s' % self.settingsID, {})
                expandChildren = toggleSettingsDict.get(self.data.GetID(), self.defaultExpanded)
                self.ConstructChildren()
            else:
                self.toggleBtn.state = uiconst.UI_NORMAL
            self.ShowChildCont(expandChildren, animate=False)
        else:
            self.ShowChildCont(False, animate=False)
        if self.eventListener and hasattr(self.eventListener, 'RegisterID'):
            self.eventListener.RegisterID(self, self.data.GetID())

    def GetSpacerContWidth(self):
        return (1 + self.level) * self.LEFTPUSH + 8

    def Close(self):
        try:
            if self.eventListener and hasattr(self.eventListener, 'UnregisterID'):
                self.eventListener.UnregisterID(self.data.GetID())
            if self.parentEntry and self.data in self.parentEntry.data._children:
                self.parentEntry.data._children.remove(self.data)
        finally:
            ContainerAutoSize.Close(self)

    @telemetry.ZONE_METHOD
    def ConstructChildren(self):
        self.childrenInitialized = True
        children = self.data.GetChildren()
        if self.destroyed:
            return
        if self.childCont is None:
            self.childCont = ContainerAutoSize(parent=self, name='childCont', align=uiconst.TOTOP, clipChildren=True, state=uiconst.UI_HIDDEN)
        if children:
            for child in children:
                cls = self.GetTreeViewEntryClassByTreeData(child)
                child = cls(parent=self.childCont, parentEntry=self, level=self.level + 1, eventListener=self.eventListener, data=child, settingsID=self.settingsID, state=uiconst.UI_HIDDEN)
                child.UpdateLabel()

            if self.childCont.children:
                self.childCont.children[-1].padBottom = 5
            self.toggleBtn.state = uiconst.UI_NORMAL

    def GetTreeViewEntryClassByTreeData(self, treeData):
        """ Can be overridden to return custom tree view entry classes """
        return TreeViewEntry

    def ShowChildCont(self, show = True, animate = True):
        if self.childCont is None or self.childCont.display == show or not self.data.HasChildren():
            return
        for child in self.childCont.children:
            child.display = show

        self.isToggling = True
        if animate:
            if show:
                self.childCont.display = True
                uicore.animations.Tr2DRotateTo(self.toggleBtnSprite, pi / 2, 0.0, duration=0.15)
                self.childCont.DisableAutoSize()
                _, height = self.childCont.GetAutoSize()
                uicore.animations.FadeIn(self.childCont, duration=0.3)
                uicore.animations.MorphScalar(self.childCont, 'height', self.childCont.height, height, duration=0.15, sleep=True)
                self.childCont.EnableAutoSize()
            else:
                uicore.animations.Tr2DRotateTo(self.toggleBtnSprite, 0.0, pi / 2, duration=0.15)
                self.childCont.DisableAutoSize()
                uicore.animations.FadeOut(self.childCont, duration=0.15)
                uicore.animations.MorphScalar(self.childCont, 'height', self.childCont.height, 0, duration=0.15, sleep=True)
                self.childCont.display = False
            self.toggleBtn.Enable()
        else:
            self.childCont.display = show
            if show:
                self.toggleBtnSprite.rotation = 0.0
                self.childCont.opacity = 1.0
            else:
                self.toggleBtnSprite.rotation = pi / 2
                self.childCont.DisableAutoSize()
                self.childCont.opacity = 0.0
        self.isToggling = False

    def UpdateSelectedState(self, selectedIDs):
        invID = self.data.GetID()
        isSelected = selectedIDs[-1] == invID
        isChildSelected = not isSelected and invID in selectedIDs
        self.SetSelected(isSelected, isChildSelected)

    def SetSelected(self, isSelected, isChildSelected = False):
        self.isSelected = isSelected
        if isSelected or self.selectedBG:
            self.CheckConstructSelectedBG()
            self.selectedBG.display = isSelected
        self.UpdateLabel()
        if isChildSelected:
            if not self.childSelectedBG:
                self.childSelectedBG = GradientUnderlay(bgParent=self.spacerCont, rotation=0, alphaData=[(0, 0.5), (1.0, 0.0)], padBottom=1, colorType=uiconst.COLORTYPE_UIHILIGHT)
            else:
                self.childSelectedBG.Show()
        elif self.childSelectedBG:
            self.childSelectedBG.Hide()
        if isSelected and self.parentEntry:
            self.parentEntry.ExpandFromRoot()

    @telemetry.ZONE_METHOD
    def UpdateLabel(self):
        if self.isSelected and self.canAccess:
            self.label.color = util.Color.WHITE
        elif self.canAccess:
            self.label.color = Label.default_color
        else:
            self.label.color = self.noAccessColor
        if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            if settings.user.ui.Get('invPrimingDebugMode', False) and hasattr(self.data, 'invController') and self.data.invController.IsPrimed():
                self.label.color = util.Color.RED

    def ExpandFromRoot(self):
        """ Make sure a selected item is visible in the tree """
        self.ToggleChildren(forceShow=True)
        if self.parentEntry:
            self.parentEntry.ExpandFromRoot()

    def OnClick(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewClick'):
            self.eventListener.OnTreeViewClick(self, *args)

    def OnDblClick(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDblClick'):
            self.eventListener.OnTreeViewDblClick(self, *args)

    def OnToggleBtnClick(self, *args):
        if not self.isToggling:
            self.ToggleChildren()

    def ToggleChildren(self, forceShow = False):
        show = forceShow or self.childCont is None or not self.childCont.display
        toggleSettingsDict = settings.user.ui.Get('invTreeViewEntryToggle_%s' % self.settingsID, {})
        toggleSettingsDict[self.data.GetID()] = show
        settings.user.ui.Set('invTreeViewEntryToggle_%s' % self.settingsID, toggleSettingsDict)
        if not self.data.HasChildren():
            return
        if not self.childrenInitialized:
            self.ConstructChildren()
        self.ShowChildCont(show)

    def GetMenu(self):
        m = self.data.GetMenu()
        if session.role & service.ROLE_PROGRAMMER:
            idString = repr(self.data.GetID())
            m.append((idString, blue.pyos.SetClipboardData, (idString,)))
        if self.data.IsRemovable():
            m.append(None)
            m.append((localization.GetByLabel('UI/Common/Buttons/Close'), self.Remove, ()))
        return m

    def GetHint(self):
        return self.data.GetHint()

    def GetFullPathLabelList(self):
        labelTuple = [self.data.GetLabel()]
        if self.parentEntry:
            labelTuple = self.parentEntry.GetFullPathLabelList() + labelTuple
        return labelTuple

    def Remove(self, *args):
        self.eventListener.RemoveTreeEntry(self, byUser=True)

    def OnMouseDown(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseDown'):
            self.eventListener.OnTreeViewMouseDown(self, *args)

    def OnMouseUp(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseUp'):
            self.eventListener.OnTreeViewMouseUp(self, *args)

    def CheckConstructHoverBG(self):
        if self.hoverBG is None:
            self.hoverBG = FillUnderlay(bgParent=self.topRightCont, colorType=uiconst.COLORTYPE_UIHILIGHT, opacity=0.0)

    def CheckConstructSelectedBG(self):
        if self.selectedBG is None:
            self.selectedBG = FillUnderlay(bgParent=self.topRightCont, colorType=uiconst.COLORTYPE_UIHILIGHT, state=uiconst.UI_HIDDEN, opacity=OPACITY_SELECTED)

    def CheckConstructBlinkBG(self):
        if self.blinkBG is None:
            self.blinkBG = Fill(bgParent=self.topRightCont, color=(1.0, 1.0, 1.0, 0.0))

    def OnMouseEnter(self, *args):
        self.CheckConstructHoverBG()
        uicore.animations.FadeIn(self.hoverBG, OPACITY_HOVER, duration=0.1)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseEnter'):
            self.eventListener.OnTreeViewMouseEnter(self, *args)

    def OnMouseExit(self, *args):
        self.CheckConstructHoverBG()
        uicore.animations.FadeOut(self.hoverBG, duration=0.3)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseExit'):
            self.eventListener.OnTreeViewMouseExit(self, *args)

    def OnDropData(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDropData'):
            self.eventListener.OnTreeViewDropData(self, *args)

    def OnDragEnter(self, dragObj, nodes):
        self.CheckConstructHoverBG()
        uicore.animations.FadeIn(self.hoverBG, OPACITY_HOVER, duration=0.1)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDragEnter'):
            self.eventListener.OnTreeViewDragEnter(self, dragObj, nodes)

    def GetDragData(self):
        if self.data.IsDraggable():
            self.eventListener.OnTreeViewGetDragData(self)
            return [self.data]

    def OnDragExit(self, *args):
        self.CheckConstructHoverBG()
        uicore.animations.FadeOut(self.hoverBG, duration=0.1)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDragExit'):
            self.eventListener.OnTreeViewDragExit(self, *args)

    def Blink(self):
        self.CheckConstructBlinkBG()
        uicore.animations.FadeTo(self.blinkBG, 0.0, 0.25, duration=0.25, curveType=uiconst.ANIM_WAVE, loops=2)

    @telemetry.ZONE_METHOD
    def SetAccessability(self, canAccess):
        self.canAccess = canAccess
        if self.icon:
            self.icon.color = self.iconColor if canAccess else util.Color(*self.iconColor).SetAlpha(0.5).GetRGBA()
        self.UpdateLabel()
