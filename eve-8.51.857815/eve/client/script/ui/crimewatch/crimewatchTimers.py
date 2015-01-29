#Embedded file name: eve/client/script/ui/crimewatch\crimewatchTimers.py
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import collections
import blue
import uthread
import trinity
from math import pi
from crimewatchConst import Colors
from eve.client.script.ui.crimewatch.crimewatchHints import TimerHint, EngagementTimerHint, BoosterTimerHint, JumpTimerHint
ALPHA_EMPTY = 0.2
BLINK_BEFORE_DONE_TIME = const.SEC * 5
TimerData = collections.namedtuple('TimerData', 'icon smallIcon color tooltip maxTimeout resetAudioEvent endingAudioEvent timerFunc')

class TimerType():
    __guid__ = 'crimewatchTimers.TimerType'
    Weapons = 0
    Npc = 1
    Pvp = 2
    Suspect = 3
    Criminal = 4
    Engagement = 5
    Booster = 6
    JumpActivation = 7
    JumpFatigue = 8


TIMER_ATTRIBUTE_NAMES_BY_TIMER_TYPE = {TimerType.Weapons: 'weaponsTimer',
 TimerType.Npc: 'npcTimer',
 TimerType.Pvp: 'pvpTimer',
 TimerType.Suspect: 'criminalTimer',
 TimerType.Criminal: 'criminalTimer',
 TimerType.Engagement: 'engagementTimer',
 TimerType.Booster: 'boosterTimer',
 TimerType.JumpActivation: 'jumpActivationTimer',
 TimerType.JumpFatigue: 'jumpFatigueTimer'}
CRIMEWATCH_TIMER_DATA = [TimerData('res:/UI/Texture/Crimewatch/Crimewatch_Locked.png', 'res:/UI/Texture/Crimewatch/Crimewatch_Locked_Small.png', Colors.Red.GetRGBA(), 'UI/Crimewatch/Timers/WeaponsTimerTooltip', const.weaponsTimerTimeout, 'wise:/crimewatch_weapons_timer_play', 'wise:/crimewatch_weapons_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_Combat.png', 'res:/UI/Texture/Crimewatch/Crimewatch_Combat_Small.png', Colors.Yellow.GetRGBA(), 'UI/Crimewatch/Timers/PveTimerTooltip', const.npcTimerTimeout, 'wise:/crimewatch_log_off_timer_new_play', 'wise:/crimewatch_log_off_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_Combat.png', 'res:/UI/Texture/Crimewatch/Crimewatch_Combat_Small.png', Colors.Red.GetRGBA(), 'UI/Crimewatch/Timers/PvpTimerTooltiip', const.pvpTimerTimeout, 'wise:/crimewatch_log_off_timer_new_play', 'wise:/crimewatch_log_off_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png', 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal_Small.png', Colors.Suspect.GetRGBA(), 'UI/Crimewatch/Timers/SuspectTimerTooltip', const.criminalTimerTimeout, 'wise:/crimewatch_criminal_timer_play', 'wise:/crimewatch_criminal_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png', 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal_Small.png', Colors.Criminal.GetRGBA(), 'UI/Crimewatch/Timers/CriminalTimerTooltip', const.criminalTimerTimeout, 'wise:/crimewatch_criminal_timer_play', 'wise:/crimewatch_criminal_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_LimitedEngagement.png', None, Colors.Engagement.GetRGBA(), None, const.crimewatchEngagementDuration, 'wise:/crimewatch_engagement_timer_play', 'wise:/crimewatch_engagement_timer_end_play', blue.os.GetWallclockTime),
 TimerData('res:/UI/Texture/Crimewatch/booster.png', None, Colors.Boosters.GetRGBA(), None, const.crimewatchEngagementDuration, 'wise:/boostertimer_timerstart_play', 'wise:/boostertimer_timerend_play', blue.os.GetWallclockTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_JumpActivation.png', None, (0.945,
  0.353,
  0.141,
  1.0), 'UI/Crimewatch/Timers/JumpActivationTooltip', 1, 'wise:/jump_activation_timer_play', 'wise:/jump_activation_timer_end_play', blue.os.GetWallclockTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_JumpFatigue.png', None, (0.0,
  1.0,
  1.0,
  1.0), 'UI/Crimewatch/Timers/JumpFatigueTooltip', 1, 'wise:/jump_fatigue_timer_play', 'wise:/jump_fatigue_timer_end_play', blue.os.GetWallclockTime)]

class Timer(uiprimitives.Container):
    """
    This is a crimewatch timer used for:
        PVx timer
        criminal timer
        weapon timer
    They differ in center icon, color and text and duration
    The share all other behavior and share the same UI space
    """
    __guid__ = 'crimewatchTimers.Timer'
    default_width = 46
    default_align = uiconst.TOLEFT
    default_hintClass = TimerHint

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.hintClass = attributes.get('hintClass', self.default_hintClass)
        self.state = uiconst.UI_PICKCHILDREN
        self.timerHint = None
        self.showHint = False
        self.expiryTime = None
        self.iconBlink = None
        self.rewind = False
        self.ratio = 0.0
        self.counterText = None
        self.animationThread = None
        self.timerType = attributes.Get('timerType')
        self.timerData = attributes.get('timerData', CRIMEWATCH_TIMER_DATA[attributes.Get('timerType')])
        self.GetTime = self.timerData.timerFunc
        self.activeAnimationCurves = None
        self.callback = attributes.get('callback', None)
        self.content = uiprimitives.Transform(parent=self, name='content', align=uiconst.TOPLEFT, pos=(0, 0, 32, 32), state=uiconst.UI_NORMAL)
        self.circleSprite = uiprimitives.Sprite(name='icon', parent=self.content, pos=(0, 0, 32, 32), texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerCircle.png', color=self.timerData.color, state=uiconst.UI_DISABLED, align=uiconst.CENTER, opacity=ALPHA_EMPTY)
        self.content.OnMouseEnter = self.OnMouseEnter
        self.iconTransform = uiprimitives.Transform(parent=self.content, name='iconTransform', align=uiconst.CENTER, width=16, height=16, state=uiconst.UI_DISABLED)
        self.icon = uiprimitives.Sprite(name='icon', parent=self.iconTransform, pos=(0, 0, 16, 16), texturePath=self.timerData.icon, color=self.timerData.color, state=uiconst.UI_DISABLED, align=uiconst.CENTER)
        self.halfCircleSprite = uiprimitives.Sprite(name='half_circle', parent=self.content, width=32, height=32, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerHalfCircle.png', color=self.timerData.color, state=uiconst.UI_DISABLED)
        self.clipContainer = uiprimitives.Container(name='clipper', parent=self.content, width=16, align=uiconst.TOLEFT, clipChildren=True, state=uiconst.UI_DISABLED)
        self.cycleContainer = uiprimitives.Transform(name='cycle_container', parent=self.clipContainer, width=32, height=32)
        self.cycleSprite = uiprimitives.Sprite(name='cycle_half_circle', parent=self.cycleContainer, width=32, height=32, rotation=pi, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerHalfCircle.png', color=self.timerData.color, state=uiconst.UI_DISABLED)
        self.pointerContainer = uiprimitives.Transform(name='pointer_container', parent=self.content, width=32, height=32, idx=0)
        self.pointerClipper = uiprimitives.Container(parent=self.pointerContainer, pos=(9, -10, 15, 13), clipChildren=True, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        self.pointerSprite = uiprimitives.Sprite(name='cycle_pointer', parent=self.pointerClipper, pos=(0, 0, 15, 19), texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerPoint_WithShadow.png', color=self.timerData.color, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        self.iconTransform.scalingCenter = (0.5, 0.5)
        uicore.animations.Tr2DScaleTo(self.iconTransform, startScale=(0.8, 0.8), endScale=(1.0, 1.0), duration=0.75, curveType=uiconst.ANIM_OVERSHOT)

    def SetTimerType(self, timerType):
        self.timerData = CRIMEWATCH_TIMER_DATA[timerType]
        r, g, b, a = self.timerData.color
        self.icon.color.SetRGB(r, g, b, a)
        self.circleSprite.color.SetRGB(r, g, b, ALPHA_EMPTY)
        self.halfCircleSprite.SetRGB(r, g, b, a)
        self.cycleSprite.color.SetRGB(r, g, b, a)
        self.pointerSprite.color.SetRGB(r, g, b, a)

    def SetRatio(self, ratio):
        """Set the cycle timer ratio for 0 <= timout to 1 <= full time"""
        self.ratio = min(1.0, max(0.0, ratio))
        if self.ratio > 0.5:
            self.clipContainer.SetAlign(uiconst.TORIGHT)
            self.cycleContainer.left = -16
            self.halfCircleSprite.display = True
        else:
            self.clipContainer.SetAlign(uiconst.TOLEFT)
            self.cycleContainer.left = 0
            self.halfCircleSprite.display = False
        rotation = min(pi * 2, 2 * pi * self.ratio)
        self.pointerContainer.rotation = rotation
        self.cycleContainer.rotation = rotation

    def SetExpiryTime(self, expiryTime, doAlert, maxDuration = None):
        self.Reset(expiryTime, doAlert, maxDuration=maxDuration)
        self.expiryTime = expiryTime
        if expiryTime is None:
            self.PlayActiveAnimation()
        else:
            self.animationThread = uthread.new(self.Animate_Thread)

    def Reset(self, resetTo, doAlert, maxDuration = None):
        """Animate back to full time"""
        if self.animationThread is not None:
            self.animationThread.kill()
        if maxDuration and maxDuration != self.timerData.maxTimeout:
            self.timerData = self.timerData._replace(maxTimeout=maxDuration)
        uthread.new(self.Rewind_Thread, resetTo, doAlert)

    def Rewind_Thread(self, resetTo, doAlert):
        if self.rewind:
            return
        if doAlert and self.timerData.resetAudioEvent is not None:
            sm.GetService('audio').SendUIEvent(self.timerData.resetAudioEvent)
        self.rewind = True
        ratio = self.ratio
        startTime = self.GetTime()
        distance = 1 - ratio
        cycleSpeed = float(distance * 500)
        while not self.destroyed and self.ratio < (self.GetRatio(resetTo - self.GetTime()) if resetTo is not None else 1.0):
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

    def GetRatio(self, timeLeft):
        ratio = timeLeft / float(self.timerData.maxTimeout)
        ratio = min(1.0, max(0.0, ratio))
        return ratio

    def Animate_Thread(self):
        self.StopActiveAnimation()
        while not self.destroyed and self.expiryTime is not None:
            if not self.rewind:
                if self.ratio <= 0.0:
                    break
                timeLeft = self.expiryTime - self.GetTime()
                ratio = self.GetRatio(timeLeft)
                self.SetRatio(ratio)
                if timeLeft < BLINK_BEFORE_DONE_TIME:
                    self.PlayIconBlink()
                else:
                    self.StopIconBlink()
            blue.pyos.synchro.SleepWallclock(50)

        if self.callback:
            self.callback(self)

    def PlayIconBlink(self):
        if self.iconBlink is None:
            self.iconBlink = self.FlipFlop(self.icon, startValue=1.0, endValue=0.0)
            if self.timerData.endingAudioEvent:
                sm.GetService('audio').SendUIEvent(self.timerData.endingAudioEvent)

    def StopIconBlink(self):
        if self.iconBlink is not None:
            self.iconBlink.Stop()
            self.iconBlink = None
            self.icon.opacity = 1.0

    def EndAnimation(self):
        self.SetRatio(0.0)
        uicore.animations.MoveOutBottom(self.pointerSprite, amount=9, duration=0.3, sleep=False)
        self.content.scalingCenter = (0.5, 0.5)
        uicore.animations.Tr2DScaleTo(self.content, startScale=(1.0, 1.0), endScale=(0.8, 0.8), duration=0.4, sleep=True)

    def OnMouseEnter(self, *args):
        uthread.new(self.ShowHide)

    def ShowHide(self):
        blue.pyos.synchro.SleepWallclock(250)
        if uicore.uilib.mouseOver is self.content:
            self.showHint = True
            if self.timerHint is None:
                left, top, width, height = self.content.GetAbsolute()
                self.timerHint = self.hintClass(parent=uicore.layer.abovemain, left=left + 16, top=top + 16, timerData=self.timerData, parentTimer=self)

    def ShiftLeft(self):
        uicore.animations.MoveInFromRight(self, self.width, duration=0.5)

    def SetCounter(self, count):
        """
        Set a special counter giving use for number of engagements
        """
        if count is None or count <= 1:
            if self.counterText is not None:
                self.counterText.Close()
                self.counterText = None
        else:
            if self.counterText is None:
                self.counterText = uicontrols.EveHeaderLarge(parent=self.content, name='counter', left=34, top=-2, bold=True, color=self.timerData.color)
            text = str(count) if count < 10 else '9+'
            self.counterText.text = text

    def PlayActiveAnimation(self):
        self.activeAnimationCurves = ((self.halfCircleSprite, self.FlipFlop(self.halfCircleSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)), (self.cycleSprite, self.FlipFlop(self.cycleSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)), (self.pointerSprite, self.FlipFlop(self.pointerSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)))

    def StopActiveAnimation(self):
        if self.activeAnimationCurves is not None:
            for sprite, animCurve in self.activeAnimationCurves:
                animCurve.Stop()
                sprite.opacity = 1.0

            self.activeAnimationCurves = None


class TimerContainer(uiprimitives.Container):
    __guid__ = 'crimewatchTimers.TimerContainer'
    __notifyevents__ = ['OnWeaponsTimerUpdate',
     'OnPvpTimerUpdate',
     'OnCriminalTimerUpdate',
     'OnNpcTimerUpdate',
     'OnCombatTimersUpdated',
     'OnCrimewatchEngagementUpdated',
     'OnCrimeWatchBoosterUpdated',
     'OnJumpTimersUpdated']
    default_name = 'TimerContainer'
    default_height = 32
    default_width = 96 + 16
    default_padBottom = 6
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.weaponsTimer = None
        self.npcTimer = None
        self.pvpTimer = None
        self.criminalTimer = None
        self.engagementTimer = None
        self.boosterTimer = None
        self.jumpActivationTimer = None
        self.jumpFatigueTimer = None
        self.crimewatchSvc = sm.GetService('crimewatchSvc')
        uthread.new(self.OnCombatTimersUpdated)

    def OnCombatTimersUpdated(self):
        """This sets the combat timers when ever we change a location"""
        self.OnWeaponsTimerUpdate(doAlert=False, *self.crimewatchSvc.GetWeaponsTimer())
        self.OnNpcTimerUpdate(doAlert=False, *self.crimewatchSvc.GetNpcTimer())
        self.OnPvpTimerUpdate(doAlert=False, *self.crimewatchSvc.GetPvpTimer())
        self.OnCriminalTimerUpdate(doAlert=False, *self.crimewatchSvc.GetCriminalTimer())
        self.OnCrimewatchEngagementUpdated(None, None, doAlert=False)
        self.OnCrimeWatchBoosterUpdated()
        self.OnJumpTimersUpdated(doAlert=False, *self.crimewatchSvc.GetJumpTimers())

    def OnWeaponsTimerUpdate(self, state, expiryTime, doAlert = True):
        """Resets when weapons and offencive modules fire"""
        if state in (const.weaponsTimerStateActive, const.weaponsTimerStateInherited):
            timer = self.GetTimer(TimerType.Weapons)
            timer.SetExpiryTime(None, doAlert)
        elif expiryTime is not None:
            timer = self.GetTimer(TimerType.Weapons)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Weapons)

    def OnNpcTimerUpdate(self, state, expiryTime, doAlert = True):
        """Resets when player aggresses against npc entities"""
        if state in (const.npcTimerStateActive, const.npcTimerStateInherited):
            timer = self.GetTimer(TimerType.Npc)
            timer.SetExpiryTime(None, doAlert)
        elif expiryTime is not None:
            timer = self.GetTimer(TimerType.Npc)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Npc)

    def OnPvpTimerUpdate(self, state, expiryTime, doAlert = True):
        """Resets when player aggresses against other players"""
        if state in (const.pvpTimerStateActive, const.pvpTimerStateInherited):
            timer = self.GetTimer(TimerType.Pvp)
            timer.SetExpiryTime(None, doAlert)
        elif expiryTime is not None:
            timer = self.GetTimer(TimerType.Pvp)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Pvp)

    def OnCriminalTimerUpdate(self, state, expiryTime, doAlert = True):
        """Resets when player commits illegal and criminal acts"""
        if state in (const.criminalTimerStateActiveSuspect, const.criminalTimerStateInheritedSuspect):
            timer = self.GetTimer(TimerType.Suspect)
            timer.SetExpiryTime(None, doAlert)
        elif state == const.criminalTimerStateTimerSuspect and expiryTime is not None:
            timer = self.GetTimer(TimerType.Suspect)
            timer.SetExpiryTime(expiryTime, doAlert)
        elif state in (const.criminalTimerStateActiveCriminal, const.criminalTimerStateInheritedCriminal):
            timer = self.GetTimer(TimerType.Criminal)
            timer.SetExpiryTime(None, doAlert)
        elif state == const.criminalTimerStateTimerCriminal and expiryTime is not None:
            timer = self.GetTimer(TimerType.Criminal)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Suspect)

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout, doAlert = True):
        engagements = self.crimewatchSvc.GetMyEngagements()
        if len(engagements) == 0:
            self.DeleteTimer(TimerType.Engagement)
        else:
            timer = self.GetTimer(TimerType.Engagement)
            onGoingEngagement = any((_timeout == const.crimewatchEngagementTimeoutOngoing for _timeout in engagements.itervalues()))
            if onGoingEngagement:
                timeout = None
            else:
                timeout = max((_timeout for _timeout in engagements.itervalues()))
            timer.SetExpiryTime(timeout, doAlert)
            timer.SetCounter(len(engagements))

    def OnCrimeWatchBoosterUpdated(self, doAlert = True):
        boosters = self.crimewatchSvc.GetMyBoosters()
        boosterList = [ b for b in boosters if b.boosterDuration ]
        if len(boosterList) == 0:
            self.DeleteTimer(TimerType.Booster)
        else:
            timer = self.GetTimer(TimerType.Booster)
            boosterList.sort(key=lambda x: x.expiryTime, reverse=True)
            longestLastingBooster = boosterList[0]
            timeout = longestLastingBooster.expiryTime
            maxDuration = longestLastingBooster.boosterDuration
            timer.SetExpiryTime(timeout, doAlert, maxDuration * 10000)
            timer.SetCounter(len(boosterList))

    def OnJumpTimersUpdated(self, jumpActivation, jumpFatigue, fatigueRatio, lastUpdated, doAlert = False):
        """
        There are 2 possible jump timers which are shown / hidden indepdently.
        """
        if jumpFatigue and jumpFatigue > blue.os.GetWallclockTime():
            timer = self.GetTimer(TimerType.JumpFatigue)
            timer.fatigueRatio = fatigueRatio
            timer.SetExpiryTime(jumpFatigue, doAlert, jumpFatigue - lastUpdated)
        else:
            self.DeleteTimer(TimerType.JumpFatigue)
        if jumpActivation and jumpActivation > blue.os.GetWallclockTime():
            self.GetTimer(TimerType.JumpActivation).SetExpiryTime(jumpActivation, doAlert, jumpActivation - lastUpdated)
        else:
            self.DeleteTimer(TimerType.JumpActivation)

    def DeleteTimer(self, timerType):
        """
        Delete the timer and set it to None
        Tigger timer death animation and sliding close gaps
        """
        idx = None
        timerName = TIMER_ATTRIBUTE_NAMES_BY_TIMER_TYPE[timerType]
        timer = getattr(self, timerName, None)
        if timer is not None:
            idx = self.children.index(timer)
            timer.EndAnimation()
            timer.Close()
            setattr(self, timerName, None)
        if idx is not None:
            for timer in self.children[idx:idx + 1]:
                timer.ShiftLeft()

    def DeleteWhenFinished(self, timer):
        self.DeleteTimer(timer.timerType)

    def GetTimer(self, timerType):
        """
        Gets the appropriate timer for the type. Will create new if no one exists
        """
        if timerType == TimerType.Weapons:
            if self.weaponsTimer is None:
                self.weaponsTimer = Timer(parent=self, name='WeaponsTimer', timerType=TimerType.Weapons)
            timer = self.weaponsTimer
        elif timerType == TimerType.Npc:
            if self.npcTimer is None:
                self.npcTimer = Timer(parent=self, name='NpcTimer', timerType=TimerType.Npc)
            timer = self.npcTimer
        elif timerType == TimerType.Pvp:
            if self.pvpTimer is None:
                self.pvpTimer = Timer(parent=self, name='PvpTimer', timerType=TimerType.Pvp)
            timer = self.pvpTimer
        elif timerType == TimerType.Suspect:
            if self.criminalTimer is None:
                self.criminalTimer = Timer(parent=self, name='CriminalTimer', timerType=TimerType.Suspect)
            timer = self.criminalTimer
        elif timerType == TimerType.Criminal:
            if self.criminalTimer is None:
                self.criminalTimer = Timer(parent=self, name='CriminalTimer', timerType=TimerType.Criminal)
            else:
                self.criminalTimer.SetTimerType(TimerType.Criminal)
            timer = self.criminalTimer
        elif timerType == TimerType.Engagement:
            if self.engagementTimer is None:
                self.engagementTimer = Timer(parent=self, name='EngagementTimer', timerType=TimerType.Engagement, hintClass=EngagementTimerHint)
            timer = self.engagementTimer
        elif timerType == TimerType.Booster:
            if self.boosterTimer is None:
                self.boosterTimer = Timer(parent=self, name='BoosterTimer', timerType=TimerType.Booster, hintClass=BoosterTimerHint)
            timer = self.boosterTimer
        elif timerType == TimerType.JumpActivation:
            if self.jumpActivationTimer is None:
                self.jumpActivationTimer = Timer(parent=self, name='JumpActivationTimer', timerType=TimerType.JumpActivation, hintClass=JumpTimerHint, callback=self.DeleteWhenFinished)
            timer = self.jumpActivationTimer
        elif timerType == TimerType.JumpFatigue:
            if self.jumpFatigueTimer is None:
                self.jumpFatigueTimer = Timer(parent=self, name='JumpFatigueTimer', timerType=TimerType.JumpFatigue, hintClass=JumpTimerHint, callback=self.DeleteWhenFinished)
            timer = self.jumpFatigueTimer
        return timer
