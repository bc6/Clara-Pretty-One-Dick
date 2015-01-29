#Embedded file name: dogma/authoring\expressionAuthoring.py
import yaml
from dogma.authoring.expressions import DumpExpression

class ExpressionAuthorer(object):

    def __init__(self, dogmaIM):
        self.dogmaIM = dogmaIM

    def UpdateExpression(self, userID, effect, modifierInfo):
        self.dogmaIM.ModifyEffect(userID, effect.effectID, effect.effectName, effect.effectCategory, effect.preExpression, effect.postExpression, effect.guid, effect.iconID, effect.isOffensive, effect.isAssistance, effect.durationAttributeID, effect.trackingSpeedAttributeID, effect.dischargeAttributeID, effect.rangeAttributeID, effect.falloffAttributeID, effect.published, effect.isWarpSafe, effect.rangeChance, effect.electronicChance, effect.propulsionChance, effect.distribution, effect.sfxName, effect.npcUsageChanceAttributeID, effect.npcActivationChanceAttributeID, effect.fittingUsageChanceAttributeID, DumpExpression(modifierInfo))
