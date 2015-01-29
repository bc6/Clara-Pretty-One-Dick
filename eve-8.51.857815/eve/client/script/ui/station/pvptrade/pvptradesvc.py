#Embedded file name: eve/client/script/ui/station/pvptrade\pvptradesvc.py
import service
import form
import uicontrols
import uicls

class PVPTradeService(service.Service):
    __guid__ = 'svc.pvptrade'
    __exportedcalls__ = {'StartTradeSession': []}
    __notifyevents__ = ['OnTrade']

    def StartTradeSession(self, charID):
        tradeSession = sm.RemoteSvc('trademgr').InitiateTrade(charID)
        tradeContainerID = tradeSession.List().tradeContainerID
        checkWnd = uicontrols.Window.GetIfOpen(windowID='trade_%d' % tradeContainerID)
        if checkWnd and not checkWnd.destroyed:
            checkWnd.Maximize()
        else:
            self.OnInitiate(charID, tradeSession)

    def OnTrade(self, what, *args):
        self.LogInfo('OnTrade', what, args)
        getattr(self, 'On' + what)(*args)

    def OnInitiate(self, charID, tradeSession):
        self.LogInfo('OnInitiate', charID, tradeSession)
        tradeContainerID = tradeSession.List().tradeContainerID
        checkWnd = uicontrols.Window.GetIfOpen(windowID='trade_%d' % tradeContainerID)
        if checkWnd:
            return
        form.PVPTrade.Open(windowID='trade_%d' % tradeContainerID, tradeSession=tradeSession)

    def OnCancel(self, containerID):
        w = uicontrols.Window.GetIfOpen(windowID='trade_' + str(containerID))
        if w:
            w.OnCancel()

    def OnStateToggle(self, containerID, state):
        w = uicontrols.Window.GetIfOpen(windowID='trade_' + str(containerID))
        if w:
            w.OnStateToggle(state)

    def OnMoneyOffer(self, containerID, money):
        w = uicontrols.Window.GetIfOpen(windowID='trade_' + str(containerID))
        if w:
            w.OnMoneyOffer(money)

    def OnTradeComplete(self, containerID):
        w = uicontrols.Window.GetIfOpen(windowID='trade_' + str(containerID))
        if w:
            w.OnTradeComplete()
