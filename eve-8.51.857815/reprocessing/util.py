#Embedded file name: reprocessing\util.py
import logging
from itertoolsext import Bundle
from inventorycommon.types import GetPortionSize, GetCategoryID
import inventorycommon.const as invconst
import dogma.const as dgmconst
from eveexceptions import UserError
from math import floor
logger = logging.getLogger(__name__)

def GetReprocessInfoForItem(reprocessingSvc, charID, item, itemsToBeReprocessed, stationsTake):
    portionSize = GetPortionSize(item.typeID)
    stacksize = item.stacksize
    portions = stacksize / portionSize
    leftOvers = stacksize % portionSize
    quantityToProcess = stacksize - leftOvers
    efficiency = _GetEfficiency(reprocessingSvc, charID, item.typeID)
    recoverables = _GetRecoverables(reprocessingSvc, item, stationsTake, portions, efficiency)
    return (item.itemID,
     item.typeID,
     int(round(quantityToProcess)),
     int(round(leftOvers)),
     recoverables)


def GetRefiningYieldPercentageForType(charID, dogmaIM, dogmaLM, skillHandler, typeID):
    if GetCategoryID(typeID) == invconst.categoryAsteroid:
        refiningYieldPercentage = dogmaLM.GetCharacterAttribute(charID, dgmconst.attributeRefiningYieldPercentage)
        skillTypeID = dogmaIM.GetTypeAttribute(typeID, dgmconst.attributeReprocessingSkillType)
    else:
        refiningYieldPercentage = 1.0
        skillTypeID = invconst.typeScrapmetalProcessing
    skillLevel = skillHandler.GetSkillLevel_Ex(charID, skillTypeID)
    percentagePerLevel = dogmaIM.GetTypeAttribute2(skillTypeID, dgmconst.attributeRefiningYieldMutator)
    refiningYieldPercentage *= (100 + skillLevel * float(percentagePerLevel)) / 100
    return refiningYieldPercentage


def _GetEfficiency(reprocessingSvc, charID, typeID):
    """
    Takes in the reprocessingSvc, int: charID & typeID.
    Gets efficiency from station and char skills and returns it.
    """
    categoryID = GetCategoryID(typeID)
    stationEfficiency = reprocessingSvc.GetStationEfficiencyForCategoryID(categoryID)
    efficiency = min(stationEfficiency * reprocessingSvc.GetCharRefiningYieldPercentageForType(charID, typeID), 1.0)
    return efficiency


def _GetRecoverables(reprocessingSvc, item, stationsTake, portions, efficiency):
    recoverables = []
    if invconst.typeCredits != item.typeID and portions:
        materials = reprocessingSvc.inventorymgr.GetMaterialComposition(item.typeID)
        if materials and len(materials):
            for material in materials:
                try:
                    quantity = material.quantity * portions
                    recoverable = int(floor(quantity * efficiency))
                    station = int(round(recoverable * stationsTake))
                    client = recoverable - station
                except OverflowError:
                    raise UserError('ReprocessingPleaseSplit')

                unrecoverable = int(round(quantity - station - client))
                recoverables.append(Bundle(typeID=material.materialTypeID, client=client, station=station, unrecoverable=unrecoverable))

    return recoverables


def CanBeReprocessed(typeID):
    if typeID not in cfg.invtypematerials:
        return False
    if not cfg.invtypematerials[typeID]:
        return False
    return True
