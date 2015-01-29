#Embedded file name: carbonui/camera\cameraClient.py
"""
    Assigns the active camera on a stack and provides storage for cameras shared between different
    systems that may need them. 
"""
import util
import uthread
import trinity
from carbon.common.script.sys.service import CoreService

class CameraClient(CoreService):
    __guid__ = 'svc.cameraClient'
    __notifyevents__ = ['OnSetDevice']
    THREAD_CONTEXT = __guid__.split('.')[-1]

    def Run(self, *etc):
        CoreService.Run(self, *etc)
        self.trinityViewMatrix = trinity.TriView()
        self.trinityProjectionMatrix = trinity.TriProjection()
        self.cameraStartupInfo = None
        self.audioListener = None
        self.enabled = False
        self.transition = False
        import cameras
        defaultCamera = cameras.PolarCamera()
        defaultCamera.SetTrinityMatrixObjects(self.trinityViewMatrix, self.trinityProjectionMatrix)
        self.sharedCameras = {'Basic Camera': defaultCamera}
        self.cameraStack = [defaultCamera]

    def RegisterCameraStartupInfo(self, yaw, pitch, zoom):
        """
        Saves a specific yaw, pitch and zoom so that it can be used in derived 
        services for initializing the camera correctly (e.g. on avatar creation)
        """
        self.cameraStartupInfo = util.KeyVal(yaw=yaw, pitch=pitch, zoom=zoom)
        cam = self.GetActiveCamera()
        cam.yaw = yaw
        cam.pitch = pitch

    def AddSharedCamera(self, cameraName, cameraObj, setActive = False, transitionBehaviors = []):
        """
        Add a camera to a pool of shared cameras to be used by several systems.
        """
        cameraObj.SetTrinityMatrixObjects(self.trinityViewMatrix, self.trinityProjectionMatrix)
        self.sharedCameras[cameraName] = cameraObj
        if setActive:
            self.PushActiveCamera(cameraObj, transitionBehaviors)

    def RemoveSharedCamera(self, cameraName):
        """
        Remove a previously added shared camera.
        """
        if cameraName in self.sharedCameras:
            del self.sharedCameras[cameraName]
        else:
            self.LogWarn('Attempting to remove shared camera ' + cameraName + " but it doesn't exist in the available cameras!")

    def GetSharedCamera(self, cameraName):
        """
        Return a shared camera.
        """
        if cameraName in self.sharedCameras:
            return self.sharedCameras[cameraName]

    def ResetCameras(self):
        """
        Completely resets all cameras and behaviors.
        """
        for camera in self.cameraStack:
            camera.Reset()

    def ResetLayerInfo(self):
        """
        Resets all camera layer information. Some cameras won't care but they all have ResetLayer.
        """
        for camera in self.cameraStack:
            camera.ResetLayer()

    def Disable(self):
        """
        Disables processing in the Update loop (disables all camera processing)
        """
        self.enabled = False

    def Enable(self):
        """
        Resumes processing in the Update loop
        """
        self.enabled = True

    def SetAudioListener(self, listener):
        """
        Sets the audio listener object and also adds it to the current active camera
        """
        self.audioListener = listener
        self.GetActiveCamera().audio2Listener = listener

    def PushActiveCamera(self, cameraObj, transitionBehaviors = []):
        """
        Put a camera on the top of the stack, making it the active camera.
        """
        cameraObj.SetTrinityMatrixObjects(self.trinityViewMatrix, self.trinityProjectionMatrix)
        if transitionBehaviors:
            uthread.new(self._PushAndTransition, cameraObj, transitionBehaviors).context = 'CameraClient::_PushAndTransitionNewCamera'
        else:
            if self.audioListener is not None:
                cameraObj.audio2Listener = self.audioListener
            self._PushNewCamera(cameraObj)

    def _PushAndTransition(self, cameraObj, transitionBehaviors):
        """
        Uthread this out to minimize the frametime gap between the processing that takes place here and the transition
        camera's first frame loop
        """
        if self.audioListener is not None:
            cameraObj.audio2Listener = self.audioListener
        import cameras
        transitionCamera = cameras.TransitionCamera()
        transitionCamera.fieldOfView = cameraObj.fieldOfView
        transitionCamera.SetTrinityMatrixObjects(self.trinityViewMatrix, self.trinityProjectionMatrix)
        for transitionbehavior in transitionBehaviors:
            transitionCamera.AddBehavior(transitionbehavior)

        transitionCamera.SetTransitionTargets(self.GetActiveCamera(), cameraObj, pushing=True)
        self.transition = True
        self._PushNewCamera(transitionCamera)

    def _PushNewCamera(self, camera):
        if len(self.cameraStack):
            activeCamera = self.GetActiveCamera()
            activeCamera.Deactivate()
        self.cameraStack.append(camera)
        self._CreateCameraRenderJob()
        camera.Update()

    def PopAndPush(self, newCamera):
        """
        First pushes the new camera and then removes the currently active camera. This makes sure
        that camera number 2 on the stack never gets used to render the scene (which can happen
            between popping and pushing)
        """
        if len(self.cameraStack) > 1:
            self.cameraStack.append(newCamera)
            self.cameraStack.remove(self.cameraStack[-2])
        else:
            self.cameraStack.append(newCamera)
        self.GetActiveCamera().UpdateProjectionMatrix()
        self._CreateCameraRenderJob()

    def PopActiveCamera(self, transitionBehaviors = []):
        """
        Remove the active camera from the stack, restoring the previous camera as the active one.
        """
        if len(self.cameraStack) > 1:
            if transitionBehaviors:
                uthread.new(self._PopAndTransition, transitionBehaviors).context = 'CameraClient._PopAndTransition'
            else:
                self.GetActiveCamera().Deactivate()
                self.cameraStack.pop()
                self.GetActiveCamera().UpdateProjectionMatrix()
                self._CreateCameraRenderJob()
        else:
            self.LogWarn('Attempting to pop the default camera!  Cannot clear the camera stack!')

    def _PopAndTransition(self, transitionBehaviors):
        """
        Uthread this out to minimize the frametime gap between the processing that takes place here and the transition
        camera's first frame loop
        """
        import cameras
        transitionCamera = cameras.TransitionCamera()
        transitionCamera.fieldOfView = self.GetActiveCamera().fieldOfView
        transitionCamera.SetTrinityMatrixObjects(self.trinityViewMatrix, self.trinityProjectionMatrix)
        for transitionbehavior in transitionBehaviors:
            transitionCamera.AddBehavior(transitionbehavior)

        transitionCamera.SetTransitionTargets(self.GetActiveCamera(), self.cameraStack[-2], pushing=False)
        self.transition = True
        self._PushNewCamera(transitionCamera)

    def SetDefaultCamera(self, camera, clearStack = True):
        """
        Replace the default camera in the camera stack.
        Optional parameter allows for clearing the stack so only the default camera is the active one.
        """
        if clearStack:
            self.cameraStack = [camera]
        else:
            self.cameraStack[0] = camera
        self.GetActiveCamera().UpdateProjectionMatrix()
        self._CreateCameraRenderJob()

    def GetDefaultCamera(self):
        """
        Return the camera at the base of the stack.
        """
        return self.cameraStack[0]

    def GetActiveCamera(self):
        """
        Get the camera from the top of the stack.
        """
        return self.cameraStack[-1]

    def GetCameraStack(self):
        return self.cameraStack

    def OnSetDevice(self):
        """
        When the resolution changes, we need to update our projection matrix.
        """
        self.GetActiveCamera().UpdateProjectionMatrix()

    def _CreateCameraRenderJob(self):
        """
        Implemented in derived classes. Creates a render job for the camera at 
        the beginning of start up. Only needs to be called once!
        """
        pass
