#Embedded file name: eve/client/script/ui/view/aurumstore\vgsUiController.py
import carbonui.const as uiconst
import logging
from eve.client.script.ui.util.uiComponents import RunThreadOnce
from eve.client.script.ui.view.aurumstore.vgsDetailContainer import VgsDetailContainer
from eve.client.script.ui.view.viewStateConst import ViewState
import blue
logger = logging.getLogger(__name__)
OPEN_OFFER_THREAD_KEY = 'OPEN_OFFER'
CLOSE_OFFER_THREAD_KEY = 'CLOSE_OFFER'
MINIMUM_PROGRESS_DISPLAY_TIME = 1.2 * const.SEC
OFFER_ADDED_TO_REDEEMING_QUEUE_TIME = 0.75
REDEEMING_BUTTON_SHOW_TIME = 2

class VgsUiController(object):

    def __init__(self, vgsService, viewStateService):
        self.viewState = viewStateService
        self.vgsService = vgsService
        self.view = self.viewState.GetView(ViewState.VirtualGoodsStore)
        self.detailContainer = None
        self.buyIsInProgress = False

    @RunThreadOnce(OPEN_OFFER_THREAD_KEY)
    def ShowOffer(self, offerId, suppressFullScreen = False):
        self.ForceClose()
        offer = self.vgsService.GetStore().GetOffer(offerId)
        if suppressFullScreen:
            parent = uicore.layer.abovemain
        else:
            parent = uicore.layer.vgsabovesuppress
        sm.GetService('audio').SendUIEvent('store_click')
        self.detailContainer = VgsDetailContainer(parent=parent, align=uiconst.CENTER, opacity=0.0, vgsUiController=self, offer=offer, aurumBalance=self.vgsService.GetStore().GetAccount().GetAurumBalance())
        self.view._LogOpenOffer(offerId)
        openDuration = 0.25
        if not suppressFullScreen:
            if not self.viewState.IsViewActive(ViewState.VirtualGoodsStore):
                self.viewState.ActivateView(ViewState.VirtualGoodsStore)
            self.view.ActivateSuppressLayer(duration=openDuration, clickCallback=self.CloseOffer)
        uicore.animations.FadeTo(self.detailContainer, 0.0, 1.0, duration=openDuration, sleep=True)

    def CanClose(self):
        return self.detailContainer is not None and not self.detailContainer.destroyed and not self.buyIsInProgress

    def ForceClose(self):
        if not self.CanClose():
            return
        logger.debug('Force closing offer')
        self.view.storeContainer.redeemingPanel.SetListenToRedeemQueueUpdatedEvents(True)
        self.view.storeContainer.redeemingPanel.UpdateDisplay(animate=False)
        self.detailContainer.fakeRedeemingPanel.CollapsePanel(animate=False)
        self.detailContainer.Close()
        self.view.DeactivateSuppressLayer(duration=0.0)

    @RunThreadOnce(CLOSE_OFFER_THREAD_KEY)
    def CloseOffer(self):
        if not self.CanClose():
            return
        closeDuration = 0.25
        self.view.storeContainer.redeemingPanel.SetListenToRedeemQueueUpdatedEvents(True)
        self.view.storeContainer.redeemingPanel.UpdateDisplay(animate=False)
        self.detailContainer.fakeRedeemingPanel.CollapsePanel(duration=closeDuration)
        self.detailContainer.PrepareClose()
        uicore.animations.FadeOut(self.detailContainer.offerContainer, duration=closeDuration)
        self.view.DeactivateSuppressLayer(duration=closeDuration, callback=self.detailContainer.Close)

    def BuyOffer(self, offer, quantity = 1):
        self.vgsService.LogInfo('VgsUiController.BuyOffer', offer, quantity)
        self.buyIsInProgress = True
        try:
            self.detailContainer.SwitchToProgressPanel()
            startTime = blue.os.GetWallclockTime()
            result = None
            try:
                result = self.vgsService.GetStore().BuyOffer(offer, qty=quantity)
                blue.pyos.synchro.SleepUntilWallclock(startTime + MINIMUM_PROGRESS_DISPLAY_TIME)
            finally:
                if result:
                    self.view._LogPurchase(offer.id, quantity, True)
                    self.detailContainer.SwitchToSuccessPanel(quantity)
                else:
                    self.view._LogPurchase(offer.id, quantity, False)
                    self.detailContainer.SwitchToFailurePanel()

        finally:
            self.buyIsInProgress = False
