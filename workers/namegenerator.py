#Embedded file name: workers\namegenerator.py
from collections import defaultdict
import random
from industry import MANUFACTURING, RESEARCH_TIME, RESEARCH_MATERIAL, COPYING
import workers.staticdata

def _GetFactionID(solarSystemID):
    regionID = cfg.mapSystemCache.Get(solarSystemID).regionID
    return workers.staticdata.factionByRegionID[regionID]


def _GetCorpIDForFactionID(factionID, activity):
    return workers.staticdata.corpIDByFactionAndActivity[activity][factionID]


def _GetCorpIDForSolarSystemAndActivity(solarSystemID, activity):
    factionID = _GetFactionID(solarSystemID)
    return _GetCorpIDForFactionID(factionID, activity)


LETTER_BY_ACTIVYT = {MANUFACTURING: 'M',
 RESEARCH_TIME: 'T',
 RESEARCH_MATERIAL: 'R',
 COPYING: 'C'}

def _GetCharForActivity(activity):
    return LETTER_BY_ACTIVYT[activity]


LETTER_BY_SPECIALITY = {workers.const.TYPE_STRUCTURE: 'T',
 workers.const.TYPE_COMPONENT: 'P',
 workers.const.TYPE_CONSUMABLE: 'C',
 workers.const.TYPE_SHIP: 'S',
 workers.const.TYPE_MOBILE: 'M',
 workers.const.TYPE_EQUIPMENT: 'E'}

def _GetCharForSpeciality(speciality):
    return LETTER_BY_SPECIALITY[speciality]


def _GetCharForSolarSystem(solarSystemID):
    return cfg.evelocations.Get(solarSystemID).name[0]


def _GetTypeIdentifier(solarSystemID, activity, speciality):
    typeIdentifier = '{activity}{speciality}{solarSystem}'.format(activity=_GetCharForActivity(activity), speciality=_GetCharForSpeciality(speciality), solarSystem=_GetCharForSolarSystem(solarSystemID))
    return typeIdentifier


def GenerateName(solarSystemID, activity, speciality):
    corpID = _GetCorpIDForSolarSystemAndActivity(solarSystemID, activity)
    typeIdentifier = _GetTypeIdentifier(solarSystemID, activity, speciality)
    return (corpID, typeIdentifier)


def ConstructName(corpID, typeIdentifier, uniqueIdentifier):
    return u'{corpName}<br>Team {typeIdentifier}{uniqueIdentifier}'.format(corpName=cfg.eveowners.Get(corpID).name, typeIdentifier=typeIdentifier, uniqueIdentifier=str(uniqueIdentifier).zfill(2))


class NameGenerator(object):

    def __init__(self):
        self.registeredNames = defaultdict(set)

    def GenerateNameInfo(self, solarSystemID, activity, speciality):
        corporationID, typeIdentifier = GenerateName(solarSystemID, activity, speciality)
        uniqueIdentifier = self._GetUniqueIdentifier(corporationID, activity, typeIdentifier)
        self.RegisterName(corporationID, activity, typeIdentifier, uniqueIdentifier)
        return (corporationID, typeIdentifier, str(uniqueIdentifier).zfill(2))

    def RegisterName(self, corporationID, activity, typeIdentifier, uniqueIdentifier):
        self.registeredNames[corporationID, activity, typeIdentifier].add(uniqueIdentifier)

    def _GetUniqueIdentifier(self, corporationID, activity, typeIdentifier):
        uniqueIdentifiers = self.registeredNames[corporationID, activity, typeIdentifier]
        try:
            identifier = max(uniqueIdentifiers) + 1
        except ValueError:
            identifier = 0

        if identifier >= 0:
            for i in xrange(100):
                if i not in uniqueIdentifiers:
                    identifier = i
                    break

        return identifier
