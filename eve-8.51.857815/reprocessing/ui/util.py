#Embedded file name: reprocessing/ui\util.py
from dogma.const import attributeRefiningYieldMutator, attributeReprocessingSkillType
from inventorycommon.const import categoryAsteroid, typeReprocessing, typeReprocessingEfficiency, typeScrapmetalProcessing
from inventorycommon.types import GetCategoryID

def GetSkillFromTypeID(typeID, getTypeAttribute, getSkillLevel):
    categoryID = GetCategoryID(typeID)
    ret = GetSkillBonuses(categoryID, getTypeAttribute, getSkillLevel)
    if categoryID == categoryAsteroid:
        attribRet = GetAttributeSkillsFromTypeID(typeID, getTypeAttribute, getSkillLevel)
        ret.append(attribRet)
    return ret


def GetSkillBonuses(categoryID, getTypeAttribute, getSkillLevel):
    ret = []
    if categoryID == categoryAsteroid:
        skillLevelReprocessing = GetSkillLevel(getSkillLevel, typeReprocessing)
        ret.append((typeReprocessing, skillLevelReprocessing * getTypeAttribute(typeReprocessing, attributeRefiningYieldMutator)))
        skillLevelEfficiency = GetSkillLevel(getSkillLevel, typeReprocessingEfficiency)
        ret.append((typeReprocessingEfficiency, skillLevelEfficiency * getTypeAttribute(typeReprocessingEfficiency, attributeRefiningYieldMutator)))
    else:
        skillLevelScrapmetalProcessing = GetSkillLevel(getSkillLevel, typeScrapmetalProcessing)
        ret.append((typeScrapmetalProcessing, skillLevelScrapmetalProcessing * getTypeAttribute(typeScrapmetalProcessing, attributeRefiningYieldMutator)))
    return ret


def GetSkillLevel(getSkillLevel, skillType):
    skillLevel = getSkillLevel(skillType)
    if skillLevel is None:
        skillLevel = 0
    return skillLevel


def GetAttributeSkillsFromTypeID(typeID, getTypeAttribute, getSkillLevel):
    skillTypeID = getTypeAttribute(typeID, attributeReprocessingSkillType)
    if skillTypeID is None:
        ret = (None, 0)
    else:
        skillLevel = GetSkillLevel(getSkillLevel, skillTypeID)
        ret = (skillTypeID, skillLevel * getTypeAttribute(skillTypeID, attributeRefiningYieldMutator))
    return ret


def GetSkillFromCategoryID(categoryID, getTypeAttribute, getSkillLevel):
    return GetSkillBonuses(categoryID, getTypeAttribute, getSkillLevel)
