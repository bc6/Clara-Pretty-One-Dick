#Embedded file name: trinity\sceneRenderJobSpaceJessica.py
"""
Contains a jessica version of the space scene render job.
"""
from . import _trinity as trinity
from . import _singletons
from .sceneRenderJobSpace import SceneRenderJobSpace

def CreateJessicaSpaceRenderJob(name = None, stageKey = None):
    """
    We can't use __init__ on a decorated class, so we provide a creation function that does it for us
    """
    newRJ = SceneRenderJobSpaceJessica()
    if name is not None:
        newRJ.ManualInit(name)
    else:
        newRJ.ManualInit()
    newRJ.SetMultiViewStage(stageKey)
    return newRJ


class SceneRenderJobSpaceJessica(SceneRenderJobSpace):
    """ Jessica/Maya version of the space render job. """

    def _ManualInit(self, name = 'SceneRenderJobSpace'):
        SceneRenderJobSpace._ManualInit(self, name)
        self.persistedPostProcess = {}
        self.settings = {'aaQuality': 3,
         'postProcessingQuality': 2,
         'shadowQuality': 2,
         'shadowMapSize': 1024,
         'hdrEnabled': True}
        self.backBufferOverride = None
        self.depthBufferOverride = None

    def SetSettings(self, rjSettings):
        self.settings = rjSettings

    def GetSettings(self):
        return self.settings

    def GetMultiSampleTypeFromQuality(self, quality):
        pp = _singletons.device.GetPresentParameters()
        windowed = pp['Windowed']
        msaaTypes = [0]
        fmt = trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT if self.hdrEnabled else self.bbFormat

        def Supported(msType):
            return _singletons.adapters.GetRenderTargetMsaaSupport(_singletons.device.adapter, fmt, windowed, msType)

        if Supported(2):
            msaaTypes.append(2)
        if Supported(4):
            msaaTypes.append(4)
        if Supported(8):
            msaaTypes.append(8)
        elif Supported(6):
            msaaTypes.append(6)
        if quality >= len(msaaTypes):
            quality = len(msaaTypes) - 1
        return msaaTypes[quality]

    def GetMSAATypeFromQuality(self, aaQuality):
        if aaQuality == 0:
            return 0
        return self.GetMultiSampleTypeFromQuality(aaQuality)

    def _RefreshAntiAliasing(self):
        if self.useFXAA:
            self.EnableFXAA(self.antiAliasingEnabled)
        else:
            self.EnableMSAA(self.antiAliasingEnabled)

    def GetPostProcesses(self):
        if self.postProcessingJob is not None:
            return self.postProcessingJob.GetPostProcesses()
        return []

    def _GetSettings(self):
        """ See SceneRenderJobSpace._GetSettings """
        return self.settings

    def OverrideBuffers(self, backBuffer, depthBuffer):
        """ Overrides default backbuffer and depthbuffer """
        self.backBufferOverride = backBuffer
        self.depthBufferOverride = depthBuffer

    def _SetSettingsBasedOnPerformancePreferences(self):
        self.aaQuality = self.settings['aaQuality']
        self.antiAliasingEnabled = self.aaQuality > 0
        self.antiAliasingQuality = self.aaQuality
        self.msaaType = self.GetMSAATypeFromQuality(self.aaQuality)
        self.fxaaQuality = self._GetFXAAQuality(self.aaQuality)
        self.shadowQuality = self.settings['shadowQuality']
        if self.shadowQuality > 0 and self.shadowMap is None:
            self.shadowMap = trinity.TriShadowMap()
            self.shadowMap.size = self.settings['shadowMapSize']
        elif self.shadowQuality == 0:
            self.shadowMap = None
        else:
            self.shadowMap.size = self.settings['shadowMapSize']
        self.usePostProcessing = self.postProcessingJob.liveCount > 0

    def SetRenderTargets(self, *args):
        SceneRenderJobSpace.SetRenderTargets(self, *args)
        if self.depthBufferOverride:
            self.AddStep('SET_SWAPCHAIN_DEPTH', trinity.TriStepSetDepthStencil(self.depthBufferOverride))
        if self.backBufferOverride:
            self.AddStep('SET_SWAPCHAIN_RT', trinity.TriStepSetRenderTarget(self.backBufferOverride))

    def GetBackBufferSize(self):
        """
        Gets the size of the BackBuffer of the renderjob
        """
        if self.backBufferOverride is None:
            return SceneRenderJobSpace.GetBackBufferSize(self)
        width = self.backBufferOverride.width
        height = self.backBufferOverride.height
        return (width, height)

    def _GetRTForDepthPass(self):
        if self.backBufferOverride is not None:
            return self.backBufferOverride
        return SceneRenderJobSpace._GetRTForDepthPass(self)

    def GetBackBufferRenderTarget(self):
        """
        Gets the BackBufferRenderTarget based on the renderContext or swapchain
        """
        if self.backBufferOverride is not None:
            return self.backBufferOverride
        return SceneRenderJobSpace.GetBackBufferRenderTarget(self)
