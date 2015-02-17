#Embedded file name: eve/client/script/environment/spaceObject\sovereigntyInfrastructueHub.py
import blue
from eve.client.script.environment.spaceObject.playerOwnedStructure import PlayerOwnedStructure
import eve.common.script.mgt.posConst as pos
import sys
SHIELD_EFFECT = 'effects.ModifyShieldResonance'
ARMOR_EFFECT = 'effects.StructureRepair'

class SovereigntyInfrastructueHub(PlayerOwnedStructure):

    def LoadModel(self, fileName = None, loadedModel = None):
        PlayerOwnedStructure.LoadModel(self, fileName, loadedModel)
        posState = self.typeData['slimItem'].posState
        if posState is None:
            return
        self.HandleStateChange(posState)

    def OnSlimItemUpdated(self, slimItem):
        self.HandleStateChange(slimItem.posState)

    def HandleStateChange(self, posState):
        self.ShieldReinforced(False)
        self.ArmorReinforced(False)
        if posState == pos.STRUCTURE_SHIELD_REINFORCE:
            self.ShieldReinforced(True)
        elif posState == pos.STRUCTURE_ARMOR_REINFORCE:
            self.ArmorReinforced(True)

    def ShieldReinforced(self, startEffect):
        """Start and stop the shield effect, this will use maxint number of repetitions as the state will persist across downtimes. """
        fx = self.sm.GetService('FxSequencer')
        fx.OnSpecialFX(self.id, None, None, None, None, SHIELD_EFFECT, False, startEffect, True, repeat=sys.maxint)

    def ArmorReinforced(self, startEffect):
        """Start and stop the armor effect, this will use maxint number of repetitions as the state will persist across downtimes. """
        fx = self.sm.GetService('FxSequencer')
        fx.OnSpecialFX(self.id, None, None, None, None, ARMOR_EFFECT, False, startEffect, True, repeat=sys.maxint)
