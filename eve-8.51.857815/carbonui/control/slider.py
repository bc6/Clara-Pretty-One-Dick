#Embedded file name: carbonui/control\slider.py
from eve.client.script.ui.control.eveWindowUnderlay import SpriteUnderlay
import mathUtil
import blue
import carbonui.const as uiconst
import fontConst
from carbonui.primitives.container import Container
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.util.various_unsorted import GetAttrs
from carbonui.control.label import LabelOverride as Label
from carbonui.primitives.frame import FrameCoreOverride as Frame

class Slider(Container):
    __guid__ = 'uicls.Slider'
    default_name = 'slider'
    default_align = uiconst.TOTOP
    default_height = 16
    default_barHeight = 6
    default_barPadding = 5
    default_sliderID = ''
    default_minValue = 0.0
    default_maxValue = 1.0
    default_config = ''
    default_displayName = ''
    default_increments = []
    default_getvaluefunc = None
    default_setlabelfunc = None
    default_endsliderfunc = None
    default_onsetvaluefunc = None
    default_startVal = None
    default_labeltab = 4
    default_showValueInLabel = True
    default_showLabel = True
    default_fontsize = None
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        if self.default_fontsize is None:
            self.default_fontsize = fontConst.DEFAULT_FONTSIZE
        self.value = None
        self.label = None
        self.top = 0
        self.dragging = 0
        self.handle = None
        self.handleOffset = 0
        self.increments = []
        increments = attributes.get('increments', self.default_increments)
        self.displayName = attributes.get('displayName', self.default_displayName)
        self.config = attributes.get('config', self.default_config)
        self.isEvenIncrementsSlider = attributes.get('isEvenIncrementsSlider', False) and bool(increments)
        self.startVal = attributes.get('startVal', self.default_startVal)
        self.maxValue = attributes.get('maxValue', self.default_maxValue)
        self.minValue = attributes.get('minValue', self.default_minValue)
        self.sliderID = attributes.get('sliderID', self.default_sliderID)
        self.barHeight = attributes.get('barHeight', self.default_barHeight)
        self.barPadding = attributes.get('barPadding', self.default_barPadding)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.labeltab = attributes.get('labeltab', self.default_labeltab)
        self.SetSliderLabel = attributes.get('setlabelfunc', self.default_setlabelfunc)
        self.GetSliderValue = attributes.get('getvaluefunc', self.default_getvaluefunc)
        self.EndSetSliderValue = attributes.get('endsliderfunc', self.default_endsliderfunc)
        self.OnSetValue = attributes.get('onsetvaluefunc', self.default_onsetvaluefunc)
        self.showLabel = attributes.get('showLabel', self.default_showLabel)
        self.showValueInLabel = attributes.get('showValueInLabel', self.default_showValueInLabel)
        self.Prepare_Underlay_()
        self.Prepare_Handle_()
        self.Prepare_Label_()
        self.Prepare_Increments_()
        self.SetIncrements(increments)
        if self.config:
            if len(self.config) == 3:
                cfgName, prefsType, defaultValue = self.config
                if prefsType is not None:
                    si = GetAttrs(settings, *prefsType)
                    if si:
                        value = si.Get(cfgName, defaultValue)
                    else:
                        value = defaultValue
                else:
                    value = defaultValue
                self.name = self.config[0]
            else:
                value = settings.user.ui.Get(self.config, (self.maxValue - self.minValue) * 0.5)
                if value is None:
                    value = 0.0
                self.name = self.config
            self.SetValue(value, updateHandle=True)
        elif self.startVal is not None:
            self.SetValue(self.startVal, updateHandle=True)
        else:
            self.state = uiconst.UI_NORMAL

    def Prepare_Underlay_(self):
        self.barCont = Container(parent=self, name='barCont', align=uiconst.TOBOTTOM, state=uiconst.UI_NORMAL, hint=self.hint, height=self.barHeight + 2 * self.barPadding)
        self.barCont.ticks = []
        self.frame = Frame(parent=self.barCont, name='barFrame', align=uiconst.TOALL, padding=(0,
         self.barPadding,
         0,
         self.barPadding), color=(0.2, 0.2, 0.2, 1.0), state=uiconst.UI_DISABLED, hint=self.hint)
        self.barCont.OnClick = self.OnSliderClicked
        self.barCont.OnMouseMove = self.OnSliderMouseMove
        self.barCont.OnMouseExit = self.OnMouseBarExit
        self.barCont.OnMouseWheel = self.OnMouseWheel

    def OnSliderClicked(self, *args):
        localMousePos, newValue = self.FindNewValue()
        self.SetValue(newValue, updateHandle=True)
        if self.EndSetSliderValue:
            self.EndSetSliderValue(self)

    def OnSliderMouseMove(self, *args):
        if not self.increments:
            return
        mousePos, value = self.FindNewValue()
        if value not in self.increments[0] or not self.barCont.ticks:
            return
        valueIndex = self.increments[0].index(value)
        self.ColorTicks(valueIndex)

    def ColorTicks(self, valueIndex):
        for i, tick in enumerate(self.barCont.ticks):
            if i == valueIndex:
                alpha = 0.5
            else:
                alpha = 0.25
            tick.color.a = alpha

    def Prepare_Handle_(self):
        self.handleOffset = 2
        self.handle = SpriteUnderlay(name='diode', parent=self.barCont, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, pos=(-self.handleOffset,
         0,
         12,
         12), idx=0, texturePath='res:/UI/Texture/classes/Slider/handle.png')
        self.handle.OnMouseEnter = self.OnHandleMouseEnter
        self.handle.OnMouseExit = self.OnHandleMouseExit
        self.handle.OnMouseDown = self.OnHandleMouseDown
        self.handle.OnMouseUp = self.OnHandleMouseUp
        self.handle.OnMouseMove = self.OnHandleMouseMove

    def Prepare_Label_(self):
        if self.showLabel:
            self.label = Label(parent=self, fontsize=self.fontsize, pos=(self.labeltab,
             13,
             0,
             0), state=uiconst.UI_NORMAL, hint=self.hint)

    def Prepare_Increments_(self):
        for each in self.children[:]:
            if each.name.startswith('tickLine'):
                each.Close()

        if self.increments and getattr(self, 'barCont', None):
            w, _ = self.GetAbsoluteSize()
            maxX = self.GetMaxX()
            ticks = []
            for i, each in enumerate(self.increments[1]):
                padding = self.barPadding + 2
                if i in (0, len(self.increments[1]) - 1):
                    padding -= 1
                left = int(each * maxX) + self.GetHandleWidth() / 2
                line = Line(parent=self.barCont, name='tickLine', align=uiconst.TOLEFT_NOPUSH, padding=(left,
                 padding,
                 0,
                 padding), opacity=0.2, idx=0)
                ticks.append(line)

            self.barCont.ticks = ticks

    def SetIncrements(self, increments, draw = 1):
        if len(increments) < 3:
            return
        self.increments = [[], []]
        numIncrements = len(increments)
        for idx, inc in enumerate(increments):
            self.increments[0].append(inc)
            value = self.GetIncrementValue(idx, inc, numIncrements)
            self.increments[1].append(value)

        if draw:
            self.Prepare_Increments_()

    def GetIncrementValue(self, idx, inc, numIncrements):
        if self.isEvenIncrementsSlider:
            part = 1.0 / (numIncrements - 1)
            return idx * part
        else:
            return (inc - self.minValue) / float(self.maxValue - self.minValue)

    def GetValue(self):
        return self.value

    def MorphTo(self, value, time = 150.0):
        if getattr(self, 'morphTo', None) is not None:
            self.pendingMorph = (value, time)
            return
        self.morphTo = value
        startPos = self.value
        endPos = value
        start, ndt = blue.os.GetWallclockTime(), 0.0
        while ndt != 1.0:
            ndt = min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / time, 1.0)
            newVal = mathUtil.Lerp(startPos, endPos, ndt)
            self.SetValue(newVal, updateHandle=True)
            blue.pyos.synchro.Yield()

        self.morphTo = None
        if getattr(self, 'pendingMorph', None):
            value, time = self.pendingMorph
            self.MorphTo(value, time)
        self.pendingMorph = None

    def SlideTo(self, value, update = 1):
        print 'not supported, pass updateHandle=True into SetValue instead'

    def UpdateHandle(self, nValue, useIncrements = True):
        maxX = self.GetMaxX()
        leftPercentage = max(0, nValue)
        if self.increments and useIncrements:
            leftPercentage = self.FindClosest(leftPercentage, self.increments[1])
        left = leftPercentage * maxX
        self.handle.left = int(left) - self.handleOffset
        self.handle.state = uiconst.UI_NORMAL

    def SetValue(self, value, updateHandle = False, useIncrements = True, triggerCallback = True):
        if self.increments and useIncrements:
            value = self.FindClosest(self.RoundValue(value), self.increments[0])
        value = max(self.minValue, min(self.maxValue, value))
        normalizedValue = self.GetNormalizedValue(value)
        self.value = value
        if self.GetSliderValue:
            self.GetSliderValue(self.sliderID, value)
        self.UpdateLabel()
        if updateHandle:
            self.UpdateHandle(normalizedValue, useIncrements=useIncrements)
        if self.OnSetValue and triggerCallback:
            self.OnSetValue(self)

    def GetNormalizedValue(self, value):
        if self.isEvenIncrementsSlider:
            valueIndex = self.increments[0].index(value)
            percentage = self.increments[1][valueIndex]
            return percentage
        else:
            return float(value - self.minValue) / (-self.minValue + self.maxValue)

    def RoundValue(self, value):
        return float('%.2f' % value)

    def FindClosest(self, check, values):
        mindiff = values[-1] - values[0]
        found = mindiff
        for value in values:
            diff = abs(value - check)
            if diff < mindiff:
                mindiff = diff
                found = value

        return found

    def UpdateLabel(self):
        if self.label:
            if self.SetSliderLabel:
                self.SetSliderLabel(self.label, self.sliderID, self.displayName, self.GetValue())
            elif self.showValueInLabel:
                if self.displayName:
                    self.label.text = '%s %.2f' % (self.displayName, self.GetValue())
                else:
                    self.label.text = '%.2f' % self.GetValue()
            else:
                self.label.text = self.displayName

    def OnMouseWheel(self, delta, *args):
        if not self.increments:
            return
        currentValue = self.GetValue()
        if delta < 0:
            if currentValue <= self.increments[0][0]:
                return
            newValue = max((x for x in self.increments[0] if x < currentValue))
        else:
            if currentValue >= self.increments[0][-1]:
                return
            newValue = min((x for x in self.increments[0] if x > currentValue))
        self.SetValue(newValue, updateHandle=True)
        if self.EndSetSliderValue:
            self.EndSetSliderValue(self)

    def OnMouseBarExit(self):
        self.ColorTicks(-1)

    def OnHandleMouseEnter(self, *args):
        uicore.animations.FadeTo(self.handle, self.handle.opacity, 1.3, duration=0.1)

    def OnHandleMouseExit(self, *args):
        uicore.animations.FadeTo(self.handle, self.handle.opacity, 1.0, duration=0.3)

    def OnHandleMouseDown(self, *args):
        self.dragging = 1
        self.ColorTicks(-1)

    def OnHandleMouseUp(self, *args):
        uicore.uilib.UnclipCursor()
        self.dragging = 0
        if self.config:
            if len(self.config) == 3:
                cfgName, prefsType, defaultValue = self.config
                if prefsType:
                    si = GetAttrs(settings, *prefsType)
                    if si:
                        value = si.Set(cfgName, self.value)
            settings.user.ui.Set(self.config, self.value)
        if self.EndSetSliderValue:
            self.EndSetSliderValue(self)

    def OnHandleMouseMove(self, *args):
        if self.dragging:
            localMousePos, value = self.FindNewValue()
            if self.handle.left + self.handleOffset == localMousePos:
                return
            self.handle.left = localMousePos - self.handleOffset
            maxX = self.GetMaxX()
            self.SetValue(value)

    def FindNewValue(self):
        l, _, w, _ = self.GetAbsolute()
        hw = self.GetHandleWidth()
        maxX = self.GetMaxX()
        localMousePos = uicore.uilib.x - l - hw / 2
        localMousePos = max(0, min(maxX, localMousePos))
        localMousePercentagePos = min(1, max(0, float(localMousePos) / maxX))
        if self.isEvenIncrementsSlider:
            numIncrements = len(self.increments[1])
            eachStep = float(maxX) / (numIncrements - 1)
            localMousePercentagePos = self.FindClosest(localMousePercentagePos, self.increments[1])
            partIndex = self.increments[1].index(localMousePercentagePos)
            localMousePos = partIndex * eachStep
            value = self.increments[0][partIndex]
        else:
            if self.increments:
                localMousePercentagePos = self.FindClosest(localMousePercentagePos, self.increments[1])
                localMousePos = localMousePercentagePos * maxX
            value = self.minValue + localMousePercentagePos * (self.maxValue - self.minValue)
        return (localMousePos, value)

    def GetMaxX(self):
        w, _ = self.GetAbsoluteSize()
        maxX = w - self.GetHandleWidth()
        return maxX

    def GetHandleWidth(self):
        return self.handle.width - 2 * self.handleOffset
