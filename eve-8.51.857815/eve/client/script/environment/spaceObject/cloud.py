#Embedded file name: eve/client/script/environment/spaceObject\cloud.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import evegraphics.settings as gfxsettings
ENVIRONMENTS = (19713, 19746, 19747, 19748, 19749, 19750, 19751, 19752, 19753, 19754, 19755, 19756)

class Cloud(SpaceObject):

    def LoadModel(self, fileName = None, loadedModel = None):
        if self.typeID in ENVIRONMENTS:
            self.LogInfo('Not loading dungeon environment (%s), since rework is pending.' % self.typeID)
            return
        if not gfxsettings.Get(gfxsettings.UI_EFFECTS_ENABLED):
            return
        SpaceObject.LoadModel(self, fileName, loadedModel)

    def Assemble(self):
        self.SetStaticRotation()
        self.SetRadius(self.radius)

    def SetRadius(self, r):
        s = 2.0
        if self.model is not None and hasattr(self.model, 'scaling'):
            self.model.scaling = (s * r, s * r, s * r)
