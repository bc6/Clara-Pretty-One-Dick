#Embedded file name: eve/client/script/ui\mapCmdWindow.py
import uicontrols
import carbonui.const as uiconst
import localization

class MapCmdWindow(uicontrols.Window):
    """
    The pop-up window in the system menu shortcuts section that enables players to map shortcuts
    """
    __guid__ = 'form.MapCmdWindow'
    default_fixedWidth = 250
    default_state = uiconst.UI_NORMAL
    default_windowID = 'MapCmdWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        cmdname = attributes.cmdname
        self.SetCaption(uicore.cmd.FuncToDesc(cmdname))
        self.SetTopparentHeight(0)
        self.SetMainIconSize(0)
        self.MakeUnResizeable()
        self.MakeUnpinable()
        self.mouseCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnGlobalMouseUp)
        self.keyCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_KEYUP, self.OnGlobalKeyUp)
        currShortcut = uicore.cmd.GetShortcutStringByFuncName(cmdname) or localization.GetByLabel('UI/Common/None')
        lbl = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Commands/EnterNewShortcutPrompt', currShortcut=currShortcut), parent=self.sr.main, state=uiconst.UI_DISABLED, width=self.default_width - 100, left=50, top=10, maxLines=None)
        btnGroup = uicontrols.ButtonGroup(btns=[(localization.GetByLabel('UI/Common/Cancel'), self.Close, None)], parent=self.sr.main, line=True)
        self.SetHeight(self.GetHeaderHeight() + lbl.textheight + btnGroup.height + 20)

    def OnGlobalMouseUp(self, window, msgID, param):
        btnNum, type = param
        btnMap = {uiconst.MOUSEMIDDLE: uiconst.VK_MBUTTON,
         uiconst.MOUSEXBUTTON1: uiconst.VK_XBUTTON1,
         uiconst.MOUSEXBUTTON2: uiconst.VK_XBUTTON2}
        if btnNum in btnMap:
            self.Apply(btnMap[btnNum])

    def OnGlobalKeyUp(self, window, msgID, param):
        vkey, type = param
        self.Apply(vkey)

    def Confirm(self, *args):
        """
        Overriding the default functionality of closing modal window on ENTER
        """
        pass

    def Apply(self, vkey):
        shortcut = []
        for modKey in uiconst.MODKEYS:
            if uicore.uilib.Key(modKey) and modKey != vkey:
                shortcut.append(modKey)

        shortcut.append(vkey)
        self.result = {'shortcut': tuple(shortcut)}
        self.SetModalResult(1)

    def _OnClose(self, *args):
        uicore.event.UnregisterForTriuiEvents(self.mouseCookie)
        uicore.event.UnregisterForTriuiEvents(self.keyCookie)
