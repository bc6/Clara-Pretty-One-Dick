#Embedded file name: evecamera\utils.py
"""
Helper functions and client implementations
"""
import blue
import evecamera
import evecamera.animation as camanim
import evecamera.shaker as camshake
import geo2
import carbon.common.script.util.mathUtil as mathUtil
from math import isnan
import trinity

def GetARZoomMultiplier(aspectRatio):
    return max(1, aspectRatio / 1.6)


class LookAt_Pan(camanim.BaseCameraAnimation):

    def __init__(self, setZ, duration = 0.5, cache = False):
        camanim.BaseCameraAnimation.__init__(self, camanim.PAN_ANIMATION, duration)
        self.isDone = True
        self.setZ = setZ
        self.cache = cache

    def Start(self, cameraContext, simTime, clockTime):
        camanim.BaseCameraAnimation.Start(self, cameraContext, simTime, clockTime)
        if self.setZ is None:
            self.startTrZ = cameraContext.GetSpaceCamera().translationFromParent
            self.endTrZ = cameraContext.CheckTranslationFromParent(2.0, distanceIsScale=True)
            self.isDone = False
        else:
            self.endTrZ = self.setZ

    def End(self, cameraContext):
        camera = cameraContext.GetSpaceCamera()
        camera.translationFromParent = cameraContext.CheckTranslationFromParent(self.endTrZ)
        if self.cache:
            cameraContext.CacheCameraTranslation()

    def _Tick(self, progress, cameraContext):
        cameraContext.GetSpaceCamera().translationFromParent = mathUtil.Lerp(self.startTrZ, self.endTrZ, progress)


class LookAt_FOV(camanim.BaseCameraAnimation):

    def __init__(self, reset):
        camanim.BaseCameraAnimation.__init__(self, camanim.FOV_ANIMATION, 0.5)
        self.reset = reset

    def Start(self, cameraContext, simTime, clockTime):
        camanim.BaseCameraAnimation.Start(self, cameraContext, simTime, clockTime)
        camera = cameraContext.GetSpaceCamera()
        self.startFov = camera.fieldOfView
        if self.reset:
            self.endFov = evecamera.FOV_MAX
        else:
            self.endFov = max(evecamera.FOV_MIN, min(camera.fieldOfView, evecamera.FOV_MAX))
        if self.startFov == self.endFov:
            self.isDone = True

    def _Tick(self, progress, cameraContext):
        cameraContext.GetSpaceCamera().fieldOfView = mathUtil.Lerp(self.startFov, self.endFov, progress)

    def End(self, cameraContext):
        cameraContext.GetSpaceCamera().fieldOfView = self.endFov


class LookAt_Translation(camanim.BaseCameraAnimation):

    def __init__(self, tracker):
        camanim.BaseCameraAnimation.__init__(self, camanim.TRANSLATION_ANIMATION, 0.5)
        self.startPos = (0, 0, 0)
        self.starting = True
        self.tracker = tracker

    def Start(self, cameraContext, simTime, clockTime):
        camanim.BaseCameraAnimation.Start(self, cameraContext, simTime, clockTime)
        cameraParent = cameraContext.GetCameraParent()
        if cameraParent.translationCurve is not None:
            startPos = cameraParent.translationCurve.GetVectorAt(blue.os.GetSimTime())
            self.startPos = (startPos.x, startPos.y, startPos.z)
        else:
            self.startPos = cameraParent.translation

    def _getEndPos(self):
        if hasattr(self.tracker.parent, 'modelWorldPosition'):
            return self.tracker.parent.modelWorldPosition
        if getattr(self.tracker.parent, 'translationCurve', None) is not None:
            endPos = self.tracker.parent.translationCurve.GetVectorAt(blue.os.GetSimTime())
            return (endPos.x, endPos.y, endPos.z)
        return self.tracker.parent.translation

    def _Tick(self, progress, cameraContext):
        cameraParent = cameraContext.GetCameraParent()
        if self.starting:
            cameraParent.translationCurve = None
            self.starting = False
        endPos = self._getEndPos()
        cameraParent.translation = geo2.Vec3Lerp(self.startPos, endPos, progress)

    def End(self, cameraContext):
        cameraContext.GetCameraParent().translationCurve = self.tracker


class SetTranslationCurve(camanim.BaseCameraAnimation):

    def __init__(self, translationCurve):
        camanim.BaseCameraAnimation.__init__(self, camanim.TRANSLATION_ANIMATION, 0.0)
        self.translationCurve = translationCurve
        self.isDone = True

    def End(self, cameraContext):
        cameraContext.GetCameraParent().translationCurve = self.translationCurve


class PanCamera(camanim.BaseCameraAnimation):

    def __init__(self, cambeg = None, camend = None, duration = 0.5, source = 'default', cache = False):
        camanim.BaseCameraAnimation.__init__(self, camanim.PAN_ANIMATION, duration)
        self.cambeg = cambeg
        self.camend = camend
        self.isDone = cambeg is None or camend is None
        self.source = source
        self.cache = cache

    def _Tick(self, progress, cameraContext):
        transl = mathUtil.Lerp(self.cambeg, self.camend, progress)
        checkedTranslation = cameraContext.CheckTranslationFromParent(transl, source=self.source)
        cameraContext.GetCameraByName(self.source).translationFromParent = checkedTranslation

    def End(self, cameraContext):
        if self.camend is not None:
            cam = cameraContext.GetCameraByName(self.source)
            cam.translationFromParent = cameraContext.CheckTranslationFromParent(self.camend, source=self.source)
        if self.cache:
            cameraContext.CacheCameraTranslation()


class PanCameraAccelerated(camanim.BaseCameraAnimation):

    def __init__(self, start, end, duration = 0.5, accelerationPower = 2.0):
        camanim.BaseCameraAnimation.__init__(self, camanim.PAN_ANIMATION, duration)
        self.start = start
        self.end = end
        self.accelerationPower = accelerationPower

    def _Tick(self, progress, cameraContext):
        progress = pow(progress, self.accelerationPower)
        translation = mathUtil.Lerp(self.start, self.end, progress)
        cam = cameraContext.GetSpaceCamera()
        cam.translationFromParent = cameraContext.CheckTranslationFromParent(translation)


def CreateBehaviorFromMagnitudeAndPosition(magnitude, shakeOrigin, camera):
    timeFactor = pow(magnitude / 400.0, 0.7)
    noiseScaleCurve = trinity.TriScalarCurve()
    noiseScaleCurve.AddKey(0.0, 1.2, 0.0, 0.0, 3)
    noiseScaleCurve.AddKey(0.1, 0.1, 0.0, 0.0, 3)
    noiseScaleCurve.AddKey(1.5 * timeFactor, 0.13, 0.0, 0.0, 3)
    noiseScaleCurve.AddKey(2.0 * timeFactor, 0.0, 0.0, 0.0, 3)
    noiseScaleCurve.extrapolation = 1
    noiseDampCurve = trinity.TriScalarCurve()
    noiseDampCurve.AddKey(0.0, 80.0, 0.0, 0.0, 3)
    noiseDampCurve.AddKey(0.1, 20.0, 0.0, 0.0, 3)
    noiseDampCurve.AddKey(1.5 * timeFactor, 0.0, 0.0, 0.0, 3)
    noiseDampCurve.AddKey(2.0 * timeFactor, 0.0, 0.0, 0.0, 3)
    noiseDampCurve.extrapolation = 1
    distance = geo2.Vec3Length(geo2.Vec3Subtract(shakeOrigin, camera.pos))
    if isnan(distance):
        return
    if distance < 700.0:
        distance = 700.0
    elif distance > 2000000000:
        distance = 2000000000
    actualMagnitude = 0.7 * magnitude / pow(distance, 0.7)
    noiseScaleCurve.ScaleValue(actualMagnitude)
    noiseDampCurve.ScaleValue(actualMagnitude)
    if camera.noiseScaleCurve is not None and camera.noiseScaleCurve.value > noiseScaleCurve.keys[1].value:
        return
    behavior = camshake.ShakeBehavior()
    behavior.scaleCurve = noiseScaleCurve
    behavior.dampCurve = noiseDampCurve
    return behavior
