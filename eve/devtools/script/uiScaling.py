#Embedded file name: eve/devtools/script\uiScaling.py
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import trinity

class UIScaling(uicontrols.Window):
    """ An Insider window which makes it easy test different UI Scaling options """
    __guid__ = 'form.UIScaling'
    default_windowID = 'UIScaling'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon(None)
        self.SetCaption('UI Scaling')
        self.SetTopparentHeight(0)
        self.SetMinSize([150, 100])
        mainCont = uiprimitives.Container(name='params', parent=self.sr.main, align=uiconst.TOALL, padding=const.defaultPadding)
        floats = (0.5, 2.0, 2)
        uicontrols.Label(text='use values from 0.5 to 2.0', parent=mainCont, align=uiconst.TOPLEFT)
        self.scaleEdit = uicontrols.SinglelineEdit(parent=mainCont, name='scaleEdit', align=uiconst.TOPLEFT, floats=floats, setvalue=uicore.desktop.dpiScaling, width=50, top=18)
        applyBtn = uicontrols.Button(parent=mainCont, name='apply', align=uiconst.TOPLEFT, label='Apply', left=54, top=18, func=self.ScaleUI)
        resetBtn = uicontrols.Button(parent=mainCont, name='reset', align=uiconst.TOPLEFT, label='Reset', left=0, top=40, func=self.ResetUI)

    def GetChange(self):
        scaleValue = self.scaleEdit.GetValue()
        oldHeight = int(trinity.device.height / uicore.desktop.dpiScaling)
        oldWidth = int(trinity.device.width / uicore.desktop.dpiScaling)
        newHeight = int(trinity.device.height / scaleValue)
        newWidth = int(trinity.device.width / scaleValue)
        changeDict = {}
        changeDict['ScalingWidth'] = (oldWidth, newWidth)
        changeDict['ScalingHeight'] = (oldHeight, newHeight)
        return (changeDict, True)

    def ResetUI(self, *args):
        self.scaleEdit.SetValue(1.0)
        change, canResize = self.GetChange()
        uicore.desktop.dpiScaling = 1.0
        sm.ScatterEvent('OnScalingChange', change)

    def ScaleUI(self, *args):
        scaleValue = self.scaleEdit.GetValue()
        change, canResize = self.GetChange()
        if not canResize:
            return
        uicore.desktop.dpiScaling = scaleValue
        sm.ScatterEvent('OnScalingChange', change)
