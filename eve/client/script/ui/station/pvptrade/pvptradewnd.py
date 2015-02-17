#Embedded file name: eve/client/script/ui/station/pvptrade\pvptradewnd.py
from carbonui.primitives.sprite import Sprite
from localization import GetByLabel
import uiprimitives
import uicontrols
import uix
import uiutil
import util
import uicls
import carbonui.const as uiconst
import localization
import invCtrl
import invCont
from carbonui.primitives.flowcontainer import FlowContainer
from eve.client.script.ui.control.buttons import Button

class PVPTrade(uicontrols.Window):
    __guid__ = 'form.PVPTrade'
    default_topParentHeight = 0
    default_minSize = (300, 370)
    scope = 'station'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.tradeSession = attributes.tradeSession
        self.tradedShips = []
        self.SetWndIcon()
        buttonParent = FlowContainer(name='buttonParent', parent=self.sr.main, align=uiconst.TOBOTTOM, padding=6, autoHeight=True, centerContent=True, contentSpacing=(6, 6))
        self.acceptButton = Button(parent=buttonParent, label=localization.GetByLabel('UI/PVPTrade/Accept'), func=self.OnClickAccept, align=uiconst.NOALIGN)
        Button(parent=buttonParent, label=localization.GetByLabel('UI/Common/Buttons/Cancel'), func=self.Cancel, align=uiconst.NOALIGN)
        sessionData = self.tradeSession.List()
        herID = sessionData.traders[not sessionData.traders.index(session.charid)]
        self.sr.herinfo = cfg.eveowners.Get(herID)
        mainCont = uiprimitives.Container(name='mainCont', parent=self.sr.main)
        self.sr.my = my = invCont.PlayerTrade(parent=mainCont, align=uiconst.TOTOP_PROP, height=0.5, itemID=sessionData.tradeContainerID, ownerID=session.charid, tradeSession=self.tradeSession, state=uiconst.UI_PICKCHILDREN)
        self.sr.myAccept = my.acceptIcon
        self.sr.myMoney = my.moneyLabel
        self.sr.her = her = invCont.PlayerTrade(parent=mainCont, align=uiconst.TOTOP_PROP, height=0.5, itemID=sessionData.tradeContainerID, ownerID=herID, tradeSession=self.tradeSession, state=uiconst.UI_PICKCHILDREN)
        self.sr.herAccept = her.acceptIcon
        self.sr.herMoney = her.moneyLabel
        offerBtn = Button(parent=my.topCont, label=localization.GetByLabel('UI/PVPTrade/OfferMoney'), func=self.OnClickOfferMoney, args=None, idx=0, pos=(2, 2, 0, 0), align=uiconst.TOPRIGHT)
        self.sr.myIx = sessionData.traders.index(eve.session.charid)
        self.sr.herIx = sessionData.traders.index(herID)
        self.OnMoneyOffer([0, 0])
        self.SetCaption(self.GetWindowCaptionText())

    def _OnClose(self, *args):
        if self and getattr(self, 'sr', None):
            if self.sr.my:
                self.sr.my.Close()
            if self.sr.her:
                self.sr.her.Close()

    def Cancel(self, *etc):
        if self.tradeSession and eve.Message('ConfirmCancelTrade', {}, uiconst.OKCANCEL) == uiconst.ID_OK:
            if self and not self.destroyed and hasattr(self, 'sr'):
                tmp = self.tradeSession
                self.tradeSession = None
                tmp.Abort()
            else:
                eve.Message('TradeNotCanceled')

    CloseByUser = Cancel

    def OnClickAccept(self, *etc):
        self.acceptButton.Disable()
        currentState = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED].index(self.sr.myAccept.state)
        self.tradedShips = []
        tradeItems = self.tradeSession.List().items
        for item in tradeItems:
            if cfg.invgroups.Get(item.groupID).Category().id == const.categoryShip:
                self.tradedShips.append(item.itemID)
                sm.GetService('gameui').KillCargoView(item.itemID)

        try:
            self.tradeSession.ToggleAccept(not currentState)
        except UserError as what:
            if not what.msg.startswith('TradeShipWarning'):
                raise
            msgName, msgDict = what.msg, what.dict
            if msgName is not None:
                if eve.Message('TradeShipWarning', {}, uiconst.OKCANCEL) == uiconst.ID_OK:
                    self.tradeSession.ToggleAccept(not currentState, forceTrade=True)
                else:
                    self.acceptButton.Enable()

    def GetWindowCaptionText(self):
        return localization.GetByLabel('UI/PVPTrade/TradeWith', otherParty=self.sr.herinfo.id)

    def OnStateToggle(self, states):
        self.sr.myAccept.state = (uiconst.UI_HIDDEN, uiconst.UI_DISABLED)[states[self.sr.myIx]]
        self.sr.herAccept.state = (uiconst.UI_HIDDEN, uiconst.UI_DISABLED)[states[self.sr.herIx]]
        if self.sr.myAccept.state == uiconst.UI_DISABLED:
            self.acceptButton.Disable()
        else:
            self.acceptButton.Enable()
        if states[0] and states[1]:
            self.sr.my.invReady = 0
            self.sr.her.invReady = 0
            self.Close()

    def OnMoneyOffer(self, money):
        self.acceptButton.Enable()
        myMoney = util.FmtISK(money[self.sr.myIx])
        if money[self.sr.myIx] > 0:
            myMoney = localization.GetByLabel('UI/PVPTrade/NegativeChangeInFunds', amount=myMoney)
        else:
            myMoney = localization.GetByLabel('UI/PVPTrade/NoChangeInFunds', amount=myMoney)
        herMoney = util.FmtISK(money[self.sr.herIx])
        if money[self.sr.herIx] > 0:
            herMoney = localization.GetByLabel('UI/PVPTrade/PositiveChangeInFunds', amount=herMoney)
        else:
            herMoney = localization.GetByLabel('UI/PVPTrade/NoChangeInFunds', amount=herMoney)
        self.sr.myMoney.text = localization.GetByLabel('UI/PVPTrade/Money', formattedAmount=myMoney)
        self.sr.herMoney.text = localization.GetByLabel('UI/PVPTrade/Money', formattedAmount=herMoney)
        self.OnStateToggle([0, 0])

    def OnClickOfferMoney(self, *etc):
        self.tradeSession.ToggleAccept(False)
        ret = uix.QtyPopup(sm.GetService('wallet').GetWealth(), 0, 0, digits=2)
        if ret is not None and self is not None and not self.destroyed:
            self.tradeSession.OfferMoney(ret['qty'])

    def OnTradeComplete(self):
        for itemID in self.tradedShips:
            sm.GetService('gameui').KillCargoView(itemID)

        eve.Message('TradeComplete', {'name': self.sr.herinfo.name})
        self.sr.my.invReady = 0
        self.sr.her.invReady = 0
        self.Close()

    def OnCancel(self):
        eve.Message('TradeCancel', {'name': self.sr.herinfo.name})
        self.sr.my.invReady = 0
        self.sr.her.invReady = 0
        self.Close()


class PlayerTrade(invCont._InvContBase):
    __guid__ = 'invCont.PlayerTrade'
    __invControllerClass__ = invCtrl.PlayerTrade

    def ApplyAttributes(self, attributes):
        invCont._InvContBase.ApplyAttributes(self, attributes)
        ownerID = attributes.ownerID
        ownerName = cfg.eveowners.Get(ownerID).name
        self.topCont = uiprimitives.Container(parent=self, align=uiconst.TOTOP, height=65, idx=0)
        myImgCont = Sprite(parent=self.topCont, align=uiconst.TOLEFT, width=64, idx=0, texturePath='res:/UI/Texture/silhouette_64.png', left=2)
        sm.GetService('photo').GetPortrait(ownerID, 64, myImgCont)
        myImgCont.OnClick = (self.ShowCharInfo, ownerID)
        myImgCont.hint = ownerName
        ownerLink = GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=ownerName, info=('showinfo', const.typeCharacterAmarr, ownerID))
        uicontrols.EveLabelMedium(text=ownerLink, parent=self.topCont, left=72, top=2, bold=True, state=uiconst.UI_NORMAL)
        self.acceptIcon = uicontrols.Icon(icon='ui_38_16_193', parent=self.topCont, left=67, top=14)
        uicls.InvContViewBtns(parent=self.topCont, align=uiconst.BOTTOMLEFT, left=72, controller=self)
        self.moneyLabel = uicontrols.EveLabelMedium(parent=self.topCont, left=6, top=-2, align=uiconst.BOTTOMRIGHT)

    def SetInvContViewMode(self, value):
        """ Called by InvContViewBtns when view mode is changed """
        self.ChangeViewMode(value)

    def _GetInvController(self, attributes):
        return self.__invControllerClass__(itemID=attributes.itemID, ownerID=attributes.ownerID, tradeSession=attributes.tradeSession)

    def ShowCharInfo(self, ownerID, *args):
        sm.GetService('info').ShowInfo(const.typeCharacterAmarr, ownerID)
