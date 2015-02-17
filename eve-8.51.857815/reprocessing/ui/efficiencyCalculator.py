#Embedded file name: reprocessing/ui\efficiencyCalculator.py
from reprocessing.ui.util import GetSkillFromTypeID

def CalculateTheoreticalEfficiency(typeIDs, tax, efficiency):
    getTypeAttribute = sm.GetService('clientDogmaStaticSvc').GetTypeAttribute
    getSkillLevel = sm.GetService('skills').MySkillLevel
    bonuses = []
    for typeID in typeIDs:
        skillBonuses = GetSkillFromTypeID(typeID, getTypeAttribute, getSkillLevel)
        totalSkillBonus = 1.0
        for _, bonus in skillBonuses:
            totalSkillBonus *= 1 + bonus / 100

        bonuses.append(100 * (totalSkillBonus - 1))

    avgSkillBonus = sum(bonuses) / len(typeIDs)
    return efficiency * (1 - tax) * (100 + avgSkillBonus) / 100
