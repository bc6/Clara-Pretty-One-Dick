#Embedded file name: trinutils\sceneutils.py
import blue
import trinity
try:
    import jessica
except ImportError:
    jessica = None

def FindScene(useDeviceSceneIfFound = True, types = None):
    """Returns a scene fitting the given criteria, or None if none found.
    
    If ``types`` is none default
    to ``(trinity.Tr2InteriorScene, trinity.EveSpaceScene)``
    
    :param useDeviceSceneIfFound: If True, return trinity.device.scene if
      it is set, otherwise, force searching in scheduledRecurring.
    :param types: Type or tuple of types to isinstance a render step's object
      with.
    """
    if types is None:
        types = (trinity.Tr2InteriorScene, trinity.EveSpaceScene)

    def RecursiveSearch(rj):
        for step in rj.steps:
            if hasattr(step, 'object') and isinstance(step.object, types):
                return step.object
            if isinstance(step, trinity.TriStepRunJob):
                scene = RecursiveSearch(step.job)
                if scene:
                    return scene

    scene = None
    if useDeviceSceneIfFound and trinity.device.scene:
        return trinity.device.scene
    for rj in trinity.renderJobs.recurring:
        scene = RecursiveSearch(rj)
        if scene:
            break

    return scene


def GetOrCreateScene():
    scene = FindScene()
    if scene is None or not isinstance(scene, trinity.EveSpaceScene):
        scene = trinity.EveSpaceScene()
    if trinity.device.scene != scene:
        trinity.device.scene = scene
    return scene


def CreateFisRenderJob(scene):
    jessica.GetGlobalJessicaModel().SetRenderInfo(scene)


def CreateBackgroundLandscape(scene, medDetailThreshold = 0.0001, lowDetailThreshold = 0.0001, shaderModel = 'SM_3_0_DEPTH'):
    scene.sunDiffuseColor = (1.5, 1.5, 1.5, 1.0)
    trinity.settings.SetValue('eveSpaceSceneVisibilityThreshold', 3.0)
    trinity.settings.SetValue('eveSpaceSceneMediumDetailThreshold', medDetailThreshold)
    trinity.settings.SetValue('eveSpaceSceneLowDetailThreshold', lowDetailThreshold)
    trinity.SetShaderModel(shaderModel)
    scene.sunDirection = (1.0, -1.0, 1.0)
    scene.envMapRotation = (0.0, 0.0, 0.0, 1.0)
    scene.envMapResPath = 'res:/dx9/scene/universe/m10_cube_refl.dds'
    scene.envMap1ResPath = 'res:/dx9/scene/universe/m10_cube.dds'
    scene.envMap2ResPath = 'res:/dx9/scene/universe/m10_cube_blur.dds'
    scene.envMap3ResPath = ''
    scene.gpuParticlePoolManager = trinity.Tr2GPUParticlePoolManager()
    scene.backgroundEffect = trinity.Load('res:/dx9/scene/starfield/nebula.red')
    scene.starfield = trinity.Load('res:/dx9/scene/starfield/spritestars.red')
    scene.starfield.minDist = 40
    scene.starfield.maxDist = 80
    scene.starfield.numStars = 500
    universe = [ stars for stars in scene.backgroundObjects if stars.name == 'Neighboring Stars' ]
    if not universe:
        universe = trinity.Load('res:/dx9/scene/starfield/universe.red')
        scene.backgroundObjects.append(universe)
        systemX = -20474870.72500089
        systemY = 4023837.993657142
        systemZ = 5762127.890242104
        universe.children[0].translation = (systemX, systemY, systemZ)
    scene.backgroundRenderingEnabled = True
    if jessica:
        CreateFisRenderJob(scene)
