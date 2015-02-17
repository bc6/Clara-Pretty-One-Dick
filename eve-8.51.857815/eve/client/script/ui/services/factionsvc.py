#Embedded file name: eve/client/script/ui/services\factionsvc.py
import service
import telemetry
from collections import defaultdict

class Faction(service.Service):
    __exportedcalls__ = {'GetFaction': [],
     'GetCorpsOfFaction': [],
     'GetFactionLocations': [],
     'GetFactionOfSolarSystem': [],
     'GetPirateFactionsOfRegion': []}
    __guid__ = 'svc.faction'
    __notifyevents__ = ['OnSessionChanged']
    __servicename__ = 'account'
    __displayname__ = 'Faction Service'

    def __init__(self):
        service.Service.__init__(self)

    def Run(self, memStream = None):
        self.LogInfo('Starting Faction Svc')
        self.factionIDbyNPCCorpID = None
        self.factionRegions = None
        self.factionConstellations = None
        self.factionSolarSystems = None
        self.factionRaces = None
        self.solarSystemFactions = None
        self.factionStationCount = None
        self.factionSolarSystemCount = None
        self.npcCorpInfo = None
        self.corpsByFactionID = {}
        self.currentFactionID = None

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid2' in change:
            self.currentFactionID = (eve.session.solarsystemid2, self.GetFactionOfSolarSystem(eve.session.solarsystemid2))

    def GetCurrentFactionID(self):
        if self.currentFactionID is None:
            self.currentFactionID = (eve.session.solarsystemid2, self.GetFactionOfSolarSystem(eve.session.solarsystemid2))
        return self.currentFactionID[1]

    @telemetry.ZONE_METHOD
    def GetFactionOfSolarSystem(self, solarsystemID):
        if self.solarSystemFactions is None:
            self.GetData()
        return self.solarSystemFactions.get(solarsystemID, None)

    def GetPirateFactionsOfRegion(self, regionID):
        return {10000001: (500019,),
         10000002: (500010,),
         10000003: (500010,),
         10000005: (500011,),
         10000006: (500011,),
         10000007: (500011,),
         10000008: (500011,),
         10000009: (500011,),
         10000010: (500010,),
         10000011: (500011,),
         10000012: (500011,),
         10000014: (500019,),
         10000015: (500010,),
         10000016: (500010,),
         10000020: (500019,),
         10000022: (500019,),
         10000023: (500010,),
         10000025: (500011,),
         10000028: (500011,),
         10000029: (500010,),
         10000030: (500011,),
         10000031: (500011,),
         10000032: (500020,),
         10000033: (500010,),
         10000035: (500010,),
         10000036: (500019,),
         10000037: (500020,),
         10000038: (500012,),
         10000039: (500019,),
         10000041: (500020,),
         10000042: (500011,),
         10000043: (500019,),
         10000044: (500020,),
         10000045: (500010,),
         10000046: (500020,),
         10000047: (500019,),
         10000048: (500020,),
         10000049: (500012, 500019),
         10000050: (500012,),
         10000051: (500020,),
         10000052: (500012,),
         10000054: (500012,),
         10000055: (500010,),
         10000056: (500011,),
         10000057: (500020,),
         10000058: (500020,),
         10000059: (500019,),
         10000060: (500012,),
         10000061: (500011,),
         10000062: (500011,),
         10000063: (500012,),
         10000064: (500020,),
         10000065: (500012,),
         10000067: (500012,),
         10000068: (500020,)}.get(regionID, ())

    def GetFactionLocations(self, factionID):
        if self.factionRegions is None:
            self.GetData()
        return (self.factionRegions.get(factionID, []), self.factionConstellations.get(factionID, []), self.factionSolarSystems.get(factionID, []))

    def GetFactionInfo(self, factionID):
        if self.factionRegions is None:
            self.GetData()
        return (self.factionRaces.get(factionID, [1,
          2,
          4,
          8]), self.factionStationCount.get(factionID, 0), self.factionSolarSystemCount.get(factionID, 0))

    def Stop(self, memStream = None):
        self.factionIDbyNPCCorpID, self.factionRegions, self.factionConstellations, self.factionSolarSystems, self.factionRaces, self.factionAllies, self.factionEnemies = (None, None, None, None, None, None, None)

    def GetFaction(self, corporationID):
        if self.factionIDbyNPCCorpID is None:
            self.GetData()
        return self.factionIDbyNPCCorpID.get(corporationID, None)

    def GetNPCCorpInfo(self, corpID):
        if self.npcCorpInfo is None:
            self.GetData()
        return self.npcCorpInfo.get(corpID, None)

    def GetCorpsOfFaction(self, factionID):
        if not self.corpsByFactionID:
            self.GetData()
        return self.corpsByFactionID.get(factionID, [])

    @telemetry.ZONE_METHOD
    def GetData(self):
        """
            Prime all faction relevant data
        """
        self.factionIDbyNPCCorpID = {}
        self.corpsByFactionID = defaultdict(list)
        self.factionRaces = {}
        self.npcCorpInfo = {}
        self.factionStationCount = {}
        self.factionSolarSystemCount = {}
        self.factionRegions = defaultdict(list)
        self.factionConstellations = defaultdict(list)
        self.factionSolarSystems = defaultdict(list)
        self.solarSystemFactions = {}
        ownersToPrime = set()
        for corporation in cfg.npccorporations:
            ownersToPrime.add(corporation.corporationID)
            self.factionIDbyNPCCorpID[corporation.corporationID] = corporation.factionID
            self.npcCorpInfo[corporation.corporationID] = corporation
            self.corpsByFactionID[corporation.factionID].append(corporation.corporationID)

        for faction in cfg.factions:
            ownersToPrime.add(faction.factionID)
            self.factionStationCount[faction.factionID] = faction.stationCount
            self.factionSolarSystemCount[faction.factionID] = faction.stationSystemCount
            self.factionRaces[faction.factionID] = []
            for raceID in cfg.races:
                if faction.raceIDs & raceID > 0:
                    self.factionRaces[faction.factionID].append(raceID)

        for regionID, region in cfg.mapRegionCache.iteritems():
            if hasattr(region, 'factionID'):
                self.factionRegions[region.factionID].append(regionID)

        for constellationID, constellation in cfg.mapConstellationCache.iteritems():
            if hasattr(constellation, 'factionID'):
                self.factionConstellations[constellation.factionID].append(constellationID)

        for solarSystemID, solarSystem in cfg.mapSystemCache.iteritems():
            if hasattr(solarSystem, 'factionID'):
                self.factionSolarSystems[solarSystem.factionID].append(solarSystemID)
                self.solarSystemFactions[solarSystemID] = solarSystem.factionID

        if len(ownersToPrime):
            cfg.eveowners.Prime(ownersToPrime)
