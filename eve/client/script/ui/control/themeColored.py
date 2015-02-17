#Embedded file name: eve/client/script/ui/control\themeColored.py
from math import pi
from carbonui import const as uiconst
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
import telemetry
from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
from carbonui.primitives.stretchspritevertical import StretchSpriteVertical
from eve.client.script.ui.control.eveFrame import Frame
from eve.client.script.ui.control.eveLabel import Label

class ColorThemeMixin:
    """
    Mixin used to automatically apply UI Theme color to controls inheriting from it
    """
    default_colorType = None
    default_fixedColor = None

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        self.fixedColor = attributes.Get('color', self.default_fixedColor)
        self.colorType = attributes.Get('colorType', self.default_colorType)
        sm.GetService('uiColor').Register(self)
        self.UpdateColor()

    @telemetry.ZONE_METHOD
    def UpdateColor(self):
        if self.fixedColor is not None:
            color = self.fixedColor
        else:
            color = sm.GetService('uiColor').GetUIColor(self.colorType)
        r, g, b, _ = color
        self.SetRGB(r, g, b, self.opacity)

    def SetFixedColor(self, fixedColor):
        self.fixedColor = fixedColor
        self.UpdateColor()

    def SetColorType(self, colorType):
        self.colorType = colorType
        self.UpdateColor()


class SpriteThemeColored(Sprite, ColorThemeMixin):
    default_name = 'SpriteThemeColored'
    default_colorType = uiconst.COLORTYPE_UIHILIGHT

    def ApplyAttributes(self, attributes):
        Sprite.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)


class FrameThemeColored(Frame, ColorThemeMixin):
    default_name = 'FrameThemeColored'
    default_colorType = uiconst.COLORTYPE_UIBASE

    def ApplyAttributes(self, attributes):
        Frame.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)


class FillThemeColored(Fill, ColorThemeMixin):
    default_name = 'FillThemeColored'
    default_colorType = uiconst.COLORTYPE_UIBASE

    def ApplyAttributes(self, attributes):
        Fill.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)


class LineThemeColored(Line, ColorThemeMixin):
    default_name = 'LineThemeColored'
    default_colorType = uiconst.COLORTYPE_UIHILIGHT
    default_opacity = 0.5

    def ApplyAttributes(self, attributes):
        Line.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)


class GradientThemeColored(GradientSprite, ColorThemeMixin):
    default_rgbData = [(0, (1.0, 1.0, 1.0))]
    default_alphaData = [(0, 0.7), (0.9, 0.0)]
    default_rotation = -pi / 2
    default_colorType = uiconst.COLORTYPE_UIBASECONTRAST

    def ApplyAttributes(self, attributes):
        GradientSprite.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)


class LabelThemeColored(Label, ColorThemeMixin):
    default_colorType = uiconst.COLORTYPE_UIHILIGHTGLOW

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        ColorThemeMixin.ApplyAttributes(self, attributes)
        Label.ApplyAttributes(self, attributes)


class StretchSpriteHorizontalThemeColored(StretchSpriteHorizontal, ColorThemeMixin):
    default_colorType = uiconst.COLORTYPE_UIHILIGHT

    def ApplyAttributes(self, attributes):
        StretchSpriteHorizontal.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)


class StretchSpriteVerticalThemeColored(StretchSpriteVertical, ColorThemeMixin):
    default_colorType = uiconst.COLORTYPE_UIHILIGHT

    def ApplyAttributes(self, attributes):
        StretchSpriteVertical.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)
