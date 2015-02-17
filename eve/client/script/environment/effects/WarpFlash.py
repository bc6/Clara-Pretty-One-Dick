#Embedded file name: eve/client/script/environment/effects\WarpFlash.py
from eve.client.script.environment.effects.GenericEffect import GenericEffect, STOP_REASON_DEFAULT, STOP_REASON_BALL_REMOVED
import destiny
import geo2
import trinity
import blue
import uthread
import random

class WarpFlashIn(GenericEffect):
    _bigGlows = 0

    def __init__(self, trigger, *args):
        GenericEffect.__init__(self, trigger, *args)
        self.gfxBall = None
        self.gfxModel = None
        self.gfxModel_ship = None
        self.observer = None

    def Prepare(self, addToScene = True):
        shipBall = self.GetEffectShipBall()
        self.position = shipBall.GetVectorAt(blue.os.GetSimTime())
        self.position = (self.position.x, self.position.y, self.position.z)
        if WarpFlashIn._bigGlows < 5:
            gfx = trinity.Load('res:/fisfx/jump/warp/warp_in_glow.red')
            WarpFlashIn._bigGlows += 1
            self.useBigGlow = True
        else:
            gfx = trinity.Load('res:/fisfx/jump/warp/warp_in_noglow.red')
            self.useBigGlow = False
        if gfx is None:
            return
        self.gfx = gfx
        model = getattr(shipBall, 'model', None)
        if model is None:
            return
        s = 0.7778 * model.GetBoundingSphereRadius() ** 0.3534
        gfx.scaling = (s, s, s)
        self.gfx_ship = trinity.Load('res:/fisfx/jump/warp/warp_glow.red')

        def _glowScale(x):
            return 9e-08 * x * x + 0.005 * x + 0.6898

        self.gfxModel_ship = trinity.EveRootTransform()
        self.gfxModel_ship.children.append(self.gfx_ship)
        r = 0.125 * _glowScale(model.boundingSphereRadius)
        self.gfxModel_ship.scaling = (r, r, r * 3)
        self.gfxBall = self._SpawnClientBall(self.position)
        for each in gfx.Find('trinity.EveTransform'):
            each.useLodLevel = False

        gfxModel = trinity.EveRootTransform()
        gfxModel.children.append(gfx)
        gfxModel.translationCurve = self.gfxBall
        self.gfxModel = gfxModel
        self.soundEvent = 'warp_in_frig_play'
        if model.GetBoundingSphereRadius() > 350:
            self.soundEvent = 'warp_in_battle_play'
        self.AddSoundToEffect(0.001)

    def Start(self, duration):
        shipBall = self.GetEffectShipBall()
        if shipBall is None or not self._IsAtWarpInAcceleration(shipBall):
            if self.useBigGlow:
                WarpFlashIn._bigGlows -= 1
            self._Cleanup()
            return
        uthread.new(self._RunEffect)

    def _IsAtWarpInAcceleration(self, ball):
        a = ball.GetVectorDoubleDotAt(blue.os.GetSimTime())
        a = (a.x, a.y, a.z)
        return geo2.Vec3Length(a) > 5000.0

    def _RunEffect(self):
        if self.gfxModel is not None:
            if self.graphicInfo != 'npc':
                blue.synchro.SleepSim(random.random() * 200.0)
            self.AddToScene(self.gfxModel)
            self.gfx.curveSets[0].Play()
            self.observer.observer.SendEvent(self.soundEvent)
            self.gfxModel_ship.translationCurve = self.GetEffectShipBall()
            self.gfxModel_ship.rotationCurve = self.GetEffectShipBall()
            self.AddToScene(self.gfxModel_ship)
            self.gfx_ship.curveSets[0].Play()
            if self.useBigGlow:
                blue.synchro.SleepSim(300.0)
                WarpFlashIn._bigGlows -= 1
                blue.synchro.SleepSim(2700.0)
            else:
                blue.synchro.SleepSim(3000.0)
        self._Cleanup()

    def _Cleanup(self):
        if self.gfxBall is not None:
            self._DestroyClientBall(self.gfxBall)
            self.gfxBall = None
        if self.gfxModel is not None:
            self.RemoveFromScene(self.gfxModel)
            self.gfxModel = None
        if self.gfxModel_ship is not None:
            self.RemoveFromScene(self.gfxModel_ship)
            self.gfxModel_ship = None
        if self.observer is not None:
            self.observer.observer = None
            self.observer = None
        self.gfx_ship = None
        self.gfx = None


class WarpFlashOut(GenericEffect):
    """
    Triggered by the actual jump. Plays a flash at the destination of the jump.
    """
    __guid__ = 'effects.WarpFlashOut'

    def __init__(self, trigger, *args):
        GenericEffect.__init__(self, trigger, *args)
        self.gfxModel_ship = None
        self.gfxModel_trace = None
        self.startPos = (0, 0, 0)
        self.lastPos = (0, 0, 0)
        self.gotStopCommand = False
        self.abort = False
        self.direction = (0, 0, 1)
        self.gfxBall = None
        self.observer = None
        self.isShortWarp = False

    def Prepare(self, addToScene = True):
        shipBall = self.GetEffectShipBall()
        self.isShortWarp = self._IsShortWarp(shipBall)
        if self.isShortWarp:
            return
        model = getattr(shipBall, 'model', None)
        if model is None:
            return
        self.startPos = shipBall.GetVectorAt(blue.os.GetSimTime())
        self.startPos = (self.startPos.x, self.startPos.y, self.startPos.z)
        self.lastPos = self.startPos

        def _sizeFunction(x):
            return 0.0039 * x + 2.5

        r = _sizeFunction(model.boundingSphereRadius)
        self.gfx_trace = trinity.Load('res:/fisfx/jump/warp/warp_out.red')
        self.gfxModel_trace = trinity.EveRootTransform()
        self.gfxModel_trace.children.append(self.gfx_trace)
        self.gfxModel_trace.scaling = (r, r, 8)
        self.gfx_ship = trinity.Load('res:/fisfx/jump/warp/warp_glow.red')
        self.gfxModel_ship = trinity.EveRootTransform()
        self.gfxModel_ship.children.append(self.gfx_ship)
        r *= 0.5
        self.gfxModel_ship.scaling = (r, r, 6)
        self.soundInsert = 'frig'
        if model.boundingSphereRadius > 350:
            self.soundInsert = 'battle'
        self.gfx = self.gfx_trace
        self.AddSoundToEffect(0.0007)

    def _IsShortWarp(self, ball):
        pos0 = (ball.x, ball.y, ball.z)
        pos1 = (ball.gotoX, ball.gotoY, ball.gotoZ)
        d = geo2.Vec3DistanceSq(pos0, pos1)
        return d < 4000000000000.0

    def _WaitForAcceleration(self, accT = 215000.0):
        shipBall = self.GetEffectShipBall()
        shipPosL = shipBall.GetVectorAt(blue.os.GetSimTime())
        shipPosL = (shipPosL.x, shipPosL.y, shipPosL.z)
        speedL = 0
        timeL = blue.os.GetSimTime()
        acc = 0
        while not self.abort:
            timeN = blue.os.GetSimTime()
            v = shipBall.GetVectorDotAt(timeN)
            speed = geo2.Vec3Length((v.x, v.y, v.z))
            shipPos = shipBall.GetVectorAt(blue.os.GetSimTime())
            shipPos = (shipPos.x, shipPos.y, shipPos.z)
            self.direction = geo2.Vec3Subtract(shipPos, shipPosL)
            shipPosL = shipPos
            timeDiffSec = blue.os.TimeDiffInMs(timeL, timeN) / 1000.0
            if timeDiffSec != 0.0:
                acc = (speed - speedL) / timeDiffSec
            speedL = speed
            timeL = timeN
            if acc > accT:
                break
            blue.synchro.Yield()

        return speedL

    def _IsWarpingWithClient(self, speed):
        playerBall = self.fxSequencer.GetBall(session.shipid)
        if playerBall is None or playerBall.mode != destiny.DSTBALL_WARP:
            return False
        velo = playerBall.GetVectorDotAt(blue.os.GetSimTime())
        velo = (velo.x, velo.y, velo.z)
        playerSpeed = geo2.Vec3Length(velo)
        if playerSpeed == 0.0:
            return False
        return abs((playerSpeed - speed) / playerSpeed) < 0.1

    def _RunEffect(self):
        shipBall = self.GetEffectShipBall()
        if self.abort or shipBall is None:
            self._Cleanup()
            return
        speed = self._WaitForAcceleration(310000.0)
        if self.abort or self._IsWarpingWithClient(speed):
            self._Cleanup()
            return
        blue.synchro.SleepSim(random.random() * 250.0)
        direction = geo2.Vec3Normalize(self.direction)
        rotation = geo2.QuaternionRotationArc((0, 0, 1), direction)
        if self.abort:
            return
        posNow = shipBall.GetVectorAt(blue.os.GetSimTime())
        posNow = (posNow.x, posNow.y, posNow.z)
        self.gfxBall = self._SpawnClientBall(posNow)
        if self.gfxModel_trace is not None:
            soundEvent = 'warp_out_%s1_play' % (self.soundInsert,)
            self.observer.observer.SendEvent(soundEvent)
            self.gfxModel_trace.translationCurve = self.gfxBall
            self.gfxModel_trace.rotation = rotation
            self.AddToScene(self.gfxModel_trace)
            for each in self.gfx_trace.curveSets:
                each.Play()

            self.gfxModel_ship.translationCurve = shipBall
            self.gfxModel_ship.rotation = rotation
            self.AddToScene(self.gfxModel_ship)
            for each in self.gfx_ship.curveSets:
                each.Play()

        if shipBall.model is not None:
            shipBall.model.display = False
        blue.synchro.SleepSim(1500.0)
        self._Cleanup()

    def _Cleanup(self):
        if self.gfxBall is not None:
            self._DestroyClientBall(self.gfxBall)
            self.gfxBall = None
        self.gfxModel_start = None
        if self.gfxModel_trace is not None:
            self.RemoveFromScene(self.gfxModel_trace)
            self.gfxModel_trace = None
        self.gfx_trace = None
        if self.gfxModel_ship is not None:
            self.RemoveFromScene(self.gfxModel_ship)
            self.gfxModel_ship = None
        self.gfx_ship = None
        self.gfx = None
        if self.observer is not None:
            self.observer.observer = None
            self.observer = None

    def Start(self, duration):
        if self.isShortWarp:
            return
        uthread.new(self._RunEffect)

    def Stop(self, reason = STOP_REASON_DEFAULT):
        if reason == STOP_REASON_BALL_REMOVED:
            self.abort = True
            self._Cleanup()
