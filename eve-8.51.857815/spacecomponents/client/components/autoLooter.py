#Embedded file name: spacecomponents/client/components\autoLooter.py
from carbon.common.lib.const import SEC
from carbon.common.script.util.format import FmtDist, FmtTimeInterval
from eve.common.lib.appConst import maxCargoContainerTransferDistance
from spacecomponents.client.display import EntryData, RANGE_ICON, CYCLE_TIME_ICON
from spacecomponents.common.components.component import Component

class AutoLooter(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/AutoLooter/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/AutoLooter/RangeLabel'), FmtDist(getattr(attributes, 'range', maxCargoContainerTransferDistance)), iconID=RANGE_ICON), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/AutoLooter/CycleTimeSecondsLabel'), FmtTimeInterval(long(attributes.cycleTimeSeconds * SEC), breakAt='sec'), iconID=CYCLE_TIME_ICON)]
        return attributeEntries
