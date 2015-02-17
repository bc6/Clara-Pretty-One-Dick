#Embedded file name: eve/common/script/util\espwriters.py
"""
This file contains the implementation of the server ESP writers
"""
import urlparse
import time
import carbon.common.script.util.spwriters as spwriters
import carbon.common.script.util.htmlwriter as htmlwriter
import util
import re
import blue
import sys
import carbon.common.script.net.machobase as macho
import os
import localization
import const
from eve.common.script.mgt.appLogConst import groupDailyQuest
from eve.common.script.mgt.appLogConst import groupDustWarbarge
hook_AppSpContentPaperdolls = True
hook_AppSpContentResources = True
hook_AppSpContentWorldSpaces = True
try:
    import logConst
except:
    logConst = util.KeyVal()

from service import ROLEMASK_VIEW, ROLE_ADMIN, ROLE_CONTENT, ROLE_GML, ROLE_GMH, ROLE_PROGRAMMER, ROLE_PETITIONEE
WORMHOLE_CLASS_NAMES = {1: 'Class 1',
 2: 'Class 2',
 3: 'Class 3',
 4: 'Class 4',
 5: 'Class 5',
 6: 'Class 6',
 7: 'Class 7 Hisec',
 8: 'Class 8 Lowsec',
 9: 'Class 9 Nullsec',
 10: 'Testing Class A (10)',
 11: 'Testing Class B (11)',
 12: 'Class 12 Thera',
 13: 'Class 13 Small Shattered'}

class ESPHtmlWriter(spwriters.SPHtmlWriter):
    __guid__ = 'htmlwriter.ESPHtmlWriter'

    def __init__(self, *params):
        spwriters.SPHtmlWriter.__init__(self, *params)
        self.AddCssFile('/static/css/bootstrap.stripped.css')
        self.AddJsFile('/static/js/libs/bootstrap.js')
        self.AddCssFile('/static/css/select2.css')
        self.AddJsFile('/static/js/libs/select2.js')
        self.AddJsFile('/gd/js/formutils.js')

    def SelectCharacter(self):
        if session.charid is None:
            urlparameters = ''
            for q in self.request.query.iteritems():
                if q[0] is not '':
                    urlparameters += '%s=%s&' % q

            session.redirecturl = self.request.path + '?' + urlparameters
            self.response.Redirect('/gm/character.py?action=MyCharacters&')

    def AppBottomLeft(self):
        s = spwriters.SPHtmlWriter.AppBottomLeft(self)
        if macho.mode == 'server':
            if session.charid:
                s += ' - <a href="/gm/character.py?action=LogOffCharacter&"><font color=SILVER>Logoff</font></a>'
        return s

    if macho.mode == 'server':

        def GetOperationText(self, operationID, isDescription = False):
            if operationID not in self.cache.Index(const.cacheStaOperations):
                return ''
            if isDescription:
                return localization.GetByMessageID(self.cache.Index(const.cacheStaOperations, operationID).descriptionID)
            return localization.GetByMessageID(self.cache.Index(const.cacheStaOperations, operationID).operationNameID)

        def GetRoleDescription(self, roleID, isShort = False):
            if roleID not in self.cache.Index(const.cacheCrpRoles):
                return ''
            if isShort:
                return localization.GetByMessageID(self.cache.Index(const.cacheCrpRoles, roleID).shortDescriptionID)
            return localization.GetByMessageID(self.cache.Index(const.cacheCrpRoles, roleID).descriptionID)

        def GetCelestialDescription(self, itemID):
            if itemID in self.cache.Index(const.cacheMapCelestialDescriptions):
                return localization.GetByMessageID(self.cache.Index(const.cacheMapCelestialDescriptions, itemID).descriptionID)
            return ''

        def GetCorpActivityName(self, activityID):
            if activityID in self.cache.Index(const.cacheCrpActivities):
                return localization.GetByMessageID(self.cache.Index(const.cacheCrpActivities, activityID).activityNameID)
            return ''

        def MetaGroupLink(self, metaGroupID, linkText = None, props = ''):
            if metaGroupID is None:
                return ''
            else:
                if linkText is None:
                    linkText = cfg.invmetagroups.Get(metaGroupID).metaGroupName
                    if linkText is None:
                        return self.FontRed('Unknown')
                return self.Link('/gd/type.py', linkText, {'action': 'MetaGroups'}, props)

        def OwnerLink(self, ownerID, ownerTypeID = None, linkText = None, props = ''):
            if ownerID is None:
                return ''
            if ownerTypeID is None:
                try:
                    owner = cfg.eveowners.Get(ownerID)
                except:
                    sys.exc_clear()
                    if linkText is None:
                        return self.FontRed('???')
                    else:
                        return linkText

                ownerTypeID = owner.typeID
                if not linkText:
                    linkText = owner.ownerName
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            if ownerTypeID == const.typeFaction:
                return self.FactionLink(ownerID, linkText, props)
            elif ownerTypeID == const.typeCorporation:
                return self.CorporationLink(ownerID, linkText, props)
            elif ownerTypeID == const.typeAlliance:
                return self.AllianceLink(ownerID, linkText, props)
            elif ownerTypeID == const.typeSystem:
                return linkText
            else:
                return self.CharacterLink(ownerID, linkText, props)

        def LocationLink(self, locationID, linkText = None, props = ''):
            if locationID is None:
                return ''
            if linkText is None:
                if locationID < 70000000 or locationID > 80000000:
                    try:
                        location = cfg.evelocations.Get(locationID)
                    except:
                        sys.exc_clear()
                        return self.FontRed('???')

                    linkText = location.locationName
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            if locationID < const.minRegion:
                return linkText
            elif locationID < const.minConstellation:
                return self.RegionLink(locationID, linkText, props)
            elif locationID < const.minSolarSystem:
                return self.ConstellationLink(locationID, linkText, props)
            elif locationID < const.minUniverseCelestial:
                return self.SystemLink(locationID, linkText, props)
            elif locationID < const.minStation:
                return linkText
            elif locationID < const.minUniverseAsteroid:
                return self.StationLink(locationID, linkText, props)
            else:
                return linkText

        def CharacterLink(self, characterID, linkText = None, props = '', noHover = False):
            if util.IsDustCharacter(characterID):
                return spwriters.SPHtmlWriter.CharacterLink(self, characterID, linkText, props)
            if characterID is None:
                return ''
            if linkText is None:
                linkText = self.OwnerName(characterID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gm/character.py?action=Character&characterID=%s' % characterID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=1' % characterID, title=linkText, caption=linkText)

        def CharacterLinkActions(self, characterID, linkText = None, actions = []):
            if characterID is None:
                return ''
            if linkText is None:
                linkText = self.OwnerName(characterID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltipActions(href='/gm/character.py?action=Character&characterID=%s' % characterID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=1' % characterID, title=linkText, caption=linkText, actions=actions)

        def PetitionLink(self, petID, linkText = None, props = ''):
            if petID is None:
                return ''
            else:
                if linkText is None:
                    linkText = 'ticket'
                if linkText is not None:
                    linkText = self.HTMLEncode(linkText)
                return self.Link('/gm/petitionClient.py', linkText, {'action': 'ViewPetition',
                 'petitionID': petID}, props)

        def CorporationLink(self, corporationID, linkText = None, props = ''):
            if corporationID is None:
                return ''
            if linkText is None:
                linkText = self.OwnerName(corporationID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gm/corporation.py?action=Corporation&corporationID=%s' % corporationID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=3' % corporationID, title=linkText, caption=linkText)

        def AllianceLink(self, allianceID, linkText = None, props = ''):
            if allianceID is None:
                return ''
            if linkText is None:
                linkText = self.OwnerName(allianceID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gm/alliance.py?action=Alliance&allianceID=%s' % allianceID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=9' % allianceID, title=linkText, caption=linkText)

        def WarableEntityLink(self, ownerID, linkText = None, props = ''):
            if ownerID is None:
                return ''
            else:
                if linkText is None:
                    linkText = self.OwnerName(ownerID)
                    if linkText is None:
                        return self.FontRed('Unknown')
                if linkText is not None:
                    linkText = self.HTMLEncode(linkText)
                return self.Link('/gm/war.py', linkText, {'action': 'WarableEntity',
                 'ownerID': ownerID}, props)

        def FactionLink(self, factionID, linkText = None, props = ''):
            if factionID is None:
                return ''
            if linkText is None:
                linkText = self.OwnerName(factionID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gm/faction.py?action=Faction&factionID=%s' % factionID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=8' % factionID, title=linkText, caption=linkText)

        def StationLink(self, stationID, linkText = None, props = ''):
            if stationID is None:
                return ''
            if linkText is None:
                linkText = self.LocationName(stationID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gm/stations.py?action=Station&stationID=%s' % stationID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=7' % stationID, title=linkText, caption=linkText)

        def WorldSpaceLink(self, worldSpaceID, linkText = None, props = ''):
            if worldSpaceID is None:
                return ''
            else:
                if linkText is None:
                    linkText = self.LocationName(worldSpaceID)
                    if linkText is None:
                        return self.FontRed('Unknown')
                if linkText is not None:
                    linkText = self.HTMLEncode(linkText)
                return self.Link('/gm/worldSpaces.py', linkText, {'action': 'WorldSpace',
                 'worldspaceID': worldSpaceID}, props)

        def SystemLink(self, systemID, linkText = None, props = ''):
            if systemID is None:
                return ''
            if linkText is None:
                linkText = self.LocationName(systemID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gd/universe.py?action=System&systemID=%s' % systemID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=4' % systemID, title=linkText, caption=linkText)

        def ConstellationLink(self, constellationID, linkText = None, props = ''):
            if constellationID is None:
                return ''
            if linkText is None:
                linkText = self.LocationName(constellationID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gd/universe.py?action=Constellation&constellationID=%s' % constellationID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=6' % constellationID, title=linkText, caption=linkText)

        def RegionLink(self, regionID, linkText = None, props = ''):
            if regionID is None:
                return ''
            if linkText is None:
                linkText = self.LocationName(regionID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gd/universe.py?action=Region&regionID=%s' % regionID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=5' % regionID, title=linkText, caption=linkText)

        def PlanetLink(self, planetID, linkText = None, props = ''):
            if planetID is None:
                return ''
            if linkText is None:
                linkText = self.LocationName(planetID)
                if linkText is None:
                    return self.FontRed('Unknown')
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.GetTooltip(href='/gd/universe.py?action=Celestial&celestialID=%s' % planetID, ajax='/gm/worker_info.py?action=FetchInfo&id=%s&idType=10' % planetID, title=linkText, caption=linkText)

        def DistrictLink(self, district, text = None, props = ''):
            if district is None:
                return ''
            if isinstance(district, (int, long)):
                district = self.session.ServiceProxy('districtManager').GetDistrict(district)
            if text is None:
                text = localization.GetImportantByLabel('UI/Locations/LocationDistrictFormatter', solarSystemID=district['solarSystemID'], romanCelestialIndex=util.IntToRoman(district['celestialIndex']), districtIndex=district['index'])
                if text is None:
                    return self.FontRed('Unknown')
            if text is not None:
                text = self.HTMLEncode(text)
            return self.Link('/dust/districts.py', text, {'action': 'District',
             'districtID': district['districtID']}, props)

        def BattleLink(self, battle, text = None, props = ''):
            if battle is None:
                return ''
            if isinstance(battle, (int, long)):
                battle = self.session.ServiceProxy('battleManager').GetBattleInfo(battle)
            if not text:
                if battle['battleName']:
                    text = battle['battleName']
                elif battle['queueID']:
                    text = 'Queue Battle (%s) - %s' % (const.battleQueues[battle['queueID']]['name'], battle['battleID'])
                elif battle['conflictID'] and battle['conflictID'] > 0:
                    if battle['attackerID'] in const.battleMilitiaCorporations or battle['defenderID'] in const.battleMilitiaCorporations:
                        text = 'Faction Battle - %s' % battle['battleID']
                    else:
                        text = 'Corporation Battle - %s' % battle['battleID']
                else:
                    text = 'Battle - %s' % battle['battleID']
            return self.Link('/dust/battles.py', text, {'action': 'Battle',
             'battleID': battle['battleID']}, props)

        def ConflictLink(self, conflict):
            if isinstance(conflict, int):
                return self.Link('districts.py', 'Conflict - %s' % conflict, {'action': 'Conflict',
                 'conflictID': conflict})
            if isinstance(conflict, dict):
                return self.Link('districts.py', 'Conflict - %s' % conflict['conflictID'], {'action': 'Conflict',
                 'conflictID': conflict['conflictID']})

        def MapLink(self, itemID, linkText = 'Map', props = ''):
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            if itemID is None:
                return ''
            else:
                return self.Link('/gd/universe.py', linkText, {'action': 'Map',
                 'itemID': itemID}, props)

        def MissionLink(self, contentID, linkText = None, props = ''):
            if contentID in self.cache.Index(const.cacheAgtContentTemplates):
                r = self.cache.Index(const.cacheAgtContentTemplates, contentID)
                if linkText is None:
                    t = r.contentTemplate
                    t = t[t.find('_') + 1:]
                    linkText = localization.GetByMessageID(r.contentNameID)
                return '%s - %s' % (t, self.Link('/gd/agents.py', linkText, {'action': 'CreateOrEditContent',
                  'contentID': contentID,
                  'contentTemplate': r.contentTemplate,
                  'edit': 0}))
            else:
                return self.FontRed('Mission not found')

        def RewardLink(self, rewardID, linkText = None, props = ''):
            if linkText is None:
                row = self.DB2.SQLInt('name', 'reward.rewards', '', '', 'rewardID', rewardID)
                if len(row) == 0:
                    return 'Deleted reward'
                linkText = row.name
            if linkText is not None:
                linkText = self.HTMLEncode(linkText)
            return self.Link('/gd/rewards.py', linkText, {'action': 'ViewReward',
             'rewardID': rewardID}, props)

        def PinLink(self, pinID, linkText = None, props = ''):
            pinName = linkText
            if pinName is None:
                pinRow = self.DB2.SQLBigInt('typeID', 'planet.pins', '', '', 'pinID', pinID)
                if len(pinRow) == 0:
                    return 'Deleted pin'
                pinName = cfg.invtypes.Get(pinRow[0].typeID).name
            if pinName is not None:
                pinName = self.HTMLEncode(pinName)
            return self.Link('/gm/planets.py', pinName, {'action': 'ViewPin',
             'pinID': pinID}, props)

        def PinTypeLink(self, pinID, linkText = None, props = ''):
            pinRow = self.DB2.SQLBigInt('typeID', 'planet.pins', '', '', 'pinID', pinID)[0]
            pinTypeID = pinRow.typeID
            pinName = linkText
            if pinName is None:
                pinName = cfg.invtypes.Get(pinRow.typeID).name
            if pinName is not None:
                pinName = self.HTMLEncode(pinName)
            return self.TypeLink(pinTypeID, linkText=pinName, props=props)

        def SchematicLink(self, schematicID, linkText = None, props = ''):
            schematicName = linkText
            if schematicName is None:
                schematicName = cfg.schematics.Get(schematicID).schematicName
            if schematicName is not None:
                schematicName = self.HTMLEncode(schematicName)
            return self.Link('/gd/schematics.py', schematicName, {'action': 'View',
             'schematicID': schematicID})

        def RecipeLink(self, parentID, parentType, text = None):
            """ parentID can be a typeID, groupID or categoryID """
            if text is None:
                text = self.HTMLEncode(text)
                if parentType == const.cef.PARENT_TYPEID:
                    text = cfg.invtypes.Get(parentID).typeName
                elif parentType == const.cef.PARENT_GROUPID:
                    text = cfg.invgroups.Get(parentID).groupName
                else:
                    text = cfg.invcategories.Get(parentID).categoryName
            if text is not None:
                text = self.HTMLEncode(text)
            return self.Link('/gd/entities.py', text, {'action': 'Recipe',
             'parentID': parentID,
             'parentType': parentType})

        def GetWormholeClassName(self, wormholeClassID):
            return WORMHOLE_CLASS_NAMES.get(wormholeClassID, 'N/A')

        def SystemHeader(self, systemID, smallHeader = 1, menuPlacement = 'rMenu'):
            solarSystem = cfg.mapSystemCache[systemID]
            factionID = getattr(solarSystem, 'factionID', None)
            combatZonesFilteredBySystem = self.cache.Filter(const.cacheFacWarCombatZoneSystems, 'solarSystemID')
            if factionID is None:
                image = '/img/system.jpg'
            else:
                image = '/img/faction%s.jpg' % factionID
            lines = []
            lines.append([1, 'Constellation', self.FSDField(self.ConstellationLink(solarSystem.constellationID))])
            lines.append([1, 'Region', self.FSDField(self.RegionLink(solarSystem.regionID))])
            if smallHeader == 0 and systemID in combatZonesFilteredBySystem:
                combatZoneID = combatZonesFilteredBySystem[systemID][0].combatZoneID
                combatZoneName = self.cache.IndexText(const.cacheFacWarCombatZones, combatZoneID)
                lines.append([0, 'Combat Zone', self.Link('/gd/combatZones.py', combatZoneName, {'action': 'Zone',
                  'zoneID': combatZoneID})])
            if factionID:
                lines.append([0, 'Faction', self.FSDField(self.FactionLink(factionID))])
            lines.append([0, 'Security', self.FSDField(solarSystem.securityStatus)])
            self.SubjectHeader(smallHeader, 'SYSTEM', systemID, cfg.evelocations[systemID].name, '#FFFF80', image, '/gd/universe.py', 'System', 'systemID', lines)
            li = []
            li.append('#SYSTEM')
            li.append(self.Link('/gd/universe.py', 'INFO', {'action': 'System',
             'systemID': systemID}))
            li.append('-')
            li.append(self.Link('/gd/universe.py', 'Population and Park Load', {'action': 'PopulationParkLoad',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Jumps', {'action': 'Jumps',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Stations', {'action': 'Stations',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Sovereignty Structures', {'action': 'SovereigntyStructures',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Starbases', {'action': 'Starbases',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Celestials', {'action': 'Celestials',
             'systemID': systemID}) + self.MidDot() + self.Link('/gd/universe.py', 'Moons', {'action': 'Moons',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Asteroid Belts', {'action': 'AsteroidBelts',
             'systemID': systemID}) + self.MidDot() + self.Link('/gd/universe.py', 'Asteroids', {'action': 'Asteroids',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Development Indices', {'action': 'DevelopmentIndices',
             'systemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Cargo Links', {'action': 'SystemCargoLinks',
             'systemID': systemID}))
            li.append(self.Link('/gm/logs.py', 'Events', {'action': 'ItemEvents',
             'itemID': systemID}))
            li.append(self.Link('/gd/universe.py', 'Factional Warfare', {'action': 'FactionalWarfare',
             'systemID': systemID}))
            li.append(self.Link('/gm/inventory.py', 'Find Item', {'action': 'FindItem',
             'locationID': systemID}))
            if session.role & (ROLE_GMH | ROLE_CONTENT | ROLE_ADMIN) > 0:
                li.append(self.Link('/gd/universe.py', 'Free Slots', {'action': 'FreeSlots',
                 'systemID': systemID}))
            if session.role & ROLE_CONTENT > 0:
                li.append(self.Link('/gd/universe.py', 'Product Distributions', {'action': 'ProductDistributions',
                 'systemID': systemID}))
            li.append(self.Link('/info/map.py', 'List Pilots', {'action': 'PilotsInSolarSystem',
             'solarSystemID': systemID}))
            li.append(self.Link('/info/map.py', 'Map Details', {'action': 'MapDetails',
             'solarSystemID': systemID}))
            li.append('-')
            li.append(self.FontGray('Dungeons and Complexes'))
            li.append('>' + self.Link('/gd/universe.py', 'Dungeons', {'action': 'DungeonList',
             'systemID': systemID}) + self.MidDot() + self.Link('/gd/universe.py', 'Distributions', {'action': 'DungeonDistributions',
             'solarSystemID': systemID}))
            li.append('>' + self.Link('/gd/universe.py', 'Spawnpoints', {'action': 'Spawnpoints',
             'systemID': systemID}) + self.MidDot() + self.Link('/gd/universe.py', 'Agent Spawnpoints', {'action': 'AgentSpawnpoints',
             'systemID': systemID}))
            li.append('>' + self.Link('/gd/dungeonDistributions.py', 'Wormholes', {'action': 'ShowWormholesBySystem',
             'systemID': systemID}))
            li.append('-')
            li.append(self.FontGray('Cluster'))
            li.append('>' + self.Link('/gd/universe.py', 'Go to System Node', {'action': 'GotoNodeFromSolarSystemID',
             'solarSystemID': systemID}))
            li.append('>' + self.Link('/admin/network.py', 'Node History', {'action': 'AddressDetails',
             'serviceID': 2,
             'addressID': systemID}))
            self.SubjectActions(li, menuPlacement)
            return solarSystem

        def GetPlanetSystemConstellationAndRegionIDs(self, planetID):
            planet = cfg.mapSolarSystemContentCache.planets[planetID]
            solarSystem = cfg.mapSystemCache[planet.solarSystemID]
            return (solarSystem.solarSystemID, solarSystem.constellationID, solarSystem.regionID)

        def GetMoonSystemConstellationAndRegionIDs(self, moonID):
            moon = cfg.mapSolarSystemContentCache.moons[moonID]
            return self.GetPlanetSystemConstellationAndRegionIDs(moon.orbitID)

        def CelestialHeader(self, celestialID, smallHeader = 1, menuPlacement = 'rMenu'):
            isPlanet = celestialID in cfg.mapSolarSystemContentCache.planets
            if isPlanet:
                solarSystemID, constellationID, regionID = self.GetPlanetSystemConstellationAndRegionIDs(celestialID)
            else:
                solarSystemID, constellationID, regionID = self.GetMoonSystemConstellationAndRegionIDs(celestialID)
            celestial = cfg.mapSolarSystemContentCache.celestials[celestialID]
            lines = []
            typeName = self.SP.TypeName(celestial.typeID)
            lines.append([1, 'System', self.FSDField(self.SystemLink(solarSystemID))])
            lines.append([1, 'Constellation', self.FSDField(self.ConstellationLink(constellationID))])
            lines.append([1, 'Region', self.FSDField(self.RegionLink(regionID))])
            self.SubjectHeader(smallHeader, typeName, celestialID, self.FSDField(cfg.evelocations.Get(celestialID).locationName), '#C0C0C0', '/img/celestial.jpg', '/gd/universe.py', 'Celestial', 'celestialID', lines)
            li = []
            li.append('#%s' % typeName)
            li.append(self.Link('/gd/universe.py', 'INFO', {'action': 'Celestial',
             'celestialID': celestialID}))
            li.append('-')
            li.append(self.Link('/gd/universe.py', 'Orbit Celestials', {'action': 'OrbitCelestials',
             'celestialID': celestialID}))
            li.append(self.Link('/gd/universe.py', 'Customs Offices', {'action': 'CustomsOffices',
             'planetID': celestialID}))
            li.append(self.Link('/gd/universe.py', 'Resource Distributions', {'action': 'ResourceDistributions',
             'planetID': celestialID}))
            li.append('-')
            li.append(self.FontGray('Planetary Interaction'))
            li.append('>' + self.Link('/gm/planets.py', 'Colonies', {'action': 'Colonies',
             'planetID': celestialID}))
            li.append('-')
            li.append(self.FontGray('Cluster'))
            li.append('>' + self.Link('/gm/planets.py', 'Go to Planet Node', {'action': 'GotoNodeForPlanetID',
             'planetID': celestialID,
             'redirectAction': 'Planet'}))
            li.append('>' + self.Link('/admin/network.py', 'Node History', {'action': 'AddressDetails',
             'serviceID': 23,
             'addressID': celestialID}))
            self.SubjectActions(li, menuPlacement)
            return celestial

        def ComboRaces(self, allowNone = 0):
            combo = {}
            if allowNone:
                combo[0] = '(none)'
            for r in cfg.races:
                combo[r.raceID] = r.raceName

            return combo

        def ComboBloodlines(self, allowNone = 0):
            combo = {}
            if allowNone:
                combo[0] = '(none)'
            for b in self.cache.Rowset(const.cacheChrBloodlines):
                r = cfg.races.Get(b.raceID)
                combo[b.bloodlineID] = '%s, %s' % (localization.GetByMessageID(r.raceNameID), localization.GetByMessageID(b.bloodlineNameID))

            return combo

        def SelectCategory(self, action, categoryID, placement = 'rMenu'):
            categories = []
            for c in cfg.invcategories:
                if c.categoryID > 0:
                    bon = ''
                    boff = ''
                    if c.categoryID == categoryID:
                        bon = '<b>'
                        boff = '</b>'
                    categories.append([c.categoryName, bon + self.Link('', c.categoryName, {'action': action,
                      'categoryID': c.categoryID}) + boff])

            categories.sort()
            categories = map(lambda line: line[1:], categories)
            if categoryID is None:
                self.Write(self.WebPart('Categories', self.GetTable([], categories), 'wpCategories'))
                return 0
            else:
                self.WriteDirect(placement, self.WebPart('Categories', self.GetTable([], categories), 'wpCategories'))
                return 1

        def SelectCategoryGroup(self, action, categoryID, groupID, placement = 'rMenu', webPart = None):
            if categoryID is None and groupID is not None:
                categoryID = cfg.invgroups.Get(groupID).categoryID
            categories = []
            for c in cfg.invcategories:
                if c.categoryID > 0:
                    bon = ''
                    boff = ''
                    if c.categoryID == categoryID:
                        bon = '<b>'
                        boff = '</b>'
                    categories.append([c.categoryName, bon + self.Link('', c.categoryName, {'action': action,
                      'categoryID': c.categoryID}) + boff])

            categories.sort()
            categories = map(lambda line: line[1:], categories)
            if categoryID is None:
                self.Write(self.WebPart('Categories', self.GetTable([], categories), 'wpCategories'))
                return 0
            else:
                groups = []
                for g in cfg.groupsByCategories.get(categoryID, []):
                    bon = ''
                    boff = ''
                    if g.groupID == groupID:
                        bon = '<b>'
                        boff = '</b>'
                    groups.append([g.groupName, bon + self.Link('', g.groupName, {'action': action,
                      'categoryID': categoryID,
                      'groupID': g.groupID}) + boff])

                groups.sort()
                groups = map(lambda line: line[1:], groups)
                if groupID is None:
                    self.Write(self.WebPart('Groups', self.GetTable([], groups), 'wpGroups'))
                    self.WriteDirect(placement, self.WebPart('Categories', self.GetTable([], categories), 'wpCategories'))
                    return 0
                if webPart:
                    self.WriteDirect(placement, webPart)
                self.WriteDirect(placement, self.WebPart('Groups', self.GetTable([], groups), 'wpGroups'))
                self.WriteDirect(placement, self.WebPart('Categories', self.GetTable([], categories), 'wpCategories'))
                return 1

        def SelectCategoryGroupType(self, action, categoryID, groupID, placement = 'rMenu'):
            if self.SelectCategoryGroup(action, categoryID, groupID, placement):
                li = []
                for t in cfg.typesByGroups.get(groupID, []):
                    li.append([t.typeID, self.Link('', t.typeName, {'action': action,
                      'categoryID': categoryID,
                      'groupID': groupID,
                      'typeID': t.typeID})])

                self.LinesSortByLink(li, 1)
                self.Write(self.WebPart('Types', self.GetTable(['id', 'name'], li), 'wpTypes'))

        def SelectRegion(self, action, regionID):
            li = []
            for r in self.DB2.SQL('SELECT * FROM map.regionsDx ORDER BY regionName'):
                bon = ''
                boff = ''
                if r.regionID == regionID:
                    bon = '<b>'
                    boff = '</b>'
                li.append([bon + self.Link('', self.IsBlank(r.regionName, r.regionID), {'action': action,
                  'regionID': r.regionID}) + boff])

            regSel = self.GetTable([], li)
            if regionID is None:
                self.Write(self.WebPart('Select Region', regSel, 'wpRegSel'))
                return 0
            else:
                self.WriteDirect('rMenu', self.WebPart('Regions', regSel, 'wpRegSel'))
                return 1

        def SelectRegionConstellation(self, action, regionID, constellationID):
            if self.SelectRegion(action, regionID):
                li = []
                for c in self.DB2.SQLInt('constellationID, constellationName', 'map.constellationsDx', '', 'constellationName', 'regionID', regionID):
                    bon = ''
                    boff = ''
                    if c.constellationID == constellationID:
                        bon = '<b>'
                        boff = '</b>'
                    li.append([bon + self.Link('', self.IsBlank(c.constellationName, c.constellationID), {'action': action,
                      'regionID': regionID,
                      'constellationID': c.constellationID}) + boff])

                conSel = self.GetTable([], li)
                if constellationID is None:
                    self.Write(self.WebPart('Select Constellation', conSel, 'wpConSel'))
                    return 0
                else:
                    self.WriteDirect('rMenu', self.WebPart('Constellations', conSel, 'wpConSel'))
                    return 1

        def SelectRegionConstellationSolarSystem(self, action, regionID, constellationID, solarSystemID):
            if self.SelectRegionConstellation(action, regionID, constellationID):
                li = []
                for s in self.DB2.SQLInt('solarSystemID, solarSystemName', 'map.solarSystemsDx', '', 'solarSystemName', 'constellationID', constellationID):
                    bon = ''
                    boff = ''
                    if s.solarSystemID == solarSystemID:
                        bon = '<b>'
                        boff = '</b>'
                    li.append([bon + self.Link('', self.IsBlank(s.solarSystemName, s.solarSystemID), {'action': action,
                      'regionID': regionID,
                      'constellationID': constellationID,
                      'solarSystemID': s.solarSystemID}) + boff])

                solSel = self.GetTable([], li)
                if solarSystemID is None:
                    self.Write(self.WebPart('Select Solar System', solSel, 'wpSolSel'))
                    return 0
                else:
                    self.WriteDirect('rMenu', self.WebPart('Solar Systems', solSel, 'wpSolSel'))
                    return 1

        def AddTableItem(self, lines, r, owner, location, category = 0, checkBox = 0):
            t = cfg.invtypes.Get(r.typeID)
            g = cfg.invgroups.Get(t.groupID)
            c = cfg.invcategories.Get(g.categoryID)
            cgtn = str(r.typeID) + ': '
            if category:
                if c.categoryName != g.groupName:
                    cgtn += c.categoryName + ', '
            if g.groupName == t.typeName:
                cgtn += self.TypeLink(r.typeID, t.typeName)
            else:
                cgtn += g.groupName + ', ' + self.TypeLink(r.typeID, t.typeName)
            itemName = self.SP.EspItemName(0, r.itemID, r.quantity, r.typeID, t.groupID, g.categoryID)
            if itemName != '':
                cgtn += ': <b>' + itemName + '</b>'
            attr = ''
            if r.quantity < 0:
                attr += ' S'
                if r.quantity != -1:
                    attr += self.FontRed(r.quantity)
            else:
                attr += ' %d' % r.quantity
            line = []
            if checkBox == 1:
                line.append('<input type="checkbox" name="itemID" value="%s">' % r.itemID)
            line.append(self.ItemID(r.itemID))
            line.append(cgtn)
            if owner:
                ownerName = self.SP.EspItemName(1, r.ownerID)
                if ownerName == '':
                    line.append(self.ItemID(r.ownerID))
                else:
                    line.append(self.ItemID(r.ownerID) + ': ' + ownerName)
            if location:
                locationName = self.SP.EspItemName(2, r.locationID)
                if locationName == '':
                    line.append(self.ItemID(r.locationID))
                else:
                    line.append(self.ItemID(r.locationID) + ': ' + locationName)
            line.append('%d: %s' % (r.flagID, self.config.GetFlags(r.flagID).flagName))
            line.append(attr)
            act = ''
            if t.groupID == const.groupCharacter:
                act = self.CharacterLink(r.itemID, 'Character')
            elif t.groupID == const.groupCorporation:
                act = self.CorporationLink(r.itemID, 'Corporation')
            elif t.groupID == const.groupFaction:
                act = self.FactionLink(r.itemID, 'Faction')
            elif t.groupID == const.groupRegion:
                act = self.RegionLink(r.itemID, 'Region')
            elif t.groupID == const.groupConstellation:
                act = self.ConstellationLink(r.itemID, 'Constellation')
            elif t.groupID == const.groupSolarSystem:
                act = self.SystemLink(r.itemID, 'System')
            elif t.groupID == const.groupStation:
                act = self.StationLink(r.itemID, 'Station')
            elif t.groupID == const.groupControlTower:
                act = self.Link('/gm/starbase.py', 'Starbase', {'action': 'Starbase',
                 'towerID': r.itemID})
            elif t.groupID == const.groupPlanet:
                act = self.Link('/gd/universe.py', 'Planet', {'action': 'Planet',
                 'planetID': r.itemID})
            elif t.groupID == const.groupAsteroidBelt:
                act = self.Link('/gd/universe.py', 'Belt', {'action': 'AsteroidBelt',
                 'asteroidBeltID': r.itemID})
            line.append(act)
            lines.append(line)

        def AddTypeSelector(self, form, name = '', depth = 'type'):
            self.WriteScript('\n                function replaceOptions(sElement, newOptions)\n                {\n                    for (i=document.all[sElement].length; i > -1; i--)\n                    {\n                        document.all[sElement].options[i]=null\n                    }\n                    for (i = 0; i < newOptions.length; i += 2)\n                    {\n                        document.all[sElement].add(new Option( newOptions[i], newOptions[i+1]))\n                    }\n                }\n                ')
            self.WriteScript('c=new ActiveXObject("Scripting.Dictionary");\n')
            self.WriteScript('g=new ActiveXObject("Scripting.Dictionary");\n')
            s = htmlwriter.UnicodeMemStream()
            for g in cfg.invgroups:
                self.BeNice()
                if g.groupID not in cfg.typesByGroups:
                    continue
                typesByGroup = cfg.typesByGroups[g.groupID].Copy()
                typesByGroup.Sort('typeName')
                s.Write('g.Add("%d", new Array(' % g.groupID)
                for t in typesByGroup:
                    self.BeNice()
                    typeName = t.typeName.replace('"', "'")
                    typeName = typeName.replace('\n', '')
                    typeName = typeName.replace('\r', '')
                    s.Write('"%s",%d,' % (str(typeName), t.typeID))

                s.Seek(s.pos - 1)
                s.Write('));\n')

            cic = {}
            for c in cfg.invcategories:
                self.BeNice()
                if c.categoryID not in cfg.groupsByCategories:
                    continue
                groupsByCategory = cfg.groupsByCategories[c.categoryID].Copy()
                groupsByCategory.Sort('groupName')
                cic[c.categoryID] = c.name
                s.Write('c.Add("%d", new Array(' % c.categoryID)
                for g in groupsByCategory:
                    self.BeNice()
                    s.Write('"%s",%d,' % (str(g.groupName.replace('"', "'")), g.groupID))

                s.Seek(s.pos - 1)
                s.Write('));\n')

            s.Seek(0)
            self.WriteScript(str(s.Read()))
            form.AddSelect(name + 'categoryid', cic, 'Category', None, 0, 'onChange="replaceOptions(\'' + name + "groupid',c(this.options[this.selectedIndex].value)); replaceOptions('" + name + "typeid',g(document.all['" + name + 'groupid\'].options[0].value))"')
            if depth == 'type' or depth == 'group':
                form.AddSelect(name + 'groupid', {}, 'Group', None, 0, 'onChange="replaceOptions(\'' + name + 'typeid\',g(this.options[this.selectedIndex].value))"')
            if depth == 'type':
                form.AddSelect(name + 'typeid', {}, 'Type')

        def QuickLinks(self, text):
            pup = re.compile('charid\\((\\d+)\\)', re.IGNORECASE)
            text = pup.sub('<a href=character.py?action=Character&characterID=\\1>\\1</a>', text)
            pup = re.compile('userid\\((\\d+)\\)', re.IGNORECASE)
            text = pup.sub('<a href=users.py?action=User&userID=\\1>\\1</a>', text)
            pup = re.compile('itemid\\((\\d+)\\)', re.IGNORECASE)
            text = pup.sub('<a href=../gm/inventory.py?action=Item&itemID=\\1>\\1</a>', text)
            pup = re.compile('petid\\((\\d+)\\)', re.IGNORECASE)
            text = pup.sub('<a href=petitionClient.py?action=ViewPetition&petitionID=\\1>\\1</a>', text)
            return text

        def GetOwnerImage(self, ownerType, ownerID, width = 128):
            if ownerType == 'Character':
                extension = 'jpg'
            else:
                extension = 'png'
            serverLink = sm.GetService('machoNet').GetGlobalConfig().get('imageserverurl')
            if serverLink == '':
                return
            if serverLink is None:
                serverLink = 'http://%s.dev.image/' % os.environ.get('USERNAME').replace('.', '_').lower()
            serverLink += '%s/%d_%d.%s'
            return serverLink % (ownerType,
             ownerID,
             width,
             extension)

        def GetTransferDelay(self):
            transferDelay = self.cache.Setting('Character', 'TransferDelay')
            if transferDelay == '':
                return 10
            return int(transferDelay)

        def GetTransferQueue(self, transferQueue, displayLastEmailChange = False, displayLastPasswordChange = False):
            transferDelay = self.GetTransferDelay()
            header = ['Character',
             'Old User',
             'New User',
             'IP Number',
             'IP Info',
             'Transfer Requested',
             'Transfer Delay Ends']
            if displayLastEmailChange:
                header.append('Old User Email Changed (last 7d)')
            if displayLastPasswordChange:
                header.append('Old User Password Changed (last 7d)')
            lines = []
            for item in transferQueue:
                line = [self.CharacterLink(item.characterID),
                 '%s (<strong>%s</strong>)' % (self.UserLink(item.oldUserID), item.oldUserCountryCode),
                 '%s (<strong>%s</strong>)' % (self.UserLink(item.newUserID), item.newUserCountryCode),
                 item.ipNumber,
                 self.IPAddress(item.ipNumber),
                 util.FmtDate(item.created, 'll'),
                 util.FmtDate(item.created + transferDelay * const.HOUR)]
                if displayLastPasswordChange or displayLastEmailChange:
                    SQL = '\n                        SELECT count=COUNT(*), columnID\n                          FROM (SELECT TOP 100 eventDate, columnID\n                                  FROM zuser.userEvents\n                                 WHERE userID = %i\n                                 ORDER BY eventID DESC) AS RES\n                        WHERE eventDate > GETUTCDATE() - 7 AND columnID in (205, 206)\n                        GROUP BY columnID'
                    displayLastEmailChangeText = ''
                    displayLastPasswordChangeText = ''
                    for row in self.DB2.SQL(SQL % item.oldUserID):
                        if row.columnID == 205:
                            displayLastEmailChangeText = 'Yes (%i)' % row.count
                        if row.columnID == 206:
                            displayLastPasswordChangeText = 'Yes (%i)' % row.count

                if displayLastEmailChange:
                    line.append(displayLastEmailChangeText)
                if displayLastPasswordChange:
                    line.append(displayLastPasswordChangeText)
                lines.append(line)

            return self.GetTable(header, lines, useFilter=True)

        def VgsAdminAccountLink(self, userID, text):
            try:
                vgsAdminRootUrl = prefs.GetValue('vgsAdminRootUrl')
            except KeyError:
                return self.FontRed('<b>vgsAdminRootUrl</b> not configured in server prefs - VGSAdmin links will be unavailable')

            accountUrl = urlparse.urljoin(vgsAdminRootUrl, '/Accounts2?userId=%d' % userID)
            return '<a href="%s">%s</a>' % (accountUrl, text)

    def GetPickerAgent(self, ctrlID, ctrlLabel = None, minLength = 4):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/agentds.py', minLength=minLength)

    def GetPickerType(self, ctrlID, ctrlLabel = None, minLength = 4):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/typeds.py', minLength=minLength)

    def GetPickerCharacter(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/characterds.py', minLength=minLength)

    def GetPickerOAuthApplication(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/oauthAppds.py', minLength=minLength)

    def GetPickerAffiliate(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/affiliateds.py', minLength=minLength)

    def GetPickerStation(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/stationds.py', minLength=minLength)

    def GetPickerCorporation(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/corporationds.py', minLength=minLength)

    def GetPickerRegion(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/regionds.py', minLength=minLength)

    def GetPickerConstellation(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/constellationds.py', minLength=minLength)

    def GetPickerSolarSystem(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/solarsystemds.py', minLength=minLength)

    def GetPickerPlanet(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/planetds.py', minLength=minLength)

    def GetPickerDistrict(self, ctrlID, ctrlLabel = None, minLength = 3):
        if ctrlLabel is not None:
            ctrlLabel = self.HTMLEncode(ctrlLabel)
        return self.GetAutoComplete(ctrlID, ctrlLabel, callbackPy='/ds/districtds.py', minLength=minLength)

    def AppGetAwayStatusTextForCharacter(self, characterID):
        if not characterID:
            return ''
        try:
            afkStatus = ''
            charMod = characterID % const.CHARNODE_MOD
            charNodeID = sm.GetService('machoNet').GetNodeFromAddress(const.cluster.SERVICE_CHARACTER, charMod)
            afkTime = self.session.ConnectToRemoteService('charMgr', charNodeID).IsCharacterAFK(characterID)
            if afkTime:
                diff = blue.os.GetWallclockTime() - afkTime
                afkStatus = ' &middot; Away for <b>%s</b>, since %s' % (util.FmtTimeEng(diff), util.FmtDateEng(afkTime, 'ns'))
        except Exception as e:
            afkStatus = '<span class=red>Error: %s</span>' % e

        return afkStatus


class AdminHtmlWriter(ESPHtmlWriter):
    pass


class MlsHtmlWriter(ESPHtmlWriter):
    pass


class GMHtmlWriter(ESPHtmlWriter):
    pass


class GDHtmlWriter(ESPHtmlWriter):
    pass


class SessionHtmlWriter(htmlwriter.HtmlWriterEx):
    pass


class PetitionHtmlWriter(ESPHtmlWriter):
    pass


class PetitionClientHtmlWriter(ESPHtmlWriter):
    pass


if macho.mode == 'server':

    class MlsHtmlWriter(ESPHtmlWriter):
        __guid__ = 'htmlwriter.MlsHtmlWriter'

        def __init__(self, template = 'script:/wwwroot/lib/template/baseNoRight.html', page = ''):
            ESPHtmlWriter.__init__(self, template, 'MLS', page)


    class GMHtmlWriter(ESPHtmlWriter):
        __guid__ = 'htmlwriter.GMHtmlWriter'

        def __init__(self, template = 'script:/wwwroot/lib/template/base.html', page = ''):
            ESPHtmlWriter.__init__(self, template, 'GM', page)
            self.EnableExperiments()

        def WriteLeftMenu(self, action):
            pass

        def WriteRightMenu(self):
            pass

        def CategorySelector(self, selectName, selectedCategoryID = None, submitOnChange = False):
            categories = []
            parents, childs, descriptions, billinCategories = self.petitioner.GetCategoryHierarchicalInfo()
            for parentID in parents:
                categories.append([parentID, parents[parentID], True])
                for childID in childs[parentID]:
                    categories.append([childID, childs[parentID][childID], False])

            selectorHTML = '<SELECT NAME="%s"' % selectName
            if submitOnChange:
                selectorHTML += ' ONCHANGE="this.form.submit() '
            selectorHTML += '">' + selectName
            for category in categories:
                categoryID = category[0]
                categoryName = category[1][0]
                categoryIsParent = category[2]
                selectorHTML = selectorHTML + '<OPTION VALUE="%s"' % str(categoryID)
                if categoryID == selectedCategoryID:
                    selectorHTML = selectorHTML + ' SELECTED '
                if categoryIsParent == True:
                    selectorHTML = selectorHTML + '>%s' % unicode(categoryName)
                else:
                    selectorHTML = selectorHTML + '>&nbsp &nbsp %s' % unicode(categoryName)

            return selectorHTML

        def AppCharacterImage(self, coreStatic, appStatic):
            if util.IsDustCharacter(coreStatic.characterID):
                return '/img/dust/portrait%s%s.jpg' % (appStatic.portraitID, ['F', 'M'][coreStatic.gender])
            image = self.GetOwnerImage('Character', coreStatic.characterID)
            if image == None:
                image = '/img/bloodline%d%s.jpg' % (appStatic.bloodlineID, ['F', 'M'][coreStatic.gender])
            return image

        def AppUserCharactersInfo(self, coreStatic, appStatic):
            outputText = (self.FontBoldRed('Offline') if coreStatic.online == 0 else self.FontBoldGreen('Online')) + self.Break()
            if util.IsDustCharacter(coreStatic.characterID):
                return outputText
            rs = self.dbcharacter.Characters_SelectSkills(coreStatic.characterID)
            totalPoints = 0
            for r in rs:
                totalPoints += r.skillPoints

            outputText += self.Link('/gm/character.py', util.FmtAmt(totalPoints) + ' Skill points', {'action': 'CharacterSkills',
             'characterID': coreStatic.characterID}) + self.Break()
            outputText += self.Link('/gm/accounting.py', util.FmtAmtEng(self.account.GetCashBalance_Ex(coreStatic.characterID)) + ' ISK', {'action': 'Journal',
             'ownerID': coreStatic.characterID}) + self.Break()
            outputText += self.CorporationLink(appStatic.corporationID)
            if appStatic.transferPrepareDateTime:
                outputText += self.Break() + self.FontBoldPurple('TRANSFER INITIATED')
            dbzcharacter = self.DB2.GetSchema('zcharacter')
            recentTransfer = dbzcharacter.Character_SelectRecentTransfer(coreStatic.userID, coreStatic.characterID)
            if recentTransfer:
                outputText += self.Break() + self.FontBoldRed('Character recently transferred at: ' + self.Break() + util.FmtDateEng(recentTransfer[0].eventDate))
            return outputText

        def AppUserCharactersLocation(self, coreStatic, appStatic):
            if util.IsDustCharacter(coreStatic.characterID):
                return ''
            return self.CharacterLocationText(coreStatic.characterID, appStatic.locationID, appStatic.locationTypeID, appStatic.locationLocationID, appStatic.activeShipID, appStatic.activeShipTypeID)

        def AppUserCharactersAct(self, coreStatic, appStatic):
            if util.IsDustCharacter(coreStatic.characterID):
                return ''
            act = ''
            if coreStatic.userID == session.userid:
                if session.charid is None:
                    solarSystemID = None
                    if util.IsSolarSystem(appStatic.locationLocationID):
                        solarSystemID = appStatic.locationLocationID
                    elif util.IsStation(appStatic.locationLocationID):
                        solarSystemID = sm.StartService('stationSvc').GetStation(appStatic.locationLocationID).solarSystemID
                    if solarSystemID == 30000380:
                        act += self.Break(2)
                        act += self.Link('/gm/character.py', 'SELECT', {'action': 'SelectCharacter',
                         'characterID': coreStatic.characterID})
                        if session.role & ROLE_PETITIONEE > 0:
                            act += self.Break()
                            act += self.Link('/gm/character.py', 'TICKET', {'action': 'SelectCharacter',
                             'characterID': coreStatic.characterID,
                             'redir': 'p'})
                    else:
                        act += self.Break()
                        act += '<span class="inlinehelp" title="Move|By moving character to polaris you can select the character" class="red">Not in Polaris, can\'t select</span>'
                elif session.charid == coreStatic.characterID:
                    act += self.Break(2)
                    act += self.Link('/gm/character.py', 'LOGOFF', {'action': 'LogOffCharacter'})
            return act

        def CharacterHeader(self, characterID, smallHeader = 1, menuPlacement = 'rMenu'):
            spwriters.SPHtmlWriter.CharacterHeader(self, characterID, smallHeader, menuPlacement)
            coreStatic, appStatic = self.cache.CharacterDataset(characterID)
            li = []
            if coreStatic is None:
                li.append('Character not found.  No header menu possible.')
            elif util.IsDustCharacter(characterID):
                self.PopulateDustHeaderLinks(li, characterID, coreStatic, appStatic)
            else:
                self.PopulateEveHeaderLinks(li, characterID, coreStatic, appStatic)
            self.SubjectActions(li, menuPlacement)

        def PopulateEveHeaderLinks(self, li, characterID, coreStatic, appStatic):
            eveGateProfileUrl = self.cache.Setting('zcluster', 'CommunityWebsite')
            if eveGateProfileUrl:
                if eveGateProfileUrl[-1] != '/':
                    eveGateProfileUrl += '/'
                li.append(self.Link(eveGateProfileUrl + 'GM/Profile/' + coreStatic.characterName, 'Go to Community Profile Page'))
            forumUrl = unicode('https://forums.eveonline.com/default.aspx?g=search&postedby=') + unicode(coreStatic.characterName)
            li.append(self.Link(forumUrl, 'Go to Forum History', {}))
            li.append('-')
            li.append(self.Link('/gm/character.py', 'Destroyed Ships', {'action': 'ShipsKilled',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Kill Rights', {'action': 'KillRights',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Kill Report', {'action': 'KillReport',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/character.py', 'Agents', {'action': 'AgentsForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Spawnpoints', {'action': 'AgentSpawnpoints',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Epic Arc', {'action': 'DisplayEpicMissionArcStatus',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'LP Report', {'action': 'ShowCorpLPForCharacter',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/character.py', 'Move', {'action': 'MoveCharacterForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Last Station', {'action': 'MoveCharacter',
             'characterID': characterID,
             'stationID': 0,
             'moveShipIfApplicable': 'on'}) + self.MidDot() + self.Link('/gm/character.py', 'Last System', {'action': 'MoveCharacter',
             'characterID': characterID,
             'solarSystemID': 0,
             'moveShipIfApplicable': 'on'}))
            li.append('-')
            li.append(self.FontGray('Items', padding=2, inline=True))
            li.append('>' + self.Link('/gm/inventory.py', 'Find Item', {'action': 'FindItem',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/inventory.py', 'Find Traded Items', {'action': 'FindTradedItems',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'System Items', {'action': 'SystemItems',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Station Items', {'action': 'StationItems',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Destroyed Junk', {'action': 'JunkedItems',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Give Loot', {'action': 'CharacterLootFormNew',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Planetary Launches', {'action': 'PlanetaryLaunches',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Deployables', {'action': 'Deployables',
             'ownerID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/logs.py', 'Movement', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupMovement}) + self.MidDot() + self.Link('/gm/logs.py', 'Standing', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupStanding}) + self.MidDot() + self.Link('/gm/logs.py', 'Mission', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupMission}))
            li.append('>' + self.Link('/gm/logs.py', 'Damage', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupDamage}) + self.MidDot() + self.Link('/gm/logs.py', 'Market', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupMarket}) + self.MidDot() + self.Link('/gm/logs.py', 'Dungeon', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupDungeon}))
            li.append('>' + self.Link('/gm/logs.py', 'Killed!', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': -1}) + self.MidDot() + self.Link('/gm/logs.py', 'Mission!', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': -2}) + self.MidDot() + self.Link('/gm/logs.py', 'Bounty!', {'action': 'BountyLog',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/logs.py', 'Crimes', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupCrimes}))
            li.append('>' + self.Link('/gm/logs.py', 'Accessed Others Cargo', {'action': 'CargoAccessLogs',
             'charID': characterID}))
            li.append('>' + self.Link('/gm/logs.py', 'Owned by history', {'action': 'CharacterOwnedBy',
             'charID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/accounting.py', 'Accounting', {'action': 'Statement',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/accounting.py', 'Cash', {'action': 'Journal',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/accounting.py', 'Insurance', {'action': 'Journal',
             'ownerID': characterID,
             'entryTypeID': 19}) + self.MidDot() + self.Link('/gm/owner.py', 'Bills', {'action': 'Bills',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/accounting.py', 'Aurum', {'action': 'Journal',
             'ownerID': characterID,
             'keyID': const.accountingKeyAUR}) + self.MidDot() + self.Link('/gm/character.py', 'Credits', {'action': 'CharacterCreditsForm',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/accounting.py', 'Mass Reversal', {'action': 'MassReversal',
             'ownerID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/character.py', 'Skills', {'action': 'CharacterSkills',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/skilljournal.py', 'Give Skills', {'action': 'CharacterSkillsForm',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/skilljournal.py', 'Set Free Skill Points', {'action': 'SetFreeSkillPointsForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Training Queue', {'action': 'SkillQueue',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/skilljournal.py', 'Skill Journal', {'action': 'CharacterSkillsJournal',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/skilljournal.py', 'LSR Logs', {'action': 'LSRLogs',
             'characterID': characterID,
             'ownerType': 1}) + self.MidDot() + self.Link('/gm/skilljournal.py', 'Connection SR Logs', {'action': 'ConnectionSRLogs',
             'characterID': characterID,
             'ownerType': 1}))
            li.append('-')
            li.append(self.FontGray('Market', padding=2, inline=True))
            li.append('>' + self.Link('/gm/owner.py', 'Orders', {'action': 'Orders',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Transactions', {'action': 'Transactions',
             'ownerID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/contracts.py', 'Contracts', {'action': 'ListForEntity',
             'submit': 1,
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/contracts.py', 'Issued By', {'action': 'List',
             'submit': 1,
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/contracts.py', 'Issued To', {'action': 'List',
             'submit': 1,
             'acceptedByID': characterID,
             'filtStatus': const.conStatusInProgress}))
            li.append('>' + self.Link('/gm/contracts.py', 'Assigned To', {'action': 'List',
             'submit': 1,
             'assignedToID': characterID}))
            li.append('-')
            li.append(self.FontGray('Character', padding=2, inline=True))
            li.append('>' + self.Link('/gm/clones.py', 'Clones', {'action': 'Clones',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Insurance', {'action': 'Insurance',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Contacts', {'action': 'Contacts',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Standings', {'action': 'Standings',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Bookmarks', {'action': 'Bookmarks',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/faction.py', 'Militia Stats', {'action': 'FactionalWarfareStatisticsForEntity',
             'entityID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Ranks And Medals', {'action': 'RanksAndMedals',
             'characterID': characterID}))
            now = time.gmtime()
            li.append('>' + self.Link('/gm/calendar.py', 'Calendar', {'action': 'FindByOwner',
             'ownerID': characterID,
             'ownerType': const.groupCharacter,
             'fromMonth': 1,
             'fromYear': const.calendarStartYear,
             'toMonth': 1,
             'toYear': now[0] + 1}) + self.MidDot() + self.Link('/gm/character.py', 'Goodies and Respeccing', {'action': 'EditGoodiesAndRespeccing',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Jump Timers', {'action': 'JumpTimers',
             'characterID': characterID}))
            li.append('-')
            li.append(self.FontGray('Corporate', padding=2, inline=True))
            li.append('>' + self.Link('/gm/logs.py', 'Audit Log', {'action': 'AuditLog',
             'logGroup': const.groupCharacter,
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Member Details', {'action': 'CorpMemberDetailsByCharID',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Employment Records', {'action': 'EmploymentRecords',
             'characterID': characterID}))
            li.append('-')
            li.append(self.FontGray('Administrative', padding=2, inline=True))
            li.append('>' + self.Link('/gm/petition.py', 'Ticket', {'action': 'BriefPetitionHistory',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Create Ticket', {'action': 'CreatePetitionForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Punishments', {'action': 'PunishCharacterForm',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/users.py', 'Ban User', {'action': 'BanUserByCharacterID',
             'characterID': characterID}))
            li.append('-')
            li.append(self.FontGray('Messages', padding=2, inline=True))
            li.append('>' + self.Link('/gm/owner.py', 'Received', {'action': 'Messages',
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Sent', {'action': 'SentMessages',
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Mailing Lists', {'action': 'MailingLists',
             'charID': characterID}))
            li.append('-')
            li.append(self.FontGray('Notifications', padding=2, inline=True))
            li.append('>' + self.Link('/gm/owner.py', 'Agents', {'action': 'Notifications',
             'groupID': 1,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Bills', {'action': 'Notifications',
             'groupID': 2,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Contacts', {'action': 'Notifications',
             'groupID': 9,
             'charID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Sovereignty', {'action': 'Notifications',
             'groupID': 6,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Structures', {'action': 'Notifications',
             'groupID': 7,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'War', {'action': 'Notifications',
             'groupID': 8,
             'charID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Corporate', {'action': 'Notifications',
             'groupID': 3,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Miscellaneous', {'action': 'Notifications',
             'groupID': 4,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Old', {'action': 'Notifications',
             'groupID': 5,
             'charID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Bounty', {'action': 'Notifications',
             'groupID': 10,
             'charID': characterID}))
            li.append('-')
            li.append(self.FontGray('Industry', padding=2, inline=True))
            li.append('>' + self.Link('/gm/industry.py', 'Facilities', {'action': 'Facilities',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/industry.py', 'Blueprints', {'action': 'Blueprints',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/industry.py', 'Jobs', {'action': 'Jobs',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/ram.py', 'Give Blueprint', {'action': 'GiveBlueprint',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/planets.py', 'Planets', {'action': 'PlanetsByOwner',
             'ownerID': characterID}))
            if session.role & ROLE_CONTENT > 0:
                li.append('-')
                li.append(self.Link('/gm/achievements.py', 'Opportunities', {'action': 'Achievements',
                 'characterID': characterID}))
            li.append('-')
            li.append(self.FontGray('Paper doll', padding=2, inline=True))
            s = self.Link('/gm/character.py', 'Flags', {'action': 'PaperdollFlags',
             'characterID': characterID})
            if session.role & ROLE_CONTENT > 0:
                s += self.MidDot() + self.Link('/gm/character.py', 'Copy Paperdoll', {'action': 'PaperdollCharacterCopy',
                 'characterID': characterID})
            li.append('>' + s)
            li.append('-')
            li.append(self.Link('/gm/owner.py', 'Bounty', {'action': 'ViewBountyPool',
             'entityID': characterID}))

        def PopulateDustHeaderLinks(self, li, characterID, coreStatic, appStatic):
            forumUrl = unicode('https://forums.dust514.com/default.aspx?g=search&postedby=') + unicode(coreStatic.characterName)
            li.append(self.Link(forumUrl, 'Go to Forum History', {}))
            li.append('-')
            li.append(self.Link('/dust/character.py', 'Battle', {'action': 'Battle',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'History', {'action': 'Battles',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/character.py', 'Move', {'action': 'MoveCharacterForm',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/dust/character.py', 'Items', {'action': 'Items',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/inventory.py', 'Find Item', {'action': 'FindItem',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Give Loot', {'action': 'CharacterLootFormNew',
             'characterID': characterID}) + self.MidDot() + self.Link('/dust/character.py', 'Grant All Items', {'action': 'SuperItemsForm',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/accounting.py', 'Accounting', {'action': 'Statement',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/accounting.py', 'Cash', {'action': 'Journal',
             'ownerID': characterID,
             'keyID': const.ACCOUNTING_DUST_ISK}) + self.MidDot() + self.Link('/gm/character.py', 'Credits', {'action': 'CharacterCreditsForm',
             'characterID': characterID}))
            li.append('-')
            li.append(self.Link('/dust/character.py', 'Skills', {'action': 'Skills',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Modify Skill Points', {'action': 'AddSkillPointsForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Grant All Skills', {'action': 'GrantAllSkillsForm',
             'characterID': characterID}) + self.MidDot() + self.Link('/dust/character.py', 'Add Skill', {'action': 'AddSkillForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Refresh Cache', {'action': 'SkillsRefreshCache',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupDustSkill}))
            li.append('-')
            li.append(self.FontGray('Market', padding=2, inline=True))
            li.append('>' + self.Link('/gm/owner.py', 'Orders', {'action': 'Orders',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Transactions', {'action': 'Transactions',
             'ownerID': characterID}))
            li.append('-')
            li.append(self.Link('/dust/character.py', 'Boosters', {'action': 'Boosters',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Passive', {'action': 'PassiveSkillGainBoosters',
             'characterID': characterID}) + self.MidDot() + self.Link('/dust/character.py', 'Active', {'action': 'ActiveSkillGainBoosters',
             'characterID': characterID}) + self.MidDot() + self.Link('/dust/character.py', 'Faction', {'action': 'FactionBoosters',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Refresh Cache', {'action': 'BoostersRefreshCache',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': logConst.groupDustBoosters}))
            li.append('-')
            li.append(self.FontGray('Character', padding=2, inline=True))
            li.append('>' + self.Link('/dust/character.py', 'Lifetime Stats', {'action': 'LifetimeStats',
             'characterID': characterID}) + self.MidDot() + self.Link('/dust/character.py', 'Fitting', {'action': 'Fittings',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Contacts', {'action': 'Contacts',
             'ownerID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Standings', {'action': 'Standings',
             'ownerID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Bookmarks', {'action': 'Bookmarks',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/faction.py', 'Militia Stats', {'action': 'FactionalWarfareStatisticsForEntity',
             'entityID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Ranks And Medals', {'action': 'RanksAndMedals',
             'characterID': characterID}))
            now = time.gmtime()
            li.append('>' + self.Link('/gm/calendar.py', 'Calendar', {'action': 'FindByOwner',
             'ownerID': characterID,
             'ownerType': const.groupCharacter,
             'fromMonth': 1,
             'fromYear': const.calendarStartYear,
             'toMonth': 1,
             'toYear': now[0] + 1}) + self.MidDot() + self.Link('/gm/character.py', 'Goodies and Respeccing', {'action': 'EditGoodiesAndRespeccing',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Daily Quests', {'action': 'DailyQuests',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/logs.py', 'Daily Quest Events', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': groupDailyQuest}))
            li.append('>' + self.Link('/dust/character.py', 'Personal Warbarges', {'action': 'PersonalWarbarges',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/logs.py', 'Personal Warbarge Events', {'action': 'OwnerEvents',
             'ownerID': characterID,
             'eventGroupID': groupDustWarbarge}))
            li.append('-')
            li.append(self.FontGray('Corporate', padding=2, inline=True))
            li.append('>' + self.Link('/gm/logs.py', 'Audit Log', {'action': 'AuditLog',
             'logGroup': const.groupCharacter,
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Member Details', {'action': 'CorpMemberDetailsByCharID',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Employment Records', {'action': 'EmploymentRecords',
             'characterID': characterID}))
            li.append('-')
            li.append(self.FontGray('Administrative', padding=2, inline=True))
            li.append('>' + self.Link('/gm/petition.py', 'Ticket', {'action': 'BriefPetitionHistory',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/character.py', 'Create Ticket', {'action': 'CreatePetitionForm',
             'characterID': characterID}))
            li.append('>' + self.Link('/gm/character.py', 'Punishments', {'action': 'PunishCharacterForm',
             'characterID': characterID}) + self.MidDot() + self.Link('/gm/users.py', 'Ban User', {'action': 'BanUserByCharacterID',
             'characterID': characterID}))
            li.append('>' + self.Link('/dust/character.py', 'Copy Character', {'action': 'CopyCharacterForm',
             'characterID': characterID}))
            li.append('-')
            li.append(self.FontGray('Messages', padding=2, inline=True))
            li.append('>' + self.Link('/gm/owner.py', 'Received', {'action': 'Messages',
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Sent', {'action': 'SentMessages',
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Mailing Lists', {'action': 'MailingLists',
             'charID': characterID}))
            li.append('-')
            li.append(self.FontGray('Notifications', padding=2, inline=True))
            li.append('>' + self.Link('/gm/owner.py', 'Agents', {'action': 'Notifications',
             'groupID': 1,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Bills', {'action': 'Notifications',
             'groupID': 2,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Contacts', {'action': 'Notifications',
             'groupID': 9,
             'charID': characterID}))
            li.append('>' + self.Link('/gm/owner.py', 'Sovereignty', {'action': 'Notifications',
             'groupID': 6,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'Structures', {'action': 'Notifications',
             'groupID': 7,
             'charID': characterID}) + self.MidDot() + self.Link('/gm/owner.py', 'War', {'action': 'Notifications',
             'groupID': 8,
             'charID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/planets.py', 'Planets', {'action': 'PlanetsByOwner',
             'ownerID': characterID}))
            li.append('-')
            li.append(self.Link('/gm/owner.py', 'Bounty', {'action': 'ViewBountyPool',
             'entityID': characterID}))
            li.append('-')
            li.append(self.Link('/dust/character.py', 'Quests', {'action': 'Quests',
             'characterID': characterID}))

        def CorporationHeader(self, corporationID, smallHeader = 1, menuPlacement = 'rMenu'):
            c = self.cache.EspCorporation(corporationID)
            stationSvc = sm.GetService('stationSvc')
            station = stationSvc.GetStation(c.stationID)
            image = self.GetOwnerImage('Corporation', corporationID)
            if image == None:
                image = '/img/corporation'
                if corporationID < const.minPlayerOwner:
                    image += str(corporationID)
                image += '.jpg'
            lines = []
            if corporationID < const.minPlayerOwner:
                nc = self.cache.Index(const.cacheCrpNpcCorporations, corporationID)
                lines.append([1, 'Faction', self.FactionLink(nc.factionID)])
            else:
                allianceRegistry = session.ConnectToService('allianceRegistry')
                allianceID = allianceRegistry.AllianceIDFromCorpID(corporationID)
                allianceName = ''
                if allianceID is not None:
                    allianceName = self.AllianceLink(allianceID)
                lines.append([1, 'Alliance', allianceName])
            lines.append([1, 'Station', self.StationLink(c.stationID)])
            if station is not None:
                lines.append([0, 'System', self.SystemLink(station.solarSystemID)])
            else:
                lines.append([0, 'System', ''])
            self.SubjectHeader(smallHeader, 'CORPORATION', corporationID, self.OwnerName(corporationID), '#FFE0C0', image, '/gm/corporation.py', 'Corporation', 'corporationID', lines)
            li = []
            li.append('#CORPORATION')
            li.append(self.Link('/gm/corporation.py', 'INFO', {'action': 'Corporation',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.Link('/gm/corporation.py', 'Members', {'action': 'SimplyViewMembers',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/corporation.py', 'Complex Members', {'action': 'ViewMembers',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/logs.py', 'Audit Log', {'action': 'AuditLog',
             'logGroup': const.groupCorporation,
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Roles', {'action': 'Roles',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Titles', {'action': 'Titles',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/corporation.py', 'Pending Auto-kicks', {'action': 'PendingAutoKicks',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Items'))
            li.append('>' + self.Link('/gm/inventory.py', 'Find Item', {'action': 'FindItem',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/owner.py', 'System Items', {'action': 'SystemItems',
             'ownerID': corporationID}))
            li.append('>' + self.Link('/gm/owner.py', 'Station Items', {'action': 'StationItems',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/owner.py', 'Office Items', {'action': 'OfficeItems',
             'ownerID': corporationID}))
            li.append('>' + self.Link('/gm/corporation.py', 'Find Item Members', {'action': 'FindItemsOnMembers',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Locked Items', {'action': 'LockedItems',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/corporation.py', 'Stations', {'action': 'Stations',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Starbases', {'action': 'Starbases',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/owner.py', 'Offices', {'action': 'RentableItems',
             'ownerID': corporationID,
             'typeID': 26}))
            li.append('-')
            li.append(self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': corporationID}))
            li.append('>' + self.Link('/gm/logs.py', 'Accessed Others Cargo', {'action': 'CargoAccessLogs',
             'charID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Kill Report', {'action': 'KillReport',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.Link('/gm/accounting.py', 'Accounting', {'action': 'Statement',
             'ownerID': corporationID}))
            li.append('>' + self.Link('/gm/accounting.py', 'Cash', {'action': 'Journal',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/accounting.py', 'Insurance', {'action': 'Journal',
             'ownerID': corporationID,
             'entryTypeID': 19}) + self.MidDot() + self.Link('/gm/owner.py', 'Bills', {'action': 'Bills',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Credits', {'action': 'CorporationCreditsForm',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/accounting.py', 'Mass Reversal', {'action': 'MassReversal',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/accounting.py', 'Aurum', {'action': 'Journal',
             'ownerID': corporationID,
             'keyID': const.accountingKeyAUR}))
            li.append('>' + self.Link('/gm/corporation.py', 'Shareholders', {'action': 'ViewShareholders',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Shares', {'action': 'CreateCorporationSharesForm',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Industry'))
            li.append('>' + self.Link('/gm/industry.py', 'Facilities', {'action': 'Facilities',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/industry.py', 'Blueprints', {'action': 'Blueprints',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/industry.py', 'Jobs', {'action': 'Jobs',
             'ownerID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Market'))
            li.append('>' + self.Link('/gm/owner.py', 'Orders', {'action': 'Orders',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/owner.py', 'Transactions', {'action': 'Transactions',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Trades', {'action': 'Trades',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.Link('/gm/contracts.py', 'Contracts', {'action': 'ListForEntity',
             'submit': 1,
             'ownerID': corporationID}))
            li.append('>' + self.Link('/gm/contracts.py', 'Issued By', {'action': 'List',
             'submit': 1,
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/contracts.py', 'Issued To', {'action': 'List',
             'submit': 1,
             'acceptedByID': corporationID,
             'filtStatus': const.conStatusInProgress}))
            li.append('>' + self.Link('/gm/contracts.py', 'Assigned To', {'action': 'List',
             'submit': 1,
             'assignedToID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Corporation'))
            li.append('>' + self.Link('/gm/corporation.py', 'Bulletins', {'action': 'Bulletins',
             'ownerID': corporationID}) + self.MidDot() + self.Link('/gm/owner.py', 'Contacts', {'action': 'Contacts',
             'ownerID': corporationID}))
            li.append('>' + self.Link('/gm/faction.py', 'Militia Stats', {'action': 'FactionalWarfareStatisticsForEntity',
             'entityID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Medals', {'action': 'Medals',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/corporation.py', 'Alliance Records', {'action': 'AllianceRecords',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/owner.py', 'Standings', {'action': 'Standings',
             'ownerID': corporationID}))
            s = self.Link('/gm/corporation.py', 'Corporate Registry Ads', {'action': 'CorporateRegistry',
             'corporationID': corporationID})
            if not util.IsNPC(corporationID):
                now = time.gmtime()
                s += self.MidDot() + self.Link('/gm/calendar.py', 'Calendar', {'action': 'FindByOwner',
                 'ownerID': corporationID,
                 'ownerType': const.groupCorporation,
                 'fromMonth': 1,
                 'fromYear': const.calendarStartYear,
                 'toMonth': 1,
                 'toYear': now[0] + 1})
            li.append('>' + s)
            if not util.IsNPC(corporationID):
                li.append('>' + self.Link('/gm/corporation.py', 'Applications', {'action': 'CorpApplications',
                 'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Welcome Mail', {'action': 'CorpWelcomeMail',
                 'corporationID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Votes and Sanctioned Actions'))
            li.append('>' + self.Link('/gm/corporation.py', 'Open Votes', {'action': 'ViewVotes',
             'corporationID': corporationID,
             'isOpen': 1}) + self.MidDot() + self.Link('/gm/corporation.py', 'Closed Votes', {'action': 'ViewVotes',
             'corporationID': corporationID,
             'isOpen': 0}))
            li.append('>' + self.Link('/gm/corporation.py', 'Votes in Effect', {'action': 'ViewSanctionableActions',
             'corporationID': corporationID,
             'inEffect': 1}) + self.MidDot() + self.Link('/gm/corporation.py', 'Votes not in Effect', {'action': 'ViewSanctionableActions',
             'corporationID': corporationID,
             'inEffect': 0}))
            li.append('-')
            li.append(self.FontGray('Wars'))
            li.append('>' + self.Link('/gm/war.py', 'Active', {'action': 'ViewWars',
             'ownerID': corporationID,
             'onlyActive': 1}) + self.MidDot() + self.Link('/gm/war.py', 'All', {'action': 'ViewWars',
             'ownerID': corporationID,
             'onlyActive': 0}) + self.MidDot() + self.Link('/gm/corporation.py', 'Faction', {'action': 'ViewFactionWarsForCorp',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Administrative'))
            li.append('>' + self.Link('/gm/corporation.py', 'Gag Corp', {'action': 'GagCorporationForm',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Ungag Corp', {'action': 'UnGagCorporation',
             'corporationID': corporationID}))
            li.append('>' + self.Link('/gm/petition.py', 'Tickets', {'action': 'CorpPetitions',
             'corpID': corporationID}))
            li.append('>' + self.Link('/gm/corporation.py', 'Corporation Notes', {'action': 'Notes',
             'corporationID': corporationID}) + self.MidDot() + self.Link('/gm/corporation.py', 'Member Notes', {'action': 'NotesForCorp',
             'corporationID': corporationID}))
            li.append('-')
            li.append(self.FontGray('Skills'))
            li.append('>' + self.Link('/gm/skilljournal.py', 'LSR Logs', {'action': 'LSRLogs',
             'characterID': corporationID,
             'ownerType': 2}) + self.MidDot() + self.Link('/gm/skilljournal.py', 'Connection SR Logs', {'action': 'ConnectionSRLogs',
             'characterID': corporationID,
             'ownerType': 2}))
            li.append('-')
            li.append(self.Link('/gm/owner.py', 'Bounty', {'action': 'ViewBountyPool',
             'entityID': corporationID}))
            self.SubjectActions(li, menuPlacement)
            return c

        def AllianceHeader(self, allianceID, smallHeader = 1, menuPlacement = 'rMenu'):
            a = self.cache.EspAlliance(allianceID)
            image = self.GetOwnerImage('Alliance', allianceID)
            if image == None:
                image = '/img/alliance.jpg'
            lines = []
            info = ''
            info = self.SplitAdd(info, util.FmtDateEng(a.startDate, 'ln'), ', ')
            lines.append([0, 'Info', info])
            if a.url:
                lines.append([0, 'web', a.url])
            self.SubjectHeader(smallHeader, 'ALLIANCE', allianceID, self.OwnerName(allianceID), '#D7AFAF', image, '/gm/alliance.py', 'Alliance', 'allianceID', lines)
            li = []
            li.append('#ALLIANCE')
            li.append(self.Link('/gm/alliance.py', 'INFO', {'action': 'Alliance',
             'allianceID': allianceID}))
            li.append('-')
            li.append(self.Link('/gm/accounting.py', 'Accounting', {'action': 'Statement',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/alliance.py', 'Applications', {'action': 'ViewApplications',
             'allianceID': allianceID}))
            now = time.gmtime()
            li.append(self.Link('/gm/calendar.py', 'Calendar', {'action': 'FindByOwner',
             'ownerID': allianceID,
             'ownerType': const.groupAlliance,
             'fromMonth': 1,
             'fromYear': const.calendarStartYear,
             'toMonth': 1,
             'toYear': now[0] + 1}))
            li.append(self.Link('/gm/owner.py', 'Bills', {'action': 'Bills',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/alliance.py', 'Bills (Payable by GMH)', {'action': 'ViewBills',
             'allianceID': allianceID}))
            li.append(self.Link('/gm/corporation.py', 'Bulletins', {'action': 'Bulletins',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/owner.py', 'Contacts', {'action': 'Contacts',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/inventory.py', 'Find Item', {'action': 'FindItem',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/alliance.py', 'Members', {'action': 'ViewMembers',
             'allianceID': allianceID}))
            li.append(self.Link('/gm/alliance.py', 'Notes', {'action': 'Notes',
             'allianceID': allianceID}))
            li.append(self.Link('/gm/owner.py', 'Standings', {'action': 'Standings',
             'ownerID': allianceID}))
            li.append(self.Link('/gm/alliance.py', 'Sovereignty Bill', {'action': 'Sovereignty',
             'allianceID': allianceID}))
            li.append(self.Link('/gm/war.py', 'Wars (Active)', {'action': 'ViewWars',
             'ownerID': allianceID,
             'onlyActive': 1}))
            li.append(self.Link('/gm/war.py', 'Wars (All)', {'action': 'ViewWars',
             'ownerID': allianceID,
             'onlyActive': 0}))
            li.append('-')
            li.append(self.Link('/gm/owner.py', 'Bounty', {'action': 'ViewBountyPool',
             'entityID': allianceID}))
            self.SubjectActions(li, menuPlacement)
            return a

        def FactionHeader(self, factionID, smallHeader = 1, menuPlacement = 'rMenu'):
            f = cfg.factions.Get(factionID)
            image = '/img/faction%s.jpg' % factionID
            self.SubjectHeader(smallHeader, 'FACTION', factionID, f.factionName, '#E8E8FF', image, '/gm/faction.py', 'Faction', 'factionID', [[1, 'System', self.SystemLink(f.solarSystemID)], [1, 'Corporation', self.CorporationLink(f.corporationID)]])
            li = []
            li.append('#FACTION')
            li.append(self.Link('/gm/faction.py', 'INFO', {'action': 'Faction',
             'factionID': factionID}))
            li.append('-')
            li.append(self.Link('/gm/faction.py', 'Corporations', {'action': 'Corporations',
             'factionID': factionID}))
            li.append(self.Link('/gm/faction.py', 'Factional Warfare Corporations', {'action': 'FactionalWarfareCorporations',
             'factionID': factionID}))
            li.append(self.Link('/gm/faction.py', 'Militia Stats', {'action': 'FactionalWarfareStatisticsForEntity',
             'entityID': factionID}))
            li.append(self.Link('/gm/faction.py', 'Distributions', {'action': 'Distributions',
             'factionID': factionID}))
            li.append(self.Link('/gm/faction.py', 'Territory', {'action': 'Territory',
             'factionID': factionID}))
            li.append(self.Link('/gm/logs.py', 'Events', {'action': 'OwnerEvents',
             'ownerID': factionID}))
            li.append(self.Link('/gm/owner.py', 'Standings', {'action': 'Standings',
             'ownerID': factionID}))
            self.SubjectActions(li, menuPlacement)
            return f

        def OwnerHeader(self, ownerID, smallHeader = 1, menuPlacement = 'rMenu'):
            if util.IsFaction(ownerID):
                self.FactionHeader(ownerID, smallHeader, menuPlacement)
            elif util.IsAlliance(ownerID):
                self.AllianceHeader(ownerID, smallHeader, menuPlacement)
            elif util.IsCorporation(ownerID):
                self.CorporationHeader(ownerID, smallHeader, menuPlacement)
            elif util.IsCharacter(ownerID):
                self.CharacterHeader(ownerID, smallHeader, menuPlacement)
            else:
                self.WriteError('Owner header requested for an ID that is not an owner, if this happens frequently contact development')

        def CharacterLocationText(self, characterID, locationID, locationTypeID, locationLocationID, activeShipID = None, activeShipTypeID = None):
            solarSystemID = None
            if util.IsSolarSystem(locationLocationID):
                solarSystemID = locationLocationID
            elif util.IsStation(locationLocationID):
                solarSystemID = sm.StartService('stationSvc').GetStation(locationLocationID).solarSystemID
            s = ''
            try:
                shipID = None
                if not util.IsSystemOrNPC(locationID):
                    shipID = locationID
                    locationID = locationLocationID
                if util.IsWorldSpace(locationID):
                    s += self.FontHeaderProperty('WorldSpace')
                    s += ':<br>%s' % self.WorldSpaceLink(locationID)
                elif util.IsSolarSystem(locationID):
                    s += self.FontHeaderProperty('SYSTEM')
                    s += ':<br>%s' % self.SystemLink(locationID)
                else:
                    s += self.FontHeaderProperty('STATION')
                    s += ':<br>%s' % self.StationLink(locationID)
                    s += ' - %s' % self.SystemLink(solarSystemID)
                if shipID:
                    s += '<br>' + self.FontHeaderProperty('SHIP') + ':<br>%s' % self.Link('/gm/character.py', cfg.evelocations.Get(shipID).locationName, {'action': 'Ship',
                     'characterID': characterID,
                     'shipID': shipID})
                    s += '<br>' + self.FontProperty('Type') + ': %s' % cfg.invtypes.Get(locationTypeID).typeName
                elif activeShipID:
                    s += '<br>' + self.FontHeaderProperty('SHIP') + ':<br>%s' % self.Link('/gm/character.py', cfg.evelocations.Get(activeShipID).locationName, {'action': 'Ship',
                     'characterID': characterID,
                     'shipID': activeShipID})
                    s += '<br>' + self.FontProperty('Type') + ': %s' % cfg.invtypes.Get(activeShipTypeID).typeName
            except:
                s = self.FontRed('Invalid Location: %s' % locationID)

            return s

        def FormatDateTime(self, dt):
            if dt is None:
                return ''
            dtNow = blue.win32.GetSystemTimeAsFileTime()
            diff = dtNow - dt
            numMinutes = diff / 10000000.0 / 60
            numDays = numMinutes / 60 / 24
            dTimeFmt = util.FmtDateEng(dt, 'ns')
            dst = util.FmtDateEng(dt, 'sn')
            lst = dst.split('.')
            dDateFmt = lst[2] + '. ' + ['Jan',
             'Feb',
             'Mar',
             'Apr',
             'May',
             'Jun',
             'Jul',
             'Aug',
             'Sep',
             'Oct',
             'Nov',
             'Dec'][int(lst[1]) - 1] + ' ' + lst[0]
            dn = util.FmtDateEng(dtNow, 'ns')
            if numDays < 1 and dTimeFmt.split(':')[0] <= dn.split(':')[0]:
                return '<strong>Today at %s</strong>' % dTimeFmt
            elif numDays < 2:
                return 'Yesterday at %s' % dTimeFmt
            else:
                return dDateFmt + ' ' + dTimeFmt

        def BloodlineGenderImage(self, bloodlineID, gender):
            image = '/img/bloodline%d' % bloodlineID
            if gender == 0:
                image += 'F'
            else:
                image += 'M'
            return self.Image(image + '.jpg')

        def BloodlineDetailCombo(self, detail, colID, colName, bloodlineID, gender):
            s = 'SELECT D.' + colID + ', M.' + colName + ' FROM chrBloodline' + detail + ' D INNER JOIN chr' + detail + ' M ON M.' + colID + ' = D.' + colID
            s += ' WHERE D.bloodlineID = %d AND D.gender = %d' % (bloodlineID, gender)
            rs = self.DB2.SQL(s)
            d = {}
            if len(rs) > 0:
                d[None] = '(random)'
                for r in rs:
                    d[r[colID]] = r[colName]

            return d

        def CatmaEntryLink(self, entryID, linkText = None, props = ''):
            if entryID is None:
                return ''
            if linkText is None:
                from catma import catmaDBUtil
                linkText = catmaDBUtil.GetDisplayNameByID(entryID)
                if linkText == '':
                    from catma import catmaDB
                    obj = catmaDB.GetTypeByID(entryID)
                    linkText = obj.GetTypeName()
            return self.Link('/catma/catmaMK2.py', linkText, {'action': 'Entry',
             'entryID': entryID}, props)

        def BattleStatus(self, status):
            if status in const.battleStatuses:
                statusText = const.battleStatuses[status]
                if status == const.battleStatusRunning:
                    statusText = self.FontBoldGreen(statusText)
                return statusText
            else:
                return self.FontRed('???')

        def EventReference(self, row):
            """
            General function returning readable info/links for events using columns referenceTable/Column in table zevent.types.
            For frequent cases a developer adding event types only needs to set the columns correctly meaning no code change is needed.
            This function is used by the OwnerEventReference and ItemEventReference functions.
            """
            eventTypeID = row.eventTypeID
            referenceID = row.referenceID
            if referenceID is None:
                return
            et = self.cache.Index(const.cacheEventTypes, eventTypeID)
            referenceColumn = et.referenceColumn
            if referenceColumn:
                if referenceColumn == 'characterID':
                    return [self.ItemID(referenceID), 'Character', self.CharacterLink(referenceID)]
                if referenceColumn == 'corporationID':
                    return [self.ItemID(referenceID), 'Corporation', self.CorporationLink(referenceID)]
                if referenceColumn == 'allianceID':
                    return [self.ItemID(referenceID), 'Alliance', self.AllianceLink(referenceID)]
                if referenceColumn == 'factionID':
                    return [self.ItemID(referenceID), 'Faction', self.FactionLink(referenceID)]
                if referenceColumn == 'regionID':
                    return [self.ItemID(referenceID), 'Region', self.RegionLink(referenceID)]
                if referenceColumn == 'constellationID':
                    return [self.ItemID(referenceID), 'Constellation', self.ConstellationLink(referenceID)]
                if referenceColumn == 'solarSystemID':
                    return [self.ItemID(referenceID), 'System', self.SystemLink(referenceID)]
                if referenceColumn == 'planetID':
                    return [self.ItemID(referenceID), 'Planet', self.PlanetLink(referenceID)]
                if referenceColumn == 'stationID':
                    return [self.ItemID(referenceID), 'Station', self.StationLink(referenceID)]
                if referenceColumn == 'ownerID':
                    if util.IsFaction(referenceID):
                        return [self.ItemID(referenceID), 'Faction', self.FactionLink(referenceID)]
                    if util.IsNPCCorporation(referenceID):
                        return [self.ItemID(referenceID), 'NPC Corporation', self.CorporationLink(referenceID)]
                    if util.IsNPCCharacter(referenceID):
                        return [self.ItemID(referenceID), 'NPC Character', self.CharacterLink(referenceID)]
                    if util.IsCharacter(referenceID):
                        return [self.ItemID(referenceID), 'Character', self.CharacterLink(referenceID)]
                    if util.IsCorporation(referenceID):
                        return [self.ItemID(referenceID), 'Corporation', self.CorporationLink(referenceID)]
                    if util.IsAlliance(referenceID):
                        return [self.ItemID(referenceID), 'Alliance', self.AllianceLink(referenceID)]
                    return [self.ItemID(referenceID), 'Owner', '']
                if referenceColumn == 'itemID':
                    if util.IsFaction(referenceID):
                        return [self.ItemID(referenceID), 'Faction', self.FactionLink(referenceID)]
                    if util.IsNPCCorporation(referenceID):
                        return [self.ItemID(referenceID), 'NPC Corporation', self.CorporationLink(referenceID)]
                    if util.IsNPCCharacter(referenceID):
                        return [self.ItemID(referenceID), 'NPC Character', self.CharacterLink(referenceID)]
                    if util.IsRegion(referenceID):
                        return [self.ItemID(referenceID), 'Region', self.RegionLink(referenceID)]
                    if util.IsConstellation(referenceID):
                        return [self.ItemID(referenceID), 'Constellation', self.ConstellationLink(referenceID)]
                    if util.IsSolarSystem(referenceID):
                        return [self.ItemID(referenceID), 'System', self.SystemLink(referenceID)]
                    if util.IsStation(referenceID):
                        return [self.ItemID(referenceID), 'Station', self.StationLink(referenceID)]
                    if util.IsCharacter(referenceID):
                        return [self.ItemID(referenceID), 'Character', self.CharacterLink(referenceID)]
                    if util.IsCorporation(referenceID):
                        return [self.ItemID(referenceID), 'Corporation', self.CorporationLink(referenceID)]
                    if util.IsAlliance(referenceID):
                        return [self.ItemID(referenceID), 'Alliance', self.AllianceLink(referenceID)]
                    if 'typeID' in row.__columns__ and row.typeID:
                        return [self.ItemID(referenceID), cfg.invtypes.Get(row.typeID).Category().categoryName, self.TypeLink(row.typeID)]
                    return [self.ItemID(referenceID), 'Item', '']
                if referenceColumn == 'typeID':
                    return [referenceID, 'Type', self.TypeLink(referenceID)]
                if referenceColumn == 'tokenID':
                    return [self.Link('/gm/users.py', referenceID, {'action': 'LookupRedeemToken',
                      'tokenID': referenceID}), '', '']

        def OwnerEventReference(self, row):
            """
            Function returning readable info/links for owner events.
            Calling general function EventReference, if not handled there then check for special cases.
            """
            ref = self.EventReference(row)
            if ref is not None:
                return ref
            eventTypeID = row.eventTypeID
            referenceID = row.referenceID
            if referenceID is None:
                return ['', '', '']
            et = self.cache.Index(const.cacheEventTypes, eventTypeID)
            eventGroupID = et.eventGroupID
            referenceColumn = et.referenceColumn
            if referenceColumn:
                if referenceColumn in ('dungeonID', 'instanceID'):
                    if referenceColumn == 'dungeonID':
                        dungeonID = referenceID
                    elif 'dungeonID' in row.__columns__:
                        dungeonID = row.dungeonID
                    else:
                        dungeonID = None
                    if dungeonID in self.cache.Index(const.cacheDungeonDungeons):
                        dungeonName = self.Link('/gd/dungeons.py', localization.GetByMessageID(self.cache.Index(const.cacheDungeonDungeons, dungeonID).dungeonNameID), {'action': 'Dungeon',
                         'dungeonID': dungeonID})
                    else:
                        dungeonName = self.FontRed('Dungeon not found')
                    return [referenceID, 'Dungeon Instance', dungeonName]
                if referenceColumn == 'missionCountID':
                    if 'missionID' in row.__columns__:
                        missionName = self.MissionLink(row.missionID)
                    else:
                        missionName = self.FontRed('Mission not found')
                    return [referenceID, 'Mission Instance', missionName]
                if referenceColumn == 'tutorialID':
                    tutorialIx = sm.GetService('tutorialSvc').GetTutorialsIx()
                    if referenceID in tutorialIx:
                        tutorialName = localization.GetByMessageID(tutorialIx[referenceID].tutorialNameID)
                        return [referenceID, 'Tutorial', self.Link('/gd/tutorials.py', tutorialName, {'action': 'Tutorial',
                          'tutorialID': referenceID})]
                    else:
                        return [referenceID, 'Tutorial', self.FontRed('Tutorial not found')]
                if referenceColumn == 'planetID':
                    return [self.ItemID(referenceID), 'Planet', self.PlanetLink(referenceID)]
                if referenceColumn == 'launchID':
                    return [self.Link('/gm/owner.py', referenceID, {'action': 'PlanetaryLaunch',
                      'launchID': referenceID}), 'Planetary Launch', '']
                if referenceColumn == 'offerID':
                    if eventTypeID in (logConst.eventStoreGaveCredits, logConst.eventStoreTookCredits):
                        rx = self.DB2.SQLBigInt('*', 'zevent.genericEvents', "eventTable = 'O'", '', 'eventID', row.eventID)
                        refID = '%s %s' % ('Gave' if eventTypeID == logConst.eventStoreGaveCredits else 'Took', 'ISK' if rx[0].int_1 == const.creditsISK else 'AURUM')
                        refType = '%10.2f' % (rx[0].money_1 or 0.0)
                        if rx[0].bigint_1 is not None:
                            refText = self.Link('/gm/accounting.py', 'Transaction ID: %s' % rx[0].bigint_1, {'action': 'TxDetail',
                             'transactionID': rx[0].bigint_1})
                        else:
                            refText = ''
                        return [refID, refType, refText]
                    return [referenceID, 'Offer', self.GetTooltip(href='/gd/store.py', ajax='/gm/store.py?action=OfferTooltip&offerID=%d' % referenceID, title='Offer Details', caption='Offer Details')]
                if referenceColumn == 'taleID':
                    return [self.Link('/gm/tale.py', referenceID, {'taleID': referenceID}), 'Tale ID', self.Link('/gm/tale.py', 'Tale', {'taleID': referenceID})]
                if referenceColumn == 'killID':
                    return [self.Link('/gm/character.py', referenceID, {'action': 'KillReport',
                      'killID': referenceID}), 'Kill Report', self.Link('/gm/character.py', 'Kill Report', {'action': 'KillReport',
                      'killID': referenceID})]
            if eventTypeID == logConst.eventCharacterPaused:
                return ['', 'User Account', 'The users account is not active, all training paused on all characters! (skills, RP)']
            if eventTypeID == logConst.eventCharacterResumed:
                return ['', 'User Account', 'The users account has been reactivated, all training resumed on all characters! (skills, RP)']
            if eventTypeID == logConst.eventResearchStopped:
                return [referenceID, 'Research points lost', '']
            if eventTypeID == logConst.eventResearchGMEdit:
                return [self.ItemID(referenceID), 'Character', self.CharacterLink(referenceID)]
            if eventTypeID == logConst.eventStoreOfferDeleted:
                return [referenceID, '', 'it was deleted, and lost for all time!']
            if eventGroupID == const.groupAlliance:
                if util.IsCorporation(referenceID):
                    return [self.ItemID(referenceID), 'Corporation', self.CorporationLink(referenceID)]
                else:
                    return [self.Link('/gm/logs.py', str(referenceID), {'action': 'OwnerEvent',
                      'eventID': referenceID}), 'Alliance Event', '']
            if eventTypeID in (logConst.eventItemReimburse,
             logConst.eventItemEdit,
             logConst.eventItemEditFrom,
             logConst.eventItemEditTo):
                referenceText = ''
                if 'uiItemID' in row.__columns__:
                    if row.uiItemID:
                        referenceText = self.ItemID(row.uiItemID)
                        referenceText = self.SplitAdd(referenceText, self.TypeLink(row.uiTypeID))
                return [self.Link('/gm/logs.py', referenceID, {'action': 'ItemEvent',
                  'eventID': referenceID}), 'Item Event', referenceText]
            if eventTypeID == logConst.eventSecStatusGmRollback:
                return [self.Link('/gm/logs.py', str(referenceID), {'action': 'OwnerEvent',
                  'eventID': referenceID}), 'Original Event', '']
            refType = 'Unknown'
            if et.referenceTable and et.referenceColumn:
                refType = '%s.%s' % (et.referenceTable, et.referenceColumn)
            elif et.referenceTable:
                refType = et.referenceTable
            elif et.referenceColumn:
                refType = et.referenceColumn
            return [referenceID, refType, 'Unknown']


    class GDHtmlWriter(ESPHtmlWriter):
        __guid__ = 'htmlwriter.GDHtmlWriter'

        def __init__(self, template = 'script:/wwwroot/lib/template/base.html', page = '', showMenu = True):
            ESPHtmlWriter.__init__(self, template, 'CONTENT', page, showMenu)
            self.inserts['body'] = ''

        def WriteLeftMenu(self, action):
            pass

        def WriteRightMenu(self):
            pass

        def CategoriesPart(self, categoryID, categoryAction = 'Category', placement = 'rMenu'):
            categories = []
            for c in cfg.invcategories:
                if c.categoryID > 0:
                    bon = ''
                    boff = ''
                    if c.categoryID == categoryID:
                        bon = '<b>'
                        boff = '</b>'
                    categories.append([c.categoryName, bon + self.Link('type.py', c.categoryName, {'action': categoryAction,
                      'categoryID': c.categoryID}) + boff])

            categories.sort()
            categories = map(lambda line: line[1:], categories)
            return categories

        def GroupsPart(self, categoryID, groupID, groupAction = 'Group', placement = 'rMenu'):
            groups = []
            for g in cfg.groupsByCategories.get(categoryID, []):
                bon = ''
                boff = ''
                if g.groupID == groupID:
                    bon = '<b>'
                    boff = '</b>'
                groups.append([g.groupName, bon + self.Link('type.py', g.groupName, {'action': groupAction,
                  'categoryID': categoryID,
                  'groupID': g.groupID}) + boff])

            groups.sort()
            groups = map(lambda line: line[1:], groups)
            return groups

        def TypesPart(self, groupID, typeID, typeAction = 'Type', placement = 'rMenu'):
            types = []
            for t in self.DB2.SQLInt('typeID, typeName', 'inventory.typesEx', '', 'typeName', 'groupID', groupID):
                bon = ''
                boff = ''
                if t.typeID == typeID:
                    bon = '<b>'
                    boff = '</b>'
                types.append([bon + self.Link('type.py', t.typeName, {'action': typeAction,
                  'typeID': t.typeID}) + boff])

            return types

        def TypeImage(self, typeID, width = 64):
            """
            Provide a link to the image from the image server
            """
            imageServerURL = sm.GetService('machoNet').GetGlobalConfig().get('imageserverurl')
            if imageServerURL == '':
                return '/img/type.jpg'
            imgURL = imageServerURL + 'Type/%s_64.png' % typeID
            return imgURL

        def GetType(self, typeID, rawBsdData = False):
            typeObject = None
            row = self.DB2.SQLInt('*', 'inventory.typesEx', '', '', 'typeID', typeID)
            if len(row) > 0:
                typeObject = row[0]
                if not rawBsdData and typeID in cfg.invtypes:
                    typeObject.graphicID = cfg.invtypes.Get(typeID).graphicID
                    typeObject.iconID = cfg.invtypes.Get(typeID).iconID
                    typeObject.soundID = cfg.invtypes.Get(typeID).soundID
                    typeObject.radius = cfg.invtypes.Get(typeID).radius
            return typeObject

        def BSDTypeHeader(self, typeID, typeAction = 'Type'):
            return self.TypeHeader(typeID, typeAction, rawBsdData=True)

        def TypeHeader(self, typeID, typeAction = 'Type', rawBsdData = False):
            typeObject = self.GetType(typeID, rawBsdData)
            typeName = ''
            typeNameID = None
            groupID = -1
            categoryID = -1
            if typeObject != None:
                typeName = typeObject.typeName
                typeNameID = typeObject.typeNameID
                groupID = typeObject.groupID
                group = cfg.invgroups.GetIfExists(groupID)
                if group is None:
                    categoryID = None
                else:
                    categoryID = group.categoryID
            lines = []
            lines.append([1, 'Group', self.GroupLink(groupID)])
            lines.append([1, 'Category', self.CategoryLink(categoryID)])
            self.SubjectHeader(1, 'TYPE', typeID, self.GetLocalizationLabel(typeName, typeNameID), '#C0C0C0', self.TypeImage(typeID), '/gd/type.py', 'Type', 'typeID', lines, 64, 64)
            li = []
            li.append('#TYPE')
            li.append(self.Link('type.py', 'INFO', {'action': 'Type',
             'typeID': typeID}))
            li.append('%s%s%s' % (self.Link('type.py', 'Balls', {'action': 'TypeBalls',
              'typeID': typeID}), self.MidDot(), self.Link('type.py', 'Contraband', {'action': 'TypeContraband',
              'typeID': typeID})))
            li.append(self.Link('type.py', 'Dogma Info', {'action': 'TypeDogma',
             'typeID': typeID}))
            li.append('%s%s%s' % (self.Link('type.py', 'Loot', {'action': 'TypeLoot',
              'typeID': typeID}), self.MidDot(), self.Link('type.py', 'Market', {'action': 'TypeMarket',
              'typeID': typeID})))
            li.append('%s%s%s' % (self.Link('type.py', 'Materials', {'action': 'TypeMaterials',
              'typeID': typeID}), self.MidDot(), self.Link('type.py', 'Requirements', {'action': 'TypeRequirements',
              'typeID': typeID})))
            li.append('%s%s%s' % (self.Link('type.py', 'Reactions', {'action': 'TypeReactions',
              'typeID': typeID}), self.MidDot(), self.Link('type.py', 'Skills', {'action': 'TypeSkills',
              'typeID': typeID})))
            if categoryID == const.categoryEntity:
                li.append(self.Link('npcCreator.py', 'View Modules', {'action': 'ViewModulesOnType',
                 'typeID': typeID}))
            if groupID == const.groupControlTower:
                li.append(self.Link('type.py', 'Tower Resources', {'action': 'TypeTowerResources',
                 'typeID': typeID}))
            li.append('-')
            if typeObject:
                act = self.RevisionLink(typeObject)
                if session.role & ROLE_CONTENT:
                    act = self.Link('type.py', 'EDIT', {'action': 'EditTypeForm',
                     'typeID': typeID}) + self.MidDot() + act
                li.append(act)
            li.append('%s%s%s' % (self.Link('type.py', 'CHANGES', {'action': 'Changes',
              'typeID': typeID}), self.MidDot(), self.Link('type.py', 'RELATIONS', {'action': 'Relations',
              'typeID': typeID})))
            if session.role & ROLE_CONTENT > 0:
                li.append(self.Link('type.py', 'Copy', {'action': 'TypeCopyForm',
                 'typeID': typeID}))
                if categoryID == const.categoryShip:
                    li.append(self.Link('type.py', 'Edit Ship Info', {'action': 'EditTypeShipForm',
                     'typeID': typeID}))
                elif groupID == const.groupStation:
                    li.append(self.Link('type.py', 'Edit Station Info', {'action': 'EditTypeStationForm',
                     'typeID': typeID}))
                li.append(self.Link('type.py', 'Edit Dogma Info', {'action': 'EditTypeDogmaForm',
                 'typeID': typeID}))
                li.append(self.Link('materials.py', 'Edit Materials', {'action': 'EditTypeMaterialsForm',
                 'typeID': typeID}))
                li.append(self.Link('type.py', 'Meta Types', {'action': 'MetaTypes',
                 'parentTypeID': typeID}))
                li.append('>%s%s%s' % (self.Link('type.py', 'Add', {'action': 'InsertMetaTypeForm',
                  'parentTypeID': typeID}), self.MidDot(), self.Link('type.py', 'Associate to Master', {'action': 'InsertMetaTypeReverseForm',
                  'typeID': typeID})))
                li.append(self.Link('type.py', 'REMOVE', {'action': 'RemoveTypeForm',
                 'typeID': typeID}))
            self.SubjectActions(li)
            self.WriteDirect('rMenu', self.Break())
            self.WriteDirect('rMenu', self.WebPart('Types', self.GetTable([], self.TypesPart(groupID, typeID, typeAction), showCount=False), 'wpTypes'))
            self.WriteDirect('rMenu', self.WebPart('Groups', self.GetTable([], self.GroupsPart(categoryID, groupID), showCount=False), 'wpGroups'))
            self.WriteDirect('rMenu', self.WebPart('Categories', self.GetTable([], self.CategoriesPart(categoryID), showCount=False), 'wpCategories'))
            if typeObject is None:
                self.WriteError('Record not found')
            return typeObject

        def ValidateMarketGroupPublishedTypes(self, marketGroupID):
            rs = self.DB2.SQL('SELECT T.published\n                                   FROM inventory.typesDx T\n                                     INNER JOIN inventory.marketGroups MG ON MG.marketGroupID = T.marketGroupID\n                                  WHERE MG.marketGroupID = %d' % marketGroupID)
            if rs:
                for r in rs:
                    if r.published == 1:
                        return True

                return False
            return True

        def MarketGroupHasInvalidTypes(self, marketGroupID):
            rs = self.DB2.SQL('SELECT TOP 1 *\n                                   FROM inventory.typesDx T\n                                     INNER JOIN inventory.marketGroups MG ON MG.marketGroupID = T.marketGroupID\n                                  WHERE MG.hasTypes = 0 AND MG.marketGroupID = %d' % marketGroupID)
            if rs:
                return True
            return False

        def FormatMarketGroupLink(self, marketGroupID):
            if self.MarketGroupHasInvalidTypes(marketGroupID):
                return self.Link('', self.FontBoldRed(marketGroupID), {'action': 'MarketGroupTypes',
                 'marketGroupID': marketGroupID})
            return marketGroupID


    class SessionHtmlWriter(htmlwriter.HtmlWriterEx):
        __guid__ = 'htmlwriter.SessionHtmlWriter'

        def __init__(self):
            htmlwriter.HtmlWriterEx.__init__(self)

        def Generate(self):
            self.s = htmlwriter.UnicodeMemStream()
            if session is not None and session.charid:
                li = []
                liHead = []
                liHead.append([self.Image('/img/character.py?characterID=%i&size=64' % session.charid), self.FontPurple(session.charid, size=4)])
                self.s.Write(self.WebPart('&nbsp;&nbsp;&nbsp;&nbsp;Character', self.Table([], liHead) + self.GetTable([], li), 'charpart'))
            self.s.Seek(0)
            return str(self.s.Read())


    class PetitionHtmlWriter(ESPHtmlWriter):
        __guid__ = 'htmlwriter.PetitionHtmlWriter'

        def __init__(self, template = 'script:/wwwroot/lib/template/baseNoRight.html', page = ''):
            ESPHtmlWriter.__init__(self, template, 'TICKET', page)
            self.EnableExperiments()


    class PetitionClientHtmlWriter(ESPHtmlWriter):
        __guid__ = 'htmlwriter.PetitionClientHtmlWriter'

        def __init__(self, template = 'script:/wwwroot/lib/template/baseWideLeftNoRight.html', page = ''):
            ESPHtmlWriter.__init__(self, template, 'TICKET', page)
            self.EnableExperiments()


if macho.mode in ('server', 'proxy'):

    class AdminHtmlWriter(ESPHtmlWriter):
        __guid__ = 'htmlwriter.AdminHtmlWriter'

        def __init__(self, template = 'script:/wwwroot/lib/template/base.html', page = ''):
            ESPHtmlWriter.__init__(self, template, 'ADMIN', page)


class InfoHtmlWriter(ESPHtmlWriter):
    __guid__ = 'htmlwriter.InfoHtmlWriter'

    def __init__(self, template = 'script:/wwwroot/lib/template/baseNoRight.html', page = ''):
        ESPHtmlWriter.__init__(self, template, 'INFO', page)


def hook_AppServerPages(writer, menu = ''):
    if writer.showMenu:
        dGML = not session.role & ROLE_GML
        dCONTENT = not session.role & ROLE_CONTENT
        dADMIN = not session.role & ROLE_ADMIN
        dVIEW = not session.role & ROLEMASK_VIEW
        dPROG = not session.role & ROLE_PROGRAMMER
        if macho.mode == 'server':
            writer.inserts['icon'] = writer.Link('/gm/search.py', writer.Image('/img/menu_search32.jpg', 'width=32 height=32'))
            writer.AddTopMenuSubLine('GM')
            writer.AddTopMenuSub('GM', 'Search', '/gm/search.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Find Item', '/gm/inventory.py?action=FindItem', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Item Report', '/gm/inventory.py?action=Item', disabled=dVIEW)
            writer.AddTopMenuSubLine('GM')
            writer.AddTopMenuSub('GM', 'Alliances', '/gm/alliance.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Calendar', '/gm/calendar.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Contracts', '/gm/contracts.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Corporations', '/gm/corporation.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Factions', '/gm/faction.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Fleets', '/gm/fleet.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Inventory', '/gm/inventory.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Starbases', '/gm/starbase.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Stations', '/gm/stations.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Tale', '/gm/tale.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Industry', '/gm/industry.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Teams', '/gm/teams.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Planets', '/gm/planets.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Voice Chat', '/gm/voice.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Virtual Store', '/gm/store.py', disabled=dVIEW)
            writer.AddTopMenuSubLine('GM')
            writer.AddTopMenuSub('GM', 'Battles', '/dust/battles.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Districts', '/dust/districts.py', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Queues', '/dust/queues.py', disabled=dVIEW)
            writer.AddTopMenuSubLine('GM')
            writer.AddTopMenuSub('GM', 'Content Staging', '/admin/contentstreaming.py?action=Staging', disabled=dVIEW)
            writer.AddTopMenuSub('GM', 'Content Assets', '/admin/contentstreaming.py?action=Overview', disabled=dVIEW)
            writer.AddTopMenuSub('TICKET', 'My Tickets', '/gm/petitionClient.py?action=ShowMyPetitions', disabled=dVIEW)
            writer.AddTopMenuSubLine('TICKET')
            writer.AddTopMenuSub('TICKET', 'Answer Tickets', '/gm/petitionClient.py?action=ShowClaimedPetitions', disabled=dVIEW)
            writer.AddTopMenuSub('TICKET', 'Knowledge Base', '/gm/knowledgebase.py', disabled=dCONTENT)
            writer.AddTopMenuSub('TICKET', 'Ticket Management', '/gm/petition.py', disabled=dGML)
            writer.AddTopMenuSub('TICKET', 'Support Management', '/gm/supportManagement.py', disabled=dGML)
            writer.AddTopMenuSubLine('CONTENT')
            writer.AddTopMenuSub('CONTENT', 'Agents', '/gd/agents.py', disabled=dGML and dCONTENT and dADMIN)
            writer.AddTopMenuSub('CONTENT', 'Characters', '/gd/characters.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Client Setings', '/gd/client.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Combat Zones', '/gd/combatZones.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Corporations', '/gd/corporations.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Dungeons', '/gd/dungeons.py', disabled=dVIEW and dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Dungeon Distribution', '/gd/dungeonDistributions.py', disabled=dVIEW and dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Expo Settings', '/gd/expo.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Market', '/gd/market.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Materials', '/gd/materials.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Moon Distributions', '/gd/distribution.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Names', '/gd/names.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'NPC', '/gd/npc.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'NPC Creator', '/gd/npcCreator.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Planet Resources', '/gd/planetResource.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Play Ground', '/gd/playGround.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Reactions', '/gd/reactions.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Rewards', '/gd/rewards.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Schematics', '/gd/schematics.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Science & Industry', '/gd/ram.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Spawn List', '/gd/spawnlist.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Tale', '/gd/tale.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Types', '/gd/type.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Type Distribution', '/gd/tdm.py', disabled=dCONTENT)
            writer.AddTopMenuSub('CONTENT', 'Tutorials', '/gd/tutorials.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Universe', '/gd/universe.py', disabled=dVIEW)
            writer.AddTopMenuSub('CONTENT', 'Virtual Store', '/gd/store.py', disabled=dVIEW)
            writer.AddTopMenuSubLine('CONTENT')
            writer.AddTopMenuSub('CONTENT', 'Catma', '/catma/catmaMK2.py', disabled=dVIEW)
            writer.AddTopMenuSubLine('INFO')
            writer.AddTopMenuSub('INFO', 'Beyonce', '/info/beyonce.py', disabled=dVIEW)
            writer.AddTopMenuSub('INFO', 'Map', '/info/map.py', disabled=dVIEW)
            writer.AddTopMenuSub('INFO', 'Dogma', '/info/dogma.py')
            writer.AddTopMenuSub('INFO', 'FW Reports', '/info/facwarreports.py')
            writer.AddTopMenuSub('INFO', 'Inventory', '/info/inventory.py')
            writer.AddTopMenuSub('INFO', 'CEF', '/info/cef.py')
            writer.AddTopMenuSub('INFO', 'Aperture', '/info/aperture.py')
            writer.AddTopMenuSub('INFO', 'Crimewatch', '/info/crimewatch.py', disabled=dVIEW)
            writer.AddTopMenuSub('INFO', 'Loot-rights', '/info/lootRights.py', disabled=dVIEW)
            writer.AddTopMenuSubLine('ADMIN')
            writer.AddTopMenuSub('ADMIN', 'Client Stats', '/admin/clientStats2_2.py', disabled=dADMIN)
            writer.AddTopMenuSub('ADMIN', 'Info Gathering', '/admin/infoGathering.py', disabled=dADMIN)
            writer.AddTopMenuSub('ADMIN', 'Multinode Setup Helper', '/admin/multinodeSetup.py', disabled=dADMIN)
            writer.AddTopMenuSubLine('ADMIN')
            writer.AddTopMenuSub('ADMIN', 'Prefs', '/info/machine.py?action=Prefs', disabled=dADMIN)
            writer.AddTopMenuSub('ADMIN', 'DB Settings', '/info/db.py?action=Settings', disabled=dADMIN)
            writer.AddTopMenuSub('ADMIN', 'Global Config', '/admin/network.py?action=GlobalConfig', disabled=dADMIN)
            writer.AddTopMenuSubLine('ADMIN')
            writer.AddTopMenuSub('ADMIN', 'Server Options', '/admin/default.py', disabled=dPROG)
            writer.AddTopMenuSub('ADMIN', 'Live Market', '/admin/liveMarket.py', disabled=dADMIN)
            writer.AddTopMenuSubLine('ADMIN')
            writer.AddTopMenuSub('ADMIN', 'Edit ESP', '/admin/editEsp.py', disabled=dPROG)
            writer.AddTopMenuSubLine('ADMIN')
            writer.AddTopMenuSub('ADMIN', 'Crest Queue Testing', '/admin/crestQueueTesting.py', disabled=dVIEW)
        elif macho.mode == 'proxy':
            pass
        elif macho.mode == 'client':
            pass
        if macho.mode == 'server':
            if menu == 'GM':
                writer.AddMenu('Search', 'Search', '', '/gm/search.py')
                writer.AddMenu('Alliances', 'Alliances', '', '/gm/alliance.py')
                writer.AddMenu('Contracts', 'Contracts', '', '/gm/contracts.py')
                writer.AddMenu('Corporations', 'Corporations', '', '/gm/corporation.py')
                writer.AddMenu('Factions', 'Factions', '', '/gm/faction.py')
                writer.AddMenu('Inventory', 'Inventory', '', '/gm/inventory.py')
                writer.AddMenu('Starbases', 'Starbases', '', '/gm/starbase.py')
                writer.AddMenu('Stations', 'Stations', '', '/gm/stations.py')
                writer.AddMenu('Industry', 'Industry', '', '/gm/industry.py')
                writer.AddMenu('Teams', 'Teams', '', '/gm/teams.py')
                writer.AddMenu('Battles', 'Battles', '', '/dust/battles.py')
                writer.AddMenu('Districts', 'Districts', '', '/dust/districts.py')
            elif menu == 'TICKET':
                writer.AddMenu('AnswerPetitions', 'Answer Tickets', '', '/gm/petitionClient.py?action=ShowClaimedPetitions')
                writer.AddMenu('KnowledgeBase', 'Knowledge Base', '', '/gm/knowledgebase.py')
                writer.AddMenu('PetitionManagement', 'Ticket Management', '', '/gm/petition.py')
                writer.AddMenu('SupportManagement', 'Support Management', '', '/gm/supportManagement.py')
                writer.AddMenu('SpamReports', 'Spam Reports', '', '/gm/users.py?action=ListSpamUsers')
                writer.AddMenu('Characters', 'Characters', '', '/gm/character.py')
                writer.AddMenu('Users', 'Users', '', '/gm/users.py')
                writer.AddMenu('Search', 'Search', '', '/gm/search.py')
                writer.AddMenu('ItemReport', 'Item Report', '', '/gm/inventory.py?action=Item')
                writer.AddMenu('FindItem', 'Find Item', '', '/gm/inventory.py?action=FindItem')
                writer.AddMenu('My Characters', 'My Characters', '', '/gm/character.py?action=MyCharacters')
            elif menu == 'CONTENT':
                writer.AddMenu('Agents', 'Agents', '', '/gd/agents.py')
                writer.AddMenu('Characters', 'Characters', '', '/gd/characters.py')
                writer.AddMenu('Corporations', 'Corporations', '', '/gd/corporations.py')
                writer.AddMenu('Dungeons', 'Dungeons', '', '/gd/dungeons.py')
                writer.AddMenu('Market', 'Market', '', '/gd/market.py')
                writer.AddMenu('Materials', 'Materials', '', '/gd/materials.py')
                writer.AddMenu('MoonDistributions', 'Moon Distributions', '', '/gd/distribution.py')
                writer.AddMenu('NPC', 'NPC', '', '/gd/npc.py')
                writer.AddMenu('NPCCreator', 'NPC Creator', '', '/gd/npcCreator.py')
                writer.AddMenu('Reactions', 'Reactions', '', '/gd/reactions.py')
                writer.AddMenu('Rewards', 'Rewards', '', '/gd/rewards.py')
                writer.AddMenu('Schematics', 'Schematics', '', '/gd/schematics.py')
                writer.AddMenu('S&I', 'S&I', '', '/gd/ram.py')
                writer.AddMenu('Spawnlist', 'Spawn List', '', '/gd/spawnlist.py')
                writer.AddMenu('Tale', 'Tale', '', '/gd/tale.py')
                writer.AddMenu('Types', 'Types', '', '/gd/type.py')
                writer.AddMenu('Tutorials', 'Tutorials', '', '/gd/tutorials.py')
                writer.AddMenu('Universe', 'Universe', '', '/gd/universe.py')
            elif menu == 'INFO':
                writer.AddMenu('Inventory', 'Inventory', '', '/info/inventory.py')
                writer.AddMenu('Dogma', 'Dogma', '', '/info/dogma.py')
                writer.AddMenu('Beyonce', 'Beyonce', '', '/info/beyonce.py')
                writer.AddMenu('Map', 'Map', '', '/info/map.py')
                writer.AddMenu('Crimewatch', 'Crimewatch', '', '/info/crimewatch.py')
                writer.AddMenu('Loot-rights', 'Loot-rights', '', '/info/lootRights.py')
            elif menu == 'ADMIN':
                writer.AddMenu('ClientStats', 'Client-Stats', '', '/admin/clientStats2.py')
        elif macho.mode == 'proxy':
            pass
        elif macho.mode == 'client':
            pass
