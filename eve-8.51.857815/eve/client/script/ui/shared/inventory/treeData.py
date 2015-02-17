#Embedded file name: eve/client/script/ui/shared/inventory\treeData.py
from carbon.common.lib import telemetry
from eve.client.script.ui.control.treeData import TreeData
from eve.client.script.ui.shared.inventory.invCommon import CONTAINERGROUPS, SortData
import invCont
import invCtrl
from inventorycommon.util import IsModularShip
import localization
import util
import uix
NO_DISTANCE_SHOWN = ['POSCorpHangar',
 'POSStrontiumBay',
 'POSFuelBay',
 'POSStructureChargesStorage',
 'POSStructureChargeCrystal']

class TreeDataInv(TreeData):

    def __init__(self, clsName, parent = None, children = None, label = None, isRemovable = False, cmdName = None, iconName = None, **kw):
        TreeData.__init__(self, parent=parent, children=children, label=label, isRemovable=isRemovable, **kw)
        self.clsName = clsName
        self.cmdName = cmdName
        self.iconName = iconName
        self.invController = getattr(invCtrl, clsName)(**kw)

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        if self._label:
            return self._label
        else:
            return self.invController.GetName()

    @telemetry.ZONE_METHOD
    def GetLabelWithDistance(self):
        label = self.GetLabel()
        if session.solarsystemid is None or self.clsName in NO_DISTANCE_SHOWN or self.invController.itemID == util.GetActiveShip():
            return label
        if session.solarsystemid:
            ball = sm.GetService('michelle').GetBallpark().GetBall(self.invController.itemID)
            if not ball:
                return label
            dist = util.FmtDist(ball.surfaceDist, 1)
            return '%s <color=#66FFFFFF>%s</color>' % (label, dist)
        return label

    def GetIcon(self):
        if self.iconName:
            return self.iconName
        return self.invController.GetIconName()

    def GetMenu(self):
        m = self.invController.GetMenu()
        if self.invController.IsInRange():
            m += [(localization.GetByLabel('UI/Inventory/OpenInNewWindow'), self.OpenNewWindow, ())]
        return m

    def GetHint(self):
        if self.cmdName:
            shortcut = uicore.cmd.GetShortcutStringByFuncName(self.cmdName)
            if shortcut:
                return localization.GetByLabel('UI/Inventory/ShortcutBrackets', shortcut=shortcut)

    def GetID(self):
        return self.invController.GetInvID()

    def GetItemID(self):
        return self.invController.itemID

    def GetInvCont(self, **kw):
        kw.update(self._kw)
        return getattr(invCont, self.clsName)(**kw)

    def HasInvCont(self):
        return True

    def OpenNewWindow(self, openDragging = False):
        from eve.client.script.ui.shared.inventory.invWindow import Inventory
        return Inventory.OpenOrShow(invID=self.GetID(), usePrimary=False, toggle=True, openDragging=openDragging, **self._kw)

    def IsForceCollapsed(self):
        return not self.invController.IsPrimed()

    def IsDraggable(self):
        return self.invController.IsInRange()

    def CheckCanQuery(self):
        if self.clsName == 'StationContainer':
            return self.GetParent().CheckCanTake()
        return self.invController.CheckCanQuery()

    def CheckCanTake(self):
        return self.invController.CheckCanTake()


class TreeDataPlasticWrap(TreeDataInv):

    def GetChildren(self):
        """ Plastic wraps can contain other containers """
        data = GetContainerDataFromItems(self.invController.GetItems(), parent=self)
        if not data:
            data = [TreeData(parent=self, label=localization.GetByLabel('UI/Inventory/NoNestedContainers'), id='none_%s' % self.invController.itemID)]
        return data

    def HasChildren(self):
        return True


def GetSharedBayHint(invController):
    if invController.itemID != util.GetActiveShip():
        hint = cfg.evelocations.Get(invController.itemID).name
        ownerID = invController.GetOwnerID()
        if ownerID:
            hint += '<br>%s' % cfg.eveowners.Get(ownerID).name
        return hint


class TreeDataFleetHangar(TreeDataInv):

    def GetChildren(self):
        """ Fleet hangars can contain other containers """
        return GetContainerDataFromItems(self.invController.GetItems(), parent=self)

    def HasChildren(self):
        for item in self.invController.GetItems():
            if item.groupID in CONTAINERGROUPS:
                return True

        return False

    def GetHint(self):
        return GetSharedBayHint(self.invController)


class TreeDataShipMaintenanceBay(TreeDataInv):

    def GetHint(self):
        return GetSharedBayHint(self.invController)


class TreeDataCelestialParent(TreeDataInv):

    def HasInvCont(self, **kw):
        return False

    def IsForceCollapsed(self):
        return False


class TreeDataInvFolder(TreeData):
    """ Represents a tree node that is not an inv location, but a folder container inv locations """

    def OpenNewWindow(self, openDragging = False):
        from eve.client.script.ui.shared.inventory.invWindow import Inventory
        return Inventory.OpenOrShow(invID=self.GetID(), usePrimary=False, toggle=True, openDragging=openDragging, iconNum=self.GetIcon(), **self._kw)

    def GetMenu(self):
        return [(localization.GetByLabel('UI/Inventory/OpenInNewWindow'), self.OpenNewWindow, ())]

    def HasChildren(self):
        return True

    @telemetry.ZONE_METHOD
    def GetLabelWithDistance(self):
        return self.GetLabel()

    def IsDraggable(self):
        return True


class TreeDataPOSCorp(TreeDataInvFolder):

    def __init__(self, slimItem, **kw):
        TreeData.__init__(self, **kw)
        self.slimItem = slimItem
        self.invController = invCtrl.POSCorpHangar(self.slimItem.itemID)

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        return uix.GetSlimItemName(self.slimItem)

    @telemetry.ZONE_METHOD
    def GetLabelWithDistance(self):
        label = self.GetLabel()
        bp = sm.GetService('michelle').GetBallpark()
        ball = bp.GetBall(self.invController.itemID)
        if not ball:
            return label
        dist = util.FmtDist(ball.surfaceDist, 1)
        return '%s <color=#66FFFFFF>%s</color>' % (label, dist)

    def GetIcon(self):
        return 'res:/ui/Texture/WindowIcons/corporation.png'

    def GetItemID(self):
        return self.slimItem.itemID

    def GetID(self):
        return ('POSCorpHangars', self.slimItem.itemID)

    def GetMenu(self):
        m = TreeDataInvFolder.GetMenu(self)
        m += sm.GetService('menu').GetMenuFormItemIDTypeID(self.slimItem.itemID, self.slimItem.typeID)
        return m

    def GetChildren(self):
        data = []
        itemID = self.slimItem.itemID
        for divID in xrange(7):
            data.append(TreeDataInv(parent=self, clsName='POSCorpHangar', itemID=itemID, divisionID=divID))

        return data

    def IsDraggable(self):
        return self.invController.IsInRange()


class TreeDataShip(TreeDataInv):

    def __init__(self, clsName, typeID, **kw):
        TreeDataInv.__init__(self, clsName, **kw)
        self.typeID = typeID

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        shipName = TreeDataInv.GetLabel(self)
        return localization.GetByLabel('UI/Inventory/ShipNameAndType', shipName=shipName, typeName=cfg.invtypes.Get(self.typeID).name)

    def GetHint(self):
        hint = TreeDataInv.GetHint(self)
        typeName = cfg.invtypes.Get(self.typeID).name
        if hint:
            return typeName + hint
        else:
            return typeName

    def HasChildren(self):
        return True

    def IsForceCollapsed(self):
        if self.invController.itemID == util.GetActiveShip():
            return False
        return TreeDataInv.IsForceCollapsed(self)

    def GetIcon(self):
        return self.invController.GetIconName(highliteIfActive=True)

    def GetChildren(self):
        shipData = []
        itemID = self.invController.itemID
        typeID = self.typeID
        if itemID == util.GetActiveShip():
            cmdName = 'OpenDroneBayOfActiveShip'
        else:
            cmdName = None
        godmaType = sm.GetService('godma').GetType(typeID)
        if godmaType.droneCapacity or IsModularShip(typeID):
            shipData.append(TreeDataInv(parent=self, clsName='ShipDroneBay', itemID=itemID, cmdName=cmdName))
        godmaSM = sm.GetService('godma').GetStateManager()
        if bool(godmaSM.GetType(typeID).hasShipMaintenanceBay):
            shipData.append(TreeDataShipMaintenanceBay(parent=self, clsName='ShipMaintenanceBay', itemID=itemID))
        if bool(godmaSM.GetType(typeID).hasFleetHangars):
            shipData.append(TreeDataFleetHangar(parent=self, clsName='ShipFleetHangar', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialFuelBayCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipFuelBay', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialOreHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipOreHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialGasHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipGasHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialMineralHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipMineralHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialSalvageHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipSalvageHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialShipHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialSmallShipHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipSmallShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialMediumShipHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipMediumShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialLargeShipHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipLargeShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialIndustrialShipHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipIndustrialShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialAmmoHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipAmmoHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialCommandCenterHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipCommandCenterHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialPlanetaryCommoditiesHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipPlanetaryCommoditiesHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialQuafeHoldCapacity):
            shipData.append(TreeDataInv(parent=self, clsName='ShipQuafeHold', itemID=itemID))
        invController = invCtrl.ShipCargo(itemID=itemID)
        shipData += GetContainerDataFromItems(invController.GetItems(), parent=self)
        if not shipData:
            shipData.append(TreeData(parent=self, label=localization.GetByLabel('UI/Inventory/NoAdditionalBays'), id='none_%s' % itemID))
        return shipData


class TreeDataStationCorp(TreeDataInvFolder):

    def __init__(self, forceCollapsed = True, forceCollapsedMembers = True, *args):
        self.itemID = sm.GetService('corp').GetOffice().itemID
        self.forceCollapsedMembers = forceCollapsedMembers
        self.forceCollapsed = forceCollapsed
        TreeDataInvFolder.__init__(self, *args)

    def GetChildren(self):
        if self._children:
            return self._children
        corpData = []
        for divID in xrange(7):
            invController = invCtrl.StationCorpHangar(self.itemID, divID)
            divData = []
            for item in invController.GetItems():
                if item.groupID in CONTAINERGROUPS and item.singleton:
                    divData.append(TreeDataInv(clsName='StationContainer', itemID=item.itemID, typeID=item.typeID))

            cfg.evelocations.Prime([ d.invController.itemID for d in divData ])
            SortData(divData)
            corpData.append(TreeDataInv(parent=self, clsName='StationCorpHangar', itemID=self.itemID, divisionID=divID, children=divData))

        securityOfficerRoles = session.corprole & const.corpRoleSecurityOfficer == const.corpRoleSecurityOfficer
        if securityOfficerRoles:
            memberData = sm.GetService('corpui').GetMemberHangarsData().keys()
            cfg.eveowners.Prime([ member[1] for member in memberData ])
            corpData.append(TreeDataCorpMembers(parent=self, memberData=memberData, groupChildren=True, forceCollapsed=self.forceCollapsedMembers))
        self._children = corpData
        return corpData

    def HasChildren(self):
        return True

    def IsForceCollapsed(self):
        """ Force collapse if we haven't primed the inventory location """
        if self._children or not self.forceCollapsed:
            return False
        invController = invCtrl.StationCorpHangar(self.itemID, 0)
        return not invController.IsPrimed()

    def GetIcon(self):
        return 'res:/ui/Texture/WindowIcons/corpHangar.png'

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        return localization.GetByLabel('UI/Inventory/CorporationHangars')

    def GetID(self):
        return ('StationCorpHangars', self.itemID)


class TreeDataCorpMembers(TreeDataInvFolder):

    def __init__(self, memberData, groupChildren = False, label = None, forceCollapsed = True, *args, **kw):
        if label is None:
            label = localization.GetByLabel('UI/Inventory/MemberHangars')
        self.memberData = memberData
        self.groupChildren = groupChildren
        self.memberData.sort(key=lambda x: cfg.eveowners.Get(x[0]).name.lower())
        self.forceCollapsed = forceCollapsed
        TreeData.__init__(self, label=label, *args, **kw)

    def GetID(self):
        return ('StationCorpMembers', self.GetLabel())

    def GetChildren(self):
        """
        Returns corp members as a flat list if fewer than 50, or grouped alphabetically otherwise
        """
        if self._children:
            return self._children
        data = []
        maxNumPerLevel = 50
        numMembers = len(self.memberData)
        if not self.groupChildren or numMembers <= maxNumPerLevel:
            for itemID, ownerID in self.memberData:
                if itemID == session.charid:
                    continue
                if util.IsDustCharacter(itemID):
                    continue
                if itemID == ownerID:
                    data.append(TreeDataInv(parent=self, clsName='StationCorpMember', itemID=itemID, ownerID=ownerID))
                else:
                    data.append(TreeDataInv(parent=self, clsName='StationOwnerView', itemID=itemID, ownerID=ownerID))

        else:
            currLetter = None
            levelData = []
            for itemID, ownerID in self.memberData:
                letter = cfg.eveowners.Get(ownerID).name[0].upper()
                if letter != currLetter:
                    if levelData:
                        data.append(TreeDataCorpMembers(label=currLetter, memberData=levelData))
                    currLetter = letter
                    levelData = []
                levelData.append((itemID, ownerID))

            if levelData:
                data.append(TreeDataCorpMembers(label=currLetter, memberData=levelData))
        if not data:
            data.append(TreeData(label=localization.GetByLabel('UI/Inventory/NoCorpHangars')))
        self.forceCollapsed = False
        self._children = data
        return data

    def IsForceCollapsed(self):
        return self.forceCollapsed

    def GetIcon(self):
        return 'res:/ui/Texture/WindowIcons/corporationmembers.png'


def GetContainerDataFromItems(items, parent = None):
    """ Returns a list of tree data for all the items that represent an inventory location (a container) """
    data = []
    for item in items:
        if item.typeID == const.typePlasticWrap and item.singleton:
            data.append(TreeDataPlasticWrap(parent=parent, clsName='StationContainer', itemID=item.itemID, typeID=item.typeID))
        elif item.groupID in CONTAINERGROUPS and item.singleton:
            data.append(TreeDataInv(parent=parent, clsName='StationContainer', itemID=item.itemID, typeID=item.typeID))

    cfg.evelocations.Prime([ d.invController.itemID for d in data ])
    SortData(data)
    return data


def GetTreeDataClassByInvName(invName):
    """ Returs tree data class given invController name """
    if invName == 'ShipFleetHangar':
        return TreeDataFleetHangar
    elif invName == 'ShipMaintenanceBay':
        return TreeDataShipMaintenanceBay
    else:
        return TreeDataInv
