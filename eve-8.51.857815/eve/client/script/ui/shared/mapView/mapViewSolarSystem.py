#Embedded file name: eve/client/script/ui/shared/mapView\mapViewSolarSystem.py
import math
import logging
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from eve.client.script.ui.control.buttons import Button, ButtonIcon
from eve.client.script.ui.shared.mapView.dockPanelSubFrame import DockablePanelContentFrame
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerMyHome import MarkerMyHome
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerMyLocation import MarkerMyLocation
from eve.client.script.ui.shared.mapView.mapViewMarkersHandler import MapViewMarkersHandler
from eve.client.script.ui.shared.mapView.mapViewSceneContainer import MapViewSceneContainer
from eve.client.script.ui.shared.mapView.mapViewUtil import SolarSystemPosToMapPos, ScaleSolarSystemValue, GetTranslationFromParentWithRadius
from eve.client.script.ui.shared.mapView.systemMapHandler import SystemMapHandler, SolarSystemInfoBox
import blue
from inventorycommon.util import IsWormholeSystem, IsWormholeRegion, IsWormholeConstellation
import trinity
import uthread
import fleetbr
import nodemanager
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
from eve.client.script.ui.shared.mapView.mapViewNavigation import MapViewNavigation
from eve.client.script.ui.shared.mapView.mapViewConst import VIEWMODE_COLOR_SETTINGS, VIEWMODE_GROUP_SETTINGS, VIEWMODE_GROUP_REGIONS, VIEWMODE_GROUP_CONSTELLATIONS, VIEWMODE_GROUP_DEFAULT, VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS, VIEWMODE_LINES_SETTINGS, VIEWMODE_LINES_DEFAULT, VIEWMODE_LINES_NONE, VIEWMODE_LINES_ALL, VIEWMODE_LINES_SELECTION_REGION_NEIGHBOURS, VIEWMODE_LINES_SELECTION_REGION, VIEWMODE_LAYOUT_SHOW_ABSTRACT_DEFAULT, VIEWMODE_COLOR_DEFAULT, VIEWMODE_LINES_SHOW_ALLIANCE_SETTINGS, VIEWMODE_LINES_SHOW_ALLIANCE_DEFAULT, MARKERID_MYPOS, MARKERID_BOOKMARK, MARKERID_SOLARSYSTEM_CELESTIAL, MARKERID_MYHOME, MARKER_POINT_TOP, VIEWMODE_MARKERS_SETTINGS, JUMPBRIDGE_COLOR, JUMPBRIDGE_CURVE_SCALE, VIEWMODE_FOCUS_SELF
import eve.client.script.ui.shared.maps.mapcommon as mapcommon
import geo2
import carbonui.const as uiconst
import localization
log = logging.getLogger(__name__)
SUNBASE = 7.5
LINE_EFFECT = 'res:/Graphics/Effect/Managed/Space/SpecialFX/Lines3DStarMapNew.fx'
PARTICLE_EFFECT = 'res:/Graphics/Effect/Managed/Space/SpecialFX/Particles/StarmapNew.fx'
PARTICLE_SPRITE_TEXTURE = 'res:/Texture/Particle/mapStarNew5.dds'
PARTICLE_SPRITE_HEAT_TEXTURE = 'res:/Texture/Particle/mapStarNewHeat.dds'
DISTANCE_RANGE = 'distanceRange'
NEUTRAL_COLOR = (0.25, 0.25, 0.25, 1.0)
HEX_TILE_SIZE = 60

class MapViewSolarSystem(Container):
    __notifyevents__ = ['OnUIScalingChange', 'OnAutopilotUpdated', 'OnDestinationSet']
    curveSet = None
    systemMap = None
    mapRoot = None
    infoBox = None
    markersHandler = None
    markersAlwaysVisible = set()
    inFocus = False
    currentSolarsystem = None
    abstractMode = False
    hilightID = None
    _yScaleFactor = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.mapSvc = sm.GetService('map')
        innerPadding = attributes.innerPadding or 0
        self.infoLayer = Container(parent=self, clipChildren=True, name='infoLayer', padding=innerPadding)
        if attributes.showCloseButton:
            closeButton = ButtonIcon(parent=self.infoLayer, hint='Close', texturePath='res:/UI/Texture/classes/DockPanel/closeButton.png', func=attributes.closeFunction or self.Close, align=uiconst.TOPRIGHT)
        if attributes.showInfobox:
            self.infoBox = SolarSystemInfoBox(parent=self.infoLayer, align=uiconst.TOPLEFT, left=32, top=32)
        self.mapNavigation = MapViewNavigation(parent=self, align=uiconst.TOALL, state=uiconst.UI_NORMAL, mapView=self, padding=(0, 32, 0, 0))
        sceneContainer = MapViewSceneContainer(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, padding=innerPadding)
        sceneContainer.Startup()
        self.sceneContainer = sceneContainer
        self.sceneContainer.display = False
        self.camera.SetCallback(self.OnCameraMoved)
        scene = trinity.EveSpaceScene()
        scene.starfield = trinity.Load('res:/dx9/scene/starfield/spritestars.red')
        scene.backgroundEffect = trinity.Load('res:/dx9/scene/starfield/starfieldNebula.red')
        scene.backgroundRenderingEnabled = True
        node = nodemanager.FindNode(scene.backgroundEffect.resources, 'NebulaMap', 'trinity.TriTexture2DParameter')
        if node is not None:
            s = sm.GetService('sceneManager')
            sceneCube = s.GetNebulaPathForSystem(session.solarsystemid)
            node.resourcePath = sceneCube or 'res:/UI/Texture/classes/MapView/backdrop_cube.dds'
        self.mapRoot = trinity.EveRootTransform()
        self.mapRoot.name = 'universe'
        scene.objects.append(self.mapRoot)
        self.sceneContainer.scene = scene
        self.sceneContainer.DisplaySpaceScene()
        self.markersHandler = MapViewMarkersHandler(self, self.sceneContainer.bracketCurveSet, self.infoLayer, eventHandler=self.mapNavigation)
        self.abstractMode = settings.user.ui.Get(VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS, VIEWMODE_LAYOUT_SHOW_ABSTRACT_DEFAULT)
        if self.abstractMode:
            self.yScaleFactor = 0.0001
        sm.RegisterNotify(self)
        uthread.new(uicore.registry.SetFocus, self)

    def Close(self, *args, **kwds):
        self.mapMode = VIEWMODE_GROUP_DEFAULT
        if hasattr(self, 'mapRoot') and self.mapRoot is not None:
            del self.mapRoot.children[:]
        self.mapRoot = None
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
        Container.Close(self, *args, **kwds)

    def SetFocusState(self, focusState):
        self.inFocus = focusState

    def SetHilightItem(self, itemID):
        hilightID = itemID
        if self.hilightID != hilightID:
            self.hilightID = hilightID

    def OnMapViewSettingChanged(self, settingKey, *args, **kwds):
        if settingKey == VIEWMODE_FOCUS_SELF:
            return
        if settingKey == VIEWMODE_MARKERS_SETTINGS:
            if self.currentSolarsystem:
                self.currentSolarsystem.LoadMarkers()
            return
        currentAbstract = settings.user.ui.Get(VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS, VIEWMODE_LAYOUT_SHOW_ABSTRACT_DEFAULT)
        if currentAbstract != self.abstractMode:
            self.LoadAbstractMode(currentAbstract)

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
            self.mapRoot.scaling = (1.0, value, 1.0)
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

    def OnUIScalingChange(self, *args):
        self.markersHandler.ReloadAll()

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
        if self.destroyed:
            return
        if stationInfo.solarSystemID != self.currentSolarsystem.solarsystemID:
            return
        mapPosition = (0, 0, 0)
        localPosition = SolarSystemPosToMapPos((stationInfo.x, stationInfo.y, stationInfo.z))
        mapPosition = geo2.Vec3Add(mapPosition, localPosition)
        markerObject = self.markersHandler.AddMarker(markerID, mapPosition, MarkerMyHome, stationInfo=stationInfo, texturePath='res:/UI/Texture/classes/MapView/homeIcon.png', hintString='Home Station', distanceFadeAlpha=False)
        markerObject.SetSolarSystemID(stationInfo.solarSystemID)
        self.markersAlwaysVisible.add(markerID)

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

        mapPosition = (0, 0, 0)
        if session.stationid:
            stationInfo = self.mapSvc.GetStation(session.stationid)
            if self.destroyed:
                return
            localPosition = SolarSystemPosToMapPos((stationInfo.x, stationInfo.y, stationInfo.z))
            mapPosition = geo2.Vec3Add(mapPosition, localPosition)
            markerObject = self.markersHandler.AddMarker(markerID, mapPosition, MarkerMyLocation, texturePath='res:/UI/Texture/classes/MapView/focusIcon.png', hintString=localization.GetByLabel('UI/Map/StarMap/lblYouAreHere'), distanceFadeAlpha=False)
        else:
            markerObject = self.markersHandler.AddMarker(markerID, mapPosition, MarkerMyLocation, trackObjectID=session.shipid or session.stationid, solarSystemMapPosition=mapPosition, texturePath='res:/UI/Texture/classes/MapView/focusIcon.png', hintString=localization.GetByLabel('UI/Map/StarMap/lblYouAreHere'), distanceFadeAlpha=False)
        markerObject.SetSolarSystemID(session.solarsystemid2)
        self.markersAlwaysVisible.add(markerID)

    def LoadAbstractMode(self, modeState):
        self.abstractMode = modeState
        if self.abstractMode == True:
            uicore.animations.MorphScalar(self, 'yScaleFactor', startVal=self.yScaleFactor, endVal=0.0001, duration=1.0)
        else:
            uicore.animations.MorphScalar(self, 'yScaleFactor', startVal=self.yScaleFactor, endVal=1.0, duration=1.0)

    def OnCameraMoved(self):
        camera = self.camera
        if camera is None:
            return
        if self.markersHandler:
            self.markersHandler.RegisterCameraTranslationFromParent(self.camera.translationFromParent)

    def SetActiveItem(self, itemID, updateCamera = True, zoomToItem = False, *args, **kwds):
        markerObject = self.markersHandler.GetMarkerByID(itemID)
        if not markerObject:
            return
        markerPosition = markerObject.scaledCenter
        if updateCamera:
            self.camera.pointOfInterest = markerPosition

    def LoadSolarSystemDetails(self, solarSystemID):
        current = getattr(self, 'currentSolarsystem', None)
        if current:
            resetSolarsystemID = current.solarsystemID
        else:
            resetSolarsystemID = None
        if IsWormholeSystem(solarSystemID):
            self.scene.starfield.numStars = 0
        if resetSolarsystemID != solarSystemID:
            if current:
                current.Close()
            self.currentSolarsystem = None
            self.currentSolarsystem = SystemMapHandler(solarSystemID, self.scene, scaling=mapcommon.STARMAP_SCALE * 100, position=(0, 0, 0), markersHandler=self.markersHandler)
            self.currentSolarsystem.LoadSolarSystemMap()
            if self.destroyed:
                return
            self.currentSolarsystem.yScaleFactor = self.yScaleFactor
            self.currentSolarsystem.LoadMarkers()
            if self.destroyed:
                return
            uicore.animations.MorphVector3(self.currentSolarsystem.systemMapTransform, 'scaling', (0.0, 0.0, 0.0), (mapcommon.STARMAP_SCALE * 100, mapcommon.STARMAP_SCALE * 100 * self.yScaleFactor, mapcommon.STARMAP_SCALE * 100), duration=0.5)
            uthread.new(self.ShowMyHomeStation)
            uthread.new(self.ShowMyLocation)
            if self.infoBox:
                self.infoBox.LoadSolarSystemID(solarSystemID)

    def FrameSolarSystem(self):
        radius = ScaleSolarSystemValue(self.currentSolarsystem.solarSystemRadius)
        cameraDistanceFromInterest = GetTranslationFromParentWithRadius(radius, self.camera)
        minCameraDistanceFromInterest = 2.5
        cameraPointOfInterest = None
        if minCameraDistanceFromInterest:
            self.camera.SetMinTranslationFromParent(minCameraDistanceFromInterest)
        if cameraDistanceFromInterest:
            self.camera.ZoomToDistance(cameraDistanceFromInterest)
        if cameraPointOfInterest:
            self.camera.pointOfInterest = cameraPointOfInterest
        self.sceneContainer.display = True

    def GetPickObjects(self, *args, **kwds):
        return None

    def OnAutopilotUpdated(self):
        pass

    def OnDestinationSet(self, *args, **kwds):
        self.ShowMyLocation()

    def UpdateViewPort(self):
        if self.sceneContainer:
            self.sceneContainer.UpdateViewPort()
