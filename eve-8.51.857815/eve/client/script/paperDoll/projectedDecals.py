#Embedded file name: eve/client/script/paperDoll\projectedDecals.py
import trinity
import uthread
import blue
import copy
import yaml
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollCommonFunctions as PD
import eve.client.script.paperDoll.commonClientFunctions as pdCcF
import eve.common.script.paperDoll.paperDollDataManagement as pdDm
ST_SHADERRES = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarBRDF.fx'
RT_SHADERRES = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarTattooBRDF.fx'
BK_SHADERRES = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarTattooBaking.fx'
INV_SHADERRES = 'res:/Graphics/Effect/Managed/Interior/Avatar/InvisibleAvatar.fx'
EO_SHADERRES = 'res:/Graphics/Effect/Utility/Compositing/ExpandOpaque.fx'
MASK_SHADERRES = 'res:/Graphics/Effect/Managed/Interior/Avatar/SkinnedAvatarTattooMaskBaking.fx'
DECAL_PROJECTION_DISABLED = -1.0
DECAL_PROJECTION_PLANAR = 0.0
DECAL_PROJECTION_CYLINDRICAL = 1.0
DECAL_PROJECTION_CAMERA = 2.0
DECAL_PROJECTION_EO_LOD_THRESHOLD = 1

def ShowTexture(texture, showAlpha = False):
    import app.Common.RenderWindow as rw
    f = rw.CreateTextureWindow(texture, showAlpha)
    f.Show()


class DecalBaker(object):
    """
    DecalBaker is responsible for creating textures out of decals that can be applied to the
    doll that the decal was projected onto.
    It is the single point of entry for communication between a decal and the underlying rendering
    system that bakes it out.
    """
    __guid__ = 'paperDoll.DecalBaker'

    def __init__(self, factory):
        self.factory = factory
        self.__avatar = None
        self._gender = None
        self.bakeScene = None
        self.size = None
        self.isReady = False
        self.doingAvatar = False
        self.doingDecal = False
        self.bakingTasklet = None
        self.avatarShaderSettingTasklet = None
        self.decalSettingTasklet = None
        if pdDef.GENDER_ROOT:
            self.femalePath = 'res:\\Graphics\\Character\\Female\\Paperdoll'
            self.malePath = 'res:\\Graphics\\Character\\Male\\Paperdoll'
        else:
            self.femalePath = 'res:\\Graphics\\Character\\Modular\\Female'
            self.malePath = 'res:\\Graphics\\Character\\Modular\\Male'
        self.femaleBindPose = self.GetBindPose(pdDef.FEMALE_DECAL_BINDPOSE)
        self.maleBindPose = self.GetBindPose(pdDef.MALE_DECAL_BINDPOSE)

    def Initialize(self):
        self.doingAvatar = False
        self.doingDecal = False

    def HasAvatar(self):
        """
        Returns true if the decalbaker has an avatar that can be used for baking
        """
        return self.__avatar is not None and type(self.__avatar) is trinity.Tr2IntSkinnedObject

    def GetBindPose(self, resPath):
        updater = trinity.Tr2GrannyAnimation()
        updater.resPath = resPath
        return updater

    def SetSize(self, size):
        """
        Pre: size is a tuple of integers
        """
        if not (type(size) is tuple or type(size) is list) and len(size) == 2:
            raise TypeError('DecalBaker::SetSize - Size is not a tuple or list of length 2!')
        self.size = size

    def __DoBlendShapes(self, doll):
        """
        Applies blendshapes from the doll to the decalbaker's avatar
        """
        self.factory.ApplyMorphTargetsToMeshes(self.__avatar.visualModel.meshes, doll.buildDataManager.GetMorphTargets())

    def __CreateNudeAvatar(self, doll):
        if doll.gender == pdDef.GENDER.FEMALE:
            genderPath = self.femalePath
        else:
            genderPath = self.malePath
        self._gender = doll.gender
        avatar = trinity.Tr2IntSkinnedObject()
        avatar.visualModel = self.factory.CreateVisualModel(doll.gender)
        avatar.name = 'TattooBakingAvatar'
        bodyParts = []
        for nudePartModularPath in pdDef.DEFAULT_NUDE_PARTS:
            bodyPartTuple = None
            if pdDef.DOLL_PARTS.HEAD in nudePartModularPath:
                headMods = doll.buildDataManager.GetModifiersByCategory(pdDef.DOLL_PARTS.HEAD)
                if headMods:
                    headMod = doll.buildDataManager.GetModifiersByCategory(pdDef.DOLL_PARTS.HEAD)[0]
                    if headMod.redfile:
                        bodyPartTuple = (headMod.name, blue.resMan.LoadObject(headMod.redfile))
            if not bodyPartTuple:
                mod = self.factory.CollectBuildData(self._gender, nudePartModularPath)
                bodyPartTuple = (mod.name, blue.resMan.LoadObject(mod.redfile))
            bodyParts.append(bodyPartTuple)

        PD.BeFrameNice()
        for bodyPartTuple in bodyParts:
            modname, bodyPart = bodyPartTuple
            if bodyPart:
                for mesh in bodyPart.meshes:
                    mesh.name = modname
                    if len(mesh.opaqueAreas) > 0:
                        areasCount = mesh.GetAreasCount()
                        for i in xrange(areasCount):
                            areas = mesh.GetAreas(i)
                            if areas and areas != mesh.opaqueAreas:
                                del areas[:]

                        avatar.visualModel.meshes.append(mesh)

        self.__avatar = avatar
        self.__DoBlendShapes(doll)
        if doll.gender == pdDef.GENDER.FEMALE:
            bindPose = self.femaleBindPose
        else:
            bindPose = self.maleBindPose
        avatar.animationUpdater = bindPose
        clip = bindPose.grannyRes.GetAnimationName(0)
        bindPose.PlayAnimationEx(clip, 0, 0, 0)
        avatar.ResetAnimationBindings()
        bindPose.EndAnimation()

    def CreateTargetAvatarFromDoll(self, doll):
        """
        Creates the target avatar that is used for projecting the decal onto based on the doll instance.
        That avatar is completely nude, but matches the doll's blendshapes.
        The projection baking shader is then applied to this avatar.
        It is enough to set avatar once when baking out multiple decals that will project onto it.
        """
        self.doingAvatar = True
        self.__CreateNudeAvatar(doll)

        def PrepareAvatar_t():
            try:
                self.SetShader_t(self.__avatar, [], BK_SHADERRES, False)
            finally:
                self.doingAvatar = False

        self.avatarShaderSettingTasklet = uthread.new(PrepareAvatar_t)
        uthread.schedule(self.avatarShaderSettingTasklet)

    def CreateTargetsOnModifier(self, modifier, asRenderTargets = False):
        """
        Checks for existance of valid targets on the modifier according to size and rendertarget usage.
        If that check fails the method will create targets so the modifier contains valid maps for 
        rendering out the decal.
        """
        textureFormat = trinity.PIXEL_FORMAT.B8G8R8A8_UNORM

        def validateTarget(target, width, height):
            if not (target and target.isGood and target.depth > 0):
                return False
            if target.width != width or target.height != height:
                return False
            return True

        if modifier.decalData.bodyEnabled:
            modifier.mapD[pdDef.DOLL_PARTS.BODY] = trinity.TriTextureRes(trinity.Tr2RenderTarget(self.size[0] / 2, self.size[1], 1, textureFormat))
        if modifier.decalData.headEnabled:
            modifier.mapD[pdDef.DOLL_PARTS.HEAD] = trinity.TriTextureRes(trinity.Tr2RenderTarget(self.size[0] / 2, self.size[1] / 2, 1, textureFormat))

    def BakeDecalToModifier(self, decal, projectedDecalModifier):
        """
        Pre: 
            Decal is an instance of ProjectedDecal
            Avatar has been created for baking
            
        Post:
            projectedDecalModifier.decalData contains the given decal and diffuse maps on the modifier
            contain textures for body and head.
        
        Summary: Bakes out the decal using currently set avatar, the targets for outputted textures are 
        the diffuse maps for body and head in the modifier.
        """
        while self.doingAvatar:
            PD.Yield(frameNice=False)

        if type(self.__avatar) is not trinity.Tr2IntSkinnedObject:
            raise TypeError('DecalBaker::DoPrepare - Avatar is not set!')
        if type(decal) is not ProjectedDecal:
            raise TypeError('DecalBaker::BakeDecalToModifier - decal is not an instance of PaperDoll::ProjectedDecal!')
        self.isReady = False
        self.doingDecal = False
        if projectedDecalModifier.decalData != decal:
            projectedDecalModifier.decalData = decal

        def PrepareDecal_t():
            self.doingDecal = True
            self.SetDecal_t(self.__avatar, decal, True, True)
            self.doingDecal = False

        self.decalSettingTasklet = uthread.new(PrepareDecal_t)
        self.CreateTargetsOnModifier(projectedDecalModifier)
        self.bakingTasklet = uthread.new(self.DoBake_t, projectedDecalModifier)

    def _ExpandOpaque(self, bodyPart, targetTex):
        """
        Using pre-generated masks, we bleed the opaque accross the edges defined by said masks.
        This reduces visible seams when the tattoos have been projected in object space so that 
        their pixels in UV space aren't continuous.
        """
        eoMaskPath = 'res:/graphics/character/global/tattoomask/{0}_opaque_mask_{1}.dds'.format(self._gender, bodyPart)
        eoMaskRes = blue.resMan.GetResource(eoMaskPath)
        fx = trinity.Tr2Effect()
        fx.effectFilePath = EO_SHADERRES
        while eoMaskRes.isLoading or fx.effectResource.isLoading:
            PD.Yield()

        tex = trinity.TriTexture2DParameter()
        tex.name = 'Mask'
        tex.SetResource(eoMaskRes)
        fx.resources.append(tex)
        v = trinity.Tr2Vector2Parameter()
        v.name = 'gMaskSize'
        v.value = (eoMaskRes.width, eoMaskRes.height)
        fx.parameters.append(v)
        tex = trinity.TriTexture2DParameter()
        tex.name = 'Texture'
        tex.SetResource(targetTex)
        fx.resources.append(tex)
        v = trinity.Tr2Vector2Parameter()
        v.name = 'gTextureSize'
        v.value = (targetTex.width, targetTex.height)
        fx.parameters.append(v)
        fx.RebuildCachedData()
        vp = trinity.TriViewport()
        vp.width = targetTex.width
        vp.height = targetTex.height
        expandedRT = trinity.Tr2RenderTarget(vp.width, vp.height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        rj = trinity.CreateRenderJob('Expanding Opaque')
        rj.PushRenderTarget(expandedRT)
        rj.SetProjection(trinity.TriProjection())
        rj.SetView(trinity.TriView())
        rj.SetViewport(vp)
        rj.PushDepthStencil(None)
        rj.Clear((0.0, 0.0, 0.0, 0.0))
        rj.SetStdRndStates(trinity.RM_FULLSCREEN)
        rj.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        rj.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        rj.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        rj.RenderEffect(fx)
        rj.SetRenderTarget(targetTex.wrappedRenderTarget)
        rj.RenderTexture(expandedRT)
        rj.PopRenderTarget()
        rj.PopDepthStencil()
        rj.ScheduleChained()
        rj.WaitForFinish()

    def _Bake(self, targetTex, transform):
        self.SetShaderValue(self.__avatar, 'TattooVSUVTransform', transform)
        size = (targetTex.width, targetTex.height)
        renderTarget = targetTex.wrappedRenderTarget
        sourceVP = trinity.TriViewport()
        sourceVP.width = size[0]
        sourceVP.height = size[1]
        rj = trinity.CreateRenderJob('Baking out source decal texture')
        rj.PushRenderTarget(renderTarget)
        rj.SetProjection(trinity.TriProjection())
        rj.SetView(trinity.TriView())
        rj.SetViewport(sourceVP)
        rj.PushDepthStencil(None)
        rj.Clear((0.0, 0.0, 0.0, 0.0))
        rj.SetStdRndStates(trinity.RM_FULLSCREEN)
        rj.Update(self.bakeScene)
        rj.RenderScene(self.bakeScene)
        rj.PopRenderTarget()
        rj.PopDepthStencil()
        rj.ScheduleChained()
        rj.WaitForFinish()

    def DoBake_t(self, projectedDecalModifier):
        while self.doingDecal or self.doingAvatar:
            PD.Yield()

        self.bakeScene = trinity.WodBakingScene()
        self.bakeScene.Avatar = self.__avatar
        if projectedDecalModifier.decalData.bodyEnabled:
            while not projectedDecalModifier.mapD[pdDef.DOLL_PARTS.BODY].isPrepared:
                PD.Yield(frameNice=False)

            bodyTex = projectedDecalModifier.mapD[pdDef.DOLL_PARTS.BODY]
            self._Bake(bodyTex, (0.0, 0.0, 2.0, 1.0))
            self._ExpandOpaque(pdDef.DOLL_PARTS.BODY, bodyTex)
        elif projectedDecalModifier.mapD.get(pdDef.DOLL_PARTS.BODY):
            del projectedDecalModifier.mapD[pdDef.DOLL_PARTS.BODY]
        if projectedDecalModifier.decalData.headEnabled:
            while not projectedDecalModifier.mapD[pdDef.DOLL_PARTS.HEAD].isPrepared:
                PD.Yield(frameNice=False)

            headTex = projectedDecalModifier.mapD[pdDef.DOLL_PARTS.HEAD]
            self._Bake(headTex, (-0.5, 0.0, 2.0, 2.0))
            self._ExpandOpaque(pdDef.DOLL_PARTS.HEAD, headTex)
        elif projectedDecalModifier.mapD.get(pdDef.DOLL_PARTS.HEAD):
            del projectedDecalModifier.mapD[pdDef.DOLL_PARTS.HEAD]
        self.bakeScene = None
        self.isReady = True

    def SetShader_t(self, avatar, targetsToIgnore, shaderres, allTargets = False):
        try:
            effect = trinity.Tr2Effect()
            effect.effectFilePath = shaderres
            while effect.effectResource.isLoading:
                PD.Yield()

            for mesh in avatar.visualModel.meshes:
                areasList = [mesh.opaqueAreas, mesh.decalAreas, mesh.transparentAreas]
                if allTargets or mesh.name not in targetsToIgnore:
                    for areas in areasList:
                        for area in areas:
                            transformUV = None
                            for p in area.effect.parameters:
                                if p.name == 'TransformUV0':
                                    transformUV = p.value
                                    break

                            area.effect.effectFilePath = shaderres
                            area.effect.PopulateParameters()
                            area.effect.RebuildCachedData()
                            for p in area.effect.parameters:
                                if p.name == 'TransformUV0':
                                    p.value = transformUV
                                    break

        except TaskletExit:
            raise

    def SetShaderValue(self, avatar, name, value):
        """
        For all shaders on avatar, the parameters have name == 'name' are set to value 'value'.
        """
        for mesh in avatar.visualModel.meshes:
            for effect in pdCcF.GetEffectsFromMesh(mesh):
                effect.StartUpdate()
                for p in effect.parameters:
                    if p.name == name:
                        p.value = value
                        break

                effect.RebuildCachedData()
                effect.EndUpdate()

    def SetDecal_t(self, avatar, decal, setTexture, setMask):
        """
        Sets decal texture and mask map defined in 'decal' to all meshes in the avatar,
        except for the meshes that have their names in 'ignoreTargets'
        
        Precondition: The effect _must_ have loaded prior to calling this function.        
        """
        if decal is None:
            return
        while self.doingAvatar or decal.BusyLoading():
            PD.Yield(frameNice=False)

        for mesh in iter(avatar.visualModel.meshes):
            for effect in pdCcF.GetEffectsFromMesh(mesh):
                effect.StartUpdate()
                for p in effect.parameters:
                    valuesToSet = None
                    if p.name == 'TattooYawPitchRoll':
                        valuesToSet = decal.GetYPR()
                    elif p.name == 'TattooPosition':
                        valuesToSet = decal.GetPositionAndScale()
                    elif p.name == 'TattooOptions':
                        valuesToSet = decal.GetOptions()
                    elif p.name == 'TattooDimensions':
                        valuesToSet = decal.GetDimensions()
                    elif p.name == 'TattooAspectRatio' and hasattr(decal, 'aspectRatio'):
                        valuesToSet = decal.aspectRatio
                    elif p.name == 'TattooPickingLayer':
                        valuesToSet = decal.layer
                    if type(valuesToSet) == tuple:
                        valLen = len(valuesToSet)
                        if valLen < len(p.value):
                            valuesToSet = valuesToSet + p.value[valLen:]
                    if valuesToSet:
                        p.value = valuesToSet

                resourceNameFound = False
                if setTexture:
                    resourceNameFound = self.SetTexture_t('TattooTextureMap', decal.textureResource, effect)
                if setMask and resourceNameFound:
                    resourceNameFound = self.SetTexture_t('TattooTextureMask', decal.maskResource, effect)
                effect.RebuildCachedData()
                effect.EndUpdate()

    def SetTexture_t(self, name, texture, effect):
        """
        Precondition: 
            Must run in a tasklet. Shader must have been set.
            'texture' is either a resource path or a resource.        
        """
        for i, r in enumerate(effect.resources):
            if r.name == name:
                r.SetResource(texture)
                return True

        return False


class ProjectedDecal(object):
    """
    Each instance of this class contains all the neccesary data to
    project a decal. It specifies the resources and values needed
    for the various projection shaders.
    """
    __guid__ = 'paperDoll.ProjectedDecal'

    def __init__(self):
        self.layer = 0
        self.azimuth = 0.0
        self.incline = 1.5707963267948966
        self.bodyEnabled = True
        self.headEnabled = True
        self.posx = 0.0
        self.posy = 0.0
        self.posz = 0.0
        self.scale = 0.0
        self.aspectRatio = 1.0
        self.angleRotation = 180.0
        self.mode = DECAL_PROJECTION_DISABLED
        self.flipx = False
        self.flipy = False
        self.offsety = 0.0
        self.offsetx = 0.0
        self.radius = 2.0
        self.height = 4.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.planarBeta = 0.0
        self.planarScale = 0.0
        self.maskPathEnabled = False
        self.texturePath = ''
        self.maskPath = ''
        self.label = ''
        self.textureResource = None
        self.maskResource = None

    def __str__(self):
        """
        Returns this decal in a string format
        """
        return yaml.dump(self.__getstate__(), default_flow_style=False, Dumper=yaml.CDumper)

    def __getstate__(self):
        state = dict()
        for key, value in self.__dict__.iteritems():
            if type(value) is not trinity.TriTextureRes:
                state[key] = copy.copy(value)
            else:
                state[key] = None

        return state

    def __eq__(self, other):
        if not other:
            return False
        typesThatMatter = (float,
         bool,
         str,
         int)
        for key, val in other.__dict__.iteritems():
            if key not in self.__dict__:
                return False
            if type(self.__dict__[key]) in typesThatMatter:
                if self.__dict__[key] != val:
                    return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def BusyLoading(self):
        if self.texturePath and not self.textureResource:
            raise AttributeError('PaperDoll::ProjectedDecal - Decal has texturepath defined but no texture resource and is not loading it!')
        if self.maskPath and not self.maskResource:
            raise AttributeError('PaperDoll::ProjectedDecal - Decal has maskpath defined but no texture resource and is not loading it!')
        loading = self.textureResource and self.textureResource.isLoading or self.maskResource and self.maskResource.isLoading
        return loading

    def __GetResourceSetPath(self, path, pathMember):
        if path:
            setattr(self, pathMember, path)
            return blue.resMan.GetResource(str(path))
        else:
            return None

    def SetTexturePath(self, path):
        """
        Sets the texture path used for projection, 
        loads up the resource associated with that path and stores it in self.textureResource
        """
        self.textureResource = self.__GetResourceSetPath(path, 'texturePath')

    def SetMaskPath(self, path):
        """
        Sets the mask path used for projection, 
        loads up the resource associated with that path and stores it in self.maskResource
        """
        self.maskResource = self.__GetResourceSetPath(path, 'maskPath')

    def SetCylindricalProjection(self):
        self.mode = DECAL_PROJECTION_CYLINDRICAL

    def SetPlanarProjection(self):
        self.mode = DECAL_PROJECTION_PLANAR

    def SetDisabledProjection(self):
        self.mode = DECAL_PROJECTION_DISABLED

    def SetPosition(self, posx, posy, posz):
        self.posx = posx
        self.posy = posy
        self.posz = posz

    def GetPositionAndScale(self):
        return (self.posx,
         self.posy,
         self.posz,
         self.scale)

    def SetOptions(self, angleRotation, flipX, flipY, offsetY = 0.0, offsetX = 0.0):
        self.angleRotation = angleRotation
        self.flipx = flipX
        self.flipy = flipY
        self.offsety = offsetY
        self.offsetx = offsetX

    def GetOptions(self):
        flipPack = 10.0 * float(self.flipy) + float(self.flipx)
        return (self.angleRotation,
         flipPack,
         self.offsety,
         self.offsetx)

    def SetDimensions(self, radius, height):
        self.radius = radius
        self.height = height

    def GetDimensions(self):
        if self.mode == DECAL_PROJECTION_PLANAR:
            return (self.planarBeta, self.planarScale, float(self.maskPathEnabled))
        else:
            return (self.radius, self.height, float(self.maskPathEnabled))

    def SetYPR(self, yaw, pitch, roll):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def GetYPR(self):
        return (self.yaw,
         self.pitch,
         self.roll,
         self.mode)

    @staticmethod
    def Load(source):
        """
        'source' is either a respath or a decal instance that needs to be fixed
        because its legacy.
        Backwards compatible decal loader. Use this to load decals at all times.        
        It supports loading in decals that might have been saved out before more attributes
        were added to the class.
        """
        inst = source
        if isinstance(source, basestring):
            inst = pdDm.LoadYamlFileNicely(source)
        projectedDecal = ProjectedDecal()
        for key, val in inst.__dict__.iteritems():
            if key in projectedDecal.__dict__:
                projectedDecal.__dict__[key] = val

        if inst.texturePath:
            projectedDecal.SetTexturePath(inst.texturePath)
        if inst.maskPath:
            projectedDecal.SetMaskPath(inst.maskPath)
        return projectedDecal

    @staticmethod
    def Save(source, resPath):
        """
        Dumps the source as text and saves it in a .proj file to the given respath.
        """
        f = file(resPath, 'w')
        yaml.dump(source, f, default_flow_style=False, Dumper=yaml.CDumper)
        f.flush()
        f.close()


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('paperDoll', locals())
