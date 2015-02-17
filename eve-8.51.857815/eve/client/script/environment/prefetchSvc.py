#Embedded file name: eve/client/script/environment\prefetchSvc.py
"""
Handles prefetching of assets on session change.
"""
import service
import util
import everesourceprefetch

class PrefetchSvc(service.Service):
    __guid__ = 'svc.prefetchSvc'
    __notifyevents__ = ['OnSessionChanged']

    def __init__(self):
        service.Service.__init__(self)

    def _AddGraphicAttribute(self, pla, attr, filesToPrefetch):
        graphic = util.GraphicFile(getattr(pla, attr))
        filesToPrefetch.add(graphic.lower())

    def GatherFilesForSolarSystem(self, ssid):
        filesToPrefetch = set()
        neighborSystemContents = cfg.mapSolarSystemContentCache[ssid]
        for stargateID, stargateInfo in neighborSystemContents.stargates.iteritems():
            typeID = stargateInfo.typeID
            graphic = cfg.invtypes.Get(typeID).Graphic().graphicFile
            filesToPrefetch.add(graphic.lower())

        for planetID, planetInfo in neighborSystemContents.planets.iteritems():
            pla = planetInfo.planetAttributes
            self._AddGraphicAttribute(pla, 'heightMap1', filesToPrefetch)
            self._AddGraphicAttribute(pla, 'heightMap2', filesToPrefetch)
            self._AddGraphicAttribute(pla, 'shaderPreset', filesToPrefetch)
            if hasattr(planetInfo, 'npcStations'):
                for stationID, stationInfo in planetInfo.npcStations.iteritems():
                    graphic = util.GraphicFile(stationInfo.graphicID)
                    filesToPrefetch.add(graphic.lower())

        return filesToPrefetch

    def SchedulePrefetchForSystem(self, ssid):
        key = 'solarsystem_%d_statics' % ssid
        if not everesourceprefetch.KeyExists(key):
            filesToPrefetch = self.GatherFilesForSolarSystem(ssid)
            everesourceprefetch.AddFileset(key, filesToPrefetch)
        everesourceprefetch.ScheduleFront(key)

    def SchedulePrefetchForStation(self, stationId):
        key = 'station_%d' % stationId
        if not everesourceprefetch.KeyExists(key):
            filesToPrefetch = set()
            npcStation = cfg.mapSolarSystemContentCache.npcStations.get(stationId, None)
            if npcStation:
                graphic = util.GraphicFile(npcStation.graphicID)
                filesToPrefetch.add(graphic.lower())
            everesourceprefetch.AddFileset(key, filesToPrefetch)
        everesourceprefetch.ScheduleFront(key)

    def OnSessionChanged(self, isremote, session, change):
        if 'stationid' in change:
            stationId = change['stationid'][1]
            if stationId:
                npcStation = cfg.mapSolarSystemContentCache.npcStations.get(stationId, None)
                if npcStation:
                    self.SchedulePrefetchForSystem(npcStation.solarSystemID)
                self.SchedulePrefetchForStation(stationId)
                return
        if 'solarsystemid' not in change:
            return
        ssid = change['solarsystemid'][1]
        if ssid is None:
            return
        systemInfo = cfg.mapSystemCache[ssid]
        for neighbor in systemInfo.neighbours:
            self.SchedulePrefetchForSystem(neighbor.solarSystemID)
