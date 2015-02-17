#Embedded file name: carbon/client/script/entities/AI\perceptionClient.py
"""
Contains class for the client AI perception service.
"""
import GameWorld
from carbon.common.script.sys.service import Service
from carbon.common.script.entities.AI.perceptionCommon import perceptionCommon

class PerceptionClient(perceptionCommon):
    """
    Client perception service
    """
    __guid__ = 'svc.perceptionClient'
    __notifyevents__ = []
    __dependencies__ = ['gameWorldClient']

    def __init__(self):
        """
        Constructs the class
        """
        perceptionCommon.__init__(self)

    def Run(self, *etc):
        """
        Runs the service
        """
        self.gameWorldService = self.gameWorldClient
        Service.Run(self, etc)

    def MakePerceptionManager(self):
        """
        Creates a client perception manager object.
        """
        return GameWorld.PerceptionManagerClient()

    def IsClientServerFlagValid(self, clientServerFlag):
        """
        Returns whether this flag is valid for this boot role
        """
        return clientServerFlag & const.aiming.AIMING_CLIENTSERVER_FLAG_CLIENT
