#Embedded file name: eve/client/script/ui/inflight\moonscan.py
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
from carbonui.util.various_unsorted import SortListOfTuples
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.eveScroll import Scroll
import localization
from utillib import KeyVal

class MoonScanView(Container):
    __update_on_reload__ = 1

    def Startup(self):
        self.sr.scroll = Scroll(parent=self)
        self.sr.scroll.sr.id = 'moonsurveyscroll'

    def ClearAll(self, *args):
        sm.GetService('moonScan').Clear()

    def Clear(self):
        self.sr.scroll.Clear()

    def SetEntries(self, entries):
        scrolllist = []
        entries = SortListOfTuples([ (celestialID, (celestialID, products)) for celestialID, products in entries.iteritems() ])
        for celestialID, products in entries:
            data = {'GetSubContent': self.GetSubContent,
             'MenuFunction': self.GetMenu,
             'label': cfg.evelocations.Get(celestialID).name,
             'groupItems': products,
             'id': ('moon', celestialID),
             'tabs': [],
             'state': 'locked',
             'showlen': 0}
            scrolllist.append(listentry.Get('Group', data))

        scrolllist.append(listentry.Get('Space', {'height': 64}))
        pos = self.sr.scroll.GetScrollProportion()
        self.sr.scroll.Load(contentList=scrolllist, headers=[localization.GetByLabel('UI/Inflight/Scanner/MoonProduct'), localization.GetByLabel('UI/Inflight/Scanner/Abundance')], scrollTo=pos)

    def GetSubContent(self, data, *args):
        scrolllist = []
        for typeID, quantity in data.groupItems.iteritems():
            data = KeyVal()
            data.label = '%s<t>%s' % (cfg.invtypes.Get(typeID).name, quantity)
            data.typeID = typeID
            data.GetMenu = self.OnGetEntryMenu
            data.itemID = None
            data.getIcon = 1
            scrolllist.append(listentry.Get('Item', data=data))

        return scrolllist

    def GetMenu(self, entry, *args):
        celestialID = entry.id[1]
        note = ''
        for typeID, quantity in entry.groupItems.iteritems():
            note += '%s [%s]<br>' % (cfg.invtypes.Get(typeID).name, quantity)

        celestialMenu = sm.GetService('menu').CelestialMenu(celestialID, hint=note)
        return celestialMenu + [None] + [(MenuLabel('UI/Common/Delete'), self.ClearEntry, (celestialID,))]

    def ClearEntry(self, celestialID, *args):
        sm.GetService('moonScan').ClearEntry(celestialID)

    def OnGetEntryMenu(self, entry, *args):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(None, entry.sr.node.typeID)
