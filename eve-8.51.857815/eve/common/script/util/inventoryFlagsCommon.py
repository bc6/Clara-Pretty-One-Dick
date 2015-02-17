#Embedded file name: eve/common/script/util\inventoryFlagsCommon.py
"""
Contains inventory-related constants for different inventory flags. This is
used to help centralize information on different fuel bays & cargo holds.
"""
import localization
inventoryFlagData = {const.flagCargo: {'name': 'UI/Ship/CargoHold',
                   'attribute': const.attributeCapacity,
                   'allowCategories': None,
                   'allowGroups': None,
                   'blockGroups': None,
                   'allowTypes': None,
                   'blockTypes': None},
 const.flagDroneBay: {'name': 'UI/Ship/DroneBay',
                      'attribute': const.attributeDroneCapacity,
                      'allowCategories': (const.categoryDrone,),
                      'allowGroups': None,
                      'blockGroups': None,
                      'allowTypes': None,
                      'blockTypes': None},
 const.flagShipHangar: {'name': 'UI/Ship/ShipMaintenanceBay',
                        'attribute': const.attributeShipMaintenanceBayCapacity,
                        'allowCategories': (const.categoryShip,),
                        'allowGroups': None,
                        'blockGroups': (const.groupCapsule,),
                        'allowTypes': None,
                        'blockTypes': None},
 const.flagFleetHangar: {'name': 'UI/Ship/FleetHangar',
                         'attribute': const.attributeFleetHangarCapacity,
                         'allowCategories': None,
                         'allowGroups': None,
                         'blockGroups': None,
                         'allowTypes': None,
                         'blockTypes': None},
 const.flagSpecializedFuelBay: {'name': 'UI/Ship/FuelBay',
                                'attribute': const.attributeSpecialFuelBayCapacity,
                                'allowCategories': None,
                                'blockCategories': None,
                                'allowGroups': (const.groupIceProduct,),
                                'blockGroups': None,
                                'allowTypes': None,
                                'blockTypes': None},
 const.flagSpecializedOreHold: {'name': 'UI/Ship/OreHold',
                                'attribute': const.attributeSpecialOreHoldCapacity,
                                'allowCategories': (const.categoryAsteroid,),
                                'blockCategories': None,
                                'allowGroups': (const.groupHarvestableCloud,),
                                'blockGroups': None,
                                'allowTypes': None,
                                'blockTypes': None},
 const.flagSpecializedGasHold: {'name': 'UI/Ship/GasHold',
                                'attribute': const.attributeSpecialGasHoldCapacity,
                                'allowCategories': None,
                                'blockCategories': None,
                                'allowGroups': (const.groupHarvestableCloud,),
                                'blockGroups': None,
                                'allowTypes': None,
                                'blockTypes': None},
 const.flagSpecializedMineralHold: {'name': 'UI/Ship/MineralHold',
                                    'attribute': const.attributeSpecialMineralHoldCapacity,
                                    'allowCategories': None,
                                    'blockCategories': None,
                                    'allowGroups': (const.groupMineral,),
                                    'blockGroups': None,
                                    'allowTypes': None,
                                    'blockTypes': None},
 const.flagSpecializedSalvageHold: {'name': 'UI/Ship/SalvageHold',
                                    'attribute': const.attributeSpecialSalvageHoldCapacity,
                                    'allowCategories': None,
                                    'blockCategories': None,
                                    'allowGroups': (const.groupAncientSalvage, const.groupSalvagedMaterials, const.groupRefinables),
                                    'blockGroups': None,
                                    'allowTypes': None,
                                    'blockTypes': None},
 const.flagSpecializedShipHold: {'name': 'UI/Ship/ShipHold',
                                 'attribute': const.attributeSpecialShipHoldCapacity,
                                 'allowCategories': (const.categoryShip,),
                                 'blockCategories': None,
                                 'allowGroups': None,
                                 'blockGroups': None,
                                 'allowTypes': None,
                                 'blockTypes': None},
 const.flagSpecializedSmallShipHold: {'name': 'UI/Ship/SmallShipHold',
                                      'attribute': const.attributeSpecialSmallShipHoldCapacity,
                                      'allowCategories': None,
                                      'blockCategories': None,
                                      'allowGroups': (const.groupFrigate,
                                                      const.groupAssaultShip,
                                                      const.groupDestroyer,
                                                      const.groupInterdictor,
                                                      const.groupInterceptor,
                                                      const.groupCovertOps,
                                                      const.groupElectronicAttackShips,
                                                      const.groupStealthBomber,
                                                      const.groupExpeditionFrigate,
                                                      const.groupTacticalDestroyer),
                                      'blockGroups': None,
                                      'allowTypes': None,
                                      'blockTypes': None},
 const.flagSpecializedMediumShipHold: {'name': 'UI/Ship/MediumShipHold',
                                       'attribute': const.attributeSpecialMediumShipHoldCapacity,
                                       'allowCategories': None,
                                       'blockCategories': None,
                                       'allowGroups': (const.groupCruiser,
                                                       const.groupCombatReconShip,
                                                       const.groupCommandShip,
                                                       const.groupHeavyAssaultShip,
                                                       const.groupHeavyInterdictors,
                                                       const.groupLogistics,
                                                       const.groupStrategicCruiser,
                                                       const.groupBattlecruiser,
                                                       const.groupAttackBattlecruiser,
                                                       const.groupForceReconShip),
                                       'blockGroups': None,
                                       'allowTypes': None,
                                       'blockTypes': None},
 const.flagSpecializedLargeShipHold: {'name': 'UI/Ship/LargeShipHold',
                                      'attribute': const.attributeSpecialLargeShipHoldCapacity,
                                      'allowCategories': None,
                                      'blockCategories': None,
                                      'allowGroups': (const.groupBattleship, const.groupBlackOps, const.groupMarauders),
                                      'blockGroups': None,
                                      'allowTypes': None,
                                      'blockTypes': None},
 const.flagSpecializedIndustrialShipHold: {'name': 'UI/Ship/IndustrialShipHold',
                                           'attribute': const.attributeSpecialIndustrialShipHoldCapacity,
                                           'allowCategories': None,
                                           'blockCategories': None,
                                           'allowGroups': (const.groupBlockadeRunner,
                                                           const.groupExhumer,
                                                           const.groupIndustrial,
                                                           const.groupMiningBarge,
                                                           const.groupTransportShip),
                                           'blockGroups': None,
                                           'allowTypes': None,
                                           'blockTypes': None},
 const.flagSpecializedAmmoHold: {'name': 'UI/Ship/AmmoHold',
                                 'attribute': const.attributeSpecialAmmoHoldCapacity,
                                 'allowCategories': (const.categoryCharge,),
                                 'blockCategories': None,
                                 'allowGroups': None,
                                 'blockGroups': None,
                                 'allowTypes': None,
                                 'blockTypes': None},
 const.flagSpecializedCommandCenterHold: {'name': 'UI/Ship/CommandCenterHold',
                                          'attribute': const.attributeSpecialCommandCenterHoldCapacity,
                                          'allowCategories': None,
                                          'blockCategories': None,
                                          'allowGroups': (const.groupCommandPins,),
                                          'blockGroups': None,
                                          'allowTypes': None,
                                          'blockTypes': None},
 const.flagSpecializedPlanetaryCommoditiesHold: {'name': 'UI/Ship/PlanetaryCommoditiesHold',
                                                 'attribute': const.attributeSpecialPlanetaryCommoditiesHoldCapacity,
                                                 'allowCategories': (const.categoryPlanetaryCommodities, const.categoryPlanetaryResources),
                                                 'blockCategories': None,
                                                 'allowGroups': None,
                                                 'blockGroups': None,
                                                 'allowTypes': (const.typeWater, const.typeOxygen),
                                                 'blockTypes': None},
 const.flagSpecializedMaterialBay: {'name': 'UI/Ship/MaterialBay',
                                    'attribute': const.attributeSpecialMaterialBayCapacity,
                                    'allowCategories': (const.categoryPlanetaryCommodities, const.categoryCommodity, const.categoryMaterial),
                                    'blockCategories': None,
                                    'allowGroups': None,
                                    'blockGroups': None,
                                    'allowTypes': None,
                                    'blockTypes': None},
 const.flagQuafeBay: {'name': 'UI/Ship/QuafeBay',
                      'attribute': const.attributeSpecialQuafeHoldCapacity,
                      'allowCategories': None,
                      'blockCategories': None,
                      'allowGroups': None,
                      'blockGroups': None,
                      'allowTypes': (const.typeLargeCratesOfQuafe,
                                     const.typeQuafe,
                                     const.typeQuafeUltra,
                                     const.typeQuafeUltraSpecialEdition,
                                     const.typeQuafeZero,
                                     const.typeSpikedQuafe),
                      'blockTypes': None}}

def ShouldAllowAdd(flag, categoryID, groupID, typeID):
    """
        Implements a cascading allow/block hierarchy in Jacob's Ladder format.
        
        DIAGRAM: http://trac/trac/wiki/EveSoftwareGroup/Designs/SpecializedCargoBays
    
        ARGUMENTS:
            flag        : The inventory flag for the bay receiving the item.
            categoryID  : The category ID of the item being tested for add.
            groupID     : The group ID of the item being tested for add.
            typeID      : The typeID of the item being tested for add.
    
        RETURNS:
            None if succeeded, a tuple otherwise.
    """
    if flag not in inventoryFlagData:
        return
    flagData = inventoryFlagData[flag]
    errorTuple = None
    useAllow = True
    if flagData['allowCategories'] is not None:
        if categoryID in flagData['allowCategories']:
            useAllow = False
        else:
            errorTuple = (const.UE_CATID, categoryID)
    if useAllow:
        if flagData['allowGroups'] is not None:
            if groupID in flagData['allowGroups']:
                errorTuple = None
                useAllow = False
            else:
                errorTuple = (const.UE_GROUPID, groupID)
                useAllow = True
    elif flagData['blockGroups'] is not None:
        if groupID in flagData['blockGroups']:
            errorTuple = (const.UE_GROUPID, groupID)
            useAllow = True
        else:
            errorTuple = None
            useAllow = False
    if useAllow:
        if flagData['allowTypes'] is not None:
            if typeID in flagData['allowTypes']:
                errorTuple = None
            else:
                errorTuple = (const.UE_TYPEID, typeID)
    elif flagData['blockTypes'] is not None:
        if typeID in flagData['blockTypes']:
            errorTuple = (const.UE_TYPEID, typeID)
        else:
            errorTuple = None
    return errorTuple


autoConsumeTypes = {}
autoConsumeGroups = {const.groupIceProduct: (const.flagSpecializedFuelBay,)}
autoConsumeCategories = {}

def GetBaysToCheck(typeID, priorityBays = []):
    """
        Retrieves a list of inventory flags indicating which bays should be checked.
        Accepts a list of 'override' bays to check first in an optional argument.
        Always appends const.flagCargo if it's not already present in the list.
        
        ARGUMENTS
        typeID:         The inventory type ID of the item type being consumed. 
                        Cfg will be used to check group & category IDs.
        priorityBays:   A list of inventory flags to check first. Defaults to an empty list.
                        Also resets to an empty list if set to None.
        
        RETURNS
            A list of inventory flags to check for items.
    """
    baysToCheck = priorityBays
    if baysToCheck is None:
        baysToCheck = []
    if typeID in autoConsumeTypes:
        baysToCheck.extend(autoConsumeTypes[typeID])
    else:
        invType = cfg.invtypes.Get(typeID)
        if invType.groupID in autoConsumeGroups:
            baysToCheck.extend(autoConsumeGroups[invType.groupID])
        elif invType.categoryID in autoConsumeCategories:
            baysToCheck.extend(autoConsumeCategories[invType.categoryID])
    if const.flagCargo not in baysToCheck:
        baysToCheck.append(const.flagCargo)
    return baysToCheck


def GetNameForFlag(flagID):
    return localization.GetByLabel(inventoryFlagData[flagID]['name'])


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('inventoryFlagsCommon', locals())
