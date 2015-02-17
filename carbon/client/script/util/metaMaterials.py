#Embedded file name: carbon/client/script/util\metaMaterials.py
"""
Implementation of various functions relating to MaterialRes
"""
import blue
import yaml
import trinity
import log
import os
METASHADER_PATH = 'res:/Graphics/Shaders/MetashaderLibrary.yaml'
TEXPACKS_PATH = 'res:/Graphics/Shaders/Texpacks/'
_gMetaShaderLibrary = None
_gMetaShaderPacking = None
ENABLE_P4 = True

class MetaMaterialParam:
    """
    This class adds a bit more metadata to enumerated shader parameters,
    by binding the current value along with an appropriate default value, as well
    as the shader description.
    """

    def __init__(self, name, desc, default, value):
        self.name = name
        self.value = value
        self.default = default
        self.desc = desc


def FindAreaResByMeshAndIndex(materialRes, mesh, areaIdx):
    """
    Given a mesh and a GrannyArea index within the mesh,
    return the Tr2MaterialArea from the Tr2MaterialRes
    """
    geo = mesh.geometry
    meshName = mesh.name
    areaName = geo.GetMeshAreaName(mesh.meshIndex, areaIdx)
    if not materialRes:
        return None
    try:
        meshRes = materialRes.meshes[meshName]
    except KeyError:
        log.LogWarn('KeyError! Missing mesh %s in materialRes' % meshName)
        return None

    try:
        areaRes = meshRes.areas[areaName]
    except KeyError:
        log.LogWarn('KeyError! Missing area %s in meshRes %s' % (areaName, meshName))
        return None

    return areaRes


def ApplyMaterialStoreToEffect(effect, materialStore):
    """
    Given a Tr2ShaderMaterial and an areaRes, apply the contents of the areares to the Tr2ShaderMaterial.
    """
    params = effect.highLevelShader.parameterDescriptions
    for p in params:
        try:
            value = materialStore.FindParameter(p.parameterName)
            if value:
                effect.parameters[p.parameterName] = value.CopyTo()
        except TypeError:
            print '   Type Error copying %s in effect %s' % (p, effect.name)
            continue
        except KeyError:
            continue


class MaterialApplier:
    """
    This class is used to defer application of metamaterials
    """

    def __init__(self, mesh, materialRes):
        self.mesh = mesh
        self.materialRes = materialRes

    def Apply(self):
        geo = self.mesh.geometry
        meshIdx = self.mesh.meshIndex
        meshName = self.mesh.name
        try:
            meshRes = self.materialRes.meshes[meshName]
        except KeyError:
            log.LogWarn('===== Did not find mesh %s in materialRes!' % meshName)
            return

        for areaIdx in xrange(geo.GetMeshAreaCount(meshIdx)):
            areaName = geo.GetMeshAreaName(meshIdx, areaIdx)
            try:
                areaRes = meshRes.areas[areaName]
            except KeyError:
                log.LogWarn('===== Did not find area %s in materialRes!' % areaName)
                continue

            ApplyAreaRes(areaRes, self.mesh, areaIdx)


def LoadMaterialRes(resPath, initialize = False):
    materialRes = None
    if resPath:
        if not initialize:
            materialRes = blue.resMan.LoadObjectWithoutInitialize(resPath)
        else:
            materialRes = trinity.Load(resPath, nonCached=True)
        if materialRes is None:
            log.LogError('Could not load material library from path:', resPath)
    return materialRes


def LoadMaterialResFromObject(ob, initialize = False):
    """
    Loads an existing material res from disk if it exists,
    based on the res path of the supplied object
    """
    materialRes = None
    resPath = GetResPath(ob)
    path = None
    if resPath:
        path = GetMaterialPathFromGeometryPath(resPath)
    if path is not None:
        if not initialize:
            materialRes = blue.resMan.LoadObjectWithoutInitialize(path)
        else:
            materialRes = trinity.Load(path, nonCached=True)
    return materialRes


def ApplyMaterialRes(ob, materialRes):
    """
    Applies an existing material res to an object
    """
    if materialRes == None:
        return
    meshList = GetMeshList(ob)
    for mesh in meshList:
        try:
            meshRes = materialRes.meshes[mesh.name]
        except KeyError:
            log.LogWarn('===== Did not find mesh %s in materialRes!' % mesh.name)
            continue

        if mesh.geometry is None:
            continue
        if mesh.geometry.isLoading or not mesh.geometry.isPrepared or not mesh.geometry.isGood:
            mesh.AddGeometryPreparedCallback(MaterialApplier(mesh, materialRes).Apply)
        else:
            MaterialApplier(mesh, materialRes).Apply()

    BindObjectShaders(ob)


def LoadAndApplyMaterialRes(ob, materialRes = None, initialize = False):
    """
    Given an object and optionally an existing material res,
    this function will attempt to use the existing materialRes
    (if available), or else it will try and load the appropriate
    material res (if it exists), or else it will create a new one.
    
    The materialRes that was ultimately applied is the return value.
    """
    if materialRes is None:
        materialRes = LoadMaterialResFromObject(ob, initialize)
    if materialRes is None:
        materialRes = CreateMaterialResFromAreas(ob, '')
        return materialRes
    if materialRes is None:
        return
    ApplyMaterialRes(ob, materialRes)
    return materialRes


def SerializeMaterialStore(resPath, materialStore):
    """
    Store out a single material store.
    Mostly used to export base material definitions
    """
    import CCP_P4 as P4
    p4path = blue.paths.ResolvePathForWriting(resPath)
    destFolder = os.path.dirname(p4path)
    if not os.path.exists(destFolder):
        os.makedirs(destFolder)
    if ENABLE_P4 is True:
        if not P4.P4FileInDepot(p4path):
            P4.P4Add(p4path)
        else:
            P4.P4Edit(p4path)
    blue.resMan.SaveObject(materialStore, resPath)


def SerializeMaterialRes(ob, materialRes, p4c = None, path = None):
    """
    Given an object and its associated materialRes,
    store out the materialRes.
    
    TODO: Pass in the ob's res path rather than the whole object
    """
    import CCP_P4 as P4
    if path is None:
        resPath = GetResPath(ob)
        path = GetMaterialPathFromGeometryPath(resPath)
    if not path:
        return
    p4path = blue.paths.ResolvePathForWriting(path)
    destFolder = os.path.dirname(p4path)
    if not os.path.exists(destFolder):
        os.makedirs(destFolder)
    p4Root = P4.getRoot().lower()
    p4Root = p4Root.replace('/', '\\')
    osPath = os.path.abspath(path).lower()
    osPath = osPath.replace('/', '\\')
    inDepot = p4Root in osPath
    if inDepot and ENABLE_P4 is True:
        if not P4.P4FileInDepot(p4path, p4c):
            P4.P4Add2(p4path, p4c)
        else:
            P4.P4Edit2(p4path, p4c)
    if not blue.resMan.SaveObject(materialRes, path):
        log.LogWarn('===== SAVING FAILED for file %s =====' % p4path)


def CreateMaterialResFromAreas(ob, defaultMetatype):
    """
    Create a new material res for this object based on the content of the areas
    """
    trinity.WaitForResourceLoads()
    meshes = GetMeshList(ob)
    if not meshes:
        return
    materialRes = trinity.Tr2MaterialRes()
    for mesh in meshes:
        geo = mesh.geometry
        meshStore = trinity.Tr2MaterialMesh()
        materialRes.meshes[mesh.name] = meshStore
        for areaIdx in xrange(geo.GetMeshAreaCount(mesh.meshIndex)):
            areaName = geo.GetMeshAreaName(mesh.meshIndex, areaIdx)
            areaStore = trinity.Tr2MaterialArea()
            areaStore.metatype = str(defaultMetatype)
            areaStore.material = trinity.Tr2MaterialParameterStore()
            meshStore.areas[areaName] = areaStore
            params = GetParametersFromMeshArea(mesh, areaIdx, None)
            for p in params:
                if params[p].value is not None:
                    try:
                        if params[p].value is not params[p].default:
                            areaStore.material.parameters[p] = params[p].value
                    except TypeError:
                        pass

    return materialRes


def BindObjectShaders(ob):
    """
    Attempt to call the highest level bind function available
    """
    if hasattr(ob, 'MarkAsDirty'):
        ob.MarkAsDirty()
    if hasattr(ob, 'BindLowLevelShaders'):
        ob.BindLowLevelShaders()
    else:
        meshes = GetMeshList(ob)
        if not meshes:
            return
        for mesh in meshes:
            mesh.BindLowLevelShaders([])


def SetAreaMetaShader(materialRes, mesh, areaIdx, metashader):
    """
    Applies the specified metashader to the mesharea specified by the mesh and the areaId
    """
    geo = mesh.geometry
    meshName = mesh.name
    areaName = geo.GetMeshAreaName(mesh.meshIndex, areaIdx)
    try:
        meshRes = materialRes.meshes[meshName]
    except KeyError:
        log.LogWarn('Mesh not found!')
        return

    try:
        areaRes = meshRes.areas[areaName]
    except KeyError:
        log.LogWarn('Area not found!')
        return

    areaRes.metatype = str(metashader)
    ApplyAreaRes(areaRes, mesh, areaIdx)


def ApplyAreaRes(areaRes, mesh, areaIdx):
    """
    This function ensures that the specified Area is
    in the correct areaLists in the specified Mesh,
    and then applies the material from the specified
    areaRes.
    """
    geo = mesh.geometry
    if not (geo.isPrepared and geo.isGood):
        log.LogWarn('FAILED TO PREPARE MESH %s' % mesh.name)
        return
    metashaders = LoadMetaMaterialLibrary()
    try:
        currentShader = metashaders[str(areaRes.metatype)]
    except KeyError:
        log.LogWarn('Unknown MetaMaterial: %s' % areaRes.metatype)
        return

    for typeIdx in xrange(mesh.GetAreasCount()):
        areaList = mesh.GetAreas(typeIdx)
        if areaList is not None:
            for area in areaList:
                if area.index == areaIdx:
                    areaList.remove(area)
                    break

    for area in currentShader:
        areaList = getattr(mesh, area['name'])
        if areaList is not None:
            areaName = geo.GetMeshAreaName(mesh.meshIndex, areaIdx)
            newArea = trinity.Tr2MeshArea()
            newArea.index = areaIdx
            newArea.count = 1
            newArea.name = areaName
            if 'shLighting' in area and area['shLighting']:
                newArea.useSHLighting = True
            newArea.effect = trinity.Tr2ShaderMaterial()
            newArea.effect.highLevelShaderName = area['shader']
            if 'situation' in area:
                newArea.effect.defaultSituation = area['situation']
            newArea.effect.PopulateDefaultParameters()
            areaList.append(newArea)
            ApplyMaterialStoreToEffect(newArea.effect, areaRes.material)


def LoadMetaMaterialFile(resourceFile = METASHADER_PATH, forceload = False):
    """
    Loads the global meta-material library and initializes global shader library
    and global packing. Returns tuple of both.
    """
    global _gMetaShaderLibrary
    global _gMetaShaderPacking
    if _gMetaShaderLibrary is not None and _gMetaShaderPacking is not None and forceload is False:
        return (_gMetaShaderLibrary, _gMetaShaderPacking)
    _gMetaShaderLibrary = {}
    _gMetaShaderPacking = {}
    if blue.paths.exists(resourceFile):
        rf = blue.ResFile()
        rf.Open(resourceFile)
        yamlStr = rf.read()
        rf.close()
        data = yaml.load(yamlStr)
        for metashader in data['metashaders']:
            _gMetaShaderLibrary[metashader['name']] = metashader['areas']
            try:
                _gMetaShaderPacking[metashader['name']] = metashader['texpacks']
            except:
                pass

    return (_gMetaShaderLibrary, _gMetaShaderPacking)


def LoadMetaMaterialLibrary(resourceFile = METASHADER_PATH, forceload = False):
    """
    Loads the global meta-material library
    Returns a dict of area dicts, keyed by metashader name
    """
    library, packing = LoadMetaMaterialFile(resourceFile, forceload)
    return library


def LoadMetaMaterialPacking(resourceFile = METASHADER_PATH, forceload = False):
    """
    Loads the global meta-material packing sceheme
    Returns a dict of packing filepaths, keyed by metashader name
    """
    global TEXPACKS_PATH
    library, packing = LoadMetaMaterialFile(resourceFile, forceload)
    packingPaths = dict()
    for k, texpack in packing.items():
        path = os.path.join(TEXPACKS_PATH, texpack) + '.texpack'
        packingPaths[k] = path

    return packingPaths


def GetPackingPathFromMetashader(metaShaderName):
    """Get packing path from metashader"""
    packings = LoadMetaMaterialPacking()
    return packings[metaShaderName]


def GetDefaultParametersFromMetashader(metaShaderName):
    materialMap = {}
    metaLib = LoadMetaMaterialLibrary()
    shaderInfo = metaLib[metaShaderName]
    for area in shaderInfo:
        shader = area['shader']
        mat = trinity.Tr2ShaderMaterial()
        mat.highLevelShaderName = shader
        if 'situation' in area:
            mat.defaultSituation = area['situation']
        mat.BindLowLevelShader([])
        if mat.highLevelShader:
            for desc in mat.highLevelShader.parameterDescriptions:
                defVal = None
                if hasattr(desc, 'CreateDefaultParameter'):
                    defVal = desc.CreateDefaultParameter()
                materialMap[desc.parameterName] = MetaMaterialParam(name=desc.parameterName, desc=desc, value=defVal, default=defVal)

        del mat

    return materialMap


def GetParametersFromMeshArea(mesh, areaIdx, areaRes):
    """
    Get a list of interface-friendly parameters from the specified mesh and area,
    using defaults specified by the areaRes, if required.
    """
    materialMap = {}
    for typeIdx in xrange(mesh.GetAreasCount()):
        areaList = mesh.GetAreas(typeIdx)
        if areaList:
            for area in areaList:
                if area.index == areaIdx:
                    if hasattr(area.effect, 'highLevelShader') and area.effect.highLevelShader is not None:
                        for desc in area.effect.highLevelShader.parameterDescriptions:
                            defVal = None
                            if areaRes and areaRes.material.parent and areaRes.material.parent.FindParameter(desc.parameterName):
                                inheritedParam = areaRes.material.parent.FindParameter(desc.parameterName)
                            else:
                                inheritedParam = None
                            if inheritedParam:
                                defVal = inheritedParam
                            elif hasattr(desc, 'CreateDefaultParameter'):
                                defVal = desc.CreateDefaultParameter()
                            else:
                                defVal = None
                            materialMap[desc.parameterName] = MetaMaterialParam(name=desc.parameterName, desc=desc, value=defVal, default=defVal)

                        params = area.effect.parameters
                        for p in params:
                            if p not in materialMap:
                                continue
                            materialMap[p].value = params[p]
                            if areaRes:
                                if p not in areaRes.material.parameters and p in materialMap:
                                    materialMap[p].default = params[p]

    return materialMap


def GetMaterialPathFromGeometryPath(oldPath):
    """
    Given a resource path to a gr2 or red file,
    return an appropriate path for storing or
    loading the materials file.
    """
    if oldPath is None:
        return
    import re
    newPath = re.sub('(?i)((.gr2)|(.red))$', '_Materials.red', oldPath)
    return newPath


def GetResPath(ob):
    """
    Queries an object and returns the path of the res file that contains the geometry.
    Often used in conjunction with GetMaterialPathFromGeometryPath 
    to determine where to store or load the materialRes file.
    """
    if hasattr(ob, 'geometryResPath'):
        return ob.geometryResPath
    elif hasattr(ob, 'visualModel') and hasattr(ob.visualModel, 'geometryResPath'):
        return ob.visualModel.geometryResPath
    elif hasattr(ob, 'placeableResPath'):
        return ob.placeableResPath
    else:
        log.LogWarn('UNKNOWN RESPATH for object type %s' % type(ob))
        return None


def GetMeshList(ob):
    """
    Queries an object and gets its mesh list if it supports it.
    """
    try:
        if hasattr(ob, 'meshes'):
            return ob.meshes
        if hasattr(ob, 'detailMeshes'):
            return ob.detailMeshes
        if hasattr(ob, 'visualModel'):
            return ob.visualModel.meshes
        if hasattr(ob, 'placeableRes'):
            return ob.placeableRes.visualModel.meshes
        if hasattr(ob, 'model') and hasattr(ob.model, 'meshes'):
            return ob.model.meshes
        return None
    except AttributeError:
        return None


exports = {'metaMaterials.BindObjectShaders': BindObjectShaders,
 'metaMaterials.ApplyAreaRes': ApplyAreaRes,
 'metaMaterials.ApplyMaterialRes': ApplyMaterialRes,
 'metaMaterials.LoadMaterialResFromObject': LoadMaterialResFromObject,
 'metaMaterials.LoadAndApplyMaterialRes': LoadAndApplyMaterialRes,
 'metaMaterials.LoadMetaMaterialLibrary': LoadMetaMaterialLibrary,
 'metaMaterials.LoadMetaMaterialPacking': LoadMetaMaterialPacking,
 'metaMaterials.GetPackingPathFromMetashader': GetPackingPathFromMetashader,
 'metaMaterials.FindAreaResByMeshAndIndex': FindAreaResByMeshAndIndex,
 'metaMaterials.SetAreaMetaShader': SetAreaMetaShader,
 'metaMaterials.SerializeMaterialRes': SerializeMaterialRes,
 'metaMaterials.SerializeMaterialStore': SerializeMaterialStore,
 'metaMaterials.GetMeshList': GetMeshList,
 'metaMaterials.GetParametersFromMeshArea': GetParametersFromMeshArea,
 'metaMaterials.GetResPath': GetResPath,
 'metaMaterials.GetMaterialPathFromGeometryPath': GetMaterialPathFromGeometryPath,
 'metaMaterials.GetDefaultParametersFromMetashader': GetDefaultParametersFromMetashader,
 'metaMaterials.LoadMaterialRes': LoadMaterialRes}
