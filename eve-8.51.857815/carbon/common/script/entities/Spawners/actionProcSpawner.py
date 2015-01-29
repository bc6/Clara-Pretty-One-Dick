#Embedded file name: carbon/common/script/entities/Spawners\actionProcSpawner.py
import GameWorld
from carbon.common.script.entities.Spawners.runtimeSpawner import RuntimeSpawner

class ActionProcSpawner(RuntimeSpawner):
    """
    This spawner handles runtime-entities that are spawned via action-procs.
    The only static information is the recipe, but everything else is dynamic.
    """
    __guid__ = 'cef.ActionProcSpawner'

    def __init__(self, entitySceneID, dynamicSpawnID, recipeTypeID, posProp, rotProp):
        """
        Action procs are only slightly different than RuntimeSpawner's
        Specifically, the pos/rot needs to be unpacked first.
        """
        position = GameWorld.GetPropertyForCurrentPythonProc(posProp)
        rotation = GameWorld.GetPropertyForCurrentPythonProc(rotProp)
        RuntimeSpawner.__init__(self, entitySceneID, dynamicSpawnID, recipeTypeID, position, rotation)
