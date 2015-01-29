#Embedded file name: eve/client/script/ui/shared/comtool\chatExtraWindows.py
"""
    This file contains extra windows for the chat system
"""
import localization
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.eveWindow import Window
from carbonui.primitives.layoutGrid import LayoutGrid
import carbonui.const as uiconst

class ChannelPasswordWindow(Window):
    MAX_TRIES = 3

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.title = attributes.title
        self.channelID = attributes.channelID
        self.channelName = attributes.channelName
        self.displayName = attributes.displayName
        self.SetMinSize([250, 250])
        self.SetCaption(localization.GetByLabel('UI/Menusvc/PasswordRequired'))
        self.SetTopparentHeight(0)
        self.tries = 0
        settings.user.ui.Set('%sPassword' % self.channelName, '')
        parentGrid = LayoutGrid(parent=self.sr.main, columns=1, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPLEFT, left=10, top=4)
        topLabel = EveLabelMedium(text=attributes.title, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, width=300)
        parentGrid.AddCell(cellObject=topLabel)
        passwordLabel = localization.GetByLabel('UI/Menusvc/PleaseEnterPassword')
        self.passwordLabel = EveLabelMedium(text=passwordLabel, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, padTop=10)
        parentGrid.AddCell(cellObject=self.passwordLabel)
        self.passwordEdit = SinglelineEdit(name='passwordEdit', align=uiconst.TOTOP, passwordCharacter=u'\u2022', top=4)
        parentGrid.AddCell(cellObject=self.passwordEdit)
        savePasswordLabel = localization.GetByLabel('UI/Chat/SavePassword')
        self.rememberPwdCb = Checkbox(text=savePasswordLabel, configName='rememberPwdCb', retval=1, checked=0, groupname=None, align=uiconst.TOTOP)
        parentGrid.AddCell(cellObject=self.rememberPwdCb)
        parentGrid.RefreshGridLayout()
        self.btnGroup = ButtonGroup(parent=self.sr.main, idx=0)
        self.btnGroup.AddButton(localization.GetByLabel('UI/Chat/ChannelWindow/JoinChannel'), self.TryPassword, ())
        self.btnGroup.AddButton(localization.GetByLabel('UI/Common/Cancel'), self.Close, ())
        self.height = self.btnGroup.height + parentGrid.height + self.sr.headerParent.height + parentGrid.top + 10
        self.width = parentGrid.width + 2 * parentGrid.left
        self.MakeUnResizeable()
        self.MakeUnMinimizable()
        self.MakeUncollapseable()

    def TryPassword(self):
        password = self.passwordEdit.GetValue()
        password = password.strip()
        if len(password) < 1:
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/Common/PleaseTypeSomething')})
            return
        self.tries += 1
        savePassword = self.rememberPwdCb.GetValue()
        didWork = sm.GetService('LSC').TryOpenChannel(self.channelID, self.channelName, password, savePassword)
        if didWork is True:
            self.Close()
            return
        self.passwordEdit.SetValue('')
        uicore.Message('uiwarning03')
        self.passwordLabel.text = localization.GetByLabel('UI/Menusvc/PleaseTryEnteringPasswordAgain')
        if self.tries >= self.MAX_TRIES:
            if didWork is False and password is not None:
                sm.GetService('LSC').OpenChannel(self.channelID, 0, ('LSCWrongPassword', {'channelName': self.displayName}))
            self.Close()
