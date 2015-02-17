#Embedded file name: spacecomponents/client/components\siphon.py
from dogma.attributes.format import GetFormatAndValue
from inventorycommon import types
__author__ = 'markus'
from spacecomponents.client.display import EntryData, RANGE_ICON
from spacecomponents.common.components.component import Component

class Siphon(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/Siphon/SiphoningMaterials'))]
        materialNames = []
        for materialID in attributes.materials:
            materialNames.append((types.GetName(materialID), materialID))

        for material in sorted(materialNames):
            attributeEntries.append(EntryData('LabelTextSides', material[0], '', types.GetIconID(material[1]), material[1]))

        return attributeEntries
