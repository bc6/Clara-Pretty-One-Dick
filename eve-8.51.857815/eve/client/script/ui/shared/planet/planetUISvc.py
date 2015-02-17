#Embedded file name: eve/client/script/ui/shared/planet\planetUISvc.py
"""
This service handles UI specific functionality for the planetay interaction feature.
All persistence or server interaction should be delegated to the planetSvc.

map UI layer is shared with star and system map... planet map?
Responsibility:
    - scene
    - graphics
"""
import math
import service
import carbonui.const as uiconst
import form
import trinity
import blue
import uiprimitives
import uicontrols
import uthread
import log
import localization
import geo2
import evegraphics.settings as gfxsettings
from eve.client.script.environment.spaceObject.planet import Planet
from .planetCommon import PLANET_TEXTURE_SIZE, PLANET_ZOOM_MAX, PLANET_SCALE
from .planetCommon import PLANET_RESOURCE_TEX_WIDTH, PLANET_RESOURCE_TEX_HEIGHT, AMBIENT_SOUNDS
from PlanetResources import builder
from pychartdir import XYChart, Transparent, NoValue
from eve.common.script.planet.planetUtil import MATH_2PI
from eve.common.script.util.planetCommon import SurfacePoint
from .curveLineDrawer import CurveLineDrawer
from .myPinManager import MyPinManager
from .otherPinManager import OtherPinManager
from .eventManager import EventManager
SQRT_NUM_SAMPLES = 80
LINER_BLENDING_RATIO = 0.8
RESOURCE_BASE_COLOR = (1, 1, 1, 0.175)

class ResourceRenderAbortedError(Exception):
    pass


class PlanetUISvc(service.Service):
    __guid__ = 'svc.planetUI'
    __notifyevents__ = ['OnGraphicSettingsChanged',
     'OnSetDevice',
     'OnUIRefresh',
     'ProcessUIRefresh']
    __exportedcalls__ = {}
    __servicename__ = 'planetUI'
    __displayname__ = 'Planet UI Client Service'
    __update_on_reload__ = 0

    def Run(self, memStream = None):
        self.state = service.SERVICE_START_PENDING
        self.LogInfo('Starting Planet UI Client Svc')
        uicore.layer.planet.Flush()
        self.planetID = None
        self.oldPlanetID = None
        self.format = trinity.PIXEL_FORMAT.B8G8R8A8_UNORM
        self.busy = 0
        self.isLoadingResource = False
        self.selectedResourceTypeID = None
        self.minimizedWindows = []
        self.planetAccessRequired = None
        self.currSphericalHarmonic = None
        self.spherePinsPendingLoad = []
        self.spherePinLoadThread = None
        self.inEditMode = False
        self.planet = None
        self.curveLineDrawer = CurveLineDrawer()
        self.myPinManager = None
        self.otherPinManager = None
        self.eventManager = None
        self.planetRoot = None
        self.trinityPlanet = None
        self.planetTransform = None
        self.resourceLayer = None
        self.pinTransform = None
        self.pinOthersTransform = None
        self.orbitalObjectTransform = None
        self.modeController = None
        self.scanController = None
        self.currentContainer = None
        self.planetNav = None
        self.planetUIContainer = uiprimitives.Container(parent=uicore.layer.planet, name='planetUIContainer', align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.state = service.SERVICE_RUNNING
        self.LogInfo('Planet UI Client Svc Started')

    def Stop(self, memStream = None):
        if trinity.device is None:
            return
        self.LogInfo('service is stopping')
        if self.spherePinLoadThread:
            self.spherePinLoadThread.kill()
            self.spherePinLoadThread = None
        self.Reset()

    def Reset(self):
        """
        reset all variables when entering/exiting planet UI mode
        """
        self.LogInfo('PlanetUISvc Reset')
        self.minimizedWindows = []
        self.CleanScene()
        sm.ScatterEvent('OnPlanetUIReset')

    def CleanScene(self):
        """
        Clean up the scene when changing planets and exiting planet UI
        """
        self.LogInfo('CleanScene')
        self.CloseCurrentlyOpenContainer()
        self.planetUIContainer.Flush()
        if self.planetTransform is not None:
            del self.planetTransform.children[:]
        if self.planetRoot is not None:
            del self.planetRoot.children[:]
        self.planetTransform = None
        self.pinTransform = None
        self.pinOthersTransform = None
        if self.trinityPlanet is not None:
            self.trinityPlanet.model = None
            self.trinityPlanet = None
        self.planetRoot = None
        self.planetNav = None
        if self.scanController is not None:
            self.scanController.Close()
            self.scanController = None
        self.resourceLayer = None
        self.isLoadingResource = False

    def CleanView(self):
        if self.planetTransform is not None:
            self.planetTransform.children.remove(self.pinTransform)
            self.planetTransform.children.remove(self.pinOthersTransform)
        if self.eventManager:
            self.eventManager.OnPlanetViewClosed()
        if self.myPinManager:
            self.myPinManager.OnPlanetViewClosed()
        if self.otherPinManager:
            self.otherPinManager.OnPlanetViewClosed()
        self.CloseCurrentlyOpenContainer()
        self.planetUIContainer.Flush()
        self.busy = 0
        self.StopSpherePinLoadThread()
        del self.pinTransform
        self.pinTransform = None
        del self.pinOthersTransform
        self.pinOthersTransform = None
        if self.scanController is not None:
            self.scanController.Close()
            self.scanController = None
        self.resourceLayer = None

    def ProcessUIRefresh(self):
        self.oldPlanetID = None
        if sm.GetService('viewState').IsViewActive('planet'):
            self.oldPlanetID = self.planetID
            self.planetID = None
        self.Reset()

    def OnUIRefresh(self):
        if self.oldPlanetID:
            self.Open(self.oldPlanetID)
            self.oldPlanetID = None

    def MinimizeWindows(self):
        """
            Minimize windows that are not related to the map. Currently it's only the
            lobby which is minimized.
        """
        lobby = form.Lobby.GetIfOpen()
        if lobby and not lobby.destroyed and lobby.state != uiconst.UI_HIDDEN and not lobby.IsMinimized() and not lobby.IsCollapsed():
            lobby.Minimize()
            self.minimizedWindows.append(form.Lobby.default_windowID)

    def Open(self, planetID):
        """
        Open the planet mode with a particular planet
        if no planetID is supplied no planet is rendered
        """
        sm.GetService('viewState').ActivateView('planet', planetID=planetID)

    def ExitView(self):
        sm.GetService('viewState').CloseSecondaryView('planet')

    def _Open(self, planetID):
        mapSvc = sm.GetService('map')
        planetData = mapSvc.GetPlanetInfo(planetID)
        planetChanged = planetID != self.planetID
        oldPlanetID = self.planetID
        self.planetID = planetID
        self.typeID = planetData.typeID
        self.solarSystemID = planetData.solarSystemID
        try:
            self.InitUI(planetChanged)
        except:
            self.Stop()
            self.Run()
            raise

        sm.GetService('audio').SendUIEvent('wise:/msg_pi_general_opening_play')
        sm.ScatterEvent('OnPlanetViewChanged', planetID, oldPlanetID)
        try:
            self.planetNav.camera.Open()
        except AttributeError:
            pass

        sm.StartService('audio').SendUIEvent(unicode(AMBIENT_SOUNDS[self.typeID].start))
        self.planetAccessRequired = session.solarsystemid2 == self.solarSystemID or sm.GetService('planetSvc').IsPlanetColonizedByMe(planetID)

    def Close(self, clearAll = True):
        """
        TODO: most of this could be handled by a view manager, right
        The returning of True/False is an ugly hack for the case where you open up the
        map while in edit mode or switch to another planet while already in edit mode.
        """
        if getattr(self, 'busy', 0):
            return True
        self.busy = 1
        try:
            self.planetNav.camera.Close()
        except AttributeError:
            pass

        if hasattr(self, 'typeID'):
            sm.StartService('audio').SendUIEvent(unicode(AMBIENT_SOUNDS[self.typeID].stop))
        if len(self.minimizedWindows) > 0:
            for windowID in self.minimizedWindows:
                wnd = uicontrols.Window.GetIfOpen(windowID=windowID)
                if wnd and wnd.IsMinimized():
                    wnd.Maximize()

            self.minimizedWindows = []
        if getattr(self, 'planetNav', None):
            settings.char.ui.Set('planet_camera_zoom', self.planetNav.zoom)
        else:
            settings.char.ui.Set('planet_camera_zoom', 1.0)
        sm.GetService('sceneManager').SetRegisteredScenes('default')
        self.busy = 0
        if self.eventManager:
            self.eventManager.OnPlanetViewClosed()
        if self.myPinManager:
            self.myPinManager.OnPlanetViewClosed()
        if self.otherPinManager:
            self.otherPinManager.OnPlanetViewClosed()
        self.CleanScene()
        self.StopSpherePinLoadThread()
        sm.ScatterEvent('OnPlanetViewChanged', None, self.planetID)
        self.LogPlanetAccess()
        self.planetID = None
        self.planet = None
        self.selectedResourceTypeID = None
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_general_closing_play')
        if clearAll:
            self.cameraScene = None
            self.planetScene = None
            sm.GetService('sceneManager').UnregisterScene('planet')
            sm.GetService('sceneManager').UnregisterCamera('planet')
            sm.GetService('camera').ClearCameraParent('planet')
        return True

    def InitUI(self, planetChanged):
        """
        initialize planerary interaction UI.
        create scene if requried
        update planet if required
        """
        self.LogInfo('Initializing UI')
        self.StartLoadingBar('planet_ui_init', localization.GetByLabel('UI/PI/Common/PlanetMode'), localization.GetByLabel('UI/PI/Common/LoadingPlanetResources'), 5)
        try:
            sm.GetService('planetSvc').GetPlanet(self.planetID)
        except UserError:
            self.StopLoadingBar('planet_ui_init')
            raise
        except Exception:
            eve.Message('PlanetLoadingFailed', {'planet': (const.UE_LOCID, self.planetID)})
            self.StopLoadingBar('planet_ui_init')
            log.LogException()
            return

        if not sm.GetService('viewState').IsViewActive('planet'):
            self.MinimizeWindows()
        newScene = False
        if self.planetRoot is None or planetChanged:
            self.CreateScene()
            newScene = True
        self.UpdateLoadingBar('planet_ui_init', localization.GetByLabel('UI/PI/Common/PlanetMode'), localization.GetByLabel('UI/PI/Common/LoadingPlanetResources'), 1, 4)
        sm.GetService('sceneManager').SetRegisteredScenes('planet')
        self.UpdateLoadingBar('planet_ui_init', localization.GetByLabel('UI/PI/Common/PlanetMode'), localization.GetByLabel('UI/PI/Common/LoadingPlanetResources'), 2, 4)
        self.SetPlanet()
        self.UpdateLoadingBar('planet_ui_init', localization.GetByLabel('UI/PI/Common/PlanetMode'), localization.GetByLabel('UI/PI/Common/LoadingPlanetResources'), 3, 4)
        self.LoadPI(newScene)
        uthread.new(self.FocusCameraOnCommandCenter, 3.0)
        self.UpdateLoadingBar('planet_ui_init', localization.GetByLabel('UI/PI/Common/PlanetMode'), localization.GetByLabel('UI/PI/Common/LoadingPlanetResources'), 4, 4)
        self.StopLoadingBar('planet_ui_init')

    def LoadPI(self, newScene = True):
        self.InitTrinityTransforms()
        self.InitUIContainers()
        self.InitLinesets()
        if self.myPinManager:
            self.myPinManager.Close()
        self.myPinManager = MyPinManager()
        if self.otherPinManager:
            self.otherPinManager.Close()
        self.otherPinManager = OtherPinManager()
        if self.eventManager:
            self.eventManager.Close()
        self.eventManager = EventManager()
        self.planetNav.Startup()
        if newScene:
            self.planetNav.zoom = 1.0
        else:
            self.planetNav.zoom = settings.char.ui.Get('planet_camera_zoom', 1.0)
        self.zoom = sm.GetService('planetUI').planetNav.camera.zoom
        self.eventManager.OnPlanetViewOpened()
        self.myPinManager.OnPlanetViewOpened()
        self.otherPinManager.OnPlanetViewOpened()

    def SetModeController(self, modeController):
        self.modeController = modeController

    def InitUIContainers(self):
        """ 
        Set up UI containers
        """
        self.pinInfoParent = uiprimitives.Container(parent=self.planetUIContainer, name='pinInfoParent', align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.planetNav = sm.GetService('viewState').GetView('planet').layer

    def InitTrinityTransforms(self):
        self.pinTransform = trinity.EveTransform()
        self.pinTransform.name = 'myPins'
        self.pinOthersTransform = trinity.EveTransform()
        self.pinOthersTransform.name = 'othersPins'
        self.planetTransform.children.append(self.pinTransform)
        self.planetTransform.children.append(self.pinOthersTransform)

    def InitLinesets(self):
        self.curveLineDrawer.CreateLineSet('links', self.pinTransform, 'res:/UI/Texture/Planet/link.dds', scale=1.009)
        self.curveLineDrawer.CreateLineSet('linksExtraction', self.pinTransform, 'res:/UI/Texture/Planet/link.dds', scale=1.001)
        self.curveLineDrawer.CreateLineSet('rubberLink', self.pinTransform, 'res:/UI/Texture/Planet/link.dds', scale=1.0089)
        self.curveLineDrawer.CreateLineSet('otherLinks', self.pinOthersTransform, 'res:/UI/Texture/Planet/link.dds', scale=1.0049)

    def CreateRenderTarget(self):
        textureQuality = gfxsettings.Get(gfxsettings.GFX_TEXTURE_QUALITY)
        self.maxSizeLimit = size = PLANET_TEXTURE_SIZE >> textureQuality
        rt = None
        while rt is None or not rt.isValid:
            rt = trinity.Tr2RenderTarget(2 * size, size, 0, self.format)
            if not rt.isValid:
                if size < 2:
                    return
                self.maxSizeLimit = size = size / 2
                rt = None

        self.LogInfo('CreateRenderTarget textureQuality', textureQuality, 'size', size, 'maxSizeLimit', self.maxSizeLimit)
        return rt

    def CreateScene(self):
        self.LogInfo('CreateScene')
        self.planetScene = self.GetPlanetScene()
        self.planetRoot = trinity.EveRootTransform()
        self.planetRoot.name = 'planetRoot'
        self.planetScene.objects.append(self.planetRoot)
        self.LoadPlanet()
        self.LoadOrbitalObjects(self.planetScene)
        camera = trinity.EveCamera()
        sm.GetService('sceneManager').RegisterCamera('planet', camera)
        sm.GetService('sceneManager').RegisterScene(self.planetScene, 'planet')
        camera.translationFromParent = PLANET_ZOOM_MAX

    def GetScene(self):
        """
        Based on magical code from gameui to produce the correct inflight base scene.
        """
        _, regionID, constellationID, solarSystemID, _ = sm.GetService('map').GetParentLocationID(self.solarSystemID)
        scene = sm.GetService('sceneManager').GetScene(location=(solarSystemID, constellationID, regionID))
        return scene

    def GetPlanetScene(self):
        """
        NOTE: this is based on the evePhotoService way of getting the base scene scene with nebula.
        """
        scenepath = self.GetScene()
        scene = trinity.Load(scenepath)
        scene.backgroundRenderingEnabled = True
        return scene

    def LoadPlanet(self):
        self.LogInfo('LoadPlanet planet', self.planetID, 'type', self.typeID, 'system', self.solarSystemID)
        planet = Planet()
        objType = cfg.invtypes.Get(self.typeID)
        graphicFile = objType.GraphicFile()
        planet.typeData['graphicFile'] = graphicFile
        planet.typeID = self.typeID
        planet.LoadPlanet(self.planetID, forPhotoService=True, rotate=False, hiTextures=True)
        self.trinityPlanet = planet
        if planet.model is None or planet.model.highDetail is None:
            return
        planetTransform = trinity.EveTransform()
        planetTransform.name = 'planet'
        planetTransform.scaling = (PLANET_SCALE, PLANET_SCALE, PLANET_SCALE)
        planetTransform.children.append(planet.model.highDetail)
        self.PreProcessPlanet()
        scene = self.planetScene
        trinity.WaitForResourceLoads()
        for t in planet.model.highDetail.children:
            if t.mesh is not None:
                if len(t.mesh.transparentAreas) > 0:
                    t.sortValueMultiplier = 2.0

        scene.sunDirection = (0.0, 0.0, 1.0)
        scene.sunDiffuseColor = (1.0, 1.0, 1.0, 1.0)
        self.planetTransform = planetTransform
        self.planetRoot.children.append(self.planetTransform)

    def LoadOrbitalObjects(self, scene):
        """
            Load any significant orbital objects into this scene.
        """
        orbitalObjects = sm.GetService('planetInfo').GetOrbitalsForPlanet(self.planetID, const.groupPlanetaryCustomsOffices)
        park = sm.GetService('michelle').GetBallpark()
        addedObjects = []
        for orbitalObjectID in orbitalObjects:
            invItem = park.GetInvItem(orbitalObjectID)
            fileName = None
            if cfg.invtypes.Get(invItem.typeID).graphicID is not None:
                if type(cfg.invtypes.Get(invItem.typeID).graphicID) != type(0):
                    raise RuntimeError('NeedGraphicIDNotMoniker', invItem.itemID)
                if cfg.invtypes.Get(invItem.typeID).Graphic():
                    fileName = cfg.invtypes.Get(invItem.typeID).GraphicFile()
                    if not (fileName.lower().endswith('.red') or fileName.lower().endswith('.blue')):
                        filenameAndTurretType = fileName.split(' ')
                        fileName = filenameAndTurretType[0]
            if fileName is None:
                self.LogError('Error: Object type %s has invalid graphicFile, using graphicID: %s' % (invItem.typeID, cfg.invtypes.Get(invItem.typeID).graphicID))
                continue
            tryFileName = fileName.replace(':/Model', ':/dx9/Model').replace('.blue', '.red')
            tryFileName = tryFileName.replace('.red', '_UI.red')
            model = None
            if tryFileName is not None:
                try:
                    model = blue.resMan.LoadObject(tryFileName)
                except:
                    model = None

                if model is None:
                    self.LogError('Was looking for:', tryFileName, 'but it does not exist!')
            if model is None:
                try:
                    model = blue.resMan.LoadObject(fileName)
                except:
                    model = None

            if not model:
                log.LogError('Could not load model for orbital object. FileName:', fileName, ' id:', invItem.itemID, ' typeID:', getattr(invItem, 'typeID', '?unknown?'))
                if invItem is not None and hasattr(invItem, 'typeID'):
                    log.LogError('Type is:', cfg.invtypes.Get(invItem.typeID).typeName)
                continue
            model.name = '%s' % invItem.itemID
            model.display = 0
            model.scaling = (0.002, 0.002, 0.002)
            addedObjects.append(model)
            orbitRoot = trinity.EveTransform()
            orbitRoot.children.append(model)
            inclinationRoot = trinity.EveTransform()
            inclinationRoot.children.append(orbitRoot)
            orbitalInclination = orbitalObjectID / math.pi % (math.pi / 4.0) - math.pi / 8.0
            if orbitalInclination <= 0.0:
                orbitalInclination -= math.pi / 8.0
            else:
                orbitalInclination += math.pi / 8.0
            inclinationRoot.rotation = geo2.QuaternionRotationSetYawPitchRoll(0.0, orbitalInclination, 0.0)
            rotationCurveSet = trinity.TriCurveSet()
            rotationCurveSet.playOnLoad = False
            rotationCurveSet.Stop()
            rotationCurveSet.scaledTime = 0.0
            rotationCurveSet.scale = 0.25
            orbitRoot.curveSets.append(rotationCurveSet)
            ypr = trinity.TriYPRSequencer()
            ypr.YawCurve = trinity.TriScalarCurve()
            ypr.YawCurve.extrapolation = trinity.TRIEXT_CYCLE
            ypr.YawCurve.AddKey(0.0, 0.0, 0.0, 0.0, trinity.TRIINT_LINEAR)
            ypr.YawCurve.AddKey(200.0, 360.0, 0.0, 0.0, trinity.TRIINT_LINEAR)
            ypr.YawCurve.Sort()
            rotationCurveSet.curves.append(ypr)
            binding = trinity.TriValueBinding()
            binding.sourceObject = ypr
            binding.sourceAttribute = 'value'
            binding.destinationObject = orbitRoot
            binding.destinationAttribute = 'rotation'
            rotationCurveSet.bindings.append(binding)
            rotationCurveSet.Play()
            model.translation = (0.0, 0.0, 1500.0)
            model.rotation = geo2.QuaternionRotationSetYawPitchRoll(math.pi, 0.0, 0.0)
            scene.objects.append(inclinationRoot)
            ls = trinity.EveCurveLineSet()
            ls.scaling = (1.0, 1.0, 1.0)
            tex2D1 = trinity.TriTexture2DParameter()
            tex2D1.name = 'TexMap'
            tex2D1.resourcePath = 'res:/UI/Texture/Planet/link.dds'
            ls.lineEffect.resources.append(tex2D1)
            tex2D2 = trinity.TriTexture2DParameter()
            tex2D2.name = 'OverlayTexMap'
            tex2D2.resourcePath = 'res:/UI/Texture/Planet/link.dds'
            ls.lineEffect.resources.append(tex2D2)
            lineColor = (1.0, 1.0, 1.0, 0.05)
            p1 = SurfacePoint(0.0, 0.0, -1500.0, 1000.0)
            p2 = SurfacePoint(5.0, 0.0, 1498.0, 1000.0)
            l1 = ls.AddSpheredLineCrt(p1.GetAsXYZTuple(), lineColor, p2.GetAsXYZTuple(), lineColor, (0.0, 0.0, 0.0), 3.0)
            p1 = SurfacePoint(0.0, 0.0, -1500.0, 1000.0)
            p2 = SurfacePoint(-5.0, 0.0, 1498.0, 1000.0)
            l2 = ls.AddSpheredLineCrt(p1.GetAsXYZTuple(), lineColor, p2.GetAsXYZTuple(), lineColor, (0.0, 0.0, 0.0), 3.0)
            animationColor = (0.3, 0.3, 0.3, 0.5)
            ls.ChangeLineAnimation(l1, animationColor, 0.25, 1.0)
            ls.ChangeLineAnimation(l2, animationColor, -0.25, 1.0)
            ls.ChangeLineSegmentation(l1, 100)
            ls.ChangeLineSegmentation(l2, 100)
            ls.SubmitChanges()
            orbitRoot.children.append(ls)

        trinity.WaitForResourceLoads()
        for model in addedObjects:
            model.display = 1

    def GetCurrentPlanet(self):
        if not self.planetID:
            return None
        return sm.GetService('planetSvc').GetPlanet(self.planetID)

    def PreProcessPlanet(self):
        renderTarget = self.CreateRenderTarget()
        self.trinityPlanet.DoPreProcessEffect(self.maxSizeLimit, self.format, renderTarget)

    def StartLoadingBar(self, key, tile, action, total):
        """
        Wrapping the loading bar to prevent multiple conflicting loading bars
        If no loading bar is active we can start a new one otherwise request is ignored
        """
        if getattr(self, 'loadingBarActive', None) is None:
            sm.GetService('loading').ProgressWnd(tile, action, 0, total)
            self.loadingBarActive = key

    def UpdateLoadingBar(self, key, tile, action, part, total):
        """
        Only allow update to loading bar if the key maches the active loading bar
        """
        if getattr(self, 'loadingBarActive', None) == key:
            sm.GetService('loading').ProgressWnd(tile, action, part, total)

    def StopLoadingBar(self, key):
        """
        Only allow loading bar to be stopped if the key maches the active loading bar
        """
        if getattr(self, 'loadingBarActive', None) == key:
            sm.GetService('loading').StopCycle()
            self.loadingBarActive = None

    def OnSetDevice(self):
        if sm.GetService('viewState').IsViewActive('planet'):
            self.planetNav.camera.ManualZoom(0.0)

    def OnGraphicSettingsChanged(self, changes):
        """
        Reload the planet graphics since they can corrupt when the are altered
        """
        changed = gfxsettings.GFX_TEXTURE_QUALITY in changes or gfxsettings.GFX_SHADER_QUALITY in changes
        if sm.GetService('viewState').IsViewActive('planet') and self.trinityPlanet is not None and changed:
            self.PreProcessPlanet()
            if self.selectedResourceTypeID is not None:
                self.ShowResource(self.selectedResourceTypeID)

    def ShowResource(self, resourceTypeID):
        """Show resource with typeID on the planet surface"""
        self.LogInfo('ShowResource', resourceTypeID)
        oldResourceTypeID = self.selectedResourceTypeID
        self.selectedResourceTypeID = resourceTypeID
        if resourceTypeID is None:
            if self.resourceLayer is not None:
                self.resourceLayer.display = False
            self.otherPinManager.HideOtherPlayersExtractors()
            if self.modeController is not None and hasattr(self.modeController, 'resourceControllerTab') and self.modeController.resourceControllerTab is not None:
                self.modeController.resourceControllerTab.ResourceSelected(resourceTypeID)
        elif not getattr(self, 'isLoadingResource', False):
            if self.modeController is not None and hasattr(self.modeController, 'resourceControllerTab') and self.modeController.resourceControllerTab is not None:
                self.modeController.resourceControllerTab.ResourceSelected(resourceTypeID)
            self.isLoadingResource = True
            uthread.new(self._ShowResource, resourceTypeID)
            self.modeController.resourceControllerTab.ResourceSelected(resourceTypeID)
        elif oldResourceTypeID != resourceTypeID:
            while self.isLoadingResource:
                blue.pyos.synchro.SleepWallclock(50)

            if resourceTypeID == self.selectedResourceTypeID:
                self.ShowResource(resourceTypeID)

    def _ShowResource(self, resourceTypeID):
        self.LogInfo('_ShowResource', resourceTypeID)
        inRange = False
        try:
            inRange, texture = self.GetResourceAndRender(resourceTypeID)
            if self.planetTransform is not None:
                self.EnableResourceLayer()
                self.SetResourceTexture(texture)
        except ResourceRenderAbortedError:
            pass
        finally:
            self.isLoadingResource = False
            if self.modeController is not None and hasattr(self.modeController, 'resourceControllerTab') and self.modeController.resourceControllerTab is not None:
                self.modeController.resourceControllerTab.StopLoadingResources(resourceTypeID)
            if self.otherPinManager is not None and inRange:
                self.otherPinManager.RenderOtherPlayersExtractors(resourceTypeID)

    def EnableResourceLayer(self):
        """Enables the resource layer and sets it up if required"""
        if self.planetTransform is not None:
            if self.resourceLayer is None:
                self.LogInfo('_ShowResource no resourceLayer found. Loading resource layer')
                self.resourceLayer = trinity.Load('res:/dx9/model/worldobject/planet/uiplanet.red')
                trinity.WaitForResourceLoads()
                effect = self.resourceLayer.mesh.transparentAreas[0].effect
                for resource in effect.resources:
                    if resource.name == 'ColorRampMap':
                        resource.resourcePath = 'res:/dx9/model/worldobject/planet/resource_colorramp.dds'

                for param in effect.parameters:
                    if param.name == 'MainColor':
                        param.value = RESOURCE_BASE_COLOR
                    elif param.name == 'ResourceTextureInfo':
                        param.value = (PLANET_RESOURCE_TEX_WIDTH,
                         PLANET_RESOURCE_TEX_HEIGHT,
                         0,
                         0)

                offset = trinity.Tr2FloatParameter()
                offset.name = 'HeatOffset'
                offset.value = 0.0
                effect.parameters.append(offset)
                stretch = trinity.Tr2FloatParameter()
                stretch.name = 'HeatStretch'
                stretch.value = 1.0
                effect.parameters.append(stretch)
                self.planetTransform.children.append(self.resourceLayer)
            else:
                self.resourceLayer.display = True
            low, hi = settings.char.ui.Get('planet_resource_display_range', (0.0, 1.0))
            self.SetResourceDisplayRange(low, hi)

    def GetResourceTexture(self):
        effect = self.resourceLayer.mesh.transparentAreas[0].effect
        for resource in effect.resources:
            if resource.name == 'ResourceDistMap':
                return resource

    def GetResourceAndRender(self, resourceTypeID):
        """
        Get the spherical harmonic from planetSvc going to server if nessesasary.
        We render the SH in slices yielding in between so we won't stall the client.
        We check if we are still rendering the correct resournce whenever we have yielded the thread.
        """
        self.LogInfo('GetResourceAndRender resourceTypeID', resourceTypeID)
        planet = sm.GetService('planetSvc').GetPlanet(self.planetID)
        inRange, sh = planet.GetResourceData(resourceTypeID)
        self.currSphericalHarmonic = sh
        sh = builder.CopySH(sh)
        builder.ScaleSH(sh, 1.0 / const.planetResourceMaxValue)
        chart = self.ChartResourceLayer(sh)
        buf = chart.makeChart2(chart.PNG)
        if resourceTypeID != self.selectedResourceTypeID:
            raise ResourceRenderAbortedError
        bmp = trinity.Tr2HostBitmap(PLANET_RESOURCE_TEX_WIDTH, PLANET_RESOURCE_TEX_HEIGHT, 1, trinity.PIXEL_FORMAT.B8G8R8X8_UNORM)
        bmp.LoadFromPngInMemory(buf)
        texture = trinity.TriTextureRes()
        if resourceTypeID != self.selectedResourceTypeID:
            raise ResourceRenderAbortedError
        texture.CreateFromHostBitmap(bmp)
        if resourceTypeID != self.selectedResourceTypeID:
            raise ResourceRenderAbortedError
        return (inRange, texture)

    def GetCurrentResourceValueAt(self, phi, theta):
        if not self.currSphericalHarmonic:
            return None
        return builder.GetValueAt(self.currSphericalHarmonic, phi, theta)

    def CreateChartFromSamples(self, width, height, dataX, dataY, dataZ, rangeXY = None):
        """Generate a chart based on sample data"""
        startTime = blue.os.GetWallclockTime()
        if rangeXY:
            minX, minY, maxX, maxY = rangeXY
        else:
            minX = min(dataX)
            maxX = max(dataX)
            minY = min(dataY)
            maxY = max(dataY)
        maxZ = max(dataZ)
        minZ = min(dataZ)
        chart = XYChart(width, height)
        chart.setPlotArea(0, 0, width, height, Transparent, Transparent, Transparent, Transparent, Transparent)
        layer = chart.addContourLayer(dataX, dataY, dataZ)
        chart.xAxis().setLinearScale(minX, maxX, NoValue)
        chart.xAxis().setColors(Transparent)
        chart.yAxis().setLinearScale(maxY, minY, NoValue)
        chart.yAxis().setColors(Transparent)
        colorAxis = layer.colorAxis()
        colorAxis.setColorGradient(True, [long(max(0, minZ)) << 24, long(min(255, maxZ)) << 24])
        layer.setSmoothInterpolation(True)
        layer.setContourColor(Transparent)
        self.LogInfo('CreateChartFromSamples width', width, 'height', height, 'render time', float(blue.os.GetWallclockTime() - startTime) / const.SEC, 'seconds')
        return chart

    def GenerateSamplePoints(self, sqrtNumSamples):
        self.LogInfo('GenerateSamplePoints creating', sqrtNumSamples ** 2, 'samples for chart generation')
        thetaSamples = []
        phiSamples = []
        scale = 1.0 / (sqrtNumSamples - 1)
        for a in xrange(sqrtNumSamples):
            y = a * scale
            phi = MATH_2PI * y
            for b in xrange(sqrtNumSamples):
                x = b * scale
                linear = math.pi * x * LINER_BLENDING_RATIO
                theta = math.acos(1 - x * 2) * (1 - LINER_BLENDING_RATIO) + linear
                thetaSamples.append(theta)
                phiSamples.append(phi)

        return (thetaSamples, phiSamples)

    def ChartResourceLayer(self, resSH):
        resourceTypeID = self.selectedResourceTypeID
        if not hasattr(self, 'thetaSamples'):
            self.thetaSamples, self.phiSamples = self.GenerateSamplePoints(SQRT_NUM_SAMPLES)
        data = []
        for i in xrange(len(self.thetaSamples)):
            value = builder.GetValueAt(resSH, self.phiSamples[i], self.thetaSamples[i])
            data.append(value)
            blue.pyos.BeNice()
            if resourceTypeID != self.selectedResourceTypeID:
                raise ResourceRenderAbortedError

        chart = self.CreateChartFromSamples(PLANET_RESOURCE_TEX_WIDTH, PLANET_RESOURCE_TEX_HEIGHT, self.phiSamples, self.thetaSamples, data)
        return chart

    def SetResourceTexture(self, texture):
        effect = self.resourceLayer.mesh.transparentAreas[0].effect
        for resource in effect.resources:
            if resource.name == 'ResourceDistMap':
                resource.SetResource(texture)

    def SetResourceDisplayRange(self, low, hi):
        """adjust the resource layer display range"""
        settings.char.ui.Set('planet_resource_display_range', (low, hi))
        stretch = 1.0 / (hi - low)
        offset = -low * stretch
        if self.planetTransform is not None:
            if self.resourceLayer is not None:
                effect = self.resourceLayer.mesh.transparentAreas[0].effect
                for param in effect.parameters:
                    if param.name == 'HeatStretch':
                        param.value = stretch
                    elif param.name == 'HeatOffset':
                        param.value = offset

    def OpenPlanetCustomsOfficeImportWindow(self, customsOfficeID, spaceportPinID = None):
        wnd = form.PlanetaryImportExportUI.GetIfOpen()
        if wnd:
            if wnd.customsOfficeID != customsOfficeID or wnd.spaceportPinID != spaceportPinID:
                wnd.CloseByUser()
                wnd = None
            else:
                wnd.Maximize()
        if not wnd:
            form.PlanetaryImportExportUI.Open(customsOfficeID=customsOfficeID, spaceportPinID=spaceportPinID)

    def OpenUpgradeWindow(self, orbitalID):
        wnd = form.OrbitalMaterialUI.GetIfOpen()
        if wnd:
            if wnd.orbitalID != orbitalID:
                wnd.CloseByUser()
                wnd = None
            else:
                wnd.Maximize()
        if not wnd:
            form.OrbitalMaterialUI.Open(orbitalID=orbitalID)

    def OpenConfigureWindow(self, orbitalItem):
        wnd = form.OrbitalConfigurationWindow.GetIfOpen()
        if wnd:
            if getattr(wnd, 'orbitalID', None) != orbitalItem.itemID:
                wnd.CloseByUser()
                wnd = None
            else:
                wnd.Maximize()
        if not wnd:
            if getattr(orbitalItem, 'locationID', None) is None:
                orbitalItem.locationID = session.solarsystemid
            form.OrbitalConfigurationWindow.Open(orbitalItem=orbitalItem)

    def GetSurveyWindow(self, ecuPinID):
        wnd = form.PlanetSurvey.Open(ecuPinID=ecuPinID)
        if wnd.ecuPinID != ecuPinID:
            self.CloseSurveyWindow()
            self.myPinManager.EnterSurveyMode(ecuPinID)
        else:
            self.EnterSurveyMode(ecuPinID)
        return form.PlanetSurvey.GetIfOpen()

    def EnterSurveyMode(self, ecuPinID):
        if self.modeController is not None and hasattr(self.modeController, 'resourceControllerTab') and self.modeController.resourceControllerTab is not None:
            self.modeController.resourceControllerTab.EnterSurveyMode()

    def ExitSurveyMode(self):
        if self.modeController is not None and hasattr(self.modeController, 'resourceControllerTab') and self.modeController.resourceControllerTab is not None:
            self.modeController.resourceControllerTab.ExitSurveyMode()
        self.myPinManager.LockHeads()

    def CloseSurveyWindow(self):
        form.PlanetSurvey.CloseIfOpen()

    def GMShowResource(self, resourceTypeID, layer):
        self.LogInfo('GMShowResource', resourceTypeID, layer)
        planet = sm.GetService('planetSvc').GetPlanet(self.planetID)
        data = planet.remoteHandler.GMGetCompleteResource(resourceTypeID, layer)
        sh = builder.CreateSHFromBuffer(data.data, data.numBands)
        self.ShowSH(sh, scaleIt=layer == 'base')

    def ShowSH(self, sh, scaleIt = True):
        if scaleIt:
            builder.ScaleSH(sh, 1.0 / const.planetResourceMaxValue)
        chart = self.ChartResourceLayer(sh)
        buf = chart.makeChart2(chart.PNG)
        bmp = trinity.Tr2HostBitmap(PLANET_RESOURCE_TEX_WIDTH, PLANET_RESOURCE_TEX_HEIGHT, 1, trinity.TRIFMT_X8R8G8B8)
        bmp.LoadFromPngInMemory(buf)
        texture = trinity.TriTextureRes()
        texture.CreateFromHostBitmap(bmp)
        if self.planetTransform is not None:
            self.EnableResourceLayer()
            self.SetResourceTexture(texture)

    def GMCreateNuggetLayer(self, typeID):
        self.planet.remoteHandler.GMCreateNuggetLayer(self.planetID, typeID)
        self.GMShowResource(typeID, 'nuggets')

    def LogPlanetAccess(self):
        if self.planetAccessRequired is not None:
            planetAccessed = 1 if self.planetAccessRequired else 0
            myPlanets = sm.GetService('planetSvc').GetMyPlanets()
            colonized = 0
            for p in myPlanets:
                if p.planetID == self.planetID:
                    colonized = 1
                    break

            sm.GetService('infoGatheringSvc').LogInfoEvent(eventTypeID=const.infoEventPlanetUserAccess, itemID=session.charid, int_1=planetAccessed, int_2=1, int_3=colonized)
            self.planetAccessRequired = None

    def SetPlanet(self, planetID = None):
        pID = planetID
        if pID is None:
            pID = self.planetID
        self.planet = sm.GetService('planetSvc').GetPlanet(pID)
        self.planet.StartTicking()

    def OpenContainer(self, pin):
        """
        Open the pin UI container for the pin specified
        """
        self.CloseCurrentlyOpenContainer()
        self.currentContainer = pin.GetContainer(parent=self.planetUIContainer)
        self.currentExpandedPin = pin

    def CloseCurrentlyOpenContainer(self):
        """
        Close the currently open pin UI container, if any
        """
        if not self.currentContainer:
            return
        self.planetUIContainer.children.remove(self.currentContainer)
        self.currentContainer.updateInfoContTimer.KillTimer()
        self.currentContainer.Close()
        self.currentContainer = None
        self.currentExpandedPin.OnSomethingElseClicked()
        self.currentExpandedPin = None
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_pininteraction_close_play')

    def FocusCameraOnCommandCenter(self, time = 1.0):
        for p in self.myPinManager.pinsByID.values():
            if p.pin.IsCommandCenter():
                try:
                    self.planetNav.camera.AutoOrbit(p.surfacePoint, newZoom=0.3, time=time)
                except AttributeError:
                    pass

                return

    def OnPlanetZoomChanged(self, zoom):
        self.zoom = zoom
        self.curveLineDrawer.ChangeLineSetWidth('links', 1.1 - zoom)
        self.myPinManager.OnPlanetZoomChanged(zoom)

    def VerifySimulation(self):
        self.planet.GMVerifySimulation()

    def GetLocalDistributionReport(self, surfacePoint):
        """Get the local SH levels from the harmonics"""
        report = self.planet.GetLocalDistributionReport(surfacePoint)
        reportRows = []
        for k in report['base'].keys():
            reportRows.append(localization.GetByLabel('UI/PI/Planet/LocalDistributionReportRow', item=k, itemID=k, base=report['base'][k], quality=report['quality'][k], deplete=report['deplete'][k], final=report['final'][k], raw=report['raw'][k]))

        txtMsg = localization.GetByLabel('UI/PI/Planet/LocalDistributionReport', latitude=math.degrees(surfacePoint.phi), longitude=math.degrees(surfacePoint.theta), reportRows='<br>'.join(reportRows))
        uthread.new(eve.Message, 'CustomInfo', {'info': txtMsg}).context = 'gameui.ServerMessage'

    def AddDepletionPoint(self, point):
        self.myPinManager.AddDepletionPoint(point)

    def CancelInstallProgram(self, pinID, pinData):
        currentPlanet = self.GetCurrentPlanet()
        if currentPlanet is None:
            return
        pin = currentPlanet.CancelInstallProgram(pinID, pinData)
        if pin is not None:
            self.myPinManager.ReRenderPin(pin)

    def LoadSpherePinResources(self, spherePin, textureName):
        self.spherePinsPendingLoad.append((spherePin, textureName))
        if not self.spherePinLoadThread:
            self.spherePinLoadThread = uthread.new(self._LoadSpherePinResources)

    def _LoadSpherePinResources(self):
        """
        This thread bulk loads EveSpherePin resources, so we don't have to yield during
        the creation of UI pins, which was causing nasty race conditions
        """
        while True:
            trinity.WaitForResourceLoads()
            while self.spherePinsPendingLoad:
                spherePin, textureName = self.spherePinsPendingLoad.pop()
                spherePin.pinEffect.PopulateParameters()
                for res in spherePin.pinEffect.resources:
                    if res.name == 'Layer1Map':
                        res.resourcePath = textureName
                    elif res.name == 'Layer2Map':
                        res.resourcePath = 'res:/dx9/texture/UI/pinCircularRamp.dds'

                spherePin.pickEffect.PopulateParameters()
                for res in spherePin.pickEffect.resources:
                    if res.name == 'Layer1Map':
                        res.resourcePath = textureName

                spherePin.pinColor = spherePin.pinColor
                spherePin.geometryResPath = 'res:/dx9/model/worldobject/planet/PlanetSphere.gr2'

            blue.pyos.synchro.Yield()

    def StopSpherePinLoadThread(self):
        if self.spherePinLoadThread:
            self.spherePinLoadThread.kill()
            self.spherePinLoadThread = None

    def EnteredEditMode(self, planetID):
        self.inEditMode = True
        if self.planetID == planetID and self.myPinManager is not None:
            self.myPinManager.OnPlanetEnteredEditMode()

    def ExitedEditMode(self, planetID):
        self.inEditMode = False
        if self.planetID == planetID and self.myPinManager is not None:
            self.myPinManager.OnPlanetExitedEditMode()