#Embedded file name: carbon/common/script/entities/Spawners\dynamicSimpleStaticSpawner.py
from carbon.common.script.entities.Spawners.baseSpawner import BaseSpawner

class DynamicSimpleStaticSpawner(BaseSpawner):
    """
    This spawner is meant to handle single-static-spawns, that do not spawn immediately.
    These spawns are fixed location, but only spawn when an external system commands them to spawn.
    """
    __guid__ = 'cef.DynamicSimpleStaticSpawner'

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
        Position exists on the row for simple-static-spawns.
        """
        return (self.spawnRow.spawnRotationY, self.spawnRow.spawnRotationX, self.spawnRow.spawnRotationZ)

    def GetRecipe(self, entityRecipeSvc):
        positionOverrides = self._OverrideRecipePosition({}, self.GetPosition(), self.GetRotation())
        spawnRecipe = entityRecipeSvc.GetRecipe(self.spawnRow.recipeID, positionOverrides)
        return spawnRecipe
