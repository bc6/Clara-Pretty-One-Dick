#Embedded file name: carbonui/primitives\stretchspritehorizontal.py
from .sprite import TexturedBase
import carbonui.const as uiconst
import trinity

class StretchSpriteHorizontal(TexturedBase):
    """
    A UI object that renders a stretched sprite. This is done by cutting a texture
    into 3 pieces and stretching the middle part.
    """
    __guid__ = 'uicls.StretchSpriteHorizontalCore'
    __renderObject__ = trinity.Tr2Sprite2dStretch
    default_name = 'stretchspritehorizontal'
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0
    default_color = (1.0, 1.0, 1.0, 1.0)
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_DISABLED
    default_leftEdgeSize = 6
    default_rightEdgeSize = 6
    default_fillCenter = True
    default_offset = 0
    _leftEdgeSize = 0
    _rightEdgeSize = 0
    _offset = 0

    def ApplyAttributes(self, attributes):
        self.offset = attributes.get('offset', self.default_offset)
        self.leftEdgeSize = attributes.get('leftEdgeSize', self.default_leftEdgeSize)
        self.rightEdgeSize = attributes.get('rightEdgeSize', self.default_rightEdgeSize)
        self.fillCenter = attributes.get('fillCenter', self.default_fillCenter)
        TexturedBase.ApplyAttributes(self, attributes)

    def SetAlign(self, align):
        TexturedBase.SetAlign(self, align)
        ro = self.renderObject
        if not ro:
            return

    align = property(TexturedBase.GetAlign, SetAlign)

    @apply
    def leftEdgeSize():
        doc = ''

        def fget(self):
            return self._leftEdgeSize

        def fset(self, value):
            self._leftEdgeSize = value
            ro = self.renderObject
            if ro:
                ro.leftEdgeSize = value

        return property(**locals())

    @apply
    def rightEdgeSize():
        doc = ''

        def fget(self):
            return self._rightEdgeSize

        def fset(self, value):
            self._rightEdgeSize = value
            ro = self.renderObject
            if ro:
                ro.rightEdgeSize = value

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
