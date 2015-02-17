#Embedded file name: eve/client/script/ui/view/aurumstore\vgsOffer.py
import carbonui.const as uiconst
import dogma.const
import eve.common.lib.appConst as appConst
import fsdlite
import industry
import itertools
import logging
import math
import uthread
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.uicore import uicorebase as uicore
from eve.client.script.ui import eveFontConst as fontConst
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveLoadingWheel import LoadingWheel
from eve.client.script.ui.shared.preview import PreviewContainer
from eve.client.script.ui.util.uiComponents import Component, ButtonEffect, RadioButtonEffect, ToggleButtonEffect
from eve.client.script.ui.view.aurumstore.vgsUiConst import VGS_FONTSIZE_LARGE, VGS_FONTSIZE_SMALL, OFFER_RADIAL_SHADOW, OFFER_BACKGROUND_COLOR, VGS_FONTSIZE_OFFER, OFFER_TEXT_BOX_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import LazyUrlSprite, VgsLabelRibbon, VgsLabelRibbonLarge, AurAmountContainer
from eve.common.script.sys.eveCfg import IsApparel, IsBlueprint, IsPreviewable
logger = logging.getLogger(__name__)
RIBBON_WIDTH = 151
RIBBON_HEIGHT = 151
INFO_BOX_HEIGHT = 60
INFO_PADDING = 8
INFO_PADDING_BIG = 10

class Ribbon(Container):
    default_name = 'Ribbon'
    default_state = uiconst.UI_DISABLED
    default_align = uiconst.TOPLEFT
    default_left = INFO_PADDING

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        Sprite(bgParent=self, texturePath=attributes.label.url)
        if attributes.isBig:
            self.left = INFO_PADDING_BIG
            label = VgsLabelRibbonLarge(parent=self, align=uiconst.CENTER, text=attributes.label.description)
        else:
            label = VgsLabelRibbon(parent=self, align=uiconst.CENTER, text=attributes.label.description)
        self.width = label.textwidth + 20
        self.height = label.textheight + 2


def CreateFill(parent, _):
    return Fill(name='highlight', bgParent=parent.imageLayer, color=OFFER_BACKGROUND_COLOR, idx=0)


@Component(ButtonEffect(bgElementFunc=CreateFill, idx=0, opacityIdle=0.0, opacityHover=0.5, opacityMouseDown=0.85, audioOnEntry='store_hover'))

class VgsOffer(Container):
    default_name = 'Offer'
    default_align = uiconst.TOPLEFT
    default_clipChildren = False
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.offer = attributes.offer
        if self.offer:
            self.CreateInfoBox(attributes.upperText, attributes.lowerText, attributes.upperSize or VGS_FONTSIZE_OFFER, attributes.lowerSize or VGS_FONTSIZE_OFFER)
        self.imageLayer = Transform(name='imageLayer', parent=self, align=uiconst.TOALL, scalingCenter=(0.5, 0.5), bgColor=OFFER_BACKGROUND_COLOR)
        if self.offer is not None and self.offer.label is not None:
            Ribbon(parent=self.imageLayer, align=uiconst.TOPLEFT, label=self.offer.label, state=uiconst.UI_DISABLED, idx=0, isBig=False)
        if self.offer:
            self.lazySprite = LazyUrlSprite(parent=self.imageLayer, align=uiconst.TOALL, imageUrl=self.offer.imageUrl)
        GradientSprite(name='OfferGradient', align=uiconst.TOALL, bgParent=self.imageLayer, rgbData=((1.0, OFFER_RADIAL_SHADOW),), alphaData=((0.0, 0.0), (1.0, 1.0)), radial=True, idx=0)

    def OnClick(self):
        if self.offer:
            uicore.cmd.ShowVgsOffer(self.offer.id)

    def CreateInfoBox(self, upperText, lowerText, upperSize, lowerSize):
        textLayer = Container(name='TextLayer', parent=self, align=uiconst.TOALL)
        infoBox = ContainerAutoSize(name='InfoBox', parent=textLayer, align=uiconst.TOBOTTOM, height=INFO_BOX_HEIGHT, state=uiconst.UI_DISABLED, bgColor=OFFER_TEXT_BOX_COLOR)
        Label(parent=infoBox, align=uiconst.TOTOP, text=upperText, fontsize=upperSize, padding=(INFO_PADDING,
         2,
         INFO_PADDING,
         -2), fontStyle=fontConst.STYLE_HEADER, uppercase=True, lineSpacing=-0.15)
        AurAmountContainer(parent=infoBox, align=uiconst.TOTOP, height=20, amount=self.offer.price, baseAmount=self.offer.basePrice, padLeft=8, padBottom=2)

    def OnMouseEnter(self, *args):
        uicore.animations.Tr2DScaleTo(self.imageLayer, startScale=self.imageLayer.scale, endScale=(1.02, 1.02), duration=0.2)

    def OnMouseExit(self, *args):
        uicore.animations.Tr2DScaleTo(self.imageLayer, self.imageLayer.scale, endScale=(1.0, 1.0), duration=0.2)


class VgsOfferPreview(Container):
    default_name = 'OfferPreview'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_PICKCHILDREN
    default_clipChildren = True
    charID = industry.Property('_charID', 'on_charid')
    typeID = industry.Property('_typeID', 'on_typeid')

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.offer = attributes.offer
        self._charID = None
        self._typeID = None
        self.on_charid = fsdlite.Signal()
        self.on_typeid = fsdlite.Signal()
        self.on_charid.connect(self.OnPickCharacter)
        self.on_typeid.connect(self.OnPickType)
        self.charButtons = []
        self._charButtonsDisplayed = False
        textLayer = Container(name='TextLayer', parent=self)
        descriptionBox = ContainerAutoSize(parent=textLayer, align=uiconst.TOBOTTOM, bgColor=OFFER_TEXT_BOX_COLOR, clipChildren=True)
        Label(parent=descriptionBox, align=uiconst.TOTOP, text=self.offer.description, fontsize=VGS_FONTSIZE_SMALL, padding=(INFO_PADDING_BIG,
         0,
         INFO_PADDING_BIG,
         10))
        titleBox = ContainerAutoSize(name='InfoBox', parent=textLayer, align=uiconst.TOBOTTOM, bgColor=OFFER_TEXT_BOX_COLOR)
        Label(parent=titleBox, align=uiconst.TOTOP, text=self.offer.name, fontsize=VGS_FONTSIZE_LARGE, padding=(INFO_PADDING_BIG,
         2,
         INFO_PADDING_BIG + 32,
         2), fontStyle=fontConst.STYLE_HEADER, uppercase=True, lineSpacing=-0.15)
        collapseBox = ContainerAutoSize(parent=textLayer, align=uiconst.TOBOTTOM_NOPUSH, top=-36)
        CollapseButton(parent=collapseBox, align=uiconst.TOPRIGHT, target=descriptionBox)
        self.characterPickerLayer = ContainerAutoSize(parent=self, align=uiconst.TOPLEFT, state=uiconst.UI_PICKCHILDREN, top=50 if self.offer.label else 10, left=10)
        self.CreateCharacterButtons()
        self.loadingLayer = Container(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        self.loadingWheel = LoadingWheel(parent=self.loadingLayer, align=uiconst.CENTER, state=uiconst.UI_DISABLED, opacity=0.0)
        self.cover = Sprite(parent=self.loadingLayer, align=uiconst.TOALL, texturePath='res:/UI/Texture/preview/asset_preview_background.png')
        self.imageLayer = Transform(name='imageLayer', parent=self, align=uiconst.TOALL, scalingCenter=(0.5, 0.5), bgColor=OFFER_BACKGROUND_COLOR)
        if self.offer.label is not None:
            Ribbon(parent=self.imageLayer, align=uiconst.TOPLEFT, label=self.offer.label, state=uiconst.UI_DISABLED, idx=0, isBig=True)
        self.previewContainer = PreviewContainer(parent=self.imageLayer, OnStartLoading=self.OnStartLoading, OnStopLoading=self.OnStopLoading)
        self.lazySprite = LazyUrlSprite(parent=self.imageLayer, align=uiconst.TOALL, imageUrl=self.offer.imageUrl, state=uiconst.UI_DISABLED)
        GradientSprite(name='OfferGradient', align=uiconst.TOALL, bgParent=self.imageLayer, rgbData=((1.0, OFFER_RADIAL_SHADOW),), alphaData=((0.0, 0.0), (1.0, 1.0)), radial=True, idx=0)
        self.PickFirstPreviewableType()

    def CreateCharacterButtons(self):
        characters = sm.GetService('cc').GetCharactersToSelect()
        charIDList = itertools.chain([None], map(lambda c: c.characterID, characters))
        for i, charID in enumerate(charIDList):
            button = CharacterButton(parent=self.characterPickerLayer, align=uiconst.RELATIVE, pos=(0,
             i * 43,
             38,
             38), charID=charID, onClick=lambda charID: setattr(self, 'charID', charID), isActive=charID == self.charID, opacity=0.0, state=uiconst.UI_DISABLED)
            self.on_charid.connect(button.OnCharID)
            self.on_typeid.connect(button.OnTypeID)
            self.charButtons.append(button)

    def ShowCharacterButtons(self):
        if self._charButtonsDisplayed:
            return
        for i, button in enumerate(self.charButtons):
            uicore.animations.MoveInFromLeft(button, amount=10, duration=0.2, timeOffset=i * 0.1)
            uicore.animations.FadeIn(button, duration=0.4, timeOffset=i * 0.1)
            button.state = uiconst.UI_NORMAL

        self._charButtonsDisplayed = True

    def HideCharacterButtons(self):
        if not self._charButtonsDisplayed:
            return
        for button in self.charButtons:
            uicore.animations.FadeOut(button, duration=0.2)
            button.state = uiconst.UI_DISABLED

        self._charButtonsDisplayed = False

    def OnPickCharacter(self, _):
        uthread.new(self.ShowPreview)

    def OnPickType(self, _):
        if IsPreviewable(self.typeID) and IsApparel(self.typeID) and not IsWearableBy(self.typeID, self.charID):
            self.charID = None
            return
        uthread.new(self.ShowPreview)

    def OnStartLoading(self, _):
        if not IsApparel(self.typeID):
            self.HideCharacterButtons()
        uicore.animations.FadeIn(self.loadingWheel, duration=0.3, timeOffset=0.2)
        uicore.animations.SpMaskIn(self.cover, duration=0.5, sleep=True)
        self.previewContainer.Show()

    def OnStopLoading(self, _):
        if IsApparel(self.typeID):
            self.ShowCharacterButtons()
        uicore.animations.FadeOut(self.loadingWheel, duration=0.3)
        uicore.animations.SpMaskOut(self.cover, duration=0.5)

    def PickFirstPreviewableType(self):
        for typeID, _ in self.offer.productQuantities.itervalues():
            if IsPreviewable(GetPreviewType(typeID)):
                self.typeID = typeID
                break
        else:
            self.previewContainer.SetState(uiconst.UI_HIDDEN)
            uicore.animations.SpMaskOut(self.cover, duration=0.4)

    def ShowPreview(self):
        typeID = GetPreviewType(self.typeID)
        if not IsPreviewable(typeID):
            return
        if IsApparel(self.typeID) and self.charID:
            self.previewContainer.PreviewCharacter(self.charID, apparel=[self.typeID])
        else:
            self.previewContainer.PreviewType(typeID, scenePath='res:/dx9/scene/fitting/fitting.red')
        if IsApparel(typeID):
            self.previewContainer.AnimEntry(-0.1, 0.0, 0.5, -0.2)
        else:
            self.previewContainer.AnimEntry(0.3, 0.2, 0.6, -0.3)

    def PrepareClose(self):
        uicore.animations.SpMaskIn(self.cover, duration=0.2, sleep=True)
        self.previewContainer.SetState(uiconst.UI_HIDDEN)


@Component(ToggleButtonEffect(bgElementFunc=lambda parent, _: parent.arrow, opacityIdle=0.5, opacityHover=0.8, opacityMouseDown=1.0, audioOnEntry='store_hover'))

class CollapseButton(Container):
    """
    This toggle button collapses and expands ContainerAutoSize instances.
    """
    default_state = uiconst.UI_NORMAL
    default_width = 32
    default_height = 32

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.target = attributes.target
        self.arrow = Sprite(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Icons/105_32_21.png')

    def Expand(self):
        self.target.EnableAutoSize()
        self.Animate(0, self.target.height, 0)

    def Collapse(self):
        self.target.DisableAutoSize()
        self.Animate(self.target.height, 0, math.pi)

    def Animate(self, startHeight, endHeight, rotation):
        uicore.animations.MorphScalar(self.target, 'height', startVal=startHeight, endVal=endHeight, duration=0.4, curveType=uiconst.ANIM_OVERSHOT)
        uicore.animations.MorphScalar(self.arrow, 'rotation', startVal=self.arrow.rotation, endVal=rotation, duration=0.2)

    def OnClick(self, *args):
        if self.isActive:
            self.Expand()
        else:
            self.Collapse()


@Component(RadioButtonEffect(bgElementFunc=lambda parent, _: parent.highlight, idx=0, opacityIdle=0.0, opacityHover=0.5, opacityMouseDown=0.85, audioOnEntry='store_hover'))

class CharacterButton(Container):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.charID = attributes.get('charID', None)
        self.onClick = attributes.onClick
        self.gender = None
        if self.charID:
            self.gender = cfg.eveowners.Get(self.charID).gender
        self.highlight = Fill(bgParent=self, color=(0.8, 0.8, 0.8, 1.0), padding=[-3,
         -3,
         -2,
         -2], fillCenter=True)
        self.portrait = Sprite(parent=self, name='portraitSprite', align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        if self.charID:
            sm.GetService('photo').GetPortrait(self.charID, 38, self.portrait)
        else:
            self.portrait.texturePath = 'res:/UI/Texture/Vgs/mannequin.png'

    def OnClick(self, *args):
        if not self.disabled:
            self.onClick(self.charID)

    def OnCharID(self, container):
        self.SetActive(container.charID == self.charID)

    def OnTypeID(self, container):
        if self.gender is None or not IsApparel(container.typeID):
            return
        gender = GetApparelGender(container.typeID)
        if gender is None or gender == self.gender:
            self.disabled = False
            uicore.animations.SpColorMorphTo(self.portrait, endColor=(1.0, 1.0, 1.0), duration=0.4)
        else:
            self.disabled = True
            uicore.animations.SpColorMorphTo(self.portrait, endColor=(0.4, 0.4, 0.4), duration=0.4)


GENDER_BY_APPAREL_GENDER = {1: appConst.MALE,
 2: None,
 3: appConst.FEMALE}

def GetApparelGender(typeID):
    dogmaStatic = sm.GetService('clientDogmaStaticSvc')
    apparelGender = dogmaStatic.GetTypeAttribute(typeID, dogma.const.attributeApparelGender)
    return GENDER_BY_APPAREL_GENDER[apparelGender]


def IsWearableBy(typeID, charID):
    if not IsApparel(typeID):
        return False
    if charID is None:
        return True
    apparelGender = GetApparelGender(typeID)
    characterGender = cfg.eveowners.Get(charID).gender
    return apparelGender is None or apparelGender == characterGender


def GetPreviewType(typeID):
    """
    Blueprints are not directly previewable but we want to be able to preview
    ship skin blueprints, so this function takes a typeID and returns the same
    typeID unless it's a blueprint type, in which case it returns that
    blueprint's first product's typeID.
    """
    if IsBlueprint(typeID):
        blueprint = sm.GetService('blueprintSvc').GetBlueprintType(typeID)
        return blueprint.productTypeID
    return typeID
