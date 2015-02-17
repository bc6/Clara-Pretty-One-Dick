#Embedded file name: achievements/common\extraInfoForTasks.py
from achievements.common.achievementConst import AchievementConsts
noobWeaponsByRaceID = {const.raceAmarr: 'res:/UI/Texture/Icons/13_64_13.png',
 const.raceCaldari: 'res:/UI/Texture/Icons/13_64_5.png',
 const.raceGallente: 'res:/UI/Texture/Icons/13_64_1.png',
 const.raceMinmatar: 'res:/UI/Texture/Icons/12_64_9.png'}

def GetWeaponTexturePathFromRace():
    return noobWeaponsByRaceID.get(session.raceID)


class TaskInfoEntry_ImageText(object):

    def __init__(self, text, imagePath, imageSize, imageColor = (1, 1, 1, 1), textColor = (1, 1, 1, 0.75), imagePathFetchFunc = None):
        self.textPath = text
        self.textColor = textColor
        self.imagePath = imagePath
        self.imageSize = imageSize
        self.imageColor = imageColor
        self.imagePathFetchFunc = imagePathFetchFunc

    def GetTexturePath(self):
        if self.imagePath:
            return self.imagePath
        if self.imagePathFetchFunc:
            return self.imagePathFetchFunc()


class TaskInfoEntry_Text(object):

    def __init__(self, text, textColor = (1, 1, 1, 0.75)):
        self.text = text
        self.textColor = textColor


ORBIT_TASKINFO = TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/OrbitCommand', imagePath='res:/UI/Texture/Icons/44_32_21.png', imageSize=32)
LOCK_TASKINFO = TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/LockCommand', imagePath='res:/UI/Texture/Icons/44_32_17.png', imageSize=32)
HOSTILE_NPC_TASKINFO = [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/HostileNPC', imagePath='res:/UI/Texture/Icons/38_16_22.png', imageSize=16, imageColor=(1, 0, 0, 1)), TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/HostileNPC', imagePath='res:/UI/Texture/Icons/38_16_21.png', imageSize=16, imageColor=(1, 0, 0, 1))]
ACHIEVEMENT_TASK_EXTRAINFO = {AchievementConsts.APPROACH: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/ApproachCommand', imagePath='res:/UI/Texture/icons/44_32_23.png', imageSize=32)],
 AchievementConsts.ORBIT_NPC: [ORBIT_TASKINFO] + HOSTILE_NPC_TASKINFO,
 AchievementConsts.LOCK_NPC: [LOCK_TASKINFO],
 AchievementConsts.ACTIVATE_GUN: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/Gun', imagePath=None, imagePathFetchFunc=GetWeaponTexturePathFromRace, imageSize=32)],
 AchievementConsts.KILL_NPC: HOSTILE_NPC_TASKINFO,
 AchievementConsts.LOOT_FROM_NPC_WRECK: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/WreckBracket', imagePath='res:/UI/Texture/Icons/38_16_29.png', imageSize=16)],
 AchievementConsts.ORBIT_ASTEROID: [ORBIT_TASKINFO],
 AchievementConsts.LOCK_ASTEROID: [LOCK_TASKINFO],
 AchievementConsts.ACTIVATE_MINER: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/MiningLaser', imagePath='res:/UI/Texture/Icons/12_64_8.png', imageSize=32)],
 AchievementConsts.WARP: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/WarpCommand', imagePath='res:/UI/Texture/Icons/44_32_18.png', imageSize=32)],
 AchievementConsts.DOCK_IN_STATION: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/DockCommand', imagePath='res:/UI/Texture/Icons/44_32_9.png', imageSize=32), TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/StationBracket', imagePath='res:/UI/Texture/Icons/38_16_252.png', imageSize=16)],
 AchievementConsts.MOVE_FROM_CARGO_TO_HANGAR: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/InventoryNeocom', imagePath='res:/ui/Texture/WindowIcons/items.png', imageSize=32)],
 AchievementConsts.FIT_ITEM: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/FittingNeocom', imagePath='res:/ui/Texture/WindowIcons/fitting.png', imageSize=32)],
 AchievementConsts.PLACE_BUY_ORDER: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/MarketNeocom', imagePath='res:/ui/Texture/WindowIcons/market.png', imageSize=32)],
 AchievementConsts.UNDOCK_FROM_STATION: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/UndockStationServices', imagePath='res:/ui/Texture/classes/Achievements/undockIcon.png', imageSize=32)],
 AchievementConsts.USE_STARGATE: [TaskInfoEntry_ImageText(text='UI/Achievements/TooltipExtraInfo/StargateBracket', imagePath='res:/UI/Texture/Icons/38_16_251.png', imageSize=16)]}
