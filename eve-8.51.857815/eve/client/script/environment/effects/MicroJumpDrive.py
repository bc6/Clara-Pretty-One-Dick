#Embedded file name: eve/client/script/environment/effects\MicroJumpDrive.py
"""
Effect classes for the micro jump drive module
"""
from eve.client.script.environment.effects.GenericEffect import GenericEffect, ShipEffect, STOP_REASON_BALL_REMOVED, STOP_REASON_DEFAULT
import trinity
import blue
import uthread
SECOND = 1000
CAMERA_RESET_TIME = 1500

class MicroJumpDriveEngage(ShipEffect):
    """
    Handles the chargeup and player perspective flash for the micro jump.
    """
    __guid__ = 'effects.MicroJumpDriveEngage'

    def __init__(self, trigger, *args):
        ShipEffect.__init__(self, trigger, *args)
        self.playerEffect = None

    def Prepare(self):
        ShipEffect.Prepare(self, False)
        if session.shipid == self.GetEffectShipID():
            self.playerEffect = trinity.Load('res:/dx9/model/effect/mjd_effect_player.red')
            self.AddSoundToEffect(2)

    def Stop(self, reason = STOP_REASON_DEFAULT):
        """ We do our cleanup in the _DelayedStop method """
        if reason == STOP_REASON_BALL_REMOVED:
            ShipEffect.Stop(self, reason)

    def _DelayedStop(self, delay):
        """
        This is effectively our stop method. It's here to ensure everything has time to finish.
        """
        blue.synchro.SleepSim(delay)
        if self.playerEffect is not None:
            self.RemoveFromScene(self.playerEffect)
            self.playerEffect = None
        if self.gfx is not None:
            ShipEffect.Stop(self)

    def Start(self, duration):
        if self.gfx is None:
            raise RuntimeError('MicroJumpDriveEngage: no effect defined:' + self.__guid__)
        self.curveSets = self.gfx.curveSets
        self.controllerCurve = None
        length = 0
        for each in self.gfx.curveSets:
            length = max(each.GetMaxCurveDuration() * 1000, length)
            each.Play()
            if each.name == 'PLAY_START':
                self.controllerCurve = each.curves[0]

        self.AddToScene(self.gfxModel)
        if self.playerEffect is None:
            self._SetCurveTime(duration * 0.001)
        else:
            self._SetCurveTime(duration * 0.001 - 0.25)
            length = 0
            for each in self.playerEffect.curveSets:
                length = max(each.GetMaxCurveDuration() * 1000, length)
                each.Stop()

            triggerDelayPlayer = duration - length
            uthread.new(self._TriggerPlaybackPlayer, triggerDelayPlayer)
        uthread.new(self._DelayedStop, duration + 2 * SECOND)

    def _SetCurveTime(self, duration):
        """
        Alter the curve keys to match a specific duration.
        Assumes a current setup where the last two keys can safely be moved
        back to match the duration without breaking the effect. That is the
        duration must be long enough for them to fit after any previous keys.
        Curve must have at least one key(not counting the implicit first and last key).
        """
        lastKey = self.controllerCurve.GetKeyCount() - 1
        timeDelta = self.controllerCurve.length - self.controllerCurve.GetKeyTime(lastKey)
        self.controllerCurve.length = duration
        self.controllerCurve.SetKeyTime(lastKey, duration - timeDelta)
        self.controllerCurve.Sort()

    def _TriggerPlaybackPlayer(self, delay):
        """
        Handle playing the player's perspecive effect.
        """
        blue.synchro.SleepSim(delay - CAMERA_RESET_TIME)
        cam = sm.GetService('camera')
        if cam.LookingAt() != session.shipid:
            cam.LookAt(session.shipid)
        blue.synchro.SleepSim(CAMERA_RESET_TIME)
        self.AddToScene(self.playerEffect)
        for each in self.playerEffect.curveSets:
            each.Play()

        sm.GetService('audio').SendUIEvent('microjumpdrive_jump_play')


class MicroJumpDriveJump(GenericEffect):
    """
    Triggered by the actual jump. Plays a flash at the destination of the jump.
    """
    __guid__ = 'effects.MicroJumpDriveJump'

    def __init__(self, trigger, *args):
        GenericEffect.__init__(self, trigger, *args)
        self.position = trigger.graphicInfo
        self.gfxModel = None

    def Prepare(self):
        self.ball = self._SpawnClientBall(self.position)
        gfx = trinity.Load('res:/dx9/model/effect/mjd_effect_jump.red')
        if gfx is None:
            return
        model = getattr(self.GetEffectShipBall(), 'model', None)
        if model is None:
            return
        radius = model.GetBoundingSphereRadius()
        gfx.scaling = (radius, radius, radius)
        self.gfxModel = trinity.EveRootTransform()
        self.gfxModel.children.append(gfx)
        self.gfxModel.boundingSphereRadius = radius
        self.gfxModel.translationCurve = self.ball
        self.sourceObject = self.gfxModel
        self.gfx = gfx
        self.AddSoundToEffect(2)

    def Start(self, duration):
        if self.gfxModel is not None:
            self.AddToScene(self.gfxModel)

    def Stop(self, reason = STOP_REASON_DEFAULT):
        self._DestroyClientBall(self.ball)
        self.ball = None
        self.sourceObject = None
        self.gfx = None
        if self.gfxModel is not None:
            self.RemoveFromScene(self.gfxModel)
            self.gfxModel.translationCurve = None
            self.gfxModel = None
