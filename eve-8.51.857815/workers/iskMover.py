#Embedded file name: workers\iskMover.py
from eve.common.lib.appConst import ownerCONCORD, refIndustryTeamEscrow, refIndustryTeamEscrowReimbursement

class IskMover(object):

    def __init__(self, account):
        self.account = account

    def MoveCash(self, charID, teamID, amount):
        self.account.MoveCash2(-1, refIndustryTeamEscrow, charID, ownerCONCORD, amount)

    def ReimburseLosers(self, reimburseInfo):
        for charID, amount in reimburseInfo.iteritems():
            self.account.MoveCash2(-1, refIndustryTeamEscrowReimbursement, ownerCONCORD, charID, amount)
