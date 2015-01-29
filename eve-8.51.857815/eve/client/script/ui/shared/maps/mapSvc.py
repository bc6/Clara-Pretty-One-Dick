#Embedded file name: eve/client/script/ui/shared/maps\mapSvc.py
"""
A facade for the map and the keeper of the map cache along with related slicing and dicing of cache data.
Now the star map and system map are hosted in seperated services proxied by this map service.
"""
import fsdSchemas.binaryLoader as fsdBinaryLoader
import uicontrols
import service
from service import SERVICE_START_PENDING, SERVICE_RUNNING
import blue
import telemetry
import form
import trinity
import uthread
import util
from mapcommon import COLORCURVE_SECURITY, STARMAP_SCALE, SOLARSYSTEM_JUMP, JUMP_COLORS, LINESET_EFFECT
import mapcommon
import geo2
import log
import carbonui.const as uiconst
import const
import searchUtil
TRANSLATETBL = '                               ! #$%&\\  ()*+,-./0123456789:;<=>?@abcdefghijklmnopqrstuvwxyz[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~                  \x91\x92             \xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbfaaaaaa\xc6ceeeeiiii\xd0nooooo\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdfaaaaaa\xe6ceeeeiiii\xf0nooooo\xf7ouuuuy\xfey'

class MapSvc(service.Service):
    __guid__ = 'svc.map'
    __notifyevents__ = ['OnSessionChanged']
    __servicename__ = 'map'
    __displayname__ = 'Map Client Service'
    __update_on_reload__ = 0
    __startupdependencies__ = ['settings']

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        self.LogInfo('Starting Map Client Svc')
        self.Reset()
        self.state = SERVICE_RUNNING

    def Stop(self, memStream = None):
        if trinity.device is None:
            return
        self.LogInfo('Map svc')
        self.Reset()

    def OnSessionChanged(self, isRemote, sess, change):
        if 'charid' in change:
            self.__PurgeOldCachedMap2dData()

    def Reset(self):
        self.LogInfo('MapSvc Reset')
        self.securityInfo = None
        self.minimizedWindows = []
        self.activeMap = ''
        self.mapconnectionscache = None
        self.landmarks = None
        sm.ScatterEvent('OnMapReset')

    def Open(self):
        viewSvc = sm.GetService('viewState')
        if not viewSvc.IsViewActive('starmap', 'systemmap'):
            activeMap = settings.user.ui.Get('activeMap', 'starmap')
            viewSvc.ActivateView(activeMap)

    def GetActiveMapName(self):
        return settings.user.ui.Get('activeMap', 'starmap')

    def MinimizeWindows(self):
        """
            Minimize windows that are not related to the map. Currently it's only the
            lobby which is minimized.
        """
        lobby = form.Lobby.GetIfOpen()
        if lobby and not lobby.destroyed and lobby.state != uiconst.UI_HIDDEN and not lobby.IsMinimized() and not lobby.IsCollapsed():
            lobby.Minimize()
            self.minimizedWindows.append(form.Lobby.default_windowID)

    def ResetMinimizedWindows(self):
        if len(self.minimizedWindows) > 0:
            windowSvc = sm.GetService('window')
            for windowID in self.minimizedWindows:
                wnd = uicontrols.Window.GetIfOpen(windowID=windowID)
                if wnd and wnd.IsMinimized():
                    wnd.Maximize()

            self.minimizedWindows = []

    def Toggle(self, *args):
        viewSvc = sm.GetService('viewState').ToggleSecondaryView(self.GetActiveMapName())

    def ToggleMode(self, *args):
        viewSvc = sm.GetService('viewState')
        if viewSvc.IsViewActive('starmap'):
            viewSvc.ActivateView('systemmap')
        elif viewSvc.IsViewActive('systemmap'):
            viewSvc.ActivateView('starmap')

    def OpenMapsPalette(self):
        openMinimized = settings.user.ui.Get('MapWindowMinimized', False)
        form.MapsPalette.Open(openMinimized=openMinimized)

    def CloseMapsPalette(self):
        form.MapsPalette.CloseIfOpen()

    def GetSecColorList(self):
        return COLORCURVE_SECURITY

    def GetSecurityStatus(self, solarSystemID, getColor = False):
        """
            returns 'pseudo' security for 'solarSystemID' in the following format:
            Rounds the security to the nearest one digit precision with the following exeption:
            0.0 < sec < 0.05 is rounded up to 0.1 but not down to 0.0
            example: 0.08 -> 0.1, -0.22 -> -0.2, 0.451 -> 0.5, 0.449 -> 0.4, -0.26 -> -0.3
        """
        if self.securityInfo is None:
            uthread.Lock(self)
            try:
                self.securityInfo = {}
                for systemID, each in cfg.mapSystemCache.iteritems():
                    self.securityInfo[systemID] = each.pseudoSecurity

            finally:
                uthread.UnLock(self)

        return util.FmtSystemSecStatus(self.securityInfo.get(solarSystemID, 0.0), getColor)

    def GetSecurityClass(self, solarSystemID):
        """
            Returns the security class of 'solarSystemID'
            use:  secClass = sm.GetService("map").GetSecurityClass(solarSystemID)
            pre:  solarSystemID is a valid solarsystemID
            post: secClass is securityClassZeroSec if zero sec, securityClassLowSec if low sec and securityClassHighSec if high sec
        """
        secLevel = self.GetSecurityStatus(solarSystemID)
        return util.SecurityClassFromLevel(secLevel)

    @telemetry.ZONE_METHOD
    def GetSolarsystemItems(self, solarsystemID, requireLocalizedTexts = True, doYields = False):
        """ The values returned here are cached for each client run """
        local, playerStations = uthread.parallel([(cfg.GetLocationsLocalBySystem, (solarsystemID, requireLocalizedTexts, doYields)), (sm.RemoteSvc('config').GetDynamicCelestials, (solarsystemID,))], contextSuffix='GetSolarsystemItems')
        for station in playerStations:
            local.InsertNew(station)

        return local

    def __PurgeOldCachedMap2dData(self):
        """ 
            This is here to remove massive amounts of unnecessary data that were being stored in user settings
            Added Jan 2012 by Arnar B., CL 329819
            Please remove if plenty of time has passed
        """
        try:
            settingKeys = settings.user.ui.GetValues()
            toRemove = []
            for key in settingKeys.keys():
                if isinstance(key, str) and key.startswith('map2d_'):
                    toRemove.append(key)

            for key in toRemove:
                settings.user.ui.Delete(key)
                log.LogInfo('Successfully removed old F11 map cache data: %s' % key)

        except:
            log.LogException('Failed to purge old map cache out of settings')

    def GetMapConnectionCache(self):
        if self.mapconnectionscache is None:
            self.mapconnectionscache = settings.user.ui.Get('map_cacheconnectionsfile', {})
        return self.mapconnectionscache or {}

    def GetItem(self, itemID, retall = False):
        """
        Get item or items from map cache items section
        
        itemID: the id of the item to retrieve
        retall: return first if False, all if True
        returns one or more map cache items or None if not found
        """
        if util.IsStation(itemID):
            station = cfg.stations.Get(itemID)
            return util.KeyVal(itemID=itemID, locationID=station.solarSystemID, itemName=cfg.evelocations.Get(itemID).name, typeID=station.stationTypeID, groupID=const.groupStation, x=station.x, y=station.y, z=station.z)
        if util.IsSolarSystem(itemID):
            solarSystem = cfg.mapSystemCache.Get(itemID)
            return util.KeyVal(itemID=itemID, locationID=solarSystem.constellationID, itemName=cfg.evelocations.Get(itemID).name, typeID=const.typeSolarSystem, groupID=const.groupSolarSystem, factionID=getattr(solarSystem, 'factionID', None), neighbours=[ i.solarSystemID for i in solarSystem.neighbours ], x=solarSystem.center.x, y=solarSystem.center.y, z=solarSystem.center.z, security=solarSystem.securityStatus)
        if util.IsConstellation(itemID):
            constellation = cfg.mapConstellationCache.Get(itemID)
            return util.KeyVal(itemID=itemID, locationID=constellation.regionID, itemName=cfg.evelocations.Get(itemID).name, typeID=const.typeConstellation, neighbours=list(constellation.neighbours), groupID=const.groupConstellation, x=constellation.center.x, y=constellation.center.y, z=constellation.center.z)
        if util.IsRegion(itemID):
            region = cfg.mapRegionCache.Get(itemID)
            return util.KeyVal(itemID=itemID, locationID=const.locationUniverse, itemName=cfg.evelocations.Get(itemID).name, neighbours=list(region.neighbours), typeID=const.typeRegion, groupID=const.groupRegion, x=region.center.x, y=region.center.y, z=region.center.z)
        if util.IsCelestial(itemID):
            solarSystemID = cfg.mapCelestialLocationCache[itemID]
            typeID, pos = self._GetCelestialsTypeIdAndPosition(itemID, solarSystemID)
            return util.KeyVal(itemID=itemID, locationID=solarSystemID, itemName=cfg.evelocations.Get(itemID).name, typeID=typeID, x=pos[0], y=pos[1], z=pos[2])

    def _GetCelestialsTypeIdAndPosition(self, itemID, solarSystemID):
        """
        Returns the typeId and position of a celestial in a solarsystem
        :raises KeyError: if a celestial is not found
        
        :param itemID: the id of a celestial
        :param solarSystemID: the id of the celestials solarsystem
        :return: a tuple containing a typeID and a position (a tuple containing x, y and z)
        """
        if itemID in cfg.mapSolarSystemContentCache.celestials:
            celestial = cfg.mapSolarSystemContentCache.celestials[itemID]
            return (celestial.typeID, celestial.position)
        solarSystem = cfg.mapSolarSystemContentCache[solarSystemID]
        if itemID == solarSystem.star.id:
            return (solarSystem.star.typeID, (0.0, 0.0, 0.0))
        raise KeyError('Celestial with id %s not found' % itemID)

    @telemetry.ZONE_METHOD
    def GetParentLocationID(self, locationID):
        if util.IsSolarSystem(locationID):
            solarSystem = cfg.mapSystemCache.Get(locationID)
            return (const.locationUniverse,
             solarSystem.regionID,
             solarSystem.constellationID,
             locationID,
             None)
        if util.IsConstellation(locationID):
            constellation = cfg.mapConstellationCache.Get(locationID)
            return (const.locationUniverse,
             constellation.regionID,
             locationID,
             None,
             None)
        if util.IsRegion(locationID):
            return (const.locationUniverse,
             locationID,
             None,
             None,
             None)
        if util.IsCelestial(locationID):
            solarSystemID = cfg.mapCelestialLocationCache[locationID]
            solarSystem = cfg.mapSystemCache.Get(solarSystemID)
            return (const.locationUniverse,
             solarSystem.regionID,
             solarSystem.constellationID,
             solarSystemID,
             locationID)
        if util.IsStation(locationID):
            station = cfg.stations.Get(locationID)
            ssID = station.solarSystemID
            solarSystem = cfg.mapSystemCache.Get(ssID)
            return (const.locationUniverse,
             solarSystem.regionID,
             solarSystem.constellationID,
             ssID,
             locationID)
        return (const.locationUniverse,
         None,
         None,
         None,
         locationID)

    def FindByName(self, searchstr, ignorecommas = 1):
        searchGroupList = [const.searchResultConstellation, const.searchResultSolarSystem, const.searchResultRegion]
        results = searchUtil.QuickSearch(searchstr, searchGroupList)
        return map(self.GetItem, results)

    def GetLandmarks(self):
        if self.landmarks is None:
            self.landmarks = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/landmarks.static')
        return self.landmarks

    def GetLandmark(self, landmarkID):
        return self.GetLandmarks()[landmarkID]

    def GetNeighbors(self, itemID):
        if util.IsWormholeSystem(itemID) or util.IsWormholeConstellation(itemID) or util.IsWormholeRegion(itemID):
            return []
        if util.IsSolarSystem(itemID):
            solarSystem = cfg.mapSystemCache.Get(itemID)
            return [ i.solarSystemID for i in solarSystem.neighbours ]
        if util.IsConstellation(itemID):
            constellation = cfg.mapConstellationCache.Get(itemID)
            return constellation.neighbours
        if util.IsRegion(itemID):
            region = cfg.mapRegionCache.Get(itemID)
            return region.neighbours
        return []

    def GetParent(self, itemID):
        if util.IsSolarSystem(itemID):
            solarSystem = cfg.mapSystemCache.Get(itemID)
            return solarSystem.constellationID
        elif util.IsConstellation(itemID):
            constellation = cfg.mapConstellationCache.Get(itemID)
            return constellation.regionID
        elif util.IsRegion(itemID):
            return const.locationUniverse
        elif util.IsCelestial(itemID):
            return cfg.mapCelestialLocationCache[itemID]
        elif util.IsStation(itemID):
            station = cfg.stations.Get(itemID)
            return station.solarSystemID
        else:
            return None

    def GetRegionForSolarSystem(self, solarSystemID):
        if util.IsSolarSystem(solarSystemID):
            solarSystem = cfg.mapSystemCache.Get(solarSystemID)
            return solarSystem.regionID
        else:
            return None

    def GetConstellationForSolarSystem(self, solarSystemID):
        if util.IsSolarSystem(solarSystemID):
            solarSystem = cfg.mapSystemCache.Get(solarSystemID)
            return solarSystem.constellationID
        else:
            return None

    def GetLocationChildren(self, itemID):
        if util.IsConstellation(itemID):
            return cfg.mapConstellationCache.Get(itemID).solarSystemIDs
        if util.IsRegion(itemID):
            return cfg.mapRegionCache.Get(itemID).constellationIDs
        raise Exception('Unexpected itemID calling GetLocationChildren?' + str(itemID))

    def ExpandItems(self, itemIDs):
        ret = []
        for i in itemIDs:
            ret.extend(self.GetSolarSystemIDsIn(i))

        return ret

    def GetSolarSystemIDsIn(self, i):
        if util.IsSolarSystem(i):
            return [i]
        if util.IsConstellation(i):
            return list(cfg.mapConstellationCache.Get(i).solarSystemIDs)
        if util.IsRegion(i):
            return list(cfg.mapRegionCache.Get(i).solarSystemIDs)

    def GetKnownspaceRegions(self):
        """
        get a generator for all knownspace regions
        """
        for regionID in cfg.mapRegionCache.iterkeys():
            if not util.IsWormholeRegion(regionID):
                yield regionID

    def IterateKnownspaceRegions(self):
        """
        Returns a generator for all knownspace regionID and regions
        """
        for regionID, region in cfg.mapRegionCache.iteritems():
            if not util.IsWormholeRegion(regionID):
                yield (regionID, region)

    def GetSleeperspaceRegions(self):
        """
        get a generator for all knownspace regions
        """
        for regionID in cfg.mapRegionCache.iterkeys():
            if regionID >= const.mapWormholeRegionMin:
                yield regionID

    def GetNumberOfStargates(self, itemID):
        """returns the total number of stargates in a system"""
        return len(cfg.mapSolarSystemContentCache[itemID].stargates)

    def IterateSolarSystemIDs(self, itemID = None):
        """returns an iterator with all the solarsystem IDs contained in itemID"""
        if itemID is None:
            for regionID in self.GetKnownspaceRegions():
                for s in cfg.mapRegionCache.Get(regionID).solarSystemIDs:
                    yield s

        elif util.IsSolarSystem(itemID):
            yield itemID
        elif util.IsConstellation(itemID):
            for systemID in cfg.mapConstellationCache.Get(itemID).solarSystemIDs:
                yield systemID

        elif util.IsRegion(itemID):
            for systemID in cfg.mapRegionCache.Get(itemID).solarSystemIDs:
                yield systemID

    def IterateKnownSpaceSolarSystems(self):
        for systemID, system in cfg.mapSystemCache.iteritems():
            if not util.IsWormholeSystem(systemID):
                yield (systemID, system)

    def GetPlanetInfo(self, planetID, hierarchy = False):
        """
        get the solarSystemID and typeID as a KeyVal
        Arguments:
        planetID - id of planet to get info on
        hierarchy - will extend the info with constellationID and regionID
        """
        p = cfg.mapSolarSystemContentCache.planets[planetID]
        typeID = p.typeID
        solarSystemID = p.solarSystemID
        info = util.KeyVal(solarSystemID=solarSystemID, typeID=typeID)
        if hierarchy:
            u, regionID, constellationID, s, i = self.GetParentLocationID(solarSystemID)
            info.regionID = regionID
            info.constellationID = constellationID
        return info

    def IteratePlanetInfo(self):
        for planetID, planetData in cfg.mapSolarSystemContentCache.planets.iteritems():
            yield self.PlanetInfo(planetID, planetData.solarSystemID, planetData.typeID)

    def CreateLineSet(self, path = LINESET_EFFECT):
        lineSet = trinity.EveLineSet()
        lineSet.effect = trinity.Tr2Effect()
        lineSet.effect.effectFilePath = path
        lineSet.renderTransparent = False
        return lineSet

    def CreateCurvedLineSet(self, effectPath = None):
        lineSet = trinity.EveCurveLineSet()
        if effectPath is not None:
            lineSet.lineEffect.effectFilePath = effectPath
        texMap = trinity.TriTexture2DParameter()
        texMap.name = 'TexMap'
        texMap.resourcePath = 'res:/dx9/texture/UI/lineSolid.dds'
        lineSet.lineEffect.resources.append(texMap)
        overlayTexMap = trinity.TriTexture2DParameter()
        overlayTexMap.name = 'OverlayTexMap'
        overlayTexMap.resourcePath = 'res:/dx9/texture/UI/lineOverlay5.dds'
        lineSet.lineEffect.resources.append(overlayTexMap)
        return lineSet

    class PlanetInfo(object):
        __slots__ = ['planetID', 'solarSystemID', 'typeID']

        def __init__(self, planetID, solarSystemID, typeID):
            self.planetID = planetID
            self.solarSystemID = solarSystemID
            self.typeID = typeID

    def GetSystemColorString(self, solarSystemID):
        """Get security color value for solarsystem as hex color"""
        col = self.GetSystemColor(solarSystemID)
        return util.Color.RGBtoHex(col.r, col.g, col.b)

    def GetSystemColor(self, solarSystemID):
        """Get the security color value for a solarsystem"""
        sec, col = util.FmtSystemSecStatus(self.GetSecurityStatus(solarSystemID), 1)
        return col

    def GetStation(self, stationID):
        """Gets information from the remote service and returns translated names. No caching involved."""
        station = sm.RemoteSvc('stationSvc').GetStation(stationID)
        if cfg.IsLocalIdentity(stationID) and not station.conquerable:
            station.stationName = cfg.evelocations.Get(stationID).name
        return station
