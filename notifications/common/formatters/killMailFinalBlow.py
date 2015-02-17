#Embedded file name: notifications/common/formatters\killMailFinalBlow.py
import localization
from notifications.common.formatters.killMailBase import KillMailBaseFormatter

class KillMailFinalBlowFormatter(KillMailBaseFormatter):

    def __init__(self):
        self.subjectLabel = 'Notifications/subjKillReportFinalBlow'
        self.subjectLabelStructure = 'Notifications/subjKillReportFinalBlowStructure'

    @staticmethod
    def MakeData(killMailID, killMailHash, victimID, victimShipTypeID):
        d = {'victimID': victimID,
         'victimShipTypeID': victimShipTypeID}
        d.update(KillMailBaseFormatter.MakeData(killMailID=killMailID, killMailHash=killMailHash))
        return d

    @staticmethod
    def GetVictimID(data):
        return data['victimID']

    @staticmethod
    def GetVictimShipTypeID(data):
        return data['victimShipTypeID']

    def Format(self, notification):
        victimID = self.GetVictimID(notification.data)
        if victimID is not None:
            notification.subject = localization.GetByLabel(self.subjectLabel, victimCharID=self.GetVictimID(notification.data))
        else:
            notification.subject = localization.GetByLabel(self.subjectLabelStructure, typeID=self.GetVictimShipTypeID(notification.data))

    @staticmethod
    def MakeSampleData(variant = 1):
        if variant is 1:
            ballisticDeflectionArrayID = 17184
            return KillMailFinalBlowFormatter.MakeData(killMailID=1, killMailHash='', victimID=None, victimShipTypeID=ballisticDeflectionArrayID)
        else:
            rifterTypeID = 587
            firstCharacterId = 90000001
            return KillMailFinalBlowFormatter.MakeData(killMailID=1, killMailHash='', victimID=firstCharacterId, victimShipTypeID=rifterTypeID)
