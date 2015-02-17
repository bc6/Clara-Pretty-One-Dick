#Embedded file name: eve/client/script/ui/shared/planet\expeditedTransferUI.py
"""
    This file houses the expedited transfer (one-off transfer) UI, which is used to 
    move commodities from a storage pin to an arbitrary destination, once.
"""
import math
import carbonui.const as uiconst
import const
import eve.client.script.ui.control.entries as listentry
import base
import blue
import uiprimitives
import uicontrols
import uix
import util
import uicls
import eve.common.script.util.planetCommon as planetCommon
from . import planetCommon as planetCommonUI
import uthread
import localization

class ExpeditedTransferManagementWindow(uicontrols.Window):
    __guid__ = 'form.ExpeditedTransferManagementWindow'
    default_windowID = 'createTransfer'
    default_iconNum = 'res:/ui/Texture/WindowIcons/items.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.planet = attributes.planet
        self.path = attributes.path
        if not self.path or len(self.path) < 2:
            raise UserError('CreateRouteTooShort')
        colony = self.planet.GetColony(session.charid)
        self.sourcePin = colony.GetPin(self.path[0])
        self.destinationPin = None
        minBandwidth = None
        prevID = None
        pin = None
        for pinID in self.path:
            pin = colony.GetPin(pinID)
            if not pin:
                raise UserError('RouteFailedValidationPinDoesNotExist')
            if prevID is None:
                prevID = pinID
                continue
            link = colony.GetLink(pin.id, prevID)
            if link is None:
                raise UserError('RouteFailedValidationLinkDoesNotExist')
            if minBandwidth is None or minBandwidth > link.GetTotalBandwidth():
                minBandwidth = link.GetTotalBandwidth()
            prevID = pinID

        self.availableBandwidth = minBandwidth
        sourceName = planetCommon.GetGenericPinName(self.sourcePin.typeID, self.sourcePin.id)
        self.SetCaption(localization.GetByLabel('UI/PI/Common/ExpeditedTransferFrom', sourceName=sourceName))
        self.SetMinSize([500, 400])
        self.SetWndIcon(self.iconNum)
        self.MakeUnstackable()
        uicontrols.WndCaptionLabel(text=localization.GetByLabel('UI/PI/Common/PreparingExpeditedTransferOrder'), subcaption=localization.GetByLabel('UI/PI/Common/ExpeditedTransferSubHeading'), parent=self.sr.topParent, align=uiconst.RELATIVE)
        self.ConstructLayout()
        self.SetSourcePinGaugeInfo()
        self.scope = 'station_inflight'
        self.ResetPinContents()
        self.SetDestination(colony.GetPin(self.path[-1]))
        self.OnResizeUpdate()
        self.updateTimer = base.AutoTimer(100, self.SetNextTransferText)

    def ConstructLayout(self):
        pad = const.defaultPadding
        self.sr.footer = uiprimitives.Container(name='footer', parent=self.sr.main, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 25), padding=(pad,
         pad,
         pad,
         pad))
        self.sr.cols = uiprimitives.Container(name='col1', parent=self.sr.main, align=uiconst.TOALL)
        uiprimitives.Line(parent=self.sr.cols, align=uiconst.TOTOP)
        uiprimitives.Line(parent=self.sr.cols, align=uiconst.TOBOTTOM)
        self.sr.col1 = uiprimitives.Container(name='col1', parent=self.sr.cols, align=uiconst.TOLEFT, padding=(pad,
         pad,
         pad,
         pad), clipChildren=True)
        self.sr.col2 = uiprimitives.Container(name='col1', parent=self.sr.cols, align=uiconst.TOLEFT, padding=(pad,
         pad,
         pad,
         pad), clipChildren=True)
        uiprimitives.Line(parent=self.sr.cols, align=uiconst.TOLEFT)
        self.sr.col3 = uiprimitives.Container(name='col1', parent=self.sr.cols, align=uiconst.TOLEFT, padding=(pad,
         pad,
         pad,
         pad), clipChildren=True)
        colTopHeight = 60
        self.sr.sourcePinHeader = uiprimitives.Container(name='pinHeader', parent=self.sr.col1, align=uiconst.TOTOP, padding=(pad,
         0,
         pad,
         pad), pos=(0,
         0,
         0,
         colTopHeight))
        self.sr.sourcePinList = uiprimitives.Container(name='pinList', parent=self.sr.col1, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.sr.transferHeader = uiprimitives.Container(name='transferHeader', parent=self.sr.col2, align=uiconst.TOTOP, padding=(pad,
         0,
         pad,
         pad), pos=(0,
         0,
         0,
         colTopHeight))
        self.sr.transferList = uiprimitives.Container(name='transferList', parent=self.sr.col2, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.sr.destPinHeader = uiprimitives.Container(name='destPinHeader', parent=self.sr.col3, align=uiconst.TOTOP, padding=(pad,
         0,
         pad,
         pad), pos=(0,
         0,
         0,
         colTopHeight))
        self.sr.destPinList = uiprimitives.Container(name='destPinList', parent=self.sr.col3, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.sr.footerLeft = uiprimitives.Container(name='footerLeft', parent=self.sr.footer, align=uiconst.TOLEFT)
        self.sr.footerRight = uiprimitives.Container(name='footerRight', parent=self.sr.footer, align=uiconst.TORIGHT)
        btns = [(localization.GetByLabel('UI/PI/Common/ExecuteTransfer'),
          self.GoForTransfer,
          (),
          None)]
        uicontrols.ButtonGroup(btns=btns, parent=self.sr.footerRight, line=0)
        self.sr.volumeText = uicontrols.EveLabelSmall(text='', parent=self.sr.transferHeader, left=0, top=20, state=uiconst.UI_NORMAL)
        self.sr.timeText = uicontrols.EveLabelSmall(text='', parent=self.sr.transferHeader, left=0, top=35, state=uiconst.UI_NORMAL)
        self.sr.timeText.hint = localization.GetByLabel('UI/PI/Common/ExpeditedTransferProcessingHint')
        self.sr.cooldownTimeText = uicontrols.EveLabelSmall(parent=self.sr.transferHeader, left=0, top=46)
        self.sr.cooldownTimeText.hint = localization.GetByLabel('UI/PI/Common/CoolDownTimeHint')
        btns = [(localization.GetByLabel('UI/PI/Common/Add'),
          self.AddBtnClicked,
          (),
          None), (localization.GetByLabel('UI/PI/Common/Remove'),
          self.RemoveBtnClicked,
          (),
          None)]
        btns = uicontrols.ButtonGroup(btns=btns, parent=self.sr.footerLeft, line=0)
        for b in btns.children[0].children:
            b.SetHint(localization.GetByLabel('UI/PI/Common/ExpeditedTransferSplitHint'))

        self.OnResizeUpdate()
        self.sr.sourcePinHeaderText = uicontrols.Label(text=planetCommon.GetGenericPinName(self.sourcePin.typeID, self.sourcePin.id), parent=self.sr.sourcePinHeader, align=uiconst.TOPLEFT, fontsize=16, left=0, state=uiconst.UI_NORMAL)
        self.sr.sourcePinSubGauge = uicls.Gauge(parent=self.sr.sourcePinHeader, value=0.0, color=planetCommonUI.PLANET_COLOR_STORAGE, label=localization.GetByLabel('UI/PI/Common/Capacity'), left=0, top=24, state=uiconst.UI_NORMAL)
        self.sr.sourcePinListScroll = uicontrols.Scroll(parent=self.sr.sourcePinList, name='pinList')
        content = self.sr.sourcePinListScroll.sr.content
        content.OnDropData = self.OnSourceScrollDropData
        self.sr.transferHeaderText = uicontrols.Label(text=localization.GetByLabel('UI/PI/Common/ToBeTransferred'), parent=self.sr.transferHeader, align=uiconst.TOPLEFT, fontsize=16, left=0, state=uiconst.UI_NORMAL)
        self.sr.transferListScroll = uicontrols.Scroll(parent=self.sr.transferList, name='transferList')
        content = self.sr.transferListScroll.sr.content
        content.OnDropData = self.OnTransferScrollDropData
        self.sr.destPinText = uicontrols.Label(text='', parent=self.sr.destPinHeader, align=uiconst.TOTOP, fontsize=16, state=uiconst.UI_NORMAL, maxLines=1)
        self.sr.destPinSubText = uicontrols.EveLabelLarge(text='', parent=self.sr.destPinHeader, align=uiconst.TOTOP, top=5, state=uiconst.UI_HIDDEN)
        self.sr.destPinSubGauge = uicls.Gauge(parent=self.sr.destPinHeader, value=0.0, color=planetCommonUI.PLANET_COLOR_STORAGE, label=localization.GetByLabel('UI/PI/Common/Capacity'), left=0, top=24, state=uiconst.UI_HIDDEN)
        self.sr.destPinListScroll = uicontrols.Scroll(parent=self.sr.destPinList)

    def OnTransferScrollDropData(self, dragObj, nodes, *args):
        if nodes[0].scroll.name == 'pinList':
            self.AddCommodity(nodes)

    def OnSourceScrollDropData(self, dragObj, nodes, *args):
        if nodes[0].scroll.name == 'transferList':
            self.RemoveCommodity(nodes)

    def OnResizeUpdate(self, *args):
        if self.destroyed:
            return
        uthread.new(self.__OnResizeUpdate)

    def __OnResizeUpdate(self):
        if not self.sr.col1:
            return
        sl, st, sw, sh = self.GetAbsolute()
        desiredWidth = (sw - 25) / 3
        self.sr.col1.width = desiredWidth
        self.sr.col2.width = desiredWidth
        self.sr.col3.width = desiredWidth
        self.sr.footerLeft.width = 2 * desiredWidth + 3 * const.defaultPadding
        self.sr.footerRight.width = desiredWidth + const.defaultPadding

    def AddBtnClicked(self, *args):
        selected = self.sr.sourcePinListScroll.GetSelected()
        self.AddCommodity(selected)

    def RemoveBtnClicked(self, *args):
        selected = self.sr.transferListScroll.GetSelected()
        self.RemoveCommodity(selected)

    def AddCommodity(self, selected):
        toMove = {}
        if len(selected) == 1 and uicore.uilib.Key(uiconst.VK_SHIFT):
            typeID = selected[0].typeID
            typeName = cfg.invtypes.Get(typeID).name
            ret = uix.QtyPopup(self.pinContents[typeID], 1, 1, None, localization.GetByLabel('UI/PI/Common/QuantityToTransfer', typeName=typeName))
            if ret and 'qty' in ret:
                toMove[typeID] = min(self.pinContents[typeID], max(1, ret['qty']))
        else:
            for entry in selected:
                toMove[entry.typeID] = self.pinContents[entry.typeID]

        if self.destPin.IsConsumer():
            toMove = self._ApplyConsumerFilter(toMove)
            if not toMove:
                raise UserError('ConsumerCantAcceptCommodities')
        elif self.destPin.IsStorage():
            toMove = self._ApplyMaxAmountFilter(toMove)
        for typeID, qty in toMove.iteritems():
            self.pinContents[typeID] -= qty
            if self.pinContents[typeID] <= 0:
                del self.pinContents[typeID]
            if typeID not in self.transferContents:
                self.transferContents[typeID] = 0
            self.transferContents[typeID] += qty

        self.RefreshLists()

    def _ApplyConsumerFilter(self, toMove):
        """
        Filter out stuff that can't be accepted by the consuming pin, and limit the quantity
        to the amount the consumer can accept
        """
        newToMove = {}
        for typeID, qty in toMove.iteritems():
            remainingSpace = self.destPin.CanAccept(typeID, -1)
            alreadyInTransfer = self.transferContents.get(typeID, 0)
            if remainingSpace:
                amount = min(remainingSpace - alreadyInTransfer, qty)
                if amount > 0:
                    newToMove[typeID] = amount

        return newToMove

    def _ApplyMaxAmountFilter(self, toMove):
        """
        Make sure that there is enough space at destination before moving stuff to the
        transfer list. If we are only moving one commodity, we move as much as we can.
        If we are moving more than one commodity, we move nothing.
        """
        availableVolume = self.destPin.GetCapacity() - self.destPin.capacityUsed
        availableVolume -= planetCommon.GetCommodityTotalVolume(self.transferContents)
        transferVolume = planetCommon.GetCommodityTotalVolume(toMove)
        if transferVolume >= availableVolume:
            newToMove = {}
            if len(toMove) == 1:
                for typeID, quantity in toMove.iteritems():
                    commodityVolume = cfg.invtypes.Get(typeID).volume
                    maxAmount = int(math.floor(availableVolume / commodityVolume))
                    newToMove[typeID] = maxAmount

            eve.Message('ExpeditedTransferNotEnoughSpace')
            return newToMove
        else:
            return toMove

    def RemoveCommodity(self, selected):
        toMove = {}
        if len(selected) == 1 and uicore.uilib.Key(uiconst.VK_SHIFT):
            typeID = selected[0].typeID
            typeName = cfg.invtypes.Get(typeID).name
            ret = uix.QtyPopup(self.transferContents[typeID], 1, 1, None, localization.GetByLabel('UI/PI/Common/QuantityToRemove', typeName=typeName))
            if ret and 'qty' in ret:
                toMove[typeID] = min(self.transferContents[typeID], max(1, ret['qty']))
        else:
            for entry in selected:
                toMove[entry.typeID] = self.transferContents[entry.typeID]

        for typeID, qty in toMove.iteritems():
            self.transferContents[typeID] -= qty
            if self.transferContents[typeID] <= 0:
                del self.transferContents[typeID]
            if typeID not in self.pinContents:
                self.pinContents[typeID] = 0
            self.pinContents[typeID] += qty

        self.RefreshLists()

    def GoForTransfer(self, *args):
        if len(self.transferContents) < 1:
            raise UserError('PleaseSelectCommoditiesToTransfer')
        for typeID, quantity in self.transferContents.iteritems():
            if typeID not in self.sourcePin.contents:
                raise UserError('RouteFailedValidationExpeditedSourceLacksCommodity', {'typeName': cfg.invtypes.Get(typeID).name})
            if quantity > self.sourcePin.contents[typeID]:
                raise UserError('RouteFailedValidationExpeditedSourceLacksCommodityQty', {'typeName': cfg.invtypes.Get(typeID).name,
                 'qty': quantity})

        if not self.sourcePin.CanTransfer(self.transferContents):
            raise UserError('RouteFailedValidationExpeditedSourceNotReady')
        if len(self.transferContents) > 0:
            self.ShowLoad()
            try:
                self.planet.TransferCommodities(self.path, self.transferContents)
            finally:
                self.ResetPinContents()
                self.HideLoad()

            self.CloseByUser()

    def ResetPinContents(self, *args):
        self.pinContents = self.sourcePin.contents.copy()
        self.transferContents = {}
        self.RefreshLists()

    def RefreshLists(self, *args):
        pinListItems = []
        for typeID, qty in self.pinContents.iteritems():
            lbl = '<t>%s<t>%d' % (cfg.invtypes.Get(typeID).name, qty)
            data = util.KeyVal(itemID=None, typeID=typeID, label=lbl, getIcon=1, quantity=qty, OnDropData=self.OnSourceScrollDropData)
            pinListItems.append(listentry.Get('DraggableItem', data=data))

        transferListItems = []
        for typeID, qty in self.transferContents.iteritems():
            lbl = '<t>%s<t>%d' % (cfg.invtypes.Get(typeID).name, qty)
            data = util.KeyVal(itemID=None, typeID=typeID, label=lbl, getIcon=1, quantity=qty, OnDropData=self.OnTransferScrollDropData)
            transferListItems.append(listentry.Get('DraggableItem', data=data))

        self.sr.sourcePinListScroll.Load(contentList=pinListItems, noContentHint=localization.GetByLabel('UI/PI/Common/StorehouseIsEmpty'), headers=[localization.GetByLabel('UI/Common/Type'), localization.GetByLabel('UI/Common/Name'), localization.GetByLabel('UI/Common/Quantity')])
        self.sr.transferListScroll.Load(contentList=transferListItems, noContentHint=localization.GetByLabel('UI/PI/Common/NoItemsFound'), headers=[localization.GetByLabel('UI/Common/Type'), localization.GetByLabel('UI/Common/Name'), localization.GetByLabel('UI/Common/Quantity')])
        transferVolume = planetCommon.GetCommodityTotalVolume(self.transferContents)
        self.sr.volumeText.text = localization.GetByLabel('UI/PI/Common/VolumeAmount', amount=transferVolume)
        self.SetNextTransferText()
        self.SetCooldownTimeText()

    def SetNextTransferText(self):
        if self.sourcePin.lastRunTime is None or self.sourcePin.lastRunTime <= blue.os.GetWallclockTime():
            self.sr.timeText.text = localization.GetByLabel('UI/PI/Common/NextTransferNow')
        else:
            self.sr.timeText.text = localization.GetByLabel('UI/PI/Common/NextTransferTime', time=self.sourcePin.lastRunTime - blue.os.GetWallclockTime())

    def SetCooldownTimeText(self):
        time = planetCommon.GetExpeditedTransferTime(self.availableBandwidth, self.transferContents)
        self.sr.cooldownTimeText.text = localization.GetByLabel('UI/PI/Common/CooldownTime', time=time)

    def SetSourcePinGaugeInfo(self):
        self.sr.sourcePinSubGauge.state = uiconst.UI_DISABLED
        self.sr.sourcePinSubGauge.SetText(localization.GetByLabel('UI/PI/Common/Capacity'))
        usageRatio = self.sourcePin.capacityUsed / self.sourcePin.GetCapacity()
        self.sr.sourcePinSubGauge.SetSubText(localization.GetByLabel('UI/PI/Common/CapacityProportionUsed', capacityUsed=self.sourcePin.capacityUsed, capacityMax=self.sourcePin.GetCapacity(), percentage=usageRatio * 100.0))
        self.sr.sourcePinSubGauge.SetValue(usageRatio)

    def RefreshDestinationPinInfo(self):
        self.sr.destPinSubText.state = uiconst.UI_HIDDEN
        self.sr.destPinSubGauge.state = uiconst.UI_HIDDEN
        if not self.destPin:
            self.sr.destPinText.text = localization.GetByLabel('UI/PI/Common/NoOriginSelected')
            self.sr.destPinSubText.text = ''
            self.sr.destPinSubText.state = uiconst.UI_DISABLED
            self.sr.destPinListScroll.Load(contentList=[], noContentHint=localization.GetByLabel('UI/PI/Common/NoOriginSelected'))
            return
        self.sr.destPinText.text = localization.GetByLabel('UI/PI/Common/TransferDestinationName', typeName=planetCommon.GetGenericPinName(self.destPin.typeID, self.destPin.id))
        scrollHeaders = []
        scrollContents = []
        scrollNoContentText = ''
        if self.destPin.IsConsumer():
            self.sr.destPinSubText.state = uiconst.UI_DISABLED
            if self.destPin.schematicID is None:
                self.sr.destPinSubText.text = localization.GetByLabel('UI/PI/Common/NoSchematicInstalled')
                scrollNoContentText = localization.GetByLabel('UI/PI/Common/NoSchematicInstalled')
            else:
                self.sr.destPinSubText.text = localization.GetByLabel('UI/PI/Common/SchematicName', schematicName=cfg.schematics.Get(self.destPin.schematicID).schematicName)
                scrollHeaders = []
                demands = self.destPin.GetConsumables()
                for typeID, qty in demands.iteritems():
                    remainingSpace = self.destPin.CanAccept(typeID, -1)
                    load = qty - remainingSpace
                    fraction = load / float(qty)
                    data = {'label': cfg.invtypes.Get(typeID).name,
                     'text': localization.GetByLabel('UI/PI/Common/UnitQuantityAndDemand', quantity=load, demand=qty),
                     'value': fraction,
                     'iconID': cfg.invtypes.Get(typeID).iconID}
                    entry = listentry.Get('StatusBar', data=data)
                    scrollContents.append(entry)

        elif self.destPin.IsStorage():
            self.sr.destPinSubGauge.state = uiconst.UI_DISABLED
            self.sr.destPinSubGauge.SetText(localization.GetByLabel('UI/PI/Common/Capacity'))
            usageRatio = self.destPin.capacityUsed / self.destPin.GetCapacity()
            self.sr.destPinSubGauge.SetSubText(localization.GetByLabel('UI/PI/Common/CapacityProportionUsed', capacityUsed=self.destPin.capacityUsed, capacityMax=self.destPin.GetCapacity(), percentage=usageRatio * 100.0))
            self.sr.destPinSubGauge.SetValue(usageRatio)
            scrollHeaders = [localization.GetByLabel('UI/Common/Type'), localization.GetByLabel('UI/Common/Name'), localization.GetByLabel('UI/Common/Quantity')]
            contents = self.destPin.GetContents()
            for typeID, qty in contents.iteritems():
                lbl = '<t>%s<t>%d' % (cfg.invtypes.Get(typeID).name, qty)
                scrollContents.append(listentry.Get('DraggableItem', {'itemID': None,
                 'typeID': typeID,
                 'label': lbl,
                 'getIcon': 1,
                 'quantity': qty}))

            scrollNoContentText = localization.GetByLabel('UI/PI/Common/StorehouseIsEmpty')
        self.sr.destPinListScroll.Load(contentList=scrollContents, headers=scrollHeaders, noContentHint=scrollNoContentText)

    def SetDestination(self, destinationPin):
        self.destPin = destinationPin
        self.RefreshDestinationPinInfo()
