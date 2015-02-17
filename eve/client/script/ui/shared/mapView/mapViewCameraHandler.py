#Embedded file name: eve/client/script/ui/shared/mapView\mapViewCameraHandler.py
import uthread
import blue
import geo2
import math
import trinity

class MapViewCamera(object):
    fieldOfView = 1.0
    frontClip = 0.1
    backClip = 300000.0
    translationFromParent = 0.0
    minDistance = 5.0
    maxDistance = 100000.0
    _yScaleFactor = 1.0
    _pointOfInterest = (0, 0, 0)
    _pointOfInterestCurrent = _pointOfInterest
    _eyePositionCurrent = (0, 1000.0, 1000.0)
    _translationFromPOI = maxDistance * 4
    _yawSpeed = 0.0
    _pitchSpeed = 0.0
    _panSpeed = None
    callback = None
    upVector = (0, 1, 0)

    def __init__(self, *args, **kwds):
        self.viewport = None
        self.viewMatrix = trinity.TriView()
        self.projectionMatrix = trinity.TriProjection()
        self.enabled = True
        uthread.new(self.UpdateTick)

    def Close(self):
        self.enabled = False
        self.callback = None

    def SetCallback(self, callback):
        self.callback = callback

    def SetViewPort(self, viewport):
        self.viewport = viewport

    def UpdateTick(self):
        while self.enabled:
            self.Update()
            blue.synchro.Sleep(15)

    @apply
    def yScaleFactor():
        """Affects pointOfInterest"""

        def fget(self):
            return self._yScaleFactor

        def fset(self, value):
            self._yScaleFactor = value

        return property(**locals())

    @apply
    def pointOfInterest():
        """The 'LookAt' position"""

        def fget(self):
            x, y, z = self._pointOfInterest
            return (x, y * self._yScaleFactor, z)

        def fset(self, value):
            self._pointOfInterest = value

        return property(**locals())

    def Update(self):
        speedFactor = 0.2
        diff = geo2.Vec3Subtract(self.pointOfInterest, self._pointOfInterestCurrent)
        diffLength = geo2.Vec3Length(diff)
        if diffLength > 0.001:
            self._pointOfInterestCurrent = geo2.Vec3Add(self._pointOfInterestCurrent, geo2.Vec3Scale(diff, speedFactor))
        else:
            self._pointOfInterestCurrent = self.pointOfInterest
        if abs(self._yawSpeed) > 0.0001:
            yawChange = self._yawSpeed * speedFactor
            rotYaw = geo2.MatrixRotationAxis(self.upVector, yawChange)
            self._eyePositionCurrent = geo2.Vec3Transform(self._eyePositionCurrent, rotYaw)
            self._yawSpeed -= yawChange
        else:
            self._yawSpeed = 0.0
        if abs(self._pitchSpeed) > 0.0001:
            pitchChange = self._pitchSpeed * speedFactor
            viewVectorNormalized = geo2.Vec3Normalize(self._eyePositionCurrent)
            axis = geo2.Vec3Cross(viewVectorNormalized, self.upVector)
            rotPitch = geo2.MatrixRotationAxis(axis, pitchChange)
            self._eyePositionCurrent = geo2.Vec3Transform(self._eyePositionCurrent, rotPitch)
            self._pitchSpeed -= pitchChange
        else:
            self._pitchSpeed = 0.0
        if self._panSpeed:
            panDistance = geo2.Vec3Length(self._panSpeed)
            if panDistance > 0.001:
                toMove = geo2.Vec3Scale(self._panSpeed, 0.95)
                self.pointOfInterest = geo2.Add(self.pointOfInterest, toMove)
                self._panSpeed -= toMove
            else:
                self._panSpeed = None
        cameraDistance = self.GetZoomDistance()
        cameraDistanceDiff = self._translationFromPOI - cameraDistance
        if math.fabs(cameraDistanceDiff) > 0.001:
            usedDist = cameraDistanceDiff * 0.1
            viewVectorNormalized = geo2.Vec3Normalize(self._eyePositionCurrent)
            newDistance = min(self.maxDistance, max(self.minDistance, cameraDistance + usedDist))
            self._eyePositionCurrent = geo2.Vec3Scale(viewVectorNormalized, newDistance)
            self.translationFromParent = newDistance
        self.UpdateProjection()
        self.UpdateView()
        if self.callback:
            self.callback()

    def UpdateProjection(self):
        if self.viewport:
            aspectRatio = self.viewport.GetAspectRatio()
        else:
            aspectRatio = uicore.uilib.desktop.width / float(uicore.uilib.desktop.height)
        self.projectionMatrix.PerspectiveFov(self.fieldOfView, aspectRatio, self.frontClip, self.backClip)

    def UpdateView(self):
        self.viewMatrix.SetLookAtPosition(geo2.Vec3Add(self._eyePositionCurrent, self._pointOfInterestCurrent), self._pointOfInterestCurrent, self.upVector)

    def GetXAxis(self):
        t = self.viewMatrix.transform
        return (t[0][0], t[1][0], t[2][0])

    def GetYAxis(self):
        t = self.viewMatrix.transform
        return (t[0][1], t[1][1], t[2][1])

    def GetZAxis(self):
        t = self.viewMatrix.transform
        return (t[0][2], t[1][2], t[2][2])

    def GetYawPitch(self):
        rotMatrix = geo2.MatrixTranspose(self.viewMatrix.transform)
        quat = geo2.QuaternionRotationMatrix(rotMatrix)
        yaw, pitch, roll = geo2.QuaternionRotationGetYawPitchRoll(quat)
        yaw = math.pi / 2 - yaw
        pitch = math.pi / 2 - pitch
        return (yaw, pitch)

    def OrbitMouseDelta(self, dx = 0, dy = 0):
        yaw, pitch = self.GetYawPitch()
        self._yawSpeed -= dx * self.fieldOfView * 0.005
        pitchSpeed = self._pitchSpeed + dy * self.fieldOfView * 0.005
        endPitch = max(0.05, min(pitchSpeed + pitch, math.pi - 0.05))
        pitchSpeed -= pitchSpeed + pitch - endPitch
        self._pitchSpeed = pitchSpeed

    def SetYawPitch(self, yaw = None, pitch = None):
        currentYaw, currentPitch = self.GetYawPitch()
        if yaw is not None:
            self._yawSpeed = currentYaw - yaw
        if pitch is not None:
            self._pitchSpeed = pitch - currentPitch

    def PanMouseDelta(self, dx, dy):
        unit = geo2.Vec3Length(self._eyePositionCurrent) / math.atan(self.fieldOfView / 2)
        if self.viewport:
            viewUnit = unit / self.viewport.height / 2.0
        else:
            viewUnit = 2.0
        if self._panSpeed is None:
            self._panSpeed = geo2.Vector(0, 0, 0)
        if dx:
            self._panSpeed += geo2.Scale(self.GetXAxis(), -dx * viewUnit)
        if dy:
            self._panSpeed += geo2.Scale(self.GetYAxis(), dy * viewUnit)

    def ZoomMouseWheelDelta(self, dz):
        dz = dz / 500.0
        self.ZoomToDistance(self._translationFromPOI + dz * self._translationFromPOI)

    def ZoomMouseDelta(self, dx, dy):
        dz = -dy / 100.0
        self.ZoomToDistance(self._translationFromPOI + dz * self._translationFromPOI)

    def SetMinTranslationFromParent(self, minDistance):
        refresh = self._translationFromPOI < minDistance
        self.minDistance = minDistance
        if refresh:
            self.ZoomToDistance(minDistance)

    def ZoomToDistance(self, endCameraDistance):
        self._translationFromPOI = max(self.minDistance, min(self.maxDistance, endCameraDistance))

    def GetZoomDistance(self):
        return geo2.Vec3Length(self._eyePositionCurrent)

    def GetZoomProportion(self):
        dist = self.GetZoomDistance()
        return (dist - self.minDistance) / (self.maxDistance - self.minDistance)

    def ClampAngle(self, angle):
        while angle < 0:
            angle += 2 * math.pi

        while angle >= 2 * math.pi:
            angle -= 2 * math.pi

        return angle
