#Embedded file name: workers\eventLogger.py
from eveexceptions.exceptionEater import ExceptionEater
EVENT_BID_ON_TEAM = 'teams::auction_BidOnTeam'
EVENT_EXPIRE_AUCTION = 'teams::auction_ExpireAuction'
EVENT_REIMBURSE_LOSER = 'teams::auction_ReimburseLoser'
EVENT_EXPIRY = 'teams::teamKiller_KillExpiredTeams'

class EventLogger(object):
    """
    Event Logger for the industry-teams feature.
    """

    def __init__(self, eventLog):
        self.eventLog = eventLog

    def GetBidsAsText(self, bidInfo):
        """
        Converts all bids on a team to a string for logging.
        solarSystemID:charID1:amount:charID2:amount,solarSystem2:etc.
        """
        bidList = []
        for bidEntry in bidInfo:
            solarSystemID, bidsBySolarSystem = bidEntry
            bidsForSystemString = self.GetBidsForSolarSystemAsText(bidsBySolarSystem)
            systemBidsString = str(solarSystemID) + ':' + bidsForSystemString
            bidList.append(systemBidsString)

        bidsString = ','.join((e for e in bidList))
        return bidsString

    def GetBidsForSolarSystemAsText(self, bidsBySolarSystem):
        """
        Converts bids for a given solarSystem to text.
        charID1:amount:charID2:amount etc.
        """
        systemBids = []
        for charID, amount in bidsBySolarSystem.iteritems():
            systemBids.extend((charID, amount))

        bidsString = ':'.join((str(e) for e in systemBids))
        return bidsString

    def LogBid(self, charID, locationID, teamID, amount, activity):
        """
        Logs every bid on a team.
        """
        with ExceptionEater('eventLog'):
            self.eventLog.LogOwnerEvent(EVENT_BID_ON_TEAM, charID, locationID, teamID, amount, activity)
            self.eventLog.LogOwnerEventJson(EVENT_BID_ON_TEAM, charID, locationID, teamID=teamID, amount=amount, activity=activity)

    def LogEndAuction(self, locationID, teamID, bidList, activity):
        """
        Logs when team auction expires. Both for teams that received player auctions and didn't.
        If bidList is empty it means it never received player auction before expiring.
        Puts a random charID as owner from the winning auction if the team received auctions.
        """
        with ExceptionEater('eventLog'):
            if bidList:
                charID = bidList[locationID].keys()[0]
                bidList = self.GetBidsAsText(bidList.iteritems())
            else:
                charID = const.ownerSystem
            self.eventLog.LogOwnerEvent(EVENT_EXPIRE_AUCTION, charID, locationID, teamID, bidList, activity)
            self.eventLog.LogOwnerEventJson(EVENT_EXPIRE_AUCTION, charID, locationID, teamID, bidList=bidList, activity=activity)

    def LogReimbursement(self, locationID, teamID, bidInfo, activity):
        """
        Logs for characters that lost a team auction.
        Puts a random charID as owner from the bid info.
        """
        with ExceptionEater('eventLog'):
            charID = bidInfo.keys()[0]
            bidList = self.GetBidsForSolarSystemAsText(bidInfo)
            self.eventLog.LogOwnerEvent(EVENT_REIMBURSE_LOSER, charID, locationID, teamID, bidList, activity)
            self.eventLog.LogOwnerEventJson(EVENT_REIMBURSE_LOSER, charID, locationID, teamID=teamID, bidList=bidList, activity=activity)

    def LogExpiry(self, locationID, teamID):
        """
            Logs when an active team expires from the world.
        """
        with ExceptionEater('eventLog'):
            self.eventLog.LogOwnerEvent(EVENT_EXPIRY, const.ownerSystem, locationID, teamID)
            self.eventLog.LogOwnerEventJson(EVENT_EXPIRY, const.ownerSystem, locationID, teamID=teamID)
