#Embedded file name: carbon/client/script/world\worldSpaceScene.py
from carbon.common.script.world.worldSpaceCommon import WorldSpace

class WorldSpaceScene(WorldSpace):
    """
    World Space containing a 3d scene that can be rendered with
    """
    __guid__ = 'world.CoreWorldSpaceScene'

    def __init__(self, worldSpaceID = None, instanceID = None):
        WorldSpace.__init__(self, worldSpaceID, instanceID)
        self.properties = {}

    def LoadProperties(self):
        pass
