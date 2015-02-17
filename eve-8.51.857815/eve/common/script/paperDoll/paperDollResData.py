#Embedded file name: eve/common/script/paperDoll\paperDollResData.py
"""
PaperDoll ResData. 
This module contains the in-memory view & business rules of paperDoll assets.
The reason for that is to frontload processing that is only needed once per runtime, instead of doing some of the work multiple times per
each character assembly.
"""
import uthread
import log
import telemetry
import walk
import weakref
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollCommonFunctions as pdCf
from .yamlPreloader import LoadYamlFileNicely

class SourceGeo(object):
    """
    This class is responsible for mapping the same geometry accross its LODs
    """
    __guid__ = 'paperDoll.resData.SourceGeo'

    def __init__(self, geoBase):
        self.geoBase = geoBase
        self.geoLod0 = None
        self.geoLod1 = None
        self.geoLod2 = None
        self.geoLod3 = None
        self.geoLodA = geoBase

    def __getitem__(self, idx):
        if idx == -1:
            return self.geoLodA
        if idx == 0:
            return self.geoLod0
        if idx == 1:
            return self.geoLod1
        if idx == 2:
            return self.geoLod2
        if idx == 3:
            return self.geoLod3
        raise AttributeError()

    def SetItemBySuffix(self, suffix, value, ext):
        if ext:
            if suffix == pdDef.GEO_SUFFIX_LOD0:
                self.geoLod0 = value
            elif suffix == pdDef.GEO_SUFFIX_LOD1:
                self.geoLod1 = value
            elif suffix == pdDef.GEO_SUFFIX_LOD2:
                self.geoLod2 = value
            elif suffix == pdDef.GEO_SUFFIX_LOD3:
                self.geoLod3 = value
            elif suffix in (pdDef.GEO_SUFFIX_LODA, None):
                self.geoLodA = value

    def __repr__(self):
        r = []
        for k, v in self.__dict__.iteritems():
            if 'geo' in k and v:
                r.append(v)

        return ','.join(r)


class SourceMap(object):
    """
    This class is responsible for mapping the same source texture accross its different source
    resolutions. During compositing, we require different source resolutions based on the final composited
    image's width and height.
    """
    __guid__ = 'paperDoll.resData.SourceMap'

    def __init__(self, mapBase):
        self.mapBase = mapBase
        self.map4k = None
        self.map512 = None
        self.map256 = None

    def SetItemBySuffix(self, suffix, value, ext):
        """
        Sets the filename to load for the given suffix which represents a source quality level.
        """
        if suffix == pdDef.MAP_SUFFIX_4K:
            ptr = 'map4k'
        elif suffix == pdDef.MAP_SUFFIX_512:
            ptr = 'map512'
        elif suffix == pdDef.MAP_SUFFIX_256:
            ptr = 'map256'
        elem = getattr(self, ptr)
        if not (elem and ext == pdDef.MAP_FORMAT_PNG):
            setattr(self, ptr, value)

    def __getitem__(self, width):
        if width <= 256:
            return self.map256 or self.map512 or self.mapBase
        if width <= 512:
            return self.map512 or self.mapBase
        if width < 4096:
            return self.mapBase
        if width >= 4096:
            return self.map4k or self.mapBase
        raise AttributeError()

    def __repr__(self):
        r = []
        for k, v in self.__dict__.iteritems():
            if 'map' in k and v:
                r.append(v)

        return ','.join(r)


class Entry(object):
    """
    Entry - ResDataEntry, represents a folder. If it contains files, it represents a source asset.
    """
    __guid__ = 'paperDoll.resData.Entry'

    def __init__(self, gender, root, respath, dirs, files):
        self.gender = gender
        self.root = root
        self.respath = respath
        self.leafFolderName = respath.split(pdDef.SEPERATOR_CHAR)[-1]
        self.depth = respath.count(pdDef.SEPERATOR_CHAR)
        self.dirs = []
        self.files = []
        self.sourceMaps = {}
        self.sourceGeos = {}
        self.extToFiles = {}
        self.redFiles = {}
        self.siblings = set()
        for directory in dirs:
            self.dirs.append(str(directory).lower())

        for f in files:
            fname = str(f).lower()
            self.files.append(fname)
            fnSplit = fname.split('.')
            if len(fnSplit) > 1:
                ext = fnSplit[-1]
                pdCf.AddToDictList(self.extToFiles, ext, fname)

        lodCutoff = None
        cutOffFn = self.extToFiles.get('lr', [None])[0]
        if cutOffFn:
            lodCutoff = int(cutOffFn.split('.')[0][1:])
        self.lodCutoff = lodCutoff
        self.MapLODSourceData(SourceMap, self.sourceMaps, pdDef.MAP_SIZE_SUFFIXES, pdDef.MAP_FORMATS, extensionVoilatile=False)
        self.MapLODSourceData(SourceGeo, self.sourceGeos, pdDef.GEO_LOD_SUFFIXES, pdDef.GEO_FORMATS)
        self.MapRedFiles()
        self.isVariationFolder = len(self.leafFolderName) > 1 and self.leafFolderName[0] == 'v' and self.leafFolderName[1:].isdigit()
        self.isModifierFolder = not self.isVariationFolder and (self.sourceGeos or self.sourceMaps or 'metadata.yaml' in self.files)

    def MapRedFiles(self):
        redFiles = self.GetFilesByExt('red')
        redFileGenerator = (redFile for redFile in redFiles if not ('_hood' in redFile or '_hat' in redFile or '_lod' in redFile))
        for redFile in redFileGenerator:
            if '_physx_lod' in redFile:
                continue
            fullPath = self.GetFullResPath(redFile)
            if redFile.endswith('_physx.red'):
                self.redFiles[pdDef.CLOTH_PATH] = fullPath
                continue
            if redFile.endswith('_nosim.red'):
                self.redFiles[pdDef.CLOTH_OVERRIDE] = fullPath
                continue
            if redFile.endswith('stubble.red'):
                self.redFiles[pdDef.STUBBLE_PATH] = fullPath
                continue
            if redFile.endswith('_shader.red'):
                self.redFiles[pdDef.SHADER_PATH] = fullPath
                continue
            self.redFiles[pdDef.RED_FILE] = fullPath

    def GetFilesByExt(self, ext):
        return pdCf.GetFromDictList(self.extToFiles, ext)

    def GetFullResPath(self, item):
        return '{0}/{1}'.format(self.root, item)

    def GetResPath(self, item):
        return '{0}/{1}'.format(self.respath, item)

    def GetMapResolutonMatch(self, path, width):
        """
        Returns the full res path to the best source map match found for the path and width provided
        """
        idx = path.rfind(pdDef.SEPERATOR_CHAR) + 1
        fn = path[idx:]
        rdsm = self.sourceMaps.get(fn)
        if rdsm:
            fn = rdsm[width]
            if fn:
                fn = self.GetFullResPath(fn)
        return fn or path

    def GetGeoLodMatch(self, path, lod):
        """
        Returns the full path in res to the best geometry resource found for the path and lod provided
        """
        basename = self.GetBaseGeoName(path)
        selfRDSG = self.sourceGeos.get(basename)

        def queryLOD(lodValue):
            if selfRDSG and selfRDSG[lodValue]:
                return self.GetFullResPath(selfRDSG[lodValue])
            for sibling in self.siblings:
                siblingRDSG = sibling.sourceGeos.get(basename) if sibling else None
                if siblingRDSG and siblingRDSG[lodValue]:
                    return sibling.GetFullResPath(siblingRDSG[lodValue])

        fn = None
        try:
            while lod > -2 and fn is None:
                fn = queryLOD(lod)
                lod -= 1

        except AttributeError:
            fn = None

        if fn:
            return fn
        return path

    def GetBaseGeoName(self, path):
        """
        Returns the base geometry name for the given path
        """
        idx = path.rfind(pdDef.SEPERATOR_CHAR) + 1
        filename = path[idx:]
        for k, v in self.sourceGeos.iteritems():
            if v == filename:
                return k

        return filename

    def MapLODSourceData(self, sourceClassFactory, sources, suffixes, extensions, extensionVoilatile = True):
        """
        Processes all, if any, resources so they are quickly accessible by LOD
        """
        if sources:
            sources.clear()
        for fn in iter(self.files):
            currentRDS = None
            currentSuffix = None
            try:
                basename, ext = fn.split('.')
                for suffix in suffixes:
                    if suffix in basename:
                        currentSuffix = suffix
                        basename = basename.replace(suffix, '')
                        break

            except ValueError:
                continue

            if ext in extensions:
                baseFileName = None
                if extensionVoilatile:
                    baseFileName = '{0}.{1}'.format(basename, ext)
                else:
                    for baseFileCandidate in self.files:
                        bfcn, bfce = baseFileCandidate.split('.')[-2:]
                        if bfcn == basename and bfce in extensions:
                            baseFileName = baseFileCandidate
                            break

                if baseFileName:
                    currentRDS = sources.get(baseFileName)
                    if not currentRDS:
                        currentRDS = sourceClassFactory(baseFileName)
                        sources[baseFileName] = currentRDS
                    if currentSuffix:
                        currentRDS.SetItemBySuffix(currentSuffix, fn, ext)


class GenderData(object):
    """
    GenderData contains entries for a particular gender.
    """
    LOD_KEY = 'lod'
    TEST_KEY = 'test'
    TEST_LOD_KEY = 'testlod'
    __guid__ = 'paperDoll.resData.GenderData'

    def __init__(self, gender):
        self.gender = gender
        self.keyedEntries = {None: {},
         GenderData.LOD_KEY: {},
         GenderData.TEST_KEY: {},
         GenderData.TEST_LOD_KEY: {}}
        self.keyedPathsToEntries = {None: {},
         GenderData.LOD_KEY: {},
         GenderData.TEST_KEY: {},
         GenderData.TEST_LOD_KEY: {}}

    def QueryPath(self, path):
        """
        Returns true if the given 'path', which is a short res path, exists in the collection of shortened res paths
        """
        for pathsToEntries in self.keyedPathsToEntries.itervalues():
            if path in pathsToEntries:
                return True

        return False

    def GetPathsToEntries(self, key = None):
        """
        Returns a PathToEntries dictionary. If key is none, returns the default dictionary.
        Other example keys are 'lod' for LOD entries, and 'test' for graphic_test entries
        """
        return self.keyedPathsToEntries.get(key)

    def GetEntries(self, key = None):
        """
        Returns an Entries dictionary. If key is none, returns the default dictionary.
        Other example keys are 'lod' for LOD entries, and 'test' for graphic_test entries
        """
        return self.keyedEntries.get(key)

    def IterEntries(self):
        """
        Iterates through the Entries dictionaries. This yields the keys and entries dictionaries
        associated with each key
        """
        for key, entries in self.keyedEntries.iteritems():
            yield (key, entries)

    def GetEntryByPath(self, path, key = None):
        entry = self.GetPathsToEntries(key).get(path)
        if not entry:
            for k, pathsToEntries in self.keyedPathsToEntries.iteritems():
                if k != key:
                    entry = pathsToEntries.get(path)
                    if entry:
                        break

        return entry


class ResData(object):
    """
    This class contains all directors and filenames that are used by the modifier system
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.resData.ResData'

    def __init__(self):
        self.rootsToEntries = {}
        self.genderData = {}
        self._tasklets = weakref.WeakKeyDictionary()

    def CreateGenderData(self, gender):
        self.genderData[gender] = GenderData(gender)

    def GetEntryByFullResPath(self, fullResPath):
        """
        If fullResPath points to a directory, it returns the ResDataEntry instance of that directory.
        If it points to a file, it returns the ResDataEntry instance that contains that file.
        """
        if '.' in fullResPath:
            fullResPath = pdDef.SEPERATOR_CHAR.join(fullResPath.split(pdDef.SEPERATOR_CHAR)[:-1])
        return self.rootsToEntries.get(fullResPath, None)

    def GetEntriesByGender(self, gender, key = None):
        """
        Returns the default entries for the given 'gender'.
        If 'key' is supplied, it will return the entries applicable for that key
        """
        if gender in self.genderData:
            return self.genderData[gender].GetEntries(key)
        return {}

    def GetPathToEntryByGender(self, gender, key = None):
        """
        Returns the default pathToEntries for the given 'gender'.
        If 'key' is supplied, it will return the entries applicable for that key
        """
        if gender in self.genderData:
            genderData = self.genderData[gender]
            return genderData.GetPathsToEntries(key)
        return {}

    def QueryPathByGender(self, gender, path):
        """
        Returns true if path exists for given gender
        Path is short res path, which is of the form [categorie[/[group/]modifier*[/folder]]]
        """
        if gender in self.genderData:
            genderData = self.genderData[gender]
            return genderData.QueryPath(path)
        return False

    def GetEntryByPath(self, gender, path, key = None):
        """
        Returns a entry by gender and a short res path, which is of the form [categorie[/[group/]modifier*[/folder]]]
        """
        if gender in self.genderData:
            genderData = self.genderData[gender]
            return genderData.GetEntryByPath(path, key)

    def _GetFilesByExtension(self, ext, entries):
        results = []
        for resEntry in entries.iterkeys():
            for f in iter(resEntry.GetFilesByExt(ext)):
                fullPath = resEntry.GetFullResPath(f)
                results.append(fullPath)

        return results

    def GetFilesByExtension(self, ext, gender = None):
        """
        Returns all files with full res paths having the extension supplied in 'ext'
        If 'gender' is supplied, returns only files for the given gender
        """
        results = []
        if gender:
            entries = self.GetEntriesByGender(gender)
            results.extend(self._GetFilesByExtension(ext, entries))
        else:
            for gender in self.genderData.iterkeys():
                results.extend(self._GetFilesByExtension(ext, self.genderData[gender].GetEntries()))

        return results

    def Traverse(self, resDataEntry, visitFunc = None, key = None):
        """
        Returns an iterator that traverses the resDataEntry and all of its descendants.
        If visitFunc is defined, it will be passed each resDataEntry and only entries for which
        visitFunc returns True are yielded.
        """
        if not resDataEntry:
            return
        if not visitFunc or visitFunc(resDataEntry):
            yield resDataEntry
        for childEntry in self.GetChildEntries(resDataEntry, key=key):
            for entry in self.Traverse(childEntry, visitFunc, key):
                yield entry

    def GetChildEntries(self, resDataEntry, key = None):
        """
        Returns the child entries of the given ResDataEntry instance. This only returns the explicit
        children of that instance, not it's instance siblings.
        """
        entries = self.GetEntriesByGender(resDataEntry.gender, key)
        return entries.get(resDataEntry, [])

    def GetParentEntry(self, resDataEntry):
        """
        Returns the parent of the given ResDataEntry instance
        """
        entryRootPath = resDataEntry.root
        parentPath = entryRootPath[:entryRootPath.rindex(pdDef.SEPERATOR_CHAR)]
        parent = self.rootsToEntries.get(parentPath)
        return parent

    def _AddEntry(self, gender, entries, pathsToEntries, root, respath, dirs, files):
        pdCf.BeFrameNice(100)
        if respath.startswith(pdDef.SEPERATOR_CHAR):
            respath = respath[1:]
        respath = str(respath)
        searchPath, stemPath = root.split(':')
        root = '{0}:{1}'.format(searchPath, stemPath.lower())
        resDataEntry = Entry(gender, root, respath, dirs, files)
        entries[resDataEntry] = []
        self.rootsToEntries[root] = resDataEntry
        pathsToEntries[respath] = resDataEntry
        parentEntry = self.GetParentEntry(resDataEntry)
        if parentEntry:
            entries[parentEntry].append(resDataEntry)
        return resDataEntry

    def LinkSiblings(self, keyA, keyB):
        """
        This function links all resDataEntries with their siblings.
        This is explicitly done on keys and mostly meant to gather LOD specific data from one folder (keyB)and
        match it to the base asset definition in another folder (keyA)
        """

        def doLinkage(pathsToEntriesA, pathsToEntriesB):
            for path, entry in pathsToEntriesA.iteritems():
                siblingEntry = pathsToEntriesB.get(path)
                if siblingEntry:
                    siblingEntry.siblings.add(entry)
                    entry.siblings.add(siblingEntry)
                    pdCf.BeFrameNice(100)

        for gender in self.genderData.iterkeys():
            genderData = self.genderData[gender]
            sourcePathsToEntries = genderData.GetPathsToEntries(key=keyA)
            siblingPathsToEntries = genderData.GetPathsToEntries(key=keyB)
            if sourcePathsToEntries and siblingPathsToEntries:
                doLinkage(sourcePathsToEntries, siblingPathsToEntries)

    def PopulateVirtualModifierFolders(self, gender):
        """
        The modifier system supports modifiernames.yaml files that represent modifiers that do not
        contain any source data in res. These modifiers still need to exist as virtual folders since
        that is how modifiers are dealt with. This function adds these modifierse as virtual folders
        to ResData.
        
        For those that really need to know, the main usage of these modifiers is to reflect blendshape
        morph targets as modifiers. Some of them actually do contain real folders with some source maps
        associated to them, hence, we need to have a homogeneous solution.
        """
        genderData = self.genderData[gender]
        entries = genderData.GetEntries()
        pathsToEntries = genderData.GetPathsToEntries()
        yamlFiles = [ yamlFile for yamlFile in self.GetFilesByExtension('yaml', gender) if 'modifiernames' in yamlFile ]
        for yamlFile in yamlFiles:
            yamlFileData = LoadYamlFileNicely(yamlFile)
            if not yamlFileData:
                continue
            else:
                virtualModifierFolders = yamlFileData.lower().replace('\n', '').split()
                rootEntry = self.GetEntryByFullResPath(yamlFile)
                for virtualModifierFolder in virtualModifierFolders:
                    if virtualModifierFolder not in rootEntry.dirs:
                        rootEntry.dirs.append(virtualModifierFolder)
                        newEntry = self._AddEntry(gender, entries, pathsToEntries, '{0}/{1}'.format(rootEntry.root, virtualModifierFolder), rootEntry.GetResPath(virtualModifierFolder), [], [])
                        newEntry.isModifierFolder = True

    def PropogateLODRules(self):
        """
        Propogates lod cutoff values from entries that have values to those decendants of theirs 
        that dont.
        """
        log.LogInfo('PaperDoll - ResData: Propagating LOD rules')

        def TraverseLODCutoff(currentEntry, lodCutoff, entries):
            if not currentEntry:
                return
            if currentEntry.lodCutoff is not None:
                lodCutoff = currentEntry.lodCutoff
            elif lodCutoff is not None:
                currentEntry.lodCutoff = lodCutoff
            for childEntry in entries[currentEntry]:
                TraverseLODCutoff(childEntry, lodCutoff, entries)
                pdCf.BeFrameNice()

        for gender in self.genderData.iterkeys():
            genderData = self.genderData[gender]
            for key, entries in genderData.IterEntries():
                rootEntries = [ entry for entry in entries.iterkeys() if not entry.respath ]
                for rootEntry in rootEntries:
                    TraverseLODCutoff(rootEntry, 2, entries)

        log.LogInfo('PaperDoll - ResData: Done propagating LOD rules!')

    def Populate(self, gender, path, key = None, callBack = None):
        """
        Populates this instance by adding all files contents found at the given path.
        """
        t = uthread.new(self._Populate_t, *(gender,
         str(path),
         key,
         callBack))
        self._tasklets[t] = True

    def _Populate_t(self, gender, path, key, callBack):
        log.LogInfo('ResData: populating from ', path)
        if gender not in self.genderData:
            self.CreateGenderData(gender)
        genderData = self.genderData[gender]
        entries = genderData.GetEntries(key)
        pathsToEntries = genderData.GetPathsToEntries(key)
        path = path.lower()

        def processAsync(root, respath, dirs, files):
            self._AddEntry(gender, entries, pathsToEntries, root, respath, dirs, files)

        try:
            i = 0
            for root, dirs, files in walk.walk(path):
                if dirs or files:
                    pdCf.BeFrameNice(300)
                    respath = root.split(path)[1]
                    t = uthread.new(processAsync, root, respath, dirs, files)
                    i += 1
                    self._tasklets[t] = True

        finally:
            log.LogInfo('ResData:', i, ' entries populated from ', path)
            if callBack:
                uthread.new(callBack)

    def IsLoading(self):
        return len(self._tasklets.keys()) > 0
