#Embedded file name: vgsclient\account.py
import logging
from threadutils import Signal
log = logging.getLogger(__name__)

class Account:
    """
    Tracks the Aurum balance on the user's account.
    Provides a hook to register callbacks that trigger when the balance changes.
    """

    def __init__(self, vgsCrestConnection):
        self.vgsCrestConnection = vgsCrestConnection
        self.aurumBalance = None
        self.transactionHref = None
        self.accountAurumBalanceChanged = Signal()
        self.redeemingQueueUpdated = Signal()

    def ClearCache(self):
        self.aurumBalance = None
        self.vgsCrestConnection.ClearCache()

    def SubscribeToAurumBalanceChanged(self, callBackFunction):
        """
        Calls the callBackFunction every time the aurum balance is changed.
        The callBackFunction needs to accept a single float representing the balance.
        """
        self.accountAurumBalanceChanged.connect(callBackFunction)

    def SubscribeToRedeemingQueueUpdatedEvent(self, callBackFunction):
        """
        Calls the callBackFunction every time the redeeming queue is updated.
        The callBackFunction should not accept any parameters.
        """
        self.redeemingQueueUpdated.connect(callBackFunction)

    def UnsubscribeFromAurumBalanceChanged(self, callBackFunction):
        """
        Unsubscribes the callback from the AurumBalanceChanged event
        """
        self.accountAurumBalanceChanged.disconnect(callBackFunction)

    def UnsubscribeFromRedeemingQueueUpdatedEvent(self, callBackFunction):
        """
        Unsubscribes the callback from the RedeemingQueueUpdatedEvent event
        """
        self.redeemingQueueUpdated.disconnect(callBackFunction)

    def OnAurumChangeFromVgs(self, newBalance):
        """
        Update the saved balance and signal any registered listeners.
        """
        log.debug('OnAurumChangeFromVgs %s' % newBalance)
        self.aurumBalance = newBalance
        self.accountAurumBalanceChanged.emit(self.aurumBalance)

    def OnRedeemingQueueUpdated(self):
        self.redeemingQueueUpdated.emit()

    def GetAurumBalance(self):
        """ Returns the current Aurum balance. May block whilst communicating with server. """
        if self.aurumBalance is None:
            self._GetAurumAccount()
        return self.aurumBalance

    def _GetAurumAccount(self):
        account = self.vgsCrestConnection.GetAurAccount()
        self.aurumBalance = account['balance']
        self.transactionHref = account['transactions']['href']

    def GetTransactionHref(self):
        """ Returns the current transaction href of the account. May block whilst communicating with server. """
        if self.transactionHref is None:
            self._GetAurumAccount()
        return self.transactionHref
