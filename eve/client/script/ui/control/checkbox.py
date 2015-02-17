#Embedded file name: eve/client/script/ui/control\checkbox.py
from carbonui.control.checkbox import CheckboxCore
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveWindowUnderlay import CheckboxUnderlay, RadioButtonUnderlay
import uiprimitives
import uiutil
import carbonui.const as uiconst
TOPMARGIN = 3

class Checkbox(CheckboxCore):
    __guid__ = 'uicontrols.Checkbox'
    default_height = 100
    default_prefstype = ('user', 'ui')

    def ApplyAttributes(self, attributes):
        CheckboxCore.ApplyAttributes(self, attributes)
        self.prefstype = attributes.get('prefstype', self.default_prefstype)
        if self.prefstype == 1:
            self.prefstype = ('char', 'ui')
        elif self.prefstype == 2:
            self.prefstype = 'prefs'

    def __getattr__(self, k):
        if k == 'groupName' and self.__dict__.has_key('_groupName'):
            return self.__dict__['_groupName']
        if k == 'checked' and self.__dict__.has_key('_checked'):
            return self.__dict__['_checked']
        return CheckboxCore.__getattr__(self, k)

    def Prepare_Label_(self):
        if self.GetAlign() == uiconst.TOPRIGHT:
            leftPad = 0
            rightPad = 16
        else:
            leftPad = 16
            rightPad = 0
        if not self.wrapLabel:
            align = uiconst.CENTERLEFT
            padding = 0
            pos = (leftPad,
             0,
             0,
             0)
            maxLines = 1
        else:
            align = uiconst.TOTOP
            padding = (leftPad,
             TOPMARGIN,
             rightPad,
             0)
            pos = (0, 0, 0, 0)
            maxLines = None
        self.sr.label = EveLabelSmall(text='', parent=self, name='text', align=align, state=uiconst.UI_DISABLED, padding=padding, pos=pos, maxLines=maxLines)
        self.sr.label.OnSizeChanged = self.OnSizeChanged

    def Prepare_Diode_(self):
        if self.sr.diode:
            self.sr.diode.Close()
        self.sr.diode = uiprimitives.Container(parent=self, pos=(-1, 1, 16, 16), name='diode', state=uiconst.UI_DISABLED, align=uiconst.RELATIVE)
        if self._groupName is None:
            self.sr.active = uiprimitives.Sprite(parent=self.sr.diode, pos=(0, 0, 16, 16), name='active', state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/Shared/checkboxActive.png', opacity=0.1)
            self.checkMark = uiprimitives.Sprite(parent=self.sr.diode, pos=(0, 0, 16, 16), name='self_ok', state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/Shared/checkboxChecked.png')
            self.underlay = CheckboxUnderlay(parent=self.sr.diode, padding=2)
        else:
            self.sr.active = uiprimitives.Sprite(parent=self.sr.diode, pos=(1, 1, 14, 14), name='active', state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/RadioButton/frame.png', opacity=0.1)
            self.checkMark = uiprimitives.Sprite(parent=self.sr.diode, pos=(1, 1, 14, 14), name='self_ok', state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/RadioButton/selected.png')
            self.underlay = RadioButtonUnderlay(parent=self.sr.diode, padding=2)

    def Prepare_Active_(self):
        pass

    def SetChecked(self, onoff, report = 1):
        onoff = onoff or 0
        self._checked = int(onoff)
        if self.sr.diode is None:
            self.Prepare_Diode_()
        self.checkMark.state = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED][self._checked]
        if report:
            self.UpdateSettings()
            if self.OnChange:
                self.OnChange(self)
        if onoff:
            self.underlay.Select(animate=report)
        else:
            self.underlay.Deselect(animate=report)

    def ToggleState(self, *args):
        if not self or self.destroyed:
            return
        if self._checked:
            uicore.Message('DiodeDeselect')
        else:
            uicore.Message('DiodeClick')
        CheckboxCore.ToggleState(self, *args)

    def RefreshHeight(self):
        label = uiutil.GetChild(self, 'text')
        minHeight = 12
        if self.sr.diode:
            minHeight = 18
        self.height = max(minHeight, label.textheight + TOPMARGIN * 2)

    def SetLabel(self, labeltext):
        self.SetLabelText(labeltext)

    def GetTooltipPosition(self, *args, **kwds):
        l, t, w, h = self.GetAbsolute()
        label = self.sr.label
        if label.text:
            return (l,
             t,
             label.padLeft + label.left + label.textwidth,
             h)
        else:
            return (l,
             t,
             w,
             h)

    def OnMouseEnter(self, *args):
        self.underlay.OnMouseEnter()

    def OnMouseExit(self, *args):
        self.underlay.OnMouseExit()

    def OnMouseDown(self, *args):
        CheckboxCore.OnMouseDown(self, *args)
        self.underlay.OnMouseDown()

    def OnMouseUp(self, *args):
        CheckboxCore.OnMouseUp(self, *args)
        self.underlay.OnMouseUp()


from carbonui.control.checkbox import CheckboxCoreOverride
CheckboxCoreOverride.__bases__ = (Checkbox,)
