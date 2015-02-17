#Embedded file name: eve/client/script/ui/shared/neocom/addressBook\contactsForm.py
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

class ContactsForm(uiprimitives.Container):
    """ This class contains the contacts UI"""
    __guid__ = 'form.ContactsForm'
    __notifyevents__ = ['OnContactChange',
     'OnUnblockContact',
     'OnNotificationsRefresh',
     'OnMessageChanged',
     'OnMyLabelsChanged',
     'OnEditLabel']

    def Setup(self, formType):
        sm.RegisterNotify(self)
        self.startPos = 0
        self.numContacts = const.maxContactsPerPage
        self.group = None
        self.contactType = 'contact'
        self.formType = formType
        self.expandedHeight = False
        self.DrawStuff()

    def _OnClose(self):
        sm.UnregisterNotify(self)

    def DrawStuff(self, *args):
        self.sr.topCont = uiprimitives.Container(name='topCont', parent=self, align=uiconst.TOTOP, pos=(0, 0, 0, 45))
        self.sr.mainCont = uiprimitives.Container(name='mainCont', parent=self, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.topLeft = uiprimitives.Container(name='topCont', parent=self.sr.topCont, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         0,
         0,
         0))
        self.sr.topRight = uiprimitives.Container(name='topCont', parent=self.sr.topCont, align=uiconst.TORIGHT, pos=(0, 0, 50, 0))
        self.quickFilter = uicls.QuickFilterEdit(parent=self.sr.topLeft, left=const.defaultPadding, top=8)
        self.quickFilter.ReloadFunction = lambda : self.LoadContactsForm(self.contactType)
        self.sr.onlinecheck = uicontrols.Checkbox(text=localization.GetByLabel('UI/PeopleAndPlaces/OnlineOnly'), parent=self.sr.topLeft, configName='onlinebuddyonly', retval=1, checked=settings.user.ui.Get('onlinebuddyonly', 0), groupname=None, callback=self.CheckBoxChange, align=uiconst.TOPLEFT, pos=(0, 30, 100, 0))
        if sm.GetService('addressbook').ShowLabelMenuAndManageBtn(self.formType):
            labelBtn = uix.GetBigButton(size=32, where=self.sr.topLeft, left=115, top=8, hint=localization.GetByLabel('UI/PeopleAndPlaces/LabelsManageLabels'), align=uiconst.RELATIVE)
            uiutil.MapIcon(labelBtn.sr.icon, 'res:/ui/Texture/WindowIcons/evemailtag.png', ignoreSize=True)
            labelBtn.OnClick = self.ManageLabels
        btn = uix.GetBigButton(24, self.sr.topRight, 32, const.defaultPadding)
        btn.OnClick = (self.BrowseContacts, -1)
        btn.hint = localization.GetByLabel('UI/Common/Previous')
        btn.state = uiconst.UI_HIDDEN
        btn.SetAlign(align=uiconst.TOPRIGHT)
        btn.sr.icon.LoadIcon('ui_23_64_1')
        self.sr.contactBackBtn = btn
        btn = uix.GetBigButton(24, self.sr.topRight, const.defaultPadding, const.defaultPadding)
        btn.OnClick = (self.BrowseContacts, 1)
        btn.hint = localization.GetByLabel('UI/Common/Next')
        btn.state = uiconst.UI_HIDDEN
        btn.SetAlign(uiconst.TOPRIGHT)
        btn.sr.icon.LoadIcon('ui_23_64_2')
        self.sr.contactFwdBtn = btn
        self.sr.pageCount = uicontrols.EveLabelMedium(text='', parent=self.sr.topRight, left=10, top=30, state=uiconst.UI_DISABLED, align=uiconst.CENTERTOP)
        systemStatsCont = uicontrols.DragResizeCont(name='systemStatsCont', settingsID='contactsListSplit', parent=self.sr.mainCont, align=uiconst.TOLEFT, minSize=100, maxSize=200, defaultSize=160)
        self.sr.leftCont = uiprimitives.Container(name='leftCont', parent=systemStatsCont.mainCont, padding=(const.defaultPadding,
         0,
         0,
         0))
        self.sr.leftScroll = uicontrols.Scroll(name='leftScroll', parent=self.sr.leftCont, padding=(0,
         const.defaultPadding,
         0,
         const.defaultPadding))
        self.sr.leftScroll.multiSelect = 0
        self.sr.leftScroll.sr.content.OnDropData = self.OnContactDropData
        self.sr.rightCont = uiprimitives.Container(name='rightCont', parent=self.sr.mainCont, padding=(0,
         0,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.rightScroll = uicontrols.Scroll(name='rightScroll', parent=self.sr.rightCont, padding=(0,
         const.defaultPadding,
         0,
         0))
        self.sr.rightScroll.sr.ignoreTabTrimming = 1
        self.sr.rightScroll.multiSelect = 1
        self.sr.rightScroll.sr.content.OnDropData = self.OnContactDropData
        self.sr.rightScroll.sr.id = self.formType

    def LoadLeftSide(self):
        scrolllist = self.GetStaticLabelsGroups()
        scrolllist.insert(1, listentry.Get('Space', {'height': 16}))
        scrolllist.append(listentry.Get('Space', {'height': 16}))
        data = {'GetSubContent': self.GetLabelsSubContent,
         'MenuFunction': self.LabelGroupMenu,
         'label': localization.GetByLabel('UI/PeopleAndPlaces/Labels'),
         'cleanLabel': localization.GetByLabel('UI/PeopleAndPlaces/Labels'),
         'id': ('contacts', 'Labels', localization.GetByLabel('UI/PeopleAndPlaces/Labels')),
         'state': 'locked',
         'BlockOpenWindow': 1,
         'showicon': 'ui_73_16_9',
         'showlen': 0,
         'groupName': 'labels',
         'groupItems': [],
         'updateOnToggle': 0}
        scrolllist.append(listentry.Get('Group', data))
        self.sr.leftScroll.Load(contentList=scrolllist)
        if self.contactType == 'contact':
            lastViewedID = settings.char.ui.Get('contacts_lastselected', None)
        elif self.contactType == 'corpcontact':
            lastViewedID = settings.char.ui.Get('corpcontacts_lastselected', None)
        elif self.contactType == 'alliancecontact':
            lastViewedID = settings.char.ui.Get('alliancecontacts_lastselected', None)
        for entry in self.sr.leftScroll.GetNodes():
            groupID = entry.groupID
            if groupID is None:
                continue
            if groupID == lastViewedID:
                panel = entry.panel
                if panel is not None:
                    panel.OnClick()
                    return

        if len(self.sr.leftScroll.GetNodes()) > 0:
            entry = self.sr.leftScroll.GetNodes()[0]
            panel = entry.panel
            if panel is not None:
                panel.OnClick()

    def GetStandingNameShort(self, standing):
        if standing == const.contactHighStanding:
            return localization.GetByLabel('UI/PeopleAndPlaces/StandingExcellent')
        if standing == const.contactGoodStanding:
            return localization.GetByLabel('UI/PeopleAndPlaces/StandingGood')
        if standing == const.contactNeutralStanding:
            return localization.GetByLabel('UI/PeopleAndPlaces/StandingNeutral')
        if standing == const.contactBadStanding:
            return localization.GetByLabel('UI/PeopleAndPlaces/StandingBad')
        if standing == const.contactHorribleStanding:
            return localization.GetByLabel('UI/PeopleAndPlaces/StandingTerrible')

    def GetLabelsSubContent(self, items):
        """
            gets the subcontent for label group, the player defined labels
        """
        scrolllist = []
        myLabels = sm.GetService('addressbook').GetContactLabels(self.contactType)
        for each in myLabels.itervalues():
            if getattr(each, 'static', 0):
                continue
            entryItem = self.CreateLabelEntry(each)
            scrolllist.append((each.name.lower(), entryItem))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        data = util.KeyVal()
        data.cleanLabel = localization.GetByLabel('UI/PeopleAndPlaces/NoLabel')
        data.label = '%s [%s]' % (localization.GetByLabel('UI/PeopleAndPlaces/NoLabel'), self.GetContactsLabelCount(-1))
        data.sublevel = 1
        data.currentView = -1
        data.OnClick = self.LoadGroupFromEntry
        data.groupID = -1
        scrolllist.insert(0, listentry.Get('MailLabelEntry', data=data))
        return scrolllist

    def CreateLabelEntry(self, labelEntry):
        count = self.GetContactsLabelCount(labelEntry.labelID)
        label = '%s [%s]' % (labelEntry.name, count)
        data = util.KeyVal()
        data.cleanLabel = labelEntry.name
        data.label = label
        data.sublevel = 1
        data.currentView = labelEntry.labelID
        data.OnClick = self.LoadGroupFromEntry
        data.GetMenu = self.GetLabelMenu
        data.OnDropData = self.OnGroupDropData
        data.groupID = labelEntry.labelID
        return listentry.Get('MailLabelEntry', data=data)

    def GetLabelMenu(self, entry):
        labelID = entry.sr.node.currentView
        m = []
        if sm.GetService('addressbook').ShowLabelMenuAndManageBtn(self.formType):
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/LabelsRename'), sm.GetService('addressbook').RenameContactLabelFromUI, (labelID,)))
            m.append(None)
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/LabelsDelete'), sm.GetService('addressbook').DeleteContactLabelFromUI, (labelID, entry.sr.node.label)))
        return m

    def ManageLabels(self, *args):
        configName = '%s%s' % ('ManageLabels', self.formType)
        form.ManageLabels.Open(windowID=configName, labelType=self.formType)

    def GetStaticLabelsGroups(self):
        """
            Gets the groups for the static labels
        """
        scrolllist = []
        labelList = [(localization.GetByLabel('UI/PeopleAndPlaces/AllContacts'), const.contactAll),
         (localization.GetByLabel('UI/PeopleAndPlaces/ExcellentStanding'), const.contactHighStanding),
         (localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'), const.contactGoodStanding),
         (localization.GetByLabel('UI/PeopleAndPlaces/NeutralStanding'), const.contactNeutralStanding),
         (localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'), const.contactBadStanding),
         (localization.GetByLabel('UI/PeopleAndPlaces/TerribleStanding'), const.contactHorribleStanding)]
        if self.contactType == 'contact':
            labelList.append((localization.GetByLabel('UI/PeopleAndPlaces/Watchlist'), const.contactWatchlist))
            labelList.append((localization.GetByLabel('UI/PeopleAndPlaces/Blocked'), const.contactBlocked))
            labelList.insert(0, (localization.GetByLabel('UI/PeopleAndPlaces/Notifications'), const.contactNotifications))
            lastViewedID = settings.char.ui.Get('contacts_lastselected', None)
        elif self.contactType == 'corpcontact':
            lastViewedID = settings.char.ui.Get('corpcontacts_lastselected', None)
        elif self.contactType == 'alliancecontact':
            lastViewedID = settings.char.ui.Get('alliancecontacts_lastselected', None)
        for label, groupID in labelList:
            entry = self.GetGroupEntry(groupID, label, groupID == lastViewedID)
            scrolllist.append(entry)

        if self.contactType == 'contact':
            scrolllist.insert(-1, listentry.Get('Space', {'height': 16}))
        return scrolllist

    def GetGroupEntry(self, groupID, label, selected = 0):
        data = {'GetSubContent': self.GetLeftGroups,
         'label': label,
         'cleanLabel': label,
         'id': ('contact', groupID),
         'state': 'locked',
         'BlockOpenWindow': 0,
         'disableToggle': 1,
         'expandable': 0,
         'showicon': 'hide',
         'showlen': 1,
         'groupItems': self.GetContactsCount(groupID),
         'hideNoItem': 1,
         'hideExpander': 1,
         'hideExpanderLine': 1,
         'selectGroup': 1,
         'isSelected': selected,
         'groupID': groupID,
         'OnClick': self.LoadGroupFromEntry}
        entry = listentry.Get('Group', data)
        return entry

    def LoadContactsForm(self, contactType, *args):
        self.contactType = contactType
        if contactType == 'contact':
            self.sr.topCont.height = 45
            self.sr.onlinecheck.state = uiconst.UI_NORMAL
        else:
            if sm.GetService('addressbook').ShowLabelMenuAndManageBtn(self.formType):
                self.sr.topCont.height = 38
            else:
                self.sr.topCont.height = 32
            self.sr.onlinecheck.state = uiconst.UI_HIDDEN
        self.LoadData()
        self.LoadLeftSide()

    def CheckInGroup(self, groupID, relationshipID):
        if groupID == const.contactHighStanding:
            if relationshipID > const.contactGoodStanding:
                return True
        elif groupID == const.contactGoodStanding:
            if relationshipID > const.contactNeutralStanding and relationshipID <= const.contactGoodStanding:
                return True
        elif groupID == const.contactNeutralStanding:
            if relationshipID == const.contactNeutralStanding:
                return True
        elif groupID == const.contactBadStanding:
            if relationshipID < const.contactNeutralStanding and relationshipID >= const.contactBadStanding:
                return True
        elif groupID == const.contactHorribleStanding:
            if relationshipID < const.contactBadStanding:
                return True
        return False

    def CheckHasLabel(self, labelID, labelMask):
        if not labelMask and labelID == -1:
            return True
        elif labelMask & labelID == labelID:
            return True
        else:
            return False

    def LoadGroupFromEntry(self, entry, *args):
        group = entry.sr.node
        self.blockedSelected = False
        if self.group != group.groupID:
            self.startPos = 0
            self.group = group.groupID
        if group.groupID == const.contactBlocked:
            self.blockedSelected = True
        self.LoadGroupFromNode(group)

    def CheckIfAgent(self, contactID):
        if sm.GetService('agents').IsAgent(contactID):
            return True
        if util.IsNPC(contactID) and util.IsCharacter(contactID):
            return True

    def GetContactsLabelCount(self, labelID):
        contactList = []
        for contact in self.contacts:
            if self.CheckHasLabel(labelID, contact.labelMask):
                contactList.append(contact.contactID)

        count = len(contactList)
        return count

    def GetContactsCount(self, groupID):
        contactList = []
        if groupID == const.contactBlocked:
            for blocked in self.blocked:
                contactList.append(blocked.contactID)

        elif groupID == const.contactNotifications:
            for notification in self.notifications:
                contactList.append(notification.notificationID)

        else:
            for contact in self.contacts:
                if groupID == const.contactAll:
                    contactList.append(contact.contactID)
                elif groupID == const.contactWatchlist:
                    if contact.inWatchlist:
                        contactList.append(contact.contactID)
                elif groupID == const.contactHighStanding:
                    if contact.relationshipID > const.contactGoodStanding:
                        contactList.append(contact.contactID)
                elif groupID == const.contactGoodStanding:
                    if contact.relationshipID > const.contactNeutralStanding and contact.relationshipID <= const.contactGoodStanding:
                        contactList.append(contact.contactID)
                elif groupID == const.contactNeutralStanding:
                    if contact.relationshipID == const.contactNeutralStanding:
                        contactList.append(contact.contactID)
                elif groupID == const.contactBadStanding:
                    if contact.relationshipID < const.contactNeutralStanding and contact.relationshipID >= const.contactBadStanding:
                        contactList.append(contact.contactID)
                elif groupID == const.contactHorribleStanding:
                    if contact.relationshipID < const.contactBadStanding:
                        contactList.append(contact.contactID)

        return contactList

    def GetLabelName(self, labelID, *args):
        labels = sm.GetService('addressbook').GetContactLabels(self.contactType).values()
        if labelID == -1:
            return localization.GetByLabel('UI/PeopleAndPlaces/NoLabel')
        for label in labels:
            if labelID == label.labelID:
                return label.name

    def GetScrolllist(self, data):
        scrolllist = []
        noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoContacts')
        onlineOnly = False
        headers = True
        reverse = False
        if self.contactType == 'contact':
            settings.char.ui.Set('contacts_lastselected', data.groupID)
            onlineOnly = settings.user.ui.Get('onlinebuddyonly', 0)
            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoContacts')
        elif self.contactType == 'corpcontact':
            settings.char.ui.Set('corpcontacts_lastselected', data.groupID)
            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoCorpContacts')
        elif self.contactType == 'alliancecontact':
            settings.char.ui.Set('alliancecontacts_lastselected', data.groupID)
            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoAllianceContacts')
        if data.groupID == const.contactWatchlist:
            self.sr.rightScroll.multiSelect = 1
            for contact in self.contacts:
                if not self.CheckIfAgent(contact.contactID) and util.IsCharacter(contact.contactID) and contact.inWatchlist:
                    entryTuple = sm.GetService('addressbook').GetContactEntry(data, contact, onlineOnly, contactType=self.contactType, contactLevel=contact.relationshipID, labelMask=contact.labelMask)
                    if entryTuple is not None:
                        scrolllist.append(entryTuple)

            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoneOnWatchlist')
        elif data.groupID == const.contactBlocked:
            self.sr.rightScroll.multiSelect = 1
            for blocked in self.blocked:
                if blocked.contactID > 0 and not self.CheckIfAgent(blocked.contactID):
                    entryTuple = sm.GetService('addressbook').GetContactEntry(data, blocked, onlineOnly, contactType=self.contactType)
                    if entryTuple is not None:
                        scrolllist.append(entryTuple)

            if sm.GetService('account').GetDefaultContactCost() == -1:
                noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/UnknownBlocked')
            else:
                noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoneBlockedYet')
        elif data.groupID == const.contactAll:
            self.sr.rightScroll.multiSelect = 1
            for contact in self.contacts:
                if not self.CheckIfAgent(contact.contactID):
                    entryTuple = sm.GetService('addressbook').GetContactEntry(data, contact, onlineOnly, contactType=self.contactType, contactLevel=contact.relationshipID, labelMask=contact.labelMask)
                    if entryTuple is not None:
                        scrolllist.append(entryTuple)

        elif data.groupID == const.contactNotifications:
            self.sr.rightScroll.multiSelect = 0
            for notification in self.notifications:
                scrolllist.append(sm.GetService('addressbook').GetNotifications(notification))

            headers = False
            reverse = True
            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoNotifications')
        elif data.groupID in (const.contactGoodStanding,
         const.contactHighStanding,
         const.contactNeutralStanding,
         const.contactBadStanding,
         const.contactHorribleStanding):
            self.sr.rightScroll.multiSelect = 1
            for contact in self.contacts:
                if not self.CheckIfAgent(contact.contactID):
                    if self.CheckInGroup(data.groupID, contact.relationshipID):
                        entryTuple = sm.GetService('addressbook').GetContactEntry(data, contact, onlineOnly, contactType=self.contactType, contactLevel=contact.relationshipID, labelMask=contact.labelMask)
                        if entryTuple is not None:
                            scrolllist.append(entryTuple)

            standingText = self.GetStandingNameShort(data.groupID)
            if self.contactType == 'contact':
                noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoContactsStanding', standingText=standingText)
            elif self.contactType == 'corpcontact':
                noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoCorpContactsStanding', standingText=standingText)
            elif self.contactType == 'alliancecontact':
                noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoAllianceContactsStanding', standingText=standingText)
        else:
            self.sr.rightScroll.multiSelect = 1
            for contact in self.contacts:
                if not self.CheckIfAgent(contact.contactID):
                    if self.CheckHasLabel(data.groupID, contact.labelMask):
                        entryTuple = sm.GetService('addressbook').GetContactEntry(data, contact, onlineOnly, contactType=self.contactType, contactLevel=contact.relationshipID, labelMask=contact.labelMask)
                        if entryTuple is not None:
                            scrolllist.append(entryTuple)

            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoContactsLabel', standingText=self.GetLabelName(data.groupID))
        if onlineOnly:
            noContentHint = localization.GetByLabel('UI/PeopleAndPlaces/NoOnlineContact')
        if len(self.quickFilter.GetValue()):
            noContentHint = localization.GetByLabel('UI/Common/NothingFound')
        totalNum = len(scrolllist)
        scrolllist = uiutil.SortListOfTuples(scrolllist, reverse)
        scrolllist = scrolllist[self.startPos:self.startPos + self.numContacts]
        return (scrolllist,
         noContentHint,
         totalNum,
         headers)

    def LoadGroupFromNode(self, data, *args):
        if self.formType == 'alliancecontact' and session.allianceid is None:
            self.sr.rightScroll.Load(fixedEntryHeight=19, contentList=[], noContentHint=localization.GetByLabel('UI/PeopleAndPlaces/OwnerNotInAnyAlliance', corpName=cfg.eveowners.Get(session.corpid).ownerName))
            return
        scrolllist, noContentHint, totalNum, displayHeaders = self.GetScrolllist(data)
        if displayHeaders:
            headers = [localization.GetByLabel('UI/Common/Name')]
        else:
            headers = []
        self.sr.rightScroll.Load(contentList=scrolllist, headers=headers, noContentHint=noContentHint)
        if totalNum is not None:
            self.ShowHideBrowse(totalNum)

    def CheckBoxChange(self, checkbox):
        config = checkbox.data['config']
        if checkbox.data.has_key('value'):
            if checkbox.checked:
                settings.user.ui.Set(config, checkbox.data['value'])
            else:
                settings.user.ui.Set(config, checkbox.checked)
        self.LoadContactsForm(self.contactType)

    def GetLeftGroups(self, data, *args):
        scrolllist = self.GetScrolllist(data)[0]
        return scrolllist

    def LabelGroupMenu(self, node, *args):
        m = []
        m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/ManageLabels'), self.ManageLabels))
        return m

    def LoadData(self, *args):
        self.contacts = []
        self.blocked = []
        self.notifications = []
        allContacts = sm.GetService('addressbook').GetContacts()
        if self.contactType == 'contact':
            self.contacts = allContacts.contacts.values()
            self.blocked = allContacts.blocked.values()
            self.notifications = sm.GetService('notificationSvc').GetFormattedNotifications(const.groupContacts)
        elif self.contactType == 'corpcontact':
            self.contacts = allContacts.corpContacts.values()
        elif self.contactType == 'alliancecontact':
            self.contacts = allContacts.allianceContacts.values()
        filter = self.quickFilter.GetValue()
        if len(filter):
            self.blocked = uiutil.NiceFilter(self.quickFilter.QuickFilter, self.blocked)
            self.contacts = uiutil.NiceFilter(self.quickFilter.QuickFilter, self.contacts)

    def BrowseContacts(self, backforth, *args):
        """
            called when one of the browse window is clicked
        """
        pos = max(0, self.startPos + self.numContacts * backforth)
        self.startPos = pos
        self.LoadContactsForm(self.contactType)

    def ShowHideBrowse(self, totalNum):
        """
            figuring out if the browse buttons are needed
        """
        btnDisplayed = 0
        if self.startPos == 0:
            self.sr.contactBackBtn.state = uiconst.UI_HIDDEN
        else:
            self.sr.contactBackBtn.state = uiconst.UI_NORMAL
            btnDisplayed = 1
        if self.startPos + self.numContacts >= totalNum:
            self.sr.contactFwdBtn.state = uiconst.UI_HIDDEN
        else:
            self.sr.contactFwdBtn.state = uiconst.UI_NORMAL
            btnDisplayed = 1
        if btnDisplayed:
            if self.sr.onlinecheck.state == uiconst.UI_HIDDEN and not self.expandedHeight:
                self.sr.topCont.height += 10
                self.expandedHeight = True
            numPages = int(math.ceil(totalNum / float(self.numContacts)))
            currentPage = self.startPos / self.numContacts + 1
            self.sr.pageCount.text = '%s/%s' % (currentPage, numPages)
        else:
            self.sr.pageCount.text = ''

    def OnContactDropData(self, dragObj, nodes):
        if self.contactType == 'contact' and settings.char.ui.Get('contacts_lastselected', None) == const.contactBlocked:
            sm.GetService('addressbook').DropInBlocked(nodes)
        else:
            sm.GetService('addressbook').DropInPersonal(nodes, self.contactType)

    def ReloadData(self):
        self.LoadData()
        self.LoadLeftSide()
        if len(self.sr.rightScroll.GetNodes()) < 1:
            self.BrowseContacts(-1)

    def OnNotificationsRefresh(self):
        if self.formType == 'contact' and settings.char.ui.Get('contacts_lastselected', None) == const.contactNotifications:
            self.ReloadData()

    def OnMessageChanged(self, type, messageIDs, what):
        """
            this event is scattered when notification is deleted or trashed from outside this
            window
        """
        if type == const.mailTypeNotifications and what == 'deleted':
            if self.formType == 'contact' and settings.char.ui.Get('contacts_lastselected', None) == const.contactNotifications:
                self.ReloadData()

    def OnContactChange(self, contactIDs, contactType = None):
        if contactType == self.formType:
            self.ReloadData()

    def OnMyLabelsChanged(self, contactType, labelID):
        if contactType == self.formType:
            self.LoadLeftSide()

    def OnEditLabel(self, contactIDs, contactType):
        if contactType == self.formType:
            self.ReloadData()

    def OnUnblockContact(self, contactID):
        if self.formType == 'contact':
            self.ReloadData()

    def OnGroupDropData(self, groupID, nodes, *args):
        what, labelID, labelName = groupID
        contactIDs = []
        for node in nodes:
            contactIDs.append(node.itemID)

        if len(contactIDs):
            sm.StartService('addressbook').AssignLabelFromWnd(contactIDs, labelID, labelName)
