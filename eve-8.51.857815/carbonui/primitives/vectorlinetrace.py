#Embedded file name: carbonui/primitives\vectorlinetrace.py
import carbonui.const as uiconst
import trinity
import geo2
from .sprite import TexturedBase
import mathUtil
from math import cos, sin
CORNERTYPE_MITER = 0
CORNERTYPE_ROUND = 1
CORNERTYPE_NONE = 2

class VectorLineTrace(TexturedBase):
    """
    A series of lines, optionally in a closed loop. The rendering can start and
    end at relative points along the path. Interesting effects can be done by
    animating those start and end points.
    
    To texture the line, set spriteEffect=TR2_SFX_COPY, then pass in a texturePath, 
    textureWidth and use textureOffset to animate
    """
    __guid__ = 'uiprimitives.VectorLineTrace'
    __renderObject__ = trinity.Tr2Sprite2dLineTrace
    default_name = 'vectorlinetrace'
    default_align = uiconst.TOPLEFT
    default_lineWidth = 1.0
    default_spriteEffect = trinity.TR2_SFX_FILL_AA
    default_textureWidth = 1.0
    default_cornerType = CORNERTYPE_MITER

    def ApplyAttributes(self, attributes):
        TexturedBase.ApplyAttributes(self, attributes)
        self.lineWidth = attributes.get('lineWidth', self.default_lineWidth)
        self.textureWidth = attributes.get('textureWidth', self.default_textureWidth)
        self.cornerType = attributes.Get('cornerType', self.default_cornerType)

    @apply
    def lineWidth():
        doc = '\n        The width of the line segments.\n        '

        def fget(self):
            return self._lineWidth

        def fset(self, value):
            self._lineWidth = value
            if self.renderObject:
                self.renderObject.lineWidth = uicore.ScaleDpiF(value)

        return property(**locals())

    @apply
    def isLoop():
        doc = '\n        If set, the path is closed, implicitly adding a line segment from\n        the last point to the starting point.\n        '

        def fget(self):
            return self.renderObject.isLoop

        def fset(self, value):
            self.renderObject.isLoop = value

        return property(**locals())

    @apply
    def cornerType():
        doc = '\n        Determines the shapes of corners connecting the line segments. Use CORNERTYPE_X enumerations.\n        '

        def fget(self):
            return self.renderObject.cornerType

        def fset(self, value):
            self.renderObject.cornerType = value

        return property(**locals())

    @apply
    def start():
        doc = '\n        Where to start drawing the line, as a proportion of the length of\n        the line path. Defaults to 0 to start at the start of the path.\n        '

        def fget(self):
            return self.renderObject.start

        def fset(self, value):
            self.renderObject.start = value

        return property(**locals())

    @apply
    def end():
        doc = '\n        Where to stop drawing the line, as a proportion of the length of\n        the line path. Defaults to 1 to stop at the end of the path.\n        '

        def fget(self):
            return self.renderObject.end

        def fset(self, value):
            self.renderObject.end = value

        return property(**locals())

    @apply
    def textureWidth():
        doc = '\n        Width of the texture along the line\n        '

        def fget(self):
            return self.renderObject.textureWidth

        def fset(self, value):
            self.renderObject.textureWidth = value

        return property(**locals())

    @apply
    def textureOffset():
        doc = '\n        Offset of the texture along the line\n        '

        def fget(self):
            return self.renderObject.textureOffset

        def fset(self, value):
            self.renderObject.textureOffset = value

        return property(**locals())

    def AddPoint(self, pos, color = (1.0, 1.0, 1.0, 1.0), name = '', idx = -1):
        v = trinity.Tr2Sprite2dLineTraceVertex()
        x, y = pos
        x = uicore.ScaleDpiF(x)
        y = uicore.ScaleDpiF(y)
        v.position = (x, y)
        v.color = color
        v.name = name
        self.renderObject.vertices.insert(idx, v)

    def AddPoints(self, posList, color = (1.0, 1.0, 1.0, 1.0)):
        for pos in posList:
            self.AddPoint(pos, color)

    def SetTexturePath(self, texturePath):
        TexturedBase.SetTexturePath(self, texturePath)
        if self.texturePath:
            self.renderObject.texturePrimary.atlasTexture.isStandAlone = True

    texturePath = property(TexturedBase.GetTexturePath, SetTexturePath)

    def Flush(self):
        if self.renderObject:
            del self.renderObject.vertices[:]


class DashedCircle(VectorLineTrace):
    __notifyevents__ = ['OnUIScalingChange']
    demoCount = 0

    def ApplyAttributes(self, attributes):
        VectorLineTrace.ApplyAttributes(self, attributes)
        self.dashCount = attributes.dashCount or 5
        self.dashSizeFactor = attributes.dashSizeFactor or 2.0
        self.startAngle = attributes.startAngle or mathUtil.DegToRad(180.0)
        self.range = attributes.range or mathUtil.DegToRad(180.0)
        self.radius = attributes.radius or 60
        self.lineWidth = attributes.lineWidth or 7
        self.startColor = attributes.startColor or (1, 1, 1, 1)
        self.endColor = attributes.endColor or (1, 1, 1, 1)
        self.gapEnds = attributes.gapEnds or True
        self.PlotLineTrace()
        sm.RegisterNotify(self)

    def ValueDown(self):
        self.demoCount += 1
        if self.demoCount < 2:
            uicore.animations.MorphScalar(self, 'end', 1.0, 0.0, duration=2.0, callback=self.ValueUp)

    def ValueUp(self):
        uicore.animations.MorphScalar(self, 'end', 0.0, 1.0, duration=2.0, callback=self.ValueDown)

    def PlotLineTrace(self):
        circum = self.radius * self.range
        if self.gapEnds:
            gapStepRad = self.range / (self.dashCount * (self.dashSizeFactor + 1))
        else:
            gapStepRad = self.range / (self.dashCount * (self.dashSizeFactor + 1) - 1)
        dashStepRad = gapStepRad * self.dashSizeFactor
        pixelRad = self.range / circum
        centerOffset = self.radius + self.lineWidth * 0.5
        jointOffset = min(gapStepRad / 3, pixelRad / 2)
        smooth = True
        rot = self.startAngle
        if self.gapEnds:
            rot += gapStepRad / 2
        for i in xrange(self.dashCount):
            point = (centerOffset + self.radius * cos(rot - jointOffset), centerOffset + self.radius * sin(rot - jointOffset))
            dashColor = geo2.Vec4Lerp(self.startColor, self.endColor, (rot - jointOffset - self.startAngle) / self.range)
            r, g, b, a = dashColor
            self.AddPoint(point, (r,
             g,
             b,
             0.0))
            point = (centerOffset + self.radius * cos(rot + jointOffset), centerOffset + self.radius * sin(rot + jointOffset))
            dashColor = geo2.Vec4Lerp(self.startColor, self.endColor, (rot + jointOffset - self.startAngle) / self.range)
            self.AddPoint(point, dashColor)
            if smooth:
                smoothRad = pixelRad * 4 + jointOffset
                while smoothRad < dashStepRad - jointOffset:
                    point = (centerOffset + self.radius * cos(rot + smoothRad), centerOffset + self.radius * sin(rot + smoothRad))
                    dashColor = geo2.Vec4Lerp(self.startColor, self.endColor, (rot + smoothRad - self.startAngle) / self.range)
                    self.AddPoint(point, dashColor)
                    smoothRad += pixelRad * 4

            rot += dashStepRad
            point = (centerOffset + self.radius * cos(rot - jointOffset), centerOffset + self.radius * sin(rot - jointOffset))
            dashColor = geo2.Vec4Lerp(self.startColor, self.endColor, (rot - jointOffset - self.startAngle) / self.range)
            self.AddPoint(point, dashColor)
            point = (centerOffset + self.radius * cos(rot + jointOffset), centerOffset + self.radius * sin(rot + jointOffset))
            dashColor = geo2.Vec4Lerp(self.startColor, self.endColor, (rot + jointOffset - self.startAngle) / self.range)
            r, g, b, a = dashColor
            self.AddPoint(point, (r,
             g,
             b,
             0.0))
            rot += gapStepRad

        self.width = self.height = centerOffset * 2

    def OnUIScalingChange(self, *args):
        self.Flush()
        self.PlotLineTrace()
