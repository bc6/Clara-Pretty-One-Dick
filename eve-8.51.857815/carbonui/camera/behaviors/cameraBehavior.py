#Embedded file name: carbonui/camera/behaviors\cameraBehavior.py
"""
Simple base class for camera behaviors.
Contains base functionality and Corified versions of common functions needed.
"""

class CameraBehavior(object):
    __guid__ = 'cameras.CameraBehavior'

    def __init__(self):
        self.gameWorldClient = sm.GetService('gameWorldClient')
        self.gameWorld = None
        self._LoadGameWorld()

    def _LoadGameWorld(self):
        if self.gameWorldClient.HasGameWorld(session.worldspaceid):
            self.gameWorld = self.gameWorldClient.GetGameWorld(session.worldspaceid)

    def ProcessCameraUpdate(self, camera, now, frameTime):
        """
        Implemented in derived classes, what do I do when the camera tells me to update?
        """
        pass

    def _GetEntity(self, entID):
        return sm.GetService('entityClient').FindEntityByID(entID)

    def _GetEntityModel(self, entID):
        entity = sm.GetService('entityClient').FindEntityByID(entID)
        if entity and entity.HasComponent('paperdoll'):
            return entity.GetComponent('paperdoll').doll.avatar

    def Reset(self):
        """
        Implemented in derived classes.
        Used for when changing the scene and values need to be reset
        """
        pass

    def OnBehaviorAdded(self, camera):
        """
        Implemented in derived classes.
        Used for custom behavior for when this behavior is added to a camera
        """
        pass
