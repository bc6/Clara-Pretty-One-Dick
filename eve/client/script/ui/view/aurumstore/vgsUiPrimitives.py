#Embedded file name: eve/client/script/ui/view/aurumstore\vgsUiPrimitives.py
import math
from carbon.common.script.util.format import FmtAmt
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
import localization
import uthread
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveLabel import Label, EveCaptionLarge
from eve.client.script.ui.control.eveLoadingWheel import LoadingWheel
from eve.client.script.ui.util.uiComponents import Component, ButtonEffect, RadioButtonEffect
from eve.client.script.ui import eveFontConst as fontConst
from eve.client.script.ui.view.aurumstore.vgsHelper import LoadImageToSprite
from eve.client.script.ui.view.aurumstore.vgsUiConst import VGS_FONTSIZE_OFFER, VGS_WHITE_TEXT_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import VGS_SPECIAL_PRICE_COLOR, VGS_AUR_TEXT_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import CATEGORY_TEXT_COLOR, HEADER_BG_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import TAG_COLOR, CATEGORY_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import TAG_GLOW_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import CATEGORY_GLOW_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import SUBCATEGORY_TEXT_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import BUY_AUR_BUTTON_COLOR, BUY_BUTTON_FONT_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import VGS_FONTSIZE_SMALL, VGS_FONTSIZE_MEDIUM, VGS_FONTSIZE_LARGE
TAG_TEXT_PADDING = 16
DEFAULT_BUTTON_PADDING = 16
AUR_COLOR_HEX = Color(*VGS_AUR_TEXT_COLOR).GetHex()
SPECIAL_COLOR_HEX = Color(*VGS_SPECIAL_PRICE_COLOR).GetHex()

class VgsLabelLarge(Label):
    default_name = 'VgsLabelLarge'
    default_fontsize = VGS_FONTSIZE_LARGE
    default_uppercase = True
    default_fontStyle = fontConst.STYLE_HEADER


class VgsLabelMedium(Label):
    default_name = 'VgsLabelMedium'
    default_fontsize = VGS_FONTSIZE_MEDIUM
    default_uppercase = True
    default_fontStyle = fontConst.STYLE_HEADER


class VgsLabelSmall(Label):
    default_name = 'VgsLabelSmall'
    default_fontsize = VGS_FONTSIZE_SMALL


class VgsLabelSubCategories(Label):
    default_fontsize = VGS_FONTSIZE_MEDIUM


class VgsLabelRibbon(Label):
    default_name = 'VgsLabelRibbon'
    default_fontsize = VGS_FONTSIZE_MEDIUM
    default_uppercase = True
    default_bold = True
    default_fontStyle = fontConst.STYLE_HEADER


class VgsLabelRibbonLarge(Label):
    default_name = 'VgsLabelRibbon'
    default_fontsize = VGS_FONTSIZE_LARGE
    default_uppercase = True
    default_bold = True
    default_fontStyle = fontConst.STYLE_HEADER


class VgsLabelAurSmall(Label):
    default_name = 'VgsLabelAurSmall'
    default_fontsize = VGS_FONTSIZE_SMALL
    default_uppercase = True
    default_bold = True
    default_color = VGS_AUR_TEXT_COLOR
    default_text = localization.GetByLabel('UI/Wallet/WalletWindow/AUR')


class VgsLabelAurLarge(VgsLabelAurSmall):
    default_name = 'VgsLabelAurLarge'
    default_fontsize = VGS_FONTSIZE_MEDIUM


class AurAmountContainer(ContainerAutoSize):
    default_name = 'AurLabel'
    amountSize = VGS_FONTSIZE_OFFER
    aurSize = VGS_FONTSIZE_SMALL
    wordPadding = 8

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.amountLabel = None
        self.baseAmountLabel = None
        if attributes.amountSize:
            self.amountSize = attributes.amountSize
        if attributes.aurSize:
            self.aurSize = attributes.aurSize
        amount = attributes.amount
        baseAmount = attributes.baseAmount
        self.amountLabel = self.AddAurSection(amount)
        if baseAmount is not None and amount != baseAmount:
            self.baseAmountLabel = self.AddAurSection(baseAmount, color=VGS_SPECIAL_PRICE_COLOR, strikeThrough=True)

    def AddAurSection(self, amount, color = None, strikeThrough = False):
        cont = Container(parent=self, align=uiconst.TOLEFT, padRight=self.wordPadding)
        if strikeThrough:
            Sprite(parent=cont, align=uiconst.TOALL, texturePath='res:/UI/Texture/Vgs/strikethrough.png', padding=(0, 0, 0, 0), color=color or VGS_WHITE_TEXT_COLOR, state=uiconst.UI_DISABLED)
        amountLabel = Label(parent=cont, align=uiconst.TOPLEFT, fontsize=self.amountSize, color=color or VGS_WHITE_TEXT_COLOR)
        SetAmountForAurLabel(amountLabel, amount, self.aurSize, SPECIAL_COLOR_HEX if color else AUR_COLOR_HEX)
        return amountLabel

    def SetAmount(self, amount, baseAmount = None):
        SetAmountForAurLabel(self.amountLabel, amount, self.aurSize, AUR_COLOR_HEX)
        if baseAmount and amount != baseAmount:
            SetAmountForAurLabel(self.baseAmountLabel, baseAmount, self.aurSize, SPECIAL_COLOR_HEX)


def SetAmountForAurLabel(label, amount, aurSize, color):
    label.SetText('%s<font size=%s color=%s> %s</font>' % (FmtAmt(amount),
     aurSize,
     color,
     localization.GetByLabel('UI/Wallet/WalletWindow/AUR')))
    label.parent.width = label.textwidth


class AurLabelLarge(AurAmountContainer):
    default_name = 'AurLabelLarge'
    amountSize = VGS_FONTSIZE_LARGE
    aurSize = VGS_FONTSIZE_MEDIUM
    wordPadding = 12


class AurLabelHeader(AurAmountContainer):
    default_name = 'AurLabelLarge'
    amountSize = VGS_FONTSIZE_LARGE
    aurSize = VGS_FONTSIZE_MEDIUM
    wordPadding = 0


@Component(ButtonEffect())

class ExitButton(Container):
    default_name = 'exitButton'
    default_width = 16
    default_height = 16
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.onClick = attributes.onClick
        Sprite(parent=self, texturePath='res:/UI/Texture/Icons/73_16_45.png', width=16, height=16, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=Color.GRAY7)

    def OnClick(self):
        self.onClick()


@Component(ButtonEffect(opacityIdle=0.0, opacityHover=0.25, opacityMouseDown=0.5, bgElementFunc=lambda parent, _: parent.highlight))

class LogoHomeButton(Container):
    default_name = 'LogoHomeButton'
    default_width = 280
    default_height = 100
    default_state = uiconst.UI_NORMAL
    logoTexturePath = 'res:/UI/Texture/Vgs/storeLogo.png'
    highlightTexturePath = 'res:/UI/Texture/Vgs/storeLogoGlow.png'

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        logoTexturePath = attributes.logoTexturePath or self.logoTexturePath
        highlightTexturePath = attributes.highlightTexturePath or self.highlightTexturePath
        Sprite(name='Logo', bgParent=self, texturePath=logoTexturePath)
        self.highlight = Sprite(name='Highlight', bgParent=self, texturePath=highlightTexturePath)
        self.onClick = attributes.onClick

    def OnClick(self):
        self.onClick()


@Component(ButtonEffect())

class RedeemingQueueButton(Container):
    default_name = 'redeemingQueueButton'
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.label = EveCaptionLarge(parent=self, align=uiconst.CENTER, text=localization.GetByLabel('UI/CharacterSelection/RedeemItems'))
        self.width = max(attributes.width, self.label.width + 2 * DEFAULT_BUTTON_PADDING)
        self.sprite = Sprite(parent=self, width=self.width, height=attributes.height, texturePath='res:\\UI\\Texture\\redeem_bar.png', bgColor=attributes.bgColor, state=uiconst.UI_DISABLED, align=uiconst.CENTER)


@Component(ButtonEffect())

class HeaderBuyAurButton(Container):
    default_state = uiconst.UI_NORMAL
    default_padding = (4, 2, 4, 2)
    textPadding = (8, 4)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        Fill(bgParent=self, color=BUY_AUR_BUTTON_COLOR, opacity=1.0)
        label = VgsLabelMedium(parent=self, align=uiconst.CENTER, text=localization.GetByLabel('UI/VirtualGoodsStore/BuyAurOnline'), color=BUY_BUTTON_FONT_COLOR)
        horizontalPadding, verticalPadding = self.textPadding
        self.width = label.textwidth + 2 * horizontalPadding
        self.height = label.textheight + 2 * verticalPadding
        self.OnClick = attributes.onClick


@Component(ButtonEffect())

class DetailButton(Container):
    default_state = uiconst.UI_NORMAL
    default_height = 30
    textPadding = (8, 4)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        if attributes.textPadding:
            self.textPadding = attributes.textPadding
        self.color = Fill(bgParent=self, color=attributes.color, opacity=1.0)
        self.label = VgsLabelMedium(parent=self, align=uiconst.CENTER, text=attributes.label, color=BUY_BUTTON_FONT_COLOR)
        self.SetText(attributes.label)
        self.OnClick = attributes.onClick

    def SetText(self, text):
        self.label.SetText(text)
        horizontalPadding, verticalPadding = self.textPadding
        self.width = self.label.textwidth + 2 * horizontalPadding
        self.height = self.label.textheight + 2 * verticalPadding


@Component(RadioButtonEffect(bgElementFunc=lambda parent, _: parent.highlight, opacityHover=0.3, opacityMouseDown=0.9, audioOnEntry='store_menuhover', audioOnClick='store_click'))

class CategoryButton(Container):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.categoryId = attributes.categoryId
        self.highlight = Sprite(name='hoverGradient', bgParent=self, texturePath='res:/UI/Texture/Vgs/store-button-gradient.png', color=CATEGORY_GLOW_COLOR)
        Fill(name='BackgroundColor', bgParent=self, color=HEADER_BG_COLOR)
        self.label = VgsLabelMedium(parent=self, text=attributes.label, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=CATEGORY_TEXT_COLOR, top=-1)
        self.onClick = attributes.onClick

    def OnClick(self, *args):
        self.onClick(self.categoryId)

    def OnActiveStateChange(self):
        if self.isActive:
            self.label.SetTextColor(Color.WHITE)
        else:
            self.label.SetTextColor(CATEGORY_TEXT_COLOR)


@Component(RadioButtonEffect(bgElementFunc=lambda parent, _: parent.highlight, opacityHover=0.3, opacityMouseDown=0.7, audioOnEntry='store_menuhover', audioOnClick='store_click'))

class SubCategoryButton(Container):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.categoryId = attributes.categoryId
        self.highlight = Sprite(name='hoverGradient', bgParent=self, texturePath='res:/UI/Texture/Vgs/store-button-gradient2.png', color=TAG_GLOW_COLOR)
        Fill(name='BackgroundColor', bgParent=self, color=TAG_COLOR)
        self.label = VgsLabelMedium(text=attributes.label, parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=SUBCATEGORY_TEXT_COLOR, top=-1)
        self.width = self.label.actualTextWidth + 2 * TAG_TEXT_PADDING
        self.onClick = attributes.onClick

    def OnClick(self, *args):
        self.onClick(self.categoryId)

    def OnActiveStateChange(self):
        if self.isActive:
            self.label.SetTextColor(Color.WHITE)
        else:
            self.label.SetTextColor(SUBCATEGORY_TEXT_COLOR)


class VgsFilterCombo(Combo):
    default_adjustWidth = True
    default_name = 'VgsFilterCombo'
    default_fontStyle = fontConst.STYLE_SMALLTEXT
    default_fontsize = 14

    def Prepare_Underlay_(self):
        self.sr.backgroundFrame = GradientSprite(bgParent=self, rotation=-math.pi / 2, rgbData=[(0, (1.0, 1.0, 1.0))], alphaData=[(0, 0.5), (0.3, 0.2), (0.6, 0.08)], opacity=0.0)
        Fill(bgParent=self, name='BackgroundColor', color=CATEGORY_COLOR)

    def Prepare_SelectedText_(self):
        self.sr.selected = Label(text='', fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize, parent=self.sr.textclipper, name='value', align=uiconst.CENTERLEFT, left=6, state=uiconst.UI_DISABLED, color=Color.WHITE)


class LazyUrlSprite(Container):
    default_name = 'LazyUrlSprite'
    default_clipChildren = False

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        loadSize = attributes.loadSize or 100
        self.loadingWheel = LoadingWheel(parent=self, align=uiconst.CENTER, width=loadSize, height=loadSize, opacity=0.2)
        self.sprite = Sprite(bgParent=self, align=uiconst.TOALL)
        self.SetImageFromUrl(attributes.imageUrl)

    def SetImageFromUrl(self, imageUrl):
        uthread.new(self._SetImageFromUrl, imageUrl)

    def _SetImageFromUrl(self, imageUrl):
        LoadImageToSprite(self.sprite, imageUrl)
        uicore.animations.SpMaskIn(self.sprite, duration=1)
        self.loadingWheel.Close()
