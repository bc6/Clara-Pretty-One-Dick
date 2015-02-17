#Embedded file name: evePathfinder\cache.py
"""
This module defines an abstraction around new and old cache formats for the pathfinder
"""
import logging
log = logging.getLogger('eve.pathfinder.cache')
log.addHandler(logging.NullHandler())
import pyEvePathfinder

class NewPathfinderCache(object):
    """
    Wrapper class to provide a common interface for 
    """

    def __init__(self, universeMap):
        log.debug('Creating New pathfinder cache')
        self.internalCache = pyEvePathfinder.EveMapPathfinderCache()
        self.internalCache.Initialize(universeMap)
        self.map = universeMap
        self.dirty = True

    def MarkAsDirty(self):
        self.dirty = True

    def MarkAsClean(self):
        self.dirty = False

    def IsDirty(self):
        return self.dirty

    def ClearCache(self):
        self.internalCache.Clear()

    def GetJumpCountTo(self, solarSystemID):
        return self.internalCache.GetJumpCountTo(self.map, solarSystemID)

    def GetPathTo(self, solarSystemID):
        return self.internalCache.GetRouteTo(self.map, solarSystemID)

    def GetCacheForPathfinding(self):
        return self.internalCache

    def GetSystemsWithinJumpCount(self, minCount, maxCount):
        """
        Returns systems that have a jump count that is >= minCount and < maxCount
        """
        return self.internalCache.GetSystemsWithinJumpCount(self.map, minCount, maxCount)
