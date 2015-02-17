#Embedded file name: evePathfinder\factory.py
"""
Contains factory methods to construct a pathfinder core instance
"""
import pyEvePathfinder
from . import core
from inventorycommon.util import IsWormholeRegion

def CreatePathfinder(mapRegionCache, mapSystemCache, mapJumpCache):
    """
    returns pathinder initialized with an eve map and jump data
    """
    eveMap = pyEvePathfinder.EveMap()
    for regionID, regionItem in mapRegionCache.iteritems():
        eveMap.CreateRegion(regionID)
        for constellationID in regionItem.constellationIDs:
            eveMap.CreateConstellation(constellationID, regionID)

    for solarSystemID, ssInfo in mapSystemCache.iteritems():
        eveMap.CreateSolarSystem(solarSystemID, ssInfo.constellationID, ssInfo.securityStatus)

    for jump in mapJumpCache:
        eveMap.AddJump(jump.fromSystemID, jump.toSystemID, jump.stargateID)
        eveMap.AddJump(jump.toSystemID, jump.fromSystemID, jump.stargateID)

    eveMap.Finalize()
    return core.EvePathfinderCore(eveMap)
