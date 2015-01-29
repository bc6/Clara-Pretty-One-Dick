#Embedded file name: eve/client/script/ui/view/aurumstore\vgsDetailContainer.py
import math
import carbonui.const as uiconst
import inventorycommon.const as invconst
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.util.color import Color
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
import localization
import uthread
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLoadingWheel import LoadingWheel
from eve.client.script.ui.shared.redeem.redeemPanel import StaticRedeemContainer, RedeemPanel
from eve.client.script.ui.util import uix
from eve.client.script.ui.util.uiComponents import Component, ButtonEffect
from eve.client.script.ui.view.aurumstore.vgsOffer import GetPreviewType, VgsOfferPreview
from eve.client.script.ui.view.aurumstore.vgsUiConst import BACKGROUND_COLOR, BUY_AUR_BUTTON_COLOR, BUY_BUTTON_COLOR, HEADER_BG_COLOR, REDEEM_BUTTON_BACKGROUND_COLOR, REDEEM_BUTTON_FILL_COLOR, TAG_COLOR, VGS_FONTSIZE_MEDIUM
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import VgsLabelLarge, VgsLabelSmall, DetailButton, ExitButton, AurLabelLarge
from eve.common.script.sys.eveCfg import IsPreviewable
import logging
from eve.client.script.ui.view.viewStateConst import ViewState
import uicontrols
logger = logging.getLogger(__name__)
TOP_PANEL_HEIGHT = 512
BOTTOM_PANEL_HEIGHT = 220
PRODUCTSCROLL_PANEL_HEIGHT = 175
SINGLE_PRODUCT_ENTRY_HEIGHT = 66
BUY_PANEL_HEIGHT = BOTTOM_PANEL_HEIGHT - PRODUCTSCROLL_PANEL_HEIGHT
CONTAINER_WIDTH = 512
EXIT_BUTTON_PADDING = 4
PROGRESS_TRANSITION_TIME = 0.7
TEXT_PADDING = 10
FRAME_WIDTH = 10
FRAME_COLOR = (1.0, 1.0, 1.0, 0.25)
SOUND_ENTRY_ENTER = 'wise:/msg_ListEntryEnter_play'
SOUND_ENTRY_CLICK = 'wise:/msg_ListEntryClick_play'
QUANTITY_MIN = 1
QUANTITY_MAX = 99

def GetSortedTokens(productQuantities):
    return localization.util.Sort(productQuantities.values(), key=lambda (typeID, _): cfg.invtypes.Get(typeID).typeName)


@Component(ButtonEffect(bgElementFunc=lambda self, _: self.highlight, opacityHover=0.1, opacityMouseDown=0.4, audioOnEntry=SOUND_ENTRY_ENTER, audioOnClick=SOUND_ENTRY_CLICK))

class VgsDetailProduct(Container):
    """
    Expects: typeID, quantity
    """
    default_height = SINGLE_PRODUCT_ENTRY_HEIGHT
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        super(VgsDetailProduct, self).ApplyAttributes(attributes)
        self.typeID = attributes.typeID
        self.onClick = attributes.onClick
        self.highlight = Sprite(name='hoverGradient', bgParent=self, texturePath='res:/UI/Texture/Vgs/store-button-gradient2.png', color=(0.2, 0.7, 1.0))
        iconCont = Container(parent=self, align=uiconst.TOLEFT, width=64, height=64, padding=(TEXT_PADDING,
         1,
         TEXT_PADDING,
         1), state=uiconst.UI_DISABLED)
        Sprite(bgParent=iconCont, name='background', texturePath='res:/UI/Texture/classes/InvItem/bgNormal.png')
        techIcon = uix.GetTechLevelIcon(typeID=self.typeID)
        isCopy = cfg.invtypes.Get(self.typeID).categoryID == invconst.categoryBlueprint
        if techIcon:
            iconCont.children.append(techIcon)
        Icon(parent=iconCont, align=uiconst.TOPLEFT, typeID=self.typeID, size=64, state=uiconst.UI_DISABLED, isCopy=isCopy)
        container = Container(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        VgsLabelSmall(parent=container, align=uiconst.CENTERLEFT, text=localization.GetByLabel('UI/Contracts/ContractsWindow/TypeNameWithQuantity', typeID=self.typeID, quantity=attributes.quantity))
        if IsPreviewable(GetPreviewType(self.typeID)):
            self.cursor = uiconst.UICURSOR_MAGNIFIER
        else:
            self.disabled = True

    def OnClick(self):
        self.onClick(self.typeID)


class BasePurchasePanel(Container):
    default_align = uiconst.TOPLEFT
    default_height = BOTTOM_PANEL_HEIGHT
    default_state = uiconst.UI_HIDDEN

    def ApplyAttributes(self, attributes):
        super(BasePurchasePanel, self).ApplyAttributes(attributes)

    def OnPanelActivated(self):
        """ Trigger any animations/sounds that should start once the panel has appeared """
        pass


class PurchaseDetailsPanel(BasePurchasePanel):
    """ Contains the list of products, the total price and the BUY button """
    default_name = 'purchaseDetailsPanel'

    def ApplyAttributes(self, attributes):
        super(PurchaseDetailsPanel, self).ApplyAttributes(attributes)
        self.button = None
        self.offer = attributes.offer
        self.aurumBalance = attributes.aurumBalance
        self.buyOfferCallback = attributes.buyOfferCallback
        self.previewCallback = attributes.previewCallback
        self.CreateProductLayout(self.offer)
        self.CreateBuyLayout(self.offer, self.aurumBalance)

    def CreateProductLayout(self, offer):
        productContainer = Container(name='productContainer', parent=self, align=uiconst.TOTOP, height=PRODUCTSCROLL_PANEL_HEIGHT)
        productScroll = ScrollContainer(parent=productContainer, align=uiconst.TOALL, padTop=16)
        productQuantities = GetSortedTokens(offer.productQuantities)
        for typeID, quantity in productQuantities:
            VgsDetailProduct(parent=productScroll, typeID=typeID, quantity=quantity, onClick=self.previewCallback)

    def CreateBuyLayout(self, offer, aurumBalance):
        self.buyContainer = Container(name='buyContainer', parent=self, align=uiconst.TOTOP, height=BUY_PANEL_HEIGHT)
        self.priceLabel = AurLabelLarge(parent=self.buyContainer, align=uiconst.TOLEFT, amount=offer.price, baseAmount=offer.basePrice, padding=(10, 7, 0, 6))
        self.button = DetailButton(parent=self.buyContainer, align=uiconst.TORIGHT, left=TEXT_PADDING, padTop=8, padBottom=8)
        self.UpdateButton(offer.price)
        self.quantityEdit = SinglelineEdit(parent=self.buyContainer, integermode=True, width=30, fontsize=VGS_FONTSIZE_MEDIUM, align=uiconst.TORIGHT, left=TEXT_PADDING, padTop=6, padBottom=10, bgColor=TAG_COLOR, OnChange=self.OnQuantityChange, maxLength=2, hint=localization.GetByLabel('UI/Common/Quantity'))
        self.quantityEdit.IntMode(minint=QUANTITY_MIN, maxint=QUANTITY_MAX)
        self.quantityEdit.sr.background.Hide()

    def UpdateButton(self, offerPrice):
        if self.aurumBalance >= offerPrice:
            buttonLabel = localization.GetByLabel('UI/VirtualGoodsStore/OfferDetailBuyNowButton')
            buttonFunc = self.OnBuyClick
            color = BUY_BUTTON_COLOR
        else:
            buttonLabel = localization.GetByLabel('UI/VirtualGoodsStore/BuyAurOnline')
            buttonFunc = self._BuyAurum
            color = BUY_AUR_BUTTON_COLOR
        self.button.OnClick = buttonFunc
        self.button.SetText(buttonLabel)
        self.button.color.SetRGB(*color)

    def OnQuantityChange(self, text):
        try:
            quantity = int(text)
            quantity = max(QUANTITY_MIN, min(quantity, QUANTITY_MAX))
        except ValueError:
            quantity = QUANTITY_MIN

        newOfferPrice = self.offer.price * quantity
        self.priceLabel.SetAmount(newOfferPrice, self.offer.basePrice * quantity)
        self.UpdateButton(newOfferPrice)

    def _BuyAurum(self):
        sm.GetService('audio').SendUIEvent('store_aur')
        sm.GetService('viewState').GetView(ViewState.VirtualGoodsStore)._LogBuyAurum('DetailButton')
        uicore.cmd.BuyAurumOnline()

    def OnBuyClick(self, *args):
        logger.debug('OnBuyClick %s' % (self.offer,))
        sm.GetService('audio').SendUIEvent('store_buy')
        self.button.Disable()
        self.buyOfferCallback(self.offer, quantity=self.quantityEdit.GetValue())


class PurchaseProgressPanel(BasePurchasePanel):
    """ Contains the purchase progress UI """
    default_name = 'purchaseProgressPanel'

    def ApplyAttributes(self, attributes):
        super(PurchaseProgressPanel, self).ApplyAttributes(attributes)
        cont = Container(parent=self, align=uiconst.TOTOP, height=72, padTop=4)
        LoadingWheel(parent=cont, align=uiconst.CENTER, width=100, height=100)
        captionCont = Container(parent=self, align=uiconst.TOTOP, height=40)
        VgsLabelLarge(parent=captionCont, align=uiconst.CENTER, text=localization.GetByLabel('UI/VirtualGoodsStore/Purchase/Processing'))


class PurchaseResultPanel(BasePurchasePanel):
    """ Contains the purchase completed/failed UI """
    default_name = 'purchaseResultPanel'

    def ApplyAttributes(self, attributes):
        super(PurchaseResultPanel, self).ApplyAttributes(attributes)
        self.audioEventName = attributes.audioEventName
        cont = Container(parent=self, align=uiconst.TOTOP, height=72, padTop=4)
        self.iconForegroundTransform = Transform(parent=cont, align=uiconst.CENTERTOP, width=72, height=78, scalingCenter=(0.5, 0.5))
        self.iconForeground = Sprite(parent=self.iconForegroundTransform, align=uiconst.CENTER, texturePath=attributes.iconForegroundTexturePath, width=72, height=64, opacity=0)
        self.iconBackgroundTransform = Transform(parent=cont, align=uiconst.CENTERTOP, width=72, height=78, scalingCenter=(0.5, 0.5))
        self.iconBackground = Sprite(parent=self.iconBackgroundTransform, align=uiconst.CENTER, texturePath=attributes.iconBackgroundTexturePath, width=72, height=64, opacity=0)
        captionCont = Container(parent=self, align=uiconst.TOTOP, height=40, padding=(TEXT_PADDING,
         4,
         TEXT_PADDING,
         0))
        VgsLabelLarge(parent=captionCont, align=uiconst.CENTER, text=attributes.textTitle)

    def OnPanelActivated(self):
        if self.audioEventName:
            sm.GetService('audio').SendUIEvent(self.audioEventName)
        uicore.animations.FadeIn(self.iconBackground, duration=0.5, timeOffset=PROGRESS_TRANSITION_TIME)
        uicore.animations.FadeIn(self.iconForeground, duration=0.5, timeOffset=PROGRESS_TRANSITION_TIME + 0.5)
        uicore.animations.Tr2DScaleTo(self.iconBackgroundTransform, (2.0, 2.0), (1.0, 1.0), duration=0.25, timeOffset=PROGRESS_TRANSITION_TIME)
        uicore.animations.Tr2DScaleTo(self.iconForegroundTransform, (2.0, 2.0), (1.0, 1.0), duration=0.25, timeOffset=PROGRESS_TRANSITION_TIME + 0.5)


class VgsDetailContainer(Container):
    default_name = 'VgsDetailContainer'
    default_alignMode = None
    default_state = uiconst.UI_PICKCHILDREN
    frameColor = Color.GRAY9

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.vgsUiController = attributes.vgsUiController
        self.offer = attributes.offer
        self.align = uiconst.TOALL
        fullWidth, fullHeight = self.GetAbsoluteSize()
        self.backgroundBottomContainer = uicontrols.ContainerAutoSize(parent=self, name='backgroundBottomContainer', align=uiconst.TOBOTTOM_NOPUSH, state=uiconst.UI_PICKCHILDREN, width=fullWidth)
        self.backgroundTopContainer = Container(parent=self, name='backgroundTopContainer', align=uiconst.TOBOTTOM, state=uiconst.UI_PICKCHILDREN, height=fullHeight, width=fullWidth)
        self.offerContainer = Container(parent=self.backgroundTopContainer, name='offerContainer', state=uiconst.UI_NORMAL, align=uiconst.CENTER, width=CONTAINER_WIDTH, height=TOP_PANEL_HEIGHT + BOTTOM_PANEL_HEIGHT, bgColor=BACKGROUND_COLOR)
        Fill(bgParent=self.offerContainer, color=FRAME_COLOR, padding=[-FRAME_WIDTH] * 4, fillCenter=True)
        ExitButton(parent=self.offerContainer, align=uiconst.TOPRIGHT, onClick=self.CloseOffer, top=EXIT_BUTTON_PADDING, left=EXIT_BUTTON_PADDING)
        self.preview = VgsOfferPreview(parent=self.offerContainer, align=uiconst.TOTOP, height=TOP_PANEL_HEIGHT, offer=self.offer)
        self.CreateBottomLayout(self.offer, attributes.aurumBalance)
        self.CreateFakeRedeemPanel()

    def CreateBottomLayout(self, offer, aurumBalance):
        self.bottomContainer = Container(name='bottomContainer', parent=self.offerContainer, align=uiconst.TOTOP, clipChildren=True, height=BOTTOM_PANEL_HEIGHT)
        Fill(align=uiconst.TOALL, bgParent=self.bottomContainer, color=HEADER_BG_COLOR)
        GradientSprite(align=uiconst.TOALL, bgParent=self.bottomContainer, rgbData=((0.0, (0.0, 0.0, 0.0)), (1.0, (0.0, 0.0, 0.0))), alphaData=((0.0, 0.8), (0.2, 0.6), (0.6, 0.0)), rotation=math.pi * 0.4)
        self.purchaseDetailsPanel = PurchaseDetailsPanel(parent=self.bottomContainer, offer=offer, aurumBalance=aurumBalance, buyOfferCallback=self.vgsUiController.BuyOffer, previewCallback=self.OnPreviewType, state=uiconst.UI_PICKCHILDREN, width=CONTAINER_WIDTH)
        self.activeBottomPanel = self.purchaseDetailsPanel
        self.purchaseProgressPanel = PurchaseProgressPanel(parent=self.bottomContainer, width=CONTAINER_WIDTH)
        self.purchaseSuccessPanel = PurchaseResultPanel(parent=self.bottomContainer, closeOfferCallback=self.CloseOffer, iconForegroundTexturePath='res:/UI/Texture/vgs/purchase_success_fg.png', iconBackgroundTexturePath='res:/UI/Texture/vgs/purchase_success_bg.png', textTitle=localization.GetByLabel('UI/VirtualGoodsStore/Purchase/Completed'), audioEventName='store_purchase_success', width=CONTAINER_WIDTH)
        self.purchaseFailurePanel = PurchaseResultPanel(parent=self.bottomContainer, closeOfferCallback=self.CloseOffer, iconForegroundTexturePath='res:/UI/Texture/vgs/purchase_fail_fg.png', iconBackgroundTexturePath='res:/UI/Texture/vgs/purchase_fail_bg.png', textTitle=localization.GetByLabel('UI/VirtualGoodsStore/Purchase/Failed'), audioEventName='store_purchase_failure', width=CONTAINER_WIDTH)
        VgsLabelSmall(parent=self.purchaseFailurePanel, align=uiconst.TOTOP, text='<center>%s</center>' % localization.GetByLabel('UI/VirtualGoodsStore/Purchase/FailureReasonUnknown'), padding=(TEXT_PADDING,
         TEXT_PADDING,
         TEXT_PADDING,
         0))

    def CreateRedeemPanel(self, offer, offerQuantity):
        self.redeemContainer = StaticRedeemContainer(parent=self.purchaseSuccessPanel, name='offerRedeemQueueContent', align=uiconst.TOTOP, padTop=TEXT_PADDING, redeemTokens=GetSortedTokens(offer.productQuantities), offerQuantity=offerQuantity, clipChildren=False, containerWidth=CONTAINER_WIDTH, dragEnabled=False, minimizeTokens=True)
        self.successDescriptionText = VgsLabelSmall(parent=self.purchaseSuccessPanel, align=uiconst.TOTOP, text='<center>%s</center>' % localization.GetByLabel('UI/VirtualGoodsStore/Purchase/NewPurchaseInstruction'), padding=(TEXT_PADDING,
         TEXT_PADDING,
         TEXT_PADDING,
         0))
        self.successDescriptionText.opacity = 0.0

    def CreateFakeRedeemPanel(self):
        instructionText = '<url=localsvc:service=vgsService&method=ShowRedeemUI>%s</url>' % (localization.GetByLabel('UI/RedeemWindow/ClickToInitiateRedeeming'),)
        self.fakeRedeemingPanel = RedeemPanel(parent=self.backgroundBottomContainer, name='fakeRedeemPanel', align=uiconst.TOBOTTOM, dragEnabled=False, redeemButtonBackgroundColor=REDEEM_BUTTON_BACKGROUND_COLOR, redeemButtonFillColor=REDEEM_BUTTON_FILL_COLOR, buttonClick=None, instructionText=instructionText)
        self.fakeRedeemingPanel.UpdateDisplay(animate=False)
        self.fakeRedeemingPanel.HidePanel(animate=False)
        self.vgsUiController.view.storeContainer.redeemingPanel.HidePanel()
        self.vgsUiController.view.storeContainer.redeemingPanel.SetListenToRedeemQueueUpdatedEvents(False)

    def OnPreviewType(self, typeID):
        self.preview.typeID = typeID

    def OpenFakeRedeemPanel(self):
        self.fakeRedeemingPanel.ExpandPanel(animate=True, showNewItems=False)

    def SwitchToProgressPanel(self):
        self.SwitchToPanel(self.purchaseProgressPanel)

    def SwitchToSuccessPanel(self, offerQuantity):
        self.CreateRedeemPanel(self.offer, offerQuantity)
        self.SwitchToPanel(self.purchaseSuccessPanel)
        self.OpenFakeRedeemPanel()
        self.fakeRedeemingPanel.AddRedeemContainerContent(self.redeemContainer)
        uicore.animations.MoveOutTop(self.redeemContainer, amount=self.redeemContainer.height, timeOffset=1.0, sleep=True, callback=self.redeemContainer.Close)
        uicore.animations.FadeIn(self.successDescriptionText, duration=1.0, sleep=True)
        self.fakeRedeemingPanel.HidePanel(animate=True)

    def SwitchToFailurePanel(self):
        self.SwitchToPanel(self.purchaseFailurePanel)

    def HasSuccessfullyBoughtItem(self):
        return self.activeBottomPanel == self.purchaseSuccessPanel

    def SwitchToPanel(self, newPanel):
        newPanel.OnPanelActivated()
        uicore.animations.MoveOutLeft(self.activeBottomPanel, CONTAINER_WIDTH, duration=PROGRESS_TRANSITION_TIME)
        self.activeBottomPanel = newPanel
        self.activeBottomPanel.state = uiconst.UI_PICKCHILDREN
        uicore.animations.MoveInFromRight(self.activeBottomPanel, CONTAINER_WIDTH, duration=PROGRESS_TRANSITION_TIME, sleep=True)

    def CloseOffer(self, *args):
        uthread.new(sm.GetService('vgsService').GetUiController().CloseOffer)

    def PrepareClose(self):
        self.preview.PrepareClose()

    def _OnResize(self, *args):
        if not hasattr(self, 'backgroundTopContainer'):
            return
        self.backgroundTopContainer.height = self.parent.GetAbsoluteSize()[1]
