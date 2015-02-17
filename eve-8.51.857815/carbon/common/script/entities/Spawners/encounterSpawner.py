#Embedded file name: carbon/common/script/entities/Spawners\encounterSpawner.py
from carbon.common.script.entities.Spawners.runtimeSpawner import RuntimeSpawner

class EncounterSpawner(RuntimeSpawner):
    """
    This spawner is meant to handle NPC encounter spawns.
    This creates a separation between how static objects, and encounter objects are spawned.
    """
    __guid__ = 'cef.EncounterSpawner'
