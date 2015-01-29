#Embedded file name: eve/client/script/ui/shared/neocom/addressBook\addressbookService.py
import math
import sys
import service
import uiprimitives
import uicontrols
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import Frame
import uthread
import uix
import uiutil
import form
import util
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import uicls
import log
import localization
import telemetry
from eve.client.script.ui.shared.neocom.evemail import ManageLabelsBase

class AddressBookSvc(service.Service):
    __exportedcalls__ = {'AddToPersonal': [],
     'AddToPersonalMulti': [],
     'DeleteEntryMulti': [],
     'GetBookmarks': [],
     'GetSolConReg': [],
     'BookmarkCurrentLocation': [],
     'BookmarkLocationPopup': [],
     'ZipMemo': [],
     'UnzipMemo': [],
     'DeleteBookmarks': [],
     'RefreshWindow': [],
     'IsInAddressBook': [],
     'GetAddressBook': [],
     'IsBlocked': [],
     'GetRelationship': [],
     'GetContactsByMinRelationship': [],
     'AssignLabelFromWnd': [],
     'RemoveLabelFromWnd': []}
    __guid__ = 'svc.addressbook'
    __update_on_reload__ = 0
    __notifyevents__ = ['ProcessSessionChange',
     'OnDestinationSet',
     'OnSessionChanged',
     'OnContactNoLongerContact',
     'OnOrganizationContactsUpdated',
     'OnPersonalContactsUpdated',
     'OnContactSlashCommand',
     'OnRefreshBookmarks',
     'OnAgentAdded']
    __servicename__ = 'addressbook'
    __displayname__ = 'AddressBook Client Service'
    __dependencies__ = ['bookmarkSvc']
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.agents = None
        self.blocked = None
        self.labels = None
        self.corporateLabels = None
        self.allianceLabels = None
        self.contactType = None
        self.contacts = None
        self.corporateContacts = None
        self.allianceContacts = None

    def Run(self, memStream = None):
        self.LogInfo('Starting AddressBook')
        self.Reset()
        if eve.session.charid:
            self.GetContacts()

    def CloseWindow(self):
        form.AddressBook.CloseIfOpen()

    def OnSessionChanged(self, isremote, session, change):
        if 'charid' in change and session.charid:
            self.GetContacts()
            self.RefreshWindow()

    def OnDropData(self, dragObj, nodes):
        wnd = self.GetWnd()
        if wnd is None or wnd.destroyed or not wnd.inited:
            return
        wnd.OnDropData(dragObj, nodes)

    def ProcessSessionChange(self, isremote, session, change):
        if session.charid is None:
            self.CloseWindow()
            self.Reset()
        elif 'solarsystemid' in change:
            self.RefreshWindow()

    def OnContactSlashCommand(self, contactID, level):
        """
            Method to deal with forced contact actions from slash commands on other clients.
        """
        if level is None:
            try:
                self.contacts.pop(contactID)
            except:
                sys.exc_clear()

        elif contactID not in self.contacts:
            contact = util.KeyVal()
            contact.contactID = contactID
            contact.relationshipID = level
            contact.labelMask = 0
            contact.inWatchlist = 0
            self.contacts[contactID] = contact
        else:
            self.contacts[contactID].relationshipID = level
        sm.ScatterEvent('OnContactChange', [contactID], 'contact')

    def OnPersonalContactsUpdated(self, contactIDs, standing, inWatchlist):
        """
            Event signifying one or more of our contacts were edited.
            standing is float, from -10.0 to 10.0, inWatchlist is bool
            both None means the contact was deleted
        """
        if self.contacts is None:
            self.GetContacts()
        onlineContactsToUpdate = []
        for contactID in contactIDs:
            if standing is None and inWatchlist is None:
                contact = self.contacts.pop(contactID, None)
            else:
                try:
                    contact = self.contacts[contactID]
                    contact.relationshipID = standing if standing is not None else contact.relationshipID
                    contact.inWatchlist = inWatchlist if inWatchlist is not None else contact.inWatchlist
                except KeyError as e:
                    sys.exc_clear()
                    contact = util.KeyVal()
                    contact.contactID = contactID
                    contact.relationshipID = standing
                    contact.inWatchlist = inWatchlist
                    contact.labelMask = 0

                self.contacts[contactID] = contact
            if inWatchlist is not None or contact and contact.inWatchlist:
                onlineContactsToUpdate.append(contactID)

        sm.ScatterEvent('OnContactChange', contactIDs, 'contact')
        for contactID in onlineContactsToUpdate:
            if util.IsCharacter(contactID) and not util.IsNPC(contactID):
                isOnline = sm.GetService('onlineStatus').GetOnlineStatus(contactID)
                sm.ScatterEvent('OnClientContactChange', contactID, isOnline)

    def OnOrganizationContactsUpdated(self, ownerID, updates):
        if self.contacts is None:
            self.GetContacts()
        if ownerID == session.corpid:
            contacts = self.corporateContacts
            event = 'OnSetCorpStanding'
        elif ownerID == session.allianceid:
            contacts = self.allianceContacts
            event = 'OnSetAllianceStanding'
        else:
            self.LogError('Invalid ownerID in contact update notification', ownerID, updates)
            return
        for update in updates:
            contactID, level, labelMask = update
            if level is None and labelMask is None:
                try:
                    contacts.pop(contactID)
                except:
                    sys.exc_clear()

            elif contactID not in contacts:
                labelMask = labelMask or 0
                contact = util.KeyVal()
                contact.contactID = contactID
                contact.relationshipID = level
                contact.inWatchlist = 0
                contact.labelMask = labelMask
                contacts[contactID] = contact
            elif labelMask is None:
                contacts[contactID].relationshipID = level
            else:
                contacts[contactID].labelMask = labelMask

        sm.ScatterEvent(event)

    def GetContacts(self):
        uthread.Lock(self, 'contacts')
        try:
            bms = self.bookmarkSvc.GetBookmarks()
            if self.contacts is not None and self.blocked is not None and self.corporateContacts is not None and self.allianceContacts is not None and self.agents is not None and bms is not None:
                return util.KeyVal(contacts=self.contacts, blocked=self.blocked, corpContacts=self.corporateContacts, allianceContacts=self.allianceContacts)
            self.contacts = {}
            self.blocked = {}
            self.corporateContacts = {}
            self.allianceContacts = {}
            self.agents = []
            tmpBlocked = []
            if session.allianceid:
                addressbook, self.corporateContacts, self.allianceContacts, statuses = uthread.parallel([(sm.RemoteSvc('charMgr').GetContactList, ()),
                 (sm.GetService('corp').GetContactList, ()),
                 (sm.GetService('alliance').GetContactList, ()),
                 (sm.GetService('onlineStatus').Prime, ())])
            else:
                addressbook, self.corporateContacts, statuses = uthread.parallel([(sm.RemoteSvc('charMgr').GetContactList, ()), (sm.GetService('corp').GetContactList, ()), (sm.GetService('onlineStatus').Prime, ())])
            for each in addressbook.addresses:
                if util.IsNPC(each.contactID) and util.IsCharacter(each.contactID):
                    if sm.GetService('agents').IsAgent(each.contactID):
                        self.agents.append(each.contactID)
                else:
                    contact = util.KeyVal()
                    contact.contactID = each.contactID
                    contact.inWatchlist = each.inWatchlist
                    contact.relationshipID = each.relationshipID
                    contact.labelMask = each.labelMask
                    self.contacts[each.contactID] = contact

            for each in addressbook.blocked:
                if each.senderID != 0:
                    blocked = util.KeyVal()
                    blocked.contactID = each.senderID
                    self.blocked[each.senderID] = blocked

            cfg.eveowners.Prime(self.blocked.keys())
            cfg.eveowners.Prime(self.contacts.keys())
            cfg.eveowners.Prime(self.corporateContacts)
            cfg.eveowners.Prime(self.allianceContacts)
            cfg.eveowners.Prime(self.agents)
            return util.KeyVal(contacts=self.contacts, blocked=self.blocked, corpContacts=self.corporateContacts, allianceContacts=self.allianceContacts)
        finally:
            uthread.UnLock(self, 'contacts')

    def GetRelationship(self, charID, corporationID, allianceID = None):
        relationships = util.KeyVal()
        relationships.persToPers = const.contactNeutralStanding
        relationships.persToCorp = const.contactNeutralStanding
        relationships.persToAlliance = const.contactNeutralStanding
        relationships.corpToPers = const.contactNeutralStanding
        relationships.corpToCorp = const.contactNeutralStanding
        relationships.corpToAlliance = const.contactNeutralStanding
        relationships.allianceToPers = const.contactNeutralStanding
        relationships.allianceToCorp = const.contactNeutralStanding
        relationships.allianceToAlliance = const.contactNeutralStanding
        relationships.hasRelationship = False
        if charID in self.contacts:
            relationships.persToPers = self.contacts[charID].relationshipID
            relationships.hasRelationship = True
        if corporationID in self.contacts:
            relationships.persToCorp = self.contacts[corporationID].relationshipID
            relationships.hasRelationship = True
        if allianceID is not None and allianceID in self.contacts:
            relationships.persToAlliance = self.contacts[allianceID].relationshipID
            relationships.hasRelationship = True
        if charID in self.corporateContacts:
            relationships.corpToPers = self.corporateContacts[charID].relationshipID
            relationships.hasRelationship = True
        if corporationID in self.corporateContacts:
            relationships.corpToCorp = self.corporateContacts[corporationID].relationshipID
            relationships.hasRelationship = True
        if allianceID in self.corporateContacts:
            relationships.corpToAlliance = self.corporateContacts[allianceID].relationshipID
            relationships.hasRelationship = True
        if charID in self.allianceContacts:
            relationships.allianceToPers = self.allianceContacts[charID].relationshipID
            relationships.hasRelationship = True
        if corporationID in self.allianceContacts:
            relationships.allianceToCorp = self.allianceContacts[corporationID].relationshipID
            relationships.hasRelationship = True
        if allianceID is not None and allianceID in self.allianceContacts:
            relationships.allianceToAlliance = self.allianceContacts[allianceID].relationshipID
            relationships.hasRelationship = True
        return relationships

    def GetContactsByMinRelationship(self, relationshipID):
        contacts = set()
        for contactID, contact in self.contacts.iteritems():
            if contact.relationshipID >= relationshipID:
                contacts.add(contactID)

        for contactID, contact in self.corporateContacts.iteritems():
            if contact.relationshipID >= relationshipID:
                contacts.add(contactID)

        for contactID, contact in self.allianceContacts.iteritems():
            if contact.relationshipID >= relationshipID:
                contacts.add(contactID)

        return contacts

    def OnDestinationSet(self, destinationID):
        self.RefreshWindow()

    def OnContactNoLongerContact(self, charID):
        """
            this is handled elsewhere, but just adding this scatterevent listener here so
            that we know this for the future
        """
        pass

    def OnRefreshBookmarks(self):
        self.RefreshWindow()

    def GetBookmarks(self, *args):
        """
            Returns the real bookmarks, but only locations
        """
        log.LogTraceback('We should call the bookmarkSvc directly')
        return self.bookmarkSvc.GetBookmarks()

    def GetAgents(self, *args):
        return self.agents

    def GetSolConReg(self, bookmark):
        solname = '-'
        conname = '-'
        regname = '-'
        mapSvc = sm.GetService('map')
        sol = None
        con = None
        reg = None
        try:
            if util.IsSolarSystem(bookmark.locationID):
                sol = mapSvc.GetItem(bookmark.locationID)
                con = mapSvc.GetItem(sol.locationID)
                reg = mapSvc.GetItem(con.locationID)
            elif util.IsConstellation(bookmark.locationID):
                sol = mapSvc.GetItem(bookmark.itemID)
                con = mapSvc.GetItem(sol.locationID)
                reg = mapSvc.GetItem(con.locationID)
            elif util.IsRegion(bookmark.locationID):
                con = mapSvc.GetItem(bookmark.itemID)
                reg = mapSvc.GetItem(con.locationID)
            elif bookmark.typeID == const.typeRegion:
                reg = mapSvc.GetItem(bookmark.itemID)
            if sol is not None:
                solname = sol.itemName
            if con is not None:
                conname = con.itemName
            if reg is not None:
                regname = reg.itemName
        finally:
            return (solname, conname, regname)

    def BookmarkCurrentLocation(self, *args):
        wnd = self.GetWnd()
        if wnd:
            text = localization.GetByLabel('UI/PeopleAndPlaces/AddBookmark')
            btn = wnd.sr.bookmarkbtns.GetBtnByLabel(text)
            btn.Disable()
        try:
            if not (session.stationid or session.shipid):
                eve.Message('HavetobeatstationOrinShip')
                return
            if session.stationid:
                stationinfo = sm.RemoteSvc('stationSvc').GetStation(session.stationid)
                self.BookmarkLocationPopup(session.stationid, stationinfo.stationTypeID, session.solarsystemid2)
            elif session.solarsystemid and session.shipid:
                bp = sm.GetService('michelle').GetBallpark()
                if bp is None:
                    return
                slimItem = bp.GetInvItem(session.shipid)
                if slimItem is None:
                    return
                self.BookmarkLocationPopup(session.shipid, slimItem.typeID, session.solarsystemid)
        finally:
            if wnd:
                btn = wnd.sr.bookmarkbtns.GetBtnByLabel(text)
                btn.Enable()

    def CheckLocationID(self, locationID):
        bms = sm.GetService('bookmarkSvc').GetMyBookmarks()
        for bookmark in bms.itervalues():
            if bookmark.itemID == locationID:
                return self.UnzipMemo(bookmark.memo)[0]

    def BookmarkLocationPopup(self, locationid, typeID, parentID, note = None, scannerInfo = None, locationName = None):
        checkavail = self.CheckLocationID(locationid)
        if locationName is None:
            locationName = self.GetDefaultLocationName(locationid, scannerInfo)
        if checkavail and locationid not in (session.shipid, session.solarsystemid):
            if eve.Message('AskProceedBookmarking', {'locationname': cfg.invtypes.Get(typeID).typeName,
             'caption': checkavail}, uiconst.YESNO) != uiconst.ID_YES:
                return
        wnd = form.BookmarkLocationWindow.Open(locationID=locationid, typeID=typeID, parentID=parentID, scannerInfo=scannerInfo, locationName=locationName, note=note)
        uthread.new(uicore.registry.SetFocus, wnd.labelEdit)

    def GetDefaultLocationName(self, locationID, scannerInfo):
        if locationID in (session.solarsystemid, session.shipid):
            if scannerInfo is not None:
                locationName = scannerInfo.name
            else:
                locationName = localization.GetByLabel('UI/PeopleAndPlaces/SpotInSolarSystem', solarSystemName=cfg.evelocations.Get(session.solarsystemid2).name)
        else:
            mapSvc = sm.GetService('map')
            locationName = cfg.evelocations.Get(locationID).name
            locationObj = mapSvc.GetItem(locationID)
            if locationObj:
                locationName = localization.GetByLabel('UI/PeopleAndPlaces/NewBookmarkLocationLabel', loc=locationID, group=cfg.invtypes.Get(locationObj.typeID).name)
            bp = sm.GetService('michelle').GetBallpark()
            if bp:
                slimItem = uix.GetBallparkRecord(locationID)
                if slimItem is not None:
                    if locationName is None or len(locationName) <= 1:
                        locationName = cfg.invtypes.Get(slimItem.typeID).Group().name
                    else:
                        locationName = localization.GetByLabel('UI/PeopleAndPlaces/NewBookmarkLocationLabel', loc=locationID, group=cfg.invtypes.Get(slimItem.typeID).Group().name)
        return locationName

    def UpdateBookmark(self, bookmarkID, ownerID = None, header = None, note = None, folderID = -1):
        """
            Note:  Only supported for locations
        """
        bm = self.GetBookmark(bookmarkID)
        oldheader, oldnote = self.UnzipMemo(bm.memo)
        oldnote = bm.note
        oldFolderID = bm.folderID
        oldOwnerID = bm.ownerID
        if header is None:
            header = oldheader
        if note is None:
            note = oldnote
        if folderID is -1:
            folderID = oldFolderID
        if ownerID is None:
            ownerID = oldOwnerID
        if note == oldnote and header == oldheader and folderID == oldFolderID and ownerID == oldOwnerID:
            return
        memo = self.ZipMemo(header[:100], '')
        if bm.memo != memo or note != oldnote or folderID != oldFolderID or ownerID != oldOwnerID:
            uthread.pool('AddressBook::CorpBookmarkMgr.UpdateBookmark', sm.GetService('bookmarkSvc').UpdateBookmark, bookmarkID, ownerID, memo, note, folderID)

    def BookmarkLocation(self, itemID, name, comment, typeID, locationID = None, folderID = None):
        self.bookmarkSvc.BookmarkLocation(itemID, name, comment, typeID, locationID=locationID, folderID=folderID)

    def GetBookmark(self, bookmarkID):
        return sm.GetService('bookmarkSvc').GetBookmark(bookmarkID)

    def DeleteBookmarks(self, ids, refreshWindow = True, alreadyDeleted = 0):
        if eve.Message('RemoveLocation', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        wnd = self.GetWnd()
        if wnd is not None and not wnd.destroyed:
            wnd.ShowLoad()
        try:
            self.bookmarkSvc.DeleteBookmarks(ids)
        finally:
            if wnd is not None and not wnd.destroyed:
                wnd.HideLoad()

        if refreshWindow:
            self.RefreshWindow()

    def EditBookmark(self, bm):
        if not hasattr(bm, 'note'):
            return
        oldlabel, oldnote = self.UnzipMemo(bm.memo)
        oldnote = bm.note
        return form.BookmarkLocationWindow(bookmark=bm, locationName=oldlabel, note=oldnote)

    def Reset(self):
        self.destinationSetOnce = 0
        self.deleted = []

    @telemetry.ZONE_METHOD
    def RefreshWindow(self):
        wnd = form.AddressBook.GetIfOpen()
        if wnd is not None and not wnd.destroyed and wnd.inited:
            if getattr(wnd.sr, 'maintabs', None) is not None:
                wnd.sr.maintabs.ReloadVisible()

    def DropInAgents(self, dragObj, nodes):
        self.DropInPersonal(nodes, None)

    def DropInPersonalContact(self, dragObj, nodes):
        self.DropInPersonal(nodes, 'contact')

    def DropInPersonal(self, nodes, contactType):
        for what in nodes:
            if getattr(what, '__guid__', None) not in uiutil.AllUserEntries():
                return
            if sm.GetService('agents').IsAgent(what.itemID) and contactType != None:
                eve.Message('CannotAddContactType')
                continue
            elif not sm.GetService('agents').IsAgent(what.itemID) and contactType == None:
                eve.Message('CannotAddContactType2')
                continue
            else:
                self.AddToAddressBook(what.itemID, contactType)

    def DropInBlocked(self, nodes):
        for what in nodes:
            if getattr(what, '__guid__', None) not in uiutil.AllUserEntries():
                return
            if not util.IsOwner(what.itemID) and not util.IsAlliance(what.itemID):
                self.LogWarn('Skipping block item', what.itemID, 'as this item is not a character!')
                continue
            self.BlockOwner(what.itemID)

    def DropInBuddyGroup(self, listID_groupID, nodes, *args):
        ids = []
        for node in nodes:
            if node.Get('__guid__', None) in ('listentry.User', 'listentry.Sender') and node.itemID != session.charid:
                self.AddToPersonal(node.itemID, None, refresh=node == nodes[-1])
            currentListGroupID = node.Get('listGroupID', None)
            ids.append((node.itemID, currentListGroupID, listID_groupID))

        for itemID, currentListGroupID, listID_groupID in ids:
            if currentListGroupID and itemID:
                uicore.registry.RemoveFromListGroup(currentListGroupID, itemID)
            uicore.registry.AddToListGroup(listID_groupID, itemID)

        uicore.registry.ReloadGroupWindow(listID_groupID)
        self.RefreshWindow()

    def GetWnd(self, new = 0):
        if new:
            return form.AddressBook.ToggleOpenClose()
        else:
            return form.AddressBook.GetIfOpen()

    def CheckBoxChange(self, checkbox):
        config = checkbox.data['config']
        if checkbox.data.has_key('value'):
            if checkbox.checked:
                settings.user.ui.Set(config, checkbox.data['value'])
            else:
                settings.user.ui.Set(config, checkbox.checked)
        self.RefreshWindow()

    def OnAgentAdded(self, entityID):
        """
            this is an agent adding itself to my bookmarks
        """
        if entityID in self.agents:
            return
        self.agents.append(entityID)
        sm.GetService('neocom').Blink('addressbook')
        self.RefreshWindow()

    def AddToPersonalMulti(self, charIDs, contactType = None, edit = 0):
        if type(charIDs) != list:
            charIDs = [charIDs]
        for charID in charIDs:
            self.AddToPersonal(charID, contactType=contactType, refresh=charID == charIDs[-1], edit=edit)

    def AddToPersonal(self, charID, contactType, refresh = 1, edit = 0):
        if charID == const.ownerSystem:
            eve.Message('CantbookmarkEveSystem')
            return
        if contactType is None:
            if charID not in self.agents:
                try:
                    character = cfg.eveowners.Get(charID)
                except:
                    log.LogWarn('User trying to bookmark character which is not in the owners table', charID)
                    sys.exc_clear()
                    return

                self.AddToAddressBook(charID, contactType, edit)
        else:
            self.AddToAddressBook(charID, contactType, edit)

    def BlockOwner(self, ownerID):
        if ownerID == session.charid:
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/CannotBlockSelf')})
            return
        if util.IsNPC(ownerID):
            if util.IsCharacter(ownerID):
                eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/CannotBlockAgents')})
            elif util.IsCorporation(ownerID) or util.IsAlliance(ownerID):
                eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/CannotBlockNPCCorps')})
            return
        if ownerID in self.blocked:
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/AlreadyHaveBlocked', userName=cfg.eveowners.Get(ownerID).name)})
            return
        sm.RemoteSvc('charMgr').BlockOwners([ownerID])
        blocked = util.KeyVal()
        blocked.contactID = ownerID
        self.blocked[ownerID] = blocked
        sm.ScatterEvent('OnBlockContacts', [ownerID])
        self.RefreshWindow()

    def UnblockOwner(self, ownerIDs):
        blocked = []
        for ownerID in ownerIDs:
            if ownerID in self.blocked:
                blocked.append(ownerID)
                self.blocked.pop(ownerID)

        if len(blocked):
            sm.RemoteSvc('charMgr').UnblockOwners(blocked)
            sm.ScatterEvent('OnUnblockContacts', blocked)
        self.RefreshWindow()

    def IsBlocked(self, ownerID):
        return ownerID in self.blocked

    def EditContacts(self, contactIDs, contactType):
        wnd = form.ContactManagementMultiEditWnd.Open(windowID='contactmanagement', entityIDs=contactIDs, contactType=contactType)
        if wnd.ShowModal() == 1:
            results = wnd.result
            relationshipID = results
            if contactType == 'contact':
                sm.RemoteSvc('charMgr').EditContactsRelationshipID(contactIDs, relationshipID)
                for contactID in contactIDs:
                    self.contacts[contactID].relationshipID = relationshipID

            elif contactType == 'corpcontact':
                sm.GetService('corp').EditContactsRelationshipID(contactIDs, relationshipID)
                for contactID in contactIDs:
                    self.corporateContacts[contactID].relationshipID = relationshipID

            elif contactType == 'alliancecontact':
                sm.GetService('alliance').EditContactsRelationshipID(contactIDs, relationshipID)
                for contactID in contactIDs:
                    self.allianceContacts[contactID].relationshipID = relationshipID

            sm.ScatterEvent('OnContactChange', [contactIDs], contactType)

    def AddToAddressBook(self, contactID, contactType, edit = 0, labelID = None):
        if contactID == session.charid and contactType == 'contact':
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/CannotAddSelf')})
            return
        if util.IsNPC(contactID) and not sm.GetService('agents').IsAgent(contactID) and util.IsCharacter(contactID):
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/IsNotAnAgent', agentName=cfg.eveowners.Get(contactID).name)})
            return
        if contactType is None and contactID in self.agents:
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/AlreadyAContact', contactName=cfg.eveowners.Get(contactID).name)})
            return
        if contactType == 'contact':
            if contactID in self.contacts and not edit:
                eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/AlreadyAContact', contactName=cfg.eveowners.Get(contactID).name)})
                return
        if contactType == 'corpcontact':
            if contactID in self.corporateContacts and not edit:
                eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/AlreadyACorpContact', contactName=cfg.eveowners.Get(contactID).name)})
                return
        if contactType == 'alliancecontact':
            if contactID in self.allianceContacts and not edit:
                eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/PeopleAndPlaces/AlreadyAnAllianceContact', contactName=cfg.eveowners.Get(contactID).name)})
                return
        inWatchlist = False
        relationshipID = None
        labelMask = 0
        message = None
        if util.IsNPC(contactID) and sm.GetService('agents').IsAgent(contactID):
            sm.RemoteSvc('charMgr').AddContact(contactID)
            self.agents.append(contactID)
            self.RefreshWindow()
        else:
            isContact = self.IsInAddressBook(contactID, contactType)
            if contactType == 'contact':
                windowType = form.ContactManagementWnd
                entityID = contactID
                relationshipID = relationshipID
                wasInWatchlist = inWatchlist
                isContact = isContact
            else:
                windowType = form.CorpAllianceContactManagementWnd
                entityID = contactID
                relationshipID = relationshipID
                wasInWatchlist = None
                isContact = isContact
            if isContact:
                if contactType == 'contact':
                    contact = self.contacts.get(contactID)
                    relationshipID = contact.relationshipID
                    inWatchlist = wasInWatchlist = contact.inWatchlist
                    labelMask = contact.labelMask
                    startupParams = (contactID,
                     relationshipID,
                     inWatchlist,
                     isContact)
                elif contactType == 'corpcontact':
                    contact = self.corporateContacts.get(contactID)
                    relationshipID = contact.relationshipID
                    labelMask = contact.labelMask
                    startupParams = (contactID, relationshipID, isContact)
                elif contactType == 'alliancecontact':
                    contact = self.allianceContacts.get(contactID)
                    relationshipID = contact.relationshipID
                    labelMask = contact.labelMask
                    startupParams = (contactID, relationshipID, isContact)
            wnd = windowType.Open(windowID='contactmanagement', entityID=entityID, level=relationshipID, watchlist=wasInWatchlist, isContact=isContact, contactType=contactType, labelID=labelID)
            if wnd.ShowModal() == 1:
                results = wnd.result
                if contactType == 'contact':
                    relationshipID = results[0]
                    inWatchlist = results[1]
                    sendNotification = results[2]
                    message = results[3]
                    contactLabel = results[4]
                else:
                    relationshipID = results[0]
                    contactLabel = results[1]
                contact = util.KeyVal()
                contact.contactID = contactID
                contact.relationshipID = relationshipID
                contact.inWatchlist = inWatchlist
                contact.labelMask = labelMask
                if contactType == 'contact':
                    if isContact and edit:
                        func = 'EditContact'
                    else:
                        func = 'AddContact'
                    util.CSPAChargedAction('CSPAContactNotifyCheck', sm.RemoteSvc('charMgr'), func, contactID, relationshipID, inWatchlist, sendNotification, message)
                    self.contacts[contactID] = contact
                    if contactLabel is not None:
                        self.AssignLabelFromWnd([contactID], contactLabel)
                elif contactType == 'corpcontact':
                    if isContact and edit:
                        sm.GetService('corp').EditCorporateContact(contactID, relationshipID=relationshipID)
                    else:
                        sm.GetService('corp').AddCorporateContact(contactID, relationshipID=relationshipID)
                    self.corporateContacts[contactID] = contact
                    if contactLabel is not None:
                        self.AssignLabelFromWnd([contactID], contactLabel)
                elif contactType == 'alliancecontact':
                    if isContact and edit:
                        sm.GetService('alliance').EditAllianceContact(contactID, relationshipID=relationshipID)
                    else:
                        sm.GetService('alliance').AddAllianceContact(contactID, relationshipID=relationshipID)
                    self.allianceContacts[contactID] = contact
                    if contactLabel is not None:
                        self.AssignLabelFromWnd([contactID], contactLabel)
                sm.ScatterEvent('OnContactChange', [contactID], contactType)
                if util.IsCharacter(contactID) and not util.IsNPC(contactID) and contact.inWatchlist and contactType == 'contact':
                    isOnline = sm.GetService('onlineStatus').GetOnlineStatus(contactID)
                    if not wasInWatchlist:
                        sm.ScatterEvent('OnContactAddedToWatchlist', contactID, isOnline)
                    sm.ScatterEvent('OnClientContactChange', contactID, isOnline)

    def RemoveFromAddressBook(self, contactIDs, contactType):
        if contactType is None:
            if util.IsNPC(contactIDs) and sm.GetService('agents').IsAgent(contactIDs):
                sm.RemoteSvc('charMgr').DeleteContacts([contactIDs])
                self.agents.remove(contactIDs)
                self.RefreshWindow()
                return
        charnameList = ''
        for contactID in contactIDs:
            charName = cfg.eveowners.Get(contactID).name
            if len(contactIDs) > 1:
                if charnameList == '':
                    charnameList = '%s' % charName
                else:
                    charnameList = '%s, %s' % (charnameList, charName)
            else:
                charnameList = cfg.eveowners.Get(contactID).name

        if len(contactIDs) > 1:
            msg = 'RemoveManyFromContacts'
        else:
            msg = 'RemoveOneFromContacts'
        if contactType == 'contact':
            if eve.Message(msg, {'names': charnameList}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            sm.RemoteSvc('charMgr').DeleteContacts(contactIDs)
        elif contactType == 'corpcontact':
            if eve.Message(msg, {'names': charnameList}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            sm.GetService('corp').RemoveCorporateContacts(contactIDs)
        elif contactType == 'alliancecontact':
            if eve.Message(msg, {'names': charnameList}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            sm.GetService('alliance').RemoveAllianceContacts(contactIDs)
        scatterList = []
        for contactID in contactIDs:
            scatterList.append(contactID)
            if contactType == 'contact':
                if contactID in self.contacts:
                    self.contacts.pop(contactID)
                    if util.IsCharacter(contactID):
                        sm.GetService('onlineStatus').ClearOnlineStatus(contactID)
            elif contactType == 'corpcontact':
                if contactID in self.corporateContacts:
                    self.corporateContacts.pop(contactID)
            elif contactType == 'alliancecontact':
                if contactID in self.allianceContacts:
                    self.allianceContacts.pop(contactID)

        if len(scatterList):
            sm.ScatterEvent('OnContactChange', scatterList, contactType)

    def DeleteEntryMulti(self, charIDs, contactType = None):
        buddygroups = uicore.registry.GetListGroups('buddygroups')
        agentgroups = uicore.registry.GetListGroups('agentgroups')
        if not hasattr(charIDs, '__iter__'):
            charIDs = [charIDs]
        if contactType is None:
            if eve.Message('RemoveAgents', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            for charID in charIDs:
                for listgroup in [agentgroups]:
                    for group in listgroup.itervalues():
                        if not group:
                            continue
                        if charID in group['groupItems']:
                            group['groupItems'].remove(charID)

                self.RemoveFromAddressBook(charID, contactType)

        else:
            self.RemoveFromAddressBook(charIDs, contactType)

    def OnGroupDeleted(self, ids):
        if len(ids):
            self.DeleteBookmarks(ids, 0)

    def ZipMemo(self, *parts):
        return uiutil.Zip(*parts)

    def UnzipMemo(self, s):
        split = uiutil.Unzip(s)
        if len(split) == 1:
            return (split[0], '')
        return split[:2]

    def GetStandingsLevel(self, contactID, contactType):
        if self.IsInAddressBook(contactID, contactType):
            if contactType == 'alliancecontact':
                contact = self.allianceContacts.get(contactID, None)
                if contact is not None:
                    return contact.relationshipID
            if contactType == 'corpcontact':
                contact = self.corporateContacts.get(contactID, None)
                if contact is not None:
                    return contact.relationshipID
            if contactType == 'contact':
                contact = self.contacts.get(contactID, None)
                if contact is not None:
                    return contact.relationshipID

    def IsInAddressBook(self, contactID, contactType):
        if self.contacts is None or self.allianceContacts is None or self.corporateContacts is None:
            self.GetContacts()
        if contactType == 'alliancecontact':
            return contactID in self.allianceContacts
        if contactType == 'corpcontact':
            return contactID in self.corporateContacts
        if contactType == 'contact':
            return contactID in self.contacts or contactID in self.agents

    def GetAddressBook(self):
        return self.contacts.keys()

    def IsInWatchlist(self, ownerID):
        contacts = []
        if self.contacts is None:
            self.GetContacts()
        contact = self.contacts.get(ownerID, None)
        if contact is not None:
            return contact.inWatchlist
        return False

    def GetContactEntry(self, data, contact, onlineOnly = False, dblClick = None, contactType = None, contactLevel = None, labelMask = None, menuFunction = None, extraInfo = None, listentryType = 'User'):
        entryTuple = None
        charinfo = cfg.eveowners.Get(contact.contactID)
        if onlineOnly:
            if self.IsInWatchlist(contact.contactID):
                os = sm.GetService('onlineStatus').GetOnlineStatus(contact.contactID)
                if os:
                    entry = self.GetEntryLine(data, contact, dblClick, contactType, contactLevel, labelMask, listentryType=listentryType)
                    entryTuple = (charinfo.name.lower(), entry)
        else:
            entry = self.GetEntryLine(data, contact, dblClick, contactType, contactLevel, labelMask, menuFunction, extraInfo, listentryType)
            entryTuple = (charinfo.name.lower(), entry)
        return entryTuple

    def GetEntryLine(self, data, contact, dblClick = None, contactType = None, contactLevel = None, labelMask = None, menuFunction = None, extraInfo = None, listentryType = 'User'):
        if data is None:
            data = uiutil.Bunch()
        if data.Get('groupID', None) == const.contactBlocked:
            inWatchlist = False
        else:
            inWatchlist = getattr(contact, 'inWatchlist', False)
        entry = listentry.Get(listentryType, {'listGroupID': data.Get('id', None),
         'charID': contact.contactID,
         'showOnline': inWatchlist,
         'info': cfg.eveowners.Get(contact.contactID),
         'OnDblClick': dblClick,
         'contactType': contactType,
         'contactLevel': contactLevel,
         'labelMask': labelMask,
         'MenuFunction': menuFunction,
         'extraInfo': extraInfo})
        return entry

    def GetNotifications(self, notification):
        label = ''
        senderName = ''
        if notification.senderID is not None:
            senderName = cfg.eveowners.Get(notification.senderID).ownerName
        hint = notification.body.replace('<br><br>', '<br>')
        text = notification.body.split('<br><br>')
        data = util.KeyVal()
        data.label = text[0]
        data.label2 = text[1]
        data.hint = hint
        data.id = notification.notificationID
        data.typeID = notification.typeID
        data.senderID = notification.senderID
        data.data = util.KeyVal(read=notification.processed)
        data.info = notification
        data.ignoreRightClick = 1
        data.Draggable_blockDrag = 1
        entry = listentry.Get('ContactNotificationEntry', data=data)
        return (notification.created, entry)

    def RenameContactLabelFromUI(self, labelID):
        ret = uiutil.NamePopup(localization.GetByLabel('UI/PeopleAndPlaces/LabelsLabelName'), localization.GetByLabel('UI/PeopleAndPlaces/LabelsTypeNewLabelName'), maxLength=const.mailMaxLabelSize, validator=self.CheckLabelName)
        if ret is None:
            return
        name = ret
        name = name.strip()
        if name:
            self.EditContactLabel(labelID, name=name)

    def EditContactLabel(self, labelID, name = None, color = None):
        if name is None and color is None or name == '':
            raise UserError('MailLabelMustProvideName')
        self.GetSvc().EditLabel(labelID, name, color)
        labels = self.GetContactLabels(self.contactType)
        if name is not None:
            if labelID in labels:
                labels[labelID].name = name
        if color is not None:
            if labelID in labels:
                labels[labelID].color = color
        sm.ScatterEvent('OnMyLabelsChanged', self.contactType, None)

    def CreateContactLabel(self, name, color = None):
        labelID = self.GetSvc().CreateLabel(name, color)
        labels = self.GetContactLabels(self.contactType)
        labels[labelID] = util.KeyVal(labelID=labelID, name=name, color=color)
        sm.ScatterEvent('OnMyLabelsChanged', self.contactType, labelID)
        return labelID

    def GetContactLabels(self, contactType):
        """
          Returns a dictionary with all player defined labels
        """
        uthread.Lock(self, 'labels')
        try:
            self.contactType = contactType
            if contactType == 'contact':
                if self.labels is None:
                    self.labels = self.GetSvc().GetLabels()
                return self.labels
            if contactType == 'corpcontact':
                if self.corporateLabels is None:
                    self.corporateLabels = self.GetSvc().GetLabels()
                return self.corporateLabels
            if contactType == 'alliancecontact':
                if self.allianceLabels is None:
                    self.allianceLabels = self.GetSvc().GetLabels()
                return self.allianceLabels
            raise RuntimeError('contact type missing')
        finally:
            uthread.UnLock(self, 'labels')

    def GetSvc(self):
        svc = ''
        if self.contactType == 'contact':
            svc = sm.RemoteSvc('charMgr')
        elif self.contactType == 'corpcontact':
            svc = sm.GetService('corp')
        elif self.contactType == 'alliancecontact':
            svc = sm.GetService('alliance')
        return svc

    def CheckLabelName(self, labelName, *args):
        name = labelName.strip().lower()
        myLabelNames = [ label.name.lower() for label in self.GetContactLabels(self.contactType).values() ]
        if name in myLabelNames:
            return localization.GetByLabel('UI/PeopleAndPlaces/LabelsLabelNameTaken')

    def DeleteContactLabelFromUI(self, labelID, labelName):
        if eve.Message('DeleteMailLabel', {'labelName': labelName}, uiconst.YESNO) == uiconst.ID_YES:
            self.DeleteContactLabel(labelID)

    def DeleteContactLabel(self, labelID):
        self.GetSvc().DeleteLabel(labelID)
        if self.contactType == 'contact':
            contacts = self.contacts
            self.labels = None
        elif self.contactType == 'corpcontact':
            contacts = self.corporateContacts
            self.corporateLabels = None
        elif self.contactType == 'alliancecontact':
            contacts = self.allianceContacts
            self.allianceLabels = None
        else:
            raise RuntimeError('contact type missing')
        labels = self.GetContactLabels(self.contactType)
        for contactID, contact in contacts.iteritems():
            contacts[contactID].labelMask = contact.labelMask & const.maxLong - labelID

        sm.ScatterEvent('OnMyLabelsChanged', self.contactType, None)

    def AssignLabelFromMenu(self, selIDs, labelID, labelName):
        self.AssignLabelFromWnd(selIDs, labelID, labelName)

    def AssignLabelFromWnd(self, selIDs, labelID, labelName = '', displayNotify = 1):
        self.GetSvc().AssignLabels(selIDs, labelID)
        if self.contactType == 'contact':
            contacts = self.contacts
        elif self.contactType == 'corpcontact':
            contacts = self.corporateContacts
        elif self.contactType == 'alliancecontact':
            contacts = self.allianceContacts
        else:
            raise RuntimeError('contact type missing')
        for contactID in selIDs:
            if self.IsInAddressBook(contactID, self.contactType):
                contacts[contactID].labelMask = contacts[contactID].labelMask | labelID
                sm.ScatterEvent('OnEditLabel', selIDs, self.contactType)
            elif len(selIDs) == 1:
                self.AddToAddressBook(contactID, self.contactType, False, labelID)
                if self.IsInAddressBook(contactID, self.contactType):
                    contacts[contactID].labelMask = contacts[contactID].labelMask | labelID
                    sm.ScatterEvent('OnEditLabel', [contactID], self.contactType)
                else:
                    return

        if len(selIDs) and displayNotify:
            if not labelName:
                labels = self.GetContactLabels(self.contactType)
                if labelID in labels:
                    labelName = labels[labelID].name
            text = localization.GetByLabel('UI/PeopleAndPlaces/LabelsLabelAssigned', labelName=labelName, contacts=len(selIDs))
            eve.Message('CustomNotify', {'notify': text})

    def RemoveLabelFromMenu(self, selIDs, labelID, labelName):
        self.RemoveLabelFromWnd(selIDs, labelID)
        text = localization.GetByLabel('UI/PeopleAndPlaces/LabelRemoved', labelName=labelName, numContacts=len(selIDs))
        eve.Message('CustomNotify', {'notify': text})

    def RemoveLabelFromWnd(self, selIDs, labelID):
        self.GetSvc().RemoveLabels(selIDs, labelID)
        if self.contactType == 'contact':
            contacts = self.contacts
        elif self.contactType == 'corpcontact':
            contacts = self.corporateContacts
        elif self.contactType == 'alliancecontact':
            contacts = self.allianceContacts
        else:
            raise RuntimeError('contact type missing')
        for contactID in selIDs:
            contacts[contactID].labelMask = contacts[contactID].labelMask & const.maxLong - labelID

        sm.ScatterEvent('OnEditLabel', selIDs, self.contactType)

    def GetAssignLabelMenu(self, sel, selIDs, contactType, *args):
        m = []
        myLabels = self.GetContactLabels(contactType).values()
        labelMask = const.maxLong
        for node in sel:
            if not hasattr(node, 'labelMask'):
                return []
            if node.labelMask is not None:
                labelMask = labelMask & node.labelMask

        for each in myLabels:
            labelID = each.labelID
            if labelMask & labelID == labelID:
                continue
            label = each.name
            m.append((label, (each.name, self.AssignLabelFromMenu, (selIDs, each.labelID, each.name))))

        m = uiutil.SortListOfTuples(m)
        return m

    def GetRemoveLabelMenu(self, sel, selIDs, contactType, *args):
        m = []
        myLabels = self.GetContactLabels(contactType).values()
        labelMask = 0
        for node in sel:
            if not hasattr(node, 'labelMask'):
                return []
            if node.labelMask is not None:
                labelMask = labelMask | node.labelMask

        for each in myLabels:
            labelID = each.labelID
            if labelMask & labelID != labelID:
                continue
            label = each.name
            m.append((label, (each.name, self.RemoveLabelFromMenu, (selIDs, each.labelID, each.name))))

        m = uiutil.SortListOfTuples(m)
        return m

    def GetLabelText(self, labelMask, contactType):
        """
            finds what label text should be on this mail entry
        """
        myLabels = self.GetContactLabels(contactType)
        labelText = ''
        labelNames = []
        labels = sm.GetService('mailSvc').GetLabelMaskAsList(labelMask)
        swatchColors = sm.GetService('mailSvc').GetSwatchColors()
        for labelID in labels:
            label = myLabels.get(labelID, None)
            if label is not None:
                labelNames.append((label.name, label.color))

        labelNames.sort()
        for each, colorID in labelNames:
            if colorID is None or colorID not in swatchColors:
                colorID = 0
            color = swatchColors.get(colorID)[0]
            labelText += '<color=0xBF%s>%s</color>, ' % (color, each)

        labelText = labelText[:-2]
        return labelText

    def GetLabelMask(self, ownerID):
        contacts = None
        if self.contactType == 'contact':
            contacts = self.contacts
        elif self.contactType == 'corpcontact':
            contacts = self.corporateContacts
        elif self.contactType == 'alliancecontact':
            contacts = self.allianceContacts
        if contacts is None:
            contacts = self.GetContacts()
        contact = contacts.get(ownerID, None)
        if contact is not None:
            return contact.labelMask
        return 0

    def ShowLabelMenuAndManageBtn(self, formType):
        """
            using this to see if righclick menu on labels and the label management button should be visible
        """
        if formType == 'contact':
            return True
        if formType == 'corpcontact':
            if (const.corpRoleDirector | const.corpRoleDiplomat) & eve.session.corprole:
                return True
        elif formType == 'alliancecontact':
            if session.allianceid and sm.GetService('alliance').GetAlliance(session.allianceid).executorCorpID == session.corpid:
                if (const.corpRoleDirector | const.corpRoleDiplomat) & eve.session.corprole:
                    return True
        return False
