#Embedded file name: achievements/common\__init__.py
from collections import defaultdict
import blue

def GetNewAchievements(existingAchivements, completedDict, statsTrakcer):
    newAchievementDict = {}
    for key, achievement in existingAchivements.iteritems():
        if achievement.achievementID in completedDict:
            continue
        if achievement.IsAchievementFullfilled(statsTrakcer.GetStatistics()):
            timestamp = blue.os.GetWallclockTime()
            statsTrakcer.AddAchievement(achievement.achievementID, dateAchieved=timestamp)
            newAchievementDict[achievement.achievementID] = timestamp

    return newAchievementDict


def GetClientAchievements(allAchievementsDict):
    clientAchievements = {}
    for achievementID, achievementData in allAchievementsDict.iteritems():
        if not achievementData.isClientAchievement:
            continue
        clientAchievements[achievementID] = achievementData

    return clientAchievements


def GetAchievementsByEventsDict(achievementDict):
    eventDict = defaultdict(set)
    for achievementID, achievementData in achievementDict.iteritems():
        for c in achievementData.conditions:
            eventDict[c.statName].add(achievementID)

    return eventDict
