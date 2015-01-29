#Embedded file name: eve/client/script/ui/shared/market\sellMulti.py
import math
from carbon.common.script.util.format import FmtAmt
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import EveLabelMedium, EveLabelMediumBold, EveLabelLargeBold, EveLabelSmall, EveCaptionSmall, Label
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.eveWindow import Window
import carbonui.const as uiconst
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.services.menuSvcExtras.invItemFunctions import CheckIfInHangarOrCorpHangarAndCanTake
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.util.contractutils import TypeName
from eve.common.script.sys.eveCfg import GetActiveShip, IsStation
from eve.common.script.util.eveFormat import FmtISK
from localization import GetByLabel
import uthread
from utillib import KeyVal
COL_GREEN = (0.3, 0.9, 0.1)
COL_RED = (9.0, 0.3, 0.1)
COL_WHITE = (1.0,
 1.0,
 1.0,
 0.7)

class SellItems(Window):
    __guid__ = 'form.SellItems'
    __notifyevents__ = ['OnSessionChanged']
    default_width = 520
    default_height = 280
    default_minSize = (default_width, default_height)
    default_windowID = 'SellItemsWindow'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.SetCaption(GetByLabel('UI/Inventory/ItemActions/MultiSell'))
        self.scope = 'station_inflight'
        self.SetTopparentHeight(0)
        mainCont = Container(parent=self.sr.main, name='mainCont', padding=4)
        infoCont = Container(parent=mainCont, name='bottomCont', align=uiconst.TOBOTTOM, height=88, padTop=4)
        Line(parent=infoCont, align=uiconst.TOTOP)
        self.bottomLeft = Container(parent=infoCont, name='bottomLeft', padLeft=6, padTop=6)
        self.bottomRight = Container(parent=infoCont, name='bottomRight', align=uiconst.TORIGHT, width=250, padRight=6, padTop=6)
        dropCont = Container(parent=mainCont, name='dropCont', align=uiconst.TOTOP, height=28, state=uiconst.UI_NORMAL, padBottom=4)
        dropCont.OnDropData = self.DropItems
        self.dropLabel = EveCaptionSmall(text=GetByLabel('UI/Market/Marketbase/DropItemsToAdd'), parent=dropCont, align=uiconst.CENTER)
        self.dropLabel.opacity = 0.6
        self.fakeItemsCont = Container(parent=dropCont, align=uiconst.TOALL, clipChildren=True)
        self.itemList = []
        self.preItems = attributes.preItems
        self.itemDict = {}
        self.sellItemList = []
        self.cannotSellItemList = []
        self.itemsNeedRepackaging = []
        self.itemAlreadyInList = []
        self.hasDrawn = False
        self.baseStationID = None
        self.useCorp = None
        self.addItemsThread = None
        scrollCont = Container(parent=mainCont, name='scrollCont')
        self.itemsScroll = ScrollContainer(parent=scrollCont, id='MultiSellScroll')
        self.DefineButtons(uiconst.OKCANCEL, okLabel=GetByLabel('UI/Market/MarketQuote/CommandSell'), okFunc=self.SellItems, cancelFunc=self.Cancel)
        self.DrawNumbers()
        self.DrawCombos()
        durationValue = settings.user.ui.Get('multiSellDuration', 0)
        self.durationCombo.SetValue(durationValue)
        top = 30
        corpAcctName = self._CanSellForCorp()
        if corpAcctName is not None:
            self.DrawCheckBox(corpAcctName)
            top += 18
        self.orderCountLabel = EveLabelSmall(parent=self.bottomLeft, top=top, left=2)
        self.maxCount, self.myOrderCount = self.GetOrderCount()
        if len(self.preItems):
            self.addItemsThread = uthread.new(self.AddPreItems, self.preItems)
        self.UpdateOrderCount()
        self.globalDragHover = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEHOVER, self.OnGlobalMouseHover)

    def _CanSellForCorp(self):
        if session.corprole & (const.corpRoleAccountant | const.corpRoleTrader):
            corpAcctName = sm.GetService('corp').GetMyCorpAccountName()
            if corpAcctName is not None:
                return corpAcctName

    def GetOrderCount(self):
        limits = sm.GetService('marketQuote').GetSkillLimits()
        maxCount = limits['cnt']
        myOrders = sm.GetService('marketQuote').GetMyOrders()
        return (maxCount, len(myOrders))

    def DrawCheckBox(self, corpAcctName):
        useCorpWallet = settings.user.ui.Get('sellUseCorp', False)
        self.useCorp = Checkbox(text=GetByLabel('UI/Market/MarketQuote/UseCorpAccount', accountName=corpAcctName), parent=self.bottomLeft, configName='usecorp', checked=useCorpWallet, callback=self.OnUseCorp, top=28)

    def OnUseCorp(self, *args):
        if self.useCorp.checked:
            settings.user.ui.Set('sellUseCorp', True)
        else:
            settings.user.ui.Set('sellUseCorp', False)
        self.UpdateOrderCount()

    def UpdateOrderCount(self):
        self.orderCountLabel.text = GetByLabel('UI/Market/MarketQuote/OpenOrdersRemaining', orders=FmtAmt(self.maxCount - self.myOrderCount), maxOrders=FmtAmt(self.maxCount))

    def GetItems(self):
        return self.itemList

    def AddPreItems(self, preItems):
        if not self.CheckItemLocation(preItems[0][0]):
            return
        items = self.CheckOrderAvailability(preItems)
        self.ClearErrorLists()
        for item in items:
            self.AddItem(item[0])

        self.DisplayErrorHints()

    def CheckItemLocation(self, item):
        if not self.CheckStation(item) and len(self.itemList) > 0:
            eve.Message('CustomNotify', {'notify': GetByLabel('UI/Market/MarketQuote/LocationNotShared')})
            return False
        return True

    def CheckOrderAvailability(self, preItems):
        availableOrders = int(sm.GetService('machoNet').GetGlobalConfig().get('MultiSellOrderCap', 100)) - len(self.itemList)
        if len(preItems) > availableOrders:
            eve.Message('CustomNotify', {'notify': GetByLabel('UI/Market/MarketQuote/TooManyItemsForOrder')})
            return preItems[:availableOrders]
        return preItems

    def DisplayErrorHints(self):
        hintText = ''
        if len(self.itemAlreadyInList):
            hintText = '<b>%s</b><br>' % GetByLabel('UI/Market/MarketQuote/AlreadyInList')
            for item in self.itemAlreadyInList:
                hintText += TypeName(item.typeID) + '<br>'

        if len(self.cannotSellItemList):
            if hintText:
                hintText += '<br>'
            hintText += '<b>%s</b><br>' % GetByLabel('UI/Market/MarketQuote/CannotBeSold')
            for item in self.cannotSellItemList:
                hintText += TypeName(item.typeID) + '<br>'

        if len(self.itemsNeedRepackaging):
            if hintText:
                hintText += '<br>'
            hintText += '<b>%s</b><br>' % GetByLabel('UI/Market/MarketQuote/NeedsRepackaging')
            for item in self.itemsNeedRepackaging:
                hintText += TypeName(item.typeID) + '<br>'

        if hintText:
            eve.Message('CustomNotify', {'notify': hintText})

    def AddItem(self, item):
        if not self.IsSellable(item):
            return
        self.itemDict[item.itemID] = item
        itemEntry = SellItemContainer(item=item, editFunc=self.OnEntryEdit, align=uiconst.TOTOP, parentFunc=self.RemoveItem)
        itemEntry.state = uiconst.UI_NORMAL
        self.itemsScroll._InsertChild(0, itemEntry)
        self.itemList.append(itemEntry)
        self.UpdateNumbers()
        if len(self.itemList) == 1:
            self.UpdateStationInfo(itemEntry.stationID)
        self.CheckItemSize()
        self.UpdateHeaderCount()
        uicore.registry.SetFocus(itemEntry.priceEdit)

    def CheckItemSize(self):
        if not len(self.itemList):
            return
        firstItem = self.itemList[0]
        if len(self.itemList) == 1:
            firstItem.MakeSingle()
        elif len(self.itemList) == 2:
            firstItem.RemoveSingle()

    def UpdateStationInfo(self, stationID):
        self.baseStationID = stationID
        if self.baseStationID:
            self.UpdateHeaderCount()
        else:
            self.SetCaption(GetByLabel('UI/Inventory/ItemActions/MultiSell'))

    def UpdateHeaderCount(self):
        self.SetCaption('%s (%i) - %s' % (GetByLabel('UI/Inventory/ItemActions/MultiSell'), len(self.itemList), self.GetStationLocationText()))

    def RemoveItem(self, itemEntry):
        self.itemsScroll._RemoveChild(itemEntry)
        self.itemList.remove(itemEntry)
        self.itemDict.pop(itemEntry.itemID)
        self.CheckItemSize()
        self.UpdateNumbers()
        if len(self.itemList) == 0:
            self.baseStationID = None
            self.UpdateStationInfo(None)

    def CheckStation(self, item):
        itemStationID, _, _ = sm.GetService('invCache').GetStationIDOfficeFolderIDOfficeIDOfItem(item)
        if itemStationID != self.baseStationID:
            return False
        return True

    def ClearErrorLists(self):
        self.cannotSellItemList = []
        self.itemsNeedRepackaging = []
        self.itemAlreadyInList = []

    def IsSellable(self, item):
        sellable = True
        if item.itemID in self.itemDict.keys():
            self.itemAlreadyInList.append(item)
            sellable = False
        elif item.singleton:
            self.itemsNeedRepackaging.append(item)
            sellable = False
        elif IsStation(item.itemID):
            self.cannotSellItemList.append(item)
            sellable = False
        elif cfg.invtypes.Get(item.typeID).marketGroupID is None:
            self.cannotSellItemList.append(item)
            sellable = False
        elif item.ownerID not in [session.corpid, session.charid]:
            self.cannotSellItemList.append(item)
            sellable = False
        elif item.itemID == GetActiveShip():
            self.cannotSellItemList.append(item)
            sellable = False
        elif bool(item.singleton) and item.categoryID == const.categoryBlueprint:
            self.cannotSellItemList.append(item)
            sellable = False
        elif not CheckIfInHangarOrCorpHangarAndCanTake(item):
            self.cannotSellItemList.append(item)
            sellable = False
        return sellable

    def OnEntryEdit(self, *args):
        uthread.new(self.UpdateNumbers)

    def DropItems(self, dragObj, nodes):
        if not self.CheckItemLocation(nodes[0].item):
            return
        items = self.CheckOrderAvailability(nodes)
        self.ClearErrorLists()
        for node in items:
            if getattr(node, '__guid__', None) == 'xtriui.InvItem':
                self.AddItem(node.item)

        self.DisplayErrorHints()

    def Cancel(self, *args):
        self.Close()

    def Close(self, setClosed = False, *args, **kwds):
        Window.Close(self, *args, **kwds)
        if self.addItemsThread:
            self.addItemsThread.kill()
        uicore.event.UnregisterForTriuiEvents(self.globalDragHover)

    def DrawCombos(self):
        durations = [[GetByLabel('UI/Market/MarketQuote/Immediate'), 0],
         [GetByLabel('UI/Common/DateWords/Day'), 1],
         [GetByLabel('UI/Market/MarketQuote/ThreeDays'), 3],
         [GetByLabel('UI/Common/DateWords/Week'), 7],
         [GetByLabel('UI/Market/MarketQuote/TwoWeeks'), 14],
         [GetByLabel('UI/Common/DateWords/Month'), 30],
         [GetByLabel('UI/Market/MarketQuote/ThreeMonths'), 90]]
        self.durationCombo = Combo(parent=self.bottomLeft, options=durations, top=6, callback=self.OnDurationChange)

    def OnDurationChange(self, *args):
        settings.user.ui.Set('multiSellDuration', self.durationCombo.GetValue())
        self.UpdateNumbers()
        for item in self.GetItems():
            if self.durationCombo.GetValue() == 0:
                item.ShowNoSellOrders()
            else:
                item.HideNoSellOrders()

    def DrawNumbers(self):
        self.numbersGrid = LayoutGrid(parent=self.bottomRight, columns=2, align=uiconst.TORIGHT, top=6)
        self.brokersFee = EveLabelMedium(text='', padRight=4)
        self.numbersGrid.AddCell(self.brokersFee)
        self.brokersFeeAmt = EveLabelMediumBold(text='', align=uiconst.CENTERRIGHT, padLeft=4)
        self.numbersGrid.AddCell(self.brokersFeeAmt)
        self.salesTax = EveLabelMedium(text='', padRight=4)
        self.numbersGrid.AddCell(self.salesTax)
        self.salesTaxAmt = EveLabelMediumBold(text='', align=uiconst.CENTERRIGHT, padLeft=4)
        self.numbersGrid.AddCell(self.salesTaxAmt)
        spacer = Container(align=uiconst.TOTOP, height=12)
        self.numbersGrid.AddCell(spacer, colSpan=2)
        self.totalAmt = EveLabelLargeBold(text='', align=uiconst.CENTERRIGHT, padLeft=4, color=COL_GREEN)
        self.numbersGrid.AddCell(self.totalAmt, colSpan=2)

    def UpdateNumbers(self):
        brokersFee, salesTax, totalSum = self.GetSums()
        totalShown = totalSum - salesTax - brokersFee
        if totalSum > 0:
            brokersPerc = round(brokersFee / totalSum * 100, 2)
            salesPerc = round(salesTax / totalSum * 100, 2)
        else:
            brokersPerc = 0.0
            salesPerc = 0.0
        self.brokersFeeAmt.text = FmtISK(brokersFee)
        self.brokersFee.text = GetByLabel('UI/Market/MarketQuote/BrokersFeePerc', percentage=brokersPerc)
        self.salesTaxAmt.text = FmtISK(salesTax)
        self.salesTax.text = GetByLabel('UI/Market/MarketQuote/SalesTaxPerc', percentage=salesPerc)
        self.totalAmt.text = FmtISK(totalShown)
        if totalShown < 0:
            self.totalAmt.color = COL_RED
        else:
            self.totalAmt.color = COL_GREEN

    def GetSums(self):
        brokersFee = 0.0
        salesTax = 0
        totalSum = 0
        isImmediate = self.durationCombo.GetValue() == 0
        for item in self.GetItems():
            if item:
                brokersFee += item.brokersFee
                if isImmediate and item.bestBid is None:
                    salesTax += 0
                else:
                    salesTax += item.salesTax
                totalSum += item.totalSum

        if isImmediate:
            brokersFee = 0.0
        return (brokersFee, salesTax, totalSum)

    def SellItems(self, *args):
        self.sellItemList = []
        unitCount = self.GetUnitCount()
        allItems = self.GetItems()
        if unitCount == 0:
            return
        if eve.Message('ConfirmSellingItems', {'noOfItems': int(unitCount)}, uiconst.OKCANCEL, suppress=uiconst.ID_OK) != uiconst.ID_OK:
            return
        self.errorItemList = []
        if self.useCorp:
            useCorp = self.useCorp.checked
        else:
            useCorp = False
        duration = self.durationCombo.GetValue()
        for item in allItems:
            if duration == 0:
                if item.bestBid:
                    self.ValidateItem(item)
                else:
                    continue
            else:
                self.ValidateItem(item)

        if not len(self.sellItemList):
            return
        sm.GetService('marketQuote').SellMulti(self.sellItemList, useCorp, duration)
        self.Close()

    def GetUnitCount(self):
        unitCount = 0
        for item in self.itemList:
            if self.durationCombo.GetValue() == 0:
                if item.bestBid:
                    if item.bestBid.volRemaining > item.GetQty():
                        unitCount += item.GetQty()
                    else:
                        unitCount += item.bestBid.volRemaining
            else:
                unitCount += item.GetQty()

        return unitCount

    def ValidateItem(self, item):
        price = round(item.GetPrice(), 2)
        if price > 9223372036854.0:
            return
        if self.durationCombo.GetValue() == 0:
            if not item.bestBid:
                return
        qty = item.GetQty()
        validatedItem = KeyVal(stationID=int(item.stationID), typeID=int(item.typeID), itemID=item.itemID, price=price, quantity=int(qty), located=item.located)
        self.sellItemList.append(validatedItem)

    def GetStationLocationText(self):
        stationLocation = cfg.evelocations.Get(self.baseStationID).locationName
        return stationLocation

    def OnGlobalMouseHover(self, *args, **kw):
        if uicore.IsDragging() and uicore.dragObject:
            mo = uicore.uilib.mouseOver
            if mo == self or mo.IsUnder(self):
                if not self.hasDrawn:
                    self.DrawDraggedItems(uicore.dragObject.dragData)
            else:
                self.ClearDragData()
        else:
            self.ClearDragData()
        return True

    def DrawDraggedItems(self, dragData):
        if getattr(dragData[0], '__guid__', None) != 'xtriui.InvItem':
            return
        self.hasDrawn = True
        uicore.animations.FadeOut(self.dropLabel, duration=0.15)
        noOfItems = len(dragData)
        noOfAvailable = math.floor((self.width - 16) / 28)
        for i, dragItem in enumerate(dragData):
            c = Container(parent=self.fakeItemsCont, align=uiconst.TOLEFT, padding=2, width=24)
            if noOfItems > noOfAvailable and i == noOfAvailable - 1:
                icon = Sprite(parent=c, texturePath='res:/UI/Texture/classes/MultiSell/DotDotDot.png', state=uiconst.UI_DISABLED, width=24, height=24, align=uiconst.CENTER)
                icon.SetAlpha(0.6)
                return
            icon = Icon(parent=c, typeID=dragItem.item.typeID, state=uiconst.UI_DISABLED)
            icon.SetSize(24, 24)

    def ClearDragData(self):
        self.fakeItemsCont.Flush()
        uicore.animations.FadeIn(self.dropLabel, 0.6, duration=0.3)
        self.hasDrawn = False

    def OnDropData(self, dragSource, dragData):
        self.ClearDragData()


class SellItemContainer(Container):
    __guid__ = 'uicls.SellItemContainer'
    default_height = 40
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.parentFunc = attributes.parentFunc
        self.padding = (0, 2, 0, 2)
        self.item = attributes.item
        self.singleton = self.item.singleton
        self.parentEditFunc = attributes.editFunc
        self.typeID = self.item.typeID
        self.itemID = self.item.itemID
        self.invType = cfg.invtypes.Get(self.typeID)
        self.itemName = self.invType.name
        self.brokersFee = 0.0
        self.salesTax = 0.0
        self.totalSum = 0.0
        self.quote = sm.GetService('marketQuote')
        self.limits = self.quote.GetSkillLimits()
        self.stationID, officeFolderID, officeID = sm.GetService('invCache').GetStationIDOfficeFolderIDOfficeIDOfItem(self.item)
        self.located = None
        if officeFolderID is not None:
            self.located = [officeFolderID, officeID]
        station = sm.GetService('ui').GetStation(self.stationID)
        self.solarSystemID = station.solarSystemID
        self.regionID = self.GetRegionID(self.stationID)
        self.averagePrice = self.quote.GetAveragePrice(self.typeID)
        self.bestBid = self.quote.GetBestBid(self.typeID, locationID=self.solarSystemID)
        self.GetBestPrice()
        self.deltaCont = Container(parent=self, align=uiconst.TORIGHT, width=30)
        theRestCont = Container(parent=self, align=uiconst.TOALL)
        self.totalCont = Container(parent=theRestCont, align=uiconst.TORIGHT_PROP, width=0.3)
        self.priceCont = Container(parent=theRestCont, align=uiconst.TORIGHT_PROP, width=0.22)
        self.qtyCont = Container(parent=theRestCont, align=uiconst.TORIGHT_PROP, width=0.15)
        self.itemCont = Container(parent=theRestCont, align=uiconst.TORIGHT_PROP, width=0.33)
        self.deleteCont = Container(parent=self.itemCont, align=uiconst.TORIGHT, width=24)
        self.deleteButton = ButtonIcon(texturePath='res:/UI/Texture/Icons/73_16_210.png', pos=(0, 0, 16, 16), align=uiconst.CENTERRIGHT, parent=self.deleteCont, hint=GetByLabel('UI/Generic/RemoveItem'), idx=0, func=self.RemoveItem)
        self.deleteCont.display = False
        self.textCont = Container(parent=self.itemCont, align=uiconst.TOALL)
        self.errorBg = ErrorFrame(bgParent=self)
        self.DrawItem()
        self.DrawQty()
        self.DrawPrice()
        self.DrawTotal()
        self.DrawDelta()
        self.GetTotalSum()
        self.GetBrokersFee()
        self.GetSalesTax()
        self.ShowNoSellOrders()

    def RemoveItem(self, *args):
        self.parentFunc(self, *args)

    def GetRegionID(self, stationID):
        regionID = cfg.evelocations.Get(stationID).Station().regionID
        return regionID

    def ShowNoSellOrders(self):
        wnd = SellItems.GetIfOpen()
        if not wnd:
            return
        if wnd.durationCombo.GetValue() == 0 and self.bestBid is None:
            uicore.animations.FadeIn(self.errorBg, 0.35, duration=0.3)

    def HideNoSellOrders(self):
        uicore.animations.FadeOut(self.errorBg, duration=0.3)

    def DrawQty(self):
        qty = self.item.stacksize
        self.qtyEdit = SinglelineEdit(name='qtyEdit', parent=self.qtyCont, align=uiconst.TOTOP, top=11, padLeft=4)
        self.qtyEdit.IntMode(*(1, long(qty)))
        self.qtyEdit.SetValue(qty)
        self.qtyEdit.OnChange = self.OnChange
        self.qtyEdit.hint = GetByLabel('UI/Common/Quantity')

    def DrawTotal(self):
        self.totalLabel = EveLabelMediumBold(text=self.totalSum, parent=self.totalCont, left=4, align=uiconst.CENTERRIGHT, state=uiconst.UI_NORMAL, autoFadeSides=35)
        self.totalLabel.hint = GetByLabel('UI/Market/MarketQuote/AskTotal')

    def DrawPrice(self):
        self.priceEdit = SinglelineEdit(name='priceEdit', parent=self.priceCont, align=uiconst.TOTOP, top=11, padLeft=8)
        self.priceEdit.FloatMode(*(0.01, 9223372036854.0, 2))
        self.priceEdit.SetValue(self.bestPrice)
        self.priceEdit.OnChange = self.OnChange
        self.priceEdit.hint = GetByLabel('UI/Market/MarketQuote/AskPrice')

    def DrawDelta(self):
        self.deltaContainer = DeltaContainer(parent=self.deltaCont, delta=self.GetDelta(), func=self.OpenMarket, align=uiconst.CENTERRIGHT)
        self.deltaContainer.LoadTooltipPanel = self.LoadDeltaTooltip
        self.UpdateDelta()

    def OnMouseEnter(self, *args):
        self.mouseovertimer = AutoTimer(1, self.UpdateMouseOver)
        self.deleteCont.display = True

    def UpdateMouseOver(self):
        mo = uicore.uilib.mouseOver
        if mo in (self.itemNameLabel,
         self,
         self.deleteCont,
         self.deleteButton,
         self.totalLabel):
            return
        self.mouseovertimer = None
        self.deleteCont.display = False

    def Close(self, *args):
        self.mouseovertimer = None
        self.parentFunc = None
        Container.Close(self, *args)

    def OpenMarket(self, *args):
        sm.GetService('marketutils').ShowMarketDetails(self.typeID, None)
        wnd = SellItems.GetIfOpen()
        wnd.SetOrder(0)

    def LoadDeltaTooltip(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric2ColumnTemplate()
        tooltipPanel.cellPadding = (4, 1, 4, 1)
        tooltipPanel.AddLabelLarge(text=GetByLabel('UI/Market/MarketQuote/AskPrice'))
        tooltipPanel.AddLabelLarge(text=FmtISK(self.priceEdit.GetValue()), align=uiconst.CENTERRIGHT)
        tooltipPanel.AddSpacer(1, 8, colSpan=tooltipPanel.columns)
        tooltipPanel.AddLabelMedium(text='%s %s' % (GetByLabel('UI/Market/MarketQuote/RegionalAdverage'), self.GetDeltaText()))
        tooltipPanel.AddLabelMedium(text=FmtISK(self.averagePrice), align=uiconst.CENTERRIGHT)
        tooltipPanel.AddLabelMedium(text=GetByLabel('UI/Market/MarketQuote/BestRegional'))
        bestMatch = tooltipPanel.AddLabelMedium(text='', align=uiconst.CENTERRIGHT)
        bestMatchDetails = tooltipPanel.AddLabelSmall(text='', align=uiconst.CENTERRIGHT, colSpan=tooltipPanel.columns)
        if not self.bestBid:
            bestMatch.text = GetByLabel('UI/Contracts/ContractEntry/NoBids')
            bestMatchDetails.text = GetByLabel('UI/Market/MarketQuote/ImmediateWillFail')
            bestMatch.color = (1.0, 0.275, 0.0, 1.0)
            bestMatchDetails.color = (1.0, 0.275, 0.0, 1.0)
        else:
            bestMatch.text = FmtISK(self.bestBid.price)
            bestMatchText, volRemaining = self.GetBestMatchText()
            bestMatchDetails.text = bestMatchText
            bestMatchDetails.SetAlpha(0.6)
            if volRemaining:
                vol = tooltipPanel.AddLabelSmall(text=volRemaining, align=uiconst.CENTERRIGHT, colSpan=tooltipPanel.columns)
                vol.SetAlpha(0.6)

    def GetDeltaText(self):
        price = self.GetPrice()
        percentage = (price - self.averagePrice) / self.averagePrice
        if percentage < 0:
            color = '<color=0xffff5050>'
        else:
            color = '<color=0xff00ff00>'
        percText = '%s%s</color>' % (color, GetByLabel('UI/Common/Percentage', percentage=FmtAmt(percentage * 100, showFraction=1)))
        return percText

    def GetBestMatchText(self):
        jumps = max(self.bestBid.jumps - max(0, self.bestBid.range), 0)
        minVolumeText = None
        if jumps == 0 and self.stationID == self.bestBid.stationID:
            jumpText = GetByLabel('UI/Market/MarketQuote/ItemsInSameStation')
        else:
            jumpText = GetByLabel('UI/Market/MarketQuote/JumpsFromThisSystem', jumps=jumps)
        if self.bestBid.minVolume > 1 and self.bestBid.volRemaining >= self.bestBid.minVolume:
            minVolumeText = GetByLabel('UI/Market/MarketQuote/SimpleMinimumVolume', min=self.bestBid.minVolume)
        return (GetByLabel('UI/Market/MarketQuote/SellQuantity', volRemaining=long(self.bestBid.volRemaining), jumpText=jumpText), minVolumeText)

    def GetDelta(self):
        price = self.GetPrice()
        percentage = (price - self.averagePrice) / self.averagePrice
        return percentage

    def UpdateDelta(self):
        delta = self.GetDelta()
        self.deltaContainer.UpdateDelta(delta)

    def DrawItem(self):
        iconCont = Container(parent=self.textCont, align=uiconst.TOLEFT, width=32, padding=4)
        self.icon = Icon(parent=iconCont, typeID=self.typeID, state=uiconst.UI_DISABLED)
        self.icon.SetSize(32, 32)
        itemName = GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=self.itemName, info=('showinfo', self.typeID, self.item.itemID))
        self.itemNameLabel = Label(text=itemName, parent=self.textCont, left=40, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, autoFadeSides=35, fontsize=12)

    def GetBestPrice(self):
        bestMatchableBid = self.quote.GetBestMatchableBid(self.typeID, self.stationID, self.item.stacksize)
        if bestMatchableBid:
            self.bestPrice = bestMatchableBid.price
        else:
            self.bestPrice = self.averagePrice

    def GetBrokersFee(self):
        fee = self.quote.BrokersFee(self.stationID, self.totalSum, self.limits['fee'])
        feeAmount = fee.amt
        self.brokersFee = feeAmount

    def GetSalesTax(self):
        tax = self.totalSum * self.limits['acc']
        self.salesTax = tax

    def GetTotalSum(self):
        price = self.GetPrice()
        qty = self.GetQty()
        self.totalSum = price * qty
        self.totalLabel.text = FmtISK(self.totalSum)
        return self.totalSum

    def OnChange(self, *args):
        self.GetTotalSum()
        self.GetBrokersFee()
        self.GetSalesTax()
        self.UpdateDelta()
        if self.parentEditFunc:
            self.parentEditFunc(args)

    def GetPrice(self):
        price = self.priceEdit.GetValue()
        return price

    def GetQty(self):
        qty = self.qtyEdit.GetValue()
        return qty

    def MakeSingle(self):
        self.height = 80
        self.qtyCont.width = 0
        self.itemCont.width = 0.42
        self.totalCont.width = 0.36
        self.itemNameLabel.fontsize = 14
        self.totalLabel.fontsize = 14
        self.itemNameLabel.left = 72
        self.icon.SetSize(64, 64)
        self.icon.top = 4
        self.priceEdit.padLeft = 4
        self.priceEdit.align = uiconst.TOBOTTOM
        self.qtyEdit.top = 20
        self.priceEdit.top = 20
        self.qtyEdit.SetParent(self.priceCont)

    def RemoveSingle(self):
        self.height = 40
        self.qtyCont.width = 0.15
        self.itemCont.width = 0.33
        self.totalCont.width = 0.3
        self.itemNameLabel.fontsize = 12
        self.totalLabel.fontsize = 12
        self.itemNameLabel.left = 40
        self.icon.SetSize(32, 32)
        self.icon.top = 0
        self.priceEdit.align = uiconst.TOTOP
        self.qtyEdit.top = 11
        self.priceEdit.top = 11
        self.priceEdit.padLeft = 8
        self.qtyEdit.SetParent(self.qtyCont)


class DeltaContainer(ButtonIcon):
    __guid__ = 'uicls.DeltaContainer'
    default_height = 24

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)
        delta = attributes.delta
        self.icon = self.ConstructIcon()
        self.deltaText = Label(parent=self, align=uiconst.CENTER, fontsize=9, top=2)
        self.UpdateDelta(delta)

    def ConstructIcon(self):
        return GlowSprite(name='icon', parent=self, align=uiconst.CENTERTOP, width=self.iconSize, height=self.iconSize, texturePath=self.texturePath, state=uiconst.UI_DISABLED, color=self.iconColor, rotation=self.rotation)

    def UpdateDelta(self, delta):
        deltaText = self.GetDeltaText(delta)
        if delta > 0:
            self.deltaText.text = deltaText
            self.deltaText.align = uiconst.CENTERBOTTOM
            self.icon.align = uiconst.CENTERTOP
            texturePath = 'res:/UI/Texture/classes/MultiSell/up.png'
        elif delta < 0:
            self.deltaText.text = deltaText
            self.deltaText.align = uiconst.CENTERTOP
            self.icon.align = uiconst.CENTERBOTTOM
            texturePath = 'res:/UI/Texture/classes/MultiSell/down.png'
        else:
            self.icon.align = uiconst.CENTER
            self.deltaText.text = ''
            texturePath = 'res:/UI/Texture/classes/MultiSell/equal.png'
        self.icon.SetTexturePath(texturePath)

    def GetDeltaText(self, delta):
        if delta < 0:
            color = '<color=0xffff5050>'
        else:
            color = '<color=0xff00ff00>'
        if abs(delta) < 1.0:
            showFraction = 1
        else:
            showFraction = 0
        deltaText = '%s%s</color>' % (color, GetByLabel('UI/Common/Percentage', percentage=FmtAmt(delta * 100, showFraction=showFraction)))
        return deltaText
