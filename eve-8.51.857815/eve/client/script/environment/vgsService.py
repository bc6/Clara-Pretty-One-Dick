#Embedded file name: eve/client/script/environment\vgsService.py
"""
    Vgs Service , does the communicating with the vgs server through the crest client
"""
import service
from eve.client.script.ui.view.aurumstore.vgsUiController import VgsUiController
from eve.client.script.ui.view.viewStateConst import ViewState
from vgsclient.store import Store
from vgsclient.vgsCrestConnection import VgsCrestConnection
DEFAULT_STORE = 'EVE Store'
AUR_CURRENCY = 'EAR'
PAYMENT_METHOD = 2

class VgsService(service.Service):
    __guid__ = 'svc.vgsService'
    __servicename__ = 'vgsSvc'
    __displayName__ = 'Vgs Service'
    __startupdependencies__ = ['crestConnectionService', 'viewState', 'redeem']
    __notifyevents__ = ['OnAurumChangeFromVgs',
     'OnRedeemingQueueUpdated',
     'OnSessionChanged',
     'OnUIScalingChange']
    __exportedcalls__ = {'ShowRedeemUI': [service.ROLE_IGB]}

    def Run(self, memStream = None):
        self.LogInfo('Starting Vgs Service')
        self.vgsCrestConnection = VgsCrestConnection(DEFAULT_STORE, self.crestConnectionService)
        self.store = Store(self.vgsCrestConnection)
        self.uiController = VgsUiController(self, self.viewState)

    def ClearCache(self):
        self.store.ClearCache()

    def OnUIScalingChange(self, *args):
        if self.viewState.IsViewActive(ViewState.VirtualGoodsStore):
            self.LogInfo('VgsService.OnUIScalingChange - closing store to avoid UI errors')
            self.viewState.CloseSecondaryView(ViewState.VirtualGoodsStore)

    def OnAurumChangeFromVgs(self, notification):
        if session.userid == notification['userid']:
            self.store.GetAccount().OnAurumChangeFromVgs(notification['balance'])
            sm.GetService('neocom').Blink('aurumStore')

    def OnRedeemingQueueUpdated(self):
        self.store.GetAccount().OnRedeemingQueueUpdated()

    def GetStore(self):
        return self.store

    def GetUiController(self):
        return self.uiController

    def OnSessionChanged(self, isRemote, session, change):
        if self.viewState.IsViewActive(ViewState.VirtualGoodsStore):
            if 'locationid' in change or 'userid' in change:
                self.LogInfo('VgsService.OnSessionChanged - locationid change detected, closing store')
                self.viewState.CloseSecondaryView(ViewState.VirtualGoodsStore)
            elif 'userid' in change:
                self.LogInfo('VgsService.OnSessionChanged - userid change detected, closing store')
                self.viewState.CloseSecondaryView(ViewState.VirtualGoodsStore)

    def ShowRedeemUI(self):
        if session.charid:
            self.redeem.OpenRedeemWindow()
        if self.viewState.IsViewActive(ViewState.VirtualGoodsStore):
            self.uiController.CloseOffer()
            self.viewState.CloseSecondaryView(ViewState.VirtualGoodsStore)
        if session.charid is None:
            uicore.layer.charsel.EnterRedeemMode(animate=True)
