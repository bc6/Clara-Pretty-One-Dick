#Embedded file name: spacecomponents/client/components\decay.py
from carbon.common.lib.const import SEC
from spacecomponents.client.display import EntryData, TIMER_ICON
from spacecomponents.client.messages import MSG_ON_ADDED_TO_SPACE
from spacecomponents.client.messages import MSG_ON_SLIM_ITEM_UPDATED
from spacecomponents.common.components.component import Component

class Decay(Component):

    def __init__(self, *args):
        Component.__init__(self, *args)
        self.SubscribeToMessage(MSG_ON_ADDED_TO_SPACE, self.OnAddedToSpace)
        self.SubscribeToMessage(MSG_ON_SLIM_ITEM_UPDATED, self.OnSlimItemUpdate)
        self.decayTimestamp = None

    def OnAddedToSpace(self, slimItem):
        self.OnSlimItemUpdate(slimItem)

    def OnSlimItemUpdate(self, slimItem):
        if slimItem.component_decay is not None:
            self.decayTimestamp = slimItem.component_decay

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/Decay/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Decay/DurationLabel'), localization.GetByLabel('UI/Inflight/SpaceComponents/Decay/DurationValue', duration=long(attributes.durationSeconds * SEC)), iconID=TIMER_ICON)]
        if instance and instance.decayTimestamp:
            attributeEntries.append(EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Decay/TimestampLabel'), localization.GetByLabel('UI/Journal/JournalWindow/Contracts/TimeRemaining', time=instance.decayTimestamp - instance.GetSimTime()), iconID=TIMER_ICON))
        return attributeEntries
