#Embedded file name: dogma/mocks\mockDogmaLocation.py
from collections import defaultdict
from itertoolsext import Bundle
from inventorycommon.const import categoryShip, categoryModule, groupProjectileWeapon, categoryStructure
import dogma.const

class MockDogmaLocation(object):

    def __init__(self, isSolarsystem = True):
        self.isSolarsystem = isSolarsystem
        self.dogmaItems = {}
        self.pilotsByShipID = {}
        self.fittedItems = defaultdict(dict)
        self.typeAttributes = defaultdict(dict)
        self.effectsByType = defaultdict(dict)
        self.onlineEffects = {dogma.const.effectOnline: True,
         dogma.const.effectOnlineForStructures: True}
        self.dogmaStaticMgr = self._GetDogmaStaticMgr()

    def AddShip(self, typeID, ownerID, groupID = 1000):
        itemID, _ = self._AddGenericItem(typeID, groupID, categoryShip, ownerID=ownerID, GetFittedItems=lambda : self._GetFittedItems(itemID))
        if ownerID is not None:
            self.SetPilot(ownerID, itemID)
        return itemID

    def AddStructure(self, typeID, groupID = 1001):
        itemID, _ = self._AddGenericItem(typeID, groupID, categoryStructure, ownerID=None)
        return itemID

    def AddModuleToShip(self, typeID, locationID, flagID, groupID = 1):
        itemID, module = self._AddGenericItem(typeID, groupID, categoryModule, locationID=locationID, ownerID=self.dogmaItems[locationID].ownerID, flagID=flagID, GetEnvironmentInfo=lambda : self._GetEnvironmentInfo(itemID))
        self.dogmaItems[itemID] = module
        self.fittedItems[locationID][itemID] = module
        return itemID

    def _AddGenericItem(self, typeID, groupID, categoryID, **kwargs):
        itemID = self._GetNewID()
        item = Bundle(itemID=itemID, typeID=typeID, groupID=groupID, categoryID=categoryID, **kwargs)
        self.dogmaItems[itemID] = item
        return (itemID, item)

    def AddProjectileToShip(self, typeID, locationID, flagID):
        return self.AddModuleToShip(typeID, locationID, flagID, groupProjectileWeapon)

    def AddTargetableEffect(self, effectID, typeID):
        self.AddEffect(effectID, typeID, dogma.const.dgmEffTarget)

    def SetPilot(self, pilotID, shipID):
        self.pilotsByShipID[shipID] = pilotID

    def AddEffect(self, effectID, typeID, effectCategory):
        effect = Bundle(effectCategory=effectCategory)
        self.dogmaStaticMgr.effects[effectID] = effect
        self.effectsByType[typeID][effectID] = effect

    def SetTypeAttribute(self, typeID, attributeID):
        pass

    def LoadItem(self, itemID, *args, **kwargs):
        pass

    def GetDogmaItem(self, itemID):
        return self.dogmaItems[itemID]

    def GetItem(self, itemID):
        return self.dogmaItems[itemID]

    def GetPilot(self, shipID):
        return self.pilotsByShipID[shipID]

    def GetSlaveModules(self, shipID, moduleID):
        return []

    def StartEffect(self, *args, **kwargs):
        pass

    def _GetNewID(self):
        try:
            return max(self.dogmaItems.iterkeys()) + 1
        except ValueError:
            return 1

    def _GetEnvironmentInfo(self, itemID):
        item = self.dogmaItems[itemID]
        return Bundle(charID=item.ownerID, itemID=item.itemID, shipID=item.locationID, otherID=None)

    def _GetFittedItems(self, shipID):
        return self.fittedItems[shipID]

    def _GetDogmaStaticMgr(self):
        return Bundle(effects={}, crystalModuleGroupIDs={}, effectsByType=self.effectsByType, GetTypeAttribute2=lambda typeID, attributeID: self.typeAttributes[typeID].get(attributeID, 0))


class MockServerDogmaLocation(MockDogmaLocation):

    def __init__(self):
        super(MockServerDogmaLocation, self).__init__()
        self.__balls = {}
        self.inventory2 = self._GetInventory2()
        self.ballpark = self._GetBallpark()

    def AddShip(self, typeID, ownerID, groupID = 1000):
        itemID = super(MockServerDogmaLocation, self).AddShip(typeID, ownerID, groupID=groupID)
        self.__balls[itemID] = Bundle(structures=[])
        return itemID

    def AddStructure(self, typeID, groupID = 1001):
        itemID = super(MockServerDogmaLocation, self).AddStructure(typeID, groupID=groupID)
        self.__balls[itemID] = Bundle()
        return itemID

    def _GetInventory2(self):
        return Bundle(IsPrimed=lambda itemID: itemID in self.dogmaItems, GetItem=lambda itemID: self.GetItem(itemID))

    def _GetBallpark(self):
        return Bundle(HasBall=lambda ballID: ballID in self.__balls, IsWarping=lambda ballID: False, IsCloaked=lambda ballID: False, IsFrozen=lambda ballID: False, GetBall=self._GetBall, AbortSafeLogoff=lambda *args, **kwargs: None, GetInvulnerableState=lambda ballID: None)

    def _GetBall(self, ballID):
        return self.__balls[ballID]
