#Embedded file name: sensorsuite/overlay\sitecompass.py
from carbon.common.lib import telemetry
from carbon.common.lib.const import SEC
from carbon.common.script.util.mathUtil import MATH_PI_2, MATH_2_PI, MATH_PI_8
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
import carbonui.const as uiconst
import geo2
import math
import logging
from carbonui.uianimations import animations
from carbonui.util.color import Color
from eve.client.script.ui.control.buttons import ButtonIcon
from sensorsuite.overlay.sitetype import *
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from eve.client.script.util.settings import IsShipHudTopAligned
import localization
from sensorsuite.overlay.siteconst import COMPASS_DIRECTIONS_COLOR, COMPASS_SWEEP_COLOR, COMPASS_OPACITY_ACTIVE
from sensorsuite.overlay.sitefilter import SiteButton
import trinity
import blue
logger = logging.getLogger(__name__)
COMPASS_WIDTH = 200
INDICATOR_RADIUS_OFFSET = 16
INDICATOR_HEIGHT = 18
INDICATOR_WIDTH = 15
INCLINATION_TICK_MAX_OFFSET = 6
INCLINATION_TICK_TOP_OFFSET = 0
INCLINATION_TICK_BASE_OPACITY = 0.5
INCLINATION_TICK_HIGHLIGHT_OPACITY = 0.4
INCLINATION_HIGHLIGHT_RANGE_RADIANS = MATH_PI_8

def AreVectorsEqual(a, b, delta):
    for x in xrange(3):
        if math.fabs(a[x] - b[x]) > delta:
            return False

    return True


class Compass(Container):
    default_name = 'compass'
    default_width = COMPASS_WIDTH
    default_height = COMPASS_WIDTH
    default_align = uiconst.CENTER
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.cameraSvc = sm.GetService('camera')
        self.michelle = sm.GetService('michelle')
        self.compassTransform = Transform(name='compass_transform', parent=self, width=COMPASS_WIDTH, height=COMPASS_WIDTH, align=uiconst.CENTER, opacity=COMPASS_OPACITY_ACTIVE)
        Sprite(name='compass_dots', bgParent=self.compassTransform, texturePath='res:/UI/Texture/classes/SensorSuite/compass_dots.png', color=COMPASS_DIRECTIONS_COLOR.GetRGBA())
        self.sweepTransform = Transform(bgParent=self.compassTransform, name='compass_transform', width=COMPASS_WIDTH, height=COMPASS_WIDTH, align=uiconst.CENTER, opacity=0.0)
        Sprite(name='sensor_sweep', bgParent=self.sweepTransform, texturePath='res:/UI/Texture/classes/SensorSuite/scan_sweep.png', blendMode=trinity.TR2_SBM_ADD, color=COMPASS_SWEEP_COLOR.GetRGBA())
        Sprite(name='sensor_centerline', bgParent=self, texturePath='res:/UI/Texture/classes/SensorSuite/compass_centerline.png', blendMode=trinity.TR2_SBM_ADD, opacity=0.2)
        Sprite(name='compass_underlay', bgParent=self, texturePath='res:/UI/Texture/classes/SensorSuite/compass_underlay.png')
        self.sensorSuite = sm.GetService('sensorSuite')
        self.siteIndicatorsBySiteID = {}
        self.lastPose = None
        logger.debug('Compass updating starting')
        self.timer = AutoTimer(40, self.__UpdateCompass)
        self.sensorSuite.AddSiteObserver(self.OnSiteChanged)
        self.sensorSuite.AddSweepObserver(self.OnSweepStarted, self.OnSweepEnded)

    def GetCamera(self):
        return self.cameraSvc.GetSpaceCamera()

    def Close(self):
        Container.Close(self)
        self.timer = None
        sensorSuite = sm.GetService('sensorSuite')
        sensorSuite.RemoveSiteObserver(self.OnSiteChanged)
        sensorSuite.RemoveSweepObserver(self.OnSweepStarted, self.OnSweepEnded)

    @telemetry.ZONE_METHOD
    def __UpdateCompass(self):
        bp = self.michelle.GetBallpark()
        if bp is None:
            return
        camera = self.GetCamera()
        camRotation = geo2.QuaternionRotationGetYawPitchRoll(camera.rotationAroundParent)
        yaw, pitch, roll = camRotation
        cx, cy, cz = geo2.QuaternionTransformVector(camera.rotationAroundParent, (0, 0, -1.0))
        camLengthInPlane = geo2.Vec2Length((cx, cz))
        camAngle = math.atan2(cy, camLengthInPlane)
        self.compassTransform.rotation = -yaw + math.pi
        myPos = bp.GetCurrentEgoPos()
        if self.lastPose:
            lastCamRot, lastPos = self.lastPose
            isNewCamRotation = not AreVectorsEqual(lastCamRot, camRotation, 0.05)
            isNewPosition = not AreVectorsEqual(lastPos, myPos, 0.5)
            isNewPose = isNewPosition or isNewCamRotation
        else:
            isNewPosition = True
            isNewPose = True
        for siteID, indicator in self.siteIndicatorsBySiteID.iteritems():
            if indicator.isNew or isNewPose:
                toSiteVec = geo2.Vec3SubtractD(indicator.data.position, myPos)
                toSiteVec = geo2.Vec3NormalizeD(toSiteVec)
                if indicator.isNew or isNewPosition:
                    angle = math.atan2(-toSiteVec[2], toSiteVec[0])
                    indicator.SetRotation(angle + MATH_PI_2)
                sx, sy, sz = toSiteVec
                siteLengthInPlane = geo2.Vec2Length((sx, sz))
                siteAngle = math.atan2(sy, siteLengthInPlane)
                inclinationAngle = siteAngle - camAngle
                verticalAngle = min(inclinationAngle, MATH_PI_2)
                indicator.SetInclination(verticalAngle)
                indicator.isNew = False

        self.lastPose = (camRotation, myPos)

    def OnSiteChanged(self, siteData):
        indicator = self.siteIndicatorsBySiteID.get(siteData.siteID)
        if indicator:
            indicator.isNew = True
        self.UpdateVisibleSites()

    def OnSweepStarted(self, systemReadyTime, durationInSec, viewAngleInPlane, orderedDelayAndSiteList, sweepStartDelayMSec):
        logger.debug('OnSweepStarted readyTime=%s durationInSec=%s angle=%s sweepStartDelayMSec=%s', systemReadyTime, durationInSec, viewAngleInPlane, sweepStartDelayMSec)
        timeNow = blue.os.GetWallclockTime()
        timeSinceStartSec = float(timeNow - systemReadyTime) / SEC
        if timeSinceStartSec > sweepStartDelayMSec:
            logger.debug('OnSweepStarted too late. timeSinceStartSec=%s timeNow=%s', timeSinceStartSec, timeNow)
            self.UpdateVisibleSites()
            self.OnSweepEnded()
            return
        timeOffset = sweepStartDelayMSec - timeSinceStartSec
        self.UpdateVisibleSites()
        animations.FadeTo(self.sweepTransform, duration=durationInSec, startVal=0.0, endVal=0.0, curveType=((0.05, 1.0), (0.95, 1.0)), timeOffset=timeOffset)
        viewAngleInPlane += MATH_PI_2
        animations.Tr2DRotateTo(self.sweepTransform, duration=durationInSec, startAngle=viewAngleInPlane, endAngle=viewAngleInPlane + MATH_2_PI, curveType=uiconst.ANIM_LINEAR, timeOffset=timeOffset)
        for delaySec, siteData in orderedDelayAndSiteList:
            indicator = self.siteIndicatorsBySiteID.get(siteData.siteID)
            if indicator:
                animations.FadeIn(indicator, duration=0.2, curveType=uiconst.ANIM_OVERSHOT, timeOffset=delaySec - timeSinceStartSec)

    def OnSweepEnded(self):
        for indicator in self.compassTransform.children:
            indicator.opacity = 1.0

    @telemetry.ZONE_METHOD
    def UpdateVisibleSites(self):
        if not self.sensorSuite.IsSolarSystemReady():
            return
        siteMap = self.sensorSuite.siteController.GetVisibleSiteMap()
        for siteID in self.siteIndicatorsBySiteID.keys():
            if siteID not in siteMap:
                self.RemoveSiteIndicator(siteID)

        for siteData in siteMap.itervalues():
            if siteData.siteID not in self.siteIndicatorsBySiteID:
                self.AddSiteIndicator(siteData)

    def AddSiteIndicator(self, siteData):
        logger.debug('adding site indicator %s', siteData.siteID)
        indicator = CompassIndicator(parent=self.compassTransform, siteData=siteData)
        if self.sensorSuite.IsSweepDone() or IsSiteInstantlyAccessible(siteData):
            indicator.opacity = 1.0
        else:
            indicator.opacity = 0.0
        self.siteIndicatorsBySiteID[siteData.siteID] = indicator

    def RemoveSiteIndicator(self, siteID):
        logger.debug('removing site indicator %s', siteID)
        indicator = self.siteIndicatorsBySiteID.pop(siteID)
        indicator.Close()

    def RemoveAll(self):
        for siteID in self.siteIndicatorsBySiteID.keys():
            self.RemoveSiteIndicator(siteID)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        LoadSensorOverlayFilterTooltip(tooltipPanel)

    def GetTooltipPosition(self):
        left, top, width, height = self.GetAbsolute()
        left += width / 2
        if IsShipHudTopAligned():
            top += height - 7
        else:
            top += 9
        return (left,
         top,
         0,
         0)

    def GetTooltipPointer(self):
        if IsShipHudTopAligned():
            return uiconst.POINT_TOP_2
        return uiconst.POINT_BOTTOM_2


class CompassIndicator(Transform):
    default_height = COMPASS_WIDTH - INDICATOR_RADIUS_OFFSET
    default_width = COMPASS_WIDTH - INDICATOR_RADIUS_OFFSET
    default_name = 'compass_indicator'
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        Transform.ApplyAttributes(self, attributes)
        self.data = attributes.siteData
        self.sprite = Sprite(parent=self, texturePath='res:/UI/Texture/classes/SensorSuite/small_tick.png', align=uiconst.CENTERTOP, width=INDICATOR_WIDTH, height=INDICATOR_HEIGHT, color=self.data.baseColor.GetRGBA(), blendMode=trinity.TR2_SBM_ADDX2, opacity=INCLINATION_TICK_BASE_OPACITY)
        self.verticalSprite = Sprite(parent=self, texturePath='res:/UI/Texture/classes/SensorSuite/big_tick.png', align=uiconst.CENTERTOP, width=INDICATOR_WIDTH, height=INDICATOR_HEIGHT, color=self.data.baseColor.GetRGBA(), blendMode=trinity.TR2_SBM_ADD, opacity=0.5)
        self.isNew = True

    @telemetry.ZONE_METHOD
    def SetRotation(self, rotation = 0):
        Transform.SetRotation(self, rotation)

    @telemetry.ZONE_METHOD
    def SetInclination(self, angle):
        offset = -angle / MATH_PI_2 * INCLINATION_TICK_MAX_OFFSET
        self.sprite.top = INCLINATION_TICK_TOP_OFFSET + offset
        absAngle = math.fabs(angle)
        if absAngle < INCLINATION_HIGHLIGHT_RANGE_RADIANS:
            opacity = INCLINATION_TICK_BASE_OPACITY + (1 - absAngle / INCLINATION_HIGHLIGHT_RANGE_RADIANS) * INCLINATION_TICK_HIGHLIGHT_OPACITY
        else:
            opacity = INCLINATION_TICK_BASE_OPACITY
        self.sprite.opacity = opacity


def LoadSensorOverlayFilterTooltip(tooltipPanel):
    sensorSuite = sm.GetService('sensorSuite')
    tooltipPanel.pickState = uiconst.TR2_SPS_ON
    tooltipPanel.LoadGeneric2ColumnTemplate()
    heading = CreateSensorOverlayHeading()
    tooltipPanel.AddCell(heading, colSpan=2)
    tooltipPanel.AddCell(Container(height=2, align=uiconst.NOALIGN), colSpan=2)
    buttons = []
    siteTypes = [ANOMALY,
     BOOKMARK,
     STATIC_SITE,
     CORP_BOOKMARK,
     SIGNATURE,
     MISSION]
    for siteType in siteTypes:
        handler = sensorSuite.siteController.GetSiteHandler(siteType)
        config = handler.GetFilterConfig()
        button = SiteButton(filterConfig=config, isActive=config.enabled)
        buttons.append(button)
        tooltipPanel.AddCell(button)

    maxWidth = max([ b.width for b in buttons ])
    for b in buttons:
        b.width = maxWidth

    heading.width = 2 * maxWidth


def CreateSensorOverlayHeading():
    topEntry = Container(height=20, align=uiconst.NOALIGN)
    EveLabelMediumBold(parent=topEntry, align=uiconst.CENTERLEFT, text=localization.GetByLabel('UI/Inflight/Scanner/SensorOverlay'))
    button = ButtonIcon(name='overlayButton', parent=topEntry, align=uiconst.CENTERRIGHT, width=16, height=16, iconSize=16, texturePath='res://UI/Texture/classes/SensorSuite/sensor_overlay_small.png', func=OnToggleOverlayActive)
    button.args = button
    SetOverlayButtonActiveState(button, sm.GetService('sensorSuite').IsOverlayActive())
    return topEntry


def OnToggleOverlayActive(button):
    sensorSuite = sm.GetService('sensorSuite')
    isActive = sensorSuite.IsOverlayActive()
    if isActive:
        sensorSuite.DisableSensorOverlay()
    else:
        sensorSuite.EnableSensorOverlay()
    SetOverlayButtonActiveState(button, not isActive)


def SetOverlayButtonActiveState(button, isActive):
    if isActive:
        color = (0.1, 1.0, 0.1, 1.0)
        hint = localization.GetByLabel('UI/Inflight/Scanner/DisableSensorOverlay')
    else:
        color = Color.GetGrayRGBA(1.0, 0.5)
        hint = localization.GetByLabel('UI/Inflight/Scanner/EnableSensorOverlay')
    button.icon.SetRGB(*color)
    button.hint = hint
