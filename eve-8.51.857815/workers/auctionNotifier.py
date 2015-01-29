#Embedded file name: workers\auctionNotifier.py
from eve.common.script.util.notificationconst import notificationTypeIndustryTeamAuctionWon, notificationTypeIndustryTeamAuctionLost
from inventorycommon.const import ownerCONCORD

class AuctionNotifier(object):

    def __init__(self, notificationMgr, teams):
        self.notificationMgr = notificationMgr
        self.teams = teams

    def NotifyAuctionEnded(self, winningSolarSystemID, bids, teamID):
        if not bids:
            return
        nameInfo = self.teams.GetTeamNameInfo(teamID)
        totalAmount = sum(bids[winningSolarSystemID].itervalues())
        for solarSystemID, systemBids in bids.iteritems():
            for charID, amount in systemBids.iteritems():
                notificationType = self._GetNotificationType(winningSolarSystemID, solarSystemID)
                self._SendNotification(notificationType, charID, winningSolarSystemID, amount, totalAmount, nameInfo, systemBids)

    def _SendNotification(self, notificationType, charID, solarSystemID, amount, totalAmount, nameInfo, systemBids):
        self.notificationMgr.SendToCharacter(notificationType, charID, ownerCONCORD, data={'solarSystemID': solarSystemID,
         'yourAmount': amount,
         'teamNameInfo': nameInfo,
         'totalIsk': totalAmount,
         'systemBids': dict(systemBids)})

    def _GetNotificationType(self, winningSolarSystemID, solarSystemID):
        if solarSystemID == winningSolarSystemID:
            return notificationTypeIndustryTeamAuctionWon
        else:
            return notificationTypeIndustryTeamAuctionLost
