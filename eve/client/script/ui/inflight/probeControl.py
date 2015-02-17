#Embedded file name: eve/client/script/ui/inflight\probeControl.py
from carbon.common.script.util.mathUtil import DegToRad
from carbonui.primitives.bracket import Bracket
from eve.client.script.ui.inflight.probeBracket import ProbeBracket
from eve.client.script.ui.shared.maps.mapcommon import SYSTEMMAP_SCALE
import trinity
import carbonui.const as uiconst
import math
import geo2
from math import pi
CURSOR_SCALE_ARG_1 = 2000000.0
CURSOR_SCALE = SYSTEMMAP_SCALE * 250000000000.0
CURSOR_COLOR_PARAMETER_INDEX = 2
CURSOR_DEFAULT_COLOR = (0.7960784435272217, 0.8313725590705872, 0.8509804010391235, 1.0)
CURSOR_HIGHLIGHT_COLOR = (0.29411764705882354, 0.7254901960784313, 0.996078431372549, 1.0)
TR2TM_LOOK_AT_CAMERA = 3

class BaseProbeControl(object):

    def __init__(self, uniqueID, parent):
        locator = trinity.EveTransform()
        locator.name = 'spherePar_%s' % uniqueID
        parent.children.append(locator)
        cursor = trinity.Load('res:/Model/UI/probeCursor.red')
        cursor.scaling = (CURSOR_SCALE, CURSOR_SCALE, CURSOR_SCALE)
        cursor.useDistanceBasedScale = True
        cursor.distanceBasedScaleArg1 = 1500000.0
        cursor.distanceBasedScaleArg2 = 0.0
        cursor.translation = (0.0, 0.0, 0.0)
        for c in cursor.children:
            c.name += '_' + str(uniqueID)

        locator.children.append(cursor)
        self.uniqueID = uniqueID
        self.cursor = cursor
        self.locator = locator

    def SetPosition(self, position):
        """
        set the position of the probe thingy
        position: x,y,z coordinates as tuple or geo2.Vector
        """
        position = geo2.Vector(*position)
        self.locator.translation = position

    def GetPosition(self):
        return geo2.Vector(self.locator.translation)

    def GetWorldPosition(self):
        return geo2.Vector(self.locator.worldTransform[3][:3])

    def ShiftPosition(self, translation):
        """
        translate the coordinates
        translation: x,y,z coordinates as tuple or geo2.Vector
        """
        newPos = geo2.Vector(*self.locator.translation) + geo2.Vector(*translation)
        self.SetPosition(newPos)

    def ResetCursorHighlight(self):
        for each in self.cursor.children:
            each.mesh.opaqueAreas[0].effect.parameters[CURSOR_COLOR_PARAMETER_INDEX].value = CURSOR_DEFAULT_COLOR

    def HighlightAxis(self, hiliteAxis):
        for each in self.cursor.children:
            cursorName, side, probeID = each.name.split('_')
            cursorAxis = cursorName[6:]
            if hiliteAxis == cursorAxis:
                each.mesh.opaqueAreas[0].effect.parameters[CURSOR_COLOR_PARAMETER_INDEX].value = CURSOR_HIGHLIGHT_COLOR
            elif len(hiliteAxis) == 2 and cursorAxis in hiliteAxis:
                each.mesh.opaqueAreas[0].effect.parameters[CURSOR_COLOR_PARAMETER_INDEX].value = CURSOR_HIGHLIGHT_COLOR

    def ShowIntersection(self):
        pass


class ProbeControl(BaseProbeControl):
    """
    Struct for managing probe graphic stuff
    """
    __update_on_reload__ = 1

    def __init__(self, probeID, probe, parent, scanner):
        """
        Construct and load all graphic elements and resources
        probeID: id of probe
        probe: probe data KeyVal struct
        parent: parent EveTransform to attach probe control to
        """
        scanSvc = sm.GetService('scanSvc')
        BaseProbeControl.__init__(self, probeID, parent)
        sphereBracket = Bracket()
        sphereBracket.align = uiconst.NOALIGN
        sphereBracket.width = sphereBracket.height = 2
        sphereBracket.state = uiconst.UI_DISABLED
        sphereBracket.name = '__probeSphereBracket'
        sphereBracket.trackTransform = self.locator
        sphereBracket.probeID = probeID
        sphereBracket.positionProbeID = probeID
        uicore.layer.systemMapBrackets.children.insert(0, sphereBracket)
        sphere = trinity.Load('res:/dx9/model/UI/Scanbubble.red')
        sphere.name = 'Scanbubble'
        sphere.children[0].scaling = (2.0, 2.0, 2.0)
        sphere.children[0].children[0].scaling = (-50.0, 50.0, 50.0)
        sphere.children[0].children[1].scaling = (50.0, 50.0, 50.0)
        sphere.children[0].children[2].scaling = (50.0, 50.0, 50.0)
        sphere.children[0].curveSets[1].curves[0].keys[1].time = 0.0625
        sphere.children[0].curveSets[1].curves[0].Sort()
        self.locator.children.append(sphere)
        cal = trinity.EveTransform()
        cal.name = 'cameraAlignedLocation'
        cal.modifier = TR2TM_LOOK_AT_CAMERA
        sphere.children.append(cal)
        tracker = trinity.EveTransform()
        tracker.name = 'pr_%d' % probe.probeID
        val = math.sin(DegToRad(45.0)) * 0.2
        translation = (val, val, 0.0)
        tracker.translation = translation
        cal.children.append(tracker)
        bracket = ProbeBracket()
        bracket.name = '__probeSphereBracket'
        bracket.align = uiconst.NOALIGN
        bracket.state = uiconst.UI_HIDDEN
        bracket.width = bracket.height = 16
        bracket.dock = False
        bracket.minDispRange = 0.0
        bracket.maxDispRange = 1e+32
        bracket.inflight = False
        bracket.color = None
        bracket.invisible = False
        bracket.fadeColor = False
        bracket.showLabel = 2
        bracket.probe = probe
        bracket.probeID = probeID
        bracket.displayName = scanSvc.GetProbeLabel(probeID)
        bracket.showDistance = 0
        bracket.noIcon = True
        bracket.Startup(probeID, probe.typeID, None)
        bracket.trackTransform = tracker
        uicore.layer.systemMapBrackets.children.insert(0, bracket)
        bracket.ShowLabel()
        bracket.label.OnClick = None
        bracket.label.state = uiconst.UI_HIDDEN
        intersection = trinity.Load('res:/Model/UI/probeIntersection.red')
        intersection.display = False
        intersection.scaling = (2.0, 2.0, 2.0)
        sphere.children.append(intersection)
        self.bracket = bracket
        self.scanRanges = scanSvc.GetScanRangeStepsByTypeID(probe.typeID)
        self.intersection = intersection
        self.sphere = sphere
        self.cameraAlignedLocation = cal
        self.probeID = probeID
        self.scanrangeCircles = None
        self._highlighted = True
        self.HighlightBorder(0)

    def SetScanDronesState(self, state):
        for c in self.sphere.children[0].children:
            if c.name == 'Circle':
                c.display = state

    def SetRange(self, probeRange):
        """
        Set the probe range accepting range in meters and automagically scaling the value
        range: radius in meters
        """
        self.sphere.scaling = (probeRange, probeRange, probeRange)

    def ScaleRange(self, scale):
        """
        Scale range with a scalar
        scale: scalar value used to scale current scale
        """
        scale = self.sphere.scaling[0] * scale
        self.SetRange((scale, scale, scale))

    def GetRange(self):
        return self.sphere.scaling[0]

    def HighlightBorder(self, on = 1):
        if bool(on) == self._highlighted:
            return
        self._highlighted = bool(on)
        curveSets = self.sphere.Find('trinity.TriCurveSet')
        curveSet = None
        for each in curveSets:
            if getattr(each, 'name', None) == 'Highlight':
                curveSet = each
                break

        if curveSet:
            curveSet.Stop()
            if on:
                curveSet.scale = 1.0
                curveSet.Play()
            else:
                curveSet.scale = -1.0
                curveSet.PlayFrom(curveSet.GetMaxCurveDuration())

    def ShowIntersection(self, axis = None, side = None):
        if axis == 'xy':
            q = geo2.QuaternionRotationSetYawPitchRoll(0.0, 0.0, 0.0)
            self.intersection.rotation = q
            self.intersection.display = True
            if side == 0:
                self.intersection.translation = (0.0, 0.0, -2.0)
            else:
                self.intersection.translation = (0.0, 0.0, 2.0)
        elif axis == 'yz':
            q = geo2.QuaternionRotationSetYawPitchRoll(pi * 0.5, 0.0, 0.0)
            self.intersection.rotation = q
            self.intersection.display = True
            if side == 0:
                self.intersection.translation = (-2.0, 0.0, 0.0)
            else:
                self.intersection.translation = (2.0, 0.0, 0.0)
        else:
            self.intersection.display = False

    def HideScanRanges(self):
        if self.scanrangeCircles is not None:
            self.scanrangeCircles.display = False

    def ShowScanRanges(self):
        if self.scanrangeCircles is None:
            par = trinity.EveTransform()
            self.scanrangeCircles = par
            par.modifier = TR2TM_LOOK_AT_CAMERA
            self.locator.children.append(par)
            for r in self.scanRanges:
                r *= 100.0
                sr = trinity.Load('res:/Model/UI/probeRange.red')
                sr.scaling = (r, r, r)
                par.children.append(sr)

        self.scanrangeCircles.display = True

    def HighlightProbe(self):
        self.HighlightBorder(1)
        self.bracket.label.state = uiconst.UI_NORMAL

    def StopHighlightProbe(self):
        self.HighlightBorder(0)
        self.bracket.label.state = uiconst.UI_HIDDEN
