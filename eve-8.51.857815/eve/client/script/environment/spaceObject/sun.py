#Embedded file name: eve/client/script/environment/spaceObject\sun.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import trinity
import evegraphics.settings as gfxsettings

class Sun(SpaceObject):

    def __init__(self):
        SpaceObject.__init__(self)
        self.useGodRays = False
        self.godRaysLoaded = False

    def LoadModel(self):
        graphicFile = self.typeData.get('graphicFile', None)
        baseName = graphicFile.split('/')[-1]
        self.godRaysLoaded = False
        if self.useGodRays and gfxsettings.Get(gfxsettings.UI_GODRAYS):
            graphicFile = graphicFile.replace('.red', '_godrays.red')
            self.godRaysLoaded = True
        self.lensflare = trinity.Load(graphicFile)
        scene = self.spaceMgr.GetScene()
        scene.sunBall = self
        sunModelFile = 'res:/dx9/Model/WorldObject/Sun/' + baseName
        self.sunmodel = trinity.Load(sunModelFile)
        self.model = trinity.EvePlanet()
        self.model.translationCurve = self
        self.model.rotationCurve = self
        self.model.name = '%d' % self.id
        self.model.ready = True
        self.sunmodel.name = self.model.name
        self.model.highDetail = self.sunmodel
        self.model.resourceCallback = self.ResourceCallback
        if self.model is not None:
            scene.planets.append(self.model)
        if self.lensflare is not None:
            self.lensflare.translationCurve = self
            scene.lensflares.append(self.lensflare)
        self.SetupAmbientAudio()
        if self._audioEntity:
            self._audioEntity.SetAttenuationScalingFactor(100.0)

    def EnableGodRays(self, enable):
        self.useGodRays = enable
        if self.godRaysLoaded == enable and gfxsettings.Get(gfxsettings.UI_GODRAYS) == self.godRaysLoaded:
            return
        if self.lensflare is None:
            return
        if not self.released:
            self.ReleaseSun()
        self.LoadModel()
        self.Assemble()

    def SetGodRaysIntensity(self, intensity):
        if not self.useGodRays:
            return
        if self.lensflare is None:
            return
        if not gfxsettings.Get(gfxsettings.UI_GODRAYS):
            return
        for flare in self.lensflare.flares:
            if flare.mesh is not None:
                for area in flare.mesh.additiveAreas:
                    if area.effect is not None:
                        if area.effect.effectFilePath.endswith('GR.fx'):
                            for param in area.effect.parameters:
                                if param.name == 'intensity':
                                    param.value = (param.value[0],
                                     param.value[1],
                                     param.value[2],
                                     intensity)

    def GetGodRaysIntensityParam(self):
        if not self.useGodRays:
            return
        if self.lensflare is None:
            return
        if not gfxsettings.Get(gfxsettings.UI_GODRAYS):
            return
        for area in self.lensflare.mesh.additiveAreas:
            if area.effect.effectFilePath.endswith('godrays.fx'):
                for param in area.effect.parameters:
                    if param.name == 'Intensity':
                        return param

    def ResourceCallback(self, create, size = 2048):
        """ A hack because the sun is not a real planet """
        if self.model:
            self.model.ready = True
            self.model.resourceActionPending = False

    def Assemble(self):
        self.model.scaling = self.radius
        self.model.radius = self.radius / 10.0

    def Release(self):
        if self.released:
            return
        self.ReleaseSun()
        SpaceObject.Release(self, 'Sun')

    def HandleGodraySetting(self):
        self.EnableGodRays(self.useGodRays)

    def ReleaseSun(self):
        scene = self.spaceMgr.GetScene()
        if hasattr(self.model, 'resourceCallback'):
            self.model.resourceCallback = None
        if hasattr(self.model, 'children'):
            del self.model.children[:]
        scene.planets.fremove(self.model)
        if self.model is not None:
            self.model.translationCurve = None
            self.model.rotationCurve = None
            self.model = None
        self.sunmodel = None
        self.lensflare = None
        scene.sunBall = None
        del scene.lensflares[:]


exports = {'spaceObject.Sun': Sun}
