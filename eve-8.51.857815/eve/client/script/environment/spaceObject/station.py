#Embedded file name: eve/client/script/environment/spaceObject\station.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import sys
import eve.common.script.mgt.posConst as pos
SHIELD_EFFECT = 'effects.ModifyShieldResonance'
ARMOR_EFFECT = 'effects.StructureRepair'

class Station(SpaceObject):

    def LoadModel(self, fileName = None, loadedModel = None):
        npcStation = cfg.mapSolarSystemContentCache.npcStations.get(self.id, None)
        if npcStation:
            graphicID = npcStation.graphicID
            graphicFile = cfg.graphics.Get(graphicID).graphicFile
        else:
            graphicFile = self.typeData.get('graphicFile')
        SpaceObject.LoadModel(self, fileName=graphicFile)
        self.fx = self.sm.GetService('FxSequencer')
        self.stationState = pos.STRUCTURE_ONLINE
        self.HandleStateChange()

    def Assemble(self):
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        self.SetupAmbientAudio()
        self.HandleStateChange()

    def OnSlimItemUpdated(self, newSlim):
        self.HandleStateChange()

    def HandleStateChange(self):
        """Handle the state change and start the visual effects. """
        if self.stationState == pos.STRUCTURE_SHIELD_REINFORCE:
            self.ShieldReinforced(False)
        elif self.stationState == pos.STRUCTURE_ARMOR_REINFORCE:
            self.ArmorReinforced(False)
        slimItem = self.ballpark.GetInvItem(self.id)
        if slimItem.structureState == pos.STRUCTURE_SHIELD_REINFORCE:
            self.ShieldReinforced(True)
        elif slimItem.structureState == pos.STRUCTURE_ARMOR_REINFORCE:
            self.ArmorReinforced(True)
        self.stationState = slimItem.structureState

    def ShieldReinforced(self, startEffect):
        """Start and stop the shield effect, this will use maxint number of repetitions as the state will persist across downtimes. """
        self.fx.OnSpecialFX(self.id, None, None, None, None, SHIELD_EFFECT, False, startEffect, True, repeat=sys.maxint)

    def ArmorReinforced(self, startEffect):
        """Start and stop the armor effect, this will use maxint number of repetitions as the state will persist across downtimes. """
        self.fx.OnSpecialFX(self.id, None, None, None, None, ARMOR_EFFECT, False, startEffect, True, repeat=sys.maxint)
