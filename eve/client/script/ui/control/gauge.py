#Embedded file name: eve/client/script/ui/control\gauge.py
"""
Horizontal analog gauges that can be used to represent analog values.
"""
from math import pi
from carbonui.const import TOLEFT_PROP, TOPRIGHT, TOPLEFT
import carbonui.const as uiconst
from carbonui.primitives.containerAutoSize import ContainerAutoSize
import uiprimitives
import uicontrols
import util
import uthread

class _GaugeBase(ContainerAutoSize):
    """
    A base class that gauges derive from
    """
    __guid__ = 'uicls._GaugeBase'
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_alignMode = uiconst.TOTOP
    default_width = 100
    default_height = 30
    default_gaugeHeight = 6
    default_label = ''
    default_subText = ''
    default_gradientBrightnessFactor = 2.0

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        labelTxt = attributes.Get('label', self.default_label)
        subTxt = attributes.Get('subText', self.default_subText)
        gaugeHeight = attributes.Get('gaugeHeight', self.default_gaugeHeight)
        self.gradientBrightnessFactor = attributes.Get('gradientBrightnessFactor', self.default_gradientBrightnessFactor)
        self.markers = {}
        self.gaugeCont = uiprimitives.Container(parent=self, name='gaugeCont', height=gaugeHeight, align=uiconst.TOTOP, clipChildren=True, state=uiconst.UI_DISABLED)
        self.label = None
        if labelTxt:
            self.SetText(labelTxt)
        self.subText = None
        if subTxt:
            self.SetSubText(subTxt)

    def _SetValue(self, gauge, value, frequency, animate):
        if animate:
            uicore.animations.MorphScalar(gauge, 'width', gauge.width, value)
        else:
            gauge.width = value
        self.value = value

    def ShowMarker(self, value, width = 1, color = util.Color.WHITE):
        """
        Show a marker at the position defined by value [0.0-1.0]
        Overrides any marker that might already exist at the position.
        """
        self.HideMarker(value)
        left = int(self.width * value)
        marker = uiprimitives.Fill(parent=self.gaugeCont, name='marker', color=color, align=uiconst.TOPLEFT_PROP, pos=(value,
         0,
         width,
         self.gaugeCont.height), state=uiconst.UI_DISABLED, idx=0)
        self.markers[value] = marker

    def ShowMarkers(self, values, width = 1, color = util.Color.WHITE):
        """ 
        Show multiple markers defined by the list of values on the range [0.0-1.0]
        """
        for value in values:
            self.ShowMarker(value, width, color)

    def HideMarker(self, value):
        """
        Hide the marker at the position defined by value (if it exists)
        """
        if value in self.markers:
            self.markers[value].Close()
            self.markers.pop(value)

    def HideAllMarkers(self):
        for marker in self.markers.values():
            marker.Close()

        self.markers = {}

    def SetSubText(self, text):
        if not self.subText:
            self.subText = uicontrols.EveLabelSmall(parent=self, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, maxLines=1, padTop=1)
        self.subText.text = text

    def SetText(self, text):
        if not self.label:
            self.label = uicontrols.EveLabelSmallBold(parent=self, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, maxLines=1, padBottom=1, idx=0)
        self.label.text = text

    def _CreateGradient(self, parent, color):
        colBase = util.Color(*color).GetRGB()
        colBright = util.Color(*color)
        colBright = colBright.SetBrightness(min(1.0, self.gradientBrightnessFactor * colBright.GetBrightness())).GetRGB()
        return uicontrols.GradientSprite(align=uiconst.TOALL, parent=parent, rotation=-pi / 2, rgbData=[(0, colBright), (0.5, colBase), (1.0, colBase)], alphaData=[(0, 1.0)])


class Gauge(_GaugeBase):
    """
    A class representing a horizontal analog gauge
    """
    __guid__ = 'uicls.Gauge'
    default_name = 'Gauge'
    default_value = 0.0
    default_backgroundColor = None
    default_cyclic = False
    default_color = util.Color.WHITE
    default_gaugeAlign = TOLEFT_PROP

    def ApplyAttributes(self, attributes):
        _GaugeBase.ApplyAttributes(self, attributes)
        self.color = attributes.Get('color', self.default_color)
        backgroundColor = attributes.Get('backgroundColor', self.default_backgroundColor)
        self.value = attributes.Get('value', self.default_value)
        self.cyclic = attributes.Get('cyclic', self.default_cyclic)
        gaugeAlign = attributes.Get('gaugeAlign', self.default_gaugeAlign)
        self.gauge = uiprimitives.Container(parent=self.gaugeCont, name='gauge', align=gaugeAlign, clipChildren=True, width=0.0, state=uiconst.UI_DISABLED)
        self.gaugeGradient = self._CreateGradient(parent=self.gauge, color=self.color)
        self.flashGradient = None
        if backgroundColor is None:
            backgroundColor = util.Color(*self.color).SetAlpha(0.2).GetRGBA()
        self.sr.backgroundFill = uiprimitives.Fill(bgParent=self.gaugeCont, name='background', color=backgroundColor)
        self.SetValueInstantly(self.value)

    def SetGaugeAlign(self, align):
        self.gauge.align = align

    def SetValue(self, value, frequency = 10.0, animate = True, timeOffset = 0.0):
        if self.value == value:
            return
        if self.cyclic and self.value > value:
            self.SetValueInstantly(value)
        else:
            if animate:
                self.AnimFlash(value - self.value, timeOffset)
            self._SetValue(self.gauge, value, frequency, animate)

    def SetValueText(self, text):
        if getattr(self, 'valueText', None) is None:
            self.valueText = uicontrols.EveLabelSmall(parent=self.gaugeCont, align=uiconst.CENTER, state=uiconst.UI_DISABLED, idx=0)
        if self.valueText.text != text:
            self.valueText.text = text

    def SetColor(self, color, animDuration = None):
        if color == self.color:
            return
        self.color = color
        if self.gaugeGradient:
            if animDuration:
                uicore.animations.FadeOut(self.gaugeGradient, duration=animDuration, callback=self.gaugeGradient.Close)
            else:
                self.gaugeGradient.Close()
        self.gaugeGradient = self._CreateGradient(self.gauge, color)
        if animDuration:
            uicore.animations.FadeTo(self.gaugeGradient, 0.0, self.gaugeGradient.opacity, duration=animDuration)

    def SetBackgroundColor(self, color):
        adjustedColor = util.Color(*color).SetAlpha(0.2).GetRGBA()
        self.sr.backgroundFill.color = adjustedColor

    def SetValueInstantly(self, value):
        self.value = value
        self.gauge.width = value
        self.gauge.StopAnimations()

    def AnimFlash(self, diff, duration = 1.6, timeOffset = 0.0):
        uthread.new(self._AnimFlash, diff, duration, timeOffset)

    def _AnimFlash(self, diff, duration, timeOffset):
        w, h = self.gaugeCont.GetAbsoluteSize()
        align = TOPLEFT if self.gauge.align == TOLEFT_PROP else TOPRIGHT
        if not self.flashGradient:
            self.flashGradient = uicontrols.GradientSprite(parent=self.gauge, idx=0, name='flashGradient', align=align, width=w, height=h, rgbData=[(0, (0.99, 1.0, 1.0))], alphaData=[(0, 0.0), (0.9, 0.5), (1.0, 0.0)])
        self.flashGradient.opacity = 1.0
        if diff > 0:
            self.flashGradient.rotation = 0
            uicore.animations.MorphScalar(self.flashGradient, 'left', -w, w, duration - 0.4, timeOffset=timeOffset)
        else:
            self.flashGradient.rotation = pi
            uicore.animations.MorphScalar(self.flashGradient, 'left', w, -w, duration - 0.4, timeOffset=timeOffset)
        uicore.animations.FadeOut(self.flashGradient, duration=duration, timeOffset=timeOffset)


class GaugeMultiValue(_GaugeBase):
    """
    A class representing a horizontal analog with multiple values
    """
    __guid__ = 'uicls.GaugeMultiValue'
    default_name = 'GaugeMultiValue'
    default_backgroundColor = (1.0, 1.0, 1.0, 0.2)
    default_colors = []

    def ApplyAttributes(self, attributes):
        _GaugeBase.ApplyAttributes(self, attributes)
        colors = attributes.Get('colors', self.default_colors)
        values = attributes.Get('values', [])
        backgroundColor = attributes.Get('backgroundColor', self.default_backgroundColor)
        numGauges = len(colors)
        self.gauges = []
        for gaugeNum in xrange(numGauges):
            layer = uiprimitives.Container(parent=self.gaugeCont, name='layer')
            gauge = uiprimitives.Container(parent=layer, name='gaugeCont%s' % gaugeNum, align=uiconst.TOLEFT_PROP)
            self._CreateGradient(gauge, color=colors[gaugeNum])
            self.gauges.append(gauge)

        uiprimitives.Fill(bgParent=self.gaugeCont, name='background', color=backgroundColor)
        for gaugeNum, value in enumerate(values):
            self.SetValueInstantly(gaugeNum, value)

    def SetValue(self, gaugeNum, value, frequency = 10.0, animate = True):
        self._SetValue(self.gauges[gaugeNum], value, frequency, animate)

    def SetValueInstantly(self, gaugeNum, value):
        self.gauges[gaugeNum].width = value
