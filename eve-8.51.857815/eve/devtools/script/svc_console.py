#Embedded file name: eve/devtools/script\svc_console.py
import sys
from traceback import format_exception
import slash
from eve.client.script.ui.control.divider import Divider
import blue
import uiutil
import util
import uicls
import carbonui.const as uiconst
from service import *
import uiprimitives
import uicontrols
SERVICENAME = 'console'

class ConsoleService(Service):
    """Python console"""
    __exportedcalls__ = {'Show': []}
    __notifyevents__ = ['ProcessRestartUI']
    __dependencies__ = []
    __guid__ = 'svc.console'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME
    __neocommenuitem__ = (('<color=0xffff8080>Python Console', 'res:/ui/Texture/WindowIcons/warning.png'), 'Show', ROLE_PROGRAMMER)
    __slashhook__ = True

    def __init__(self):
        Service.__init__(self)
        self.consolecontents = ''
        self.outputcontents_default = self.outputcontents = "Use the variable 'MyResult' to display results here."

    def GetMenu(self, *args):
        return [['Python Console', self.Show]]

    def Run(self, memStream = None):
        self.wnd = None

    def Stop(self, memStream = None):
        self.CleanUp()
        Service.Stop(self)

    def CleanUp(self):
        if self.wnd and not self.wnd.destroyed:
            self.Hide()

    def cmd_reportdesync(self, p):
        try:
            threshold, = p.Parse('f')
        except:
            threshold = 1000.0

        serverTimestamp = 0
        bp = sm.GetService('michelle').GetBallpark()
        tries = 0
        while bp.currentTime != serverTimestamp and tries < 10:
            ret, serverTimestamp = sm.RemoteSvc('slash').SlashCmd('/reportdesync')
            if bp.currentTime < serverTimestamp:
                blue.pyos.synchro.SleepSim((serverTimestamp - bp.currentTime) * 1000)
            tries += 1

        txt = '<h2>Desync Report</h2>This report shows object in the local ballpark that are more than %.1f m from the server position.<br><br>' % threshold
        txt += '%s<br>Server timestamp: %s<br>Local timestamp: %s<br>' % (util.FmtDate(blue.os.GetSimTime()), serverTimestamp, bp.currentTime)
        txt += 'Location: %s - Char: %s - Ship: %s<br><br>' % (eve.session.locationid, eve.session.charid, eve.session.shipid)
        import math
        for ballID, pos in ret.iteritems():
            if ballID in bp.balls:
                b = bp.balls[ballID]
                serverVec = ret[ballID]
                clientPos = (b.x, b.y, b.z)
                clientVel = (b.vx, b.vy, b.vz)
                diff = (clientPos[0] - serverVec[0], clientPos[1] - serverVec[1], clientPos[2] - serverVec[2])
                delta = math.sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)
                if delta > threshold:
                    diffVel = (clientVel[0] - serverVec[3], clientVel[1] - serverVec[4], clientVel[2] - serverVec[5])
                    deltaVel = math.sqrt(diffVel[0] * diffVel[0] + diffVel[1] * diffVel[1] + diffVel[2] * diffVel[2])
                    spdClient = math.sqrt(clientVel[0] * clientVel[0] + clientVel[1] * clientVel[1] + clientVel[2] * clientVel[2])
                    spdServer = math.sqrt(serverVec[3] * serverVec[3] + serverVec[4] * serverVec[4] + serverVec[5] * serverVec[5])
                    if hasattr(b, 'typeID'):
                        typeName = cfg.invtypes.Get(b.typeID).name
                    else:
                        try:
                            typeName = cfg.invtypes.Get(bp.slimItems[ballID].typeID).name
                        except KeyError:
                            continue

                    dynamicThreshold = max(spdClient, spdServer) * (abs(serverTimestamp - bp.currentTime) + 1)
                    if delta > dynamicThreshold:
                        txt += '<b>%s (%s)</b> <font color="#FF0000">LOCATION MISMATCH</font>: <b>%.1f m</b> ' % (ballID, typeName, delta)
                    else:
                        txt += '<b>%s (%s)</b> Location Mismatch: <b>%.1f m</b> ' % (ballID, typeName, delta)
                    txt += 'Client Speed: %.2f m/s - Server Speed: %.2f m/s - Delta Velocity: <b>%.2f m/s</b><br><br>' % (spdClient, spdServer, deltaVel)

        eve.Message('CustomInfo', {'info': txt}, modal=0)

    def cmd_execfile(self, p):
        """fileName"""
        if not (eve.session and eve.session.role & ROLE_PROGRAMMER):
            raise slash.Error('You are not authorized to use this command.')
        filename, = p.Parse('s')
        execfile(filename, globals())
        return 'Ok'

    def DoExecute(self, *args):
        if not eve.session.role & ROLE_PROGRAMMER:
            return
        crud = self.wnd.sr.input.GetAllText()
        returnDict = {}
        result2 = ''
        try:
            if crud:
                code = compile(crud, '<console>', 'exec')
                eval(code, globals(), returnDict)
        except:
            exc, e, tb = sys.exc_info()
            result2 = (''.join(format_exception(exc, e, tb)) + '\n').replace('\n', '<br>')
            exc = e = tb = None
            raise
        finally:
            if self.wnd and not self.wnd.destroyed:
                self.wnd.sr.output.SetValue(result2 + str(returnDict.get('MyResult', '')))

    def DoClear(self, *args):
        self.wnd.sr.input.SetValue('')
        self.wnd.sr.output.SetValue(self.outputcontents_default)

    def DoCopy(self, *args):
        self.wnd.sr.input.CopyAll()

    def DoPaste(self, *args):
        text = blue.pyos.GetClipboardData()
        for chunk in util.LineWrap(text, maxlines=-1, maxlen=1500, pfx=''):
            self.wnd.sr.input.Paste(chunk)

    def Show(self):
        self.wnd = wnd = uicontrols.Window.GetIfOpen(windowID=SERVICENAME)
        if wnd:
            self.wnd.Maximize()
            return
        self.wnd = wnd = uicontrols.Window.Open(windowID=SERVICENAME)
        wnd._OnClose = self.Hide
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Console')
        wnd.SetMinSize([352, 200])
        main = uiprimitives.Container(name='con', parent=uiutil.GetChild(wnd, 'main'), pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        o = wnd.sr.o = uiprimitives.Container(name='output', parent=main, align=uiconst.TOBOTTOM)
        o.height = max(32, settings.user.ui.Get('consoleoutputheight', 48))
        c = uiprimitives.Container(name='control', parent=main, align=uiconst.TOBOTTOM, height=24)
        i = uiprimitives.Container(name='input', parent=main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        divider = Divider(name='divider', align=uiconst.TOBOTTOM, idx=1, height=const.defaultPadding, parent=c, state=uiconst.UI_NORMAL)
        divider.Startup(o, 'height', 'y', 32, 128)
        input = wnd.sr.input = uicls.EditPlainText(setvalue=self.consolecontents, parent=i)
        input.autoScrollToBottom = 1
        buttons = [['Copy All',
          self.DoCopy,
          None,
          81],
         ['Paste',
          self.DoPaste,
          None,
          81],
         ['Clear',
          self.DoClear,
          None,
          81],
         ['<color=0xff40ff40>Execute',
          self.DoExecute,
          None,
          81]]
        controls = uicontrols.ButtonGroup(btns=buttons, line=0)
        controls.align = uiconst.TORIGHT
        controls.width = 64 * len(buttons)
        controls.height = 16
        c.children.append(controls)

        def checker(cb):
            checked = cb.GetValue()
            settings.user.ui.Set('consolestealth', checked)
            if checked:
                wnd.sr.stealth.hint = 'Stealth: ON<br>Console exceptions are not logged.<br>Click to disable stealth.'
            else:
                wnd.sr.stealth.hint = 'Stealth: OFF<br>Console exceptions are logged.<br>Click to enable stealth.'
            cb.state = uiconst.UI_HIDDEN
            cb.state = uiconst.UI_NORMAL

        wnd.sr.stealth = uicontrols.Checkbox(text='Stealth', parent=c, configName='consolestealth', retval=0, checked=settings.user.ui.Get('consolestealth', 0), callback=checker)
        checker(wnd.sr.stealth)
        output = wnd.sr.output = uicontrols.Edit(setvalue=self.outputcontents_default, parent=o, readonly=1)
        output.autoScrollToBottom = 1
        uicore.registry.SetFocus(input)

    def Hide(self, *args):
        if self.wnd:
            settings.user.ui.Set('consoleoutputheight', self.wnd.sr.o.height)
            self.consolecontents = self.wnd.sr.input.GetValue()
            self.outputcontents = self.wnd.sr.output.GetValue()
            self.wnd.Close()
        self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()
