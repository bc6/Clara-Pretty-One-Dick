#Embedded file name: achievements/common\achievementGroups.py
from achievements.common.achievementConst import AchievementConsts

class AchievementGroup(object):

    def __init__(self, groupName, groupHint, extraInfo, groupAchievementIDs, iconPath, groupID, *args):
        self.groupName = groupName
        self.groupHint = groupHint
        self.groupID = groupID
        self.iconPath = iconPath
        self.SetExtraInfo(extraInfo)
        self.achievements = []
        self.AddAchievements(groupAchievementIDs)

    def SetExtraInfo(self, extraInfo, *args):
        self.extraInfo = extraInfo

    def AddAchievements(self, achievements):
        self.achievements.extend(achievements)

    def AddAchievements(self, achievementIDs):
        achievementList = []
        allAchievements = sm.GetService('achievementSvc').allAchievements
        for aID in achievementIDs:
            a = allAchievements.get(aID, None)
            if not a:
                continue
            achievementList.append(a)

        if achievementList:
            self.achievements.extend(achievementList)


class AllAchievementGroups(object):

    def GetGroups(self):
        BASIC = AchievementGroup(groupName='Explore the Universe', groupHint='Find a stargate or station by right clicking anywhere in space or by looking for their icons in space or the overview', extraInfo=[{'text': 'Stargate',
          'path': 'res:/UI/Texture/Icons/38_16_251.png',
          'size': 16}, {'text': 'Station',
          'path': 'res:/UI/Texture/Icons/38_16_252.png',
          'size': 16}], groupID=1, iconPath='res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Explore.png', groupAchievementIDs=[AchievementConsts.USE_STARGATE, AchievementConsts.DOCK_IN_STATION, AchievementConsts.WARP])
        MARKET = AchievementGroup(groupName='Master the market', groupHint='Trade with other players through the market', extraInfo=[], groupID=2, iconPath='res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Market.png', groupAchievementIDs=[AchievementConsts.PLACE_BUY_ORDER, AchievementConsts.PLACE_SELL_ORDER])
        AGENTS = AchievementGroup(groupName='Run Missions', groupHint='Mission agents can be found inside stations', extraInfo=[], groupID=3, iconPath='res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Missions.png', groupAchievementIDs=[AchievementConsts.TALK_TO_AGENT, AchievementConsts.ACCEPT_MISSION])
        NPCS = AchievementGroup(groupName='Hunt Your Enemies', groupHint='Hostile, non-player ships can always be indentified by their red icon color', extraInfo=[{'text': 'Hostile NPC',
          'path': 'res:/UI/Texture/Icons/38_16_22.png',
          'size': 16,
          'color': (1, 0, 0, 1)}, {'text': 'Hostile NPC',
          'path': 'res:/UI/Texture/Icons/38_16_21.png',
          'size': 16,
          'color': (1, 0, 0, 1)}], groupID=4, iconPath='res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Combat.png', groupAchievementIDs=[AchievementConsts.KILL_NPC])
        SKILLS = AchievementGroup(groupName='Grow in Power', groupHint='Your skills are shown in the Character Sheet and you can train a new one by simply right clicking any skill', extraInfo=[], groupID=5, iconPath='res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Skills.png', groupAchievementIDs=[AchievementConsts.START_TRAINING])
        MINING = AchievementGroup(groupName='Harvest Resources', groupHint='Before you can activate your mining laser you must lock an asteroid', extraInfo=[], groupID=6, iconPath='res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Mining.png', groupAchievementIDs=[AchievementConsts.MINE_ORE])
        return {BASIC.groupID: BASIC,
         MARKET.groupID: MARKET,
         AGENTS.groupID: AGENTS,
         NPCS.groupID: NPCS,
         SKILLS.groupID: SKILLS,
         MINING.groupID: MINING}
