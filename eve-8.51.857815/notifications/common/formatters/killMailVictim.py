#Embedded file name: notifications/common/formatters\killMailVictim.py
import localization
from notifications.common.formatters.attributeConstants import VICTIM_SHIP_TYPE_ID
from notifications.common.formatters.killMailBase import KillMailBaseFormatter

class KillMailVictimFormatter(KillMailBaseFormatter):

    def __init__(self):
        self.subjectLabel = 'Notifications/subjKillReportVictim'

    @staticmethod
    def MakeData(killMailID, killMailHash, victimShipTypeID):
        d = {VICTIM_SHIP_TYPE_ID: victimShipTypeID}
        d.update(KillMailBaseFormatter.MakeData(killMailID, killMailHash))
        return d

    def Format(self, notification):
        notification.subject = localization.GetByLabel(self.subjectLabel)

    @staticmethod
    def MakeSampleData():
        rifterTypeID = 587
        return KillMailVictimFormatter.MakeData(killMailID=1, killMailHash='', victimShipTypeID=rifterTypeID)

    @staticmethod
    def GetVictimShipType(data):
        return data[VICTIM_SHIP_TYPE_ID]
