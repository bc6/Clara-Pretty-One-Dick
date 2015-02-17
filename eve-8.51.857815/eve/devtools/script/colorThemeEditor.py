#Embedded file name: eve/devtools/script\colorThemeEditor.py
from carbonui.control.slider import Slider
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.util.color import Color
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveWindow import Window
import carbonui.const as uiconst
import blue
from eve.client.script.ui.control.eveWindowUnderlay import LineUnderlay

class ColorThemeEditor(Window):
    __notifyevents__ = ['OnUIColorsChanged']
    default_caption = 'Color Theme Editor'
    default_windowID = 'ColorThemeEditorID'
    default_width = 600
    default_height = 400
    default_topParentHeight = 0
    default_minSize = (600, 490)

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.baseColorPicker = ColorPicker(parent=self.sr.main, align=uiconst.TOTOP, label='Base Color', colorCallback=self.OnBaseColor, padding=(8, 4, 4, 20), color=sm.GetService('uiColor').GetUIColor(uiconst.COLORTYPE_UIBASE), maxValue=0.3)
        LineUnderlay(parent=self.sr.main, align=uiconst.TOTOP)
        self.hiliteColorPicker = ColorPicker(parent=self.sr.main, align=uiconst.TOTOP, label='Hilite Color', colorCallback=self.OnHiliteColor, padding=(8, 20, 4, 4), color=sm.GetService('uiColor').GetUIColor(uiconst.COLORTYPE_UIHILIGHT))

    def OnBaseColor(self, color, *args):
        sm.GetService('uiColor').SetBaseColor(color)

    def OnHiliteColor(self, color, *args):
        sm.GetService('uiColor').SetHilightColor(color)

    def OnUIColorsChanged(self):
        self.baseColorPicker.UpdateColor(sm.GetService('uiColor').GetUIColor(uiconst.COLORTYPE_UIBASE))
        self.hiliteColorPicker.UpdateColor(sm.GetService('uiColor').GetUIColor(uiconst.COLORTYPE_UIHILIGHT))


PADTOP = 8

class ColorPicker(ContainerAutoSize):
    default_name = 'ColorPicker'
    default_alignMode = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        label = attributes.label
        maxValue = attributes.Get('maxValue', 1.0)
        self.colorCallback = attributes.colorCallback
        self.color = Color(*attributes.color)
        self.initialized = False
        Label(parent=self, align=uiconst.TOTOP, text=label, fontsize=20, left=14)
        Button(parent=self, left=4, top=4, align=uiconst.TOPRIGHT, label='Copy to Clipboard', func=self.CopyToClipboard)
        self.r = ValueSelector(parent=self, align=uiconst.TOTOP, height=18, value=self.color.r, maxValue=maxValue, label='R', callback=self.OnRChange)
        self.g = ValueSelector(parent=self, align=uiconst.TOTOP, height=18, value=self.color.g, maxValue=maxValue, label='G', callback=self.OnGChange, padTop=PADTOP)
        self.b = ValueSelector(parent=self, align=uiconst.TOTOP, height=18, value=self.color.b, maxValue=maxValue, label='B', callback=self.OnBChange, padTop=PADTOP)
        h, s, b = self.color.GetHSB()
        self.h = ValueSelector(parent=self, align=uiconst.TOTOP, height=18, value=h, maxValue=1.0, label='H', callback=self.OnHChange, padTop=PADTOP + 14)
        self.s = ValueSelector(parent=self, align=uiconst.TOTOP, height=18, value=s, maxValue=1.0, label='S', callback=self.OnSChange, padTop=PADTOP)
        self.br = ValueSelector(parent=self, align=uiconst.TOTOP, height=18, value=b, maxValue=maxValue, label='B', callback=self.OnBrChange, padTop=PADTOP)
        self.initialized = True

    def UpdateColor(self, color):
        self.color.SetRGB(*color)
        self.UpdateSliders()

    def UpdateSliders(self):
        self.r.SetValue(self.color.r)
        self.g.SetValue(self.color.g)
        self.b.SetValue(self.color.b)
        h, s, br = self.color.GetHSB()
        self.h.SetValue(h)
        self.s.SetValue(s)
        self.br.SetValue(br)

    def UpdateValues(self):
        if not self.initialized:
            return
        self.UpdateSliders()
        self.colorCallback(self.color.GetRGBA())

    def OnRChange(self, slider):
        self.color.SetRGB(slider.GetValue(), self.color.g, self.color.b)
        self.UpdateValues()

    def OnGChange(self, slider):
        self.color.SetRGB(self.color.r, slider.GetValue(), self.color.b)
        self.UpdateValues()

    def OnBChange(self, slider):
        self.color.SetRGB(self.color.r, self.color.g, slider.GetValue())
        self.UpdateValues()

    def OnHChange(self, slider):
        self.color.SetHue(slider.GetValue())
        self.UpdateValues()

    def OnSChange(self, slider):
        self.color.SetSaturation(slider.GetValue())
        self.UpdateValues()

    def OnBrChange(self, slider):
        self.color.SetBrightness(slider.GetValue())
        self.UpdateValues()

    def CopyToClipboard(self, *args):
        data = '(%s, %s, %s)' % self.color.GetRGBRounded()
        blue.win32.SetClipboardData(data)


class ValueSelector(Container):
    default_name = 'ValueSelector'

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        label = attributes.label
        value = attributes.value
        maxValue = attributes.maxValue
        callback = attributes.callback
        Label(parent=self, align=uiconst.TOLEFT, width=10, text=label, fontsize=15, top=-3)
        self.slider = Slider(parent=self, align=uiconst.TOLEFT_PROP, width=0.95, padLeft=3, minValue=0.0, maxValue=maxValue, startVal=value, onsetvaluefunc=callback)

    def SetValue(self, value):
        self.slider.SetValue(value, updateHandle=True, triggerCallback=False)
