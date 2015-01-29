#Embedded file name: eve/client/script/ui/control\countdownTimer.py
from math import pi
from carbonui.primitives import container
from carbonui.primitives import transform
from carbonui.primitives import sprite
from carbonui import const as uiconst
import uthread
import blue
import trinity
ALPHA_EMPTY = 0.2
BLINK_BEFORE_DONE_TIME = const.SEC * 5
REWIND_SPEED = 500
TEXT_OFFSET = -17
TIMER_RUNNING_OUT_NO_ANIMATION = 1
TIMER_RUNNING_OUT_BLINK_ALL = 2
TIMER_RUNNING_OUT_BLINK_ICON = 4

def FormatCounterTime(timeLeft):
    """Format time left in 00:00 format or 00:00:00 if time is hours"""
    timeLeft = max(0, timeLeft / const.SEC)
    minutes, seconds = divmod(timeLeft, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return '%02d:%02d:%02d' % (hours, minutes, seconds)
    else:
        return '%02d:%02d' % (minutes, seconds)


class CountdownTimer(container.Container):
    default_width = 32
    default_height = 32
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED
    sound_loop_play_event = None
    sound_loop_stop_event = None

    def ApplyAttributes(self, attributes):
        container.Container.ApplyAttributes(self, attributes)
        self.SetupVariables(attributes)
        self.CreateMainContentLayout()
        self.CreateIconLayout(attributes)
        self.CreateTimerCycleLayout()
        self.SetTimerColor(self.color)
        self.SetExpiryTime(None, 0.0)
        self.PlayEntryAnimation()

    def SetupVariables(self, attributes):
        self.countsDown = attributes.Get('countsDown', False)
        self.GetTime = attributes.Get('timerFunc', blue.os.GetSimTime)
        self.color = attributes.Get('color', (1, 1, 1, 1))
        self.maxTimeout = attributes.maxTimeout
        self.resetAudioEvent = attributes.Get('resetAudioEvent', None)
        self.endingAudioEvent = attributes.Get('endingAudioEvent', None)
        self.timerRunningOutAnimation = attributes.Get('timerRunningOutAnimation', TIMER_RUNNING_OUT_BLINK_ICON)
        self.icon = None
        self.iconBlink = None
        self.rewind = False
        self.ratio = 1.0
        self.animationThread = None
        self.activeAnimationCurves = None

    def CreateMainContentLayout(self):
        self.content = transform.Transform(parent=self, name='content', align=uiconst.CENTER, pos=(0, 0, 32, 32), state=uiconst.UI_NORMAL)
        self.content.OnMouseEnter = self.OnMouseEnter

    def CreateIconLayout(self, attributes):
        if attributes.icon:
            self.iconTransform = transform.Transform(parent=self.content, name='iconTransform', align=uiconst.CENTER, width=16, height=16, state=uiconst.UI_DISABLED)
            self.icon = sprite.Sprite(name='icon', parent=self.iconTransform, pos=(0, 0, 16, 16), texturePath=attributes.icon, state=uiconst.UI_DISABLED, align=uiconst.CENTER)
            self.iconTransform.scalingCenter = (0.5, 0.5)
        else:
            self.icon = None

    def CreateTimerCycleLayout(self):
        self.circleSprite = sprite.Sprite(name='icon', parent=self.content, pos=(0, 0, 32, 32), texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerCircle.png', state=uiconst.UI_DISABLED, align=uiconst.CENTER, opacity=ALPHA_EMPTY)
        self.halfCircleSprite = sprite.Sprite(name='half_circle', parent=self.content, width=32, height=32, rotation=0 if self.countsDown else pi, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerHalfCircle.png', state=uiconst.UI_DISABLED)
        self.clipContainer = container.Container(name='clipper', parent=self.content, width=16, align=uiconst.TOLEFT, clipChildren=True, state=uiconst.UI_DISABLED)
        self.cycleContainer = transform.Transform(name='cycle_container', parent=self.clipContainer, width=32, height=32)
        self.cycleSprite = sprite.Sprite(name='cycle_half_circle', parent=self.cycleContainer, width=32, height=32, rotation=pi if self.countsDown else 0, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerHalfCircle.png', state=uiconst.UI_DISABLED)
        self.pointerContainer = transform.Transform(name='pointer_container', parent=self.content, width=32, height=32, idx=0)
        self.pointerClipper = container.Container(parent=self.pointerContainer, pos=(9, -10, 15, 13), clipChildren=True, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        self.pointerSprite = sprite.Sprite(name='cycle_pointer', parent=self.pointerClipper, pos=(0, 0, 15, 19), texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerPoint_WithShadow.png', align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)

    def PlayEntryAnimation(self):
        uicore.animations.FadeIn(self, duration=0.25, endVal=1.0)
        if self.icon:
            uicore.animations.Tr2DScaleTo(self.iconTransform, startScale=(0.8, 0.8), endScale=(1.0, 1.0), duration=0.75, curveType=uiconst.ANIM_OVERSHOT)

    def SetTimerColor(self, color):
        r, g, b, a = color
        self.circleSprite.color.SetRGB(r, g, b, 0.5)
        self.halfCircleSprite.SetRGB(r, g, b, a)
        self.cycleSprite.color.SetRGB(r, g, b, a)
        self.pointerSprite.color.SetRGB(r, g, b, a)
        if self.icon:
            self.icon.color.SetRGB(r, g, b, a)

    def SetRatio(self, ratio):
        """Set the cycle timer ratio for 0 <= timeout to 1 <= full time"""
        self.ratio = min(1.0, max(0.0, ratio))
        if self.ratio > 0.5:
            self.clipContainer.SetAlign(uiconst.TORIGHT)
            self.cycleContainer.left = -16
            self.halfCircleSprite.display = True if self.countsDown else False
        else:
            self.clipContainer.SetAlign(uiconst.TOLEFT)
            self.cycleContainer.left = 0
            self.halfCircleSprite.display = False if self.countsDown else True
        rotation = 2 * pi * self.ratio
        self.pointerContainer.rotation = rotation
        self.cycleContainer.rotation = rotation

    def SetExpiryTime(self, timerExpiryTime, timerDuration, doAlert = False):
        self.Reset(timerExpiryTime, timerDuration, doAlert)
        if timerExpiryTime is None:
            self.PlayActiveAnimation()
        else:
            self.animationThread = uthread.new(self.Animate_Thread, timerExpiryTime, timerDuration)

    def Reset(self, resetTo, timerDuration, doAlert):
        """Animate back to full time"""
        if self.animationThread is not None:
            self.animationThread.kill()
        uthread.new(self.Rewind_Thread, resetTo, timerDuration, doAlert)

    def Rewind_Thread(self, resetTo, timerDuration, doAlert):
        if self.rewind:
            return
        if doAlert and self.resetAudioEvent:
            sm.GetService('audio').SendUIEvent(self.resetAudioEvent)
        self.rewind = True
        ratio = self.ratio
        startTime = self.GetTime()
        distance = 1 - ratio
        cycleSpeed = float(distance * REWIND_SPEED)
        while not self.destroyed and cycleSpeed > 0:
            if resetTo is not None:
                resetRatio = self.GetRatio(resetTo - self.GetTime(), timerDuration)
                if self.ratio >= resetRatio:
                    break
            elapsedTime = blue.os.TimeDiffInMs(startTime, self.GetTime())
            toAdd = elapsedTime / cycleSpeed
            self.SetRatio(ratio + toAdd)
            blue.pyos.synchro.SleepWallclock(25)

        self.rewind = False

    def FlipFlop(self, sprite, duration = 1.0, startValue = 0.0, endValue = 1.0, loops = 5):
        curve = trinity.Tr2ScalarCurve()
        curve.length = duration
        curve.interpolation = trinity.TR2CURVE_LINEAR
        curve.startValue = startValue
        curve.AddKey(0.01 * duration, endValue)
        curve.AddKey(0.5 * duration, endValue)
        curve.AddKey(0.51 * duration, startValue)
        curve.endValue = startValue
        return uicore.animations.Play(curve, sprite, 'opacity', loops, None, False)

    def GetRatio(self, timeLeft, duration):
        ratio = timeLeft / float(duration)
        ratio = min(1.0, max(0.0, ratio))
        return ratio

    def Animate_Thread(self, expiryTime, duration):
        self.StopActiveAnimation()
        self.StartSoundLoop()
        while not self.destroyed and expiryTime is not None:
            if not self.rewind:
                if self.ratio <= 0.0:
                    break
                timeLeft = expiryTime - self.GetTime()
                ratio = self.GetRatio(timeLeft, duration)
                self.SetRatio(ratio)
                if timeLeft < BLINK_BEFORE_DONE_TIME:
                    self.PlayTimerRunningOutAnimation()
                else:
                    self.StopTimerRunningOutAnimation()
            blue.pyos.synchro.SleepWallclock(50)

        self.StopActiveAnimation()
        self.StopSoundLoop()

    def PlayTimerRunningOutAnimation(self):
        if self.timerRunningOutAnimation == TIMER_RUNNING_OUT_NO_ANIMATION:
            return
        if self.iconBlink is not None:
            return
        if self.timerRunningOutAnimation == TIMER_RUNNING_OUT_BLINK_ICON:
            animationSprite = self.icon
        else:
            animationSprite = self.content
        self.iconBlink = self.FlipFlop(animationSprite, startValue=1.0, endValue=0.0)
        if self.endingAudioEvent:
            sm.GetService('audio').SendUIEvent(self.endingAudioEvent)

    def StopTimerRunningOutAnimation(self):
        if self.iconBlink is not None:
            self.iconBlink.Stop()
            self.iconBlink = None

    def EndAnimation(self):
        self.SetRatio(0.0)
        uicore.animations.FadeOut(self, duration=0.5, timeOffset=0.5)
        uicore.animations.MoveOutBottom(self.pointerSprite, amount=9, duration=0.3, sleep=False)
        self.content.scalingCenter = (0.5, 0.5)
        uicore.animations.Tr2DScaleTo(self.content, startScale=(1.0, 1.0), endScale=(0.8, 0.8), duration=0.4, sleep=True)

    def PlayActiveAnimation(self):
        self.activeAnimationCurves = ((self.halfCircleSprite, self.FlipFlop(self.halfCircleSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)), (self.cycleSprite, self.FlipFlop(self.cycleSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)), (self.pointerSprite, self.FlipFlop(self.pointerSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)))

    def StopActiveAnimation(self):
        if self.activeAnimationCurves is not None:
            for sprite, animationCurve in self.activeAnimationCurves:
                animationCurve.Stop()
                sprite.opacity = 1.0

            self.activeAnimationCurves = None

    def SetSoundLoop(self, playEvent, stopEvent):
        self.sound_loop_play_event = playEvent
        self.sound_loop_stop_event = stopEvent

    def StartSoundLoop(self):
        if self.sound_loop_play_event is not None:
            sm.GetService('audio').SendUIEvent(self.sound_loop_play_event)

    def StopSoundLoop(self):
        if self.sound_loop_stop_event is not None:
            sm.GetService('audio').SendUIEvent(self.sound_loop_stop_event)
