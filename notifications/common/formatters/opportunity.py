#Embedded file name: notifications/common/formatters\opportunity.py
from achievements.common.achievementGroups import GetAchievementGroup
from localization import GetByLabel
from notifications.common.formatters.baseFormatter import BaseNotificationFormatter

class AchievementOpportunityFormatter(BaseNotificationFormatter):

    @staticmethod
    def MakeData(groupID):
        return {'groupID': groupID}

    def Format(self, notification):
        data = notification.data
        groupID = data['groupID']
        group = GetAchievementGroup(groupID)
        notificationPath = group.notificationPath
        subject = GetByLabel(notificationPath)
        notification.subject = subject

    def MakeSampleData(self):
        from utillib import KeyVal
        msg = KeyVal({'groupID': 10})
        return AchievementOpportunityFormatter.MakeData(msg)
