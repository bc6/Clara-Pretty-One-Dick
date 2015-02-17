#Embedded file name: achievements/common\achievementEvent.py
from achievements.common.achievementConst import AchievementEventConst
import eve.common.lib.infoEventConst as infoEventConst
achievementEventNamesByLogEventIDs = {infoEventConst.infoEventNPCKilled: [{'eventName': AchievementEventConst.HOSTILE_NPC_DESTROY,
                                      'logWhat': None}],
 infoEventConst.infoEventRefinedTypesAmount: [{'eventName': AchievementEventConst.INDUSTRY_REFINE_ORE_COUNT,
                                               'logWhat': None}],
 infoEventConst.infoEventOreMined: [{'eventName': AchievementEventConst.MINING_TIMES_MINED,
                                     'logWhat': None}, {'eventName': AchievementEventConst.MINING_TOTAL_MINED,
                                     'logWhat': 'int_2'}]}

def GetAchievementEventInfoFromLogEventID(logEventID):
    return achievementEventNamesByLogEventIDs.get(logEventID, None)


def IsEventAnAchievement(logEventID):
    return logEventID in achievementEventNamesByLogEventIDs
