#Embedded file name: eve/client/script/ui/shared/industry/views\industryLine.py
from carbonui.const import TOALL
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from carbonui.util.color import Color
from eve.client.script.ui.shared.industry.industryUIConst import OPACITY_LINES, COLOR_FRAME, COLOR_NOTREADY, COLOR_READY
import trinity
COLOR_OPTIONAL_NOTREADY = (0.2, 0.2, 0.2, 1.0)

class IndustryLineTrace(VectorLineTrace):
    default_name = 'IndustryLineTrace'
    default_spriteEffect = trinity.TR2_SFX_COPY
    default_textureWidth = 12.0
    default_texturePath = 'res:/UI/Texture/classes/Industry/input/lineSolid.png'
    default_lineWidth = 8.0
    default_opacity = OPACITY_LINES

    def UpdateColor(self, isReady, isOptional = False, isOptionSelected = True, animate = True):
        color = IndustryLineTrace.GetLineColor(isReady, isOptionSelected=isOptionSelected)
        if animate:
            uicore.animations.SpColorMorphTo(self, self.GetRGBA(), color, duration=0.3)
        else:
            self.SetRGBA(*color)
        if isOptional:
            self.texturePath = 'res:/UI/Texture/classes/Industry/input/lineOptional.png'
        elif isReady:
            self.texturePath = 'res:/UI/Texture/classes/Industry/input/lineSolid.png'
        else:
            self.texturePath = 'res:/UI/Texture/classes/Industry/input/line.png'

    @staticmethod
    def GetLineColor(isReady, isOptionSelected):
        if not isOptionSelected:
            color = COLOR_OPTIONAL_NOTREADY
        elif isReady:
            color = COLOR_READY
        else:
            color = COLOR_NOTREADY
        color = Color(*color).SetAlpha(OPACITY_LINES).GetRGBA()
        return color

    def AnimEntry(self, timeOffset = 0.0, i = 1, animate = True):
        if animate:
            uicore.animations.FadeTo(self, 0.0, OPACITY_LINES, duration=0.2, timeOffset=0.15 + timeOffset + i * 0.05)
            uicore.animations.MorphScalar(self, 'end', 0.0, 1.0, duration=0.4, timeOffset=timeOffset + i * 0.1)
        else:
            self.opacity = OPACITY_LINES
            self.end = 1.0
