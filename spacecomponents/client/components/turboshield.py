#Embedded file name: spacecomponents/client/components\turboshield.py
import logging
from clienteffects import StartShipEffect, StopShipEffect
from spacecomponents.client.messages import MSG_ON_SLIM_ITEM_UPDATED, MSG_ON_TARGET_BRACKET_ADDED, MSG_ON_TARGET_BRACKET_REMOVED
from spacecomponents.common.components.component import Component
from spacecomponents.client.messages import MSG_ON_ADDED_TO_SPACE
from spacecomponents.common.components.turboshield import TURBO_SHIELD_STATE_ACTIVE, TURBO_SHIELD_STATE_INVULNERABLE
logger = logging.getLogger(__name__)
TURBO_SHIELD_EFFECT = 'effects.TurboShield'
EFFECT_DURATION = 7500

class TurboShield(Component):

    def __init__(self, itemID, typeID, attributes, componentRegistry):
        super(TurboShield, self).__init__(itemID, typeID, attributes, componentRegistry)
        self.turboShieldState = None
        self.SubscribeToMessage(MSG_ON_ADDED_TO_SPACE, self.OnAddedToSpace)
        self.SubscribeToMessage(MSG_ON_SLIM_ITEM_UPDATED, self.OnSlimItemUpdated)
        self.SubscribeToMessage(MSG_ON_TARGET_BRACKET_ADDED, self.OnTargetBracketAdded)
        self.SubscribeToMessage(MSG_ON_TARGET_BRACKET_REMOVED, self.OnTargetBracketRemoved)
        self.targetBracket = None

    def OnAddedToSpace(self, slimItem):
        logger.debug('TurboShield.OnAddedToSpace %d', self.itemID)
        self.OnSlimItemUpdated(slimItem)

    def OnSlimItemUpdated(self, slimItem):
        turboShieldMode = slimItem.component_turboshield or False
        if turboShieldMode != self.turboShieldState:
            self.turboShieldState = turboShieldMode
            self.UpdateHullEffect()
            self.UpdateTargetBracket()

    def UpdateHullEffect(self):
        if self.turboShieldState == TURBO_SHIELD_STATE_ACTIVE:
            StartShipEffect(self.itemID, TURBO_SHIELD_EFFECT, 7500, 9999)
        if self.turboShieldState == TURBO_SHIELD_STATE_INVULNERABLE:
            StopShipEffect(self.itemID, TURBO_SHIELD_EFFECT)

    def OnTargetBracketAdded(self, targetBracket):
        logger.debug('Target bracket added')
        self.targetBracket = targetBracket
        self.UpdateTargetBracket()

    def UpdateTargetBracket(self):
        if self.targetBracket:
            if self.turboShieldState == TURBO_SHIELD_STATE_ACTIVE:
                texturePath = 'res:/UI/Texture/classes/Target/turboShieldGaugeColor.png'
            else:
                texturePath = None
            self.targetBracket.SetGaugeTextureForBar('shieldBar', texturePath)

    def OnTargetBracketRemoved(self):
        logger.debug('Target bracket removed')
        self.targetBracket = None
