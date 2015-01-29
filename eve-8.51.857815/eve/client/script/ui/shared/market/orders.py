#Embedded file name: eve/client/script/ui/shared/market\orders.py
import blue
import uiprimitives
import uicontrols
import util
from eve.client.script.ui.control import entries as listentry
import base
import carbonui.const as uiconst
import log
import localization
import uiutil
MINSCROLLHEIGHT = 64
LEFTSIDEWIDTH = 74

class MarketOrders(uiprimitives.Container):
    __guid__ = 'form.MarketOrders'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnOwnOrdersChanged']
    lastUpdateTime = None
    refreshOrdersTimer = None

    def Close(self, *args, **kwds):
        uiprimitives.Container.Close(self, *args, **kwds)
        sm.UnregisterNotify(self)
        self.lastUpdateTime = None
        self.refreshOrdersTimer = None

    def OnOwnOrdersChanged(self, orders, reason, isCorp):
        if self and not self.destroyed and self.state != uiconst.UI_HIDDEN:
            self.RefreshOrders()

    def RefreshOrders(self):
        if self.lastUpdateTime and self.refreshOrdersTimer is None:
            diff = max(1, blue.os.TimeDiffInMs(self.lastUpdateTime, blue.os.GetWallclockTime()))
            if diff > 30000:
                self._RefreshOrders()
            else:
                self.refreshOrdersTimer = base.AutoTimer(int(diff), self._RefreshOrders)
        else:
            self._RefreshOrders()

    def _RefreshOrders(self):
        if self and not self.destroyed:
            if not getattr(self, 'ordersInited', 0):
                self.Setup()
            self.ShowOrders(isCorp=self.isCorp, refreshing=1)
            self.refreshOrdersTimer = None
            self.lastUpdateTime = blue.os.GetWallclockTime()

    def Setup(self, where = None):
        self.isCorp = None
        self.where = where
        self.limits = sm.GetService('marketQuote').GetSkillLimits()
        par = uiprimitives.Container(name='counter', parent=self, align=uiconst.TOBOTTOM, height=60, clipChildren=1)
        self.sr.counter = uicontrols.EveLabelMedium(parent=par, align=uiconst.TOLEFT, padding=const.defaultPadding, tabs=[175, 500], state=uiconst.UI_NORMAL)
        self.sr.counter2 = uicontrols.EveLabelMedium(parent=par, align=uiconst.TOLEFT, padding=(12,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), state=uiconst.UI_NORMAL)
        buySellCont = uiprimitives.Container(name='buySellCont', parent=self)
        self.dividerCont = uicontrols.DragResizeCont(name='dividerCont', settingsID='marketOrders', parent=buySellCont, align=uiconst.TOTOP_PROP, minSize=0.25, maxSize=0.75, defaultSize=0.5, clipChildren=True)
        sellParent = uiprimitives.Container(name='sellParent', parent=self.dividerCont.mainCont)
        sellLeft = uiprimitives.Container(name='sellLeft', parent=sellParent, align=uiconst.TOLEFT, width=LEFTSIDEWIDTH)
        sellingText = uicontrols.CaptionLabel(text=localization.GetByLabel('UI/Market/Orders/Selling'), parent=sellLeft, align=uiconst.RELATIVE, fontsize=16, left=4, top=4)
        scroll = uicontrols.Scroll(name='sellscroll', parent=sellParent)
        scroll.multiSelect = 0
        scroll.smartSort = 1
        scroll.ignoreHeaderWidths = 1
        scroll.sr.id = 'ordersSellScroll'
        scroll.OnColumnChanged = self.OnOrderSellColumnChanged
        self.sr.sellScroll = scroll
        self.sr.sellParent = sellParent
        buyParent = uiprimitives.Container(name='buyParent', parent=buySellCont)
        buyLeft = uiprimitives.Container(name='buyLeft', parent=buyParent, align=uiconst.TOLEFT, width=LEFTSIDEWIDTH)
        buyingText = uicontrols.CaptionLabel(text=localization.GetByLabel('UI/Market/Orders/Buying'), parent=buyLeft, align=uiconst.RELATIVE, fontsize=16, left=4, top=4)
        leftsidewidth = max(LEFTSIDEWIDTH, sellingText.width + 10, buyingText.width + 10)
        sellLeft.width = leftsidewidth
        buyLeft.width = leftsidewidth
        self.sr.counter.left = const.defaultPadding + leftsidewidth
        scroll = uicontrols.Scroll(name='buyscroll', parent=buyParent)
        scroll.multiSelect = 0
        scroll.smartSort = 1
        scroll.ignoreHeaderWidths = 1
        scroll.sr.id = 'ordersBuyScroll'
        scroll.OnColumnChanged = self.OnOrderBuyColumnChanged
        self.sr.buyScroll = scroll
        if self.isCorp:
            buttonHint = localization.GetByLabel('Tooltips/Market/MarketCorpOrdersExport')
        else:
            buttonHint = localization.GetByLabel('Tooltips/Market/MarketMyOrdersExportButton')
        uicontrols.Button(label=localization.GetByLabel('UI/Market/Orders/Export'), align=uiconst.BOTTOMLEFT, parent=par, func=self.ExportToFile, hint=buttonHint)
        sm.RegisterNotify(self)
        w, h = self.GetAbsoluteSize()
        self._OnSizeChange_NoBlock(w, h)
        self.ordersInited = 1

    def ExportToFile(self, *args):
        if self.isCorp:
            orders = sm.GetService('marketQuote').GetCorporationOrders()
        else:
            orders = sm.GetService('marketQuote').GetMyOrders()
        if len(orders) == 0:
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/Market/MarketWindow/ExportNoData')})
            return
        date = util.FmtDateEng(blue.os.GetWallclockTime())
        f = blue.classes.CreateInstance('blue.ResFile')
        directory = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '\\EVE\\logs\\Marketlogs\\'
        filename = '%s-%s.txt' % ([localization.GetByLabel('UI/Market/Orders/MyOrders'), localization.GetByLabel('UI/Market/Orders/CorporationOrders')][self.isCorp], util.FmtDateEng(blue.os.GetWallclockTime(), 'ls').replace(':', ''))
        filename = uiutil.SanitizeFilename(filename)
        if not f.Open(directory + filename, 0):
            f.Create(directory + filename)
        first = 1
        dateIdx = -1
        numSell = numBuy = 0
        for order in orders:
            if first:
                for key in order.__columns__:
                    f.Write('%s,' % key)
                    if key == 'charID':
                        f.Write('charName,')
                    elif key == 'regionID':
                        f.Write('regionName,')
                    elif key == 'stationID':
                        f.Write('stationName,')
                    elif key == 'solarSystemID':
                        f.Write('solarSystemName,')

                f.Write('\r\n')
                first = 0
            for key in order.__columns__:
                o = getattr(order, key, None)
                if key == 'bid':
                    if o > 0:
                        numBuy += 1
                    else:
                        numSell += 1
                if key == 'issueDate':
                    f.Write('%s,' % util.FmtDateEng(o, 'el').replace('T', ' '))
                elif key == 'charID':
                    f.Write('%s,%s,' % (o, str(cfg.eveowners.Get(o).name.encode('utf-8'))))
                elif key in ('stationID', 'regionID', 'solarSystemID'):
                    f.Write('%s,%s,' % (o, cfg.evelocations.Get(o).name.encode('utf-8')))
                else:
                    f.Write('%s,' % o)

            f.Write('\r\n')

        f.Close()
        eve.Message('PersonalMarketExportInfo', {'sell': numSell,
         'buy': numBuy,
         'filename': '<b>' + filename + '</b>',
         'directory': '<b>%s</b>' % directory})

    def GetLimitText(self, limit):
        if limit == -1:
            text = localization.GetByLabel('UI/Market/Orders/LimitedToStations')
        elif limit == 0:
            text = localization.GetByLabel('UI/Market/Orders/LimitedToSystem')
        elif limit == 50:
            text = localization.GetByLabel('UI/Market/Orders/LimitedToRegions')
        else:
            text = localization.GetByLabel('UI/Market/Orders/LimitedToJumps', jumps=limit)
        return text

    def UpdateCounter(self, current = None):
        if current is None:
            current = 0
        maxCount = self.limits['cnt']
        self.sr.counter.text = localization.GetByLabel('UI/Market/Orders/OrdersRemaining', remaining=maxCount - current, maxCount=maxCount, escrow=util.FmtISK(self.totalEscrow, showFractionsAlways=False), totalLeft=util.FmtISK(self.totalLeft, showFractionsAlways=False), feeLimit=round(self.limits['fee'] * 100, 2), accLimit=round(self.limits['acc'] * 100, 2), income=util.FmtISK(self.totalIncome, showFractionsAlways=False), expenses=util.FmtISK(self.totalExpenses, showFractionsAlways=False))
        askLimit = self.limits['ask']
        bidLimit = self.limits['bid']
        modLimit = self.limits['mod']
        visLimit = self.limits['vis']
        if askLimit == -1 and bidLimit == -1 and modLimit == -1 and visLimit == -1:
            self.sr.counter2.text = localization.GetByLabel('UI/Market/Orders/OrderRangesWithoutRemote')
        else:
            self.sr.counter2.text = localization.GetByLabel('UI/Market/Orders/OrderRanges', askLimit=self.GetLimitText(askLimit), bidLimit=self.GetLimitText(bidLimit), modLimit=self.GetLimitText(modLimit), visLimit=self.GetLimitText(visLimit))
        self.sr.counter.parent.height = max(60, self.sr.counter.textheight + const.defaultPadding * 2, self.sr.counter2.textheight + const.defaultPadding * 2)

    def OnOrderBuyColumnChanged(self, *args):
        self.ShowOrders(isCorp=self.isCorp)

    def OnOrderSellColumnChanged(self, *args):
        self.ShowOrders(isCorp=self.isCorp)

    def ShowOrders(self, isCorp = False, refreshing = 0):
        if isCorp is None:
            isCorp = False
        if self.isCorp is None:
            self.isCorp = isCorp
        sscrollList = []
        sheaders = self.sr.sellScroll.sr.headers = [localization.GetByLabel('UI/Common/Type'),
         localization.GetByLabel('UI/Common/Quantity'),
         localization.GetByLabel('UI/Market/MarketQuote/headerPrice'),
         localization.GetByLabel('UI/Common/Station'),
         localization.GetByLabel('UI/Common/LocationTypes/Region'),
         localization.GetByLabel('UI/Market/Marketbase/ExpiresIn')]
        if self.isCorp:
            sheaders.append(localization.GetByLabel('UI/Market/MarketQuote/headerIssuedBy'))
            sheaders.append(localization.GetByLabel('UI/Market/MarketQuote/headerWalletDivision'))
        visibleSHeaders = self.sr.sellScroll.GetColumns()
        bscrollList = []
        bheaders = self.sr.buyScroll.sr.headers = [localization.GetByLabel('UI/Common/Type'),
         localization.GetByLabel('UI/Common/Quantity'),
         localization.GetByLabel('UI/Market/MarketQuote/headerPrice'),
         localization.GetByLabel('UI/Common/Station'),
         localization.GetByLabel('UI/Common/LocationTypes/Region'),
         localization.GetByLabel('UI/Common/Range'),
         localization.GetByLabel('UI/Market/MarketQuote/HeaderMinVolumn'),
         localization.GetByLabel('UI/Market/Marketbase/ExpiresIn')]
        if self.isCorp:
            bheaders.append(localization.GetByLabel('UI/Market/MarketQuote/headerIssuedBy'))
            bheaders.append(localization.GetByLabel('UI/Market/MarketQuote/headerWalletDivision'))
        visibleBHeaders = self.sr.buyScroll.GetColumns()
        marketUtil = sm.GetService('marketutils')
        if self.isCorp:
            orders = sm.GetService('marketQuote').GetCorporationOrders()
        else:
            orders = sm.GetService('marketQuote').GetMyOrders()
        if self.destroyed:
            return
        self.totalEscrow = 0.0
        self.totalLeft = 0.0
        self.totalIncome = 0.0
        self.totalExpenses = 0.0
        buySelected = self.sr.buyScroll.GetSelected()
        sellSelected = self.sr.sellScroll.GetSelected()
        funcs = sm.GetService('marketutils').GetFuncMaps()
        for order in orders:
            scroll = [self.sr.sellScroll, self.sr.buyScroll][order.bid]
            if scroll == self.sr.sellScroll:
                self.totalIncome += order.price * order.volRemaining
            else:
                self.totalExpenses += order.price * order.volRemaining
            data = util.KeyVal()
            data.label = ''
            data.typeID = order.typeID
            data.order = order
            data.OnDblClick = self.ShowMarketDetilsForTypeInOrder
            if cfg.invtypes.GetIfExists(order.typeID) is not None:
                data.showinfo = 1
            selected = [sellSelected, buySelected][order.bid]
            if selected and selected[0].order.orderID == order.orderID:
                data.isSelected = 1
            visibleHeaders = [visibleSHeaders, visibleBHeaders][order.bid]
            for header in visibleHeaders:
                header = uiutil.StripTags(header, stripOnly=['localized'])
                funcName = funcs.get(header, None)
                if funcName == 'GetQuantity':
                    funcName = 'GetQuantitySlashVolume'
                if funcName and hasattr(marketUtil, funcName):
                    apply(getattr(marketUtil, funcName, None), (order, data))
                else:
                    log.LogWarn('Unsupported header in record', header, order)
                    data.label += '###<t>'

            data.label = data.label.rstrip('<t>')
            [sscrollList, bscrollList][order.bid].append(listentry.Get('OrderEntry', data=data))
            if order.bid:
                self.totalEscrow += order.escrow
                self.totalLeft += order.volRemaining * order.price - order.escrow

        buyScrollTo = None
        sellScrollTo = None
        if refreshing:
            buyScrollTo = self.sr.buyScroll.GetScrollProportion()
            sellScrollTo = self.sr.sellScroll.GetScrollProportion()
        self.sr.sellScroll.Load(contentList=sscrollList, headers=sheaders, scrollTo=sellScrollTo, noContentHint=localization.GetByLabel('UI/Market/Orders/NoOrdersFound'))
        self.sr.buyScroll.Load(contentList=bscrollList, headers=bheaders, scrollTo=buyScrollTo, noContentHint=localization.GetByLabel('UI/Market/Orders/NoOrdersFound'))
        if not isCorp:
            self.UpdateCounter(len(orders))

    def ShowMarketDetilsForTypeInOrder(self, order):
        sm.StartService('marketutils').ShowMarketDetails(order.typeID, None)


class OrderEntry(listentry.Generic):
    __guid__ = 'listentry.OrderEntry'
    __nonpersistvars__ = []

    def GetMenu(self):
        self.OnClick()
        m = []
        if self.sr.node.order.charID == session.charid:
            m.append((uiutil.MenuLabel('UI/Market/Orders/CancelOrder'), self.CancelOffer, (self.sr.node,)))
            m.append((uiutil.MenuLabel('UI/Market/Orders/ModifyOrder'), self.ModifyPrice, (self.sr.node,)))
        m.append(None)
        m += sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.sr.node.order.typeID, ignoreMarketDetails=0)
        m.append(None)
        stationInfo = sm.GetService('ui').GetStation(self.sr.node.order.stationID)
        m += [(uiutil.MenuLabel('UI/Common/Location'), sm.GetService('menu').CelestialMenu(self.sr.node.order.stationID, typeID=stationInfo.stationTypeID, parentID=stationInfo.solarSystemID))]
        return m

    def ShowInfo(self, *args):
        sm.GetService('info').ShowInfo(self.sr.node.order.typeID)

    def CancelOffer(self, node = None):
        node = node if node != None else self.sr.node
        sm.GetService('marketutils').CancelOffer(node.order)

    def ModifyPrice(self, node = None):
        node = node if node != None else self.sr.node
        sm.GetService('marketutils').ModifyOrder(node.order)
