#Embedded file name: eve/client/script/ui/shared/shipTree\infoBubble.py
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.primitives.layoutGrid import LayoutGrid, LayoutGridRow
from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.entries import SkillTreeEntry
from eve.client.script.ui.control.eveLabel import EveCaptionMedium, Label, EveLabelMediumBold
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.eveIcon import Icon
from localization import GetByLabel, GetByMessageID
from eve.common.script.util.eveFormat import FmtISKAndRound
import util
from carbonui.primitives.fill import Fill
from eve.client.script.ui.shared.neocom.skillinfo import SkillLevels
from carbonui.primitives.frame import Frame
from utillib import KeyVal
from eve.client.script.ui.shared.shipTree.shipTreeConst import COLOR_TEXT
from eve.client.script.ui.shared.traits import TraitsContainer, TraitAttributeIcon
from itertoolsext import first
from eve.client.script.ui.util.uiComponents import Component, ButtonEffect

class InfoBubble(Container):
    default_name = 'InfoBubble'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_width = 350
    default_height = 200
    default_idx = 0
    default_topOffset = 0
    default_opacity = 0.0

    def __init__(self, **kw):
        Container.__init__(self, **kw)
        self.StartupInfoBubble()

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.parentObj = attributes.parentObj
        self.topOffset = attributes.Get('topOffset', self.default_topOffset)
        self.__isClosing = False
        self.mainCont = Container(name='mainCont', parent=self, padding=10)
        self.bgFrame = Container(name='bgFrame', parent=self, state=uiconst.UI_DISABLED)
        self.frameTop = StretchSpriteHorizontal(parent=self.bgFrame, align=uiconst.TOTOP, texturePath='res:/UI/Texture/classes/ShipTree/InfoBubble/frameUpper.png', height=36, opacity=0.0)
        self.frameBottom = StretchSpriteHorizontal(parent=self.bgFrame, align=uiconst.TOBOTTOM, texturePath='res:/UI/Texture/classes/ShipTree/InfoBubble/frameLower.png', height=36, opacity=0.0)
        self.bgFill = Container(name='bgFill', parent=self, state=uiconst.UI_DISABLED, opacity=0.0)
        StretchSpriteHorizontal(parent=self.bgFill, align=uiconst.TOTOP, texturePath='res:/UI/Texture/classes/ShipTree/InfoBubble/backTopExtender.png', height=1)
        StretchSpriteHorizontal(parent=self.bgFill, align=uiconst.TOBOTTOM, texturePath='res:/UI/Texture/classes/ShipTree/InfoBubble/backBottom.png', height=6)
        Sprite(parent=self.bgFill, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/ShipTree/InfoBubble/backMiddle.png')
        self.topContainer = ContainerAutoSize(name='topContainer', parent=self.mainCont, align=uiconst.TOTOP, callback=self.OnMainContentSizeChanged)
        self.iconCont = Container(name='iconCont', parent=self.topContainer, align=uiconst.TOPLEFT, width=80, height=80, left=0, top=0)
        self.topRightCont = ContainerAutoSize(name='topRightCont', align=uiconst.TOPLEFT, left=90, width=self.width - 115, parent=self.topContainer)
        self.caption = EveCaptionMedium(parent=self.topRightCont, align=uiconst.TOTOP)
        self.attributeCont = ContainerAutoSize(name='attributeCont', parent=self.topRightCont, align=uiconst.TOTOP, padTop=5)
        self.mainContent = ContainerAutoSize(name='mainContent', parent=self.mainCont, align=uiconst.TOTOP, callback=self.OnMainContentSizeChanged, padTop=5)

    def StartupInfoBubble(self):
        self.mainContent.SetSizeAutomatically()
        self.OnMainContentSizeChanged()
        self.SetLeftAndTop()

    def SetLeftAndTop(self):
        left, top, width, height = self.parentObj.GetAbsolute()
        self.left = left - (self.width - width) / 2
        if top > self.height:
            self.top = top - self.height + self.topOffset
        else:
            self.top = top + height + 2

    def OnMainContentSizeChanged(self, *args):
        self.height = self.topContainer.height + self.mainContent.height + 25
        self.SetLeftAndTop()

    def AnimShow(self):
        uicore.animations.FadeIn(self.bgFill, duration=0.3)
        uicore.animations.FadeIn(self.frameTop, duration=0.3)
        uicore.animations.FadeIn(self.frameBottom, duration=0.3, timeOffset=0.15)
        uicore.animations.FadeIn(self, duration=0.15)
        for i, attrIcon in enumerate(self.attributeCont.children):
            timeOffset = i * 0.05
            uicore.animations.FadeTo(attrIcon, 0.0, 1.0, duration=0.3, timeOffset=timeOffset)
            uicore.animations.MorphScalar(attrIcon, 'left', attrIcon.left + 5, attrIcon.left, duration=0.1, timeOffset=timeOffset)

    def Close(self):
        if self.__isClosing:
            return
        self.__isClosing = True
        uicore.animations.FadeOut(self, duration=0.15, callback=self._Close)

    def _Close(self):
        Container.Close(self)

    def ConstructElements(self, attributeIDs):
        numInRow = 7
        size = InfoBubbleAttributeIcon.default_width
        for i, (_, attributeID) in enumerate(attributeIDs.iteritems()):
            left = i % numInRow * (size + 1)
            top = i / numInRow * (size + 1)
            InfoBubbleAttributeIcon(parent=self.attributeCont, align=uiconst.TOPLEFT, attributeID=attributeID, left=left, top=top)


@Component(ButtonEffect(bgElementFunc=lambda parent, _: Fill(bgParent=parent), opacityHover=0.1, opacityMouseDown=0.2))

class TrialRestrictionButton(Container):
    default_state = uiconst.UI_NORMAL
    ICON_SIZE = 24
    PADDING = 4

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.OnClick = attributes.get('callback')
        Sprite(parent=self, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Monetization/Trial_24x24_Gradient.png', color=(0.965, 0.467, 0.157, 1.0), width=self.ICON_SIZE, height=self.ICON_SIZE, top=6)
        label = Label(parent=self, align=uiconst.TOTOP, text=GetByLabel(attributes['message']), color=(0.965, 0.467, 0.157, 1.0), padding=(self.ICON_SIZE + 2 * self.PADDING,
         self.PADDING,
         self.PADDING,
         self.PADDING))
        self.height = label.height + 2 * self.PADDING


class InfoBubbleShipGroup(InfoBubble):
    default_name = 'InfoBubbleShipGroup'
    default_topOffset = 6

    def ApplyAttributes(self, attributes):
        InfoBubble.ApplyAttributes(self, attributes)
        self.node = attributes.node
        infoBubbleGroup = cfg.fsdInfoBubbleGroups[self.node.shipGroupID]
        self.caption.text = GetByMessageID(infoBubbleGroup.nameID)
        Frame(bgParent=self.iconCont, texturePath='res:/UI/Texture/Classes/ShipTree/Groups/groupIconFrame.png', opacity=0.15)
        self.icon = Sprite(name='icon', parent=self.iconCont, pos=(0, 0, 64, 64), align=uiconst.CENTER, texturePath=infoBubbleGroup.iconLarge)
        self.ConstructElements(infoBubbleGroup.elements)
        Label(parent=self.mainContent, align=uiconst.TOTOP, text=GetByMessageID(infoBubbleGroup.descriptionID), padTop=5)
        if self.node.IsRestricted():
            TrialRestrictionButton(parent=self.mainContent, align=uiconst.TOTOP, padTop=8, callback=self.OpenSubscriptionPage, message='UI/ShipTree/ShipGroupTrialRestricted')
        if self.node.IsLocked():
            layoutGrid = LayoutGrid(parent=self.mainContent, align=uiconst.TOTOP, padTop=12)
            cont = Container(align=uiconst.TOPLEFT, height=14, width=self.width - 20)
            Sprite(parent=cont, pos=(0, -1, 16, 16), texturePath='res:/UI/Texture/classes/inventory/locked.png', align=uiconst.CENTERLEFT, opacity=0.5)
            caption = InfoBubbleCaption(align=uiconst.CENTERLEFT, parent=cont, text=GetByLabel('UI/ShipTree/SkillsRequiredToUnlock'), left=18, padTop=0)
            layoutGrid.AddCell(cont, colSpan=2, cellPadding=(0, 0, 0, 2))
            for typeID, level in self.node.GetRequiredSkillsSorted():
                layoutGrid.AddRow(rowClass=SkillEntry, typeID=typeID, level=level, showLevel=False)

            trainingTime = self.node.GetTimeToUnlock()
            if trainingTime > 0:
                totalTimeText = GetByLabel('UI/SkillQueue/Skills/TotalTrainingTime', timeLeft=long(trainingTime))
                EveLabelMediumBold(parent=self.mainContent, align=uiconst.TOTOP, padTop=4, text=totalTimeText)
        else:
            bonusSkills = self.node.GetBonusSkillsSorted()
            if bonusSkills:
                layoutGrid = LayoutGrid(parent=self.mainContent, align=uiconst.TOTOP)
                caption = InfoBubbleCaption(align=uiconst.TOPLEFT, text=GetByLabel('UI/ShipTree/ShipBonusSkills'), padding=(0, 12, 0, 2), width=self.width - 20)
                layoutGrid.AddCell(caption, colSpan=2)
                for typeID, level in bonusSkills:
                    layoutGrid.AddRow(rowClass=SkillEntry, typeID=typeID, level=level, showLevel=False)

        self.AnimShow()
        sm.GetService('shipTree').LogIGS('HoverGroup')

    def OpenSubscriptionPage(self, *args):
        shipTree = sm.GetService('shipTree')
        shipTypeID = first(shipTree.GetShipTypeIDs(self.node.factionID, self.node.shipGroupID))
        shipGroupID = cfg.invtypes.Get(shipTypeID).groupID
        shipTree.OpenSubscriptionPage(['ship', shipGroupID])


class SkillEntry(LayoutGridRow):
    default_name = 'SkillEntry'
    default_state = uiconst.UI_NORMAL
    default_showLevel = True
    isDragObject = True

    def ApplyAttributes(self, attributes):
        LayoutGridRow.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.level = attributes.level
        self.showLevel = attributes.Get('showLevel', self.default_showLevel)
        self.bgPattern = Sprite(bgParent=self, align=uiconst.TOALL, padBottom=1, texturePath='res:/UI/Texture/Classes/Industry/Output/hatchPattern.png', tileX=True, tileY=True, color=SkillTreeEntry.COLOR_RESTRICTED, opacity=0.0)
        self.bgFill = Fill(bgParent=self, padBottom=1)
        leftCont = ContainerAutoSize(padding=(0, 3, 0, 3), align=uiconst.CENTERLEFT)
        self.icon = Sprite(name='icon', parent=leftCont, align=uiconst.CENTERLEFT, pos=(2, 0, 16, 16), state=uiconst.UI_NORMAL)
        if self.showLevel:
            text = GetByLabel('UI/InfoWindow/SkillAndLevelInRoman', skill=self.typeID, levelInRoman=util.IntToRoman(self.level))
        else:
            text = cfg.invtypes.Get(self.typeID).name
        self.label = Label(name='label', parent=leftCont, align=uiconst.CENTERLEFT, left=self.icon.width + 4, text=text)
        self.AddCell(leftCont)
        self.skillBar = SkillLevels(align=uiconst.CENTERRIGHT, typeID=self.typeID)
        self.AddCell(self.skillBar, cellPadding=(8, 8, 8, 8))
        self.UpdateState()

    def UpdateState(self):
        mySkill = sm.GetService('skills').MySkills(byTypeID=True).get(self.typeID, None)
        if mySkill:
            self.skillBar.SetLevel(mySkill)
            myLevel = mySkill.skillLevel
        else:
            myLevel = None
        isTrialRestricted = sm.GetService('skills').IsTrialRestricted(self.typeID)
        if isTrialRestricted:
            self.icon.SetTexturePath('res:/UI/Texture/classes/Skills/trial-restricted-16.png')
            self.icon.color = SkillTreeEntry.COLOR_RESTRICTED
            self.icon.state = uiconst.UI_NORMAL
            self.icon.OnClick = self.OpenSubscriptionPage
            self.icon.hint = GetByLabel('UI/InfoWindow/SkillRestrictedForTrial')
            self.bgFill.SetRGBA(0.2, 0.1, 0.05, 1.0)
            self.bgPattern.opacity = 0.15
        elif myLevel is None:
            self.icon.SetTexturePath('res:/UI/Texture/icons/38_16_194.png')
            self.icon.hint = GetByLabel('UI/InfoWindow/NotTrained')
            self.bgFill.SetRGBA(*SkillTreeEntry.COLOR_NOTTRAINED)
            self.skillBar.opacity = 0.4
            self.bgPattern.opacity = 0.0
        elif myLevel < self.level:
            self.icon.SetTexturePath('res:/UI/Texture/icons/38_16_195.png')
            self.icon.hint = GetByLabel('UI/InfoWindow/TrainedButNotOfRequiredLevel')
            self.bgFill.SetRGBA(*SkillTreeEntry.COLOR_PARTIAL)
            self.skillBar.opacity = 1.0
            self.bgPattern.opacity = 0.0
        else:
            self.icon.SetTexturePath('res:/UI/Texture/icons/38_16_193.png')
            self.icon.hint = GetByLabel('UI/InfoWindow/TrainedAndOfRequiredLevel')
            self.bgFill.SetRGBA(*SkillTreeEntry.COLOR_TRAINED)
            self.skillBar.opacity = 1.0
            self.bgPattern.opacity = 0.0

    def GetMenu(self):
        return sm.GetService('menu').GetMenuForSkill(self.typeID)

    def OnClick(self):
        sm.GetService('info').ShowInfo(self.typeID)

    def GetDragData(self):
        ret = KeyVal(__guid__='uicls.GenericDraggableForTypeID', typeID=self.typeID, label=cfg.invtypes.Get(self.typeID).name)
        return (ret,)

    def OpenSubscriptionPage(self, *args):
        sm.GetService('shipTree').OpenSubscriptionPage(['skill', self.typeID])


class InfoBubbleShip(InfoBubble):
    default_name = 'InfoBubbleShip'
    default_topOffset = 5

    def ApplyAttributes(self, attributes):
        InfoBubble.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.caption.text = cfg.invtypes.Get(self.typeID).name
        self.icon = Icon(name='icon', parent=self.iconCont, pos=(0, 0, 80, 80), typeID=self.typeID, ignoreSize=True, cursor=uiconst.UICURSOR_MAGNIFIER)
        self.icon.OnClick = self.OnIconClicked
        fsdType = cfg.fsdTypeOverrides.Get(self.typeID)
        if hasattr(fsdType, 'infoBubbleTypeElement'):
            self.ConstructElements(fsdType.infoBubbleTypeElement)
        isTrialRestricted = sm.GetService('skills').IsTrialRestricted(self.typeID)
        if isTrialRestricted:
            TrialRestrictionButton(parent=self.mainContent, align=uiconst.TOTOP, padding=(0, 8, 0, 8), callback=self.OpenSubscriptionPage, message='UI/ShipTree/ShipTrialRestricted')
        TraitsContainer(parent=self.mainContent, typeID=self.typeID)
        price = cfg.invtypes.Get(self.typeID).averagePrice or 0
        text = GetByLabel('UI/Inventory/EstIskPrice', iskString=FmtISKAndRound(price, False))
        Label(parent=self.topRightCont, text=text, align=uiconst.TOTOP, padTop=7)
        uicore.animations.FadeTo(self.icon, 1.5, 1.0, duration=0.6)
        self.AnimShow()
        sm.GetService('shipTree').LogIGS('HoverType')

    def AnimShow(self):
        InfoBubble.AnimShow(self)
        for i, obj in enumerate(self.mainContent.children):
            timeOffset = i * 0.015
            uicore.animations.FadeTo(obj, 0.0, 1.0, duration=0.3, timeOffset=timeOffset)

    def OnIconClicked(self):
        sm.GetService('preview').PreviewType(self.typeID)

    def OpenSubscriptionPage(self, *args):
        shipGroupID = cfg.invtypes.Get(self.typeID).groupID
        sm.GetService('shipTree').OpenSubscriptionPage(['ship', shipGroupID, self.typeID])


class InfoBubbleCaption(Label):
    default_color = COLOR_TEXT
    default_bold = True
    default_padTop = 8


class InfoBubbleAttributeIcon(TraitAttributeIcon):
    default_name = 'InfoBubbleAttributeIcon'
    default_padRight = 1
    default_opacity = 0.0
