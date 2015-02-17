#Embedded file name: eve/client/script/ui/camera\eveCameraClient.py
import sys
import log
import blue
import audio2
import trinity
import cameras
import service
import uthread
import const
import evegraphics.settings as gfxsettings
from carbonui.camera.cameraClient import CameraClient
import utillib as util
MAX_MOUSE_DELTA = 500
MOUSE_LOOK_SPEED = 0.005
MOUSE_MOVE_DELTA_FALLOFF = 0.5
MAX_MOUSE_SCREEN_FRACTION_JUMP = 1.85
MOUSE_MOVE_DELTA_HISTORY_BUFFER_LENGTH = 10

class EveCameraClient(CameraClient):
    __guid__ = 'svc.eveCameraClient'
    __replaceservice__ = 'cameraClient'
    __exportedcalls__ = {'GetCameraSettings': [],
     'CheckCameraOffsets': [],
     'CheckMouseLookSpeed': []}
    __dependencies__ = CameraClient.__dependencies__[:]
    __dependencies__.extend(['mouseInput', 'sceneManager'])
    __startupdependencies__ = CameraClient.__startupdependencies__[:]
    __startupdependencies__.extend(['settings'])

    def Run(self, *etc):
        CameraClient.Run(self, *etc)
        self.cameraStack = [cameras.AvatarCamera()]
        self.sharedCameras = {'Default Startup Camera': self.cameraStack[0]}
        self.entityLoop = None
        self.invertYAxis = False
        self.mouseSmooth = True
        self.mouseLookSpeed = cameras.MOUSE_LOOK_SPEED
        self.desiredDeltaX = 0
        self.desiredDeltaY = 0
        self.lastDeltaX = 0
        self.lastDeltaY = 0
        self.currAverageDeltaX = 0
        self.currAverageDeltaY = 0
        self.skipMouseFrameCount = 0
        self.mouseDeltaHistory = []
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEDOWN, self.OnMouseDown)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEUP, self.OnMouseUp)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEMOVE, self.OnMouseMove)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEWHEEL, self.OnMouseWheel)

    def Stop(self, stream):
        self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEDOWN, self.OnMouseDown)
        self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEUP, self.OnMouseUp)
        self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEMOVE, self.OnMouseMove)
        self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEWHEEL, self.OnMouseWheel)

    def OnMouseDown(self, button, posX, posY, entityID):
        if self.enabled and not self.transition:
            activeCamera = self.GetActiveCamera()
            activeCamera.OnMouseDown(posX, posY, button)

    def OnMouseUp(self, button, posX, posY, entityID):
        if self.enabled and not self.transition:
            activeCamera = self.GetActiveCamera()
            activeCamera.OnMouseUp(posX, posY, button)

    def OnMouseMove(self, deltaX, deltaY, entityID):
        if not self.enabled or self.transition:
            return
        if self.skipMouseFrameCount > 0 and self.skipMouseFrameCount < 3:
            self.desiredDeltaX = self.lastDeltaX * self.mouseLookSpeed
            self.desiredDeltaY = self.lastDeltaY * self.mouseLookSpeed
            self.skipMouseFrameCount += 1
            if self.skipMouseFrameCount > 2:
                self.skipMouseFrameCount = 0
            return
        overflow = False
        if abs(deltaX) > trinity.app.width / cameras.MAX_MOUSE_SCREEN_FRACTION_JUMP:
            if deltaX < 0 and self.lastDeltaX > 0 or deltaX > 0 and self.lastDeltaX < 0:
                self.desiredDeltaX = self.lastDeltaX * self.mouseLookSpeed
                overflow = True
        if abs(deltaY) > trinity.app.height / cameras.MAX_MOUSE_SCREEN_FRACTION_JUMP:
            if deltaY < 0 and self.lastDeltaY > 0 or deltaY > 0 and self.lastDeltaY < 0:
                self.desiredDeltaY = self.lastDeltaY * self.mouseLookSpeed
                overflow = True
        if overflow:
            return
        if self.invertYAxis:
            deltaY = -deltaY
        self.lastDeltaX = deltaX
        self.lastDeltaY = deltaY
        self.desiredDeltaX = deltaX * self.mouseLookSpeed
        self.desiredDeltaY = deltaY * self.mouseLookSpeed
        activeCamera = self.GetActiveCamera()
        activeCamera.OnMouseMove(deltaX, deltaY)

    def OnMouseWheel(self, delta):
        if self.enabled:
            activeCamera = self.GetActiveCamera()
            if hasattr(activeCamera, 'AdjustZoom'):
                activeCamera.AdjustZoom(delta * cameras.MOUSE_LOOK_SPEED)

    def GetCameraSettings(self):
        offset = gfxsettings.Get(gfxsettings.UI_INCARNA_CAMERA_OFFSET)
        invertY = gfxsettings.Get(gfxsettings.UI_INCARNA_CAMERA_INVERT_Y)
        mouseLookSpeed = gfxsettings.Get(gfxsettings.UI_INCARNA_CAMERA_MOUSE_LOOK_SPEED)
        mouseSmooth = True
        mySettings = util.KeyVal(charOffsetSetting=offset, invertY=invertY, mouseLookSpeed=mouseLookSpeed, mouseSmooth=mouseSmooth)
        return mySettings

    def ApplyUserSettings(self):
        self.CheckCameraOffsets()
        self.CheckInvertY()
        self.CheckMouseLookSpeed()

    def CheckCameraOffsets(self):
        offset = gfxsettings.Get(gfxsettings.UI_INCARNA_CAMERA_OFFSET)
        offsetBehaviors = []
        for cam in self.cameraStack:
            offsetBehavior = cam.GetBehavior(cameras.CharacterOffsetBehavior)
            if offsetBehavior:
                offsetBehaviors.append(offsetBehavior)

        for offsetBehavior in offsetBehaviors:
            offsetBehavior.AdjustOffset(offset)

    def CheckInvertY(self):
        self.invertYAxis = gfxsettings.Get(gfxsettings.UI_INCARNA_CAMERA_INVERT_Y)

    def CheckMouseLookSpeed(self):
        self.mouseLookSpeed = gfxsettings.Get(gfxsettings.UI_INCARNA_CAMERA_MOUSE_LOOK_SPEED)

    def Disable(self):
        CameraClient.Disable(self)
        self.StopCamera()
        uicore.uilib.centerMouse = False
        self.enabled = False

    def Enable(self):
        CameraClient.Enable(self)
        self.ResetLayerInfo()
        self.StartCamera()
        self.enabled = True

    def ClearCameraStack(self):
        self.cameraStack = [cameras.AvatarCamera()]
        self.sharedCameras = {'Default Startup Camera': self.cameraStack[0]}

    def StartCamera(self):
        self.entityLoop = uthread.new(self.CameraLoop)
        self.entityLoop.context = 'CameraClient::CameraLoop'

    def StopCamera(self):
        if self.entityLoop is not None and self.entityLoop.alive:
            self.entityLoop.kill()

    def _PushNewCamera(self, camera):
        CameraClient._PushNewCamera(self, camera)
        uicore.uilib.centerMouse = False

    def EnterWorldspace(self):
        """
        Happens whenever we go into a worldspace, originates in the viewState transition for entering a worldspace. 
        Resets all the camera stuff so that we start with a clean, unburdened slate.
        """
        if self.enabled:
            self.Disable()
        self.ResetCameras()
        self.SetAudioListener(audio2.GetListener(0))
        defaultCamera = cameras.AvatarCamera()
        if self.cameraStartupInfo is not None:
            defaultCamera.yaw = self.cameraStartupInfo.yaw
            defaultCamera.pitch = self.cameraStartupInfo.pitch
            defaultCamera.zoom = defaultCamera.collisionZoom = defaultCamera.desiredZoom = self.cameraStartupInfo.zoom
            defaultCamera.userSelectedZoom = self.cameraStartupInfo.zoom
        if self.audioListener is not None:
            defaultCamera.audio2Listener = self.audioListener
        self.cameraStack = [defaultCamera]
        self._CreateCameraRenderJob()
        defaultCamera.Update()
        self.sharedCameras = {'Default Incarna Avatar Camera': defaultCamera}
        defaultCamera.AddBehavior(cameras.CharacterOffsetBehavior(session.charid), priority=1)
        defaultCamera.AddBehavior(cameras.ZoomFovBehavior(), priority=2)
        self.ApplyUserSettings()
        self.Enable()

    def ExitWorldspace(self):
        """
        Happens when we leave a worldspace, originates in UnloadView on the CQ view.
        """
        if self.enabled:
            self.Disable()
        self.GetActiveCamera().Reset()
        self.audioListener = None
        for camera in self.cameraStack:
            for priority, behaviour in camera.cameraBehaviors:
                if hasattr(behaviour, 'gameWorld'):
                    behaviour.gameWorld = None

        self.ClearCameraStack()

    def _CreateCameraRenderJob(self):
        self.sceneManager.RefreshJob(self.GetActiveCamera())

    def ApplyMouseDeltaMoveSmoothing(self, activeCamera):
        """
            Collects the latest mouse move delta every frame and adds it to a buffer. Makes sure the buffer is never bigger than 
            MOUSE_MOVE_DELTA_HISTORY_BUFFER_LENGTH. It then averages the history of the mouse move deltas, applying a decreasing weight
            to each entry so that the latest updates have more weight than the older ones. It then updates the camera position using
            the weight averaged delta.
        """
        self.mouseDeltaHistory.insert(0, (self.desiredDeltaX, self.desiredDeltaY))
        if len(self.mouseDeltaHistory) > cameras.MOUSE_MOVE_DELTA_HISTORY_BUFFER_LENGTH:
            self.mouseDeltaHistory.pop()
        self.desiredDeltaX = 0
        self.desiredDeltaY = 0
        averageWeight = 1.0
        averageDecrease = cameras.MOUSE_MOVE_DELTA_FALLOFF
        deltaX = 0
        deltaY = 0
        divideBy = 0
        for entry in self.mouseDeltaHistory:
            deltaX += entry[0] * averageWeight
            deltaY += entry[1] * averageWeight
            divideBy += averageWeight
            averageWeight *= averageDecrease

        deltaX = deltaX / divideBy
        deltaY = deltaY / divideBy
        self.currAverageDeltaX = deltaX / self.mouseLookSpeed
        self.currAverageDeltaY = deltaY / self.mouseLookSpeed
        activeCamera.SetDesiredMouseDelta(deltaX, deltaY)

    def CameraLoop(self):
        while self.state != service.SERVICE_STOPPED:
            if self.enabled:
                self.TickCamera()
            blue.pyos.synchro.SleepWallclock(5)

    def TickCamera(self):
        try:
            activeCam = self.GetActiveCamera()
            if self.mouseSmooth:
                self.ApplyMouseDeltaMoveSmoothing(activeCam)
            else:
                activeCam.SetDesiredMouseDelta(self.desiredDeltaX, self.desiredDeltaY)
                self.desiredDeltaX = 0
                self.desiredDeltaY = 0
            activeCam.UpdateProjectionMatrix()
            activeCam.Update()
        except Exception:
            log.LogException('Error in CameraLoop')
            sys.exc_clear()


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('cameras', locals())
