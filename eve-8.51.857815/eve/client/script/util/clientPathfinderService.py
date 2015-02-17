#Embedded file name: eve/client/script/util\clientPathfinderService.py
"""
A thin service wrapper around a client specific pathfinder implementation
"""
import service
import util
import const
from evePathfinder.pathfinder import ClientPathfinder
from evePathfinder.stateinterface import AutopilotPathfinderInterface, StandardPathfinderInterface
from evePathfinder import factory

def ConvertStationIDToSolarSystemIDIfNecessary(waypointID):
    if util.IsStation(waypointID):
        return cfg.stations.Get(waypointID).solarSystemID
    else:
        return waypointID


def GetCurrentSolarSystemID():
    return session.solarsystemid2


def UpdatesAutopilot(func):
    """A decorator that scatters an event after doing a unit of work"""

    def Wrapper(*args, **kwargs):
        func(*args, **kwargs)
        sm.ScatterEvent('OnAutopilotUpdated')

    return Wrapper


class ClientPathfinderService(service.Service):
    __exportedcalls__ = {}
    __guid__ = 'svc.clientPathfinderService'
    __servicename__ = 'pathfinderSvc'
    __displayname__ = 'Client Pathfinder Service'
    __dependencies__ = ['settings', 'map', 'objectCaching']
    __notifyevents__ = ['OnSessionChanged']

    def Run(self, memStream = None):
        self.LogInfo('Starting Client Pathfinder Service')

    def OnSessionChanged(self, isRemote, session, change):
        if 'charid' in change and change['charid'][1] is not None:
            self.Initialize()

    def Initialize(self):
        self.LogInfo('Initializing the pathfinding internals')
        self.lastPKversionNumber = -1
        pathfinderCore = factory.CreatePathfinder(cfg.mapRegionCache, cfg.mapSystemCache, cfg.mapJumpCache)
        autopilotStateInterface = AutopilotPathfinderInterface(self.map, self.UpdatePodKillList, settings.char.ui)
        standardStateInterface = StandardPathfinderInterface()
        self.clientPathfinder = ClientPathfinder(pathfinderCore, standardStateInterface, autopilotStateInterface, ConvertStationIDToSolarSystemIDIfNecessary, GetCurrentSolarSystemID)
        self.SetPodKillAvoidance = UpdatesAutopilot(self.clientPathfinder.SetPodKillAvoidance)
        self.SetSystemAvoidance = UpdatesAutopilot(self.clientPathfinder.SetSystemAvoidance)
        self.SetAutopilotRouteType = UpdatesAutopilot(self.clientPathfinder.SetAutopilotRouteType)
        self.AddAvoidanceItem = UpdatesAutopilot(self.clientPathfinder.AddAvoidanceItem)
        self.RemoveAvoidanceItem = UpdatesAutopilot(self.clientPathfinder.RemoveAvoidanceItem)
        self.SetSecurityPenaltyFactor = UpdatesAutopilot(self.clientPathfinder.SetSecurityPenaltyFactor)
        self.GetAvoidanceItems = self.clientPathfinder.GetAvoidanceItems
        self.GetAutopilotRouteType = self.clientPathfinder.GetAutopilotRouteType
        self.GetWaypointPath = self.clientPathfinder.GetWaypointPath
        self.GetJumpCountsBetweenSystemPairs = self.clientPathfinder.GetJumpCountsBetweenSystemPairs
        self.GetPathBetween = self.clientPathfinder.GetPathBetween
        self.GetAutopilotPathBetween = self.clientPathfinder.GetAutopilotPathBetween
        self.GetJumpCount = self.clientPathfinder.GetJumpCount
        self.GetAutopilotJumpCount = self.clientPathfinder.GetAutopilotJumpCount
        self.GetJumpCountFromCurrent = self.clientPathfinder.GetJumpCountFromCurrent
        self.GetSystemsWithinJumpRange = self.clientPathfinder.GetSystemsWithinJumpRange
        self.GetExpandedAvoidanceItems = self.clientPathfinder.GetExpandedAvoidanceItems

    def UpdatePodKillList(self, podKillList):
        args = (const.mapHistoryStatKills, 24)
        if self.lastPKversionNumber == -1 or self.lastPKversionNumber != self.objectCaching.GetCachedMethodCallVersion(None, 'map', 'GetHistory', args):
            unfilteredSystemHistory = sm.RemoteSvc('map').GetHistory(*args)
            self.lastPKversionNumber = self.objectCaching.GetCachedMethodCallVersion(None, 'map', 'GetHistory', args)
            podKillList = []
            for system in unfilteredSystemHistory:
                if system.value3 > 0:
                    podKillList.append(system.solarSystemID)

            podKillList.sort()
        return podKillList
