#Embedded file name: eve/client/script/ui/camera\baseCamera.py
import math
import trinity
import geo2
import uthread
import blue
from collections import defaultdict

class Camera(object):
    __guid__ = 'util.Camera'
    __typename__ = None
    __notifyevents__ = ['OnSetDevice']
    name = 'util.Camera'
    default_fov = 1.0
    default_nearClip = 1.0
    default_farClip = 1000000
    default_eyePosition = (0, 500, 1000)
    default_atPosition = (0, 0, 0)
    default_upDirection = (0, 1, 0)
    maxZoom = 100
    minZoom = 10000
    kZoomSpeed = 4.0
    kZoomStopDist = 100
    kOrbitSpeed = 2.0
    kOrbitStopAngle = 0.0001
    kMinPitch = 0.05
    kMaxPitch = math.pi - kMinPitch
    kPanSpeed = 5.0
    kPanStopDist = 50

    def __init__(self):
        sm.RegisterNotify(self)
        self._animationCurves = {}
        self._fov = self.default_fov
        self._nearClip = self.default_nearClip
        self._farClip = self.default_farClip
        self._eyePosition = self.default_eyePosition
        self._atPosition = self.default_atPosition
        self._upDirection = self.default_upDirection
        self.panTarget = None
        self.panUpdateThread = None
        self.zoomTarget = None
        self.zoomUpdateThread = None
        self.orbitTarget = None
        self.orbitUpdateThread = None
        self.eventListeners = defaultdict(list)
        self.viewMatrix = trinity.TriView()
        self.projectionMatrix = trinity.TriProjection()
        self.Update()

    def Update(self):
        self.UpdateProjection()
        self.UpdateView()

    def OnSetDevice(self, *args):
        self.UpdateProjection()

    def Close(self):
        self.StopAnimations()
        if self.panUpdateThread:
            self.panUpdateThread.kill()
        if self.zoomUpdateThread:
            self.zoomUpdateThread.kill()
        if self.orbitUpdateThread:
            self.orbitUpdateThread.kill()
        sm.UnregisterNotify(self)

    def UpdateProjection(self):
        aspectRatio = uicore.uilib.desktop.width / float(uicore.uilib.desktop.height)
        self.projectionMatrix.PerspectiveFov(self._fov, aspectRatio, self._nearClip, self._farClip)

    def UpdateView(self):
        self.viewMatrix.SetLookAtPosition(self._eyePosition, self._atPosition, self._upDirection)

    def GetXAxis(self):
        t = self.viewMatrix.transform
        return (t[0][0], t[1][0], t[2][0])

    def GetYAxis(self):
        t = self.viewMatrix.transform
        return (t[0][1], t[1][1], t[2][1])

    def GetZAxis(self):
        t = self.viewMatrix.transform
        return (t[0][2], t[1][2], t[2][2])

    def GetLookAtDirection(self):
        return geo2.Vec3Direction(self.eyePosition, self.atPosition)

    def Pan(self, dx = 0, dy = 0, dz = 0):
        """ Pan along current camera xyz coordinates """
        if self.panTarget is None:
            self.panTarget = geo2.Vector(0, 0, 0)
        if dx:
            self.panTarget += geo2.Scale(self.GetXAxis(), dx)
        if dy:
            self.panTarget += geo2.Scale(self.GetYAxis(), dy)
        if dz:
            self.panTarget += geo2.Scale(self.GetZAxis(), dz)
        if not self.panUpdateThread:
            self.panUpdateThread = uthread.new(self.PanUpdateThread)

    def PanAxis(self, axis, amount):
        """ Pan along a given axis """
        if self.panTarget is None:
            self.panTarget = geo2.Vector(0, 0, 0)
        self.panTarget += geo2.Scale(axis, amount)
        if not self.panUpdateThread:
            self.panUpdateThread = uthread.new(self.PanUpdateThread)

    def PanUpdateThread(self):
        while True:
            if self.panTarget is None:
                break
            distLeft = geo2.Vec3Length(self.panTarget)
            if distLeft == 0:
                break
            dist = self.kPanSpeed / blue.os.fps
            if distLeft < self.kPanStopDist:
                dist *= self.kPanStopDist / distLeft
            dist = min(dist, 1.0)
            toMove = geo2.Vec3Scale(self.panTarget, dist)
            self.eyePosition = geo2.Add(self.eyePosition, toMove)
            self.atPosition = geo2.Add(self.atPosition, toMove)
            self.panTarget -= toMove
            if dist == 1.0:
                break
            blue.synchro.Yield()

        self.panUpdateThread = None
        self.panTarget = None

    def _EnforceMinMaxZoom(self, eyePos):
        vEye = geo2.Subtract(eyePos, self.atPosition)
        vMaxZoom = geo2.Scale(self.GetZAxis(), self.maxZoom)
        vEyeToMaxZoom = geo2.Subtract(vEye, vMaxZoom)
        if geo2.Vec3Dot(vEyeToMaxZoom, vMaxZoom) < 0:
            eyePos = geo2.Add(self.atPosition, vMaxZoom)
            self.zoomTarget = None
        vMinZoom = geo2.Scale(self.GetZAxis(), self.minZoom)
        vEyeToMinZoom = geo2.Subtract(vEye, vMinZoom)
        if geo2.Vec3Dot(vEyeToMinZoom, vMinZoom) > 0:
            eyePos = geo2.Add(self.atPosition, vMinZoom)
            self.zoomTarget = None
        return eyePos

    def Zoom(self, dz):
        if self.zoomTarget is None:
            self.zoomTarget = self.GetZoomDistance()
        self.zoomTarget += dz
        if not self.zoomUpdateThread:
            self.zoomUpdateThread = uthread.new(self.ZoomUpdateThread)

    def ZoomUpdateThread(self):
        while True:
            if self.zoomTarget is None:
                break
            distLeft = self.zoomTarget - self.GetZoomDistance()
            if not distLeft:
                break
            moveProp = self.kZoomSpeed / blue.os.fps
            if math.fabs(distLeft) < self.kZoomStopDist:
                moveProp *= self.kZoomStopDist / math.fabs(distLeft)
            moveProp = min(moveProp, 1.0)
            toMove = geo2.Vec3Scale(self.GetLookAtDirection(), moveProp * distLeft)
            eyePos = geo2.Add(self.eyePosition, toMove)
            self.eyePosition = self._EnforceMinMaxZoom(eyePos)
            if moveProp == 1.0:
                break
            for listener in self.eventListeners['zoom']:
                listener.OnZoomChanged(self.GetZoomProportion())

            blue.synchro.Yield()

        self.zoomUpdateThread = None
        self.zoomTarget = None

    def StopUpdateThreads(self, exceptTarget = None):
        if self.zoomTarget != exceptTarget:
            self.zoomTarget = None
        if self.panTarget != exceptTarget:
            self.panTarget = None
        if self.orbitTarget != exceptTarget:
            self.orbitTarget = None

    def GetZoomDistance(self):
        return geo2.Vec3Distance(self.eyePosition, self.atPosition)

    def GetZoomProportion(self):
        dist = self.GetZoomDistance()
        return (dist - self.maxZoom) / (self.minZoom - self.maxZoom)

    def RegisterZoomListener(self, listener):
        self.eventListeners['zoom'].append(listener)

    def UnregisterZoomListener(self, listener):
        if listener in self.eventListeners['zoom']:
            self.eventListeners['zoom'].remove(listener)

    def SetMaxZoom(self, value):
        self.maxZoom = value

    def SetMinZoom(self, value):
        self.minZoom = value

    def Orbit(self, dx = 0, dy = 0):
        diff = geo2.Subtract(self.eyePosition, self.atPosition)
        if not self.orbitTarget:
            self.orbitTarget = (0, self.GetAngleLookAtToUpDirection())
        yaw = self.orbitTarget[0] - dx
        pitch = self.orbitTarget[1] - dy / 2.0
        pitch = max(self.kMinPitch, min(pitch, self.kMaxPitch))
        self.orbitTarget = [yaw, pitch]
        if not self.orbitUpdateThread:
            self.orbitUpdateThread = uthread.new(self.OrbitUpdateThread)

    def OrbitUpdateThread(self):
        try:
            while True:
                if self.orbitTarget is None:
                    break
                vLookAt = self.GetLookAtDirection()
                currPitch = self.GetAngleLookAtToUpDirection()
                self.eyePosition = geo2.Subtract(self.eyePosition, self.atPosition)
                yawLeft = self.orbitTarget[0]
                if yawLeft:
                    yaw = self.kOrbitSpeed * yawLeft / blue.os.fps
                    if math.fabs(yawLeft) < self.kOrbitStopAngle:
                        yaw = yawLeft
                    rotYaw = geo2.MatrixRotationAxis(self.upDirection, yaw)
                    self.eyePosition = geo2.Vec3Transform(self.eyePosition, rotYaw)
                    self.orbitTarget[0] -= yaw
                targetPitch = self.orbitTarget[1]
                pitchLeft = currPitch - targetPitch
                if pitchLeft:
                    pitch = self.kOrbitSpeed * pitchLeft / blue.os.fps
                    if math.fabs(pitchLeft) < self.kOrbitStopAngle:
                        pitch = pitchLeft
                    axis = geo2.Vec3Cross(vLookAt, self.upDirection)
                    rotPitch = geo2.MatrixRotationAxis(axis, pitch)
                    self.eyePosition = geo2.Vec3Transform(self.eyePosition, rotPitch)
                self.eyePosition = geo2.Add(self.eyePosition, self.atPosition)
                if not pitchLeft and not yawLeft:
                    break
                blue.synchro.Yield()

        finally:
            self.orbitUpdateThread = None
            self.orbitTarget = None

    def GetAngleLookAtToUpDirection(self):
        try:
            vLookAt = self.GetLookAtDirection()
            return math.acos(geo2.Vec3Dot(vLookAt, self.upDirection) / (geo2.Vec3Length(vLookAt) * geo2.Vec3Length(self.upDirection)))
        except ValueError:
            return 0.0

    def Rotate(self, x = 0, y = 0):
        xAxis = self.GetXAxis()
        yAxis = self.GetYAxis()
        self.atPosition = geo2.Subtract(self.atPosition, self.eyePosition)
        rotY = geo2.MatrixRotationAxis(xAxis, y)
        self.atPosition = geo2.Vec3Transform(self.atPosition, rotY)
        rotX = geo2.MatrixRotationAxis(yAxis, x)
        self.atPosition = geo2.Vec3Transform(self.atPosition, rotX)
        self.atPosition = geo2.Add(self.atPosition, self.eyePosition)

    def GetDistanceFromLookAt(self):
        return geo2.Vec3Distance(self.eyePosition, self.atPosition)

    def LookAt(self, position, duration = None, followWithEye = True, eyePos = None):
        if duration:
            uicore.animations.MorphVector3(self, 'atPosition', self.atPosition, position, duration=duration)
        else:
            self.atPosition = position
        if followWithEye:
            if not eyePos:
                eyePos = geo2.Subtract(self.eyePosition, self.atPosition)
                eyePos = geo2.Add(eyePos, position)
            if duration:
                uicore.animations.MorphVector3(self, 'eyePosition', self.eyePosition, eyePos, duration=duration)
            else:
                self.eyePosition = eyePos

    def TransitTo(self, atPosition, eyePosition, duration = 1.0, smoothing = 1.0, numPoints = 100, timeOffset = 0.0):
        """ Transit smoothly to a new at and eye position """
        newDir = geo2.Vec3Direction(eyePosition, atPosition)
        atPoints = self.GetTransitAtCurve(self.atPosition, atPosition, newDir, smoothing, numPoints=numPoints)
        uicore.animations.MorphVector3(self, 'atPosition', curveType=atPoints, duration=duration, timeOffset=timeOffset)
        eyePoints = self.GetTransitEyeCurve(eyePosition, atPosition, newDir, atPoints)
        uicore.animations.MorphVector3(self, 'eyePosition', curveType=eyePoints, duration=duration, timeOffset=timeOffset)

    def GetTransitAtCurve(self, posStart, posEnd, newDir, smoothing, numPoints):
        """ Returns control points for the lookAt transit curve spline. We travel along a straight line offset quadtratically according the the smoothing argument"""
        currDir = self.GetLookAtDirection()
        angle = math.acos(geo2.Vec3Dot((currDir[0], 0, currDir[2]), (newDir[1], 0, newDir[2])))
        if smoothing and angle:
            offset = geo2.Vec3Normalize(geo2.Vec3Negate(newDir))
            dist = geo2.Vec3Distance(posStart, posEnd)
            offset = geo2.Vec3Scale(offset, dist * angle * smoothing)
        else:
            offset = (0, 0, 0)
        points = []
        for i in xrange(numPoints + 1):
            t = self._GetHermiteValue(float(i) / numPoints)
            offsetDist = 2 * (t - t ** 2)
            point = geo2.Vec3Lerp(posStart, posEnd, t)
            point = geo2.Add(point, geo2.Vec3Scale(offset, offsetDist))
            points.append(point)

        return points

    def GetTransitEyeCurve(self, eyePos, atPos, newDir, atCurve):
        """ Returns control points for the eye transit curve spline. To get a smooth transition, we do a linear interpolation of the rotation around the y-axis, radius and y-value. """
        currDir = self.GetLookAtDirection()
        try:
            angle = math.acos(geo2.Vec3Dot(currDir, newDir))
        except ValueError:
            angle = 0

        th0 = math.atan2(currDir[2], currDir[0])
        th0 = self.ClampAngle(th0)
        th1 = math.atan2(newDir[2], newDir[0])
        th1 = self.ClampAngle(th1)
        if th0 - th1 > math.pi:
            th0 -= 2 * math.pi
        elif th1 - th0 > math.pi:
            th1 -= 2 * math.pi
        r0 = geo2.Vec3Distance((self.eyePosition[0], 0, self.eyePosition[2]), (self.atPosition[0], 0, self.atPosition[2]))
        r1 = geo2.Vec3Distance((eyePos[0], 0, eyePos[2]), (atPos[0], 0, atPos[2]))
        y0 = self.eyePosition[1] - self.atPosition[1]
        y1 = eyePos[1] - atPos[1]
        points = []
        for i, atPoint in enumerate(atCurve):
            t = self._GetHermiteValue(float(i) / len(atCurve))
            r = r0 + t * (r1 - r0)
            th = th0 + t * (th1 - th0)
            y = y0 + t * (y1 - y0)
            point = (r * math.cos(th), y, r * math.sin(th))
            point = geo2.Vec3Add(point, atCurve[i])
            points.append(point)

        return points

    def _GetHermiteValue(self, t):
        """ Hermite interpolation ranging from 0.0-1.0 """
        vec = geo2.Hermite((0, 0), (0, 0), (1, 0), (0, 0), t)
        return vec[0]

    def ClampAngle(self, angle):
        while angle < 0:
            angle += 2 * math.pi

        while angle >= 2 * math.pi:
            angle -= 2 * math.pi

        return angle

    def StopAnimations(self):
        """
        Stop all animation curveSets associated with object
        """
        if self._animationCurves:
            for curveSet in self._animationCurves.values():
                curveSet.Stop()

        self._animationCurves = None

    def GetFov(self):
        return self._fov

    def SetFov(self, value):
        self._fov = value
        self.UpdateProjection()

    fov = property(GetFov, SetFov)

    def GetNearClip(self):
        return self._nearClip

    def SetNearClip(self, value):
        self._nearClip = value
        self.UpdateProjection()

    nearClip = property(GetNearClip, SetNearClip)

    def GetFarClip(self):
        return self._farClip

    def SetFarClip(self, value):
        self._farClip = value
        self.UpdateProjection()

    farClip = property(GetFarClip, SetFarClip)

    def GetEyePosition(self):
        return self._eyePosition

    def SetEyePosition(self, value):
        self._eyePosition = value
        self.UpdateView()

    eyePosition = property(GetEyePosition, SetEyePosition)

    def GetAtPosition(self):
        return self._atPosition

    def SetAtPosition(self, value):
        self._atPosition = value
        self.UpdateView()

    atPosition = property(GetAtPosition, SetAtPosition)

    def GetUpDirection(self):
        return self._upDirection

    def SetUpDirection(self, value):
        self._upDirection = geo2.Vec3Normalize(value)
        self.UpdateView()

    upDirection = property(GetUpDirection, SetUpDirection)
