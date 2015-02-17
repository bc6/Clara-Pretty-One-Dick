#Embedded file name: spacecomponents/client/components\activate.py
from spacecomponents.client.display import EntryData, TIMER_ICON
from spacecomponents.common.components.component import Component
from carbon.common.lib.const import SEC
from spacecomponents.client.messages import MSG_ON_ADDED_TO_SPACE
from spacecomponents.client.messages import MSG_ON_SLIM_ITEM_UPDATED
from spacecomponents.client.messages import MSG_ON_ACTIVATE_TIMER_UPDATED

class Activate(Component):

    def __init__(self, *args):
        Component.__init__(self, *args)
        self.isActive = False
        self.activeTimestamp = None
        self.SubscribeToMessage(MSG_ON_ADDED_TO_SPACE, self.OnAddedToSpace)
        self.SubscribeToMessage(MSG_ON_SLIM_ITEM_UPDATED, self.OnSlimItemUpdated)

    def OnAddedToSpace(self, slimItem):
        self.OnSlimItemUpdated(slimItem)

    def OnSlimItemUpdated(self, slimItem):
        if slimItem.component_activate is not None:
            isActive, activeTimestamp = slimItem.component_activate
            self.isActive = isActive
            self.activeTimestamp = activeTimestamp
            self.SendMessage(MSG_ON_ACTIVATE_TIMER_UPDATED, self, slimItem)

    def IsActive(self):
        return self.isActive

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/Activate/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Activate/DurationLabel'), localization.GetByLabel('UI/Inflight/SpaceComponents/Activate/DurationValue', duration=long(attributes.durationSeconds * SEC)), iconID=TIMER_ICON)]
        if instance and instance.activeTimestamp:
            attributeEntries.append(EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Activate/TimestampLabel'), localization.GetByLabel('UI/Journal/JournalWindow/Contracts/TimeRemaining', time=instance.activeTimestamp - instance.GetSimTime()), iconID=TIMER_ICON))
        return attributeEntries
