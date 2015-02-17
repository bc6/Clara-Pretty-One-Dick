#Embedded file name: spacecomponents/client/components\cargobay.py
"""
A space object that contains a personal cargo bay inventory
"""
from inventorycommon import types
from localization import GetByLabel
from carbon.common.script.util.format import FmtDist, FmtYesNo
from dogma.attributes.format import GetFormattedAttributeAndValue
from dogma.const import attributeCapacity
from spacecomponents.client.display import EntryData, DogmaEntryData, RANGE_ICON
from spacecomponents.common.components.component import Component
from carbonui.control.menuLabel import MenuLabel
from spacecomponents.common.componentConst import CARGO_BAY

class CargoBay(Component):

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        cargoCapacity = GetFormattedAttributeAndValue(attributeCapacity, types.GetCapacity(typeID))
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/CargoBay/InfoAttributesHeader')),
         DogmaEntryData('LabelTextSides', cargoCapacity),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/CargoBay/AccessRangeLabel'), FmtDist(attributes.accessRange), iconID=RANGE_ICON),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/CargoBay/AllowUserAdd'), FmtYesNo(attributes.allowUserAdd), iconID=0),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/CargoBay/AllowFreeForAll'), FmtYesNo(attributes.allowFreeForAll), iconID=0)]
        return attributeEntries

    @staticmethod
    def GetSuppressedDogmaAttributeIDs():
        return [attributeCapacity]


def OpenCargoWindow(cargoBayItemID, typeID, menuSvc, spaceComponentStaticData):
    accessRange = spaceComponentStaticData.GetAttributes(typeID, CARGO_BAY).accessRange
    menuSvc.GetCloseAndTryCommand(cargoBayItemID, menuSvc.OpenSpaceComponentInventory, (cargoBayItemID,), interactionRange=accessRange)


def GetMenu(cargoBayItemID, typeID, menuSvc, spaceComponentStaticData):
    return [[MenuLabel('UI/Commands/OpenCargo'), OpenCargoWindow, [cargoBayItemID,
       typeID,
       menuSvc,
       spaceComponentStaticData]]]


def IsAccessibleByCharacter(cargoBayItem, charID, spaceComponentStaticData):
    if cargoBayItem.ownerID == charID:
        return True
    if spaceComponentStaticData.GetAttributes(cargoBayItem.typeID, CARGO_BAY).allowFreeForAll:
        return True
    return False
