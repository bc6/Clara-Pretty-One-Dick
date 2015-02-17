#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerSolarSystem.py
from carbon.common.script.util.commonutils import StripTags
from carbon.common.script.util.format import StrFromColor
from carbonui.primitives.base import ReverseScaleDpi, ScaleDpi
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.vectorlinetrace import DashedCircle
from carbonui.util.bunch import Bunch
from carbonui.util.color import Color
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase import MarkerBase
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Label import MarkerLabelBase
import carbonui.const as uiconst
import math
import trinity
from eve.common.script.util.eveFormat import FmtSystemSecStatus
from carbonui.uianimations import animations

class MarkerLabelSolarSystem(MarkerLabelBase):
    maxVisibleRange = 7500.0
    minVisibleRange = 50.0
    hilightContainer = None
    positionPickable = True
    extraInfo = None
    _cachedLabel = None

    def Load(self):
        self.isLoaded = True
        self.textLabel = EveLabelSmall(parent=self.markerContainer, text=self.GetLabelText(), bold=True, state=uiconst.UI_DISABLED)
        self.markerContainer.width = self.textLabel.textwidth
        self.markerContainer.height = self.textLabel.textheight
        self.projectBracket.offsetX = ScaleDpi(self.markerContainer.width * 0.5 + 10)
        self.UpdateActiveAndHilightState()

    def DestroyRenderObject(self):
        if self.textSprite:
            self.textSprite.fontMeasurer = None
        self.textSprite = None
        self.measurer = None
        MarkerBase.DestroyRenderObject(self)
        self.hilightContainer = None

    def GetLabelText(self):
        if self._cachedLabel is None:
            securityStatus, color = sm.GetService('map').GetSecurityStatus(self.markerID, True)
            self._cachedLabel = '%s <color=%s>%s</color>' % (cfg.evelocations.Get(self.markerID).name, Color.RGBtoHex(color.r, color.g, color.b), securityStatus)
        return self._cachedLabel

    def SetActiveState(self, activeState):
        oldState = self.activeState
        MarkerLabelBase.SetActiveState(self, activeState)
        if oldState != self.activeState:
            self.UpdateActiveAndHilightState()

    def SetHilightState(self, hilightState):
        oldState = self.hilightState
        MarkerLabelBase.SetHilightState(self, hilightState)
        if oldState != self.hilightState:
            self.UpdateActiveAndHilightState()

    def UpdateActiveAndHilightState(self):
        if self.hilightState or self.activeState:
            self.projectBracket.maxDispRange = 10000000.0
            if self.markerContainer:
                if not self.hilightContainer:
                    circleSize = 14
                    hilightContainer = Container(parent=self.markerContainer, align=uiconst.CENTERLEFT, pos=(-10 - circleSize / 2,
                     0,
                     circleSize,
                     circleSize))
                    DashedCircle(parent=hilightContainer, dashCount=4, lineWidth=0.8, radius=circleSize / 2, range=math.pi * 2)
                    self.hilightContainer = hilightContainer
                if self.hilightState:
                    if not self.extraInfo:
                        self.extraInfo = ExtraInfoContainer(parent=self.markerContainer.parent, text=self.GetExtraMouseOverInfo(), top=self.textLabel.textheight, idx=0)
                        self.extraContainer = self.extraInfo
                        self.UpdateExtraContainer()
                    else:
                        self.extraInfo.SetText(self.GetExtraMouseOverInfo())
                elif self.extraInfo:
                    self.extraContainer = None
                    self.extraInfo.Close()
                    self.extraInfo = None
        else:
            self.projectBracket.maxDispRange = self.maxVisibleRange
            if self.hilightContainer:
                self.hilightContainer.Close()
                self.hilightContainer = None
            if self.extraInfo:
                self.extraContainer = None
                self.extraInfo.Close()
                self.extraInfo = None
        self.lastUpdateCameraValues = None

    def GetDragData(self, *args):
        dragDisplayText, url = cfg.evelocations.Get(self.markerID).name, 'showinfo:%d//%d' % (const.typeSolarSystem, self.markerID)
        entry = Bunch()
        entry.__guid__ = 'TextLink'
        entry.url = url
        entry.dragDisplayText = dragDisplayText
        entry.displayText = StripTags(dragDisplayText)
        return [entry]


class ExtraInfoContainer(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_opacity = 0.0
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.label = EveLabelSmall(parent=self, text=attributes.text, bold=True, state=uiconst.UI_NORMAL, opacity=0.8)
        self.height = self.label.textheight
        self.width = self.label.textwidth
        animations.FadeTo(self, startVal=0.0, endVal=1.0, duration=0.1)
        animations.MorphScalar(self, 'displayWidth', 0, self.label.actualTextWidth, duration=0.2)

    def SetText(self, text):
        self.label.text = text
