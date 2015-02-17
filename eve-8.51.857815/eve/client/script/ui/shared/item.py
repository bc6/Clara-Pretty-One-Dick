#Embedded file name: eve/client/script/ui/shared\item.py
from carbonui.control.scrollentries import SE_BaseClassCore, OPACITY_IDLE
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay
from eve.client.script.ui.services.menuSvcExtras.menuFunctions import ActivatePlex, ActivateMultiTraining, ActivateCharacterReSculpt
from eve.client.script.ui.shared.market.sellMulti import SellItems
from eve.common.script.util import industryCommon
from inventorycommon.util import GetItemVolume, IsShipFittingFlag
import uicontrols
import uiprimitives
import uix
import uiutil
import util
import carbonui.const as uiconst
import log
import localization
import invCtrl
import telemetry
import const
from eve.client.script.ui.station.fitting.base_fitting import FittingWindow
from eve.client.script.ui.shared.inventory.invWindow import Inventory as InventoryWindow
from eve.client.script.ui.shared.industry.industryWnd import Industry

class InvItem(uicontrols.SE_BaseClassCore):
    __guid__ = 'xtriui.InvItem'
    __groups__ = []
    __categories__ = []
    __notifyevents__ = ['ProcessActiveShipChanged',
     'OnSessionChanged',
     'OnLockedItemChangeUI',
     'OnInvClipboardChanged']
    default_name = 'InvItem'
    default_left = 64
    default_top = 160
    default_width = 64
    default_height = 92
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    isDragObject = True
    highlightable = True

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        uicontrols.SE_BaseClassCore.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.ConstructLayout()
        self.typeID = None
        self.subTypeID = None
        self.id = None
        self.powerType = None
        self.sr.node = None
        self.sr.tlicon = None
        self.rec = None
        self.activeShipHighlite = None
        self.blinkBG = None
        self.lockedIcon = None
        self.darkenedBG = None

    @staticmethod
    def GetInvItemHeight():
        """ Returns the height to use for this entry, based on language font size settings """
        return 64 + uicore.fontSizeFactor * 30

    def ConstructLayout(self):
        self.sr.mainCont = mainCont = uiprimitives.Container(name='mainCont', parent=self)
        self.iconCont = uiprimitives.Container(name='iconCont', align=uiconst.TOTOP, parent=mainCont, height=self.width)
        self.sr.label = uicontrols.Label(parent=mainCont, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, lineSpacing=-0.2, maxLines=2)

    def OnInvClipboardChanged(self):
        if self.sr.node and sm.GetService('inv').IsOnClipboard(self.sr.node.item.itemID):
            self.opacity = 0.2
        else:
            self.opacity = 1.0

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        if not self.destroyed and self.sr and self.sr.node:
            self.Load(self.sr.node)

    def OnSessionChanged(self, isRemote, session, change):
        if not self.destroyed and self.sr and self.sr.node:
            if 'shipid' in change and getattr(self, 'isShip', 0) and self and not self.destroyed:
                self.Load(self.sr.node)

    def OnLockedItemChangeUI(self, itemID, ownerID, locationID, change):
        if not self.destroyed and self.sr.node:
            if itemID == self.id:
                item = None
                if self.rec:
                    item = self.rec
                elif self.sr.node.item:
                    item = self.sr.node.item
                if item is None:
                    log.LogInfo('Lock issue item is None')
                else:
                    locked = item.flagID == const.flagLocked or sm.GetService('corp').IsItemLocked(item)
                    log.LogInfo('Locked:', locked, 'item:', item)
                    self.SetLockState(locked)

    def SetState(self, state):
        self.viewOnly = state
        if self.sr.node:
            self.sr.node.viewOnly = state

    def SetLockState(self, locked):
        self.SetState(min(1, locked))
        if not self.sr.icon:
            return
        if self.viewOnly:
            self.sr.icon.opacity = 0.25
            self.ConstructLockedIcon()
            self.lockedIcon.Show()
            self.darkenedBG.Show()
        else:
            self.sr.icon.opacity = 1.0
            if self.lockedIcon:
                self.lockedIcon.Hide()
            if self.darkenedBG:
                self.darkenedBG.Hide()

    def ConstructLockedIcon(self):
        if not self.lockedIcon:
            self.lockedIcon = uiprimitives.Sprite(name='lockedIcon', parent=self.iconCont, texturePath='res:/UI/Texture/classes/Inventory/locked.png', align=uiconst.TOPRIGHT, pos=(0, 0, 13, 14), idx=0, hint=localization.GetByLabel('UI/Inventory/ItemLocked'))
        if not self.darkenedBG:
            self.darkenedBG = uiprimitives.Sprite(name='darkenedBG', parent=self.iconCont, texturePath='res:/UI/Texture/classes/Inventory/darken.png', state=uiconst.UI_DISABLED, align=uiconst.TOALL, opacity=0.3, padding=-1, idx=1)

    def Reset(self):
        self.viewOnly = 0
        self.subTypeID = None

    def PreLoad(node):
        if node.viewMode in ('list', 'details'):
            label = uix.GetItemLabel(node.item, node)

    def LoadMainIcon(self):
        if self.sr.node.viewMode == 'list':
            return
        if not self.sr.icon:
            uiprimitives.Sprite(bgParent=self.iconCont, name='background', texturePath='res:/UI/Texture/classes/InvItem/bgNormal.png')
            self.sr.icon = uicontrols.Icon(parent=self.iconCont, name='icon', align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        self.sr.icon.LoadIconByTypeID(typeID=self.rec.typeID, ignoreSize=True, isCopy=self.sr.node.isBlueprint and self.sr.node.isCopy)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.sr.node.__guid__ = self.__guid__
        self.sr.node.itemID = node.item.itemID
        self.id = node.item.itemID
        self.rec = node.item
        self.typeID = node.item.typeID
        self.isShip = self.rec.categoryID == const.categoryShip and self.rec.singleton
        self.isUnassembledShip = self.rec.categoryID == const.categoryShip and not self.rec.singleton
        self.isStation = self.rec.categoryID == const.categoryStation and self.rec.groupID == const.groupStation
        self.isContainer = self.rec.groupID in (const.groupWreck,
         const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer) and self.rec.singleton
        self.isUnassembledContainer = self.rec.groupID in (const.groupWreck,
         const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer) and not self.rec.singleton
        self.isHardware = node.invtype.Group().Category().IsHardware()
        self.sr.node.isBlueprint = node.invtype.Group().categoryID == const.categoryBlueprint
        if self.sr.node.isBlueprint:
            self.sr.node.isCopy = self.sr.node.isBlueprint and self.rec.singleton == const.singletonBlueprintCopy
        if self.sr.node is None:
            return
        self.Reset()
        self.name = uix.GetItemName(node.item, self.sr.node)
        self.quantity = self.rec.stacksize
        listFlag = self.sr.node.viewMode in ('list', 'details')
        if util.GetActiveShip() == self.sr.node.item.itemID:
            if self.activeShipHighlite is None:
                if listFlag:
                    padding = (0, 1, 0, 1)
                else:
                    padding = -3
                self.activeShipHighlite = uiprimitives.Container(name='activeShipHighlite', parent=self, idx=-1)
                uicontrols.Frame(texturePath='res:/UI/Texture/Classes/InvItem/bgSelected.png', color=util.Color.GREEN, parent=self.activeShipHighlite, padding=padding)
                uicontrols.Frame(parent=self.activeShipHighlite, color=util.Color.GREEN, padding=padding, opacity=0.4)
        elif self.activeShipHighlite:
            self.activeShipHighlite.Close()
            self.activeShipHighlite = None
        if self.sr.node.Get('selected', 0):
            self.Select(animate=False)
        else:
            self.Deselect(animate=False)
        attribs = node.Get('godmaattribs', {})
        self.powerType = None
        for icon in (self.sr.ammosize_icon, self.sr.slotsize_icon, self.sr.contraband_icon):
            if icon:
                icon.Hide()

        if self.isHardware:
            if self.sr.node.viewMode != 'list':
                if attribs.has_key(const.attributeChargeSize):
                    self.ConstructAmmoSizeIcon()
                    self.sr.ammosize_icon.rectLeft = [0,
                     16,
                     32,
                     48,
                     64][int(attribs[const.attributeChargeSize]) - 1]
                elif attribs.has_key(const.attributeRigSize):
                    self.ConstructAmmoSizeIcon()
                    self.sr.ammosize_icon.rectLeft = [0,
                     16,
                     32,
                     48,
                     64][int(attribs[const.attributeRigSize]) - 1]
            for effect in cfg.dgmtypeeffects.get(self.rec.typeID, []):
                if effect.effectID in (const.effectRigSlot,
                 const.effectHiPower,
                 const.effectMedPower,
                 const.effectLoPower):
                    if self.sr.node.viewMode != 'list':
                        effinfo = cfg.dgmeffects.Get(effect.effectID)
                        iconNo = {const.effectRigSlot: 'ui_38_16_124',
                         const.effectHiPower: 'ui_38_16_123',
                         const.effectMedPower: 'ui_38_16_122',
                         const.effectLoPower: 'ui_38_16_121'}[effect.effectID]
                        self.ConstructSlotSizeIcon()
                        self.sr.slotsize_icon.LoadIcon(iconNo, ignoreSize=True)
                    self.powerType = effect.effectID
                    continue
                if self.sr.node.viewMode != 'list' and effect.effectID == const.effectSubSystem and const.attributeSubSystemSlot in attribs:
                    subsystemFlag = attribs.get(const.attributeSubSystemSlot, None)
                    iconNo = 'ui_38_16_42'
                    self.ConstructSlotSizeIcon()
                    self.sr.slotsize_icon.LoadIcon(iconNo, ignoreSize=True)

        elif self.rec.groupID == const.groupVoucher:
            if self.rec.typeID != const.typeBookmark:
                self.subTypeID = self.sr.node.voucher.GetTypeInfo()[1]
        elif self.rec.categoryID == const.categoryCharge and attribs.has_key(const.attributeChargeSize):
            self.ConstructAmmoSizeIcon()
            self.sr.ammosize_icon.rectLeft = [0,
             16,
             32,
             48,
             64][int(attribs[const.attributeChargeSize]) - 1]
        if 0 < len(self.sr.node.invtype.Illegality()) and self.sr.node.invtype.Illegality().get(sm.GetService('map').GetItem(eve.session.solarsystemid2).factionID, None) is not None:
            self.ConstructContrabandIcon()
        if listFlag:
            self.sr.label.width = uicore.desktop.width
        if self.sr.node.viewMode == 'icons':
            self.LoadMainIcon()
        self.UpdateLabel()
        self.LoadTechLevelIcon(node.item.typeID)
        locked = node.Get('locked', 0)
        viewOnly = node.Get('viewOnly', 0)
        self.SetLockState(locked)
        if not locked:
            self.SetState(viewOnly)
        if self.isStation:
            self.DisableDrag()
        self.OnInvClipboardChanged()

    def ConstructFlagsCont(self):
        if self.sr.flags is None:
            if self.sr.node.viewMode == 'details':
                self.sr.flags = uiprimitives.Container(parent=self, idx=0, name='flags', pos=(5, 20, 32, 16), align=uiconst.TOPLEFT, state=uiconst.UI_PICKCHILDREN)
            elif self.sr.node.viewMode == 'icons':
                self.sr.flags = uiprimitives.Container(parent=self, idx=0, name='flags', pos=(0, 37, 32, 16), align=uiconst.TOPRIGHT, state=uiconst.UI_PICKCHILDREN)

    def ConstructSlotSizeIcon(self):
        self.ConstructFlagsCont()
        if not self.sr.slotsize_icon:
            self.sr.slotsize_icon = uicontrols.Icon(parent=self.sr.flags, name='slotSize', pos=(0, 0, 16, 16), align=uiconst.TORIGHT, hint=localization.GetByLabel('UI/Inventory/FittingConstraint'))
        self.sr.slotsize_icon.state = uiconst.UI_DISABLED

    def ConstructAmmoSizeIcon(self):
        self.ConstructFlagsCont()
        if not self.sr.ammosize_icon:
            self.sr.ammosize_icon = uiprimitives.Sprite(parent=self.sr.flags, name='ammoSize', pos=(0, 0, 16, 16), rectWidth=16, rectHeight=16, align=uiconst.TORIGHT, texturePath='res:/UI/Texture/classes/InvItem/ammoSize.png', hint=localization.GetByLabel('UI/Inventory/AmmoSizeConstraint'))
        self.sr.ammosize_icon.state = uiconst.UI_DISABLED

    def ConstructContrabandIcon(self):
        self.ConstructFlagsCont()
        if not self.sr.contraband_icon:
            self.sr.contraband_icon = uiprimitives.Sprite(parent=self.sr.flags, name='contrabandIcon', pos=(0, 0, 16, 16), align=uiconst.TORIGHT, texturePath='res:/UI/Texture/classes/InvItem/contrabandIcon.png', hint=localization.GetByLabel('UI/Inventory/ItemIsContraband'))
        self.sr.contraband_icon.state = uiconst.UI_DISABLED

    def LoadTechLevelIcon(self, typeID = None):
        tlicon = uix.GetTechLevelIcon(self.sr.tlicon, 0, typeID)
        if tlicon is not None and util.GetAttrs(tlicon, 'parent') is None:
            self.sr.tlicon = tlicon
            tlicon.SetParent(self, 0)

    def UpdateLabel(self, new = 0):
        label = uix.GetItemLabel(self.rec, self.sr.node, new)
        if self.sr.node.viewMode in ('list', 'details'):
            self.sr.label.text = label
            return
        self.sr.label.text = label
        quantity = uix.GetItemQty(self.sr.node, 'ss')
        if self.rec.singleton or self.rec.typeID in (const.typeBookmark,):
            if self.sr.qtypar:
                self.sr.qtypar.Close()
                self.sr.qtypar = None
            return
        if not self.sr.qtypar:
            self.sr.qtypar = uiprimitives.Container(parent=self, idx=0, name='qtypar', pos=(0, 53, 32, 11), align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED, bgColor=(0, 0, 0, 0.95))
            self.sr.quantity_label = uicontrols.Label(parent=self.sr.qtypar, left=2, maxLines=1, fontsize=9)
        self.sr.quantity_label.text = quantity

    def GetMenu(self):
        if self.sr.node:
            containerMenu = []
            if hasattr(self.sr.node.scroll.sr.content, 'GetMenu'):
                containerMenu = self.sr.node.scroll.sr.content.GetMenu()
            selected = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
            args = []
            for node in selected:
                if node.item:
                    args.append((node.item, node.Get('viewOnly', 0), node.Get('voucher', None)))

            return sm.GetService('menu').InvItemMenu(args) + [None] + containerMenu
        else:
            return sm.GetService('menu').InvItemMenu(self.rec, self.viewOnly)

    def GetHeight(self, *args):
        node, width = args
        if node.viewMode in ('details', 'assets'):
            node.height = 42
        else:
            node.height = 21
        return node.height

    def OnClick(self, *args):
        if self.sr.node:
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)
            else:
                self.sr.node.scroll.SelectNode(self.sr.node)
                eve.Message('ListEntryClick')

    def OnMouseEnter(self, *args):
        if uicore.uilib.leftbtn:
            return
        SE_BaseClassCore.OnMouseEnter(self, *args)
        self.sr.hint = ''
        wnd = FittingWindow.GetIfOpen()
        if wnd is not None:
            if getattr(self, 'rec', None):
                wnd.HiliteFitting(self.rec)
        if self.sr.node and self.sr.node.viewMode == 'icons':
            self.sr.hint = '%s%s' % ([uix.GetItemQty(self.sr.node, 'ln') + ' - ', ''][bool(self.rec.singleton)], uix.GetItemName(self.sr.node.item, self.sr.node))

    def GetHint(self, *args):
        if not self.sr.node:
            return
        ret = uix.GetItemName(self.sr.node.item, self.sr.node)
        if self.rec.stacksize > 1:
            quantity = uix.GetItemQty(self.sr.node, 'ln')
            ret = localization.GetByLabel('UI/Inventory/QuantityAndName', quantity=quantity, name=ret)
        marketPrice = util.GetAveragePrice(self.rec)
        if marketPrice is None:
            marketPriceStr = localization.GetByLabel('UI/Inventory/PriceUnavailable')
        else:
            marketPriceStr = util.FmtISKAndRound(marketPrice)
        ret += '<br>' + localization.GetByLabel('UI/Inventory/ItemEstimatedPrice', estPrice=marketPriceStr)
        if self.rec.stacksize > 1 and marketPrice:
            ret += '<br>' + localization.GetByLabel('UI/Inventory/ItemEstimatedPriceStack', estPrice=util.FmtISKAndRound(marketPrice * self.rec.stacksize))
        return ret

    def ConstructHiliteFill(self):
        if not self._hiliteFill:
            self._hiliteFill = FillUnderlay(bgParent=self, colorType=uiconst.COLORTYPE_UIHILIGHT, opacity=OPACITY_IDLE, padding=(-5, -4, -5, -6))

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        if getattr(self, 'Draggable_dragging', 0):
            return
        wnd = FittingWindow.GetIfOpen()
        if wnd is not None:
            wnd.HiliteFitting(None)

    def OnDblClick(self, *args):
        if self.sr.node and self.sr.node.Get('OnDblClick', None):
            self.sr.node.OnDblClick(self)
        elif self.isContainer and not self.rec.flagID == const.flagCorpMarket:
            self.OpenContainer()
        elif not self.viewOnly:
            if industryCommon.IsBlueprintCategory(self.rec.categoryID):
                Industry.OpenOrShowBlueprint(blueprintID=self.sr.node.itemID)
            elif self.typeID == const.typePilotLicence:
                ActivatePlex(self.rec.itemID)
            elif self.typeID == const.typeReSculptToken:
                ActivateCharacterReSculpt(self.rec.itemID)
            elif self.typeID == const.typeMultiTrainingToken:
                ActivateMultiTraining(self.rec.itemID)
            elif not sm.GetService('menu').CheckSameLocation(self.rec):
                return
            if self.isShip and session.stationid:
                sm.StartService('station').TryActivateShip(self.rec)
            elif self.isUnassembledShip:
                sm.GetService('menu').AssembleShip([self.rec])
            elif self.isUnassembledContainer:
                sm.GetService('menu').AssembleContainer([self.rec])

    def OnMouseDown(self, *args):
        if getattr(self, 'powerType', None):
            wnd = FittingWindow.GetIfOpen()
            if wnd is not None:
                wnd.HiliteFitting(self.rec)
        uicontrols.SE_BaseClassCore.OnMouseDown(self, *args)

    def GetDragData(self, *args):
        if not self.sr.node:
            return None
        nodes = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        for node in nodes:
            if not getattr(node, 'viewOnly', False):
                return nodes

    def OnEndDrag(self, dragSource, dropLocation, dragData):
        if self is dragSource:
            wnd = SellItems.GetIfOpen()
            if dropLocation.IsUnder(wnd) or dropLocation is wnd:
                wnd.DropItems(None, dragData)

    def OnMouseUp(self, btn, *args):
        if uicore.uilib.mouseOver != self:
            if getattr(self, 'powerType', None):
                main = sm.GetService('station').GetSvc('fitting')
                if main is not None:
                    main.Hilite(None)
        uicontrols.SE_BaseClassCore.OnMouseUp(self, btn, *args)

    def OpenShipCargo(self):
        if not self.rec.ownerID == eve.session.charid:
            eve.Message('CantDoThatWithSomeoneElsesStuff')
            return
        if not sm.StartService('menu').CheckSameStation(self.rec):
            return
        if session.stationid2:
            if self.rec.groupID == const.groupCapsule:
                if eve.Message('AskActivateShip', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
                    sm.GetService('station').SelectShipDlg()
                return
        wnd = uiutil.GetWindowAbove(self)
        InventoryWindow.OpenOrShow(invID=('ShipCargo', self.rec.itemID), openFromWnd=wnd)

    def OpenContainer(self):
        if self.rec.ownerID not in (eve.session.charid, eve.session.corpid):
            eve.Message('CantDoThatWithSomeoneElsesStuff')
            return
        wnd = uiutil.GetWindowAbove(self)
        if self.rec.typeID == const.typePlasticWrap:
            InventoryWindow.OpenOrShow(invID=('StationContainer', self.rec.itemID), openFromWnd=wnd)
        elif sm.StartService('menu').CheckSameLocation(self.rec):
            invID = ('StationContainer', self.rec.itemID)
            InventoryWindow.OpenOrShow(invID=invID, openFromWnd=wnd)
        else:
            location = self.rec.locationID
            if not session.stationid or util.IsStation(location) and location != session.stationid:
                log.LogInfo('Trying to open a container in', location, 'while actor is in', session.stationid)
                return
            inventory = sm.GetService('invCache').GetInventoryFromId(location)
            if not inventory:
                return
            item = inventory.GetItem()
            if not item:
                return
            category = getattr(item, 'categoryID', None)
            if category == const.categoryShip and item.locationID == session.stationid:
                InventoryWindow.OpenOrShow(invID=('StationContainer', self.rec.itemID), openFromWnd=wnd)

    def OnDragEnter(self, dragObj, nodes):
        if self.sr.node.container:
            self.sr.node.container.OnDragEnter(dragObj, nodes)
        if not nodes or not getattr(nodes[0], 'rec', None):
            return
        isStackable = False
        if not self.rec.singleton:
            for node in nodes:
                if not getattr(node.rec, 'singleton', False) and node.rec.typeID == self.rec.typeID and node.rec.itemID != self.rec.itemID:
                    isStackable = True
                    break

        if self.isContainer or self.isShip or isStackable:
            self.ConstructBlinkBG()
            uicore.animations.FadeIn(self.blinkBG, 0.3, duration=0.2)

    def OnDragExit(self, dragObj, nodes):
        if self.sr.node.container:
            self.sr.node.container.OnDragExit(dragObj, nodes)
        if self.blinkBG:
            uicore.animations.FadeOut(self.blinkBG, duration=0.2)

    def OnDropData(self, dragObj, nodes):
        if self.blinkBG:
            uicore.animations.FadeOut(self.blinkBG, duration=0.2)
        if len(nodes) and getattr(nodes[0], 'scroll', None):
            nodes[0].scroll.ClearSelection()
            if not nodes[0].rec:
                return
            if not hasattr(nodes[0].rec, 'locationID'):
                return
            locationID = nodes[0].rec.locationID
            if locationID != self.rec.locationID:
                if not sm.GetService('crimewatchSvc').CheckCanTakeItems(locationID):
                    sm.GetService('crimewatchSvc').SafetyActivated(const.shipSafetyLevelPartial)
                    return
        if self.isShip:
            if invCtrl.ShipCargo(self.rec.itemID).OnDropData(nodes):
                self.Blink()
            return
        if self.isContainer:
            if invCtrl.StationContainer(self.rec.itemID).OnDropData(nodes):
                self.Blink()
            return
        mergeToMe = []
        notUsed = []
        sourceID = None
        for node in nodes:
            if getattr(node, '__guid__', None) not in ('xtriui.ShipUIModule', 'xtriui.InvItem', 'listentry.InvItem'):
                notUsed.append(node)
                continue
            if node.item.itemID == self.sr.node.item.itemID:
                notUsed.append(node)
                continue
            if node.item.typeID == self.sr.node.item.typeID and not isinstance(self.sr.node.item.itemID, tuple) and not getattr(node.item, 'singleton', False) and not self.sr.node.item.singleton:
                mergeToMe.append(node.item)
            else:
                notUsed.append(node)
            if sourceID is None:
                sourceID = node.rec.locationID

        if sourceID is None:
            log.LogInfo('OnDropData: Moot operation with ', nodes)
            return
        if mergeToMe:
            containerItem = sm.GetService('invCache').GetInventoryFromId(self.rec.locationID).GetItem()
            if session.solarsystemid and containerItem.itemID == mergeToMe[0].locationID and containerItem.ownerID not in (session.charid, session.corpid, session.allianceid):
                return
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        mergeData = []
        stateMgr = sm.StartService('godma').GetStateManager()
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        singletons = []
        for invItem in mergeToMe:
            if invItem.stacksize == 1:
                quantity = 1
            elif shift:
                ret = uix.QtyPopup(invItem.stacksize, 1, 1, None, localization.GetByLabel('UI/Inventory/ItemActions/StackItems'))
                if ret is not None:
                    quantity = ret['qty']
                else:
                    quantity = None
            else:
                quantity = invItem.stacksize
            if not quantity:
                continue
            if invItem.categoryID == const.categoryCharge and IsShipFittingFlag(invItem.flagID):
                if type(invItem.itemID) is tuple:
                    flag = invItem.itemID[1]
                    chargeIDs = dogmaLocation.GetSubLocationsInBank(invItem.locationID, invItem.itemID)
                    if chargeIDs:
                        for chargeID in chargeIDs:
                            charge = dogmaLocation.dogmaItems[chargeID]
                            mergeData.append((charge.itemID,
                             self.rec.itemID,
                             dogmaLocation.GetAttributeValue(chargeID, const.attributeQuantity),
                             charge))

                    else:
                        mergeData.append((invItem.itemID,
                         self.rec.itemID,
                         quantity,
                         invItem))
                else:
                    crystalIDs = dogmaLocation.GetCrystalsInBank(invItem.locationID, invItem.itemID)
                    if crystalIDs:
                        for crystalID in crystalIDs:
                            crystal = dogmaLocation.GetItem(crystalID)
                            if crystal.singleton:
                                singletons.append(crystalID)
                            else:
                                mergeData.append((crystal.itemID,
                                 self.rec.itemID,
                                 crystal.stacksize,
                                 crystal))

                    else:
                        mergeData.append((invItem.itemID,
                         self.rec.itemID,
                         quantity,
                         invItem))
            else:
                mergeData.append((invItem.itemID,
                 self.rec.itemID,
                 quantity,
                 invItem))

        if singletons and util.GetAttrs(self, 'sr', 'node', 'rec', 'flagID'):
            flag = self.sr.node.rec.flagID
            inv = sm.GetService('invCache').GetInventoryFromId(self.rec.locationID)
            if inv:
                inv.MultiAdd(singletons, sourceID, flag=flag, fromManyFlags=True)
        if mergeData and util.GetAttrs(self, 'sr', 'node', 'container', 'invController', 'MultiMerge'):
            invController = self.sr.node.container.invController
            sm.ScatterEvent('OnInvContDragExit', invController.GetInvID(), [])
            if invController.MultiMerge(mergeData, sourceID):
                sm.GetService('audio').SendUIEvent('ui_state_stack')
                self.Blink()
        if notUsed and util.GetAttrs(self, 'sr', 'node', 'container', 'OnDropData'):
            self.sr.node.container.OnDropData(dragObj, notUsed)

    def Blink(self):
        self.ConstructBlinkBG()
        uicore.animations.FadeTo(self.blinkBG, 0.0, 1.0, duration=0.25, curveType=uiconst.ANIM_WAVE, loops=2)

    def ConstructBlinkBG(self):
        if self.blinkBG is None:
            self.blinkBG = uiprimitives.Sprite(name='blinkBg', parent=self.iconCont, align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/InvItem/bgSelected.png', opacity=0.0, idx=0)

    @classmethod
    def GetCopyData(cls, node):
        return node.label


class Item(InvItem):
    __guid__ = 'listentry.InvItem'

    def ConstructLayout(self):
        self.sr.label = uicontrols.EveLabelMedium(parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, idx=3, lineSpacing=-0.2, maxLines=1)
        container = uiprimitives.Container(parent=self, pos=(21, 20, 16, 16), name='container', state=uiconst.UI_PICKCHILDREN, align=uiconst.RELATIVE)
        self.iconCont = uiprimitives.Container(parent=self, pos=(5, 0, 32, 32), align=uiconst.CENTERLEFT)
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, idx=1, color=uiconst.ENTRY_LINE_COLOR)

    def Load(self, node):
        InvItem.Load(self, node)
        if self.sr.node.viewMode == 'details':
            self.sr.label.left = 46
            self.LoadMainIcon()
        else:
            self.sr.label.left = 12

    def ConstructHiliteFill(self):
        """
        Nasty hack needed because of screwed up inheritance
        """
        SE_BaseClassCore.ConstructHiliteFill(self)

    def SetLockState(self, locked):
        self.SetState(min(1, locked))
        if self.viewOnly:
            self.sr.label.SetRGBA(0.5, 0.5, 0.5, 1.0)
            self.iconCont.opacity = 0.25
            if self.sr.node.viewMode == 'details':
                self.ConstructLockedIcon()
                self.lockedIcon.Show()
        else:
            self.sr.label.SetRGBA(*util.Color.WHITE)
            self.iconCont.opacity = 1.0
            if self.lockedIcon:
                self.lockedIcon.Hide()

    def ConstructLockedIcon(self):
        if not self.lockedIcon:
            self.lockedIcon = uiprimitives.Sprite(name='lockedIcon', parent=self, texturePath='res:/UI/Texture/classes/Inventory/locked.png', align=uiconst.TOPLEFT, pos=(30, 0, 12, 12), idx=0, hint=localization.GetByLabel('UI/Inventory/ItemLocked'))


class InvBlueprintItem(Item):
    __guid__ = 'listentry.InvBlueprintItem'

    def UpdateLabel(self, new = 0):
        InvItem.UpdateLabel(self, new)
        self.sr.node.label += self.GetExtraColumnsText(self.sr.node)
        if self.sr.node.viewMode in ('list', 'details'):
            self.sr.label.text = self.sr.node.label
        else:
            self.sr.name_label.text += self.sr.node.label

    @classmethod
    def GetExtraColumnsText(cls, node, *args):
        blueprint = node.blueprint
        if blueprint.copy:
            isCopy = localization.GetByLabel('UI/Common/Yes')
        else:
            isCopy = localization.GetByLabel('UI/Common/No')
        ml = blueprint.materialLevel
        pl = blueprint.productivityLevel
        lprr = blueprint.licensedProductionRunsRemaining
        if lprr == -1:
            lprr = ''
        else:
            lprr = localization.formatters.FormatNumeric(lprr, decimalPlaces=0, useGrouping=True)
        label = '<t>%s<t><right>%s<t><right>%s<t><right>%s' % (isCopy,
         localization.formatters.FormatNumeric(ml, decimalPlaces=0, useGrouping=True),
         localization.formatters.FormatNumeric(pl, decimalPlaces=0, useGrouping=True),
         lprr)
        return label

    @classmethod
    def GetCopyData(cls, node):
        label = uix.GetItemLabel(node.rec, node)
        return label + cls.GetExtraColumnsText(node)


class ItemWithVolume(Item):
    __guid__ = 'listentry.InvItemWithVolume'

    def UpdateLabel(self, new = 0):
        InvItem.UpdateLabel(self, new)
        if util.GetAttrs(self, 'sr', 'node', 'remote'):
            return
        volume = GetItemVolume(self.rec)
        self.sr.node.Set('sort_%s' % localization.GetByLabel('UI/Inventory/ItemVolume'), volume)
        u = cfg.dgmunits.Get(const.unitVolume)
        unit = u.displayName
        label = '<t>%s %s' % (util.FmtAmt(volume), unit)
        if self.sr.node.viewMode in ('list', 'details'):
            self.sr.label.text += label
            label = self.sr.label.text
        else:
            self.sr.label.text += label
            label = self.sr.label.text
        self.sr.node.label = label


class ItemCheckbox(Item):
    __guid__ = 'listentry.ItemCheckbox'

    def Startup(self, *args):
        cbox = uicontrols.Checkbox(align=uiconst.CENTERLEFT, left=4, callback=self.CheckBoxChange)
        cbox.data = {}
        self.children.insert(0, cbox)
        self.sr.checkbox = cbox
        self.sr.checkbox.state = uiconst.UI_DISABLED
        self.iconCont.left = 25
        self.sr.label.left = 65

    def Load(self, args):
        InvItem.Load(self, args)
        self.LoadMainIcon()
        if self.sr.flags:
            self.sr.flags.left = 25
            self.sr.flags.top = 18
        if self.sr.tlicon is not None:
            self.sr.tlicon.left = 23
            self.sr.tlicon.top = 1
        data = self.sr.node
        self.sr.checkbox.SetGroup(data.group)
        self.sr.checkbox.SetChecked(data.checked, 0)
        self.sr.checkbox.data.update({'key': data.cfgname,
         'retval': data.retval})
        if not data.OnChange:
            data.OnChange = self.OnChange
        if self.sr.tlicon:
            self.sr.tlicon.left += 1
            self.sr.tlicon.top += 2

    def OnChange(self, checkbox):
        pass

    def CheckBoxChange(self, *args):
        self.sr.node.checked = self.sr.checkbox.checked
        self.sr.node.OnChange(*args)

    def OnClick(self, *args):
        if self.sr.checkbox.checked:
            eve.Message('DiodeDeselect')
        else:
            eve.Message('DiodeClick')
        if self.sr.checkbox.groupName is None:
            self.sr.checkbox.SetChecked(not self.sr.checkbox.checked)
            return
        for node in self.sr.node.scroll.GetNodes():
            if node.Get('__guid__', None) == 'listentry.Checkbox' and node.Get('group', None) == self.sr.checkbox.groupName:
                if node.panel:
                    node.panel.sr.checkbox.SetChecked(0, 0)
                    node.checked = 0
                else:
                    node.checked = 0

        if not self.destroyed:
            self.sr.checkbox.SetChecked(1)


class InvAssetItem(Item):
    __guid__ = 'listentry.InvAssetItem'

    def Load(self, node):
        Item.Load(self, node)
        if node.Get('sublevel', 0):
            padding = 16 * node.Get('sublevel', 0)
            iconPadding = 5 + padding
            self.sr.label.left = 46 + padding
            self.iconCont.left = iconPadding
            if self.sr.flags:
                self.sr.flags.left = iconPadding
            if self.sr.tlicon:
                self.sr.tlicon.left = iconPadding

    def OnDropData(self, dragObj, nodes):
        pass
