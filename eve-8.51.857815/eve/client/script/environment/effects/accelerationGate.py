#Embedded file name: eve/client/script/environment/effects\accelerationGate.py
from eve.client.script.environment.effects.GenericEffect import GenericEffect

class AccelerationGate(GenericEffect):
    __guid__ = 'effects.WarpGateEffect'

    def Start(self, duration):
        """ get the gate and start the 'activation' curve on the model, also start the dungeon music for the dungeon"""
        gateID = self.GetEffectShipID()
        targetID = self.GetEffectTargetID()
        gateBall = self.GetEffectShipBall()
        slimItem = self.fxSequencer.GetItem(gateID)
        sm.GetService('dungeonChecker').enteringDungeon = True
        if slimItem.dunMusicUrl is not None and targetID == eve.session.shipid:
            sm.GetService('audio').SendUIEvent(slimItem.dunMusicUrl.lower())
        self.PlayNamedAnimations(gateBall.model, 'Activation')
