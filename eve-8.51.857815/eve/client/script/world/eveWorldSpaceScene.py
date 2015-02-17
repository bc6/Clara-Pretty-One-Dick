#Embedded file name: eve/client/script/world\eveWorldSpaceScene.py
from carbon.client.script.world.worldSpaceScene import WorldSpaceScene as CoreWorldSpaceScene

class EveWorldSpaceScene(CoreWorldSpaceScene):
    """
    Class that extends WorldSpaceScene to add some Wod-specific functionality 
    """
    __guid__ = 'world.WorldSpaceScene'
