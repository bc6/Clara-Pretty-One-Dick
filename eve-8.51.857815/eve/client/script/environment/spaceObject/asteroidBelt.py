#Embedded file name: eve/client/script/environment/spaceObject\asteroidBelt.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import trinity

class AsteroidBelt(SpaceObject):

    def LoadModel(self):
        model = trinity.EveRootTransform()
        SpaceObject.LoadModel(self, fileName='', loadedModel=model)

    def Assemble(self):
        self.SetupAmbientAudio(u'worldobject_asteroidbelt_wind_play')
        SpaceObject.Assemble(self)
