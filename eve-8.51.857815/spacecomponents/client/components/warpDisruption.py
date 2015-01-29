#Embedded file name: spacecomponents/client/components\warpDisruption.py
from spacecomponents.common.components.component import Component
from carbon.common.script.util.format import FmtDist
from spacecomponents.client.display import EntryData, RANGE_ICON

class WarpDisruption(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/WarpDisruption/InfoAttributesHeader')), EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/WarpDisruption/WarpDisruptionRangeLabel'), FmtDist(attributes.warpDisruptionRange), iconID=RANGE_ICON)]
        return attributeEntries
