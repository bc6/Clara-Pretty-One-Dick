#Embedded file name: carbon/common/script/entities/Spawners\baseSpawner.py


class BaseSpawner(object):
    """
    Define the interface for spawner objects.
    """
    __guid__ = 'cef.BaseSpawner'

    def __init__(self, sceneID):
        self.sceneID = sceneID

    def GetSceneID(self):
        return self.sceneID

    def GetEntityID(self):
        """
        This is the entityID to use for the spawn.  If False is returned then the
        spawn service will select is own ID.
        """
        return False

    def GetPosition(self):
        raise NotImplementedError('GetPosition() not defined on:', self.__guid__)

    def GetRotation(self):
        raise NotImplementedError('GetRotation() not defined on:', self.__guid__)

    def GetRecipe(self, entityRecipeSvc):
        raise NotImplementedError('GetRecipe() not defined on:', self.__guid__)

    def CanSpawn(self):
        """
        Basic validation that the basic entity attributes exist.
        """
        if self.GetPosition() is None:
            return False
        if self.GetRotation() is None:
            return False
        return True

    def _OverrideRecipePosition(self, recipeOverrides, position, rotation):
        """
        Set the given position and rotation to the given recipeOverrides dictionary.
        """
        if const.cef.POSITION_COMPONENT_ID not in recipeOverrides:
            recipeOverrides[const.cef.POSITION_COMPONENT_ID] = {}
        recipeOverrides[const.cef.POSITION_COMPONENT_ID]['position'] = position
        recipeOverrides[const.cef.POSITION_COMPONENT_ID]['rotation'] = rotation
        return recipeOverrides
