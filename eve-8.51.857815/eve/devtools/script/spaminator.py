#Embedded file name: eve/devtools/script\spaminator.py
import service
import uicontrols
import uiprimitives
import blue
import uix
import uiutil
import listentry
import util
import yaml
import log
import chat
import uicls
import uthread
import carbonui.const as uiconst
SERVICENAME = 'spaminator'
SCROLL_HEADERS = ['Action',
 'Time',
 'Channel',
 'Character',
 'User',
 'IP Address',
 'Match',
 'Message']
CAPTION = 'ISK Spaminator v0.6'

class ISKSpammerToolSvc(service.Service):
    __module__ = __name__
    __doc__ = 'ISK Spaminator Tool'
    __exportedcalls__ = {'Show': []}
    __notifyevents__ = ['ProcessRestartUI', 'OnClientReady', 'OnLSC']
    __dependencies__ = []
    __guid__ = 'svc.spaminator'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME.capitalize()
    __neocommenuitem__ = (('ISK Spaminator', None), 'Show', service.ROLE_GML)

    def Run(self, *args):
        sm.RegisterNotify(self)
        self.wnd = None
        self.checked = {}
        self.output = ''
        self.isRunning = False
        self.config = {'detention': [],
         'notify': [],
         'ipAddresses': []}
        self.configFileName = ''
        self.suspects = set()
        self.lookedUpChars = {}
        self.scrolllist = []
        self.startedTime = None
        self.stats = None
        self.path = prefs.GetValue('SpaminatorWorkFolder', 'c:\\temp') + '\\'
        self.state = service.SERVICE_RUNNING

    def Start(self):
        uthread.new(self.DoStart)

    def DoStart(self):
        self.Run()
        self.Show()

    def LoadConfig(self):
        configFileName = self.path + 'config.ini'
        self.LogInfo('Loading config from', configFileName)
        inputfile = file(configFileName, 'r')
        self.config = yaml.load(inputfile)
        inputfile.close()
        if type(self.config) != type({}):
            self.config = {}
            return
        for k, v in self.config.iteritems():
            if type(v) == type([]):
                txt = '<br>'.join(v)
            else:
                txt = ''
            if k == 'detention':
                self.wnd.sr.detentionWindow.SetValue(txt)
            elif k == 'notify':
                self.wnd.sr.notifyWindow.SetValue(txt)

    def SaveConfig(self):
        txt = self.wnd.sr.detentionWindow.GetValue()
        detention = txt.split('<br>')
        self.config['detention'] = detention
        txt = self.wnd.sr.notifyWindow.GetValue()
        notify = txt.split('<br>')
        self.config['notify'] = notify
        self.DoSaveConfig()

    def DoSaveConfig(self):
        configFileName = self.path + 'config.ini'
        o = file(configFileName, 'w')
        yaml.safe_dump(self.config, o, default_flow_style=False)
        o.close()

    def Show(self):
        if self.wnd and 0:
            self.wnd.Maximize()
            return
        self.wnd = wnd = uicontrols.Window.GetIfOpen(windowID='spaminator')
        if not wnd:
            self.wnd = wnd = uicontrols.Window.Open(windowID='spaminator')
            wnd.DoClose = self.Hide
            wnd.SetWndIcon(None)
            wnd.SetTopparentHeight(0)
            wnd.SetCaption(CAPTION)
            wnd.SetMinSize([520, 256])
            main = uiprimitives.Container(name='main', parent=uiutil.FindChild(wnd, 'main'), left=0, top=0)
            buttonContainer = uiprimitives.Container(name='bottom', parent=main, align=uiconst.TOBOTTOM, height=30)
            mainCont = uiprimitives.Container(name='mainCont', parent=main, isClipper=1, top=8, left=8)
            settingsCont = uiprimitives.Container(name='settingsCont', parent=main, isClipper=1, top=8, left=8)
            tabs = [['Main',
              mainCont,
              self,
              'main'], ['Settings',
              settingsCont,
              self,
              'settings']]
            self.tabs = uicontrols.TabGroup(name='tabparent', parent=main, idx=1).Startup(tabs, 'monitortabs')
            leftContainer = uiprimitives.Container(name='left', parent=settingsCont, align=uiconst.TOLEFT, width=250)
            rightContainer = uiprimitives.Container(name='right', parent=settingsCont, align=uiconst.TOLEFT, width=250)
            contents = ''
            tc = uiprimitives.Container(name='titleContLeft', parent=leftContainer, align=uiconst.TOTOP, height=16)
            uicontrols.Label(text='Automatic detention:', parent=tc, width=160, align=uiconst.TOPLEFT)
            tc = uiprimitives.Container(name='titleContRight', parent=rightContainer, align=uiconst.TOTOP, height=16)
            uicontrols.Label(text='Notify:', parent=tc, width=100, align=uiconst.TOPLEFT)
            self.wnd.sr.detentionWindow = uicls.EditPlainText(setvalue='', parent=leftContainer, align=uiconst.TOALL)
            self.wnd.sr.notifyWindow = uicls.EditPlainText(setvalue='', parent=rightContainer, align=uiconst.TOALL)
            self.scrollCont = uiprimitives.Container(name='scrollCont', parent=mainCont, align=uiconst.TOALL)
            self.scroll = uicontrols.Scroll(name='scroll', parent=self.scrollCont, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding), align=uiconst.TOALL)
            self.scroll.Startup()
            self.scroll.id = 'iskspammerscroll'
            self.scroll.multiSelect = 0
            self.scroll.Load(contentList=[], headers=SCROLL_HEADERS, scrolltotop=1)
            btns = uicontrols.ButtonGroup(btns=[['Join Channels',
              self.JoinChannels,
              (),
              None], ['Reset',
              self.Reset,
              (),
              None], ['Start/Stop',
              self.ToggleStartWatching,
              (),
              None]], parent=buttonContainer)
        self.LoadConfig()

    def JoinChannels(self, *args):
        l = sm.GetService('LSC')
        channels = l.GetChannels()
        channels = [ c.channelID for c in channels if c.estimatedMemberCount > 10 or type(c.channelID) == type(()) ]
        self.LogInfo('Joining', len(channels), 'chat channels')
        l.JoinChannels(channels)

    def Reset(self, *args):
        self.scroll.Load(contentList=[], headers=SCROLL_HEADERS, scrolltotop=1)
        self.StartWatching(False)
        self.StartWatching(True)

    def ToggleStartWatching(self, *args):
        isit = not self.isRunning
        self.StartWatching(isit)

    def StartWatching(self, isit):
        self.SaveConfig()
        self.isRunning = isit
        if self.isRunning:
            txt = 'ISK Spaminator tool started @ %s' % util.FmtDate(blue.os.GetTime())
            self.LogNotice(txt)
            self.startedTime = util.FmtDate(blue.os.GetTime(), 'ls')
            self.stats = {'numMessages': 0,
             'numNotify': 0,
             'numDetention': 0,
             'numServerCalls': 0}
            self.wnd.SetCaption(CAPTION + ' (RUNNING)')
        elif self.startedTime:
            txt = 'ISK Spammer tool stopped @ %s' % util.FmtDate(blue.os.GetTime())
            self.LogNotice(txt)
            statsFileName = self.path + 'stats.txt'
            o = file(statsFileName, 'a')
            o.write('ISK Spammer tool running from %s to %s\n%s\n' % (self.startedTime, util.FmtDate(blue.os.GetTime(), 'ls'), '=' * 60))
            for k, v in self.stats.iteritems():
                o.write('%s:\t%s\n' % (k, v))

            o.write('\n\n')
            o.close()
            self.startedTime = None
            self.wnd.SetCaption(CAPTION + ' (stopped)')
        else:
            return
        eve.Message('CustomNotify', {'notify': txt})

    def Hide(self, *args):
        self.StartWatching(False)
        if self.wnd:
            self.wnd.Close()
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def OnClientReady(self, *args):
        pass

    def GetCharInfo(self, charID):
        if charID not in self.lookedUpChars:
            self.stats['numServerCalls'] += 1
            info = sm.RemoteSvc('userSvc').GetInfoFromCharID(charID)
            ipAddress = info.connectEvents[0].ipAddress
            info.ipAddress = ipAddress
            self.lookedUpChars[charID] = info
        info = self.lookedUpChars[charID]
        return info

    def SanitizeMessage(self, message):
        message = message.replace(u'\uff25', 'E')
        message = message.replace(u'\uff36', 'V')
        message = message.replace(u'\uff2c', 'L')
        message = message.replace(u'\uff33', 'S')
        message = message.replace(u'\uff32', 'R')
        message = message.replace(u'\uff21', 'A')
        message = message.replace(u'\uff26', 'F')
        message = message.replace(u'\u3000', ' ')
        message = message.replace(u'\uff34', 'T')
        message = message.replace(u'\uff24', 'D')
        message = message.replace(u'\uff2e', 'N')
        message = message.replace(u'\uff27', 'G')
        message = message.replace(u'\uff35', 'U')
        message = message.replace('0', 'O')
        return message

    def OnLSC(self, channelID, estimatedMemberCount, method, who, args):
        channelName = chat.GetDisplayName(channelID)
        if method != 'SendMessage' or not self.isRunning:
            return
        self.stats['numMessages'] += 1
        message = args[0]
        sanitizedMessage = self.SanitizeMessage(message)
        message = unicode(message).encode('UTF-8')
        charID = who[2][0]
        charName = who[2][1]
        whoAllianceID, whoCorpID, who, whoRole, whoCorpRole, whoWarFactionID = who
        suspect = self.IsMessageSuspect(sanitizedMessage)
        if suspect is None:
            return
        try:
            self.LogInfo('There is something suspect from character %s: %s...' % (who, suspect))
        except:
            pass

        info = self.GetCharInfo(charID)
        userID = info.charStatic.userID
        userName = info.userStatic.userName
        fullName = info.userStatic.fullName
        email = info.userStatic.eMail
        userType = info.userDynamic.userType
        ipAddress = info.ipAddress
        isIpMatch = False
        if suspect[0] == 2:
            if ipAddress in self.config['ipAddresses'] and 0:
                self.LogInfo('Upgrading from notify to detention because of IP relationship', ipAddress)
                suspect[0] = 1
                isIpMatch = True
        if suspect[0]:
            if whoRole & service.ROLE_NEWBIE == 0:
                self.LogInfo('... %s is not a newbie.' % who[1])
                return
            if not util.IsNPC(whoCorpID):
                self.LogInfo('... %s is in a player corp.' % who[1])
                return
        if charID in self.suspects:
            self.LogInfo('... %s is already a suspect.' % who[1])
            return
        message = message.decode('UTF-8', 'replace')
        cleanmessage = message.replace('>', '&gt;').replace('<', '&lt;')
        try:
            self.LogInfo('... %s is really a suspect for saying %s!' % (charName, message))
        except:
            self.LogInfo('... %s is really a suspect for saying %s!' % (charName, 'unknown'))

        self.lookedUpChars[charID] = info
        if suspect[0] == 1:
            act = '<b>DETENTION</b>'
            self.stats['numDetention'] += 1
            try:
                self.LogError('I will place', who[1], 'in detention for saying', message)
            except:
                self.LogError('I will place', who[1], 'in detention for saying', 'unknown')

        else:
            act = '<color=red>NOTIFY</color>'
            self.stats['numNotify'] += 1
            try:
                self.LogError('I will notify user of', who[1], 'for saying', message)
            except:
                self.LogError('I will notify user of', who[1], 'for saying', 'unknown')

        self.suspects.add(charID)
        act2 = ''
        try:
            if suspect[0] == 1:
                self.PlaceInDetention(charID)
        except Exception as e:
            raise

        ip = ipAddress
        if isIpMatch:
            ip = '<color=red>%s</color>' % ip
        matchstring = suspect[1]
        label = '%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s' % (act,
         util.FmtDate(blue.os.GetTime(), 'ss'),
         channelName,
         charName,
         userName,
         ip,
         matchstring,
         cleanmessage[:64])
        kv = {}
        data = util.KeyVal(charID=charID, userID=userID, label=label, GetMenu=self.GetSpammerMenu, hint=cleanmessage, data=info)
        l = listentry.Get('Generic', data=data)
        self.scrolllist.append(l)
        self.scroll.AddEntries(0, [l])
        self.WriteLog(label)

    def WriteLog(self, label):
        try:
            txt = label.replace('<t>', '\t')
            f = open(self.path + 'spamlog.txt', 'a')
            f.write('%s\n' % txt)
            f.close()
        except:
            log.LogException()

    def AddSnippetToAutodetentionList(self, txt):
        wnd = sm.GetService('window').GetWindow('detentionsnippet', decoClass=DetentionSnippetWnd, create=1)
        wnd.Load(txt)
        if getattr(wnd, 'reason', None):
            self.config['detention'].append(wnd.reason)
            self.DoSaveConfig()
            self.LoadConfig()

    def GetSpammerMenu(self, entry):
        info = entry.sr.node.data
        charID = entry.sr.node.charID
        userID = entry.sr.node.userID
        m = []
        m.append(['Gag ISK Spammer', self.AskPlaceInDetention, (charID,)])
        m.append(None)
        m.append(['Add snippet to auto detention list', self.AddSnippetToAutodetentionList, (entry.hint,)])
        m.append(None)
        m.append(['ESP - View Character', self.ViewInESP, ('character.py?action=Character&characterID=%s' % charID,)])
        m.append(['ESP - View User', self.ViewInESP, ('users.py?action=User&userID=%s' % userID,)])
        m.append(['ESP - View IP Logs', self.ViewInESP, ('users.py?action=IPLogs&logID=None&Post=Submit&IPID=%s' % info.connectEvents[0].ipAddressID,)])
        m.append(['ESP - View Aliases', self.ViewInESP, ('users.py?action=Aliases&simple=1&userID=%s&check=0' % userID,)])
        return m

    def ViewInESP(self, action):
        espaddy = '87.237.38.201:50001/gm'
        blue.os.ShellExecute('http://%s/%s' % (espaddy, action))

    def IsMessageSuspect(self, message):
        detention = self.config.get('detention', [])
        notify = self.config.get('notify', [])
        m = message
        try:
            m = message.decode('UTF-8', 'replace').lower()
        except:
            pass

        for i in detention:
            if len(i) > 0 and m.find(i.lower()) >= 0:
                return [1, i.lower()]

        for i in notify:
            if len(i) > 0 and m.find(i.lower()) >= 0:
                return [2, i.lower()]

    def PlaceInDetention(self, charID):
        ipAddresses = self.config['ipAddresses']
        info = self.GetCharInfo(charID)
        if info.ipAddress not in ipAddresses:
            self.config['ipAddresses'].append(info.ipAddress)
        self.SaveConfig()
        sm.GetService('menu').SlashCmd('/gagiskspammer %s' % charID)
        eve.Message('CustomNotify', {'notify': '%s has been placed in detention for ISK Spamming' % cfg.eveowners.Get(charID).name})

    def AskPlaceInDetention(self, charID):
        if eve.Message('ConfirmGagIskSpammer', {'name': cfg.eveowners.Get(charID).name}, uix.YESNO) != uix.ID_YES:
            return
        self.PlaceInDetention(charID)


class DetentionSnippetWnd(uicontrols.Window):
    __guid__ = 'form.DetentionSnippetWnd'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'station_inflight'
        self.SetCaption('Add snippet to detention list')
        self.SetMinSize([256, 256], 1)
        self.MakeUnResizeable()
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.sr.main = uiutil.GetChild(self, 'main')
        textparent = uiprimitives.Container(name='push', align=uiconst.TOTOP, height=48, parent=self.sr.main)
        uicontrols.Label(text='Remove everything from the message below except\nfor the snippet that you want to add to the automatic \ndetention list', parent=textparent, left=6, top=3, fontsize=12, width=250, align=uiconst.TOPLEFT)
        self.sr.reason = uicls.EditPlainText(setvalue='', parent=self.sr.main, align=uiconst.TOPLEFT, width=248, height=150, top=50)
        mainbtns = uicontrols.ButtonGroup(btns=[['Add snippet',
          self.Confirm,
          (),
          81], ['Cancel',
          self.Cancel,
          (),
          81]])
        self.sr.main.children.insert(0, mainbtns)

    def Cancel(self, *args):
        self.SetModalResult(uix.ID_CANCEL)

    def Confirm(self, *args):
        self.reason = self.sr.reason.GetValue()
        self.SetModalResult(uix.ID_OK)

    def Load(self, txt):
        self.SetCaption('bla')
        self.sr.reason.SetValue(txt)
        uicore.registry.SetFocus(self.sr.reason)
        self.state = uiconst.UI_NORMAL
        self.ShowModal()


exports = {'form.DetentionSnippetWnd': DetentionSnippetWnd}
