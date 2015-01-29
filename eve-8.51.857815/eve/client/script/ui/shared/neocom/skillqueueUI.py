#Embedded file name: eve/client/script/ui/shared/neocom\skillqueueUI.py
"""
This file contains the UI needed to view and change your skill queue!
"""
import blue
from carbonui.control.scrollentries import SE_BaseClassCore
from carbonui.primitives.base import ReverseScaleDpi
from carbonui.primitives.frame import Frame
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from characterskills.util import DISPLAY_SKILLQUEUE_LENGTH, GetSkillQueueTimeLength, HasShortSkillqueue, IsTrialRestricted, GetSPForLevelRaw
import uiprimitives
import uicontrols
import util
import uix
import uthread
import math
import listentry
import base
import sys
import carbonui.const as uiconst
import log
import uicls
import localization
import form
import uiutil
import telemetry
from carbon.common.script.sys.service import ROLE_GMH
from carbonui.control.dragResizeCont import DragResizeCont
from eve.client.script.ui.shared.monetization.trialPopup import ORIGIN_CHARACTERSHEET
TIMELINE_BASEHEIGHT = 16
FILTER_ALL = 0
FILTER_PARTIAL = 1
FILTER_EXCLUDELVL5 = 2
FITSINQUEUE_DEFAULT = 0

class SkillQueue(uicontrols.Window):
    __guid__ = 'form.SkillQueue'
    __notifyevents__ = ['OnSkillFinished',
     'OnSkillStarted',
     'OnSkillPaused',
     'OnSkillQueueTrimmed',
     'OnGodmaSkillInjected',
     'OnSkillQueueRefreshed',
     'OnGodmaSkillTrained',
     'OnUIRefresh']
    default_windowID = 'trainingqueue'
    default_captionLabelPath = 'UI/SkillQueue/TrainingQueue'
    default_descriptionLabelPath = 'Tooltips/Neocom/SkillTrainingQueue_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/trainingqueue.png'
    COLOR_SKILL_1 = (0.21, 0.62, 0.74, 1.0)
    COLOR_SKILL_2 = (0.0, 0.52, 0.67, 1.0)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.godma = sm.GetService('godma')
        self.skillHandler = self.godma.GetSkillHandler()
        self.SetTopparentHeight(0)
        self.queueLastApplied = []
        self.isSaving = 0
        self.maxSkillqueueLength = GetSkillQueueTimeLength(session.userType)
        self.minWidth = 275
        self.SetMinSize([self.minWidth, 350])
        self.expanded = 0
        self.skillTimer = 0
        self.barTimer = 0
        self.skillQueueSvc = sm.GetService('skillqueue')
        self.ConstructLayout()
        self.Load()
        uthread.new(self._OnResize)

    @telemetry.ZONE_METHOD
    def Load(self, *args):
        """
            Performs the initialization of the window's data by loading
            the current session's character's base attributes, clamping them to
            conform to basic business rules (for the player's convenience),
            and setting up the UI's initial display data.
        """
        self.sr.skillCombo.SelectItemByValue(settings.user.ui.Get('skillqueue_comboFilter', FILTER_ALL))
        self.expanded = settings.user.ui.Get('skillqueue_skillsExpanded', 1)
        if self.expanded:
            self.SetMinSize([700, 350])
            self.OnClickRightExpander()
        else:
            self.OnClickLeftExpander()
        self.SetTime()
        self.skillQueueSvc.BeginTransaction()
        self.queueLastApplied = self.skillQueueSvc.GetQueue()
        parallelCalls = []
        parallelCalls.append((self.LoadQueue, ()))
        parallelCalls.append((self.LoadSkills, ()))
        uthread.parallel(parallelCalls)
        inTraining = sm.StartService('skills').SkillInTraining()
        if not inTraining:
            self.GrayButton(self.sr.pauseBtn, gray=1)
        uthread.new(self.StartBars)
        uthread.new(self.LoopTimers)

    @telemetry.ZONE_METHOD
    def ConstructLayout(self):
        """
            This method lays out the elements that comprise the skill queue window,
            assigning them initial display values that make sense in the case that
            Load() later fails.
            Performs no data initialization.
        """
        self.sr.leftOuterPar = DragResizeCont(name='leftOuterPar', parent=self.sr.main, align=uiconst.TOLEFT_PROP, settingsID='skillQueue', minSize=0.35, maxSize=0.7)
        self.sr.main.padLeft = self.sr.main.padRight = const.defaultPadding
        self.sr.rightOuterPar = uiprimitives.Container(name='rightOuterPar', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.leftFooterPar = uiprimitives.Container(parent=self.sr.leftOuterPar, align=uiconst.TOBOTTOM, height=26)
        self.sr.rightFooterPar = uiprimitives.Container(parent=self.sr.rightOuterPar, align=uiconst.TOBOTTOM, height=26)
        self.sr.leftHeader = uiprimitives.Container(parent=self.sr.leftOuterPar, align=uiconst.TOTOP, height=62, top=0, clipChildren=1)
        self.sr.leftScroll = uicontrols.Scroll(parent=self.sr.leftOuterPar, padTop=const.defaultPadding, padBottom=const.defaultPadding)
        self.sr.leftScroll.SelectAll = self.DoNothing
        self.sr.leftScroll.sr.content.OnDropData = self.DoRemove
        self.sr.leftScroll.sr.content.AddSkillToQueue = self.AddSkillToQueue
        self.sr.rightHeader = uiprimitives.Container(parent=self.sr.rightOuterPar, align=uiconst.TOTOP, height=20, padBottom=2, clipChildren=1)
        self.sr.rightHeader._OnSizeChange_NoBlock = self.OnRightHeaderSizeChanged
        self.sr.sqFinishesText = uicontrols.EveLabelSmall(parent=self.sr.rightHeader, left=4, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMLEFT)
        self.sr.sqTimeText = uicontrols.EveLabelSmall(parent=self.sr.rightHeader, left=4, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMRIGHT)
        mainBarCont = uiprimitives.Container(name='mainBarCont', parent=self.sr.rightOuterPar, align=uiconst.TOTOP, height=19, padLeft=const.defaultPadding, padRight=const.defaultPadding)
        self.sr.barCont = uiprimitives.Container(name='barCont', parent=mainBarCont, align=uiconst.TOTOP, height=19)
        self.sr.arrowCont = uiprimitives.Container(name='arrowCont', parent=self.sr.barCont, align=uiconst.TORIGHT, width=5, state=uiconst.UI_HIDDEN, idx=0)
        self.sr.mainBar = uiprimitives.Container(name='mainBar', parent=self.sr.barCont, align=uiconst.TOALL, pos=(0, 0, 0, 0), clipChildren=1)
        self.sr.timeLine = uiprimitives.Container(name='timeLine', parent=self.sr.rightOuterPar, align=uiconst.TOTOP, height=TIMELINE_BASEHEIGHT, padLeft=const.defaultPadding, padRight=const.defaultPadding, clipChildren=True)
        sprite = uiprimitives.Sprite(name='arrow', parent=self.sr.arrowCont, align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/whiteArrow.png')
        sprite.rectTop = 0
        sprite.rectLeft = 0
        sprite.rectWidth = 9
        sprite.rectHeight = 19
        self.sr.arrowSprite = sprite
        self.sr.rightScroll = uicontrols.Scroll(parent=self.sr.rightOuterPar, padTop=const.defaultPadding, padBottom=const.defaultPadding)
        self.sr.rightScroll.sr.content.OnDropData = self.DoDropData
        self.sr.rightScroll.sr.content.OnDragEnter = self.OnContentDragEnter
        self.sr.rightScroll.sr.content.OnDragExit = self.OnContentDragExit
        self.sr.rightScroll.sr.content.RemoveSkillFromQueue = self.RemoveSkillFromQueue
        comboOptions = [(localization.GetByLabel('UI/SkillQueue/MySkills'), FILTER_ALL), (localization.GetByLabel('UI/SkillQueue/MyPartiallyTrainedSkills'), FILTER_PARTIAL), (localization.GetByLabel('UI/SkillQueue/ExcludeFullyTrainedSkills'), FILTER_EXCLUDELVL5)]
        self.sr.skillCombo = uicontrols.Combo(label='', parent=self.sr.leftHeader, options=comboOptions, name='', align=uiconst.TOPLEFT, pos=(2, 22, 0, 0), callback=self.OnComboChange, width=200)
        if HasShortSkillqueue(session.userType):
            self.sr.leftHeader.height = 82
            fitsChecked = settings.user.ui.Get('skillqueue_fitsinqueue', FITSINQUEUE_DEFAULT)
            cb = uicontrols.Checkbox(text=localization.GetByLabel('UI/SkillQueue/FitInQueueTimeframe'), parent=self.sr.leftHeader, configName='skillqueue_fitsinqueue', retval=None, checked=fitsChecked, callback=self.OnCheckboxChange, align=uiconst.TOPLEFT, pos=(0,
             self.sr.skillCombo.top + self.sr.skillCombo.height + const.defaultPadding,
             400,
             0))
            self.sr.fitsCheckbox = cb
            top = cb.top + cb.height
        else:
            top = self.sr.skillCombo.top + self.sr.skillCombo.height + const.defaultPadding
        self.quickFilter = uicls.QuickFilterEdit(parent=self.sr.leftHeader, pos=(2,
         top,
         200,
         0))
        self.quickFilter.ReloadFunction = self.ReloadSkills
        applyBtn = uicontrols.Button(parent=self.sr.rightFooterPar, name='trainingQueueApplyBtn', label=localization.GetByLabel('UI/Commands/Apply'), pos=(const.defaultPadding,
         3,
         0,
         0), func=self.SaveChanges)
        self.sr.pauseBtn = uicontrols.Button(parent=self.sr.rightFooterPar, name='trainingQueuePauseBtn', label=localization.GetByLabel('UI/Commands/Pause'), pos=(applyBtn.left + applyBtn.width + 2,
         3,
         0,
         0), func=self.PauseTraining)
        removeBtn = uicontrols.Button(parent=self.sr.rightFooterPar, name='trainingQueueRemoveBtn', label=localization.GetByLabel('UI/Commands/Remove'), pos=(const.defaultPadding,
         3,
         0,
         0), align=uiconst.TOPRIGHT, func=self.RemoveSkillFromQueue)
        addBtn = uicontrols.Button(parent=self.sr.leftFooterPar, name='trainingQueueAddBtn', label=localization.GetByLabel('UI/Commands/AddItem'), top=3, align=uiconst.CENTERTOP, func=self.AddSkillToQueue)
        self.sr.leftExpander = uicontrols.Icon(parent=self.sr.leftOuterPar, idx=0, size=16, state=uiconst.UI_NORMAL, icon='ui_1_16_99', top=2)
        self.sr.rightExpander = uicontrols.Icon(parent=self.sr.rightOuterPar, idx=0, size=16, state=uiconst.UI_HIDDEN, icon='ui_1_16_100', top=2)
        self.sr.leftExpander.OnClick = self.OnClickLeftExpander
        self.sr.rightExpander.OnClick = self.OnClickRightExpander

    def OnComboChange(self, combo, config, value):
        settings.user.ui.Set('skillqueue_comboFilter', value)
        self.ReloadSkills()

    def OnCheckboxChange(self, cb, *args):
        """
            Filtering the skills
        """
        settings.user.ui.Set(cb.name, bool(cb.checked))
        self.ReloadSkills()

    def GrayButton(self, btn, gray = 1):
        inTraining = sm.StartService('skills').SkillInTraining()
        if gray and not inTraining:
            btn.SetLabel(['<color=gray>', localization.GetByLabel('UI/Commands/Pause')])
            btn.state = uiconst.UI_DISABLED
        else:
            btn.SetLabel(localization.GetByLabel('UI/Commands/Pause'))
            btn.state = uiconst.UI_NORMAL

    def OnClickLeftExpander(self, *args):
        self.SetupCollapsed()
        self._OnResize()

    def SetupCollapsed(self):
        self.SetMinSize([self.minWidth, 350])
        self.expanded = 0
        settings.user.ui.Set('skillqueue_skillsExpanded', 0)
        self.sr.leftOuterPar.state = uiconst.UI_HIDDEN
        self.sr.rightExpander.state = uiconst.UI_NORMAL

    def OnClickRightExpander(self, *args):
        self.SetupExpanded()
        self.LoadSkills()
        self._OnResize()

    def SetupExpanded(self):
        self.SetMinSize([700, 350])
        self.expanded = 1
        settings.user.ui.Set('skillqueue_skillsExpanded', 1)
        self.sr.leftOuterPar.state = uiconst.UI_PICKCHILDREN
        self.sr.rightExpander.state = uiconst.UI_HIDDEN

    def SaveChanges(self, *args):
        """
            This is where the changes to the queue are saved and the queue started
            When changes to the queue have been saved, we will need to scatter it 
            to let the character sheet know of the changes (will probably not do it here though)
        """
        if self.isSaving == 1:
            return
        queue = self.skillQueueSvc.GetQueue()
        try:
            self.isSaving = 1
            self.skillQueueSvc.CommitTransaction()
            self.queueLastApplied = queue
        finally:
            if self and not self.destroyed:
                self.skillQueueSvc.BeginTransaction()
                self.isSaving = 0

    def PauseTraining(self, *args):
        inTraining = sm.StartService('skills').SkillInTraining()
        if inTraining:
            sm.StartService('skills').AbortTrain(inTraining)

    def _OnClose(self, *args):
        if self.isSaving:
            return
        queue = self.skillQueueSvc.GetQueue()
        if queue != self.queueLastApplied:
            uthread.new(self.ConfirmSavingOnClose)
        else:
            self.skillQueueSvc.RollbackTransaction()
        self.barTimer = None
        self.barUpdatingTimer = None

    def ConfirmSavingOnClose(self):
        if eve.Message('QueueSaveChangesOnClose', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            queue = self.skillQueueSvc.GetQueue()
            self.skillQueueSvc.CommitTransaction()
        else:
            self.skillQueueSvc.RollbackTransaction()

    def ReloadSkills(self, force = 0, time = 1000):
        if self.expanded == 1 or force:
            self.skillTimer = base.AutoTimer(time, self.LoadSkills)

    @telemetry.ZONE_METHOD
    def LoadSkills(self):
        """
            Load the list of skills I HAVE on the left hand side
        """
        self.skillTimer = 0
        groups = sm.GetService('skills').GetSkillGroups()
        scrolllist = []
        queueLength = self.skillQueueSvc.GetTrainingLengthOfQueue()
        timeLeftInQueue = max(0, self.maxSkillqueueLength - queueLength)
        queue = self.skillQueueSvc.GetQueue()
        skillsInQueue = [ skillID for skillID, level in queue ]
        fitsChecked = HasShortSkillqueue(session.userType) and settings.user.ui.Get('skillqueue_fitsinqueue', FITSINQUEUE_DEFAULT)
        partialChecked = settings.user.ui.Get('skillqueue_comboFilter', FILTER_ALL) == FILTER_PARTIAL
        excludeLvl5 = settings.user.ui.Get('skillqueue_comboFilter', FILTER_ALL) == FILTER_EXCLUDELVL5
        for group, skills, untrained, intraining, inqueue, points in groups:
            if not len(skills):
                continue
            skills.sort(lambda x, y: cmp(cfg.invtypes.Get(x.typeID).name, cfg.invtypes.Get(y.typeID).name))
            filteredSkills = []
            if fitsChecked or partialChecked or excludeLvl5:
                for skill in skills:
                    if excludeLvl5:
                        if skill.skillLevel >= 5:
                            continue
                    if partialChecked:
                        if skill.skillPoints >= skill.spHi or not skill.skillPoints > int(math.ceil(skill.spLo)):
                            continue
                    if fitsChecked:
                        timeLeft = 0
                        if skill.typeID in skillsInQueue:
                            nextLevel = self.skillQueueSvc.FindNextLevel(skill.typeID, skill.skillLevel, queue)
                        else:
                            nextLevel = skill.skillLevel + 1
                        if nextLevel:
                            if nextLevel <= 5:
                                totalTime, timeLeft, _ = self.skillQueueSvc.GetTrainingLengthOfSkill(skill.typeID, nextLevel)
                                if timeLeft > timeLeftInQueue:
                                    continue
                                skill.fitInfo = (nextLevel, timeLeft)
                            else:
                                continue
                    filteredSkills.append(skill)

                skills = filteredSkills
            myFilter = self.quickFilter.GetValue()
            if len(myFilter):
                skills = uiutil.NiceFilter(self.quickFilter.QuickFilter, skills)
            if len(skills) < 1:
                continue
            label = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillGroupOverviewSimple', groupName=group.groupName, skills=len(skills), points=int(points), skillsInQueue='')
            data = {'GetSubContent': self.GetSubContent,
             'label': label,
             'groupItems': skills,
             'inqueue': inqueue,
             'id': ('skillqueue', group.groupID),
             'tabs': [],
             'state': 'locked',
             'showicon': 'hide',
             'showlen': 0,
             'DropData': self.RemoveToGroup,
             'allowGuids': ['listentry.SkillQueueSkillEntry'],
             'BlockOpenWindow': 1}
            scrolllist.append(listentry.Get('Group', data))

        pos = self.sr.leftScroll.GetScrollProportion()
        self.sr.leftScroll.sr.id = 'skillqueue_leftview'
        self.sr.leftScroll.Load(contentList=scrolllist, headers=[], scrollTo=pos, noContentHint=localization.GetByLabel('UI/SkillQueue/NoResultsForFilters'))

    def GetSubContent(self, data, *args):
        """
            Gets the skills in the group
        """
        scrolllist = []
        queue = self.skillQueueSvc.GetQueue()
        skillsInQueue = [ skillID for skillID, level in queue ]
        skillsInGroup = localization.util.Sort(data.groupItems, key=lambda x: cfg.invtypes.Get(x.typeID).name)
        isAccelerated = False
        for skill in skillsInGroup:
            invtype = cfg.invtypes.Get(skill.typeID)
            fitInfo = getattr(skill, 'fitInfo', None)
            if fitInfo is not None:
                nextLevel = fitInfo[0]
                timeLeft = fitInfo[1]
            else:
                skillID = invtype.id
                mySkillLevel = skill.skillLevel
                if skillID in skillsInQueue:
                    nextLevel = self.skillQueueSvc.FindNextLevel(skillID, skill.skillLevel, queue)
                else:
                    nextLevel = mySkillLevel + 1
                timeLeft = 0
                if nextLevel and nextLevel <= 5:
                    totalTime, timeLeft, isAccelerated = self.skillQueueSvc.GetTrainingLengthOfSkill(skillID, nextLevel)
            data = {}
            data['invtype'] = invtype
            data['skill'] = skill
            data['trained'] = skill.itemID != None
            data['timeLeft'] = timeLeft
            data['skillID'] = invtype.id
            data['trainToLevel'] = nextLevel - 1
            data['currentLevel'] = skill.skillLevel
            data['inTraining'] = [0, 1][skill.flagID == const.flagSkillInTraining]
            scrolllist.append(listentry.Get('SkillQueueSkillEntry', data))
            if hasattr(skill, 'flagID') and skill.flagID == const.flagSkillInTraining:
                sm.StartService('godma').GetStateManager().GetEndOfTraining(skill.itemID)

        return scrolllist

    def ReloadQueue(self):
        self.queueTimer = base.AutoTimer(1000, self.LoadQueue)

    @telemetry.ZONE_METHOD
    def LoadQueue(self):
        """
            Loads the planned queue.
            At startup this will be the queue that's on the server, but when the queue
            is loaded again the planned queue is loaded, which might not be the same as 
            the server queue
        """
        self.queueTimer = 0
        mySkills = sm.StartService('skills').GetMyGodmaItem().skills
        queue = self.skillQueueSvc.GetQueue()
        allTrainingLengths = self.skillQueueSvc.GetAllTrainingLengths()
        scrolllist = []
        for skillID, nextLevel in queue:
            invtype = cfg.invtypes.Get(skillID)
            skill = mySkills.get(skillID, None)
            if skill is None:
                self.skillQueueSvc.RemoveSkillFromQueue(skillID, nextLevel)
                continue
            time = allTrainingLengths.get((invtype.id, nextLevel), [0, 0])
            entry = self.GetRightEntry(invtype, skill, nextLevel, time[1], time[2])
            scrolllist.append(entry)

        lastDropEntry = listentry.Get(decoClass=SkillQueueLastDropEntry)
        scrolllist.append(lastDropEntry)
        self.sr.rightScroll.Load(contentList=scrolllist)
        self.UpdateTime()

    @telemetry.ZONE_METHOD
    def GetRightEntry(self, invtype, skill, trainToLevel, timeLeft, isAccelerated):
        """
            Set up an entry for the skill queue (the right scroll) 
            ARGUMENTS:
                invtype         :   the inventory of the item (the skill)
                skill           :   information about the skill
                trainToLevel    :   level to train the skill to
                                
            RETURNS:
                A SkillQueueSkillEntry that contains all the data 
                and is ready to be loaded into the skill queue
        """
        data = {}
        data['invtype'] = invtype
        data['skill'] = skill
        data['trained'] = skill.itemID != None
        data['inQueue'] = 1
        data['trainToLevel'] = trainToLevel
        data['currentLevel'] = getattr(skill, 'skillLevel', 0)
        data['timeLeft'] = timeLeft
        data['skillID'] = invtype.id
        data['inTraining'] = [0, 1][skill.flagID == const.flagSkillInTraining]
        data['isAccelerated'] = isAccelerated
        entry = listentry.Get('SkillQueueSkillEntry', data)
        return entry

    def UpdateTime(self):
        """
            Update the total timers.
            This is called when changes have been made to the queue so we need to recalculate
            the times.
        """
        self.SetTime()
        self.DrawBars()

    @telemetry.ZONE_METHOD
    def SetTime(self):
        timeEnd = self.skillQueueSvc.GetTrainingEndTimeOfQueue()
        originalTimeEnd = timeEnd
        inTraining = sm.StartService('skills').SkillInTraining()
        if inTraining and self.skillQueueSvc.FindInQueue(inTraining.typeID, inTraining.skillLevel + 1) > 0:
            fullTrainingTime = self.skillQueueSvc.GetTrainingLengthOfSkill(inTraining.typeID, inTraining.skillLevel + 1)
            ETA = inTraining.skillTrainingEnd
            if ETA is not None:
                timeEnd -= fullTrainingTime[1]
                leftTime = ETA - blue.os.GetWallclockTime()
                timeEnd += leftTime
        timeEnd = long(timeEnd)
        if timeEnd > blue.os.GetWallclockTime():
            myDate = util.FmtDate(timeEnd, 'sn')
            myTime = util.FmtDate(timeEnd, 'ns')
            self.sr.sqFinishesText.text = localization.GetByLabel('UI/SkillQueue/QueueFinishesOn', date=myDate, time=myTime)
            self.sr.rightHeader.height = max(self.sr.rightHeader.height, self.sr.sqFinishesText.top + self.sr.sqFinishesText.height)
        timeLeft = timeEnd - blue.os.GetWallclockTime()
        if timeLeft < 0:
            timeLeftText = ''
            currentTime = blue.os.GetWallclockTime()
            log.LogTraceback('Negative value in SetTime in skillqueue')
        else:
            timeLeftText = localization.formatters.FormatTimeIntervalShortWritten(long(timeLeft), showFrom='day', showTo='second')
        self.sr.sqTimeText.text = timeLeftText
        self.UpdateSQTimeTextSizes()
        self.allTrainingLengths = self.skillQueueSvc.GetAllTrainingLengths()
        self.queueEnds = timeEnd
        self.queueTimeLeft = timeLeft
        self.lasttime = blue.os.GetWallclockTime()

    def OnRightHeaderSizeChanged(self, *args, **kwds):
        if self.destroyed:
            return
        self.UpdateSQTimeTextSizes()

    def UpdateSQTimeTextSizes(self):
        if self.destroyed or not self.sr.rightHeader:
            return
        rightSideWidth = ReverseScaleDpi(self.sr.rightHeader.displayWidth)
        self.sr.sqFinishesText.width = rightSideWidth - self.sr.sqTimeText.textwidth - self.sr.sqTimeText.left - self.sr.sqFinishesText.left - 10
        self.sr.rightHeader.height = max(20, self.sr.sqTimeText.top + self.sr.sqTimeText.height, self.sr.sqFinishesText.height + self.sr.sqFinishesText.top)

    @telemetry.ZONE_METHOD
    def LoopTimers(self, *args):
        """
            Updating the time left and finish time
            Later, we will have bars that need updating and that will be done here
            This update happens too frequently as it is, and we will need to 
            find the right interval
        """
        while self and not self.destroyed:
            inTraining = sm.StartService('skills').SkillInTraining()
            now = blue.os.GetWallclockTime()
            lasttime = getattr(self, 'lasttime', now)
            diff = now - lasttime
            queueEnds = getattr(self, 'queueEnds', None)
            timeLeft = getattr(self, 'queueTimeLeft', None)
            if queueEnds is not None and queueEnds >= now and timeLeft is not None:
                if inTraining and self.skillQueueSvc.FindInQueue(inTraining.typeID, inTraining.skillLevel + 1) is not None:
                    timeLeft = timeLeft - diff
                    self.queueTimeLeft = timeLeft
                else:
                    queueEnds = self.queueEnds + diff
                    self.queueEnds = queueEnds
                self.lasttime = now
                if queueEnds > blue.os.GetWallclockTime():
                    myDate = util.FmtDate(queueEnds, 'sn')
                    myTime = util.FmtDate(queueEnds, 'ns')
                    self.sr.sqFinishesText.text = localization.GetByLabel('UI/SkillQueue/QueueFinishesOn', date=myDate, time=myTime)
                    self.sr.rightHeader.height = max(self.sr.rightHeader.height, self.sr.sqFinishesText.top + self.sr.sqFinishesText.height)
                timeLeft = max(0, timeLeft)
                timeLeftText = localization.formatters.FormatTimeIntervalShortWritten(long(timeLeft), showFrom='day', showTo='second')
                self.sr.sqTimeText.text = timeLeftText
                self.UpdatingBars()
            else:
                self.sr.sqFinishesText.text = ''
                self.sr.sqTimeText.text = ''
            self.UpdateSQTimeTextSizes()
            blue.pyos.synchro.SleepWallclock(1000)

    def StartBars(self):
        while self and not self.destroyed:
            if util.GetAttrs(self, 'sr', 'mainBar') and self.sr.mainBar.absoluteRight - self.sr.mainBar.absoluteLeft > 0:
                break
            blue.pyos.synchro.SleepWallclock(500)

        if not self or self.destroyed:
            return
        self.DrawBars()

    def UpdatingBars(self):
        self.barUpdatingTimer = base.AutoTimer(1000, self.DrawBars, (1,))

    def RedrawBars(self):
        self.barTimer = base.AutoTimer(1000, self.DrawBars)

    @telemetry.ZONE_METHOD
    def DrawBars(self, updating = 0):
        bar = self.sr.mainBar
        if bar is None or bar.destroyed:
            return
        l, t, w, h = bar.GetAbsolute()
        if w <= 0:
            return
        inTraining = sm.StartService('skills').SkillInTraining()
        if updating and inTraining is None:
            return
        self.barTimer = 0
        self.barUpdatingTimer = 0
        barWidth = w
        if getattr(self, 'timelineCont', None) and not self.timelineCont.destroyed:
            self.timelineCont.FlushLine()
        else:
            self.timelineCont = TimelineContainer(parent=self.sr.mainBar, barHeight=19)
        uix.Flush(self.sr.timeLine)
        percentages = {}
        for item in self.allTrainingLengths.iteritems():
            key, value = item
            time = value[1]
            if inTraining and key[0] == inTraining.typeID and key[1] == inTraining.skillLevel + 1:
                ETA = inTraining.skillTrainingEnd
                if ETA is not None:
                    time = float(ETA - blue.os.GetWallclockTime())
            per = time / DISPLAY_SKILLQUEUE_LENGTH
            percentages[key] = per

        hours = DISPLAY_SKILLQUEUE_LENGTH / const.HOUR
        interval = barWidth / float(hours)
        left = 0
        for i in xrange(hours + 1):
            left = min(barWidth - 1, int(i * interval))
            uiprimitives.Line(parent=self.sr.timeLine, align=uiconst.RELATIVE, weight=1, left=left, width=1, height=5)

        txt0 = uicontrols.EveHeaderSmall(text='0', parent=self.sr.timeLine, top=5, left=0, state=uiconst.UI_NORMAL)
        txt12 = uicontrols.EveHeaderSmall(text='12', parent=self.sr.timeLine, top=5, left=int(interval * 12) - 5, state=uiconst.UI_NORMAL)
        txt24 = uicontrols.EveHeaderSmall(text='24', parent=self.sr.timeLine, top=5, state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        self.sr.timeLine.height = max(TIMELINE_BASEHEIGHT, txt24.height + 5)
        colors = [self.COLOR_SKILL_1, self.COLOR_SKILL_2]
        queue = self.skillQueueSvc.GetQueue()
        left = 0
        counter = 0
        barInfo = []
        color = 1
        f = None
        for key in queue:
            color = int(not color)
            realColor = colors[color]
            percentage = percentages.get(key, 0.0)
            width = max(2, percentage * barWidth)
            newLeft = left + width
            self.timelineCont.AddPoint(left, color=(realColor[0],
             realColor[1],
             realColor[2],
             1.0))
            self.timelineCont.AddPoint(newLeft, color=(realColor[0],
             realColor[1],
             realColor[2],
             1.0))
            barInfo.append((width, left, colors[color]))
            left = newLeft
            counter += 1

        uiprimitives.Fill(parent=bar, align=uiconst.TOTOP, color=(0.2, 0.2, 0.2, 1), height=19, state=uiconst.UI_DISABLED)
        if barWidth and left > barWidth:
            self.sr.arrowCont.state = uiconst.UI_DISABLED
            self.sr.arrowSprite.color.SetRGB(colors[color][0], colors[color][1], colors[color][2])
            if f is not None:
                f.align = uiconst.TOALL
                f.width = 0
        else:
            self.sr.arrowCont.state = uiconst.UI_HIDDEN
        self.UpdateBars(barInfo)

    def UpdateBars(self, barInfo):
        if not barInfo:
            return
        barInfoLength = len(barInfo)
        for counter, entry in enumerate(self.sr.rightScroll.GetNodes()):
            if entry.__guid__ != 'listentry.SkillQueueSkillEntry':
                continue
            barInfoLength = len(barInfo)
            if counter > barInfoLength - 1:
                return
            self.SetBarInfo(entry, barInfo[counter])
            if entry.panel is None or counter >= barInfoLength:
                continue
            entry.panel.UpdateBar()

    def SetBarInfo(self, entry, barInfo):
        width, left, color = barInfo
        entry.barWidth = width
        entry.barLeft = left
        entry.barColor = color

    def AddSkillToQueue(self, *args):
        """
            Adding skill with the "Add" button
        """
        queue = self.skillQueueSvc.GetQueue()
        selected = self.sr.leftScroll.GetSelected()
        try:
            for entry in selected:
                skillAdded = self.AddSkillThroughSkillEntry(entry, queue)
                if skillAdded:
                    self.ChangeTimesOnEntriesInSkillList(nodeList=[entry])

        finally:
            self.UpdateTime()

    def AddSkillThroughSkillEntry(self, data, queue, idx = -1, refresh = 0):
        """
            SkillEntry and SkillQueueSkillEntry are very similar. This function is used
            to add a skill to the skill queue if the entry it's coming from 
            either SkillEntry or SkillQueueSkillEntry
        
            ARGUMENTS:
                data:   KeyVal with information on the skill
                queue:  the current skill queue
                idx :   the skill position in the queue (idx==-1 -> last)
                                
            RETURNS:
                False if the skill was not added
                True if the skill was added
        """
        if not data.Get('meetRequirements', 0):
            return False
        nextLevel = self.skillQueueSvc.FindNextLevel(data.skillID, data.skill.skillLevel, queue)
        if nextLevel is None or nextLevel > 5:
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/SkillQueue/SkillFullyPlanned')})
            return False
        self.DoAddSkill(data.invtype, data.skill, nextLevel, idx)
        if settings.user.ui.Get('skillqueue_fitsinqueue', FITSINQUEUE_DEFAULT):
            self.ReloadSkills(time=2000)
        if refresh:
            self.UpdateTime()
            self.ReloadEntriesIfNeeded()
        return True

    def AddSkillsThroughOtherEntry(self, skillID, idx, queue, nextLevel = None, refresh = 0):
        mySkills = sm.StartService('skills').GetMyGodmaItem().skills
        skill = mySkills.get(skillID, None)
        if skill is None:
            raise UserError('CustomNotify', {'notify': localization.GetByLabel('UI/SkillQueue/DoNotHaveSkill')})
        if nextLevel is None:
            nextLevel = self.skillQueueSvc.FindNextLevel(skillID, skill.skillLevel, queue)
        if nextLevel > 5:
            return
        invtype = cfg.invtypes.Get(skillID)
        self.DoAddSkill(invtype, skill, nextLevel, idx)
        if settings.user.ui.Get('skillqueue_fitsinqueue', FITSINQUEUE_DEFAULT):
            self.ReloadSkills(time=2000)
        if refresh:
            self.UpdateTime()
            self.ReloadEntriesIfNeeded()
        return True

    def DoAddSkill(self, invtype, skill, trainToLevel, idx = -1):
        """
            Add a skill to the skill queue, both in the UI and the temp skill queue.
        
            ARGUMENTS:
                invtype     :   the inventory of the item (the skill)
                skill       :   information about the skill
                trainToLevel:   level to train the skill to
        """
        skillID = invtype.id
        position = idx
        if position == -1:
            position = None
        timeLeft = self.skillQueueSvc.GetTrainingLengthOfSkill(skillID, trainToLevel, position=position)
        entry = self.GetRightEntry(invtype, skill, trainToLevel, timeLeft[1], timeLeft[2])
        try:
            self.skillQueueSvc.AddSkillToQueue(skillID, trainToLevel, position=idx)
            if idx == -1:
                idx = len(self.sr.rightScroll.GetNodes()) - 1
            self.sr.rightScroll.AddEntries(idx, [entry])
        except UserError as e:
            if e.msg == 'QueueTooLong' and IsTrialRestricted(session.userType):
                sys.exc_clear()
                uicore.cmd.OpenTrialUpsell(origin=ORIGIN_CHARACTERSHEET, reason='skillqueue', message=localization.GetByLabel('UI/TrialUpsell/SkillQueueBody'))
            else:
                raise

    def MoveUp(self, *args):
        """
            Called when the player tries to move up an entry in the skill queue (using up UI button)
        """
        self.Move(-1)

    def MoveDown(self, *args):
        """
            Called when the player tries to move down an entry in the skill queue (using down UI button)
        """
        self.Move(1)

    def Move(self, direction):
        """
            Moves the selected entry either up or down the scrolllist (depending on 
            what __direction__ is
        """
        queueLength = self.skillQueueSvc.GetNumberOfSkillsInQueue()
        selected = self.sr.rightScroll.GetSelected()
        if len(selected) > 1:
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/SkillQueue/CanMoveOnlyOneSkill')})
            return
        for data in selected:
            newIdx = max(-1, data.idx + direction)
            condition = False
            if direction == -1 and data.idx >= 0:
                condition = True
            elif direction == 1 and data.idx < queueLength - 1:
                condition = True
            if data.skillID and condition:
                self.DoMove(data, newIdx, queueLength)

    def DoMove(self, data, newIdx, queueLength, movingBelow = 0):
        trainToLevel = data.Get('trainToLevel', None)
        if data.skillID and trainToLevel:
            skillPos = newIdx
            if newIdx == -1:
                skillPos = queueLength - 1
            self.skillQueueSvc.MoveSkillToPosition(data.skillID, trainToLevel, skillPos)
            newLength = self.skillQueueSvc.GetNumberOfSkillsInQueue()
            if queueLength != newLength:
                self.ReloadQueue()
            else:
                self.sr.rightScroll.RemoveEntries([data])
                self.sr.rightScroll.AddEntries(skillPos - movingBelow, [data])
                self.sr.rightScroll.SelectNode(data)
                self.ChangeTimesOnEntriesInQueue()

    def RemoveSkillFromQueue(self, *args):
        """
            Removes the selected items from the skill queue, both in the UI and the 
            actual queue.
            When items have been removed, entries on the left hand side (which correspond 
            to the same skill) need to be modified
        """
        selected = self.sr.rightScroll.GetSelected()
        self.DoRemove(None, selected)

    def RemoveToGroup(self, id, nodes):
        self.DoRemove(None, nodes)

    def DoRemove(self, dragObj, entries, *args):
        entries.reverse()
        removeList = []
        for entry in entries:
            if entry.__guid__ != 'listentry.SkillQueueSkillEntry':
                continue
            if not util.GetAttrs(entry, 'inQueue'):
                return
            trainToLevel = entry.Get('trainToLevel', -1)
            try:
                self.skillQueueSvc.RemoveSkillFromQueue(entry.invtype.id, trainToLevel)
                removeList.append(entry)
            except UserError:
                self.ReloadAfterRemove(removeList)
                raise

        self.ReloadAfterRemove(removeList)

    def ReloadAfterRemove(self, removeList):
        self.sr.rightScroll.RemoveEntries(removeList)
        self.ReloadEntriesIfNeeded()
        self.UpdateTime()
        if settings.user.ui.Get('skillqueue_fitsinqueue', FITSINQUEUE_DEFAULT):
            self.ReloadSkills(time=2000)

    def OnContentDragEnter(self, *args):
        self.ChangeDropIndicator('OnDragEnter', *args)

    def OnContentDragExit(self, *args):
        self.ChangeDropIndicator(funcName='OnDragExit')

    def ChangeDropIndicator(self, funcName, *args):
        nodes = self.sr.rightScroll.GetNodes()
        if not nodes:
            return
        lastNode = nodes[-1]
        if lastNode.__guid__ != 'SkillQueueLastDropEntry':
            return
        if lastNode.panel is None:
            return
        func = getattr(lastNode.panel, funcName, None)
        if func is None:
            return
        func(*args)

    def DoDropData(self, dragObj, entries, idx = -1):
        """
            Here if nodes are dropped in the skill queue.
            These nodes might not be "allowed" in the queue so we need to check
            their guids, and handle them differently depending on what the guids are.
        
            ARGUMENTS:
                entries:    entries dropped in the skill queue
                idx:        the position where the first added/moved entry should be
        """
        queue = self.skillQueueSvc.GetQueue()
        self.ChangeDropIndicator('HideIndicator')
        if not entries:
            return
        if idx == -1:
            idx = len(queue)
        data = entries[0]
        if data.__guid__ == 'listentry.SkillQueueSkillEntry':
            if data.Get('inQueue', None) and not uicore.uilib.Key(uiconst.VK_SHIFT):
                movingBelow = 0
                if idx > data.idx:
                    movingBelow = 1
                newIdx = max(0, idx)
                if data.skillID:
                    self.DoMove(data, newIdx, len(queue), movingBelow)
            else:
                self.AddSkillThroughSkillEntry(data, queue, idx)
        elif data.__guid__ == 'listentry.SkillEntry':
            self.AddSkillThroughSkillEntry(data, queue, idx)
        elif data.__guid__ in ('xtriui.InvItem', 'listentry.InvItem'):
            category = util.GetAttrs(data, 'rec', 'categoryID')
            if category == const.categorySkill:
                sm.StartService('skills').InjectSkillIntoBrain([data.item])
                blue.pyos.synchro.SleepWallclock(500)
                self.AddSkillsThroughOtherEntry(data.item.typeID, idx, queue, nextLevel=1)
        elif data.__guid__ == 'listentry.SkillTreeEntry':
            self.AddSkillsThroughOtherEntry(data.typeID, idx, queue)
        elif data.__guid__ == 'uicls.GenericDraggableForTypeID':
            categoryID = cfg.invtypes.Get(data.typeID).categoryID
            if categoryID == const.categorySkill:
                self.AddSkillsThroughOtherEntry(data.typeID, idx, queue)
        self.UpdateTime()
        self.ReloadEntriesIfNeeded()

    def ChangeTimesOnEntriesInQueue(self):
        timesForSkillsInQueue = self.skillQueueSvc.GetAllTrainingLengths()
        for node in self.sr.rightScroll.GetNodes():
            if node.__guid__ != 'listentry.SkillQueueSkillEntry':
                continue
            times = timesForSkillsInQueue.get((node.skillID, node.trainToLevel))
            if times:
                timeLeft, addedTime, isAccelerated = times
            else:
                addedTime = 0
                isAccelerated = False
            self.ChangeTimeOnSingleEntry(node, timeLeft=addedTime, isAccelerated=isAccelerated)

    def ChangeTimesOnEntriesInSkillList(self, nodeList = None):
        queue = self.skillQueueSvc.GetQueue()
        godmaSkillSet = self.skillQueueSvc.GetGodmaSkillsSet()
        currentAttributes = self.skillQueueSvc.GetPlayerAttributeDict()
        if nodeList is None:
            nodeList = self.sr.leftScroll.GetNodes()
        for entry in nodeList:
            if entry.__guid__ != 'listentry.SkillQueueSkillEntry':
                continue
            skillTypeID = entry.skillID
            skill = entry.skill
            nextLevel = self.skillQueueSvc.FindNextLevel(skillTypeID, skill.skillLevel, queue)
            entry.trainToLevel = nextLevel - 1
            if nextLevel and nextLevel <= 5:
                if nextLevel > 1:
                    previousLevelEndSP = GetSPForLevelRaw(skill.skillTimeConstant, nextLevel - 1)
                    previousLevelEndSP = max(previousLevelEndSP, skill.skillPoints)
                    theoreticalSP = {skillTypeID: previousLevelEndSP}
                else:
                    theoreticalSP = {}
                _, trainingTime, _ = self.skillQueueSvc.GetAddedSpAndAddedTimeForSkill(skillTypeID, nextLevel, godmaSkillSet, theoreticalSP, 0, None, currentAttributes)
            else:
                trainingTime = 0
            self.ChangeTimeOnSingleEntry(entry, trainingTime, False)

    def ChangeTimeOnSingleEntry(self, node, timeLeft = 0, isAccelerated = False):
        timeHasChanged = long(node.timeLeft) != long(timeLeft)
        node.timeLeft = timeLeft
        node.isAccelerated = isAccelerated
        if node.panel and timeHasChanged:
            if timeLeft > 0:
                timeLeftText = localization.formatters.FormatTimeIntervalShortWritten(long(timeLeft), showFrom='day', showTo='second')
            else:
                timeLeftText = ''
            node.panel.sr.timeLeftText.text = timeLeftText
            node.panel.AdjustTimerContWidth()
            node.panel.UpdateAcceleratedMarker()
            node.panel.FillBoxes(node.skill.skillLevel, node.trainToLevel)

    def ReloadEntriesIfNeeded(self, force = 0):
        """
            If a skill is added to the skill queue the corresponding entry in the skill list
            needs to be updated. 
            If a skill is dropped in the skill queue, we need to check if it's visible
            in the skill list. If there is one entry that needs to be updated we just reload
            the whole list
        
            ARGUMENTS:
                entries:    a list of skillIDs that need to be reloaded
        """
        self.ChangeTimesOnEntriesInQueue()
        if self.expanded == 0 and not force:
            return
        self.ChangeTimesOnEntriesInSkillList()

    def OnSkillQueueTrimmed(self, removedSkills):
        self.LoadQueue()
        self.ReloadSkills()

    def OnSkillFinished(self, skillItemID, skillID, level):
        if (skillID, level) in self.queueLastApplied:
            self.queueLastApplied.remove((skillID, level))
        self.LoadQueue()
        self.ReloadSkills()

    def OnSkillStarted(self, skillID = None, level = None):
        self.LoadQueue()
        self.ReloadSkills()
        self.GrayButton(self.sr.pauseBtn, gray=0)

    def OnSkillPaused(self, skillItemID):
        self.LoadQueue()
        self.ReloadSkills()
        self.GrayButton(self.sr.pauseBtn, gray=1)

    def OnGodmaSkillInjected(self):
        self.ReloadSkills()

    def OnGodmaSkillTrained(self, skillID):
        self.ReloadSkills()

    def OnSkillQueueRefreshed(self):
        self.LoadQueue()
        self.ReloadSkills()

    def OnUIRefresh(self, *args):
        if getattr(self, 'timelineCont'):
            self.timelineCont.Close()

    def DoNothing(self):
        pass


class SkillQueueSkillEntry(listentry.BaseSkillEntry):
    """
    This entry is very similar to SkillEntry.
    """
    __guid__ = 'listentry.SkillQueueSkillEntry'
    __nonpersistvars__ = ['selection', 'id']
    isDragObject = True

    def Startup(self, *args):
        self.entryHeight = 0
        self.blinking = 0
        listentry.BaseSkillEntry.Startup(self, *args)
        self.barWidth = 0
        self.barHeigth = 0
        self.barLeft = 0
        self.sr.bar = uiprimitives.Container(name='posIndicator', parent=self, align=uiconst.TOBOTTOM, state=uiconst.UI_DISABLED, height=3, top=0, clipChildren=1)
        self.sr.posIndicatorCont = uiprimitives.Container(name='posIndicator', parent=self, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, height=2)
        self.sr.posIndicatorNo = uiprimitives.Fill(parent=self.sr.posIndicatorCont, color=(0.61, 0.05, 0.005, 1.0))
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes = uiprimitives.Fill(parent=self.sr.posIndicatorCont, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN
        self.acceleratedSprite = uiprimitives.Sprite(name='accelratedTraining', parent=self, align=uiconst.BOTTOMLEFT, state=uiconst.UI_NORMAL, pos=(2, 4, 16, 16), texturePath='res:/UI/Texture/Crimewatch/booster.png', idx=0)
        self.acceleratedSprite.hint = localization.GetByLabel('UI/SkillQueue/Skills/AcceleratedTraining')
        self.acceleratedSprite.display = False
        self.skillQueueSvc = sm.GetService('skillqueue')

    def Load(self, node):
        listentry.BaseSkillEntry.Load(self, node)
        data = node
        self.skillID = data.skillID
        for i in xrange(5):
            fill = self.sr.Get('box_%s' % i)
            fill.SetRGB(*self.whiteColor)
            if data.skill.skillLevel > i:
                fill.state = uiconst.UI_DISABLED
            else:
                fill.state = uiconst.UI_HIDDEN
            sm.StartService('ui').StopBlink(fill)

        self.sr.nameLevelLabel.text = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndRankValue', skill=data.invtype.typeID, rank=self.rank)
        self.sr.pointsLabel.top = self.sr.nameLevelLabel.top + self.sr.nameLevelLabel.height
        self.inQueue = data.Get('inQueue', 0)
        if self.inQueue == 1:
            self.sr.levelHeader1.text = localization.GetByLabel('UI/SkillQueue/Skills/SkillLevelWordAndValue', skillLevel=data.trainToLevel)
            self.sr.pointsLabel.text = ''
        else:
            self.sr.levelHeader1.text = localization.GetByLabel('UI/SkillQueue/Skills/SkillLevelWordAndValue', skillLevel=data.skill.skillLevel)
            self.sr.pointsLabel.text = self.skillPointsText
        if data.trained:
            shouldNotUpdate = self.inQueue == 1 and data.skill.skillLevel + 1 != self.sr.node.trainToLevel
            if data.skill.flagID == const.flagSkillInTraining and not shouldNotUpdate:
                uthread.new(self.UpdateTraining, data.skill)
            else:
                skill = data.skill
                if skill.spHi is not None:
                    timeLeft = data.timeLeft
                    if timeLeft > 0:
                        timeLeftText = localization.formatters.FormatTimeIntervalShortWritten(long(timeLeft), showFrom='day', showTo='second')
                    else:
                        timeLeftText = ''
                    self.sr.timeLeftText.text = timeLeftText
                if shouldNotUpdate:
                    self.GetIcon('chapter')
                else:
                    self.UpdateHalfTrained()
        self.AdjustTimerContWidth()
        self.sr.levelParent.width = self.sr.levels.width + const.defaultPadding
        self.FillBoxes(data.skill.skillLevel, data.trainToLevel)
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN
        if self.inQueue == 1:
            self.sr.inTrainingHilite.state = uiconst.UI_HIDDEN
            self.UpdateBar()
        self.UpdateAcceleratedMarker()

    def UpdateAcceleratedMarker(self):
        if not self.inQueue:
            return
        data = self.sr.node
        if data.isAccelerated:
            self.acceleratedSprite.display = True
        else:
            self.acceleratedSprite.display = False

    def FillBoxes(self, currentLevel, trainToLevel):
        """
            Colors the boxes you have planned to train but do not have yet
            If the skill is in training, there should be no blinking, except
            if this is the entry for the level which is training.
            The entries are blue now but the color might change
        """
        inTraining = sm.StartService('skills').SkillInTraining()
        for i in xrange(currentLevel, 5):
            if inTraining and inTraining.typeID == self.skillID:
                if not self.inQueue:
                    if i == currentLevel:
                        self.blinking = 1
                        continue
                elif currentLevel + 1 == trainToLevel:
                    self.blinking = 1
                    continue
            box = self.sr.Get('box_%s' % i, None)
            box.state = uiconst.UI_HIDDEN
            if box and i < trainToLevel:
                box.SetRGB(*self.blueColor)
                box.state = uiconst.UI_DISABLED

    def GetMenu(self):
        m = []
        if eve.session.role & ROLE_GMH == ROLE_GMH:
            m.extend(sm.GetService('info').GetGMGiveSkillMenu(self.skillID))
        if self.rec.typeID is not None:
            m += sm.StartService('menu').GetMenuFormItemIDTypeID(None, self.rec.typeID, ignoreMarketDetails=0)
        selected = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        if self.inQueue == 1:
            if util.GetAttrs(self, 'parent', 'RemoveSkillFromQueue'):
                m.append(None)
                m.append((uiutil.MenuLabel('UI/Commands/Remove'), self.parent.RemoveSkillFromQueue, ()))
        elif util.GetAttrs(self, 'parent', 'AddSkillToQueue'):
            if util.GetAttrs(self, 'sr', 'node', 'currentLevel') < 5:
                queue = self.skillQueueSvc.GetQueue()
                nextLevel = self.skillQueueSvc.FindNextLevel(self.sr.node.skillID, self.sr.node.skill.skillLevel, queue)
                if nextLevel < 6:
                    m.append(None)
                    m.append((uiutil.MenuLabel('UI/Commands/AddItem'), self.parent.AddSkillToQueue, ()))
        return m

    def GetHint(self):
        return cfg.invtypes.Get(self.skillID).description

    def OnClick(self, *args):
        if self.sr.node:
            if self.sr.node.Get('selectable', 1):
                self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def UpdateTraining(self, skill):
        if not self or self.destroyed:
            return
        currentPoints = listentry.BaseSkillEntry.UpdateTraining(self, skill)
        level = skill.skillLevel
        fill = self.sr.Get('box_%s' % int(level))
        fill.state = uiconst.UI_DISABLED
        if self.blinking == 1:
            fill.SetRGB(*form.SkillQueue.COLOR_SKILL_1)
            sm.StartService('ui').BlinkSpriteA(fill, 1.0, time=1000.0, maxCount=0, passColor=0, minA=0.5)
        if self.inQueue == 0:
            self.OnSkillpointChange(currentPoints)
        self.UpdateHalfTrained()

    def UpdateProgress(self):
        try:
            if self.endOfTraining is None:
                self.timer = None
                return
            skill = self.rec
            timeLeft = self.endOfTraining - blue.os.GetWallclockTime()
            if self.inQueue == 0:
                secs = timeLeft / 10000000L
                currentPoints = min(skill.spHi - secs / 60.0 * skill.spm, skill.spHi)
                self.OnSkillpointChange(currentPoints)
            else:
                self.SetTimeLeft(timeLeft)
            self.UpdateHalfTrained()
        except:
            self.timer = None
            log.LogException()
            sys.exc_clear()

    def GetDragData(self, *args):
        self.sr.node.scroll.SelectNode(self.sr.node)
        return [self.sr.node]

    def OnDropData(self, dragObj, nodes, *args):
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN
        if util.GetAttrs(self, 'parent', 'OnDropData'):
            if self.inQueue:
                self.parent.OnDropData(dragObj, nodes, idx=self.sr.node.idx)
            else:
                node = nodes[0]
                if util.GetAttrs(node, 'panel', 'inQueue'):
                    self.parent.OnDropData(dragObj, nodes)

    def OnDragEnter(self, dragObj, nodes, *args):
        if not self.inQueue or nodes is None:
            return
        node = nodes[0]
        allowedMove = self.skillQueueSvc.IsMoveAllowed(node, self.sr.node.idx)
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN
        if allowedMove == True:
            self.sr.posIndicatorYes.state = uiconst.UI_DISABLED
        elif allowedMove == False:
            self.sr.posIndicatorNo.state = uiconst.UI_DISABLED

    def OnDragExit(self, *args):
        if not self.inQueue:
            return
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN

    def UpdateBar(self):
        if getattr(self, 'timelineCont', None) and not self.timelineCont.destroyed:
            self.timelineCont.FlushLine()
        else:
            self.timelineCont = TimelineContainer(parent=self.sr.bar, barHeight=6)
        width = self.sr.node.Get('barWidth', 0)
        left = self.sr.node.Get('barLeft', 0)
        color = self.sr.node.Get('barColor', (0, 0, 0, 0))
        self.timelineCont.AddPoint(x=left, color=color)
        self.timelineCont.AddPoint(x=left + width, color=color)

    def GetDynamicHeight(node, width):
        """ We need this hack so the entry is high enough for chinese text """
        name = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndRankValue', skill=node.skill.type.typeID, rank=0)
        _, nameHeight = uicontrols.EveLabelMedium.MeasureTextSize(name, maxLines=1)
        return max(36, 2 * nameHeight + 2)


class SkillQueueLastDropEntry(SE_BaseClassCore):
    __guid__ = 'SkillQueueLastDropEntry'
    NO_COLOR = (0.61, 0.05, 0.005, 1.0)
    OK_COLOR = (1.0, 1.0, 1.0, 0.5)

    def ApplyAttributes(self, attributes):
        SE_BaseClassCore.ApplyAttributes(self, attributes)
        self.height = 18
        self.posIndicator = uiprimitives.Fill(parent=self, color=self.OK_COLOR, align=uiconst.TOTOP, height=2)
        self.posIndicator.display = False

    def Load(self, node):
        pass

    def OnDragEnter(self, dragObj, nodes, *args):
        node = nodes[0]
        allowedMove = sm.GetService('skillqueue').IsMoveAllowed(node, None)
        if allowedMove is None:
            self.HideIndicator()
            return
        if allowedMove:
            color = self.OK_COLOR
        else:
            color = self.NO_COLOR
        self.posIndicator.SetRGBA(*color)
        self.posIndicator.display = True

    def OnDragExit(self, *args):
        self.HideIndicator()

    def OnDropData(self, dragObj, nodes, *args):
        self.HideIndicator()
        if util.GetAttrs(self, 'parent', 'OnDropData'):
            self.parent.OnDropData(dragObj, nodes)

    def HideIndicator(self):
        self.posIndicator.display = False


class TimelineContainer(uiprimitives.Container):
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        barHeight = attributes.barHeight
        self.line = VectorLineTrace(name='bg', parent=self, lineWidth=barHeight, align=uiconst.CENTERLEFT)
        self.midpoint = barHeight / 2.0

    def AddPoint(self, x, color):
        if not self.destroyed:
            self.line.AddPoint((x, self.midpoint), color=color)

    def FlushLine(self):
        self.line.Flush()
