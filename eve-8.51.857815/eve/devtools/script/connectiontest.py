#Embedded file name: eve/devtools/script\connectiontest.py
import uix
import uiutil
import util
import carbonui.const as uiconst
import uiprimitives
import uicontrols

class ConnectionLoopTest(uicontrols.Window):
    __guid__ = 'form.ConnLoop'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        w = 270
        h = 237
        self.HideMainIcon()
        self.SetTopparentHeight(0)
        self.SetMinSize([w, h])
        self.SetHeight(h)
        self.LockWidth(w)
        self.MakeUnResizeable()
        self.SetCaption('Client Connection Test')
        self.Begin()

    def Begin(self, *args):
        margin = const.defaultPadding
        btns = uicontrols.ButtonGroup(btns=[['Use Current',
          self.Current,
          None,
          81], ['Defaults',
          self.Defaults,
          None,
          81], ['Save',
          self.Save,
          None,
          81]])
        self.buttons = uiprimitives.Container(name='buttons', parent=self.sr.main, align=uiconst.TOBOTTOM, height=20)
        self.buttons.children.insert(0, btns)
        self.currentBtn = uiutil.GetChild(self, 'Use Current_Btn')
        self.currentBtn.hint = 'This button sets the account details to the current logged in account'
        self.defaultBtn = uiutil.GetChild(self, 'Defaults_Btn')
        self.defaultBtn.hint = 'This resets all values to predetermined defaults'
        border = uiprimitives.Container(name='border', align=uiconst.TOALL, parent=self.sr.main, pos=(margin,
         margin,
         margin,
         margin))
        border.height = margin + 1
        uiprimitives.Line(parent=border, align=uiconst.TOTOP, color=(1.0, 1.0, 1.0, 0.2))
        uiprimitives.Line(parent=border, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.2))
        uiprimitives.Line(parent=border, align=uiconst.TORIGHT, color=(1.0, 1.0, 1.0, 0.2))
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TORIGHT, width=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOLEFT, width=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        uix.GetContainerHeader('Connect Options:', self.sr.main, bothlines=0)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TORIGHT, width=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOLEFT, width=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)

        def Logon(cb):
            checked = cb.GetValue()
            prefs.SetValue('bmnextrun', checked)
            if checked:
                cb.hint = 'This will auto connect the next time <b>exefile</b> is initiated.'
            else:
                cb.hint = 'No automated processes will be undertaken.'
            cb.state = uiconst.UI_HIDDEN
            cb.state = uiconst.UI_NORMAL

        def Loop(cb):
            checked = cb.GetValue()
            prefs.SetValue('csloopenabled', checked)
            if checked:
                count = 1
                if hasattr(self, 'count'):
                    count = self.count.GetValue()
                prefs.SetValue('cscount', count)
                cb.hint = 'Disables the loop ability of the connection tool.'
            else:
                cb.hint = 'Enables the loop ability of the connection tool.'
            cb.state = uiconst.UI_HIDDEN
            cb.state = uiconst.UI_NORMAL

        self.runcb = uicontrols.Checkbox(text='Run at next logon', parent=self.sr.main, retval=0, configName='cbLogon', checked=prefs.GetValue('bmnextrun', 0), callback=Logon, pos=(0, 0, 145, 0))
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpCount = uiprimitives.Container(name='gpCount', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        self.countcb = uicontrols.Checkbox(text="Loop for 'x' connections", parent=gpCount, retval=0, configName='cbLoopForXRuns', checked=prefs.GetValue('csloopenabled', 0), callback=Loop, pos=(0, 0, 145, 0), align=uiconst.TOLEFT)
        self.count = uicontrols.SinglelineEdit(name='editLoopCount', parent=gpCount, width=80, height=20, align=uiconst.TORIGHT, ints=(1, 99999), maxLength=5)
        self.count.SetValue(prefs.GetValue('cscount', '1'))
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        uiprimitives.Line(parent=push, align=uiconst.TOTOP, color=(1.0, 1.0, 1.0, 0.2))
        gpDuration = uiprimitives.Container(name='gpDuration', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        text = uicontrols.Label(text='Duration per cycle (seconds)', name='textLoopDuration', parent=gpDuration, align=uiconst.TOLEFT, top=5, left=margin - 1, width=170, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        text.rectTop = -2
        self.duration = uicontrols.SinglelineEdit(name='editLoopDuration', parent=gpDuration, width=80, height=20, align=uiconst.TORIGHT, ints=(1, 99999), maxLength=5)
        self.duration.SetValue(prefs.GetValue('csduration', '180'))
        Logon(self.runcb)
        Loop(self.countcb)
        EDITWIDTH = 150
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        uix.GetContainerHeader('Account Details:', self.sr.main, bothlines=1, xmargin=-margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpServer = uiprimitives.Container(name='gpServer', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textServer = uicontrols.Label(text='Server IP', name='textServerIP', parent=gpServer, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1)
        textServer.rectTop = -2
        self.serverip = uicontrols.SinglelineEdit(name='editServerIP', parent=gpServer, width=EDITWIDTH, height=20, align=uiconst.TORIGHT)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpUserName = uiprimitives.Container(name='gpUserName', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textUserName = uicontrols.Label(text='Account Name', name='textUserName', parent=gpUserName, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        textUserName.rectTop = -2
        self.username = uicontrols.SinglelineEdit(name='editUserName', parent=gpUserName, width=EDITWIDTH, height=20, align=uiconst.TORIGHT)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpUserPass = uiprimitives.Container(name='gpUserPass', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textUserPass = uicontrols.Label(text='Account Password', name='textUserPass', parent=gpUserPass, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        textUserPass.rectTop = -2
        self.userpass = uicontrols.SinglelineEdit(name='editUserPass', parent=gpUserPass, width=EDITWIDTH, height=20, align=uiconst.TORIGHT, passwordCharacter='\xe2\x80\xa2')
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpCharName = uiprimitives.Container(name='gpCharName', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textCharName = uicontrols.Label(text='Character Name', name='textCharName', parent=gpCharName, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1)
        textCharName.rectTop = -2
        self.charname = uicontrols.SinglelineEdit(name='editCharName', parent=gpCharName, width=EDITWIDTH, height=20, align=uiconst.TORIGHT)
        accdetails = hasattr(prefs, 'bmaccount')
        if accdetails:
            acc = prefs.GetValue('bmaccount', None)
            try:
                if acc is not None:
                    server, user, userpass, userchar = acc.split(':')
                    self.serverip.SetValue(server)
                    self.username.SetValue(user)
                    self.userpass.SetValue(userpass)
                    self.charname.SetValue(userchar)
            except:
                server = ''
                user = ''
                userpass = ''
                userchar = ''
                sys.exc_clear()

    def Current(self, *args):
        server = util.GetServerName()
        user = sm.RemoteSvc('userSvc').GetUserName(eve.session.userid)
        character = cfg.eveowners.Get(eve.session.charid).name
        fields = [('serverip', server),
         ('username', user),
         ('userpass', ''),
         ('charname', character)]
        for entry, value in fields:
            a = getattr(self, entry)
            a.SetValue(value)

    def Defaults(self, *args):
        fields = [('count', '1'),
         ('duration', '180'),
         ('serverip', ''),
         ('username', ''),
         ('userpass', ''),
         ('charname', '')]
        for entry, default in fields:
            a = getattr(self, entry)
            a.SetValue(default)

    def Save(self, *args):
        fields = [('count', 'cscount'), ('duration', 'csduration')]
        for attribute, prefsVal in fields:
            value = getattr(self, attribute).GetValue()
            setattr(prefs, prefsVal, value)

        s = self.serverip.GetValue()
        u = self.username.GetValue()
        p = self.userpass.GetValue()
        c = self.charname.GetValue()
        output = '%s:%s:%s:%s' % (s,
         u,
         p,
         c)
        setattr(prefs, 'bmaccount', output)
