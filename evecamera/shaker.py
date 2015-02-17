#Embedded file name: evecamera\shaker.py
import blue
import geo2
import trinity
DEFAULT_NOISE_SCALE = 0
DEFAULT_NOISE_DAMP = 1.1

class ShakeBehavior(object):

    def __init__(self, key = None):
        self.key = key
        self.noiseCurve = None
        self.scaleCurve = None
        self.dampCurve = None
        self.noiseScale = DEFAULT_NOISE_SCALE
        self.noiseDamp = DEFAULT_NOISE_DAMP


class ShakeController(object):

    def __init__(self, cameraSvc):
        self._currentBehavior = ShakeBehavior()
        self._cameraSvc = cameraSvc
        self._isEnabled = True

    def _ApplyCurveStartTime(self, behavior, now):
        if hasattr(behavior.noiseCurve, 'start'):
            behavior.noiseCurve.start = now
        if hasattr(behavior.scaleCurve, 'start'):
            behavior.scaleCurve.start = now
        if hasattr(behavior.dampCurve, 'start'):
            behavior.dampCurve.start = now

    def _Apply(self, behavior, camera):
        now = blue.os.GetSimTime()
        self._ApplyCurveStartTime(behavior, now)
        camera.noiseCurve = behavior.noiseCurve
        camera.noiseScaleCurve = behavior.scaleCurve
        camera.noiseScale = behavior.noiseScale
        camera.noiseDampCurve = behavior.dampCurve
        camera.noiseDamp = behavior.noiseDamp

    def Enable(self, enabled):
        self._isEnabled = enabled
        if self._isEnabled:
            camera = self._cameraSvc.GetSpaceCamera()
            if camera is not None:
                camera.noise = True
        else:
            self.ClearCurrentShake()
            camera = self._cameraSvc.GetSpaceCamera()
            if camera is not None:
                camera.noise = False

    def DoCameraShake(self, shakeObj):
        if not self._isEnabled:
            return
        camera = self._cameraSvc.GetSpaceCamera()
        if camera is None:
            return
        self._Apply(shakeObj, camera)
        self._currentBehavior = shakeObj

    def EndCameraShake(self, key = None):
        if not self._isEnabled:
            return
        if self._currentBehavior.key == key:
            self.ClearCurrentShake()

    def ClearCurrentShake(self):
        if not self._isEnabled:
            return
        self._currentBehavior = ShakeBehavior()
        self._Apply(self._currentBehavior, self._cameraSvc.GetSpaceCamera())
