#Embedded file name: eve/client/script/ui/control\labelEditable.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit

class LabelEditable(Container):
    default_height = 40
    default_width = 100
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_PICKCHILDREN

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.defaultText = attributes.get('defaultText', None)
        self.currentText = attributes['text']
        hint = attributes.get('hint', None)
        self.configName = attributes['configName']
        self.maxLength = attributes.get('maxLength', None)
        self.minLength = attributes.get('minLength', None)
        self.editField = SinglelineEdit(name='editField', parent=self, align=uiconst.CENTERLEFT, pos=(0, 0, 100, 0), setvalue=self.currentText, OnFocusLost=self.OnEditFieldLostFocus, OnChange=self.OnEditFieldChanged, OnReturn=self.OnEditFieldLostFocus, maxLength=self.maxLength)
        self.editField.display = False
        self.textLabel = Label(name='textLabel', parent=self, left=SinglelineEdit.TEXTLEFTMARGIN + self.editField._textClipper.padLeft, state=uiconst.UI_NORMAL, maxLines=1, align=uiconst.CENTERLEFT, fontsize=self.editField.sr.text.fontsize, text=self.currentText)
        self.textLabel.color.SetRGBA(1.0, 1.0, 1.0, 1.0)
        self.textLabel.cursor = uiconst.UICURSOR_IBEAM
        self.editField.width = self.textLabel.textwidth + 20
        self.width = self.editField.width
        self.height = self.editField.height
        self.textLabel.OnClick = self.OnLabelClicked
        if hint:
            self.textLabel.hint = hint

    def OnLabelClicked(self, *args):
        self.textLabel.display = False
        self.editField.display = True
        uicore.registry.SetFocus(self.editField)

    def OnEditFieldLostFocus(self, *args):
        currentText = self.currentText
        if self.minLength and len(currentText) < self.minLength and self.defaultText:
            currentText = self.defaultText
            self.SetValue(currentText)
        self.textLabel.display = True
        self.editField.display = False
        settings.user.ui.Set(self.configName, currentText)

    def OnEditFieldChanged(self, *args):
        self.currentText = self.editField.GetValue()
        self.textLabel.text = self.currentText
        self.editField.width = self.editField.sr.text.textwidth + 20
        self.width = self.editField.width

    def GetValue(self):
        return self.currentText.strip()

    def SetValue(self, text):
        self.currentText = text
        self.textLabel.text = self.currentText
        self.editField.SetText(text)
        self.OnEditFieldChanged()
