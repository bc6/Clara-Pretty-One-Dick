#Embedded file name: eve/client/script/paperDoll\SkinLightmapRenderer.py
import trinity
import blue
import telemetry
import weakref
import itertools
import log
import commonClientFunctions as pdCcf
from eve.common.script.paperDoll import paperDollCommonFunctions as pdCf

def LogError(*args):
    log.Log(' '.join(map(strx, args)), log.LGERR)


class SkinLightmapRenderer:
    """
    Class that encapsulates all the setup and shader work that happens when subsurface scattering is enabled.
    
    The big outline of the algorithm is as follows:
    
    1. Data setup: user sets the single visual model, as well as the individual meshes inside this visual
       model, that must be rendered with scattering
    
    2. Engine setup: render these meshes using a Stretchmap shader to a render target; this map is then used in
       the scattering step to compensate for distortion in the UV mapping.
       (We always want to bleed light over the same distance in world space -- a couple of mm -- but the coverage
        of a texel in the lightmap changes due to stretching.  This map compensates that).
    
    3. Render loop:
        - a recurring renderjob renders the meshes out to a rendertarget, using a shader that only calculates diffuse light
          Python callbacks are used to make sure that this step only draws the meshes that are scattering, and doesn't
          render the shadow maps (we reuse those from the last frame);
        - a recurring renderjob then scatters this lightmap; it uses the stretchmap as well as a noise map to randomly rotate
          the poisson disk per pixel.  This is a single step, using the simplification from ShaderX7 instead of 6 gaussians.
        - a callback on the previous renderjob attaches a shader to the meshes that will do skin shading, except it takes its
          diffuse light from the scattered map prepared by the previous renderjob.  Actually rendering them will then just
          happen using regular RenderScene() from trinity -- no further renderjobs are needed.
    
    See
    http://http.developer.nvidia.com/GPUGems3/gpugems3_ch14.html
    http://carbon/wiki/Portrait_Skin_Shader
    """
    __guid__ = 'paperDoll.SkinLightmapRenderer'
    renderJob = None
    scene = None
    instances = set({})

    @staticmethod
    def Scene():
        """
        Helper to protect from jessica not using renderjobs; grab scene from the device if weak ref is not set
        """
        if SkinLightmapRenderer.scene is None or SkinLightmapRenderer.scene.object is None:
            jobs = trinity.renderJobs.recurring
            for job in jobs:
                if 'paperdoll' in job.name.lower():
                    return job.steps[0].object

            return
        return SkinLightmapRenderer.scene.object

    LIGHTMAP_RENDERER_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFLightmapUnwrap_Single.fx'
    LIGHTMAP_RENDERER_DOUBLE_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFLightmapUnwrap_Double.fx'
    STRETCHMAP_RENDERER_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFStretchmap.fx'
    LIGHTMAP_SCATTER_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/LightmapScatter.fx'
    LIGHTMAP_EXPAND_EFFECT = 'res:/Graphics/Effect/Utility/Compositing/ExpandOpaqueNoMask.fx'
    BECKMANN_LOOKUP_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFBeckmannLookup.fx'
    LIGHTMAP_APPLICATION_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFLightmapApplication_Single.fx'
    LIGHTMAP_APPLICATION_DOUBLE_EFFECT = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFLightmapApplication_Double.fx'

    class Mesh:

        def __init__(self):
            self.origEffect = {}
            self.stretchmapRenderEffect = {}
            self.lightmapRenderEffect = {}
            self.lightmapApplyEffect = {}
            self.liveParameters = []

        def ExtractOrigEffect(self, mesh):
            for area in itertools.chain(mesh.opaqueAreas, mesh.decalAreas):
                pdCcf.AddWeakBlue(self, 'origEffect', area, area.effect)

            return len(self.origEffect) > 0

    @staticmethod
    def CreateRenderTarget(width, height, format, useRT = False):
        return trinity.TriTextureRes(trinity.Tr2RenderTarget(width, height, 1, format))

    @telemetry.ZONE_METHOD
    def CreateRenderTargets(self, lightmapFormat):
        """
        See if the hardware supports self.lightmapSize with the given format.
        """
        try:
            self.lightmap = self.CreateRenderTarget(self.lightmapSize[0], self.lightmapSize[1], lightmapFormat)
            self.stretchmap = self.CreateRenderTarget(min(1024, self.lightmapSize[0]), min(1024, self.lightmapSize[1]), lightmapFormat)
            self.scatteredLightmap = self.CreateRenderTarget(self.lightmapSize[0], self.lightmapSize[1], lightmapFormat)
            self.depth = trinity.Tr2DepthStencil(self.lightmapSize[0], self.lightmapSize[1], trinity.DEPTH_STENCIL_FORMAT.D24S8)
        except Exception:
            self.lightmap = None
            self.stretchmap = None
            self.scatteredLightmap = None
            return False

        return True

    @telemetry.ZONE_METHOD
    def AddTex2D(self, effect, name, resourcePath = None):
        """
        Helper to save typing when attaching texture maps to an effect.
        """
        param = trinity.TriTexture2DParameter()
        param.name = name
        if resourcePath is not None:
            param.resourcePath = resourcePath
        effect.resources.append(param)
        return param

    def Print(self, msg):
        print '[Skin]', msg

    def DebugPrint(self, msg):
        pass

    @telemetry.ZONE_METHOD
    def __init__(self, highQuality = True, useHDR = True):
        """
        Preload a number of effects, create rendertargets;
        """
        if True:
            raytraceWidth = 2048
            raytraceHeight = 2048
        else:
            raytraceWidth = 512
            raytraceHeight = 512
        self.raytracing = None
        self.refreshMeshes = False
        self.skinMapPath = None
        self.precomputeBeckmann = False
        self.useExpandOpaque = False
        self.lightmapEffectPreload = self.PreloadEffect(self.LIGHTMAP_RENDERER_EFFECT)
        self.lightmapDoubleEffectPreload = self.PreloadEffect(self.LIGHTMAP_RENDERER_DOUBLE_EFFECT)
        self.stretchmapEffectPreload = self.PreloadEffect(self.STRETCHMAP_RENDERER_EFFECT)
        self.lightmapApplicationEffectPreload = self.PreloadEffect(self.LIGHTMAP_APPLICATION_EFFECT)
        self.lightmapApplicationDoubleEffectPreload = self.PreloadEffect(self.LIGHTMAP_APPLICATION_DOUBLE_EFFECT)
        self.lightmapScatterEffect = self.PreloadEffect(self.LIGHTMAP_SCATTER_EFFECT)
        self.lightmapExpandEffect = self.PreloadEffect(self.LIGHTMAP_EXPAND_EFFECT)
        if self.precomputeBeckmann:
            self.beckmannLookupEffect = self.PreloadEffect(self.BECKMANN_LOOKUP_EFFECT)
        self.skinnedObject = None
        self.paramLightmap = self.AddTex2D(self.lightmapScatterEffect, 'Lightmap')
        self.paramStretchmap = self.AddTex2D(self.lightmapScatterEffect, 'Stretchmap')
        self.paramNoisemap = self.AddTex2D(self.lightmapScatterEffect, 'Noisemap', 'res:/Texture/Global/noise.png')
        self.paramSkinMap = self.AddTex2D(self.lightmapScatterEffect, 'SkinMap')
        self.paramExpandSource = self.AddTex2D(self.lightmapExpandEffect, 'Texture')
        self.paramDiffuseScattermap = self.AddTex2D(self.lightmapApplicationEffectPreload, 'DiffuseScatterMap')
        self.paramDiffusemap = self.AddTex2D(self.lightmapApplicationEffectPreload, 'DiffuseMap')
        if self.precomputeBeckmann:
            self.paramBeckmannLookup = self.AddTex2D(self.lightmapApplicationEffectPreload, 'BeckmannLookup')
        if highQuality:
            self.lightmapSize = (2048, 2048)
        else:
            self.lightmapSize = (512, 512)
        lightmapFormat = []
        if useHDR:
            lightmapFormat = [trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT]
        lightmapFormat.append(trinity.PIXEL_FORMAT.B8G8R8X8_UNORM)
        lightmapFormat.append(trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        lightmapFormat.append(trinity.PIXEL_FORMAT.R8G8B8A8_UNORM)
        self.lightmapRenderJob = None
        setupOK = False
        for format in lightmapFormat:
            if self.CreateRenderTargets(format):
                setupOK = True
                break

        if not setupOK:
            self.lightmapSize = (self.lightmapSize[0] / 2, self.lightmapSize[1] / 2)
            for format in lightmapFormat:
                if self.CreateRenderTargets(format):
                    setupOK = True
                    break

            if setupOK:
                self.Print('Warning: needed to downsize the lightmap resolution')
            else:
                self.Print("Error: couldn't find any lightmap render format that works :(")
                return
        if self.precomputeBeckmann:
            try:
                self.beckmannLookup = self.CreateRenderTarget(256, 256, trinity.PIXEL_FORMAT.R8_UNORM)
                self.RenderBeckmannLookup()
            except Exception:
                self.Print("[Skin] Error: can't create specular lookup table texture")
                return

        self.meshes = {}
        SkinLightmapRenderer.instances.add(weakref.ref(self))

    @telemetry.ZONE_METHOD
    def __del__(self):
        newSet = set({})
        for instance in SkinLightmapRenderer.instances:
            if instance():
                newSet.add(instance)

        SkinLightmapRenderer.instances = newSet
        self.StopRendering()
        self.RestoreShaders()

    @staticmethod
    def PreloadEffect(path):
        """
        Helper for preloading effect: create it, wait on blue, rebuild it.
        """
        effect = trinity.Tr2Effect()
        effect.effectFilePath = path
        while effect.effectResource.isLoading:
            pdCf.Yield()

        effect.RebuildCachedData()
        return effect

    @telemetry.ZONE_METHOD
    def CreateExtraMaps(self, effect):
        """
        Helper function for making sure certains maps exist, adding it if needed
        """
        res = self.FindResource(effect, 'DiffuseScatterMap')
        if res is None:
            res = self.AddTex2D(effect, 'DiffuseScatterMap')
        res.SetResource(self.lightmap if self.useExpandOpaque else self.scatteredLightmap)
        res = self.FindResource(effect, 'BeckmannLookup')
        if res is None:
            if self.precomputeBeckmann:
                res = self.AddTex2D(effect, 'BeckmannLookup')
            else:
                res = self.AddTex2D(effect, 'BeckmannLookup', 'res:/Texture/Global/beckmannSpecular.dds')
        if self.precomputeBeckmann:
            res.SetResource(self.beckmannLookup)

    @staticmethod
    def FindResource(effect, name):
        for r in effect.resources:
            if r.name == name:
                return r

    @staticmethod
    def DuplicateResource(targetEffect, sourceEffect, name):
        """
        Make sure a resource called name exists on targetEffect, pointing back to sourceEffect
        """
        p = trinity.TriTexture2DParameter()
        p.name = name
        p.SetResource(SkinLightmapRenderer.FindResource(sourceEffect, name).resource)
        targetEffect.resources.append(p)

    @staticmethod
    def DuplicateEffect(fx, newPath, dupResources = True):
        newEffect = trinity.Tr2Effect()
        newEffect.effectFilePath = newPath
        newEffect.parameters = fx.parameters
        newEffect.name = fx.name
        if dupResources:
            for r in fx.resources:
                SkinLightmapRenderer.DuplicateResource(newEffect, fx, r.name)

        newEffect.PopulateParameters()
        newEffect.RebuildCachedData()
        return newEffect

    @telemetry.ZONE_METHOD
    def AddMesh(self, mesh):
        """
        Add a mesh to the list of items that need to be scattered.  It must be from the visual model that was
        previous set with setSkinnedObject().
        We don't actually support multiple objects, since they each require their own rendertarget and renderjobs.
        What we support however is a multiple opaque areas in the same mesh, eg head[1..5] and such.
        
        The needed setup for a mesh is
        - set them up with the same resources as the original effect
        - set up for resources they need (scattermap, specular lookup table, etc)
        """
        if mesh is None or self.lightmap is None:
            return

        def SetupSkinMap():
            for a in itertools.chain(mesh.opaqueAreas, mesh.decalAreas):
                if a.effect is not None and a.effect.resources is not None:
                    for e in a.effect.resources:
                        if e.name == 'SkinMap':
                            self.skinMapPath = e.resourcePath
                            self.paramSkinMap.resourcePath = self.skinMapPath
                            return

        if self.skinMapPath is None:
            SetupSkinMap()
        m = self.Mesh()
        if not m.ExtractOrigEffect(mesh):
            return
        for areaRef, fx in m.origEffect.iteritems():
            if areaRef.object is None:
                continue
            if pdCcf.IsBeard(areaRef.object):
                pdCcf.AddWeakBlue(m, 'lightmapRenderEffect', areaRef.object, None)
                pdCcf.AddWeakBlue(m, 'lightmapApplyEffect', areaRef.object, fx)
                pdCcf.AddWeakBlue(m, 'stretchmapRenderEffect', areaRef.object, None)
                continue
            wasDouble = 'double' in fx.effectFilePath.lower()
            singleApply = self.LIGHTMAP_APPLICATION_EFFECT
            doubleApply = self.LIGHTMAP_APPLICATION_DOUBLE_EFFECT
            lightmapRenderEffect = SkinLightmapRenderer.DuplicateEffect(fx, self.LIGHTMAP_RENDERER_DOUBLE_EFFECT if wasDouble else self.LIGHTMAP_RENDERER_EFFECT)
            lightmapApplyEffect = SkinLightmapRenderer.DuplicateEffect(fx, doubleApply if wasDouble else singleApply)
            pdCcf.AddWeakBlue(m, 'lightmapRenderEffect', areaRef.object, lightmapRenderEffect)
            pdCcf.AddWeakBlue(m, 'lightmapApplyEffect', areaRef.object, lightmapApplyEffect)
            stretchmapRenderEffect = trinity.Tr2Effect()
            stretchmapRenderEffect.effectFilePath = self.STRETCHMAP_RENDERER_EFFECT
            stretchmapRenderEffect.parameters = fx.parameters
            pdCcf.AddWeakBlue(m, 'stretchmapRenderEffect', areaRef.object, stretchmapRenderEffect)
            m.liveParameters.append(filter(lambda r: r[0].name.startswith('WrinkleNormalStrength') or r[0].name.startswith('spotLight'), zip(fx.parameters, lightmapRenderEffect.parameters, lightmapApplyEffect.parameters)))
            self.CreateExtraMaps(lightmapApplyEffect)
            stretchmapRenderEffect.PopulateParameters()
            stretchmapRenderEffect.RebuildCachedData()
            if False:
                self.DebugPrint('lightmapRenderEffect resources:')
                for p in lightmapRenderEffect.resources:
                    self.DebugPrint(p.name)

                self.DebugPrint('lightmapApplyEffect resources:')
                for p in lightmapApplyEffect.resources:
                    self.DebugPrint(p.name)

        pdCcf.AddWeakBlue(self, 'meshes', mesh, m)

    @staticmethod
    def DoChangeEffect(attrName, meshes):
        for meshRef, meshData in meshes.iteritems():
            mesh = meshRef.object
            count = 0
            dictionary = getattr(meshData, attrName)
            for areaRef, effect in dictionary.iteritems():
                if areaRef.object is not None:
                    areaRef.object.effect = effect

    def ChangeEffect(self, attrName, meshes = None):
        """
        Change the effect on every mesh to point to mesh.attrName.
        Used to swap out effects before doing custom rendersteps.
        """
        if meshes is None:
            meshes = self.meshes
        SkinLightmapRenderer.DoChangeEffect(attrName, meshes)

    @staticmethod
    def DoRestoreShaders(meshes):
        for meshRef, meshData in meshes.iteritems():
            mesh = meshRef.object
            for areaRef, effect in meshData.origEffect.iteritems():
                if areaRef.object:
                    areaRef.object.effect = effect

    @telemetry.ZONE_METHOD
    def RestoreShaders(self, meshes = None):
        """
        Reset the mesh effects to their original.
        Used to restore things to normal after doing custom rendersteps.
        """
        if meshes is None:
            meshes = self.meshes
        SkinLightmapRenderer.DoRestoreShaders(meshes)

    @staticmethod
    def IsScattering(mesh):
        if mesh.name.startswith('head'):
            for a in mesh.opaqueAreas:
                if a.effect is not None:
                    name = a.effect.name.lower()
                    if name.startswith('c_skin') and 'tearduct' not in name:
                        return True

        return False

    @telemetry.ZONE_METHOD
    def BindLightmapShader(self, mesh):
        if SkinLightmapRenderer.IsScattering(mesh):
            self.AddMesh(mesh)
            return True
        return False

    @telemetry.ZONE_METHOD
    def SetSkinnedObject(self, skinnedObject):
        """
        Indicate which visual model we want to use the shader on.  Only supports one at the same time.
        """
        if self.skinnedObject != skinnedObject or self.refreshMeshes:
            self.skinnedObject = skinnedObject
            self.meshes = {}
        self.refreshMeshes = False
        if skinnedObject is None or skinnedObject.visualModel is None:
            return
        haveNewMeshes = False
        for mesh in skinnedObject.visualModel.meshes:
            for meshRef in self.meshes:
                if meshRef.object == mesh:
                    break
            else:
                haveNewMeshes = self.BindLightmapShader(mesh) or haveNewMeshes

        scene = SkinLightmapRenderer.Scene()
        scene.filterList.removeAt(-1)
        scene.filterList.append(skinnedObject)
        if haveNewMeshes:
            self.RenderStretchmap()

    @telemetry.ZONE_METHOD
    def Refresh(self, immediateUpdate = False):
        self.refreshMeshes = True
        if immediateUpdate:
            self.SetSkinnedObject(self.skinnedObject)

    @staticmethod
    def DoCopyMeshesToVisual(skinnedObject, meshList):
        """
        Helper to transfer one blue list of meshes to another; transfer meshList to self.skinnedObject.visualModel.meshes
        """
        if skinnedObject is None or skinnedObject.visualModel is None:
            return
        skinnedObject.visualModel.meshes.removeAt(-1)
        for mesh in meshList:
            skinnedObject.visualModel.meshes.append(mesh)

    @telemetry.ZONE_METHOD
    def CopyMeshesToVisual(self, meshList):
        """
        Helper to transfer one blue list of meshes to another; transfer meshList to self.skinnedObject.visualModel.meshes
        """
        SkinLightmapRenderer.DoCopyMeshesToVisual(self.skinnedObject, meshList)

    @telemetry.ZONE_METHOD
    def OnBeforeUnwrap(self):
        """
        Renderstep Callback to prepare things for the lightspace unwrap.
        """
        self.ChangeEffect('lightmapRenderEffect')
        scene = SkinLightmapRenderer.Scene()
        if hasattr(scene, 'updateShadowCubeMap'):
            scene.updateShadowCubeMap = False
        if self.skinnedObject is not None and self.skinnedObject.visualModel is not None:
            self.savedMeshes = self.skinnedObject.visualModel.meshes[:]
        filteredMeshes = [ ref.object for ref in self.meshes.iterkeys() if ref.object is not None ]
        self.CopyMeshesToVisual(filteredMeshes)
        for meshData in self.meshes.itervalues():
            for list in meshData.liveParameters:
                for params in list:
                    params[1].value = params[0].value
                    params[2].value = params[0].value

        scene.useFilterList = True
        trinity.settings.SetValue('apexVisualizeOnly', True)

    @telemetry.ZONE_METHOD
    def OnAfterUnwrap(self):
        """
        Renderstep Callback post-unwrap to reset things to normal.
        Not resetting shaders as we'll continue with light application next anyway.
        """
        scene = SkinLightmapRenderer.Scene()
        if hasattr(scene, 'updateShadowCubeMap'):
            scene.updateShadowCubeMap = True
        if hasattr(self, 'savedMeshes'):
            self.CopyMeshesToVisual(self.savedMeshes)
            del self.savedMeshes
        scene.useFilterList = False
        trinity.settings.SetValue('apexVisualizeOnly', False)

    @telemetry.ZONE_METHOD
    def CreateRJ(self, target, name, depthClear = 0.0, setDepthStencil = True, clearColor = (0.125, 0.125, 0.125, 1.0), isRT = False):
        """
        Helper method to create a renderjob that has a target and viewport matching the target argument.
        """
        rj = trinity.CreateRenderJob(name)
        rj.PushRenderTarget(target.wrappedRenderTarget).name = name
        if setDepthStencil:
            rj.PushDepthStencil(self.depth)
        rj.Clear(clearColor, depthClear)
        rj.SetStdRndStates(trinity.RM_FULLSCREEN)
        vp = trinity.TriViewport()
        vp.x = 0
        vp.y = 0
        if False:
            rdesc = target.GetDesc()
            vp.width = rdesc['Width']
            vp.height = rdesc['Height']
        else:
            vp.width = target.width
            vp.height = target.height
        rj.SetViewport(vp)
        return rj

    @telemetry.ZONE_METHOD
    def RenderBeckmannLookup(self):
        """
        Helper function that creates a schedule-once renderjob to precompute a lookup texture for the expensive bits in
        Beckmann specular.  An optimization by the book from Gems 3.  Ends up in self.beckmannLokup
        """
        rj = self.CreateRJ(self.beckmannLookup, 'Beckmann precalc')
        rj.SetDepthStencil(None)
        rj.RenderEffect(self.beckmannLookupEffect)
        rj.PopRenderTarget()
        rj.PopDepthStencil()
        rj.ScheduleOnce()

    @staticmethod
    def FuncWrapper(weakSelf, func):
        if weakSelf():
            func(weakSelf())

    @telemetry.ZONE_METHOD
    def AddCallback(self, func, name, rj = None):
        cb = trinity.TriStepPythonCB()
        weakSelf = weakref.ref(self)
        cb.SetCallback(lambda : SkinLightmapRenderer.FuncWrapper(weakSelf, func))
        cb.name = name
        rj = rj if rj is not None else self.lightmapRenderJob
        rj.steps.append(cb)

    @telemetry.ZONE_METHOD
    def RenderStretchmap(self):
        """
        Create a stretchmap: simply apply a custom shader to a schedule-once renderjob and store the result to self.stretchmap
        """
        if SkinLightmapRenderer.Scene() is None:
            return
        rj = self.CreateRJ(self.stretchmap, 'Stretchmap precalc', depthClear=None, setDepthStencil=False)
        rj.PushDepthStencil(None)
        self.AddCallback(SkinLightmapRenderer.OnBeforeUnwrap, 'onBeforeUnwrap', rj)
        self.AddCallback(lambda weakSelf: weakSelf.ChangeEffect('stretchmapRenderEffect'), 'change to stretch effect', rj)
        rj.Update(SkinLightmapRenderer.Scene())
        rj.RenderScene(SkinLightmapRenderer.Scene())
        self.AddCallback(SkinLightmapRenderer.OnAfterUnwrap, 'onAfterUnwrap', rj)
        self.AddCallback(SkinLightmapRenderer.RestoreShaders, 'restoreShaders', rj)
        rj.PopDepthStencil()
        rj.PopRenderTarget()
        rj.ScheduleOnce()

    @telemetry.ZONE_METHOD
    def OnBeforeBlur(self):
        """
        Renderstep Callback: Blur pass setup; grab the lightmap, which was last step's rendertarget, and set it as a sampler.
        """
        rj = self.lightmapRenderJob
        self.paramLightmap.SetResource(self.lightmap)
        self.paramStretchmap.SetResource(self.stretchmap)

    @telemetry.ZONE_METHOD
    def OnBeforeExpand(self):
        rj = self.lightmapRenderJob
        self.paramExpandSource.SetResource(self.scatteredLightmap)

    @telemetry.ZONE_METHOD
    def OnAfterExpand(self):
        """
        Renderstep Callback: Scatter blur + expand is done, so set its rendertarget as 'DiffuseScatterMap', and attach shaders to the scene to do the final render with it;
        """
        rj = self.lightmapRenderJob
        self.ChangeEffect('lightmapApplyEffect')

    @telemetry.ZONE_METHOD
    def SetViewport(self, rj, width, height):
        vp = trinity.TriViewport()
        vp.x = 0
        vp.y = 0
        vp.width = width
        vp.height = height
        rj.SetViewport(vp)

    @telemetry.ZONE_METHOD
    def RenderLightmap(self):
        """
        Create all renderjobs needed to do the whole thing:
        1. Render the scene using a light unwrap shader, saving out diffuse shading only
        2. Dipole blur this map
        3. Render the scene again with regular shading, except that all diffuse lighting comes from the output of step 2.
           This is actually part of the main rendering, we just need to make sure we exit with a decent setup (effect in place, step 2 RT attached)
        """
        rj = self.CreateRJ(self.lightmap, 'Lightmap rendering', depthClear=None, setDepthStencil=False, clearColor=(0, 0, 0, 0))
        self.lightmapRenderJob = rj
        self.AddCallback(SkinLightmapRenderer.OnBeforeUnwrap, 'onBeforeUnwrap')
        doHighZOptimization = False
        if not doHighZOptimization:
            rj.PushDepthStencil(None).name = 'Depthbuffer = None'
        rj.RenderScene(SkinLightmapRenderer.Scene()).name = 'Unwrap light pass'
        self.AddCallback(SkinLightmapRenderer.OnAfterUnwrap, 'onAfterUnwrap')
        rj.SetRenderTarget(self.scatteredLightmap.wrappedRenderTarget).name = 'Set Scattermap RT'
        self.AddCallback(SkinLightmapRenderer.OnBeforeBlur, 'onBeforeBlur')
        rj.SetStdRndStates(trinity.RM_FULLSCREEN)
        rj.RenderEffect(self.lightmapScatterEffect).name = 'Light blur pass'
        if self.useExpandOpaque:
            rj.SetRenderTarget(self.lightmap.wrappedRenderTarget).name = 'Set Lightmap RT for expand'
            self.AddCallback(SkinLightmapRenderer.OnBeforeExpand, 'onBeforeExpand')
            rj.RenderEffect(self.lightmapExpandEffect).name = 'Expand lightmap'
        self.AddCallback(SkinLightmapRenderer.OnAfterExpand, 'onAfterExpand')
        rj.PopRenderTarget().name = 'PopRT - main scene rendering'
        if not doHighZOptimization:
            rj.PopDepthStencil()
        if SkinLightmapRenderer.renderJob is not None and SkinLightmapRenderer.renderJob.object is not None:
            step = trinity.TriStepRunJob()
            step.job = rj
            SkinLightmapRenderer.renderJob.object.steps.append(step)
        else:
            jobs = trinity.renderJobs.recurring
            for job in jobs:
                if 'paperdoll' in job.name.lower():
                    step = trinity.TriStepRunJob(rj)
                    step.name = rj.name
                    job.steps.insert(len(job.steps) - 1, step)
                    break
            else:
                rj.ScheduleRecurring()

    @staticmethod
    def SaveTarget(target, path, isRT = False):
        """
        Debug helper to save RT
        """
        if type(target) == trinity.Tr2RenderTarget:
            trinity.Tr2HostBitmap(target).Save(path)
        else:
            target.Save(path)

    def IsRendering(self):
        return self.lightmapRenderJob is not None

    @telemetry.ZONE_METHOD
    def StartRendering(self):
        if self.lightmap is None:
            return
        if self.lightmapRenderJob is not None:
            return
        self.RenderLightmap()

    @telemetry.ZONE_METHOD
    def StopRendering(self):
        if self.lightmapRenderJob is None:
            return
        if SkinLightmapRenderer.renderJob is not None and SkinLightmapRenderer.renderJob.object is not None:
            for step in SkinLightmapRenderer.renderJob.object.steps:
                if step.job == self.lightmapRenderJob:
                    SkinLightmapRenderer.renderJob.object.steps.remove(step)
                    break

        else:
            self.lightmapRenderJob.UnscheduleRecurring()
        self.lightmapRenderJob = None

    def CreateScatterStep(renderJob, scene, append = True):
        step = trinity.TriStepRunJob()
        step.name = 'Subsurface scattering'
        step.job = trinity.CreateRenderJob('Render scattering')
        if append:
            renderJob.steps.append(step)
        SkinLightmapRenderer.renderJob = blue.BluePythonWeakRef(step.job)
        SkinLightmapRenderer.scene = blue.BluePythonWeakRef(scene)
        return step
