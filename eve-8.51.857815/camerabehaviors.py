#Embedded file name: camerabehaviors.py
import trinity
import decometaclass
CCA_SET_FREE_LOOK = 0
CCA_SHAKE = 1
CCA_SET_IDLE = 2
CCA_SET_FOVZOOM = 3
DefaultCamera = 'JESSICA'
__cameraBehaviors__ = {}

def RegisterCamera(oCamera):
    """
    This fucntion will register a camera behaviour, the module containing the camerabehavio
    should be imported at the end of CameraBehaviors.py
    """
    sName = oCamera.GetName()
    if sName not in __cameraBehaviors__:
        __cameraBehaviors__[sName] = oCamera


import trinity.camerajessica

class PythonCamera(decometaclass.WrapBlueClass('trinity.TriCameraPython')):

    def __init__(self):
        trinity.TriCameraPython.__init__(self)
        self.instancedBehaviors = {}
        self.SetCallbackObject(self)

    def GetBehavior(self, sName):
        """
        This will return a instance of a behavior, if we have never seen this behavior
        but it is registered, then create a isntance and return it and save the instance for future use.
        This will only create behaviors that are needed, when they are needed.
        """
        pRes = None
        if sName in self.instancedBehaviors:
            pRes = self.instancedBehaviors[sName]
        if pRes == None and sName in __cameraBehaviors__:
            pRes = __cameraBehaviors__[sName]()
            self.instancedBehaviors[sName] = pRes
        return pRes

    def GetDefaultBehavior(self):
        """
        return the name of the default camera
        """
        return DefaultCamera

    def HasBehavior(self, sName):
        """
        does the camera know about this behavior?
        """
        return sName in __cameraBehaviors__

    def GetHookPosition(self):
        """
        What is the position of the camera hook
        """
        if self.parent != None:
            if hasattr(self.parent, 'vCamearHook'):
                return (self.parent.vCamearHook.x, self.parent.vCamearHook.y, self.parent.vCamearHook.z)
            if hasattr(self.parent, 'vLocation'):
                return (self.parent.vLocation.x, self.parent.vLocation.y, self.parent.vLocation.z)
            if hasattr(self.parent, 'translation'):
                return (self.parent.translation.x, self.parent.translation.y, self.parent.translation.z)
            if hasattr(self.parent, 'position'):
                return (self.parent.position.x, self.parent.position.y, self.parent.position.z)
        return (0.0, 0.0, 0.0)

    def GetHookRotation(self):
        """
        What is the rotaiton of the camera hook?
        """
        if self.parent != None:
            if hasattr(self.parent, 'qCamearRotation'):
                return (self.parent.qCamearRotation.x,
                 self.parent.qCamearRotation.y,
                 self.parent.qCamearRotation.z,
                 self.parent.qCamearRotation.w)
            if hasattr(self.parent, 'qRotation'):
                return (self.parent.qRotation.x,
                 self.parent.qRotation.y,
                 self.parent.qRotation.z,
                 self.parent.qRotation.w)
            if hasattr(self.parent, 'rotation'):
                return (self.parent.rotation.x,
                 self.parent.rotation.y,
                 self.parent.rotation.z,
                 self.parent.rotation.w)
        return (0.0, 0.0, 0.0, 0.0)
