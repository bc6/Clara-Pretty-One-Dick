#Embedded file name: evePathfinder\core.py
import time
import logging
from collections import defaultdict
log = logging.getLogger(__name__)
import pyEvePathfinder
from cache import NewPathfinderCache
import pathfinderconst as const

class MissingGetCacheEntryMethod(Exception):
    pass


def PairSequence(s):
    i = iter(s)
    last = i.next()
    for current in i:
        yield (last, current)
        last = current


class PathfinderCacheEntry(object):

    def __init__(self, hashValue, cache):
        self.hashValue = hashValue
        self.cache = cache


class SecurityInterval(object):
    """Describes a vaild interval of security levels"""

    def __init__(self, minSecurity, maxSecurity):
        self.minSecurity = minSecurity
        self.maxSecurity = maxSecurity


def IsUnreachableJumpCount(jumpCount):
    return jumpCount == const.UNREACHABLE_JUMP_COUNT


ROUTE_TYPES = {const.ROUTE_TYPE_SAFE: SecurityInterval(0.45, 1.0),
 const.ROUTE_TYPE_UNSAFE: SecurityInterval(0.0, 0.45),
 const.ROUTE_TYPE_UNSAFE_AND_NULL: SecurityInterval(-1.0, 0.45),
 const.ROUTE_TYPE_SHORTEST: SecurityInterval(-1.0, 1.0)}

class StatefulPathfinderInterfaceTemplate(object):
    """
    This is a template example for implementing the stateful interface for 
    EvePathfinderCore. It is expected to perform whatever caching is nessecary.
    
    It is also supposed to provide a hash value of the current state which changes
    when the state changes, allowing the pathfinder to know when to re-evaluate a cached result.
    """

    def GetStartingSystem(self):
        """
        Returns the current solarSystemID as an integer
        """
        raise NotImplementedError('EvePathfinderCore requires this function')

    def GetSecurityPenalty(self):
        """
        Returns a floating point value for deviating outside of the security bounds
        """
        raise NotImplementedError('EvePathfinderCore requires this function')

    def GetAvoidanceList(self):
        """
        Returns a list of solarSystemIDs that the user is avoiding
        """
        raise NotImplementedError('EvePathfinderCore requires this function')

    def GetRouteType(self):
        """
        Returns the currently set route type (shortest/safe/unsafe)
        """
        raise NotImplementedError('EvePathfinderCore requires this function')

    def GetCurrentStateHash(self, fromSolarSystemID):
        """
        Returns a hash of the current state (even if the calls have not been made)
        to allow the pathfinder to know if it needs to re-evaluate a route
        """
        raise NotImplementedError('EvePathfinderCore requires this function')


class EvePathfinderCore(object):
    """
    This class implements all of the functionality of the Eve pathfinder service, but
    makes all dependencies explicit in the constructor, allowing it to be unit tested.
    
    Absolutely NO service calls or access to global state are allowed in this file! 
    They must all be passed in in the following constructor.
    """

    def __init__(self, newPathfinderMap):
        self.newPathfinderMap = newPathfinderMap
        self.newPathfinderExecutionCount = 0
        self.newPathfinderGoal = pyEvePathfinder.EveStandardFloodFillGoal()

    def CreateCacheEntry(self):
        log.debug('default cache entry called')
        return PathfinderCacheEntry(None, NewPathfinderCache(self.newPathfinderMap))

    def _RunNewPathfinderFrom(self, solarSystemID, cache, routeType, penalty, minSec, maxSec, avoidanceSystems, goalSystems):
        """
        This function is largely stateless, allowing it to be used without worry about invalidation of caches or the
        particulars of the caching mechanisms
        """
        if solarSystemID is None or cache is None:
            raise TypeError('Must supply a solarSystemID and a cache')
        cache.ClearCache()
        universe = self.newPathfinderMap
        if routeType == const.ROUTE_TYPE_SHORTEST:
            self.newPathfinderGoal.IgnoreSecurityLimits()
        else:
            self.newPathfinderGoal.AvoidSystemsOutsideSecurityLimits(minSec, maxSec, penalty)
        self.newPathfinderGoal.ClearOrigins()
        self.newPathfinderGoal.AddOrigin(universe, solarSystemID)
        self.newPathfinderGoal.ClearGoalSystems()
        for i in goalSystems:
            self.newPathfinderGoal.AddGoalSystem(universe, i)

        self.newPathfinderGoal.ClearAvoidSystems()
        for itemID in avoidanceSystems:
            self.newPathfinderGoal.AddAvoidSystem(universe, itemID)

        start = time.clock()
        pyEvePathfinder.FindRoute(self.newPathfinderMap, self.newPathfinderGoal, cache.GetCacheForPathfinding())
        self.newPathfinderExecutionCount += 1
        log.debug('EvePathfinder pathfind done in: %f ms', (time.clock() - start) * 1000)

    def GetCachedEntry(self, stateInterface, fromID):
        """
        This method should be overridden by owner to control the caching strategy used.
        The basic pattern is as follows.
        this would normally be a lookup in a dict.
        """
        raise MissingGetCacheEntryMethod('Pathfinder needs an external method to provide the caching strategy.')

    def GoalSystemsContainAnyAvoidedSystem(self, goalSystems, avoidedSystems):
        """
        Checks whether the list of goal systems contains any avoided systems
        
        :param goalSystems: a list of goal system ids
        :param avoidedSystems: a list of system ids to avoid
        :return: True/False
        """
        return len(set(goalSystems).intersection(set(avoidedSystems))) != 0

    def GetPathfinderCache(self, stateInterface, fromID, goalSystems):
        cacheEntry = self._GetCachedEntry(stateInterface, fromID)
        currentHashValue = stateInterface.GetCurrentStateHash(fromID)
        cache = cacheEntry.cache
        if self.GoalSystemsContainAnyAvoidedSystem(goalSystems, stateInterface.GetAvoidanceList()):
            cache.MarkAsDirty()
        if cache.IsDirty() or currentHashValue != cacheEntry.hashValue:
            self.RefreshCache(cache, stateInterface, fromID, goalSystems)
            cacheEntry.hashValue = currentHashValue
        return cache

    def RefreshCache(self, pathfindingCache, stateInterface, startingSolarSystemID, goalSystems):
        avoidedSystems = stateInterface.GetAvoidanceList()
        routeType = stateInterface.GetRouteType()
        secInterval = ROUTE_TYPES[routeType]
        self._RunNewPathfinderFrom(startingSolarSystemID, pathfindingCache, routeType, stateInterface.GetSecurityPenalty(), secInterval.minSecurity, secInterval.maxSecurity, avoidedSystems, goalSystems)
        pathfindingCache.MarkAsClean()
        for goalSystem in goalSystems:
            if goalSystem in avoidedSystems:
                pathfindingCache.MarkAsDirty()
                break

    def GetJumpCountsBetweenSystemPairs(self, stateInterface, solarSystemPairs):
        """
        Returns the number of jumps for multiple pairs of systems
        """
        result = {}
        for originID, destinationID in solarSystemPairs:
            result[originID, destinationID] = self.GetJumpCountBetween(stateInterface, originID, destinationID)

        return result

    def GetListOfWaypointPaths(self, stateInterface, fromID, waypoints):
        if len(waypoints) < 2:
            raise AttributeError('There should be at least two waypoints')
        fullRoute = []
        for fromID, toID in PairSequence(waypoints):
            fullRoute.append(self.GetPathBetween(stateInterface, fromID, toID))

        return fullRoute

    def GetPathBetween(self, stateInterface, fromID, toID):
        """
        Returns the shortest path between the given fromID to the given toID (inclusive of both).
        """
        log.debug('GetPathBetween: %s to %s', fromID, toID)
        cache = self.GetPathfinderCache(stateInterface, fromID, [toID])
        return cache.GetPathTo(toID)

    def GetJumpCountBetween(self, stateInterface, fromID, toID):
        """
        Returns the jump count between the two ids
        """
        log.debug('GetPathBetween: %s to %s', fromID, toID)
        cache = self.GetPathfinderCache(stateInterface, fromID, [toID])
        jumpCount = cache.GetJumpCountTo(toID)
        if jumpCount == -1:
            return const.UNREACHABLE_JUMP_COUNT
        else:
            return jumpCount

    def GetSystemsWithinJumpRange(self, stateInterface, fromID, jumpCountMin, jumpCountMax):
        """
        Returns a defaultdict of systems by jump count that have a jump count that is >= minCount and < maxCount
        """
        cache = self.GetPathfinderCache(stateInterface, fromID, [])
        systemsWithinJumpCountGenerator = cache.GetSystemsWithinJumpCount(jumpCountMin, jumpCountMax)
        m = defaultdict(list)
        for system, jumpCount in systemsWithinJumpCountGenerator.iteritems():
            m[jumpCount].append(system)

        return m

    def SetGetCachedEntryMethod(self, GetCachedEntryMethod):
        self._GetCachedEntry = GetCachedEntryMethod
