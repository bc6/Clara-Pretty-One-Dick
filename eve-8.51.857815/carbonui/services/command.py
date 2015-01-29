#Embedded file name: carbonui/services\command.py
import blue
import service
from carbonui.control.menu import ClearMenuLayer, CloseContextMenus
import uthread
import log
from carbonui.control.window import WindowCore
import trinity
import appUtils
import localization
import carbonui.const as uiconst
import bluepy
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.util.various_unsorted import GetClipboardData
NUMPAD_KEYS = []
for num in range(0, 10):
    NUMPAD_KEYS.append(getattr(uiconst, 'VK_NUMPAD%s' % num, num + 96))

VK_KEYS = [ key for key in dir(uiconst) if key.startswith('VK_') ]
RENAMEMAP = {'CONTROL': 'CTRL',
 'MENU': 'ALT',
 'MBUTTON': 'MOUSE3',
 'XBUTTON1': 'MOUSE4',
 'XBUTTON2': 'MOUSE5',
 'SNAPSHOT': 'PRINTSCREEN',
 'NEXT': 'PAGEDOWN',
 'PRIOR': 'PAGEUP'}
labelsByFuncName = {'CmdCloseActiveWindow': '/Carbon/UI/Commands/CmdCloseActiveWindow',
 'CmdCloseAllWindows': '/Carbon/UI/Commands/CmdCloseAllWindows',
 'CmdLogOff': '/Carbon/UI/Commands/CmdLogOff',
 'CmdMinimizeActiveWindow': '/Carbon/UI/Commands/CmdMinimizeActiveWindow',
 'CmdMinimizeAllWindows': '/Carbon/UI/Commands/CmdMinimizeAllWindows',
 'CmdQuitGame': '/Carbon/UI/Commands/CmdQuitGame',
 'CmdResetMonitor': '/Carbon/UI/Commands/CmdResetMonitor',
 'CmdToggleAudio': '/Carbon/UI/Commands/CmdToggleAudio',
 'OnCtrlA': '/Carbon/UI/Commands/OnCtrlA',
 'OnCtrlC': '/Carbon/UI/Commands/OnCtrlC',
 'OnCtrlShiftTab': '/Carbon/UI/Commands/OnCtrlShiftTab',
 'OnCtrlTab': '/Carbon/UI/Commands/OnCtrlTab',
 'OnCtrlV': '/Carbon/UI/Commands/OnCtrlV',
 'OnCtrlX': '/Carbon/UI/Commands/OnCtrlX',
 'OnEsc': '/Carbon/UI/Commands/OnEsc',
 'OnReturn': '/Carbon/UI/Commands/OnReturn',
 'OnShiftTab': '/Carbon/UI/Commands/OnShiftTab',
 'OnTab': '/Carbon/UI/Commands/OnTab',
 'OpenMonitor': '/Carbon/UI/Commands/OpenMonitor',
 'PrintScreen': '/Carbon/UI/Commands/PrintScreen',
 'WinCmdToggleWindowed': '/Carbon/UI/Commands/WinCmdToggleWindowed',
 'CmdBack': '/Carbon/UI/Commands/Back',
 'CmdForward': '/Carbon/UI/Commands/Forward'}

class CommandMapping:
    """
        A class that represents a mapping of some [MODKEY_1] + ... + [MODKEY_N] + [KEY] 
        combination to a python function. 
        The shortcut should be on the form (uiconst.VK_CTRL, uiconst.VK_X)
    """

    def __init__(self, callback, shortcut, category = None, isLocked = False, enabled = True, ignoreModifierKey = False, repeatable = False):
        self.callback = callback
        self.name = self.callback.func_name
        self.SetShortcut(shortcut)
        self.category = category or 'general'
        self.isLocked = isLocked
        self.ignoreModifierKey = ignoreModifierKey
        self.repeatable = repeatable

    def __repr__(self):
        return "<CommandMapping instance -  name='%s', shortcut='%s', callback=%s>" % (self.name, self.shortcut, self.callback)

    def GetShortcutAsString(self):
        """
        Goes to the OS and asks for the name of the key(s) that was pressed. This is
        used for shortcut mappings. If no key name is obtained from the OS we default
        to the VKEY name that we have. The key name is then wrapped as if localized by
        cerberus since we are trusting the OS to get a properly translated name.
        """
        if not self.shortcut:
            return ''
        retString = ''
        for key in self.shortcut:
            import trinity
            newKey = trinity.app.GetKeyNameText(key)
            if not newKey:
                newKey = ', '.join([ each[3:] for each in VK_KEYS if getattr(uiconst, each) == key ])
                newKey = RENAMEMAP.get(newKey, newKey)
            retString += '%s-' % newKey

        retString = retString[:-1]
        retString = localization.uiutil.PrepareLocalizationSafeString(retString, messageID='commandShortcut')
        try:
            retString.decode('cp1252')
        except UnicodeDecodeError:
            retString = '???'

        return retString

    def GetDescription(self):
        if hasattr(self.callback, 'nameLabelPath'):
            return localization.GetByLabel(self.callback.nameLabelPath)
        if getattr(self.callback, 'nameString', None):
            return self.callback.nameString
        return uicore.cmd.FuncToDesc(self.name)

    def GetName(self):
        if getattr(self.callback, 'nameLabelPath', None):
            return localization.GetByLabel(self.callback.nameLabelPath)
        if getattr(self.callback, 'nameString', None):
            return self.callback.nameString

    def GetDetailedDescription(self):
        if hasattr(self.callback, 'detailedDescription'):
            return localization.GetByLabel(self.callback.detailedDescription)
        if getattr(self.callback, 'descriptionLabelPath', None):
            return localization.GetByLabel(self.callback.descriptionLabelPath)
        if getattr(self.callback, 'descriptionString', None):
            return self.callback.descriptionString

    def SetShortcut(self, shortcut):
        self.shortcut = self._ValidateShortcut(shortcut)

    def _ValidateShortcut(self, shortcut):
        if shortcut is None:
            return
        if type(shortcut) is int:
            shortcut = (shortcut,)
        return shortcut

    def GetAccelerator(self):
        if not self.shortcut:
            return None
        vkey = self.shortcut[-1]
        shortcutModKeys = self.shortcut[:-1]
        modKeys = []
        for modKey in uiconst.MODKEYS:
            modKeys.append(modKey in shortcutModKeys)

        return (tuple(modKeys), vkey)


class CommandMap:
    """
    A command map class which manages commands, command mappings and accelerators
    """

    def __init__(self, defaultCmds = [], customCmds = {}):
        self.commandsByName = {}
        self.commandsByShortcut = {}
        self.accelerators = {}
        self.customCmds = customCmds
        for c in defaultCmds:
            self.AddCommand(c)

    def AddCommand(self, command):
        """
        Add a command to the command map and load it as a shortcut accelerator
        """
        if command.name in self.customCmds:
            command.shortcut = self.customCmds[command.name]
            command.shortcut = self._ModernizeOldTypeShortcut(command.shortcut)
        if self.GetCommandByName(command.name) is None:
            self.commandsByName[command.name] = command
            if command.shortcut is not None:
                self.commandsByShortcut[command.shortcut] = command
        else:
            log.LogWarn('Trying to add the same command twice: %s' % command.name)

    def RemapCommand(self, cmdname, newShortcut = None):
        """
        Remap the shortcut of an existing command. To erase a shortcut, set newShortucut to None
        """
        if newShortcut:
            newShortcut = tuple(newShortcut)
        cmd = self.GetCommandByName(cmdname)
        self.UnloadAccelerator(cmd)
        oldShortcut = cmd.shortcut
        if oldShortcut and oldShortcut in self.commandsByShortcut:
            self.commandsByShortcut.pop(tuple(cmd.shortcut))
        self.customCmds[cmdname] = newShortcut
        if newShortcut:
            self.commandsByShortcut[newShortcut] = cmd
        settings.user.cmd.customCmds[cmdname] = newShortcut
        cmd.SetShortcut(newShortcut)
        self.LoadAccelerator(cmd)

    def _ModernizeOldTypeShortcut(self, shortcut):
        """
        Old shortcuts look like this: (ctrl[bool], alt[bool], shift[bool], vkey [int])
        If an old one is still exists in the users cache, we convert it.
        """
        if not shortcut or len(shortcut) != 4:
            return shortcut
        for i in xrange(3):
            if shortcut[i] not in (0, 1):
                return shortcut

        newShortcut = []
        if shortcut[0]:
            newShortcut.append(uiconst.VK_CONTROL)
        if shortcut[1]:
            newShortcut.append(uiconst.VK_MENU)
        if shortcut[2]:
            newShortcut.append(uiconst.VK_SHIFT)
        try:
            vkKey = getattr(uiconst, 'VK_%s' % shortcut[-1].upper())
        except:
            return None

        newShortcut.append(vkKey)
        return tuple(newShortcut)

    def GetAllCommands(self):
        return self.commandsByName.values()

    def Reset(self):
        self.UnloadAccelerators()

    def GetAllUnmappedCommands(self):
        retCmds = []
        for c in self.commandsByName.values():
            if c.shortcut is None:
                retCmds.append(c)

        return retCmds

    def GetAllMappedCommands(self):
        retCmds = []
        for c in self.commandsByName.values():
            if c.shortcut is not None:
                retCmds.append(c)

        return retCmds

    def GetCommandByShortcut(self, shortcut):
        return self.commandsByShortcut.get(shortcut)

    def GetCommandByName(self, cmdname):
        return self.commandsByName.get(cmdname)

    def GetCommandCategoryNames(self):
        categories = []
        for c in self.GetAllCommands():
            if c.category not in categories:
                categories.append(c.category)

        return categories

    def UnloadAcceleratorsByCategory(self, category):
        for cmd in self.commandsByName.values():
            if cmd.category == category:
                self.UnloadAccelerator(cmd)

    def LoadAcceleratorsByCategory(self, category):
        for cmd in self.commandsByName.values():
            if cmd.category == category:
                self.LoadAccelerator(cmd)

    def LoadAccelerator(self, cmd):
        accelerator = cmd.GetAccelerator()
        if accelerator is None:
            return
        self.accelerators[accelerator] = cmd

    def UnloadAccelerator(self, cmd):
        accelerator = cmd.GetAccelerator()
        if accelerator is None or accelerator not in self.accelerators:
            return
        del self.accelerators[accelerator]

    def LoadAllAccelerators(self):
        for c in self.GetAllCommands():
            self.LoadAccelerator(c)

    def UnloadAllAccelerators(self):
        for c in self.commandsByName.values():
            self.UnloadAccelerator(c)


class CommandService(service.Service):
    __guid__ = 'svc.cmd'
    __update_on_reload__ = 1
    __startupdependencies__ = ['settings']
    __notifyevents__ = ['OnSessionChanged']

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        self.labelsByFuncName = labelsByFuncName
        self.Reload()

    def Reload(self, forceGenericOnly = False):
        if not settings.user.cmd.customCmds:
            settings.user.cmd.customCmds = {}
        self.defaultShortcutMapping = self.SetDefaultShortcutMappingCORE()
        self.defaultShortcutMapping.extend(self.SetDefaultShortcutMappingGAME())
        self.CheckDuplicateShortcuts()
        if hasattr(self, 'commandMap'):
            self.commandMap.UnloadAllAccelerators()
        self.commandMap = CommandMap(defaultCmds=self.defaultShortcutMapping, customCmds=settings.user.cmd.customCmds)
        if session.charid is not None and forceGenericOnly is False:
            self.commandMap.LoadAllAccelerators()
        else:
            self.commandMap.LoadAcceleratorsByCategory('general')

    def Stop(self, stream):
        service.Service.Stop(self)

    def CheckDuplicateShortcuts(self):
        for cmd in self.defaultShortcutMapping:
            for cmdCheck in self.defaultShortcutMapping:
                if cmdCheck.shortcut:
                    sameName = cmdCheck.name == cmd.name
                    sameShortcut = cmdCheck.shortcut == cmd.shortcut
                    if sameShortcut and not sameName:
                        self.LogError('Same default shortcut used for multiple commands:', cmd)

    def OnSessionChanged(self, isRemote, sess, change):
        if 'userid' in change:
            self.Reload()
        if 'charid' in change:
            self.commandMap.LoadAllAccelerators()

    def SetDefaultShortcutMappingCORE(self):
        ret = []
        c = CommandMapping
        CTRL = uiconst.VK_CONTROL
        ALT = uiconst.VK_MENU
        SHIFT = uiconst.VK_SHIFT
        m = [c(self.OnReturn, uiconst.VK_RETURN),
         c(self.OnCtrlA, (CTRL, uiconst.VK_A)),
         c(self.OnCtrlC, (CTRL, uiconst.VK_C)),
         c(self.OnCtrlX, (CTRL, uiconst.VK_X)),
         c(self.OnCtrlV, (CTRL, uiconst.VK_V)),
         c(self.OnEsc, uiconst.VK_ESCAPE),
         c(self.PrintScreen, uiconst.VK_SNAPSHOT),
         c(self.OnCtrlShiftTab, (CTRL, SHIFT, uiconst.VK_TAB)),
         c(self.OnCtrlTab, (CTRL, uiconst.VK_TAB)),
         c(self.OnTab, uiconst.VK_TAB),
         c(self.OnShiftTab, (SHIFT, uiconst.VK_TAB))]
        for cm in m:
            cm.category = 'general'
            cm.isLocked = True
            ret.append(cm)

        m = [c(self.CmdQuitGame, (ALT, SHIFT, uiconst.VK_Q)),
         c(self.CmdLogOff, None),
         c(self.CmdToggleAudio, (CTRL,
          ALT,
          SHIFT,
          uiconst.VK_F12)),
         c(self.WinCmdToggleWindowed, (ALT, uiconst.VK_RETURN)),
         c(self.CmdCloseAllWindows, (CTRL, ALT, uiconst.VK_W)),
         c(self.CmdMinimizeAllWindows, None),
         c(self.CmdMinimizeActiveWindow, None),
         c(self.CmdCloseActiveWindow, (CTRL, uiconst.VK_W)),
         c(self.CmdResetMonitor, (CTRL, ALT, uiconst.VK_RETURN)),
         c(self.OpenMonitor, (CTRL,
          ALT,
          SHIFT,
          uiconst.VK_M)),
         c(self.CmdBack, uiconst.VK_XBUTTON1),
         c(self.CmdForward, uiconst.VK_XBUTTON2)]
        for cm in m:
            cm.category = 'general'
            ret.append(cm)

        return ret

    def SetDefaultShortcutMappingGAME(self):
        """ Overridden by Game specific command file """
        return []

    def HasCommand(self, cmdname):
        avail = self.GetAvailableCmds()
        return bool(cmdname in avail)

    def EditCmd(self, cmdname, context = None):
        if self.IsLocked(cmdname):
            uicore.Message('ShortcutLocked')
            return
        command = self.commandMap.GetCommandByName(cmdname)
        self.MapCmd(cmdname, context)

    def MapCmd(self, *args, **kwds):
        """Overridable by clients"""
        pass

    def CheckKeyDown(self, edit, vkey, flag):
        if vkey == uiconst.VK_RETURN:
            return
        edit.SetValue(self.GetKeyNameFromVK(vkey))

    def MapCmdErrorCheck(self, retval):
        """ 
        Error checking for mapping of new shortcut commands. SHOULD BE OVERRIDDEN.
        """
        return ''

    def ClearMappedCmd(self, cmdname, showMsg = 1):
        if self.IsLocked(cmdname):
            if showMsg:
                uicore.Message('ShortcutLocked')
            return
        self.commandMap.RemapCommand(cmdname, None)
        sm.ScatterEvent('OnMapShortcut', cmdname, None, None, None, None)

    def RestoreDefaults(self):
        settings.user.cmd.customCmds = {}
        self.Reload()
        sm.ScatterEvent('OnRestoreDefaultShortcuts')

    def IsLocked(self, cmdname):
        command = self.commandMap.GetCommandByName(cmdname)
        if command and command.isLocked:
            return True
        else:
            return False

    def IsTaken(self, cmdname):
        return self.GetFuncByShortcut(cmdname) is None

    def MapKeys(self, VK):
        """
            Maps certain keys to what they should be, like the number pad key's to the actual numbers
        """
        if VK in NUMPAD_KEYS:
            num = NUMPAD_KEYS.index(VK)
            VK = getattr(uiconst, 'VK_%s' % num)
        return VK

    def GetCommandCategoryNames(self):
        return self.commandMap.GetCommandCategoryNames()

    def GetKeyNameFromVK(self, VK):
        VK = self.MapKeys(VK)
        return ', '.join([ each[3:] for each in VK_KEYS if getattr(uiconst, each) == VK ])

    def GetVKFromChar(self, char):
        return [ each for each in VK_KEYS if unichr(getattr(uiconst, each)) == char ]

    def GetFuncByShortcut(self, shortcut):
        command = self.commandMap.GetCommandByShortcut(shortcut)
        if command:
            return command.name
        else:
            return None

    def GetShortcutByFuncName(self, funcname, format = False):
        """
        Returns tuple cmd (ctrl, alt, shift, vkey) assigned to the funcname 
        ("CmdQuitGame") if any, else None.
        If format is True, formatted string is returned (Ctrl-F)
        """
        command = self.commandMap.GetCommandByName(funcname)
        if command:
            if format:
                return command.GetShortcutAsString()
            else:
                return command.shortcut
        else:
            return None

    def GetShortcutStringByFuncName(self, funcname):
        command = self.commandMap.GetCommandByName(funcname)
        if command:
            return command.GetShortcutAsString()
        else:
            return ''

    def GetShortcutByString(self, stringfunc):
        command = self.commandMap.GetCommandByName(stringfunc)
        if command and command.shortcut:
            return command.GetShortcutAsString()
        else:
            return None

    def UnpackFuncName(self, funcname):
        nameSpace, className, funcname = funcname.split('.')
        return funcname

    def FuncToDesc(self, funcname):
        if funcname in self.labelsByFuncName:
            return localization.GetByLabel(self.labelsByFuncName[funcname])
        return funcname

    def GetFuncName(self, cmdname):
        cmdname = cmdname.lower().strip()
        for letter in ('_', ' '):
            while cmdname.find(letter * 2) >= 0:
                cmdname = cmdname.replace(letter * 2, letter)

            _cmdname = cmdname.split(letter)
            cmdname = ''
            for part in _cmdname:
                cmdname += '%s%s' % (part[0].upper(), part[1:])

        return cmdname

    def GetAvailableCmds(self, reload = False):
        if not getattr(self, 'availableCmds', None) or reload:
            self.availableCmds = []
            for cmdattr in dir(self):
                if cmdattr[:4] == 'Open' or cmdattr[:3] == 'Cmd':
                    if not self.IsAvailableFunction(self, cmdattr):
                        continue
                    self.availableCmds.append(cmdattr)
                if cmdattr[:6] == 'WinCmd' and not blue.win32.IsTransgaming():
                    self.availableCmds.append(cmdattr)
                if cmdattr[:6] == 'QAOpen' or cmdattr[:5] == 'QACmd':
                    self.availableCmds.append(cmdattr)

        return self.availableCmds

    def IsAvailableFunction(self, fromWhere, cmdattr, *args):
        function = getattr(fromWhere, cmdattr, None)
        if function is None:
            return False
        availabiltyCheck = getattr(function, 'availabiltyCheck', None)
        if availabiltyCheck and not availabiltyCheck():
            return False
        return True

    def GetActiveCmds(self):
        return self.commandMap.GetAllMappedCommands()

    def GetUnmappedCmds(self):
        return self.commandMap.GetAllUnmappedCommands()

    def GetCustomCmd(self, cmdname):
        return self.customCmds.get(cmdname, None)

    def Execute(self, cmdname, cmdNameExact = False):
        if not cmdNameExact:
            cmdname = cmdname.lower()
            if cmdname[0] == '/':
                cmdname = cmdname[1:]
            funcName = self.GetFuncName(cmdname)
        else:
            funcName = cmdname
        func = getattr(self, funcName, None)
        if func is not None:
            try:
                apply(func)
                return '%s executed' % cmdname
            except:
                pass

    def CheckCtrlUp(self, wnd, msgID, ckey):
        chooseWndMenu = getattr(self, 'chooseWndMenu', None)
        if chooseWndMenu and not chooseWndMenu.destroyed and chooseWndMenu.state != uiconst.UI_HIDDEN:
            chooseWndMenu.ChooseHilited()
        self.chooseWndMenu = None
        return 1

    def _AppQuitGame(self):
        bluepy.Terminate('User requesting close')

    def CmdQuitGame(self):
        if uicore.Message('AskQuitGame', {}, uiconst.YESNO, uiconst.ID_YES) == uiconst.ID_YES:
            self.settings.SaveSettings()
            self._AppQuitGame()

    def CmdLogOff(self):
        if uicore.Message('AskLogoffGame', {}, uiconst.YESNO, uiconst.ID_YES) == uiconst.ID_YES:
            appUtils.Reboot('Generic Logoff')

    def CmdToggleAudio(self):
        settings.public.audio.Set('audioEnabled', not settings.public.audio.Get('audioEnabled', 1))
        if settings.public.audio.audioEnabled:
            uicore.audioHandler.Activate()
        else:
            uicore.audioHandler.Deactivate()
        return True

    def WinCmdToggleWindowed(self):
        uicore.device.ToggleWindowed()
        return True

    def CmdCloseAllWindows(self):
        for wnd in uicore.registry.GetWindows()[:]:
            if not uicore.registry.IsWindow(wnd):
                continue
            if wnd.IsKillable():
                if hasattr(wnd, 'CloseByUser'):
                    wnd.CloseByUser()
                else:
                    try:
                        wnd.Close()
                    except:
                        log.LogException()

            elif not wnd.InStack():
                wnd.Minimize()

        return True

    def CmdMinimizeAllWindows(self):
        all = uicore.registry.GetValidWindows()
        for each in all:
            if each.sr.stack is not None:
                continue
            if each.align == uiconst.TOALL:
                continue
            uthread.new(each.Minimize)

        return True

    def CmdMinimizeActiveWindow(self):
        activeWnd = uicore.registry.GetActiveStackOrWindow()
        if activeWnd:
            if activeWnd.align == uiconst.TOALL or not hasattr(activeWnd, 'Minimize'):
                return
            activeWnd.Minimize()
            return True

    def CmdCloseActiveWindow(self):
        activeWnd = uicore.registry.GetActive()
        if not isinstance(activeWnd, WindowCore):
            return
        if activeWnd and getattr(activeWnd, 'canCloseActiveWnd', 1):
            if hasattr(activeWnd, 'CloseByUser'):
                activeWnd.CloseByUser()
                return True
            if hasattr(activeWnd, 'Close'):
                activeWnd.Close()
                return True

    def CmdResetMonitor(self):
        uicore.device.ResetMonitor()
        return True

    def OnUp(self):
        fa = uicore.registry.GetFocus() or uicore.registry.GetActive()
        if fa and hasattr(fa, 'OnUp'):
            uthread.pool('commandSvc::OnKey OnUp', fa.OnUp)

    def OnDown(self):
        fa = uicore.registry.GetFocus() or uicore.registry.GetActive()
        if fa and hasattr(fa, 'OnDown'):
            uthread.pool('commandSvc::OnKey OnDown', fa.OnDown)

    def OnLeft(self):
        fa = uicore.registry.GetFocus() or uicore.registry.GetActive()
        if fa and hasattr(fa, 'OnLeft'):
            uthread.pool('commandSvc::OnKey OnLeft', fa.OnLeft)

    def OnRight(self):
        fa = uicore.registry.GetFocus() or uicore.registry.GetActive()
        if fa and hasattr(fa, 'OnRight'):
            uthread.pool('commandSvc::OnKey OnRight', fa.OnRight)

    def OnHome(self):
        fa = uicore.registry.GetFocus() or uicore.registry.GetActive()
        if fa and hasattr(fa, 'OnHome'):
            uthread.pool('commandSvc::OnKey OnHome', fa.OnHome)

    def OnEnd(self):
        fa = uicore.registry.GetFocus() or uicore.registry.GetActive()
        if fa and hasattr(fa, 'OnEnd'):
            uthread.pool('commandSvc::OnKey OnEnd', fa.OnEnd)

    def OnShiftTab(self):
        self.OnTab()

    def OnTab(self):
        oldfoc = uicore.registry.GetFocus()
        if oldfoc is None or oldfoc == uicore.desktop:
            uicore.registry.ToggleCollapseAllWindows()
        else:
            uicore.registry.FindFocus([1, -1][uicore.uilib.Key(uiconst.VK_SHIFT)])

    def CmdBack(self):
        activeWnd = uicore.registry.GetActive()
        focus = uicore.registry.GetFocus()
        if activeWnd and isinstance(activeWnd, WindowCore) and hasattr(activeWnd, 'OnBack'):
            activeWnd.OnBack()
        elif focus and hasattr(focus, 'OnBack'):
            focus.OnBack()

    def CmdForward(self):
        activeWnd = uicore.registry.GetActive()
        focus = uicore.registry.GetFocus()
        if activeWnd and isinstance(activeWnd, WindowCore) and hasattr(activeWnd, 'OnForward'):
            activeWnd.OnForward()
        elif focus and hasattr(focus, 'OnForward'):
            focus.OnForward()

    def OnReturn(self):
        uicore.registry.Confirm()

    def OnCtrlA(self):
        focus = uicore.registry.GetFocus()
        if focus and hasattr(focus, 'SelectAll'):
            focus.SelectAll()
            return True
        active = uicore.registry.GetActive()
        if active and hasattr(active, 'SelectAll'):
            active.SelectAll()
            return True

    def OnCtrlC(self):
        focus = uicore.registry.GetFocus()
        if getattr(focus, 'Copy', None):
            return focus.Copy()

    def OnCtrlX(self):
        focus = uicore.registry.GetFocus()
        if getattr(focus, 'Cut', None):
            return focus.Cut()

    def OnCtrlV(self):
        text = GetClipboardData()
        if not text:
            return False
        focus = uicore.registry.GetFocus()
        if focus and hasattr(focus, 'Paste'):
            focus.Paste(text)
            return True

    def OnCtrlTab(self):
        w = self.GetWndMenu()
        if w:
            w.Next()
            return True

    def OnCtrlShiftTab(self):
        w = self.GetWndMenu()
        if w:
            w.Prev()
            return True

    def GetWndMenu(self):
        if uicore.registry.GetModalWindow():
            return
        if not getattr(self, 'chooseWndMenu', None) or self.chooseWndMenu.destroyed or self.chooseWndMenu.state == uiconst.UI_HIDDEN:
            ClearMenuLayer()
            wnds = [ each for each in uicore.registry.GetWindows() if not getattr(each, 'defaultExcludeFromWindowMenu', 0) ]
            showhide = uicore.layer.main.state == uiconst.UI_PICKCHILDREN
            m = []
            for each in wnds:
                if not hasattr(each, 'Maximize'):
                    continue
                if hasattr(each, 'GetCaption'):
                    label = each.GetCaption()
                else:
                    label = each.name
                m.append((label, each.Maximize))

            if m:
                mv = menu.CreateMenuView(menu.CreateMenuFromList(m), None, None)
                mv.left, mv.top = (uicore.desktop.width - mv.width) // 2, (uicore.desktop.height - mv.height) // 2
                uicore.layer.menu.children.insert(0, mv)
                self.chooseWndMenu = mv
                self.wmTimer = AutoTimer(10, self._CheckWndMenu)
            else:
                self.chooseWndMenu = None
        return self.chooseWndMenu

    def _CheckWndMenu(self, *args):
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        if not ctrl:
            self.wmTimer = None
        chooseWndMenu = getattr(self, 'chooseWndMenu', None)
        if chooseWndMenu and not chooseWndMenu.destroyed and chooseWndMenu.state != uiconst.UI_HIDDEN:
            chooseWndMenu.ChooseHilited()
        self.chooseWndMenu = None

    def OnEsc(self, stopLoading = True):
        if CloseContextMenus():
            return 1
        modalResult = uicore.registry.GetModalResult(uiconst.ID_CANCEL, 'btn_cancel')
        if modalResult is not None:
            uicore.registry.GetModalWindow().SetModalResult(modalResult)
            return True
        if stopLoading and uicore.layer.loading.state == uiconst.UI_NORMAL:
            uthread.new(sm.GetService('loading').HideAllLoad)
            return True
        sys = uicore.layer.systemmenu
        if sys:
            if sys.isopen:
                uthread.new(sys.CloseMenu)
            else:
                uthread.new(sys.OpenView)
            return True

    OnEsc_Core = OnEsc

    def PrintScreen(self, *args):
        year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetWallclockTime())
        date = '%d.%.2d.%.2d.%.2d.%.2d.%.2d' % (year,
         month,
         day,
         hour,
         minute,
         second)
        ext = 'png'
        path = '%s/%s/capture/Screenshots/%s.%s' % (blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL),
         boot.appname,
         date,
         ext)
        rt = trinity.device.GetRenderContext().GetDefaultBackBuffer()
        if not rt.isReadable:
            readable = trinity.Tr2RenderTarget(rt.width, rt.height, 1, rt.format)
            rt.Resolve(readable)
            bmp = trinity.Tr2HostBitmap(readable)
        else:
            bmp = trinity.Tr2HostBitmap(rt)
        if bmp.format == trinity.PIXEL_FORMAT.B8G8R8A8_UNORM:
            bmp.ChangeFormat(trinity.PIXEL_FORMAT.B8G8R8X8_UNORM)
        bmp.Save(path)
        return True

    def OpenMonitor(self, *args):
        sm.GetService('monitor').Show()
