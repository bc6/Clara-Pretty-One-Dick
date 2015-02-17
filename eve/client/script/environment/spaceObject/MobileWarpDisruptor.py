#Embedded file name: eve/client/script/environment/spaceObject\MobileWarpDisruptor.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
SOUND_EFFECT_EMITTER_NAME = 'forcefield_audio'

class MobileWarpDisruptor(SpaceObject):

    def Assemble(self):
        godmaStateManager = self.sm.GetService('godma').GetStateManager()
        godmaType = godmaStateManager.GetType(self.typeID)
        self.effectRadius = godmaType.warpScrambleRange
        if self.model is not None:
            anchored = not self.isFree
            if anchored:
                self.ShowForcefield(animated=False)
            else:
                self.SetColor('green')
        self.ScaleAttenuation(self.effectRadius)

    def ShowForcefield(self, animated = True):
        self.SetRadius(self.effectRadius)
        for cs in self.model.curveSets:
            if cs.name == 'Collapse':
                if animated:
                    cs.Play()
                else:
                    cs.PlayFrom(cs.GetMaxCurveDuration())

    def SetColor(self, col):
        if col == 'red':
            self.ShowForcefield()
        elif col == 'green':
            self.SetRadius(0.0)
            self.FadeOutEffectSound()

    def SetRadius(self, r):
        scale = r / 20000.0
        self.model.curveSets[0].bindings[0].scale = scale

    def Explode(self, explosionURL = None, scaling = 1.0, managed = False, delay = 0.0):
        explosionPath, (delay, scaling) = self.GetExplosionInfo()
        if not self.exploded:
            self.sm.ScatterEvent('OnShipExplode', self.GetModel())
        return SpaceObject.Explode(self, explosionURL=explosionPath, managed=True, delay=delay, scaling=scaling)

    def ScaleAttenuation(self, effectRadius):
        emitter = self.GetNamedAudioEmitterFromObservers(SOUND_EFFECT_EMITTER_NAME)
        if emitter is not None:
            emitter.SetAttenuationScalingFactor(effectRadius)

    def FadeOutEffectSound(self):
        emitter = self.GetNamedAudioEmitterFromObservers(SOUND_EFFECT_EMITTER_NAME)
        if emitter is not None:
            emitter.SendEvent('fade_out')
