#Embedded file name: eve/client/script/ui/services\inventorysvc.py
import _weakref
import sys
import blue
from eve.client.script.ui.control.treeData import TreeData
from eve.client.script.ui.shared.inventory.invCommon import SortData
from eve.client.script.ui.shared.inventory.treeData import TreeDataShip, TreeDataInv, GetContainerDataFromItems, TreeDataStationCorp, TreeDataCelestialParent, TreeDataPOSCorp, TreeDataInvFolder, GetTreeDataClassByInvName
import form
import invCtrl
import localization
import log
import service
from spacecomponents.common.componentConst import CARGO_BAY
from spacecomponents.common.helper import HasCargoBayComponent
import telemetry
import uthread
import util

class InventorySvc(service.Service):
    """
    Keep track of inventory registrations.
    """
    __guid__ = 'svc.inv'
    __exportedcalls__ = {'Register': [],
     'Unregister': [],
     'OnBreadcrumbTextClicked': [service.ROLE_IGB]}
    __notifyevents__ = []

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.regs = {}
        self.itemClipboard = []
        self.itemClipboardCopy = False
        self.tempInvLocations = set()

    @telemetry.ZONE_METHOD
    def OnItemChange(self, item, change):
        self.LogInfo('OnItemChange', change, item)
        self.ClearItemClipboard()
        fancyChange = {}
        for k, v in change.iteritems():
            fancyChange[item.__columns__[k]] = (v, '->', item[k])

        self.LogInfo('OnItemChange (fancy)', fancyChange, item)
        old = blue.DBRow(item)
        for k, v in change.iteritems():
            if k == const.ixSingleton and v == 0:
                v = 1
            if k in (const.ixStackSize, const.ixSingleton):
                k = const.ixQuantity
            old[k] = v

        closeContainer = 0
        containerCookie = None
        containerName = ''
        if item.groupID in (const.groupWreck,
         const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer) and item.singleton:
            if const.ixLocationID in change or const.ixOwnerID in change or const.ixFlag in change:
                closeContainer = 1
                containerName = 'loot_%s' % item.itemID
        for cookie, wr in self.regs.items():
            ob = wr()
            if not ob or ob.destroyed:
                self.Unregister(cookie)
                continue
            if closeContainer == 1:
                if getattr(ob, 'id', 0) == item.itemID:
                    containerCookie = cookie
                    continue
                if getattr(ob, 'name', '') == containerName:
                    containerCookie = cookie
                    continue
            if hasattr(ob, 'invController'):
                if ob.invController is None:
                    continue
                wasHere = old.stacksize != 0 and ob.invController.IsItemHere(old)
                isHere = item.stacksize != 0 and ob.invController.IsItemHere(item)
            else:
                wasHere = old.stacksize != 0 and ob.IsItemHere(old)
                isHere = item.stacksize != 0 and ob.IsItemHere(item)
            try:
                if getattr(ob, 'OnInvChangeAny', None):
                    ob.OnInvChangeAny(item, change)
                if not wasHere and not isHere:
                    continue
                if wasHere and isHere and getattr(ob, 'UpdateItem', None):
                    ob.UpdateItem(item, change)
                elif wasHere and not isHere and getattr(ob, 'RemoveItem', None):
                    ob.RemoveItem(item)
                elif not wasHere and isHere and getattr(ob, 'AddItem', None):
                    ob.AddItem(item)
                if getattr(ob, 'OnInvChange', None):
                    ob.OnInvChange(item, change)
            except:
                self.Unregister(cookie)
                log.LogException('svc.inv')
                sys.exc_clear()

        if closeContainer == 1:
            if containerCookie is not None:
                self.Unregister(containerCookie)
            sm.GetService('window').CloseContainer(item.itemID)

    def Register(self, callbackObj):
        """
                'checkFn' is a function that takes an item and returns true iff
                the item is inside this container.
        
                'callbackObj' must define this function:
                    IsMine(item)
                            must return true iff the item is considered to be
                            inside the container
                Additionally, these callback functions will called if present:
                    OnInvChange(item, change)
                            some item has changed somehow
                            this is cumulative with the following callbacks
                    AddItem(item)
                            item has moved into this container
                    UpdateItem(item, change)
                            item has changed inside this container
                    RemoveItem(itemID)
                            item was removed from this container
        
        
                Callbacks won't get executed in this callbackObj until it has an
                attribute invReady with a true value. It is suggested that you turn
                invReady to true as soon as you have your initial listing.
        
                For convenience, callbacks on deco windows are not executed,
                and the registration is killed, if the window is dead. (Note that a
                callback object doesn't need be a window.)
        
        
        #        Return a (cookie, list) tuple, where 'cookie' is a value that can
        #        be passed to Unregister to cancel this registration, and list is
        #        the list of items that meet the conditions at this time.
                Currently return the cookie alone, as explained in the commented
                out paragraph above :). For correctness, it is recommended that
                you
                    1) register
                    2) get the initial set of items as normally
                    3) set self.invReady = 1 so you'll get updates as soon as you
                        have the initial state.
                """
        cookie = uthread.uniqueId() or uthread.uniqueId()
        self.LogInfo('Registering', cookie, callbackObj)
        self.regs[cookie] = _weakref.ref(callbackObj)
        return cookie

    def Unregister(self, cookie):
        if cookie in self.regs:
            del self.regs[cookie]
            self.LogInfo('Unregistered', cookie)
        else:
            log.LogWarn('inv.Unregister: Unknown cookie', cookie)

    def SetItemClipboard(self, nodes, copy = False):
        """ Cut / Copy / Paste functionality for invContainers """
        newNodes = []
        for node in nodes:
            if not self.IsOnClipboard(node.item.itemID):
                newNodes.append(node)

        self.itemClipboard = newNodes
        self.itemClipboardCopy = copy
        sm.ScatterEvent('OnInvClipboardChanged')

    @telemetry.ZONE_METHOD
    def PopItemClipboard(self):
        """ Cut / Copy / Paste functionality for invContainers """
        ret = self.itemClipboard
        if not self.itemClipboardCopy:
            self.itemClipboard = []
        sm.ScatterEvent('OnInvClipboardChanged')
        return (ret, self.itemClipboardCopy)

    @telemetry.ZONE_METHOD
    def ClearItemClipboard(self):
        if self.itemClipboard:
            self.itemClipboard = []
            sm.ScatterEvent('OnInvClipboardChanged')

    def IsOnClipboard(self, itemID):
        if self.itemClipboardCopy:
            return
        itemIDs = [ node.item.itemID for node in self.itemClipboard ]
        return itemID in itemIDs

    def GetTemporaryInvLocations(self):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None or not session.solarsystemid:
            self.tempInvLocations = set()
        else:
            toRemove = []
            for invName, itemID in self.tempInvLocations:
                if itemID not in bp.slimItems:
                    toRemove.append((invName, itemID))

            for invID in toRemove:
                self.tempInvLocations.remove(invID)

        return self.tempInvLocations

    def AddTemporaryInvLocation(self, invID):
        if invID not in self.tempInvLocations:
            self.tempInvLocations.add(invID)
            sm.ChainEvent('ProcessTempInvLocationAdded', invID)

    def RemoveTemporaryInvLocation(self, invID, byUser = False):
        if invID in self.tempInvLocations:
            self.tempInvLocations.remove(invID)
            sm.ChainEvent('ProcessTempInvLocationRemoved', invID, byUser)

    def OnBreadcrumbTextClicked(self, linkNum, windowID1, windowID2 = ()):
        wnd = form.Inventory.GetIfOpen((windowID1, windowID2))
        if wnd:
            wnd.OnBreadcrumbLinkClicked(linkNum)

    @telemetry.ZONE_METHOD
    def GetInvLocationTreeData(self, rootInvID = None):
        """ Returns a tree of all inventory locations currently accessible to the player """
        data = []
        shipID = util.GetActiveShip()
        typeID = None
        if shipID:
            if session.stationid2:
                activeShip = invCtrl.StationShips().GetActiveShip()
                if activeShip:
                    typeID = activeShip.typeID
            else:
                godmaLoc = sm.GetService('clientDogmaIM').GetDogmaLocation()
                if shipID in godmaLoc.dogmaItems:
                    typeID = godmaLoc.dogmaItems[shipID].typeID
            if typeID:
                data.append(TreeDataShip(clsName='ShipCargo', itemID=shipID, typeID=typeID, cmdName='OpenCargoHoldOfActiveShip'))
        if session.stationid2:
            shipsData = []
            activeShipID = util.GetActiveShip()
            singletonShips = [ ship for ship in invCtrl.StationShips().GetItems() if ship.singleton == 1 and ship.itemID != activeShipID ]
            cfg.evelocations.Prime([ ship.itemID for ship in singletonShips ])
            for ship in singletonShips:
                shipsData.append(TreeDataShip(clsName='ShipCargo', itemID=ship.itemID, typeID=ship.typeID))

            SortData(shipsData)
            data.append(TreeDataInv(clsName='StationShips', itemID=session.stationid2, children=shipsData, cmdName='OpenShipHangar'))
            containersData = GetContainerDataFromItems(invCtrl.StationItems().GetItems())
            data.append(TreeDataInv(clsName='StationItems', itemID=session.stationid2, children=containersData, cmdName='OpenHangarFloor'))
            if sm.GetService('corp').GetOffice() is not None:
                forceCollapsedMembers = not (rootInvID and rootInvID[0] in ('StationCorpMember', 'StationCorpMembers'))
                forceCollapsed = not (rootInvID and rootInvID[0] in ('StationCorpHangar', 'StationCorpHangars'))
                data.append(TreeDataStationCorp(forceCollapsed=forceCollapsed, forceCollapsedMembers=forceCollapsedMembers))
            deliveryRoles = const.corpRoleAccountant | const.corpRoleJuniorAccountant | const.corpRoleTrader
            if session.corprole & deliveryRoles > 0:
                data.append(TreeDataInv(clsName='StationCorpDeliveries', itemID=session.stationid2, cmdName='OpenCorpDeliveries'))
        elif session.solarsystemid:
            starbaseData = []
            defensesData = []
            industryData = []
            hangarData = []
            infrastrcutureData = []
            bp = sm.GetService('michelle').GetBallpark()
            if bp:
                for slimItem in bp.slimItems.values():
                    itemID = slimItem.itemID
                    groupID = slimItem.groupID
                    if HasCargoBayComponent(slimItem.typeID):
                        if slimItem.ownerID == session.charid or cfg.spaceComponentStaticData.GetAttributes(slimItem.typeID, CARGO_BAY).allowFreeForAll:
                            data.append(TreeDataInv(clsName='SpaceComponentInventory', itemID=itemID))
                    haveAccess = bool(slimItem) and (slimItem.ownerID == session.charid or slimItem.ownerID == session.corpid or session.allianceid and slimItem.allianceID == session.allianceid)
                    isAnchored = not bp.balls[itemID].isFree
                    if not haveAccess or not isAnchored:
                        continue
                    if groupID == const.groupControlTower:
                        towerData = [TreeDataInv(clsName='POSStrontiumBay', itemID=itemID), TreeDataInv(clsName='POSFuelBay', itemID=itemID)]
                        starbaseData.append(TreeDataCelestialParent(clsName='BaseCelestialContainer', itemID=itemID, children=towerData, iconName='ui_7_64_10'))
                    elif groupID == const.groupCorporateHangarArray:
                        hangarData.append(TreeDataPOSCorp(slimItem=slimItem))
                    elif groupID == const.groupAssemblyArray:
                        industryData.append(TreeDataPOSCorp(slimItem=slimItem))
                    elif groupID == const.groupMobileLaboratory:
                        industryData.append(TreeDataPOSCorp(slimItem=slimItem))
                    elif groupID == const.groupJumpPortalArray:
                        infrastrcutureData.append(TreeDataInv(clsName='POSJumpBridge', itemID=itemID))
                    elif groupID in (const.groupMobileMissileSentry, const.groupMobileProjectileSentry, const.groupMobileHybridSentry):
                        defensesData.append(TreeDataInv(clsName='POSStructureCharges', itemID=itemID))
                    elif groupID == const.groupMobileLaserSentry:
                        sentryData = [TreeDataInv(clsName='POSStructureChargeCrystal', itemID=itemID), TreeDataInv(clsName='POSStructureChargesStorage', itemID=itemID)]
                        defensesData.append(TreeDataCelestialParent(clsName='BaseCelestialContainer', itemID=itemID, children=sentryData, iconName='ui_13_64_9'))
                    elif groupID == const.groupShipMaintenanceArray:
                        hangarData.append(TreeDataInv(clsName='POSShipMaintenanceArray', itemID=itemID))
                    elif groupID == const.groupSilo:
                        industryData.append(TreeDataInv(clsName='POSSilo', itemID=itemID))
                    elif groupID == const.groupMobileReactor:
                        industryData.append(TreeDataInv(clsName='POSMobileReactor', itemID=itemID))
                    elif groupID == const.groupReprocessingArray:
                        industryData.append(TreeDataInv(clsName='POSRefinery', itemID=itemID))
                    elif groupID == const.groupCompressionArray:
                        industryData.append(TreeDataInv(clsName='POSCompression', itemID=itemID))
                    elif groupID in (const.groupConstructionPlatform, const.groupStationUpgradePlatform, const.groupStationImprovementPlatform):
                        industryData.append(TreeDataInv(clsName='POSConstructionPlatform', itemID=itemID))
                    elif groupID == const.groupPersonalHangar:
                        hangarData.append(TreeDataInv(clsName='POSPersonalHangar', itemID=itemID))

            if industryData:
                SortData(industryData)
                starbaseData.append(TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupIndustry'), children=industryData, icon='res:/UI/Texture/WindowIcons/industry.png'))
            if hangarData:
                SortData(hangarData)
                starbaseData.append(TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupStorage'), children=hangarData, icon='ui_26_64_13'))
            if infrastrcutureData:
                SortData(infrastrcutureData)
                starbaseData.append(TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupInfrastructure'), children=infrastrcutureData, icon='res:/ui/Texture/WindowIcons/sovereignty.png'))
            if defensesData:
                SortData(defensesData)
                starbaseData.append(TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupDefenses'), children=defensesData, icon='ui_5_64_13'))
            if starbaseData:
                data.append(TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/StarbaseStructures'), children=starbaseData, icon='ui_3_64_13'))
        return TreeData(children=data)

    def GetInvLocationTreeDataTemp(self, rootInvID = None):
        data = []
        tmpLocations = sm.GetService('inv').GetTemporaryInvLocations().copy()
        for invName, itemID in tmpLocations:
            if rootInvID in tmpLocations and rootInvID != (invName, itemID):
                continue
            if itemID == util.GetActiveShip():
                sm.GetService('inv').RemoveTemporaryInvLocation((invName, itemID))
                continue
            else:
                cls = GetTreeDataClassByInvName(invName)
                data.append(cls(invName, itemID=itemID, isRemovable=True))

        return TreeData(children=data)
