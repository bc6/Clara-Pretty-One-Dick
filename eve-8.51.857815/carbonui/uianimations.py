#Embedded file name: carbonui\uianimations.py
from carbonui.util.color import Color
import trinity
import math
import carbonui.const as uiconst
import blue
import telemetry
OVERSHOT_TIME = 0.4

class UIAnimations(object):
    __guid__ = 'uicls.UIAnimations'
    RELATED_ATTRIBUTES = {'opacity': 'color',
     'color': 'opacity'}

    def __init__(self):
        self.curvesByObjectIDAttrName = {}

    def _CreateCurveSet(self):
        curveSet = trinity.TriCurveSet()
        curveSet.useRealTime = True
        trinity.device.curveSets.append(curveSet)
        return curveSet

    def Play(self, curve, obj, attrName, loops = 1, callback = None, sleep = False, curveSet = None):
        curve.cycle = loops is uiconst.ANIM_REPEAT or loops > 1
        if not curveSet:
            curveSet = self._CreateCurveSet()
            curveSet.name = getattr(obj, 'name', str(id(obj)))
        curveSet.curves.append(curve)
        self.RegisterCurvesetForObject(obj, curveSet, attrName)
        if hasattr(obj, '__iroot__'):
            binding = trinity.CreateBinding(curveSet, curve, 'currentValue', obj, attrName)
        else:
            obj.isAnimated = True
            binding = trinity.CreatePythonBinding(curveSet, curve, 'currentValue', obj, attrName)
        binding.name = getattr(obj, 'name', str(id(obj))) + '_' + attrName
        curveSet.Play()
        if loops == uiconst.ANIM_REPEAT:
            return curveSet
        duration = loops * curveSet.GetMaxCurveDuration()
        duration += self.GetMaxTimeOffset(curveSet)
        if callback:
            curveSet.StopAfterWithCallback(duration, callback)
        else:
            curveSet.StopAfter(duration)
        if sleep:
            blue.pyos.synchro.SleepSim(duration * 1000)
        return curveSet

    def RegisterCurvesetForObject(self, obj, curveSet, attrName):
        self.StopAnimation(obj, attrName)
        key = (id(obj), attrName)
        self.curvesByObjectIDAttrName[key] = blue.BluePythonWeakRef(curveSet)
        self.curvesByObjectIDAttrName[key].callback = lambda : self.OnWeakRefLost(key)

    def StopAnimation(self, obj, attrName):
        key = (id(obj), attrName)
        self._StopAndRemoveCurveSet(key)
        if attrName in self.RELATED_ATTRIBUTES:
            key = (id(obj), self.RELATED_ATTRIBUTES[attrName])
            self._StopAndRemoveCurveSet(key)

    def _StopAndRemoveCurveSet(self, key):
        curveSet = self.curvesByObjectIDAttrName.pop(key, None)
        if curveSet and curveSet.object:
            curveSet.callback = None
            curveSet.object.Stop()

    @telemetry.ZONE_METHOD
    def StopAllAnimations(self, obj):
        objID = id(obj)
        toRemove = set()
        for key, curveSet in self.curvesByObjectIDAttrName.iteritems():
            _objID, attrName = key
            if _objID == objID:
                toRemove.add(key)

        for key in toRemove:
            self._StopAndRemoveCurveSet(key)

    def GetAnimationCurveSet(self, obj, attrName):
        key = (id(obj), attrName)
        wr = self.curvesByObjectIDAttrName.get(key, None)
        if wr:
            return wr.object

    def OnWeakRefLost(self, key):
        """ Throw curve entry once it's stopped, if it's still present """
        self.curvesByObjectIDAttrName.pop(key, None)

    def GetMaxTimeOffset(self, curveSet):
        return max([ getattr(curve, 'timeOffset', 0.0) for curve in curveSet.curves ])

    def MorphScalar(self, obj, attrName, startVal = 0.0, endVal = 1.0, duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        curve = self.GetScalar(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, attrName, loops, callback, sleep, curveSet)

    def MorphVector2(self, obj, attrName, startVal = (0.0, 0.0), endVal = (1.0, 1.0), duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetVector2(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, attrName, loops, callback, sleep)

    def MorphVector3(self, obj, attrName, startVal = (0.0, 0.0), endVal = (1.0, 1.0), duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetVector3(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, attrName, loops, callback, sleep)

    def MorphQuaternion(self, obj, attrName, startVal = (0.0, 0.0), endVal = (1.0, 1.0), duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetQuaternion(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, attrName, loops, callback, sleep)

    def FadeTo(self, obj, startVal = 0.0, endVal = 1.0, duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        if hasattr(obj, 'opacity'):
            curve = self.GetScalar(startVal, endVal, duration, curveType, timeOffset=timeOffset)
            attrName = 'opacity'
        else:
            c = obj.color
            curve = self.GetColor((c.r,
             c.g,
             c.b,
             startVal), (c.r,
             c.g,
             c.b,
             endVal), duration, curveType, timeOffset=timeOffset)
            attrName = 'color'
        return self.Play(curve, obj, attrName, loops, callback, sleep, curveSet=curveSet)

    def FadeIn(self, obj, endVal = 1.0, duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        startVal = getattr(obj, 'opacity', 0.0)
        return self.FadeTo(obj, startVal, endVal, duration, loops, curveType, callback, sleep, curveSet=curveSet, timeOffset=timeOffset)

    def FadeOut(self, obj, duration = 0.75, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        startVal = getattr(obj, 'opacity', 0.0)
        return self.FadeTo(obj, startVal, 0.0, duration, loops, curveType, callback, sleep, curveSet=curveSet, timeOffset=timeOffset)

    def BlinkIn(self, obj, startVal = 0.0, endVal = 1.0, duration = 0.1, loops = 3, curveType = uiconst.ANIM_LINEAR, callback = None, sleep = False, timeOffset = 0.0):
        return self.FadeTo(obj, startVal, endVal, duration, loops, curveType, callback, sleep, timeOffset=timeOffset)

    def BlinkOut(self, obj, startVal = 1.0, endVal = 0.0, duration = 0.1, loops = 3, curveType = uiconst.ANIM_LINEAR, callback = None, sleep = False, timeOffset = 0.0):
        return self.FadeTo(obj, startVal, endVal, duration, loops, curveType, callback, sleep, timeOffset=timeOffset)

    def MoveTo(self, obj, startPos = None, endPos = None, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0, curveSet = None):
        if not startPos:
            startPos = (obj.displayX, obj.displayY)
        if not endPos:
            endPos = (obj.displayX, obj.displayY)
        curve = self.GetScalar(startPos[0], endPos[0], duration, curveType, timeOffset=timeOffset)
        curveSet = self.Play(curve, obj, 'left', loops, callback, curveSet=curveSet)
        curve = self.GetScalar(startPos[1], endPos[1], duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'top', loops, callback, sleep, curveSet=curveSet)

    def MoveInFromLeft(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        curve = self.GetScalar(obj.left - amount, obj.left, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'left', loops, callback, sleep, curveSet=curveSet)

    def MoveInFromRight(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        curve = self.GetScalar(obj.left + amount, obj.left, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'left', loops, callback, sleep, curveSet=curveSet)

    def MoveInFromTop(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(obj.top - amount, obj.top, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'top', loops, callback, sleep)

    def MoveInFromBottom(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(obj.top + amount, obj.top, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'top', loops, callback, sleep)

    def MoveOutLeft(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(obj.left, obj.left - amount, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'left', loops, callback, sleep)

    def MoveOutRight(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(obj.left, obj.left + amount, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'left', loops, callback, sleep)

    def MoveOutTop(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(obj.top, obj.top - amount, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'top', loops, callback, sleep)

    def MoveOutBottom(self, obj, amount = 30, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(obj.top, obj.top + amount, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'top', loops, callback, sleep)

    def Tr2DScaleTo(self, obj, startScale = (0.0, 0.0), endScale = (1.0, 1.0), duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0, curveSet = None):
        curve = self.GetVector2(startScale, endScale, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'scale', loops, callback, sleep, curveSet=curveSet)

    def Tr2DScaleIn(self, obj, scaleCenter = (0.0, 0.0), duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0, curveSet = None):
        obj.scaleCenter = scaleCenter
        return self.Tr2DScaleTo(obj, (0.0, 0.0), (1.0, 1.0), duration, loops, curveType, callback, sleep, timeOffset, curveSet=curveSet)

    def Tr2DScaleOut(self, obj, startScale = (0.0, 0.0), endScale = (1.0, 1.0), duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0, curveSet = None):
        return self.Tr2DScaleTo(obj, obj.scale, (0.0, 0.0), duration, loops, curveType, callback, sleep, timeOffset, curveSet=curveSet)

    def Tr2DFlipIn(self, obj, startScale = (0.0, 0.0), endScale = (1.0, 1.0), duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        self.Tr2DScaleTo(obj, (1.0, 0.0), (1.0, 1.0), duration, loops, curveType, callback, timeOffset)
        curve = self.GetScalar(0.0, 1.0, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'scalingRotation', loops, callback, sleep)

    def Tr2DFlipOut(self, obj, startScale = (1.0, 1.0), endScale = (0.0, 0.0), duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        self.Tr2DScaleTo(obj, startScale, endScale, duration, loops, curveType, callback, timeOffset)
        curve = self.GetScalar(1.0, 0.0, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'scalingRotation', loops, callback, sleep)

    def Tr2DSquashOut(self, obj, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        obj.scalingRotation = 0.5
        obj.scalingCenter = (0.5, 0.5)
        curve = self.GetVector2((1.0, 1.0), (0.0, 1.0), duration, curveType=uiconst.ANIM_SMOOTH, timeOffset=timeOffset)
        return self.Play(curve, obj, 'scale', loops, callback, sleep)

    def Tr2DSquashIn(self, obj, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        obj.scalingRotation = 0.5
        obj.scalingCenter = (0.5, 0.5)
        curve = self.GetVector2((0.0, 1.0), (1.0, 1.0), duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'scale', loops, callback, sleep)

    def Tr2DRotateTo(self, obj, startAngle = 0.0, endAngle = 2 * math.pi, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0, curveSet = None):
        curve = self.GetScalar(startAngle, endAngle, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'rotation', loops, callback, sleep, curveSet=curveSet)

    def SpColorMorphTo(self, obj, startColor = None, endColor = Color.BLUE, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0, includeAlpha = True, attrName = 'color'):
        if startColor is None:
            startColor = obj.GetRGBA()
        if not includeAlpha:
            startColor = (startColor[0],
             startColor[1],
             startColor[2],
             obj.opacity)
            endColor = (endColor[0],
             endColor[1],
             endColor[2],
             obj.opacity)
        curve = self.GetColor(startColor, endColor, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, attrName, loops, callback, sleep)

    def SpColorMorphToBlack(self, obj, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        return self.SpColorMorphTo(obj, obj.GetRGBA(), Color.BLACK, duration, loops, curveType, callback, sleep, timeOffset)

    def SpColorMorphToWhite(self, obj, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        return self.SpColorMorphTo(obj, obj.GetRGBA(), Color.WHITE, duration, loops, curveType, callback, sleep, timeOffset)

    def SpGlowFadeTo(self, obj, startColor = (0.8, 0.8, 1.0, 0.3), endColor = (0, 0, 0, 0), glowFactor = 0.8, glowExpand = 3.0, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        obj.glowFactor = glowFactor
        obj.glowExpand = glowExpand
        curve = self.GetColor(startColor, endColor, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'glowColor', loops, callback, sleep, curveSet=curveSet)

    def SpGlowFadeIn(self, obj, glowColor = (0.8, 0.8, 1.0, 0.3), glowFactor = 0.8, glowExpand = 3.0, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        return self.SpGlowFadeTo(obj, (0, 0, 0, 0), glowColor, glowFactor, glowExpand, duration, loops, curveType, callback, sleep, curveSet=curveSet, timeOffset=timeOffset)

    def SpGlowFadeOut(self, obj, glowColor = (0.8, 0.8, 1.0, 0.3), glowFactor = 0.8, glowExpand = 3.0, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, curveSet = None, timeOffset = 0.0):
        return self.SpGlowFadeTo(obj, glowColor, (0, 0, 0, 0), glowFactor, glowExpand, duration, loops, curveType, callback, sleep, curveSet=curveSet, timeOffset=timeOffset)

    def SpShadowMoveTo(self, obj, startPos = (0.0, 0.0), endPos = (10.0, 10.0), color = None, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        obj.shadowColor = color or (0.0, 0.0, 0.0, 0.5)
        curve = self.GetVector2(startPos, endPos, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'shadowOffset', loops, callback, sleep)

    def SpShadowAppear(self, obj, offset = (10.0, 10.0), color = None, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        color = color or (0.0, 0.0, 0.0, 0.5)
        return self.SpShadowMoveTo(obj, (0.0, 0.0), offset, color, duration, loops, curveType, callback, sleep, timeOffset)

    def SpShadowDisappear(self, obj, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        return self.SpShadowMoveTo(obj, obj.shadowOffset, (0.0, 0.0), None, duration, loops, curveType, callback, sleep, timeOffset)

    def SpSecondaryTextureRotate(self, obj, startVal = 0.0, endVal = 2 * math.pi, duration = 2.0, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetScalar(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'rotationSecondary', loops, callback, sleep)

    def SpSecondaryTextureScale(self, obj, startVal = (1.0, 1.0), endVal = (0.0, 0.0), duration = 1.0, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetVector2(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'scaleSecondary', loops, callback, sleep)

    def SpTunnelTo(self, obj, startVal = (1.0, 1.0), endVal = (0.0, 0.0), texturePath = None, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        if not texturePath:
            texturePath = 'res:/UI/Texture/Classes/Animations/radialGradient.png'
        obj.SetSecondaryTexturePath(texturePath)
        obj.spriteEffect = trinity.TR2_SFX_MODULATE
        return self.SpSecondaryTextureScale(obj, startVal, endVal, duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def SpTunnelIn(self, obj, duration = 1.0, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        self.SpTunnelTo(obj, (3.0, 3.0), (0.0, 0.0), duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def SpTunnelOut(self, obj, duration = 1.0, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        self.SpTunnelTo(obj, (0.0, 0.0), (3.0, 3.0), duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def SpSecondaryTextureMove(self, obj, startVal = (-1.0, -1.0), endVal = (0, 0), duration = 1.0, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        curve = self.GetVector2(startVal, endVal, duration, curveType, timeOffset=timeOffset)
        return self.Play(curve, obj, 'translationSecondary', loops, callback, sleep)

    def SpMaskTo(self, obj, startVal = (-1.0, 0.0), endVal = (2.0, 0.0), texturePath = None, rotation = 0.0, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        if not texturePath:
            texturePath = 'res:/UI/Texture/Classes/Animations/maskToGradient.png'
        obj.SetSecondaryTexturePath(texturePath)
        obj.translationSecondary = startVal
        obj.spriteEffect = trinity.TR2_SFX_MODULATE
        obj.rotationSecondary = rotation
        return self.SpSecondaryTextureMove(obj, startVal, endVal, duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def SpMaskIn(self, obj, rotation = math.pi * 0.75, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        return self.SpMaskTo(obj, startVal=(-1.0, 0.0), endVal=(1.0, 0.0), rotation=rotation, duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def SpMaskOut(self, obj, rotation = -math.pi * 0.25, duration = 0.5, loops = 1, curveType = uiconst.ANIM_SMOOTH, callback = None, sleep = False, timeOffset = 0.0):
        return self.SpMaskTo(obj, startVal=(1.0, 0.0), endVal=(-1.0, 0.0), rotation=rotation, duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def SpSwoopBlink(self, obj, startVal = (-1.0, 0.0), endVal = (2.0, 0.0), texturePath = None, rotation = 0.75 * math.pi, duration = 0.5, loops = 1, curveType = uiconst.ANIM_LINEAR, callback = None, sleep = False, timeOffset = 0.0):
        if not texturePath:
            texturePath = 'res:/UI/Texture/Classes/Animations/swoopGradient.png'
        obj.SetSecondaryTexturePath(texturePath)
        obj.spriteEffect = trinity.TR2_SFX_MODULATE
        obj.rotationSecondary = rotation
        return self.SpSecondaryTextureMove(obj, startVal, endVal, duration=duration, loops=loops, curveType=curveType, callback=callback, sleep=sleep, timeOffset=timeOffset)

    def GetScalar(self, startValue, endValue, duration, curveType = uiconst.ANIM_SMOOTH, timeOffset = 0.0):
        if curveType is uiconst.ANIM_RANDOM:
            curve = trinity.Tr2ScalarExprCurve()
        else:
            curve = trinity.Tr2ScalarCurve()
            if not isinstance(curveType, (list, tuple)):
                curve.startValue = startValue
                curve.endValue = endValue
            curve.length = duration
        curve.timeOffset = timeOffset
        if curveType not in (uiconst.ANIM_LINEAR, uiconst.ANIM_RANDOM) and not isinstance(curveType, (list, tuple)):
            curve.interpolation = trinity.TR2CURVE_HERMITE
        if isinstance(curveType, (list, tuple)):
            points = curveType
            for keyTime, keyValue in points:
                key = keyTime * duration
                curve.AddKey(key, keyValue)

        elif curveType in uiconst.ANIM_OVERSHOT_TYPES:
            amount = self.GetOvershotAmount(curveType)
            keyTime = OVERSHOT_TIME * duration
            keyVal = endValue + amount * (endValue - startValue)
            curve.AddKey(keyTime, keyVal)
        elif curveType is uiconst.ANIM_WAVE:
            curve.AddKey(0.5 * duration, endValue)
            curve.endValue = startValue
        elif curveType is uiconst.ANIM_RANDOM:
            curve.expr = 'input1 + input2 * perlin(value, %s, 3.0, 4)' % duration
            curve.input1 = startValue
            curve.input2 = endValue
            curve.startValue = curve.endValue = startValue + (endValue - startValue) / 2
            curve.AddKey(25, endValue)
            curve.length = 50.0
        elif curveType is uiconst.ANIM_BOUNCE:
            curve.interpolation = trinity.TR2CURVE_HERMITE
            curve.startValue = startValue
            curve.AddKey(0.5 * duration, endValue)
            curve.endValue = startValue
        return curve

    def GetVector2(self, startValue, endValue, duration, curveType = uiconst.ANIM_SMOOTH, timeOffset = 0.0):
        curve = trinity.Tr2Vector2Curve()
        return self._GetVector(curve, startValue, endValue, duration, curveType, timeOffset)

    def GetVector3(self, startValue, endValue, duration, curveType = uiconst.ANIM_SMOOTH, timeOffset = 0.0):
        if isinstance(curveType, (list, tuple)):
            curve = trinity.Tr2GrannyVector3Curve()
            curve.CreateFromPoints(duration / (len(curveType) - 1), curveType)
            curve.timeOffset = timeOffset
            return curve
        else:
            curve = trinity.Tr2Vector3Curve()
            return self._GetVector(curve, startValue, endValue, duration, curveType, timeOffset)

    def _GetVector(self, curve, startValue, endValue, duration, curveType = uiconst.ANIM_SMOOTH, timeOffset = 0.0):
        curve.length = duration
        if not isinstance(curveType, (list, tuple)):
            curve.startValue = startValue
            curve.endValue = endValue
        curve.timeOffset = timeOffset
        if curveType is not uiconst.ANIM_LINEAR:
            curve.interpolation = trinity.TR2CURVE_HERMITE
        if isinstance(curveType, (list, tuple)):
            points = curveType
            for keyTime, keyValue in points:
                key = keyTime * duration
                curve.AddKey(key, keyValue)

        if curveType in uiconst.ANIM_OVERSHOT_TYPES:
            amount = self.GetOvershotAmount(curveType)
            keyTime = OVERSHOT_TIME * duration
            keyValX = endValue[0] + amount * (endValue[0] - startValue[0])
            keyValY = endValue[1] + amount * (endValue[1] - startValue[1])
            curve.AddKey(keyTime, (keyValX, keyValY))
        elif curveType is uiconst.ANIM_WAVE:
            curve.AddKey(0.5 * duration, endValue)
            curve.endValue = startValue
        return curve

    def GetOvershotAmount(self, curveType):
        return uiconst.ANIM_OVERSHOT_TYPES.index(curveType) * 0.2 + 0.1

    def GetQuaternion(self, startValue, endValue, duration, curveType = uiconst.ANIM_SMOOTH, timeOffset = 0.0):
        curve = trinity.Tr2QuaternionCurve()
        curve.length = duration
        if not isinstance(curveType, (list, tuple)):
            curve.startValue = startValue
            curve.endValue = endValue
        curve.interpolation = trinity.TR2CURVE_SPHERICAL_LINEAR
        if isinstance(curveType, (list, tuple)):
            points = curveType
            for keyTime, keyValue in points:
                key = keyTime * duration
                curve.AddKey(key, keyValue)

        elif curveType in uiconst.ANIM_OVERSHOT_TYPES:
            amount = self.GetOvershotAmount(curveType)
            keyTime = OVERSHOT_TIME * duration
            keyValX = endValue[0] + amount * (endValue[0] - startValue[0])
            keyValY = endValue[1] + amount * (endValue[1] - startValue[1])
            curve.AddKey(keyTime, (keyValX, keyValY))
        elif curveType is uiconst.ANIM_WAVE:
            curve.AddKey(0.5 * duration, endValue)
            curve.endValue = startValue
        return curve

    def GetColor(self, startValue, endValue, duration, curveType = uiconst.ANIM_LINEAR, timeOffset = 0.0):
        curve = trinity.Tr2ColorCurve()
        curve.length = duration
        curve.timeOffset = timeOffset
        if isinstance(curveType, (list, tuple)):
            points = curveType
            for keyTime, keyValue in points:
                key = keyTime * duration
                curve.AddKey(key, keyValue)

        else:
            curve.startValue = startValue
            curve.endValue = endValue
        if curveType is uiconst.ANIM_WAVE:
            curve.AddKey(0.5 * duration, endValue)
            curve.endValue = startValue
        return curve


animations = UIAnimations()
