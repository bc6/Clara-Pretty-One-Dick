#Embedded file name: eve/devtools/script\svc_modtest.py
import uix
import uiutil
import blue
import listentry
import state
import util
import carbonui.const as uiconst
import uiprimitives
import uicontrols
from service import Service, ROLE_QA, ROLE_PROGRAMMER
SERVICENAME = 'modtest'
Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)

class ModTest(Service):
    __exportedcalls__ = {}
    __notifyevents__ = ['ProcessRestartUI']
    __dependencies__ = []
    __guid__ = 'svc.modtest'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME
    __neocommenuitem__ = (('Module Test', '41_4'), 'Show', ROLE_QA)

    def Run(self, memStream = None):
        self.wnd = None
        self.ammo = None

    def InitGroups(self):
        if getattr(self, 'testgroups', None):
            return
        self.testgroups = {}
        t, a, p = self.GetModuleLists()
        t = t + a
        for x in t:
            gid = x[0].groupID
            if gid not in (const.groupSiegeModule,
             const.groupSuperWeapon,
             const.groupJumpPortalGenerator,
             const.groupMiningLaser):
                self.testgroups[gid] = True
            else:
                self.testgroups[gid] = False

    def Stop(self, memStream = None):
        self.Hide()
        Service.Stop(self, memStream)

    def Show(self):
        if not self.wnd:
            self.wnd = wnd = uicontrols.Window.Open(windowID=SERVICENAME)
            wnd._OnClose = self.Hide
            wnd.SetWndIcon(None)
            wnd.SetTopparentHeight(0)
            wnd.SetCaption('Module Test')
            wnd.sr.main = uiutil.GetChild(wnd, 'main')
            wnd.SetMinSize((352, 200))
            main = uiprimitives.Container(name='main', parent=wnd.sr.main, pos=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            uicontrols.Label(text='Select module groups to test', parent=main, align=uiconst.TOTOP, width=10, left=5, top=5, color=None, state=uiconst.UI_DISABLED)
            wnd.sr.scroll = uicontrols.Scroll(parent=main)
            buttons = [['Test',
              self.Test,
              None,
              81], ['Close',
              self.Hide,
              None,
              81]]
            wnd.sr.main.children.insert(0, uicontrols.ButtonGroup(btns=buttons))
            scrolllist = []
            t, a, p = self.GetModuleLists()
            t = t + a
            self.InitGroups()
            for gid in self.testgroups:
                g = cfg.invgroups.Get(gid)
                data = util.KeyVal()
                data.label = g.name
                data.checked = self.testgroups[g.id]
                data.cfgname = g.name.replace(' ', '')
                data.retval = g.id
                data.OnChange = self.CheckBoxChange
                scrolllist.append(listentry.Get('Checkbox', data=data))

            scrolllist.sort(lambda a, b: cmp(a.label, b.label))
            wnd.sr.scroll.Load(contentList=scrolllist)

    def CheckBoxChange(self, checkbox):
        self.testgroups[checkbox.data['retval']] = checkbox.checked

    def Hide(self, *args):
        if self.wnd:
            self.wnd.Close()
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def GetModuleLists(self):
        test = {}
        groups = dict.fromkeys([ g.id for g in cfg.invgroups if g.categoryID == const.categoryModule ])
        for k in cfg.invmetatypesByParent.iterkeys():
            rowset = cfg.invmetatypesByParent[k]
            for row in rowset:
                if row.metaGroupID == 2:
                    rec = cfg.invtypes.Get(row.typeID)
                    if rec.marketGroupID and rec.categoryID == const.categoryModule:
                        test[rec.groupID] = rec

        for line in cfg.invtypes:
            if line.groupID not in test and line.groupID in groups:
                if not cfg.invmetatypesByParent.has_key(line.typeID):
                    rec = cfg.invtypes.Get(line.typeID)
                    if rec.marketGroupID:
                        test[rec.groupID] = rec

        targeted = []
        activated = []
        passive = []
        for rec in test.values():
            effects = [ cfg.dgmeffects.Get(row.effectID) for row in cfg.dgmtypeeffects.get(rec.typeID, []) ]
            effectCategories = [ eff.effectCategory for eff in effects if eff.effectName != 'online' ]
            if const.dgmEffTarget in effectCategories:
                targeted.append((rec, effects))
            elif const.dgmEffActivation in effectCategories:
                activated.append((rec, effects))
            else:
                passive.append((rec, effects))

        return (targeted, activated, passive)

    def GetAmmo(self):
        if getattr(self, 'ammo', None):
            return
        groups = {}
        for g in cfg.invgroups:
            if g.categoryID == const.categoryCharge:
                groups[g.id] = True

        self.ammo = {}
        godma = sm.GetService('godma')
        for line in cfg.invtypes:
            if line.groupID in groups:
                rec = cfg.invtypes.Get(line.typeID)
                if rec.groupID in self.ammo:
                    self.ammo[rec.groupID].append(godma.GetType(rec.typeID))
                else:
                    self.ammo[rec.groupID] = [godma.GetType(rec.typeID)]

    def Test(self, *args):
        if eve.session.stationid:
            return
        self.Hide()

        def _Click(module):
            module.Click()
            while module.sr.glow.state == uiconst.UI_HIDDEN:
                blue.pyos.synchro.SleepWallclock(1)

            try:
                module.Click()
            except:
                pass

        def _Idle(module):
            return module.sr.glow.state == uiconst.UI_HIDDEN and module.sr.busy.state == uiconst.UI_HIDDEN and module.blinking == False and module.reloadingAmmo is False

        def _WaitForIdle(module, timeout = 60000, reason = None):
            if reason:
                print 'WaitForIdle: %s' % reason
            blue.pyos.synchro.SleepWallclock(100)
            timeout -= 100
            while not _Idle(module) and timeout > 0:
                blue.pyos.synchro.SleepWallclock(100)
                timeout -= 100

        self.GetAmmo()
        t, a, p = self.GetModuleLists()
        ship = sm.GetService('godma').GetItem(eve.session.shipid)
        if eve.session.role & ROLE_PROGRAMMER:
            if ship.cpuOutput != 13371337:
                w = sm.RemoteSvc('slash')
                w.SlashCmd('/dogma me cpuOutput = 13371337')
                w.SlashCmd('/dogma me powerOutput = 10000000')
                w.SlashCmd('/dogma me hiSlots = 8')
                w.SlashCmd('/dogma me medSlots = 8')
                w.SlashCmd('/dogma me lowSlots = 8')
                w.SlashCmd('/dogma me rigSlots = 8')
                w.SlashCmd('/dogma me upgradeCapacity = 10000')
                w.SlashCmd('/dogma me turretSlotsLeft = 8')
                w.SlashCmd('/dogma me launcherSlotsLeft = 8')
                w.SlashCmd('/dogma me upgradeSlotsLeft = 8')
                w.SlashCmd('/dogma me capacity = 1000000')
                w.SlashCmd('/dogma me capacitorCapacity = 1000000')
        errors = []
        t = filter(lambda x: self.testgroups[x[0].groupID], t + a)
        total = len(t)
        current = 0
        while t:
            sm.RemoteSvc('slash').SlashCmd('/unload me all')
            slotsLeft = {'hiPower': [ x + const.flagHiSlot0 for x in range(int(ship.hiSlots)) ],
             'medPower': [ x + const.flagMedSlot0 for x in range(int(ship.medSlots)) ],
             'loPower': [ x + const.flagLoSlot0 for x in range(int(ship.lowSlots)) ],
             'rigSlot': [ x + const.flagRigSlot0 for x in range(int(ship.rigSlots)) ]}
            for item in t[:]:
                rec, effects = item
                Progress('Module Test', 'Fitting %d/%d: %s' % (current, total, rec.name), current, total)
                current += 1
                try:
                    slotType = [ eff.effectName for eff in effects if eff.effectName.endswith('Power') or eff.effectName == 'rigSlot' ][0]
                    if slotsLeft[slotType]:
                        sm.RemoteSvc('slash').SlashCmd('/fit me %s' % rec.typeID)
                        t.remove(item)
                        flag = slotsLeft[slotType].pop(0)
                        module = []
                        while not module:
                            blue.pyos.synchro.SleepSim(500)
                            module = [ x for x in sm.GetService('godma').GetItem(eve.session.shipid).modules if x.flagID == flag ]

                        if not eve.session.stationid:
                            sm.RemoteSvc('slash').SlashCmd('/heal me capac=1')
                        if slotsLeft.values() == [[],
                         [],
                         [],
                         []]:
                            break
                except UserError as e:
                    errors.append((rec.typeID, str(e)))

            Progress('Module Test', 'Testing, hold on...', current, total)
            for itemID in sm.GetService('target').GetTargets():
                slimItem = uix.GetBallparkRecord(itemID)
                if slimItem.typeID == 12403:
                    break
            else:
                itemID = sm.RemoteSvc('slash').SlashCmd('/spawn 12403 victim')
                sm.GetService('target').ClearTargets()
                sm.GetService('target').LockTarget(itemID)
                slimItem = uix.GetBallparkRecord(itemID)

            if slimItem:
                sm.GetService('state').SetState(slimItem.itemID, state.selected, 1)
                sm.GetService('state').SetState(slimItem.itemID, state.activeTarget, 1)
            shipui = uicore.layer.shipui
            if not shipui:
                return
            for module in shipui.sr.modules.itervalues():
                module.SetRepeat(1000)
                attr = sm.GetService('godma').GetType(module.sr.moduleInfo.typeID)
                groups = []
                for x in range(1, 4):
                    if attr.AttributeExists('chargeGroup%d' % x):
                        groups.append(getattr(attr, 'chargeGroup%d' % x))

                if groups:
                    module.SetAutoReload(0)
                    for gid in groups:
                        for ammo in self.ammo[gid]:
                            if ammo.chargeSize == attr.chargeSize and cfg.invtypes.Get(ammo.typeID).marketGroupID:
                                print '%s <- %s' % (cfg.invtypes.Get(attr.typeID).name, cfg.invtypes.Get(ammo.typeID).name)
                                sm.RemoteSvc('slash').SlashCmd('/create %d' % ammo.typeID)
                                try:
                                    module.ChangeAmmo(module.id, 1, ammo.typeID)
                                    _WaitForIdle(module, 2000, reason='pre-activate')
                                    if attr.chargeSize == 4:
                                        blue.pyos.synchro.SleepSim(5000)
                                    else:
                                        blue.pyos.synchro.SleepSim(1000)
                                    _Click(module)
                                    _WaitForIdle(module, reason='post-activate')
                                except UserError as e:
                                    errors.append((module.sr.moduleInfo.typeID, str(e)))

                                sm.RemoteSvc('slash').SlashCmd('/unload me %d' % ammo.typeID)
                                break

                        break

                else:
                    try:
                        _Click(module)
                    except UserError as e:
                        errors.append((module.sr.moduleInfo.typeID, str(e)))

            busy = True
            timeout = 30000
            while busy and timeout > 0:
                blue.pyos.synchro.SleepSim(250)
                timeout -= 250
                for module in shipui.sr.modules.itervalues():
                    if not _Idle(module):
                        break
                else:
                    busy = False

        Progress('Module Test', 'Done!', 3, 4)
        blue.pyos.synchro.Sleep(2000)
        Progress('Module Test', 'Done!', 4, 4)
        for typeID, errormsg in errors:
            self.LogError('%d: %s' % (typeID, errormsg))
