#Embedded file name: achievements/client\achievementSvc.py
__author__ = 'aevar'
import service
from achievements.common.achievementLoader import AchievementLoader
import blue
from notifications.common.notification import SimpleNotification
import localization

class AchievementTrackerClientService(service.Service):
    __guid__ = 'svc.achievementSvc'
    service = 'svc.achievementSvc'
    __startupdependencies__ = ['machoNet']
    __dependencies__ = ['machoNet']
    __notifyevents__ = ['OnServerAchievementUnlocked', 'OnAchievementsReset', 'OnSessionChanged']
    __slashhook__ = True

    def cmd_achievement_reset(self, p):
        from eve.devtools.script.svc_slash import Error as SlashError
        self.remoteService.Reset()

    def Run(self, memStream = None, remoteService = None, scatterService = sm):
        self.scatterService = scatterService
        self.remoteService = None
        self.allAchievements = self.LoadAchievements()
        self._debugStatsForCharacter = None
        self.completedIDs = set()
        self.hasAllData = False

    def GetDebugStatsFromCharacter(self, force = False):
        if self._debugStatsForCharacter is None or force == True:
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
        sm.ScatterEvent('OnAchievementChanged')

    def OnServerAchievementUnlocked(self, achievementsInfo):
        achievementSet = achievementsInfo['achievementSet']
        for achievementID in achievementSet:
            achievement = self.allAchievements[achievementID]
            self.scatterService.ScatterEvent('OnClientAchievementUnlocked', achievement)
            if achievement.notificationText:
                subject = achievement.notificationText
            else:
                subject = localization.GetByLabel('UI/Achievements/AchievementCompleted', achievementName=achievement.name)
            eve.Message('SwooshUp')
            newNotification = SimpleNotification(subject=subject, created=blue.os.GetWallclockTime(), notificationID=1, notificationTypeID=29, senderID=1)
            self.completedIDs.add(achievementID)
            self.allAchievements[achievementID].completed = True
            sm.ScatterEvent('OnNewNotificationReceived', newNotification)
            sm.ScatterEvent('OnAchievementChanged')

    def FetchMyAchievementStatus(self):
        self.completedIDs = self.remoteService.GetCompletedAchievements()
        self.UpdateAchievementList()
        self.hasAllData = True
        self.ScatterStatus()

    def ScatterStatus(self):
        self.scatterService.ScatterEvent('OnAchievementsReady', self.allAchievements)

    def UpdateAchievementList(self):
        for achievementID in self.completedIDs:
            self.allAchievements[achievementID].completed = True

    def LoadAchievements(self):
        return AchievementLoader().GetAchievements()

    def IsAchievementCompleted(self, achievementID):
        return achievementID in self.completedIDs

    def OnSessionChanged(self, isRemote, session, change):
        if 'charid' in change and not self.HasData():
            if self.remoteService is None:
                self.remoteService = sm.RemoteSvc('achievementTrackerMgr')
            self.FetchMyAchievementStatus()
