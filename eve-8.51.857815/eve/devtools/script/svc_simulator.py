#Embedded file name: eve/devtools/script\svc_simulator.py
import uicontrols
import uiprimitives
from service import *
import blue
import uiutil
import listentry
import util
import carbonui.const as uiconst
from math import sqrt, exp, log
import const
SERVICENAME = 'capsim'

class Simulator:

    def __init__(self, mods):
        self.data = sim = []
        for a in mods:
            duration = getattr(a, 'speed', 0) or a.duration
            sim.append([a.capacitorNeed, long(duration * 10000), 0L])

    def Reset(self):
        for x in self.data:
            x[2] = 0L

    def Run(self, capacitorCapacity, rechargeRate):
        capacitor = capacitorCapacity
        tauThingy = float(const.dgmTauConstant) * (rechargeRate / 5.0)
        currentTime = nextTime = 0L
        while capacitor > 0.0 and nextTime < const.DAY:
            capacitor = (1.0 + (sqrt(capacitor / capacitorCapacity) - 1.0) * exp((currentTime - nextTime) / tauThingy)) ** 2 * capacitorCapacity
            currentTime = nextTime
            nextTime = const.DAY
            for data in self.data:
                if data[2] == currentTime:
                    data[2] += data[1]
                    capacitor -= data[0]
                nextTime = min(nextTime, data[2])

        if capacitor > 0.0:
            self.duration = const.DAY
            return const.DAY
        self.duration = currentTime
        return currentTime


class SimulatorService(Service):
    __module__ = __name__
    __doc__ = 'Capacitor Simulator'
    __exportedcalls__ = {'Show': []}
    __notifyevents__ = ['ProcessRestartUI', 'OnItemChange', 'OnClientReady']
    __dependencies__ = []
    __guid__ = 'svc.capsim'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME.capitalize()
    __neocommenuitem__ = (('Cap Simulator', 'ui_1_64_1'), 'Show', ROLEMASK_ELEVATEDPLAYER)

    def Run(self, *args):
        self.wnd = None
        self.checked = {}

    def Stop(self, memStream = None):
        self.Hide()
        Service.Stop(self, memStream)

    def Show(self):
        if self.wnd:
            self.wnd.Maximize()
            return
        self.wnd = wnd = uicontrols.Window.Open(windowID='Cap Simulator')
        wnd._OnClose = self.Hide
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Capacitor Simulator')
        wnd.SetMinSize([256, 384])
        main = uiprimitives.Container(name='main', parent=uiutil.GetChild(wnd, 'main'), pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        bottom = uiprimitives.Container(name='bottom', parent=main, align=uiconst.TOBOTTOM, height=60)
        wnd.sr.text = uicontrols.Label(text='<br><br><br><br>', parent=bottom, align=uiconst.TOALL, left=const.defaultPadding, state=uiconst.UI_NORMAL)
        wnd.sr.scroll = uicontrols.Scroll(name='attributescroll', parent=main)
        wnd.sr.scroll.sr.id = 'capsim_modulescroll'
        wnd.sr.scroll.hiliteSorted = 0
        btns = uicontrols.ButtonGroup(btns=[['Run Simulation',
          self.Simulate,
          (),
          None]], parent=main, idx=0, unisize=0)
        self.Load()
        wnd.Maximize(1)

    def Hide(self, *args):
        if self.wnd:
            self.wnd.Close()
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def Load(self):
        d = {}
        dgm = sm.GetService('godma')
        for item in sm.GetService('invCache').GetInventoryFromId(eve.session.shipid).ListHardwareModules():
            a = dgm.GetItem(item.itemID)
            if (getattr(a, 'speed', 0) or getattr(a, 'duration', 0)) and getattr(a, 'capacitorNeed'):
                d[item.flagID] = a

        mods = []
        for x in (const.flagHiSlot0, const.flagMedSlot0, const.flagLoSlot0):
            for flag in range(x, x + 8):
                if flag in d:
                    mods.append(d[flag])

        self.mods = mods
        del d
        scrollList = []
        for a in mods:
            e = listentry.Get('AttributeCheckbox', {'line': 1,
             'info': a,
             'label': cfg.invgroups.Get(a.groupID).name,
             'iconID': a.iconID,
             'item': a,
             'text': a.name,
             'hint': a.name,
             'cfgname': a.itemID,
             'retval': a.itemID,
             'checked': self.checked.get(a.itemID, True),
             'OnChange': self.OnModuleSelectedChanged})
            scrollList.append(e)

        if self.wnd:
            self.wnd.sr.scroll.Load(contentList=scrollList)
            self.wnd.sr.text.text = 'Sustainable: ???'

    def OnClientReady(self, *args):
        if self.wnd:
            self.Load()

    def OnItemChange(self, item, change):
        if item.locationID == eve.session.shipid and change.get(const.ixLocationID, 0) != eve.session.shipid:
            self.checked[item.itemID] = True
            self.Load()
        if item.locationID != eve.session.shipid and change.get(const.ixLocationID, 0) == eve.session.shipid:
            if item.itemID in self.checked:
                del self.checked[item.itemID]
            self.Load()

    def OnModuleSelectedChanged(self, obj):
        itemID = obj.parent.sr.node.info.itemID
        self.checked[itemID] = obj.checked

    def Simulate(self):

        def Progress(current, total):
            sm.GetService('loading').ProgressWnd('Running Simulation', 'Please wait...', current, total)
            blue.pyos.synchro.Yield()

        dgm = sm.GetService('godma')
        ship = dgm.GetItem(eve.session.shipid)
        mods = [ a for a in self.mods if self.checked.get(a.itemID, True) ]
        Progress(0, 1)
        sim = Simulator(mods)
        sim.Run(ship.capacitorCapacity, ship.rechargeRate)
        duration = sim.duration
        t = self.wnd.sr.text
        if sim.duration == const.DAY:
            colorTag = '<color=0xFF00FF00>'
            t.text = 'Sustainable: %sIndefinitely</color><br>' % colorTag
        else:
            colorTag = '<color=0xFFFF0000>'
            t.text = 'Sustainable: %s%s</color><br>' % (colorTag, util.FmtTimeInterval(sim.duration, breakAt='sec'))
        i = 1
        if sim.duration < const.DAY:
            sustainCapacity = ship.capacitorCapacity
            while sim.duration < const.DAY and i < 32:
                failCapacity = sustainCapacity
                sustainCapacity *= 2.0
                sim.Reset()
                sim.Run(sustainCapacity, ship.rechargeRate)
                i += 1

        else:
            failCapacity = ship.capacitorCapacity
            while sim.duration == const.DAY and i < 32:
                sustainCapacity = failCapacity
                failCapacity /= 2.0
                sim.Reset()
                sim.Run(failCapacity, ship.rechargeRate)
                i += 1

        totalSteps = int(log(sustainCapacity - failCapacity) / log(2) + 1.5) * 2 + 1
        while sustainCapacity - failCapacity > 1 and i < 32:
            Progress(min(i, totalSteps / 2 - 1), totalSteps)
            tryCapacity = (sustainCapacity + failCapacity) / 2.0
            sim.Reset()
            sim.Run(tryCapacity, ship.rechargeRate)
            if sim.duration < const.DAY:
                failCapacity = tryCapacity
            else:
                sustainCapacity = tryCapacity
            i += 1

        sustainRecharge = ship.rechargeRate / 1000.0
        t.text = t.text + 'Minimum cap/recharge needed for sustainability:<br>'
        t.text = t.text + '- %s%.2f cap</color> / %0.2f sec (ratio: %.2f)<br>' % (colorTag,
         sustainCapacity,
         sustainRecharge,
         sustainCapacity / sustainRecharge)
        Progress(1, 2)
        sim.duration = duration
        i = 1
        if sim.duration < const.DAY:
            sustainRecharge = ship.rechargeRate
            while sim.duration < const.DAY and i < 32:
                failRecharge = sustainRecharge
                sustainRecharge /= 2.0
                sim.Reset()
                sim.Run(ship.capacitorCapacity, sustainRecharge)
                i += 1

        else:
            failRecharge = ship.rechargeRate
            while sim.duration == const.DAY and i < 32:
                sustainRecharge = failRecharge
                failRecharge *= 2.0
                sim.Reset()
                sim.Run(ship.capacitorCapacity, failRecharge)
                i += 1

        totalSteps = int(log(failRecharge - sustainRecharge) / log(2) + 0.5)
        while failRecharge - sustainRecharge > 500 and i < 32:
            Progress(min(i + totalSteps, totalSteps * 2 - 1), totalSteps * 2)
            tryRecharge = (sustainRecharge + failRecharge) / 2.0
            sim.Reset()
            sim.Run(ship.capacitorCapacity, tryRecharge)
            if sim.duration < const.DAY:
                failRecharge = tryRecharge
            else:
                sustainRecharge = tryRecharge
            i += 1

        sustainRecharge = sustainRecharge / 1000.0
        sustainCapacity = ship.capacitorCapacity
        t.text = t.text + '- %.2f cap / %s%0.2f</color> sec (ratio: %.2f)<br>' % (sustainCapacity,
         colorTag,
         sustainRecharge,
         sustainCapacity / sustainRecharge)
        Progress(1, 1)


exports = {}
