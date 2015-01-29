#Embedded file name: eve/client/script/environment/spaceObject\sovereigntyClaimMarker.py
import nodemanager
import blue
import eve.common.script.mgt.posConst as pos
from eve.client.script.environment.spaceObject.LargeCollidableStructure import LargeCollidableStructure
STATE_NONE = None
STATE_OFFLINE = 'Offline'
STATE_ONLINING = 'Onlining'
STATE_ONLINE = 'Online'
POS_STATES_TO_STATE = {pos.STRUCTURE_UNANCHORED: STATE_NONE,
 pos.STRUCTURE_ANCHORED: STATE_OFFLINE,
 pos.STRUCTURE_ONLINING: STATE_ONLINING,
 pos.STRUCTURE_REINFORCED: STATE_ONLINE,
 pos.STRUCTURE_ONLINE: STATE_ONLINE,
 pos.STRUCTURE_OPERATING: STATE_ONLINE,
 pos.STRUCTURE_VULNERABLE: STATE_ONLINE,
 pos.STRUCTURE_SHIELD_REINFORCE: STATE_ONLINE,
 pos.STRUCTURE_ARMOR_REINFORCE: STATE_ONLINE,
 pos.STRUCTURE_INVULNERABLE: STATE_ONLINE}
NANO_CONTAINER = 'res:/dx9/Model/deployables/nanocontainer/nanocontainer.red'

class SovereigntyClaimMarker(LargeCollidableStructure):
    __notifyevents__ = ['OnAllianceLogoReady']
    _animationStates = 'res:/dx9/model/states/tcu.red'

    def __init__(self):
        LargeCollidableStructure.__init__(self)
        sm.RegisterNotify(self)

    def GetAnimationState(self, posState):
        return POS_STATES_TO_STATE.get(posState, STATE_NONE)

    def GetPosState(self):
        slimItem = self.typeData['slimItem']
        return getattr(slimItem, 'posState', None)

    def LoadModel(self, fileName = None, loadedModel = None):
        animationState = self.GetAnimationState(self.GetPosState())
        if animationState is STATE_NONE:
            LargeCollidableStructure.LoadModel(self, NANO_CONTAINER)
        else:
            LargeCollidableStructure.LoadModel(self)
            self.LoadAllianceLogo()
            self.TriggerAnimation(animationState)

    def OnSlimItemUpdated(self, slimItem):
        """Notification from the ballpark that the SlimItem has been changed"""
        oldPosState = self.GetPosState()
        newPosState = getattr(slimItem, 'posState', None)
        if newPosState is None or oldPosState == newPosState:
            return
        self.typeData['slimItem'].posState = newPosState
        if self.GetAnimationState(oldPosState) is None or self.GetAnimationState(newPosState) is None:
            self.RemoveAndClearModel(self.model)
            self.LoadModel()
        animationState = self.GetAnimationState(newPosState)
        if animationState is not STATE_NONE:
            self.TriggerAnimation(animationState)
        self.PlaySounds(oldPosState, newPosState)

    def LoadAllianceLogo(self):
        """Load the alliance Logo into the texture"""
        if self.ballpark is None or self.id not in self.ballpark.slimItems:
            return
        allianceID = self.typeData['slimItem'].allianceID
        iconPath = self.sm.GetService('photo').GetAllianceLogo(allianceID, 128, callback=True)
        if iconPath is not None:
            self._ApplyAllianceLogo(iconPath)

    def _ApplyAllianceLogo(self, iconPath):
        screenNode = nodemanager.FindNode(self.model.planeSets, 'Hologram', 'trinity.EvePlaneSet')
        for res in screenNode.effect.resources:
            if res.name == 'ImageMap':
                res.resourcePath = iconPath

    def OnAllianceLogoReady(self, allianceID):
        if self.ballpark is None or self.id not in self.ballpark.slimItems:
            return
        if self.model is None:
            return
        slimItem = self.typeData['slimItem']
        if slimItem.allianceID == allianceID:
            iconPath = self.sm.GetService('photo').GetAllianceLogo(allianceID, 128, orderIfMissing=False)
            if iconPath is not None:
                self._ApplyAllianceLogo(iconPath)

    def PlaySounds(self, oldState, posState):
        """ Play the sound effect that are associated with the state change"""
        if oldState == pos.STRUCTURE_ONLINING and posState == pos.STRUCTURE_ONLINE:
            self.PlayGeneralAudioEvent('wise:/msg_ct_online_play')
        elif oldState == pos.STRUCTURE_ONLINE and posState == pos.STRUCTURE_ANCHORED:
            self.PlayGeneralAudioEvent('wise:/msg_ct_online_play')
        elif oldState == pos.STRUCTURE_UNANCHORED and posState == pos.STRUCTURE_ANCHORED:
            self.PlayGeneralAudioEvent('wise:/msg_ct_assembly_play')
        elif oldState == pos.STRUCTURE_ANCHORED and posState == pos.STRUCTURE_UNANCHORED:
            self.PlayGeneralAudioEvent('wise:/msg_ct_disassembly_play')

    def DelayedRemove(self, model, delay):
        """In X ms delete the model, this allows for lazy unloading of assets. """
        model.name += '_removing'
        blue.pyos.synchro.SleepWallclock(delay)
        model.display = False
        self.RemoveAndClearModel(model)
