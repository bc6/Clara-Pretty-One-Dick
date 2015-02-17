#Embedded file name: carbon/client/script/entities/spawnerClients\simpleStaticSpawnClient.py
"""
Simple-static-spawns are auto-loaded when a worldspace comes online.

TODO: Add respawning of entities managed here, when they are destroyed.
"""
import cef
import service

class SimpleStaticSpawnClient(service.Service):
    __guid__ = 'svc.simpleStaticSpawnClient'
    __notifyevents__ = []
    __dependencies__ = ['entityRecipeSvc', 'entitySpawnClient']

    def _GetRelevantSpawnRows(self, worldSpaceTypeID):
        if worldSpaceTypeID not in cfg.entitySpawnsByWorldSpaceID:
            return []
        clientFilter = lambda spawnRow: spawnRow.spawnType == const.cef.SPAWN_TYPE_ACTIVE_ON_LOAD

        def FilterForRole(spawn):
            recipe = self.entityRecipeSvc.GetRecipe(spawn.recipeID)
            if cef.ShouldSpawnOn(recipe.keys(), boot.role):
                return True
            return False

        allRows = cfg.entitySpawnsByWorldSpaceID[worldSpaceTypeID]
        filteredRows = filter(clientFilter, allRows)
        filteredRows = filter(FilterForRole, allRows)
        return filteredRows

    def OnEntitySceneLoaded(self, sceneID):
        """
        Load all static entities in this worldspace, when the scene loads.
        """
        worldSpaceTypeID = self.entitySpawnClient.GetWorldSpaceTypeID(sceneID)
        worldSpaceSpawns = self._GetRelevantSpawnRows(worldSpaceTypeID)
        for spawnRow in worldSpaceSpawns:
            spawner = cef.SimpleStaticSpawner(sceneID, spawnRow)
            self.entitySpawnClient.LoadEntityFromSpawner(spawner)
