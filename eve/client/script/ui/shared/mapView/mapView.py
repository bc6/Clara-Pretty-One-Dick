#Embedded file name: eve/client/script/ui/shared/mapView\mapView.py
import sys
import math
import itertools
from collections import defaultdict
import cPickle
import logging
from carbon.common.script.sys.service import ROLE_GML
from carbonui.primitives.base import ScaleDpi
from carbonui.primitives.fill import Fill
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.infoIcon import InfoIcon
from eve.client.script.ui.control.pointerPanel import RefreshPanelPosition
from eve.client.script.ui.shared.mapView.dockPanelSubFrame import DockablePanelContentFrame, ContainerLockedRatio
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerMyHome import MarkerMyHome
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerMyLocation import MarkerMyLocation
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerSolarSystem import MarkerLabelSolarSystem
from eve.client.script.ui.shared.mapView.mapViewMarkersHandler import MapViewMarkersHandler
from eve.client.script.ui.shared.mapView.mapViewSceneContainer import MapViewSceneContainer
from eve.client.script.ui.shared.mapView.mapViewSettings import GetMapViewSetting, SetMapViewSetting
from eve.client.script.ui.shared.mapView.mapViewSolarSystem import MapViewSolarSystem
from eve.client.script.ui.shared.mapView.mapViewUtil import GetBoundingSphereRadiusCenter, GetTranslationFromParentWithRadius, SolarSystemPosToMapPos, WorldPosToMapPos, ScaledPosToMapPos, ScaleSolarSystemValue, IsDynamicMarkerType, IsLandmark
from eve.client.script.ui.shared.mapView.systemMapHandler import SystemMapHandler
from eve.common.script.sys.idCheckers import IsStation
from eve.common.script.util.eveFormat import FmtSystemSecStatus
import industry
import blue
from inventorycommon.util import IsWormholeSystem, IsWormholeRegion, IsWormholeConstellation
import trinity
import uthread
import fleetbr
import nodemanager
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.bracket import Bracket
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.shared.maps.hexMap import HexMapController
from eve.client.script.ui.shared.mapView.mapViewNavigation import MapViewNavigation
import eve.client.script.ui.shared.mapView.mapViewColorHandler as colorHandler
from eve.client.script.ui.shared.mapView.mapViewConst import VIEWMODE_COLOR_SETTINGS, VIEWMODE_GROUP_SETTINGS, VIEWMODE_GROUP_REGIONS, VIEWMODE_GROUP_CONSTELLATIONS, VIEWMODE_GROUP_DEFAULT, VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS, VIEWMODE_LINES_SETTINGS, VIEWMODE_LINES_DEFAULT, VIEWMODE_LINES_NONE, VIEWMODE_LINES_ALL, VIEWMODE_LINES_SELECTION_REGION_NEIGHBOURS, VIEWMODE_LINES_SELECTION_REGION, VIEWMODE_LAYOUT_SHOW_ABSTRACT_DEFAULT, VIEWMODE_COLOR_DEFAULT, VIEWMODE_LINES_SHOW_ALLIANCE_SETTINGS, VIEWMODE_LINES_SHOW_ALLIANCE_DEFAULT, MARKERID_MYPOS, MARKERID_BOOKMARK, MARKERID_SOLARSYSTEM_CELESTIAL, MARKERID_MYHOME, MARKER_POINT_TOP, VIEWMODE_MARKERS_SETTINGS, JUMPBRIDGE_COLOR, JUMPBRIDGE_CURVE_SCALE, VIEWMODE_FOCUS_SELF, MAPVIEW_OVERLAY_PADDING_FULLSCREEN, MAPVIEW_OVERLAY_PADDING_NONFULLSCREEN
import eve.client.script.ui.shared.maps.mapcommon as mapcommon
from eve.common.script.sys.eveCfg import IsSolarSystem, IsConstellation, IsRegion, GetActiveShip
import geo2
import carbonui.const as uiconst
import localization
from starmap.util import Pairwise, ScaleColour
from utillib import KeyVal
log = logging.getLogger(__name__)
SUNBASE = 50.0
LINE_EFFECT = 'res:/Graphics/Effect/Managed/Space/SpecialFX/Lines3DStarMapNew.fx'
PARTICLE_EFFECT = 'res:/Graphics/Effect/Managed/Space/SpecialFX/Particles/StarmapNew.fx'
PARTICLE_SPRITE_TEXTURE = 'res:/Texture/Particle/mapStarNew5.dds'
PARTICLE_SPRITE_HEAT_TEXTURE = 'res:/Texture/Particle/mapStarNewHeat.dds'
PARTICLE_SPRITE_DATA_TEXTURE = 'res:/Texture/Particle/mapStatData_Circle.dds'
LINE_BASE_WIDTH = 2.5
DISTANCE_RANGE = 'distanceRange'
NEUTRAL_COLOR = (0.33, 0.33, 0.33, 1.0)
HEX_TILE_SIZE = 60

class MapView(Container):
    __notifyevents__ = ['OnAvoidanceItemsChanged',
     'OnUIScalingChange',
     'OnAutopilotUpdated',
     'OnDestinationSet',
     'OnHomeStationChanged']
    curveSet = None
    starMapCache = None
    knownSolarSystems = None
    knownConstellations = None
    knownRegions = None
    mapJumps = None
    systemMap = None
    markersHandler = None
    markersAlwaysVisible = set()
    inFocus = False
    solarSystemStandalone = None
    isFullScreen = False
    currentSolarsystem = None
    hilightID = None
    _yScaleFactor = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.isFullScreen = attributes.isFullScreen
        self.Reset()
        self.mapSvc = sm.GetService('map')
        self.clientPathfinderService = sm.GetService('clientPathfinderService')
        self.infoLayer = Container(parent=self, clipChildren=True, name='infoLayer')
        self.mapNavigation = MapViewNavigation(parent=self, align=uiconst.TOALL, state=uiconst.UI_NORMAL, mapView=self)
        sceneContainer = MapViewSceneContainer(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        sceneContainer.Startup()
        self.sceneContainer = sceneContainer
        self.camera.SetCallback(self.OnCameraMoved)
        uthread.new(self.InitMap)
        sm.RegisterNotify(self)
        uthread.new(uicore.registry.SetFocus, self)

    def Close(self, *args, **kwds):
        sm.GetService('audio').SendUIEvent('map_stop_all')
        self.starMapCache = None
        self.knownSolarSystems = None
        self.knownConstellations = None
        self.knownRegions = None
        self.mapJumps = None
        if self.currentSolarsystem:
            self.currentSolarsystem.RemoveFromScene()
        self.currentSolarsystem = None
        if self.camera:
            self.camera.Close()
        self.camera = None
        if self.markersHandler:
            self.markersHandler.StopHandler()
        self.markersHandler = None
        self.mapNavigation = None
        self.Reset()
        Container.Close(self, *args, **kwds)

    def SetFocusState(self, focusState):
        self.inFocus = focusState

    def Reset(self):
        self.LogInfo('MapViewPanel Reset')
        self.destinationPath = [None]
        self.currentSolarsystem = None
        self.activeItemID = None
        self.mapMode = VIEWMODE_GROUP_DEFAULT
        self.lineMode = VIEWMODE_LINES_DEFAULT
        if hasattr(self, 'mapRoot') and self.mapRoot is not None:
            del self.mapRoot.children[:]
        self.mapRoot = None
        if hasattr(self, 'hexMap') and self.hexMap is not None:
            self.hexMap.tilePool = []
            self.hexMap = None
        self.particleIDToSystemIDMap = None
        self.solarSystemIDToParticleID = None
        self.autoPilotRoute = None
        self.genericRoute = None
        self.abstractMode = False
        self.lineIdAndToSystemIdByFromSystemId = None
        self.allianceSolarSystems = {'s': {},
         'c': {}}
        self.mapStars = None
        self.starParticles = None
        self.solarSystemJumpLineSet = None
        self.starColorHandlers = None
        self.cursor = None
        self.overlayContentFrame = None
        self.starData = {}
        self.starColorByID = {}

    def LoadSearchResult(self, searchResult):
        if searchResult:
            self.SetActiveItem(searchResult[0].itemID, zoomToItem=True)

    def OnDockModeChanged(self, isFullScreen):
        self.isFullScreen = isFullScreen
        if self.overlayContentFrame and not self.overlayContentFrame.destroyed:
            if isFullScreen:
                self.overlayContentFrame.padding = MAPVIEW_OVERLAY_PADDING_FULLSCREEN
            else:
                self.overlayContentFrame.padding = MAPVIEW_OVERLAY_PADDING_NONFULLSCREEN

    def OnMapViewSettingChanged(self, settingKey, *args, **kwds):
        if self.solarSystemStandalone:
            self.solarSystemStandalone.OnMapViewSettingChanged(settingKey, *args, **kwds)
        if settingKey == VIEWMODE_FOCUS_SELF:
            myPosMarkerID = (MARKERID_MYPOS, session.charid)
            markerObject = self.markersHandler.GetMarkerByID(myPosMarkerID)
            if IsWormholeSystem(session.solarsystemid2):
                if self.solarSystemStandalone and not self.solarSystemStandalone.destroyed:
                    self.CloseOverlayContainer()
                else:
                    overlayContainer = Container(parent=self, state=uiconst.UI_NORMAL, idx=0)
                    fadeFill = Fill(bgParent=overlayContainer, color=(0, 0, 0, 0))
                    uicore.animations.FadeTo(fadeFill, startVal=0.0, endVal=0.75, duration=1.0)
                    self.overlayContainer = overlayContainer
                    if self.isFullScreen:
                        padding = MAPVIEW_OVERLAY_PADDING_FULLSCREEN
                        self.sceneContainer.renderJob.enabled = False
                    else:
                        padding = MAPVIEW_OVERLAY_PADDING_NONFULLSCREEN
                        self.sceneContainer.renderJob.enabled = True
                    contentFrame = DockablePanelContentFrame(parent=overlayContainer, padding=padding)
                    self.solarSystemStandalone = MapViewSolarSystem(parent=contentFrame.content, showCloseButton=True, showInfobox=True, closeFunction=self.CloseOverlayContainer)
                    contentFrame.AnimateContentIn(animationOffset=0.1)
                    self.solarSystemStandalone.LoadSolarSystemDetails(session.solarsystemid2)
                    self.solarSystemStandalone.FrameSolarSystem()
                    self.overlayContentFrame = contentFrame
            elif markerObject:
                self.SetActiveItem(myPosMarkerID, zoomToItem=True)
            else:
                self.SetActiveItem(session.solarsystemid2, zoomToItem=True)
            return
        if settingKey == VIEWMODE_MARKERS_SETTINGS:
            if self.currentSolarsystem:
                self.currentSolarsystem.LoadMarkers()
            return
        self.UpdateMapViewColorMode()
        if self.destroyed:
            return
        currentViewModeGroup = settings.user.ui.Get(VIEWMODE_GROUP_SETTINGS, VIEWMODE_GROUP_DEFAULT)
        if currentViewModeGroup != self.mapMode:
            if currentViewModeGroup == VIEWMODE_GROUP_REGIONS:
                self.RegionMode()
            elif currentViewModeGroup == VIEWMODE_GROUP_CONSTELLATIONS:
                self.ConstellationMode()
            elif currentViewModeGroup == VIEWMODE_GROUP_DEFAULT:
                self.SystemMode()
            if self.destroyed:
                return
        currentAbstract = settings.user.ui.Get(VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS, VIEWMODE_LAYOUT_SHOW_ABSTRACT_DEFAULT)
        if currentAbstract != self.abstractMode:
            self.LoadAbstractMode(currentAbstract)
        currentLineMode = settings.user.ui.Get(VIEWMODE_LINES_SETTINGS, VIEWMODE_LINES_DEFAULT)
        if currentLineMode != self.lineMode:
            self.UpdateLines(hint='OnMapViewSettingChanged')

    def CloseOverlayContainer(self, *args, **kwds):
        self.sceneContainer.renderJob.enabled = True
        self.overlayContainer.Close()
        self.solarSystemStandalone = None
        self.overlayContainer = None

    def InitMap(self):
        if self.destroyed:
            return
        self.LogInfo('MapSvc: InitStarMap')
        initMapText = localization.GetByLabel('UI/Map/StarMap/InitializingMap')
        gettingDataText = localization.GetByLabel('UI/Map/StarMap/GettingData')
        self.StartLoadingBar('starmap_init', initMapText, gettingDataText, 4)
        scene = trinity.EveSpaceScene()
        scene.starfield = trinity.Load('res:/dx9/scene/starfield/spritestars.red')
        scene.backgroundEffect = trinity.Load('res:/dx9/scene/starfield/starfieldNebula.red')
        scene.backgroundRenderingEnabled = True
        node = nodemanager.FindNode(scene.backgroundEffect.resources, 'NebulaMap', 'trinity.TriTexture2DParameter')
        if node is not None:
            node.resourcePath = 'res:/UI/Texture/classes/MapView/backdrop_cube.dds'
        self.mapRoot = trinity.EveRootTransform()
        self.mapRoot.name = 'universe'
        scene.objects.append(self.mapRoot)
        self.sceneContainer.scene = scene
        self.sceneContainer.DisplaySpaceScene()
        self.markersHandler = MapViewMarkersHandler(self, self.sceneContainer.bracketCurveSet, self.infoLayer, eventHandler=self.mapNavigation)
        self.UpdateLoadingBar('starmap_init', initMapText, gettingDataText, 1, 4)
        self.CreateJumpLineSet(scene)
        self.CreateHexmap()
        self.UpdateLoadingBar('starmap_init', initMapText, gettingDataText, 2, 4)
        addMarkers = True
        self.DrawStars(loadSolarsystemMarkers=addMarkers)
        self.CreateSystemJumpLines()
        self.CreateAllianceJumpLines()
        if addMarkers:
            self.LoadRegionMarkers()
            self.LoadConstellationMarkers()
            self.LoadLandmarkMarkers()
        if self.destroyed:
            return
        self.starLegend = []
        self.tileLegend = []
        self.RegisterStarColorModes()
        self.UpdateLoadingBar('starmap_init', initMapText, gettingDataText, 3, 4)
        self.OnMapViewSettingChanged(None)
        if self.destroyed:
            return
        self.SetActiveItem(session.solarsystemid2, zoomToItem=True, hint='InitMap')
        if self.destroyed:
            return
        uthread.new(self.ShowMyLocation)
        uthread.new(self.ShowMyHomeStation)
        self.OnCameraMoved()
        self.StopLoadingBar('starmap_init')

    @apply
    def yScaleFactor():
        """
        Flatted effect of the map, here we delegate the factor
        to all components which need it
        """

        def fget(self):
            return self._yScaleFactor

        def fset(self, value):
            self._yScaleFactor = value
            self.mapRoot.scaling = self.solarSystemJumpLineSet.scaling = (1.0, value, 1.0)
            if self.markersHandler:
                self.markersHandler.yScaleFactor = value
            if self.currentSolarsystem:
                self.currentSolarsystem.yScaleFactor = value
            if self.camera:
                self.camera.yScaleFactor = value

        return property(**locals())

    @apply
    def camera():

        def fget(self):
            if self.sceneContainer:
                return self.sceneContainer.camera

        def fset(self, value):
            pass

        return property(**locals())

    @apply
    def scene():

        def fget(self):
            return self.sceneContainer.scene

        return property(**locals())

    def LogError(self, *args, **kwds):
        log.error('MAPVIEW ' + repr(args))

    def LogInfo(self, *args, **kwds):
        log.info('MAPVIEW ' + repr(args))

    def LogWarn(self, *args, **kwds):
        log.warning('MAPVIEW ' + repr(args))

    def OnAvoidanceItemsChanged(self):
        colorMode = settings.user.ui.Get(VIEWMODE_COLOR_SETTINGS, VIEWMODE_COLOR_DEFAULT)
        if colorMode == mapcommon.STARMODE_AVOIDANCE:
            self.UpdateMapViewColorMode()

    def OnUIScalingChange(self, *args):
        self.markersHandler.ReloadAll()

    def GetPickObjects(self, mouseX, mouseY, getMarkers = True):
        if not self.markersHandler:
            return
        x, y = ScaleDpi(mouseX), ScaleDpi(mouseY)
        vx, vy = self.sceneContainer.viewport.x, self.sceneContainer.viewport.y
        lastDistance = None
        picked = []
        for markerID, marker in self.markersHandler.projectBrackets.iteritems():
            if not marker.projectBracket.isInFront or not marker.positionPickable:
                continue
            mx, my = marker.projectBracket.rawProjectedPosition
            if x - 7 < vx + mx < x + 8 and y - 7 < vy + my < y + 8:
                distance = marker.projectBracket.cameraDistance
                if lastDistance is None or distance < lastDistance:
                    if getMarkers:
                        picked = [(markerID, marker)]
                    else:
                        picked = [markerID]
                    lastDistance = distance

        return picked

    def GetItemMenu(self, itemID):
        item = self.mapSvc.GetItem(itemID, retall=True)
        if not item:
            return []
        m = []
        mm = []
        universeID, regionID, constellationID, solarSystemID, celestialID = self.mapSvc.GetParentLocationID(item.itemID)
        if solarSystemID:
            mm.append((MenuLabel('UI/Common/LocationTypes/System'), self.ViewInSovDashboard, (solarSystemID, constellationID, regionID)))
        if constellationID:
            mm.append((MenuLabel('UI/Common/LocationTypes/Constellation'), self.ViewInSovDashboard, (None, constellationID, regionID)))
        mm.append((MenuLabel('UI/Common/LocationTypes/Region'), self.ViewInSovDashboard, (None, None, regionID)))
        m.append((MenuLabel('UI/Sovereignty/ViewInSovDashboard'), mm))
        m.append(None)
        filterFunc = [MenuLabel('UI/Commands/ShowLocationOnMap')]
        m += sm.GetService('menu').CelestialMenu(itemID, noTrace=1, mapItem=item, filterFunc=filterFunc)
        return m

    def ViewInSovDashboard(self, systemID, constellationID, regionID):
        location = (systemID, constellationID, regionID)
        sm.GetService('sov').GetSovOverview(location)

    def MakeBroadcastBracket(self, gbType, itemID, charID):
        if gbType != 'TravelTo':
            raise NotImplementedError
        if self.mapRoot is None:
            return
        sysname = cfg.evelocations.Get(itemID).name.encode('utf-8')
        tracker = trinity.EveTransform()
        tracker.name = '__fleetbroadcast_%s' % sysname
        self.mapRoot.children.append(tracker)
        loc = self.mapSvc.GetItem(itemID)
        pos = (loc.x * mapcommon.STARMAP_SCALE, loc.y * mapcommon.STARMAP_SCALE, loc.z * mapcommon.STARMAP_SCALE)
        tracker.translation = pos
        anchor = Bracket(parent=uicore.layer.starmap, state=uiconst.UI_DISABLED, width=1, height=1, align=uiconst.NOALIGN, name='fleetBroadcastAnchor_%s' % sysname)
        anchor.itemID = itemID
        anchor.display = True
        anchor.trackTransform = tracker
        iconPath = fleetbr.types['TravelTo']['bigIcon']
        icon = Icon(icon=iconPath, parent=anchor, idx=0, pos=(0, 0, 32, 32), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        icon.name = 'fleetBroadcastIcon_%s' % sysname
        icon.hint = fleetbr.GetCaption_TravelTo(charID, itemID, itemID)
        icon.GetMenu = fleetbr.MenuGetter('TravelTo', charID, itemID)

        def Cleanup(*args):
            try:
                self.mapRoot.children.fremove(tracker)
            except (AttributeError, ValueError):
                sys.exc_clear()

        icon.OnClose = Cleanup
        return anchor

    def GetCloudNumFromItemID(self, itemID):
        if itemID in self.solarSystemIDToParticleID:
            return self.solarSystemIDToParticleID[itemID]

    def GetItemIDFromParticleID(self, particleID):
        """
        Transforms particleID to solarSystemID
        
        return solarSystemID for particle or None if not present
        """
        solarSystemID = None
        if self.particleIDToSystemIDMap:
            solarSystemID = self.particleIDToSystemIDMap[particleID]
        return solarSystemID

    def RemoveChild(self, tf, childname):
        for each in tf.children[:]:
            if each.name == childname:
                tf.children.remove(each)

    def ShowJumpDriveRange(self):
        if getattr(self, 'mylocation', None):
            for each in self.mylocation.trackerTransform.children[:]:
                if each.name == 'jumpDriveRange':
                    self.mylocation.trackerTransform.children.remove(each)

        else:
            return
        if session.regionid > const.mapWormholeRegionMin:
            return
        shipID = GetActiveShip()
        if shipID is None:
            return
        dogmaLM = sm.GetService('clientDogmaIM').GetDogmaLocation()
        driveRange = dogmaLM.GetAttributeValue(shipID, const.attributeJumpDriveRange)
        if driveRange is None or driveRange == 0:
            return
        scale = 2.0 * driveRange * const.LIGHTYEAR * mapcommon.STARMAP_SCALE
        sphere = trinity.Load('res:/dx9/model/UI/JumpRangeBubble.red')
        sphere.scaling = (scale, scale, scale)
        sphere.name = 'jumpDriveRange'
        if self.abstractMode():
            sphere.display = False
        self.mylocation.trackerTransform.children.append(sphere)

    def ShowMyHomeStation(self):
        if self.destroyed:
            return
        markerID = (MARKERID_MYHOME, session.charid)
        self.markersHandler.RemoveMarker(markerID)
        try:
            self.markersAlwaysVisible.remove(markerID)
        except:
            pass

        homeStationID = sm.RemoteSvc('charMgr').GetHomeStation()
        if not homeStationID or self.destroyed:
            return
        stationInfo = self.mapSvc.GetStation(homeStationID)
        if IsWormholeRegion(stationInfo.regionID):
            return
        mapPosition = self.GetKnownSolarSystem(stationInfo.solarSystemID).scaledCenter
        localPosition = SolarSystemPosToMapPos((stationInfo.x, stationInfo.y, stationInfo.z))
        mapPosition = geo2.Vec3Add(mapPosition, localPosition)
        markerObject = self.markersHandler.AddMarker(markerID, mapPosition, MarkerMyHome, stationInfo=stationInfo, texturePath='res:/UI/Texture/classes/MapView/homeIcon.png', hintString='Home Station', distanceFadeAlpha=False)
        markerObject.SetSolarSystemID(stationInfo.solarSystemID)
        self.markersAlwaysVisible.add(markerID)
        self.UpdateMarkersGrouping()

    def ShowMyLocation(self):
        if self.destroyed:
            return
        if self.mapRoot is None:
            return
        markerID = (MARKERID_MYPOS, session.charid)
        self.markersHandler.RemoveMarker(markerID)
        try:
            self.markersAlwaysVisible.remove(markerID)
        except:
            pass

        if not IsWormholeRegion(session.regionid):
            mapPosition = self.GetKnownSolarSystem(session.solarsystemid2).scaledCenter
            if session.stationid:
                stationInfo = self.mapSvc.GetStation(session.stationid)
                if self.destroyed:
                    return
                localPosition = SolarSystemPosToMapPos((stationInfo.x, stationInfo.y, stationInfo.z))
                mapPosition = geo2.Vec3Add(mapPosition, localPosition)
                markerObject = self.markersHandler.AddMarker(markerID, mapPosition, MarkerMyLocation, solarSystemMapPosition=mapPosition, texturePath='res:/UI/Texture/classes/MapView/focusIcon.png', hintString=localization.GetByLabel('UI/Map/StarMap/lblYouAreHere'), distanceFadeAlpha=False)
            else:
                markerObject = self.markersHandler.AddMarker(markerID, mapPosition, MarkerMyLocation, trackObjectID=session.shipid or session.stationid, solarSystemMapPosition=mapPosition, texturePath='res:/UI/Texture/classes/MapView/focusIcon.png', hintString=localization.GetByLabel('UI/Map/StarMap/lblYouAreHere'), distanceFadeAlpha=False)
            markerObject.SetSolarSystemID(session.solarsystemid2)
            self.markersAlwaysVisible.add(markerID)
            self.UpdateMarkersGrouping()

    def IsFlat(self):
        return self.abstractMode

    def ToggleFlattenMode(self):
        """WMPC will get notified of the new state and refresh accordingly"""
        pass

    def UpdateMarkersGrouping(self):
        """Adjust markers location to the grouping of the map, so if marker is
        not in expanded constellation or region we put it at parent constellation
        or region location"""
        active = self.GetActiveObjectIDs()
        mapMode = self.mapMode
        for markerID in self.markersAlwaysVisible:
            markerObject = self.markersHandler.GetMarkerByID(markerID)
            if markerObject:
                markerSolarSystemID = markerObject.GetSolarSystemID()
                if markerSolarSystemID:
                    solarSystemItem = self.GetKnownSolarSystem(markerSolarSystemID)
                    if mapMode == VIEWMODE_GROUP_REGIONS and active.regionID != solarSystemItem.regionID:
                        regionItem = self.GetKnownRegion(solarSystemItem.regionID)
                        markerObject.SetPositionOverride(regionItem.scaledCenter)
                    elif mapMode == VIEWMODE_GROUP_CONSTELLATIONS and active.constellationID != solarSystemItem.constellationID:
                        constellationItem = self.GetKnownConstellation(solarSystemItem.constellationID)
                        markerObject.SetPositionOverride(constellationItem.scaledCenter)
                    else:
                        markerObject.SetPositionOverride(None)

    def GetParticlePositions(self, mapMode):
        active = self.GetActiveObjectIDs()
        particleSystem = self.starParticles
        particlePositions = []
        for regionID, regionItem in self.GetKnownUniverseRegions().iteritems():
            regionPosition = regionItem.scaledCenter
            for constellationID in regionItem.constellationIDs:
                constellationItem = self.GetKnownConstellation(constellationID)
                for solarsystemID in constellationItem.solarSystemIDs:
                    particleID = self.solarSystemIDToParticleID.get(solarsystemID, None)
                    if particleID:
                        if mapMode == VIEWMODE_GROUP_REGIONS:
                            if active.regionID == regionID:
                                solarSystemItem = self.GetKnownSolarSystem(solarsystemID)
                                toPosition = solarSystemItem.scaledCenter
                            else:
                                toPosition = regionPosition
                        elif mapMode == VIEWMODE_GROUP_CONSTELLATIONS:
                            if active.constellationID == constellationID:
                                solarSystemItem = self.GetKnownSolarSystem(solarsystemID)
                                toPosition = solarSystemItem.scaledCenter
                            else:
                                toPosition = constellationItem.scaledCenter
                        else:
                            solarSystemItem = self.GetKnownSolarSystem(solarsystemID)
                            toPosition = solarSystemItem.scaledCenter
                        fromPos = particleSystem.GetItemElement(particleID, 0)
                        if not geo2.Vec3Equal(fromPos, toPosition):
                            particlePositions.append((particleID, fromPos, toPosition))

        return particlePositions

    def MorphToMapMode(self, mapMode):
        particleSystem = self.starParticles
        lineSet = self.solarSystemJumpLineSet
        active = self.GetActiveObjectIDs()
        particlePositions = self.GetParticlePositions(mapMode)
        for particleID, oldPosition, newPosition in particlePositions:
            particleSystem.SetItemElement(particleID, 0, oldPosition)
            particleSystem.SetItemElement(particleID, 1, newPosition)

        particleSystem.UpdateData()
        self.UpdateMarkersGrouping()
        self.UpdateMarkersFilter()
        start, ndt = blue.os.GetWallclockTime(), 0.0
        duration = 500.0
        vs = trinity.GetVariableStore()
        linePositions = []
        for lineID, lineData in self.jumpLineInfoByLineID.iteritems():
            fromPosition, toPosition = self.GetJumpLinePositions(lineData, active)
            arePositionsEqual = geo2.Vec3Equal(fromPosition, lineData.currentFromPosition) and geo2.Vec3Equal(toPosition, lineData.currentToPosition)
            if not arePositionsEqual:
                linePositions.append((lineID,
                 fromPosition,
                 toPosition,
                 lineData))

        while ndt != 1.0:
            ndt = min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / duration, 1.0)
            vs.RegisterVariable('StarmapMorphValue', ndt)

            def morph(entry):
                lineID, fromPosition, toPosition, lineData = entry
                fromPosition = geo2.Vec3Lerp(lineData.currentFromPosition, fromPosition, ndt)
                toPosition = geo2.Vec3Lerp(lineData.currentToPosition, toPosition, ndt)
                lineSet.ChangeLinePositionCrt(lineID, fromPosition, toPosition)

            map(morph, linePositions)
            lineSet.SubmitChanges()
            blue.pyos.synchro.Yield()
            if self.destroyed:
                return

        for lineID, fromPosition, toPosition, lineData in linePositions:
            self.ChangeJumpLinePosition(lineID, fromPosition, toPosition)

        if self.currentSolarsystem:
            self.AdjustJumplinesToStargates(self.currentSolarsystem.solarsystemID)
        for particleID, oldPosition, newPosition in particlePositions:
            particleSystem.SetItemElement(particleID, 0, newPosition)

        particleSystem.UpdateData()
        vs.RegisterVariable('StarmapMorphValue', 0.0)
        self.UpdateLines(hint='MorphToMapMode')

    def GetJumpLinePositions(self, lineData, activeState = None):
        """Return from/to postion of a line based on the star-group
        setting of the map"""
        if activeState is None:
            activeState = self.GetActiveObjectIDs()
        mapMode = self.mapMode
        if mapMode == VIEWMODE_GROUP_REGIONS:
            if lineData.fromRegionID == activeState.regionID:
                fromPosition = lineData.fromSolarSystemScaledPosition
            else:
                fromPosition = lineData.fromRegionScaledPosition
            if lineData.toRegionID == activeState.regionID:
                toPosition = lineData.toSolarSystemScaledPosition
            else:
                toPosition = lineData.toRegionScaledPosition
        elif mapMode == VIEWMODE_GROUP_CONSTELLATIONS:
            if lineData.fromConstellationID == activeState.constellationID:
                fromPosition = lineData.fromSolarSystemScaledPosition
            else:
                fromPosition = lineData.fromConstellationScaledPosition
            if lineData.toConstellationID == activeState.constellationID:
                toPosition = lineData.toSolarSystemScaledPosition
            else:
                toPosition = lineData.toConstellationScaledPosition
        else:
            fromPosition = lineData.fromSolarSystemScaledPosition
            toPosition = lineData.toSolarSystemScaledPosition
        return (fromPosition, toPosition)

    def GetActiveObjectIDs(self):
        activeObjects = Bunch()
        if IsSolarSystem(self.activeItemID):
            if not IsWormholeSystem(self.activeItemID):
                solarSystemData = self.GetKnownSolarSystem(self.activeItemID)
                activeObjects.solarSystemID = self.activeItemID
                activeObjects.constellationID = solarSystemData.constellationID
                activeObjects.regionID = solarSystemData.regionID
        elif IsConstellation(self.activeItemID):
            if not IsWormholeConstellation(self.activeItemID):
                constellationData = self.GetKnownConstellation(self.activeItemID)
                activeObjects.constellationID = self.activeItemID
                activeObjects.regionID = constellationData.regionID
        elif IsRegion(self.activeItemID):
            if not IsWormholeRegion(self.activeItemID):
                activeObjects.regionID = self.activeItemID
        return activeObjects

    def UpdateMarkersFilter(self):
        active = self.GetActiveObjectIDs()
        if self.mapMode == VIEWMODE_GROUP_REGIONS:
            filterMarkers = self.GetKnownUniverseRegions().keys()
            if active.regionID:
                regionData = self.GetKnownRegion(active.regionID)
                filterMarkers += regionData.constellationIDs
                filterMarkers += regionData.solarSystemIDs
        elif self.mapMode == VIEWMODE_GROUP_CONSTELLATIONS:
            filterMarkers = self.GetKnownUniverseRegions().keys()
            filterMarkers += self.GetKnownUniverseConstellations().keys()
            if active.constellationID:
                constellationData = self.GetKnownConstellation(active.constellationID)
                filterMarkers += constellationData.solarSystemIDs
        else:
            filterMarkers = None
        if filterMarkers:
            filterMarkers += list(self.markersAlwaysVisible)
        self.markersHandler.SetDisplayStateOverrideFilter(filterMarkers)

    def RegionMode(self, *args):
        self.mapMode = VIEWMODE_GROUP_REGIONS
        self.MorphToMapMode(VIEWMODE_GROUP_REGIONS)

    def ConstellationMode(self, *args):
        self.mapMode = VIEWMODE_GROUP_CONSTELLATIONS
        self.MorphToMapMode(VIEWMODE_GROUP_CONSTELLATIONS)

    def SystemMode(self, *args):
        self.mapMode = VIEWMODE_GROUP_DEFAULT
        self.MorphToMapMode(VIEWMODE_GROUP_DEFAULT)

    def LoadAbstractMode(self, modeState):
        self.abstractMode = modeState
        if self.abstractMode == True:
            uicore.animations.MorphScalar(self, 'yScaleFactor', startVal=self.yScaleFactor, endVal=0.0001, duration=1.0)
            self.camera.SetYawPitch(-math.pi / 2, math.pi - 0.05)
            self.camera.ZoomToDistance(50000.0)
        else:
            uicore.animations.MorphScalar(self, 'yScaleFactor', startVal=self.yScaleFactor, endVal=1.0, duration=1.0)

    def DrawStars(self, loadSolarsystemMarkers = False):
        """
        Draw the solarsystem stars
        """
        self.mapStars = trinity.EveTransform()
        self.mapStars.name = '__mapStars'
        self.mapRoot.children.append(self.mapStars)
        tex = trinity.TriTexture2DParameter()
        tex.name = 'TexMap'
        tex.resourcePath = PARTICLE_SPRITE_TEXTURE
        heattex = trinity.TriTexture2DParameter()
        heattex.name = 'HeatTexture'
        heattex.resourcePath = PARTICLE_SPRITE_HEAT_TEXTURE
        self.starDataTexture = heattex
        distanceRangeStars = trinity.Tr2Vector4Parameter()
        distanceRangeStars.name = DISTANCE_RANGE
        distanceRangeStars.value = (0, 1, 0, 0)
        self.distanceRangeStars = distanceRangeStars
        self.starParticles = trinity.Tr2RuntimeInstanceData()
        self.starParticles.SetElementLayout([(trinity.PARTICLE_ELEMENT_TYPE.POSITION, 0, 3),
         (trinity.PARTICLE_ELEMENT_TYPE.POSITION, 1, 3),
         (trinity.PARTICLE_ELEMENT_TYPE.CUSTOM, 0, 1),
         (trinity.PARTICLE_ELEMENT_TYPE.CUSTOM, 1, 4)])
        mesh = trinity.Tr2InstancedMesh()
        mesh.geometryResPath = 'res:/Graphics/Generic/UnitPlane/UnitPlane.gr2'
        mesh.instanceGeometryResource = self.starParticles
        area = trinity.Tr2MeshArea()
        area.effect = trinity.Tr2Effect()
        area.effect.effectFilePath = PARTICLE_EFFECT
        area.effect.resources.append(tex)
        area.effect.resources.append(heattex)
        area.effect.parameters.append(distanceRangeStars)
        mesh.additiveAreas.append(area)
        self.mapStars.mesh = mesh
        distanceRangeLines = trinity.Tr2Vector4Parameter()
        distanceRangeLines.name = DISTANCE_RANGE
        distanceRangeLines.value = (0, 1, 0, 0)
        self.distanceRangeLines = distanceRangeLines
        self.solarSystemJumpLineSet.lineEffect.parameters.append(self.distanceRangeLines)
        self.particleIDToSystemIDMap = {}
        self.solarSystemIDToParticleID = {}
        particleCounter = itertools.count()
        starParticleData = []
        for systemID, system in self.GetKnownUniverseSolarSystems().iteritems():
            particleID = particleCounter.next()
            self.solarSystemIDToParticleID[systemID] = particleID
            self.particleIDToSystemIDMap[particleID] = systemID
            starParticleData.append((system.scaledCenter,
             (0.0, 0.0, 0.0),
             0.0,
             (0.0, 0.0, 0.0, 0.0)))
            if loadSolarsystemMarkers:
                self.markersHandler.AddStarMarker(systemID, system.scaledCenter)

        self.starParticles.SetData(starParticleData)
        self.starParticles.UpdateBoundingBox()
        vs = trinity.GetVariableStore()
        vs.RegisterVariable('StarmapMorphValue', 0.0)
        mesh.minBounds = self.starParticles.aabbMin
        mesh.maxBounds = self.starParticles.aabbMax

    def GetStarMapCache(self):
        if self.starMapCache is None:
            res = blue.ResFile()
            starMapResPath = 'res:/staticdata/starMapCache.pickle'
            if not res.open('%s' % starMapResPath):
                self.LogError('Could not load Starmap Cache data file: %s' % starMapResPath)
            else:
                try:
                    pickleData = res.Read()
                    self.starMapCache = cPickle.loads(pickleData)
                finally:
                    res.Close()

        return self.starMapCache

    def GetKnownUniverseSolarSystems(self):
        if self.knownSolarSystems is None:
            self.knownSolarSystems = {}
            for systemID, system in self.GetStarMapCache()['solarSystems'].iteritems():
                if IsWormholeSystem(systemID):
                    continue
                center = system['center']
                solarSystemInfo = Bunch()
                solarSystemInfo.center = center
                solarSystemInfo.scaledCenter = WorldPosToMapPos(center)
                solarSystemInfo.regionID = system['regionID']
                solarSystemInfo.constellationID = system['constellationID']
                solarSystemInfo.star = mapcommon.SUN_DATA[system['sunTypeID']]
                solarSystemInfo.factionID = system['factionID']
                solarSystemInfo.neighbours = system['neighbours']
                solarSystemInfo.planetCountByType = system['planetCountByType']
                self.knownSolarSystems[systemID] = solarSystemInfo

        return self.knownSolarSystems

    def GetKnownUniverseRegions(self):
        if self.knownRegions is None:
            self.knownRegions = {}
            for regionID, region in self.GetStarMapCache()['regions'].iteritems():
                if IsWormholeRegion(regionID):
                    continue
                regionInfo = Bunch()
                regionInfo.neighbours = region['neighbours']
                regionInfo.solarSystemIDs = region['solarSystemIDs']
                regionInfo.constellationIDs = region['constellationIDs']
                regionInfo.scaledCenter = WorldPosToMapPos(region['center'])
                self.knownRegions[regionID] = regionInfo

        return self.knownRegions

    def GetKnownUniverseConstellations(self):
        if self.knownConstellations is None:
            self.knownConstellations = {}
            for constellationID, constellation in self.GetStarMapCache()['constellations'].iteritems():
                if IsWormholeConstellation(constellationID):
                    continue
                constellationInfo = Bunch()
                constellationInfo.regionID = constellation['regionID']
                constellationInfo.neighbours = constellation['neighbours']
                constellationInfo.solarSystemIDs = constellation['solarSystemIDs']
                constellationInfo.scaledCenter = WorldPosToMapPos(constellation['center'])
                self.knownConstellations[constellationID] = constellationInfo

        return self.knownConstellations

    def IterateJumps(self):
        if self.mapJumps is None:
            self.mapJumps = []
            for jump in self.GetStarMapCache()['jumps']:
                fromSystemID = jump['fromSystemID']
                toSystemID = jump['toSystemID']
                jumpInfo = self.PrimeJumpData(fromSystemID, toSystemID, jump['jumpType'])
                self.mapJumps.append(jumpInfo)
                yield jumpInfo

        else:
            for jump in self.mapJumps:
                yield jump

    def PrimeJumpData(self, fromSolarSystemID, toSolarSystemID, jumpType):
        fromSystem = self.GetKnownSolarSystem(fromSolarSystemID)
        toSystem = self.GetKnownSolarSystem(toSolarSystemID)
        fromConstellation = self.GetKnownConstellation(fromSystem.constellationID)
        toConstellation = self.GetKnownConstellation(toSystem.constellationID)
        fromRegion = self.GetKnownRegion(fromSystem.regionID)
        toRegion = self.GetKnownRegion(toSystem.regionID)
        jumpInfo = KeyVal()
        jumpInfo.jumpType = jumpType
        jumpInfo.fromSolarSystemID = fromSolarSystemID
        jumpInfo.toSolarSystemID = toSolarSystemID
        jumpInfo.fromConstellationID = fromSystem.constellationID
        jumpInfo.toConstellationID = toSystem.constellationID
        jumpInfo.fromRegionID = fromSystem.regionID
        jumpInfo.toRegionID = toSystem.regionID
        jumpInfo.fromSolarSystemScaledPosition = fromSystem.scaledCenter
        jumpInfo.toSolarSystemScaledPosition = toSystem.scaledCenter
        jumpInfo.fromConstellationScaledPosition = fromConstellation.scaledCenter
        jumpInfo.toConstellationScaledPosition = toConstellation.scaledCenter
        jumpInfo.fromRegionScaledPosition = fromRegion.scaledCenter
        jumpInfo.toRegionScaledPosition = toRegion.scaledCenter
        jumpInfo.currentFromPosition = (0, 0, 0)
        jumpInfo.currentToPosition = (0, 0, 0)
        return jumpInfo

    def GetKnownSolarSystem(self, solarSystemID):
        return self.GetKnownUniverseSolarSystems()[solarSystemID]

    def GetKnownConstellation(self, constellationID):
        return self.GetKnownUniverseConstellations()[constellationID]

    def GetKnownRegion(self, regionID):
        return self.GetKnownUniverseRegions()[regionID]

    def CreateHexmap(self):
        hexMapRoot = trinity.EveTransform()
        hexMapRoot.name = '__hexMapRoot'
        hexMapRoot.translation = ScaledPosToMapPos((0.0, 20000.0, 0.0))
        self.hexMap = HexMapController(hexMapRoot, self.GetKnownUniverseSolarSystems().iteritems())
        self.mapRoot.children.append(hexMapRoot)

    def LoadSolarSystemTooltipPanel(self, tooltipPanel, *args):
        return
        tooltipPanel.LoadGeneric2ColumnTemplate()
        tooltipPanel.state = uiconst.UI_NORMAL
        mapSvc = sm.GetService('map')
        starmapSvc = sm.GetService('starmap')
        particleID = self.uicursor.particleID
        itemID = self.uicursor.solarsystemID
        mapData = mapSvc.GetItem(itemID)
        if mapData is None:
            return
        securityColor = mapSvc.GetSystemColor(itemID)
        typeID = None
        groupID = None
        if mapData:
            displayName = mapData.itemName
            typeID = mapData.typeID
            groupID = cfg.invtypes.Get(mapData.typeID).groupID
        if groupID is None:
            return
        tooltipPanel.AddLabelLarge(text=displayName, bold=True)
        tooltipPanel.AddCell(cellObject=InfoIcon(typeID=typeID, itemID=itemID, align=uiconst.TOPRIGHT, left=-3))
        tooltipPanel.state = uiconst.UI_NORMAL
        ss = mapSvc.GetSecurityStatus(itemID)
        if ss is not None:
            tooltipPanel.AddLabelMedium(text=localization.GetByLabel('Tooltips/Map/SecurityStatus'))
            tooltipPanel.AddLabelMedium(text=ss, align=uiconst.CENTERRIGHT, color=(securityColor.r,
             securityColor.g,
             securityColor.b,
             1.0), cellPadding=(10, 0, 0, 0))
        data = starmapSvc.GetStarData()
        if particleID in data:
            hintFunc, hintArgs = data[particleID]
            particleHint = hintFunc(*hintArgs)
            if particleHint:
                tooltipPanel.AddCell(Line(align=uiconst.TOTOP, color=(1, 1, 1, 0.2)), colSpan=tooltipPanel.columns, cellPadding=(-11, 3, -11, 3))
                starColorModeLabel = GetActiveStarColorModeLabel()
                if starColorModeLabel:
                    tooltipPanel.AddLabelMedium(text=starColorModeLabel, bold=True, colSpan=tooltipPanel.columns)
                if isinstance(particleHint, (list, tuple)):
                    for each in particleHint:
                        tooltipPanel.AddLabelSmall(text=each, state=uiconst.UI_NORMAL, colSpan=tooltipPanel.columns)

                else:
                    tooltipPanel.AddLabelSmall(text=particleHint, state=uiconst.UI_NORMAL, colSpan=tooltipPanel.columns)
        uthread.new(self.UpdateTooltipPosition, tooltipPanel)

    def UpdateTooltipPosition(self, tooltipPanel):
        while not tooltipPanel.destroyed:
            RefreshPanelPosition(tooltipPanel)
            blue.synchro.Yield()

    def CreateJumpLineSet(self, scene):
        lineSet = trinity.EveCurveLineSet()
        lineSet.lineEffect.effectFilePath = LINE_EFFECT
        lineSet.name = 'JumpLines'
        tex2D = trinity.TriTexture2DParameter()
        tex2D.name = 'TexMap'
        tex2D.resourcePath = 'res:/UI/Texture/classes/MapView/lineSegment.dds'
        lineSet.lineEffect.resources.append(tex2D)
        overlayTex2D = trinity.TriTexture2DParameter()
        overlayTex2D.name = 'OverlayTexMap'
        overlayTex2D.resourcePath = 'res:/UI/Texture/classes/MapView/lineSegmentConstellation.dds'
        lineSet.lineEffect.resources.append(overlayTex2D)
        self.solarSystemJumpLineSet = lineSet
        transform = trinity.EveTransform()
        transform.children.append(lineSet)
        scene.objects.append(transform)

    def OnCameraMoved(self):
        self._OnCameraMoved()

    def _OnCameraMoved(self):
        """
        Callback from the camera whenever the viewpoint changes, recompute the distance to the nearest
        and furthest star, so we can fade out the stars in the back; similar to applying (black) fog, but
        we don't want everything to disappear when the camera zooms out.
        """
        camera = self.camera
        if camera is None:
            return
        if not self.starParticles:
            return
        if self.camera.translationFromParent < 10000:
            if self.inFocus:
                self.ChangeAmbientAudioLoop('map_system_loop_play')
            else:
                self.ChangeAmbientAudioLoop('map_system_loop_window_play')
        elif self.camera.translationFromParent < 50000:
            if self.inFocus:
                self.ChangeAmbientAudioLoop('map_constellation_loop_play')
            else:
                self.ChangeAmbientAudioLoop('map_constellation_loop_window_play')
        elif self.inFocus:
            self.ChangeAmbientAudioLoop('map_region_loop_play')
        else:
            self.ChangeAmbientAudioLoop('map_region_loop_window_play')
        rangeFromParent = 1000000
        self.distanceRangeStars.value = (self.camera.translationFromParent,
         self.camera.translationFromParent + rangeFromParent,
         0,
         0)
        self.distanceRangeLines.value = (self.camera.translationFromParent,
         self.camera.translationFromParent + rangeFromParent,
         0,
         0)
        if self.markersHandler:
            self.markersHandler.RegisterCameraTranslationFromParent(self.camera.translationFromParent)

    def ChangeAmbientAudioLoop(self, audioPath):
        if getattr(self, 'ambientAudioPath', None) != audioPath:
            self.ambientAudioPath = audioPath
            sm.GetService('audio').SendUIEvent('map_stop_all')
            sm.GetService('audio').SendUIEvent(audioPath)

    def GetStarData(self):
        """used by starmap navigation layer"""
        return getattr(self, 'starData', {})

    def GetDistance(self, fromVector, toVector):
        return geo2.Vec3Length(geo2.Vec3Subtract(fromVector, toVector))

    def GetExtraMouseOverInfoForItemID(self, itemID):
        particleID = self.solarSystemIDToParticleID.get(itemID, None)
        if particleID in self.starData:
            hintFunc, hintArgs = self.starData[particleID]
            particleHint = hintFunc(*hintArgs)
            return particleHint

    def SetHilightItem(self, itemID):
        hilightID = itemID
        if self.hilightID != hilightID:
            self.hilightID = hilightID
            self.UpdateLines(hint='HilightMarkers')
            if hilightID:
                self.markersHandler.HilightMarkers([hilightID])
            else:
                self.markersHandler.HilightMarkers([])

    def SetActiveItem(self, itemID, updateCamera = True, zoomToItem = False, *args, **kwds):
        if self.activeItemID == itemID:
            return
        if IsWormholeSystem(itemID):
            return
        if IsWormholeConstellation(itemID):
            return
        if IsWormholeRegion(itemID):
            return
        if IsStation(itemID):
            stationData = cfg.stations.Get(itemID)
            markerGroups = GetMapViewSetting(VIEWMODE_MARKERS_SETTINGS)
            if const.groupStation not in markerGroups:
                markerGroups.append(const.groupStation)
                SetMapViewSetting(VIEWMODE_MARKERS_SETTINGS, markerGroups)
            self.SetActiveItem(stationData.solarSystemID, updateCamera=False)
            itemID = (MARKERID_SOLARSYSTEM_CELESTIAL, itemID)
        markerPosition = None
        if IsDynamicMarkerType(itemID):
            markerObject = self.markersHandler.GetMarkerByID(itemID)
            if markerObject:
                markerPosition = markerObject.scaledCenter
                markerSolarSystemID = markerObject.GetSolarSystemID()
                if markerSolarSystemID is not None:
                    itemID = markerSolarSystemID
            else:
                return
        currentActive = self.GetActiveObjectIDs()
        if self.mapMode == VIEWMODE_GROUP_REGIONS and currentActive.regionID:
            activeRegionItem = self.GetKnownRegion(currentActive.regionID)
            if IsSolarSystem(itemID):
                if itemID not in activeRegionItem.solarSystemIDs:
                    mapInfo = self.GetKnownSolarSystem(itemID)
                    self.SetActiveItem(mapInfo.regionID, updateCamera=False)
            elif IsConstellation(itemID):
                if itemID not in activeRegionItem.constellationIDs:
                    mapInfo = self.GetKnownConstellation(itemID)
                    self.SetActiveItem(mapInfo.constellationID, updateCamera=False)
        elif self.mapMode == VIEWMODE_GROUP_CONSTELLATIONS and currentActive.constellationID:
            activeConstellationItem = self.GetKnownConstellation(currentActive.constellationID)
            if IsSolarSystem(itemID):
                if itemID not in activeConstellationItem.solarSystemIDs:
                    mapInfo = self.GetKnownSolarSystem(itemID)
                    self.SetActiveItem(mapInfo.constellationID, updateCamera=False)
        cameraPointOfInterest = None
        cameraDistanceFromInterest = None
        minCameraDistanceFromInterest = None
        self.activeItemID = itemID
        activeMarkers = []
        if IsSolarSystem(itemID):
            mapInfo = self.GetKnownSolarSystem(itemID)
            cameraPointOfInterest = mapInfo.scaledCenter
            self.LoadSolarSystemDetails(itemID)
            radius = ScaleSolarSystemValue(self.currentSolarsystem.solarSystemRadius)
            cameraDistanceFromInterest = GetTranslationFromParentWithRadius(radius, self.camera)
            minCameraDistanceFromInterest = 2.5
            sm.GetService('audio').SendUIEvent('map_system_zoom_play')
            activeMarkers.append(itemID)
        elif IsConstellation(itemID):
            mapInfo = self.GetKnownConstellation(itemID)
            cameraPointOfInterest = mapInfo.scaledCenter
            self.CloseCurrentSolarSystemIfAny()
            if self.mapMode == VIEWMODE_GROUP_CONSTELLATIONS and itemID != currentActive.constellationID:
                uthread.new(self.MorphToMapMode, VIEWMODE_GROUP_CONSTELLATIONS)
            positions = [ self.GetKnownSolarSystem(solarSystemID).scaledCenter for solarSystemID in mapInfo.solarSystemIDs ]
            boundingSphere, radius = GetBoundingSphereRadiusCenter(positions, self.abstractMode)
            minCameraDistanceFromInterest = GetTranslationFromParentWithRadius(radius, self.camera) * 0.5
            sm.GetService('audio').SendUIEvent('map_constellation_zoom_play')
        elif IsRegion(itemID):
            mapInfo = self.GetKnownRegion(itemID)
            cameraPointOfInterest = mapInfo.scaledCenter
            self.CloseCurrentSolarSystemIfAny()
            if self.mapMode == VIEWMODE_GROUP_REGIONS and itemID != currentActive.regionID:
                uthread.new(self.MorphToMapMode, VIEWMODE_GROUP_REGIONS)
            positions = [ self.GetKnownSolarSystem(solarSystemID).scaledCenter for solarSystemID in mapInfo.solarSystemIDs ]
            boundingSphere, radius = GetBoundingSphereRadiusCenter(positions, self.abstractMode)
            minCameraDistanceFromInterest = GetTranslationFromParentWithRadius(radius, self.camera) * 0.25
            sm.GetService('audio').SendUIEvent('map_region_zoom_play')
        elif IsLandmark(itemID):
            lm = self.mapSvc.GetLandmark(itemID * -1)
            cameraPointOfInterest = WorldPosToMapPos(lm.position)
        else:
            print 'Unsupported type for active state in map', itemID
            return
        self.markersHandler.ActivateMarkers(activeMarkers)
        self.UpdateMarkersFilter()
        self.UpdateLines(hint='SetActiveItem')
        if updateCamera:
            if minCameraDistanceFromInterest:
                self.camera.SetMinTranslationFromParent(minCameraDistanceFromInterest)
            if zoomToItem and cameraDistanceFromInterest:
                self.camera.ZoomToDistance(cameraDistanceFromInterest)
            if cameraPointOfInterest or markerPosition:
                self.camera.pointOfInterest = markerPosition or cameraPointOfInterest

    def SetInterest(self, itemID = None, forceframe = None, forcezoom = None, objectTransform = None, parentSolarsystemID = None):
        self.SetActiveItem(itemID, zoomToItem=forcezoom, hint='SetInterest')

    def CloseCurrentSolarSystemIfAny(self):
        if self.currentSolarsystem:
            self.currentSolarsystem.Close()
        self.currentSolarsystem = None

    def LoadSolarSystemDetails(self, solarSystemID):
        current = self.currentSolarsystem
        if current:
            resetSolarsystemID = current.solarsystemID
        else:
            resetSolarsystemID = None
        if resetSolarsystemID != solarSystemID:
            if current:
                current.Close()
            self.currentSolarsystem = None
            self.currentSolarsystem = SystemMapHandler(solarSystemID, self.scene, scaling=mapcommon.STARMAP_SCALE * 100, markersHandler=self.markersHandler)
            self.currentSolarsystem.LoadSolarSystemMap()
            if self.destroyed:
                return
            try:
                system = self.GetKnownSolarSystem(solarSystemID)
                scaledCenter = system.scaledCenter
            except KeyError:
                scaledCenter = (50000.0, 10000.0, 0.0)

            self.currentSolarsystem.SetPosition(scaledCenter)
            self.currentSolarsystem.yScaleFactor = self.yScaleFactor
            self.currentSolarsystem.LoadMarkers()
            if self.destroyed:
                return
            cameraParentTravel = self.GetDistance(self.camera.pointOfInterest, scaledCenter)
            uicore.animations.MorphVector3(self.currentSolarsystem.systemMapTransform, 'scaling', (0.0, 0.0, 0.0), (mapcommon.STARMAP_SCALE * 100, mapcommon.STARMAP_SCALE * 100 * self.yScaleFactor, mapcommon.STARMAP_SCALE * 100), duration=min(1500.0, cameraParentTravel) / 2000.0)
            self.AdjustJumplinesToStargates(solarSystemID, resetSolarsystemID)

    def ChangeJumpLinePosition(self, lineID, fromPosition, toPosition):
        lineData = self.jumpLineInfoByLineID.get(lineID, None)
        if lineData:
            lineData.currentFromPosition = fromPosition
            lineData.currentToPosition = toPosition
        self.solarSystemJumpLineSet.ChangeLinePositionCrt(lineID, fromPosition, toPosition)

    def AdjustJumplinesToStargates(self, solarsystemID = None, resetSolarsystemID = None):
        if resetSolarsystemID:
            for lineID, toSolarsystemID, isFrom in self.lineIdAndToSystemIdByFromSystemId[resetSolarsystemID]:
                jumpInfo = self.jumpLineInfoByLineID[lineID]
                self.ChangeJumpLinePosition(lineID, jumpInfo.fromSolarSystemScaledPosition, jumpInfo.toSolarSystemScaledPosition)

        if not solarsystemID or solarsystemID not in self.lineIdAndToSystemIdByFromSystemId:
            return
        fromSystemInfo = cfg.mapSolarSystemContentCache[solarsystemID]
        for lineID, toSolarsystemID, isFrom in self.lineIdAndToSystemIdByFromSystemId[solarsystemID]:
            jumpInfo = self.jumpLineInfoByLineID[lineID]
            toSystemInfo = cfg.mapSolarSystemContentCache[toSolarsystemID]
            fromStargateVector = None
            for each in fromSystemInfo.stargates:
                if fromSystemInfo.stargates[each].destination in toSystemInfo.stargates:
                    fromStargate = fromSystemInfo.stargates[each]
                    fromStargateVector = (fromStargate.position.x, fromStargate.position.y, fromStargate.position.z)
                    break

            if fromStargateVector:
                fromPosition, toPosition = self.GetJumpLinePositions(jumpInfo)
                stargateOffset = geo2.Vec3Scale(fromStargateVector, mapcommon.STARMAP_SCALE * 100)
                if isFrom:
                    self.ChangeJumpLinePosition(lineID, geo2.Vec3Add(jumpInfo.fromSolarSystemScaledPosition, stargateOffset), toPosition)
                else:
                    self.ChangeJumpLinePosition(lineID, fromPosition, geo2.Vec3Add(jumpInfo.toSolarSystemScaledPosition, stargateOffset))

        self.solarSystemJumpLineSet.SubmitChanges()

    def LoadBookmarkMarkers(self):
        uthread.new(self._LoadBookmarkMarkers)

    def _LoadBookmarkMarkers(self):
        bookmarkService = sm.GetService('bookmarkSvc')
        bookmarks = bookmarkService.GetBookmarks()
        for bookmark in bookmarks.itervalues():
            solarSystemID, worldPosition, localBookmarkPosition = bookmarkService.GetSolarSystemIDAndPositionForBookmark(bookmark.bookmarkID)
            if worldPosition is not None:
                worldPosition = WorldPosToMapPos(worldPosition)
            else:
                continue
            if localBookmarkPosition:
                scaledLocalPos = SolarSystemPosToMapPos(localBookmarkPosition)
                worldPosition = geo2.Vec3Add(worldPosition, scaledLocalPos)
            markerID = (MARKERID_BOOKMARK, bookmark.bookmarkID)
            markerObject = self.markersHandler.GetMarkerByID(markerID)
            if not markerObject:
                hint, comment = bookmarkService.UnzipMemo(bookmark.memo)
                markerObject = self.markersHandler.AddGenericIconMarker(markerID, worldPosition, texturePath='res:/UI/Texture/classes/MapView/pinIcon.png', hintString=hint)
                markerObject.SetSolarSystemID(solarSystemID)
                self.markersAlwaysVisible.add(markerID)
                markerObject.scaledCenter = worldPosition
            markerObject.SetPosition(worldPosition)

    def LoadLandmarkMarkers(self):
        for landmarkID, landmark in self.mapSvc.GetLandmarks().iteritems():
            markerObject = self.markersHandler.AddLandmarkMarker(-landmarkID, ScaledPosToMapPos(geo2.Vec3Scale(landmark.position, mapcommon.STARMAP_SCALE)))
            markerObject.SetLandmarkData(landmark)

    def LoadRegionMarkers(self):
        self.LogInfo('LoadRegionMarkers')
        for regionID, regionItem in self.GetKnownUniverseRegions().iteritems():
            if IsWormholeRegion(regionID):
                continue
            self.markersHandler.AddRegionMarker(regionID, regionItem.scaledCenter)

    def LoadConstellationMarkers(self):
        for constellationID, constellationItem in self.GetKnownUniverseConstellations().iteritems():
            if IsWormholeConstellation(constellationID):
                continue
            self.markersHandler.AddConstellationMarker(constellationID, constellationItem.scaledCenter)

    def GetAllFactions(self):
        return list(cfg.mapFactionsOwningSolarSystems)

    def GetAllianceSolarSystems(self):
        self.allianceSolarSystems = {}
        allianceSystemCache = sm.RemoteSvc('stationSvc').GetAllianceSystems()
        for x in allianceSystemCache:
            self.allianceSolarSystems[x.solarSystemID] = x.allianceID

        facwarSystems = sm.GetService('facwar').GetFacWarSystemsOccupiers()
        for systemID, occupierID in facwarSystems.iteritems():
            self.allianceSolarSystems[systemID] = occupierID

        return self.allianceSolarSystems

    def GetAllFactionsAndAlliances(self):
        """
        Should be used in preference to GetAllFactions
        """
        factions = self.GetAllFactions()
        alliances = self.GetAllianceSolarSystems().values()
        return list(set(factions + alliances))

    def GetFactionOrAllianceColor(self, entityID):
        if not hasattr(self, 'factionOrAllianceColors'):
            self.factionOrAllianceColors = {}
        if entityID not in self.factionOrAllianceColors:
            col = trinity.TriColor()
            hue = entityID * 12.345 * 3.0
            s = entityID % 2 * 0.5 + 0.5
            col.SetHSV(hue % 360.0, s, 1.0)
            self.factionOrAllianceColors[entityID] = col
        return self.factionOrAllianceColors[entityID]

    def GetLineIDForJumpBetweenSystems(self, fromSystemID, toSystemID):
        for lineID, _toSystemID, _isFrom in self.lineIdAndToSystemIdByFromSystemId[fromSystemID]:
            if _toSystemID == toSystemID:
                return lineID
        else:
            raise RuntimeError('Did not find a lineID for a jump between %s and %s', fromSystemID, toSystemID)

    def GetLineIDsForSystemID(self, sysID):
        return [ i[0] for i in self.lineIdAndToSystemIdByFromSystemId[sysID] ]

    def GetLineIDsForSystemList(self, solarSystemIDs):
        result = []
        for solarSystemID in solarSystemIDs:
            result.extend(self.GetLineIDsForSystemID(solarSystemID))

        return result

    def CreateSystemJumpLines(self):
        """
        Create solar system jump lines from cache
        """
        self.allianceJumpLines = []
        self.jumpLineInfoByLineID = {}
        self.lineIdAndToSystemIdByFromSystemId = defaultdict(list)
        lineSet = self.solarSystemJumpLineSet
        defaultColor = (0, 0, 0, 0)
        for jumpLineInfo in self.IterateJumps():
            lineID = lineSet.AddStraightLine(jumpLineInfo.fromSolarSystemScaledPosition, defaultColor, jumpLineInfo.toSolarSystemScaledPosition, defaultColor, LINE_BASE_WIDTH)
            jumpToSystemID = jumpLineInfo.toSolarSystemID
            jumpFromSystemID = jumpLineInfo.fromSolarSystemID
            jumpLineInfo.lineID = lineID
            self.jumpLineInfoByLineID[lineID] = jumpLineInfo
            self.lineIdAndToSystemIdByFromSystemId[jumpFromSystemID].append((lineID, jumpToSystemID, True))
            self.lineIdAndToSystemIdByFromSystemId[jumpToSystemID].append((lineID, jumpFromSystemID, False))
            jumpLineInfo.currentFromPosition = jumpLineInfo.fromSolarSystemScaledPosition
            jumpLineInfo.currentToPosition = jumpLineInfo.toSolarSystemScaledPosition

    def CreateAllianceJumpLines(self):
        """
        Create alliance jump lines from cache
        """
        if not hasattr(session, 'allianceid') or session.allianceid is None:
            return
        m = sm.RemoteSvc('map')
        bridgesByLocation = m.GetAllianceJumpBridges()
        jumpBridgeColor = JUMPBRIDGE_COLOR
        lineSet = self.solarSystemJumpLineSet
        for jumpFromSystemID, jumpToSystemID in bridgesByLocation:
            if not IsSolarSystem(jumpToSystemID) or not IsSolarSystem(jumpFromSystemID):
                self.LogWarn("DrawAllianceJumpLines had entry that wasn't a solarsystem:", jumpToSystemID, jumpFromSystemID)
                continue
            toSolarSystem = self.GetKnownSolarSystem(jumpToSystemID)
            toPos = toSolarSystem.scaledCenter
            fromSolarSystem = self.GetKnownSolarSystem(jumpFromSystemID)
            fromPos = fromSolarSystem.scaledCenter
            worldUp = geo2.Vector(0.0, -1.0, 0.0)
            linkVec = geo2.Vec3Subtract(toPos, fromPos)
            normLinkVec = geo2.Vec3Normalize(linkVec)
            rightVec = geo2.Vec3Cross(worldUp, normLinkVec)
            upVec = geo2.Vec3Cross(rightVec, normLinkVec)
            offsetVec = geo2.Vec3Scale(geo2.Vec3Normalize(upVec), geo2.Vec3Length(linkVec) * JUMPBRIDGE_CURVE_SCALE)
            midPos = geo2.Vec3Scale(geo2.Vec3Add(toPos, fromPos), 0.5)
            splinePos = geo2.Vec3Add(midPos, offsetVec)
            lineID = lineSet.AddCurvedLineCrt(toPos, jumpBridgeColor, fromPos, jumpBridgeColor, splinePos, 3)
            info = self.PrimeJumpData(jumpFromSystemID, jumpToSystemID, None)
            self.lineIdAndToSystemIdByFromSystemId[jumpFromSystemID].append((lineID, jumpToSystemID, True))
            self.lineIdAndToSystemIdByFromSystemId[jumpToSystemID].append((lineID, jumpFromSystemID, False))
            self.allianceJumpLines.append(lineID)
            self.jumpLineInfoByLineID[lineID] = info

    def UpdateLines(self, hint = '', **kwds):
        self.LogInfo('MapView UpdateLines ' + hint)
        lineMode = settings.user.ui.Get(VIEWMODE_LINES_SETTINGS, VIEWMODE_LINES_DEFAULT)
        self.lineMode = lineMode
        showAllianceLines = settings.user.ui.Get(VIEWMODE_LINES_SHOW_ALLIANCE_SETTINGS, VIEWMODE_LINES_SHOW_ALLIANCE_DEFAULT)
        active = self.GetActiveObjectIDs()
        maxAlpha = 0.9
        lineAlpha = {}
        if lineMode == VIEWMODE_LINES_NONE:
            baseLineAlphaModulate = 0.0
        else:
            hiliteID = self.hilightID
            if hiliteID is None:
                hiliteID = active.solarSystemID or active.constellationID or active.regionID
            if lineMode == VIEWMODE_LINES_ALL:
                baseLineAlphaModulate = maxAlpha * 0.25
            else:
                baseLineAlphaModulate = 0.0
                if active.regionID and lineMode in (VIEWMODE_LINES_SELECTION_REGION, VIEWMODE_LINES_SELECTION_REGION_NEIGHBOURS) and not IsWormholeRegion(active.regionID):
                    regionsToShow = [active.regionID]
                    if lineMode == VIEWMODE_LINES_SELECTION_REGION_NEIGHBOURS:
                        regionsToShow = regionsToShow + self.GetKnownRegion(active.regionID).neighbours
                    regionIDs = self.mapSvc.ExpandItems(regionsToShow)
                    lineIDs = self.GetLineIDsForSystemList(regionIDs)
                    for each in lineIDs:
                        lineAlpha[each] = maxAlpha / 2

            if IsSolarSystem(hiliteID) and not IsWormholeSystem(hiliteID):
                lineIDs = self.GetLineIDsForSystemID(hiliteID)
                for each in lineIDs:
                    lineAlpha[each] = maxAlpha

                hiliteItem = self.GetKnownSolarSystem(hiliteID)
                lineIDs = self.GetLineIDsForSystemList(hiliteItem.neighbours)
                for each in lineIDs:
                    lineAlpha[each] = maxAlpha

            elif IsConstellation(hiliteID) and not IsWormholeConstellation(hiliteID):
                hiliteItem = self.GetKnownConstellation(hiliteID)
                lineIDs = self.GetLineIDsForSystemList(hiliteItem.solarSystemIDs)
                for each in lineIDs:
                    lineAlpha[each] = maxAlpha

            elif IsRegion(hiliteID) and not IsWormholeRegion(hiliteID):
                hiliteItem = self.GetKnownRegion(hiliteID)
                lineIDs = self.GetLineIDsForSystemList(hiliteItem.solarSystemIDs)
                for each in lineIDs:
                    lineAlpha[each] = maxAlpha

        for each in self.allianceJumpLines:
            lineAlpha[each] = maxAlpha if showAllianceLines else 0.0

        self.UpdateLineColorData(baseLineAlphaModulate, lineAlpha)
        self.UpdateAutopilotJumpRoute()
        self.solarSystemJumpLineSet.SubmitChanges()

    def ChangeLineColor(self, lineSet, lineID, color, baseAlphaModulate = 1.0, overrideAlpha = {}):
        if len(color) == 2:
            fromColor = self.ModulateAlpha(color[0], overrideAlpha.get(lineID, baseAlphaModulate))
            toColor = self.ModulateAlpha(color[1], overrideAlpha.get(lineID, baseAlphaModulate))
        else:
            fromColor = toColor = self.ModulateAlpha(color, overrideAlpha.get(lineID, baseAlphaModulate))
        lineSet.ChangeLineColor(lineID, fromColor, toColor)

    def ModulateAlpha(self, color, alphaModulate):
        if len(color) == 3:
            r, g, b = color
            return (r,
             g,
             b,
             alphaModulate)
        r, g, b, a = color
        return (r,
         g,
         b,
         a * alphaModulate)

    def UpdateLineColorData(self, lineAlphaModulate, lineAlpha):
        """Update color data per line in the map"""
        lineSet = self.solarSystemJumpLineSet
        for lineID, lineData in self.jumpLineInfoByLineID.iteritems():
            if lineID in self.allianceJumpLines:
                fromColor = toColor = JUMPBRIDGE_COLOR
            else:
                fromColor = self.starColorByID.get(lineData.fromSolarSystemID, NEUTRAL_COLOR)
                toColor = self.starColorByID.get(lineData.toSolarSystemID, NEUTRAL_COLOR)
            self.ChangeLineColor(lineSet, lineID, (fromColor, toColor), lineAlphaModulate, lineAlpha)
            lineSet.ChangeLineWidth(lineID, LINE_BASE_WIDTH)
            if lineData.jumpType == mapcommon.REGION_JUMP:
                lineLength = self.GetDistance(lineData.currentFromPosition, lineData.currentToPosition)
                lineSet.ChangeLineAnimation(lineID, (0, 0, 0, 1), 0.0, lineLength / 100)
            elif lineData.jumpType == mapcommon.CONSTELLATION_JUMP:
                lineLength = self.GetDistance(lineData.currentFromPosition, lineData.currentToPosition)
                lineSet.ChangeLineAnimation(lineID, (0, 0, 0, 1), 0.0, lineLength / 50)
            else:
                lineSet.ChangeLineAnimation(lineID, (0, 0, 0, 0), 0.0, 1.0)

    def UpdateAutopilotJumpRoute(self):

        def GetSystemColorBasedOnSecRating(ssID):
            ss = self.mapSvc.GetSecurityStatus(ssID)
            c = FmtSystemSecStatus(ss, 1)[1]
            return (c.r,
             c.g,
             c.b,
             2.0)

        starmapSvc = sm.GetService('starmap')
        destinationPath = starmapSvc.GetDestinationPath()
        if destinationPath and destinationPath[0] != session.solarsystemid2:
            destinationPath = [session.solarsystemid2] + destinationPath
        lineSet = self.solarSystemJumpLineSet
        for i in xrange(len(destinationPath) - 1):
            fromID = destinationPath[i]
            toID = destinationPath[i + 1]
            try:
                lineID = self.GetLineIDForJumpBetweenSystems(fromID, toID)
            except (RuntimeError, KeyError):
                continue

            jumpLineInfo = self.jumpLineInfoByLineID[lineID]
            if fromID == jumpLineInfo.fromSolarSystemID:
                fromColor = GetSystemColorBasedOnSecRating(fromID)
                toColor = GetSystemColorBasedOnSecRating(toID)
                animationDirection = -1
            else:
                fromColor = GetSystemColorBasedOnSecRating(toID)
                toColor = GetSystemColorBasedOnSecRating(fromID)
                animationDirection = 1
            self.ChangeLineColor(lineSet, lineID, (fromColor, toColor))
            lineSet.ChangeLineWidth(lineID, LINE_BASE_WIDTH * 2)
            lineLength = self.GetDistance(jumpLineInfo.currentFromPosition, jumpLineInfo.currentToPosition)
            if lineLength:
                segmentScale = lineLength / 400.0
                animationSpeed = 3.0 / segmentScale * animationDirection
                lineSet.ChangeLineAnimation(lineID, (0, 0, 0, 0.75), animationSpeed, segmentScale)

    def RegisterStarColorModes(self):
        """
        register starcolor mode handlers
        The handlers are a tuple of (loadingText, colorFuction [, (args,)]) mapped to a color mode
        color function should manage getting data and coloring stars
        """
        self.starColorHandlers = {mapcommon.STARMODE_ASSETS: (localization.GetByLabel('UI/Map/StarMap/ShowAssets'), colorHandler.ColorStarsByAssets),
         mapcommon.STARMODE_VISITED: (localization.GetByLabel('UI/Map/StarMap/ShowSystemsVisited'), colorHandler.ColorStarsByVisited),
         mapcommon.STARMODE_SECURITY: (localization.GetByLabel('UI/Map/StarMap/SecurityStatus'), colorHandler.ColorStarsBySecurity),
         mapcommon.STARMODE_INDEX_STRATEGIC: (localization.GetByLabel('UI/Map/StarMap/Strategic'),
                                              colorHandler.ColorStarsByDevIndex,
                                              const.attributeDevIndexSovereignty,
                                              localization.GetByLabel('UI/Map/StarMap/Strategic')),
         mapcommon.STARMODE_INDEX_MILITARY: (localization.GetByLabel('UI/Map/StarMap/Military'),
                                             colorHandler.ColorStarsByDevIndex,
                                             const.attributeDevIndexMilitary,
                                             localization.GetByLabel('UI/Map/StarMap/Military')),
         mapcommon.STARMODE_INDEX_INDUSTRY: (localization.GetByLabel('UI/Map/StarMap/Industry'),
                                             colorHandler.ColorStarsByDevIndex,
                                             const.attributeDevIndexIndustrial,
                                             localization.GetByLabel('UI/Map/StarMap/Industry')),
         mapcommon.STARMODE_SOV_CHANGE: (localization.GetByLabel('UI/Map/StarMap/RecentSovereigntyChanges'), colorHandler.ColorStarsBySovChanges, mapcommon.SOV_CHANGES_ALL),
         mapcommon.STARMODE_SOV_GAIN: (localization.GetByLabel('UI/Map/StarMap/SovereigntyGain'), colorHandler.ColorStarsBySovChanges, mapcommon.SOV_CHANGES_SOV_GAIN),
         mapcommon.STARMODE_SOV_LOSS: (localization.GetByLabel('UI/Map/StarMap/SovereigntyLoss'), colorHandler.ColorStarsBySovChanges, mapcommon.SOV_CHANGES_SOV_LOST),
         mapcommon.STARMODE_OUTPOST_GAIN: (localization.GetByLabel('UI/Map/StarMap/StationGain'), colorHandler.ColorStarsBySovChanges, mapcommon.SOV_CHANGES_OUTPOST_GAIN),
         mapcommon.STARMODE_OUTPOST_LOSS: (localization.GetByLabel('UI/Map/StarMap/StationLoss'), colorHandler.ColorStarsBySovChanges, mapcommon.SOV_CHANGES_OUTPOST_LOST),
         mapcommon.STARMODE_SOV_STANDINGS: (localization.GetByLabel('UI/Map/StarMap/Standings'), colorHandler.ColorStarsByFactionStandings),
         mapcommon.STARMODE_FACTION: (localization.GetByLabel('UI/Map/StarMap/SovereigntyMap'), colorHandler.ColorStarsByFaction),
         mapcommon.STARMODE_FACTIONEMPIRE: (localization.GetByLabel('UI/Map/StarMap/SovereigntyMap'), colorHandler.ColorStarsByFaction),
         mapcommon.STARMODE_MILITIA: (localization.GetByLabel('UI/Map/StarMap/FactionalWarfare'), colorHandler.ColorStarsByMilitia),
         mapcommon.STARMODE_REGION: (localization.GetByLabel('UI/Map/StarMap/ColorStarsByRegion'), colorHandler.ColorStarsByRegion),
         mapcommon.STARMODE_CARGOILLEGALITY: (localization.GetByLabel('UI/Map/StarMap/MyCargoIllegality'), colorHandler.ColorStarsByCargoIllegality),
         mapcommon.STARMODE_PLAYERCOUNT: (localization.GetByLabel('UI/Map/StarMap/ShowPilotsInSpace'), colorHandler.ColorStarsByNumPilots),
         mapcommon.STARMODE_PLAYERDOCKED: (localization.GetByLabel('UI/Map/StarMap/ShowPilotsDocked'), colorHandler.ColorStarsByNumPilots),
         mapcommon.STARMODE_STATIONCOUNT: (localization.GetByLabel('UI/Map/StarMap/ShowStationCount'), colorHandler.ColorStarsByStationCount),
         mapcommon.STARMODE_DUNGEONS: (localization.GetByLabel('UI/Map/StarMap/ShowDeadspaceComplexes'), colorHandler.ColorStarsByDungeons),
         mapcommon.STARMODE_DUNGEONSAGENTS: (localization.GetByLabel('UI/Map/StarMap/ShowAgentSites'), colorHandler.ColorStarsByDungeons),
         mapcommon.STARMODE_JUMPS1HR: (localization.GetByLabel('UI/Map/StarMap/ShowRecentJumps'), colorHandler.ColorStarsByJumps1Hour),
         mapcommon.STARMODE_SHIPKILLS1HR: (localization.GetByLabel('UI/Map/StarMap/ShowShipsDestroyed'),
                                           colorHandler.ColorStarsByKills,
                                           const.mapHistoryStatKills,
                                           1),
         mapcommon.STARMODE_SHIPKILLS24HR: (localization.GetByLabel('UI/Map/StarMap/ShowShipsDestroyed'),
                                            colorHandler.ColorStarsByKills,
                                            const.mapHistoryStatKills,
                                            24),
         mapcommon.STARMODE_MILITIAKILLS1HR: (localization.GetByLabel('UI/Map/StarMap/ShowMilitiaShipsDestroyed'),
                                              colorHandler.ColorStarsByKills,
                                              const.mapHistoryStatFacWarKills,
                                              1),
         mapcommon.STARMODE_MILITIAKILLS24HR: (localization.GetByLabel('UI/Map/StarMap/ShowMilitiaShipsDestroyed'),
                                               colorHandler.ColorStarsByKills,
                                               const.mapHistoryStatFacWarKills,
                                               24),
         mapcommon.STARMODE_PODKILLS1HR: (localization.GetByLabel('UI/Map/StarMap/ShowMilitiaShipsDestroyed'), colorHandler.ColorStarsByPodKills),
         mapcommon.STARMODE_PODKILLS24HR: (localization.GetByLabel('UI/Map/StarMap/ShowMilitiaShipsDestroyed'), colorHandler.ColorStarsByPodKills),
         mapcommon.STARMODE_FACTIONKILLS1HR: (localization.GetByLabel('UI/Map/StarMap/ShowFactionShipsDestroyed'), colorHandler.ColorStarsByFactionKills),
         mapcommon.STARMODE_CYNOSURALFIELDS: (localization.GetByLabel('UI/Map/StarMap/ActiveCynosuralFields'), colorHandler.ColorStarsByCynosuralFields),
         mapcommon.STARMODE_CORPOFFICES: (localization.GetByLabel('UI/Map/StarMap/ShowAssets'),
                                          colorHandler.ColorStarsByCorpAssets,
                                          'offices',
                                          localization.GetByLabel('UI/Map/StarMap/Offices')),
         mapcommon.STARMODE_CORPIMPOUNDED: (localization.GetByLabel('UI/Map/StarMap/ShowAssets'),
                                            colorHandler.ColorStarsByCorpAssets,
                                            'junk',
                                            localization.GetByLabel('UI/Map/StarMap/Impounded')),
         mapcommon.STARMODE_CORPPROPERTY: (localization.GetByLabel('UI/Map/StarMap/ShowAssets'),
                                           colorHandler.ColorStarsByCorpAssets,
                                           'property',
                                           localization.GetByLabel('UI/Map/StarMap/Property')),
         mapcommon.STARMODE_CORPDELIVERIES: (localization.GetByLabel('UI/Map/StarMap/ShowAssets'),
                                             colorHandler.ColorStarsByCorpAssets,
                                             'deliveries',
                                             localization.GetByLabel('UI/Map/StarMap/Deliveries')),
         mapcommon.STARMODE_FRIENDS_FLEET: (localization.GetByLabel('UI/Map/StarMap/FindAssociates'), colorHandler.ColorStarsByFleetMembers),
         mapcommon.STARMODE_FRIENDS_CORP: (localization.GetByLabel('UI/Map/StarMap/FindAssociates'), colorHandler.ColorStarsByCorpMembers),
         mapcommon.STARMODE_FRIENDS_AGENT: (localization.GetByLabel('UI/Map/StarMap/FindAssociates'), colorHandler.ColorStarsByMyAgents),
         mapcommon.STARMODE_AVOIDANCE: (localization.GetByLabel('UI/Map/StarMap/AvoidanceSystems'), colorHandler.ColorStarsByAvoidedSystems),
         mapcommon.STARMODE_REAL: (localization.GetByLabel('UI/Map/StarMap/ActualColor'), colorHandler.ColorStarsByRealSunColor),
         mapcommon.STARMODE_SERVICE: (localization.GetByLabel('UI/Map/StarMap/FindStationServices'), colorHandler.ColorStarsByServices),
         mapcommon.STARMODE_PISCANRANGE: (localization.GetByLabel('UI/Map/StarMap/PlanetScanRange'), colorHandler.ColorStarsByPIScanRange),
         mapcommon.STARMODE_MYCOLONIES: (localization.GetByLabel('UI/Map/StarMap/MyColonies'), colorHandler.ColorStarsByMyColonies),
         mapcommon.STARMODE_PLANETTYPE: (localization.GetByLabel('UI/Map/StarMap/ShowSystemsByPlanetTypes'), colorHandler.ColorStarsByPlanetType),
         mapcommon.STARMODE_INCURSION: (localization.GetByLabel('UI/Map/StarMap/Incursions'), colorHandler.ColorStarsByIncursions),
         mapcommon.STARMODE_JOBS24HOUR: (localization.GetByLabel('UI/Map/StarMap/JobsLast24Hours'), colorHandler.ColorStarsByJobs24Hours, None),
         mapcommon.STARMODE_MANUFACTURING_JOBS24HOUR: (localization.GetByLabel('UI/Map/StarMap/JobsLast24Hours'), colorHandler.ColorStarsByJobs24Hours, industry.MANUFACTURING),
         mapcommon.STARMODE_RESEARCHTIME_JOBS24HOUR: (localization.GetByLabel('UI/Map/StarMap/JobsLast24Hours'), colorHandler.ColorStarsByJobs24Hours, industry.RESEARCH_TIME),
         mapcommon.STARMODE_RESEARCHMATERIAL_JOBS24HOUR: (localization.GetByLabel('UI/Map/StarMap/JobsLast24Hours'), colorHandler.ColorStarsByJobs24Hours, industry.RESEARCH_MATERIAL),
         mapcommon.STARMODE_COPY_JOBS24HOUR: (localization.GetByLabel('UI/Map/StarMap/JobsLast24Hours'), colorHandler.ColorStarsByJobs24Hours, industry.COPYING),
         mapcommon.STARMODE_INVENTION_JOBS24HOUR: (localization.GetByLabel('UI/Map/StarMap/JobsLast24Hours'), colorHandler.ColorStarsByJobs24Hours, industry.INVENTION),
         mapcommon.STARMODE_INDUSTRY_MANUFACTURING_COST_INDEX: (localization.GetByLabel('UI/Map/StarMap/IndustryCostModifer'), colorHandler.ColorStarsByIndustryCostModifier, industry.MANUFACTURING),
         mapcommon.STARMODE_INDUSTRY_RESEARCHTIME_COST_INDEX: (localization.GetByLabel('UI/Map/StarMap/IndustryCostModifer'), colorHandler.ColorStarsByIndustryCostModifier, industry.RESEARCH_TIME),
         mapcommon.STARMODE_INDUSTRY_RESEARCHMATERIAL_COST_INDEX: (localization.GetByLabel('UI/Map/StarMap/IndustryCostModifer'), colorHandler.ColorStarsByIndustryCostModifier, industry.RESEARCH_MATERIAL),
         mapcommon.STARMODE_INDUSTRY_COPY_COST_INDEX: (localization.GetByLabel('UI/Map/StarMap/IndustryCostModifer'), colorHandler.ColorStarsByIndustryCostModifier, industry.COPYING),
         mapcommon.STARMODE_INDUSTRY_INVENTION_COST_INDEX: (localization.GetByLabel('UI/Map/StarMap/IndustryCostModifer'), colorHandler.ColorStarsByIndustryCostModifier, industry.INVENTION)}
        if session.role & ROLE_GML:
            self.starColorHandlers[mapcommon.STARMODE_INCURSIONGM] = (localization.GetByLabel('UI/Map/StarMap/IncursionsGm'), colorHandler.ColorStarsByIncursionsGM)

    def UpdateMapViewColorMode(self):
        import eve.client.script.ui.shared.mapView.mapViewColorHandler as colorHandler
        colorMode = settings.user.ui.Get(VIEWMODE_COLOR_SETTINGS, VIEWMODE_COLOR_DEFAULT)
        self.starLegend = []
        mode = colorMode[0] if isinstance(colorMode, tuple) else colorMode
        definition = self.starColorHandlers.get(mode, (localization.GetByLabel('UI/Map/StarMap/ActualColor'), colorHandler.ColorStarsByRealSunColor))
        desc, colorFunc, args = definition[0], definition[1], definition[2:]
        self.StartLoadingBar('set_star_color', localization.GetByLabel('UI/Map/StarMap/GettingData'), desc, 2)
        blue.pyos.synchro.SleepWallclock(1)
        if self.destroyed:
            return
        colorInfo = KeyVal(solarSystemDict={}, colorList=None, legend=set(), colorType=colorHandler.STAR_COLORTYPE_PASSIVE)
        colorFunc(colorInfo, colorMode, *args)
        if self.destroyed:
            return
        self.starLegend = list(colorInfo.legend)
        self.UpdateLoadingBar('set_star_color', desc, localization.GetByLabel('UI/Map/StarMap/GettingData'), 1, 2)
        blue.pyos.synchro.SleepWallclock(1)
        if self.destroyed:
            return
        self.ApplyStarColors(colorInfo)
        self.UpdateLines(hint='UpdateMapViewColorMode')
        self.markersHandler.RefreshActiveAndHilightedMarkers()
        self.StopLoadingBar('set_star_color')

    def GetColorCurve(self, colorList):
        colorCurve = trinity.TriColorCurve()
        black = trinity.TriColor()
        colorListDivisor = float(len(colorList) - 1)
        for colorID, colorValue in enumerate(colorList):
            time = float(colorID) / colorListDivisor
            colorCurve.AddKey(time, colorValue, black, black, trinity.TRIINT_LINEAR)

        colorCurve.Sort()
        colorCurve.extrapolation = trinity.TRIEXT_CONSTANT
        colorCurve.start = 0L
        return colorCurve

    def GetColorCurveValue(self, colorCurve, time):
        return colorCurve.GetColorAt(long(const.SEC * time))

    def ApplyStarColors(self, colorInfo):
        """
        solarSystemDict: dict of solarSystemIDs with (size, age, comment, color) as value
        colorList: lots of colors forming a color gradiant
        """
        self.starData = {}
        self.starColorByID = {}
        solarSystemDict = colorInfo.solarSystemDict
        colorList = colorInfo.colorList
        colorCurve = self.GetColorCurve(colorList or self.GetDefaultColorList())
        neutralStarSize = SUNBASE / 2
        sizeFactor = 1.0
        if colorInfo.colorType == colorHandler.STAR_COLORTYPE_DATA:
            self.starDataTexture.resourcePath = PARTICLE_SPRITE_DATA_TEXTURE
            colorValues = len(solarSystemDict)
            if colorValues:
                sizeFactor = min(5, len(self.particleIDToSystemIDMap) / len(solarSystemDict))
            neutralStarSize = 0.0
        else:
            self.starDataTexture.resourcePath = PARTICLE_SPRITE_HEAT_TEXTURE
        particleSystem = self.starParticles
        pr = False
        for particleID, solarSystemID in self.particleIDToSystemIDMap.iteritems():
            if solarSystemID in solarSystemDict:
                sizeNormalized, colorPositionNormalized, commentCallback, uniqueColor = solarSystemDict[solarSystemID]
                starSize = SUNBASE + SUNBASE * sizeNormalized * sizeFactor
                if uniqueColor is None and colorPositionNormalized is not None:
                    col = self.GetColorCurveValue(colorCurve, colorPositionNormalized)
                else:
                    col = uniqueColor
                if commentCallback:
                    self.starData[particleID] = commentCallback
                try:
                    starColor = (col.r,
                     col.g,
                     col.b,
                     1.0)
                except:
                    starColor = col

            else:
                starColor = NEUTRAL_COLOR
                starSize = neutralStarSize
            self.starColorByID[solarSystemID] = starColor
            particleSystem.SetItemElement(particleID, 2, starSize)
            particleSystem.SetItemElement(particleID, 3, starColor)

        particleSystem.UpdateData()
        self.mapStars.display = 1

    def GetDefaultColorList(self):
        return [trinity.TriColor(1.0, 0.0, 0.0), trinity.TriColor(1.0, 1.0, 0.0), trinity.TriColor(0.0, 1.0, 0.0)]

    def GetRouteFromWaypoints(self, waypoints, startSystem = None):
        if startSystem is None:
            startSystem = session.solarsystemid2
        fullWaypointList = [startSystem] + waypoints
        self.LogInfo('Calling pathfinder with waypoint list', str(waypoints))
        destinationPath = self.clientPathfinderService.GetWaypointPath(fullWaypointList)
        return destinationPath or []

    def UpdateHexMap(self, isFlat = None):
        return

        def GetUserUiSetting(name, default):
            return settings.user.ui.Get(name, default)

        showHexMap = GetUserUiSetting('map_tile_no_tiles', 1) == 0
        showUnflattened = GetUserUiSetting('map_tile_show_unflattened', 0)
        self.tileLegend = []
        if isFlat is None:
            isFlat = self.IsFlat()
        if showHexMap and (showUnflattened or isFlat):
            systemToAllianceMap = self.GetAllianceSolarSystems()
            changeList = []
            if GetUserUiSetting('map_tile_activity', 0) == 1:
                changeList = sm.GetService('sov').GetRecentActivity()
            tileMode = GetUserUiSetting('map_tile_mode', TILE_MODE_SOVEREIGNTY)
            colorByStandings = tileMode == TILE_MODE_STANDIGS
            self.hexMap.LayoutTiles(HEX_TILE_SIZE, systemToAllianceMap, changeList, colorByStandings)
            self.hexMap.Enable()
            showOutlines = GetUserUiSetting('map_tile_show_outlines', 1) == 1
            self.hexMap.EnableOutlines(showOutlines)
            self.tileLegend = self.hexMap.legend
        else:
            self.hexMap.Enable(False)

    def HighlightTiles(self, dataList, colorList):
        self.hexMap.HighlightTiles(dataList, colorList)

    def GetLegend(self, name):
        return getattr(self, name + 'Legend', [])

    def OnMapObjectSelected(self, itemID, parentID, objectTransform = None):
        self.SetInterest(itemID, objectTransform=objectTransform, parentSolarsystemID=parentID)

    def StartLoadingBar(self, key, tile, action, total):
        pass

    def UpdateLoadingBar(self, key, tile, action, part, total):
        pass

    def StopLoadingBar(self, key):
        pass

    def OnAutopilotUpdated(self):
        self.UpdateLines(hint='OnAutopilotUpdated')

    def OnDestinationSet(self, *args, **kwds):
        self.UpdateLines(hint='OnDestinationSet')
        self.ShowMyLocation()

    def OnHomeStationChanged(self, *args, **kwds):
        self.ShowMyHomeStation()

    def OnLoadWMCPSettings(self, tileMode):
        self.UpdateHexMap()

    def UpdateViewPort(self):
        if self.sceneContainer:
            self.sceneContainer.UpdateViewPort()
        if self.solarSystemStandalone:
            self.solarSystemStandalone.UpdateViewPort()
