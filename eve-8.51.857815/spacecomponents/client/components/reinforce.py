#Embedded file name: spacecomponents/client/components\reinforce.py
from carbon.common.lib.const import SEC
from carbon.common.script.util.format import FmtTimeInterval, FmtDate, FmtYesNo
from spacecomponents.client.display import EntryData, TIMER_ICON
from spacecomponents.common.components.component import Component
from spacecomponents.client.messages import MSG_ON_ADDED_TO_SPACE
from spacecomponents.client.messages import MSG_ON_SLIM_ITEM_UPDATED
from spacecomponents.client.messages import MSG_ON_REINFORCE_TIMER_UPDATED

class Reinforce(Component):

    def __init__(self, *args):
        Component.__init__(self, *args)
        self.isReinforced = False
        self.reinforceTimestamp = None
        self.SubscribeToMessage(MSG_ON_ADDED_TO_SPACE, self.OnSlimItemUpdated)
        self.SubscribeToMessage(MSG_ON_SLIM_ITEM_UPDATED, self.OnSlimItemUpdated)

    def OnSlimItemUpdated(self, slimItem):
        if slimItem.component_reinforce is not None:
            isReinforced, reinforceTimestamp = slimItem.component_reinforce
            self.isReinforced = isReinforced
            self.reinforceTimestamp = reinforceTimestamp
            self.SendMessage(MSG_ON_REINFORCE_TIMER_UPDATED, self, slimItem)

    def IsReinforced(self):
        return self.isReinforced

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/Reinforce/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Reinforce/DurationLabel'), FmtTimeInterval(long(attributes.durationSeconds * SEC), breakAt='sec'), iconID=TIMER_ICON)]
        if instance:
            attributeEntries.append(EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Reinforce/ReinforcedLabel'), FmtYesNo(instance.isReinforced)))
            if instance.isReinforced and instance.reinforceTimestamp > instance.GetWallclockTime():
                attributeEntries.append(EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/Reinforce/ExitReinforcementLabel'), FmtDate(instance.reinforceTimestamp, 'ss'), iconID=TIMER_ICON))
        return attributeEntries
