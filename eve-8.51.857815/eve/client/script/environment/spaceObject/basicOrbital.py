#Embedded file name: eve/client/script/environment/spaceObject\basicOrbital.py
"""
This SpaceObject handles graphical effects and model setup for orbital anchorable structures.
This basic version does little more than capture data and set up the model and force it
to face the planet.
"""
import blue
import eve.common.script.mgt.entityConst as entities
from eve.client.script.environment.spaceObject.playerOwnedStructure import PlayerOwnedStructure
import uthread

class BasicOrbital(PlayerOwnedStructure):

    def Assemble(self):
        self.SetStaticRotation()

    def OnSlimItemUpdated(self, slimItem):
        orbitalState = getattr(slimItem, 'orbitalState', None)
        orbitalTimestamp = getattr(slimItem, 'orbitalTimestamp', blue.os.GetSimTime())
        fxSequencer = self.sm.GetService('FxSequencer')
        if not hasattr(self, 'orbitalState'):
            if orbitalState in (entities.STATE_ANCHORING, entities.STATE_ANCHORED):
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.AnchorDrop', 0, 1, 0)
            elif orbitalState in (entities.STATE_IDLE, entities.STATE_OPERATING):
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.StructureOnlined', 0, 1, 0)
        else:
            if orbitalState == entities.STATE_ANCHORING and self.orbitalState == entities.STATE_UNANCHORED:
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.AnchorDrop', 0, 1, 0)
            if orbitalState == entities.STATE_ONLINING and self.orbitalState == entities.STATE_ANCHORED:
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.StructureOnline', 0, 1, 0)
            if orbitalState == entities.STATE_IDLE and self.orbitalState == entities.STATE_ONLINING:
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.StructureOnlined', 0, 1, 0)
            if orbitalState == entities.STATE_ANCHORED and self.orbitalState in (entities.STATE_OFFLINING, entities.STATE_IDLE, entities.STATE_OPERATING):
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.StructureOffline', 0, 1, 0)
            if orbitalState == entities.STATE_UNANCHORING and self.orbitalState == entities.STATE_ANCHORED:
                uthread.pool('SpaceObject::BasicOrbital::OnSlimItemUpdated', fxSequencer.OnSpecialFX, slimItem.itemID, slimItem.itemID, None, None, None, 'effects.AnchorLift', 0, 1, 0)
        self.orbitalState = orbitalState
        self.orbitalTimestamp = orbitalTimestamp

    def IsOnline(self):
        slimItem = self.typeData.get('slimItem')
        return slimItem.orbitalState is not None and slimItem.orbitalState in (entities.STATE_OPERATING, entities.STATE_IDLE)
