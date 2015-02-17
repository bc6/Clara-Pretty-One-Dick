#Embedded file name: evespacescene\routevisualizer.py
import geo2
import log
import trinity
import util

class RouteVisualizer(object):
    """
    A simple class to control the auto pilot route visualization. 
    Relies on the map being initialized.
    Should probably use dependency injection, instead of all the service calls.
    """
    __notifyevents__ = ['OnDestinationSet', 'OnLoadScene']

    def __init__(self, scene = None, solarsystemID = None):
        sm.RegisterNotify(self)
        self._SetupRoute(scene, solarsystemID)

    def _SetupRoute(self, scene, solarsystemID):
        if not self.IsEnabled():
            return
        self.route = None
        self.scene = scene
        if self.scene is None:
            scene = self.GetScene()
        if solarsystemID is None:
            solarsystemID = session.solarsystemid
        self.CreateLineSet(scene, solarsystemID)

    def IsEnabled(self):
        return settings.user.ui.Get('routeVisualizationEnabled', True)

    def ToggleRouteVisualization(self):
        enabled = not self.IsEnabled()
        settings.user.ui.Set('routeVisualizationEnabled', enabled)
        if enabled:
            self._SetupRoute(self.GetScene(), session.solarsystemid)
        else:
            self.Cleanup()

    def OnLoadScene(self, scene, key):
        if not self.IsEnabled():
            return
        if key != 'default':
            return
        self.Cleanup()
        self._SetupRoute(scene, session.solarsystemid)

    def OnDestinationSet(self, destination):
        self.Update()

    def Update(self):
        """
        Cleanup the old one and make a new line set
        """
        self.Cleanup()
        scene = self.GetScene()
        if scene and self.IsEnabled():
            self.CreateLineSet(scene, session.solarsystemid)

    def GetScene(self):
        return self.scene or sm.GetService('sceneManager').GetRegisteredScene('default')

    def Cleanup(self):
        if self.route:
            scene = self.GetScene()
            if scene:
                scene.backgroundObjects.fremove(self.route)
        self.scene = None

    def CreateLineSet(self, scene, solarsystemID):
        if scene is None:
            scene = self.GetScene()
        if not hasattr(scene, 'backgroundObjects'):
            return
        if not scene:
            log.LogWarn('RouteVisualizer - No scene')
            return
        waypoints = sm.GetService('starmap').GetDestinationPath()
        if None in waypoints:
            return
        lineSet = trinity.EveCurveLineSet()
        lineSet.scaling = (1.0, 1.0, 1.0)
        tex2D1 = trinity.TriTexture2DParameter()
        tex2D1.name = 'TexMap'
        tex2D1.resourcePath = 'res:/texture/global/lineSolid.dds'
        lineSet.lineEffect.resources.append(tex2D1)
        tex2D2 = trinity.TriTexture2DParameter()
        tex2D2.name = 'OverlayTexMap'
        tex2D2.resourcePath = 'res:/UI/Texture/Planet/link.dds'
        lineSet.lineEffect.resources.append(tex2D2)
        topTransform = trinity.EveTransform()
        topTransform.name = 'Route'
        topTransform.modifier = 2
        transform = trinity.EveTransform()
        topTransform.children.append(transform)
        transform.name = 'AutoPilotRoute'
        transform.children.append(lineSet)
        scene.backgroundObjects.append(topTransform)
        here = sm.StartService('map').GetItem(solarsystemID)
        if not here:
            log.LogWarn('RouteVisualizer - No _here_')
            return
        itemInfo = []
        for sid in waypoints:
            if not util.IsSolarSystem(sid):
                continue
            item = sm.StartService('map').GetItem(sid)
            position = (-item.x + here.x, -item.y + here.y, item.z - here.z)
            position = geo2.Vec3Normalize(position)
            position = geo2.Vec3Scale(position, 1000)
            security = item.security
            itemInfo.append((position, security))

        waypointDisplayCount = 15
        itemInfo = itemInfo[0:min(waypointDisplayCount, len(itemInfo))]
        securityColors = sm.GetService('map').GetSecColorList()
        baseAlpha = 0.25
        for i, each in enumerate(itemInfo):
            length = len(itemInfo)
            if i < length - 1:
                colorIndex1 = int(round(max(itemInfo[i][1], 0), 1) * 10)
                color1 = securityColors[colorIndex1]
                alpha1 = 1 - float(i) / len(itemInfo)
                alpha1 *= baseAlpha
                lineColor1 = (color1.r,
                 color1.g,
                 color1.b,
                 alpha1)
                colorIndex2 = int(round(max(itemInfo[i + 1][1], 0), 1) * 10)
                color2 = securityColors[colorIndex2]
                alpha2 = 1 - float(i + 1) / len(itemInfo)
                alpha2 *= baseAlpha
                lineColor2 = (color2.r,
                 color2.g,
                 color2.b,
                 alpha2)
                lineWidth = 3
                l1 = lineSet.AddStraightLine(itemInfo[i][0], lineColor1, itemInfo[i + 1][0], lineColor2, lineWidth)
                animationColor = (0.12, 0.12, 0.12, 0.6)
                lineSet.ChangeLineAnimation(l1, animationColor, -0.35, 1)

        lineSet.SubmitChanges()
        self.route = topTransform
