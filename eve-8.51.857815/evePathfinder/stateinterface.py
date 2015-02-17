#Embedded file name: evePathfinder\stateinterface.py
"""
Pathfinder state interfaces for the client to use
"""
import hashlib
import math
from evePathfinder.pathfinderconst import ROUTE_TYPE_SHORTEST
from evePathfinder.pathfinderconst import ROUTE_TYPE_SAFE
from evePathfinder.pathfinderconst import DEFAULT_SECURITY_PENALTY_VALUE
from evePathfinder.pathfinderconst import SECURITY_PENALTY_FACTOR
from evePathfinder.pathfinderconst import DEFAULT_SECURITY_PENALTY
from inventorycommon.util import IsWormholeSystem
DEFAULT_AVOIDANCE = [30000142]

def GetCurrentStateHash(stateInterface, fromSolarSystemID):
    m = hashlib.md5()
    m.update(str(fromSolarSystemID))
    m.update(stateInterface.GetRouteType())
    m.update(str(stateInterface.GetSecurityPenalty()))
    m.update(str(stateInterface.GetAvoidanceList()))
    return m.hexdigest()


class StandardPathfinderInterface(object):
    """
    This class defines the interface from the pathfinder to the server implementation
    """

    def __init__(self):
        self.routeType = ROUTE_TYPE_SHORTEST

    def GetSecurityPenalty(self):
        return DEFAULT_SECURITY_PENALTY_VALUE

    def GetAvoidanceList(self):
        return []

    def SetRouteType(self, routeType):
        self.routeType = routeType

    def GetRouteType(self):
        return self.routeType

    def GetCurrentStateHash(self, fromSolarSystemID):
        return GetCurrentStateHash(self, fromSolarSystemID)


class AutopilotPathfinderInterface(object):
    """
    This class defines the interface from the pathfinder to the game and UI
    """

    def __init__(self, mapSvc, updatePodKillListFunc, autopilotSettings):
        self.podKillList = []
        self.lastPKversionNumber = -1
        self.mapSvc = mapSvc
        self.UpdatePodKillList = updatePodKillListFunc
        self.autopilotSettings = autopilotSettings

    def GetPodkillSystemList(self):
        self.podKillList = self.UpdatePodKillList(self.podKillList)
        return self.podKillList

    def GetSecurityPenalty(self):
        return math.exp(SECURITY_PENALTY_FACTOR * self.autopilotSettings.Get('pfPenalty', DEFAULT_SECURITY_PENALTY))

    def GetAvoidanceList(self):
        """The pathfinder is only really interested in a complete sorted list of solar systems"""
        items = []
        if self.IsAvoidanceEnabled():
            avoidedItems = self.autopilotSettings.Get('autopilot_avoidance2', DEFAULT_AVOIDANCE)
            avoidedSystems = self.mapSvc.ExpandItems(avoidedItems)
            items.extend(avoidedSystems)
        if self.IsPodkillAvoidanceEnabled():
            items.extend(self.GetPodkillSystemList())
        items = [ solarSystemID for solarSystemID in items if not IsWormholeSystem(solarSystemID) ]
        items.sort()
        return items

    def GetAvoidanceItems(self, expandSystems):
        items = self.autopilotSettings.Get('autopilot_avoidance2', DEFAULT_AVOIDANCE)
        if expandSystems:
            items = self.mapSvc.ExpandItems(items)
        return items

    def SetAvoidanceItems(self, items):
        self.autopilotSettings.Set('autopilot_avoidance2', items)

    def SetSystemAvoidance(self, pkAvoid = None):
        self.autopilotSettings.Set('pfAvoidSystems', pkAvoid)

    def SetRouteType(self, routeType):
        self.autopilotSettings.Set('pfRouteType', routeType)

    def GetRouteType(self):
        return self.autopilotSettings.Get('pfRouteType', ROUTE_TYPE_SAFE)

    def SetPodKillAvoidance(self, pkAvoid):
        self.autopilotSettings.Set('pfAvoidPodKill', pkAvoid)

    def IsAvoidanceEnabled(self):
        return self.autopilotSettings.Get('pfAvoidSystems', 1)

    def IsPodkillAvoidanceEnabled(self):
        return self.autopilotSettings.Get('pfAvoidPodKill', 0)

    def GetCurrentStateHash(self, fromSolarSystemID):
        return GetCurrentStateHash(self, fromSolarSystemID)

    def SetSecurityPenaltyFactor(self, securityPenalty):
        self.autopilotSettings.Set('pfPenalty', securityPenalty)
