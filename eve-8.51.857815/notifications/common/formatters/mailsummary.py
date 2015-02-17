#Embedded file name: notifications/common/formatters\mailsummary.py
import localization
from notifications.common.formatters.baseFormatter import BaseNotificationFormatter

class MailSummaryFormatter(BaseNotificationFormatter):

    def __init__(self):
        self.subjectLabel = 'UI/Mail/NewMailHeader'
        self.subtextLabel = 'UI/Mail/NewMails'

    def Format(self, notification):
        numMails = notification.data.get('numMails', 0)
        notification.subject = localization.GetByLabel(self.subjectLabel)
        notification.subtext = localization.GetByLabel(self.subtextLabel, numMails=numMails)

    @staticmethod
    def MakeData(numberOfMails):
        data = {'numMails': numberOfMails}
        return data

    @staticmethod
    def MakeSampleData():
        return MailSummaryFormatter.MakeData(numberOfMails=3)
