#Embedded file name: eve/client/script/ui/control\scenecontainer.py
import blue
from carbonui.primitives.base import Base
from carbonui.primitives.container import Container
from carbonui.util.various_unsorted import GetWindowAbove
import trinity
import log
import uicontrols
import carbonui.const as uiconst
import bitmapjob
import paperDoll
import geo2
import evegraphics.utils as gfxutils

class SceneContainer(Base):
    __guid__ = 'form.SceneContainer'
    __renderObject__ = trinity.Tr2Sprite2dRenderJob
    default_minZoom = 10.0
    default_maxZoom = 3000.0

    def ApplyAttributes(self, attributes):
        self.viewport = trinity.TriViewport()
        self.viewport.x = 0
        self.viewport.y = 0
        self.viewport.width = 1
        self.viewport.height = 1
        self.viewport.minZ = 0.0
        self.viewport.maxZ = 1.0
        self.projection = trinity.TriProjection()
        self.renderJob = None
        self.frontClip = 1.0
        self.backClip = 350000.0
        self.fieldOfView = 1.0
        self.minPitch = -1.4
        self.maxPitch = 1.4
        self.offscreen = False
        Base.ApplyAttributes(self, attributes)
        self.minZoom = attributes.Get('minZoom', self.default_minZoom)
        self.maxZoom = attributes.Get('maxZoom', self.default_maxZoom)
        self._zoom = 0.5

    def SetParent(self, parent, idx = None):
        Base.SetParent(self, parent, idx)
        wnd = GetWindowAbove(self)
        if wnd:
            wnd.RegisterSceneContainer(self)

    def Startup(self, *args):
        self.PrepareCamera()
        self.scene = None
        self.DisplayScene()

    def PrepareSpaceScene(self, maxPitch = 1.4, scenePath = None, offscreen = False):
        """
        Setup the scene for space objects
        """
        self.offscreen = offscreen
        if scenePath is None:
            scenePath = 'res:/dx9/scene/fitting/previewTurrets.red'
        self.scene = trinity.Load(scenePath)
        self.scene.dynamicClipPlanes = False
        if gfxutils.BlockStarfieldOnLionOSX():
            self.scene.starfield = None
        self.frontClip = 1.0
        self.backClip = 350000.0
        self.fieldOfView = 1.0
        self.minPitch = -1.4
        self.maxPitch = maxPitch
        self.SetupCamera()
        self.DisplaySpaceScene()

    def CreateBracketCurveSet(self):
        """ Create a curveset to update any uiprimitives.Bracket present """
        self.bracketCurveSet = trinity.TriCurveSet()
        self.bracketCurveSet.Play()
        step = trinity.TriStepUpdate()
        step.object = self.bracketCurveSet
        step.name = 'Update brackets'
        self.renderJob.AddStep('UPDATE_BRACKETS', step)

    def PrepareInteriorScene(self, addShadowStep = False, backgroundImage = None):
        """
        Setup the scene for interior objects
        """
        self.scene = trinity.Load('res:/Graphics/Interior/characterCreation/Preview.red')
        self.frontClip = 0.1
        self.backClip = 10.0
        self.fieldOfView = 0.3
        self.minPitch = -0.6
        self.maxPitch = 0.6
        self.SetupCamera()
        blue.resMan.Wait()
        self.DisplayScene(addClearStep=True, addBitmapStep=True, addShadowStep=addShadowStep, backgroundImage=backgroundImage)

    def SetupCamera(self):
        """
        Sets the camera's parameters
        """
        self.camera.frontClip = self.frontClip
        self.camera.backClip = self.backClip
        self.camera.fieldOfView = self.fieldOfView
        self.camera.minPitch = self.minPitch
        self.camera.maxPitch = self.maxPitch

    def PrepareCamera(self):
        """
        Creates the camera and camera parent
        """
        self.camera = trinity.EveCamera()
        self.cameraParent = self.camera.parent = trinity.EveSO2ModelCenterPos()

    def DisplaySpaceScene(self, blendMode = None):
        """
        Create a Render Job which renders this job on top of this window.
        """
        from trinity.sceneRenderJobSpaceEmbedded import CreateEmbeddedRenderJobSpace
        self.renderJob = CreateEmbeddedRenderJobSpace()
        rj = self.renderJob
        rj.CreateBasicRenderSteps()
        self.CreateBracketCurveSet()
        rj.SetActiveCamera(self.camera)
        rj.SetCameraProjection(self.projection)
        rj.SetScene(self.scene)
        rj.SetViewport(self.viewport)
        if self.offscreen:
            rj.SetOffscreen(self.offscreen)
        rj.UpdateViewport(self.viewport)
        sm.GetService('sceneManager').RegisterJob(rj)
        try:
            rj.DoPrepareResources()
        except trinity.D3DError:
            pass

        if blendMode:
            step = trinity.TriStepSetStdRndStates()
            step.renderingMode = blendMode
            rj.AddStep('SET_BLENDMODE', step)
        rj.Enable(False)
        rj.SetSettingsBasedOnPerformancePreferences()
        self.renderObject.renderJob = self.renderJob

    def DisplayScene(self, addClearStep = False, addBitmapStep = False, addShadowStep = False, backgroundImage = None):
        """
        Create a Render Job which renders this job on top of this window.
        """
        self.renderJob = trinity.CreateRenderJob('SceneInScene')
        self.renderJob.SetViewport(self.viewport)
        self.projection.PerspectiveFov(self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)
        self.renderJob.SetProjection(self.projection)
        self.renderJob.SetView(None, self.camera, None)
        self.renderJob.Update(self.scene)
        if addShadowStep:
            paperDoll.SkinSpotLightShadows.CreateShadowStep(self.renderJob)
        if addClearStep:
            self.renderJob.Clear(None, 1.0)
        if addBitmapStep:
            if backgroundImage is None:
                backgroundImage = 'res:/UI/Texture/preview/asset_preview_background.png'
            step = bitmapjob.makeBitmapStep(backgroundImage, scaleToFit=False, color=(1.0, 1.0, 1.0, 1.0))
            self.renderJob.steps.append(step)
        self.renderJob.RenderScene(self.scene)
        self.renderObject.renderJob = self.renderJob

    def SetStencilMap(self, path = 'res:/UI/Texture/circleStencil.dds'):
        if hasattr(self.renderJob, 'SetStencil'):
            self.renderJob.SetStencil(path)

    def AddToScene(self, model, clear = 1):
        """
        Clear the scene, add the model to it and have the model be the
        camera's point of interest
        """
        if model == None or self.scene == None:
            return
        if clear:
            del self.scene.objects[:]
        self.scene.objects.append(model)
        self.scene.UpdateScene(blue.os.GetSimTime())
        self.cameraParent.parent = model
        self.camera.rotationOfInterest = geo2.QuaternionIdentity()

    def ClearScene(self):
        self.scene.UpdateScene(blue.os.GetSimTime())
        del self.scene.objects[:]

    def _OnResize(self):
        """
        When we move or resize the window we need the viewport to follow
        """
        self.UpdateViewPort()

    def UpdateViewPort(self, *args):
        l, t, w, h = self.GetAbsoluteViewport()
        if not w and not h:
            return
        if not self.offscreen:
            l = uicore.ScaleDpi(l)
            t = uicore.ScaleDpi(t)
            w = uicore.ScaleDpi(w)
            h = uicore.ScaleDpi(h)
        self.viewport.x = l
        self.viewport.y = t
        self.viewport.width = w
        self.viewport.height = h
        self.projection.PerspectiveFov(self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)
        if hasattr(self.renderJob, 'UpdateViewport'):
            self.renderJob.UpdateViewport(self.viewport)

    def OnResize_(self, k, v):
        self.UpdateViewPort()

    def UpdateAlignment(self, *args):
        ret = Base.UpdateAlignment(self, *args)
        self.UpdateViewPort()
        return ret

    def _OnClose(self, *args):
        self.clearStep = None
        self.viewport = None
        self.projection = None
        self.camera = None
        self.cameraParent = None
        self.scene = None
        if hasattr(self.renderJob, 'Disable'):
            self.renderJob.Disable()
        self.renderJob = None

    def AnimEntry(self, yaw0 = 0.0, pitch0 = 0.0, yaw1 = -0.5, pitch1 = -0.5, duration = 2.0):
        """
        Zoom and rotate camera entry animation
        """
        uicore.animations.MorphScalar(self, 'zoom', (1.0 - self.zoom) / 2.0, self.zoom, duration=duration)
        uicore.animations.MorphVector2(self, 'orbit', (yaw0, pitch0), (yaw1, pitch1), duration=duration)

    def GetOrbit(self):
        return (0.0, 0.0)

    def SetOrbit(self, yawPitch):
        self.camera.SetOrbit(*yawPitch)

    orbit = property(GetOrbit, SetOrbit)

    def OrbitParent(self, dx, dy):
        self.StopAnimations()
        fov = self.camera.fieldOfView
        cameraSpeed = 0.6
        self.camera.OrbitParent(-dx * fov * cameraSpeed, dy * fov * cameraSpeed)

    def GetZoom(self):
        return self._zoom

    def SetZoom(self, value):
        self._zoom = value
        self._zoom = max(0.0, min(self._zoom, 1.0))
        self.camera.translationFromParent = self.minZoom + self._zoom * (self.maxZoom - self.minZoom)

    zoom = property(GetZoom, SetZoom)

    def SetMinMaxZoom(self, minZoom, maxZoom):
        self.minZoom = minZoom
        self.maxZoom = maxZoom

    def Zoom(self, dz):
        self.StopAnimations()
        self.zoom += dz * max(self.zoom, 0.1)


class SceneWindowTest(uicontrols.Window):
    __guid__ = 'form.SceneWindowTest'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        sc = SceneContainer(uicontrols.Frame(parent=self.sr.main, padding=(6, 6, 6, 6)))
        sc.Startup()
        nav = SceneContainerBaseNavigation(Container(parent=self.sr.main, left=6, top=6, width=6, height=6, idx=0, state=uiconst.UI_NORMAL))
        nav.Startup(sc)
        self.sr.navigation = nav
        self.sr.sceneContainer = sc

    def OnResizeUpdate(self, *args):
        self.sr.sceneContainer.UpdateViewPort()


class SceneContainerBaseNavigation(Container):
    __guid__ = 'form.SceneContainerBaseNavigation'
    isTabStop = 1

    def Startup(self, sceneContainer):
        self.sr.sceneContainer = sceneContainer
        self.sr.cookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self._OnGlobalMouseUp)

    def _OnClose(self, *args):
        if self.sr.cookie:
            uicore.event.UnregisterForTriuiEvents(self.sr.cookie)
            self.sr.cookie = None

    def SetMinMaxZoom(self, minZoom, maxZoom):
        self.sr.sceneContainer.SetMinMaxZoom(minZoom, maxZoom)

    def OnMouseWheel(self, *args):
        self.sr.sceneContainer.Zoom(uicore.uilib.dz * 0.001)

    def OnMouseMove(self, *args):
        if self.destroyed or uicore.IsDragging():
            return
        lib = uicore.uilib
        dx = lib.dx
        dy = lib.dy
        fov = self.sr.sceneContainer.camera.fieldOfView
        ctrl = lib.Key(uiconst.VK_CONTROL)
        if lib.leftbtn and not lib.rightbtn:
            self.sr.sceneContainer.OrbitParent(dx, dy)
        if lib.leftbtn and lib.rightbtn:
            self.sr.sceneContainer.Zoom(-dy * 0.01)
            self.sr.sceneContainer.OrbitParent(dx, 0.0)

    def _OnGlobalMouseUp(self, wnd, msgID, btn, *args):
        if btn and btn[0] == 1:
            self.sr.sceneContainer.camera.rotationOfInterest = geo2.QuaternionIdentity()
        return 1


class SceneContainerBrackets(Base):
    """
    A scene container whose only job is to house instances of Bracket. No
    Scene as such is displayed.
    """
    __guid__ = 'form.SceneContainerBrackets'
    __renderObject__ = trinity.Tr2Sprite2dRenderJob

    def ApplyAttributes(self, attributes):
        Base.ApplyAttributes(self, attributes)
        self.viewport = trinity.TriViewport()
        self.viewport.x = 0
        self.viewport.y = 0
        self.viewport.width = 1
        self.viewport.height = 1
        self.viewport.minZ = 0.0
        self.viewport.maxZ = 1.0
        self.projection = trinity.TriProjection()
        self.frontClip = 1.0
        self.backClip = 350000.0
        self.fieldOfView = 1.0
        self.minPitch = -3.0
        self.maxPitch = 3.4
        self.minZoom = 0.0
        self.maxZoom = 1.0
        self._zoom = 0.5
        self.scene = trinity.EveSpaceScene()
        self.transform = trinity.EveRootTransform()
        self.scene.objects.append(self.transform)
        self.PrepareCamera()
        self.DisplayScene()
        self.CreateBracketCurveSet()
        self.UpdateViewPort()

    def SetParent(self, parent, idx = None):
        Base.SetParent(self, parent, idx)
        wnd = GetWindowAbove(self)
        if wnd:
            wnd.RegisterSceneContainer(self)

    def PrepareCamera(self):
        """
        Creates the camera and camera parent
        """
        self.cameraParent = trinity.EveSO2ModelCenterPos()
        self.camera = trinity.EveCamera()
        self.camera.parent = self.cameraParent
        self.camera.frontClip = self.frontClip
        self.camera.backClip = self.backClip
        self.camera.fieldOfView = self.fieldOfView
        self.camera.minPitch = self.minPitch
        self.camera.maxPitch = self.maxPitch

    def GetTranslationsForSolarsystemIDs(self, solarSystemIDs):
        xAv = yAv = zAv = 0
        scale = 1e+16
        for solarsystemID in solarSystemIDs:
            systemCenter = cfg.mapSystemCache[solarsystemID].center
            xAv += systemCenter.x
            yAv += systemCenter.y
            zAv += systemCenter.z

        numSystems = len(solarSystemIDs)
        xAv /= numSystems
        yAv /= numSystems
        zAv /= numSystems
        translations = []
        for solarsystemID in solarSystemIDs:
            systemCenter = cfg.mapSystemCache[solarsystemID].center
            translations.append(((systemCenter.x - xAv) / scale, (systemCenter.y - yAv) / scale, (systemCenter.z - zAv) / scale))

        return translations

    def CreateBracketTransform(self, translation):
        tr = trinity.EveTransform()
        tr.translation = translation
        self.transform.children.append(tr)
        return tr

    def AnimRotateFrom(self, yaw, pitch, zoom, duration):
        sequencer = trinity.TriYPRSequencer()
        self.transform.rotationCurve = sequencer
        start = blue.os.GetSimTime()
        sequencer.YawCurve = yawCurve = trinity.TriScalarCurve()
        yawCurve.start = start
        yawCurve.extrapolation = trinity.TRIEXT_CONSTANT
        yawCurve.AddKey(0.0, yaw, 0, 0, trinity.TRIINT_HERMITE)
        yawCurve.AddKey(duration, 0.0, 0, 0, trinity.TRIINT_HERMITE)
        sequencer.PitchCurve = pitchCurve = trinity.TriScalarCurve()
        pitchCurve.start = start
        pitchCurve.extrapolation = trinity.TRIEXT_CONSTANT
        pitchCurve.AddKey(0.0, pitch, 0, 0, trinity.TRIINT_HERMITE)
        pitchCurve.AddKey(duration, 0.0, 0, 0, trinity.TRIINT_HERMITE)

    def DisplayScene(self):
        """
        Create a Render Job which renders this job on top of this window.
        """
        self.renderJob = trinity.CreateRenderJob()
        self.renderJob.SetViewport(self.viewport)
        self.renderJob.SetView(None, self.camera, None)
        self.renderJob.SetProjection(self.projection)
        self.renderJob.Update(self.scene)
        self.renderJob.RenderScene(self.scene)
        self.renderObject.renderJob = self.renderJob

    def CreateBracketCurveSet(self):
        """ Create a curveset to update any Bracket present """
        self.bracketCurveSet = trinity.TriCurveSet()
        self.bracketCurveSet.Play()
        step = trinity.TriStepUpdate()
        step.object = self.bracketCurveSet
        step.name = 'Update brackets'
        self.renderJob.steps.append(step)

    def _OnResize(self):
        """
        When we move or resize the window we need the viewport to follow
        """
        self.UpdateViewPort()

    def UpdateViewPort(self, *args):
        l, t, w, h = self.GetAbsoluteViewport()
        log.LogInfo('SceneContainerBrackets::UpdateViewPort', l, t, w, h)
        if not w and not h:
            return
        self.viewport.width = uicore.ScaleDpi(w)
        self.viewport.height = uicore.ScaleDpi(h)
        log.LogInfo('new viewport dimensions', self.viewport.x, self.viewport.y, self.viewport.width, self.viewport.height)
        log.LogInfo('projection', self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)
        self.projection.PerspectiveFov(self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)

    def _OnClose(self, *args):
        self.clearStep = None
        self.viewport = None
        self.projection = None
        self.camera = None
        self.cameraParent = None
        self.scene = None
        if hasattr(self.renderJob, 'Disable'):
            self.renderJob.Disable()
        self.renderJob = None

    def GetOrbit(self):
        return (0.0, 0.0)

    def SetOrbit(self, yawPitch):
        self.camera.SetOrbit(*yawPitch)

    orbit = property(GetOrbit, SetOrbit)

    def OrbitParent(self, dx, dy):
        self.StopAnimations()
        fov = self.camera.fieldOfView
        cameraSpeed = 0.6
        self.camera.OrbitParent(-dx * fov * cameraSpeed, dy * fov * cameraSpeed)

    def GetZoom(self):
        return self._zoom

    def SetZoom(self, value):
        self._zoom = value
        self._zoom = max(0.0, min(self._zoom, 1.0))
        self.camera.translationFromParent = self.minZoom + self._zoom * (self.maxZoom - self.minZoom)

    zoom = property(GetZoom, SetZoom)

    def SetMinMaxZoom(self, minZoom, maxZoom):
        self.minZoom = minZoom
        self.maxZoom = maxZoom

    def Zoom(self, dz):
        self.zoom += dz * max(self.zoom, 0.1) ** 0.5
