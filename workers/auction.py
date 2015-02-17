#Embedded file name: workers\auction.py
from collections import defaultdict
import heapq
from operator import itemgetter
from uthread2 import start_tasklet, Semaphore

class Auction(object):

    def __init__(self, timer, persister, teamsInAuction, teams, iskMover, notifier, eventLogger, startExpirer = True):
        self.timer = timer
        self.persister = persister
        self.teamsInAuction = teamsInAuction
        self.teams = teams
        self.iskMover = iskMover
        self.notifier = notifier
        self.auctionExpirer = AuctionExpirer(self.ExpireAuction, timer)
        self.locks = defaultdict(Semaphore)
        if startExpirer:
            self.auctionExpirerThread = start_tasklet(self.auctionExpirer.Run)
        else:
            self.auctionExpirerThread = None
        self.bidsByTeamID = {}
        self.eventLogger = eventLogger

    def AddTeam(self, teamID, auctionID, expiryTime):
        self.bidsByTeamID[teamID] = Bids()
        self.auctionExpirer.AddExpiryEntry(auctionID, expiryTime)

    def BidOnTeam(self, teamID, solarSystemID, characterID, amount):
        self.locks[teamID].acquire()
        try:
            if teamID in self.bidsByTeamID:
                self.iskMover.MoveCash(characterID, teamID, amount)
                time = self.timer.GetTime()
                self.persister.UpdateBid(teamID, characterID, solarSystemID, amount, time)
                self._RegisterBid(teamID, characterID, solarSystemID, amount, time)
                activity = self.teamsInAuction.GetTeamByID(teamID).activity
                self.eventLogger.LogBid(characterID, solarSystemID, teamID, amount, activity)
        finally:
            self.locks[teamID].release()

    def SetAuctionExpiryTime(self, teamID, time):
        self.auctionExpirer.ChangeExpiryTime(teamID, time)
        self.persister.UpdateAuctionExpiryTime(teamID, time)

    def _GetBids(self, teamID):
        return self.bidsByTeamID[teamID].GetBids()

    def GetBidsOnTeam(self, teamID):
        return self.bidsByTeamID[teamID]

    def ExpireAuction(self, teamID):
        self.locks[teamID].acquire()
        try:
            bids = self._GetBids(teamID)
            if bids:
                solarSystemID = self._PickBestBid(teamID)
                self.persister.UpdateSolarSystem(teamID, solarSystemID)
                self._MoveTeam(teamID, solarSystemID)
                activity = self.teams.GetTeamByID(teamID).activity
                self._ReimburseLosers(teamID, solarSystemID, bids, activity)
                self.notifier.NotifyAuctionEnded(solarSystemID, bids, teamID)
            else:
                solarSystemID = self.teamsInAuction.GetSolarSystemIDByTeamID(teamID)
                activity = self.teamsInAuction.GetTeamByID(teamID).activity
                self.teamsInAuction.RemoveTeams([teamID])
                self.persister.DeleteTeam(teamID)
            self.eventLogger.LogEndAuction(solarSystemID, teamID, bids, activity)
            del self.bidsByTeamID[teamID]
        finally:
            self.locks[teamID].release()

    def _MoveTeam(self, teamID, solarSystemID):
        team = self.teamsInAuction.GetTeamByID(teamID)
        self.teamsInAuction.RemoveTeams([teamID])
        self.teams.AddTeam(team)
        self.teams.UpdateTeamSolarSystemID(teamID, solarSystemID)

    def LoadBids(self, bidInfo):
        for row in bidInfo:
            if row.teamID not in self.bidsByTeamID:
                self.bidsByTeamID[row.teamID] = Bids()
            self._RegisterBid(row.teamID, row.characterID, row.solarSystemID, row.bid, None)

    def SetBidTimes(self, bidTimeInfo):
        for row in bidTimeInfo:
            if row.teamID in self.bidsByTeamID:
                self.bidsByTeamID[row.teamID].SetBidTime(row.solarSystemID, row.bidTime)

    def _RegisterBid(self, auctionID, characterID, solarSystemID, amount, time):
        self.bidsByTeamID[auctionID].AddBid(solarSystemID, characterID, amount, time)

    def _PickBestBid(self, auctionID):
        return self.bidsByTeamID[auctionID].PickSolarSystemWithBestBid()

    def _ReimburseLosers(self, auctionID, winningSolarSystemID, bids, activity):
        reimbursement = defaultdict(float)
        for solarSystemID, bidInfo in bids.iteritems():
            if solarSystemID == winningSolarSystemID:
                continue
            for characterID, bidAmount in bidInfo.iteritems():
                reimbursement[characterID] += bidAmount

            self.eventLogger.LogReimbursement(solarSystemID, auctionID, bidInfo, activity)

        self.iskMover.ReimburseLosers(reimbursement)

    def HasSolarSystemBidForAuctionID(self, auctionID, solarSystemID):
        return self.bidsByTeamID[auctionID].HasBidOnSolarSystem(solarSystemID)

    def GetExpiryTime(self, teamID):
        return self.auctionExpirer.GetExpiryTime(teamID)


class Bids(object):

    def __init__(self):
        self.bidsBySolarSystemID = {}
        self.bidTimesBySolarSystemID = {}

    def AddBid(self, solarSystemID, characterID, amount, time):
        if solarSystemID not in self.bidTimesBySolarSystemID:
            self.bidsBySolarSystemID[solarSystemID] = {}
        if characterID not in self.bidsBySolarSystemID[solarSystemID]:
            self.bidsBySolarSystemID[solarSystemID][characterID] = 0
        self.bidsBySolarSystemID[solarSystemID][characterID] += amount
        if time is not None:
            self.bidTimesBySolarSystemID[solarSystemID] = time

    def GetBids(self):
        return self.bidsBySolarSystemID

    def GetBidsBySolarSystem(self):
        totalBids = []
        for solarSystemID, bidInfo in self.bidsBySolarSystemID.iteritems():
            totalBids.append((sum(bidInfo.itervalues()), solarSystemID))

        return totalBids

    def PickSolarSystemWithBestBid(self):
        totalBids = self.GetBidsBySolarSystem()
        if not totalBids:
            return None
        maxValue, _ = max(totalBids, key=itemgetter(0))
        solarSystemIDs = set()
        for value, solarSystemID in totalBids:
            if value >= maxValue:
                solarSystemIDs.add(solarSystemID)

        bidTimes = self.bidTimesBySolarSystemID
        _, solarSystemID = min(((bidTimes.get(solarSystemID, 0), solarSystemID) for solarSystemID in solarSystemIDs))
        return solarSystemID

    def SetBidTime(self, solarSystemID, time):
        self.bidTimesBySolarSystemID[solarSystemID] = time

    def HasBidOnSolarSystem(self, solarSystemID):
        return solarSystemID in self.bidsBySolarSystemID

    def GetRankedBids(self):
        return sorted(self.GetBidsBySolarSystem(), key=lambda x: (-x[0], self.bidTimesBySolarSystemID[x[1]]))


class AuctionExpirer(object):

    def __init__(self, callback, timer):
        self.timer = timer
        self.callback = callback
        self.expiryTimes = []
        self.expiryTimesByTeamID = {}

    def AddExpiryEntry(self, teamID, expiryTime):
        heapq.heappush(self.expiryTimes, (expiryTime, teamID))
        self.expiryTimesByTeamID[teamID] = expiryTime

    def _PopExpiryEntry(self):
        expiryTime, teamID = heapq.heappop(self.expiryTimes)
        del self.expiryTimesByTeamID[teamID]
        return teamID

    def GetAuctionsToExpire(self, time):
        teamIDs = []
        while self.expiryTimes and self.expiryTimes[0][0] < time:
            teamIDs.append(self._PopExpiryEntry())

        return teamIDs

    def ChangeExpiryTime(self, teamIDToChange, newExpiryTime):
        oldExpiryTimes = self.expiryTimes[:]
        self.expiryTimes = []
        for expiryTime, teamID in oldExpiryTimes:
            if teamID == teamIDToChange:
                self.AddExpiryEntry(teamIDToChange, newExpiryTime)
            else:
                self.AddExpiryEntry(teamID, expiryTime)

    def Run(self):
        while True:
            self.timer.Sleep(5000)
            self._ExpireAuctions(self.timer.GetTime())

    def _ExpireAuctions(self, time):
        for teamID in self.GetAuctionsToExpire(time):
            self.callback(teamID)

    def GetExpiryTime(self, teamID):
        return self.expiryTimesByTeamID[teamID]
