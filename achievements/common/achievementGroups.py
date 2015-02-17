#Embedded file name: achievements/common\achievementGroups.py
from achievements.common.achievementConst import AchievementConsts
from localization import GetByLabel

class AchievementGroup(object):
    achievementTasks = None

    def __init__(self, groupID, nameLabelPath, descriptionLabelPath, notificationPath, extraInfo, achievementTaskIDs, groupConnections, treePosition, *args, **kwargs):
        self.groupID = groupID
        self.groupName = GetByLabel(nameLabelPath)
        self.groupDescription = GetByLabel(descriptionLabelPath)
        self.groupConnections = groupConnections
        self.achievementTaskIDs = achievementTaskIDs
        self.treePosition = treePosition
        self.extraInfo = extraInfo
        self.notificationPath = notificationPath

    def GetAchievementTaskIDs(self):
        return self.achievementTaskIDs

    def GetAchievementTasks(self):
        if self.achievementTasks is None:
            self.achievementTasks = []
            allAchievements = sm.GetService('achievementSvc').allAchievements
            for achievementTaskID in self.achievementTaskIDs:
                self.achievementTasks.append(allAchievements[achievementTaskID])

        return self.achievementTasks

    def IsCompleted(self):
        groupTasks = self.GetAchievementTasks()
        totalNum = len(groupTasks)
        completed = len([ x for x in groupTasks if x.completed ])
        return totalNum == completed

    def HasAchievement(self, achievementID):
        return achievementID in self.achievementTaskIDs

    def GetNextIncompleteTask(self):
        tasks = self.GetAchievementTasks()
        for each in tasks:
            if not each.completed:
                return each

    def GetFirstCompletedTask(self):
        tasks = self.GetAchievementTasks()
        for each in tasks:
            if each.completed:
                return each

    def GetProgressProportion(self):
        tasks = self.GetAchievementTasks()
        total = len(tasks)
        completed = 0
        for each in tasks:
            if each.completed:
                completed += 1

        return completed / float(total)


achievementGroups = [AchievementGroup(nameLabelPath='Achievements/GroupNameText/fly', descriptionLabelPath='Achievements/GroupDescriptionText/fly', notificationPath='Achievements/GroupNotificationText/fly', extraInfo=[], groupID=11, achievementTaskIDs=[AchievementConsts.DOUBLE_CLICK, AchievementConsts.APPROACH], groupConnections=[12], treePosition=(3, 1)),
 AchievementGroup(nameLabelPath='Achievements/GroupNameText/kill', descriptionLabelPath='Achievements/GroupDescriptionText/kill', notificationPath='Achievements/GroupNotificationText/kill', extraInfo=[], groupID=12, achievementTaskIDs=[AchievementConsts.ORBIT_NPC,
  AchievementConsts.LOCK_NPC,
  AchievementConsts.ACTIVATE_GUN,
  AchievementConsts.KILL_NPC,
  AchievementConsts.LOOT_FROM_NPC_WRECK], groupConnections=[13], treePosition=(4, 1)),
 AchievementGroup(nameLabelPath='Achievements/GroupNameText/mine', descriptionLabelPath='Achievements/GroupDescriptionText/mine', notificationPath='Achievements/GroupNotificationText/mine', extraInfo=[], groupID=13, achievementTaskIDs=[AchievementConsts.ORBIT_ASTEROID,
  AchievementConsts.LOCK_ASTEROID,
  AchievementConsts.ACTIVATE_MINER,
  AchievementConsts.MINE_ORE], groupConnections=[14], treePosition=(5, 1)),
 AchievementGroup(nameLabelPath='Achievements/GroupNameText/warp', descriptionLabelPath='Achievements/GroupDescriptionText/warp', notificationPath='Achievements/GroupNotificationText/warp', extraInfo=[], groupID=14, achievementTaskIDs=[AchievementConsts.WARP], groupConnections=[15], treePosition=(5, 2)),
 AchievementGroup(nameLabelPath='Achievements/GroupNameText/station', descriptionLabelPath='Achievements/GroupDescriptionText/station', notificationPath='Achievements/GroupNotificationText/station', extraInfo=[], groupID=15, achievementTaskIDs=[AchievementConsts.DOCK_IN_STATION,
  AchievementConsts.MOVE_FROM_CARGO_TO_HANGAR,
  AchievementConsts.FIT_ITEM,
  AchievementConsts.PLACE_BUY_ORDER,
  AchievementConsts.UNDOCK_FROM_STATION], groupConnections=[16], treePosition=(4, 3)),
 AchievementGroup(nameLabelPath='Achievements/GroupNameText/stargate', descriptionLabelPath='Achievements/GroupDescriptionText/stargate', notificationPath='Achievements/GroupNotificationText/stargate', extraInfo=[], groupID=16, achievementTaskIDs=[AchievementConsts.USE_STARGATE], groupConnections=[], treePosition=(3, 2))]

def GetAchievementGroups():
    return achievementGroups


def GetFirstIncompleteAchievementGroup():
    for each in achievementGroups:
        if not each.IsCompleted():
            return each


def GetNextAchievementGroup(fromGroupID):
    allGroupIDs = [ each.groupID for each in achievementGroups ]
    if fromGroupID in allGroupIDs:
        fIndex = allGroupIDs.index(fromGroupID)
        if len(allGroupIDs) > fIndex + 1:
            return allGroupIDs[fIndex + 1]
        return None
    return allGroupIDs[0]


def GetAchievementGroup(groupID):
    for each in achievementGroups:
        if each.groupID == groupID:
            return each


def GetGroupForAchievement(achievementID):
    for eachGroup in achievementGroups:
        if achievementID in eachGroup.achievementTaskIDs:
            return eachGroup


def GetActiveAchievementGroup():
    activeGroupID = sm.GetService('achievementSvc').GetActiveAchievementGroupID()
    return GetAchievementGroup(activeGroupID)


def HasCompletedAchievementGroup():
    for each in achievementGroups:
        if each.IsCompleted():
            return True

    return False


def HasCompletedAchievementTask():
    for each in achievementGroups:
        if each.GetFirstCompletedTask():
            return True

    return False
