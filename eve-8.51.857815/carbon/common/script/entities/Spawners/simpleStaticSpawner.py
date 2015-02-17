#Embedded file name: carbon/common/script/entities/Spawners\simpleStaticSpawner.py
from carbon.common.script.entities.Spawners.baseSpawner import BaseSpawner
import log

class SimpleStaticSpawner(BaseSpawner):
    """
    This spawner is meant to handle single-static-spawns.
    Essentially a single spawn is defined at a fixed location, and always spawns the same way.
    """
    __guid__ = 'cef.SimpleStaticSpawner'

    def __init__(self, sceneID, spawnRow):
        BaseSpawner.__init__(self, sceneID)
        self.spawnRow = spawnRow

    def GetPosition(self):
        """
        Position exists on the row for simple-static-spawns.
        """
        return (self.spawnRow.spawnPointX, self.spawnRow.spawnPointY, self.spawnRow.spawnPointZ)

    def GetRotation(self):
        """
        Rotation exists on the row for simple-static-spawns.
        """
        return (self.spawnRow.spawnRotationY, self.spawnRow.spawnRotationX, self.spawnRow.spawnRotationZ)

    def GetRecipe(self, entityRecipeSvc):
        if self.spawnRow.recipeID is None:
            log.LogError('SpawnID ', self.spawnRow.spawnID, ' has no recipe set')
            return {}
        positionOverrides = self._OverrideRecipePosition({}, self.GetPosition(), self.GetRotation())
        spawnRecipe = entityRecipeSvc.GetRecipe(self.spawnRow.recipeID, positionOverrides)
        return spawnRecipe
