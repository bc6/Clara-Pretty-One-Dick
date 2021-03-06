#Embedded file name: eve/client/script/ui/shared/neocom\evemailingListConfig.py
"""
    Configuration window for EVEMAIL mailing lists
"""
import math
from eve.client.script.ui.shared.neocom.evemail import MailWindow
import uiprimitives
import uicontrols
import uix
import util
import uiutil
import listentry
import carbonui.const as uiconst
import uicls
import uthread
import localization
PAD = 6
SPACING = 22
EDITHEIGHT = 18
FIELDWIDTH = 70
FIELDSPACE = 10
BUTTONTOP = 2
FILTER_ALL = 0
FILTER_MEMBERS = 1
FILTER_MUTED = 2
FILTER_OPERATORS = 3
FILTER_BYNAME = 4
ACTION_SETMEMBER = 0
ACTION_SETMUTED = 1
ACTION_SETOPERATOR = 2
ACTION_KICK = 3
NUMPERPAGE = 50

class MaillistSetupWindow(uicontrols.Window):
    __guid__ = 'form.MaillistSetupWindow'
    default_iconNum = MailWindow.default_iconNum
    default_topParentHeight = 0

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.mailingListID = attributes.mailingListID
        self.mlsvc = sm.GetService('mailinglists')
        self.groupName = self.mlsvc.GetDisplayName(self.mailingListID)
        self.SetMinSize([350, 350])
        self.SetCaption(localization.GetByLabel('UI/EVEMail/MailingLists/Caption', mailinglistName=self.groupName))
        self.welcomeText = None
        self.sr.tabs = uicontrols.TabGroup(name='tabs', parent=self.sr.main)
        self.sr.membersPanel = uiprimitives.Container(name='membersPanel', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(PAD,
         PAD,
         PAD,
         PAD))
        self.sr.accessPanel = uiprimitives.Container(name='accessPanel', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(PAD,
         PAD,
         PAD,
         0))
        self.sr.welcomePanel = uiprimitives.Container(name='welcomePanel', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(PAD,
         PAD,
         PAD,
         0))
        tabs = [[localization.GetByLabel('UI/EVEMail/MailingLists/MembersTab'),
          self.sr.membersPanel,
          self,
          'members'], [localization.GetByLabel('UI/EVEMail/MailingLists/AccessTab'),
          self.sr.accessPanel,
          self,
          'access'], [localization.GetByLabel('UI/EVEMail/MailingLists/WelcomeMailTab'),
          self.sr.welcomePanel,
          self,
          'welcome']]
        self.StartupMembersPanel()
        self.StartupAccessPanel()
        self.StartupWelcomePanel()
        self.sr.tabs.Startup(tabs, 'mailinglistSetup_tabs', autoselecttab=1)

    def StartupMembersPanel(self):
        membersPanel = self.sr.membersPanel
        comboOptions = [(localization.GetByLabel('UI/Common/All'), FILTER_ALL),
         (localization.GetByLabel('UI/EVEMail/MailingLists/NormalMembers'), FILTER_MEMBERS),
         (localization.GetByLabel('UI/EVEMail/MailingLists/MutedMembers'), FILTER_MUTED),
         (localization.GetByLabel('UI/Chat/Operators'), FILTER_OPERATORS),
         (localization.GetByLabel('UI/EVEMail/MailingLists/SearchByName'), FILTER_BYNAME)]
        topCont = uiprimitives.Container(name='topCont', parent=membersPanel, align=uiconst.TOTOP, pos=(0, 10, 0, 28))
        self.sr.membersPanel.showMembersCombo = uicontrols.Combo(label=localization.GetByLabel('UI/EVEMail/MailingLists/ShowLabel'), parent=topCont, options=comboOptions, name='showMembersCombo', callback=self.OnShowMembersComboChanged, width=100, align=uiconst.TOPLEFT)
        self.sr.membersPanel.searchEdit = uicontrols.SinglelineEdit(label=localization.GetByLabel('UI/PeopleAndPlaces/SearchString'), name='searchEdit', parent=topCont, align=uiconst.TOPLEFT, pos=(115,
         0,
         80,
         EDITHEIGHT), state=uiconst.UI_HIDDEN)
        self.sr.membersPanel.searchEdit.OnReturn = self.UpdateMembersScroll
        self.sr.membersPanel.searchButton = uicontrols.Button(parent=topCont, label=localization.GetByLabel('UI/Common/Buttons/Search'), left=200, func=self.UpdateMembersScroll, align=uiconst.TOPLEFT, state=uiconst.UI_HIDDEN)
        browseCont = uiprimitives.Container(name='browseCont', parent=topCont, align=uiconst.TOPRIGHT, pos=(0, -10, 50, 50))
        btn = uix.GetBigButton(24, browseCont, 0, 0)
        btn.OnClick = (self.ChangeMembersPage, -1)
        btn.hint = localization.GetByLabel('UI/Common/Previous')
        btn.state = uiconst.UI_NORMAL
        btn.sr.icon.LoadIcon('ui_23_64_1')
        self.sr.pageBackBtn = btn
        btn = uix.GetBigButton(24, browseCont, 24, 0)
        btn.OnClick = (self.ChangeMembersPage, 1)
        btn.hint = localization.GetByLabel('UI/Generic/Next')
        btn.state = uiconst.UI_NORMAL
        btn.sr.icon.LoadIcon('ui_23_64_2')
        self.sr.pageFwdBtn = btn
        self.sr.pageCount = uicontrols.EveLabelMedium(text='', parent=browseCont, left=16, top=26, height=12, state=uiconst.UI_DISABLED)
        bottomCont = uiprimitives.Container(parent=membersPanel, align=uiconst.TOBOTTOM, pos=(0,
         0,
         100,
         EDITHEIGHT), padding=(0,
         3 * PAD,
         0,
         PAD), state=uiconst.UI_PICKCHILDREN)
        comboOptions = [(localization.GetByLabel('UI/EVEMail/MailingLists/SetRoleMember'), ACTION_SETMEMBER),
         (localization.GetByLabel('UI/EVEMail/MailingLists/SetRoleMuted'), ACTION_SETMUTED),
         (localization.GetByLabel('UI/EVEMail/MailingLists/SetRoleOperator'), ACTION_SETOPERATOR),
         (localization.GetByLabel('UI/EVEMail/MailingLists/Kick'), ACTION_KICK)]
        self.sr.membersPanel.actionCombo = uicontrols.Combo(label=localization.GetByLabel('UI/EVEMail/MailingLists/ApplyToSelected'), parent=bottomCont, options=comboOptions, name='showMembersCombo', width=150, align=uiconst.TOPLEFT)
        self.sr.membersPanel.ApplyBtn = uicontrols.Button(parent=bottomCont, label=localization.GetByLabel('UI/Generic/Apply'), func=self.ApplyActionToMembers, align=uiconst.TOPRIGHT)
        self.sr.membersPanel.ApplyBtn.Disable()
        self.roles = {const.mailingListMemberDefault: localization.GetByLabel('UI/EVEMail/MailingLists/Member'),
         const.mailingListMemberMuted: localization.GetByLabel('UI/EVEMail/MailingLists/MutedMember'),
         const.mailingListMemberOperator: localization.GetByLabel('UI/EVEMail/MailingLists/Operator'),
         const.mailingListMemberOwner: localization.GetByLabel('UI/EVEMail/MailingLists/Owner')}
        self.sr.membersPanel.scroll = uicontrols.Scroll(parent=membersPanel, name='membersScroll', padTop=PAD)
        self.sr.membersPanel.scroll.sr.id = 'membersPanelScroll'
        self.sr.membersPanel.scroll.OnSelectionChange = self.OnMembersScrollSelectionChange

    def OnMembersScrollSelectionChange(self, *args):
        if len(self.sr.membersPanel.scroll.GetSelected()) > 0:
            self.sr.membersPanel.ApplyBtn.Enable()
        else:
            self.sr.membersPanel.ApplyBtn.Disable()

    def OnShowMembersComboChanged(self, comboBox, selString, selVal):
        if selVal == FILTER_BYNAME:
            self.sr.membersPanel.searchEdit.state = uiconst.UI_NORMAL
            self.sr.membersPanel.searchButton.state = uiconst.UI_NORMAL
        else:
            self.sr.membersPanel.searchEdit.state = uiconst.UI_HIDDEN
            self.sr.membersPanel.searchButton.state = uiconst.UI_HIDDEN
            self.UpdateMembersScroll()

    def ChangeMembersPage(self, pageChange, *args):
        self.currPage += pageChange
        if self.numPages <= 1:
            self.sr.pageBackBtn.state = self.sr.pageFwdBtn.state = uiconst.UI_HIDDEN
        elif self.currPage == 0:
            self.sr.pageBackBtn.state = uiconst.UI_HIDDEN
            self.sr.pageFwdBtn.state = uiconst.UI_NORMAL
        elif self.currPage == self.numPages - 1:
            self.sr.pageBackBtn.state = uiconst.UI_NORMAL
            self.sr.pageFwdBtn.state = uiconst.UI_HIDDEN
        else:
            self.sr.pageBackBtn.state = self.sr.pageFwdBtn.state = uiconst.UI_NORMAL
        self.PopulateMembersScroll()
        if self.numPages > 1:
            self.sr.pageCount.text = '%s/%s' % (self.currPage + 1, self.numPages)
        else:
            self.sr.pageCount.text = ''

    def UpdateMembersScroll(self, *args):
        """
            Fetch members from server, apply filter, sort, page and finally populate the scroll
        """
        self.members = self.mlsvc.GetMembers(self.mailingListID)
        if not self or self.destroyed:
            return
        self.FilterMembers()
        self.SortMembers()
        self.PageMembers()
        self.PopulateMembersScroll()

    def FilterMembers(self, *args):
        """
            Filter the members shown in scroll according to the selection of showMembersCombo
        """
        filter = self.sr.membersPanel.showMembersCombo.GetValue()
        self.filteredMembers = []
        if filter == FILTER_ALL:
            for memberID, accessLevel in self.members.iteritems():
                self.filteredMembers.append(util.KeyVal(memberID=memberID, accessLevel=accessLevel))

        elif filter == FILTER_MEMBERS:
            for memberID, accessLevel in self.members.iteritems():
                if accessLevel == const.mailingListMemberDefault:
                    self.filteredMembers.append(util.KeyVal(memberID=memberID, accessLevel=accessLevel))

        elif filter == FILTER_MUTED:
            for memberID, accessLevel in self.members.iteritems():
                if accessLevel == const.mailingListMemberMuted:
                    self.filteredMembers.append(util.KeyVal(memberID=memberID, accessLevel=accessLevel))

        elif filter == FILTER_OPERATORS:
            for memberID, accessLevel in self.members.iteritems():
                if accessLevel == const.mailingListMemberOperator or accessLevel == const.mailingListMemberOwner:
                    self.filteredMembers.append(util.KeyVal(memberID=memberID, accessLevel=accessLevel))

        elif filter == FILTER_BYNAME:
            searchStr = self.sr.membersPanel.searchEdit.GetValue().strip().lower()
            for memberID, accessLevel in self.members.iteritems():
                name = cfg.eveowners.Get(memberID).name.strip().lower()
                if name.startswith(searchStr):
                    self.filteredMembers.append(util.KeyVal(memberID=memberID, accessLevel=accessLevel))

    def SortMembers(self):
        self.filteredMembers.sort(cmp=self._CompareMembers)

    def _CompareMembers(self, x, y):
        """
            A comparison method for list.sort to sort members by name
        """
        nameX = cfg.eveowners.Get(x.memberID).name.lower()
        nameY = cfg.eveowners.Get(y.memberID).name.lower()
        if nameX < nameY:
            return -1
        elif nameX == nameY:
            return 0
        else:
            return 1

    def PageMembers(self):
        """
            Order members fetched into pages and update the page combo box
        """
        self.currPage = 0
        self.pagedMembers = []
        self.numPages = int(math.ceil(float(len(self.filteredMembers)) / NUMPERPAGE))
        for i in range(self.numPages):
            self.pagedMembers.append(self.filteredMembers[i * NUMPERPAGE:(i + 1) * NUMPERPAGE])

        if self.numPages > 1:
            pages = []
            for i in range(self.numPages):
                pages.append((str(i + 1), i))

        self.ChangeMembersPage(0)

    def PopulateMembersScroll(self, *args):
        """
            Load the currently selected page of members into the members scroll
        """
        scrolllist = []
        self.checkedMembers = []
        if len(self.pagedMembers) == 0:
            page = []
        else:
            page = self.pagedMembers[self.currPage]
        for m in page:
            data = util.KeyVal()
            data.label = '%s<t>%s' % (cfg.eveowners.Get(m.memberID).name, self.roles[m.accessLevel])
            data.checked = False
            data.cfgname = 'member'
            data.retval = m.memberID
            data.charID = m.memberID
            data.GetMenu = self.GetCharMenu
            scrolllist.append(listentry.Get('Generic', data=data))

        self.sr.membersPanel.scroll.Load(contentList=scrolllist, headers=[localization.GetByLabel('UI/Generic/NamePerson'), localization.GetByLabel('UI/EVEMail/MailingLists/Role')], customColumnWidths=True, noContentHint=localization.GetByLabel('UI/EVEMail/MailingLists/NoMembersFound'))
        self.sr.membersPanel.ApplyBtn.Disable()

    def GetCharMenu(self, entry, *args):
        data = entry.sr.node
        charID = data.charID
        typeID = const.typeCharacterAmarr
        if charID:
            charMenu = sm.GetService('menu').CharacterMenu(charID)
        return charMenu

    def ApplyActionToMembers(self, *args):
        """
            Apply the selected action to those members that have been checked
        """
        action = self.sr.membersPanel.actionCombo.GetValue()
        selectedMembers = self._GetSelectedMembers()
        doClose = False
        if action == ACTION_SETMEMBER:
            if session.charid in selectedMembers:
                ret = eve.Message('MailingListMemberSelfConfirm', {}, uiconst.YESNO)
                if ret != uiconst.ID_YES:
                    return
                doClose = True
            self.mlsvc.SetMembersClear(self.mailingListID, selectedMembers)
        elif action == ACTION_SETMUTED:
            if session.charid in selectedMembers:
                ret = eve.Message('MailingListMuteSelfConfirm', {}, uiconst.YESNO)
                if ret != uiconst.ID_YES:
                    return
                doClose = True
            self.mlsvc.SetMembersMuted(self.mailingListID, selectedMembers)
        elif action == ACTION_SETOPERATOR:
            self.mlsvc.SetMembersOperator(self.mailingListID, selectedMembers)
        elif action == ACTION_KICK:
            self.mlsvc.KickMembers(self.mailingListID, selectedMembers)
            self.UpdateAccessScrollData()
        if doClose:
            self.Close()
        else:
            self.UpdateMembersScroll()

    def _GetSelectedMembers(self):
        selected = []
        for s in self.sr.membersPanel.scroll.GetSelected():
            selected.append(s.retval)

        return selected

    def ClearAccessForSelected(self, *args):
        """
            Remove blocked or allowed access flags from those selected
        """
        selected = self.sr.blockedScroll.GetSelected() + self.sr.allowedScroll.GetSelected()
        if selected:
            for e in selected:
                self.mlsvc.ClearEntityAccess(self.mailingListID, e.retval)

            self.UpdateAccessScrollData()
        else:
            raise UserError('PICKERRORNOTIFY', {'num': 1})

    def AddToBlocked(self, *args):
        self._ModifyAccess(const.mailingListBlocked)

    def AddToAllowed(self, *args):
        self._ModifyAccess(const.mailingListAllowed)

    def _ModifyAccess(self, newAccess):
        """
            Block or allow someone (newAccess: {const.mailingListBlocked or const.mailingListAllowed} )
        """
        ownerID = self.Search(self.sr.blockEdit.GetValue())
        if ownerID is not None:
            self.mlsvc.SetEntityAccess(self.mailingListID, ownerID, newAccess)
            self.UpdateAccessScrollData()

    def UpdateBlockedScroll(self):
        self.sr.blockedScroll.Load(contentList=self.scrolllist[const.mailingListBlocked], headers=[localization.GetByLabel('UI/Generic/NamePerson'), localization.GetByLabel('UI/Common/Type')], customColumnWidths=True)

    def UpdateAllowedScroll(self):
        self.sr.allowedScroll.Load(contentList=self.scrolllist[const.mailingListAllowed], headers=[localization.GetByLabel('UI/Generic/NamePerson'), localization.GetByLabel('UI/Common/Type')], customColumnWidths=True)

    def StartupAccessPanel(self):
        accessPanel = self.sr.accessPanel
        topCont = uiprimitives.Container(name='topCont', parent=accessPanel, align=uiconst.TOTOP, pos=(0, 0, 0, 90))
        comboOptions = [(localization.GetByLabel('UI/EVEMail/MailingLists/PrivateAccess'), const.mailingListBlocked), (localization.GetByLabel('UI/EVEMail/MailingLists/PublicAccess'), const.mailingListAllowed)]
        self.sr.accessPanel.defaultAccessCombo = uicontrols.Combo(label=localization.GetByLabel('UI/EVEMail/MailingLists/DefaultAccessLabel'), parent=topCont, options=comboOptions, name='subcriptionAccessCombo', select=self.mlsvc.GetSettings(self.mailingListID).defaultAccess, pos=(0,
         SPACING,
         0,
         0), width=200)
        uicontrols.Button(parent=topCont, label=localization.GetByLabel('UI/Common/Buttons/Apply'), pos=(0, 41, 0, 0), func=self.ApplySettings, align=uiconst.TOPRIGHT)
        roleComboOptions = [(localization.GetByLabel('UI/EVEMail/MailingLists/Normal'), const.mailingListMemberDefault), (localization.GetByLabel('UI/EVEMail/MailingLists/MutedRole'), const.mailingListMemberMuted)]
        self.sr.accessPanel.defaultRoleCombo = uicontrols.Combo(label=localization.GetByLabel('UI/EVEMail/MailingLists/DefaultMemberRole'), parent=topCont, options=roleComboOptions, name='roleCombo', select=self.mlsvc.GetSettings(self.mailingListID).defaultMemberAccess, pos=(0,
         self.sr.accessPanel.defaultAccessCombo.top + self.sr.accessPanel.defaultAccessCombo.height + SPACING,
         0,
         0), width=200)
        uiprimitives.Line(parent=topCont, align=uiconst.TOBOTTOM)
        addToBlockCont = uiprimitives.Container(name='AddToBlockCont', parent=accessPanel, align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, pos=(0, 0, 0, 22), padding=(0, 20, 0, 0))
        self.sr.blockEdit = uicontrols.SinglelineEdit(label=localization.GetByLabel('UI/EVEMail/MailingLists/EntitySearchLabel'), name='AddToBlockEdit', parent=addToBlockCont, align=uiconst.TOPLEFT, pos=(0, 0, 100, 0))
        b1 = uicontrols.Button(parent=addToBlockCont, label=localization.GetByLabel('UI/EVEMail/MailingLists/Allow'), func=self.AddToAllowed, align=uiconst.CENTERRIGHT)
        uicontrols.Button(parent=addToBlockCont, label=localization.GetByLabel('UI/PeopleAndPlaces/BlockContact'), func=self.AddToBlocked, align=uiconst.CENTERRIGHT, left=b1.width + b1.left + 4)
        self.sr.scrollCont = scrollCont = uiprimitives.Container(name='scrollCont', parent=accessPanel, align=uiconst.TOALL)
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/EVEMail/MailingLists/BlockedLabel'), parent=scrollCont, align=uiconst.TOTOP, top=10, state=uiconst.UI_NORMAL)
        self.sr.blockedScroll = uicontrols.Scroll(parent=scrollCont, name='blockedScroll', align=uiconst.TOTOP)
        self.sr.blockedScroll.OnSetFocus = self.BlockedScrollOnSetFocus
        self.sr.blockedScroll.sr.id = 'blockedScroll'
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/EVEMail/MailingLists/AllowedLabel'), parent=scrollCont, align=uiconst.TOTOP, top=10, state=uiconst.UI_NORMAL)
        self.sr.allowedScroll = uicontrols.Scroll(parent=scrollCont, name='allowedScroll', align=uiconst.TOTOP)
        self.sr.allowedScroll.OnSetFocus = self.AllowedScrollOnSetFocus
        self.sr.allowedScroll.sr.id = 'allowedScroll'
        self.UpdateAccessScrollData()
        uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/EVEMail/MailingLists/RemoveSelected'),
          self.ClearAccessForSelected,
          None,
          None]], parent=accessPanel, line=False)
        self._OnResize()

    def AllowedScrollOnSetFocus(self):
        self.sr.blockedScroll.DeselectAll()

    def BlockedScrollOnSetFocus(self):
        self.sr.allowedScroll.DeselectAll()

    def UpdateAccessScrollData(self):
        """
            Fetches information from server and populates both Blocked and Allowed scrolls,
            since the information is in the same dictionary provided by the mailinglist service
        """
        self.scrolllist = {const.mailingListAllowed: [],
         const.mailingListBlocked: []}
        accessList = self.mlsvc.GetSettings(self.mailingListID).access
        for i, m in enumerate(accessList.iteritems()):
            ownerID, accessLevel = m
            owner = cfg.eveowners.Get(ownerID)
            ownerGroup = cfg.invgroups.Get(owner.groupID)
            data = util.KeyVal()
            data.label = '%s<t>%s' % (owner.name, ownerGroup.name)
            data.props = None
            data.cfgname = 'member'
            data.retval = ownerID
            data.index = i
            self.scrolllist[accessLevel].append(listentry.Get('Generic', data=data))

        self.UpdateAllowedScroll()
        self.UpdateBlockedScroll()

    def ApplySettings(self, *args):
        defaultAccess = self.sr.accessPanel.defaultAccessCombo.GetValue()
        defaultRole = self.sr.accessPanel.defaultRoleCombo.GetValue()
        self.mlsvc.SetDefaultAccess(self.mailingListID, defaultAccess, defaultRole)

    def Search(self, searchStr):
        """
            Find characters/corps/alliances matching the search string. Pops up a selection window
        """
        return uix.SearchOwners(searchStr=searchStr, groupIDs=[const.groupCharacter, const.groupCorporation, const.groupAlliance], hideNPC=True, notifyOneMatch=True, searchWndName='AddToBlockSearch')

    def StartupWelcomePanel(self, *args):
        welcomePanel = self.sr.welcomePanel
        cbCont = uiprimitives.Container(name='cbCont', parent=welcomePanel, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 20))
        self.sr.wekcomeToAllCB = uicontrols.Checkbox(text=localization.GetByLabel('UI/EVEMail/MailingLists/SendWelcomeMailToAllCheckbox'), parent=cbCont, configName='welcomeToAllCB', retval=self.mailingListID, checked=settings.user.ui.Get('welcomeToAllCB_%s' % self.mailingListID, 0), align=uiconst.TOPLEFT, pos=(0, 0, 330, 0), callback=self.OnCheckboxChange)
        subjectCont = uiprimitives.Container(name='subjectCont', parent=welcomePanel, align=uiconst.TOTOP, pos=(0, 0, 0, 30), padding=(0, 0, 1, 0))
        subjectTextCont = uiprimitives.Container(name='subjectCont', parent=subjectCont, align=uiconst.TOLEFT, pos=(0, 0, 40, 0))
        subjectLabel = uicontrols.EveHeaderSmall(text=localization.GetByLabel('UI/EVEMail/MailingLists/WelcomeMailSubject'), parent=subjectTextCont, align=uiconst.TOPLEFT, top=2, left=0, state=uiconst.UI_NORMAL)
        subjectTextCont.width = subjectLabel.textwidth + 5
        self.sr.subjecField = uicontrols.SinglelineEdit(name='subjecField', parent=subjectCont, maxLength=const.mailMaxSubjectSize, pos=(0, 0, 0, 0), label='', align=uiconst.TOTOP)
        self.sr.welcomeScrollCont = scrollCont = uiprimitives.Container(name='scrollCont', parent=welcomePanel, align=uiconst.TOALL)
        self.sr.welcomeEdit = uicls.EditPlainText(setvalue='', parent=self.sr.welcomeScrollCont, align=uiconst.TOALL, showattributepanel=1)
        uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Common/Buttons/Save'),
          self.SaveWelcomeMail,
          None,
          None]], parent=welcomePanel, idx=0, line=False)

    def OnCheckboxChange(self, checkbox, *args):
        value = checkbox.data.get('value', '')
        name = '%s_%s' % (checkbox.name, value)
        settings.user.ui.Set(name, checkbox.checked)

    def UpdateWelcome(self, *args):
        welcomeMail = self.mlsvc.GetWelcomeMail(self.mailingListID)
        if not welcomeMail:
            self.sr.welcomeEdit.SetValue('')
            self.sr.subjecField.SetValue('')
            return
        self.welcomeText = welcomeMail
        mail = welcomeMail[0]
        self.sr.welcomeEdit.SetValue(mail.body)
        self.sr.subjecField.SetValue(mail.title)

    def SaveWelcomeMail(self, *args):
        sendToAll = self.sr.wekcomeToAllCB.GetValue()
        subject = self.sr.subjecField.GetValue()
        body = self.sr.welcomeEdit.GetValue()
        if len(subject) < 1 and len(body) < 1:
            self.mlsvc.ClearWelcomeMail(self.mailingListID)
            return
        if len(subject) < 1:
            raise UserError('NoSubject')
        if sendToAll:
            self.mlsvc.SaveAndSendWelcomeMail(self.mailingListID, subject, body)
        else:
            self.mlsvc.SaveWelcomeMail(self.mailingListID, subject, body)

    def _OnResize(self, *args):
        uthread.new(self.__OnResize)

    def __OnResize(self):
        """
            Resize blocked and allowed scrolls when window is resized
        """
        if self.destroyed or not self.sr.scrollCont:
            return
        aL, aT, aW, aH = self.sr.scrollCont.GetAbsolute()
        newHeight = (aH - 72) / 2
        self.sr.allowedScroll.height = newHeight
        self.sr.blockedScroll.height = newHeight

    def Load(self, key):
        """ 
            Load call for the tabs 
        """
        if key == 'members':
            self.UpdateMembersScroll()
        elif key == 'access':
            self.UpdateAllowedScroll()
            self._OnResize()
        elif key == 'welcome':
            if self.welcomeText is None:
                self.UpdateWelcome()
