#Embedded file name: achievements/common\achievementLoader.py
__author__ = 'aevar'
from ..common.achievementController import Achievement
from ..common.achievementController import AchievementSimpleCondition
import localization

class AchievementLoader:

    def _LoadRawAchievementData(self):
        import fsdSchemas.binaryLoader as fsdBinaryLoader
        return fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/achievements.static')

    def GetAchievements(self, getDisabled = False):
        rawData = self._LoadRawAchievementData()
        return self.ConstructAchievementDictFromData(rawData, getDisabled=getDisabled)

    def AddConditions(self, achievement, value):
        if value.simpleConditions:
            for conditionid in value.simpleConditions:
                simplecondition = value.simpleConditions[conditionid]
                achievement.AddCondition(AchievementSimpleCondition(statName=simplecondition.statistic, targetValue=simplecondition.targetValue))

    def ConstructAchievementDictFromData(self, loadedAchievements, getDisabled = False):
        achievements = {}
        if loadedAchievements is None:
            print 'LogError'
            return {}
        for key, value in loadedAchievements.iteritems():
            if not getDisabled and not value.isEnabled:
                continue
            notificationTextID = getattr(value, 'notificationTextID', None)
            if notificationTextID:
                notificationText = localization.GetByMessageID(value.notificationTextID)
            else:
                notificationText = None
            achievement = Achievement(achievementID=key, name=localization.GetByMessageID(value.nameID), description=localization.GetByMessageID(value.descriptionID), notificationText=notificationText, isClientAchievement=value.isClientAchievement, isEnabled=value.isEnabled)
            self.AddConditions(achievement, value)
            achievements[key] = achievement

        return achievements
