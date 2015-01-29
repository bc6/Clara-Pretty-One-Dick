#Embedded file name: eve/client/script/ui/shared/mapView\mapViewSceneContainer.py
import trinity
from eve.client.script.ui.control.scenecontainer import SceneContainer
from eve.client.script.ui.shared.mapView.mapViewCameraHandler import MapViewCamera

class MapViewSceneContainer(SceneContainer):

    def PrepareCamera(self):
        self.camera = MapViewCamera()
        self.camera.SetViewPort(self.viewport)
        self.projection = self.camera.projectionMatrix

    def SetupCamera(self):
        """We have special purpose camera so we ignore the base functionality"""
        pass

    def Close(self, *args, **kwds):
        SceneContainer.Close(self, *args, **kwds)
        self.scene = None
        self.camera = None
        self.projection = None
        self.renderJob = None
        self.bracketCurveSet = None

    def DisplaySpaceScene(self, blendMode = None):
        """
        Create a Render Job which renders this job on top of this window.
        """
        from trinity.sceneRenderJobSpaceEmbedded import CreateEmbeddedRenderJobSpace
        self.renderJob = CreateEmbeddedRenderJobSpace()
        rj = self.renderJob
        rj.CreateBasicRenderSteps()
        self.CreateBracketCurveSet()
        rj.SetActiveCamera(None, self.camera.viewMatrix, self.camera.projectionMatrix)
        rj.SetScene(self.scene)
        rj.SetViewport(self.viewport)
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
        pass
