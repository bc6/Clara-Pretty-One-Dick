#Embedded file name: workers\teamCache.py
from collections import defaultdict
from carbon.common.lib.const import SEC
from workers import RANGE_WORLD
from workers.teamFilters import FILTER_RANGE, FILTER_SPECIALIZATION, FILTER_GROUP
from workers.teams import Teams
from workers.util import GetBaseSpecializationForGroup
import logging
logger = logging.getLogger(__name__)

class SmartCache(object):

    def __init__(self, remoteTeams, filterGenerator, getRegion, timer):
        self.remoteTeams = remoteTeams
        self.getRegion = getRegion
        self.hasCachedAllTeams = False
        self.timer = timer
        self.cache = defaultdict(set)
        self.nextUpdateTime = None
        self.teams = Teams()
        self.filterGenerator = filterGenerator

    def GetTeams(self, filterArgs):
        self._RemoveNonFilters(filterArgs)
        if self._ShouldGetAllTeams(filterArgs):
            self._CacheAllTeams()
        elif not self._IsCached(filterArgs):
            if FILTER_RANGE in filterArgs:
                regionID = self.getRegion(filterArgs[FILTER_RANGE][1])
                self._CacheRegionTeams(regionID)
            elif FILTER_SPECIALIZATION in filterArgs:
                specializationID = filterArgs[FILTER_SPECIALIZATION][0]
                self._CacheSpecialization(specializationID)
            elif FILTER_GROUP in filterArgs:
                specializationID = GetBaseSpecializationForGroup(filterArgs[FILTER_GROUP][0])
                self._CacheSpecialization(specializationID)
        if self.nextUpdateTime is None:
            self.nextUpdateTime = self.timer.GetTime()
        if self.nextUpdateTime <= self.timer.GetTime():
            logger.debug('Getting recently added teams')
            newTeams, self.nextUpdateTime = self.remoteTeams.GetRecentlyAddedTeams(self.nextUpdateTime)
            for team in newTeams:
                self.teams.AddTeam(team)

        return self.filterGenerator.Filter(tuple(filterArgs.items()), self.teams)

    def _RemoveNonFilters(self, filterArgs):
        if FILTER_RANGE in filterArgs and filterArgs[FILTER_RANGE][0] == RANGE_WORLD:
            del filterArgs[FILTER_RANGE]

    def _CacheAllTeams(self):
        logger.debug('CACHE-MISS. Getting all the teams')
        for team in self.remoteTeams.GetAllTeams():
            self.teams.AddTeam(team)

        self.hasCachedAllTeams = True

    def _ShouldGetAllTeams(self, filterArgs):
        if self.hasCachedAllTeams:
            return False
        for filterType, args in filterArgs.iteritems():
            if filterType == FILTER_RANGE:
                if args[0] != RANGE_WORLD:
                    return False
            else:
                return False

        return True

    def _IsCached(self, filterArgs):
        for filterType, args in filterArgs.iteritems():
            if filterType == FILTER_RANGE:
                if self.getRegion(args[1]) in self.cache[FILTER_RANGE]:
                    return True
            elif filterType == FILTER_SPECIALIZATION:
                if args[0] in self.cache[FILTER_SPECIALIZATION]:
                    return True

        return False

    def _CacheRegionTeams(self, regionID):
        logger.debug('CACHE-MISS Getting teams for region %d', regionID)
        for team in self.remoteTeams.GetTeamsByRegion(regionID):
            self.teams.AddTeam(team)

        self.cache[FILTER_RANGE].add(regionID)

    def _CacheSpecialization(self, specializationID):
        logger.debug('CACHE-MISS Getting teams for specialization %d', specializationID)
        for team in self.remoteTeams.GetTeamsBySpecialization(specializationID):
            self.teams.AddTeam(team)

        self.cache[FILTER_SPECIALIZATION].add(specializationID)

    def GetTeam(self, teamID):
        return self.teams.GetTeamByID(teamID)

    def AddTeam(self, team):
        self.teams.AddTeam(team)

    def GetTeamsThatArentCached(self, teamIDs):
        return {teamID for teamID in teamIDs if not self.teams.HasTeam(teamID)}

    def AddTeams(self, teams):
        for team in teams:
            self.teams.AddTeam(team)
