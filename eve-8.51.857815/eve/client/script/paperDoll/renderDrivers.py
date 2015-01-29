#Embedded file name: eve/client/script/paperDoll\renderDrivers.py
import trinity
import log
import types
import uthread
from eve.common.script.paperDoll import paperDollCommonFunctions as pdCf
import commonClientFunctions as pdCcf
from .SkinSpotLightShadows import SkinSpotLightShadows
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollConfiguration as pdCfg
import paperDollPrePassFixup
import paperDollPortrait as pdPor
from .SkinLightmapRenderer import SkinLightmapRenderer
COLLAPSED_SHADOW_EFFECT_PATH = 'res:/Graphics/Effect/Managed/Interior/Avatar/ShadowCollapsed.fx'
COLLAPSED_MATERIAL_EFFECT_PATH = 'res:/Graphics/Effect/Managed/Interior/Avatar/MaterialCollapsed.fx'
COLLAPSED_BASIC_EFFECT_PATH = 'res:/graphics/effect/managed/interior/avatar/skinnedavatarbrdflinear.fx'
COLLAPSE_USE_PD_VISUALMODEL = True

class RenderDriver:
    """
    Base definition of a render driver. Includes forwarding mechanism to support aggregation.
    """
    __guid__ = 'paperDoll.renderDrivers.RenderDriver'

    def __init__(self):
        self._chainedRenderDriver = None

    def SetChainedRenderDriver(self, chainedRenderDriver):
        """
        When called, sets next driver to call in a chain per instance method, will decorate this instance to do so
        if not already done.
        """
        if not isinstance(chainedRenderDriver, RenderDriver):
            return False
        if self._chainedRenderDriver:
            self._chainedRenderDriver = chainedRenderDriver
            return
        self._chainedRenderDriver = chainedRenderDriver
        imethods = [ (n, getattr(self, n), getattr(chainedRenderDriver, n)) for n in dir(self) if not n.startswith('_') and n != 'SetChainedRenderDriver' and type(getattr(self, n)) is types.MethodType and hasattr(chainedRenderDriver, n) ]
        for i in xrange(len(imethods)):
            imethodPair = imethods[i]
            imName = imethodPair[0]
            thisObjIM = imethodPair[1]
            nextObjIM = imethodPair[2]
            thisObjIM = setattr(self, imName, self._CallChainedDeco(thisObjIM.im_func, nextObjIM.im_func))

    def _CallChainedDeco(self, first, second):

        def wrapped(*args, **kwargs):
            extraArgs = kwargs
            newArgs = first(self, *args, **kwargs)
            if newArgs is not None:
                extraArgs.update(newArgs)
            second(self._chainedRenderDriver, *args, **extraArgs)

        return wrapped

    def OnBeginUpdate(self, doll):
        """
        Called before we do anything at all.
        """
        pass

    def OnModifierUVChanged(self, modifier):
        """
        ApplyUV just did something to the UVs of this modifier.
        """
        pass

    def OnModifierRedfileLoaded(self, modifier, redfilePath):
        """
        A modifier's red file was loaded
        
        redfileLod - redfile, adjusted for LOD and any other overrides that PD does on the fly
        """
        pass

    def OnApplyMorphTargets(self, meshes, morphTargets):
        """
        The meshes are ready and loaded and the morphTargets are known as a name -> weight dict.
        Let the driver respond to that info if needed.
        """
        pass

    def ApplyShaders(self, doll, meshes):
        pass

    def OnFinalizeAvatar(self, visualModel, avatar, updateRuleBundle, doll, factory):
        """
        Called when all meshes etc have been loaded, but async tasklets are still running.
        """
        pass

    def OnEndUpdate(self, avatar, visualModel, doll, factory, **kwargs):
        """
        Called as the very last step in Update, everything is done, including child tasklets.
        """
        pass


class RenderDriverNCC(RenderDriver):
    """
    This class encapsulates the rendering setup needed for a full forward rendered doll using
    some of portrait tools.
    """
    __guid__ = 'paperDoll.renderDrivers.RenderDriverNCC'

    def __init__(self):
        RenderDriver.__init__(self)
        self.wrinkleFx = None

    def OnBeginUpdate(self, doll):
        """
        Called before we do anything at all.
        """
        pass

    def OnModifierUVChanged(self, modifier):
        pass

    def OnModifierRedfileLoaded(self, modifier, redfilePath):
        pass

    def OnApplyMorphTargets(self, meshes, morphTargets):
        pass

    def ApplyShaders(self, doll, meshes):
        self.wrinkleFx = []
        if not meshes:
            return
        skinSpotLightShadowsActive = lambda : SkinSpotLightShadows.instance is not None
        skinLightmapRendererActive = lambda : doll.skinLightmapRenderer is not None
        tasklets = []
        asyncMeshes = {}

        def DoClothMesh(mesh):
            isHair = False
            isHair = self.BindClothShaders(mesh, doll, isHair)
            if type(mesh.effect) == trinity.Tr2Effect:
                loadingResources = []
                if mesh.effect and type(mesh.effect) == trinity.Tr2Effect:
                    loadingResources.append(mesh.effect.effectResource)
                if mesh.effectReversed:
                    loadingResources.append(mesh.effectReversed.effectResource)
                pdCf.WaitForAll(loadingResources, lambda x: x.isLoading)
                if mesh.effect:
                    mesh.effect.PopulateParameters()
                if mesh.effectReversed:
                    mesh.effectReversed.PopulateParameters()
            if SkinSpotLightShadows.instance is not None:
                SkinSpotLightShadows.instance.CreateEffectParamsForMesh(mesh, isClothMesh=True)
            if isHair and hasattr(mesh, 'useTransparentBatches'):
                mesh.useTransparentBatches = True

        for mesh in iter(meshes):
            if type(mesh) is trinity.Tr2ClothingActor:
                t = uthread.new(DoClothMesh, mesh)
            else:
                if skinSpotLightShadowsActive() or skinLightmapRendererActive():
                    asyncMeshes[mesh] = False
                if pdDef.DOLL_PARTS.HEAD in mesh.name:
                    t = uthread.new(self.SetInteriorShader, *(asyncMeshes,
                     mesh,
                     self.wrinkleFx,
                     doll))
                else:
                    t = uthread.new(self.SetInteriorShader, *(asyncMeshes,
                     mesh,
                     None,
                     doll))
            tasklets.append(t)
            uthread.schedule(t)

        pdCf.WaitForAll(tasklets, lambda x: x.alive)
        for mesh in asyncMeshes.iterkeys():
            if skinSpotLightShadowsActive():
                SkinSpotLightShadows.instance.CreateEffectParamsForMesh(mesh)
            if skinLightmapRendererActive() and asyncMeshes[mesh]:
                doll.skinLightmapRenderer.BindLightmapShader(mesh)

    def SetInteriorShader(self, asyncMeshes, mesh, wrinkleFx, doll):
        """
        Applies interior shaders to the given mesh
        """
        fx = pdCcf.GetEffectsFromMesh(mesh)
        tasklets = []
        for f in iter(fx):
            if type(f) == trinity.Tr2ShaderMaterial:
                continue
            t = uthread.new(self.SetInteriorShaderForFx_t, *(f,
             asyncMeshes,
             mesh,
             wrinkleFx,
             doll))
            tasklets.append(t)

        pdCf.WaitForAll(tasklets, lambda x: x.alive)

    def SetInteriorShaderForFx_t(self, effect, asyncMeshes, mesh, wrinkleFx, doll):
        path = effect.effectFilePath.lower()
        if 'masked.fx' in path:
            return
        if self.BindCustomShader(effect, doll.useFastShader, doll):
            return
        if asyncMeshes:
            asyncMeshes[mesh] = True
        suffix = '.fx'
        if doll.useFastShader and ('_fast.fx' in path or path in pdDef.SHADERS_THAT_CAN_SWITCH_TO_FAST_SHADER_MODE):
            suffix = '_fast.fx'
        if doll.useDXT5N and ('_dxt5n.fx' in path or path in pdDef.SHADERS_TO_ENABLE_DXT5N):
            suffix = '{0}_dxt5n.fx'.format(suffix[:-3])
        self.BindInteriorShader(effect, wrinkleFx, doll, suffix)

    def BindCustomShader(self, effect, useFastShaders, doll):
        """
        Check if the effect should not be affected by SetInteriorShader, and while we're at it,
        do anything special we need like binding cubemaps etc.
        """
        name = effect.name.lower()
        if name.startswith('c_custom') or name.startswith('c_s2'):
            pdPor.PortraitTools.BindCustomShaders(effect, useFastShaders, doll)
            return True
        return False

    def BindClothShaders(self, mesh, doll, isHair):
        """
        Look at all effects in a cloth mesh and crank up their quality if needed.
        """
        if doll.currentLOD <= 0:
            fx = pdCcf.GetEffectsFromMesh(mesh)
            for f in iter(fx):
                isHair = pdPor.PortraitTools.BindHeroHairShader(f, '.fx') or isHair
                if doll.currentLOD <= pdDef.LOD_SKIN:
                    pdPor.PortraitTools.BindHeroClothShader(f, doll.useDXT5N)

        return isHair

    def BindInteriorShader(self, effect, wrinkleFx, doll, suffix):
        """
        Look at the LOD, and attach the hero/skin/linear shaders that the asset may not have been exported with.
        
        wrinkleFx - contains all the effects that are part of the head.
        suffix    - which permutation of the shaders are we interested in (dxt5 and such)
        """
        path = effect.effectFilePath.lower()
        if pdDef.DOLL_PARTS.HAIR not in path:
            if doll.currentLOD >= 0:
                if 'skinnedavatarbrdf' not in path:
                    effect.effectFilePath = '{0}{1}'.format(pdDef.INTERIOR_AVATAR_EFFECT_FILE_PATH[:-3], suffix)
                    for r in effect.resources:
                        if r.name == 'FresnelLookupMap':
                            break
                    else:
                        res = trinity.TriTexture2DParameter()
                        res.name = 'FresnelLookupMap'
                        res.resourcePath = pdDef.FRESNEL_LOOKUP_MAP
                        effect.resources.append(res)

            elif doll.currentLOD == pdDef.LOD_A:
                pass
            elif doll.currentLOD in [pdDef.LOD_SKIN]:
                pdPor.PortraitTools.BindSkinShader(effect, wrinkleFx, scattering=False, buildDataManager=doll.buildDataManager, gender=doll.gender, use_png=pdDef.USE_PNG, fxSuffix=suffix)
                pdPor.PortraitTools.BindLinearAvatarBRDF(effect, suffix)
            elif doll.currentLOD == pdDef.LOD_SCATTER_SKIN:
                pdPor.PortraitTools.BindSkinShader(effect, wrinkleFx, scattering=True, buildDataManager=doll.buildDataManager, gender=doll.gender, use_png=pdDef.USE_PNG, fxSuffix=suffix)
                pdPor.PortraitTools.BindLinearAvatarBRDF(effect, suffix)
        elif doll.currentLOD <= 0:
            pdPor.PortraitTools.BindHeroHairShader(effect, suffix)

    def OnFinalizeAvatar(self, visualModel, avatar, updateRuleBundle, doll, factory):
        """
        Called when all meshes etc have been loaded, but async tasklets are still running.
        
        Now that we have a reference to all fx that are skin and need wrinkles, set up a curve
        binding that targets all of them in one go.
        """
        if updateRuleBundle.meshesChanged:
            if self.wrinkleFx:
                pdPor.PortraitTools().SetupWrinkleMapControls(avatar, self.wrinkleFx, doll)
            if doll.currentLOD == pdDef.LOD_SKIN:
                inst = pdPor.SkinSpotLightShadows.instance
                if inst:
                    inst.SetupSkinnedObject(avatar, createJobs=False)

    def OnEndUpdate(self, avatar, visualModel, doll, factory, **kwargs):
        """
        Called as the very last step in Update, everything is done, including child tasklets.
        """
        pass


class RenderDriverPLP(RenderDriver):
    """
    Driver that adds a PLP-conversion post process
    """
    __guid__ = 'paperDoll.renderDrivers.RenderDriverPLP'

    def __init__(self):
        RenderDriver.__init__(self)

    def OnEndUpdate(self, avatar, visualModel, doll, factory, **kwargs):
        if visualModel and avatar:
            hasMeshDirtyModifiers = any((x for x in doll.buildDataManager.GetModifiersAsList() if x.IsMeshDirty()))
            if hasMeshDirtyModifiers:
                paperDollPrePassFixup.AddPrepassAreasToAvatar(avatar, visualModel, doll, factory.clothSimulationActive, **kwargs)


class RenderDriverCollapsePLP(RenderDriver):
    __guid__ = 'paperDoll.renderDrivers.RenderDriverCollapsePLP'

    def __init__(self):
        RenderDriver.__init__(self)

    def OnBeginUpdate(self, doll):
        builder = trinity.Tr2SkinnedModelBuilder()
        builder.createGPUMesh = True
        builder.removeReversed = True
        builder.collapseToOpaque = True
        builder.enableSubsetBuilding = True
        builder.effectPath = COLLAPSED_MATERIAL_EFFECT_PATH
        builder.enableVertexChopping = False
        builder.enableVertexPadding = False
        builder.SetAdjustPathMethod(lambda x: x)
        self.builder = builder
        self.sources = {}

    def FindTransformUV(self, meshes):
        for mesh in meshes:
            for areas in (mesh.opaqueAreas, mesh.decalAreas, mesh.transparentAreas):
                for area in areas:
                    if hasattr(area, 'effect') and hasattr(area.effect, 'parameters'):
                        for p in area.effect.parameters:
                            if p.name == 'TransformUV0':
                                return p.value

        return (0, 0, 1, 1)

    def OnModifierUVChanged(self, modifier):
        source = self.sources.get(modifier, None)
        if source is None:
            return
        uv = self.FindTransformUV(modifier.meshes)
        source.upperLeftTexCoord = (uv[0], uv[1])
        source.lowerRightTexCoord = (uv[2], uv[3])

    def OnModifierRedfileLoaded(self, modifier, redfilePath):
        if not redfilePath or 'ragdoll' in redfilePath:
            return
        source = trinity.Tr2SkinnedModelBuilderSource()
        source.moduleResPath = redfilePath
        self.sources[modifier] = source

    def OnApplyMorphTargets(self, meshes, morphTargets):
        for name, weight in morphTargets.iteritems():
            if weight > 0.0:
                blend = trinity.Tr2SkinnedModelBuilderBlend()
                blend.name = name
                blend.power = weight
                self.builder.blendshapeInfo.append(blend)

    def OnEndUpdate(self, avatar, visualModel, doll, factory, **kwargs):

        def FindSkinEffect(meshes):
            for mesh in iter(meshes):
                fx = pdCcf.GetEffectsFromMesh(mesh)
                for effect in iter(fx):
                    if effect.name.lower().startswith('c_skin_'):
                        return effect

        def TransferArrayOf(destEffect, sourceEffect):
            for p in sourceEffect.parameters:
                if p.name.startswith('ArrayOf'):
                    for q in destEffect.parameters:
                        if p.name == q.name:
                            destEffect.parameters.remove(q)
                            break

                    destEffect.parameters.append(p)

        if avatar is None or visualModel is None:
            del self.sources
            del self.builder
            RenderDriver.OnEndUpdate(self, avatar, visualModel, doll, factory, **kwargs)
            return
        sourceEffect = FindSkinEffect(visualModel.meshes)
        collapsedEffect = None
        collapseShadowMesh = pdCfg.PerformanceOptions.collapseShadowMesh and doll.overrideLod >= 0 and doll.overrideLod <= 1
        collapseMainMesh = pdCfg.PerformanceOptions.collapseMainMesh and doll.overrideLod == 2
        collapsePLPMesh = pdCfg.PerformanceOptions.collapsePLPMesh and doll.overrideLod >= 0
        if collapseMainMesh:
            collapsePLPMesh = True
            collapseShadowMesh = False
        if sourceEffect:
            if collapseMainMesh:
                collapsedEffect = SkinLightmapRenderer.DuplicateEffect(sourceEffect, COLLAPSED_BASIC_EFFECT_PATH)
            elif collapseShadowMesh or collapsePLPMesh:
                collapsedEffect = SkinLightmapRenderer.DuplicateEffect(sourceEffect, COLLAPSED_SHADOW_EFFECT_PATH)
        if collapsedEffect is None:
            del self.sources
            del self.builder
            RenderDriver.OnEndUpdate(self, avatar, visualModel, doll, factory, **kwargs)
            return
        for param in collapsedEffect.parameters:
            if param.name == 'TransformUV0':
                param.value = (0, 0, 1, 1)
                break

        self.builder.collapseTransparentAreas = collapseMainMesh
        if not collapseMainMesh and COLLAPSE_USE_PD_VISUALMODEL:
            paperDollPrePassFixup.AddPrepassAreasToAvatar(avatar, visualModel, doll, factory.clothSimulationActive, **kwargs)
            self.builder.collapseFromDepthNormal = True
            self.builder.sourceSkinnedModel = visualModel
            for modifier, inSource in self.sources.iteritems():
                for mesh in modifier.meshes:
                    source = trinity.Tr2SkinnedModelBuilderSource()
                    source.upperLeftTexCoord = inSource.upperLeftTexCoord
                    source.lowerRightTexCoord = inSource.lowerRightTexCoord
                    source.visualModelMeshName = mesh.name
                    source.visualModelMeshGrannyPath = modifier.meshGeometryResPaths[mesh.name]
                    if source.visualModelMeshGrannyPath != '':
                        self.builder.sourceMeshesInfo.append(source)

        else:
            modifiers = self.sources.keys()
            modifiers = sorted(modifiers, key=lambda x: x.name)
            sources = map(self.sources.get, modifiers)
            for source in sources:
                self.builder.sourceMeshesInfo.append(source)

        self.builder.SetExtraArrayOf(['ArrayOfCutMaskInfluence',
         'ArrayOfMaterialLibraryID',
         'ArrayOfMaterial2LibraryID',
         'ArrayOfMaterialSpecularFactors'])
        if not self.builder.PrepareForBuild():
            log.LogWarn('PD Collapse: PrepareForBuild failed')
        else:
            buildCount = 0
            collapsedMeshes = {}
            while self.builder.Build():
                info = self.builder.GetCollapsedInfo()
                model = self.builder.GetSkinnedModel()
                if model is None:
                    break
                for mesh in model.meshes:
                    collapsedMeshes[mesh] = info

                model.meshes.removeAt(-1)
                buildCount += 1

            if buildCount == 0:
                collapseShadowMesh = False
                collapseMainMesh = False
                collapsePLPMesh = False
            if pdCfg.PerformanceOptions.collapseVerbose:
                if buildCount > 1 and doll.overrideLod == 2:
                    log.LogWarn('PD Collapse: lod2 has ' + str(buildCount) + ' meshes after collapse (expected 1).')
                if buildCount > 3 and doll.overrideLod == 0:
                    log.LogWarn('PD Collapse: lod0 has ' + str(buildCount) + ' meshes after collapse (expected 3 at most).')
            if buildCount > 0:
                if collapseMainMesh:
                    visualModel.meshes.removeAt(-1)
                elif collapsePLPMesh:
                    for mesh in visualModel.meshes:
                        mesh.depthAreas.removeAt(-1)
                        mesh.depthNormalAreas.removeAt(-1)

                for count, mesh in enumerate(collapsedMeshes.iterkeys()):
                    mesh.name = 'collapsed' + str(buildCount) + str(count)
                    for area in mesh.opaqueAreas:
                        TransferArrayOf(collapsedEffect, area.effect)
                        area.effect = collapsedEffect

                    def TransferArrayToTexture(cut, mat1, mat2, spec):
                        pixels = []

                        def GetFromArray(array, index, component = 0, default = 0):
                            if array is None or not hasattr(array, 'value') or index >= len(array.value):
                                return default
                            v = array.value[index]
                            if type(v) == trinity.TriVector4:
                                return v.data[component]
                            return v

                        OPT_CUTOUT = 8
                        OPT_DOUBLE_MATERIAL = 16
                        for x in xrange(32):
                            infoList = collapsedMeshes.get(mesh, [])
                            infoTuple = infoList[x] if x < len(infoList) else (0, 0, 0, 0)
                            permute = infoTuple[3]
                            table = paperDollPrePassFixup.MATERIAL_ID_TRANSPARENT_HACK_EXACT if infoTuple[1] == 2 else paperDollPrePassFixup.MATERIAL_ID_EXACT
                            r = int(0.5 + 100 * GetFromArray(cut, x))
                            if permute & OPT_CUTOUT:
                                r += 128
                            g = int(GetFromArray(mat1, x))
                            if permute & OPT_DOUBLE_MATERIAL:
                                b = int(GetFromArray(mat2, x))
                            else:
                                b = g
                            a = int(0.5 + 50 * GetFromArray(spec, x, component=2))
                            pixels.append((x, 0, (a << 24) + (r << 16) + (g << 8) + b))

                        hb = trinity.Tr2HostBitmap(32, 1, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
                        hb.SetPixels(0, pixels, 0)
                        lookup = trinity.TriTextureRes()
                        lookup.CreateFromHostBitmap(hb)
                        texParam = trinity.TriTexture2DParameter()
                        texParam.name = 'CollapsedMeshArrayLookup'
                        texParam.SetResource(lookup)
                        return texParam

                    if collapsePLPMesh:
                        paperDollPrePassFixup.AddDepthNormalAreasToStandardMesh(mesh)
                        for dn in mesh.depthNormalAreas:
                            parameters = dn.effect.parameters
                            dn.effect.defaultSituation = 'OPT_COLLAPSED_PLP DoubleMaterial'
                            cut = parameters.get('ArrayOfCutMaskInfluence', None)
                            mat1 = parameters.get('ArrayOfMaterialLibraryID', None)
                            mat2 = parameters.get('ArrayOfMaterial2LibraryID', None)
                            spec = parameters.get('ArrayOfMaterialSpecularFactors', None)
                            texParam = TransferArrayToTexture(cut, mat1, mat2, spec)
                            parameters['CollapsedMeshArrayLookup'] = texParam
                            for remove in ['CutMaskInfluence',
                             'MaterialLibraryID',
                             'Material2LibraryID',
                             'MaterialSpecularFactors',
                             'ArrayOfCutMaskInfluence',
                             'ArrayOfMaterialLibraryID',
                             'ArrayOfMaterial2LibraryID',
                             'ArrayOfMaterialSpecularFactors']:
                                if parameters.get(remove, None) is not None:
                                    del parameters[remove]

                    if collapseMainMesh:
                        for dn in mesh.opaqueAreas:
                            parameters = dn.effect.parameters
                            cut = pdCcf.FindParameterByName(dn.effect, 'ArrayOfCutMaskInfluence')
                            mat1 = pdCcf.FindParameterByName(dn.effect, 'ArrayOfMaterialLibraryID')
                            mat2 = pdCcf.FindParameterByName(dn.effect, 'ArrayOfMaterial2LibraryID')
                            spec = pdCcf.FindParameterByName(dn.effect, 'ArrayOfMaterialSpecularFactors')
                            texParam = TransferArrayToTexture(cut, mat1, mat2, spec)
                            dn.effect.parameters.append(texParam)
                            for remove in ['CutMaskInfluence',
                             'MaterialLibraryID',
                             'Material2LibraryID',
                             'MaterialSpecularFactors',
                             'ArrayOfCutMaskInfluence',
                             'ArrayOfMaterialLibraryID',
                             'ArrayOfMaterial2LibraryID',
                             'ArrayOfMaterialSpecularFactors']:
                                p = pdCcf.FindParameterByName(dn.effect, remove)
                                if p is not None:
                                    dn.effect.parameters.remove(p)

                    if collapseShadowMesh:
                        pdCcf.MoveAreas(mesh.opaqueAreas, mesh.depthAreas)
                        for d in mesh.depthAreas:
                            d.effect = SkinLightmapRenderer.DuplicateEffect(d.effect, COLLAPSED_SHADOW_EFFECT_PATH)
                            cut = pdCcf.FindParameterByName(d.effect, 'ArrayOfCutMaskInfluence')
                            texParam = TransferArrayToTexture(cut, None, None, None)
                            for r in d.effect.resources:
                                if r.name == 'CollapsedMeshArrayLookup':
                                    d.effect.resources.remove(r)
                                    break

                            d.effect.resources.append(texParam)

                    if not collapseMainMesh:
                        mesh.opaqueAreas.removeAt(-1)
                    visualModel.meshes.append(mesh)

        del self.sources
        del self.builder
        newArgs = {'collapseShadowMesh': collapseShadowMesh,
         'collapsePLPMesh': collapsePLPMesh,
         'collapseMainMesh': collapseMainMesh}
        kwargs.update(newArgs)
        if collapseMainMesh or not COLLAPSE_USE_PD_VISUALMODEL:
            paperDollPrePassFixup.AddPrepassAreasToAvatar(avatar, avatar.visualModel, doll, factory.clothSimulationActive, **kwargs)
        else:
            avatar.BindLowLevelShaders()
        return newArgs
