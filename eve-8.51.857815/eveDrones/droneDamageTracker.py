#Embedded file name: eveDrones\droneDamageTracker.py
"""
    Object that keeps track of damage of drone that in the drone bay
"""
from eveDrones.droneConst import DAMAGESTATE_NOT_READY
from inventorycommon.const import flagDroneBay, flagNone
import uthread2
import blue

class InBayDroneDamageTracker(object):
    __notifyevents__ = ['OnItemChange',
     'OnRepairDone',
     'OnDamageStateChange',
     'OnDroneControlLost']

    def __init__(self, dogmaLM):
        self.droneDamageStatesByDroneIDs = {}
        sm.RegisterNotify(self)
        self.fetchingInfoForDrones = set()
        self.clearTimestamp = None
        self.SetDogmaLM(dogmaLM)

    def SetDogmaLM(self, dogmaLM):
        self.dogmaLM = dogmaLM

    def FetchInBayDroneDamageToServer(self, droneIDs):
        droneIDsMissingDamage = self.FindDronesMissingDamageState(droneIDs)
        if not droneIDsMissingDamage:
            return
        self.fetchingInfoForDrones.update(droneIDsMissingDamage)
        callMadeTime = blue.os.GetSimTime()
        damageStateForDrones = self.dogmaLM.GetDamageStateItems(droneIDsMissingDamage)
        if not self.HasDictBeenClearedAfterCall(callMadeTime):
            damageStateDict = ConvertDroneStateToCorrectFormat(damageStateForDrones)
            self.droneDamageStatesByDroneIDs.update(damageStateDict)
        self.fetchingInfoForDrones.difference_update(droneIDsMissingDamage)

    def FindDronesMissingDamageState(self, droneIDs):
        droneIDsMissingDamage = {x for x in droneIDs if x not in self.droneDamageStatesByDroneIDs}
        return droneIDsMissingDamage - self.fetchingInfoForDrones

    def HasDictBeenClearedAfterCall(self, callMadeTime):
        if self.clearTimestamp and self.clearTimestamp > callMadeTime:
            return True
        else:
            return False

    def GetDamageStateForDrone(self, droneID):
        if self.IsDroneDamageReady(droneID):
            return self.droneDamageStatesByDroneIDs.get(droneID, None)
        droneIDsMissingDamage = self.FindDronesMissingDamageState([droneID])
        if droneIDsMissingDamage:
            uthread2.StartTasklet(self.FetchInBayDroneDamageToServer, droneIDsMissingDamage)
        return DAMAGESTATE_NOT_READY

    def IsDroneDamageReady(self, droneID):
        return droneID in self.droneDamageStatesByDroneIDs

    def OnItemChange(self, change, *args):
        if change.itemID not in self.droneDamageStatesByDroneIDs:
            return
        if change.flagID not in (flagDroneBay, flagNone):
            del self.droneDamageStatesByDroneIDs[change.itemID]

    def OnDroneControlLost(self, droneID):
        self.droneDamageStatesByDroneIDs.pop(droneID, None)

    def OnRepairDone(self, itemIDs, *args):
        for itemID in itemIDs:
            self.droneDamageStatesByDroneIDs.pop(itemID, None)

    def OnDamageStateChange(self, itemID, damageState):
        droneDamageInfo = self.droneDamageStatesByDroneIDs.get(itemID, None)
        if droneDamageInfo is None:
            return
        timestamp = blue.os.GetSimTime()
        droneDamageInfo.UpdateInfo(timestamp, damageState)


def ConvertDroneStateToCorrectFormat(damageStateForDrones):
    newDroneDamageDict = {}
    for itemID, ds in damageStateForDrones.iteritems():
        shieldInfo = ds[0]
        shieldHealth = shieldInfo[0]
        shieldTau = shieldInfo[1]
        timestamp = shieldInfo[2]
        d = DroneDamageObject(itemID, shieldTau, timestamp, shieldHealth, ds[1], ds[2])
        newDroneDamageDict[itemID] = d

    return newDroneDamageDict


class DroneDamageObject:

    def __init__(self, itemID, shieldTau, timestamp, shieldHealth, armorHealth, hullHealth):
        self.itemID = itemID
        self.shieldTau = shieldTau
        self.timestamp = timestamp
        self.shieldHealth = shieldHealth
        self.armorHealth = armorHealth
        self.hullHealth = hullHealth

    def UpdateInfo(self, timestamp, damageValues):
        self.timestamp = timestamp
        self.shieldHealth = damageValues[0]
        self.armorHealth = damageValues[1]
        self.hullHealth = damageValues[2]

    def GetInfoInMichelleFormat(self):
        return [(self.shieldHealth, self.shieldTau, self.timestamp), self.armorHealth, self.hullHealth]
