#Embedded file name: carbon/client/script/entities/spawnerClients\clientOnlyPlayerSpawnClient.py
"""
Players in CQ's are spawned client-side only, via pure client logic.
"""
import cef
import service
import uthread

class ClientOnlyPlayerSpawnClient(service.Service):
    __guid__ = 'svc.clientOnlyPlayerSpawnClient'
    __notifyevents__ = []
    __dependencies__ = ['entityRecipeSvc', 'entitySpawnClient']

    def Run(self, *etc):
        service.Service.Run(self, etc)
        self.charMgr = sm.RemoteSvc('charMgr')
        self.paperDollService = sm.GetService('paperdoll')

    def SpawnClientSidePlayer(self, scene, position, rotation):
        """
        Spawns a clients side version of the player entity into the given scene
        """
        self.LogInfo('Spawning client side player entity for', session.charid)
        scene.WaitOnStartupEntities()
        serverInfoCalls = []
        serverInfoCalls.append((self.paperDollService.GetMyPaperDollData, (session.charid,)))
        serverInfoCalls.append((self.charMgr.GetPublicInfo, (session.charid,)))
        paperdolldna, pubInfo = uthread.parallel(serverInfoCalls)
        spawner = cef.ClientOnlyPlayerSpawner(scene.sceneID, session.charid, position, rotation, paperdolldna, pubInfo)
        spawnedEntity = self.entitySpawnClient.LoadEntityFromSpawner(spawner)
        self.LogInfo('Client side player entity spawned for', session.charid)
