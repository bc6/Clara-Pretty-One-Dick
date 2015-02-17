#Embedded file name: eve/client/script/ui/inflight/bracketsAndTargets\blinkingSpriteOnSharedCurve.py
import uiprimitives
import uicls
import trinity

class BlinkingSpriteOnSharedCurve(uiprimitives.Sprite):
    """
        This class is a sprite that blinks continuously from fromCurveValue to toCurveValue.
        It's originally made for the targeting/agressing brackets and overview icons,
        and the flag icons, but could be used for any set of sprites that should share
        a curve (cheaper to share a curve than if each has it's own curve).
        The values can only be set once, when the curve is created! If you need other values, you
        are probably trying to share curves on something that shouldn't share curves
    """
    __guid__ = 'uicls.BlinkingSpriteOnSharedCurve'

    def ApplyAttributes(self, attributes):
        uiprimitives.Sprite.ApplyAttributes(self, attributes)
        self.blinkBinding = None
        curveSetName = attributes.curveSetName
        self.curveSetName = curveSetName
        fromCurveValue = attributes.get('fromCurveValue', 0.3)
        toCurveValue = attributes.get('toCurveValue', 0.6)
        duration = attributes.get('duration', 0.5)
        self.SetupSharedBlinkingCurve(curveSetName, fromCurveValue, toCurveValue, duration)

    def SetupSharedBlinkingCurve(self, cuverSetName, fromCurveValue, toCurveValue, duration, *args):
        curveSet = getattr(uicore, cuverSetName, None)
        if curveSet:
            curve = curveSet.curves[0]
        else:
            curveSet = trinity.TriCurveSet()
            setattr(uicore, cuverSetName, curveSet)
            setattr(curveSet, 'name', cuverSetName)
            trinity.device.curveSets.append(curveSet)
            curveSet.Play()
            curve = trinity.Tr2ScalarCurve()
            curve.name = 'blinking_curve'
            curve.length = duration
            curve.startValue = fromCurveValue
            curve.endValue = fromCurveValue
            curve.AddKey(duration / 2.0, toCurveValue)
            curve.cycle = True
            curve.interpolation = trinity.TR2CURVE_LINEAR
            curveSet.curves.append(curve)
        if getattr(self, 'blinkBinding', None) is not None:
            curveSet.bindings.remove(self.blinkBinding)
        self.blinkBinding = trinity.CreatePythonBinding(curveSet, curve, 'currentValue', self, 'opacity')

    def Close(self):
        if getattr(self, 'blinkBinding', None) is not None:
            curveSet = getattr(uicore, self.curveSetName, None)
            if curveSet:
                curveSet.bindings.remove(self.blinkBinding)
            self.blinkBinding = None
        uiprimitives.Sprite.Close(self)
