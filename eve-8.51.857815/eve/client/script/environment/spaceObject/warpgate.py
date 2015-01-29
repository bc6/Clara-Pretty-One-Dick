#Embedded file name: eve/client/script/environment/spaceObject\warpgate.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject

class WarpGate(SpaceObject):

    def Assemble(self):
        self.SetStaticDirection()
        self.SetupAmbientAudio()
