#Embedded file name: eve/client/script/ui/shared/fleet\fleetwindow.py
import uiprimitives
import uicontrols
import uix
import carbonui.const as uiconst
import uiutil
from eve.client.script.ui.shared.fleet.fleet import FleetAction
from eve.client.script.ui.shared.fleet.fleet import FleetView
from eve.client.script.ui.shared.fleet.fleetbroadcast import FleetBroadcastView
from eve.client.script.ui.shared.fleet.fleetfinder import FleetFinderWindow
from eve.client.script.ui.shared.fleet.fleetbroadcast import BroadcastSettings
import blue
import util
from eve.client.script.ui.control import entries as listentry
import uthread
import fleetbr
import fleetcommon
import localization
from eve.client.script.ui.shared.fleet.storeFleetSetupWnd import StoredFleetSetupListWnd
BROADCAST_HEIGHT = 46

class FleetWindow(uicontrols.Window):
    __guid__ = 'form.FleetWindow'
    __notifyevents__ = ['OnFleetBroadcast_Local', 'OnSpeakingEvent_Local', 'OnBroadcastScopeChange']
    default_width = 400
    default_height = 300
    default_windowID = 'fleetwindow'
    default_captionLabelPath = 'Tooltips/Neocom/Fleet'
    default_descriptionLabelPath = 'Tooltips/Neocom/Fleet_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/fleet.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        tabIdx = attributes.tabIdx
        self.isFlat = settings.user.ui.Get('flatFleetView', False)
        self.scope = 'all'
        self.broadcastMenuItems = []
        self.SetTopparentHeight(0)
        self.SetHeaderIcon()
        hicon = self.sr.headerIcon
        hicon.GetMenu = self.GetFleetMenuTop
        hicon.expandOnLeft = 1
        hicon.hint = localization.GetByLabel('UI/Fleet/FleetWindow/FleetMenuHint')
        currentryActiveColumn = settings.user.ui.Get('activeSortColumns', {})
        self.sr.main = uiutil.GetChild(self, 'main')
        self.InitBroadcastBottom()
        myFleetParent = uiprimitives.Container(name='myfleet', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        uiprimitives.Container(name='push', parent=myFleetParent, width=const.defaultPadding, align=uiconst.TOLEFT)
        uiprimitives.Container(name='push', parent=myFleetParent, width=const.defaultPadding, align=uiconst.TORIGHT)
        self.sr.myFleetContent = FleetView(parent=myFleetParent, name='fleetfinderpar', pos=(0, 0, 0, 0))
        broadcastsParent = uiprimitives.Container(name='broadcasts', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.broadcastsContent = FleetBroadcastView(parent=broadcastsParent, name='fleetfinderpar', pos=(0, 0, 0, 0))
        fleetFinderParent = uiprimitives.Container(name='fleetfinder', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.fleetFinderContent = FleetFinderWindow(parent=fleetFinderParent, name='fleetfinderpar', pos=(0, 0, 0, 0))
        settingsParent = uiprimitives.Container(name='settings', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.startPage = uiprimitives.Container(name='startpage', parent=self.sr.main, align=uiconst.TOALL, state=uiconst.UI_HIDDEN)
        myFleetParent.children.append(self.startPage)
        self.sr.tabs = uicontrols.TabGroup(name='fleettabs', parent=self.sr.main, idx=0)
        tabs = []
        inFleetTabs = [[localization.GetByLabel('UI/Fleet/FleetWindow/MyFleet'),
          myFleetParent,
          self,
          'myfleet'], [localization.GetByLabel('UI/Fleet/FleetWindow/FleetHistory'),
          broadcastsParent,
          self,
          'broadcasts']]
        fleetFinderTabs = [[localization.GetByLabel('UI/Fleet/FleetWindow/FleetFinder'),
          fleetFinderParent,
          self,
          'fleetfinder']]
        if session.fleetid is not None:
            tabs.extend(inFleetTabs)
        tabs.extend(fleetFinderTabs)
        self.sr.tabs.Startup(tabs, 'fleettabs', autoselecttab=1)
        if session.fleetid is not None:
            myFleetTab = self.sr.tabs.GetTabs()[0]
            myFleetTab.OnTabDropData = self.OnDropInMyFleet
        if session.fleetid:
            tabToOpen = localization.GetByLabel('UI/Fleet/FleetWindow/MyFleet')
        else:
            tabToOpen = localization.GetByLabel('UI/Fleet/FleetWindow/FleetFinder')
        uthread.new(self.sr.tabs.ShowPanelByName, tabToOpen)
        if settings.user.ui.Get('fleetFinderBroadcastsVisible', False) and session.fleetid:
            self.ToggleBroadcasts()

    def _OnClose(self, *args):
        pass

    def ToggleBroadcasts(self, *args):
        if self.sr.broadcastBottom.state != uiconst.UI_HIDDEN:
            self.sr.broadcastBottom.state = uiconst.UI_HIDDEN
            self.sr.broadcastExpanderIcon.texturePath = 'res:/UI/Texture/Shared/expanderUp.png'
            settings.user.ui.Set('fleetFinderBroadcastsVisible', False)
        else:
            self.sr.broadcastBottom.state = uiconst.UI_PICKCHILDREN
            self.sr.broadcastExpanderIcon.texturePath = 'res:/UI/Texture/Shared/expanderDown.png'
            settings.user.ui.Set('fleetFinderBroadcastsVisible', True)
        self.UpdateMinSize()

    def InitBroadcastBottom(self):
        self.sr.broadcastBottom = uiprimitives.Container(name='broadcastBottom', parent=self.sr.main, align=uiconst.TOBOTTOM, height=BROADCAST_HEIGHT, state=uiconst.UI_HIDDEN)
        broadcastHeaderParent = uiprimitives.Container(name='lastbroadcastheader', parent=self.sr.main, align=uiconst.TOBOTTOM, state=uiconst.UI_NORMAL, height=24)
        broadcastHeaderParent.padBottom = 3
        expanderCont = uiprimitives.Container(name='expanderCont', parent=broadcastHeaderParent, align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, width=18)
        expanderCont.OnClick = self.ToggleBroadcasts
        broadcastHeaderParent.height = uix.GetTextHeight('Xg')
        self.sr.broadcastHeaderParent = broadcastHeaderParent
        expander = uiprimitives.Sprite(parent=expanderCont, pos=(5, 0, 11, 11), name='expandericon', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/expanderUp.png', align=uiconst.TOPRIGHT)
        self.sr.broadcastExpanderIcon = expander
        uix.Flush(self.sr.broadcastBottom)
        self.sr.lastBroadcastCont = uiprimitives.Container(name='lastBroadcastCont', parent=broadcastHeaderParent, align=uiconst.TOALL, pos=(0, 0, 0, 0), state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Fleet/FleetBroadcast/NoBroadcasts'), parent=self.sr.lastBroadcastCont, left=6, top=1, width=500, state=uiconst.UI_NORMAL)
        self.sr.lastVoiceEventCont = uiprimitives.Container(name='lastVoiceEventCont', parent=self.sr.broadcastBottom, align=uiconst.TOTOP_PROP, top=0, left=0, height=1.0, width=1.0, state=uiconst.UI_PICKCHILDREN)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Fleet/FleetBroadcast/NoVoiceBroadcasts'), parent=self.sr.lastVoiceEventCont, left=6, top=0, width=500)
        self.sr.actionsCont = uiprimitives.Container(name='actionsCont', parent=self.sr.broadcastBottom, align=uiconst.TOBOTTOM, height=26, state=uiconst.UI_NORMAL)
        self.sr.toggleCont = uiprimitives.Container(name='toggleCont', parent=self.sr.actionsCont, align=uiconst.TOBOTTOM, height=26, state=uiconst.UI_PICKCHILDREN)
        self.sr.line = uiprimitives.Container(name='lineparent', align=uiconst.TOTOP, parent=self.sr.actionsCont, idx=0, height=1)
        uiprimitives.Line(parent=self.sr.line, align=uiconst.TOALL)
        self.InitActions()

    def GetLastBroadcastMenu(self, broadcast):
        m = []
        func = getattr(fleetbr, 'GetMenu_%s' % broadcast.name, None)
        if func:
            m = func(broadcast.charID, broadcast.solarSystemID, broadcast.itemID)
            m += [None]
        m += fleetbr.GetMenu_Member(broadcast.charID)
        m += [None]
        m += fleetbr.GetMenu_Ignore(broadcast.name)
        return m

    def GetLastVoiceEventMenu(self, broadcast):
        m = []
        func = getattr(fleetbr, 'GetMenu_%s' % broadcast.name, None)
        if func:
            m = func(broadcast.charID, broadcast.solarSystemID, broadcast.itemID)
            m += [None]
        m += fleetbr.GetMenu_Member(broadcast.charID)
        return m

    def UpdateMinSize(self):
        args = self.sr.tabs.GetSelectedArgs()
        if not args:
            return
        if args == 'fleetfinder':
            self.sr.broadcastBottom.state = uiconst.UI_HIDDEN
        elif settings.user.ui.Get('fleetFinderBroadcastsVisible', False) and session.fleetid:
            self.sr.broadcastBottom.state = uiconst.UI_NORMAL
        s = [uiconst.UI_NORMAL, uiconst.UI_HIDDEN][not session.fleetid or args == 'fleetfinder']
        self.sr.broadcastHeaderParent.state = s
        minHeight = 220
        minWidth = 256
        if session.fleetid:
            minHeight = 120
        if self.sr.broadcastBottom.state != uiconst.UI_HIDDEN:
            minHeight += BROADCAST_HEIGHT
        self.SetMinSize([minWidth, minHeight])

    def Load(self, args):
        wnd = self
        if wnd is None or wnd.destroyed:
            return
        if args == 'myfleet':
            self.sr.myFleetContent.state = uiconst.UI_NORMAL
            self.sr.myFleetContent.Load(args)
        elif args == 'broadcasts':
            self.broadcastsContent.Load('option1')
        elif args == 'fleetfinder':
            self.fleetFinderContent.Load(args)
        self.UpdateMinSize()

    def GotoTab(self, idx):
        self.sr.tabs.SelectByIdx(idx)

    def GetFleetMenuTop(self):
        fleetSvc = sm.GetService('fleet')
        if session.fleetid is None:
            ret = [(uiutil.MenuLabel('UI/Fleet/FleetWindow/FormFleet'), lambda : sm.GetService('menu').InviteToFleet(eve.session.charid))]
            ret.append(None)
        else:
            ret = [(uiutil.MenuLabel('UI/Fleet/LeaveMyFleet'), fleetSvc.LeaveFleet)]
            ret.append(None)
            takesFleetWarp = fleetSvc.TakesFleetWarp()
            if takesFleetWarp:
                ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/ExemptFleetWarp'), fleetSvc.SetIgnoreFleetWarp))
            else:
                ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/AcceptFleetWarp'), fleetSvc.SetTakeFleetWarp))
            if session.fleetrole in [const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr]:
                ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/Regroup'), lambda : fleetSvc.Regroup()))
            if fleetSvc.HasActiveBeacon(session.charid):
                ret.append((uiutil.MenuLabel('UI/Fleet/BroadcastJumpBeacon'), lambda : fleetSvc.SendBroadcast_JumpBeacon()))
            if fleetSvc.IsBoss():
                options = fleetSvc.GetOptions()
                ret.append(([uiutil.MenuLabel('UI/Fleet/FleetWindow/SetFreeMove'), localization.GetByLabel('UI/Fleet/FleetWindow/UnsetFreeMove')][options.isFreeMove], lambda : fleetSvc.SetOptions(isFreeMove=not options.isFreeMove)))
                ret.append(([uiutil.MenuLabel('UI/Fleet/FleetWindow/SetVoiceEnabled'), localization.GetByLabel('UI/Fleet/FleetWindow/UnsetVoiceEnabled')][options.isVoiceEnabled], lambda : fleetSvc.SetOptions(isVoiceEnabled=not options.isVoiceEnabled)))
            ret.append(None)
            ret.extend([None, [uiutil.MenuLabel('UI/Fleet/FleetWindow/Broadcasts'), self.broadcastMenuItems]])
            ret.append((uiutil.MenuLabel('UI/Fleet/FleetBroadcast/BroadcastSettings'), lambda : BroadcastSettings.Open()))
            if self.isFlat:
                hierarchyText = uiutil.MenuLabel('UI/Fleet/FleetWindow/ViewAsHierarchy')
            else:
                hierarchyText = uiutil.MenuLabel('UI/Fleet/FleetWindow/ViewAsFlatList')
            ret.append((hierarchyText, self.ToggleFlat))
            ret.extend([None, [uiutil.MenuLabel('UI/Fleet/FleetWindow/ExportLootHistory'), self.ExportLootHistory]])
            ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/StoreFleetSetup'), fleetSvc.StoreSetup))
            if fleetSvc.IsCommanderOrBoss():
                ret.append(None)
                if fleetSvc.GetSetups():
                    ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/FleetSetups'), ('isDynamic', self.GetFleetSetups, ())))
                ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/ShowFleetComposition'), fleetSvc.OpenFleetCompositionWindow))
            if fleetSvc.IsBoss():
                ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/OpenJoinRequest'), fleetSvc.OpenJoinRequestWindow))
                if fleetSvc.options.isRegistered:
                    ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/EditAdvert'), sm.GetService('fleet').OpenRegisterFleetWindow))
                    ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/RemoveAdvert'), sm.GetService('fleet').UnregisterFleet))
                else:
                    ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/CreateAdvert'), sm.GetService('fleet').OpenRegisterFleetWindow))
        return ret

    def GetFleetSetups(self):
        fleetSvc = sm.GetService('fleet')
        setups = fleetSvc.GetSetups()
        if setups:
            setups.append(None)
            setups.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/SetupsOverview'), self.OpenStoredFleetSetupListWnd, ()))
        return setups

    def OpenStoredFleetSetupListWnd(self):
        fleetSvc = sm.GetService('fleet')
        StoredFleetSetupListWnd.Open(fleetSvc=fleetSvc)

    def ToggleFlat(self):
        self.isFlat = not self.isFlat
        settings.user.ui.Set('flatFleetView', self.isFlat)
        self.sr.myFleetContent.isFlat = self.isFlat
        self.sr.myFleetContent.HandleFleetChanged()

    def UpdateHeader(self):
        if self and not self.destroyed:
            self.sr.node = self.sr.myFleetContent.GetHeaderData('fleet', session.fleetid, 0)
            nMembers = len(self.sr.myFleetContent.members)
            info = sm.GetService('fleet').GetMemberInfo(session.charid)
            if info is None:
                return
            if info.role == const.fleetRoleLeader:
                caption = localization.GetByLabel('UI/Fleet/FleetWindow/FleetHeaderBoss', numMembers=nMembers)
            elif info.role == const.fleetRoleWingCmdr:
                caption = localization.GetByLabel('UI/Fleet/FleetWindow/FleetHeaderWingCmdr', numMembers=nMembers, wingName=info.wingName)
            else:
                caption = localization.GetByLabel('UI/Fleet/FleetWindow/FleetHeaderSquadMember', numMembers=nMembers, wingName=info.wingName, squadName=info.squadName)
            self.SetCaption(caption)

    def InitActions(self):
        broadcasts = ('EnemySpotted', 'HealArmor', 'HealShield', 'HealCapacitor', 'InPosition', 'NeedBackup', 'HoldPosition', 'Location')

        def BroadcastSender(name, *args):
            return lambda *args: getattr(sm.GetService('fleet'), 'SendBroadcast_%s' % name)()

        left = 6
        hmargin = 2
        self.broadcastMenuItems = []
        for name in broadcasts:
            par = FleetAction(parent=self.sr.actionsCont, align=uiconst.TOPLEFT, top=4, left=left, width=21, height=16, state=uiconst.UI_NORMAL)
            par.OnClick = BroadcastSender(name)
            left += hmargin + par.width + 1
            hint = fleetbr.GetBroadcastName(name)
            icon = fleetbr.types[name]['smallIcon']
            par.Startup(hint, icon)
            par.align = uiconst.RELATIVE
            self.broadcastMenuItems.append((hint, BroadcastSender(name)))

        self.SetBroadcastScopeButton()
        if eve.session.fleetrole in (const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr):
            self.broadcastMenuItems.append((localization.GetByLabel('UI/Fleet/FleetBroadcast/Commands/BroadcastTravelToMe'), sm.GetService('fleet').SendBroadcast_TravelTo, (eve.session.solarsystemid2,)))
        self.broadcastMenuItems += [None]

    def OnBroadcastScopeChange(self):
        self.SetBroadcastScopeButton()

    def CycleBroadcastScope(self, *args):
        sm.GetService('fleet').CycleBroadcastScope()

    def SetBroadcastScopeButton(self):
        uix.Flush(self.sr.toggleCont)
        scope = sm.GetService('fleet').broadcastScope
        hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/CycleBroadcastScope', scope=fleetbr.GetBroadcastScopeName(scope))
        self.sr.broadcastScopeButton = par = FleetAction(parent=self.sr.toggleCont, align=uiconst.TOPRIGHT, top=4, left=4, width=21, height=16, state=uiconst.UI_NORMAL)
        icon = {fleetcommon.BROADCAST_DOWN: 'res:/UI/Texture/Icons/73_16_28.png',
         fleetcommon.BROADCAST_UP: 'res:/UI/Texture/Icons/73_16_27.png',
         fleetcommon.BROADCAST_ALL: 'res:/UI/Texture/Icons/73_16_29.png'}.get(scope, 'res:/UI/Texture/Icons/73_16_28.png')
        par.OnClick = self.CycleBroadcastScope
        par.Startup(hint, icon)
        par.sr.icon.left = -1

    def OnLastBroadcastClick(self, broadcast):
        if not uicore.uilib.Key(uiconst.VK_CONTROL) or broadcast.itemID == session.shipid or session.shipid is None or broadcast.itemID is None or util.IsUniverseCelestial(broadcast.itemID):
            return
        itemID = broadcast.itemID
        if sm.GetService('target').IsInTargetingRange(itemID):
            sm.GetService('target').TryLockTarget(itemID)

    def OnFleetBroadcast_Local(self, broadcast):
        caption = broadcast.broadcastLabel
        iconName = fleetbr.defaultIcon[1]
        t = fleetbr.types.get(broadcast.name, None)
        if t:
            iconName = t['smallIcon']
        roleIcon = fleetbr.GetRoleIconFromCharID(broadcast.charID)
        self.sr.lastBroadcastCont.Flush()
        t = uicontrols.EveLabelMedium(text=caption, parent=self.sr.lastBroadcastCont, align=uiconst.TOALL, left=25, maxLines=1, state=uiconst.UI_DISABLED)
        self.sr.lastBroadcastCont.GetMenu = lambda : self.GetLastBroadcastMenu(broadcast)
        self.sr.lastBroadcastCont.OnClick = lambda : self.OnLastBroadcastClick(broadcast)
        self.sr.lastBroadcastCont.hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastNotificationHint', eventLabel=broadcast.broadcastLabel, time=broadcast.time, charID=broadcast.charID, range=fleetbr.GetBroadcastScopeName(broadcast.scope, broadcast.where), role=fleetbr.GetRankName(sm.GetService('fleet').GetMemberInfo(int(broadcast.charID))))
        icon = uicontrols.Icon(icon=iconName, parent=self.sr.lastBroadcastCont, align=uiconst.RELATIVE, pos=(6, 0, 16, 16), state=uiconst.UI_DISABLED)
        uthread.worker('fleet::flash', self.Flash, icon)

    def Flash(self, icon):
        timeStart = blue.os.GetWallclockTime()
        period = 0.7
        cycles = 3
        duration = period * int(cycles)
        import math
        coeff = math.pi / period
        while True:
            time = (blue.os.GetWallclockTime() - timeStart) / 10000000.0
            if time >= duration:
                icon.SetAlpha(1.0)
                return
            icon.SetAlpha(1.0 - math.sin(coeff * (time % period)))
            blue.pyos.synchro.SleepWallclock(10)

    def OnSpeakingEvent_Local(self, data):
        if self.destroyed:
            return
        caption = localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastEventSpeaking', charID=data.charID, channelName=data.channelName)
        iconName = '73_35'
        roleIcon = fleetbr.GetRoleIconFromCharID(data.charID)
        uix.Flush(self.sr.lastVoiceEventCont)
        t = uicontrols.EveLabelMedium(text=caption, parent=self.sr.lastVoiceEventCont, align=uiconst.TOALL, left=25, maxLines=1)
        lt = t
        lt.GetMenu = lambda : fleetbr.GetVoiceMenu(None, data.charID, data.channelID)
        lt.hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/VoiceBroadcastReceivedAt', time=data.time)
        icon = uicontrols.Icon(align=uiconst.RELATIVE, left=6, top=0, icon=iconName, width=16, height=16)
        icon.state = uiconst.UI_DISABLED
        self.sr.lastVoiceEventCont.children.append(icon)

    def ExportLootHistory(self):
        lootHistory = sm.GetService('fleet').GetLootHistory()
        rows = []
        for kv in lootHistory:
            t = cfg.invtypes.Get(kv.typeID)
            row = [util.FmtDate(kv.time, 'ss'),
             cfg.eveowners.Get(kv.charID).name,
             t.name,
             kv.quantity,
             cfg.invgroups.Get(t.groupID).name]
            rows.append(row)

        fileNameExtension = 'Loot'
        header = 'Time\tCharacter\tItem Type\tQuantity\tItem Group'
        self.ExportToDisk(header, rows, fileNameExtension)

    def ExportToDisk(self, header, rows, fileNameExtension):
        """
        Exports to the Fleetlogs folder a table of data
        """
        date = util.FmtDate(blue.os.GetWallclockTime())
        f = blue.classes.CreateInstance('blue.ResFile')
        directory = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '\\EVE\\logs\\Fleetlogs\\'
        filename = '%s - %s.txt' % (fileNameExtension, date.replace(':', '.'))
        fullPath = directory + filename
        if not f.Open(fullPath, 0):
            f.Create(fullPath)
        f.Write('%s\r\n' % header)
        for r in rows:
            row = ''
            for col in r:
                row += '%s\t' % unicode(col).encode('utf-8')

            f.Write('%s\r\n' % row)

        f.Write('\r\n')
        f.Close()
        eve.Message('FleetExportInfo', {'filename': filename,
         'folder': directory})

    def OnDropInMyFleet(self, dropObj, nodes):
        if not (sm.GetService('fleet').IsBoss() or session.fleetrole in (const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr)):
            return
        myNode = nodes[0]
        try:
            charID = myNode.charID
        except:
            return

        if not charID:
            return
        fleetSvc = sm.GetService('fleet')
        members = fleetSvc.GetMembers()
        if charID in members:
            return
        fleetSvc.Invite(charID, None, None, None)
        eve.Message('CharacterAddedAsSquadMember', {'char': charID})


class FleetJoinRequestWindow(uicontrols.Window):
    __guid__ = 'form.FleetJoinRequestWindow'
    default_windowID = 'FleetJoinRequestWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/fleet.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'all'
        self.SetCaption(localization.GetByLabel('UI/Fleet/FleetWindow/JoinRequests'))
        self.SetMinSize([256, 75])
        self.SetTopparentHeight(0)
        self.sr.main.padding = const.defaultPadding
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Fleet/FleetWindow/JoinRequestsHelp'), parent=self.sr.main, align=uiconst.TOTOP, padBottom=const.defaultPadding)
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main)
        self.sr.scroll.multiSelect = 0
        self.LoadJoinRequests()

    def LoadJoinRequests(self):
        scrolllist = []
        for joinRequest in sm.GetService('fleet').GetJoinRequests().itervalues():
            if joinRequest is None:
                continue
            name = localization.GetByLabel('UI/Common/CharacterNameLabel', charID=joinRequest.charID)
            data = util.KeyVal()
            data.label = name
            data.props = None
            data.checked = False
            data.charID = joinRequest.charID
            data.retval = None
            data.hint = None
            scrolllist.append((name, listentry.Get('JoinRequestField', data=data)))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.scroll.Load(contentList=scrolllist)


class JoinRequestField(listentry.Generic):
    __guid__ = 'listentry.JoinRequestField'
    __nonpersistvars__ = []

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        self.rejectBtn = uicontrols.Button(parent=self, label='<color=0xFFFF5555>' + localization.GetByLabel('UI/Fleet/RejectJoinRequest') + '</color>', left=2, func=self.RejectJoinRequest, idx=0, align=uiconst.TOPRIGHT)
        self.acceptBtn = uicontrols.Button(parent=self, label='<color=0xFF55FF55>' + localization.GetByLabel('UI/Fleet/AcceptJoinRequest') + '</color>', left=self.rejectBtn.left + self.rejectBtn.width + 2, func=self.AcceptJoinRequest, idx=0, align=uiconst.TOPRIGHT)

    def GetHeight(self, *args):
        node, width = args
        node.height = 23
        return node.height

    def GetMenu(self, *args):
        menuSvc = sm.GetService('menu')
        charID = self.sr.node.charID
        m = menuSvc.CharacterMenu(charID)
        return m

    def AcceptJoinRequest(self, *args):
        charID = self.sr.node.charID
        sm.GetService('fleet').Invite(charID, None, None, None)

    def RejectJoinRequest(self, *args):
        charID = self.sr.node.charID
        sm.GetService('fleet').RejectJoinRequest(charID)


class FleetComposition(uicontrols.Window):
    __guid__ = 'form.FleetComposition'
    default_windowID = 'FleetComposition'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'all'
        self.SetCaption(localization.GetByLabel('UI/Fleet/FleetComposition/FleetComposition'))
        self.SetMinSize([390, 200])
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.sr.main.left = self.sr.main.width = self.sr.main.top = self.sr.main.height = const.defaultPadding
        self.sr.top = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, height=34)
        self.sr.bottom = uiprimitives.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        refreshButtCont = uiprimitives.Container(name='refreshButtCont', parent=self.sr.top, align=uiconst.TORIGHT, width=80)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Fleet/FleetComposition/FleetCompositionHelp'), parent=self.sr.top, align=uiconst.TOALL, left=3)
        self.counterLabel = uicontrols.EveLabelMedium(text='', parent=self.sr.bottom, align=uiconst.TOBOTTOM, padRight=4, padTop=4)
        self.sr.refreshBtn = uicontrols.Button(parent=refreshButtCont, label=localization.GetByLabel('UI/Commands/Refresh'), left=2, func=self.RefreshClick, align=uiconst.TOPRIGHT)
        self.sr.scrollBroadcasts = uicontrols.Scroll(name='scrollComposition', parent=self.sr.bottom)
        self.sr.scrollBroadcasts.OnSelectionChange = self.OnScrollSelectionChange
        self.LoadComposition()
        uicore.registry.SetFocus(self.sr.scrollBroadcasts)

    def LoadComposition(self):
        fleetSvc = sm.GetService('fleet')
        if not fleetSvc.IsCommanderOrBoss():
            raise UserError('FleetNotCommanderOrBoss')
        scrolllist = []
        composition = fleetSvc.GetFleetComposition()
        fleetHierarchy = fleetSvc.GetFleetHierarchy()
        fleetPositionText = localization.GetByLabel('UI/Fleet/FleetWindow/FleetPosition')
        for kv in composition:
            blue.pyos.BeNice()
            member = fleetSvc.GetMemberInfo(kv.characterID, fleetHierarchy)
            if not fleetSvc.IsMySubordinate(kv.characterID) and not fleetSvc.IsBoss():
                continue
            data = util.KeyVal()
            charName = localization.GetByLabel('UI/Common/CharacterNameLabel', charID=kv.characterID)
            locationName = localization.GetByLabel('UI/Common/LocationDynamic', location=kv.solarSystemID)
            if kv.stationID:
                locationName = '%s %s' % (locationName, localization.GetByLabel('UI/Fleet/FleetComposition/Docked'))
            if kv.shipTypeID is not None:
                t = cfg.invtypes.Get(kv.shipTypeID)
                shipTypeName = t.name
                shipGroupName = t.Group().name
            else:
                shipTypeName = ''
                shipGroupName = ''
            if kv.skills:
                skillLevels = localization.GetByLabel('UI/Fleet/FleetComposition/SkillLevels', skillLevelA=kv.skills[2], skillLevelB=kv.skills[1], skillLevelC=kv.skills[0])
                data.hint = localization.GetByLabel('UI/Fleet/FleetComposition/SkillsHint', skillTypeA=kv.skillIDs[2], skillLevelA=kv.skills[2], skillTypeB=kv.skillIDs[1], skillLevelB=kv.skills[1], skillTypeC=kv.skillIDs[0], skillLevelC=kv.skills[0])
            else:
                skillLevels = ''
            if not member.wingName:
                fleetPosition = ''
                positionSortValue = (None, None)
            elif not member.squadName:
                fleetPosition = member.wingName
                positionSortValue = (fleetPosition, None)
            else:
                fleetPosition = '%s / %s ' % (member.wingName, member.squadName)
                positionSortValue = (member.wingName, member.squadName)
            data.label = '<t>'.join([charName,
             locationName,
             shipTypeName,
             shipGroupName,
             member.roleName,
             skillLevels,
             fleetPosition])
            data.GetMenu = self.OnCompositionEntryMenu
            data.cfgname = charName
            data.retval = None
            data.charID = kv.characterID
            data.shipTypeID = kv.shipTypeID
            data.solarSystemID = kv.solarSystemID
            data.info = cfg.eveowners.Get(kv.characterID)
            data.Set('sort_%s' % fleetPositionText, positionSortValue)
            scrolllist.append(listentry.Get('FleetCompositionEntry', data=data))

        self.counterLabel.text = localization.GetByLabel('UI/Fleet/FleetComposition/PilotsSelected', numSelected=0, numTotalPilots=len(scrolllist))
        self.sr.scrollBroadcasts.sr.id = 'scrollComposition'
        headers = [localization.GetByLabel('UI/Common/Name'),
         localization.GetByLabel('UI/Common/Location'),
         localization.GetByLabel('UI/Fleet/FleetComposition/ShipType'),
         localization.GetByLabel('UI/Fleet/FleetComposition/ShipGroup'),
         localization.GetByLabel('UI/Fleet/FleetComposition/FleetRole'),
         localization.GetByLabel('UI/Fleet/FleetComposition/FleetSkills'),
         fleetPositionText]
        self.sr.scrollBroadcasts.Load(headers=headers, contentList=scrolllist)

    def OnScrollSelectionChange(self, selectedList, *args):
        totalPilots = len(self.sr.scrollBroadcasts.GetNodes())
        selectedPilots = len(selectedList)
        self.counterLabel.text = localization.GetByLabel('UI/Fleet/FleetComposition/PilotsSelected', numSelected=selectedPilots, numTotalPilots=totalPilots)

    def OnCompositionEntryMenu(self, entry):
        m = []
        data = entry.sr.node
        m += fleetbr.GetMenu_Member(data.charID)
        if data.solarSystemID:
            m += [(uiutil.MenuLabel('UI/Common/SolarSystem'), sm.GetService('menu').CelestialMenu(data.solarSystemID))]
        if data.shipTypeID:
            m += [(uiutil.MenuLabel('UI/Common/Ship'), sm.GetService('menu').GetMenuFormItemIDTypeID(None, data.shipTypeID, ignoreMarketDetails=0))]
        return m

    def RefreshClick(self, *args):
        self.LoadComposition()


class FleetCompositionEntry(listentry.Generic):
    """
        A class for the entries in the fleet composition window.
        It gets its own class so it can be dragged/dropped correctly.
    """
    __guid__ = 'listentry.FleetCompositionEntry'
    isDragObject = True

    def GetDragData(self, *args):
        return self.sr.node.scroll.GetSelectedNodes(self.sr.node)
