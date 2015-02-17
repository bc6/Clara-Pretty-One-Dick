#Embedded file name: eve/client/script/ui/shared/neocom/corporation\corp_ui_home.py
import sys
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.entries import LabelTextTop
from eve.client.script.ui.control.infoIcon import InfoIcon, MoreInfoIcon
from eve.client.script.ui.control.themeColored import LineThemeColored
import blue
import uiprimitives
import uicontrols
import util
import uix
import uiutil
import form
import listentry
import log
import moniker
import uicls
import carbonui.const as uiconst
import localization
from carbon.common.script.sys.row import Row

class CorpUIHome(uiprimitives.Container):
    __guid__ = 'form.CorpUIHome'
    __nonpersistvars__ = []

    def _OnClose(self, *args):
        if self.sr.Get('offices', None) is not None:
            self.sr.offices.RemoveListener(self)

    def Load(self, args):
        self.canEditCorp = not util.IsNPC(eve.session.corpid) and const.corpRoleDirector & eve.session.corprole == const.corpRoleDirector
        sm.GetService('corpui').LoadTop(None, None)
        if not self.sr.Get('inited', 0):
            self.OnInitializePanel()

    def OnInitializePanel(self):
        if not self or self.destroyed:
            return
        self.sr.inited = 1
        if not self.sr.Get('offices'):
            self.sr.offices = None
        self.topContainer = uiprimitives.Container(name='topContainer', align=uiconst.TOTOP, parent=self, height=54)
        self.mainContainer = uiprimitives.Container(name='mainContainer', align=uiconst.TOALL, pos=(0, 0, 0, 0), parent=self)
        self.logoContainer = uiprimitives.Container(name='logoContainer', align=uiconst.TOLEFT, parent=self.topContainer, width=60)
        self.captionContainer = uiprimitives.Container(name='captionContainer', align=uiconst.TOALL, pos=(10, 8, 10, 8), parent=self.topContainer)
        self.LoadLogo(eve.session.corpid)
        bulletinParent = uiprimitives.Container(name='bulletinParent', parent=self.mainContainer, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        detailsParent = uiprimitives.Container(name='detailsParent', parent=self.mainContainer, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        tabs = [[localization.GetByLabel('UI/Common/Details'),
          detailsParent,
          self,
          'details']]
        if not util.IsNPC(session.corpid):
            tabs.insert(0, [localization.GetByLabel('UI/Corporations/CorpUIHome/Bulletins'),
             bulletinParent,
             self,
             'bulletin'])
        self.sr.tabs = uicontrols.TabGroup(name='corphometabs', parent=self.mainContainer, idx=0)
        self.sr.tabs.Startup(tabs, 'corphometabs')
        btns = []
        if const.corpRoleChatManager & eve.session.corprole == const.corpRoleChatManager:
            btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/AddBulletin'),
             self.AddBulletin,
             None,
             None])
            uicontrols.ButtonGroup(btns=btns, parent=bulletinParent, line=0, unisize=1)
        if not util.IsNPC(session.corpid):
            self.messageArea = uicontrols.Scroll(parent=bulletinParent, padding=const.defaultPadding)
            self.LoadBulletins()
        btns = []
        if getattr(self, 'canEditCorp', False):
            btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/EditDetails'),
             self.EditDetails,
             None,
             None])
        if sm.GetService('corp').UserIsCEO():
            btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/Dividends'),
             self.PayoutDividendForm,
             None,
             None])
            btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/Divisions'),
             self.DivisionsForm,
             None,
             None])
        else:
            btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/CreateNewCorp'),
             self.CreateCorpForm,
             None,
             None])
            if not util.IsNPC(eve.session.corpid):
                corpSvc = sm.StartService('corp')
                canLeave, error, errorDetails = corpSvc.CanLeaveCurrentCorporation()
                if not canLeave and error == 'CrpCantQuitNotInStasis':
                    btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/PrepareQuitCorporation'),
                     self.RemoveAllRoles,
                     None,
                     None])
                else:
                    btns.append([localization.GetByLabel('UI/Corporations/CorpUIHome/QuitCorp'),
                     self.ResignFromCorp,
                     None,
                     None])
                if corpSvc.UserBlocksRoles():
                    btns.append([localization.GetByLabel('UI/Corporations/Common/AllowCorpRoles'),
                     self.AllowRoles,
                     None,
                     None])
        uicontrols.ButtonGroup(btns=btns, parent=detailsParent, line=0, unisize=1)
        self.sr.scroll = uicontrols.Scroll(name='detailsScroll', parent=detailsParent, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.LoadScroll()

    def LoadBulletins(self):
        scrollEntries = sm.GetService('corp').GetBulletinEntries()
        self.messageArea.LoadContent(contentList=scrollEntries, noContentHint=localization.GetByLabel('UI/Corporations/BaseCorporationUI/NoBulletins'))

    def LoadLogo(self, corporationID):
        if self is None or self.destroyed:
            return
        loc = getattr(self, 'logoContainer', None)
        if loc is not None:
            uix.Flush(loc)
            uiutil.GetLogoIcon(itemID=corporationID, parent=loc, align=uiconst.RELATIVE, name='logo', state=uiconst.UI_NORMAL, left=12, top=3, idx=0, size=48, ignoreSize=True)
        loc = getattr(self, 'captionContainer', None)
        if loc is not None:
            uix.Flush(loc)
            caption = uicontrols.CaptionLabel(text=localization.GetByLabel('UI/Corporations/CorpUIHome/CorpNamePlaceholder', corpName=cfg.eveowners.Get(eve.session.corpid).ownerName), parent=loc, align=uiconst.RELATIVE, uppercase=False)
            caption.left = 0
            infoicon = InfoIcon(typeID=const.typeCorporation, itemID=corporationID, parent=loc, left=caption.width + 4, top=3, state=uiconst.UI_NORMAL)

    def EditDetails(self, *args):
        if not const.corpRoleDirector & eve.session.corprole == const.corpRoleDirector:
            eve.Message('OnlyCEOOrEquivCanEditCorp')
            return
        wnd = form.EditCorpDetails.Open()

    def AddBulletin(self, *args):
        sm.GetService('corp').EditBulletin(None, isAlliance=False)

    def PayoutDividendForm(self, *args):
        if getattr(self, 'openingDividendForm', False):
            return
        self.openingDividendForm = True
        try:
            if not sm.GetService('corp').UserIsCEO():
                eve.Message('OnlyCEOCanPayoutDividends')
                return
            maxAmount = sm.RemoteSvc('account').GetCashBalance(1, 1000)
            if maxAmount < 1:
                eve.Message('CorpHasNoMoneyToPayoutDividends')
                return
            payShareholders = 0
            format = [{'type': 'btline'},
             {'type': 'push',
              'frame': 1},
             {'type': 'text',
              'text': localization.GetByLabel('UI/Corporations/CorpUIHome/HintSelectDividend'),
              'frame': 1},
             {'type': 'push',
              'frame': 1},
             {'type': 'btline'},
             {'type': 'push',
              'frame': 1}]
            payShareholders = 0
            payMembers = 1
            format.append({'type': 'text',
             'text': localization.GetByLabel('UI/Corporations/CorpUIHome/PayDividendTo'),
             'frame': 1})
            format.append({'type': 'checkbox',
             'required': 1,
             'group': 'OdividendType',
             'height': 16,
             'setvalue': 1,
             'key': payShareholders,
             'label': '',
             'text': localization.GetByLabel('UI/Corporations/CorpUIHome/Shareholders'),
             'frame': 1})
            format.append({'type': 'checkbox',
             'required': 1,
             'group': 'OdividendType',
             'height': 16,
             'setvalue': 0,
             'key': payMembers,
             'label': '',
             'text': localization.GetByLabel('UI/Corporations/CorpUIHome/Members'),
             'frame': 1})
            format.append({'type': 'push',
             'frame': 1})
            format.append({'type': 'btline'})
            format.append({'type': 'push',
             'frame': 1})
            format.append({'type': 'text',
             'text': localization.GetByLabel('UI/Corporations/CorpUIHome/EnterTotalAmount'),
             'frame': 1})
            format.append({'type': 'text',
             'text': localization.GetByLabel('UI/Corporations/CorpUIHome/AmountWillBeDivided'),
             'frame': 1})
            format.append({'type': 'edit',
             'key': 'payoutAmount',
             'setvalue': 1,
             'label': localization.GetByLabel('UI/Corporations/CorpUIHome/Amount'),
             'frame': 1,
             'floatonly': [1, maxAmount]})
            format.append({'type': 'push',
             'frame': 1})
            format.append({'type': 'bbline'})
            retval = uix.HybridWnd(format, localization.GetByLabel('UI/Corporations/CorpUIHome/PayDividend'), 1, None, None, None, 340, 256, ignoreCurrent=0)
            if retval is not None:
                payShareholders = [1, 0][retval['OdividendType']]
                payoutAmount = retval['payoutAmount']
                sm.GetService('corp').PayoutDividend(payShareholders, payoutAmount)
        finally:
            self.openingDividendForm = False

    def DivisionsForm(self, *args):
        if not sm.GetService('corp').UserIsCEO():
            eve.Message('CorpAccessOnlyCEOEditDivisionNames')
            return
        divisions = sm.GetService('corp').GetDivisionNames()
        format = [{'type': 'btline'},
         {'type': 'push',
          'frame': 1},
         {'type': 'text',
          'frame': 1,
          'text': localization.GetByLabel('UI/Corporations/CorpUIHome/AssignNames')},
         {'type': 'push',
          'frame': 1}]
        labelWidth = 160
        for i in xrange(1, 8):
            key = 'division%s' % i
            format.append({'type': 'edit',
             'setvalue': divisions[i],
             'label': localization.GetByLabel('UI/Corporations/CorpUIHome/DivisionName', index=i),
             'key': key,
             'frame': 1,
             'labelwidth': labelWidth,
             'maxlength': 50})

        format.append({'type': 'labeltext',
         'label': localization.GetByLabel('UI/Corporations/CorpUIHome/WalletDivisionName', index=1),
         'text': localization.GetByLabel('UI/Corporations/Common/CorporateDivisionMasterWallet'),
         'frame': 1,
         'labelwidth': labelWidth})
        for i in xrange(9, 15):
            key = 'division%s' % i
            format.append({'type': 'edit',
             'setvalue': divisions[i],
             'label': localization.GetByLabel('UI/Corporations/CorpUIHome/WalletDivisionName', index=i - 7),
             'key': key,
             'frame': 1,
             'labelwidth': labelWidth,
             'maxlength': 50})

        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'btline'})
        format.append({'type': 'errorcheck',
         'errorcheck': self.ApplyDivisionNames})
        wnd = uix.HybridWnd(format, localization.GetByLabel('UI/Corporations/CorpUIHome/DivisionNamesCaption'), 0, minW=450, ignoreCurrent=0)
        if wnd:
            wnd.Maximize()

    def ApplyDivisionNames(self, retval):

        def KeyToInt(k):
            return int(k[len('division'):])

        new = dict([ (KeyToInt(k), v) for k, v in retval.iteritems() ])
        current = sm.GetService('corp').GetDivisionNames()
        currentNamesForNewKeys = dict([ (k, current[k]) for k in new.iterkeys() ])
        if new != currentNamesForNewKeys:
            try:
                sm.GetService('corp').UpdateDivisionNames(*[ new.get(k, current[k]) for k in xrange(1, len(current) + 1) ])
            except UserError as e:
                msg = cfg.GetMessage(e.msg, e.dict)
                if msg.type == 'notify' and e.msg.find('CorpDiv') > -1:
                    sys.exc_clear()
                    return msg.text
                raise

        return ''

    def CreateCorpForm(self, *args):
        wnd = form.CreateCorp.GetIfOpen()
        if wnd is not None:
            wnd.Maximize()
        else:
            sm.GetService('sessionMgr').PerformSessionChange('corp.addcorp', self.ShowCreateCorpForm)

    def ShowCreateCorpForm(self, *args):
        if not eve.session.stationid:
            eve.Message('CanOnlyCreateCorpInStation')
            eve.session.ResetSessionChangeTimer('Failed criteria for creating a corporation')
            return
        if sm.GetService('godma').GetType(eve.stationItem.stationTypeID).isPlayerOwnable == 1:
            eve.Message('CanNotCreateCorpAtPlayerOwnedStation')
            eve.session.ResetSessionChangeTimer('Failed criteria for creating a corporation')
            return
        if not sm.GetService('corp').MemberCanCreateCorporation():
            cost = sm.GetService('corp').GetCostForCreatingACorporation()
            eve.Message('PlayerCantCreateCorporation', {'cost': cost})
            eve.session.ResetSessionChangeTimer('Failed criteria for creating a corporation')
            return
        if sm.GetService('corp').UserIsCEO():
            eve.Message('CEOCannotCreateCorporation')
            eve.session.ResetSessionChangeTimer('Failed criteria for creating a corporation')
            return
        form.CreateCorp.Open()

    def LoadScroll(self):
        if self is None or self.destroyed:
            return
        if not self.sr.Get('scroll'):
            return
        try:
            scrolllist = []
            sm.GetService('corpui').ShowLoad()
            self.ShowMyCorporationsDetails(scrolllist)
            self.ShowMyCorporationsOffices(scrolllist)
            self.ShowMyCorporationsStations(scrolllist)
            self.sr.scroll.Load(contentList=scrolllist)
        except:
            log.LogException()
            sys.exc_clear()
        finally:
            sm.GetService('corpui').HideLoad()

    def ShowMyCorporationsDetails(self, scrolllist):
        sm.GetService('corpui').ShowLoad()
        try:
            data = {'GetSubContent': self.GetSubContentDetails,
             'label': localization.GetByLabel('UI/Common/Details'),
             'groupItems': None,
             'id': ('corporation', 'details'),
             'tabs': [],
             'state': 'locked',
             'showicon': 'hide'}
            scrolllist.append(listentry.Get('Group', data))
            uicore.registry.SetListGroupOpenState(('corporation', 'details'), 1)
        finally:
            sm.GetService('corpui').HideLoad()

    def GetSubContentDetails(self, nodedata, *args):
        scrolllist = []
        corpinfo = sm.GetService('corp').GetCorporation()
        founderdone = 0
        if cfg.invtypes.Get(cfg.eveowners.Get(corpinfo.ceoID).typeID).groupID == const.groupCharacter:
            if corpinfo.creatorID == corpinfo.ceoID:
                ceoLabel = 'UI/Corporations/CorpUIHome/CeoAndFounder'
                founderdone = 1
            else:
                ceoLabel = 'UI/Corporations/Common/CEO'
            scrolllist.append(self.GetListEntry(ceoLabel, localization.GetByLabel('UI/Corporations/CorpUIHome/PlayerNamePlaceholder', player=corpinfo.ceoID), typeID=const.typeCharacterAmarr, itemID=corpinfo.ceoID))
        if not founderdone and cfg.invtypes.Get(cfg.eveowners.Get(corpinfo.creatorID).typeID).groupID == const.groupCharacter:
            scrolllist.append(self.GetListEntry('UI/Corporations/Common/Founder', localization.GetByLabel('UI/Corporations/CorpUIHome/PlayerNamePlaceholder', player=corpinfo.creatorID), typeID=const.typeCharacterAmarr, itemID=corpinfo.creatorID))
        if corpinfo.stationID:
            station = sm.GetService('map').GetStation(corpinfo.stationID)
            row = Row(['stationID', 'typeID'], [corpinfo.stationID, station.stationTypeID])
            jumps = sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(station.solarSystemID)
            scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/Headquarters', localization.GetByLabel('UI/Corporations/CorpUIHome/StationAndJumps', station=station.stationID, jumpCount=jumps, jumps=jumps), typeID=station.stationTypeID, itemID=corpinfo.stationID, station=row))
        scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/TickerName', localization.GetByLabel('UI/Corporations/CorpUIHome/TickerNamePlaceholder', ticker=corpinfo.tickerName)))
        scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/Shares', localization.formatters.FormatNumeric(value=corpinfo.shares)))
        if not util.IsNPC(eve.session.corpid):
            scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/MemberCount', localization.formatters.FormatNumeric(value=corpinfo.memberCount)))
        scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/TaxRate', localization.GetByLabel('UI/Corporations/CorpUIHome/TaxRatePlaceholder', tax=corpinfo.taxRate * 100)))
        if corpinfo.url:
            linkTag = '<url=%s>' % corpinfo.url
            scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/URL', localization.GetByLabel('UI/Corporations/CorpUIHome/URLPlaceholder', linkTag=linkTag, url=corpinfo.url)))
        enabledDisabledText = localization.GetByLabel('UI/Corporations/CorpUIHome/Enabled')
        if not corpinfo.isRecruiting:
            enabledDisabledText = localization.GetByLabel('UI/Corporations/CorpUIHome/Disabled')
        scrolllist.append(self.GetListEntry('UI/Corporations/CorpUIHome/MembershipApplication', enabledDisabledText))
        myListEntry = listentry.Get('FriendlyFireEntry', {'line': 1,
         'label': localization.GetByLabel('UI/Corporations/CorpUIHome/FriendlyFire'),
         'text': 'text'})
        scrolllist.append(myListEntry)
        return scrolllist

    def GetListEntry(self, label, text, typeID = None, itemID = None, station = None):
        entry = listentry.Get('LabelTextTop', {'line': 1,
         'label': localization.GetByLabel(label),
         'text': text,
         'typeID': typeID,
         'itemID': itemID,
         'station': station})
        return entry

    def ShowMyCorporationsOffices(self, scrolllist):
        sm.GetService('corpui').ShowLoad()
        try:
            data = {'GetSubContent': self.GetSubContentMyCorporationsOffices,
             'label': localization.GetByLabel('UI/Corporations/Common/Offices'),
             'groupItems': None,
             'id': ('corporation', 'offices'),
             'tabs': [],
             'state': 'locked',
             'showicon': 'hide'}
            scrolllist.append(listentry.Get('Group', data))
            uicore.registry.SetListGroupOpenState(('corporation', 'offices'), 0)
        finally:
            sm.GetService('corpui').HideLoad()

    def OnDataChanged(self, rowset, primaryKey, change, notificationParams):
        log.LogInfo('----------------------------------------------')
        log.LogInfo('OnDataChanged')
        log.LogInfo('primaryKey:', primaryKey)
        log.LogInfo('change:', change)
        log.LogInfo('notificationParams:', notificationParams)
        log.LogInfo('----------------------------------------------')
        if not (self and not self.destroyed):
            return
        if self.sr.Get('offices', None) is not None:
            if rowset == self.sr.offices:
                self.LoadScroll()

    def GetSubContentMyCorporationsOffices(self, nodedata, *args):
        subcontent = []
        if self.sr.Get('offices', None) is None:
            self.sr.offices = sm.GetService('corp').GetMyCorporationsOffices()
            self.sr.offices.Fetch(0, len(self.sr.offices))
            self.sr.offices.AddListener(self)
        if self.sr.offices and len(self.sr.offices):
            for row in self.sr.offices:
                solarSystemID = sm.GetService('ui').GetStation(row.stationID).solarSystemID
                jumps = sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(solarSystemID)
                locationName = cfg.evelocations.Get(row.stationID).locationName
                subcontent.append((locationName.lower(), listentry.Get('CorpOfficeEntry', {'label': localization.GetByLabel('UI/Corporations/CorpUIHome/StationAndJumps', station=row.stationID, jumpCount=jumps, jumps=jumps),
                  'station': row,
                  'GetMenu': self.GetMenuForCorpOffice,
                  'typeID': row.typeID,
                  'itemID': row.stationID})))

        if not len(subcontent):
            subcontent.append(listentry.Get('Generic', {'label': localization.GetByLabel('UI/Corporations/CorpUIHome/CorpHasNoOffices')}))
        else:
            subcontent = uiutil.SortListOfTuples(subcontent)
        return subcontent

    def GetMenuForCorpOffice(self, entry):
        station = entry.sr.node.station
        ret = sm.GetService('menu').CelestialMenu(station.stationID, typeID=station.typeID)
        if session.corprole & const.corpRoleDirector == const.corpRoleDirector:
            ret.append([uiutil.MenuLabel('UI/Station/Hangar/UnrentOffice'), self.UnrentOffice, [station.stationID]])
        return ret

    def UnrentOffice(self, stationID):
        if eve.Message('crpUnrentOffice', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        corpStationMgr = moniker.GetCorpStationManagerEx(stationID)
        corpStationMgr.CancelRentOfOffice()

    def GetMenu(self, entry):
        station = entry.sr.node.station
        return sm.GetService('menu').CelestialMenu(station.stationID, typeID=station.typeID)

    def ShowMyCorporationsStations(self, scrolllist):
        sm.GetService('corpui').ShowLoad()
        try:
            data = {'GetSubContent': self.GetSubContentMyCorporationsStations,
             'label': localization.GetByLabel('UI/Corporations/CorpUIHome/Stations'),
             'groupItems': None,
             'id': ('corporation', 'stations'),
             'tabs': [],
             'state': 'locked',
             'showicon': 'hide'}
            scrolllist.append(listentry.Get('Group', data))
            uicore.registry.SetListGroupOpenState(('corporation', 'stations'), 0)
        finally:
            sm.GetService('corpui').HideLoad()

    def GetSubContentMyCorporationsStations(self, nodedata, *args):
        subcontent = []
        rows = sm.GetService('corp').GetMyCorporationsStations()
        if rows and len(rows):
            for row in rows:
                solarSystemID = sm.GetService('ui').GetStation(row.stationID).solarSystemID
                jumps = sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(solarSystemID)
                subcontent.append(listentry.Get('Generic', {'label': localization.GetByLabel('UI/Corporations/CorpUIHome/StationAndJumps', station=row.stationID, jumpCount=jumps, jumps=jumps),
                 'station': row,
                 'GetMenu': self.GetMenu,
                 'typeID': row.typeID,
                 'itemID': row.stationID}))

        if not len(subcontent):
            subcontent.append(listentry.Get('Generic', {'label': localization.GetByLabel('UI/Corporations/CorpUIHome/CorpHasNoStations')}))
        return subcontent

    def RemoveAllRoles(self, *args):
        corpSvc = sm.StartService('corp')
        canLeave, error, errorDetails = corpSvc.CanLeaveCurrentCorporation()
        if not canLeave:
            if error == 'CrpCantQuitNotInStasis':
                if eve.Message('ConfirmRemoveAllRolesDetailed', errorDetails, uiconst.OKCANCEL) != uiconst.ID_OK:
                    return
                corpSvc.RemoveAllRoles(silent=True)
            else:
                raise UserError(error, errorDetails)

    def ResignFromCorp(self, *args):
        corpSvc = sm.StartService('corp')
        canLeave, error, errorDetails = corpSvc.CanLeaveCurrentCorporation()
        if canLeave:
            corpSvc.KickOut(eve.session.charid)
        else:
            raise UserError(error, errorDetails)

    def AllowRoles(self, *args):
        if eve.Message('ConfirmAllowRoles', {}, uiconst.OKCANCEL) != uiconst.ID_OK:
            return
        sm.StartService('corp').UpdateMember(eve.session.charid, None, None, None, None, None, None, None, None, None, None, None, None, None, 0)
        eve.Message('NotifyRolesAllowed', {})


class FriendlyFireEntry(LabelTextTop):
    __guid__ = 'listentry.FriendlyFireEntry'

    def Startup(self, *args):
        LabelTextTop.Startup(self, args)
        self.statusText = ''
        self.changeAtTime = None
        self.isEnabled = True
        self.SetCorpFFStatus()
        helpIcon = MoreInfoIcon(parent=self, align=uiconst.CENTERRIGHT, hint=localization.GetByLabel('UI/Corporations/FriendlyFire/Description'))
        self.ffButton = Button(name='ffButton', align=uiconst.CENTERRIGHT, parent=self, label='', func=self.OnFFClick, left=20)
        self.UpdateButton()
        canEditCorp = not util.IsNPC(session.corpid) and const.corpRoleDirector & session.corprole == const.corpRoleDirector
        if not canEditCorp:
            self.ffButton.display = False

    def Load(self, node):
        LabelTextTop.Load(self, node)
        self.UpdateStatusText()

    def SetCorpFFStatus(self, myCorpAggressionSettings = None):
        if myCorpAggressionSettings is None:
            myCorpAggressionSettings = sm.GetService('crimewatchSvc').GetCorpAggressionSettings()
        now = blue.os.GetWallclockTime()
        self.isEnabled = myCorpAggressionSettings.IsFriendlyFireLegalAtTime(now)
        self.changeAtTime = myCorpAggressionSettings.GetNextPendingChangeTime(now)
        self.statusText = sm.GetService('corp').GetCorpFriendlyFireStatus(myCorpAggressionSettings)

    def UpdateStatusText(self):
        self.sr.text.SetText(self.statusText)

    def UpdateButton(self):
        if self.isEnabled:
            self.ffButton.SetLabel_(localization.GetByLabel('UI/Corporations/FriendlyFire/SetIllegalBtn'))
        else:
            self.ffButton.SetLabel_(localization.GetByLabel('UI/Corporations/FriendlyFire/SetLegalBtn'))
        if self.changeAtTime:
            self.ffButton.Disable()
        else:
            self.ffButton.Enable()

    def OnFFClick(self, *args):
        if self.isEnabled:
            confirmMsgText = 'ConfirmChangeFriendlyFireToIllegal'
        else:
            confirmMsgText = 'ConfirmChangeFriendlyFireToLegal'
        if eve.Message(confirmMsgText, {}, uiconst.OKCANCEL) != uiconst.ID_OK:
            return
        newAggressionSettings = sm.GetService('corp').GetCorpRegistry().RegisterNewAggressionSettings(not self.isEnabled)
        self.SetCorpFFStatus(newAggressionSettings)
        self.UpdateButton()
        self.UpdateStatusText()


class BulletinEntry(uicontrols.SE_BaseClassCore):
    __guid__ = 'listentry.BulletinEntry'
    default_showHilite = False

    def Startup(self, *args):
        LineThemeColored(parent=self, align=uiconst.TOBOTTOM)
        self.text = uicontrols.EveLabelMedium(parent=self, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, padding=const.defaultPadding, linkStyle=uiconst.LINKSTYLE_REGULAR)
        self.postedBy = uicontrols.EveLabelMedium(parent=self, align=uiconst.BOTTOMRIGHT, state=uiconst.UI_NORMAL, maxLines=1, top=const.defaultPadding, left=const.defaultPadding)

    def Load(self, node):
        self.text.text = node.text
        self.postedBy.text = node.postedBy

    def GetDynamicHeight(node, width):
        textWidth, textHeight = uicontrols.EveLabelMedium.MeasureTextSize(text=node.text, width=width - const.defaultPadding * 2)
        height = textHeight + const.defaultPadding * 2
        postedWidth, postedHeight = uicontrols.EveLabelMedium.MeasureTextSize(text=node.postedBy, maxLines=1)
        height += postedHeight + const.defaultPadding
        return height


class EditCorpBulletin(uicontrols.Window):
    __guid__ = 'form.EditCorpBulletin'
    default_windowID = 'EditCorpBulletin'
    default_iconNum = 'res:/ui/Texture/WindowIcons/corporation.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        isAlliance = attributes.isAlliance
        bulletin = attributes.bulletin
        self.scope = 'all'
        self.bulletin = bulletin
        self.bulletinID = None
        self.editDateTime = None
        self.isAlliance = isAlliance
        self.SetMinSize([420, 300])
        self.SetWndIcon(self.iconNum, mainTop=-10)
        self.SetCaption(localization.GetByLabel('UI/Corporations/EditCorpBulletin/EditBulletinCaption'))
        self.SetTopparentHeight(45)
        main = uiutil.FindChild(self, 'main')
        main.left = main.top = main.width = main.height = const.defaultPadding
        uiprimitives.Container(parent=self.sr.topParent, width=4, align=uiconst.TORIGHT, name='push')
        uiprimitives.Container(parent=self.sr.topParent, width=120, align=uiconst.TOLEFT, name='push')
        titleInput = uicontrols.SinglelineEdit(name='titleInput', parent=self.sr.topParent, align=uiconst.TOBOTTOM, maxLength=100)
        titleInput.OnDropData = self.OnDropData
        self.sr.titleInput = titleInput
        l = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Corporations/EditCorpBulletin/BulletinTitle'), parent=titleInput, width=64, height=12, left=48, top=4, state=uiconst.UI_DISABLED)
        l.left = -l.textwidth - 6
        uiprimitives.Container(parent=main, height=const.defaultPadding, align=uiconst.TOTOP, name='push')
        self.sr.messageEdit = uicls.EditPlainText(setvalue='', parent=main, maxLength=2000, showattributepanel=1)
        self.sr.bottom = uiprimitives.Container(name='bottom', parent=self.sr.maincontainer, align=uiconst.TOBOTTOM, height=24, idx=0)
        uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Common/Buttons/Submit'),
          self.ClickSend,
          None,
          None], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.OnCancel,
          None,
          None]], parent=self.sr.bottom, line=False)
        if bulletin is not None:
            self.sr.titleInput.SetValue(bulletin.title)
            self.sr.messageEdit.SetValue(bulletin.body)
            self.bulletinID = bulletin.bulletinID
            self.editDateTime = bulletin.editDateTime

    def OnCancel(self, *args):
        self.Close()

    def _OnClose(self, *args):
        self.messageEdit = None

    def IsAlliance(self):
        return self.isAlliance

    def ClickSend(self, *args):
        if getattr(self, 'sending', False):
            return
        self.sending = True
        title = self.sr.titleInput.GetValue()
        body = self.sr.messageEdit.GetValue(html=0).strip()
        if title == '' or body == '':
            self.sending = False
            raise UserError('CorpBulletinMustFillIn')
        if self.bulletinID is None:
            sm.GetService('corp').AddBulletin(title, body, self.isAlliance)
        else:
            sm.GetService('corp').UpdateBulletin(self.bulletinID, title, body, self.isAlliance, self.editDateTime)
        if not self or self.destroyed:
            return
        self.Close()
