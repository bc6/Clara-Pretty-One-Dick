#Embedded file name: eve/client/script/ui/services\menusvc.py
import sys
import types
import random
from eve.client.script.ui.services.menuSvcExtras.menuConsts import GetReasonsDict, GetMultiFunctionList
from eve.client.script.ui.shared.industry.industryWnd import Industry
from eve.common.script.util import industryCommon
from inventorycommon.const import compareCategories
from inventorycommon.util import IsModularShip, IsShipFittingFlag
import uix
import uiutil
import uthread
import util
import log
import blue
import menu
import form
import moniker
import service
import destiny
import chat
import state
import trinity
import base
import carbonui.const as uiconst
import pos
import uicls
import eve.common.script.mgt.entityConst as entities
import localization
import invCtrl
import telemetry
import geo2
import eve.client.script.environment.spaceObject.spaceObject as spaceObject
import eve.client.script.environment.spaceObject.planet as planet
import eve.client.script.ui.util.defaultRangeUtils as defaultRangeUtils
import const
import evefleet.menu
import evegraphics.settings as gfxsettings
import evegraphics.utils as gfxutils
from eveexceptions import UserError
from spacecomponents.common.helper import HasCargoBayComponent, HasBehaviorComponent
from spacecomponents.common.helper import HasDeployComponent
from spacecomponents.common.helper import HasScoopComponent
from spacecomponents.common.helper import IsActiveComponent
from spacecomponents.common.helper import HasBountyEscrowComponent
from spacecomponents.common.helper import HasMicroJumpDriverComponent
from spacecomponents.client.components import cargobay
from spacecomponents.client.components import deploy
from spacecomponents.client.components import fitting
from spacecomponents.client.components import behavior
from spacecomponents.client.components import microJumpDriver
from spacecomponents.common.components.fitting import IsShipWithinFittingRange
from spacecomponents.common.components.bookmark import IsTypeBookmarkable
from .menuSvcExtras import menuFunctions
from .menuSvcExtras import modelDebugFunctions
from .menuSvcExtras import movementFunctions
from .menuSvcExtras import invItemFunctions
from .menuSvcExtras import droneFunctions
from .menuSvcExtras import devFunctions
from .menuSvcExtras import openFunctions
from carbon.common.script.sys.service import ROLE_GMH
from carbonui.control.menu import DISABLED_ENTRY0, CloseContextMenus
CELESTIAL_MENU_CATEGORIES = (const.categoryCelestial,
 const.categoryStructure,
 const.categoryStation,
 const.categoryShip,
 const.categoryEntity,
 const.categoryDrone,
 const.categoryAsteroid,
 const.categoryDeployable)

class MenuSvc(service.Service):
    """
        Provides menus for the client.
    """
    __guid__ = 'svc.menu'
    __update_on_reload__ = 0
    __dependencies__ = ['account',
     'addressbook',
     'pvptrade',
     'LSC',
     'fleet',
     'pwn',
     'godma',
     'michelle',
     'faction',
     'invCache',
     'viewState',
     'crimewatchSvc',
     'clientPathfinderService']
    __notifyevents__ = ['DoBallRemove', 'OnSessionChanged', 'DoBallsRemove']
    __startupdependencies__ = ['settings']

    def Run(self, memStream = None):
        self.primedMoons = {}
        self.multiFunctions = GetMultiFunctionList()
        self.allReasonsDict = GetReasonsDict()
        self.multiFunctionFunctions = [self.DeliverToCorpHangarFolder]
        uicore.uilib.RegisterForTriuiEvents([uiconst.UI_MOUSEDOWN], self.OnGlobalMouseDown)
        self.containerGroups = menuFunctions.CONTAINERGROUPS

    def OnGlobalMouseDown(self, object, *args):
        if not uiutil.IsUnder(object, uicore.layer.menu):
            CloseContextMenus()
        return True

    def Stop(self, *args):
        self.expandTimer = None

    def OnSessionChanged(self, isremote, session, change):
        self.expandTimer = None
        CloseContextMenus()
        if 'solarsystemid' in change:
            self.PrimeMoons()

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if ball is None:
            return
        self.LogInfo('DoBallRemove::menusvc', ball.id)
        if sm.GetService('camera').LookingAt() == ball.id and ball.id != session.shipid:
            if terminal:
                uthread.new(self.ResetCameraDelayed, ball.id)
            else:
                sm.GetService('camera').LookAt(session.shipid)

    def ResetCameraDelayed(self, id):
        blue.pyos.synchro.SleepWallclock(5000)
        if sm.GetService('camera').LookingAt() == id:
            sm.GetService('camera').LookAt(session.shipid)

    def TryExpandActionMenu(self, itemID, clickedObject, *args, **kwargs):
        sm.GetService('radialmenu').TryExpandActionMenu(itemID, clickedObject, *args, **kwargs)

    def AddHint(self, *args):
        return menuFunctions.AddHint(*args)

    def MapMenu(self, itemIDs, unparsed = 0):
        if type(itemIDs) == list:
            menus = []
            for itemID in itemIDs:
                menus.append(self._MapMenu(itemID, unparsed))

            return self.MergeMenus(menus)
        else:
            return self._MapMenu(itemIDs, unparsed)

    def _MapMenu(self, itemID, unparsed = 0):
        menuEntries = []
        if util.IsSolarSystem(itemID) or util.IsStation(itemID):
            waypoints = sm.StartService('starmap').GetWaypoints()
            uni, regionID, constellationID, _sol, _item = sm.StartService('map').GetParentLocationID(itemID)
            checkInWaypoints = itemID in waypoints
            menuEntries += [None]
            menuEntries += [[uiutil.MenuLabel('UI/Inflight/SetDestination'), sm.StartService('starmap').SetWaypoint, (itemID, 1)]]
            if checkInWaypoints:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/RemoveWaypoint'), sm.StartService('starmap').ClearWaypoints, (itemID,)]]
            else:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/AddWaypoint'), sm.StartService('starmap').SetWaypoint, (itemID,)]]
            menuEntries += [[uiutil.MenuLabel('UI/Inflight/BookmarkLocation'), self.Bookmark, (itemID, const.typeSolarSystem, constellationID)]]
        else:
            return []
        if unparsed:
            return menuEntries
        return self.ParseMenu(menuEntries)

    def InvItemMenu(self, invItems, viewOnly = 0, voucher = None, unparsed = 0, filterFunc = None):
        if type(invItems) == list:
            menus = []
            for invItem, viewOnly, voucher in invItems:
                menus.append(self._InvItemMenu(invItem, viewOnly, voucher, unparsed, len(invItems) > 1, filterFunc, allInvItems=invItems))

            return self.MergeMenus(menus)
        else:
            return self.MergeMenus([self._InvItemMenu(invItems, viewOnly, voucher, unparsed, filterFunc=filterFunc, allInvItems=None)])

    def _InvItemMenu(self, invItem, viewOnly, voucher, unparsed = 0, multi = 0, filterFunc = None, allInvItems = None):
        if invItem.groupID == const.groupMoney:
            return []
        godmaSM = self.godma.GetStateManager()
        invType = cfg.invtypes.Get(invItem.typeID)
        groupID = invType.groupID
        invGroup = cfg.invgroups.Get(groupID)
        categoryID = invGroup.categoryID
        invCategory = cfg.invcategories.Get(categoryID)
        serviceMask = None
        if session.stationid:
            serviceMask = eve.stationItem.serviceMask
        checkIfInSpace = self.GetCheckInSpace()
        checkIfInStation = self.GetCheckInStation()
        checkIfDrone = categoryID == const.categoryDrone
        checkIfInDroneBay = invItem.flagID == const.flagDroneBay
        checkIfInHangar = invItem.flagID == const.flagHangar
        checkIfInCargo = invItem.flagID == const.flagCargo
        checkIfInOreHold = invItem.flagID == const.flagSpecializedOreHold
        locationItem = checkIfInSpace and self.michelle.GetItem(invItem.locationID) or None
        checkIfDBLessAmmo = type(invItem.itemID) is tuple and locationItem is not None and locationItem.categoryID == const.categoryStructure
        checkIfInWreck = locationItem is not None and locationItem.groupID == const.groupWreck
        checkIfInShipMA = locationItem is not None and locationItem.groupID in (const.groupShipMaintenanceArray, const.groupAssemblyArray)
        checkIfInShipMAShip = locationItem is not None and locationItem.categoryID == const.categoryShip and godmaSM.GetType(locationItem.typeID).hasShipMaintenanceBay and invItem.flagID == const.flagShipHangar
        checkIfInShipMAShip2 = locationItem is not None and locationItem.categoryID == const.categoryShip and godmaSM.GetType(locationItem.typeID).hasShipMaintenanceBay and invItem.flagID == const.flagShipHangar and invItem.locationID != session.shipid
        checkIfShipMAShip = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).hasShipMaintenanceBay)
        checkIfShipFHShip = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).hasFleetHangars)
        checkIfShipCloneShip = bool(godmaSM.GetType(invItem.typeID).canReceiveCloneJumps)
        checkMAInRange = self.CheckMAInRange(const.maxConfigureDistance)
        checkIfCompressible = bool(self.godma.GetTypeAttribute2(invItem.typeID, const.attributeCompressionTypeID))
        checkIfShipFuelBay = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialFuelBayCapacity)
        checkIfShipOreHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialOreHoldCapacity)
        checkIfShipGasHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialGasHoldCapacity)
        checkIfShipMineralHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialMineralHoldCapacity)
        checkIfShipSalvageHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialSalvageHoldCapacity)
        checkIfShipShipHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialShipHoldCapacity)
        checkIfShipSmallShipHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialSmallShipHoldCapacity)
        checkIfShipMediumShipHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialMediumShipHoldCapacity)
        checkIfShipLargeShipHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialLargeShipHoldCapacity)
        checkIfShipIndustrialShipHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialIndustrialShipHoldCapacity)
        checkIfShipAmmoHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialAmmoHoldCapacity)
        checkIfShipCommandCenterHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialCommandCenterHoldCapacity)
        checkIfShipPlanetaryCommoditiesHold = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialPlanetaryCommoditiesHoldCapacity)
        checkIfShipHasQuafeBay = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).specialQuafeHoldCapacity)
        checkIfShipHasDroneBay = categoryID == const.categoryShip and bool(godmaSM.GetType(invItem.typeID).droneCapacity or IsModularShip(invItem.typeID))
        checkViewOnly = bool(viewOnly)
        checkIfAtStation = util.IsStation(invItem.locationID)
        checkIfActiveShip = invItem.itemID == util.GetActiveShip()
        checkIfInHangarAtStation = not (bool(checkIfInHangar) and invItem.locationID != session.stationid)
        isJettisonable = self.IsJettisonable(invItem, locationItem)
        isPlayerDeployedContainer = invItem.groupID in const.playerDeployedContainers
        checkCanContain = cfg.IsContainer(invItem)
        checkSingleton = bool(invItem.singleton)
        checkBPSingleton = bool(invItem.singleton) and invItem.categoryID == const.categoryBlueprint
        checkPlasticWrap = invItem.typeID == const.typePlasticWrap
        checkIsStation = util.IsStation(invItem.itemID)
        checkIfMineOrCorps = invItem.ownerID in [session.corpid, session.charid]
        checkIfImInStation = bool(session.stationid2)
        checkIfIsMine = invItem.ownerID == session.charid
        checkIfIsShip = invItem.categoryID == const.categoryShip
        checkIfIsCapsule = invItem.groupID == const.groupCapsule
        checkIfIsMyCorps = invItem.ownerID == session.corpid
        checkIfIsStructure = invItem.categoryID == const.categoryStructure
        checkIfIsSovStructure = categoryID == const.categorySovereigntyStructure
        checkIfOrbital = categoryID == const.categoryOrbital
        checkIfIsHardware = invCategory.IsHardware()
        checkActiveShip = util.GetActiveShip() is not None
        checkIsOrbital = util.IsOrbital(invItem.categoryID)
        checkIfRepackableInStation = categoryID in const.repackableInStationCategories or groupID in const.repackableInStationGroups
        checkIfRepackableInStructure = categoryID in const.repackableInStructureCategories
        checkIfNoneLocation = invItem.flagID == const.flagNone
        checkIfAnchorable = invGroup.anchorable
        checkConstructionPF = groupID in (const.groupConstructionPlatform, const.groupStationUpgradePlatform, const.groupStationImprovementPlatform)
        checkMineable = categoryID == const.categoryAsteroid or groupID == const.groupHarvestableCloud
        checkRefining = bool(session.stationid) and bool(serviceMask & const.stationServiceRefinery or serviceMask & const.stationServiceReprocessingPlant)
        checkRefinable = bool(checkRefining) and sm.StartService('reprocessing').GetOptionsForItemTypes({invItem.typeID: 0})[invItem.typeID].isRefinable
        checkSkill = categoryID == const.categorySkill
        checkImplant = categoryID == const.categoryImplant and bool(godmaSM.GetType(invItem.typeID).implantness)
        checkBooster = groupID == const.groupBooster and bool(godmaSM.GetType(invItem.typeID).boosterness)
        checkPilotLicence = invItem.typeID == const.typePilotLicence
        checkAurumToken = invItem.groupID == const.groupGameTime
        checkReSculptToken = invItem.typeID == const.typeReSculptToken
        checkMultiTrainingToken = invItem.typeID == const.typeMultiTrainingToken
        checkServiceItem = invItem.groupID == const.groupServices
        checkReverseRedeemable = invItem.groupID in const.reverseRedeemingLegalGroups
        checkTrashable = not checkIfActiveShip and not checkPilotLicence and not checkAurumToken and not checkServiceItem
        checkSecContainer = groupID in (const.groupSecureCargoContainer, const.groupAuditLogSecureContainer)
        checkIfInQuickBar = invItem.typeID in settings.user.ui.Get('marketquickbar', [])
        checkMultiSelection = bool(multi)
        checkAuditLogSecureContainer = groupID == const.groupAuditLogSecureContainer
        checkIfLockedInALSC = invItem.flagID == const.flagLocked
        checkIfUnlockedInALSC = invItem.flagID == const.flagUnlocked
        checkSameLocation = self.CheckSameLocation(invItem)
        checkSameStation = self.CheckSameStation(invItem)
        checkHasMarketGroup = cfg.invtypes.Get(invItem.typeID).marketGroupID is not None
        checkIsPublished = cfg.invtypes.Get(invItem.typeID).published
        chckInsuranceService = bool(session.stationid) and bool(serviceMask & const.stationServiceInsurance)
        checkRepairService = bool(session.stationid) and bool(serviceMask & const.stationServiceRepairFacilities)
        checkIfRepairable = util.IsItemOfRepairableType(invItem)
        checkLocationInSpace = locationItem is not None
        checkLocationCorpHangarArrayEquivalent = locationItem is not None and locationItem.groupID in (const.groupCorporateHangarArray, const.groupAssemblyArray, const.groupPersonalHangar)
        checkShipInStructure = locationItem is not None and locationItem.categoryID == const.categoryStructure and invItem.categoryID == const.categoryShip
        checkInControlTower = locationItem is not None and locationItem.groupID == const.groupControlTower
        checkIfInHighSec = checkIfInSpace and sm.GetService('map').GetSecurityClass(session.solarsystemid) >= const.securityClassHighSec
        checkIfInHangarOrCorpHangarAndCanTake = self.CheckIfInHangarOrCorpHangarAndCanTake(invItem)
        checkIfInDeliveries = invItem.flagID == const.flagCorpMarket
        checkIfInHangarOrCorpHangarOrDeliveriesAndCanTake = checkIfInHangarOrCorpHangarAndCanTake or checkIfInDeliveries
        isBlueprintItem = industryCommon.IsBlueprintCategory(invItem.categoryID)
        checkIfLockableBlueprint = self.CheckIfLockableBlueprint(invItem)
        checkIfUnlockableBlueprint = self.CheckIfUnlockableBlueprint(invItem)
        checkIfIAmDirector = session.corprole & const.corpRoleDirector > 0
        checkItemIsInSpace = bool(const.minSolarSystem <= invItem.locationID <= const.maxSolarSystem)
        checkStack = invItem.stacksize > 1
        checkIfQueueOpen = sm.GetService('skillqueue').IsQueueWndOpen()
        checkMultStations = False
        if allInvItems and len(allInvItems) > 0:
            checkIsMultipleStations = False
            locationIDCompare = allInvItems[0][0].locationID
            for item in allInvItems:
                item = item[0]
                if item.locationID != locationIDCompare:
                    checkIsMultipleStations = True
                    break

            checkMultStations = checkIsMultipleStations
        menuEntries = MenuList()
        if checkIfActiveShip:
            menuEntries += self.RigSlotMenu(invItem.itemID)
        if not checkMultiSelection:
            menuEntries += [[uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (invItem.typeID,
               invItem.itemID,
               0,
               invItem,
               None)]]
        if checkIfInSpace and checkIfDrone and checkIfInDroneBay and not checkViewOnly:
            menuEntries += [[uiutil.MenuLabel('UI/Drones/LaunchDrones'), self.LaunchDrones, [invItem]]]
        else:
            prereqs = [('notInSpace', checkIfInSpace, True), ('badGroup',
              checkIfDrone,
              True,
              {'groupName': invCategory.name})]
            reason = self.FindReasonNotAvailable(prereqs)
            if reason:
                menuEntries.reasonsWhyNotAvailable['UI/Drones/LaunchDrones'] = reason
        if checkStack and not checkIfInDeliveries and checkIfIsMyCorps and checkIfInHangarOrCorpHangarAndCanTake and checkIfInStation:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/SplitStack'), self.SplitStack, [invItem]]]
        menuEntries += [None]
        if checkIfInStation and checkRefining and not checkViewOnly and not checkIfInDeliveries:
            if checkMineable and checkRefinable and checkIfAtStation and checkIfInHangarAtStation:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/Reprocess'), self.Refine, [invItem]]]
            if checkSameLocation and checkRefining and checkIfAtStation and not checkIfActiveShip:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/Reprocess'), self.Refine, [invItem]]]
            if checkMineable and not checkIfAtStation and checkRefinable:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/Reprocess'), self.RefineToHangar, [invItem]]]
        menuEntries += [None]
        if not checkViewOnly:
            if checkSameLocation:
                if checkSkill and not checkIfQueueOpen:
                    menuEntries += [[uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/TrainNowToLevel1'), self.TrainNow, [invItem]]]
                if checkSkill:
                    menuEntries += [[uiutil.MenuLabel('UI/SkillQueue/InjectSkill'), self.InjectSkillIntoBrain, [invItem]]]
                if checkImplant:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/PlugInImplant'), self.PlugInImplant, [invItem]]]
                if checkBooster:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ConsumeBooster'), self.ConsumeBooster, [invItem]]]
            if checkPilotLicence and not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/ActivatePlex'), self.ActivatePlex, (invItem.itemID,)]]
            if checkReverseRedeemable and not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ReverseRedeem'), sm.GetService('redeem').ReverseRedeem, (invItem,)]]
            if checkAurumToken and checkIfInStation and checkSameLocation and not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/RedeemForAurum'), self.ApplyAurumToken, (invItem, invItem.stacksize)]]
            if checkReSculptToken and not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/ActivateCharacterReSculptToken'), self.ActivateCharacterReSculpt, (invItem.itemID,)]]
            if checkMultiTrainingToken and not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/ActivateMultiTrainingToken'), self.ActivateMultiTraining, (invItem.itemID,)]]
        menuEntries += [None]
        if not checkViewOnly and checkSameLocation and not checkMultiSelection and checkSingleton:
            if checkSecContainer and checkIfInStation:
                desc = localization.GetByLabel('UI/Menusvc/SetNewPasswordForContainerDesc')
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/SetNewPasswordForContainer'), self.AskNewContainerPwd, ([invItem], desc, const.SCCPasswordTypeGeneral)]]
            if checkAuditLogSecureContainer and checkIfInStation:
                desc = localization.GetByLabel('UI/Menusvc/SetNewPasswordForContainerDesc')
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/SetNewConfigPasswordForContainer'), self.AskNewContainerPwd, ([invItem], desc, const.SCCPasswordTypeConfig)]]
            if checkAuditLogSecureContainer and checkIfMineOrCorps:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ViewLog'), openFunctions.ViewAuditLogForALSC, (invItem.itemID,)], [uiutil.MenuLabel('UI/Inventory/ItemActions/ConfigureALSContainer'), self.ConfigureALSC, (invItem.itemID,)], [uiutil.MenuLabel('UI/Commands/RetrievePassword'), self.RetrievePasswordALSC, (invItem.itemID,)]]
            if isPlayerDeployedContainer and not checkIsOrbital:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/SetName'), self.SetName, (invItem,)]]
        if isPlayerDeployedContainer and groupID != const.groupSiphonPseudoSilo and checkIfInStation and not checkSingleton and not checkViewOnly and checkSameLocation:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/AssembleContainer'), self.AssembleContainer, [invItem]]]
        menuEntries += [None]
        if checkConstructionPF and not checkViewOnly and checkSingleton and not checkMultiSelection:
            desc1 = localization.GetByLabel('UI/Menusvc/SetAccessPasswordOnPlatformDesc')
            desc2 = localization.GetByLabel('UI/Menusvc/SetBuildPasswordOnPlatformDesc')
            menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/SetPlatformAccessPassword'), self.AskNewContainerPwd, ([invItem], desc1, const.SCCPasswordTypeGeneral)]]
            menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/SetPlatformBuildPassword'), self.AskNewContainerPwd, ([invItem], desc2, const.SCCPasswordTypeConfig)]]
        if checkIfInSpace and checkIfDBLessAmmo and not checkMultiSelection:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/TransferAmmoToCarbo'), self.TransferToCargo, (invItem.itemID,)]]
        menuEntries += [None]
        if checkIfUnlockedInALSC:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/LockItem'), self.ALSCLock, [invItem]]]
        if checkIfLockedInALSC:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/UnlockItem'), self.ALSCUnlock, [invItem]]]
        if checkIfLockableBlueprint:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ProposeBlueprintLockdownVote'), self.LockDownBlueprint, (invItem,)]]
        if checkIfUnlockableBlueprint:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ProposeBlueprintUnlockVote'), self.UnlockBlueprint, (invItem,)]]
        if checkIfIsShip and checkIfInStation and chckInsuranceService and checkSameStation and checkSingleton:
            if (checkIfIsMine or checkIfMineOrCorps and session.corprole & (const.corpRoleJuniorAccountant | const.corpRoleAccountant != 0)) and sm.GetService('insurance').GetInsurancePrice(invItem.typeID) > 0:
                menuEntries += [[uiutil.MenuLabel('UI/Insurance/InsuranceWindow/Commands/Insure'), sm.GetService('insurance').Insure, (invItem,)]]
        if checkIfInStation and checkRepairService and checkIfRepairable and checkIfAtStation and checkSameLocation and checkIfIsMine:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/GetRepairQuote'), openFunctions.RepairItems, [invItem]]]
        if checkHasMarketGroup and not checkIsStation:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'), self.ShowMarketDetails, (invItem,)]]
            if checkIfMineOrCorps and not checkIfActiveShip and checkIfInHangarOrCorpHangarAndCanTake and not checkBPSingleton and not invItem.singleton:
                if allInvItems and len(allInvItems) > 1:
                    sellMenuLabel = 'UI/Inventory/ItemActions/MultiSell'
                    sellItems = allInvItems
                else:
                    sellMenuLabel = 'UI/Inventory/ItemActions/SellThisItem'
                    sellItems = [allInvItems]
                menuEntries += [[uiutil.MenuLabel(sellMenuLabel), self.MultiSell, [sellItems]]]
            if not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/BuyThisType'), self.QuickBuy, (invItem.typeID,)]]
        if not checkIsStation and checkIfMineOrCorps and not checkIfActiveShip and not checkMultStations and checkIfInHangarOrCorpHangarOrDeliveriesAndCanTake:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/CreateContract'), self.QuickContract, [invItem]]]
        if checkIsPublished and not checkMultiSelection and not checkIsStation:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/FindInContracts'), sm.GetService('contracts').FindRelated, (invItem.typeID,
               None,
               None,
               None,
               None,
               None)]]
        if not checkIfInQuickBar and not checkMultiSelection and not checkIsStation and not checkIfIsCapsule:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/AddTypeToMarketQuickbar'), self.AddToQuickBar, (invItem.typeID,)]]
        if checkIfInQuickBar and not checkMultiSelection:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/RemoveTypeFromMarketQuickbar'), self.RemoveFromQuickBar, (invItem,)]]
        if checkIfInHangar and checkIfAtStation and checkIfIsMine and checkCanContain and not checkIfIsCapsule:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ViewContents'), self.GetContainerContents, [invItem]]]
        if not checkViewOnly and checkSingleton:
            if checkSameLocation and isPlayerDeployedContainer and not checkIfInDeliveries:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/OpenContainer'), openFunctions.OpenCargoContainer, [invItem]]]
                if checkIfAtStation and checkIfInHangar and checkPlasticWrap:
                    menuEntries += [[uiutil.MenuLabel('UI/Contracts/BreakContract'), self.Break, [invItem]]]
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ContractsDelieverCourierPackage'), self.DeliverCourierContract, [invItem]]]
            if checkSameStation and checkIfIsShip and checkIfImInStation and checkIfAtStation and checkIfInHangar and checkIfIsMine and not checkMultiSelection:
                if not checkIfActiveShip and checkIfMineOrCorps:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/MakeShipActive'), self.ActivateShip, (invItem,)]]
                if checkIfActiveShip and checkIfMineOrCorps and not checkIfIsCapsule:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/LeaveShip'), self.LeaveShip, (invItem,)]]
                if not checkIfIsCapsule:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/StripFitting'), self.StripFitting, [invItem]]]
        if isPlayerDeployedContainer and checkPlasticWrap:
            menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/FindContract'), self.FindCourierContract, [invItem]]]
        menuEntries += [None]
        if isBlueprintItem:
            text = uiutil.MenuLabel('UI/Industry/UseBlueprint')
            menuEntries += [[text, self.ShowInIndustryWindow, [invItem]]]
        menuEntries += [None]
        if not checkViewOnly:
            if checkIfIsShip and checkSameLocation and checkIfImInStation and checkIfAtStation and checkIfInHangar and checkIfIsMine and not checkSingleton:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/AssembleShip'), self.AssembleShip, [invItem]]]
            if checkIfIsShip and checkIfInSpace and checkIfInCargo and checkIfIsMine and not checkSingleton:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/AssembleShip'), self.AssembleShip, [invItem]]]
            if checkIfIsShip and checkIfInSpace and checkLocationCorpHangarArrayEquivalent and checkLocationInSpace and not checkSingleton:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/AssembleShip'), self.AssembleShip, [invItem]]]
            if checkIfImInStation and checkIfIsHardware and checkActiveShip and checkSameStation and not checkImplant and not checkBooster:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/FitToActiveShip'), self.TryFit, [invItem]]]
            if checkIfInSpace and not checkIfInDroneBay and checkIfDrone and checkMAInRange:
                menuEntries += [[uiutil.MenuLabel('UI/Drones/MoveToDroneBay'), self.FitDrone, [invItem]]]
        menuEntries += [None]
        if checkIfImInStation and checkIfInHangar and checkIfIsShip and checkSingleton and checkSameStation:
            if checkIfActiveShip and checkIfShipCloneShip:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/ConfigureShipCloneFacility'), self.ShipCloneConfig, (invItem.itemID,)]]
            if not checkIfIsCapsule:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenCargoHold'), openFunctions.OpenShipHangarCargo, [invItem.itemID]]]
            if checkIfShipHasDroneBay:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenDroneBay'), openFunctions.OpenDroneBay, [invItem.itemID]]]
            if checkIfShipMAShip:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenShipMaintenanceBay'), openFunctions.OpenShipMaintenanceBayShip, (invItem.itemID, localization.GetByLabel('UI/Commands/OpenShipMaintenanceBayError'))]]
            if checkIfShipFHShip:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenFleetHangar'), openFunctions.OpenFleetHangar, (invItem.itemID,)]]
            if checkIfShipFuelBay:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenFuelBay'), self.OpenFuelBay, [invItem.itemID]]]
            if checkIfShipOreHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenOreHold'), self.OpenOreHold, [invItem.itemID]]]
            if checkIfShipGasHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenGasHold'), self.OpenGasHold, [invItem.itemID]]]
            if checkIfShipMineralHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenMineralHold'), self.OpenMineralHold, [invItem.itemID]]]
            if checkIfShipSalvageHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenSalvageHold'), self.OpenSalvageHold, [invItem.itemID]]]
            if checkIfShipShipHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenShipHold'), self.OpenShipHold, [invItem.itemID]]]
            if checkIfShipSmallShipHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenSmallShipHold'), self.OpenSmallShipHold, [invItem.itemID]]]
            if checkIfShipMediumShipHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenMediumShipHold'), self.OpenMediumShipHold, [invItem.itemID]]]
            if checkIfShipLargeShipHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenLargeShipHold'), self.OpenLargeShipHold, [invItem.itemID]]]
            if checkIfShipIndustrialShipHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenIndustrialShipHold'), self.OpenIndustrialShipHold, [invItem.itemID]]]
            if checkIfShipAmmoHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenAmmoHold'), self.OpenAmmoHold, [invItem.itemID]]]
            if checkIfShipCommandCenterHold:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenCommandCenterHold'), self.OpenCommandCenterHold, [invItem.itemID]]]
            if checkIfShipPlanetaryCommoditiesHold:
                menuEntries += [[uiutil.MenuLabel('UI/PI/Common/OpenPlanetaryCommoditiesHold'), self.OpenPlanetaryCommoditiesHold, [invItem.itemID]]]
            if checkIfShipHasQuafeBay:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenQuafeBay'), self.OpenQuafeHold, [invItem.itemID]]]
        menuEntries += [None]
        if checkSameStation and checkIfImInStation and checkIfInHangar and checkIfIsShip and checkIfIsMine and checkSingleton and not checkMultiSelection and not checkViewOnly:
            menuEntries += [[uiutil.MenuLabel('UI/Commands/ChangeName'), self.SetName, (invItem,)]]
        if checkSingleton and checkIfInHangarOrCorpHangarAndCanTake and checkIfMineOrCorps:
            if not checkIsStation and not checkLocationInSpace and not checkIfActiveShip and checkIfRepackableInStation:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/Repackage'), self.RepackageItemsInStation, [invItem]]]
            elif checkLocationCorpHangarArrayEquivalent and checkIfRepackableInStructure:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/Repackage'), self.RepackageItemsInStructure, [invItem]]]
        menuEntries += [None]
        if checkIfInSpace and not checkViewOnly:
            if checkIfInCargo:
                if HasDeployComponent(invItem.typeID):
                    menuEntries.extend(deploy.GetDeployMenu(invItem))
                elif checkIfAnchorable:
                    if not checkConstructionPF and not checkIfIsStructure and not checkIfIsSovStructure and not checkIfOrbital:
                        menuEntries.append([uiutil.MenuLabel('UI/Inventory/ItemActions/LaunchForSelf'), self.LaunchForSelf, [invItem]])
                    menuEntries.append([uiutil.MenuLabel('UI/Inventory/ItemActions/LaunchForCorp'), self.LaunchForCorp, [invItem]])
            if isJettisonable:
                if invItem.flagID in const.jettisonableFlags and not checkPlasticWrap:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/Jettison'), self.Jettison, [invItem]]]
            elif isPlayerDeployedContainer and not checkIfAnchorable:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/LaunchForSelf'), self.Jettison, [invItem]]]
            if checkIfIsShip and not checkMultiSelection:
                if checkIfInShipMA:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/LaunchShip'), self.LaunchSMAContents, [invItem]]]
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/BoardShip'), self.BoardSMAShip, (invItem.locationID, invItem.itemID)]]
                if checkIfInShipMAShip:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/LaunchShipFromBay'), self.LaunchSMAContents, [invItem]]]
                if checkIfInShipMAShip2:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/BoardShipFromBay'), self.BoardSMAShip, (invItem.locationID, invItem.itemID)]]
                if checkIfInWreck and invItem.singleton:
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/LaunchShip'), self.LaunchSMAContents, [invItem]]]
        if checkIfImInStation and checkSameStation and checkIfIsShip and checkIfActiveShip:
            menuEntries += [[uiutil.MenuLabel('UI/Commands/UndockFromStation'), self.ExitStation, (invItem,)]]
        if locationItem is not None and checkIfCompressible and locationItem.groupID in (const.groupCompressionArray, const.groupCapitalIndustrialShip):
            menuEntries += [[uiutil.MenuLabel('UI/Commands/Compress'), self.CompressItem, (invItem, locationItem)]]
        if locationItem is not None and locationItem.groupID == const.groupReprocessingArray:
            if invItem.categoryID == const.categoryAsteroid or invItem.groupID == const.groupRefinables:
                menuEntries += [[uiutil.MenuLabel('UI/ScienceAndIndustry/Reprocess'), self.Reprocess, (invItem, locationItem)]]
        if not util.IsNPC(session.corpid) and checkIfIsMyCorps:
            deliverToMenu = []
            divisions = sm.GetService('corp').GetDivisionNames()
            deliverToCorpHangarMenu = [(divisions[1], self.DeliverToCorpHangarFolder, [[invItem, const.flagHangar]]),
             (divisions[2], self.DeliverToCorpHangarFolder, [[invItem, const.flagCorpSAG2]]),
             (divisions[3], self.DeliverToCorpHangarFolder, [[invItem, const.flagCorpSAG3]]),
             (divisions[4], self.DeliverToCorpHangarFolder, [[invItem, const.flagCorpSAG4]]),
             (divisions[5], self.DeliverToCorpHangarFolder, [[invItem, const.flagCorpSAG5]]),
             (divisions[6], self.DeliverToCorpHangarFolder, [[invItem, const.flagCorpSAG6]]),
             (divisions[7], self.DeliverToCorpHangarFolder, [[invItem, const.flagCorpSAG7]])]
            deliverToMenu.append([uiutil.MenuLabel('UI/Corporations/CorpHangarSubmenu'), deliverToCorpHangarMenu])
            deliverToMenu.append((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Members/CorpMember'), self.DeliverToCorpMember, [invItem]))
            if not checkIfNoneLocation and not checkLocationCorpHangarArrayEquivalent and checkIfInHangarOrCorpHangarOrDeliveriesAndCanTake:
                menuEntries += [None]
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/DeliverCorpStuffTo'), deliverToMenu]]
        menuEntries += [None]
        if checkTrashable:
            if checkIfInHangar and checkIfAtStation and checkIfIsMine:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/TrashIt'), self.TrashInvItems, [invItem]]]
            if checkIfIsMyCorps and checkIfIAmDirector and not checkItemIsInSpace and not checkShipInStructure and not checkInControlTower and checkIfInHangarOrCorpHangarAndCanTake:
                menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/TrashIt'), self.TrashInvItems, [invItem]]]
        checkCanConfigureOrbital = invItem and invItem.groupID != const.groupOrbitalConstructionPlatforms
        checkIsOrbital = util.IsOrbital(invItem.categoryID)
        if checkIsOrbital and checkCanConfigureOrbital:
            menuEntries += [[uiutil.MenuLabel('UI/DustLink/ConfigureOrbital'), self.ConfigureOrbital, (invItem,)]]
        if categoryID in compareCategories:
            menuEntries += [(uiutil.MenuLabel('UI/Compare/CompareButton'), self.CompareType, (invItem.typeID,))]
        if unparsed:
            return menuEntries
        m = []
        if not (filterFunc and 'GM / WM Extras' in filterFunc) and session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            m = [('GM / WM Extras', ('isDynamic', self.GetGMMenu, (invItem.itemID,
                None,
                None,
                invItem,
                None)))]
        return m + self.ParseMenu(menuEntries, filterFunc)

    def CheckItemsInSamePlace(self, invItems):
        return invItemFunctions.CheckItemsInSamePlace(invItems)

    def InvalidateItemLocation(self, ownerID, stationID, flag):
        return invItemFunctions.InvalidateItemLocation(ownerID, stationID, flag, self.invCache)

    def DeliverToCorpHangarFolder(self, invItemAndFlagList):
        return invItemFunctions.DeliverToCorpHangarFolder(invItemAndFlagList, self.invCache)

    def DeliverToCorpMember(self, invItems):
        return invItemFunctions.DeliverToCorpMember(invItems, self.invCache)

    def SplitStack(self, invItems):
        return invItemFunctions.SplitStack(invItems, self.invCache)

    def GetDroneMenu(self, data):
        return self.DroneMenu(data, unmerged=0)

    def DroneMenu(self, data, unmerged = 0):
        """
            data is tuple of itemIDs and groupIDs ((itemID, groupID, ownerID),)
        """
        menu = self.GetGroupSpecificDroneMenu(data, unmerged=unmerged)
        menu += self.GetCommonDroneMenu(data, unmerged=unmerged)
        return menu

    def GetGroupSpecificDroneMenu(self, data, unmerged = 0):
        """
            data is tuple of itemIDs and groupIDs ((itemID, groupID, ownerID),)
        """
        menuEntries = MenuList()
        targetID = sm.GetService('target').GetActiveTargetID()
        for droneID, groupID, ownerID in data:
            droneState = sm.StartService('michelle').GetDroneState(droneID)
            if droneState:
                ownerID = droneState.ownerID
                controllerID = droneState.controllerID
                groupID = cfg.invtypes.Get(droneState.typeID).groupID
            else:
                controllerID = None
            groupName = cfg.invgroups.Get(groupID).name
            bp = sm.StartService('michelle').GetBallpark()
            if not bp:
                return []
            checkMiningDrone = groupID == const.groupMiningDrone
            checkSalvageDrone = groupID == const.groupSalvageDrone
            checkFighterDrone = groupID == const.groupFighterDrone
            checkCombatDrone = groupID == const.groupCombatDrone
            checkUnanchoringDrone = groupID == const.groupUnanchoringDrone
            checkOtherDrone = not (checkMiningDrone or checkUnanchoringDrone or checkSalvageDrone)
            checkOwner = ownerID == session.charid
            checkController = controllerID == session.shipid
            checkDroneState = droneState is not None
            checkFleet = bool(session.fleetid)
            m = []
            if checkController and checkDroneState:
                if checkOtherDrone:
                    droneIDs = [droneID]
                    crimewatchSvc = sm.GetService('crimewatchSvc')
                    requiredSafetyLevel = crimewatchSvc.GetRequiredSafetyLevelForEngagingDrones(droneIDs, targetID)
                    menuClass = None
                    if crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
                        if requiredSafetyLevel == const.shipSafetyLevelNone:
                            menuClass = uicls.CriminalMenuEntryView
                        else:
                            menuClass = uicls.SuspectMenuEntryView
                    m += [[uiutil.MenuLabel('UI/Drones/EngageTarget'),
                      self.EngageTarget,
                      droneIDs,
                      None,
                      menuClass]]
                else:
                    reason = self.FindReasonNotAvailable([('thisIsNot',
                      checkOtherDrone,
                      True,
                      {'groupName': groupName})])
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Drones/EngageTarget'] = reason
                if checkMiningDrone:
                    m += [[uiutil.MenuLabel('UI/Drones/MineWithDrone'), self.Mine, [droneID]]]
                    m += [[uiutil.MenuLabel('UI/Drones/MineRepeatedly'), self.MineRepeatedly, [droneID]]]
                elif checkSalvageDrone:
                    m += [[uiutil.MenuLabel('UI/Drones/Salvage'), self.Salvage, [[droneID]]]]
                else:
                    reason = self.FindReasonNotAvailable([('thisIsNot',
                      checkMiningDrone,
                      True,
                      {'groupName': groupName})])
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Drones/MineWithDrone'] = reason
                        menuEntries.reasonsWhyNotAvailable['UI/Drones/MineRepeatedly'] = reason
            else:
                prereqs = [('dontControlDrone', checkController, True), ('droneIncapacitated', checkDroneState, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Drones/EngageTarget'] = reason
                    menuEntries.reasonsWhyNotAvailable['UI/Drones/MineWithDrone'] = reason
                    menuEntries.reasonsWhyNotAvailable['UI/Drones/MineRepeatedly'] = reason
            if checkOwner and checkController and checkFleet and checkDroneState:
                if checkFighterDrone:
                    m += [[uiutil.MenuLabel('UI/Drones/DelegateDroneControl'), ('isDynamic', self.GetFleetMemberMenu, (self.DelegateControl,)), [droneID]]]
                elif checkCombatDrone:
                    m += [[uiutil.MenuLabel('UI/Drones/DroneAssist'), ('isDynamic', self.GetFleetMemberMenu, (self.Assist,)), [droneID]]]
                    m += [[uiutil.MenuLabel('UI/Drones/DroneGuard'), ('isDynamic', self.GetFleetMemberMenu, (self.Guard,)), [droneID]]]
            if not checkOwner and checkController and checkFighterDrone and checkDroneState:
                m += [[uiutil.MenuLabel('UI/Drones/ReturnDroneControl'), self.ReturnControl, [droneID]]]
            if checkController and checkUnanchoringDrone and checkDroneState:
                m += [[uiutil.MenuLabel('UI/Inflight/UnanchorObject'), self.DroneUnanchor, [droneID]]]
            else:
                prereqs = [('dontControlDrone', checkController, True), ('thisIsNot',
                  checkUnanchoringDrone,
                  True,
                  {'groupName': groupName}), ('droneIncapacitated', checkDroneState, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/UnanchorObject'] = reason
            if unmerged:
                menuEntries.append(m)
            else:
                menuEntries.append(self.ParseMenu(m))
                menuEntries.reasonsWhyNotAvailable = getattr(self, 'reasonsWhyNotAvailable', {})

        if unmerged:
            return menuEntries
        merged = self.MergeMenus(menuEntries)
        return merged

    def GetCommonDroneMenu(self, data, unmerged = 0):
        """
            data is tuple of itemIDs and groupIDs ((itemID, groupID, ownerID),)
        """
        menuEntries = MenuList()
        for droneID, groupID, ownerID in data:
            droneState = sm.StartService('michelle').GetDroneState(droneID)
            if droneState:
                ownerID = droneState.ownerID
                controllerID = droneState.controllerID
            else:
                controllerID = None
            bp = sm.StartService('michelle').GetBallpark()
            if not bp:
                return []
            droneBall = bp.GetBall(droneID)
            checkOwner = ownerID == session.charid
            checkController = controllerID == session.shipid
            checkDroneState = droneState is not None
            dist = droneBall and max(0, droneBall.surfaceDist)
            checkScoopable = droneState is None or ownerID == session.charid
            checkScoopDist = dist is not None and dist < const.maxCargoContainerTransferDistance
            checkWarpDist = dist > const.minWarpDistance
            checkOwnerOrController = checkOwner or checkController
            m = []
            if checkOwnerOrController and checkDroneState:
                m += [[uiutil.MenuLabel('UI/Drones/ReturnDroneAndOrbit'), self.ReturnAndOrbit, [droneID]]]
            else:
                prereqs = [('dontControlDrone', checkOwnerOrController, True), ('droneIncapacitated', checkDroneState, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Drones/ReturnDroneAndOrbit'] = reason
            if checkOwner and checkDroneState:
                m += [[uiutil.MenuLabel('UI/Drones/ReturnDroneToBay'), self.ReturnToDroneBay, [droneID]]]
            else:
                prereqs = [('dontOwnDrone', checkOwner, True), ('droneIncapacitated', checkDroneState, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Drones/ReturnDroneToBay'] = reason
            if not checkWarpDist and checkScoopable and droneBall is not None:
                m += [[uiutil.MenuLabel('UI/Drones/ScoopDroneToBay'), self.ScoopToDroneBay, [droneID]]]
            else:
                prereqs = [('cantScoopDrone', checkScoopable, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Drones/ScoopDroneToBay'] = reason
            m += [None]
            if checkOwner and checkDroneState:
                m += [[uiutil.MenuLabel('UI/Drones/AbandonDrone'), self.AbandonDrone, [droneID]]]
            if unmerged:
                menuEntries.append(m)
            else:
                menuEntries.append(self.ParseMenu(m))

        if unmerged:
            return menuEntries
        merged = self.MergeMenus(menuEntries)
        return merged

    def CharacterMenu(self, charid, charIDs = [], corpid = None, unparsed = 0, filterFunc = None, **kwargs):
        if type(charid) == list:
            menus = []
            for chid, coid in charid:
                menus.append(self._CharacterMenu(chid, coid, unparsed, filterFunc, len(charid) > 1), **kwargs)

            return self.MergeMenus(menus)
        else:
            return self._CharacterMenu(charid, corpid, unparsed, filterFunc, **kwargs)

    def _CharacterMenu(self, charid, corpid, unparsed = 0, filterFunc = None, multi = 0, **kwargs):
        if not charid:
            return []
        addressBookSvc = sm.GetService('addressbook')
        checkIsNPC = util.IsNPC(charid)
        checkIsAgent = sm.GetService('agents').IsAgent(charid)
        checkInStation = bool(session.stationid)
        checkInAddressbook = bool(addressBookSvc.IsInAddressBook(charid, 'contact'))
        checkInCorpAddressbook = bool(addressBookSvc.IsInAddressBook(charid, 'corpcontact'))
        checkInAllianceAddressbook = bool(addressBookSvc.IsInAddressBook(charid, 'alliancecontact'))
        checkIfBlocked = addressBookSvc.IsBlocked(charid)
        checkIfGuest = session.stationid and sm.StartService('station').IsGuest(charid)
        checkIfMe = charid == session.charid
        checkHaveCloneBay = sm.GetService('clonejump').HasCloneReceivingBay()
        checkIfExecCorp = session.allianceid and sm.GetService('alliance').GetAlliance(session.allianceid).executorCorpID == session.corpid
        checkIAmDiplomat = (const.corpRoleDirector | const.corpRoleDiplomat) & session.corprole != 0
        checkIfEmpireSpace = sm.GetService('map').GetSecurityClass(session.solarsystemid2) != const.securityClassZeroSec
        checkIfDustCharacter = util.IsDustCharacter(charid)
        checkMultiSelection = bool(multi)
        menuEntries = MenuList()
        doShowInfo = True
        if checkIsAgent:
            agentInfo = sm.GetService('agents').GetAgentByID(charid)
            if agentInfo and agentInfo.agentTypeID == const.agentTypeAura:
                doShowInfo = False
        if doShowInfo:
            menuEntries += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (cfg.eveowners.Get(charid).typeID, charid))]
        if not checkMultiSelection and not checkIfMe and not checkIsNPC:
            isRecruiting = None
            if 'isRecruiting' in kwargs:
                isRecruiting = kwargs['isRecruiting']
            menuEntries += [[uiutil.MenuLabel('UI/Chat/StartConversation'), sm.StartService('LSC').Invite, (charid, None, isRecruiting)]]
        else:
            prereqs = [('checkMultiSelection', checkMultiSelection, False), ('checkIfMe', checkIfMe, False), ('checkIsNPC', checkIsNPC, False)]
            reason = self.FindReasonNotAvailable(prereqs)
            if reason:
                menuEntries.reasonsWhyNotAvailable['UI/Chat/StartConversation'] = reason
        if not checkMultiSelection and not checkIfMe and checkIsNPC and checkIsAgent:
            menuEntries += [[uiutil.MenuLabel('UI/Chat/StartConversationAgent'), sm.StartService('agents').InteractWith, (charid,)]]
        else:
            prereqs = [('checkMultiSelection', checkMultiSelection, False),
             ('checkIfMe', checkIfMe, False),
             ('checkIsNPC', checkIsNPC, True),
             ('checkIsAgent', checkIsAgent, True)]
            reason = self.FindReasonNotAvailable(prereqs)
            if reason:
                menuEntries.reasonsWhyNotAvailable['UI/Chat/StartConversation'] = reason
        if not checkIfMe:
            if not checkInAddressbook and checkIsNPC and checkIsAgent:
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/AddToAddressbook'), addressBookSvc.AddToPersonalMulti, [charid]]]
            if not checkIsNPC:
                if not checkMultiSelection:
                    menuEntries += [[uiutil.MenuLabel('UI/Chat/InviteToChat'), ('isDynamic', self.__GetInviteMenu, (charid,))]]
                menuEntries += [[uiutil.MenuLabel('UI/EVEMail/SendPilotEVEMail'), sm.StartService('mailSvc').SendMsgDlg, ([charid], None, None)]]
                if not checkMultiSelection and not checkInAddressbook:
                    menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/AddContact'), addressBookSvc.AddToPersonalMulti, [charid, 'contact']]]
                if not checkMultiSelection and checkInAddressbook:
                    menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/EditContact'), addressBookSvc.AddToPersonalMulti, [charid, 'contact', True]]]
                if not checkMultiSelection and checkInAddressbook:
                    menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveContact'), addressBookSvc.DeleteEntryMulti, [[charid], 'contact']]]
            if checkInAddressbook and checkIsNPC and checkIsAgent:
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveFromAddressbook'), addressBookSvc.DeleteEntryMulti, [charid]]]
            if not checkMultiSelection and checkIfBlocked:
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/UnblockContact'), addressBookSvc.UnblockOwner, ([charid],)]]
            if not checkMultiSelection and not checkIsNPC and not checkIfBlocked:
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/BlockContact'), addressBookSvc.BlockOwner, (charid,)]]
        if not checkIsNPC and checkIAmDiplomat:
            if not checkInCorpAddressbook:
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/AddCorpContact'), addressBookSvc.AddToPersonalMulti, [charid, 'corpcontact']]]
            else:
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/EditCorpContact'), addressBookSvc.AddToPersonalMulti, [charid, 'corpcontact', True]]]
                menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveCorpContact'), addressBookSvc.DeleteEntryMulti, [[charid], 'corpcontact']]]
            if checkIfExecCorp and not checkIfDustCharacter:
                if not checkInAllianceAddressbook:
                    menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/AddAllianceContact'), addressBookSvc.AddToPersonalMulti, [charid, 'alliancecontact']]]
                else:
                    menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/EditAllianceContact'), addressBookSvc.AddToPersonalMulti, [charid, 'alliancecontact', True]]]
                    menuEntries += [[uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveAllianceContact'), addressBookSvc.DeleteEntryMulti, [[charid], 'alliancecontact']]]
        if not checkMultiSelection and not checkIfMe and not checkIsNPC and not checkIfDustCharacter:
            menuEntries += [[uiutil.MenuLabel('UI/Commands/GiveMoney'), sm.StartService('wallet').TransferMoney, (session.charid,
               None,
               charid,
               None)]]
            if checkHaveCloneBay and not checkIfDustCharacter:
                menuEntries += [[uiutil.MenuLabel('UI/CloneJump/OfferCloneInstallation'), sm.StartService('clonejump').OfferShipCloneInstallation, (charid,)]]
        if not multi:
            agentInfo = sm.StartService('agents').GetAgentByID(charid)
            if agentInfo:
                if agentInfo.solarsystemID and agentInfo.solarsystemID != session.solarsystemid2:
                    menuEntries += [None]
                    menuEntries += self.MapMenu(agentInfo.stationID, unparsed=1)
        if not checkMultiSelection and not checkIfMe and checkInStation and not checkIsNPC and checkIfGuest and not checkIfDustCharacter:
            menuEntries += [[uiutil.MenuLabel('UI/Market/TradeWithCharacter'), sm.StartService('pvptrade').StartTradeSession, (charid,)]]
        if not checkMultiSelection and not checkIsNPC and not checkIfDustCharacter:
            menuEntries += [[uiutil.MenuLabel('UI/Station/BountyOffice/PlaceBounty'), openFunctions.OpenBountyOffice, (charid,)]]
        if not checkIsNPC and not util.IsDustCharacter(charid):
            menuEntries += [[uiutil.MenuLabel('UI/Commands/CapturePortrait'), sm.StartService('photo').SavePortraits, [charid]]]
        if not checkIsNPC and not checkIfDustCharacter:
            if session.fleetid is not None:
                fleetSvc = sm.GetService('fleet')
                members = fleetSvc.GetMembers()
                checkIfImLeader = self.ImFleetLeaderOrCommander()
                member = members.get(charid, None)
                if member is None:
                    if not checkMultiSelection and checkIfImLeader:
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/InvitePilotToFleet'), self.FleetInviteMenu(charid)]]
                elif not checkMultiSelection:
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/Fleet'), ('isDynamic', self.FleetMenu, (charid, False))]]
            else:
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FormFleetWith'), self.InviteToFleet, [charid]]]
        if checkIfEmpireSpace and not (checkIsNPC or checkIfMe or checkIfDustCharacter or checkMultiSelection):
            if not self.crimewatchSvc.HasLimitedEngagmentWith(charid):
                menuEntries += [[uiutil.MenuLabel('UI/Crimewatch/Duel/DuelMenuEntry'), self.crimewatchSvc.StartDuel, (charid,)]]
        if not checkIsNPC:
            menuEntries += self.CorpMemberMenu(charid, multi)
        if unparsed:
            return menuEntries
        m = []
        if not (filterFunc and 'GM / WM Extras' in filterFunc) and session.role & (service.ROLE_GML | service.ROLE_WORLDMOD | service.ROLE_LEGIONEER):
            m = [('GM / WM Extras', ('isDynamic', self.GetGMMenu, (None,
                None,
                charid,
                None,
                None)))]
        return m + self.ParseMenu(menuEntries, filterFunc)

    def GetCheckInSpace(self):
        return bool(session.solarsystemid)

    def GetCheckInStation(self):
        return bool(session.stationid)

    def CheckIfLockableBlueprint(self, invItem):
        return invItemFunctions.CheckIfLockableBlueprint(invItem)

    def CheckIfUnlockableBlueprint(self, invItem):
        return invItemFunctions.CheckIfUnlockableBlueprint(invItem)

    def CheckIfInHangarOrCorpHangarAndCanTake(self, invItem):
        return invItemFunctions.CheckIfInHangarOrCorpHangarAndCanTake(invItem)

    def CheckSameStation(self, invItem):
        return invItemFunctions.CheckSameStation(invItem)

    def CheckSameLocation(self, invItem):
        return invItemFunctions.CheckSameLocation(invItem)

    def CheckMAInRange(self, useRange):
        if not session.solarsystemid:
            return False
        bp = sm.StartService('michelle').GetBallpark()
        if not bp:
            return False
        godmaSM = self.godma.GetStateManager()
        for slimItem in bp.slimItems.itervalues():
            if slimItem.groupID == const.groupShipMaintenanceArray or slimItem.categoryID == const.categoryShip and godmaSM.GetType(slimItem.typeID).hasShipMaintenanceBay:
                otherBall = bp.GetBall(slimItem.itemID)
                if otherBall:
                    if otherBall.surfaceDist < useRange:
                        return True

        return False

    def ImFleetLeaderOrCommander(self):
        return sm.GetService('fleet').IsBoss() or session.fleetrole in (const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr)

    def ImFleetCommander(self):
        return session.fleetrole in (const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr)

    def CheckImFleetLeaderOrBoss(self):
        return sm.GetService('fleet').IsBoss() or session.fleetrole == const.fleetRoleLeader

    def CheckImFleetLeader(self):
        return session.fleetrole == const.fleetRoleLeader

    def CheckImWingCmdr(self):
        return session.fleetrole == const.fleetRoleWingCmdr

    def CheckImSquadCmdr(self):
        return session.fleetrole == const.fleetRoleSquadCmdr

    def FleetMenu(self, charID, unparsed = True):

        def ParsedMaybe(menuEntries):
            if unparsed:
                return menuEntries
            else:
                return self.ParseMenu(menuEntries, None)

        if session.fleetid is None:
            return []
        fleetSvc = sm.GetService('fleet')
        vivox = sm.GetService('vivox')
        members = fleetSvc.GetMembers()
        shipItem = util.SlimItemFromCharID(charID)
        bp = sm.StartService('michelle').GetBallpark()
        otherBall = bp and shipItem and bp.GetBall(shipItem.itemID) or None
        me = members[session.charid]
        checkIfImLeader = self.ImFleetLeaderOrCommander()
        checkIfImWingCommanderOrHigher = self.CheckImFleetLeaderOrBoss() or self.CheckImWingCmdr()
        member = members.get(charID)
        char = cfg.eveowners.Get(charID)
        if member is None:
            menuEntries = [[uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (int(char.Type()),
               charID,
               0,
               None,
               None)]]
            return menuEntries
        isTitan = False
        isJumpDrive = False
        if session.solarsystemid and session.shipid:
            ship = sm.StartService('godma').GetItem(session.shipid)
            if ship.canJump:
                isJumpDrive = True
            if ship.groupID in [const.groupTitan, const.groupBlackOps]:
                isTitan = True
        checkImCreator = bool(me.job & const.fleetJobCreator)
        checkIfMe = charID == session.charid
        checkIfInSpace = self.GetCheckInSpace()
        checkIfActiveBeacon = fleetSvc.HasActiveBeacon(charID)
        checkIsTitan = isTitan
        checkIsJumpDrive = isJumpDrive
        checkBoosterFleet = bool(member.roleBooster == const.fleetBoosterFleet)
        checkBoosterWing = bool(member.roleBooster == const.fleetBoosterWing)
        checkBoosterSquad = bool(member.roleBooster == const.fleetBoosterSquad)
        checkBoosterAny = bool(checkBoosterFleet or checkBoosterWing or checkBoosterSquad)
        checkSubordinate = self.CheckImFleetLeaderOrBoss() or me.role == const.fleetRoleWingCmdr and member.wingID == me.wingID or me.role == const.fleetRoleSquadCmdr and member.squadID == me.squadID
        checkBoss = member.job & const.fleetJobCreator
        checkWingCommander = member.role == const.fleetRoleWingCmdr
        checkFleetCommander = member.role == const.fleetRoleLeader
        checkBoosterSubordinate = checkBoosterAny and (checkImCreator or me.role == const.fleetRoleLeader) or (checkBoosterWing or checkBoosterSquad) and me.role == const.fleetRoleWingCmdr or checkBoosterSquad and me.role == const.fleetRoleSquadCmdr
        checkBoosterSubordinateOrSelf = checkBoosterSubordinate or checkBoosterAny and checkIfMe
        checkIfFavorite = fleetSvc.IsFavorite(charID)
        checkIfIsBubble = shipItem is not None
        checkMultiSelection = False
        dist = sys.maxint
        if otherBall:
            dist = max(0, otherBall.surfaceDist)
        checkWarpDist = dist > const.minWarpDistance
        checkIsVoiceEnabled = sm.StartService('vivox').Enabled()
        checkCanMute = fleetSvc.CanIMuteOrUnmuteCharInMyChannel(charID) > 0
        checkCanUnmute = fleetSvc.CanIMuteOrUnmuteCharInMyChannel(charID) < 0
        checkIfPrivateMuted = charID in vivox.GetMutedParticipants()
        if session.fleetrole == const.fleetRoleWingCmdr:
            muteString = uiutil.MenuLabel('UI/Fleet/MuteFromWingChannel')
            unmuteString = uiutil.MenuLabel('UI/Fleet/UnmuteFromWingChannel')
        elif session.fleetrole == const.fleetRoleSquadCmdr:
            muteString = uiutil.MenuLabel('UI/Fleet/MuteFromSquadChannel')
            unmuteString = uiutil.MenuLabel('UI/Fleet/UnmuteFromSquadChannel')
        else:
            muteString = uiutil.MenuLabel('UI/Fleet/MuteFromFleetChannel')
            unmuteString = uiutil.MenuLabel('UI/Fleet/UnmuteFromFleetChannel')
        defaultWarpDist = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
        menuEntries = []
        if not checkMultiSelection:
            menuEntries += [[uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (int(char.Type()),
               charID,
               0,
               None,
               None)]]
        menuEntries += [None]
        if checkSubordinate and not checkIfMe and not checkBoss:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/KickFleetMember'), self.ConfirmMenu(lambda *x: fleetSvc.KickMember(charID))]]
        if not checkIfMe and checkImCreator:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/MakeFleetLeader'), fleetSvc.MakeLeader, (charID,)]]
        if not checkMultiSelection and not checkIfFavorite and not checkIfMe:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/AddPilotToWatchlist'), fleetSvc.AddFavorite, ([charID],)]]
        if self.CheckImFleetLeaderOrBoss() and not checkBoosterAny and checkSubordinate:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/SetFleetBooster'), fleetSvc.SetBooster, (charID, const.fleetBoosterFleet)]]
        if checkIfImWingCommanderOrHigher and not checkBoosterAny and not checkFleetCommander and checkSubordinate:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/SetWingBooster'), fleetSvc.SetBooster, (charID, const.fleetBoosterWing)]]
        if not checkBoosterAny and not checkWingCommander and not checkFleetCommander and checkSubordinate:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/SetSquadBooster'), fleetSvc.SetBooster, (charID, const.fleetBoosterSquad)]]
        if checkBoosterSubordinateOrSelf:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/RevokeFleetBooster'), fleetSvc.SetBooster, (charID, const.fleetBoosterNone)]]
        if checkIfImLeader and checkIfMe:
            label = uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastTravelToMe')
            menuEntries += [[label, sm.GetService('fleet').SendBroadcast_TravelTo, (session.solarsystemid2,)]]
        if checkWarpDist and checkIfInSpace and not checkIfMe:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpToMember'), self.WarpToMember, (charID, float(defaultWarpDist))]]
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpToMemberSubmenuOption'), self.WarpToMenu(self.WarpToMember, charID)]]
            if self.CheckImFleetLeader():
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpFleetToMember'), self.WarpFleetToMember, (charID, float(defaultWarpDist))]]
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpFleetToMember'), self.WarpToMenu(self.WarpFleetToMember, charID)]]
            if self.CheckImWingCmdr():
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpWingToMember'), self.WarpFleetToMember, (charID, float(defaultWarpDist))]]
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpWingToMember'), self.WarpToMenu(self.WarpFleetToMember, charID)]]
            if self.CheckImSquadCmdr():
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpSquadToMember'), self.WarpFleetToMember, (charID, float(defaultWarpDist))]]
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpSquadToMember'), self.WarpToMenu(self.WarpFleetToMember, charID)]]
        if not checkIfIsBubble and checkIfInSpace and not checkIfMe and checkIfActiveBeacon:
            if checkIsJumpDrive:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/JumpToFleetMember'), self.JumpToMember, (charID,)]]
            if checkIsTitan:
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/BridgeToMember'), self.BridgeToMember, (charID,)]]
        if not checkMultiSelection and checkIfFavorite:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/RemovePilotFromWatchlist'), fleetSvc.RemoveFavorite, (charID,)]]
        if not checkIfMe and checkCanMute:
            menuEntries += [[muteString, fleetSvc.AddToVoiceMute, (charID,)]]
        if checkCanUnmute:
            menuEntries += [[unmuteString, fleetSvc.ExcludeFromVoiceMute, (charID,)]]
        if checkIsVoiceEnabled and not checkIfPrivateMuted and not checkIfMe:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/MuteFleetMemberVoice'), vivox.MuteParticipantForMe, (charID, 1)]]
        if checkIsVoiceEnabled and checkIfPrivateMuted and not checkIfMe:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetUnmuteVoice'), vivox.MuteParticipantForMe, (charID, 0)]]
        if checkIfMe:
            menuEntries += [[uiutil.MenuLabel('UI/Fleet/LeaveMyFleet'), self.ConfirmMenu(fleetSvc.LeaveFleet)]]
        menuEntries = ParsedMaybe(menuEntries)
        moveMenu = self.GetFleetMemberMenu2(charID, fleetSvc.MoveMember, True)
        if moveMenu:
            menuEntries.extend([[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/MoveFleetMember'), moveMenu]])
        return menuEntries

    def FleetInviteMenu(self, charID):
        return self.GetFleetMemberMenu2(charID, lambda *args: self.DoInviteToFleet(*args))

    def GetFleetMemberMenu2(self, charID, callback, isMove = False):
        wings = sm.GetService('fleet').GetWings()
        members = sm.GetService('fleet').GetMembers()
        ret = evefleet.menu.MemberMenu(charID, wings, members, callback, sm.GetService('fleet').GetOptions().isFreeMove, isMove, uiutil.MenuLabel, localization.GetByLabel).Get()
        return ret

    def DoInviteToFleet(self, charID, wingID, squadID, role):
        sm.GetService('fleet').Invite(charID, wingID, squadID, role)

    def CorpMemberMenu(self, charID, multi = 0):
        checkInSameCorp = charID in sm.StartService('corp').GetMemberIDs()
        checkIAmDirector = const.corpRoleDirector & session.corprole == const.corpRoleDirector
        checkICanKickThem = session.charid == charID or const.corpRoleDirector & session.corprole == const.corpRoleDirector
        checkIAmCEO = sm.StartService('corp').UserIsCEO()
        checkIAmAccountant = const.corpRoleAccountant & session.corprole == const.corpRoleAccountant
        checkIBlockRoles = sm.StartService('corp').UserBlocksRoles()
        checkIsMe = session.charid == charID
        checkIAmPersonnelMgr = const.corpRolePersonnelManager & session.corprole == const.corpRolePersonnelManager
        checkIsNPC = util.IsNPC(charID)
        checkIAmInNPCCorp = util.IsNPC(session.corpid)
        checkMultiSelection = bool(multi)
        checkIsDustChar = util.IsDustCharacter(charID)
        quitCorpMenu = [[uiutil.MenuLabel('UI/Corporations/Common/RemoveAllCorpRoles'), sm.StartService('corp').RemoveAllRoles, ()], [uiutil.MenuLabel('UI/Corporations/Common/ConfirmQuitCorp'), sm.StartService('corp').KickOut, (charID,)]]
        allowRolesMenu = [[uiutil.MenuLabel('UI/Corporations/Common/ConfirmAllowCorpRoles'), sm.StartService('corp').UpdateMember, (session.charid,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           None,
           0)]]
        expelMenu = [[uiutil.MenuLabel('UI/Corporations/Common/ConfirmExpelMember'), sm.StartService('corp').KickOut, (charID,)]]
        resignMenu = [[uiutil.MenuLabel('UI/Corporations/Common/ConfirmResignAsCEO'), sm.StartService('corp').ResignFromCEO, ()]]
        menuEntries = [None]
        if not checkMultiSelection and checkInSameCorp:
            if not checkIAmDirector:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/ViewCorpMemberDetails'), self.ShowCorpMemberDetails, (charID,)]]
            else:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/EditCorpMember'), self.ShowCorpMemberDetails, (charID,)]]
            if checkIsMe and checkIBlockRoles:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/AllowCorpRoles'), allowRolesMenu]]
        if not checkMultiSelection and checkIAmAccountant and not checkIsNPC and not checkIsDustChar:
            menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/TransferCorpCash'), sm.StartService('wallet').TransferMoney, (session.corpid,
               None,
               charID,
               None)]]
        if checkInSameCorp:
            if checkICanKickThem and checkIsMe and not checkIAmInNPCCorp and not checkIAmCEO:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/QuitCorp'), quitCorpMenu]]
            if checkICanKickThem and not checkIsMe:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/ExpelCorpMember'), expelMenu]]
            if checkIsMe and checkIAmCEO:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/ResignAsCEO'), resignMenu]]
            if checkIAmPersonnelMgr and not checkIsNPC and not checkIsDustChar:
                menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/AwardCorpMemberDecoration'), self.AwardDecoration, [charID]]]
        if checkIAmPersonnelMgr and not checkInSameCorp and not checkMultiSelection:
            menuEntries += [[uiutil.MenuLabel('UI/Corporations/Common/SendCorpInvite'), sm.StartService('corp').InviteToJoinCorp, (charID,)]]
        return menuEntries

    def AwardDecoration(self, charIDs):
        return menuFunctions.AwardDecoration(charIDs)

    def ShowCorpMemberDetails(self, charID):
        form.CorpMembers().MemberDetails(charID)

    def __GetInviteMenu(self, charID, submenu = None):

        def Invite(charID, channelID):
            sm.StartService('LSC').Invite(charID, channelID)

        inviteMenu = []
        submenus = {}
        for channel in sm.StartService('LSC').GetChannels():
            if sm.StartService('LSC').IsJoined(channel.channelID) and type(channel.channelID) == types.IntType:
                members = sm.StartService('LSC').GetMembers(channel.channelID)
                if members and charID not in members:
                    t = chat.GetDisplayName(channel.channelID).split('\\')
                    if submenu and len(t) == 2 and submenu == t[0] or not submenu and len(t) != 2:
                        inviteMenu += [[t[-1], Invite, (charID, channel.channelID)]]
                    elif not submenu and len(t) == 2:
                        submenus[t[0]] = 1

        for each in submenus.iterkeys():
            inviteMenu += [[each, ('isDynamic', self.__GetInviteMenu, (charID, each))]]

        inviteMenu.sort()
        inviteMenu = [[uiutil.MenuLabel('UI/Chat/StartConversation'), Invite, (charID, None)]] + inviteMenu
        return inviteMenu

    def SlashCmd(self, cmd):
        return devFunctions.SlashCmd(cmd)

    def SlashCmdTr(self, cmd):
        return devFunctions.SlashCmdTr(cmd)

    def GetGMTypeMenu(self, typeID, itemID = None, divs = False, unload = False):
        if not session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            return []

        def _wrapMulti(command, what = None, maxValue = 2147483647):
            if uicore.uilib.Key(uiconst.VK_SHIFT):
                if not what:
                    what = command.split(' ', 1)[0]
                result = uix.QtyPopup(maxvalue=maxValue, minvalue=1, caption=what, label=localization.GetByLabel('UI/Common/Quantity'), hint='')
                if result:
                    qty = result['qty']
                else:
                    return
            else:
                qty = 1
            return sm.GetService('slash').SlashCmd(command % qty)

        item = cfg.invtypes.Get(typeID)
        cat = item.categoryID
        if unload:
            if type(itemID) is tuple:
                for row in self.invCache.GetInventoryFromId(itemID[0]).ListHardwareModules():
                    if row.flagID == itemID[1]:
                        itemID = row.itemID
                        break
                else:
                    itemID = None

            else:
                charge = self.godma.GetItem(itemID)
                if charge.categoryID == const.categoryCharge:
                    for row in self.invCache.GetInventoryFromId(charge.locationID).ListHardwareModules():
                        if row.flagID == charge.flagID and row.itemID != itemID:
                            itemID = row.itemID
                            break
                    else:
                        itemID = None

        gm = []
        if divs:
            gm.append(None)
        if session.role & (service.ROLE_WORLDMOD | service.ROLE_SPAWN):
            if not session.stationid:
                if cat == const.categoryShip:
                    gm.append(('WM: /Spawn this type', lambda *x: _wrapMulti('/spawnN %%d 4000 %d' % item.typeID, '/Spawn', 50)))
                    gm.append(('WM: /Unspawn this ship', lambda *x: sm.RemoteSvc('slash').SlashCmd('/unspawn %d' % itemID)))
                if cat == const.categoryEntity:
                    gm.append(('WM: /Entity deploy this type', lambda *x: _wrapMulti('/entity deploy %%d %d' % item.typeID, '/Entity', 100)))
        if item.typeID != const.typeSolarSystem and cat not in [const.categoryStation, const.categoryOwner]:
            if session.role & service.ROLE_WORLDMOD:
                gm.append(('WM: /create this type', lambda *x: _wrapMulti('/create %d %%d' % item.typeID)))
            gm.append(('GM: /load me this type', lambda *x: _wrapMulti('/load me %d %%d' % item.typeID)))
            typeObj = cfg.invtypes.Get(item.typeID)
            graphicID = typeObj.graphicID
            animations = typeObj.AnimationStates()
            graphicFile = util.GraphicFile(graphicID)
            if graphicFile is '':
                graphicFile = None
            gm.append(('res', [('typeID: ' + str(item.typeID), blue.pyos.SetClipboardData, (str(item.typeID),)), ('graphicID: ' + str(graphicID), blue.pyos.SetClipboardData, (str(graphicID),)), ('graphicFile: ' + str(graphicFile), blue.pyos.SetClipboardData, (str(graphicFile),))]))
        if cfg.IsFittableCategory(cat):
            gm.append(('GM: /fit me this type', lambda *x: _wrapMulti('/loop %%d /fit me %d' % item.typeID, '/Fit', 8)))
            if unload:
                if itemID:
                    gm.append(('GM: /unload me this item', lambda *x: sm.RemoteSvc('slash').SlashCmd('/unload me %d' % itemID)))
                gm.append(('GM: /unload me this type', lambda *x: sm.RemoteSvc('slash').SlashCmd('/unload me %d' % item.typeID)))
                if itemID and self.godma.GetItem(itemID).damage:
                    gm.append(('GM: Repair this module', lambda *x: sm.RemoteSvc('slash').SlashCmd('/heal %d' % itemID)))
        if itemID:
            gm.append(('GM: Inspect Attributes', self.InspectAttributes, (itemID, typeID)))
        if session.role & service.ROLE_PROGRAMMER:
            gm.append(('PROG: Modify Attributes', ('isDynamic', self.AttributeMenu, (itemID, typeID))))
        if divs:
            gm.append(None)
        return gm

    def InspectAttributes(self, itemID, typeID):
        form.AttributeInspector.Open(itemID=itemID, typeID=typeID)

    def NPCInfoMenu(self, item):
        return devFunctions.NPCInfoMenu(item)

    def AttributeMenu(self, itemID, typeID):
        return devFunctions.AttributeMenu(itemID, typeID)

    def SetDogmaAttribute(self, itemID, attrName, actualValue):
        return devFunctions.SetDogmaAttribute(itemID, attrName, actualValue)

    def GagPopup(self, charID, numMinutes):
        return devFunctions.GagPopup(charID, numMinutes)

    def ReportISKSpammer(self, charID, channelID):
        return devFunctions.ReportISKSpammer(charID, channelID)

    def BanIskSpammer(self, charID):
        return devFunctions.BanIskSpammer(charID)

    def GagIskSpammer(self, charID):
        return devFunctions.GagIskSpammer(charID)

    def GetFromESP(self, action):
        """
            Constructs an URL using the connected to server info and the action parameter.
        """
        return devFunctions.GetFromESP(action)

    def GetGMMenu(self, itemID = None, slimItem = None, charID = None, invItem = None, mapItem = None, typeID = None):
        if not session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            if charID and session.role & service.ROLE_LEGIONEER:
                return [('Gag ISK Spammer', self.GagIskSpammer, (charID,))]
            return []
        gm = [(str(itemID or charID), blue.pyos.SetClipboardData, (str(itemID or charID),))]
        if mapItem and not slimItem:
            gm.append(('TR me here!', self.SlashCmdTr, ('/tr me ' + str(mapItem.itemID),)))
            gm.append(None)
        elif charID:
            gm.append(('TR me to %s' % cfg.eveowners.Get(charID).name, self.SlashCmdTr, ('/tr me ' + str(charID),)))
            gm.append(None)
        elif slimItem:
            gm.append(('TR me here!', self.SlashCmdTr, ('/tr me ' + str(itemID),)))
            gm.append(None)
        elif itemID:
            gm.append(('TR me here!', self.SlashCmdTr, ('/tr me ' + str(itemID),)))
            gm.append(None)
        if invItem:
            gm += [('Copy ID/Qty', self.CopyItemIDAndMaybeQuantityToClipboard, (invItem,))]
            typeText = 'copy typeID (%s)' % invItem.typeID
            gm += [(typeText, blue.pyos.SetClipboardData, (str(invItem.typeID),))]
            gm.append(('Edit', self.GetAdamEditType, [invItem.typeID]))
            gm.append(None)
            typeID = invItem.typeID
            gm.append(('typeID: ' + str(typeID) + ' (%s)' % cfg.invtypes.Get(typeID).name, blue.pyos.SetClipboardData, (str(typeID),)))
            invType = cfg.invtypes.Get(typeID)
            group = invType.groupID
            gm.append(('groupID: ' + str(group) + ' (%s)' % invType.Group().name, blue.pyos.SetClipboardData, (str(group),)))
            category = invType.categoryID
            categoryName = cfg.invcategories.Get(category).name
            gm.append(('categID: ' + str(category) + ' (%s)' % categoryName, blue.pyos.SetClipboardData, (str(category),)))
            graphic = invType.Graphic()
            if graphic is not None:
                gm.append(('graphicID: ' + str(invType.graphicID), blue.pyos.SetClipboardData, (str(invType.graphicID),)))
                if hasattr(graphic, 'graphicFile'):
                    gm.append(('graphicFile: ' + str(graphic.graphicFile), blue.pyos.SetClipboardData, (str(graphic.graphicFile),)))
        if charID and not util.IsNPC(charID):
            action = 'gm/character.py?action=Character&characterID=' + str(charID)
            gm.append(('Show in ESP', self.GetFromESP, (action,)))
            gm.append(None)
            gm.append(('Gag ISK Spammer', self.GagIskSpammer, (charID,)))
            gm.append(('Ban ISK Spammer', self.BanIskSpammer, (charID,)))
            action = 'gm/users.py?action=BanUserByCharacterID&characterID=' + str(charID)
            gm.append(('Ban User (ESP)', self.GetFromESP, (action,)))
            gm += [('Gag User', [('30 minutes', self.GagPopup, (charID, 30)),
               ('1 hour', self.GagPopup, (charID, 60)),
               ('6 hours', self.GagPopup, (charID, 360)),
               ('24 hours', self.GagPopup, (charID, 1440)),
               None,
               ('Ungag', lambda *x: self.SlashCmd('/ungag %s' % charID))])]
        gm.append(None)
        item = slimItem or invItem
        if item:
            if item.categoryID == const.categoryShip and (item.singleton or not session.stationid):
                import dna
                if item.ownerID in [session.corpid, session.charid] or session.role & service.ROLE_WORLDMOD:
                    try:
                        menu = dna.Ship().ImportFromShip(shipID=item.itemID, ownerID=item.ownerID, deferred=True).GetMenuInline(spiffy=False, fit=item.itemID != session.shipid)
                        gm.append(('Copycat', menu))
                    except RuntimeError:
                        pass

                gm += [('/Online modules', lambda shipID = item.itemID: self.SlashCmd('/online %d' % shipID))]
            gm += self.GetGMTypeMenu(item.typeID, itemID=item.itemID)
            if getattr(slimItem, 'categoryID', None) == const.categoryEntity or getattr(slimItem, 'groupID', None) == const.groupWreck:
                gm.append(('NPC Info', ('isDynamic', self.NPCInfoMenu, (item,))))
            gm.append(None)
        elif typeID:
            gm += self.GetGMTypeMenu(typeID)
        if session.role & service.ROLE_CONTENT:
            if slimItem:
                if getattr(slimItem, 'dunObjectID', None) != None:
                    if not sm.StartService('scenario').IsSelected(itemID):
                        gm.append(('Add to Selection', sm.StartService('scenario').AddSelected, (itemID,)))
                    else:
                        gm.append(('Remove from Selection', sm.StartService('scenario').RemoveSelected, (itemID,)))
        if slimItem:
            itemID = slimItem.itemID
            typeObj = cfg.invtypes.Get(item.typeID)
            graphicID = typeObj.graphicID
            if slimItem.categoryID == const.categoryStation and slimItem.itemID:
                npcStation = cfg.mapSolarSystemContentCache.npcStations.get(itemID, None)
                if npcStation:
                    graphicID = npcStation.graphicID
            animations = typeObj.AnimationStates()
            graphicFile = util.GraphicFile(graphicID)
            if graphicFile is '':
                graphicFile = None
            g = cfg.graphics.GetIfExists(graphicID)
            raceName = getattr(g, 'sofRaceName', None)
            sofDNA = None
            with util.ExceptionEater('SOF DNA unavailable - FSD needs rebuilding?'):
                sofDNA = gfxutils.BuildSOFDNAFromTypeID(slimItem.typeID)
            ball = sm.StartService('michelle').GetBallpark().GetBall(slimItem.itemID)
            subMenu = self.GetGMStructureStateMenu(itemID, slimItem, charID, invItem, mapItem)
            if len(subMenu) > 0:
                gm += [('Change State', subMenu)]
            gm += self.GetGMBallsAndBoxesMenu(itemID, slimItem, charID, invItem, mapItem)
            currentGeoLODstr = 'INVALID'
            currentTexLODmenu = []
            if ball is not None:
                if hasattr(ball, 'model'):
                    if ball.model is not None:
                        if hasattr(ball.model, 'mesh'):
                            if ball.model.mesh is not None:
                                currentGeoLODstr = ball.model.mesh.GetGeometryResPath()
                                paramLst = ball.model.mesh.Find('trinity.TriTexture2DParameter')
                                currentTexLODstr = {}
                                for param in paramLst:
                                    currentTexLODstr[param.resourcePath.lower()] = param.name

                                for param in currentTexLODstr.iterkeys():
                                    currentTexLODmenu.append((param, blue.pyos.SetClipboardData, (str(param),)))

                                currentTexLODmenu.append(None)
                                paramLst = ball.model.mesh.Find('trinity.Tr2Texture2dLodParameter')
                                currentTexLODstr = {}
                                for param in paramLst:
                                    currentTexLODstr[param.GetResourcePath().lower()] = param.name

                                for param in currentTexLODstr.iterkeys():
                                    currentTexLODmenu.append((param, blue.pyos.SetClipboardData, (str(param),)))

            gm.append(None)
            gm.append(('charID: ' + self.GetOwnerLabel(slimItem.charID), blue.pyos.SetClipboardData, (str(slimItem.charID),)))
            gm.append(('ownerID: ' + self.GetOwnerLabel(slimItem.ownerID), blue.pyos.SetClipboardData, (str(slimItem.ownerID),)))
            gm.append(('corpID: ' + self.GetOwnerLabel(slimItem.corpID), blue.pyos.SetClipboardData, (str(slimItem.corpID),)))
            gm.append(('allianceID: ' + self.GetOwnerLabel(slimItem.allianceID), blue.pyos.SetClipboardData, (str(slimItem.allianceID),)))
            if hasattr(slimItem, 'districtID'):
                gm.append(('districtID: ' + str(slimItem.districtID), blue.pyos.SetClipboardData, (str(slimItem.districtID),)))
            gm.append(None)
            gm.append(('typeID: ' + str(slimItem.typeID) + ' (%s)' % cfg.invtypes.Get(slimItem.typeID).name, blue.pyos.SetClipboardData, (str(slimItem.typeID),)))
            gm.append(('groupID: ' + str(slimItem.groupID) + ' (%s)' % cfg.invgroups.Get(slimItem.groupID).name, blue.pyos.SetClipboardData, (str(slimItem.groupID),)))
            gm.append(('categID: ' + str(slimItem.categoryID) + ' (%s)' % cfg.invcategories.Get(slimItem.categoryID).name, blue.pyos.SetClipboardData, (str(slimItem.categoryID),)))
            gm.append(('res', [('graphicID: ' + str(graphicID), blue.pyos.SetClipboardData, (str(graphicID),)),
              ('graphicFile: ' + str(graphicFile), blue.pyos.SetClipboardData, (str(graphicFile),)),
              ('SOF DNA: ' + str(sofDNA), blue.pyos.SetClipboardData, (str(sofDNA),)),
              ('race: ' + str(raceName), blue.pyos.SetClipboardData, (str(raceName),)),
              ('current geo LOD: ' + currentGeoLODstr, blue.pyos.SetClipboardData, (currentGeoLODstr,)),
              ('current tex LODs', currentTexLODmenu),
              ('state machines: ' + str(animations), blue.pyos.SetClipboardData, (str(animations),)),
              ('Save red file', self.SaveRedFile, (ball, graphicFile)),
              modelDebugFunctions.GetGMModelInfoMenuItem(itemID)]))
            if slimItem.groupID == const.groupPlanet:
                if ball is not None:
                    if ball.typeID == const.typePlanetEarthlike:
                        gm.append(('DUST', [('current: ' + str(len(ball.districts)), blue.pyos.SetClipboardData, (str(len(ball.districts)),)),
                          None,
                          ('+1 district', self.DustAddDistricts, (1, ball)),
                          ('+10 district', self.DustAddDistricts, (10, ball)),
                          ('+50 district', self.DustAddDistricts, (50, ball)),
                          ('clear districts', self.DustClearDistricts, (ball,)),
                          None,
                          ('start battles', self.DustEnableBattles, (True, ball)),
                          ('stop battles', self.DustEnableBattles, (False, ball)),
                          None,
                          ('BOOM!', self.DustStartExplosions, (True, ball)),
                          ('Stop BOOM!', self.DustStartExplosions, (False, ball))]))
            if slimItem.groupID == const.groupSatellite:
                gm.append(('Orbital Strike', [('Enable District', sm.GetService('district').EnableDistrict, (slimItem.districtID, True)),
                  ('Disable District', sm.GetService('district').DisableDistrict, ()),
                  ('Request Strike', sm.RemoteSvc('slash').SlashCmd, ('/osrequest ' + str(slimItem.districtID),)),
                  ('Cancel Strike', sm.RemoteSvc('slash').SlashCmd, ('/oscancel ' + str(slimItem.districtID),))]))
            gm.append(None)
            gm.append(('Copy Coordinates', self.CopyCoordinates, (itemID,)))
            gm.append(None)
            try:
                state = slimItem.orbitalState
                if state in (entities.STATE_UNANCHORING,
                 entities.STATE_ONLINING,
                 entities.STATE_ANCHORING,
                 entities.STATE_OPERATING,
                 entities.STATE_OFFLINING,
                 entities.STATE_SHIELD_REINFORCE):
                    stateText = localization.GetByLabel(pos.DISPLAY_NAMES[pos.Entity2DB(state)])
                    gm.append(('End orbital state change (%s)' % stateText, self.CompleteOrbitalStateChange, (itemID,)))
                elif state == entities.STATE_ANCHORED:
                    upgradeType = sm.GetService('godma').GetTypeAttribute2(slimItem.typeID, const.attributeConstructionType)
                    if upgradeType is not None:
                        gm.append(('Upgrade to %s' % cfg.invtypes.Get(upgradeType).typeName, self.GMUpgradeOrbital, (itemID,)))
                gm.append(('GM: Take Control', self.TakeOrbitalOwnership, (itemID, slimItem.planetID)))
            except ValueError:
                pass

            if HasBehaviorComponent(slimItem.typeID):
                gm.extend(behavior.GetBehaviorGMMenu(slimItem))
        gm.append(None)
        dict = {'CHARID': charID,
         'ITEMID': itemID,
         'ID': charID or itemID}
        for i in range(20):
            item = prefs.GetValue('gmmenuslash%d' % i, None)
            if item:
                for k, v in dict.iteritems():
                    if ' %s ' % k in item and v:
                        item = item.replace(k, str(v))
                        break
                else:
                    continue

                gm.append((item, sm.RemoteSvc('slash').SlashCmd, (item,)))

        return gm

    def SaveRedFile(self, ball, graphicFile):
        return modelDebugFunctions.SaveRedFile(ball, graphicFile)

    def DustAddDistricts(self, count, ball):
        for each in range(0, count):
            randomCenterNormal = geo2.Vec3Normalize((random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)))
            ball.AddDistrict('unique' + str(len(ball.districts)), randomCenterNormal, 0.1, False)

    def DustClearDistricts(self, ball):
        ball.DelAllDistricts()

    def DustEnableBattles(self, enable, ball):
        for key, value in ball.districts.iteritems():
            ball.EnableBattleForDistrict(key, enable)

    def DustStartExplosions(self, enable, ball):

        def TriggerExplosions():
            while True:
                for key, value in ball.districts.iteritems():
                    availableFX = [planet.ORBBOMB_IMPACT_FX_EM, planet.ORBBOMB_IMPACT_FX_HYBRID, planet.ORBBOMB_IMPACT_FX_LASER]
                    ball.AddExplosion(key, random.choice(availableFX), 0.4)

                blue.synchro.SleepSim(10000.0)

        if enable:
            if getattr(self, 'triggerExplosionThreadObj', None) is None:
                self.triggerExplosionThreadObj = uthread.new(TriggerExplosions)
        elif getattr(self, 'triggerExplosionThreadObj', None) is not None:
            self.triggerExplosionThreadObj.kill()
            self.triggerExplosionThreadObj = None

    def GetGMStructureStateMenu(self, itemID = None, slimItem = None, charID = None, invItem = None, mapItem = None):
        """Make the menu for the Structure change state menu. """
        subMenu = []
        if hasattr(slimItem, 'posState') and slimItem.posState is not None:
            currentState = slimItem.posState
            if currentState not in pos.ONLINE_STABLE_STATES:
                if currentState == pos.STRUCTURE_ANCHORED:
                    subMenu.append(('Online', sm.RemoteSvc('slash').SlashCmd, ('/pos online ' + str(itemID),)))
                    subMenu.append(('Unanchor', sm.RemoteSvc('slash').SlashCmd, ('/pos unanchor ' + str(itemID),)))
                elif currentState == pos.STRUCTURE_UNANCHORED:
                    subMenu.append(('Anchor', sm.RemoteSvc('slash').SlashCmd, ('/pos anchor ' + str(itemID),)))
            else:
                if getattr(slimItem, 'posTimestamp', None) is not None:
                    subMenu.append(('Complete State', sm.RemoteSvc('slash').SlashCmd, ('/sov complete ' + str(itemID),)))
                subMenu.append(('Offline', sm.RemoteSvc('slash').SlashCmd, ('/pos offline ' + str(itemID),)))
        if hasattr(slimItem, 'structureState') and slimItem.structureState != None and slimItem.structureState in [pos.STRUCTURE_SHIELD_REINFORCE, pos.STRUCTURE_ARMOR_REINFORCE]:
            subMenu.append(('Complete State', sm.RemoteSvc('slash').SlashCmd, ('/sov complete ' + str(itemID),)))
        return subMenu

    def GetGMBallsAndBoxesMenu(self, itemID = None, slimItem = None, charID = None, invItem = None, mapItem = None):
        return modelDebugFunctions.GetGMBallsAndBoxesMenu(itemID, slimItem, charID, invItem, mapItem)

    def GetOwnerLabel(self, ownerID):
        return menuFunctions.GetOwnerLabel(ownerID)

    def GetAdamEditType(self, typeID):
        uthread.new(self.ClickURL, 'http://adam:50001/gd/type.py?action=EditTypeDogmaForm&typeID=%s' % typeID)

    def ClickURL(self, url, *args):
        blue.os.ShellExecute(url)

    def GetWarpOptions(self, FleetWarpToMethod, WarpToMethod, itemId):
        warptoLabel = movementFunctions.DefaultWarpToLabel()
        defaultWarpDist = self.GetDefaultActionDistance('WarpTo')
        ret = [(warptoLabel, WarpToMethod, (itemId, defaultWarpDist)), (uiutil.MenuLabel('UI/Inflight/Submenus/WarpToWithin'), self.WarpToMenu(WarpToMethod, itemId))]
        if self.CheckImFleetLeader():
            ret.extend([(uiutil.MenuLabel('UI/Fleet/WarpFleet'), FleetWarpToMethod, (itemId, float(defaultWarpDist))), (uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpFleetToWithin'), self.WarpToMenu(FleetWarpToMethod, itemId))])
        elif self.CheckImWingCmdr():
            ret.extend([(uiutil.MenuLabel('UI/Fleet/WarpWing'), FleetWarpToMethod, (itemId, float(defaultWarpDist))), (uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpWingToWithin'), self.WarpToMenu(FleetWarpToMethod, itemId))])
        elif self.CheckImSquadCmdr():
            ret.extend([(uiutil.MenuLabel('UI/Fleet/WarpSquad'), FleetWarpToMethod, (itemId, float(defaultWarpDist))), (uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpSquadToWithin'), self.WarpToMenu(FleetWarpToMethod, itemId))])
        return ret

    def SolarsystemScanMenu(self, scanResultID):
        WarpToMethod = self.WarpToScanResult
        FleetWarpToMethod = self.WarpFleetToScanResult
        itemId = scanResultID
        return self.GetWarpOptions(FleetWarpToMethod, WarpToMethod, itemId)

    def WarpToScanResult(self, scanResultID, minRange = None):
        self._WarpXToScanResult(scanResultID, minRange)

    def WarpFleetToScanResult(self, scanResultID, minRange = None):
        self._WarpXToScanResult(scanResultID, minRange, fleet=True)

    def _WarpXToScanResult(self, scanResultID, minRange = None, fleet = False):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            itemID = sm.GetService('sensorSuite').GetCosmicAnomalyItemIDFromTargetID(scanResultID)
            if itemID is None:
                subject, subjectID = 'scan', scanResultID
            else:
                subject, subjectID = 'item', itemID
            bp.CmdWarpToStuff(subject, subjectID, minRange=minRange, fleet=fleet)
            sm.StartService('space').WarpDestination(celestialID=scanResultID)

    def GetCelestialMenuForSelectedItem(self, itemID, ignoreShipConfig = True):
        if isinstance(itemID, list):
            myData = itemID[0]
        else:
            myData = (itemID,
             None,
             None,
             0,
             None,
             None,
             None)
        myMenu = self._CelestialMenu(myData, ignoreTypeCheck=True, ignoreShipConfig=ignoreShipConfig, ignoreMarketDetails=True)
        return myMenu

    def IsItemDead(self, ballPark, itemID):
        ball = ballPark.GetBall(itemID)
        return not ball or ball.isMoribund

    @telemetry.ZONE_METHOD
    def CelestialMenu(self, itemID, mapItem = None, slimItem = None, noTrace = 0, typeID = None, parentID = None, bookmark = None, itemIDs = [], ignoreTypeCheck = 0, ignoreDroneMenu = 0, filterFunc = None, hint = None, ignoreMarketDetails = 1, ignoreShipConfig = True):
        """
        To serve all inflight-, map- and bookmarkitems
        """
        if type(itemID) == list:
            menus = []
            for data in itemID:
                m = self._CelestialMenu(data, ignoreTypeCheck, ignoreDroneMenu, filterFunc, hint, ignoreMarketDetails, len(itemID) > 1, ignoreShipConfig=ignoreShipConfig)
                menus.append(m)

            return self.MergeMenus(menus)
        else:
            ret = self._CelestialMenu((itemID,
             mapItem,
             slimItem,
             noTrace,
             typeID,
             parentID,
             bookmark), ignoreTypeCheck, ignoreDroneMenu, filterFunc, hint, ignoreMarketDetails)
            return self.MergeMenus([ret])

    @telemetry.ZONE_METHOD
    def _CelestialMenu(self, data, ignoreTypeCheck = 0, ignoreDroneMenu = 0, filterFunc = None, hint = None, ignoreMarketDetails = 1, multi = 0, ignoreShipConfig = False):
        """
            if getReasons is True, this function gets the reasons the option is not available, and returns a tuple with the menu options and
            the dictionary with the reasons.
            This is only used for the selected items window and the action buttons.
        
        """
        itemID, mapItem, slimItem, noTrace, typeID, parentID, bookmark = data
        categoryID = None
        bp = sm.StartService('michelle').GetBallpark()
        fleetSvc = sm.GetService('fleet')
        if bp:
            slimItem = slimItem or bp.GetInvItem(itemID)
        if slimItem:
            typeID = slimItem.typeID
            parentID = sm.StartService('map').GetParent(itemID) or session.solarsystemid
            categoryID = slimItem.categoryID
        mapItemID = None
        if bookmark:
            typeID = bookmark.typeID
            parentID = bookmark.locationID
            itemID = itemID or bookmark.locationID
        else:
            mapItem = mapItem or sm.StartService('map').GetItem(itemID)
            if mapItem:
                typeID = mapItem.typeID
                parentID = getattr(mapItem, 'locationID', None) or const.locationUniverse
                if typeID == const.groupSolarSystem:
                    mapItemID = mapItem.itemID
        if typeID is None or categoryID and categoryID == const.categoryCharge:
            return []
        invType = cfg.invtypes.Get(typeID)
        groupID = invType.groupID
        invGroup = cfg.invgroups.Get(groupID)
        groupName = invGroup.name
        categoryID = categoryID or invGroup.categoryID
        godmaSM = self.godma.GetStateManager()
        shipItem = self.godma.GetStateManager().GetItem(session.shipid)
        isMyShip = itemID == session.shipid
        otherBall = bp and bp.GetBall(itemID) or None
        ownBall = bp and bp.GetBall(session.shipid) or None
        dist = otherBall and max(0, otherBall.surfaceDist)
        otherCharID = slimItem and (slimItem.charID or slimItem.ownerID) or None
        if parentID is None and groupID == const.groupStation and itemID:
            tmp = sm.StartService('ui').GetStation(itemID)
            if tmp is not None:
                parentID = tmp.solarSystemID
        dist = self.FindDist(dist, bookmark, ownBall, bp)
        checkMultiCategs1 = categoryID in (const.categoryEntity, const.categoryDrone, const.categoryShip)
        niceRange = dist and util.FmtDist(dist) or localization.GetByLabel('UI/Inflight/NoDistanceAvailable')
        checkIsMine = bool(slimItem) and slimItem.ownerID == session.charid
        checkIsMyCorps = bool(slimItem) and slimItem.ownerID == session.corpid
        checkIsMineOrCorps = bool(slimItem) and (slimItem.ownerID == session.charid or slimItem.ownerID == session.corpid)
        checkIsMineOrCorpsOrAlliances = bool(slimItem) and (slimItem.ownerID == session.charid or slimItem.ownerID == session.corpid or session.allianceid and slimItem.allianceID == session.allianceid)
        checkIsFree = bool(otherBall) and otherBall.isFree
        checkBP = bool(bp)
        checkMyShip = isMyShip
        checkInCapsule = itemID == session.shipid and groupID == const.groupCapsule
        checkShipBusy = bool(otherBall) and otherBall.isInteractive
        checkInSpace = bool(session.solarsystemid)
        checkInSystem = dist is not None and (bp and itemID in bp.balls or parentID == session.solarsystemid)
        checkIsObserving = sm.GetService('target').IsObserving()
        checkStation = groupID == const.groupStation
        checkPlanetCustomsOffice = groupID == const.groupPlanetaryCustomsOffices
        checkPlanet = groupID == const.groupPlanet
        checkMoon = groupID == const.groupMoon
        checkThisPlanetOpen = sm.GetService('viewState').IsViewActive('planet') and sm.GetService('planetUI').planetID == itemID
        checkStargate = bool(slimItem) and groupID == const.groupStargate
        checkWarpgate = groupID == const.groupWarpGate
        checkWormhole = groupID == const.groupWormhole
        checkControlTower = groupID == const.groupControlTower
        checkSentry = groupID in (const.groupMobileMissileSentry, const.groupMobileProjectileSentry, const.groupMobileHybridSentry)
        checkLaserSentry = groupID == const.groupMobileLaserSentry
        checkShipMaintainer = groupID == const.groupShipMaintenanceArray
        checkCorpHangarArray = groupID == const.groupCorporateHangarArray
        checkAssemblyArray = groupID == const.groupAssemblyArray
        checkMobileLaboratory = groupID == const.groupMobileLaboratory
        checkSilo = groupID == const.groupSilo
        checkReactor = groupID == const.groupMobileReactor
        checkContainer = groupID in self.containerGroups
        checkCynoField = typeID == const.typeCynosuralFieldI
        checkConstructionPf = groupID in (const.groupConstructionPlatform, const.groupStationUpgradePlatform, const.groupStationImprovementPlatform)
        checkShip = categoryID == const.categoryShip
        checkSpacePig = (groupID == const.groupAgentsinSpace or groupID == const.groupDestructibleAgentsInSpace) and bool(sm.StartService('godma').GetType(typeID).agentID)
        checkIfShipMAShip = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).hasShipMaintenanceBay)
        checkIfShipFHShip = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).hasFleetHangars)
        checkIfShipCloneShip = slimItem and bool(godmaSM.GetType(typeID).canReceiveCloneJumps)
        checkSolarSystem = groupID == const.groupSolarSystem
        checkWreck = groupID == const.groupWreck
        checkSpewContainer = groupID == const.groupSpewContainer
        checkZeroSecSpace = checkInSpace and sm.StartService('map').GetSecurityClass(session.solarsystemid) == const.securityClassZeroSec
        checkIfShipDroneBay = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).droneCapacity or IsModularShip(typeID))
        checkIfShipFuelBay = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialFuelBayCapacity)
        checkIfShipOreHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialOreHoldCapacity)
        checkIfShipGasHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialGasHoldCapacity)
        checkIfShipMineralHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialMineralHoldCapacity)
        checkIfShipSalvageHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialSalvageHoldCapacity)
        checkIfShipShipHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialShipHoldCapacity)
        checkIfShipSmallShipHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialSmallShipHoldCapacity)
        checkIfShipMediumShipHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialMediumShipHoldCapacity)
        checkIfShipLargeShipHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialLargeShipHoldCapacity)
        checkIfShipIndustrialShipHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialIndustrialShipHoldCapacity)
        checkIfShipAmmoHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialAmmoHoldCapacity)
        checkIfShipCommandCenterHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialCommandCenterHoldCapacity)
        checkIfShipPlanetaryCommoditiesHold = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialPlanetaryCommoditiesHoldCapacity)
        checkIfShipHasQuafeBay = slimItem and categoryID == const.categoryShip and bool(godmaSM.GetType(typeID).specialQuafeHoldCapacity)
        checkIfMaterialsHold = slimItem and bool(godmaSM.GetType(typeID).specialMaterialBayCapacity)
        checkIfCanUpgrade = slimItem and categoryID == const.categoryOrbital and slimItem.orbitalState == entities.STATE_ANCHORED
        maxTransferDistance = max(getattr(godmaSM.GetType(typeID), 'maxOperationalDistance', 0), const.maxCargoContainerTransferDistance)
        maxLookatDist = sm.GetService('camera').maxLookatRange
        checkWarpDist = dist is not None and dist > const.minWarpDistance
        checkApproachDist = dist is not None and dist < const.minWarpDistance
        checkAlignTo = dist is not None and dist > const.minWarpDistance
        checkJumpDist = dist is not None and dist < const.maxStargateJumpingDistance
        checkWormholeDist = dist is not None and dist < const.maxWormholeEnterDistance
        checkTransferDist = dist is not None and dist < maxTransferDistance
        checkConfigDist = dist is not None and dist < const.maxConfigureDistance
        checkLookatDist = dist is not None and (dist < maxLookatDist or checkIsObserving)
        checkTargetingRange = dist is not None and shipItem is not None and shipItem and dist < shipItem.maxTargetRange
        checkSpacePigDist = dist is not None and dist < sm.StartService('godma').GetType(typeID).agentCommRange
        checkDistNone = dist is None
        if not checkTransferDist or not checkConfigDist:
            if bp and bp.IsShipInRangeOfStructureControlTower(session.shipid, itemID):
                checkTransferDist = True
                checkConfigDist = True
        checkWarpActive = ownBall and ownBall.mode == destiny.DSTBALL_WARP
        checkJumpThrough = slimItem and sm.GetService('fleet').CanJumpThrough(slimItem)
        checkWreckViewed = checkWreck and sm.GetService('wreck').IsViewedWreck(itemID)
        checkFleet = bool(session.fleetid)
        checkIfImCommander = self.ImFleetCommander()
        checkEnemySpotted = sm.GetService('fleet').CurrentFleetBroadcastOnItem(itemID, state.gbEnemySpotted)
        checkHasMarketGroup = cfg.invtypes.Get(typeID).marketGroupID is not None and not ignoreMarketDetails
        checkIsPublished = cfg.invtypes.Get(typeID).published
        checkMultiSelection = bool(multi)
        checkIfLandmark = itemID and itemID < 0
        checkIfAgentBookmark = bookmark and getattr(bookmark, 'agentID', 0) and hasattr(bookmark, 'locationNumber')
        checkIfReadonlyBookmark = bookmark and type(getattr(bookmark, 'bookmarkID', 0)) == types.TupleType
        checkIsStationManager = session.corprole & const.corpRoleStationManager == const.corpRoleStationManager
        menuEntries = MenuList()
        defaultWarpDist = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
        m = MenuList()
        if bp and IsShipWithinFittingRange(cfg.spaceComponentStaticData, shipItem, slimItem, bp):
            menuEntries.extend(fitting.GetFittingMenu(uicore.cmd.OpenFitting))
        if groupID == const.groupOrbitalTarget:
            return [[uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (typeID,
               itemID,
               0,
               None,
               parentID)]]
        if bookmark:
            checkBookmarkWarpTo = dist is not None and (itemID == session.solarsystemid or parentID == session.solarsystemid)
            checkBookmarkDeadspace = bool(getattr(bookmark, 'deadspace', 0))
            if slimItem:
                if not checkMultiSelection:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (slimItem.typeID,
                       slimItem.itemID,
                       0,
                       None,
                       None)]]
            if checkInSpace and not checkWarpActive:
                if checkInSystem and checkApproachDist:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/ApproachLocationActionGroup'), movementFunctions.ApproachLocation, (bookmark,)]]
                if checkBookmarkWarpTo and checkWarpDist:
                    if not checkBookmarkDeadspace:
                        label = uiutil.MenuLabel('UI/Inflight/WarpToBookmarkWithinDistance', {'warpToDistance': util.FmtDist(float(defaultWarpDist))})
                        menuEntries += [[label, movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist))]]
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/WarpToBookmark'), self.WarpToMenu(movementFunctions.WarpToBookmark, bookmark)]]
                        if checkFleet:
                            if self.CheckImFleetLeader():
                                label = uiutil.MenuLabel('UI/Fleet/WarpFleetToLocationWithinDistance', {'warpToDistance': util.FmtDist(float(defaultWarpDist))})
                                menuEntries += [[label, movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist), True)]]
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpFleetToWithin'), self.WarpToMenu(movementFunctions.WarpFleetToBookmark, bookmark)]]
                            if self.CheckImWingCmdr():
                                label = uiutil.MenuLabel('UI/Fleet/WarpWingToLocationWithinDistance', {'warpToDistance': util.FmtDist(float(defaultWarpDist))})
                                menuEntries += [[label, movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist), True)]]
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpWingToWithin'), self.WarpToMenu(movementFunctions.WarpFleetToBookmark, bookmark)]]
                            if self.CheckImSquadCmdr():
                                label = uiutil.MenuLabel('UI/Fleet/WarpSquadToLocationWithinDistance', {'warpToDistance': util.FmtDist(float(defaultWarpDist))})
                                menuEntries += [[label, movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist), True)]]
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpSquadToWithin'), self.WarpToMenu(movementFunctions.WarpFleetToBookmark, bookmark)]]
                    if checkBookmarkDeadspace:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/WarpToBookmark'), movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist))]]
                        if checkFleet:
                            if self.CheckImFleetLeader():
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpFleetToLocation'), movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist), True)]]
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpFleetToWithin'), self.WarpToMenu(movementFunctions.WarpFleetToBookmark, bookmark)]]
                            if self.CheckImWingCmdr():
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpWingToLocation'), movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist), True)]]
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpWingToWithin'), self.WarpToMenu(movementFunctions.WarpFleetToBookmark, bookmark)]]
                            if self.CheckImSquadCmdr():
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpSquadToLocation'), movementFunctions.WarpToBookmark, (bookmark, float(defaultWarpDist), True)]]
                                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpSquadToWithin'), self.WarpToMenu(movementFunctions.WarpFleetToBookmark, bookmark)]]
            if checkInSystem and not checkMyShip and checkAlignTo and not checkWarpActive and not checkIfAgentBookmark:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/AlignTo'), self.AlignToBookmark, (getattr(bookmark, 'bookmarkID', None),)]]
            if not checkIfAgentBookmark and not checkIfReadonlyBookmark:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/EditBookmark'), sm.GetService('addressbook').EditBookmark, (bookmark,)]]
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/RemoveBookmark'), sm.GetService('addressbook').DeleteBookmarks, ([getattr(bookmark, 'bookmarkID', None)],)]]
            if ignoreTypeCheck or checkStation is True:
                menuEntries += [None]
                if checkBP and checkInSystem and checkStation:
                    if checkWarpActive:
                        self.AddDisabledEntryForWarp(menuEntries, 'UI/Inflight/DockInStation')
                    else:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/DockInStation'), self.Dock, (itemID,)]]
                else:
                    prereqs = [('checkBP', checkBP, True), ('notInSystem', checkInSystem, True), ('notStation', checkStation, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/DockInStation'] = reason
        elif bp and itemID is not None:
            checkBillboard = groupID == const.groupBillboard
            checkStructure = categoryID in (const.categoryStructure, const.categorySovereigntyStructure)
            checkSovStructure = categoryID == const.categorySovereigntyStructure
            checkControlTower = groupID == const.groupControlTower
            checkContainer = groupID in self.containerGroups
            checkMyWreck = groupID == const.groupWreck and bp.HaveLootRight(itemID)
            checkMyCargo = groupID == const.groupCargoContainer and bp.HaveLootRight(itemID)
            checkNotAbandoned = not bp.IsAbandoned(itemID)
            checkCorpHangarArray = groupID == const.groupCorporateHangarArray
            checkPersonalHangar = groupID == const.groupPersonalHangar
            checkAssemblyArray = groupID == const.groupAssemblyArray
            checkMobileLaboratory = groupID == const.groupMobileLaboratory
            checkSilo = groupID == const.groupSilo
            checkConstructionPf = groupID in (const.groupConstructionPlatform, const.groupStationUpgradePlatform, const.groupStationImprovementPlatform)
            checkJumpPortalArray = groupID == const.groupJumpPortalArray
            checkPMA = groupID in (const.groupPlanet, const.groupMoon, const.groupAsteroidBelt)
            checkMultiGroups1 = groupID in (const.groupSecureCargoContainer, const.groupAuditLogSecureContainer)
            checkMultiGroups2 = categoryID == const.categoryDrone or groupID == const.groupBiomass
            checkAnchorDrop = godmaSM.TypeHasEffect(typeID, const.effectAnchorDrop)
            checkAnchorLift = godmaSM.TypeHasEffect(typeID, const.effectAnchorLift)
            checkAutoPilot = bool(sm.StartService('autoPilot').GetState())
            checkCanRename = checkIsMine or bool(checkIsMyCorps and session.corprole & const.corpRoleEquipmentConfig and categoryID != const.categorySovereigntyStructure) or session.role & service.ROLE_WORLDMOD
            checkAnchorable = invGroup.anchorable
            checkRenameable = not (groupID == const.groupStation and godmaSM.GetType(typeID).isPlayerOwnable == 1)
            checkInTargets = itemID in sm.StartService('target').GetTargets()
            checkBeingTargeted = sm.StartService('target').BeingTargeted(itemID)
            checkOrbital = categoryID == const.categoryOrbital
            camera = sm.GetService('sceneManager').GetRegisteredCamera('default')

            def CheckScoopable(shipItem, groupID, categoryID, typeID):
                if groupID == const.groupBiomass or categoryID == const.categoryDrone:
                    return True
                if shipItem is None:
                    return False
                if self.IsItemDead(bp, itemID):
                    return False
                if HasScoopComponent(typeID) and slimItem and IsActiveComponent(bp.componentRegistry, typeID, itemID):
                    return slimItem.ownerID == session.charid
                isAnchorable = checkAnchorable and checkIsFree
                if shipItem.groupID in (const.groupFreighter, const.groupJumpFreighter):
                    if groupID == const.groupFreightContainer:
                        return True
                    if isAnchorable and groupID not in (const.groupCargoContainer, const.groupAuditLogSecureContainer, const.groupSecureCargoContainer):
                        return True
                    return False
                if isAnchorable or groupID in (const.groupCargoContainer, const.groupFreightContainer) and typeID not in (const.typeCargoContainer, const.typePlanetaryLaunchContainer):
                    return True
                return False

            checkScoopable = CheckScoopable(shipItem, groupID, categoryID, typeID)
            checkScoopableSMA = categoryID == const.categoryShip and groupID != const.groupCapsule and not isMyShip and shipItem is not None and shipItem.hasShipMaintenanceBay
            checkKeepRangeGroups = categoryID != const.categoryAsteroid and groupID not in (const.groupHarvestableCloud,
             const.groupMiningDrone,
             const.groupCargoContainer,
             const.groupSecureCargoContainer,
             const.groupAuditLogSecureContainer,
             const.groupStation,
             const.groupStargate,
             const.groupFreightContainer,
             const.groupWreck)
            checkLookingAtItem = bool(sm.GetService('camera').LookingAt() == itemID)
            checkInterest = bool(util.GetAttrs(camera, 'interest', 'translationCurve', 'id') == itemID)
            advancedCamera = bool(gfxsettings.Get(gfxsettings.UI_ADVANCED_CAMERA))
            checkHasConsumables = checkStructure and godmaSM.GetType(typeID).consumptionType != 0
            checkAuditLogSecureContainer = groupID == const.groupAuditLogSecureContainer
            checkShipJumpDrive = slimItem and shipItem is not None and shipItem.canJump
            checkShipJumpPortalGenerator = slimItem and shipItem is not None and shipItem.groupID in [const.groupTitan, const.groupBlackOps] and len([ each for each in godmaSM.GetItem(session.shipid).modules if each.groupID == const.groupJumpPortalGenerator ]) > 0
            structureShipBridge = sm.services['pwn'].GetActiveBridgeForShip(itemID)
            checkShipHasBridge = structureShipBridge is not None
            if structureShipBridge is not None:
                structureShipBridgeLabel = uiutil.MenuLabel('UI/Fleet/JumpThroughToSystem', {'solarsystem': structureShipBridge[0]})
            else:
                structureShipBridgeLabel = uiutil.MenuLabel('UI/Inflight/JumpThroughError')
            keepRangeMenu = self.GetKeepAtRangeMenu(itemID, dist, niceRange)
            orbitMenu = self.GetOrbitMenu(itemID, dist, niceRange)
            if checkEnemySpotted:
                senderID, = checkEnemySpotted
                label = uiutil.MenuLabel('UI/Fleet/FleetSubmenus/BroadCastEnemySpotted', {'character': senderID})
                menuEntries += [[label, ('isDynamic', self.CharacterMenu, (senderID,))]]
            if ignoreTypeCheck or checkShip is True:
                checkCanStoreVessel = shipItem is not None and slimItem is not None and shipItem.groupID != const.groupCapsule and slimItem.itemID != shipItem.itemID
                checkInSameCorp = bool(slimItem) and slimItem.ownerID in sm.StartService('corp').GetMemberIDs()
                checkInSameFleet = bool(slimItem) and session.fleetid and slimItem.ownerID in sm.GetService('fleet').GetMembers()

                @util.Memoized
                def GetShipConfig(shipID):
                    """ Cached for the duration of this menu building per ship. Note that we never get here for our own ships."""
                    return sm.GetService('shipConfig').GetShipConfig(shipID)

                def CanUseShipServices(serviceFlag, ignoreShipConfig):
                    if checkMyShip or checkIsMine:
                        return True
                    if ignoreShipConfig:
                        return False
                    if not (checkInSameCorp or checkInSameFleet):
                        return False
                    config = GetShipConfig(slimItem.itemID)
                    if serviceFlag == const.flagFleetHangar:
                        if config['FleetHangar_AllowCorpAccess'] and checkInSameCorp or config['FleetHangar_AllowFleetAccess'] and checkInSameFleet:
                            return True
                    if serviceFlag == const.flagShipHangar:
                        if config['SMB_AllowCorpAccess'] and checkInSameCorp or config['SMB_AllowFleetAccess'] and checkInSameFleet:
                            return True
                    return False

                if groupID == const.groupCapsule:
                    stopLabelPath = 'UI/Inflight/StopMyCapsule'
                else:
                    stopLabelPath = 'UI/Inflight/StopMyShip'
                stopText = uiutil.MenuLabel(stopLabelPath)
                if checkShip and checkMyShip:
                    menuEntries += [[stopText, self.StopMyShip]]
                else:
                    prereqs = [('checkShip', checkShip, True), ('isNotMyShip', checkMyShip, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable[stopLabelPath] = reason
                        menuEntries.reasonsWhyNotAvailable['UI/Commands/OpenMyCargo'] = reason
                if checkShip and checkIfShipMAShip and CanUseShipServices(const.flagShipHangar, ignoreShipConfig):
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenShipMaintenanceBay'), openFunctions.OpenShipMaintenanceBayShip, (itemID, localization.GetByLabel('UI/Commands/OpenShipMaintenanceBayError'))]]
                if checkShip and checkIfShipFHShip and CanUseShipServices(const.flagFleetHangar, ignoreShipConfig):
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenFleetHangar'), openFunctions.OpenFleetHangar, (itemID,)]]
                if checkShip and checkMyShip and not checkInCapsule:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenCargoHold'), openFunctions.OpenShipHangarCargo, [itemID]]]
                    if checkIfShipDroneBay:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenDroneBay'), openFunctions.OpenDroneBay, [itemID]]]
                    if checkIfShipFuelBay:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenFuelBay'), self.OpenFuelBay, [itemID]]]
                    if checkIfShipOreHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenOreHold'), self.OpenOreHold, [itemID]]]
                    if checkIfShipGasHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenGasHold'), self.OpenGasHold, [itemID]]]
                    if checkIfShipMineralHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenMineralHold'), self.OpenMineralHold, [itemID]]]
                    if checkIfShipSalvageHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenSalvageHold'), self.OpenSalvageHold, [itemID]]]
                    if checkIfShipShipHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenShipHold'), self.OpenShipHold, [itemID]]]
                    if checkIfShipSmallShipHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenSmallShipHold'), self.OpenSmallShipHold, [itemID]]]
                    if checkIfShipMediumShipHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenMediumShipHold'), self.OpenMediumShipHold, [itemID]]]
                    if checkIfShipLargeShipHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenLargeShipHold'), self.OpenLargeShipHold, [itemID]]]
                    if checkIfShipIndustrialShipHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenIndustrialShipHold'), self.OpenIndustrialShipHold, [itemID]]]
                    if checkIfShipAmmoHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenAmmoHold'), self.OpenAmmoHold, [itemID]]]
                    if checkIfShipCommandCenterHold:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenCommandCenterHold'), self.OpenCommandCenterHold, [itemID]]]
                    if checkIfShipPlanetaryCommoditiesHold:
                        menuEntries += [[uiutil.MenuLabel('UI/PI/Common/OpenPlanetaryCommoditiesHold'), self.OpenPlanetaryCommoditiesHold, [itemID]]]
                    if checkIfShipHasQuafeBay:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenQuafeBay'), self.OpenQuafeHold, [itemID]]]
                if checkConfigDist and checkIfShipMAShip and checkCanStoreVessel and CanUseShipServices(const.flagShipHangar, ignoreShipConfig):
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/StoreVesselInSMA'), self.StoreVessel, (itemID, session.shipid)]]
                if checkShip and checkMyShip and checkIfShipCloneShip:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/ConfigureShipCloneFacility'), self.ShipCloneConfig, (itemID,)]]
                if checkShip and checkMyShip and not checkInCapsule and not checkWarpActive:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/EjectFromShip'), self.Eject]]
                else:
                    prereqs = [('checkShip', checkShip, True),
                     ('isNotMyShip', checkMyShip, True),
                     ('inCapsule', checkInCapsule, False),
                     ('inWarp', checkWarpActive, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/EjectFromShip'] = reason
                if checkMyShip and not checkWarpActive:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/ReconnectToLostDrones'), self.ReconnectToDrones]]
                if checkMyShip and not checkWarpActive:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/SafeLogoff'), self.SafeLogoff]]
                if checkMyShip and not checkWarpActive:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/SelfDestructShipOrPod'), self.SelfDestructShip, (itemID,)]]
                else:
                    prereqs = [('isNotMyShip', checkMyShip, True), ('inWarp', checkWarpActive, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/SelfDestructShipOrPod'] = reason
                if checkShip and not checkMyShip and not checkShipBusy and not checkDistNone:
                    if checkWarpActive:
                        self.AddDisabledEntryForWarp(menuEntries, 'UI/Inflight/BoardShip')
                    else:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/BoardShip'), self.Board, (itemID,)]]
                else:
                    prereqs = [('checkShip', checkShip, True), ('isMyShip', checkMyShip, False), ('pilotInShip', checkShipBusy, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/BoardShip'] = reason
                if checkShip and checkMyShip:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/EnterStarbasePassword'), self.EnterPOSPassword]]
                if checkShip and checkMyShip and checkAutoPilot:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/DeactivateAutopilot'), self.ToggleAutopilot, (0,)]]
                else:
                    prereqs = [('checkShip', checkShip, True), ('isNotMyShip', checkMyShip, True), ('autopilotNotActive', checkAutoPilot, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/DeactivateAutopilot'] = reason
                if checkShip and checkMyShip and not checkAutoPilot:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/ActivateAutopilot'), self.ToggleAutopilot, (1,)]]
                else:
                    prereqs = [('checkShip', checkShip, True), ('isNotMyShip', checkMyShip, True), ('autopilotActive', checkAutoPilot, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/ActivateAutopilot'] = reason
                menuEntries += [None]
                if checkMyShip and not checkInCapsule and checkShipJumpDrive:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/Submenus/JumpTo'), ('isDynamic', self.GetHybridBeaconJumpMenu, [])]]
                    if checkShipJumpPortalGenerator:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/Submenus/BridgeTo'), ('isDynamic', self.GetHybridBridgeMenu, [])]]
                if not checkMyShip and checkShipHasBridge:
                    menuEntries += [[structureShipBridgeLabel, self.JumpThroughAlliance, (itemID,)]]
                menuEntries += [None]
                if checkShip and checkIfShipMAShip and (checkInSameCorp or checkInSameFleet):
                    menuEntries += [[uiutil.MenuLabel('UI/Fitting/UseFittingService'), uicore.cmd.OpenFitting, ()]]
            if ignoreTypeCheck or checkPMA is False:
                checkDrone = groupID == const.groupMiningDrone
                menuEntries += [None]
                if checkInSystem and not checkMyShip and not checkPMA and not checkWarpActive:
                    if checkApproachDist:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/ApproachObject'), self.Approach, (itemID, 50)]]
                    else:
                        reason = self.FindReasonNotAvailable([('notInApproachRange', checkApproachDist, True)])
                        if reason:
                            menuEntries.reasonsWhyNotAvailable['UI/Inflight/ApproachObject'] = reason
                    if not checkWarpDist:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/OrbitObject'), orbitMenu]]
                    else:
                        reason = self.FindReasonNotAvailable([('inWarpRange', checkWarpDist, False)])
                        if reason:
                            menuEntries.reasonsWhyNotAvailable['UI/Inflight/OrbitObject'] = reason
                    if not checkDrone and checkKeepRangeGroups and not checkWarpDist:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/Submenus/KeepAtRange'), keepRangeMenu]]
                    else:
                        prereqs = [('cantKeepInRange',
                          checkKeepRangeGroups,
                          True,
                          {'groupName': groupName}), ('inWarpRange', checkWarpDist, False)]
                        reason = self.FindReasonNotAvailable(prereqs)
                        if reason:
                            menuEntries.reasonsWhyNotAvailable['UI/Inflight/Submenus/KeepAtRange'] = reason
                else:
                    prereqs = [('notInSystem', checkInSystem, True),
                     ('isMyShip', checkMyShip, False),
                     ('badGroup',
                      checkPMA,
                      False,
                      {'groupName': groupName}),
                     ('inWarp', checkWarpActive, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/ApproachObject'] = reason
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/OrbitObject'] = reason
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/Submenus/KeepAtRange'] = reason
            warpRange = None
            if checkShip and slimItem and slimItem.charID and checkInSameFleet:
                warpFn = self.WarpToMember
                warpFleetFn = self.WarpFleetToMember
                warpID = slimItem.charID
                warpRange = float(defaultWarpDist)
            else:
                warpFn = movementFunctions.WarpToItem
                warpFleetFn = self.WarpFleet
                warpID = itemID
            validWarpTarget = False
            if checkInSystem and not checkWarpActive and not checkMyShip and checkWarpDist:
                if checkShip and slimItem and slimItem.charID and checkInSameFleet or not checkIsFree:
                    validWarpTarget = True
            if validWarpTarget:
                menuEntries += [[movementFunctions.DefaultWarpToLabel(), warpFn, (warpID, warpRange)]]
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/Submenus/WarpToWithin'), self.WarpToMenu(warpFn, warpID)]]
                if checkFleet:
                    if self.CheckImFleetLeader():
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpFleet'), warpFleetFn, (warpID, float(defaultWarpDist))]]
                    if self.CheckImFleetLeader():
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpFleetToWithin'), self.WarpToMenu(warpFleetFn, warpID)]]
                    if self.CheckImWingCmdr():
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpWing'), warpFleetFn, (warpID, float(defaultWarpDist))]]
                    if self.CheckImWingCmdr():
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpWingToWithin'), self.WarpToMenu(warpFleetFn, warpID)]]
                    if self.CheckImSquadCmdr():
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/WarpSquad'), warpFleetFn, (warpID, float(defaultWarpDist))]]
                    if self.CheckImSquadCmdr():
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/WarpSquadToWithin'), self.WarpToMenu(warpFleetFn, warpID)]]
                    if checkApproachDist:
                        menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastTarget'), sm.GetService('fleet').SendBroadcast_Target, (itemID,)]]
            else:
                prereqs = [('notInSystem', checkInSystem, True),
                 ('inWarp', checkWarpActive, False),
                 ('isMyShip', checkMyShip, False),
                 ('notInWarpRange', checkWarpDist, True),
                 ('cantWarpTo', checkIsFree, False)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable[movementFunctions.DefaultWarpToLabel()[0]] = reason
            if checkInSystem and not checkMyShip:
                if checkAlignTo and not checkWarpActive:
                    if not checkIsFree:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/AlignTo'), self.AlignTo, (itemID,)]]
            if checkInSystem and checkFleet:
                if checkApproachDist and not checkMyShip:
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastTarget'), sm.GetService('fleet').SendBroadcast_Target, (itemID,)]]
                if not checkMultiCategs1:
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastWarpTo'), sm.GetService('fleet').SendBroadcast_WarpTo, (itemID, typeID)]]
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastAlignTo'), sm.GetService('fleet').SendBroadcast_AlignTo, (itemID, typeID)]]
                if checkStargate:
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastJumpTo'), sm.GetService('fleet').SendBroadcast_JumpTo, (itemID, typeID)]]
            if ignoreTypeCheck or checkJumpThrough:
                throughSystemID = sm.GetService('fleet').CanJumpThrough(slimItem)
                menuEntries += [None]
                if checkInSystem and checkJumpDist and not checkWarpActive:
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/JumpThroughToSystem', {'solarsystem': throughSystemID}), self.JumpThroughFleet, (otherCharID, itemID)]]
            if ignoreTypeCheck or checkStation is True:
                menuEntries += [None]
                if checkInSystem and checkStation:
                    if checkWarpActive:
                        self.AddDisabledEntryForWarp(menuEntries, 'UI/Inflight/DockInStation')
                    else:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/DockInStation'), self.Dock, (itemID,)]]
                else:
                    prereqs = [('notInSystem', checkInSystem, True), ('notStation', checkStation, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/DockInStation'] = reason
            if ignoreTypeCheck or checkStargate:
                dests = []
                locs = []
                for each in slimItem.jumps:
                    if each.locationID not in locs:
                        locs.append(each.locationID)
                    if each.toCelestialID not in locs:
                        locs.append(each.toCelestialID)

                if len(locs):
                    cfg.evelocations.Prime(locs)
                for each in slimItem.jumps:
                    name = uiutil.MenuLabel('UI/Menusvc/MenuHints/DestinationNameInSystem', {'destination': each.toCelestialID,
                     'solarsystem': each.locationID})
                    dests.append((name, self.StargateJump, (itemID, each.toCelestialID, each.locationID)))

                if not dests:
                    dests = [('None', None, None)]
                checkSingleJumpDest = len(dests) == 1
                if dests:
                    currentWarpTarget = sm.GetService('space').warpDestinationCache[0]
                    checkInWarpToGate = itemID == currentWarpTarget
                    if checkStargate and checkSingleJumpDest:
                        if not checkWarpActive or checkInWarpToGate:
                            menuEntries += [[uiutil.MenuLabel('UI/Inflight/Jump'), dests[0][1], dests[0][2]]]
                        else:
                            self.AddDisabledEntryForWarp(menuEntries, 'UI/Inflight/Jump')
                    else:
                        prereqs = [('notStargate', checkStargate, True), ('notWithinMaxJumpDist', checkJumpDist, True), ('severalJumpDest', checkSingleJumpDest, True)]
                        reason = self.FindReasonNotAvailable(prereqs)
                        if reason:
                            menuEntries.reasonsWhyNotAvailable['UI/Inflight/Jump'] = reason
                    if checkStargate and checkJumpDist and not checkSingleJumpDest:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/Submenus/JumpTo'), dests]]
                    if dests[0][2]:
                        waypoints = sm.StartService('starmap').GetWaypoints()
                        checkInWaypoints = dests[0][2][2] in waypoints
                        if checkSingleJumpDest and checkStargate and not checkInWaypoints:
                            menuEntries += [[uiutil.MenuLabel('UI/Inflight/AddFirstWaypoint'), sm.StartService('starmap').SetWaypoint, (dests[0][2][2], 0, 1)]]
            if slimItem and (ignoreTypeCheck or checkWarpgate is True):
                checkOneTwo = 1
                if checkWarpgate and checkOneTwo:
                    if checkWarpActive:
                        self.AddDisabledEntryForWarp(menuEntries, 'UI/Inflight/ActivateGate')
                    else:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/ActivateGate'), self.ActivateAccelerationGate, (itemID,)]]
                else:
                    prereqs = [('notWarpGate', checkWarpgate, True), ('severalJumpDest', checkOneTwo, True), ('notWithinMaxJumpDist', checkJumpDist, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/ActivateGate'] = reason
            if slimItem and (ignoreTypeCheck or checkWormhole is True):
                if checkWormhole:
                    if checkWarpActive:
                        self.AddDisabledEntryForWarp(menuEntries, 'UI/Inflight/EnterWormhole')
                    else:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/EnterWormhole'), self.EnterWormhole, (itemID,)]]
                else:
                    prereqs = [('notCloseEnoughToWH', checkWormholeDist, True), ('inWarp', checkWarpActive, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/EnterWormhole'] = reason
            menuEntries += [None]
            if not checkWarpActive and checkLookatDist:
                if not checkLookingAtItem and not checkPlanet and not checkMoon:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/LookAtObject'), sm.GetService('camera').LookAt, (itemID,)]]
                else:
                    prereqs = [('isLookingAtItem', checkLookingAtItem, False)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/LookAtObject'] = reason
                if not checkLookingAtItem and advancedCamera:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/SetAsCameraParent'), self.SetParent, (itemID,)]]
                if not checkInterest and advancedCamera:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/SetAsCameraInterest'), self.SetInterest, (itemID,)]]
            else:
                prereqs = [('inWarp', checkWarpActive, False), ('notInLookingRange', checkLookatDist, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/LookAtObject'] = reason
            if checkLookingAtItem:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/ResetCamera'), sm.GetService('camera').ResetCamera]]
            else:
                reason = self.FindReasonNotAvailable([('notLookingAtItem', checkLookingAtItem, True)])
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/ResetCamera'] = reason
            if ignoreTypeCheck or checkBillboard is True:
                newsURL = 'http://www.eveonline.com/mb2/news.asp'
                if boot.region == 'optic':
                    newsURL = 'http://eve.tiancity.com/client/news.html'
                menuEntries += [None]
                if checkBillboard:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/ReadNews'), uicore.cmd.OpenBrowser, (newsURL, 'browser')]]
            if ignoreTypeCheck or checkContainer is True:
                menuEntries += [None]
                if checkContainer and otherBall:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/OpenCargo'), self.OpenCargo, [itemID]]]
                else:
                    prereqs = [('notWithinMaxTransferRange', checkTransferDist, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Commands/OpenCargo'] = reason
            if ignoreTypeCheck or checkPlanetCustomsOffice is True:
                menuEntries += [None]
                menuEntries += [[uiutil.MenuLabel('UI/PI/Common/AccessCustomOffice'), self.OpenPlanetCustomsOfficeImportWindow, [itemID]]]
            if checkIfMaterialsHold and checkTransferDist and checkIsMineOrCorps and checkIfCanUpgrade and checkInSystem and (groupID == const.groupOrbitalConstructionPlatforms or checkZeroSecSpace):
                menuEntries += [[uiutil.MenuLabel('UI/DustLink/OpenUpgradeHold'), self.OpenUpgradeWindow, [itemID]]]
            if ignoreTypeCheck or checkMyWreck is True or checkMyCargo is True:
                if checkNotAbandoned:
                    if checkMyWreck:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/AbandonWreack'), self.AbandonLoot, [itemID]]]
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/AbandonAllWrecks'), self.AbandonAllLoot, [itemID]]]
                    if checkMyCargo:
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/AbandonCargo'), self.AbandonLoot, [itemID]]]
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/AbandonAllCargo'), self.AbandonAllLoot, [itemID]]]
            if checkScoopable and slimItem is not None:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/ScoopToCargoHold'), self.Scoop, (itemID, typeID)]]
            if checkScoopableSMA:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/ScoopToShipMaintenanceBay'), self.ScoopSMA, (itemID,)]]
            if checkConstructionPf is True:
                menuEntries += [None]
                if checkTransferDist:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSResources'), self.OpenConstructionPlatform, (itemID,)]]
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/BuildConstructionPlatform'), self.BuildConstructionPlatform, (itemID,)]]
            if checkAnchorable and checkConfigDist and checkIsMineOrCorps and checkAnchorDrop and checkIsFree:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AnchorObject'), self.AnchorObject, (itemID, 1)]]
            if checkAnchorable and checkConfigDist and checkIsMineOrCorps and checkAnchorLift and not checkIsFree:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/UnanchorObject'), self.AnchorObject, (itemID, 0)]]
            else:
                prereqs = [('notWithinMaxConfigRange', checkConfigDist, True), ('checkIsMineOrCorps', checkIsMineOrCorps, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/UnanchorObject'] = reason
            structureEntries = []
            if checkJumpPortalArray is True:
                structureBridge = sm.services['pwn'].GetActiveBridgeForStructure(itemID)
                checkStructureHasBridge = structureBridge is not None
                if structureBridge is not None:
                    bridgeJumpLabel = uiutil.MenuLabel('UI/Fleet/JumpThroughToSystem', {'solarsystem': structureBridge[1]})
                    bridgeUnlinkLabel = uiutil.MenuLabel('UI/Inflight/UnbridgeFromSolarsystem', {'solarsystem': structureBridge[1]})
                else:
                    bridgeJumpLabel = uiutil.MenuLabel('UI/Inflight/JumpThroughError')
                    bridgeUnlinkLabel = uiutil.MenuLabel('UI/Inflight/JumpThroughError')
                checkStructureFullyOnline = sm.services['pwn'].IsStructureFullyOnline(itemID)
                checkStructureFullyAnchored = sm.services['pwn'].IsStructureFullyAnchored(itemID)
                if not checkInCapsule and checkIsMyCorps and checkStructureFullyAnchored and not checkStructureHasBridge:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/Submenus/BridgeTo'), self.JumpPortalBridgeMenu, (itemID,)]]
                if not checkInCapsule and checkIsMyCorps and checkStructureHasBridge and checkStructureFullyAnchored:
                    structureEntries += [[bridgeUnlinkLabel, self.UnbridgePortal, (itemID,)]]
                if not checkInCapsule and checkStructureHasBridge and checkStructureFullyOnline and checkJumpDist:
                    structureEntries += [[bridgeJumpLabel, self.JumpThroughPortal, (itemID,)]]
                if checkAnchorable and checkConfigDist and checkIsMineOrCorpsOrAlliances and not checkIsFree and checkTransferDist:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSResources'), self.OpenPOSJumpBridge, (itemID,)]]
            if checkAnchorable and checkConfigDist and checkIsMineOrCorpsOrAlliances and not checkIsFree:
                if checkControlTower:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSFuelBay'), self.OpenPOSFuelBay, (itemID,)]]
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStrontiumBay'), self.OpenStrontiumBay, (itemID,)]]
                if checkSentry:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSAmmo'), self.OpenPOSStructureCharges, (itemID, True)]]
                if checkLaserSentry:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSActiveCrystal'), self.OpenPOSStructureChargeCrystal, (itemID,)]]
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSCrystalStorage'), self.OpenPOSStructureChargesStorage, (itemID,)]]
                checkCanStoreVessel = shipItem is not None and shipItem.groupID != const.groupCapsule
                if checkCanStoreVessel and checkShipMaintainer:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/StoreVesselInSMA'), self.StoreVessel, (itemID, session.shipid)]]
                if checkShipMaintainer:
                    structureEntries += [[uiutil.MenuLabel('UI/Fitting/UseFittingService'), uicore.cmd.OpenFitting, ()]]
                if checkAssemblyArray:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStorage'), self.OpenCorpHangarArray, (itemID,)]]
                if checkMobileLaboratory:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStorage'), self.OpenCorpHangarArray, (itemID,)]]
            if checkAnchorable and not checkIsFree:
                if checkIsMineOrCorps and checkControlTower:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/ManageControlTower'), self.ManageControlTower, (slimItem,)]]
                    if checkConfigDist:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/SetNewPasswordForForceField'), self.EnterForceFieldPassword, (itemID,)]]
                if checkTransferDist and checkIsMineOrCorpsOrAlliances and checkShipMaintainer:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSVessels'), self.OpenPOSShipMaintenanceArray, (itemID,)]]
                    structureEntries += [None]
                else:
                    prereqs = [('notWithinMaxTransferRange', checkTransferDist, True), ('notOwnedByYouOrCorpOrAlliance', checkIsMineOrCorpsOrAlliances, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/POS/AccessPOSVessels'] = reason
                if checkTransferDist and checkIsMineOrCorpsOrAlliances:
                    if checkCorpHangarArray:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStorage'), self.OpenCorpHangarArray, (itemID,)]]
                    if checkPersonalHangar:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStorage'), self.OpenPersonalHangar, (itemID,)]]
                    if checkRenameable and (checkAssemblyArray or checkMobileLaboratory):
                        structureEntries += [[uiutil.MenuLabel('UI/Commands/SetName'), self.SetName, (slimItem,)]]
                    if checkSilo:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStorage'), self.OpenPOSSilo, (itemID,)]]
                    if checkReactor:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSStorage'), self.OpenPOSMobileReactor, (itemID,)]]
                else:
                    prereqs = [('notWithinMaxTransferRange', checkTransferDist, True), ('notOwnedByYouOrCorpOrAlliance', checkIsMineOrCorpsOrAlliances, True)]
                    reason = self.FindReasonNotAvailable(prereqs)
                    if reason:
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/POS/AccessPOSVessels'] = reason
                        menuEntries.reasonsWhyNotAvailable['UI/Inflight/POS/AccessPOSStorage'] = reason
            checkRefineryState = otherBall and not otherBall.isFree
            if groupID == const.groupReprocessingArray and checkRefineryState and checkTransferDist:
                structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSRefinery'), self.OpenPOSRefinery, (itemID,)]]
            else:
                prereqs = [('notWithinMaxTransferRange', checkTransferDist, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/POS/AccessPOSRefinery'] = reason
            if typeID == const.typeCompressionArray and checkTransferDist:
                structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AccessPOSCompression'), self.OpenPOSCompression, (itemID,)]]
            else:
                prereqs = [('notWithinMaxTransferRange', checkTransferDist, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/POS/AccessPOSCompression'] = reason
            if groupID == const.groupControlBunker:
                structureEntries += [[uiutil.MenuLabel('UI/FactionWarfare/IHub/OpenInfrastructureHubPanel'), openFunctions.OpenInfrastructureHubPanel, (itemID,)]]
            if checkStructure is True:
                checkIsSovereigntyClaimMarker = categoryID == const.categorySovereigntyStructure and groupID == const.groupSovereigntyClaimMarkers
                checkIsSovereigntyDisruptor = categoryID == const.categorySovereigntyStructure and groupID == const.groupSovereigntyDisruptionStructures
                checkCanAnchorStructure = bool(slimItem) and self.pwn.CanAnchorStructure(itemID)
                checkCanUnanchorStructure = bool(slimItem) and self.pwn.CanUnanchorStructure(itemID)
                checkCanOnlineStructure = bool(slimItem) and self.pwn.CanOnlineStructure(itemID)
                checkCanOfflineStructure = bool(slimItem) and self.pwn.CanOfflineStructure(itemID)
                checkCanAssumeControlStructure = bool(slimItem) and self.pwn.CanAssumeControlStructure(itemID)
                checkHasControlStructureTarget = bool(slimItem) and self.pwn.GetCurrentTarget(itemID) is not None
                checkHasControl = bool(slimItem) and slimItem.controllerID is not None
                checkHasMyControl = bool(slimItem) and slimItem.controllerID is not None and slimItem.controllerID == session.charid
                checkIsMineOrCorpsOrAlliancesOrOrphaned = bool(slimItem) and (self.pwn.StructureIsOrphan(itemID) or checkIsMineOrCorpsOrAlliances)
                checkIfIAmDirector = session.corprole & const.corpRoleDirector > 0
                checkInfrastructureHub = groupID == const.groupInfrastructureHub
                checkStructureFullyOnline = self.pwn.IsStructureFullyOnline(itemID)
                checkInPlanetMode = sm.GetService('viewState').IsViewActive('planet')
                if checkAnchorable and checkConfigDist and checkStructure:
                    if checkIsMineOrCorpsOrAlliances and checkCanAnchorStructure:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AnchorStructure'), sm.StartService('posAnchor').StartAnchorPosSelect, (itemID,)]]
                    if checkIsMineOrCorpsOrAlliancesOrOrphaned and checkCanUnanchorStructure:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/UnanchorStructure'), self.UnanchorStructure, (itemID,)]]
                    if checkIsMineOrCorpsOrAlliances and checkCanOnlineStructure and not checkIsSovereigntyDisruptor:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/PutStructureOnline'), self.ToggleObjectOnline, (itemID, 1)]]
                    if checkIsMineOrCorpsOrAlliances and checkCanOfflineStructure:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/PutStructureOffline'), self.ToggleObjectOnline, (itemID, 0)]]
                    if checkIsSovereigntyDisruptor and checkCanOnlineStructure:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/PutStructureOnline'), self.ToggleObjectOnline, (itemID, 1)]]
                if checkAnchorable and checkIsMineOrCorpsOrAlliances and checkCanAssumeControlStructure and checkCanOfflineStructure and checkStructure and not checkSovStructure and not checkInPlanetMode:
                    if checkHasMyControl:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/RelinquishPOSControl'), self.pwn.RelinquishStructureControl, (slimItem,)]]
                    if not checkHasControl:
                        structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AssumeStructureControl'), self.pwn.AssumeStructureControl, (slimItem,)]]
                if checkAnchorable and checkIsMineOrCorpsOrAlliances and checkCanAssumeControlStructure and checkStructure and checkHasMyControl and checkHasControlStructureTarget and not checkSovStructure:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/UnlcokSTructureTarget'), self.pwn.UnlockStructureTarget, (itemID,)]]
                if checkAnchorable and checkConfigDist and checkIsMyCorps and checkCanOfflineStructure and checkStructure and checkSovStructure and checkIfIAmDirector and checkIsSovereigntyClaimMarker:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/TransferSovStructureOwnership'), self.TransferOwnership, (itemID,)]]
                if checkConfigDist and checkIsMyCorps and checkInfrastructureHub and checkStructure and checkStructureFullyOnline:
                    structureEntries += [[uiutil.MenuLabel('UI/Menusvc/OpenHubManager'), sm.GetService('sov').GetInfrastructureHubWnd, (itemID,)]]
            if slimItem and (checkOrbital or checkPlanetCustomsOffice):
                checkCanAnchorOrbital = slimItem and slimItem.orbitalState in (None, entities.STATE_UNANCHORED)
                checkIsOrbitalAnchored = slimItem and slimItem.orbitalState == entities.STATE_ANCHORED
                checkCanUnanchorOrbital = slimItem and slimItem.groupID == const.groupOrbitalConstructionPlatforms
                checkCanConfigureOrbital = slimItem and slimItem.groupID != const.groupOrbitalConstructionPlatforms
                checkIfIAmDirector = session.corprole & const.corpRoleDirector > 0
                if checkBP and checkAnchorable and checkCanAnchorOrbital and checkIsMyCorps:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/AnchorObject'), self.AnchorOrbital, (itemID,)]]
                if checkBP and checkAnchorable and checkIsOrbitalAnchored and checkCanUnanchorOrbital and checkIsMyCorps:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/UnanchorObject'), self.UnanchorOrbital, (itemID,)]]
                if checkBP and checkIsOrbitalAnchored and checkCanConfigureOrbital and checkIsMyCorps and checkIsStationManager:
                    structureEntries += [[uiutil.MenuLabel('UI/DustLink/ConfigureOrbital'), self.ConfigureOrbital, (slimItem,)]]
                if checkBP and checkIsOrbitalAnchored and checkCanConfigureOrbital and checkIsMyCorps and checkIfIAmDirector:
                    structureEntries += [[uiutil.MenuLabel('UI/Inflight/POS/TransferSovStructureOwnership'), self.TransferCorporationOwnership, (itemID,)]]
            if len(structureEntries):
                menuEntries.append(None)
                menuEntries.extend(structureEntries)
            if checkWreck:
                if checkWreckViewed:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/MarkWreckNotViewed'), sm.GetService('wreck').MarkViewed, (itemID, False)]]
                else:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/MarkWreckViewed'), sm.GetService('wreck').MarkViewed, (itemID, True)]]
            if slimItem and (ignoreTypeCheck or checkMultiGroups2 is False):
                menuEntries += [None]
                checkIsOrbital = slimItem and util.IsOrbital(slimItem.categoryID)
                if not checkMultiGroups2 and not checkCynoField and not checkIsOrbital and checkCanRename and checkRenameable:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/SetName'), self.SetName, (slimItem,)]]
            tagItemMenu = [(uiutil.MenuLabel('UI/Fleet/FleetTagNumber'), [ (' ' + str(i), self.TagItem, (itemID, str(i))) for i in xrange(10) ])]
            tagItemMenu += [(uiutil.MenuLabel('UI/Fleet/FleetTagLetter'), [ (' ' + str(i), self.TagItem, (itemID, str(i))) for i in 'ABCDEFGHIJXYZ' ])]
            menuEntries += [None]
            if checkInTargets and not checkBeingTargeted:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/UnlockTarget'), self.UnlockTarget, (itemID,)]]
            else:
                prereqs = [('notInTargets', checkInTargets, True), ('beingTargeted', checkBeingTargeted, False)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/UnlockTarget'] = reason
            if not checkMyShip and not checkInTargets and not checkBeingTargeted and not checkPMA and checkTargetingRange:
                menuEntries += [[uiutil.MenuLabel('UI/Inflight/LockTarget'), self.LockTarget, (itemID,)]]
            else:
                prereqs = [('isMyShip', checkMyShip, False),
                 ('alreadyTargeted', checkInTargets, False),
                 ('checkBeingTargeted', checkBeingTargeted, False),
                 ('badGroup',
                  checkPMA,
                  False,
                  {'groupName': groupName}),
                 ('notInTargetingRange', checkTargetingRange, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Inflight/LockTarget'] = reason
            if not checkMyShip and not checkPMA and checkFleet and checkIfImCommander:
                menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetSubmenus/FleetTagItem'), tagItemMenu]]
            if checkSpacePig and checkSpacePigDist:
                menuEntries += [[uiutil.MenuLabel('UI/Chat/StartConversation'), sm.StartService('agents').InteractWith, (sm.StartService('godma').GetType(typeID).agentID,)]]
            else:
                prereqs = [('notSpacePig', checkSpacePig, True)]
                reason = self.FindReasonNotAvailable(prereqs)
                if reason:
                    menuEntries.reasonsWhyNotAvailable['UI/Chat/StartConversation'] = reason
            menuEntries += [None]
            if ignoreTypeCheck or checkMultiGroups1 is True:
                menuEntries += [None]
                if checkMultiGroups1:
                    desc = localization.GetByLabel('UI/Menusvc/SetNewPasswordForContainerDesc')
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/SetNewPasswordForContainer'), self.AskNewContainerPassword, (itemID, desc, const.SCCPasswordTypeGeneral)]]
                if checkAuditLogSecureContainer:
                    desc = localization.GetByLabel('UI/Menusvc/SetNewConfigPasswordForContainer')
                    menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/SetNewConfigPasswordForContainer'), self.AskNewContainerPassword, (itemID, desc, const.SCCPasswordTypeConfig)]]
                if checkIsMineOrCorps:
                    if checkAuditLogSecureContainer:
                        menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ViewLog'), openFunctions.ViewAuditLogForALSC, (itemID,)]]
                    if checkAuditLogSecureContainer:
                        menuEntries += [[uiutil.MenuLabel('UI/Inventory/ItemActions/ConfigureALSContainer'), self.ConfigureALSC, (itemID,)]]
                    if checkAuditLogSecureContainer:
                        menuEntries += [[uiutil.MenuLabel('UI/Commands/RetrievePassword'), self.RetrievePasswordALSC, (itemID,)]]
            if typeID == const.typeMobileShippingUnit and slimItem.timerInfo is None:
                menuEntries += [[uiutil.MenuLabel('UI/Menusvc/AccessShippingUnit'), self.OpenShippingUnitStorage, (itemID,)]]
            if not self.IsItemDead(bp, itemID) and slimItem and IsActiveComponent(bp.componentRegistry, typeID, itemID):
                if HasCargoBayComponent(typeID):
                    if cargobay.IsAccessibleByCharacter(slimItem, session.charid, cfg.spaceComponentStaticData):
                        menuEntries.extend(cargobay.GetMenu(itemID, typeID, self, cfg.spaceComponentStaticData))
                if HasBountyEscrowComponent(typeID):
                    from spacecomponents.common.componentConst import BOUNTYESCROW_CLASS
                    be = bp.componentRegistry.GetComponentForItem(itemID, BOUNTYESCROW_CLASS)
                    menuEntries.extend(be.GetMenu())
                if HasMicroJumpDriverComponent(typeID):
                    menuEntries.extend(microJumpDriver.GetMenu(sm.GetService('michelle'), session.shipid, itemID))
        if checkIsStationManager and (groupID in (const.groupAssemblyArray, const.groupMobileLaboratory) or util.IsStation(itemID)):
            if checkIsMyCorps or util.IsStation(itemID) and sm.StartService('ui').GetStation(itemID).ownerID == session.corpid:
                if sm.GetService('facilitySvc').IsFacility(itemID):
                    menuEntries += [[uiutil.MenuLabel('UI/Menusvc/ConfigureFacility'), self.ConfigureIndustryTax, (itemID, typeID)]]
        checkInTactical = sm.StartService('tactical').CheckIfGroupIDActive(groupID)
        mapTypeID = typeID
        mapFunctionID = itemID
        if groupID in [const.groupSolarSystem, const.groupConstellation, const.groupRegion] and parentID != session.solarsystemid and not (bookmark and bookmark.itemID == bookmark.locationID and bookmark.x and bookmark.y and bookmark.z):
            mapFunctionID = mapItemID or itemID
        elif bookmark:
            if groupID != const.groupStation:
                mapFunctionID = bookmark.locationID
                parentBookmarkItem = sm.GetService('map').GetItem(mapFunctionID)
                if parentBookmarkItem and parentBookmarkItem.groupID == const.groupSolarSystem:
                    mapTypeID = parentBookmarkItem.typeID
        checkSameSolarSystemID = mapFunctionID and mapFunctionID == session.solarsystemid2
        checkCanBeWaypoint = mapTypeID == const.typeSolarSystem or groupID == const.groupStation
        if checkCanBeWaypoint:
            waypoints = sm.GetService('starmap').GetWaypoints()
            checkInWaypoints = mapFunctionID in waypoints
            if util.IsSolarSystem(mapFunctionID):
                solarSystemID = mapFunctionID
            elif util.IsStation(mapFunctionID):
                solarSystemID = cfg.stations.Get(mapFunctionID).solarSystemID
            else:
                log.LogError('mapFunctionID is not a solarsystem or a station, this will probably end up in a strange menu behaviour.', mapFunctionID)
                solarSystemID = mapFunctionID
            checkCanJump = session.solarsystemid is not None and solarSystemID in sm.GetService('map').GetNeighbors(session.solarsystemid)
            menuEntries += [None]
            if checkCanJump:

                def FindStargateAndRequestJump():
                    localStargate = uix.FindLocalStargate(solarSystemID)
                    if localStargate is None:
                        return
                    destSolarSystemID = localStargate.jumps[0].locationID
                    destStargateID = localStargate.jumps[0].toCelestialID
                    localStargateID = localStargate.itemID
                    self.StargateJump(localStargateID, destStargateID, destSolarSystemID)

                menuEntries += [[uiutil.MenuLabel('UI/Inflight/JumpThroughStargate'), FindStargateAndRequestJump, tuple()]]
            if mapFunctionID:
                if not checkSameSolarSystemID:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/SetDestination'), sm.StartService('starmap').SetWaypoint, (mapFunctionID, True)]]
                if checkInWaypoints:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/RemoveWaypoint'), sm.StartService('starmap').ClearWaypoints, (mapFunctionID,)]]
                else:
                    menuEntries += [[uiutil.MenuLabel('UI/Inflight/AddWaypoint'), sm.StartService('starmap').SetWaypoint, (mapFunctionID,)]]
                if checkFleet and (checkSolarSystem or checkStation):
                    menuEntries += [None]
                    menuEntries += [[uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastTravelTo'), sm.GetService('fleet').SendBroadcast_TravelTo, (mapFunctionID,)]]
        elif checkStation and itemID and itemID != session.solarsystemid2:
            menuEntries += [None]
            menuEntries += [[uiutil.MenuLabel('UI/Inflight/SetDestination'), sm.StartService('starmap').SetWaypoint, (itemID, True)]]
        if checkStation:
            menuEntries += [[uiutil.MenuLabel('UI/Menusvc/SetHomeStation'), self.SetHomeStation, (itemID,)]]
        if session.solarsystemid and not checkIfLandmark and groupID not in const.OVERVIEW_IGNORE_GROUPS:
            if checkInTactical == True:
                label = uiutil.MenuLabel('UI/Overview/RemoveGroupFromOverview', {'groupName': groupName})
                changeList = [('groups', groupID, 0)]
                menuEntries += [[label, sm.StartService('overviewPresetSvc').ChangeSettings, (changeList,)]]
            elif checkInTactical == False:
                label = uiutil.MenuLabel('UI/Overview/AddGroupToOverview', {'groupName': groupName})
                changeList = [('groups', groupID, 1)]
                menuEntries += [[label, sm.StartService('overviewPresetSvc').ChangeSettings, (changeList,)]]
        if not bookmark and checkMultiCategs1 is False:
            if groupID == const.groupBeacon:
                beacon = sm.StartService('michelle').GetItem(itemID)
                if beacon and hasattr(beacon, 'dunDescriptionID') and beacon.dunDescriptionID:
                    hint = localization.GetByMessageID(beacon.dunDescriptionID)
            if itemID and parentID:
                menuEntries += [None]
                if not checkMultiCategs1 and not checkIfLandmark:
                    if IsTypeBookmarkable(typeID, cfg.spaceComponentStaticData):
                        menuEntries += [[uiutil.MenuLabel('UI/Inflight/BookmarkLocation'), self.Bookmark, (itemID,
                           typeID,
                           parentID,
                           hint)]]
        if ignoreTypeCheck or mapFunctionID is not None:
            if groupID in [const.groupSolarSystem, const.groupConstellation, const.groupRegion]:
                checkMultiGroups3 = mapFunctionID is not None
                menuEntries += [None]
                if checkMultiGroups3:
                    menuEntries += [[uiutil.MenuLabel('UI/Commands/ShowLocationOnMap'), self.ShowInMap, (mapFunctionID,)]]
                    label = uiutil.MenuLabel('UI/Inflight/ShowInMapBrowser', {'locationType': groupName})
                    menuEntries += [[label, self.ShowInMapBrowser, (mapFunctionID,)]]
                    if mapFunctionID not in self.clientPathfinderService.GetAvoidanceItems():
                        label = uiutil.MenuLabel('UI/Inflight/AvoidLocation', {'theLocation': mapFunctionID,
                         'locationType': groupName})
                        menuEntries += [[label, self.clientPathfinderService.AddAvoidanceItem, (mapFunctionID,)]]
                    else:
                        label = uiutil.MenuLabel('UI/Inflight/StopAvoidingLocation', {'theLocation': mapFunctionID,
                         'locationType': groupName})
                        menuEntries += [[label, self.clientPathfinderService.RemoveAvoidanceItem, (mapFunctionID,)]]
        if checkPlanet and itemID is not None:
            if checkPlanet and not checkThisPlanetOpen:
                openPlanet = lambda planetID: sm.GetService('viewState').ActivateView('planet', planetID=planetID)
                menuEntries += [[uiutil.MenuLabel('UI/PI/Common/ViewInPlanetMode'), openPlanet, (itemID,)]]
            if checkPlanet and checkThisPlanetOpen:
                menuEntries += [[uiutil.MenuLabel('UI/PI/Common/ExitPlanetMode'), sm.GetService('viewState').CloseSecondaryView, ()]]
        if not ignoreDroneMenu and slimItem and categoryID == const.categoryDrone:
            newMenuEntries = MenuList([None])
            for me in self.DroneMenu([[itemID, groupID, slimItem.ownerID]], 1):
                newMenuEntries.extend(me)

            newMenuEntries.extend(menuEntries)
            menuEntries = newMenuEntries
        if not (filterFunc and localization.GetByLabel('UI/Commands/ShowInfo') in filterFunc):
            if not checkMultiSelection:
                menuEntries += [[uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (typeID,
                   itemID,
                   0,
                   None,
                   parentID)]]
        m += self.ParseMenu(menuEntries, filterFunc)
        m.reasonsWhyNotAvailable.update(getattr(menuEntries, 'reasonsWhyNotAvailable', None))
        if groupID == const.groupPlanet:
            moons = self.GetPrimedMoons(itemID)
            if moons:
                m.append((uiutil.MenuLabel('UI/Menusvc/MoonsMenuOption'), ('isDynamic', self.GetMoons, (itemID, moons))))
            if checkBP and checkInSystem:
                customsOfficeIDs = sm.GetService('planetInfo').GetOrbitalsForPlanet(itemID, const.groupPlanetaryCustomsOffices)
                if customsOfficeIDs is not None and len(customsOfficeIDs) > 0:
                    for customsOfficeID in customsOfficeIDs:
                        customsOfficeBall = bp.GetBall(customsOfficeID)
                        if customsOfficeBall:
                            m.append((uiutil.MenuLabel('UI/PI/Common/CustomsOffice'), ('isDynamic', self.GetCustomsOfficeMenu, (customsOfficeID,))))
                        break

            districts = sm.GetService('district').GetDistrictByPlanet(itemID)
            if len(districts):
                m.append((uiutil.MenuLabel('UI/Menusvc/DistrictsMenuOption'), ('isDynamic', self.GetDistricts, (itemID, districts))))
        if checkShip is True and slimItem:
            m += [None] + [(uiutil.MenuLabel('UI/Common/Pilot'), ('isDynamic', self.CharacterMenu, (slimItem.charID or slimItem.ownerID,
                [],
                slimItem.corpID,
                0,
                ['GM / WM Extras'])))]
        if not (filterFunc and 'UI/Inventory/ItemActions/ViewTypesMarketDetails' in filterFunc) and checkHasMarketGroup:
            m += [(uiutil.MenuLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'), self.ShowMarketDetails, (util.KeyVal(typeID=typeID),))]
        if not (filterFunc and 'UI/Inventory/ItemActions/FindInContracts' in filterFunc) and checkIsPublished and not ignoreMarketDetails:
            m += [(uiutil.MenuLabel('UI/Inventory/ItemActions/FindInContracts'), sm.GetService('contracts').FindRelated, (typeID,
               None,
               None,
               None,
               None,
               None))]
        if not (filterFunc and 'GM / WM Extras' in filterFunc) and session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            m.insert(0, ('GM / WM Extras', ('isDynamic', self.GetGMMenu, (itemID,
               slimItem,
               None,
               None,
               mapItem,
               typeID))))
        return m

    def GetKeepAtRangeMenu(self, itemID, dist, currentDistance, *args):
        keepRangeRanges = movementFunctions.GetKeepAtRangeRanges()
        keepRangeMenu = self.GetRangeMenu(itemID=itemID, dist=dist, currentDistance=currentDistance, rangesList=keepRangeRanges, mainFunc=movementFunctions.KeepAtRange, setDefaultFunc=self.SetDefaultKeepAtRangeDist, atCurrentRangeLabel='UI/Inflight/KeepAtCurrentRange', setDefaultLabel='UI/Inflight/Submenus/SetDefaultWarpRange')
        return keepRangeMenu

    def GetOrbitRanges(self, *args):
        orbitRanges = [500,
         1000,
         2500,
         5000,
         7500,
         10000,
         15000,
         20000,
         25000,
         30000]
        return orbitRanges

    def GetOrbitMenu(self, itemID, dist, currentDistance, *args):
        orbitRanges = self.GetOrbitRanges()
        orbitMenu = self.GetRangeMenu(itemID=itemID, dist=dist, currentDistance=currentDistance, rangesList=orbitRanges, mainFunc=movementFunctions.Orbit, setDefaultFunc=self.SetDefaultOrbitDist, atCurrentRangeLabel='UI/Inflight/OrbitAtCurrentRange', setDefaultLabel='UI/Inflight/Submenus/SetDefaultWarpRange')
        return orbitMenu

    def GetRangeMenu(self, itemID, dist, currentDistance, rangesList, mainFunc, setDefaultFunc, atCurrentRangeLabel, setDefaultLabel, *args):
        rangeSubMenu = []
        for eachRange in rangesList:
            fmtRange = util.FmtDist(eachRange)
            rangeSubMenu.append((fmtRange, setDefaultFunc, (eachRange,)))

        rangeMenu = []
        for eachRange in rangesList:
            fmtRange = util.FmtDist(eachRange)
            rangeMenu.append((fmtRange, mainFunc, (itemID, eachRange)))

        rangeMenu += [(uiutil.MenuLabel(atCurrentRangeLabel, {'currentDistance': currentDistance}), mainFunc, (itemID, dist)), None, (uiutil.MenuLabel(setDefaultLabel), rangeSubMenu)]
        return rangeMenu

    def FindDist(self, currentDist, bookmark, ownBall, bp, *args):
        return menuFunctions.FindDist(currentDist, bookmark, ownBall, bp)

    def JumpPortalBridgeMenu(self, itemID):
        l = []
        fromSystem = cfg.evelocations.Get(session.solarsystemid)
        for solarSystemID, structureID in sm.RemoteSvc('map').GetLinkableJumpArrays():
            if solarSystemID == session.solarsystemid:
                continue
            toSystem = cfg.evelocations.Get(solarSystemID)
            dist = uix.GetLightYearDistance(fromSystem, toSystem)
            l.append(('%s<t>%.1f ly' % (toSystem.name, dist), (solarSystemID, structureID)))

        pick = uix.ListWnd(l, 'generic', localization.GetByLabel('UI/Inflight/PickDestination'), isModal=1, scrollHeaders=[localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'), localization.GetByLabel('UI/Common/Distance')])
        if pick:
            remoteSolarSystemID, remoteItemID = pick[1]
            self.BridgePortals(itemID, remoteSolarSystemID, remoteItemID)

    def BridgePortals(self, localItemID, remoteSolarSystemID, remoteItemID):
        posLocation = util.Moniker('posMgr', session.solarsystemid)
        posLocation.InstallJumpBridgeLink(localItemID, remoteSolarSystemID, remoteItemID)

    def UnbridgePortal(self, itemID):
        posLocation = util.Moniker('posMgr', session.solarsystemid)
        posLocation.UninstallJumpBridgeLink(itemID)

    def JumpThroughPortal(self, itemID):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        slim = sm.services['michelle'].GetItem(itemID)
        remoteStructureID = slim.remoteStructureID
        if not remoteStructureID:
            return
        remoteSystemID = slim.remoteSystemID
        self.LogNotice('Jump Through Portal', itemID, remoteStructureID, remoteSystemID)
        sm.StartService('sessionMgr').PerformSessionChange('jump', bp.CmdJumpThroughCorporationStructure, itemID, remoteStructureID, remoteSystemID)

    def GetFuelConsumptionOfJumpBridgeForMyShip(self, fromSystem, toSystem, toStructureType):
        """
            this is used to calculate how much a jump bridge consumes for your current ship for a certain
            distance in Lightyears.
        
            distance * target.JumpDriveConsumptionAmount * target.JumpPortalConsumptionMassFactor * ship.mass
        """
        if not session.shipid:
            return
        myShip = sm.services['godma'].GetItem(session.shipid)
        if myShip is None:
            return
        distance = uix.GetLightYearDistance(fromSystem, toSystem, False)
        if distance is None:
            return
        attrDict = sm.GetService('info').GetAttributeDictForType(toStructureType)
        if const.attributeJumpDriveConsumptionAmount in attrDict:
            consumptionRate = attrDict[const.attributeJumpDriveConsumptionAmount]
        else:
            consumptionRate = 1
        shipMass = getattr(myShip, 'mass', None)
        if shipMass is None:
            shipMass = 1
        if const.attributeJumpPortalConsumptionMassFactor in attrDict:
            massFactor = shipMass * attrDict[const.attributeJumpPortalConsumptionMassFactor]
        return (pos.GetJumpFuelConsumption(distance, consumptionRate, massFactor), attrDict.get(const.attributeJumpDriveConsumptionType, None))

    def GetHybridBeaconJumpMenu(self):
        """
            Returns menus that list fleet member beacons first, then
            structure beacons second, in formats similar to the regular
            alliance beacon format.
        
            Only works for jumps due to the hardcoded function names.
        
            ARGUMENTS:
                None
        
            RETURNS:
                See above. Returns a dummy No Destination option if there are no destinations.
        """
        fleetMenu = []
        allianceMenu = []
        menuSize = 20
        if session.fleetid:
            beacons = sm.GetService('fleet').GetActiveBeacons()
            for charID, beaconArgs in beacons.iteritems():
                solarSystemID, itemID = beaconArgs
                if solarSystemID != session.solarsystemid:
                    character = cfg.eveowners.Get(charID)
                    charName = uiutil.MenuLabel('UI/Menusvc/BeaconLabel', {'name': character.name,
                     'system': solarSystemID})
                    fleetMenu.append((character.name, (charID, beaconArgs, charName)))

            fleetMenu = uiutil.SortListOfTuples(fleetMenu)
        if session.allianceid:
            beacons = sm.RemoteSvc('map').GetAllianceBeacons()
            for solarSystemID, structureID, structureTypeID in beacons:
                if solarSystemID != session.solarsystemid:
                    solarsystem = cfg.evelocations.Get(solarSystemID)
                    invType = cfg.invtypes.Get(structureTypeID)
                    structureName = uiutil.MenuLabel('UI/Menusvc/BeaconLabel', {'name': invType.name,
                     'system': solarSystemID})
                    allianceMenu.append((solarsystem.name, (solarSystemID, structureID, structureName)))

            allianceMenu = uiutil.SortListOfTuples(allianceMenu)
        fullMenu = []
        if len(fleetMenu) > 0:
            for charID, beaconArgs, charName in fleetMenu:
                fullMenu.append([charName, self.JumpToBeaconFleet, (charID, beaconArgs)])

        if len(allianceMenu) > 0:
            if len(fullMenu) > 0:
                fullMenu.append(None)
            am = []
            for solarSystemID, structureID, structureName in allianceMenu:
                systemName = cfg.evelocations.Get(solarSystemID).name
                am.append([structureName,
                 self.JumpToBeaconAlliance,
                 (solarSystemID, structureID),
                 systemName])

            fullMenu.extend(self.CreateSubMenusForLongMenus(am, menuSize, subMenuFunc=self.GetJumpSubMenu))
        if len(fullMenu) > 0:
            return fullMenu
        else:
            return ([uiutil.MenuLabel('UI/Inflight/NoDestination'), self.DoNothing],)

    def OpenCapitalNavigation(self, *args):
        if util.GetActiveShip():
            form.CapitalNav.Open()

    def GetHybridBridgeMenu(self):
        """
            This menu retrieves the Bridge To... menu for jump portal generators.
            It first lists out any fleet members that have active beacons.
            It then lists out any active alliance jump beacons, which it sorts
            into alphabetical categories if there are a lot of them.
        
            In the case that there are both fleet members and alliance beacons, it inserts
            a separator line between the two lists.
        """
        fleetMenu = []
        allianceMenu = []
        menuSize = 20
        if session.fleetid:
            menu = []
            beacons = sm.GetService('fleet').GetActiveBeacons()
            for charID, beaconArgs in beacons.iteritems():
                solarSystemID, itemID = beaconArgs
                if solarSystemID != session.solarsystemid:
                    character = cfg.eveowners.Get(charID)
                    charName = uiutil.MenuLabel('UI/Menusvc/BeaconLabel', {'name': character.name,
                     'system': solarSystemID})
                    menu.append((character.name, (charID, beaconArgs, charName)))

            menu = uiutil.SortListOfTuples(menu)
            fleetMenu = [ (charName, self.BridgeToBeacon, (charID, beaconArgs)) for charID, beaconArgs, charName in menu ]
        if session.allianceid:
            menu = []
            datas = sm.RemoteSvc('map').GetAllianceBeacons()
            for solarSystemID, structureID, structureTypeID in datas:
                if solarSystemID != session.solarsystemid:
                    solarsystem = cfg.evelocations.Get(solarSystemID)
                    invtype = cfg.invtypes.Get(structureTypeID)
                    structureName = uiutil.MenuLabel('UI/Menusvc/BeaconLabel', {'name': invtype.name,
                     'system': solarSystemID})
                    menu.append((solarsystem.name, (solarSystemID, structureID, structureName)))

            menu = uiutil.SortListOfTuples(menu)
            am = [ (structureName,
             self.BridgeToBeaconAlliance,
             (solarSystemID, structureID),
             cfg.evelocations.Get(solarSystemID).name) for solarSystemID, structureID, structureName in menu ]
            allianceMenu = self.CreateSubMenusForLongMenus(am, menuSize, subMenuFunc=self.GetAllianceBeaconSubMenu)
        if len(fleetMenu) > 0 and len(allianceMenu) > 0:
            fleetMenu.append(None)
        fleetMenu.extend(allianceMenu)
        if len(fleetMenu) == 0:
            return ([uiutil.MenuLabel('UI/Inflight/NoDestination'), self.DoNothing],)
        else:
            return fleetMenu

    def CreateSubMenusForLongMenus(self, menuList, menuSize, subMenuFunc, *args):
        allMenuItems = []
        menuListLeft = menuList[:]
        while len(menuListLeft) > menuSize:
            allMenuItems.append(menuListLeft[:menuSize])
            menuListLeft = menuListLeft[menuSize:]

        if menuListLeft:
            allMenuItems.append(menuListLeft)
        if not allMenuItems:
            m = allMenuItems
        if len(allMenuItems) == 1:
            m = subMenuFunc(allMenuItems[0])
        else:
            m = []
            for sub in allMenuItems:
                firstItem = sub[0]
                lastItem = sub[-1]
                if firstItem:
                    firstLetter = firstItem[3][0]
                else:
                    firstLetter = '0'
                if lastItem:
                    lastLetter = lastItem[3][0]
                else:
                    lastLetter = '-1'
                m.append(('%s ... %s' % (firstLetter, lastLetter), ('isDynamic', subMenuFunc, [sub])))

        return m

    def GetJumpSubMenu(self, subMenuItems, *args):
        m = []
        for menuItem in subMenuItems:
            if menuItem is None:
                m.append(None)
                continue
            name, eachFunc, eachArgs, systemName = menuItem
            m.append([name, eachFunc, eachArgs])

        return m

    def GetAllianceBeaconSubMenu(self, structureIDs):
        m = []
        for menuItem in structureIDs:
            if menuItem is None:
                m.append(None)
                continue
            structureName, eachFunc, eachArgs, systemName = menuItem
            solarSystemID, structureID = eachArgs
            m.append([structureName, eachFunc, eachArgs])

        return m

    def RigSlotMenu(self, itemID):
        menu = []
        if itemID == session.shipid:
            ship = sm.GetService('godma').GetItem(session.shipid)
            for module in ship.modules:
                rigslots = [ getattr(const, 'flagRigSlot%s' % i, None) for i in xrange(8) ]
                if module.flagID in rigslots:
                    menu.append([module.name + ' (Slot %s)' % rigslots.index(module.flagID),
                     [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (module.typeID, module.itemID))],
                     None,
                     ()])

        if not menu:
            return []
        return [(uiutil.MenuLabel('UI/Fitting/RigsMenuOption'), menu)]

    def RemoveRig(self, moduleID, shipID):
        if session.stationid:
            self.invCache.GetInventory(const.containerHangar).Add(moduleID, shipID)

    def RigFittingCheck(self, invItem):
        return invItemFunctions.RigFittingCheck(invItem)

    def ConfirmMenu(self, func):
        m = [(uiutil.MenuLabel('UI/Menusvc/ConfirmMenuOption'), func)]
        return m

    def WarpToMenu(self, func, ID):
        ranges = movementFunctions.GetWarpToRanges()
        defMenuWarpOptions = [ (util.FmtDist(rnge), self.SetDefaultWarpToDist, (rnge,)) for rnge in ranges ]
        warpDistMenu = [(uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[0])}), func, (ID, float(ranges[0]))),
         (uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[1])}), func, (ID, float(ranges[1]))),
         (uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[2])}), func, (ID, float(ranges[2]))),
         (uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[3])}), func, (ID, float(ranges[3]))),
         (uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[4])}), func, (ID, float(ranges[4]))),
         (uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[5])}), func, (ID, float(ranges[5]))),
         (uiutil.MenuLabel('UI/Inflight/WarpToWithin', {'distance': util.FmtDist(ranges[6])}), func, (ID, float(ranges[6]))),
         None,
         (uiutil.MenuLabel('UI/Inflight/Submenus/SetDefaultWarpRange'), defMenuWarpOptions)]
        return warpDistMenu

    def MergeMenus(self, menus):
        if not menus:
            return []
        allCaptions = []
        allEntries = []
        allReasons = {}
        for menu in menus:
            i = 0
            if getattr(menu, 'reasonsWhyNotAvailable', {}):
                allReasons.update(menu.reasonsWhyNotAvailable)
            for each in menu:
                if each is None:
                    if len(allEntries) <= i:
                        allEntries.append(None)
                    else:
                        while allEntries[i] != None:
                            i += 1
                            if i == len(allEntries):
                                allEntries.append(None)
                                break

                else:
                    if isinstance(each[0], uiutil.MenuLabel):
                        eachCaption = each[0][0]
                        kwords = each[0][1]
                    else:
                        eachCaption = each[0]
                        kwords = {}
                    if (eachCaption, kwords) not in allCaptions:
                        allEntries.insert(i, each[0])
                        allCaptions.append((eachCaption, kwords))
                i += 1

        menus = filter(None, [ filter(None, each) for each in menus ])
        ret = MenuList()
        ret.reasonsWhyNotAvailable = allReasons
        for eachEntry in allEntries:
            if eachEntry is None:
                ret.append(None)
                continue
            keywords = {}
            if isinstance(eachEntry, uiutil.MenuLabel):
                caption = eachEntry[0]
                keywords = eachEntry[1]
            else:
                caption = eachEntry
            lst = []
            isList = None
            broken = 0
            for menu in menus:
                for entry in menu:
                    entryKeywords = {}
                    if isinstance(eachEntry, uiutil.MenuLabel):
                        entryCaption = entry[0][0]
                        entryKeywords = entry[0][1]
                    else:
                        entryCaption = entry[0]
                    if entryCaption == caption and entryKeywords == keywords:
                        if type(entry[1]) in (str, unicode):
                            ret.append((eachEntry, entry[1]))
                            broken = 1
                            break
                        if type(entry[1]) == tuple and entry[1][0] == 'isDynamic' and len(entry) == 2:
                            ret.append((eachEntry, entry[1]))
                            broken = 1
                            break
                        if isList is None:
                            isList = type(entry[1]) == list
                        if isList != (type(entry[1]) == list):
                            broken = 1
                        elif isList:
                            lst.append(entry[1])
                        else:
                            lst.append(entry[1:])
                        break

                if broken:
                    break

            if not broken:
                if isList:
                    ret.append((eachEntry, self.MergeMenus(lst)))
                elif self.CaptionIsInMultiFunctions(caption) or len(lst) and len(lst[0]) and lst[0][0] in self.multiFunctionFunctions:
                    mergedArgs = []
                    rest = []
                    for entry in lst:
                        _func = entry[0]
                        args = entry[1]
                        rest = entry[2:]
                        if type(args) == type([]):
                            mergedArgs += args
                        else:
                            log.LogWarn('unsupported format of arguments for MergeMenu, function label: ', caption)

                    if isinstance(rest, tuple):
                        rest = list(rest)
                    if mergedArgs:
                        if type(lst[0][0]) == tuple and lst[0][0][0] == 'isDynamic':
                            ret.append([eachEntry, ('isDynamic', lst[0][0][1], lst[0][0][2] + (mergedArgs,))] + rest)
                        else:
                            ret.append([eachEntry, self.CheckLocked, (lst[0][0], mergedArgs)] + rest)
                else:
                    ret.append((eachEntry, self.ExecMulti, lst))

        return ret

    def CaptionIsInMultiFunctions(self, caption):
        if isinstance(caption, uiutil.MenuLabel):
            functionName = caption[0]
        else:
            functionName = caption
        return functionName in self.multiFunctions

    def ExecMulti(self, *actions):
        for each in actions:
            uthread.new(self.ExecAction, each)

    def ExecAction(self, action):
        apply(*action)

    def GetMenuFormItemIDTypeID(self, itemID, typeID, bookmark = None, filterFunc = None, invItem = None, ignoreMarketDetails = 1, abstractInfo = None, **kwargs):
        if typeID is None:
            return []
        elif invItem:
            return self.InvItemMenu(invItem, filterFunc=filterFunc)
        else:
            typeinfo = cfg.invtypes.Get(typeID)
            groupinfo = typeinfo.Group()
            if typeinfo.groupID in (const.groupCharacter,):
                return self.CharacterMenu(itemID, filterFunc=filterFunc, **kwargs)
            elif groupinfo.categoryID in CELESTIAL_MENU_CATEGORIES:
                return self.CelestialMenu(itemID, typeID=typeID, bookmark=bookmark, filterFunc=filterFunc, ignoreMarketDetails=ignoreMarketDetails)
            m = []
            if not (filterFunc and localization.GetByLabel('UI/Commands/ShowInfo') in filterFunc):
                m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (typeID,
                   itemID,
                   0,
                   None,
                   None,
                   abstractInfo))]
            if typeinfo.groupID == const.groupCorporation and util.IsCorporation(itemID) and not util.IsNPC(itemID):
                m += [(uiutil.MenuLabel('UI/Commands/GiveMoney'), sm.StartService('wallet').TransferMoney, (session.charid,
                   None,
                   itemID,
                   None))]
            if industryCommon.IsBlueprintCategory(typeinfo.categoryID) and not (filterFunc and 'UI/Industry/ViewInIndustry' in filterFunc):
                from eve.client.script.ui.shared.industry.industryWnd import Industry
                bpData = abstractInfo.get('bpData', None) if abstractInfo else None
                m += ((localization.GetByLabel('UI/Industry/ViewInIndustry'), Industry.OpenOrShowBlueprint, (None, typeID, bpData)),)
            if typeinfo.groupID in [const.groupCorporation, const.groupAlliance, const.groupFaction]:
                addressBookSvc = sm.GetService('addressbook')
                inAddressbook = addressBookSvc.IsInAddressBook(itemID, 'contact')
                isBlocked = addressBookSvc.IsBlocked(itemID)
                isNPC = util.IsNPC(itemID)
                if inAddressbook:
                    m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/EditContact'), addressBookSvc.AddToPersonalMulti, [itemID, 'contact', True]),)
                    m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveContact'), addressBookSvc.DeleteEntryMulti, [[itemID], 'contact']),)
                else:
                    m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/AddContact'), addressBookSvc.AddToPersonalMulti, [itemID, 'contact']),)
                if not isNPC:
                    if isBlocked:
                        m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/UnblockContact'), addressBookSvc.UnblockOwner, [[itemID]]),)
                    else:
                        m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/BlockContact'), addressBookSvc.BlockOwner, [itemID]),)
                iAmDiplomat = (const.corpRoleDirector | const.corpRoleDiplomat) & session.corprole != 0
                if iAmDiplomat:
                    inCorpAddressbook = addressBookSvc.IsInAddressBook(itemID, 'corpcontact')
                    if inCorpAddressbook:
                        m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/EditCorpContact'), addressBookSvc.AddToPersonalMulti, [itemID, 'corpcontact', True]),)
                        m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveCorpContact'), addressBookSvc.DeleteEntryMulti, [[itemID], 'corpcontact']),)
                    else:
                        m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/AddCorpContact'), addressBookSvc.AddToPersonalMulti, [itemID, 'corpcontact']),)
                    if session.allianceid and not util.IsDustCharacter(itemID):
                        execCorp = sm.GetService('alliance').GetAlliance(session.allianceid).executorCorpID == session.corpid
                        if execCorp:
                            inAllianceAddressbook = addressBookSvc.IsInAddressBook(itemID, 'alliancecontact')
                            if inAllianceAddressbook:
                                m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/EditAllianceContact'), addressBookSvc.AddToPersonalMulti, [itemID, 'alliancecontact', True]),)
                                m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveAllianceContact'), addressBookSvc.DeleteEntryMulti, [[itemID], 'alliancecontact']),)
                            else:
                                m += ((uiutil.MenuLabel('UI/PeopleAndPlaces/AddAllianceContact'), addressBookSvc.AddToPersonalMulti, [itemID, 'alliancecontact']),)
                if session.corprole & const.corpRoleDirector == const.corpRoleDirector and typeinfo.groupID in (const.groupCorporation, const.groupAlliance):
                    if itemID not in (session.corpid, session.allianceid) and not util.IsNPC(itemID):
                        m += ((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Alliances/Rankings/DeclareWar'), self.DeclareWarAgainst, [itemID]),)
            if not (filterFunc and 'UI/Inventory/ItemActions/ViewTypesMarketDetails' in filterFunc) and not ignoreMarketDetails:
                if session.charid:
                    if cfg.invtypes.Get(typeID).marketGroupID is not None:
                        m += [(uiutil.MenuLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'), self.ShowMarketDetails, (util.KeyVal(typeID=typeID),))]
                    if cfg.invtypes.Get(typeID).published:
                        m += [(uiutil.MenuLabel('UI/Inventory/ItemActions/FindInContracts'), sm.GetService('contracts').FindRelated, (typeID,
                           None,
                           None,
                           None,
                           None,
                           None))]
            if typeinfo.categoryID in compareCategories:
                m += [(uiutil.MenuLabel('UI/Compare/CompareButton'), self.CompareType, (typeID,))]
            if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD | service.ROLE_LEGIONEER):
                m.insert(0, ('GM / WM Extras', ('isDynamic', self.GetGMMenu, (None,
                   None,
                   None,
                   None,
                   None,
                   typeID))))
            return m

    def CompareType(self, typeID, *args):
        from eve.client.script.ui.shared.neocom.compare import TypeCompare
        typeWnd = TypeCompare.Open()
        typeWnd.AddTypeID(typeID)

    def ParseMenu(self, menuEntries, filterFunc = None):
        m = MenuList()
        for menuProps in menuEntries:
            if menuProps is None:
                m += [None]
                continue
            label = menuProps[0]
            if len(menuProps) == 3:
                label, func, test = menuProps
                if test == None:
                    log.LogTraceback('Someone still using None as args')
            if filterFunc and label in filterFunc:
                continue
            m += [menuProps]

        m.reasonsWhyNotAvailable = getattr(menuEntries, 'reasonsWhyNotAvailable', {})
        return m

    def GetMenuForSkill(self, typeID):
        m = []
        if session.role & ROLE_GMH == ROLE_GMH:
            m.extend(sm.GetService('info').GetGMGiveSkillMenu(typeID))
        skills = sm.GetService('skills').MySkills(byTypeID=True)
        if skills is not None and typeID in skills:
            skill = sm.StartService('skills').GetMySkillsFromTypeID(typeID)
            if skill is not None:
                m += sm.GetService('skillqueue').GetAddMenuForSkillEntries(skill)
        m += self.GetMenuFormItemIDTypeID(None, typeID, ignoreMarketDetails=0)
        return m

    def GetPrimedMoons(self, planetID):
        if session.solarsystemid2 not in self.primedMoons:
            self.PrimeMoons()
        return self.primedMoons[session.solarsystemid2].get(planetID, [])

    def PrimeMoons(self):
        if session.solarsystemid2 not in self.primedMoons:
            solarsystemitems = sm.GetService('map').GetSolarsystemItems(session.solarsystemid2)
            moonsByPlanets = {}
            for item in solarsystemitems:
                if item.groupID != const.groupMoon:
                    continue
                moonsByPlanets.setdefault(item.orbitID, []).append(item)

            self.primedMoons[session.solarsystemid2] = moonsByPlanets

    def GetMoons(self, planetID, moons, *args):
        if len(moons):
            moons = uiutil.SortListOfTuples([ (moon.orbitIndex, moon) for moon in moons ])
            moonmenu = []
            for moon in moons:
                label = uiutil.MenuLabel('UI/Inflight/Submenus/MoonX', {'moonNumber': moon.orbitIndex})
                moonmenu.append((label, ('isDynamic', self.ExpandMoon, (moon.itemID, moon))))

            return moonmenu
        return [(uiutil.MenuLabel('UI/Menusvc/PlanetHasNoMoons'), self.DoNothing)]

    def GetDistricts(self, planetID, districts, *args):
        menu = []
        for district in districts:
            label = uiutil.MenuLabel('UI/Inflight/Submenus/DistrictX', {'districtIndex': district['index']})
            menu.append((label, ('isDynamic', self.ExpandDistrict, (district,))))

        return menu

    def ExpandDistrict(self, district):
        defaultLabel = movementFunctions.DefaultWarpToLabel()
        defaultDistance = float(self.GetDefaultActionDistance('WarpTo'))
        menu = [(defaultLabel, movementFunctions.WarpToDistrict, (district['districtID'], defaultDistance)), (uiutil.MenuLabel('UI/Inflight/Submenus/WarpToWithin'), self.WarpToMenu(movementFunctions.WarpToDistrict, district['districtID']))]
        if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            menu.insert(0, ('GM / WM Extras', ('isDynamic', self.GetGMMenu, (district['districtID'],
               None,
               None,
               None,
               None))))
        return menu

    def ShowDistrictInfo(self, district):
        pass

    def GetCustomsOfficeMenu(self, customsOfficeID, *args):
        return sm.StartService('menu').CelestialMenu(customsOfficeID)

    def TransferToCargo(self, itemKey):
        structure = self.invCache.GetInventoryFromId(itemKey[0])
        structure.RemoveChargeToCargo(itemKey)

    def DoNothing(self, *args):
        pass

    def ExpandMoon(self, itemID, moon):
        return sm.StartService('menu').CelestialMenu(itemID, moon)

    def Activate(self, slimItem):
        if eve.rookieState and eve.rookieState < 22:
            return
        itemID, groupID, categoryID = slimItem.itemID, slimItem.groupID, slimItem.categoryID
        if itemID == session.shipid:
            myship = sm.StartService('godma').GetItem(session.shipid)
            if myship.groupID == const.groupCapsule:
                bp = sm.StartService('michelle').GetRemotePark()
                if bp is not None:
                    bp.CmdStop()
            else:
                uicore.cmd.OpenCargoHoldOfActiveShip()
            return
        bp = sm.StartService('michelle').GetBallpark()
        if bp:
            ownBall = bp.GetBall(session.shipid)
            otherBall = bp.GetBall(itemID)
            dist = None
            if ownBall and otherBall:
                dist = bp.GetSurfaceDist(ownBall.id, otherBall.id)
            if dist < const.minWarpDistance:
                if groupID == const.groupStation and dist < const.maxDockingDistance:
                    self.Dock(itemID)
                elif groupID == const.groupControlBunker:
                    openFunctions.OpenInfrastructureHubPanel(otherBall.id)
                elif groupID != const.groupMissionContainer and groupID in self.containerGroups:
                    self.OpenCargo(itemID, 'SomeCargo')
                else:
                    self.Approach(itemID, 50)
            else:
                self.AlignTo(itemID)

    def SetDefaultWarpToDist(self, newRange):
        defaultRangeUtils.UpdateRangeSetting('WarpTo', newRange)

    def SetDefaultOrbitDist(self, newRange, *args):
        defaultRangeUtils.UpdateRangeSetting('Orbit', newRange)

    def SetDefaultKeepAtRangeDist(self, newRange, *args):
        defaultRangeUtils.UpdateRangeSetting('KeepAtRange', newRange)

    def FindReasonNotAvailable(self, prereqs):
        for each in prereqs:
            d = {}
            if len(each) == 4:
                label, value, expected, d = each
            else:
                label, value, expected = each
            if value == expected:
                continue
            if label not in self.allReasonsDict:
                continue
            reasonPath = self.allReasonsDict[label]
            reason = localization.GetByLabel(reasonPath, **d)
            return reason

    def ShowDestinyBalls(self, itemID, showType):
        return modelDebugFunctions.ShowDestinyBalls(itemID, showType)

    def ShowBallPartition(self, itemID):
        ball = sm.StartService('michelle').GetBallpark().GetBall(itemID)
        ball.showBoxes = 1

    def AnchorObject(self, itemID, anchorFlag):
        dogmaLM = self.godma.GetDogmaLM()
        if dogmaLM:
            typeID = sm.StartService('michelle').GetItem(itemID).typeID
            anchoringDelay = self.godma.GetType(typeID).anchoringDelay
            if anchorFlag:
                dogmaLM.Activate(itemID, const.effectAnchorDrop)
                eve.Message('AnchoringObject', {'delay': anchoringDelay / 1000.0})
            else:
                dogmaLM.Activate(itemID, const.effectAnchorLift)
                eve.Message('UnanchoringObject', {'delay': anchoringDelay / 1000.0})

    def UnanchorStructure(self, itemID):
        item = sm.GetService('michelle').GetItem(itemID)
        orphaned = self.pwn.StructureIsOrphan(itemID)
        if orphaned:
            msgName = 'ConfirmOrphanStructureUnanchor'
        elif item.groupID == const.groupInfrastructureHub:
            msgName = 'ConfirmInfrastructureHubUnanchor'
        elif item.groupID == const.groupAssemblyArray:
            msgName = 'ConfirmAssemblyArrayUnanchor'
        elif item.groupID == const.groupPersonalHangar:
            msgName = 'ConfirmUnanchoringPersonalHangar'
        else:
            msgName = 'ConfirmStructureUnanchor'
        if eve.Message(msgName, {'item': item.typeID}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        unanchoringDelay = self.godma.GetType(item.typeID).unanchoringDelay
        dogmaLM = sm.GetService('godma').GetDogmaLM()
        dogmaLM.Activate(itemID, const.effectAnchorLiftForStructures)
        eve.Message('UnanchoringObject', {'delay': unanchoringDelay / 1000.0})

    def AnchorStructure(self, itemID):
        dogmaLM = self.godma.GetDogmaLM()
        if dogmaLM:
            item = sm.StartService('michelle').GetItem(itemID)
            typeID = item.typeID
            if anchorFlag:
                anchoringDelay = self.godma.GetType(typeID).anchoringDelay
                ball = sm.StartService('michelle').GetBallpark().GetBall(itemID)
                sm.StartService('pwn').Anchor(itemID, (ball.x, ball.y, ball.z))
                eve.Message('AnchoringObject', {'delay': anchoringDelay / 1000.0})

    def ToggleObjectOnline(self, itemID, onlineFlag):
        dogmaLM = self.godma.GetDogmaLM()
        if dogmaLM:
            item = sm.StartService('michelle').GetItem(itemID)
            if onlineFlag:
                if item.groupID in (const.groupSovereigntyClaimMarkers,):
                    if eve.Message('ConfirmSovStructureOnline', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                        return
                dogmaLM.Activate(itemID, const.effectOnlineForStructures)
            else:
                if item.groupID == const.groupControlTower:
                    msgName = 'ConfirmTowerOffline'
                elif item.groupID == const.groupSovereigntyClaimMarkers:
                    msgName = 'ConfirmSovereigntyClaimMarkerOffline'
                else:
                    msgName = 'ConfirmStructureOffline'
                if eve.Message(msgName, {'item': (const.UE_TYPEID, item.typeID)}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                    return
                dogmaLM.Deactivate(itemID, const.effectOnlineForStructures)

    def DeclareWar(self):
        return menuFunctions.DeclareWar()

    def DeclareWarAgainst(self, againstID):
        return menuFunctions.DeclareWarAgainst(againstID)

    def TransferOwnership(self, itemID):
        return menuFunctions.TransferOwnership(itemID)

    def TransferCorporationOwnership(self, itemID):
        return menuFunctions.TransferCorporationOwnership(itemID)

    def ConfigureObject(self, itemID):
        self.pwn.ConfigureSentryGun(itemID)

    def AskNewContainerPassword(self, id_, desc, which = 1, setnew = '', setold = ''):
        return menuFunctions.AskNewContainerPassword(self.invCache, id_, desc, which, setnew, setold)

    def LockDownBlueprint(self, invItem):
        return invItemFunctions.LockDownBlueprint(invItem, self.invCache)

    def UnlockBlueprint(self, invItem):
        return invItemFunctions.UnlockBlueprint(invItem, self.invCache)

    def ALSCLock(self, invItems):
        return invItemFunctions.ALSCLock(invItems, self.invCache)

    def ALSCUnlock(self, invItems):
        return invItemFunctions.ALSCUnlock(invItems, self.invCache)

    def ConfigureALSC(self, itemID):
        return menuFunctions.ConfigureALSC(itemID, self.invCache)

    def RetrievePasswordALSC(self, itemID):
        return menuFunctions.RetrievePasswordALSC(itemID, self.invCache)

    def OpenShippingUnitStorage(self, itemID):
        self.GetCloseAndTryCommand(itemID, self.ReallyOpenShippingUnitStorage, (itemID,))

    def ReallyOpenShippingUnitStorage(self, itemID):
        entity = moniker.GetEntityAccess()
        if entity:
            entity.OpenShippingUnitStorage(itemID)

    def GetFleetMemberMenu(self, func, args):
        menuSize = 20
        watchlistCharIDs = [ member.charID for member in sm.GetService('fleet').GetFavorites() ]
        fleet = []
        watchlistMembers = []
        for member in sm.GetService('fleet').GetMembers().itervalues():
            if member.charID == session.charid:
                continue
            data = cfg.eveowners.Get(member.charID)
            memberInfo = (data.name.lower(), (member.charID, data.name))
            fleet.append(memberInfo)
            if member.charID in watchlistCharIDs:
                watchlistMembers.append(memberInfo)

        fleet = uiutil.SortListOfTuples(fleet)
        if watchlistMembers:
            watchlistMembers = uiutil.SortListOfTuples(watchlistMembers)
            watchlistEntry = [(localization.GetByLabel('UI/Fleet/WatchList'), ('isDynamic', self.GetSubFleetMemberMenu, (watchlistMembers, func, args))), None]
        else:
            watchlistEntry = []
        all = []
        while len(fleet) > menuSize:
            all.append(fleet[:menuSize])
            fleet = fleet[menuSize:]

        if fleet:
            all.append(fleet)
        if not all:
            return []
        elif len(all) == 1:
            return watchlistEntry + self.GetSubFleetMemberMenu(all[0], func, args)
        else:
            return watchlistEntry + [ ('%c ... %c' % (sub[0][1][0], sub[-1][1][0]), ('isDynamic', self.GetSubFleetMemberMenu, (sub, func, args))) for sub in all ]

    def GetSubFleetMemberMenu(self, memberIDs, func, args):
        return [ [name, func, (charID, args)] for charID, name in memberIDs ]

    def BridgeToMember(self, charID):
        beaconStuff = sm.GetService('fleet').GetActiveBeaconForChar(charID)
        if beaconStuff is None:
            return
        self.BridgeToBeacon(charID, beaconStuff)

    def BridgeToBeaconAlliance(self, solarSystemID, beaconID):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        bp.CmdBridgeToStructure(beaconID, solarSystemID)

    def BridgeToBeacon(self, charID, beacon):
        solarsystemID, beaconID = beacon
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        bp.CmdBridgeToMember(charID, beaconID, solarsystemID)

    def JumpThroughFleet(self, otherCharID, otherShipID):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        bridge = sm.GetService('fleet').GetActiveBridgeForShip(otherShipID)
        if bridge is None:
            return
        solarsystemID, beaconID = bridge
        self.LogNotice('Jump Through Fleet', otherCharID, otherShipID, beaconID, solarsystemID)
        sm.StartService('sessionMgr').PerformSessionChange('jump', bp.CmdJumpThroughFleet, otherCharID, otherShipID, beaconID, solarsystemID)

    def JumpThroughAlliance(self, otherShipID):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        bridge = sm.StartService('pwn').GetActiveBridgeForShip(otherShipID)
        if bridge is None:
            return
        solarsystemID, beaconID = bridge
        self.LogNotice('Jump Through Alliance', otherShipID, beaconID, solarsystemID)
        sm.StartService('sessionMgr').PerformSessionChange('jump', bp.CmdJumpThroughAlliance, otherShipID, beaconID, solarsystemID)

    def JumpToMember(self, charid):
        beaconStuff = sm.GetService('fleet').GetActiveBeaconForChar(charid)
        if beaconStuff is None:
            return
        self.JumpToBeaconFleet(charid, beaconStuff)

    def JumpToBeaconFleet(self, charid, beacon):
        solarsystemID, beaconID = beacon
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        self.LogNotice('Jump To Beacon Fleet', charid, beaconID, solarsystemID)
        sm.StartService('sessionMgr').PerformSessionChange('jump', bp.CmdBeaconJumpFleet, charid, beaconID, solarsystemID)

    def JumpToBeaconAlliance(self, solarSystemID, beaconID):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        self.LogNotice('Jump To Beacon Alliance', beaconID, solarSystemID)
        sm.StartService('sessionMgr').PerformSessionChange('jump', bp.CmdBeaconJumpAlliance, beaconID, solarSystemID)

    def ActivateGridSmartBomb(self, charid, effect):
        beaconStuff = sm.GetService('fleet').GetActiveBeaconForChar(charid)
        if beaconStuff is None:
            return
        solarsystemID, beaconID = beaconStuff
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is None:
            return
        effect.Activate(beaconID, False)

    def LeaveFleet(self):
        sm.GetService('fleet').LeaveFleet()

    def MakeLeader(self, charid):
        sm.GetService('fleet').MakeLeader(charid)

    def KickMember(self, charid):
        sm.GetService('fleet').KickMember(charid)

    def DisbandFleet(self):
        sm.GetService('fleet').DisbandFleet()

    def InviteToFleet(self, charIDs, ignoreWars = 0):
        if type(charIDs) != list:
            charIDs = [charIDs]
        charErrors = {}
        for charID in charIDs:
            try:
                sm.GetService('fleet').Invite(charID, None, None, None)
            except UserError as ue:
                charErrors[charID] = ue
                sys.exc_clear()

        if len(charErrors) == 1:
            raise charErrors.values()[0]
        elif len(charErrors) > 1:
            charNames = None
            for charID in charErrors.iterkeys():
                if charNames is not None:
                    charNames += ', %s' % cfg.eveowners.Get(charID).name
                else:
                    charNames = cfg.eveowners.Get(charID).name

            raise UserError('FleetInviteMultipleErrors', {'namelist': charNames})

    def Regroup(self, *args):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            bp.CmdFleetRegroup()

    def WarpFleet(self, id, warpRange = None):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            bp.CmdWarpToStuff('item', id, minRange=warpRange, fleet=True)
            sm.StartService('space').WarpDestination(celestialID=id)

    def WarpToMember(self, charID, warpRange = None):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            bp.CmdWarpToStuff('char', charID, minRange=warpRange)
            sm.StartService('space').WarpDestination(fleetMemberID=charID)

    def WarpFleetToMember(self, charID, warpRange = None):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            bp.CmdWarpToStuff('char', charID, minRange=warpRange, fleet=True)
            sm.StartService('space').WarpDestination(fleetMemberID=charID)

    def TacticalItemClicked(self, itemID):
        isTargeted = sm.GetService('target').IsTarget(itemID)
        if isTargeted:
            sm.GetService('state').SetState(itemID, state.activeTarget, 1)
        uicore.cmd.ExecuteCombatCommand(itemID, uiconst.UI_CLICK)

    def Approach(self, itemID, cancelAutoNavigation = True):
        """
        apprach an object in space
        itemID: the item to approach
        approachRange: the desired proximity to approach to, default 50 meters
        cancelAutoNavigation: should the call cancel the current system navigation task, default True
        """
        if itemID == session.shipid:
            return
        autoPilot = sm.GetService('autoPilot')
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            if cancelAutoNavigation:
                autoPilot.CancelSystemNavigation()
        else:
            autoPilot.AbortWarpAndTryCommand()
            autoPilot.AbortApproachAndTryCommand(itemID)
        bp = self.michelle.GetRemotePark()
        if bp is not None:
            shipBall = self.michelle.GetBall(session.shipid)
            if shipBall is not None:
                if shipBall.mode != destiny.DSTBALL_FOLLOW or shipBall.followId != itemID or shipBall.followRange != const.approachRange:
                    sm.GetService('space').SetIndicationTextForcefully(ballMode=destiny.DSTBALL_FOLLOW, followId=itemID, followRange=const.approachRange)
                    bp.CmdFollowBall(itemID, const.approachRange)
                    sm.GetService('flightPredictionSvc').OptionActivated('Approach', itemID, const.approachRange)
                    sm.ScatterEvent('OnClientEvent_Approach')

    def AlignTo(self, alignID):
        if alignID == session.shipid:
            return
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            self.StoreAlignTarget(alignTargetID=alignID, aligningToBookmark=False)
            sm.GetService('space').SetIndicationTextForcefully(ballMode=destiny.DSTBALL_GOTO, followId=alignID, followRange=None)
            bp.CmdAlignTo(alignID)
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            sm.GetService('flightPredictionSvc').OptionActivated('AlignTo', alignID)

    def AlignToBookmark(self, alignID):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp is not None:
            bp.CmdAlignTo(bookmarkID=alignID)
            self.StoreAlignTarget(alignTargetID=None, aligningToBookmark=True)
            sm.GetService('space').SetIndicationTextForcefully(ballMode=destiny.DSTBALL_GOTO, followId=None, followRange=None)
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()

    def StoreAlignTarget(self, alignTargetID = None, aligningToBookmark = False, *args):
        self.lastAlignTargetID = alignTargetID
        self.lastAlignedToBookmark = aligningToBookmark

    def GetLastAlignTarget(self, *args):
        return (getattr(self, 'lastAlignTargetID', None), getattr(self, 'lastAlignedToBookmark', False))

    def ClearAlignTargets(self, *args):
        self.lastAlignTargetID = None
        self.lastAlignedToBookmark = None

    def TagItem(self, itemID, tag):
        bp = sm.StartService('michelle').GetRemotePark()
        if bp:
            bp.CmdFleetTagTarget(itemID, tag)

    def LockTarget(self, id):
        sm.StartService('target').TryLockTarget(id)

    def UnlockTarget(self, id):
        sm.StartService('target').UnlockTarget(id)

    def ShowInfo(self, typeID, itemID = None, new = 0, rec = None, parentID = None, abstractInfo = None, *args):
        sm.StartService('info').ShowInfo(typeID, itemID, new, rec, parentID, abstractinfo=abstractInfo)

    def ShowInfoForItem(self, itemID):
        bp = sm.StartService('michelle').GetBallpark()
        if bp:
            itemTypeID = bp.GetInvItem(itemID).typeID
            sm.GetService('info').ShowInfo(itemTypeID, itemID)

    def PreviewType(self, typeID):
        sm.GetService('preview').PreviewType(typeID)

    def StoreVessel(self, destID, shipID):
        if shipID != session.shipid:
            return
        shipItem = self.godma.GetStateManager().GetItem(shipID)
        if shipItem.groupID == const.groupCapsule:
            return
        destItem = uix.GetBallparkRecord(destID)
        if destItem.categoryID == const.categoryShip:
            msgName = 'ConfirmStoreVesselInShip'
        else:
            msgName = 'ConfirmStoreVesselInStructure'
        if eve.Message(msgName, {'dest': destItem.typeID}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        if shipID != session.shipid:
            return
        shipItem = self.godma.GetStateManager().GetItem(shipID)
        if shipItem.groupID == const.groupCapsule:
            return
        ship = sm.StartService('gameui').GetShipAccess()
        if ship:
            sm.ScatterEvent('OnBeforeActiveShipChanged', shipID, util.GetActiveShip())
            sm.StartService('sessionMgr').PerformSessionChange('storeVessel', ship.StoreVessel, destID)

    def OpenCorpHangarArray(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSCorpHangars', itemID))

    def OpenPersonalHangar(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSPersonalHangar', itemID))

    def OpenPOSSilo(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSSilo', itemID))

    def OpenPOSMobileReactor(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSMobileReactor', itemID))

    def OpenPOSShipMaintenanceArray(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSShipMaintenanceArray', itemID))

    def OpenPOSStructureChargesStorage(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSStructureChargesStorage', itemID))

    def OpenPOSStructureChargeCrystal(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSStructureChargeCrystal', itemID))

    def OpenPOSFuelBay(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSFuelBay', itemID))

    def OpenPOSJumpBridge(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSJumpBridge', itemID))

    def OpenPOSRefinery(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSRefinery', itemID))

    def OpenPOSCompression(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSCompression', itemID))

    def OpenPOSStructureCharges(self, itemID, showCapacity = 0):
        form.Inventory.OpenOrShow(invID=('POSStructureCharges', itemID))

    def OpenStrontiumBay(self, itemID):
        form.Inventory.OpenOrShow(invID=('POSStrontiumBay', itemID))

    def ManageControlTower(self, itemID):
        uthread.new(self._ManageControlTower, itemID)

    def _ManageControlTower(self, itemID):
        uicore.cmd.OpenMoonMining(itemID)

    def OpenConstructionPlatform(self, itemID):
        invID = ('POSConstructionPlatform', itemID)
        form.Inventory.OpenOrShow(invID=invID)

    def OpenFuelBay(self, itemID):
        self._OpenShipBay(invID=('ShipFuelBay', itemID))

    def OpenOreHold(self, itemID):
        self._OpenShipBay(invID=('ShipOreHold', itemID))

    def OpenGasHold(self, itemID):
        self._OpenShipBay(invID=('ShipGasHold', itemID))

    def OpenMineralHold(self, itemID):
        self._OpenShipBay(invID=('ShipMineralHold', itemID))

    def OpenSalvageHold(self, itemID):
        self._OpenShipBay(invID=('ShipSalvageHold', itemID))

    def OpenShipHold(self, itemID):
        self._OpenShipBay(invID=('ShipShipHold', itemID))

    def OpenSmallShipHold(self, itemID):
        self._OpenShipBay(invID=('ShipSmallShipHold', itemID))

    def OpenMediumShipHold(self, itemID):
        self._OpenShipBay(invID=('ShipMediumShipHold', itemID))

    def OpenLargeShipHold(self, itemID):
        self._OpenShipBay(invID=('ShipLargeShipHold', itemID))

    def OpenIndustrialShipHold(self, itemID):
        self._OpenShipBay(invID=('ShipIndustrialShipHold', itemID))

    def OpenAmmoHold(self, itemID):
        self._OpenShipBay(invID=('ShipAmmoHold', itemID))

    def OpenCommandCenterHold(self, itemID):
        self._OpenShipBay(invID=('ShipCommandCenterHold', itemID))

    def OpenPlanetaryCommoditiesHold(self, itemID):
        self._OpenShipBay(invID=('ShipPlanetaryCommoditiesHold', itemID))

    def OpenQuafeHold(self, itemID):
        self._OpenShipBay(invID=('ShipQuafeHold', itemID))

    def _OpenShipBay(self, invID):
        form.Inventory.OpenOrShow(invID=invID, openFromWnd=uicore.registry.GetActive())

    def OpenSpaceComponentInventory(self, itemID):
        form.Inventory.OpenOrShow(invID=('SpaceComponentInventory', itemID))

    def BuildConstructionPlatform(self, id):
        if getattr(self, '_buildingPlatform', 0):
            return
        self._buildingPlatform = 1
        uthread.new(self._BuildConstructionPlatform, id)

    def _BuildConstructionPlatform(self, id):
        try:
            securityCode = None
            shell = self.invCache.GetInventoryFromId(id)
            while 1:
                try:
                    if securityCode is None:
                        shell.Build()
                    else:
                        shell.Build(securityCode=securityCode)
                    break
                except UserError as what:
                    if what.args[0] == 'PermissionDenied':
                        if securityCode:
                            caption = localization.GetByLabel('UI/Menusvc/IncorrectPassword')
                            label = localization.GetByLabel('UI/Menusvc/PleaseTryEnteringPasswordAgain')
                        else:
                            caption = localization.GetByLabel('UI/Menusvc/PasswordRequired')
                            label = localization.GetByLabel('UI/Menusvc/PleaseEnterPassword')
                        passw = uiutil.NamePopup(caption=caption, label=label, setvalue='', maxLength=50, passwordChar='*')
                        if passw is None:
                            raise UserError('IgnoreToTop')
                        else:
                            securityCode = passw
                    else:
                        raise
                    sys.exc_clear()

        finally:
            self._buildingPlatform = 0

    def Bookmark(self, itemID, typeID, parentID, note = None):
        sm.StartService('addressbook').BookmarkLocationPopup(itemID, typeID, parentID, note)

    def ShowInMapBrowser(self, itemID, *args):
        uicore.cmd.OpenMapBrowser(itemID)

    def ShowInMap(self, itemID, *args):
        sm.GetService('viewState').ActivateView('starmap', interestID=itemID)

    def Dock(self, id):
        bp = sm.StartService('michelle').GetBallpark()
        if not bp:
            return
        self.GetCloseAndTryCommand(id, movementFunctions.RealDock, (id,))

    def GetIllegality(self, itemID, typeID = None, solarSystemID = None):
        if solarSystemID is None:
            solarSystemID = session.solarsystemid
        toFactionID = sm.StartService('faction').GetFactionOfSolarSystem(solarSystemID)
        if typeID is not None and cfg.invtypes.Get(typeID).groupID not in (const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer):
            if cfg.invtypes.Get(typeID).Illegality(toFactionID):
                return cfg.invtypes.Get(typeID).name
            return ''
        stuff = ''
        invItem = self.invCache.GetInventoryFromId(itemID)
        for item in invItem.List():
            try:
                illegality = cfg.invtypes.Get(item.typeID).Illegality(toFactionID)
                if illegality:
                    stuff += cfg.invtypes.Get(item.typeID).name + ', '
                if cfg.invtypes.Get(item.typeID).groupID in (const.groupCargoContainer,
                 const.groupSecureCargoContainer,
                 const.groupAuditLogSecureContainer,
                 const.groupFreightContainer):
                    sublegality = self.GetIllegality(item.itemID, solarSystemID=solarSystemID)
                    if sublegality:
                        stuff += sublegality + ', '
            except:
                log.LogTraceback('bork in illegality check 2')
                sys.exc_clear()

        return stuff[:-2]

    def StargateJump(self, id, beaconID = None, solarSystemID = None):
        if beaconID:
            self.GetCloseAndTryCommand(id, self.RealStargateJump, (id, beaconID, solarSystemID), interactionRange=const.maxStargateJumpingDistance)

    def RealStargateJump(self, id, beaconID, solarSystemID):
        if beaconID:
            bp = sm.StartService('michelle').GetRemotePark()
            if bp is not None:
                if solarSystemID is not None:
                    fromFactionID = sm.StartService('faction').GetFactionOfSolarSystem(session.solarsystemid)
                    toFactionID = sm.StartService('faction').GetFactionOfSolarSystem(solarSystemID)
                    if toFactionID and fromFactionID != toFactionID:
                        stuff = self.GetIllegality(session.shipid, solarSystemID=solarSystemID)
                        if stuff and eve.Message('ConfirmJumpWithIllicitGoods', {'faction': cfg.eveowners.Get(toFactionID).name,
                         'stuff': stuff}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                            return
                    sec = sm.StartService('map').GetSecurityStatus(solarSystemID)
                    toSecClass = sm.StartService('map').GetSecurityClass(solarSystemID)
                    fromSecClass = sm.StartService('map').GetSecurityClass(session.solarsystemid)
                    if toSecClass <= const.securityClassLowSec:
                        if fromSecClass >= const.securityClassHighSec and eve.Message('ConfirmJumpToUnsafeSS', {'ss': sec}, uiconst.OKCANCEL) != uiconst.ID_OK:
                            return
                    elif fromSecClass <= const.securityClassLowSec and self.crimewatchSvc.IsCriminal(session.charid):
                        if eve.Message('JumpCriminalConfirm', {}, uiconst.YESNO) != uiconst.ID_YES:
                            return
                self.LogNotice('Stargate Jump from', session.solarsystemid2, 'to', id)
                sm.StartService('sessionMgr').PerformSessionChange(localization.GetByLabel('UI/Inflight/Jump'), bp.CmdStargateJump, id, beaconID, session.shipid)

    def ActivateAccelerationGate(self, id):
        self.GetCloseAndTryCommand(id, movementFunctions.RealActivateAccelerationGate, (id,), interactionRange=const.maxStargateJumpingDistance)

    def EnterWormhole(self, itemID):
        self.GetCloseAndTryCommand(itemID, movementFunctions.RealEnterWormhole, (itemID,), interactionRange=const.maxWormholeEnterDistance)

    def CopyItemIDToClipboard(self, itemID):
        blue.pyos.SetClipboardData(str(itemID))

    def StopMyShip(self):
        uicore.cmd.CmdStopShip()

    def OpenCargo(self, id, *args):
        self.GetCloseAndTryCommand(id, self.RealOpenCargo, (id,))

    def RealOpenCargo(self, id, *args):
        if getattr(self, '_openingCargo', 0):
            return
        self._openingCargo = 1
        uthread.new(self._OpenCargo, id)

    def _OpenCargo(self, _id):
        if type(_id) != types.ListType:
            _id = [_id]
        for itemID in _id:
            try:
                if itemID == util.GetActiveShip():
                    uicore.cmd.OpenCargoHoldOfActiveShip()
                else:
                    slim = sm.GetService('michelle').GetItem(itemID)
                    if slim and slim.groupID == const.groupWreck:
                        invID = ('ItemWreck', itemID)
                    else:
                        invID = ('ItemFloatingCargo', itemID)
                    invCtrl.GetInvCtrlFromInvID(invID).GetItems()
                    if not (slim and HasCargoBayComponent(slim.typeID)):
                        sm.GetService('inv').AddTemporaryInvLocation(invID)
                    form.Inventory.OpenOrShow(invID=invID)
            finally:
                self._openingCargo = 0

    def OpenPlanetCustomsOfficeImportWindow(self, customsOfficeID):
        sm.GetService('planetUI').OpenPlanetCustomsOfficeImportWindow(customsOfficeID)

    def OpenUpgradeWindow(self, orbitalID):
        sm.GetService('planetUI').OpenUpgradeWindow(orbitalID)

    def AbandonLoot(self, wreckID, *args):
        return menuFunctions.AbandonLoot(wreckID)

    def AbandonAllLoot(self, wreckID, *args):
        return menuFunctions.AbandonAllLoot(wreckID)

    def ShipCloneConfig(self, id = None):
        if id == util.GetActiveShip():
            uthread.new(self._ShipCloneConfig)

    def _ShipCloneConfig(self):
        uicore.cmd.OpenShipConfig()

    def Reprocess(self, item, refinery):
        self.invCache.GetInventoryFromId(refinery.itemID).Reprocess(item.itemID)

    def EnterPOSPassword(self):
        sm.StartService('pwn').EnterShipPassword()

    def EnterForceFieldPassword(self, towerID):
        sm.StartService('pwn').EnterTowerPassword(towerID)

    def Eject(self):
        return menuFunctions.Eject()

    def Board(self, id):
        return menuFunctions.Board(id)

    def BoardSMAShip(self, structureID, shipID):
        return menuFunctions.BoardSMAShip(structureID, shipID)

    def ToggleAutopilot(self, on):
        if on:
            sm.StartService('autoPilot').SetOn()
        else:
            sm.StartService('autoPilot').SetOff('toggled through menu')

    def SelfDestructShip(self, pickid):
        return menuFunctions.SelfDestructShip(pickid)

    def SafeLogoff(self):
        return menuFunctions.SafeLogoff()

    def SetParent(self, pickid):
        sm.GetService('camera').LookAt(pickid, smooth=False)

    def SetInterest(self, pickid):
        sm.GetService('camera').SetCameraInterest(pickid)

    def TryLookAt(self, itemID):
        return menuFunctions.TryLookAt(itemID)

    def ToggleLookAt(self, itemID):
        return menuFunctions.ToggleLookAt(itemID)

    def Scoop(self, objectID, typeID, password = None):
        self.GetCloseAndTryCommand(objectID, self.RealScoop, (objectID, typeID, password))

    def RealScoop(self, objectID, typeID, password = None):
        ship = sm.StartService('gameui').GetShipAccess()
        if ship:
            toFactionID = sm.StartService('faction').GetFactionOfSolarSystem(session.solarsystemid)
            stuff = self.GetIllegality(objectID, typeID)
            if stuff and eve.Message('ConfirmScoopWithIllicitGoods', {'faction': cfg.eveowners.Get(toFactionID).name}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            try:
                if password is None:
                    ship.Scoop(objectID)
                else:
                    ship.Scoop(objectID, password)
            except UserError as what:
                if what.args[0] == 'ShpScoopSecureCC':
                    if password:
                        caption = localization.GetByLabel('UI/Menusvc/IncorrectPassword')
                        label = localization.GetByLabel('UI/Menusvc/PleaseTryEnteringPasswordAgain')
                    else:
                        caption = localization.GetByLabel('UI/Menusvc/PasswordRequired')
                        label = localization.GetByLabel('UI/Menusvc/PleaseEnterPassword')
                    passw = uiutil.NamePopup(caption=caption, label=label, setvalue='', maxLength=50, passwordChar='*')
                    if passw:
                        self.Scoop(objectID, password=passw)
                else:
                    raise
                sys.exc_clear()

    def ScoopSMA(self, objectID):
        self.GetCloseAndTryCommand(objectID, self.RealScoopSMA, (objectID,))

    def RealScoopSMA(self, objectID):
        ship = sm.StartService('gameui').GetShipAccess()
        if ship:
            ship.ScoopToSMA(objectID)

    def InteractWithAgent(self, agentID, *args):
        sm.StartService('agents').InteractWith(agentID)

    def QuickBuy(self, typeID, quantity = 1):
        sm.StartService('marketutils').Buy(typeID, quantity=quantity)

    def QuickSell(self, invItem):
        self.MultiSell([[(invItem, None, None)]])

    def MultiSell(self, invItems):
        sm.GetService('marketutils').StartupCheck()
        wnd = form.SellItems.GetIfOpen()
        if wnd is not None:
            wnd.AddPreItems(invItems[0])
            wnd.Maximize()
        else:
            form.SellItems.Open(preItems=invItems[0])

    def QuickContract(self, invItems, *args):
        sm.GetService('contracts').OpenCreateContract(items=invItems)

    def ShowMarketDetails(self, invItem):
        uthread.new(sm.StartService('marketutils').ShowMarketDetails, invItem.typeID, None)

    def GetContainerContents(self, invItem):
        return invItemFunctions.GetContainerContents(invItem, self.invCache)

    def DoGetContainerContents(self, itemID, stationID, hasFlag, name):
        return invItemFunctions.DoGetContainerContents(itemID, stationID, hasFlag, name, self.invCache)

    def AddToQuickBar(self, typeID, parent = 0):
        return menuFunctions.AddToQuickBar(typeID, parent)

    def RemoveFromQuickBar(self, node):
        return menuFunctions.RemoveFromQuickBar(node)

    def GetAndvancedMarket(self, typeID):
        pass

    def ActivateShip(self, invItem):
        if invItem.singleton and not uicore.uilib.Key(uiconst.VK_CONTROL):
            sm.StartService('station').TryActivateShip(invItem)

    def LeaveShip(self, invItem):
        if invItem.singleton and not uicore.uilib.Key(uiconst.VK_CONTROL):
            sm.StartService('station').TryLeaveShip(invItem)

    def EnterHangar(self, invItem):
        uicore.cmd.CmdEnterHangar()

    def EnterCQ(self, invItem):
        uicore.cmd.CmdEnterCQ()

    def StripFitting(self, invItem):
        if eve.Message('AskStripShip', None, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            shipID = invItem.itemID
            self.invCache.GetInventoryFromId(shipID).StripFitting()

    def ExitStation(self, invItem):
        uicore.cmd.CmdExitStation()

    def CompressItem(self, invItem, locationItem):
        return invItemFunctions.CompressItem(invItem, locationItem, self.invCache)

    def CheckLocked(self, func, invItemsOrIDs):
        return invItemFunctions.CheckLocked(func, invItemsOrIDs, self.invCache)

    def RepackageItemsInStation(self, invItems):
        return invItemFunctions.RepackageItemsInStation(invItems, self.invCache)

    def RepackageItemsInStructure(self, invItems):
        self.invCache.GetInventoryFromId(invItems[0].locationID).RepackageItemsInStructure([ item.itemID for item in invItems ])

    def Break(self, invItems):
        return invItemFunctions.Break(invItems, self.invCache)

    def DeliverCourierContract(self, invItem):
        sm.GetService('contracts').DeliverCourierContractFromItemID(invItem.itemID)

    def FindCourierContract(self, invItem):
        sm.GetService('contracts').FindCourierContractFromItemID(invItem.itemID)

    def FitShip(self, invItem):
        wnd = form.FittingWindow.GetIfOpen()
        if wnd is not None:
            wnd.CloseByUser()
        form.FittingWindow.Open(shipID=invItem.itemID)

    def LaunchDrones(self, invItems, *args):
        sm.GetService('godma').GetStateManager().SendDroneSettings()
        util.LaunchFromShip(invItems)

    def LaunchForSelf(self, invItems):
        util.LaunchFromShip(invItems, session.charid, maxQty=1)

    def LaunchForCorp(self, invItems, ignoreWarning = False):
        util.LaunchFromShip(invItems, session.corpid, ignoreWarning, maxQty=1)

    def LaunchSMAContents(self, invItems):
        return invItemFunctions.LaunchSMAContents(invItems[0])

    def Jettison(self, invItems):
        return invItemFunctions.Jettison(invItems)

    def TrashInvItems(self, invItems):
        return invItemFunctions.TrashInvItems(invItems, self.invCache)

    def Refine(self, invItems):
        return invItemFunctions.Refine(invItems)

    def RefineToHangar(self, invItems):
        return invItemFunctions.RefineToHangar(invItems)

    def TrainNow(self, invItems):
        return invItemFunctions.TrainNow(invItems)

    def InjectSkillIntoBrain(self, invItems):
        return invItemFunctions.InjectSkillIntoBrain(invItems)

    def PlugInImplant(self, invItems):
        return invItemFunctions.PlugInImplant(invItems)

    def ActivatePlex(self, itemID):
        return menuFunctions.ActivatePlex(itemID)

    def ApplyAurumToken(self, item, qty):
        return menuFunctions.ApplyAurumToken(item, qty)

    def ActivateCharacterReSculpt(self, itemID):
        return menuFunctions.ActivateCharacterReSculpt(itemID)

    def ActivateMultiTraining(self, itemID):
        return menuFunctions.ActivateMultiTraining(itemID)

    def ConsumeBooster(self, invItems):
        return invItemFunctions.ConsumeBooster(invItems)

    def AssembleContainer(self, invItems):
        invMgr = self.invCache.GetInventoryMgr()
        for invItem in invItems:
            invMgr.AssembleCargoContainer(invItem.itemID, None, 0.0)

    def ShowInIndustryWindow(self, invItem):
        Industry.OpenOrShowBlueprint(blueprintID=invItem.itemID)

    def SetHomeStation(self, stationID):
        form.CloneStationWindow.SetStation(stationID)

    @base.ThrottlePerSecond()
    def AssembleShip(self, invItems):
        return invItemFunctions.AssembleShip(invItems)

    def TryFit(self, invItems, shipID = None):
        """ Also known as the for-else function. """
        if not shipID:
            shipID = util.GetActiveShip()
            if not shipID:
                return
        godma = sm.services['godma']
        shipInv = self.invCache.GetInventoryFromId(shipID, locationID=session.stationid2)
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        godmaSM = godma.GetStateManager()
        useRigs = None
        charges = set()
        drones = []
        subSystemGroupIDs = set()
        for invItem in invItems[:]:
            if invItem.categoryID == const.categoryModule:
                moduleEffects = cfg.dgmtypeeffects.get(invItem.typeID, [])
                for mEff in moduleEffects:
                    if mEff.effectID == const.effectRigSlot:
                        if useRigs is None:
                            useRigs = True if self.RigFittingCheck(invItem) else False
                        if not useRigs:
                            invItems.remove(invItem)
                            self.invCache.UnlockItem(invItem.itemID)
                            break

            if invItem.categoryID == const.categorySubSystem:
                if invItem.groupID in subSystemGroupIDs:
                    invItems.remove(invItem)
                else:
                    subSystemGroupIDs.add(invItem.groupID)
            elif invItem.categoryID == const.categoryCharge:
                charges.add(invItem)
                invItems.remove(invItem)
            elif invItem.categoryID == const.categoryDrone:
                drones.append(invItem)
                invItems.remove(invItem)

        if len(invItems) > 0:
            shipInv.moniker.MultiAdd([ invItem.itemID for invItem in invItems ], invItems[0].locationID, flag=const.flagAutoFit)
        if charges:
            shipStuff = shipInv.List()
            shipStuff.sort(key=lambda r: (r.flagID, isinstance(r.itemID, tuple)))
            loadedSlots = set()
        if drones:
            invCtrl.ShipDroneBay(shipID or util.GetActiveShip()).AddItems(drones)
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        shipDogmaItem = dogmaLocation.dogmaItems.get(shipID, None)
        loadedSomething = False
        for DBRowInvItem in charges:
            invItem = util.KeyVal(DBRowInvItem)
            chargeDgmType = godmaSM.GetType(invItem.typeID)
            isCrystalOrScript = invItem.groupID in cfg.GetCrystalGroups()
            for row in shipStuff:
                if row in loadedSlots:
                    continue
                if not IsShipFittingFlag(row.flagID):
                    continue
                if dogmaLocation.IsInWeaponBank(row.locationID, row.itemID) and dogmaLocation.IsModuleSlave(row.itemID, row.locationID):
                    continue
                if row.categoryID == const.categoryCharge:
                    continue
                moduleDgmType = godmaSM.GetType(row.typeID)
                desiredSize = getattr(moduleDgmType, 'chargeSize', None)
                for x in xrange(1, 5):
                    chargeGroup = getattr(moduleDgmType, 'chargeGroup%d' % x, False)
                    if not chargeGroup:
                        continue
                    if chargeDgmType.groupID != chargeGroup:
                        continue
                    if desiredSize and getattr(chargeDgmType, 'chargeSize', -1) != desiredSize:
                        continue
                    leftOvers = False
                    for i, squatter in enumerate([ i for i in shipStuff if i.flagID == row.flagID ]):
                        if isCrystalOrScript and i > 0:
                            break
                        if shipDogmaItem is None:
                            continue
                        subLocation = dogmaLocation.GetSubLocation(shipID, squatter.flagID)
                        if subLocation is None:
                            continue
                        chargeVolume = chargeDgmType.volume * dogmaLocation.GetAttributeValue(subLocation, const.attributeQuantity)
                        if godmaSM.GetType(row.typeID).capacity <= chargeVolume:
                            break
                    else:
                        moduleCapacity = godmaSM.GetType(row.typeID).capacity
                        numCharges = moduleCapacity / chargeDgmType.volume
                        subLocation = dogmaLocation.GetSubLocation(shipID, row.flagID)
                        if subLocation:
                            numCharges -= dogmaLocation.GetAttributeValue(subLocation, const.attributeQuantity)
                        dogmaLocation.LoadAmmoToModules(shipID, [row.itemID], invItem.typeID, invItem.itemID, invItem.locationID)
                        loadedSomething = True
                        invItem.stacksize -= numCharges
                        loadedSlots.add(row)
                        blue.pyos.synchro.SleepWallclock(100)
                        break

                else:
                    continue

                if invItem.stacksize <= 0:
                    break
            else:
                if not loadedSomething:
                    eve.Message('NoSuitableModules')

    def HandleMultipleCallError(self, droneID, ret, messageName):
        return droneFunctions.HandleMultipleCallError(droneID, ret, messageName)

    def EngageTarget(self, droneIDs):
        return droneFunctions.EngageTarget(droneIDs)

    def ReturnControl(self, droneIDs):
        return droneFunctions.ReturnControl(droneIDs)

    def DelegateControl(self, charID, droneIDs):
        return droneFunctions.DelegateControl(charID, droneIDs)

    def Assist(self, charID, droneIDs):
        return droneFunctions.Assist(charID, droneIDs)

    def Guard(self, charID, droneIDs):
        return droneFunctions.Guard(charID, droneIDs)

    def Mine(self, droneIDs):
        return droneFunctions.Mine(droneIDs)

    def MineRepeatedly(self, droneIDs):
        return droneFunctions.MineRepeatedly(droneIDs)

    def Salvage(self, droneIDs):
        return droneFunctions.Salvage(droneIDs)

    def DroneUnanchor(self, droneIDs):
        return droneFunctions.DroneUnanchor(droneIDs)

    def ReturnAndOrbit(self, droneIDs):
        return droneFunctions.ReturnAndOrbit(droneIDs)

    def ReturnToDroneBay(self, droneIDs):
        return droneFunctions.ReturnToDroneBay(droneIDs)

    def ScoopToDroneBay(self, objectIDs):
        if len(objectIDs) == 1:
            self.GetCloseAndTryCommand(objectIDs[0], self.RealScoopToDroneBay, (objectIDs,))
        else:
            self.RealScoopToDroneBay(objectIDs)

    def RealScoopToDroneBay(self, objectIDs):
        return droneFunctions.RealScoopToDroneBay(objectIDs)

    def FitDrone(self, invItems):
        return droneFunctions.FitDrone(invItems, self.invCache)

    def AbandonDrone(self, droneIDs):
        return droneFunctions.AbandonDrone(droneIDs)

    def CopyItemIDAndMaybeQuantityToClipboard(self, invItem):
        return menuFunctions.CopyItemIDAndMaybeQuantityToClipboard(invItem)

    def SetName(self, invOrSlimItem):
        return menuFunctions.SetName(invOrSlimItem, self.invCache)

    def AskNewContainerPwd(self, invItems, desc, which = 1):
        for invItem in invItems:
            self.AskNewContainerPassword(invItem.itemID, desc, which)

    def GetDefaultActionDistance(self, key):
        return defaultRangeUtils.FetchRangeSetting(key)

    def CopyCoordinates(self, itemID):
        ball = self.michelle.GetBall(itemID)
        if ball:
            blue.pyos.SetClipboardData(str((ball.x, ball.y, ball.z)))

    def AnchorOrbital(self, itemID):
        posMgr = util.Moniker('posMgr', session.solarsystemid)
        posMgr.AnchorOrbital(itemID)

    def UnanchorOrbital(self, itemID):
        posMgr = util.Moniker('posMgr', session.solarsystemid)
        posMgr.UnanchorOrbital(itemID)

    def ConfigureOrbital(self, item):
        sm.GetService('planetUI').OpenConfigureWindow(item)

    def ConfigureIndustryTax(self, itemID, typeID):
        facilityName = cfg.evelocations.Get(itemID).name
        if not facilityName:
            facilityName = cfg.invtypes.Get(typeID).name
        if util.IsStation(itemID):
            form.FacilityStandingsWindow.Open(facilityID=itemID, facilityName=facilityName)
        else:
            form.FacilityTaxWindow.Open(facilityID=itemID, facilityName=facilityName)

    def CompleteOrbitalStateChange(self, itemID):
        posMgr = util.Moniker('posMgr', session.solarsystemid)
        posMgr.CompleteOrbitalStateChange(itemID)

    def GMUpgradeOrbital(self, itemID):
        posMgr = util.Moniker('posMgr', session.solarsystemid)
        posMgr.GMUpgradeOrbital(itemID)

    def TakeOrbitalOwnership(self, itemID, planetID):
        registry = moniker.GetPlanetOrbitalRegistry(session.solarsystemid)
        registry.GMChangeSpaceObjectOwner(itemID, session.corpid)

    def GetCloseAndTryCommand(self, itemID, cmdMethod, args, interactionRange = 2500):
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            sm.GetService('autoPilot').NavigateSystemTo(itemID, interactionRange, cmdMethod, *args)
        else:
            self.GetCloseAndTryCommand_Old(itemID, cmdMethod, args, interactionRange)

    def GetCloseAndTryCommand_Old(self, id, cmdMethod, args, interactionRange = 2500):
        """
        # TODO: DEPRICATED: this should be removed when we clean up newAutoNavigationKillSwitch
        
        This is the old way to close in on object and execute a command.
        This should be removed when/if we are sure the new version performs
        """
        bp = sm.StartService('michelle').GetBallpark()
        if not bp:
            return
        ball = bp.GetBall(id)
        ball.GetVectorAt(blue.os.GetSimTime())
        if ball.surfaceDist >= const.minWarpDistance:
            sm.GetService('autoPilot').WarpAndTryCommand(id, cmdMethod, args, interactionRange=interactionRange)
        elif ball.surfaceDist > interactionRange:
            sm.GetService('autoPilot').ApproachAndTryCommand(id, cmdMethod, args, interactionRange=interactionRange)
        else:
            cmdMethod(*args)

    def ReconnectToDrones(self):
        return droneFunctions.ReconnectToDrones()

    def SetDefaultDist(self, key):
        return movementFunctions.SetDefaultDist(key)

    def IsJettisonable(self, invItem, locationItem):
        """
        Takes in the item and its' location
        Checks if you are in space
        Checks if item is legal for jettison (NOT: ships, certain items with cargo, items in certain locations)
        Returns true/false
        """
        if not self.GetCheckInSpace():
            return False
        if invItem.categoryID == const.categoryShip:
            return False
        if invItem.groupID in const.playerDeployedContainers:
            return False
        if HasCargoBayComponent(invItem.typeID):
            return False
        if locationItem and HasCargoBayComponent(locationItem.typeID):
            return False
        return True

    def AddDisabledEntryForWarp(self, menuEntries, textPath):
        menuEntries += [[uiutil.MenuLabel(textPath), DISABLED_ENTRY0]]
        menuEntries.reasonsWhyNotAvailable[textPath] = localization.GetByLabel('UI/Menusvc/MenuHints/YouAreInWarp')


class MenuList(list):
    """
        This class extends the normal list by adding an attribute
    """
    reasonsWhyNotAvailable = {}
