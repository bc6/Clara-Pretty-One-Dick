#Embedded file name: eve/client/script/ui/shared/info/panels\panelNotes.py
from carbonui.primitives.container import Container
import uthread
import uiutil
from eve.client.script.ui.control.eveEditPlainText import EditPlainText
import const
import carbonui.const as uiconst

class PanelNotes(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.infoType = attributes.infoType
        self.itemID = attributes.itemID
        self.initialized = False
        self.oldText = None
        self.edit = EditPlainText(parent=self, padding=const.defaultPadding, align=uiconst.TOALL, maxLength=5000, showattributepanel=True)

    def Close(self, *args):
        self.SaveNote()
        Container.Close(self)

    def Load(self):
        if self.initialized:
            return
        self.initialized = True
        text = ''
        if self.itemID:
            text = sm.RemoteSvc('charMgr').GetNote(self.itemID)
        self.edit.SetValue(text, scrolltotop=1)
        self.oldText = text

    def SaveNote(self, closing = 0, *args):
        if not self.itemID:
            return
        if self.oldText is None:
            return
        text = self.edit.GetValue()
        if text is None:
            return
        toSave = None
        if len(uiutil.StripTags(text)):
            if self.oldText != text:
                toSave = text[:5000]
        elif self.oldText:
            toSave = ''
        if toSave is not None:
            uthread.new(sm.RemoteSvc('charMgr').SetNote, self.itemID, toSave)
