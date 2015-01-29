#Embedded file name: carbonui/primitives\vectorline.py
import carbonui.const as uiconst
import trinity
import util
from .sprite import TexturedBase

class VectorLine(TexturedBase):
    """
    A line between two points.
    
    To texture the line, set spriteEffect=TR2_SFX_COPY, then pass in a texturePath, 
    textureWidth and use textureOffset to animate
    """
    __guid__ = 'uicls.VectorLine'
    __renderObject__ = trinity.Tr2Sprite2dLine
    __notifyevents__ = ['OnUIScalingChange']
    default_name = 'vectorline'
    default_align = uiconst.TOPLEFT
    default_spriteEffect = trinity.TR2_SFX_FILL_AA
    default_translationFrom = (0.0, 0.0)
    default_translationTo = (100.0, 100.0)
    default_widthFrom = 1.0
    default_widthTo = 1.0
    default_colorFrom = util.Color.WHITE
    default_colorTo = util.Color.WHITE
    default_textureWidth = 1.0
    _colorFrom = None
    _colorTo = None
    _translationFrom = None
    _translationTo = None
    _widthFrom = None
    _widthTo = None

    def ApplyAttributes(self, attributes):
        TexturedBase.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.translationFrom = attributes.get('translationFrom', self.default_translationFrom)
        self.widthFrom = attributes.get('widthFrom', self.default_widthFrom)
        self.translationTo = attributes.get('translationTo', self.default_translationTo)
        self.widthTo = attributes.get('widthTo', self.default_widthTo)
        self.colorFrom = attributes.get('colorFrom', self.default_colorFrom)
        self.colorTo = attributes.get('colorTo', self.default_colorTo)
        self.textureWidth = attributes.get('textureWidth', self.default_textureWidth)
        if attributes.texturePath is not None:
            self.renderObject.texturePrimary.atlasTexture.isStandAlone = True

    @apply
    def translationFrom():
        doc = '\n        The translation of the starting point of the line.\n        '

        def fget(self):
            return self._translationFrom

        def fset(self, value):
            self._translationFrom = value
            if self.renderObject:
                x = uicore.ScaleDpiF(value[0])
                y = uicore.ScaleDpiF(value[1])
                self.renderObject.translationFrom = (x, y)

        return property(**locals())

    @apply
    def translationTo():
        doc = '\n        The translation of the ending point of the line.\n        '

        def fget(self):
            return self._translationTo

        def fset(self, value):
            self._translationTo = value
            if self.renderObject:
                x = uicore.ScaleDpiF(value[0])
                y = uicore.ScaleDpiF(value[1])
                self.renderObject.translationTo = (x, y)

        return property(**locals())

    @apply
    def widthFrom():
        doc = '\n        The width of the line at the starting point.\n        '

        def fget(self):
            return self._widthFrom

        def fset(self, value):
            self._widthFrom = float(value)
            if self.renderObject:
                self.renderObject.widthFrom = uicore.ScaleDpiF(value)

        return property(**locals())

    @apply
    def widthTo():
        doc = '\n        The width of the line at the ending point.\n        '

        def fget(self):
            return self._widthTo

        def fset(self, value):
            self._widthTo = float(value)
            if self.renderObject:
                self.renderObject.widthTo = uicore.ScaleDpiF(value)

        return property(**locals())

    @apply
    def colorFrom():
        doc = '\n        The color of the line at the starting point.\n        '

        def fget(self):
            return self._colorFrom

        def fset(self, value):
            self._colorFrom = value
            if self.renderObject:
                self.renderObject.colorFrom = value

        return property(**locals())

    @apply
    def colorTo():
        doc = '\n        The color of the line at the ending point.\n        '

        def fget(self):
            return self._colorTo

        def fset(self, value):
            self._colorTo = value
            if self.renderObject:
                self.renderObject.colorTo = value

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

    def OnUIScalingChange(self, *args):
        self.translationFrom = self._translationFrom
        self.translationTo = self._translationTo
        self.widthFrom = self._widthFrom
        self.widthTo = self._widthTo
