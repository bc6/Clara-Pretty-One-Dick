#Embedded file name: notifications/common/formatters\contractAttention.py
from notifications.common.formatters.baseFormatter import BaseNotificationFormatter
import localization
FIRST_CONTRACT_ID = 'firstContractID'
IS_FOR_CORP = 'isForCorp'
NEEDS_ATTENTION = 'needsAttention'

class ContractNeedsAttentionFormatter(BaseNotificationFormatter):

    def __init__(self):
        self.subjectLabel = 'UI/Contracts/ContractsWindow/Contracts'
        self.subtextLabelOneAttention = 'UI/Contracts/ContractsWindow/ContractNeedsAttention'
        self.subtextLabelManyAttention = 'UI/Contracts/ContractsService/ContractsNeedAttention'
        self.subtextArgs = {}

    @staticmethod
    def MakeData(needsAttention, isForCorp = False, firstContractID = 0):
        return {NEEDS_ATTENTION: needsAttention,
         IS_FOR_CORP: isForCorp,
         FIRST_CONTRACT_ID: firstContractID}

    @staticmethod
    def GetNeedsAttentionFromData(data):
        return data[NEEDS_ATTENTION]

    @staticmethod
    def GetFirstContractId(data):
        return data[FIRST_CONTRACT_ID]

    @staticmethod
    def GetIsForCorp(data):
        return data[IS_FOR_CORP]

    def GetSubtext(self, needsAttention):
        subtext = ''
        if needsAttention == 1:
            subtext = localization.GetByLabel(self.subtextLabelOneAttention)
        else:
            subtext = localization.GetByLabel(self.subtextLabelManyAttention, numContracts=needsAttention)
        return subtext

    def Format(self, notification):
        needsAttention = notification.data[NEEDS_ATTENTION]
        notification.subject = localization.GetByLabel(self.subjectLabel)
        notification.subtext = self.GetSubtext(needsAttention)

    @staticmethod
    def MakeSampleData():
        return ContractNeedsAttentionFormatter.MakeData(needsAttention=1)
