#Embedded file name: eve/client/script/ui/shared/neocom\channels.py
import uiprimitives
import uicontrols
import uthread
import uix
from eve.client.script.ui.control import entries as listentry
import util
import types
import service
import uiutil
import carbonui.const as uiconst
import fontConst
import localization
from collections import defaultdict

class ChannelsSvc(service.Service):
    __exportedcalls__ = {'Show': [],
     'RefreshMine': []}
    __guid__ = 'svc.channels'
    __notifyevents__ = ['ProcessSessionChange']
    __servicename__ = 'channels'
    __displayname__ = 'Channels Client Service'
    __dependencies__ = []
    __update_on_reload__ = 0

    def Run(self, memStream = None):
        self.LogInfo('Starting Channels')
        self.semaphore = uthread.Semaphore()

    def Stop(self, memStream = None):
        wnd = self.GetWnd()
        if wnd and not wnd.destroyed:
            wnd.Close()

    def ProcessSessionChange(self, isremote, session, change):
        if session.charid is None:
            self.Stop()

    def Show(self):
        wnd = self.GetWnd(1)
        if wnd is not None and not wnd.destroyed:
            wnd.Maximize()

    def GetWnd(self, create = 0):
        if create:
            sm.GetService('tutorial').OpenTutorialSequence_Check(uix.advchannelsTutorial)
            return Channels.Open()
        return Channels.GetIfOpen()

    def SetHint(self, hintstr = None):
        wnd = self.GetWnd()
        if wnd is not None:
            wnd.sr.scroll.ShowHint(hintstr)

    def CreateOrJoinChannel(self, name, doCreate = True):
        s = self.semaphore
        s.acquire()
        try:
            if len(name) > 60:
                raise UserError('ChatCustomChannelNameTooLong', {'max': 60})
            if len(name.split('\\')) > [1, 2][eve.session.role & (service.ROLE_CHTADMINISTRATOR | service.ROLE_GMH) != 0]:
                raise UserError('ChatCustomChannelNameNoSeparators')
            sm.GetService('LSC').CreateOrJoinChannel(name, create=doCreate)
            self.RefreshMine()
        finally:
            s.release()

    def RefreshMine(self, reload = 0):
        wnd = self.GetWnd()
        if wnd and not wnd.destroyed:
            wnd.ShowContent(reload)


class ChannelField(listentry.Generic):
    __guid__ = 'listentry.ChannelField'
    __nonpersistvars__ = ['groupID',
     'status',
     'active',
     'selection',
     'channel']
    isDragObject = True

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        self.joinleaveBtn = uicontrols.Button(parent=self, label=localization.GetByLabel('UI/Chat/ChannelWindow/Join'), func=self.JoinLeaveChannelFromBtn, idx=0, left=2, align=uiconst.CENTERRIGHT)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        if type(self.sr.node.channel.channelID) == types.IntType or self.sr.node.channel.channelID[0][0] in ('global', 'regionid', 'constellationid') or self.sr.node.channel.channelID[0][0] == 'corpid' and self.sr.node.channel.channelID[0][1] != session.corpid:
            self.joinleaveBtn.state = uiconst.UI_NORMAL
            if self.sr.node.isJoined:
                self.joinleaveBtn.SetLabel(localization.GetByLabel('UI/Chat/ChannelWindow/Leave'))
            else:
                self.joinleaveBtn.SetLabel(localization.GetByLabel('UI/Chat/ChannelWindow/Join'))
        else:
            self.joinleaveBtn.state = uiconst.UI_HIDDEN

    def GetHeight(self, *args):
        node, width = args
        btnHeight1 = uix.GetTextHeight(localization.GetByLabel('UI/Chat/ChannelWindow/Leave'), maxLines=1, fontsize=fontConst.EVE_SMALL_FONTSIZE, hspace=1, uppercase=1)
        btnHeight2 = uix.GetTextHeight(localization.GetByLabel('UI/Chat/ChannelWindow/Join'), maxLines=1, fontsize=fontConst.EVE_SMALL_FONTSIZE, hspace=1, uppercase=1)
        if btnHeight1 > btnHeight2:
            node.height = btnHeight1
        else:
            node.height = btnHeight2
        return node.height + 11

    def OnDblClick(self, *args):
        channelID = self.sr.node.channel.channelID
        if type(channelID) != types.IntType and not eve.session.role & (service.ROLE_CHTADMINISTRATOR | service.ROLE_GMH):
            if channelID[0][0] not in ('global', 'regionid', 'constellationid'):
                return
        self.JoinLeaveChannel()

    def GetMenu(self):
        self.OnClick()
        channelID = self.sr.node.channel.channelID
        menu = []
        if type(self.sr.node.channel.channelID) == types.IntType or self.sr.node.channel.channelID[0][0] in ('global', 'regionid', 'constellationid'):
            if sm.GetService('LSC').IsJoined(channelID):
                menu.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/LeaveChannel'), self.JoinLeaveChannel, (channelID,)))
            else:
                menu.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/JoinChannel'), self.JoinLeaveChannel, (channelID,)))
        if sm.GetService('LSC').IsOwner(self.sr.node.channel) or type(channelID) != types.IntType and getattr(channelID, 'ownerID', 0) > 100000000 and sm.GetService('LSC').IsCreator(channelID):
            menu.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/DeleteChannel'), self.DeleteChannel))
        elif sm.GetService('LSC').IsForgettable(channelID):
            menu.append((uiutil.MenuLabel('UI/Chat/ChannelWindow/ForgetChannel'), self.ForgetChannel))
        if type(channelID) == types.IntType and sm.GetService('LSC').IsOperator(channelID):
            menu.append((uiutil.MenuLabel('UI/Chat/Settings'), self.Settings))
        if len(menu):
            return menu

    def Settings(self, *args):
        sm.GetService('LSC').Settings(self.sr.node.channel.channelID)

    def JoinLeaveChannelFromBtn(self, *args):
        self.JoinLeaveChannel()

    def JoinLeaveChannel(self, chID = None, *args):
        channelID = chID if chID != None else self.sr.node.channel.channelID
        self.state = uiconst.UI_DISABLED
        sm.GetService('LSC').JoinOrLeaveChannel(channelID)
        self.state = uiconst.UI_NORMAL

    def DeleteChannel(self, *args):
        self.state = uiconst.UI_DISABLED
        try:
            sm.GetService('LSC').DestroyChannel(self.sr.node.channel)
            sm.GetService('channels').RefreshMine(reload=True)
        finally:
            self.state = uiconst.UI_NORMAL

    DeleteChannel = uiutil.ParanoidDecoMethod(DeleteChannel, ('sr', 'node', 'channel'))

    def ForgetChannel(self, *args):
        self.state = uiconst.UI_DISABLED
        try:
            sm.GetService('LSC').ForgetChannel(self.sr.node.channel.channelID)
            sm.GetService('channels').RefreshMine(reload=True)
        finally:
            self.state = uiconst.UI_NORMAL

    ForgetChannel = uiutil.ParanoidDecoMethod(ForgetChannel, ('sr', 'node', 'channel', 'channelID'))

    def GetDragData(self, *args):
        if isinstance(self.sr.node.channel.channelID, int):
            return [self.sr.node]
        return []


def _RetNameFromMessageID(messageID):
    """
    Use the localization system to convert some (numeric) `messageID` into a string
    -- unless the ID is our CHAT_SYSTEM_CHANNEL "sentinel", which is special.
    """
    if messageID == const.CHAT_SYSTEM_CHANNEL:
        return localization.GetByLabel('UI/Chat/SystemChannels')
    else:
        return localization.GetByMessageID(messageID)


def _RetDetailedChannelName(channel):
    """
    Return the "detailed" name string for use in the "Channels" window.
    
    The Channels window uses longer, more contextual, and more fully localized names,
    e.g. such as "English Help (Help)" instead of the shorter/plainer name "Help"
    which is used as the display name in the Chat window tabs themselves.
    
    See also: the GetDisplayName function in lscengine.py
    
    Refactored out of Channels::ShowContent_thread in an effort to make it clearer.
    """
    if isinstance(channel.channelMessageID, unicode):
        channelName = channel.channelMessageID
    elif channel.displayName is not None:
        channelName = localization.GetByLabel('UI/Chat/ChannelWindow/ChannelWithForienDisplay', msgID=channel.channelMessageID, displayName=channel.displayName)
    else:
        channelName = localization.GetByMessageID(channel.channelMessageID)
    return channelName


def _RetChannelsTree(channels):
    """
    Convert the big list of channels into a shallow "tree" of grouped channels,
    from which we can eventually build a scroll-list for the UI.
    
    Returns a defaultdict of dicts of channels; keyed by groupName and channelName respectively.
    
    
    Each channel is an object-like thing -- in practice, is seems to be either
    a KeyVal or a blue.DBRow object, with fields including:
    
      channelID, groupMessageID, channelMessageID, ownerID, displayName
    
    (You can enumerate the column-named of a DBRow via its __columns__ member.)
    
    Refactored out of Channels::ShowContent_thread in an effort to make it clearer.
    """
    tree = defaultdict(dict)
    myChannels = localization.GetByLabel('UI/Chat/ChannelWindow/MyChannels')
    playerChannels = localization.GetByLabel('UI/Chat/ChannelWindow/PlayerChannels')
    otherChannels = localization.GetByLabel('UI/Chat/ChannelWindow/Other')
    tree[otherChannels] = {}
    for channel in channels:
        if channel.temporary:
            continue
        if channel.groupMessageID:
            groupName = _RetNameFromMessageID(channel.groupMessageID)
            groupName = uiutil.StripTags(groupName, stripOnly=['localized'])
            channelGroup = tree[groupName]
            channelName = _RetDetailedChannelName(channel)
            channelGroup[channelName] = channel
        else:
            if channel.ownerID == const.ownerSystem:
                channelGroup = tree[otherChannels]
                channelName = _RetNameFromMessageID(channel.channelMessageID)
            elif channel.ownerID == eve.session.charid:
                channelGroup = tree[myChannels]
                channelName = channel.displayName
            else:
                channelGroup = tree[playerChannels]
                channelName = channel.displayName
            channelGroup[channelName] = channel

    return tree


class Channels(uicontrols.Window):
    __guid__ = 'form.Channels'
    __neocommenuitem__ = (('Channel window', '51_10'), 'Startup', service.ROLE_GML)
    default_windowID = 'channels'
    default_captionLabelPath = 'UI/Chat/ChannelWindow/Channels'
    default_descriptionLabelPath = 'Tooltips/Neocom/ChatChannels_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/chatchannels.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.loadingShowcontent = 0
        self.SetScope('station_inflight')
        self.SetMinSize([400, 250])
        self.SetWndIcon('res:/ui/Texture/WindowIcons/chatchannels.png')
        self.SetTopparentHeight(70)
        self.sr.inpt = inpt = uicontrols.SinglelineEdit(name='input', parent=self.sr.topParent, maxLength=60, left=74, top=20, width=86, label=localization.GetByLabel('UI/Chat/ChannelWindow/Channels'))
        joinBtn = uicontrols.Button(parent=self.sr.topParent, label=localization.GetByLabel('UI/Chat/ChannelWindow/Join'), pos=(inpt.left,
         inpt.top + inpt.height + 4,
         0,
         0), func=self.JoinChannelFromBtn, args='self', btn_default=1)
        createBtn = uicontrols.Button(parent=self.sr.topParent, label=localization.GetByLabel('UI/Chat/ChannelWindow/Create'), pos=(joinBtn.left + joinBtn.width + 2,
         joinBtn.top,
         0,
         0), func=self.CreateChannelFromBtn, args='self')
        self.sr.inpt.width = max(100, joinBtn.left + joinBtn.width - inpt.left)
        channelsMaillist = uiprimitives.Container(name='channelsMaillist', parent=self.sr.main, left=const.defaultPadding, top=const.defaultPadding, width=const.defaultPadding, height=const.defaultPadding)
        self.sr.scroll = uicontrols.Scroll(parent=channelsMaillist)
        self.sr.scroll.multiSelect = 0
        self.ShowContent()

    def ShowContent(self, reload = 1):
        uthread.new(self.ShowContent_thread, reload).context = 'Channels::ShowContent'

    def ShowContent_thread(self, reload = 1):
        """
        A threaded worker function which creates the scrollable treelist thingy in which
        all of the available chat channels are listed.
        """
        if getattr(self, 'loadingShowcontent', 0):
            return
        self.loadingShowcontent = 1
        try:
            channels = sm.GetService('LSC').GetChannels(reload)
            tree = _RetChannelsTree(channels)
            if not self or self.destroyed:
                return
            scrolllist = self.__BuildTreeList(tree)
            h = [localization.GetByLabel('UI/Chat/ChannelWindow/Name'), localization.GetByLabel('UI/Chat/ChannelWindow/Members')]
            self.sr.scroll.Load(fixedEntryHeight=24, contentList=scrolllist, headers=h)
        finally:
            if self and not self.destroyed:
                self.loadingShowcontent = 0

    def __BuildTreeList(self, tree, indent = 0):
        ret = []
        h = [localization.GetByLabel('UI/Chat/ChannelWindow/Name'), localization.GetByLabel('UI/Chat/ChannelWindow/Members')]
        guid = 'ChannelField'
        lscSvc = sm.StartService('LSC')
        for k, v in tree.iteritems():
            if isinstance(v, dict):
                data = {'GetSubContent': self.__GetSubContent,
                 'RefreshScroll': self.RefreshMine,
                 'label': k,
                 'sublevel': indent,
                 'id': ('CHANNELSchannels', k),
                 'groupItems': (indent, v),
                 'headers': h,
                 'iconMargin': 18,
                 'showlen': 0,
                 'state': 'locked',
                 'allowCopy': 0,
                 'showicon': 'res:/UI/Texture/WindowIcons/member.png',
                 'posttext': localization.GetByLabel('UI/Chat/NumChannels', numChannels=len(v)),
                 'allowGuids': ['listentry.Group', 'listentry.%s' % guid]}
                ret.append((k, listentry.Get('Group', data)))
            else:
                data = util.KeyVal()
                data.channel = v
                if v.estimatedMemberCount:
                    emc = localization.formatters.FormatNumeric(v.estimatedMemberCount)
                    data.label = '%s<t>%s' % (k, emc)
                else:
                    data.label = '%s<t>' % (k,)
                data.genericDisplayLabel = k
                data.sublevel = indent
                data.isJoined = lscSvc.IsJoined(v.channelID)
                ret.append((k, listentry.Get(guid, data=data)))

        ret.sort()
        ret2 = []
        for each in ret:
            ret2.append(each[1])

        return ret2

    def RefreshMine(self, *args):
        self.ShowContent()

    def __GetSubContent(self, nodedata, newitems = 0):
        indent, sub = nodedata.groupItems
        if not len(sub):
            return []
        return self.__BuildTreeList(sub, indent + 1)

    def CreateChannelFromBtn(self, btn, *args):
        self.CreateOrJoinChannel(btn, create=1)

    def JoinChannelFromBtn(self, btn, *args):
        self.CreateOrJoinChannel(btn, create=0)

    def CreateOrJoinChannel(self, btn, create = 1, *args):
        name = self.sr.inpt.GetValue()
        if name.strip() == '':
            eve.Message('LookupStringMinimum', {'minimum': 1})
            return
        channelID = sm.GetService('LSC').GetChannelIDFromName(name)
        if channelID is not None:
            wnd = uicontrols.Window.GetIfOpen('chatchannel_%s' % channelID)
            if wnd:
                wnd.Maximize()
                eve.Message('LSCChannelIsJoined', {'displayName': name})
                return
        try:
            btn.Disable()
            sm.GetService('channels').CreateOrJoinChannel(name=name, doCreate=create)
        finally:
            if not btn.destroyed:
                btn.Enable()
