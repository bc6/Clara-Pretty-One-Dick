#Embedded file name: eve/client/script/ui/inflight\capitalnavigation.py
import uiprimitives
import uicontrols
import uix
import uiutil
from eve.client.script.ui.control import entries as listentry
import util
import uthread
import blue
import carbonui.const as uiconst
import localization

class CapitalNav(uicontrols.Window):
    __guid__ = 'form.CapitalNav'
    __notifyevents__ = ['OnSessionChanged']
    default_windowID = 'capitalnav'
    default_captionLabelPath = 'UI/CapitalNavigation/CapitalNavigationWindow/CapitalNavigationLabel'
    default_iconNum = 'res:/ui/Texture/WindowIcons/capitalNavigation.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'station_inflight'
        self.soldict = {}
        self.sr.main = uiutil.GetChild(self, 'main')
        self.SetWndIcon(self.iconNum, mainTop=-5)
        self.SetMinSize([350, 200])
        uicontrols.WndCaptionLabel(text=localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/CapitalNavigationLabel'), subcaption=localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/OnlinedStarbaseMessage'), parent=self.sr.topParent, align=uiconst.RELATIVE)
        self.sr.scroll = uicontrols.Scroll(name='scroll', parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.settingsParent = uiprimitives.Container(name='settingsParent', parent=self.sr.main, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, idx=1, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), clipChildren=1)
        maintabs = [[localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/JumpTo'),
          self.sr.scroll,
          self,
          'jumpto',
          self.sr.scroll], [localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/WithinRange'),
          self.sr.scroll,
          self,
          'inrange',
          self.sr.scroll]]
        shipID = util.GetActiveShip()
        if shipID and sm.GetService('clientDogmaIM').GetDogmaLocation().GetItem(shipID).groupID == const.groupTitan:
            maintabs.insert(1, [localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/BridgeTo'),
             self.sr.scroll,
             self,
             'bridgeto',
             self.sr.scroll])
        self.sr.maintabs = uicontrols.TabGroup(name='tabparent', parent=self.sr.main, idx=0, tabs=maintabs, groupID='capitaljumprangepanel')

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid' in change:
            self.sr.showing = ''
            self.sr.maintabs.ReloadVisible()

    def _OnClose(self, *args):
        self.soldict = {}

    def Load(self, args):
        self.sr.scroll.sr.id = 'capitalnavigationscroll'
        if args == 'inrange':
            self.ShowInRangeTab()
        elif args == 'jumpto':
            self.ShowJumpBridgeToTab()
        elif args == 'bridgeto':
            self.ShowJumpBridgeToTab(1)
        elif args == 'settings':
            self.ShowSettingsTab()

    def GetSolarSystemsInRange_thread(self, solarSystemID):
        shipID = util.GetActiveShip()
        if not shipID:
            return
        self.sr.scroll.Load(contentList=[], noContentHint=localization.GetByLabel('UI/Common/GettingData'))
        jumpDriveRange, consumptionType, consumptionAmount = self.GetJumpDriveInfo(shipID)
        inRange = set()
        soldict = self.soldict.get(solarSystemID, None)
        for solID, solData in cfg.mapSystemCache.iteritems():
            if session.solarsystemid2 != solID and solData.securityStatus <= const.securityClassLowSec:
                distance = uix.GetLightYearDistance(solarSystemID, solID, False)
                if distance is not None and distance <= jumpDriveRange:
                    inRange.add(solID)
            self.soldict[solarSystemID] = inRange
        else:
            inRange = soldict

        scrolllist = []
        if inRange:
            for solarSystemID in inRange:
                blue.pyos.BeNice()
                if not self or self.destroyed:
                    return
                requiredQty, requiredType = self.GetFuelConsumptionForMyShip(session.solarsystemid2, solarSystemID, consumptionType, consumptionAmount)
                entry = self.GetSolarSystemBeaconEntry(solarSystemID, requiredQty, requiredType, jumpDriveRange)
                if entry:
                    scrolllist.append(entry)

        if not len(scrolllist):
            self.sr.scroll.ShowHint(localization.GetByLabel('UI/Common/NothingFound'))
        if self.sr.scroll and scrolllist and self.sr.Get('showing', None) == 'inrange':
            self.sr.scroll.ShowHint('')
            self.sr.scroll.Load(contentList=scrolllist, headers=[localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'),
             localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/SecurityColumnHeader'),
             localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/FuelColumnHeader'),
             localization.GetByLabel('UI/Common/Volume'),
             localization.GetByLabel('UI/Common/Distance'),
             localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/JumpTo')])

    def ShowInRangeTab(self):
        if not util.GetActiveShip():
            return None
        if self.sr.Get('showing', '') != 'inrange':
            self.sr.scroll.Load(contentList=[], noContentHint=localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/CalculatingStellarDistancesMessage'))
            uthread.pool('form.CapitalNav::ShowInRangeTab', self.GetSolarSystemsInRange_thread, session.solarsystemid2)
            self.sr.showing = 'inrange'

    def ShowJumpBridgeToTab(self, isBridge = False):
        allianceBeacons = [] if eve.session.allianceid is None else sm.RemoteSvc('map').GetAllianceBeacons()
        showing = 'UI/CapitalNavigation/CapitalNavigationWindow/BridgeTo' if isBridge else 'UI/CapitalNavigation/CapitalNavigationWindow/JumpTo'
        if self.sr.Get('showing', '') != showing:
            scrolllist = []
            shipID = util.GetActiveShip()
            if shipID:
                jumpDriveRange, consumptionType, consumptionAmount = self.GetJumpDriveInfo(shipID)
                for allianceBeacon in allianceBeacons:
                    solarSystemID, structureID, structureTypeID = allianceBeacon
                    if solarSystemID != session.solarsystemid:
                        requiredQty, requiredType = self.GetFuelConsumptionForMyShip(session.solarsystemid2, solarSystemID, consumptionType, consumptionAmount)
                        entry = self.GetSolarSystemBeaconEntry(solarSystemID, requiredQty, requiredType, jumpDriveRange, structureID, isBridge)
                        scrolllist.append(entry)

            if not len(scrolllist):
                self.sr.scroll.ShowHint(localization.GetByLabel('UI/Common/NothingFound') if eve.session.allianceid else localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/CorporationNotInAllianceMessage'))
            headers = [] if eve.session.allianceid is None else [localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'),
             localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/SecurityColumnHeader'),
             localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/FuelColumnHeader'),
             localization.GetByLabel('UI/Common/Volume'),
             localization.GetByLabel('UI/Common/Distance'),
             localization.GetByLabel(showing)]
            self.sr.scroll.state = uiconst.UI_NORMAL
            self.sr.scroll.Load(contentList=scrolllist, headers=headers)
            self.sr.showing = showing

    def JumpTo(self, entry, *args):
        m = []
        if entry.sr.node.itemID != session.solarsystemid2:
            m = [(uiutil.MenuLabel('UI/CapitalNavigation/CapitalNavigationWindow/JumpTo'), self._JumpTo, (entry.sr.node.itemID, entry.sr.node.beaconID))]
        return m

    def _JumpTo(self, solarSystemID, beaconID):
        sm.GetService('menu').JumpToBeaconAlliance(solarSystemID, beaconID)

    def BridgeTo(self, entry, *args):
        m = []
        if entry.sr.node.itemID != session.solarsystemid2:
            m = [(uiutil.MenuLabel('UI/CapitalNavigation/CapitalNavigationWindow/BridgeTo'), self._BridgeTo, (entry.sr.node.itemID, entry.sr.node.beaconID))]
        return m

    def _BridgeTo(self, solarSystemID, beaconID):
        sm.GetService('menu').BridgeToBeaconAlliance(solarSystemID, beaconID)

    def GetSolarSystemBeaconEntry(self, solarSystemID, requiredQty, requiredType, jumpDriveRange, structureID = None, isBridge = False):
        if solarSystemID is None or requiredQty is None or requiredType is None or jumpDriveRange is None:
            return
        invType = cfg.invtypes.Get(requiredType)
        lightYearDistance = uix.GetLightYearDistance(session.solarsystemid2, solarSystemID, False)
        s_typename = invType.name
        solarSystemName = localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/SolarSystemName', solarSystem=solarSystemID)
        securityStatus = sm.GetService('map').GetSecurityStatus(solarSystemID)
        requiredVolume = invType.volume * requiredQty
        rangeString = ''
        if jumpDriveRange > lightYearDistance:
            rangeString = 'UI/CapitalNavigation/CapitalNavigationWindow/WithinRange'
        else:
            rangeString = 'UI/CapitalNavigation/CapitalNavigationWindow/NotInRange'
        label = '%s<t>%s<t>%s<t>%s<t>%s<t>%s' % (solarSystemName,
         localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/SecurityStatus', securityStatus=securityStatus),
         localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/FuelTypeRequired', fuelType=requiredType, requiredQty=requiredQty),
         localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/FuelVolumeRequired', requiredVolume=requiredVolume),
         localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/DistanceToSystem', lightYearDistance=lightYearDistance),
         localization.GetByLabel(rangeString))
        data = util.KeyVal()
        data.label = label
        data.showinfo = 1
        data.typeID = const.typeSolarSystem
        data.itemID = solarSystemID
        if structureID:
            data.beaconID = structureID
            if isBridge:
                data.GetMenu = self.BridgeTo
            else:
                data.GetMenu = self.JumpTo
        data.Set('sort_%s' % localization.GetByLabel('UI/Common/Distance'), lightYearDistance)
        data.Set('sort_%s' % localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/FuelColumnHeader'), requiredQty)
        data.Set('sort_%s' % localization.GetByLabel('UI/Common/Destination'), solarSystemName)
        data.Set('sort_%s' % localization.GetByLabel('UI/CapitalNavigation/CapitalNavigationWindow/SecurityColumnHeader'), securityStatus)
        data.Set('sort_%s' % localization.GetByLabel('UI/Common/Volume'), requiredVolume)
        return listentry.Get('Generic', data=data)

    def GetJumpDriveInfo(self, shipID):
        if shipID:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            jumpDriveRange = dogmaLocation.GetAttributeValue(shipID, const.attributeJumpDriveRange)
            consumptionType = dogmaLocation.GetAttributeValue(shipID, const.attributeJumpDriveConsumptionType)
            consumptionAmount = dogmaLocation.GetAttributeValue(shipID, const.attributeJumpDriveConsumptionAmount)
            return (jumpDriveRange, consumptionType, consumptionAmount)

    def GetFuelConsumptionForMyShip(self, fromSystem, toSystem, consumptionType, consumptionAmount):
        if not util.GetActiveShip():
            return
        myDist = uix.GetLightYearDistance(fromSystem, toSystem, False)
        if myDist is None:
            return
        consumptionAmount = myDist * consumptionAmount
        return (int(consumptionAmount), consumptionType)
