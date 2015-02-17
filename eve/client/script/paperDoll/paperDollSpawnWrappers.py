#Embedded file name: eve/client/script/paperDoll\paperDollSpawnWrappers.py
import trinity
import uthread
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollDataManagement as pdDm
import eve.client.script.paperDoll.commonClientFunctions as pdCcf
import eve.common.script.paperDoll.paperDollCommonFunctions as pdCf
import eve.client.script.paperDoll.paperDollImpl as pdImpl
import eve.client.script.paperDoll.paperDollLOD as pdLod
import eve.client.script.paperDoll.paperDollPortrait as pdPor
from eve.client.script.paperDoll.SkinSpotLightShadows import SkinSpotLightShadows
import blue
import telemetry
import yaml
import log

class PaperDollManager(object):
    """
    Manages a set of PaperDollCharacters and simplifies the creation of such entities.
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.PaperDollManager'

    def __init__(self, factory, keyFunc = None):
        self.factory = factory
        self.keyFunc = keyFunc
        self.__pdc = {}

    def __del__(self):
        self.ClearDolls()

    def __iter__(self):
        """
        Default iterator of paperdoll characters.
        """
        for pdc in self.__pdc.itervalues():
            yield pdc

    def Count(self):
        return len(self.__pdc)

    def GetPaperDollCharacterByDoll(self, doll):
        """
        Iterates over all PaperDollCharacter instances and returns the first instance that has a doll
        matching 'doll' via their instanceIDs.
        Returns None if none is found.    
        """
        for pdc in iter(self):
            if pdImpl.Doll.InstanceEquals(pdc.doll, doll):
                return pdc

    def GetPaperDollCharacterByAvatar(self, avatar):
        """
        Iterates over all PaperDollCharacter instances and returns the first instance that has an avatar
        matching 'avatar'.
        Returns None if none is found.    
        """
        for pdc in iter(self):
            if pdc.avatar == avatar:
                return pdc

    def GetPaperDollCharacterByKey(self, key):
        """
        Returns the paperdoll character at the specified dictionary key.
        Returns None if none is found.
        """
        return self.__pdc.get(key)

    def RemovePaperDollCharacter(self, pdc):
        """
        Removes PaperDollCharacter instance 'pdc' from this manager.
        """
        key = self.__GetKey(pdc)
        if key in self.__pdc:
            del self.__pdc[key]

    def ClearDolls(self):
        """
        Removes and deletes all paperdoll characters.
        """
        self.__pdc.clear()

    def __GetKey(self, pdc):
        """
        Returns the key corresponding to the pdc.
        """
        doll = pdc.GetDoll()
        if self.keyFunc:
            return self.keyFunc(doll)
        else:
            return doll.instanceID

    def SpawnPaperDollCharacterFromDNA(self, scene, dollName, dollDNA, position = None, rotation = None, lodEnabled = False, compressionSettings = None, gender = pdDef.GENDER.FEMALE, usePrepass = False, textureResolution = None, updateDoll = True, spawnAtLOD = 0):
        """
        Creates a doll with given name and applies the specified dna.
        """
        pdc = PaperDollCharacter(self.factory)
        pdc.LoadDollFromDNA(dollDNA, dollName=dollName, lodEnabled=lodEnabled, compressionSettings=compressionSettings)
        if textureResolution:
            pdc.doll.SetTextureSize(textureResolution)
        if lodEnabled:
            pdc.SpawnLOD(scene, point=position, rotation=rotation, gender=gender, usePrepass=usePrepass)
        else:
            pdc.Spawn(scene, point=position, rotation=rotation, gender=gender, usePrepass=usePrepass, updateDoll=updateDoll, lod=spawnAtLOD)
        self.__pdc[self.__GetKey(pdc)] = pdc
        sm.ScatterEvent('OnDollCreated', self.__GetKey(pdc))
        return pdc

    def SpawnRandomDoll(self, scene, **kwargs):
        """
        Creates and spawns a random doll to the given scene.
        """
        pdc = PaperDollCharacter(self.factory)
        pdc.MakeRandomDoll()
        autoLod = kwargs.get('autoLOD')
        if autoLod:
            pdc.SpawnLOD(scene, **kwargs)
        else:
            pdc.Spawn(scene, **kwargs)
        self.__pdc[self.__GetKey(pdc)] = pdc
        sm.ScatterEvent('OnDollCreated', self.__GetKey(pdc))
        return pdc

    def SpawnDoll(self, scene, **kwargs):
        """
        Spawns a doll to the given scene.
        If 'doll' is none, creates a standard nude doll.
        If 'gender' is none, the doll is female, otherwise provide either GENDER.MALE or GENDER.FEMALE
        If 'point' is given, spawns at that point in world coordinates, otherwise at the origin.
        If 'autoLOD' is given and is not None or False, spawns the doll so it performs automatic LOD.
        """
        doll = kwargs.get('doll')
        autoLod = kwargs.get('autoLOD')
        pdc = PaperDollCharacter(self.factory, doll=doll)
        if autoLod:
            pdc.SpawnLOD(scene, **kwargs)
        else:
            pdc.Spawn(scene, **kwargs)
        self.__pdc[self.__GetKey(pdc)] = pdc
        sm.ScatterEvent('OnDollCreated', self.__GetKey(pdc))
        return pdc

    def SpawnDollFromRes(self, scene, resPath, **kwargs):
        """
        Creates a PaperDollCharacter with a doll instance using data defined in resPath and spawns to the scene.        
        Returns a reference to the PaperDollCharacter
        """
        pdc = PaperDollCharacter(self.factory)
        pdc.LoadFromRes(resPath)
        pdc.Spawn(scene, **kwargs)
        self.__pdc[self.__GetKey(pdc)] = pdc
        sm.ScatterEvent('OnDollCreated', self.__GetKey(pdc))
        return pdc

    def GetAllDolls(self):
        """
        Returns a list of doll info dicts. Each dict contains name, translation, rotation and dna.
        """
        dolls = []
        for dc in self.__pdc.itervalues():
            dollInfo = {}
            dollInfo['name'] = dc.doll.name
            dollInfo['translation'] = dc.avatar.translation
            dollInfo['rotation'] = dc.avatar.rotation
            dollInfo['dna'] = dc.GetDNA()
            dollInfo['doll'] = dc
            dolls.append(dollInfo)

        return dolls

    def RestoreDollsFromDnaToScene(self, dolls, scene):
        """
        Restores dolls from a list of doll info dicts, as returned by GetAllDolls.
        """
        for dc in dolls:
            self.SpawnPaperDollCharacterFromDNA(scene, dc['name'], dc['dna'], position=dc['translation'], rotation=dc['rotation'])

    def WaitForAllDolls(self):
        for dc in self.__pdc.itervalues():
            dc.WaitForUpdate()


class PaperDollCharacter(object):
    """
    PaperDollCharacter instance encapsulates and contains a doll, avatar and a visualModel. 
    This class makes it easy to spawn a nude character into a scene. 
    Unlike other usage patterns common to paperdoll, this class is defined so each instance holds 
    on to a reference to Factory to simplify message passing.    
    
    Example macro:
        
        import paperDoll as PD
        import trinity
    
        factory = PD.Factory("Female")
        character = PD.PaperDollCharacter(factory)
        character.Spawn(trinity.device.scene)       
    """
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __guid__ = 'paperDoll.PaperDollCharacter'
    __DEFAULT_NAME = 'Spawned Character'

    def setscene(self, scene):
        self.__scene = blue.BluePythonWeakRef(scene)

    scene = property(fget=lambda self: self.__scene.object, fset=lambda self, x: self.setscene(x))

    def __init__(self, factory, doll = None, avatar = None, visualModel = None):
        """
        'factory' must be passed and must be of type paperDoll.Factory
        """
        self.factory = factory
        self.doll = None
        self.factory.WaitUntilLoaded()
        self.doll = doll
        self.avatar = avatar
        self.visualModel = visualModel
        if not visualModel and hasattr(avatar, 'visualModel'):
            self.visualModel = avatar.visualModel
        self.__scene = blue.BluePythonWeakRef(None)
        self.autoLod = False
        self.disableDel = False
        trinity.device.RegisterResource(self)

    def __del__(self):
        if self.disableDel:
            return
        del self.doll
        del self.visualModel
        if self.scene:
            self.factory.RemoveAvatarFromScene(self.avatar, self.scene)
        if self.avatar:
            self.avatar.visualModel = None
        if self.autoLod:
            pdLod.AbortAllLod(self.avatar)
        del self.avatar

    def OnInvalidate(self, dev):
        pass

    def OnCreate(self, dev):
        """
        Device reset handler
        """
        if self.doll and self.avatar:
            self.doll.KillUpdate()
            self.doll.mapBundle.ReCreate()
            for modifier in self.doll.buildDataManager.GetModifiersAsList():
                modifier.IsDirty |= modifier.decalData is not None or modifier.IsMeshDirty()

            self.doll.decalBaker = None
            if SkinSpotLightShadows.instance is not None:
                SkinSpotLightShadows.instance.RefreshLights()
            uthread.new(self.doll.Update, self.factory, self.avatar)

    def ExportCharacter(self, resPath):
        """
        Exports the character to the given resPath, which must point to a folder, so paperDoll does not need to be used to reassamble
        it. However, this data is always static and will never reflect the latest changes in source
        assets / modifiers.
        """

        def fun():
            path = resPath

            def GetMapResourcePath(map):
                return path + '/' + pdDef.MAPNAMES[map] + '.dds'

            for map in pdDef.MAPS:
                texture = self.doll.mapBundle[map]
                texture.SaveAsync(GetMapResourcePath(map))
                texture.WaitForSave()

            meshGeometryResPaths = {}
            for modifier in self.doll.buildDataManager.GetSortedModifiers():
                meshGeometryResPaths.update(modifier.meshGeometryResPaths)

            for mesh in self.avatar.visualModel.meshes:
                mesh.geometryResPath = meshGeometryResPaths.get(mesh.name, '')
                for fx in pdCcf.GetEffectsFromMesh(mesh):
                    for resource in fx.resources:
                        if resource.name in pdDef.MAPNAMES:
                            resource.resourcePath = GetMapResourcePath(pdDef.MAPNAMES.index(resource.name))

            trinity.Save(self.avatar, path + '/unique.red')
            morphTargets = {}
            for modifier in self.doll.buildDataManager.GetSortedModifiers():
                if modifier.categorie in pdDef.BLENDSHAPE_CATEGORIES:
                    morphTargets[modifier.name] = modifier.weight

            bsFilePath = blue.paths.ResolvePath(path + '/blendshapes.yaml')
            f = file(bsFilePath, 'w')
            yaml.dump(morphTargets, f)
            f.close()
            animOffsets = {}
            for bone in self.doll.boneOffsets:
                trans = self.doll.boneOffsets[bone]['translation']
                animOffsets[bone] = trans

            aoFilePath = blue.paths.ResolvePath(path + '/animationOffsets.yaml')
            f = file(aoFilePath, 'w')
            yaml.dump(animOffsets, f)
            f.close()

        uthread.new(fun)

    @staticmethod
    def ImportCharacter(factory, scene, resPath, **kwargs):
        """
        'factory' is an instance of Factory
        'scene' is a reference to the scene into which the character should appear
        'resPath' is the path to the directory which the character was exported to
        'callBack' if provided, is a function that gets called once importing is done.
        
        Imports a character from the given resPath and adds it to the scene.
        This character will not have a doll instance, it is purely a trinity setup of a character.
        Returns a PaperDollCharacter instance
        """
        blocking = kwargs.get('blocking')
        callBack = kwargs.get('callBack')
        rotation = kwargs.get('rotation')
        position = kwargs.get('point')
        pdc = PaperDollCharacter(factory)
        pdc.scene = scene
        pdc.avatar = trinity.Load(resPath + '/unique.red')
        if pdc.avatar is None:
            log.LogInfo('Import failed on ' + resPath + '/unique.red')
            return
        pdc.visualModel = pdc.avatar.visualModel
        slash = resPath.rfind('/')
        pdc.avatar.name = str(resPath[slash + 1:] + ' (import)')
        if position:
            pdc.avatar.translation = position
        if rotation:
            pdc.avatar.rotation = rotation
        rf = blue.ResFile()
        bsPath = resPath + '/blendshapes.yaml'
        meshes = None
        morphTargets = pdDm.LoadYamlFileNicely(bsPath)
        if morphTargets:
            meshes = pdc.visualModel.meshes

        def fun():
            if meshes:
                factory.ApplyMorphTargetsToMeshes(meshes, morphTargets)
                if trinity.GetShaderModel() == 'SM_2_0_LO':
                    pdPor.PortraitTools.RebindDXT5ShadersForSM2(meshes)
            if callBack:
                callBack()

        if blocking:
            fun()
        else:
            uthread.worker('paperDoll::PaperDollCharacter::ImportCharacter', fun)
        scene.AddDynamic(pdc.avatar)
        aoPath = resPath + '/animationOffsets.yaml'
        animationOffsets = pdDm.LoadYamlFileNicely(aoPath)
        if animationOffsets:
            pdc.ApplyAnimationOffsets(animationOffsets)
        pdc.avatar.explicitMinBounds = (-5, -5, -5)
        pdc.avatar.explicitMaxBounds = (5, 5, 5)
        pdc.avatar.useExplicitBounds = True
        if SkinSpotLightShadows.instance is not None:
            for mesh in pdc.visualModel.meshes:
                SkinSpotLightShadows.instance.CreateEffectParamsForMesh(mesh)

        return pdc

    def ApplyAnimationOffsets(self, animationOffsets = None):
        import GameWorld
        if animationOffsets and self.avatar.animationUpdater and type(self.avatar.animationUpdater) == GameWorld.GWAnimation and self.avatar.animationUpdater.network:
            for animationOffset in iter(self.animationOffsets):
                self.avatar.animationUpdater.network.boneOffset.SetOffset(animationOffset, animationOffsets[animationOffset][0], animationOffsets[animationOffset][1], animationOffsets[animationOffset][2])

    def GetDoll(self):
        return self.doll

    def GetAvatar(self):
        return self.avatar

    def MakeRandomDoll(self):
        """
        Makes the doll random, so it will have some cloth, even hair.
        """
        self.doll = pdCcf.CreateRandomDoll(self.doll.name if self.doll else PaperDollCharacter.__DEFAULT_NAME, self.factory)
        if self.avatar:
            self.doll.Update(self.factory, self.avatar)

    def MakeDollNude(self):
        """
        Makes the doll nude.
        """
        self.doll.buildDataManager = pdDm.BuildDataManager()
        if self.avatar:
            self.doll.Update(self.factory, self.avatar)

    def LoadFromRes(self, resPath):
        """
        Loads the doll from the given resPath and applies it to its avatar if it has one.
        """
        self.doll = pdImpl.Doll(PaperDollCharacter.__DEFAULT_NAME)
        while not self.factory.IsLoaded:
            pdCf.Yield()

        self.doll.Load(resPath, self.factory)
        if self.avatar:
            self.doll.Update(self.factory, self.avatar)

    def LoadDollFromDNA(self, dollDNA, dollName = None, lodEnabled = True, compressionSettings = None):
        """
        Loads a doll from the given dna and then applies it to its avatar if it has one.
        """
        name = dollName if dollName is not None else PaperDollCharacter.__DEFAULT_NAME
        self.doll = pdImpl.Doll(name)
        self.doll.LoadDNA(dollDNA, self.factory)
        if compressionSettings:
            self.doll.compressionSettings = compressionSettings
        if self.avatar:
            gender = pdDef.GENDER.MALE if self.doll.gender else pdDef.GENDER.FEMALE
            networkToLoad = const.FEMALE_MORPHEME_PATH if gender == pdDef.GENDER.FEMALE else const.MALE_MORPHEME_PATH
            if lodEnabled:
                uthread.worker('^PaperDollCharacter::LoadFromDNA', pdLod.SetupLODFromPaperdoll, self.avatar, self.doll, self.factory, networkToLoad)
            else:
                uthread.worker('^PaperDollCharacter::LoadFromDNA', self.doll.Update, self.factory, self.avatar)

    def GetDNA(self):
        """
        Returns the DNA for this doll. This can be used with LoadDollFromDNA to recreate
        this exact doll.
        """
        return self.doll.GetDNA()

    def __PrepareAvatar(self, scene, point = None, rotation = None):
        if scene is None:
            raise ValueError('None type passed as scene to paperDoll::__PrepareAvatar!')
        oldAnimation = None
        sceneTypesDifferent = getattr(self.scene, '__typename__', None) != getattr(scene, '__typename__', None)
        if self.avatar:
            oldAnimation = self.avatar.animationUpdater
            if self.scene:
                self.factory.RemoveAvatarFromScene(self.avatar, self.scene)
            if sceneTypesDifferent:
                pdLod.AbortAllLod(self.avatar)
                del self.avatar
        if type(scene) in (trinity.Tr2InteriorScene, trinity.WodBakingScene) and type(self.scene) is not type(scene):
            self.avatar = trinity.Tr2IntSkinnedObject()
            self.doll.avatarType = 'interior'
        self.factory.AddAvatarToScene(self.avatar, scene)
        if point:
            self.avatar.translation = point
        if rotation:
            self.avatar.rotation = rotation
            self.avatar.animationUpdater = oldAnimation
        if getattr(self.avatar.animationUpdater, 'network', None):
            if self.doll.gender == pdDef.GENDER.MALE and self.avatar.animationUpdater.network.GetAnimationSetCount() > 1:
                self.avatar.animationUpdater.network.SetAnimationSetIndex(1)
            else:
                self.avatar.animationUpdater.network.SetAnimationSetIndex(0)

    def SpawnLOD(self, scene, **kwargs):
        """
        Like Spawn but sets up LOD-ing.
        """
        self.Spawn(scene, spawnLod=True, **kwargs)

    def Spawn(self, scene, **kwargs):
        """
        Spawns a new character into a scene.
        If 'point' is supplied, the doll will spawn at that point in world coordinates.
        If 'gender' is supplied, must be either GENDER.FEMALE or GENDER.MALE, defaults to GENDER.FEMALE
        Other arguments should be kept in args.
        """
        gender = pdDef.GENDER.FEMALE
        if 'gender' in kwargs:
            gender = kwargs['gender']
        if self.doll is None:
            self.doll = pdImpl.Doll(PaperDollCharacter.__DEFAULT_NAME, gender=gender)
        else:
            gender = self.doll.gender
        spawnLod = kwargs.get('spawnLod', False)
        usePrepass = kwargs.get('usePrepass', False)
        self.doll.SetUsePrepass(usePrepass)
        if 'lod' in kwargs and not spawnLod:
            self.doll.overrideLod = kwargs['lod']
        if self.visualModel is None:
            self.visualModel = self.factory.CreateVisualModel(gender=gender)
        self.__PrepareAvatar(scene, point=kwargs.get('point'), rotation=kwargs.get('rotation'))
        self.scene = scene
        self.avatar.visualModel = self.visualModel
        if spawnLod:
            networkToLoad = const.FEMALE_MORPHEME_PATH if gender == pdDef.GENDER.FEMALE else const.MALE_MORPHEME_PATH
            pdLod.SetupLODFromPaperdoll(self.avatar, self.doll, self.factory, networkToLoad)
        elif kwargs.get('updateDoll', True):
            self.doll.Update(self.factory, self.avatar)

    def MoveToScene(self, scene, point = None):
        """
        Moves this PDC from one scene to another.
        """
        if scene and self.doll:
            if getattr(self.scene, '__typename__', None) != getattr(scene, '__typename__', None):
                self.doll.buildDataManager.SetAllAsDirty(clearMeshes=True)
            self.Spawn(scene, point=point)

    def Update(self, channel = None):
        return self.doll.Update(self.factory, self.avatar, channel=channel)

    def UpdateClothSimulationStatus(self):
        self.doll.buildDataManager.SetAllAsDirty(clearMeshes=True)
        self.Update()

    def WaitForUpdate(self):
        """
        Wait until the doll Update has finished.
        """
        while self.doll.busyUpdating:
            pdCf.Yield()
