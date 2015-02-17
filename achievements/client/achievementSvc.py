#Embedded file name: achievements/client\achievementSvc.py
from achievements.client.eventHandler import EventHandler
from achievements.common import GetNewAchievements, GetClientAchievements, GetAchievementsByEventsDict
from achievements.common.achievementController import StatsTracker
from achievements.common.achievementGroups import GetNextAchievementGroup, GetFirstIncompleteAchievementGroup, GetGroupForAchievement
from achievements.common.achievementLoader import AchievementLoader
from achievements.common.achievementGroups import GetAchievementGroup
import service
import blue
import eve.common.script.util.notificationconst as notificationConst
from notifications.common.formatters.achievementTask import AchievementTaskFormatter
from notifications.common.formatters.opportunity import AchievementOpportunityFormatter
import threadutils
import gatekeeper
import gatekeeper.gatekeeperConst as gkConst

class AchievementTrackerClientService(service.Service):
    __guid__ = 'svc.achievementSvc'
    service = 'svc.achievementSvc'
    __startupdependencies__ = ['machoNet']
    __dependencies__ = ['machoNet']
    __notifyevents__ = ['OnServerAchievementUnlocked',
     'OnAchievementsReset',
     'OnSessionChanged',
     'ProcessShutdown']
    _debugStatsForCharacter = None
    remoteService = None
    hasAllData = False
    achievementsEnabled = False

    def Run(self, memStream = None, remoteService = None, scatterService = sm):
        self.scatterService = scatterService
        self.eventHandler = EventHandler(self)
        self.allAchievements = self.LoadAchievements(getDisabled=True)
        self.clientAchievements = GetClientAchievements(self.allAchievements)
        self.achievementsByEventsDict = GetAchievementsByEventsDict(self.clientAchievements)
        self.clientStatsTracker = StatsTracker()
        self.completedDict = {}
        self.scatterService.ScatterEvent('OnAchievementsDataInitialized')

    def UpdateEnabledStatus(self):
        self.achievementsEnabled = gatekeeper.user.IsInCohort(gkConst.cohortPirateUnicornsNPETwo)

    def IsEnabled(self):
        return self.achievementsEnabled

    def GetDebugStatsFromCharacter(self, force = False):
        if self._debugStatsForCharacter is None or force is True:
            self._debugStatsForCharacter = self.remoteService.GetDebugStatsFromCharacter(session.charid)
        return self._debugStatsForCharacter

    def HasData(self):
        return self.hasAllData

    def GetFullAchievementList(self):
        return self.allAchievements.values()

    def OnAchievementsReset(self):
        for eachAchievement in self.allAchievements.itervalues():
            eachAchievement.completed = False

        self.FetchMyAchievementStatus()
        self.scatterService.ScatterEvent('OnAchievementsDataInitialized')
        self.AuraIntroduction()

    def ResetAllForCharacter(self):
        from achievements.client.auraAchievementWindow import AchievementAuraWindow
        self.remoteService.ResetAllForChar()
        AchievementAuraWindow.CloseIfOpen()
        settings.char.ui.Set('opportunities_aura_introduced', False)
        self.SetActiveAchievementGroupID(None)

    def SetActiveAchievementGroupID(self, groupID, emphasize = False):
        if groupID != self.GetActiveAchievementGroupID():
            settings.char.ui.Set('opportunities_active_group', groupID)
            sm.ScatterEvent('OnAchievementActiveGroupChanged', groupID, emphasize)

    def GetActiveAchievementGroupID(self):
        return settings.char.ui.Get('opportunities_active_group', None)

    def GetAchievementTask(self, achievementTaskID):
        return self.allAchievements.get(achievementTaskID, None)

    def OnServerAchievementUnlocked(self, achievementsInfo):
        achievementDict = achievementsInfo['achievementDict']
        self.HandleAchievementsUnlocked(achievementDict)

    def HandleAchievementsUnlocked(self, achievementDict):
        self.MarkAchievementAsCompleted(achievementDict)
        if not self.IsEnabled():
            return
        for achievementID in achievementDict:
            if achievementID not in self.allAchievements:
                continue
            achievement = self.allAchievements[achievementID]
            self.SendAchievementNotification(achievementID)
            self.SendOpportunityNotification(achievementID)
            activeGroupID = self.GetActiveAchievementGroupID()
            if activeGroupID and self.IsAchievementInGroup(achievementID, activeGroupID):
                activeGroupCompleted = self.IsCurrentGroupCompleted()
            else:
                activeGroupCompleted = False
            if activeGroupCompleted:
                from achievements.client.auraAchievementWindow import AchievementAuraWindow
                auraWindow = AchievementAuraWindow.GetIfOpen()
                if not auraWindow:
                    AchievementAuraWindow.Open()
            sm.ScatterEvent('OnAchievementChanged', achievement, activeGroupCompleted=activeGroupCompleted)

    def MarkAchievementAsCompleted(self, achievementDict):
        for achievementID, timestamp in achievementDict.iteritems():
            if achievementID not in self.allAchievements:
                continue
            self.completedDict[achievementID] = timestamp
            self.allAchievements[achievementID].completed = True

    def SendAchievementNotification(self, achievementID):
        notificationData = AchievementTaskFormatter.MakeData(achievementID)
        self.SendNotification(notificationData, notificationConst.notificationTypeAchievementTaskFinished)

    def SendOpportunityNotification(self, achievementID):
        group = GetGroupForAchievement(achievementID)
        if not group:
            return
        if group.IsCompleted():
            notificationData = AchievementOpportunityFormatter.MakeData(group.groupID)
            self.SendNotification(notificationData, notificationConst.notificationTypeOpportunityFinished)

    def SendNotification(self, notificationData, notificationType):
        sm.ScatterEvent('OnNotificationReceived', 123, notificationType, session.charid, blue.os.GetWallclockTime(), data=notificationData)

    def FetchMyAchievementStatus(self):
        achievementAndEventInfo = self.remoteService.GetCompletedAchievementsAndClientEventCount()
        self.completedDict = achievementAndEventInfo['completedDict']
        self.PopulateEventHandler(achievementAndEventInfo['eventDict'])
        self.UpdateAchievementList()
        self.hasAllData = True

    def PopulateEventHandler(self, eventCountDict):
        for eventName, eventCount in eventCountDict.iteritems():
            if eventCount < 1:
                self.clientStatsTracker.statistics[eventName] = 0
            else:
                self.clientStatsTracker.LogStatistic(eventName, eventCount, addToUnlogged=False)

    def UpdateAchievementList(self):
        for achievementID in self.completedDict:
            if achievementID in self.allAchievements:
                self.allAchievements[achievementID].completed = True

    def LoadAchievements(self, getDisabled = False):
        return AchievementLoader().GetAchievements(getDisabled=getDisabled)

    def IsAchievementCompleted(self, achievementID):
        return achievementID in self.completedDict

    def IsAchievementInGroup(self, achievementID, groupID):
        achievementGroup = GetAchievementGroup(groupID)
        return achievementGroup.HasAchievement(achievementID)

    def IsCurrentGroupCompleted(self):
        currentGroupID = self.GetActiveAchievementGroupID()
        if not currentGroupID:
            return False
        achievementGroup = GetAchievementGroup(currentGroupID)
        return achievementGroup.IsCompleted()

    def OnSessionChanged(self, isRemote, session, change):
        if 'charid' in change and not self.HasData():
            if self.remoteService is None:
                self.remoteService = sm.RemoteSvc('achievementTrackerMgr')
            self.FetchMyAchievementStatus()
            self.UpdateEnabledStatus()
        if 'stationid' in change and change['stationid'][1] or 'solarsystemid' in change and change['solarsystemid'][1]:
            self.AuraIntroduction()

    def ProcessShutdown(self):
        try:
            self.UpdateClientAchievementsAndCountersOnServer()
        except Exception as e:
            self.LogError('Failed at storing client achievement events, e = ', e)

    def AuraIntroduction(self):
        if not self.IsEnabled():
            return
        if not settings.char.ui.Get('opportunities_aura_introduced', False):
            nextIncompleteGroup = GetFirstIncompleteAchievementGroup()
            if nextIncompleteGroup:
                from achievements.client.auraAchievementWindow import AchievementAuraWindow
                AchievementAuraWindow.Open()

    def LogClientEvent(self, eventName, value = 1):
        achievementsWithEvent = self.achievementsByEventsDict.get(eventName, set())
        achievementsLeft = achievementsWithEvent - set(self.completedDict.keys())
        if not achievementsLeft:
            return
        self.clientStatsTracker.LogStatistic(eventName, value, addToUnlogged=False)
        achievementsWereCompleted = self.CheckAchievementStatus()
        if not achievementsWereCompleted:
            self.UpdateClientAchievementsAndCountersOnServer_throttled(self)

    def CheckAchievementStatus(self):
        newAchievementSet = self.GetNewAchievementsForCharacter()
        if newAchievementSet:
            self.HandleAchievementsUnlocked(newAchievementSet)
            self.UpdateClientAchievementsAndCountersOnServer()
            return True
        return False

    @threadutils.throttled(180)
    def UpdateClientAchievementsAndCountersOnServer_throttled(self):
        self.UpdateClientAchievementsAndCountersOnServer()

    def UpdateClientAchievementsAndCountersOnServer(self):
        stats = self.clientStatsTracker.GetStatistics()
        self.remoteService.UpdateClientAchievmentsAndCounters(self.completedDict, dict(stats))

    def GetNewAchievementsForCharacter(self):
        return GetNewAchievements(self.clientAchievements, self.completedDict, self.clientStatsTracker)
