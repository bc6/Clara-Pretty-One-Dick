#Embedded file name: carbonui/camera\transitionCamera.py
"""
    A specific camera for transitions between two other cameras
"""
import util
import cameras

class TransitionCamera(cameras.BasicCamera):
    __guid__ = 'cameras.TransitionCamera'

    def __init__(self):
        cameras.BasicCamera.__init__(self)
        self.fromCamera = None
        self.toCamera = None
        self.pushing = False

    def SetTransitionTargets(self, fromCamera, toCamera, pushing = True):
        """
            Sets the from and to positions and rotations. Pushing tells the camera if this
            transition is between adding or removing a camera from the camera stack
        """
        self.fromCamera = fromCamera
        self.toCamera = toCamera
        self.pushing = pushing
        self.SetPosition(self.fromCamera.cameraPosition)
        self.SetYaw(self.fromCamera.yaw)
        self.SetPitch(self.fromCamera.pitch)
        self.fromPoint = self.fromCamera.cameraPosition
        self.fromRotation = util.KeyVal(yaw=self.fromCamera.yaw, pitch=self.fromCamera.pitch)
        self.toPoint = self.toCamera.cameraPosition
        self.toRotation = util.KeyVal(yaw=self.toCamera.yaw, pitch=self.toCamera.pitch)
        self.fromFov = self.fromCamera.fieldOfView
        self.toFov = self.toCamera.fieldOfView

    def PerformPick(self, x, y, ignoreEntID = -1):
        """
            Picking is currently disabled during transitions
        """
        pass

    def DoneTransitioning(self):
        """
            Called when a transition behavior has decided its transition process has come to an end.
            Depending on whether this is a push or a pop transition, we either push the camera we are
            transitioning to, or pop ourselves and the camera above us on the stack.
        """
        camClient = sm.GetService('cameraClient')
        camClient.transition = False
        if self.pushing:
            camClient.PopAndPush(self.toCamera)
        else:
            camClient.PopActiveCamera()
            camClient.PopActiveCamera()

    def UpdateToCamera(self):
        self.toCamera.Update()
        self.toPoint = self.toCamera.cameraPosition
        self.toRotation = util.KeyVal(yaw=self.toCamera.yaw, pitch=self.toCamera.pitch)

    def Update(self):
        self.UpdateToCamera()
        cameras.BasicCamera.Update(self)
