#Embedded file name: achievements/common\achievementController.py
from collections import defaultdict

class AchievementConstants:
    EVENT_TYPE_MINING = 'mining'
    EVENT_TYPE_JUMP = 'jump'
    EVENT_TYPE_KILL = 'kill'
    EVENT_TYPE_TRACKING_CAMERA = 'TrackingEnabled'


class AchievementCondition(object):

    def __init__(self):
        pass

    def IsFullfilled(self, statDict):
        pass


class AchievementSimpleCondition(AchievementCondition):

    def __init__(self, statName, targetValue):
        self.statName = statName
        self.targetValue = targetValue

    def IsFullfilled(self, statsDict):
        fullfilled = False
        if self.statName in statsDict:
            value = int(statsDict[self.statName])
            fullfilled = value >= self.targetValue
        return fullfilled

    def __str__(self):
        return self.statName + ' Needs to be value: ' + str(self.targetValue)


class AchievementTracker(object):

    def __init__(self, notifyCallback):
        self.value = 0
        self.triggerValue = 10
        self.notifyCallback = notifyCallback

    def LogEvent(self, value):
        self.value += value
        self.checkAndNotify()

    def checkAndNotify(self):
        if self.HasFullfilledCondition():
            self.Notify()

    def Notify(self):
        self.notifyCallback('success', self)

    def HasFullfilledCondition(self):
        return self.value >= self.triggerValue


class AchievementConditionData(object):

    def __init__(self, eventName, eventType, value):
        self.eventName = eventName
        self.eventType = eventType
        self.value = value


class ExampleConditionProducer(object):

    def __init__(self):
        self.datas = {}

    def GetExampleConditionData(self):
        list = []
        list.append(AchievementConditionData('oreMined', 'ore', 1))


class AchievementService(object):

    def __init__(self, scatterService):
        self.sm = scatterService
        self.activeAchievementTracking = {}
        self.achievementTracker = AchievementTracker(self.OnTrackerNotify)
        self.statsTracker = StatsTracker()

    def OnTrackerNotify(self, sender):
        print 'Service notified'

    def _achievementUnlocked(self, achievement):
        self.sm.scatterEvent(achievement)

    def GetAvailableAchievements(self):
        return self.GetFakeEntries()

    def LogEvent(self, eventType, count = 1, extrainfo = None):
        self.statsTracker.LogStatistic(eventType, count)

    def GetFakeEntries(self):
        list = []
        list.append(Achievement(1, 'Kill', 'Kill Description'))
        list.append(Achievement(2, 'Mine', 'Mine Description'))
        list.append(Achievement(3, 'Die', 'Die Description'))
        list.append(Achievement(4, 'Say hi', 'Say Description'))
        list.append(Achievement(5, 'Say bye', 'Say Description'))
        list.append(Achievement(6, 'join corp', 'join Description'))
        list.append(Achievement(7, 'leave corp', 'leave Description'))
        list.append(Achievement(8, 'Win', 'Win Description'))
        return list


class Achievement(object):

    def __init__(self, id, name, description, completed = False, conditions = None, notificationText = None):
        self.id = id
        self.name = name
        self.description = description
        self.notificationText = notificationText
        self.completed = completed
        if conditions is None:
            self.conditions = []
        else:
            self.conditions = conditions

    def AddCondition(self, condition):
        self.conditions.append(condition)

    def GetConditions(self):
        return self.conditions


class AchievementWrapper(object):

    def __init__(self, achievementID, conditions = []):
        self.achievementID = achievementID
        self.conditions = conditions

    def AddCondition(self, condition):
        self.conditions.append(condition)


class BelowZeroCountException(Exception):
    pass


class StatsTracker(object):

    def __init__(self):
        self.statistics = defaultdict(int)
        self.extraInfo = {}
        self.achievedSet = set()
        self.ResetUnloggedStats()
        self.ResetUnloggedAchievements()

    def GetStatValue(self, key):
        return self.statistics[key]

    def ThrowErrorIfBelowZero(self, count):
        if count < 0:
            raise BelowZeroCountException()

    def LogStatistic(self, key, count = 1, addToUnlogged = True):
        self.ThrowErrorIfBelowZero(count)
        if count < 1:
            return
        self.statistics[key] += count
        if addToUnlogged:
            self.unloggedStats[key] += count

    def GetStatistics(self):
        return self.statistics

    def GetCurrentAchievements(self):
        return self.achievedSet

    def AddAchievement(self, achievementID, addToUnlogged = True):
        self.achievedSet.add(achievementID)
        if addToUnlogged:
            self.unloggedAchievements.add(achievementID)

    def GetUnloggedStats(self):
        return self.unloggedStats

    def ResetUnloggedStats(self):
        self.unloggedStats = defaultdict(int)

    def GetUnloggedAchievements(self):
        return self.unloggedAchievements

    def ResetUnloggedAchievements(self):
        self.unloggedAchievements = set()

    def ResetStatistics(self):
        self.statistics.clear()

    def ResetAchieved(self):
        self.achievedSet.clear()

    def RemoveAchieved(self, achievementID):
        if achievementID in self.achievedSet:
            self.achievedSet.remove(achievementID)

    def RemoveEvent(self, eventName):
        self.statistics.pop(eventName, None)
