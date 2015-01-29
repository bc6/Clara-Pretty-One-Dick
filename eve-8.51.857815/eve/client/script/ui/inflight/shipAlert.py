#Embedded file name: eve/client/script/ui/inflight\shipAlert.py
import math
import blue
import uiprimitives
import uicontrols
from eve.client.script.util.settings import IsShipHudTopAligned
from eveaudio.shiphealthnotification import SoundNotification
import uthread
import carbonui.const as uiconst
import const
import fontConst
import localization
import util
SHIELD_INDEX = 0
ARMOR_INDEX = 1
HULL_INDEX = 2
CAPACITOR_INDEX = 3
CARGOHOLD_INDEX = 4
NAMES_TO_LEVEL = {'shield': SHIELD_INDEX,
 'armour': ARMOR_INDEX,
 'hull': HULL_INDEX,
 'capacitor': CAPACITOR_INDEX,
 'cargoHold': CARGOHOLD_INDEX}

class ShipAlertContainer(uiprimitives.Container):
    """
    Displays alerts when the ship is being damaged (including capacitor).
    """
    __guid__ = 'uicls.ShipAlertContainer'
    __notifyevents__ = ['OnSessionChanged', 'OnDamageStateChange', 'OnCapacitorChange']
    messages = ['UI/Inflight/ShieldLevelAlert', 'UI/Inflight/ArmorLevelAlert', 'UI/Inflight/HullLevelAlert']
    rtpcNames = ['shield_level',
     'armor_level',
     'hull_level',
     'capacitor_level',
     'cargo_hold_level']
    hudGlowColor = (1.0, 0.4, 0.4, 0.2)

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.alertText = None
        self.fullScreen = uiprimitives.Container(name='shipAlerts', parent=uicore.layer.inflight, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        self.labelCont = uiprimitives.Container(name='fakeTextCont', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=400)
        self.warningLabelCont = uiprimitives.Container(name='warningLabelCont', parent=self.labelCont, align=uiconst.TOBOTTOM, height=40, top=100)
        self.warningLabel = uicontrols.EveCaptionLarge(name='warningLabel', parent=self.warningLabelCont, align=uiconst.CENTER, bold=True, color=(1, 1, 1, 1.0), idx=0)
        self.warningLabel.uppercase = True
        self.warningLabel.opacity = 0.0
        self.exceptionLabel = uicontrols.Label(name='fakeException', parent=self.labelCont, align=uiconst.TOBOTTOM, fontsize=fontConst.EVE_SMALL_FONTSIZE, color=(1, 0, 0, 0.4))
        self.damageElements = self.AddSideElements()
        self.oldDamageState = [1,
         1,
         1,
         1,
         1]
        self.alertStartTimes = [None,
         None,
         None,
         None,
         None]
        self.isActuallyDamaged = [False,
         False,
         False,
         False,
         False]
        self.lastRTPCLevels = [None,
         None,
         None,
         None,
         None]
        self.animMethods = [self.DoShieldAnimation, self.DoArmorAnimation, self.DoHullAnimation]
        self.animDuration = 2.0
        self.UpdatePosition()
        sm.RegisterNotify(self)
        self.enteringCapsule = False

    def AddSideElements(self):
        name = 'red bars'
        texture = 'res:/UI/Texture/classes/ShipAlert/warped2.png'
        cont = uiprimitives.Container(name=name, parent=self.fullScreen, align=uiconst.TOALL)
        width = 1024
        height = 256
        uiprimitives.Sprite(parent=cont, texturePath=texture, align=uiconst.CENTERTOP, height=height, width=width, color=(1, 0, 0, 1), rotation=math.pi, useSizeFromTexture=True)
        uiprimitives.Sprite(parent=cont, texturePath=texture, align=uiconst.CENTERBOTTOM, height=height, width=width, color=(1, 0, 0, 1), rotation=0, useSizeFromTexture=True)
        cont.opacity = 0
        return cont

    def _OnClose(self, *args):
        uiprimitives.Container._OnClose(self, *args)
        self.fullScreen.Close()

    def SetNotificationEnabled(self, levelName, enabled):
        """
        Called when a checkbox in the NotifySettingsWindow is changed
        """
        level = NAMES_TO_LEVEL[levelName]
        if enabled:
            isActive = self.IsLevelActive(level, self.oldDamageState[level])
            if isActive:
                self.LevelTakenDamage(level, True)
        else:
            self.alertStartTimes[level] = None

    def AlertThresholdChanged(self, levelName):
        """
        Called when a slider in the NotifySettingsWindow is changed
        """
        level = NAMES_TO_LEVEL[levelName]
        isActive = self.IsLevelActive(level, self.oldDamageState[level])
        if isActive:
            self.LevelTakenDamage(level, True)
        else:
            self.alertStartTimes[level] = None

    def UpdatePosition(self):
        if self.parent is None:
            return
        self.height = uicore.desktop.height - self.parent.height
        self.width = self.parent.width
        self.top = self.parent.height
        self.labelCont.height = self.height
        self.alignedTop = IsShipHudTopAligned()
        if not self.alignedTop:
            self.align = uiconst.CENTERBOTTOM
            self.warningLabelCont.align = uiconst.TOBOTTOM
            self.exceptionLabel.align = uiconst.TOBOTTOM
        else:
            self.align = uiconst.CENTERTOP
            self.warningLabelCont.align = uiconst.TOTOP
            self.exceptionLabel.align = uiconst.TOTOP

    def OnSessionChanged(self, isRemote, sess, change):
        if 'shipid' not in change:
            return
        if sess.sessionChangeReason in ('eject', 'storeVessel'):
            return
        self.alertStartTimes[2] = None
        ship = sm.GetService('godma').GetItem(change['shipid'][1])
        if ship is not None and ship.groupID == const.groupCapsule:
            self.DoEnteringCapsuleAnimation()

    def OnCapacitorChange(self, load, maxCap, level):
        isActive, changeDirection = self.SetDamageAmountAndCheckIfActive(3, level)
        if isActive and changeDirection < 0:
            self.LevelTakenDamage(3)

    def OnDamageStateChange(self, shipID, damageState):
        if shipID != session.shipid:
            return
        self.NewDamageState(damageState)

    def NewDamageState(self, damageState):
        activateHigher = False
        for level in [HULL_INDEX, ARMOR_INDEX, SHIELD_INDEX]:
            damageAmount = damageState[level]
            isActive, changeDirection = self.SetDamageAmountAndCheckIfActive(level, damageAmount)
            if changeDirection < 0:
                activateHigher = True
            if isActive and (changeDirection < 0 or activateHigher):
                self.LevelTakenDamage(level, changeDirection < 0)
            elif changeDirection > 0:
                if level == HULL_INDEX:
                    self.alertStartTimes[HULL_INDEX] = None
                    self.exceptionLabel.text = ''

    def IsLevelActive(self, level, damageAmount):
        """
        Finds if an alert level should be active based on the user settings and damage for this level
        """
        info = SoundNotification(level)
        enabled = settings.user.notifications.Get(info.activeFlagSettingsName, 1)
        alertLevel = settings.user.notifications.Get(info.healthThresholdSettingsName, info.defaultThreshold)
        if enabled and damageAmount < alertLevel:
            return True
        return False

    def SetDamageAmountAndCheckIfActive(self, level, damageAmount):
        isActive = self.IsLevelActive(level, damageAmount)
        changeDirection = 0
        if self.oldDamageState is not None and damageAmount != self.oldDamageState[level]:
            if damageAmount < self.oldDamageState[level]:
                changeDirection = -1
            elif damageAmount > self.oldDamageState[level]:
                changeDirection = 1
        rtpcLevel = min(int((1.0 - damageAmount) * 100), 99)
        if self.lastRTPCLevels[level] is None or self.lastRTPCLevels[level] != rtpcLevel:
            sm.GetService('audio').SetGlobalRTPC(self.rtpcNames[level], rtpcLevel)
            self.lastRTPCLevels[level] = rtpcLevel
        self.oldDamageState[level] = damageAmount
        return (isActive, changeDirection)

    def LevelTakenDamage(self, level, isDamaged = True):
        """
        Called when a level has taken damage. Starts the appropriate animation thread if it isn't already running.
        """
        self.isActuallyDamaged[level] = isDamaged
        self.alertStartTimes[level] = blue.os.GetSimTime()
        if level != CAPACITOR_INDEX:
            if getattr(self, 'alertAnimation_Thread', None) is None:
                self.alertAnimation_Thread = uthread.new(self.DoAlertAnimation_Thread)
        elif getattr(self, 'capacitorAnimation_Thread', None) is None:
            self.capacitorAnimation_Thread = uthread.new(self.DoCapacitorAnimation_Thread)

    def SetWarningText(self, text):
        if not self.enteringCapsule:
            self.warningLabel.text = text

    def GetAlertLevelAndStartTime(self):
        """
        Gets the current active alert level and the time the alert started
        """
        alertLevel = self.GetActiveAlertLevel()
        if alertLevel is None:
            return (None, None)
        alertStartTime = self.alertStartTimes[alertLevel]
        return (alertLevel, alertStartTime)

    def DoAlertAnimation_Thread(self):
        alertLevel, alertStartTime = self.GetAlertLevelAndStartTime()
        if alertLevel is None or alertStartTime is None:
            return
        alertActive = True
        while alertActive and not self.destroyed:
            self.SetWarningText(localization.GetByLabel(self.messages[alertLevel]))
            if not self.enteringCapsule:
                animationMethod = self.animMethods[alertLevel]
                animationMethod()
            else:
                blue.synchro.SleepSim(self.animDuration * 1000)
            alertLevel, alertStartTime = self.GetAlertLevelAndStartTime()
            if alertLevel is None or alertStartTime is None:
                alertActive = False
            else:
                alertActive = alertStartTime < 0 or blue.os.TimeDiffInMs(alertStartTime, blue.os.GetSimTime()) < self.animDuration * 1000

        self.alertAnimation_Thread = None

    def GetActiveAlertLevel(self):
        highestAlertLevel = None
        for level, startTime in enumerate(self.alertStartTimes[:3]):
            if startTime is None:
                continue
            if not self.IsLevelActive(level, self.oldDamageState[level]):
                continue
            valid = startTime < 0 or blue.os.TimeDiffInMs(startTime, blue.os.GetSimTime()) < self.animDuration * 1000
            if valid:
                highestAlertLevel = level

        return highestAlertLevel

    def DoCapacitorAnimation_Thread(self):
        alertActive = True
        while alertActive:
            self.DoCapacitorAnimation(self.animDuration)
            blue.synchro.SleepSim(self.animDuration * 1000)
            capacitorAlertStartTime = self.alertStartTimes[CAPACITOR_INDEX]
            if capacitorAlertStartTime is None:
                alertActive = False
            else:
                alertActive = blue.os.TimeDiffInMs(capacitorAlertStartTime, blue.os.GetSimTime()) < self.animDuration * 1000

        self.capacitorAnimation_Thread = None

    def DoCapacitorAnimation(self, totalDuration):
        loops = 1.0
        duration = totalDuration / loops
        sm.GetService('audio').SendUIEvent('ui_warning_capacitor')
        uicore.animations.MorphScalar(uicore.layer.shipui.GetChild('powercore'), 'opacity', 1.0, 0.5, duration=duration, loops=loops, curveType=uiconst.ANIM_WAVE)

    def DoShieldAnimation(self, duration = 2.0, fromHigher = False):
        uicore.animations.MorphScalar(self.damageElements, 'opacity', 0, 0.7, duration=duration, curveType=uiconst.ANIM_WAVE)
        uicore.animations.SpGlowFadeIn(uicore.layer.shipui.shieldGauge, duration=duration, glowColor=self.hudGlowColor, glowExpand=3.0, curveType=uiconst.ANIM_WAVE)
        if not fromHigher:
            sm.GetService('audio').SendUIEvent('ui_warning_shield')
            blue.synchro.SleepSim(duration * 1000)

    def DoArmorAnimation(self, duration = 1.0, fromHigher = False):
        uicore.animations.MorphScalar(self.damageElements, 'opacity', 0, 0.7, duration=duration, curveType=uiconst.ANIM_WAVE)
        uicore.animations.SpGlowFadeIn(uicore.layer.shipui.armorGauge, duration=duration, glowColor=self.hudGlowColor, glowExpand=3.0, curveType=uiconst.ANIM_WAVE)
        self.DoShieldAnimation(duration, True)
        if not fromHigher:
            sm.GetService('audio').SendUIEvent('ui_warning_armor')
            blue.synchro.SleepSim(duration * 1000)

    def DoHullAnimation(self, duration = 0.6):
        uicore.animations.MorphScalar(self.damageElements, 'opacity', 0, 1, duration=duration, curveType=uiconst.ANIM_WAVE)
        uicore.animations.SpGlowFadeIn(uicore.layer.shipui.structureGauge, duration=duration, glowColor=self.hudGlowColor, glowExpand=3.0, curveType=uiconst.ANIM_WAVE)
        self.DoArmorAnimation(duration, True)
        sm.GetService('audio').SendUIEvent('ui_warning_hull')
        blue.synchro.SleepSim(duration * 1000)

    def DoEnteringCapsuleAnimation(self):
        loops = 1.0
        duration = 2.0 / loops
        self.SetWarningText(localization.GetByLabel('UI/Inflight/CapsuleEjected'))
        self.enteringCapsule = True
        self.warningLabel.color = util.Color.RED
        uicore.animations.MorphScalar(self.warningLabel, 'opacity', 1, 0, duration=duration, loops=loops)
