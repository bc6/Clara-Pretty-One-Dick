#Embedded file name: notifications/common/formatters\baseFormatter.py


class BaseNotificationFormatter(object):

    def __init__(self):
        self.subjectLabel = ''
        self.bodyLabel = ''
        self.subtextLabel = ''

    def Format(self, notification):
        pass

    @staticmethod
    def MakeSampleData(variant = 0):
        return {}
