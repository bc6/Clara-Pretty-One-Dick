#Embedded file name: eve/client/script/ui/shared\addressBookWindow.py
"""
Main people and places window
"""
import blue
import uicontrols
import form
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.listgroup import ListGroup
from sensorsuite.overlay.bookmarkvisibilitymanager import bookmarkVisibilityManager
import uthread
import carbonui.const as uiconst
from eve.client.script.ui.control import entries as listentry
import uiutil
import util
import eve.client.script.ui.util.searchUtil as searchUtil
import localization
from evePathfinder.core import IsUnreachableJumpCount
DEFAULT_SEARCH_STYLE = const.searchByPartialTerms

class AddressBookWindow(uicontrols.Window):
    """
    TODO: Move window setup here instead of doing it inside the service  
    """
    __guid__ = 'form.AddressBook'
    default_width = 500
    default_height = 400
    default_minSize = (320, 307)
    default_windowID = 'addressbook'
    default_captionLabelPath = 'UI/PeopleAndPlaces/PeopleAndPlaces'
    default_descriptionLabelPath = 'Tooltips/Neocom/PeopleAndPlaces_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/peopleandplaces.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        uthread.new(sm.GetService('bookmarkSvc').UpdateFoldersToDB)
        uicore.registry.GetLockedGroup('agentgroups', 'all', localization.GetByLabel('UI/PeopleAndPlaces/AllAgents'))
        self.inited = 0
        self.semaphore = uthread.Semaphore((self.windowID, 0))
        self.SetCaption(localization.GetByLabel('UI/PeopleAndPlaces/PeopleAndPlaces'))
        self.SetTopparentHeight(52)
        self.SetWndIcon(self.iconNum, mainTop=-3)
        self.SetScope('station_inflight')
        self.sr.main = uiutil.GetChild(self, 'main')
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.contacts = form.ContactsForm(name='contactsform', parent=self.sr.main, pos=(0, 0, 0, 0))
        self.sr.bookmarkbtns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/PeopleAndPlaces/AddBookmark'),
          self.BookmarkCurrentLocation,
          (),
          81], [localization.GetByLabel('UI/PeopleAndPlaces/CreateFolder'),
          self.CreateFolder,
          (),
          81]], parent=self.sr.main, idx=0)
        self.sr.agentbtns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/PeopleAndPlaces/CreateFolder'),
          self.AddGroup,
          'agentgroups',
          81], [localization.GetByLabel('UI/AgentFinder/AgentFinder'),
          uicore.cmd.OpenAgentFinder,
          'agentgroups',
          81]], parent=self.sr.main, idx=0)
        self.sr.hint = None
        grplst = [[localization.GetByLabel('UI/Common/Any'), -1],
         [localization.GetByLabel('UI/Journal/JournalWindow/Agents/HeaderAgent'), const.searchResultAgent],
         [localization.GetByLabel('UI/Common/Character'), const.searchResultCharacter],
         [localization.GetByLabel('UI/Common/Corporation'), const.searchResultCorporation],
         [localization.GetByLabel('UI/Common/Alliance'), const.searchResultAlliance],
         [localization.GetByLabel('UI/Common/Faction'), const.searchResultFaction],
         [localization.GetByLabel('UI/Common/LocationTypes/Station'), const.searchResultStation],
         [localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'), const.searchResultSolarSystem],
         [localization.GetByLabel('UI/Common/LocationTypes/Constellation'), const.searchResultConstellation],
         [localization.GetByLabel('UI/Common/LocationTypes/Region'), const.searchResultRegion]]
        self.sr.sgroup = group = uicontrols.Combo(label=localization.GetByLabel('UI/Common/SearchType'), parent=self.sr.topParent, options=grplst, name='addressBookComboSearchType', select=settings.user.ui.Get('ppSearchGroup', -1), width=86, left=74, top=20, callback=self.ChangeSearchGroup)
        self.sr.inpt = inpt = uicontrols.SinglelineEdit(name='search', parent=self.sr.topParent, maxLength=100, left=group.left + group.width + 6, top=group.top, width=86, label=localization.GetByLabel('UI/PeopleAndPlaces/SearchString'))
        btn = uicontrols.Button(parent=self.sr.topParent, label=localization.GetByLabel('UI/Common/Buttons/Search'), pos=(inpt.left + inpt.width + 2,
         inpt.top,
         0,
         0), func=self.Search, btn_default=1)
        self.sr.searchBy = searchBy = uicontrols.Combo(label=localization.GetByLabel('UI/Common/SearchBy'), parent=self.sr.topParent, options=searchUtil.searchByChoices, name='addressBookComboSearchBy', select=settings.user.ui.Get('ppSearchBy', DEFAULT_SEARCH_STYLE), width=233, left=75, top=inpt.top + inpt.height + 2, labelleft=group.left + group.width + 6 - 75, callback=self.ChangeSearchBy)
        self.SetTopparentHeight(max(52, searchBy.top + searchBy.height))
        self.sr.scroll.sr.content.OnDropData = self.OnDropData
        idx = settings.user.tabgroups.Get('addressbookpanel', None)
        if idx is None:
            settings.user.tabgroups.Set('addressbookpanel', 4)
        tabs = [[localization.GetByLabel('UI/PeopleAndPlaces/Contacts'),
          self.sr.contacts,
          self,
          'contact',
          None], [localization.GetByLabel('UI/PeopleAndPlaces/Agents'),
          self.sr.scroll,
          self,
          'agents',
          None], [localization.GetByLabel('UI/PeopleAndPlaces/Places'),
          self.sr.scroll,
          self,
          'places',
          None]]
        maintabs = uicontrols.TabGroup(name='tabparent', align=uiconst.TOTOP, height=18, parent=self.sr.main, idx=0, tabs=tabs, groupID='addressbookpanel', autoselecttab=True)
        maintabs.sr.Get('%s_tab' % localization.GetByLabel('UI/PeopleAndPlaces/Agents'), None).OnTabDropData = self.DropInAgents
        maintabs.sr.Get('%s_tab' % localization.GetByLabel('UI/PeopleAndPlaces/Contacts'), None).OnTabDropData = self.DropInPersonalContact
        self.placesHeaders = [localization.GetByLabel('UI/PeopleAndPlaces/Label'),
         localization.GetByLabel('UI/Common/Type'),
         localization.GetByLabel('UI/PeopleAndPlaces/Jumps'),
         localization.GetByLabel('UI/PeopleAndPlaces/Sol'),
         localization.GetByLabel('UI/PeopleAndPlaces/Con'),
         localization.GetByLabel('UI/PeopleAndPlaces/Reg'),
         localization.GetByLabel('UI/Common/Date'),
         localization.GetByLabel('UI/PeopleAndPlaces/Creator')]
        self.sr.maintabs = maintabs
        self.inited = 1

    def DropInAgents(self, *args):
        sm.GetService('addressbook').DropInAgents(*args)

    def DropInPersonalContact(self, *args):
        sm.GetService('addressbook').DropInPersonalContact(*args)

    def DropInPlacesGroup_Agent(self, listID_groupID, nodes, *args):
        pass

    def DropInPlacesGroup(self, groupID, nodes, *args):
        sectionID, folderID = groupID
        if sectionID == 'myPlaces':
            ownerID = session.charid
        elif sectionID == 'corpPlaces':
            ownerID = session.corpid
        else:
            return
        itemIDsToBookmark = []
        bookmarkIDsToMove = set()
        bookmarkSvc = sm.GetService('bookmarkSvc')
        for node in nodes:
            guid = getattr(node, '__guid__', None)
            if guid in ('xtriui.InvItem', 'listentry.InvItem') and node.rec.typeID == const.typeBookmark and node.rec.ownerID in (session.charid, session.corpid):
                itemIDsToBookmark.append(node.rec.itemID)
            elif guid == 'listentry.PlaceEntry':
                if node.bm is not None:
                    bookmarkIDsToMove.add(node.bm.bookmarkID)

        if ownerID in (session.charid, session.corpid):
            if len(itemIDsToBookmark) > 0:
                for i in range(0, len(itemIDsToBookmark), const.maxBookmarkCopies):
                    bookmarkBatch = itemIDsToBookmark[i:i + const.maxBookmarkCopies]
                    self._AddBookmarksFromVoucher(bookmarkBatch, ownerID, folderID, bookmarkSvc)
                    if len(itemIDsToBookmark) > const.maxBookmarkCopies:
                        blue.pyos.synchro.SleepSim(600)

        if bookmarkIDsToMove:
            bookmarkSvc.MoveBookmarksToFolder(ownerID, folderID, bookmarkIDsToMove)
        self.RefreshWindow()

    def _AddBookmarksFromVoucher(self, bookmarkIDs, ownerID, folderID, bookmarkSvc):
        bookmarkSvc.LogInfo('_AddBookmarksFromVoucher', bookmarkIDs, ownerID, folderID)
        bookmarkRows = sm.GetService('sessionMgr').PerformSessionLockedOperation('bookmarking', sm.RemoteSvc('bookmark').AddBookmarksFromVoucher, bookmarkIDs, ownerID, folderID, violateSafetyTimer=True)
        for bookmark in bookmarkRows:
            bookmarkSvc.OnBookmarkAdd(bookmark, refresh=0)

        bookmarkSvc.RefreshWindow()

    def OnGroupDeleted(self, *args):
        sm.GetService('addressbook').OnGroupDeleted(*args)

    def DropInBuddyGroup(self, *args):
        sm.GetService('addressbook').DropInBuddyGroup(*args)

    def OnDropData(self, dragObj, nodes):
        self.ShowLoad()
        try:
            visibletab = self.sr.maintabs.GetVisible(1)
            if visibletab and hasattr(visibletab, 'OnTabDropData'):
                visibletab.OnTabDropData(dragObj, nodes)
        finally:
            if self is not None and not self.destroyed and self.inited:
                self.HideLoad()

    def BookmarkCurrentLocation(self, *args):
        sm.GetService('addressbook').BookmarkCurrentLocation(*args)

    def AddGroup(self, listID, *args):
        uicore.registry.AddListGroup(listID)
        self.RefreshWindow()

    def RefreshWindow(self):
        if not self.destroyed and self.inited:
            if getattr(self.sr, 'maintabs', None) is not None:
                self.sr.maintabs.ReloadVisible()

    def _OnClose(self, *args):
        uicore.registry.GetLockedGroup('agentgroups', 'all', localization.GetByLabel('UI/PeopleAndPlaces/AllAgents'))

    def ChangeSearchGroup(self, entry, header, value, *args):
        settings.user.ui.Set('ppSearchGroup', value)

    def ChangeSearchBy(self, entry, header, value, *args):
        settings.user.ui.Set('ppSearchBy', value)

    def Search(self, *args):
        groupID = settings.user.ui.Get('ppSearchGroup', -1)
        if groupID == -1:
            groupIDList = [const.searchResultAgent,
             const.searchResultCharacter,
             const.searchResultCorporation,
             const.searchResultAlliance,
             const.searchResultFaction,
             const.searchResultStation,
             const.searchResultSolarSystem,
             const.searchResultConstellation,
             const.searchResultRegion]
        else:
            groupIDList = [groupID]
        exactSearch = settings.user.ui.Get('ppSearchBy', DEFAULT_SEARCH_STYLE)
        searchUtil.Search(self.sr.inpt.GetValue().strip(), groupIDList, exact=exactSearch, searchWndName='addressBookSearch')

    def Load(self, args):
        uthread.Lock(self, 'load')
        try:
            self.sr.bookmarkbtns.state = uiconst.UI_HIDDEN
            self.sr.agentbtns.state = uiconst.UI_HIDDEN
            self.sr.scroll.sr.iconMargin = 0
            self.sr.scroll.sr.id = '%sAddressBookScroll' % args
            self.sr.scroll.sr.fixedColumns = [{'name': 64}, {}][args == 'places']
            self.sr.scroll.sr.ignoreTabTrimming = not args == 'places'
            if args == 'agents':
                self.ShowAgents()
            elif args == 'places':
                self.ShowPlaces()
            elif args == 'contact':
                self.ShowContacts('contact')
            elif args == 'corpcontact':
                self.ShowContacts('corpcontact')
            elif args == 'alliancecontact':
                self.ShowContacts('alliancecontact')
            self.lastTab = args
        finally:
            uthread.UnLock(self, 'load')

    def ShowContacts(self, contactType):
        if getattr(self, 'contactsIniting', 0):
            return
        if not getattr(self, 'contactsInited', 0):
            self.contactsIniting = 1
            self.sr.contacts.Setup('contact')
            self.contactsInited = 1
            self.contactsIniting = 0
        contactsForm = self.sr.contacts
        contactsForm.LoadContactsForm(contactType)

    def ShowAgents(self):
        self.sr.agentbtns.state = uiconst.UI_PICKCHILDREN
        scrollData = self._GetAgentScrollData()
        scrolllist = []
        for s in scrollData:
            data = {'GetSubContent': self.GetAgentsSubContent,
             'DropData': self.DropInBuddyGroup,
             'RefreshScroll': self.RefreshWindow,
             'label': s.label,
             'id': s.id,
             'groupItems': s.groupItems,
             'headers': [localization.GetByLabel('UI/Common/Name')],
             'iconMargin': 18,
             'showlen': 1,
             'state': s.state,
             'npc': True,
             'allowCopy': 1,
             'showicon': s.logo,
             'allowGuids': uiutil.AllUserEntries()}
            sortBy = s.sortBy
            scrolllist.append((sortBy.lower(), listentry.Get('Group', data)))

        self.sr.scroll.sr.iconMargin = 18
        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.scroll.Load(contentList=scrolllist, fixedEntryHeight=None, headers=[localization.GetByLabel('UI/Common/Name')], scrolltotop=not getattr(self, 'personalshown', 0), noContentHint=localization.GetByLabel('UI/PeopleAndPlaces/NoAgents'))
        setattr(self, 'personalshown', 1)
        if not self.destroyed:
            self.HideLoad()

    def _GetAgentScrollData(self):
        agents = sm.GetService('addressbook').GetAgents()
        scrollData = []
        groups = uicore.registry.GetListGroups('agentgroups')
        for g in groups.iteritems():
            key = g[0]
            data = util.KeyVal(g[1])
            if key == 'all':
                data.sortBy = ['  1', '  2'][key == 'allcorps']
                data.groupItems = agents
            else:
                data.sortBy = data.label
                data.state = None
                data.groupItems = filter(lambda charID: charID in agents, data.groupItems)
            data.logo = 'res:/UI/Texture/WindowIcons/agent.png'
            scrollData.append(data)

        return scrollData

    def ShowPlaces(self):
        self.semaphore.acquire()
        try:
            self.ShowLoad()
            try:
                self.sr.bookmarkbtns.state = uiconst.UI_PICKCHILDREN
                locations = []
                for bm in sm.GetService('bookmarkSvc').GetAllBookmarks().itervalues():
                    if bm.itemID is not None:
                        locations.append(bm.itemID)
                    if bm.locationID is not None:
                        locations.append(bm.locationID)

                if len(locations):
                    cfg.evelocations.Prime(locations, 0)
                scrolllist = self.GetSectionList(session.charid)
                if not util.IsNPCCorporation(session.corpid):
                    scrolllist.extend(self.GetSectionList(session.corpid))
                scrolllist.extend(self.GetAgentPlacesScrollList())
                self.sr.scroll.sr.iconMargin = 18
                scrollToProportion = 0
                if getattr(self, 'lastTab', '') == 'places':
                    scrollToProportion = self.sr.scroll.GetScrollProportion()
                self.sr.scroll.Load(contentList=scrolllist, fixedEntryHeight=None, headers=self.placesHeaders, scrollTo=scrollToProportion, noContentHint=localization.GetByLabel('UI/PeopleAndPlaces/NoKnownPlaces'))
            finally:
                if not self.destroyed:
                    self.HideLoad()

        finally:
            self.semaphore.release()

    def GetAgentPlacesScrollList(self):
        """Assemble the agent bookmarks and generate scrolllist for them"""
        missiongroupState = uicore.registry.GetListGroupOpenState(('missiongroups', 'agentmissions'))
        agentGroup = uicore.registry.GetLockedGroup('missiongroups', 'agentmissions', localization.GetByLabel('UI/PeopleAndPlaces/AgentMissions'), openState=missiongroupState)
        places = sm.GetService('bookmarkSvc').GetAgentBookmarks()
        data = {'GetSubContent': self.GetPlacesSubContent_AgentMissions,
         'RefreshScroll': self.RefreshWindow,
         'label': agentGroup['label'],
         'id': agentGroup['id'],
         'groupItems': places,
         'headers': self.placesHeaders,
         'showlen': 0,
         'state': 'locked',
         'allowGuids': ['listentry.PlaceEntry', 'xtriui.InvItem', 'listentry.InvItem'],
         'showicon': 'hide'}
        groupEntry = listentry.Get('Group', data)
        scrolllist = []
        localization.util.Sort(scrolllist, key=lambda x: x.label)
        return [groupEntry] + scrolllist

    def GetPlacesSubContent_AgentMissions(self, nodedata, newitems = 0):
        if newitems:
            nodedata.groupItems = sm.GetService('bookmarkSvc').GetAgentBookmarks()
        agentMenu = sm.GetService('journal').GetMyAgentJournalBookmarks()
        scrolllist = []
        headers = [localization.GetByLabel('UI/PeopleAndPlaces/Label'),
         localization.GetByLabel('UI/Common/Type'),
         localization.GetByLabel('UI/Common/Date'),
         localization.GetByLabel('UI/PeopleAndPlaces/Sol'),
         localization.GetByLabel('UI/PeopleAndPlaces/Con'),
         localization.GetByLabel('UI/PeopleAndPlaces/Reg')]
        if agentMenu:
            for missionNameID, bms, agentID in agentMenu:
                if bms:
                    if isinstance(missionNameID, basestring):
                        missionName = missionNameID
                    else:
                        missionName = localization.GetByMessageID(missionNameID)
                    missionID = unicode(missionNameID) + unicode(agentID)
                    data = {'GetSubContent': self.GetPlacesSubContent_AgentMissions2,
                     'DropData ': self.DropInPlacesGroup_Agent,
                     'RefreshScroll': self.RefreshWindow,
                     'label': missionName,
                     'id': (missionID, missionName),
                     'groupItems': nodedata.groupItems,
                     'headers': headers,
                     'iconMargin': 18,
                     'showlen': 0,
                     'state': 'locked',
                     'sublevel': 1,
                     'showicon': 'hide',
                     'allowGuids': ['listentry.PlaceEntry', 'xtriui.InvItem', 'listentry.InvItem']}
                    scrolllist.append(listentry.Get('Group', data))

        return scrolllist

    def GetPlacesSubContent_AgentMissions2(self, nodedata, newitems = 0):
        if newitems:
            nodedata.groupItems = sm.GetService('bookmarkSvc').GetAgentBookmarks()
        groupID = nodedata.id
        places = [ bm for bm in nodedata.groupItems.itervalues() if bm.missionName == groupID[0] ]
        return self.GetPlacesScrollList(places, groupID, sublevel=2)

    def GetSectionList(self, ownerID):
        if ownerID == session.charid:
            label = localization.GetByLabel('UI/PeopleAndPlaces/PersonalLocations')
            groupKey = 'myPlaces'
            bookmarks = sm.GetService('bookmarkSvc').GetMyBookmarks()
            count = '[%d]' % len(bookmarks)
        elif ownerID == session.corpid:
            label = localization.GetByLabel('UI/PeopleAndPlaces/CorporationLocations')
            groupKey = 'corpPlaces'
            bookmarks = sm.GetService('bookmarkSvc').GetCorpBookmarks()
            count = '[%d/%d]' % (len(bookmarks), const.maxCorpBookmarkCount)
        data = {'GetSubContent': self.GetPlacesFolders,
         'DropData': self.DropInPlacesGroup,
         'label': label,
         'posttext': count,
         'id': (groupKey, None),
         'groupItems': bookmarks,
         'ownerID': ownerID,
         'state': 'locked',
         'showicon': 'hide',
         'showlen': False,
         'allowGuids': ['listentry.PlaceEntry', 'xtriui.InvItem', 'listentry.InvItem']}
        return [listentry.Get('Group', data)]

    def GetFolderEntry(self, folder, groupKey):
        if folder.creatorID is not None:
            label = localization.GetByLabel('UI/PeopleAndPlaces/FolderName', folderName=folder.folderName, creator=folder.creatorID)
        else:
            label = folder.folderName
        data = {'GetSubContent': self.GetPlacesEntries,
         'DropData': self.DropInPlacesGroup,
         'label': label,
         'id': (groupKey, folder.folderID),
         'groupItems': folder.bookmarks,
         'sublevel': 1,
         'folderID': folder.folderID,
         'folder': folder,
         'MenuFunction': self.BookmarkFolderMenu,
         'state': 'locked',
         'showicon': 'hide',
         'allowGuids': ['listentry.PlaceEntry', 'xtriui.InvItem', 'listentry.InvItem']}
        return listentry.Get(decoClass=BookmarkFolderEntry, data=data)

    def GetPlacesEntries(self, nodedata, newitems = 0):
        bookmarkFolders = sm.GetService('bookmarkSvc').GetBookmarksInFoldersForOwner(nodedata.folder.ownerID)
        return self.GetPlacesScrollList(bookmarkFolders[nodedata.folderID].bookmarks, nodedata.folderID, sublevel=2)

    def GetPlacesFolders(self, nodedata, newitems = 0):
        ownerID = nodedata.ownerID
        groupKey = nodedata.id[0]
        bookmarkFolders = sm.GetService('bookmarkSvc').GetBookmarksInFoldersForOwner(ownerID)
        entries = []
        for folder in localization.util.Sort(bookmarkFolders.values(), key=lambda folder: folder.folderName):
            if folder.folderID is not None:
                entries.append(self.GetFolderEntry(folder, groupKey))

        entries.extend(self.GetPlacesScrollList(bookmarkFolders[None].bookmarks, (groupKey, None), sublevel=1))
        return entries

    def BookmarkFolderMenu(self, node):
        return [(localization.GetByLabel('/Carbon/UI/Controls/ScrollEntries/ChangeLabel'), self.EditBookmarkFolder, (node.folderID,)), (localization.GetByLabel('/Carbon/UI/Controls/ScrollEntries/DeleteFolder'), self.DeleteBookmarkFolder, (node.folderID,))]

    def DeleteBookmarkFolder(self, folderID):
        if eve.Message('ConfirmDeleteFolder', {}, uiconst.YESNO, uiconst.ID_YES) == uiconst.ID_YES:
            sm.GetService('bookmarkSvc').DeleteFolder(folderID)

    def EditBookmarkFolder(self, folderID):
        folder = sm.GetService('bookmarkSvc').GetFolder(folderID)
        wnd = form.BookmarkFolderWindow.Open(folder=folder)
        wnd.Maximize()

    def CreateFolder(self, *args):
        wnd = form.BookmarkFolderWindow.Open()
        wnd.Maximize()

    def GetPlacesScrollList(self, places, groupID, sublevel):
        addressbook = sm.GetService('addressbook')
        bookmarkSvc = sm.GetService('bookmarkSvc')
        pathfinder = sm.GetService('clientPathfinderService')
        scrolllist = []
        unreachabelText = localization.GetByLabel('UI/Common/unreachable')
        coordinateText = localization.GetByLabel('UI/PeopleAndPlaces/Coordinate')
        for bookmark in places:
            hint, comment = bookmarkSvc.UnzipMemo(bookmark.memo)
            sol, con, reg = addressbook.GetSolConReg(bookmark)
            typename = cfg.invgroups.Get(cfg.invtypes.Get(bookmark.typeID).groupID).name
            date = util.FmtDate(bookmark.created, 'ls')
            if bookmark and (bookmark.itemID == bookmark.locationID or bookmark.typeID == const.typeSolarSystem) and bookmark.x:
                typename = coordinateText
            jumps = 0
            if 40000000 > bookmark.itemID > 30000000:
                jumps = pathfinder.GetAutopilotJumpCount(session.solarsystemid2, bookmark.itemID)
            elif 40000000 > bookmark.locationID > 30000000:
                jumps = pathfinder.GetAutopilotJumpCount(session.solarsystemid2, bookmark.locationID)
            if IsUnreachableJumpCount(jumps):
                jumps = unreachabelText
            creatorID = getattr(bookmark, 'creatorID', None)
            if creatorID is not None:
                creatorName = cfg.eveowners.Get(creatorID).name
            else:
                creatorName = ''
            text = '<t>'.join((unicode(x) for x in (hint,
             typename,
             jumps,
             sol,
             con,
             reg,
             date,
             creatorName)))
            data = {'bm': bookmark,
             'DropData': lambda *args: self.DropOnBookmark(bookmark, *args),
             'itemID': bookmark.bookmarkID,
             'tabs': [],
             'hint': hint,
             'comment': comment,
             'label': text,
             'sublevel': sublevel,
             'listGroupID': groupID}
            scrolllist.append(listentry.Get('PlaceEntry', data))

        return scrolllist

    def DropOnBookmark(self, bookmark, dragNode, nodes, *args):
        if bookmark.ownerID == session.charid:
            groupKey = ('myPlaces', bookmark.folderID)
        else:
            groupKey = ('corpPlaces', bookmark.folderID)
        self.DropInPlacesGroup(groupKey, nodes)

    def GetAgentsSubContent(self, nodedata, newitems = 0):
        if not len(nodedata.groupItems):
            return []
        charsToPrime = []
        for charID in nodedata.groupItems:
            charsToPrime.append(charID)

        cfg.eveowners.Prime(charsToPrime)
        agents = sm.GetService('addressbook').GetAgents()
        scrolllist = []
        for charID in nodedata.groupItems:
            if charID in agents:
                scrolllist.append(listentry.Get('AgentEntry', {'listGroupID': nodedata.id,
                 'charID': charID,
                 'info': cfg.eveowners.Get(charID)}))

        scrolllist = localization.util.Sort(scrolllist, key=lambda x: x['info'].ownerName)
        return scrolllist


class BookmarkFolderEntry(ListGroup):

    def Startup(self, *etc):
        ListGroup.Startup(self, *etc)
        self.sensorSuite = sm.GetService('sensorSuite')
        self.overlayButton = ButtonIcon(name='overlayButton', parent=self.sr.labelClipper, align=uiconst.CENTERLEFT, width=16, height=16, iconSize=16, left=200, texturePath='res://UI/Texture/classes/SensorSuite/sensor_overlay_small.png', func=self.OnChangeSensorOverlayVisibility)

    def Load(self, node):
        ListGroup.Load(self, node)
        self.folderID = node.folderID
        self.overlayButton.left = self.sr.label.width + self.sr.label.left + 8
        self.SetIsVisible(bookmarkVisibilityManager.IsFolderVisible(node.folderID))

    def OnChangeSensorOverlayVisibility(self):
        isVisible = not bookmarkVisibilityManager.IsFolderVisible(self.folderID)
        bookmarkVisibilityManager.SetFolderVisibility(self.folderID, isVisible)
        self.sensorSuite.UpdateVisibleSites()
        self.SetIsVisible(isVisible)

    def SetIsVisible(self, isVisible):
        if isVisible:
            color = (0.1, 1.0, 0.1, 1.0)
            hint = localization.GetByLabel('UI/PeopleAndPlaces/RemoveLocationFolderFromSensorOverlay')
        else:
            color = util.Color.GetGrayRGBA(1.0, 0.5)
            hint = localization.GetByLabel('UI/PeopleAndPlaces/ShowLocationFolderInSensorOverlay')
        self.overlayButton.icon.SetRGB(*color)
        self.overlayButton.hint = hint
