#Embedded file name: eve/client/script/ui/services\skillsvc.py
import sys
import operator
from collections import defaultdict
import blue
import service
import uiutil
from notifications.common.formatters.skillPoints import UnusedSkillPointsFormatter
from notifications.common.notification import Notification
import uthread
import util
import xtriui
import characterskills.util
import carbonui.const as uiconst
import localization
import telemetry
from characterskills.util import GetSkillLevelRaw
import const
import inventorycommon.const as invconst
import eve.common.script.util.notificationconst as notificationConst
SKILLREQ_DONTHAVE = 1
SKILLREQ_HAVEBUTNOTTRAINED = 2
SKILLREQ_HAVEANDTRAINED = 3
SKILLREQ_HAVEANDTRAINEDFULLY = 4
SKILLREQ_TRIALRESTRICTED = 5
TEXTURE_PATH_BY_SKILLREQ = {SKILLREQ_DONTHAVE: 'res:/UI/Texture/Classes/Skills/doNotHaveFrame.png',
 SKILLREQ_HAVEBUTNOTTRAINED: 'res:/UI/Texture/Classes/Skills/levelPartiallyTrainedFrame.png',
 SKILLREQ_HAVEANDTRAINED: 'res:/UI/Texture/Classes/Skills/levelTrainedFrame.png',
 SKILLREQ_HAVEANDTRAINEDFULLY: 'res:/UI/Texture/Classes/Skills/fullyTrainedFrame.png',
 SKILLREQ_TRIALRESTRICTED: 'res:/UI/Texture/Classes/Skills/trialRestrictedFrame.png'}
SHIP_SKILLREQ_HINT = {SKILLREQ_DONTHAVE: 'UI/InfoWindow/ShipSkillReqDoNotHave',
 SKILLREQ_HAVEBUTNOTTRAINED: 'UI/InfoWindow/ShipSkillReqPartiallyTrained',
 SKILLREQ_HAVEANDTRAINED: 'UI/InfoWindow/ShipSkillReqTrained',
 SKILLREQ_HAVEANDTRAINEDFULLY: 'UI/InfoWindow/ShipSkillReqFullyTrained',
 SKILLREQ_TRIALRESTRICTED: 'UI/InfoWindow/ShipSkillReqRestrictedForTrial'}
SKILL_SKILLREQ_HINT = {SKILLREQ_DONTHAVE: 'UI/InfoWindow/SkillReqDoNotHave',
 SKILLREQ_HAVEBUTNOTTRAINED: 'UI/InfoWindow/SkillReqPartiallyTrained',
 SKILLREQ_HAVEANDTRAINED: 'UI/InfoWindow/SkillReqTrained',
 SKILLREQ_HAVEANDTRAINEDFULLY: 'UI/InfoWindow/SkillReqFullyTrained',
 SKILLREQ_TRIALRESTRICTED: 'UI/InfoWindow/SkillReqRestrictedForTrial'}
ITEM_SKILLREQ_HINT = {SKILLREQ_DONTHAVE: 'UI/InfoWindow/ItemSkillReqDoNotHave',
 SKILLREQ_HAVEBUTNOTTRAINED: 'UI/InfoWindow/ItemSkillReqPartiallyTrained',
 SKILLREQ_HAVEANDTRAINED: 'UI/InfoWindow/ItemSkillReqTrained',
 SKILLREQ_HAVEANDTRAINEDFULLY: 'UI/InfoWindow/ItemSkillReqFullyTrained',
 SKILLREQ_TRIALRESTRICTED: 'UI/InfoWindow/ItemSkillReqRestrictedForTrial'}

class SkillsSvc(service.Service):
    __guid__ = 'svc.skills'
    __exportedcalls__ = {'SkillInTraining': [],
     'HasSkill': [],
     'MySkills': [],
     'MySkillLevelsByID': [],
     'GetSkillPoints': [],
     'GetSkillGroups': [],
     'GetSkillCount': [],
     'GetAllSkills': [],
     'GetSkillHistory': [],
     'GetFreeSkillPoints': [],
     'SetFreeSkillPoints': []}
    __notifyevents__ = ['ProcessSessionChange',
     'OnGodmaSkillStartTraining',
     'OnGodmaSkillTrainingStopped',
     'OnSkillFinished',
     'OnRespecInfoChanged',
     'OnGodmaMultipleSkillsTrained',
     'OnFreeSkillPointsChanged',
     'OnGodmaSkillInjected',
     'OnGodmaSkillTrained',
     'OnItemChange']
    __servicename__ = 'skills'
    __displayname__ = 'Skill Client Service'
    __dependencies__ = ['settings', 'godma']

    def Run(self, memStream = None):
        self.LogInfo('Starting Skills')
        self.Reset()

    def Stop(self, memStream = None):
        self.Reset()

    def ProcessSessionChange(self, isremote, session, change):
        if session.charid is None:
            self.Stop()
            self.Reset()

    def Reset(self):
        self.myskills = None
        self.mySkillsByTypeID = None
        self.allskills = None
        self.skillGroups = None
        self.skillHistory = None
        self.respecInfo = None
        self.freeSkillPoints = None

    def ResetSkillHistory(self):
        self.skillHistory = None

    @telemetry.ZONE_METHOD
    def SkillInTraining(self, *args):
        inTraining = [ each for each in self.GetMyGodmaItem().skills.itervalues() if each.flagID == const.flagSkillInTraining ]
        if inTraining:
            return inTraining[0]
        else:
            return None

    def OnSkillFinished(self, skillID, skillTypeID = None, skillLevel = None):
        oldNotification = settings.user.ui.Get('skills_showoldnotification', 0)
        try:
            self.skillHistory = None
            skill = self.godma.GetItem(skillID)
            self.myskills = None
            if oldNotification == 1:
                eve.Message('SkillTrained', {'name': cfg.invtypes.Get(skill.typeID).name,
                 'lvl': skill.skillLevel})
        except:
            sys.exc_clear()

        if oldNotification == 0:
            eve.Message('skillTrainingFanfare')
            onlineTraining = True
            uthread.new(sm.StartService('neocom').ShowSkillNotification, [skill.typeID], onlineTraining)

    def OnGodmaMultipleSkillsTrained(self, skillTypeIDs):
        oldNotification = settings.user.ui.Get('skills_showoldnotification', 0)
        if oldNotification == 1:
            if len(skillTypeIDs) == 1:
                skill = self.GetMySkillsFromTypeID(skillTypeIDs[0])
                skillLevel = skill.skillLevel if skill is not None else localization.GetByLabel('UI/Common/Unknown')
                eve.Message('SkillTrained', {'name': cfg.invtypes.Get(skillTypeIDs[0]).name,
                 'lvl': skillLevel})
            else:
                eve.Message('MultipleSkillsTrainedNotify', {'num': len(skillTypeIDs)})
        else:
            eve.Message('skillTrainingFanfare')
            onlineTraining = False
            uthread.new(sm.StartService('neocom').ShowSkillNotification, skillTypeIDs, onlineTraining)

    def MySkills(self, renew = 0, byTypeID = False):
        if self.myskills is None or renew:
            self.LogInfo('MySkills::Renewing skill info')
            self.myskills = self.GetMyGodmaItem().skills.values()
            self.mySkillsByTypeID = self.myskills.Index('typeID')
        if byTypeID:
            return self.mySkillsByTypeID
        return self.myskills

    def MySkillLevel(self, typeID):
        skill = self.MySkills(byTypeID=True).get(typeID, None)
        if skill is not None:
            return skill.skillLevel

    def MySkillPoints(self, typeID):
        skill = self.MySkills(byTypeID=True).get(typeID, None)
        if skill is not None:
            return skill.skillPoints

    def MySkillLevelsByID(self, renew = 0):
        skills = {}
        for skill in self.MySkills(renew):
            skills[skill.typeID] = skill.skillLevel

        return skills

    def OnGodmaSkillStartTraining(self, typeID = None, *args):
        self.skillHistory = None
        if self.myskills is not None and typeID is not None:
            for skill in self.myskills:
                if skill.typeID == typeID:
                    return

            self.MySkills(1)

    def OnGodmaSkillTrainingStopped(self, *args):
        self.skillHistory = None
        self.MySkills(1)

    def OnGodmaSkillInjected(self, *args):
        self.MySkills(1)

    def OnGodmaSkillTrained(self, skillItemID):
        self.MySkills(1)

    def OnItemChange(self, item, change):
        if item.categoryID != const.categorySkill:
            return
        if const.ixLocationID not in change or change[const.ixLocationID] != session.charid:
            return
        self.myskills = None

    def HasSkill(self, skillID):
        mine = self.MySkills()
        skills = [ skill for skill in mine if skill.typeID == skillID ]
        if len(skills):
            return skills[0]

    @telemetry.ZONE_METHOD
    def GetAllSkills(self):
        if not self.allskills:
            self.allskills = [ sm.GetService('godma').GetType(each.typeID) for each in cfg.invtypes if each.categoryID == const.categorySkill and each.published == 1 ]
        return self.allskills

    @telemetry.ZONE_METHOD
    def GetAllSkillGroups(self):
        if not self.skillGroups:
            skillgroups = [ g for g in cfg.invgroups if g.categoryID == const.categorySkill and g.groupID not in [const.groupFakeSkills] ]
            skillgroups = localization.util.Sort(skillgroups, key=operator.attrgetter('groupName'))
            self.skillGroups = skillgroups
        return self.skillGroups

    @telemetry.ZONE_METHOD
    def GetSkillHistory(self, maxresults = 50):
        if self.skillHistory is None:
            self.skillHistory = self.godma.GetSkillHandler().GetSkillHistory(maxresults)
        return self.skillHistory

    @telemetry.ZONE_METHOD
    def GetRecentlyTrainedSkills(self):
        """ Fetches from the server those skills that have recently been trained. Will only return same skill upgrade once """
        skillChanges = {}
        skillData = self.godma.GetSkillHandler().GetSkillChangesForISIS()
        for skill in skillData:
            typeID = skill.skillTypeID
            currentSkillPoints = self.MySkillPoints(typeID) or 0
            timeConstant = self.godma.GetTypeAttribute2(typeID, const.attributeSkillTimeConstant)
            pointsBefore = currentSkillPoints - skill.pointChange
            oldLevel = GetSkillLevelRaw(pointsBefore, timeConstant)
            if self.MySkillLevel(typeID) > oldLevel:
                skillChanges[typeID] = oldLevel

        return skillChanges

    @telemetry.ZONE_METHOD
    def GetSkillGroups(self, advanced = False):
        if session.charid:
            ownSkills = self.GetMyGodmaItem().skills.values()
            skillQueue = sm.GetService('skillqueue').GetServerQueue()
            skillsInQueue = [ skillID for skillID, trainlevel in skillQueue ]
        else:
            ownSkills = []
            skillsInQueue = []
        ownSkillTypeIDs = []
        ownSkillsByGroupID = defaultdict(list)
        ownSkillsInTrainingByGroupID = defaultdict(list)
        ownSkillsInQueueByGroupID = defaultdict(list)
        ownSkillPointsByGroupID = defaultdict(int)
        for mySkill in ownSkills:
            if not mySkill:
                continue
            ownSkillsByGroupID[mySkill.groupID].append(mySkill)
            if mySkill.flagID == const.flagSkillInTraining:
                ownSkillsInTrainingByGroupID[mySkill.groupID].append(mySkill)
            if mySkill.typeID in skillsInQueue:
                ownSkillsInQueueByGroupID[mySkill.groupID].append(mySkill.typeID)
            ownSkillPointsByGroupID[mySkill.groupID] += mySkill.skillPoints
            ownSkillTypeIDs.append(mySkill.typeID)

        missingSkillsByGroupID = defaultdict(list)
        if advanced:
            allSkills = self.GetAllSkills()
            for aSkill in allSkills:
                if aSkill.typeID not in ownSkillTypeIDs:
                    missingSkillsByGroupID[aSkill.groupID].append(aSkill)

        skillsByGroup = []
        skillgroups = self.GetAllSkillGroups()
        for invGroup in skillgroups:
            mySkillsInGroup = ownSkillsByGroupID[invGroup.groupID]
            skillsIDontHave = missingSkillsByGroupID[invGroup.groupID]
            mySkillsInTraining = ownSkillsInTrainingByGroupID[invGroup.groupID]
            mySkillsInQueue = ownSkillsInQueueByGroupID[invGroup.groupID]
            skillPointsInGroup = ownSkillPointsByGroupID[invGroup.groupID]
            skillsByGroup.append([invGroup,
             mySkillsInGroup,
             skillsIDontHave,
             mySkillsInTraining,
             mySkillsInQueue,
             skillPointsInGroup])

        return skillsByGroup

    @telemetry.ZONE_METHOD
    def GetMySkillsFromTypeID(self, typeID):
        return self.MySkills(byTypeID=True).get(typeID, None)

    @telemetry.ZONE_METHOD
    def GetMyGodmaItem(self):
        ret = self.godma.GetItem(eve.session.charid)
        while ret is None:
            blue.pyos.synchro.SleepWallclock(500)
            ret = self.godma.GetItem(eve.session.charid)

        return ret

    def IsSkillRequirementMet(self, typeID):
        """ Are skills trained well enough to use this type """
        required = self.GetRequiredSkills(typeID)
        for skillid, lvl in required.iteritems():
            if self.MySkillLevel(skillid) < lvl:
                return False

        return True

    def GetRequiredSkills(self, typeID):
        """ Returns a dict of all skills directly required to use a typeID as well as their level """
        ret = {}
        for i in xrange(1, 7):
            attrID = getattr(const, 'attributeRequiredSkill%s' % i)
            skillID = sm.GetService('godma').GetTypeAttribute(typeID, attrID)
            if skillID is not None:
                skillID = int(skillID)
                attrID = getattr(const, 'attributeRequiredSkill%sLevel' % i)
                lvl = sm.GetService('godma').GetTypeAttribute(typeID, attrID, 1.0)
                ret[skillID] = lvl

        return ret

    def GetRequiredSkillsLevel(self, skills):
        """
        Returns an enumeration value, SKILLREQ_X, that represents how well the current character has trained
        for the item specified by typeID
        """
        if not skills:
            return SKILLREQ_HAVEANDTRAINED
        allLevel5 = True
        haveAll = True
        missingSkill = False
        for skillTypeID, level in skills:
            if self.IsTrialRestricted(skillTypeID):
                return SKILLREQ_TRIALRESTRICTED
            mySkill = sm.GetService('skills').GetMySkillsFromTypeID(skillTypeID)
            if mySkill is None:
                missingSkill = True
                continue
            if mySkill.skillLevel < level:
                haveAll = False
            if mySkill.skillLevel != 5:
                allLevel5 = False

        if missingSkill:
            return SKILLREQ_DONTHAVE
        elif not haveAll:
            return SKILLREQ_HAVEBUTNOTTRAINED
        elif allLevel5:
            return SKILLREQ_HAVEANDTRAINEDFULLY
        else:
            return SKILLREQ_HAVEANDTRAINED

    def GetRequiredSkillsLevelTexturePathAndHint(self, skills, typeID = None):
        skillLevel = self.GetRequiredSkillsLevel(skills)
        texturePath = TEXTURE_PATH_BY_SKILLREQ[skillLevel]
        if typeID is None:
            hint = ITEM_SKILLREQ_HINT[skillLevel]
        else:
            typeInfo = cfg.invtypes.Get(typeID)
            if typeInfo.categoryID == invconst.categoryShip:
                hint = SHIP_SKILLREQ_HINT[skillLevel]
            elif typeInfo.categoryID == invconst.categorySkill:
                hint = SKILL_SKILLREQ_HINT[skillLevel]
            else:
                hint = ITEM_SKILLREQ_HINT[skillLevel]
        return (texturePath, localization.GetByLabel(hint))

    def GetRequiredSkillsRecursive(self, typeID):
        """ 
        Returns all required to use a typeID, including nested requirements. 
        Returns highest level if same skill found multiple times
        """
        ret = {}
        self._GetSkillsRequiredToUseTypeRecursive(typeID, ret)
        return ret

    def _GetSkillsRequiredToUseTypeRecursive(self, typeID, ret):
        for skillID, lvl in self.GetRequiredSkills(typeID).iteritems():
            ret[skillID] = max(ret.get(skillID, 0), lvl)
            self._GetSkillsRequiredToUseTypeRecursive(skillID, ret)

    def GetTrainingTimeToGetToLevel(self, skillID, lvl):
        """ Total training time required to get from current level """
        totalTime = 0
        mySkill = self.GetMySkillsFromTypeID(skillID)
        mySkillLevel = 0
        if mySkill is not None:
            mySkillLevel = mySkill.skillLevel
        for i in xrange(int(mySkillLevel) + 1, int(lvl) + 1):
            totalTime += self.GetRawTrainingTimeForSkillLevel(skillID, i)

        return totalTime

    def GetSkillTrainingTimeLeftToUseType(self, typeID):
        """ Total training time required to be able to use type """
        if self.IsSkillRequirementMet(typeID):
            return 0
        totalTime = 0
        required = self.GetRequiredSkillsRecursive(typeID)
        for typeID, lvl in required.iteritems():
            totalTime += self.GetTrainingTimeToGetToLevel(typeID, lvl)

        return totalTime

    def GetSkillToolTip(self, skillID, level):
        if session.charid is None:
            return
        mySkill = sm.GetService('skills').GetMySkillsFromTypeID(skillID)
        mySkillLevel = 0
        if mySkill is not None:
            mySkillLevel = mySkill.skillLevel
        tooltipText = cfg.invtypes.Get(skillID).description
        tooltipTextList = []
        for i in xrange(int(mySkillLevel) + 1, int(level) + 1):
            timeLeft = self.GetRawTrainingTimeForSkillLevel(skillID, i)
            tooltipTextList.append(localization.GetByLabel('UI/SkillQueue/Skills/SkillLevelAndTrainingTime', skillLevel=i, timeLeft=long(timeLeft)))

        levelsText = '<br>'.join(tooltipTextList)
        if levelsText:
            tooltipText += '<br><br>' + levelsText
        return tooltipText

    def GetRawTrainingTimeForSkillLevel(self, skillID, skillLevel):
        """ 
        This gets the training time for this player to train JUST THIS LEVEL of THIS SKILL
        It purposely subtracts off any prior levels raw skillpoints, and any trained skillpoint in the skill 
        """
        skillTimeConstant = sm.GetService('godma').GetTypeAttribute(skillID, const.attributeSkillTimeConstant)
        primaryAttributeID = sm.GetService('godma').GetTypeAttribute(skillID, const.attributePrimaryAttribute)
        secondaryAttributeID = sm.GetService('godma').GetTypeAttribute(skillID, const.attributeSecondaryAttribute)

        def GetSkillPointsFromSkillObject(skillObject):
            if skillObject is None:
                return 0
            else:
                skillTrainingEnd, spHi, spm = skillObject.skillTrainingEnd, skillObject.spHi, skillObject.spm
                if skillTrainingEnd is not None and spHi is not None:
                    secs = (skillTrainingEnd - blue.os.GetWallclockTime()) / const.SEC
                    return min(spHi - secs / 60.0 * spm, spHi)
                return skillObject.skillPoints

        charItem = sm.GetService('godma').GetItem(session.charid)
        attrDict = {}
        for each in charItem.displayAttributes:
            attrDict[each.attributeID] = each.value

        playerPrimaryAttribute = attrDict[primaryAttributeID]
        playerSecondaryAttribute = attrDict[secondaryAttributeID]
        rawSkillPointsToTrain = characterskills.util.GetSPForLevelRaw(skillTimeConstant, skillLevel)
        trainingRate = characterskills.util.GetSkillPointsPerMinute(playerPrimaryAttribute, playerSecondaryAttribute)
        existingSP = 0
        priorLevel = skillLevel - 1
        if priorLevel >= 0:
            mySkill = sm.StartService('skills').GetMySkillsFromTypeID(skillID)
            mySkillLevel = 0
            if mySkill is not None:
                mySkillLevel = mySkill.skillLevel
            if priorLevel == mySkillLevel:
                playerCurrentSP = 0
                skillObj = sm.StartService('skills').GetMyGodmaItem().skills.get(skillID, None)
                if skillObj is not None:
                    playerCurrentSP = GetSkillPointsFromSkillObject(skillObj)
                else:
                    playerCurrentSP = 0
                existingSP = playerCurrentSP
            else:
                existingSP = characterskills.util.GetSPForLevelRaw(skillTimeConstant, priorLevel)
        skillPointsToTrain = rawSkillPointsToTrain - existingSP
        trainingTimeInMinutes = float(skillPointsToTrain) / float(trainingRate)
        return trainingTimeInMinutes * const.MIN

    @telemetry.ZONE_METHOD
    def GetSkillCount(self):
        return len(self.GetMyGodmaItem().skills.values())

    @telemetry.ZONE_METHOD
    def GetSkillPoints(self, groupID = None):
        total = 0
        skills = self.GetMyGodmaItem().skills
        for skillID in skills:
            skill = skills[skillID]
            if groupID is not None:
                if skill.groupID == groupID:
                    total += skill.skillPoints
            else:
                total += skill.skillPoints

        return total

    def Train(self, skillX):
        skill = self.SkillInTraining()
        if skill and eve.Message('ConfirmResetSkillTraining', {'name': skill.type.typeName,
         'lvl': skill.skillLevel + 1}, uiconst.OKCANCEL) != uiconst.ID_OK:
            return
        self.godma.GetSkillHandler().CharStartTrainingSkill(skillX.itemID, skillX.locationID)

    def InjectSkillIntoBrain(self, skillX):
        skillIDList = [ skill.itemID for skill in skillX ]
        if not skillIDList:
            return
        skillsLocation = skillX[0].locationID
        try:
            self.godma.GetSkillHandler().InjectSkillIntoBrain(skillIDList, skillsLocation)
        except UserError as e:
            if e.msg == 'TrialAccountRestriction':
                uicore.cmd.OpenTrialUpsell(origin='skills', reason=e.dict['skill'], message=localization.GetByLabel('UI/TrialUpsell/SkillRestrictionBody', skillname=cfg.invtypes.Get(e.dict['skill']).name))
            else:
                raise

    def AbortTrain(self, skillX):
        if eve.Message('ConfirmAbortSkillTraining', {}, uiconst.OKCANCEL) == uiconst.ID_OK:
            self.godma.GetSkillHandler().CharStopTrainingSkill()

    @telemetry.ZONE_METHOD
    def GetRespecInfo(self):
        """
            This is aggressively cached client-side, so most calls will not cause wire trips.
        """
        if self.respecInfo is None:
            self.respecInfo = self.godma.GetSkillHandler().GetRespecInfo()
        return self.respecInfo

    def OnRespecInfoChanged(self, *args):
        """
            Called when the server updates this player's respec info.
            This invalidates the cache and then scatters an event, allowing
            local services to respond appropriately AFTER the respec info
            queried from this object is guaranteed to be correct.
        """
        self.respecInfo = None
        sm.ScatterEvent('OnRespecInfoUpdated')

    def OnOpenCharacterSheet(self, skillIDs, *args):
        sm.GetService('charactersheet').ForceShowSkillHistoryHighlighting(skillIDs)

    def MakeSkillQueueEmptyNotification(self, skillQueueNotification):
        queueText = localization.GetByLabel('UI/SkillQueue/NoSkillsInQueue')
        skillQueueNotification = Notification.MakeSkillNotification(header=queueText, text='', created=blue.os.GetWallclockTime(), callBack=sm.StartService('skills').OnOpenCharacterSheet, callbackargs=None, notificationType=Notification.SKILL_NOTIFICATION_EMPTYQUEUE)
        return skillQueueNotification

    def ShowSkillNotification(self, skillTypeIDs, left, onlineTraining):
        data = util.KeyVal()
        skillText = ''
        notifySkillTraining = False
        if len(skillTypeIDs) == 1:
            skill = sm.StartService('skills').GetMySkillsFromTypeID(skillTypeIDs[0])
            skillLevel = skill.skillLevel if skill is not None else localization.GetByLabel('UI/Generic/Unknown')
            skillText = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndLevel', skill=skillTypeIDs[0], amount=skillLevel)
            if onlineTraining:
                notifySkillTraining = True
        else:
            notifySkillTraining = True
            skillText = localization.GetByLabel('UI/SkillQueue/Skills/NumberOfSkills', amount=len(skillTypeIDs))
        queue = sm.GetService('skillqueue').GetServerQueue()
        skillQueueNotification = None
        if len(queue) == 0:
            skillQueueNotification = self.MakeSkillQueueEmptyNotification(skillQueueNotification)
        headerText = localization.GetByLabel('UI/Generic/SkillTrainingComplete')
        skillnotification = Notification.MakeSkillNotification(headerText + ' - ' + skillText, skillText, blue.os.GetWallclockTime(), callBack=sm.StartService('skills').OnOpenCharacterSheet, callbackargs=skillTypeIDs)
        if notifySkillTraining:
            sm.ScatterEvent('OnNewNotificationReceived', skillnotification)
        if skillQueueNotification:
            sm.ScatterEvent('OnNewNotificationReceived', skillQueueNotification)

    def OnFreeSkillPointsChanged(self, newFreeSkillPoints):
        self.SetFreeSkillPoints(newFreeSkillPoints)

    @telemetry.ZONE_METHOD
    def GetFreeSkillPoints(self):
        if self.freeSkillPoints is None:
            return 0
        return self.freeSkillPoints

    def ApplyFreeSkillPoints(self, skillTypeID, pointsToApply):
        if self.freeSkillPoints is None:
            self.GetFreeSkillPoints()
        if self.SkillInTraining() is not None:
            raise UserError('CannotApplyFreePointsWhileQueueActive')
        skill = self.GetMySkillsFromTypeID(skillTypeID)
        if skill is None:
            raise UserError('CannotApplyFreePointsDoNotHaveSkill', {'skillName': cfg.invtypes.Get(skillTypeID).name})
        spAtMaxLevel = characterskills.util.GetSPForLevelRaw(skill.skillTimeConstant, 5)
        if skill.skillPoints + pointsToApply > spAtMaxLevel:
            pointsToApply = spAtMaxLevel - skill.skillPoints
        if pointsToApply > self.freeSkillPoints:
            raise UserError('CannotApplyFreePointsNotEnoughRemaining', {'pointsRequested': pointsToApply,
             'pointsRemaining': self.freeSkillPoints})
        if pointsToApply <= 0:
            return
        skillQueue = sm.GetService('skillqueue').GetQueue()
        for queueTypeID, queueLevel in skillQueue:
            if queueTypeID == skillTypeID:
                raise UserError('CannotApplyFreePointsToQueuedSkill', {'skillName': cfg.invtypes.Get(skillTypeID).name})

        newFreePoints = self.godma.GetSkillHandler().ApplyFreeSkillPoints(skill.typeID, pointsToApply)
        self.SetFreeSkillPoints(newFreePoints)

    def SetFreeSkillPoints(self, newFreePoints):
        if self.freeSkillPoints is None or newFreePoints != self.freeSkillPoints:
            if self.freeSkillPoints is None or newFreePoints > self.freeSkillPoints:
                uthread.new(self.ShowSkillPointsNotification_thread)
            self.freeSkillPoints = newFreePoints
            sm.ScatterEvent('OnFreeSkillPointsChanged_Local')

    def MakeAndScatterSkillPointNotification(self):
        notificationData = UnusedSkillPointsFormatter.MakeData()
        sm.GetService('notificationSvc').MakeAndScatterNotification(type=notificationConst.notificationTypeUnusedSkillPoints, data=notificationData)

    def ShowSkillPointsNotification(self, number = (0, 0), time = 5000, *args):
        skillPointsNow = self.GetFreeSkillPoints()
        skillPointsLast = settings.user.ui.Get('freeSkillPoints', -1)
        if skillPointsLast == skillPointsNow:
            return
        if skillPointsNow <= 0:
            return
        self.MakeAndScatterSkillPointNotification()
        settings.user.ui.Set('freeSkillPoints', skillPointsNow)

    def ShowSkillPointsNotification_thread(self):
        blue.pyos.synchro.SleepWallclock(5000)
        self.ShowSkillPointsNotification()

    def IsTrialRestricted(self, typeID):
        """
        If this is a trial account and this item or one of its requirements are
        restricted for trial accounts we return True. In all other cases we
        return False.
        """
        isTrialUser = session.userType == const.userTypeTrial
        if not isTrialUser:
            return False
        typeInfo = cfg.invtypes.Get(typeID)
        restricted = self.godma.GetTypeAttribute(typeID, const.attributeCanNotBeTrainedOnTrial)
        if typeInfo.categoryID == invconst.categorySkill and restricted:
            return True
        requirements = self.GetRequiredSkillsRecursive(typeID)
        for skillID in requirements.iterkeys():
            restricted = self.godma.GetTypeAttribute(skillID, const.attributeCanNotBeTrainedOnTrial)
            if restricted:
                return True

        return False
