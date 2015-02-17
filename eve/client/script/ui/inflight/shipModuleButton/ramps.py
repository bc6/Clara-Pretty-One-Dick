#Embedded file name: eve/client/script/ui/inflight/shipModuleButton\ramps.py
"""
    This file contains ramps for the ship module buttons
"""
import math
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
import carbonui.const as uiconst
import blue
from carbonui.primitives.vectorlinetrace import DashedCircle
import log

class ShipModuleButtonRamps(Container):
    default_height = 64
    default_width = 64
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_DISABLED
    default_opacity = 0.5

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        leftTexture = 'res:/UI/Texture/classes/ShipUI/slotRampLeft.png'
        leftRampCont = Container(parent=self, name='leftRampCont', pos=(0, 0, 32, 64), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.leftRamp = Transform(parent=leftRampCont, name='leftRamp', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        rampLeftSprite = Sprite(parent=self.leftRamp, name='rampLeftSprite', pos=(0, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath=leftTexture)
        self.leftShadowRamp = Transform(parent=leftRampCont, name='leftShadowRamp', pos=(0, 1, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_HIDDEN)
        shadow = Sprite(parent=self.leftShadowRamp, name='rampSprite', pos=(0, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath=leftTexture, color=(0, 0, 0, 1))
        rightTexture = 'res:/UI/Texture/classes/ShipUI/slotRampRight.png'
        rightRampCont = Container(parent=self, name='rightRampCont', pos=(32, 0, 32, 64), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.rightRamp = Transform(parent=rightRampCont, name='rightRamp', pos=(-32, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        rampRightSprite = Sprite(parent=self.rightRamp, name='rampRightSprite', pos=(32, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath=rightTexture)
        self.rightShadowRamp = Transform(parent=rightRampCont, name='rightShadowRamp', pos=(-32, 1, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_HIDDEN)
        shadow = Sprite(parent=self.rightShadowRamp, name='rampSprite', pos=(32, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath=rightTexture, color=(0, 0, 0, 1))
        self.display = False

    def SetRampValues(self, portionDone):
        self.SetRampUpValue(portionDone)
        self.SetRampDownValue(portionDone)

    def SetRampUpValue(self, portionDone):
        rampUpVal = min(1.0, max(0.0, portionDone * 2))
        newValue = math.pi * (1 - rampUpVal)
        self.leftRamp.SetRotation(newValue)
        self.leftShadowRamp.SetRotation(newValue)

    def SetRampDownValue(self, portionDone):
        rampDownVal = min(1.0, max(0.0, portionDone * 2 - 1.0))
        newValue = math.pi * (1 - rampDownVal)
        self.rightRamp.SetRotation(newValue)
        self.rightShadowRamp.SetRotation(newValue)
        if newValue == 1.0:
            self.rightRamp.SetRotation(math.pi)
            self.rightShadowRamp.SetRotation(math.pi)
            self.leftRamp.SetRotation(math.pi)
            self.leftShadowRamp.SetRotation(math.pi)

    def AnimateReload(self, startTime, repairTime):
        self.SetRampValues(1)
        percentageDone = 0
        while self and not self.destroyed and percentageDone < 1:
            newNow = blue.os.GetSimTime()
            percentageDone = (newNow - startTime) / float(repairTime)
            self.SetRampValues(1 - percentageDone)
            self.display = True
            blue.pyos.synchro.Yield()


class DamageStateCont(Container):
    size = 64
    default_height = size
    default_width = size
    default_top = 0
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_HIDDEN
    default_opacity = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.isBeingRepaired = False
        self.endTime = None
        leftRampCont = Container(parent=self, name='leftRampCont', pos=(0,
         0,
         self.size / 2,
         self.size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.leftRamp = Sprite(parent=leftRampCont, align=uiconst.TOPLEFT, width=self.size, height=self.size, texturePath='res:\\UI\\Texture\\classes\\ShipUI\\slotDamage_Base.png', textureSecondaryPath='res:\\UI\\Texture\\classes\\PieCircle\\halfMask32.png', blendMode=1, spriteEffect=64)
        rightRampCont = Container(parent=self, name='rightRampCont', pos=(self.size / 2,
         0,
         self.size / 2,
         self.size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.rightRamp = Sprite(parent=rightRampCont, align=uiconst.TOPRIGHT, width=self.size, height=self.size, texturePath='res:\\UI\\Texture\\classes\\ShipUI\\slotDamage_Base.png', textureSecondaryPath='res:\\UI\\Texture\\classes\\PieCircle\\halfMask32.png', blendMode=1, spriteEffect=64)

    def SetLeftRampValue(self, hpPercentage):
        hpPercentage = min(1.0, max(0.5, hpPercentage))
        self.leftRamp.rotationSecondary = -0.8 * (2 * hpPercentage - 1) * math.pi

    def SetRightRampValue(self, hpPercentage):
        hpPercentage = max(0, min(0.5, hpPercentage))
        self.rightRamp.rotationSecondary = 0.8 * (1 - 2 * hpPercentage) * math.pi

    def SetRampValues(self, hpPercentage):
        self.leftRamp.spriteEffect = 64
        self.rightRamp.spriteEffect = 64
        self.SetLeftRampValue(hpPercentage)
        self.SetRightRampValue(hpPercentage)

    def SetDamage(self, damage):
        imageIndex = max(1, int(damage * 8))
        texturePath = 'res:/UI/Texture/classes/ShipUI/slotDamage_%s.png' % imageIndex
        self.leftRamp.SetTexturePath(texturePath)
        self.rightRamp.SetTexturePath(texturePath)
        self.leftRamp.spriteEffect = 32
        self.rightRamp.spriteEffect = 32

    def Blink(self, damageAmount):
        for ramp in (self.rightRamp, self.leftRamp):
            sm.GetService('ui').BlinkSpriteA(ramp, 1.0, 2000 - 1000 * damageAmount, 2, passColor=0)

    def AnimateRepair(self, dmg, hp, repairTime, startTime):
        if not repairTime:
            return
        self.isBeingRepaired = True
        self.endTime = repairTime + startTime
        while self and not self.destroyed and self.isBeingRepaired:
            newNow = blue.os.GetSimTime()
            percentageDone = (newNow - startTime) / float(repairTime)
            damageLeft = 1 - percentageDone
            hpPercentage = (hp - dmg * damageLeft) / hp
            self.SetRampValues(hpPercentage)
            blue.pyos.synchro.Yield()

        self.endTime = None

    def StopRepair(self):
        self.isBeingRepaired = False


class ShipModuleReactivationTimer(Container):
    default_height = 50
    default_width = 50
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        size = self.width
        if self.width != self.height:
            log.LogTraceback("ShipModuleReactivationTimer don't have width and height as the same value")
        maskSize = round(size * 1.28)
        Sprite(parent=self, name='maskSprite', align=uiconst.CENTER, pos=(0,
         0,
         maskSize,
         maskSize), texturePath='res:/UI/Texture/classes/ShipUI/slotSolidBackground.png', color=(0, 0, 0, 1))
        gaugeRadius = self.height / 2 - 3
        self.gauge = DashedCircle(parent=self, dashCount=18, dashSizeFactor=4.0, range=math.pi * 2, lineWidth=6, radius=gaugeRadius, startAngle=math.pi / 2, startColor=(1, 1, 1, 0.3), endColor=(1, 1, 1, 0.3))
        self.endTime = None

    def AnimateTimer(self, startTime, repairTime):
        percentageDone = 0
        self.end = 1
        self.endTime = startTime + repairTime
        uicore.animations.MorphScalar(self.gauge, 'opacity', startVal=1.0, endVal=0.6, duration=1.5, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_BOUNCE)
        while self and not self.destroyed and percentageDone < 1:
            newNow = blue.os.GetSimTime()
            percentageDone = (newNow - startTime) / float(repairTime)
            self.gauge.end = 1 - percentageDone
            self.display = True
            blue.pyos.synchro.Yield()

        self.endTime = None
        self.gauge.StopAnimations()
