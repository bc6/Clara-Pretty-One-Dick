#Embedded file name: eve/devtools/script\svc_cspam.py
import uicontrols
import uiprimitives
import sys
import blue
import os
import random
import uix
import uiutil
import form
import listentry
import chat
import menu
import types
import uthread
import service
import carbonui.const as uiconst
from service import *
FILENAME = 'spam.txt'
DEFAULTLINES = ['Lorem ipsum dolor sit amet',
 'consectetur adipisicing elit',
 'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
 'Ut enim ad minim veniam',
 'quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.',
 'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.',
 'Excepteur sint occaecat cupidatat non proident',
 'sunt in culpa qui officia deserunt mollit anim id est laborum']
DEFAULTTMIN = 5
DEFAULTTMAX = 20
EDITWIDTH = 30
SPECIALVARS = [('regionid', 'Region'),
 ('constellationid', 'Constellation'),
 ('solarsystemid2', 'Local'),
 ('corpid', 'Corp'),
 ('warfactionid', 'Militia'),
 ('allianceid', 'Alliance'),
 ('fleetid', 'Fleet'),
 ('squadid', 'Squad')]

class CSpam(listentry.Generic):
    """
        Custom listentry class with right click menus
    """
    __guid__ = 'listentry.CSpam'

    def GetMenu(self):
        """
            Right click menu options
        """
        self.multiple = False
        n = self.sr.node
        count = len(n.scroll.GetSelectedNodes(n))
        if count > 1:
            self.multiple = True
            ret = [('Join Channels', self.Join, ()), ('Remove Channels', self.Delete, ())]
        else:
            ret = [('Join Channel', self.Join, ()), ('Remove Channel', self.Delete, ())]
        return ret

    def Join(self):
        n = self.sr.node
        if self.multiple:
            nodes = n.scroll.GetSelectedNodes(n)
            for node in nodes:
                n.Join(node.channelID)

        else:
            n.Join(n.channelID)

    def Delete(self):
        n = self.sr.node
        if self.multiple:
            nodes = n.scroll.GetSelectedNodes(n)
            for node in nodes:
                n.Delete(node.cname)

        else:
            n.Delete(n.cname)


class ChannelSpam(service.Service):
    __module__ = __name__
    __guid__ = 'svc.cspam'
    __servicename__ = 'cspam'
    __displayname__ = 'cspam'
    __exportedcalls__ = {'Show': [ROLE_GML],
     'GetChannels': [ROLE_GML],
     'ClearChannels': [ROLE_GML],
     'Setup': [ROLE_GML],
     'GetName': [ROLE_GML],
     'AddToList': [ROLE_GML],
     'DeleteFromList': [ROLE_GML],
     'LookupChannel': [ROLE_GML],
     'AddChannel': [ROLE_GML],
     'GetChannel': [ROLE_GML]}
    __notifyevents__ = ['OnSessionChanged']

    def __init__(self):
        service.Service.__init__(self)
        self.channels = {}

    def OnSessionChanged(self, isRemote, session, change):
        for var, text in SPECIALVARS:
            if var in change:
                if text in self.channels:
                    self.channels[text] = ((var, getattr(eve.session, var)),)

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        Service.Run(self, memStream)
        self.state = SERVICE_RUNNING

    def Stop(self, memStream = None):
        self.state = SERVICE_STOP_PENDING
        Service.Stop(self, memStream)
        self.state = SERVICE_STOPPED

    def Setup(self, min = DEFAULTTMIN, max = DEFAULTTMAX, more = None, *args):
        if more is None:
            return
        if not len(self.channels.keys()):
            return
        self.min = min
        self.max = max
        self.runs = more
        if not hasattr(self, 'lines'):
            self.Parse()
        self.Go()

    def Parse(self, *args):
        INSIDERDIR = sm.StartService('insider').GetInsiderDir()
        target = os.path.join(INSIDERDIR, FILENAME)
        file = blue.classes.CreateInstance('blue.ResFile')
        if file.Open(target, 0):
            obj = file.read()
            self.lines = obj.split('\r\n')
            file.Close()
        else:
            self.lines = DEFAULTLINES

    def Go(self, *args):
        """
            This makes it go places!
        """
        randDelay = self.min
        randIdx = 0
        randIdx2 = 0
        randChan = [False, True][bool(len(self.channels.keys()) - 1)]
        randTime = [True, False][self.min == self.max]
        randLine = [False, True][bool(len(self.lines) - 1)]
        while self.runs:
            self.runs -= 1
            prefs.SetValue('spamcount', self.runs)
            if randTime:
                randDelay = random.randint(self.min, self.max)
            if randChan:
                randIdx = random.randint(0, len(self.channels.keys()) - 1)
            if randLine:
                randIdx2 = random.randint(0, len(self.lines) - 1)
            key = self.channels.keys()[randIdx]
            channel = self.channels[key]
            try:
                if channel not in sm.StartService('LSC').channels:
                    sm.StartService('LSC').JoinOrLeaveChannel(channel)
            except ValueError:
                sys.exc_clear()
                continue

            message = self.lines[randIdx2]
            for a in xrange(randDelay, 0, -1):
                blue.pyos.synchro.SleepWallclock(1000)

            count = prefs.GetValue('spamcount', 0)
            if not count:
                break
            try:
                c = sm.StartService('LSC').GetChannelWindow(channel)
                c.Speak(message, eve.session.charid, localEcho=True)
                sm.StartService('LSC').SendMessage(channel, message)
            except RuntimeError:
                sys.exc_clear()

        eve.Message('CustomNotify', {'notify': 'Spam test complete, all done!'})

    def Show(self, *args):
        form.cspam.Open()

    def ClearChannels(self, *args):
        self.channels = {}

    def GetChannels(self, *args):
        return self.channels

    def GetDict(self, *args):
        if hasattr(self, 'dict'):
            return self.dict
        else:
            return {}

    def MakeDict(self, *args):
        """
            Creates a local dictionary cache of channels
        """
        self.dict = {}
        for channel in sm.StartService('LSC').GetChannels(refresh=1):
            self.dict[chat.GetDisplayName(channel.channelID).lower()] = channel
            self.dict[channel.displayName.lower()] = channel

    def GetChannel(self, name = None, *args):
        """
            Returns the channel info for the specified channel
        """
        if name is None:
            return
        if not hasattr(self, 'dict'):
            self.MakeDict()
        if name.lower() in self.dict:
            return self.dict[name.lower()]

    def AddChannel(self, name = None, *args):
        """
            Creates a channel and forces an update to the dictionary
        """
        if name is None:
            return
        ret = sm.RemoteSvc('LSC').CreateChannel(name, joinExisting=True, memberless=False, create=True)
        self.MakeDict()

    def AddToList(self, cname = None, cid = None, *args):
        """
            Adds the specified channelID to the main list of channels to post in
        """
        if cname is None:
            return
        if cid is None:
            return
        name = self.GetName(cname, cid)
        self.channels[name] = cid

    def DeleteFromList(self, key = None, *args):
        if key is None:
            return
        del self.channels[key]

    def LookupChannel(self, name = None, *args):
        """
            Checks to see if a channel is in the local cache. 
        """
        if name is None:
            return
        else:
            if not hasattr(self, 'dict'):
                self.MakeDict()
            if name in self.dict:
                return True
            return False

    def JoinChannel(self, id = None, *args):
        """
            Joins the specified channelID
        """
        if id is None:
            return
        if not sm.StartService('LSC').IsJoined(id):
            sm.StartService('LSC').JoinOrLeaveChannel(channelID=id, onlyJoin=True)

    def GetName(self, dictName = None, dictID = None, *args):
        if dictID is None:
            return
        if not hasattr(self, 'dict'):
            self.MakeDict()
        if type(dictID) is types.IntType:
            if dictName in self.dict:
                info = self.dict[dictName]
            else:
                tmp = [ c for c in sm.StartService('LSC').GetChannels(refresh=1) if c.channelID == dictID ]
                if len(tmp):
                    info = tmp[0]
                else:
                    return
            name = info.displayName
            length = len(name.split('\\'))
            if length > 1:
                name = name.split('\\')[1]
        else:
            name = chat.GetDisplayName(dictID)
        return name


class ChannelSpamForm(uicontrols.Window):
    __guid__ = 'form.cspam'
    __notifyevents__ = ['OnSessionChanged']
    default_windowID = 'cspam'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        w = 150
        h = 300
        self.HideMainIcon()
        self.SetTopparentHeight(0)
        self.SetMinSize([w, h])
        self.SetHeight(h)
        self.SetCaption('Spambot 3000')
        self.svc = sm.StartService('cspam')
        self.channels = {}
        uthread.new(self.GetSystemChannels, True)
        self.Begin()

    def OnSessionChanged(self, isRemote, session, change):
        """
            Updates the local list of channels and forces a refresh of the scroll as a result
        """
        for var, text in SPECIALVARS:
            if var in change:
                if text in self.channels:
                    self.channels[text] = ((var, getattr(eve.session, var)),)
                    self.Refresh()

    def Begin(self, *args):
        margin = const.defaultPadding
        btns = uicontrols.ButtonGroup(btns=[['Add',
          self.AddChannel,
          None,
          81], ['Begin',
          self.Start,
          None,
          81], ['Stop',
          self.Cease,
          None,
          81]])
        self.buttons = uiprimitives.Container(name='buttons', parent=self.sr.main, align=uiconst.TOBOTTOM, height=20)
        self.buttons.children.insert(0, btns)
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
        uix.GetContainerHeader('Twiddle my options...', self.sr.main, bothlines=0)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TORIGHT, width=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOLEFT, width=margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        defaultval = '%s:%s' % (DEFAULTTMIN, DEFAULTTMAX)
        minVal, maxVal = str(prefs.GetValue('spamdelay', defaultval)).split(':')
        try:
            minVal = int(minVal)
        except ValueError:
            sys.exc_clear()
            minVal = DEFAULTTMIN

        try:
            maxVal = int(maxVal)
        except ValueError:
            sys.exc_clear()
            maxVal = DEFAULTTMAX

        amount = str(prefs.GetValue('spamcount', 0))
        gpMin = uiprimitives.Container(name='gpMin', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textMin = uicontrols.Label(text='Minimum Duration', name='textMin', parent=gpMin, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        textMin.rectTop = -2
        self.min = uicontrols.SinglelineEdit(name='editMin', parent=gpMin, width=EDITWIDTH, height=20, align=uiconst.TORIGHT)
        self.min.SetValue(str(minVal))
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpMax = uiprimitives.Container(name='gpMax', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textMax = uicontrols.Label(text='Maximum Duration', name='textMax', parent=gpMax, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        textMax.rectTop = -2
        self.max = uicontrols.SinglelineEdit(name='editMax', parent=gpMax, width=EDITWIDTH, height=20, align=uiconst.TORIGHT)
        self.max.SetValue(str(maxVal))
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        gpCount = uiprimitives.Container(name='gpCount', parent=self.sr.main, align=uiconst.TOTOP, height=16)
        textCount = uicontrols.Label(text='Amount', name='textCount', parent=gpCount, align=uiconst.TOLEFT, height=12, top=5, left=margin - 1, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        textCount.rectTop = -2
        self.count = uicontrols.SinglelineEdit(name='editCount', parent=gpCount, width=EDITWIDTH, height=20, align=uiconst.TORIGHT)
        self.count.SetValue(amount)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        uix.GetContainerHeader('Spamming in...', self.sr.main, bothlines=1, xmargin=-margin)
        push = uiprimitives.Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=margin)
        self.scroll = uicontrols.Scroll(parent=self.sr.main, height=145)
        self.scroll.height = margin * 2
        self.scroll.sr.id = 'chatchannels'
        self.scroll.Load(contentList=[], headers=['Channels', 'ID'])
        self.svc.ClearChannels()

    def Start(self, *args):
        """
            Grabs all the variables from the form and passes them to the service
        """
        minVal = int(self.min.GetValue())
        maxVal = int(self.max.GetValue())
        minVal = min(minVal, 1)
        maxVal = max(minVal, maxVal)
        amount = int(self.count.GetValue())
        delay = '%s:%s' % (minVal, maxVal)
        prefs.SetValue('spamdelay', delay)
        prefs.SetValue('spamcount', amount)
        self.svc.Setup(minVal, maxVal, amount)

    def Refresh(self, *args):
        """
            Refresh funciton to reload the scrolllist on changes
        """
        contentList = []
        for k, v in self.channels.iteritems():
            name = self.svc.GetName(k, v)
            contentList.append(listentry.Get('CSpam', {'label': '%s<t>%s' % (name, v),
             'hint': '<b>Name:</b> %s<br><b>ID:</b> %s' % (name, v),
             'channelID': v,
             'cname': name,
             'Delete': self.DeleteChannel,
             'Join': self.Join}))

        self.scroll.Load(contentList=contentList, headers=['Channels', 'ID'])

    def Cease(self, *args):
        prefs.SetValue('spamcount', 0)

    def GetSystemChannels(self, refresh = False, *args):
        """
            Parse the entire list of channels to a drop down menu format
        """
        if not refresh:
            if hasattr(self, 'systemcache'):
                return self.systemcache
            else:
                return []

        def Add(special, text):
            if text not in self.channels:
                self.svc.AddToList(text, special)
                self.channels[text] = special
                self.Refresh()

        m = []
        n = []
        o = []
        p = []
        channels = sm.StartService('LSC').GetChannels(refresh=1)
        for c in channels:
            if not hasattr(c, 'ownerID') or hasattr(c, 'ownerID') and getattr(c, 'ownerID') == const.ownerSystem:
                sub = c.displayName.split('\\')
                if len(sub) > 1:
                    name = sub[0]
                    fieldname = 'channnel_%s' % name
                    if fieldname not in n:
                        n.append(fieldname)
                    if not hasattr(self, fieldname):
                        setattr(self, fieldname, [])
                    o = getattr(self, fieldname)
                    o.append((sub[1], c.channelID))
                else:
                    m.append((c.displayName, Add, (c.channelID, c.displayName)))

        cid = 1
        name = self.svc.GetName(dictID=cid)
        m.append((name, Add, (cid, name)))
        n.sort()
        for c in n:
            q = getattr(self, c)
            q.sort()
            name = c.split('_')[1]
            p = []
            for cid in q:
                p.append((cid[0], Add, (cid[1], cid[0])))

            m.append((name, p))

        self.systemcache = m
        return m

    def GetCurrentChannels(self, *args):
        """
            Returns the current channels you're in
        """

        def Add(special, text):
            if text not in self.channels:
                self.svc.AddToList(text, special)
                self.channels[text] = special
                self.Refresh()

        m = []
        list = [ cid for cid in sm.StartService('LSC').channels ]
        if len(list) > 2:
            for cid in list:
                name = self.svc.GetName(dictID=cid)
                if name is not None:
                    m.append((name, Add, (cid, name)))

        else:
            m.append(('None', None))
        m.sort()
        return m

    def AddChannel(self, *args):
        """
            Method to list all possible normal channels you would use and allow you to
            add your own custom channel names
        """
        m = []

        def Add(special, text):
            s = ((special, getattr(eve.session, special)),)
            if text not in self.channels:
                self.svc.AddToList(text, s)
                self.channels[text] = s
                self.Refresh()

        for var, text in SPECIALVARS:
            if hasattr(eve.session, var):
                if getattr(eve.session, var) is not None:
                    m.append((text, Add, (var, text)))

        m.append(None)
        m.append(('System Channels', self.GetSystemChannels()))
        m.append(None)
        m.append(('Current Channels', self.GetCurrentChannels()))
        m.append(None)
        m.append(('Custom', self.CustomChannel))
        self.Refresh()
        self.MakeMenu(m, 'Add_Btn')

    def DeleteChannel(self, cname = None, *args):
        """
            Method to remove a channelID from the scroll and maintained list
        """
        del self.channels[cname]
        self.svc.DeleteFromList(cname)
        self.Refresh()

    def Join(self, channelID = None, *args):
        """
            Joins a specified channel
        """
        if channelID is None:
            return
        list = [ cid for cid in sm.StartService('LSC').channels ]
        if channelID not in list:
            sm.StartService('LSC').JoinOrLeaveChannel(channelID)

    def CustomChannel(self, *args):
        """
            Function to add/join a custom channel (by name, NOT ID!)
        """
        ret = uix.NamePopup(u'Create / Join Channel', u'Type in name', '')
        if ret is not None:
            name = str(ret['name'])
            if not self.svc.LookupChannel(name):
                self.svc.AddChannel(name)
            info = self.svc.GetChannel(name)
            if info is not None:
                dname = info.displayName
                self.svc.AddToList(dname, info.channelID)
                self.channels[dname] = info.channelID
                self.Refresh()

    def MakeMenu(self, list = None, anchor = None):
        """
            Custom method to create a simple popup menu anchored around the calling button
        """
        if list is None:
            return
        if anchor is None:
            return
        mv = menu.CreateMenuView(menu.CreateMenuFromList(list), None, None)
        anchorwindow = self
        x = max(uiutil.GetChild(anchorwindow, anchor).GetAbsolute()[0], 0)
        y = anchorwindow.top + anchorwindow.height
        if anchorwindow.top + anchorwindow.height + mv.height > uicore.desktop.height:
            mv.top = min(form.InsiderWnd.GetIfOpen().top - mv.height, y)
        else:
            mv.top = min(uicore.desktop.width - mv.height, y)
        mv.left = min(uicore.desktop.width - mv.width, x)
        uicontrols.Frame(parent=mv, color=(1.0, 1.0, 1.0, 0.2))
        uicore.layer.menu.children.insert(0, mv)
