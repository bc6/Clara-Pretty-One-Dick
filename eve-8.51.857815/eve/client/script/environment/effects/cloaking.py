#Embedded file name: eve/client/script/environment/effects\cloaking.py
import random
from eve.client.script.environment.effects.GenericEffect import GenericEffect, ShipRenderEffect, STOP_REASON_DEFAULT, STOP_REASON_BALL_REMOVED

class Cloaking(GenericEffect):
    __guid__ = 'effects.Cloaking'


class Cloak(ShipRenderEffect):
    __guid__ = 'effects.Cloak'
    __gfxName__ = 'Cloak'

    def Prepare(self):
        sourceObject = self.GetEffectShipBall().model
        for effect in sourceObject.overlayEffects:
            if effect.name == self.__gfxName__:
                sourceObject.overlayEffects.remove(effect)

        ShipRenderEffect.Prepare(self)
        self.gfx.name = self.__gfxName__
        for binding in self.gfx.curveSet.bindings:
            if binding.name.startswith('self'):
                binding.destinationObject = self.sourceObject

        shipBall = self.GetEffectShipBall()
        if shipBall is not None:
            if shipBall.id != session.shipid:
                del self.gfx.additiveEffects[:]
                del self.gfx.distortionEffects[:]
        self.sourceObject.clipSphereCenter = random.choice(self.sourceObject.damageLocators)[0]
        self.SetupEffectEmitter()

    def Start(self, duration):
        ShipRenderEffect.Start(self, duration)
        self.SendAudioEvent(eventName='ship_cloak_play')

    def Stop(self, reason = STOP_REASON_DEFAULT):
        if reason == STOP_REASON_BALL_REMOVED:
            ShipRenderEffect.Stop(self, reason)


class CloakNoAnim(Cloak):
    __guid__ = 'effects.CloakNoAmim'

    def Start(self, duration):
        Cloak.Start(self, 6000)
        length = self.gfx.curveSet.GetMaxCurveDuration()
        self.gfx.curveSet.PlayFrom(length)


class CloakRegardless(Cloak):
    __guid__ = 'effects.CloakRegardless'


class Uncloak(Cloak):
    __guid__ = 'effects.Uncloak'

    def __init__(self, *args, **kwargs):
        Cloak.__init__(self, *args, **kwargs)
        self.fromTime = None

    def Prepare(self):
        ball = self.GetEffectShipBall()
        self.sourceObject = ball.model
        for effect in self.sourceObject.overlayEffects:
            if effect.name == self.__gfxName__:
                self.gfx = effect
                self.fromTime = self.gfx.curveSet.scaledTime
                self.SetupEffectEmitter()
                break

        if not self.gfx:
            Cloak.Prepare(self)

    def Start(self, duration):
        if self.gfx is None:
            return
        playFrom = duration / 1000.0
        if self.fromTime:
            playFrom = min(self.fromTime, playFrom)
        self.gfx.curveSet.scale = -1.0
        self.gfx.curveSet.PlayFrom(playFrom)
        self.SendAudioEvent(eventName='ship_uncloak_play')

    def Stop(self, reason = STOP_REASON_DEFAULT):
        self.sourceObject.clipSphereFactor = 0.0
        self.sourceObject.activationStrength = 1.0
        ShipRenderEffect.Stop(self, reason)
