#Embedded file name: notifications/client/development\achievementHistoryProvider.py
from achievements.common.achievementGroups import GetAchievementGroups
import eve.common.script.util.notificationconst as notificationConst
from notifications.common.formatters.achievementTask import AchievementTaskFormatter
from notifications.common.formatters.opportunity import AchievementOpportunityFormatter
from notifications.common.notification import Notification

class AchievementHistoryProvider(object):

    def __init__(self, scatterDebug = False, onlyShowAfterDate = None):
        self.scatterDebug = scatterDebug
        self.onlyShowAfterDate = onlyShowAfterDate

    def provide(self):
        notificationList = []
        completedDict = sm.GetService('achievementSvc').completedDict
        for taskID, timestamp in completedDict.iteritems():
            if self.onlyShowAfterDate and timestamp <= self.onlyShowAfterDate:
                continue
            notificationData = AchievementTaskFormatter.MakeData(taskID)
            notification = Notification.MakeAchievementNotification(data=notificationData, created=timestamp)
            notificationList.append(notification)
            if self.scatterDebug:
                sm.ScatterEvent('OnNewNotificationReceived', notification)

        allGroups = GetAchievementGroups()
        for eachGroup in allGroups:
            if not eachGroup.IsCompleted():
                continue
            lastCompleteTimestamp = max((completedDict.get(taskID, None) for taskID in eachGroup.achievementTaskIDs))
            notificationData = AchievementOpportunityFormatter.MakeData(eachGroup.groupID)
            notification = Notification.MakeAchievementNotification(data=notificationData, created=lastCompleteTimestamp + 1, notificationType=notificationConst.notificationTypeOpportunityFinished)
            notificationList.append(notification)

        return notificationList
