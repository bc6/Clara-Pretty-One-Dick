#Embedded file name: eve/client/script/environment/spaceObject\harvestableGasCloud.py
from eve.client.script.environment.spaceObject.cloud import Cloud
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import geo2
import math
import random

class HarvestableGasCloud(Cloud):

    def LoadModel(self, fileName = None, loadedModel = None):
        SpaceObject.LoadModel(self, fileName, loadedModel)

    def Assemble(self):
        Cloud.Assemble(self)
        self.model.rotation = geo2.QuaternionRotationSetYawPitchRoll(random.random() * math.pi * 2.0, random.random() * math.pi, random.random() * math.pi)
