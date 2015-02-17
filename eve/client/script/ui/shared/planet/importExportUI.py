#Embedded file name: eve/client/script/ui/shared/planet\importExportUI.py
"""
    This file houses the planetary launching UI, which is used to transfer
    commodities from the command pin to space.
"""
from inventorycommon.util import GetTypeVolume
import carbonui.const as uiconst
import const
import eve.client.script.ui.control.entries as listentry
import blue
import uiprimitives
import uicontrols
import uix
import uthread
import util
import uicls
import localization
import moniker
import log
import form
import eve.common.script.util.planetCommon as planetCommon
from . import planetCommon as planetCommonUI

class CustomsItem(listentry.Item):
    """ Wrapper around an inventory item to make it draggable from the customs office. """
    __guid__ = 'listentry.CustomsItem'
    isDragObject = True

    def Startup(self, *args):
        listentry.Item.Startup(self, *args)
        self.sr.selectedEntry = uiprimitives.Fill(parent=self, padTop=1, padBottom=1, color=(0.0, 1.0, 0.0, 0.25))
        self.sr.selectedEntry.state = uiconst.UI_HIDDEN
        if self.sr.node.isItemTransfer:
            self.sr.selectedEntry.state = uiconst.UI_PICKCHILDREN

    def GetDragData(self, *args):
        ret = []
        for node in self.sr.node.scroll.GetSelectedNodes(self.sr.node):
            if node.item is not None:
                item = uix.GetItemData(node.item, 'icon')
                item.scroll = node.scroll
                item.itemID = node.itemID
                item.typeID = node.typeID
                item.quantity = node.quantity
                ret.append(item)
            else:
                ret.append(node)

        return ret


class PlanetaryImportExportUI(uicontrols.Window):
    """ Customs Office Import / Export Window """
    __guid__ = 'form.PlanetaryImportExportUI'
    __notifyevents__ = ['OnItemChange',
     'OnPlanetPinsChanged',
     'OnBallparkCall',
     'OnRefreshPins']
    default_windowID = 'PlanetaryImportExportUI'
    default_iconNum = 'res:/ui/Texture/WindowIcons/items.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.spaceportPinID = attributes.spaceportPinID
        self.customsOfficeID = attributes.customsOfficeID
        self.id = self.customsOfficeID
        self.customsOffice = sm.GetService('invCache').GetInventoryFromId(self.customsOfficeID)
        if not self.customsOffice:
            raise RuntimeError('PlanetaryImportExportUI::Cannot find cargo link with ID %s' % str(self.customsOfficeID))
        bp = sm.GetService('michelle').GetBallpark()
        if self.customsOfficeID not in bp.slimItems:
            raise RuntimeError('OpenPlanetCustomsOfficeImportWindow::Failed to get cargo link data for link ID %s' % str(self.customsOfficeID))
        self.customsOfficeItem = bp.slimItems[self.customsOfficeID]
        self.customsOfficeLevel = self.customsOfficeItem.level
        if self.customsOfficeItem.planetID is None:
            raise RuntimeError('OpenPlanetCustomsOfficeImportWindow::Customs office slim item has no planetID set, most likely failed to startup correctly %s' % str(self.customsOfficeItem))
        self.planet = sm.GetService('planetSvc').GetPlanet(self.customsOfficeItem.planetID)
        self.scope = 'inflight'
        sm.GetService('inv').Register(self)
        blue.pyos.synchro.Yield()
        self.Layout()
        self._OnResize()
        self.ResetContents()

    def Layout(self):
        self.SetMinSize([560, 400])
        self.SetWndIcon(self.iconNum)
        self.SetTopparentHeight(56)
        self.MakeUnstackable()
        checkIsMyCorps = self.customsOfficeItem.ownerID == session.corpid
        checkIsStationManager = session.corprole & const.corpRoleStationManager == const.corpRoleStationManager
        if checkIsMyCorps and checkIsStationManager:
            self.SetHeaderIcon()
            self.settingsIcon = self.sr.headerIcon
            self.settingsIcon.state = uiconst.UI_NORMAL
            self.settingsIcon.GetMenu = self.GetSettingsMenu
            self.settingsIcon.expandOnLeft = 1
            self.settingsIcon.hint = localization.GetByLabel('UI/DustLink/ConfigureOrbital')
        self.windowCaption = uicontrols.WndCaptionLabel(text=localization.GetByLabel('UI/PI/Common/PlanetaryCustomsOfficeName', planetName=cfg.evelocations.Get(self.planet.planetID).name), subcaption=localization.GetByLabel('UI/PI/Common/ImportExportSubHeading'), parent=self.sr.topParent, align=uiconst.RELATIVE)
        self.SetCaption(localization.GetByLabel('UI/PI/Common/PlanetaryCustomsOfficeName', planetName=cfg.evelocations.Get(self.planet.planetID).name))
        pad = const.defaultPadding
        self.sr.footer = uiprimitives.Container(name='footer', parent=self.sr.main, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 25), padding=(pad * 2,
         0,
         pad,
         2))
        self.sr.cols = uiprimitives.Container(name='colums', parent=self.sr.main, align=uiconst.TOALL, padding=(pad,
         0,
         0,
         0))
        self.sr.leftColumn = uiprimitives.Container(name='leftColumn', parent=self.sr.cols, align=uiconst.TOLEFT, padding=(pad,
         pad,
         pad,
         pad), clipChildren=True)
        self.sr.rightColumn = uiprimitives.Container(name='rightColumn', parent=self.sr.cols, align=uiconst.TOLEFT, padding=(pad,
         pad,
         pad,
         pad), clipChildren=True)
        colTopHeight = 45
        self.sr.customsHeader = uiprimitives.Container(name='customsHeader', parent=self.sr.leftColumn, align=uiconst.TOTOP, padding=(pad,
         0,
         pad,
         pad), pos=(0,
         0,
         0,
         colTopHeight))
        self.sr.customsList = uiprimitives.Container(name='customsList', parent=self.sr.leftColumn, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.sr.customsHeaderTitle = uicontrols.Label(text=localization.GetByLabel('UI/PI/Common/PlanetaryCustomsOffice'), parent=self.sr.customsHeader, align=uiconst.TOPLEFT, fontsize=16, state=uiconst.UI_NORMAL)
        self.sr.customsGauge = uicls.Gauge(parent=self.sr.customsHeader, value=0.0, color=planetCommonUI.PLANET_COLOR_STORAGE, left=0, top=25, state=uiconst.UI_HIDDEN, align=uiconst.TOPLEFT)
        self.sr.spaceportHeader = uiprimitives.Container(name='spaceportHeader', parent=self.sr.rightColumn, align=uiconst.TOTOP, padding=(pad,
         0,
         pad,
         pad), pos=(0,
         0,
         0,
         colTopHeight))
        self.sr.spaceportList = uiprimitives.Container(name='spaceportList', parent=self.sr.rightColumn, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.sr.spaceportGauge = uicls.Gauge(parent=self.sr.spaceportHeader, value=0.0, color=planetCommonUI.PLANET_COLOR_STORAGE, left=0, top=25, state=uiconst.UI_HIDDEN, align=uiconst.TOPRIGHT)
        self.sr.spaceportCombo = uicontrols.Combo(label=None, parent=self.sr.spaceportHeader, options=[], name='imex_import_select', callback=self.OnSpaceportComboChanged, width=70, align=uiconst.TOTOP)
        self.sr.transferCostLabel = uicontrols.EveLabelSmall(parent=self.sr.footer, state=uiconst.UI_NORMAL, top=7)
        btns = [(localization.GetByLabel('UI/PI/Common/CustomsOfficeTransfer'),
          self.ConfirmCommodityTransfer,
          (),
          None)]
        btns = uicontrols.ButtonGroup(btns=btns, parent=self.sr.footer, line=0, align=uiconst.TOPRIGHT)
        self.transferBtn = btns.GetBtnByIdx(0)
        self.__OnResizeUpdate()
        self.sr.customsListScroll = uicontrols.Scroll(parent=self.sr.customsList, name='customsList')
        self.sr.spaceportListScroll = uicontrols.Scroll(parent=self.sr.spaceportList, name='spaceportList')

    def ResetContents(self):
        self.LoadDestComboOptions()
        self.SetCustomsOfficeContent()
        self.SetSpaceportContent()
        self.importContents = {}
        self.exportContents = {}
        self.UpdateTaxRate()
        self.RefreshLists()

    def RefreshLists(self, *args):
        self.LoadContentToScroll(self.customsOfficeContents, self.exportContents, self.sr.customsListScroll, self.OnCustomsScrollDropData)
        self.LoadContentToScroll(self.spaceportContents, self.importContents, self.sr.spaceportListScroll, self.OnSpaceportScrollDropData)
        self.RefreshHeaderInfo()

    def GetSettingsMenu(self, *args):
        return [(localization.GetByLabel('UI/DustLink/ConfigureOrbital'), self.OpenConfiguration, ())]

    def OpenConfiguration(self):
        form.OrbitalConfigurationWindow.Open(orbitalItem=self.customsOffice.GetItem())

    def LoadDestComboOptions(self):
        colony = self.planet.GetColony(session.charid)
        if colony is None:
            self.sr.spaceportCombo.LoadOptions([(localization.GetByLabel('UI/PI/Common/NoDestinationsFound'), None)])
            return
        self.endpoints = colony.GetImportEndpoints()
        if len(self.endpoints) < 1:
            self.sr.spaceportCombo.LoadOptions([(localization.GetByLabel('UI/PI/Common/NoDestinationsFound'), None)])
            return
        options = []
        for endpoint in self.endpoints:
            pin = self.planet.GetPin(endpoint.id)
            options.append((planetCommon.GetGenericPinName(pin.typeID, pin.id), endpoint.id))

        if self.spaceportPinID is None:
            self.spaceportPinID = options[0][1]
        self.sr.spaceportCombo.LoadOptions(options, select=self.spaceportPinID)

    def SetCustomsOfficeContent(self):
        self.customsOfficeContents = {}
        for item in self.customsOffice.List(const.flagHangar):
            if item.flagID != const.flagHangar:
                continue
            if item.ownerID != session.charid:
                continue
            self.customsOfficeContents[item.itemID, item.typeID] = util.KeyVal(itemID=item.itemID, typeID=item.typeID, quantity=item.stacksize, name=cfg.invtypes.Get(item.typeID).name, item=getattr(item, 'item', item))

    def SetSpaceportContent(self):
        self.spaceportContents = {}
        if self.spaceportPinID is None:
            return
        if self.planet.GetColony(session.charid) is None:
            log.LogWarn('Unable to update spaceport contents, colony not yet loaded')
            return
        pin = self.planet.GetPin(self.spaceportPinID)
        if pin is None:
            raise UserError('CannotImportEndpointNotFound')
        for typeID, qty in pin.GetContents().iteritems():
            name = cfg.invtypes.Get(typeID).name
            self.spaceportContents[None, typeID] = util.KeyVal(itemID=None, typeID=typeID, quantity=qty, name=name)

    def LoadContentToScroll(self, contentList, transferList, scroll, onDropDataCallback):
        scroll.sr.content.OnDropData = onDropDataCallback
        scrollHeaders = ['', localization.GetByLabel('UI/Common/Commodity'), localization.GetByLabel('UI/Common/Quantity')]
        scrollContents = []
        scrollNoContentText = localization.GetByLabel('UI/PI/Common/NoItemsFound')
        for item in contentList.values():
            data = util.KeyVal()
            data.label = '<t>%s<t>%d' % (item.name, item.quantity)
            data.quantity = item.quantity
            data.typeID = item.typeID
            data.itemID = item.itemID
            data.getIcon = 1
            data.hint = item.name
            data.item = getattr(item, 'item', None)
            data.isItemTransfer = (item.itemID, item.typeID) in transferList
            data.OnDropData = onDropDataCallback
            scrollContents.append(listentry.Get('CustomsItem', data=data))

        sortBy = scroll.GetSortBy()
        if sortBy is None:
            sortBy = localization.GetByLabel('UI/Common/Commodity')
        scroll.LoadContent(contentList=scrollContents, headers=scrollHeaders, noContentHint=scrollNoContentText, sortby=sortBy)
        scroll.RefreshSort()

    def GetCommodityVolume(self, commodities = None, excluded = None):
        volume = 0
        for key, item in commodities.iteritems():
            if excluded is None or key not in excluded:
                volume += GetTypeVolume(key[1], item.quantity)

        return volume

    def GetCustomsCapacityUsed(self):
        capacity = self.customsOffice.GetCapacity().used
        for item in self.exportContents.values():
            capacity += GetTypeVolume(item.typeID, item.quantity)

        return capacity

    def GetCustomsCapacityTotal(self):
        return self.customsOffice.GetCapacity().capacity

    def GetCustomsCapacityAvailable(self):
        used = self.GetCustomsCapacityUsed()
        capacity = self.GetCustomsCapacityTotal()
        return capacity - used

    def CheckAvailableSpaceInCustoms(self, commodities = None):
        available = self.GetCustomsCapacityAvailable()
        required = self.GetCommodityVolume(commodities, self.importContents)
        if required - available > 1e-05:
            raise UserError('NotEnoughSpace', {'volume': required,
             'available': available})

    def GetSpaceportCapacityUsed(self):
        pin = self.planet.GetPin(self.spaceportPinID)
        if not pin:
            return 0
        capacity = pin.capacityUsed
        for item in self.importContents.values():
            capacity += GetTypeVolume(item.typeID, item.quantity)

        return capacity

    def GetSpaceportCapacityTotal(self):
        pin = self.planet.GetPin(self.spaceportPinID)
        if not pin:
            return 0
        return pin.GetCapacity()

    def IsItemHere(self, item):
        return item.itemID == self.customsOfficeID

    def GetSpaceportCapacityAvailable(self):
        used = self.GetSpaceportCapacityUsed()
        capacity = self.GetSpaceportCapacityTotal()
        return capacity - used

    def CheckAvailableSpaceInSpaceport(self, commodities = None):
        available = self.GetSpaceportCapacityAvailable()
        required = self.GetCommodityVolume(commodities, self.exportContents)
        if required - available > 1e-05:
            raise UserError('NotEnoughSpace', {'volume': required,
             'available': available})

    def RefreshHeaderInfo(self):
        self.sr.spaceportGauge.state = uiconst.UI_HIDDEN
        if self.spaceportPinID is not None:
            pin = self.planet.GetPin(self.spaceportPinID)
            if not pin:
                return
            capacityUsed = self.GetSpaceportCapacityUsed()
            capacityMax = self.GetSpaceportCapacityTotal()
            self.sr.spaceportGauge.state = uiconst.UI_DISABLED
            self.sr.spaceportGauge.SetSubText(localization.GetByLabel('UI/PI/Common/StorageUsed', capacityUsed=capacityUsed, capacityMax=capacityMax))
            self.sr.spaceportGauge.SetValue(capacityUsed / capacityMax)
        self.sr.customsGauge.state = uiconst.UI_HIDDEN
        if self.customsOffice is not None:
            capacityUsed = self.GetCustomsCapacityUsed()
            capacityMax = self.GetCustomsCapacityTotal()
            self.sr.customsGauge.state = uiconst.UI_DISABLED
            self.sr.customsGauge.SetSubText(localization.GetByLabel('UI/PI/Common/StorageUsed', capacityUsed=capacityUsed, capacityMax=capacityMax))
            self.sr.customsGauge.SetValue(capacityUsed / capacityMax)
        self.RefreshCostText()

    def GetCommodities(self, source):
        commods = {}
        for itemVoucher in source.itervalues():
            if itemVoucher.typeID not in commods:
                commods[itemVoucher.typeID] = itemVoucher.quantity
            else:
                commods[itemVoucher.typeID] += itemVoucher.quantity

        return commods

    def GetCost(self):
        cost = None
        pin = self.planet.GetPin(self.spaceportPinID)
        if pin is not None and self.taxRate is not None:
            cost = pin.GetExportTax(self.GetCommodities(self.exportContents), self.taxRate)
            cost += pin.GetImportTax(self.GetCommodities(self.importContents), self.taxRate)
        return cost

    def RefreshCostText(self):
        cost = self.GetCost()
        if cost is not None:
            costStr = util.FmtISK(cost)
            if cost > 0:
                costStr = '<color=red>%s</color>' % costStr
            self.sr.transferCostLabel.text = localization.GetByLabel('UI/PI/Common/TransferCost', iskAmount=costStr)
        if self.taxRate is not None:
            self.windowCaption.SetSubcaption(localization.GetByLabel('UI/PI/Common/CustomsOfficeTaxRate', taxRate=self.taxRate * 100))
        else:
            self.windowCaption.SetSubcaption(localization.GetByLabel('UI/PI/Common/CustomsOfficeAccessDenied'))

    def UpdateTaxRate(self):
        self.taxRate = moniker.GetPlanetOrbitalRegistry(session.solarsystemid).GetTaxRate(self.id)
        self.RefreshCostText()

    def OnSpaceportComboChanged(self, comboItem, spaceportName, spaceportPinID, *args):
        if self.spaceportPinID != spaceportPinID:
            self.spaceportPinID = spaceportPinID
            self.ResetContents()

    def OnItemChange(self, item = None, change = None):
        """ Some of my items have changed. If the item is/was in the cargo link, then reset """
        locationIdx = const.ixLocationID
        if self.id not in (item[locationIdx], change.get(locationIdx, 'No location change')):
            return
        self.ResetContents()

    def OnRefreshPins(self, pinIDs):
        if not self or self.destroyed:
            return
        if self.spaceportPinID in pinIDs:
            self.ResetContents()

    def OnPlanetPinsChanged(self, planetID):
        """ Some pins have changed. If it's on the planet I'm importing/exporting from, 
        then reset """
        if self.planet.planetID == planetID:
            for endpoint in self.endpoints:
                if not self.planet.GetPin(endpoint.id):
                    self.CloseByUser()
                    return

            self.ResetContents()

    def OnResizeUpdate(self, *args):
        if not self or self.destroyed:
            return
        uthread.new(self.__OnResizeUpdate)

    def __OnResizeUpdate(self):
        if not self.sr.leftColumn:
            return
        width, height = self.GetAbsoluteSize()
        desiredWidth = (width - 25) / 2
        self.sr.leftColumn.width = desiredWidth
        self.sr.rightColumn.width = desiredWidth

    def OnCustomsScrollDropData(self, dragObj, nodes, *args):
        """ This drop handler accepts dropping items from either the spaceport on the right
        or any inventory within range. Dropping from the spaceport is a pending transfer
        until confirmed due to the cost. Other item swaps happen immediately. """
        scroll = nodes[0].scroll
        if not scroll:
            return
        if scroll.name == 'spaceportList':
            self.ExportCommodity(nodes)
        elif scroll.name != 'customsList':
            self.MoveFromInventory(nodes)

    def OnSpaceportScrollDropData(self, dragObj, nodes, *args):
        """ You can only drop items onto the spaceport panel if it came directly from the
        customs office cargo hold. (the left panel on this UI) """
        scroll = nodes[0].scroll
        if not scroll:
            return
        if scroll.name == 'customsList':
            self.ImportCommodity(nodes)
        else:
            raise UserError('CannotDropItemsOntoSpaceport')

    def ImportCommodity(self, nodes):
        """ Importing goes from the customs office to the planet """
        if not self.spaceportPinID:
            raise UserError('NoSpaceportsAvailable')
        if self.taxRate is None:
            raise UserError('PortStandingCheckFail', {'corpName': (const.UE_OWNERID, self.customsOfficeItem.ownerID)})
        items = self.CommoditiesToTransfer(nodes, toSpaceport=True)
        for key, item in items.iteritems():
            self.RemoveStuff(key, item, self.customsOfficeContents)
            self.AddStuff(key, item, self.spaceportContents)
            if key in self.exportContents:
                self.RemoveStuff(key, item, self.exportContents)
            else:
                self.AddStuff(key, item, self.importContents)

        self.RefreshLists()

    def ExportCommodity(self, nodes):
        """ Exporting goes from the planet to the customs office """
        if self.taxRate is None:
            raise UserError('PortStandingCheckFail', {'corpName': (const.UE_OWNERID, self.customsOfficeItem.ownerID)})
        items = self.CommoditiesToTransfer(nodes)
        for key, item in items.iteritems():
            self.RemoveStuff(key, item, self.spaceportContents)
            self.AddStuff(key, item, self.customsOfficeContents)
            if key in self.importContents:
                self.RemoveStuff(key, item, self.importContents)
            else:
                self.AddStuff(key, item, self.exportContents)

        self.RefreshLists()

    def CommoditiesToTransfer(self, commodities, toSpaceport = False):
        """ Returns a dictionary of the items and quanities we wish to transfer from a drag 
        and drop. Checks for shift drag and adjusts quantities. Raises an exception if the
        commodities won't fit in the destination. """
        toMove = {}
        for item in commodities:
            toMove[item.itemID, item.typeID] = util.KeyVal(name=cfg.invtypes.Get(item.typeID).name, itemID=item.itemID, typeID=item.typeID, quantity=item.quantity, item=getattr(item, 'item', item))

        if len(commodities) == 1:
            if toSpaceport:
                available = self.GetSpaceportCapacityAvailable()
                required = self.GetCommodityVolume(toMove, self.exportContents)
            else:
                available = self.GetCustomsCapacityAvailable()
                required = self.GetCommodityVolume(toMove, self.importContents)
            if required > 0 and uicore.uilib.Key(uiconst.VK_SHIFT) or required - available > 1e-05:
                selectedItem = commodities[0]
                itemID = selectedItem.itemID
                typeID = selectedItem.typeID
                typeName = cfg.invtypes.Get(typeID).name
                availableQuantity = min(selectedItem.quantity, int(available / required * selectedItem.quantity))
                if availableQuantity > 0:
                    ret = uix.QtyPopup(availableQuantity, 1, availableQuantity, None, localization.GetByLabel('UI/PI/Common/QuantityToTransfer', typeName=typeName))
                    if ret and 'qty' in ret:
                        toMove[itemID, typeID].quantity = min(availableQuantity, max(1, ret['qty']))
                    else:
                        toMove = {}
        if toSpaceport:
            self.CheckAvailableSpaceInSpaceport(toMove)
        else:
            self.CheckAvailableSpaceInCustoms(toMove)
        return toMove

    def AddStuff(self, key, item, toDict):
        if key not in toDict:
            toDict[key] = util.KeyVal(itemID=item.itemID, typeID=item.typeID, quantity=item.quantity, name=item.name, item=item.item)
        else:
            toDict[key].quantity += item.quantity

    def RemoveStuff(self, key, item, fromDict):
        if key in fromDict:
            fromDict[key].quantity -= item.quantity
            if fromDict[key].quantity <= 0:
                del fromDict[key]

    def MoveFromInventory(self, nodes):
        """ Performs an immediate inventory move between some container such as your ship 
        cargo and the Customs Office. This move has no cost and should be done without 
        the need for confirmation. """
        allowableSources = ('xtriui.InvItem', 'listentry.InvItem')
        items = [ item for item in nodes if item.Get('__guid__', None) in allowableSources ]
        if len(items) > 0:
            sourceLocation = items[0].rec.locationID
            items = self.CommoditiesToTransfer([ item.item for item in items ])
            for key, item in items.iteritems():
                self.customsOffice.Add(key[0], sourceLocation, qty=item.quantity)

    def ConfirmCommodityTransfer(self, *args):
        """ Takes the pending import / export commodities and confirms the transfer,
        deducting relevant taxes. """
        if self.spaceportPinID is None:
            raise UserError('CannotImportEndpointNotFound')
        planet = sm.GetService('planetUI').GetCurrentPlanet()
        if planet is not None and planet.IsInEditMode():
            raise UserError('CannotImportExportInEditMode')
        if len(self.importContents) + len(self.exportContents) < 1:
            raise UserError('PleaseSelectCommoditiesToImport')
        importData = {key[0]:value.quantity for key, value in self.importContents.iteritems()}
        exportData = {key[1]:value.quantity for key, value in self.exportContents.iteritems()}
        try:
            customsOfficeInventory = sm.GetService('invCache').GetInventoryFromId(self.customsOfficeID)
            customsOfficeInventory.ImportExportWithPlanet(self.spaceportPinID, importData, exportData, self.taxRate)
        except UserError as e:
            if e.msg != 'TaxChanged':
                raise
            self.UpdateTaxRate()
            if self.taxRate is None:
                self.ResetContents()
                raise UserError('PortStandingCheckFail', {'corpName': (const.UE_OWNERID, self.customsOfficeItem.ownerID)})
            if eve.Message('CustomsOfficeTaxRateChanged', {'cost': self.GetCost()}, uiconst.YESNO) == uiconst.ID_YES:
                customsOfficeInventory.ImportExportWithPlanet(self.spaceportPinID, importData, exportData, self.taxRate)
            else:
                self.ResetContents()
