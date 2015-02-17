#Embedded file name: eve/client/script/ui/station/insurance\base_insurance.py
from carbonui.control.dragResizeCont import DragResizeCont
from carbonui.primitives.container import Container
from carbonui.primitives.line import Line
from eve.client.script.ui.control.eveLabel import WndCaptionLabel, EveLabelLargeBold
from eve.client.script.ui.control.eveScroll import Scroll
import uicontrols
import blue
import listentry
import service
import uiutil
import uthread
import util
import carbonui.const as uiconst
import localization
from eve.common.script.sys.rowset import Rowset

class InsuranceSvc(service.Service):
    __exportedcalls__ = {'CleanUp': [],
     'Reset': [],
     'GetContracts': []}
    __guid__ = 'svc.insurance'
    __notifyevents__ = []
    __servicename__ = 'insurance'
    __displayname__ = 'Insurance Service'
    __dependencies__ = ['corp', 'station']

    def __init__(self):
        service.Service.__init__(self)
        self.scroll = None
        self.insurance = None
        self.contracts = {}
        self.stuff = {}
        self.insurancePrice = {}

    def Run(self, memStream = None):
        self.LogInfo('Insurance Service Started')
        self.wnd = None
        self.CleanUp()

    def Stop(self, memStream = None):
        self.LogInfo('Insurance Medical Service')
        self.CleanUp()
        service.Service.Stop(self)

    def CleanUp(self):
        self.insurance = None
        self.contracts = {}
        self.stuff = {}
        self.insuranceNames = {}

    def Reset(self):
        pass

    def GetInsuranceMgr(self):
        if self.insurance is not None:
            return self.insurance
        self.insurance = util.Moniker('insuranceSvc', session.stationid2)
        self.insurance.SetSessionCheck({'stationid2': session.stationid2})
        return self.insurance

    def GetContracts(self):
        self.contracts = {}
        if session.stationid2:
            contracts = self.GetInsuranceMgr().GetContracts()
        else:
            contracts = sm.RemoteSvc('insuranceSvc').GetContracts()
        for contract in contracts:
            self.contracts[contract.shipID] = contract

        if eve.session.corprole & (const.corpRoleJuniorAccountant | const.corpRoleAccountant) != 0:
            contracts = self.GetInsuranceMgr().GetContracts(1)
            for contract in contracts:
                self.contracts[contract.shipID] = contract

        return self.contracts

    def GetInsurancePrice(self, typeID):
        if typeID in self.insurancePrice:
            return self.insurancePrice[typeID]
        if session.stationid2:
            self.insurancePrice[typeID] = self.GetInsuranceMgr().GetInsurancePrice(typeID)
        else:
            self.insurancePrice[typeID] = sm.RemoteSvc('insuranceSvc').GetInsurancePrice(typeID)
        return self.insurancePrice[typeID]

    def GetItems(self):
        self.stuff = {}
        items = sm.GetService('invCache').GetInventory(const.containerHangar)
        items = items.List()
        for item in items:
            if item.categoryID != const.categoryShip:
                continue
            if not item.singleton:
                continue
            if self.GetInsurancePrice(item.typeID) <= 0:
                continue
            self.stuff[item.itemID] = item

        if eve.session.corprole & (const.corpRoleAccountant | const.corpRoleJuniorAccountant) != 0:
            office = self.corp.GetOffice()
            if office is not None:
                items = sm.GetService('invCache').GetInventoryFromId(office.itemID, locationID=session.stationid2)
                items = items.List()
                for item in items:
                    if item.categoryID != const.categoryShip:
                        continue
                    if not item.singleton:
                        continue
                    if self.GetInsurancePrice(item.typeID) <= 0:
                        continue
                    self.stuff[item.itemID] = item

        return self.stuff

    def GetQuoteForShip(self, ship):
        if ship is None:
            raise UserError('InsCouldNotFindItem')
        insurancePrice = self.GetInsurancePrice(ship.typeID)
        fivePC = float(insurancePrice) * 0.05
        cost = fivePC
        fraction = 0.5
        quotes = Rowset(['fraction', 'amount'])
        while fraction <= 1.0:
            quotes.lines.append([fraction, cost])
            fraction += 0.1
            cost += fivePC

        return quotes

    def GetInsuranceName(self, fraction):
        if not self.insuranceNames:
            self.insuranceNames = {'0.5': localization.GetByLabel('UI/Insurance/QuoteWindow/Basic'),
             '0.6': localization.GetByLabel('UI/Insurance/QuoteWindow/Standard'),
             '0.7': localization.GetByLabel('UI/Insurance/QuoteWindow/Bronze'),
             '0.8': localization.GetByLabel('UI/Insurance/QuoteWindow/Silver'),
             '0.9': localization.GetByLabel('UI/Insurance/QuoteWindow/Gold'),
             '1.0': localization.GetByLabel('UI/Insurance/QuoteWindow/Platinum')}
        fraction = '%.1f' % fraction
        return self.insuranceNames.get(fraction, fraction)

    def Insure(self, item):
        if item.ownerID == session.corpid:
            isCorpItem = True
        else:
            isCorpItem = False
        wnd = InsuranceTermsWindow.GetIfOpen()
        if wnd:
            if wnd.itemID == item.itemID and not wnd.destroyed:
                wnd.Maximize()
                return
            wnd.Close()
        if isCorpItem:
            msg = 'InsAskAcceptTermsCorp'
        else:
            msg = 'InsAskAcceptTerms'
        if eve.Message(msg, {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        InsuranceTermsWindow.Open(item=item, isCorpItem=isCorpItem)


class InsuranceWindow(uicontrols.Window):
    __guid__ = 'form.InsuranceWindow'
    default_width = 400
    default_height = 300
    default_windowID = 'insurance'
    default_captionLabelPath = 'Tooltips/StationServices/Insurance'
    default_descriptionLabelPath = 'Tooltips/StationServices/Insurance_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/insurance.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.contracts = {}
        self.stuff = {}
        self.corpShipsScroll = None
        self.SetWndIcon(self.iconNum, mainTop=-8)
        self.SetMinSize([350, 270])
        WndCaptionLabel(text=localization.GetByLabel('UI/Insurance/InsuranceWindow/Title'), parent=self.sr.topParent, align=uiconst.RELATIVE)
        self.scope = 'station'
        btns = uicontrols.ButtonGroup(btns=[(localization.GetByLabel('UI/Insurance/InsuranceWindow/Commands/Insure'),
          self.InsureFromBtn,
          None,
          81)])
        self.sr.main.children.append(btns)
        self.sr.insureBtns = btns
        self.headers = [localization.GetByLabel('UI/Common/Type'),
         localization.GetByLabel('UI/Common/DateWords/FromDate'),
         localization.GetByLabel('UI/Common/DateWords/ToDate'),
         localization.GetByLabel('UI/Insurance/InsuranceWindow/Level'),
         localization.GetByLabel('UI/Insurance/InsuranceWindow/Name')]
        if self.CheckCorpRoles():
            self.DrawSplitList()
        else:
            self.DrawMyShipsScroll(parentCont=self.sr.main)
        self.ShowInsuranceInfo()

    def DrawSplitList(self):
        myShipsCont = DragResizeCont(name='myShipsCont', parent=self.sr.main, align=uiconst.TOTOP_PROP, minSize=0.3, maxSize=0.7, defaultSize=0.45, padding=4)
        EveLabelLargeBold(parent=myShipsCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Insurance/InsuranceWindow/MyShips'), padTop=2, padLeft=2)
        self.DrawMyShipsScroll(parentCont=myShipsCont)
        corpShipsCont = Container(parent=self.sr.main, name='corpShipsCont', align=uiconst.TOALL, padLeft=4, padRight=4)
        EveLabelLargeBold(parent=corpShipsCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Insurance/InsuranceWindow/CorpShips'), padTop=2, padLeft=2)
        self.corpShipsScroll = Scroll(parent=corpShipsCont, padding=const.defaultPadding)
        self.corpShipsScroll.sr.id = 'corpinsurance'
        self.corpShipsScroll.multiSelect = 0
        self.corpShipsScroll.sr.minColumnWidth = {localization.GetByLabel('UI/Common/Type'): 30}

    def DrawMyShipsScroll(self, parentCont):
        self.myShipsScroll = Scroll(parent=parentCont, padding=(4, 4, 4, 0))
        self.myShipsScroll.sr.id = 'insurance'
        self.myShipsScroll.multiSelect = 0
        self.myShipsScroll.sr.minColumnWidth = {localization.GetByLabel('UI/Common/Type'): 30}

    def SetHint(self, hintstr = None, isCorp = False):
        if not isCorp:
            if self.myShipsScroll:
                self.myShipsScroll.ShowHint(hintstr)
        elif self.corpShipsScroll:
            self.corpShipsScroll.ShowHint(hintstr)

    def GetItemMenu(self, entry):
        item = entry.sr.node.info
        contract = self.contracts.get(item.itemID, None)
        m = []
        if contract and contract.ownerID == session.charid:
            m = [(uiutil.MenuLabel('UI/Insurance/InsuranceWindow/Commands/CancelInsurance'), self.UnInsure, (item,))]
            m.append(None)
        m += sm.GetService('menu').InvItemMenu(item, 1)
        return m

    def ShowInsuranceInfo(self):
        uthread.pool('Insurance :: ShowInsuranceInfo', self._ShowInsuranceInfo)

    def CheckCorpRoles(self):
        if eve.session.corprole & (const.corpRoleJuniorAccountant | const.corpRoleAccountant) != 0:
            return True
        return False

    def _ShowInsuranceInfo(self):
        insurance = sm.GetService('insurance')
        self.contracts = insurance.GetContracts()
        self.stuff = insurance.GetItems()
        corpShipsList = []
        myShipsList = self.GetMyShips()
        self.myShipsScroll.Load(contentList=myShipsList, headers=self.headers)
        if not len(myShipsList):
            self.SetHint(localization.GetByLabel('UI/Insurance/InsuranceWindow/NothingToInsure'))
        if self.CheckCorpRoles():
            corpShipsList = self.GetCorpShips()
            self.corpShipsScroll.Load(contentList=corpShipsList, headers=self.headers)
            if not len(corpShipsList):
                self.SetHint(localization.GetByLabel('UI/Insurance/InsuranceWindow/NothingToInsure'), isCorp=True)

    def GetMyShips(self):
        ownerID = session.charid
        self.PrimeItems(ownerID)
        return self.CreateScrolllist(ownerID)

    def GetCorpShips(self):
        ownerID = session.corpid
        self.PrimeItems(ownerID)
        return self.CreateScrolllist(ownerID)

    def PrimeItems(self, ownerID):
        itemList = []
        for itemID in self.stuff:
            item = self.stuff[itemID]
            if item.ownerID != ownerID:
                continue
            if item.categoryID == const.categoryShip:
                itemList.append(item.itemID)

        cfg.evelocations.Prime(itemList)

    def CreateScrolllist(self, ownerID):
        scrolllist = []
        for itemID in self.stuff:
            item = self.stuff[itemID]
            if item.ownerID != ownerID:
                continue
            itemName = ''
            if item.categoryID == const.categoryShip:
                shipName = cfg.evelocations.GetIfExists(item.itemID)
                if shipName is not None:
                    itemName = shipName.locationName
            contract = None
            if self.contracts.has_key(item.itemID):
                contract = self.contracts[item.itemID]
            name = cfg.invtypes.Get(item.typeID).name
            if contract is None:
                label = '%s<t>%s<t>%s<t>%s<t>%s' % (name,
                 '-',
                 '-',
                 '-',
                 itemName)
            else:
                label = '%s<t>%s<t>%s<t>%s<t>%s' % (name,
                 util.FmtDate(contract.startDate, 'ls'),
                 util.FmtDate(contract.endDate, 'ls'),
                 sm.GetService('insurance').GetInsuranceName(contract.fraction),
                 itemName)
            if ownerID == session.charid:
                onDblClickFunc = self.OnEntryDblClick
                onClickFunc = self.OnEntryClick
            else:
                onDblClickFunc = self.OnCorpEntryDblClick
                onClickFunc = self.OnCorpEntryClick
            data = {'info': item,
             'itemID': item.itemID,
             'typeID': item.typeID,
             'label': label,
             'getIcon': 1,
             'GetMenu': self.GetItemMenu,
             'OnDblClick': onDblClickFunc,
             'selected': True,
             'OnClick': onClickFunc}
            entry = listentry.Get('Item', data)
            scrolllist.append(entry)

        return scrolllist

    def OnEntryClick(self, entry):
        if self.corpShipsScroll:
            self.corpShipsScroll.DeselectAll()

    def OnCorpEntryClick(self, entry):
        self.myShipsScroll.DeselectAll()

    def OnEntryDblClick(self, entry):
        self.Insure(None)

    def OnCorpEntryDblClick(self, entry):
        self.Insure(None)

    def UnInsure(self, item, *args):
        if item is None or not len(item):
            return
        if eve.Message('InsAskUnInsure', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        sm.GetService('insurance').GetInsuranceMgr().UnInsureShip(item.itemID)
        self.ShowInsuranceInfo()

    def GetSelected(self):
        corpSelected = None
        if self.corpShipsScroll:
            corpSelected = self.corpShipsScroll.GetSelected()
        mySelected = self.myShipsScroll.GetSelected()
        if mySelected:
            return [ node.info for node in mySelected ]
        if corpSelected:
            return [ node.info for node in corpSelected ]

    def InsureFromBtn(self, *args):
        self.Insure(None)

    def Insure(self, item, *args):
        if item is None or not len(item):
            item = self.GetSelected()
            if not item:
                eve.Message('SelectShipToInsure')
                return
            item = item[0]
        return sm.GetService('insurance').Insure(item)


class InsuranceTermsWindow(uicontrols.Window):
    """
        Window where you select the insurance plan for your ship
    """
    default_width = 400
    default_height = 300
    default_minSize = (default_width, default_height)
    default_windowID = 'InsuranceTermsWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.MakeUnResizeable()
        item = attributes.item
        isCorpItem = attributes.isCorpItem
        self.itemID = item.itemID
        self.insuranceSvc = sm.GetService('insurance')
        self.width = 500
        self.SetCaption(localization.GetByLabel('UI/Insurance/QuoteWindow/Title'))
        btnGroup = uicontrols.ButtonGroup(btns=[], parent=self.sr.main, idx=0)
        btnGroup.AddButton(label=localization.GetByLabel('UI/Insurance/InsuranceWindow/Commands/Insure'), func=self.Accept, args=(item.itemID, isCorpItem), isDefault=True)
        btnGroup.AddButton(label=localization.GetByLabel('UI/Common/Buttons/Cancel'), func=self.Cancel, isDefault=False)
        iconsSize = 64
        self.SetTopparentHeight(iconsSize + 4)
        typeIcon = uicontrols.Icon(parent=self.sr.topParent, pos=(4,
         2,
         iconsSize,
         iconsSize), align=uiconst.TOPLEFT, idx=0)
        typeIcon.LoadIconByTypeID(typeID=item.typeID, size=iconsSize, ignoreSize=True)
        typeIcon.GetMenu = lambda *args: sm.GetService('menu').GetMenuFormItemIDTypeID(item.itemID, item.typeID, invItem=item, ignoreMarketDetails=False)
        shipTextList = [cfg.invtypes.Get(item.typeID).name]
        shipInfo = cfg.evelocations.GetIfExists(item.itemID)
        if shipInfo:
            shipTextList.append(shipInfo.locationName)
        contracts = self.insuranceSvc.GetContracts()
        shipContract = contracts.get(item.itemID)
        if shipContract:
            if shipContract.ownerID in (session.corpid, session.charid):
                insuranceName = self.insuranceSvc.GetInsuranceName(shipContract.fraction)
                timeDiff = shipContract.endDate - blue.os.GetWallclockTime()
                timeLeft = localization.GetByLabel('UI/Insurance/TimeLeft', time=timeDiff)
                currentLevelText = localization.GetByLabel('UI/Insurance/QuoteWindow/CurrentLevel', insuranceLevel=insuranceName, timeLeft=timeLeft)
                shipTextList.append(currentLevelText)
        shipText = '<br>'.join(shipTextList)
        typeNameLabel = uicontrols.EveLabelMedium(parent=self.sr.topParent, name='nameLabel', align=uiconst.TOPLEFT, text=shipText, pos=(iconsSize + 10,
         6,
         0,
         0))
        maxElementWidth = typeNameLabel.textwidth + typeNameLabel.left + 20
        cont = uicontrols.ContainerAutoSize(parent=self.sr.main, name='parentContainer', align=uiconst.TOTOP, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding), alignMode=uiconst.TOTOP)
        text = localization.GetByLabel('UI/Insurance/QuoteWindow/SelectInsuranceLevel')
        selectLabel = uicontrols.EveLabelMedium(parent=cont, name='nameLabel', align=uiconst.TOTOP, text=text, padLeft=0, padTop=10)
        insurancePrice = self.insuranceSvc.GetInsurancePrice(item.typeID)
        quotes = self.insuranceSvc.GetQuoteForShip(item)
        self.quotesCbs = []
        for quote in quotes:
            text = localization.GetByLabel('UI/Insurance/QuoteWindow/Line', name=self.insuranceSvc.GetInsuranceName(quote.fraction), cost=localization.GetByLabel('UI/Common/Cost'), amount=util.FmtISK(quote.amount), payout=localization.GetByLabel('UI/Insurance/QuoteWindow/EstimatedPayout'), price=util.FmtISK(quote.fraction * insurancePrice))
            cb = uicontrols.Checkbox(text=text, parent=cont, retval=str(quote.fraction), checked=quote.fraction == 0.5, padLeft=8, padTop=2, align=uiconst.TOTOP, groupname='quotes')
            cb.quote = quote
            self.quotesCbs.append(cb)
            maxElementWidth = max(maxElementWidth, cb.padLeft + cb.sr.label.textwidth + cb.sr.label.padLeft + 20)

        cw, ch = cont.GetAbsoluteSize()
        self.height = ch + self.sr.topParent.height + 50
        self.width = maxElementWidth
        self.SetMinSize([self.width, self.height])

    def Accept(self, itemID, isCorpItem):
        quote = None
        for cb in self.quotesCbs:
            if cb.checked:
                quote = cb.quote
                break

        if quote is None:
            raise RuntimeError('No insurance option chosen')
        insuringText = localization.GetByLabel('UI/Insurance/ProgressWindow/Insuring')
        sm.GetService('loading').ProgressWnd(insuringText, '', 0, 1)
        try:
            self.insuranceSvc.GetInsuranceMgr().InsureShip(itemID, quote.amount, isCorpItem)
            sm.GetService('loading').ProgressWnd(insuringText, '', 1, 1)
        except UserError as e:
            if e.msg == 'InsureShipFailedSingleContract':
                ownerName = e.args[1]['ownerName']
                if eve.Message('InsureShipAlreadyInsured', {'ownerName': ownerName}, uiconst.YESNO) == uiconst.ID_YES:
                    self.insuranceSvc.GetInsuranceMgr().InsureShip(itemID, quote.amount, isCorpItem, voidOld=True)
                    self.TryUpdateInsuranceWindow()
                    sm.GetService('loading').ProgressWnd(insuringText, '', 1, 1)
                    return
                else:
                    cancelledText = localization.GetByLabel('UI/Insurance/QuoteWindow/InsuringCancelled')
                    sm.GetService('loading').ProgressWnd(insuringText, cancelledText, 1, 1)
                    return
            failedText = localization.GetByLabel('UI/Insurance/QuoteWindow/InsuringFailed')
            sm.GetService('loading').ProgressWnd(insuringText, failedText, 1, 1)
            if e.msg == 'InsureShipFailed':
                self.TryUpdateInsuranceWindow()
            self.Close()
            raise

        self.Close()
        self.TryUpdateInsuranceWindow()
        sm.GetService('loading').ProgressWnd(insuringText, '', 1, 1)

    def Cancel(self, btn):
        self.Close()

    def TryUpdateInsuranceWindow(self):
        wnd = InsuranceWindow.GetIfOpen()
        if not wnd or wnd.destroyed:
            return
        wnd.ShowInsuranceInfo()
