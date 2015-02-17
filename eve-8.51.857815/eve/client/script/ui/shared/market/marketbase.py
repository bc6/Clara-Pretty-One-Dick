#Embedded file name: eve/client/script/ui/shared/market\marketbase.py
import base
import blue
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveWindowUnderlay import LineUnderlay
import log
import service
import sys
import uicls
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import uiutil
import uix
import uthread
import util
import localization
from localization import GetByLabel
import telemetry
from eve.client.script.ui.control.listwindow import ListWindow
from eve.client.script.ui.control.eveImage import Image
from eve.client.script.ui.control.listgroup import ListGroup as Group
from collections import defaultdict
import const
from eve.client.script.ui.shared.traits import TraitsContainer, HasTraits
from carbonui.primitives.container import Container
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.common.script.util import industryCommon
from eve.client.script.ui.shared.market.requirements import RequirementsContainer
INFINITY = 999999999999999999L
MAXVALUE = 9223372036854L

class RegionalMarket(uicontrols.Window):
    __guid__ = 'form.RegionalMarket'
    default_width = 800
    default_height = 600
    default_windowID = 'market'
    default_captionLabelPath = 'Tooltips/StationServices/Market'
    default_descriptionLabelPath = 'Tooltips/StationServices/Market_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/market.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'station_inflight'
        self.sr.main = uiutil.GetChild(self, 'main')
        self.SetMinSize([650, 435])
        self.HideMainIcon()
        self.SetTopparentHeight(0)
        self.sr.market = MarketBase(name='marketbase', parent=self.sr.main, state=uiconst.UI_PICKCHILDREN, pos=(0, 0, 0, 0))
        self.sr.market.Startup()

    def LoadTypeID_Ext(self, typeID):
        self.sr.market.LoadTypeID_Ext(typeID)
        uiutil.SetOrder(self, 0)

    def OnBack(self, *args):
        self.sr.market.GoBack()

    def OnForward(self, *args):
        self.sr.market.GoForward()


class StationMarket(uiprimitives.Container):
    __guid__ = 'form.StationMarket'

    def Startup(self, *args):
        uiprimitives.Line(parent=self, align=uiconst.TOTOP)
        self.sr.market = MarketBase(name='marketbase', parent=self, state=uiconst.UI_PICKCHILDREN, pos=(0, 0, 0, 0))
        self.sr.market.Startup(1)


class MarketBase(uiprimitives.Container):
    __guid__ = 'form.Market'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnMarketQuickbarChange', 'OnOwnOrdersChanged', 'OnSessionChanged']
    __update_on_reload__ = 1

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.inited = 0
        self.pendingType = None
        self.loadingType = 0
        self.lastdetailTab = localization.GetByLabel('UI/Market/MarketData')
        self.lastOnOrderChangeTime = None
        self.refreshOrdersTimer = None
        self.groupListData = None
        self.sr.lastSearchResult = []
        self.sr.lastBrowseResult = []
        self.sr.marketgroups = None
        self.sr.quickType = None
        self.sr.pricehistory = None
        self.sr.grouplist = None
        self.sr.marketdata = None
        self.detailsInited = 0
        self.updatingGroups = 0
        self.settingsInited = 0
        self.OnChangeFuncs = {}
        self.SetChangeFuncs()
        self.lastid = 0
        self.marketItemList = []
        self.name = 'MarketBase'
        self.sr.detailTypeID = None
        self.parentDictionary = {}
        self.historyData = []
        self.historyIdx = None

    def _OnClose(self, *args):
        if self.groupListData is not None:
            settings.char.ui.Set('market_groupList', self.groupListData)
        if self.sr.leftSide:
            settings.user.ui.Set('marketselectorwidth_%s' % self.idName, self.sr.leftSide.width)
        settings.user.ui.Set('quickbar_lastid', self.lastid)
        settings.user.ui.Set('quickbar', self.folders)
        sm.UnregisterNotify(self)

    def Startup(self, isStationMarket = 0):
        self.idName = 'region'
        self.groupListData = settings.char.ui.Get('market_groupList', None)
        leftSide = uiprimitives.Container(name='leftSide', parent=self, align=uiconst.TOLEFT, padding=const.defaultPadding, width=settings.user.ui.Get('marketselectorwidth_%s' % self.idName, 180))
        from eve.client.script.ui.control.divider import Divider
        divider = Divider(name='divider', align=uiconst.TOLEFT, width=const.defaultPadding, parent=self, state=uiconst.UI_NORMAL)
        divider.Startup(leftSide, 'width', 'x', 180, 380)
        uiprimitives.Line(parent=divider, align=uiconst.TORIGHT, opacity=0.05)
        self.sr.leftSide = leftSide
        caption = localization.GetByLabel('UI/Market/RegionalMarket', name=cfg.evelocations.Get(session.regionid).name)
        self.sr.caption = uicontrols.EveCaptionMedium(text=caption, parent=leftSide, align=uiconst.TOTOP, padding=(8, 4, 8, 10))
        tabs = uicontrols.TabGroup(name='tabparent', parent=leftSide)
        self.sr.sbTabs = tabs
        self.sr.tabs = uicontrols.TabGroup(name='tabparent', parent=self)
        self.groupScroll = ScrollContainer(name='groupScroll', parent=self, padding=const.defaultPadding, showUnderlay=True)
        from eve.client.script.ui.shared.market.orders import MarketOrders
        self.sr.myorders = MarketOrders(name='orders', parent=self, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        searchparent = uiprimitives.Container(name='searchparent', parent=leftSide, align=uiconst.TOTOP, height=22, padBottom=const.defaultPadding, padTop=const.defaultPadding)
        self.sr.filtericon = uicls.UtilMenu(parent=searchparent, align=uiconst.CENTERRIGHT, left=0, GetUtilMenu=self.SettingMenu, texturePath='res:/UI/Texture/SettingsCogwheel.png', width=18, height=18, iconSize=18)
        btn = uicontrols.Button(parent=searchparent, label=localization.GetByLabel('UI/Common/Search'), func=self.Search, btn_default=1, idx=0, align=uiconst.CENTERRIGHT, left=20)
        searchText = settings.char.ui.Get('market_searchText', '')
        inpt = uicls.QuickFilterEdit(name='searchField', parent=searchparent, setvalue=searchText, hinttext=localization.GetByLabel('UI/Market/Marketbase/SearchTerm'), pos=(0, 0, 0, 18), padRight=btn.width + 24, maxLength=64, align=uiconst.TOALL, OnClearFilter=self.LoadMarketListOrSearch)
        inpt.ReloadFunction = self.OnSearchFieldChanged
        inpt.OnReturn = self.LoadMarketListOrSearch
        self.sr.searchInput = inpt
        self.sr.searchparent = searchparent
        self.sr.quickButtons = uiprimitives.Container(name='quickButtons', align=uiconst.TOBOTTOM, padTop=6, height=20, state=uiconst.UI_HIDDEN, parent=leftSide)
        buttons = [(localization.GetByLabel('UI/Market/NewFolder'),
          self.NewFolderClick,
          0,
          84,
          False,
          False,
          False,
          localization.GetByLabel('Tooltips/Market/MarketQuickbarNewFolder')), (localization.GetByLabel('UI/Market/Marketbase/ResetQuickbar'),
          self.ResetQuickbar,
          (),
          84,
          False,
          False,
          False,
          localization.GetByLabel('Tooltips/Market/MarketQuickbarReset'))]
        buttonGroup = uicontrols.ButtonGroup(btns=buttons, parent=self.sr.quickButtons, unisize=0)
        self.sr.detailsparent = uiprimitives.Container(name='details', parent=self, clipChildren=True)
        maintabs = [[localization.GetByLabel('UI/Market/Browse'),
          None,
          self,
          'browse',
          None,
          localization.GetByLabel('Tooltips/Market/MarketBrowseTab')], [localization.GetByLabel('UI/Market/QuickBar'),
          None,
          self,
          'quickbar',
          None,
          localization.GetByLabel('Tooltips/Market/MarketQuickbarTab')]]
        subtabs = [[uiutil.FixedTabName('UI/Common/Details'),
          self.sr.detailsparent,
          self,
          'details',
          None,
          localization.GetByLabel('Tooltips/Market/MarketDetailsTab')], [uiutil.FixedTabName('UI/Common/Groups'),
          self.groupScroll,
          self,
          'groups',
          None,
          localization.GetByLabel('Tooltips/Market/MarketGroupsTab')], [localization.GetByLabel('UI/Market/Orders/MyOrders'),
          self.sr.myorders,
          self,
          'myorders',
          None,
          localization.GetByLabel('Tooltips/Market/MarketMyOrdersTab')]]
        if eve.session.corprole & const.corpRoleAccountant:
            from eve.client.script.ui.shared.market.orders import MarketOrders
            self.sr.corporders = MarketOrders(name='corporders', parent=self, pos=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            subtabs.append([localization.GetByLabel('UI/Market/Orders/CorporationOrders'),
             self.sr.corporders,
             self,
             'corporders',
             None,
             localization.GetByLabel('Tooltips/Market/MarketCorpOrdersTab')])
        if self.destroyed:
            return
        self.sr.typescroll = uicontrols.Scroll(name='typescroll', parent=leftSide, padTop=2)
        self.sr.typescroll.multiSelect = 0
        self.sr.typescroll.OnSelectionChange = self.CheckTypeScrollSelection
        self.sr.typescroll.GetContentContainer().OnDropData = self.OnScrollDrop
        self.sr.sbTabs.Startup(maintabs, 'tbselectortabs_%s' % self.idName, autoselecttab=1, UIIDPrefix='marketTab')
        quickbarTab = self.sr.sbTabs.GetTabs()[1]
        quickbarTab.OnTabDropData = self.OnQuickbarScrollDrop
        self.sr.tabs.Startup(subtabs, 'marketsubtabs_%s' % self.idName, autoselecttab=1, UIIDPrefix='marketTab')
        sm.RegisterNotify(self)
        self.inited = 1
        self.folders = settings.user.ui.Get('quickbar', {})
        self.lastid = settings.user.ui.Get('quickbar_lastid', 0)
        self.SetupFilters()
        self.SetFilterHint()
        self.maxdepth = 99

    def SettingMenu(self, menuParent):
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Market/ShowOnlyAvailable'), checked=bool(settings.user.ui.Get('showonlyavailable', 1)), callback=(self.OnCheckboxChange, 'showonlyavailable'))
        menuParent.AddSpace()
        menuParent.AddText(text=localization.GetByLabel('UI/Market/RangeFilter'))
        if session.stationid:
            menuParent.AddRadioButton(text=localization.GetByLabel('UI/Common/LocationTypes/Station'), checked=self.GetRange() == const.rangeStation, callback=(self.OnComboChange, const.rangeStation))
        menuParent.AddRadioButton(text=localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'), checked=self.GetRange() == const.rangeSolarSystem, callback=(self.OnComboChange, const.rangeSolarSystem))
        menuParent.AddRadioButton(text=localization.GetByLabel('UI/Common/LocationTypes/Region'), checked=self.GetRange() == const.rangeRegion, callback=(self.OnComboChange, const.rangeRegion))
        menuParent.AddSpace()
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Market/Marketbase/FilterBySkills'), checked=bool(settings.user.ui.Get('showonlyskillsfor', 0)), callback=(self.OnCheckboxChange, 'showonlyskillsfor'))
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Market/Marketbase/FilterByCPUAndPowergrid'), checked=bool(settings.user.ui.Get('showhavecpuandpower', 0)), callback=(self.OnCheckboxChange, 'showhavecpuandpower'))
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Market/Marketbase/FilterByUntrainedSkills'), checked=bool(settings.user.ui.Get('shownewskills', 0)), callback=(self.OnCheckboxChange, 'shownewskills'))
        menuParent.AddSpace()
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Market/Marketbase/AutoRefresh'), checked=bool(settings.user.ui.Get('autorefresh', 0)), callback=(self.OnCheckboxChange, 'autorefresh'))
        menuParent.AddSpace()
        menuParent.AddButton(text=GetByLabel('UI/Browser/BrowserSettings/ResetCacheLocation'), callback=self.ResetFilterSettings)

    def CheckTypeScrollSelection(self, sel):
        if len(sel) == 1:
            entry = sel[0]
            if entry.__guid__ == 'listentry.GenericMarketItem' or entry.__guid__ == 'listentry.QuickbarItem':
                self.OnTypeClick(entry.panel)

    def GetOptions(self):
        if eve.session.stationid:
            options = [(localization.GetByLabel('UI/Common/LocationTypes/Station'), const.rangeStation), (localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'), const.rangeSolarSystem), (localization.GetByLabel('UI/Common/LocationTypes/Region'), const.rangeRegion)]
        else:
            options = [(localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'), const.rangeSolarSystem), (localization.GetByLabel('UI/Common/LocationTypes/Region'), const.rangeRegion)]
        return options

    def GetRange(self):
        return sm.StartService('marketutils').GetMarketRange()

    def OnComboChange(self, value, *args):
        if self.inited:
            sm.GetService('marketutils').SetMarketRange(value)
            self.sr.lastSearchResult = []
            uthread.new(self.ReloadMarketListTab)

    def ReloadMarketListTab(self, *args):
        if self.sr.sbTabs.GetSelectedArgs() == 'browse':
            self.LoadMarketListOrSearch()
        self.sr.tabs.ReloadVisible()

    def SetFilterHint(self, *args):
        filtersInUse, filterUsed = self.FiltersInUse1()
        self.sr.filtericon.hint = filtersInUse

    def OnCheckboxChange(self, sender, *args):
        c = settings.user.ui.Get(sender, 0)
        settings.user.ui.Set(sender, not c)
        self.SetFilterHint()
        if self.sr.sbTabs.GetSelectedArgs() == 'browse':
            self.LoadMarketListOrSearch()
        if self.sr.tabs.GetSelectedArgs() == 'browse':
            self.LoadMarketListOrSearch()

    def OnCheckboxChangeSett(self, sender, *args):
        settings.user.ui.Set(sender.name, bool(sender.checked))
        self.LoadMarketData()
        self.ShowFiltersInUse()

    def OnMarketQuickbarChange(self, fromMarket = 0, *args):
        if self and not self.destroyed:
            if not fromMarket:
                self.lastid = settings.user.ui.Get('quickbar_lastid', 0)
                self.folders = settings.user.ui.Get('quickbar', {})
            if self.sr.sbTabs.GetSelectedArgs() == 'quickbar':
                self.LoadQuickBar()

    def OnOwnOrdersChanged(self, orders, reason, isCorp):
        if self and not self.destroyed:
            showAutoRefresh = False
            for order in orders:
                if reason != 'Expiry':
                    if self.lastOnOrderChangeTime and self.OnOrderChangeTimer is None:
                        intval = 15000
                        diff = blue.os.TimeDiffInMs(self.lastOnOrderChangeTime, blue.os.GetWallclockTime())
                        if diff > intval:
                            self._OnOwnOrderChanged(order.typeID)
                        else:
                            self.OnOrderChangeTimer = base.AutoTimer(intval - int(diff), self._OnOwnOrderChanged, (order.typeID,))
                    else:
                        self._OnOwnOrderChanged(order.typeID)
                elif not settings.user.ui.Get('autorefresh', True) and self.sr.detailTypeID:
                    if order.typeID == self.sr.detailTypeID:
                        showAutoRefresh = True

            if showAutoRefresh:
                self.sr.reloadBtn.state = uiconst.UI_NORMAL
                self.AdjustRightButtonCont()

    def _OnOwnOrderChanged(self, orderTypeID):
        if self and not self.destroyed:
            try:
                if settings.user.ui.Get('autorefresh', True):
                    if self.sr.sbTabs.GetSelectedArgs() == 'browse':
                        self.LoadMarketListOrSearch()
                    self.sr.tabs.ReloadVisible()
                    self.OnOrderChangeTimer = None
                    self.lastOnOrderChangeTime = blue.os.GetWallclockTime()
                elif orderTypeID == self.sr.detailTypeID:
                    self.sr.reloadBtn.state = uiconst.UI_NORMAL
                    self.AdjustRightButtonCont()
            except AttributeError:
                if not self or self.destoyed:
                    return
                raise

    def OnSessionChanged(self, isremote, session, change):
        if 'solarsystemid' in change and self and not self.destroyed:
            combo = uiutil.FindChild(self, 'marketComboRangeFilter')
            if combo:
                oldValue = combo.GetValue()
                newValue = self.GetRange()
                combo.LoadOptions(self.GetOptions(), newValue)
                if oldValue != newValue:
                    self.ReloadMarketListTab()
            self.sr.caption.text = localization.GetByLabel('UI/Market/RegionalMarket', name=cfg.evelocations.Get(session.regionid).name)

    def GetQuickItemMenu(self, btn, *args):
        if btn.sr.node.extraText:
            menuText = 'UI/Market/Marketbase/EditAdditionalText'
        else:
            menuText = 'UI/Market/Marketbase/AddAdditionalText'
        m = [(uiutil.MenuLabel(menuText), self.EditExtraText, (btn.sr.node.id, btn.sr.node.extraText, btn.sr.node.label))]
        m += [None]
        m += [(uiutil.MenuLabel('UI/Market/Remove'), self.RemoveFromQuickBar, (btn.sr.node,))]
        if eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
            m.append(None)
            m += sm.GetService('menu').GetGMTypeMenu(btn.sr.node.typeID)
        return m

    def RemoveFromQuickBar(self, node):
        nodes = node.scroll.GetSelectedNodes(node)
        for each in nodes:
            sm.GetService('menu').RemoveFromQuickBar(each)

    def EditExtraText(self, groupID, extraText, label, *args):
        typeNewTextLabel = localization.GetByLabel('UI/Market/Marketbase/TypeInAdditionalText')
        extraText = uiutil.NamePopup(label, typeNewTextLabel, setvalue=unicode(extraText), maxLength=25, validator=self.ValidateExtraText)
        if extraText is None:
            return
        self.folders[groupID[1]].extraText = extraText
        sm.ScatterEvent('OnMarketQuickbarChange')

    def ValidateExtraText(self, *args):
        pass

    def OnSearchFieldChanged(self, *args):
        if self.sr.searchInput.GetValue().strip() == '':
            self.LoadMarketListOrSearch()

    def LoadMarketListOrSearch(self):
        if self.destroyed:
            return
        settings.char.ui.Set('market_searchText', self.sr.searchInput.GetValue())
        self.SetFilterHint()
        self.sr.quickButtons.state = uiconst.UI_HIDDEN
        self.mine = self.GetMySkills()
        self.PopulateAsksForMyRange()
        if self.sr.searchInput.GetValue().strip():
            self.Search()
        else:
            if not self.sr.filtericon.enabled:
                self.sr.filtericon.Enable()
                self.SetFilterHint()
            self.LoadMarketList()

    def LoadMarketList(self):
        scrolllist = self.GetGroupListForBrowse()
        if self.destroyed:
            return
        self.sr.typescroll.Load(contentList=scrolllist, scrollTo=self.sr.typescroll.GetScrollProportion())

    def PopulateAsksForMyRange(self):
        """
            This function gets the info on the order with the best price in the range
            for each type.
            It is very important this function is called right before GetGroupListForBrowse() is called
            and that it's called in ShowGroupPage()
            GetGroupListForBrowse() only cares about whether a type is in the dictionary, but 
            ShowGroupPage() acutally uses the values in the dictionary
            
            use:  PopulateAsksForMyRange()
            pre:  None
            post: self.asksForMyRange is a dictionary of this form
                    {
                        typeID1:<info on order with best price in the range for typeID1>,
                        typeID2:<info on order with best price in the range for typeID2>,...
                    }
        """
        quote = sm.StartService('marketQuote')
        marketRange = self.GetRange()
        if marketRange == const.rangeStation:
            self.asksForMyRange = quote.GetStationAsks()
        elif marketRange == const.rangeSolarSystem:
            self.asksForMyRange = quote.GetSystemAsks()
        else:
            self.asksForMyRange = quote.GetRegionBest()

    def GetScrollListFromTypeList(self, nodedata, *args):
        invTypes = nodedata.invTypes
        sublevel = nodedata.sublevel
        return self._GetScrollListFromTypeList(invTypes, sublevel)

    def _GetScrollListFromTypeList(self, invTypes, sublevel):
        subList = []
        for invType in invTypes:
            data = util.KeyVal()
            data.label = invType.name
            data.OnClick = self.OnTypeClick
            data.invtype = invType
            data.sublevel = sublevel + 1
            data.GetMenu = self.OnTypeMenu
            data.ignoreRightClick = 1
            data.showinfo = 1
            data.typeID = invType.typeID
            subList.append((invType.name, listentry.Get('GenericMarketItem', data=data)))

        subList = [ item[1] for item in localization.util.Sort(subList, key=lambda x: x[0]) ]
        return subList

    def GetTypesByMetaGroups(self, typeIDs):
        typesByMetaGroupID = defaultdict(list)
        for typeID in typeIDs:
            invType = cfg.invtypes.Get(typeID)
            metaType = cfg.invmetatypes.GetIfExists(typeID)
            if metaType is None:
                metaGroupID = None
            else:
                metaGroupID = metaType.metaGroupID
                if metaGroupID == const.metaGroupStoryline:
                    metaGroupID = const.metaGroupFaction
            typesByMetaGroupID[metaGroupID].append(invType)

        return typesByMetaGroupID

    def OnMetaGroupClicked(self, *args):
        self.sr.tabs.ShowPanelByName(localization.GetByLabel('UI/Common/Groups'))

    def GetGroupListForBrowse(self, nodedata = None, newitems = 0):
        scrolllist = []
        if nodedata and nodedata.marketGroupInfo.hasTypes:
            typesByMetaGroupID = self.GetTypesByMetaGroups(nodedata.typeIDs)
            for metaGroupID, types in sorted(typesByMetaGroupID.items()):
                subList = []
                if len(types) == 0:
                    continue
                categoryID = types[0].categoryID
                if metaGroupID in (const.metaGroupStoryline,
                 const.metaGroupFaction,
                 const.metaGroupOfficer,
                 const.metaGroupDeadspace) and categoryID in (const.categoryModule, const.categoryDrone, const.categoryStructure):
                    if metaGroupID in (const.metaGroupStoryline, const.metaGroupFaction):
                        label = localization.GetByLabel('UI/Market/FactionAndStoryline')
                    else:
                        label = cfg.invmetagroups.Get(metaGroupID).metaGroupName
                    typeIDs = [ t.typeID for t in types ]
                    marketGroupID = nodedata.marketGroupInfo.marketGroupID if nodedata is not None else None
                    data = {'GetSubContent': self.GetScrollListFromTypeList,
                     'label': label,
                     'id': (marketGroupID, metaGroupID),
                     'showlen': 0,
                     'metaGroupID': metaGroupID,
                     'invTypes': types,
                     'sublevel': nodedata.sublevel + 1,
                     'showicon': uix.GetTechLevelIconID(metaGroupID),
                     'state': 'locked',
                     'BlockOpenWindow': True,
                     'OnToggle': self.OnMetaGroupClicked,
                     'typeIDs': typeIDs}
                    subList.append((label, listentry.Get('MarketMetaGroupEntry', data=data)))
                    subList = [ item[1] for item in localization.util.Sort(subList, key=lambda x: x[0]) ]
                else:
                    subList = self._GetScrollListFromTypeList(types, nodedata.sublevel)
                scrolllist += subList

        else:
            marketGroupID = None
            level = 0
            if nodedata:
                marketGroupID = nodedata.marketGroupInfo.marketGroupID
                level = nodedata.sublevel + 1
            grouplist = sm.GetService('marketutils').GetMarketGroups()[marketGroupID]
            for marketGroupInfo in grouplist:
                if not len(marketGroupInfo.types):
                    continue
                if self.destroyed:
                    return
                typeIDs = self.FilterItemsForBrowse(marketGroupInfo)
                if len(typeIDs) == 0:
                    continue
                if level in (0, 1):
                    groupHint = marketGroupInfo.description
                else:
                    groupHint = ''
                groupID = (marketGroupInfo.marketGroupName, marketGroupInfo.marketGroupID)
                data = {'GetSubContent': self.GetGroupListForBrowse,
                 'label': marketGroupInfo.marketGroupName,
                 'id': groupID,
                 'typeIDs': typeIDs,
                 'iconMargin': 18,
                 'showlen': 0,
                 'marketGroupInfo': marketGroupInfo,
                 'sublevel': level,
                 'state': 'locked',
                 'OnClick': self.LoadGroup,
                 'showicon': [None, 'hide'][marketGroupInfo.hasTypes],
                 'iconID': marketGroupInfo.iconID,
                 'selected': False,
                 'BlockOpenWindow': 1,
                 'MenuFunction': self.SelectFolderMenu,
                 'hint': groupHint}
                if not level and marketGroupInfo.description:
                    data['hint'] = marketGroupInfo.description
                if marketGroupInfo.hasTypes and getattr(self, 'groupListData', None) and self.groupListData.marketGroupID != marketGroupInfo.marketGroupID:
                    uicore.registry.SetListGroupOpenState(groupID, 0)
                scrolllist.append(((marketGroupInfo.hasTypes, marketGroupInfo.marketGroupName), listentry.Get('Group', data)))

            scrolllist = [ item for item in localization.util.Sort(scrolllist, key=lambda x: x[0][1]) ]
            scrolllist = [ item[1] for item in sorted(scrolllist, key=lambda x: x[0][0]) ]
        return scrolllist

    def LoadGroup(self, group, *args):
        self.state = uiconst.UI_DISABLED
        try:
            if group.sr.node.marketGroupInfo.hasTypes:
                groupID = group.sr.node.marketGroupInfo.marketGroupID
                for entry in self.sr.typescroll.GetNodes():
                    if not (entry.marketGroupInfo and entry.marketGroupInfo.hasTypes):
                        continue
                    if entry.marketGroupInfo.marketGroupID == groupID:
                        if not entry.panel:
                            entry.open = 1
                            self.sr.typescroll.PrepareSubContent(entry)
                        self.sr.typescroll.SelectNode(entry)
                        self.sr.typescroll.ShowNodeIdx(entry.idx)
                        if entry.open or self.groupListData is None or self.groupListData.get('marketGroupID', None) != groupID:
                            self.groupListData = entry.marketGroupInfo
                            self.sr.tabs.ShowPanelByName(localization.GetByLabel('UI/Common/Groups'))
                    else:
                        if not entry.open:
                            continue
                        if entry.panel:
                            entry.panel.Toggle()
                        else:
                            entry.open = 0
                            if entry.subNodes:
                                rm = entry.subNodes
                                entry.subNodes = []
                                entry.open = 0
                                self.sr.typescroll.RemoveEntries(rm)

        finally:
            self.state = uiconst.UI_PICKCHILDREN

    def GetAttrDict(self, typeID):
        ret = {}
        for each in cfg.dgmtypeattribs.get(typeID, []):
            attribute = cfg.dgmattribs.Get(each.attributeID)
            if attribute.attributeCategory == 9:
                ret[each.attributeID] = getattr(cfg.invtypes.Get(typeID), attribute.attributeName)
            else:
                ret[each.attributeID] = each.value

        if not ret.has_key(const.attributeCapacity) and cfg.invtypes.Get(typeID).capacity:
            ret[const.attributeCapacity] = cfg.invtypes.Get(typeID).capacity
        attrInfo = sm.GetService('godma').GetType(typeID)
        for each in attrInfo.displayAttributes:
            ret[each.attributeID] = each.value

        return ret

    def GetActiveShipSlots(self):
        """
            hml > high:1, med:2 or low:3
        
        """
        ship = sm.GetService('godma').GetItem(eve.session.shipid)
        if ship is None:
            return 0
        hiSlots = getattr(ship, 'hiSlots', 0)
        medSlots = getattr(ship, 'medSlots', 0)
        lowSlots = getattr(ship, 'lowSlots', 0)
        rigSlots = getattr(ship, 'rigSlots', 0)
        flags = []
        key = uix.FitKeys()
        for gidx in xrange(3):
            for sidx in xrange(8):
                flags.append(getattr(const, 'flag%sSlot%s' % (key[gidx], sidx)))

        for module in ship.modules:
            if module.flagID not in flags:
                continue
            for effect in module.effects.itervalues():
                if effect.effectID == const.effectHiPower:
                    hiSlots -= 1
                elif effect.effectID == const.effectMedPower:
                    medSlots -= 1
                elif effect.effectID == const.effectLoPower:
                    lowSlots -= 1
                elif effect.effectID == const.effectRigSlot:
                    rigSlots -= 1

        return (hiSlots,
         medSlots,
         lowSlots,
         rigSlots)

    def GetMySkills(self):
        return sm.GetService('skills').MySkillLevelsByID()

    @telemetry.ZONE_METHOD
    def ShowGroupPage(self, *args):
        if self.updatingGroups:
            return
        self.updatingGroups = 0
        self.PopulateAsksForMyRange()
        try:
            self.groupScroll.Flush()
            group = self.groupListData
            if group:
                self.groupScroll.ShowNoContentHint(localization.GetByLabel('UI/Market/Marketbase/Loading'))
                freeslots = self.GetActiveShipSlots()
                self.mine = mySkills = self.GetMySkills()
                dataByTypeID = {data.typeID:data for data in self.FilterItemsForGroupPage(group)}
                typesByMetaGroupID = self.GetTypesByMetaGroups(dataByTypeID.keys())
                scrolllist = []
                for _, invTypes in sorted(typesByMetaGroupID.iteritems()):
                    subList = []
                    if len(invTypes) == 0:
                        continue
                    for invType in invTypes:
                        subList.append((invType.name, dataByTypeID[invType.typeID]))

                    subList = [ item[1] for item in localization.util.Sort(subList, key=lambda x: x[0]) ]
                    scrolllist += subList

                if not scrolllist:
                    noItemsText = localization.GetByLabel('UI/Market/Marketbase/NoItemsAvailable')
                    if settings.user.ui.Get('showonlyavailable', 1):
                        noItemsText += '<br><br>' + localization.GetByLabel('UI/Market/Marketbase/DisableShowOnlyAvailable')
                    self.groupScroll.ShowNoContentHint(noItemsText)
                marketRange = self.GetRange()
                if marketRange == const.rangeStation:
                    bestPriceLocation = localization.GetByLabel('UI/Common/LocationTypes/Station')
                elif marketRange == const.rangeSolarSystem:
                    bestPriceLocation = localization.GetByLabel('UI/Common/LocationTypes/System')
                else:
                    bestPriceLocation = localization.GetByLabel('UI/Common/LocationTypes/Region')
                for data in scrolllist:
                    invtype = cfg.invtypes.Get(data.typeID)
                    entryData = uiutil.Bunch()
                    entryData.marketData = data
                    entryData.invType = invtype
                    entryData.typeImageAttributes = uiutil.Bunch(width=64, height=64, src='typeicon:%s' % data.typeID, bumped=True, showfitting=True, showtechlevel=True)
                    entryData.freeslots = freeslots
                    entryData.mySkills = mySkills
                    desc = invtype.description.replace('\r\n', '<br>').strip()
                    if desc.endswith('<br>'):
                        desc = desc[:len(desc) - 4]
                    entryData.description = desc
                    jump = ''
                    if data.qty:
                        jumps = int(data.jumps)
                        if jumps == 0:
                            jump = localization.GetByLabel('UI/Market/Marketbase/InThisSystem')
                        elif jumps == -1:
                            jump = localization.GetByLabel('UI/Market/Marketbase/InThisStation')
                        else:
                            jump = localization.GetByLabel('UI/Market/Marketbase/JumpsAway', jump=data.jumps)
                    if data.qty > 0:
                        entryData.unitsAvailable = localization.GetByLabel('UI/Market/Marketbase/UnitsAvailable', quantity=int(data.qty), numberOfJumps=jump)
                    entryData.bestPrice = localization.GetByLabel('UI/Market/Marketbase/BestPriceIn', place=bestPriceLocation)
                    MarketGroupEntry(parent=self.groupScroll, data=entryData)

                self.groupScroll.HideNoContentHint()
            else:
                self.groupScroll.ShowNoContentHint(localization.GetByLabel('UI/Market/Marketbase/SelectGroupToBrowse'))
        finally:
            if self.destroyed:
                return
            self.updatingGroups = 0

    def Load(self, key):
        if key == 'marketdata':
            self.lastdetailTab = localization.GetByLabel('UI/Market/MarketData')
            self.LoadMarketData()
        elif key == 'quickbar':
            self.sr.searchparent.display = False
            self.sr.typescroll.multiSelect = 1
            self.LoadQuickBar()
        elif key == 'details':
            self.LoadDetails()
        elif key == 'pricehistory':
            self.lastdetailTab = localization.GetByLabel('UI/Market/Marketbase/PriceHistory')
            self.LoadPriceHistory()
        elif key == 'browse':
            self.sr.searchparent.display = True
            self.sr.typescroll.multiSelect = 0
            self.LoadMarketListOrSearch()
        elif key == 'groups':
            self.ShowGroupPage()
        elif key == 'myorders':
            self.LoadOrders()
        elif key == 'corporders':
            self.LoadCorpOrders()

    def LoadOrders(self, *args):
        if not getattr(self, 'ordersInited', 0):
            self.sr.myorders.Setup('market')
            self.ordersInited = 1
        self.sr.myorders.ShowOrders()

    def LoadCorpOrders(self, *args):
        if not getattr(self, 'corpordersInited', 0):
            self.sr.corporders.Setup('market')
            self.corpordersInited = 1
        self.sr.corporders.ShowOrders(isCorp=True)

    def Search(self, *args):
        self.sr.searchInput.RegisterHistory()
        self.sr.filtericon.Disable()
        self.sr.filtericon.hint = localization.GetByLabel('UI/Market/FiltersDontApply')
        self.sr.quickButtons.state = uiconst.UI_HIDDEN
        search = self.sr.searchInput.GetValue().lower()
        if not search or search == ' ':
            pleaseTypeAndSearchLabel = localization.GetByLabel('UI/Market/PleaseTypeAndSearch')
            self.sr.typescroll.Load(contentList=[listentry.Get('Generic', {'label': pleaseTypeAndSearchLabel})])
            return
        self.sr.typescroll.Load(contentList=[])
        self.sr.typescroll.ShowHint(localization.GetByLabel('UI/Common/Searching'))
        t = uix.TakeTime('Market::GetSearchResult', self.GetSearchResult)
        if not t:
            t = [listentry.Get('Generic', {'label': localization.GetByLabel('UI/Market/NothingFoundWithSearch', search=search)})]
        self.sr.typescroll.ShowHint()
        self.sr.typescroll.Load(contentList=t)

    def SetChangeFuncs(self):
        self.OnChangeFuncs['market_filter_price_min'] = self.OnChange_minEdit_market_filter_price
        self.OnChangeFuncs['market_filter_price_max'] = self.OnChange_maxEdit_market_filter_price
        self.OnChangeFuncs['market_filter_jumps_min'] = self.OnChange_minEdit_market_filter_jump
        self.OnChangeFuncs['market_filter_jumps_max'] = self.OnChange_maxEdit_market_filter_jumps
        self.OnChangeFuncs['market_filter_quantity_min'] = self.OnChange_minEdit_market_filter_quantity
        self.OnChangeFuncs['market_filter_quantity_max'] = self.OnChange_maxEdit_market_filter_quantity
        self.OnChangeFuncs['market_filters_sellorderdev_min'] = self.OnChange_minEdit_market_filters_sellorderdev
        self.OnChangeFuncs['market_filters_sellorderdev_max'] = self.OnChange_maxEdit_market_filters_sellorderdev
        self.OnChangeFuncs['market_filters_buyorderdev_min'] = self.OnChange_minEdit_market_filters_buyorderdev
        self.OnChangeFuncs['market_filters_buyorderdev_max'] = self.OnChange_maxEdit_market_filters_buyorderdev

    def LoadDetails(self):
        filtersInUse = self.FiltersInUse2()
        if not self.detailsInited:
            uiprimitives.Container(name='push', parent=self.sr.detailsparent, align=uiconst.TOTOP, height=const.defaultPadding)
            topPar = uiprimitives.Container(name='topCont', align=uiconst.TOTOP, height=100, parent=self.sr.detailsparent, clipChildren=1)
            self.rightButtonCont = uiprimitives.Container(name='rightButtonCont', align=uiconst.TORIGHT, parent=topPar, width=30)
            top = uiprimitives.Container(name='typeNameCont', align=uiconst.TOALL, parent=topPar, clipChildren=1)
            self.sr.reloadBtn = uicontrols.Button(parent=self.rightButtonCont, label=localization.GetByLabel('UI/Market/Marketbase/Reload'), pos=(const.defaultPadding,
             20,
             0,
             0), func=self.OnReload, align=uiconst.TOPRIGHT)
            self.sr.reloadBtn.state = uiconst.UI_HIDDEN
            self.AdjustRightButtonCont()
            self.goBackBtn = uicontrols.Icon(parent=self.rightButtonCont, align=uiconst.TOPRIGHT, icon='ui_38_16_223', pos=(const.defaultPadding + 34,
             0,
             16,
             16), hint=localization.GetByLabel('UI/Control/EveWindow/Previous'))
            self.goBackBtn.OnClick = self.GoBack
            self.DisableArrow(self.goBackBtn)
            self.goForwardBtn = uicontrols.Icon(parent=self.rightButtonCont, align=uiconst.TOPRIGHT, icon='ui_38_16_224', pos=(const.defaultPadding + 18,
             0,
             16,
             16), hint=localization.GetByLabel('UI/Control/EveWindow/Next'))
            self.goForwardBtn.OnClick = self.GoForward
            self.DisableArrow(self.goForwardBtn)
            self.settingsIcon = uicls.UtilMenu(parent=self.rightButtonCont, align=uiconst.TOPRIGHT, left=4, GetUtilMenu=self.DetailsSettingsMenu, texturePath='res:/UI/Texture/SettingsCogwheel.png', width=18, height=18, iconSize=18)
            self.sr.detailIcon = uicls.MarketGroupItemImage(parent=top, align=uiconst.TOPLEFT, name='detailIcon', left=12, top=2, width=64, height=64)
            self.sr.detailIcon.Hide()
            self.sr.detailGroupTrace = uicontrols.EveLabelMedium(text='', parent=top, top=2, left=86, state=uiconst.UI_NORMAL)
            self.sr.detailGroupTrace.OnClick = (self.ClickGroupTrace, self.sr.detailGroupTrace)
            noTypeSelectedLabel = localization.GetByLabel('UI/Market/Marketbase/NoTypeSelected')
            self.sr.detailTop = uicontrols.EveCaptionMedium(text=noTypeSelectedLabel, parent=top, align=uiconst.TOPLEFT)
            self.sr.detailTop.left = 86
            self.sr.detailTop.top = 20
            self.sr.detailInfoicon = uicontrols.InfoIcon(size=16, left=78, top=0, parent=top, idx=0, state=uiconst.UI_HIDDEN)
            self.sr.detailInfoicon.OnClick = self.ShowInfoFromDetails
            self.sr.detailTypeID = None
            self.browseBtn = uicontrols.ButtonIcon(name='browseBtn', parent=top, align=uiconst.TOPLEFT, width=16, height=16, iconSize=16, texturePath='res:/UI/Texture/classes/MapView/focusIcon.png', hint=localization.GetByLabel('UI/Market/Marketbase/FindInBrowseTab'), func=self.OpenOnType, args=self.sr.detailGroupTrace)
            self.browseBtn.display = False
            self.sr.requirements = RequirementsContainer(parent=top, align=uiconst.TOPLEFT, top=self.sr.detailTop.top + self.sr.detailTop.height, left=self.sr.detailTop.left, width=200)
            self.sr.filtersText = uicontrols.EveLabelMedium(text='', parent=top, align=uiconst.TOPLEFT, top=82, state=uiconst.UI_NORMAL, left=12)
            self.sr.detailtabs = uicontrols.TabGroup(name='tabparent', parent=self.sr.detailsparent)
            self.sr.marketdata = uiprimitives.Container(name='marketinfo', parent=self.sr.detailsparent, pos=(0, 0, 0, 0))
            from eve.client.script.ui.shared.market.pricehistorychart import PriceHistoryParent
            self.sr.pricehistory = PriceHistoryParent(name='pricehistory', parent=self.sr.detailsparent, pos=(0, 0, 0, 0))
            detailtabs = [[localization.GetByLabel('UI/Market/MarketData'),
              self.sr.marketdata,
              self,
              'marketdata',
              None,
              localization.GetByLabel('Tooltips/Market/MarketDetailsData')], [uiutil.FixedTabName('UI/Market/Marketbase/PriceHistory'),
              self.sr.pricehistory,
              self,
              'pricehistory',
              None,
              localization.GetByLabel('Tooltips/Market/MarketDetailsHistory')]]
            self.sr.detailtabs.Startup(detailtabs, 'marketdetailtabs', autoselecttab=1, UIIDPrefix='marketDetailsTab')
            self.detailsInited = 1
            return
        if self.lastdetailTab:
            self.sr.detailtabs.ShowPanelByName(self.lastdetailTab)
        self.ShowFiltersInUse()

    def ShowFiltersInUse(self):
        filtersInUse = self.FiltersInUse2()
        self.sr.filtersText.text = ['', localization.GetByLabel('UI/Market/Marketbase/MarketFilters')][bool(filtersInUse)]
        self.sr.filtersText.hint = ['', filtersInUse][bool(filtersInUse)]

    def DetailsSettingsMenu(self, menuParent):
        grid = menuParent.AddLayoutGrid(columns=4, cellPadding=4)
        priceConfig = settings.user.ui.Get('market_filter_price', 0)
        uicontrols.Checkbox(text=GetByLabel('UI/Market/Marketbase/Price'), configName='market_filter_price', retval=priceConfig == 1, checked=priceConfig, parent=grid, align=uiconst.TOPLEFT, callback=self.OnCheckboxChangeSett, wrapLabel=False)
        self.MakeFloatEdit('market_filter_price', isMin=True, parent=grid, floats=[0, MAXVALUE])
        uicontrols.EveLabelSmall(text='-', parent=grid, align=uiconst.CENTER)
        self.MakeFloatEdit('market_filter_price', isMin=False, parent=grid, floats=[0, MAXVALUE])
        jumpsConfig = settings.user.ui.Get('market_filter_jumps', 0)
        uicontrols.Checkbox(text=GetByLabel('UI/Market/Marketbase/Jumps'), configName='market_filter_jumps', retval=jumpsConfig == 1, checked=jumpsConfig, parent=grid, align=uiconst.TOPLEFT, callback=self.OnCheckboxChangeSett, wrapLabel=False)
        self.MakeIntEdit('market_filter_jumps', isMin=True, parent=grid, ints=[0, None])
        uicontrols.EveLabelSmall(text='-', parent=grid, align=uiconst.CENTER)
        self.MakeIntEdit('market_filter_jumps', isMin=False, parent=grid, ints=[0, None])
        qtyConfig = settings.user.ui.Get('market_filter_quantity', 0)
        uicontrols.Checkbox(text=GetByLabel('UI/Common/Quantity'), configName='market_filter_quantity', retval=qtyConfig == 1, checked=qtyConfig, parent=grid, align=uiconst.TOPLEFT, callback=self.OnCheckboxChangeSett, wrapLabel=False)
        self.MakeIntEdit('market_filter_quantity', isMin=True, parent=grid, ints=[0, None])
        uicontrols.EveLabelSmall(text='-', parent=grid, align=uiconst.CENTER)
        self.MakeIntEdit('market_filter_quantity', isMin=False, parent=grid, ints=[0, None])
        subGrid = LayoutGrid(columns=3, cellPadding=(0, 0, 20, 0))
        showOrdersLabel = EveLabelSmall(text=GetByLabel('UI/Market/Marketbase/ShowOrdersIn'), left=2)
        subGrid.AddCell(cellObject=showOrdersLabel, colSpan=3)
        boxes = self.GetSecStatusBoxes()
        for label, configname, retval, checked, hint in boxes:
            cb = uicontrols.Checkbox(text='%s' % label, parent=subGrid, configName=configname, retval=retval, checked=checked, callback=self.OnCheckboxChangeSett, align=uiconst.TOPLEFT, wrapLabel=False)

        subGrid.RefreshGridLayout()
        grid.AddCell(cellObject=subGrid, colSpan=4)
        sellConfig = settings.user.ui.Get('market_filters_sellorderdev', 0)
        uicontrols.Checkbox(text=GetByLabel('UI/Market/Marketbase/SellOrdersDeviation'), configName='market_filters_sellorderdev', retval=sellConfig == 1, checked=sellConfig, parent=grid, align=uiconst.TOPLEFT, hint=GetByLabel('UI/Market/Marketbase/SellOrdersDeviationToolTip'), callback=self.OnCheckboxChangeSett, wrapLabel=False)
        self.MakeIntEdit('market_filters_sellorderdev', isMin=True, parent=grid, ints=[-100, None])
        uicontrols.EveLabelSmall(text='-', parent=grid, align=uiconst.CENTER)
        self.MakeIntEdit('market_filters_sellorderdev', isMin=False, parent=grid, ints=[-100, None])
        buyConfig = settings.user.ui.Get('market_filters_buyorderdev', 0)
        uicontrols.Checkbox(text=GetByLabel('UI/Market/Marketbase/BuyOrdersDeviation'), configName='market_filters_buyorderdev', retval=buyConfig == 1, checked=buyConfig, parent=grid, align=uiconst.TOPLEFT, hint=GetByLabel('UI/Market/Marketbase/BuyOrdersDeviationToolTip'), callback=self.OnCheckboxChangeSett, wrapLabel=False)
        self.MakeIntEdit('market_filters_buyorderdev', isMin=True, parent=grid, ints=[-100, None])
        uicontrols.EveLabelSmall(text='-', parent=grid, align=uiconst.CENTER)
        self.MakeIntEdit('market_filters_buyorderdev', isMin=False, parent=grid, ints=[-100, None])
        currentMyOrdersValue = settings.user.ui.Get('hilitemyorders', 0)
        mmo = uicontrols.Checkbox(text=GetByLabel('UI/Market/Marketbase/MarkMyOrders'), configName='hilitemyorders', retval=currentMyOrdersValue == 1, checked=currentMyOrdersValue, hint=GetByLabel('UI/Market/Marketbase/MarkMyOrdersHint'), callback=self.OnCheckboxChangeSett)
        grid.AddCell(cellObject=mmo, colSpan=4)
        menuParent.AddButton(text=GetByLabel('UI/Browser/BrowserSettings/ResetCacheLocation'), callback=self.ResetDetailsSettings)

    def MakeIntEdit(self, configName, isMin, parent, ints):
        if isMin:
            funcKey = '%s_min' % configName
            editName = 'minEdit_%s' % configName
        else:
            funcKey = '%s_max' % configName
            editName = 'maxEdit_%s' % configName
        edit = uicontrols.SinglelineEdit(name=editName, setvalue=settings.user.ui.Get(editName, 0), parent=parent, ints=ints, OnChange=self.OnChangeFuncs[funcKey])
        edit.AutoFitToText(util.FmtAmt(sys.maxint))
        return edit

    def MakeFloatEdit(self, configName, isMin, parent, floats):
        if isMin:
            funcKey = '%s_min' % configName
            editName = 'minEdit_%s' % configName
        else:
            funcKey = '%s_max' % configName
            editName = 'maxEdit_%s' % configName
        edit = uicontrols.SinglelineEdit(name=editName, setvalue=settings.user.ui.Get(editName, 0), parent=parent, floats=[floats[0], floats[1], 2], OnChange=self.OnChangeFuncs[funcKey])
        edit.AutoFitToText(util.FmtAmt(sys.maxint))
        return edit

    def GetSecStatusBoxes(self):
        highSecurityLabel = GetByLabel('UI/Common/HighSec')
        highSecurityToolTipLabel = GetByLabel('UI/Market/Marketbase/FilterHighSecurityToolTip')
        lowSecurityLabel = GetByLabel('UI/Common/LowSec')
        lowSecurityToolTipLabel = GetByLabel('UI/Market/Marketbase/FilterLowSecurityToolTip')
        zeroSecurityLabel = GetByLabel('UI/Common/NullSec')
        zeroSecurityToolTipLabel = GetByLabel('UI/Market/Marketbase/FilterZeroSecurityToolTip')
        boxes = [(highSecurityLabel,
          'market_filter_highsec',
          settings.user.ui.Get('market_filter_highsec', 0) == 1,
          settings.user.ui.Get('market_filter_highsec', 0),
          highSecurityToolTipLabel), (lowSecurityLabel,
          'market_filter_lowsec',
          settings.user.ui.Get('market_filter_lowsec', 0) == 1,
          settings.user.ui.Get('market_filter_lowsec', 0),
          lowSecurityToolTipLabel), (zeroSecurityLabel,
          'market_filter_zerosec',
          settings.user.ui.Get('market_filter_zerosec', 0) == 1,
          settings.user.ui.Get('market_filter_zerosec', 0),
          zeroSecurityToolTipLabel)]
        return boxes

    def OnReload(self, *args):
        self.sr.reloadBtn.state = uiconst.UI_HIDDEN
        self.AdjustRightButtonCont()
        self.sr.marketdata.children[0].OnReload()
        if self.sr.sbTabs.GetSelectedArgs() == 'browse':
            self.LoadMarketListOrSearch()
        self.OnOrderChangeTimer = None
        self.lastOnOrderChangeTime = blue.os.GetWallclockTime()

    def ShowInfoFromDetails(self, *args):
        typeID = self.GetTypeIDFromDetails()
        if typeID is not None:
            sm.GetService('info').ShowInfo(typeID)

    def PreviewFromDetails(self, *args):
        typeID = self.GetTypeIDFromDetails()
        if typeID is not None:
            sm.GetService('preview').PreviewType(typeID)

    def GetTypeIDFromDetails(self):
        typeID = None
        invtype = self.GetSelection()
        if invtype:
            typeID = invtype.typeID
        if typeID is None:
            if self.sr.Get('detailTypeID'):
                typeID = self.sr.detailTypeID
        return typeID

    def ClickGroupTrace(self, trace, *args):
        if trace.sr.marketGroupInfo:
            self.groupListData = trace.sr.marketGroupInfo
            self.sr.tabs.ShowPanelByName(localization.GetByLabel('UI/Common/Groups'))

    def OpenOnType(self, trace, *args):
        typeID = trace.typeID
        if trace.sr.marketGroupInfo:
            self.groupListData = trace.sr.marketGroupInfo
        searchValueBefore = self.sr.searchInput.GetValue().strip()
        if searchValueBefore:
            self.sr.searchInput.SetText('')
            self.sr.searchInput.caretIndex = (0, 0)
            self.sr.searchInput.CheckHintText()
            self.sr.searchInput.RefreshCaretPosition()
        reloadingDone = False
        if not self.sr.sbTabs.GetSelectedArgs() == 'browse':
            self.sr.sbTabs.ShowPanelByName(localization.GetByLabel('UI/Market/Browse'))
            reloadingDone = True
        if settings.user.ui.Get('showonlyavailable', True):
            settings.user.ui.Set('showonlyavailable', False)
            self.LoadMarketListOrSearch()
            reloadingDone = True
        if searchValueBefore and not reloadingDone:
            self.LoadMarketListOrSearch()
        if self.sr.typescroll:
            self.OpenOnTypeID(typeID)

    def OpenOnTypeID(self, typeID, groupsToSkip = [], *args):
        for node in self.sr.typescroll.GetNodes():
            if typeID in node.get('typeIDs', []) and node.id not in groupsToSkip:
                if self.sr.typescroll.scrollingRange:
                    position = node.scroll_positionFromTop / float(self.sr.typescroll.scrollingRange)
                    self.sr.typescroll.ScrollToProportion(position, threaded=False)
                groupsToSkipCopy = groupsToSkip[:] + [node.id]
                if not node.open:
                    if node.panel is not None:
                        node.panel.OnClick()
                    else:
                        uicore.registry.SetListGroupOpenState(node.id, True)
                    blue.synchro.Yield()
                    return self.OpenOnTypeID(typeID, groupsToSkipCopy)
            elif node.get('typeID', None) == typeID:
                self.sr.typescroll.SelectNode(node)
                break

    def LoadQuickBar(self, selectFolder = 0, *args):
        self.sr.quickButtons.state = uiconst.UI_PICKCHILDREN
        self.selectFolder = selectFolder
        self.folders = settings.user.ui.Get('quickbar', {})
        if not self.folders:
            if settings.user.ui.Get('marketquickbar', 0):
                self.LoadOldQuickBar()
        scrolllist = self.LoadQuickBarItems(selectFolder)
        if self.selectFolder:
            selectAFolderLabel = localization.GetByLabel('UI/Market/Marketbase/SelectAFolder')
            result = self.ListWnd([], 'item', selectAFolderLabel, None, 1, contentList=scrolllist)
            if not result:
                return False
            id, parentDepth = result
            if self.depth + 1 + parentDepth + 1 > 7:
                msg = localization.GetByLabel('UI/Market/Marketbase/DeepQuickbarFolder', folderDepth=self.depth + 1 + parentDepth + 1)
                yesNo = eve.Message('AskAreYouSure', {'cons': msg}, uiconst.YESNO)
                return [False, id][yesNo == uiconst.ID_YES]
            return id
        self.sr.typescroll.Load(contentList=scrolllist)

    def LoadOldQuickBar(self):
        items = settings.user.ui.Get('marketquickbar', [])
        for each in items:
            n = util.KeyVal()
            n.parent = 0
            n.id = self.lastid
            n.label = each
            self.folders[n.id] = n
            self.lastid += 1

        settings.user.ui.Delete('marketquickbar')

    def LoadMarketData(self, *args):
        invtype = self.GetSelection()
        if self.sr.marketdata:
            if not len(self.sr.marketdata.children):
                MarketData(name='marketdata', parent=self.sr.marketdata, pos=(0, 0, 0, 0))
            if invtype:
                self.sr.marketdata.children[0].LoadType(invtype)
                self.StoreTypeInHistory(invtype.typeID)
            else:
                self.sr.marketdata.children[0].ReloadType()
            self.sr.reloadBtn.state = uiconst.UI_HIDDEN
            self.AdjustRightButtonCont()

    def LoadPriceHistory(self, invtype = None, *args):
        invtype = invtype or self.GetSelection()
        if not invtype:
            return
        if self.sr.pricehistory:
            self.sr.reloadBtn.state = uiconst.UI_HIDDEN
            self.AdjustRightButtonCont()
            if not self.sr.pricehistory.inited:
                self.sr.pricehistory.Startup()
            self.sr.pricehistory.LoadType(invtype)
            self.StoreTypeInHistory(invtype.typeID)

    def GetSearchResult(self):
        marketTypes = sm.GetService('marketutils').GetMarketTypes()
        marketTypes = dict([ [i, None] for i in marketTypes ])
        search = self.sr.searchInput.GetValue().lower()
        showOnlyAvailable = settings.user.ui.Get('showonlyavailable', 1)
        if self.sr.lastSearchResult and self.sr.lastSearchResult[0] == search and self.sr.lastSearchResult[2] == showOnlyAvailable:
            scrollList = self.sr.lastSearchResult[1][:]
        else:
            scrollList = []
            byCategories = {}
            if search:
                res = [ invtype.typeID for invtype in cfg.invtypes if invtype.typeID in marketTypes and invtype.typeName.lower().find(search) != -1 ]
                allMarketGroups = sm.GetService('marketutils').GetMarketGroups()[None]
                myCategories = {}
                for typeID in res:
                    for mg in allMarketGroups:
                        if typeID in mg.types:
                            topMarketCategory = mg
                            break
                    else:
                        topMarketCategory = None

                    if topMarketCategory is None:
                        continue
                    if topMarketCategory.marketGroupID in byCategories:
                        byCategories[topMarketCategory.marketGroupID].append(typeID)
                    else:
                        byCategories[topMarketCategory.marketGroupID] = [typeID]
                        myCategories[topMarketCategory.marketGroupID] = topMarketCategory

                if len(byCategories) > 1:
                    for categoryID, categoryTypeIDs in byCategories.iteritems():
                        category = myCategories[categoryID]
                        data = {'GetSubContent': self.GetSeachCategory,
                         'label': category.marketGroupName,
                         'id': ('searchGroups', categoryID),
                         'showlen': 0,
                         'sublevel': 0,
                         'state': 'locked',
                         'BlockOpenWindow': True,
                         'categoryID': category.marketGroupID,
                         'typeIDs': categoryTypeIDs,
                         'iconID': category.iconID,
                         'hint': category.description}
                        group = listentry.Get('Group', data)
                        scrollList.append(group)

                else:
                    for categoryID, categoryTypeIDs in byCategories.iteritems():
                        fakeNodeData = util.KeyVal(typeIDs=categoryTypeIDs, sublevel=-1, categoryID=categoryID)
                        results = self.GetSeachCategory(fakeNodeData)
                        scrollList.extend(results)

        self.sr.lastSearchResult = (search, scrollList[:], showOnlyAvailable)
        return scrollList

    def GetSeachCategory(self, nodedata, *args):
        types = nodedata.typeIDs
        typesByMetaGroupID = self.GetTypesByMetaGroups(types)
        sublevel = nodedata.sublevel
        categoryID = nodedata.categoryID
        scrollList = []
        for metaGroupID, types in sorted(typesByMetaGroupID.items()):
            specialItemGroups = (const.metaGroupStoryline,
             const.metaGroupFaction,
             const.metaGroupOfficer,
             const.metaGroupDeadspace)
            if metaGroupID in specialItemGroups:
                searchGroup = self.GetSearchSubGroup(metaGroupID, types, sublevel=sublevel + 1, categoryID=categoryID)
                scrollList.append((searchGroup.label, searchGroup))
            else:
                for t in types:
                    searchEntry = self.GetSearchEntry(t, sublevel=sublevel + 1)
                    scrollList.append((' ' + t.name, searchEntry))
                    blue.pyos.BeNice()

        scrollList = [ item[1] for item in localization.util.Sort(scrollList, key=lambda x: x[0]) ]
        return scrollList

    def GetSearchSubGroup(self, metaGroupID, types, sublevel = 0, categoryID = -1, *args):
        if metaGroupID in (const.metaGroupStoryline, const.metaGroupFaction):
            label = localization.GetByLabel('UI/Market/FactionAndStoryline')
        else:
            label = cfg.invmetagroups.Get(metaGroupID).metaGroupName
        typeIDs = [ t.typeID for t in types ]
        data = {'GetSubContent': self.GetSearchScrollListFromTypeList,
         'label': label,
         'id': ('searchGroups', (metaGroupID, categoryID)),
         'showlen': 0,
         'metaGroupID': metaGroupID,
         'invTypes': types,
         'sublevel': sublevel,
         'showicon': uix.GetTechLevelIconID(metaGroupID),
         'state': 'locked',
         'BlockOpenWindow': True,
         'OnToggle': self.OnMetaGroupClicked,
         'typeIDs': typeIDs}
        groupEntry = listentry.Get('MarketMetaGroupEntry', data=data)
        return groupEntry

    def GetSearchScrollListFromTypeList(self, nodedata):
        subList = []
        invTypes = nodedata.invTypes
        sublevel = nodedata.sublevel
        for invType in invTypes:
            searchEntry = self.GetSearchEntry(invType, sublevel=sublevel + 1)
            subList.append((invType.name, searchEntry))

        subList = [ item[1] for item in localization.util.Sort(subList, key=lambda x: x[0]) ]
        return subList

    def GetSearchEntry(self, typeInfo, sublevel = 0, *args):
        data = util.KeyVal()
        data.label = typeInfo.name
        data.GetMenu = self.OnTypeMenu
        data.invtype = typeInfo
        data.showinfo = 1
        data.sublevel = sublevel
        data.typeID = typeInfo.typeID
        data.ignoreRightClick = 1
        onlyShowAvailable = settings.user.ui.Get('showonlyavailable', 0)
        if onlyShowAvailable and self.asksForMyRange.get(typeInfo.typeID, None) is None:
            data.inRange = False
        else:
            data.inRange = True
        entry = listentry.Get('GenericMarketItem', data=data)
        return entry

    def OnTypeClick(self, entry, *args):
        if not self.sr.typescroll.GetSelected():
            return
        if self.loadingType:
            self.pendingType = 1
            return
        self.sr.quickType = None
        self.ReloadType()

    def OnTypeMenu(self, entry):
        invtype = entry.sr.node.invtype
        categoryID = invtype.categoryID
        menu = [(uiutil.MenuLabel('UI/Inventory/ItemActions/AddTypeToMarketQuickbar'), self.AddTypeToQuickBar, (entry.sr.node.typeID,)), (uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (invtype.typeID,))]
        if categoryID in const.previewCategories and invtype.Icon() and invtype.Icon().iconFile != '':
            previewLabel = uiutil.MenuLabel('UI/Market/Marketbase/Preview')
            menu.append((previewLabel, sm.GetService('preview').PreviewType, (entry.sr.node.invtype.typeID,)))
        if industryCommon.IsBlueprintCategory(categoryID):
            from eve.client.script.ui.shared.industry.industryWnd import Industry
            menu.append((localization.GetByLabel('UI/Industry/ViewInIndustry'), Industry.OpenOrShowBlueprint, (None, entry.sr.node.invtype.typeID)))
        if eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
            menu.append(None)
            menu += sm.GetService('menu').GetGMTypeMenu(entry.sr.node.invtype.typeID)
        return menu

    def ShowInfo(self, typeID):
        sm.GetService('info').ShowInfo(typeID)

    def AddTypeToQuickBar(self, typeID, parent = 0):
        settings.user.ui.Set('quickbar', self.folders)
        settings.user.ui.Set('quickbar_lastid', self.lastid)
        sm.GetService('marketutils').AddTypeToQuickBar(typeID, parent, fromMarket=True)
        self.lastid = settings.user.ui.Get('quickbar_lastid', 0)
        self.folders = settings.user.ui.Get('quickbar', {})

    def LoadQuickType(self, quick = None, *args):
        if quick:
            self.sr.quickType = quick.invType
            self.ReloadType()

    def LoadTypeID_Ext(self, typeID):
        self.sr.quickType = cfg.invtypes.Get(typeID)
        self.ReloadType()

    def ReloadType(self):
        self.pendingType = 0
        self.loadingType = 1
        blue.pyos.synchro.Yield()
        try:
            self.sr.tabs.ShowPanelByName(localization.GetByLabel('UI/Common/Details'))
        except StandardError as e:
            self.loadingType = 0
            raise e

        blue.pyos.synchro.Yield()
        invtype = self.GetSelection()
        if not invtype:
            self.loadingType = 0
            return
        self.sr.detailTop.text = invtype.name
        self.sr.detailIcon.attrs = uiutil.Bunch(width=64, height=64, src='typeicon:%s' % invtype.typeID, bumped=True, showfitting=True, showtechlevel=True)
        self.sr.detailIcon.typeName = invtype.name
        self.sr.detailIcon.LoadTypeIcon(invtype.typeID)
        self.sr.detailIcon.SetState(uiconst.UI_NORMAL)
        self.sr.detailIcon.Show()
        left = self.sr.detailTop.left + self.sr.detailTop.textwidth + 8
        top = self.sr.detailTop.top + 4
        self.sr.detailInfoicon.state = uiconst.UI_NORMAL
        self.sr.detailInfoicon.top = top
        self.sr.detailInfoicon.left = left
        self.browseBtn.display = True
        self.browseBtn.top = top
        self.browseBtn.left = left + 20
        self.sr.detailTypeID = invtype.typeID
        self.sr.requirements.LoadTypeRequirements(self.sr.detailTypeID)
        marketGroup, trace = sm.GetService('marketutils').FindMarketGroup(invtype.typeID)
        if marketGroup:
            self.sr.detailGroupTrace.sr.marketGroupInfo = marketGroup
            self.sr.detailGroupTrace.text = trace
            self.sr.detailGroupTrace.typeID = invtype.typeID
        else:
            self.sr.detailGroupTrace.text = ''
            self.sr.detailGroupTrace.sr.marketGroupInfo = None
            self.sr.detailGroupTrace.typeID = None
        self.loadingType = 0
        if self.pendingType:
            self.ReloadType()

    def GetSelection(self):
        if self.sr.quickType:
            return self.sr.quickType
        selection = self.sr.typescroll.GetSelected()
        if not selection:
            return None
        if hasattr(selection[0], 'invtype'):
            return selection[0].invtype

    def ResetQuickbar(self):
        self.folders = {}
        settings.user.ui.Set('quickbar', self.folders)
        self.lastid = 0
        settings.user.ui.Set('quickbar_lastid', self.lastid)
        sm.ScatterEvent('OnMarketQuickbarChange')

    def ResetFilterSettings(self):
        settings.user.ui.Set('showonlyskillsfor', False)
        settings.user.ui.Set('showhavecpuandpower', False)
        settings.user.ui.Set('shownewskills', False)
        settings.user.ui.Set('showonlyavailable', True)
        settings.user.ui.Set('autorefresh', True)
        if self.sr.sbTabs.GetSelectedArgs() == 'browse':
            self.LoadMarketListOrSearch()

    def ResetDetailsSettings(self):
        settings.user.ui.Set('market_filter_price', False)
        settings.user.ui.Set('minEdit_market_filter_price', 0)
        settings.user.ui.Set('maxEdit_market_filter_price', 100000)
        settings.user.ui.Set('market_filter_jumps', False)
        settings.user.ui.Set('minEdit_market_filter_jumps', 0)
        settings.user.ui.Set('maxEdit_market_filter_jumps', 20)
        settings.user.ui.Set('market_filter_quantity', False)
        settings.user.ui.Set('minEdit_market_filter_quantity', 0)
        settings.user.ui.Set('maxEdit_market_filter_quantity', 1000)
        settings.user.ui.Set('market_filter_zerosec', True)
        settings.user.ui.Set('market_filter_lowsec', True)
        settings.user.ui.Set('market_filter_highsec', True)
        settings.user.ui.Set('market_filters_sellorderdev', False)
        settings.user.ui.Set('minEdit_market_filters_sellorderdev', 0)
        settings.user.ui.Set('maxEdit_market_filters_sellorderdev', 0)
        settings.user.ui.Set('market_filters_buyorderdev', False)
        settings.user.ui.Set('minEdit_market_filters_buyorderdev', 0)
        settings.user.ui.Set('maxEdit_market_filters_buyorderdev', 0)
        self.LoadMarketData()
        self.ShowFiltersInUse()

    def LoadQuickBarItems(self, selectFolder = 0, *args):
        import types
        scrolllist = []
        notes = self.GetItems(parent=0)
        for id, n in notes.items():
            try:
                if type(n.label) == types.UnicodeType:
                    groupID = ('quickbar', id)
                    data = {'GetSubContent': self.GetGroupSubContent,
                     'label': n.label,
                     'id': groupID,
                     'groupItems': self.GroupGetContentIDList(groupID),
                     'iconMargin': 18,
                     'showlen': 0,
                     'state': 0,
                     'sublevel': 0,
                     'MenuFunction': [self.GroupMenu, self.SelectFolderMenu][self.selectFolder],
                     'BlockOpenWindow': 1,
                     'DropData': self.GroupDropNode,
                     'ChangeLabel': self.GroupChangeLabel,
                     'DeleteFolder': self.GroupDeleteFolder,
                     'selected': 1,
                     'hideNoItem': self.selectFolder,
                     'allowGuids': ['listentry.QuickbarGroup', 'listentry.QuickbarItem'],
                     'selectGroup': selectFolder}
                    if self.selectFolder:
                        data['OnDblClick'] = self.OnDblClick
                        if data.get('sublevel', 0) + self.depth >= self.maxdepth:
                            return []
                    scrolllist.append((n.label, listentry.Get('QuickbarGroup', data)))
            except Exception as e:
                log.LogWarn('Failed to load quickbar folder, reason: ', e)
                continue

        if scrolllist:
            scrolllist = [ item[1] for item in localization.util.Sort(scrolllist, key=lambda x: x[0]) ]
        tempScrolllist = []
        if not self.selectFolder:
            for id, n in notes.items():
                try:
                    if type(n.label) == types.IntType:
                        groupID = ('quickbar', id)
                        data = {'label': cfg.invtypes.Get(n.label).name,
                         'typeID': n.label,
                         'id': groupID,
                         'itemID': None,
                         'getIcon': 0,
                         'sublevel': 0,
                         'showinfo': 1,
                         'GetMenu': self.GetQuickItemMenu,
                         'DropData': self.GroupDropNode,
                         'parent': n.parent,
                         'selected': 1,
                         'invtype': cfg.invtypes.Get(n.label),
                         'extraText': n.get('extraText', '')}
                        tempScrolllist.append((cfg.invtypes.Get(n.label).name, listentry.Get('QuickbarItem', data)))
                except Exception as e:
                    log.LogWarn('Failed to load_ quickbar type, reason: ', e)
                    continue

        if tempScrolllist:
            tempScrolllist = [ item[1] for item in localization.util.Sort(tempScrolllist, key=lambda x: x[0]) ]
            scrolllist.extend(tempScrolllist)
        return scrolllist

    def GroupMenu(self, node):
        m = []
        if node.sublevel < self.maxdepth:
            m.append((uiutil.MenuLabel('UI/Market/NewFolder'), self.NewFolder, (node.id[1], node)))
        return m

    def QuickbarHasFolder(self):
        import types
        if settings.user.ui.Get('quickbar', {}):
            for id, node in settings.user.ui.Get('quickbar', {}).items():
                if type(node.label) == types.UnicodeType:
                    return True

        return False

    def SelectFolderMenu(self, node):
        m = []
        if node.sublevel < self.maxdepth:
            if self.QuickbarHasFolder():
                m.append((uiutil.MenuLabel('UI/Market/Marketbase/AddGroupToQuickbarFolder'), self.FolderPopUp, (node,)))
            m.append((uiutil.MenuLabel('UI/Market/Marketbase/AddGroupToQuickbarRoot'), self.FolderPopUp, (node, True)))
        return m

    def FolderPopUp(self, node, root = False):
        self.tempLastid = self.lastid
        self.tempFolders = {}
        self.depth, firstID = self.AddGroupParent(nodedata=node)
        if root:
            id = 0
        else:
            id = self.LoadQuickBar(selectFolder=1)
        if id is not None and id is not False:
            self.tempFolders[firstID].parent = id
            for each in range(firstID, self.tempLastid + 1):
                self.folders[each] = self.tempFolders[each]

            self.lastid = self.tempLastid
            settings.user.ui.Set('quickbar_lastid', self.lastid)

    def GetGroupSubContent(self, nodedata, newitems = 0):
        scrolllist = []
        notelist = self.GetItems(nodedata.id[1])
        if len(notelist):
            qi = 1
            NoteListLength = len(notelist)
            import types
            for id, note in notelist.items():
                if type(note.label) == types.UnicodeType:
                    entry = self.GroupCreateEntry((note.label, id), nodedata.sublevel + 1, selectGroup=self.selectFolder)
                    if entry:
                        scrolllist.append((note.label, entry))

            if scrolllist:
                scrolllist = [ item[1] for item in localization.util.Sort(scrolllist, key=lambda x: x[0]) ]
            tempScrolllist = []
            if not self.selectFolder:
                for id, note in notelist.items():
                    if type(note.label) == types.IntType:
                        entry = self.GroupCreateEntry((note.label, id), nodedata.sublevel + 1)
                        if entry:
                            tempScrolllist.append((cfg.invtypes.Get(note.label).name, entry))

            if tempScrolllist:
                tempScrolllist = [ item[1] for item in localization.util.Sort(tempScrolllist, key=lambda x: x[0]) ]
                scrolllist.extend(tempScrolllist)
            if len(nodedata.groupItems) != len(scrolllist):
                nodedata.groupItems = self.GroupGetContentIDList(nodedata.id)
        return scrolllist

    def GroupCreateEntry(self, id, sublevel, selectGroup = 0):
        note, id = self.folders[id[1]], id[1]
        import types
        if type(note.label) == types.UnicodeType:
            groupID = ('quickbar', id)
            data = {'GetSubContent': self.GetGroupSubContent,
             'label': note.label,
             'id': groupID,
             'groupItems': self.GroupGetContentIDList(groupID),
             'iconMargin': 18,
             'showlen': 0,
             'state': 0,
             'sublevel': sublevel,
             'BlockOpenWindow': 1,
             'parent': note.parent,
             'MenuFunction': self.GroupMenu,
             'ChangeLabel': self.GroupChangeLabel,
             'DeleteFolder': self.GroupDeleteFolder,
             'selected': 1,
             'DropData': self.GroupDropNode,
             'hideNoItem': self.selectFolder,
             'allowGuids': ['listentry.QuickbarGroup', 'listentry.QuickbarItem'],
             'selectGroup': selectGroup}
            if self.selectFolder:
                data['OnDblClick'] = self.OnDblClick
                if data.get('sublevel', 0) + self.depth >= self.maxdepth:
                    return []
            return listentry.Get('QuickbarGroup', data)
        if type(note.label) == types.IntType:
            groupID = ('quickbar', id)
            data = {'label': cfg.invtypes.Get(note.label).name,
             'typeID': note.label,
             'id': groupID,
             'itemID': None,
             'getIcon': 0,
             'sublevel': sublevel,
             'showinfo': 1,
             'GetMenu': self.GetQuickItemMenu,
             'DropData': self.GroupDropNode,
             'parent': note.parent,
             'selected': 1,
             'invtype': cfg.invtypes.Get(note.label),
             'extraText': note.get('extraText', '')}
            return listentry.Get('QuickbarItem', data)
        del self.folders[id]

    def OnDblClick(self, *args):
        pass

    def GroupGetContentIDList(self, id):
        ids = self.GetItems(id[1])
        test = [ (self.folders[id].label, id) for id in ids ]
        return test

    def GetItems(self, parent):
        dict = {}
        for id in self.folders:
            if self.folders[id].parent == parent:
                dict[id] = self.folders[id]

        return dict

    def NewFolderClick(self, *args):
        self.NewFolder(0)

    def GroupChangeLabel(self, id, newname):
        self.RenameFolder(id[1], name=newname)

    def RenameFolder(self, folderID = 0, entry = None, name = None, *args):
        if name is None:
            folderNameLabel = localization.GetByLabel('UI/Market/Marketbase/FolderName')
            typeNewFolderNameLabel = localization.GetByLabel('UI/Market/Marketbase/TypeNewFolderName')
            ret = uiutil.NamePopup(folderNameLabel, typeNewFolderNameLabel, maxLength=20)
            if ret is None:
                return self.folders[folderID].label
            name = ret
        self.folders[folderID].label = name
        sm.ScatterEvent('OnMarketQuickbarChange')
        return name

    def NewFolder(self, folderID = 0, node = None, *args):
        folderNameLabel = localization.GetByLabel('UI/Market/Marketbase/FolderName')
        typeFolderNameLabel = localization.GetByLabel('UI/Market/Marketbase/TypeFolderName')
        ret = uiutil.NamePopup(folderNameLabel, typeFolderNameLabel, maxLength=20)
        if ret is not None:
            self.lastid += 1
            n = util.KeyVal()
            n.parent = folderID
            n.id = self.lastid
            n.label = ret
            self.folders[n.id] = n
            settings.user.ui.Set('quickbar', self.folders)
            settings.user.ui.Set('quickbar_lastid', self.lastid)
            sm.ScatterEvent('OnMarketQuickbarChange')
            return n

    def GroupDeleteFolder(self, id):
        import types
        noteID = id[1]
        notes = self.GetItems(noteID)
        for id, note in notes.items():
            if type(note.label) == types.UnicodeType:
                self.GroupDeleteFolder((0, id))
                continue
            self.DeleteFolderNote(id)

        self.DeleteFolderNote(noteID)
        sm.ScatterEvent('OnMarketQuickbarChange')

    def DeleteFolderNote(self, noteID):
        del self.folders[noteID]

    def GroupDropNode(self, id, nodes):
        """
        Mouse event triggered when an item is dropped on a group or
        list item in the quickbar
        """
        for node in nodes:
            if getattr(node, 'id', None) and id[1] in self.folders:
                parent = self.folders[id[1]].parent
                shouldContinue = False
                while parent:
                    if node.id[1] == parent or node.id[1] == id[1]:
                        shouldContinue = True
                        break
                    parent = self.folders[parent].parent

                if shouldContinue:
                    continue
            if node.__guid__ in ('listentry.FittingEntry',):
                self.AddFittingFolder(node, id[1])
                continue
            shouldContinue = False
            for folderID, data in self.folders.items():
                if data.label == node.typeID and data.parent == id[1]:
                    shouldContinue = True
                    break

            if shouldContinue:
                continue
            if node.__guid__ in ('listentry.QuickbarItem', 'listentry.QuickbarGroup'):
                noteID = node.id[1]
                if uicore.uilib.Key(uiconst.VK_CONTROL):
                    self.AddTypeToQuickBar(node.typeID, parent=id[1])
                elif noteID in self.folders and noteID != id[1]:
                    self.folders[noteID].parent = id[1]
            elif node.__guid__ == 'listentry.GenericMarketItem':
                self.AddTypeToQuickBar(node.typeID, parent=id[1])
            elif node.__guid__ in ('xtriui.ShipUIModule', 'xtriui.InvItem', 'listentry.InvItem', 'listentry.InvAssetItem'):
                self.AddTypeToQuickBar(node.rec.typeID, parent=id[1])

        sm.ScatterEvent('OnMarketQuickbarChange')

    def OnScrollDrop(self, dropObj, nodes):
        if self.sr.sbTabs.GetSelectedArgs() != 'quickbar':
            return
        self.OnQuickbarScrollDrop(dropObj, nodes)

    def OnQuickbarScrollDrop(self, dropObj, nodes):
        """
        Mouse event triggered when an item is dropped on the 
        empty part of the quickbar scroll or the tab itself
        """
        for node in nodes:
            if node.__guid__ == 'listentry.GenericMarketItem':
                self.AddTypeToQuickBar(node.typeID)
            elif node.__guid__ in ('xtriui.ShipUIModule', 'xtriui.InvItem', 'listentry.InvItem', 'listentry.InvAssetItem'):
                self.AddTypeToQuickBar(node.rec.typeID)
            elif node.__guid__ in ('listentry.QuickbarItem', 'listentry.QuickbarGroup'):
                self.folders[node.id[1]].parent = 0
                sm.ScatterEvent('OnMarketQuickbarChange')
            elif node.__guid__ == 'listentry.FittingEntry':
                self.AddFittingFolder(node)

    def AddFittingFolder(self, node, parent = 0):
        self.lastid += 1
        fittingGroup = util.KeyVal()
        fittingGroup.parent = parent
        fittingGroup.id = self.lastid
        fittingGroup.label = node.label
        self.folders[fittingGroup.id] = fittingGroup
        settings.user.ui.Set('quickbar', self.folders)
        settings.user.ui.Set('quickbar_lastid', self.lastid)
        rackTypes = sm.GetService('fittingSvc').GetTypesByRack(node.fitting)
        rackNames = {'hiSlots': const.effectHiPower,
         'medSlots': const.effectMedPower,
         'lowSlots': const.effectLoPower,
         'rigSlots': const.effectRigSlot,
         'subSystems': const.effectSubSystem}
        for rack, contents in rackTypes.iteritems():
            if len(contents):
                name = None
                if rack == 'drones':
                    name = localization.GetByLabel('UI/Drones/Drones')
                elif rack == 'charges':
                    name = localization.GetByLabel('UI/Generic/Charges')
                elif rack in rackNames:
                    name = cfg.dgmeffects.Get(rackNames[rack]).displayName
                self.lastid += 1
                n = util.KeyVal()
                n.parent = fittingGroup.id
                n.id = self.lastid
                n.label = name
                self.folders[n.id] = n
                for typeID in contents:
                    self.AddTypeToQuickBar(typeID, parent=n.id)

                settings.user.ui.Set('quickbar', self.folders)
                settings.user.ui.Set('quickbar_lastid', self.lastid)

        self.AddTypeToQuickBar(node.fitting.shipTypeID, parent=fittingGroup.id)
        sm.ScatterEvent('OnMarketQuickbarChange')

    def ShouldShowType(self, typeID):
        """
            This function check if a type is supposed to be displayed based on the
            filters the player has on in the settings page. This does not filter out
            what should be displayed based on whether the "show only available" is on or off,
            that is done somewhere else
            
            use:  shouldShow = ShouldShowType(typeID)
            pre:  typeID is a valid typeID
            post: shouldShow is True if the type passes through all the filtering criteria
                  shouldShow is if this type should be filtered out
        """
        filterSkills = settings.user.ui.Get('showonlyskillsfor', 0)
        filterCpuPower = settings.user.ui.Get('showhavecpuandpower', 0)
        filterKnownSkills = settings.user.ui.Get('shownewskills', 0)
        doesMeetReq = True
        if filterSkills or filterCpuPower or filterKnownSkills:
            currShip = sm.StartService('godma').GetItem(eve.session.shipid)
            invtype = cfg.invtypes.Get(typeID)
            doesMeetReq, hasSkills, hasPower, hasCpu, hasSkill = self.MeetsRequirements(invtype, ship=currShip, reqTypeSkills=filterSkills, reqTypeCpuPower=filterCpuPower, hasSkill=filterKnownSkills)
        return doesMeetReq

    def FilterItemsForBrowse(self, marketGroupInfo):
        """
            This function returns the list of typeID that are to be displayed in the browse
            list (for the group you have the marketGroupInfo on)
            
            It filters out the items that are not supposed to be displayed due to the filters
            the player has on.
             
            use:  typeIDs = FilterItemsForBrowse(marketGroupInfo)
            pre:  marketGroupInfo is information on the current groups, where marketGroupInfo.type
                  contains the types that are in the group and all its subgroups
            post: typeIDs is a list of the typeIDs from that group that are supposed to be displayed
                  in the browse list
        """
        filterNone = settings.user.ui.Get('showonlyavailable', 0)
        ret = []
        for typeID in marketGroupInfo.types:
            ask = self.asksForMyRange.get(typeID, None)
            if (not filterNone or ask) and self.ShouldShowType(typeID):
                ret.append(typeID)

        return ret

    def FilterItemsForGroupPage(self, marketGroupInfo):
        """
            This function returns a list of KeyVals that contain the info on the types that 
            should be displayed on the group page  (for the group the group you have the marketGroupInfo on)
                        
            It filters out the items that are not supposed to be displayed due to the filters
            the player has on.
             
            use:  items = FilterItemsForBrowse(marketGroupInfo)
            pre:  marketGroupInfo is information on the current group, where marketGroupInfo.type
                  contains the types that are in the group and all its subgroups
            post: items is a list of KeyValse with the information on the orders that have the best 
                  prices for each of the types (that are not filtered out) in that groups
        """
        filterNone = settings.user.ui.Get('showonlyavailable', 0)
        marketSvc = sm.StartService('marketQuote')
        ret = []
        for typeID in marketGroupInfo.types:
            data = None
            ask = self.asksForMyRange.get(typeID, None)
            if ask is None and filterNone:
                continue
            shouldShow = self.ShouldShowType(typeID)
            if not shouldShow:
                continue
            data = util.KeyVal()
            data.typeID = typeID
            data.price = getattr(ask, 'price', 0)
            data.qty = getattr(ask, 'volRemaining', 0)
            data.fmt_price = util.FmtISK(data.price) if data.price else localization.GetByLabel('UI/Market/Marketbase/NoneAvailable')
            data.fmt_qty = util.FmtAmt(data.qty) if data.qty else '0'
            data.jumps = marketSvc.GetStationDistance(ask.stationID, False) if ask else None
            ret.append(data)

        return ret

    def MeetsRequirements(self, invType, ship = None, reqTypeSkills = 0, reqTypeCpuPower = 0, hasSkill = 0):
        haveReqSkill = True
        haveReqPower = True
        haveReqCpu = True
        haveSkillAlready = True
        typeID = invType.typeID
        if hasSkill:
            isSkill = invType.categoryID == const.categorySkill
            if isSkill:
                if self.mine.get(typeID, None) is not None:
                    haveSkillAlready = False
        if reqTypeSkills:
            requiredSkills = sm.GetService('clientDogmaStaticSvc').GetRequiredSkills(typeID)
            if requiredSkills:
                for skillID, level in requiredSkills.iteritems():
                    if skillID not in self.mine or self.mine[skillID] < level:
                        haveReqSkill = False
                        break

            else:
                haveReqSkill = True
        if reqTypeCpuPower:
            havePower = 0
            haveCpu = 0
            isHardware = invType.Group().Category().IsHardware()
            if isHardware:
                powerEffect = None
                powerIdx = None
                powerEffects = [const.effectHiPower, const.effectMedPower, const.effectLoPower]
                for effect in cfg.dgmtypeeffects.get(typeID, []):
                    if effect.effectID in powerEffects:
                        powerEffect = cfg.dgmeffects.Get(effect.effectID)
                        powerIdx = powerEffects.index(effect.effectID)
                        break

                powerLoad = 0
                cpuLoad = 0
                shipID = util.GetActiveShip()
                if shipID is not None and powerIdx is not None:
                    dgmAttr = sm.GetService('godma').GetType(typeID)
                    for attribute in dgmAttr.displayAttributes:
                        if attribute.attributeID in (const.attributeCpuLoad, const.attributeCpu):
                            cpuLoad += attribute.value
                        elif attribute.attributeID in (const.attributePowerLoad, const.attributePower):
                            powerLoad += attribute.value

                    dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
                    havePower = dogmaLocation.GetAttributeValue(shipID, const.attributePowerOutput) > powerLoad
                    haveCpu = dogmaLocation.GetAttributeValue(shipID, const.attributeCpuOutput) > cpuLoad
                if powerEffect:
                    haveReqPower = havePower
                    haveReqCpu = haveCpu
        meetsReq = haveReqSkill and haveReqPower and haveReqCpu and haveSkillAlready
        return (meetsReq,
         haveReqSkill,
         haveReqPower,
         haveReqCpu,
         haveSkillAlready)

    def OnChange_minEdit_market_filter_price(self, value, *args):
        newValue = self.ConvertInput(value, 2)
        settings.user.ui.Set('minEdit_market_filter_price', newValue)

    def OnChange_maxEdit_market_filter_price(self, value, *args):
        newValue = self.ConvertInput(value, 2)
        settings.user.ui.Set('maxEdit_market_filter_price', newValue)

    def OnChange_minEdit_market_filter_jump(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('minEdit_market_filter_jumps', newValue)

    def OnChange_maxEdit_market_filter_jumps(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('maxEdit_market_filter_jumps', newValue)

    def OnChange_minEdit_market_filter_quantity(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('minEdit_market_filter_quantity', newValue)

    def OnChange_maxEdit_market_filter_quantity(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('maxEdit_market_filter_quantity', newValue)

    def OnChange_minEdit_market_filters_sellorderdev(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('minEdit_market_filters_sellorderdev', newValue)

    def OnChange_maxEdit_market_filters_sellorderdev(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('maxEdit_market_filters_sellorderdev', newValue)

    def OnChange_minEdit_market_filters_buyorderdev(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('minEdit_market_filters_buyorderdev', newValue)

    def OnChange_maxEdit_market_filters_buyorderdev(self, value, *args):
        newValue = self.ConvertInput(value)
        settings.user.ui.Set('maxEdit_market_filters_buyorderdev', newValue)

    def ConvertInput(self, value, numDecimals = None):
        """
            Check if input is empty and change the value to be a number
        """
        if not value:
            value = 0
        value = self.ConvertToPoint(value, numDecimals)
        return value

    def FiltersInUse1(self):
        filterUsed = False
        browseFilters = [(localization.GetByLabel('UI/Market/ShowOnlyAvailable'), 'showonlyavailable'),
         (localization.GetByLabel('UI/Market/Marketbase/FilterBySkills'), 'showonlyskillsfor'),
         (localization.GetByLabel('UI/Market/Marketbase/FilterByCPUAndPowergrid'), 'showhavecpuandpower'),
         (localization.GetByLabel('UI/Market/Marketbase/FilterByUntrainedSkills'), 'shownewskills')]
        retBrowse = ''
        for label, filter in browseFilters:
            if settings.user.ui.Get('%s' % filter, 0):
                filterUsed = True
                temp = '%s<br>' % label
                retBrowse += temp

        if retBrowse == '' and not settings.user.ui.Get('showonlyavailable', 0):
            temp = '%s<br>' % localization.GetByLabel('UI/Common/Show all')
            retBrowse += temp
        if retBrowse:
            retBrowse = '%s<br>%s' % (localization.GetByLabel('UI/Market/Marketbase/BrowseFilters'), retBrowse)
            retBrowse = retBrowse[:-1]
        return (retBrowse, filterUsed)

    def FiltersInUse2(self, *args):
        ret = ''
        jumpFilter = [(localization.GetByLabel('UI/Market/Marketbase/Jumps'), 'market_filter_jumps')]
        detailFilters = [(localization.GetByLabel('UI/Common/Quantity'), 'market_filter_quantity'),
         (localization.GetByLabel('UI/Market/Marketbase/Price'), 'market_filter_price'),
         (localization.GetByLabel('UI/Market/Marketbase/SellOrdersDeviation'), 'market_filters_sellorderdev'),
         (localization.GetByLabel('UI/Market/Marketbase/BuyOrdersDeviation'), 'market_filters_buyorderdev')]
        secFilters = [(localization.GetByLabel('UI/Market/Marketbase/NoHighSecurity'), 'market_filter_highsec'), (localization.GetByLabel('UI/Market/Marketbase/NoLowSecurity'), 'market_filter_lowsec'), (localization.GetByLabel('UI/Market/Marketbase/NoZeroSecurity'), 'market_filter_zerosec')]
        retJump = ''
        for label, filter in jumpFilter:
            if settings.user.ui.Get('%s' % filter, 0):
                min = float(settings.user.ui.Get('minEdit_%s' % filter, 0))
                max = float(settings.user.ui.Get('maxEdit_%s' % filter, 0))
                andUp = False
                if min > max:
                    andUp = True
                    temp = '%s<br>' % localization.GetByLabel('UI/Market/Marketbase/FilterRangeAndUp', filterType=label, minValue=min)
                else:
                    temp = '%s<br>' % localization.GetByLabel('UI/Market/Marketbase/FilterRangeTo', filterType=label, minValue=min, maxValue=max)
                retJump += temp

        retDetail = retJump
        for label, filter in detailFilters:
            if settings.user.ui.Get('%s' % filter, 0):
                min = float(settings.user.ui.Get('minEdit_%s' % filter, 0))
                max = float(settings.user.ui.Get('maxEdit_%s' % filter, 0))
                andUp = False
                if min >= max:
                    andUp = filter not in ('market_filters_sellorderdev', 'market_filters_buyorderdev')
                    if andUp:
                        temp = '%s<br>' % localization.GetByLabel('UI/Market/Marketbase/FilterRangeAndUp', filterType=label, minValue=min)
                if not andUp:
                    temp = '%s<br>' % localization.GetByLabel('UI/Market/Marketbase/FilterRangeTo', filterType=label, minValue=min, maxValue=max)
                retDetail += temp

        if retDetail:
            retDetail = '%s<br>%s' % (localization.GetByLabel('UI/Market/Marketbase/DetailFilters'), retDetail)
        retSecurity = ''
        for label, filter in secFilters:
            if not settings.user.ui.Get('%s' % filter, 0):
                temp = '%s<br>' % label
                retSecurity += temp

        if retSecurity:
            retSecurity = '%s<br>%s' % (localization.GetByLabel('UI/Market/Marketbase/SecurityFilters'), retSecurity)
        for each in [retDetail, retSecurity]:
            if each:
                ret += '%s<br>' % each

        if ret:
            ret = ret[:-1]
        return ret

    def CheckboxRange(self, boxes, container):
        for height, label, configname, retval, checked, groupname, numRange, hint, isFloat in boxes:
            box = uiprimitives.Container(name='checkbox_%s' % configname, parent=container, align=uiconst.TOTOP, padBottom=const.defaultPadding)
            rbox = uiprimitives.Container(name='checkbox_%s' % configname, parent=box, align=uiconst.TORIGHT, width=180)
            cb = uicontrols.Checkbox(text='%s' % label, parent=box, configName=configname, retval=retval, checked=checked, groupname=groupname, callback=self.OnCheckboxChangeSett, align=uiconst.TOPLEFT, height=height, width=150)
            if numRange:
                funcKey = '%s_min' % configname
                fromLabel = localization.GetByLabel('UI/Common/FromNumber')
                minText = uicontrols.EveLabelMedium(text=fromLabel, parent=rbox, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL)
                if not isFloat:
                    minEdit = uicontrols.SinglelineEdit(name='minEdit_%s' % configname, setvalue=settings.user.ui.Get('minEdit_%s' % configname, 0), parent=rbox, left=minText.left + minText.textwidth + const.defaultPadding, top=0, align=uiconst.CENTERLEFT, ints=[numRange[0], numRange[1]], OnChange=self.OnChangeFuncs[funcKey])
                    minEdit.AutoFitToText(util.FmtAmt(sys.maxint))
                else:
                    minEdit = uicontrols.SinglelineEdit(name='minEdit_%s' % configname, setvalue=settings.user.ui.Get('minEdit_%s' % configname, 0), parent=rbox, left=minText.left + minText.textwidth + const.defaultPadding, top=0, align=uiconst.CENTERLEFT, floats=[numRange[0], numRange[1], 2], OnChange=self.OnChangeFuncs[funcKey])
                    minEdit.AutoFitToText(util.FmtAmt(float(MAXVALUE), showFraction=2))
                funcKey = '%s_max' % configname
                maxText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Common/ToNumber'), parent=rbox, left=minEdit.left + minEdit.width + const.defaultPadding, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL)
                if not isFloat:
                    maxEdit = uicontrols.SinglelineEdit(name='maxEdit_%s' % configname, setvalue=settings.user.ui.Get('maxEdit_%s' % configname, 0), parent=rbox, left=maxText.left + maxText.textwidth + const.defaultPadding, top=0, align=uiconst.CENTERLEFT, ints=[numRange[0], numRange[1]], OnChange=self.OnChangeFuncs[funcKey])
                    maxEdit.AutoFitToText(util.FmtAmt(sys.maxint))
                else:
                    maxEdit = uicontrols.SinglelineEdit(name='maxEdit_%s' % configname, setvalue=settings.user.ui.Get('maxEdit_%s' % configname, 0), parent=rbox, left=maxText.left + maxText.textwidth + const.defaultPadding, top=0, align=uiconst.CENTERLEFT, floats=[numRange[0], numRange[1], 2], OnChange=self.OnChangeFuncs[funcKey])
                    maxEdit.AutoFitToText(util.FmtAmt(float(MAXVALUE), showFraction=2))
                rbox.width = maxEdit.left + maxEdit.width + const.defaultPadding
                box.height = rbox.height = max(cb.height, minEdit.height, minText.height, maxEdit.height, maxText.height)
            if hint:
                cb.hint = hint

    def SetupFilters(self):
        settings.user.ui.Set('showonlyavailable', settings.user.ui.Get('showonlyavailable', True))
        settings.user.ui.Set('showonlyskillsfor', settings.user.ui.Get('showonlyskillsfor', False))
        settings.user.ui.Set('showhavecpuandpower', settings.user.ui.Get('showhavecpuandpower', False))
        settings.user.ui.Set('shownewskills', settings.user.ui.Get('shownewskills', False))
        settings.user.ui.Set('market_filter_price', settings.user.ui.Get('market_filter_price', False))
        settings.user.ui.Set('minEdit_market_filter_price', settings.user.ui.Get('minEdit_market_filter_price', 0))
        settings.user.ui.Set('maxEdit_market_filter_price', settings.user.ui.Get('maxEdit_market_filter_price', 100000))
        settings.user.ui.Set('market_filter_jumps', settings.user.ui.Get('market_filter_jumps', False))
        settings.user.ui.Set('minEdit_market_filter_jumps', settings.user.ui.Get('minEdit_market_filter_jumps', 0))
        settings.user.ui.Set('maxEdit_market_filter_jumps', settings.user.ui.Get('maxEdit_market_filter_jumps', 20))
        settings.user.ui.Set('market_filter_quantity', settings.user.ui.Get('market_filter_quantity', False))
        settings.user.ui.Set('minEdit_market_filter_quantity', settings.user.ui.Get('minEdit_market_filter_quantity', 0))
        settings.user.ui.Set('maxEdit_market_filter_quantity', settings.user.ui.Get('maxEdit_market_filter_quantity', 1000))
        settings.user.ui.Set('market_filter_zerosec', settings.user.ui.Get('market_filter_zerosec', True))
        settings.user.ui.Set('market_filter_lowsec', settings.user.ui.Get('market_filter_lowsec', True))
        settings.user.ui.Set('market_filter_highsec', settings.user.ui.Get('market_filter_highsec', True))
        settings.user.ui.Set('market_filters_sellorderdev', settings.user.ui.Get('market_filters_sellorderdev', False))
        settings.user.ui.Set('minEdit_market_filters_sellorderdev', settings.user.ui.Get('minEdit_market_filters_sellorderdev', 0))
        settings.user.ui.Set('maxEdit_market_filters_sellorderdev', settings.user.ui.Get('maxEdit_market_filters_sellorderdev', 0))
        settings.user.ui.Set('market_filters_buyorderdev', settings.user.ui.Get('market_filters_buyorderdev', False))
        settings.user.ui.Set('minEdit_market_filters_buyorderdev', settings.user.ui.Get('minEdit_market_filters_buyorderdev', 0))
        settings.user.ui.Set('maxEdit_market_filters_buyorderdev', settings.user.ui.Get('maxEdit_market_filters_buyorderdev', 0))
        settings.user.ui.Set('quickbar', settings.user.ui.Get('quickbar', {}))
        settings.user.ui.Set('autorefresh', settings.user.ui.Get('autorefresh', True))

    def AddGroupParent(self, nodedata = None, newitems = 0):
        """ Adding a group to the quickbar. Nothing is displayed here,
        only set up and checked if adding the folder will make
        the quickbar too deep"""
        marketGroupID = None
        self.parentDictionary = {}
        if nodedata:
            marketGroupID = nodedata.marketGroupInfo.marketGroupID
        firstID = self.InsertQuickbarGroupItem(nodedata.marketGroupInfo.marketGroupName, 0)
        self.parentDictionary[marketGroupID] = self.tempLastid
        scrolllist = self.AddGroupChildren(nodedata=nodedata)
        self.test = QuickbarEntries()
        depth = self.test.Load(contentList=scrolllist, maxDepth=5, parentDepth=nodedata.sublevel)
        self.test.Close()
        return (depth, firstID)

    def AddGroupChildren(self, nodedata = None):
        """ Adding the group's children to the quickbar list (not displaying them yet)"""
        scrolllist = []
        if nodedata and nodedata.marketGroupInfo.hasTypes:
            parent = self.parentDictionary.get(nodedata.marketGroupInfo.marketGroupID, 0)
            for typeID in nodedata.typeIDs:
                self.InsertQuickbarGroupItem(typeID, parent)

        else:
            marketGroupID = None
            level = 0
            if nodedata:
                marketGroupID = nodedata.marketGroupInfo.marketGroupID
                level = nodedata.sublevel + 1
            grouplist = sm.GetService('marketutils').GetMarketGroups()[marketGroupID]
            for marketGroupInfo in grouplist:
                if not len(marketGroupInfo.types):
                    continue
                if self.destroyed:
                    return
                items = [ typeID for typeID in marketGroupInfo.types ]
                groupID = (marketGroupInfo.marketGroupName, marketGroupInfo.marketGroupID)
                data = {'GetSubContent': self.AddGroupChildren,
                 'id': groupID,
                 'typeIDs': items,
                 'marketGroupInfo': marketGroupInfo,
                 'sublevel': level}
                parent = self.parentDictionary.get(marketGroupInfo.parentGroupID, 0)
                self.InsertQuickbarGroupItem(marketGroupInfo.marketGroupName, parent)
                self.parentDictionary[marketGroupInfo.marketGroupID] = self.tempLastid
                scrolllist.append(((marketGroupInfo.hasTypes, marketGroupInfo.marketGroupName.lower()), listentry.Get('QuickbarGroup', data)))

        return scrolllist

    def InsertQuickbarGroupItem(self, label, parent, extraText = ''):
        self.tempLastid += 1
        n = util.KeyVal()
        n.parent = parent
        n.id = self.tempLastid
        n.label = label
        n.extraText = extraText
        self.tempFolders[n.id] = n
        return n.id

    def ListWnd(self, lst, listtype = None, caption = None, hint = None, ordered = 0, minw = 200, minh = 256, minChoices = 1, maxChoices = 1, initChoices = [], validator = None, isModal = 1, scrollHeaders = [], iconMargin = 0, contentList = None):
        """ This is pretty much the same as uix.ListWnd, but I needed access to the scroll and didn't want
        to mess with the other one """
        if caption is None:
            caption = localization.GetByLabel('UI/Market/Marketbase/SelectAFolder')
        import form
        if not isModal:
            SelectFolderWindow.CloseIfOpen()
        wnd = SelectFolderWindow.Open(lst=[], listtype=listtype, ordered=ordered, minw=minw, minh=minh, caption=caption, minChoices=minChoices, maxChoices=maxChoices, initChoices=initChoices, validator=validator, scrollHeaders=scrollHeaders, iconMargin=iconMargin)
        wnd.scroll.Load(contentList=contentList)
        wnd.Error(wnd.GetError(checkNumber=0))
        if hint:
            wnd.SetHint('<center>' + hint)
        if isModal:
            wnd.DefineButtons(uiconst.OKCANCEL)
            if wnd.ShowModal() == uiconst.ID_OK:
                return wnd.result
            else:
                return
        else:
            wnd.DefineButtons(uiconst.CLOSE)
            wnd.Maximize()

    def ConvertToPoint(self, value, numDigits = 0):
        ret = uiutil.ConvertDecimal(value, ',', '.', numDigits)
        if numDigits is not None:
            ret = '%.*f' % (numDigits, float(ret))
        return ret

    def StoreTypeInHistory(self, typeID):
        if len(self.historyData) > 0:
            newHistory = self.historyData[:self.historyIdx + 1]
            lastTypeID = newHistory[min(self.historyIdx, len(self.historyData) - 1)]
            if lastTypeID != typeID:
                newHistory.append(typeID)
                self.historyIdx += 1
                self.historyData = newHistory
        else:
            self.historyData.append(typeID)
            self.historyIdx = 0
        self.ChangeBackAndForwardButtons()

    def GoBack(self, *args):
        if len(self.historyData) > 1 and self.historyIdx > 0:
            self.historyIdx = max(0, self.historyIdx - 1)
            typeID = self.historyData[min(self.historyIdx, len(self.historyData) - 1)]
            marketWnd = RegionalMarket.GetIfOpen()
            if marketWnd:
                marketWnd.LoadTypeID_Ext(typeID)

    def GoForward(self, *args):
        if self.historyIdx is None:
            return
        if len(self.historyData) > self.historyIdx + 1:
            self.historyIdx = max(0, self.historyIdx + 1)
            typeID = self.historyData[min(self.historyIdx, len(self.historyData) - 1)]
            marketWnd = RegionalMarket.GetIfOpen()
            if marketWnd:
                marketWnd.LoadTypeID_Ext(typeID)

    def ChangeBackAndForwardButtons(self):
        if self.historyIdx == 0:
            self.DisableArrow(self.goBackBtn)
        else:
            self.EnableArrow(self.goBackBtn)
        if self.historyIdx >= len(self.historyData) - 1:
            self.DisableArrow(self.goForwardBtn)
        else:
            self.EnableArrow(self.goForwardBtn)

    def DisableArrow(self, btn):
        btn.opacity = 0.25
        btn.Disable()

    def EnableArrow(self, btn):
        btn.opacity = 1.0
        btn.Enable()

    def AdjustRightButtonCont(self, *args):
        if self.sr.reloadBtn.state == uiconst.UI_HIDDEN or self.sr.reloadBtn.display == False:
            self.rightButtonCont.width = 50
        else:
            self.rightButtonCont.width = self.sr.reloadBtn.width + 28


class MarketGroupEntry(ContainerAutoSize):
    default_name = 'MarketGroupEntry'
    default_align = uiconst.TOTOP
    PADDING_GENERIC = const.defaultPadding * 2

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        data = attributes.data
        invType = data.invType
        self.topCont = Container(name='topCont', parent=self, align=uiconst.TOTOP, height=74)
        typeImage = uicls.MarketGroupItemImage(parent=self.topCont, align=uiconst.TOPLEFT, width=64, height=64, top=self.PADDING_GENERIC, left=self.PADDING_GENERIC, state=uiconst.UI_NORMAL)
        typeImage.attrs = data.typeImageAttributes
        typeImage.typeName = invType.name
        typeImage.LoadTypeIcon(invType.typeID)
        typeNameLabel = uicontrols.EveCaptionMedium(parent=self.topCont, align=uiconst.TOPLEFT, left=typeImage.left + typeImage.width + self.PADDING_GENERIC, top=self.PADDING_GENERIC, text=invType.name, name='typeNameLabel')
        uicontrols.InfoIcon(parent=self.topCont, align=uiconst.TOPLEFT, size=16, typeID=invType.typeID, left=typeNameLabel.left + typeNameLabel.width + const.defaultPadding, top=typeNameLabel.top + (typeNameLabel.height - 16) / 2)
        RequirementsContainer(parent=self.topCont, align=uiconst.TOPLEFT, top=typeNameLabel.top + typeNameLabel.height + const.defaultPadding, left=typeNameLabel.left, width=200, typeID=invType.typeID)
        combinedDescription = data.bestPrice + '<br><fontsize=16><b>' + data.marketData.fmt_price + '</b></fontsize>'
        if data.unitsAvailable:
            combinedDescription += '<br>' + data.unitsAvailable
        if HasTraits(data.invType.typeID):
            TraitsContainer(parent=self, typeID=data.invType.typeID, align=uiconst.TOTOP, padding=(self.PADDING_GENERIC,
             4,
             self.PADDING_GENERIC,
             self.PADDING_GENERIC))
        else:
            combinedDescription = data.description + '<br><br>' + combinedDescription
        uicontrols.Label(parent=self, align=uiconst.TOTOP, padding=(self.PADDING_GENERIC,
         4,
         self.PADDING_GENERIC,
         0), state=uiconst.UI_NORMAL, name='descriptionLabel', text=combinedDescription)
        self.buttonCont = Container(name='buttonCont', parent=self, align=uiconst.TOTOP, height=18, padTop=4)
        viewDetailsButton = uicontrols.Button(parent=self.buttonCont, align=uiconst.TORIGHT, label=localization.GetByLabel('UI/Market/Marketbase/CommandViewDetails'), func=sm.GetService('marketutils').ShowMarketDetails, args=(invType.typeID, None), padLeft=4, hint=localization.GetByLabel('Tooltips/Market/MarketGroupsViewDetails'))
        buyLabel = localization.GetByLabel('UI/Market/MarketQuote/CommandBuy') if data.marketData.qty else localization.GetByLabel('UI/Market/Marketbase/CommandPlaceBuyOrder')
        buyHint = localization.GetByLabel('Tooltips/Market/MarketGroupsBuyButton') if data.marketData.qty else localization.GetByLabel('Tooltips/Market/MarketGroupsPlaceBuy')
        uicontrols.Button(parent=self.buttonCont, align=uiconst.TORIGHT, label=buyLabel, func=sm.GetService('marketutils').Buy, args=(invType.typeID, None), padLeft=4, hint=buyHint)
        if industryCommon.IsBlueprintCategory(invType.categoryID):
            from eve.client.script.ui.shared.industry.industryWnd import Industry
            uicontrols.Button(parent=self.buttonCont, align=uiconst.TORIGHT, label=localization.GetByLabel('UI/Industry/ViewInIndustry'), func=Industry.OpenOrShowBlueprint, args=(None, invType.typeID), padLeft=4)
        LineUnderlay(parent=self, align=uiconst.TOTOP, padTop=4)


MINSCROLLHEIGHT = 64
LEFTSIDEWIDTH = 90
LABELWIDTH = 110

class MarketData(uiprimitives.Container):
    __guid__ = 'form.MarketData'
    __notifyevents__ = ['OnPathfinderSettingsChange', 'OnSessionChanged']

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.name = 'marketQuote'
        self.caption = 'Market Data'
        self.prefs = 'marketquote'
        self.invType = None
        self.loading = None
        self.scrollHeight = 0
        self.allMyOrderIDs = set()
        self.buyheaders = [localization.GetByLabel('UI/Market/Marketbase/Jumps'),
         localization.GetByLabel('UI/Common/Quantity'),
         localization.GetByLabel('UI/Market/Marketbase/Price'),
         localization.GetByLabel('UI/Common/Location'),
         localization.GetByLabel('UI/Market/Marketbase/ExpiresIn')]
        self.sellheaders = [localization.GetByLabel('UI/Market/Marketbase/Jumps'),
         localization.GetByLabel('UI/Common/Quantity'),
         localization.GetByLabel('UI/Market/Marketbase/Price'),
         localization.GetByLabel('UI/Common/Location'),
         localization.GetByLabel('UI/Common/Range'),
         localization.GetByLabel('UI/Market/MarketQuote/HeaderMinVolumn'),
         localization.GetByLabel('UI/Market/Marketbase/ExpiresIn')]
        self.avgSellPrice = None
        self.avgBuyPrice = None
        self.sr.buyParent = uiprimitives.Container(name='buyParent', parent=self, align=uiconst.TOTOP, height=64)
        buyLeft = uiprimitives.Container(name='buyLeft', parent=self.sr.buyParent, align=uiconst.TOTOP, height=20)
        sellersLabel = localization.GetByLabel('UI/Market/Marketbase/Sellers')
        cap = uicontrols.EveCaptionMedium(text=sellersLabel, parent=buyLeft, align=uiconst.TOPLEFT, left=4)
        buyLeft.height = max(buyLeft.height, cap.textheight)
        a = uicontrols.EveLabelSmall(text='', parent=buyLeft, left=24, top=0, state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        a.OnClick = self.BuyClick
        a.GetMenu = None
        self.buyFiltersActive1 = a
        a = uicontrols.EveLabelSmall(text='', parent=buyLeft, left=24, top=14, state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        a.OnClick = self.BuyClick
        a.GetMenu = None
        self.buyFiltersActive2 = a
        self.sr.buyIcon = uiprimitives.Sprite(name='buyIcon', parent=buyLeft, width=16, height=16, left=6, top=0, align=uiconst.TOPRIGHT)
        self.sr.buyIcon.OnClick = self.BuyClick
        self.sr.buyIcon.state = uiconst.UI_HIDDEN
        btns = [(localization.GetByLabel('UI/Market/Marketbase/ExportToFile'),
          self.ExportToFile,
          (),
          84,
          False,
          False,
          False,
          localization.GetByLabel('Tooltips/Market/MarketDetailsExportFile')), (localization.GetByLabel('UI/Market/Marketbase/CommandPlaceBuyOrder'),
          self.PlaceOrder,
          ('buy',),
          84,
          False,
          False,
          False,
          localization.GetByLabel('Tooltips/Market/MarketDetailsPlaceBuyOrder'))]
        grp = uicontrols.ButtonGroup(btns=btns, parent=self, unisize=1)
        from eve.client.script.ui.control.divider import Divider
        divider = Divider(name='divider', align=uiconst.TOTOP, height=const.defaultPadding, parent=self, state=uiconst.UI_NORMAL)
        divider.Startup(self.sr.buyParent, 'height', 'y', 64, self.scrollHeight)
        divider.OnSizeChanged = self.OnDetailScrollSizeChanged
        self.sr.divider = divider
        uiprimitives.Line(parent=divider, align=uiconst.TOTOP, opacity=0.05)
        self.sr.buyscroll = uicontrols.Scroll(name='buyscroll', parent=self.sr.buyParent, padding=const.defaultPadding)
        self.sr.buyscroll.multiSelect = 0
        self.sr.buyscroll.smartSort = 1
        self.sr.buyscroll.ignoreHeaderWidths = 1
        self.sr.buyscroll.sr.id = '%sBuyScroll' % self.prefs
        self.sr.buyscroll.OnColumnChanged = self.OnBuyColumnChanged
        uiprimitives.Container(name='divider', align=uiconst.TOTOP, height=const.defaultPadding, parent=self)
        self.sr.sellParent = uiprimitives.Container(name='sellParent', parent=self, align=uiconst.TOALL)
        sellLeft = uiprimitives.Container(name='sellLeft', parent=self.sr.sellParent, align=uiconst.TOTOP, height=20)
        buyersLabel = localization.GetByLabel('UI/Market/Marketbase/Buyers')
        cap = uicontrols.EveCaptionMedium(text=buyersLabel, parent=sellLeft, align=uiconst.TOPLEFT, left=4)
        sellLeft.height = max(sellLeft.height, cap.textheight)
        a = uicontrols.EveLabelSmall(text='', parent=sellLeft, left=24, top=0, align=uiconst.TOPRIGHT, state=uiconst.UI_NORMAL)
        a.OnClick = self.SellClick
        a.GetMenu = None
        self.sellFiltersActive1 = a
        a = uicontrols.EveLabelSmall(text='', parent=sellLeft, left=24, top=14, state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        a.OnClick = self.SellClick
        a.GetMenu = None
        self.sellFiltersActive2 = a
        self.sr.sellIcon = uiprimitives.Sprite(name='sellIcon', parent=sellLeft, width=16, height=16, left=6, top=0, align=uiconst.TOPRIGHT)
        self.sr.sellIcon.OnClick = self.SellClick
        self.sr.sellIcon.state = uiconst.UI_HIDDEN
        self.sr.sellscroll = uicontrols.Scroll(name='sellscroll', parent=self.sr.sellParent, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.sellscroll.multiSelect = 0
        self.sr.sellscroll.smartSort = 1
        self.sr.sellscroll.ignoreHeaderWidths = 1
        self.sr.sellscroll.sr.id = '%sSellScroll' % self.prefs
        self.sr.sellscroll.OnColumnChanged = self.OnSellColumnChanged
        self._OnResize()
        sm.RegisterNotify(self)
        self.inited = 1
        self.sr.buy_ActiveFilters = 1
        self.sr.sell_ActiveFilters = 1

    def OnDetailScrollSizeChanged(self):
        h = self.sr.buyParent.height
        absHeight = self.absoluteBottom - self.absoluteTop
        if h > absHeight - self.height - 64:
            h = absHeight - self.height - 64
            ratio = float(h) / absHeight
            settings.user.ui.Set('detailScrollHeight', ratio)
            self._OnResize()
            return
        ratio = float(h) / absHeight
        settings.user.ui.Set('detailScrollHeight', ratio)

    def SellClick(self, *args):
        self.sr.sell_ActiveFilters = not self.sr.sell_ActiveFilters
        self.Reload('sell')

    def BuyClick(self, *args):
        self.sr.buy_ActiveFilters = not self.sr.buy_ActiveFilters
        self.Reload('buy')

    def ExportToFile(self, *args):
        if not self.invType:
            return
        sm.GetService('marketQuote').DumpOrdersForType(self.invType.typeID)

    def OnPathfinderSettingsChange(self, *args):
        self.ReloadType()

    def OnSessionChanged(self, isremote, session, change):
        if 'solarsystemid' in change:
            self.ReloadType()

    def _OnResize(self, *args):
        if self and not self.destroyed and self.sr.buyParent:
            self.scrollHeight = self.absoluteBottom - self.absoluteTop - 34 - 64
            height = (self.absoluteBottom - self.absoluteTop - 46) / 2
            absHeight = self.absoluteBottom - self.absoluteTop
            ratio = settings.user.ui.Get('detailScrollHeight', 0.5)
            h = int(ratio * absHeight)
            if h > self.scrollHeight:
                h = self.scrollHeight
            self.sr.buyParent.height = max(64, h)
            self.sr.divider.max = self.scrollHeight

    def OnBuyColumnChanged(self, tabstops):
        if self.loading != 'buy':
            self.Reload('buy')

    def OnSellColumnChanged(self, tabstops):
        if self.loading != 'sell':
            self.Reload('sell')

    def PlaceOrder(self, what, *args):
        if not self.invType:
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Market/Marketbase/NoTypeToBuy')})
            return
        if what == 'buy':
            sm.GetService('marketutils').Buy(self.invType.typeID, placeOrder=True)
        elif what == 'sell':
            uicore.cmd.OpenAssets()

    def Reload(self, what):
        records = self.sr.Get('%sItems' % what, None)
        scrollList = []
        scroll = self.sr.Get('%sscroll' % what, None)
        self.loading = what
        headers = [self.buyheaders, self.sellheaders][what == 'sell']
        marketUtil = sm.GetService('marketutils')
        funcs = marketUtil.GetFuncMaps()

        def IsOrderASellWithinReach(order):
            return what == 'sell' and (order.jumps <= order.range or eve.session.stationid and order.range == -1 and order.stationID == eve.session.stationid or eve.session.solarsystemid and order.jumps == 0)

        usingFilters = self.GetFilters2()[0]
        foundCounter = 0
        destPathList = sm.GetService('starmap').GetDestinationPath()
        if self.invType and records:
            dataList = []
            scroll.sr.headers = headers
            visibleHeaders = scroll.GetColumns()
            accumPrice = 0
            count = 0
            for order in records[0]:
                data = util.KeyVal()
                data.label = ''
                data.typeID = order.typeID
                data.order = order
                data.mode = what
                data.inMyPath = order.solarSystemID in destPathList
                accumPrice += order.price * order.volRemaining
                count += order.volRemaining
                data.flag = IsOrderASellWithinReach(order)
                data.markAsMine = order.orderID in self.allMyOrderIDs
                expires = order.issueDate + order.duration * DAY - blue.os.GetWallclockTime()
                if expires < 0:
                    continue
                for header in visibleHeaders:
                    header = uiutil.StripTags(header, stripOnly=['localized'])
                    funcName = funcs.get(header, None)
                    if funcName and hasattr(marketUtil, funcName):
                        apply(getattr(marketUtil, funcName, None), (order, data))
                    else:
                        log.LogWarn('Unsupported header in record', header, order)
                        data.label += '###<t>'

                self.SetDataValues(order, data)
                data.label = data.label[:-3]
                dataList.append(data)

            avg = None
            if count > 0:
                avg = round(float(accumPrice / count), 2)
            if what == 'sell':
                self.avgSellPrice = avg
            else:
                self.avgBuyPrice = avg
            for data in dataList:
                if self.ApplyDetailFilters(data, self.sr.Get('%s_ActiveFilters' % what, None)):
                    scrollList.append(listentry.Get('MarketOrder', data=data))
                else:
                    foundCounter += 1

        hintText = ''
        if not scrollList:
            if self.invType:
                if (usingFilters or settings.user.ui.Get('market_filters_%sorderdev' % ['buy', 'sell'][what == 'buy'], 0)) and self.sr.Get('%s_ActiveFilters' % what, None):
                    hintText = localization.GetByLabel('UI/Market/Marketbase/NoOrdersMatched')
                else:
                    hintText = localization.GetByLabel('UI/Market/Orders/NoOrdersFound')
            else:
                hintText = localization.GetByLabel('UI/Market/Marketbase/NoTypeToBuy')
                self.sr.filtersText.text = ''
                self.sr.filtersText.hint = ''
        scroll.Load(contentList=scrollList, headers=headers, noContentHint=hintText)
        if what == 'buy':
            if usingFilters or settings.user.ui.Get('market_filters_sellorderdev', 0):
                if self.sr.buy_ActiveFilters:
                    text1 = localization.GetByLabel('UI/Market/Marketbase/AdditionalEntriesFound', foundCounter=foundCounter)
                    text2 = localization.GetByLabel('UI/Market/Marketbase/TurnFiltersOff')
                else:
                    text1 = localization.GetByLabel('UI/Market/Marketbase/TurnFiltersOn')
                    text2 = ''
                self.buyFiltersActive1.text = text1
                self.buyFiltersActive2.text = text2
                self.sr.buyIcon.state = uiconst.UI_NORMAL
                self.SetFilterIcon2(self.sr.buyIcon, on=bool(self.sr.buy_ActiveFilters))
            else:
                self.buyFiltersActive1.text = ''
                self.buyFiltersActive2.text = ''
                self.sr.buyIcon.state = uiconst.UI_HIDDEN
        if what == 'sell':
            if usingFilters or settings.user.ui.Get('market_filters_buyorderdev', 0):
                if self.sr.sell_ActiveFilters:
                    text1 = localization.GetByLabel('UI/Market/Marketbase/AdditionalEntriesFound', foundCounter=foundCounter)
                    text2 = localization.GetByLabel('UI/Market/Marketbase/TurnFiltersOff')
                else:
                    text1 = localization.GetByLabel('UI/Market/Marketbase/TurnFiltersOn')
                    text2 = ''
                self.sellFiltersActive1.text = text1
                self.sellFiltersActive2.text = text2
                self.sr.sellIcon.state = uiconst.UI_NORMAL
                self.SetFilterIcon2(self.sr.sellIcon, on=bool(self.sr.sell_ActiveFilters))
            else:
                self.sellFiltersActive1.text = ''
                self.sellFiltersActive2.text = ''
                self.sr.sellIcon.state = uiconst.UI_HIDDEN
        self.loading = None

    def SetFilterIcon2(self, icon, on, *args):
        if on:
            iconNo = 'ui_38_16_205'
        else:
            iconNo = 'ui_38_16_204'
        icon.LoadIcon(iconNo)

    def SetDataValues(self, record, data):
        data.Set('filter_Price', record.price)
        filterJumps = record.jumps
        if record.jumps == 0:
            filterJumps = -1
        data.Set('filter_Jumps', filterJumps)
        data.Set('filter_Quantity', int(record.volRemaining))

    def GetFilters2(self):
        self.filter_jumps_min = int(settings.user.ui.Get('minEdit_market_filter_jumps', 0))
        self.filter_jumps_max = int(settings.user.ui.Get('maxEdit_market_filter_jumps', 0))
        if self.filter_jumps_min == None or self.filter_jumps_min == '':
            self.filter_jumps_min = 0
        if self.filter_jumps_max == None or self.filter_jumps_max == '':
            self.filter_jumps_max = INFINITY
        if self.filter_jumps_min > self.filter_jumps_max:
            self.filter_jumps_max = INFINITY
        self.filter_quantity_min = int(settings.user.ui.Get('minEdit_market_filter_quantity', 0))
        self.filter_quantity_max = int(settings.user.ui.Get('maxEdit_market_filter_quantity', 0))
        if self.filter_quantity_min == None or self.filter_quantity_min == '':
            self.filter_quantity_min = 0
        if self.filter_quantity_max == None or self.filter_quantity_max == '':
            self.filter_quantity_max = INFINITY
        if self.filter_quantity_min >= self.filter_quantity_max:
            self.filter_quantity_max = INFINITY
        self.filter_price_min = float(settings.user.ui.Get('minEdit_market_filter_price', 0))
        self.filter_price_max = float(settings.user.ui.Get('maxEdit_market_filter_price', 0))
        if self.filter_price_min == None or self.filter_price_min == '':
            self.filter_price_min = 0
        if self.filter_price_max == None or self.filter_price_max == '':
            self.filter_price_max = INFINITY
        if self.filter_price_min >= self.filter_price_max:
            self.filter_price_max = INFINITY
        self.ignore_sellorder_min = settings.user.ui.Get('minEdit_market_filters_sellorderdev', 0)
        if self.ignore_sellorder_min == None or self.ignore_sellorder_min == '':
            self.ignore_sellorder_min = 0
        self.ignore_sellorder_max = settings.user.ui.Get('maxEdit_market_filters_sellorderdev', 0)
        if self.ignore_sellorder_max == None or self.ignore_sellorder_max == '':
            self.ignore_sellorder_max = 0
        self.ignore_buyorder_min = settings.user.ui.Get('minEdit_market_filters_buyorderdev', 0)
        if self.ignore_buyorder_min == None or self.ignore_buyorder_min == '':
            self.ignore_buyorder_min = 0
        self.ignore_buyorder_max = settings.user.ui.Get('maxEdit_market_filters_buyorderdev', 0)
        if self.ignore_buyorder_max == None or self.ignore_buyorder_max == '':
            self.ignore_buyorder_max = 0
        filters = [settings.user.ui.Get('market_filter_jumps', 0),
         settings.user.ui.Get('market_filter_quantity', 0),
         settings.user.ui.Get('market_filter_price', 0),
         not settings.user.ui.Get('market_filter_zerosec', 0),
         not settings.user.ui.Get('market_filter_highsec', 0),
         not settings.user.ui.Get('market_filter_lowsec', 0)]
        usingFilters = False
        for each in filters:
            if each:
                usingFilters = True
                break

        return [usingFilters,
         self.filter_jumps_min,
         self.filter_jumps_max,
         self.filter_quantity_min,
         self.filter_quantity_max,
         self.filter_price_min,
         self.filter_price_max,
         self.ignore_sellorder_min,
         self.ignore_sellorder_max,
         self.ignore_buyorder_min,
         self.ignore_buyorder_max]

    def ApplyDetailFilters(self, data, activeFilters = 1):
        if not activeFilters:
            return True
        if settings.user.ui.Get('market_filter_jumps', 0):
            if data.filter_Jumps:
                if self.filter_jumps_min > data.filter_Jumps or self.filter_jumps_max < data.filter_Jumps:
                    if not (self.filter_jumps_min == 0 and data.filter_Jumps == -1):
                        return False
        if settings.user.ui.Get('market_filter_quantity', 0):
            if data.filter_Quantity:
                if self.filter_quantity_min > data.filter_Quantity or self.filter_quantity_max < data.filter_Quantity:
                    return False
        if settings.user.ui.Get('market_filter_price', 0):
            if data.filter_Price:
                if self.filter_price_min > data.filter_Price or self.filter_price_max < data.filter_Price:
                    return False
        secClass = sm.StartService('map').GetSecurityClass(data.order.solarSystemID)
        if secClass == const.securityClassZeroSec:
            if not settings.user.ui.Get('market_filter_zerosec', 0):
                return False
        elif secClass == const.securityClassHighSec:
            if not settings.user.ui.Get('market_filter_highsec', 0):
                return False
        elif not settings.user.ui.Get('market_filter_lowsec', 0):
            return False
        if data.filter_Price:
            if settings.user.ui.Get('market_filters_sellorderdev', 0) and data.mode == 'buy':
                if self.avgBuyPrice:
                    percentage = (data.filter_Price - self.avgBuyPrice) / self.avgBuyPrice
                    if float(self.ignore_sellorder_max) < percentage * 100 or float(self.ignore_sellorder_min) > percentage * 100:
                        return False
            if settings.user.ui.Get('market_filters_buyorderdev', 0) and data.mode == 'sell':
                if self.avgSellPrice:
                    percentage = (data.filter_Price - self.avgSellPrice) / self.avgSellPrice
                    if float(self.ignore_buyorder_max) < percentage * 100 or float(self.ignore_buyorder_min) > percentage * 100:
                        return False
        return True

    def LoadType(self, invType):
        self.invType = invType
        self.ReloadType()

    def OnReload(self):
        self.ReloadType()

    def ReloadType(self, *args):
        if self.invType:
            self.sr.sellscroll.Load(contentList=[], fixedEntryHeight=18, headers=self.sellheaders)
            self.sr.buyscroll.Load(contentList=[], fixedEntryHeight=18, headers=self.buyheaders)
            self.sr.sellscroll.ShowHint(localization.GetByLabel('UI/Market/Marketbase/FetchingOrders'))
            self.sr.buyscroll.ShowHint(localization.GetByLabel('UI/Market/Marketbase/FetchingOrders'))
            self.sr.buyItems, self.sr.sellItems = sm.GetService('marketQuote').GetOrders(self.invType.typeID)
            if settings.user.ui.Get('hilitemyorders', False):
                self.allMyOrderIDs = {order.orderID for order in sm.GetService('marketQuote').GetMyOrders()}
            else:
                self.allMyOrderIDs = set()
            self.Reload('buy')
            self.Reload('sell')
        else:
            self.sr.sellscroll.Load(contentList=[], fixedEntryHeight=18)
            self.sr.buyscroll.Load(contentList=[], fixedEntryHeight=18)


class MarketOrder(listentry.Generic):
    __guid__ = 'listentry.MarketOrder'

    def Startup(self, *args):
        listentry.Generic.Startup(self, args)
        self.sr.green = None

    def Load(self, node):
        listentry.Generic.Load(self, node)
        data = self.sr.node
        if data.inMyPath:
            self.sr.label.color = util.Color.YELLOW
        if data.markAsMine:
            self.ShowBackground(color=util.Color.BLUE)
        elif data.flag == 1 and data.mode == 'sell':
            self.ShowBackground(color=(0.0, 1.0, 0.0))
        elif self.sr.green:
            self.sr.bgFill.state = uiconst.UI_HIDDEN

    def ShowBackground(self, color, *args):
        if self.sr.bgFill is None:
            self.sr.bgFill = uiprimitives.Fill(bgParent=self, color=(1.0, 1.0, 1.0, 0.25), state=uiconst.UI_DISABLED)
        self.sr.bgFill.color.SetRGB(a=0.25, *color[:3])
        self.sr.bgFill.state = uiconst.UI_DISABLED

    def Buy(self, node = None, ignoreAdvanced = False, *args):
        if not hasattr(self, 'sr'):
            return
        node = node if node != None else self.sr.node
        sm.GetService('marketutils').Buy(self.sr.node.order.typeID, node.order, 0, ignoreAdvanced=ignoreAdvanced)

    def ShowInfo(self, node = None, *args):
        node = node if node != None else self.sr.node
        sm.GetService('info').ShowInfo(node.order.typeID)

    def GetMenu(self):
        self.OnClick()
        m = []
        if self.sr.node.mode == 'buy':
            m.append((uiutil.MenuLabel('UI/Market/Marketbase/BuyThis'), self.Buy, (self.sr.node, True)))
        m.append(None)
        m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (self.sr.node,))]
        stationID = self.sr.node.order.stationID
        if stationID:
            stationInfo = sm.GetService('ui').GetStation(stationID)
            m += [(uiutil.MenuLabel('UI/Common/Location'), sm.GetService('menu').CelestialMenu(stationID, typeID=stationInfo.stationTypeID, parentID=stationInfo.solarSystemID, mapItem=None))]
        if self.sr.node.markAsMine:
            m.append((uiutil.MenuLabel('UI/Market/Orders/ModifyOrder'), self.ModifyPrice, (self.sr.node,)))
            m.append((uiutil.MenuLabel('UI/Market/Orders/CancelOrder'), self.CancelOffer, (self.sr.node,)))
        return m

    def OnDblClick(self, *args):
        self.Buy(ignoreAdvanced=True)

    def ModifyPrice(self, node):
        sm.GetService('marketutils').ModifyOrder(node.order)

    def CancelOffer(self, node):
        sm.GetService('marketutils').CancelOffer(node.order)


class GenericMarketItem(listentry.Generic):
    __guid__ = 'listentry.GenericMarketItem'
    isDragObject = True

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        if not node.get('inRange', True):
            self.SetOpacity(0.5)
            self.hint = localization.GetByLabel('UI/Market/Marketbase/NotAvailableInRange')

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes


class QuickbarItem(GenericMarketItem):
    __guid__ = 'listentry.QuickbarItem'

    def Load(self, node):
        GenericMarketItem.Load(self, node)
        self.sr.sublevel = node.Get('sublevel', 0)
        self.sr.label.left = 12 + max(0, self.sr.sublevel * 16)
        if node.get('extraText', ''):
            self.sr.label.text = localization.GetByLabel('UI/Market/Marketbase/QuickbarTypeNameWithExtraText', typeName=node.label, extraText=node.get('extraText', ''))
        else:
            self.sr.label.text = node.label
        if node.invtype.marketGroupID is None:
            self.SetOpacity(0.5)
            if self.hint is not None:
                self.hint += '<br>'
            else:
                self.hint = ''
            self.hint += localization.GetByLabel('UI/Market/Marketbase/NotAvailableOnMarket')

    def OnClick(self, *args):
        if self.sr.node:
            if self.sr.node.invtype.marketGroupID is None:
                return
            self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def GetMenu(self):
        m = []
        if self.sr.node and self.sr.node.Get('GetMenu', None):
            m += self.sr.node.GetMenu(self)
        if getattr(self, 'itemID', None) or getattr(self, 'typeID', None):
            m += sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(self, 'itemID', None), getattr(self, 'typeID', None), ignoreMarketDetails=0)
        return m

    def GetDragData(self, *args):
        nodes = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        return nodes

    def OnDropData(self, dragObj, nodes):
        if self.sr.node.get('DropData', None):
            self.sr.node.DropData(('quickbar', self.sr.node.parent), nodes)


class QuickbarGroup(Group):
    __guid__ = 'listentry.QuickbarGroup'
    isDragObject = True

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes


class QuickbarEntries(uiprimitives.Container):
    """ This class is stolen from virtualscroll.py - class Scroll.
    Used to step through tree (folder structure) to check its depth.
    When using a scroll, the full tree is not traversed until it's loaded so 
    the depth is not known, which is needed for the quickbar.
    This doesn't display anything
    """
    __guid__ = 'xtriui.QuickbarEntries'
    __nonpersistvars__ = []

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.sr.nodes = []
        self.tooDeep = False

    def __Load(self, contentList = [], maxDepth = 99, parentDepth = 0):
        if self.destroyed:
            return
        self.sr.nodes = []
        self.maxDepth = maxDepth
        self.parentDepth = parentDepth
        self.depth = 0
        self.AddEntries(0, contentList)
        if self.destroyed:
            return
        return [0, self.depth - parentDepth][bool(self.depth)]

    Load = LoadContent = __Load

    def AddEntry(self, idx, entry, update = 0, isSub = 0, fromW = None):
        _idx = idx
        if idx == -1:
            idx = len(self.GetNodes())
        entry.idx = idx
        if not self or not getattr(self, 'sr', None):
            return
        self.ReloadEntry(entry)
        return entry

    def ReloadEntry(self, entry):
        if entry.id and entry.GetSubContent:
            self.depth = max(self.depth, entry.sublevel)
            subcontent = entry.GetSubContent(entry)
            if self.destroyed:
                return
            self.AddEntries(entry.idx + 1, subcontent, entry)

    def AddEntries(self, fromIdx, entriesData, parentEntry = None):
        if self.parentDepth > self.maxDepth:
            self.tooDeep = True
            return
        if fromIdx == -1:
            fromIdx = len(self.GetNodes())
        isSub = 0
        if parentEntry:
            isSub = getattr(parentEntry, 'sublevel', 0) + 1
        entries = []
        idx = fromIdx
        for crap, data in entriesData:
            newentry = self.AddEntry(idx, data, isSub=isSub)
            if newentry is None:
                continue
            idx = newentry.idx + 1
            entries.append(newentry)

        if self.destroyed:
            return

    def _OnClose(self):
        for each in self.GetNodes():
            each.scroll = None
            each.data = None

        self.sr.nodes = []

    def GetNodes(self):
        return self.sr.nodes


class SelectFolderWindow(ListWindow):
    """ A modified ListWindow. The data structure being used differs from the data
    structure listwindow expects and it would be more hassle to adjust it than just
    make a subclass"""
    default_windowID = 'SelectFolderWindow'

    def GetError(self, checkNumber = 1):
        result = None
        if self.scroll.GetSelected():
            result = [self.scroll.GetSelected()[0].id[1], self.scroll.GetSelected()[0].sublevel]
        if hasattr(self, 'customValidator'):
            ret = self.customValidator and self.customValidator(result) or ''
            if ret:
                return ret
        try:
            if checkNumber:
                if result == None:
                    if self.minChoices == self.maxChoices:
                        label = localization.GetByLabel('UI/Control/ListWindow/MustSelectError', num=self.minChoices)
                    else:
                        label = localization.GetByLabel('UI/Control/ListWindow/SelectTooFewError', num=self.minChoices)
                    return label
        except ValueError as e:
            log.LogException()
            sys.exc_clear()
            return

        return ''

    def Confirm(self, *etc):
        if not self.isModal:
            return
        self.Error(self.GetError(checkNumber=0))
        if not self.GetError():
            if self.scroll.GetSelected():
                if hasattr(self.scroll.GetSelected()[0], 'id'):
                    self.result = [self.scroll.GetSelected()[0].id[1], self.scroll.GetSelected()[0].sublevel]
            self.SetModalResult(uiconst.ID_OK)

    def Error(self, error):
        ep = uiutil.GetChild(self, 'errorParent')
        uix.Flush(ep)
        if error:
            t = uicontrols.EveLabelMedium(text='<center>' + error, top=-3, parent=ep, width=self.minsize[0] - 32, state=uiconst.UI_DISABLED, color=(1.0, 0.0, 0.0, 1.0), align=uiconst.CENTER)
            ep.state = uiconst.UI_DISABLED
            ep.height = t.height + 8
        else:
            ep.state = uiconst.UI_HIDDEN


class MarketGroupItemImage(Image):
    __guid__ = 'uicls.MarketGroupItemImage'
    isDragObject = True

    def LoadTypeIcon(self, typeID):
        uicls.Image.LoadTypeIcon(self)
        self.typeID = typeID
        if util.IsPreviewable(self.typeID):
            self.OnClick = (sm.GetService('preview').PreviewType, self.typeID)
        else:
            self.OnClick = None

    def GetDragData(self, *args):
        invType = cfg.invtypes.Get(self.typeID)
        return [uiutil.Bunch(typeID=self.typeID, __guid__='listentry.GenericMarketItem', label=self.typeName, invtype=invType)]

    def OnMouseMove(self, *args):
        if self.IsBeingDragged():
            self.cursor = self.default_cursor
        uiprimitives.Container.OnMouseMove(self)

    def OnMouseEnter(self, *args):
        if util.IsPreviewable(self.typeID):
            self.cursor = uiconst.UICURSOR_MAGNIFIER
        else:
            self.cursor = self.default_cursor


class MarketMetaGroupEntry(Group):
    """
        I only created this to be able to hook into the OnClick event without overwriting it
        To be honest this should really be part of the core group entry behavior.
    """
    __guid__ = 'listentry.MarketMetaGroupEntry'

    def Load(self, node):
        Group.Load(self, node)
        self.OnToggle = node.OnToggle

    def OnClick(self, *args):
        Group.OnClick(self, *args)
        if self.OnToggle is not None:
            self.OnToggle()
