#Embedded file name: carbonui/primitives\gradientSprite.py
"""
Convenience classes for manipulation of UI elements containing gradient textures
"""
from .sprite import Sprite
import math
import trinity

class GradientConst:
    __guid__ = 'uicls.GradientConst'
    INTERP_LINEAR = 0
    INTERP_COSINE = 1
    INTERP_BEZIER = 2
    interpModeToString = {INTERP_LINEAR: 'linear',
     INTERP_COSINE: 'cosine',
     INTERP_BEZIER: 'bezier'}
    interpModeFromString = {'linear': INTERP_LINEAR,
     'cosine': INTERP_COSINE,
     'bezier': INTERP_BEZIER}


class GradientSprite(Sprite):
    """ A sprite that dynamically renders gradients """
    __guid__ = 'uicontrols.GradientSprite'
    default_rgbData = [(0.0, (1.0, 0.0, 0.0)), (0.5, (0.0, 1.0, 0.0)), (1.0, (0.0, 0.0, 1.0))]
    default_alphaData = [(0.0, 1.0), (1.0, 1.0)]
    default_textureSize = 128
    default_colorInterp = GradientConst.INTERP_LINEAR
    default_alphaInterp = GradientConst.INTERP_LINEAR
    default_toCorners = False
    default_radial = False

    def ApplyAttributes(self, attributes):
        self.colorData = attributes.get('rgbData', self.default_rgbData)
        self.alphaData = attributes.get('alphaData', self.default_alphaData)
        self.textureSize = attributes.get('textureSize', self.default_textureSize)
        self.colorInterp = attributes.get('colorInterp', self.default_colorInterp)
        self.alphaInterp = attributes.get('alphaInterp', self.default_alphaInterp)
        self.toCorners = attributes.get('toCorners', self.default_toCorners)
        self.radial = attributes.get('radial', self.default_radial)
        Sprite.ApplyAttributes(self, attributes)
        self.SetGradient()
        trinity.device.RegisterResource(self)

    def SetGradient(self, colorData = None, alphaData = None):
        if colorData:
            self.colorData = colorData
        if alphaData:
            self.alphaData = alphaData
        rgbDivs = [ div for div, color in self.colorData ]
        rgbPoints = [ color for div, color in self.colorData ]
        alphaDivs = [ div for div, alpha in self.alphaData ]
        alphaPoints = [ alpha for div, alpha in self.alphaData ]
        gradientData = {'rgbInterp': GradientConst.interpModeToString[self.colorInterp],
         'alphaInterp': GradientConst.interpModeToString[self.alphaInterp],
         'rgbDivs': rgbDivs,
         'rgbPoints': rgbPoints,
         'alphaDivs': alphaDivs,
         'alphaPoints': alphaPoints,
         'textureSize': self.textureSize,
         'toCorners': self.toCorners}
        if self.radial:
            prefixString = 'dynamic:/gradient_radial/'
        else:
            prefixString = 'dynamic:/gradient/'
        self.gradientDataString = prefixString + str(gradientData)
        self.SetTexturePath(self.gradientDataString)

    @apply
    def rotation():
        doc = 'Set rotation of primary texture'

        def fget(self):
            return self.texture.rotation

        def fset(self, value):
            if not self.texture:
                return
            self.texture.rotation = value
            self.texture.useTransform = bool(value)
            if value:
                value %= math.pi / 2.0
                diff = self.textureSize / 2.0 * (math.sin(value) + math.cos(value) - 1.0)
                k_magic = 0.99
                self.texture.srcWidth = (self.textureSize - 2.0 * diff) * k_magic
                self.texture.srcX = math.ceil(diff)

        return property(**locals())

    def OnInvalidate(self, level):
        if self.texture:
            self.texture.atlasTexture = None

    def OnCreate(self, dev):
        self.SetTexturePath(self.gradientDataString)


class Gradient2DSprite(Sprite):
    """ DEPRICATED: Use GradientSprite instead """
    __guid__ = 'uicls.Gradient2DSprite'
    default_colors = [(1.0, 1.0, 1.0), (0.0, 0.0, 0.0)]
    default_interp = [0.0, 1.0]
    default_alpha = [1.0, 0.0]
    default_textureSize = 128

    def ApplyAttributes(self, kwargs):
        Sprite.ApplyAttributes(self, kwargs)
        gradientData = {'rgbDataHorizontal': kwargs.get('rgbDataHorizontal', self.default_colors),
         'rgbDataVertical': kwargs.get('rgbDataVertical', self.default_colors),
         'alphaDataHorizontal': kwargs.get('alphaDataHorizontal', self.default_alpha),
         'alphaDataVertical': kwargs.get('alphaDataVertical', self.default_alpha),
         'rgbHorizontal': kwargs.get('rgbHorizontal', self.default_interp),
         'rgbVertical': kwargs.get('rgbVertical', self.default_interp),
         'alphaHorizontal': kwargs.get('alphaHorizontal', self.default_interp),
         'alphaVertical': kwargs.get('alphaVertical', self.default_interp),
         'textureSize': kwargs.get('textureSize', self.default_textureSize),
         'rgbInterp': kwargs.get('rgbInterp', 'linear'),
         'alphaInterp': kwargs.get('alphaInterp', 'linear')}
        self.gradientDataString = 'dynamic:/gradient2d/' + str(gradientData)
        self.SetTexturePath(self.gradientDataString)
        trinity.device.RegisterResource(self)

    def OnInvalidate(self, level):
        if self.texture:
            self.texture.atlasTexture = None

    def OnCreate(self, dev):
        self.SetTexturePath(self.gradientDataString)
