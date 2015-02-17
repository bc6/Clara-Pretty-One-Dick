#Embedded file name: eve/client/script/ui/crimewatch\crimewatchHints.py
"""
    This file contains the code for the hints you get when mousing over the crimewatch timers
"""
import uiprimitives
import localization
import uicontrols
import uthread
import copy
import state
import blue
import yaml
import carbonui.const as uiconst
from carbonui.primitives.fill import Fill
from carbonui.util.color import Color
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import Label, EveLabelSmall
from carbonui.util.various_unsorted import IsUnder
from eve.client.script.ui.crimewatch.crimewatchConst import Colors
from eve.client.script.ui.shared.stateFlag import FlagIconWithState
from utillib import KeyVal
from carbonui.control.scrollContainer import ScrollContainer
from localization.formatters.timeIntervalFormatters import FormatTimeInterval
HINT_FRAME_COLOR = (1.0, 1.0, 1.0, 0.25)
HINT_BACKGROUND_COLOR = (0, 0, 0, 0.85)
MAX_ENGAGED_VISIBLE = 10

def FmtTime(timeLeft):
    """Format time left in 00:00 format"""
    if timeLeft > 0:
        seconds = timeLeft / const.SEC
        minutes = seconds / 60
        seconds = seconds % 60
    else:
        minutes = 0
        seconds = 0
    return '%02d:%02d' % (max(0, minutes), max(0, seconds))


class TimerHint(uiprimitives.Container):
    __guid__ = 'crimewatchTimers.TimerHint'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_bgColor = HINT_BACKGROUND_COLOR
    default_width = 300
    default_height = 48
    TIME_WIDTH = 58
    TEXT_WIDTH = 242

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.parentTimer = attributes.get('parentTimer')
        self.timerData = attributes.get('timerData')
        self.GetTime = self.timerData.timerFunc
        uicontrols.Frame(pgParent=self, state=uiconst.UI_DISABLED, color=HINT_FRAME_COLOR)
        leftCont = uiprimitives.Container(parent=self, align=uiconst.TOLEFT, width=self.TIME_WIDTH)
        rightCont = uiprimitives.Container(parent=self, align=uiconst.TOALL)
        self.time = uicontrols.Label(parent=leftCont, name='counter', text=str(int(self.timerData.maxTimeout / const.SEC)), fontsize=self.GetTimerFontSize(), bold=False, align=uiconst.CENTERLEFT, color=self.timerData.color, left=2 * const.defaultPadding)
        self.text = uicontrols.EveLabelSmall(left=const.defaultPadding, parent=rightCont, name='timer description', text=localization.GetByLabel(self.timerData.tooltip), align=uiconst.CENTERLEFT, width=self.TEXT_WIDTH - 2 * const.defaultPadding)
        self.height = self.text.actualTextHeight + 2 * const.defaultPadding
        self.activeBlink = None
        self.doUpdates = True
        uthread.new(self.UpdateTimer)
        self.opacity = 0.0
        uicore.animations.FadeIn(self, duration=0.5)

    def GetTimerFontSize(self):
        if session.languageID == 'ZH':
            return 16
        else:
            return 20

    def _OnClose(self):
        self.doUpdates = False
        self.parentTimer.timerHint = None

    def UpdateTimer(self):
        startTime = self.GetTime()
        while self.doUpdates:
            timeNow = self.GetTime()
            if self.parentTimer.expiryTime is not None:
                timeLeft = max(0, self.parentTimer.expiryTime - timeNow)
                if timeLeft == 0:
                    self.doUpdates = False
                if self.activeBlink is not None:
                    self.activeBlink.Stop()
                    self.time.opacity = 1.0
                    self.activeBlink = None
            else:
                timeLeft = self.timerData.maxTimeout
                if self.activeBlink is None:
                    self.activeBlink = uicore.animations.BlinkOut(self.time, duration=1.0, loops=uiconst.ANIM_REPEAT)
            if startTime + const.SEC < timeNow:
                if not (uicore.uilib.mouseOver is self or IsUnder(uicore.uilib.mouseOver, self.parentTimer)):
                    self.doUpdates = False
            self.OnUpdate(timeLeft)
            if self.doUpdates:
                blue.pyos.synchro.SleepWallclock(200)

        uicore.animations.FadeOut(self, sleep=True)
        self.Close()

    def OnUpdate(self, timeLeft):
        self.time.text = FmtTime(timeLeft)


class EngagementEntry(uiprimitives.Container):
    __guid__ = 'crimewatchTimers.EngagementEntry'
    default_align = uiconst.TOTOP
    default_height = 32
    default_padBottom = 1
    default_state = uiconst.UI_NORMAL
    isDragObject = True
    __notifyevents__ = ['OnCrimewatchEngagementUpdated']

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.charID = attributes.get('charID')
        self.timeout = attributes.get('timeout')
        self.isDragObject = True
        self.itemID = self.charID
        self.info = cfg.eveowners.Get(self.charID)
        self.activeBlink = None
        self.highlight = uiprimitives.Fill(bgParent=self, color=(1, 1, 1, 0.1), state=uiconst.UI_HIDDEN)
        leftCont = uiprimitives.Container(parent=self, align=uiconst.TOLEFT, width=54)
        self.time = uicontrols.Label(parent=leftCont, name='counter', text='', fontsize=16, bold=False, align=uiconst.CENTERLEFT, color=Colors.Engagement.GetRGBA(), left=2 * const.defaultPadding)
        self.portrait = uiprimitives.Sprite(parent=self, pos=(50, 0, 32, 32), state=uiconst.UI_DISABLED)
        uicontrols.EveLabelSmall(parent=self, name='name', text=self.info.ownerName, align=uiconst.TOPLEFT, top=1, left=96)
        self.corpText = uicontrols.EveLabelSmall(parent=self, name='corporation', text='', align=uiconst.TOPLEFT, top=17, left=96)
        self.stateFlag = FlagIconWithState(parent=self, align=uiconst.TOPRIGHT, left=13, top=4)
        self.LoadData()
        sm.RegisterNotify(self)

    def LoadData(self):
        self.SetTimer()
        sm.GetService('photo').GetPortrait(self.charID, 32, self.portrait)
        uthread.new(self.LazyLoadData)

    def OnMouseEnter(self, *args):
        self.highlight.display = True

    def OnMouseExit(self, *args):
        self.highlight.display = False

    def SetTimer(self):
        if self.timeout == const.crimewatchEngagementTimeoutOngoing:
            self.time.text = FmtTime(const.crimewatchEngagementDuration)
            if self.activeBlink is None:
                self.activeBlink = uicore.animations.BlinkOut(self.time, duration=1.0, loops=uiconst.ANIM_REPEAT)
        else:
            self.time.text = FmtTime(self.timeout - blue.os.GetWallclockTime())
            if self.activeBlink is not None:
                self.activeBlink.Stop()
                self.activeBlink = None
                self.time.opacity = 1.0

    def LazyLoadData(self):
        slimItem = sm.GetService('crimewatchSvc').GetSlimItemDataForCharID(self.charID)
        if slimItem is not None:
            self.corpText.text = cfg.eveowners.Get(slimItem.corpID).ownerName
            stateSvc = sm.GetService('state')
            flagCode = stateSvc.CheckFilteredFlagState(slimItem, (state.flagLimitedEngagement,))
            flagInfo = stateSvc.GetStatePropsColorAndBlink(flagCode)
            self.stateFlag.ModifyIcon(flagInfo=flagInfo)
            self.slimItem = copy.copy(slimItem)

    def OnClick(self):
        sm.GetService('info').ShowInfo(typeID=self.info.typeID, itemID=self.charID)

    def GetDragData(self, *args):
        if self and not self.destroyed:
            fakeNode = KeyVal()
            fakeNode.charID = self.charID
            fakeNode.typeID = self.info.typeID
            fakeNode.info = self.info
            fakeNode.itemID = self.itemID
            fakeNode.__guid__ = 'listentry.User'
            return [fakeNode]
        else:
            return []

    def GetMenu(self):
        if self.slimItem:
            if self.slimItem.itemID:
                return sm.GetService('menu').CelestialMenu(self.slimItem.itemID)
            else:
                return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.info.typeID)

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout):
        if otherCharId == self.charID:
            if timeout is None:
                uicore.animations.FadeOut(self, duration=0.5, sleep=True)
                self.Close()
                sm.ScatterEvent('OnEngagementTimerHintResize')
            else:
                self.timeout = timeout


class BaseAdvancedTimerHint(uicontrols.ContainerAutoSize):
    default_name = 'BaseAdvancedTimerHint'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_bgColor = HINT_BACKGROUND_COLOR
    default_width = 240

    def ApplyAttributes(self, attributes):
        uicontrols.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.parentTimer = attributes.get('parentTimer')
        self.timerData = attributes.get('timerData')
        self.GetTime = self.timerData.timerFunc
        self.doUpdates = True
        uicontrols.Frame(bgParent=self, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.25))
        self.mainText = uicontrols.EveLabelMedium(parent=self, align=uiconst.TOTOP, text='', padding=(8, 8, 8, 8), state=uiconst.UI_DISABLED)
        self.entryContainer = ScrollContainer(parent=self, align=uiconst.TOTOP)

    def UpdateTimer(self):
        startTime = self.GetTime()
        count = 0
        while self.doUpdates:
            timeNow = self.GetTime()
            for child in self.entryContainer.mainCont.children[:]:
                child.SetTimer()

            if startTime + const.SEC < timeNow:
                if not (uicore.uilib.mouseOver is self or IsUnder(uicore.uilib.mouseOver, self) or IsUnder(uicore.uilib.mouseOver, self.parentTimer)):
                    if count > 2:
                        self.doUpdates = False
                    else:
                        count += 1
                else:
                    count = 0
            if self.doUpdates:
                blue.pyos.synchro.SleepWallclock(200)

        uicore.animations.FadeOut(self, sleep=True)
        self.Close()

    def _OnClose(self):
        self.doUpdates = False
        self.parentTimer.timerHint = None


class EngagementTimerHint(BaseAdvancedTimerHint):
    __guid__ = 'crimewatchTimers.EngagementTimerHint'
    __notifyevents__ = ['OnEngagementTimerHintResize', 'OnCrimewatchEngagementUpdated']
    default_name = 'EngagementTimerHint'

    def ApplyAttributes(self, attributes):
        BaseAdvancedTimerHint.ApplyAttributes(self, attributes)
        self.LoadData()
        uthread.new(self.UpdateTimer)
        sm.RegisterNotify(self)

    def OnEngagementTimerHintResize(self):
        self.UpdateScrollHeight()

    def SortKey(self, entry):
        if entry[0] == const.crimewatchEngagementTimeoutOngoing:
            return blue.os.GetWallclockTime()

    def LoadData(self):
        engagements = sm.GetService('crimewatchSvc').GetMyEngagements()
        cfg.eveowners.Prime(engagements.keys())
        engagementList = [ (timeout, charID) for charID, timeout in engagements.iteritems() ]
        engagementList.sort(key=self.SortKey)
        for timeout, charID in engagementList:
            self.AddEntry(charID, timeout)

        self.mainText.text = localization.GetByLabel('UI/Crimewatch/Timers/EngagementTooltipHintHeader', count=len(engagementList))
        self.UpdateScrollHeight()

    def AddEntry(self, charID, timeout):
        EngagementEntry(parent=self.entryContainer, charID=charID, timeout=timeout)

    def UpdateScrollHeight(self):
        self.entryContainer.height = sum((x.height + x.padBottom for x in self.entryContainer.mainCont.children[:MAX_ENGAGED_VISIBLE]))

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout):
        for child in self.entryContainer.mainCont.children[:]:
            if otherCharId == child.charID:
                break
        else:
            self.AddEntry(otherCharId, timeout)
            self.UpdateScrollHeight()


class BoosterTimerHint(BaseAdvancedTimerHint):
    __guid__ = 'crimewatchTimers.EngagementTimerHint'
    default_name = 'BoosterTimerHint'

    def ApplyAttributes(self, attributes):
        BaseAdvancedTimerHint.ApplyAttributes(self, attributes)
        self.mainText.text = localization.GetByLabel('UI/Crimewatch/Timers/ActiveBoosters')
        self.entryContainer = ScrollContainer(parent=self, align=uiconst.TOTOP)
        self.LoadData()
        uthread.new(self.UpdateTimer)

    def LoadData(self):
        boosters = sm.GetService('crimewatchSvc').GetMyBoosters()
        sortedBoosters = [ (b.expiryTime, b) for b in boosters if b.boosterDuration ]
        sortedBoosters.sort(reverse=True)
        for expiryTime, booster in sortedBoosters:
            effects = sm.GetService('crimewatchSvc').GetBoosterEffects(booster)
            entry = self.AddEntry(booster, expiryTime, effects)

        self.UpdateHeightAndWidth()

    def AddEntry(self, booster, expiryTime, effects):
        entry = BoosterEntry(parent=self.entryContainer, booster=booster, expiryTime=expiryTime, effects=effects)
        return entry

    def UpdateHeightAndWidth(self):
        self.entryContainer.height = sum((x.height + x.padBottom for x in self.entryContainer.mainCont.children))
        self.width = max((x.maxtextwidth + 10 for x in self.entryContainer.mainCont.children))


class BoosterEntry(uiprimitives.Container):
    __guid__ = 'crimewatchTimers.BoosterEntry'
    default_align = uiconst.TOTOP
    default_height = 50
    default_padBottom = 1
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.booster = attributes.get('booster')
        self.expiryTime = attributes.get('expiryTime')
        self.effects = attributes.get('effects')
        self.positiveEffects = self.effects.get('positive', [])
        self.negativeEffects = self.effects.get('negative', [])
        self.typeInfo = cfg.invtypes.Get(self.booster.typeID)
        self.activeBlink = None
        self.highlight = Fill(bgParent=self, color=(1, 1, 1, 0.1), state=uiconst.UI_HIDDEN)
        leftWidth = 60
        leftCont = uiprimitives.Container(parent=self, align=uiconst.TOLEFT, width=leftWidth)
        self.time = Label(parent=leftCont, name='counter', text='', fontsize=16, bold=False, align=uiconst.TOPLEFT, color=(1, 1, 1, 0.75), left=2 * const.defaultPadding)
        self.boosterSprite = Icon(parent=self, name='boosterIcon', icon=self.typeInfo.iconID, pos=(leftWidth,
         0,
         24,
         24), ignoreSize=True, state=uiconst.UI_DISABLED)
        left = self.boosterSprite.left + self.boosterSprite.width
        boosterName = EveLabelSmall(parent=self, name='name', text=self.typeInfo.name, align=uiconst.TOPLEFT, top=1, left=left)
        self.maxtextwidth = boosterName.textwidth + boosterName.left
        padTop = boosterName.textheight + 4
        allModified = self.GetEffectsInfo(self.positiveEffects) + self.GetEffectsInfo(self.negativeEffects)
        for lineText in allModified:
            effectLabel = EveLabelSmall(parent=self, name='effect', text=lineText, align=uiconst.TOPLEFT, padTop=padTop, left=90)
            padTop += effectLabel.textheight + 2
            self.maxtextwidth = max(self.maxtextwidth, effectLabel.textwidth + effectLabel.left)

        self.height = max(padTop + 4, self.boosterSprite.height + 2)
        self.LoadData()

    def GetEffectsInfo(self, effects):
        effectsTextList = []
        for eff in effects:
            if eff.modifierInfo:
                modifyingAttributeID = yaml.safe_load(eff.modifierInfo)[0]['modifyingAttributeID']
                nameOfChanged = cfg.dgmattribs.Get(modifyingAttributeID).displayName
                effectAmount = sm.GetService('clientDogmaIM').GetDogmaLocation().GetAccurateAttributeValue(self.booster.itemID, modifyingAttributeID)
                effectText = localization.GetByLabel('UI/Crimewatch/Timers/BoosterPenaltyWithValue', percentage=abs(effectAmount), penaltyName=nameOfChanged)
            else:
                effectText = eff.displayName
            effectsTextList.append(effectText)

        return effectsTextList

    def LoadData(self):
        self.SetTimer()

    def OnMouseEnter(self, *args):
        self.highlight.display = True

    def OnMouseExit(self, *args):
        self.highlight.display = False

    def SetTimer(self):
        self.time.text = FmtTime(self.expiryTime - blue.os.GetWallclockTime())
        if self.activeBlink is not None:
            self.activeBlink.Stop()
            self.activeBlink = None
            self.time.opacity = 1.0

    def OnClick(self):
        sm.GetService('info').ShowInfo(typeID=self.typeInfo.typeID, itemID=self.booster.itemID)

    def GetMenu(self):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(itemID=self.booster.itemID, typeID=self.typeInfo.typeID)


class JumpTimerHint(TimerHint):
    __guid__ = 'crimewatchTimers.JumpTimerHint'

    def ApplyAttributes(self, attributes):
        TimerHint.ApplyAttributes(self, attributes)
        self.time.parent.Close()
        self.text.parent.Close()
        self.container = uicontrols.ContainerAutoSize(parent=self, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, padding=(3 * const.defaultPadding,
         2 * const.defaultPadding,
         2 * const.defaultPadding,
         2 * const.defaultPadding), callback=self.OnContainerResized)
        self.time = uicontrols.Label(parent=self.container, align=uiconst.TOTOP, fontsize=self.GetTimerFontSize(), color=self.timerData.color)
        self.text = uicontrols.EveLabelSmall(parent=self.container, align=uiconst.TOTOP, top=const.defaultPadding)
        self.next = uicontrols.EveLabelSmall(parent=self.container, align=uiconst.TOTOP, top=2 * const.defaultPadding, color=self.timerData.color)

    def OnContainerResized(self):
        self.height = self.container.height + 4 * const.defaultPadding

    def OnUpdate(self, remaining):
        color = Color.RGBtoHex(*self.timerData.color)
        if remaining:
            self.time.text = FormatTimeInterval(remaining, color, color)
            self.text.text = localization.GetByLabel(self.timerData.tooltip)
        if getattr(self.parentTimer, 'fatigueRatio', None):
            time = FormatTimeInterval(long(remaining * self.parentTimer.fatigueRatio), color, color)
            self.next.text = localization.GetByLabel('UI/Crimewatch/Timers/JumpFatigueNextActivation', time=time)
