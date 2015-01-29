#Embedded file name: eve/client/script/ui/shared\messagebox.py
import uiprimitives
import uicontrols
import uiutil
import uthread
import uicls
import carbonui.const as uiconst
import localization

class MessageBox(uicontrols.Window):
    __guid__ = 'form.MessageBox'
    __nonpersistvars__ = ['suppress']
    default_width = 340
    default_height = 210
    default_alwaysLoadDefaults = True

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.suppress = 0
        self.name = 'modal'
        self.scope = 'all'
        self.edit = None
        self.sr.main.clipChildren = True

    def Execute(self, text, title, buttons, icon, suppText, customicon = None, height = None, default = None, modal = True, okLabel = None, cancelLabel = None):
        self._Execute(title, buttons, icon, suppText, customicon, height, default, modal, okLabel, cancelLabel)
        if text:
            text = text.replace('\r', '').replace('\n', '')
            edit = uicls.EditPlainText(parent=self.sr.main, padding=const.defaultPadding, readonly=1)
            self.edit = edit
            uthread.new(self.SetText, text)

    def ExecuteCustomContent(self, customContentCls, title, buttons, icon, suppText, customicon = None, height = None, default = None, modal = True, okLabel = None, cancelLabel = None, messageData = None):
        self._Execute(title, buttons, icon, suppText, customicon, height, default, modal, okLabel, cancelLabel)
        customContent = customContentCls(parent=self.sr.main, padding=const.defaultPadding, messageData=messageData, align=uiconst.TOTOP)
        self.height = customContent.GetContentHeight() + 110

    def _Execute(self, title, buttons, icon, suppText, customicon, height, default, modal, okLabel, cancelLabel):
        if height is None:
            height = 210
        self.MakeUnMinimizable()
        self.HideHeader()
        self.SetMinSize([340, height])
        self.DefineIcons(icon, customicon)
        if title is None:
            title = localization.GetByLabel('UI/Common/Information')
        self.sr.main = uiutil.FindChild(self, 'main')
        caption = uicontrols.EveCaptionLarge(text=title, align=uiconst.CENTERLEFT, parent=self.sr.topParent, left=64, width=270)
        self.SetTopparentHeight(max(56, caption.textheight + 16))
        self.DefineButtons(buttons, default=default, okLabel=okLabel, cancelLabel=cancelLabel)
        if suppText:
            self.ShowSupp(suppText)
        if modal:
            uicore.registry.SetFocus(self)

    def ShowSupp(self, text):
        bottom = uiprimitives.Container(name='suppressContainer', parent=self.sr.main, align=uiconst.TOBOTTOM, height=20, idx=0)
        self.sr.suppCheckbox = uicontrols.Checkbox(text=text, parent=bottom, configName='suppress', retval=0, checked=0, groupname=None, callback=self.ChangeSupp, align=uiconst.TOPLEFT, pos=(6, 0, 320, 0))
        bottom.height = max(20, self.sr.suppCheckbox.height)

    def ChangeSupp(self, sender):
        self.suppress = sender.checked

    def SetText(self, txt):
        self.edit.SetValue(txt, scrolltotop=1)

    def CloseByUser(self, *etc):
        if self.isModal:
            self.SetModalResult(uiconst.ID_CLOSE)
        else:
            uicontrols.Window.CloseByUser(self)
