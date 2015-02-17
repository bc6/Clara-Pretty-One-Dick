#Embedded file name: eve/client/script/environment/effects\JumpPortal.py
from eve.client.script.environment.effects.GenericEffect import ShipEffect

class JumpPortal(ShipEffect):
    __guid__ = 'effects.JumpPortal'

    def Start(self, duration):
        if self.gfx is None:
            raise RuntimeError('JumpPortal: no effect defined')
        self.PlayOldAnimations(self.gfx)

    def Repeat(self, duration):
        if self.gfx is None:
            raise RuntimeError('JumpPortal: no effect defined')
        self.PlayOldAnimations(self.gfx)


class JumpPortalBO(JumpPortal):
    __guid__ = 'effects.JumpPortalBO'
