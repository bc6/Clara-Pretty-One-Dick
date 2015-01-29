#Embedded file name: spacecomponents/common\componentmessenger.py
"""
Component messenger manages publish/subscribe messaging for components
"""
from collections import defaultdict
import logging
from brennivin.threadutils import Signal
log = logging.getLogger(__name__)

class ComponentMessenger(object):

    def __init__(self):
        self.subscriptions = defaultdict(lambda : defaultdict(Signal))

    def SubscribeToItemMessage(self, itemID, messageName, messageHandler):
        self.subscriptions[itemID][messageName].connect(messageHandler)

    def SendMessageToItem(self, itemID, messageName, *args, **kwargs):
        log.debug("Sending '%s' message to %s with %s and %s", messageName, itemID, args, kwargs)
        subscribedMessages = self.subscriptions.get(itemID)
        if subscribedMessages:
            signaler = subscribedMessages.get(messageName)
            if signaler:
                signaler.emit(*args, **kwargs)

    def SendMessageToAllItems(self, messageName, *args, **kwargs):
        log.debug("Sending '%s' message to all items with %s and %s", messageName, args, kwargs)
        for itemID, subscribedMessages in self.subscriptions.iteritems():
            signaler = subscribedMessages.get(messageName)
            if signaler:
                signaler.emit(*args, **kwargs)

    def DeleteSubscriptionsForItem(self, itemID):
        try:
            del self.subscriptions[itemID]
        except KeyError:
            pass

    def UnsubscribeFromItemMessage(self, itemID, messageName, messageHandler):
        try:
            self.subscriptions[itemID][messageName].disconnect(messageHandler)
        except KeyError:
            pass
