#Embedded file name: eve/client/script/ui/inflight\baseTacticalEntry.py
import uicontrols
import uiprimitives
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import telemetry
import util
import state
import base

class BaseTacticalEntry(listentry.Generic):
    __guid__ = 'listentry.BaseTacticalEntry'
    __notifyevents__ = ['OnStateChange']
    __update_on_reload__ = 1
    gaugesInited = 0
    gaugesVisible = 0

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        sm.RegisterNotify(self)

    @telemetry.ZONE_METHOD
    def Load(self, node):
        data = node
        selected, = sm.GetService('state').GetStates(data.itemID, [state.selected])
        node.selected = selected
        listentry.Generic.Load(self, node)
        self.sr.label.left = 20 + 16 * data.sublevel
        self.UpdateDamage()
        self.sr.label.Update()

    def UpdateDamage(self):
        if self.destroyed:
            self.sr.dmgTimer = None
            return
        if not util.InBubble(self.GetShipID()):
            self.HideDamageDisplay()
            return False
        d = self.sr.node
        if not getattr(d, 'slimItem', None):
            typeOb = cfg.invtypes.Get(d.typeID)
            groupID = typeOb.groupID
            categoryID = typeOb.categoryID
        else:
            slimItem = d.slimItem()
            if not slimItem:
                self.HideDamageDisplay()
                return False
            groupID = slimItem.groupID
            categoryID = slimItem.categoryID
        shipID = self.GetShipID()
        ret = False
        if shipID and categoryID in (const.categoryShip, const.categoryDrone):
            dmg = self.GetDamage(shipID)
            if dmg is not None:
                ret = self.SetDamageState(dmg)
                if self.sr.dmgTimer is None:
                    self.sr.dmgTimer = base.AutoTimer(1000, self.UpdateDamage)
            else:
                self.HideDamageDisplay()
        return ret

    def ShowDamageDisplay(self):
        self.InitGauges()

    def HideDamageDisplay(self):
        if self.gaugesInited:
            self.sr.gaugeParent.state = uiconst.UI_HIDDEN

    def GetDamage(self, itemID):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            self.sr.dmgTimer = None
            return
        ret = bp.GetDamageState(itemID)
        if ret is None:
            self.sr.dmgTimer = None
        return ret

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('height', 0) or 32
        return node.height

    def GetMenu(self):
        return sm.GetService('menu').CelestialMenu(self.sr.node.itemID)

    def GetShipID(self):
        if self.sr.node:
            return self.sr.node.itemID

    def OnMouseEnter(self, *args):
        listentry.Generic.OnMouseEnter(self, *args)
        if self.sr.node:
            sm.GetService('state').SetState(self.sr.node.itemID, state.mouseOver, 1)

    def OnMouseExit(self, *args):
        listentry.Generic.OnMouseExit(self, *args)
        if self.sr.node:
            sm.GetService('state').SetState(self.sr.node.itemID, state.mouseOver, 0)

    def OnStateChange(self, itemID, flag, isActive, *args):
        if util.GetAttrs(self, 'sr', 'node') is None:
            return
        if self.sr.node.itemID != itemID:
            return
        if flag == state.mouseOver:
            if isActive:
                self.ShowHilite()
            else:
                self.HideHilite()
        elif flag == state.selected:
            if isActive:
                self.Select()
            else:
                self.Deselect()

    def Select(self, *args):
        listentry.Generic.Select(self, *args)
        self.sr.node.selected = True

    def Deselect(self, *args):
        listentry.Generic.Deselect(self, *args)
        self.sr.node.selected = False

    def SetDamageState(self, state):
        self.InitGauges()
        visible = 0
        gotDmg = False
        for i, gauge in enumerate((self.sr.gauge_shield, self.sr.gauge_armor, self.sr.gauge_struct)):
            if state[i] is None:
                gauge.state = uiconst.UI_HIDDEN
            else:
                oldWidth = gauge.sr.bar.width
                gauge.sr.bar.width = int(gauge.width * round(state[i], 3))
                if gauge.sr.bar.width < oldWidth:
                    gotDmg = True
                gauge.state = uiconst.UI_DISABLED
                visible += 1

        self.gaugesVisible = visible
        return gotDmg

    def InitGauges(self):
        if self.gaugesInited:
            self.sr.gaugeParent.state = uiconst.UI_NORMAL
            return
        par = uiprimitives.Container(name='gauges', parent=self, align=uiconst.TORIGHT, width=68, height=0, state=uiconst.UI_NORMAL, top=2, idx=0)
        uiprimitives.Container(name='push', parent=par, align=uiconst.TORIGHT, width=4)
        for each in ('SHIELD', 'ARMOR', 'STRUCT'):
            g = uiprimitives.Container(name=each, align=uiconst.TOTOP, width=64, height=9, left=-2)
            uiprimitives.Container(name='push', parent=g, align=uiconst.TOBOTTOM, height=2)
            uicontrols.EveLabelSmall(text=each[:2], parent=g, left=68, top=-1, width=64, height=12, state=uiconst.UI_DISABLED)
            g.name = 'gauge_%s' % each.lower()
            uiprimitives.Line(parent=g, align=uiconst.TOTOP)
            uiprimitives.Line(parent=g, align=uiconst.TOBOTTOM)
            uiprimitives.Line(parent=g, align=uiconst.TOLEFT)
            uiprimitives.Line(parent=g, align=uiconst.TORIGHT)
            g.sr.bar = uiprimitives.Fill(parent=g, align=uiconst.TOLEFT)
            uiprimitives.Fill(parent=g, color=(158 / 256.0,
             11 / 256.0,
             14 / 256.0,
             1.0))
            par.children.append(g)
            setattr(self.sr, 'gauge_%s' % each.lower(), g)

        self.sr.gaugeParent = par
        self.gaugesInited = 1
