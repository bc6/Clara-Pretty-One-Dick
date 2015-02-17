#Embedded file name: spacecomponents/client/components\autoTractorBeam.py
from carbon.common.lib.const import SEC
from carbon.common.script.util.format import FmtDist, FmtTimeInterval
from dogma import const as dogmaconst
from dogma.attributes.format import GetFormattedAttributeAndValue
from spacecomponents.client.display import EntryData, DogmaEntryData, CYCLE_TIME_ICON, RANGE_ICON
from spacecomponents.common.components.component import Component

class AutoTractorBeam(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        value = godmaService.GetTypeAttribute2(typeID, dogmaconst.attributeMaxTractorVelocity)
        maxTractorVelocity = GetFormattedAttributeAndValue(dogmaconst.attributeMaxTractorVelocity, value)
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/AutoTractorBeam/InfoAttributesHeader')),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/AutoTractorBeam/MaxRangeLabel'), FmtDist(attributes.maxRange), iconID=RANGE_ICON),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/AutoTractorBeam/CycleTimeSecondsLabel'), FmtTimeInterval(attributes.cycleTimeSeconds * SEC, breakAt='sec'), iconID=CYCLE_TIME_ICON),
         DogmaEntryData('LabelTextSides', maxTractorVelocity)]
        return attributeEntries

    @staticmethod
    def GetSuppressedDogmaAttributeIDs():
        return [dogmaconst.attributeMaxTractorVelocity, dogmaconst.attributeDuration]
