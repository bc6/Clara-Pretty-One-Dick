#Embedded file name: achievements/common\achievementLoader.py
__author__ = 'aevar'
from ..common.achievementController import Achievement
from ..common.achievementController import AchievementSimpleCondition
import localization

class AchievementLoader:

    def _LoadRawAchievementData(self):
        import fsdSchemas.binaryLoader as fsdBinaryLoader
        return fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/achievements.static')

    def GetAchievements(self):
        rawData = self._LoadRawAchievementData()
        return self.ConstructAchievementDictFromData(rawData)

    def AddConditions(self, achievement, value):
        if value.simpleConditions:
            for conditionid in value.simpleConditions:
                simplecondition = value.simpleConditions[conditionid]
                achievement.AddCondition(AchievementSimpleCondition(statName=simplecondition.statistic, targetValue=simplecondition.targetValue))

    def ConstructAchievementDictFromData(self, loadedAchievements):
        achievements = {}
        if loadedAchievements is None:
            print 'LogError'
            return {}
        for key, value in loadedAchievements.iteritems():
            notificationTextID = getattr(value, 'notificationTextID', None)
            if notificationTextID:
                notificationText = localization.GetByMessageID(value.notificationTextID)
            else:
                notificationText = None
            achievement = Achievement(id=key, name=localization.GetByMessageID(value.nameID), description=localization.GetByMessageID(value.descriptionID), notificationText=notificationText)
            self.AddConditions(achievement, value)
            achievements[key] = achievement

        return achievements
