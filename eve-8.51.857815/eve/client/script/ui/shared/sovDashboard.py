#Embedded file name: eve/client/script/ui/shared\sovDashboard.py
from eve.client.script.ui.control.divider import Divider
import blue
import localization
import uiprimitives
import uicontrols
import uix
import uiutil
import util
import carbonui.const as uiconst
from eve.client.script.ui.control import entries as listentry
import uicls
from mapcommon import STARMODE_SOV_CHANGE, STARMODE_FACTION
COLOR_LIGHT_BLUE = (0.21, 0.62, 0.74, 1.0)
COLOR_DARK_BLUE = (0.0, 0.52, 0.67, 1.0)
BAR_COLORS = [COLOR_LIGHT_BLUE, COLOR_DARK_BLUE]
TIME_SLIDER_HEIGHT = 40
TIME_BAR_HEIGHT = 19
MENU_HEIGHT = 22
LABEL_HEIGHT = 10
LOCATION_HEIGHT = 18 + LABEL_HEIGHT + 4
HEADER_HEIGHT = MENU_HEIGHT + LOCATION_HEIGHT + LABEL_HEIGHT * 2 + 24
LINE_HEIGHT = 8
ACTIVEKILL_HEIGHT = 10

class SovereigntyTab(object):
    """Enum constants to identify the sovereignty tabs"""
    __guid__ = 'sovereignty.SovereigntyTab'
    SolarSystem, Constellation, Region, World, Changes = range(1, 6)


LINK_COLOR = '<color=0xffddaa44>%s</color>'

class SovereigntyOverviewWnd(uicontrols.Window):
    __guid__ = 'form.SovereigntyOverviewWnd'
    __notifyevents__ = ['OnSessionChanged',
     'OnSystemStatusChanged',
     'OnStateSetupChance',
     'OnSovereigntyChanged']
    default_windowID = 'sovOverview'
    default_iconNum = 'res:/ui/Texture/WindowIcons/sovereignty.png'
    default_captionLabelPath = 'Tooltips/Neocom/Sovereignty'
    default_descriptionLabelPath = 'Tooltips/Neocom/Sovereignty_description'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.locationScope = settings.user.ui.Get('sovDashboardLocationScope', SovereigntyTab.SolarSystem)
        self.SetMinSize([420, 400])
        self.SetTopparentHeight(0)
        self.solarSystemID = eve.session.solarsystemid2
        self.constellationID = eve.session.constellationid
        self.regionID = eve.session.regionid
        self.ConstructLayout()
        self.scope = 'all'
        self.ResetLocation()

    def SetLocation(self, solarSystemID, constellationID, regionID, restoreTab = False):
        self.solarSystemID = solarSystemID
        self.constellationID = constellationID
        self.regionID = regionID
        selectedTab = SovereigntyTab.World
        self.pushButtons.DisableButton(localization.GetByLabel('UI/Common/LocationTypes/Constellation'))
        self.pushButtons.DisableButton(localization.GetByLabel('UI/Common/LocationTypes/System'))
        if self.regionID is not None:
            selectedTab = SovereigntyTab.Region
        if self.constellationID is not None:
            selectedTab = SovereigntyTab.Constellation
            self.pushButtons.EnableButton(localization.GetByLabel('UI/Common/LocationTypes/Constellation'))
        if self.solarSystemID is not None:
            self.pushButtons.EnableButton(localization.GetByLabel('UI/Common/LocationTypes/System'))
            selectedTab = SovereigntyTab.SolarSystem
        if restoreTab and self.locationScope > selectedTab:
            selectedTab = self.locationScope
        self.pushButtons.SelectByID(selectedTab)

    def ConstructLayout(self):
        self.sr.header = uiprimitives.Container(name='header', parent=self.sr.main, align=uiconst.TOTOP, pos=(0,
         0,
         0,
         HEADER_HEIGHT), padding=(0,
         const.defaultPadding,
         0,
         const.defaultPadding))
        self.sr.location = uiprimitives.Container(name='location', parent=self.sr.header, align=uiconst.TOTOP, pos=(0,
         0,
         0,
         LOCATION_HEIGHT), padding=(4, 4, 6, 0))
        self.sr.line = uiprimitives.Container(name='line', parent=self.sr.header, align=uiconst.TOTOP, pos=(0,
         0,
         0,
         LINE_HEIGHT), padding=(0, 2, 0, 0))
        self.sr.activekill = uiprimitives.Container(name='activekill', parent=self.sr.header, align=uiconst.TOTOP, pos=(0,
         0,
         0,
         LABEL_HEIGHT * 2), padding=(0, 0, 0, 0))
        self.sr.regionalOverview = uiprimitives.Container(name='regionalOverview', parent=self.sr.main, align=uiconst.TOALL, padding=(0, 4, 0, 0))
        self.sr.worldOverview = uiprimitives.Container(name='worldOverview', parent=self.sr.main, align=uiconst.TOALL, padding=(0, 4, 0, 0), state=uiconst.UI_HIDDEN)
        self.CreateLocationInfo()
        self.CreateActiveKillInfo()
        self.DrawStationsOutposts()
        self.DrawDivider()
        self.DrawInfrastructureHubs()
        self.DrawChanges()
        self.CreateMenu()

    def OnButtonSelected(self, scope):
        self.locationScope = scope
        settings.user.ui.Set('sovDashboardLocationScope', self.locationScope)
        self.Refresh()

    def GetLocationFromScope(self):
        locationID = ''
        if self.locationScope == SovereigntyTab.World:
            locationID = None
        if self.locationScope == SovereigntyTab.Changes:
            locationID = None
        elif self.locationScope == SovereigntyTab.SolarSystem:
            locationID = self.solarSystemID
        elif self.locationScope == SovereigntyTab.Constellation:
            locationID = self.constellationID
        elif self.locationScope == SovereigntyTab.Region:
            locationID = self.regionID
        return locationID

    def DrawChanges(self):
        l = uiprimitives.Line(parent=self.sr.worldOverview, align=uiconst.TOTOP, color=(0.0, 0.0, 0.0, 0.25))
        l = uiprimitives.Line(parent=self.sr.worldOverview, align=uiconst.TOTOP)
        changeContainer = uiprimitives.Container(name='changeContainer', parent=self.sr.worldOverview, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         6,
         const.defaultPadding,
         6))
        self.sr.changesScroll = uicontrols.Scroll(parent=changeContainer)

    def DrawStationsOutposts(self):
        self.sr.stationsoutposts = uiprimitives.Container(parent=self.sr.regionalOverview, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, height=24)
        stationsoutposts = self.sr.stationsoutposts
        textContainer = uiprimitives.Container(name='textContainer', parent=stationsoutposts, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(0, 0, 0, 0))
        leftContainer = uiprimitives.Container(name='leftContainer', parent=textContainer, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(3, 0, 0, 0))
        rightContainer = uiprimitives.Container(name='rightContainer', parent=textContainer, align=uiconst.TORIGHT, pos=(0, 0, 15, 0), padding=(0, 0, 3, 0))
        t = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/Overview'), parent=leftContainer, state=uiconst.UI_DISABLED, left=3, align=uiconst.CENTERLEFT, bold=True)
        rightContainer.width = t.width
        stationsoutposts.height = max(20, t.textheight + 6)
        stationsoutpostsResults = uiprimitives.Container(name='stationsoutpostsResults', parent=self.sr.regionalOverview, align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, pos=(0, 0, 0, 100), padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         6))
        self.sr.stationsoutpostsResults = stationsoutpostsResults
        self.sr.stationOutpostsScroll = uicontrols.Scroll(parent=stationsoutpostsResults)

    def DrawDivider(self):
        divPar = uiprimitives.Container(name='divPar', align=uiconst.TOBOTTOM, pos=(0,
         0,
         0,
         const.defaultPadding), parent=self.sr.stationsoutpostsResults, idx=0)
        divider = Divider(name='divider', align=uiconst.TOALL, pos=(0, 0, 0, 0), parent=divPar, state=uiconst.UI_NORMAL, idx=0)
        divider.Startup(self.sr.stationsoutpostsResults, 'height', 'y', 57, 800)
        divider.OnSizeChanged = self._OnContentSizeChanged
        divider.OnSizeChangeStarting = self._OnContentSizeChangeStarting
        divider.OnSizeChanging = self._OnContentSizeChanging
        self.sr.divider = divider

    def ApplyContentPortion(self):
        if not util.GetAttrs(self, 'sr', 'stationsoutpostsResults') or getattr(self, '_ignorePortion', False) or not uiutil.IsVisible(self.sr.stationsoutpostsResults) or not util.GetAttrs(self, 'sr', 'infrastructurehubs'):
            return
        portion = settings.user.ui.Get('stationsoutpostsPortion', 0.5)
        minResultSpace = self.sr.infrastructurehubs.height + 18
        if self.sr.infrastructurehubsResults.state != uiconst.UI_HIDDEN:
            minResultSpace += 50
        else:
            portion = 1.0
        sl, st, sw, sh = self.sr.regionalOverview.GetAbsolute()
        rcl, rct, rcw, rch = self.sr.infrastructurehubsResults.GetAbsolute()
        spread = sh - self.sr.stationsoutposts.height - self.sr.header.height
        height = int(spread * portion)
        self.sr.stationsoutpostsResults.height = min(height, spread - minResultSpace)

    def _OnContentSizeChanging(self, *args):
        if self.sr.stationsoutpostsResults.height < self._maxContentHeight:
            if self.sr.stack:
                l, t, w, h = self.sr.stack.GetAbsolute()
            else:
                l, t, w, h = self.GetAbsolute()
            minResultSpace = self.sr.infrastructurehubs.height + 18
            if self.sr.infrastructurehubsResults.state != uiconst.UI_HIDDEN:
                minResultSpace += 50
            if t + h - uicore.uilib.y < minResultSpace:
                if self.sr.stack:
                    self.sr.stack.height = uicore.uilib.y + minResultSpace - t
                else:
                    self.height = uicore.uilib.y + minResultSpace - t

    def _OnContentSizeChangeStarting(self, *args):
        self._ignorePortion = True
        l, t, w, h = self.sr.stationsoutpostsResults.GetAbsolute()
        minResultSpace = self.sr.infrastructurehubs.height + 18
        if self.sr.infrastructurehubsResults.state != uiconst.UI_HIDDEN:
            minResultSpace += 50
        maxValue = uicore.desktop.height - t - minResultSpace
        self.sr.divider.SetMinMax(maxValue=maxValue)
        self._maxContentHeight = maxValue

    def _OnContentSizeChanged(self, *args):
        sl, st, sw, sh = self.sr.regionalOverview.GetAbsolute()
        probesPart = self.sr.stationsoutposts.height + self.sr.stationsoutpostsResults.height
        rcl, rct, rcw, rch = self.sr.infrastructurehubsResults.GetAbsolute()
        resultPart = self.sr.infrastructurehubs.height + rch
        portion = probesPart / float(sh - self.sr.header.height)
        settings.user.ui.Set('stationsoutpostsPortion', portion)
        self._ignorePortion = False

    def DrawInfrastructureHubs(self):
        self.sr.infrastructurehubs = uiprimitives.Container(parent=self.sr.regionalOverview, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, height=24)
        infrastructurehubs = self.sr.infrastructurehubs
        textContainer = uiprimitives.Container(name='textContainer', parent=infrastructurehubs, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(0, 0, 0, 0))
        leftContainer = uiprimitives.Container(name='leftContainer', parent=textContainer, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(3, 0, 0, 0))
        rightContainer = uiprimitives.Container(name='rightContainer', parent=textContainer, align=uiconst.TORIGHT, pos=(0, 0, 15, 0), padding=(0, 0, 3, 0))
        t = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Sovereignty/DevelopmentIndices'), parent=leftContainer, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, left=3, bold=True)
        rightContainer.width = t.width
        infrastructurehubs.height = max(20, t.textheight + 6)
        infrastructurehubsResults = uiprimitives.Container(name='infrastructurehubsResults', parent=self.sr.regionalOverview, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         6))
        self.sr.infrastructurehubsResults = infrastructurehubsResults
        self.sr.infrastructurehubsScroll = uicontrols.Scroll(parent=infrastructurehubsResults)

    def CreateHeaderText(self):
        """
        mode will tell us how many sections we want, 3 being all of region, constellation and solarsystem
        """
        text = ''
        if self.locationScope == SovereigntyTab.World:
            text = localization.GetByLabel('UI/Sovereignty/WorldSovStatus')
            return text
        elif self.locationScope == SovereigntyTab.Changes:
            text = localization.GetByLabel('UI/Sovereignty/RecentSovChanges')
            return text
        else:
            mapSvc = sm.GetService('map')
            systemItem = mapSvc.GetItem(self.solarSystemID)
            constItem = mapSvc.GetItem(self.constellationID)
            regItem = mapSvc.GetItem(self.regionID)
            showInfoTag = '<url=showinfo:%d//%d>'
            endUrlTag = '</url>'
            text = ''
            if self.locationScope == SovereigntyTab.SolarSystem:
                if util.IsWormholeRegion(self.regionID):
                    text = '%s / %s / <url=showinfo:%s//%s>%s</url>' % (regItem.itemName,
                     constItem.itemName,
                     systemItem.typeID,
                     self.solarSystemID,
                     systemItem.itemName)
                else:
                    text = localization.GetByLabel('UI/Sovereignty/SystemLocation', regionName=regItem.itemName, constName=constItem.itemName, systemName=systemItem.itemName, startRegionUrlTag=showInfoTag % (regItem.typeID, self.regionID), startConstUrlTag=showInfoTag % (constItem.typeID, self.constellationID), startSystemUrlTag=showInfoTag % (systemItem.typeID, self.solarSystemID), endUrlTag=endUrlTag)
            elif self.locationScope == SovereigntyTab.Constellation:
                if util.IsWormholeRegion(self.regionID):
                    text = localization.GetByLabel('UI/Sovereignty/ConstLocationWH', regionName=regItem.itemName, constName=constItem.itemName)
                else:
                    text = localization.GetByLabel('UI/Sovereignty/ConstLocation', startRegionUrlTag=showInfoTag % (regItem.typeID, self.regionID), startConstUrlTag=showInfoTag % (constItem.typeID, self.constellationID), regionName=regItem.itemName, constName=constItem.itemName, endUrlTag=endUrlTag)
            elif self.locationScope == SovereigntyTab.Region:
                if util.IsWormholeRegion(self.regionID):
                    text = localization.GetByLabel('UI/Sovereignty/RegionLocationWH', regionName=regItem.itemName)
                else:
                    text = localization.GetByLabel('UI/Sovereignty/RegionLocation', startRegionUrlTag=showInfoTag % (regItem.typeID, self.regionID), regionName=regItem.itemName, endUrlTag='</url>')
            return text

    def CreateMenu(self):
        self.pushButtons = uicls.ToggleButtonGroup(parent=self.sr.header, align=uiconst.TOTOP, height=MENU_HEIGHT, padding=(3, 2, 3, 2), callback=self.OnButtonSelected)
        for btnID, label, panel in ((SovereigntyTab.SolarSystem, localization.GetByLabel('UI/Common/LocationTypes/System'), self.sr.regionalOverview),
         (SovereigntyTab.Constellation, localization.GetByLabel('UI/Common/LocationTypes/Constellation'), self.sr.regionalOverview),
         (SovereigntyTab.Region, localization.GetByLabel('UI/Common/LocationTypes/Region'), self.sr.regionalOverview),
         (SovereigntyTab.World, localization.GetByLabel('UI/Common/LocationTypes/World'), self.sr.regionalOverview),
         (SovereigntyTab.Changes, localization.GetByLabel('UI/Sovereignty/Changes'), self.sr.worldOverview)):
            self.pushButtons.AddButton(btnID, label, panel)

    def CreateLocationInfo(self):
        mapIconContainer = uiprimitives.Container(name='mapIconContainer', parent=self.sr.location, align=uiconst.TORIGHT, pos=(0, 0, 32, 0), padding=(0, 0, 0, 5))
        self.sr.textContainer = uiprimitives.Container(name='textContainer', parent=self.sr.location, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(0, 0, 0, 0))
        btn = uix.GetBigButton(32, mapIconContainer)
        btn.SetAlign(uiconst.CENTERRIGHT)
        btn.OnClick = self.OpenMap
        btn.hint = localization.GetByLabel('UI/Map/Map')
        btn.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/map.png')
        locationMenu = uicontrols.MenuIcon(size=24, ignoreSize=True)
        locationMenu.GetMenu = self.GetLocationMenu
        locationMenu.left = -5
        locationMenu.top = -3
        locationMenu.hint = ''
        self.sr.textContainer.children.append(locationMenu)
        self.sr.breadCrumbs = uicontrols.Label(name='label', text='', parent=self.sr.textContainer, fontsize=16, align=uiconst.TOTOP, padding=(15, 0, 0, 0), boldlinks=0, state=uiconst.UI_NORMAL)
        self.sr.dominatorText = uicontrols.EveLabelMedium(text='', parent=self.sr.textContainer, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, maxLines=1)

    def GetDominantAllianceName(self):
        """
        Will return the name of most influential alliance with in the current scope.
        returns:
            contested if two or more have equal number of systems with sov
            none if none has sov
            else returns the alliance name
        """
        sovID = sm.GetService('sov').GetDominantAllianceID(self.locationScope, self.regionID, self.constellationID, self.solarSystemID)
        if sovID == 'none':
            self.sovID = None
            return ('',
             '',
             localization.GetByLabel('UI/Common/None'),
             '')
        elif sovID == 'contested':
            self.sovID = None
            return ('',
             '',
             '',
             localization.GetByLabel('UI/Inflight/Brackets/SystemContested'))
        else:
            self.sovID = sovID
            typeID = const.typeAlliance
            if util.IsFaction(self.sovID):
                typeID = const.typeFaction
            sovName = cfg.eveowners.Get(sovID).name
            return (typeID,
             sovID,
             sovName,
             '')

    def UpdateLocationInfo(self):
        self.sr.breadCrumbs.text = self.CreateHeaderText()
        contestedState = ''
        allianceName = None
        if self.locationScope == SovereigntyTab.SolarSystem:
            contestedState = sm.GetService('sov').GetContestedState(self.solarSystemID)
            if self.solarSystemID == session.solarsystemid2:
                sovInfo = sm.GetService('sov').GetSystemSovereigntyInfo(self.solarSystemID)
                if sovInfo:
                    typeID = const.typeAlliance
                    allianceID = sovInfo.allianceID
                    allianceName = cfg.eveowners.Get(sovInfo.allianceID).name
                if sm.GetService('facwar').IsFacWarSystem(session.solarsystemid2):
                    contestedState = sm.GetService('infoPanel').GetSolarSystemStatusText()
                    typeID = const.typeFaction
        if allianceName is None:
            typeID, allianceID, allianceName, contestedState = self.GetDominantAllianceName()
        if self.sovID is None:
            text = localization.GetByLabel('UI/Sovereignty/DominantSovHolderNone', contestedState=contestedState)
        else:
            showInfoTag = '<url=showinfo:%d//%d>' % (typeID, allianceID)
            text = localization.GetByLabel('UI/Sovereignty/DominantSovHolder', allianceName=allianceName, contestedState=contestedState, startUrlTag=showInfoTag, endUrlTag='</url>')
        self.sr.dominatorText.text = text

    def CreateActiveKillInfo(self):
        leftContainer = uiprimitives.Container(name='leftContainer', parent=self.sr.activekill, align=uiconst.TOALL, padding=(5, 0, 0, 0))
        rightContainer = uiprimitives.Container(name='rightContainer', parent=self.sr.activekill, align=uiconst.TORIGHT, padding=(0, 0, 5, 0))
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Sovereignty/KillsLast24H'), parent=leftContainer, align=uiconst.TOPLEFT)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Sovereignty/CynoFieldsActive'), parent=leftContainer, align=uiconst.TOPLEFT, top=14)
        self.killsText = uicontrols.EveLabelMedium(text='0 / 0', parent=rightContainer, align=uiconst.TOPRIGHT)
        self.activeText = uicontrols.EveLabelMedium(text='0 / 0', parent=rightContainer, align=uiconst.TOPRIGHT, top=14)
        maxwidth = max(self.killsText.width, self.activeText.width)
        rightContainer.width = maxwidth
        self.UpdateActiveKillInfo()

    def UpdateActiveKillInfo(self):
        if util.IsWormholeRegion(self.regionID):
            self.killsText.text = localization.GetByLabel('UI/Generic/Unknown')
            self.activeText.text = localization.GetByLabel('UI/Generic/Unknown')
        else:
            kills, pods = sm.GetService('sov').GetKillLast24H(self.GetLocationFromScope())
            self.killsText.text = '%d / %d' % (kills, pods)
            cynoResult = sm.GetService('sov').GetActiveCynos(self.GetLocationFromScope())
            self.activeText.text = '%d / %d' % (cynoResult.cynoStructures, cynoResult.cynoModules)

    def GetBarColor(self, hasSov):
        if hasSov:
            return COLOR_LIGHT_BLUE
        else:
            return COLOR_DARK_BLUE

    def SetEndPointDates(self):
        uix.Flush(self.sr.dates)
        uicontrols.EveLabelMedium(text=util.FmtDate(blue.os.GetWallclockTime()), parent=self.sr.dates, align=uiconst.TORIGHT)
        uicontrols.EveLabelMedium(text=util.FmtDate(blue.os.GetWallclockTime()), parent=self.sr.dates, align=uiconst.TOLEFT)

    def _OnResize(self, *args):
        self.ApplyContentPortion()

    def ShowStationsOutposts(self):
        locationHeader, items, fwitems = self.GetHeaderAndPrimedItems()
        self.sr.stationOutpostsScroll.sr.id = 'stationOutpostsScroll'
        scrolllist = []
        headers = [localization.GetByLabel('UI/Sovereignty/Sovereignty'), locationHeader, localization.GetByLabel('UI/Common/LocationTypes/Stations')]
        cfg.eveowners.Prime([ item.allianceID for item in items if item.allianceID is not None ])
        stateSvc = sm.GetService('state')
        facwarSvc = sm.GetService('facwar')
        for item in items:
            kv = util.KeyVal(item)
            kv.ownerID = kv.allianceID
            locationName = cfg.evelocations.Get(item.locationID).name
            if facwarSvc.IsFacWarSystem(item.locationID):
                occupierID = facwarSvc.GetSystemOccupier(item.locationID)
                alliance = cfg.eveowners.Get(occupierID).name
            elif item.allianceID is not None:
                alliance = cfg.eveowners.Get(item.allianceID).name
            else:
                alliance = ''
            text = '%s<t>%s<t><right>%d' % (alliance, locationName, item.stationCount)
            scrolllist.append((alliance, listentry.Get('SovereigntyEntry', {'line': 1,
              'label': text,
              'allianceID': item.allianceID,
              'stationCount': item.stationCount,
              'loss': False,
              'locationID': item.locationID,
              'scope': self.locationScope,
              'regionID': None,
              'flag': stateSvc.CheckStates(kv, 'flag')})))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.stationOutpostsScroll.Load(contentList=scrolllist, headers=headers)
        self.sr.stationOutpostsScroll.ShowHint('')

    def ShowIndexLevels(self):
        locationHeader, sovitems, fwitems = self.GetHeaderAndPrimedItems()
        facwarSvc = sm.GetService('facwar')
        scrolllist = []
        fwscrolllist = []
        for item in sovitems:
            locationName = cfg.evelocations.Get(item.locationID).name
            data = util.KeyVal(label=locationName, locationID=item.locationID, scope=self.locationScope)
            if facwarSvc.IsFacWarSystem(item.locationID):
                if item.locationID in fwitems:
                    data.upgradePoints = fwitems[item.locationID].loyaltyPoints
                else:
                    data.upgradePoints = 0
                entry = listentry.Get('UpgradeEntry', data)
                fwscrolllist.append((locationName, entry))
            else:
                data.militaryPoints = item.militaryPoints
                data.industrialPoints = item.industrialPoints
                data.claimedFor = item.claimedFor
                entry = listentry.Get('IndexEntry', data)
                scrolllist.append((locationName, entry))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        fwscrolllist = uiutil.SortListOfTuples(fwscrolllist)
        if len(scrolllist) > 0:
            scrolllist.insert(0, listentry.Get('HeaderEntry', {'systemHeader': locationHeader,
             'militaryHeader': localization.GetByLabel('UI/Sovereignty/Military'),
             'industryHeader': localization.GetByLabel('UI/Sovereignty/Industry'),
             'claimTimeHeader': localization.GetByLabel('UI/Sovereignty/Strategic')}))
        if len(fwscrolllist) > 0:
            fwscrolllist.insert(0, listentry.Get('FWHeaderEntry', {'systemHeader': localization.GetByLabel('UI/Common/LocationTypes/FacWarSystem'),
             'upgradesHeader': localization.GetByLabel('UI/Sovereignty/UpgradeLevel')}))
            if len(scrolllist) > 0:
                fwscrolllist.insert(0, listentry.Get('Push', {'height': 10}))
        self.sr.infrastructurehubsScroll.Load(contentList=scrolllist + fwscrolllist)

    def GetHeaderAndPrimedItems(self):
        locationID = self.GetLocationFromScope()
        locationHeader = ''
        if self.locationScope == SovereigntyTab.SolarSystem:
            locationHeader = localization.GetByLabel('UI/Common/LocationTypes/System')
        elif self.locationScope == SovereigntyTab.Constellation:
            locationHeader = localization.GetByLabel('UI/Common/LocationTypes/System')
        elif self.locationScope == SovereigntyTab.Region:
            locationHeader = localization.GetByLabel('UI/Common/LocationTypes/Constellation')
        elif self.locationScope == SovereigntyTab.World:
            locationHeader = localization.GetByLabel('UI/Common/LocationTypes/Region')
        sovitems, fwitems = sm.GetService('sov').GetCurrentData(locationID)
        toPrime = [ item.locationID for item in sovitems ]
        toPrime.extend(fwitems.keys())
        cfg.evelocations.Prime(toPrime)
        return (locationHeader, sovitems, fwitems)

    def ShowChanges(self):
        self.sr.changesScroll.sr.id = 'changesScroll'
        scrolllist = []
        headers = []
        headers = [localization.GetByLabel('UI/Sovereignty/Owner'),
         localization.GetByLabel('UI/Common/LocationTypes/Region'),
         localization.GetByLabel('UI/Common/LocationTypes/System'),
         localization.GetByLabel('UI/Sovereignty/Change'),
         localization.GetByLabel('UI/Common/Date')]
        items = sm.GetService('sov').GetRecentActivity()
        solarSystemList = [ item.solarSystemID for item in items ]
        map = sm.GetService('map')
        regionList = [ map.GetRegionForSolarSystem(item) for item in solarSystemList ]
        cfg.evelocations.Prime(solarSystemList + regionList)
        ownerList = [ item.ownerID for item in items ]
        oldOwnerList = [ item.oldOwnerID for item in items ]
        cfg.eveowners.Prime(ownerList + oldOwnerList)
        stateSvc = sm.GetService('state')
        for i, item in enumerate(items):
            systemName = cfg.evelocations.Get(item.solarSystemID).name
            ownerID = item.ownerID
            oldOwnerID = item.oldOwnerID
            regionID = regionList[i]
            region = cfg.evelocations.Get(regionID).name
            ownerChanges = []
            loss = False
            if item.stationID is None:
                if item.oldOwnerID is None:
                    ownerChanges.append(util.KeyVal(text=localization.GetByLabel('UI/Sovereignty/SovereigntyGain'), allianceID=ownerID, ownerID=ownerID, loss=False))
                elif item.ownerID is None:
                    ownerChanges.append(util.KeyVal(text=localization.GetByLabel('UI/Sovereignty/SovereigntyLoss'), allianceID=oldOwnerID, ownerID=oldOwnerID, loss=True))
                else:
                    ownerChanges.append(util.KeyVal(text=localization.GetByLabel('UI/Sovereignty/SovereigntyGain'), allianceID=ownerID, ownerID=ownerID, loss=False))
            elif item.oldOwnerID is None:
                ownerChanges.append(util.KeyVal(text=localization.GetByLabel('UI/Sovereignty/StationGain'), corpID=ownerID, ownerID=ownerID, loss=False))
            elif item.ownerID is not None:
                ownerChanges.append(util.KeyVal(text=localization.GetByLabel('UI/Sovereignty/StationLoss'), corpID=oldOwnerID, ownerID=oldOwnerID, loss=True))
                ownerChanges.append(util.KeyVal(text=localization.GetByLabel('UI/Sovereignty/StationGain'), corpID=ownerID, ownerID=ownerID, loss=False))
            date = util.FmtDate(item.activityTime, 'ss')
            for kv in ownerChanges:
                ownerName = cfg.eveowners.Get(kv.ownerID).name
                text = '%s<t>%s<t>%s<t>%s<t>%s' % (ownerName,
                 region,
                 systemName,
                 kv.text,
                 date)
                flag = stateSvc.CheckStates(kv, 'flag')
                scrolllist.append((ownerName, listentry.Get('SovereigntyEntry', {'line': 1,
                  'label': text,
                  'allianceID': kv.Get('allianceID', None),
                  'corpID': kv.Get('corpID', None),
                  'loss': kv.loss,
                  'locationID': item.solarSystemID,
                  'scope': self.locationScope,
                  'regionID': regionID,
                  'flag': stateSvc.CheckStates(kv, 'flag')})))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.changesScroll.Load(contentList=scrolllist, headers=headers)
        self.sr.changesScroll.ShowHint('')

    def Refresh(self):
        self.GetDominantAllianceName()
        self.UpdateLocationInfo()
        self.UpdateActiveKillInfo()
        if self.locationScope == SovereigntyTab.Changes:
            self.ShowChanges()
        else:
            self.ShowStationsOutposts()
            self.ShowIndexLevels()

    def OnSystemStatusChanged(self):
        self.Refresh()

    def OnSovereigntyChanged(self, solarSystemID, allianceID):
        """A scatter event broadcast from the ballpark when the 
           sovereignty of the current system changes
        """
        self.UpdateLocationInfo()

    def OnSessionChanged(self, isremote, session, change):
        if 'solarsystemid2' in change:
            if not self.destroyed:
                self.Refresh()

    def OnStateSetupChance(self, *args):
        self.ShowStationsOutposts()

    def OpenMap(self, *args):
        viewSvc = sm.GetService('viewState')
        if viewSvc.IsViewActive('starmap', 'systemmap'):
            viewSvc.CloseSecondaryView()
        else:
            viewSvc.ActivateView('starmap', interestID=self.GetLocationFromScope() or const.locationUniverse)

    def GetLocationMenu(self, *args):
        """Populate the white triangle menu by the location path"""
        m = []
        m.append([uiutil.MenuLabel('UI/Map/ViewCurrentLocation'), self.ResetLocation])
        m.append((uiutil.MenuLabel('UI/Sovereignty/ShowSovInMap'), self.ShowStarsInMap, ((STARMODE_FACTION, -1),)))
        m.append((uiutil.MenuLabel('UI/Sovereignty/ShowSovTilesInMap'), self.ShowSovTilesInMap))
        m.append((uiutil.MenuLabel('UI/Sovereignty/ShowSovChangesInMap'), self.ShowStarsInMap, (STARMODE_SOV_CHANGE,)))
        return m

    def ShowStarsInMap(self, starMode):
        sm.GetService('viewState').ActivateView('starmap', interestID=self.GetLocationFromScope() or const.locationUniverse, starColorMode=starMode)

    def ShowSovTilesInMap(self):
        sm.GetService('viewState').ActivateView('starmap', interestID=self.GetLocationFromScope() or const.locationUniverse, tileMode=STARMODE_SOV_CHANGE)

    def ResetLocation(self):
        self.SetLocation(eve.session.solarsystemid2, eve.session.constellationid, eve.session.regionid)
