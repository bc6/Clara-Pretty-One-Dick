#Embedded file name: carbonui/primitives\frame.py
import carbonui.const as uiconst
import trinity
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import TexturedBase

class Frame(TexturedBase):
    """
    A UI object that renders a frame. This is done by cutting a texture into 9 pieces
    and stretching the side parts. The corner width and height is defined by cornerSize.
    
    It is possible to use pre-defined styles having different corner radius, width
    and shadow styles by passing in different frameConst arguments.
    """
    __guid__ = 'uiprimitives.FrameCore'
    __renderObject__ = trinity.Tr2Sprite2dFrame
    default_name = 'framesprite'
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0
    default_color = (1.0, 1.0, 1.0, 1.0)
    default_align = uiconst.TOALL
    default_frameConst = uiconst.FRAME_BORDER1_CORNER0
    default_state = uiconst.UI_DISABLED
    default_offset = 0
    default_cornerSize = 6
    default_fillCenter = True
    default_filter = False
    _offset = 0
    _cornerSize = 0

    def ApplyAttributes(self, attributes):
        self.offset = self.default_offset
        self.cornerSize = self.default_cornerSize
        self.fillCenter = attributes.get('fillCenter', self.default_fillCenter)
        TexturedBase.ApplyAttributes(self, attributes)
        texturePath = attributes.get('texturePath', self.default_texturePath)
        if texturePath:
            self.cornerSize = attributes.get('cornerSize', self.default_cornerSize)
            self.offset = attributes.get('offset', self.default_offset)
        else:
            self.LoadFrame(attributes.get('frameConst', self.default_frameConst))

    @apply
    def cornerSize():
        doc = ''

        def fget(self):
            return self._cornerSize

        def fset(self, value):
            self._cornerSize = value
            ro = self.renderObject
            if ro:
                ro.cornerSize = value

        return property(**locals())

    @apply
    def fillCenter():
        doc = 'If True, the center of the frame is filled - otherwise it is left blank'

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
        doc = '\n        Offset the frame. Positive values will make it smaller, and negative bigger.\n        '

        def fget(self):
            return self._offset

        def fset(self, value):
            self._offset = value
            ro = self.renderObject
            if ro:
                ro.offset = value
            self.FlagAlignmentDirty()

        return property(**locals())

    def LoadFrame(self, frameConst = None):
        """
        Select frame style. frameConst must be a uiconst.FRAME_{style} constant
        """
        frameConst = frameConst or uiconst.FRAME_BORDER1_CORNER0
        if len(frameConst) == 4:
            iconNo, cornerSize, offset, fillCenter = frameConst
            self.fillCenter = fillCenter
        else:
            iconNo, cornerSize, offset = frameConst
            self.fillCenter = True
        if 'ui_' in iconNo:
            resPath = iconNo.replace('ui_', 'res:/ui/texture/icons/') + '.png'
        else:
            resPath = iconNo
        self.SetTexturePath(resPath)
        self.cornerSize = cornerSize
        self.offset = offset

    def SetOffset(self, offset):
        self.offset = offset

    def GetOffset(self):
        return self.offset

    def SetCornerSize(self, cornerSize = 0):
        """
        Defines the pixel width and height of the frame corners
        """
        self.cornerSize = cornerSize

    def GetCornerSize(self):
        return self.cornerSize


class FrameCoreOverride(Frame):
    pass
