#Embedded file name: eve/client/script/ui/inflight/shipModuleButton\shipmodulebutton.py
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from inventorycommon.util import GetItemVolume
import uicontrols
import math
import uiprimitives
import uthread
import uix
import mathUtil
import base
import util
import blue
import service
import re
import state
import uiutil
import carbonui.const as uiconst
import log
import localization
import godma
import trinity
import crimewatchConst
from eve.client.script.ui.inflight.shipModuleButton.moduleButtonHint import ModuleButtonHint, MAXMODULEHINTWIDTH
from eve.client.script.ui.inflight.shipModuleButton.moduleButtonTooltip import TooltipModuleWrapper
from eve.client.script.ui.inflight.shipModuleButton.ramps import DamageStateCont, ShipModuleButtonRamps, ShipModuleReactivationTimer
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_SETTINGS_MODULE, TOOLTIP_DELAY_MODULE
from eve.common.script.sys.rowset import IndexedRows
cgre = re.compile('chargeGroup\\d{1,2}')
GLOWCOLOR = (0.24, 0.67, 0.16, 0.75)
BUSYCOLOR = (1.0, 0.13, 0.0, 0.73)
OVERLOADBTN_INDEX = 1
MODULEHINTDELAY = 800

class ModuleButton(uiprimitives.Container):
    __guid__ = 'xtriui.ModuleButton'
    __notifyevents__ = ['OnStateChange',
     'OnItemChange',
     'OnModuleRepaired',
     'OnAmmoInBankChanged',
     'OnFailLockTarget',
     'OnChargeBeingLoadedToModule']
    __update_on_reload__ = 1
    __cgattrs__ = []
    __loadingcharges__ = []
    __chargesizecache__ = {}
    default_name = 'ModuleButton'
    default_pickRadius = 20
    isDragObject = True
    def_effect = None
    charge = None
    target = None
    waitingForActiveTarget = 0
    changingAmmo = 0
    reloadingAmmo = False
    online = False
    stateManager = None
    dogmaLocation = None
    autorepeat = 0
    autoreload = 0
    quantity = None
    invReady = 1
    invCookie = None
    isInvItem = 1
    isBeingRepaired = 0
    blinking = 0
    blinkingDamage = 0
    effect_activating = 0
    typeName = ''
    ramp_active = False
    isMaster = 0
    animation = None
    isPendingUnlockForDeactivate = False
    moduleHintTimer = None
    shouldUpdate = False
    moduleButtonHint = None
    tooltipPanelClassInfo = TooltipModuleWrapper()

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.icon = uicontrols.Icon(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        sm.RegisterNotify(self)

    def Close(self, *args, **kwds):
        if getattr(self, 'invCookie', None) is not None:
            sm.GetService('inv').Unregister(self.invCookie)
        uiprimitives.Container.Close(self, *args, **kwds)

    def Setup(self, moduleinfo, grey = None):
        self.crimewatchSvc = sm.GetService('crimewatchSvc')
        if not len(self.__cgattrs__):
            self.__cgattrs__.extend([ a.attributeID for a in cfg.dgmattribs if cgre.match(a.attributeName) is not None ])
        invType = cfg.invtypes.Get(moduleinfo.typeID)
        group = cfg.invtypes.Get(moduleinfo.typeID).Group()
        self.id = moduleinfo.itemID
        self.sr.moduleInfo = moduleinfo
        self.locationFlag = moduleinfo.flagID
        self.stateManager = sm.StartService('godma').GetStateManager()
        self.dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        self.grey = grey
        self.isInActiveState = True
        self.isDeactivating = False
        icon = uiutil.GetChild(self.parent, 'overloadBtn')
        icon.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')
        icon.OnClick = self.ToggleOverload
        icon.OnMouseDown = (self.OLButtonDown, icon)
        icon.OnMouseUp = (self.OLButtonUp, icon)
        icon.OnMouseExit = (self.OLMouseExit, icon)
        icon.SetOrder(OVERLOADBTN_INDEX)
        self.sr.overloadButton = icon
        if cfg.IsChargeCompatible(moduleinfo):
            self.invCookie = sm.GetService('inv').Register(self)
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        if group.categoryID == const.categoryCharge:
            self.SetCharge(moduleinfo)
        else:
            self.SetCharge(None)
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        for key in moduleinfo.effects.iterkeys():
            effect = moduleinfo.effects[key]
            if self.IsEffectActivatible(effect):
                self.def_effect = effect
                if effect.isActive:
                    if effect.isDeactivating:
                        self.SetDeactivating()
                    else:
                        self.SetActive()
            if effect.effectName == 'online':
                if effect.isActive:
                    self.ShowOnline()
                else:
                    self.ShowOffline()

        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        repairTimeStamps = self.stateManager.GetRepairTimeStamp(self.id)
        if repairTimeStamps:
            self.isBeingRepaired = True
            self.SetRepairing(repairTimeStamps)
        self.TryStartCooldownTimers()
        reloadTimes = self.stateManager.GetReloadTimes(self.id)
        if reloadTimes:
            startTime, duration = reloadTimes
            self.DoReloadAnimation(duration, startTime=startTime)
        repeat = settings.char.autorepeat.Get(self.sr.moduleInfo.itemID, -1)
        if group.groupID in (const.groupMiningLaser, const.groupStripMiner):
            self.SetRepeat(1000)
        elif repeat != -1:
            self.SetRepeat(repeat)
        else:
            repeatSet = 0
            for key in self.sr.moduleInfo.effects.iterkeys():
                effect = self.sr.moduleInfo.effects[key]
                if self.IsEffectRepeatable(effect):
                    self.SetRepeat(1000)
                    repeatSet = 1
                    break

            if not repeatSet:
                self.SetRepeat(0)
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        if not self.isDeactivating:
            self.isInActiveState = True
        else:
            self.isInActiveState = False
        self.slaves = self.dogmaLocation.GetSlaveModules(self.sr.moduleInfo.itemID, session.shipid)
        moduleDamage = self.GetModuleDamage()
        if moduleDamage:
            self.SetDamage(moduleDamage / moduleinfo.hp)
        else:
            self.SetDamage(0.0)
        self.EnableDrag()
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        uthread.new(self.BlinkIcon)

    def OLButtonDown(self, btn, *args):
        btn.top = 6

    def OLButtonUp(self, btn, *args):
        btn.top = 5

    def OLMouseExit(self, btn, *args):
        btn.top = 5

    def ToggleOverload(self, *args):
        if settings.user.ui.Get('lockOverload', 0):
            eve.Message('error')
            eve.Message('LockedOverloadState')
            return
        for effect in self.sr.moduleInfo.effects.itervalues():
            if effect.effectCategory == const.dgmEffOverload:
                effectID = effect.effectID
                break
        else:
            return

        overloadState = self.stateManager.GetOverloadState(self.sr.moduleInfo.itemID)
        eve.Message('click')
        itemID = self.sr.moduleInfo.itemID
        if overloadState == godma.MODULE_NOT_OVERLOADED:
            self.stateManager.Overload(itemID, effectID)
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOffOverload')
        elif overloadState == godma.MODULE_OVERLOADED:
            self.stateManager.StopOverload(itemID, effectID)
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')
        elif overloadState == godma.MODULE_PENDING_OVERLOADING:
            self.stateManager.StopOverload(itemID, effectID)
        elif overloadState == godma.MODULE_PENDING_STOPOVERLOADING:
            self.stateManager.StopOverload(itemID, effectID)

    def UpdateOverloadState(self):
        overloadState = self.stateManager.GetOverloadState(self.sr.moduleInfo.itemID)
        if overloadState == godma.MODULE_PENDING_OVERLOADING:
            self.animation = uicore.animations.BlinkIn(self.sr.overloadButton, startVal=1.8, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT)
        elif overloadState == godma.MODULE_PENDING_STOPOVERLOADING:
            self.animation = uicore.animations.BlinkIn(self.sr.overloadButton, startVal=0.2, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT)
        else:
            if self.animation:
                self.animation.Stop()
            self.sr.overloadButton.SetAlpha(1.0)
        if overloadState == godma.MODULE_OVERLOADED:
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOffOverload')
        elif overloadState == godma.MODULE_NOT_OVERLOADED:
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')

    def InitQuantityLabel(self):
        if self.sr.qtylabel is None:
            quantityParent = uiprimitives.Container(parent=self, name='quantityParent', pos=(18, 27, 24, 10), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
            self.sr.qtylabel = uicontrols.Label(text='', parent=quantityParent, fontsize=9, letterspace=1, left=3, top=0, width=30, state=uiconst.UI_DISABLED)
            underlay = uiprimitives.Sprite(parent=quantityParent, name='underlay', pos=(0, 0, 0, 0), align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotQuantityUnderlay.png', color=(0.0, 0.0, 0.0, 1.0))

    def SetCharge(self, charge):
        if charge and charge.stacksize != 0:
            if self.charge is None or charge.typeID != self.charge.typeID:
                self.icon.LoadIconByTypeID(charge.typeID)
            self.charge = charge
            self.stateManager.ChangeAmmoTypeForModule(self.sr.moduleInfo.itemID, charge.typeID)
            self.id = charge.itemID
            self.UpdateChargeQuantity(charge)
        else:
            self.icon.LoadIconByTypeID(self.sr.moduleInfo.typeID)
            if self.sr.qtylabel:
                self.sr.qtylabel.parent.state = uiconst.UI_HIDDEN
            self.quantity = 0
            self.id = self.sr.moduleInfo.itemID
            self.charge = None
        self.CheckOverload()
        self.CheckOnline()
        self.CheckMasterSlave()

    def UpdateChargeQuantity(self, charge):
        if charge is self.charge:
            if cfg.invtypes.Get(charge.typeID).groupID in cfg.GetCrystalGroups():
                if self.sr.qtylabel:
                    self.sr.qtylabel.parent.state = uiconst.UI_HIDDEN
                return
            self.InitQuantityLabel()
            self.quantity = charge.stacksize
            self.sr.qtylabel.text = '%s' % util.FmtAmt(charge.stacksize)
            self.sr.qtylabel.parent.state = uiconst.UI_DISABLED

    def ShowGroupHighlight(self):
        self.dragging = True
        if self.sr.groupHighlight is None:
            groupHighlight = uiprimitives.Container(parent=self.parent, name='groupHighlight', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
            leftCircle = uiprimitives.Sprite(parent=groupHighlight, name='leftCircle', pos=(0, 0, 32, 64), texturePath='res:/UI/Texture/classes/ShipUI/slotRampLeft.png')
            rightCircle = uiprimitives.Sprite(parent=groupHighlight, name='leftCircle', pos=(32, 0, 32, 64), texturePath='res:/UI/Texture/classes/ShipUI/slotRampRight.png')
            self.sr.groupHighlight = groupHighlight
        else:
            self.sr.groupHighlight.state = uiconst.UI_DISABLED
        uthread.new(self.PulseGroupHighlight)

    def StopShowingGroupHighlight(self):
        self.dragging = False
        if self.sr.groupHighlight:
            self.sr.groupHighlight.state = uiconst.UI_HIDDEN

    def PulseGroupHighlight(self):
        pulseSize = 0.4
        opacity = 1.0
        startTime = blue.os.GetSimTime()
        while self.dragging:
            self.sr.groupHighlight.opacity = opacity
            blue.pyos.synchro.SleepWallclock(200)
            if not self or self.destroyed:
                break
            sinWave = math.cos(float(blue.os.GetSimTime() - startTime) / (0.5 * const.SEC))
            opacity = min(sinWave * pulseSize + (1 - pulseSize / 2), 1)

    def SetDamage(self, damage):
        if not damage or damage < 0.0001:
            if self.sr.damageState:
                self.sr.damageState.state = uiconst.UI_HIDDEN
            return
        imageIndex = max(1, int(damage * 8))
        if self.sr.damageState is None:
            if self.sr.ramps:
                idx = OVERLOADBTN_INDEX + 2
            else:
                idx = OVERLOADBTN_INDEX + 1
            self.sr.damageState = DamageStateCont(parent=self.parent, name='damageState', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, texturePath='res:/UI/Texture/classes/ShipUI/slotDamage_%s.png' % imageIndex, idx=idx)
        self.sr.damageState.state = uiconst.UI_NORMAL
        self.sr.damageState.SetDamage(damage)
        amount = self.sr.moduleInfo.damage / self.sr.moduleInfo.hp * 100
        self.sr.damageState.hint = localization.GetByLabel('UI/Inflight/Overload/hintDamagedModule', preText='', amount=amount)
        self.sr.damageState.Blink(damage)

    def GetVolume(self):
        if self.charge:
            return GetItemVolume(self.charge, 1)

    def IsItemHere(self, rec):
        ret = rec.locationID == eve.session.shipid and rec.flagID == self.locationFlag and cfg.invtypes.Get(rec.typeID).Group().Category().id == const.categoryCharge
        return ret

    def AddItem(self, rec):
        if cfg.invtypes.Get(rec.typeID).categoryID == const.categoryCharge:
            self.RemoveModulesBeingReloaded()
            self.SetCharge(rec)

    def UpdateItem(self, rec, change):
        if cfg.invtypes.Get(rec.typeID).categoryID == const.categoryCharge:
            self.RemoveModulesBeingReloaded()
            self.SetCharge(rec)

    def RemoveItem(self, rec):
        if cfg.invtypes.Get(rec.typeID).categoryID == const.categoryCharge:
            if self.charge and rec.itemID == self.id:
                self.RemoveModulesBeingReloaded()
                self.SetCharge(None)

    def RemoveModulesBeingReloaded(self):
        if self.stateManager.GetReloadTimes(self.sr.moduleInfo.itemID) is None:
            return
        self.stateManager.RemoveModulesBeingReloaded(self.sr.moduleInfo.itemID)
        slaves = self.dogmaLocation.GetSlaveModules(self.sr.moduleInfo.itemID, session.shipid)
        if slaves:
            for eachSlaveID in slaves:
                self.stateManager.RemoveModulesBeingReloaded(eachSlaveID)

    def GetShell(self):
        return sm.GetService('invCache').GetInventoryFromId(eve.session.shipid)

    def IsCorrectChargeSize(self, item, wantChargeSize):
        if not self.__chargesizecache__.has_key(item.typeID):
            cRS = cfg.dgmtypeattribs.get(item.typeID, [])
            cAttribs = IndexedRows(cRS, ('attributeID',))
            if cAttribs.has_key(const.attributeChargeSize):
                gotChargeSize = cAttribs[const.attributeChargeSize].value
            else:
                gotChargeSize = 0
            self.__chargesizecache__[item.typeID] = gotChargeSize
        else:
            gotChargeSize = self.__chargesizecache__[item.typeID]
        if wantChargeSize != gotChargeSize:
            return 0
        return 1

    def UnloadToCargo(self, itemID):
        self.reloadingAmmo = True
        try:
            self.dogmaLocation.UnloadChargeToContainer(session.shipid, itemID, (session.shipid,), const.flagCargo)
        finally:
            self.reloadingAmmo = False

    def ReloadAmmo(self, itemID, quantity, preferSingletons = False):
        if not quantity:
            return
        self.reloadingAmmo = True
        lastChargeTypeID = self.stateManager.GetAmmoTypeForModule(self.sr.moduleInfo.itemID)
        try:
            self.dogmaLocation.LoadChargeToModule(self.sr.moduleInfo.itemID, lastChargeTypeID, preferSingletons=preferSingletons)
        finally:
            self.reloadingAmmo = False

    def ReloadAllAmmo(self):
        uicore.cmd.CmdReloadAmmo()

    def BlinkIcon(self, time = None):
        """
            time is in ms. it's how long the button is supposed to blink
        """
        if self.destroyed or self.blinking:
            return
        startTime = blue.os.GetSimTime()
        if time is not None:
            timeToBlink = time * 10000
        while self.changingAmmo or self.reloadingAmmo or self.waitingForActiveTarget or time:
            if time is not None:
                if blue.os.GetSimTime() - startTime > timeToBlink:
                    break
            blue.pyos.synchro.SleepWallclock(250)
            if self.destroyed:
                return
            self.icon.SetAlpha(0.25)
            blue.pyos.synchro.SleepWallclock(250)
            if self.destroyed:
                return
            self.icon.SetAlpha(1.0)

        if self.destroyed:
            return
        self.blinking = 0
        self.CheckOverload()
        self.CheckOnline()

    def ChangeAmmo(self, itemID, quantity, ammoType):
        if not quantity:
            return
        self.changingAmmo = 1
        try:
            self.dogmaLocation.LoadChargeToModule(itemID, ammoType, qty=quantity)
        finally:
            if self and not self.destroyed:
                self.changingAmmo = 0

    def DoNothing(self, *args):
        pass

    def CopyItemIDToClipboard(self, itemID):
        blue.pyos.SetClipboardData(str(itemID))

    def GetMenu(self):
        ship = sm.GetService('godma').GetItem(eve.session.shipid)
        if ship is None:
            return []
        m = []
        if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            if cfg.IsChargeCompatible(self.sr.moduleInfo):
                m += [('Launcher: ' + str(self.sr.moduleInfo.itemID), self.CopyItemIDToClipboard, (self.sr.moduleInfo.itemID,))]
                if self.id != self.sr.moduleInfo.itemID:
                    m += [('Charge: ' + str(self.id), self.CopyItemIDToClipboard, (self.id,)), None]
            else:
                m += [(str(self.id), self.CopyItemIDToClipboard, (self.id,)), None]
            m += sm.GetService('menu').GetGMTypeMenu(self.sr.moduleInfo.typeID, itemID=self.id, divs=True, unload=True)
        moduleType = cfg.invtypes.Get(self.sr.moduleInfo.typeID)
        groupID = moduleType.groupID
        if cfg.IsChargeCompatible(self.sr.moduleInfo):
            chargeTypeID, chargeQuantity, roomForReload = self.GetChargeReloadInfo()
            chargeID = self.charge.itemID if self.charge is not None else None
            m.extend(self.dogmaLocation.GetAmmoMenu(session.shipid, self.sr.moduleInfo.itemID, chargeID, roomForReload))
            if self.autoreload == 0:
                m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoReloadOn'), self.SetAutoReload, (1,)))
            else:
                m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoReloadOff'), self.SetAutoReload, (0,)))
        overloadLock = settings.user.ui.Get('lockOverload', 0)
        itemID = self.sr.moduleInfo.itemID
        slaves = self.dogmaLocation.GetSlaveModules(itemID, session.shipid)
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if self.IsEffectRepeatable(effect) and groupID not in (const.groupMiningLaser, const.groupStripMiner):
                if self.autorepeat == 0:
                    m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoRepeatOn'), self.SetRepeat, (1000,)))
                else:
                    m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoRepeatOff'), self.SetRepeat, (0,)))
            if effect.effectName == 'online':
                m.append(None)
                if not slaves:
                    if effect.isActive:
                        m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/PutModuleOffline'), self.ChangeOnline, (0,)))
                    else:
                        m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/PutModuleOnline'), self.ChangeOnline, (1,)))
            if not overloadLock and effect.effectCategory == const.dgmEffOverload:
                active = effect.isActive
                if active:
                    m.append((uiutil.MenuLabel('UI/Inflight/Overload/TurnOffOverload'), self.Overload, (0, effect)))
                else:
                    m.append((uiutil.MenuLabel('UI/Inflight/Overload/TurnOnOverload'), self.Overload, (1, effect)))
                m.append((uiutil.MenuLabel('UI/Inflight/OverloadRack'), self.OverloadRack, ()))
                m.append((uiutil.MenuLabel('UI/Inflight/StopOverloadingRack'), self.StopOverloadRack, ()))

        moduleDamage = self.GetModuleDamage()
        if moduleDamage:
            if self.isBeingRepaired:
                m.append((uiutil.MenuLabel('UI/Inflight/menuCancelRepair'), self.CancelRepair, ()))
            else:
                m.append((uiutil.MenuLabel('UI/Commands/Repair'), self.RepairModule, ()))
        if slaves:
            m.append((uiutil.MenuLabel('UI/Fitting/ClearGroup'), self.UnlinkModule, ()))
        m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), sm.GetService('info').ShowInfo, (self.sr.moduleInfo.typeID,
           self.sr.moduleInfo.itemID,
           0,
           self.sr.moduleInfo))]
        return m

    def RepairModule(self):
        success = self.stateManager.RepairModule(self.sr.moduleInfo.itemID)
        if self.slaves:
            for slave in self.slaves:
                success = self.stateManager.RepairModule(slave) or success

        if success == True:
            self.isBeingRepaired = True
            self.SetRepairing()

    def CancelRepair(self):
        success = self.stateManager.StopRepairModule(self.sr.moduleInfo.itemID)
        if self.slaves:
            for slave in self.slaves:
                success = self.stateManager.StopRepairModule(slave) and success

        if success == True:
            self.isBeingRepaired = False
            self.RemoveRepairing()

    def OnFailLockTarget(self, tid, *args):
        self.waitingForActiveTarget = 0

    def OnModuleRepaired(self, itemID):
        if itemID == self.sr.moduleInfo.itemID:
            self.RemoveRepairing()
            self.isBeingRepaired = False

    def OnAmmoInBankChanged(self, masterID):
        slaves = self.dogmaLocation.GetSlaveModules(masterID, session.shipid)
        if self.sr.moduleInfo.itemID in slaves:
            self.SetCharge(self.sr.moduleInfo)

    def OnChargeBeingLoadedToModule(self, itemIDs, chargeTypeID, time):
        if self.sr.moduleInfo.itemID not in itemIDs:
            return
        chargeGroupID = self.stateManager.GetType(chargeTypeID).groupID
        params = {'ammoGroupName': (const.UE_GROUPID, chargeGroupID),
         'launcherGroupName': (const.UE_GROUPID, self.sr.moduleInfo.groupID),
         'time': time / 1000}
        eve.Message('LauncherLoadDelay', params)
        self.DoReloadAnimation(time)

    def DoReloadAnimation(self, duration, startTime = None):
        if startTime:
            blinkTime = max(0, duration - (blue.os.GetSimTime() - startTime) / 10000)
        else:
            blinkTime = duration
        uthread.new(self.ShowReloadLeft, duration, startTime)
        uthread.new(self.BlinkIcon, blinkTime)

    def TryStartCooldownTimers(self):
        cooldownTimes = self.stateManager.GetCooldownTimes(self.sr.moduleInfo.itemID)
        if cooldownTimes:
            startTime, duration = cooldownTimes
            self.DoReactivationAnimation(duration, startTime=startTime)

    def DoReactivationAnimation(self, duration, startTime = None):
        uthread.new(self.ShowReactivationLeft, duration, startTime)

    def UnlinkModule(self):
        self.dogmaLocation.DestroyWeaponBank(session.shipid, self.sr.moduleInfo.itemID)

    def Overload(self, onoff, eff):
        if onoff:
            eff.Activate()
        else:
            eff.Deactivate()

    def OverloadRack(self):
        sm.GetService('godma').OverloadRack(self.sr.moduleInfo.itemID)

    def StopOverloadRack(self):
        sm.GetService('godma').StopOverloadRack(self.sr.moduleInfo.itemID)

    def GetChargeReloadInfo(self, ignoreCharge = 0):
        moduleType = cfg.invtypes.Get(self.sr.moduleInfo.typeID)
        lastChargeTypeID = self.stateManager.GetAmmoTypeForModule(self.sr.moduleInfo.itemID)
        if self.charge and not ignoreCharge:
            chargeTypeID = self.charge.typeID
            chargeQuantity = self.charge.stacksize
        elif lastChargeTypeID is not None:
            chargeTypeID = lastChargeTypeID
            chargeQuantity = 0
        else:
            chargeTypeID = None
            chargeQuantity = 0
        if chargeTypeID is not None:
            roomForReload = int(moduleType.capacity / cfg.invtypes.Get(chargeTypeID).volume - chargeQuantity + 1e-07)
        else:
            roomForReload = 0
        return (chargeTypeID, chargeQuantity, roomForReload)

    def SetAutoReload(self, on):
        settings.char.autoreload.Set(self.sr.moduleInfo.itemID, on)
        self.autoreload = on
        self.AutoReload()

    def AutoReload(self, force = 0, useItemID = None, useQuant = None):
        if self.reloadingAmmo is not False:
            return
        if not cfg.IsChargeCompatible(self.sr.moduleInfo) or not (self.autoreload or force):
            return
        chargeTypeID, chargeQuantity, roomForReload = self.GetChargeReloadInfo()
        if chargeQuantity > 0 and not force or roomForReload <= 0:
            return
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        self.dogmaLocation.LoadChargeToModule(self.sr.moduleInfo.itemID, chargeTypeID)
        uthread.new(self.CheckPending)

    def OnItemChange(self, item, change):
        if not self or self.destroyed or not getattr(self, 'sr', None):
            return
        if const.ixQuantity not in change:
            return
        if self.reloadingAmmo == item.itemID and not sm.GetService('invCache').IsItemLocked(self, item.itemID):
            shiplayer = uicore.layer.shipui
            reloadsByID = shiplayer.sr.reloadsByID
            self.reloadingAmmo = True
            if reloadsByID[item.itemID].balance:
                reloadsByID[item.itemID].send(None)
            else:
                del reloadsByID[item.itemID]

    def CheckPending(self):
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        blue.pyos.synchro.SleepSim(1000)
        if shiplayer and shiplayer:
            shiplayer.CheckPendingReloads()

    def CheckOverload(self):
        if not self or self.destroyed:
            return
        isActive = False
        hasOverloadEffect = False
        if not util.HasAttrs(self, 'sr', 'moduleInfo', 'effects'):
            return
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectCategory == const.dgmEffOverload:
                if effect.isActive:
                    isActive = True
                hasOverloadEffect = True

        if hasOverloadEffect:
            self.sr.overloadButton.top = 5
            if self.online:
                if isActive:
                    self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadOn.png')
                    self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOffOverload')
                else:
                    self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadOff.png')
                    self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')
                self.sr.overloadButton.state = uiconst.UI_NORMAL
            else:
                self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadDisabled.png')
                self.sr.overloadButton.state = uiconst.UI_DISABLED
        else:
            self.sr.overloadButton.top = 6
            self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadDisabled.png')
            self.sr.overloadButton.state = uiconst.UI_DISABLED

    def CheckMasterSlave(self):
        if not self or self.destroyed:
            return
        itemID = self.sr.moduleInfo.itemID
        slaves = self.dogmaLocation.GetSlaveModules(itemID, session.shipid)
        if slaves:
            if self.sr.stackParent is None:
                stackParent = uiprimitives.Container(parent=self, name='stackParent', pos=(6, 27, 12, 10), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
                self.sr.stacklabel = uicontrols.Label(text=len(slaves) + 1, parent=stackParent, fontsize=9, letterspace=1, left=5, top=0, width=30, state=uiconst.UI_DISABLED, shadowOffset=(0, 0), color=(1.0, 1.0, 1.0, 1))
                underlay = uiprimitives.Sprite(parent=stackParent, name='underlay', pos=(0, 0, 0, 0), align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotStackUnderlay.png', color=(0.51, 0.0, 0.0, 1.0))
                self.sr.stackParent = stackParent
            else:
                self.sr.stackParent.state = uiconst.UI_DISABLED
                self.sr.stacklabel.text = len(slaves) + 1
        elif self.sr.stackParent:
            self.sr.stackParent.state = uiconst.UI_HIDDEN

    def CheckOnline(self, sound = 0):
        if not self or self.destroyed:
            return
        if not util.HasAttrs(self, 'sr', 'moduleInfo', 'effects'):
            return
        for key in self.sr.moduleInfo.effects.keys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectName == 'online':
                if effect.isActive:
                    self.ShowOnline()
                    if sound:
                        eve.Message('OnLogin')
                else:
                    self.ShowOffline()
                return

    def ChangeOnline(self, on = 1):
        uthread.new(self._ChangeOnline, on)

    def _ChangeOnline(self, on):
        masterID = self.dogmaLocation.IsInWeaponBank(session.shipid, self.sr.moduleInfo.itemID)
        if masterID:
            if not on:
                ret = eve.Message('CustomQuestion', {'header': 'OFFLINE',
                 'question': "When offlining this module you will destroy the weapons bank it's in. Are you sure you want to offline it? "}, uiconst.YESNO)
                if ret != uiconst.ID_YES:
                    return
        elif not on and eve.Message('PutOffline', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        for key in self.sr.moduleInfo.effects.keys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectName == 'online':
                if on:
                    effect.Activate()
                else:
                    self.ShowOffline(1)
                    effect.Deactivate()
                return

    def ShowOverload(self, on):
        self.CheckOverload()

    def ShowOnline(self):
        self.isMaster = 0
        if self.AreModulesOffline():
            self.ShowOffline()
            return
        self.online = True
        if self.grey:
            self.icon.SetAlpha(0.1)
        else:
            self.icon.SetAlpha(1.0)
        self.CheckOverload()

    def ShowOffline(self, ping = 0):
        self.online = False
        if self.grey:
            self.icon.SetAlpha(0.1)
        else:
            self.icon.SetAlpha(0.25)
        if ping:
            eve.Message('OnLogin')
        self.CheckOverload()
        self.isInActiveState = True

    def AreModulesOffline(self):
        slaves = self.dogmaLocation.GetSlaveModules(self.sr.moduleInfo.itemID, session.shipid)
        if not slaves:
            return False
        self.isMaster = 1
        onlineEffect = self.stateManager.GetEffect(self.sr.moduleInfo.itemID, 'online')
        if onlineEffect is None or not onlineEffect.isActive:
            return True
        for slave in slaves:
            onlineEffect = self.stateManager.GetEffect(slave, 'online')
            if onlineEffect is None or not onlineEffect.isActive:
                return True

        return False

    def IsEffectRepeatable(self, effect, activatibleKnown = 0):
        if activatibleKnown or self.IsEffectActivatible(effect):
            if not effect.item.disallowRepeatingActivation:
                return effect.durationAttributeID is not None
        return 0

    def IsEffectActivatible(self, effect):
        return effect.isDefault and effect.effectName != 'online' and effect.effectCategory in (const.dgmEffActivation, const.dgmEffTarget)

    def SetRepeat(self, num):
        settings.char.autorepeat.Set(self.sr.moduleInfo.itemID, num)
        self.autorepeat = num

    def GetDefaultEffect(self):
        if not self or self.destroyed:
            return
        if self.sr is None or self.sr.moduleInfo is None or not self.stateManager.IsItemLoaded(self.sr.moduleInfo.itemID):
            return
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if self.IsEffectActivatible(effect):
                return effect

    def OnClick(self, *args):
        if not self or self.IsBeingDragged() or not self.isInActiveState:
            return
        sm.GetService('audio').SendUIEvent('wise:/msg_click_play')
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            self.ToggleOverload()
            return
        ctrlRepeat = 0
        if uicore.uilib.Key(uiconst.VK_CONTROL):
            ctrlRepeat = 1000
        self.Click(ctrlRepeat)

    def Click(self, ctrlRepeat = 0):
        if self.waitingForActiveTarget:
            sm.GetService('target').CancelTargetOrder(self)
            self.waitingForActiveTarget = 0
        elif self.def_effect is None:
            log.LogWarn('No default Effect available for this moduletypeID:', self.sr.moduleInfo.typeID)
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/ModuleRacks/TryingToActivatePassiveModule')})
        elif not self.online:
            if getattr(self, 'isMaster', None):
                eve.Message('ClickOffllineGroup')
            else:
                eve.Message('ClickOffllineModule')
        elif self.def_effect.isActive:
            self.DeactivateEffect(self.def_effect)
        elif not self.effect_activating:
            self.activationTimer = base.AutoTimer(500, self.ActivateEffectTimer)
            self.effect_activating = 1
            self.ActivateEffect(self.def_effect, ctrlRepeat=ctrlRepeat)

    def ActivateEffectTimer(self, *args):
        self.effect_activating = 0
        self.activationTimer = None

    def OnEndDrag(self, *args):
        uthread.new(uicore.layer.shipui.ResetSwapMode)

    def GetDragData(self, *args):
        if settings.user.ui.Get('lockModules', 0):
            return []
        if self.charge:
            fakeNode = uix.GetItemData(self.charge, 'icons')
            fakeNode.isCharge = 1
        else:
            fakeNode = uix.GetItemData(self.sr.moduleInfo, 'icons')
            fakeNode.isCharge = 0
        fakeNode.__guid__ = 'xtriui.ShipUIModule'
        fakeNode.slotFlag = self.sr.moduleInfo.flagID
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        uicore.layer.shipui.StartDragMode(self.sr.moduleInfo.itemID, self.sr.moduleInfo.typeID)
        return [fakeNode]

    def OnDropData(self, dragObj, nodes):
        log.LogInfo('Module.OnDropData', self.id)
        flag1 = self.sr.moduleInfo.flagID
        flag2 = None
        for node in nodes:
            if node.Get('__guid__', None) == 'xtriui.ShipUIModule':
                flag2 = node.slotFlag
                break

        if flag1 == flag2:
            return
        if flag2 is not None:
            uicore.layer.shipui.ChangeSlots(flag1, flag2)
            return
        multiLoadCharges = True
        chargeTypeID = None
        chargeItems = []
        for node in nodes:
            if not hasattr(node, 'rec'):
                return
            chargeItem = node.rec
            if not hasattr(chargeItem, 'categoryID'):
                return
            if chargeItem.categoryID != const.categoryCharge:
                continue
            if chargeTypeID is None:
                chargeTypeID = chargeItem.typeID
            if chargeItem.typeID == chargeTypeID:
                chargeItems.append(chargeItem)

        if len(chargeItems) > 0:
            self.dogmaLocation.DropLoadChargeToModule(self.sr.moduleInfo.itemID, chargeTypeID, chargeItems=chargeItems)

    def OnMouseHover(self, *args):
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            self.OverloadHiliteOn()
        else:
            self.OverloadHiliteOff()

    def OnMouseDown(self, *args):
        uiprimitives.Container.OnMouseDown(self, *args)
        log.LogInfo('Module.OnMouseDown', self.id)
        if getattr(self, 'downTop', None) is not None or not self.isInActiveState or self.def_effect is None:
            return
        self.downTop = self.parent.top
        self.parent.top += 2

    def OnMouseUp(self, *args):
        uiprimitives.Container.OnMouseUp(self, *args)
        if self.destroyed:
            return
        log.LogInfo('Module.OnMouseUp', self.id)
        if getattr(self, 'downTop', None) is not None:
            self.parent.top = self.downTop
            self.downTop = None
        if len(args) > 0 and args[0] == uiconst.MOUSERIGHT and getattr(uicore.layer.hint, 'moduleButtonHint', None):
            uicore.layer.hint.moduleButtonHint.FadeOpacity(0.0)

    def OnMouseEnter(self, *args):
        uthread.pool('ShipMobuleButton::MouseEnter', self.MouseEnter)

    def MouseEnter(self, *args):
        if self.destroyed or sm.GetService('godma').GetItem(self.sr.moduleInfo.itemID) is None:
            return
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            self.OverloadHiliteOn()
        self.SetHilite()
        tacticalSvc = sm.GetService('tactical')
        bracketMgr = sm.GetService('bracket')
        maxRange, falloffDist, bombRadius = tacticalSvc.FindMaxRange(self.sr.moduleInfo, self.charge)
        if maxRange > 0:
            bracketMgr.ShowModuleRange(self.sr.moduleInfo.itemID, maxRange + falloffDist)
            bracketMgr.ShowHairlinesForModule(self.sr.moduleInfo.itemID)
        log.LogInfo('Module.OnMouseEnter', self.id)
        eve.Message('NeocomButtonEnter')
        if settings.user.ui.Get('showModuleTooltips', 1):
            if self.tooltipPanelClassInfo is None:
                self.tooltipPanelClassInfo = TooltipModuleWrapper()
        else:
            self.tooltipPanelClassInfo = None
        uthread.pool('ShipMobuleButton::OnMouseEnter-->UpdateTargetingRanges', tacticalSvc.UpdateTargetingRanges, self.sr.moduleInfo, self.charge)

    def GetTooltipDelay(self):
        return settings.user.ui.Get(TOOLTIP_SETTINGS_MODULE, TOOLTIP_DELAY_MODULE)

    def OnMouseExit(self, *args):
        self.RemoveHilite()
        sm.GetService('bracket').StopShowingModuleRange(self.sr.moduleInfo.itemID)
        self.OverloadHiliteOff()
        log.LogInfo('Module.OnMouseExit', self.id)
        self.OnMouseUp(None)

    def UpdateInfo_TimedCall(self):
        self.UpdateInfo()

    def UpdateInfo(self):
        """
            This function returns True if it was finished, otherwise False
        """
        if self.destroyed or not self.moduleButtonHint or self.moduleButtonHint.destroyed:
            self.moduleButtonHint = None
            self.updateTimer = None
            return False
        if not self.stateManager.IsItemLoaded(self.id):
            return False
        chargeItemID = None
        if self.charge:
            chargeItemID = self.charge.itemID
        self.moduleButtonHint.UpdateAllInfo(self.sr.moduleInfo.itemID, chargeItemID)
        requiredSafetyLevel = self.GetRequiredSafetyLevel()
        if self.crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
            self.moduleButtonHint.SetSafetyWarning(requiredSafetyLevel)
        else:
            self.moduleButtonHint.RemoveSafetyWarning()
        return True

    def GetSafetyWarning(self):
        requiredSafetyLevel = self.GetRequiredSafetyLevel()
        if self.crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
            return requiredSafetyLevel
        else:
            return None

    def GetModuleDamage(self):
        return uicore.layer.shipui.GetModuleGroupDamage(self.sr.moduleInfo.itemID)

    def GetAccuracy(self, targetID = None):
        if self is None or self.destroyed:
            return

    def SetActive(self):
        self.InitGlow()
        self.sr.glow.state = uiconst.UI_DISABLED
        sm.GetService('ui').BlinkSpriteA(self.sr.glow, 0.75, 1000, None, passColor=0)
        self.effect_activating = 0
        self.activationTimer = None
        self.isInActiveState = True
        self.ActivateRamps()

    def SetDeactivating(self):
        self.isDeactivating = True
        if self.sr.glow:
            self.sr.glow.state = uiconst.UI_HIDDEN
        self.InitBusyState()
        self.sr.busy.state = uiconst.UI_DISABLED
        sm.GetService('ui').BlinkSpriteA(self.sr.busy, 0.75, 1000, None, passColor=0)
        self.isInActiveState = False
        self.DeActivateRamps()

    def SetIdle(self):
        self.isDeactivating = False
        if self.sr.glow:
            self.sr.glow.state = uiconst.UI_HIDDEN
            sm.GetService('ui').StopBlink(self.sr.glow)
        if self.sr.busy:
            self.sr.busy.state = uiconst.UI_HIDDEN
            sm.GetService('ui').StopBlink(self.sr.busy)
        self.isInActiveState = True
        self.IdleRamps()
        self.TryStartCooldownTimers()

    def SetRepairing(self, startTime = None):
        self.InitGlow()
        self.sr.glow.state = uiconst.UI_DISABLED
        self.sr.glow.SetRGB(1, 1, 1, 1)
        sm.GetService('ui').BlinkSpriteA(self.sr.glow, 0.9, 2500, None, passColor=0)
        self.isInActiveState = True
        uthread.new(self.ShowRepairLeft, startTime)

    def RemoveRepairing(self):
        if self.sr.glow:
            sm.GetService('ui').StopBlink(self.sr.glow)
            self.sr.glow.SetRGB(*GLOWCOLOR)
            self.sr.glow.state = uiconst.UI_HIDDEN
        if self.sr.damageState:
            self.sr.damageState.StopRepair()

    def SetHilite(self):
        self.InitHilite()
        self.sr.hilite.display = True
        requiredSafetyLevel = self.GetRequiredSafetyLevel()
        if self.crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
            self.InitSafetyGlow()
            if requiredSafetyLevel == const.shipSafetyLevelNone:
                color = crimewatchConst.Colors.Criminal
            else:
                color = crimewatchConst.Colors.Suspect
            self.sr.safetyGlow.color.SetRGBA(*color.GetRGBA())
            self.sr.safetyGlow.display = True

    def GetRequiredSafetyLevel(self):
        requiredSafetyLevel = self.crimewatchSvc.GetRequiredSafetyLevelForEffect(self.GetRelevantEffect(), targetID=None)
        return requiredSafetyLevel

    def RemoveHilite(self):
        if self.sr.hilite:
            self.sr.hilite.display = False
        if self.sr.safetyGlow:
            self.sr.safetyGlow.display = False

    def InitSafetyGlow(self):
        if self.sr.safetyGlow is None:
            self.sr.safetyGlow = uiprimitives.Sprite(parent=self.parent, name='safetyGlow', padding=2, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/slotGlow.png', color=crimewatchConst.Colors.Yellow.GetRGBA())

    def InitGlow(self):
        if self.sr.glow is None:
            self.sr.glow = uiprimitives.Sprite(parent=self.parent, name='glow', padding=2, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/slotGlow.png', color=GLOWCOLOR)

    def InitBusyState(self):
        if self.sr.busy is None:
            self.sr.busy = uiprimitives.Sprite(parent=self.parent, name='busy', padding=2, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/slotGlow.png', color=BUSYCOLOR)

    def InitHilite(self):
        if self.sr.hilite is None:
            if getattr(self.parent, 'mainShape', None) is not None:
                idx = max(-1, uiutil.GetIndex(self.parent.mainShape) - 1)
            else:
                idx = -1
            self.sr.hilite = uiprimitives.Sprite(parent=self.parent, name='hilite', padding=(10, 10, 10, 10), align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotHilite.png', blendMode=trinity.TR2_SBM_ADDX2, idx=idx)
            self.sr.hilite.display = False

    def OverloadHiliteOn(self):
        self.sr.overloadButton.SetAlpha(1.5)

    def OverloadHiliteOff(self):
        self.sr.overloadButton.SetAlpha(1.0)

    def GetEffectByName(self, effectName):
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectName == effectName:
                return effect

    def Update(self, effectState):
        if not self or self.destroyed:
            return
        if not self.stateManager.IsItemLoaded(self.id):
            return
        if self.def_effect and effectState.effectName == self.def_effect.effectName:
            if effectState.start:
                self.SetActive()
            else:
                self.SetIdle()
        effect = self.GetEffectByName(effectState.effectName)
        if effect and effect.effectCategory == const.dgmEffOverload:
            self.ShowOverload(effect.isActive)
        if effectState.effectName == 'online':
            if effectState.active:
                self.ShowOnline()
            else:
                self.ShowOffline()
        if effect.effectCategory in [const.dgmEffTarget, const.dgmEffActivation, const.dgmEffArea] and effect.effectID != const.effectOnline:
            if not effectState.active and self.quantity == 0:
                self.AutoReload()
        self.UpdateInfo()

    def GetRelevantEffect(self):
        if self.def_effect and (self.def_effect.effectName == 'useMissiles' or self.def_effect.effectName == 'warpDisruptSphere' and self.charge is not None):
            if self.charge is None:
                return
            effect = sm.GetService('godma').GetStateManager().GetDefaultEffect(self.charge.typeID)
        else:
            effect = self.def_effect
        return effect

    def ActivateEffect(self, effect, targetID = None, ctrlRepeat = 0):
        if self.charge and self.charge.typeID in const.orbitalStrikeAmmo:
            return sm.GetService('district').ActivateModule(self.sr.moduleInfo.itemID)
        relevantEffect = self.GetRelevantEffect()
        if relevantEffect is None:
            typeID, _ = self.GetModuleType()
            raise UserError('NoCharges', {'launcher': (const.UE_TYPEID, typeID)})
        if relevantEffect and not targetID and relevantEffect.effectCategory == 2:
            targetID = sm.GetService('target').GetActiveTargetID()
            if not targetID:
                sm.GetService('target').OrderTarget(self)
                uthread.new(self.BlinkIcon)
                self.waitingForActiveTarget = 1
                return
        if self.sr.Get('moduleinfo'):
            for key in self.sr.moduleInfo.effects.iterkeys():
                checkeffect = self.sr.moduleInfo.effects[key]
                if checkeffect.effectName == 'online':
                    if not checkeffect.isActive:
                        self._ChangeOnline(1)
                    break

        if self.def_effect:
            if relevantEffect.isOffensive:
                if not sm.GetService('consider').DoAttackConfirmations(targetID, relevantEffect):
                    return
            repeats = ctrlRepeat or self.autorepeat
            if not self.IsEffectRepeatable(self.def_effect, 1):
                repeats = 0
            if not self.charge:
                self.stateManager.ChangeAmmoTypeForModule(self.sr.moduleInfo.itemID, None)
            self.def_effect.Activate(targetID, repeats)

    def DeactivateEffect(self, effect):
        self.SetDeactivating()
        try:
            effect.Deactivate()
        except UserError as e:
            if e.msg == 'EffectStillActive':
                if not self.isPendingUnlockForDeactivate:
                    self.isPendingUnlockForDeactivate = True
                    uthread.new(self.DelayButtonUnlockForDeactivate, max(0, e.dict['timeLeft']))
            raise

    def DelayButtonUnlockForDeactivate(self, sleepTimeBlue):
        blue.pyos.synchro.SleepSim(sleepTimeBlue / const.MSEC)
        self.isInActiveState = True
        self.isPendingUnlockForDeactivate = False

    def OnStateChange(self, itemID, flag, isTrue, *args):
        if self and isTrue and flag == state.activeTarget and self.waitingForActiveTarget:
            self.waitingForActiveTarget = 0
            self.ActivateEffect(self.def_effect, itemID)
            sm.GetService('target').CancelTargetOrder(self)

    def GetModuleType(self):
        return (self.sr.moduleInfo.typeID, self.sr.moduleInfo.itemID)

    def ActivateRamps(self):
        if not self or self.destroyed:
            return
        if self.ramp_active:
            self.UpdateRamps()
            return
        self.DoActivateRamps()

    def DeActivateRamps(self):
        self.UpdateRamps()

    def IdleRamps(self):
        self.ramp_active = False
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        moduleID = self.sr.moduleInfo.itemID
        rampTimers = shiplayer.sr.rampTimers
        if rampTimers.has_key(moduleID):
            del rampTimers[moduleID]
        if self.sr.ramps:
            self.sr.ramps.display = False

    def UpdateRamps(self):
        self.DoActivateRamps()

    def DoActivateRamps(self):
        if self.ramp_active:
            return
        uthread.new(self.DoActivateRampsThread)

    def InitRamps(self):
        if self.sr.ramps and not self.sr.ramps.destroyed:
            return
        self.sr.ramps = ShipModuleButtonRamps(parent=self.parent, idx=OVERLOADBTN_INDEX + 1)

    def InitReactivationRamps(self):
        if self.sr.reactivationRamps and not self.sr.reactivationRamps.destroyed:
            return
        self.sr.reactivationRamps = ShipModuleReactivationTimer(parent=self.parent, idx=-1)

    def DoActivateRampsThread(self):
        if not self or self.destroyed:
            return
        (firstActivation, startTime), durationInMilliseconds = self.GetEffectTiming()
        if durationInMilliseconds <= 0:
            return
        now = blue.os.GetSimTime()
        if firstActivation:
            startTimeAdjustment = now - startTime
            if startTimeAdjustment > const.SEC:
                startTimeAdjustment = 0
            correctionTimeMS = durationInMilliseconds / 2
            adjustmentDecayPerSec = float(-startTimeAdjustment) / (correctionTimeMS / 1000)
        else:
            startTimeAdjustment = 0
            correctionTimeMS = 0
        self.ramp_active = True
        self.InitRamps()
        self.sr.ramps.display = True
        while self and not self.destroyed and self.ramp_active:
            newNow = blue.os.GetSimTime()
            deltaTime = newNow - now
            now = newNow
            if correctionTimeMS != 0:
                deltaMS = min(deltaTime / const.MSEC, correctionTimeMS)
                startTimeAdjustment += long(adjustmentDecayPerSec * (float(deltaMS) / 1000))
                correctionTimeMS -= deltaMS
            else:
                startTimeAdjustment = 0
            portionDone = blue.os.TimeDiffInMs(startTime + startTimeAdjustment, now) / durationInMilliseconds
            if portionDone > 1:
                iterations = int(portionDone)
                startTime += long(durationInMilliseconds * iterations * const.MSEC)
                _, durationInMilliseconds = self.GetEffectTiming()
                try:
                    uicore.layer.shipui.sr.rampTimers[self.sr.moduleInfo.itemID] = (False, startTime)
                except AttributeError:
                    pass

                portionDone -= iterations
                if self.InLimboState():
                    self.IdleRamps()
                    break
            self.sr.ramps.SetRampValues(portionDone)
            blue.pyos.synchro.Yield()

    def InLimboState(self):
        for each in ['waitingForActiveTarget',
         'changingAmmo',
         'reloadingAmmo',
         'isDeactivating']:
            if getattr(self, each, False):
                return True

        return False

    def GetRampStartTime(self):
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        moduleID = self.sr.moduleInfo.itemID
        rampTimers = shiplayer.sr.rampTimers
        if moduleID not in rampTimers:
            now = blue.os.GetSimTime()
            default = getattr(self.def_effect, 'startTime', now) or now
            rampTimers[moduleID] = (True, default)
        return rampTimers[moduleID]

    def ShowRepairLeft(self, startTime = None):
        dmg = self.GetModuleDamage()
        rateOfRepair = self.stateManager.GetAttribute(session.charid, 'moduleRepairRate')
        repairTime = dmg / rateOfRepair
        repairTime = int(repairTime * const.MIN)
        if startTime is None:
            startTime = blue.os.GetSimTime()
        hp = self.dogmaLocation.GetAttributeValue(self.sr.moduleInfo.itemID, const.attributeHp)
        self.sr.damageState.AnimateRepair(dmg, hp, repairTime, startTime)

    def ShowReloadLeft(self, reloadTime, startTime = None):
        if startTime is None:
            startTime = blue.os.GetSimTime()
        reloadTime = int(reloadTime * const.MSEC)
        if self.sr.reactivationRamps and self.sr.reactivationRamps.endTime > startTime + reloadTime:
            return
        self.InitRamps()
        self.sr.ramps.display = True
        self.sr.ramps.AnimateReload(startTime, reloadTime)

    def ShowReactivationLeft(self, reactivationTime, startTime = None):
        self.InitReactivationRamps()
        reactivationTime = int(reactivationTime * const.MSEC)
        if startTime is None:
            startTime = blue.os.GetSimTime()
        self.sr.reactivationRamps.AnimateTimer(startTime, reactivationTime)

    def GetEffectTiming(self):
        """
            GetEffectTiming will try to compensate for over-the-wire lag and otherwise
            unwelcome variables to the activation queue.
            
            When an effect is activated and in a repeat loop, the effect doesn't get updated
            with the new attribute on the client, the server knows about it, but we can't query
            the default effect for the correct value, instead we need to look up the correct value 
            in godma's statemanager.
            
        """
        rampStartTime = self.GetRampStartTime()
        durationInMilliseconds = 0.0
        attr = cfg.dgmattribs.GetIfExists(getattr(self.def_effect, 'durationAttributeID', None))
        item = self.stateManager.GetItem(self.def_effect.itemID)
        if item is None:
            return (0, 0.0)
        if attr:
            durationInMilliseconds = self.stateManager.GetAttribute(self.def_effect.itemID, attr.attributeName)
        if not durationInMilliseconds:
            durationInMilliseconds = getattr(self.def_effect, 'duration', 0.0)
        return (rampStartTime, durationInMilliseconds)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if not settings.user.ui.Get('showModuleTooltips', 1):
            return
        tooltipPanel.LoadGeneric1ColumnTemplate()
        self.moduleButtonHint = ModuleButtonHint(name='moduleButtonHint', align=uiconst.TOPLEFT, pos=(0,
         0,
         MAXMODULEHINTWIDTH,
         200))
        tooltipPanel.AddCell(cellObject=self.moduleButtonHint)
        chargeItemID = None
        if self.charge:
            chargeItemID = self.charge.itemID
        self.moduleButtonHint.UpdateAllInfo(self.sr.moduleInfo.itemID, chargeItemID, positionTuple=None)
        self.updateTimer = base.AutoTimer(1000, self.UpdateInfo_TimedCall)
