#Embedded file name: spacecomponents/client/components\scanblocker.py
from carbon.common.script.util.format import FmtDist
from spacecomponents.client.display import EntryData, RANGE_ICON
from spacecomponents.common.components.component import Component

class ScanBlocker(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/ScanBlocker/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/ScanBlocker/RangeLabel'), FmtDist(attributes.range), iconID=RANGE_ICON)]
        return attributeEntries
