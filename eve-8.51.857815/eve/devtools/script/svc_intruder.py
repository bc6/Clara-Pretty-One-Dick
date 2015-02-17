#Embedded file name: eve/devtools/script\svc_intruder.py
import blue
import listentry
import uiutil
import carbonui.const as uiconst
import uicontrols
import uiprimitives
from service import Service, ROLEMASK_ELEVATEDPLAYER, ROLE_GMH
SERVICENAME = 'intruder'

class IntruderEntry(listentry.Generic):
    __guid__ = 'listentry.IntruderEntry'

    def GetMenu(self, *args):
        d = self.sr.node
        m = []
        if d.type == 'Station' and eve.session.role & ROLEMASK_ELEVATEDPLAYER:
            m.append(['TR me to this Station', self.TR, ()])
        if d.type == 'SolarSystem' and eve.session.role & ROLEMASK_ELEVATEDPLAYER:
            m.append(['TR me to this SolarSystem', self.TR, ()])
        if eve.session.role & ROLE_GMH:
            if d.type == 'SolarSystem':
                m.append(["Peek at Local (can't chat!)", self.Join, ('solarsystemid2',)])
        m.append(['Copy ID (%s)' % d.itemID, self.Copy, ()])
        m += [None]
        if d.type == 'Character':
            ok = 0
            for entry in m:
                if entry and entry[0].lower() == 'show info':
                    ok = 1

            if not ok:
                m.append(['Show Info', sm.GetService('info').ShowInfo, (d.typeID, d.itemID)])
        m += sm.GetService('menu').GetMenuFormItemIDTypeID(d.itemID, d.typeID)
        return m

    def TR(self):
        sm.RemoteSvc('slash').SlashCmd('/tr me %s' % self.sr.node.itemID)

    def Copy(self):
        blue.pyos.SetClipboardData(str(self.sr.node.itemID))

    def Join(self, idtype):
        if self.sr.node.type != 'SolarSystem':
            msg = ['This function joins the private chat channel of the %s %s, allowing you to actively participate in the chat.' % (self.sr.node.name, self.sr.node.type),
             'DO NOT PROCEED UNLESS YOU ARE AUTHORISED TO DO SO.',
             '',
             'Proceed with join?']
            ret = sm.GetService('gameui').MessageBox(title='Privacy Invasion', text='<br>'.join(msg), buttons=uiconst.OKCANCEL, icon=uiconst.QUESTION)
            if ret[0] != uiconst.ID_OK:
                return
        sm.GetService('LSC').JoinChannel(((idtype, self.sr.node.itemID),))


class Intruder(Service):
    __module__ = __name__
    __exportedcalls__ = {}
    __notifyevents__ = ['ProcessRestartUI']
    __dependencies__ = []
    __guid__ = 'svc.intruder'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME
    __neocommenuitem__ = (('Super Search', 'res:/ui/Texture/WindowIcons/peopleandplaces.png'), 'Show', ROLEMASK_ELEVATEDPLAYER)

    def Run(self, memStream = None):
        self.wnd = None

    def Stop(self, memStream = None):
        self.Hide()
        Service.Stop(self, memStream)

    def Show(self):
        if self.wnd:
            self.wnd.Maximize()
            return
        self.wnd = wnd = uicontrols.Window.Open(windowID='Super Search')
        wnd._OnClose = self.Hide
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Super Search')
        wnd.SetMinSize([256, 256])
        main = uiprimitives.Container(name='main', parent=uiutil.GetChild(wnd, 'main'), pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        top = uiprimitives.Container(name='top', parent=main, height=25, align=uiconst.TOTOP)
        btn = uicontrols.Button(parent=top, label='Search', align=uiconst.TORIGHT, func=self.Search)
        self.input = uicontrols.SinglelineEdit(name='system', parent=top, width=-1, height=-1, align=uiconst.TOALL, left=1)
        self.input.OnReturn = self.Search
        uiprimitives.Container(name='div', parent=main, height=5, align=uiconst.TOTOP)
        self.scroll = uicontrols.Scroll(parent=main)
        self.scroll.Load(contentList=[], headers=['Type', 'itemID', 'Name'], fixedEntryHeight=18)

    def Hide(self, *args):
        if self.wnd:
            self.wnd.Close()
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def Search(self, *args):
        searchStr = self.input.GetValue()
        ret = []
        result = sm.RemoteSvc('lookupSvc').LookupCharacters(searchStr, 0)
        if result:
            cfg.eveowners.Prime([ each.characterID for each in result ])
            for each in result:
                ret.append(('Character',
                 each.typeID,
                 each.characterID,
                 each.characterName))

        d = {}
        result = sm.RemoteSvc('lookupSvc').LookupCorporationTickers(searchStr.upper()[:5], 0)
        if result:
            cfg.eveowners.Prime([ each.corporationID for each in result ])
            for each in result:
                d[each.corporationID] = '%s [%s]' % (each.corporationName, each.tickerName)

        result = sm.RemoteSvc('lookupSvc').LookupCorporations(searchStr, 0)
        if result:
            cfg.eveowners.Prime([ each.corporationID for each in result ])
            for each in result:
                d[each.corporationID] = each.corporationName

        for k, v in d.iteritems():
            ret.append(('Corporation',
             2,
             k,
             v))

        del d
        result = sm.GetService('alliance').GetRankedAlliances(maxLen=0)
        if result:
            for each in result.alliances:
                if searchStr.upper() in each.shortName or searchStr.lower() in each.allianceName.lower():
                    ret.append(('Alliance',
                     16159,
                     each.allianceID,
                     '%s [%s]' % (each.allianceName, each.shortName)))

        for s in [(const.groupSolarSystem, 'SolarSystem'), (const.groupStation, 'Station')]:
            result = sm.RemoteSvc('lookupSvc').LookupLocationsByGroup(s[0], searchStr)
            if result:
                cfg.evelocations.Prime([ each.itemID for each in result ])
                for each in result:
                    ret.append((s[1],
                     each.typeID,
                     each.itemID,
                     each.itemName))

        stuff = []
        for each in ret:
            entry = listentry.Get('IntruderEntry', {'label': u'%s<t>%s<t>%s' % (each[0], each[2], each[3]),
             'type': each[0],
             'typeID': each[1],
             'itemID': each[2],
             'name': each[3]})
            stuff.append(entry)

        self.scroll.Load(contentList=stuff, headers=['Type', 'itemID', 'Name'], fixedEntryHeight=18)
