#Embedded file name: carbon/common/script/entities\entitySpawnService.py
import service

class EntitySpawnService(service.Service):
    """
    BASE service class for type-specific spawn services.
    
    The base class does NOT respond to events and DECIDE to activate spawns.
    SpawnType specific systems will have their own events or functions for this.
    """
    __guid__ = 'entities.EntitySpawnService'
    __exportedcalls__ = {}
    __notifyevents__ = []
    __dependencies__ = ['entityRecipeSvc']

    def GetNextEntityID(self):
        """
        This service is the central hub responsible for generating new entityIDs
          for the spawner services.
        """
        raise NotImplementedError('GetNextEntityID() function not implemented on: ', self.__guid__)

    def GetWorldSpaceTypeID(self, sceneID):
        """
        This service is the central hub responsible for converting
          sceneID to worldSpaceTypeID and vice-versa.
        """
        raise NotImplementedError('GetWorldSpaceTypeID() function not implemented on: ', self.__guid__)

    def GetSceneID(self, worldSpaceTypeID):
        """
        This service is the central hub responsible for converting
          worldSpaceTypeID to sceneID and vice-versa.
        """
        raise NotImplementedError('GetSceneID() function not implemented on: ', self.__guid__)

    def LoadEntityFromSpawner(self, spawner):
        """
        For the given spawner, spawn an entity and place it in the world.
        """
        if not spawner.CanSpawn():
            return
        itemID = spawner.GetEntityID()
        if itemID is False:
            itemID = self.GetNextEntityID()
        scene = self.entityService.LoadEntityScene(spawner.GetSceneID())
        spawnedEntity = self.entityService.CreateEntityFromRecipe(scene, spawner.GetRecipe(self.entityRecipeSvc), itemID)
        if spawnedEntity is not None:
            scene.CreateAndRegisterEntity(spawnedEntity)
        return spawnedEntity
