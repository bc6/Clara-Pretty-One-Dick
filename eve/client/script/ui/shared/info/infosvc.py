#Embedded file name: eve/client/script/ui/shared/info\infosvc.py
from dogma.attributes.format import FormatValue, FormatUnit
from dogma.attributes.format import GetFormatAndValue, GetFormattedAttributeAndValue
from dogma import attributes as dogmaAttributes
from carbon.common.script.util.commonutils import StripTags
from eve.client.script.ui.control.entries import LocationGroup, LocationTextEntry
from eve.client.script.ui.shared.info.infoUtil import GetAttributeTooltipTitleAndDescription
from eve.client.script.ui.tooltips.tooltipsWrappers import TooltipHeaderDescriptionWrapper
from eve.common.script.util import industryCommon
from eveexceptions import UserError
from inventorycommon.util import GetTypeVolume
from spacecomponents.client import factory
import uicontrols
import sys
import service
import blue
import telemetry
import uthread
import uix
import uiutil
import util
import copy
import base
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.damageGaugeContainers import DamageEntry
import carbonui.const as uiconst
import log
import localization
import moniker
import mapcommon
from collections import defaultdict, OrderedDict
from eve.common.script.sys.rowset import IndexedRows, Rowset
import const
from spacecomponents.client.display import IterAttributeCollectionInInfoOrder
from .infoWindow import InfoWindow, AttributeRowEntry
from .infoConst import *
import itertoolsext
from eve.client.script.ui.shared.monetization.trialPopup import ORIGIN_SHOWINFO
GENERIC_ATTRIBUTES_TO_AVOID = (const.attributeMass,)
SUN_STATISTICS_ATTRIBUTES = ['spectralClass',
 'luminosity',
 'age',
 'radius',
 'temperature']
ASTEROID_BELT_STATISTICS_ATTRIBUTES = ['density',
 'massDust',
 'orbitPeriod',
 'orbitRadius',
 'eccentricity']
MOON_STATISTICS_ATTRIBUTES = ['density',
 'escapeVelocity',
 'massDust',
 'orbitPeriod',
 'orbitRadius',
 'pressure',
 'radius',
 'surfaceGravity',
 'temperature']
PLANET_STATISTICS_ATTRIBUTES = ['density',
 'eccentricity',
 'escapeVelocity',
 'massDust',
 'orbitPeriod',
 'orbitRadius',
 'pressure',
 'radius',
 'surfaceGravity',
 'temperature']
CELESTIAL_STATISTICS_ATTRIBUTES_BY_GROUPID = {const.groupPlanet: PLANET_STATISTICS_ATTRIBUTES,
 const.groupMoon: MOON_STATISTICS_ATTRIBUTES,
 const.groupAsteroidBelt: ASTEROID_BELT_STATISTICS_ATTRIBUTES}

class Info(service.Service):
    __exportedcalls__ = {'ShowInfo': [],
     'GetAttributeScrollListForType': [],
     'GetAttributeScrollListForItem': [],
     'GetSolarSystemReport': [],
     'GetKillsRecentKills': [],
     'GetKillsRecentLosses': [],
     'GetEmploymentHistorySubContent': [],
     'GetAllianceMembersSubContent': []}
    __guid__ = 'svc.info'
    __notifyevents_ = ('DoSessionChanging', 'OnItemChange', 'OnAllianceRelationshipChanged', 'OnContactChange')
    __servicename__ = 'info'
    __displayname__ = 'Information Service'
    __dependencies__ = ['dataconfig', 'map']
    __startupdependencies__ = ['settings']

    def Run(self, memStream = None):
        self.LogInfo('Starting InfoSvc')
        self.wnds = []
        self.lastActive = None
        self.moniker = None
        self.attributesByName = None
        self._usedWithTypeIDs = None
        self.ClearWnds()

    def OnItemChange(self, item, change):
        if item.categoryID != const.categoryCharge and (item.locationID == eve.session.shipid or const.ixLocationID in change and change[const.ixLocationID] == eve.session.shipid):
            self.itemchangeTimer = base.AutoTimer(1000, self.DelayOnItemChange, item, change)
        itemGone = False
        if const.ixLocationID in change and util.IsJunkLocation(item.locationID):
            itemGone = True
        if const.ixQuantity in change and item.stacksize == 0:
            log.LogTraceback('infoSvc processing ixQuantity change')
            itemGone = True
        if const.ixStackSize in change and item.stacksize == 0:
            itemGone = True
        if itemGone:
            for each in self.wnds:
                if each is None or each.destroyed:
                    self.wnds.remove(each)
                    continue
                if each.itemID == item.itemID:
                    each.ReconstructInfoWindow(each.typeID)

    def DelayOnItemChange(self, item, change):
        self.itemchangeTimer = None
        for each in self.wnds:
            if each is None or each.destroyed:
                self.wnds.remove(each)
                continue
            if each.itemID == eve.session.shipid and not each.IsMinimized():
                each.ReconstructInfoWindow(each.typeID, each.itemID, each.rec)

    def OnContactChange(self, contactIDs, contactType = None):
        for contactID in contactIDs:
            self.UpdateWnd(contactID)

    def OnAllianceRelationshipChanged(self, *args):
        for allianceid in (args[0], args[1]):
            self.UpdateWnd(allianceid)

    def GetShipAndDroneAttributes(self):
        if not hasattr(self, 'shipAttributes'):
            shipAttributes = OrderedDict()
            shipAttributes[localization.GetByLabel('UI/Fitting/Structure')] = {'normalAttributes': [const.attributeHp,
                                  const.attributeCapacity,
                                  const.attributeDroneCapacity,
                                  const.attributeDroneBandwidth,
                                  const.attributeMass,
                                  const.attributeVolume,
                                  const.attributeAgility,
                                  const.attributeSpecialAmmoHoldCapacity,
                                  const.attributeSpecialGasHoldCapacity,
                                  const.attributeSpecialIndustrialShipHoldCapacity,
                                  const.attributeSpecialLargeShipHoldCapacity,
                                  const.attributeSpecialMediumShipHoldCapacity,
                                  const.attributeSpecialMineralHoldCapacity,
                                  const.attributeSpecialOreHoldCapacity,
                                  const.attributeSpecialSalvageHoldCapacity,
                                  const.attributeSpecialShipHoldCapacity,
                                  const.attributeSpecialSmallShipHoldCapacity,
                                  const.attributeSpecialCommandCenterHoldCapacity,
                                  const.attributeSpecialPlanetaryCommoditiesHoldCapacity],
             'groupedAttributes': [('em', const.attributeEmDamageResonance),
                                   ('thermal', const.attributeThermalDamageResonance),
                                   ('kinetic', const.attributeKineticDamageResonance),
                                   ('explosive', const.attributeExplosiveDamageResonance)]}
            shipAttributes[localization.GetByLabel('UI/Common/Armor')] = {'normalAttributes': [const.attributeArmorHP],
             'groupedAttributes': [('em', const.attributeArmorEmDamageResonance),
                                   ('thermal', const.attributeArmorThermalDamageResonance),
                                   ('kinetic', const.attributeArmorKineticDamageResonance),
                                   ('explosive', const.attributeArmorExplosiveDamageResonance)]}
            shipAttributes[localization.GetByLabel('UI/Common/Shield')] = {'normalAttributes': [const.attributeShieldCapacity, const.attributeShieldRechargeRate],
             'groupedAttributes': [('em', const.attributeShieldEmDamageResonance),
                                   ('thermal', const.attributeShieldThermalDamageResonance),
                                   ('kinetic', const.attributeShieldKineticDamageResonance),
                                   ('explosive', const.attributeShieldExplosiveDamageResonance)]}
            shipAttributes[localization.GetByLabel('UI/Fitting/FittingWindow/Capacitor')] = {'normalAttributes': [const.attributeCapacitorCapacity, const.attributeRechargeRate]}
            shipAttributes[localization.GetByLabel('UI/Fitting/FittingWindow/Targeting')] = {'normalAttributes': [const.attributeMaxTargetRange,
                                  const.attributeMaxRange,
                                  const.attributeMaxLockedTargets,
                                  const.attributeSignatureRadius,
                                  const.attributeSignatureResolution,
                                  const.attributeScanResolution,
                                  const.attributeScanLadarStrength,
                                  const.attributeScanMagnetometricStrength,
                                  const.attributeScanRadarStrength,
                                  const.attributeScanGravimetricStrength,
                                  const.attributeProximityRange,
                                  const.attributeFalloff,
                                  const.attributeTrackingSpeed]}
            shipAttributes[localization.GetByLabel('UI/InfoWindow/SharedFacilities')] = {'normalAttributes': [const.attributeFleetHangarCapacity, const.attributeShipMaintenanceBayCapacity, const.attributeMaxJumpClones]}
            shipAttributes[localization.GetByLabel('UI/InfoWindow/JumpDriveSystems')] = {'normalAttributes': [const.attributeJumpDriveCapacitorNeed,
                                  const.attributeJumpDriveRange,
                                  const.attributeJumpDriveConsumptionType,
                                  const.attributeJumpDriveConsumptionAmount,
                                  const.attributeJumpDriveDuration,
                                  const.attributeJumpPortalCapacitorNeed,
                                  const.attributeJumpPortalConsumptionMassFactor,
                                  const.attributeJumpPortalDuration,
                                  const.attributeSpecialFuelBayCapacity]}
            shipAttributes[localization.GetByLabel('UI/Compare/Propulsion')] = {'normalAttributes': [const.attributeMaxVelocity]}
            self.shipAttributes = shipAttributes
        return self.shipAttributes

    def GetAttributeOrder(self):
        if not hasattr(self, 'attributeOrder'):
            self.attributeOrder = [const.attributePrimaryAttribute,
             const.attributeSecondaryAttribute,
             const.attributeRequiredSkill1,
             const.attributeRequiredSkill2,
             const.attributeRequiredSkill3,
             const.attributeRequiredSkill4,
             const.attributeRequiredSkill5,
             const.attributeRequiredSkill6]
        return self.attributeOrder

    def GetStatusAttributeInfo(self):
        if not hasattr(self, 'statusAttributeInfo'):
            cargoCapacityColor = (0.0, 0.31, 0.4)
            shipBayLoadFunc = self.GetCurrentShipBayLoad
            self.statusAttributeInfo = {const.attributeCpuOutput: {'label': localization.GetByLabel('UI/Common/Cpu'),
                                        'loadAttributeID': const.attributeCpuLoad,
                                        'color': (0.203125, 0.3828125, 0.37890625, 1.0)},
             const.attributePowerOutput: {'label': localization.GetByLabel('UI/Common/Powergrid'),
                                          'loadAttributeID': const.attributePowerLoad,
                                          'color': (0.40625, 0.078125, 0.03125, 1.0)},
             const.attributeUpgradeCapacity: {'label': localization.GetByLabel('UI/Common/Calibration'),
                                              'loadAttributeID': const.attributeUpgradeLoad},
             const.attributeMaxJumpClones: {'label': localization.GetByLabel('UI/InfoWindow/JumpClonesStatusBar'),
                                            'loadAttributeFunc': self.GetCurrentShipCloneCount},
             const.attributeCapacity: {'loadAttributeFunc': shipBayLoadFunc,
                                       'color': cargoCapacityColor},
             const.attributeDroneCapacity: {'label': localization.GetByLabel('UI/Common/DroneBay'),
                                            'loadAttributeFunc': shipBayLoadFunc,
                                            'color': cargoCapacityColor},
             const.attributeSpecialAmmoHoldCapacity: {'label': localization.GetByLabel('UI/Ship/AmmoHold'),
                                                      'loadAttributeFunc': shipBayLoadFunc,
                                                      'color': cargoCapacityColor},
             const.attributeSpecialGasHoldCapacity: {'label': localization.GetByLabel('UI/Ship/GasHold'),
                                                     'loadAttributeFunc': shipBayLoadFunc,
                                                     'color': cargoCapacityColor},
             const.attributeSpecialIndustrialShipHoldCapacity: {'label': localization.GetByLabel('UI/Ship/IndustrialShipHold'),
                                                                'loadAttributeFunc': shipBayLoadFunc,
                                                                'color': cargoCapacityColor},
             const.attributeSpecialLargeShipHoldCapacity: {'label': localization.GetByLabel('UI/Ship/LargeShipHold'),
                                                           'loadAttributeFunc': shipBayLoadFunc,
                                                           'color': cargoCapacityColor},
             const.attributeSpecialMediumShipHoldCapacity: {'label': localization.GetByLabel('UI/Ship/MediumShipHold'),
                                                            'loadAttributeFunc': shipBayLoadFunc,
                                                            'color': cargoCapacityColor},
             const.attributeSpecialMineralHoldCapacity: {'label': localization.GetByLabel('UI/Ship/MineralHold'),
                                                         'loadAttributeFunc': shipBayLoadFunc,
                                                         'color': cargoCapacityColor},
             const.attributeSpecialOreHoldCapacity: {'label': localization.GetByLabel('UI/Ship/OreHold'),
                                                     'loadAttributeFunc': shipBayLoadFunc,
                                                     'color': cargoCapacityColor},
             const.attributeSpecialSalvageHoldCapacity: {'label': localization.GetByLabel('UI/Ship/SalvageHold'),
                                                         'loadAttributeFunc': shipBayLoadFunc,
                                                         'color': cargoCapacityColor},
             const.attributeSpecialShipHoldCapacity: {'label': localization.GetByLabel('UI/Ship/ShipHold'),
                                                      'loadAttributeFunc': shipBayLoadFunc,
                                                      'color': cargoCapacityColor},
             const.attributeSpecialSmallShipHoldCapacity: {'label': localization.GetByLabel('UI/Ship/SmallShipHold'),
                                                           'loadAttributeFunc': shipBayLoadFunc,
                                                           'color': cargoCapacityColor},
             const.attributeSpecialCommandCenterHoldCapacity: {'label': localization.GetByLabel('UI/Ship/CommandCenterHold'),
                                                               'loadAttributeFunc': shipBayLoadFunc,
                                                               'color': cargoCapacityColor},
             const.attributeSpecialPlanetaryCommoditiesHoldCapacity: {'label': localization.GetByLabel('UI/Ship/PlanetaryCommoditiesHold'),
                                                                      'loadAttributeFunc': shipBayLoadFunc,
                                                                      'color': cargoCapacityColor},
             const.attributeFleetHangarCapacity: {'label': localization.GetByLabel('UI/Ship/FleetHangar'),
                                                  'loadAttributeFunc': shipBayLoadFunc,
                                                  'color': cargoCapacityColor},
             const.attributeShipMaintenanceBayCapacity: {'label': localization.GetByLabel('UI/Ship/ShipMaintenanceBay'),
                                                         'loadAttributeFunc': shipBayLoadFunc,
                                                         'color': cargoCapacityColor},
             const.attributeSpecialFuelBayCapacity: {'label': localization.GetByLabel('UI/Ship/FuelBay'),
                                                     'loadAttributeFunc': shipBayLoadFunc,
                                                     'color': cargoCapacityColor}}
        return self.statusAttributeInfo

    def Stop(self, memStream = None):
        self.ClearWnds()
        self.lastActive = None
        self.moniker = None
        self.attributesByName = None
        self.wnds = []

    def ClearWnds(self):
        self.wnds = []
        if getattr(uicore, 'registry', None):
            for each in uicore.registry.GetWindows()[:]:
                if each is not None and not each.destroyed and each.windowID and each.windowID[0] == 'infowindow':
                    each.Close()

    def DoSessionChanging(self, isremote, session, change):
        self.moniker = None
        if session.charid is None:
            self.ClearWnds()

    def GetSolarSystemReport(self, solarsystemID = None):
        solarsystemID = solarsystemID or eve.session.solarsystemid or eve.session.solarsystemid2
        if solarsystemID is None:
            return
        items = self.map.GetSolarsystemItems(solarsystemID)
        types = {}
        for celestial in items:
            types.setdefault(celestial.groupID, []).append(celestial)

        for groupID in types.iterkeys():
            if groupID == const.groupStation:
                continue

    def ShowInfo(self, typeID, itemID = None, new = 0, rec = None, parentID = None, abstractinfo = None, selectTabType = None):
        if itemID == const.factionUnknown:
            eve.Message('KillerOfUnknownFaction')
            return
        modal = uicore.registry.GetModalWindow()
        createNew = new or not settings.user.ui.Get('useexistinginfownd', 1) or uicore.uilib.Key(uiconst.VK_SHIFT)
        if len(self.wnds):
            for each in self.wnds:
                if each is None or each.destroyed:
                    self.wnds.remove(each)

        useWnd = None
        if len(self.wnds) and not createNew:
            if self.lastActive is not None and self.lastActive in self.wnds:
                if not self.lastActive.destroyed:
                    useWnd = self.lastActive
            wnd = self.wnds[-1]
            if not modal or modal and modal.parent == wnd.parent:
                if not wnd.destroyed:
                    useWnd = wnd
        if useWnd and not modal:
            useWnd.ReconstructInfoWindow(typeID, itemID, rec=rec, parentID=parentID, abstractinfo=abstractinfo, selectTabType=selectTabType)
            useWnd.Maximize()
        else:
            useWnd = InfoWindow.Open(windowID=('infowindow', blue.os.GetWallclockTime()), typeID=typeID, itemID=itemID, rec=rec, parentID=parentID, ignoreStack=modal, abstractinfo=abstractinfo, selectTabType=selectTabType)
            self.wnds.append(useWnd)
        if modal and not modal.destroyed and modal.windowID != 'progresswindow':
            useWnd.ShowModal()
        return useWnd

    def UpdateWnd(self, itemID, maximize = 0):
        for wnd in self.wnds:
            if wnd.itemID == itemID or getattr(wnd.sr, 'corpID', None) == itemID or getattr(wnd.sr, 'allianceID', None) == itemID:
                wnd.ReconstructInfoWindow(wnd.typeID, wnd.itemID)
                if maximize:
                    wnd.Maximize()
                break

    def UnregisterWindow(self, wnd, *args):
        if wnd in self.wnds:
            self.wnds.remove(wnd)
        if self.lastActive == wnd:
            self.lastActive = None

    def OnActivateWnd(self, wnd):
        self.lastActive = wnd

    def GetRankEntry(self, rank, hilite = False):
        facwarcurrrank = getattr(rank, 'currentRank', 1)
        facwarfaction = getattr(rank, 'factionID', None)
        if rank and facwarfaction is not None:
            lbl, _ = sm.GetService('facwar').GetRankLabel(facwarfaction, facwarcurrrank)
            if hilite:
                lbl = localization.GetByLabel('UI/FactionWarfare/CurrentRank', currentRankName=lbl)
            entry = listentry.Get('RankEntry', {'label': cfg.factions.Get(facwarfaction).factionName,
             'text': lbl,
             'rank': facwarcurrrank,
             'warFactionID': facwarfaction,
             'selected': False,
             'typeID': const.typeRank,
             'showinfo': 1,
             'line': 1})
            return entry

    def GetMedalEntry(self, info, details, *args):
        d = details
        numAwarded = 0
        if type(info) == list:
            m = info[0]
            numAwarded = len(info)
        else:
            m = info
        sublevel = 1
        if args:
            sublevel = args[0]
        medalribbondata = uix.FormatMedalData(d)
        title = m.title
        if numAwarded > 0:
            title = localization.GetByLabel('UI/InfoWindow/MedalAwardedNumTimes', medalName=title, numTimes=numAwarded)
        description = m.description
        medalTitleText = localization.GetByLabel('UI/InfoWindow/MedalTitle')
        data = {'label': title,
         'text': description,
         'sublevel': sublevel,
         'id': m.medalID,
         'line': 1,
         'abstractinfo': medalribbondata,
         'typeID': const.typeMedal,
         'itemID': m.medalID,
         'icon': 'ui_51_64_4',
         'showinfo': True,
         'sort_%s' % medalTitleText: '_%s' % title.lower(),
         'iconsize': 26}
        return listentry.Get('MedalRibbonEntry', data)

    def EditContact(self, wnd, itemID, edit):
        addressBookSvc = sm.GetService('addressbook')
        addressBookSvc.AddToPersonalMulti(itemID, 'contact', edit)

    def UpdateContactButtons(self, wnd, itemID):
        addressBookSvc = sm.GetService('addressbook')
        if not addressBookSvc.IsInAddressBook(itemID, 'contact'):
            wnd.data['buttons'] += [(localization.GetByLabel('UI/PeopleAndPlaces/AddContact'),
              self.EditContact,
              (wnd, itemID, False),
              81)]
        else:
            wnd.data['buttons'] += [(localization.GetByLabel('UI/PeopleAndPlaces/EditContact'),
              self.EditContact,
              (wnd, itemID, True),
              81)]

    def GetCurrentShipCloneCount(self, attributeID):
        if util.GetActiveShip():
            return len(sm.GetService('clonejump').GetShipClones())
        return 0

    def GetCurrentShipBayLoad(self, attributeID):
        attributeToInventoryFlagMap = {const.attributeCapacity: const.flagCargo,
         const.attributeDroneCapacity: const.flagDroneBay,
         const.attributeSpecialAmmoHoldCapacity: const.flagSpecializedAmmoHold,
         const.attributeSpecialGasHoldCapacity: const.flagSpecializedGasHold,
         const.attributeSpecialIndustrialShipHoldCapacity: const.flagSpecializedIndustrialShipHold,
         const.attributeSpecialLargeShipHoldCapacity: const.flagSpecializedLargeShipHold,
         const.attributeSpecialMediumShipHoldCapacity: const.flagSpecializedMediumShipHold,
         const.attributeSpecialMineralHoldCapacity: const.flagSpecializedMineralHold,
         const.attributeSpecialOreHoldCapacity: const.flagSpecializedOreHold,
         const.attributeSpecialSalvageHoldCapacity: const.flagSpecializedSalvageHold,
         const.attributeSpecialShipHoldCapacity: const.flagSpecializedShipHold,
         const.attributeSpecialSmallShipHoldCapacity: const.flagSpecializedSmallShipHold,
         const.attributeSpecialCommandCenterHoldCapacity: const.flagSpecializedCommandCenterHold,
         const.attributeSpecialPlanetaryCommoditiesHoldCapacity: const.flagSpecializedPlanetaryCommoditiesHold,
         const.attributeFleetHangarCapacity: const.flagFleetHangar,
         const.attributeShipMaintenanceBayCapacity: const.flagShipHangar,
         const.attributeSpecialFuelBayCapacity: const.flagSpecializedFuelBay}
        return sm.GetService('clientDogmaIM').GetDogmaLocation().GetCapacity(util.GetActiveShip(), attributeID, attributeToInventoryFlagMap[attributeID]).used

    def GetStatusBarEntryForAttribute(self, attributeID, itemID = None, typeID = None):
        if itemID is None or itemID != util.GetActiveShip():
            return
        statusAttributeInfo = self.GetStatusAttributeInfo().get(attributeID, None)
        if statusAttributeInfo is None:
            return
        GAV = self.GetGAVFunc(itemID, typeID)
        total = GAV(attributeID)
        if total == 0.0:
            return
        loadAttributeID = statusAttributeInfo.get('loadAttributeID', attributeID)
        loadGetterFunc = statusAttributeInfo.get('loadAttributeFunc', GAV)
        load = loadGetterFunc(loadAttributeID)
        status = load / float(total)
        attributeFormatInfo = dogmaAttributes.GetAttribute(attributeID)
        text = localization.GetByLabel('UI/InfoWindow/StatusAttributeLabel', numerator=load, denominator=total, unit=FormatUnit(attributeFormatInfo.unitID))
        return listentry.Get('StatusBar', {'attributeID': attributeID,
         'label': statusAttributeInfo.get('label', attributeFormatInfo.displayName),
         'text': text,
         'value': status,
         'iconID': attributeFormatInfo.iconID,
         'color': statusAttributeInfo.get('color', util.Color.GRAY3),
         'gradientBrightnessFactor': 1.2})

    def UpdateDataShip(self, wnd, typeID, itemID):
        shipinfo = sm.GetService('godma').GetItem(itemID) if itemID is not None else None
        wnd.dynamicTabs.append(TAB_TRAITS)
        attributeEntries, _ = self.GetShipAndDroneAttributeScrolllistAndAttributesList(itemID, typeID)
        wnd.data[TAB_ATTIBUTES]['items'] += attributeEntries
        baseWarpSpeed = self.GetBaseWarpSpeed(typeID, shipinfo)
        if baseWarpSpeed:
            bwsAttr = cfg.dgmattribs.Get(const.attributeBaseWarpSpeed)
            data = {'attributeID': const.attributeBaseWarpSpeed,
             'line': 1,
             'label': bwsAttr.displayName,
             'text': baseWarpSpeed,
             'iconID': bwsAttr.iconID}
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        wnd.dynamicTabs.append(TAB_FITTING)
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)
        metaTypeScrollList, variationTypeDict = self.GetMetaTypeInfo(typeID)
        wnd.data[TAB_VARIATIONS]['items'] += metaTypeScrollList
        wnd.variationTypeDict = variationTypeDict
        self.InitVariationBottom(wnd)
        if hasattr(cfg.fsdTypeOverrides.Get(typeID), 'masteries'):
            wnd.dynamicTabs.append(TAB_MASTERY)
        if sm.GetService('shipTree').IsInShipTree(typeID):
            wnd.data['buttons'] += [(localization.GetByLabel('UI/InfoWindow/ShowInISIS'),
              self.ShowShipInISIS,
              typeID,
              81)]

    def ApplyAttributeTooltip(self, entries):
        for entry in entries:
            if not hasattr(entry, 'attributeID'):
                continue
            tooltipTitleText, tooltipDescriptionText = GetAttributeTooltipTitleAndDescription(entry.attributeID)
            if tooltipTitleText:
                entry.tooltipPanelClassInfo = TooltipHeaderDescriptionWrapper(header=tooltipTitleText, description=tooltipDescriptionText, tooltipPointer=uiconst.POINT_RIGHT_2)

    def GetGroupedAttributesEntry(self, groupedAttributes, itemID, typeID):
        if itemID and sm.GetService('godma').GetItem(itemID):
            attributeDict = self.GetAttributeDictForItem(itemID, typeID)
        else:
            attributeDict = self.GetAttributeDictForType(typeID)
            if itemID:
                dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
                if dogmaLocation.IsItemLoaded(itemID):
                    attributeDict.update(dogmaLocation.GetDisplayAttributes(itemID, attributeDict.keys()))
        attributeInfoList = []
        for dmgType, eachAttributeID in groupedAttributes:
            if eachAttributeID not in attributeDict:
                dogmaAttributeInfo = dogmaAttributes.GetAttribute(eachAttributeID)
                if dogmaAttributeInfo.unitID in (const.unitInverseAbsolutePercent, const.unitInversedModifierPercent):
                    value = 1
                else:
                    value = 0
            else:
                value = attributeDict[eachAttributeID]
            formatInfo = GetFormattedAttributeAndValue(eachAttributeID, value)
            if not formatInfo:
                attributeInfoList.append(None)
                continue
            attributeTypeInfo = cfg.dgmattribs.Get(eachAttributeID)
            if attributeTypeInfo.unitID in (const.unitInverseAbsolutePercent, const.unitInversedModifierPercent):
                value = 1 - value
            attributeInfo = {'dmgType': dmgType,
             'text': formatInfo.displayName,
             'iconID': formatInfo.iconID,
             'value': value,
             'valueText': formatInfo.value,
             'attributeID': eachAttributeID}
            attributeInfoList.append(attributeInfo)

        data = {'attributeInfoList': attributeInfoList,
         'OnClick': lambda attributeID: self.OnAttributeClick(attributeID, itemID)}
        return listentry.Get(decoClass=DamageEntry, data=data)

    def ShowShipInISIS(self, typeID):
        sm.GetService('shipTree').LogIGS('OpenInISIS')
        sm.GetService('shipTreeUI').OpenAndShowShip(typeID)

    def ShowCharacterSheetCertificates(self):
        sm.GetService('charactersheet').OpenCertificates()

    def UpdateDataDrone(self, wnd, typeID, itemID):
        metaTypeScrollList, variationTypeDict = self.GetMetaTypeInfo(typeID)
        wnd.data[TAB_VARIATIONS]['items'] += metaTypeScrollList
        wnd.variationTypeDict = variationTypeDict
        self.InitVariationBottom(wnd)
        attributeEntries, addedAttributes = self.GetShipAndDroneAttributeScrolllistAndAttributesList(itemID, typeID)
        wnd.data[TAB_ATTIBUTES]['items'] += attributeEntries
        attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID, typeID, banAttrs=addedAttributes + self.GetSkillAttrs())
        if attributeScrollListForItem:
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/Miscellaneous')}))
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)

    def GetShipAndDroneAttributeScrolllistAndAttributesList(self, itemID, typeID):
        attrDict = self.GetAttributeDictForType(typeID)
        addedAttributes = []
        scrollList = []
        for caption, attrs in self.GetShipAndDroneAttributes().iteritems():
            normalAttributes = attrs['normalAttributes']
            groupedAttributes = attrs.get('groupedAttributes', [])
            shipAttr = [ each for each in normalAttributes if each in attrDict ]
            newEntries = []
            if shipAttr:
                attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, attrList=shipAttr)
                newEntries += attributeScrollListForItem
                addedAttributes += [ x.attributeID for x in attributeScrollListForItem ]
                for eachNode in attributeScrollListForItem:
                    if getattr(eachNode, 'attributeIDs', None):
                        addedAttributes += eachNode.attributeIDs

            if groupedAttributes:
                entry = self.GetGroupedAttributesEntry(groupedAttributes, itemID, typeID)
                addedAttributes += [ g[1] for g in groupedAttributes ]
                newEntries.append(entry)
            if newEntries:
                scrollList.append(listentry.Get('Header', {'label': caption}))
                scrollList += newEntries

        return (scrollList, addedAttributes)

    def UpdateDataModule(self, wnd, typeID, itemID):
        invTypeScrollList = self.GetInvTypeInfo(typeID, [const.attributeCapacity, const.attributeVolume])
        wnd.data[TAB_ATTIBUTES]['items'] += invTypeScrollList
        if not itemID:
            damageTypes = cfg.dgmtypeattribs.get(typeID, [])
            firstAmmoLoaded = itertoolsext.first_or_default([ x for x in damageTypes if x.attributeID == const.attributeAmmoLoaded ])
            if firstAmmoLoaded:
                damageScrollList = self.GetAttributeScrollListForType(typeID=firstAmmoLoaded.value, attrList=[const.attributeEmDamage,
                 const.attributeThermalDamage,
                 const.attributeKineticDamage,
                 const.attributeExplosiveDamage])
                wnd.data[TAB_ATTIBUTES]['items'] += damageScrollList
        effectTypeScrollList = self.GetEffectTypeInfo(typeID=typeID, effList=[const.effectHiPower,
         const.effectMedPower,
         const.effectLoPower,
         const.effectRigSlot,
         const.effectSubSystem])
        wnd.data[TAB_FITTING]['items'] += effectTypeScrollList
        attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, banAttrs=[const.attributeCpu,
         const.attributePower,
         const.attributeRigSize,
         const.attributeUpgradeCost,
         const.attributeCapacity,
         const.attributeVolume,
         const.attributeMass] + self.GetSkillAttrs())
        wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        fittingScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, attrList=(const.attributeCpu,
         const.attributePower,
         const.attributeRigSize,
         const.attributeUpgradeCost))
        wnd.data[TAB_FITTING]['items'] += fittingScrollListForItem
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)
        if self.GetUsedWithTypeIDs(wnd.typeID):
            wnd.dynamicTabs.append(TAB_USEDWITH)
        metaTypeScrollList, variationTypeDict = self.GetMetaTypeInfo(typeID)
        wnd.data[TAB_VARIATIONS]['items'] += metaTypeScrollList
        wnd.variationTypeDict = variationTypeDict
        self.InitVariationBottom(wnd)

    def UpdateComponentData(self, wnd, typeID, itemID):
        attributesSuppressed = self.GetAttributesSuppressedByComponents(typeID)
        attributeScroll = wnd.data[TAB_ATTIBUTES]['items']
        invTypeScrollList = self.GetInvTypeInfo(typeID, [const.attributeVolume])
        attributeScroll += invTypeScrollList
        spaceComponentScrollList = self.GetSpaceComponentAttrItemInfo(typeID, itemID)
        attributeScroll += spaceComponentScrollList
        attributeScroll.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Common/Other')}))
        attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, banAttrs=attributesSuppressed + self.GetSkillAttrs())
        attributeScroll += attributeScrollListForItem
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)
        metaTypeScrollList, variationTypeDict = self.GetMetaTypeInfo(typeID)
        wnd.data[TAB_VARIATIONS]['items'] += metaTypeScrollList
        wnd.variationTypeDict = variationTypeDict
        self.InitVariationBottom(wnd)

    def UpdateDataSecureContainer(self, wnd, itemID):
        self.UpdateDataModule(wnd, wnd.typeID, itemID)
        bp = sm.GetService('michelle').GetBallpark()
        if not bp:
            return
        ball = bp.GetBall(itemID)
        if not ball or ball.isFree:
            return
        bpr = sm.GetService('michelle').GetRemotePark()
        if bpr:
            expiry = bpr.GetContainerExpiryDate(itemID)
            daysLeft = max(0, (expiry - blue.os.GetWallclockTime()) / const.DAY)
            expiryText = localization.GetByLabel('UI/Common/NumDays', numDays=daysLeft)
            expiryLabel = listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/Common/Expires'),
             'text': expiryText,
             'iconID': const.iconDuration})
            wnd.data[TAB_ATTIBUTES]['items'].append(expiryLabel)

    def UpdateDataCharge(self, wnd, typeID, itemID):
        invTypeScrollList = self.GetInvTypeInfo(typeID, [const.attributeCapacity, const.attributeVolume])
        wnd.data[TAB_ATTIBUTES]['items'] += invTypeScrollList
        if itemID:
            attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, banAttrs=[const.attributeCapacity, const.attributeVolume] + self.GetSkillAttrs())
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        else:
            attributeScrollListForType = self.GetAttributeScrollListForType(typeID=typeID, banAttrs=[const.attributeCapacity, const.attributeVolume] + self.GetSkillAttrs())
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForType
        bsd, bad = self.GetBaseDamageValue(typeID)
        if bad is not None and bsd is not None:
            text = localization.formatters.FormatNumeric(bsd[0], useGrouping=True, decimalPlaces=1)
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/InfoWindow/BaseShieldDamageLabel'),
             'text': text,
             'iconID': bsd[1]}))
            text = localization.formatters.FormatNumeric(bad[0], useGrouping=True, decimalPlaces=1)
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/InfoWindow/BaseArmorDamageLabel'),
             'text': text,
             'iconID': bad[1]}))
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)
        metaTypeScrollList, variationTypeDict = self.GetMetaTypeInfo(typeID)
        wnd.data[TAB_VARIATIONS]['items'] += metaTypeScrollList
        wnd.variationTypeDict = variationTypeDict
        if self.GetUsedWithTypeIDs(wnd.typeID):
            wnd.dynamicTabs.append(TAB_USEDWITH)
        self.InitVariationBottom(wnd)

    def ConstructUsedWithTypeIDs(self):
        """
        Constructs a dictionary of list of typesIDs used by another typeIDs, such as charges used by a launcher,
        and vice versa
        """
        usedWith = defaultdict(set)
        godmaStateManager = sm.GetService('godma').GetStateManager()
        for launcherTypeObj in cfg.invtypes:
            if not launcherTypeObj.published:
                continue
            if launcherTypeObj.categoryID != const.categoryModule:
                continue
            godmaType = godmaStateManager.GetType(launcherTypeObj.typeID)
            i = 1
            for attrName in ('chargeGroup1', 'chargeGroup2', 'chargeGroup3', 'chargeGroup4'):
                if not godmaType.AttributeExists(attrName):
                    continue
                groupID = getattr(godmaType, attrName)
                i += 1
                if groupID not in cfg.typesByGroups:
                    continue
                for chargeTypeObj in cfg.typesByGroups[groupID]:
                    if not chargeTypeObj.published:
                        continue
                    chargeGodmaType = godmaStateManager.GetType(chargeTypeObj.typeID)
                    if not godmaType.chargeSize or chargeGodmaType.chargeSize == godmaType.chargeSize:
                        usedWith[chargeTypeObj.typeID].add(launcherTypeObj.typeID)
                        usedWith[launcherTypeObj.typeID].add(chargeTypeObj.typeID)

        self._usedWithTypeIDs = usedWith
        return usedWith

    def GetUsedWithTypeIDs(self, typeID):
        """
        Returns all typeIDs used by the input typeID (such as all charges used by a launcher)
        """
        if self._usedWithTypeIDs is None:
            self.ConstructUsedWithTypeIDs()
        return self._usedWithTypeIDs.get(typeID, None)

    def UpdateDataCharacter(self, wnd, typeID, itemID):
        if not util.IsNPC(itemID):
            if session.charid != itemID:
                self.UpdateContactButtons(wnd, itemID)
            wnd.dynamicTabs.append(TAB_EMPLOYMENTHISTORY)
            if not util.IsDustCharacter(itemID):
                self.UpdateDataDecorations(wnd, typeID, itemID)
        else:
            self.UpdateDataAgent(wnd, typeID, itemID)
        wnd.dynamicTabs.append(TAB_NOTES)
        if not util.IsDustCharacter(itemID):
            wnd.dynamicTabs.append(TAB_STANDINGS)

    def UpdateDataDecorations(self, wnd, typeID, itemID):
        medalsEntries = sm.StartService('charactersheet').GetMedalScroll(itemID, True, True)
        wnd.data[TAB_MEDALS]['items'] = medalsEntries
        corpID = sm.GetService('corp').GetInfoWindowDataForChar(itemID, acceptBlank=True).corpID
        rank = sm.StartService('facwar').GetCharacterRankInfo(itemID, corpID)
        if rank is not None:
            wnd.data[TAB_RANKS]['items'].append(self.GetRankEntry(rank))
        if not medalsEntries and not rank:
            wnd.dynamicTabs.append(TAB_DECORATIONS)

    def UpdateDataCorp(self, wnd, typeID, itemID):
        if not util.IsNPC(itemID):
            self.UpdateContactButtons(wnd, itemID)
            wnd.dynamicTabs.append(TAB_ALLIANCEHISTORY)
            wnd.dynamicTabs.append(TAB_WARHISTORY)
        parallelCalls = []
        parallelCalls.append((sm.RemoteSvc('config').GetStationSolarSystemsByOwner, (itemID,)))
        if util.IsNPC(itemID):
            parallelCalls.append((sm.GetService('agents').GetAgentsByCorpID, (itemID,)))
            parallelCalls.append((sm.RemoteSvc('corporationSvc').GetCorpInfo, (itemID,)))
        else:
            parallelCalls.append((lambda : None, ()))
            parallelCalls.append((lambda : None, ()))
        parallelCalls.append((sm.GetService('faction').GetNPCCorpInfo, (itemID,)))
        systems, agents, corpmktinfo, npcCorpInfo = uthread.parallel(parallelCalls)
        founderdone = 0
        if cfg.invtypes.Get(cfg.eveowners.Get(wnd.corpinfo.ceoID).typeID).groupID == const.groupCharacter:
            if wnd.corpinfo.creatorID == wnd.corpinfo.ceoID:
                ceoLabel = localization.GetByLabel('UI/Corporations/CorpUIHome/CeoAndFounder')
                founderdone = 1
            else:
                ceoLabel = localization.GetByLabel('UI/Corporations/Common/CEO')
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': ceoLabel,
             'text': cfg.eveowners.Get(wnd.corpinfo.ceoID).name,
             'typeID': cfg.eveowners.Get(wnd.corpinfo.ceoID).typeID,
             'itemID': wnd.corpinfo.ceoID}))
        if not founderdone and cfg.invtypes.Get(cfg.eveowners.Get(wnd.corpinfo.creatorID).typeID).groupID == const.groupCharacter:
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/Corporations/Common/Founder'),
             'text': cfg.eveowners.Get(wnd.corpinfo.creatorID).name,
             'typeID': cfg.eveowners.Get(wnd.corpinfo.creatorID).typeID,
             'itemID': wnd.corpinfo.creatorID}))
        if wnd.corpinfo.allianceID:
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/Common/Alliance'),
             'text': cfg.eveowners.Get(wnd.corpinfo.allianceID).name,
             'typeID': const.typeAlliance,
             'itemID': wnd.corpinfo.allianceID}))
        for configName, label in [('tickerName', localization.GetByLabel('UI/Corporations/CorpUIHome/TickerName')),
         ('shares', localization.GetByLabel('UI/Corporations/CorpUIHome/Shares')),
         ('memberCount', localization.GetByLabel('UI/Corporations/CorpUIHome/MemberCount')),
         ('taxRate', localization.GetByLabel('UI/Corporations/CorpUIHome/TaxRate')),
         ('friendlyFire', localization.GetByLabel('UI/Corporations/CorpUIHome/FriendlyFire'))]:
            if configName == 'memberCount' and util.IsNPC(itemID):
                continue
            val = getattr(wnd.corpinfo, configName, 0.0)
            decoClass = listentry.LabelTextSides
            moreInfoHint = ''
            if configName == 'taxRate':
                val = localization.GetByLabel('UI/Common/Percentage', percentage=val * 100)
            elif isinstance(val, int):
                val = localization.formatters.FormatNumeric(val, useGrouping=True, decimalPlaces=0)
            elif configName == 'friendlyFire':
                statusText = sm.GetService('corp').GetCorpFriendlyFireStatus(wnd.corpinfo.aggressionSettings)
                val = statusText
                decoClass = listentry.LabelTextSidesMoreInfo
                moreInfoHint = localization.GetByLabel('UI/Corporations/FriendlyFire/Description')
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=decoClass, data={'line': 1,
             'label': label,
             'text': val,
             'moreInfoHint': moreInfoHint}))

        if wnd.corpinfo.url:
            linkTag = '<url=%s>' % wnd.corpinfo.url
            url = localization.GetByLabel('UI/Corporations/CorpUIHome/URLPlaceholder', linkTag=linkTag, url=wnd.corpinfo.url)
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/Corporations/CorpUIHome/URL'),
             'text': url}))
        if npcCorpInfo is not None and util.IsNPC(itemID):
            sizeDict = {'T': localization.GetByLabel('UI/Corporations/TinyCorp'),
             'S': localization.GetByLabel('UI/Corporations/SmallCorp'),
             'M': localization.GetByLabel('UI/Corporations/MediumCorp'),
             'L': localization.GetByLabel('UI/Corporations/LargeCorp'),
             'H': localization.GetByLabel('UI/Corporations/HugeCorp')}
            txt = sizeDict[npcCorpInfo.size]
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/Corporations/CorpSize'),
             'text': txt}))
            extentDict = {'N': localization.GetByLabel('UI/Corporations/NationalCrop'),
             'G': localization.GetByLabel('UI/Corporations/GlobalCorp'),
             'R': localization.GetByLabel('UI/Corporations/RegionalCorp'),
             'L': localization.GetByLabel('UI/Corporations/LocalCorp'),
             'C': localization.GetByLabel('UI/Corporations/ConstellationCorp')}
            txt = extentDict[npcCorpInfo.extent]
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/Corporations/CorpExtent'),
             'text': txt}))
        if itemID == session.corpid:
            for charinfo in sm.GetService('corp').GetMembersAsEveOwners():
                if not util.IsNPC(charinfo.ownerID):
                    wnd.data[TAB_CORPMEMBERS]['items'].append(listentry.Get('User', {'info': charinfo,
                     'charID': charinfo.ownerID}))

            wnd.data[TAB_CORPMEMBERS]['headers'].append(localization.GetByLabel('UI/Common/NameCharacter'))
        solarSystemDict = {}
        corpName = cfg.eveowners.Get(itemID).name
        mapHintCallback = lambda : localization.GetByLabel('UI/InfoWindow/SystemSettledByCorp', corpName=corpName)
        for solarSys in systems:
            solarSystemDict[solarSys.solarSystemID] = (2.0,
             1.0,
             (mapHintCallback, ()),
             None)

        for solarSys in systems:
            parentConstellation = self.map.GetParent(solarSys.solarSystemID)
            parentRegion = self.map.GetParent(parentConstellation)
            name_with_path = ' / '.join([ self.map.GetItem(each).itemName for each in (parentRegion, parentConstellation, solarSys.solarSystemID) ])
            wnd.data[TAB_SYSTEMS]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/Common/SolarSystem'),
             'text': name_with_path,
             'typeID': const.typeSolarSystem,
             'itemID': solarSys.solarSystemID}))

        wnd.data[TAB_SYSTEMS]['name'] = localization.GetByLabel('UI/InfoWindow/SettledSystems')

        def ShowMap(*args):
            sm.GetService('viewState').ActivateView('starmap', hightlightedSolarSystems=solarSystemDict)

        wnd.data['buttons'] += [(localization.GetByLabel('UI/Commands/ShowLocationOnMap'),
          ShowMap,
          (),
          66)]
        if not util.IsNPC(itemID):
            if sm.GetService('corp').GetActiveApplication(itemID) is not None:
                buttonLabel = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplication')
            else:
                buttonLabel = localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Rankings/ApplyToJoin')
            wnd.data['buttons'] += [(buttonLabel, sm.GetService('corp').ApplyForMembership, (itemID,))]
        else:
            wnd.data['buttons'] += [(localization.GetByLabel('UI/AgentFinder/AgentFinder'),
              uicore.cmd.OpenAgentFinder,
              (),
              66)]

        def SortStuff(a, b):
            for i in xrange(3):
                x, y = a[i], b[i]
                if x.name < y.name:
                    return -1
                if x.name > y.name:
                    return 1

            return 0

        if corpmktinfo is not None:
            sellStuff = []
            buyStuff = []
            for each in corpmktinfo:
                t = cfg.invtypes.GetIfExists(each.typeID)
                if t:
                    g = cfg.invgroups.Get(t.groupID)
                    c = cfg.invcategories.Get(g.categoryID)
                    if each.sellPrice is not None:
                        sellStuff.append((c,
                         g,
                         t,
                         each.sellPrice,
                         each.sellQuantity,
                         each.sellDate,
                         each.sellStationID))
                    if each.buyPrice is not None:
                        buyStuff.append((c,
                         g,
                         t,
                         each.buyPrice,
                         each.buyQuantity,
                         each.buyDate,
                         each.buyStationID))

            sellStuff.sort(SortStuff)
            buyStuff.sort(SortStuff)
            for stuff, label in ((sellStuff, localization.GetByLabel('UI/InfoWindow/Supply')), (buyStuff, localization.GetByLabel('UI/InfoWindow/Demand'))):
                if stuff:
                    wnd.data[TAB_MARKETACTIVITY]['items'].append(listentry.Get('Header', {'label': label}))
                    for each in stuff:
                        c, g, t, price, quantity, lastActivity, station = each
                        if lastActivity:
                            txt = localization.GetByLabel('UI/InfoWindow/CategoryGroupTypeForPrice', categoryName=c.name, groupName=g.name, typeName=t.name, price=price)
                        else:
                            txt = localization.GetByLabel('UI/InfoWindow/CategoryGroupTypeForPriceAndLastTransaction', categoryName=c.name, groupName=g.name, typeName=t.name, price=price, date=util.FmtDate(lastActivity, 'ls'), amount=quantity, location=station)
                        wnd.data[TAB_MARKETACTIVITY]['items'].append(listentry.Get('Text', {'line': 1,
                         'typeID': t.typeID,
                         'text': txt}))

        if util.IsNPC(itemID):
            agentCopy = agents[:]
            header = agentCopy.header
            acopy2 = Rowset(header)
            for agent in agentCopy:
                if agent.agentTypeID in (const.agentTypeResearchAgent, const.agentTypeBasicAgent, const.agentTypeFactionalWarfareAgent):
                    acopy2.append(agent)

            agentCopy = acopy2
            self.GetAgentScrollGroups(agentCopy, wnd.data[TAB_AGENTS]['items'])
        wnd.dynamicTabs.append(TAB_STANDINGS)

    def UpdateDataAlliance(self, wnd):
        if not util.IsNPC(wnd.itemID):
            self.UpdateContactButtons(wnd, wnd.itemID)
            wnd.dynamicTabs.append(TAB_WARHISTORY)
        rec = wnd.allianceinfo
        executor = cfg.eveowners.Get(rec.executorCorpID)
        data = {'line': 1,
         'label': localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Home/Executor'),
         'text': executor.ownerName,
         'typeID': const.typeCorporation,
         'itemID': rec.executorCorpID}
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        data = {'line': 1,
         'label': localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Home/ShortName'),
         'text': rec.shortName}
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        data = {'line': 1,
         'label': localization.GetByLabel('UI/InfoWindow/CreatedByCorp'),
         'text': cfg.eveowners.Get(rec.creatorCorpID).ownerName,
         'typeID': const.typeCorporation,
         'itemID': rec.creatorCorpID}
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        data = {'line': 1,
         'label': localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Home/CreatedBy'),
         'text': cfg.eveowners.Get(rec.creatorCharID).ownerName,
         'typeID': const.typeCharacterAmarr,
         'itemID': rec.creatorCharID}
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        data = {'line': 1,
         'label': localization.GetByLabel('UI/InfoWindow/StartDate'),
         'text': util.FmtDate(rec.startDate, 'ls'),
         'typeID': None,
         'itemID': None}
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        if rec.url:
            linkTag = '<url=%s>' % rec.url
            url = localization.GetByLabel('UI/Corporations/CorpUIHome/URLPlaceholder', linkTag=linkTag, url=rec.url)
            data = {'line': 1,
             'label': localization.GetByLabel('UI/Common/URL'),
             'text': url}
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data=data))
        wnd.dynamicTabs.append(TAB_MEMBERS)
        wnd.dynamicTabs.append(TAB_STANDINGS)

    def UpdateDataStargate(self, wnd, itemID):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is not None:
            slimItem = bp.GetInvItem(itemID)
            if slimItem is not None:
                locs = []
                for each in slimItem.jumps:
                    if each.locationID not in locs:
                        locs.append(each.locationID)
                    if each.toCelestialID not in locs:
                        locs.append(each.toCelestialID)

                if len(locs):
                    cfg.evelocations.Prime(locs)
                for each in slimItem.jumps:
                    destLabel = localization.GetByLabel('UI/InfoWindow/DestinationInSolarsystem', destination=each.toCelestialID, solarsystem=each.locationID)
                    wnd.data[TAB_JUMPS]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': localization.GetByLabel('UI/Common/Jump'),
                     'text': destLabel,
                     'typeID': const.groupSolarSystem,
                     'itemID': each.locationID}))

    def GetCelestialStatisticsForCelestial(self, celestialID, celestialGroupID):
        statistics = {}
        celestial = cfg.mapSolarSystemContentCache.celestials[celestialID]
        if not hasattr(celestial, 'statistics'):
            return statistics
        celestialStatistics = celestial.statistics
        attributeNames = CELESTIAL_STATISTICS_ATTRIBUTES_BY_GROUPID[celestialGroupID]
        attributeNames.sort()
        for attributeName in attributeNames:
            statistics[attributeName] = getattr(celestialStatistics, attributeName)

        return statistics

    def GetCelestialStatisticsForSun(self, sun):
        statistics = {}
        if not hasattr(sun, 'statistics'):
            return statistics
        sunStatistics = sun.statistics
        attributeNames = SUN_STATISTICS_ATTRIBUTES
        for attributeName in attributeNames:
            statistics[attributeName] = getattr(sunStatistics, attributeName)

        return statistics

    def UpdateDataCelestial(self, wnd, typeID, itemID, parentID):
        _, regionID, constellationID, solarsystemID, _itemID = self.map.GetParentLocationID(itemID)
        if util.IsCelestial(itemID):
            if wnd.groupID == const.groupSun:
                statistics = self.GetCelestialStatisticsForSun(cfg.mapSolarSystemContentCache[solarsystemID].star)
            else:
                statistics = self.GetCelestialStatisticsForCelestial(itemID, wnd.groupID)
            for attributeName, attributeValue in statistics.iteritems():
                label, value = util.FmtPlanetAttributeKeyVal(attributeName, attributeValue)
                wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
                 'label': label,
                 'text': value}))

        if solarsystemID is not None:
            itemID = self.GetOrbitalBodies(wnd, itemID, solarsystemID, typeID)
            if typeID == const.typeSolarSystem:
                self.GetStationTab(wnd, itemID)
        typeGroupID = cfg.invtypes.Get(typeID).groupID
        neighborGrouping = {const.groupConstellation: localization.GetByLabel('UI/InfoWindow/AdjacentConstellations'),
         const.groupRegion: localization.GetByLabel('UI/InfoWindow/AdjacentRegions'),
         const.groupSolarSystem: localization.GetByLabel('UI/InfoWindow/AdjacentSolarSystem')}
        childGrouping = {const.groupRegion: localization.GetByLabel('UI/InfoWindow/RelatedConstellation'),
         const.groupConstellation: localization.GetByLabel('UI/InfoWindow/RelatedSolarSystem')}
        if typeGroupID == const.groupConstellation:
            children = self.map.GetLocationChildren(itemID)
            for childID in children:
                childItem = self.map.GetItem(childID)
                if childItem is not None:
                    text = self.GetColorCodedSecurityStringForSystem(childItem.itemID, childItem.itemName)
                    childTypeName = cfg.invtypes.Get(childItem.typeID).name
                    genericDisplayLabel = '%s - %s' % (childTypeName, childItem.itemName)
                    wnd.data[TAB_CHILDREN]['items'].append(listentry.Get('LabelLocationTextTop', {'line': 1,
                     'label': cfg.invtypes.Get(childItem.typeID).name,
                     'text': text,
                     'typeID': childItem.typeID,
                     'itemID': childItem.itemID,
                     'tabs': [35],
                     'tabMargin': -2,
                     'genericDisplayLabel': genericDisplayLabel}))

            wnd.data[TAB_CHILDREN]['name'] = childGrouping.get(const.groupConstellation, localization.GetByLabel('UI/InfoWindow/UnknownTabName'))
        elif typeGroupID == const.groupRegion:
            children = self.map.GetLocationChildren(itemID)
            for childID in children:
                childItem = self.map.GetItem(childID)
                if childItem is not None:
                    childTypeName = cfg.invtypes.Get(childItem.typeID).name
                    genericDisplayLabel = '%s - %s' % (childTypeName, childItem.itemName)
                    wnd.data[TAB_CHILDREN]['items'].append(listentry.Get('LabelLocationTextTop', {'line': 1,
                     'label': childTypeName,
                     'text': childItem.itemName,
                     'typeID': childItem.typeID,
                     'itemID': childItem.itemID,
                     'genericDisplayLabel': genericDisplayLabel}))

            wnd.data[TAB_CHILDREN]['name'] = childGrouping.get(const.groupRegion, localization.GetByLabel('UI/InfoWindow/UnknownTabName'))
        if typeGroupID in [const.groupConstellation, const.groupRegion, const.groupSolarSystem]:
            neigbors = self.map.GetNeighbors(itemID)
            for childID in neigbors:
                childItem = self.map.GetItem(childID)
                if childItem is not None:
                    if childItem.typeID == const.groupSolarSystem:
                        text = self.GetColorCodedSecurityStringForSystem(childID, childItem.itemName)
                    else:
                        text = childItem.itemName
                    childTypeName = cfg.invtypes.Get(childItem.typeID).name
                    genericDisplayLabel = '%s - %s' % (childTypeName, childItem.itemName)
                    wnd.data[TAB_NEIGHBORS]['items'].append(listentry.Get('LabelLocationTextTop', {'line': 1,
                     'label': childTypeName,
                     'text': text,
                     'typeID': childItem.typeID,
                     'itemID': childItem.itemID,
                     'tabs': [35],
                     'tabMargin': -2,
                     'genericDisplayLabel': genericDisplayLabel}))

            wnd.data[TAB_NEIGHBORS]['name'] = neighborGrouping.get(typeGroupID, localization.GetByLabel('UI/InfoWindow/UnknownTabName'))
        if cfg.invtypes.Get(typeID).groupID in [const.groupConstellation, const.groupSolarSystem]:
            shortestRoute = sm.GetService('starmap').ShortestGeneralPath(itemID)
            shortestRoute = shortestRoute[1:]
            wasRegion = None
            wasConstellation = None
            if len(shortestRoute) > 0:
                wnd.data[TAB_ROUTE]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Market/MarketQuote/NumberOfJumps', num=len(shortestRoute))}))
            for i in range(len(shortestRoute)):
                childID = shortestRoute[i]
                childItem = self.map.GetItem(childID)
                parentConstellation = self.map.GetParent(childID)
                parentRegion = self.map.GetParent(parentConstellation)
                nameWithPath = localization.GetByLabel('UI/InfoWindow/SolarsystemLocation', region=parentRegion, constellation=parentConstellation, solarsystem=childID)
                nameWithPath = self.GetColorCodedSecurityStringForSystem(childID, nameWithPath)
                jumpDescription = localization.GetByLabel('UI/InfoWindow/RegularJump', numJumps=i + 1)
                if i > 0:
                    if wasRegion != parentRegion:
                        jumpDescription = localization.GetByLabel('UI/InfoWindow/RegionJump', numJumps=i + 1)
                    elif wasConstellation != parentConstellation:
                        jumpDescription = localization.GetByLabel('UI/InfoWindow/ConstellationJump', numJumps=i + 1)
                wasRegion = parentRegion
                wasConstellation = parentConstellation
                if childItem is not None:
                    genericDisplayLabel = cfg.evelocations.Get(childID).name
                    wnd.data[TAB_ROUTE]['items'].append(listentry.Get('LabelLocationTextTop', {'line': 1,
                     'label': jumpDescription,
                     'text': nameWithPath,
                     'typeID': childItem.typeID,
                     'itemID': childItem.itemID,
                     'tabs': [35],
                     'tabMargin': -2,
                     'genericDisplayLabel': genericDisplayLabel}))

        groupID = cfg.invtypes.Get(typeID).groupID

        def ShowMap(idx, *args):
            sm.GetService('viewState').ActivateView('starmap', interestID=itemID)

        if groupID in [const.groupSolarSystem, const.groupConstellation, const.groupRegion]:
            loc = (None, None, None)
            if groupID == const.groupSolarSystem:
                systemID = itemID
                constellationID = self.map.GetParent(itemID)
                regionID = self.map.GetParent(constellationID)
                loc = (systemID, constellationID, regionID)
            elif groupID == const.groupConstellation:
                constellationID = itemID
                regionID = self.map.GetParent(constellationID)
                loc = (None, constellationID, regionID)
            elif groupID == const.groupRegion:
                regionID = itemID
                loc = (None, None, regionID)
            wnd.data['buttons'] = [(localization.GetByLabel('UI/Inflight/BookmarkLocation'),
              self.Bookmark,
              (itemID, typeID, parentID),
              81), (localization.GetByLabel('UI/Commands/ShowLocationOnMap'),
              ShowMap,
              [const.groupSolarSystem, const.groupConstellation, const.groupRegion].index(groupID),
              81), (localization.GetByLabel('UI/Sovereignty/Sovereignty'), self.DrillToLocation, loc)]

    def GetOrbitalBodies(self, wnd, itemID, solarsystemID, typeID):
        solarsystem = self.map.GetSolarsystemItems(solarsystemID, False)
        sun = None
        if cfg.invtypes.Get(typeID).groupID == const.groupSolarSystem:
            for each in solarsystem:
                if cfg.invtypes.Get(each.typeID).groupID == const.groupSun:
                    sun = each.itemID

            if sun:
                itemID = sun
        if solarsystemID == itemID and sun:
            rootID = [ each for each in solarsystem if cfg.invtypes.Get(each.typeID).groupID == const.groupSun ][0].itemID
        else:
            rootID = itemID
        groupSort = {const.groupStargate: -1,
         const.groupAsteroidBelt: 1,
         const.groupMoon: 2,
         const.groupPlanet: 3}

        def DrawOrbitItems(rootID, indent):
            tmp = [ each for each in solarsystem if each.orbitID == rootID ]
            tmp.sort(lambda a, b: cmp(*[ groupSort.get(cfg.invtypes.Get(each.typeID).groupID, 0) for each in (a, b) ]) or cmp(a.celestialIndex, b.celestialIndex) or cmp(a.orbitIndex, b.orbitIndex))
            for each in tmp:
                name = cfg.evelocations.Get(each.itemID).name
                planet = False
                if util.IsStation(each.itemID):
                    continue
                elif each.groupID == const.groupMoon:
                    name = '<color=0xff888888>' + name + '</color>'
                elif each.groupID == const.groupAsteroidBelt:
                    name = '<color=0xffdddddd>' + name + '</color>'
                elif each.groupID == const.groupPlanet:
                    planet = True
                if planet:
                    planetTypeName = cfg.invtypes.Get(each.typeID).name
                    genericDisplayLabel = '%s - %s' % (planetTypeName, name)
                    data = {'line': 1,
                     'text': indent * '    ' + name + ' %s' % planetTypeName,
                     'typeID': each.typeID,
                     'itemID': each.itemID,
                     'locationID': solarsystemID,
                     'genericDisplayLabel': genericDisplayLabel,
                     'isDragObject': True}
                    entry = listentry.Get(entryType=None, data=data, decoClass=LocationTextEntry)
                    wnd.data[TAB_ORBITALBODIES]['items'].append(entry)
                else:
                    data = {'line': 1,
                     'text': indent * '    ' + name,
                     'genericDisplayLabel': StripTags(name),
                     'typeID': each.typeID,
                     'itemID': each.itemID,
                     'isDragObject': True}
                    entry = listentry.Get(entryType=None, data=data, decoClass=LocationTextEntry)
                    wnd.data[TAB_ORBITALBODIES]['items'].append(entry)
                DrawOrbitItems(each.itemID, indent + 1)

        if sun:
            DrawOrbitItems(rootID, 0)
        itemID = solarsystemID
        return itemID

    def GetStationTab(self, wnd, solarsystemID):
        solarsystem = self.map.GetSolarsystemItems(solarsystemID, False)
        allStations = [ each for each in solarsystem if cfg.invtypes.Get(each.typeID).groupID == const.groupStation ]
        if not allStations:
            return
        stationEntryList = self.GetStationEntryList(allStations)
        wnd.data[TAB_STATIONS]['items'] += stationEntryList

    def GetStationEntryList(self, stationList):
        entryList = []
        stationList.sort(lambda a, b: cmp(a.celestialIndex, b.celestialIndex) or cmp(a.orbitIndex, b.orbitIndex))
        stationIDs = []
        for each in stationList:
            stationIDs.append(each.itemID)

        if len(stationIDs):
            cfg.evelocations.Prime(stationIDs)
        for each in stationList:
            name = cfg.evelocations.Get(each.itemID).name
            data = {'GetSubContent': self.GetStationSubContent,
             'label': name,
             'MenuFunction': self.GetMenuLocationMenu,
             'id': ('infownd_stations', each.itemID),
             'groupItems': [],
             'iconMargin': 18,
             'allowCopy': 1,
             'showicon': 'hide',
             'showlen': 0,
             'itemID': each.itemID,
             'typeID': each.typeID,
             'state': 'locked'}
            entry = listentry.Get(entryType=None, data=data, decoClass=LocationGroup)
            entryList.append(entry)

        return entryList

    def GetStationSubContent(self, nodedata, *args):
        itemID = nodedata.itemID
        stationInfo = self.map.GetStation(itemID)
        serviceEntryList = self.GetServicesForStation(stationInfo, itemID, iconoffset=20)
        return serviceEntryList

    def GetMenuLocationMenu(self, node):
        stationInfo = self.map.GetStation(node.itemID)
        return sm.StartService('menu').CelestialMenu(node.itemID, typeID=stationInfo.stationTypeID, parentID=stationInfo.solarSystemID)

    def UpdateDataControlTower(self, wnd, typeID, itemID):
        self.UpdateDataModule(wnd, typeID, itemID)
        wnd.dynamicTabs.append(TAB_FUELREQ)

    def UpdateDataAsteroidOrCloud(self, wnd, typeID, itemID):
        invtype = cfg.invtypes.Get(typeID)
        formatedValue = localization.formatters.FormatNumeric(invtype.volume, useGrouping=True)
        value = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=FormatUnit(const.unitVolume))
        fields = [(localization.GetByLabel('UI/Common/Volume'), value), (localization.GetByLabel('UI/InfoWindow/UnitsToRefine'), localization.formatters.FormatNumeric(int(invtype.portionSize), useGrouping=True))]
        try:
            fields.append((localization.GetByLabel('UI/Generic/FormatPlanetAttributes/attributeRadius'), FormatValue(sm.GetService('michelle').GetBallpark().GetBall(itemID).radius, const.unitLength)))
        except:
            sys.exc_clear()

        for header, text in fields:
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': header,
             'text': text}))

    def UpdateDataFaction(self, wnd, typeID, itemID):
        races, stations, systems = sm.GetService('faction').GetFactionInfo(itemID)
        memberRaceList = []
        for race in cfg.races:
            if race.raceID in races:
                memberRaceList.append(race.raceName)

        if len(memberRaceList) > 0:
            memberRaceText = localization.formatters.FormatGenericList(memberRaceList)
            wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/InfoWindow/MemberRaces'),
             'text': memberRaceText}))
        text = localization.formatters.FormatNumeric(systems, useGrouping=True)
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
         'label': localization.GetByLabel('UI/InfoWindow/SettledSystems'),
         'text': text}))
        text = localization.formatters.FormatNumeric(stations, useGrouping=True)
        wnd.data[TAB_ATTIBUTES]['items'].append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
         'label': localization.GetByLabel('UI/Common/Stations'),
         'text': text}))
        wnd.data[TAB_ATTIBUTES]['name'] = localization.GetByLabel('UI/InfoWindow/TabNames/Statistics')

        def SortFunc(x, y):
            xname = cfg.eveowners.Get(x).name
            if xname.startswith('The '):
                xname = xname[4:]
            yname = cfg.eveowners.Get(y).name
            if yname.startswith('The '):
                yname = yname[4:]
            if xname < yname:
                return -1
            if xname > yname:
                return 1
            return 0

        corpsOfFaction = sm.GetService('faction').GetCorpsOfFaction(itemID)
        corpsOfFaction = copy.copy(corpsOfFaction)
        corpsOfFaction.sort(SortFunc)
        for corpID in corpsOfFaction:
            corp = cfg.eveowners.Get(corpID)
            wnd.data[TAB_MEMBEROFCORPS]['items'].append(listentry.Get('Text', {'line': 1,
             'typeID': corp.typeID,
             'itemID': corp.ownerID,
             'text': corp.name}))

        regions, constellations, solarsystems = sm.GetService('faction').GetFactionLocations(itemID)
        for regionID in regions:
            nameWithPath = self.map.GetItem(regionID).itemName
            wnd.data[TAB_SYSTEMS]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/Common/LocationTypes/Region'),
             'text': nameWithPath,
             'typeID': const.typeRegion,
             'itemID': regionID}))

        for constellationID in constellations:
            regionID = self.map.GetParent(constellationID)
            nameWithPath = localization.GetByLabel('UI/InfoWindow/ConstellationLocation', region=regionID, constellation=constellationID)
            wnd.data[TAB_SYSTEMS]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/Corporations/ConstellationCorp'),
             'text': nameWithPath,
             'typeID': const.typeConstellation,
             'itemID': constellationID}))

        for solarsystemID in solarsystems:
            constellationID = self.map.GetParent(solarsystemID)
            regionID = self.map.GetParent(constellationID)
            nameWithPath = localization.GetByLabel('UI/InfoWindow/SolarsystemLocation', region=regionID, constellation=constellationID, solarsystem=solarsystemID)
            wnd.data[TAB_SYSTEMS]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'),
             'text': nameWithPath,
             'typeID': const.typeSolarSystem,
             'itemID': solarsystemID}))

        wnd.data[TAB_SYSTEMS]['name'] = localization.GetByLabel('UI/InfoWindow/ControlledTerritory')
        illegalities = cfg.invcontrabandTypesByFaction.get(itemID, {})
        for tmpTypeID, illegality in illegalities.iteritems():
            txt = self.__GetIllegalityString(illegality)
            illegalityText = localization.GetByLabel('UI/InfoWindow/IllegalTypeString', item=tmpTypeID, implications=txt)
            wnd.data[TAB_LEGALITY]['items'].append(listentry.Get('Text', {'line': 1,
             'text': illegalityText,
             'typeID': tmpTypeID}))

        wnd.data[TAB_LEGALITY]['items'] = localization.util.Sort(wnd.data[TAB_LEGALITY]['items'], key=lambda x: x['text'])
        if illegalities:
            wnd.data[TAB_LEGALITY]['items'].insert(0, listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/IllegalTypes')}))
        wnd.dynamicTabs.append(TAB_STANDINGS)

    def UpdateDataAgent(self, wnd, typeID, itemID):
        agentID = itemID or sm.GetService('godma').GetType(typeID).agentID
        try:
            details = sm.GetService('agents').GetAgentMoniker(agentID).GetInfoServiceDetails()
            if details is not None:
                npcDivisions = sm.GetService('agents').GetDivisions()
                agentInfo = sm.GetService('agents').GetAgentByID(agentID)
                if agentInfo:
                    typeDict = {const.agentTypeGenericStorylineMissionAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeStorylineImportant'),
                     const.agentTypeStorylineMissionAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeStorylineImportant'),
                     const.agentTypeEventMissionAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeEvent'),
                     const.agentTypeCareerAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeCareer')}
                    t = typeDict.get(agentInfo.agentTypeID, None)
                    if t:
                        wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentType'),
                         'text': t}))
                if agentInfo and agentInfo.agentTypeID not in (const.agentTypeGenericStorylineMissionAgent, const.agentTypeStorylineMissionAgent):
                    wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': localization.GetByLabel('UI/InfoWindow/AgentDivision'),
                     'text': npcDivisions[agentInfo.divisionID].divisionName.replace('&', '&amp;')}))
                if details.stationID:
                    stationinfo = sm.RemoteSvc('stationSvc').GetStation(details.stationID)
                    wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': localization.GetByLabel('UI/InfoWindow/AgentLocation'),
                     'text': cfg.evelocations.Get(details.stationID).name,
                     'typeID': stationinfo.stationTypeID,
                     'itemID': details.stationID}))
                else:
                    agentSolarSystemID = sm.GetService('agents').GetSolarSystemOfAgent(agentID)
                    if agentSolarSystemID is not None:
                        wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentLocation'),
                         'text': cfg.evelocations.Get(agentSolarSystemID).name,
                         'typeID': const.typeSolarSystem,
                         'itemID': agentSolarSystemID}))
                if agentInfo and agentInfo.agentTypeID not in (const.agentTypeGenericStorylineMissionAgent, const.agentTypeStorylineMissionAgent):
                    level = localization.formatters.FormatNumeric(details.level, decimalPlaces=0)
                    wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': localization.GetByLabel('UI/InfoWindow/AgentLevel'),
                     'text': level}))
                for data in details.services:
                    serviceInfo = sm.GetService('agents').ProcessAgentInfoKeyVal(data)
                    for entry in serviceInfo:
                        wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('Header', {'label': entry[0]}))
                        for entryDetails in entry[1]:
                            wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                             'label': entryDetails[0],
                             'text': entryDetails[1]}))

                if details.incompatible:
                    if type(details.incompatible) is tuple:
                        incText = localization.GetByLabel(details.incompatible[0], **details.incompatible[1])
                    elif details.incompatible == 'Not really an agent':
                        incText = None
                    else:
                        incText = details.incompatible
                    if incText:
                        wnd.data[TAB_AGENTINFO]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentCompatibility'),
                         'text': incText}))
        except (UserError, RuntimeError):
            pass

    def UpdateDataOrbital(self, wnd, itemID):
        self.UpdateDataModule(wnd, wnd.typeID, itemID)

        def FetchDynamicAttributes(wnd, data, itemID):
            """ Threaded method to fetch some dynamic data from the server for the Attributes tab on the show info window. """
            if sm.GetService('michelle').GetBallpark().GetBall(itemID) is not None:
                taxRate = moniker.GetPlanetOrbitalRegistry(session.solarsystemid).GetTaxRate(itemID)
                if taxRate is not None:
                    text = localization.GetByLabel('UI/Common/Percentage', percentage=taxRate * 100)
                else:
                    text = localization.GetByLabel('UI/PI/Common/CustomsOfficeAccessDenied')
                data['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/PI/Common/CustomsOfficeTaxRateLabel'),
                 'text': text,
                 'icon': 'ui_77_32_46'}))
                wnd.maintabs.ReloadVisible()
            else:
                log.LogInfo('Unable to fetch tax rate for customs office in a different system')

        uthread.new(FetchDynamicAttributes, wnd, wnd.data[TAB_ATTIBUTES], itemID)

    def UpdateDataIllegal(self, wnd, typeID):
        illegalities = cfg.invtypes.Get(typeID).Illegality()
        if illegalities:
            wnd.data[TAB_LEGALITY]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/LegalImplications')}))
        for tmpFactionID, illegality in illegalities.iteritems():
            txt = self.__GetIllegalityString(illegality)
            illegalityText = localization.GetByLabel('UI/InfoWindow/IllegalWithFactionString', factionName=cfg.eveowners.Get(tmpFactionID).name, implications=txt)
            wnd.data[TAB_LEGALITY]['items'].append(listentry.Get('Text', {'line': 1,
             'text': illegalityText,
             'typeID': const.typeFaction,
             'itemID': tmpFactionID}))

    def UpdateDataGenericItem(self, wnd, typeID, itemID):
        invTypeScrollList = self.GetInvTypeInfo(typeID, [const.attributeVolume])
        wnd.data[TAB_ATTIBUTES]['items'] += invTypeScrollList
        if itemID is not None and sm.GetService('godma').GetItem(itemID) is not None:
            attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, banAttrs=self.GetSkillAttrs())
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        else:
            attributeScrollListForType = self.GetAttributeScrollListForType(typeID=typeID, banAttrs=self.GetSkillAttrs())
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForType
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)

    def UpdateDataSecurityTag(self, wnd, typeID, itemID):
        attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID)
        wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        invTypeScrollList = self.GetInvTypeInfo(typeID, [const.attributeVolume])
        wnd.data[TAB_ATTIBUTES]['items'] += invTypeScrollList
        ShowSecurityOfficeMap = lambda : sm.GetService('starmap').Open(starColorMode=mapcommon.STARMODE_SERVICE_SecurityOffice)
        wnd.data['buttons'] += [(localization.GetByLabel('UI/Commands/ShowSecurityOffices'),
          ShowSecurityOfficeMap,
          (),
          66)]

    def UpdateDataSkill(self, wnd, typeID, itemID):
        self.UpdateDataGenericItem(wnd, typeID, itemID)
        if len(cfg.GetTypesRequiredBySkill(typeID)) > 0:
            wnd.dynamicTabs.append(TAB_REQUIREDFOR)

    def UpdateDataStation(self, wnd, typeID, itemID):
        stationInfo = self.map.GetStation(itemID)
        serviceEntryList = self.GetServicesForStation(stationInfo, itemID)
        wnd.data[TAB_SERVICES]['items'] += serviceEntryList
        for locID in [stationInfo.regionID, stationInfo.constellationID, stationInfo.solarSystemID]:
            mapItem = self.map.GetItem(locID)
            if mapItem is not None:
                if mapItem.typeID == const.typeSolarSystem:
                    text = self.GetColorCodedSecurityStringForSystem(mapItem.itemID, mapItem.itemName)
                    text = text.replace('<t>', ' ')
                else:
                    text = mapItem.itemName
                wnd.data[TAB_LOCATION]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': cfg.invtypes.Get(mapItem.typeID).name,
                 'text': text,
                 'typeID': mapItem.typeID,
                 'itemID': mapItem.itemID}))

        stationOwnerID = None
        if eve.session.solarsystemid is not None:
            slimitem = sm.GetService('michelle').GetBallpark().GetInvItem(itemID)
            if slimitem is not None:
                stationOwnerID = slimitem.ownerID
        if stationOwnerID is None and stationInfo and stationInfo.ownerID:
            stationOwnerID = stationInfo.ownerID
        if stationOwnerID is not None:
            wnd.GetCorpLogo(stationOwnerID, parent=wnd.subinfolinkcontainer)
            wnd.subinfolinkcontainer.height = 64
        wnd.data['buttons'] = [(localization.GetByLabel('UI/Inflight/SetDestination'),
          self.SetDestination,
          (itemID,),
          81)]

    def GetServicesForStation(self, stationInfo, itemID, iconoffset = 4):
        serviceEntryList = []
        sortServices = []
        mask = stationInfo.serviceMask
        for info in sm.GetService('station').GetStationServiceInfo(stationInfo=stationInfo):
            if info.name == 'navyoffices':
                faction = sm.GetService('faction').GetFaction(stationInfo.ownerID)
                if not faction or faction not in [const.factionAmarrEmpire,
                 const.factionCaldariState,
                 const.factionGallenteFederation,
                 const.factionMinmatarRepublic]:
                    continue
            elif info.name == 'securityoffice':
                if not sm.GetService('securityOfficeSvc').CanAccessServiceInStation(itemID):
                    continue
            for bit in info.serviceIDs:
                if mask & bit:
                    if hasattr(info, 'iconID'):
                        icon = info.iconID
                    else:
                        icon = info.texturePath
                    sortServices.append((info.label, (info.label, icon)))
                    break

        if sortServices:
            sortServices = uiutil.SortListOfTuples(sortServices)
            for displayName, iconpath in sortServices:
                data = {'line': 1,
                 'label': displayName,
                 'selectable': 0,
                 'iconoffset': iconoffset,
                 'icon': iconpath}
                serviceEntryList.append(listentry.Get('IconEntry', data=data))

        return serviceEntryList

    def UpdateDataRank(self, wnd):
        """ Factional warfare Rank """
        characterRanks = sm.StartService('facwar').GetCharacterRankOverview(session.charid)
        characterRanks = [ each for each in characterRanks if each.factionID == wnd.abstractinfo.warFactionID ]
        for x in range(9, -1, -1):
            hilite = False
            if characterRanks:
                if characterRanks[0].currentRank == x:
                    hilite = True
            rank = util.KeyVal(currentRank=x, factionID=wnd.abstractinfo.warFactionID)
            wnd.data[TAB_HIERARCHY]['items'].append(self.GetRankEntry(rank, hilite=hilite))

    def UpdateDataCertificate(self, wnd):
        wnd.dynamicTabs.append(TAB_CERTSKILLS)
        recommendedForScrollList = self.GetRecommendedFor(wnd.abstractinfo.certificateID)
        wnd.data[TAB_CERTRECOMMENDEDFOR]['items'] += recommendedForScrollList
        wnd.data['buttons'] += [(localization.GetByLabel('UI/InfoWindow/BrowseCertificates'),
          self.ShowCharacterSheetCertificates,
          (),
          81)]

    def UpdateDataSchematic(self, wnd):
        """ PI Schematic """
        schematicTypeScrollList = self.GetSchematicTypeScrollList(wnd.abstractinfo.schematicID)
        wnd.data[TAB_PRODUCTIONINFO]['items'] += schematicTypeScrollList
        schematicAttributesScrollList = self.GetSchematicAttributes(wnd.abstractinfo.schematicID, wnd.abstractinfo.cycleTime)
        wnd.data[TAB_ATTIBUTES]['items'] += schematicAttributesScrollList

    def UpdateDataPlanetPin(self, wnd, typeID, itemID):
        banAttrs = self.GetSkillAttrs()
        if cfg.invtypes.Get(typeID).groupID == const.groupExtractorPins:
            banAttrs.extend([const.attributePinCycleTime, const.attributePinExtractionQuantity])
        if itemID is not None and sm.GetService('godma').GetItem(itemID) is not None:
            attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID, banAttrs=banAttrs)
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        else:
            attributeScrollListForType = self.GetAttributeScrollListForType(typeID=typeID, banAttrs=banAttrs)
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForType
        wnd.dynamicTabs.append(TAB_REQUIREMENTS)
        if cfg.invtypes.Get(typeID).groupID == const.groupProcessPins:
            wnd.dynamicTabs.append(TAB_SCHEMATICS)

    def UpdateDataPlanet(self, wnd, typeID, itemID, parentID):
        if sm.GetService('machoNet').GetGlobalConfig().get('enableDustLink'):
            if session.solarsystemid is not None:
                slimitem = sm.GetService('michelle').GetBallpark().GetInvItem(itemID)
                if slimitem is not None and slimitem.corpID is not None:
                    wnd.dynamicTabs.append(TAB_PLANETCONTROL)
        self.UpdateDataCelestial(wnd, typeID, itemID, parentID)

    def UpdateDataDogma(self, wnd, typeID):
        """ Dogma debugging tab, enabled by setting prefs.showdogmatab = 1 """
        container = wnd.data[TAB_DOGMA]['items']
        container.append(listentry.Get('Header', {'label': 'Type Attributes'}))
        typeattribs = cfg.dgmtypeattribs.get(typeID, [])
        tattribs = []
        for ta in typeattribs:
            v = ta.value
            a = cfg.dgmattribs.Get(ta.attributeID)
            if v is None:
                v = a.defaultValue
            tattribs.append([a.attributeID,
             a.attributeName,
             v,
             a.attributeCategory,
             a.description])

        tattribs.sort(lambda x, y: cmp(x[1], y[1]))
        for ta in tattribs:
            attributeName = ta[1]
            v = ta[2]
            attributeCategory = ta[3]
            description = ta[4]
            if attributeCategory == 7:
                v = hex(int(v))
            entryData = {'line': 1,
             'label': attributeName,
             'text': '%s<br>%s' % (v, description)}
            entry = listentry.Get('LabelTextTop', entryData)
            container.append(entry)

        container.append(listentry.Get('Header', {'label': 'Effects'}))
        teffects = []
        for te in cfg.dgmtypeeffects.get(typeID, []):
            e = cfg.dgmeffects.Get(te.effectID)
            teffects.append([e, e.effectName])

        teffects.sort(lambda x, y: cmp(x[1], y[1]))
        for e, effectName in teffects:
            entryData = {'label': effectName}
            entry = listentry.Get('Subheader', entryData)
            container.append(entry)
            for columnName in e.header:
                entryData = {'line': 1,
                 'label': columnName,
                 'text': '%s' % getattr(e, columnName)}
                entry = listentry.Get('LabelTextTop', entryData)
                container.append(entry)

    def UpdateDataConstructionPlatform(self, wnd, typeID, itemID):
        self.UpdateDataModule(wnd, typeID, itemID)
        wnd.dynamicTabs.append(TAB_MATERIALREQ)

    def UpdateDataEntity(self, wnd):
        tmp = [ each for each in sm.GetService('godma').GetType(wnd.typeID).displayAttributes if each.attributeID == const.attributeEntityKillBounty ]
        if tmp:
            wnd.Wanted(tmp[0].value, False, True, isNPC=True)

    def UpdateMarketButtons(self, wnd):
        if not wnd.typeID:
            return
        typeObj = cfg.invtypes.Get(wnd.typeID)
        if typeObj.marketGroupID:
            wnd.data['buttons'] += [(localization.GetByLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'),
              self.ShowMarketDetails,
              wnd.typeID,
              81)]
        elif typeObj.published:
            wnd.data['buttons'] += [(localization.GetByLabel('UI/Inventory/ItemActions/FindInContracts'),
              self.FindInContracts,
              wnd.typeID,
              81)]
        if industryCommon.IsBlueprintCategory(typeObj.categoryID):
            from eve.client.script.ui.shared.industry.industryWnd import Industry
            bpData = wnd.GetBlueprintData()
            wnd.data['buttons'] += [(localization.GetByLabel('UI/Industry/ViewInIndustry'),
              Industry.OpenOrShowBlueprint,
              (wnd.itemID, wnd.typeID, bpData),
              81)]

    def UpdateWindowData(self, wnd, typeID, itemID, parentID = None):
        """ 
        A method that updates the data of the show info wnd passed to it
        
        The data updated is:
        wnd.data[tabID]["items"] : listentries to beloaded for tabID
        wnd.data[tabID]["name"]  : the name of tabID
        wnd.data["buttons"]      : the bottom line buttons shown in the window
        wnd.dynamicTabs          : tabs that have an update method associated with them
        """
        invtype = cfg.invtypes.Get(typeID)
        self.UpdateMarketButtons(wnd)
        if wnd.IsType(TYPE_CHARACTER):
            self.UpdateDataCharacter(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_CORPORATION):
            self.UpdateDataCorp(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_ALLIANCE):
            self.UpdateDataAlliance(wnd)
        elif wnd.IsType(TYPE_FACTION):
            self.UpdateDataFaction(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_SHIP):
            self.UpdateDataShip(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_MODULE, TYPE_STRUCTURE, TYPE_STRUCTUREUPGRADE, TYPE_APPAREL):
            self.UpdateDataModule(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_DRONE):
            self.UpdateDataDrone(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_CUSTOMSOFFICE):
            self.UpdateDataOrbital(wnd, itemID)
        elif wnd.IsType(TYPE_SECURECONTAINER):
            self.UpdateDataSecureContainer(wnd, itemID)
        elif wnd.IsType(TYPE_CHARGE):
            self.UpdateDataCharge(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_BLUEPRINT):
            wnd.dynamicTabs.append(TAB_INDUSTRY)
        elif wnd.IsType(TYPE_STARGATE):
            self.UpdateDataStargate(wnd, itemID)
        elif wnd.IsType(TYPE_CELESTIAL):
            self.UpdateDataCelestial(wnd, typeID, itemID, parentID)
        elif wnd.IsType(TYPE_ASTEROID):
            self.UpdateDataAsteroidOrCloud(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_CONTROLTOWER):
            self.UpdateDataControlTower(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_CONSTRUCTIONPLATFORM):
            self.UpdateDataConstructionPlatform(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_REACTION):
            wnd.dynamicTabs.append(TAB_REACTION)
        elif wnd.IsType(TYPE_GENERICITEM):
            self.UpdateDataGenericItem(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_SKILL):
            self.UpdateDataSkill(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_SECURITYTAG):
            self.UpdateDataSecurityTag(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_STATION) and itemID is not None:
            self.UpdateDataStation(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_RANK) and wnd.abstractinfo is not None:
            self.UpdateDataRank(wnd)
        elif wnd.IsType(TYPE_CERTIFICATE) and wnd.abstractinfo is not None:
            self.UpdateDataCertificate(wnd)
        elif wnd.IsType(TYPE_SCHEMATIC) and wnd.abstractinfo is not None:
            self.UpdateDataSchematic(wnd)
        elif wnd.IsType(TYPE_PLANETPIN):
            self.UpdateDataPlanetPin(wnd, typeID, itemID)
        elif wnd.IsType(TYPE_PLANETCOMMODITY):
            wnd.dynamicTabs.append(TAB_PRODUCTIONINFO)
        elif wnd.IsType(TYPE_PLANET):
            self.UpdateDataPlanet(wnd, typeID, itemID, parentID)
        elif wnd.IsType(TYPE_ENTITY):
            self.UpdateDataEntity(wnd)
        elif wnd.IsType(TYPE_DEPLOYABLE):
            self.UpdateComponentData(wnd, typeID, itemID)
        if self.IsIndustryItem(typeID):
            wnd.dynamicTabs.append(TAB_ITEMINDUSTRY)
        if wnd.IsUpgradeable():
            wnd.dynamicTabs.append(TAB_UPGRADEMATERIALREQ)
        if not wnd.IsType(TYPE_FACTION):
            self.UpdateDataIllegal(wnd, typeID)
        if invtype.groupID == const.groupAgentsinSpace and sm.GetService('godma').GetType(typeID).agentID:
            self.UpdateDataAgent(wnd, typeID, itemID)
        if typeID == const.typePlasticWrap:
            attributeScrollListForItem = self.GetAttributeScrollListForItem(itemID=itemID, typeID=typeID)
            wnd.data[TAB_ATTIBUTES]['items'] += attributeScrollListForItem
        if self.IsAttributesTabShown(wnd) and not wnd.data[TAB_ATTIBUTES]['items']:
            self.UpdateAttributes(wnd)
        if prefs.GetValue('showdogmatab', 0) == 1:
            self.UpdateDataDogma(wnd, typeID)
        if wnd.IsType(TYPE_SHIP) or wnd.IsType(TYPE_DRONE):
            self.ApplyAttributeTooltip(wnd.data[TAB_ATTIBUTES]['items'])

    def IsIndustryItem(self, typeID):
        typeObj = cfg.invtypes.Get(typeID)
        if typeObj.groupID == const.groupStation:
            return False
        return typeID in cfg.invtypematerials

    def UpdateAttributes(self, wnd):
        for a in cfg.dgmattribs:
            if a.attributeID in GENERIC_ATTRIBUTES_TO_AVOID:
                continue
            try:
                invTypeScrollList = self.GetInvTypeInfo(wnd.typeID, [a.attributeID])
                wnd.data[TAB_ATTIBUTES]['items'] += invTypeScrollList
            except:
                sys.exc_clear()

        for e in cfg.dgmeffects:
            try:
                effectTypeScrollList = self.GetEffectTypeInfo(wnd.typeID, [e.effectID])
                wnd.data[TAB_ATTIBUTES]['items'] += effectTypeScrollList
            except:
                sys.exc_clear()

    def IsAttributesTabShown(self, wnd):
        noShowCatergories = (const.categoryEntity,
         const.categoryStation,
         const.categoryAncientRelic,
         const.categoryBlueprint)
        noShowGroups = (const.groupMoon,
         const.groupPlanet,
         const.groupConstellation,
         const.groupSolarSystem,
         const.groupRegion,
         const.groupLargeCollidableObject,
         const.groupCharacter,
         const.groupCorporation,
         const.groupAlliance)
        return wnd.categoryID not in noShowCatergories and wnd.groupID not in noShowGroups

    def GetInsuranceName(self, fraction):
        fraction = '%.1f' % fraction
        label = {'0.5': 'UI/Insurance/BasicInsurance',
         '0.6': 'UI/Insurance/StandardInsurance',
         '0.7': 'UI/Insurance/BronzeInsurance',
         '0.8': 'UI/Insurance/SilverInsurance',
         '0.9': 'UI/Insurance/GoldInsurance',
         '1.0': 'UI/Insurance/PlatinumInsurance'}.get(fraction, fraction)
        return localization.GetByLabel(label)

    @telemetry.ZONE_METHOD
    def GetBloodlineByTypeID(self, typeID):
        if not hasattr(self, 'bloodlines'):
            bls = {}
            for each in cfg.bloodlines:
                bls[util.LookupConstValue('bloodline%dType' % each.bloodlineID)] = each.bloodlineID

            self.bloodlines = bls
        return cfg.bloodlines.Get(self.bloodlines[typeID])

    def GetGAVFunc(self, itemID, typeID):
        """
            This returns a function for querying attributes depending on whether godma or
            client simulation of dogma knows about the item. Godma has the most accurate
            info but if it's not there then client simulation of dogma has it. Otherwise
            we fall back to the type info
        """
        info = sm.GetService('godma').GetItem(itemID)
        if info is not None:
            return lambda attributeID: getattr(info, cfg.dgmattribs.Get(attributeID).attributeName)
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        if dogmaLocation.IsItemLoaded(itemID):
            return lambda attributeID: dogmaLocation.GetAttributeValue(itemID, attributeID)
        info = sm.GetService('godma').GetStateManager().GetShipType(typeID)
        return lambda attributeID: getattr(info, cfg.dgmattribs.Get(attributeID).attributeName)

    def GetCertEntry(self, certificate, level):
        entry = {'label': certificate.GetName(),
         'level': level,
         'iconID': 'res:/UI/Texture/Classes/Certificates/level%sSmall.png' % level,
         'level': level,
         'id': ('CertEntry', '%s_%s' % (certificate.certificateID, level)),
         'certificate': certificate,
         'certID': certificate.certificateID,
         'GetSubContent': listentry.CertEntry.GetSubContent}
        return entry

    def DrillToLocation(self, systemID, constellationID, regionID):
        location = (systemID, constellationID, regionID)
        sm.GetService('sov').GetSovOverview(location)

    def GetAgentScrollGroups(self, agents, scroll):
        dudesToPrime = []
        locationsToPrime = []
        for each in agents:
            dudesToPrime.append(each.agentID)
            if each.stationID:
                locationsToPrime.append(each.stationID)
            locationsToPrime.append(each.solarsystemID)

        cfg.eveowners.Prime(dudesToPrime)
        cfg.evelocations.Prime(locationsToPrime)

        def SortFunc(level, agentID, x, y):
            if x[level] < y[level]:
                return -1
            if x[level] > y[level]:
                return 1
            xname = cfg.eveowners.Get(x[agentID]).name
            yname = cfg.eveowners.Get(y[agentID]).name
            if xname < yname:
                return -1
            if xname > yname:
                return 1
            return 0

        agents.sort(lambda x, y: SortFunc(agents.header.index('level'), agents.header.index('agentID'), x, y))
        allAgents = sm.RemoteSvc('agentMgr').GetAgents().Index('agentID')
        divisions = {}
        for each in agents:
            if allAgents[each[0]].divisionID not in divisions:
                divisions[allAgents[each[0]].divisionID] = 1

        npcDivisions = sm.GetService('agents').GetDivisions()

        def SortDivisions(npcDivisions, x, y):
            x = npcDivisions[x].divisionName.lower()
            y = npcDivisions[y].divisionName.lower()
            if x < y:
                return -1
            elif x > y:
                return 1
            else:
                return 0

        divisions = divisions.keys()
        divisions.sort(lambda x, y, npcDivisions = npcDivisions: SortDivisions(npcDivisions, x, y))
        for divisionID in divisions:
            amt = 0
            for agent in agents:
                if agent.divisionID == divisionID:
                    amt += 1

            label = localization.GetByLabel('UI/InfoWindow/AgentDivisionWithCount', divisionName=npcDivisions[divisionID].divisionName.replace('&', '&amp;'), numAgents=amt)
            data = {'GetSubContent': self.GetCorpAgentListSubContent,
             'label': label,
             'agentdata': (divisionID, agents),
             'id': ('AGENTDIVISIONS', divisionID),
             'tabs': [],
             'state': 'locked',
             'showicon': 'hide',
             'showlen': 0}
            scroll.append(listentry.Get('Group', data))

    def InitVariationBottom(self, wnd):
        btns = [localization.GetByLabel('UI/Compare/CompareButton'),
         self.CompareTypes,
         wnd,
         81,
         uiconst.ID_OK,
         0,
         0]
        btns = uicontrols.ButtonGroup(btns=[btns], parent=wnd.mainContentCont, idx=0, line=False)
        wnd.variationCompareBtn = btns
        wnd.variationCompareBtn.state = uiconst.UI_HIDDEN

    def CompareTypes(self, wnd):
        from eve.client.script.ui.shared.neocom.compare import TypeCompare
        typeWnd = TypeCompare.Open()
        typeWnd.AddEntry(wnd.variationTypeDict)

    def GetBaseWarpSpeed(self, typeID, shipinfo = None):
        defaultWSM = 1.0
        defaultBWS = 3.0
        if shipinfo:
            wsm = getattr(shipinfo, 'warpSpeedMultiplier', defaultWSM)
            bws = getattr(shipinfo, 'baseWarpSpeed', defaultBWS)
        else:
            attrTypeInfo = IndexedRows(cfg.dgmtypeattribs.get(typeID, []), ('attributeID',))
            wsm = attrTypeInfo.get(const.attributeWarpSpeedMultiplier) or util.KeyVal(value=defaultWSM)
            bws = attrTypeInfo.get(const.attributeBaseWarpSpeed) or util.KeyVal(value=defaultBWS)
            wsm = wsm.value
            bws = bws.value
        return localization.GetByLabel('UI/Fitting/FittingWindow/WarpSpeed', distText=util.FmtDist(max(1.0, bws) * wsm * const.AU, 2))

    def GetBaseDamageValue(self, typeID):
        bsd = None
        bad = None
        attrTypeInfo = IndexedRows(cfg.dgmtypeattribs.get(typeID, []), ('attributeID',))
        vals = []
        for attrID in [const.attributeEmDamage,
         const.attributeThermalDamage,
         const.attributeKineticDamage,
         const.attributeExplosiveDamage]:
            if attrID in attrTypeInfo:
                vals.append(attrTypeInfo[attrID].value)

        if len(vals) == 4:
            bsd = (vals[0] * 1.0 + vals[1] * 0.8 + vals[2] * 0.6 + vals[3] * 0.4, 69)
            bad = (vals[0] * 0.4 + vals[1] * 0.65 + vals[2] * 0.75 + vals[3] * 0.9, 68)
        return (bsd, bad)

    def GetKillsRecentKills(self, num, startIndex):
        shipKills = sm.RemoteSvc('charMgr').GetRecentShipKillsAndLosses(num, startIndex)
        return [ k for k in shipKills if k.finalCharacterID == eve.session.charid ]

    def GetKillsRecentLosses(self, num, startIndex):
        shipKills = sm.RemoteSvc('charMgr').GetRecentShipKillsAndLosses(num, startIndex)
        return [ k for k in shipKills if k.victimCharacterID == eve.session.charid ]

    def FindInContracts(self, typeID):
        sm.GetService('contracts').FindRelated(typeID, None, None, None, None, None)

    def ShowMarketDetails(self, typeID):
        uthread.new(sm.StartService('marketutils').ShowMarketDetails, typeID, None)

    def GetAllianceHistorySubContent(self, itemID):
        scrolllist = []
        allianceHistory = sm.RemoteSvc('allianceRegistry').GetEmploymentRecord(itemID)

        def AddToScroll(**data):
            scrolllist.append(listentry.Get('LabelTextTop', data))

        if len(allianceHistory) == 0:
            AddToScroll(line=True, text='', label=localization.GetByLabel('UI/InfoWindow/NoRecordsFound'), typeID=None, itemID=None)
        lastQuit = None
        for allianceRec in allianceHistory[:-1]:
            if allianceRec.allianceID is None:
                lastQuit = allianceRec.startDate
            else:
                alliance = cfg.eveowners.Get(allianceRec.allianceID)
                if allianceRec.startDate:
                    sd = util.FmtDate(allianceRec.startDate, 'ln')
                else:
                    sd = localization.GetByLabel('UI/InfoWindow/UnknownAllianceStartDate')
                if allianceRec.deleted:
                    nameTxt = localization.GetByLabel('UI/InfoWindow/AllianceClosed', allianceName=alliance.name)
                else:
                    nameTxt = alliance.name
                if lastQuit:
                    ed = util.FmtDate(lastQuit, 'ln')
                    text = localization.GetByLabel('UI/InfoWindow/InAllianceFromAndTo', allianceName=nameTxt, fromDate=sd, toDate=ed)
                else:
                    text = localization.GetByLabel('UI/InfoWindow/InAllianceFromAndToThisDay', allianceName=nameTxt, fromDate=sd)
                AddToScroll(line=True, label=localization.GetByLabel('UI/Common/Alliance'), text=text, typeID=alliance.typeID, itemID=allianceRec.allianceID)
                lastQuit = None

        if len(allianceHistory) > 1:
            scrolllist.append(listentry.Get('Divider'))
        if len(allianceHistory) >= 1:
            AddToScroll(line=True, label=localization.GetByLabel('UI/InfoWindow/CorporationFounded'), text=util.FmtDate(allianceHistory[-1].startDate, 'ln'), typeID=None, itemID=None)
        return scrolllist

    def GetWarHistorySubContent(self, itemID):
        regwars = sm.RemoteSvc('warsInfoMgr').GetWarsByOwnerID(itemID)
        facwars = []
        owners = []
        scrolllist = []
        if not util.IsAlliance(itemID) and util.IsCorporation(itemID) and sm.StartService('facwar').GetCorporationWarFactionID(itemID):
            facwars = sm.GetService('facwar').GetFactionWars(itemID).values()
        for wars in (facwars, regwars):
            for war in wars:
                if war.declaredByID not in owners:
                    owners.append(war.declaredByID)
                if war.againstID not in owners:
                    owners.append(war.againstID)

        if len(owners):
            cfg.eveowners.Prime(owners)
            cfg.corptickernames.Prime(owners)
        notStartedWars = []
        ongoingWars = []
        finishedWars = []
        for war in regwars:
            currentTime = blue.os.GetWallclockTime()
            warFinished = war.timeFinished
            timeStarted = war.timeStarted if hasattr(war, 'timeStarted') else 0
            if warFinished:
                if currentTime >= warFinished:
                    finishedWars.append(war)
                else:
                    ongoingWars.append(war)
            elif timeStarted:
                if currentTime <= timeStarted:
                    notStartedWars.append(war)
                else:
                    ongoingWars.append(war)

        if len(ongoingWars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/ActiveWars')
            warGroup = self.GetWarGroup(ongoingWars, myLabel, 'ongoingWars')
            scrolllist.append(warGroup)
        if len(facwars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/FactionalWars')
            warGroup = self.GetWarGroup(facwars, myLabel, 'factional')
            scrolllist.append(warGroup)
        if len(notStartedWars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/PendingWars')
            warGroup = self.GetWarGroup(notStartedWars, myLabel, 'notStartedWars')
            scrolllist.append(warGroup)
        if len(finishedWars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/FinishedWars')
            warGroup = self.GetWarGroup(finishedWars, myLabel, 'finished')
            scrolllist.append(warGroup)
        return scrolllist

    def GetWarGroup(self, groupItems, label, groupType):
        data = {'GetSubContent': self.GetWarSubContent,
         'label': label,
         'id': ('war', groupType, label),
         'state': 'locked',
         'BlockOpenWindow': 1,
         'showicon': 'hide',
         'showlen': 1,
         'groupName': groupType,
         'groupItems': groupItems,
         'updateOnToggle': 0}
        return listentry.Get('Group', data)

    def GetWarSubContent(self, items, *args):
        scrolllist = []
        data = util.KeyVal()
        data.label = ''
        if items.groupName == 'factional':
            for war in items.groupItems:
                data.war = war
                scrolllist.append(listentry.Get('WarEntry', data=data))

        else:
            for war in sorted(items.groupItems, key=lambda x: x.timeDeclared, reverse=True):
                data.war = war
                scrolllist.append(listentry.Get('WarEntry', data=data))

        return scrolllist

    def GetEmploymentHistorySubContent(self, itemID):
        scrolllist = []
        employmentHistory = sm.RemoteSvc('corporationSvc').GetEmploymentRecord(itemID)
        nextDate = None
        corpIDsToPrime = {j.corporationID for j in employmentHistory}
        cfg.eveowners.Prime(corpIDsToPrime)
        for job in employmentHistory:
            corp = cfg.eveowners.Get(job.corporationID)
            if job.deleted:
                nameText = localization.GetByLabel('UI/InfoWindow/CorporationClosed', corpName=corp.name)
            else:
                nameText = corp.name
            date = util.FmtDate(job.startDate, 'ls')
            if nextDate is None:
                text = localization.GetByLabel('UI/InfoWindow/InCorpFromAndToThisDay', corpName=nameText, fromDate=date)
            else:
                text = localization.GetByLabel('UI/InfoWindow/InCorpFromAndTo', corpName=nameText, fromDate=date, toDate=nextDate)
            nextDate = date
            scrolllist.append(listentry.Get('LabelTextTop', {'line': True,
             'label': localization.GetByLabel('UI/Common/Corporation'),
             'text': text,
             'typeID': corp.typeID,
             'itemID': job.corporationID}))

        return scrolllist

    def GetAllianceMembersSubContent(self, itemID):
        members = sm.RemoteSvc('allianceRegistry').GetAllianceMembers(itemID)
        cfg.eveowners.Prime([ m.corporationID for m in members ])
        scrolllist = []
        for m in members:
            corp = cfg.eveowners.Get(m.corporationID)
            data = {'line': True,
             'label': localization.GetByLabel('UI/Common/Corporation'),
             'text': corp.name,
             'typeID': corp.typeID,
             'itemID': m.corporationID}
            scrolllist.append(listentry.Get('LabelTextTop', data))

        return scrolllist

    def GetCorpAgentListSubContent(self, tmp, *args):
        divisionID, agents = tmp.agentdata
        scrolllist = []
        scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/AvailableToYou')}))
        noadd = 1
        for agent in agents:
            if agent.divisionID != divisionID:
                continue
            isLimitedToFacWar = False
            if agent.agentTypeID == const.agentTypeFactionalWarfareAgent and sm.StartService('facwar').GetCorporationWarFactionID(agent.corporationID) != session.warfactionid:
                isLimitedToFacWar = True
            if sm.GetService('standing').CanUseAgent(agent.factionID, agent.corporationID, agent.agentID, agent.level, agent.agentTypeID) and isLimitedToFacWar == False:
                scrolllist.append(listentry.Get('AgentEntry', {'charID': agent.agentID,
                 'defaultDivisionID': agent.divisionID}))
                noadd = 0

        if noadd:
            scrolllist.pop(-1)
        scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/NotAvailableToYou')}))
        noadd = 1
        for agent in agents:
            if agent.divisionID != divisionID:
                continue
            isLimitedToFacWar = False
            if agent.agentTypeID == const.agentTypeFactionalWarfareAgent and sm.StartService('facwar').GetCorporationWarFactionID(agent.corporationID) != session.warfactionid:
                isLimitedToFacWar = True
            if not sm.GetService('standing').CanUseAgent(agent.factionID, agent.corporationID, agent.agentID, agent.level, agent.agentTypeID) or isLimitedToFacWar == True:
                scrolllist.append(listentry.Get('AgentEntry', {'charID': agent.agentID,
                 'defaultDivisionID': agent.divisionID}))
                noadd = 0

        if noadd:
            scrolllist.pop(-1)
        return scrolllist

    def __GetIllegalityString(self, illegality):
        textList = []
        if illegality.standingLoss > 0.0:
            t = localization.GetByLabel('UI/InfoWindow/StandingLoss', standingLoss=illegality.standingLoss)
            textList.append(t)
        if illegality.confiscateMinSec <= 1.0:
            t = localization.GetByLabel('UI/InfoWindow/ConfiscationInSec', confiscateMinSec=max(illegality.confiscateMinSec, 0.0))
            textList.append(t)
        if illegality.fineByValue > 0.0:
            t = localization.GetByLabel('UI/InfoWindow/FineOfEstimatedMarketValue', fine=illegality.fineByValue * 100.0)
            textList.append(t)
        if illegality.attackMinSec <= 1.0:
            t = localization.GetByLabel('UI/InfoWindow/AttackInSec', attackMinSec=max(illegality.attackMinSec, 0.0))
            textList.append(t)
        if len(textList) > 0:
            text = ' / '.join(textList)
        else:
            text = ''
        return text

    def GetInvTypeInfo(self, typeID, attrList):
        scrolllist = []
        invTypeInfo = cfg.invtypes.Get(typeID)
        for attrID in attrList:
            attrTypeInfo = cfg.dgmattribs.Get(attrID)
            value = self.FilterZero(getattr(invTypeInfo, attrTypeInfo.attributeName, None))
            if value is None:
                continue
            if not attrTypeInfo.published:
                continue
            if attrID == const.attributeVolume:
                packagedVolume = GetTypeVolume(typeID, 1)
                if value != packagedVolume:
                    text = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=value, packaged=packagedVolume, unit=FormatUnit(attrTypeInfo.unitID))
                else:
                    formatedValue = FormatValue(value, const.attributeVolume)
                    text = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=FormatUnit(attrTypeInfo.unitID))
            else:
                formatedValue = localization.formatters.FormatNumeric(value, useGrouping=True)
                text = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=FormatUnit(attrTypeInfo.unitID))
            scrolllist.append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': attrTypeInfo.displayName,
             'text': text,
             'iconID': attrTypeInfo.iconID}))

        return scrolllist

    def GetMetaParentTypeID(self, typeID):
        parentTypeID = None
        if typeID in cfg.invmetatypesByParent:
            parentTypeID = typeID
        elif typeID in cfg.invmetatypes:
            parentTypeID = cfg.invmetatypes.Get(typeID).parentTypeID
        return parentTypeID

    def GetTypesSortedByMetaScrollList(self, invTypeInfo):
        scrolllist = []
        variationTypeDict = []
        sortByGroupID = {}
        sortHeaders = []
        if invTypeInfo:
            for each in invTypeInfo:
                if each.metaGroupID not in sortByGroupID:
                    sortByGroupID[each.metaGroupID] = []
                    sortHeaders.append((each.metaGroupID, each.metaGroupID))
                invType = cfg.invtypes.Get(each.typeID)
                metaLevel = sm.GetService('godma').GetTypeAttribute(each.typeID, const.attributeMetaLevel, 0)
                sortByGroupID[each.metaGroupID].append((metaLevel, each, invType))

        sortHeaders = uiutil.SortListOfTuples(sortHeaders)
        for i, metaGroupID in enumerate(sortHeaders):
            sub = sortByGroupID[metaGroupID]
            sub = sorted(sub, key=lambda (metaLvl, _, typeObj): (metaLvl, typeObj.name))
            if i > 0:
                scrolllist.append(listentry.Get('Divider'))
            scrolllist.append(listentry.Get('Header', {'line': metaGroupID,
             'label': cfg.invmetagroups.Get(metaGroupID).name,
             'text': None}))
            for _, _, invType in sub:
                variationTypeDict.append(invType)
                scrolllist.append(listentry.Get('Item', {'GetMenu': None,
                 'itemID': None,
                 'typeID': invType.typeID,
                 'label': invType.typeName,
                 'getIcon': 1}))

        return (scrolllist, variationTypeDict)

    def GetMetaTypeInfo(self, typeID):
        invTypeInfo = self.GetMetaTypesFromTypeID(typeID)
        return self.GetTypesSortedByMetaScrollList(invTypeInfo)

    def GetMetaTypesFromTypeID(self, typeID, groupOnly = 0):
        tmp = None
        if typeID in cfg.invmetatypesByParent:
            tmp = copy.deepcopy(cfg.invmetatypesByParent[typeID])
        grp = cfg.invmetagroups.Get(1)
        if not tmp:
            if typeID in cfg.invmetatypes:
                tmp = cfg.invmetatypes.Get(typeID)
            if tmp:
                grp = cfg.invmetagroups.Get(tmp.metaGroupID)
                tmp = self.GetMetaTypesFromTypeID(tmp.parentTypeID)
        else:
            metaGroupID = tmp[0].metaGroupID
            if metaGroupID != 14:
                metaGroupID = 1
            else:
                grp = cfg.invmetagroups.Get(14)
            tmp.append(blue.DBRow(tmp.header, [tmp[0].parentTypeID, tmp[0].parentTypeID, metaGroupID]))
        if groupOnly:
            return grp
        else:
            return tmp

    def GetAttributeScrollListForItem(self, itemID, typeID, attrList = None, banAttrs = []):
        info = sm.GetService('godma').GetItem(itemID)
        if info:
            attributeDict = self.GetAttributeDictForItem(itemID, typeID)
            typeVolume = GetTypeVolume(typeID, 1)
            attrVolume = attributeDict.get(const.attributeVolume, None)
            if isinstance(attrVolume, (int, float, long)) and attrVolume != typeVolume:
                attributeDict[const.attributeVolume] = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=attributeDict[const.attributeVolume], packaged=typeVolume, unit=FormatUnit(const.unitVolume))
            scrolllist = self.GetAttributeScrollListFromAttributeDict(attrdict=attributeDict, attrList=attrList, banAttrs=banAttrs, itemID=itemID, typeID=typeID)
            return scrolllist
        else:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            if dogmaLocation.IsItemLoaded(itemID):
                attributeDict = self.GetAttributeDictForType(typeID)
                attributeDict.update(dogmaLocation.GetDisplayAttributes(itemID, attributeDict.keys()))
                scrolllist = self.GetAttributeScrollListFromAttributeDict(attrdict=attributeDict, attrList=attrList, banAttrs=banAttrs, itemID=itemID, typeID=typeID)
                return scrolllist
            scrolllist = self.GetAttributeScrollListForType(typeID=typeID, attrList=attrList, banAttrs=banAttrs, itemID=itemID)
            return scrolllist

    def GetSpaceComponentAttrItemInfo(self, typeID, itemID):
        scrolllist = []
        attributeCollection = {}
        componentInstances = {}
        componentNames = cfg.spaceComponentStaticData.GetComponentNamesForType(typeID)
        if len(componentNames) == 0:
            return scrolllist
        if itemID:
            ballpark = sm.GetService('michelle').GetBallpark()
            if ballpark:
                try:
                    componentInstances = ballpark.componentRegistry.GetComponentsByItemID(itemID)
                except KeyError:
                    pass

        godmaService = sm.GetService('godma')
        for componentName in componentNames:
            try:
                componentClass = factory.GetComponentClass(componentName)
                if hasattr(componentClass, 'GetAttributeInfo'):
                    instance = componentInstances.get(componentName)
                    attributes = cfg.spaceComponentStaticData.GetAttributes(typeID, componentName)
                    attributeList = componentClass.GetAttributeInfo(godmaService, typeID, attributes, instance, localization)
                    attributeCollection[componentName] = attributeList
            except KeyError:
                pass

        for attributeList in IterAttributeCollectionInInfoOrder(attributeCollection):
            for entryClass, entryData in attributeList:
                scrolllist.append(listentry.Get(entryClass, entryData))

        return scrolllist

    def GetAttributesSuppressedByComponents(self, typeID):
        componentNames = cfg.spaceComponentStaticData.GetComponentNamesForType(typeID)
        suppressedAttributeIDs = []
        for componentName in componentNames:
            componentClass = factory.GetComponentClass(componentName)
            if hasattr(componentClass, 'GetSuppressedDogmaAttributeIDs'):
                suppressedAttributeIDs.extend(componentClass.GetSuppressedDogmaAttributeIDs())

        return suppressedAttributeIDs

    def GetAttributeScrollListForType(self, typeID, attrList = None, attrValues = None, banAttrs = [], itemID = None):
        attributeDict = self.GetAttributeDictForType(typeID)
        scrolllist = self.GetAttributeScrollListFromAttributeDict(attrdict=attributeDict, attrList=attrList, attrValues=attrValues, banAttrs=banAttrs, itemID=itemID, typeID=typeID)
        return scrolllist

    def GetAttributeRows(self, tryAddAttributeIDs, attrdict, itemID):
        newScrollEntries = []
        attributeListInfo = [(0, const.damageTypeAttributes, 'UI/Common/Damage'),
         (1, const.damageResistanceBonuses, 'UI/Inflight/ModuleRacks/Tooltips/DamageResistanceBonuses'),
         (2, const.hullDamageTypeResonanceAttributes, 'UI/Inflight/ModuleRacks/Tooltips/HullDamageResistanceHeader'),
         (3, const.armorDamageTypeResonanceAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader'),
         (4, const.shieldDamageTypeResonanceAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ShieldDamageResistanceHeader'),
         (5, const.sensorStrength, 'UI/Inflight/ModuleRacks/Tooltips/SensorStrength'),
         (6, const.sensorStrengthPercentAttrs, 'UI/Inflight/ModuleRacks/Tooltips/SensorStrength'),
         (7, const.sensorStrengthBonusAttrs, 'UI/Inflight/ModuleRacks/Tooltips/SensorStrengthBonuses')]
        allGroupedAttributes = []
        for attributeGroup in attributeListInfo:
            allGroupedAttributes += attributeGroup[1]

        attributesAdded = []
        for eachAttributeID in tryAddAttributeIDs:
            if eachAttributeID not in allGroupedAttributes or eachAttributeID in attributesAdded:
                continue
            for eachAttributeListInfo in attributeListInfo:
                sortIdx, eachAttributeList, textPath = eachAttributeListInfo
                if eachAttributeID not in eachAttributeList:
                    continue
                allAttributes = []
                for xID in eachAttributeList:
                    value = attrdict.get(xID, 0)
                    formatInfo = GetFormattedAttributeAndValue(xID, value)
                    if formatInfo:
                        formatValue = formatInfo.value
                    else:
                        formatValue = None
                    allAttributes.append((xID, formatValue))

                validValues = filter(None, [ a[1] for a in allAttributes ])
                if not validValues:
                    continue
                data = {'labelPath': textPath,
                 'attributeValues': allAttributes,
                 'attributeIDs': [ a[0] for a in allAttributes ],
                 'OnClickAttr': lambda attributeID: self.OnAttributeClick(attributeID, itemID)}
                entry = listentry.Get(decoClass=AttributeRowEntry, data=data)
                newScrollEntries.append((sortIdx, entry))
                attributesAdded += eachAttributeList
                break

        newScrollEntries = uiutil.SortListOfTuples(newScrollEntries)
        return (newScrollEntries, attributesAdded)

    def GetAttributeScrollListFromAttributeDict(self, attrdict, attrList = None, attrValues = None, banAttrs = [], itemID = None, typeID = None):
        scrolllist = []
        if attrValues:
            for each in attrValues.displayAttributes:
                attrdict[each.attributeID] = each.value

        attrList = attrList or attrdict.keys()
        aggregateAttributes = defaultdict(list)
        for attrID in tuple(attrList):
            if attrID in const.canFitShipGroups or attrID in const.canFitShipTypes:
                dgmType = cfg.dgmattribs.Get(attrID)
                value = GetFormatAndValue(dgmType, attrdict[attrID])
                aggregateAttributes['canFitShip'].append(value)
                attrList.remove(attrID)

        order = self.GetAttributeOrder()
        tryAddAttributeIDs = []
        for attrID_ in order:
            if attrID_ in attrList and attrID_ not in banAttrs:
                tryAddAttributeIDs.append(attrID_)

        for attrID_ in attrList:
            if attrID_ not in order and attrID_ not in banAttrs:
                tryAddAttributeIDs.append(attrID_)

        newAttributeRows, attributesAddedInRows = self.GetAttributeRows(tryAddAttributeIDs, attrdict, itemID)

        def TryAddAttributeEntry(attrID):
            if attrID not in attrdict:
                return
            listItem = self.GetEntryForAttribute(attrID, attrdict[attrID], itemID, typeID=typeID)
            if listItem:
                scrolllist.append(listItem)

        for attrID_ in tryAddAttributeIDs:
            if attrID_ not in attributesAddedInRows:
                TryAddAttributeEntry(attrID_)

        attributeValues = aggregateAttributes.get('canFitShip')
        if attributeValues is not None:
            attrID = const.canFitShipTypes[0]
            attributeInfo = cfg.dgmattribs.Get(attrID)
            attributeValues = localization.util.Sort(attributeValues)
            listItem = listentry.Get('LabelMultilineTextTop', {'attributeID': attrID,
             'OnClick': (self.OnAttributeClick, attrID, itemID),
             'line': 1,
             'label': attributeInfo.displayName,
             'text': '<br>'.join(attributeValues),
             'iconID': attributeInfo.iconID,
             'typeID': None,
             'itemID': itemID})
            scrolllist.append(listItem)
        scrolllist += newAttributeRows
        return scrolllist

    def GetAttributeDictForItem(self, itemID, typeID):
        attributeDict = self.GetAttributeDictForType(typeID)
        if not itemID:
            return attributeDict
        itemAttributesDict = self.AddDisplayAttributesForItem(itemID)
        attributeDict.update(itemAttributesDict)
        return attributeDict

    def GetAttributeDictForType(self, typeID):
        ret = {}
        for each in cfg.dgmtypeattribs.get(typeID, []):
            attribute = cfg.dgmattribs.Get(each.attributeID)
            if attribute.attributeCategory == 9:
                ret[each.attributeID] = getattr(cfg.invtypes.Get(typeID), attribute.attributeName)
            else:
                ret[each.attributeID] = each.value

        invType = cfg.invtypes.Get(typeID)
        if const.attributeCapacity not in ret and invType.capacity:
            ret[const.attributeCapacity] = invType.capacity
        if invType.categoryID in (const.categoryCharge, const.categoryModule):
            if const.attributeVolume not in ret and invType.volume:
                formatedValue = localization.formatters.FormatNumeric(invType.volume, useGrouping=True)
                value = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=FormatUnit(const.unitVolume))
                ret[const.attributeVolume] = value
        if invType.categoryID in (const.categoryPlanetaryInteraction, const.categoryShip, const.categoryDrone):
            if const.attributeVolume not in ret and invType.volume:
                value = localization.GetByLabel('UI/InfoWindow/ItemVolume', volume=invType.volume, unit=FormatUnit(const.unitVolume))
                packagedVolume = GetTypeVolume(typeID, 1)
                if invType.volume != packagedVolume:
                    unit = FormatUnit(const.unitVolume)
                    value = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=invType.volume, packaged=packagedVolume, unit=unit)
                ret[const.attributeVolume] = value
        if invType.categoryID in (const.categoryShip, const.categoryDrone):
            if const.attributeMass not in ret and invType.mass:
                ret[const.attributeMass] = invType.mass
        displayAttributes = self.AddDisplayAttributesForType(typeID)
        ret.update(displayAttributes)
        return ret

    def AddDisplayAttributesForType(self, typeID):
        ret = {}
        attrInfo = sm.GetService('godma').GetType(typeID)
        for each in attrInfo.displayAttributes:
            ret[each.attributeID] = each.value

        return ret

    def AddDisplayAttributesForItem(self, itemID):
        ret = {}
        attrInfo = sm.GetService('godma').GetItem(itemID)
        if not attrInfo:
            return ret
        for each in attrInfo.displayAttributes:
            ret[each.attributeID] = each.value

        return ret

    def GetEntryForAttribute(self, attributeID, value, itemID = None, typeID = None):
        listItem = self.GetStatusBarEntryForAttribute(attributeID, itemID=itemID, typeID=typeID)
        if listItem:
            return listItem
        formatInfo = GetFormattedAttributeAndValue(attributeID, value)
        if not formatInfo:
            return
        if itemID and formatInfo.infoTypeID and typeID != formatInfo.infoTypeID:
            itemID = None
        listItem = listentry.Get(decoClass=listentry.LabelTextSides, data={'attributeID': attributeID,
         'OnClick': (self.OnAttributeClick, attributeID, itemID),
         'line': 1,
         'label': formatInfo.displayName,
         'text': formatInfo.value,
         'iconID': formatInfo.iconID,
         'typeID': formatInfo.infoTypeID,
         'itemID': itemID})
        return listItem

    def OnAttributeClick(self, id_, itemID):
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if not ctrl:
            return
        if not shift and itemID is not None and (itemID >= const.minPlayerItem or util.IsCharacter(itemID)):
            sm.GetService('godma').LogAttribute(itemID, id_)
        if eve.session.role & service.ROLE_CONTENT == service.ROLE_CONTENT and ctrl and shift:
            self.GetUrlAdamDogmaAttribute(id_)

    def GetUrlAdamDogmaAttribute(self, id_):
        uthread.new(self.ClickURL, 'http://adam:50001/gd/type.py?action=DogmaModifyAttributeForm&attributeID=%s' % id_)

    def ClickURL(self, url, *args):
        blue.os.ShellExecute(url)

    def GetSkillAttrs(self):
        skillAttrs = [ getattr(const, 'attributeRequiredSkill%s' % i, None) for i in xrange(1, 7) if hasattr(const, 'attributeRequiredSkill%s' % i) ] + [ getattr(const, 'attributeRequiredSkill%sLevel' % i, None) for i in xrange(1, 7) if hasattr(const, 'attributeRequiredSkill%sLevel' % i) ]
        return skillAttrs

    def GetSchematicAttributes(self, schematicID, cycleTime):
        scrolllist = []
        time = util.FmtTimeInterval(cycleTime * const.SEC, 'minute')
        scrolllist.append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
         'label': localization.GetByLabel('UI/PI/Common/CycleTime'),
         'text': time,
         'iconID': 1392}))
        scrolllist.append(listentry.Get('Header', data=util.KeyVal(label=localization.GetByLabel('UI/InfoWindow/CanBeUsedOnPinTypes'))))
        pinTypes = []
        for pinRow in cfg.schematicspinmap.get(schematicID, []):
            typeName = cfg.invtypes.Get(pinRow.pinTypeID).typeName
            data = util.KeyVal(label=typeName, typeID=pinRow.pinTypeID, itemID=None, getIcon=1)
            pinTypes.append((data.label, listentry.Get('Item', data=data)))

        pinTypes = uiutil.SortListOfTuples(pinTypes)
        return scrolllist + pinTypes

    def GetSchematicTypeScrollList(self, schematicID):
        scrolllist = []
        inputs = []
        outputs = []
        for typeInfo in cfg.schematicstypemap.get(schematicID, []):
            label = localization.GetByLabel('UI/InfoWindow/TypeNameWithNumUnits', invType=typeInfo.typeID, qty=typeInfo.quantity)
            data = util.KeyVal(label=label, typeID=typeInfo.typeID, itemID=None, getIcon=1, quantity=typeInfo.quantity)
            if typeInfo.isInput:
                inputs.append(data)
            else:
                outputs.append(data)

        scrolllist.append(listentry.Get('Header', data=util.KeyVal(label=localization.GetByLabel('UI/PI/Common/SchematicInput'))))
        for data in inputs:
            scrolllist.append(listentry.Get('Item', data=data))

        scrolllist.append(listentry.Get('Header', data=util.KeyVal(label=localization.GetByLabel('UI/PI/Common/Output'))))
        for data in outputs:
            scrolllist.append(listentry.Get('Item', data=data))

        return scrolllist

    def GetReqSkillInfo(self, typeID, reqSkills = [], showPrereqSkills = True):
        scrolllist = []
        i = 1
        commands = []
        skills = None
        if typeID is not None:
            skills = sm.GetService('skills').GetRequiredSkills(typeID).items()
        if reqSkills:
            skills = reqSkills
        if skills is None:
            return
        for skillID, lvl in skills:
            ret = self.DrawSkillTree(skillID, lvl, scrolllist, 0, showPrereqSkills=showPrereqSkills)
            commands += ret
            i += 1

        cmds = {}
        for typeID, level in commands:
            typeID, level = int(typeID), int(level)
            currentLevel = cmds.get(typeID, 0)
            cmds[typeID] = max(currentLevel, level)

        if i > 1 and eve.session.role & service.ROLE_GMH == service.ROLE_GMH:
            scrolllist.append(listentry.Get('Button', {'label': 'GMH: Give me these skills',
             'caption': 'Give',
             'OnClick': self.DoGiveSkills,
             'args': (cmds,)}))
        return scrolllist

    def GetRecommendedFor(self, certID):
        recommendedFor = sm.StartService('certificates').GetCertificateRecommendationsFromCertificateID(certID)
        recommendedGroups = {}
        for typeID in recommendedFor:
            groupID = cfg.invtypes.Get(typeID).groupID
            current = recommendedGroups.get(groupID, [])
            current.append(typeID)
            recommendedGroups[groupID] = current

        scrolllist = []
        for groupID, value in recommendedGroups.iteritems():
            label = cfg.invgroups.Get(groupID).name
            data = {'GetSubContent': self.GetEntries,
             'label': label,
             'groupItems': value,
             'id': ('cert_shipGroups', groupID),
             'sublevel': 0,
             'showlen': 1,
             'showicon': 'hide',
             'state': 'locked'}
            scrolllist.append((label, listentry.Get('Group', data)))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        return scrolllist

    def GetEntries(self, data, *args):
        scrolllist = []
        for typeID in data.groupItems:
            entry = self.CreateEntry(typeID)
            scrolllist.append(entry)

        return scrolllist

    def CreateEntry(self, typeID, *args):
        entry = util.KeyVal()
        entry.line = 1
        entry.label = cfg.invtypes.Get(typeID).name
        entry.sublevel = 1
        entry.showinfo = 1
        entry.typeID = typeID
        entry.getIcon = True
        return listentry.Get(decoClass=listentry.Item, data=entry)

    def DoGiveSkills(self, cmds, button):
        cntFrom = 1
        cntTo = len(cmds) + 1
        sm.GetService('loading').ProgressWnd('GM Skill Gift', '', cntFrom, cntTo)
        for typeID, level in cmds.iteritems():
            invType = cfg.invtypes.Get(typeID)
            cntFrom = cntFrom + 1
            sm.GetService('loading').ProgressWnd('GM Skill Gift', 'Training of the skill %s to level %d has been completed' % (invType.typeName, level), cntFrom, cntTo)
            sm.RemoteSvc('slash').SlashCmd('/giveskill me %s %s' % (typeID, level))

        sm.GetService('loading').ProgressWnd('Done', '', cntTo, cntTo)

    def DoRemoveSkill(self, typeID):
        sm.RemoteSvc('slash').SlashCmd('/removeskill me %s' % typeID)
        sm.GetService('gameui').Say('Skill %s has been removed' % cfg.invtypes.Get(typeID).name)

    def GetGMGiveSkillMenu(self, typeID):
        subMenu = (('Remove', self.DoRemoveSkill, (typeID,)),
         ('1', self.DoGiveSkills, ({typeID: 1}, None)),
         ('2', self.DoGiveSkills, ({typeID: 2}, None)),
         ('3', self.DoGiveSkills, ({typeID: 3}, None)),
         ('4', self.DoGiveSkills, ({typeID: 4}, None)),
         ('5', self.DoGiveSkills, ({typeID: 5}, None)))
        return (('GM: Modify skill level', subMenu), ('GM: typeID: %s' % typeID, blue.pyos.SetClipboardData, (str(typeID),)))

    def DoCreateMaterials(self, commands, header = 'GML: Create in cargo', qty = 10, button = None):
        runs = {'qty': qty}
        if qty > 1:
            runs = uix.QtyPopup(100000, 1, qty, None, header)
        if runs is not None and runs.has_key('qty') and runs['qty'] > 0:
            cntFrom = 1
            cntTo = len(commands) + 1
            sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Common/GiveLoot'), '', cntFrom, cntTo)
            for typeID, quantity in commands:
                invType = cfg.invtypes.Get(typeID)
                cntFrom = cntFrom + 1
                actualQty = quantity * runs['qty']
                qtyText = '%(quantity)s items(s) of %(typename)s' % {'quantity': quantity * runs['qty'],
                 'typename': invType.typeName}
                sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Common/GiveLoot'), qtyText, cntFrom, cntTo)
                if actualQty > 0:
                    if session.role & service.ROLE_WORLDMOD:
                        sm.RemoteSvc('slash').SlashCmd('/create %s %d' % (typeID, actualQty))
                    elif session.role & service.ROLE_GML:
                        sm.RemoteSvc('slash').SlashCmd('/load me %s %d' % (typeID, actualQty))

            sm.GetService('loading').ProgressWnd('Done', '', cntTo, cntTo)

    def DrawSkillTree(self, typeID, lvl, scrolllist, indent, done = None, firstID = None, showPrereqSkills = True):
        thisSet = [(typeID, lvl)]
        if done is None:
            done = []
        if firstID is None:
            firstID = typeID
        data = {'line': 1,
         'typeID': typeID,
         'lvl': lvl,
         'indent': indent + 1,
         'hint': sm.GetService('skills').GetSkillToolTip(typeID, lvl),
         'origin': ORIGIN_SHOWINFO}
        scrolllist.append(listentry.Get(settings=data, decoClass=listentry.SkillTreeEntry))
        done.append(typeID)
        current = typeID
        if showPrereqSkills:
            for typeID, lvl in sm.GetService('skills').GetRequiredSkills(typeID).iteritems():
                if typeID == current:
                    log.LogWarn('Here I have skill which has it self as required skill... skillTypeID is ' + str(typeID))
                    continue
                newSet = self.DrawSkillTree(typeID, lvl, scrolllist, indent + 1, done, firstID)
                thisSet = thisSet + newSet

        return thisSet

    def GetEffectTypeInfo(self, typeID, effList):
        scrolllist = []
        thisTypeEffects = cfg.dgmtypeeffects.get(typeID, [])
        for effectID in effList:
            itemDgmEffect = self.TypeHasEffect(effectID, thisTypeEffects)
            if not itemDgmEffect:
                continue
            effTypeInfo = cfg.dgmeffects.Get(effectID)
            if effTypeInfo.published:
                scrolllist.append(listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
                 'label': effTypeInfo.displayName,
                 'text': effTypeInfo.description,
                 'iconID': effTypeInfo.iconID}))

        return scrolllist

    def FilterZero(self, value):
        if value == 0:
            return None
        return value

    def TypeHasEffect(self, effectID, itemEffectTypeInfo = None, typeID = None):
        if itemEffectTypeInfo is None:
            itemEffectTypeInfo = cfg.dgmtypeeffects.get(typeID, [])
        for itemDgmEffect in itemEffectTypeInfo:
            if itemDgmEffect.effectID == effectID:
                return itemDgmEffect

        return 0

    def GetStandingsHistorySubContent(self, itemID):
        return sm.GetService('standing').GetStandingRelationshipEntries(itemID)

    def SetDestination(self, itemID):
        sm.StartService('starmap').SetWaypoint(itemID, clearOtherWaypoints=True)

    def Bookmark(self, itemID, typeID, parentID, *args):
        sm.GetService('addressbook').BookmarkLocationPopup(itemID, typeID, parentID)

    def GetColorCodedSecurityStringForSystem(self, solarsystemID, itemName):
        sec, col = util.FmtSystemSecStatus(self.map.GetSecurityStatus(solarsystemID), 1)
        col.a = 1.0
        color = util.StrFromColor(col)
        text = '<color=%s>%s</color><t>%s' % (color, sec, itemName)
        return text
