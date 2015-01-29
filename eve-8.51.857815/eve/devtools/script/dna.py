#Embedded file name: eve/devtools/script\dna.py
import uiprimitives
import uicontrols
import blue
import triui
import uix
import uiutil
from eve.client.script.ui.control import entries as listentry
import uthread
import carbonui.const as uiconst
import util
from service import ROLE_WORLDMOD, ROLE_GML, ROLE_SPAWN
USE_SPAWN = True

def GetTypeName(typeID):
    return cfg.invtypes.Get(typeID).name


def GetCategory(typeID):
    return cfg.invtypes.Get(typeID).Group().Category()


Message = lambda title, body, icon = triui.INFO: sm.GetService('gameui').MessageBox(body, title, buttons=uiconst.OK, icon=icon)
Progress = lambda title, text, current, total: (title,
 text,
 current,
 total)
Cycle = lambda title, text: sm.GetService('loading').Cycle(title, text)
StopCycle = lambda : sm.GetService('loading').StopCycle()
Slash = lambda command: sm.RemoteSvc('slash').SlashCmd(command)
COPYCAT = 'copycat'
groupByFlag = {}
SLOTGROUPS = (const.flagHiSlot0,
 const.flagMedSlot0,
 const.flagLoSlot0,
 const.flagRigSlot0,
 const.flagSubSystemSlot0)

def InitStuff():
    global SLOTGROUPS
    if groupByFlag:
        return
    SLOTGROUPS = (const.flagHiSlot0,
     const.flagMedSlot0,
     const.flagLoSlot0,
     const.flagRigSlot0,
     const.flagSubSystemSlot0)
    grp = 0
    for slot in SLOTGROUPS:
        for flag in xrange(slot, slot + 8):
            groupByFlag[flag] = grp

        grp += 1


def GetSlotGroup(typeID):
    try:
        for effect in cfg.dgmtypeeffects.get(typeID, []):
            if effect.effectID == const.effectHiPower:
                return 0
            if effect.effectID == const.effectMedPower:
                return 1
            if effect.effectID == const.effectLoPower:
                return 2
            if effect.effectID == const.effectRigSlot:
                return 3
            if effect.effectID == const.effectSubSystem:
                return 4

    except KeyError:
        return None


def Load(typeID, qty = 1, where = 'me'):
    try:
        return sm.RemoteSvc('slash').SlashCmd('/load %s %s %s' % (where, typeID, qty))[0]
    except:
        return None


def WaitAndSetLabel(itemID, name, timeout = 10):
    timeout *= 4
    bp = sm.GetService('michelle').GetBallpark()
    while timeout:
        if bp.GetBall(itemID):
            sm.GetService('invCache').GetInventoryMgr().SetLabel(itemID, name)
            break
        timeout -= 1
        blue.pyos.synchro.SleepSim(250)


def CreateShip_WORLDMOD(typeID, name = None, subsystems = None):
    if eve.session.stationid:
        itemID = sm.RemoteSvc('slash').SlashCmd('/createitem %d 1 %d' % (typeID, eve.session.stationid))
        subSystemIDs = []
        if subsystems is not None:
            for subSystemTypeID in subsystems:
                subSystemID = sm.RemoteSvc('slash').SlashCmd('/createitem %d' % subSystemTypeID)
                subSystemIDs.append(subSystemID)

        sm.GetService('gameui').GetShipAccess().AssembleShip(itemID, name, subSystems=subSystemIDs)
    else:
        if USE_SPAWN:
            return CreateShip_SPAWN(typeID, name)
        itemID = sm.RemoteSvc('slash').SlashCmd('/createitem %d' % typeID)
        sm.GetService('gameui').GetShipAccess().Jettison([itemID])
        if name:
            WaitAndSetLabel(itemID, name)
    return itemID


def CreateShip_SPAWN(typeID, name = None):
    if eve.session.stationid:
        return CreateShip_GML(typeID, name)
    itemID = sm.RemoteSvc('slash').SlashCmd('/spawn %d' % typeID)
    if name:
        WaitAndSetLabel(itemID, name)
    return itemID


def CreateShip_GML(typeID, name = None):
    shipID = None
    itemID = Load(typeID)
    invCache = sm.GetService('invCache')
    if not itemID:
        if session.stationid:
            hangar = invCache.GetInventory(const.containerHangar)
            cargo = invCache.GetInventoryFromId(util.GetActiveShip()).GetCapacity(const.flagCargo)
            if cargo.capacity - cargo.used >= 100:
                shipID = Load(11019)
                if shipID:
                    hangar.Add(shipID, util.GetActiveShip(), qty=1)
                    sm.GetService('gameui').GetShipAccess().AssembleShip(shipID, 'Copycat Temporary')
                    itemID = Load(typeID, where=shipID)
                    if not itemID:
                        Message('what the?!', 'Something is hosed alright.')
                        return
    if itemID:
        if eve.session.stationid:
            invCache.GetInventory(const.containerHangar).Add(itemID, util.GetActiveShip(), qty=1)
            sm.GetService('gameui').GetShipAccess().AssembleShip(itemID, name)
        else:
            sm.GetService('gameui').GetShipAccess().Jettison([itemID])
            if name:
                WaitAndSetLabel(itemID, name)
    if shipID and eve.session.stationid:
        invCache.GetInventoryMgr().TrashItems([shipID], session.stationid)
    if not itemID:
        Message('Planck field overload', "Sorry, you can't squeeze a <color=0xffffff00>%s<color=0xffffffff> into your current ship's cargohold.<br><br>Please make sure you have enough free cargo capacity to load this ship before trying again.<br>" % cfg.invtypes.Get(typeID).name)
    return itemID


def CreateShip(typeID, name = None, subsystems = None):
    if eve.session.role & ROLE_WORLDMOD:
        return CreateShip_WORLDMOD(typeID, name, subsystems)
    elif eve.session.role & ROLE_SPAWN and USE_SPAWN:
        return CreateShip_SPAWN(typeID, name)
    elif eve.session.role & ROLE_GML:
        return CreateShip_GML(typeID, name)
    else:
        return None


class Ship():

    def __init__(self, shipID = None, dnaKey = None, name = None):
        self.source = None
        self.dna = []
        self.typeID = 0
        self.moduleByFlag = {}
        self.name = None
        self.valid = False
        self.errorMessage = 'Template not initialized'
        self.errorTypeID = 0
        InitStuff()
        if shipID:
            self.ImportFromShip(shipID=shipID)
            return
        if dnaKey:
            self.ImportFromDNA(dnaKey, name)
            return

    def itermodules(self, smart = False, banks = None):
        if banks is None:
            banks = SLOTGROUPS
        get = self.moduleByFlag.get
        if smart:
            for slot in banks:
                fit = []
                go = False
                for flag in xrange(slot + 7, slot - 1, -1):
                    typeID = get(flag, 0)
                    if typeID:
                        go = True
                    if go:
                        fit.insert(0, (flag, typeID))

                for flag, typeID in fit:
                    yield (flag, typeID)

        else:
            for slot in banks:
                for flag in xrange(slot, slot + 8):
                    yield (flag, get(flag, 0))

    def ImportFromShip(self, shipID = None, ownerID = None, deferred = False):
        if deferred:
            self.deferred = (shipID, ownerID)
            return self
        self.__init__()
        if shipID is None:
            shipID = util.GetActiveShip()
        if ownerID is None:
            ownerID = eve.session.charid
        loc = cfg.evelocations.GetIfExists(shipID)
        if loc:
            self.name = loc.name
        else:
            self.name = None
        if ownerID != eve.session.charid:
            dna = sm.RemoteSvc('slash').SlashCmd('/getshipsetup %d' % shipID)
            return self.ImportFromDNA(dna)
        if shipID == util.GetActiveShip():
            ship = sm.GetService('clientDogmaIM').GetDogmaLocation().GetDogmaItem(shipID)
            if ship is None:
                self.errorMessage = 'Could not get shipID: %s' % shipID
                return self
            self.typeID = ship.typeID
            for module in ship.GetFittedItems().itervalues():
                if cfg.IsFittableCategory(module.categoryID):
                    self.moduleByFlag[module.flagID] = module.typeID

        else:
            try:
                shipinv = sm.GetService('invCache').GetInventoryFromId(shipID)
                self.typeID = shipinv.GetTypeID()
                if not self.name:
                    self.name = cfg.invtypes.Get(self.typeID).name
                mods = shipinv.ListHardwareModules()
            except:
                self.errorMessage = 'Could not get inv of shipID: %s' % shipID
                return self

            for rec in mods:
                if cfg.IsFittableCategory(cfg.invtypes.Get(rec.typeID).categoryID):
                    self.moduleByFlag[rec.flagID] = rec.typeID

        self.valid = True
        self.Update()
        return self

    def ImportFromDNA(self, dna, name = None):
        self.__init__()
        if dna[:4] != 'DNA:':
            self.errorMessage = 'Not a DNA key: %s' % (dna,)
            return self
        if name:
            self.name = name
        self.source = dna
        self.dna = dna.split(':')[1:]
        expectedCategoryIDs = [const.categoryShip]
        flags = list(SLOTGROUPS)
        try:
            for frag in self.dna:
                try:
                    parts = map(int, frag.split('*', 1))
                except:
                    raise RuntimeError(-1, "Invalid DNA fragment: '%s'" % frag)

                if len(parts) == 2:
                    typeID, multi = parts
                else:
                    typeID, = parts
                    multi = 1
                self.errorTypeID = typeID
                if multi < 1 or multi > 8:
                    raise RuntimeError(typeID, 'Invalid module count: %s' % multi)
                if typeID > 3:
                    inv = cfg.invtypes.GetIfExists(typeID)
                    if not inv:
                        raise RuntimeError(typeID, 'Type not found')
                    categoryID = inv.Group().Category().id
                while multi > 0:
                    if typeID <= 3:
                        grp = typeID
                        self.moduleByFlag[flags[grp]] = 0
                        flags[grp] += 1
                        multi -= 1
                        continue
                    if categoryID not in expectedCategoryIDs:
                        raise RuntimeError(typeID, 'Expected %s type, got %s type' % (cfg.invcategories.Get(expectedCategoryIDs[0]).name, cfg.invcategories.Get(categoryID).name))
                    if categoryID == const.categoryShip:
                        self.typeID = typeID
                        expectedCategoryIDs = [const.categoryModule, const.categorySubSystem]
                    elif cfg.IsFittableCategory(categoryID):
                        grp = GetSlotGroup(typeID)
                        if grp is not None:
                            self.moduleByFlag[flags[grp]] = typeID
                            flags[grp] += 1
                        else:
                            raise RuntimeError(typeID, 'Type is not a module or rig')
                    else:
                        raise RuntimeError(typeID, 'Type is not a ship or module')
                    multi -= 1

            for startFlag, endFlag in zip(SLOTGROUPS, flags):
                if endFlag > startFlag + 8:
                    raise RuntimeError(-1, 'Malformed template')

            self.valid = True
            self.Update()
        except RuntimeError as e:
            self.errorTypeID, self.errorMessage = e

        return self

    def Update(self):
        real = 0
        fake = 0
        for flag, typeID in self.itermodules(smart=True):
            if typeID:
                real += 1
            else:
                fake += 1

        self.realmodulecount = real
        self.fakemodulecount = fake

    def AssembleMany(self, amount = None):
        self.NoPodCheck(wantNewShip=True)
        if amount is None:
            result = uix.QtyPopup(maxvalue=50, minvalue=1, caption='Mass Manufacture', label='', hint='Specify amount of ships to assemble (Max. 50).<br>Note: this function cannot be aborted once running.')
            if result:
                amount = result['qty']
            else:
                amount = 0
        for x in xrange(amount):
            self.Assemble()

    def Assemble(self, clone = 0):
        if not self.Valid(report=True):
            return None
        self.NoPodCheck(wantNewShip=True)
        tname = GetTypeName(self.typeID)
        title = ['Create %s', 'Clone %s'][clone] % tname
        sm.GetService('loading').ProgressWnd(title, 'Spawning: %s ...' % tname, 0, 1)
        subsystems = []
        for i in xrange(const.flagSubSystemSlot0, const.flagSubSystemSlot0 + const.visibleSubSystems):
            if i in self.moduleByFlag:
                subsystems.append(self.moduleByFlag[i])

        if session.solarsystemid and len(subsystems) > 0:
            raise UserError('CustomInfo', {'info': "You can't assemble ship with subsystems in space. Please try again in station"})
            return None
        shipID = CreateShip(self.typeID, self.name, subsystems)
        if shipID:
            self.Fit(shipID, fromAssemble=True)
            sm.GetService('loading').ProgressWnd(title, 'Success', 1, 1)
            return shipID
        sm.GetService('loading').ProgressWnd(title, 'Failed', 1, 1)

    def Fit(self, shipID = None, fromAssemble = False):
        if not self.Valid(report=True):
            return None
        self.NoPodCheck(wantNewShip=fromAssemble)
        if not shipID:
            shipID = util.GetActiveShip()
        if not fromAssemble:
            try:
                shipTypeID = sm.GetService('clientDogmaIM').GetDogmaLocation().GetDogmaItem(shipID).typeID
            except:
                shipTypeID = sm.GetService('invCache').GetInventoryFromId(shipID).GetTypeID()

            if shipTypeID != self.typeID:
                Message('Unable to refit', 'Sorry, this setup is designed for a %s. You are currently piloting a %s.' % (GetTypeName(self.typeID), GetTypeName(shipTypeID)))
                raise UserError('IgnoreToTop')
        if eve.session.role & ROLE_GML:
            return self.FitUsingSlash(shipID)
        if eve.session.stationid:
            self.SkillCheck()
            return self.FitUsingHangar(shipID)
        self.Oops('Oops', 'Fitting operations cannot be done in space. Please dock at a station and try again.')

    def FitUsingHangar(self, shipID):
        if shipID != util.GetActiveShip():
            self.Oops('Oops', 'You cannot fit ships other than your active one.')
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        ship = dogmaLocation.GetDogmaItem(shipID)
        if ship is None:
            self.Oops('Huh?', 'Where is your ship?')
        title = 'Fitting %s' % GetTypeName(self.typeID)
        setup = self.GetModuleInfo()
        Cycle(title, 'Locating required modules...')
        source = {}
        for typeID in setup['modulelist']:
            source[typeID] = []

        fit = {}
        for flag, typeID in self.moduleByFlag.iteritems():
            if typeID:
                fit[flag] = typeID

        for item in ship.GetFittedItems().itervalues():
            if item.typeID == self.moduleByFlag[item.flagID]:
                if fit.has_key(item.flagID):
                    del fit[item.flagID]
            else:
                source[typeID].append(item)
            if setup.has_key(item.typeID):
                setup[item.typeID] -= 1

        invCache = sm.GetService('invCache')
        for item in invCache.GetInventory(const.containerHangar).List():
            if cfg.IsFittableCategory(item.categoryID):
                if setup.has_key(item.typeID):
                    if item.singleton:
                        source[item.typeID].insert(0, item)
                    else:
                        source[item.typeID].append(item)
                    setup[item.typeID] -= item.stacksize

        missing = []
        for typeID in setup['modulelist']:
            if setup[typeID] > 0:
                missing.append('  %s %s' % (setup[typeID], GetTypeName(typeID)))

        if missing:
            StopCycle()
            msg = 'Sorry, you cannot fit your ship with this setup; The following modules are not in your possession:<br><br>'
            msg += '<br>'.join(missing)
            self.Oops('Unable to fit ship', msg)
        Cycle(title, 'Unfitting modules...')
        charges = {}
        for item in ship.subLocations.itervalues():
            charges[item.flagID] = item

        unfit = []
        for item in ship.GetFittedItems().itervalues():
            if item.categoryID == const.categoryCharge:
                charges[item.flagID] = item
            elif self.moduleByFlag[item.flagID] != item.typeID:
                unfit.append(item)

        ids = []
        for item in unfit:
            charge = charges.get(item.flagID, None)
            if charge:
                ids.append(charge.itemID)
            ids.append(item.itemID)

        invCache.GetInventory(const.containerHangar).MultiAdd(ids, shipID, flag=const.flagHangar)
        del charges
        del unfit
        del ids
        del item
        fitByTypeID = {}
        for slot in (const.flagLoSlot0, const.flagMedSlot0, const.flagHiSlot0):
            for flag in xrange(slot, slot + 8):
                if fit.has_key(flag):
                    typeID = fit[flag]
                    if fitByTypeID.has_key(typeID):
                        fitByTypeID[typeID].append(flag)
                    else:
                        fitByTypeID[typeID] = [flag]

        total = len(fit)
        state = [1, False]

        def _fit(typeID, flags):
            for flag in flags:
                sm.GetService('loading').ProgressWnd(title, 'Fitting modules...', state[0], total)
                try:
                    while source[typeID]:
                        item = source[typeID][0]
                        try:
                            if item.stacksize == 1:
                                source[typeID].pop(0)
                            invCache.GetInventoryFromId(shipID).Add(item.itemID, item.locationID, qty=1, flag=flag)
                            state[0] += 1
                            break
                        except:
                            pass

                except:
                    state[1] = True
                    break

        parallelCalls = []
        for typeID, flags in fitByTypeID.iteritems():
            parallelCalls.append((_fit, (typeID, flags)))

        StopCycle()
        try:
            uthread.parallel(parallelCalls)
        except:
            pass

        if state[1]:
            StopCycle()
            self.Oops('There was a problem...', 'Your hangar inventory changed while fitting the ship, one or more required modules are locked or no longer within your reach.<br>The fitting operation has been aborted.')
        sm.GetService('loading').ProgressWnd(title, 'Done', 1, 1)

    def FitUsingSlash(self, shipID):
        title = 'Fitting %s' % GetTypeName(self.typeID)
        state = [0, 0]

        def _fitgroup(slot):
            w = sm.RemoteSvc('slash')
            for flag, typeID in self.itermodules(banks=(slot,), smart=True):
                if typeID:
                    state[0] += 1
                    modname = GetTypeName(typeID)
                else:
                    continue
                state[1] += 1
                sm.GetService('loading').ProgressWnd(title, 'Fitting module %s/%s: %s' % (state[0], self.realmodulecount, modname), state[1] * 1000, (self.realmodulecount + self.fakemodulecount) * 1000 + 1)
                w.SlashCmd('/fit %s %s flag=%d' % (shipID, typeID, flag))

        if shipID == util.GetActiveShip():
            sm.RemoteSvc('slash').SlashCmd('/unload me all')
        parallelCalls = []
        for slot in SLOTGROUPS:
            parallelCalls.append((_fitgroup, (slot,)))

        uthread.parallel(parallelCalls)
        sm.GetService('loading').ProgressWnd(title, 'Done', 1, 1)

    def NoPodCheck(self, wantNewShip = False):
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        inPod = not (util.GetActiveShip() is not None and dogmaLocation.GetDogmaItem(util.GetActiveShip()).groupID != 29)
        if not inPod:
            return
        if inPod and wantNewShip and eve.session.role & (ROLE_WORLDMOD | ROLE_SPAWN):
            return
        self.Oops('Allergic to eggs', 'This feature cannot be used when you are in a pod.<br>Get yourself in a ship and try again!')

    def SkillCheck(self, setup = None):
        if not setup:
            setup = self.GetModuleInfo()
        Cycle('   Preparing...', 'Checking skill requirements')
        skills = {}
        groups = sm.GetService('skills').GetSkillGroups()
        for _each in groups:
            for skill in _each[1]:
                skills[skill.typeID] = skill.skillLevel

        required = {}
        for eachTypeID in setup['modulelist']:
            c = 0
            for typeID, requiredLevel in sm.RemoteSvc('dogmaIM').GetRequiredSkillLevels(eachTypeID).iteritems():
                c += 1
                if not (skills.has_key(typeID) and skills[typeID] >= requiredLevel):
                    required[typeID] = max(required.get(typeID, 0), requiredLevel)

        StopCycle()
        if required:
            rs = []
            for typeID, level in required.iteritems():
                rs.append('  %s level %s' % (GetTypeName(typeID), level))

            msg = 'To fit this setup to your ship you require the following skills:<br><br>'
            msg += '<br>'.join(rs)
            self.Oops('Insufficient Skill', msg)

    def GetModuleInfo(self):
        setup = {}
        setup['modulelist'] = []
        for flag, typeID in self.itermodules():
            if typeID:
                if setup.has_key(typeID):
                    setup[typeID] += 1
                else:
                    setup['modulelist'].append(typeID)
                    setup[typeID] = 1

        return setup

    def ExportAsDNA(self):
        if not self.Valid():
            return self.ErrorReport()
        dna = 'DNA:%s' % self.typeID
        multi = 1
        lastID = None
        grp = 0
        get = self.moduleByFlag.get
        for flag, typeID in self.itermodules(smart=True):
            if not typeID:
                typeID = groupByFlag[flag]
            if typeID == lastID:
                multi += 1
            else:
                if multi > 1:
                    dna += '*%s' % multi
                    multi = 1
                dna += ':%s' % typeID
            lastID = typeID

        if multi > 1:
            dna += '*%s' % multi
        return dna

    def ExportAsTriText(self, modulesOnly = False, maxLen = 0):
        if not self.Valid():
            return self.ErrorReport()
        text = ''
        if modulesOnly:
            indent = ''
        else:
            indent = '  '
            if self.name:
                text += '<color=0xffffff00>Name:<color=0xffffffff> %s<br>' % self.name
            text += '<color=0xffffff00>Ship:<color=0xffffffff> %s<br>' % GetTypeName(self.typeID)
            text += '<color=0xffffff00>Modules: <color=0xffc0c0c0><br>'
        info = self.GetModuleInfo()
        if not info['modulelist']:
            text += indent + 'None<br>'
        if maxLen:
            for typeID in info['modulelist']:
                name = GetTypeName(typeID)
                if len(name) > maxLen:
                    name = name[:maxLen] + '...'
                text += indent + '%s %s<br>' % (info[typeID], name)

        else:
            for typeID in info['modulelist']:
                text += indent + '%s %s<br>' % (info[typeID], GetTypeName(typeID))

        if not modulesOnly:
            text += '<br><color=0xffffff00>Key:<color=0xffc0c0c0><br>%s' % self.ExportAsDNA()
        return text

    def ExportAsText(self, modulesOnly = False, maxLen = 0):
        r = self.ExportAsTriText(modulesOnly, maxLen).replace('<br>', '\r\n') + '\r\n'
        while 1:
            i = r.find('<color=0x')
            if i == -1:
                break
            r = r[:i] + r[i + 18:]

        return r

    def ExportAsHTML(self):
        if not self.Valid():
            msg = '<html><body><h1><font color="red">?TEMPLATE ERROR</font></h1><br>'
            msg += self.ErrorReport()
            msg += '</body></html>'
            return msg
        html = '<html><title>Copycat</title><body link="#4080FF">'
        html += '<a href="showinfo:%s"><img style="margin: 0px 0px 4px 0px;" src="typeicon:%s" align="right" width="64" height="64"></a>' % (self.typeID, self.typeID)
        html += '<font color="yellow">Ship:</font>'
        html += '<font size="+2"> %s</font>' % GetTypeName(self.typeID)
        if self.name:
            html += '<br><font color="yellow">Name:</font> %s' % self.name
        else:
            html += ''
        info = self.GetModuleInfo()
        html += '<br><br><font color="yellow">Modules:</font><br>'
        if info['modulelist']:
            for typeID in info['modulelist']:
                html += '&nbsp;&nbsp;&nbsp;%s <a href="showinfo:%s">%s</a><br>' % (info[typeID], typeID, GetTypeName(typeID))

            html += '<br><font color="yellow">Fitting overview:</font><br>'
            for grp in xrange(3):
                if not self.modules[grp]:
                    continue
                if grp == 1:
                    html += '<img src="icon:09_14" width="16" height="32">'
                for typeID in self.modules[grp]:
                    if typeID != 0:
                        html += '<a href="showinfo:%s"><img alt="%s" src="typeicon:%s" width="32" height="32"></a>' % (typeID, GetTypeName(typeID), typeID)
                    else:
                        html += '<img src="icon:09_14" width="32" height="32">'

                html += '<br>'

        else:
            html += 'No modules fitted<br><br>'
        html += '</body></html>'
        return html

    def ExportAsIGBLink(self, label = None):
        if label is None:
            label = self.name
        return '<a href="localsvc:service=copycat&method=igb&action=open&key=%s&name=%s">%s</a>' % (self.ExportAsDNA(), self.name, label)

    def ExportToClipboard(self, mode = 1):
        if mode == 0:
            blue.pyos.SetClipboardData(self.ExportAsText())
        elif mode == 1:
            blue.pyos.SetClipboardData(self.ExportAsDNA())
        elif mode == 2:
            blue.pyos.SetClipboardData(self.ExportAsIGBLink())

    def Valid(self, report = False):
        if self.valid:
            return True
        if hasattr(self, 'deferred'):
            self.ImportFromShip(shipID=self.deferred[0], ownerID=self.deferred[1])
        if self.valid:
            return True
        if report:
            Message('Invalid Template', self.ErrorReport(), icon=triui.ERROR)
        return False

    def Oops(self, title, message):
        Message(title, message)
        raise UserError('IgnoreToTop')

    def ErrorReport(self):
        msg = 'The template does not contain valid data.<br><br>Maybe it is because of this error:<br>  %s: %s' % (self.errorTypeID, self.errorMessage)
        if self.source:
            msg += '<br><br>Key: %s' % self.source
        return msg

    def ShowInfo(self, buttons = False):
        Popup(self, buttons=buttons)

    def ShowCargo(self, id = None, *args):
        cargoContents = []
        try:
            if id:
                itemID = id
            else:
                itemID = self.deferred[0]
        except:
            return

        for cargo in sm.GetService('invCache').GetInventoryFromId(itemID).ListCargo():
            if cargo.categoryID != const.categoryOwner:
                rec = cfg.invtypes.Get(cargo.typeID)
                cargoContents.append(('%s<t>%s' % (rec.name, cargo.stacksize), cargo))

        uix.ListWnd(cargo, listtype='generic', caption='Cargo loaded with %d items' % len(cargoContents), isModal=0, minChoices=0, scrollHeaders=[u'Type', u'Quantity'])

    def Store(self):
        sm.GetService(COPYCAT).DoStore(self.ExportAsDNA(), self.name)

    def RefitMenu(self):
        m = []

        def _Refit(dnaKey):
            self.__class__().ImportFromDNA(dnaKey).Fit(util.GetActiveShip())

        for name, dnaKey in sm.GetService('copycat').GetSetupsByTypeID(self.typeID):
            m.append((name, _Refit, (dnaKey,)))

        if m:
            m.insert(0, ('My %s setups' % cfg.invtypes.Get(self.typeID).name, None))
        return m

    def GetMenuInline(self, disabled = False, store = True, assemble = True, info = True, fit = True, refit = False, spiffy = False):

        def d(func, condition = None):
            if disabled:
                return
            if condition is None or condition:
                return func

        m = []
        if info:
            m += [(('Show Info', 'ui_38_16_208'), self.ShowInfo), None]
        if store:
            m += [(('Store Setup', '41_1'), self.Store)]
        if refit:
            m += [(('Switch Setup', 'res:/ui/Texture/WindowIcons/fitting.png'), self.RefitMenu())]
        if assemble:
            if eve.session.role & (ROLE_GML | ROLE_WORLDMOD):
                m += [(('Assemble Ship', '41_2'), d(self.Assemble, eve.session.role & (ROLE_GML | ROLE_WORLDMOD))), (('Mass Manufacture', '27_1'), d(self.AssembleMany, eve.session.role & (ROLE_GML | ROLE_WORLDMOD)))]
            if fit:
                m += [(('Fit to active Ship', 'ui_8_64_11'), d(self.Fit))]
        if store or assemble or fit:
            m.append(None)
        if not disabled:
            m += [(('Copy Manifest', 'ui_10_64_16'), d(self.ExportToClipboard), (0,)), (('Copy DNA Key', 'res:/ui/Texture/WindowIcons/attributes.png'), d(self.ExportToClipboard), (1,)), (('Copy IGB Link', 'res:/ui/Texture/WindowIcons/browser.png'), d(self.ExportToClipboard), (2,))]
        if spiffy is True:
            return m
        else:
            m2 = []
            for x in m:
                if x:
                    m2.append((x[0][0],) + x[1:])
                else:
                    m2.append(None)

            return m2


TOOLSIZE = 34
ICONSIZE = 72

class InfoPanel(uiprimitives.Container):
    __guid__ = 'xtriui.DNAInfoPanel'

    def Setup(self, template = None, readonly = False):
        self.typeID = None
        self.readonly = readonly
        self.boven = uiprimitives.Container(name='ccip_top', parent=self, height=ICONSIZE, align=uiconst.TOTOP)
        self.toolbar = uiprimitives.Container(name='ccip_bar', parent=self.boven, left=ICONSIZE + 2, top=ICONSIZE - TOOLSIZE, height=TOOLSIZE, align=uiconst.TOPLEFT, width=240)
        uiprimitives.Container(name='ccip_push', parent=self, height=3, align=uiconst.TOTOP)
        cont = uiprimitives.Container(name='mainicon', parent=self.boven, width=ICONSIZE, align=uiconst.TOLEFT)
        self.infoframe = uicontrols.Frame(parent=cont)
        self.infoicon = infoicon = uicontrols.InfoIcon(size=16, left=1, top=1, parent=cont, idx=0, align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED)
        infoicon.OnClick = lambda *x: self.ShowInfo()
        self.icon = uicontrols.Icon(parent=cont)
        self.icon.OnClick = self.ShowInfo
        self.icon.LoadTexture('res:/UI/Texture/notavailable.dds')
        self.icon.width = self.icon.height = ICONSIZE
        uiprimitives.Container(name='ccip_push', parent=self.boven, width=6, align=uiconst.TOLEFT)
        cont = uiprimitives.Container(name='ccip_icon', parent=self.boven, align=uiconst.TOTOP, height=24)
        self.capt = uicontrols.CaptionLabel(text='', parent=cont)
        cont = uiprimitives.Container(name='ccip_textcont', parent=self.boven, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.text = uicontrols.Label(text='', parent=cont, align=uiconst.TOTOP, height=self.boven.height, state=uiconst.UI_NORMAL)
        self.scroll = uicontrols.Scroll(name='ccip_top', parent=self)
        if template:
            self.Load(template)
        else:
            self.typeID = None
            self.capt.text = 'Copycat'
            self.text.text = 'Select a ship setup from the list to display details in this panel'
            self.scroll.Load(contentList=[], headers=['qty', 'name'])

    def ShowInfo(self, *args):
        if self.typeID:
            sm.GetService('info').ShowInfo(typeID=self.typeID)

    def Clicketyclick(self, btn):
        f = btn.menuitem[1]
        if f:
            if len(btn.menuitem) >= 3:
                f(*btn.menuitem[2])
            else:
                f()

    def Load(self, template):
        entries = []
        headers = ['qty', 'name']
        state = uiconst.UI_NORMAL
        if template:
            if template.Valid():
                self.typeID = template.typeID
                info = template.GetModuleInfo()
                capt = GetTypeName(template.typeID)
                name = template.name
                for typeID in info['modulelist']:
                    entries.append(listentry.Get('Generic', {'label': '%s<t>%s' % (info[typeID], GetTypeName(typeID)),
                     'typeID': typeID,
                     'showinfo': True}))

            else:
                state = uiconst.UI_HIDDEN
                capt = 'TEMPLATE ERROR'
                name = 'This template does not contain a valid ship setup'
                entries.append(listentry.Get('Generic', {'label': '%s<t>%s' % (template.errorTypeID, template.errorMessage)}))
                headers = ['typeID', 'error']
        else:
            state = uiconst.UI_HIDDEN
            capt = name = ''
        uix.Flush(self.toolbar)
        if state == uiconst.UI_NORMAL:
            self.icon.LoadIconByTypeID(template.typeID)
            m = template.GetMenuInline(info=False, store=not self.readonly, spiffy=True)
            x = 0
            for item in m:
                if item:
                    hint, icon = item[0]
                    btn = uix.GetBigButton(TOOLSIZE, self.toolbar, left=x, hint=hint)
                    btn.sr.icon.LoadIcon(icon)
                    btn.sr.icon.left += 1
                    btn.sr.icon.top += 2
                    btn.menuitem = item
                    btn.OnClick = (self.Clicketyclick, btn)
                    x += TOOLSIZE

        else:
            self.typeID = None
            self.icon.LoadTexture('res:/UI/Texture/notavailable.dds')
        self.capt.text = capt
        self.text.text = name
        self.infoframe.state = self.infoicon.state = self.toolbar.state = state
        self.scroll.Load(contentList=entries, headers=headers)


class Popup():
    __wndname__ = 'DNA Popup'

    def __init__(self, key_or_template, name = None, buttons = True, store = True):
        import dna
        if isinstance(key_or_template, dna.Ship):
            self.t = key_or_template
        else:
            self.t = Ship().ImportFromDNA(key_or_template, name)
        _wndname = '%s_%s' % (Popup.__wndname__, blue.os.GetWallclockTime())
        wnd = uicontrols.Window.Open(windowID=_wndname)
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Ship Setup Information')
        wnd.sr.main = uiutil.GetChild(wnd, 'main')
        wnd.SetMinSize((320, 256))
        main = uiprimitives.Container(name='main', parent=wnd.sr.main, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), align=uiconst.TOALL)
        info = InfoPanel(name='info', parent=main, pos=(0, 0, 0, 0))
        info.Setup(self.t)
        if buttons:
            buttons = [['Close',
              self.Close,
              None,
              81]]
            wnd.sr.main.children.insert(0, uicontrols.ButtonGroup(btns=buttons))

    def Spawn(self, *args):
        self.wnd.Close()
        self.t.Assemble()

    def Store(self, *args):
        if sm.GetService(COPYCAT).DoStore(self.t.ExportAsDNA(), self.t.name):
            self.wnd.Close()

    def Close(self, *args):
        self.wnd.Close()
        del self.wnd


exports = {'dna.Ship': Ship,
 'dna.InfoPanel': InfoPanel,
 'dna.Popup': Popup}
