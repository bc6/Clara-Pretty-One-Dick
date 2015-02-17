#Embedded file name: eve/common/script/planet/entities\storagePin.py
"""
    This pin holds a fixed amount of resources. It cannot ever be activated
    normally; instead, it only activates on the addition or removal of resources
    from the pin.
    
    Whenever the pin receives or supplies resources, it is flagged as 'active'.
    When active, it attempts to supply other pins with its contents.
    The simulation will actively remove any distributed resources from
    this pin, which serves as a signal that resources are being supplied via this pin.
    
    When it is unable to supply any further resources, it deactivates.
"""
from eve.common.script.planet.entities.basePin import BasePin
import blue

class StoragePin(BasePin):
    __guid__ = 'planet.StoragePin'
    __slots__ = []

    def OnStartup(self, id, ownerID, latitude, longitude):
        pass

    def GetCycleTime(self):
        return 0

    def GetCapacity(self):
        return cfg.invtypes.Get(self.typeID).capacity

    def IsStorage(self):
        return True

    def CanActivate(self):
        return False

    def CanRun(self, runTime = None):
        return False

    def GetNextTransferTime(self):
        if self.lastRunTime is not None:
            return self.lastRunTime

    def CanTransfer(self, commodities, transferTime = None):
        for typeID, quantity in commodities.iteritems():
            if typeID not in self.contents:
                return False
            if quantity > self.contents[typeID]:
                return False

        tt = transferTime
        if transferTime is None:
            tt = blue.os.GetWallclockTime()
        nextTransferTime = self.GetNextTransferTime()
        if nextTransferTime is None or nextTransferTime <= tt:
            return True
        return False

    def ExecuteTransfer(self, runTime, expeditedTransferTime):
        self.lastRunTime = runTime + expeditedTransferTime

    def GetFreeSpace(self):
        capacity = self.GetCapacity()
        usedSpace = 0
        for typeID, qty in self.contents.iteritems():
            usedSpace += cfg.invtypes.Get(typeID).volume * qty

        return capacity - usedSpace


exports = {'planet.StoragePin': StoragePin}
