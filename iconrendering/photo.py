#Embedded file name: iconrendering\photo.py
import blue
import remotefilecache
import trinity
import geo2
from trinity.sceneRenderJobSpaceJessica import CreateJessicaSpaceRenderJob
import eveSpaceObject.spaceobjanimation as soanimation
import iconrendering.camera_util as camera_util
import eve.common.lib.appConst as const
sofFactory = None

def GetSofFactory():
    global sofFactory
    if sofFactory:
        return sofFactory
    sofFactory = trinity.EveSOF()
    sofFactory.dataMgr.LoadData('res:/dx9/model/spaceobjectfactory/data.red')
    blue.resMan.Wait()
    return sofFactory


def FreezeTime():
    """Freezes blue and animation time.
    Should be called before blue.os.Pump because it changes its behavior.
    """
    blue.os.advanceTimeInPump = False
    blue.os.SetTime(1L)
    trinity.device.animationTimeScale = 0.0
    trinity.device.animationTime = 1
    blue.os.Pump()
    trinity.app.ProcessMessages()


def SetupScene(scene, transparentBackground = False, sunDirection = None):
    scene.sunDirection = sunDirection or (-0.5, -0.5, -0.6)
    scene.ambientColor = (1.0, 1.0, 1.0, 1.0)
    scene.sunDiffuseColor = (1.3, 1.3, 1.3, 1.0)
    if transparentBackground:
        scene.backgroundRenderingEnabled = False


def SetupModel(model):
    if hasattr(model, 'FreezeHighDetailMesh'):
        model.FreezeHighDetailMesh()
    perlinCurves = model.Find('trinity.TriPerlinCurve')
    for curve in perlinCurves:
        curve.scale = 0.0

    if hasattr(model, 'curveSets'):
        model.curveSets.removeAt(-1)
    if hasattr(model, 'modelRotationCurve'):
        model.modelRotationCurve = None
    if hasattr(model, 'modelTranslationCurve'):
        model.modelTranslationCurve = None
    if hasattr(model, 'rotationCurve'):
        model.rotationCurve = None
    if hasattr(model, 'translationCurve'):
        model.translationCurve = None


def CreateSprite(scale, size):
    sprite = trinity.Tr2Sprite2d()
    sprite.texturePrimary = trinity.Tr2Sprite2dTexture()
    sprite.texturePrimary.resPath = 'res:/Texture/Global/blackAlpha.dds'
    sprite.displayHeight = scale
    sprite.displayWidth = scale
    sprite.displayX = 0.5 * (1.0 - 1.0 / size)
    sprite.displayY = 0.5 * (1.0 - 1.0 / size)
    return sprite


def CreateRenderJob(size, view, projection, bgColor = None, transparent = False, postProcessingQuality = 2, antiAliasingQuality = 3):
    """
    Creates a Jessica render job and adds functionality for 2D sprite background and overlays.
    """

    def _GetRenderStepPosition(renderJob, name):
        for i, each in enumerate(renderJob.steps):
            if each.name == name:
                return i

        return i

    if transparent:
        clearColor = bgColor or (0.0, 0.0, 0.0, 0.0)
        format = trinity.PIXEL_FORMAT.B8G8R8A8_UNORM
    else:
        clearColor = bgColor or (0.0, 0.0, 0.0, 1.0)
        format = trinity.PIXEL_FORMAT.B8G8R8X8_UNORM
    rt = trinity.Tr2RenderTarget(size, size, 1, format)
    rt.name = 'MyRT'
    ds = trinity.Tr2DepthStencil()
    ds.Create(size, size, trinity.DEPTH_STENCIL_FORMAT.D24S8, 0, 0)
    ds.name = 'MyDS'
    vp = trinity.TriViewport()
    vp.width = size
    vp.height = size
    renderJob = CreateJessicaSpaceRenderJob()
    renderJob.updateJob = None
    renderJob.CreateBasicRenderSteps()
    renderJob.OverrideSettings('hdrEnabled', True)
    settings = renderJob.GetSettings()
    settings['postProcessingQuality'] = postProcessingQuality
    settings['aaQuality'] = antiAliasingQuality
    renderJob.SetSettings(settings)
    renderJob.SetClearColor(clearColor)
    renderJob.OverrideSettings('bbFormat', format)
    renderJob.SetActiveCamera(view=view, projection=projection)
    renderJob.SetViewport(vp)
    renderJob.OverrideBuffers(rt, ds)
    renderJob.Enable(False)
    bgStep = trinity.TriStepRenderScene()
    bgStep.name = 'BACKGROUND_SPRITE'
    bgSprite1 = CreateSprite(1.0, size)
    bgSprite2 = CreateSprite(1.0, size)
    bgSpriteScene = trinity.Tr2Sprite2dScene()
    bgSpriteScene.children.append(bgSprite1)
    bgSpriteScene.children.append(bgSprite2)
    bgStep.scene = bgSpriteScene
    pos = _GetRenderStepPosition(renderJob, 'CLEAR')
    renderJob.steps.insert(pos + 1, bgStep)
    setattr(renderJob, 'iconTexture', bgSprite1.texturePrimary)
    setattr(renderJob, 'backgroundTexture', bgSprite2.texturePrimary)
    oStep = trinity.TriStepRenderScene()
    oStep.name = 'OVERLAY_SPRITES'
    oSprite1 = CreateSprite(1.0, size)
    oSprite1.blendMode = 2
    oSprite2 = CreateSprite(16.0 / size, size)
    oSpriteScene = trinity.Tr2Sprite2dScene()
    oSpriteScene.children.append(oSprite1)
    oSpriteScene.children.append(oSprite2)
    oStep.scene = oSpriteScene
    pos2 = _GetRenderStepPosition(renderJob, 'END_RENDERING')
    renderJob.steps.insert(pos2 + 1, oStep)
    setattr(renderJob, 'overlayTexture', oSprite1.texturePrimary)
    setattr(renderJob, 'techTexture', oSprite2.texturePrimary)
    setattr(renderJob, 'renderTarget', rt)
    return renderJob


def RenderToSurface(view, projection, size = 128, scene = None, bgColor = None, transparent = False, backgroundPath = None, overlayPath = None, techPath = None, iconPath = None, postProcessingQuality = 2, antiAliasingQuality = 3):
    """
    Renders a scene and sprites to a surface.
    """
    renderJob = CreateRenderJob(size, view, projection, bgColor, transparent, postProcessingQuality, antiAliasingQuality)
    if scene:
        renderJob.SetScene(scene)
    else:
        renderJob.SetScene(trinity.EveSpaceScene())
    if backgroundPath:
        if scene:
            scene.backgroundRenderingEnabled = False
        renderJob.backgroundTexture.resPath = backgroundPath
    if iconPath:
        renderJob.iconTexture.resPath = iconPath
    if overlayPath:
        renderJob.overlayTexture.resPath = overlayPath
    if techPath:
        renderJob.techTexture.resPath = techPath
    blue.resMan.Wait()
    renderJob.DoPrepareResources()
    renderJob.ScheduleOnce()
    renderJob.WaitForFinish()
    hostBitmap = trinity.Tr2HostBitmap(renderJob.renderTarget)
    return hostBitmap


def RenderIcon(outPath, size = 128, backgroundPath = None, overlayPath = None, techPath = None, iconPath = None):
    """
    Renders a 2D sprite. TODO just pass the kwargs through?
    """
    transparent = True
    if backgroundPath:
        transparent = False
    hostBitmap = RenderToSurface(view=None, projection=None, size=size, scene=None, bgColor=None, transparent=transparent, backgroundPath=backgroundPath, overlayPath=overlayPath, techPath=techPath, iconPath=iconPath)
    hostBitmap.Save(outPath)


def RenderSpaceScene(outPath, view, projection, scenePath, size = 128):
    """
    This method loads up a trinity.EveSpaceScene from res paths passed in and renders it given the provided camera matrices
    """
    scene = None
    if scenePath:
        scene = blue.resMan.LoadObject(scenePath)
        SetupScene(scene)
    blue.resMan.Wait()
    blue.os.Pump()
    hostBitmap = RenderToSurface(scene=scene, view=view, projection=projection, size=size)
    hostBitmap.Save(outPath)
    trinity.app.ProcessMessages()


def RenderSpaceObject(outPath, scenePath = '', objectPath = '', sofDNA = None, size = 128, bgColor = None, transparent = False, backgroundPath = None, overlayPath = None, techPath = None, cameraAngle = None, freezeTime = True, postProcessingQuality = 2, antiAliasingQuality = 3, modifyScene = None, sunDirection = None, animationStates = []):
    """
    This method loads up a trinity.EveSpaceObject and a trinity.EveSpaceScene from res paths passed in.
    The model and scene are modified and the camera (transforms) are set up in the same way as the Eve Photo service.
    """
    if freezeTime:
        FreezeTime()
    trinity.GetVariableStore().RegisterVariable('DepthMap', trinity.TriTextureRes())
    trinity.GetVariableStore().RegisterVariable('DepthMapMsaa', trinity.TriTextureRes())
    if scenePath:
        scene = blue.resMan.LoadObject(scenePath)
        SetupScene(scene, transparentBackground=transparent, sunDirection=sunDirection)
    else:
        scene = trinity.EveSpaceScene()
    model = None
    if sofDNA:
        factory = GetSofFactory()
        model = factory.BuildFromDNA(sofDNA)
    elif objectPath:
        model = blue.resMan.LoadObject(objectPath)
    if model:
        SetupModel(model)
        scene.objects.append(model)
    if len(animationStates) > 0:
        soanimation.LoadAnimationStatesFromFiles(animationStates, model, trinity)
        soanimation.TriggerDefaultStates(model)
    blue.resMan.Wait()
    blue.os.Pump()
    view = projection = None
    if model:
        boundingSphereRadius = model.GetBoundingSphereRadius()
        if model.mesh is not None:
            geometry = model.mesh.geometry
            boundingSphereCenter = model.GetBoundingSphereCenter()
            view, projection = camera_util.GetViewAndProjectionUsingMeshGeometry(geometry, scene=scene, boundingSphereRadius=boundingSphereRadius, boundingSphereCenter=boundingSphereCenter, cameraAngle=cameraAngle)
        else:
            view, projection = camera_util.GetViewAndProjectionUsingBoundingSphere(boundingSphereRadius)
    if modifyScene:
        view, projection = modifyScene(scene, view, projection)
    hostBitmap = RenderToSurface(scene=scene, view=view, projection=projection, size=size, bgColor=bgColor, transparent=transparent, backgroundPath=backgroundPath, overlayPath=overlayPath, techPath=techPath, postProcessingQuality=postProcessingQuality, antiAliasingQuality=antiAliasingQuality)
    hostBitmap.Save(outPath)


def _ApplyIsisEffect(ship, isSkinned):
    if isSkinned:
        isisEffect = blue.resMan.LoadObject('res:/dx9/model/ui/isisEffectSkinned.red')
    else:
        isisEffect = blue.resMan.LoadObject('res:/dx9/model/ui/isisEffect.red')
    blue.resMan.Wait()
    areaCount = ship.mesh.geometry.GetMeshAreaCount(0)
    resourceList = ship.mesh.opaqueAreas[0].effect.resources
    normalMapParam = [ res for res in resourceList if res.name == 'NormalMap' ][0]
    if hasattr(normalMapParam, 'lodResource'):
        normalMapPath = normalMapParam.lodResource.highDetailResPath
    else:
        normalMapPath = normalMapParam.resourcePath
    del ship.spriteSets[:]
    del ship.spotlightSets[:]
    del ship.planeSets[:]
    del ship.decals[:]
    del ship.mesh.opaqueAreas[:]
    del ship.mesh.depthAreas[:]
    del ship.mesh.transparentAreas[:]
    del ship.mesh.additiveAreas[:]
    del ship.mesh.decalAreas[:]
    del ship.mesh.distortionAreas[:]
    area = trinity.Tr2MeshArea()
    area.index = 0
    area.count = areaCount
    area.effect = isisEffect
    normalMap = [ res for res in area.effect.resources if res.name == 'NormalMap' ][0]
    normalMap.resourcePath = normalMapPath
    ship.mesh.additiveAreas.append(area)


def RenderISISObject(outPath, model, isSkinned, size = 128):
    """
    Generates a render for ISIS. This render fixes the camera to the side and
    applies a specialized shader to the model.
    Assumption: This is only used for V3/V5 Ships.
    """
    scene = trinity.EveSpaceScene()
    SetupModel(model)
    _ApplyIsisEffect(model, isSkinned)
    scene.objects.append(model)
    blue.resMan.Wait()
    blue.os.Pump()
    view = projection = None
    if model:
        boundingSphereRadius = model.GetBoundingSphereRadius()
        angle = (-1.5708, 0, 0)
        if model.mesh is not None:
            geometry = model.mesh.geometry
            boundingSphereCenter = model.GetBoundingSphereCenter()
            view, projection = camera_util.GetViewAndProjectionUsingMeshGeometry(geometry, scene=scene, boundingSphereRadius=boundingSphereRadius, boundingSphereCenter=boundingSphereCenter, cameraAngle=angle)
    hostBitmap = RenderToSurface(scene=scene, view=view, projection=projection, size=size, transparent=False)
    hostBitmap.Save(outPath)
    trinity.app.ProcessMessages()


def RenderISISObjectRedFile(outPath, objectPath = '', isSkinned = False, size = 128):
    """
    Generates a render for ISIS. This render fixes the camera to the side and
    applies a specialized shader to the model.
    Assumption: This is only used for V3/V5 Ships.
    """
    model = blue.resMan.LoadObject(objectPath)
    blue.resMan.Wait()
    RenderISISObject(outPath, model, isSkinned, size)


def FitTurret(ship, slot, turretPath, turretFaction, shipFaction = 'None'):
    turretSet = blue.resMan.LoadObject(turretPath)
    turretSet.slotNumber = slot
    turretSet.bottomClipHeight = 0.0
    ship.turretSets.append(turretSet)
    ship.RebuildTurretPositions()
    turretSet.FreezeHighDetailLOD()
    factory = GetSofFactory()
    factory.SetupTurretMaterial(turretSet, shipFaction, turretFaction)
    return turretSet


def RenderTurret(outPath, turretPath, turretFaction, size = 128, bgColor = None, transparent = False, usePreviewScene = True, postProcessingQuality = 2, antiAliasingQuality = 3):
    """
    Renders a turret at a given resolution.
    """
    if usePreviewScene:
        scene = blue.resMan.LoadObject('res:/dx9/scene/fitting/previewTurrets.red')
        model = blue.resMan.LoadObject('res:/dx9/model/ship/IconPreview/PreviewTurretShip.red')
    else:
        scene = blue.resMan.LoadObject('res:/dx9/Scene/preview/ship_other.red')
        scene.sunDirection = (-0.5, -0.5, 0.6)
        scene.sunDiffuseColor = (2.0, 2.0, 2.0)
        scene.ambientColor = (0.0, 0.0, 0.0)
        model = blue.resMan.LoadObject('res:/dx9/model/ship/IconPreview/PhotoServiceTurretShip.red')
    turretSet = FitTurret(model, 1, turretPath, turretFaction)
    blue.resMan.Wait()
    scene.objects.append(model)
    if transparent:
        scene.backgroundRenderingEnabled = False
    boundingSphereRadius = turretSet.boundingSphere[3] * 0.9
    boundingSphereCenter = turretSet.boundingSphere[:3]
    view, projection = camera_util.GetViewAndProjectionUsingBoundingSphere(boundingSphereRadius, boundingSphereCenter, cameraAngle=(0.7, -0.6, 0.0), fov=0.5)
    hostBitmap = RenderToSurface(scene=scene, view=view, projection=projection, size=size, bgColor=bgColor, transparent=transparent, postProcessingQuality=postProcessingQuality, antiAliasingQuality=antiAliasingQuality)
    hostBitmap.Save(outPath)


DEFAULT_SCENE_PATH = 'res:/dx9/Scene/preview/ship_other.red'

def GetScenePathByRaceID(raceID):
    """
    Return the scene path associated with a specific raceID.
    """
    scenePaths = {const.raceCaldari: 'res:/dx9/Scene/preview/ship_caldari.red',
     const.raceMinmatar: 'res:/dx9/Scene/preview/ship_minmatar.red',
     const.raceGallente: 'res:/dx9/Scene/preview/ship_gallente.red',
     const.raceAmarr: 'res:/dx9/Scene/preview/ship_amarr.red'}
    return scenePaths.get(raceID, DEFAULT_SCENE_PATH)


def RenderPin(outPath, objectPath, size = 128, freezeTime = True):
    """
    Takes a picture of a Planetary Interaction UI model.
    """
    if freezeTime:
        FreezeTime()
    model = blue.resMan.LoadObject(objectPath)
    blue.resMan.Wait()
    blue.os.Pump()
    if hasattr(model, 'curveSets'):
        model.curveSets.removeAt(-1)
    scene = trinity.EveSpaceScene()
    scene.sunDirection = (-0.5, -0.5, -0.6)
    scene.objects.append(model)
    bgColor = (0.0, 0.0, 0.0, 1.0)
    transparent = False
    if model.mesh != None:
        bBoxMin = (0.0, 0.0, 0.0)
        bBoxMax = (0.0, 0.0, 0.0)
        for i in range(model.mesh.geometry.GetMeshAreaCount(0)):
            boundingBoxMin, boundingBoxMax = model.mesh.geometry.GetAreaBoundingBox(0, i)
            if abs(boundingBoxMax[1] - boundingBoxMin[1]) > 0.005:
                if geo2.Vec3Length(bBoxMin) < geo2.Vec3Length(boundingBoxMin):
                    bBoxMin = boundingBoxMin
                if geo2.Vec3Length(bBoxMax) < geo2.Vec3Length(boundingBoxMax):
                    bBoxMax = boundingBoxMax

        view, projection = camera_util.GetViewAndProjectionUsingBoundingBox(bBoxMin, bBoxMax)
        hostBitmap = RenderToSurface(scene=scene, view=view, projection=projection, size=size, bgColor=bgColor, transparent=transparent)
        hostBitmap.Save(outPath)


def SetupLensflare(lensflare):
    lensflare.position = (0.0, 0.0, -1.0)
    lensflare.translationCurve = None
    lensflare.doOcclusionQueries = False
    for flare in lensflare.flares:
        for param in flare.Find(['trinity.Tr2FloatParameter']):
            if param.name == 'mainSizeFactor':
                param.value = param.value + 1.0


def RenderSun(outPath, objectPath, scenePath, size = 512, cameraAngle = (0, 0, 0), postProcessingQuality = 2, antiAliasingQuality = 3, modifyScene = None):
    scene = trinity.Load(scenePath)
    blue.resMan.Wait()
    lensflare = blue.resMan.LoadObject(objectPath)
    blue.resMan.Wait()
    blue.os.Pump()
    scene.lensflares.append(lensflare)
    SetupLensflare(lensflare)
    fov = 1.0
    boundingSphereRadius = 100.0
    boundingSphereCenter = (0.0, 0.0, 0.0)
    view, projection = camera_util.GetViewAndProjectionUsingBoundingSphere(boundingSphereRadius, boundingSphereCenter, cameraAngle=cameraAngle, fov=fov)
    if modifyScene:
        view, projection = modifyScene(scene, view, projection)
    hostBitmap = RenderToSurface(scene=scene, view=view, projection=projection, size=size, postProcessingQuality=postProcessingQuality, antiAliasingQuality=antiAliasingQuality)
    hostBitmap.Save(outPath)


def GetIconFileFromSheet(iconNo):
    """Gets an icon path given the iconNo from FSD. Can return None.
    
    The iconNo gotten from FSD is not always a valid path.
    It can be sheet and index seperated by an underscore. In this case we need
    the size in order to construct the path. the method _GetIconSize is used
    for this.
    If the iconNo starts with 'ui_' it already contains all the necessary 
    information to construct the path.
    
    This is legacy code from hell (uix.py).
    
    TODO make test
    """

    def _GetIconSize(sheetNum):
        """
        This code is copied from uix.py
        """
        sheetNum = int(sheetNum)
        one = [90,
         91,
         92,
         93]
        two = [17,
         18,
         19,
         28,
         29,
         32,
         33,
         59,
         60,
         61,
         65,
         66,
         67,
         80,
         85,
         86,
         87,
         88,
         89,
         102,
         103,
         104]
        eight = [22,
         44,
         75,
         77,
         105]
        sixteen = [38, 73]
        if sheetNum in one:
            return 256
        if sheetNum in two:
            return 128
        if sheetNum in eight:
            return 32
        if sheetNum in sixteen:
            return 16
        return 64

    if not iconNo:
        return
    if 'res:' in iconNo or 'cache:' in iconNo:
        return iconNo
    if iconNo.startswith('ui_'):
        return iconNo.replace('ui_', 'res:/ui/texture/icons/')
    parts = iconNo.split('_')
    if len(parts) == 2:
        sheet, ix = parts
        size = _GetIconSize(sheet)
        return 'res:/ui/texture/icons/%s_%s_%s.png' % (int(sheet), int(size), int(ix))


def RenderApparel(outPath, sourceRes, size = 128):
    """
    "Renders" apparel by just copying the sourceRes image to the outPath
    and downsizing if needed.
    Eventually this will be a proper rendering,
    but this is as good as we can do for now.
    """
    from PIL import Image
    remotefilecache.prefetch_single_file(sourceRes)
    src = blue.paths.ResolvePath(sourceRes)
    im = Image.open(src)
    if im.size > (size, size):
        im = im.resize((size, size), Image.ANTIALIAS)
    im.save(outPath)
