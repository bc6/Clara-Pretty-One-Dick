#Embedded file name: eve/client/script/ui/shared/radialMenu\spaceRadialMenuFunctions.py
import types
from carbonui.control.menuLabel import MenuLabel
from eve.client.script.ui.util.uix import GetBallparkRecord
from eve.common.lib.infoEventConst import infoEventRadialMenuAction
from eve.common.script.sys.eveCfg import IsCharacter, GetActiveShip
from eveexceptions import UserError
import inventorycommon.const as invConst
import uthread
import carbonui.const as uiconst
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import KeepAtRange as movementFunctions__KeepAtRange
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import Orbit as movementFunctions__Orbit
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import GetWarpToRanges as movementFunctions__GetWarpToRanges
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import WarpToBookmark as movementFunctions__WarpToBookmark
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import WarpToItem as movementFunctions__WarpToItem
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import RadialMenuOptionsInfo
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import RangeRadialMenuAction
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SecondLevelRadialMenuAction
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SimpleRadialMenuAction
from eve.client.script.ui.services.menuSvcExtras.menuConsts import MOUSEBUTTONS
from spacecomponents.common.componentConst import FITTING_CLASS, SCOOP_CLASS, CARGO_BAY
from spacecomponents.common.helper import HasBountyEscrowComponent, HasMicroJumpDriverComponent
from utillib import KeyVal
primaryCategoryActions = {invConst.categoryDrone: [SimpleRadialMenuAction(option1='UI/Drones/EngageTarget', option2='UI/Drones/LaunchDrones')],
 invConst.categoryShip: [SimpleRadialMenuAction(option1='UI/Inflight/BoardShip')],
 invConst.categoryStation: [SimpleRadialMenuAction(option1='UI/Inflight/DockInStation', option2='UI/Inflight/SetDestination')],
 invConst.categoryAsteroid: [SimpleRadialMenuAction(option1='UI/Inflight/SetDestination')]}
primaryGroupActions = {invConst.groupAgentsinSpace: [SimpleRadialMenuAction(option1='UI/Chat/StartConversation')],
 invConst.groupAuditLogSecureContainer: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupBillboard: [SimpleRadialMenuAction(option1='UI/Commands/ReadNews')],
 invConst.groupBiomass: [SimpleRadialMenuAction(option1='UI/Inflight/ScoopToCargoHold')],
 invConst.groupCargoContainer: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupSecureCargoContainer: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupMissionContainer: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupMiningDrone: [SimpleRadialMenuAction(option1='UI/Drones/MineRepeatedly', option2='UI/Drones/LaunchDrones')],
 invConst.groupPlanet: [SimpleRadialMenuAction(option1='UI/PI/Common/ViewInPlanetMode', option2='UI/Inflight/SetDestination')],
 invConst.groupSalvageDrone: [SimpleRadialMenuAction(option1='UI/Drones/Salvage', option2='UI/Drones/LaunchDrones')],
 invConst.groupStargate: [SimpleRadialMenuAction(option1='UI/Inflight/Jump', option2='UI/Inflight/SetDestination')],
 invConst.groupWormhole: [SimpleRadialMenuAction(option1='UI/Inflight/EnterWormhole')],
 invConst.groupWreck: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupWarpGate: [SimpleRadialMenuAction(option1='UI/Inflight/ActivateGate')],
 invConst.groupSpawnContainer: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupSpewContainer: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')],
 invConst.groupJumpPortalArray: [SimpleRadialMenuAction(option1='UI/Fleet/JumpThroughToSystem')],
 invConst.groupTitan: [SimpleRadialMenuAction(option1='UI/Inflight/BoardShip', option2='UI/Fleet/JumpThroughToSystem')],
 invConst.groupBlackOps: [SimpleRadialMenuAction(option1='UI/Inflight/BoardShip', option2='UI/Fleet/JumpThroughToSystem')],
 invConst.groupOrbitalInfrastructure: [SimpleRadialMenuAction(option1='UI/PI/Common/AccessCustomOffice')],
 invConst.groupSolarSystem: [SimpleRadialMenuAction(option1='UI/Inflight/SetDestination')],
 invConst.groupMoon: [SimpleRadialMenuAction(option1='UI/Inflight/SetDestination')],
 invConst.groupSun: [SimpleRadialMenuAction(option1='UI/Inflight/SetDestination')],
 invConst.groupIndustrialCommandShip: [SimpleRadialMenuAction(option1='UI/Inflight/BoardShip', option2='UI/Commands/OpenFleetHangar')],
 invConst.groupAssemblyArray: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSStorage')],
 invConst.groupControlTower: [SimpleRadialMenuAction(option1='UI/Inflight/POS/ManageControlTower')],
 invConst.groupCorporateHangarArray: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSStorage')],
 invConst.groupMobileLaboratory: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSStorage')],
 invConst.groupMobileLaserSentry: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSCrystalStorage')],
 invConst.groupMobileMissileSentry: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSAmmo')],
 invConst.groupMobileHybridSentry: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSAmmo')],
 invConst.groupMobileProjectileSentry: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSAmmo')],
 invConst.groupMobileReactor: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSStorage')],
 invConst.groupPersonalHangar: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSStorage')],
 invConst.groupReprocessingArray: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSRefinery')],
 invConst.groupCompressionArray: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSCompression')],
 invConst.groupShipMaintenanceArray: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSVessels')],
 invConst.groupSilo: [SimpleRadialMenuAction(option1='UI/Inflight/POS/AccessPOSStorage')],
 invConst.groupInfrastructureHub: [SimpleRadialMenuAction(option1='UI/Menusvc/OpenHubManager')],
 invConst.groupDeadspaceOverseersBelongings: [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')]}
bookMarkOption = SimpleRadialMenuAction(option1='UI/Inflight/BookmarkLocation')
lookAtOption = SimpleRadialMenuAction(option1='UI/Inflight/LookAtObject', option2='UI/Inflight/ResetCamera')
bookMarkAndLookatOptions = [lookAtOption, bookMarkOption]
secondaryCategoryActions = {invConst.categoryAsteroid: bookMarkAndLookatOptions,
 invConst.categoryEntity: [lookAtOption],
 invConst.categoryShip: [lookAtOption],
 invConst.categoryStation: bookMarkAndLookatOptions,
 invConst.categoryStructure: bookMarkAndLookatOptions,
 invConst.categorySovereigntyStructure: bookMarkAndLookatOptions,
 invConst.categoryCelestial: bookMarkAndLookatOptions,
 invConst.categoryOrbital: bookMarkAndLookatOptions,
 invConst.categoryDeployable: bookMarkAndLookatOptions,
 invConst.categoryDrone: [lookAtOption] + [SimpleRadialMenuAction(option1='UI/Drones/ReturnDroneAndOrbit'),
                          SimpleRadialMenuAction(option1='UI/Inflight/ScoopToCargoHold'),
                          SimpleRadialMenuAction(option1='UI/Drones/ReturnDroneToBay'),
                          SimpleRadialMenuAction(),
                          SimpleRadialMenuAction(option1='UI/Drones/ScoopDroneToBay')]}
secondaryGroupActions = {invConst.groupAuditLogSecureContainer: [SimpleRadialMenuAction(option1='UI/Inflight/ScoopToCargoHold')],
 invConst.groupBillboard: [bookMarkOption]}
placeholderIconPath = 'res:/UI/Texture/Icons/9_64_13.png'
iconDict = {'UI/Commands/ShowInfo': 'res:/UI/Texture/Icons/44_32_24.png',
 'UI/Inflight/ApproachObject': 'res:/UI/Texture/Icons/44_32_23.png',
 'UI/Inflight/ApproachLocationActionGroup': 'res:/UI/Texture/Icons/44_32_23.png',
 'UI/Inflight/AlignTo': 'res:/UI/Texture/Icons/44_32_59.png',
 'UI/Inflight/OrbitObject': 'res:/UI/Texture/Icons/44_32_21.png',
 'UI/Inflight/Submenus/KeepAtRange': 'res:/UI/Texture/Icons/44_32_22.png',
 'UI/Inflight/LockTarget': 'res:/UI/Texture/Icons/44_32_17.png',
 'UI/Inflight/UnlockTarget': 'res:/UI/Texture/classes/RadialMenuActions/untarget.png',
 'UI/Inflight/LookAtObject': 'res:/UI/Texture/Icons/44_32_20.png',
 'UI/Inflight/ResetCamera': 'res:/UI/Texture/classes/RadialMenuActions/resetCamera.png',
 'UI/Inflight/BoardShip': 'res:/UI/Texture/Icons/44_32_40.png',
 'UI/Inflight/DockInStation': 'res:/UI/Texture/Icons/44_32_9.png',
 'UI/Inflight/Jump': 'res:/UI/Texture/Icons/44_32_39.png',
 'UI/Fleet/JumpThroughToSystem': 'res:/UI/Texture/Icons/44_32_39.png',
 'UI/Commands/OpenCargo': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Commands/OpenCargoHold': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Commands/OpenFleetHangar': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/PI/Common/AccessCustomOffice': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/ScoopToCargoHold': 'res:/UI/Texture/Icons/scoopcargo.png',
 'UI/Drones/ScoopDroneToBay': 'res:/UI/Texture/classes/RadialMenuActions/scoopDrone.png',
 'UI/Drones/LaunchDrones': 'res:/UI/Texture/Icons/44_32_2.png',
 'UI/Drones/ReturnDroneToBay': 'res:/UI/Texture/Icons/44_32_1.png',
 'UI/Chat/StartConversation': 'res:/UI/Texture/Icons/44_32_33.png',
 'UI/Inflight/EnterWormhole': 'res:/UI/Texture/Icons/44_32_39.png',
 'UI/Drones/EngageTarget': 'res:/UI/Texture/Icons/44_32_4.png',
 'UI/Drones/MineRepeatedly': 'res:/UI/Texture/Icons/44_32_5.png',
 'UI/Drones/Salvage': 'res:/UI/Texture/Icons/44_32_4.png',
 'UI/Drones/ReturnDroneAndOrbit': 'res:/UI/Texture/Icons/44_32_3.png',
 'UI/Commands/ReadNews': 'res:/UI/Texture/Icons/44_32_47.png',
 'UI/Inflight/Submenus/WarpToWithin': 'res:/UI/Texture/Icons/44_32_18.png',
 'UI/Fleet/WarpToMemberSubmenuOption': 'res:/UI/Texture/Icons/44_32_18.png',
 'UI/Inflight/WarpToBookmark': 'res:/UI/Texture/Icons/44_32_18.png',
 'UI/Inflight/BookmarkLocation': 'res:/UI/Texture/Icons/bookmark.png',
 'UI/Inflight/EditBookmark': 'res:/UI/Texture/classes/RadialMenuActions/edit_bookmark.png',
 'UI/PI/Common/ViewInPlanetMode': 'res:/UI/Texture/Icons/77_32_34.png',
 'UI/Inflight/ActivateGate': 'res:/UI/Texture/Icons/44_32_39.png',
 'UI/Common/Open': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/StopMyShip': 'res:/UI/Texture/Icons/44_32_38.png',
 'UI/Inflight/StopMyCapsule': 'res:/UI/Texture/Icons/44_32_38.png',
 'UI/Inflight/SetDestination': 'res:/UI/Texture/classes/RadialMenuActions/setDestination.png',
 'UI/Fitting/UseFittingService': 'res:/UI/Texture/classes/RadialMenuActions/useFittingService.png',
 'UI/Inflight/SetDefaultWarpWithinDistanceShort': 'res:/UI/Texture/classes/RadialMenuActions/setWarpDefault.png',
 'UI/Inflight/SetDefaultKeepAtRangeDistanceShort': 'res:/UI/Texture/classes/RadialMenuActions/setKeepRangeDefault.png',
 'UI/Inflight/SetDefaultOrbitDistanceShort': 'res:/UI/Texture/classes/RadialMenuActions/setOrbitDefault.png',
 'UI/Inflight/POS/ManageControlTower': 'res:/UI/Texture/classes/RadialMenuActions/manageStarbase.png',
 'UI/Menusvc/OpenHubManager': 'res:/UI/Texture/classes/RadialMenuActions/manageStarbase.png',
 'UI/Inflight/POS/AccessPOSStorage': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/POS/AccessPOSCrystalStorage': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/POS/AccessPOSAmmo': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/POS/AccessPOSRefinery': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/POS/AccessPOSCompression': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/POS/AccessPOSVessels': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Commands/AccessBountyEscrow': 'res:/UI/Texture/Icons/44_32_35.png',
 'UI/Inflight/SpaceComponents/MicroJumpDriver/ActivateMicroJumpDrive': 'res:/UI/Texture/Icons/44_32_39.png',
 'UI/Inflight/Scanner/IngoreResult': 'res:/UI/Texture/classes/RadialMenuActions/ignore_results.png',
 'UI/Inflight/Scanner/IgnoreOtherResults': 'res:/UI/Texture/classes/RadialMenuActions/ignore_others_results.png',
 'UI/Inflight/Scanner/ProbeScanner': 'res:/UI/Texture/Icons/probe_scan.png'}

def GetSpaceComponentPrimaryActionsForTypeID(typeID):
    componentNames = cfg.spaceComponentStaticData.GetComponentNamesForType(typeID)
    if CARGO_BAY in componentNames:
        return [SimpleRadialMenuAction(option1='UI/Commands/OpenCargo')]
    if HasBountyEscrowComponent(typeID):
        return [SimpleRadialMenuAction(option1='UI/Commands/AccessBountyEscrow')]
    if HasMicroJumpDriverComponent(typeID):
        return [SimpleRadialMenuAction(option1='UI/Inflight/SpaceComponents/MicroJumpDriver/ActivateMicroJumpDrive')]


def GetSpaceComponentSecondaryActions(typeID):
    componentNames = cfg.spaceComponentStaticData.GetComponentNamesForType(typeID)
    actions = []
    if SCOOP_CLASS in componentNames:
        actions.append(SimpleRadialMenuAction(option1='UI/Inflight/ScoopToCargoHold'))
    if FITTING_CLASS in componentNames:
        actions.append(SimpleRadialMenuAction(option1='UI/Fitting/UseFittingService'))
    return actions


def GetObjectsActions(categoryID, groupID, typeID = None, itemID = None, bookmarkInfo = None, siteData = None, *args):
    secondaryActions = GetObjectsSecondaryActions(categoryID, groupID, typeID=typeID, itemID=itemID, bookmarkInfo=bookmarkInfo, siteData=siteData)
    generalActions = GetGeneralActions(hasExtraOptions=bool(secondaryActions), itemID=itemID, bookmarkInfo=bookmarkInfo, siteData=siteData)
    myActions = generalActions[:]
    if itemID == GetActiveShip():
        return myActions
    primaryComponentActions = GetSpaceComponentPrimaryActionsForTypeID(typeID)
    groupActions = primaryGroupActions.get(groupID, None)
    categoryActions = primaryCategoryActions.get(categoryID, None)
    siteActions = siteData.GetSiteActions() if siteData else None
    if primaryComponentActions:
        primaryActions = primaryComponentActions
    elif siteActions:
        primaryActions = siteActions
    elif groupActions:
        primaryActions = groupActions
    elif categoryActions:
        primaryActions = categoryActions
    else:
        primaryActions = [SimpleRadialMenuAction()]
    return primaryActions + myActions


def GetObjectsSecondaryActions(categoryID, groupID, typeID = None, itemID = None, bookmarkInfo = None, siteData = None):
    """
        this function returns all the secondary options we want for this category/group.
        It's different from GetObjectsActions in the sense that it will collect all the options,
        while GetObjectsActions only retuns the action from a group OR category
    """
    myActions = []
    categoryActions = secondaryCategoryActions.get(categoryID, None)
    if categoryActions:
        myActions += categoryActions
    groupActions = secondaryGroupActions.get(groupID, None)
    if groupActions:
        myActions += groupActions
    if itemID == GetActiveShip() and session.solarsystemid:
        myActions += GetMyShipSpecialCaseSecondLevel(typeID=typeID, itemID=itemID)
    secondaryComponentActions = GetSpaceComponentSecondaryActions(typeID)
    if secondaryComponentActions:
        myActions += secondaryComponentActions
    if siteData:
        myActions.extend(siteData.GetSecondaryActions())
    if myActions:
        myActions = [SecondLevelRadialMenuAction(hasExtraOptions=False)] + myActions
    return myActions


def GetGeneralActions(hasExtraOptions = True, itemID = None, bookmarkInfo = None, siteData = None):
    """
        defaults, and range could have changed since this was generated, so we always make this list again
        This returns actions for slots 2-8 (the first one is base don group/category/type)
    """
    if itemID == GetActiveShip():
        generalActions = [SimpleRadialMenuAction(option1='UI/Inflight/StopMyShip', option2='UI/Inflight/StopMyCapsule'),
         GetOrbitOption(itemID, isMyShip=True),
         SecondLevelRadialMenuAction(hasExtraOptions=hasExtraOptions),
         GetKeepAtRangeOption(itemID, isMyShip=True),
         SimpleRadialMenuAction(option1='UI/Commands/OpenCargoHold'),
         SimpleRadialMenuAction(),
         SimpleRadialMenuAction(option1='UI/Commands/ShowInfo'),
         GetWarpToOption(itemID, bookmarkInfo=None, isMyShip=True)]
    else:
        if siteData is not None:
            itemID = siteData.siteID
        generalActions = [GetOrbitOption(itemID),
         SecondLevelRadialMenuAction(hasExtraOptions=hasExtraOptions),
         GetKeepAtRangeOption(itemID),
         SimpleRadialMenuAction(option1='UI/Inflight/LockTarget', option2='UI/Inflight/UnlockTarget'),
         GetApproachOption(bookmarkInfo, siteData),
         SimpleRadialMenuAction(option1='UI/Commands/ShowInfo'),
         GetWarpToOption(itemID, bookmarkInfo, siteData=siteData)]
    return generalActions


def GetOrbitOption(itemID, isMyShip = False, *args):
    if isMyShip:
        return RangeRadialMenuAction(optionPath='UI/Inflight/SetDefaultOrbitDistanceShort', rangeList=GetOrbitRangesForDefault(), defaultRange=GetOrbitDefault(), callback=SetDefaultOrbit, funcArgs=itemID, alwaysAvailable=True)
    return RangeRadialMenuAction(optionPath='UI/Inflight/OrbitObject', rangeList=GetOrbitRanges(), defaultRange=GetOrbitDefault(), callback=Orbit, funcArgs=itemID)


def GetKeepAtRangeOption(itemID, isMyShip = False, *args):
    if isMyShip:
        return RangeRadialMenuAction(optionPath='UI/Inflight/SetDefaultKeepAtRangeDistanceShort', rangeList=GetKeepAtRangeRangesForDefault(), defaultRange=GetKeepAtRangeDefault(), callback=SetDefaultKeepAtRange, funcArgs=itemID, alwaysAvailable=True)
    return RangeRadialMenuAction(optionPath='UI/Inflight/Submenus/KeepAtRange', rangeList=GetKeepAtRangeRanges(), defaultRange=GetKeepAtRangeDefault(), callback=KeepAtRange, funcArgs=itemID)


def GetWarpToOption(itemID, bookmarkInfo, isMyShip = False, siteData = None, *args):
    if isMyShip:
        return RangeRadialMenuAction(optionPath='UI/Inflight/SetDefaultWarpWithinDistanceShort', rangeList=GetWarpToRanges(), defaultRange=GetWarpToDefault(), callback=SetDefaultWarpTo, funcArgs=itemID, alwaysAvailable=True)
    if bookmarkInfo:
        callback = WarpToBookmark
        funcArgs = bookmarkInfo
        optionPath2 = 'UI/Inflight/WarpToBookmark'
    elif siteData:
        callback = siteData.WarpToAction
        funcArgs = None
        optionPath2 = 'UI/Inflight/WarpToBookmark'
    else:
        optionPath2 = 'UI/Fleet/WarpToMemberSubmenuOption'
        callback = WarpTo
        funcArgs = itemID
    return RangeRadialMenuAction(optionPath='UI/Inflight/Submenus/WarpToWithin', option2Path=optionPath2, rangeList=GetWarpToRanges(), defaultRange=GetWarpToDefault(), callback=callback, funcArgs=funcArgs)


def GetApproachOption(bookmarkInfo, siteData, *args):
    if bookmarkInfo or siteData:
        option1 = 'UI/Inflight/AlignTo'
        option2 = 'UI/Inflight/ApproachLocationActionGroup'
    else:
        option1 = 'UI/Inflight/AlignTo'
        option2 = 'UI/Inflight/ApproachObject'
    return SimpleRadialMenuAction(option1=option1, option2=option2)


def GetMyShipSpecialCaseSecondLevel(typeID = None, itemID = None, *args):
    """
        your ship is special, and therefore it does have some extra options in the second level
    """
    secondLevelOptions = []
    if session.solarsystemid:
        func = sm.GetService('menu').Bookmark
        funcArgs = (itemID, typeID, session.solarsystemid)
        secondLevelOptions += [SimpleRadialMenuAction(option1='UI/Inflight/BookmarkLocation', alwaysAvailable=True, func=func, funcArgs=funcArgs)]
    return secondLevelOptions


def FindRadialMenuOptions(slimItem = None, itemID = None, typeID = None, primaryActions = True, bookmarkInfo = None, manyItemsData = None, siteData = None):
    """
        'slimItem' and 'bookmarkInfo' should never both be set, one is always None
        we prefer to get slimItem but if we don't have it or bookmarkinfo, we try to find the slimItem
    
        returns either None (if something failed) or a KeyVal with the menu option info for the
        slimItem (or itemID).
        The menu option info consists of:
            allWantedMenuOptions =  a list of all options we that should be in the radial menu
            activeSingleOptions =   a dictionary with all the avaible clickable options. The key is the labelpath and the value is
                                    the menu option keyval which contains the callback and arguments among other things
            inactiveSingleOptions = a set of menu options(labelpath) that we want in our radial menu but are not available (and are therefore greyed out)
            activeRangeOptions =    a dictionary with all the available range options. The key is the labelpath and the value is
                                     the menu option keyval which contains the callback, rangeOptions and default distance among other things
            inactiveRangeOptions =  a set with all the range options(labelpath) we want, but are not available
    """
    filterList = []
    if not bookmarkInfo and not manyItemsData and not slimItem and itemID:
        slimItem = GetBallparkRecord(itemID)
    menuSvc = sm.GetService('menu')
    if manyItemsData:
        allMenuOptions = manyItemsData.menuFunction(manyItemsData.itemData)
    elif slimItem:
        celestialData = [(slimItem.itemID,
          None,
          slimItem,
          0,
          None,
          None,
          None)]
        allMenuOptions = menuSvc.GetCelestialMenuForSelectedItem(celestialData, ignoreShipConfig=False)
        typeID = slimItem.typeID
        filterList.append('UI/Inflight/SetDestination')
    elif siteData is not None:
        allMenuOptions = siteData.GetMenu()
    elif bookmarkInfo is not None:
        allMenuOptions = menuSvc.CelestialMenu(itemID, bookmark=bookmarkInfo)
        typeID = bookmarkInfo.typeID
    elif itemID and IsCharacter(itemID):
        allMenuOptions = menuSvc.CharacterMenu(itemID) + menuSvc.FleetMenu(itemID, unparsed=False)
    elif typeID is not None:
        allMenuOptions = menuSvc.GetMenuFormItemIDTypeID(itemID, typeID)
    else:
        allMenuOptions = []
    if typeID is not None:
        typeInfo = cfg.invtypes.Get(typeID)
        categoryID = typeInfo.categoryID
        groupID = typeInfo.groupID
    else:
        categoryID = None
        groupID = None
    if primaryActions:
        allWantedMenuOptions = GetObjectsActions(categoryID, groupID, typeID, itemID, bookmarkInfo=bookmarkInfo, siteData=siteData)
    else:
        allWantedMenuOptions = GetObjectsSecondaryActions(categoryID, groupID, typeID, itemID, bookmarkInfo, siteData=siteData)
    return PrepareRadialMenuOptions(allMenuOptions, allWantedMenuOptions, filterList)


def AddOption(optionLabel, menuOption, oneClickMenuOptions, activeSingleOptions):
    menuOption.activeOption = optionLabel
    menuOption.labelArgs = oneClickMenuOptions[optionLabel].labelArgs
    callbackInfo = oneClickMenuOptions[optionLabel].callbackInfo
    menuOption.func = callbackInfo[0]
    if len(callbackInfo) > 1:
        if sm.GetService('menu').CaptionIsInMultiFunctions(optionLabel):
            menuOption.funcArgs = (callbackInfo[1],)
        else:
            menuOption.funcArgs = callbackInfo[1]
    activeSingleOptions[optionLabel] = menuOption


def PrepareRadialMenuOptions(allMenuOptions, allWantedMenuOptions, filterList, *args):
    oneClickMenuOptions = {}
    otherMenuOptions = set()
    for eachMenuEntry in allMenuOptions:
        if eachMenuEntry is None:
            continue
        menuLabel = eachMenuEntry[0]
        if isinstance(menuLabel, (MenuLabel, list)):
            actionName = menuLabel[0]
            labelArgs = menuLabel[1]
        else:
            actionName = menuLabel
            labelArgs = {}
        if actionName in filterList:
            continue
        if isinstance(eachMenuEntry[1], (types.MethodType, types.LambdaType)):
            oneClickMenuOptions[actionName] = KeyVal(callbackInfo=eachMenuEntry[1:], labelArgs=labelArgs)
        else:
            otherMenuOptions.add(actionName)

    activeSingleOptions = {}
    inactiveSingleOptions = set()
    activeRangeOptions = {}
    inactiveRangeOptions = set()
    for menuOption in allWantedMenuOptions[:]:
        option1 = menuOption.option1Path
        option2 = menuOption.Get('option2Path', None)
        if isinstance(menuOption, SimpleRadialMenuAction):
            option2 = menuOption.option2Path
            if option1 in oneClickMenuOptions:
                AddOption(option1, menuOption, oneClickMenuOptions, activeSingleOptions)
            elif option2 is not None and option2 in oneClickMenuOptions:
                AddOption(option2, menuOption, oneClickMenuOptions, activeSingleOptions)
            elif menuOption.get('alwaysAvailable', False):
                menuOption.activeOption = option1
                activeSingleOptions[option1] = menuOption
            else:
                inactiveSingleOptions.add(option1)
        elif isinstance(menuOption, RangeRadialMenuAction):
            if option1 in otherMenuOptions or menuOption.get('alwaysAvailable', False):
                activeRangeOptions[option1] = menuOption
            elif option2 in otherMenuOptions:
                menuOption.activeOption = option2
                activeRangeOptions[option2] = menuOption
            elif option2 in oneClickMenuOptions:
                newMenuOption = SimpleRadialMenuAction(option1=option1, option2=option2)
                AddOption(option2, newMenuOption, oneClickMenuOptions, activeSingleOptions)
                idx = allWantedMenuOptions.index(menuOption)
                allWantedMenuOptions[idx] = newMenuOption
            else:
                inactiveRangeOptions.add(option1)

    optionsInfo = RadialMenuOptionsInfo(allWantedMenuOptions=allWantedMenuOptions, activeSingleOptions=activeSingleOptions, inactiveSingleOptions=inactiveSingleOptions, activeRangeOptions=activeRangeOptions, inactiveRangeOptions=inactiveRangeOptions)
    return optionsInfo


def GetIconPath(labelPath):
    return iconDict.get(labelPath, None)


def KeepAtRange(itemID, distance, percOfAllRange):
    movementFunctions__KeepAtRange(itemID, distance)


def GetKeepAtRangeRanges():
    return GetRanges(minValue=500, maxValue=30000)


def GetKeepAtRangeRangesForDefault():
    return GetRanges(minValue=50, maxValue=100000)


def GetKeepAtRangeDefault():
    return sm.GetService('menu').GetDefaultActionDistance('KeepAtRange')


def Orbit(itemID, distance, percOfAllRange):
    movementFunctions__Orbit(itemID, distance)


def GetOrbitRanges():
    return GetRanges(minValue=500, maxValue=30000)


def GetOrbitRangesForDefault():
    return GetRanges(minValue=500, maxValue=100000)


def GetOrbitDefault():
    return sm.GetService('menu').GetDefaultActionDistance('Orbit')


def WarpTo(itemID, distance, percOfAllRange):
    if IsCharacter(itemID):
        sm.GetService('menu').WarpToMember(charID=itemID, warpRange=distance)
    else:
        movementFunctions__WarpToItem(itemID=itemID, warpRange=distance)


def WarpToBookmark(bookmarkInfo, distance, percOfAllRange):
    movementFunctions__WarpToBookmark(bookmark=bookmarkInfo, warpRange=distance)


def GetWarpToRanges():
    return movementFunctions__GetWarpToRanges()


def GetWarpToDefault():
    return sm.GetService('menu').GetDefaultActionDistance('WarpTo')


def GetRanges(minValue = 250, maxValue = 30000):
    newValue = minValue
    rangeList = []
    while newValue <= maxValue:
        rangeList.append(newValue)
        if newValue < 500:
            interval = 150
        elif newValue < 5000:
            interval = 250
        elif newValue < 8000:
            interval = 500
        elif newValue < 30000:
            interval = 1000
        else:
            interval = 5000
        newValue += interval

    return rangeList


def SetDefaultKeepAtRange(itemID, distance, percOfAllRange):
    sm.GetService('menu').SetDefaultKeepAtRangeDist(distance)


def SetDefaultOrbit(itemID, distance, percOfAllRange):
    sm.GetService('menu').SetDefaultOrbitDist(distance)


def SetDefaultWarpTo(itemID, distance, percOfAllRange):
    sm.GetService('menu').SetDefaultWarpToDist(distance)


def LogRadialMenuEvent(actionName, rangeVal = 0):
    uthread.new(DoLogLogRadialMenuEvent, actionName, rangeVal)


def DoLogLogRadialMenuEvent(actionName, rangeVal = 0):
    try:
        sm.GetService('infoGatheringSvc').LogInfoEvent(eventTypeID=infoEventRadialMenuAction, itemID=session.charid, int_1=rangeVal, int_2=1, char_1=actionName)
    except UserError:
        pass


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
