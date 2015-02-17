#Embedded file name: eve/client/script/ui/shared/neocom\skillinfo.py
import math
import sys
import blue
from carbonui.control.scrollentries import SE_BaseClassCore
from eve.client.script.ui.control.infoIcon import InfoIcon
import uiprimitives
import uicontrols
import uthread
import log
import base
import util
import characterskills.util
import carbonui.const as uiconst
import localization
import telemetry
from carbon.common.script.sys.service import ROLE_GMH
from carbonui.primitives.frame import Frame
from carbonui.primitives.fill import Fill
from eve.client.script.ui.shared.monetization.trialPopup import ORIGIN_CHARACTERSHEET
BLUE_COLOR = (0.0,
 0.52,
 0.67,
 1.0)
LIGHTBLUE_COLOR = (0.6,
 0.8,
 0.87,
 1.0)
WHITE_COLOR = (1.0,
 1.0,
 1.0,
 0.5)

class BaseSkillEntry(uicontrols.SE_BaseClassCore):
    """
    This class is superclass of SkillEntry and SkillQueueEntry.
    """
    __guid__ = 'listentry.BaseSkillEntry'
    __nonpersistvars__ = ['selection', 'id']
    lasttime = None
    lastprogress = None
    lastrate = None
    timer = None
    totalpoints = None
    hilitePartiallyTrained = None
    blueColor = BLUE_COLOR
    lightBlueColor = LIGHTBLUE_COLOR
    whiteColor = WHITE_COLOR
    skillPointsText = ''
    rank = 0.0

    def _OnClose(self):
        uicontrols.SE_BaseClassCore._OnClose(self)
        self.timer = None

    def Startup(self, *args):
        sub = uiprimitives.Container(name='sub', parent=self)
        self.sr.inTrainingHilite = uiprimitives.Fill(parent=self, name='inTrainingHilite', padTop=1, padBottom=1, color=self.blueColor, state=uiconst.UI_HIDDEN)
        self.sr.inTrainingHilite.SetAlpha(0.15)
        self.sr.icon = uicontrols.Icon(name='skillIcon', parent=sub, align=uiconst.TOPLEFT, top=2, size=32, width=32, height=32, ignoreSize=True)
        self.sr.icon.state = uiconst.UI_DISABLED
        self.sr.haveicon = uicontrols.Icon(name='haveIcon', parent=sub, size=16, left=20, align=uiconst.TOPRIGHT, state=uiconst.UI_HIDDEN)
        self.sr.levelParent = uiprimitives.Container(name='levelParent', parent=sub, align=uiconst.TORIGHT, state=uiconst.UI_DISABLED, padRight=18)
        self.sr.levelHeaderParent = uiprimitives.Container(name='levelHeaderParent', parent=sub, align=uiconst.TORIGHT, state=uiconst.UI_HIDDEN)
        self.sr.levels = uiprimitives.Container(name='levels', parent=self.sr.levelParent, align=uiconst.TOPLEFT, left=0, top=5, width=48, height=10)
        uicontrols.Frame(parent=self.sr.levels, color=self.whiteColor)
        for i in xrange(5):
            f = uiprimitives.Fill(parent=self.sr.levels, name='level%d' % i, align=uiconst.RELATIVE, color=(1.0, 1.0, 1.0, 0.5), left=2 + i * 9, top=2, width=8, height=6)
            setattr(self.sr, 'box_%s' % i, f)

        self.sr.progressbarparent = uiprimitives.Container(name='progressbarparent', parent=self.sr.levelParent, align=uiconst.TOPLEFT, left=0, top=20, width=48, height=6)
        self.sr.progressBar = uiprimitives.Fill(parent=self.sr.progressbarparent, name='progressbar', align=uiconst.RELATIVE, color=self.whiteColor, height=4, top=1, left=1, state=uiconst.UI_HIDDEN)
        uicontrols.Frame(parent=self.sr.progressbarparent)
        self.sr.levelHeader1 = uicontrols.EveLabelSmall(text='', parent=self.sr.levelHeaderParent, left=10, top=3, state=uiconst.UI_DISABLED, idx=0, align=uiconst.TOPRIGHT)
        self.sr.levelHeader1.name = 'levelHeader1'
        textCont = uiprimitives.Container(name='textCont', parent=sub, align=uiconst.TOALL, padLeft=32, clipChildren=1)
        self.sr.nameLevelLabel = uicontrols.EveLabelMedium(text='', parent=textCont, left=0, top=0, state=uiconst.UI_DISABLED, maxLines=1)
        self.sr.nameLevelLabel.name = 'nameLevelLabel'
        self.sr.pointsLabel = uicontrols.EveLabelMedium(text='', parent=textCont, left=0, top=16, state=uiconst.UI_DISABLED, maxLines=1)
        self.sr.pointsLabel.name = 'pointsLabel'
        self.sr.timeLeftText = uicontrols.EveHeaderSmall(text='', parent=self.sr.levelHeaderParent, left=10, top=17, state=uiconst.UI_DISABLED, idx=0, align=uiconst.TOPRIGHT)
        self.sr.timeLeftText.name = 'timeLeftText'
        self.sr.infoicon = InfoIcon(left=2, parent=sub, idx=0, name='infoicon', align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo
        self.endOfTraining = None

    def Load(self, node):
        self.sr.node = node
        self.sr.node.meetRequirements = False
        self.lasttime = None
        self.lastsecs = None
        self.lastpoints = None
        self.timer = None
        self.endOfTraining = None
        self.hilitePartiallyTrained = settings.user.ui.Get('charsheet_hilitePartiallyTrainedSkills', False)
        data = node
        self.rec = data.skill
        self.skillPointsText = ''
        self.rank = 0.0
        self.sr.timeLeftText.text = ''
        if data.trained:
            self.rank = int(data.skill.skillTimeConstant + 0.4)
            if data.skill.skillLevel >= 5:
                self.skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillPointsValue', skillPoints=int(data.skill.skillPoints))
            else:
                self.skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillPointsAndNextLevelValues', skillPoints=int(data.skill.skillPoints), skillPointsToNextLevel=int(data.skill.spHi + 0.5))
                self.sr.node.meetRequirements = True
            self.sr.levelParent.state = uiconst.UI_PICKCHILDREN
            self.sr.levelHeaderParent.state = uiconst.UI_PICKCHILDREN
            self.sr.haveicon.state = uiconst.UI_HIDDEN
            self.sr.nameLevelLabel.color.SetRGB(1.0, 1.0, 1.0, 1.0)
            self.sr.pointsLabel.color.SetRGB(1.0, 1.0, 1.0, 1.0)
            self.hint = None
            self.GetIcon('complete')
        else:
            self.sr.levelParent.state = uiconst.UI_HIDDEN
            self.sr.levelHeaderParent.state = uiconst.UI_HIDDEN
            self.sr.node.meetRequirements = sm.GetService('skills').IsSkillRequirementMet(data.invtype.typeID)
            if sm.GetService('skills').IsTrialRestricted(data.invtype.typeID):
                self.sr.haveicon.state = uiconst.UI_NORMAL
                self.sr.haveicon.hint = localization.GetByLabel('UI/InfoWindow/SkillRestrictedForTrial')
                self.sr.haveicon.LoadIcon('res:/UI/Texture/classes/Skills/trial-restricted-16.png')
                self.sr.haveicon.color = (0.965, 0.467, 0.157, 1.0)

                def OpenSubscriptionPage(*args):
                    uicore.cmd.OpenSubscriptionPage(origin=ORIGIN_CHARACTERSHEET, reason=':'.join(['skill', str(data.invtype.typeID)]))

                self.sr.haveicon.OnClick = OpenSubscriptionPage
            else:
                self.sr.haveicon.state = uiconst.UI_PICKCHILDREN
                if self.sr.node.meetRequirements:
                    self.sr.haveicon.LoadIcon('ui_38_16_193')
                else:
                    self.sr.haveicon.LoadIcon('ui_38_16_194')
            if self.sr.node.meetRequirements:
                tappend = localization.GetByLabel('UI/SkillQueue/Skills/SkillRequirementsMet')
            else:
                tappend = localization.GetByLabel('UI/SkillQueue/Skills/SkillRequirementsNotMet')
            self.skillPointsText = tappend
            self.hint = tappend
            self.sr.nameLevelLabel.color.SetRGB(1.0, 1.0, 1.0, 0.75)
            self.sr.pointsLabel.color.SetRGB(1.0, 1.0, 1.0, 0.75)
            for each in cfg.dgmtypeattribs.get(data.invtype.typeID, []):
                if each.attributeID == const.attributeSkillTimeConstant:
                    self.rank = int(each.value)

            self.GetIcon()
        if data.Get('inTraining', 0):
            self.sr.inTrainingHilite.state = uiconst.UI_DISABLED
        else:
            self.sr.inTrainingHilite.state = uiconst.UI_HIDDEN
        if data.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()

    def GetIcon(self, state = None):
        """
            5 states, 4 icons
            1) untrained, new skill : 50_11
            2) in training or partially trained : 50_12
            3) reached a "chapter" ie: level: 50_13
            4) completed skill ie: level5: 50_14
        """
        icon = {'untrained': 'res:/UI/Texture/Classes/Skills/doNotHave.png',
         'new': 'res:/UI/Texture/Classes/Skills/doNotHave.png',
         'partial': 'res:/UI/Texture/Classes/Skills/levelPartiallyTrained.png',
         'intraining': 'res:/UI/Texture/Classes/Skills/levelPartiallyTrained.png',
         'chapter': 'res:/UI/Texture/Classes/Skills/levelTrained.png',
         'complete': 'res:/UI/Texture/Classes/Skills/fullyTrained.png'}.get(state, 'res:/UI/Texture/Classes/Skills/doNotHave.png')
        self.sr.icon.LoadIcon(icon, ignoreSize=True)
        self.sr.icon.SetSize(32, 32)

    def UpdateTraining(self, skill):
        if not self or self.destroyed:
            return
        spm = skill.spm
        ETA = skill.skillTrainingEnd
        spHi = skill.spHi
        level = skill.skillLevel
        if not self or self.destroyed or util.GetAttrs(self, 'sr', 'node', 'skill', 'itemID') != skill.itemID:
            return
        if ETA:
            time = ETA - blue.os.GetWallclockTime()
            secs = time / 10000000L
        else:
            time = 0
            secs = 0
        currentPoints = 0
        if spHi is not None:
            currentPoints = spHi - secs / 60.0 * spm
        if util.GetAttrs(self, 'sr', 'node', 'trainToLevel') != level:
            if util.GetAttrs(self, 'sr', 'node', 'timeLeft'):
                time = self.sr.node.timeLeft
            else:
                time = None
        self.SetTimeLeft(time)
        if ETA:
            self.endOfTraining = ETA
        else:
            self.endOfTraining = None
        self.lasttime = blue.os.GetWallclockTime()
        self.lastsecs = secs
        self.lastpoints = currentPoints
        self.timer = base.AutoTimer(1000, self.UpdateProgress)
        return currentPoints

    def UpdateHalfTrained(self):
        skill = self.rec
        if self.endOfTraining is None:
            self.timer = None
            currentPoints = skill.skillPoints
        elif self.rec.flagID == const.flagSkillInTraining:
            secs = (self.endOfTraining - blue.os.GetWallclockTime()) / 10000000L
            currentPoints = min(skill.spHi - secs / 60.0 * skill.spm, skill.spHi)
            self.GetIcon('intraining')
        else:
            currentPoints = skill.skillPoints
        currentSpL = characterskills.util.GetSPForLevelRaw(skill.skillTimeConstant, skill.skillLevel)
        if skill.skillPoints < skill.spHi:
            if skill.skillPoints > int(math.ceil(skill.spLo)):
                self.GetIcon('partial')
                if self.hilitePartiallyTrained:
                    yellowish = (238 / 255.0,
                     201 / 255.0,
                     0.0,
                     1.0)
                    self.sr.nameLevelLabel.SetTextColor(yellowish)
                    self.sr.pointsLabel.SetTextColor(yellowish)
            else:
                self.GetIcon('chapter')
            self.sr.progressBar.width = int(46 * (float(currentPoints - currentSpL) / (skill.spHi - currentSpL)))
            self.sr.progressBar.state = uiconst.UI_DISABLED
        else:
            self.GetIcon('complete')
            self.sr.progressBar.state = uiconst.UI_HIDDEN
        if self.rec.flagID == const.flagSkillInTraining:
            self.GetIcon('intraining')

    def OnSkillpointChange(self, skillPoints = None):
        if self.destroyed:
            return
        if skillPoints is None:
            skillPoints = self.rec.skillPoints
        skill = self.rec
        if skill.skillLevel >= 5:
            skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillPointsValue', skillPoints=int(skillPoints))
        else:
            skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillPointsAndNextLevelValues', skillPoints=int(skillPoints), skillPointsToNextLevel=int(skill.spHi + 0.5))
        self.sr.nameLevelLabel.text = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndRankValue', skill=skill.type.typeID, rank=int(skill.skillTimeConstant + 0.4))
        self.sr.pointsLabel.top = self.sr.nameLevelLabel.top + self.sr.nameLevelLabel.height
        self.sr.pointsLabel.text = skillPointsText

    def OnMouseEnter(self, *args):
        if self.rec.itemID is None:
            return
        SE_BaseClassCore.OnMouseEnter(self, *args)

    def OnDblClick(self, *args):
        pass

    def OnClick(self, *args):
        pass

    def ShowInfo(self, *args):
        sm.StartService('info').ShowInfo(self.rec.typeID, self.rec.itemID)

    def GetTimeLeft(self, rec):
        timeLeft = None
        if rec.skillLevel < 5 and rec.flagID == const.flagSkill:
            timeLeft = sm.StartService('godma').GetStateManager().GetTimeForTraining(rec.itemID) * 60 * const.SEC
        return timeLeft

    def SetTimeLeft(self, timeLeft):
        if self is not None and not self.destroyed and self.sr.Get('timeLeftText', None):
            if timeLeft is None:
                timeLeftText = ''
            elif timeLeft <= 0:
                timeLeftText = localization.GetByLabel('UI/SkillQueue/Skills/CompletionImminent')
            else:
                timeLeftText = localization.formatters.FormatTimeIntervalShortWritten(long(timeLeft), showFrom='day', showTo='second')
            self.sr.timeLeftText.text = timeLeftText
            self.AdjustTimerContWidth()

    def AdjustTimerContWidth(self, *args):
        self.sr.levelHeaderParent.width = max(self.sr.levelHeader1.textwidth + 18, self.sr.timeLeftText.textwidth + 18, 60)


class SkillEntry(BaseSkillEntry):
    __guid__ = 'listentry.SkillEntry'
    __nonpersistvars__ = ['selection', 'id']
    isDragObject = True

    @telemetry.ZONE_METHOD
    def Load(self, node):
        BaseSkillEntry.Load(self, node)
        data = node
        self.skillID = data.skillID
        plannedInQueue = data.Get('plannedInQueue', None)
        for i in xrange(5):
            fill = self.sr.Get('box_%s' % i)
            fill.SetRGB(*self.whiteColor)
            if data.skill.skillLevel > i:
                fill.state = uiconst.UI_DISABLED
            else:
                fill.state = uiconst.UI_HIDDEN
            if plannedInQueue and i >= data.skill.skillLevel and i <= plannedInQueue - 1:
                fill.SetRGB(*self.blueColor)
                fill.state = uiconst.UI_DISABLED
            sm.StartService('ui').StopBlink(fill)

        self.sr.nameLevelLabel.text = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndRankValue', skill=data.invtype.typeID, rank=self.rank)
        self.sr.pointsLabel.top = self.sr.nameLevelLabel.top + self.sr.nameLevelLabel.height
        self.sr.pointsLabel.text = self.skillPointsText
        self.sr.levelHeader1.text = localization.GetByLabel('UI/SkillQueue/Skills/SkillLevelWordAndValue', skillLevel=data.skill.skillLevel)
        if data.trained:
            if data.skill.flagID == const.flagSkillInTraining:
                uthread.new(self.UpdateTraining, data.skill)
            else:
                skill = data.skill
                if skill.spHi is not None:
                    timeLeft = self.GetTimeLeft(skill)
                    self.SetTimeLeft(timeLeft)
                if not self or self.destroyed:
                    return
                self.UpdateHalfTrained()
        self.AdjustTimerContWidth()
        self.sr.levelParent.width = self.sr.levels.width + const.defaultPadding

    def UpdateTraining(self, skill):
        if not self or self.destroyed:
            return
        currentPoints = BaseSkillEntry.UpdateTraining(self, skill)
        level = skill.skillLevel
        fill = self.sr.Get('box_%s' % int(level))
        fill.state = uiconst.UI_DISABLED
        fill.SetRGB(*self.lightBlueColor)
        sm.StartService('ui').BlinkSpriteA(fill, 1.0, time=1000.0, maxCount=0, passColor=0, minA=0.5)
        self.OnSkillpointChange(currentPoints)
        self.UpdateHalfTrained()
        self.AdjustTimerContWidth()

    def GetMenu(self):
        m = []
        if self.rec.itemID is not None:
            m += sm.GetService('skillqueue').GetAddMenuForSkillEntries(self.rec)
            m += sm.StartService('menu').GetMenuFormItemIDTypeID(self.rec.itemID, self.rec.typeID, ignoreMarketDetails=0)
        elif self.rec.typeID is not None:
            m += sm.StartService('menu').GetMenuFormItemIDTypeID(None, self.rec.typeID, ignoreMarketDetails=0)
        if eve.session.role & ROLE_GMH == ROLE_GMH:
            m.extend(sm.GetService('info').GetGMGiveSkillMenu(self.skillID))
        return m

    def GetHint(self):
        return cfg.invtypes.Get(self.skillID).description

    def UpdateProgress(self):
        try:
            if self.endOfTraining is None:
                self.timer = None
                return
            ms = blue.os.TimeDiffInMs(self.lasttime, blue.os.GetWallclockTime())
            timeEndured = blue.os.GetWallclockTime() - self.lasttime
            skill = self.rec
            timeLeft = self.endOfTraining - blue.os.GetWallclockTime()
            secs = timeLeft / 10000000L
            currentPoints = min(skill.spHi - secs / 60.0 * skill.spm, skill.spHi)
            self.OnSkillpointChange(currentPoints)
            self.SetTimeLeft(timeLeft)
            self.UpdateHalfTrained()
        except:
            self.timer = None
            log.LogException()
            sys.exc_clear()

    def GetDragData(self, *args):
        return [self.sr.node]

    def GetDynamicHeight(node, width):
        name = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndRankValue', skill=node.invtype.typeID, rank=int(node.skill.skillTimeConstant + 0.4))
        nameWidth, nameHeight = uicontrols.EveLabelMedium.MeasureTextSize(name, maxLines=1)
        if node.trained:
            skillPoints = node.skill.skillPoints
            skill = node.skill
            if skill.skillLevel >= 5:
                skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillPointsValue', skillPoints=int(skillPoints))
            else:
                skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillPointsAndNextLevelValues', skillPoints=int(skillPoints), skillPointsToNextLevel=int(skill.spHi + 0.5))
        elif node.meetRequirements:
            skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillRequirementsMet')
        else:
            skillPointsText = localization.GetByLabel('UI/SkillQueue/Skills/SkillRequirementsNotMet')
        pointsWidth, pointsHeight = uicontrols.EveLabelMedium.MeasureTextSize(skillPointsText, maxLines=1)
        return max(36, nameHeight + pointsHeight + 2)


class SkillLevels(uiprimitives.Container):
    """
    This is a skill level control. Not used in the skill queue though but could be used there later
    if we added some event handling.
    """
    __guid__ = 'uicls.SkillLevels'
    default_align = uiconst.TORIGHT
    default_state = uiconst.UI_NORMAL
    default_width = 47
    default_height = 10
    default_frameColor = (1.0, 1.0, 1.0, 0.3)
    default_bgColor = (1.0, 1.0, 1.0, 0.0)
    default_barColor = (1.0, 1.0, 1.0, 0.5)

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.get('typeID', None)
        self.groupID = attributes.get('groupID', None)
        self.barColor = attributes.get('barColor', self.default_barColor)
        frameColor = attributes.get('frameColor', self.default_frameColor)
        bgColor = attributes.get('bgColor', self.default_bgColor)
        self.bgFrame = Frame(bgParent=self, color=frameColor)
        self.bgFill = Fill(bgParent=self, color=bgColor)
        self.bars = []
        for i in xrange(5):
            padLeft = 2 if i == 0 else 1
            bar = uiprimitives.Fill(parent=self, name='level%d' % i, align=uiconst.TOLEFT_PROP, color=self.barColor, width=0.2, padding=(padLeft,
             2,
             0,
             2))
            self.bars.append(bar)

        self.Update()

    def Update(self):
        skill = self.GetSkill()
        self.SetLevel(skill)

    def SetBarPadding(self, padding):
        for i, bar in enumerate(self.bars):
            if i == 0:
                bar.padLeft = padding + 1
            else:
                bar.padLeft = padding

    def GetSkill(self):
        return sm.GetService('skills').GetMySkillsFromTypeID(self.typeID)

    def SetLevel(self, skill):
        skillQueue = sm.GetService('skillqueue').GetQueue()
        level = skill.skillLevel if skill else 0
        if level == 0:
            hint = localization.GetByLabel('UI/SkillQueue/Skills/SkillNotTrained')
        elif level == 5:
            hint = localization.GetByLabel('UI/SkillQueue/Skills/SkillAtMaximumLevel')
        else:
            hint = localization.GetByLabel('UI/SkillQueue/Skills/SkillAtLevel', skillLevel=level)
        inTraining = 0
        plannedInQueue = 0
        for skillTypeID, skillLevel in skillQueue:
            if skillTypeID == self.typeID:
                plannedInQueue = skillLevel

        if hasattr(skill, 'flagID') and skill.flagID == const.flagSkillInTraining:
            inTraining = 1
        for i in xrange(5):
            fill = self.bars[i]
            fill.SetRGB(*self.barColor)
            if level > i:
                fill.display = True
            else:
                fill.display = False
            if plannedInQueue and i >= level and i <= plannedInQueue - 1:
                hint = localization.GetByLabel('UI/SkillQueue/Skills/SkillTrainingToLevel', skillLevel=plannedInQueue)
                fill.SetRGB(*BLUE_COLOR)
                fill.display = True
            if inTraining and i == level:
                fill.SetRGB(*LIGHTBLUE_COLOR)
                sm.GetService('ui').BlinkSpriteA(fill, 1.0, time=1000.0, maxCount=0, passColor=0, minA=0.5)

        self.hint = hint
