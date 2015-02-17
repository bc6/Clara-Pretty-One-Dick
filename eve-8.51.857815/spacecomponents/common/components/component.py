#Embedded file name: spacecomponents/common/components\component.py
"""
A base space component.
"""

class Component(object):

    def __init__(self, itemID, typeID, attributes, componentRegistry):
        self.itemID = itemID
        self.typeID = typeID
        self.attributes = attributes
        self.componentRegistry = componentRegistry
        self.GetSimTime = componentRegistry.asyncFuncs.GetSimTime
        self.SleepSim = componentRegistry.asyncFuncs.SleepSim
        self.GetWallclockTime = componentRegistry.asyncFuncs.GetWallclockTime
        self.SleepWallclock = componentRegistry.asyncFuncs.SleepWallclock
        self.TimeDiffInMs = componentRegistry.asyncFuncs.TimeDiffInMs
        self.UThreadNew = componentRegistry.asyncFuncs.UThreadNew

    def SubscribeToMessage(self, messageName, messageHandler):
        """Subscribe to message sent to this item"""
        self.componentRegistry.SubscribeToItemMessage(self.itemID, messageName, messageHandler)

    def UnsubscribeFromMessage(self, messageName, messageHandler):
        """Unsubscribe from a message send from this item"""
        self.componentRegistry.UnsubscribeFromItemMessage(self.itemID, messageName, messageHandler)

    def SendMessage(self, messageName, *args, **kwargs):
        """Send message to the this item"""
        self.componentRegistry.SendMessageToItem(self.itemID, messageName, *args, **kwargs)
