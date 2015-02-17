#Embedded file name: eve/client/script/ui/inflight\activeitem.py
import uicontrols
import uiprimitives
import base
import uix
import uiutil
import util
import blue
import state
from brennivin import itertoolsext
import uthread
import carbonui.const as uiconst
import uicls
import localization
import const
import telemetry
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import DefaultWarpToLabel
from spacecomponents.client.components import cargobay
from spacecomponents.common.helper import HasCargoBayComponent
from spacecomponents.common.helper import HasBountyEscrowComponent
from spacecomponents.client.components.bountyEscrow import GetBountyReductionForSolarSystem
from carbonui.control.menu import DISABLED_ENTRY0

class ActiveItem(uicontrols.Window):
    __guid__ = 'form.ActiveItem'
    __notifyevents__ = ['OnMultiSelect',
     'ProcessSessionChange',
     'OnStateChange',
     'DoBallRemove',
     'OnDistSettingsChange',
     'OnPlanetViewChanged',
     'DoBallsRemove',
     'OnActiveTrackingChange']
    default_pinned = True
    default_height = 92
    default_width = 256
    default_top = 16
    default_minSize = (default_width, default_height)
    default_windowID = 'selecteditemview'
    default_open = True

    @staticmethod
    def default_left(*args):
        return uicore.desktop.width - ActiveItem.default_width - 16

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        panelname = attributes.panelname
        self.scope = 'inflight'
        self.canAnchorToOthers = 0
        self.lastActionSerial = None
        self.lastSessionChange = None
        self.laseUpdateWidth = None
        self.lastIcon = None
        self.lastBountyCheck = None
        self.bounty = None
        self.sr.actions = None
        self.sr.updateTimer = None
        self.itemIDs = []
        self.panelname = panelname
        self.lastActionDist = None
        self.sr.noSelectedHint = None
        self.sr.blink = None
        self.UpdateActions()
        self.postorder = ['UI/Inflight/OrbitObject',
         'UI/Inflight/Submenus/KeepAtRange',
         ('UI/Inflight/LockTarget', 'UI/Inflight/UnlockTarget'),
         ('UI/Inflight/LookAtObject', 'UI/Inflight/ResetCamera'),
         'UI/Commands/ShowInfo']
        self.groups = {const.groupStation: ['UI/Inflight/DockInStation'],
         const.groupWreck: ['UI/Commands/OpenCargo'],
         const.groupCargoContainer: ['UI/Commands/OpenCargo'],
         const.groupMissionContainer: ['UI/Commands/OpenCargo'],
         const.groupSecureCargoContainer: ['UI/Commands/OpenCargo'],
         const.groupAuditLogSecureContainer: ['UI/Commands/OpenCargo'],
         const.groupFreightContainer: ['UI/Commands/OpenCargo'],
         const.groupSpawnContainer: ['UI/Commands/OpenCargo'],
         const.groupSpewContainer: ['UI/Commands/OpenCargo'],
         const.groupDeadspaceOverseersBelongings: ['UI/Commands/OpenCargo'],
         const.groupPlanetaryCustomsOffices: ['UI/PI/Common/AccessCustomOffice'],
         const.groupOrbitalConstructionPlatforms: ['UI/DustLink/OpenUpgradeHold'],
         const.groupPlanet: [('UI/PI/Common/ViewInPlanetMode', 'UI/PI/Common/ExitPlanetMode')],
         const.groupReprocessingArray: ['UI/Inflight/POS/AccessPOSRefinery'],
         const.groupCompressionArray: ['UI/Inflight/POS/AccessPOSCompression'],
         const.groupMobileReactor: ['UI/Inflight/POS/AccessPOSStorage'],
         const.groupControlTower: ['UI/Inflight/POS/AccessPOSFuelBay', 'UI/Inflight/POS/AccessPOSStrontiumBay'],
         const.groupSilo: ['UI/Inflight/POS/AccessPOSStorage'],
         const.groupAssemblyArray: ['UI/Inflight/POS/AccessPOSStorage'],
         const.groupMobileLaboratory: ['UI/Inflight/POS/AccessPOSStorage'],
         const.groupCorporateHangarArray: ['UI/Inflight/POS/AccessPOSStorage'],
         const.groupPersonalHangar: ['UI/Inflight/POS/AccessPOSStorage'],
         const.groupMobileMissileSentry: ['UI/Inflight/POS/AccessPOSAmmo'],
         const.groupMobileHybridSentry: ['UI/Inflight/POS/AccessPOSAmmo'],
         const.groupMobileProjectileSentry: ['UI/Inflight/POS/AccessPOSAmmo'],
         const.groupMobileLaserSentry: ['UI/Inflight/POS/AccessPOSCrystalStorage'],
         const.groupShipMaintenanceArray: ['UI/Inflight/POS/AccessPOSVessels'],
         const.groupStargate: ['UI/Inflight/Jump'],
         const.groupWormhole: ['UI/Inflight/EnterWormhole'],
         const.groupWarpGate: ['UI/Inflight/ActivateGate'],
         const.groupBillboard: ['UI/Commands/ReadNews'],
         const.groupAgentsinSpace: ['UI/Chat/StartConversation'],
         const.groupDestructibleAgentsInSpace: ['UI/Chat/StartConversation'],
         const.groupMiningDrone: ['UI/Drones/MineWithDrone',
                                  'UI/Drones/MineRepeatedly',
                                  'UI/Drones/ReturnDroneAndOrbit',
                                  ('UI/Drones/LaunchDrones', 'UI/Drones/ReturnDroneToBay', 'UI/Drones/ScoopDroneToBay')],
         const.groupSalvageDrone: ['UI/Drones/Salvage', 'UI/Drones/ReturnDroneAndOrbit', ('UI/Drones/LaunchDrones', 'UI/Drones/ReturnDroneToBay', 'UI/Drones/ScoopDroneToBay')]}
        self.categories = {const.categoryShip: ['UI/Inflight/BoardShip', 'UI/Chat/StartConversation'],
         const.categoryDrone: ['UI/Drones/EngageTarget', 'UI/Drones/ReturnDroneAndOrbit', ('UI/Drones/LaunchDrones', 'UI/Drones/ReturnDroneToBay', 'UI/Drones/ScoopDroneToBay')]}
        if self.destroyed:
            return
        self.sr.main = main = uiutil.GetChild(self, 'main')
        self.SetTopparentHeight(0)
        self.SetWndIcon()
        self.SetCaption(localization.GetByLabel('UI/Inflight/ActiveItem/SelectedItem'))
        self.SetMinSize([256, 93])
        self.MakeUnKillable()
        main.left = main.top = main.width = main.height = const.defaultPadding
        main.clipChildren = 1
        self.sr.toparea = uiprimitives.Container(name='toparea', align=uiconst.TOTOP, parent=self.sr.main, height=36)
        self.sr.utilMenuArea = uiprimitives.Container(name='utilMenuArea', align=uiconst.TORIGHT, parent=self.sr.toparea, width=20)
        self.utilMenu = uicls.KillRightsUtilMenu(menuAlign=uiconst.TOPRIGHT, parent=self.sr.utilMenuArea, align=uiconst.TOPRIGHT)
        self.sr.utilMenuArea.display = False
        self.sr.actions = uiprimitives.Container(name='actions', align=uiconst.TOTOP, parent=self.sr.main, left=0, top=0)
        self.sr.actions.isTabStop = 1
        self.sr.iconpar = uiprimitives.Container(name='iconpar', align=uiconst.TOPLEFT, parent=self.sr.toparea, width=32, height=32, left=1, top=2, state=uiconst.UI_HIDDEN)
        self.sr.icon = uicontrols.Icon(parent=self.sr.iconpar, align=uiconst.TOALL)
        self.sr.icon.OnClick = (self.ShowInfo, self.sr.icon)
        self.sr.icon.GetMenu = (self.GetIconMenu, self.sr.icon)
        self.sr.chariconpar = uiprimitives.Container(name='chariconpar', align=uiconst.TOPLEFT, parent=self.sr.toparea, width=32, height=32, left=37, top=2, state=uiconst.UI_HIDDEN)
        self.sr.charicon = uicontrols.Icon(parent=self.sr.chariconpar, align=uiconst.TOALL)
        self.sr.charicon.OnClick = (self.ShowInfo, self.sr.charicon)
        self.sr.pushCont = uiprimitives.Container(name='push', width=39, parent=self.sr.toparea, align=uiconst.TOLEFT)
        self.sr.text = uicontrols.EveLabelSmall(text='', parent=self.sr.toparea, align=uiconst.TOTOP, left=const.defaultPadding, top=const.defaultPadding, state=uiconst.UI_NORMAL)
        self.inited = 1
        self.bountySvc = sm.GetService('bountySvc')
        selected = None
        stateSvc = sm.GetServiceIfRunning('state')
        if stateSvc:
            selected = stateSvc.GetExclState(state.selected)
        if selected:
            self.OnMultiSelect([selected])
        else:
            self.UpdateAll()

    def UpdateActions(self):
        self.actions = {'UI/Commands/ShowInfo': ('res:/UI/Texture/icons/44_32_24.png', 0, 0, 0, 0, 'selectedItemShowInfo', 'CmdShowItemInfo'),
         'UI/Inflight/ApproachObject': ('res:/UI/Texture/icons/44_32_23.png', 0, 0, 0, 0, 'selectedItemApproach', 'CmdApproachItem'),
         'UI/Inflight/AlignTo': ('res:/UI/Texture/icons/44_32_59.png', 0, 0, 0, 0, 'selectedItemAlignTo', 'CmdAlignToItem'),
         'UI/Inflight/OrbitObject': ('res:/UI/Texture/icons/44_32_21.png', 0, 0, 1, 0, 'selectedItemOrbit', 'CmdOrbitItem'),
         'UI/Inflight/Submenus/KeepAtRange': ('res:/UI/Texture/icons/44_32_22.png', 0, 0, 1, 0, 'selectedItemKeepAtRange', 'CmdKeepItemAtRange'),
         'UI/Inflight/LockTarget': ('res:/UI/Texture/icons/44_32_17.png', 0, 0, 0, 0, 'selectedItemLockTarget', 'CmdLockTargetItem'),
         'UI/Inflight/UnlockTarget': ('res:/UI/Texture/icons/44_32_17.png', 0, 0, 0, 1, 'selectedItemUnLockTarget', 'CmdUnlockTargetItem'),
         'UI/Inflight/LookAtObject': ('res:/UI/Texture/icons/44_32_20.png', 0, 0, 0, 0, 'selectedItemLookAt', 'CmdToggleLookAtItem'),
         'UI/Inflight/ResetCamera': ('res:/UI/Texture/icons/44_32_20.png', 0, 0, 0, 1, 'selectedItemResetCamera', None),
         'UI/Chat/StartConversation': ('res:/UI/Texture/icons/44_32_33.png', 0, 0, 0, 0, 'selectedItemStartConversation', None),
         'UI/Commands/OpenCargo': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemOpenCargo', None),
         'UI/PI/Common/AccessCustomOffice': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemOpenCargo', None),
         'UI/DustLink/OpenUpgradeHold': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemOpenCargo', None),
         'UI/PI/Common/ViewInPlanetMode': ('res:/UI/Texture/icons/77_32_34.png', 0, 0, 0, 0, 'selectedItemViewInPlanetMode', None),
         'UI/PI/Common/ExitPlanetMode': ('res:/UI/Texture/icons/77_32_35.png', 0, 0, 0, 0, 'selectedItemExitPlanetMode', None),
         'UI/Inflight/POS/AccessPOSRefinery': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessRefinery', None),
         'UI/Inflight/POS/AccessPOSCompression': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessCompression', None),
         'UI/Inflight/POS/AccessPOSStrontiumBay': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessTrontiumStorage', None),
         'UI/Inflight/POS/AccessPOSFuelBay': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessFuelStorage', None),
         'UI/Inflight/POS/AccessPOSAmmo': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessAmmunition', None),
         'UI/Inflight/POS/AccessPOSCrystalStorage': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessCrystalStorage', None),
         'UI/Inflight/POS/AccessPOSStorage': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessStorage', None),
         'UI/Inflight/POS/AccessPOSVessels': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemAccessVessels', None),
         'UI/Commands/AccessBountyEscrow': ('res:/UI/Texture/icons/44_32_35.png', 0, 0, 0, 0, 'selectedItemOpenCargo', None),
         'UI/Drones/EngageTarget': ('res:/UI/Texture/icons/44_32_4.png', 0, 0, 0, 0, 'selectedItemEngageTarget', None),
         'UI/Drones/MineWithDrone': ('res:/UI/Texture/icons/44_32_4.png', 0, 0, 0, 0, 'selectedItemMine', None),
         'UI/Drones/MineRepeatedly': ('res:/UI/Texture/icons/44_32_5.png', 0, 0, 0, 0, 'selectedItemMineRepeatedly', None),
         'UI/Drones/Salvage': ('res:/UI/Texture/icons/44_32_5.png', 0, 0, 0, 0, 'selectedItemSalvage', None),
         'UI/Inflight/POS/AnchorObject': ('res:/UI/Texture/icons/44_32_4.png', 0, 0, 0, 0, 'selectedItemUnanchor', None),
         'UI/Drones/ReturnDroneAndOrbit': ('res:/UI/Texture/icons/44_32_3.png', 0, 0, 0, 0, 'selectedItemReturnAndOrbit', None),
         'UI/Drones/ReturnDroneToBay': ('res:/UI/Texture/icons/44_32_1.png', 0, 0, 0, 0, 'selectedItemReturnToDroneBay', None),
         'UI/Drones/ScoopDroneToBay': ('res:/UI/Texture/icons/44_32_1.png', 0, 0, 0, 0, 'selectedItemScoopToDroneBay', None),
         'UI/Drones/LaunchDrones': ('res:/UI/Texture/icons/44_32_2.png', 0, 0, 0, 0, 'selectedItemLaunchDrones', None),
         'UI/Inflight/BoardShip': ('res:/UI/Texture/icons/44_32_40.png', 0, 0, 0, 0, 'selectedItemBoardShip', None),
         'UI/Inflight/DockInStation': ('res:/UI/Texture/icons/44_32_9.png', 0, 0, 0, 0, 'selectedItemDock', 'CmdDockOrJumpOrActivateGate'),
         'UI/Inflight/Jump': ('res:/UI/Texture/icons/44_32_39.png', 0, 0, 0, 0, 'selectedItemJump', 'CmdDockOrJumpOrActivateGate'),
         'UI/Inflight/EnterWormhole': ('res:/UI/Texture/icons/44_32_39.png', 0, 0, 0, 0, 'selectedItemEnterWormhole', None),
         'UI/Inflight/ActivateGate': ('res:/UI/Texture/icons/44_32_39.png', 0, 0, 0, 0, 'selectedItemActivateGate', 'CmdDockOrJumpOrActivateGate'),
         'UI/Commands/ReadNews': ('res:/UI/Texture/icons/44_32_47.png', 0, 0, 0, 0, 'selectedItemReadNews', None)}

    def Blink(self, on_off = 1):
        if on_off and self.sr.blink is None:
            self.sr.blink = uiprimitives.Fill(parent=self.sr.top, padding=(1, 1, 1, 1), color=(1.0, 1.0, 1.0, 0.25))
        if on_off:
            sm.GetService('ui').BlinkSpriteA(self.sr.blink, 0.25, 500, None, passColor=0)
        elif self.sr.blink:
            sm.GetService('ui').StopBlink(self.sr.blink)
            b = self.sr.blink
            self.sr.blink = None
            b.Close()

    def BlinkBtn(self, key):
        for btn in self.sr.actions.children:
            if btn.name.replace(' ', '').lower() == key.replace(' ', '').lower():
                sm.GetService('ui').BlinkSpriteA(btn.children[0], 1.0, 500, None, passColor=0)
            else:
                sm.GetService('ui').StopBlink(btn.children[0])

    def OnResizeUpdate(self, *args):
        self.CheckActions(forceSizeUpdate=1, ignoreScaling=1)

    def OnActiveTrackingChange(self, isActivelyTracking):
        self.AdjustUIToActiveTrackingStatus(isActivelyTracking)

    def AdjustUIToActiveTrackingStatus(self, isTracking):
        caption = localization.GetByLabel('UI/Inflight/ActiveItem/SelectedItem')
        if isTracking:
            caption += ' - ' + localization.GetByLabel('UI/Inflight/ActiveItem/Tracking')
        self.SetCaption(caption)

    @telemetry.ZONE_METHOD
    def CheckActions(self, forceSizeUpdate = 0, ignoreScaling = 0):
        if self.destroyed or not self.sr.actions:
            return
        self.sr.toparea.height = max(40, self.sr.text.textheight + self.sr.text.top * 2)
        scaling = getattr(self, 'scaling', 0) if ignoreScaling == 0 else 0
        if forceSizeUpdate and not scaling and self.ImVisible():
            l, t, w, h = self.GetAbsolute()
            al, at, aw, ah = self.sr.actions.GetAbsolute()
            maxHeight = t + h - at - 8
            self.LayoutButtons(self.sr.actions, uiconst.UI_PICKCHILDREN, maxHeight)
            gl, gt, gr, gb = self.GetGroupRect(self.sr.actions.children)
            diff = gb - (t + h - 6)
            if diff > 0:
                self.SetHeight_PushOrPullWindowsBelow(self.height + diff)

    @telemetry.ZONE_METHOD
    def LayoutButtons(self, parent, state = None, maxHeight = None):
        if parent is None:
            return
        l, t, w, h = parent.GetAbsolute()
        colwidth = 33
        if w <= colwidth:
            return
        perRow = w / colwidth
        small = len(parent.children) / float(perRow) > 2.0
        size = [32, 24][small]
        if maxHeight and size > maxHeight:
            size = 24
        if len(parent.children) * (size + 1) + 1 > w:
            size = 24
        left = 1
        top = 0
        parent.height = size + 1
        for icon in parent.children:
            if l + left + size + 1 >= l + w:
                left = 1
                top += size + 1
                parent.height += size + 1
            icon.left = left
            icon.top = top
            icon.width = size
            icon.height = size
            if state is not None:
                icon.state = state
            left += size + 1

    def _OnClose(self, *args):
        self.sr.updateTimer = None

    def ProcessSessionChange(self, isRemote, session, change):
        self.lastActionSerial = None
        self.lastActionDist = None
        self.lastSessionChange = blue.os.GetWallclockTime()

    def OnMultiSelect(self, itemIDs):
        self.itemIDs = itemIDs
        self.lastActionSerial = None
        self.lastActionDist = None
        self.lastBountyCheck = None
        self.bounty = None
        if self.ImVisible():
            uthread.pool('ActiveItem::UpdateAll', self.UpdateAll, 1)

    def OnStateChange(self, itemID, flag, true, *args):
        if itemID != eve.session.shipid and not self.destroyed:
            uthread.new(self._OnStateChange, itemID, flag, true)

    @telemetry.ZONE_METHOD
    def _OnStateChange(self, itemID, flag, true):
        if flag == state.selected and true:
            self.OnMultiSelect([itemID])
        if itemID in self.itemIDs and flag not in (state.selected, state.mouseOver):
            self.lastActionSerial = None
            self.lastActionDist = None
            self.UpdateAll()

    def OnDistSettingsChange(self):
        uthread.new(self._OnDistSettingsChange)

    @telemetry.ZONE_METHOD
    def _OnDistSettingsChange(self):
        self.lastActionSerial = None
        self.UpdateAll(1)

    def TryGetInvItem(self, itemID):
        if eve.session.shipid is None:
            return
        ship = sm.GetService('invCache').GetInventoryFromId(eve.session.shipid)
        if ship:
            for invItem in ship.List():
                if invItem.itemID == itemID:
                    return invItem

    def GetItem(self, itemID):
        item = uix.GetBallparkRecord(itemID)
        if not item:
            item = self.TryGetInvItem(itemID)
        return item

    def Load(self, itemID):
        pass

    def OnTabSelect(self, *args):
        if not getattr(self, 'inited', 0):
            return
        self.lastActionSerial = None
        self.UpdateAll(1)

    def OnExpanded(self, *args):
        if not getattr(self, 'inited', 0):
            return
        self.lastActionSerial = None
        self.UpdateAll(1)

    def OnEndMaximize(self):
        if not getattr(self, 'inited', 0):
            return
        self.lastActionSerial = None
        self.UpdateAll(1)

    def ShowNoSelectedHint(self, hint = None):
        if self.sr.noSelectedHint is None and hint:
            self.sr.noSelectedHint = uicontrols.EveCaptionMedium(text=hint, parent=self.sr.main, align=uiconst.RELATIVE, left=16, top=18, width=256)
            self.sr.noSelectedHint.SetAlpha(0.5)
        elif self.sr.noSelectedHint:
            if hint:
                self.sr.noSelectedHint.text = hint
                self.sr.noSelectedHint.state = uiconst.UI_DISABLED
            else:
                self.sr.noSelectedHint.state = uiconst.UI_HIDDEN

    def FlushContent(self):
        self.SetText('')
        self.ShowNoSelectedHint(localization.GetByLabel('UI/Inflight/ActiveItem/NoObjectSelected'))
        self.sr.actions.Flush()
        self.sr.iconpar.state = uiconst.UI_HIDDEN
        self.sr.chariconpar.state = uiconst.UI_HIDDEN

    @telemetry.ZONE_METHOD
    def UpdateAll(self, updateActions = 0):
        if not self or self.destroyed:
            return
        if eve.session.shipid in self.itemIDs:
            self.itemIDs.remove(eve.session.shipid)
        bp = sm.GetService('michelle').GetBallpark()
        if not self.ImVisible() or not bp or not self.itemIDs:
            self.sr.updateTimer = None
            self.FlushContent()
            return
        goForSlim = 1
        slimItems = []
        invItems = []
        fleetMember = None
        for itemID in self.itemIDs:
            blue.pyos.BeNice()
            if sm.GetService('fleet').IsMember(itemID):
                fleetMember = cfg.eveowners.Get(itemID)
                break
            slimItem = None
            if goForSlim:
                slimItem = uix.GetBallparkRecord(itemID)
                if slimItem:
                    slimItems.append(slimItem)
            if not slimItem:
                invItem = self.TryGetInvItem(itemID)
                if invItem:
                    invItems.append(invItem)
                    goForSlim = 0

        if not slimItems and not invItems and not fleetMember:
            self.itemIDs = []
            self.lastActionSerial = None
            self.lastActionDist = None
            self.FlushContent()
            return
        if not self or self.destroyed:
            return
        text = ''
        blue.pyos.BeNice()
        updateActions = updateActions or 0
        typeID = None
        groupID = None
        fleetSlim = None
        if fleetMember:
            multi = 1
            text = fleetMember.name
            typeID = fleetMember.typeID
            typeOb = cfg.invtypes.Get(typeID)
            groupID = typeOb.groupID
            categoryID = typeOb.categoryID
            fleetSlim = self.GetSlimItemForCharID(fleetMember.id)
            blue.pyos.BeNice()
        elif invItems:
            text = uix.GetItemName(invItems[0])
            typeID = invItems[0].typeID
            typeOb = cfg.invtypes.Get(typeID)
            groupID = typeOb.groupID
            categoryID = typeOb.categoryID
            multi = len(invItems)
            blue.pyos.BeNice()
        elif slimItems:
            text = uix.GetSlimItemName(slimItems[0])
            typeID = slimItems[0].typeID
            groupID = slimItems[0].groupID
            categoryID = slimItems[0].categoryID
            multi = len(slimItems)
            if multi == 1:
                slimItem = slimItems[0]
                itemID = slimItem.itemID
                ball = bp.GetBall(itemID)
                if not ball:
                    self.itemIDs = []
                    self.sr.updateTimer = None
                    self.FlushContent()
                    return
                dist = ball.surfaceDist
                if dist is not None:
                    md = None
                    myball = bp.GetBall(eve.session.shipid)
                    if myball:
                        md = myball.mode
                    text += '<br>' + localization.GetByLabel('UI/Inflight/ActiveItem/SelectedItemDistance', distToItem=util.FmtDist(dist, maxdemicals=1))
                    if not self.lastActionDist or md != self.lastActionDist[1] or self.CheckDistanceUpdate(self.lastActionDist[0], dist):
                        self.lastActionDist = (dist, md)
                        updateActions = 1
                sec = slimItem.securityStatus
                if sec:
                    text += '<br>' + localization.GetByLabel('UI/Inflight/ActiveItem/SelectedItemSecurity', secStatus=sec)
            blue.pyos.BeNice()
        corpID = None
        charID = None
        categoryID = None
        bountyItemID = None
        bountyTypeID = None
        bountySlim = None
        displayUtilMenu = False
        if multi > 1:
            text += '<br>' + localization.GetByLabel('UI/Inflight/ActiveItem/MultipleItems', itemCount=multi)
            blue.pyos.BeNice()
        elif multi == 1:
            if slimItems:
                slim = slimItems[0]
                if slim.categoryID == const.categoryShip:
                    if util.IsCharacter(slim.charID):
                        charID = slim.charID
                        categoryID = slim.categoryID
                if slim.categoryID == const.categoryEntity:
                    bountyTypeID = slim.typeID
                elif slim.charID:
                    bountyItemID = slim.charID
                    bountySlim = slim
                killRightID, price = self.bountySvc.GetBestKillRight(slim.charID)
                self.utilMenu.UpdateKillRightInfo(killRightID, price, slim.charID, slim.itemID)
                stateSvc = sm.GetService('state')
                if killRightID is not None and not (stateSvc.CheckSuspect(slim) or stateSvc.CheckCriminal(slim)):
                    displayUtilMenu = True
            blue.pyos.BeNice()
        self.sr.utilMenuArea.display = displayUtilMenu
        self.utilMenu.display = displayUtilMenu
        if self.lastIcon != (typeID, itemID, charID):
            uthread.pool('ActiveItem::GetIcon', self.GetIcon, typeID, itemID, charID, corpID, categoryID)
            self.lastIcon = (typeID, itemID, charID)
        else:
            self.sr.iconpar.state = uiconst.UI_PICKCHILDREN
            if categoryID == const.categoryShip and charID:
                self.sr.chariconpar.state = uiconst.UI_PICKCHILDREN
        bountyHint = None
        reducedBountyIndication = None
        if (bountyItemID, bountyTypeID) != self.lastBountyCheck:
            bounty, bountyHint, reducedBountyIndication = self.CheckBounty(bountyTypeID, bountySlim)
            blue.pyos.BeNice()
            if bounty:
                self.bounty = localization.GetByLabel('UI/Common/BountyAmount', bountyAmount=util.FmtISK(bounty, 0))
            else:
                self.bounty = None
            self.lastBountyCheck = (bountyItemID, bountyTypeID)
            self.lastBountyInfo = (bountyHint, reducedBountyIndication)
        else:
            bountyHint, reducedBountyIndication = self.lastBountyInfo
        if self.bounty:
            text += '<br>'
            text += self.bounty
        if reducedBountyIndication:
            text += reducedBountyIndication
        if updateActions:
            self.ReloadActions(slimItems, invItems, fleetMember, fleetSlim)
        else:
            self.CheckActions(1)
        self.SetText(text, bountyHint)
        self.ShowNoSelectedHint()
        blue.pyos.BeNice()
        self.laseUpdateWidth = self.absoluteRight - self.absoluteLeft
        if not self.sr.updateTimer and not invItems:
            self.sr.updateTimer = base.AutoTimer(500, self.UpdateAll)

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if self.ImVisible() and ball and ball.id in self.itemIDs:
            uthread.pool('ActiveItem::UpdateAll', self.UpdateAll, 1)

    def SetText(self, text, hint = None):
        if text != self.sr.text.text:
            self.sr.text.text = text
            self.sr.text.hint = hint
            self.CheckActions(1)

    def GetIcon(self, typeID, itemID, charID, corpID, categoryID):
        self.sr.icon.LoadIconByTypeID(typeID, itemID=itemID, ignoreSize=True)
        self.sr.icon.typeID = typeID
        self.sr.icon.itemID = itemID
        self.sr.iconpar.state = uiconst.UI_PICKCHILDREN
        self.sr.chariconpar.state = uiconst.UI_HIDDEN
        self.sr.pushCont.width = 39
        if categoryID == const.categoryShip and charID:
            typeID = cfg.eveowners.Get(charID).typeID
            self.sr.charicon.LoadIconByTypeID(typeID, itemID=charID, ignoreSize=True)
            self.sr.charicon.typeID = typeID
            self.sr.charicon.itemID = charID
            self.sr.pushCont.width = 75
            self.sr.chariconpar.state = uiconst.UI_PICKCHILDREN

    def CheckBounty(self, bountyTypeID, slimItem):
        bounty = None
        bountyHint = None
        reducedBountyIndication = None
        if bountyTypeID:
            tmp = [ each for each in sm.GetService('godma').GetType(bountyTypeID).displayAttributes if each.attributeID == const.attributeEntityKillBounty ]
            if tmp:
                bounty, bountyHint, reducedBountyIndication = self.GetNpcBounty(tmp[0].value)
        elif slimItem:
            if self.bountySvc.CanHaveBounty(slimItem):
                bounty = self.bountySvc.GetBounty(slimItem.charID, slimItem.corpID, slimItem.allianceID)
        return (bounty, bountyHint, reducedBountyIndication)

    def GetNpcBounty(self, bountyAmount):
        ballpark = sm.GetService('michelle').GetBallpark()
        reducedBounty, takenBounty = GetBountyReductionForSolarSystem(ballpark, bountyAmount)
        if reducedBounty:
            bountyHint = localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/ReducedBountyHint', takenBounty=takenBounty)
            reducedBountyIndication = localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/ReducedBountyIndication')
            return (reducedBounty, bountyHint, reducedBountyIndication)
        return (bountyAmount, None, None)

    def GetSlimItemForCharID(self, charID):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark:
            for itemID, rec in ballpark.slimItems.iteritems():
                if rec.charID == charID:
                    return rec

    def ShowInfo(self, btn, *args):
        if btn and btn.typeID:
            sm.GetService('info').ShowInfo(btn.typeID, btn.itemID)

    def GetIconMenu(self, btn, *args):
        if btn and btn.typeID:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(btn, 'itemID', None), btn.typeID)

    def CheckDistanceUpdate(self, lastdist, dist):
        diff = abs(lastdist - dist)
        if not diff:
            return False
        elif dist:
            return bool(diff / dist > 0.01)
        else:
            return bool(lastdist != dist)

    def ImVisible(self):
        return bool(not self.IsCollapsed() and not self.IsMinimized())

    @telemetry.ZONE_METHOD
    def ReloadActions(self, slimItems, invItems, fleetMember, fleetSlim):
        if not self or self.destroyed:
            return
        if not self.ImVisible():
            self.sr.updateTimer = None
            return
        itemIDs = []
        actions = []
        if invItems:
            data = [ (invItem, 0, None) for invItem in invItems ]
            actions = sm.StartService('menu').InvItemMenu(data)
        elif slimItems:
            celestialData = []
            for slimItem in slimItems:
                celestialData.append((slimItem.itemID,
                 None,
                 slimItem,
                 0,
                 None,
                 None,
                 None))

            if len(celestialData) > 1:
                actions = sm.StartService('menu').CelestialMenu(itemID=celestialData)
            else:
                actions = sm.StartService('menu').GetCelestialMenuForSelectedItem(celestialData)
        elif fleetSlim:
            actions = sm.GetService('menu').CelestialMenu(fleetSlim.itemID, slimItem=fleetSlim, ignoreTypeCheck=1)
        elif fleetMember:
            actions = sm.GetService('menu').CharacterMenu(fleetMember.id)
        reasonsWhyNotAvailable = getattr(actions, 'reasonsWhyNotAvailable', {})
        warptoLabel = DefaultWarpToLabel()[0]
        warpops = {warptoLabel: ('res:/UI/Texture/icons/44_32_18.png', 0, 0, 1, 0, 'selectedItemWarpTo', 'CmdWarpToItem')}
        if not self or self.destroyed:
            return
        self.actions.update(warpops)
        serial = ''
        valid = {}
        for each in actions:
            if each:
                if isinstance(each[0], tuple):
                    name = each[0][0]
                else:
                    name = each[0]
                if each[1] == DISABLED_ENTRY0:
                    continue
                if name in self.actions:
                    valid[name] = each
                    if type(each[1]) not in (str, unicode):
                        serial += '%s_' % name

        blue.pyos.BeNice()
        ph = None
        if serial != self.lastActionSerial:
            if self.absoluteLeft == 0:
                blue.pyos.synchro.Yield()
            if self.destroyed:
                return
            self.sr.actions.Flush()
            self.sr.actions.height = 0
            typeID = None
            groupID = None
            categoryID = None
            if slimItems:
                typeID = slimItems[0].typeID
                groupID = slimItems[0].groupID
                categoryID = slimItems[0].categoryID
            elif invItems:
                typeID = invItems[0].typeID
                groupID = invItems[0].groupID
                categoryID = invItems[0].categoryID
            isAlignDisabled = type(valid.get('UI/Inflight/AlignTo', ('', ''))[1]) in (str, unicode)
            if isAlignDisabled:
                approachLabelPath = 'UI/Inflight/ApproachObject'
            else:
                approachLabelPath = 'UI/Inflight/AlignTo'
            order = [approachLabelPath, warptoLabel]
            if groupID and groupID in self.groups:
                order += self.groups[groupID]
            elif categoryID and categoryID in self.categories:
                order += self.categories[categoryID]
            item = self.ChooseItem(slimItems, invItems)
            if item:
                if HasCargoBayComponent(typeID):
                    if cargobay.IsAccessibleByCharacter(item, session.charid, cfg.spaceComponentStaticData):
                        order.append('UI/Commands/OpenCargo')
                if HasBountyEscrowComponent(typeID):
                    order.append('UI/Commands/AccessBountyEscrow')
            order = itertoolsext.remove_duplicates_and_preserve_order(order)
            order += self.postorder
            for actionName in order:
                if actionName is None:
                    continue
                if isinstance(actionName, tuple):
                    action = None
                    for each in actionName:
                        tryaction = valid.get(each, None)
                        if tryaction and type(tryaction[1]) not in (str, unicode):
                            actionName = each
                            action = tryaction
                            break

                    if action is None:
                        actionName = actionName[0]
                        if actionName in valid:
                            action = valid.get(actionName)
                        elif actionName in reasonsWhyNotAvailable:
                            action = (actionName, reasonsWhyNotAvailable.get(actionName))
                        else:
                            action = (actionName, localization.GetByLabel('UI/Menusvc/MenuHints/NoReasonGiven'))
                elif actionName in valid:
                    action = valid.get(actionName)
                elif actionName in reasonsWhyNotAvailable:
                    action = (actionName, reasonsWhyNotAvailable.get(actionName))
                else:
                    action = (actionName, localization.GetByLabel('UI/Menusvc/MenuHints/NoReasonGiven'))
                disabled = type(action[1]) in (str, unicode)
                if isinstance(action[0], uiutil.MenuLabel):
                    actionID = action[0][0]
                else:
                    actionID = action[0]
                par = uiprimitives.Container(parent=self.sr.actions, align=uiconst.TOPLEFT, width=32, height=32, state=uiconst.UI_HIDDEN)
                props = self.actions[actionID]
                if len(props) >= 6:
                    par.name = props[5]
                else:
                    par.name = actionID
                if len(props) >= 7:
                    cmdName = props[6]
                else:
                    cmdName = ''
                import xtriui
                icon = xtriui.Action(icon=props[0], parent=par, align=uiconst.TOALL, disabled=disabled)
                icon.actionID = actionID
                icon.action = action
                icon.itemIDs = self.itemIDs[:]
                icon.killsub = props[3]
                icon.cmdName = cmdName
                if disabled:
                    icon.opacity = 0.5
                if ph and props[2]:
                    uiprimitives.Fill(parent=par, align=uiconst.RELATIVE, height=ph, width=30, left=1, top=31 - ph)
                    icon.OnClick = None
                if props[4]:
                    x = uicontrols.Icon(icon='ui_44_32_8', parent=par, left=1, top=1, align=uiconst.TOALL, state=uiconst.UI_DISABLED, idx=0)

            self.lastActionSerial = serial
        self.CheckActions(1)

    def ChooseItem(self, slimItems, invItems):
        if slimItems:
            return slimItems[0]
        if invItems:
            return invItems[0]

    def OnPlanetViewChanged(self, newPlanetID, oldPlanetID):
        """Called by planet view change"""
        for planetID in (newPlanetID, oldPlanetID):
            if planetID in self.itemIDs:
                self.OnMultiSelect(self.itemIDs)
