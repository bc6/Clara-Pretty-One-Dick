#Embedded file name: eve/client/script/paperDoll\paperDollImpl.py
import os
import sys
import remotefilecache
import trinity
import blue
import telemetry
import uthread
import log
import yaml
import TextureCompositor.TextureCompositor as tc
import RenderTargetManager.RenderTargetManager as rtm
import legacy_r_drive
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollDataManagement as pdDm
import eve.client.script.paperDoll.commonClientFunctions as pdCcf
import eve.common.script.paperDoll.paperDollCommonFunctions as pdCf
import eve.common.script.paperDoll.paperDollConfiguration as pdCfg
import paperDollPortrait as pdPor
from .projectedDecals import ProjectedDecal, DecalBaker
from .SkinSpotLightShadows import SkinSpotLightShadows
from .SkinLightmapRenderer import SkinLightmapRenderer
import renderDrivers
import paperDollStatistics as statistics
TC_MARKERS_ENABLED = False

def AddMarker(m):
    if TC_MARKERS_ENABLED:
        trinity.graphs.AddMarker('frameTime', m)


RTM = rtm.RenderTargetManager()
COMPRESS_DXT1 = trinity.TR2DXT_COMPRESS_SQUISH_DXT1
COMPRESS_DXT5 = trinity.TR2DXT_COMPRESS_SQUISH_DXT5
COMPRESS_DXT5n = trinity.TR2DXT_COMPRESS_RT_DXT5N

class UVCalculator(object):
    UVs = {pdDef.DOLL_PARTS.HEAD: pdDef.HEAD_UVS,
     pdDef.DOLL_PARTS.BODY: pdDef.BODY_UVS,
     pdDef.DOLL_PARTS.HAIR: pdDef.HAIR_UVS,
     pdDef.DOLL_PARTS.ACCESSORIES: pdDef.ACCE_UVS}

    @staticmethod
    def BoxCoversX(x, box):
        if x >= box[0] and x < box[2]:
            return True
        return False

    @staticmethod
    def GetHeightAt(x, returnUVs):
        height = 0
        newX = x
        for r in returnUVs:
            if UVCalculator.BoxCoversX(x, r):
                if r[3] > height:
                    height = r[3]
                    newX = r[2]

        return (height, newX)

    @staticmethod
    def BoxIntersects(x, y, box, uv):
        for vert in ((x, y),
         (x + box[0], y),
         (x, y + box[1]),
         (x + box[0], y + box[1])):
            if vert[0] > uv[0] and vert[0] < uv[2] and vert[1] > uv[1] and vert[1] < uv[3]:
                return True

        return False

    @staticmethod
    def BoxFits(x, y, box, target, returnUVs):
        if x < 0 or x + box[0] > target[0] or y < 0:
            return False
        for r in returnUVs:
            if UVCalculator.BoxIntersects(x, y, box, r):
                return False

        return True

    @staticmethod
    def PackTextures(textures, target):
        watermark = 0
        returnUVs = []
        xinc = 0.001953125
        for t in textures:
            candidates = {}
            minInc = 100000
            x = 0.0
            while x < 1.0:
                currentX = x
                h, x = UVCalculator.GetHeightAt(currentX, returnUVs)
                inc = h + t[1]
                if UVCalculator.BoxFits(currentX, h, t, target, returnUVs):
                    if inc < minInc:
                        minInc = inc
                        candidates[inc] = (currentX, h)
                if x == currentX:
                    x += xinc

            if candidates:
                final = candidates[minInc]
                returnUVs.append((final[0],
                 final[1],
                 final[0] + t[0],
                 final[1] + t[1]))
                watermark = final[1] + t[1]

        if watermark > target[1]:
            factor = target[1] / watermark
            for ix in xrange(len(returnUVs)):
                returnUVs[ix] = [returnUVs[ix][0] * factor,
                 returnUVs[ix][1] * factor,
                 returnUVs[ix][2] * factor,
                 returnUVs[ix][3] * factor]

        return returnUVs

    @staticmethod
    def GetMapSize(modifier):
        """
        Fallback code to query the accesorie texture size for UV calculation.
        This code is always hit when running from content, since the size files are only
        published from content to the branches.
        """
        tag = pdDef.ACCESSORIES_CATEGORIES.ACCESSORIES
        path = modifier.mapL.get(tag) or modifier.mapD.get(tag)
        if path:
            param = trinity.TriTexture2DParameter()
            param.resourcePath = path
            while param.resource.isLoading:
                pdCf.Yield()

            return (param.resource.width, param.resource.height)

    @staticmethod
    def CalculateAccessoryUVs(buildDataManager):
        accesorieModifiers = buildDataManager.GetModifiersByPart(pdDef.DOLL_PARTS.ACCESSORIES, showHidden=True)
        targetBox = (1.0, 1.0)
        textures = []
        for modifier in iter(accesorieModifiers):
            adjustedSize = (0.0, 0.0)
            amSize = modifier.accessoryMapSize or UVCalculator.GetMapSize(modifier)
            if amSize:
                adjustedSize = [amSize[0] / 512.0, amSize[1] / 512.0]
                if adjustedSize[0] > 0.5:
                    adjustedSize[0] = 0.5
                if adjustedSize[1] > 0.5:
                    adjustedSize[1] = 0.5
            textures.append(adjustedSize)

        result = UVCalculator.PackTextures(textures, targetBox)
        for ix in xrange(len(accesorieModifiers)):
            mod = accesorieModifiers[ix]
            mod.ulUVs = (result[ix][0], result[ix][1])
            mod.lrUVs = (result[ix][2], result[ix][3])

    @staticmethod
    def ApplyUVs(buildDataManager, renderDriver):
        """        
        Applies UVs by setting the TransformUV0 parameter on all the meshes kept in the dolls modifiers.
        """
        UVCalculator.CalculateAccessoryUVs(buildDataManager)
        defaultUVs = dict(UVCalculator.UVs)
        modifierGenerator = (modifier for modifier in buildDataManager.GetSortedModifiers() if modifier.weight > 0 and modifier.IsMeshContainingModifier())
        for modifier in modifierGenerator:
            meshes = list(modifier.meshes)
            if modifier.clothData:
                meshes.append(modifier.clothData)
            modifierUVCategory = buildDataManager.CategoryToPart(modifier.categorie)
            for mesh in iter(meshes):
                uvCategory = modifierUVCategory
                if uvCategory == pdDef.DOLL_PARTS.HAIR and hasattr(mesh, 'decalAreas') and mesh.decalAreas:
                    for area in mesh.decalAreas:
                        if 'stubble' in area.name.lower():
                            uvCategory = pdDef.DOLL_PARTS.HEAD
                            break

                if hasattr(mesh, 'opaqueAreas') and hasattr(mesh, 'decalAreas') and hasattr(mesh, 'transparentAreas'):
                    for area in tuple(mesh.opaqueAreas) + tuple(mesh.decalAreas) + tuple(mesh.transparentAreas):
                        for category in defaultUVs:
                            if category.lower() + 'uv' in area.name.lower():
                                uvCategory = category
                                break

                fxs = pdCcf.GetEffectsFromMesh(mesh)
                for fx in iter(fxs):
                    if type(fx) != trinity.Tr2ShaderMaterial and fx.effectResource and fx.effectResource.isLoading:
                        while fx.effectResource.isLoading:
                            pdCf.Yield()

                    transformUV0 = None
                    for effectParameter in iter(fx.parameters):
                        if effectParameter.name == 'TransformUV0':
                            transformUV0 = effectParameter
                            break

                    if not transformUV0:
                        transformUV0 = trinity.Tr2Vector4Parameter()
                        transformUV0.name = 'TransformUV0'
                        fx.parameters.append(transformUV0)
                    computedUVs = None
                    if uvCategory == pdDef.DOLL_PARTS.ACCESSORIES:
                        width = defaultUVs[uvCategory][2] - defaultUVs[uvCategory][0]
                        height = defaultUVs[uvCategory][3] - defaultUVs[uvCategory][1]
                        computedUVs = (defaultUVs[uvCategory][0] + modifier.ulUVs[0] * width,
                         defaultUVs[uvCategory][1] + modifier.ulUVs[1] * height,
                         defaultUVs[uvCategory][0] + modifier.lrUVs[0] * width,
                         defaultUVs[uvCategory][1] + modifier.lrUVs[1] * height)
                    elif type(mesh) is trinity.Tr2ClothingActor:
                        computedUVs = (defaultUVs[uvCategory][0],
                         defaultUVs[uvCategory][3],
                         defaultUVs[uvCategory][2],
                         defaultUVs[uvCategory][1])
                    else:
                        computedUVs = (defaultUVs[uvCategory][0],
                         defaultUVs[uvCategory][1],
                         defaultUVs[uvCategory][2],
                         defaultUVs[uvCategory][3])
                    transformUV0.value = computedUVs

            renderDriver.OnModifierUVChanged(modifier)


class UpdateRuleBundle(object):
    """
    An instance of this class is created for each execution of the Update tasklet.
    It records state and rule changes based on the set of operations that Update takes
    that are needed at a later point during the tasklets execution.
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.UpdateRuleBundle'

    def __init__(self):
        self.forcesLooseTop = False
        self.hidesBootShin = False
        self.swapTops = False
        self.swapBottom = False
        self.swapSocks = False
        self.undoMaskedShaders = False
        self.rebuildHair = False
        self.mapsToComposite = list(pdDef.MAPS)
        self.blendShapesOnly = False
        self.decalsOnly = False
        self.doDecals = False
        self.doBlendShapes = False
        self.doStubble = False
        self.meshesChanged = False
        self.partsToComposite = []
        self.dirtyDecalModifiers = []
        self.videoMemoryFailure = False

    def __str__(self):
        s = '{0}\n'.format(id(self))
        for key, value in self.__dict__.iteritems():
            s += '\t{0} := {1}\n'.format(key, value)

        return s

    def DiscoverState(self, dirtyModifiers, avatar):
        """
        Discovers the partial state of this UpdateRule instance based on dity modifiers
        """
        allModifiersBlendShapes = False
        someModifiersBlendShapes = False
        allModifiersDecals = False
        someModifiersDecals = False
        for modifier in iter(dirtyModifiers):
            isBlendShapeModifier = modifier.IsBlendshapeModifier()
            isDecalModifier = not isBlendShapeModifier and modifier.decalData is not None and (modifier.IsDirty or not modifier.IsTextureContainingModifier())
            if modifier.stubblePath:
                self.doStubble = True
            if isDecalModifier:
                self.dirtyDecalModifiers.append(modifier)
            someModifiersBlendShapes = isBlendShapeModifier or someModifiersBlendShapes
            allModifiersBlendShapes = isBlendShapeModifier and allModifiersBlendShapes
            someModifiersDecals = isDecalModifier or someModifiersDecals
            allModifiersDecals = isDecalModifier and allModifiersDecals

        self.blendShapesOnly = allModifiersBlendShapes
        self.decalsOnly = allModifiersDecals and avatar is not None
        self.doBlendShapes = someModifiersBlendShapes
        self.doDecals = someModifiersDecals and avatar is not None


class MapBundle(object):
    """
    Contains the 4 maps used by a Doll, they start out as none.
    Each member can become a texture or a rendertarget (texture used as rendertarget)
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.MapBundle'

    def __init__(self):
        self.diffuseMap = None
        self.specularMap = None
        self.normalMap = None
        self.maskMap = None
        self.baseResolution = None
        self.hashKeys = {}
        self.mapResolutions = {pdDef.MASK_MAP: pdCfg.PerformanceOptions.maskMapTextureSize}
        self.mapResolutionFactors = {}
        self.SetBaseResolution(2048, 1024)

    def __getitem__(self, idx):
        if idx == pdDef.DIFFUSE_MAP:
            return self.diffuseMap
        if idx == pdDef.SPECULAR_MAP:
            return self.specularMap
        if idx == pdDef.NORMAL_MAP:
            return self.normalMap
        if idx == pdDef.MASK_MAP:
            return self.maskMap
        raise AttributeError()

    def SetBaseResolution(self, width, height):
        """
        Sets the base resolution for all maps and calculates the default map specific resolution
        using the last defined factors, defaulting to 1 if none exist
        """
        self.baseResolution = (width, height)
        for mapType in pdDef.RESIZABLE_MAPS:
            factor = self.mapResolutionFactors.get(mapType, pdCfg.PerformanceOptions.textureSizeFactors[mapType])
            self.SetMapTypeResolutionFactor(mapType, factor)

    def SetMapByTypeIndex(self, idx, mapToSet, hashKey = None):
        """
        Given the mapType index in 'idx' sets that map on this instance to 'mapToSet' and records the 
        hashkey value in this instance using 'hashKey' if its given
        """
        if idx == pdDef.DIFFUSE_MAP:
            self.diffuseMap = mapToSet
        elif idx == pdDef.SPECULAR_MAP:
            self.specularMap = mapToSet
        elif idx == pdDef.NORMAL_MAP:
            self.normalMap = mapToSet
        elif idx == pdDef.MASK_MAP:
            self.maskMap = mapToSet
        else:
            raise ValueError('paperDoll::MapBundle::SetMapByTypeIndex - Index provided is not defined or supported. It must be defined in paperDoll.MAPS')
        if hashKey:
            self.hashKeys[idx] = hashKey

    def GetResolutionByMapType(self, mapType):
        """
        Returns the resolution of the map that is keyed to the given 'mapType'
        """
        return self.mapResolutions.get(mapType, self.baseResolution)

    def SetMapTypeResolutionFactor(self, mapType, factor):
        """
        Sets the resolution factor for the given 'mapType' and calcuates the resolution for that map 
        as a function of baseResolution>>(factor-1)
        """
        oldFactor = self.mapResolutionFactors.get(mapType, 1)
        self.mapResolutionFactors[mapType] = factor
        shift = factor - 1
        newResolution = (self.baseResolution[0] >> shift, self.baseResolution[1] >> shift)
        if newResolution[0] < 16:
            self.mapResolutionFactors[mapType] = oldFactor
            return
        oldResolution = self.mapResolutions.get(mapType, self.baseResolution)
        self.mapResolutions[mapType] = newResolution

    def AllMapsGood(self):
        """
        Returns True iff all maps are good according to Blue resource manager
        """
        for each in iter(self):
            if not each or not each.isGood:
                return False

        return True

    def __iter__(self):
        """
        Custom iterator to itrate over all 4 maps belonging to this mapBundle
        """
        yield self.diffuseMap
        yield self.specularMap
        yield self.normalMap
        yield self.maskMap

    def ReCreate(self, includeFixedSizeMaps = True):
        """
        Releases all resources and resets hashKeys to initial empty state.
        Does not change resolution settings.
        """
        del self.diffuseMap
        del self.specularMap
        del self.normalMap
        if includeFixedSizeMaps:
            del self.maskMap
        self.diffuseMap = None
        self.specularMap = None
        self.normalMap = None
        if includeFixedSizeMaps:
            self.maskMap = None
        for key in list(self.hashKeys.iterkeys()):
            if not self[key]:
                del self.hashKeys[key]

    def __repr__(self):
        s = 'Base resolution: w{}\th{}'.format(self.baseResolution[0], self.baseResolution[1])
        for mapType in pdDef.MAPS:
            if self[mapType]:
                cMap = self[mapType]
                s = '{}\n{}\tw{}\th{}'.format(s, pdDef.MAPNAMES[mapType], cMap.width, cMap.height)

        return s

    def __del__(self):
        del self.diffuseMap
        del self.specularMap
        del self.normalMap
        del self.maskMap


class CompressionSettings():
    """
    This class provides compression settings configuration and is inherited by the factory and is an
    attribute of the doll
    """
    __guid__ = 'paperDoll.CompressionSettings'

    @telemetry.ZONE_METHOD
    def __init__(self, compressTextures = True, generateMipmap = False, qualityLevel = None):
        """
        Instances of this class are used to control how textures are compressed on dolls.
        There is a default instance set on the factory that is used in general when compositing dolls and that setting can be
        overwritten per doll level by setting a compression settings instance on the doll.
        'compressTextures'  If False, disables texture compression
        'generateMipmap'    If True, allows mipmaps to be generated for composited textures
        'qualityLevel'      Defaults to trinity.TR2DXT_COMPRESS_SQ_RANGE_FIT, see documentation for trinity.device.CompressSurfaceWithQuality
        """
        self.compressTextures = compressTextures
        self.generateMipmap = generateMipmap
        self.qualityLevel = qualityLevel or trinity.TR2DXT_COMPRESS_SQ_RANGE_FIT
        self.compressNormalMap = True
        self.compressSpecularMap = True
        self.compressDiffuseMap = True
        self.compressMaskMap = True

    @telemetry.ZONE_METHOD
    def __repr__(self):
        return '%i%i%i%i%i%i' % (self.compressTextures,
         self.compressNormalMap,
         self.compressSpecularMap,
         self.compressDiffuseMap,
         self.compressMaskMap,
         self.generateMipmap)

    @telemetry.ZONE_METHOD
    def SetMapCompression(self, compressNormalMap = True, compressSpecularMap = True, compressDiffuseMap = True, compressMaskMap = True):
        """
        SetMapCompression
            bool compressNormalMap=True, 
            bool compressSpecularMap=True, 
            bool compressDiffuseMap=True,
            bool compressMaskMap=True
                
        Sets which maps are to be compressed when self.compressTextures is set to True.
        """
        self.compressNormalMap = compressNormalMap
        self.compressSpecularMap = compressSpecularMap
        self.compressDiffuseMap = compressDiffuseMap
        self.compressMaskMap = compressMaskMap

    @telemetry.ZONE_METHOD
    def AllowCompress(self, textureType):
        """
        Helper function that maps the integer defined map types to the more readable
        class-instance level boolean names used to define map-specific compression.
        """
        if textureType == pdDef.DIFFUSE_MAP:
            return self.compressDiffuseMap
        if textureType == pdDef.SPECULAR_MAP:
            return self.compressSpecularMap
        if textureType == pdDef.NORMAL_MAP:
            return self.compressNormalMap
        if textureType == pdDef.MASK_MAP:
            return self.compressMaskMap


class Factory(object, CompressionSettings, pdDm.ModifierLoader):
    """
    There should be only one factory at runtime.
    Factory processes the data to load modifiers from res and caches that data.
    Modifier data is controlled by the options file that is loaded.
    It handles various compositing and mesh operational tasks.
    """
    __guid__ = 'paperDoll.Factory'
    shaderPreload = None
    texturePreload = None

    def setclothSimulationActive(self, value):
        value = value and not blue.win32.IsTransgaming()
        if value:
            import GameWorld
            trinity.InitializeApex(GameWorld.GWPhysXWrapper())
        self._clothSimulationActive = value
        pdDm.ModifierLoader.setclothSimulationActive(self, value)

    clothSimulationActive = property(fget=lambda self: self._clothSimulationActive, fset=lambda self, value: self.setclothSimulationActive(value))

    @telemetry.ZONE_METHOD
    def __init__(self, gender = None):
        object.__init__(self)
        CompressionSettings.__init__(self, compressTextures=False)
        pdDm.ModifierLoader.__init__(self)
        if gender:
            log.LogWarn('PaperDoll: Deprication warning, Gender is no longer a property of the Factory.')
        self.allowTextureCache = False
        self.verbose = False
        self.skipCompositing = False
        self.preloadedResources = list()
        self.calculatedSubrects = dict()
        self.CalculateSubrects()
        self.PreloadedGenericHeadModifiers = {pdDef.GENDER.MALE: None,
         pdDef.GENDER.FEMALE: None}
        self.PreloadShaders()
        uthread.new(self.PreloadGenericHeadsOnceLoaded_t)
        if pdCfg.PerformanceOptions.preloadNudeAssets:
            uthread.new(self.PreloadNudeResources_t)

    def CalculateSubrects(self):
        """
        Calculate subrects that are always going to be the same as a function of bodypart, widht and height.
        This data is used heavily when compositing.        
        """
        for i in range(3, 13):
            width = 2 ** i
            height = 2 ** (i - 1)
            self.calculatedSubrects[pdDef.DOLL_PARTS.HEAD, width] = self.CalcSubRect(pdDef.HEAD_UVS, width, height)
            self.calculatedSubrects[pdDef.DOLL_PARTS.HAIR, width] = self.CalcSubRect(pdDef.HAIR_UVS, width, height)
            self.calculatedSubrects[pdDef.DOLL_PARTS.BODY, width] = self.CalcSubRect(pdDef.BODY_UVS, width, height)

    def GetSubRect(self, bodypart, w, h, modifier = None, uvs = None):
        """
        Retrieves a pre-calcuated subrectangle given bodypart, width and height.
        If nothing is found, will fall back to calculating that subrectangle based on the
        modifier or UV if either are supplied.
        """
        key = (bodypart, w)
        subrect = self.calculatedSubrects.get(key)
        if subrect is None:
            if not uvs and modifier:
                uvs = modifier.GetUVsForCompositing(bodypart)
            if uvs:
                subrect = self.CalcSubRect(uvs, w, h)
        return subrect

    @telemetry.ZONE_METHOD
    def CalcSubRect(self, inputUV, w, h):
        """
        Calculates a rectangle in cartesian coordinates as a function of UV, width and height.        
        'inputUV' must be a 4 component iteratable of values [0.0, 1.0]
        Returns a tuple of 4 integers, where no value is less than 0.        
        """
        return (int(w * inputUV[0]),
         int(h * inputUV[1]),
         int(w * inputUV[2]),
         int(h * inputUV[3]))

    def PreloadNudeResources_t(self):
        """
        Preloads and stores in memory all resources that are used to create a nude doll.
        These are the most common resources between all possible dolls and hence benifit from being
        stored with hard references.
        """
        while not self.IsLoaded:
            pdCf.Yield()

        for genderData in self.resData.genderData.itervalues():
            for respath in pdDef.DEFAULT_NUDE_PARTS:
                entry = genderData.GetPathsToEntries()[respath]
                filenames = entry.files
                for filename in filenames:
                    if '_4k' in filename:
                        continue
                    if 'wrinkle' in filename or filename.startswith('skinmap'):
                        continue
                    if filename.endswith('.png'):
                        ddsTest = filename[:-4] + '.dds'
                        if ddsTest in filenames:
                            continue
                    resourcePath = entry.GetFullResPath(filename)
                    resource = blue.resMan.GetResource(resourcePath)
                    if resource and resource not in self.preloadedResources:
                        self.preloadedResources.append(resource)

    def PreloadGenericHeadsOnceLoaded_t(self):
        while not self.IsLoaded:
            pdCf.Yield()

        self.PreloadedGenericHeadModifiers[pdDef.GENDER.MALE] = self.CollectBuildData(pdDef.GENDER.MALE, 'head/head_generic')
        self.PreloadedGenericHeadModifiers[pdDef.GENDER.FEMALE] = self.CollectBuildData(pdDef.GENDER.FEMALE, 'head/head_generic')

    @staticmethod
    @telemetry.ZONE_FUNCTION
    def PreloadShaders():
        if Factory.shaderPreload is not None:
            return
        Factory.shaderPreload = []
        for path in pdDef.EFFECT_PRELOAD_PATHS:
            effect = trinity.Tr2Effect()
            effect.effectFilePath = 'res:/graphics/effect/managed/interior/avatar/{0}'.format(path)
            Factory.shaderPreload.append(effect)

        for path in tc.COMPOSITE_SHADER_PATHS:
            effect = trinity.Tr2Effect()
            effect.effectFilePath = '{0}/{1}'.format(tc.EFFECT_LOCATION, path)
            Factory.shaderPreload.append(effect)

        Factory.texturePreload = []
        for path in pdDef.TEXTURE_PRELOAD_PATHS:
            texture = trinity.TriTexture2DParameter()
            texture.resourcePath = path
            Factory.texturePreload.append(texture)

    @staticmethod
    @telemetry.ZONE_FUNCTION
    def ApplyMorphTargetsToMeshes(meshes, morphTargets, blendShapeMeshCache = None, meshGeometryResPaths = None):
        """
        Applies blendshapes to meshes which morphs the character.
        """
        blendShapeMeshCache = blendShapeMeshCache if blendShapeMeshCache is not None else {}
        loadingGrannyResources = {}
        meshGenerator = (mesh for mesh in meshes if not (blendShapeMeshCache.get(mesh.name) and blendShapeMeshCache.get(mesh.name)[1].isGood))
        for mesh in meshGenerator:
            index = mesh.meshIndex
            path = mesh.geometryResPath
            if not path and meshGeometryResPaths is not None:
                path = meshGeometryResPaths.get(mesh.name, None)
                if not path and mesh.name[-1].isdigit():
                    for meshName in meshGeometryResPaths:
                        if meshName.startswith(mesh.name[:-1]):
                            path = meshGeometryResPaths.get(meshName, None)
                            break

                    if not path and mesh.name[-2].isdigit:
                        for meshName in meshGeometryResPaths:
                            if meshName.startswith(mesh.name[:-2]):
                                path = meshGeometryResPaths.get(meshName, None)
                                break

            if not path:
                continue
            gr2 = path
            grannyResource = blue.resMan.GetResource(gr2, 'raw')
            loadingGrannyResources[mesh.name] = grannyResource

        doYield = True
        while doYield:
            doYield = False
            for lgr in loadingGrannyResources.itervalues():
                if lgr.isLoading:
                    doYield = True
                    break

            if doYield:
                pdCf.Yield(frameNice=False)

        if loadingGrannyResources:
            meshCount = len(meshes)
            for mIdx in xrange(meshCount):
                mesh = meshes[mIdx]
                grannyResource = loadingGrannyResources.get(mesh.name)
                index = mesh.meshIndex
                if grannyResource and grannyResource.isGood and grannyResource.meshCount > index:
                    geometryRes = grannyResource.CreateGeometryRes()
                    geometryRes.name = 'PaperDoll: {0} morphed'.format(mesh.name)
                    morphNames = grannyResource.GetAllMeshMorphNamesNoDigits(index)
                    blendShapeMeshCache[mesh.name] = (grannyResource, geometryRes, morphNames)
                elif loadingGrannyResources.get(mesh.name):
                    del loadingGrannyResources[mesh.name]

        meshGenerator = (mesh for mesh in meshes if blendShapeMeshCache.get(mesh.name))
        for mesh in meshGenerator:
            grannyResource, geometryRes, morphNames = blendShapeMeshCache[mesh.name]
            weights = [ morphTargets.get(name, 0.0) for name in morphNames ]
            isValid = False
            if len(weights) > 0:
                try:
                    grannyResource.BakeBlendshape(mesh.meshIndex, weights, geometryRes)
                    isValid = True
                except RuntimeError:
                    pass

                if isValid:
                    if mesh.geometry != geometryRes:
                        mesh.SetGeometryRes(geometryRes)
            if not isValid:
                del blendShapeMeshCache[mesh.name]

    @staticmethod
    @telemetry.ZONE_FUNCTION
    def ProcessBlendshapesForCloth(clothMeshes, morphTargets, clothMorphValues):
        clothMorphValues = clothMorphValues if clothMorphValues is not None else {}
        for clothActor in clothMeshes:
            if clothActor.morphRes is None:
                clothActor.morphRes = blue.resMan.GetResource(clothActor.resPath.lower().replace('.apb', '_bs.gr2'), 'raw')

        pdCf.WaitForAll(clothMeshes, lambda x: x.morphRes.isLoading)
        for clothActor in clothMeshes:
            if clothActor.morphRes.meshCount > 0:
                count = clothActor.morphRes.GetMeshMorphCount(clothActor.morphResMeshIndex)
                morphNames = []
                for i in xrange(count):
                    name = clothActor.morphRes.GetMeshMorphName(clothActor.morphResMeshIndex, i)
                    morphNames.append(pdCcf.StripDigits(name))

                weights = [ morphTargets.get(name, 0.0) for name in morphNames ]
                key = str(clothActor)
                if key not in clothMorphValues or weights != clothMorphValues[key]:
                    clothMorphValues[key] = weights
                    clothActor.SetMorphResWeights(weights)

    @staticmethod
    @telemetry.ZONE_FUNCTION
    def BindMapsToMeshes(meshes, mapBundle, prepass = False):
        """
        Binds composited maps in the mapBundle to the meshes and applies global maps.
        meshes      - a list of Tr2Mesh objects
        normal      - the normal map
        specular    - the specular map
        diffuse     - the diffuse map
        mask        - the mask map            
        """
        colorNdotLLookupMap = 'ColorNdotLLookupMap'
        fresnelLookupMap = 'FresnelLookupMap'
        ndotLLibrary = 'res:/Texture/Global/NdotLLibrary.png'
        for mesh in iter(meshes):
            effects = pdCcf.GetEffectsFromMesh(mesh, allowShaderMaterial=prepass, includePLP=prepass)
            for fx in (effect for effect in effects if effect is not None):
                if type(fx) != trinity.Tr2ShaderMaterial:
                    for r in iter(fx.resources):
                        if mapBundle.diffuseMap and r.name == pdDef.MAPNAMES[pdDef.DIFFUSE_MAP]:
                            Factory.SetResourceTexture(r, mapBundle.diffuseMap)
                        elif mapBundle.specularMap and r.name == pdDef.MAPNAMES[pdDef.SPECULAR_MAP]:
                            Factory.SetResourceTexture(r, mapBundle.specularMap)
                        elif mapBundle.normalMap and r.name == pdDef.MAPNAMES[pdDef.NORMAL_MAP]:
                            Factory.SetResourceTexture(r, mapBundle.normalMap)
                        elif mapBundle.maskMap and r.name == pdDef.MAPNAMES[pdDef.MASK_MAP]:
                            Factory.SetResourceTexture(r, mapBundle.maskMap)

                elif type(fx) == trinity.Tr2ShaderMaterial:
                    if mapBundle.diffuseMap and pdDef.MAPNAMES[pdDef.DIFFUSE_MAP] in fx.parameters:
                        fx.parameters[pdDef.MAPNAMES[pdDef.DIFFUSE_MAP]].SetResource(mapBundle.diffuseMap)
                    if mapBundle.specularMap and pdDef.MAPNAMES[pdDef.SPECULAR_MAP] in fx.parameters:
                        fx.parameters[pdDef.MAPNAMES[pdDef.SPECULAR_MAP]].SetResource(mapBundle.specularMap)
                    if mapBundle.normalMap and pdDef.MAPNAMES[pdDef.NORMAL_MAP] in fx.parameters:
                        fx.parameters[pdDef.MAPNAMES[pdDef.NORMAL_MAP]].SetResource(mapBundle.normalMap)
                    if mapBundle.maskMap and pdDef.MAPNAMES[pdDef.MASK_MAP] in fx.parameters:
                        fx.parameters[pdDef.MAPNAMES[pdDef.MASK_MAP]].SetResource(mapBundle.maskMap)
                    fx.RebuildCachedDataInternal()
                ndotLres = None
                fresnelLookupMapRes = None
                if type(fx) != trinity.Tr2ShaderMaterial:
                    for r in iter(fx.resources):
                        if r.name == colorNdotLLookupMap:
                            ndotLres = r
                        elif r.name == fresnelLookupMap:
                            fresnelLookupMapRes = r

                if ndotLres is None:
                    res = trinity.TriTexture2DParameter()
                    res.name = colorNdotLLookupMap
                    res.resourcePath = ndotLLibrary
                    if type(fx) == trinity.Tr2ShaderMaterial:
                        fx.parameters[res.name] = res
                    else:
                        fx.resources.append(res)
                else:
                    ndotLres.resourcePath = ndotLLibrary
                if fresnelLookupMapRes is None:
                    res = trinity.TriTexture2DParameter()
                    res.name = fresnelLookupMap
                    res.resourcePath = pdDef.FRESNEL_LOOKUP_MAP
                    if type(fx) == trinity.Tr2ShaderMaterial:
                        fx.parameters[res.name] = res
                    else:
                        fx.resources.append(res)
                else:
                    fresnelLookupMapRes.resourcePath = pdDef.FRESNEL_LOOKUP_MAP

    @telemetry.ZONE_METHOD
    def ClearAllCachedMaps(self):
        """
        Clears out the entire cache of maps saved using SaveMaps
        """
        cachePath = self.GetMapCachePath()
        fileSystemPath = blue.paths.ResolvePath(cachePath)
        for root, dirs, files in os.walk(fileSystemPath):
            for f in iter(files):
                os.remove(os.path.join(root, f))

    def GetMapCachePath(self):
        avatarCachePath = u''
        try:
            userCacheFolder = blue.paths.ResolvePath(u'cache:')
            avatarCachePath = u'{0}/{1}'.format(userCacheFolder, u'Avatars/cachedMaps')
        except Exception:
            avatarCachePath = u''
            sys.exc_clear()

        return avatarCachePath

    @telemetry.ZONE_METHOD
    def FindCachedTexture(self, hashKey, textureWidth, mapType):
        """        
        Searches the user's cache for a pre-existing texture.        
        'hashKey' is the hash of a doll's modifiers
        'textureWidth' is the width of the texture
        'mapType' is defined in MAPS
        Returns a texture instance or None if nothing is found.
        """
        cachePath = self.GetMapCachePath()
        try:
            if cachePath:
                filePath = self.GetCacheFilePath(cachePath, hashKey, textureWidth, mapType)
                if filePath:
                    if blue.paths.exists(filePath):
                        rotPath = blue.paths.ResolvePathToRoot('res', filePath)
                        os.utime(filePath, None)
                        cachedTexture = blue.resMan.GetResourceW(rotPath)
                        return cachedTexture
        except Exception:
            sys.exc_clear()

    @telemetry.ZONE_METHOD
    def SaveMaps(self, hashKey, maps):
        """
        'hashKey' is the unique hash of a given paperdoll builddata list        
        'textureWidth' is the width of the texture
        'maps' is a list of textures.
        Saves the maps out to the users cache folder.
        """
        cachePath = self.GetMapCachePath()
        if not cachePath:
            return
        try:
            for i, each in enumerate(maps):
                if each is not None:
                    textureWidth = each.width
                    filePath = self.GetCacheFilePath(cachePath, hashKey, textureWidth, i)
                    if filePath:
                        folder = os.path.split(filePath)[0]
                        try:
                            if not os.path.exists(folder):
                                os.makedirs(folder)
                            each.SaveAsync(filePath)
                            each.WaitForSave()
                        except OSError:
                            pass

        except Exception:
            sys.exc_clear()

    @telemetry.ZONE_METHOD
    def _CreateBiped(self, avatar, geometryRes, name = 'FactoryCreated'):
        biped = trinity.Tr2SkinnedModel()
        biped.skinScale = (1.0, 1.0, 1.0)
        biped.name = name
        if geometryRes:
            biped.geometryResPath = geometryRes
        biped.skeletonName = 'Root'
        avatar.visualModel = biped
        avatar.scaling = (1.0, 1.0, 1.0)
        return avatar

    @telemetry.ZONE_METHOD
    def CreateVisualModel(self, gender = pdDef.GENDER.FEMALE, geometryRes = None):
        biped = trinity.Tr2SkinnedModel()
        if not geometryRes:
            if gender == pdDef.GENDER.FEMALE:
                geometryRes = pdCcf.INTERIOR_FEMALE_GEOMETRY_RESPATH
            else:
                geometryRes = pdCcf.INTERIOR_MALE_GEOMETRY_RESPATH
        biped.geometryResPath = geometryRes
        biped.name = gender
        biped.skeletonName = 'Root'
        return biped

    @telemetry.ZONE_METHOD
    def CreateAvatar(self, geometryRes, name = 'FactoryCreated'):
        avatar = trinity.WodExtSkinnedObject()
        avatar = self._CreateBiped(avatar, geometryRes, name)
        return avatar

    @telemetry.ZONE_METHOD
    def CreateInteriorAvatar(self, geometryRes, name = 'FactoryCreated'):
        avatar = trinity.Tr2IntSkinnedObject()
        avatar = self._CreateBiped(avatar, geometryRes, name)
        return avatar

    @telemetry.ZONE_METHOD
    def RemoveAvatarFromScene(self, avatar, scene):
        """
        Removes 'avatar' from 'scene'.        
        """
        if avatar is None or scene is None:
            return
        try:
            scene.RemoveDynamic(avatar)
        except AttributeError:
            scene.Avatar = None
            sys.exc_clear()

    @telemetry.ZONE_METHOD
    def AddAvatarToScene(self, avatar, scene = None):
        """
        Adds the given avatar to a scene. 
        The scene defaults to the current scene on the device if it is not passed.
        """
        if avatar is None:
            raise AttributeError('No avatar passed to Factory::AddAvatarToScene')
        if scene is not None:
            if hasattr(scene, 'Avatar'):
                scene.Avatar = avatar
                return
            scene.AddDynamic(avatar)
            return
        dev = trinity.device
        if dev.scene:
            dev.scene.AddDynamic(avatar)
        else:
            dev.scene = trinity.Tr2InteriorScene()
            dev.scene.AddDynamic(avatar)

    @telemetry.ZONE_METHOD
    def CreateGWAnimation(self, avatar, morphemeNetwork):
        import GameWorld
        remotefilecache.prefetch_folder(os.path.dirname(morphemeNetwork))
        animation = GameWorld.GWAnimation(morphemeNetwork)
        avatar.animationUpdater = animation
        return animation

    def RebindAnimations(self, avatar, visualModel):
        """
        Rebinds animations on either the avatar or the visualModel
        Does nothing of both are passed in as None
        """
        if avatar:
            avatar.ResetAnimationBindings()
        elif visualModel:
            visualModel.ResetAnimationBindings()

    @telemetry.ZONE_METHOD
    def CreateAnimationOffsets(self, avatar, doll):
        if doll.boneOffsets:
            setOffset = None
            if avatar.animationUpdater and getattr(avatar.animationUpdater, 'network', None):
                setOffset = avatar.animationUpdater.network.boneOffset.SetOffset
            elif avatar.animationUpdater and getattr(avatar.animationUpdater, 'boneOffset', None):
                setOffset = avatar.animationUpdater.boneOffset.SetOffset
            if setOffset:
                for bone in doll.boneOffsets.iterkeys():
                    trans = doll.boneOffsets[bone][pdCcf.TRANSLATION]
                    setOffset(bone, *trans)

    @telemetry.ZONE_METHOD
    def CompositeStepsFunction(self, buildDataManager, gender, mapType, partsToComposite, comp, w, h, lod = None):
        genericHeadMod = self.PreloadedGenericHeadModifiers.get(gender)
        modifierList = [ modifier for modifier in buildDataManager.GetSortedModifiers() if modifier.IsTextureContainingModifier() and modifier.weight > 0 and modifier.categorie != pdDef.HEAD_CATEGORIES.HEAD ]
        if mapType == pdDef.DIFFUSE_MAP:
            genTex = genericHeadMod.mapD
        elif mapType == pdDef.SPECULAR_MAP:
            genTex = genericHeadMod.mapSRG
        elif mapType == pdDef.NORMAL_MAP:
            genTex = genericHeadMod.mapN
        elif mapType == pdDef.MASK_MAP:
            genTex = genericHeadMod.mapMask
        isNormalMap = mapType == pdDef.NORMAL_MAP
        if not partsToComposite or pdDef.DOLL_PARTS.BODY in partsToComposite:
            pdCf.BeFrameNice()
            baseBodyTexture = genTex.get(pdDef.DOLL_PARTS.BODY, '')
            if baseBodyTexture:
                comp.CopyBlitTexture(baseBodyTexture, self.GetSubRect(pdDef.DOLL_PARTS.BODY, w, h), isNormalMap=isNormalMap, alphaMultiplier=0.0 if isNormalMap else 1.0)
            self._CompositeTexture(modifierList, pdDef.DOLL_PARTS.BODY, comp, mapType, w, h, addAlpha=True, lod=lod)
        if not partsToComposite or pdDef.DOLL_PARTS.HEAD in partsToComposite or pdDef.DOLL_PARTS.HAIR in partsToComposite:
            pdCf.BeFrameNice()
            baseHeadTexture = genTex.get(pdDef.DOLL_PARTS.HEAD, '')
            if baseHeadTexture:
                comp.CopyBlitTexture(baseHeadTexture, self.GetSubRect(pdDef.DOLL_PARTS.HEAD, w, h), isNormalMap=isNormalMap, alphaMultiplier=0.0 if isNormalMap else 1.0)
            self._CompositeTexture(modifierList, pdDef.DOLL_PARTS.HEAD, comp, mapType, w, h, addAlpha=False, lod=lod)
        if not partsToComposite or pdDef.DOLL_PARTS.HAIR in partsToComposite:
            pdCf.BeFrameNice()
            self._CompositeTexture(modifierList, pdDef.DOLL_PARTS.HAIR, comp, mapType, w, h, addAlpha=False, lod=lod)
        if not partsToComposite or pdDef.DOLL_PARTS.ACCESSORIES in partsToComposite:
            pdCf.BeFrameNice()
            self._CompositeTexture(modifierList, pdDef.DOLL_PARTS.ACCESSORIES, comp, mapType, w, h, addAlpha=False, lod=lod)

    @telemetry.ZONE_METHOD
    def CompositeCombinedTexture(self, mapType, gender, buildDataManager, mapBundle, textureCompositor, compressionSettings = None, partsToComposite = None, copyToExistingTexture = False, lod = None):
        """
        Composites a texture of the given 'mapType' using the modifiers in the buildDataManager.
        The texture is put onto the 'mapBundle' provided.
        """
        renderTarget = None
        try:
            if compressionSettings is None:
                compressionSettings = self
            w, h = mapBundle.GetResolutionByMapType(mapType)
            textureFormat = trinity.PIXEL_FORMAT.B8G8R8A8_UNORM
            renderTarget = RTM.GetRenderTarget(textureFormat, w, h, locked=True)
            w = renderTarget.width
            h = renderTarget.height
            textureCompositor.renderTarget = renderTarget
            textureCompositor.targetWidth = w
            textureCompositor.Start(clear=False)
            if mapBundle[mapType]:
                textureCompositor.CopyBlitTexture(mapBundle[mapType])
            self.CompositeStepsFunction(buildDataManager, gender, mapType, partsToComposite, textureCompositor, w, h, lod=lod)
            textureCompositor.End()
            while not textureCompositor.isReady:
                pdCf.Yield()

            if copyToExistingTexture and mapBundle[mapType].isGood:
                tex = textureCompositor.Finalize(textureFormat, w, h, generateMipmap=compressionSettings.generateMipmap, textureToCopyTo=mapBundle[mapType], compressionSettings=compressionSettings, mapType=mapType)
            else:
                tex = textureCompositor.Finalize(textureFormat, w, h, generateMipmap=compressionSettings.generateMipmap, compressionSettings=compressionSettings, mapType=mapType)
            textureCompositor.renderTarget = None
            return tex
        except (trinity.E_OUTOFMEMORY, trinity.D3DERR_OUTOFVIDEOMEMORY):
            raise
        except TaskletExit:
            RTM.ReturnLockedRenderTarget(renderTarget)
            if textureCompositor:
                textureCompositor.renderTarget = None
            raise
        finally:
            RTM.ReturnLockedRenderTarget(renderTarget)

    @telemetry.ZONE_METHOD
    def _CompositeDiffuseMap(self, modifierList, bodyPart, textureCompositor, width, height, addAlpha = False, lod = 0):
        for m in iter(modifierList):
            pdCf.BeFrameNice()
            if m.stubblePath and lod in [pdDef.LOD_SKIN, pdDef.LOD_SCATTER_SKIN]:
                continue
            subrect = self.GetSubRect(bodyPart, width, height, m)
            srcRect = None
            texture = m.mapD
            skipAlpha = False
            useAlphaTest = False
            if m.colorize and bodyPart in m.mapL:
                if bodyPart not in m.mapO:
                    m.mapO[bodyPart] = pdDef.TEXTURE_STUB
                if bodyPart not in m.mapZ:
                    m.mapZ[bodyPart] = pdDef.TEXTURE_STUB
                if m.categorie in (pdDef.BODY_CATEGORIES.SKINTONE,
                 pdDef.BODY_CATEGORIES.SKINTYPE,
                 pdDef.HEAD_CATEGORIES.MAKEUP,
                 pdDef.BODY_CATEGORIES.TATTOO,
                 pdDef.BODY_CATEGORIES.SCARS,
                 pdDef.DOLL_EXTRA_PARTS.BODYSHAPES,
                 pdDef.HEAD_CATEGORIES.FACEMODIFIERS):
                    if pdDef.MAKEUP_GROUPS.IMPLANTS in m.group:
                        skipAlpha = False
                        addAlpha = True
                    elif pdDef.MAKEUP_GROUPS.EYELASHES in m.group or pdDef.MAKEUP_GROUPS.EYEBROWS in m.group:
                        skipAlpha = False
                        addAlpha = True
                        useAlphaTest = True
                    else:
                        skipAlpha = True
                        addAlpha = True
                if m.categorie == pdDef.DOLL_PARTS.HAIR and bodyPart == pdDef.DOLL_PARTS.HEAD:
                    skipAlpha = False
                    addAlpha = True
                if m.pattern == '':
                    colors = m.colorizeData
                    if bodyPart == pdDef.DOLL_PARTS.HAIR:
                        textureCompositor.ColorizedCopyBlitTexture(m.mapL[bodyPart], m.mapZ[bodyPart], m.mapO[bodyPart], colors[0], colors[1], colors[2], subrect)
                    else:
                        textureCompositor.ColorizedBlitTexture(m.mapL[bodyPart], m.mapZ[bodyPart], m.mapO[bodyPart], colors[0], colors[1], colors[2], subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, useAlphaTest=useAlphaTest, weight=m.weight)
                else:
                    colors = m.patternData
                    patternDir = self.GetPatternDir()
                    patternPath = '{0}/{1}_z.dds'.format(patternDir, m.pattern)
                    if legacy_r_drive.loadFromContent:
                        if not os.path.exists(pdDef.OUTSOURCING_JESSICA_PATH):
                            patternPath = patternPath.replace('.dds', '.tga')
                    textureCompositor.PatternBlitTexture(patternPath, m.mapL[bodyPart], m.mapZ[bodyPart], m.mapO[bodyPart], colors[0], colors[1], colors[2], colors[3], colors[4], subrect, patternTransform=colors[5], patternRotation=colors[6], addAlpha=addAlpha, skipAlpha=skipAlpha)
            if bodyPart in texture and not (m.colorize and m.categorie == pdDef.BODY_CATEGORIES.TATTOO):
                maskname = tname = texture[bodyPart]
                if not (isinstance(tname, basestring) and pdDef.SKIN_GENERIC_PATH in tname.lower()):
                    if bodyPart in texture:
                        maskname = texture[bodyPart]
                    elif bodyPart in m.mapL:
                        maskname = m.mapL[bodyPart]
                    skipAlpha = False
                    if m.categorie in (pdDef.BODY_CATEGORIES.SKINTONE,
                     pdDef.BODY_CATEGORIES.SKINTYPE,
                     pdDef.HEAD_CATEGORIES.MAKEUP,
                     pdDef.BODY_CATEGORIES.TATTOO,
                     pdDef.BODY_CATEGORIES.SCARS,
                     pdDef.DOLL_EXTRA_PARTS.BODYSHAPES,
                     pdDef.HEAD_CATEGORIES.ARCHETYPES,
                     pdDef.HEAD_CATEGORIES.FACEMODIFIERS):
                        if pdDef.MAKEUP_GROUPS.EYELASHES in m.group:
                            skipAlpha = False
                            addAlpha = False
                        else:
                            skipAlpha = True
                            addAlpha = True
                    if m.categorie == pdDef.DOLL_PARTS.HAIR and bodyPart == pdDef.DOLL_PARTS.HEAD:
                        skipAlpha = False
                        addAlpha = True
                    if bodyPart == pdDef.DOLL_PARTS.HAIR:
                        textureCompositor.CopyBlitTexture(tname, subrect=subrect, srcRect=srcRect)
                    else:
                        textureCompositor.BlitTexture(tname, maskname, m.weight, subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, srcRect=srcRect, multAlpha=False)

    @telemetry.ZONE_METHOD
    def _CompositeSpecularMap(self, modifierList, bodyPart, textureCompositor, width, height, addAlpha = False, lod = 0):
        for m in iter(modifierList):
            pdCf.BeFrameNice()
            if m.stubblePath and lod in [pdDef.LOD_SKIN, pdDef.LOD_SCATTER_SKIN]:
                continue
            subrect = self.GetSubRect(bodyPart, width, height, m)
            srcRect = None
            skipAlpha = False
            maskname = tname = m.mapSRG.get(bodyPart)
            if bodyPart in m.mapSRG and not (m.categorie == pdDef.BODY_CATEGORIES.TATTOO or isinstance(tname, basestring) and pdDef.SKIN_GENERIC_PATH in tname.lower()):
                if bodyPart in m.mapD:
                    maskname = m.mapD[bodyPart]
                elif bodyPart in m.mapL:
                    maskname = m.mapL[bodyPart]
                skipAlpha = True
                addAlpha = True
                if m.useSkin:
                    tname = tname.replace('_S.', '_SR.')
                doColorizedStep = False
                if m.colorize and m.specularColorData:
                    doColorizedStep = bodyPart in m.mapL
                    if bodyPart == pdDef.DOLL_PARTS.HAIR:
                        textureCompositor.CopyBlitTexture(tname, subrect=subrect, srcRect=srcRect)
                        doColorizedStep = True
                    if doColorizedStep:
                        if bodyPart not in m.mapO:
                            m.mapO[bodyPart] = pdDef.TEXTURE_STUB
                        if bodyPart not in m.mapZ:
                            m.mapZ[bodyPart] = pdDef.TEXTURE_STUB
                        colors = m.specularColorData
                        textureCompositor.ColorizedBlitTexture(m.mapSRG[bodyPart], m.mapZ[bodyPart], m.mapO[bodyPart], colors[0], colors[1], colors[2], mask=maskname, subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, weight=m.weight)
                if not doColorizedStep:
                    textureCompositor.BlitTexture(tname, maskname, m.weight, subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, srcRect=srcRect, multAlpha=False)
                if m.colorize and m.specularColorData and bodyPart in m.mapZ:
                    values = (m.specularColorData[0][3],
                     m.specularColorData[1][3],
                     m.specularColorData[2][3],
                     1.0)
                    textureCompositor.BlitAlphaIntoAlphaWithMaskAndZones(tname, maskname, m.mapZ[bodyPart], values, subrect=subrect, srcRect=srcRect)
                else:
                    textureCompositor.BlitAlphaIntoAlphaWithMask(tname, maskname, subrect=subrect, srcRect=srcRect)

    @telemetry.ZONE_METHOD
    def _CompositeNormalMap(self, modifierList, bodyPart, textureCompositor, width, height, addAlpha = False, lod = None):
        for m in iter(modifierList):
            pdCf.BeFrameNice()
            if m.categorie == pdDef.DOLL_EXTRA_PARTS.BODYSHAPES and lod > pdDef.LOD_0:
                continue
            texture = m.mapN
            subrect = self.GetSubRect(bodyPart, width, height, m)
            srcRect = None
            skipAlpha = False
            if bodyPart in texture and m.respath != 'skin/generic':
                maskname = tname = texture[bodyPart]
                if bodyPart in m.mapD:
                    maskname = m.mapD[bodyPart]
                elif bodyPart in m.mapL:
                    maskname = m.mapL[bodyPart]
                skipAlpha = False
                if m.categorie in (pdDef.BODY_CATEGORIES.SKINTONE,
                 pdDef.BODY_CATEGORIES.SKINTYPE,
                 pdDef.HEAD_CATEGORIES.MAKEUP,
                 pdDef.BODY_CATEGORIES.TATTOO,
                 pdDef.BODY_CATEGORIES.SCARS,
                 pdDef.DOLL_EXTRA_PARTS.BODYSHAPES,
                 pdDef.HEAD_CATEGORIES.ARCHETYPES,
                 pdDef.HEAD_CATEGORIES.FACEMODIFIERS):
                    skipAlpha = True
                    addAlpha = True
                elif m.categorie == pdDef.DOLL_PARTS.HAIR and bodyPart == pdDef.DOLL_PARTS.HEAD:
                    skipAlpha = False
                    addAlpha = True
                if bodyPart == pdDef.DOLL_PARTS.HAIR:
                    textureCompositor.CopyBlitTexture(tname, subrect=subrect, srcRect=srcRect, isNormalMap=True)
                else:
                    textureCompositor.BlitTexture(tname, maskname, m.weight, subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, srcRect=srcRect, multAlpha=False, isNormalMap=True)
            mapD = m.mapD.get(bodyPart)
            mapMN = m.mapMN.get(bodyPart)
            mapTN = m.mapTN.get(bodyPart)
            if mapMN:
                textureCompositor.MaskedNormalBlitTexture(mapMN, m.weight, subrect, srcRect=srcRect)
            if mapTN:
                textureCompositor.TwistNormalBlitTexture(mapTN, m.weight, subrect, srcRect=srcRect)
            if mapD and m.categorie not in (pdDef.BODY_CATEGORIES.SKINTONE,
             pdDef.BODY_CATEGORIES.SKINTYPE,
             pdDef.BODY_CATEGORIES.TATTOO,
             pdDef.BODY_CATEGORIES.SCARS,
             pdDef.DOLL_EXTRA_PARTS.BODYSHAPES,
             pdDef.HEAD_CATEGORIES.ARCHETYPES,
             pdDef.HEAD_CATEGORIES.FACEMODIFIERS):
                if m.categorie in pdDef.CATEGORIES_THATCLEAN_MATERIALMAP:
                    textureCompositor.SubtractAlphaFromAlpha(mapD, subrect, srcRect=srcRect)
                mapMM = m.mapMaterial.get(bodyPart)
                if mapMM is not None:
                    textureCompositor.BlitTextureIntoAlphaWithMask(mapMM, mapD, subrect, srcRect=srcRect)
                else:
                    textureCompositor.BlitTextureIntoAlphaWithMask(mapD, mapD, subrect, srcRect=srcRect)

    @telemetry.ZONE_METHOD
    def _CompositeMaskMap(self, modifierList, bodyPart, textureCompositor, width, height, addAlpha = False, lod = None):
        for m in iter(modifierList):
            pdCf.BeFrameNice()
            texture = m.mapMask
            subrect = self.GetSubRect(bodyPart, width, height, m)
            srcRect = None
            skipAlpha = False
            if bodyPart in texture:
                maskname = tname = texture[bodyPart]
                tname = texture[bodyPart].lower()
                textureCompositor.BlitTexture(tname, maskname, m.weight, subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, srcRect=srcRect, multAlpha=False)
                if not (isinstance(tname, basestring) and pdDef.SKIN_GENERIC_PATH in tname):
                    skipAlpha = False
                    if m.categorie in (pdDef.BODY_CATEGORIES.SKINTONE,
                     pdDef.BODY_CATEGORIES.SKINTYPE,
                     pdDef.HEAD_CATEGORIES.MAKEUP,
                     pdDef.BODY_CATEGORIES.TATTOO,
                     pdDef.BODY_CATEGORIES.SCARS,
                     pdDef.DOLL_EXTRA_PARTS.BODYSHAPES,
                     pdDef.HEAD_CATEGORIES.ARCHETYPES,
                     pdDef.HEAD_CATEGORIES.FACEMODIFIERS):
                        skipAlpha = True
                        addAlpha = True
                    if m.categorie == pdDef.DOLL_PARTS.HAIR and bodyPart == pdDef.DOLL_PARTS.HEAD:
                        skipAlpha = False
                        addAlpha = True
                    textureCompositor.BlitTexture(tname, maskname, m.weight, subrect=subrect, addAlpha=addAlpha, skipAlpha=skipAlpha, srcRect=srcRect, multAlpha=False)

    @telemetry.ZONE_METHOD
    def _CompositeTexture(self, modifierList, bodyPart, textureCompositor, textureType, width, height, addAlpha = False, lod = None):
        partSpecificModifierGenerator = (m for m in modifierList if bodyPart in m.GetAffectedTextureParts())
        if textureType == pdDef.DIFFUSE_MAP:
            return self._CompositeDiffuseMap(partSpecificModifierGenerator, bodyPart, textureCompositor, width, height, addAlpha, lod)
        if textureType == pdDef.SPECULAR_MAP:
            return self._CompositeSpecularMap(partSpecificModifierGenerator, bodyPart, textureCompositor, width, height, addAlpha, lod)
        if textureType == pdDef.NORMAL_MAP:
            return self._CompositeNormalMap(partSpecificModifierGenerator, bodyPart, textureCompositor, width, height, addAlpha, lod)
        if textureType == pdDef.MASK_MAP:
            return self._CompositeMaskMap(partSpecificModifierGenerator, bodyPart, textureCompositor, width, height, addAlpha, lod)
        raise ValueError('Paperdoll::Unsupported texturetype passed to compositing')

    @staticmethod
    @telemetry.ZONE_FUNCTION
    def SetResourceTexture(effectResource, texture):
        if isinstance(texture, str):
            if effectResource.resourcePath != texture:
                effectResource.resourcePath = texture
        else:
            effectResource.resourcePath = ''
            effectResource.SetResource(texture)

    @telemetry.ZONE_METHOD
    def BuildMeshForAvatar(self, avatar, avatarName, buildSources, createDynamicLOD = False, bodyShapesActive = {}, overrideLod = 0, weldthreshold = 1e-09, meshName = 'mesh', addMesh = False, asyncLOD = False):
        """
        asyncLOD - if False, set up the proxies and return the full avatar; this is used in Jessica etc, 
        it's the old behavior where everything is set up and running without further work;
        If True, only the visual model is built, and it's directly returned, caller needs to hook it up.
        """
        builder = trinity.WodAvatar2Builder()
        avatarName = str(avatarName)
        if asyncLOD:
            builder.createGPUMesh = True
            builder.effectPath = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDFDouble.fx'
            if overrideLod == 2:
                weldthreshold = 0
        for each in iter(buildSources):
            builder.sourceMeshesInfo.append(each)

        realBsNames = {}
        realBsNames['fatshape'] = 'FatShape'
        realBsNames['thinshape'] = 'ThinShape'
        realBsNames['muscularshape'] = 'MuscularShape'
        realBsNames['softshape'] = 'SoftShape'
        if bodyShapesActive:
            for bs in bodyShapesActive:
                for suffix in ['',
                 '1',
                 '2',
                 '3',
                 '4',
                 '5',
                 '6']:
                    blendshape1 = trinity.WodAvatar2BuilderBlend()
                    if bs in realBsNames:
                        blendshape1.name = realBsNames[bs] + suffix
                    else:
                        blendshape1.name = bs + suffix
                    blendshape1.power = bodyShapesActive[bs]
                    builder.blendshapeInfo.append(blendshape1)

        cachePath = blue.paths.ResolvePath('cache:/Avatars/' + avatarName)
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        builder.outputName = str('cache:/Avatars/' + avatarName + '/' + meshName + '.gr2')
        builder.weldThreshold = weldthreshold

        class BuildEvent:

            def __init__(self):
                self.isDone = False
                self.succeeded = False

            def __call__(self, success):
                self.isDone = True
                self.succeeded = success

            def Wait(self):
                while not self.isDone:
                    blue.pyos.synchro.Yield()

        def BuildSkinnedModel(avatarBuilder, lod):
            avatarBuilder.lod = lod
            avatarBuilder.PrepareForBuild()
            evt = BuildEvent()
            avatarBuilder.BuildAsync(evt)
            evt.Wait()
            if not evt.succeeded:
                return None
            ret = avatarBuilder.GetSkinnedModel()
            return ret

        if asyncLOD:
            return BuildSkinnedModel(builder, overrideLod)

    @telemetry.ZONE_METHOD
    def RemoveMeshesFromVisualModel(self, visualModel, ignoreMeshes = None):
        """
        If 'ignoreMeshes' is provided, removes only those meshes from the supplied 'visualModel'
        that are not in ignoreMeshes
        Otherwise, removes all meshes from the visualmodel
        """
        if ignoreMeshes:
            remIdxs = []
            vmMeshCount = len(visualModel.meshes)
            for i in xrange(vmMeshCount):
                if visualModel.meshes[i] not in ignoreMeshes:
                    remIdxs.insert(0, i)

            for i in remIdxs:
                del visualModel.meshes[i]

        else:
            del visualModel.meshes[:]

    @telemetry.ZONE_METHOD
    def AppendMeshesToVisualModel(self, visualModel, meshes):
        for mesh in iter(meshes):
            if type(mesh) is trinity.Tr2Mesh and mesh not in visualModel.meshes:
                visualModel.meshes.append(mesh)

    @telemetry.ZONE_METHOD
    def RemoveMeshesFromVisualModelByCategory(self, visualModel, category):
        remList = []
        for each in iter(visualModel.meshes):
            if each.name.startswith(category):
                remList.append(each)

        for each in iter(remList):
            visualModel.meshes.remove(each)

    @telemetry.ZONE_METHOD
    def ReplaceMeshesOnAvatar(self, visualModel, meshes):
        remList = []
        for each in iter(meshes):
            for every in iter(visualModel.meshes):
                if every.name == each.name:
                    remList.append(every)

        for each in iter(remList):
            visualModel.meshes.remove(each)

        self.AppendMeshesToVisualModel(visualModel, meshes)

    @telemetry.ZONE_METHOD
    def GetDNAFromYamlFile(self, filename):
        """
        Returns the DNA string representing a doll configuration from a given filename 
        that has been saved using YAML.
        """
        if blue.paths.exists(filename):
            resFile = blue.ResFile()
            resFile.Open(filename)
            yamlStr = resFile.Read()
            resFile.Close()
            if len(yamlStr) == 0:
                raise Exception('PaperDoll::Factory::GetDNAFromYamlFile - Error, loading an empty file!')
            dna = pdCf.NastyYamlLoad(yamlStr)
            return dna
        raise Exception('No %s file found' % filename)


class RedundantUpdateException(Exception):
    """
    Custom error class to print only warning when Update() is called on a Doll when there is
    nothing to update.
    """
    __guid__ = 'paperDoll.RedundantUpdateException'


class OutOfVideoMemoryException(Exception):
    """
    Custom error class used to signal that we've run out of video memory during Update
    """
    __guid__ = 'paperDoll.OutOfVideoMemoryException'


class Doll(object):
    """
    A Doll instance (the paperdoll) is responsible for containing the data and methods required
    to apply the modifications neccesary to an avatar and a visualModel that togeather make up
    the visual representation of an in game character.
    
    Changes to a doll are done through adding and removing modifiers mostly via AddResource(s) 
    and RemoveResource. A call to Update() submits those changes so that they become visible. 
    
    Modifiers are instances of BuildData and they are managed through the doll's BuildDataManager
    instance. Changes to attributes of a modifier also result in some visual changes, and they are
    also reflected through calls to Update().    
    
    Glossary:
    'avatar' is the pythonic name for a trinity.WodExtSkinnedObject() or trinity.Tr2IntSkinnedObject(),
    the type really depends on the scene in which the character is in. This instance also contains
    the cloth geometry for simulated cloth.
    
    'visualModel' is the pythonic name for a trinity.Tr2SkinnedModel and contains the geometry of the
    character for its current LOD.
    
    Character LOD setup is done in an external file, called paperDollLOD.py, in the same folder as
    this file.
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.Doll'
    __nextInstanceID = -1

    @staticmethod
    def GetInstanceID():
        """
        Generates instance ID's that are used when doing instance equality comparison between dolls.
        """
        Doll.__nextInstanceID += 1
        return Doll.__nextInstanceID

    @staticmethod
    def InstanceEquals(dollA, dollB):
        return dollA.instanceID == dollB.instanceID

    def __init__(self, name, gender = pdDef.GENDER.FEMALE):
        object.__init__(self)
        self.instanceID = Doll.GetInstanceID()
        self.mapBundle = MapBundle()
        self.compressionSettings = None
        self.hasDelayedUpdateCallPending = False
        self.onUpdateDoneListeners = []
        self.name = name
        self.buildDataManager = pdDm.BuildDataManager()
        self.UVs = {pdDef.DOLL_PARTS.HEAD: pdDef.DEFAULT_UVS,
         pdDef.DOLL_PARTS.BODY: pdDef.DEFAULT_UVS,
         pdDef.DOLL_PARTS.HAIR: pdDef.DEFAULT_UVS,
         pdDef.DOLL_PARTS.ACCESSORIES: pdDef.DEFAULT_UVS}
        self.morphsLoaded = False
        self.isOptimized = False
        self.hasUpdatedOnce = False
        self.currentLOD = 0
        self.previousLOD = 0
        self.usePrepass = False
        self.avatarType = 'interior'
        self.gender = gender
        self.busyBaking = False
        self.busyLoadingDNA = False
        self.busyHandlingBlendshapes = False
        self.lastUpdateRedundant = False
        self.hairColorizeData = []
        self.boneOffsets = {}
        self.bindPose = None
        self.skinLightmapRenderer = None
        self.__updateFrameStamp = -1
        self.__useFastShader = False
        self.renderDriver = renderDrivers.RenderDriverNCC()
        self.lastRenderDriverClass = None
        self._currentUpdateTasklet = None
        self._UpdateTaskletChildren = []
        self.decalBaker = None
        trinity.device.RegisterResource(self)
        self.deviceResetAvatar = None
        self.useMaskedShaders = False
        self.useDXT5N = False
        self.usePrepassAlphaTestHair = False
        self.blendShapeMeshCache = {}
        self.clothMorphValues = {}

    def __del__(self):
        self.StopPaperDolling()
        self.skinLightmapRenderer = None
        del self.mapBundle

    def GetName(self):
        return self.name

    def GetProjectedDecals(self):
        """
        Returns a list of all modifiers that are projected decals.
        These are modifiers in the Tattoo categorie, with decalData.
        """
        modifiers = self.buildDataManager.GetModifiersByCategory(pdDef.BODY_CATEGORIES.TATTOO)
        modifiers = [ modifier for modifier in modifiers if modifier.decalData ]
        return modifiers

    def OnInvalidate(self, level):
        if self.skinLightmapRenderer is not None:
            self.skinLightmapRenderer.StopRendering()
            self.deviceResetAvatar = self.skinLightmapRenderer.skinnedObject
            del self.skinLightmapRenderer
            self.skinLightmapRenderer = None

    def OnCreate(self, dev):
        if self.currentLOD == pdDef.LOD_SCATTER_SKIN and not self.usePrepass:

            def skinCreate_t():
                if self.skinLightmapRenderer is None:
                    self.skinLightmapRenderer = SkinLightmapRenderer()
                self.skinLightmapRenderer.SetSkinnedObject(self.deviceResetAvatar)
                self.skinLightmapRenderer.StartRendering()
                self.deviceResetAvatar = None

            t = uthread.new(skinCreate_t)
            uthread.schedule(t)

    def StopPaperDolling(self, clearMaps = True):
        """
        Signal the doll that it is no longer being actively used for paperdolling and fine adjustments.
        Releases all in-memory cache that is only used for change related performance purposes.
        """
        for each in self.buildDataManager.GetModifiersAsList():
            each.ClearCachedData()

        if clearMaps:
            self.mapBundle.ReCreate()
        self.decalBaker = None

    def SetUsePrepass(self, val = True):
        """
        Call doll.SetUsePrepass() to enable prepass shaders.
        Call doll.SetUsePrepass(False) to disable prepass shaders.
        """
        self.usePrepass = val
        if val == True:
            self.lastRenderDriverClass = self.renderDriver.__class__
            if pdCfg.PerformanceOptions.collapseShadowMesh or pdCfg.PerformanceOptions.collapseMainMesh or pdCfg.PerformanceOptions.collapsePLPMesh:
                self.renderDriver = renderDrivers.RenderDriverCollapsePLP()
            else:
                self.renderDriver = renderDrivers.RenderDriverPLP()
        elif self.lastRenderDriverClass:
            lastClass = self.renderDriver.__class__
            self.renderDriver = self.lastRenderDriverClass()
            self.lastRenderDriverClass = lastClass

    def IsPrepass(self):
        """
        Returns true if set to use prepass shaders, otherwise, returns False.
        """
        if self.usePrepass:
            return True
        return False

    def GetMorphsFromGr2(self, gr2Path):
        names = {}
        resMan = blue.resMan
        gr2Res = resMan.GetResource(gr2Path, 'raw')
        while gr2Res.isLoading:
            pdCf.Yield()

        meshCount = gr2Res.GetMeshCount()
        for i in xrange(meshCount):
            morphCount = gr2Res.GetMeshMorphCount(i)
            for j in xrange(morphCount):
                name = gr2Res.GetMeshMorphName(i, j)
                data = names.get(i, [])
                data.append(name)
                names[i] = data

        return (gr2Res, names)

    def _AnalyzeBuildDataForRules(self, updateRuleBundle, buildDataManager):
        """
        Generates ruleset used during updating.
        This used to be set on the doll, but that is not tasklet safe.
        """
        modifierList = buildDataManager.GetModifiersAsList()
        forcesLooseTop = False
        hidesBootShin = False
        swapTops = False
        swapBottom = False
        swapSocks = False
        useMaskedShaders = False
        for modifier in iter(modifierList):
            useMaskedShaders = True
            metaData = modifier.metaData
            if metaData:
                forcesLooseTop = forcesLooseTop or metaData.forcesLooseTop
                hidesBootShin = hidesBootShin or metaData.hidesBootShin
                swapTops = swapTops or metaData.swapTops
                swapBottom = swapBottom or metaData.swapBottom
                swapSocks = swapSocks or metaData.swapSocks

        if not useMaskedShaders and self.useMaskedShaders:
            updateRuleBundle.undoMaskedShaders = True
        if hidesBootShin:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.FEET, pdDef.BODY_CATEGORIES.FEETTUCKED)
        else:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.FEETTUCKED, pdDef.BODY_CATEGORIES.FEET)
        if forcesLooseTop:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.BOTTOMOUTERTUCKED, pdDef.BODY_CATEGORIES.BOTTOMOUTER)
        else:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.BOTTOMOUTER, pdDef.BODY_CATEGORIES.BOTTOMOUTERTUCKED)
        if swapTops:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.TOPMIDDLE, pdDef.BODY_CATEGORIES.TOPTIGHT)
        else:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.TOPTIGHT, pdDef.BODY_CATEGORIES.TOPMIDDLE)
        if swapBottom:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.TOPUNDERWEARTUCKED, pdDef.BODY_CATEGORIES.TOPUNDERWEAR)
        else:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.TOPUNDERWEAR, pdDef.BODY_CATEGORIES.TOPUNDERWEARTUCKED)
        if swapSocks:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.SOCKS, pdDef.BODY_CATEGORIES.SOCKSTUCKED)
        else:
            buildDataManager.ChangeDesiredOrder(pdDef.BODY_CATEGORIES.SOCKSTUCKED, pdDef.BODY_CATEGORIES.SOCKS)
        self.useMaskedShaders = useMaskedShaders
        updateRuleBundle.forcesLooseTop = forcesLooseTop
        updateRuleBundle.hidesBootShin = hidesBootShin
        updateRuleBundle.swapTops = swapTops
        updateRuleBundle.swapBottom = swapBottom
        updateRuleBundle.swapSocks = swapSocks

    def AdjustGr2PathForLod(self, gr2Path, resDataEntry):
        """
        change path to redirect to a different gr2 file based on lod and/or separate-folder settings.
        """
        adjustedGr2Path = resDataEntry.GetGeoLodMatch(gr2Path, self.currentLOD)
        return adjustedGr2Path

    def __AdjustMeshForLod(self, mesh, resDataEntry):
        """
        Given a mesh with a valid geometryResPath, change that path to redirect to a different gr2
        file based on lod and/or separate-folder settings.
        """
        mesh.geometryResPath = self.AdjustGr2PathForLod(mesh.geometryResPath, resDataEntry)

    def AdjustRedFileForLod(self, redfile, resDataEntry):
        """
        Given the path of a (builddata's) redfile, redirect it to a separate folder and/or file
        based on the current lod.
        """
        if not (resDataEntry and pdCfg.PerformanceOptions.useLodForRedfiles):
            return redfile
        return resDataEntry.GetGeoLodMatch(redfile, self.currentLOD)

    def _ProcessRules(self, factory, buildDataManager, modifierList, updateRuleBundle, useCloth = False):
        """
        This method loads up geometry for modifiers in modifierList according to state set to the doll
        after __AnalyzeBuildDataForRules. It is responsible for setting up tucking, having the hair stay
        put under hats, applying material overrides and using masked shaders.
        """
        if not modifierList:
            return
        if updateRuleBundle.rebuildHair:
            hairModifiers = [ x for x in buildDataManager.GetHairModifiers() if x not in modifierList ]
            modifierList.extend(hairModifiers)
        loadedObjects = {}
        modifiersWithDataToLoad = [ modifier for modifier in modifierList if modifier.weight > 0 and (modifier.redfile and not modifier.meshes or modifier.IsMeshDirty()) ]
        modLen = len(modifiersWithDataToLoad)
        remIdx = []
        AdjustRedFileForLod = self.AdjustRedFileForLod
        GetResDataEntryByFullResPath = factory.resData.GetEntryByFullResPath

        def LoadObject(filename):
            if not filename:
                return None
            return blue.resMan.LoadObject(filename)

        for i in xrange(modLen):
            modifier = modifiersWithDataToLoad[i]
            redfile = modifier.clothOverride if useCloth and modifier.clothOverride else modifier.redfile
            if id(modifier) not in loadedObjects:
                resDataEntry = GetResDataEntryByFullResPath(redfile)
                redfileLod = AdjustRedFileForLod(redfile, resDataEntry)
                self.renderDriver.OnModifierRedfileLoaded(modifier, redfileLod)
                if not modifier.meshes or redfileLod != modifier.redfile:
                    objToLoad = LoadObject(redfileLod)
                    if objToLoad is None:
                        objToLoad = LoadObject(redfile)
                    loadedObjects[id(modifier)] = objToLoad
                else:
                    remIdx.insert(0, i)
            pdCf.BeFrameNice()

        for i in iter(remIdx):
            del modifiersWithDataToLoad[i]

        pathCache = {}
        for modifier in iter(modifiersWithDataToLoad):
            modifier.ClearCachedData()
            newBodyPart = loadedObjects.get(id(modifier), None)
            if newBodyPart and hasattr(newBodyPart, 'meshes'):
                for i, mesh in enumerate(newBodyPart.meshes):
                    oldPath = mesh.geometryResPath
                    newPath = pathCache.get(oldPath)
                    if newPath:
                        mesh.geometryResPath = newPath
                    else:
                        resDataEntry = GetResDataEntryByFullResPath(modifier.redfile)
                        self.__AdjustMeshForLod(mesh, resDataEntry)
                        pathCache[oldPath] = mesh.geometryResPath
                    if modifier.categorie == pdDef.DOLL_PARTS.HAIR:
                        if mesh.name == pdCcf.HAIR_MESH_SHAPE:
                            pdCcf.MoveAreas(mesh.opaqueAreas, mesh.transparentAreas)
                            pdCcf.MoveAreas(mesh.decalAreas, mesh.transparentAreas)
                        else:
                            pdCcf.MoveAreas(mesh.opaqueAreas, mesh.decalAreas)
                            pdCcf.MoveAreas(mesh.transparentAreas, mesh.decalAreas)
                    if mesh.name in pdCcf.DRAPE_TUCK_NAMES:
                        pdCcf.MoveAreas(mesh.opaqueAreas, mesh.transparentAreas)
                    if modifier.categorie not in pdDef.CATEGORIES_CONTAINING_GROUPS:
                        mesh.name = '{0}{1}'.format(modifier.categorie, mesh.meshIndex)
                    else:
                        mesh.name = '{0}{1}'.format(modifier.name, mesh.meshIndex)
                    if self.blendShapeMeshCache.get(mesh.name):
                        del self.blendShapeMeshCache[mesh.name]
                    modifier.meshes.append(mesh)
                    modifier.meshGeometryResPaths[mesh.name] = mesh.geometryResPath

    @telemetry.ZONE_METHOD
    def __ApplyUVs(self):
        """        
        Applies UVs by setting the TransformUV0 parameter on all the meshes kept in the dolls modifiers.
        """
        UVCalculator.ApplyUVs(self.buildDataManager, self.renderDriver)

    def _HandleBlendShapes(self, removedModifiers = None):
        """
        Handles the application of blendshapes to the doll's meshes.
        For every blendshape that is being removed, we set its weight to 0, apply it and then remove it.
        This process happens in a tasklet and will be killed if the Update tasklet is preempted.
        """
        self.decalBaker = None
        self.SpawnUpdateChildTasklet(self.__HandleBlendShapes_t, removedModifiers)

    @telemetry.ZONE_METHOD
    def __HandleClothBlendShapes_t(self, clothMeshes, morphTargets):
        pdCf.BeFrameNice()
        Factory.ProcessBlendshapesForCloth(clothMeshes, morphTargets, clothMorphValues=self.clothMorphValues)

    @telemetry.ZONE_METHOD
    def __HandleBlendShapes_t(self, removedModifiers):
        try:
            self.busyHandlingBlendshapes = True
            pdCf.BeFrameNice()
            modifierList = self.buildDataManager.GetModifiersAsList()
            morphTargets = self.buildDataManager.GetMorphTargets()
            if morphTargets:
                meshGeometryResPaths = {}
                for modifier in iter(modifierList):
                    meshGeometryResPaths.update(modifier.meshGeometryResPaths)

                meshesIncludingClothMeshes = self.buildDataManager.GetMeshes(includeClothMeshes=True)
                clothMeshes = [ mesh for mesh in meshesIncludingClothMeshes if type(mesh) == trinity.Tr2ClothingActor ]
                self.SpawnUpdateChildTasklet(self.__HandleClothBlendShapes_t, clothMeshes, morphTargets)
                meshes = [ mesh for mesh in meshesIncludingClothMeshes if type(mesh) == trinity.Tr2Mesh ]
                Factory.ApplyMorphTargetsToMeshes(meshes, morphTargets, self.blendShapeMeshCache, meshGeometryResPaths)
                self.renderDriver.OnApplyMorphTargets(meshes, morphTargets)
                for mesh in iter(meshes):
                    if mesh.name not in self.blendShapeMeshCache:
                        mesh.deferGeometryLoad = False

        finally:
            for mesh in self.buildDataManager.GetMeshes(alternativeModifierList=removedModifiers, includeClothMeshes=True):
                if self.blendShapeMeshCache.get(mesh.name):
                    del self.blendShapeMeshCache[mesh.name]
                key = str(mesh)
                if self.clothMorphValues.get(key):
                    del self.clothMorphValues[key]

            self.busyHandlingBlendshapes = False

    def ApplyBoneOffsets(self):
        """
        Applies bone offsets to the given modifiers in 'modifierList'
        """
        self.boneOffsets = {}
        modifiersDone = {}
        for modifier in (modifier for modifier in self.buildDataManager.GetModifiersAsList() if modifier.poseData):
            if modifier.respath not in modifiersDone:
                modifiersDone[modifier.respath] = None
                weight = modifier.weight
                for bone in iter(modifier.poseData):
                    if bone not in self.boneOffsets:
                        newT = modifier.poseData[bone][pdCcf.TRANSLATION]
                        newR = modifier.poseData[bone][pdCcf.ROTATION]
                        self.boneOffsets[bone] = {}
                        self.boneOffsets[bone][pdCcf.TRANSLATION] = (newT[0] * weight, newT[1] * weight, newT[2] * weight)
                        self.boneOffsets[bone][pdCcf.ROTATION] = (newR[0] * weight, newR[1] * weight, newR[2] * weight)
                    else:
                        prevT = self.boneOffsets[bone][pdCcf.TRANSLATION]
                        prevR = self.boneOffsets[bone][pdCcf.ROTATION]
                        newT = modifier.poseData[bone][pdCcf.TRANSLATION]
                        newR = modifier.poseData[bone][pdCcf.ROTATION]
                        self.boneOffsets[bone][pdCcf.TRANSLATION] = (prevT[0] + newT[0] * weight, prevT[1] + newT[1] * weight, prevT[2] + newT[2] * weight)
                        self.boneOffsets[bone][pdCcf.ROTATION] = (prevR[0] + newR[0] * weight, prevR[1] + newR[1] * weight, prevR[2] + newR[2] * weight)

    def _EnsureCompleteBody(self, factory):
        """
        Adds or shows modifiers required to display a complete doll.
        When default nude modifier is explicitly hidden, that part of the doll will disappear.
        """

        def BodyPartSearch(modifier, categoryStartsWith):
            return modifier.IsMeshContainingModifier() and modifier.categorie.startswith(categoryStartsWith)

        def EnsureBodyPart(bodyModifiers, categoryStartsWith, defaultPart):
            if not any(map(lambda x: BodyPartSearch(x, categoryStartsWith), bodyModifiers)):
                self.AddResource(defaultPart, 1.0, factory, privilegedCaller=True)

        headModifier = self.buildDataManager.GetModifierByResPath(pdDef.DEFAULT_NUDE_HEAD)
        if not headModifier:
            self.AddResource(pdDef.DEFAULT_NUDE_HEAD, 1.0, factory, privilegedCaller=True)
        if self.currentLOD != 2:
            makeupModifiers = self.buildDataManager.GetModifiersByCategory(pdDef.HEAD_CATEGORIES.MAKEUP)
            foundEyelashes = False
            for makeup in iter(makeupModifiers):
                if pdDef.MAKEUP_GROUPS.EYELASHES in makeup.group:
                    foundEyelashes = True
                    break

            if not foundEyelashes:
                self.AddResource(pdDef.DEFAULT_NUDE_EYELASHES, 1.0, factory, privilegedCaller=True)
        bodyModifiers = self.buildDataManager.GetModifiersByPart(pdDef.DOLL_PARTS.BODY)
        EnsureBodyPart(bodyModifiers, 'bottom', pdDef.DEFAULT_NUDE_LEGS)
        EnsureBodyPart(bodyModifiers, pdDef.BODY_CATEGORIES.FEET, pdDef.DEFAULT_NUDE_FEET)
        EnsureBodyPart(bodyModifiers, pdDef.BODY_CATEGORIES.HANDS, pdDef.DEFAULT_NUDE_HANDS)
        EnsureBodyPart(bodyModifiers, 'top', pdDef.DEFAULT_NUDE_TORSO)

    def Load(self, filename, factory):
        self.LoadYaml(filename, factory)

    def LoadYaml(self, filename, factory):
        """
        Loads a doll from the specific filename. 
        Filename must point to a YAML file.
        """
        dna = factory.GetDNAFromYamlFile(filename)
        self.LoadDNA(dna, factory)

    def CreateModifierFromFootPrint(self, factory, footPrint):
        """
        Creates and returns a modifier using the given footPrint.
        A footprint is a data element in a DNA.
        """

        def doDecal(modifier):
            decal = footPrint.get(pdDef.DNA_STRINGS.DECALDATA)
            if decal:
                modifier.decalData = ProjectedDecal.Load(decal)

        pathlower = footPrint[pdDef.DNA_STRINGS.PATH].lower()
        modifier = None
        if not factory.resData.QueryPathByGender(self.gender, pathlower):
            if footPrint.get(pdDef.DNA_STRINGS.DECALDATA):
                modifier = pdDm.BuildData(pathlower)
                modifier.weight = float(footPrint[pdDef.DNA_STRINGS.WEIGHT])
                doDecal(modifier)
        else:
            variation = footPrint.get(pdDef.DNA_STRINGS.VARIATION)
            modifier = self._AddResource(pathlower, footPrint.get(pdDef.DNA_STRINGS.WEIGHT), factory, variation=variation)
            modifier.pattern = footPrint.get(pdDef.DNA_STRINGS.PATTERN, '')
            modifier.tuck = footPrint.get(pdDef.DNA_STRINGS.TUCK, False)
            if isinstance(footPrint.get(pdDef.DNA_STRINGS.COLORS), basestring):
                colorData = eval(footPrint.get(pdDef.DNA_STRINGS.COLORS))
            else:
                colorData = footPrint.get(pdDef.DNA_STRINGS.COLORS)
            colorizeDataSet = False
            if colorData:
                if modifier.pattern:
                    modifier.patternData = colorData
                    if len(modifier.patternData) == 5:
                        modifier.patternData.append((0, 0, 8, 8))
                        modifier.patternData.append(0.0)
                else:
                    modifier.colorizeData = colorData
                    colorizeDataSet = True
            if pdDef.DNA_STRINGS.SPECULARCOLORS in footPrint:
                modifier.specularColorData = footPrint.get(pdDef.DNA_STRINGS.SPECULARCOLORS)
            colorVariation = footPrint.get(pdDef.DNA_STRINGS.COLORVARIATION, '')
            if colorVariation and not (colorVariation == 'default' and colorizeDataSet):
                modifier.SetColorVariation(footPrint[pdDef.DNA_STRINGS.COLORVARIATION])
            doDecal(modifier)
        return modifier

    def SortModifiersForBatchAdding(self, modifiers):

        def BatchAddModifierKey(modifier):
            if modifier.categorie == pdDef.DOLL_EXTRA_PARTS.UTILITYSHAPES:
                return 0
            elif modifier.categorie == pdDef.DOLL_EXTRA_PARTS.DEPENDANTS:
                return 1
            else:
                return 2

        modifiers.sort(key=lambda x: x.categorie)
        modifiers.sort(key=lambda x: BatchAddModifierKey(x))
        return modifiers

    def LoadDNA(self, data, factory, tattoos = None, buildDataManager = None):
        """
        If buildDataManager is passed, data is collected into that variable 
        instead of self.buildDataManager
        """
        self.busyLoadingDNA = True
        if data[0] in pdDef.GENDER:
            self.gender = data[0]
            data = data[1:]
        buildDataManager = buildDataManager or self.buildDataManager
        modifiers = []
        for footPrint in iter(data):
            modifier = self.CreateModifierFromFootPrint(factory, footPrint)
            if modifier:
                modifiers.append(modifier)
                pdCf.BeFrameNice()

        modifiers = self.SortModifiersForBatchAdding(modifiers)
        for modifier in iter(modifiers):
            buildDataManager.AddModifier(modifier)

        self.busyLoadingDNA = False

    def GetDNA(self, preserveTypes = False, getHiddenModifiers = False, getWeightless = False):
        """
        Returns the gender and a minimal representation of the modifiers of this doll.
        That data is a list of dictionary elements that contains string keys and string values.
        [ gender, modifier1, ... modifierN ]
        
        If 'preserveTypes' is set to true, the dictionary elements contains string keys and values
        of the type they originally were in the build data.        
        """
        dna = [self.gender]
        modifiers = self.buildDataManager.GetSortedModifiers(showHidden=getHiddenModifiers)
        for modifier in iter(modifiers):
            ow = self.buildDataManager.GetOcclusionWeight(modifier)
            if getWeightless or ow + modifier.weight > 0.0:
                data = modifier.GetFootPrint(preserveTypes, occlusionWeight=ow)
                dna.append(data)

        return dna

    def MatchDNA(self, factory, dna):
        """
        Matches the DNA of this doll to the given DNA. Afterwards, this doll will have only those
        modifiers that are specified in the given DNA. Therefor, a call to Update directly after MatchDNA
        will ensure that this doll looks exactly the same as the doll from whom we get the DNA.
        """
        self.busyLoadingDNA = True
        if dna[0] in pdDef.GENDER:
            self.gender = dna[0]
            tempDNA = list(dna[1:])
        else:
            tempDNA = list(dna)
        remList = []
        for modifier in self.buildDataManager.GetSortedModifiers():
            found = False
            for footPrint in tempDNA:
                cmpResult = modifier.CompareFootPrint(footPrint)
                if cmpResult != 0:
                    tempDNA.remove(footPrint)
                    found = True
                    if cmpResult == -1:
                        modifier.SetVariation(footPrint.get(pdDef.DNA_STRINGS.VARIATION, ''))
                    break

            if not found:
                remList.append(modifier)

        for modifier in remList:
            self.buildDataManager.RemoveModifier(modifier)

        modifiers = []
        for footPrint in tempDNA:
            modifier = self.CreateModifierFromFootPrint(factory, footPrint)
            if modifier:
                modifiers.append(modifier)

        modifiers = self.SortModifiersForBatchAdding(modifiers)
        for modifier in iter(modifiers):
            self.buildDataManager.AddModifier(modifier)

        self.busyLoadingDNA = False

    def Save(self, filename):
        """
        Saves out the dna of the doll using YAML.
        To get the DNA as a string without saving it, call GetDNA().
        """
        f = file(filename, 'w')
        dnaData = self.GetDNA()
        yaml.dump(dnaData, f, default_flow_style=False)
        f.close()

    def GetBuildDataManager(self):
        return self.buildDataManager

    def GetBuildDataByCategory(self, category, coalesceToPart = True):
        modifiers = self.buildDataManager.GetModifiersByCategory(category)
        if coalesceToPart and not modifiers:
            if category in pdDef.DOLL_PARTS + pdDef.DOLL_EXTRA_PARTS:
                modifiers = self.buildDataManager.GetModifiersByPart(category)
        return modifiers

    def GetBuildDataByResPath(self, resPath, includeFuture = False):
        return self.buildDataManager.GetModifierByResPath(resPath, includeFuture=includeFuture)

    def _AddResource(self, res, weight, factory, colorization = None, variation = None, colorVariation = None, privilegedCaller = False, rawColorVariation = None):
        """
        Handles adding a new resource, converting it to a modifier and thus finally adding
        that modifier instance to the Doll's BuildDataManager instance.
        """
        parts = res.split(pdDef.SEPERATOR_CHAR)
        if len(parts) == 1:
            raise Exception('Can not add a whole category to the character')
        pdCf.BeFrameNice()
        modifier = None
        removedModifiers = self.buildDataManager.GetDirtyModifiers(removedBit=True)
        for removedModifier in iter(removedModifiers):
            if removedModifier.respath == res:
                removedModifier.weight = weight
                removedModifier.dependantModifiers = {}
                modifier = removedModifier
                break

        modifier = factory.CollectBuildData(self.gender, res, weight)
        categorie = modifier.categorie
        l1rModifier = None
        if modifier.metaData.lod1Replacement:
            modifier.lodCutoff = pdDef.LOD_0
            l1rModifier = self._AddResource(modifier.metaData.lod1Replacement, 1.0, factory, privilegedCaller=privilegedCaller)
            l1rModifier.lodCutoff = pdDef.LOD_99
            l1rModifier.lodCutin = pdDef.LOD_1
            self.buildDataManager.HideModifier(l1rModifier)
        if modifier.metaData.lod2Replacement:
            if l1rModifier:
                l1rModifier.lodCutoff = pdDef.LOD_1
            else:
                modifier.lodCutoff = pdDef.LOD_1
            l2rModifier = self._AddResource(modifier.metaData.lod2Replacement, 1.0, factory, privilegedCaller=privilegedCaller)
            l2rModifier.lodCutoff = pdDef.LOD_99
            l2rModifier.lodCutin = pdDef.LOD_2
            self.buildDataManager.HideModifier(l2rModifier)
        self.ApplyVariationsToModifier(modifier, colorization, variation, colorVariation, rawColorVariation=rawColorVariation)
        dependantModifiersFullData = modifier.GetDependantModifiersFullData()
        if dependantModifiersFullData:
            for parsedValues in iter(dependantModifiersFullData):
                dependantModifier = self._AddResource(parsedValues[0], parsedValues[3], factory, variation=parsedValues[2], colorVariation=parsedValues[1], privilegedCaller=privilegedCaller)
                modifier.AddDependantModifier(dependantModifier)

        if categorie in [pdDef.DOLL_PARTS.HAIR]:
            if categorie == pdDef.DOLL_PARTS.HAIR:
                hairModifiers = self.buildDataManager.GetModifiersByCategory(categorie)
                if hairModifiers:
                    modifier.colorizeData = hairModifiers[0].colorizeData
                elif self.hairColorizeData:
                    modifier.colorizeData = self.hairColorizeData
            self.buildDataManager.SetModifiersByCategory(categorie, [modifier], privilegedCaller=privilegedCaller)
        else:
            self.buildDataManager.AddModifier(modifier, privilegedCaller=privilegedCaller)
        return modifier

    def SetItemType(self, factory, itemType, weight = 1.0, rawColorVariation = None):
        """
        Forcefully sets this itemtype on the doll, clearing out any exisiting items that are on the doll 
        for the category this item belongs to
        """
        if type(itemType) is not tuple:
            item = factory.GetItemType(itemType, gender=self.gender)
        if item is None:
            log.LogError('Unable to Set Item type:', itemType, 'on doll')
            return
        self.RemoveResource(item[0], factory)
        return self.AddItemType(factory, item, weight, rawColorVariation)

    def AddItemType(self, factory, itemType, weight = 1.0, rawColorVariation = None):
        """
        Supports adding preauthored ItemTypes (often called Types).
        "itemType" is either a 3 element tuple or a resource path pointing to the .type file
        
        ItemType maps modifier to variation and colorVariation, both of which can be None.
        These are preauthored combinations that simplify item definition for external consumers of
        the paperDoll.
        """
        if type(itemType) is not tuple:
            itemType = factory.GetItemType(itemType, gender=self.gender)
        if type(itemType) is tuple:
            return self.AddResource(itemType[0], weight, factory, variation=itemType[1], colorVariation=itemType[2], rawColorVariation=rawColorVariation)

    def ApplyVariationsToModifier(self, modifier, colorization = None, variation = None, colorVariation = None, rawColorVariation = None):
        if colorization is not None:
            modifier.SetColorizeData(colorization)
        if variation is not None:
            modifier.SetVariation(variation)
        if colorVariation is not None:
            modifier.SetColorVariation(colorVariation)
        if rawColorVariation is not None:
            if colorVariation:
                log.LogWarn('paperDoll::Doll:: ApplyVariationsToModifier: applying both colorVariation and rawColorVariation')
            modifier.SetColorVariationDirectly(rawColorVariation)

    def AddResource(self, res, weight, factory, colorization = None, variation = None, colorVariation = None, privilegedCaller = False, rawColorVariation = None):
        """
        Adds a resource to the doll. The resource ends up as a modifier (an instance of BuildData) in the doll's buildDataManager.
        'res' is either a path in res:/ or an instance of ProjectedDecals, in which case a modifier instance is created that will contain the decal.
        'weight' is a numerical number between 0 and 1. Passing 0 will effectively ignore the addition of the resource.
        'factory' is the Factory instance used to load up and gather associated data with the given resource in 'res'.        
        If colorization is passed, it must be tuple of 3 elements.
        'privilegedCaller' is used for internal purposes only. Do not call with True.
        """
        modifier = None
        if type(res) is ProjectedDecal:
            decalName = res.label or 'Decal {0}'.format(res.layer)
            modifier = pdDm.BuildData(name=decalName, categorie=pdDef.BODY_CATEGORIES.TATTOO)
            modifier.decalData = res
            self.ApplyVariationsToModifier(modifier, colorization, variation, colorVariation)
            self.buildDataManager.AddModifier(modifier, privilegedCaller=privilegedCaller)
        else:
            modifier = self._AddResource(res, weight, factory, colorization=colorization, variation=variation, colorVariation=colorVariation, privilegedCaller=privilegedCaller, rawColorVariation=rawColorVariation)
        return modifier

    def AddResources(self, resList, weight, factory):
        for each in iter(resList):
            self.AddResource(each, weight, factory)

    def RemoveResource(self, res, factory, privilegedCaller = False):
        """
        Removes the resource in 'res' from the doll.
        'privilegedCaller' is used for internal purposes only. Do not call with True.
        """
        parts = res.split(pdDef.SEPERATOR_CHAR)
        if len(parts) == 1:
            raise Exception('Can not remove a whole category from the character')
        categorie = str(parts[0].lower())
        modifiers = self.buildDataManager.GetModifiersByCategory(categorie, showHidden=True)
        targetFun = lambda modifier: str(modifier.respath.lower()) == str(res.lower())
        target = None
        for modifier in modifiers:
            if targetFun(modifier):
                target = modifier
                break

        if target:
            self.buildDataManager.RemoveModifier(target, privilegedCaller=privilegedCaller)
        return target

    def HandleChangedDependencies(self, factory):
        changedModifiers = self.buildDataManager.GetDirtyModifiers(changedBit=True)
        for modifier in iter(changedModifiers):
            self.buildDataManager.ReverseOccludeModifiersByModifier(modifier, modifier.lastVariation)
            self.buildDataManager.OccludeModifiersByModifier(modifier)
            resPaths = modifier.GetDependantModifierResPaths() or []
            for dependantModifier in iter(modifier.GetDependantModifiers()):
                if dependantModifier.respath not in resPaths:
                    modifier.RemoveDependantModifier(dependantModifier)
                    self.buildDataManager.RemoveParentModifier(modifier, dependantModifier)
                    self.buildDataManager.RemoveModifier(dependantModifier, privilegedCaller=True)
                else:
                    resPaths.remove(dependantModifier.respath)

            if resPaths:
                dependantModifiersFullData = modifier.GetDependantModifiersFullData()
                for entry in dependantModifiersFullData:
                    if entry[0] in resPaths:
                        dependantModifier = self._AddResource(entry[0], entry[3], factory, variation=entry[2], colorVariation=entry[3], privilegedCaller=True)
                        modifier.AddDependantModifier(dependantModifier)
                        self.buildDataManager.AddParentModifier(dependantModifier, modifier)

    def QueryModifiers(self, modifierList, fun):
        """
        Runs fun which is a function pointer that must return True or False
        for each modifier in 'modifierList'
        Returns True if fun is True for all modifiers, otherwise, returns false.
        """
        return all(map(fun, modifierList))

    def SpawnUpdateChildTasklet(self, fun, *args):
        """
        Spawns a tasklet as a children of the update tasklet and schedules it immediatly.
        """
        t = uthread.new(fun, *args)
        t.context = 'paperDoll::Doll::Update'
        uthread.schedule(t)
        self._UpdateTaskletChildren.append(t)

    def ReapUpdateChildTasklets(self):
        try:
            for t in self._UpdateTaskletChildren:
                if t:
                    t.kill()

        finally:
            del self._UpdateTaskletChildren[:]

    def _DelayedUpdateCall(self, factory, avatar, visualModel, LODMode, channel = None):
        self.hasDelayedUpdateCallPending = True
        pdCf.Yield()
        while self._currentUpdateTasklet and self._currentUpdateTasklet.alive:
            pdCf.Yield()

        self.hasDelayedUpdateCallPending = False
        self.Update(factory, avatar, visualModel, LODMode, channel=channel)

    def Update(self, factory, avatar = None, visualModel = None, LODMode = False, channel = None):
        """
        Applies the changes that have been done to this Doll to the avatar and visualModel.
        Tries to do the least amount of changes required since Update was last called.
        
        Starts a new tasklet, killing any previous tasklet that hasn't finished.
        
        This is safe (though not desirable) to call multiple times per frame.
        
        Returns nothing
        """
        currentFrame = trinity.GetCurrentFrameCounter()
        statistics.updateCount.Inc()
        if self.hasDelayedUpdateCallPending:
            return
        if self.__updateFrameStamp == currentFrame:
            log.LogWarn('paperDoll::Doll::Update is being called more than once on the same frame for the same doll instance! Fix your code so you only call Update after all needed changes have been applied.')
            return
        if self._currentUpdateTasklet and self._currentUpdateTasklet.alive and self.__updateFrameStamp < currentFrame:
            self.KillUpdate()
            if not self.hasDelayedUpdateCallPending:
                uthread.new(self._DelayedUpdateCall, factory, avatar, visualModel, LODMode, channel=channel)
            return
        self.__updateFrameStamp = currentFrame
        self._currentUpdateTasklet = uthread.new(self.Update_t, *(factory,
         avatar,
         visualModel,
         channel))
        self._currentUpdateTasklet.context = 'paperDoll::Doll::Update'
        if blue.os.GetWallclockTimeNow() - blue.os.GetWallclockTime() < 50000:
            uthread.schedule(self._currentUpdateTasklet)

    def KillUpdate(self):
        """
        Kills the current Update tasklet.
        """
        if self._currentUpdateTasklet and self._currentUpdateTasklet.alive:
            self._currentUpdateTasklet.raise_exception(TaskletExit, 'Preemptively killing Update')

    def IsBusyUpdating(self):
        return self._currentUpdateTasklet and self._currentUpdateTasklet.alive

    def Update_t(self, factory, avatar, visualModel, channel = None):
        """
        !Notice that this makes it dangerous to re-use a doll instance to update two different 
        avatars/visual models, since only the deltas in changes are applied!
        
        If only visualModel is passed, no updates will be done to simulated cloth.
        If only avatar is passed, an attempt is done to get its visualModel.
        This complication is due to the LODding system.
        
        Returns nothing and should never do so.
        """
        updateRuleBundle = UpdateRuleBundle()
        sTime = blue.os.GetTime()
        buildDataManager = self.buildDataManager
        try:
            while self.busyLoadingDNA or not factory.IsLoaded:
                pdCf.Yield()

            LODMode = self.previousLOD != self.currentLOD
            buildDataManager.Lock()
            if LODMode:
                pdCf.Yield()
            else:
                pdCf.BeFrameNice()
            if avatar and hasattr(avatar, 'visualModel') and not visualModel:
                visualModel = avatar.visualModel
            AddMarker('Update Start')
            self.renderDriver.OnBeginUpdate(self)
            if pdCfg.PerformanceOptions.EnsureCompleteBody:
                self._EnsureCompleteBody(factory)
            self.HandleChangedDependencies(factory)
            buildDataManager.ApplyLimitsToModifierWeights()
            gdm = buildDataManager.GetDirtyModifiers
            addedModifiers = gdm(addedBit=True, getWeightless=False)
            removedModifiers = gdm(removedBit=True) if self.hasUpdatedOnce else []
            changedModifiers = gdm(changedBit=True) if self.hasUpdatedOnce else []
            if self.hasUpdatedOnce:
                dirtyModifiers = removedModifiers + addedModifiers + changedModifiers
                addedAndChangedModifiers = addedModifiers + changedModifiers
            else:
                dirtyModifiers = addedModifiers
                addedAndChangedModifiers = addedModifiers
            if not dirtyModifiers and self.mapBundle.AllMapsGood():
                raise RedundantUpdateException('Warning - Call made to PaperDoll.Update() when no modifier is dirty!')
            pdCf.BeFrameNice()
            self._AnalyzeBuildDataForRules(updateRuleBundle, buildDataManager)
            updateRuleBundle.DiscoverState(dirtyModifiers, avatar)
            if not (updateRuleBundle.blendShapesOnly or updateRuleBundle.decalsOnly):
                self._ProcessRules(factory, buildDataManager, addedAndChangedModifiers, updateRuleBundle, factory.clothSimulationActive)
                self.ApplyBoneOffsets()
            updateRuleBundle.meshesChanged = not self.hasUpdatedOnce or any((modifier for modifier in addedAndChangedModifiers if modifier.IsMeshContainingModifier() and (modifier.IsMeshDirty() or modifier.HasWeightPulse()))) or any((modifier.IsMeshContainingModifier() for modifier in removedModifiers))
            if not updateRuleBundle.blendShapesOnly and updateRuleBundle.meshesChanged and avatar:
                factory.CreateAnimationOffsets(avatar, self)
            if updateRuleBundle.doDecals:
                self.BakeDecals_t(factory, updateRuleBundle.dirtyDecalModifiers)
            if updateRuleBundle.doBlendShapes and not updateRuleBundle.meshesChanged:
                self._HandleBlendShapes(removedModifiers)
            if factory.clothSimulationActive and avatar and updateRuleBundle.meshesChanged:
                self.LoadClothData(addedAndChangedModifiers)
            if self.currentLOD <= pdDef.LOD_SKIN:
                hashStubble = pdPor.PortraitTools.GetStubbleHash(addedAndChangedModifiers)
            else:
                hashStubble = None
            if updateRuleBundle.meshesChanged:
                self.__ApplyUVs()
            if visualModel and (self.currentLOD <= self.previousLOD or not self.mapBundle.AllMapsGood()):
                textureCompositingStartTime = blue.os.GetTime()
                if self.hasUpdatedOnce and self.mapBundle.AllMapsGood():
                    updateRuleBundle.partsToComposite = buildDataManager.GetPartsFromMaps(dirtyModifiers)
                self.WaitForChildTaskletsToFinish()
                if self.hasUpdatedOnce and self.mapBundle.AllMapsGood():
                    updateRuleBundle.mapsToComposite = buildDataManager.GetMapsToComposite(dirtyModifiers)
                if buildDataManager.desiredOrderChanged:
                    if (self.mapBundle.AllMapsGood() or updateRuleBundle.partsToComposite) and pdDef.DOLL_PARTS.BODY not in updateRuleBundle.partsToComposite:
                        updateRuleBundle.partsToComposite.append(pdDef.DOLL_PARTS.BODY)
                    updateRuleBundle.mapsToComposite = list(pdDef.MAPS)
                blendShapeVector = [ modifier.weight for modifier in buildDataManager.GetModifiersAsList() if modifier.IsBlendshapeModifier() and modifier.weight != 0.0 ]
                hES = (self.compressionSettings, hashStubble, blendShapeVector)
                hashKey = buildDataManager.HashForMaps(hashableElements=hES)
                mapsTypesComposited = self.CompositeTextures(factory, hashKey, updateRuleBundle)
                if updateRuleBundle.videoMemoryFailure:
                    raise OutOfVideoMemoryException('Out of video memory!')
                if not updateRuleBundle.blendShapesOnly:
                    self.WaitForTexturesToComposite(factory, hashKey, mapsTypesComposited, textureCompositingStartTime)
                else:
                    timeCompositedSec = statistics.GetTimeDiffInSeconds(textureCompositingStartTime)
                    statistics.compositeTime.Add(timeCompositedSec)
            compSet = self.compressionSettings if self.compressionSettings is not None else factory
            self.useDXT5N = compSet and compSet.compressTextures and compSet.AllowCompress(pdDef.NORMAL_MAP) and not blue.win32.IsTransgaming()
            meshes = buildDataManager.GetMeshes(includeClothMeshes=factory.clothSimulationActive)
            if updateRuleBundle.meshesChanged:
                self._HandleBlendShapes(removedModifiers)
            self.WaitForChildTaskletsToFinish()
            if updateRuleBundle.meshesChanged:
                self.ConfigureMaskedShader(updateRuleBundle)
                self.renderDriver.ApplyShaders(self, meshes)
                if visualModel:
                    factory.RemoveMeshesFromVisualModel(visualModel)
                if visualModel:
                    factory.AppendMeshesToVisualModel(visualModel, meshes)
                    visualModel.ResetAnimationBindings()
                if avatar and avatar.clothMeshes is not None:
                    if len(avatar.clothMeshes) > 0:
                        del avatar.clothMeshes[:]
                    if factory.clothSimulationActive:
                        for mesh in iter(meshes):
                            if type(mesh) is trinity.Tr2ClothingActor:
                                avatar.clothMeshes.append(mesh)

            Factory.BindMapsToMeshes(meshes, self.mapBundle, self.usePrepass)
            if avatar and self.usePrepass:
                avatar.BindLowLevelShaders()
            if self.currentLOD == pdDef.LOD_SCATTER_SKIN and SkinSpotLightShadows.instance is not None:
                SkinSpotLightShadows.instance.RefreshLights()
            if self.currentLOD <= pdDef.LOD_SKIN and updateRuleBundle.doStubble:

                def doStubble():
                    pdPor.PortraitTools.HandleRemovedStubble(removedModifiers, buildDataManager)
                    pdPor.PortraitTools.HandleUpdatedStubble(addedAndChangedModifiers, buildDataManager)
                    factory.RebindAnimations(avatar, visualModel)

                self.SpawnUpdateChildTasklet(doStubble)
            self.renderDriver.OnFinalizeAvatar(visualModel, avatar, updateRuleBundle, self, factory)
            self.previousLOD = self.currentLOD
            self.WaitForChildTaskletsToFinish()
            self.renderDriver.OnEndUpdate(avatar, visualModel, self, factory)
            factory.RebindAnimations(avatar, visualModel)
            if avatar:
                freq = pdCfg.PerformanceOptions.updateFreq.get(self.overrideLod, 0)
                if freq == 0:
                    avatar.updatePeriod = 0
                else:
                    avatar.updatePeriod = 1.0 / freq
            if self.currentLOD == pdDef.LOD_SCATTER_SKIN and self.skinLightmapRenderer is None:
                self.skinLightmapRenderer = SkinLightmapRenderer()
                self.skinLightmapRenderer.SetSkinnedObject(avatar)
                self.skinLightmapRenderer.StartRendering()
            elif self.skinLightmapRenderer is not None and visualModel and avatar and not LODMode:
                self.skinLightmapRenderer.SetSkinnedObject(avatar)
            buildDataManager.NotifyUpdate()
            self.lastUpdateRedundant = False
            self.hasUpdatedOnce = True
        except RedundantUpdateException as err:
            self.lastUpdateRedundant = True
            sys.exc_clear()
        except TaskletExit as err:
            self.lastUpdateRedundant = True
            raise
        except OutOfVideoMemoryException as err:
            self.lastUpdateRedundant = True
            log.LogException(str(err))
            newSize = map(lambda x: x / 2, self.mapBundle.baseResolution)
            shadow = SkinSpotLightShadows.instance
            if shadow and shadow.GetShadowMapResolution() > newSize[0]:
                shadow.SetShadowMapResolution(shadow.GetShadowMapResolution() / 2)
            self.hasUpdatedOnce = False
            self.SetTextureSize(newSize)
        except Exception as err:
            log.LogException(str(err))
            sys.exc_clear()
        finally:
            self.ReapUpdateChildTasklets()
            buildDataManager.UnLock()
            timeUpdatingSec = statistics.GetTimeDiffInSeconds(sTime)
            statistics.updateTime.Add(timeUpdatingSec)
            if not updateRuleBundle.videoMemoryFailure:
                uthread.new(self.NotifyUpdateDoneListeners_t)
            self._currentUpdateTasklet = None
            if updateRuleBundle.videoMemoryFailure:
                uthread.new(self.Update, factory, avatar, visualModel)
            AddMarker('End Start')
            if channel is not None:
                channel.send(None)

    def NotifyUpdateDoneListeners_t(self):
        """
        This code is executed within a tasklet after each call to Update.
        """
        for listener in self.onUpdateDoneListeners:
            uthread.new(listener)

    def AddUpdateDoneListener(self, callBack):
        """
        callBack must be a zero argument function that will be called everytime this doll has done updating.
        """
        if callBack not in self.onUpdateDoneListeners:
            self.onUpdateDoneListeners.append(callBack)

    def WaitForChildTaskletsToFinish(self):
        pdCf.WaitForAll(self._UpdateTaskletChildren, lambda x: x.alive)

    def WaitForTexturesToComposite(self, factory, hashKey, mapsTypesComposited, textureCompositingStartTime):
        self.WaitForChildTaskletsToFinish()
        statistics.mapsComposited.Add(len(mapsTypesComposited))
        if factory.allowTextureCache and mapsTypesComposited:
            mapsToSave = [ self.mapBundle[mapType] for mapType in mapsTypesComposited if self.mapBundle[mapType] is not None and self.mapBundle[mapType].isGood ]
            uthread.new(pdDm.SaveMapsToDisk, hashKey, mapsToSave)
        timeCompositedSec = statistics.GetTimeDiffInSeconds(textureCompositingStartTime)
        statistics.compositeTime.Add(timeCompositedSec)

    def ConfigureMaskedShader(self, updateRuleBundle):
        if self.useMaskedShaders or updateRuleBundle.undoMaskedShaders:
            applicableModifiers = (modifier for modifier in self.buildDataManager.GetModifiersAsList() if modifier.categorie in pdDef.MASKING_CATEGORIES)
            for modifier in applicableModifiers:
                for mesh in iter(modifier.meshes):
                    self.ConfigureMeshForMaskedShader(mesh, remove=updateRuleBundle.undoMaskedShaders)

    def ConfigureMeshForMaskedShader(self, mesh, remove = False):
        decalToOpaque = []
        fx = pdCcf.GetEffectsFromAreaList(mesh.opaqueAreas)
        for f in iter(fx):
            for p in f.parameters:
                if p.name == 'CutMaskInfluence':
                    p.value = 0.85

        for decalArea in mesh.decalAreas:
            f = decalArea.effect
            if f is None:
                continue
            for p in f.parameters:
                if p.name == 'CutMaskInfluence':
                    if remove:
                        if abs(p.value - 0.85) < 0.001:
                            decalToOpaque.append(decalArea)
                        p.value = 0.0
                    elif abs(p.value - 0.85) > 0.001:
                        p.value = 1.01

        if remove:
            for area in decalToOpaque:
                mesh.opaqueAreas.append(area)
                mesh.decalAreas.remove(area)

        else:
            pdCcf.MoveAreas(mesh.opaqueAreas, mesh.decalAreas)
        for transparentArea in mesh.transparentAreas:
            f = transparentArea.effect
            if f is None:
                continue
            for p in f.parameters:
                if p.name == 'CutMaskInfluence':
                    p.value = 1.0

    def BakeDecals_t(self, factory, decalModifiers):
        if decalModifiers:
            createTargetAvatar = False
            if self.decalBaker is None:
                createTargetAvatar = True
                self.decalBaker = DecalBaker(factory)
            elif not self.decalBaker.HasAvatar():
                createTargetAvatar = True
            self.decalBaker.Initialize()
            if createTargetAvatar:
                self.decalBaker.CreateTargetAvatarFromDoll(self)
                self._UpdateTaskletChildren.append(self.decalBaker.avatarShaderSettingTasklet)
            self.decalBaker.SetSize(self.textureResolution)
            for decalModifier in decalModifiers:
                try:
                    decalModifier.IsDirty = True
                    try:
                        self.decalBaker.BakeDecalToModifier(decalModifier.decalData, decalModifier)
                    except TypeError:
                        return
                    finally:
                        self._UpdateTaskletChildren.append(self.decalBaker.decalSettingTasklet)
                        self._UpdateTaskletChildren.append(self.decalBaker.bakingTasklet)

                    while not self.decalBaker.isReady:
                        pdCf.Yield()

                    decalModifier.mapL.update(decalModifier.mapD)
                    decalModifier.colorize = True
                except TaskletExit:
                    decalModifier.IsDirty = True
                    raise

    def LogDNA(self, factory):
        """
        Checks if the paperdoll is verbose and logs to the logserver
        if it is so.
        """
        if factory.verbose:
            lines = yaml.dump(self.GetDNA(), default_flow_style=False).splitlines()
            log.LogInfo('Building paperDoll: ' + self.name)
            for each in iter(lines):
                log.LogInfo(each)

    def CompositeTextures(self, factory, hashKey, updateRuleBundle):
        """
        Composites new set of textures and puts them into self.mapBundle
        Depending on the updateRuleBundle, any possible permutation of the set of maps defined in pdDef.MAPS
        are composited.
        """
        if not updateRuleBundle.blendShapesOnly and factory.allowTextureCache:
            textureCache = {}
            mapCount = len(pdDef.MAPS)
            for i in xrange(mapCount):
                tex = pdDm.FindCachedMap(hashKey, self.mapBundle.GetResolutionByMapType(i)[0], pdDef.MAPS[i])
                if tex:
                    tex.Reload()
                textureCache[i] = tex

            pdCf.WaitForAll(textureCache.values(), lambda x: x is not None and x.isLoading)
            for i in xrange(mapCount):
                if textureCache.get(i) and textureCache[i].isGood:
                    self.mapBundle.SetMapByTypeIndex(i, textureCache[i], hashKey)

        if self.compressionSettings is not None:
            self.compressionSettings.generateMipmap = False
        mapsTypesComposited = []
        for mapTypeIndex in updateRuleBundle.mapsToComposite:
            existingMap = self.mapBundle[mapTypeIndex]
            if existingMap and existingMap.isGood and hashKey == self.mapBundle.hashKeys.get(mapTypeIndex):
                continue
            else:
                mapsTypesComposited.append(mapTypeIndex)

        def CompositeTasklet_t(mapTypeIndex, copyToExistingTexture):
            """
            This tasklet composites all maps that need to be composited
            in a sequence
            """
            textureCompositor = tc.TextureCompositor(resData=factory.resData)
            pdCf.BeFrameNice()
            texture = None
            try:
                texture = factory.CompositeCombinedTexture(mapTypeIndex, self.gender, self.buildDataManager, self.mapBundle, textureCompositor, self.compressionSettings, partsToComposite=updateRuleBundle.partsToComposite, copyToExistingTexture=copyToExistingTexture, lod=self.currentLOD)
            except (trinity.E_OUTOFMEMORY, trinity.D3DERR_OUTOFVIDEOMEMORY):
                updateRuleBundle.videoMemoryFailure = True
                sys.exc_clear()

            if texture:
                self.mapBundle.SetMapByTypeIndex(mapTypeIndex, texture, hashKey)

        copyToExistingTexture = len(mapsTypesComposited) == 1 and not updateRuleBundle.meshesChanged
        for mapTypeIndex in mapsTypesComposited:
            self.SpawnUpdateChildTasklet(CompositeTasklet_t, mapTypeIndex, copyToExistingTexture)

        return mapsTypesComposited

    def LoadBindPose(self):
        """
        Loads the appropriate bind pose for wrinkle controls, etc.
        """
        filename = 'res:/Graphics/Character/Global/FaceSetup/BaseFemaleBindPose.yaml'
        if self.gender == pdDef.GENDER.MALE:
            filename = 'res:/Graphics/Character/Global/FaceSetup/BaseMaleBindPose.yaml'
        self.bindPose = pdDm.LoadYamlFileNicely(filename)

    def LoadClothData(self, modifierList):
        """
        Loads clothmeshes for each modifier in 'modifierList'.
        Returns a list of those clothmeshes.
        """
        clothMeshes = []
        clothModifierGenerator = (modifier for modifier in modifierList if modifier.clothPath and not modifier.clothData)
        for modifier in clothModifierGenerator:
            clothLoadPath = modifier.clothPath
            if not clothLoadPath:
                modifier.clothData = None
                continue
            if clothLoadPath:
                clothData = blue.resMan.LoadObject(clothLoadPath)
                if clothData and type(clothData) == trinity.Tr2ClothingActor:
                    clothData.name = modifier.name
                    clothMeshes.append(clothData)
                else:
                    clothData = None
                modifier.clothData = clothData

        pdCf.WaitForAll(clothMeshes, lambda x: x.clothingRes.isLoading)
        return clothMeshes

    def SetTextureSize(self, *args):
        """
        Sets the texture size for this doll.
        As a side-effect, all modifiers are marked dirty, since everything
        needs to become recomposited on next Update call.
        """
        if type(args[0]) in (list, tuple):
            x, y = args[0][:2]
        else:
            x, y = args
        if self.skinLightmapRenderer is not None:
            self.skinLightmapRenderer.Refresh()
        oldX, oldY = self.mapBundle.baseResolution
        self.mapBundle.SetBaseResolution(x, y)
        self.mapBundle.ReCreate(includeFixedSizeMaps=False)
        for modifier in self.buildDataManager.GetModifiersAsList():
            if modifier.IsTextureContainingModifier() and not modifier.IsDirty:
                modifier.IsDirty = True

    def getbusyUpdating(self):
        return self._currentUpdateTasklet is not None or any(map(lambda x: x.alive, self._UpdateTaskletChildren))

    busyUpdating = property(fget=lambda self: self.getbusyUpdating())

    def setoverrideLod(self, newLod, affectTextureSize = True):
        """
        Setting a new LOD marks all modifiers as dirty.
        """
        oldLod = self.currentLOD
        self.currentLOD = newLod
        self.previousLOD = oldLod
        self.buildDataManager.SetLOD(newLod)
        if oldLod == pdDef.LOD_SKIN and newLod == pdDef.LOD_SCATTER_SKIN:
            self.buildDataManager.SetAllAsDirty()
            return
        if oldLod == pdDef.LOD_SCATTER_SKIN and newLod >= pdDef.LOD_SKIN:
            self.skinLightmapRenderer = None
            if newLod == pdDef.LOD_SKIN:
                return
        if self.gender == pdDef.GENDER.MALE:
            for bm in self.buildDataManager.GetModifiersByCategory(pdDef.HAIR_CATEGORIES.BEARD):
                bm.IsDirty = True

        for modifier in self.buildDataManager.GetModifiersAsList():
            if modifier.IsMeshContainingModifier():
                modifier.IsDirty = True
                del modifier.meshes[:]
                modifier.meshGeometryResPaths = {}

        if affectTextureSize and newLod >= 0 and newLod < len(pdCfg.PerformanceOptions.lodTextureSizes):
            self.SetTextureSize(*pdCfg.PerformanceOptions.lodTextureSizes[newLod])

    overrideLod = property(fget=lambda self: self.currentLOD, fset=setoverrideLod)
    textureResolution = property(fget=lambda self: self.mapBundle.baseResolution, fset=SetTextureSize)

    def setusefastshader(self, value):
        """
        Enable or disable the use of 'fast' shaders, cutting corners.
        """
        if self.__useFastShader != value:
            self.__useFastShader = value
            self.buildDataManager.SetAllAsDirty(clearMeshes=True)

    useFastShader = property(fget=lambda self: self.__useFastShader, fset=setusefastshader)
