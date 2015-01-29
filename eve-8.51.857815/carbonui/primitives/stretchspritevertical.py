#Embedded file name: carbonui/primitives\stretchspritevertical.py
import carbonui.const as uiconst
import trinity
from .sprite import TexturedBase

class StretchSpriteVertical(TexturedBase):
    """
    A UI object that renders a stretched sprite. This is done by cutting a texture
    into 3 pieces and stretching the middle part.
    """
    __guid__ = 'uicls.StretchSpriteVerticalCore'
    __renderObject__ = trinity.Tr2Sprite2dStretchVertical
    default_name = 'stretchspritevertical'
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0
    default_color = (1.0, 1.0, 1.0, 1.0)
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_DISABLED
    default_topEdgeSize = 6
    default_bottomEdgeSize = 6
    default_fillCenter = True
    default_offset = 0
    _topEdgeSize = 0
    _bottomEdgeSize = 0
    _offset = 0
    _fillCenter = 0

    def ApplyAttributes(self, attributes):
        self.topEdgeSize = attributes.get('topEdgeSize', self.default_topEdgeSize)
        self.bottomEdgeSize = attributes.get('bottomEdgeSize', self.default_bottomEdgeSize)
        self.fillCenter = attributes.get('fillCenter', self.default_fillCenter)
        TexturedBase.ApplyAttributes(self, attributes)

    def SetAlign(self, align):
        TexturedBase.SetAlign(self, align)
        ro = self.renderObject
        if not ro:
            return

    align = property(TexturedBase.GetAlign, SetAlign)

    @apply
    def topEdgeSize():
        doc = ''

        def fget(self):
            return self._topEdgeSize

        def fset(self, value):
            self._topEdgeSize = value
            ro = self.renderObject
            if ro:
                ro.topEdgeSize = value

        return property(**locals())

    @apply
    def bottomEdgeSize():
        doc = ''

        def fget(self):
            return self._bottomEdgeSize

        def fset(self, value):
            self._bottomEdgeSize = value
            ro = self.renderObject
            if ro:
                ro.bottomEdgeSize = value

        return property(**locals())

    @apply
    def fillCenter():
        doc = 'If True, the center of the sprite is filled - otherwise it is left blank'

        def fget(self):
            return self._fillCenter

        def fset(self, value):
            self._fillCenter = value
            ro = self.renderObject
            if ro:
                ro.fillCenter = value

        return property(**locals())

    @apply
    def offset():
        doc = '\n            Offset the sprite. Positive values will make it smaller horizontally,\n            and negative bigger. The sprite is shifted vertically by this offset.\n        '

        def fget(self):
            return self._offset

        def fset(self, value):
            self._offset = value
            ro = self.renderObject
            if ro:
                ro.offset = value

        return property(**locals())
