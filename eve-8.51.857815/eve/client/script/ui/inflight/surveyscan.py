#Embedded file name: eve/client/script/ui/inflight\surveyscan.py
import uicontrols
import carbonui.const as uiconst
from eve.client.script.ui.control import entries as listentry
import util
import sys
import state
import localization
from eve.client.script.ui.control.entries import Generic
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.container import Container

class SurveyScanView(uicontrols.Window):
    __guid__ = 'form.SurveyScanView'
    default_windowID = 'SurveyScanView'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.targetSvc = sm.GetService('target')
        self.scope = 'inflight'
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.SetCaption(localization.GetByLabel('UI/Inflight/Scanner/SurveyScanResults'))
        self.DefineButtons(uiconst.OK, okLabel=localization.GetByLabel('UI/Inventory/Clear'), okFunc=self.ClearAll)
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.scroll.sr.id = 'surveyscan_scroll'

    def _OnClose(self, *args):
        sm.GetService('surveyScan').Clear()

    def ClearAll(self, *args):
        sm.GetService('surveyScan').Clear()

    def Clear(self):
        self.sr.scroll.Load(contentList=[])

    def SetEntries(self, entries):
        scrolllist = []
        asteroidTypes = {}
        headers = [localization.GetByLabel('UI/Common/Ore'), localization.GetByLabel('UI/Common/Quantity'), localization.GetByLabel('UI/Common/Distance')]
        for ballID, (typeID, qty) in entries.iteritems():
            if not asteroidTypes.has_key(typeID):
                asteroidTypes[typeID] = [(ballID, qty)]
            else:
                asteroidTypes[typeID].append((ballID, qty))

        currentTargets = self.targetSvc.GetTargets()
        scrolllist = []
        for asteroidType in asteroidTypes:
            label = cfg.invtypes.Get(asteroidType).name
            data = {'GetSubContent': self.GetTypeSubContent,
             'label': label,
             'id': ('TypeSel', asteroidType),
             'groupItems': asteroidTypes[asteroidType],
             'typeID': asteroidType,
             'showlen': 1,
             'sublevel': 0,
             'state': 'locked',
             'currentTargetIDs': currentTargets.keys()}
            scrolllist.append(listentry.Get('Group', data))

        scrolllist = localization.util.Sort(scrolllist, key=lambda x: x.label)
        self.sr.scroll.Load(contentList=scrolllist, headers=headers)

    def GetTypeSubContent(self, nodedata, newitems = 0):
        scrolllist = []
        bp = sm.GetService('michelle').GetBallpark()
        for ballID, qty in nodedata.groupItems:
            try:
                dist = bp.DistanceBetween(eve.session.shipid, ballID)
            except:
                dist = 0
                import traceback
                traceback.print_exc()
                sys.exc_clear()

            data = util.KeyVal()
            data.label = cfg.invtypes.Get(nodedata.typeID).name + '<t>' + util.FmtAmt(qty) + '<t>' + util.FmtDist(dist)
            data.itemID = ballID
            data.typeID = nodedata.typeID
            data.GetMenu = self.OnGetEntryMenu
            data.OnClick = self.OnEntryClick
            data.showinfo = 1
            data.isTarget = ballID in nodedata.currentTargetIDs
            data.sublevel = 1
            data.Set('sort_' + localization.GetByLabel('UI/Common/Distance'), dist)
            data.Set('sort_' + localization.GetByLabel('UI/Common/Quantity'), qty)
            entry = listentry.Get(None, data=data, decoClass=SurveyScanEntry)
            scrolllist.append(entry)

        return scrolllist

    def OnEntryClick(self, entry, *args):
        sm.GetService('state').SetState(entry.sr.node.itemID, state.selected, 1)
        if self.targetSvc.IsTarget(entry.sr.node.itemID):
            sm.GetService('state').SetState(entry.sr.node.itemID, state.activeTarget, 1)
        if uicore.uilib.Key(uiconst.VK_CONTROL):
            self.targetSvc.TryLockTarget(entry.sr.node.itemID)
        elif uicore.uilib.Key(uiconst.VK_MENU):
            sm.GetService('menu').TryLookAt(entry.sr.node.itemID)

    def OnGetEntryMenu(self, entry, *args):
        return sm.GetService('menu').CelestialMenu(entry.sr.node.itemID)


class SurveyScanEntry(Generic):

    def ApplyAttributes(self, attributes):
        Generic.ApplyAttributes(self, attributes)
        self.iconCont = Container(parent=self, name='iconCont', pos=(2, 0, 16, 16), align=uiconst.CENTERLEFT)

    def Load(self, node):
        Generic.Load(self, node)
        if node.isTarget:
            self.iconCont.Flush()
            targetSprite = Sprite(parent=self.iconCont, name='targetSprite', pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/classes/Bracket/activeTarget.png')
