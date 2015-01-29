#Embedded file name: eve/client/script/environment/spaceObject\planet.py
import random
import datetime
import math
import blue
import trinity
import uthread
import util
import geo2
import telemetry
import eve.common.lib.appConst as const
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
PLANET_SIZE_SCALE = 1000000.0
PLANET_DISTRICTS_COUNT = 10
PLANET_DISTRICT_RADIUS_RATIO = 5000000
ORBBOMB_IMPACT_FX_EM = 20204
ORBBOMB_IMPACT_FX_HYBRID = 20205
ORBBOMB_IMPACT_FX_LASER = 20206

class Planet(SpaceObject):

    def __init__(self):
        SpaceObject.__init__(self)
        self.textureSet = None
        self.loaded = False
        self.isInflightPlanet = True
        self.rotatePlanet = False
        self.rotationApplied = False
        self.audioStarted = False
        self.attributes = None
        self.modelRes = []
        self.modelPath = None
        self.heightMapResPath1 = ''
        self.heightMapResPath2 = ''
        self.largeTextures = False
        self.districts = {}
        self.districtsInfo = {}
        self.districtContainer = trinity.EveTransform()
        self.districtContainer.name = 'Districts'
        self.districtExplosions = trinity.EveTransform()
        self.districtExplosions.name = 'Explosions'

    def Display(self, display = 1, canYield = True):
        pass

    def LoadModel(self):
        uthread.new(self.LoadPlanet)

    def _ApplyPlanetRotation(self):
        rotationDirection = 1
        if self.id % 2:
            rotationDirection = -1
        r = random.Random()
        r.seed(self.id)
        rotationTime = r.random() * 2000 + 3000
        yCurve = trinity.TriScalarCurve()
        yCurve.extrapolation = trinity.TRIEXT_CYCLE
        yCurve.AddKey(0.0, 1.0, 0.0, 0.0, trinity.TRIINT_LINEAR)
        yCurve.AddKey(rotationTime, rotationDirection * 360.0, 0.0, 0.0, trinity.TRIINT_LINEAR)
        yCurve.Sort()
        tilt = r.random() * 60.0 - 30.0
        pCurve = trinity.TriScalarCurve()
        pCurve.extrapolation = trinity.TRIEXT_CYCLE
        pCurve.AddKey(0.0, 1.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        pCurve.AddKey(6000.0, tilt, 0.0, 0.0, trinity.TRIINT_HERMITE)
        pCurve.AddKey(12000.0, 0.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        pCurve.Sort()
        self.model.rotationCurve = trinity.TriYPRSequencer()
        self.model.rotationCurve.YawCurve = yCurve
        self.model.rotationCurve.PitchCurve = pCurve
        self.rotationApplied = True

    def _ApplyZOnlyModel(self):

        def _apply():
            self.model.zOnlyModel = blue.recycler.RecycleOrLoad('res:/dx9/model/worldobject/planet/planetzonly.red')

        uthread.new(_apply)

    def _GetModelPath(self):
        return self.typeData.get('graphicFile')

    def _GetPlanetAttributes(self, itemID):
        return cfg.mapSolarSystemContentCache.celestials[itemID].planetAttributes

    @telemetry.ZONE_METHOD
    def LoadPlanet(self, itemID = None, forPhotoService = False, rotate = True, hiTextures = False):
        if itemID is None:
            itemID = self.id
        self.itemID = itemID
        self.largeTextures = hiTextures
        self.rotatePlanet = self.typeID != const.typePlanetEarthlike and rotate
        self.isInflightPlanet = not forPhotoService
        self.model = trinity.EvePlanet()
        if self.model is None:
            self.LogError('Could not create model for planet with id', itemID)
            return
        self.model.translationCurve = self
        self.model.highDetail = trinity.EveTransform()
        self.model.scaling = self.radius
        self.model.radius = self.radius
        self.model.name = '%d' % itemID
        if self.isInflightPlanet:
            self.model.resourceCallback = self.ResourceCallback
            scene = self.spaceMgr.GetScene()
            if scene is not None:
                scene.planets.append(self.model)

    @telemetry.ZONE_METHOD
    def LoadRedFiles(self):
        if self.modelPath is None:
            self.modelPath = self._GetModelPath()
            if self.largeTextures:
                self.modelPath = self.modelPath.replace('.red', '_HI.red')
        if self.rotatePlanet and not self.rotationApplied:
            self._ApplyPlanetRotation()
        if self.typeID == const.typeMoon and self.model.zOnlyModel is None:
            self._ApplyZOnlyModel()
        if self.attributes is None:
            self.attributes = self._GetPlanetAttributes(self.itemID)
        presetPath = self.modelPath
        if self.__GetShaderPreset() is not None:
            presetPath = util.GraphicFile(self.__GetShaderPreset())
        self.presetPath = presetPath
        if self.largeTextures:
            presetPath = presetPath.replace('/Template/', '/Template_HI/')
        gfx = cfg.invtypes.GetIfExists(self.typeID).Graphic()
        if hasattr(gfx, 'albedoColor') and gfx.albedoColor:
            self.model.albedoColor = tuple(gfx.albedoColor)
        if hasattr(gfx, 'emissiveColor') and gfx.emissiveColor:
            self.model.emissiveColor = tuple(gfx.emissiveColor)
        planet = trinity.Load(presetPath)
        if planet is None:
            self.LogError('No planet was loaded!', presetPath)
            return False
        planet.name = 'Planet'
        self.model.highDetail.children.append(planet)
        self.model.highDetail.children.append(self.districtContainer)
        self.model.highDetail.children.append(self.districtExplosions)
        self.__ModifyPlanetShader()
        self.__CreateBakeEffect()
        self.__CollectLargeResources()
        self.__ApplyPlanetAttributesToDistricts()
        if self.isInflightPlanet and not self.audioStarted:
            self.audioStarted = True
            self.SetupAmbientAudio()
        return True

    def Release(self):
        if hasattr(self.model, 'resourceCallback'):
            self.model.resourceCallback = None
        if hasattr(self.model, 'children'):
            del self.model.children[:]
        scene = self.spaceMgr.GetScene()
        if scene:
            scene.planets.fremove(self.model)
        SpaceObject.Release(self, 'Planet')

    def RemoveFromScene(self, model, scene = None):
        """This is handled elsewhere.
        
        :param model: The trinity model to clear.
        :param scene: The scene to remove the object from.
          If None, use the sceneManager to get the registered 
          default scene.
        """
        pass

    def GetPlanetByID(self, itemID, typeID):
        self.LogInfo('GetPlanetByID called')
        self.typeID = typeID
        self.LoadPlanet(itemID, True)

    def PrepareForWarp(self, distance, dest):
        if self.model is not None:
            self.model.PrepareForWarp(distance, dest)

    def WarpStopped(self):
        if self.model is not None:
            self.model.WarpStopped()

    def AddDistrict(self, uniqueName, centerNormal, size, enableBattle):
        if uniqueName in self.districts:
            self.LogError('District ' + str(uniqueName) + ' already exists for planet with id ' + str(self.itemID))
            return
        randomDistrictNum = len(self.districts) % 10 + 1
        randomDistrictResPath = 'res:/dx9/model/worldobject/Planet/Terrestrial/district/District%02d.red' % randomDistrictNum
        newDistrict = trinity.Load(randomDistrictResPath)
        if newDistrict is None:
            self.LogError('District ' + str(randomDistrictResPath) + ' not found for planet with id ' + str(self.itemID))
            return
        newDistrict.name = uniqueName
        newDistrict.centerNormal = centerNormal
        for param in newDistrict.pinEffect.parameters:
            if param.name == 'AnimatedFactors2':
                param.value = (param.value[0],
                 float(enableBattle),
                 random.random(),
                 param.value[3])
                break

        newDistrict.pinRadius = PLANET_DISTRICT_RADIUS_RATIO * size / self.radius
        newDistrict.pinMaxRadius = PLANET_DISTRICT_RADIUS_RATIO * size / self.radius
        newDistrict.pinRotation = 0.0
        self.districts[uniqueName] = newDistrict
        self.districtContainer.children.append(newDistrict)
        self.districtsInfo[uniqueName] = {'num': randomDistrictNum}
        self.__ApplyPlanetAttributesToDistricts()

    def DelDistrict(self, uniqueName):
        if uniqueName not in self.districts:
            self.LogError('Could not find district ' + str(uniqueName) + ' for planet with id ' + str(self.itemID))
        self.districtContainer.children.remove(self.districts[uniqueName])
        self.districts.remove(uniqueName)

    def DelAllDistricts(self):
        self.districts = {}
        del self.districtContainer.children[:]

    def GetDistrictNum(self, uniqueName):
        if uniqueName not in self.districtsInfo:
            self.LogError('Could not find district info for ' + str(uniqueName) + ' for planet with id ' + str(self.itemID))
            return 0
        return self.districtsInfo[uniqueName]['num']

    def EnableBattleForDistrict(self, uniqueName, enableBattle):
        if uniqueName not in self.districts:
            self.LogError('Could not find district ' + str(uniqueName) + ' for planet with id ' + str(self.itemID))
        for param in self.districts[uniqueName].pinEffect.parameters:
            if param.name == 'AnimatedFactors2':
                param.value = (param.value[0],
                 float(enableBattle),
                 param.value[2],
                 param.value[3])
                break

    def AddExplosion(self, uniqueName, explosionGfxID, spreadOut):
        if uniqueName not in self.districts:
            self.LogError('Could not find district ' + str(uniqueName) + ' for planet with id ' + str(self.itemID))
        graphics = cfg.graphics.GetIfExists(explosionGfxID)
        if graphics is None:
            self.LogError('Explosion graphicsID ' + str(explosionGfxID) + " doesn't exist!")
            return
        fx = trinity.Load(graphics.graphicFile)
        if fx is None:
            self.LogError('Explosion ' + str(graphics.graphicFile) + " doesn't exist!")
            return
        if len(fx.curveSets) == 0:
            self.LogError('Explosion ' + str(graphics.graphicFile) + ' has no curveSets! This is useless...')
            return
        direction = self.districts[uniqueName].centerNormal
        rotMatrix1 = geo2.MatrixRotationAxis((direction[1], direction[2], direction[0]), random.random() * spreadOut * self.districts[uniqueName].pinRadius)
        rotMatrix2 = geo2.MatrixRotationAxis(direction, random.uniform(0, 2.0 * math.pi))
        direction = geo2.Vec3TransformNormal(direction, rotMatrix1)
        direction = geo2.Vec3TransformNormal(direction, rotMatrix2)
        fx.translation = direction
        fx.scaling = (5000.0 / PLANET_SIZE_SCALE, 5000.0 / PLANET_SIZE_SCALE, 5000.0 / PLANET_SIZE_SCALE)
        v1 = geo2.Vec3Cross(geo2.Vec3Normalize(direction), (0.0, 1.0, 0.0))
        alpha = -math.acos(geo2.Vec3Dot(geo2.Vec3Normalize(direction), (0.0, 1.0, 0.0)))
        fx.rotation = geo2.QuaternionRotationAxis(v1, alpha)
        duration = fx.curveSets[0].GetMaxCurveDuration()
        self.districtExplosions.children.append(fx)
        uthread.new(self._RemoveExplosionFromDistrict, fx, duration)

    def _RemoveExplosionFromDistrict(self, fxToRemove, delay):
        blue.synchro.SleepSim(delay * 1000.0)
        self.districtExplosions.children.remove(fxToRemove)

    def ResourceCallback(self, create, size = 2048):
        if create:
            pm = self.spaceMgr.planetManager
            if pm is None:
                self.LogError('Failed to get planet manager.')
                return
            pm.DoPlanetPreprocessing(self, size)
        else:
            if self.model is None:
                return
            heightMapParamList = self.__GetPlanetShaderParameters('HeightMap', 'trinity.TriTexture2DParameter')
            for heightMapParam in heightMapParamList:
                heightMapParam.SetResource(None)

            self.__FreeLargeResources()
            self.model.ready = False
            self.model.resourceActionPending = False

    def DoPreProcessEffectForPhotoSvc(self, size):
        renderTarget = trinity.Tr2RenderTarget(2 * size, size, 0, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        vp = trinity.TriViewport()
        vp.width = 2 * size
        vp.height = size
        if not self.LoadRedFiles():
            return
        trinity.WaitForResourceLoads()
        heightMapParam1 = self.__GetBakeShaderParameter('NormalHeight1', 'trinity.TriTexture2DParameter')
        if heightMapParam1 is not None:
            heightMapParam1.resourcePath = self.heightMapResPath1
        heightMapParam2 = self.__GetBakeShaderParameter('NormalHeight2', 'trinity.TriTexture2DParameter')
        if heightMapParam2 is not None:
            heightMapParam2.resourcePath = self.heightMapResPath2
        renderTargetSizeParam = self.__GetBakeShaderParameter('TargetTextureHeight', 'trinity.TriTexture2DParameter')
        if renderTargetSizeParam is not None:
            renderTargetSizeParam.value = size
        trinity.WaitForResourceLoads()
        rj = trinity.CreateRenderJob('Height normal Compositing')
        rj.PushRenderTarget(renderTarget)
        rj.SetViewport(vp)
        rj.PushDepthStencil(None)
        rj.Clear((0.0, 0.0, 0.0, 0.0))
        rj.RenderEffect(self.effectHeight)
        rj.PopDepthStencil()
        rj.PopRenderTarget()
        rj.GenerateMipMaps(renderTarget)
        rj.ScheduleOnce()
        rj.WaitForFinish()
        tex = trinity.TriTextureRes()
        tex.CreateAndCopyFromRenderTarget(renderTarget)
        heightMapParamList = self.__GetPlanetShaderParameters('HeightMap', 'trinity.TriTexture2DParameter')
        for heightMapParam in heightMapParamList:
            heightMapParam.SetResource(tex)

    def DoPreProcessEffect(self, size, format, renderTarget):
        if renderTarget is None:
            self.model.resourceActionPending = False
            self.model.ready = True
            return
        vp = trinity.TriViewport()
        vp.width = 2 * size
        vp.height = size
        trinity.WaitForResourceLoads()
        if self.model is None:
            return
        if len(self.modelRes) == 0:
            if not self.LoadRedFiles():
                self.model.resourceActionPending = False
                self.model.ready = True
                return
        else:
            self.__ReloadLargeResources()
        heightMapParam1 = self.__GetBakeShaderParameter('NormalHeight1', 'trinity.TriTexture2DParameter')
        if heightMapParam1 is not None:
            heightMapParam1.resourcePath = self.heightMapResPath1
        heightMapParam2 = self.__GetBakeShaderParameter('NormalHeight2', 'trinity.TriTexture2DParameter')
        if heightMapParam2 is not None:
            heightMapParam2.resourcePath = self.heightMapResPath2
        renderTargetSizeParam = self.__GetBakeShaderParameter('TargetTextureHeight', 'trinity.TriTexture2DParameter')
        if renderTargetSizeParam is not None:
            renderTargetSizeParam.value = size
        trinity.WaitForResourceLoads()
        if self.model is None:
            return
        rj = trinity.CreateRenderJob('Height normal Compositing')
        rj.PushRenderTarget(renderTarget)
        rj.SetViewport(vp)
        rj.PushDepthStencil(None)
        step = rj.Clear((0.0, 0.0, 0.0, 0.0), 1.0)
        step.isDepthCleared = False
        rj.RenderEffect(self.effectHeight)
        rj.PopDepthStencil()
        rj.PopRenderTarget()
        rj.GenerateMipMaps(renderTarget)
        rj.ScheduleOnce()
        rj.WaitForFinish()
        if self.model is None:
            return
        tex = trinity.TriTextureRes()
        tex.CreateAndCopyFromRenderTargetWithSize(renderTarget, size * 2, size)
        if heightMapParam1 is not None:
            heightMapParam1.resourcePath = ''
            heightMapParam1.SetResource(None)
        if heightMapParam2 is not None:
            heightMapParam2.resourcePath = ''
            heightMapParam2.SetResource(None)
        heightMapParamList = self.__GetPlanetShaderParameters('HeightMap', 'trinity.TriTexture2DParameter')
        for heightMapParam in heightMapParamList:
            heightMapParam.SetResource(tex)

        self.model.ready = True
        self.model.resourceActionPending = False

    def __CreateBakeEffect(self):
        """
        Create and setup a planet's effect file for heightmap baking
        """
        self.effectHeight = trinity.Tr2Effect()
        if self.effectHeight is None:
            self.LogError('Could not create effect for planet with id', self.itemID)
            return
        mainMesh = self.model.highDetail.children[0].meshLod
        if mainMesh is None:
            mainMesh = self.model.highDetail.children[0].mesh
            errorMsg = 'No LODs found on planet.\n'
            modelPath = 'modelPath=' + self.modelPath + '\n'
            presetPath = 'presetPath=' + self.presetPath + '\n'
            shaderPreset = 'shaderPreset=' + str(self.attributes.shaderPreset) + '\n'
            self.LogError(errorMsg, modelPath, presetPath, shaderPreset)
        if len(mainMesh.transparentAreas) > 0:
            resPath = mainMesh.transparentAreas[0].effect.effectFilePath
        elif len(mainMesh.opaqueAreas) > 0:
            resPath = mainMesh.opaqueAreas[0].effect.effectFilePath
        else:
            self.LogError('Unexpected program flow! Loading fallback shader.')
            resPath = 'res:/Graphics/Effect/Managed/Space/Planet/EarthlikePlanet.fx'
        resPath = resPath.replace('.fx', 'BlitHeight.fx')
        self.effectHeight.effectFilePath = resPath
        if self.__GetHeightMap1() is not None and self.__GetHeightMap2() is not None:
            param1 = trinity.TriTexture2DParameter()
            param1.name = 'NormalHeight1'
            self.heightMapResPath1 = util.GraphicFile(self.__GetHeightMap1())
            self.effectHeight.resources.append(param1)
            param2 = trinity.TriTexture2DParameter()
            param2.name = 'NormalHeight2'
            self.heightMapResPath2 = util.GraphicFile(self.__GetHeightMap2())
            self.effectHeight.resources.append(param2)
            param3 = trinity.Tr2FloatParameter()
            param3.name = 'Random'
            param3.value = float(self.itemID % 100)
            self.effectHeight.parameters.append(param3)
            param4 = trinity.Tr2FloatParameter()
            param4.name = 'TargetTextureHeight'
            param4.value = 2048
            self.effectHeight.parameters.append(param4)
        paramList = self.__GetPlanetShaderParameters('', 'trinity.Tr2Vector4Parameter')
        for param in paramList:
            self.effectHeight.parameters.append(param)

        paramList = self.__GetPlanetShaderParameters('', 'trinity.Tr2FloatParameter')
        for param in paramList:
            self.effectHeight.parameters.append(param)

        resList = self.__GetPlanetShaderParameters('', 'trinity.TriTexture2DParameter')
        for res in resList:
            self.effectHeight.resources.append(res)

    def __GetPopulation(self):
        """
        Returns the population of the planet
        """
        if self.attributes is None:
            raise RuntimeError('Planet was not loaded. Can not get population of an unloaded planet.')
        try:
            return self.attributes.population
        except Exception as e:
            self.LogError('Could not get attribute population.' + str(self.attributes), e)

    def __GetShaderPreset(self):
        """
        Returns the shader preset of the planet
        """
        if self.attributes is None:
            raise RuntimeError('Planet was not loaded. Can not get shaderPreset of an unloaded planet.')
        try:
            return self.attributes.shaderPreset
        except Exception as e:
            self.LogError('Could not get attribute shaderPreset.' + str(self.attributes), e)

    def __GetHeightMap1(self):
        """
        Returns the heightMap1 of the planet
        """
        if self.attributes is None:
            raise RuntimeError('Planet was not loaded. Can not get heightMap1 of an unloaded planet.')
        try:
            return self.attributes.heightMap1
        except Exception as e:
            self.LogError('Could not get attribute heightMap1.' + str(self.attributes), e)

    def __GetHeightMap2(self):
        """
        Returns the heightMap2 of the planet
        """
        if self.attributes is None:
            raise RuntimeError('Planet was not loaded. Can not get heightMap2 of an unloaded planet.')
        try:
            return self.attributes.heightMap2
        except Exception as e:
            self.LogError('Could not get attribute heightMap2.' + str(self.attributes), e)

    def __GetPlanetShaderParameters(self, paramName = '', paramType = ''):
        """
        Find all parameters of this type in all the planetshaders, could be more than one! so return list
        """
        retList = []
        if self.model == None:
            return retList
        planetParent = None
        for child in self.model.highDetail.children:
            if child.name == 'Planet':
                planetParent = child
                break

        if planetParent is not None:
            paramList = planetParent.Find(paramType)
            for param in paramList:
                if paramName == param.name or paramName == '':
                    retList.append(param)

        return retList

    def __GetBakeShaderParameter(self, paramName, paramType):
        """
        Find the parameter of this type in the bakeshader
        """
        if self.effectHeight == None:
            return
        paramList = self.effectHeight.Find(paramType)
        for param in paramList:
            if param.name == paramName:
                return param

    def __GetDistrictsShaderParameters(self, paramName):
        """
        Find all parameters of this type in all the districts, is usually more than one! so return list
        """
        retList = []
        for name, district in self.districts.iteritems():
            if district.pinEffect is not None:
                for param in district.pinEffect.parameters:
                    if param.name == paramName:
                        retList.append(param)

                for res in district.pinEffect.resources:
                    if res.name == paramName:
                        retList.append(res)

        return retList

    def __GetChildrenShaderParameters(self, paramName):
        """
        Find all parameters of this type in all the children, is usually more than one! so return list
        """
        retList = []
        shaderList = self.model.highDetail.children.Find('trinity.Tr2Effect')
        for shader in shaderList:
            for param in shader.parameters:
                if param.name == paramName:
                    retList.append(param)

            for res in shader.resources:
                if res.name == paramName:
                    retList.append(res)

        return retList

    def __CollectLargeResources(self):
        """
        Here we try to find all the really large resources (cloud textures, etc.) and put them in a
        list, so we can dump or re-create them as we want without deleting EvePlanet
        """
        if len(self.modelRes) > 0:
            return
        textureParamList = self.__GetPlanetShaderParameters('', 'trinity.TriTexture2DParameter')
        for textureParam in textureParamList:
            if textureParam.name != 'HeightMap':
                self.modelRes.append((textureParam.name, textureParam.resourcePath))

    def __FreeLargeResources(self):
        """
        Here we free all the large resources we have collected
        """
        for name, path in self.modelRes:
            modelResParamList = self.__GetPlanetShaderParameters(name, 'trinity.TriTexture2DParameter')
            for modelResParam in modelResParamList:
                modelResParam.resourcePath = ''

        self.__ApplyPlanetAttributesToDistricts()

    def __ReloadLargeResources(self):
        """
        Here we re-load all the large resources we have collected
        """
        for name, path in self.modelRes:
            modelResParamList = self.__GetPlanetShaderParameters(name, 'trinity.TriTexture2DParameter')
            for modelResParam in modelResParamList:
                if modelResParam.resourcePath != path:
                    modelResParam.resourcePath = path

        self.__ApplyPlanetAttributesToDistricts()

    def __ModifyPlanetShader(self):
        """
        Here we do some fun stuff, we change the cloudmaps and cloud paramters randomly (seeded with the current date)
        """
        if self.typeID == const.typePlanetEarthlike or self.typeID == const.typePlanetSandstorm:
            now = datetime.datetime.now()
            r = random.Random()
            r.seed(now.year + now.month * 30 + now.day + self.itemID)
            val = r.randint(1, 5)
            useDense = val % 5 == 0
            if self.typeID == const.typePlanetEarthlike:
                if useDense:
                    cloudMapIDs = (3857, 3858, 3859, 3860)
                    cloudCapMapIDs = (3861, 3862, 3863, 3864)
                else:
                    cloudMapIDs = (3848, 3849, 3851, 3852)
                    cloudCapMapIDs = (3853, 3854, 3855, 3856)
            else:
                cloudMapIDs = (3956, 3957, 3958, 3959)
                cloudCapMapIDs = (3960, 3961, 3962, 3963)
            cloudMapIdx = r.randint(0, 3)
            cloudCapMapIdx = r.randint(0, 3)
            cloudCapTexResPath = util.GraphicFile(cloudCapMapIDs[cloudCapMapIdx])
            cloudTexResPath = util.GraphicFile(cloudMapIDs[cloudMapIdx])
            if self.largeTextures:
                cloudCapTexResPath = cloudCapTexResPath.replace('.dds', '_HI.dds')
                cloudTexResPath = cloudTexResPath.replace('.dds', '_HI.dds')
            cloudCapParamList = self.__GetPlanetShaderParameters('CloudCapTexture', 'trinity.TriTexture2DParameter')
            for cloudCapParam in cloudCapParamList:
                cloudCapParam.resourcePath = cloudCapTexResPath

            cloudParamList = self.__GetPlanetShaderParameters('CloudsTexture', 'trinity.TriTexture2DParameter')
            for cloudParam in cloudParamList:
                cloudParam.resourcePath = cloudTexResPath

            cloudsBrightness = r.random() * 0.4 + 0.6
            cloudsTransparency = r.random() * 2.0 + 1.0
            cloudsFactorsParamList = self.__GetPlanetShaderParameters('CloudsFactors', 'trinity.Tr2Vector4Parameter')
            for cloudsFactorsParam in cloudsFactorsParamList:
                cloudsFactorsParam.v3 = cloudsTransparency
                cloudsFactorsParam.v2 = cloudsBrightness

        if self.typeID is const.typePlanetOcean or self.typeID is const.typePlanetEarthlike:
            if self.__GetPopulation() == 0:
                for textureParamName in ['CityLight', 'CityDistributionTexture', 'CityDistributionMask']:
                    textureParamList = self.__GetPlanetShaderParameters(textureParamName, 'trinity.TriTexture2DParameter')
                    for textureParam in textureParamList:
                        textureParam.resourcePath = ''

                coverageFactorsParamList = self.__GetPlanetShaderParameters('CoverageFactors', 'trinity.Tr2Vector4Parameter')
                for coverageFactorsParam in coverageFactorsParamList:
                    coverageFactorsParam.v4 = 0.0

    def __ApplyPlanetAttributesToDistricts(self):
        """
        a lot of hard-coded shader parameter names here. If this gets too big we need a better
        aolution to propagate planet attributes to children
        """

        def PropagateParamToDistrict(src, dest):
            srcParamList = self.__GetPlanetShaderParameters(src, 'trinity.Tr2Vector4Parameter')
            destParamList = self.__GetDistrictsShaderParameters(dest)
            for srcParam in srcParamList:
                if srcParam not in destParamList:
                    for destParam in destParamList:
                        destParam.value = srcParam.value

                    break

        def PropagateResPathToDistrict(src, dest):
            srcParamList = self.__GetPlanetShaderParameters(src, 'trinity.TriTexture2DParameter')
            destParamList = self.__GetDistrictsShaderParameters(dest)
            for srcParam in srcParamList:
                if srcParam not in destParamList:
                    for destParam in destParamList:
                        destParam.resourcePath = srcParam.resourcePath

                    break

        def PropagateResToDistrict(src, dest):
            srcParamList = self.__GetPlanetShaderParameters(src, 'trinity.TriTexture2DParameter')
            destParamList = self.__GetDistrictsShaderParameters(dest)
            for srcParam in srcParamList:
                if srcParam not in destParamList:
                    for destParam in destParamList:
                        destParam.SetResource(srcParam.resource)

                    break

        def PropagateResToChildren(src, dest):
            srcParamList = self.__GetPlanetShaderParameters(src, 'trinity.TriTexture2DParameter')
            destParamList = self.__GetChildrenShaderParameters(dest)
            for srcParam in srcParamList:
                if srcParam not in destParamList:
                    for destParam in destParamList:
                        destParam.SetResource(srcParam.resource)

                    break

        if len(self.districts) != 0:
            PropagateParamToDistrict('CityLightColor', 'PermanentGlowColor')
            PropagateParamToDistrict('DetailFactors', 'DetailFactors')
            PropagateParamToDistrict('MiscFactors', 'MiscFactors')
            PropagateResPathToDistrict('GroundScattering1', 'GroundScattering1')
            PropagateResPathToDistrict('PolesGradient', 'PolesGradient')
            PropagateResPathToDistrict('FillTexture', 'FillTexture')
            PropagateResToDistrict('HeightMap', 'HeightMap')
        if self.model is not None:
            if len(self.model.highDetail.children) != 0:
                PropagateResToChildren('HeightMap', 'HeightMap')
