#Embedded file name: eve/client/script/ui/shared/radialMenu\rangeCircle.py
"""
    This file contains the code that makes range circle in the center of the radial menu.
"""
from carbonui.primitives.transform import Transform
import carbonui.const as uiconst
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.themeColored import SpriteThemeColored
import trinity
from carbon.common.script.util import mathUtil

class RangeCircle(Transform):
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED
    default_name = 'rangeCircle'

    def ApplyAttributes(self, attributes):
        Transform.ApplyAttributes(self, attributes)
        self.display = False
        rangeSize = attributes.rangeSize
        self.rangeMeterLeftSide = SpriteThemeColored(parent=self, name='rangeMeterLeftSide', pos=(0,
         0,
         rangeSize,
         rangeSize), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/RadialMenu/rangeMaskL.png', textureSecondaryPath='res:/UI/Texture/classes/RadialMenu/gaugeFill.png', colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.5, align=uiconst.CENTER, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE)
        self.rangeMeterLeftSide.display = True
        self.rangeMeterRightSide = SpriteThemeColored(parent=self, name='rangeMeterRightSide', pos=(0,
         0,
         rangeSize,
         rangeSize), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/RadialMenu/rangeMaskR.png', textureSecondaryPath='res:/UI/Texture/classes/RadialMenu/gaugeFill.png', colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.5, align=uiconst.CENTER, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE)
        self.rangeMeterRightSide.display = True
        self.rangeMeterFull = Sprite(parent=self, name='rangeMeterFull', pos=(0,
         0,
         rangeSize,
         rangeSize), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/RadialMenu/rangeShadow.png', align=uiconst.CENTER, color=(1.0, 1.0, 1.0, 0.4))

    def SetRangeCircle(self, degree, percOfAllRange):
        if percOfAllRange is None:
            self.rangeMeterRightSide.display = False
            self.rangeMeterLeftSide.display = False
            self.display = False
            return
        sm.GetService('audio').SetGlobalRTPC('radial_value', percOfAllRange)
        self.rangeMeterRightSide.display = True
        self.display = True
        self.rotation = mathUtil.DegToRad(-degree)
        halfCircle = 180
        changingDegree = halfCircle * (1 - percOfAllRange / 0.5)
        if changingDegree < 0:
            changingDegree += 360
        if percOfAllRange > 0.5:
            self.rangeMeterLeftSide.display = True
            self.rangeMeterRightSide.rotationSecondary = 0
            self.rangeMeterLeftSide.rotationSecondary = mathUtil.DegToRad(changingDegree)
        else:
            self.rangeMeterLeftSide.display = False
            self.rangeMeterRightSide.rotationSecondary = mathUtil.DegToRad(changingDegree)
            self.rangeMeterLeftSide.rotationSecondary = 0

    def AnimateFromCenter(self, curveSet, animationDuration, opacityRatio, grow, sleep = False):
        if grow:
            startOpacity = opacityRatio
            endOpacity = 1.0
        else:
            startOpacity = self.opacity
            endOpacity = opacityRatio
        uicore.animations.MorphScalar(self, 'opacity', startVal=startOpacity, endVal=endOpacity, duration=animationDuration, sleep=sleep, curveSet=curveSet)
