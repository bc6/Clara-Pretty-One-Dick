#Embedded file name: notifications/common/formatting\notificationFormatMapping.py
import eve.common.script.util.notificationconst as notificationConst
from notifications.common.formatters.contractAssigned import ContractAssignedFormatter
from notifications.common.formatters.contractAttention import ContractNeedsAttentionFormatter
from notifications.common.formatters.killMailFinalBlow import KillMailFinalBlowFormatter
from notifications.common.formatters.killMailVictim import KillMailVictimFormatter
from notifications.common.formatters.mailsummary import MailSummaryFormatter
from notifications.common.formatters.newMail import NewMailFormatter
from notifications.common.formatters.skillPoints import UnusedSkillPointsFormatter

class NotificationFormatMapper:

    def __init__(self):
        self.registry = {notificationConst.notificationTypeMailSummary: MailSummaryFormatter,
         notificationConst.notificationTypeNewMailFrom: NewMailFormatter,
         notificationConst.notificationTypeUnusedSkillPoints: UnusedSkillPointsFormatter,
         notificationConst.notificationTypeContractNeedsAttention: ContractNeedsAttentionFormatter,
         notificationConst.notificationTypeContractAssigned: ContractAssignedFormatter,
         notificationConst.notificationTypeKillReportVictim: KillMailVictimFormatter,
         notificationConst.notificationTypeKillReportFinalBlow: KillMailFinalBlowFormatter}

    def Register(self, notificationTypeID, formatter):
        self.registry[notificationTypeID] = formatter

    def GetFormatterForType(self, typeID):
        if typeID in self.registry:
            return self.registry[typeID]()
        else:
            return None
