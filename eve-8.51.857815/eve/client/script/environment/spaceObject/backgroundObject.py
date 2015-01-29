#Embedded file name: eve/client/script/environment/spaceObject\backgroundObject.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import trinity

class BackgroundObject(SpaceObject):

    def LoadModel(self):
        graphicURL = self.typeData.get('graphicFile')
        obj = trinity.Load(graphicURL)
        self.backgroundObject = obj
        scene = self.spaceMgr.GetScene()
        scene.backgroundObjects.append(obj)

    def Release(self):
        if self.released:
            return
        scene = self.spaceMgr.GetScene()
        scene.backgroundObjects.fremove(self.backgroundObject)
        self.backgroundObject = None
        SpaceObject.Release(self, 'BackgroundObject')
