#Embedded file name: eve/client/script/ui/inflight/scannerFiles\pieCircle.py
import math
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.primitives.sprite import Sprite
import trinity

class PieCircle(Container):
    """
        A class for a cirlce that will visualize the degrees you are scanning
        It can very easily be moved and used by others, but until then it lives here
        where it's used
    """
    default_pieSize = 16
    default_align = uiconst.TOPLEFT
    default_circleTexture = 'res:/UI/Texture/classes/PieCircle/circle16.png'
    default_halfMaskTexture = 'res:/UI/Texture/classes/PieCircle/halfMask16.png'

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        setValue = attributes.get('setValue', None)
        self.circleTexture = attributes.get('circleTexture', self.default_circleTexture)
        self.halfMaskTexture = attributes.get('halfMaskTexture', self.default_halfMaskTexture)
        self.pieSize = attributes.get('size', self.default_pieSize)
        self.height = self.pieSize
        self.width = self.pieSize
        self.contentLeft = Container(parent=self, name='content', align=uiconst.TOPLEFT, pos=(0,
         0,
         self.pieSize / 2,
         self.pieSize), state=uiconst.UI_NORMAL, clipChildren=True)
        self.contentRight = Container(parent=self, name='contentRight', align=uiconst.TOPRIGHT, pos=(0,
         0,
         self.pieSize / 2,
         self.pieSize), state=uiconst.UI_NORMAL, clipChildren=True)
        self.halfCircleSpriteLeft = Sprite(name='halfCircleSpriteLeft', parent=self.contentLeft, pos=(0,
         0,
         self.pieSize,
         self.pieSize), texturePath=self.circleTexture, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, textureSecondaryPath=self.halfMaskTexture, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE)
        self.halfCircleSpriteLeft.rotationSecondary = math.pi
        self.halfCircleSpriteRight = Sprite(name='halfCircleSpriteRight', parent=self.contentRight, pos=(0,
         0,
         self.pieSize,
         self.pieSize), texturePath=self.circleTexture, state=uiconst.UI_DISABLED, align=uiconst.CENTERRIGHT, textureSecondaryPath=self.halfMaskTexture, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE)
        self.halfCircleSpriteRight.rotationSecondary = 0
        if setValue:
            self.SetDegree(setValue, animate=False)

    def SetDegree(self, degree, animate = True):
        halfRadians = math.pi / 180 * degree * 0.5
        leftValue = -math.pi + halfRadians
        rightValue = -halfRadians
        if animate:
            currentLeft = self.halfCircleSpriteLeft.rotationSecondary
            uicore.animations.MorphScalar(self.halfCircleSpriteLeft, 'rotationSecondary', startVal=currentLeft, endVal=leftValue, duration=0.25)
            currentRight = self.halfCircleSpriteRight.rotationSecondary
            uicore.animations.MorphScalar(self.halfCircleSpriteRight, 'rotationSecondary', startVal=currentRight, endVal=rightValue, duration=0.25)
        else:
            self.halfCircleSpriteLeft.rotationSecondary = leftValue
            self.halfCircleSpriteRight.rotationSecondary = rightValue
