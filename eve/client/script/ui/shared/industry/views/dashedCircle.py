#Embedded file name: eve/client/script/ui/shared/industry/views\dashedCircle.py
from carbonui.const import TOPLEFT, CENTER, TOALL, UI_DISABLED, UI_NORMAL
from math import pi, cos, sin
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from carbonui.util.color import Color
from eve.client.script.ui.shared.industry.industryUIConst import OPACITY_LINES, COLOR_NOTREADY, OPACITY_SEGMENTINCOMPLETE, COLOR_READY
from eve.client.script.ui.shared.industry.views.industryLine import IndustryLineTrace
import uthread

class DashedCircle(Container):
    default_name = 'DashedCircle'
    default_radius = 13
    default_lineWidth = 3.0
    default_align = TOPLEFT
    default_state = UI_NORMAL
    default_rotationCenter = (0.5, 0.5)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.numSegments = attributes.numSegments
        self.radius = attributes.Get('radius', self.default_radius)
        self.lineWidth = attributes.Get('lineWidth', self.default_lineWidth)
        self.updateIconThread = None
        self.width = self.height = self.radius * 2
        self.segmentTransform = Transform(name='segmentTransform', parent=self, align=TOALL)
        self.segments = self.ConstructSegments()
        self.icon = Sprite(name='icon', parent=self, align=CENTER, state=UI_DISABLED, width=20, height=20)
        self.AnimEntry()

    def ConstructSegments(self):
        ret = []
        stepSize = 2 * pi / self.numSegments
        numPoints = max(3, int(30 / self.numSegments))
        w = self.lineWidth / 2.0
        radius = self.radius - self.lineWidth / 2.0
        for i in xrange(self.numSegments):
            line = VectorLineTrace(name='line', parent=self.segmentTransform, lineWidth=self.lineWidth, width=100, height=100)
            for j in xrange(numPoints + 1):
                t = float(i) / self.numSegments * 2 * pi + float(j) / numPoints * stepSize
                t += pi / 2
                point = (w + radius * (1.0 + cos(t)), w + radius * (1.0 + sin(t)))
                if self.numSegments > 1 and (j == 0 or j == numPoints):
                    line.AddPoint(point, color=(1, 1, 1, 0))
                else:
                    line.AddPoint(point)

            ret.append(line)

        return ret

    def AnimEntry(self):
        duration = 0.45 / self.numSegments
        k = 0.3 / self.numSegments
        uicore.animations.Tr2DRotateTo(self.segmentTransform, 0.3, 0.0, duration=0.45, timeOffset=0.3)
        offset = 0.3 / self.numSegments
        for i, segment in enumerate(self.segments):
            uicore.animations.MorphScalar(segment, 'start', 0.5, 0.0, duration=0.3, timeOffset=0.3 + i * offset)
            uicore.animations.MorphScalar(segment, 'end', 0.5, 1.0, duration=0.3, timeOffset=0.3 + i * offset)

    def UpdateState(self, numFilledSegments, isReady = True, isOptional = False, isOptionSelected = True, animate = True):
        isEverythingReady = numFilledSegments == self.numSegments
        baseColor = IndustryLineTrace.GetLineColor(isReady, isOptionSelected)
        for i, segment in enumerate(self.segments):
            if isEverythingReady:
                opacity = OPACITY_LINES
            else:
                isFilled = i < numFilledSegments
                opacity = OPACITY_LINES if not isFilled else OPACITY_SEGMENTINCOMPLETE
            color = Color(*baseColor).SetAlpha(opacity).GetRGBA()
            if animate:
                uicore.animations.SpColorMorphTo(segment, segment.GetRGBA(), color, duration=0.3)
            else:
                segment.SetRGBA(*color)

        self.UpdateIcon(isReady, isOptional)

    def UpdateIcon(self, isEverythingReady, isOptional):
        if isEverythingReady or isOptional:
            texturePath = 'res:/UI/Texture/classes/Industry/Input/circleReady.png'
        else:
            texturePath = 'res:/UI/Texture/classes/Industry/Input/circleNotReady.png'
        if self.icon.texturePath == texturePath:
            return
        if self.updateIconThread:
            self.updateIconThread.kill()
        self.updateIconThread = uthread.new(self._UpdateIconThread, texturePath)

    def _UpdateIconThread(self, texturePath):
        uicore.animations.FadeOut(self.icon, duration=0.15, sleep=True)
        self.icon.texturePath = texturePath
        uicore.animations.FadeIn(self.icon, duration=0.15)

    def OnMouseEnter(self, *args):
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')
