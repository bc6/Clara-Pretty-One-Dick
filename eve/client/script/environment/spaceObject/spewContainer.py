#Embedded file name: eve/client/script/environment/spaceObject\spewContainer.py
"""
SpaceObject code for Spew Container
"""
import blue
import geo2
import audio2
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import evegraphics.settings as gfxsettings
import hackingcommon.hackingConstants as hackingConst

class SpewContainer(SpaceObject):
    """
    This class wraps client balls that are spew containers
    """

    def __init__(self):
        super(SpewContainer, self).__init__()
        self.explodeOnRemove = True

    def Assemble(self):
        self.UnSync()
        if self.model is not None:
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        self.spewFX = self.LoadFX()
        slimItem = self.typeData.get('slimItem')
        if slimItem.hackingSecurityState is not None:
            state = slimItem.hackingSecurityState
        else:
            state = hackingConst.hackingStateSecure
        self.SetSecurityState(state)
        self.SetupSharedAmbientAudio()
        self.SetStaticRotation()

    def SetSecurityState(self, securityState):
        """
        Sets the security state on this container and applies animations accordingly.
        """
        if securityState == hackingConst.hackingStateBeingHacked:
            self.TriggerAnimation('hacking')
        elif securityState == hackingConst.hackingStateHacked:
            self.TriggerAnimation('empty')
        elif securityState == hackingConst.hackingStateSecure:
            self.TriggerAnimation('idle')

    def PlaySpewEffect(self, spewCone):
        if self.model:
            self.ClearFX(self.model, self.spewFX)
            self.PlayFX(self.model, self.spewFX, spewCone)
            self.PlaySoundFX(self.model, spewCone)
        else:
            self.LogError('PlaySpewEffect failed - no model exists for the space object!')

    def PlaySoundFX(self, targetObject, spewCone):
        position, direction = spewCone
        audioEmitter = audio2.AudEmitter(targetObject.name + '_src')
        translatedPosition = geo2.Vec3Add(targetObject.worldPosition, position)
        audioEmitter.SetPosition(direction, translatedPosition)
        audioEmitter.SetAttenuationScalingFactor(10000)
        audioEmitter.SendEvent('scattering_spew_play')

    def LoadFX(self):
        """
        Loads and returns the graphics effect for spewing
        """
        spewGraphicsID = 20306
        graphicEntry = cfg.graphics.Get(spewGraphicsID)
        fx = blue.resMan.LoadObject(graphicEntry.graphicFile)
        return fx

    def ClearFX(self, targetObject, fx):
        """
        Removes any existing spew effect from the target object
        """
        for obj in list(targetObject.children):
            if obj.name == fx.name:
                targetObject.children.remove(obj)

    def PlayFX(self, targetObject, fx, spewCone):
        """
        Playes the spew effect on the target object, using the information supplied in the spewCone
        """
        position, direction = spewCone
        targetObject.children.append(fx)
        fx.scaling = (2000.0, 3000.0, 2000.0)
        rotation = geo2.QuaternionRotationArc((0.0, 1.0, 0.0), direction)
        fx.translation = position
        fx.rotation = rotation
        for curveSet in fx.curveSets:
            curveSet.scale = 0.15
            curveSet.PlayFrom(0.2)

    def Explode(self):
        if not gfxsettings.Get(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED):
            return False
        explosionURL, (delay, scaling) = self.GetExplosionInfo()
        return SpaceObject.Explode(self, explosionURL=explosionURL, managed=True, delay=delay, scaling=scaling)
