#Embedded file name: carbon/client/script/movement\movementClient.py
"""
This service extends the common movement service and adds the client specific functionality.
"""
import const
import GameWorld
import carbon.common.script.movement.movementService as movsvc

class MovementClient(movsvc.MovementService):
    __guid__ = 'svc.movementClient'
    __notifyevents__ = ['ProcessEntityMove', 'OnSessionChanged']
    __dependencies__ = movsvc.MovementService.__dependencies__[:]
    __dependencies__.extend(['gameWorldClient'])
    reportedMissing = False
    TIME_BEFORE_SENDING = 6 * const.SEC / 30

    def Run(self, *etc):
        movsvc.MovementService.Run(self)
        self.lastSentTime = 0
        self.unsentPlayerMoves = []
        self.movementServer = sm.RemoteSvc('movementServer')
        self.addressCache = {}
        GameWorld.SetupCLevelMovement()

    def OnSessionChanged(self, isRemote, sess, change):
        newworldspaceid = change.get('worldspaceid', (None, None))[1]
        self.LookupWorldSpaceNodeID(newworldspaceid)

    def LookupWorldSpaceNodeID(self, newworldspaceid):
        if newworldspaceid and newworldspaceid not in self.addressCache:
            if self.entityService.IsClientSideOnly(newworldspaceid):
                return None
            nodeid = self.movementServer.ResolveNodeID(newworldspaceid)
            if nodeid:
                self.addressCache[newworldspaceid] = nodeid
            else:
                self.LogError('Trying to resolve a unknown worldspaceid to a node', newworldspaceid)
        return self.addressCache.get(newworldspaceid, None)

    def GetPlayerEntity(self):
        """
        # For WoD this is the entity relating to the player's character.
        return self.gameComponentClient.GetEntityByID(entid)
        
        # For WiS this is the avatar object relating to the player's character.
        return self.GetEntity(session.charid)
        """
        raise StandardError('Not implemented')

    def SetupComponent(self, entity, component):
        """
        Gets called once all components have been registered.
        Use this to setup stuff which references other components
        """
        movsvc.MovementService.SetupComponent(self, entity, component)
        gw = self.gameWorldClient.GetGameWorld(component.sceneID)
        positionComponent = entity.GetComponent('position')
        if entity.entityID == session.charid:
            remoteNodeID = self.LookupWorldSpaceNodeID(entity.scene.sceneID)
            if remoteNodeID is None:
                remoteNodeID = -1
            component.moveModeManager = GameWorld.MoveModeManager(entity.entityID, component.sceneID, const.movement.AVATARTYPE_CLIENT_LOCALPLAYER, component.moveState, positionComponent, component.physics, component.characterController, GameWorld.PlayerInputMode(), remoteNodeID)
        else:
            component.moveModeManager = GameWorld.MoveModeManager(entity.entityID, component.sceneID, const.movement.AVATARTYPE_CLIENT_NPC, component.moveState, positionComponent, component.physics, component.characterController, GameWorld.ClientRemoteMode(), -1)
        component.InitializeCharacterControllerRefs(positionComponent)
        sm.GetService('navigation')

    def RegisterComponent(self, entity, component):
        movsvc.MovementService.RegisterComponent(self, entity, component)

    def UnRegisterComponent(self, entity, component):
        movsvc.MovementService.UnRegisterComponent(self, entity, component)
