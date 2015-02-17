#Embedded file name: notifications/common/formatters\newMail.py
import localization
from notifications.common.formatters.baseFormatter import BaseNotificationFormatter

class NewMailFormatter(BaseNotificationFormatter):

    def __init__(self):
        self.subjectLabel = 'UI/Mail/NewMailHeader'
        self.subtextLabel = 'UI/Mail/From'

    @staticmethod
    def MakeData(msg):
        return {'senderName': msg.senderName,
         'subject': msg.subject,
         'msg': msg}

    def Format(self, notification):
        data = notification.data
        notification.subject = localization.GetByLabel(self.subjectLabel)
        notification.subtext = '%s: %s' % (localization.GetByLabel('UI/Mail/From'), data['senderName'])
        subject = data['subject']
        body = subject
        if len(subject) > 100:
            body = '%s...' % subject[:100]
        notification.body = body

    def MakeSampleData(self):
        from utillib import KeyVal
        msg = KeyVal({'senderName': 'SampleSender',
         'subject': 'sampleSubject'})
        return NewMailFormatter.MakeData(msg)
