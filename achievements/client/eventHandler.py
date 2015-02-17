#Embedded file name: achievements/client\eventHandler.py
import weakref
from achievements.common.achievementConst import AchievementEventConst as eventConst
from eve.common.script.sys.idCheckers import IsStation

class EventHandler(object):
    __notifyevents__ = ['OnClientEvent_LockItem',
     'OnClientEvent_MoveWithDoubleClick',
     'OnClientEvent_Orbit',
     'OnClientEvent_MoveFromCargoToHangar',
     'OnClientEvent_ActivateModule',
     'OnClientEvent_Approach']

    def __init__(self, achievementSvc):
        sm.RegisterNotify(self)
        self.achievementSvc = weakref.proxy(achievementSvc)

    def LogAchievementEvent(self, eventType, amount = 1):
        self.achievementSvc.LogClientEvent(eventType, amount)

    def OnClientEvent_LockItem(self, slimItem):
        if slimItem.categoryID == const.categoryAsteroid:
            self.LogAchievementEvent(eventConst.ASTEROIDS_LOCK_CLIENT)
        elif self.IsHostileNPC(slimItem):
            self.LogAchievementEvent(eventConst.HOSTILE_NPC_LOCK_CLIENT)

    def OnClientEvent_MoveWithDoubleClick(self):
        self.LogAchievementEvent(eventConst.DOUBLE_CLICK_COUNT_CLIENT)

    def OnClientEvent_Orbit(self, slimItem):
        if slimItem.categoryID == const.categoryAsteroid:
            self.LogAchievementEvent(eventConst.ASTEROIDS_ORBIT_CLIENT)
        elif self.IsHostileNPC(slimItem):
            self.LogAchievementEvent(eventConst.HOSTILE_NPC_ORBIT_CLIENT)

    def OnClientEvent_Approach(self):
        self.LogAchievementEvent(eventConst.APPROACH_CLIENT)

    def OnClientEvent_MoveFromCargoToHangar(self, sourceID, destinationID, destinationFlag = None):
        if sourceID > const.minFakeItem:
            self.LogAchievementEvent(eventConst.ITEMS_LOOT_CLIENT)
            return
        if session.stationid2:
            sourceLocationItem = sm.GetService('invCache').FetchItem(sourceID, session.stationid2)
            if not sourceLocationItem:
                return
            if sourceLocationItem.categoryID == const.categoryShip and (IsStation(destinationID) or destinationFlag == const.flagHangar):
                self.LogAchievementEvent(eventConst.ITEMS_MOVE_FROM_CARGO_TO_HANGAR_CLIENT)

    def OnClientEvent_ActivateModule(self, effectID):
        if effectID in (const.effectProjectileFired, const.effectTargetAttack):
            self.LogAchievementEvent(eventConst.ACTIVATE_GUN)

    def UnregisterForEvents(self):
        sm.UnregisterNotify(self)

    def IsHostileNPC(self, slimItem):
        if slimItem.categoryID == const.categoryEntity and slimItem.typeID:
            val = sm.GetService('clientDogmaStaticSvc').GetTypeAttribute2(slimItem.typeID, const.attributeEntityBracketColour)
            if val >= 1:
                return True
        return False
