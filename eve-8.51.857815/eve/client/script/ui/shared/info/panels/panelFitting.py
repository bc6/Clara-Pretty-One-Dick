#Embedded file name: eve/client/script/ui/shared/info/panels\panelFitting.py
import collections
import itertools
import const
import carbonui.const as uiconst
from eve.client.script.ui.control.entries import LabelTextSides
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay
import uiprimitives
import uiutil
import util
from carbonui.control.scrollentries import SE_BaseClassCore
from carbonui.primitives.container import Container
from dogma.attributes.format import GetFormattedAttributeAndValue
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.eveScroll import Scroll
from localization import GetByLabel, GetByMessageID
FITTING_SLOT_INFO = [{'label': 'UI/InfoWindow/FittingHighPowerSlot',
  'attributeID': const.attributeHiSlots,
  'flags': const.hiSlotFlags,
  'effectID': const.effectHiPower},
 {'label': 'UI/InfoWindow/FittingMediumPowerSlots',
  'attributeID': const.attributeMedSlots,
  'flags': const.medSlotFlags,
  'effectID': const.effectMedPower},
 {'label': 'UI/InfoWindow/FittingLowPowerSlots',
  'attributeID': const.attributeLowSlots,
  'flags': const.loSlotFlags,
  'effectID': const.effectLoPower},
 {'label': 'UI/InfoWindow/FittingRigSlots',
  'attributeID': const.attributeUpgradeSlotsLeft,
  'flags': const.rigSlotFlags,
  'effectID': const.effectRigSlot},
 {'label': 'UI/InfoWindow/FittingSubsystemSlots',
  'attributeID': const.attributeMaxSubSystems,
  'flags': const.subSystemSlotFlags,
  'effectID': const.effectSubSystem}]

class PanelFitting(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.item = attributes.get('item', None)
        self.itemID = attributes.get('itemID', None)
        if self.itemID is None and self.item is not None:
            self.itemID = self.item.itemID
        if self.item is None and self.itemID is not None:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            if dogmaLocation.IsItemLoaded(self.itemID):
                self.item = dogmaLocation.GetItem(self.itemID)

    def Load(self):
        self.Flush()
        fittingScroll = Scroll(name='fittingScroll', parent=self, padding=const.defaultPadding)
        turretSlotsUsed = 0
        launcherSlotsUsed = 0
        entryList = []
        inventory = self.GetShipContents()
        for slotKey, slotInfo in enumerate(FITTING_SLOT_INFO):
            modulesByType = collections.defaultdict(list)
            chargesByFlag = collections.defaultdict(list)
            for item in filter(lambda item: item.flagID in slotInfo['flags'], inventory):
                if IsCharge(item):
                    chargesByFlag[item.flagID].append(item)
                else:
                    modulesByType[item.typeID].append(item)

            usedSlotCount = 0
            for typeID, items in modulesByType.iteritems():
                if HasEffect(typeID, slotInfo['effectID']):
                    usedSlotCount += len(items)
                if HasEffect(typeID, const.effectTurretFitted):
                    turretSlotsUsed += len(items)
                if HasEffect(typeID, const.effectLauncherFitted):
                    launcherSlotsUsed += len(items)
                lowestFlagID = min((item.flagID for item in items))
                sortKey = (slotKey, lowestFlagID)
                entry = self.GetFittingEntry(typeID, len(items))
                entryList.append((sortKey, entry))
                chargeQuantityByType = collections.defaultdict(int)
                for charge in itertools.chain.from_iterable((chargesByFlag[item.flagID] for item in items)):
                    chargeQuantityByType[charge.typeID] += max(charge.quantity, 1)

                for chargeType, chargeQuantity in chargeQuantityByType.iteritems():
                    sortKey = (slotKey, lowestFlagID, chargeType)
                    entry = self.GetFittingEntry(chargeType, chargeQuantity, isCharge=True)
                    entryList.append((sortKey, entry))

            sortKey = (slotKey,)
            entry = self.GetFittingSlotEntry(slotInfo, usedSlotCount)
            entryList.append((sortKey, entry))

        sortedEntryList = sm.GetService('info').GetAttributeScrollListForItem(itemID=self.itemID, typeID=self.typeID, attrList=[const.attributeCpuOutput, const.attributePowerOutput, const.attributeUpgradeCapacity])
        sortedEntryList.append(self.GetHardpointsEntry(turretSlotsUsed, launcherSlotsUsed))
        sortedEntryList.extend(uiutil.SortListOfTuples(entryList))
        fittingScroll.Load(contentList=filter(None, sortedEntryList))

    def GetFittingSlotEntry(self, slotInfo, moduleCount):
        slotCount = self.GetTotalSlotCount(slotInfo)
        if slotCount <= 0 and moduleCount <= 0:
            return
        else:
            isMyActiveShip = self.itemID is not None and util.GetActiveShip() == self.itemID
            isOwnedByMe = self.item is not None and self.item.ownerID == session.charid
            if isMyActiveShip or isOwnedByMe:
                data = {'label': self.GetFittingSlotEntryLabel(slotInfo),
                 'text': GetByLabel('UI/InfoWindow/FittingSlotsUsedAndTotal', usedSlots=moduleCount, slotCount=slotCount),
                 'iconID': cfg.dgmattribs.Get(slotInfo['attributeID']).iconID,
                 'line': 1}
                entry = listentry.Get(decoClass=FittingSlotEntry, data=data)
                return entry
            data = {'label': self.GetFittingSlotEntryLabel(slotInfo),
             'text': util.FmtAmt(slotCount),
             'iconID': cfg.dgmattribs.Get(slotInfo['attributeID']).iconID,
             'line': 1}
            entry = listentry.Get('LabelTextSides', data)
            return entry

    def GetFittingEntry(self, typeID, quantity, isCharge = False):
        itemName = cfg.invtypes.Get(typeID).name
        if quantity > 1:
            label = GetByLabel('UI/InfoWindow/FittingItemLabelWithQuantity', quantity=quantity, itemName=itemName)
        else:
            label = itemName
        data = {'typeID': typeID,
         'label': label,
         'getIcon': True,
         'indentLevel': 1 if isCharge else 0}
        entry = listentry.Get(decoClass=FittingItemEntry, data=data)
        return entry

    def GetHardpointsEntry(self, turretSlotsUsed, launcherSlotsUsed):
        turretSlotCount = self.GetAttributeValue(const.attributeTurretSlotsLeft)
        launcherSlotCount = self.GetAttributeValue(const.attributeLauncherSlotsLeft)
        if self.itemID == util.GetActiveShip():
            turretSlotCount += turretSlotsUsed
            launcherSlotCount += launcherSlotsUsed
        if turretSlotCount <= 0 and launcherSlotCount <= 0:
            return None
        data = {'turretSlotsUsed': turretSlotsUsed,
         'turretSlotCount': turretSlotCount,
         'launcherSlotsUsed': launcherSlotsUsed,
         'launcherSlotCount': launcherSlotCount}
        entry = listentry.Get(decoClass=TurretAndLauncherSlotEntry, data=data)
        return entry

    def GetTotalSlotCount(self, slotInfo):
        if slotInfo['attributeID'] == const.attributeUpgradeSlotsLeft:
            return self.GetTypeAttributeValue(slotInfo['attributeID'])
        else:
            return self.GetAttributeValue(slotInfo['attributeID'])

    def GetFittingSlotEntryLabel(self, slotInfo):
        if slotInfo['attributeID'] == const.attributeUpgradeSlotsLeft:
            rigSize = self.GetAttributeValue(const.attributeRigSize)
            formattedRigSize = GetFormattedAttributeAndValue(const.attributeRigSize, rigSize)
            return GetByLabel(slotInfo['label'], rigSize=getattr(formattedRigSize, 'value', ''))
        return GetByLabel(slotInfo['label'])

    def GetShipContents(self):
        if self.itemID is None:
            return []
        if session.shipid == self.itemID:
            shipinfo = sm.GetService('godma').GetItem(self.itemID)
            if shipinfo is not None and getattr(shipinfo, 'inventory', None) is not None:
                return shipinfo.inventory.List()
        if self.item is None:
            return []
        if self.item.ownerID == session.charid and util.IsStation(self.item.locationID):
            inventoryMgr = sm.GetService('invCache').GetInventoryMgr()
            return inventoryMgr.GetContainerContents(self.item.itemID, self.item.locationID)
        return []

    def GetAttributeValue(self, attributeID):
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        if dogmaLocation.IsItemLoaded(self.itemID):
            return dogmaLocation.GetAccurateAttributeValue(self.itemID, attributeID)
        return self.GetTypeAttributeValue(attributeID)

    def GetTypeAttributeValue(self, attributeID):
        info = sm.GetService('godma').GetStateManager().GetShipType(self.typeID)
        return getattr(info, cfg.dgmattribs.Get(attributeID).attributeName)


def IsCharge(item):
    return item.categoryID == const.categoryCharge


def HasEffect(typeID, effectID):
    return sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, effectID)


class FittingItemEntry(listentry.Item):

    def Load(self, node):
        listentry.Item.Load(self, node)
        indentLevel = node.get('indentLevel', 0)
        if indentLevel > 0:
            self.sr.icon.left = self.height * indentLevel + 4
            self.sr.techIcon.left = self.height * indentLevel + 4
            self.sr.label.left = self.height * indentLevel + 4 + self.sr.icon.width + 4


class FittingSlotEntry(listentry.LabelTextSides):

    def Startup(self, *args):
        super(FittingSlotEntry, self).Startup(*args)
        FillUnderlay(bgParent=self, colorType=uiconst.COLORTYPE_UIHEADER)


class TurretAndLauncherSlotEntry(SE_BaseClassCore):

    def Startup(self, *args):
        uiprimitives.Line(align=uiconst.TOBOTTOM, parent=self, color=uiconst.ENTRY_LINE_COLOR)
        turretTopContainer = Container(parent=self, align=uiconst.TOLEFT_PROP, width=0.5, state=uiconst.UI_NORMAL)
        turretTopContainer.LoadTooltipPanel = self.LoadTooltipPanelForTurret
        uiprimitives.Sprite(name='turretHardpointsIcon', texturePath='res:/UI/Texture/Icons/26_64_1.png', parent=turretTopContainer, align=uiconst.TOPLEFT, pos=(1, 2, 24, 24), ignoreSize=True, state=uiconst.UI_DISABLED)
        self.sr.turretBubbles = []
        for i in range(8):
            x = i * 14 + 26
            bubble = uiprimitives.Sprite(parent=turretTopContainer, pos=(x,
             7,
             14,
             16), useSizeFromTexture=True, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
            self.sr.turretBubbles.append(bubble)

        launcherTopContainer = Container(parent=self, align=uiconst.TOLEFT_PROP, width=0.5, state=uiconst.UI_NORMAL)
        launcherTopContainer.LoadTooltipPanel = self.LoadTooltipPanelForLauncher
        uiprimitives.Sprite(name='launcherHardpointsIcon', texturePath='res:/UI/Texture/Icons/81_64_16.png', parent=launcherTopContainer, align=uiconst.TOPRIGHT, pos=(1, 2, 24, 24), ignoreSize=True, state=uiconst.UI_DISABLED)
        self.sr.launcherBubbles = []
        for i in range(8):
            x = i * 14 + 26
            bubble = uiprimitives.Sprite(parent=launcherTopContainer, pos=(x,
             7,
             14,
             16), useSizeFromTexture=True, align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED)
            self.sr.launcherBubbles.append(bubble)

    def Load(self, node):
        self.sr.node = node
        self.FillBubbles(self.sr.turretBubbles, node.get('turretSlotsUsed', 0), node.get('turretSlotCount', 0))
        self.FillBubbles(self.sr.launcherBubbles, node.get('launcherSlotsUsed', 0), node.get('launcherSlotCount', 0))

    def FillBubbles(self, bubbles, slotsUsed, slotCount):
        for i, bubble in enumerate(bubbles):
            if i < slotsUsed:
                bubble.display = True
                bubble.texturePath = 'res:/UI/Texture/classes/Fitting/slotTaken.png'
            elif i < slotCount:
                bubble.display = True
                bubble.texturePath = 'res:/UI/Texture/classes/Fitting/slotLeft.png'
            else:
                bubble.display = False

    def GetHeight(self, *args):
        node, width = args
        node.height = 30
        return 30

    def LoadTooltipPanelForTurret(self, tooltipPanel, *args):
        turretsFitted = int(self.sr.node.get('turretSlotsUsed', 0))
        turretSlotsCount = int(self.sr.node.get('turretSlotCount', 0))
        counterText = GetByLabel('Tooltips/FittingWindow/TurretHardPointBubbles_description', hardpointsUsed=turretsFitted, hardpointsTotal=turretSlotsCount)
        return self.LoadTooltipPanelForTurretsAndLaunchers(tooltipPanel, const.attributeTurretSlotsLeft, counterText)

    def LoadTooltipPanelForLauncher(self, tooltipPanel, *args):
        turretsFitted = int(self.sr.node.get('launcherSlotsUsed', 0))
        turretSlotsCount = int(self.sr.node.get('launcherSlotCount', 0))
        counterText = GetByLabel('Tooltips/FittingWindow/LauncherHardPointBubbles_description', hardpointsUsed=turretsFitted, hardpointsTotal=turretSlotsCount)
        return self.LoadTooltipPanelForTurretsAndLaunchers(tooltipPanel, const.attributeLauncherSlotsLeft, counterText)

    def LoadTooltipPanelForTurretsAndLaunchers(self, tooltipPanel, attributeID, counterText):
        attribute = cfg.dgmattribs.Get(attributeID)
        headerText = GetByMessageID(attribute.tooltipTitleID)
        descriptionText = GetByMessageID(attribute.tooltipDescriptionID)
        tooltipPanel.LoadGeneric2ColumnTemplate()
        tooltipPanel.AddLabelMedium(text=headerText, bold=True)
        tooltipPanel.AddLabelMedium(text=counterText, bold=True, align=uiconst.TOPRIGHT, cellPadding=(20, 0, 0, 0))
        tooltipPanel.AddLabelMedium(text=descriptionText, wrapWidth=200, colSpan=tooltipPanel.columns, color=(0.6, 0.6, 0.6, 1))

    @classmethod
    def GetCopyData(cls, node):
        return '%s\t%s\n%s\t%s' % (cfg.dgmattribs.Get(const.attributeTurretSlotsLeft).displayName,
         node.get('turretSlotCount', 0),
         cfg.dgmattribs.Get(const.attributeLauncherSlotsLeft).displayName,
         node.get('launcherSlotCount', 0))
