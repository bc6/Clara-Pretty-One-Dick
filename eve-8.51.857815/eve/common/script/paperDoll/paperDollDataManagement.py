#Embedded file name: eve/common/script/paperDoll\paperDollDataManagement.py
"""
This file contains the classes used for data manipulation of the doll, that is, defined and track
modifiers and their configuration. Must be usable on a server so it is _strictly forbidden_ to ever
**import trinity** in this file.
"""
import os
import uthread
import copy
import types
import hashlib
import blue
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollCommonFunctions as pdCF
from eve.common.script.paperDoll.paperDollResData import ResData, GenderData
import telemetry
import log
import sys
import legacy_r_drive
from .yamlPreloader import YamlPreloader, LoadYamlFileNicely
from .paperDollConfiguration import PerformanceOptions
from .yamlPreloader import AvatarPartMetaData

def ClearAllCachedMaps():
    """
    Clears out the entire cache of maps saved using SaveMaps
    """
    cachePath = GetMapCachePath()
    fileSystemPath = blue.rot.PathToFilename(cachePath)
    for root, dirs, files in os.walk(fileSystemPath):
        for f in iter(files):
            os.remove(os.path.join(root, f))


def GetMapCachePath():
    avatarCachePath = u''
    try:
        userCacheFolder = blue.paths.ResolvePath(u'cache:')
        avatarCachePath = u'{0}/{1}'.format(userCacheFolder, u'Avatars/cachedMaps')
    except Exception:
        avatarCachePath = u''
        sys.exc_clear()

    return avatarCachePath


def GetCacheFilePath(cachePath, hashKey, textureWidth, mapType):
    r"""
    Inputs:
        'cachePath':    the absolute os path to the root folder that contains the cached textures
        'hashKey':      a number that is unique for a given doll, '-' is replaced with '_'
        'textureWidth': is the width of the texture
        'mapType':      is one of the elements defined in MAPS
    
    Returns:
        A string: cachePath \ textureWidth \ mapType + hashKey + .dds
    """
    cacheFilePath = u''
    try:
        hashKey = str(hashKey).replace('-', '_')
        cacheFilePath = u'{0}/{1}/{2}{3}.dds'.format(cachePath, textureWidth, mapType, hashKey)
    except Exception:
        cacheFilePath = u''
        sys.exc_clear()

    return cacheFilePath


def FindCachedMap(hashKey, textureWidth, mapType):
    """
    Searches the user's cache for a pre-existing texture.
    'hashKey' is the hash of a doll's modifiers
    'textureWidth' is the width of the texture
    'mapType' is defined in MAPS
    Returns a texture instance or None if nothing is found.
    """
    cachePath = GetMapCachePath()
    try:
        if cachePath:
            filePath = GetCacheFilePath(cachePath, hashKey, textureWidth, mapType)
            if filePath:
                if blue.paths.exists(filePath):
                    rotPath = blue.rot.FilenameToPath(filePath)
                    os.utime(filePath, None)
                    cachedTexture = blue.resMan.GetResourceW(rotPath)
                    return cachedTexture
    except Exception:
        sys.exc_clear()


def SaveMapsToDisk(hashKey, maps):
    """
    'hashKey' is the unique hash of a given paperdoll builddata list
    'textureWidth' is the width of the texture
    'maps' is a list of textures.
    Saves the maps out to the users cache folder.
    """
    cachePath = GetMapCachePath()
    if not cachePath:
        return
    for i, each in enumerate(maps):
        if each is not None:
            textureWidth = each.width
            filePath = GetCacheFilePath(cachePath, hashKey, textureWidth, i)
            if filePath:
                folder = os.path.split(filePath)[0]
                try:
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    each.Save(filePath)
                    each.WaitForSave()
                except OSError:
                    pass


class ModifierLoader():
    """
    This class encapsulates the operations done when loading modifiers, without using any trinity
    level components. Therefor, many factory operations can be done with server code.
    The factory inherits this class.
    """
    __guid__ = 'paperDoll.ModifierLoader'
    __sharedLoadSource = False
    __sharedResData = None
    __isLoaded = False

    def setclothSimulationActive(self, value):
        self._clothSimulationActive = value

    clothSimulationActive = property(fget=lambda self: self._clothSimulationActive, fset=lambda self, value: self.setclothSimulationActive(value))

    def __init__(self):
        self.yamlPreloader = YamlPreloader()
        self.resData = None
        self.patterns = []
        self.IsLoaded = False
        self.forceRunTimeOptionGeneration = False
        self._clothSimulationActive = False
        uthread.new(self.LoadData_t)

    def DebugReload(self, forceRunTime = False):
        """
        Reloads the option data
        """
        self.forceRunTimeOptionGeneration = forceRunTime
        ModifierLoader.__sharedLoadSource = False
        ModifierLoader.__sharedResData = None
        ModifierLoader.__isLoaded = False
        YamlPreloader.Clear()
        uthread.new(self.LoadData_t)

    @staticmethod
    @telemetry.ZONE_FUNCTION
    def LoadBlendshapeLimits(limitsResPath):
        """
        Loads blendshape limits and returns a dict of the limits,
        where key is the modifier name and the value is a tuple => (min, max)
        Returns None if the path does not contain a limits file.
        """
        data = LoadYamlFileNicely(limitsResPath)
        if data is not None:
            limits = data.get('limits')
            ret = {}
            if limits and type(limits) is dict:
                for k, v in limits.iteritems():
                    ret[k.lower()] = v

                data['limits'] = ret
        return data

    @telemetry.ZONE_METHOD
    def GetWorkingDirectory(self, gender):
        if gender == pdDef.GENDER.FEMALE:
            return pdDef.FEMALE_BASE_PATH
        else:
            return pdDef.MALE_BASE_PATH

    @telemetry.ZONE_METHOD
    def LoadData_t(self):
        try:
            if ModifierLoader.__sharedLoadSource == legacy_r_drive.loadFromContent and ModifierLoader.__sharedResData:
                self.resData = ModifierLoader.__sharedResData
                while not ModifierLoader.__isLoaded:
                    pdCF.Yield()

                self.IsLoaded = True
                return
            self.resData = ResData()
            femPath = pdDef.FEMALE_BASE_PATH
            femPathLOD = pdDef.FEMALE_BASE_LOD_PATH
            femPathGT = pdDef.FEMALE_BASE_GRAPHICS_TEST_PATH
            femPathGTLOD = pdDef.FEMALE_BASE_GRAPHICS_TEST_LOD_PATH
            malePath = pdDef.MALE_BASE_PATH
            malePathLOD = pdDef.MALE_BASE_LOD_PATH
            malePathGT = pdDef.MALE_BASE_GRAPHICS_TEST_PATH
            malePathGTLOD = pdDef.MALE_BASE_GRAPHICS_TEST_LOD_PATH
            if legacy_r_drive.loadFromContent:
                femPath = femPath.replace('res:', 'resPreview:')
                femPathLOD = femPathLOD.replace('res:', 'resPreview:')
                femPathGT = femPathGT.replace('res:', 'resPreview:')
                femPathGTLOD = femPathGTLOD.replace('res:', 'resPreview:')
                malePath = malePath.replace('res:', 'resPreview:')
                malePathLOD = malePathLOD.replace('res:', 'resPreview:')
                malePathGT = malePathGT.replace('res:', 'resPreview:')
                malePathGTLOD = malePathGTLOD.replace('res:', 'resPreview:')
            self.resData.Populate(pdDef.GENDER.FEMALE, femPath)
            self.resData.Populate(pdDef.GENDER.FEMALE, femPathLOD, key=GenderData.LOD_KEY)
            self.resData.Populate(pdDef.GENDER.FEMALE, femPathGT, key=GenderData.TEST_KEY)
            self.resData.Populate(pdDef.GENDER.FEMALE, femPathGTLOD, key=GenderData.TEST_LOD_KEY)
            self.resData.Populate(pdDef.GENDER.MALE, malePath)
            self.resData.Populate(pdDef.GENDER.MALE, malePathLOD, key=GenderData.LOD_KEY)
            self.resData.Populate(pdDef.GENDER.MALE, malePathGT, key=GenderData.TEST_KEY)
            self.resData.Populate(pdDef.GENDER.MALE, malePathGTLOD, key=GenderData.TEST_LOD_KEY)
            while self.resData.IsLoading():
                pdCF.Yield()

            PerformanceOptions.SetEnableYamlCache(True)
            while self.yamlPreloader.IsLoading():
                pdCF.Yield()

            for gender in pdDef.GENDER:
                self.resData.PopulateVirtualModifierFolders(gender)

            self.resData.LinkSiblings(None, GenderData.LOD_KEY)
            self.resData.LinkSiblings(GenderData.TEST_KEY, GenderData.TEST_LOD_KEY)
            self.resData.PropogateLODRules()
            self._LoadPatterns()
            self.IsLoaded = True
        finally:
            ModifierLoader.__sharedLoadSource = legacy_r_drive.loadFromContent
            ModifierLoader.__sharedResData = self.resData
            ModifierLoader.__isLoaded = self.IsLoaded

    @telemetry.ZONE_METHOD
    def WaitUntilLoaded(self):
        while not self.IsLoaded:
            pdCF.Yield()

    @telemetry.ZONE_METHOD
    def _LoadPatterns(self):
        if legacy_r_drive.loadFromContent:
            self.patterns = pdDef.GetPatternList()
        else:
            if pdDef.GENDER_ROOT:
                optionsFile = 'res:/{0}/Character/PatternOptions.yaml'.format(pdDef.BASE_GRAPHICS_FOLDER)
            else:
                optionsFile = 'res:/{0}/Character/Modular/PatternOptions.yaml'.format(pdDef.BASE_GRAPHICS_FOLDER)
            self.patterns = LoadYamlFileNicely(optionsFile)

    def GetPatternDir(self):
        return 'res:/{0}/Character/Patterns'.format(pdDef.BASE_GRAPHICS_FOLDER)

    @telemetry.ZONE_METHOD
    def GetItemType(self, itemTypePath, gender = None):
        """
        Reads and caches the data behind an itemType.
        If only 'itemTypePath' is given then 'itemTypePath' must be the full path in res.
        If 'itemTypePath' and 'gender' are given, then gender agnostic paths in 'itemTypePath' are supported.
        Returns a tuple of 3 elements or None if itemTypePath is invalid.
        """
        if gender and 'res:' not in itemTypePath:
            basePath = ''
            if gender == pdDef.GENDER.MALE:
                basePath = pdDef.MALE_BASE_PATH
            elif gender == pdDef.GENDER.FEMALE:
                basePath = pdDef.FEMALE_BASE_PATH
            if itemTypePath.startswith('/'):
                fmt = '{0}{1}'
            else:
                fmt = '{0}/{1}'
            itemTypePath = fmt.format(basePath, itemTypePath)
        itemType = self.__GetFromYamlCache(itemTypePath)
        return itemType

    def ListTypes(self, gender, cat = None, modifier = None):
        """
        Lists up all types belonging to the provided gender. 
        If 'cat' is specified, will only list types belonging to that category
        If 'modifier' is specified, will only list types belonging to that modifier.
        """
        availableTypes = []
        if modifier:
            parentEntry = self.resData.GetEntryByPath(gender, modifier.respath)
            entries = self.resData.GetChildEntries(parentEntry)
        elif cat:
            parentEntry = self.resData.GetEntryByPath(gender, cat)
            entries = self.resData.Traverse(parentEntry, visitFunc=lambda x: not x.dirs)
        else:
            entries = [ entry for entry in self.resData.GetEntriesByGender(gender) if not entry.dirs ]
        for entry in entries:
            fileNames = entry.GetFilesByExt('type')
            for fn in fileNames:
                fullResPath = entry.GetFullResPath(fn)
                availableTypes.append(fullResPath)

        return availableTypes

    def CategoryHasTypes(self, category):
        """
            Returns true if a category uses types.
        """

        def Visit(gender, resDataEntry):
            if not resDataEntry:
                return False
            found = False
            if 'types' in resDataEntry.dirs:
                found = True
            if not found:
                for childResDataEntry in self.resData.GetChildEntries(resDataEntry):
                    found = Visit(gender, childResDataEntry)
                    if found:
                        break

            return found

        def CheckTypes(gender):
            entry = self.resData.GetEntryByPath(gender, category)
            return Visit(gender, entry)

        return any(map(lambda x: CheckTypes(x), pdDef.GENDER))

    @telemetry.ZONE_METHOD
    def ListOptions(self, gender, cat = None, showVariations = False):
        """
        Lists the options available for the given 'gender', which should be GENDER.MALE or GENDER.FEMALE.
        This will return the available modifiers as paths.
        
        Example:
            ListOptions('female')
            >> ['accessories/drape/standard', ..., 'bodyshapes/abs_rightshape' ]
        
        
        If 'cat' is provided, it is the category for which to list the options, that is, the name
        of modifiers belonging to that category:
        
        Example: 
            ListOptions( 'female', 'bottomouter')
            >> ['blank', 'pantsaf01', 'pantscf01', 'pantsgf01', 'pantsmf01']
            
        If 'showVariations' is true, all variations are added as a tuple for a given path
        and thus a list of name, tuple pairs is returned:
        
        Example:
            ListOptions( 'female', 'bottomouter', True)
            [('blank', ()), ('pantsaf01', ()), ('pantscf01', ()), ('pantsgf01', ('v1',)), ('pantsmf01', ())
        """
        results = []
        entries = []
        if cat:
            pathEntry = self.resData.GetEntryByPath(gender, cat)
            if pathEntry:
                entries.extend(self.resData.GetChildEntries(pathEntry))
            pathEntry = self.resData.GetEntryByPath(gender, cat, key=GenderData.TEST_KEY)
            if pathEntry:
                entries.extend(self.resData.GetChildEntries(pathEntry, key=GenderData.TEST_KEY))
            if showVariations:
                for entry in entries:
                    variations = []
                    for childEntry in self.resData.GetChildEntries(entry):
                        if childEntry.isVariationFolder:
                            variations.append(childEntry.leafFolderName)

                    result = (entry.leafFolderName, tuple(variations))
                    results.append(result)

            else:
                for entry in entries:
                    results.append(entry.leafFolderName)

        else:
            results.extend(self.resData.GetPathToEntryByGender(gender).keys())
            results.extend(self.resData.GetPathToEntryByGender(gender, key=GenderData.TEST_KEY).keys())
        results.sort()
        return results

    @telemetry.ZONE_METHOD
    def CollectBuildData(self, gender, path, weight = 1.0, forceLoaded = False):
        """
        Instansiates a new builddata instance (modifier) and loads resources into it.
        Returns the modifier instance.
        """
        currentBuildData = BuildData(path)
        currentBuildData.weight = weight
        self.LoadResource(gender, path, currentBuildData, forceLoaded=forceLoaded)
        return currentBuildData

    @telemetry.ZONE_METHOD
    def LoadResource(self, gender, path, modifier, forceLoaded = False):
        if not self.resData.QueryPathByGender(gender, path):
            log.LogWarn('PaperDoll - Path {0} for gender {1} does not exist that is passed to ModifierLoader::LoadResource!'.format(path, gender))
            return
        if not forceLoaded:
            while not self.IsLoaded:
                pdCF.BeFrameNice()

        resDataEntry = self.resData.GetEntryByPath(gender, path)
        modifier.lodCutoff = resDataEntry.lodCutoff or modifier.lodCutoff
        self._GetFilesForEntry(resDataEntry, modifier)
        parentEntry = self.resData.GetParentEntry(resDataEntry)
        if 'colors' in parentEntry.dirs:
            colorEntry = self.resData.GetEntryByPath(gender, parentEntry.GetResPath('colors'))
            self._PopulateMetaData(modifier, colorEntry)
        matchingVariationEntries = (entry for entry in self.resData.GetChildEntries(resDataEntry) if entry.isVariationFolder)
        for variationResDataEntry in iter(matchingVariationEntries):
            variationModifier = BuildData()
            self._GetFilesForEntry(variationResDataEntry, variationModifier)
            modifier.variations[variationResDataEntry.leafFolderName] = variationModifier

        if len(modifier.variations):
            original = copy.deepcopy(modifier)
            original.variations = {}
            modifier.variations['v0'] = original
        if 'default' in modifier.colorVariations:
            modifier.SetColorVariation('default')
        if modifier.metaData.alternativeTextureSourcePath:
            path = modifier.metaData.alternativeTextureSourcePath.lower()
            altEntry = self.resData.GetEntryByPath(gender, path)
            self._GetFilesForEntry(altEntry, modifier, sourceMapsOnly=True)

    @telemetry.ZONE_METHOD
    def __GetFromYamlCache(self, key):
        inst = self.yamlPreloader.LoadYaml(key)
        return inst

    @telemetry.ZONE_METHOD
    def _PartFromPath(self, path, reverseLookupData = None, rvPart = None):
        for part in pdDef.DOLL_PARTS:
            if part in path:
                return part

        if '_acc_' in path:
            return pdDef.DOLL_PARTS.ACCESSORIES
        if reverseLookupData:
            for part in iter(reverseLookupData):
                if part in path:
                    return rvPart

        return ''

    @telemetry.ZONE_METHOD
    def _PopulateSourceMaps(self, modifier, resDataEntry):
        files = resDataEntry.sourceMaps.keys()
        for f in files:
            partType = self._PartFromPath(f) or self._PartFromPath(resDataEntry.respath, pdDef.BODY_CATEGORIES, pdDef.DOLL_PARTS.BODY)
            if pdDef.MAP_PREFIX_COLORIZE in f:
                modifier.colorize = True
            if pdDef.MAP_SUFFIX_DRGB in f:
                modifier.mapDRGB[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_LRGB in f:
                modifier.mapLRGB[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_LA in f:
                modifier.mapLA[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_DA in f:
                modifier.mapDA[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_L in f:
                modifier.mapL[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_Z in f:
                modifier.mapZ[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_O in f:
                modifier.mapO[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_D in f:
                modifier.mapD[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_N in f:
                modifier.mapN[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_MN in f:
                modifier.mapMN[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_TN in f:
                modifier.mapTN[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_S in f:
                modifier.mapSRG[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_AO in f:
                modifier.mapAO[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_MM in f:
                modifier.mapMaterial[partType] = resDataEntry.GetFullResPath(f)
            elif pdDef.MAP_SUFFIX_MASK in f or pdDef.MAP_SUFFIX_M in f:
                modifier.mapMask[partType] = resDataEntry.GetFullResPath(f)
                modifier.mapAO[partType] = resDataEntry.GetFullResPath(f)

    @telemetry.ZONE_METHOD
    def _PopulateGeometry(self, modifier, resDataEntry):
        modifier.clothPath = resDataEntry.redFiles.get(pdDef.CLOTH_PATH, '')
        modifier.clothOverride = resDataEntry.redFiles.get(pdDef.CLOTH_OVERRIDE, '')
        modifier.stubblePath = resDataEntry.redFiles.get(pdDef.STUBBLE_PATH, '')
        if modifier.stubblePath:
            modifier.colorize = True
        modifier.shaderPath = resDataEntry.redFiles.get(pdDef.SHADER_PATH, '')
        modifier.redfile = resDataEntry.redFiles.get(pdDef.RED_FILE, '')

    @telemetry.ZONE_METHOD
    def _PopulateMetaData(self, modifier, resDataEntry):
        metaDataFn = 'metadata.yaml'
        if metaDataFn in resDataEntry.files:
            resPath = resDataEntry.GetFullResPath(metaDataFn)
            inst = self.__GetFromYamlCache(resPath)
            if inst:
                inst.defaultMetaData = False
                modifier.metaData = inst
        files = resDataEntry.GetFilesByExt('pose')
        if files:
            resPath = resDataEntry.GetFullResPath(files[0])
            inst = self.__GetFromYamlCache(resPath)
            modifier.poseData = inst
        files = resDataEntry.GetFilesByExt('color')
        for f in files:
            resPath = resDataEntry.GetFullResPath(f)
            inst = self.__GetFromYamlCache(resPath)
            varName = f.split('.')[0]
            modifier.colorVariations[varName] = inst

        files = resDataEntry.GetFilesByExt('proj')
        if files:
            resPath = resDataEntry.GetFullResPath(files[0])
            inst = self.__GetFromYamlCache(resPath)
            if inst:
                inst.SetTexturePath(inst.texturePath)
                inst.SetMaskPath(inst.maskPath)
                modifier.decalData = inst

    @telemetry.ZONE_METHOD
    def _GetFilesForEntry(self, resDataEntry, modifier, sourceMapsOnly = False):
        if resDataEntry:
            self._PopulateSourceMaps(modifier, resDataEntry)
            dimExt = [ ext for ext in resDataEntry.extToFiles.keys() if ext.isdigit() ]
            if dimExt:
                dimFn = resDataEntry.extToFiles[dimExt[0]][0]
                modifier.accessoryMapSize = [ int(x) for x in dimFn.split('.')[-2:] ]
            if not sourceMapsOnly:
                self._PopulateGeometry(modifier, resDataEntry)
                self._PopulateMetaData(modifier, resDataEntry)
        return modifier


class BuildDataMaps(object):
    """
    This class encapsulates the map storage and querying part of a modifier (BuildData).
    BuildData inherits from BuildDataMaps.
    """

    def __init__(self):
        self._isTextureContainingModifier = None
        self._contributesToMapTypes = None
        self._affectedTextureParts = None
        self.mapN = {}
        self.mapMN = {}
        self.mapTN = {}
        self.mapSRG = {}
        self.mapAO = {}
        self.mapMaterial = {}
        self.mapMask = {}
        self.mapD = {}
        self.mapDRGB = {}
        self.mapDA = {}
        self.mapLRGB = {}
        self.mapLA = {}
        self.mapL = {}
        self.mapZ = {}
        self.mapO = {}

    def IsTextureContainingModifier(self):
        """
        Returns True if this modifier contains any textures, otherwise False.
        """
        if self._isTextureContainingModifier is None:
            self._isTextureContainingModifier = False
            for each in self.__dict__.iterkeys():
                if each.startswith('map'):
                    if self.__dict__[each]:
                        self._isTextureContainingModifier = True
                        break

        return self._isTextureContainingModifier

    def ContributesToMapTypes(self):
        """
        Returns a list of mapTypes that this modifier will contribute to.
        """
        if self._contributesToMapTypes is None:
            mapTypes = list()
            if len(self.mapD.keys()) > 0 or len(self.mapL.keys()) > 0 or len(self.mapZ.keys()) > 0 or len(self.mapO.keys()) > 0:
                mapTypes.append(pdDef.DIFFUSE_MAP)
            if len(self.mapSRG.keys()) > 0 or len(self.mapAO.keys()) > 0 or len(self.mapMaterial.keys()) > 0:
                mapTypes.append(pdDef.SPECULAR_MAP)
            if len(self.mapN.keys()) > 0 or len(self.mapMN.keys()) > 0 or len(self.mapTN.keys()) > 0:
                mapTypes.append(pdDef.NORMAL_MAP)
            if len(self.mapMask.keys()) > 0:
                mapTypes.append(pdDef.MASK_MAP)
            self._contributesToMapTypes = mapTypes
        return self._contributesToMapTypes

    def GetAffectedTextureParts(self):
        """
        Returns a distinct set of keys in all mapX attributes of this modifier
        This set is the bodyparts used for compositing.
        """
        if self._affectedTextureParts is None:
            parts = set()
            for each in self.__dict__.iterkeys():
                if each.startswith('map'):
                    parts.update(self.__dict__[each].keys())

            self._affectedTextureParts = parts
        return self._affectedTextureParts


class BuildData(BuildDataMaps):
    """
    BuildData instance is a modifier. 
    This class contains all the possible data needed to describe a modifier and to keep its state 
    during runtime. A large resposinbility of this class is to correctly dictate when it 
    has become dirty, because only dirty modifiers have any effect on a doll during Update.
    Instances of this class are also often copied, so changes that can possibly make references 
    of this class become shared are dangerous.
    
    When reading a doll from DNA, each entry in the DNA is possibly a footprint. Footprints describe a modifier
    well enough to recreate and reload it during runtime.
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.BuildData'
    DEFAULT_COLORIZEDATA = [pdDef.MID_GRAY] * 3
    DEFAULT_PATTERNDATA = [pdDef.DARK_GRAY,
     pdDef.LIGHT_GRAY,
     pdDef.MID_GRAY,
     pdDef.MID_GRAY,
     pdDef.MID_GRAY,
     (0, 0, 8, 8),
     0.0]
    DEFAULT_SPECULARCOLORDATA = [pdDef.MID_GRAY] * 3

    def __del__(self):
        self.ClearCachedData()

    def __init__(self, pathName = None, name = None, categorie = None):
        BuildDataMaps.__init__(self)
        self.name = ''
        self.categorie = categorie.lower() if categorie else ''
        extPath = None
        splits = None
        if pathName is not None:
            pathName = pathName.lower()
            splits = pathName.split(pdDef.SEPERATOR_CHAR)
            extPath = str(pdDef.SEPERATOR_CHAR.join(splits[1:]))
            self.categorie = str(splits[0])
        self.lodCutoff = pdDef.LOD_99
        self.lodCutin = -pdDef.LOD_99
        self.name = name.lower() if name else extPath
        if self.categorie and self.name:
            self.respath = '{0}/{1}'.format(self.categorie, self.name)
        else:
            self.respath = ''
        if splits and len(splits) > 2:
            self.group = splits[1]
        else:
            self.group = ''
        self.usingMaskedShader = False
        self.redfile = ''
        self.clothPath = ''
        self.clothOverride = ''
        self.meshes = []
        self.__cmpMeshes = []
        self.meshGeometryResPaths = {}
        self.dependantModifiers = {}
        self.__clothData = None
        self.__clothDirty = False
        self.stubblePath = ''
        self.shaderPath = ''
        self.drapePath = ''
        self.accessoryMapSize = None
        self.decalData = None
        self.colorize = False
        self._colorizeData = list(BuildData.DEFAULT_COLORIZEDATA)
        self.__cmpColorizeData = []
        self.__pattern = ''
        self.patternData = list(BuildData.DEFAULT_PATTERNDATA)
        self.__cmpPatternData = []
        self.specularColorData = list(BuildData.DEFAULT_SPECULARCOLORDATA)
        self.__cmpSpecularColorData = []
        self.colorVariations = {}
        self.currentColorVariation = ''
        self.variations = {}
        self.variationTextureHash = ''
        self.currentVariation = ''
        self.lastVariation = ''
        self.__weight = 1.0
        self.hasWeightPulse = False
        self.__useSkin = False
        self.metaData = AvatarPartMetaData()
        self.poseData = None
        self.__tuck = True
        self.ulUVs = (pdDef.DEFAULT_UVS[0], pdDef.DEFAULT_UVS[1])
        self.lrUVs = (pdDef.DEFAULT_UVS[2], pdDef.DEFAULT_UVS[3])
        self.__IsHidden = False
        self.WasHidden = False
        self.__IsDirty = True
        self.__hashValue = None

    def HasWeightPulse(self):
        """
        Returns True iff this modifier has changed weight value in a significant way.
        Significant being:
            weight went from 0 or less to a positive number
            weight went from a positive number to 0 or less
        """
        return self.hasWeightPulse

    def IsVisibleAtLOD(self, lod):
        return self.lodCutin <= lod <= self.lodCutoff

    def GetUVsForCompositing(self, bodyPart):
        if bodyPart != pdDef.DOLL_PARTS.ACCESSORIES:
            if bodyPart == pdDef.DOLL_PARTS.BODY:
                UVs = pdDef.BODY_UVS
            elif bodyPart == pdDef.DOLL_PARTS.HEAD:
                UVs = pdDef.HEAD_UVS
            elif bodyPart == pdDef.DOLL_PARTS.HAIR:
                UVs = pdDef.HAIR_UVS
        else:
            accUVs = pdDef.ACCE_UVS
            width = accUVs[2] - accUVs[0]
            height = accUVs[3] - accUVs[1]
            UVs = list((accUVs[0] + self.ulUVs[0] * width, accUVs[1] + self.ulUVs[1] * height) + (accUVs[0] + self.lrUVs[0] * width, accUVs[1] + self.lrUVs[1] * height))
        return UVs

    def SetColorizeData(self, *args):
        """
        SetColorizeData(self, colorA, colorB, colorC)                
        Sets the colorizable data as set of three tuples
        """
        x = args
        depth = 0
        while len(x) == 1 and type(x[0]) in (tuple, list) and depth < 5:
            x = x[0]
            depth += 1

        didChange = False
        for i in xrange(len(x)):
            if len(x) > i and type(x[i]) in (tuple, list):
                if self._colorizeData[i] != tuple(x[i]):
                    self._colorizeData[i] = tuple(x[i])
                    didChange = True

        if didChange:
            self.IsDirty = True

    def GetColorizeData(self):
        """
        Returns a list containing 3 tuples, where each
        tuple represents a color in RGB.
        """
        return self._colorizeData

    def GetColorVariations(self):
        """
        Returns a list of pre-saved color variations
        """
        return self.colorVariations.keys()

    def SetColorVariation(self, variationName):
        """
        Applies a pre-saved color variation to the modifier.
        """
        if variationName == 'none':
            self.currentColorVariation = 'none'
            return
        if not self.currentColorVariation == 'none' and self.colorVariations and variationName in self.colorVariations:
            currentColorVariation = self.colorVariations[variationName]
            if not currentColorVariation:
                return
            if 'colors' in currentColorVariation:
                for i in xrange(3):
                    self.colorizeData[i] = currentColorVariation['colors'][i]

            if 'pattern' in currentColorVariation:
                self.pattern = currentColorVariation['pattern']
            if 'patternColors' in currentColorVariation:
                arrayLength = len(currentColorVariation['patternColors'])
                for i in xrange(arrayLength):
                    self.patternData[i] = currentColorVariation['patternColors'][i]

            if 'specularColors' in currentColorVariation:
                for i in xrange(3):
                    self.specularColorData[i] = currentColorVariation['specularColors'][i]

            self.currentColorVariation = str(variationName)

    def SetColorVariationDirectly(self, variation):
        """
        Applies a color variation to the modifier that is passed in.
        Bypasses self.colorVariations
        """
        if variation is not None and type(variation) is types.DictionaryType:
            if 'colors' in variation:
                for i in xrange(3):
                    self.colorizeData[i] = variation['colors'][i]

            if 'pattern' in variation:
                self.pattern = variation['pattern']
            if 'patternColors' in variation:
                for i in xrange(5):
                    self.patternData[i] = variation['patternColors'][i]

            if 'specularColors' in variation:
                for i in xrange(3):
                    self.specularColorData[i] = variation['specularColors'][i]

    def SetColorVariationSpecularity(self, specularColor):
        self.specularColorData = specularColor

    def GetColorsFromColorVariation(self, variationName):
        """
        Returns the primary color values of a given color variation
        """
        if self.colorVariations and self.colorVariations.get(variationName):
            var = self.colorVariations[variationName]
            if var['pattern'] != '':
                return [var['patternColors'][0], var['patternColors'][3], var['patternColors'][4]]
            else:
                return var['colors']

    def GetVariations(self):
        """
        Returns a list of variations of the item. These exist in simple subfolders to the original, named v1,v2 and so on.
        """
        return self.variations.keys()

    def SetVariation(self, variationName):
        """
        Sets a variation of the modifier - this means certain aspects of it are overridden, such as textures.
        """
        variationName = variationName or 'v0'
        if self.variations and variationName in self.variations:
            oldRedFile = self.redfile
            oldClothPath = self.clothPath
            var = self.variations[variationName]
            doNotCopy = ['respath', 'dependantModifiers']
            for member in var.__dict__:
                if member not in doNotCopy:
                    if type(var.__dict__[member]) == str and var.__dict__[member]:
                        self.__dict__[member] = var.__dict__[member]
                    if type(var.__dict__[member]) == dict and len(var.__dict__[member]) > 0:
                        for entry in var.__dict__[member]:
                            self.__dict__[member][entry] = var.__dict__[member][entry]
                            if member.startswith('map'):
                                self.variationTextureHash = var.__dict__[member][entry]

                    if member == 'metaData':
                        if var.metaData and not var.metaData.defaultMetaData:
                            self.metaData = var.metaData

            if oldRedFile != self.redfile:
                del self.meshes[:]
                self.meshGeometryResPaths = {}
            if oldClothPath != self.clothPath:
                self.clothData = None
            self.lastVariation = self.currentVariation
            self.currentVariation = str(variationName)

    def GetVariationMetaData(self, variationName = None):
        """
        Returns the metadata for the currently set variation or the variation defined by 'variationName'
        Returns None if there is no metadata to return or the metadata on the variation is not authored.
        """
        if variationName == '':
            variationName = 'v0'
        variationName = variationName or self.currentVariation
        variation = self.variations.get(variationName)
        if variation and variation.metaData and not variation.metaData.defaultMetaData:
            return variation.metaData

    def GetDependantModifiersFullData(self, metaDataOverride = None):
        """
        Returns None if this modifier has no dependant modifiers
        
        Otherwise:            
            Returns a list of tuples that contains parsed version of the dependantModifiers data
            from the modifier's metaData
            
            Each tuple has 4 elements:
                respath, color variation name, variation name and weight value
            
            Only the respath is guaranteed to have specific value
            The weight value defaults to 1.0 when not specified
        """
        metaData = metaDataOverride or self.metaData
        if metaData.dependantModifiers:
            parsedValues = []
            for each in metaData.dependantModifiers:
                if '#' in each:
                    tmpList = []
                    for elem in each.split('#'):
                        tmpList.append(elem)

                    while len(tmpList) < 3:
                        tmpList.append('')

                    if len(tmpList) < 4:
                        tmpList.append(1.0)
                    else:
                        tmpList[3] = float(tmpList[3])
                    parsedValues.append(tuple(tmpList))
                else:
                    parsedValues.append((each,
                     '',
                     '',
                     1.0))

            return parsedValues

    def GetDependantModifierResPaths(self):
        """
        Returns None if this modifier has no dependant modifiers
        Otherwise, returns a list of the modifier res paths that are dependant on this modifier
        """
        if self.metaData.dependantModifiers:
            resPaths = []
            for resPath in self.metaData.dependantModifiers:
                if '#' in resPath:
                    resPaths.append(resPath.split('#')[0])
                else:
                    resPaths.append(resPath)

            return resPaths

    def GetOccludedModifiersFullData(self, metaDataOverride = None):
        """
        Returns None if this modifier is not occludeding modifiers
        
        Otherwise:            
            Returns a list of tuples that contains parsed version of the occludedModifiers data
            from the modifier's metaData
            
            Each tuple has 2 elements:
                respath and weight value
            
            Only the respath is guaranteed to have specific value
            The weight value defaults to 1.0 when not specified
        """
        if metaDataOverride:
            metaData = metaDataOverride
        else:
            metaData = self.metaData
        if metaData.occludesModifiers:
            parsedValues = []
            for each in metaData.occludesModifiers:
                if '#' in each:
                    tmpList = []
                    for elem in each.split('#'):
                        tmpList.append(elem)

                    if len(tmpList) < 2:
                        tmpList.append(1.0)
                    else:
                        tmpList[1] = float(tmpList[1])
                    tmpList[0] = tmpList[0].lower()
                    parsedValues.append(tuple(tmpList))
                else:
                    parsedValues.append((each.lower(), 1.0))

            return parsedValues

    def GetDependantModifiers(self):
        """
        Returns a list of the modifier instances that are dependant on this modifier
        """
        return self.dependantModifiers.values()

    def AddDependantModifier(self, modifier):
        """
        Adds a modifier to the collection of dependant modifier instances that
        this modifier aggregates
        """
        if self.respath == modifier.respath:
            raise AttributeError('paperDoll:BuildData:AddDependantModifier - Trying to add modifier as dependant of itself!')
        self.dependantModifiers[modifier.respath] = modifier

    def RemoveDependantModifier(self, modifier):
        if modifier.respath in self.dependantModifiers:
            del self.dependantModifiers[modifier.respath]

    def GetMeshSourcePaths(self):
        return [self.clothPath, self.redfile]

    def IsMeshDirty(self):
        """
        Returns True iff this modifier has dirty meshes
        """
        return self.__clothDirty or self.clothPath and not self.clothData or self.__cmpMeshes != self.meshes or any(map(lambda mesh: not (mesh.geometry and mesh.geometry.isGood), self.meshes))

    def IsMeshContainingModifier(self):
        """
        Returns True iff this modifier contains geometry
        """
        return any((self.meshes,
         self.clothData,
         self.clothPath,
         self.redfile))

    def IsBlendshapeModifier(self):
        """
        Returns True iff this modifier is a blendshape modifier.
        That is, its name represents a granny morph name and its weight is the
        blend factor for that morph target.
        """
        return self.categorie in pdDef.BLENDSHAPE_CATEGORIES

    def __repr__(self):
        """
        Return a better, more informative info about this instance.
        """
        s = 'BuildData instance, ID%s\n' % id(self)
        s = s + 'Name: [%s]\t Category: [%s]\t RedFile: [%s]\n' % (self.name, self.categorie, self.redfile)
        s = s + 'Dirty: [%s]\t Hidden: [%s]\t Respath: [%s]\t' % (self.IsDirty, self.IsHidden, self.GetResPath())
        return s

    def __hash__(self):
        return id(self)

    def getIsDirty(self):
        if self.__IsDirty:
            return True
        if self.lastVariation != self.currentVariation:
            return True
        if self.__cmpPatternData != self.patternData:
            return True
        if self.__cmpColorizeData != self._colorizeData:
            return True
        if self.__cmpSpecularColorData != self.specularColorData:
            return True
        if self.__cmpMeshes != self.meshes:
            return True
        if self.__cmpDecalData != self.decalData:
            return True
        return False

    def setIsDirty(self, value):
        """
        When the builddata set to not being dirty, reset the list copies
        used to monitor dirty changes in pattern and colorize data.
        """
        if value == False:
            self.__cmpColorizeData = list(self._colorizeData)
            self.__cmpSpecularColorData = list(self.specularColorData)
            self.__cmpPatternData = list(self.patternData)
            self.__cmpMeshes = list(self.meshes)
            if self.decalData is not None:
                self.__cmpDecalData = copy.deepcopy(self.decalData)
            else:
                self.__cmpDecalData = None
            self.lastVariation = self.currentVariation
            self.WasHidden = False
            self.WasShown = False
            self.__clothDirty = False
        else:
            self.__hashValue = None
            self._isTextureContainingModifier = None
            self._contributesToMapTypes = None
            self._affectedTextureParts = None
        self.__IsDirty = value

    IsDirty = property(fget=getIsDirty, fset=setIsDirty)

    def dirtDeco(fun):

        def new(*args):
            args[0].__IsDirty = True
            return fun(*args)

        return new

    colorizeData = property(fset=SetColorizeData, fget=GetColorizeData)

    @dirtDeco
    def setisHidden(self, value):
        self.WasShown = value and not self.__IsHidden
        self.WasHidden = not value and self.__IsHidden
        self.__IsHidden = value

    IsHidden = property(fget=lambda self: self.__IsHidden, fset=setisHidden)

    @property
    def clothData(self):
        return self.__clothData

    @clothData.setter
    def clothData(self, value):
        self.__clothDirty = True
        self.__clothData = value

    @dirtDeco
    def settuck(self, value):
        self.__tuck = value

    tuck = property(fget=lambda self: self.__tuck, fset=settuck)

    @dirtDeco
    def setpattern(self, value):
        self.__pattern = value

    pattern = property(fget=lambda self: self.__pattern, fset=setpattern)

    def setweight(self, value):
        """
        Setter for the weight. Computes weight pulse as a side effect.
        """
        if self.__weight == value:
            return
        if value > 0 and self.__weight <= 0:
            self.hasWeightPulse = True
        elif self.__weight > 0 and value <= 0:
            self.hasWeightPulse = True
        self.__weight = value
        self.__IsDirty = True

    weight = property(fget=lambda self: self.__weight, fset=setweight)

    @dirtDeco
    def setuseSkin(self, value):
        self.__useSkin = value

    useSkin = property(fget=lambda self: self.__useSkin, fset=setuseSkin)

    def GetTypeData(self):
        """
        Returns all the data needed to save this modifier as it is currently configured as a 
        type. A type links a modifier to a certain variation and a certain color variation.
        """
        return (self.respath, self.currentVariation, self.currentColorVariation)

    def ClearCachedData(self):
        del self.meshes[:]
        del self.__cmpMeshes[:]
        self.clothData = None
        self.meshGeometryResPaths = {}

    def GetResPath(self):
        return self.respath

    def GetFootPrint(self, preserveTypes = False, occlusionWeight = None):
        """
        Returns this modifier's contribution to a DNA.
        OcclusionWeight, if provided, is the value that this modifier's weight is currently occluded by
        and it has to be added to the modifier's weight to give correct serialization weight value.
        """
        colorsOutput = self.colorizeData if preserveTypes else str(self.colorizeData)
        colorsSource = self.colorizeData
        if self.pattern:
            colorsOutput = self.patternData if preserveTypes else str(self.patternData)
            colorsSource = self.patternData
        data = {}
        data[pdDef.DNA_STRINGS.PATH] = self.GetResPath()
        serializationWeight = self.weight if not occlusionWeight else self.weight + occlusionWeight
        data[pdDef.DNA_STRINGS.WEIGHT] = serializationWeight
        data[pdDef.DNA_STRINGS.CATEGORY] = self.categorie
        if colorsSource != BuildData.DEFAULT_COLORIZEDATA:
            data[pdDef.DNA_STRINGS.COLORS] = colorsOutput
        if self.specularColorData != BuildData.DEFAULT_SPECULARCOLORDATA:
            data[pdDef.DNA_STRINGS.SPECULARCOLORS] = self.specularColorData
        if self.pattern:
            data[pdDef.DNA_STRINGS.PATTERN] = self.pattern
        if self.decalData:
            data[pdDef.DNA_STRINGS.DECALDATA] = self.decalData
        if self.currentColorVariation:
            data[pdDef.DNA_STRINGS.COLORVARIATION] = self.currentColorVariation
        if self.currentVariation:
            data[pdDef.DNA_STRINGS.VARIATION] = self.currentVariation
        return data

    def CompareFootPrint(self, other):
        """
        Compares the footprint of this modifier with 'other'.
        'other' can be a footprint or a modifier instance.
        Returns 0 if footprints do not match for other keys than variation
        Returns 1 if footpritns match
        Returns -1 if footprints match on all keys except variation
        """
        if isinstance(other, BuildData):
            otherFP = other.GetFootPrint()
        else:
            otherFP = other

        def doCompare(sfp, ofp):
            ret = 1
            for k, v in sfp.iteritems():
                if ofp.get(k) != v:
                    if k != pdDef.DNA_STRINGS.VARIATION:
                        return 0
                    ret = -1

            return ret

        selfFP = self.GetFootPrint(preserveTypes=True)
        cmpResult = doCompare(selfFP, otherFP)
        if cmpResult < 1:
            selfFP = self.GetFootPrint(preserveTypes=False)
            cmpResult = doCompare(selfFP, otherFP)
        return cmpResult

    def Hash(self):
        return hash(self)


class BuildDataManager(object):
    """
    BuildDataManager manages a set of modifiers that define a doll.
    A single modifier is encapsulated in a single instance of BuildData.
    Each Doll instance has one BuildDataManager instance.
    
    The management revolves around ensuring that modifiers are only added or
    removed through the methods defined in this class.
    This allows for keeping tabs on dirty modifiers, that is, modifiers that
    have been added, changed or removed.
    Each modifier that is of type BuildData can also be marked as dirty.
    That happens when that modifier has any attribute changed that would require
    some handling when rebuilding the doll containing that modifier.
    Calls to Add/Remove modifier instantly modifies the internal set of modifiers.
    The client has to make provisions if he wants to operate say, on all modifiers
    as they were when this instance was last marked as non-dirty.
    To help facility that the client can call GetDirtyModifiers
    
    invariant:
        Count of modifiers as they were after last NotifyUpdateCall
        == Count of modifiers - added modifiers + removed notifiers
    
    When NotifiyUpdate() is called, all modifiers are marked as non-dirty
    and the list of dirty modifiers are emptied.
    
    This allows for add/remove/change operations on a doll to be intelligently
    handled when the doll needs to reflect its new setup.
    That happens when a call to Update() is done on a doll instance.
    
    Static relations:
        Doll -1> BuildDataManager -*> Category -*> BuildData
                 |List of                         |Dirty Flag
                    |-> Added/Removed/Dirty modifiers (BuildData)
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.BuildDataManager'

    def getmodifiers(self):
        """
        Property getter for modifiers data that is a dict of category keys, with modifier lists.
        Supports the ability to show and hide modifiers without removing them.
        """
        if self.__filterHidden:
            modifiersdata = {}
            for part in self.__modifiers.iterkeys():
                modifiers = [ modifier for modifier in self.__modifiers[part] if not modifier._BuildData__IsHidden ]
                modifiersdata[part] = modifiers

            return modifiersdata
        else:
            return self.__modifiers

    def setmodifiers(self, value):
        raise AttributeError('Cannot directly set modifiers!')

    modifiersdata = property(fget=getmodifiers, fset=setmodifiers)

    def __del__(self):
        del self.__sortedList
        del self.__dirtyModifiersAdded
        del self.__dirtyModifiersRemoved
        del self.__modifiers

    def __init__(self):
        object.__init__(self)
        self.__modifiers = {pdDef.DOLL_PARTS.BODY: [],
         pdDef.DOLL_PARTS.HEAD: [],
         pdDef.DOLL_PARTS.HAIR: [],
         pdDef.DOLL_PARTS.ACCESSORIES: [],
         pdDef.DOLL_EXTRA_PARTS.BODYSHAPES: [],
         pdDef.DOLL_EXTRA_PARTS.UTILITYSHAPES: [],
         pdDef.DOLL_EXTRA_PARTS.UNDEFINED: []}
        self.desiredOrder = pdDef.DESIRED_ORDER[:]
        self.desiredOrderChanged = False
        self.__sortedList = []
        self.__dirty = False
        self.modifierLimits = {}
        self.occludeRules = {}
        self.__dirtyModifiersAdded = []
        self.__dirtyModifiersRemoved = []
        self.currentLOD = pdDef.LOD_0
        self.__locked = False
        self.__pendingModifiersToAdd = []
        self.__pendingModifiersToRemove = []
        self.__filterHidden = True
        self._parentModifiers = {}

    def AddBlendshapeLimitsFromFile(self, resPath):
        """
        Sets the limits for blendshapes by reading a limitations file generated by 
        the BlendshapeLimiting Editor
        """
        data = ModifierLoader.LoadBlendshapeLimits(resPath)
        if data:
            limits = data['limits']
            self.AddModifierLimits(limits)

    def AddModifierLimits(self, modifierLimits):
        """
        'modifierLimits' is a dictionary, key is modifier name, value is a tuple (min, max)
        Will override any existing limits for the keys in 'modifierLimits'.
        ModifierLimits limits the weight value a modifier can have, which is in the range [0, 1] when unlimited.
        """
        self.modifierLimits.update(modifierLimits)

    def ApplyLimitsToModifierWeights(self):
        """
        Applies limits set in self.modifierLimits to all modifiers if they are limited there.
        """
        for modifier in self.GetModifiersAsList(includeFuture=True, showHidden=True):
            limit = self.modifierLimits.get(modifier.name)
            if limit:
                minLimit, maxLimit = limit
                modifier.weight = min(max(minLimit, modifier.weight), maxLimit)

    def GetMorphTargets(self):
        """
        Returns valid morphtargets based on the current state of the modifiers.
        """
        modifierList = self.GetModifiersAsList()
        removedModifiers = list(self.__dirtyModifiersRemoved)
        morphTargets = {}

        def Qualifier(modifier):
            return modifier.IsBlendshapeModifier()

        for modifier in iter(removedModifiers):
            if Qualifier(modifier):
                morphTargets[modifier.name] = 0

        for modifier in iter(modifierList):
            if Qualifier(modifier):
                weight = modifier.weight if modifier.weight < 1.0 else 1.0
                limit = self.modifierLimits.get(modifier.name)
                if limit:
                    minLimit, maxLimit = limit
                    weight = min(max(minLimit, weight), maxLimit)
                morphTargets[modifier.name] = weight

        return morphTargets

    def AddParentModifier(self, modifier, parentModifier):
        parentModifiers = self.GetParentModifiers(modifier)
        if parentModifier not in parentModifiers:
            parentModifiers.append(parentModifier)
        self._parentModifiers[modifier] = parentModifiers

    def GetParentModifiers(self, modifier):
        return self._parentModifiers.get(modifier, [])

    def RemoveParentModifier(self, modifier, dependantModifier = None):
        if dependantModifier:
            parentModifiers = self.GetParentModifiers(dependantModifier)
            if modifier in parentModifiers:
                parentModifiers.remove(modifier)
        else:
            for parentModifiers in self._parentModifiers.itervalues():
                if modifier in parentModifiers:
                    parentModifiers.remove(modifier)

    def GetSoundTags(self):
        """
        Returns a distinct list of all soundtags for all modifiers.
        """
        soundTags = []
        for modifier in iter(self.GetSortedModifiers()):
            soundTag = modifier.metaData.soundTag
            if soundTag and soundTag not in soundTags:
                soundTags.append(soundTag)

        return soundTags

    def Lock(self):
        """
        Locks the instance so all calls to Add or Remove modifiers will not be serviced, but instead
        the incoming modifiers will be put aside into lists for later addition and removal
        """
        self.__locked = True

    def UnLock(self):
        """
        Unlocks the instance, this will immediately perform add and remove operations on pending
        modifiers and then clear all pending modifiers.
        """
        self.__locked = False
        for modifier in self.__pendingModifiersToRemove:
            self.RemoveModifier(modifier)

        self.__pendingModifiersToRemove = []
        for modifier in self.__pendingModifiersToAdd:
            self.AddModifier(modifier)

        self.__pendingModifiersToAdd = []

    def HashForMaps(self, hashableElements = None):
        """        
        Returns a unique integer computed from the modifiers in such a way
        that any sets of modifiers that would result in compositing out the same
        textures return the same integer value.
        
        'hashableElements' is a list of elements that provide additional constraints
        for the hashing function. The user must make sure that str(x) where x is an
        element in hashableElements gives a clear representation of x.
        """
        hasher = hashlib.md5()
        if hashableElements:
            for he in iter(hashableElements):
                hasher.update(str(he))

        for part, modifiers in self.modifiersdata.iteritems():
            hasher.update(part)
            for modifier in iter(modifiers):
                if not (modifier.IsTextureContainingModifier() or modifier.metaData.hidesBootShin or modifier.metaData.forcesLooseTop or modifier.metaData.swapTops or modifier.metaData.swapBottom or modifier.metaData.swapSocks):
                    continue
                modString = '{0}{1}{2}{3}{4}{5}{6}{7}{8}{9}'.format(modifier.name, modifier.categorie, modifier.weight, modifier.colorizeData, modifier.specularColorData, modifier.pattern, modifier.patternData, modifier.decalData, modifier.useSkin, modifier.variationTextureHash)
                if modifier.metaData.hidesBootShin or modifier.metaData.forcesLooseTop or modifier.metaData.swapTops or modifier.metaData.swapBottom or modifier.metaData.swapSocks:
                    modString = '{0}{1}{2}'.format(modString, modifier.metaData.hidesBootShin, modifier.metaData.forcesLooseTop, modifier.metaData.swapTops, modifier.metaData.swapBottom, modifier.metaData.swapSocks)
                hasher.update(modString)

            pdCF.BeFrameNice()

        return hasher.hexdigest()

    def GetDirtyModifiers(self, changedBit = False, addedBit = False, removedBit = False, getWeightless = True):
        """
        Default: 
            Returns a reference to modifiers that have been added, 
            removed or changed since last call to NotifyUpdate()
            These modifiers are sorted using SortParts()
            
        If any of the bit flags are toggled, only those kinds of modifiers are returned.
            
        If changedBit:
            Modifiers flagged as dirty are returned, these modifiers have not been removed or added.
            Basically, all builddata instances that return True for IsDirty
            
        If addedBit:
            Modifiers added since last call to update are returned.
            
        If removedBit:
            Modifiers that have been removed since last call to update are returned.
        
        """
        ret = list()
        masking = changedBit or addedBit or removedBit
        if addedBit or not masking:
            if getWeightless:
                ret.extend(self.__dirtyModifiersAdded)
            else:
                ret.extend((modifier for modifier in self.__dirtyModifiersAdded if modifier.weight > 0))
        if removedBit or not masking:
            if getWeightless:
                ret.extend(self.__dirtyModifiersRemoved)
            else:
                ret.extend((modifier for modifier in self.__dirtyModifiersRemoved if modifier.weight > 0))
        if changedBit or not masking:
            self.__filterHidden = False
            changedModifiers = []
            for modifiers in self.modifiersdata.itervalues():
                if getWeightless:
                    changedModifiers.extend((modifier for modifier in modifiers if modifier.IsDirty and modifier not in self.__dirtyModifiersAdded))
                else:
                    changedModifiers.extend((modifier for modifier in modifiers if modifier.IsDirty and modifier.weight > 0 and modifier not in self.__dirtyModifiersAdded))

            self.__filterHidden = True
            for modifier in changedModifiers:
                if modifier not in ret:
                    ret.append(modifier)

        ret = self.SortParts(ret)
        return ret

    @telemetry.ZONE_METHOD
    def NotifyUpdate(self):
        """
        Called to notify this instance that modifer data has been used to 
        apply updates to a paperdoll instance and all changes should be 
        monitored from current state.
        """
        del self.__dirtyModifiersAdded[:]
        for modifier in iter(self.__dirtyModifiersRemoved):
            modifier.ClearCachedData()

        del self.__dirtyModifiersRemoved[:]
        for modifier in iter(self.GetModifiersAsList(showHidden=True)):
            modifier.IsDirty = False

        self.desiredOrderChanged = False
        self.__dirty = False

    def SetAllAsDirty(self, clearMeshes = False):
        """
        Marks all modifiers as being dirty.
        Even if they're dirty, they're not reloading the redfile unless it has changed; this is "too smart" for
        overridelod, which needs a reload. In that case, clear out the meshes as well.
        """
        for part in self.modifiersdata.iterkeys():
            for modifier in self.modifiersdata[part]:
                modifier.IsDirty = True
                if clearMeshes:
                    modifier.ClearCachedData()

        self.__dirty = True

    def SetLOD(self, newLod):
        """
        Sets the current LOD. The current LOD is used for modifier LOD occlusion.
        When the function is called, all current modifiers that should be hidden at this LOD get
        marked as hidden.
        All hidden modifiers that should be visible become visible.
        It is assumed that this function is called when the LOD is set on the doll. As with all other
        changes to the datamodel, nothing is submitted to the visual model until Update has been called
        on the doll.
        """
        self.currentLOD = newLod
        modifiers = self.GetModifiersAsList(showHidden=True)
        for modifier in modifiers:
            if not modifier.IsVisibleAtLOD(self.currentLOD):
                self.HideModifier(modifier)
            elif modifier.IsHidden:
                self.ShowModifier(modifier)

    def RemoveMeshContainingModifiers(self, category, privilegedCaller = False):
        """
        Removes all modifiers containing any meshes belonging to the given 'category'
        """
        for modifier in self.GetModifiersByCategory(category):
            if modifier.IsMeshContainingModifier() and not self.GetParentModifiers(modifier):
                self.RemoveModifier(modifier, privilegedCaller=privilegedCaller)

    def AddModifier(self, modifier, privilegedCaller = False):
        """
        Handles the addition of a 'modifier' of type BuildData
        If the modifier already exists but is hidden, it will not be added, it will only be shown.
        'privilegedCaller' when true, will be allow to AddModifier despite BuildDataManager 
        being locked for edits.
        """
        if self.__locked and not privilegedCaller:
            self.__pendingModifiersToAdd.append(modifier)
        else:
            part = self.CategoryToPart(modifier.categorie)
            for existingModifier in iter(self.__modifiers[part]):
                if existingModifier.respath == modifier.respath:
                    if existingModifier.IsVisibleAtLOD(self.currentLOD):
                        if existingModifier.IsHidden:
                            self.ShowModifier(existingModifier)
                    else:
                        self.HideModifier(existingModifier)
                    if modifier.weight > existingModifier.weight:
                        existingModifier.weight = modifier.weight
                        self.ApplyOccludeRules(existingModifier)
                    return

            if not modifier.IsVisibleAtLOD(self.currentLOD):
                self.HideModifier(modifier)
            self.ApplyOccludeRules(modifier)
            if modifier.weight > 0:
                if modifier.categorie == pdDef.BODY_CATEGORIES.TOPOUTER:
                    self.RemoveMeshContainingModifiers(pdDef.BODY_CATEGORIES.TOPINNER, privilegedCaller=privilegedCaller)
                elif modifier.categorie == pdDef.BODY_CATEGORIES.BOTTOMOUTER:
                    self.RemoveMeshContainingModifiers(pdDef.BODY_CATEGORIES.BOTTOMINNER, privilegedCaller=privilegedCaller)
                if modifier.IsMeshContainingModifier() and modifier.categorie not in (pdDef.DOLL_PARTS.ACCESSORIES, pdDef.DOLL_EXTRA_PARTS.DEPENDANTS):
                    self.RemoveMeshContainingModifiers(modifier.categorie, privilegedCaller=privilegedCaller)
            self.OccludeModifiersByModifier(modifier)
            self.__dirtyModifiersAdded.append(modifier)
            resPaths = modifier.GetDependantModifierResPaths()
            if resPaths:
                for resPath in iter(resPaths):
                    dependantModifier = self.GetModifierByResPath(resPath)
                    if dependantModifier:
                        modifier.AddDependantModifier(dependantModifier)
                        self.AddParentModifier(dependantModifier, modifier)

            for dependantModifier in iter(modifier.GetDependantModifiers()):
                self.AddModifier(dependantModifier, privilegedCaller=privilegedCaller)
                self.AddParentModifier(dependantModifier, modifier)

            if modifier in self.__dirtyModifiersRemoved:
                self.__dirtyModifiersRemoved.remove(modifier)
            self.__modifiers[part].append(modifier)
            self.__dirty = True

    def OccludeModifiersByModifier(self, modifier):
        """
        Performs occluding of existing modifiers and adds this modifier's occluding values to 
        self.occludeRules
        Modifiers are occluded by subtracting weight values from them, if it goes to 0 or below, they
        are removed and put aside in in a list of occluded modifiers, otherwise, their weight values are simply
        adjusted.
        """
        occludeData = modifier.GetOccludedModifiersFullData()
        if occludeData:
            for resPath, weightSubtraction in occludeData:
                self.UpdateOccludeRule(resPath, weightSubtraction)
                occlusionTargets = []
                if pdDef.SEPERATOR_CHAR not in resPath:
                    occlusionTargets.extend(self.GetModifiersByCategory(resPath))
                elif resPath.count(pdDef.SEPERATOR_CHAR) == 1 and resPath.split(pdDef.SEPERATOR_CHAR)[0] in pdDef.CATEGORIES_CONTAINING_GROUPS:
                    category, group = resPath.split(pdDef.SEPERATOR_CHAR)[:2]
                    groupCandidateModifiers = self.GetModifiersByCategory(category)
                    for groupCandidateModifier in groupCandidateModifiers:
                        if group == groupCandidateModifier.group:
                            occlusionTargets.append(groupCandidateModifier)

                else:
                    targetToOcclude = self.GetModifierByResPath(resPath, includeFuture=True)
                    if targetToOcclude:
                        occlusionTargets.append(targetToOcclude)
                for targetToOcclude in occlusionTargets:
                    targetToOcclude.weight -= weightSubtraction

    def GetOcclusionWeight(self, modifier):
        """
        Returns the total weight that occlusion rules state the given modifier should be occluded by
        """
        occlusionWeight = 0
        for resPath in self.occludeRules.iterkeys():
            if resPath in modifier.respath:
                occlusionWeight += self.occludeRules[resPath]

        return occlusionWeight

    def ApplyOccludeRules(self, modifier):
        """
        This method is called on incoming modifiers so they adhere to the current occluding state
        which is made up of all the current modifiers that occlude.
        """
        modifier.weight -= self.GetOcclusionWeight(modifier)

    def IsCategoryOccluded(self, category):
        """
        Checks the given category against occlusion rules and returns True if the given category
        is being completely occluded.
        """
        for resPath, weight in self.occludeRules.iteritems():
            if weight >= 1.0 and resPath == category:
                return True

        return False

    def UpdateOccludeRule(self, resPath, weight):
        occludeRule = self.occludeRules.get(resPath, 0)
        occludeRule += weight
        if occludeRule <= 0.0:
            try:
                del self.occludeRules[resPath]
            except KeyError:
                pass

        else:
            self.occludeRules[resPath] = occludeRule

    def ReverseOccludeModifiersByModifier(self, modifier, useVariation = None):
        """
        Reverses occluding of existing modifiers and removes this modifier's occluding values from
        self.occludeRules        
        """
        occludeData = None
        if useVariation is not None:
            metaData = modifier.GetVariationMetaData(useVariation)
            occludeData = modifier.GetOccludedModifiersFullData(metaData)
        else:
            occludeData = modifier.GetOccludedModifiersFullData()
        if occludeData:
            for resPath, weightSubtraction in occludeData:
                self.UpdateOccludeRule(resPath, -weightSubtraction)
                modifiersToReverseOcclude = []
                if pdDef.SEPERATOR_CHAR not in resPath:
                    for occludedModifier in self.GetModifiersByCategory(resPath):
                        modifiersToReverseOcclude.append(occludedModifier)

                elif resPath.count(pdDef.SEPERATOR_CHAR) == 1 and resPath.split(pdDef.SEPERATOR_CHAR)[0] in pdDef.CATEGORIES_CONTAINING_GROUPS:
                    category, group = resPath.split(pdDef.SEPERATOR_CHAR)[:2]
                    groupCandidateModifiers = self.GetModifiersByCategory(category)
                    for groupCandidateModifier in groupCandidateModifiers:
                        if group == groupCandidateModifier.group:
                            modifiersToReverseOcclude.append(groupCandidateModifier)

                else:
                    occludedModifier = self.GetModifierByResPath(resPath)
                    if occludedModifier:
                        modifiersToReverseOcclude.append(occludedModifier)
                for target in modifiersToReverseOcclude:
                    oldWeight = target.weight
                    target.weight += weightSubtraction
                    if oldWeight <= 0 and target.weight > 0:
                        self.AddModifier(target, privilegedCaller=True)

    def RemoveModifier(self, modifier, privilegedCaller = False, occludingCall = False):
        """
        Handles the removal of a 'modifier'
        'privilegedCaller' when true, will be allow to RemoveModifier despite BuildDataManager 
        being locked for edits.
        """
        if self.__locked and not privilegedCaller:
            self.__pendingModifiersToRemove.append(modifier)
        else:
            if self.GetParentModifiers(modifier) and not occludingCall:
                log.LogWarn('paperDoll::BuildDataManager::RemoveModifier - Attempting to remove a modifier that has parent modifiers', modifier)
                return
            if modifier in self.__dirtyModifiersRemoved:
                return
            part = self.CategoryToPart(modifier.categorie)
            if modifier in self.__modifiers[part]:
                self.__modifiers[part].remove(modifier)
            if modifier in self.__dirtyModifiersAdded:
                self.__dirtyModifiersAdded.remove(modifier)
            self.__dirtyModifiersRemoved.append(modifier)
            replacementPaths = (modifier.metaData.lod1Replacement, modifier.metaData.lod2Replacement)
            for replacementPath in replacementPaths:
                if replacementPath:
                    lodReplacementModifier = self.GetModifierByResPath(replacementPath)
                    if lodReplacementModifier:
                        self.RemoveModifier(lodReplacementModifier)

            self.ReverseOccludeModifiersByModifier(modifier)
            self.RemoveParentModifier(modifier)
            for dependantModifier in iter(modifier.GetDependantModifiers()):
                parentModifiers = self.GetParentModifiers(dependantModifier)
                if parentModifiers:
                    dependantModifier.weight = 0
                    for modifier in iter(parentModifiers):
                        for entry in modifier.GetDependantModifiersFullData():
                            if entry[0] == dependantModifier.respath and entry[3] > dependantModifier.weight:
                                dependantModifier.weight = entry[3]

                    self.ApplyOccludeRules(dependantModifier)
                if occludingCall or len(parentModifiers) == 0:
                    self.RemoveModifier(dependantModifier, privilegedCaller=privilegedCaller)

            self.__dirty = True

    def SetModifiersByCategory(self, category, modifiers, privilegedCaller = False):
        """
        Sets modifiers of category 'category' to 'modifiers'.
        'modifiers' must be a list of builddata instances or a single builddata instance.
        """
        self.__dirty = True
        if type(modifiers) == BuildData:
            modifiers = [modifiers]
        removeModifiers = self.GetModifiersByCategory(category)
        for modifier in iter(removeModifiers):
            self.RemoveModifier(modifier, privilegedCaller=privilegedCaller)

        for modifier in iter(modifiers):
            self.AddModifier(modifier, privilegedCaller=privilegedCaller)

    def GetModifiersByCategory(self, category, showHidden = False, includeFuture = False):
        """
        Returns list of all the modifers in a given category
        If the category is non-existent, returns an empty list.
        'category' is the category to filter modifiers by.
        'showHidden' when set to True, will also return modifiers marked
        as hidden.
        'includeFuture' if True, will prepend pending modifiers for addition to the data
        """
        filterHiddenState = self.__filterHidden
        if showHidden:
            self.__filterHidden = False
        part = self.CategoryToPart(category)
        modifiers = self.modifiersdata.get(part, [])
        modifiers = [ modifier for modifier in modifiers if modifier.categorie == category ]
        if includeFuture:
            for modifier in self.__pendingModifiersToAdd:
                if modifier.categorie == category:
                    modifiers.insert(0, modifier)

        self.__filterHidden = filterHiddenState
        return modifiers

    def GetModifiersByPart(self, part, showHidden = False):
        """
        Returns list of all the modifers for a given part
        If the part is non-existent, returns an empty list.
        'showHidden' when set to True, will also return modifiers marked
        as hidden.
        """
        filterHiddenState = self.__filterHidden
        if showHidden:
            self.__filterHidden = False
        modifiers = self.modifiersdata.get(part, [])
        self.__filterHidden = filterHiddenState
        return modifiers

    def GetModifierByResPath(self, resPath, includeFuture = False, showHidden = False):
        for modifier in self.GetModifiersAsList(includeFuture=includeFuture, showHidden=showHidden):
            if modifier.respath == resPath:
                return modifier

    def GetMeshSourcePaths(self, modifiers = None):
        """
        Traverses 'modifiers' or all current modifiers in the buildDataManager and collects
        their clothPath and redfile values if any.
        Returns a list of those values
        """
        meshSourcePaths = list()
        if modifiers is None:
            modifiers = self.GetSortedModifiers()
        for modifier in iter(modifiers):
            meshSourcePaths.extend(modifier.GetMeshSourcePaths())

        while None in meshSourcePaths:
            meshSourcePaths.remove(None)

        while '' in meshSourcePaths:
            meshSourcePaths.remove('')

        return meshSourcePaths

    def GetMapsToComposite(self, modifiers = None):
        """
        Returns a distinct set of the mapTypes that the modifiers will contribute to.
        """
        mapTypes = set()
        if modifiers is None:
            modifiers = self.GetSortedModifiers()
        modGenerator = (modifier for modifier in iter(modifiers) if modifier.weight > 0)
        for modifier in modGenerator:
            mapTypes.update(modifier.ContributesToMapTypes())

        return mapTypes

    def GetPartsFromMaps(self, modifiers = None):
        """
        Returns a distinct list of those parts in modifiers that exist in the modifiers
        mapX dictionaries as keys. This is used to determine what texture areas need to be
        recomposited.
        """
        parts = set()
        if modifiers is None:
            modifiers = self.GetSortedModifiers()
        modGenerator = (modifier for modifier in iter(modifiers) if modifier.weight > 0)
        for modifier in modGenerator:
            parts.update(modifier.GetAffectedTextureParts())

        return list(parts)

    def GetParts(self, modifiers = None):
        """
        Returns a distinct list of those parts that are in 'modifiers'
        or contained in BuildDataManager if none are provied.        
        """
        parts = set()
        if modifiers is None:
            modifiers = self.GetSortedModifiers()
        for modifier in iter(modifiers):
            part = self.CategoryToPart(modifier.categorie)
            parts.add(part)

        return list(parts)

    def HideModifiersByCategory(self, category):
        for modifier in self.GetModifiersByCategory(category):
            self.HideModifier(modifier)

    def HideModifiersByPart(self, part):
        for modifier in self.GetModifiersByPart(part):
            self.HideModifier(modifier)

    def HideModifier(self, modifier):
        """
        Hides a modifier, marks BDM as dirty and adds the hidden modifier to the list of removed
        modifiers, although it isn't actually removed.
        """
        self.__dirty = True
        modifier.IsHidden = True
        self.__dirtyModifiersRemoved.append(modifier)
        if modifier in self.__dirtyModifiersAdded:
            self.__dirtyModifiersAdded.remove(modifier)

    def ShowModifiersByCategory(self, category):
        self.__filterHidden = False
        for modifier in self.GetModifiersByCategory(category):
            self.ShowModifier(modifier)

        self.__filterHidden = True

    def ShowModifiersByPart(self, part):
        self.__filterHidden = False
        for modifier in self.GetModifiersByPart(part):
            self.ShowModifier(modifier)

        self.__filterHidden = True

    def ShowModifier(self, modifier):
        """
        Shows a modifier, marks BDM as dirty and adds the previously hidden modifier to the list of
        added modifiers
        """
        self.__dirty = True
        modifier.IsHidden = False
        self.__dirtyModifiersAdded.append(modifier)
        if modifier in self.__dirtyModifiersRemoved:
            self.__dirtyModifiersRemoved.remove(modifier)

    def GetHiddenModifiers(self):
        """
        Returns all modifiers currently hidden
        """
        self.__filterHidden = False
        modifiers = []
        for modifier in iter(self.GetModifiersAsList()):
            if modifier.IsHidden:
                modifiers.append(modifier)

        self._filterHidden = True
        return modifiers

    def GetBodyModifiers(self, remapToPart = False):
        """
        Returns all modifiers for body
        """
        return self.GetModifiersByPart(pdDef.DOLL_PARTS.BODY)

    def GetHeadModifiers(self, remapToPart = False):
        """
        Returns all modifiers for head, if remapToPart is set to true, it will remap all categories
        according to CategoryToPart, filtered for head.
        """
        category = pdDef.DOLL_PARTS.HEAD
        if remapToPart:
            category = self.CategoryToPart(category, pdDef.DOLL_PARTS.HEAD)
        return self.GetModifiersByCategory(category)

    def GetHairModifiers(self, remapToPart = False):
        """
        Returns all modifiers for hair, if remapToPart is set to true, it will remap all categories
        according to CategoryToPart, filtered for hair.
        """
        category = pdDef.DOLL_PARTS.HAIR
        if remapToPart:
            category = self.CategoryToPart(category, pdDef.DOLL_PARTS.HAIR)
        return self.GetModifiersByCategory(category)

    def GetAccessoriesModifiers(self, remapToPart = False):
        """
        Returns all modifiers for accessories, if remapToPart is set to true, 
        it will remap all categories according to CategoryToPart, filtered for accessories.
        """
        category = pdDef.DOLL_PARTS.ACCESSORIES
        if remapToPart:
            category = self.CategoryToPart(category, pdDef.DOLL_PARTS.ACCESSORIES)
        return self.GetModifiersByCategory(category)

    def GetModifiersAsList(self, includeFuture = False, showHidden = False):
        """
        Returns all the modifiers kept in this manager as a single list.
        This does not guarantee the list being sorted. 
        Call GetSortedModifiers for a sorted list.
        """
        filterHiddenState = self.__filterHidden
        if showHidden:
            self.__filterHidden = False
        ret = []
        if includeFuture:
            ret = list(self.__pendingModifiersToAdd)
        for each in self.modifiersdata.itervalues():
            ret.extend(each)

        self.__filterHidden = filterHiddenState
        return ret

    @telemetry.ZONE_METHOD
    def GetSortedModifiers(self, showHidden = False, includeFuture = False):
        """
        Returns the data in self.modifiers as a list, sorted according to self.desiredOrder
        Relies on internal caching mechanism, all changes to modifiers data should be done through
        methods in order to flag changes appropoiately as dirty.
        """
        if showHidden:
            modifiers = self.SortParts(self.GetModifiersAsList(includeFuture=includeFuture, showHidden=True))
            return modifiers
        if self.__dirty or not self.__sortedList:
            self.__sortedList = self.SortParts(self.GetModifiersAsList())
        if includeFuture:
            ret = list(self.__pendingModifiersToAdd)
            ret.extend(self.__sortedList)
        return list(self.__sortedList)

    def _SortPartFunc(self, modifier, dso):
        try:
            dsoIdx = dso.index(modifier.categorie) * 1000
            groups = pdDef.GROUPS.get(modifier.categorie, [])
            try:
                subIdx = groups.index(modifier.group)
            except ValueError:
                subIdx = 999

            dsoIdx += subIdx
        except ValueError:
            dsoIdx = -1

        return dsoIdx

    def SortParts(self, modifiersList):
        """
        Takes a list of modifiers and returns a new list, sorted according to self.desiredOrder
        """
        dso = self.desiredOrder
        retList = list(modifiersList)
        retList.sort(key=lambda x: self._SortPartFunc(x, dso))
        return retList

    def ChangeDesiredOrder(self, categoryA, categoryB):
        """
        Changes desired order by swapping categoryA with categoryB __iff B is before A__
        If no swapping is done, we do not have a state change.
        When state changes, texture compositing is impacted as is the sorting order of modifiers.
        """
        aIdx = self.desiredOrder.index(categoryA)
        bIdx = self.desiredOrder.index(categoryB)
        if aIdx > bIdx:
            self.desiredOrderChanged = True
            self.__sortedList = None
            self.desiredOrder[bIdx], self.desiredOrder[aIdx] = self.desiredOrder[aIdx], self.desiredOrder[bIdx]

    def GetMeshes(self, part = None, alternativeModifierList = None, includeClothMeshes = False):
        """
        Returns all meshes kept in modifiers or only those that are for the specific 'part'
        If 'alternativeModifierList' is passed, searches only that list instead of the default
        internal modifier data.
        If 'part' and 'alternativeModifierList' are both None, returns all meshes for all modifiers.
        if 'includeClothMeshes' is True, returns also all cloth specific meshes
        """
        meshes = []
        parts = [part] if part else pdDef.DOLL_PARTS

        def CollectMeshsFrom(fromIter):
            for each in iter(fromIter):
                if each.weight > 0:
                    if part in (None, self.CategoryToPart(each.categorie)):
                        for mesh in iter(each.meshes):
                            meshes.insert(0, mesh)

                        if includeClothMeshes and each.clothData:
                            meshes.insert(0, each.clothData)

        if alternativeModifierList is not None:
            CollectMeshsFrom(alternativeModifierList)
        elif part is not None:
            for p in parts:
                CollectMeshsFrom(self.GetModifiersByPart(p))

        else:
            CollectMeshsFrom(self.GetSortedModifiers())
        return list(meshes)

    def RemapMeshes(self, destinationMeshes):
        """
        Goes through all modifiers and makes their meshes point to meshes in destionationMeshes.
        
        This is used when working on a visual model behind the scenes, since when a copy is made
        of one visualModel, all the meshes in the modifiers are still pointing to the meshes in the
        original visualModel.
        """
        for modifier in iter(self.GetModifiersAsList()):
            for mesh in iter(modifier.meshes):
                for destMesh in iter(destinationMeshes):
                    if mesh.name == destMesh.name:
                        mesh = destMesh
                        break

    def CategoryToPart(self, category, partFilter = None):
        """
        Converts a category to doll part, return that part that a category belongs to.
        If the category passed is already a doll part, returns that party.
        Doll parts are defined in DOLL_PARTS
        
        If partFilter is defined (needs to be in DOLL_PARTS), only that part
        is checked, otherwise return 'category'
        
        Returns value of DOLL_EXTRA_PARTS.UNDEFINED as the fallthrough option.
        """
        if category in pdDef.DOLL_PARTS:
            return category
        if category in pdDef.BODY_CATEGORIES and partFilter in (None, pdDef.DOLL_PARTS.BODY):
            return pdDef.DOLL_PARTS.BODY
        if category in pdDef.HEAD_CATEGORIES and partFilter in (None, pdDef.DOLL_PARTS.HEAD):
            return pdDef.DOLL_PARTS.HEAD
        if category in pdDef.HAIR_CATEGORIES and partFilter in (None, pdDef.DOLL_PARTS.HAIR):
            return pdDef.DOLL_PARTS.HAIR
        if category in pdDef.ACCESSORIES_CATEGORIES and partFilter in (None, pdDef.DOLL_PARTS.ACCESSORIES):
            return pdDef.DOLL_PARTS.ACCESSORIES
        if category in pdDef.DOLL_EXTRA_PARTS.BODYSHAPES:
            return pdDef.DOLL_EXTRA_PARTS.BODYSHAPES
        if category in pdDef.DOLL_EXTRA_PARTS.UTILITYSHAPES:
            return pdDef.DOLL_EXTRA_PARTS.UTILITYSHAPES
        if category in pdDef.DOLL_EXTRA_PARTS.DEPENDANTS:
            return pdDef.DOLL_PARTS.BODY
        return pdDef.DOLL_EXTRA_PARTS.UNDEFINED


exports = {'paperDoll.SaveMapsToDisk': SaveMapsToDisk,
 'paperDoll.ClearAllCachedMaps': ClearAllCachedMaps,
 'paperDoll.FindCachedMap': FindCachedMap}
