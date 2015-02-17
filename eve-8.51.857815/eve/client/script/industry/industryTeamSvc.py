#Embedded file name: eve/client/script/industry\industryTeamSvc.py
import blue
import service
from carbon.common.lib.const import HOUR
from workers import RANGE_REGION
from workers.teamCache import SmartCache
from workers.teamFilters import FILTER_RANGE, FILTER_SPECIALIZATION, FILTER_GROUP, FilterGenerator, FILTER_ACTIVITY
from workers.timer import Timer

class IndustryTeamSvc(service.Service):
    __guid__ = 'svc.industryTeamSvc'

    def _GetTimerObject(self):
        return Timer(blue.os.GetWallclockTime, blue.synchro.SleepWallclock, HOUR)

    def Run(self, *args):
        self.teamHandler = sm.RemoteSvc('teamHandler')
        self.SetupCache()
        self.expiryTimesByTeamID = {}
        self.bidsByTeamID = {}

    def SetupCache(self):
        self.teamCache = self.GetTeamsSmartCache()
        self.auctionTeamCache = self.GetAuctionTeamSmartCache()

    def GetTeams(self, groupID, rangeRestriction = None, specialization = None, activityID = None):
        return self.teamCache.GetTeams(self._GetFilterArgs(rangeRestriction, specialization, activityID))

    def GetTeamsInAuction(self, groupID, rangeRestriction = None, specialization = None, activityID = None):
        return self.auctionTeamCache.GetTeams(self._GetFilterArgs(rangeRestriction, specialization, activityID))

    def _GetFilterArgs(self, rangeRestriction, specialization, activityID = None):
        filterArgs = {}
        if rangeRestriction is not None:
            restrictionType, solarSystemID = rangeRestriction
            filterArgs[FILTER_RANGE] = (restrictionType, solarSystemID)
        if specialization:
            filterArgs[FILTER_SPECIALIZATION] = (specialization,)
        if activityID:
            filterArgs[FILTER_ACTIVITY] = (activityID,)
        return filterArgs

    def _UpdateAuctionInfo(self, auctionInfo):
        teams = []
        for team, expiryTime, bids in auctionInfo:
            teams.append(team)
            self.expiryTimesByTeamID[team.teamID] = expiryTime
            self.bidsByTeamID[team.teamID] = bids

        return teams

    def GetAuctionInfo(self, filterArgs):
        return self._UpdateAuctionInfo(self.teamHandler.GetTeamsAndAuctionData(filterArgs))

    def GetRecentlyAddedAuctionTeams(self, time):
        return self._UpdateAuctionInfo(self.teamHandler.GetTeamsInAuctionMoreRecentThan(time))

    def GetBids(self, teamID):
        return self.bidsByTeamID[teamID]

    def GetAuctionExpiryTime(self, teamID):
        return self.expiryTimesByTeamID[teamID]

    def PrimeTeams(self, teamIDs):
        teamIDsToFetch = self.teamCache.GetTeamsThatArentCached(teamIDs)
        if teamIDsToFetch:
            self.teamCache.AddTeams(self.teamHandler.GetTeamsByIDs(teamIDsToFetch))

    def GetTeam(self, teamID):
        self.PrimeTeams([teamID])
        return self.teamCache.GetTeam(teamID)

    def HasSolarSystemBidForAuctionID(self, teamID, solarSystemID):
        return self.bidsByTeamID[teamID].HasBidOnSolarSystem(solarSystemID)

    def BidOnTeam(self, teamID, systemID, amount):
        newBids = self.teamHandler.BidOnTeam(teamID, systemID, amount)
        self.bidsByTeamID[teamID] = newBids

    def GMSetAuctionExpiryTime(self, auctionID, time):
        self.teamHandler.GMSetAuctionExpiryTime(auctionID, time)
        self.SetupCache()
        self.expiryTimesByTeamID = {}
        self.bidsByTeamID = {}
        sm.ScatterEvent('OnRefreshAuctionList')

    def GetTeamsSmartCache(self):
        return self._GetSmartCache(RemoteTeamsInterface(self.teamHandler))

    def GetAuctionTeamSmartCache(self):
        return self._GetSmartCache(RemoteAuctionTeamsInterface(self))

    def _GetSmartCache(self, remoteTeamsInterface):
        getRegion = lambda ssid: cfg.mapSystemCache.Get(ssid).regionID
        return SmartCache(remoteTeamsInterface, FilterGenerator(getRegion), getRegion, self._GetTimerObject())


class BaseRemoteTeamsInterface(object):

    def __init__(self, remoteTeams):
        self.remoteTeams = remoteTeams

    def GetTeamsByRegion(self, regionID):
        return self._GetTeams(((FILTER_RANGE, (RANGE_REGION, session.solarsystemid2)),))

    def GetTeamsBySpecialization(self, specialityID):
        return self._GetTeams(((FILTER_SPECIALIZATION, (specialityID,)),))

    def GetAllTeams(self):
        return self._GetTeams(())

    def _GetTeams(self, filterArgs):
        raise NotImplementedError()

    def GetRecentlyAddedTeams(self, time):
        raise NotImplementedError()


class RemoteTeamsInterface(BaseRemoteTeamsInterface):

    def _GetTeams(self, filterArgs):
        return self.remoteTeams.GetTeamsNotInAuction(filterArgs)

    def GetRecentlyAddedTeams(self, time):
        return (self.remoteTeams.GetTeamsMoreRecentThan(time), blue.os.GetWallclockTime() + 10 * const.MIN)


class RemoteAuctionTeamsInterface(BaseRemoteTeamsInterface):

    def _GetTeams(self, filterArgs):
        return self.remoteTeams.GetAuctionInfo(filterArgs)

    def GetRecentlyAddedTeams(self, time):
        return (self.remoteTeams.GetRecentlyAddedAuctionTeams(time), blue.os.GetWallclockTime() + 10 * const.MIN)
