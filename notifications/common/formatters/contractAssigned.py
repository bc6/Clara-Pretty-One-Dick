#Embedded file name: notifications/common/formatters\contractAssigned.py
from notifications.common.formatters.baseFormatter import BaseNotificationFormatter
import localization
FIRST_CONTRACT_ID = 'firstContractID'
ASSIGNED_TO_ME = 'assignedToMe'

class ContractAssignedFormatter(BaseNotificationFormatter):

    def __init__(self):
        self.subjectLabel = 'UI/Contracts/ContractsWindow/Contracts'
        self.subtextLabelOneToMe = 'UI/Contracts/ContractsWindow/ContractAssignedToYou'
        self.subtextLabelManyToMe = 'UI/Contracts/ContractsService/ContractsAssignedToYou'
        self.subtextLabel = ''
        self.subtextArgs = {}

    @staticmethod
    def MakeData(contractCountAssignedToMe, firstContractID):
        return {ASSIGNED_TO_ME: contractCountAssignedToMe,
         FIRST_CONTRACT_ID: firstContractID}

    @staticmethod
    def GetAssignedCount(data):
        return data[ASSIGNED_TO_ME]

    @staticmethod
    def GetContractID(data):
        return data[FIRST_CONTRACT_ID]

    def Format(self, notification):
        assignedToMeCount = self.GetAssignedCount(notification.data)
        self.SetCorrectSubTextLabel(assignedToMeCount)
        notification.subject = localization.GetByLabel(self.subjectLabel)
        notification.subtext = localization.GetByLabel(self.subtextLabel, **self.subtextArgs)

    def SetCorrectSubTextLabel(self, assignedToMeCount):
        if assignedToMeCount == 1:
            self.subtextLabel = self.subtextLabelOneToMe
        else:
            self.subtextLabel = self.subtextLabelManyToMe
            self.subtextArgs = {'numContracts': assignedToMeCount}

    @staticmethod
    def MakeSampleData():
        return ContractAssignedFormatter.MakeData(contractCountAssignedToMe=1, firstContractID=0)
