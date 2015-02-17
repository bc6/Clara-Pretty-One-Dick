#Embedded file name: notifications/client/development\skillHistoryProvider.py
from notifications.client.development.skillHistoryRow import SkillHistoryRow
from notifications.common.notification import Notification
import localization
EVENT_TYPE_TO_ACTION = {34: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillClonePenalty'),
 36: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillTrainingStarted'),
 37: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillTrainingComplete'),
 38: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillTrainingCanceled'),
 39: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/GMGiveSkill'),
 53: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillTrainingComplete'),
 307: localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/SkillPointsApplied')}

class SkillHistoryProvider(object):

    def __init__(self, scatterDebug = False, onlyShowAfterDate = None):
        self.scatterDebug = scatterDebug
        self.onlyShowAfterDate = onlyShowAfterDate

    def provide(self):
        notificationList = []
        result = []
        skillRowSet = sm.GetService('skills').GetSkillHistory(10)
        for row in skillRowSet:
            skill = sm.GetService('skills').HasSkill(row.skillTypeID)
            if skill is None:
                print 'Skill not found curious TODO < change to log'
                continue
            objectRow = SkillHistoryRow(row, skill.skillTimeConstant, cfg, EVENT_TYPE_TO_ACTION)
            if self.onlyShowAfterDate and objectRow.logDate <= self.onlyShowAfterDate:
                continue
            skillnameAndLevel = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndLevel', skill=objectRow.skillTypeID, amount=objectRow.level)
            result.append(objectRow)
            notification = Notification.MakeSkillNotification(header='%s - %s' % (objectRow.actionString, skillnameAndLevel), text='', created=objectRow.logDate, callBack=None, callbackargs=[objectRow.skillTypeID])
            notificationList.append(notification)
            if self.scatterDebug:
                sm.ScatterEvent('OnNewNotificationReceived', notification)

        return notificationList
