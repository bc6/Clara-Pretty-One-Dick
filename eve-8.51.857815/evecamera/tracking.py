#Embedded file name: evecamera\tracking.py
import blue
import geo2
import math
import trinity
import trinutils.callbackmanager as cbmanager

class Tracker(object):

    def __init__(self, cameraSvc):
        self._cameraSvc = cameraSvc
        self.job = None
        self.tracking = None
        self.previousTracking = None
        self.trackerRunning = False
        self.trackingPointX, self.trackingPointY = settings.char.ui.Get('tracking_cam_location', (uicore.desktop.width / 2 * 0.8, uicore.desktop.height / 2 * 0.8))
        self.lastTime = blue.os.GetWallclockTime()
        self.trackSwitchTime = blue.os.GetWallclockTime()
        self.tiltX = 0
        self.tiltY = 0
        self.camMaxPitch = 0
        self.camMinPitch = 0
        self.startTrackSpeed = 0.008

    def CalcAngle(self, x, y):
        angle = 0
        if x != 0:
            angle = math.atan(y / x)
            if x < 0 and y >= 0:
                angle = math.atan(y / x) + math.pi
            if x < 0 and y < 0:
                angle = math.atan(y / x) - math.pi
        else:
            if y > 0:
                angle = math.pi / 2
            if y < 0:
                angle = -math.pi / 2
        return angle

    def TrackItem(self, itemID):
        if itemID == self._cameraSvc.LookingAt():
            return
        camera = self._cameraSvc.GetSpaceCamera()
        if camera is None:
            return
        self.trackSwitchTime = blue.os.GetWallclockTime()
        if itemID is None and self.tracking is not None:
            self.previousTracking = None
            self.chaseCam = False
            camera.maxPitch = self.camMaxPitch
            camera.minPitch = self.camMinPitch
            camera.rotationOfInterest = geo2.QuaternionIdentity()
            self.tiltX = 0
            self.tiltY = 0
        if self.trackerRunning and itemID is not None:
            camera.maxPitch = 2 * math.pi
            camera.minPitch = -2 * math.pi
            camera.SetOrbit(camera.yaw, camera.pitch)
        self.tracking = itemID
        if not self.trackerRunning:
            self.camMaxPitch = camera.maxPitch
            self.camMinPitch = camera.minPitch
            cbmanager.CallbackManager.GetGlobal().ScheduleCallback(self._TrackItem)

    def _TrackItem(self):
        self.trackerRunning = True
        if sm.GetService('viewState').GetCurrentView().name != 'inflight':
            return
        if self.tracking is not None:
            trackSpeed = self.startTrackSpeed
            if getattr(self, 'tempTrackSpeedForItem', None) is not None:
                if self.tempTrackSpeedForItem[0] != self.tracking:
                    self.tempTrackSpeedForItem = None
                else:
                    trackSpeed = self.tempTrackSpeedForItem[1]
            self._PointCameraTo(self.tracking, trackSpeed)
        else:
            self.lastTime = blue.os.GetWallclockTime()

    def SetTemporaryTrackSpeed(self, itemID, trackSpeed):
        self.tempTrackSpeedForItem = (itemID, trackSpeed)

    def SetTrackingPoint(self, x, y):
        self.trackingPointX = x
        self.trackingPointY = y

    def _PointCameraTo(self, itemID, panSpeed = math.pi / 500):
        timeDelta = blue.os.TimeDiffInMs(self.lastTime, blue.os.GetWallclockTime())
        self.lastTime = blue.os.GetWallclockTime()
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera is None:
            return
        shipBall = sm.GetService('michelle').GetBall(self._cameraSvc.LookingAt())
        if shipBall is None:
            return
        itemBall = sm.GetService('michelle').GetBall(itemID)
        if not itemBall:
            return
        if getattr(itemBall, 'exploded', False):
            explodedTime = getattr(itemBall, 'explodedTime', None)
            if explodedTime is None:
                return
            explosionWatchTime = 3.0
            timeSinceExplosionInSecs = blue.os.TimeDiffInMs(explodedTime, blue.os.GetTime()) / 1000.0
            if timeSinceExplosionInSecs > explosionWatchTime:
                return
            panSpeed *= 1.0 - timeSinceExplosionInSecs / explosionWatchTime
        if hasattr(itemBall, 'IsCloaked') and itemBall.IsCloaked():
            return
        shipPos = shipBall.GetVectorAt(blue.os.GetSimTime())
        itemPos = itemBall.GetVectorAt(blue.os.GetSimTime())
        t = blue.os.GetWallclockTime()
        timeSinceTargetChange = min(float(blue.os.TimeDiffInMs(self.trackSwitchTime, t)), 5000.0)
        rampUp = min(timeSinceTargetChange / 2000.0, 1.0)
        panSpeed *= rampUp
        arc = self.PointCameraToPos(camera, shipPos, itemPos, panSpeed, timeDelta, trackingPoint=(self.trackingPointX, self.trackingPointY))
        self.RotationAdjust(camera, timeSinceTargetChange, arc, itemID, timeDelta)
        self.UpdateInternalTrackingInfo()

    def UpdateInternalTrackingInfo(self):
        if self.previousTracking != self.tracking:
            self.trackSwitchTime = blue.os.GetWallclockTime()
            self.previousTracking = self.tracking

    def GetRotationDeltas(self, dx, dy, arc, timeSinceTargetChange, dt):
        percentOfWay = min(timeSinceTargetChange / 5000.0, 1)
        timeComponent = 1 - percentOfWay
        tiltBrake = 25000 + 1000000 * pow(arc, 2) * timeComponent
        maxMovement = 0.005
        multiplier = dt / 16.6
        dxmod = dx / tiltBrake
        dymod = dy / tiltBrake
        tdx = min(round(dxmod * multiplier, 4), maxMovement)
        tdy = min(round(dymod * multiplier, 4), maxMovement)
        return (tdx, tdy)

    def RotationAdjust(self, camera, timeSinceTargetChange, arc, itemID, timeDelta):
        br = sm.GetService('bracket')
        itemBracket = br.GetBracket(itemID)
        if itemBracket is None:
            itemBracket = sm.GetService('sensorSuite').GetBracketByBallID(itemID)
        if itemBracket and itemBracket not in br.overlaps:
            bracketRender = itemBracket.renderObject
            if bracketRender is not None and bracketRender.display:
                if itemBracket.parent is uicore.layer.inflight:
                    offset = uicore.layer.inflight.absoluteLeft
                else:
                    offset = 0
                dx = self.trackingPointX - (bracketRender.displayX + bracketRender.displayWidth / 2) - offset
                dy = self.trackingPointY - (bracketRender.displayY + bracketRender.displayHeight / 2)
                tdx, tdy = self.GetRotationDeltas(dx, dy, arc, timeSinceTargetChange, timeDelta)
                tiltAngle = geo2.Vec2Length((tdx, tdy))
                multiplier = min(timeDelta / 16.6, 1)
                minMoveAngle = 0.0005 * multiplier
                if tiltAngle > minMoveAngle:
                    self.tiltX += tdx
                    self.tiltY += tdy
                    self.tiltX = math.fmod(self.tiltX, math.pi * 2)
                    self.tiltY = math.fmod(self.tiltY, math.pi * 2)
                    camera.SetRotationOnOrbit(self.tiltX, self.tiltY)

    def clampPitch(self, pitch):
        return min(self.camMaxPitch, max(pitch, self.camMinPitch))

    def PointCameraToPos(self, camera, shipPos, itemPos, panSpeed, timeDelta, trackingPoint = None):
        m, h = uicore.desktop.width / 2, uicore.desktop.height
        center = trinity.TriVector(uicore.ScaleDpi(m * (1 - camera.centerOffset)), uicore.ScaleDpi(h / 2), 0)
        v2 = shipPos - itemPos
        v2.Normalize()
        yzProj = trinity.TriVector(0, v2.y, v2.z)
        zxProj = trinity.TriVector(v2.x, 0, v2.z)
        yaw = self.CalcAngle(zxProj.z, zxProj.x)
        pitch = -math.asin(min(1.0, max(-1.0, yzProj.y)))
        oldYaw = camera.yaw
        oldPitch = self.clampPitch(camera.pitch)
        dx2 = 0.0
        dy2 = 0.0
        if trackingPoint is not None:
            dx2 = center.x - trackingPoint[0]
            dy2 = center.y - trackingPoint[1]
        alphaX = math.pi * dx2 * camera.fieldOfView / uicore.ScaleDpi(uicore.desktop.width)
        alphaY = math.pi * dy2 * camera.fieldOfView / uicore.ScaleDpi(uicore.desktop.width)
        dPitchTotal = pitch - oldPitch
        dYawTotal = (yaw - camera.yaw) % (2 * math.pi) - alphaX * 0.75
        clampedPitchTotal = min(2 * math.pi - dPitchTotal, dPitchTotal) - alphaY * 0.75
        if dYawTotal > math.pi:
            dYawTotal = -(2 * math.pi - dYawTotal)
        arc = geo2.Vec2Length((dYawTotal, clampedPitchTotal))
        part = min(1, timeDelta * panSpeed)
        dYawPart = dYawTotal * part
        dPitchPart = clampedPitchTotal * part
        Yaw = oldYaw + dYawPart
        Pitch = oldPitch + dPitchPart
        camera.SetOrbit(Yaw, Pitch)
        return arc
