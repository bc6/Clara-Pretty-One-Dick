#Embedded file name: eve/common/script/planet/entities\commandPin.py
"""
    This pin is the command pin for a given colony. It is a specialized
    version of a storage pin; it not only holds commodities, but also
    has a "launch timer" which permits cans to be shot into space.
    
    This is very similar to a spaceportPin, which should be inserted
    as a median class between commandPin and storagePin eventually.
"""
import eve.common.script.util.planetCommon as planetCommon
from eve.common.script.planet.entities.spaceportPin import SpaceportPin

class CommandPin(SpaceportPin):
    __guid__ = 'planet.CommandPin'
    __slots__ = []

    def OnStartup(self, id, ownerID, latitude, longitude):
        SpaceportPin.OnStartup(self, id, ownerID, latitude, longitude)

    def IsCommandCenter(self):
        return True

    def CanImportCommodities(self, commodities):
        return False

    def GetPowerOutput(self):
        level = self.eventHandler.level
        return planetCommon.GetPowerOutput(level)

    def GetCpuOutput(self):
        level = self.eventHandler.level
        return planetCommon.GetCPUOutput(level)


exports = {'planet.CommandPin': CommandPin}
