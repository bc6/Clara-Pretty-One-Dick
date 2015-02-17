#Embedded file name: eve/devtools/script\svc_slash.py
from eve.devtools.script.slashError import Error
from service import *
import const
import sys, os
import param
import blue, chat, uthread
import triui
import uix
import trinity
import uiutil
import log
import localization
import carbonui.const as uiconst
import base
import random
import util
from collections import defaultdict
import uiprimitives
import uicontrols
from utillib import KeyVal
SERVICENAME = 'slash'
TOKEN = '$'
aliasFile = 'aliases.ini'
macroFile = 'macros.ini'
version = 2.4
Message = lambda title, body, icon = triui.INFO: sm.GetService('gameui').MessageBox(body, title, buttons=uiconst.OK, icon=icon)
AsyncMessage = lambda *args: uthread.new(Message, *args)
Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)

class InlineFunctionResolver():

    def __getitem__(self, func):
        if ':' in func:
            func, args = func.split(':', 1)
        else:
            args = ()
        method = getattr(self, 'f_' + func.lower(), None)
        if func is None:
            raise Error("unknown inline function '%s'" % func)
        if args:
            args = args.split(',')
        return method(*args)

    def _getinvrow(self, *args):
        if len(args) == 1:
            containerID = eve.session.shipid
            flag = args[0]
        elif len(args) == 2:
            if args[0].lower() == 'me':
                containerID = eve.session.shipid
            else:
                containerID = int(args[0])
            flag = args[1]
        flag = getattr(const, 'flag' + flag.capitalize())
        for rec in sm.GetService('invCache').GetInventoryFromId(containerID).List():
            if rec.flag == flag:
                return rec

    def f_itemid(self, *args, **kw):
        return self._getinvrow(*args).itemID

    def f_typeid(self, *args):
        return self._getinvrow(*args).typeID


def GetCharacter(name, ignoreNotFound = False):
    result = sm.RemoteSvc('lookupSvc').LookupCharacters(name, 1)
    if result:
        cfg.eveowners.Prime([ each.characterID for each in result ])
        return result[0]
    try:
        return cfg.eveowners.Get(int(name))
    except:
        if ignoreNotFound:
            return None
        AsyncMessage('No such character', 'Character not found:<br>  %s' % name)
        raise UserError('IgnoreToTop')


def Act(what, set, p):
    c = sm.GetService(SERVICENAME).GetChannel()
    if not c:
        return
    short = False
    if what == 'gag':
        mode = chat.CHTMODE_LISTENER
        verb = 'gagged'
    elif what == 'ban':
        if set:
            mode = chat.CHTMODE_DISALLOWED
        else:
            mode = chat.CHTMODE_NOTSPECIFIED
            short = True
        verb = 'banned'
    else:
        raise ValueError('unsupported action')
    if set:
        try:
            char, reason, duration = p.Parse('ssi')
        except:
            char, reason = p.Parse('ss')
            duration = 30

        if duration:
            until = blue.os.GetWallclockTime() + duration * const.MIN
        else:
            until = None
    else:
        char, = p.Parse('s')
        reason = ''
        until = blue.os.GetWallclockTime() - 30 * const.MIN
    ret = GetCharacter(char)
    if short:
        sm.GetService('LSC').AccessControl(c.channelID, ret.characterID, mode)
    else:
        sm.GetService('LSC').AccessControl(c.channelID, ret.characterID, mode, until, reason)
    return '%s has been %s%s' % (ret.characterName, ['un', ''][set], verb)


class SlashService(Service):
    __guid__ = 'svc.slash'
    __notifyevents__ = ['ProcessRestartUI', 'ProcessUIRefresh']
    __neocommenuitem__ = (('Slash Console', 'ui_9_64_7'), 'Show', ROLEMASK_ELEVATEDPLAYER)
    __slashhook__ = True

    def __init__(self):
        self.patched = False
        self.aliases = {}
        self.macros = {}
        Service.__init__(self)

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        try:
            self.wnd = None
            self.history = []
            self.historyPtr = -1
            self.lastslash = ''
            self.busy = self.aborted = False
            self.jobs = []
            self.LoadMacrosAndAliases()
            self.Clear()
        except:
            log.LogException()
            sys.exc_clear()

        self.state = SERVICE_RUNNING

    def GetMacros(self):
        self.LoadMacrosAndAliases()
        return self.macros.items()

    def LoadMacrosAndAliases(self):
        defaultMacros = {'GMH: Unload All': '/unload me all',
         'WM: Remove All Drones': '/unspawn range=500000 only=categoryDrone',
         'WM: Remove All Wrecks': '/unspawn range=500000 only=groupWreck',
         'WM: Remove CargoContainers': '/unspawn range=500000 only=groupCargoContainer',
         'WM: Remove SecureContainers': '/unspawn range=500000 only=groupSecureCargoContainer',
         'HEALSELF: Repair My Ship': '/heal',
         'HEALSELF: Repair My Modules': '/repairmodules',
         'GMH: Online My Modules': '/online me',
         'GML: Session Change 5sec': '/sessionchange 5'}
        self.aliases = self.LoadStuff(aliasFile)
        if len(self.aliases) == 0:
            self.aliases = {}
        self.macros = self.LoadStuff(macroFile)
        self.macros.update(defaultMacros)

    def LoadStuff(self, fileName):
        targetFile = os.path.join(sm.StartService('insider').GetInsiderDir(), fileName)
        if not os.path.exists(targetFile):
            return {}
        d = {}
        lines = blue.win32.AtomicFileRead(targetFile)[0].replace('\r', '').replace('\x00', '').split('\n')
        for line in lines:
            aliasName, comseq = line.split('=', 1)
            d[aliasName.strip()] = comseq.strip()

        return d

    def SaveStuff(self, thisDict, fileName):
        text = '\r\n'.join([ '%s=%s' % (aliasName, comseq) for aliasName, comseq in thisDict.iteritems() ])
        targetFile = os.path.join(sm.StartService('insider').GetInsiderDir(), fileName)
        blue.win32.AtomicFileWrite(targetFile, text)

    def Stop(self, memStream = None):
        if self.wnd and not self.wnd.destroyed:
            self.Hide()
        Service.Stop(self, memStream)

    def Show(self):
        self.wnd = wnd = uicontrols.Window.GetIfOpen(windowID='slashcon')
        if wnd:
            self.wnd.Maximize()
            return
        self.wnd = wnd = uicontrols.Window.Open(windowID='slashcon')
        wnd.DoClose = self.Hide
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Slash')
        wnd.SetMinSize([390, 224])
        wnd.OnUIRefresh = None
        main = uiprimitives.Container(name='con', parent=uiutil.GetChild(wnd, 'main'), pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        i = wnd.sr.i = uiprimitives.Container(name='input', parent=main, align=uiconst.TOBOTTOM, height=20)
        c = uiprimitives.Container(name='control', parent=main, align=uiconst.TOBOTTOM, height=24)
        o = uiprimitives.Container(name='output', parent=main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        t = uicontrols.Label(text='Command: ', parent=i, align=uiconst.TOLEFT, color=None, state=uiconst.UI_DISABLED, singleline=1)
        input = wnd.sr.input = uicontrols.SinglelineEdit(name='slashCmd', parent=i, left=0, width=0, align=uiconst.TOALL)
        input.OnKeyDown = (self.InputKey, input)
        input.OnReturn = self.InputEnter
        buttons = [['Clear',
          self.Clear,
          None,
          81],
         ['Exec Last',
          self.ExLast,
          None,
          81],
         ['Exec Once',
          self.ExOnce,
          None,
          81],
         ['Exec Loop',
          self.ExLoop,
          None,
          81],
         ['Abort',
          self.ExAbort,
          None,
          81]]
        controls = uicontrols.ButtonGroup(btns=buttons, line=0)
        controls.align = uiconst.CENTER
        controls.width = 69 * len(buttons) + 10
        controls.height = 16
        c.children.append(controls)

        def checker(cb):
            checked = cb.GetValue()
            settings.user.ui.Set('slashasync', checked)
            if checked:
                wnd.sr.async.hint = 'Non-Blocking: ON<br>Remote slash commands do not block the slash console.<br>Note: Local slash commands always block<br>Click to disable non-blocking mode.'
            else:
                wnd.sr.async.hint = 'Non-Blocking: OFF<br>Remote slash commands block the slash console until they finish.<br>Note: Local slash commands always block<br>Click to enable non-blocking mode.'
            cb.state = uiconst.UI_HIDDEN
            cb.state = uiconst.UI_NORMAL

        wnd.sr.async = uicontrols.Checkbox(text='Non-Blocking', parent=c, configName='slashasync', retval=0, checked=settings.user.ui.Get('slashasync', 0), callback=checker)
        checker(wnd.sr.async)
        wnd.sr.async.state = uiconst.UI_HIDDEN
        output = wnd.sr.output = uicontrols.Edit(setvalue=self.outputcontents, parent=o, readonly=1)
        output.autoScrollToBottom = 1
        uicore.registry.SetFocus(input)

    def Hide(self, *args):
        if self.wnd:
            self.slashcontents = self.wnd.sr.input.GetValue()
            self.wnd.Close()
        self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def ProcessUIRefresh(self):
        if self.wnd:
            self.wnd.Close()
            self.Show()

    def Clear(self, *args):
        cmds = []
        import svc
        for sname in svc.__dict__:
            s = getattr(svc, sname)
            if getattr(s, '__slashhook__', False):
                for m in dir(s):
                    if m.startswith('cmd_'):
                        cmds.append(m[4:])

        cmds.sort()
        self.outputcontents = 'Commands: <font color="#ffc000">%s</font><br>' % (', '.join(cmds) or 'None')
        if self.aliases:
            cmds = self.aliases.keys()
            cmds.sort()
            self.outputcontents += 'Aliases: <font color="#00ffc0">%s</font><br>' % ', '.join(cmds)
        self.outputcontents += 'Note: Slash commands, extended commands and user-defined aliases all work both in chat and in console. Commands that require a chat channel cannot be run in the console.<br>'
        if self.wnd:
            self.wnd.sr.output.SetText(self.outputcontents)

    def Echo(self, text):
        self.outputcontents = '%s%s' % (self.outputcontents, text)
        if self.wnd:
            self.wnd.sr.output.SetText(self.outputcontents)

    def InputKey(self, otherself, key, flag):
        if key == uiconst.VK_UP:
            self.InputHistory(-1)
        elif key == uiconst.VK_DOWN:
            self.InputHistory(1)
        else:
            uicontrols.SinglelineEdit.OnKeyDown(otherself, key, flag)

    def InputHistory(self, offset):
        if self.history:
            self.historyPtr += offset
            if self.historyPtr < -len(self.history):
                self.historyPtr = -len(self.history)
                return
            if self.historyPtr >= 0:
                self.historyPtr = 0
                self.wnd.sr.input.SetValue('')
                return
            self.wnd.sr.input.SetValue(self.history[self.historyPtr])

    def InputEnter(self, *args):
        try:
            self.lastslash = self.wnd.sr.input.GetValue()
        except:
            return

        self.history.append(self.lastslash)
        self.historyPtr = 0
        self.wnd.sr.input.SetValue('')
        self.Ex(self.lastslash)

    def ExLoop(self, *args):
        try:
            cmd = self.wnd.sr.input.GetValue().strip()
        except:
            return

        if len(cmd) > 1:
            result = uix.QtyPopup(maxvalue=50, minvalue=1, caption='Looped Execution', label='', hint='Specify number of times to execute:<br><br> %s<br><br>Note:<br>- Max. 50 iterations<br>- USE WITH CARE!' % cmd)
            if result:
                amount = result['qty']
                self.lastslash = cmd
                self.wnd.sr.input.SetValue('')
                self.Ex(cmd, amount)

    def ExLast(self, *args):
        if self.lastslash:
            self.Ex(self.lastslash)

    def ExOnce(self, *args):
        try:
            self.lastslash = self.wnd.sr.input.GetValue()
        except:
            return

        self.Ex(self.lastslash)

    def ExAbort(self, *args):
        if self.busy and not self.aborted:
            self.Echo('<font color="#ffff00">*** Aborting...</font><br>')
        self.aborted = True
        self.busy = False

    def Ex(self, this, count = 1):
        if not this:
            return
        if this[0] != '/':
            this = '/' + this
        self.jobs.append((this, count))
        if self.busy:
            if count > 0:
                self.Echo('<font color="#ffff00">*** Queued(%d): %s</font><br>' % (count, this))
            else:
                self.Echo('<font color="#ffff00">*** Queued: %s</font><br>' % this)
            return
        self.JobHandler()

    def JobHandler(self):
        try:
            self.aborted = False
            while self.jobs and not self.aborted:
                this, count = self.jobs.pop(0)
                isLoop = count > 1
                try:
                    self.busy = True
                    self.aborted = False
                    if isLoop:
                        self.Echo('<font color="#ffff00">*** Loop started (%d iterations)</font><br>' % count)
                    while count and not self.aborted:
                        self.Echo('<font color="#00ffff">slash: %s</font><br>' % this)
                        try:
                            res = sm.GetService('slash').SlashCmd(this)
                            self.Echo('<font color="#00ff55">slash result: %s</font><br>' % res)
                        except UserError as e:
                            if e.args[0] in ('SlashError',):
                                self.Echo('<font color="#ff5500">slash error: %s</font><br>' % e.dict['reason'])
                                break
                            else:
                                self.Echo('<font color="#00ff55">slash result: None</font><br>')
                                raise UserError, e

                        count -= 1
                        blue.pyos.synchro.SleepWallclock(100)

                    if isLoop:
                        if self.aborted:
                            reason = 'Aborted by user'
                        elif count != 0:
                            reason = 'Error condition'
                        else:
                            reason = 'Batch completed'
                        self.Echo('<font color="#ffff00">*** Loop terminated (%s)</font><br>' % reason)
                finally:
                    self.busy = False

            else:
                if self.jobs:
                    self.Echo('<font color="#ffff00">*** Slash command queue flushed</font><br>')
                    self.jobs = []

        finally:
            self.aborted = False

    def InitStuff(self):
        if hasattr(self, 'remoteCommandList'):
            return
        try:
            sm.RemoteSvc('slash').SlashCmd('/')
        except UserError as e:
            try:
                msg = e.args[1]['reason']
                cmds = eval(msg.split(': ')[1])
                cmds.sort()
            except:
                cmds = []
                log.LogException()
                Message('Hmmm', "Unable to acquire server slash command list. Not particularly bad, just means command autocompletion won't work")
                sys.exc_clear()

            sys.exc_clear()

        self.remoteCommandList = cmds

    def MatchCmd(self, command):
        ret = []
        localMatch = False
        for cmd in self.aliases:
            if cmd.startswith(command):
                if cmd == command:
                    return ([cmd], True)
                if cmd not in ret:
                    ret.append(cmd)
                localMatch = True

        for cmd in self.remoteCommandList:
            if cmd.startswith(command):
                if cmd == command:
                    return ([cmd], False)
                ret.append(cmd)

        import svc
        for sname in svc.__dict__:
            s = getattr(svc, sname)
            if getattr(s, '__slashhook__', False):
                for f in s.__dict__:
                    if f.startswith('cmd_' + command):
                        cmd = f[4:]
                        if cmd == command:
                            return ([cmd], True)
                        if cmd not in ret:
                            ret.append(cmd)
                        localMatch = True

        return (ret, localMatch)

    def SlashCmd(self, command, fallThrough = True, isMacro = False):
        if command.startswith('//'):
            return sm.RemoteSvc('slash').SlashCmd(command[1:])
        try:
            return self._SlashCmd(command, fallThrough, isMacro)
        except Error as e:
            raise UserError('SlashError', {'reason': e})

    def _SlashCmd(self, txt, fallThrough, isMacro):
        if isMacro:
            self.InitStuff()
            command = None
        else:
            parts = txt.split(' ', 1)
            command = parts[0].strip().lower()
            if len(parts) > 1:
                args = parts[1].strip()
            else:
                args = ''
            if command[0] == '/':
                command = command[1:]
            self.InitStuff()
            if self.remoteCommandList is not None:
                matches, hasLocal = self.MatchCmd(command)
                if hasLocal:
                    if len(matches) == 1:
                        command = matches[0]
                    else:
                        raise Error('%s is ambiguous. It resolves to multiple commands or aliases: %s' % (command, matches))
        if self.aliases.has_key(command) or isMacro:
            if isMacro:
                sequence = txt
            else:
                sequence = self.aliases[command]
            sequence = sequence.split(';')
            for line in sequence:
                line = line.strip()
                if line:
                    newline = []
                    inToken = False
                    p = param.ParamObject(txt)
                    for part in line.split(TOKEN):
                        if newline:
                            if len(part) >= 1:
                                if part[0] in '0123456789':
                                    try:
                                        if len(part) >= 2 and part[1] == '-':
                                            part = p[int(part[0]):] + part[2:]
                                        else:
                                            part = p[int(part[0])] + part[1:]
                                    except param.Error:
                                        raise Error('Alias expected additional parameter(s)')

                                else:
                                    part = TOKEN + part
                        newline.append(part)

                    newline = ''.join(newline) % InlineFunctionResolver()
                    res = self.SlashCmd(newline)

            if len(sequence) == 1:
                return res
            return 'Ok'
        try:
            args = args % InlineFunctionResolver()
            commandLine = '/' + command + ' ' + args
        except Error:
            raise
        except:
            log.LogException()
            raise Error('unexpected error resolving inline function')

        import svc
        for sname in svc.__dict__:
            s = getattr(svc, sname)
            if getattr(s, '__slashhook__', False):
                slash = getattr(s, 'cmd_' + command, None)
                if slash:
                    try:
                        ret = getattr(sm.GetService(s.__guid__[4:]), 'cmd_' + command)(param.ParamObject(args))
                        if ret:
                            return ret
                        break
                    except param.Error as e:
                        if slash.__doc__:
                            raise Error('usage: /%s %s' % (command, slash.__doc__.replace('%s', command)))
                        else:
                            raise Error('/%s called with crap args and doesnt handle it properly' % command)

        if fallThrough:
            return sm.RemoteSvc('slash').SlashCmd(commandLine)

    def cmd_sethackingdifficulty(self, p):
        sm.GetService('hackingUI').SetDifficulty(p.Parse('i')[0])
        return 'Ok'

    def cmd_sethackingvirusstats(self, p):
        integers = p.Parse('iii')
        sm.GetService('hackingUI').SetVirusStats(integers[0], integers[1], integers[2])
        return 'Ok'

    def cmd_openhacking(self, p):
        sm.GetService('hackingUI').TriggerNewGame()

    def cmd_run(self, p):
        """filename"""
        filename, = p.Parse('s')
        if not os.path.exists(filename):
            filename += '.txt'
            if not os.path.exists(filename):
                raise Error('file not found')
        for line in open(filename, 'r'):
            line = line.strip()
            if line.startswith('/'):
                self.SlashCmd(line)

        return 'Ok'

    def cmd_macromenu(self, p):
        """add macroName command; ...<br>/%s del macroName<br>/%s list"""
        return self.cmd_alias(p, True)

    def cmd_alias(self, p, isMacro = False):
        """add aliasName command; ...<br>/%s del aliasName<br>/%s list"""
        what, rest = p.Parse('s?r')
        what = what.lower()
        if isMacro:
            thing = 'Macro'
            catalog = self.macros
            file = macroFile
        else:
            thing = 'Alias'
            catalog = self.aliases
            file = aliasFile
        if what == 'add':
            what, aliasName, rest = p.Parse('ssr')
            for key in catalog.keys():
                if key.lower() == aliasName.lower():
                    action = 'modified'
                    break
            else:
                action = 'added'

            catalog[aliasName] = rest
            self.SaveStuff(catalog, file)
            return '%s %s %s' % (thing, aliasName, action)
        if what == 'del':
            if not rest:
                raise param.Error
            aliasName = rest.lower().strip('"')
            for key in catalog.keys():
                if key.lower() == aliasName:
                    del catalog[aliasName]
                    self.SaveStuff(catalog, file)
                    return '%s %s deleted' % (thing, aliasName)
            else:
                raise Error('No such %s: %s' % (thing, aliasName))

        elif what == 'list':
            cmds = catalog.keys()
            cmds.sort()
            return '%s: <font color="#00ffc0">%s</font><br>' % (thing, ', '.join(cmds))
        for key, item in catalog.iteritems():
            if key.lower() == what.lower():
                return '%s %s is defined as: %s' % (thing, what, item)

        raise param.Error

    def cmd_loop(self, p):
        """iterations slashCommand"""
        count, rest = p.Parse('ir')
        if count >= 10:
            if count > 50:
                Message('Looped Execution', 'The number of iterations must be less than 50')
                return
            ret = sm.GetService('gameui').MessageBox(title='Looped Execution', text='You have specified %d iterations.<br>Slash commands looped this way cannot be aborted. Depending on the slash command, it can take a long time to complete or cause a high server load.<br>Continue?' % count, buttons=uiconst.OKCANCEL, icon=uiconst.WARNING)
            if ret:
                if ret[0] in (uiconst.ID_CANCEL, uiconst.ID_CLOSE):
                    return
        for i in xrange(count):
            self.SlashCmd(rest)

        return 'Ok'

    def cmd_chtgag(self, p):
        """characterName|characterID "reason" [minutes]"""
        return Act('gag', True, p)

    def cmd_chtungag(self, p):
        """characterName|characterID"""
        return Act('gag', False, p)

    def cmd_chtban(self, p):
        """characterName|characterID "reason" [minutes]"""
        return Act('ban', True, p)

    def cmd_chtunban(self, p):
        """characterName|characterID"""
        return Act('ban', False, p)

    def cmd_whoami(self, p):
        roles = []
        for k, v in globals().iteritems():
            if k.startswith('ROLE_'):
                if type(v) in (int, long):
                    if eve.session.role & v and v not in (ROLE_ANY, ROLE_PLAYER, ROLE_LOGIN):
                        roles.append(k[5:])

        text = ['character: %s (%s)' % (eve.session.charid, cfg.eveowners.Get(eve.session.charid).name), 'user: %s (type: %s)' % (eve.session.userid, eve.session.userType), 'role: 0x%08X (%s)' % (eve.session.role, ', '.join(roles))]
        AsyncMessage('Account Information', '<br>'.join(text))
        return 'Ok'

    def cmd_hop(self, p):
        """meters"""
        if eve.session.role & ROLE_WORLDMOD:
            return
        dist, = p.Parse('i')
        if eve.session.stationid:
            raise Error("This obviously won't work in a station :)")
        bp = sm.GetService('michelle').GetBallpark()
        me = bp.GetBall(bp.ego)
        v = trinity.TriVector(me.vx, me.vy, me.vz)
        v.Normalize()
        v.Scale(dist)
        sm.RemoteSvc('slash').SlashCmd('/tr me me offset=%d,%d,%d' % (int(v.x), int(v.y), int(v.z)))
        sm.GetService('menu').ClearAlignTargets()
        return 'Ok'

    def cmd_online(self, p):
        import util
        target, = p.Parse('s')
        activeShipID = util.GetActiveShip()
        if session.stationid2 is not None and (target == 'me' or int(target) == activeShipID):
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            for module in dogmaLocation.dogmaItems[activeShipID].GetFittedItems().itervalues():
                if const.effectOnline in (row.effectID for row in cfg.dgmtypeeffects.get(module.typeID, [])):
                    try:
                        dogmaLocation.OnlineModule(module.itemID)
                    except UserError as e:
                        if e.msg.startswith('EffectAlreadyActive'):
                            continue
                        raise

        else:
            sm.RemoteSvc('slash').SlashCmd('/online %s' % target)
        return 'Ok'

    def cmd_super(self, p):
        """characterName|characterID|"me\""""
        target, = p.Parse('s')
        if target.lower() == 'me':
            victim = 'you'
            target = 'me'
        else:
            char = GetCharacter(target)
            victim = '"' + char.characterName + '"'
            target = char.characterID
        Progress('Making %s Leet' % victim, 'Please wait...', 0, 1)
        try:
            sm.RemoteSvc('slash').SlashCmd('/giveskill %s all 5' % target)
        finally:
            Progress('Making %s Leet' % victim, 'Done!', 1, 1)

        return 'Ok'

    def cmd_noob(self, p):
        """characterName|characterID|"me\""""
        target, = p.Parse('s')
        if target.lower() == 'me':
            victim = 'you'
            target = 'me'
        else:
            char = GetCharacter(target)
            victim = '"' + char.characterName + '"'
            target = char.characterID
        Progress('Making %s n00b' % victim, 'Please wait...', 0, 1)
        try:
            sm.RemoteSvc('slash').SlashCmd('/removeskill %s all' % target)
        finally:
            Progress('Making %s n00b' % victim, 'Done!', 1, 1)

        return 'Ok'

    def cmd_bp(self, p):
        try:
            name, rest = p.Parse('s?r')
            if rest is None:
                rest = ''
        except param.Error:
            rest = ''
            try:
                name, = p.Parse('r')
            except param.Error:
                return

        ret = self.AutoComplete(name, allowedCategories=[const.categoryBlueprint])
        if ret:
            return sm.RemoteSvc('slash').SlashCmd('/bp %s %s' % (ret.typeID, rest))
        else:
            return

    def cmd_createitem(self, p):
        qty = 1
        try:
            name, = p.Parse('s')
        except param.Error:
            try:
                name, qty = p.Parse('ss')
            except param.Error:
                try:
                    name, = p.Parse('r')
                except param.Error:
                    return

        ret = self.AutoComplete(name)
        if ret:
            return sm.RemoteSvc('slash').SlashCmd('/createitem %s %s' % (ret.typeID, qty))
        else:
            return

    def cmd_unload(self, p):
        try:
            target, rest = p.Parse('s?r')
            if rest is None:
                rest = ''
            else:
                rest = rest.lower().strip('"')
        except param.Error:
            return

        if target.lower() != 'me' or rest == 'all' or rest.isdigit():
            return
        matches = {}
        for rec in sm.GetService('invCache').GetInventoryFromId(eve.session.shipid).List():
            if rec.categoryID != const.categoryOwner:
                rec = cfg.invtypes.Get(rec.typeID)
                if rest in rec.name.lower():
                    matches[rec.name] = rec

        if not matches:
            return
        matches = matches.items()
        matches.sort()
        if len(matches) > 1:
            ret = uix.ListWnd(matches, listtype='generic', caption='AutoComplete: %d types found' % len(matches))
        else:
            ret = matches[0]
        if ret:
            return sm.RemoteSvc('slash').SlashCmd('/unload me %s' % ret[1].typeID) or 'Ok'
        else:
            return

    def cmd_dogmaupdate(self, p):
        sm.RemoteSvc('slash').SlashCmd('/dogmaupdate')
        sm.GetService('clientEffectCompiler').effects.clear()
        eve.Message('CustomNotify', {'notify': 'Server has regenerated the expressions and yours have been cleared'})
        return 'Ok'

    def cmd_loadcontainer(self, p):
        return self.cmd_fit(p, cmd='load', categories=None)

    def cmd_fit(self, p, cmd = 'fit', categories = -1):
        if categories == -1:
            categories = [const.categoryModule, const.categoryDrone, const.categoryCharge]
        qty = ''
        try:
            target, name, qty = p.Parse('sss')
        except param.Error:
            try:
                target, name = p.Parse('ss')
            except param.Error:
                try:
                    target, name = p.Parse('sr')
                except param.Error:
                    return

        ret = self.AutoComplete(name, allowedCategories=categories)
        if ret:
            return sm.RemoteSvc('slash').SlashCmd('/%s "%s" %s %s' % (cmd,
             target,
             ret.typeID,
             qty))
        else:
            return

    def cmd_entity(self, p):
        qty = 1
        try:
            action, qty, name = p.Parse('sir')
        except param.Error:
            try:
                action, name = p.Parse('sr')
            except param.Error:
                return

        if action.lower() != 'deploy':
            return
        else:
            ret = self.AutoComplete(name, allowedCategories=[const.categoryEntity])
            if ret:
                return sm.RemoteSvc('slash').SlashCmd('/entity deploy %s %s' % (qty, ret.typeID)) or 'Ok'
            return

    def cmd_spawn(self, p):
        try:
            name, rest = p.Parse('sr')
        except param.Error:
            try:
                name, = p.Parse('r')
                rest = ''
            except param.Error:
                return

        ret = self.AutoComplete(name, allowedCategories=[const.categoryShip, const.categoryAsteroid, const.categoryDrone], allowedGroups=[const.groupLargeCollidableObject,
         const.groupCargoContainer,
         const.groupBiomass,
         const.groupComet,
         const.groupCloud,
         const.groupSentryGun])
        if ret:
            return sm.RemoteSvc('slash').SlashCmd('/spawn %s %s' % (ret.typeID, rest))
        else:
            return

    def cmd_spawnn(self, p):
        try:
            qty, deviation, name = p.Parse('ifr')
        except param.Error:
            return

        ret = self.AutoComplete(name, allowedCategories=[const.categoryShip, const.categoryAsteroid, const.categoryDrone], allowedGroups=[const.groupLargeCollidableObject,
         const.groupCargoContainer,
         const.groupBiomass,
         const.groupComet,
         const.groupCloud,
         const.groupSentryGun])
        if ret:
            return sm.RemoteSvc('slash').SlashCmd('/spawnn %s %s %s' % (qty, deviation, ret.typeID)) or 'Ok'
        else:
            return

    def cmd_giveskills(self, p):
        try:
            target, skillname, level = p.Parse('ssi')
        except param.Error:
            try:
                level = None
                target, skillname = p.Parse('sr')
            except param.Error:
                return

        skillname = skillname.strip('"')
        if skillname.lower() == 'all':
            return
        else:
            ret = self.AutoComplete(skillname, allowedCategories=[const.categorySkill])
            if ret:
                if level is None:
                    level = 5
                return sm.RemoteSvc('slash').SlashCmd('/giveskill "%s" %s %s' % (target, ret.typeID, level)) or 'Ok'
            return

    def cmd_removeskills(self, p):
        try:
            level = None
            target, skillname = p.Parse('sr')
        except param.Error:
            return

        skillname = skillname.strip('"')
        if skillname.lower() == 'all':
            return
        else:
            ret = self.AutoComplete(skillname, allowedCategories=[const.categorySkill])
            if ret:
                return sm.RemoteSvc('slash').SlashCmd('/removeskill "%s" %s' % (target, ret.typeID)) or 'Ok'
            return

    def cmd_massfleetinvite(self, p):
        """Fleet-invite everyone in the channel if they are not already in your fleet"""
        fleetSvc = sm.StartService('fleet')
        fleetSvc.CheckIsInFleet()
        members = fleetSvc.GetMembers()
        candidates = [ charID for charID in self.GetChannelUsers() if charID not in members ]
        if eve.session.charid in candidates:
            candidates.remove(eve.session.charid)
        t = len(candidates)
        c = 0
        for charID in candidates:
            c += 1
            Progress('Inviting...', '[%d/%d] %s' % (c, t, cfg.eveowners.Get(charID).ownerName), c, t)
            try:
                fleetSvc.fleet.Invite(charID, None, None, None, True)
            except:
                pass

        Progress('Inviting...', 'Done!', 1, 1)
        return 'Ok'

    def cmd_masstransport(self, p):
        """Teleport everyone in the channel this command was given in to your current location if they are not already in the same system as you."""
        local = (('solarsystemid2', session.solarsystemid2),)
        c = self.GetChannel()
        if not c or c.channelID == local:
            return
        l = sm.GetService('LSC').channels.get(local, None)
        if not l:
            return Error('No local channel?!')
        candidates = [ charID for charID in self.GetChannelUsers() if charID not in l.memberList ]
        if session.charid in candidates:
            candidates.remove(session.charid)
        t = len(candidates)
        c = 0
        for charID in candidates:
            c += 1
            Progress('Transfering...', '[%d/%d] %s' % (c, t, cfg.eveowners.Get(charID).ownerName), c, t)
            sm.RemoteSvc('slash').SlashCmd('/tr %d me noblock' % charID)

        Progress('Transfering...', 'All commands sent to the server', 1, 1)
        return 'Ok'

    def cmd_massstanding(self, p):
        """Changes the standings for everyone in the channel in line with the normal /setstanding slash command."""
        try:
            fromID, newStanding = p.Parse('sr')
        except:
            raise UserError('SlashError', {'reason': 'Provide from and the new standing value.'})
            sys.exc_clear()
            return

        local = (('solarsystemid2', eve.session.solarsystemid2),)
        c = self.GetChannel()
        if not c or c.channelID == local:
            return
        candidates = [ charID for charID in self.GetChannelUsers() ]
        if eve.session.charid in candidates:
            candidates.remove(eve.session.charid)
        t = len(candidates)
        c = 0
        reason = 'Mass standing change by %s' % cfg.eveowners.Get(eve.session.charid).name
        corps = sm.RemoteSvc('lookupSvc').LookupCorporations(fromID)
        corpIDs = [ each.corporationID for each in corps ]
        factions = sm.RemoteSvc('lookupSvc').LookupFactions(fromID)
        factionIDs = [ each.factionID for each in factions ]
        resultIDs = corpIDs + factionIDs
        resultList = [ (cfg.eveowners.Get(each).name, cfg.eveowners.Get(each).id, cfg.eveowners.Get(each).typeID) for each in resultIDs ]
        if not resultList:
            raise UserError('SlashError', {'reason': 'Unable to resolve corporation or faction name'})
            sys.exc_clear()
            return
        ret = uix.ListWnd(resultList, caption='AutoComplete: %d types found' % len(resultList), ordered=1)
        if ret:
            if eve.Message('CustomQuestion', {'header': 'Change standings?',
             'question': 'Do you really want to change the standings towards %s for the characters in this channel?' % ret[0]}, uiconst.YESNO) == uiconst.ID_YES:
                for charID in candidates:
                    c += 1
                    Progress('Setting standings...', '[%d/%d] %s' % (c, t, cfg.eveowners.Get(charID).ownerName), c, t)
                    sm.RemoteSvc('slash').SlashCmd('/setstanding "%s" %d %s "%s"' % (ret[1],
                     charID,
                     newStanding,
                     reason))

                txt = 'Standings to %s set to %s for %d characters' % (ret[0], newStanding, c)
            else:
                txt = 'Standings to %s left unmodified' % ret[0]
        else:
            txt = 'Standings left unmodified'
        Progress('Setting standings...', 'Done!', 1, 1)
        eve.Message('CustomNotify', {'notify': txt})
        return 'Ok'

    def cmd_pos(self, p):
        try:
            action, id = p.Parse('sr')
        except param.Error:
            try:
                action = p.Parse('s')
                bp = sm.GetService('michelle').GetBallpark()
                for ballID in bp.balls.keys():
                    try:
                        item = bp.GetInvItem(ballID)
                        if item.groupID in (const.groupControlTower,):
                            id = item.itemID
                            action = action[0]
                    except:
                        pass

            except:
                pass

        if not id:
            return
        elif action.lower() != 'fuel':
            return
        else:
            try:
                id = int(id)
            except ValueError:
                eve.Message('CustomInfo', {'info': "This must be called as either '/pos fuel' or '/pos fuel itemID'"})
                return 'ok'

            resourcesPerHour = []
            reinforcedResourcesPerHour = []
            totalFuelVolumePerCycle = float()
            starbaseCharters = []
            invCache = sm.GetService('invCache')
            chosenTower = invCache.GetInventoryFromId(id)
            secStatus = sm.GetService('map').GetSecurityStatus(eve.session.locationid)
            for item in cfg.invtypes:
                if item.groupID in (const.groupLease,):
                    starbaseCharters.append(item.typeID)

            for tower in sm.RemoteSvc('posMgr').GetControlTowerFuelRequirements():
                if tower.controlTowerTypeID == chosenTower.GetTypeID():
                    if tower.resourceTypeID == const.typeStrontiumClathrates:
                        reinforcedResourcesPerHour.append((tower.resourceTypeID, tower.quantity, cfg.invtypes.Get(tower.resourceTypeID).volume))
                    elif secStatus < 0.4:
                        if tower.resourceTypeID not in starbaseCharters:
                            resourcesPerHour.append((tower.resourceTypeID, tower.quantity, cfg.invtypes.Get(tower.resourceTypeID).volume))
                    else:
                        resourcesPerHour.append((tower.resourceTypeID, tower.quantity, cfg.invtypes.Get(tower.resourceTypeID).volume))

            for resourceTypeID, amountPerCycle, resourceVolume in resourcesPerHour:
                totalFuelVolumePerCycle += int(amountPerCycle * resourceVolume)

            totalFuelVolumePerCycle += 1
            strontVolume = reinforcedResourcesPerHour[0][2]
            fuelBay = chosenTower.GetCapacity()
            strontBay = chosenTower.GetCapacity(flag=const.flagSecondaryStorage)
            fuelCycles = int(fuelBay.capacity / totalFuelVolumePerCycle)
            strontCycles = int(strontBay.capacity / strontVolume)
            if eve.session.role & ROLE_WORLDMOD:
                addList = []
                for commodity, amountPerCycle, resourceVolume in reinforcedResourcesPerHour:
                    sm.GetService('slash').SlashCmd('crea %d %s' % (commodity, strontCycles))
                    for cargo in invCache.GetInventoryFromId(eve.session.shipid).ListCargo():
                        if cargo.typeID == commodity:
                            addList.append(cargo.itemID)

                invCache.GetInventoryFromId(id).MultiAdd(addList, eve.session.shipid, flag=const.flagSecondaryStorage)
                addList = []
                for fuel, amountPerCycle, resourceVolume in resourcesPerHour:
                    sm.GetService('slash').SlashCmd('crea %d %s' % (fuel, int(fuelCycles * amountPerCycle)))
                    for cargo in invCache.GetInventoryFromId(eve.session.shipid).ListCargo():
                        if cargo.typeID == fuel and cargo.stacksize == fuelCycles * amountPerCycle:
                            addList.append(cargo.itemID)

                invCache.GetInventoryFromId(id).MultiAdd(addList, eve.session.shipid, flag=const.flagNone)
                return 'Ok'
            shipType = const.typeBHMegaCargoShip
            oldShipItemID = eve.session.shipid
            newShipItemID = int()
            if invCache.GetInventoryFromId(int(eve.session.shipid)).GetTypeID() != shipType:
                newShipItemID = sm.RemoteSvc('slash').SlashCmd('/spawn %d' % shipType)
                ship = sm.StartService('gameui').GetShipAccess()
                if ship:
                    sm.StartService('sessionMgr').PerformSessionChange('board', ship.Board, newShipItemID, oldShipItemID)
            blue.pyos.synchro.SleepSim(5000)
            addList = []
            for commodity, amountPerCycle, resourceVolume in reinforcedResourcesPerHour:
                sm.GetService('slash').SlashCmd('load me %d %s' % (commodity, strontCycles))
                for cargo in invCache.GetInventoryFromId(eve.session.shipid).ListCargo():
                    if cargo.typeID == commodity:
                        addList.append(cargo.itemID)

            invCache.GetInventoryFromId(id).MultiAdd(addList, eve.session.shipid, flag=const.flagSecondaryStorage)
            addList = []
            for fuel, amountPerCycle, resourceVolume in resourcesPerHour:
                sm.GetService('slash').SlashCmd('load me %d %s' % (fuel, int(fuelCycles * amountPerCycle)))
                for cargo in invCache.GetInventoryFromId(eve.session.shipid).ListCargo():
                    if cargo.typeID == fuel and cargo.stacksize == fuelCycles * amountPerCycle:
                        addList.append(cargo.itemID)

            invCache.GetInventoryFromId(id).MultiAdd(addList, eve.session.shipid, flag=const.flagNone)
            if blue.os.GetSimTime() <= eve.session.nextSessionChange:
                ms = 1000 + 1000L * (eve.session.nextSessionChange - blue.os.GetSimTime()) / 10000000L
                blue.pyos.synchro.SleepSim(ms)
                if newShipItemID:
                    ship = sm.StartService('gameui').GetShipAccess()
                    if ship:
                        sm.StartService('sessionMgr').PerformSessionChange('board', ship.Board, oldShipItemID, newShipItemID)
                        sm.GetService('slash').SlashCmd('heal %d 0' % newShipItemID)
                        blue.pyos.synchro.SleepSim(5000)
                        sm.GetService('insider').HealRemove(const.groupWreck)
            return 'Ok'

    def GetAmmoTypesForWeapon(self, itemID):
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        dogmaItem = dogmaLocation.dogmaItems[itemID]
        ammoInfoByTypeID = defaultdict(lambda : util.KeyVal(singletons=[], nonSingletons=[]))
        validGroupIDs = dogmaLocation.dogmaStaticMgr.GetValidChargeGroupsForType(dogmaItem.typeID)
        GetTypeAttribute = dogmaLocation.dogmaStaticMgr.GetTypeAttribute
        preferredChargeSize = GetTypeAttribute(dogmaItem.typeID, const.attributeChargeSize)
        legalTypes = set()
        for t in cfg.invtypes:
            if t.groupID not in validGroupIDs:
                continue
            if preferredChargeSize is not None and GetTypeAttribute(t.typeID, const.attributeChargeSize) != preferredChargeSize:
                continue
            legalTypes.add(t.typeID)

        return legalTypes

    def IsLegalAmmo(self, weaponItemID, chargeTypeID):
        if not chargeTypeID:
            return True
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        for typeID in self.GetAmmoTypesForWeapon(weaponItemID):
            if typeID == chargeTypeID:
                return True

        return False

    def GetRandomAmmoForWeapon(self, weaponItemID):
        for typeID in self.GetAmmoTypesForWeapon(weaponItemID):
            return typeID

    def cmd_ammo(self, p):
        try:
            typeID = p.Parse('s')[0]
        except:
            raise UserError('SlashError', {'reason': 'Usage: /ammo [typeID]|random<br>Loads ammo of the specified type into all turrets or launchers that support this type.<br>If random is specified then all weapons are loaded with the first matching ammo found.'})

        if typeID == 'random':
            typeID = 0
        shipInv = sm.GetService('invCache').GetInventoryFromId(session.shipid)
        for row in shipInv.ListHardwareModules():
            if self.IsLegalAmmo(row.itemID, typeID):
                shipInv.ReplaceCharges(row.flagID, None, forceRemove=True)

        if typeID == 'clear':
            return 'Ok'
        typeID = int(typeID)
        blue.pyos.synchro.SleepSim(1000)
        cmds = []
        stateMgr = sm.GetService('godma').GetStateManager()
        for row in shipInv.ListHardwareModules():
            thisTypeID = typeID
            if not self.IsLegalAmmo(row.itemID, typeID):
                continue
            if not thisTypeID:
                thisTypeID = self.GetRandomAmmoForWeapon(row.itemID)
            if not thisTypeID:
                continue
            self.LogNotice('/ammo: Putting %s into %s' % (thisTypeID, row.itemID))
            charge = cfg.invtypes.Get(thisTypeID)
            chargeSize = sm.GetService('godma').GetTypeAttribute(thisTypeID, const.attributeChargeSize)
            ma = stateMgr.GetType(row.typeID)
            num = int(ma.capacity / charge.volume)
            if num > 0:
                cmds.append('/fit me %d %d flag=%d' % (thisTypeID, num, row.flagID))

        uthread.parallel([ (sm.GetService('slash').SlashCmd, (cmd,)) for cmd in cmds ])
        return 'Ok'

    def cmd_sessionchangetimer(self, p):
        """Change the session change timer. Values clamped between 5..60
        Missing or invalid arguments will show the current timer"""
        oldVal = base.sessionChangeDelay
        try:
            secs = p.Parse('i')[0]
            base.sessionChangeDelay = min(max(5, secs), 60) * const.SEC
            session.nextSessionChange = None
        except:
            pass

        eve.Message('CustomNotify', {'notify': 'Session-Change Timer was changed from %ss to <b>%ss</b>.<br>This value will be reset next time you log in' % (oldVal / const.SEC, base.sessionChangeDelay / const.SEC)})
        return 'Ok'

    def cmd_recustomize(self, p):
        """ opens up the recustomization of the current character"""
        if sm.GetService('cc').NoExistingCustomization():
            return 1
        sm.GetService('gameui').GoCharacterCreationCurrentCharacter()
        return 1

    def cmd_buyorders(self, p):
        """Buys stuff from the market, starts with the lowest price.
        Syntax /buyorders type [quantity] [range (0=station, 1+ =jumps, default=region)]"""
        if session.stationid is None:
            raise Error('You must be in a station to execute this command.')
        qty = 1
        orderRange = 32767
        try:
            name, = p.Parse('s')
        except param.Error:
            try:
                name, qty = p.Parse('si')
            except param.Error:
                try:
                    name, qty, orderRange = p.Parse('sii')
                except param.Error:
                    return

        theType = self.AutoComplete(name)
        typeID = theType.typeID
        minVolume = 1
        duration = 0
        useCorp = False
        qtyDone = 0
        Progress('Buying %s %s' % (qty, theType.typeName), 'Please wait...', 0, 1)
        try:
            while qty > qtyDone:
                order = sm.GetService('marketQuote').GetBestAskInRange(typeID, session.stationid, orderRange)
                if order is None:
                    break
                if order.volRemaining + qtyDone > qty:
                    buyQty = qty - qtyDone
                else:
                    buyQty = order.volRemaining
                sm.GetService('marketQuote').BuyStuff(session.stationid, typeID, order.price, buyQty, orderRange, minVolume, duration, useCorp)
                blue.pyos.synchro.SleepSim(800)
                qtyDone += buyQty

        finally:
            if qtyDone == qty:
                Progress('Done buying all the %s you asked me to.' % theType.typeName, '', 1, 1)
            else:
                Progress('Done. Did not find as many %s as you asked for.' % theType.typeName, '', 1, 1)

        return 'Ok'

    def cmd_sellorders(self, p):
        """Puts items for sale by creating the items first and then put those on the market
        Syntax /sellorders type price [qty] [ordercount] [price fluctuation in %]"""
        if session.stationid is None:
            raise Error('You must be in a station to execute this command.')
        qty = 1
        orderCount = 1
        priceFluct = 0
        try:
            theType, price = p.Parse('sf')
        except param.Error:
            try:
                theType, price, qty = p.Parse('sfi')
            except param.Error:
                try:
                    theType, price, qty, orderCount = p.Parse('sfii')
                except param.Error:
                    try:
                        theType, price, qty, orderCount, priceFluct = p.Parse('sfiif')
                    except param.Error:
                        raise Error('Syntax error: should be /sellorders type price [qty] [ordercount] [price fluctuation in %]')

        duration = 14
        useCorp = False
        located = None
        if priceFluct != 0:
            p = priceFluct / 100.0
            minPriceCents = int(max(price - price * p, 1) * 100)
            maxPriceCents = int((price + price * p) * 100)
        Progress('Creating %s Market order(s)' % orderCount, 'Please wait...', 0, 1)
        try:
            validatedItems = []
            itemID = self.cmd_createitem(param.ParamObject(str(theType) + ' ' + unicode(orderCount * qty)))
            blue.pyos.synchro.SleepSim(1200)
            typeID = sm.GetService('invCache').FetchItem(itemID, session.stationid).typeID
            for x in xrange(orderCount):
                if priceFluct == 0:
                    orderPrice = price
                else:
                    orderPrice = random.randint(minPriceCents, maxPriceCents) / 100.0
                validatedItem = KeyVal(stationID=int(session.stationid), typeID=int(typeID), itemID=itemID, price=orderPrice, quantity=int(qty), located=located)
                sm.GetService('marketQuote').SellMulti([validatedItem], useCorp, duration)

        finally:
            Progress('Done creating market orders.', '', 1, 1)

        return 'Ok'

    def cmd_cancelallorders(self, p):
        """Cancels all market orders the character has (that are legal to cancel)"""
        orders = sm.GetService('marketQuote').GetMyOrders()
        if not orders:
            raise Error('No market orders found.')
        for order in orders:
            sm.GetService('marketQuote').CancelOrder(order.orderID, order.regionID)

        return 'Ok'

    def cmd_reimbursebounties(self, p):
        sm.GetService('bountySvc').GMReimburseBounties()
        return 'Ok'

    def cmd_clearbountycache(self, p):
        sm.GetService('bountySvc').GMClearBountyCache()
        return 'Ok'

    def cmd_killright(self, p):
        sm.RemoteSvc('slash').SlashCmd('/killright %s' % p.line)
        sm.GetService('bountySvc').ClearAllKillRightData()
        return 'Ok'

    def cmd_newscanner(self, p):
        cmd = p.Parse('s')
        if 'start' in cmd:
            sm.GetService('sensorSuite')
        elif 'stop' in cmd:
            sm.StopService('sensorSuite')
        elif 'show' in cmd:
            if session.solarsystemid is not None:
                sensorSuite = sm.GetService('sensorSuite')
                sensorSuite.EnableSensorOverlay()
        elif 'hide' in cmd:
            if session.solarsystemid is not None:
                sensorSuite = sm.GetService('sensorSuite')
                sensorSuite.EnableSensorOverlay()
        elif 'register' in cmd:
            if session.solarsystemid is not None:
                sensorSuite = sm.GetService('sensorSuite')
                sm.RemoteSvc('scanMgr').SignalTrackerRegister()
        elif 'scan' in cmd:
            if session.solarsystemid is not None:
                sensorSuite = sm.GetService('sensorSuite')
                sensorSuite.DisableSensorOverlay()
                sensorSuite.systemReadyTime = blue.os.GetSimTime() - const.SEC * 2
                sensorSuite.StartSensorSweep()
        return 'Ok'

    def cmd_dplay(self, p):
        coords = None
        try:
            dungeonID, godmode, x, y, z = p.Parse('i?i?f?f?f')
            coords = (x, y, z)
            if None in coords:
                coords = None
        except param.Error:
            raise Error('Use /dplay DUNGEONID [godmode:0|1]\n(godmode defaults to 1)')

        dungeonID = int(dungeonID)
        if godmode is None:
            godmode = 1
        self.leveleditor = player = util.Moniker('keeper', session.userid)
        player.PlayDungeon(dungeonID, godmode=godmode, coords=coords)
        return 'Ok'

    def cmd_dgoto(self, p):
        roomID = int(p.Parse('i')[0])
        self.leveleditor = player = util.Moniker('keeper', session.userid)
        player.GotoRoom(roomID)
        return 'Ok'

    def MatchTypes(self, name, allowedCategories = None, allowedGroups = None, smart = True):
        name = name.strip('"')
        if not hasattr(self, 'typeIDByName'):
            d = self.typeIDByName = {}
            noOfExceptions = 0
            for line in cfg.invtypes:
                try:
                    if line._typeName is not None:
                        d[line._typeName.lower()] = line.typeID
                except Exception:
                    if noOfExceptions == 0:
                        log.LogException('Unexpected Exception in Matching types')
                    noOfExceptions += 1
                    sys.exc_clear()

            if noOfExceptions > 0:
                self.LogError('MatchTypes failed', noOfExceptions, 'times getting the typeName')
            if boot.region == 'optic':
                languageID = localization.const.LOCALE_SHORT_CHINESE
                for line in cfg.invtypes:
                    try:
                        if line.typeNameID is not None and line.typeNameID:
                            d[line.GetRawName(languageID)] = line.typeID
                    except Exception:
                        sys.exc_clear()

        def _filter(rec):
            if allowedCategories:
                if rec.categoryID in allowedCategories:
                    return True
                if allowedGroups:
                    if rec.groupID in allowedGroups:
                        return True
            elif allowedGroups:
                if rec.groupID in allowedGroups:
                    return True
            else:
                return True
            return False

        if smart and name.lower() in self.typeIDByName:
            rec = cfg.invtypes.Get(self.typeIDByName[name.lower()])
            return [(rec.name, rec)]
        if name.isdigit():
            rec = cfg.invtypes.GetIfExists(int(name))
            if rec:
                if 1 or _filter(rec):
                    return [(rec.name, rec)]
                raise Error("Type '%s' is not in the list of allowed types for this command" % rec.name)
        else:
            name = name.lower().strip('"')
        if len(name) < 3:
            raise UserError('SlashError', {'reason': 'Autocompletion requires 3 or more characters'})
        matches = []
        count = 0
        for typeName, typeID in self.typeIDByName.iteritems():
            if not count % 500:
                blue.pyos.synchro.Yield()
            count += 1
            if name in typeName:
                rec = cfg.invtypes.Get(typeID)
                if _filter(rec):
                    matches.append((rec.name, rec))

        return matches

    def AutoComplete(self, name, allowedCategories = None, allowedGroups = None):
        matches = self.MatchTypes(name, allowedCategories, allowedGroups)
        if not matches:
            return None
        if len(matches) == 1:
            ret = matches[0]
        else:
            matches.sort()
            ret = uix.ListWnd(matches, listtype='generic', caption='AutoComplete: %d types found' % len(matches))
        if not ret:
            raise Error('Cancelled')
        return ret[1]

    def GetChannel(self):
        f = sys._getframe().f_back
        while f:
            loc = f.f_locals
            if loc.has_key('self'):
                from eve.client.script.ui.shared.comtool.lscchannel import Channel as LSCChannel
                if isinstance(loc['self'], LSCChannel):
                    return loc['self']
            f = f.f_back

        raise Error('This function can only be used in a chat channel')

    def GetChannelUsers(self):
        c = self.GetChannel()
        return [ each.charID for each in c.userlist.sr.nodes ]


exports = {'slash.Error': Error}
