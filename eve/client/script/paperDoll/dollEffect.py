#Embedded file name: eve/client/script/paperDoll\dollEffect.py
import trinity
import blue
import uthread
import random
import paperDoll as PD
AURA_EFFECT_RES_PATH = 'res:/Graphics/Effect/Managed/Interior/Avatar/AuraAvatar2.fx'
NUDE_EFFECT_AVATAR_RESPATH = 'res:/Graphics/Character/Global/Effect/Aura/AuraFemale/AuraFemale.red'

def GetNudeEffectAvatar():
    return blue.resMan.LoadObject(NUDE_EFFECT_AVATAR_RESPATH)


class NameGenerator(object):
    currentIndex = 0

    @staticmethod
    def GetUniqueName(effectName):
        name = '%s%s' % (effectName, NameGenerator.currentIndex)
        NameGenerator.currentIndex += 1
        return name


class AvatarEffect(object):
    """
    Encapsulates a Tr2Effect and a EffectAvatar to be placed onto an avatar.
    Subclass this class to create a proper effect. See AuraEffect for example on how
    to do that.
    """
    __guid__ = 'paperDoll.AvatarEffect'

    def __init__(self):
        object.__init__(self)
        self.effect = None
        self.effectAvatar = None
        self.isLoaded = False
        self.name = NameGenerator.GetUniqueName(self.__class__.__name__)

    def MakeEffect(self):
        """
        Overwrite this function to make self.effect a valid Tr2Effect
        Must return an instance of Tr2Effect
        
        MakeEffect is always called in the context of a tasklet.
        """
        raise NotImplementedError()

    def ConfigureEffectAvatar(self):
        """
        Overwrite this function to make self.effectAvatar contain the correct avatar for the effect.
        
        ConfigureEffectAvatar is always called in the context of a tasklet.
        """
        raise NotImplementedError()

    def ExposeEffectAttributes(self):
        """
        Generate attributes for effect resources and parameters and puts
        them dynamically on this instance.
        
        ExposeEffectAttributes is always called in the context of a tasklet.
        """
        for i, each in enumerate(self.effect.resources):
            setattr(self, each.name, self.effect.resources[i])

        for i, each in enumerate(self.effect.parameters):
            setattr(self, each.name, self.effect.parameters[i])

    def Load(self, callBack = None):
        """
        Loads and prepares the AvatarEffect. Must be called atleast once prior to calling ApplyEffect.
        Happens inside a tasklet. self.isLoaded is set to True once loading has finished.
        """

        def fun_t():
            self.ConfigureEffectAvatar()
            self.MakeEffect()
            self.ExposeEffectAttributes()
            self.isLoaded = True
            if callBack:
                callBack()

        uthread.new(fun_t)

    def ApplyEffect(self, avatar):
        """
        Applies the effect to an 'avatar'.
        Pre-condition: self.isLoaded must be True                
        """
        for attachedObject in avatar.attachedObjects:
            if attachedObject.name == self.name:
                return

        self.effectAvatar.name = self.name
        if avatar.__bluetype__ == 'trinity.WodExtSkinnedObject':
            tempAvatar = trinity.WodExtSkinnedObject()
            tempAvatar.visualModel = self.effectAvatar.visualModel.CopyTo()
            tempAvatar.name = self.effectAvatar.name
            del self.effectAvatar
            self.effectAvatar = tempAvatar
        avatar.attachedObjects.append(self.effectAvatar)
        self.effectAvatar.animationUpdater = avatar.animationUpdater
        self.effectAvatar.rotation = avatar.rotation
        self.effectAvatar.translation = avatar.translation
        self.effectAvatar.scaling = avatar.scaling
        for mesh in self.effectAvatar.visualModel.meshes:
            for area in PD.MeshAreaIterator(mesh):
                area.effect = self.effect

            for area in mesh.opaqueAreas:
                mesh.transparentAreas.append(area)
                del mesh.opaqueAreas[:]

    def RemoveEffect(self, avatar):
        """
        Removes this effect from the avatar and sets the effect into unloaded state
        """
        if self.effectAvatar in avatar.attachedObjects:
            avatar.attachedObjects.remove(self.effectAvatar)
        self.effectAvatar = None
        self.effect = None


class AuraEffect(AvatarEffect):
    """
    Sets up aura effect that can be applied to a single doll
    """
    __guid__ = 'paperDoll.AuraEffect'

    def __init__(self, curveSets = None):
        AvatarEffect.__init__(self)
        self.curveSet = None

    def DoCurveBindings(self):
        self.effect.PopulateParameters()
        self.curveSet = trinity.TriCurveSet()
        self.effectAvatar.curveSets.append(self.curveSet)
        bm = None
        for param in self.effect.parameters:
            if param.name == 'BlurMaskUV':
                bm = param
                break

        tx = None
        for param in self.effect.parameters:
            if param.name == 'AuraTextureUV':
                tx = param
                break

        def BindValueToExpression(destObj, valueName, expression):
            curve = trinity.Tr2ScalarExprCurve()
            curve.expr = expression
            curve.length = 86400
            bind = trinity.TriValueBinding()
            bind.destinationObject = destObj
            bind.destinationAttribute = valueName
            bind.sourceObject = curve
            bind.sourceAttribute = 'currentValue'
            self.curveSet.curves.append(curve)
            self.curveSet.bindings.append(bind)

        seed = random.random() * 3
        BindValueToExpression(bm, 'v1', 'sin(2*time+%f)/3.0 + perlin(value, %f-1, 2.5, 3.3)' % (seed, seed))
        BindValueToExpression(bm, 'v2', 'time/5.0')
        BindValueToExpression(tx, 'v1', 'sin(1.2*time+%f)/3.3 + perlin(value, %f-1, 5.5, 3.3)' % (seed, seed))
        BindValueToExpression(tx, 'v2', '-1.0*time/3.0')

    def MakeEffect(self):
        """
        Creates an instance of AuraEffect and configures its resources.
        MakeEffect is always called in the context of a tasklet.
        """
        self.effect = trinity.Tr2Effect()
        self.effect.effectFilePath = AURA_EFFECT_RES_PATH
        while self.effect.effectResource.isLoading:
            PD.Yield()

        self.effect.PopulateParameters()
        blurMask = blue.resMan.GetResource('res:/Graphics/Decals/caustics4.dds')
        auraTexture = blue.resMan.GetResource('res:/Graphics/Decals/caustics4.dds')
        setCount = 0
        for resource in self.effect.resources:
            if resource.name == 'BlurMask':
                resource.SetResource(blurMask)
                setCount += 1
            elif resource.name == 'AuraTexture':
                resource.SetResource(auraTexture)
                setCount += 1
            if setCount == 2:
                break

        self.effect.RebuildCachedData()

    def ConfigureEffectAvatar(self):
        """
        Overwrite this function to make self.effectAvatar contain the correct avatar for the effect.
        """
        self.effectAvatar = GetNudeEffectAvatar()

    def ApplyEffect(self, avatar):
        """
        Extended to handle curve bindings
        """
        AvatarEffect.ApplyEffect(self, avatar)
        self.DoCurveBindings()
        self.curveSet.Play()

    def RemoveEffect(self, avatar):
        """
        Extended to remove curve bindings when effect is being removed.
        """
        if self.curveSet:
            self.effectAvatar.curveSets.remove(self.curveSet)
        self.curveSet = None
        AvatarEffect.RemoveEffect(self, avatar)
