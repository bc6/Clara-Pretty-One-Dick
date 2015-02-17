#Embedded file name: eve/client/script/ui/shared/systemMenu\cmdListEntry.py
import carbonui.const as uiconst
import localization
import listentry
import uicontrols
import uiutil

class CmdListEntry(listentry.Generic):
    __guid__ = 'listentry.CmdListEntry'
    __nonpersistvars__ = []

    def Startup(self, *args):
        listentry.Generic.Startup(self, args)
        self.sr.lock = uicontrols.Icon(icon='ui_22_32_30', parent=self, size=20, align=uiconst.CENTERRIGHT, state=uiconst.UI_HIDDEN, hint=localization.GetByLabel('UI/SystemMenu/Shortcuts/LockedShortcut'), ignoreSize=1)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.command = node.cmdname
        self.sr.context = node.context
        self.sr.isLocked = node.locked
        self.sr.lock.state = [uiconst.UI_HIDDEN, uiconst.UI_NORMAL][node.locked]

    def GetMenu(self):
        self.OnClick()
        if self.sr.isLocked:
            return []
        m = [(uiutil.MenuLabel('UI/SystemMenu/Shortcuts/EditShortcut'), self.Edit), (uiutil.MenuLabel('UI/SystemMenu/Shortcuts/ClearShortcut'), self.Clear)]
        return m

    def OnDblClick(self, *args):
        if not self.sr.isLocked:
            self.Edit()

    def Edit(self):
        uicore.cmd.EditCmd(self.sr.command, self.sr.context)
        self.RefreshCallback()

    def Clear(self):
        self.Deselect()
        uicore.cmd.ClearMappedCmd(self.sr.command)
        self.RefreshCallback()

    def RefreshCallback(self):
        if self.sr.node.Get('refreshcallback', None):
            self.sr.node.refreshcallback()
