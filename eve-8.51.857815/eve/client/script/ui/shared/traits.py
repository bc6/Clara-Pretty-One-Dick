#Embedded file name: eve/client/script/ui/shared\traits.py
import localization
import carbonui.const as uiconst
import util
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveLabel import Label
ROLE_BONUS_TYPE = -1
MISC_BONUS_TYPE = -2
COLOR_CAPTION = (0.298, 0.549, 0.69, 1.0)
COLOR_TEXT_HILITE = (0.765, 0.914, 1.0, 1.0)
COLOR_TEXT = (0.5, 0.5, 0.5, 1.0)

def HasTraits(typeID):
    fsdType = cfg.fsdTypeOverrides.GetIfExists(typeID)
    return fsdType and hasattr(fsdType, 'infoBubbleTypeBonuses')


class TraitsContainer(ContainerAutoSize):
    default_name = 'TraitsContainer'
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        super(TraitsContainer, self).ApplyAttributes(attributes)
        self.typeID = attributes.typeID
        displayTraitAttributeIcons = attributes.get('traitAttributeIcons', False)
        fsdType = cfg.fsdTypeOverrides.Get(self.typeID)
        if displayTraitAttributeIcons and hasattr(fsdType, 'infoBubbleTypeElement'):
            self.AddCaption(localization.GetByLabel('UI/InfoWindow/ShipCharacteristics'))
            self.AddAttributeIcons(fsdType.infoBubbleTypeElement)
        if not hasattr(fsdType, 'infoBubbleTypeBonuses'):
            return
        typeBonuses = fsdType.infoBubbleTypeBonuses
        for skillTypeID, skillData in typeBonuses.iteritems():
            if skillTypeID > 0:
                self.AddCaption(localization.GetByLabel('UI/ShipTree/SkillNameCaption', skillName=cfg.invtypes.Get(skillTypeID).name))
                self.AddBonusLabel(skillData)

        if ROLE_BONUS_TYPE in typeBonuses:
            self.AddCaption(localization.GetByLabel('UI/ShipTree/RoleBonus'))
            self.AddBonusLabel(typeBonuses[ROLE_BONUS_TYPE])
        elif MISC_BONUS_TYPE in typeBonuses:
            self.AddCaption(text=localization.GetByLabel('UI/ShipTree/MiscBonus'))
            self.AddBonusLabel(typeBonuses[MISC_BONUS_TYPE])

    def AddCaption(self, text):
        Label(parent=self, text=text, align=uiconst.TOTOP, padTop=8 if self.children else 0, bold=True, color=COLOR_CAPTION)

    def AddBonusLabel(self, data):
        for _, bonusData in data.iteritems():
            self._FormatBonusLine(bonusData)

    def AddAttributeIcons(self, data):
        rowCont = Container(parent=self, align=uiconst.TOTOP, padTop=3)
        labelCont = Container(parent=rowCont, align=uiconst.TOPLEFT, height=TraitAttributeIcon.default_height, width=40)
        text = localization.GetByLabel('UI/InfoWindow/TraitWithoutNumber', color=util.Color.RGBtoHex(*COLOR_TEXT_HILITE), bonusText='')
        label = Label(parent=labelCont, text=text, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, color=COLOR_TEXT, tabs=(40,), tabMargin=3)
        iconCont = FlowContainer(parent=rowCont, align=uiconst.TOTOP, padLeft=43, contentSpacing=(1, 1), autoHeight=True)
        old_OnSizeChange_NoBlock = iconCont._OnSizeChange_NoBlock

        def OnSizeChange_NoBlock_Hook(newWidth, newHeight):
            old_OnSizeChange_NoBlock(newWidth, newHeight)
            rowCont.height = newHeight

        iconCont._OnSizeChange_NoBlock = OnSizeChange_NoBlock_Hook
        for _, attributeID in data.iteritems():
            TraitAttributeIcon(parent=iconCont, align=uiconst.NOALIGN, attributeID=attributeID)

    def _FormatBonusLine(self, data):
        colorHex = util.Color.RGBtoHex(*COLOR_TEXT_HILITE)
        if hasattr(data, 'bonus'):
            value = round(data.bonus, 1)
            if int(data.bonus) == data.bonus:
                value = int(data.bonus)
            text = localization.GetByLabel('UI/InfoWindow/TraitWithNumber', color=colorHex, value=value, unit=cfg.dgmunits.Get(data.unitID).displayName, bonusText=localization.GetByMessageID(data.nameID))
        else:
            text = localization.GetByLabel('UI/InfoWindow/TraitWithoutNumber', color=colorHex, bonusText=localization.GetByMessageID(data.nameID))
        Label(parent=self, text=text, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, padTop=3, color=COLOR_TEXT, tabs=(40,), tabMargin=3)


class TraitAttributeIcon(Container):
    default_name = 'TraitAttributeIcon'
    default_width = 30
    default_height = 30
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        super(TraitAttributeIcon, self).ApplyAttributes(attributes)
        self.attributeID = attributes.attributeID
        Sprite(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath=cfg.fsdInfoBubbleElements[self.attributeID].icon)
        Sprite(name='bgHoverFrame', bgParent=self, texturePath='res:/UI/texture/classes/shipTree/InfoBubble/frame.png', opacity=0.5)
        self.bgFrame = Sprite(name='bgHoverFrame', bgParent=self, texturePath='res:/UI/texture/classes/shipTree/InfoBubble/frameHover.png', opacity=0.0)

    def GetHint(self):
        nameID = cfg.fsdInfoBubbleElements[self.attributeID].nameID
        descriptionID = cfg.fsdInfoBubbleElements[self.attributeID].descriptionID
        return '<b>' + localization.GetByMessageID(nameID) + '</b><br>' + localization.GetByMessageID(descriptionID)

    def OnMouseEnter(self):
        uicore.animations.FadeTo(self.bgFrame, 0.3, 0.0, duration=0.5)

    def OnMouseExit(self):
        uicore.animations.FadeOut(self.bgFrame, duration=0.3)
