#Embedded file name: eve/devtools/script\svc_arena.py
import blue
import os
import sys
import uix
import form
import listentry
import service
from service import *
import carbonui.const as uiconst
import uiprimitives
import uicontrols
ARENA_FILE = 'arena.txt'
IDLE = 1000

class ArenaEntry(listentry.Generic):
    """
        Custom listentry class with right click menus
    """
    __guid__ = 'listentry.ArenaEntry'

    def OnDblClick(self, *args):
        self.Modify()

    def GetMenu(self):
        self.multiple = False
        n = self.sr.node
        count = len(n.scroll.GetSelectedNodes(n))
        if count > 1:
            self.multiple = True
        ret = [('Add Entry', self.Add, ()), ('Modify Entry', self.Modify, ())]
        if self.multiple:
            ret.append(('Delete Entries', self.Delete, ()))
        else:
            ret.append(('Delete Entry', self.Delete, ()))
        return ret

    def Add(self):
        n = self.sr.node
        n.Add()

    def Modify(self):
        n = self.sr.node
        n.Modify(n.index, n.dict)

    def Delete(self):
        n = self.sr.node
        if self.multiple:
            nodes = n.scroll.GetSelectedNodes(n)
            n.MultiDelete(nodes)
        else:
            n.Delete(n.index)


class ArenaSpawn(service.Service):
    __module__ = __name__
    __guid__ = 'svc.arenaspawn'
    __servicename__ = 'arenaspawn'
    __displayname__ = 'Insider Arena Deployment and Management'
    __exportedcalls__ = {'Setup': [ROLE_GMH],
     'Parse': [ROLE_GMH],
     'Deploy': [ROLE_GMH],
     'CleanUp': [ROLE_GMH],
     'GetDeployed': [ROLE_GMH]}
    __notifyevents__ = []
    __neocommenuitem__ = (('Arena Deployment', None), 'Show', ROLE_GMH)

    def __init__(self):
        service.Service.__init__(self)
        self.items = []
        self.created = []
        self.slash = sm.StartService('slash').SlashCmd
        self.insider = sm.StartService('insider')
        self.bp = sm.StartService('michelle').GetBallpark()

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        Service.Run(self, memStream)
        self.wnd = None
        self.state = SERVICE_RUNNING

    def Stop(self, memStream = None):
        self.state = SERVICE_STOP_PENDING
        Service.Stop(self, memStream)
        self.state = SERVICE_STOPPED

    def Setup(self, originID = None, *args):
        if originID is None:
            if eve.session.shipid:
                self.origin = eve.session.shipid
            else:
                return
        else:
            self.origin = int(originID)

    def Show(self, *args):
        form.arena.Open()

    def Parse(self, *args):
        self.created = []
        self.items = None
        INSIDERDIR = self.insider.GetInsiderDir()
        target = os.path.join(INSIDERDIR, ARENA_FILE)
        file = blue.classes.CreateInstance('blue.ResFile')
        if file.Open(target, 0):
            obj = file.Read()
            self.items = obj.split('\r\n')
            file.Close()
        return self.items

    def Deploy(self, arenadict = None, *args):
        if not hasattr(self, 'origin'):
            self.Setup()
        if arenadict is None:
            return
        self.slash('/cloak')
        self.slash('/tr me %d' % self.origin)
        blue.pyos.synchro.SleepWallclock(IDLE)
        for k, v in arenadict.iteritems():
            typeID, qty, x, y, z, text = v
            spawnID = self.slash('/spawn %d qty=%d offset=%s,%s,%s name="%s"' % (int(typeID),
             int(qty),
             x,
             y,
             z,
             text))
            self.created.append(spawnID)

        return self.created

    def CleanUp(self, *args):
        if not self.created:
            return
        bp = [ id for id in sm.StartService('michelle').GetBallpark().balls.keys() ]
        for itemID in self.created:
            if itemID in bp:
                self.slash('/unspawn %d' % itemID)

    def GetDeployed(self, *args):
        return self.created

    def GetOrigin(self, *args):
        if not hasattr(self, 'origin'):
            return eve.session.shipid
        return self.origin

    def GetMaxIndex(self, *args):
        return len(self.items)


class ArenaForm(uicontrols.Window):
    """
        Window form for arena management and deployment
    """
    __guid__ = 'form.arena'
    default_windowID = 'arena'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.svc = sm.StartService('arenaspawn')
        self.raw = []
        self.arena = {}
        self.originID = None
        self.SetMinSize([330, 200])
        self.SetWndIcon(None)
        self.SetCaption('Arena Deployment')
        self.SetTopparentHeight(0)
        margin = const.defaultPadding
        main = uiprimitives.Container(name='main', parent=self.sr.main, pos=(margin,
         margin,
         margin,
         margin))
        uicontrols.Frame(parent=main, color=(1.0, 1.0, 1.0, 0.2), idx=0)
        bottom = uiprimitives.Container(name='btm', parent=main, height=30, align=uiconst.TOBOTTOM)
        btns = [['Set Origin',
          self.SetOrigin,
          None,
          81],
         ['Load File',
          self.Load,
          None,
          81],
         ['Deploy',
          self.Deploy,
          None,
          81],
         ['Open File',
          self.OpenFile,
          True,
          81],
         ['Clean',
          self.Clean,
          True,
          81]]
        btn = uicontrols.ButtonGroup(btns=btns, parent=bottom, unisize=0)
        ostr = self.OriginText()
        push = uiprimitives.Container(name='lpush', parent=main, align=uiconst.TOLEFT, width=const.defaultPadding)
        push = uiprimitives.Container(name='rpush', parent=main, align=uiconst.TORIGHT, width=const.defaultPadding)
        push = uiprimitives.Container(name='tpush', parent=main, align=uiconst.TOTOP, height=const.defaultPadding)
        self.text = uicontrols.Label(text=ostr, parent=main, align=uiconst.TOTOP, name='otext', height=18, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        self.scroll = uicontrols.Scroll(parent=main)
        self.scroll.Load(contentList=[], headers=['ID',
         'Item',
         'Qty',
         'X',
         'Y',
         'Z',
         'Text'], noContentHint=u'No items found')
        self.scroll.sr.id = 'arena'

    def OriginText(self, *args):
        if self.originID is None:
            origin = eve.session.shipid
        else:
            origin = self.originID
        str = '\xe2\x80\xa2 Current Origin: %s' % cfg.evelocations.Get(origin).name
        return str

    def UpdateOriginText(self, id = None, *args):
        if id is None:
            id = eve.session.shipid
        txt = '\xe2\x80\xa2 Current Origin: %s' % cfg.evelocations.Get(id).name
        self.text.text = txt

    def Load(self, *args):
        idx = 0
        self.arena = {}
        self.raw = self.svc.Parse()
        if self.raw is not None:
            for object in self.raw:
                idx += 1
                typeID, qty, x, y, z, text = object.split(':')
                typeID = int(typeID)
                qty = int(qty)
                x = int(x)
                y = int(y)
                z = int(z)
                self.arena[idx] = (typeID,
                 qty,
                 x,
                 y,
                 z,
                 text)

            self.Refresh()

    def Refresh(self, *args):
        contentList = []
        if not hasattr(self, 'maxIdx'):
            self.maxIdx = len(self.arena) + 1
        for index in xrange(1, self.maxIdx):
            if index in self.arena:
                config = self.arena[index]
                typeID, qty, x, y, z, text = config
                objectdict = self.MakeDict(config)
                type = self.Lookup(typeID)
                contentList.append(listentry.Get('ArenaEntry', {'label': '%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s' % (index,
                           type,
                           qty,
                           x,
                           y,
                           z,
                           text),
                 'index': index,
                 'object': object,
                 'dict': objectdict,
                 'Add': self.Add,
                 'Modify': self.Modify,
                 'Delete': self.Delete,
                 'MultiDelete': self.MultiDelete}))

        self.scroll.Load(contentList=contentList, headers=['ID',
         'Item',
         'Qty',
         'X',
         'Y',
         'Z',
         'Text'], noContentHint=u'No items found')

    def Lookup(self, id = None, *args):
        if id is None:
            return
        try:
            ret = '%s' % cfg.invtypes.Get(id).name
            return ret
        except KeyError:
            sys.exc_clear()
            return 'Unknown typeID: %s' % id

    def MakeDict(self, item = None, *args):
        if item is None:
            return
        itemdict = {}
        typeID, qty, x, y, z, text = item
        itemdict['typeID'] = typeID
        itemdict['qty'] = qty
        itemdict['x'] = x
        itemdict['y'] = y
        itemdict['z'] = z
        itemdict['text'] = text
        return itemdict

    def ParseRet(self, ret = None, *args):
        if ret is None:
            return
        typeID = int(ret['typeID'])
        qty = int(ret['qty'])
        x = int(ret['x'])
        y = int(ret['y'])
        z = int(ret['z'])
        text = ret['text']
        return (typeID,
         qty,
         x,
         y,
         z,
         text)

    def SetOrigin(self, *args):
        ret = uix.QtyPopup(caption='Arena Origin', label='itemID of the origin')
        if ret:
            self.originID = int(ret['qty'])
            if self.originID == 0:
                self.originID = None
        self.svc.Setup(self.originID)
        self.UpdateOriginText(self.originID)

    def Deploy(self, *args):
        if not self.arena:
            return
        self.svc.Deploy(self.arena)

    def OpenFile(self, *args):
        INSIDERDIR = sm.StartService('insider').GetInsiderDir()
        target = os.path.join(INSIDERDIR, ARENA_FILE)
        if os.path.exists(target):
            blue.os.ShellExecute(target)

    def Clean(self, *args):
        deployed = self.svc.GetDeployed()
        if deployed:
            self.svc.CleanUp()

    def Add(self, *args):
        a = ArenaPopup(caption='Add New Entry')
        ret = a.Wnd()
        if ret:
            typeID, qty, x, y, z, text = self.ParseRet(ret)
            index = self.maxIdx
            self.arena[index] = (typeID,
             qty,
             x,
             y,
             z,
             text)
            self.maxIdx += 1
            self.Refresh()

    def Modify(self, index = None, details = None, *args):
        if index is None:
            return
        if details is None:
            return
        a = ArenaPopup(caption='Modify Existing Entry', defaults=details)
        ret = a.Wnd()
        if ret:
            self.arena[index] = self.ParseRet(ret)
            self.Refresh()

    def Delete(self, index = None, suppress = False, *args):
        if index is None:
            return
        header = 'Delete field?'
        question = 'Are you sure you wish to remove this entry?'
        if not suppress:
            if eve.Message('CustomQuestion', {'header': header,
             'question': question}, uiconst.YESNO) == uiconst.ID_YES:
                del self.arena[index]
        else:
            del self.arena[index]
        self.Refresh()

    def MultiDelete(self, nodes = None, *args):
        if nodes is None:
            return
        header = 'Delete fields?'
        question = 'Are you sure you wish to remove these entries?'
        if eve.Message('CustomQuestion', {'header': header,
         'question': question}, uiconst.YESNO) == uiconst.ID_YES:
            for node in nodes:
                self.Delete(node.index, True)


class ArenaPopup:
    """
        Custom six field popup form
    """
    __wndname__ = 'ArenaPopup'

    def __init__(self, caption = None, defaults = None):
        values = ['typeID',
         'qty',
         'x',
         'y',
         'z',
         'text']
        if caption is None:
            caption = u'Type in name'
        if defaults is None:
            valuedict = {}
            for entry in values:
                valuedict[entry] = ''

        else:
            valuedict = defaults.copy()
        format = [{'type': 'btline'}]
        for each in values:
            v = '%s' % valuedict[each]
            l = '%s:' % each
            reqd = 1
            if each == 'text':
                reqd = 0
            format += [{'type': 'edit',
              'setvalue': v,
              'key': each,
              'label': l,
              'required': reqd,
              'frame': 1,
              'setfocus': 1,
              'selectall': 0}]

        format += [{'type': 'bbline'}]
        OKCANCEL = 1
        self.popup = uix.HybridWnd(format, caption, 1, None, OKCANCEL, None, minW=240, minH=80)

    def __getitem__(self, *args):
        return args

    def Wnd(self, *args):
        return self.popup
