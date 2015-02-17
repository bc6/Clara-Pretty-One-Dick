#Embedded file name: eve/client/script/environment/spaceObject\asteroid.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import trinity
import random
import math
import evegraphics.settings as gfxSettings
import trinity.evePostProcess as evePostProcess

class AsteroidEnvironment(object):
    _cloudfieldPath = 'res:/dx9/scene/asteroidcloudfield.red'
    _distanceFieldPath = 'res:/dx9/scene/asteroidDistanceField.red'

    def __init__(self):
        self.distanceField = trinity.Load(self._distanceFieldPath)
        self.sceneManager = sm.GetService('sceneManager')

    def _InitFog(self):
        if not gfxSettings.Get(gfxSettings.UI_ASTEROID_FOG):
            return
        ppJob = self.sceneManager.fisRenderJob.postProcessingJob
        if self.isIcefield:
            ppID = evePostProcess.POST_PROCESS_ICE_FOG
        else:
            ppID = evePostProcess.POST_PROCESS_ASTEROID_FOG
        pp = ppJob.AddPostProcess(ppID)
        FogAmountParameters = None
        AreaSizeParameters = None
        AreaCenterParameters = None
        for param in pp.postProcess.Find('trinity.Tr2Vector4Parameter'):
            if param.name == 'FogParameters':
                FogAmountParameters = param
            elif param.name == 'AreaSize':
                AreaSizeParameters = param
            elif param.name == 'AreaCenter':
                AreaCenterParameters = param

        for binding in self.distanceField.curveSet.bindings:
            if binding.name == 'FogSize':
                binding.sourceObject = self.distanceField
                binding.destinationObject = AreaSizeParameters
            elif binding.name == 'FogCenter':
                binding.sourceObject = self.distanceField
                binding.destinationObject = AreaCenterParameters
            elif binding.name == 'FogAmount':
                binding.destinationObject = FogAmountParameters

    def _InitCloudfield(self):
        if not gfxSettings.Get(gfxSettings.UI_ASTEROID_CLOUDFIELD):
            return
        cf = trinity.Load(self._cloudfieldPath)
        constraint = cf.Find('trinity.EveDustfieldConstraint')[0]
        scene = self.sceneManager.GetRegisteredScene('default')
        camera = self.sceneManager.GetRegisteredCamera('default')
        scene.cloudfield = cf
        scene.cloudfieldConstraint = constraint
        constraint.camera = camera
        colorParam = None
        for each in cf.mesh.transparentAreas[0].effect.parameters:
            if each.name == 'Color2':
                colorParam = each
                break

        for each in self.distanceField.curveSet.bindings:
            if each.name == 'CloudfieldIntensity':
                each.destinationObject = colorParam
                break

    def _InitGodrays(self):
        if sm.GetService('visualEffect').IsGodrayEnabled():
            return
        scene = self.sceneManager.GetRegisteredScene('default')
        if scene.sunBall is None:
            return
        scene.sunBall.EnableGodRays(True)
        intensity = scene.sunBall.GetGodRaysIntensityParam()
        for each in self.distanceField.curveSet.bindings:
            if each.name == 'GodRayIntensity':
                each.destinationObject = intensity
                break

    def Add(self, asteroid):
        if not gfxSettings.Get(gfxSettings.UI_ASTEROID_ATMOSPHERICS):
            return
        scene = self.sceneManager.GetRegisteredScene('default')
        if len(self.distanceField.objects) == 0:
            self.isIcefield = asteroid.typeData['groupID'] == const.groupIce
            self._InitFog()
            self._InitCloudfield()
            self._InitGodrays()
        if self.distanceField not in scene.distanceFields:
            camera = self.sceneManager.GetRegisteredCamera('default')
            self.distanceField.camera = camera
            scene.distanceFields.append(self.distanceField)
        self.distanceField.objects.append(asteroid)

    def Remove(self, asteroid):
        if len(self.distanceField.objects) == 0:
            return
        self.distanceField.objects.fremove(asteroid)
        if len(self.distanceField.objects) == 0:
            self.sceneManager.fisRenderJob.postProcessingJob.RemovePostProcess(evePostProcess.PP_GROUP_FOG)
            scene = self.sceneManager.GetRegisteredScene('default')
            if not sm.GetService('visualEffect').IsGodrayEnabled() and scene.sunBall is not None:
                scene.sunBall.EnableGodRays(False)
            scene.cloudfield = None
            scene.cloudfieldConstraint = None


class Asteroid(SpaceObject):
    _asteroidEnvironment = None

    def __init__(self):
        SpaceObject.__init__(self)
        if Asteroid._asteroidEnvironment is None:
            Asteroid._asteroidEnvironment = AsteroidEnvironment()

    def LoadModel(self, fileName = None, loadedModel = None):
        groupID = self.typeData.get('groupID')
        typeID = self.typeData.get('typeID')
        groupGraphics = cfg.groupGraphics.get(groupID, None)
        graphicID = None
        if hasattr(groupGraphics, 'graphicIDs'):
            variationID = self.id % len(groupGraphics.graphicIDs)
            graphicID = groupGraphics.graphicIDs[variationID]
        elif hasattr(groupGraphics, 'typeIDs'):
            graphicIDs = groupGraphics.typeIDs.get(typeID, None).graphicIDs
            variationID = self.id % len(graphicIDs)
            graphicID = graphicIDs[variationID]
        graphic = cfg.graphics.get(graphicID, None)
        graphicFile = getattr(graphic, 'graphicFile', None)
        if graphicFile:
            SpaceObject.LoadModel(self, fileName=graphicFile)
            Asteroid._asteroidEnvironment.Add(self)
        else:
            self.LogError('Could not load model for asteroid. groupID: %s, typeID: %s, graphicID: %s' % (groupID, typeID, graphicID))

    def Assemble(self):
        if self.model is None:
            self.LogError('Cannot Assemble Asteroid, model failed to load')
            return
        self.model.modelScale = self.radius
        pi = math.pi
        identity = trinity.TriQuaternion()
        cleanRotation = trinity.TriQuaternion()
        preRotation = trinity.TriQuaternion()
        postRotation = trinity.TriQuaternion()
        rotKey = trinity.TriQuaternion()
        r = random.Random()
        r.seed(self.id)
        preRotation.SetYawPitchRoll(r.random() * pi, r.random() * pi, r.random() * pi)
        postRotation.SetYawPitchRoll(r.random() * pi, r.random() * pi, r.random() * pi)
        curve = trinity.TriRotationCurve()
        curve.extrapolation = trinity.TRIEXT_CYCLE
        duration = 50.0 * math.log(self.radius)
        rdur = r.random() * 50.0 * math.log(self.radius)
        duration += rdur
        for i in [0.0,
         0.5,
         1.0,
         1.5,
         2.0]:
            cleanRotation.SetYawPitchRoll(0.0, pi * i, 0.0)
            rotKey.SetIdentity()
            rotKey.MultiplyQuaternion(preRotation)
            rotKey.MultiplyQuaternion(cleanRotation)
            rotKey.MultiplyQuaternion(postRotation)
            curve.AddKey(duration * i, rotKey, identity, identity, trinity.TRIINT_SLERP)

        curve.Sort()
        self.model.modelRotationCurve = curve

    def RemoveFromScene(self, model, scene):
        SpaceObject.RemoveFromScene(self, model, scene)
        Asteroid._asteroidEnvironment.Remove(self)
