#Embedded file name: eve/common/script/universe\locationWrapper.py


class SolarSystemWrapper(object):
    """
    A wrapper to gather information about the solarsystem requested by
    things that call stationSvc.GetSolarSystem
    """
    __guid__ = 'universe.SolarSystemWrapper'

    def __init__(self, solarSystemId):
        solarSystem = cfg.mapSystemCache[solarSystemId]
        self.stringRepresentation = solarSystem.__str__()
        self.solarSystemID = solarSystemId
        self.wormholeClassID = getattr(solarSystem, 'wormholeClassID', None)
        self.factionID = getattr(solarSystem, 'factionID', None)
        self.regionID = solarSystem.regionID
        self.constellationID = solarSystem.constellationID
        self.security = solarSystem.securityStatus
        self.securityStatus = solarSystem.securityStatus
        self.solarSystemName = cfg.evelocations[self.solarSystemID].locationName
        self.planetCount = len(solarSystem.planetCountByType)

    def __str__(self):
        return self.stringRepresentation

    def __repr__(self):
        return self.stringRepresentation
