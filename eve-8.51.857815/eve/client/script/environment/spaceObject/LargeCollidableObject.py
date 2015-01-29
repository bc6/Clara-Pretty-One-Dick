#Embedded file name: eve/client/script/environment/spaceObject\LargeCollidableObject.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject

class LargeCollidableObject(SpaceObject):

    def Assemble(self):
        self.SetStaticRotation()
        if getattr(self.model, 'ChainAnimationEx', None) is not None:
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        self.SetupSharedAmbientAudio()
