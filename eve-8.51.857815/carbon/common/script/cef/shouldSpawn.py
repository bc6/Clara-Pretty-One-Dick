#Embedded file name: carbon/common/script/cef\shouldSpawn.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

def ShouldSpawnOn(componentIDList, spawnLoc):
    """
    Takes in a list of componentID's and based on this determines if for the
    boot role specified if these components would be spawned on this role.
    """
    shouldSpawn = False
    for componentID in componentIDList:
        componentView = BaseComponentView.GetComponentViewByID(componentID)
        spawnHere = componentView.__SHOULD_SPAWN__.get(spawnLoc, None)
        if spawnHere is False:
            return False
        if spawnHere:
            shouldSpawn = True

    return shouldSpawn


exports = {'cef.ShouldSpawnOn': ShouldSpawnOn}
