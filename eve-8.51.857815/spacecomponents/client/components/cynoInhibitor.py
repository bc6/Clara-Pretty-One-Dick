#Embedded file name: spacecomponents/client/components\cynoInhibitor.py
from carbon.common.script.util.format import FmtDist
from spacecomponents.client.display import EntryData, RANGE_ICON
from spacecomponents.common.components.component import Component

class CynoInhibitor(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/CynoInhibitor/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/CynoInhibitor/RangeLabel'), FmtDist(attributes.range), iconID=RANGE_ICON)]
        return attributeEntries
