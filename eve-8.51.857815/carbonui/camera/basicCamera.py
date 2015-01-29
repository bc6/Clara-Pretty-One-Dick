#Embedded file name: carbonui/camera\basicCamera.py
"""
    This class is the most basic implementation of a camera class. It consist solely of a position
    and a directional vector in which the camera looks. It also supports adjusting the yaw and the pitch
    which changes the directional vector
"""
import blue
import math
import geo2
import util
import trinity

class BasicCamera(object):
    __guid__ = 'cameras.BasicCamera'

    def __init__(self):
        self.direction = (math.pi / 4.0, math.pi / 4.0, math.pi / 4.0)
        self.cameraPosition = (0, 0, 0)
        self.viewMatrix = trinity.TriView()
        self.baseViewMatrix = trinity.TriView()
        self.projectionMatrix = trinity.TriProjection()
        self.fieldOfView = 1.0
        self.frontClip = 0.1
        self.backClip = 1000.0
        self.yaw, self.pitch = self.GetYawPitch()
        self.mouseLeftButtonDown = False
        self.mouseRightButtonDown = False
        self.desiredDeltaX = 0
        self.desiredDeltaY = 0
        self.controlEnabled = True
        self.cameraBehaviors = []
        self.lastUpdateTime = blue.os.GetWallclockTime()
        self.audio2Listener = None

    def Reset(self):
        """
        Implemented in derived classes
        """
        pass

    def ResetLayer(self):
        """
        Implemented in derived classes
        """
        pass

    def SetTrinityMatrixObjects(self, viewMatrix, projectionMatrix):
        """
            Normally you don't want to create new view and projection matrixes and have to update
            the render steps whenever you change a camera because that causes noticable black outs.
            Intead the render job and views are created once and then shared between cameras. The
            creation of the render job is handled in cameraClient._CreateCameraRenderJob
        """
        self.viewMatrix = viewMatrix
        self.projectionMatrix = projectionMatrix

    def SetControlEnabled(self, boolEnable):
        self.controlEnabled = boolEnable

    def IsControlEnabled(self):
        return self.controlEnabled

    def OnMouseDown(self, posX, posY, button):
        if button is const.INPUT_TYPE_LEFTCLICK:
            self.mouseLeftButtonDown = True
        elif button is const.INPUT_TYPE_RIGHTCLICK:
            self.mouseRightButtonDown = True

    def OnMouseUp(self, posX, posY, button):
        if button is const.INPUT_TYPE_LEFTCLICK:
            self.mouseLeftButtonDown = False
        elif button is const.INPUT_TYPE_RIGHTCLICK:
            self.mouseRightButtonDown = False

    def OnMouseMove(self, deltaX, deltaY):
        if self.mouseLeftButtonDown or self.mouseRightButtonDown:
            self.AdjustYaw(deltaX)
            self.AdjustPitch(deltaY)

    def SetDesiredMouseDelta(self, desiredDeltaX, desiredDeltaY):
        self.desiredDeltaX = desiredDeltaX
        self.desiredDeltaY = desiredDeltaY

    def AdjustYaw(self, delta):
        if not self.controlEnabled:
            return
        self.yaw += delta
        self.CalcCameraDirection()

    def AdjustPitch(self, delta):
        if not self.controlEnabled:
            return
        if self.pitch + delta < math.pi and self.pitch + delta > 0.01:
            self.pitch += delta
        else:
            if self.pitch + delta < 0.01:
                self.pitch = 0.01
            if self.pitch + delta > math.pi:
                self.pitch = math.pi
        self.CalcCameraDirection()

    def SetPitch(self, pitch):
        self.pitch = pitch
        self.CalcCameraDirection()

    def SetYaw(self, yaw):
        self.yaw = yaw
        self.CalcCameraDirection()

    def Deactivate(self):
        """
        Implementation happens in derived classes
        """
        pass

    def CalcCameraDirection(self):
        if trinity.IsRightHanded():
            self.direction = (math.sin(self.pitch) * math.cos(self.yaw), -math.cos(self.pitch), math.sin(self.pitch) * math.sin(self.yaw))
        else:
            self.direction = (-math.sin(self.pitch) * math.cos(self.yaw), math.cos(self.pitch), -math.sin(self.pitch) * math.sin(self.yaw))

    def GetPosition(self):
        return self.cameraPosition

    def GetYawPitch(self):
        rotMatrix = geo2.MatrixTranspose(self.viewMatrix.transform)
        quat = geo2.QuaternionRotationMatrix(rotMatrix)
        yaw, pitch, roll = geo2.QuaternionRotationGetYawPitchRoll(quat)
        yaw = math.pi / 2 - yaw
        pitch = math.pi / 2 - pitch
        return (yaw, pitch)

    def SetPosition(self, position):
        self.cameraPosition = position

    def UpdateProjectionMatrix(self):
        aspectRatio = float(trinity.device.viewport.width) / float(trinity.device.viewport.height)
        self.projectionMatrix.PerspectiveFov(self.fieldOfView, aspectRatio, self.frontClip, self.backClip)

    def SetFieldOfView(self, fov):
        self.fieldOfView = fov
        self.UpdateProjectionMatrix()

    def CreateViewMatrix(self):
        upVector = (0, 1, 0)
        xaxis = geo2.Vec3Normalize(geo2.Vec3Cross(upVector, self.direction))
        yaxis = geo2.Vec3Cross(self.direction, xaxis)
        return ((xaxis[0],
          yaxis[0],
          self.direction[0],
          0.0),
         (xaxis[1],
          yaxis[1],
          self.direction[1],
          0.0),
         (xaxis[2],
          yaxis[2],
          self.direction[2],
          0.0),
         (-geo2.Vec3Dot(xaxis, self.cameraPosition),
          -geo2.Vec3Dot(yaxis, self.cameraPosition),
          -geo2.Vec3Dot(self.direction, self.cameraPosition),
          1.0))

    def Update(self):
        now = blue.os.GetWallclockTime()
        frameTime = float(now - self.lastUpdateTime) / const.SEC
        for priority, behavior in self.cameraBehaviors:
            behavior.ProcessCameraUpdate(self, now, frameTime)

        self.lastUpdateTime = now
        self.viewMatrix.transform = self.CreateViewMatrix()
        self.baseViewMatrix.transform = self.CreateViewMatrix()

    def AddBehavior(self, behavior, priority = 100):
        """
            Add a camera behavior to this camera.
            These are processed according to their given priority.
        """
        self.cameraBehaviors.append((priority, behavior))
        self.cameraBehaviors.sort()
        behavior.OnBehaviorAdded(self)

    def RemoveBehavior(self, behavior):
        """
            Remove a camera behavior.
        """
        toRemove = None
        for priority, myBehavior in self.cameraBehaviors:
            if myBehavior == behavior:
                toRemove = (priority, myBehavior)
                break

        if toRemove is not None:
            self.cameraBehaviors.remove(toRemove)

    def GetBehavior(self, behaviorType):
        """
            Currently, we only support one instance of each behavior type per camera.
            Return the behavior if the type passed in matches.
        """
        for priority, behavior in self.cameraBehaviors:
            if type(behavior) is behaviorType:
                return behavior

    def PerformPick(self, x, y, ignoreEntID = -1):
        """
            Implemented in inherited classes
        """
        raise NotImplementedError('PerformPick must be implemented on derived camera classes')

    def GetRay(self, x, y):
        app = trinity.app
        aspect = float(app.width) / app.height
        fovTan = math.tan(self.fieldOfView * 0.5)
        dx = fovTan * (2.0 * x / app.width - 1.0) * aspect
        dy = fovTan * (1.0 - 2.0 * y / app.height)
        if trinity.IsRightHanded():
            startPoint = trinity.TriVector(self.frontClip * dx, self.frontClip * dy, -self.frontClip)
            endPoint = trinity.TriVector(self.backClip * dx, self.backClip * dy, -self.backClip)
        else:
            startPoint = trinity.TriVector(self.frontClip * dx, self.frontClip * dy, self.frontClip)
            endPoint = trinity.TriVector(self.backClip * dx, self.backClip * dy, self.backClip)
        invViewMatrix = util.ConvertTupleToTriMatrix(self.viewMatrix.transform)
        invViewMatrix.Inverse()
        startPoint.TransformCoord(invViewMatrix)
        endPoint.TransformCoord(invViewMatrix)
        startPoint = (startPoint.x, startPoint.y, startPoint.z)
        endPoint = (endPoint.x, endPoint.y, endPoint.z)
        return (startPoint, endPoint)

    def ProjectPoint(self, point):
        """
            Projects a 3D point to 2D space
        """
        viewport = (trinity.device.viewport.x,
         trinity.device.viewport.y,
         trinity.device.viewport.width,
         trinity.device.viewport.height,
         trinity.device.viewport.minZ,
         trinity.device.viewport.maxZ)
        return geo2.Vec3Project(point, viewport, self.projectionMatrix.transform, self.viewMatrix.transform, geo2.MatrixIdentity())

    def IsPointInViewport(self, point):
        """
            Takes a point in 3D space and determines whether this point is visible.
            It does not take in to account if the object is occluded.
        """
        point2D = self.ProjectPoint(point)
        if point2D[0] < trinity.device.viewport.x or point2D[0] > trinity.device.viewport.x + trinity.device.viewport.width or point2D[1] < trinity.device.viewport.y or point2D[1] > trinity.device.viewport.y + trinity.device.viewport.height or point2D[2] < trinity.device.viewport.minZ or point2D[2] > trinity.device.viewport.maxZ:
            return False
        return True

    def ResetBehaviors(self):
        """
            Calls Reset on all behaviors on this camera
        """
        for prio, behavior in self.cameraBehaviors:
            behavior.Reset()


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('cameras', globals())
