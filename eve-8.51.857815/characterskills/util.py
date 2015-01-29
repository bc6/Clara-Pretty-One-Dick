#Embedded file name: characterskills\util.py
import math
import blue
import carbon.common.lib.const as const
import characterskills.const
import dogma.const as dogmaConst
DIVCONSTANT = math.log(2) * 2.5

def GetSPForAllLevels(skillTimeConstant):
    levelList = []
    for i in range(characterskills.const.maxSkillLevel + 1):
        levelList.append(GetSPForLevelRaw(skillTimeConstant, i))

    return levelList


def GetSkillPointsPerMinute(primaryAttributeValue, secondaryAttributeValue):
    pointsPerMinute = primaryAttributeValue + secondaryAttributeValue / 2.0
    return pointsPerMinute


def GetSPForLevelRaw(skillTimeConstant, level):
    if level <= 0:
        return 0
    if level > characterskills.const.maxSkillLevel:
        level = characterskills.const.maxSkillLevel
    skillTimeConstant = skillTimeConstant * characterskills.const.skillPointMultiplier
    ret = skillTimeConstant * 2 ** (2.5 * (level - 1))
    return int(math.ceil(ret))


def GetSkillLevelRaw(skillPoints, skillTimeConstant):
    baseSkillLevelConstant = skillTimeConstant * characterskills.const.skillPointMultiplier
    if baseSkillLevelConstant > skillPoints or baseSkillLevelConstant == 0:
        return 0
    return min(int(math.log(skillPoints / baseSkillLevelConstant) / DIVCONSTANT) + 1, characterskills.const.maxSkillLevel)


CHINA_SKILLQUEUE_TIME = const.DAY
TRIAL_SKILLQUEUE_TIME = const.DAY
NORMAL_SKILLQUEUE_TIME = 10 * const.YEAR365
SKILLQUEUE_MAX_NUM_SKILLS = 50
DISPLAY_SKILLQUEUE_LENGTH = const.DAY
USER_TYPE_NOT_ENFORCED = -1

def HasShortSkillqueue(userType):
    if IsTrialRestricted(userType) or IsChinaRestricted():
        return True
    return False


def IsTrialRestricted(userType):
    return userType == const.userTypeTrial


def IsChinaRestricted():
    return boot.region == 'optic'


def GetSkillQueueTimeLength(userType):
    if IsChinaRestricted():
        length = CHINA_SKILLQUEUE_TIME
    elif IsTrialRestricted(userType):
        length = TRIAL_SKILLQUEUE_TIME
    else:
        length = NORMAL_SKILLQUEUE_TIME
    return length


ATTRIBUTEBONUS_BY_ATTRIBUTEID = {dogmaConst.attributePerception: dogmaConst.attributePerceptionBonus,
 dogmaConst.attributeMemory: dogmaConst.attributeMemoryBonus,
 dogmaConst.attributeWillpower: dogmaConst.attributeWillpowerBonus,
 dogmaConst.attributeIntelligence: dogmaConst.attributeIntelligenceBonus,
 dogmaConst.attributeCharisma: dogmaConst.attributeCharismaBonus}

def IsBoosterExpiredThen(timeOffset, boosterExpiryTime = None):
    if boosterExpiryTime > blue.os.GetWallclockTime() + timeOffset:
        return False
    return True


def FindAttributeBooster(dogmaIM, boosters):
    """
        finding the booster that could affect attributes temporarily... it will be in slot 4
    """
    for b in boosters:
        boosterness = dogmaIM.GetTypeAttribute2(b.typeID, dogmaConst.attributeBoosterness)
        if boosterness == 4.0:
            return b


def GetBoosterlessValue(dogmaIM, typeID, attributeID, currentValue):
    effectID = ATTRIBUTEBONUS_BY_ATTRIBUTEID[attributeID]
    boosterEffect = dogmaIM.GetTypeAttribute2(typeID, effectID)
    newValue = currentValue - boosterEffect
    return newValue
