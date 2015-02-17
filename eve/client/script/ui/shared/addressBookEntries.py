#Embedded file name: eve/client/script/ui/shared\addressBookEntries.py
"""
Main people and places window
"""
import uicontrols
import uiprimitives
import uicls
import carbonui.const as uiconst
import uix
import uiutil
import uthread
import localization
import blue
import service

class PlaceEntry(uicontrols.SE_BaseClassCore):
    __guid__ = 'listentry.PlaceEntry'
    __nonpersistvars__ = []
    isDragObject = True

    def Startup(self, *etc):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=6, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.sr.icon = uicontrols.Icon(icon='res:/ui/Texture/WindowIcons/personallocations.png', parent=self, pos=(4, 1, 16, 16), align=uiconst.RELATIVE, ignoreSize=True)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.sr.label.left = 24 + data.Get('sublevel', 0) * 16
        self.sr.icon.left = 4 + data.Get('sublevel', 0) * 16
        self.sr.bm = data.bm
        self.sr.label.text = data.label
        self.id = self.sr.bm.bookmarkID
        self.groupID = self.sr.node.listGroupID
        if self.sr.node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        if self.sr.bm.itemID and self.sr.bm.itemID == sm.GetService('starmap').GetDestination():
            self.sr.label.color.SetRGB(1.0, 1.0, 0.0, 1.0)
        elif self.sr.bm.locationID == session.solarsystemid2:
            self.sr.label.color.SetRGB(0.5, 1.0, 0.5, 1.0)
        else:
            self.sr.label.color.SetRGB(1.0, 1.0, 1.0, 1.0)
        self.EnableDrag()
        dropDataFunc = getattr(node, 'DropData')
        if dropDataFunc is not None:
            self.OnDropData = dropDataFunc

    def GetHeight(_self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 4
        return node.height

    def OnMouseHover(self, *args):
        uthread.new(self.SetHint)

    def SetHint(self, *args):
        if not (self.sr and self.sr.node):
            return
        bookmark = self.sr.node.bm
        hint = self.sr.node.hint
        destination = sm.GetService('starmap').GetDestination()
        if destination is not None and destination == bookmark.itemID:
            hint = localization.GetByLabel('UI/PeopleAndPlaces/BookmarkHintCurrent', hintText=hint)
        else:
            hint = localization.GetByLabel('UI/PeopleAndPlaces/BookmarkHint', hintText=hint)
        self.hint = hint

    def OnDblClick(self, *args):
        sm.GetService('addressbook').EditBookmark(self.sr.bm)

    def OnClick(self, *args):
        self.sr.node.scroll.SelectNode(self.sr.node)
        eve.Message('ListEntryClick')
        if self.sr.node.Get('OnClick', None):
            self.sr.node.OnClick(self)

    def ShowInfo(self, *args):
        sm.GetService('info').ShowInfo(const.typeBookmark, self.sr.bm.bookmarkID)

    def GetDragData(self, *args):
        ret = []
        for each in self.sr.node.scroll.GetSelectedNodes(self.sr.node):
            if not hasattr(each, 'itemID'):
                continue
            if isinstance(each.itemID, tuple):
                self.DisableDrag()
                eve.Message('CantTradeMissionBookmarks')
                return []
            ret.append(each)

        return ret

    def GetMenu(self):
        selected = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        multi = len(selected) > 1
        m = []
        bmIDs = [ entry.bm.bookmarkID for entry in selected if entry.bm ]
        if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            bmids = []
            if len(bmIDs) > 10:
                text = uiutil.MenuLabel('UI/PeopleAndPlaces/BookmarkIDTooMany')
            else:
                idString = bmIDs
                text = uiutil.MenuLabel('UI/PeopleAndPlaces/BookmarkIDs', {'bookmarkIDs': idString})
            m += [(text, self.CopyItemIDToClipboard, (bmIDs,)), None]
            m.append(None)
        eve.Message('ListEntryClick')
        readonly = 0
        for bmID in bmIDs:
            if isinstance(bmID, tuple):
                readonly = 1

        if not multi:
            m += sm.GetService('menu').CelestialMenu(selected[0].bm.itemID, bookmark=selected[0].bm)
            if not readonly:
                m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/EditViewLocation'), sm.GetService('addressbook').EditBookmark, (selected[0].bm,)))
        elif not readonly:
            m.append((uiutil.MenuLabel('UI/Inflight/RemoveBookmark'), self.Delete, (bmIDs,)))
        if self.sr.node.Get('GetMenu', None) is not None:
            m += self.sr.node.GetMenu(self.sr.node)
        return m

    def CopyItemIDToClipboard(self, itemID):
        blue.pyos.SetClipboardData(str(itemID))

    def Approach(self, *args):
        bp = sm.GetService('michelle').GetRemotePark()
        if bp:
            bp.CmdGotoBookmark(self.sr.bm.bookmarkID)

    def WarpTo(self, *args):
        bp = sm.GetService('michelle').GetRemotePark()
        if bp:
            bp.CmdWarpToStuff('bookmark', self.sr.bm.bookmarkID)

    def Delete(self, bmIDs = None):
        ids = bmIDs or [ entry.bm.bookmarkID for entry in self.sr.node.scroll.GetSelected() ]
        if ids:
            sm.GetService('addressbook').DeleteBookmarks(ids)

    def OnMouseDown(self, *args):
        bookMarkInfo = self.sr.bm
        sm.GetService('menu').TryExpandActionMenu(itemID=bookMarkInfo.itemID, clickedObject=self, bookmarkInfo=bookMarkInfo)

    def GetRadialMenuIndicator(self, create = True, *args):
        indicator = getattr(self, 'radialMenuIndicator', None)
        if indicator and not indicator.destroyed:
            return indicator
        if not create:
            return
        self.radialMenuIndicator = uiprimitives.Fill(bgParent=self, color=(1, 1, 1, 0.1), name='radialMenuIndicator')
        return self.radialMenuIndicator

    def ShowRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=True)
        indicator.display = True

    def HideRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=False)
        if indicator:
            indicator.display = False

    @classmethod
    def GetCopyData(cls, node):
        return node.label
