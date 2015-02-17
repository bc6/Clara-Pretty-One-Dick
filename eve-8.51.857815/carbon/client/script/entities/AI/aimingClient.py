#Embedded file name: carbon/client/script/entities/AI\aimingClient.py
"""
Contains class for the client AI aiming service.
"""
import GameWorld
from carbon.common.script.sys.service import Service
from carbon.common.script.entities.AI.aimingCommon import aimingCommon

class AimingClient(aimingCommon):
    """
    Client aiming service
    """
    __guid__ = 'svc.aimingClient'
    __notifyevents__ = []
    __dependencies__ = ['gameWorldClient', 'perceptionClient']

    def __init__(self):
        """
        Constructs the class
        """
        self.aimingServer = None
        aimingCommon.__init__(self)

    def Run(self, *etc):
        """
        Runs the service
        """
        self.aimingServer = sm.RemoteSvc('aimingServer')
        self.gameWorldService = self.gameWorldClient
        Service.Run(self, etc)

    def MakeAimingManager(self):
        """
        Creates a client aiming manager object.
        """
        return GameWorld.AimingManagerClient()

    def GetTargetEntityID(self, entity, targetType):
        """
        Returns the targeted entityID, or None
        """
        if entity.scene.sceneID not in self.sceneManagers:
            self.LogError("Trying to get targets for an entity that doesn't have a scene", entity.entityID)
            return None
        aimingManager = self.sceneManagers[entity.scene.sceneID]
        targetedEntityID = aimingManager.GetTargetEntityID(entity.entityID, targetType)
        if targetedEntityID == 0:
            return None
        return targetedEntityID

    def IsTargetClientServerValid(self, targetClientServerFlag):
        """
        Returns whether this target flag is valid
        """
        return targetClientServerFlag & const.aiming.AIMING_CLIENTSERVER_FLAG_CLIENT
