#Embedded file name: eve/client/script/ui/view/aurumstore\aurumStoreView.py
from eve.client.script.ui.view.aurumstore.loadingPanel import LoadingPanel
import uthread
import carbonui.const as uiconst
from carbonui.primitives.fill import Fill
from carbonui.util.color import Color
from eve.client.script.ui.services.viewStateSvc import View
from eve.client.script.ui.view.aurumstore.aurumStoreContainer import AurumStoreContainer
from eve.client.script.ui.view.viewStateConst import ViewOverlay
import locks
import util
import blue
import logging
import localization
from crestclient.errors import ServiceUnavailableException
logger = logging.getLogger(__name__)
_SearchLock = locks.RLock()
STORE_REQUEST_TIMEOUT = 15

class AurumStoreView(View):
    __notifyevents__ = ['OnShowUI']
    __suppressedOverlays__ = {ViewOverlay.SidePanels,
     ViewOverlay.Target,
     ViewOverlay.ShipUI,
     ViewOverlay.StationEntityBrackets}
    __subLayers__ = [('l_vgsabovesuppress', None, None), ('l_vgssuppress', None, None)]
    _debug = False

    def LoadView(self, **kwargs):
        View.LoadView(self, *kwargs)
        if not self._debug:
            uicore.layer.main.display = False
        uicore.layer.abovemain.display = False
        self._SearchTasklet = None
        uthread.new(self.SetupStoreData)
        sm.GetService('audio').SendUIEvent('store_view_start')

    def SetupStoreData(self):
        logger.debug('SetupStoreData')
        loadingPanel = LoadingPanel(parent=uicore.layer.vgsabovesuppress)
        if session.userid is None:
            logger.warn('SetupStoreData - Session has no userid. Store will be unavailable')
            loadingPanel.ShowStoreUnavailable()
            return
        try:
            self.store = sm.GetService('vgsService').GetStore()
            logger.debug('SetupStoreData - Spawning Get* threads')
            getRootCategoryListTasklet = uthread.newJoinable(self.store.GetRootCategoryList)
            getAccountTasklet = uthread.newJoinable(self.store.GetAccount)
            getOffersTasklet = uthread.newJoinable(self.store.GetOffers)
            logger.debug('SetupStoreData - Creating AurumStoreContainer')
            self.storeContainer = AurumStoreContainer(parent=self.layer)
            logger.debug('SetupStoreData - Joining on Get* threads')
            rootCategoryList = uthread.waitForJoinable(getRootCategoryListTasklet, timeout=STORE_REQUEST_TIMEOUT)
            account = uthread.waitForJoinable(getAccountTasklet, timeout=STORE_REQUEST_TIMEOUT)
            aurumAmount = account.GetAurumBalance()
            uthread.waitForJoinable(getOffersTasklet, timeout=STORE_REQUEST_TIMEOUT)
            logger.debug('SetupStoreData - Populating UI')
            self.storeContainer.SetCategories(rootCategoryList)
            self.storeContainer.LoadLandingPage()
            self.viewOpenedTimer = sm.GetService('viewState').lastViewOpenTime
            self.SubscribeToStoreEvents()
        except uthread.TaskletWaitTimeout:
            logger.warn('SetupStoreData timed out, store will be unavailable')
            loadingPanel.ShowStoreUnavailable(localization.GetByLabel('UI/VirtualGoodsStore/StoreUnavailableTimeout'))
            raise
        except ServiceUnavailableException as e:
            message = None
            if 'certificate verify failed' in e.message:
                message = localization.GetByLabel('UI/VirtualGoodsStore/StoreUnavailableSSL')
            loadingPanel.ShowStoreUnavailable(message)
            raise
        except Exception as e:
            message = None
            logger.warn('SetupStoreData - Store loading failed')
            if e.message == 'tokenMissing':
                message = localization.GetByLabel('UI/VirtualGoodsStore/StoreUnavailableToken')
            loadingPanel.ShowStoreUnavailable(message)
            raise

        logger.debug('SetupStoreData - Loading completed successfully, showing store')
        uicore.animations.FadeOut(loadingPanel, duration=0.5, timeOffset=0.5, sleep=True)
        loadingPanel.Close()
        self.storeContainer.SetAUR(aurumAmount)

    def SubscribeToStoreEvents(self):
        self.store.GetAccount().SubscribeToAurumBalanceChanged(self.storeContainer.SetAUR)

    def UnsubscribeFromStoreEvents(self):
        try:
            self.store.GetAccount().UnsubscribeFromAurumBalanceChanged(self.storeContainer.SetAUR)
        except Exception:
            self.LogError('Error while unsubscribing from store events')

    def UnloadView(self):
        View.UnloadView(self)
        sm.GetService('audio').SendUIEvent('store_view_end')
        self.UnsubscribeFromStoreEvents()
        if getattr(self, 'storeContainer', None) is not None:
            self.storeContainer.Close()
        uicore.layer.main.display = True
        uicore.layer.abovemain.display = True

    def OnShowUI(self):
        if not self._debug:
            uicore.layer.main.display = False

    def SetupSuppressLayer(self):
        if len(uicore.layer.vgssuppress.children) == 0:
            Fill(parent=uicore.layer.vgssuppress, color=Color.BLACK)
        uicore.layer.vgssuppress.opacity = 0.0
        uicore.layer.vgssuppress.state = uiconst.UI_DISABLED

    def ActivateSuppressLayer(self, duration = 0.25, clickCallback = None):
        self.SetupSuppressLayer()
        uicore.layer.vgssuppress.state = uiconst.UI_NORMAL
        if clickCallback is not None:
            uicore.layer.vgssuppress.OnClick = clickCallback
        uicore.animations.FadeTo(uicore.layer.vgssuppress, uicore.layer.vgssuppress.opacity, 0.7, duration=duration)

    def DeactivateSuppressLayer(self, duration = 0.25, callback = None):
        uicore.layer.vgssuppress.state = uiconst.UI_DISABLED
        uicore.animations.FadeOut(uicore.layer.vgssuppress, duration=duration, sleep=True, callback=callback)

    def Search(self, searchString):
        if self._SearchTasklet is not None:
            with _SearchLock:
                if self._SearchTasklet is not None:
                    self._SearchTasklet.kill()
        self._SearchTasklet = uthread.new(self._Search, searchString)

    def _GetViewTime(self):
        return blue.os.GetWallclockTime() - self.viewOpenedTimer

    def _Search(self, searchString):
        blue.pyos.synchro.SleepWallclock(280)
        with _SearchLock:
            offers = self.store.SearchOffers(searchString)
            self._LogSearch(searchString)
            print len(offers)
            self.storeContainer.SetOffers(offers)

    def _LogStoreEvent(self, columnNames, eventName, *args):
        with util.ExceptionEater('eventLog'):
            uthread.new(sm.ProxySvc('eventLog').LogClientEvent, 'store', columnNames, eventName, *args)

    def _LogPurchase(self, offerID, quantity, success):
        self._LogStoreEvent(['offerID',
         'quantity',
         'success',
         'viewTime'], 'Purchase', offerID, quantity, success, self._GetViewTime())

    def _LogOpenOffer(self, offerID):
        self._LogStoreEvent(['offerID', 'viewTime'], 'OpenOffer', offerID, self._GetViewTime())

    def _LogBannerClick(self, imageUrl, actionKey, actionValue):
        self._LogStoreEvent(['imageUrl',
         'actionKey',
         'actionValue',
         'viewTime'], 'BannerClick', imageUrl, actionKey, actionValue, self._GetViewTime())

    def _LogBuyAurum(self, location):
        self._LogStoreEvent(['aurumBalance', 'location', 'viewTime'], 'BuyAurum', self.store.GetAccount().GetAurumBalance(), location, self._GetViewTime())

    def _LogFilterChange(self, filterName):
        self._LogStoreEvent(['filterName', 'viewTime'], 'FilterChange', filterName, self._GetViewTime())

    def _LogSearch(self, searchString):
        self._LogStoreEvent(['searchString', 'viewTime'], 'search', searchString, self._GetViewTime())
