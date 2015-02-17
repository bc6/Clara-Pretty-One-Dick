#Embedded file name: notifications/common/formatters\skillPoints.py
from notifications.common.formatters.baseFormatter import BaseNotificationFormatter
import localization

class UnusedSkillPointsFormatter(BaseNotificationFormatter):

    def __init__(self):
        self.subjectLabel = 'UI/Generic/SkillPointsApplied'
        self.subtextLabel = 'UI/SkillQueue/UnallocatedSkillPoints'

    @staticmethod
    def MakeData():
        return {}

    def Format(self, notification):
        notification.subject = localization.GetByLabel(self.subjectLabel)
        notification.subtext = localization.GetByLabel(self.subtextLabel)
