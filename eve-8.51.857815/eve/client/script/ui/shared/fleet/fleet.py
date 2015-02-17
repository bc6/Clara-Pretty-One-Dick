#Embedded file name: eve/client/script/ui/shared/fleet\fleet.py
"""
This file contains the implementation of the inflight fleet windows
"""
from carbonui.control.scrollentries import OPACITY_IDLE
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.listgroup import ListGroup as Group
from eve.client.script.ui.inflight.baseTacticalEntry import BaseTacticalEntry
from eve.client.script.ui.inflight.actions import ActionPanel
from eve.client.script.ui.services.menuAction import Action
from eve.client.script.ui.control.eveBaseLink import GetCharIDFromTextLink
import _weakref
import uiprimitives
import uicontrols
import uix
import util
import uthread
from eve.client.script.ui.control import entries as listentry
import destiny
import blue
import state
import fleetbr
import chat
import types
import uiutil
import carbonui.const as uiconst
import uicls
import fleetcommon
import log
import telemetry
import localization
from collections import defaultdict
from fleetcommon import CHANNELSTATE_LISTENING, CHANNELSTATE_SPEAKING, CHANNELSTATE_MAYSPEAK, CHANNELSTATE_NONE
from fleetcommon import SQUAD_STATUS_NOSQUADCOMMANDER, SQUAD_STATUS_TOOMANYMEMBERS, SQUAD_STATUS_TOOFEWMEMBERS
CONNOT_BE_MOVED_INCOMPATIBLE = -1
CANNOT_BE_MOVED = 0
CAN_BE_COMMANDER = 1
CAN_ONLY_BE_MEMBER = 2
COLOR_CANNOT_BE_MOVED = (1,
 0,
 0,
 0.15)
COLOR_CAN_BE_COMMANDER = (1,
 1,
 1,
 0.2)
COLOR_CAN_ONLY_BE_MEMBER = (1,
 1,
 1,
 0.07)

def CommanderName(group):
    cmdr = group['commander']
    if cmdr:
        return cfg.eveowners.Get(cmdr).name
    else:
        return '<color=0x%%(alpha)xffffff>%s</color>' % localization.GetByLabel('UI/Fleet/FleetWindow/NoCommander')


def SquadronName(fleet, squadID):
    squadron = fleet['squads'][squadID]
    squadronName = squadron['name']
    if squadronName == '':
        squadno = GroupNumber(fleet, 'squad', squadID)
        squadronName = localization.GetByLabel('UI/Fleet/DefaultSquadName', squadNumber=squadno)
    return squadronName


def WingName(fleet, wingID):
    wing = fleet['wings'][wingID]
    wingName = wing['name']
    if wingName == '':
        wingno = GroupNumber(fleet, 'wing', wingID)
        wingName = localization.GetByLabel('UI/Fleet/DefaultWingName', wingNumber=wingno)
    return wingName


def GroupNumber(fleet, groupType, groupID):
    ids = fleet['%ss' % groupType].keys()
    ids.sort()
    return ids.index(groupID) + 1


def ChannelTypeToHeaderType(channelType):
    if channelType == 'squadid':
        return 'squad'
    if channelType == 'wingid':
        return 'wing'
    if channelType == 'fleetid':
        return 'fleet'


def HeaderTypeToChannelType(channelType):
    if channelType == 'squad':
        return 'squadid'
    if channelType == 'wing':
        return 'wingid'
    if channelType == 'fleet':
        return 'fleetid'


def GetParsedChannelID(channelID):
    """Returns a KeyValue object with all useful forms of the ChannelID"""
    ch = util.KeyVal()
    if type(channelID) is types.TupleType:
        if type(channelID[0]) is types.TupleType:
            channelID = channelID[0]
        ch.tuple = channelID
        ch.type = channelID[0]
        ch.integer = channelID[1]
    else:
        ch.tuple = (channelID,)
        ch.type = None
        ch.integer = channelID
    return ch


def GetChannelMenu(what, id):
    channelName = (what, id)
    m = []
    state = sm.GetService('fleet').GetVoiceChannelState(channelName)
    if state in [CHANNELSTATE_LISTENING, CHANNELSTATE_SPEAKING, CHANNELSTATE_MAYSPEAK]:
        m.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/LeaveChannel'), sm.GetService('vivox').LeaveChannel, (channelName,)))
    elif sm.GetService('fleet').CanIJoinChannel(what, id):
        m.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/JoinChannel'), sm.GetService('vivox').JoinChannel, (channelName,)))
    if not (session.fleetrole == const.fleetRoleLeader and what != 'fleetid' or session.fleetrole == const.fleetRoleWingCmdr and (what != 'wingid' or id != session.wingid) or session.fleetrole == const.fleetRoleSquadCmdr and (what != 'squadid' or id != session.squadid) or session.fleetrole == const.fleetRoleMember):
        if sm.GetService('fleet').GetChannelMuteStatus(channelName):
            m.append((uiutil.MenuLabel('UI/Chat/UnmuteChannel'), sm.GetService('fleet').SetVoiceMuteStatus, (0, channelName)))
        else:
            m.append((uiutil.MenuLabel('UI/Chat/MuteChannel'), sm.GetService('fleet').SetVoiceMuteStatus, (1, channelName)))
    if m:
        m = [(uiutil.MenuLabel('UI/Chat/Channel'), m)]
    return m


def GetSquadMenu(squadID):
    m = []
    if sm.GetService('fleet').IsBoss() or session.fleetrole in (const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr):
        m = [(uiutil.MenuLabel('UI/Fleet/FleetWindow/ChangeName'), lambda : sm.GetService('fleet').ChangeSquadName(squadID)), (uiutil.MenuLabel('UI/Fleet/FleetWindow/DeleteSquad'), lambda : sm.GetService('fleet').DeleteSquad(squadID))]
    m += GetChannelMenu('squadid', squadID)
    m.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/AddSquadMembersToWatchlist'), lambda : sm.GetService('fleet').AddFavoriteSquad(squadID)))
    return m


class FleetView(uiprimitives.Container):
    __guid__ = 'form.FleetView'
    __notifyevents__ = ['OnFleetMemberChanging',
     'OnManyFleetMembersChanging',
     'OnVoiceChannelJoined',
     'OnVoiceChannelLeft',
     'OnVoiceSpeakingChannelSet',
     'OnVoiceChannelIconClicked',
     'OnCollapsed',
     'OnExpanded',
     'OnFleetJoin_Local',
     'OnFleetLeave_Local',
     'OnFleetWingAdded_Local',
     'OnFleetWingDeleted_Local',
     'OnFleetSquadAdded_Local',
     'OnFleetSquadDeleted_Local',
     'OnFleetMemberChanged_Local',
     'OnFleetWingNameChanged_Local',
     'OnFleetSquadNameChanged_Local',
     'OnVoiceMuteStatusChange_Local',
     'OnMemberMuted_Local',
     'OnFleetOptionsChanged_Local']

    def PostStartup(self):
        sm.RegisterNotify(self)
        header = self
        header.baseHeight = 30
        e = self.sr.topEntry = FleetChannels(parent=header, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, height=22)
        e.Startup()
        self.top = -1
        uiprimitives.Container(name='push', parent=self, align=uiconst.TOBOTTOM, height=3)
        self.sr.scroll = uicontrols.Scroll(parent=self)
        self.isFlat = settings.user.ui.Get('flatFleetView', False)
        self.members = {}
        self.myGroups = {}
        self.voiceChannels = {}
        self.askingJoinVoice = False
        self.pending_RefreshFromRec = []
        self.scrollToProportion = 0
        self.fleet = None
        self.HandleFleetChanged()
        if sm.GetService('fleet').GetOptions().isVoiceEnabled:
            self.SetAutoJoinVoice()

    def Load(self, args):
        if not self.sr.Get('inited', 0):
            setattr(self.sr, 'inited', 1)
            self.PostStartup()
        if session.fleetid is not None:
            if getattr(self.sr, 'scroll', None):
                self.sr.scroll._OnResize()

    def GetCollapsedHeight(self):
        from eve.client.script.ui.inflight.actions import ActionPanel
        return ActionPanel.GetCollapsedHeight(self) + self.sr.topParent.height

    def OnFleetMemberChanging(self, charID):
        rec = self.members.get(charID)
        if rec is not None:
            rec.changing = True
            self.RefreshFromRec(rec)

    def OnManyFleetMembersChanging(self, charIDs):
        """
            This is scattered when many fleet members are changing. We can group the refreshing of the rec
            so it only happens for the last squadmember in the wing, because the whole wing is reloaded then and
            there is no need to reload it again and again
        """
        squadMembersByWingID = defaultdict(list)
        otherMembers = []
        for eachCharID in charIDs:
            rec = self.members.get(eachCharID)
            if rec is None:
                continue
            if not self.isFlat and rec.squadID not in (None, -1) and rec.wingID not in (None, -1):
                rec.changing = True
                squadMembersByWingID[rec.wingID].append(rec)
            else:
                otherMembers.append(eachCharID)

        for charsInWing in squadMembersByWingID.itervalues():
            recForFirstChar = charsInWing[0]
            if recForFirstChar:
                self.RefreshFromRec(recForFirstChar)

        for charID in otherMembers:
            self.OnFleetMemberChanging(charID)

    def UpdateHeader(self):
        from eve.client.script.ui.shared.fleet.fleetwindow import FleetWindow
        wnd = FleetWindow.GetIfOpen()
        if wnd:
            wnd.UpdateHeader()

    def CheckHint(self):
        if not self.sr.scroll.GetNodes():
            self.sr.scroll.ShowHint(localization.GetByLabel('UI/Fleet/NoFleet'))
        else:
            self.sr.scroll.ShowHint()
        self.UpdateHeader()

    def OnFleetWingAdded_Local(self, *args):
        self.HandleFleetChanged()

    def OnFleetWingDeleted_Local(self, *args):
        self.HandleFleetChanged()

    def OnFleetSquadAdded_Local(self, *args):
        self.HandleFleetChanged()

    def OnFleetSquadDeleted_Local(self, *args):
        self.HandleFleetChanged()

    def OnFleetSquadNameChanged_Local(self, squadID, name):
        self.fleet['squads'][squadID]['name'] = name
        headerNode = self.HeaderNodeFromGroupTypeAndID('squad', squadID)
        if headerNode:
            numMembers = len(sm.GetService('fleet').GetMembersInSquad(squadID))
            if numMembers == 0:
                headerNode.label = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderEmpty', unitName=name)
            else:
                headerNode.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderWithCount', unitName=name, memberCount=numMembers)
            if headerNode.panel:
                headerNode.panel.Load(headerNode)

    def OnFleetWingNameChanged_Local(self, wingID, name):
        self.fleet['wings'][wingID]['name'] = name
        headerNode = self.HeaderNodeFromGroupTypeAndID('wing', wingID)
        if headerNode:
            numMembers = len(sm.GetService('fleet').GetMembersInWing(wingID))
            if numMembers == 0:
                headerNode.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderEmpty', unitName=name)
            else:
                headerNode.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderWithCount', unitName=name, memberCount=numMembers)
            if headerNode.panel:
                headerNode.panel.Load(headerNode)

    def OnVoiceMuteStatusChange_Local(self, status, channel, leader, exclusionList):
        if session.charid not in getattr(self, 'members', []):
            return
        t = 'fleet'
        if channel[0][0] == 'wingid':
            t = 'wing'
        elif channel[0][0] == 'squadid':
            t = 'squad'
        headerNode = self.HeaderNodeFromGroupTypeAndID(t, channel[0][1])
        if headerNode:
            headerNode.channelIsMuted = status
            if headerNode.panel:
                headerNode.panel.Load(headerNode)
                self.ReloadScrollEntry(headerNode)

    def OnMemberMuted_Local(self, charID, channel, isMuted):
        rec = self.members[charID]
        self.RefreshFromRec(rec)
        if charID == session.charid:
            parsedChannelID = GetParsedChannelID(channel)
            headerType = ChannelTypeToHeaderType(parsedChannelID.type)
            fleetHeader = self.HeaderNodeFromGroupTypeAndID(headerType, parsedChannelID.integer)
            if fleetHeader and fleetHeader.panel:
                fleetHeader.panel.UpdateVoiceIcon()

    def OnFleetJoin_Local(self, rec):
        if not self or self.destroyed:
            return
        if rec.charID == session.charid:
            self.HandleFleetChanged()
        else:
            self.AddChar(rec)

    def OnFleetOptionsChanged_Local(self, oldOptions, options):
        if not oldOptions.isVoiceEnabled and options.isVoiceEnabled and self.askingJoinVoice == False:
            self.askingJoinVoice = True
            self.SetAutoJoinVoice()

    def SetAutoJoinVoice(self):
        if FleetSvc().IsBoss():
            sm.GetService('fleet').SetAutoJoinVoice()
        elif settings.user.audio.Get('talkAutoJoinFleet', 1) and not getattr(sm.GetService('fleet'), 'isAutoJoinVoice', 0):
            if eve.Message('FleetConfirmAutoJoinVoice', {}, uiconst.YESNO) == uiconst.ID_YES:
                sm.GetService('fleet').SetAutoJoinVoice()
            else:
                settings.user.audio.Set('talkAutoJoinFleet', 0)
        self.askingJoinVoice = False

    def AddChar(self, rec):
        if self.fleet is None:
            return
        self.members[rec.charID] = rec
        FleetSvc().AddToFleet(self.fleet, rec)
        if not self.isFlat:
            self.HandleFleetChanged()
        self.RefreshFromRec(rec)

    def OnFleetLeave_Local(self, rec):
        if rec.charID == session.charid:
            return
        self.RemoveChar(rec.charID)
        if rec.role == const.fleetRoleSquadCmdr:
            self.FlashHeader('squad', rec.squadID)
        elif rec.role == const.fleetRoleWingCmdr:
            self.FlashHeader('wing', rec.wingID)
        elif rec.role == const.fleetRoleLeader:
            self.FlashHeader('fleet', session.fleetid)

    def RemoveChar(self, charID):
        rec = self.members.pop(charID, None)
        if rec is None or self.fleet is None:
            return
        if None not in (rec.squadID, rec.wingID):
            self.RemoveFromFleet(self.fleet, rec)
            if self.isFlat:
                self.RemoveCharFromScroll(charID)
            else:
                self.HandleFleetChanged()
            self.RefreshFromRec(rec, removing=1)

    def OnFleetMemberChanged_Local(self, charID, fleetID, oldWingID, oldSquadID, oldRole, oldJob, oldBooster, oldTakesFleetWarp, newWingID, newSquadID, newRole, newJob, newBooster, newTakesFleetWarp):
        rec = self.members[charID]

        def UpdateRec():
            rec.changing = False
            rec.role, rec.job = newRole, newJob
            rec.wingID, rec.squadID = newWingID, newSquadID
            rec.roleBooster = newBooster
            rec.takesFleetWarp = newTakesFleetWarp

        if (oldWingID, oldSquadID) != (newWingID, newSquadID):
            if self.isFlat:
                UpdateRec()
                self.RefreshFromRec(rec)
            else:
                if const.fleetRoleLeader in (oldRole, newRole):
                    self.HandleFleetChanged()
                else:
                    self.RemoveChar(charID)
                    UpdateRec()
                    self.AddChar(rec)
                self.UpdateHeader()
        else:
            UpdateRec()
            if oldRole == const.fleetRoleSquadCmdr != newRole:
                self.fleet['squads'][rec.squadID]['commander'] = None
            elif oldRole == const.fleetRoleMember != newRole:
                self.fleet['squads'][rec.squadID]['commander'] = rec.charID
            self.RefreshFromRec(rec)
        if oldRole == const.fleetRoleSquadCmdr and (newRole != const.fleetRoleSquadCmdr or newSquadID != oldSquadID):
            self.FlashHeader('squad', oldSquadID)
        elif oldRole == const.fleetRoleWingCmdr and (newRole != const.fleetRoleWingCmdr or newWingID != oldWingID):
            self.FlashHeader('wing', oldWingID)
        elif oldRole == const.fleetRoleLeader != newRole:
            self.FlashHeader('fleet', session.fleetid)

    def FlashHeader(self, groupType, groupID):
        uthread.new(self.FlashHeader_thread, groupType, groupID)

    def FlashHeader_thread(self, groupType, groupID):
        headerNode = self.HeaderNodeFromGroupTypeAndID(groupType, groupID)
        if headerNode and headerNode.panel:
            if hasattr(headerNode.panel, 'Flash'):
                headerNode.panel.Flash()

    def RemoveFromFleet(self, fleet, rec):

        def Name(charID):
            return charID and cfg.eveowners.Get(charID).name

        def RemoveCommander(group, charID):
            if group['commander'] == charID:
                group['commander'] = None
            else:
                log.LogError('Commander is', Name(group['commander']), 'not', Name(charID))

        if rec.squadID != -1:
            squad = fleet['squads'][rec.squadID]
            if rec.role == const.fleetRoleSquadCmdr:
                RemoveCommander(squad, rec.charID)
            try:
                squad['members'].remove(rec.charID)
            except ValueError:
                log.LogError(Name(rec.charID), 'not in squad.')

        elif rec.wingID != -1:
            RemoveCommander(fleet['wings'][rec.wingID], rec.charID)
        else:
            RemoveCommander(fleet, rec.charID)

    def RefreshFromRec(self, rec, removing = 0):
        self.scrollToProportion = self.sr.scroll.GetScrollProportion()
        if getattr(self, 'loading_RefreshFromRec', 0):
            self.pending_RefreshFromRec.append(rec)
            return
        setattr(self, 'loading_RefreshFromRec', 1)
        try:
            if self.isFlat:
                if not removing:
                    self.AddOrUpdateScrollEntry(rec.charID)
            elif rec.wingID not in (None, -1):
                self.RefreshRecMemberInWing(rec.wingID, rec.squadID)
            else:
                self.HandleFleetChanged()
            self.UpdateHeader()
            self.loading_RefreshFromRec = 0
            if self.pending_RefreshFromRec:
                recToRefresh = self.pending_RefreshFromRec.pop(0)
                self.RefreshFromRec(recToRefresh)
        finally:
            self.sr.scroll.ScrollToProportion(self.scrollToProportion)
            setattr(self, 'loading_RefreshFromRec', 0)

    def RefreshRecMemberInWing(self, wingID, squadID):
        inSquad = squadID not in (None, -1)
        if inSquad:
            loadingVariable = 'refreshing_squadMembers_wingID_%s' % wingID
            pendingVariable = 'pendingRefresing_squadMembers_wingID_%s' % wingID
        else:
            loadingVariable = 'refreshing_non_squadMembers_wingID_%s' % wingID
            pendingVariable = 'pending_non_refreshingWingID_%s' % wingID
        if getattr(self, loadingVariable, False):
            setattr(self, pendingVariable, True)
            return
        setattr(self, loadingVariable, True)
        wingHeaderNode = self.HeaderNodeFromGroupTypeAndID('wing', wingID)
        try:
            if inSquad:
                if wingHeaderNode:
                    self.ReloadScrollEntry(wingHeaderNode)
            else:
                fleetHeaderNode = self.HeaderNodeFromGroupTypeAndID('fleet', session.fleetid)
                if fleetHeaderNode:
                    self.ReloadScrollEntry(fleetHeaderNode)
        finally:
            setattr(self, loadingVariable, False)
            if getattr(self, pendingVariable, False):
                setattr(self, pendingVariable, False)
                self.RefreshRecMemberInWingCaller_thread(wingID, squadID)

    def RefreshRecMemberInWingCaller_thread(self, wingID, squadID):
        blue.pyos.synchro.SleepWallclock(0)
        self.RefreshRecMemberInWing(wingID, squadID)

    def ReloadScrollEntry(self, headerNode):
        if headerNode:
            scroll = getattr(headerNode, 'scroll', None)
            if scroll:
                scroll.PrepareSubContent(headerNode)

    def HeaderNodeFromGroupTypeAndID(self, groupType, groupID):
        for entry in self.sr.scroll.GetNodes():
            if entry.groupType == groupType and entry.groupID == groupID:
                return entry

    def HandleFleetChanged(self):
        uthread.pool('FleetView::HandleFleetChanged', self.DoHandleFleetChanged)

    def DoHandleFleetChanged(self):
        if not self or self.destroyed:
            return
        if getattr(self, 'loading_HandleFleetChanged', 0):
            setattr(self, 'pending_HandleFleetChanged', 1)
            return
        setattr(self, 'loading_HandleFleetChanged', 1)
        blue.pyos.synchro.SleepWallclock(1000)
        setattr(self, 'pending_HandleFleetChanged', 0)
        try:
            try:
                self.members = FleetSvc().GetMembers().copy()
                if session.charid in self.members:
                    self.sr.scroll.Load(contentList=[])
                    self.LoadFleet()
                    self.CheckHint()
                setattr(self, 'loading_HandleFleetChanged', 0)
                if getattr(self, 'pending_HandleFleetChanged', 0):
                    setattr(self, 'pending_HandleFleetChanged', 0)
                    self.HandleFleetChanged()
            finally:
                setattr(self, 'loading_HandleFleetChanged', 0)

        except:
            pass

    def EmptyGroupEntry(self, label, indent, groupType, groupID):
        data = util.KeyVal()
        data.label = label
        data.indent = indent
        data.groupType = groupType
        data.groupID = groupID
        return listentry.Get('EmptyGroup', data=data)

    def MakeCharEntry(self, charID, sublevel = 0, isLast = False):
        data = self.GetMemberData(charID, sublevel=sublevel)
        data.isLast = isLast
        data.groupType = 'fleetMember'
        return listentry.Get('FleetMember', data=data)

    def MakeSquadEntry(self, squadID, sublevel = 0):
        headerdata = self.GetHeaderData('squad', squadID, sublevel)
        if headerdata.numMembers == 0:
            data = util.KeyVal()
            data.squadID = squadID
            data.groupType = 'squad'
            data.groupID = squadID
            data.label = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderEmpty', unitName=SquadronName(self.fleet, squadID))
            data.GetMenu = self.EmptySquadMenu
            data.indent = 2
            entry = listentry.Get('EmptyGroup', data=data)
            return entry
        else:
            return listentry.Get('FleetHeader', data=headerdata)

    def EmptySquadMenu(self, entry):
        return GetSquadMenu(entry.sr.node.squadID)

    def MakeWingEntry(self, wingID, sublevel = 0):
        headerdata = self.GetHeaderData('wing', wingID, sublevel)
        return listentry.Get('FleetHeader', data=headerdata)

    def MakeFleetEntry(self):
        headerdata = self.GetHeaderData('fleet', session.fleetid, 0)
        return listentry.Get('FleetHeader', data=headerdata)

    def AddToScroll(self, *entries):
        self.sr.scroll.AddEntries(-1, entries)

    def RemoveCharFromScroll(self, charID):
        for entry in self.sr.scroll.GetNodes():
            if entry.charID == charID:
                self.sr.scroll.RemoveEntries([entry])
                return

    def LoadFleet(self):
        fleetMembers = {}
        for charID, member in self.members.iteritems():
            if None not in (member.squadID, member.wingID):
                fleetMembers[charID] = member
            if charID == session.charid:
                self.myGroups['squad'] = member.squadID
                self.myGroups['wing'] = member.wingID

        fleet = self.fleet = FleetSvc().GetFleetHierarchy(fleetMembers)
        if self.isFlat:
            scrolllist = []
            for charID in self.members.keys():
                entry = self.MakeCharEntry(charID, sublevel=1, isLast=True)
                scrolllist.append((cfg.eveowners.Get(charID).name.lower(), entry))

            scrolllist = uiutil.SortListOfTuples(scrolllist)
            self.sr.scroll.Load(contentList=scrolllist)
        else:
            self.AddToScroll(self.MakeFleetEntry())
            self.sr.scroll.ScrollToProportion(self.scrollToProportion)

    def GetMemberData(self, charID, slimItem = None, member = None, sublevel = 0):
        if slimItem is None:
            slimItem = util.SlimItemFromCharID(charID)
        data = util.KeyVal()
        data.charRec = cfg.eveowners.Get(charID)
        data.itemID = data.id = data.charID = charID
        data.typeID = data.charRec.typeID
        data.squadID = None
        data.wingID = None
        data.displayName = data.charRec.name
        data.roleIcons = []
        data.muteStatus = sm.GetService('fleet').CanIMuteOrUnmuteCharInMyChannel(charID)
        member = member or self.members.get(charID)
        if member:
            data.squadID = member.squadID
            data.wingID = member.wingID
            data.role = member.role
            if member.job & const.fleetJobCreator:
                data.roleIcons.append({'id': '73_20',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/Boss')})
            if member.roleBooster == const.fleetBoosterFleet:
                data.roleIcons.append({'id': '73_22',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/FleetBooster')})
            elif member.roleBooster == const.fleetBoosterWing:
                data.roleIcons.append({'id': '73_23',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/WingBooster')})
            elif member.roleBooster == const.fleetBoosterSquad:
                data.roleIcons.append({'id': '73_24',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/SquadBooster')})
            if member.role == const.fleetRoleLeader:
                data.roleIcons.append({'id': '73_17',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/FleetCommander')})
            elif member.role == const.fleetRoleWingCmdr:
                data.roleIcons.append({'id': '73_18',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/WingCommander')})
            elif member.role == const.fleetRoleSquadCmdr:
                data.roleIcons.append({'id': '73_19',
                 'hint': localization.GetByLabel('UI/Fleet/Ranks/SquadCommander')})
            if member.takesFleetWarp == False:
                data.roleIcons.append({'id': '73_47',
                 'hint': localization.GetByLabel('UI/Fleet/FleetWindow/DoesNotTakeFleetWarp')})
        data.label = data.displayName
        data.isSub = 0
        data.sort_name = data.displayName
        data.sublevel = sublevel
        data.member = member
        if slimItem:
            data.slimItem = _weakref.ref(slimItem)
        else:
            data.slimItem = None
        data.changing = getattr(member, 'changing', False)
        return data

    def GetHeaderData(self, gtype, gid, sublevel):
        data = util.KeyVal()
        data.id = ('fleet', '%s_%s' % (gtype, gid))
        channelName = (HeaderTypeToChannelType(gtype), gid)
        data.voiceChannelName = channelName
        data.groupType = gtype
        data.groupID = gid
        data.rawText = ''
        data.displayName = data.label = ''
        data.sublevel = sublevel
        data.expanded = True
        data.showicon = 'hide'
        data.hideFill = True
        data.hideTopLine = True
        data.hideExpanderLine = True
        data.showlen = False
        data.BlockOpenWindow = 1
        data.voiceIconChannel = None
        data.channelIsMuted = sm.GetService('fleet').GetChannelMuteStatus(channelName)
        data.labelstyle = {'uppercase': True,
         'fontsize': 9,
         'letterspacing': 2}
        data.myGroups = self.myGroups
        group = self.GetGroup(gtype, gid)
        data.commanderName = CommanderName(group) % {'alpha': 119}
        data.commanderMuteStatus = sm.GetService('fleet').CanIMuteOrUnmuteCharInMyChannel(group['commander'])
        data.commanderData = None
        num = 0
        if gtype == 'squad':
            data.GetSubContent = self.SquadContentGetter(gid, sublevel)
            num = len(sm.GetService('fleet').GetMembersInSquad(gid))
            if num == 0:
                data.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderEmpty', unitName=SquadronName(self.fleet, gid))
            else:
                data.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderWithCount', unitName=SquadronName(self.fleet, gid), memberCount=num)
        elif gtype == 'wing':
            data.GetSubContent = self.WingContentGetter(gid, sublevel)
            num = len(sm.GetService('fleet').GetMembersInWing(gid))
            data.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderWithCount', unitName=WingName(self.fleet, gid), memberCount=num)
        elif gtype == 'fleet':
            data.GetSubContent = self.FleetContentGetter(gid, sublevel)
            num = len(self.members)
            data.groupInfo = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderWithCount', unitName=localization.GetByLabel('UI/Fleet/Fleet'), memberCount=num)
            data.scroll = self.sr.scroll
        else:
            raise NotImplementedError
        data.numMembers = num
        if group['commander']:
            commanderData = self.GetMemberData(group['commander'])
            data.commanderData = commanderData
        data.active = self.IsGroupActive(gtype, gid)
        data.openByDefault = data.open = True
        return data

    def AddOrUpdateScrollEntry(self, charID):
        newEntry = self.MakeCharEntry(charID)
        newEntry.sublevel = 1
        newEntry.isLast = 1
        for i, data in enumerate(self.sr.scroll.GetNodes()):
            if data.Get('id', None) == charID:
                newEntry.panel = data.Get('panel', None)
                scroll = data.Get('scroll', None)
                if scroll is not None:
                    newEntry.scroll = scroll
                newEntry.idx = i
                self.sr.scroll.GetNodes()[i] = newEntry
                if newEntry.panel is not None:
                    newEntry.panel.Load(newEntry)
                return

        self.sr.scroll.AddEntries(-1, [newEntry])
        self.sr.scroll.Sort(by='name')

    def IsGroupActive(self, gtype, gid):
        return self.GetGroup(gtype, gid)['active']

    def SquadContentGetter(self, squadID, sublevel):

        def GetContent(*blah):
            squad = self.fleet['squads'][squadID]
            ret = []
            if squad['members']:
                sortedMembers = uiutil.SortListOfTuples([ ((charID != squad['commander'], self.members[charID].job != const.fleetJobCreator, cfg.eveowners.Get(charID).name.lower()), charID) for charID in squad['members'] ])
                if squad['commander'] is not None:
                    sortedMembers.remove(squad['commander'])
                for i in range(len(sortedMembers)):
                    charID = sortedMembers[i]
                    ret.append(self.MakeCharEntry(charID, sublevel=sublevel + 1, isLast=i == len(sortedMembers) - 1))

            if not ret:
                emptyGroupEntery = self.EmptyGroupEntry(localization.GetByLabel('UI/Fleet/FleetWindow/SquadEmpty'), sublevel + 1, 'squad', squadID)
                ret = [emptyGroupEntery]
            return ret

        return GetContent

    def WingContentGetter(self, wingID, sublevel):

        def GetContent(*blah):
            wing = self.fleet['wings'][wingID]
            ret = []
            squads = wing['squads'][:]
            squads.sort()
            for squadID in squads:
                ret.append(self.MakeSquadEntry(squadID, sublevel + 1))

            if not ret:
                emptyGroupEntery = self.EmptyGroupEntry(localization.GetByLabel('UI/Fleet/FleetWindow/WingEmpty'), sublevel + 1, 'wing', wingID)
                ret = [emptyGroupEntery]
            return ret

        return GetContent

    def FleetContentGetter(self, fleetID, sublevel):

        def GetContent(*blah):
            ret = []
            wings = self.fleet['wings'].keys()
            wings.sort()
            for wingID in wings:
                ret.append(self.MakeWingEntry(wingID, sublevel + 1))

            return ret

        return GetContent

    def GetGroup(self, groupType, groupID):
        if groupType == 'fleet':
            return self.fleet
        if groupType == 'wing':
            return self.fleet['wings'][groupID]
        if groupType == 'squad':
            return self.fleet['squads'][groupID]
        raise NotImplementedError

    def GetMemberEntry(self, charID):
        for entry in self.sr.scroll.GetNodes():
            if entry.charID == charID:
                return entry

    def OnVoiceChannelJoined(self, channelID):
        parsedChannelID = GetParsedChannelID(channelID)
        headerType = ChannelTypeToHeaderType(parsedChannelID.type)
        fleetHeader = self.HeaderNodeFromGroupTypeAndID(headerType, parsedChannelID.integer)
        if fleetHeader and fleetHeader.panel:
            fleetHeader.panel.UpdateVoiceIcon()

    def OnVoiceChannelLeft(self, channelID):
        state = sm.GetService('fleet').GetVoiceChannelState(channelID)
        parsedChannelID = GetParsedChannelID(channelID)
        headerType = ChannelTypeToHeaderType(parsedChannelID.type)
        fleetHeader = self.HeaderNodeFromGroupTypeAndID(headerType, parsedChannelID.integer)
        if fleetHeader and fleetHeader.panel:
            fleetHeader.panel.UpdateVoiceIcon()

    def OnVoiceSpeakingChannelSet(self, channelID, oldChannelID):
        if channelID:
            state = sm.GetService('fleet').GetVoiceChannelState(channelID)
            parsedChannelNew = GetParsedChannelID(channelID)
        parsedChannelOld = GetParsedChannelID(oldChannelID)
        if channelID:
            headerTypeNew = ChannelTypeToHeaderType(parsedChannelNew.type)
        headerTypeOld = ChannelTypeToHeaderType(parsedChannelOld.type)
        if channelID:
            fleetHeaderNew = self.HeaderNodeFromGroupTypeAndID(headerTypeNew, parsedChannelNew.integer)
        fleetHeaderOld = self.HeaderNodeFromGroupTypeAndID(headerTypeOld, parsedChannelOld.integer)
        if channelID and fleetHeaderNew and fleetHeaderNew.panel:
            fleetHeaderNew.panel.UpdateVoiceIcon()
        if fleetHeaderOld and fleetHeaderOld.panel:
            fleetHeaderOld.panel.UpdateVoiceIcon()

    def OnVoiceChannelIconClicked(self, iconHeader):
        state = sm.GetService('fleet').GetVoiceChannelState(iconHeader.sr.node.voiceChannelName)
        if state == CHANNELSTATE_NONE:
            sm.GetService('vivox').JoinChannel(iconHeader.sr.node.voiceIconChannel)
        elif state == CHANNELSTATE_MAYSPEAK:
            sm.GetService('vivox').SetSpeakingChannel(iconHeader.sr.node.voiceIconChannel)
        elif state == CHANNELSTATE_SPEAKING:
            sm.GetService('vivox').SetSpeakingChannel(None)

    def UpdateVoiceIcon(self, id):
        for node in self.GetNodes():
            if node.id == id and node.panel:
                node.panel.UpdateVoiceIcon()

    def OnExpanded(self, wnd, *args):
        pass


class FleetHeader(Group):
    __guid__ = 'listentry.FleetHeader'
    isDragObject = True

    def Startup(self, *args, **kw):
        Group.Startup(self, *args, **kw)
        text_gaugepar = uiprimitives.Container(name='text_gaugepar', parent=self, idx=0, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        text_gaugepar.width = 0
        self.sr.text_gaugepar = text_gaugepar
        self.sr.label.parent.width = 0
        self.sr.label.parent.SetParent(text_gaugepar)
        uiprimitives.Container(name='toppush', parent=self.sr.label.parent, align=uiconst.TOTOP, height=14)
        roleIconsContainer = uiprimitives.Container(name='roleIconsContainer', parent=self.sr.label.parent, width=0, align=uiconst.TORIGHT)
        self.roleIconsContainer = roleIconsContainer
        self.sr.topLabel = uicontrols.EveLabelMedium(text='', parent=self.sr.label.parent, left=0, top=0, state=uiconst.UI_DISABLED, color=None, idx=0)
        self.sr.bottomLabel = uicontrols.EveLabelMedium(text='', parent=self.sr.label.parent, left=0, top=12, state=uiconst.UI_DISABLED, color=None, idx=0)
        changing = uicls.AnimSprite(icons=[ 'ui_38_16_%s' % (210 + i) for i in xrange(8) ], align=uiconst.TOPRIGHT, parent=self, pos=(0, 13, 16, 16))
        self.sr.changing = changing
        changing.state = uiconst.UI_NORMAL
        self.sr.myGroupSelection = uiprimitives.Fill(name='myGroupSelection', bgParent=self, padding=(0, 1, 0, 1), color=(0.0, 0.5, 0.0, 0.1))
        self.sr.myGroupSelection.display = False
        self.movingHilite = uiprimitives.Fill(bgParent=self, name='movingHilite', color=(1, 0, 0, 0.25))
        self.movingHilite.display = False

    def Load(self, node, *args, **kw):
        sublevel = node.Get('sublevel', 0)
        if node.groupType != 'fleet':
            node.hasArrow = True
        Group.Load(self, node, *args, **kw)
        if node.groupType not in ('fleet', 'wing'):
            self.sr.expander.left += 24
        else:
            self.sr.expander.left += 16
        self.sr.bottomLineLeft.width += 16 + 16 * sublevel
        if node.groupType == 'squad':
            left = 44
        else:
            left = 38
        left += sublevel * 16
        self.sr.label.left = left
        self.sr.topLabel.left = left
        self.sr.bottomLabel.left = left
        if node.commanderData and node.commanderData.itemID == session.charid:
            self.sr.myGroupSelection.display = True
        else:
            isMyGroup = node.myGroups.get(node.groupType, None) == node.groupID or node.groupType == 'fleet'
            if isMyGroup:
                self.sr.expander.SetRGBA(0.0, 0.5, 0.0, 0.8)
        label = self.GetTopLabelText(node)
        self.sr.topLabel.text = label
        self.sr.bottomLabel.top = max(12, self.sr.topLabel.top + self.sr.topLabel.textheight)
        bottomLabelText = self.GetBottomLabelText(node)
        self.sr.bottomLabel.text = bottomLabelText
        icons = getattr(node.commanderData, 'roleIcons', [])
        UpdateRoleIcons(self.roleIconsContainer, icons)
        self.CreateVoiceIcon()
        if node.commanderData and node.commanderData.changing:
            self.sr.changing.state = uiconst.UI_DISABLED
            self.hint = localization.GetByLabel('UI/Fleet/FleetWindow/MemberChanging')
            self.sr.changing.Play()
        else:
            self.hint = None
            self.sr.changing.Stop()
            self.sr.changing.state = uiconst.UI_HIDDEN

    def OnDropData(self, dragObject, droppedGuys, *args):
        try:
            sm.GetService('fleet').OnDropCommanderDropData(dragObject, droppedGuys, self.sr.node)
        finally:
            self.movingHilite.display = False

    def OnDragEnter(self, dragObj, nodes):
        draggedGuy = nodes[0]
        if self.sr.node.commanderData and self.sr.node.commanderData.itemID == draggedGuy.charID:
            return
        groupType = self.sr.node.groupType
        groupID = self.sr.node.groupID
        isMultiMove = len(nodes) > 1
        canMove = sm.GetService('fleet').CanMoveToThisEntry(draggedGuy, self.sr.node, groupType, groupID=groupID, isMultiMove=isMultiMove)
        if canMove == CONNOT_BE_MOVED_INCOMPATIBLE:
            return
        if canMove == CANNOT_BE_MOVED:
            self.movingHilite.SetRGB(*COLOR_CANNOT_BE_MOVED)
        elif canMove == CAN_BE_COMMANDER:
            self.movingHilite.SetRGB(*COLOR_CAN_BE_COMMANDER)
        else:
            self.movingHilite.SetRGB(*COLOR_CAN_ONLY_BE_MEMBER)
        self.movingHilite.display = True

    def OnDragExit(self, dragObj, nodes):
        self.movingHilite.display = False

    def GetHeight(self, *args):
        node, width = args
        topLabelHeight = uix.GetTextHeight('<b>' + node.groupInfo + '</b>', maxLines=1)
        bottomLabelHeight = uix.GetTextHeight(node.commanderName, maxLines=1)
        node.height = max(12, topLabelHeight) + bottomLabelHeight + 2
        return node.height

    def ToggleAllSquads(self, node, isOpen = True):
        toggleThread = uthread.new(self.ToggleAllSquads_thread, node, isOpen)
        toggleThread.context = 'FleetHeader::ToggleAllSquads'

    def ToggleAllSquads_thread(self, node, isOpen = True):
        if isOpen:
            self.DoToggleFleetHeader(node, isOpen, groupType='fleet')
            self.DoToggleFleetHeader(node, isOpen, groupType='wing')
        self.DoToggleFleetHeader(node, isOpen, groupType='squad')

    def ToggleAllWings(self, node, isOpen = True):
        toggleThread = uthread.new(self.ToggleAllWings_thread, node, isOpen)
        toggleThread.context = 'FleetHeader::ToggleAllWings'

    def ToggleAllWings_thread(self, node, isOpen = True):
        if isOpen:
            self.DoToggleFleetHeader(node, isOpen, groupType='fleet')
        self.DoToggleFleetHeader(node, isOpen, groupType='wing')

    def DoToggleFleetHeader(self, node, isOpen, groupType):
        scroll = node.scroll
        for entry in scroll.GetNodes():
            if entry.__guid__ != 'listentry.FleetHeader':
                continue
            if entry.groupType == groupType:
                if entry.panel:
                    self.ShowOpenState(isOpen)
                    self.UpdateLabel()
                    uicore.registry.SetListGroupOpenState(entry.id, isOpen)
                    scroll.PrepareSubContent(entry)
                else:
                    uicore.registry.SetListGroupOpenState(entry.id, isOpen)
                    entry.scroll.PrepareSubContent(entry)

    def OnMouseDown(self, *args):
        commanderData = self.sr.node.commanderData
        if commanderData is None:
            return
        charID = commanderData.charID
        if sm.GetService('menu').TryExpandActionMenu(itemID=charID, clickedObject=self, radialMenuClass=uicls.RadialMenuSpaceCharacter):
            return

    def GetMenu(self):
        m = []
        commanderData = self.sr.node.commanderData
        if commanderData:
            filterFunc = [uiutil.MenuLabel('UI/Fleet/Fleet'), uiutil.MenuLabel('UI/Commands/ShowInfo')]
            m += sm.GetService('menu').FleetMenu(commanderData.charID, unparsed=False)
            m += [None] + [(uiutil.MenuLabel('UI/Common/Pilot'), ('isDynamic', sm.GetService('menu').CharacterMenu, (commanderData.charID,
                [],
                None,
                0,
                filterFunc)))]
        if self.sr.node.groupType == 'squad':
            return m + [None] + GetSquadMenu(self.sr.node.groupID)
        if self.sr.node.groupType == 'wing':
            return m + [None] + self.GetWingMenu(self.sr.node.groupID)
        if self.sr.node.groupType == 'fleet':
            m += [None] + self.GetFleetMenu()
            m += [None,
             (uiutil.MenuLabel('UI/Fleet/FleetWindow/OpenAllWings'), self.ToggleAllWings, (self.sr.node, True)),
             (uiutil.MenuLabel('UI/Fleet/FleetWindow/CloseAllWings'), self.ToggleAllWings, (self.sr.node, False)),
             (uiutil.MenuLabel('UI/Fleet/FleetWindow/OpenAllSquads'), self.ToggleAllSquads, (self.sr.node, True)),
             (uiutil.MenuLabel('UI/Fleet/FleetWindow/CloseAllSquads'), self.ToggleAllSquads, (self.sr.node, False))]
            return m
        raise NotImplementedError

    def GetFleetMenu(self):
        ret = []
        if session.fleetrole != const.fleetRoleLeader:
            ret += [(uiutil.MenuLabel('UI/Fleet/LeaveMyFleet'), FleetSvc().LeaveFleet)]
        if FleetSvc().IsBoss() or session.fleetrole == const.fleetRoleLeader:
            ret.extend([None, (uiutil.MenuLabel('UI/Fleet/FleetWindow/CreateNewWing'), lambda : FleetSvc().CreateWing())])
        else:
            ret.append(None)
        if session.fleetrole in [const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr]:
            ret.append((uiutil.MenuLabel('UI/Fleet/FleetWindow/Regroup'), lambda : FleetSvc().Regroup()))
        if FleetSvc().HasActiveBeacon(session.charid):
            ret.append((uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/JumpBeacon'), lambda : FleetSvc().SendBroadcast_JumpBeacon()))
        ret.append((uiutil.MenuLabel('UI/Fleet/FleetBroadcast/Commands/Location'), lambda : FleetSvc().SendBroadcast_Location()))
        ret += GetChannelMenu('fleetid', session.fleetid)
        return ret

    def GetWingMenu(self, wingID):
        if FleetSvc().IsBoss() or session.fleetrole in (const.fleetRoleLeader, const.fleetRoleWingCmdr):
            m = [(uiutil.MenuLabel('UI/Fleet/FleetWindow/DeleteWing'), lambda : sm.GetService('fleet').DeleteWing(wingID)), (uiutil.MenuLabel('UI/Fleet/FleetWindow/ChangeName'), lambda : sm.GetService('fleet').ChangeWingName(wingID)), (uiutil.MenuLabel('UI/Fleet/FleetWindow/CreateNewSquad'), lambda : sm.GetService('fleet').CreateSquad(wingID))]
            m += GetChannelMenu('wingid', wingID)
            return m
        else:
            return []

    def Flash(self):
        sm.GetService('ui').BlinkSpriteA(self.sr.topLabel, 1.0, 400, 8, passColor=0)
        sm.GetService('ui').BlinkSpriteA(self.sr.bottomLabel, 1.0, 400, 8, passColor=0)

    def CreateVoiceIcon(self):
        if self.sr.Get('voiceIconContainer'):
            self.UpdateVoiceIcon()
            return
        container = self.sr.voiceIconContainer = uiprimitives.Container(name='voiceIconContainer', align=uiconst.TOPLEFT, width=16, height=16, state=uiconst.UI_NORMAL, parent=self, idx=0)
        container.OnClick = self.VoiceIconClicked
        self.sr.voiceIcon = uicontrols.Icon(icon='ui_73_16_36', parent=container, size=16, left=1, top=0, align=uiconst.RELATIVE, state=uiconst.UI_DISABLED)
        self.UpdateVoiceIcon()

    def SetVoiceIconChannel(self, channel):
        self.sr.node.voiceIconChannel = channel

    def UpdateVoiceIcon(self):
        channelType = HeaderTypeToChannelType(self.sr.node.groupType)
        channelID = (channelType, int(self.sr.node.groupID))
        self.SetVoiceIconChannel(channelID)
        state = sm.GetService('fleet').GetVoiceChannelState(self.sr.node.voiceChannelName)
        self.sr.voiceIcon.state = uiconst.UI_DISABLED
        canJoinChannel = sm.GetService('fleet').CanIJoinChannel(self.sr.node.groupType, self.sr.node.groupID)
        if state == fleetcommon.CHANNELSTATE_LISTENING:
            self.sr.voiceIcon.LoadIcon('ui_73_16_37')
            self.sr.voiceIcon.parent.hint = localization.GetByLabel('UI/Fleet/FleetWindow/VoiceListeningHint')
        elif state == fleetcommon.CHANNELSTATE_SPEAKING:
            self.sr.voiceIcon.LoadIcon('ui_73_16_33')
            self.sr.voiceIcon.parent.hint = localization.GetByLabel('UI/Fleet/FleetWindow/VoiceSpeakingHint')
        elif state == fleetcommon.CHANNELSTATE_MAYSPEAK:
            self.sr.voiceIcon.LoadIcon('ui_73_16_35')
            self.sr.voiceIcon.parent.hint = localization.GetByLabel('UI/Fleet/FleetWindow/VoiceMaySpeakHint')
        elif canJoinChannel:
            self.sr.voiceIcon.LoadIcon('ui_73_16_36')
            self.sr.voiceIcon.parent.hint = localization.GetByLabel('UI/Fleet/FleetWindow/VoiceClickToJoinHint')
        else:
            self.sr.voiceIcon.state = uiconst.UI_HIDDEN

    def GetDragData(self, *args):
        commanderData = self.sr.node.commanderData
        if commanderData:
            info = cfg.eveowners.Get(commanderData.charID)
            fakeNode = self.sr.node
            fakeNode.info = info
            fakeNode.charID = commanderData.charID
            fakeNode.itemID = commanderData.charID
            return [fakeNode]
        else:
            return []

    def VoiceIconClicked(self, *etc):
        sm.ScatterEvent('OnVoiceChannelIconClicked', self)

    @classmethod
    def GetTopLabelText(cls, node, *args):
        if node.channelIsMuted:
            label = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeaderMuted', unitTitle=node.groupInfo)
        else:
            label = localization.GetByLabel('UI/Fleet/FleetWindow/UnitHeader', unitTitle=node.groupInfo)
        if node.numMembers == 0:
            label = '<color=0x88ffffff>%s</color>' % label
        return label

    @classmethod
    def GetBottomLabelText(cls, node, *args):
        if node.commanderMuteStatus > 0:
            label = localization.GetByLabel('UI/Fleet/FleetWindow/CommanderNameUnmuted', name=node.commanderName)
        else:
            label = node.commanderName
        return label

    @classmethod
    def GetCopyData(cls, node):
        sublevel = node.Get('sublevel', 0)
        indent = ' ' * sublevel * 4
        topLabel = cls.GetTopLabelText(node)
        bottomLabel = cls.GetBottomLabelText(node)
        text = indent + '-' + topLabel + '\n ' + indent + bottomLabel
        return text


def UpdateRoleIcons(parent, icons):
    for child in parent.children[:]:
        parent.children.remove(child)

    left = 0
    if icons is not None and len(icons):
        parent.width = len(icons) * 20
        for icon in icons:
            iconpath = icon['id']
            icon = uicontrols.Icon(icon=iconpath, parent=parent, pos=(left,
             0,
             16,
             16), align=uiconst.TOPLEFT, hint=icon['hint'])
            left += 20


def FleetSvc():
    """
    Reduce noise and help keep lines shorter!
    """
    return sm.GetService('fleet')


def GetFleetMenu():
    ret = [(localization.GetByLabel('UI/Fleet/LeaveMyFleet'), FleetSvc().LeaveFleet)]
    if FleetSvc().IsBoss() or session.fleetrole == const.fleetRoleLeader:
        ret.extend([None, (localization.GetByLabel('UI/Fleet/FleetWindow/Regroup'), lambda : FleetSvc().Regroup())])
    else:
        ret.append(None)
    if FleetSvc().HasActiveBeacon(session.charid):
        ret.append((localization.GetByLabel('UI/Fleet/FleetBroadcast/Commands/JumpBeacon'), lambda : FleetSvc().SendBroadcast_JumpBeacon()))
    ret.append((localization.GetByLabel('UI/Fleet/FleetBroadcast/Commands/Location'), lambda : FleetSvc().SendBroadcast_Location()))
    return ret


class EmptyGroup(listentry.Generic):
    __guid__ = 'listentry.EmptyGroup'

    def Load(self, data):
        listentry.Generic.Load(self, data)
        self.sr.label.left = 6 + 28 * data.indent
        self.sr.label.color.a = 0.7
        self.sr.label.Update()
        self.movingHilite = uiprimitives.Fill(bgParent=self, name='movingHilite', color=(1, 0, 0, 0.25))
        self.movingHilite.display = False

    def UpdateVoiceIcon(self):
        """
        EmptyGroups do not currently have voice icons so there is nothing to update.
        But it is still useful to have this method implemented to simplify logic elsewhere."""
        pass

    def OnDropData(self, dragObject, droppedGuys, *args):
        try:
            sm.GetService('fleet').OnDropCommanderDropData(dragObject, droppedGuys, self.sr.node)
        finally:
            self.movingHilite.display = False

    def OnDragEnter(self, dragObj, nodes):
        draggedGuy = nodes[0]
        groupType = self.sr.node.groupType
        groupID = self.sr.node.groupID
        isMultiMove = len(nodes) > 1
        canMove = sm.GetService('fleet').CanMoveToThisEntry(draggedGuy, self.sr.node, groupType, groupID=groupID, isMultiMove=isMultiMove)
        if canMove == CONNOT_BE_MOVED_INCOMPATIBLE:
            return
        if canMove == CANNOT_BE_MOVED:
            self.movingHilite.SetRGB(*COLOR_CANNOT_BE_MOVED)
        elif canMove == CAN_BE_COMMANDER:
            self.movingHilite.SetRGB(*COLOR_CAN_BE_COMMANDER)
        else:
            self.movingHilite.SetRGB(*COLOR_CAN_ONLY_BE_MEMBER)
        self.movingHilite.display = True

    def OnDragExit(self, dragObj, nodes):
        self.movingHilite.display = False

    @classmethod
    def GetCopyData(cls, node):
        sublevel = node.Get('isSub', 0)
        indent = ' ' * sublevel * 4
        return indent + node.label


class FleetMember(BaseTacticalEntry):
    __guid__ = 'listentry.FleetMember'
    isDragObject = True

    def Startup(self, *args, **kw):
        BaseTacticalEntry.Startup(self, *args, **kw)
        idx = self.sr.label.parent.children.index(self.sr.label)
        text_gaugepar = uiprimitives.Container(name='text_gaugepar', parent=self, idx=idx, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        text_gaugepar.width = 0
        textpar = uiprimitives.Container(name='textpar', parent=text_gaugepar, idx=idx, align=uiconst.TOALL, pos=(0, 0, 0, 0), clipChildren=True)
        self.sr.text_gaugepar = text_gaugepar
        self.children.remove(self.sr.label)
        textpar.children.append(self.sr.label)
        uiprimitives.Container(name='toppush', parent=textpar, align=uiconst.TOTOP, height=2)
        roleIconsContainer = uiprimitives.Container(name='roleIconsContainer', parent=textpar, width=0, align=uiconst.TORIGHT)
        self.roleIconsContainer = roleIconsContainer
        changing = uicls.AnimSprite(icons=[ 'ui_38_16_%s' % (210 + i) for i in xrange(8) ], align=uiconst.TOPRIGHT, parent=self, pos=(0, 0, 16, 16))
        self.sr.changing = changing
        changing.state = uiconst.UI_HIDDEN
        self.sr.myGroupSelection = uiprimitives.Fill(name='myGroupSelection', bgParent=self, padding=(0, 1, 0, 1), color=(0.0, 0.5, 0.0, 0.15))
        self.sr.myGroupSelection.display = False
        self.movingHilite = uiprimitives.Fill(bgParent=self, name='movingHilite', color=(1, 0, 0, 0.25))
        self.movingHilite.display = False

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.line.state = [uiconst.UI_HIDDEN, uiconst.UI_NORMAL][node.isLast]
        data = node
        if settings.user.ui.Get('flatFleetView', False):
            left = 0
        else:
            left = 44
            if node.itemID == session.charid:
                self.sr.myGroupSelection.display = True
        indent = left + node.sublevel * 16
        self.sr.label.left = indent
        if node.muteStatus > 0:
            self.sr.label.text += ' (unmuted)'
        selected, = sm.GetService('state').GetStates(data.itemID, [state.selected])
        if selected:
            self.Select()
        icons = node.Get('roleIcons', None)
        UpdateRoleIcons(self.roleIconsContainer, icons)
        if node.changing:
            self.sr.changing.state = uiconst.UI_DISABLED
            self.hint = localization.GetByLabel('UI/Fleet/FleetWindow/MemberChanging')
            self.sr.changing.Play()
        else:
            self.hint = None
            self.sr.changing.Stop()
            self.sr.changing.state = uiconst.UI_HIDDEN
        self.sr.label.Update()

    def GetHeight(_self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 4
        return node.height

    def GetDragData(self, *args):
        selectedNodes = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        for eachNode in selectedNodes:
            info = cfg.eveowners.Get(eachNode.itemID)
            eachNode.info = info

        return selectedNodes

    def OnDropData(self, dragObject, droppedGuys, *args):
        isFlatView = settings.user.ui.Get('flatFleetView', False)
        if isFlatView:
            self.movingHilite.display = False
            return
        try:
            sm.GetService('fleet').OnDropCommanderDropData(dragObject, droppedGuys, self.sr.node)
        finally:
            self.movingHilite.display = False

    def OnDragEnter(self, dragObj, nodes):
        draggedGuy = nodes[0]
        if self.sr.node.itemID == draggedGuy.charID:
            return
        isMultiMove = len(nodes) > 1
        canMove = sm.GetService('fleet').CanMoveToThisEntry(draggedGuy, self.sr.node, 'fleetMember', groupID=None, isMultiMove=isMultiMove)
        if canMove == CONNOT_BE_MOVED_INCOMPATIBLE:
            return
        if canMove == CANNOT_BE_MOVED:
            self.movingHilite.SetRGB(*COLOR_CANNOT_BE_MOVED)
        else:
            self.movingHilite.SetRGB(*COLOR_CAN_ONLY_BE_MEMBER)
        self.movingHilite.display = True

    def OnDragExit(self, dragObj, nodes):
        self.movingHilite.display = False

    def GetMenu(self):
        return GetFleetMemberMenuOptions(self.sr.node.charID)

    def OnMouseDown(self, *args):
        charID = self.sr.node.charID
        if sm.GetService('menu').TryExpandActionMenu(itemID=charID, clickedObject=self, radialMenuClass=uicls.RadialMenuSpaceCharacter):
            return

    @classmethod
    def GetCopyData(cls, node):
        sublevel = node.Get('isSub', 0)
        indent = ' ' * sublevel * 4
        return indent + node.label

    GetMenu = uiutil.ParanoidDecoMethod(GetMenu, ('sr', 'node'))


class FleetAction(Action):
    __guid__ = 'xtriui.FleetAction'

    def Prepare_(self, icon = None):
        pass

    def Startup(self, hint, iconPath):
        self.sr.icon = self.icon = GlowSprite(texturePath=iconPath, parent=self, align=uiconst.CENTER, pos=(1, 0, 16, 16), state=uiconst.UI_DISABLED)
        self.hint = hint
        self.sr.fill = uiprimitives.Fill(parent=self, state=uiconst.UI_HIDDEN, top=0, left=0, width=self.width, height=self.height, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))

    def OnMouseMove(self, *args):
        pass

    def GetHint(self, *args):
        return self.hint

    def LoadTooltipPanel(self, tooltipPanel, *args):
        pass


class FleetChannels(uiprimitives.Container):
    __guid__ = 'xtriui.FleetChannels'
    __notifyevents__ = ['OnVoiceChannelJoined',
     'OnVoiceChannelLeft',
     'OnVoiceSpeakingChannelSet',
     'OnMyFleetInfoChanged',
     'OnSessionChanged',
     'OnMemberMuted_Local',
     'OnSpeakingEvent',
     'OnFleetActive_Local',
     'OnWingActive_Local',
     'OnSquadActive_Local',
     'OnFleetJoin_Local',
     'OnFleetLeave_Local']
    __dependencies__ = ['vivox', 'fleet']

    def Startup(self):
        self.name = 'channelspanel'
        sm.RegisterNotify(self)
        self.buttons = {}
        self.speakingChannelButton = None
        row = uiprimitives.Container(name='channelButtonsContainer', parent=self, align=uiconst.TOTOP, height=18, padTop=2, padRight=2, padLeft=3)
        self.buttonsContainer = uiprimitives.Container(name='buttonsContainer', parent=row, align=uiconst.TORIGHT, width=0)
        self.bonusIconContainer = uiprimitives.Container(name='bonusIconContainer', parent=row, align=uiconst.TOLEFT, width=18)
        uiprimitives.Fill(parent=self.buttonsContainer, left=2, top=2, width=2, height=2, state=uiconst.UI_DISABLED, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))
        uiprimitives.Fill(parent=self.buttonsContainer, left=2, top=5, width=2, height=2, state=uiconst.UI_DISABLED, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))
        uiprimitives.Fill(parent=self.buttonsContainer, left=2, top=8, width=2, height=2, state=uiconst.UI_DISABLED, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))
        uiprimitives.Fill(parent=self.buttonsContainer, left=32, top=2, width=2, height=2, state=uiconst.UI_DISABLED, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))
        uiprimitives.Fill(parent=self.buttonsContainer, left=32, top=5, width=2, height=2, state=uiconst.UI_DISABLED, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))
        uiprimitives.Fill(parent=self.buttonsContainer, left=62, top=2, width=2, height=2, state=uiconst.UI_DISABLED, align=uiconst.RELATIVE, color=(1, 1, 1, 0.5))
        self.roleIconsContainer = uiprimitives.Container(name='roleIconsContainer', parent=row, align=uiconst.TOLEFT)
        self.InitButtons()
        self.UpdateBonusIcon()
        self.UpdateRoleIcons()
        self.UpdateButtons()

    def OnSpeakingEvent(self, charID, channelID, isSpeaking):
        if int(charID) == session.charid and self.speakingChannelButton:
            self.speakingChannelButton.SetSpeakingIndicator(isSpeaking)

    def UpdateRoleIcons(self):
        info = sm.GetService('fleet').GetMemberInfo(session.charid)
        if info is None:
            return
        roleMap = {const.fleetRoleLeader: {'id': 'ui_73_16_17',
                                 'hint': localization.GetByLabel('UI/Fleet/Ranks/FleetCommander')},
         const.fleetRoleWingCmdr: {'id': 'ui_73_16_18',
                                   'hint': localization.GetByLabel('UI/Fleet/Ranks/WingCommander')},
         const.fleetRoleSquadCmdr: {'id': 'ui_73_16_19',
                                    'hint': localization.GetByLabel('UI/Fleet/Ranks/SquadCommander')}}
        jobMap = {const.fleetJobCreator: {'id': 'ui_73_16_20',
                                 'hint': localization.GetByLabel('UI/Fleet/Ranks/Boss')}}
        boosterMap = {const.fleetBoosterFleet: {'id': 'ui_73_16_22',
                                   'hint': localization.GetByLabel('UI/Fleet/Ranks/FleetBooster')},
         const.fleetBoosterWing: {'id': 'ui_73_16_23',
                                  'hint': localization.GetByLabel('UI/Fleet/Ranks/WingBooster')},
         const.fleetBoosterSquad: {'id': 'ui_73_16_24',
                                   'hint': localization.GetByLabel('UI/Fleet/Ranks/SquadBooster')}}
        icons = []
        if info.role in [const.fleetRoleLeader, const.fleetRoleWingCmdr, const.fleetRoleSquadCmdr]:
            icons.append(roleMap[info.role])
        if info.job & const.fleetJobCreator:
            icons.append(jobMap[const.fleetJobCreator])
        if info.booster in [const.fleetBoosterFleet, const.fleetBoosterWing, const.fleetBoosterSquad]:
            icons.append(boosterMap[info.booster])
        UpdateRoleIcons(self.roleIconsContainer, icons)

    def InitButtons(self):
        buttonNames = ['fleet',
         'wing',
         'squad',
         'op1',
         'op2']
        for name in buttonNames:
            b = self.buttons.get(name, None)
            if b is None:
                b = ChannelsPanelAction()
                b.Startup(self.buttonsContainer, name)
                self.buttons[name] = b
            b.Clear()

    def UpdateButtons(self):
        self.InitButtons()
        self.speakingChannelButton = None
        channels = sm.GetService('fleet').GetVoiceChannels()
        for name, data in channels.iteritems():
            if data is None:
                continue
            button = self.buttons[name]
            button.channelID = data.name
            button.SetAsJoined()
            if data.state == CHANNELSTATE_SPEAKING:
                self.speakingChannelButton = button

    def UpdateBonusIcon(self):
        squadActive = wingActive = fleetActive = False
        activeStatus = sm.GetService('fleet').GetActiveStatus()
        if not activeStatus:
            return
        fleetActive = activeStatus.fleet
        squadID = session.squadid
        wingID = session.wingid
        if squadID > 0:
            squadActive = activeStatus.squads.get(squadID, None)
        if wingID > 0:
            wingActive = activeStatus.wings.get(wingID, None)
        log.LogInfo('UpdateBonusIcon() - FLEET:', fleetActive, '- WING:', wingActive, '- SQUAD:', squadActive)
        amIActive = False
        hint = ''
        if session.fleetrole == const.fleetRoleLeader:
            if fleetActive > 0:
                amIActive = True
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/GivingBonusFleet')
            elif fleetActive == fleetcommon.FLEET_STATUS_TOOFEWWINGS:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusFleetTooFew')
            elif fleetActive == fleetcommon.FLEET_STATUS_TOOMANYWINGS:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusFleetTooMany')
        elif session.fleetrole == const.fleetRoleWingCmdr:
            if wingActive > 0:
                amIActive = True
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/GivingBonusWing')
            elif wingActive == fleetcommon.WING_STATUS_TOOMANYSQUADS:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusWing')
            elif wingActive == fleetcommon.WING_STATUS_TOOFEWMEMBERS:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusFleetTooFew')
        elif session.fleetrole == const.fleetRoleSquadCmdr:
            if squadActive > 0:
                amIActive = True
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/GivingBonusSquad')
            elif squadActive == SQUAD_STATUS_NOSQUADCOMMANDER:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusSquadNoCmdr')
            elif squadActive == SQUAD_STATUS_TOOMANYMEMBERS:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusSquadTooMany')
            elif squadActive == SQUAD_STATUS_TOOFEWMEMBERS:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGivingBonusSquadTooFew')
        elif squadActive > 0:
            amIActive = True
            if wingActive > 0:
                if fleetActive > 0:
                    hint = localization.GetByLabel('UI/Fleet/FleetWindow/GettingBonusFromSquadWingFleet')
                else:
                    hint = localization.GetByLabel('UI/Fleet/FleetWindow/GettingBonusFromSquadWing')
            else:
                hint = localization.GetByLabel('UI/Fleet/FleetWindow/GettingBonusFromSquad')
        elif squadActive == SQUAD_STATUS_NOSQUADCOMMANDER:
            hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGettingBonusNoSquadCmdr')
        elif squadActive == SQUAD_STATUS_TOOMANYMEMBERS:
            hint = localization.GetByLabel('UI/Fleet/FleetWindow/NotGettingBonusTooManyMembers')
        elif squadActive == SQUAD_STATUS_TOOFEWMEMBERS:
            pass
        icon = 'ui_38_16_193' if amIActive else 'ui_38_16_194'
        lastHint = getattr(self, 'bonusIconHint', '')
        setattr(self, 'bonusIconHint', hint)
        if hasattr(self, 'bonusIcon'):
            self.bonusIcon.Close()
        self.bonusIcon = uicontrols.Icon(icon=icon, parent=self.bonusIconContainer, size=16, align=uiconst.RELATIVE)
        if lastHint != getattr(self, 'bonusIconHint', ''):
            sm.GetService('ui').BlinkSpriteA(self.bonusIcon, 1.0, 400, 10, passColor=0)
        self.bonusIcon.hint = hint

    def OnVoiceChannelJoined(self, channelID):
        self.UpdateButtons()

    def OnVoiceChannelLeft(self, channelID):
        self.UpdateButtons()

    def OnVoiceSpeakingChannelSet(self, channelID, oldChannelID):
        self.UpdateButtons()

    def OnMyFleetInfoChanged(self):
        self.UpdateRoleIcons()
        self.UpdateBonusIcon()

    def OnMemberMuted_Local(self, charID, channel, isMuted):
        if charID == session.charid:
            self.UpdateButtons()

    def OnFleetActive_Local(self, isActive):
        self.UpdateBonusIcon()

    def OnWingActive_Local(self, wingID, isActive):
        self.UpdateBonusIcon()

    def OnSquadActive_Local(self, squadID, isActive):
        self.UpdateBonusIcon()

    def OnSessionChanged(self, isRemote, sess, change):
        if not self.destroyed:
            self.UpdateRoleIcons()

    def OnFleetJoin_Local(self, rec):
        self.UpdateBonusIcon()

    def OnFleetLeave_Local(self, rec):
        self.UpdateBonusIcon()


class ChannelsPanelAction(uiprimitives.Container):
    __guid__ = 'xtriui.ChannelsPanelAction'

    def Startup(self, parent, name):
        self.name = name
        self.channelID = None
        self.channelState = CHANNELSTATE_NONE
        if name.startswith('op'):
            width = 21
            iconLeft = 3
        else:
            width = 28
            iconLeft = 8
        left = parent.width
        parent.width += width + 2
        self.container = uiprimitives.Container(name=name + '_button', align=uiconst.TOPLEFT, width=width, height=18, top=0, left=left, state=uiconst.UI_NORMAL, parent=parent)
        self.frame = uicontrols.Frame(parent=self.container, color=(1.0, 1.0, 1.0, 0.3))
        self.fill = uiprimitives.Fill(parent=self.container, state=uiconst.UI_DISABLED, color=(1, 1, 1, 0.02))
        self.sr.icon = uicontrols.Icon(icon='ui_73_16_36', parent=self.container, pos=(iconLeft,
         1,
         16,
         16), align=uiconst.TOPLEFT, idx=0, state=uiconst.UI_DISABLED)
        self.container.OnClick = self.OnChannelButtonClicked
        self.container.GetMenu = self.OnChannelButtonGetMenu
        self.container.OnMouseEnter = self.OnChannelButtonMouseEnter
        self.container.OnMouseExit = self.OnChannelButtonMouseExit
        self.SetAsUnavailable()

    def OnChannelButtonGetMenu(self, *etc):
        m = []
        state = sm.GetService('fleet').GetVoiceChannelState(self.channelID)
        if state in [CHANNELSTATE_LISTENING, CHANNELSTATE_SPEAKING, CHANNELSTATE_MAYSPEAK]:
            m.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/LeaveChannel'), sm.GetService('vivox').LeaveChannel, (self.channelID,)))
            m.append(None)
        wings = sm.GetService('fleet').wings
        wingids = wings.keys()
        wingids.sort()
        if self.name == 'fleet' and sm.GetService('vivox').IsVoiceChannel(('fleetid', session.fleetid)) == False:
            label = uiutil.MenuLabel('UI/Fleet/FleetWindow/JoinNamedChannel', {'channelName': localization.GetByLabel('UI/Fleet/Fleet')})
            m.append((label, sm.GetService('vivox').JoinChannel, (('fleetid', session.fleetid),)))
        elif self.name == 'wing':
            for i in range(len(wingids)):
                wid = wingids[i]
                w = wings[wid]
                if sm.GetService('fleet').CanIJoinChannel('wing', wid):
                    if sm.GetService('vivox').IsVoiceChannel(('wingid', wid)) == False:
                        name = w.name
                        if not name:
                            name = localization.GetByLabel('UI/Fleet/DefaultWingName', wingNumber=i + 1)
                        label = uiutil.MenuLabel('UI/Fleet/FleetWindow/JoinNamedChannel', {'channelName': name})
                        m.append((label, sm.GetService('vivox').JoinChannel, (('wingid', wid),)))
                i += 1

        elif self.name == 'squad':
            squadids = []
            squadNames = {}
            i = 1
            for i in range(len(wingids)):
                wid = wingids[i]
                w = wings[wid]
                for sid, s in w.squads.iteritems():
                    squadids.append(sid)
                    name = s.name
                    squadNames[sid] = name
                    i += 1

            squadids.sort()
            for i in range(len(squadids)):
                sid = squadids[i]
                if sm.GetService('fleet').CanIJoinChannel('squad', sid) and sm.GetService('vivox').IsVoiceChannel(('squadid', sid)) == False:
                    name = squadNames[sid]
                    if not name:
                        name = localization.GetByLabel('UI/Fleet/DefaultSquadName', squadNumber=i + 1)
                    label = uiutil.MenuLabel('UI/Fleet/FleetWindow/JoinNamedChannel', {'channelName': name})
                    m.append((label, sm.GetService('vivox').JoinChannel, (('squadid', sid),)))

        elif self.name.startswith('op'):
            import copy
            if not util.IsNPC(session.corpid) and not sm.GetService('vivox').IsVoiceChannel((('corpid', session.corpid),)):
                label = uiutil.MenuLabel('UI/Fleet/FleetWindow/JoinNamedChannel', {'channelName': localization.GetByLabel('UI/Common/Corporation')})
                m.append((label, sm.GetService('vivox').JoinChannel, (('corpid', session.corpid),)))
            if session.allianceid and not sm.GetService('vivox').IsVoiceChannel((('allianceid', session.allianceid),)):
                label = uiutil.MenuLabel('UI/Fleet/FleetWindow/JoinNamedChannel', {'channelName': localization.GetByLabel('UI/Common/Alliance')})
                m.append((label, sm.GetService('vivox').JoinChannel, (('allianceid', session.allianceid),)))
            channels = copy.copy(settings.char.ui.Get('lscengine_mychannels', []))
            for c in channels:
                channel = sm.services['LSC'].channels.get(c, None)
                if channel is None or channel.info and channel.info.mailingList:
                    continue
                if type(channel.channelID) is int and channel.channelID < 1000 and channel.channelID > 0:
                    continue
                name = ''
                ownerID = None
                if channel.info:
                    ownerID = channel.info.ownerID
                    name = channel.info.displayName
                if ownerID not in (session.allianceid, session.corpid) and not sm.GetService('vivox').IsVoiceChannel(channel.channelID):
                    label = uiutil.MenuLabel('UI/Fleet/FleetWindow/JoinNamedChannel', {'channelName': name})
                    m.append((label, sm.GetService('vivox').JoinChannel, (channel.channelID,)))

        return m

    def Clear(self):
        self.SetAsUnavailable()

    def OnChannelButtonMouseEnter(self, *etc):
        self.fill.color.a = 0.3

    def OnChannelButtonMouseExit(self, *etc):
        self.fill.color.a = 0.0

    def OnChannelButtonClicked(self, *etc):
        if self.channelState == CHANNELSTATE_MAYSPEAK:
            sm.GetService('vivox').SetSpeakingChannel(self.channelID)
        elif self.channelState == CHANNELSTATE_SPEAKING:
            sm.GetService('vivox').SetSpeakingChannel(None)

    def SetAsUnavailable(self):
        self.sr.icon.LoadIcon('ui_73_16_36')
        self.channelState = CHANNELSTATE_NONE
        self.container.hint = self.GetChannelNotSetHint()
        self.channelID = None

    def SetAsJoined(self):
        if sm.GetService('vivox').GetSpeakingChannel() == self.channelID:
            self.SetAsSpeaking()
            return
        if FleetSvc().IsVoiceMuted(self.channelID):
            self.SetAsMuted()
            return
        self.sr.icon.LoadIcon('ui_73_16_35')
        self.channelState = CHANNELSTATE_MAYSPEAK
        displayName = chat.GetDisplayName(self.channelID)
        self.container.hint = localization.GetByLabel('UI/Fleet/FleetWindow/SetAsSpeakingChannelHint', channelName=displayName)

    def SetAsSpeaking(self):
        self.sr.icon.LoadIcon('ui_73_16_33')
        self.channelState = CHANNELSTATE_SPEAKING
        displayName = chat.GetDisplayName(self.channelID)
        self.container.hint = localization.GetByLabel('UI/Fleet/FleetWindow/SpeakingInChannelHint', channelName=displayName)

    def SetAsMuted(self):
        self.sr.icon.LoadIcon('ui_73_16_37')
        displayName = chat.GetDisplayName(self.channelID)
        self.container.hint = localization.GetByLabel('UI/Fleet/FleetWindow/MutedInChannelHint', channelName=displayName)

    def SetSpeakingIndicator(self, incomingVoice):
        if incomingVoice:
            self.sr.icon.LoadIcon('ui_73_16_34')
        else:
            self.sr.icon.LoadIcon('ui_73_16_33')

    def GetChannelNotSetHint(self):
        channelType = {'fleet': localization.GetByLabel('UI/Fleet/Fleet'),
         'wing': localization.GetByLabel('UI/Fleet/Wing'),
         'squad': localization.GetByLabel('UI/Fleet/Squad'),
         'op1': localization.GetByLabel('UI/Fleet/FleetWindow/OptionalChannel'),
         'op2': localization.GetByLabel('UI/Fleet/FleetWindow/OptionalChannel')}[self.name]
        hint = localization.GetByLabel('UI/Fleet/FleetWindow/ChannelNotSet', channelType=channelType)
        return hint


class WatchListPanel(ActionPanel):
    __guid__ = 'form.WatchListPanel'
    __notifyevents__ = ['OnSpeakingEvent',
     'OnFleetFavoriteAdded',
     'OnFleetFavoriteRemoved',
     'OnFleetMemberChanged_Local',
     'DoBallsAdded',
     'DoBallRemove',
     'OnFleetBroadcast_Local',
     'OnMyFleetInfoChanged',
     'DoBallsRemove']
    __dependencies__ = ['vivox', 'fleet']
    default_windowID = 'watchlistpanel'

    @staticmethod
    def default_top(*args):
        topRight_TopOffset = uicontrols.Window.GetTopRight_TopOffset()
        if topRight_TopOffset is not None:
            return topRight_TopOffset
        return 16

    @staticmethod
    def default_left(*args):
        return uicore.desktop.width - WatchListPanel.default_width - 16

    def IsFavorite(self, charid):
        if sm.GetService('fleet').GetFavorite(charid):
            return True
        else:
            return False

    def AddBroadcastIcon(self, charid, icon, hint):
        if not self.IsFavorite(charid):
            return
        self.broadcasts[charid] = util.KeyVal(icon=icon, hint=hint, timestamp=blue.os.GetWallclockTime())
        for eachNode in self.sr.scroll.GetNodes():
            if eachNode.charID != charid:
                continue
            if eachNode.charID in self.broadcasts:
                eachNode.icon = self.broadcasts[eachNode.charID].icon
                eachNode.hint = localization.GetByLabel('UI/Fleet/Watchlist/WatchlistHintWithBroadcast', role=fleetbr.GetRankName(eachNode.member), broadcast=self.broadcasts[eachNode.charID].hint, time=self.broadcasts[eachNode.charID].timestamp)
            else:
                eachNode.icon = None
                eachNode.hint = localization.GetByLabel('UI/Fleet/Watchlist/WatchlistHint', role=fleetbr.GetRankName(eachNode.member))
            if eachNode.panel:
                eachNode.panel.Load(eachNode)

    def OnFleetBroadcast_Local(self, broadcast):
        if broadcast.name not in fleetbr.types:
            icon = 'ui_38_16_70'
        else:
            icon = fleetbr.types[broadcast.name]['smallIcon']
        self.AddBroadcastIcon(broadcast.charID, icon, broadcast.broadcastLabel)

    def ClearBroadcastHistory(self):
        self.broadcasts = {}
        self.UpdateAll()

    def OnMyFleetInfoChanged(self):
        self.UpdateAll()

    def PostStartup(self):
        self.scope = 'all'
        self.name = 'watchlistpanel'
        self.broadcasts = {}
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main)
        self.sr.scroll.sr.content.OnDropData = self.DropInWatchList
        self.SetHeaderIcon()
        self.SetMinSize((256, 50))
        hicon = self.sr.headerIcon
        hicon.GetMenu = self.GetWatchListMenu
        hicon.expandOnLeft = 1

    def GetWatchListMenu(self):
        ret = []
        if FleetSvc().IsDamageUpdates():
            ret.append((localization.GetByLabel('UI/Fleet/Watchlist/TurnOffDamageUpdates'), self.SetDamageUpdates, (False,)))
        else:
            ret.append((localization.GetByLabel('UI/Fleet/Watchlist/TurnOnDamageUpdates'), self.SetDamageUpdates, (True,)))
        ret.append((localization.GetByLabel('UI/Fleet/Watchlist/ClearWatchList'), sm.GetService('fleet').RemoveAllFavorites))
        ret.append((localization.GetByLabel('UI/Fleet/Watchlist/ClearBroadcastIcons'), self.ClearBroadcastHistory))
        return ret

    def SetDamageUpdates(self, isit):
        FleetSvc().SetDamageUpdates(isit)
        self.UpdateAll()

    def UpdateAll(self):
        self.sr.scroll.Clear()
        favorites = sm.GetService('fleet').GetFavorites()
        entries = []
        for character in favorites:
            data = self.GetEntryData(character.charID)
            if data is not None:
                entries.append(listentry.Get('WatchListEntry', data=data))

        self.sr.scroll.AddEntries(-1, entries)
        if self.panelname:
            self.SetCaption('%s [%s]' % (self.panelname, len(entries)))

    def OnFleetFavoriteAdded(self, charIDs):
        self.UpdateAll()

    def OnFleetFavoriteRemoved(self, charID):
        if self.destroyed:
            return
        self.UpdateAll()

    def OnFleetMemberChanged_Local(self, charID, *args):
        if sm.GetService('fleet').GetFavorite(charID):
            self.UpdateAll()

    def DoBallsAdded(self, lst):
        for ball, slimItem in lst:
            if ball.id < destiny.DSTLOCALBALLS:
                return
            if sm.GetService('fleet').GetFavorite(slimItem.charID):
                member = self.GetEntryData(slimItem.charID)
                self.UpdateAll()

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if slimItem is None:
            return
        if getattr(slimItem, 'charID', None):
            if sm.GetService('fleet').GetFavorite(slimItem.charID):
                member = self.GetEntryData(slimItem.charID)
                self.UpdateAll()

    def GetEntryData(self, charID):
        slimItem = util.SlimItemFromCharID(charID)
        data = util.KeyVal()
        member = sm.GetService('fleet').GetMemberInfo(charID)
        if not member:
            return
        data.charRec = cfg.eveowners.Get(charID)
        data.itemID = data.id = data.charID = charID
        data.typeID = data.charRec.typeID
        data.squadID = member.squadID
        data.wingID = member.wingID
        data.displayName = member.charName
        data.roleString = member.roleName
        data.voiceStatus = CHANNELSTATE_NONE
        data.channelName = None
        data.label = localization.GetByLabel('UI/Common/CharacterNameLabel', charID=charID)
        data.member = member
        data.slimItem = None
        if charID in self.broadcasts:
            data.icon = self.broadcasts[charID].icon
            data.hint = localization.GetByLabel('UI/Fleet/Watchlist/WatchlistHintWithBroadcast', role=fleetbr.GetRankName(member), broadcast=self.broadcasts[charID].hint, time=self.broadcasts[charID].timestamp)
        else:
            data.icon = None
            data.hint = localization.GetByLabel('UI/Fleet/Watchlist/WatchlistHint', role=fleetbr.GetRankName(member))
        if slimItem:
            data.slimItem = _weakref.ref(slimItem)
        return data

    def DropInWatchList(self, dragObj, nodes, idx = None, *args):
        if dragObj.__guid__ == 'listentry.WatchListEntry':
            if len(nodes) != 1:
                return
            self.Move(dragObj, nodes, idx)
        else:
            charIDsToAdd = []
            for eachNode in nodes:
                textlinkCharID = GetCharIDFromTextLink(eachNode)
                if textlinkCharID:
                    itemID = textlinkCharID
                elif eachNode.__guid__ == 'uicontrols.Label':
                    itemID = self.GetLabelCharID(dragObj, eachNode)
                elif eachNode.__guid__ == 'listentry.FleetCompositionEntry':
                    itemID = eachNode.charID
                elif eachNode.__guid__ in uiutil.AllUserEntries():
                    itemID = eachNode.itemID
                else:
                    continue
                if not FleetSvc().IsFavorite(itemID):
                    charIDsToAdd.append(itemID)

            if charIDsToAdd:
                FleetSvc().AddFavorite(charIDsToAdd)
                if idx is not None and len(charIDsToAdd) == 1:
                    self.Move(dragObj, nodes, idx)

    def Move(self, dragObj, entries, idx = None, *args):
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        selected = self.sr.scroll.GetSelected()
        charID = entries[0].itemID
        if not charID:
            charID = self.GetLabelCharID(dragObj, entries[0])
        if not charID:
            return
        if idx is not None:
            if selected:
                selected = selected[0]
                if idx != selected.idx:
                    if selected.idx < idx:
                        newIdx = idx - 1
                    else:
                        newIdx = idx
                else:
                    return
            else:
                newIdx = idx
        else:
            newIdx = len(self.sr.scroll.GetNodes()) - 1
        sm.GetService('fleet').ChangeFavoriteSorting(charID, newIdx)
        self.UpdateAll()

    def GetLabelCharID(self, dragObj, entry):
        if dragObj.__guid__ == 'uicontrols.Label':
            labelInfo = entry.url.split('//')
            try:
                charID = int(labelInfo[1])
            except:
                return None

            isCharacter = util.IsCharacter(charID)
            if isCharacter:
                return charID
            else:
                return None


class WatchListEntry(BaseTacticalEntry):
    __guid__ = 'listentry.WatchListEntry'
    __notifyevents__ = ['OnSpeakingEvent']
    isDragObject = True

    def Startup(self, *args, **kw):
        BaseTacticalEntry.Startup(self, *args, **kw)
        self.sr.posIndicatorCont = uiprimitives.Container(name='posIndicator', parent=self, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, height=2)
        self.sr.posIndicator = uiprimitives.Fill(parent=self.sr.posIndicatorCont, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.posIndicator.state = uiconst.UI_HIDDEN
        idx = self.sr.label.parent.children.index(self.sr.label)
        gaugesContainer = uiprimitives.Container(name='gaugesContainer', parent=self, width=85, align=uiconst.TORIGHT)
        labelContainer = uiprimitives.Container(name='labelContainer', parent=self, align=uiconst.TOALL, clipChildren=True)
        self.sr.label.SetParent(labelContainer)
        self.sr.gaugesContainer = gaugesContainer
        uiprimitives.Line(parent=self, align=uiconst.TORIGHT)
        broadcastIconContainer = uiprimitives.Container(name='broadcastIconContainer', parent=self, width=20, align=uiconst.TORIGHT)
        self.sr.icon = uicontrols.Icon(parent=broadcastIconContainer, pos=(1, 1, 16, 16), align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED)
        self.broadcastIconContainer = broadcastIconContainer
        self.voiceStatus = CHANNELSTATE_NONE
        self.isSpeaking = False
        progress = uicls.AnimSprite(icons=[ 'ui_38_16_%s' % (210 + i) for i in xrange(8) ], align=uiconst.TOPLEFT, parent=self, pos=(2, 0, 16, 16))
        progress.state = uiconst.UI_HIDDEN
        self.sr.progress = progress

    def Load(self, node):
        listentry.Generic.Load(self, node)
        data = node
        self.sr.label.left = 25
        self.UpdateDamage()
        selected, = sm.GetService('state').GetStates(data.itemID, [state.selected])
        if selected:
            self.Select()
        if node.icon is None:
            self.sr.icon.display = False
        else:
            self.sr.icon.LoadIcon(node.icon)
            self.sr.icon.display = True
        self.sr.label.Update()

    def UpdateDamage(self):
        if not sm.GetService('fleet').IsDamageUpdates():
            self.HideDamageDisplay()
            return False
        if BaseTacticalEntry.UpdateDamage(self):
            i = 0
            startCol = (self.sr.label.color.r, self.sr.label.color.g, self.sr.label.color.b)
            while i < 10:
                fadeToCol = (1.0, 0.2, 0.2)
                c = startCol
                if not self or self.destroyed:
                    return
                if (self.sr.label.color.r, self.sr.label.color.g, self.sr.label.color.b) == startCol:
                    c = fadeToCol
                    fadeToCol = startCol
                sm.GetService('ui').FadeRGB(fadeToCol, c, self.sr.label, time=500.0)
                i += 1

    def GetShipID(self):
        if not self.sr.node:
            return
        else:
            known = self.sr.node.Get('slimItemID', None)
            if known:
                return known
            item = util.SlimItemFromCharID(self.sr.node.charID)
            if item is None:
                return
            self.sr.node.slimItemID = item.itemID
            return item.itemID

    def GetHeight(_self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 4
        return node.height

    def OnClick(self, *args):
        item = util.SlimItemFromCharID(self.sr.node.charID)
        if item:
            uicore.cmd.ExecuteCombatCommand(item.itemID, uiconst.UI_CLICK)

    def OnMouseDown(self, *args):
        charID = self.sr.node.charID
        if sm.GetService('menu').TryExpandActionMenu(itemID=charID, clickedObject=self, radialMenuClass=uicls.RadialMenuSpaceCharacter):
            return

    def GetMenu(self):
        return GetFleetMemberMenuOptions(self.sr.node.charID)

    def InitGauges(self):
        parent = self.sr.gaugesContainer
        if getattr(self, 'gaugesInited', False):
            self.sr.gaugeParent.state = uiconst.UI_DISABLED
            return
        barw, barh = (24, 8)
        borderw = 2
        barsw = (barw + borderw) * 3 + borderw
        par = uiprimitives.Container(name='gauges', parent=parent, align=uiconst.TORIGHT, width=barsw + 2, height=0, left=0, top=0, idx=0)
        self.sr.gauges = []
        l = 2
        for each in ('SHIELD', 'ARMOR', 'STRUCT'):
            g = uiprimitives.Container(name=each, align=uiconst.CENTERLEFT, width=barw, height=barh, left=l)
            g.name = 'gauge_%s' % each.lower()
            uicontrols.Frame(parent=g)
            g.sr.bar = uiprimitives.Fill(parent=g, align=uiconst.TOLEFT)
            uiprimitives.Fill(parent=g, color=(158 / 256.0,
             11 / 256.0,
             14 / 256.0,
             1.0))
            par.children.append(g)
            self.sr.gauges.append(g)
            setattr(self.sr, 'gauge_%s' % each.lower(), g)
            l += barw + borderw

        self.sr.gaugeParent = par
        self.gaugesInited = True

    def GetDragData(self, *args):
        info = cfg.eveowners.Get(self.sr.node.itemID)
        self.sr.node.info = info
        self.sr.node.scroll.SelectNode(self.sr.node)
        return [self.sr.node]

    def OnDropData(self, dragObj, nodes, *args):
        if len(nodes) > 1:
            return
        if util.GetAttrs(self, 'parent', 'OnDropData'):
            self.parent.OnDropData(dragObj, nodes, idx=self.sr.node.idx)

    def OnDragEnter(self, dragObj, nodes, *args):
        if len(nodes) > 1:
            return
        charID = nodes[0].charID
        if not charID and dragObj.__guid__ == 'uicontrols.DragContainerCore':
            node = nodes[0]
            if not util.GetAttrs(node, 'url'):
                charID = None
            if node.url is None:
                charID = None
            else:
                labelInfo = node.url.split('//')
            try:
                labelCharID = int(labelInfo[1])
            except:
                labelCharID = None
                charID = None

            if labelCharID:
                isCharacter = util.IsCharacter(labelCharID)
                if isCharacter:
                    charID = labelCharID
                else:
                    charID = None
        if not charID:
            return
        if self.sr.node.charID == charID:
            return
        if nodes[0].__guid__ == 'listentry.WatchListEntry':
            self.sr.posIndicator.state = uiconst.UI_DISABLED
        if sm.GetService('fleet').CheckCanAddFavorite(charID):
            self.sr.posIndicator.state = uiconst.UI_DISABLED

    def OnDragExit(self, *args):
        self.sr.posIndicator.state = uiconst.UI_HIDDEN


def GetFleetMemberMenuOptions(charID):
    shipItem = util.SlimItemFromCharID(charID)
    if shipItem is None:
        ret = []
    else:
        wantedOptions = ['UI/Inflight/LockTarget',
         'UI/Inflight/ApproachObject',
         'UI/Inflight/OrbitObject',
         'UI/Inflight/Submenus/KeepAtRange',
         'UI/Fleet/JumpThroughToSystem']
        ret = [ entry for entry in sm.GetService('menu').CelestialMenu(shipItem.itemID) if entry and isinstance(entry[0], uiutil.MenuLabel) and entry[0][0] in wantedOptions ]
        ret.append(None)
    filterFunc = [uiutil.MenuLabel('UI/Fleet/Fleet'), uiutil.MenuLabel('UI/Commands/ShowInfo')]
    ret += sm.GetService('menu').FleetMenu(charID, unparsed=False)
    ret += [None] + [(uiutil.MenuLabel('UI/Common/Pilot'), ('isDynamic', sm.GetService('menu').CharacterMenu, (charID,
        [],
        None,
        0,
        filterFunc)))]
    return ret
