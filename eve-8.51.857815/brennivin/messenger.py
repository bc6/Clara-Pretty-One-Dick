#Embedded file name: brennivin\messenger.py
from collections import defaultdict
from brennivin.threadutils import Signal

class Messenger(object):
    """
    Messenger is a simple wrapper around a map of Signals to manage a collection of
    named message types for use as a message system following a publish/subscribe model
    """

    def __init__(self):
        self.signalsByMessageName = defaultdict(Signal)

    def SendMessage(self, messageName, *args, **kwargs):
        signal = self.signalsByMessageName.get(messageName)
        if signal:
            signal.emit(*args, **kwargs)

    def SubscribeToMessage(self, messageName, handler):
        signal = self.signalsByMessageName[messageName]
        signal.connect(handler)

    def UnsubscribeFromMessage(self, messageName, handler):
        signal = self.signalsByMessageName[messageName]
        signal.disconnect(handler)
