#Embedded file name: eve/client/script/ui/hacking\hackingVirusInfo.py
import carbonui.const as uiconst
import uiprimitives
import util
import localization
import random
import hackingcommon.hackingConstants as hackingConst
import hackingUIConst
from eve.client.script.ui.hacking.hackingStatContainer import StatContainer
import uthread
import blue
from math import pi
import trinity

class VirusInfo(uiprimitives.Container):
    __guid__ = 'hackingui.VirusInfo'
    __notifyevents__ = ['OnHackingVirusChanged']
    default_align = uiconst.BOTTOMLEFT
    default_state = uiconst.UI_NORMAL
    default_width = 123
    default_height = 95

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.strength = None
        self.coherence = None
        self.iconSprite = uiprimitives.Sprite(name='virusIconSprite', texturePath='res:/UI/Texture/classes/hacking/hudIcon.png', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, pos=(0, 0, 59, 44))
        self.coherenceBar = VirusInfoBar(parent=self, align=uiconst.CENTERLEFT, color=hackingUIConst.COLOR_HUD_BAR_COHERENCE)
        self.strengthBar = VirusInfoBar(parent=self, align=uiconst.CENTERRIGHT, color=hackingUIConst.COLOR_HUD_BAR_STRENGTH, mirrored=True)
        self.strengthCont = StatContainer(name='strengthCont', parent=self, statType=hackingUIConst.STAT_STRENGTH, align=uiconst.CENTERBOTTOM, state=uiconst.UI_NORMAL, top=4, hint=localization.GetByLabel('UI/Hacking/VirusStrength'))
        self.coherenceCont = StatContainer(name='coherencesCont', parent=self, statType=hackingUIConst.STAT_COHERENCE, align=uiconst.CENTERTOP, state=uiconst.UI_NORMAL, top=4, hint=localization.GetByLabel('UI/Hacking/VirusCoherence'))
        uiprimitives.Sprite(name='bg', parent=self, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/hacking/hudBG.png')
        noiseData = ('res:/UI/Texture/Classes/hacking/hudNoise1.png', 'res:/UI/Texture/Classes/hacking/hudNoise2.png', 'res:/UI/Texture/Classes/hacking/hudNoise3.png', 'res:/UI/Texture/Classes/hacking/hudNoise4.png')
        self.noiseSprites = []
        for num, texturePath in enumerate(noiseData):
            noise = HudNoise(parent=self, texturePath=texturePath, width=self.width, height=self.height, num=num)
            self.noiseSprites.append(noise)

        self.iconBG = uiprimitives.Sprite(name='iconBG', texturePath='res:/UI/Texture/classes/hacking/hudIconBG.png', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, pos=(0, 0, 118, 118), opacity=0.0)
        self.animateIconThread = None
        self.AnimateIconBG()

    def SetIntensity(self, value):
        for noise in self.noiseSprites:
            noise.SetIntensity(value)

    def AnimateIconBG(self):
        if self.animateIconThread:
            self.animateIconThread.kill()
        self.animateIconThread = uthread.new(self._AnimateIconBG)

    def _AnimateIconBG(self):
        color = util.Color(*hackingUIConst.COLOR_DATACACHE).SetAlpha(0.5).GetRGBA()
        uicore.animations.SpColorMorphTo(self.iconBG, self.iconBG.GetRGBA(), color, duration=1.0, callback=self.AnimateIconBG, sleep=True)
        if self.animateIconThread:
            self.animateIconThread.kill()
        uicore.animations.FadeTo(self.iconBG, 0.5, 0.85, duration=5.0, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)

    def OnHackingVirusChanged(self, objectData, eventID):
        if eventID == hackingConst.EVENT_ATTACK:
            blue.synchro.Sleep(300)
        self.UpdateVirusInfo()

    def UpdateVirusInfo(self):
        strength, coherence = sm.GetService('hackingUI').GetVirusStrengthAndCoherence()
        if self.coherence is None:
            self.coherenceBar.SetMaxValue(4.0 / 3.0 * coherence)
        if self.strength is None:
            self.strengthBar.SetMaxValue(2.0 * strength)
        if self.coherence and coherence < self.coherence:
            uicore.animations.BlinkIn(self.iconSprite, loops=1, duration=0.15)
            self.iconBG.opacity = 1.0
            if self.animateIconThread:
                self.animateIconThread.kill()
            uicore.animations.SpColorMorphTo(self.iconBG, util.Color.WHITE, (0, 0, 0, 0), duration=0.6, callback=self.AnimateIconBG)
        self.coherenceCont.SetValue(coherence)
        self.strengthCont.SetValue(strength)
        self.coherenceBar.SetValue(coherence)
        self.strengthBar.SetValue(strength)
        if self.coherence > hackingUIConst.LOW_COHERENCE_WARN_LEVEL and coherence < hackingUIConst.LOW_COHERENCE_WARN_LEVEL:
            sm.GetService('audio').SendUIEvent('minigame_coherence_low_start')
        elif self.coherence < hackingUIConst.LOW_COHERENCE_WARN_LEVEL and coherence > hackingUIConst.LOW_COHERENCE_WARN_LEVEL:
            sm.GetService('audio').SendUIEvent('minigame_coherence_low_stop')
        self.coherence = coherence
        self.strength = strength


class VirusInfoBar(uiprimitives.Container):
    __guid__ = 'hackingui.VirusInfoBar'
    default_mirrored = False
    default_width = 24
    default_height = 71
    default_left = 4
    default_state = uiconst.UI_NORMAL
    default_maxValue = 1.0

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        mirrored = attributes.get('mirrored', self.default_mirrored)
        self.color = attributes.color
        self.maxValue = float(attributes.get('maxValue', self.default_maxValue))
        self.value = 0
        stripeTexturePath = 'res:/UI/Texture/classes/hacking/hudBarStripesMirrored.png' if mirrored else 'res:/UI/Texture/classes/hacking/hudBarStripes.png'
        fillTexturePath = 'res:/UI/Texture/classes/hacking/hudBarFillMirrored.png' if mirrored else 'res:/UI/Texture/classes/hacking/hudBarFill.png'
        self.hint = localization.GetByLabel('UI/Hacking/VirusStrength') if mirrored else localization.GetByLabel('UI/Hacking/VirusCoherence')
        self.bar = uiprimitives.Container(name='bar', parent=self, align=uiconst.TOBOTTOM_PROP, state=uiconst.UI_DISABLED, height=0.0, clipChildren=True)
        self.barTexture = uiprimitives.Sprite(name='barTexture', parent=self.bar, align=uiconst.CENTERBOTTOM, width=self.width, height=self.height, texturePath=fillTexturePath, textureSecondaryPath=stripeTexturePath, spriteEffect=trinity.TR2_SFX_MODULATE, color=self.color)
        self.bg = uiprimitives.Sprite(name='bg', bgParent=self, texturePath=fillTexturePath, color=hackingUIConst.COLOR_HUD_BAR_BG, textureSecondaryPath=stripeTexturePath, spriteEffect=trinity.TR2_SFX_MODULATE)

    def SetMaxValue(self, value):
        self.maxValue = float(value)

    def SetValue(self, value):
        if value == self.value:
            return
        uicore.animations.MorphScalar(self.bar, 'height', self.bar.height, value / self.maxValue, duration=0.6)
        color = util.Color(*self.color).SetBrightness(1.0).GetRGBA()
        uicore.animations.SpColorMorphTo(self.barTexture, color, self.barTexture.GetRGBA(), duration=0.6)
        self.value = value


class HudNoise(uiprimitives.Transform):
    __guid__ = 'hackingui.HudNoise'
    default_align = uiconst.CENTER
    default_scalingCenter = (0.5, 0.5)
    default_opacity = 0.0
    COLOR = util.Color.WHITE

    def ApplyAttributes(self, attributes):
        uiprimitives.Transform.ApplyAttributes(self, attributes)
        texturePath = attributes.texturePath
        num = attributes.num
        self.intensity = 1.0
        self.sprite = uiprimitives.Sprite(bgParent=self, texturePath=texturePath)
        uthread.new(self.Animate, num)

    def Animate(self, num):
        blue.synchro.SleepWallclock(num * 800)
        while not self.destroyed:
            duration = 5.0 * self.intensity
            color = util.Color(*hackingUIConst.COLOR_EXPLORED).SetAlpha(0.1 + 0.4 * random.random()).GetRGBA()
            self.sprite.SetRGB(*color)
            self.rotation = random.choice((0, pi))
            uicore.animations.Tr2DRotateTo(self, self.rotation, self.rotation + random.choice((0.05, -0.05)), duration=duration)
            uicore.animations.Tr2DScaleTo(self, (0.9, 0.9), (1.0, 1.0), duration=duration)
            uicore.animations.FadeTo(self, 0.0, 1.0, duration=duration, curveType=uiconst.ANIM_WAVE)
            x = 0.5 * random.random() - 0.4 * self.intensity + 0.5
            sleepTime = duration * (0.2 + 0.8 * x)
            blue.synchro.SleepWallclock(sleepTime * 1000)
            self.StopAnimations()
            uicore.animations.BlinkOut(self)
            blue.synchro.SleepWallclock(1000)

    def SetIntensity(self, value):
        self.intensity = value
