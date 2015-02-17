#Embedded file name: eve/devtools/script\svc_copycat2.py
CFG_USEONLINE = 0
myversion = '2.4'
SERVICENAME = 'copycat'
DEFAULTDBNAME = 'copycat.xml'
VIEW_USER = 0
VIEW_GROUPED = 1
VIEW_MARKET = 2
import cPickle
import spiffy
import dna
import param
import sys
import types
import os
import uthread
import xml.parsers.expat
import urllib
import blue
import util
import base
import inifile
import triui
import listentry
import uiutil
import uicls
import carbonui.const as uiconst
import random
from service import Service, ROLE_WORLDMOD, ROLEMASK_ELEVATEDPLAYER, ROLE_GML, ROLE_PLAYER, ROLE_HEALSELF, ROLE_IGB, ROLE_SPAWN, SERVICE_RUNNING, SERVICE_START_PENDING
import uicontrols
import uiprimitives
import const

def GetTypeName(typeID):
    return cfg.invtypes.Get(typeID).name


def GetCategory(typeID):
    return cfg.invtypes.Get(typeID).Group().Category()


Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)
Slash = lambda command: sm.RemoteSvc('slash').SlashCmd(command)
Message = lambda title, body, icon = triui.INFO: sm.GetService('gameui').MessageBox(body, title, buttons=uiconst.OK, icon=icon)
AUTOSAVE_IMMEDIATE = 3
AUTOSAVE_TIMED = 2
AUTOSAVE_EXITONLY = 1
AUTOSAVE_DISABLED = 0
UI_WBIG = 'copycat_width_big'
UI_WSMALL = 'copycat_width_small'
UI_WINFO = 'copycat_width_infopanel'
UI_USEINFO = 'copycat_infopanel'

def IsRepeatable(module):
    dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
    if module.IsOnline() is False:
        return False
    for effectID in dogmaLocation.dogmaStaticMgr.effectsByType[module.typeID]:
        effect = dogmaLocation.dogmaStaticMgr.effects[effectID]
        if effect.effectCategory not in [const.dgmEffActivation, const.dgmEffTarget]:
            continue
        if effect.durationAttributeID is None:
            continue
        if effectID == const.effectOnline:
            continue
        return True

    return False


def AskFile(title = 'Title goes here', body = 'Enter name of file:', setvalue = '', mustexist = True):
    while True:
        ret = uiutil.NamePopup(caption=title, label=body, setvalue=setvalue, maxLength=256)
        if not ret:
            return None
        filename = ret
        if mustexist:
            if os.path.exists(filename):
                return filename
            Message('File not found', 'Could not locate the file:<br>  %s' % filename, icon=triui.WARNING)
            continue
        return filename


def EscapeString(unescaped):
    unescaped = str(unescaped)
    escaped = unescaped.replace('&', '&amp;')
    escaped = escaped.replace('<', '&lt;')
    escaped = escaped.replace('>', '&gt;')
    return escaped


def UnEscapeString(escaped):
    escaped = str(escaped)
    unescaped = escaped.replace('&lt;', '<')
    unescaped = unescaped.replace('&gt;', '>')
    unescaped = unescaped.replace('&amp;', '&')
    return unescaped


class CCItem(object):

    def __init__(self):
        self.parent = None

    def __repr__(self):
        if hasattr(self, 'name'):
            return '<Item name="%s">' % self.name
        return '<Item name=Unspecified>'

    def Remove(self):
        if self.parent:
            self.parent.RemoveItem(self)


class CCFolder(CCItem):

    def __init__(self):
        CCItem.__init__(self)
        self.content = []

    def AddItem(self, this):
        self.content.append(this)
        this.parent = self

    def RemoveItem(self, this):
        self.content.remove(this)
        this.parent = None

    def ContainsItem(self, this):
        while this.parent:
            this = this.parent
            if this == self:
                return True

        return False

    def __repr__(self):
        return '<CCFolder>'


def CreateTreeFromDict(dict):
    f = CCFolder()
    for k, v in dict.iteritems():
        if type(v) == types.DictType:
            node = CreateTreeFromDict(v)
        else:
            node = CCItem()
            node.dna = v
        node.name = k
        f.AddItem(node)

    return f


racial = {'Caldari': 1,
 'Minmatar': 2,
 'Gallente': 3,
 'Amarr': 4}

class CopycatService(Service):
    """
    Ultimate ship setup tool
    """
    __neocommenuitem__ = (('Copycat', '40_15'), 'Show', ROLEMASK_ELEVATEDPLAYER)
    __slashhook__ = True
    __exportedcalls__ = {'igb': [ROLE_IGB]}
    __notifyevents__ = ['ProcessRestartUI']
    __dependencies__ = []
    __guid__ = 'svc.copycat'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME.capitalize()

    def cmd_cc(self, p):
        """[dnaKey [quantity]]"""
        try:
            dnaKey, qty = p.Parse('s?i')
            if qty is None:
                qty = 1
            dna.Ship(dnaKey=dnaKey).AssembleMany(qty)
            return 'Ok'
        except param.Error:
            if not p.line.strip():
                uthread.new(self.Show)
                return 'Ok'
            raise

    def cmd_getshipsetup(self, p):
        """[charName|id|"me"]"""
        dnaKey = sm.RemoteSvc('slash').SlashCmd('/getshipsetup ' + p.line)
        dna.Ship(dnaKey=dnaKey).ShowInfo()
        return 'Ok'

    def igb(self, action = '', key = '', name = None):
        action = action.lower()
        if action == 'open':
            dna.Popup(key, name)

    def AddDestroyedShip(self, dnaKey, name):
        now = blue.os.GetWallclockTime()
        for info in self.last10killed:
            if info[0] == dnaKey:
                self.last10killed.remove(info)
                break

        self.last10killed = [(dnaKey, now, name)] + self.last10killed[:9]
        self.WriteKilled()

    def GetSetupsByTypeID(self, typeID):
        hits = []
        typeID = str(typeID)

        def Scan(folder):
            for item in folder.content:
                if isinstance(item, CCFolder):
                    Scan(item)
                else:
                    parts = item.dna.split(':', 2)
                    if len(parts) == 3 and typeID == parts[1]:
                        hits.append((item.name, item.dna))

        Scan(self.tree)
        return hits

    def ShowInfo(self, what = None, name = None):
        dna.Popup(what, name, buttons=False)

    def GetInsiderDir(self):
        return sm.GetService('insider').GetInsiderDir()

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        try:
            self.lockout = False
            self.wnd = None
            self.dbchanged = False
            INSIDERDIR = self.GetInsiderDir()
            self.prefs = inifile.Handler(inifile.IniFile('copycat', INSIDERDIR))
            dbpath = os.path.join(INSIDERDIR, DEFAULTDBNAME)
            for key, value in [('database', DEFAULTDBNAME), ('autosave', AUTOSAVE_IMMEDIATE)]:
                if not self.prefs.HasKey(key):
                    self.prefs.SetValue(key, value)

            TARGET = os.path.join(INSIDERDIR, self.prefs.database)
            self.dbfilename = TARGET
            self.dbautosave = self.prefs.autosave
            self.last10killed = self.ReadKilled()
            if not os.path.exists(dbpath):
                self.RetrieveDefaultDatabase(dbpath)
            self.tree = self.ReadDatabase()
            if not self.tree:
                self.tree = CreateTreeFromDict({'There is no data to display': {'': ''}})
                self.SetAutoSave(0)
            self.SetAutoSave(self.dbautosave)
        finally:
            self.state = SERVICE_RUNNING

    def Stop(self, memStream = None):
        self.Hide()
        if self.dbautosave:
            self.SaveDatabaseIfChanged()
        Service.Stop(self, memStream)

    def ReadKilled(self):
        self.last10killed = []
        try:
            for line in open(os.path.join(self.GetInsiderDir(), 'destroyed.txt'), 'r'):
                line = line.strip()
                if line.startswith('DNA:'):
                    dnaKey, lostAt, name = line.split('=', 2)
                    self.last10killed.append([dnaKey, long(lostAt), name])

        except:
            sys.exc_clear()

        return self.last10killed

    def WriteKilled(self):
        try:
            out = open(os.path.join(self.GetInsiderDir(), 'destroyed.txt'), 'w')
            for line in self.last10killed:
                print >> out, '%s=%d=%s' % line

            out.close()
        except:
            sys.exc_clear()

    def SetAutoSave(self, mode):
        self.dbautosave = mode
        if mode == AUTOSAVE_TIMED:
            self.dbautosavetimer = base.AutoTimer(300000, self.SaveDatabaseIfChanged)
        else:
            self.dbautosavetimer = None
        self.prefs.autosave = self.dbautosave = mode
        self.SaveDatabaseIfChanged()
        self.UpdateStatus()

    def SaveDatabaseIfChanged(self):
        if self.dbchanged:
            self.WriteDatabase(self.tree)
            self.dbchanged = False
            self.UpdateStatus()

    def ReadDatabaseOLD(self, filename):
        folder = CCFolder()
        db = blue.classes.CreateInstance('blue.ResFile')
        if db.Open(filename) and db.size > 0:
            crud = str(db.Read())
            try:
                stuff = cPickle.loads(crud)
                for k, v in stuff:
                    item = CCItem()
                    item.name = k
                    item.dna = v
                    folder.AddItem(item)

            except:
                for line in crud.replace('\r', '').split('\n'):
                    if len(line) > 2:
                        if line[0] == '[' and line[-1] == ']':
                            pass
                        elif line[:4] == 'DNA:':
                            line = line.split('=')
                            item = CCItem()
                            item.name = line[1]
                            item.dna = line[0]
                            folder.AddItem(item)

        if folder.content:
            return folder

    def ReadDatabase(self, filename = None):
        self._root = None
        if filename is None or filename == '':
            filename = self.dbfilename

        def XMLTagStart(tag, attrs):
            if tag == 'data':
                if self._root:
                    raise RuntimeError, 'Craptastic!'
                self._root = self.currentfolder = self.currentitem = CCFolder()
            elif tag == 'group':
                folder = CCFolder()
                self.currentfolder.AddItem(folder)
                self.currentfolder = self.currentitem = folder
            elif tag == 'item':
                self.currentitem = CCItem()
            else:
                self.currenttag = tag

        def XMLTagEnd(tag):
            if tag == 'group':
                if not hasattr(self.currentfolder, 'name'):
                    self.currentfolder.name = 'Unnamed group'
                self.currentfolder = self.currentfolder.parent
            elif tag == 'item':
                if not hasattr(self.currentitem, 'name'):
                    self.currentitem.name = 'Unnamed setup'
                if hasattr(self.currentitem, 'dna'):
                    self.currentfolder.AddItem(self.currentitem)

        def XMLTagData(data):
            if not self.currenttag:
                return
            data = data.replace('\n', '').replace('\r', '')
            if not data:
                return
            if self.currenttag == 'name':
                self.currentitem.name = UnEscapeString(eval("'" + data.replace("'", "\\'") + "'"))
            elif self.currenttag == 'dna':
                self.currentitem.dna = data
            self.currenttag = None

        try:
            f = open(filename, 'r')
        except:
            return

        self.currenttag = 'Kittens!'
        self.currentfolder = None
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = XMLTagStart
        p.EndElementHandler = XMLTagEnd
        p.CharacterDataHandler = XMLTagData
        p.buffer_text = True
        p.returns_unicode = False
        p.ParseFile(f)
        root = self._root
        self._root = None
        return root

    def WriteDatabase(self, tree, filename = None):
        if not filename:
            filename = self.dbfilename
        list = []

        def XMLTag(key, value):
            return '<%s>%s</%s>\r\n' % (key, repr(EscapeString(value))[1:-1], key)

        def XMLDumpItem(f, item, tag, indent):
            deeper = indent + '\t'
            f.write('%s<%s>\r\n' % (indent, tag))
            f.write(deeper + XMLTag('name', item.name))
            f.write(deeper + XMLTag('dna', item.dna))
            f.write('%s</%s>\r\n' % (indent, tag))
            if item in list:
                (RuntimeError, 'Endless cycle detected: %s' % item)
            list.append(item)

        def XMLDumpFolder(f, folder, tag = 'data', indent = ''):
            deeper = indent + '\t'
            if not indent:
                f.write("<?xml version='1.0' encoding='utf-8'?>\r\n")
            if hasattr(folder, 'name') and folder.name:
                f.write('%s<%s>\r\n' % (indent, tag))
                f.write(deeper + XMLTag('name', folder.name))
            else:
                f.write('%s<%s>\r\n' % (indent, tag))
            for item in folder.content:
                if isinstance(item, CCFolder):
                    XMLDumpFolder(f, item, 'group', deeper)
                else:
                    XMLDumpItem(f, item, 'item', deeper)

            f.write('%s</%s>\r\n' % (indent, tag))

        XMLDumpFolder(open(filename, 'wb'), tree)

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def Hide(self, *args):
        if self.wnd:
            self.wnd.Close()
            self.wnd = None
            self.infotemplate = None

    def RetrieveDefaultDatabase(self, dbpath):
        try:
            src = 'http://content.eveonline.com/QA/insider/copycat.xml'
            urllib.urlretrieve(src, dbpath)
            self.ReadDatabase()
        except urllib.URLError:
            sm.GetService('gameui').MessageBox('There was a problem retrieving the default copycat db', 'Error', buttons=uiconst.OK, icon=triui.ERROR)

    def Show(self):
        if not (hasattr(eve.session, 'solarsystemid') and eve.session.solarsystemid2):
            Message('Hold your horses!', 'The copycat UI requires you to be logged in.')
            return
        if self.wnd:
            self.wnd.Maximize()
            return
        initing = True
        self.wnd = wnd = uicontrols.Window.Open(windowID=SERVICENAME)
        wnd._OnClose = self.Hide
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Copycat')
        wnd.sr.main = main = uiutil.GetChild(wnd, 'main')
        top = uiprimitives.Container(name='push', align=uiconst.TOTOP, height=14, parent=main)
        uiprimitives.Line(parent=top, align=uiconst.TOBOTTOM)
        push = uiprimitives.Container(name='push', parent=top, align=uiconst.TOLEFT, width=const.defaultPadding, state=uiconst.UI_DISABLED)
        uiprimitives.Line(parent=push, align=uiconst.TORIGHT)
        for label, func in [('File', self.GetMenu_File), ('My Ship', self.GetMenu_Ship)]:
            menu = uicls.WindowDropDownMenu(name='menu', parent=top, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL)
            menu.Setup(label, func)

        uiprimitives.Container(name='bottompush', parent=main, state=uiconst.UI_DISABLED, align=uiconst.TOBOTTOM, height=const.defaultPadding)
        c = uiprimitives.Container(name='', parent=main, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOBOTTOM, height=10)
        wnd.sr.filenamelabel = uicontrols.Label(text='', parent=c, align=uiconst.TOALL, padLeft=const.defaultPadding, color=None, state=uiconst.UI_NORMAL)
        self.UpdateStatus()
        wnd.sr.tabs = uicontrols.TabGroup(name='tabsparent', parent=main)
        body = uiprimitives.Container(name='scroll', parent=main, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        wnd.sr.info = info = dna.InfoPanel(name='infopanel', parent=body, align=uiconst.TORIGHT)
        info.Setup(readonly=True)
        info.width = settings.user.ui.Get(UI_WINFO, 288)
        self.scaling = 0
        wnd.sr.div = div = uiprimitives.Container(name='meow', parent=body, align=uiconst.TORIGHT)
        uiprimitives.Fill(parent=body, color=(1.0, 1.0, 1.0, 0.5), width=2, align=uiconst.TORIGHT)
        wnd.sr.scroll = uicontrols.Scroll(parent=body)
        wnd.sr.scroll.sr.sortBy = 'Name'
        wnd.sr.scroll.Startup()
        wnd.sr.scroll.sr.id = 'Copycat2Scroll'
        wnd.sr.scroll.sr.content.OnDropData = self.OnDropData
        wnd.OnDropData = self.OnDropData

        def toggleview(*args):
            x = settings.user.ui.Get(UI_USEINFO, 0)
            if not initing:
                x = not x
            settings.user.ui.Set(UI_USEINFO, x)
            b.state = uiconst.UI_HIDDEN
            self.wnd.width = (self.smallwidth, self.bigwidth)[x]
            self.UpdateInfoPanelStuff()

        icon = uiprimitives.Sprite(parent=main, width=16, height=16, align=uiconst.TOPRIGHT, top=14, left=const.defaultPadding, texturePath='res:/UI/Texture/classes/Browser/backIdle.png')
        icon.OnClick = toggleview
        self.wnd.sr.infotoggle = b = icon
        self.viewmode = VIEW_USER
        self.fixedgroups = {}
        wnd.sr.tabs.Startup([['Normal',
          self.wnd.sr.scroll,
          self,
          VIEW_USER], ['Grouped',
          self.wnd.sr.scroll,
          self,
          VIEW_GROUPED], ['Market',
          self.wnd.sr.scroll,
          self,
          VIEW_MARKET]], 'copycattabs')
        self.smallwidth = settings.user.ui.Get(UI_WSMALL, 200)
        self.bigwidth = settings.user.ui.Get(UI_WBIG, 400)
        self.lastdna = None
        toggleview()
        if info.state != uiconst.UI_HIDDEN:
            wnd.width = self.bigwidth
        else:
            wnd.width = self.smallwidth
        wnd.Maximize(1)
        wnd.OnEndScale_ = self.UpdateInfoPanelStuff
        if eve.session.role > 1:
            self.ShowContent()
        initing = False

    def ScaleStart(self, *args):
        self.wnd.sr.info.state = uiconst.UI_DISABLED
        self.scaling = 1
        self.ss_w = self.wnd.sr.info.width
        self.ss_x = uicore.uilib.x

    def ScaleMove(self, *args):
        if self.scaling:
            minW = 256
            maxW = max(self.wnd.width - 100, minW)
            diffx = uicore.uilib.x - self.ss_x
            try:
                self.wnd.sr.info.width = min(maxW, max(minW, self.ss_w - diffx))
            except:
                pass

    def ScaleEnd(self, *args):
        settings.user.ui.Set(UI_WINFO, self.wnd.sr.info.width)
        self.UpdateInfoPanelStuff()

    def UpdateInfoPanelStuff(self, *args):
        self.scaling = 0
        b = self.wnd.sr.infotoggle
        info = self.wnd.sr.info
        info.state = self.wnd.sr.div.state = (uiconst.UI_HIDDEN, uiconst.UI_NORMAL)[settings.user.ui.Get(UI_USEINFO, 0)]
        info.hideBackground = 0
        if info.state == uiconst.UI_HIDDEN:
            b.flag = b.hint = b.name = 'Show Info Panel'
            b.rectLeft = 84
            self.wnd.SetMinSize((256, 160))
            self.smallwidth = self.wnd.width
            settings.user.ui.Set(UI_WSMALL, self.smallwidth)
        else:
            b.flag = b.hint = b.name = 'Hide Info Panel'
            b.rectLeft = 64
            self.wnd.SetMinSize((max(400, info.width + 100), 160))
            self.bigwidth = self.wnd.width
            settings.user.ui.Set(UI_WBIG, self.bigwidth)
        b.state = uiconst.UI_HIDDEN
        b.state = uiconst.UI_NORMAL
        self.ShowDNA(force=True)

    def ShowInfo(self, dnaKey = None, shipID = None, name = None):
        if dnaKey:
            dna.Ship(dnaKey=dnaKey, name=name).ShowInfo()
        elif shipID:
            dna.Ship(shipID=shipID).ShowInfo()

    def ShowDNA(self, name = None, dnaKey = None, force = False):
        info = self.wnd.sr.info
        if not force:
            if info.state == uiconst.UI_HIDDEN:
                return
            if self.lastdna == dnaKey:
                return
        self.lastdna = dnaKey
        t = None
        if name is None and dnaKey is None:
            t = getattr(self, 'infotemplate', None)
        elif dnaKey:
            self.infotemplate = t = dna.Ship(dnaKey=dnaKey, name=name)
        if t:
            info.Load(t)

    def Load(self, viewmode):
        s = self.wnd.sr.scroll
        if self.viewmode != viewmode:
            self.viewmode = viewmode
            self.ShowContent()

    def Refresh(self):
        self.wnd.sr.scroll.Refresh()

    def ShowContent(self, resetPos = True):
        if not self.wnd:
            return
        s = self.wnd.sr.scroll
        p = s.sr.position
        tree = self.tree
        if self.viewmode == VIEW_USER:
            h = ['Name', 'Type', 'Group']
        elif self.viewmode == VIEW_GROUPED:
            tree = self.ReorganisedByInvGroup(self.tree)
            h = ['Name', 'Type']
        elif self.viewmode == VIEW_MARKET:
            tree = self.ReorganisedByMarketGroup(self.tree)
            h = ['Name', 'Type']
        else:
            raise RuntimeError('Unrecognized View Mode: %s' % tree)
        self.LogInfo('ShowContent calling self.BuildTreeList')
        s.Load(contentList=self.BuildTreeList(tree), fixedEntryHeight=None, headers=h)
        if not resetPos:
            s.sr.position = p
            s.UpdatePosition()

    def UpdateStatus(self):
        if not self.wnd:
            return
        self.wnd.sr.filenamelabel.text = 'File: <color=0xff%s>%s' % (('00ff00', 'ff0000')[self.dbchanged], os.path.basename(self.dbfilename))
        status = 'Current database:<br>  %s<br><br>' % os.path.abspath(self.dbfilename)
        if self.dbautosave != AUTOSAVE_IMMEDIATE:
            status += '%sModified.<br><br>' % ('Not ', '')[self.dbchanged]
        if self.dbautosave == AUTOSAVE_DISABLED:
            status += "Changes to the database are not automatically saved. Select 'SAVE' from the database menu to make any changes permanent."
        elif self.dbautosave == AUTOSAVE_IMMEDIATE:
            status += 'Any changes to the database are permanent.'
        elif self.dbautosave == AUTOSAVE_TIMED:
            status += 'Changes to the database are automatically saved every 5 minutes.'
        elif self.dbautosave == AUTOSAVE_EXITONLY:
            status += "Changes to the database are saved at exit or by selecting 'SAVE' from the database menu."
        else:
            status += 'wtf?'
        self.wnd.sr.filenamelabel.hint = status

    def UpdateContent(self, everything = True):
        self.ShowContent(False)
        self.dbchanged = True
        if self.dbautosave == AUTOSAVE_IMMEDIATE:
            self.SaveDatabaseIfChanged()
        self.UpdateStatus()

    def CopyFromItem(self, fromItem):
        item = CCItem()
        item.name = fromItem.name
        item.dna = fromItem.dna
        item.fromItem = fromItem
        return item

    def ReorganisedByMarketGroup(self, sourcetree):
        temp = {}

        def _CollectItem(fromItem):
            if isinstance(fromItem, CCFolder):
                for x in fromItem.content:
                    _CollectItem(x)

                return
            item = self.CopyFromItem(fromItem)
            typeID = int(item.dna.split(':')[1])
            if temp.has_key(typeID):
                temp[typeID].append(item)
            else:
                temp[typeID] = [item]

        _CollectItem(sourcetree)

        def _WalkMarket(marketGroups):
            items = []
            for info in marketGroups:
                grouplist = sm.GetService('marketutils').GetMarketGroups()[info.marketGroupID]
                if grouplist:
                    subitems = _WalkMarket(grouplist)
                    if subitems:
                        folder = CCFolder()
                        folder.name = info.marketGroupName
                        for item in subitems:
                            folder.AddItem(item)

                        items.append(folder)
                else:
                    for typeID in info.types:
                        if temp.has_key(typeID):
                            folder = CCFolder()
                            folder.name = info.marketGroupName
                            for item in temp[typeID]:
                                folder.AddItem(item)

                            items.append(folder)
                            del temp[typeID]

            return items

        tree = _WalkMarket(sm.GetService('marketutils').GetMarketGroups()[None])[0]
        if temp:
            folder = CCFolder()
            folder.name = 'Other'
            for itemlist in temp.itervalues():
                for item in itemlist:
                    folder.AddItem(item)

            tree.AddItem(folder)
        return tree

    def ReorganisedByInvGroup(self, sourcetree):

        def _CollectItem(fromItem):
            if isinstance(fromItem, CCFolder):
                for x in fromItem.content:
                    _CollectItem(x)

                return
            typeID = int(fromItem.dna.split(':')[1])
            inv = cfg.invtypes.GetIfExists(typeID)
            if inv:
                groupname = inv.Group().name
            else:
                groupname = 'Unknown'
            if self.fixedgroups.has_key(groupname):
                folder = self.fixedgroups[groupname]
            else:
                folder = self.fixedgroups[groupname] = CCFolder()
                folder.name = groupname
            folder.AddItem(self.CopyFromItem(fromItem))

        for groupname in self.fixedgroups.iterkeys():
            self.fixedgroups[groupname].content = []

        _CollectItem(sourcetree)
        newtree = CCFolder()
        for groupname in self.fixedgroups.iterkeys():
            folder = self.fixedgroups[groupname]
            if folder.content:
                newtree.AddItem(folder)

        return newtree

    def BuildTreeList(self, folder, sublevel = 0):
        ret = []
        guid = 'DNAEntry'
        self.LogInfo('folder: %s' % folder)
        for this in folder.content:
            self.LogInfo('this: %s' % this)
            if isinstance(this, CCFolder):
                raceID = racial.get(this.name, 0)
                node = {'raceID': raceID,
                 'label': this.name,
                 'iconMargin': 18,
                 'showlen': self.viewmode != VIEW_MARKET or raceID,
                 'groupItems': this.content,
                 'state': 0,
                 'allowCopy': 0,
                 'allowGuids': ['listentry.DNAGroup', 'listentry.' + guid],
                 'RefreshScroll': self.ShowContent,
                 'GetSubContent': self.GroupGetSubContent,
                 'typeID': 3296,
                 'selected': 0,
                 'hideFill': True,
                 'id': ('dna', this),
                 'sublevel': sublevel}
                if self.viewmode == VIEW_USER:
                    node.update({'ChangeLabel': self.GroupChangeLabel,
                     'DeleteFolder': self.GroupDelete,
                     'DropData': self.GroupAdoptNodes})
                entry = listentry.Get('DNAGroup', node)
            else:
                typeID = int(this.dna.split(':')[1])
                tgroupname = 'Unknown'
                okay = False
                if eve.session.role & ROLE_PLAYER:
                    inv = cfg.invtypes.GetIfExists(typeID)
                    if inv:
                        tname = inv.name
                        tgroupname = inv.Group().name
                        okay = True
                    else:
                        tname = '[%s]' % typeID
                        typeID = 0
                else:
                    inv = None
                    tname = '%s' % typeID
                node = {'typename': 'Type:%s' % typeID,
                 'typeID': typeID,
                 'invitem': inv,
                 'showinfo': okay,
                 'id': ('dna', this),
                 'sublevel': sublevel}
                if self.viewmode == VIEW_USER:
                    node['label'] = '%s<t>%s<t>%s' % (this.name, tname, tgroupname)
                else:
                    node['label'] = '%s<t>%s' % (this.name, tname)
                entry = listentry.Get(guid, node)
            node['sublevel'] = sublevel
            node['id'] = (str(id(this)), this)
            node['locked'] = self.viewmode
            node[SERVICENAME] = None
            self.LogInfo('node: %s' % node)
            ret.append(entry)

        return ret

    def GroupGetSubContent(self, node, newitems = 0):
        if not len(node.groupItems):
            return []
        sublevel = node.get('sublevel', 0)
        self.LogInfo('GroupGetSubContent calling self.BuildTreeList')
        self.LogInfo('node: %s' % node)
        if not isinstance(node.id[1], CCFolder):
            return []
        return self.BuildTreeList(node.id[1], sublevel + 1)

    def GroupChangeLabel(self, id, newlabel):
        id[1].name = newlabel
        self.UpdateContent()

    def GroupAdd(self, name = None, parent = None):
        if not name:
            ret = uiutil.NamePopup(caption='New folder', label='Enter name for new folder:', setvalue='New Folder', maxLength=64)
            if ret:
                name = ret
        if not name:
            return None
        f = CCFolder()
        f.name = name
        if not parent:
            parent = self.tree
        parent.AddItem(f)
        self.UpdateContent()
        return f

    def GroupDelete(self, id):
        id[1].Remove()
        self.UpdateContent()

    def GroupAdoptNodes(self, folderid, these, *args):
        self.FolderAdoptNodes(folderid[1], these)

    def OnDropData(self, dragObj, these):
        self.FolderAdoptNodes(self.tree, these)

    def FolderAdoptNodes(self, targetfolder, these):
        changed = False
        for node in these:
            if node.Get(SERVICENAME, None):
                item = node.id[1]
                if isinstance(item, CCFolder):
                    if item == targetfolder or item.ContainsItem(targetfolder):
                        continue
                elif item.parent == targetfolder:
                    continue
                item.Remove()
                targetfolder.AddItem(item)
                changed = True

        if changed:
            self.UpdateContent()

    def GetMenu_File(self):
        mutexgfx = (('ui_9_64_14', 1.0 / 4.0), ('ui_38_16_193', 1.0 / 16.0))
        m = [(('Open...', 'ui_34_64_5'), self.DoImport, ('open',)),
         None,
         (('New Folder', 'res:/ui/Texture/WindowIcons/smallfolder.png', 0.125), (None, self.GroupAdd)[self.viewmode == VIEW_USER]),
         None,
         (('Save', 'ui_41_64_1'), self.DoSave),
         (('Save As...', 'ui_41_64_1'), self.DoSave, ('as',)),
         None,
         (('Import', 'ui_7_64_16'), [(('DNA from clipboard', 'ui_10_64_16'), self.DoImport, ('clipboard',)),
           None,
           (('XML Database (Copycat 2.x)', 'ui_34_64_5'), self.DoImport, ('import',)),
           (('DNA Database (Copycat 1.x)', 'ui_34_64_6'), self.DoImport, ('importold',))]),
         None,
         (('Autosave?', 'res:/ui/Texture/WindowIcons/assets.png'), [(('Immediately on every change',) + mutexgfx[self.dbautosave == AUTOSAVE_IMMEDIATE], self.SetAutoSave, (AUTOSAVE_IMMEDIATE,)),
           (('Every 5 minutes, if changed',) + mutexgfx[self.dbautosave == AUTOSAVE_TIMED], self.SetAutoSave, (AUTOSAVE_TIMED,)),
           (('At copycat/client exit only',) + mutexgfx[self.dbautosave == AUTOSAVE_EXITONLY], self.SetAutoSave, (AUTOSAVE_EXITONLY,)),
           (('Never (Manual only)',) + mutexgfx[self.dbautosave == AUTOSAVE_DISABLED], self.SetAutoSave, (AUTOSAVE_DISABLED,))])]
        return m

    def DoImport(self, mode):
        if mode == 'clipboard':
            self.DoStore(dnaKey=blue.pyos.GetClipboardData())
            return
        verb = 'Import'
        importfunc = self.ReadDatabase
        if mode == 'importold':
            filename = 'copycat.dna'
            title = 'Import Copycat 1.x DNA Database'
            importfunc = self.ReadDatabaseOLD
        elif mode == 'import':
            filename = 'copycat.xml'
            title = 'Import XML Database'
        elif mode == 'reload':
            filename = self.dbfilename
            verb = 'Reload'
        elif mode == 'open':
            filename = self.dbfilename
            title = 'Open Database'
            verb = 'Open'
        else:
            raise ValueError, "'%s' is not a DoImport mode" % mode
        if mode != 'reload':
            filename = AskFile(title, 'Enter name of file to %s' % verb, setvalue=filename)
            if not filename:
                return
        item = importfunc(filename)
        if item:
            if mode in ('reload', 'open'):
                append = False
                text = 'This operation will clear the currently loaded database!<br><br>Proceed?'
                ret = sm.GetService('gameui').MessageBox(title='%s Database' % verb, text=text, buttons=uiconst.OKCANCEL, icon=uiconst.WARNING)
            else:
                append = True
                text = 'Do you want to append to current database, or replace it?<br><br>Select <color=0xff00ff00>YES<color=0xffffffff> to <color=0xff00ff00>APPEND<color=0xffffffff> to current database.<br>Select <color=0xffff0000>NO<color=0xffffffff> to <color=0xffff0000>REPLACE<color=0xffffffff> current database.<br>Select <color=0xffffff00>CANCEL<color=0xffffffff> to abort the import.'
                ret = sm.GetService('gameui').MessageBox(title='Import Database', text=text, buttons=uiconst.YESNOCANCEL, customicon='ui_34_64_5')
            if ret:
                if ret[0] in (uiconst.ID_CANCEL, uiconst.ID_CLOSE):
                    return
                if ret[0] == uiconst.ID_NO:
                    append = False
            if append:
                item.name = 'Imported (%s)' % os.path.basename(filename)
                self.tree.AddItem(item)
            else:
                self.tree = item
            if mode == 'open':
                self.prefs.database = self.dbfilename = filename
            self.dbchanged = not append
            self.UpdateContent()
        else:
            Message('Database %s Error' % verb, 'The file is not a valid Copycat DNA Database, or contained no entries.', icon=triui.WARNING)

    def DoSave(self, mode = 'default'):
        if mode == 'default':
            self.WriteDatabase(self.tree)
            self.dbchanged = False
        elif mode == 'as':
            ret = uiutil.NamePopup(caption='Save database as...', label='Enter filename', setvalue=self.dbfilename, maxLength=256)
            if ret:
                self.WriteDatabase(self.tree, ret)
                self.dbchanged = False
                self.prefs.database = self.dbfilename = ret
        elif mode == 'selection':
            pass
        else:
            raise ValueError, 'Unknown save mode: %s' % mode
        self.UpdateStatus()

    def GetMenu_Ship(self):
        HaveShip = util.GetActiveShip() is not None
        HaveGML = eve.session.role & ROLE_GML
        CanSpawn = eve.session.role & (ROLE_WORLDMOD | ROLE_SPAWN)
        HaveHEALSELF = eve.session.role & ROLE_HEALSELF
        s = dna.Ship(shipID=util.GetActiveShip())
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        ship = dogmaLocation.GetDogmaItem(util.GetActiveShip())
        pod = False
        if HaveShip:
            if ship.groupID == 29:
                if not CanSpawn:
                    uthread.new(Message, "Haha! You're in a pod :)", "How did that happen?<br>Wait, never mind, I don't care.<br><br><br>Menu not available because you:<br>- are in a capsule<br>- don't have WORLDMOD or SPAWN role.")
                    return
                pod = True
                m = s.GetMenuInline(disabled=True, info=False, store=False, assemble=False, fit=False, refit=False)
            else:
                m = s.GetMenuInline(disabled=not HaveShip, store=True, assemble=False, refit=True)
        else:
            uthread.new(Message, 'No ship... No pod...', "You might want to get into a ship, it's cold out there.")
            return

        def cf(func, condition = True):
            if condition and HaveShip:
                return func
            return False

        if not pod:
            m += [None,
             ('Clone', cf(self.DoClone, HaveGML and not pod)),
             ('<color=0xff708090>Clone Perfect', cf(self.DoClonePerfect, eve.session.role & ROLE_WORLDMOD and eve.session.stationid and not pod)),
             None,
             ('Online Modules', cf(self.DoOnline, (HaveHEALSELF or eve.session.stationid) and not pod)),
             ('Autorepeat Modules', cf(self.DoRepeat, not pod))]
            m.insert(0, None)
            m.insert(0, ('<color=0xff708090>My %s' % cfg.invtypes.Get(s.typeID).name, None))
        m += [None,
         ('<color=0xff708090>Extras', None),
         None,
         ('Recover Ship', cf(('isDynamic', self.ResurrectMenu, ()), CanSpawn or HaveShip and eve.session.role & ROLE_GML))]
        m += [None, ('T3 Subsystems', cf(('isDynamic', self.T3SubsystemsMenu, ()), CanSpawn or eve.session.role & ROLE_GML))]
        return m

    def T3SubsystemsMenu(self):
        """
        This function builds and returns the menu for loading a player with
        subystems for the selected T3 ship. It also contains the method which
        deals with the creation of the items.
        
        Returns:
            The menu.
            This is a list of dictionaries where each dictionary entry contains the info
            which makes up a menu item, made up of:
            label: the label of the item in the menu.
            action: the method to be called when the item in the menu is clicked - _LoadRandomT3Subsystems
            args: the arguments to pass to the method - the typeID of the ship for which to create the subsystems
            hint: the hint for the menu item
        """
        m = []
        m.append(('/Load me subsystems for...', None))

        def _LoadRandomT3Subsystems(shipTypeID):
            """
            This method loads you with a random subsystem of each type for the typeID
            passed in by creating a list of valid subsystem IDs for this ship typeID, then
            selecting a random choice for each subsystem type and calling the slash
            service with "/load me <subsystemTypeID>"
            
            Params:
                shipTypeID -- A typeID for a tech 3 ship. This is passed in as an argument from
                the menu.
            """
            slashSvc = sm.RemoteSvc('slash')
            godmaSvc = sm.GetService('godma')
            for subsystemGroup in cfg.groupsByCategories.get(const.categorySubSystem, []):
                subsystemGroupID = subsystemGroup.groupID
                validTypes = []
                for item in cfg.typesByGroups.get(subsystemGroupID, []):
                    validShipTypeID = int(godmaSvc.GetTypeAttribute2(item.typeID, const.attributeFitsToShipType))
                    if validShipTypeID == shipTypeID and item.published:
                        validTypes.append(item.typeID)

                choice = random.choice(validTypes)
                slashSvc.SlashCmd('/load me %d' % choice)

        ships = cfg.typesByGroups.get(const.groupStrategicCruiser, [])
        for s in ships:
            m.append((s.typeName, _LoadRandomT3Subsystems, (s.typeID,)))

        return m

    def ResurrectMenu(self):
        m = []

        def _Resurrect(dnaKey, name):
            dna.Ship().ImportFromDNA(dnaKey, name).Assemble()

        for dnaKey, lostAt, name in self.last10killed:
            ship = dna.Ship().ImportFromDNA(dnaKey, name)
            m.append((name, _Resurrect, (dnaKey, name)))

        if m:
            m.insert(0, ('Recently lost ships', None))
        return m

    def DoOnline(self, shipID = None):
        if CFG_USEONLINE:
            if eve.session.role & ROLE_GML:
                sm.RemoteSvc('slash').SlashCmd('/online me')
                return
            roles = 'ROLE_GML or ROLE_HEALSELF'
        else:
            roles = 'ROLE_HEALSELF'
        if shipID is None:
            shipID = util.GetActiveShip()
        if shipID is None:
            return
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        ship = dogmaLocation.GetDogmaItem(shipID)
        onlined = 0
        offlinemods = []
        if eve.session.stationid:
            title = 'Turbo Power Up'
        else:
            if not eve.session.role & ROLE_HEALSELF:
                sm.GetService('gameui').MessageBox('To use this function in space, you need %s.' % roles, 'Function not available', buttons=uiconst.OK, icon=triui.INFO)
                return
            title = 'Power up'
        c = 0
        for slot in (const.flagLoSlot0, const.flagMedSlot0, const.flagHiSlot0):
            for flag in xrange(slot + 7, slot - 1, -1):
                c += 1
                Progress(title, 'Checking for offline modules...', c, 24)
                for module in ship.GetFittedItems().itervalues():
                    if module.flagID == flag and module.categoryID is not const.categoryCharge:
                        if not module.IsOnline():
                            offlinemods.append(module)
                        break

        def ONLINE(state, control):
            try:
                dogmaLocation.OnlineModule(control.itemID)
            except:
                pass

            state[0] += 1
            Progress(title, 'Activating module %s of %s' % (state[0], state[1]), state[0], state[1])

        offlinemodcount = len(offlinemods)
        if offlinemodcount > 0:
            state = [0, offlinemodcount]
            w = sm.RemoteSvc('slash')
            if eve.session.stationid:
                parallelCalls = []
                for control in offlinemods:
                    parallelCalls.append((ONLINE, (state, control)))

                uthread.parallel(parallelCalls)
            else:
                for control in offlinemods:
                    w.SlashCmd('/heal me capac=1')
                    ONLINE(state, control)

                w.SlashCmd('/heal me capac=1')
        Progress(title, 'Done', 1, 1)
        return offlinemodcount

    def DoRepeat(self, *args):
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        ship = dogmaLocation.GetDogmaItem(util.GetActiveShip())
        try:
            modules = uicore.layer.shipui.sr.modules
        except:
            modules = []

        for module in ship.GetFittedItems().itervalues():
            if module and IsRepeatable(module):
                if not eve.session.stationid and module.itemID in modules:
                    modules[module.itemID].SetRepeat(1000)
                else:
                    settings.char.autorepeat.Set(module.itemID, 1000)

    def DoStore(self, dnaKey = None, name = None, shipID = None):
        if dnaKey:
            template = dna.Ship(dnaKey=dnaKey)
            action = 'Import'
            if not name:
                name = 'Imported %s' % GetTypeName(template.typeID)
        else:
            template = dna.Ship(shipID=shipID)
            dnaKey = template.ExportAsDNA()
            action = 'Store'
            name = template.name
        ret = uiutil.NamePopup(caption='%s %s DNA' % (action, GetTypeName(template.typeID)), label='Enter name for this entry', setvalue=name, maxLength=64)
        if ret:
            item = CCItem()
            item.name = ret
            item.dna = dnaKey
            self.tree.AddItem(item)
            self.UpdateContent()
            return 1

    def DoClonePerfect(self):
        if eve.session.stationid:
            if eve.session.role & ROLE_WORLDMOD:
                ship = sm.GetService('clientDogmaIM').GetDogmaLocation().GetDogmaItem(util.GetActiveShip())
                if ship is None:
                    return
                tname = GetTypeName(ship.typeID)
                Progress('Clone %s' % tname, 'Executing copyship command...', 0, 1)
                Slash('/copyship %s 1' % util.GetActiveShip())
                Progress('Clone %s' % tname, 'Done', 1, 1)
                return

    def DoClone(self):
        dna.Ship().ImportFromShip().Assemble(clone=1)

    def DoShowInfo(self, node = None):
        dna.Ship().ImportFromShip().ShowInfo()


class DNAGroup(listentry.Group):
    __guid__ = 'listentry.DNAGroup'
    __update_on_reload__ = 1

    def Load(self, node):
        listentry.Group.Load(self, node)
        if node.raceID:
            self.sr.icon.LoadIcon('ui_19_128_%d' % node.raceID, ignoreSize=True)
            self.sr.icon.SetSize(16, 16)
            self.sr.icon.state = uiconst.UI_DISABLED

    def GetMenu(self):
        node = self.sr.node
        m = []
        if not node.open:
            m += [(('Expand', '25_11'), self.Toggle, ())]
        else:
            m += [(('Collapse', '25_12'), self.Toggle, ())]
        if node.Get('state', None) != 'locked':
            m += [None,
             (('New Folder', 'res:/ui/Texture/WindowIcons/smallfolder.png', 0.125), (None, self.CreateFolder)[not node.locked]),
             None,
             (('Change Label', 'ui_7_64_15'), (None, self.ChangeLabel)[not node.locked]),
             (('Delete Folder', '04_16'), self.DeleteFolder)]
        spiffy.CreateMenu(m)

    def GetDragData(self, *args):
        if self.sr.node.locked:
            return []
        nodes = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        if eve.session.role & ROLE_PLAYER:
            for node in nodes:
                node.__guid__ = 'xtriui.TypeIcon'

        else:
            for node in nodes:
                node.__guid__ = DNAGroup.__guid__

        if len(nodes) == 1:
            return nodes
        return []

    def CreateFolder(self):
        node = self.sr.node
        if not node.open:
            self.Toggle()
        sm.GetService(SERVICENAME).GroupAdd(parent=node.id[1])


class DNAEntry(listentry.Generic):
    __guid__ = 'listentry.DNAEntry'
    __update_on_reload__ = 1

    def Load(self, *args, **kwargs):
        listentry.Generic.Load(self, *args, **kwargs)
        self.hint = ''

    def GetDragData(self, *args):
        if self.sr.node.locked:
            return []
        nodes = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        if eve.session.role & ROLE_PLAYER:
            for node in nodes:
                node.__guid__ = 'xtriui.TypeIcon'

        else:
            for node in nodes:
                node.__guid__ = DNAEntry.__guid__

        if len(nodes):
            return filter(lambda n: not isinstance(n.panel, listentry.Group), nodes)
        else:
            return nodes

    def GetMenu(self):

        def cf(func, condition = True):
            if condition:
                return func
            return False

        node = self.sr.node
        selected = node.scroll.GetSelectedNodes(node)
        multi = len(selected) > 1
        m = []
        if multi:
            m += [(('Delete Setups...', '04_16'), self.Delete, (selected,))]
        else:
            item = node.id[1]
            m += dna.Ship(dnaKey=item.dna, name=item.name).GetMenuInline(store=False)
            m += [None, (('Rename Setup...', 'ui_7_64_15'), self.Rename), (('Delete Setup...', '04_16'), self.Delete)]
        spiffy.CreateMenu(m)

    def OnMouseUp(self, *args):
        try:
            item = self.sr.node.id[1]
            sm.GetService(SERVICENAME).ShowDNA(name=item.name, dnaKey=item.dna)
        except:
            sys.exc_clear()

    def Delete(self, nodes = None):
        if not nodes:
            nodes = [self.sr.node]
        text = 'You are about to delete the setup(s):<br>'
        for node in nodes:
            text += '  %s<br>' % node.id[1].name

        text += '<br>Are you sure?'
        ret = sm.GetService('gameui').MessageBox(title='Delete Stuff', text=text, buttons=uiconst.OKCANCEL, icon=uiconst.WARNING)
        if ret[0] != uiconst.ID_OK:
            return
        for node in nodes:
            if node.locked:
                node.id[1].fromItem.Remove()
            else:
                node.id[1].Remove()

        sm.GetService(SERVICENAME).UpdateContent()

    def Rename(self):
        item = self.sr.node.id[1]
        if self.sr.node.locked:
            item = item.fromItem
        ret = uiutil.NamePopup(caption='Rename %s DNA' % self.sr.node.typename, label='Enter new name', setvalue=item.name, maxLength=32)
        if ret:
            newname = ret
            if item.name != newname:
                item.name = newname
                sm.GetService(SERVICENAME).UpdateContent()

    def OnDropData(self, dragObj, these, *args):
        if self.sr.node.locked:
            return
        sm.GetService(SERVICENAME).FolderAdoptNodes(self.sr.node.id[1].parent, these)
