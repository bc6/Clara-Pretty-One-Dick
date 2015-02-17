#Embedded file name: eve/client/script/ui/shared/mapView\systemMapHandler.py
from carbonui.primitives.layoutGrid import LayoutGrid
from eve.client.script.environment.spaceObject.planet import Planet
from eve.client.script.ui.control.eveLabel import EveLabelLarge, EveLabelMedium
from eve.client.script.ui.shared.mapView.mapViewConst import MARKERID_SOLARSYSTEM_CELESTIAL, VIEWMODE_MARKERS_SETTINGS
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerCelestial import MarkerCelestial
from eve.client.script.ui.shared.mapView.mapViewSettings import GetMapViewSetting
from eve.client.script.ui.shared.maps.mapcommon import STARMAP_SCALE
from eve.client.script.ui.shared.mapView.mapViewUtil import SolarSystemPosToMapPos, ScaleSolarSystemValue
from eve.common.script.planet.surfacePoint import SurfacePoint
from eve.common.script.util.eveFormat import FmtSystemSecStatus
from localization import GetByLabel
import trinity
import uthread
import carbonui.const as uiconst
import evegraphics.settings as gfxsettings
import geo2
import sys
import math
PLANET_TEXTURE_SIZE = 512

class SystemMapHandler(object):
    scene = None
    markersHandler = None
    localMarkerIDs = None
    _yScaleFactor = 1.0

    def __init__(self, solarsystemID, scene = None, scaling = 1.0, position = None, markersHandler = None):
        self.scene = scene
        self.solarsystemID = solarsystemID
        self.scaling = scaling
        self.bracketsByID = {}
        self.systemMapSvc = sm.GetService('systemmap')
        self.markersHandler = markersHandler
        self.localMarkerIDs = set()
        parent = trinity.EveRootTransform()
        parent.name = 'solarsystem_%s' % solarsystemID
        self.systemMapTransform = parent
        if scene:
            scene.objects.append(self.systemMapTransform)
        if position:
            self.SetPosition(position)

    @apply
    def yScaleFactor():

        def fget(self):
            return self._yScaleFactor

        def fset(self, value):
            self._yScaleFactor = value
            self.UpdatePosition()

        return property(**locals())

    def SetMarkersHandler(self, markersHandler):
        self.markersHandler = markersHandler
        self.localMarkerIDs = set()

    def SetPosition(self, position):
        self.position = position
        self.UpdatePosition()

    def UpdatePosition(self):
        x, y, z = self.position
        self.systemMapTransform.translation = (x, y * self.yScaleFactor, z)
        self.systemMapTransform.scaling = (ScaleSolarSystemValue(1.0), ScaleSolarSystemValue(self.yScaleFactor), ScaleSolarSystemValue(1.0))

    def Close(self):
        if self.scene:
            uicore.animations.MorphVector3(self.systemMapTransform, 'scaling', self.systemMapTransform.scaling, (0.0, 0.0, 0.0), duration=0.5, callback=self.RemoveFromScene)
        else:
            self.RemoveFromScene()

    def RemoveFromScene(self):
        if self.markersHandler and self.localMarkerIDs:
            for markerID in self.localMarkerIDs:
                self.markersHandler.RemoveMarker(markerID)

        self.markersHandler = None
        self.bracketsByID = None
        self.scene.objects.remove(self.systemMapTransform)
        self.systemMapTransform = None
        self.scene = None

    def LoadCelestials(self):
        groups, solarsystemData = self.systemMapSvc.GetSolarsystemHierarchy(self.solarsystemID)
        for transform in self.systemMapTransform.children:
            try:
                itemID = int(transform.name)
                itemData = solarsystemData[itemID]
            except:
                continue

            if itemData.groupID == const.groupPlanet:
                planetTransform = self.LoadPlanet(itemData.typeID, itemID)
                scaling = self.scaling
                planetTransform.scaling = (1 / scaling * 0.1, 1 / scaling * 0.1, 1 / scaling * 0.1)
                planetTransform.translation = transform.translation

    def LoadPlanet(self, planetTypeID, planetID):
        planet = Planet()
        objType = cfg.invtypes.Get(planetTypeID)
        graphicFile = objType.GraphicFile()
        planet.typeData['graphicFile'] = graphicFile
        planet.typeID = planetTypeID
        planet.LoadPlanet(planetID, forPhotoService=True, rotate=False, hiTextures=True)
        if planet.model is None or planet.model.highDetail is None:
            return
        planetTransform = trinity.EveTransform()
        planetTransform.name = 'planet'
        planetTransform.children.append(planet.model.highDetail)
        renderTarget, size = self.CreateRenderTarget()
        planet.DoPreProcessEffect(size, None, renderTarget)
        trinity.WaitForResourceLoads()
        for t in planet.model.highDetail.children:
            if t.mesh is not None:
                if len(t.mesh.transparentAreas) > 0:
                    t.sortValueMultiplier = 2.0

        self.systemMapTransform.children.append(planetTransform)
        return planetTransform

    def LoadSolarSystemMap(self):
        self.maxRadius = 0.0
        solarsystemID = self.solarsystemID
        parent = self.systemMapTransform
        solarSystemData = self.systemMapSvc.GetSolarsystemData(solarsystemID)
        planets = []
        childrenToParentByID = {}
        sunID = None
        maxRadius = 0.0
        for celestialObject in solarSystemData:
            if celestialObject.groupID == const.groupPlanet:
                planets.append((celestialObject.itemID, geo2.Vector(celestialObject.x, celestialObject.y, celestialObject.z)))
            elif celestialObject.groupID == const.groupSun:
                sunID = celestialObject.itemID

        for each in solarSystemData:
            if each.groupID in (const.groupPlanet, const.groupStargate):
                childrenToParentByID[each.itemID] = sunID
                continue
            closest = []
            eachPosition = geo2.Vector(each.x, each.y, each.z)
            for planetID, planetPos in planets:
                diffPos = planetPos - eachPosition
                diffVector = geo2.Vec3Length(diffPos)
                closest.append((diffVector, planetID))
                maxRadius = max(maxRadius, diffVector)

            closest.sort()
            childrenToParentByID[each.itemID] = planets[0][1]

        self.maxRadius = maxRadius
        orbits = []
        objectTransforms = {}
        pm = (const.groupPlanet, const.groupMoon)
        for each in solarSystemData:
            if each.itemID == each.locationID:
                continue
            if each.groupID == const.groupSecondarySun:
                continue
            if each.groupID in pm:
                parentID = childrenToParentByID.get(each.itemID, None)
                if parentID:
                    orbits.append([each.itemID, parentID])
            transform = trinity.EveTransform()
            transform.translation = (each.x, each.y, each.z)
            transform.name = str(each.itemID)
            parent.children.append(transform)
            objectTransforms[each.itemID] = transform

        uthread.new(self.CreateOrbits, orbits, objectTransforms)
        self.solarSystemRadius = maxRadius
        cfg.evelocations.Prime(objectTransforms.keys(), 0)

    def LoadMarkers(self):
        if self.markersHandler and self.localMarkerIDs:
            for markerID in self.localMarkerIDs:
                self.markersHandler.RemoveMarker(markerID)

        self.localMarkerIDs = set()
        solarSystemData = self.systemMapSvc.GetSolarsystemData(self.solarsystemID)
        loadMarkerGroups = GetMapViewSetting(VIEWMODE_MARKERS_SETTINGS)
        for each in solarSystemData:
            if self.markersHandler and each.groupID in loadMarkerGroups:
                bracketData = sm.GetService('bracket').GetMappedBracketProps(cfg.invgroups.Get(each.groupID).categoryID, each.groupID, each.typeID)
                markerID = (MARKERID_SOLARSYSTEM_CELESTIAL, each.itemID)
                markerObject = self.markersHandler.AddMarker(markerID, geo2.Vec3Add(self.position, SolarSystemPosToMapPos((each.x, each.y, each.z))), MarkerCelestial, texturePath=bracketData[0], celestialData=each, distanceFadeAlpha=True, maxVisibleRange=2500)
                markerObject.SetSolarSystemID(self.solarsystemID)
                self.localMarkerIDs.add(markerID)

    def CreateOrbits(self, child_parent, objectTransforms):
        lineSet = trinity.EveCurveLineSet()
        lineSet.name = 'OrbitLines'
        lineSet.depthOffset = 10000000.0
        self.systemMapTransform.children.append(lineSet)
        tex2D = trinity.TriTexture2DParameter()
        tex2D.name = 'TexMap'
        tex2D.resourcePath = 'res:/UI/Texture/classes/MapView/lineSegment.dds'
        lineSet.lineEffect.resources.append(tex2D)
        overlayTex2D = trinity.TriTexture2DParameter()
        overlayTex2D.name = 'OverlayTexMap'
        overlayTex2D.resourcePath = 'res:/UI/Texture/classes/MapView/lineSegment.dds'
        lineSet.lineEffect.resources.append(overlayTex2D)
        for childID, parentID in child_parent:
            if childID in objectTransforms and parentID in objectTransforms:
                self.CreateOrbitCircle(objectTransforms[childID], objectTransforms[parentID], lineSet)

        if lineSet:
            lineSet.SubmitChanges()

    def CreateOrbitCircle(self, orbitem, parent, lineSet, points = 256):
        orbitPos = geo2.Vector(*orbitem.translation)
        parentPos = geo2.Vector(*parent.translation)
        dirVec = orbitPos - parentPos
        radius = geo2.Vec3Length(dirVec)
        if radius == 0:
            return
        lineColor = (1, 1, 1, 0.1)
        dx, dy, dz = dirVec
        fromPoint = SurfacePoint(dx, dy, dz)
        radius, theta, phi = fromPoint.GetAsRadThPhiTuple()
        toPoint = SurfacePoint(theta=theta + math.pi * 0.5, phi=phi)
        x, y, z = toPoint.GetAsXYZTuple()
        line1 = lineSet.AddSpheredLineCrt(fromPoint.GetAsXYZTuple(), lineColor, (x, y, z), lineColor, parentPos, 3.0)
        line2 = lineSet.AddSpheredLineCrt(fromPoint.GetAsXYZTuple(), lineColor, (-x, -y, -z), lineColor, parentPos, 3.0)
        fromPoint = SurfacePoint(-dx, -dy, -dz)
        radius, theta, phi = fromPoint.GetAsRadThPhiTuple()
        toPoint = SurfacePoint(theta=theta + math.pi * 0.5, phi=phi)
        x, y, z = toPoint.GetAsXYZTuple()
        line3 = lineSet.AddSpheredLineCrt(fromPoint.GetAsXYZTuple(), lineColor, (x, y, z), lineColor, parentPos, 3.0)
        line4 = lineSet.AddSpheredLineCrt(fromPoint.GetAsXYZTuple(), lineColor, (-x, -y, -z), lineColor, parentPos, 3.0)
        lineSet.ChangeLineSegmentation(line1, 25)
        lineSet.ChangeLineSegmentation(line2, 25)
        lineSet.ChangeLineSegmentation(line3, 25)
        lineSet.ChangeLineSegmentation(line4, 25)
        animationColor = (0, 0, 0, 0.5)
        lineSet.ChangeLineAnimation(line1, animationColor, 0.1, 0.5)
        lineSet.ChangeLineAnimation(line2, animationColor, -0.1, 0.5)
        lineSet.ChangeLineAnimation(line3, animationColor, 0.1, 0.5)
        lineSet.ChangeLineAnimation(line4, animationColor, -0.1, 0.5)

    def CreateRenderTarget(self):
        textureQuality = gfxsettings.Get(gfxsettings.GFX_TEXTURE_QUALITY)
        size = PLANET_TEXTURE_SIZE >> textureQuality
        rt = None
        while rt is None or not rt.isValid:
            rt = trinity.Tr2RenderTarget(2 * size, size, 0, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
            if not rt.isValid:
                if size < 2:
                    return
                size = size / 2
                rt = None

        return (rt, size)


class SolarSystemInfoBox(LayoutGrid):
    default_columns = 2
    default_cellPadding = (0, 1, 6, 1)

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        self.nameLabel = EveLabelLarge(bold=True)
        self.AddCell(cellObject=self.nameLabel, colSpan=self.columns)
        EveLabelMedium(parent=self, text=GetByLabel('UI/Map/StarMap/SecurityStatus'))
        self.securityValue = EveLabelMedium(parent=self, bold=True, color=(1, 0, 0, 1))

    def LoadSolarSystemID(self, solarSystemID):
        self.nameLabel.text = cfg.evelocations.Get(solarSystemID).name
        securityStatus, color = FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarSystemID), True)
        self.securityValue.color = (color.r,
         color.g,
         color.b,
         1.0)
        self.securityValue.text = securityStatus
