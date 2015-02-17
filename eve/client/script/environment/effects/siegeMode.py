#Embedded file name: eve/client/script/environment/effects\siegeMode.py
from eve.client.script.environment.effects.GenericEffect import GenericEffect, STOP_REASON_DEFAULT
import evegraphics.utils as gfxutils

class SiegeMode(GenericEffect):
    __guid__ = 'effects.SiegeMode'

    def __init__(self, trigger, transformFlags = 0, mergeFlags = 0, graphicFile = None, scaleTime = True, duration = 10000):
        GenericEffect.__init__(self, trigger, transformFlags, mergeFlags, graphicFile, scaleTime, duration)

    def Stop(self, reason = STOP_REASON_DEFAULT):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        shipBall.TriggerAnimation('normal')

    def Prepare(self):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        graphicsID = shipBall.typeData['graphicID']

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        shipBall.TriggerAnimation('siege')

    def Repeat(self, duration):
        pass
