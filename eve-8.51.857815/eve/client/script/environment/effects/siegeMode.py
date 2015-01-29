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
        self.SendEventFirstEmitter(shipBall, self.audioEnd)

    def Prepare(self):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        graphicsID = shipBall.typeData['graphicID']
        self.audioStart = gfxutils.BuildShipEffectSoundNameFromGraphicID(graphicsID, 'siege', True)
        self.audioEnd = gfxutils.BuildShipEffectSoundNameFromGraphicID(graphicsID, 'siege', False)

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        shipBall.TriggerAnimation('siege')
        self.SendEventFirstEmitter(shipBall, self.audioStart)

    def Repeat(self, duration):
        pass

    def SendEventFirstEmitter(self, shipBall, eventName):
        if shipBall is None or eventName is None or not hasattr(shipBall, 'observers'):
            return
        for observer in shipBall.model.observers:
            observer.observer.SendEvent(eventName)
            break
