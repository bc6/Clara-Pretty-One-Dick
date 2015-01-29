#Embedded file name: eve/devtools/script\svc_typebrowser.py
import blue
import uix
import uiutil
import listentry
import util
import uthread
import carbonui.const as uiconst
import uicontrols
import uiprimitives
from service import Service, ROLEMASK_ELEVATEDPLAYER

class TypeDBEntry(listentry.Generic):
    __guid__ = 'listentry.TypeDBEntry'

    def GetMenu(self, *args):
        row = self.sr.node.invtype
        catID = cfg.invgroups.Get(row.groupID).categoryID
        it = cfg.invtypes.GetIfExists(row.typeID)
        graphicFileMenu = []
        if it.graphicID is not None:
            graphic = cfg.graphics.GetIfExists(it.graphicID)
            if graphic is not None:
                graphicFile = getattr(graphic, 'graphicFile', 'None')
                graphicFileMenu = [['Copy graphicID (%s)' % row.graphicID, lambda *x: blue.pyos.SetClipboardData(str(row.graphicID)), ()], ['Copy graphicFile (%s)' % graphicFile, lambda *x: blue.pyos.SetClipboardData(graphicFile), ()]]
        averagePrice = cfg.invtypes.Get(row.typeID).averagePrice
        if averagePrice is None:
            averagePrice = 'n/a'
        else:
            averagePrice = util.FmtISK(averagePrice)
        menu = [['Preview', lambda *x: uthread.new(sm.StartService('preview').PreviewType, row.typeID), ()]]
        menu += graphicFileMenu
        menu += [['Copy typeID (%s)' % row.typeID, lambda *x: blue.pyos.SetClipboardData(str(row.typeID)), ()],
         ['Copy groupID (%s)' % row.groupID, lambda *x: blue.pyos.SetClipboardData(str(row.groupID)), ()],
         ['Copy categoryID (%s)' % catID, lambda *x: blue.pyos.SetClipboardData(str(catID)), ()],
         ['Average price: %s' % averagePrice, lambda *x: blue.pyos.SetClipboardData(averagePrice), ()],
         ['View market details', lambda *x: uthread.new(sm.StartService('marketutils').ShowMarketDetails, row.typeID, None), ()],
         None]
        menu += sm.GetService('menu').GetGMTypeMenu(row.typeID)
        return menu


class TypeBrowser(Service):
    __guid__ = 'svc.itemdb'
    __neocommenuitem__ = (('Type Browser', 'res:/ui/Texture/WindowIcons/info.png'), 'Show', ROLEMASK_ELEVATEDPLAYER)

    def __init__(self):
        Service.__init__(self)

    def Show(self):
        self.wnd = wnd = uicontrols.Window.GetIfOpen(windowID='typedb')
        if wnd:
            self.wnd.Maximize()
            return
        self.wnd = wnd = uicontrols.Window.Open(windowID='typedb')
        wnd.SetWndIcon(None)
        wnd.SetMinSize([350, 270])
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Type Browser')
        mainpar = uiutil.GetChild(wnd, 'main')
        wnd.sr.tabs = uicontrols.TabGroup(name='tabsparent', parent=mainpar)
        main = uiprimitives.Container(name='main', parent=mainpar, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        body = uiprimitives.Container(name='body', parent=main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        wnd.sr.browser = uicontrols.Scroll(name='scroll', parent=body, pos=(0, 0, 0, 0))
        wnd.sr.browser.multiSelect = False
        wnd.sr.browser.Startup()
        searchParent = uiprimitives.Container(name='search', parent=body, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        searchTop = uiprimitives.Container(name='search', parent=searchParent, height=25, align=uiconst.TOTOP)
        btn = uicontrols.Button(parent=searchTop, label='Search', func=self.Search, align=uiconst.TORIGHT)
        wnd.sr.input = uicontrols.SinglelineEdit(name='Search', parent=searchTop, width=-1, left=1, align=uiconst.TOALL)
        uiprimitives.Container(name='div', parent=searchParent, height=5, align=uiconst.TOTOP)
        wnd.sr.input.OnReturn = self.Search
        wnd.sr.scroll = uicontrols.Scroll(parent=searchParent)
        wnd.sr.scroll.multiSelect = False
        wnd.sr.tabs.Startup([['Browse',
          wnd.sr.browser,
          self,
          0], ['Search',
          searchParent,
          self,
          1]], 'typebrowsertabs')
        self.Search()
        stuff = self.GetContent(None, False)
        wnd.sr.browser.Load(contentList=stuff, headers=['Name', 'typeID'])
        wnd.sr.browser.Sort('Name')

    def GetContent(self, node, newitems = 0):
        if node is None:
            rows = cfg.invcategories
            level = 0
        elif node.sublevel == 0:
            rows = [ g for g in cfg.invgroups if g.categoryID == node.id[1] ]
            level = 1
        else:
            rows = [ cfg.invtypes.Get(line.typeID) for line in cfg.invtypes if line.groupID == node.id[1] ]
            level = 2
        stuff = []
        if level != 2:
            rows = sorted(rows, key=lambda row: row.name)
            for row in rows:
                data = {'GetSubContent': self.GetContent,
                 'MenuFunction': self.Menu,
                 'label': row.name,
                 'id': (row.name, row.id),
                 'groupItems': [],
                 'showlen': False,
                 'sublevel': level,
                 'state': 'locked',
                 'selected': 0,
                 'hideExpander': True,
                 'BlockOpenWindow': 1,
                 'hideFill': True}
                stuff.append(listentry.Get('Group', data))

        else:
            for row in rows:
                data = util.KeyVal()
                data.sublevel = 2
                data.label = '%s<t>%d' % (row.name, row.typeID)
                data.invtype = row
                data.showinfo = 1
                data.typeID = row.typeID
                stuff.append(listentry.Get('TypeDBEntry', data=data))

        return stuff

    def Menu(self, node, *args):
        ids = []
        if node.sublevel == 0:
            categoryID = node.id[1]
            for typeOb in cfg.invtypes:
                if typeOb.categoryID == categoryID:
                    ids.append(typeOb.typeID)

        else:
            groupID = node.id[1]
            for typeOb in cfg.invtypes:
                if typeOb.groupID == groupID:
                    ids.append(typeOb.typeID)

        def _crea(listOftypeIDs, what = '/createitem', qty = 1, maxValue = 2147483647):
            if uicore.uilib.Key(uiconst.VK_SHIFT):
                result = uix.QtyPopup(maxvalue=maxValue, minvalue=1, caption=what, label=u'Quantity', hint='')
                if result:
                    qty = result['qty']
                else:
                    return
            for typeID in listOftypeIDs:
                sm.StartService('slash').SlashCmd('/createitem %d %d' % (typeID, qty))

        def _load(listOftypeIDs, what = '/load', qty = 1, maxValue = 2147483647):
            if uicore.uilib.Key(uiconst.VK_SHIFT):
                result = uix.QtyPopup(maxvalue=maxValue, minvalue=1, caption=what, label=u'Quantity', hint='')
                if result:
                    qty = result['qty']
                else:
                    return
            for typeID in listOftypeIDs:
                sm.StartService('slash').SlashCmd('/load me %d %d' % (typeID, qty))

        l = [None, ('WM: create all of these', lambda *x: _crea(ids)), ('GM: load me all of these', lambda *x: _load(ids))]
        return l

    def Load(self, *args):
        pass

    def Search(self, *args):
        scroll = self.wnd.sr.scroll
        scroll.sr.id = 'searchreturns'
        search = self.wnd.sr.input.GetValue().lower()
        if not search:
            scroll.Load(contentList=[listentry.Get('Generic', {'label': u'Type in search string and press "Search"'})])
            return
        scroll.Load(contentList=[])
        scroll.ShowHint(u'Searching')
        matches = sm.GetService('slash').MatchTypes(search, smart=False)
        if matches:
            matches.sort()
            stuff = []
            for name, rec in matches:
                data = util.KeyVal()
                data.label = '%d<t>%s' % (rec.typeID, rec.name)
                data.invtype = rec
                data.showinfo = 1
                data.typeID = rec.typeID
                stuff.append(listentry.Get('TypeDBEntry', data=data))
                blue.pyos.BeNice()

        else:
            stuff = [listentry.Get('Generic', {'label': u'Nothing found with "%(search)s" in its name' % {'search': search}})]
        scroll.ShowHint()
        scroll.Load(contentList=stuff, headers=['typeID', 'Name'])

    def Hide(self):
        if self.wnd:
            self.wnd.Close()
            self.wnd = None
