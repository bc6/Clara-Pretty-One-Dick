#Embedded file name: eve/client/script/ui/shared/radialMenu\inventoryRadialMenuFunctions.py
"""
    This file containes the radial menu options for inventory items in hangars.
    The options are hand picked for categories and only common and well picked options should be in the RM
"""
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SecondLevelRadialMenuAction, SimpleRadialMenuAction
from eve.client.script.ui.services.menuSvcExtras.menuConsts import MOUSEBUTTONS
import carbonui.const as uiconst
from eve.client.script.ui.shared.radialMenu.spaceRadialMenuFunctions import PrepareRadialMenuOptions
placeholderIconPath = 'res:/UI/Texture/Icons/9_64_13.png'
iconDict = {'UI/Commands/ShowInfo': 'res:/UI/Texture/Icons/44_32_24.png',
 'UI/Inventory/ItemActions/MakeShipActive': 'res:/UI/Texture/Icons/44_32_40.png',
 'UI/Inventory/ItemActions/Reprocess': 'res:/UI/Texture/classes/RadialMenuActions/reprocess.png',
 'UI/Inventory/ItemActions/Repackage': 'res:/UI/Texture/classes/RadialMenuActions/repackage.png',
 'UI/Commands/OpenFleetHangar': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inventory/ItemActions/TrashIt': 'res:/UI/Texture/classes/RadialMenuActions/trashIt.png',
 'UI/Inventory/ItemActions/PlugInImplant': 'res:/UI/Texture/classes/RadialMenuActions/plugInImplant.png',
 'UI/Inventory/ItemActions/CreateContract': 'res:/ui/Texture/WindowIcons/contracts.png',
 'UI/Inventory/ItemActions/SellThisItem': 'res:/UI/Texture/classes/RadialMenuActions/sellItem.png',
 'UI/Inventory/ItemActions/FitToActiveShip': 'res:/UI/Texture/classes/RadialMenuActions/fitToShip.png',
 'UI/Commands/Repair': 'res:/UI/Texture/classes/RadialMenuActions/repair.png',
 'UI/Inventory/ItemActions/GetRepairQuote': 'res:/UI/Texture/classes/RadialMenuActions/repair.png',
 'UI/Inventory/ItemActions/BuyThisType': 'res:/UI/Texture/classes/RadialMenuActions/buyThisType.png',
 'UI/Inventory/ItemActions/ViewTypesMarketDetails': 'res:/UI/Texture/classes/RadialMenuActions/viewMarketDetails.png'}
baseActionMapping = {1: SimpleRadialMenuAction(),
 2: SimpleRadialMenuAction(),
 3: SimpleRadialMenuAction(),
 4: SimpleRadialMenuAction(),
 5: SimpleRadialMenuAction(),
 6: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='market', texturePath='res:/UI/Texture/classes/RadialMenuActions/market.png'),
 7: SimpleRadialMenuAction(option1='UI/Commands/ShowInfo'),
 8: SimpleRadialMenuAction()}
actionsMapping = {}

def AddReworkToMapping(category, mapping = None):
    if mapping is None:
        mapping = baseActionMapping.copy()
    mapping.update({3: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='rework')})
    actionsMapping[category] = mapping
    return mapping


shipMapping = baseActionMapping.copy()
shipMapping.update({1: SimpleRadialMenuAction(option1='UI/Inventory/ItemActions/MakeShipActive', option2='UI/Inventory/ItemActions/AssembleShip', option3='UI/Inventory/ItemActions/LeaveShip'),
 3: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='rework')})
actionsMapping[const.categoryShip] = shipMapping
moduleMapping = baseActionMapping.copy()
moduleMapping.update({1: SimpleRadialMenuAction(option1='UI/Inventory/ItemActions/FitToActiveShip'),
 3: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='rework')})
actionsMapping[const.categoryModule] = moduleMapping
asteroidMapping = baseActionMapping.copy()
asteroidMapping.update({1: SimpleRadialMenuAction(option1='UI/Inventory/ItemActions/Refine')})
actionsMapping[const.categoryAsteroid] = asteroidMapping
blueprintMapping = baseActionMapping.copy()
blueprintMapping.update({1: SimpleRadialMenuAction(option1='UI/ScienceAndIndustry/ScienceAndIndustryWindow/Filters/Manufacturing')})
actionsMapping[const.categoryBlueprint] = blueprintMapping
skillMapping = baseActionMapping.copy()
skillMapping.update({1: SimpleRadialMenuAction(option1='UI/SkillQueue/InjectSkill'),
 5: SimpleRadialMenuAction(option1='UI/SkillQueue/AddSkillMenu/TrainNowToLevel1')})
actionsMapping[const.categorySkill] = skillMapping
implantMapping = baseActionMapping.copy()
implantMapping.update({1: SimpleRadialMenuAction(option1='UI/Inventory/ItemActions/PlugInImplant'),
 3: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='rework')})
actionsMapping[const.categoryImplant] = implantMapping
droneMapping = baseActionMapping.copy()
droneMapping.update({1: SimpleRadialMenuAction(option1='UI/Drones/LaunchDrones'),
 3: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='rework')})
actionsMapping[const.categoryDrone] = droneMapping
mobileMapping = baseActionMapping.copy()
mobileMapping.update({1: SimpleRadialMenuAction(option1='UI/Inventory/ItemActions/LaunchForSelf'),
 3: SecondLevelRadialMenuAction(hasExtraOptions=True, levelType='rework')})
actionsMapping[const.categoryDeployable] = mobileMapping
AddReworkToMapping(const.categoryCelestial)
AddReworkToMapping(const.categoryCharge)
AddReworkToMapping(const.categoryCharge)
AddReworkToMapping(const.categoryStructure)
AddReworkToMapping(const.categorySubSystem)
secondaryOptionsMapping = {'rework': [SimpleRadialMenuAction('UI/Inventory/ItemActions/GetRepairQuote'), SimpleRadialMenuAction('UI/Inventory/ItemActions/Repackage'), SimpleRadialMenuAction('UI/Inventory/ItemActions/Reprocess')],
 'market': [SimpleRadialMenuAction('UI/Inventory/ItemActions/ViewTypesMarketDetails'), SimpleRadialMenuAction('UI/Inventory/ItemActions/SellThisItem'), SimpleRadialMenuAction('UI/Inventory/ItemActions/BuyThisType')]}

def GetObjectsActions(categoryID, groupID, typeID = None, itemID = None, *args):
    generalActions = GetGeneralActions(categoryID, groupID, typeID=typeID, itemID=itemID)
    myActions = generalActions[:]
    return myActions


def GetObjectsSecondaryActions(categoryID, groupID, typeID = None, itemID = None, levelType = ''):
    """
        this function returns all the secondary options we want for this level type.
    """
    myActions = secondaryOptionsMapping.get(levelType, [])
    if myActions:
        myActions = [SecondLevelRadialMenuAction(hasExtraOptions=False)] + myActions
    return myActions


def GetGeneralActions(categoryID, groupID, typeID, itemID):
    """
        gets the actions in the first layer
    """
    generalActions = actionsMapping.get(categoryID, baseActionMapping).values()
    for eachAction in generalActions:
        if isinstance(eachAction, SecondLevelRadialMenuAction):
            secondaryActions = GetObjectsSecondaryActions(categoryID, groupID, typeID, itemID, levelType=eachAction.levelType)
            if secondaryActions:
                eachAction.hasExtraOptions = True

    return generalActions


def FindRadialMenuOptions(itemID = None, typeID = None, primaryActions = True, manyItemsData = None, rec = None, levelType = None):
    filterList = []
    allMenuOptions = sm.GetService('menu').InvItemMenu(rec)
    if typeID is not None:
        typeInfo = cfg.invtypes.Get(typeID)
        categoryID = typeInfo.categoryID
        groupID = typeInfo.groupID
    else:
        categoryID = None
        groupID = None
    if primaryActions:
        allWantedMenuOptions = GetObjectsActions(categoryID, groupID, typeID, itemID)
    else:
        allWantedMenuOptions = GetObjectsSecondaryActions(categoryID, groupID, typeID, itemID, levelType=levelType)
    return PrepareRadialMenuOptions(allMenuOptions, allWantedMenuOptions, filterList)


def GetIconPath(labelPath):
    return iconDict.get(labelPath, None)


def IsRadialMenuButtonActive():
    actionmenuBtn = settings.user.ui.Get('actionmenuBtn', uiconst.MOUSELEFT)
    if not isinstance(actionmenuBtn, int):
        actionmenuBtn = uiconst.MOUSELEFT
    actionmenuBtnState = uicore.uilib.GetMouseButtonState(actionmenuBtn)
    if not actionmenuBtnState:
        return False
    for eachBtn in MOUSEBUTTONS:
        if eachBtn == actionmenuBtn:
            continue
        btnDown = uicore.uilib.GetMouseButtonState(eachBtn)
        if btnDown:
            return False

    return True
