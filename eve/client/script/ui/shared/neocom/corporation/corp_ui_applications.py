#Embedded file name: eve/client/script/ui/shared/neocom/corporation\corp_ui_applications.py
from math import pi
from carbonui.primitives.container import Container
from eve.client.script.ui.control import entries as listentry
from carbonui.control.scrollentries import SE_BaseClassCore
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.infoIcon import MoreInfoIcon
import uicls
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import uiutil
import localization
import base
import eve.common.lib.appConst as const
APPLICATION_STATUS_LABELNAMES = {const.crpApplicationAppliedByCharacter: 'UI/Corporations/CorpApplications/ApplicationUnprocessed',
 const.crpApplicationAcceptedByCorporation: 'UI/Corporations/CorpApplications/ApplicationStatusInvited',
 const.crpApplicationRejectedByCorporation: 'UI/Corporations/CorpApplications/ApplicationStatusRejected',
 const.crpApplicationAcceptedByCharacter: 'UI/Corporations/CorpApplications/ApplicationStatusAccepted',
 const.crpApplicationRejectedByCharacter: 'UI/Corporations/CorpApplications/ApplicationStatusInvitationRejected',
 const.crpApplicationWithdrawnByCharacter: 'UI/Corporations/CorpApplications/ApplicationStatusWithdrawn',
 const.crpApplicationInvitedByCorporation: 'UI/Corporations/CorpApplications/ApplicationStatusDirectlyInvited'}
STATUS_SETTING_NAME = 'applicationStatus_%d'

class ApplicationsWindow(uiprimitives.Container):
    __guid__ = 'uicls.ApplicationsTab'
    __nonpersistvars__ = []

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.ownerID = attributes.ownerID
        if self.ownerID == session.charid:
            self.myView = True
        else:
            self.myView = False
        self.quickFilterSetting = 'applicationsQuickFilter_OwnerID%s' % self.ownerID
        self.filteringBy = settings.char.ui.Get(self.quickFilterSetting, '')
        self.showingOld = settings.char.ui.Get('applicationsShowOld_%s' % self.ownerID, False)
        self.InitViewingStatus()
        self.topContainer = uiprimitives.Container(parent=self, name='topContainer', align=uiconst.TOTOP, height=20, padding=const.defaultPadding)
        self.quickFilter = uicls.QuickFilterEdit(parent=self.topContainer, align=uiconst.CENTERRIGHT, setvalue=self.filteringBy)
        self.quickFilter.ReloadFunction = self.OnSearchFieldChanged
        self.quickFilter.OnReturn = self.SearchByCharacterName
        self.statusFilter = uicls.UtilMenu(parent=self.topContainer, align=uiconst.CENTERRIGHT, padding=(1, 1, 1, 1), left=103, GetUtilMenu=self.StatusFilterMenu, texturePath='res:/ui/texture/icons/38_16_205.png', hint=localization.GetByLabel('UI/Corporations/CorpApplications/FilterByStatus'))
        self.inviteButton = Button(name='inviteButton', align=uiconst.CENTERLEFT, parent=self.topContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/InviteToCorp'), func=self.OpenInviteWindow)
        if not const.corpRolePersonnelManager & session.corprole == const.corpRolePersonnelManager:
            self.inviteButton.display = False
        if self.myView:
            self.topContainer.display = False
        self.applicationContainer = uiprimitives.Container(name='applications', parent=self, align=uiconst.TOALL, padding=const.defaultPadding)
        self.applicationScroll = uicontrols.BasicDynamicScroll(name='applicationsScroll', parent=self.applicationContainer, align=uiconst.TOALL)
        self.applicationScroll.noContentHint = localization.GetByLabel('UI/Corporations/CorpApplications/NoApplicationsFound')
        self.applicationScroll.multiSelect = 0

    def OpenInviteWindow(self, *args):
        InviteToCorpWnd.CloseIfOpen('InviteToCorpWnd')
        InviteToCorpWnd.Open()

    def GetApplications(self, statusList = None):
        """
            Method to fetch applications according to chosen filters
        """
        if statusList is None:
            statusList = self.sr.viewingStatus
        filteredApplications = []
        if self.ownerID == session.corpid:
            if const.corpRolePersonnelManager & session.corprole != const.corpRolePersonnelManager:
                return []
            if self.showingOld:
                applications = sm.GetService('corp').GetOldApplicationsWithStatus(statusList)
            else:
                applications = sm.GetService('corp').GetApplicationsWithStatus(statusList)
            if len(self.filteringBy):
                ownersToPrime = set()
                for application in applications:
                    ownersToPrime.add(application.characterID)

                if len(ownersToPrime) > 0:
                    cfg.eveowners.Prime(ownersToPrime)
                for application in applications:
                    if cfg.eveowners.Get(application.characterID).name.lower().find(self.filteringBy.lower()) > -1:
                        filteredApplications.append(application)

            else:
                filteredApplications = applications
        elif self.showingOld:
            filteredApplications = sm.GetService('corp').GetMyOldApplicationsWithStatus(None)
        else:
            filteredApplications = sm.GetService('corp').GetMyApplicationsWithStatus(None)
        return filteredApplications

    def GetCorpApplicationEntries(self, applications):
        """
            Common method to turn application rows into application list entries
        """
        ownersToPrime = set()
        scrolllist = []
        if self.myView:
            ownerKey = 'corporationID'
        else:
            ownerKey = 'characterID'
        expandedApp = settings.char.ui.Get('corporation_applications_expanded', {})
        for application in applications:
            ownerID = getattr(application, ownerKey, None)
            if ownerID is None:
                continue
            ownersToPrime.add(ownerID)
            if len(ownersToPrime):
                cfg.eveowners.Prime(ownersToPrime)
            data = {'myView': self.myView,
             'application': application,
             'sort_%s' % localization.GetByLabel('UI/Common/Date'): application.applicationDateTime,
             'charID': application.characterID,
             'isExpanded': expandedApp.get(self.myView, None) == application.applicationID}
            entry = listentry.Get('CorpApplicationEntry', data)
            scrolllist.append(entry)

        return scrolllist

    def OnSearchFieldChanged(self):
        """
            Called to clear the filter, filter is applied in GetApplications
        """
        myFilter = self.quickFilter.GetValue().strip()
        if myFilter == '':
            self.filteringBy = myFilter
            settings.char.ui.Set(self.quickFilterSetting, self.filteringBy)
            applications = self.GetApplications()
            scrolllist = self.GetCorpApplicationEntries(applications)
            self.RefreshApplicationScroll(addNodes=scrolllist, forceClear=True)

    def SearchByCharacterName(self, *args):
        """
            Called to set the filter, filter is applied in GetApplications
        """
        myFilter = self.quickFilter.GetValue().strip()
        if len(myFilter) == 0:
            return
        self.filteringBy = myFilter
        applications = self.GetApplications()
        scrolllist = self.GetCorpApplicationEntries(applications)
        self.RefreshApplicationScroll(addNodes=scrolllist, forceClear=True)

    def StatusFilterMenu(self, menuParent):
        """
            Creates the checkbox menu for status filtering
        """
        for applicationStatusID in APPLICATION_STATUS_LABELNAMES:
            if applicationStatusID == const.crpApplicationRejectedByCharacter:
                continue
            isChecked = _LoadApplicationFilterSetting(applicationStatusID, False)
            menuParent.AddCheckBox(_GetApplicationStatusLabel(applicationStatusID), checked=isChecked, callback=(self.ToggleStatusFilter, applicationStatusID, isChecked))

        menuParent.AddDivider()
        menuParent.AddCheckBox(localization.GetByLabel('UI/Corporations/CorpApplications/ShowOldApplications'), checked=self.showingOld, callback=(self.SetShowOld, not self.showingOld))

    def SetShowOld(self, value):
        """
            Called when Show Old is checked or dechecked, functionality is in GetApplications
        """
        settings.char.ui.Set('applicationsShowOld_%s' % self.ownerID, value)
        self.showingOld = value
        applications = self.GetApplications()
        scrolllist = self.GetCorpApplicationEntries(applications)
        self.RefreshApplicationScroll(addNodes=scrolllist, forceClear=True)

    def ToggleStatusFilter(self, applicationStatusID, isChecked):
        """
            Called when any status filter is checked or dechecked.
            This method will add/remove nodes in a very controlled manner so we can avoid clearing the scroll
        """
        viewingStatus = []
        if isChecked:
            removeNodes = []
            _SaveApplicationFilterSetting(applicationStatusID, False)
            for status in self.sr.viewingStatus:
                if status != applicationStatusID:
                    viewingStatus.append(status)

            for applicationNode in self.applicationScroll.GetNodes():
                if applicationNode.application.status not in viewingStatus:
                    removeNodes.append(applicationNode)

            self.RefreshApplicationScroll(removeNodes=removeNodes)
        else:
            _SaveApplicationFilterSetting(applicationStatusID, True)
            viewingStatus.append(applicationStatusID)
            viewingStatus.extend(self.sr.viewingStatus)
            applications = self.GetApplications([applicationStatusID])
            scrolllist = self.GetCorpApplicationEntries(applications)
            if len(scrolllist) > 0:
                self.RefreshApplicationScroll(addNodes=scrolllist)
        self.sr.viewingStatus = viewingStatus

    def InitViewingStatus(self):
        viewingStatus = []
        for applicationStatusID in APPLICATION_STATUS_LABELNAMES:
            if self.ownerID == session.charid:
                viewingStatus.append(applicationStatusID)
            elif _LoadApplicationFilterSetting(applicationStatusID, False):
                viewingStatus.append(applicationStatusID)

        if len(viewingStatus) == 0:
            viewingStatus = [const.crpApplicationAppliedByCharacter]
            _SaveApplicationFilterSetting(const.crpApplicationAppliedByCharacter, True)
        self.sr.viewingStatus = viewingStatus

    def LoadApplications(self):
        if self.destroyed:
            return
        try:
            myFilter = self.quickFilter.GetValue()
            if len(myFilter):
                self.filteringBy = myFilter
            sm.GetService('corpui').ShowLoad()
            applications = self.GetApplications()
            scrolllist = self.GetCorpApplicationEntries(applications)
            if len(scrolllist) > 0:
                self.RefreshApplicationScroll(addNodes=scrolllist)
        except:
            pass
        finally:
            sm.GetService('corpui').HideLoad()

    def RefreshApplicationScroll(self, addNodes = [], removeNodes = [], reloadNodes = [], forceClear = False):
        """
            Wrapper for node manipulation to enforce node order on all calls.
        """
        if forceClear:
            self.applicationScroll.Clear()
        elif len(removeNodes):
            self.applicationScroll.RemoveNodes(removeNodes, updateScroll=True)
        if len(reloadNodes):
            self.applicationScroll.ReloadNodes(reloadNodes)
        if len(addNodes):
            self.applicationScroll.AddNodes(0, addNodes, updateScroll=True)
        toSort = self.applicationScroll.GetNodes()
        if toSort:
            sortedNodes = sorted(toSort, key=lambda x: x.application.applicationDateTime, reverse=True)
            self.applicationScroll.SetOrderedNodes(sortedNodes)

    def OnCorporationApplicationChanged(self, corpID, applicantID, applicationID, newApplication):
        """
            Updates applications when they are acted on. Will not clear scroll as the changes are very controlled.
        """
        if self.destroyed:
            return
        for applicationNode in self.applicationScroll.GetNodes():
            if applicationNode.application.applicationID == applicationID:
                applicationNode.application = newApplication
                if newApplication.status in self.sr.viewingStatus:
                    self.RefreshApplicationScroll(reloadNodes=[applicationNode])
                else:
                    self.RefreshApplicationScroll(removeNodes=[applicationNode])
                break
        else:
            if newApplication.status in self.sr.viewingStatus:
                scrolllist = self.GetCorpApplicationEntries([newApplication])
                self.RefreshApplicationScroll(addNodes=scrolllist)


class ViewCorpApplicationWnd(uicontrols.Window):
    __guid__ = 'form.ViewCorpApplicationWnd'
    default_width = 400
    default_height = 255
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        self.charID = attributes.get('characterID')
        self.appText = attributes.get('applicationText')
        self.status = attributes.get('status')
        wndCaption = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplicationDetailCaption')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.ConstructLayout()

    def ConstructLayout(self):
        charInfoCont = uiprimitives.Container(name='charInfo', parent=self.sr.main, align=uiconst.TOTOP, height=68, padding=const.defaultPadding)
        charLogoCont = uiprimitives.Container(name='charLogo', parent=charInfoCont, align=uiconst.TOLEFT, width=68)
        charTextCont = uiprimitives.Container(name='charName', parent=charInfoCont, align=uiconst.TOALL)
        applicationCont = uiprimitives.Container(name='charInfo', parent=self.sr.main, align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        uiutil.GetOwnerLogo(charLogoCont, self.charID, size=64, noServerCall=True)
        charText = localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationSubjectLine', player=self.charID)
        charNameLabel = uicontrols.EveLabelLarge(parent=charTextCont, text=charText, top=12, align=uiconst.TOPLEFT, width=270)
        editText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CorporationApplicationText')
        editLabel = uicontrols.EveLabelSmall(parent=applicationCont, text=editText, align=uiconst.TOTOP)
        self.rejectRb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/RejectApplication'), parent=applicationCont, configName='reject', retval=1, checked=False, groupname='state', align=uiconst.TOBOTTOM)
        self.acceptRb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationInviteApplicant'), parent=applicationCont, configName='accept', retval=0, checked=True, groupname='state', align=uiconst.TOBOTTOM)
        if self.status not in const.crpApplicationActiveStatuses:
            self.rejectRb.state = uiconst.UI_HIDDEN
            self.acceptRb.state = uiconst.UI_HIDDEN
        self.applicationText = uicls.EditPlainText(setvalue=self.appText, parent=applicationCont, maxLength=1000, readonly=True)

    def Confirm(self, *args):
        if self.status not in const.crpApplicationActiveStatuses:
            self.Cancel()
        applicationText = self.applicationText.GetValue()
        if len(applicationText) > 1000:
            error = localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationTextTooLong', length=len(applicationText))
            eve.Message('CustomInfo', {'info': error})
        else:
            if self.rejectRb.checked:
                rejected = const.crpApplicationRejectedByCorporation
            else:
                rejected = const.crpApplicationAcceptedByCorporation
            self.result = rejected
            self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)


class MyCorpApplicationWnd(uicontrols.Window):
    __guid__ = 'form.MyCorpApplicationWnd'
    default_width = 400
    default_height = 300
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.corpid = attributes.get('corpid')
        self.application = attributes.get('application')
        self.status = attributes.get('status')
        self.windowID = 'viewApplicationWindow'
        if self.status in const.crpApplicationActiveStatuses:
            self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        else:
            self.DefineButtons(uiconst.OK, okFunc=self.Cancel)
        wndCaption = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplicationDetailCaption')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.ConstructLayout()

    def ConstructLayout(self):
        self.acceptRb = None
        self.withdrawRb = None
        corpName = cfg.eveowners.Get(self.corpid).name
        corpInfoCont = uiprimitives.Container(name='corpInfo', parent=self.sr.main, align=uiconst.TOTOP, height=68, padding=const.defaultPadding)
        corpLogoCont = uiprimitives.Container(name='corpLogo', parent=corpInfoCont, align=uiconst.TOLEFT, width=68)
        corpTextCont = uiprimitives.Container(name='corpName', parent=corpInfoCont, align=uiconst.TOALL)
        controlCont = uiprimitives.Container(name='buttons', parent=self.sr.main, align=uiconst.TOBOTTOM, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        controlContHeight = 0
        applicationCont = uiprimitives.Container(name='applicationCont', parent=self.sr.main, align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        uiutil.GetOwnerLogo(corpLogoCont, self.corpid, size=64, noServerCall=True)
        corpText = localization.GetByLabel('UI/Corporations/CorpApplications/YourApplicationToJoin', corpName=corpName)
        corpNameLabel = uicontrols.EveLabelLarge(parent=corpTextCont, text=corpText, top=12, align=uiconst.TOPLEFT, width=270)
        if self.status == const.crpApplicationAppliedByCharacter:
            statusText = localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationNotProcessed')
            statusLabel = uicontrols.EveLabelSmall(parent=applicationCont, text=statusText, align=uiconst.TOTOP, padBottom=const.defaultPadding)
        else:
            statusText = statusLabel = ''
        editText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CorporationApplicationText')
        editLabel = uicontrols.EveLabelSmall(parent=applicationCont, text=editText, align=uiconst.TOTOP)
        if self.application.applicationText is not None:
            appText = self.application.applicationText
        else:
            appText = ''
        self.applicationText = uicls.EditPlainText(setvalue=appText, parent=applicationCont, maxLength=1000, readonly=True)
        if self.status in const.crpApplicationActiveStatuses:
            isWithdrawChecked = True
            if self.status in (const.crpApplicationAcceptedByCorporation, const.crpApplicationInvitedByCorporation):
                isWithdrawChecked = False
                self.acceptRb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/AcceptApplication'), parent=controlCont, configName='accept', retval=1, checked=True, groupname='stateGroup', align=uiconst.TOBOTTOM)
                controlContHeight += 40
            self.withdrawRb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/WithdrawApplication'), parent=controlCont, configName='accept', retval=3, checked=isWithdrawChecked, groupname='stateGroup', align=uiconst.TOBOTTOM)
            controlContHeight += 20
        controlCont.height = controlContHeight

    def Confirm(self, *args):
        self.result = None
        if self.withdrawRb.checked:
            self.result = const.crpApplicationWithdrawnByCharacter
        elif self.acceptRb.checked:
            self.result = const.crpApplicationAcceptedByCharacter
        self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)

    def WithdrawApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.application
            sm.GetService('corpui').ShowLoad()
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationWithdrawnByCharacter)
        finally:
            sm.GetService('corpui').HideLoad()
            uicontrols.Window.CloseIfOpen(windowID='viewApplicationWindow')


class ApplyToCorpWnd(uicontrols.Window):
    __guid__ = 'form.ApplyToCorpWnd'
    default_width = 400
    default_height = 245
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        self.corpid = attributes.get('corpid')
        self.corporation = attributes.get('corporation')
        wndCaption = localization.GetByLabel('UI/Corporations/BaseCorporationUI/JoinCorporation')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.ConstructLayout()

    def ConstructLayout(self):
        corpName = cfg.eveowners.Get(self.corpid).name
        corpInfoCont = uiprimitives.Container(name='corpInfo', parent=self.sr.main, align=uiconst.TOTOP, height=68, padding=const.defaultPadding)
        corpLogoCont = uiprimitives.Container(name='corpLogo', parent=corpInfoCont, align=uiconst.TOLEFT, width=68)
        corpTextCont = uiprimitives.Container(name='corpName', parent=corpInfoCont, align=uiconst.TOALL)
        applicationCont = uiprimitives.Container(name='corpInfo', parent=self.sr.main, align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        uiutil.GetOwnerLogo(corpLogoCont, self.corpid, size=64, noServerCall=True)
        corpText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/ApplyForMembership', corporation=corpName)
        corpNameLabel = uicontrols.EveLabelLarge(parent=corpTextCont, text=corpText, top=12, align=uiconst.TOPLEFT, width=270)
        editText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CorporationApplicationText')
        editLabel = uicontrols.EveLabelSmall(parent=applicationCont, text=editText, align=uiconst.TOTOP)
        tax = self.corporation.taxRate * 100
        taxText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CurrentTaxRateForCorporation', corporation=corpName, taxRate=tax)
        taxLabel = uicontrols.EveLabelSmall(parent=applicationCont, text=taxText, align=uiconst.TOBOTTOM)
        corpService = sm.GetService('corp')
        aggressionSettings = corpService.GetAggressionSettings(self.corpid)
        statusText = corpService.GetCorpFriendlyFireStatus(aggressionSettings)
        ffText = localization.GetByLabel('UI/Corporations/FriendlyFire/FriendlyFireStatus', ffStatus=statusText)
        ffCont = uiprimitives.Container(parent=applicationCont, align=uiconst.TOBOTTOM, height=16)
        friendlyFireLabel = uicontrols.EveLabelSmall(parent=ffCont, text=ffText, align=uiconst.TOLEFT)
        helpIcon = MoreInfoIcon(parent=ffCont, align=uiconst.TORIGHT, hint=localization.GetByLabel('UI/Corporations/FriendlyFire/Description'))
        if self.corporation and not self.corporation.isRecruiting:
            notRecruitingText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/RecruitmentMayBeClosed')
            notRecruiting = uicontrols.EveLabelSmall(parent=applicationCont, text=notRecruitingText, align=uiconst.TOBOTTOM, idx=0)
            self.SetMinSize((self.default_width, self.default_height + notRecruiting.textheight), refresh=True)
        self.applicationText = uicls.EditPlainText(setvalue='', parent=applicationCont, align=uiconst.TOALL, maxLength=1000)

    def Confirm(self, *args):
        applicationText = self.applicationText.GetValue()
        if len(applicationText) > const.crpApplicationMaxSize:
            error = localization.GetByLabel('UI/Corporations/BaseCorporationUI/ApplicationTextTooLong', length=len(applicationText))
            eve.Message('CustomInfo', {'info': error})
        else:
            self.result = applicationText
            self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)


class CorpApplicationEntry(SE_BaseClassCore):
    __guid__ = 'listentry.CorpApplicationEntry'
    __notifyevents__ = []
    LOGOPADDING = 70
    TEXTPADDING = 18
    CORPNAMEPAD = (LOGOPADDING,
     0,
     0,
     0)
    EXTENDEDPAD = (LOGOPADDING,
     const.defaultPadding,
     const.defaultPadding,
     const.defaultPadding)
    CORPNAMECLASS = uicontrols.EveLabelLarge
    EXTENDEDCLASS = uicontrols.EveLabelMedium
    APPHEADERHEIGHT = 53

    def PreLoad(node):
        application = node.application

    def Startup(self, *args):
        node = self.sr.node
        self.corpSvc = sm.GetService('corp')
        self.lscSvc = sm.GetService('LSC')
        self.viewButton = None
        self.removeButton = None
        self.rejectButton = None
        self.acceptButton = None
        self.ownerID = None
        if node.myView:
            self.ownerID = node.application.corporationID
        else:
            self.ownerID = node.application.characterID
        self.entryContainer = uiprimitives.Container(parent=self)
        self.headerContainer = uiprimitives.Container(parent=self.entryContainer, align=uiconst.TOTOP, name='applicationHeaderContainer', height=self.APPHEADERHEIGHT)
        self.expander = uiprimitives.Sprite(parent=self.headerContainer, state=uiconst.UI_DISABLED, name='expander', pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/Shared/getMenuIcon.png', align=uiconst.CENTERLEFT)
        if node.isExpanded:
            self.expander.rotation = -pi * 0.5
        logoParent = uiprimitives.Container(parent=self.headerContainer, align=uiconst.TOPLEFT, pos=(16, 2, 48, 48))
        uiutil.GetOwnerLogo(logoParent, self.ownerID, size=48, noServerCall=True)
        logoParent.children[0].OnMouseEnter = self.OnMouseEnter
        logoParent.children[0].OnClick = self.ShowOwnerInfo
        self.nameLabel = self.CORPNAMECLASS(parent=self.headerContainer, name='nameLabel', state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, padding=self.CORPNAMEPAD)
        self.expandedParent = uiprimitives.Container(parent=self.entryContainer, name='expandedParent', height=0)
        self.expandedLabel = self.EXTENDEDCLASS(parent=self.expandedParent, name='applicationText', text=node.application.applicationText, padding=self.EXTENDEDPAD, align=uiconst.TOALL)
        self.hilite = uiprimitives.Fill(bgParent=self.headerContainer, color=(1, 1, 1, 0))
        uiprimitives.Fill(bgParent=self.expandedParent, color=(0, 0, 0, 0.2))

    def Load(self, node):
        ownerName = cfg.eveowners.Get(self.ownerID).ownerName
        applicationDate = localization.GetByLabel('UI/Corporations/Applications/ApplicationDate', applicationDateTime=node.application.applicationDateTime)
        statusText = '<fontsize=12>%s</fontsize>' % _GetApplicationStatusLabel(node.application.status)
        nameStatusAndDate = '<b>%s - %s</b><br>%s' % (ownerName, statusText, applicationDate)
        self.nameLabel.text = nameStatusAndDate
        addPadding = const.defaultPadding
        if node.myView:
            if node.application.status not in const.crpApplicationEndStatuses:
                if self.removeButton is not None and not self.removeButton.destroyed:
                    self.removeButton.left = addPadding
                else:
                    if node.application.status == const.crpApplicationInvitedByCorporation:
                        label = localization.GetByLabel('UI/Corporations/CorpApplications/DeclineInvitation')
                    else:
                        label = (localization.GetByLabel('UI/Corporations/CorpApplications/WithdrawApplication'),)
                    self.removeButton = uicontrols.Button(name='removeButton', parent=self.headerContainer, label=label, align=uiconst.CENTERRIGHT, left=addPadding, func=self.WithdrawMyApplication)
                addPadding += self.removeButton.width + const.defaultPadding
            elif self.removeButton is not None:
                self.removeButton.Close()
                self.removeButton = None
            if node.myView and node.application.status in (const.crpApplicationAcceptedByCorporation, const.crpApplicationInvitedByCorporation):
                if self.acceptButton is not None and not self.acceptButton.destroyed:
                    self.acceptButton.left = addPadding
                else:
                    self.acceptButton = uicontrols.Button(name='acceptButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/AcceptApplication'), align=uiconst.CENTERRIGHT, left=addPadding, func=self.AcceptInvitation)
            elif self.acceptButton is not None:
                self.acceptButton.Close()
                self.acceptButton = None
        else:
            if node.application.status == const.crpApplicationAppliedByCharacter:
                if self.acceptButton is not None and not self.acceptButton.destroyed:
                    self.acceptButton.left = addPadding
                else:
                    self.acceptButton = uicontrols.Button(name='acceptButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationInviteApplicant'), align=uiconst.CENTERRIGHT, left=addPadding, func=self.AcceptCorpApplication)
                addPadding += self.acceptButton.width + const.defaultPadding
            elif self.acceptButton is not None:
                self.acceptButton.Close()
                self.acceptButton = None
            if node.application.status not in const.crpApplicationEndStatuses:
                if self.rejectButton is not None and not self.rejectButton.destroyed:
                    self.rejectButton.left = addPadding
                else:
                    self.rejectButton = uicontrols.Button(name='rejectButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/RejectApplication'), align=uiconst.CENTERRIGHT, left=addPadding, func=self.RejectCorpApplication)
            elif self.rejectButton is not None:
                self.rejectButton.Close()
                self.rejectButton = None
        if node.fadeSize is not None:
            toHeight, fromHeight = node.fadeSize
            self.expandedParent.opacity = 0.0
            uicore.animations.MorphScalar(self, 'height', startVal=fromHeight, endVal=toHeight, duration=0.3)
            uicore.animations.FadeIn(self.expandedParent, duration=0.3)
        node.fadeSize = None
        if node.isExpanded:
            self.expandedParent.display = True
            self.expandedLabel.text = node.application.applicationText.strip()
            rotValue = -pi * 0.5
        else:
            rotValue = 0.0
            self.expandedParent.display = False
        uicore.animations.MorphScalar(self.expander, 'rotation', self.expander.rotation, rotValue, duration=0.15)

    def OnClick(self):
        node = self.sr.node
        reloadNodes = [node]
        if node.isExpanded:
            uicore.animations.Tr2DRotateTo(self.expander, -pi * 0.5, 0.0, duration=0.15)
            node.isExpanded = False
            allNodes = settings.char.ui.Get('corporation_applications_expanded', {})
            allNodes[node.myView] = None
            settings.char.ui.Set('corporation_applications_expanded', allNodes)
        else:
            for otherNode in node.scroll.sr.nodes:
                if otherNode.isExpanded and otherNode != node:
                    otherNode.isExpanded = False
                    reloadNodes.append(otherNode)

            uicore.animations.Tr2DRotateTo(self.expander, 0.0, -pi * 0.5, duration=0.15)
            node.isExpanded = True
            node.fadeSize = (CorpApplicationEntry.GetDynamicHeight(node, self.width), self.height)
            allNodes = settings.char.ui.Get('corporation_applications_expanded', {})
            allNodes[node.myView] = node.application.applicationID
            settings.char.ui.Set('corporation_applications_expanded', allNodes)
        self.sr.node.scroll.ReloadNodes(reloadNodes, updateHeight=True)

    def GetMenu(self):
        node = self.sr.node
        menu = [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowOwnerInfo)]
        if node.myView:
            if node.application.status not in const.crpApplicationEndStatuses:
                if node.application.status == const.crpApplicationInvitedByCorporation:
                    label = uiutil.MenuLabel('UI/Corporations/CorpApplications/DeclineInvitation')
                else:
                    label = uiutil.MenuLabel('UI/Corporations/CorpApplications/WithdrawApplication')
                menu.append((label, self.WithdrawMyApplication))
            if node.application.status in (const.crpApplicationAcceptedByCorporation, const.crpApplicationInvitedByCorporation):
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/AcceptApplication'), self.AcceptInvitation))
        elif const.corpRolePersonnelManager & session.corprole == const.corpRolePersonnelManager:
            if node.application.status == const.crpApplicationAppliedByCharacter:
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/ApplicationInviteApplicant'), self.AcceptCorpApplication))
            if node.application.status not in const.crpApplicationEndStatuses:
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/RejectApplication'), self.RejectCorpApplication))
        return menu

    def GetDynamicHeight(node, width):
        """
            Black magic at work. A static object method that is necessary for the fancy expanding UI.
        """
        entryClass = CorpApplicationEntry
        if node.isExpanded:
            lp, tp, rp, bp = entryClass.EXTENDEDPAD
            textWidth, textHeight = entryClass.EXTENDEDCLASS.MeasureTextSize(node.application.applicationText, width=width - (lp + rp))
            textHeight = textHeight + entryClass.APPHEADERHEIGHT + tp + bp
            return textHeight
        else:
            return entryClass.APPHEADERHEIGHT

    def ShowOwnerInfo(self):
        owner = cfg.eveowners.Get(self.ownerID)
        sm.GetService('info').ShowInfo(owner.typeID, owner.ownerID)

    def OnMouseEnter(self, *args):
        uicore.animations.FadeIn(self.hilite, 0.05, duration=0.1)
        self.hiliteTimer = base.AutoTimer(1, self._CheckIfStillHilited)

    def _CheckIfStillHilited(self):
        if uiutil.IsUnder(uicore.uilib.mouseOver, self) or uicore.uilib.mouseOver is self:
            return
        uicore.animations.FadeOut(self.hilite, duration=0.3)
        self.hiliteTimer = None

    def AcceptInvitation(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationAcceptedByCharacter)
        finally:
            sm.GetService('corpui').HideLoad()
            uicontrols.Window.CloseIfOpen(windowID='viewApplicationWindow')

    def WithdrawMyApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationWithdrawnByCharacter)
        finally:
            sm.GetService('corpui').HideLoad()
            uicontrols.Window.CloseIfOpen(windowID='viewApplicationWindow')

    def AcceptCorpApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationAcceptedByCorporation)
        finally:
            sm.GetService('corpui').HideLoad()
            uicontrols.Window.CloseIfOpen(windowID='viewApplicationWindow')

    def RejectCorpApplication(self, *args):
        RejectCorpApplicationWnd.CloseIfOpen(windowID='rejectCorpApplication')
        application = self.sr.node.application
        RejectCorpApplicationWnd.Open(application=application)


def _GetApplicationStatusLabel(applicationStatusID):
    return localization.GetByLabel(APPLICATION_STATUS_LABELNAMES[applicationStatusID])


def _LoadApplicationFilterSetting(applicationStatusID, default):
    return settings.char.ui.Get(_GetSettingsKeyName(applicationStatusID), default)


def _SaveApplicationFilterSetting(applicationStatusID, value):
    settings.char.ui.Set(_GetSettingsKeyName(applicationStatusID), value)


def _GetSettingsKeyName(applicationStatusID):
    return STATUS_SETTING_NAME % applicationStatusID


class RejectCorpApplicationWnd(uicontrols.Window):
    __guid__ = 'form.RejectCorpApplicationWnd'
    default_width = 400
    default_height = 280
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.application = attributes.application
        self.windowID = 'rejectCorpApplication'
        self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Reject, cancelFunc=self.Cancel, okLabel=localization.GetByLabel('UI/Corporations/CorpApplications/RejectApplication'))
        wndCaption = localization.GetByLabel('UI/Corporations/Applications/ApplicationRejection')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        topCont = Container(parent=self.sr.main, align=uiconst.TOTOP, height=58)
        textCont = Container(parent=self.sr.main, align=uiconst.TOALL, padding=8)
        charName = cfg.eveowners.Get(self.application.characterID).name
        corpName = cfg.eveowners.Get(self.application.corporationID).name
        logoParent = uiprimitives.Container(parent=topCont, align=uiconst.TOPLEFT, pos=(8, 6, 48, 48))
        uiutil.GetOwnerLogo(logoParent, self.application.characterID, size=48, noServerCall=True)
        characterLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=charName, info=('showinfo', const.typeCharacterAmarr, self.application.characterID))
        nameLabel = EveLabelMedium(parent=topCont, left=64, top=12, text=characterLink, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        applicationDate = localization.GetByLabel('UI/Corporations/Applications/ApplicationDate', applicationDateTime=self.application.applicationDateTime)
        dateLabel = EveLabelMedium(parent=topCont, left=64, top=2, text=applicationDate, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        messageLabel = EveLabelMedium(parent=textCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationRejectionText', charName=charName, corpName=corpName))
        regardsLabel = EveLabelMedium(parent=textCont, align=uiconst.TOBOTTOM, text=localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationRejectionRegards', corpName=corpName), padTop=4)
        self.messageTextEdit = uicls.EditPlainText(parent=textCont, maxLength=4000, hintText=localization.GetByLabel('UI/Corporations/CorpApplications/CorpRejectionMessage'), top=4)

    def Reject(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            customMessage = self.messageTextEdit.GetValue()
            sm.GetService('corp').UpdateApplicationOffer(self.application.applicationID, self.application.characterID, self.application.corporationID, self.application.applicationText, const.crpApplicationRejectedByCorporation, customMessage=customMessage)
        finally:
            sm.GetService('corpui').HideLoad()
            uicontrols.Window.CloseIfOpen(windowID='viewApplicationWindow')
            self.Close()

    def Cancel(self, *args):
        self.Close()


class InviteToCorpWnd(uicontrols.Window):
    __guid__ = 'form.InviteToCorpWnd'
    default_width = 320
    default_height = 300
    default_windowID = 'InviteToCorpWnd'
    default_iconNum = 'res:/ui/Texture/WindowIcons/corporation.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.searchStr = ''
        self.scope = 'all'
        self.SetMinSize([320, 300])
        self.SetWndIcon(self.iconNum)
        self.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.scroll.Startup()
        self.scroll.multiSelect = 0
        self.standardBtns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Ship/ShipConfig/Invite'),
          self.InviteToCorp,
          (),
          81], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.OnCancel,
          (),
          81]])
        self.inviteButton = self.standardBtns.GetBtnByIdx(0)
        self.inviteButton.Disable()
        self.sr.main.children.insert(0, self.standardBtns)
        self.SetCaption(localization.GetByLabel('UI/Messages/SelectCharacterTitle'))
        self.label = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Shared/TypeSearchString'), parent=self.sr.topParent, left=70, top=16, state=uiconst.UI_NORMAL)
        self.nameInput = uicontrols.SinglelineEdit(name='edit', parent=self.sr.topParent, pos=(70,
         self.label.top + self.label.height + 2,
         86,
         0), align=uiconst.TOPLEFT, maxLength=32)
        self.nameInput.OnReturn = self.Search
        btn = uicontrols.Button(parent=self.sr.topParent, label=localization.GetByLabel('UI/Wallet/WalletWindow/WalletSearch'), pos=(self.nameInput.left + self.nameInput.width + 2,
         self.nameInput.top,
         0,
         0), func=self.Search, btn_default=1)
        self.SetHint(localization.GetByLabel('UI/Common/TypeInSearch'))

    def Search(self, *args):
        scrolllist = []
        self.inviteButton.Disable()
        self.ShowLoad()
        try:
            self.searchStr = self.GetSearchStr()
            self.SetHint()
            if len(self.searchStr) < 1:
                self.SetHint(localization.GetByLabel('UI/Shared/PleaseTypeSomething'))
                return
            result = sm.RemoteSvc('lookupSvc').LookupEvePlayerCharacters(self.searchStr, 0)
            if result is None or not len(result):
                self.SetHint(localization.GetByLabel('EVE/UI/Wallet/WalletWindow/SearchNoResults'))
                return
            cfg.eveowners.Prime([ each.characterID for each in result ])
            for each in result:
                owner = cfg.eveowners.Get(each.characterID)
                scrolllist.append(listentry.Get('Item', {'label': owner.name,
                 'typeID': owner.typeID,
                 'itemID': each.characterID,
                 'OnClick': self.EnableInviteButton,
                 'OnDblClick': self.InviteToCorp}))

        finally:
            self.scroll.Load(fixedEntryHeight=18, contentList=scrolllist, noContentHint=localization.GetByLabel('UI/Wallet/WalletWindow/SearchNoResults'))
            self.HideLoad()

    def EnableInviteButton(self, *args):
        if self.GetSelected:
            self.inviteButton.Enable()

    def GetSearchStr(self):
        return self.nameInput.GetValue().strip()

    def SetHint(self, hintstr = None):
        if self.scroll:
            self.scroll.ShowHint(hintstr)

    def InviteToCorp(self, *args):
        sel = self.GetSelected()
        if sel:
            charID = sel[0].itemID
            sm.StartService('corp').InviteToJoinCorp(charID)
            self.CloseByUser()

    def GetSelected(self):
        sel = self.scroll.GetSelected()
        return sel

    def OnCancel(self, *args):
        self.CloseByUser()
