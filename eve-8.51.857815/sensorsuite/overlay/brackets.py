#Embedded file name: sensorsuite/overlay\brackets.py
from carbon.common.lib import telemetry
from carbon.common.script.util.format import FmtDist
from carbon.common.script.util.timerstuff import AutoTimer
import carbonui.const as uiconst
from carbonui.primitives.bracket import Bracket
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.uianimations import animations
from carbonui.util.color import Color
from eve.client.script.parklife.states import selected
from eve.client.script.ui.control.eveLabel import EveLabelSmallBold, EveLabelSmall
from probescanning.const import AU
from sensorsuite.error import InvalidClientStateError
OUTER_BRACKET_ORIENTATIONS = ((1, -1),
 (-1, -1),
 (-1, 1),
 (1, 1))
OUTER_BRACKET_OPACITY_CURVE_POINTS = ((0.0, 0.0),
 (0.495, 1.0),
 (0.5, 0.0),
 (0.62, 1.0),
 (0.625, 0.0),
 (0.745, 1.0),
 (0.75, 0.0),
 (0.87, 1.0),
 (0.875, 0.0),
 (1.0, 1.0))
RADIATING_CIRCLE_OPACITY_CURVE_POINTS = ((0.0, 0.0),
 (0.3, 0.25),
 (0.7, 0.25),
 (1.0, 0.0))
INNER_ICON_COLOR = Color(1.0, 1.0, 1.0, 0.5)
DISTANCE_CELL_SPACING = 4
MIN_LABEL_SIZE = 200
SITE_NAME_FADE_SIZE = 30

def RoundedDistance(dist):
    """Calculates a number to compare with for updates"""
    if dist < 10000.0:
        return (0, int(dist))
    elif dist < 10000000000.0:
        return (1, long(dist / 1000.0))
    else:
        return (2, round(dist / AU, 1))


class SensorSuiteBracket(Bracket):
    __guid__ = 'sensorSuite.SensorSuiteBracket'
    default_width = 16
    default_height = 16
    default_state = uiconst.UI_NORMAL
    default_isScrollEntry = False
    outerColor = Color.YELLOW
    innerColor = INNER_ICON_COLOR.GetRGBA()
    innerIconResPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'
    outerTextures = ('res:/UI/Texture/classes/SensorSuite/bracket_outer_long1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_outer_long2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_outer_long3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_outer_long4.png')

    def IsFloating(self):
        return True

    def LoadTooltipPanel(self, tooltipPanel, *args):
        uicore.layer.inflight.PrepareTooltipLoad(self)

    def ApplyAttributes(self, attributes):
        Bracket.ApplyAttributes(self, attributes)
        self.sensorSuite = sm.GetService('sensorSuite')
        self.isScrollEntry = attributes.get('isScrollEntry', self.default_isScrollEntry)
        self.data = attributes.data
        self.dock = False
        self.iconOpacity = self.innerColor[3]
        self.radialMenuSprite = None
        self.icon = Sprite(name='innerIcon', parent=self, texturePath=self.innerIconResPath, align=uiconst.CENTER, width=20, height=20, state=uiconst.UI_DISABLED)
        self.outerSprites = []
        for n, (x, y) in enumerate(OUTER_BRACKET_ORIENTATIONS):
            sprite = Sprite(name='outerIcon_%d' % n, parent=self, texturePath=self.outerTextures[n], align=uiconst.CENTER, state=uiconst.UI_DISABLED, pos=(x * 11,
             y * 11,
             22,
             22))
            self.outerSprites.append(sprite)

        self.labelContainer = ContainerAutoSize(name='labelContainer', parent=self, left=32, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, width=0, clipChildren=True)
        self.labelContainer.display = False
        self.labelGrid = LayoutGrid(parent=self.labelContainer, align=uiconst.TOTOP, cellSpacing=(DISTANCE_CELL_SPACING, 0))
        self.codeLabel = EveLabelSmallBold(name='codeLabel', singleline=True)
        self.distanceLabel = EveLabelSmall(name='distanceLabel', singleline=True)
        self.siteName = EveLabelSmall(name='siteNameLabel', parent=self.labelContainer, align=uiconst.TOTOP, singleline=True)
        self.labelGrid.AddCell(self.codeLabel)
        self.labelGrid.AddCell(self.distanceLabel)
        self.siteName.SetRightAlphaFade(fadeEnd=MIN_LABEL_SIZE - SITE_NAME_FADE_SIZE, maxFadeWidth=SITE_NAME_FADE_SIZE)
        if not self.isScrollEntry:
            self.radiatingTransform = Transform(name='pulse_circle_transform', parent=self, align=uiconst.CENTER)
            self.circle1 = Sprite(name='pulse_circle_1', parent=self.radiatingTransform, align=uiconst.CENTER, texturePath='res:/UI/Texture/classes/SensorSuite/PulseRing_Clean.png', pos=(0, 0, 125, 125), state=uiconst.UI_DISABLED, opacity=0.0)
            self.circle2 = Sprite(name='pulse_circle_2', parent=self.radiatingTransform, align=uiconst.CENTER, texturePath='res:/UI/Texture/classes/SensorSuite/PulseRing_Clean.png', pos=(0, 0, 175, 175), state=uiconst.UI_DISABLED, opacity=0.0)
        self.SetInnerColor(self.innerColor)
        self.SetOuterColor(self.outerColor)
        self.labelUpdateTimer = None
        self.lastRoundedDistance = None
        if self.isScrollEntry:
            self.UpdateLabel()

    def GetBracketLabelText(self):
        return self.data.GetName()

    @telemetry.ZONE_METHOD
    def UpdateLabel(self):
        if self.lastRoundedDistance is None:
            self.UpdateSiteLabel()
        try:
            distance = self.GetDistance()
            roundedDistance = RoundedDistance(distance)
            if self.lastRoundedDistance != roundedDistance:
                self.distanceLabel.SetText(FmtDist(distance, 1))
                self.lastRoundedDistance = roundedDistance
        except InvalidClientStateError:
            self.labelUpdateTimer = None

        totalLabelWidth = self.codeLabel.width + self.distanceLabel.width + DISTANCE_CELL_SPACING
        self.labelContainer.opacity = 1.0
        self.labelContainer.width = max(MIN_LABEL_SIZE, totalLabelWidth)

    def UpdateSiteName(self, text):
        self.siteName.SetText(text)

    @telemetry.ZONE_METHOD
    def UpdateSiteLabel(self):
        self.codeLabel.SetText(self.GetBracketLabelText())

    def SetInnerColor(self, color):
        self.icon.color = color

    def SetOuterColor(self, color):
        for sprite in self.outerSprites:
            sprite.color = color

    def AnimateFrameEnter(self, curveSet, timeOffset = 0.0, callback = None):
        moveDist = 40
        for index, (x, y) in enumerate(OUTER_BRACKET_ORIENTATIONS):
            sprite = self.outerSprites[index]
            curveSet = animations.MoveTo(sprite, startPos=((11 + moveDist) * x, (11 + moveDist) * y), endPos=(11 * x, 11 * y), duration=0.5, curveSet=curveSet, timeOffset=timeOffset)
            curveSet = animations.FadeTo(sprite, duration=0.8, curveType=OUTER_BRACKET_OPACITY_CURVE_POINTS, curveSet=curveSet, timeOffset=timeOffset, callback=callback)

    def AnimateCenterIcon(self, curveSet):
        animations.FadeTo(self.icon, loops=4, duration=0.2, startVal=self.iconOpacity, endVal=0.0, curveType=uiconst.ANIM_LINEAR, curveSet=curveSet)

    def AnimateEnableCenterIcon(self, curveSet):
        animations.FadeTo(self.icon, loops=4, duration=0.2, startVal=0.0, endVal=self.iconOpacity, curveType=uiconst.ANIM_LINEAR, curveSet=curveSet)

    def AnimateRadiatingCircles(self, curveSet, timeOffset = 0.0):
        if self.isScrollEntry:
            return
        circleTimeOffset = 0.15 + timeOffset
        radiationCycleDuration = 0.5
        self.radiatingTransform.display = True

        def CloseCircles():
            self.radiatingTransform.display = False

        animations.Tr2DScaleTo(self.radiatingTransform, startScale=(0.2, 0.2), endScale=(1.5, 1.5), duration=radiationCycleDuration + timeOffset, curveSet=curveSet, timeOffset=timeOffset)
        animations.FadeTo(self.circle1, curveType=RADIATING_CIRCLE_OPACITY_CURVE_POINTS, duration=radiationCycleDuration, curveSet=curveSet, timeOffset=timeOffset)
        animations.FadeTo(self.circle2, curveType=RADIATING_CIRCLE_OPACITY_CURVE_POINTS, duration=radiationCycleDuration, curveSet=curveSet, timeOffset=circleTimeOffset, callback=CloseCircles)

    def StartLabelUpdates(self):
        self.UpdateLabel()
        self.labelUpdateTimer = AutoTimer(500, self.UpdateLabel)

    def StopLabelUpdates(self):
        self.labelUpdateTimer = None

    def DoEntryAnimation(self, curveSet = None, enable = False):
        callback = self.DoEnableAnimation if enable else None
        self.AnimateCenterIcon(curveSet)
        self.AnimateRadiatingCircles(curveSet, timeOffset=0.2)
        self.AnimateFrameEnter(curveSet, timeOffset=1.0, callback=callback)
        return curveSet

    def DoExitAnimation(self, callback = None):
        curveSet = None
        duration = 0.5
        curveSet = animations.FadeTo(self.icon, duration=0.2, loops=3, startVal=self.iconOpacity, endVal=0.0, curveSet=curveSet)
        curveSet = animations.FadeTo(self.labelContainer, duration=0.2, loops=1, startVal=1.0, endVal=0.0, curveSet=curveSet, timeOffset=0.4)
        animations.FadeTo(self, startVal=self.opacity, endVal=0.0, duration=duration, curveSet=curveSet, timeOffset=0.6, callback=callback)
        self.StopLabelUpdates()

    def DoEnableAnimation(self):
        """
        animation when the bracket is enabled after the initial sweep
        """
        curveSet = None
        self.AnimateEnableCenterIcon(curveSet)

    def DoShowAnimation(self):
        """
        Animation then we show the icons
        """
        curveSet = None
        self.AnimateEnableCenterIcon(curveSet)
        self.AnimateRadiatingCircles(curveSet, timeOffset=0.2)
        self.AnimateFrameEnter(curveSet, timeOffset=1.0)
        return curveSet

    def OnDblClick(self, *args):
        scanSvc = sm.GetService('scanSvc')
        scanSvc.AlignToPosition(self.data.position)

    def OnClick(self, *args):
        sm.GetService('state').SetState(self.data.ballID, selected, 1)

    def OnMouseEnter(self, *args):
        self.labelContainer.display = True
        self.StartLabelUpdates()

    def OnMouseExit(self, *args):
        self.labelContainer.display = False
        self.StopLabelUpdates()

    def _OnClose(self, *args):
        self.StopLabelUpdates()

    def GetDistance(self):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            raise InvalidClientStateError('No longer have a ballpark.')
        ball = ballpark.GetBall(self.data.ballID)
        if ball is None:
            raise InvalidClientStateError('No longer have the ball in the ballpark')
        return ball.surfaceDist

    def OnMouseDown(self, *args):
        sm.GetService('menu').TryExpandActionMenu(None, self, siteData=self.data)

    def ShowRadialMenuIndicator(self, slimItem = None, *args):
        if not self.radialMenuSprite:
            self.radialMenuSprite = Sprite(name='radialMenuSprite', parent=self, texturePath='res:/UI/Texture/classes/RadialMenu/bracketHilite.png', pos=(0, 0, 20, 20), color=(0.5, 0.5, 0.5, 0.5), align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.radialMenuSprite.display = True

    def HideRadialMenuIndicator(self, slimItem = None, *args):
        if self.radialMenuSprite:
            self.radialMenuSprite.display = False
