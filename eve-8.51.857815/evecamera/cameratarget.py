#Embedded file name: evecamera\cameratarget.py
import trinity

class CameraTarget(object):
    """
    Represents something the camera looks at, i.e. the 'parent' or other 'interest'
    """

    def __init__(self, camera, target = 'parent'):
        self._translationCurve = None
        self._camera = camera
        self._translAttrib = target
        self.SetTranslationCurve(camera.parent)

    def SetTranslationCurve(self, curve):
        self._translationCurve = curve
        if self._camera is not None:
            setattr(self._camera, self._translAttrib, curve)

    def GetTranslationCurve(self):
        return self._translationCurve

    def SetTranslation(self, value):
        if self._translationCurve is None:
            self.SetTranslationCurve(trinity.EveSO2ModelCenterPos())
        self._translationCurve.value = value

    def GetTranslation(self):
        curve = self.GetTranslationCurve()
        if curve is None:
            return (0, 0, 0)
        if hasattr(curve, 'value'):
            if hasattr(curve.value, 'x'):
                return (curve.value.x, curve.value.y, curve.value.z)
            return curve.value
        return (curve.x, curve.y, curve.z)

    def SetParent(self, parent):
        if hasattr(self._translationCurve, 'parent'):
            self._translationCurve.parent = parent

    def GetParent(self):
        return getattr(self._translationCurve, 'parent', None)

    def SetCamera(self, camera):
        self._camera = camera
        self.SetTranslationCurve(self._translationCurve)

    def GetCamera(self):
        return self._camera

    translation = property(GetTranslation, SetTranslation)
    translationCurve = property(GetTranslationCurve, SetTranslationCurve)
    parent = property(GetParent, SetParent)
