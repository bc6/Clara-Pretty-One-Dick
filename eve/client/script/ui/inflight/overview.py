#Embedded file name: eve/client/script/ui/inflight\overview.py
import _weakref
from carbonui.control.scrollentries import SE_BaseClassCore
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.util.various_unsorted import GetAttrs
from carbon.common.script.util.format import FmtDist
from eve.client.script.parklife.state import GetNPCGroups
from eve.client.script.ui.control.colorPanel import ColorPanel
from eve.client.script.ui.control.eveEditPlainText import EditPlainText
from eve.client.script.ui.control.eveIcon import DraggableIcon
from eve.client.script.ui.control.labelEditable import LabelEditable
from eve.client.script.ui.control.tabGroup import Tab
from eve.client.script.ui.control.themeColored import FillThemeColored
from eve.client.script.ui.inflight.actions import ActionPanel
from eve.client.script.ui.control.entries import Checkbox, Generic
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.shared.stateFlag import FlagIconWithState
import uicontrols
import uicls
import uiprimitives
import blue
import const
from carbonui.primitives.layoutGrid import LayoutGrid
from overviewPresets.overviewPresetUtil import MAX_TAB_NUM
import state
import uix
import uthread
import uiutil
import carbonui.const as uiconst
import localization
import eveLocalization
import fontConst
import telemetry
import geo2
import log
import sys
import trinity
import fleetbr
import bisect
import locks
import re
from collections import defaultdict
import stackless
from eve.client.script.ui.inflight.bracketsAndTargets.blinkingSpriteOnSharedCurve import BlinkingSpriteOnSharedCurve
from eve.client.script.ui.inflight.bracketsAndTargets.bracketVarious import GetIconColor
from eve.client.script.ui.inflight.overViewLabel import OverviewLabel, SortHeaders
from eve.client.script.ui.inflight.overviewConst import *
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from inventorycommon.util import IsNPC
from eveexceptions.exceptionEater import ExceptionEater
from eve.client.script.util.bubble import InBubble
from utillib import KeyVal
import util
import operator
from carbonui.control.dragResizeCont import DragResizeCont
ScrollListLock = locks.RLock()
FMTFUNCTION = localization.formatters.FormatNumeric

class OverView(ActionPanel):
    __guid__ = 'form.OverView'
    __notifyevents__ = ['OnDestinationSet',
     'OnOverviewTabChanged',
     'OnReloadingOverviewProfile',
     'OnEwarStart',
     'OnEwarEnd',
     'OnStateSetupChance',
     'OnSessionChanged',
     'OnFleetJoin_Local',
     'OnFleetLeave_Local',
     'OnPostCfgDataChanged',
     'OnTacticalPresetChange',
     'OnFleetStateChange',
     'OnStateChange',
     'DoBallsAdded',
     'DoBallRemove',
     'OnUIScalingChange',
     'OnSlimItemChange',
     'OnContactChange',
     'OnTutorialHighlightItem',
     'ProcessBountyInfoUpdated',
     'DoBallsRemove']
    default_pinned = True
    default_windowID = 'overview'
    default_height = 300
    default_open = True
    sortingFrozen = False

    @staticmethod
    def default_top(*args):
        topRight_TopOffset = uicontrols.Window.GetTopRight_TopOffset()
        if topRight_TopOffset is not None:
            return topRight_TopOffset
        return 16

    @staticmethod
    def default_left(*args):
        return uicore.desktop.width - OverView.default_width - 16

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        global FMT_M
        global FMT_AU
        global FMT_KM
        global FMT_VELOCITY
        self.overviewUpdateThread = None
        self._freezeOverview = False
        self._ballparkDirty = True
        self._scrollEntriesDirty = True
        self._scrollNodesByItemID = {}
        attributes.showActions = False
        ActionPanel.ApplyAttributes(self, attributes)
        self.cursor = uiconst.UICURSOR_HASMENU
        self.jammers = {}
        self.ewarTypes = sm.GetService('state').GetEwarTypes()
        self.ewarHintsByGraphicID = {}
        for jamType, (flag, graphicID) in self.ewarTypes:
            self.ewarHintsByGraphicID[graphicID] = sm.GetService('state').GetEwarHint(jamType)

        self.minUpdateSleep = int(sm.GetService('machoNet').GetGlobalConfig().get('overviewMinUpdateSleep', 500))
        self.maxUpdateSleep = int(sm.GetService('machoNet').GetGlobalConfig().get('overviewMaxUpdateSleep', 1000))
        self.prevMouseCoords = trinity.GetCursorPos()
        self.lastMovementTime = blue.os.GetWallclockTime()
        self.mouseMovementTimeout = int(sm.GetService('machoNet').GetGlobalConfig().get('overviewMouseMovementTimeout', 0))
        languageID = localization.util.GetLanguageID()
        FMT_M = eveLocalization.GetMessageByID(234383, languageID)
        FMT_KM = eveLocalization.GetMessageByID(234384, languageID)
        FMT_AU = eveLocalization.GetMessageByID(234385, languageID)
        FMT_VELOCITY = eveLocalization.GetMessageByID(239583, languageID)

    def Close(self):
        ActionPanel.Close(self)

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if ball is None:
            return
        itemID = slimItem.itemID
        node = self._scrollNodesByItemID.get(itemID, None)
        if node:
            node.leavingOverview = True
            if node.panel:
                node.panel.opacity = 0.25
                node.panel.state = uiconst.UI_DISABLED
            if node.itemID in self._scrollNodesByItemID:
                del self._scrollNodesByItemID[node.itemID]

    def DoBallsAdded(self, lst, *args, **kw):
        uthread.new(self._DoBallsAdded, lst, *args, **kw)

    @telemetry.ZONE_METHOD
    def _DoBallsAdded(self, lst, *args, **kw):
        tacticalSvc = sm.GetService('tactical')
        stateSvc = sm.GetService('state')
        fleetSvc = sm.GetService('fleet')
        CheckIfFilterItem = stateSvc.CheckIfFilterItem
        CheckFiltered = tacticalSvc.CheckFiltered
        CheckIfUpdateItem = stateSvc.CheckIfUpdateItem
        filterGroups = sm.GetService('overviewPresetSvc').GetValidGroups()
        filteredStates = tacticalSvc.GetFilteredStatesFunctionNames()
        alwaysShownStates = tacticalSvc.GetAlwaysShownStatesFunctionNames()
        columns = tacticalSvc.GetColumns()
        if self.sortHeaders.GetCurrentColumns() != columns:
            self.sortHeaders.CreateColumns(columns, fixedColumns=FIXEDCOLUMNS)
        now = blue.os.GetSimTime()
        with ScrollListLock:
            newEntries = []
            for ball, slimItem in lst:
                if slimItem.itemID in self._scrollNodesByItemID:
                    continue
                if slimItem.groupID in const.OVERVIEW_IGNORE_GROUPS:
                    continue
                if slimItem.groupID in filterGroups and slimItem.itemID != eve.session.shipid:
                    if CheckIfFilterItem(slimItem) and CheckFiltered(slimItem, filteredStates, alwaysShownStates):
                        continue
                    updateItem = CheckIfUpdateItem(slimItem)
                    data = {'itemID': slimItem.itemID,
                     'updateItem': updateItem}
                    newNode = listentry.Get('OverviewScrollEntry', data)
                    newNode.ball = _weakref.ref(ball)
                    newNode.slimItem = _weakref.ref(slimItem)
                    if updateItem:
                        newNode.ewarGraphicIDs = self.GetEwarDataForNode(newNode)
                    newNode.ewarHints = self.ewarHintsByGraphicID
                    newEntries.append(newNode)

            if newEntries:
                self.UpdateStaticDataForNodes(newEntries)
                self.UpdateDynamicDataForNodes(newEntries)
                currentActive, currentDirection = self.sortHeaders.GetCurrentActive()
                broadcastsToTop = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('overviewBroadcastsToTop', False)
                fleetBroadcasts = fleetSvc.GetCurrentFleetBroadcasts()

                def GetSortValue(_node):
                    if broadcastsToTop:
                        if _node.itemID in fleetBroadcasts:
                            return (1, _node.sortValue)
                        else:
                            return (2, _node.sortValue)
                    return _node.sortValue

                self.sr.scroll.ShowHint()
                if self.sortingFrozen:
                    newEntries.sort(key=lambda x: GetSortValue(x), reverse=not currentDirection)
                    self.sr.scroll.AddNodes(-1, newEntries)
                else:
                    sortValues = [ GetSortValue(x) for x in self.sr.scroll.sr.nodes ]
                    entriesAtIdx = defaultdict(list)
                    for entry in newEntries:
                        insertionIndex = bisect.bisect(sortValues, GetSortValue(entry))
                        entriesAtIdx[insertionIndex].append(entry)

                    insertionPoints = sorted(entriesAtIdx.keys(), reverse=True)
                    for insertionIdx in insertionPoints:
                        sortedGroup = sorted(entriesAtIdx[insertionIdx], key=GetSortValue, reverse=not currentDirection)
                        self.sr.scroll.AddNodes(insertionIdx, sortedGroup)

    def OnUIScalingChange(self, *args):
        self.FullReload()

    def OnStateChange(self, itemID, flag, newState, *args):
        node = self._scrollNodesByItemID.get(itemID, None)
        if node and node.panel:
            node.panel.OnStateChange(itemID, flag, newState, *args)

    def OnFleetStateChange(self, fleetState):
        if not fleetState:
            return
        for itemID, tag in fleetState.targetTags.iteritems():
            node = self._scrollNodesByItemID.get(itemID, None)
            if node is None:
                continue
            node.display_TAG = tag
            if node.sortTagIndex is not None:
                if tag:
                    node.sortValue[node.sortTagIndex] = tag.lower()
                else:
                    node.sortValue[node.sortTagIndex] = 0

    def OnSlimItemChange(self, oldSlim, newSlim):
        node = self._scrollNodesByItemID.get(oldSlim.itemID, None)
        if node:
            node.slimItem = _weakref.ref(newSlim)
            node.iconColor = None
            self.PrimeDisplayName(node)
            self.UpdateIconAndBackgroundFlagsOnNode(node)
            if node.panel:
                node.panel.UpdateIcon()

    def ProcessBountyInfoUpdated(self, itemIDs):
        for itemID in itemIDs:
            node = self._scrollNodesByItemID.get(itemID, None)
            if node is not None:
                self.UpdateIconAndBackgroundFlagsOnNode(node)

    def FlushEwarStates(self):
        if self.jammers:
            currentSourceIDs = self.jammers.keys()
            self.jammers = {}
            for sourceBallID in currentSourceIDs:
                self.UpdateEwarStateOnItemID(sourceBallID)

    def OnEwarStart(self, sourceBallID, moduleID, targetBallID, jammingType):
        if targetBallID != session.shipid:
            return
        if not jammingType:
            return
        if not hasattr(self, 'jammers'):
            self.jammers = {}
        jammingID = sm.StartService('state').GetEwarGraphicID(jammingType)
        if not self.jammers.has_key(sourceBallID):
            self.jammers[sourceBallID] = {}
        if not self.jammers[sourceBallID].has_key(jammingID):
            self.jammers[sourceBallID][jammingID] = {}
        self.jammers[sourceBallID][jammingID][moduleID] = True
        self.UpdateEwarStateOnItemID(sourceBallID)

    def OnEwarEnd(self, sourceBallID, moduleID, targetBallID, jammingType):
        if targetBallID != session.shipid:
            return
        if not jammingType:
            return
        if not hasattr(self, 'jammers'):
            return
        jammingID = sm.StartService('state').GetEwarGraphicID(jammingType)
        if not self.jammers.has_key(sourceBallID) or not self.jammers[sourceBallID].has_key(jammingID) or not self.jammers[sourceBallID][jammingID].has_key(moduleID):
            return
        del self.jammers[sourceBallID][jammingID][moduleID]
        if self.jammers[sourceBallID][jammingID] == {}:
            del self.jammers[sourceBallID][jammingID]
        self.UpdateEwarStateOnItemID(sourceBallID)

    def UpdateEwarStateOnItemID(self, itemID):
        node = self._scrollNodesByItemID.get(itemID, None)
        if node is None:
            return
        node.ewarGraphicIDs = self.GetEwarDataForNode(node)
        if node.panel:
            node.panel.UpdateEwar()

    def GetEwarDataForNode(self, node):
        if node.itemID not in self.jammers:
            return
        jammersOnItem = self.jammers.get(node.itemID, None)
        if not jammersOnItem:
            return
        ret = []
        for jamType, (flag, graphicID) in self.ewarTypes:
            if graphicID in jammersOnItem:
                ret.append(graphicID)

        return ret

    def OnTacticalPresetChange(self, label, preset):
        label = sm.GetService('overviewPresetSvc').GetPresetDisplayName(label)
        self.sr.presetMenu.hint = label
        self.SetCaption(localization.GetByLabel('UI/Tactical/OverviewCaption', preset=label))
        self.FlagScrollEntriesAndBallparkDirty_InstantUpdate('OnTacticalPresetChange')

    def OnPostCfgDataChanged(self, what, data):
        if what == 'evelocations':
            itemID = data[0]
            if itemID in self._scrollNodesByItemID:
                node = self._scrollNodesByItemID[itemID]
                self.PrimeDisplayName(node)

    def PrimeDisplayName(self, node):
        slimItem = node.slimItem()
        if not slimItem:
            return
        name = uix.GetSlimItemName(slimItem)
        if slimItem.groupID == const.groupStation:
            name = uix.EditStationName(name, usename=0)
        if node.usingLocalizationTooltips:
            name, hint = self.PrepareLocalizationTooltip(name)
            node.hint_NAME = hint
        node.display_NAME = self.Encode(name)
        if node.sortNameIndex is not None:
            node.sortValue[node.sortNameIndex] = name.lower()
        node.hint_NAME = sm.GetService('bracket').GetDisplayNameForBracket(slimItem)

    def Encode(self, text):
        return re.sub(HTML_ENTITIES, lambda match: HTML_ENTITY_REPLACEMENTS[match.group()], text)

    def PrepareLocalizationTooltip(self, text):
        """
        In order to utilize the optimized label in overview entries
        we extract the localization hint from the string and apply
        the hint directly on the label when the entry is loaded.
        """
        localizedTags = uicontrols.Label.ExtractLocalizedTags(text)
        if localizedTags:
            hint = localizedTags[0].get('hint', None)
            text = uiutil.StripTags(text)
        else:
            hint = None
        return (text, hint)

    def OnDestinationSet(self, *etc):
        for node in self.sr.scroll.sr.nodes:
            slimItem = node.slimItem()
            if not slimItem or slimItem.groupID not in (const.groupStargate, const.groupStation):
                continue
            node.iconColor = None

    def OnContactChange(self, contactIDs, contactType = None):
        self.FlagBallparkDirty()

    def OnFleetJoin_Local(self, member, *args):
        self.UpdateFleetMemberOrFlagDirty(member)
        self.FlagBallparkDirty()

    def OnFleetLeave_Local(self, member, *args):
        self.UpdateFleetMemberOrFlagDirty(member)
        self.FlagBallparkDirty()

    def UpdateFleetMemberOrFlagDirty(self, member):
        if member.charID == session.charid:
            self.FlagScrollEntriesDirty('UpdateFleetMemberOrFlagDirty')
        else:
            slimItem = self.GetSlimItemForCharID(member.charID)
            if slimItem and slimItem.itemID in self._scrollNodesByItemID:
                node = self._scrollNodesByItemID[slimItem.itemID]
                self.UpdateIconAndBackgroundFlagsOnNode(node)

    @telemetry.ZONE_METHOD
    def UpdateAllIconAndBackgroundFlags(self):
        for node in self.sr.scroll.sr.nodes:
            if node.updateItem:
                self.UpdateIconAndBackgroundFlagsOnNode(node)
            else:
                slimItem = node.slimItem()
                if slimItem is not None and slimItem.groupID in const.containerGroupIDs:
                    node.iconColor = None
                    if node.panel is not None:
                        node.panel.UpdateIconColor()

    @telemetry.ZONE_METHOD
    def UpdateIconAndBackgroundFlagsOnNode(self, node):
        slimItem = node.slimItem()
        if slimItem is None:
            return
        iconFlag, backgroundFlag = (0, 0)
        if node.updateItem:
            iconFlag, backgroundFlag = sm.GetService('state').GetIconAndBackgroundFlags(slimItem)
        node.iconAndBackgroundFlags = (iconFlag, backgroundFlag)
        if node.sortIconIndex is not None:
            iconFlag, backgroundFlag = node.iconAndBackgroundFlags
            node.iconColor, colorSortValue = GetIconColor(slimItem, getSortValue=True)
            node.sortValue[node.sortIconIndex] = [iconFlag,
             colorSortValue,
             backgroundFlag,
             slimItem.categoryID,
             slimItem.groupID,
             slimItem.typeID]
        if node.panel:
            node.panel.UpdateFlagAndBackground(slimItem)

    def OnReloadingOverviewProfile(self):
        self.FullReload()

    def OnOverviewTabChanged(self, tabsettings, oldtabsettings, deletingTab = False):
        if tabsettings is None:
            tabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
        newtabsettings = {}
        for key, setting in tabsettings.iteritems():
            newtabsettings[key] = setting

        sm.GetService('overviewPresetSvc').SetTabSettingsForOverview(newtabsettings)
        tabs = []
        if len(tabsettings.keys()) == 0:
            defaultPresetList = ['default']
            if not deletingTab:
                defaultPresetList.extend(['defaultmining', 'defaultwarpto'])
            defaultTabSetting = {}
            for i, defaultPreset in enumerate(defaultPresetList):
                tabName = sm.GetService('overviewPresetSvc').GetDefaultOverviewName(defaultPreset)
                defaultTabSetting[i] = {'overview': defaultPreset,
                 'bracket': None,
                 'name': tabName}
                tabs.append([tabName,
                 self.sr.scroll,
                 self,
                 (defaultPreset,
                  None,
                  tabName,
                  i),
                 self.sr.scroll])

            sm.GetService('overviewPresetSvc').SetTabSettingsForOverview(defaultTabSetting)
        else:
            for key in tabsettings.keys()[:MAX_TAB_NUM]:
                bracketSettings = tabsettings[key].get('bracket', None)
                overviewSettings = tabsettings[key].get('overview', None)
                tabName = tabsettings[key].get('name', None)
                tabs.append([tabsettings[key]['name'],
                 self.sr.scroll,
                 self,
                 (overviewSettings,
                  bracketSettings,
                  tabName,
                  key),
                 self.sr.scroll])

        if getattr(self, 'maintabs', None):
            self.maintabs.Close()
        self.maintabs = uicontrols.TabGroup(name='tabparent', align=uiconst.TOTOP, parent=self.sr.main, tabs=tabs, groupID='overviewTabs', idx=0)
        if len(tabs) < MAX_TAB_NUM:
            extraTab = Tab(parent=self.maintabs, labelPadding=10, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL)
            extraTab.Startup(self.maintabs, uiutil.Bunch(label='+'))
            extraTab.SetOrder(len(self.maintabs.children) - 1)
            extraTab.OnClick = self.AddTab
            extraTab.UpdateTabSize()
            extraTab.width = extraTab.sr.width
            extraTab.hint = localization.GetByLabel('UI/Overview/AddTab')
        sm.ScatterEvent('OnRefreshOverviewTab')

    def OnStateSetupChance(self, reason = None):
        """
        If any setting of the overview changes we need to flag all as dirty
        so the node will know what columns, in what order, what state flag etc...
        it needs to update.
        """
        self.FlagScrollEntriesDirty('OnStateSetupChance')

    def GetSlimItemForCharID(self, charID):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark:
            for rec in ballpark.slimItems.itervalues():
                if rec.charID == charID:
                    return rec

    def GetTabMenu(self, tab, *args):
        presets = sm.GetService('overviewPresetSvc').GetAllPresets()
        overviewm = []
        bracketm = []
        ret = []
        isSelected = tab.IsSelected()
        tabName = tab.sr.args[2]
        tabKey = tab.sr.args[3]
        bracketm.append(('', (localization.GetByLabel('UI/Overview/ShowAllBrackets'), self.ChangeBracketInTab, (None, isSelected, tabKey))))
        for key in presets:
            label = key
            if sm.GetService('overviewPresetSvc').IsTempName(key):
                continue
            else:
                presetName = sm.GetService('overviewPresetSvc').GetDefaultOverviewName(label)
                lowerLabel = label.lower()
                if presetName is not None:
                    bracketm.append((lowerLabel, (presetName, self.ChangeBracketInTab, (key, isSelected, tabKey))))
                else:
                    overviewm.append((lowerLabel, (label, self.ChangeOverviewInTab, (key, isSelected, tabKey))))
                    bracketm.append((lowerLabel, (label, self.ChangeBracketInTab, (key, isSelected, tabKey))))

        overviewm = [ x[1] for x in localization.util.Sort(overviewm, key=lambda x: x[0]) ]
        bracketm = [ x[1] for x in localization.util.Sort(bracketm, key=lambda x: x[0]) ]
        defaultm = []
        for name in sm.GetService('overviewPresetSvc').GetDefaultOverviewNameList():
            presetName = sm.GetService('overviewPresetSvc').GetDefaultOverviewName(name)
            if presetName is not None:
                defaultm.append((presetName, self.ChangeOverviewInTab, (name, isSelected, tabKey)))

        ret = []
        ret.append((localization.GetByLabel('/Carbon/UI/Controls/ScrollEntries/ChangeLabel'), self.ChangeTabName, (tabName, tabKey)))
        ret.append((uiutil.MenuLabel('UI/Tactical/SaveCurrentTypeSelectionAs'), sm.GetService('overviewPresetSvc').SavePreset))
        ret.append((localization.GetByLabel('UI/Overview/LoadOverviewProfile'), overviewm))
        ret.append((uiutil.MenuLabel('UI/Tactical/LoadDefault'), defaultm))
        ret.append((localization.GetByLabel('UI/Overview/LoadBracketProfile'), bracketm))
        ret.append((localization.GetByLabel('UI/Overview/DeleteTab'), self.DeleteTab, (tabKey, isSelected)))
        return ret

    def ChangeTabName(self, tabName, tabKey):
        ret = uiutil.NamePopup(localization.GetByLabel('/Carbon/UI/Controls/ScrollEntries/ChangeLabel'), localization.GetByLabel('UI/Overview/TypeInLabel'), tabName, maxLength=30)
        if not ret:
            return
        tabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
        newTabName = ret
        if tabsettings.has_key(tabKey):
            oldtabsettings = tabsettings
            tabsettings[tabKey]['name'] = newTabName
            self.OnOverviewTabChanged(tabsettings, oldtabsettings)
            sm.ScatterEvent('OnOverviewPresetSaved')

    def ChangeOverviewInTab(self, overviewLabel, isSelected, tabKey):
        tabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
        if tabsettings.has_key(tabKey):
            oldtabsettings = tabsettings
            tabsettings[tabKey]['overview'] = overviewLabel
            self.OnOverviewTabChanged(tabsettings, oldtabsettings)
            if isSelected:
                sm.GetService('overviewPresetSvc').LoadPreset(overviewLabel, False)

    def ChangeBracketInTab(self, bracketLabel, isSelected, tabKey):
        tabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
        if tabKey in tabsettings or tabKey is None:
            oldtabsettings = tabsettings
            tabsettings[tabKey]['bracket'] = bracketLabel
            self.OnOverviewTabChanged(tabsettings, oldtabsettings)
            if isSelected:
                sm.GetService('overviewPresetSvc').LoadBracketPreset(bracketLabel)

    def DeleteTab(self, tabKey, isSelected):
        oldtabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
        if not oldtabsettings.has_key(tabKey):
            return
        newtabsettings = {}
        i = 0
        for key, dictItem in oldtabsettings.iteritems():
            if key == tabKey:
                continue
            newtabsettings[i] = dictItem
            i += 1

        self.OnOverviewTabChanged(newtabsettings, oldtabsettings, deletingTab=True)

    def AddTab(self):
        ret = uiutil.NamePopup(localization.GetByLabel('UI/Overview/AddTab'), localization.GetByLabel('UI/Overview/TypeInLabel'), maxLength=15)
        if not ret:
            return
        tabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
        if len(tabsettings) >= MAX_TAB_NUM:
            eve.Message('TooManyTabs', {'numTabs': MAX_TAB_NUM})
            return
        if len(tabsettings) == 0:
            newKey = 0
        else:
            newKey = max(tabsettings.keys()) + 1
        oldtabsettings = tabsettings
        tabsettings[newKey] = {'name': ret,
         'overview': 'default',
         'bracket': None}
        if self.destroyed:
            return
        self.OnOverviewTabChanged(tabsettings, oldtabsettings)

    def PostStartup(self):
        self.SetHeaderIcon()
        hicon = self.sr.headerIcon
        hicon.GetMenu = self.GetPresetsMenu
        hicon.expandOnLeft = 1
        hicon.hint = localization.GetByLabel('UI/Overview/OverviewTypePresets')
        hicon.name = 'overviewHeaderIcon'
        self.sr.presetMenu = hicon
        main = self.GetMainArea()
        main.padding = 0
        scroll = uicontrols.BasicDynamicScroll(name='overviewscroll2', align=uiconst.TOALL, parent=main, multiSelect=False, padding=4, autoPurgeHiddenEntries=False)
        scroll.OnSelectionChange = self.OnScrollSelectionChange
        scroll.OnChar = self.OnChar
        scroll.OnKeyUp = self.OnKeyUp
        self.columnHilites = []
        sortHeaders = SortHeaders(parent=scroll.sr.maincontainer, settingsID='overviewScroll2', idx=0)
        sortHeaders.SetDefaultColumn(COLUMN_DISTANCE, True)
        sortHeaders.OnColumnSizeChange = self.OnColumnSizeChanged
        sortHeaders.OnSortingChange = self.OnSortingChange
        sortHeaders.OnColumnSizeReset = self.OnColumnSizeReset
        self.sortHeaders = sortHeaders
        self.sr.scroll = scroll
        self.OnOverviewTabChanged(None, {})

    def OnSetActive_(self, *args):
        selected = self.sr.scroll.GetSelected()
        if selected is None:
            self.sr.scroll.SetSelected(0)

    def OnKeyUp(self, *args):
        """
        Used by the command svc to execute combat commands for the selected scroll entry
        """
        selected = self.sr.scroll.GetSelected()
        if not selected:
            return
        uicore.cmd.ExecuteCombatCommand(selected[0].itemID, uiconst.UI_CLICK)

    def OnChar(self, *args):
        """
        This is here so we don't swallow the event in case of single char shortcuts
        """
        return False

    def LoadTabPanel(self, args, panel, tabgroup):
        tactical = sm.GetService('tactical')
        overviewPresetSvc = sm.GetService('overviewPresetSvc')
        if len(args) > 2:
            settingName = args[0]
            overviewPresetSvc.LoadPreset(settingName, False, notSavedPreset=isinstance(settingName, tuple))
            tabsettings = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview().get(args[3], {})
            showSpecials = tabsettings.get('showSpecials', False)
            if tabsettings.get('showAll', False):
                bracketShowState = 1
            elif tabsettings.get('showNone', False):
                bracketShowState = -1
            else:
                bracketShowState = 0
            overviewPresetSvc.LoadBracketPreset(args[1], showSpecials=showSpecials, bracketShowState=bracketShowState)

    def UpdateColumnHilite(self):
        currentActive, currentDirection = self.sortHeaders.GetCurrentActive()
        if currentActive:
            columnWidths = self.sortHeaders.GetCurrentSizes()
            currentColumns = self.sortHeaders.GetCurrentColumns()
            for each in self.columnHilites[:len(currentColumns)]:
                each.Close()
                self.columnHilites.remove(each)

            prevline = None
            left = 0
            for columnIndex, columnID in enumerate(currentColumns):
                if len(self.columnHilites) > columnIndex:
                    hilite = self.columnHilites[columnIndex]
                else:
                    hilite = FillThemeColored(parent=self.sr.scroll.sr.clipper, align=uiconst.TOLEFT_NOPUSH, opacity=uiconst.OPACITY_FRAME, width=1, colorType=uiconst.COLORTYPE_UIHILIGHT)
                    self.columnHilites.append(hilite)
                columnWidth = columnWidths[columnID]
                left += columnWidth
                hilite.left = left - 1
                prevline = hilite

        else:
            for each in self.columnHilites:
                each.Close()

            self.columnHilites = []

    def OnColumnSizeReset(self, columnID):
        useSmallText = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('useSmallText', False)
        if useSmallText:
            fontSize = fontConst.EVE_SMALL_FONTSIZE
        else:
            fontSize = fontConst.EVE_MEDIUM_FONTSIZE
        labelClass = OverviewLabel
        widths = [COLUMNMINSIZE - COLUMNMARGIN * 2]
        for node in self.sr.scroll.sr.nodes:
            displayValue = OverviewScrollEntry.GetColumnDisplayValue(node, columnID)
            if displayValue:
                textWidth, textHeight = labelClass.MeasureTextSize(displayValue, fontSize=fontSize)
                widths.append(textWidth)

        self.sortHeaders.SetColumnSize(columnID, max(widths) + COLUMNMARGIN * 2)
        self.TriggerInstantUpdate('OnColumnSizeReset')

    def OnColumnSizeChanged(self, columnID, headerWidth, currentSizes, *args):
        self.UpdateColumnHilite()
        self.TriggerInstantUpdate('OnColumnSizeChanged')

    def OnSortingChange(self, oldColumnID, columnID, oldSortDirection, sortDirection):
        if oldColumnID == columnID and oldSortDirection != sortDirection:
            self.TriggerInstantUpdate('OnSortingChange')
        else:
            self.FlagScrollEntriesDirty_InstantUpdate('OnSortingChange')

    def OnScrollSelectionChange(self, nodes, *args):
        """
        Triggered when set selection changes with in the scroll.
        Only thing we do is to delegate that message over to the stateSvc
        which will trigger OnStateChange for interested parties.
        """
        if not nodes:
            return
        node = nodes[0]
        if node and node.itemID:
            sm.GetService('state').SetState(node.itemID, state.selected, 1)
            if sm.GetService('target').IsTarget(node.itemID):
                sm.GetService('state').SetState(node.itemID, state.activeTarget, 1)

    def GetPresetsMenu(self):
        return sm.GetService('overviewPresetSvc').GetPresetsMenu()

    def Cleanup(self):
        pass

    @telemetry.ZONE_METHOD
    def UpdateAll(self, *args, **kwds):
        pass

    @telemetry.ZONE_METHOD
    def FullReload(self):
        self.StopOverviewUpdate()
        self.sr.scroll.Clear()
        self._scrollNodesByItemID = {}
        self.FlagScrollEntriesAndBallparkDirty_InstantUpdate()

    def StopOverviewUpdate(self):
        if self.overviewUpdateThread:
            self.overviewUpdateThread.kill()
            self.overviewUpdateThread = None

    def TriggerInstantUpdate(self, fromFunction = None):
        self.StopOverviewUpdate()
        if self.IsCollapsed() or self.IsMinimized():
            return
        self.UpdateOverview()

    def FlagBallparkDirty(self, fromFunction = None):
        self._ballparkDirty = True
        if self.IsCollapsed() or self.IsMinimized():
            self.StopOverviewUpdate()
            return
        if not self.overviewUpdateThread:
            self.overviewUpdateThread = uthread.new(self.UpdateOverview)

    def FlagScrollEntriesAndBallparkDirty_InstantUpdate(self, fromFunction = None):
        self._ballparkDirty = True
        self._scrollEntriesDirty = True
        self.TriggerInstantUpdate('FlagScrollEntriesDirtyDirty_InstantUpdate')

    def FlagScrollEntriesDirty_InstantUpdate(self, fromFunction = None):
        self._scrollEntriesDirty = True
        self.TriggerInstantUpdate('FlagScrollEntriesDirtyDirty_InstantUpdate')

    def FlagScrollEntriesDirty(self, fromFunction = None):
        self._scrollEntriesDirty = True
        if self.IsCollapsed() or self.IsMinimized():
            self.StopOverviewUpdate()
            return
        if not self.overviewUpdateThread:
            self.overviewUpdateThread = uthread.new(self.UpdateOverview)

    @telemetry.ZONE_METHOD
    def UpdateStaticDataForNodes(self, nodeList):
        tacticalSvc = sm.GetService('tactical')
        fleetSvc = sm.GetService('fleet')
        factionSvc = sm.GetService('faction')
        stateSvc = sm.GetService('state')
        usingLocalizationTooltips = localization.UseImportantTooltip()
        useSmallColorTags = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('useSmallColorTags', False)
        useSmallText = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('useSmallText', False)
        if useSmallText:
            entryHeight = 17
            fontSize = fontConst.EVE_SMALL_FONTSIZE
        else:
            entryHeight = 19
            fontSize = fontConst.EVE_MEDIUM_FONTSIZE
        labelClass = OverviewLabel
        columns = tacticalSvc.GetColumns()
        columnWidths = self.sortHeaders.GetCurrentSizes()
        currentActive, currentDirection = self.sortHeaders.GetCurrentActive()
        if currentActive:
            sortKeys = columns[columns.index(currentActive):]
        else:
            sortKeys = []
        columnSettings = {}
        for columnID in ALLCOLUMNS:
            if columnID in columns:
                if columnID in sortKeys:
                    columnSettings[columnID] = (True, sortKeys.index(columnID))
                else:
                    columnSettings[columnID] = (True, None)
            else:
                columnSettings[columnID] = (False, None)

        showIcon, sortIconIndex = columnSettings[COLUMN_ICON]
        showName, sortNameIndex = columnSettings[COLUMN_NAME]
        showDistance, sortDistanceIndex = columnSettings[COLUMN_DISTANCE]
        showSize, sortSizeIndex = columnSettings[COLUMN_SIZE]
        showAlliance, sortAllianceIndex = columnSettings[COLUMN_ALLIANCE]
        showType, sortTypeIndex = columnSettings[COLUMN_TYPE]
        showTag, sortTagIndex = columnSettings[COLUMN_TAG]
        showCorporation, sortCorporationIndex = columnSettings[COLUMN_CORPORATION]
        showFaction, sortFactionIndex = columnSettings[COLUMN_FACTION]
        showMilitia, sortMilitiaIndex = columnSettings[COLUMN_MILITIA]
        showVelocity, sortVelocityIndex = columnSettings[COLUMN_VELOCITY]
        showRadialVelocity, sortRadialVelocityIndex = columnSettings[COLUMN_RADIALVELOCITY]
        showAngularVelocity, sortAngularVelocityIndex = columnSettings[COLUMN_ANGULARVELOCITY]
        showTransversalVelocity, sortTransversalVelocityIndex = columnSettings[COLUMN_TRANSVERSALVELOCITY]
        defaultSortValue = [ 0 for each in sortKeys ]
        inFleet = bool(session.fleetid)
        for node in nodeList:
            slimItem = node.slimItem()
            ball = node.ball()
            if not (ball and slimItem):
                node.leavingOverview = True
                if node.itemID in self._scrollNodesByItemID:
                    del self._scrollNodesByItemID[node.itemID]
                continue
            self._scrollNodesByItemID[node.itemID] = node
            node.usingLocalizationTooltips = usingLocalizationTooltips
            node.useSmallText = useSmallText
            node.useSmallColorTags = useSmallColorTags
            node.decoClass.ENTRYHEIGHT = entryHeight
            node.fontSize = fontSize
            node.columns = columns
            node.columnWidths = columnWidths
            node.sortNameIndex = sortNameIndex
            node.sortDistanceIndex = sortDistanceIndex
            node.sortIconIndex = sortIconIndex
            node.sortTagIndex = sortTagIndex
            node.sortVelocityIndex = sortVelocityIndex
            node.sortRadialVelocityIndex = sortRadialVelocityIndex
            node.sortAngularVelocityIndex = sortAngularVelocityIndex
            node.sortTransversalVelocityIndex = sortTransversalVelocityIndex
            sortValue = defaultSortValue[:]
            node.sortValue = sortValue
            if node.display_NAME is None:
                self.PrimeDisplayName(node)
            elif sortNameIndex is not None:
                sortValue[sortNameIndex] = node.display_NAME.lower()
            if showType and slimItem.typeID:
                if node.display_TYPE is None:
                    typeName = cfg.invtypes.Get(slimItem.typeID).typeName
                    if usingLocalizationTooltips:
                        typeName, hint = self.PrepareLocalizationTooltip(typeName)
                        node.hint_TYPE = hint
                    node.display_TYPE = typeName
                if sortTypeIndex is not None:
                    sortValue[sortTypeIndex] = node.display_TYPE.lower()
            if showSize:
                size = ball.radius * 2
                if node.display_SIZE is None:
                    node.display_SIZE = FmtDist(size)
                if sortSizeIndex is not None:
                    sortValue[sortSizeIndex] = size
            if showTag:
                if inFleet:
                    if node.display_TAG is None:
                        node.display_TAG = fleetSvc.GetTargetTag(node.itemID)
                else:
                    node.display_TAG = ''
                if sortTagIndex is not None:
                    tag = node.display_TAG
                    if tag:
                        sortValue[sortTagIndex] = tag.lower()
                    else:
                        sortValue[sortTagIndex] = 0
            if showCorporation and slimItem.corpID:
                node.display_CORPORATION = corpTag = '[' + cfg.corptickernames.Get(slimItem.corpID).tickerName + ']'
                if sortCorporationIndex is not None:
                    sortValue[sortCorporationIndex] = corpTag.lower()
            if showMilitia and slimItem.warFactionID:
                militia = cfg.eveowners.Get(slimItem.warFactionID).name
                if usingLocalizationTooltips:
                    militia, hint = self.PrepareLocalizationTooltip(militia)
                    node.hint_MILITIA = hint
                node.display_MILITIA = militia
                if sortMilitiaIndex is not None:
                    sortValue[sortMilitiaIndex] = militia.lower()
            if showAlliance and slimItem.allianceID:
                node.display_ALLIANCE = alliance = '[' + cfg.allianceshortnames.Get(slimItem.allianceID).shortName + ']'
                if sortAllianceIndex is not None:
                    sortValue[sortAllianceIndex] = alliance.lower()
            if showFaction:
                if slimItem.ownerID and IsNPC(slimItem.ownerID) or slimItem.charID and IsNPC(slimItem.charID):
                    factionID = factionSvc.GetFaction(slimItem.ownerID or slimItem.charID)
                    if factionID:
                        faction = cfg.eveowners.Get(factionID).name
                        if usingLocalizationTooltips:
                            faction, hint = self.PrepareLocalizationTooltip(faction)
                            node.hint_FACTION = hint
                        node.display_FACTION = faction
                        if sortFactionIndex is not None:
                            sortValue[sortFactionIndex] = faction.lower()
            if node.iconAndBackgroundFlags is None:
                iconFlag, backgroundFlag = (0, 0)
                if node.updateItem:
                    iconFlag, backgroundFlag = stateSvc.GetIconAndBackgroundFlags(slimItem)
                node.iconAndBackgroundFlags = (iconFlag, backgroundFlag)
            if sortIconIndex is not None:
                iconFlag, backgroundFlag = node.iconAndBackgroundFlags
                node.iconColor, colorSortValue = GetIconColor(slimItem, getSortValue=True)
                sortValue[sortIconIndex] = [iconFlag,
                 colorSortValue,
                 backgroundFlag,
                 slimItem.categoryID,
                 slimItem.groupID,
                 slimItem.typeID]

    @telemetry.ZONE_METHOD
    def UpdateDynamicDataForNodes(self, nodeList, doYield = False):
        tacticalSvc = sm.GetService('tactical')
        bp = sm.GetService('michelle').GetBallpark(doWait=True)
        if not bp:
            self.FlagBallparkDirty('DoBallsAdded')
            return
        myBall = bp.GetBall(eve.session.shipid)
        GetInvItem = bp.GetInvItem
        UpdateVelocityData = self.UpdateVelocityData
        columns = tacticalSvc.GetColumns()
        showVelocityCombined = False
        showDistance = COLUMN_DISTANCE in columns
        showIcon = COLUMN_ICON in columns
        calculateRadialVelocity = False
        calculateCombinedVelocity = False
        calculateRadialNormal = False
        calculateTransveralVelocity = False
        calculateAngularVelocity = False
        calculateVelocity = False
        if COLUMN_VELOCITY in columns:
            calculateVelocity = True
            showVelocityCombined = True
        if COLUMN_ANGULARVELOCITY in columns:
            calculateRadialVelocity = True
            calculateCombinedVelocity = True
            calculateRadialNormal = True
            calculateTransveralVelocity = True
            calculateAngularVelocity = True
            showVelocityCombined = True
        if COLUMN_TRANSVERSALVELOCITY in columns:
            calculateRadialVelocity = True
            calculateCombinedVelocity = True
            calculateRadialNormal = True
            calculateTransveralVelocity = True
            showVelocityCombined = True
        if COLUMN_RADIALVELOCITY in columns:
            calculateRadialVelocity = True
            calculateCombinedVelocity = True
            calculateRadialNormal = True
            showVelocityCombined = True
        now = blue.os.GetSimTime()
        counter = 0
        for node in nodeList:
            ball = node.ball()
            slimItem = node.slimItem()
            if not slimItem:
                slimItem = GetInvItem(node.itemID)
                if slimItem:
                    node.slimItem = _weakref.ref(slimItem)
                    node.iconColor = None
                    self.PrimeDisplayName(node)
                    if node.panel:
                        if showIcon:
                            node.panel.UpdateIcon()
                            node.panel.UpdateIconColor()
                    self.UpdateIconAndBackgroundFlagsOnNode(node)
            if ball:
                if showDistance:
                    ball.GetVectorAt(now)
                    node.rawDistance = rawDistance = max(ball.surfaceDist, 0)
                    if node.sortDistanceIndex is not None:
                        node.sortValue[node.sortDistanceIndex] = rawDistance
                if showVelocityCombined and node.updateItem and ball.isFree and myBall:
                    ball.GetVectorAt(now)
                    UpdateVelocityData(node, ball, myBall, calculateVelocity, calculateRadialVelocity, calculateCombinedVelocity, calculateRadialNormal, calculateTransveralVelocity, calculateAngularVelocity)
            if doYield:
                counter += 1
                if counter == 20:
                    blue.pyos.BeNice(100)
                    if self.destroyed:
                        self.StopOverviewUpdate()
                        return
                    counter = 0

    @telemetry.ZONE_METHOD
    def CheckForNewEntriesAndRefreshScrollSetup(self):
        ballpark = sm.GetService('michelle').GetBallpark(doWait=True)
        if ballpark is None:
            return
        tacticalSvc = sm.GetService('tactical')
        overviewPresetSvc = sm.GetService('overviewPresetSvc')
        columns = tacticalSvc.GetColumns()
        self.sortHeaders.CreateColumns(columns, fixedColumns=FIXEDCOLUMNS)
        self.UpdateColumnHilite()
        newEntries = []
        currentNotWanted = set()
        with ScrollListLock:
            if self._ballparkDirty:
                factionSvc = sm.GetService('faction')
                stateSvc = sm.GetService('state')
                filterGroups = overviewPresetSvc.GetValidGroups()
                filteredStates = tacticalSvc.GetFilteredStatesFunctionNames()
                alwaysShownStates = tacticalSvc.GetAlwaysShownStatesFunctionNames()
                CheckIfFilterItem = stateSvc.CheckIfFilterItem
                CheckFiltered = tacticalSvc.CheckFiltered
                CheckIfUpdateItem = stateSvc.CheckIfUpdateItem
                GetInvItem = ballpark.GetInvItem
                GetBall = ballpark.GetBall
                currentItemIDs = self._scrollNodesByItemID
                log.LogInfo('Overview - Checking ballpark for new entries')

                def CheckIfDoWant(myItemID, mySlimItem):
                    if not mySlimItem:
                        return False
                    if mySlimItem.groupID not in filterGroups:
                        return False
                    if myItemID == session.shipid:
                        return False
                    if CheckIfFilterItem(mySlimItem) and CheckFiltered(mySlimItem, filteredStates, alwaysShownStates):
                        return False
                    return True

                for itemID in ballpark.balls.keys():
                    slimItem = GetInvItem(itemID)
                    doWant = CheckIfDoWant(itemID, slimItem)
                    if not doWant:
                        if itemID in currentItemIDs:
                            currentNotWanted.add(itemID)
                            if itemID in self._scrollNodesByItemID:
                                node = self._scrollNodesByItemID[itemID]
                                node.leavingOverview = True
                                del self._scrollNodesByItemID[itemID]
                        continue
                    if itemID not in currentItemIDs:
                        updateItem = CheckIfUpdateItem(slimItem)
                        data = {'itemID': itemID,
                         'updateItem': updateItem}
                        newNode = listentry.Get('OverviewScrollEntry', data)
                        ball = GetBall(itemID)
                        newNode.ball = _weakref.ref(ball)
                        newNode.slimItem = _weakref.ref(slimItem)
                        if updateItem:
                            newNode.ewarGraphicIDs = self.GetEwarDataForNode(newNode)
                        newNode.ewarHints = self.ewarHintsByGraphicID
                        newEntries.append(newNode)

            nodeList = newEntries[:]
            if self._scrollEntriesDirty:
                log.LogInfo('Overview - Update static data on current overview entries')
                nodeList.extend([ node for node in self.sr.scroll.sr.nodes if node.itemID not in currentNotWanted ])
            self.UpdateStaticDataForNodes(nodeList)
            self.sr.scroll.PurgeInvisibleEntries()
            self.overviewSorted = False
            if newEntries:
                self.sr.scroll.ShowHint()
                self.sr.scroll.AddNodes(-1, newEntries)
        return newEntries

    @telemetry.ZONE_METHOD
    def UpdateOverview(self, doYield = False):
        """
        Loops over the overview scroll entries and updates their dynamic properties and
        sorts the list. All visible entries in the scroll will get Load triggered,
        its upto them how much they will update visually.
        On initial entry this function does not yield while updating so we get the first update
        instant, but after that it will yield while updating the sortdata and the scroll.
        This function also checks if slimItem is not longer available and removes
        scroll entry if so. (or marks it as goner and changes its appearance if the OverView
        is in 'freeze' mode)
        """
        if self.destroyed:
            return
        if self._ballparkDirty or self._scrollEntriesDirty:
            newEntries = self.CheckForNewEntriesAndRefreshScrollSetup()
            if newEntries:
                doYield = False
            self._ballparkDirty = False
            self._scrollEntriesDirty = False
        updateStartTime = blue.os.GetWallclockTimeNow()
        try:
            if not eve.session.solarsystemid:
                self.StopOverviewUpdate()
                return
            if self.IsCollapsed() or self.IsMinimized():
                self.StopOverviewUpdate()
                return
            if self.destroyed:
                return
            bp = sm.GetService('michelle').GetBallpark(doWait=True)
            if not bp:
                self.StopOverviewUpdate()
                return
            tacticalSvc = sm.GetService('tactical')
            stateSvc = sm.StartService('state')
            fleetSvc = sm.GetService('fleet')
            columns = tacticalSvc.GetColumns()
            columnWidths = self.sortHeaders.GetCurrentSizes()
            broadcastsToTop = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('overviewBroadcastsToTop', False)
            fleetBroadcasts = fleetSvc.GetCurrentFleetBroadcasts()
            mouseCoords = trinity.GetCursorPos()
            if mouseCoords != self.prevMouseCoords:
                self.lastMovementTime = blue.os.GetWallclockTime()
                self.prevMouseCoords = mouseCoords
            insider = uiutil.IsUnder(uicore.uilib.mouseOver, self.sr.scroll.GetContentContainer()) or uicore.uilib.mouseOver is self.sr.scroll.GetContentContainer()
            mouseMoving = blue.os.TimeDiffInMs(self.lastMovementTime, blue.os.GetWallclockTime()) > self.mouseMovementTimeout
            mouseInsideApp = mouseCoords[0] > 0 and mouseCoords[0] < trinity.app.width and mouseCoords[1] > 0 and mouseCoords[1] < trinity.app.height
            sortingFrozen = self.sortingFrozen = insider and mouseInsideApp and not mouseMoving or self._freezeOverview
            if sortingFrozen:
                updateList = self.sr.scroll.GetVisibleNodes()
                self.sortHeaders.SetSortIcon('res:/UI/Texture/classes/Overview/columnLock.png')
            else:
                updateList = self.sr.scroll.sr.nodes
                self.sortHeaders.SetSortIcon(None)

            def GetSortValue(_node):
                if broadcastsToTop:
                    if _node.itemID in fleetBroadcasts:
                        return (1, _node.sortValue)
                    else:
                        return (2, _node.sortValue)
                return _node.sortValue

            ballpark = sm.GetService('michelle').GetBallpark(doWait=True)
            if ballpark is None:
                return
            GetInvItem = ballpark.GetInvItem
            self.UpdateDynamicDataForNodes(updateList, doYield=doYield)
            counter = 0
            nodesToRemove = []
            for node in updateList:
                node.columnWidths = columnWidths
                if node.leavingOverview:
                    if node.panel:
                        node.panel.opacity = 0.25
                        node.panel.state = uiconst.UI_DISABLED
                    nodesToRemove.append(node)
                    continue
                ball = node.ball()
                slimItem = node.slimItem()
                if not (slimItem and ball):
                    node.leavingOverview = True
                    if node.itemID in self._scrollNodesByItemID:
                        del self._scrollNodesByItemID[node.itemID]
                    if node.panel:
                        node.panel.opacity = 0.25
                        node.panel.state = uiconst.UI_DISABLED
                    nodesToRemove.append(node)
                    continue
                if doYield:
                    counter += 1
                    if counter == 20:
                        blue.pyos.BeNice(100)
                        if self.destroyed:
                            self.StopOverviewUpdate()
                            return
                        counter = 0

            if doYield:
                blue.synchro.Yield()
                if self.destroyed:
                    self.StopOverviewUpdate()
                    return
            if not sortingFrozen:
                if nodesToRemove:
                    self.sr.scroll.RemoveNodes(nodesToRemove)
                currentActive, currentDirection = self.sortHeaders.GetCurrentActive()
                with ScrollListLock:
                    sortlist = sorted(self.sr.scroll.sr.nodes, key=GetSortValue, reverse=not currentDirection)
                    self.sr.scroll.SetOrderedNodes(sortlist, loadNodes=False)
                self.overviewSorted = True
            else:
                self.overviewSorted = False
            counter = 0
            for node in self.sr.scroll.GetVisibleNodes():
                if node.panel and node.panel.state != uiconst.UI_HIDDEN:
                    node.panel.Load(node)
                    counter += 1
                    if counter == 10:
                        blue.pyos.BeNice(100)
                        if self.destroyed:
                            self.StopOverviewUpdate()
                            return
                        counter = 0

            if not self.sr.scroll.sr.nodes:
                self.sr.scroll.ShowHint(localization.GetByLabel('UI/Common/NothingFound'))
            else:
                self.sr.scroll.ShowHint()
        except Exception:
            log.LogException(extraText='Error updating inflight overview')
            sys.exc_clear()

        if doYield:
            diff = blue.os.TimeDiffInMs(updateStartTime, blue.os.GetWallclockTimeNow())
            sleep = max(self.minUpdateSleep, self.maxUpdateSleep - diff)
            blue.pyos.synchro.SleepWallclock(sleep)
        if not self.destroyed and (not self.overviewUpdateThread or self.overviewUpdateThread == stackless.getcurrent()):
            self.overviewUpdateThread = uthread.new(self.UpdateOverview, doYield=True)

    def SetFreezeOverview(self, freeze = True):
        triggerUpdate = False
        if not freeze and freeze != self._freezeOverview:
            triggerUpdate = True
        self._freezeOverview = freeze
        if triggerUpdate and getattr(self, 'overviewSorted', False) is False:
            self.TriggerInstantUpdate('SetFreezeOverview')

    def UpdateForOneCharacter(self, charID, *args):
        pass

    def OnExpanded(self, *args):
        self.TriggerInstantUpdate('OnExpanded')

    def OnCollapsed(self, *args):
        self.StopOverviewUpdate()
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()

    def OnEndMaximize_(self, *args):
        self.TriggerInstantUpdate('OnEndMaximize_')

    def OnEndMinimize_(self, *args):
        self.StopOverviewUpdate()
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()

    @telemetry.ZONE_METHOD
    def UpdateVelocityData(self, node, ball, myBall, calculateVelocity, calculateRadialVelocity, calculateCombinedVelocity, calculateRadialNormal, calculateTransveralVelocity, calculateAngularVelocity):
        surfaceDist = max(ball.surfaceDist, 0)
        velocity = None
        radialVelocity = None
        angularVelocity = None
        transveralVelocity = None
        if calculateCombinedVelocity:
            CombVel4 = (ball.vx - myBall.vx, ball.vy - myBall.vy, ball.vz - myBall.vz)
        if calculateRadialNormal:
            RadNorm4 = geo2.Vec3Normalize((ball.x - myBall.x, ball.y - myBall.y, ball.z - myBall.z))
        if calculateVelocity:
            velocity = ball.GetVectorDotAt(blue.os.GetSimTime()).Length()
        if calculateRadialVelocity:
            radialVelocity = geo2.Vec3Dot(CombVel4, RadNorm4)
        if calculateTransveralVelocity:
            transveralVelocity = geo2.Vec3Length(geo2.Vec3Subtract(CombVel4, geo2.Vec3Scale(RadNorm4, radialVelocity)))
        if calculateAngularVelocity:
            angularVelocity = transveralVelocity / max(1.0, surfaceDist)
        node.rawVelocity = velocity
        node.rawRadialVelocity = radialVelocity
        node.rawAngularVelocity = angularVelocity
        node.rawTransveralVelocity = transveralVelocity
        if node.sortVelocityIndex is not None:
            node.sortValue[node.sortVelocityIndex] = velocity
        if node.sortRadialVelocityIndex is not None:
            node.sortValue[node.sortRadialVelocityIndex] = radialVelocity
        if node.sortAngularVelocityIndex is not None:
            node.sortValue[node.sortAngularVelocityIndex] = angularVelocity
        if node.sortTransversalVelocityIndex is not None:
            node.sortValue[node.sortTransversalVelocityIndex] = transveralVelocity

    def GetSelectedTabArgs(self):
        if hasattr(self, 'maintabs'):
            return self.maintabs.GetSelectedArgs()

    def GetSelectedTabKey(self):
        if hasattr(self, 'maintabs'):
            selectedArgs = self.maintabs.GetSelectedArgs()
            if selectedArgs is None:
                return
            else:
                return selectedArgs[3]

    def OnSessionChanged(self, isRemote, session, change):
        if self.destroyed:
            return
        if 'solarsystemid' in change:
            self.sr.scroll.Clear()
            self._scrollNodesByItemID = {}
        if 'shipid' in change:
            self.FlagBallparkDirty('OnSessionChanged')

    def OnTutorialHighlightItem(self, itemID, isActive):
        node = self._scrollNodesByItemID.get(itemID, None)
        if node is None:
            return
        if node.panel:
            node.panel.UpdateTutorialHighlight(isActive)


FMT_RADPERSEC = u'{value} rad/sec'
KILOMETERS10 = 10000.0
KILOMETERS10000000 = 10000000000.0

class SpaceObjectIcon(Container):
    iconSprite = None
    hostileIndicator = None
    attackingMeIndicator = None
    targetingIndicator = None
    targetedByMeIndicator = None
    myActiveTargetIndicator = None
    flagIcon = None
    flagIconBackground = None
    flagBackgroundColor = None
    default_width = 16
    default_height = 16
    default_align = uiconst.TOPLEFT
    iconHint = None
    iconColorHint = None
    flagStateHint = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.iconSprite = Sprite(parent=self, name='iconSprite', state=uiconst.UI_DISABLED, pos=(0, 0, 16, 16))

    def SetHostileState(self, state, *args, **kwds):
        """
        Displays or hides hostile (blinking yellow square) on
        overview entries
        """
        if state:
            if not self.hostileIndicator:
                self.hostileIndicator = BlinkingSpriteOnSharedCurve(parent=self, name='hostile', pos=(-1, -1, 18, 18), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/hostileBracket.png', align=uiconst.TOPLEFT, color=(1.0, 0.8, 0.0, 0.3), curveSetName='sharedHostileCurveSet')
        elif self.hostileIndicator:
            self.hostileIndicator.Close()
            self.hostileIndicator = None

    def SetAttackingState(self, state):
        """
        Displays or hides attacking indicator (blinking red square) on
        overview entries
        """
        if state:
            if not self.attackingMeIndicator:
                self.attackingMeIndicator = BlinkingSpriteOnSharedCurve(parent=self, name='attackingMe', pos=(-1, -1, 18, 18), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/hostileBracket.png', align=uiconst.TOPLEFT, color=(0.8, 0.0, 0.0, 0.3), curveSetName='sharedHostileCurveSet')
            if self.hostileIndicator:
                self.hostileIndicator.Close()
                self.hostileIndicator = None
        elif self.attackingMeIndicator:
            self.attackingMeIndicator.Close()
            self.attackingMeIndicator = None

    def SetTargetedByMeState(self, state):
        if state:
            if not self.targetedByMeIndicator:
                self.targetedByMeIndicator = Sprite(parent=self, name='targetedByMeIndicator', pos=(-1, -1, 18, 18), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/activeTarget.png', align=uiconst.TOPLEFT, color=(1.0, 1.0, 1.0, 0.5), idx=0)
        elif self.targetedByMeIndicator:
            self.targetedByMeIndicator.Close()
            self.targetedByMeIndicator = None

    def SetActiveTargetState(self, state):
        if state:
            if not self.myActiveTargetIndicator:
                self.myActiveTargetIndicator = Sprite(parent=self, name='myActiveTargetIndicator', pos=(-1, -1, 18, 18), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/activeTarget.png', align=uiconst.TOPLEFT, idx=0)
        elif self.myActiveTargetIndicator:
            self.myActiveTargetIndicator.Close()
            self.myActiveTargetIndicator = None

    def SetIconFlag(self, iconFlag, useSmallColorTags = False):
        if iconFlag and iconFlag != -1:
            stateSvc = sm.GetService('state')
            if self.flagIcon is None:
                self.flagIcon = FlagIconWithState(parent=self, pos=(-3, -2, 9, 9), state=uiconst.UI_DISABLED, align=uiconst.BOTTOMRIGHT)
            flagInfo = stateSvc.GetStatePropsColorAndBlink(iconFlag)
            self.flagIcon.ModifyIcon(flagInfo=flagInfo, showHint=False)
            self.flagStateHint = flagInfo.flagProperties.text
            if settings.user.overview.Get('useSmallColorTags', 0):
                self.flagIcon.ChangeFlagPos(self.flagIcon.left, self.flagIcon.top, 5, 5)
            else:
                self.flagIcon.ChangeFlagPos(self.flagIcon.left, self.flagIcon.top, 9, 9)
            hideIcon = settings.user.overview.Get('useSmallColorTags', 0)
            self.flagIcon.ChangeIconVisibility(display=not hideIcon)
        elif self.flagIcon:
            self.flagIcon.Close()
            self.flagIcon = None
            self.flagStateHint = None

    def SetBackgroundColorFlag(self, backgroundFlag):
        if backgroundFlag and backgroundFlag != -1:
            stateSvc = sm.GetService('state')
            r, g, b, a = stateSvc.GetStateBackgroundColor(backgroundFlag)
            a = a * 0.5
            if not self.flagBackgroundColor:
                self.flagBackgroundColor = Sprite(bgParent=self, name='bgColor', texturePath='res:/UI/Texture/classes/Bracket/bracketBackground.png', color=(r,
                 g,
                 b,
                 a))
            else:
                self.flagBackgroundColor.SetRGBA(r, g, b, a)
            blink = stateSvc.GetStateBackgroundBlink(backgroundFlag)
            if blink:
                if not self.flagBackgroundColor.HasAnimation('color'):
                    uicore.animations.FadeTo(self.flagBackgroundColor, startVal=0.0, endVal=a, duration=0.75, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
            else:
                self.flagBackgroundColor.StopAnimations()
        elif self.flagBackgroundColor:
            self.flagBackgroundColor.Close()
            self.flagBackgroundColor = None

    def SetTargetingState(self, state):
        if state:
            if not self.targetingIndicator:
                par = Container(name='targeting', align=uiconst.CENTER, width=28, height=28, parent=self)
                self.targetingIndicator = par
                Fill(parent=par, align=uiconst.TOPLEFT, left=0, top=3, width=5, height=2, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.TOPRIGHT, left=0, top=3, width=5, height=2, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.BOTTOMLEFT, left=0, top=3, width=5, height=2, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.BOTTOMRIGHT, left=0, top=3, width=5, height=2, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.TOPLEFT, left=3, top=0, width=2, height=3, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.TOPRIGHT, left=3, top=0, width=2, height=3, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.BOTTOMLEFT, left=3, top=0, width=2, height=3, color=(1.0, 1.0, 1.0, 0.5))
                Fill(parent=par, align=uiconst.BOTTOMRIGHT, left=3, top=0, width=2, height=3, color=(1.0, 1.0, 1.0, 0.5))
                uthread.pool('Tactical::Targeting', self.AnimateTargeting, par)
        elif self.targetingIndicator:
            self.targetingIndicator.Close()
            self.targetingIndicator = None

    def AnimateTargeting(self, par):
        while par and not par.destroyed:
            p = par.children[0]
            for i in xrange(1, 8):
                par.width = par.height = 28 - i * 2
                blue.pyos.synchro.SleepSim(50)

    @telemetry.ZONE_METHOD
    def UpdateSpaceObjectIcon(self, slimItem, ball):
        if self.destroyed:
            return
        iconHint = None
        if slimItem.groupID == const.groupWreck:
            if slimItem.isEmpty:
                iconNo = 'res:/UI/Texture/Icons/38_16_29.png'
                iconHint = localization.GetByLabel('Tooltips/Overview/EmptyWreck')
            else:
                iconNo = 'res:/UI/Texture/Icons/38_16_28.png'
                iconHint = localization.GetByLabel('Tooltips/Overview/ContainsLoot')
        elif slimItem.hackingSecurityState is not None:
            iconNo, iconHint = uicls.InSpaceBracket.GetHackingIcon(slimItem.hackingSecurityState)
        else:
            iconNo, _dockType, _minDist, _maxDist, _iconOffset, _logflag = sm.GetService('bracket').GetBracketProps(slimItem, ball)
        self.iconSprite.LoadIcon(iconNo)
        self.iconHint = iconHint

    @telemetry.ZONE_METHOD
    def UpdateSpaceObjectIconColor(self, slimItem, ball):
        if self.destroyed:
            return
        iconColor, colorHint = GetIconColor(slimItem, getColorHint=True)
        r, g, b = iconColor
        if slimItem.groupID in (const.groupWreck, const.groupSpawnContainer) and sm.GetService('wreck').IsViewedWreck(slimItem.itemID):
            attenuation = 0.55
            r, g, b = r * attenuation, g * attenuation, b * attenuation
        self.iconSprite.color = (r,
         g,
         b,
         1)
        self.iconColorHint = colorHint

    def UpdateSpaceObjectFlagAndBackgroundColor(self, slimItem, ball):
        stateService = sm.GetService('state')
        updateItem = stateService.CheckIfUpdateItem(slimItem)
        if updateItem:
            iconFlag, backgroundFlag = sm.GetService('state').GetIconAndBackgroundFlags(slimItem)
            self.SetIconFlag(iconFlag, useSmallColorTags=False)
            self.SetBackgroundColorFlag(backgroundFlag)

    def UpdateSpaceObjectState(self, slimItem, ball):
        if self.destroyed:
            return
        stateService = sm.GetService('state')
        attacking, hostile, targeting, targeted, activeTarget = stateService.GetStates(slimItem.itemID, [state.threatAttackingMe,
         state.threatTargetsMe,
         state.targeting,
         state.targeted,
         state.activeTarget])
        self.SetActiveTargetState(activeTarget)
        self.SetTargetedByMeState(targeted)
        self.SetTargetingState(targeting)
        updateItem = stateService.CheckIfUpdateItem(slimItem)
        if updateItem:
            self.SetHostileState(hostile)
            self.SetAttackingState(attacking)


class OverviewScrollEntry(uicontrols.SE_BaseClassCore):
    __guid__ = 'listentry.OverviewScrollEntry'
    __notifyevents__ = []
    ENTRYHEIGHT = 19
    hostileIndicator = None
    attackingMeIndicator = None
    myActiveTargetIndicator = None
    targetingIndicator = None
    flagIcon = None
    flagIconBackground = None
    flagBackground = None
    fleetBroadcastIcon = None
    fleetBroadcastID = None
    loadedIconAndBackgroundFlags = None
    loadedEwarGraphicIDs = None
    rightAlignedIconContainer = None
    selectionSprite = None
    globalMaxWidth = None

    @telemetry.ZONE_METHOD
    def Startup(self, *args):
        self.sr.flag = None
        self.sr.bgColor = None
        self.columnLabels = []
        self.ewarIcons = {}
        node = self.sr.node
        self.updateItem = node.updateItem
        self.itemID = node.itemID
        self.stateItemID = node.itemID
        slimItem = node.slimItem()
        ball = node.ball()
        if not (slimItem and ball):
            return
        self.mainIcon = SpaceObjectIcon(parent=self, align=uiconst.CENTERLEFT, left=3)
        self.mainIcon.LoadTooltipPanel = self.LoadIconTooltipPanel
        self.mainIcon.GetTooltipPointer = self.GetIconTooltipPointer
        self.mainIcon.DelegateEvents(self)
        self.mainIcon.UpdateSpaceObjectIcon(slimItem, ball)
        self.mainIcon.UpdateSpaceObjectState(slimItem, ball)
        selected, hilited = sm.GetService('state').GetStates(self.stateItemID, [state.selected, state.mouseOver])
        if selected:
            self.ShowSelected()
        if hilited:
            self.ShowHilite()
        elif uicore.uilib.mouseOver is not self:
            self.HideHilite()
        self.UpdateFleetBroadcast()

    @telemetry.ZONE_METHOD
    def Load(self, node):
        global FMT_M
        global FMT_AU
        global FMT_KM
        global FMT_VELOCITY
        languageID = localization.util.GetLanguageID()
        FMT_M = eveLocalization.GetMessageByID(234383, languageID)
        FMT_KM = eveLocalization.GetMessageByID(234384, languageID)
        FMT_AU = eveLocalization.GetMessageByID(234385, languageID)
        FMT_VELOCITY = eveLocalization.GetMessageByID(239583, languageID)
        with ExceptionEater("Exception during overview's Load"):
            self.UpdateColumns()
            if (node.iconAndBackgroundFlags, node.useSmallColorTags) != self.loadedIconAndBackgroundFlags:
                slimItem = node.slimItem()
                if not slimItem:
                    return
                self.UpdateFlagAndBackground(slimItem)
            if node.ewarGraphicIDs != self.loadedEwarGraphicIDs:
                self.UpdateEwar()

    def _OnSizeChange_NoBlock(self, displayWidth, displayHeight):
        self.SetGlobalMaxWidth()

    def SetGlobalMaxWidth(self):
        if self.rightAlignedIconContainer and self.rightAlignedIconContainer.width:
            globalMaxWidth = self.width - self.rightAlignedIconContainer.width - 6
        else:
            globalMaxWidth = None
        self.globalMaxWidth = globalMaxWidth
        for each in self.columnLabels:
            each.globalMaxWidth = globalMaxWidth

    def CreateRightAlignedIconContainer(self):
        if self.rightAlignedIconContainer is None:
            self.rightAlignedIconContainer = uiprimitives.Container(parent=self, name='rightAlignedIconContainer', align=uiconst.CENTERRIGHT, width=200, height=16, state=uiconst.UI_PICKCHILDREN, idx=0)
        return self.rightAlignedIconContainer

    def UpdateRightAlignedIconContainerSize(self):
        if self.rightAlignedIconContainer:
            preWidth = self.rightAlignedIconContainer.width
            self.rightAlignedIconContainer.width = newWidth = sum([ each.width for each in self.rightAlignedIconContainer.children if each.display ])
            if preWidth != newWidth:
                self.SetGlobalMaxWidth()

    @telemetry.ZONE_METHOD
    def UpdateFleetBroadcast(self):
        broadcastID, broadcastFlag, broadcastData = sm.GetService('fleet').GetCurrentFleetBroadcastOnItem(self.itemID)
        if broadcastID != self.fleetBroadcastID:
            if broadcastID is None:
                if self.fleetBroadcastIcon:
                    self.fleetBroadcastIcon.Close()
                    self.fleetBroadcastIcon = None
                    self.UpdateRightAlignedIconContainerSize()
                self.fleetBroadcastType = self.fleetBroadcastID = None
                return
            broadcastType = fleetbr.flagToName[broadcastFlag]
            if broadcastType in ('EnemySpotted', 'NeedBackup', 'InPosition', 'HoldPosition'):
                inBubble = InBubble(self.itemID)
                if not inBubble:
                    if self.fleetBroadcastID is not None:
                        if self.fleetBroadcastIcon:
                            self.fleetBroadcastIcon.Close()
                            self.fleetBroadcastIcon = None
                        self.fleetBroadcastType = self.fleetBroadcastID = None
                    return
            self.fleetBroadcastType = broadcastType
            self.fleetBroadcastID = broadcastID
            if not self.fleetBroadcastIcon:
                self.fleetBroadcastIcon = uicontrols.Icon(name='fleetBroadcastIcon', parent=self.CreateRightAlignedIconContainer(), align=uiconst.TORIGHT, pos=(0, 0, 16, 16), state=uiconst.UI_DISABLED)
            icon = fleetbr.types[broadcastType]['smallIcon']
            self.fleetBroadcastIcon.LoadIcon(icon)
            self.UpdateRightAlignedIconContainerSize()

    @telemetry.ZONE_METHOD
    def UpdateFlagAndBackground(self, slimItem, *args):
        if self.destroyed or not self.updateItem or slimItem is None:
            return
        node = self.sr.node
        self.loadedIconAndBackgroundFlags = (node.iconAndBackgroundFlags, node.useSmallColorTags)
        try:
            if slimItem.groupID != const.groupAgentsinSpace and (slimItem.ownerID and IsNPC(slimItem.ownerID) or slimItem.charID and IsNPC(slimItem.charID)):
                self.mainIcon.SetIconFlag(-1)
                if self.flagBackground:
                    self.flagBackground.Close()
                    self.flagBackground = None
            else:
                node = self.sr.node
                stateSvc = sm.GetService('state')
                iconFlag, backgroundFlag = node.iconAndBackgroundFlags
                self.mainIcon.SetIconFlag(iconFlag, useSmallColorTags=node.useSmallColorTags)
                if backgroundFlag and backgroundFlag != -1:
                    r, g, b, a = stateSvc.GetStateBackgroundColor(backgroundFlag)
                    a = a * 0.5
                    if not self.flagBackground:
                        self.flagBackground = Fill(name='bgColor', parent=self, state=uiconst.UI_DISABLED, color=(r,
                         g,
                         b,
                         a))
                    else:
                        self.flagBackground.SetRGBA(r, g, b, a)
                    blink = stateSvc.GetStateBackgroundBlink(backgroundFlag)
                    if blink:
                        if not self.flagBackground.HasAnimation('color'):
                            uicore.animations.FadeTo(self.flagBackground, startVal=0.0, endVal=a, duration=0.75, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
                    else:
                        self.flagBackground.StopAnimations()
                elif self.flagBackground:
                    self.flagBackground.Close()
                    self.flagBackground = None
        except AttributeError:
            if not self.destroyed:
                raise

    @telemetry.ZONE_METHOD
    def UpdateFlagPositions(self, *args, **kwds):
        pass

    @telemetry.ZONE_METHOD
    def UpdateColumns(self):
        node = self.sr.node
        haveIcon = False
        currentLabels = []
        columnOffset = 0
        currentColumns = node.columns
        for columnID in currentColumns:
            columnWidth = node.columnWidths[columnID]
            if columnID == COLUMN_ICON:
                self.mainIcon.left = columnOffset + 3
                self.UpdateIconColor()
                self.mainIcon.state = uiconst.UI_NORMAL
                columnOffset += columnWidth
                haveIcon = True
                continue
            displayValue = self.GetColumnDisplayValue(node, columnID)
            if not displayValue:
                columnOffset += columnWidth
                continue
            label = None
            if self.columnLabels:
                label = self.columnLabels.pop(0)
                if label.destroyed:
                    label = None
            if not label:
                label = OverviewLabel(parent=self, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, idx=0, fontSize=node.fontSize)
            columnHint = node.get('hint_' + columnID, None)
            if columnHint:
                label.state = uiconst.UI_NORMAL
            else:
                label.state = uiconst.UI_DISABLED
            label.columnWidth = columnWidth - COLUMNMARGIN * 2
            label.text = displayValue
            label.rightAligned = columnID in RIGHTALIGNEDCOLUMNS
            label.columnPosition = columnOffset + COLUMNMARGIN
            label.globalMaxWidth = self.globalMaxWidth
            label.hint = columnHint
            label.stateItemID = self.stateItemID
            columnOffset += columnWidth
            currentLabels.append(label)

        if not haveIcon:
            self.mainIcon.state = uiconst.UI_HIDDEN
        if self.columnLabels:
            while self.columnLabels:
                label = self.columnLabels.pop()
                label.Close()

        self.columnLabels = currentLabels

    def GetRadialMenuIndicator(self, create = True, *args):
        indicator = getattr(self, 'radialMenuIndicator', None)
        if indicator and not indicator.destroyed:
            return indicator
        if not create:
            return
        self.radialMenuIndicator = FillThemeColored(bgParent=self, name='radialMenuIndicator', colorType=uiconst.COLORTYPE_UIHILIGHT)
        return self.radialMenuIndicator

    def ShowRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=True)
        indicator.display = True

    def HideRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=False)
        if indicator:
            indicator.display = False

    @classmethod
    def GetColumnDisplayValue(cls, node, columnID):
        if columnID == COLUMN_DISTANCE:
            surfaceDist = node.rawDistance
            if surfaceDist is None:
                return u''
            if surfaceDist < KILOMETERS10:
                currentDist = int(surfaceDist)
                if currentDist != node.lastFormattedDistance:
                    node.display_DISTANCE = FMT_M.format(distance=FMTFUNCTION(currentDist, useGrouping=True))
                    node.lastFormattedDistance = currentDist
            elif surfaceDist < KILOMETERS10000000:
                currentDist = long(surfaceDist / 1000)
                if currentDist != node.lastFormattedDistance:
                    node.display_DISTANCE = FMT_KM.format(distance=FMTFUNCTION(currentDist, useGrouping=True))
                    node.lastFormattedDistance = currentDist
            else:
                currentDist = round(surfaceDist / const.AU, 1)
                if currentDist != node.lastFormattedDistance:
                    node.display_DISTANCE = FMT_AU.format(distance=FMTFUNCTION(currentDist, useGrouping=True, decimalPlaces=1))
                    node.lastFormattedDistance = currentDist
            return node.display_DISTANCE or u''
        if columnID == COLUMN_ANGULARVELOCITY:
            sortValue = node.rawAngularVelocity
            if sortValue is not None:
                currentAngularVelocity = round(sortValue, 7)
                if currentAngularVelocity != node.lastFormattedAngularVelocity:
                    node.display_ANGULARVELOCITY = FMTFUNCTION(currentAngularVelocity, useGrouping=True, decimalPlaces=7)
                    node.lastFormattedAngularVelocity = currentAngularVelocity
                return node.display_ANGULARVELOCITY or u'-'
        elif columnID == COLUMN_VELOCITY:
            sortValue = node.rawVelocity
            if sortValue is not None:
                currentVelocity = int(sortValue)
                if currentVelocity != node.lastFormattedVelocity:
                    node.display_VELOCITY = FMTFUNCTION(currentVelocity, useGrouping=True)
                    node.lastFormattedVelocity = currentVelocity
                return node.display_VELOCITY or u'-'
        elif columnID == COLUMN_RADIALVELOCITY:
            sortValue = node.rawRadialVelocity
            if sortValue is not None:
                currentRadialVelocity = int(sortValue)
                if currentRadialVelocity != node.lastFormattedRadialVelocity:
                    node.display_RADIALVELOCITY = FMTFUNCTION(currentRadialVelocity, useGrouping=True)
                    node.lastFormattedRadialVelocity = currentRadialVelocity
                return node.display_RADIALVELOCITY or u'-'
        elif columnID == COLUMN_TRANSVERSALVELOCITY:
            sortValue = node.rawTransveralVelocity
            if sortValue is not None:
                currentTransveralVelocity = int(sortValue)
                if currentTransveralVelocity != node.lastFormattedTransveralVelocity:
                    node.display_TRANSVERSALVELOCITY = FMTFUNCTION(currentTransveralVelocity, useGrouping=True)
                    node.lastFormattedTransveralVelocity = currentTransveralVelocity
                return node.display_TRANSVERSALVELOCITY or u'-'
        return node.Get('display_' + columnID, None)

    @telemetry.ZONE_METHOD
    def UpdateEwar(self):
        node = self.sr.node
        ewarGraphicIDs = node.ewarGraphicIDs
        self.loadedEwarGraphicIDs = ewarGraphicIDs
        for graphicID, icon in self.ewarIcons.iteritems():
            if not ewarGraphicIDs or graphicID not in ewarGraphicIDs:
                icon.state = uiconst.UI_HIDDEN

        if ewarGraphicIDs:
            for graphicID in ewarGraphicIDs:
                if graphicID in self.ewarIcons:
                    self.ewarIcons[graphicID].state = uiconst.UI_NORMAL
                else:
                    icon = uicontrols.Icon(parent=self.CreateRightAlignedIconContainer(), align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, width=16, hint=node.ewarHints[graphicID], graphicID=graphicID, ignoreSize=True)
                    self.ewarIcons[graphicID] = icon

        self.UpdateRightAlignedIconContainerSize()

    def OnStateChange(self, itemID, flag, status, *args):
        if self.stateItemID != itemID:
            return
        if flag == state.mouseOver:
            self.Hilite(status)
        elif flag == state.selected:
            if status:
                self.ShowSelected()
            else:
                self.ShowDeselected()
        elif flag == state.threatTargetsMe:
            attacking, = sm.StartService('state').GetStates(itemID, [state.threatAttackingMe])
            if attacking:
                self.Attacking(True)
            else:
                self.Hostile(status)
        elif flag == state.threatAttackingMe:
            self.Attacking(status)
            if not status:
                hostile, = sm.StartService('state').GetStates(itemID, [state.threatTargetsMe])
                self.Hostile(hostile)
        elif flag == state.targeted:
            self.Targeted(status)
        elif flag == state.targeting:
            self.Targeting(status)
        elif flag == state.activeTarget:
            self.ActiveTarget(status)
        elif flag == state.flagWreckAlreadyOpened:
            self.UpdateIconColor()
        elif flag == state.flagWreckEmpty:
            self.UpdateIcon()
        else:
            broadcastDataName = fleetbr.flagToName.get(flag, None)
            if broadcastDataName is not None:
                self.UpdateFleetBroadcast()

    @telemetry.ZONE_METHOD
    def Hostile(self, state, *args, **kwds):
        """
        Displays or hides hostile (blinking yellow square) on
        overview entries
        """
        self.mainIcon.SetHostileState(state)

    def Attacking(self, state):
        """
        Displays or hides attacking indicator (blinking red square) on
        overview entries
        """
        self.mainIcon.SetAttackingState(state)

    @telemetry.ZONE_METHOD
    def Targeting(self, state):
        self.mainIcon.SetTargetingState(state)

    def Targeted(self, activestate, *args, **kwds):
        if activestate and self.targetingIndicator:
            self.targetingIndicator.Close()
            self.targetingIndicator = None
        self.mainIcon.SetTargetedByMeState(activestate)

    def ActiveTarget(self, activestate):
        if activestate and self.targetingIndicator:
            self.targetingIndicator.Close()
            self.targetingIndicator = None
        self.mainIcon.SetActiveTargetState(activestate)

    def Hilite(self, isHovered):
        if isHovered:
            self.ShowHilite()
        else:
            self.HideHilite()

    def Select(self, *args):
        pass

    def Deselect(self, *args):
        pass

    def ShowSelected(self, *args):
        """
        Shows this entry as selected, this should be triggered by the OnStateChange
        and has nothing to do with the scroll selection handling.
        When selection changes within the scroll fe. by UP/DOWN keys, OnScrollSelectionChange
        gets triggered and we delegate that message over to the stateSvc.
        """
        SE_BaseClassCore.Select(self, *args)

    def ShowDeselected(self, *args):
        """
        Shows this entry as deselected
        """
        SE_BaseClassCore.Deselect(self, *args)

    @telemetry.ZONE_METHOD
    def UpdateIcon(self, *args, **kwds):
        slimItem = self.sr.node.slimItem()
        ball = self.sr.node.ball()
        if slimItem and ball:
            self.mainIcon.UpdateSpaceObjectIcon(slimItem, ball)

    @telemetry.ZONE_METHOD
    def UpdateIconColor(self, icon = None):
        if self.destroyed:
            return
        if icon is None:
            icon = self.mainIcon.iconSprite
        node = self.sr.node
        slimItem = node.slimItem()
        if not slimItem:
            return
        if node.iconColor:
            iconColor = node.iconColor
        else:
            iconColor, colorSortValue = GetIconColor(slimItem, getSortValue=True)
            if node.sortIconIndex is not None:
                node.sortValue[node.sortIconIndex][1] = colorSortValue
            node.iconColor = iconColor
        r, g, b = iconColor
        if slimItem.groupID in (const.groupWreck, const.groupSpawnContainer) and sm.GetService('wreck').IsViewedWreck(slimItem.itemID):
            attenuation = 0.55
            r, g, b = r * attenuation, g * attenuation, b * attenuation
        icon.color = (r,
         g,
         b,
         1)

    def OnDblClick(self, *args):
        if uicore.cmd.IsCombatCommandLoaded():
            return
        slimItem = self.sr.node.slimItem()
        if slimItem:
            sm.GetService('menu').Activate(slimItem)

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        sm.GetService('state').SetState(self.sr.node.itemID, state.mouseOver, 1)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        sm.GetService('state').SetState(self.sr.node.itemID, state.mouseOver, 0)

    def LoadIconTooltipPanel(self, tooltipPanel, *args):
        if self.sr.node.slimItem:
            slimItem = self.sr.node.slimItem()
            ball = self.sr.node.ball()
            if not (slimItem and ball):
                return
            stateService = sm.GetService('state')
            tooltipPanel.LoadGeneric3ColumnTemplate()
            iconObj = SpaceObjectIcon()
            iconObj.UpdateSpaceObjectIcon(slimItem, ball)
            iconObj.UpdateSpaceObjectIconColor(slimItem, ball)
            iconObj.UpdateSpaceObjectState(slimItem, ball)
            iconObj.UpdateSpaceObjectFlagAndBackgroundColor(slimItem, ball)
            uthread.new(self.UpdateTooltipIconThread, iconObj)
            if iconObj.iconSprite.texturePath != INVISIBLE_SPACEOBJECT_ICON:
                tooltipPanel.AddCell(iconObj, cellPadding=(-5, 0, 8, 0))
            else:
                tooltipPanel.AddSpacer(width=1, height=1)
            tooltipPanel.AddLabelMedium(text=cfg.invgroups.Get(slimItem.groupID).name, align=uiconst.CENTERLEFT, bold=True, colSpan=tooltipPanel.columns - 1)
            attacking, hostile = stateService.GetStates(slimItem.itemID, [state.threatAttackingMe, state.threatTargetsMe])
            if attacking:
                tooltipPanel.AddCell()
                tooltipPanel.AddLabelMedium(text=localization.GetByLabel('Tooltips/Overview/HostileAction'), align=uiconst.CENTERLEFT, colSpan=tooltipPanel.columns - 1)
            elif hostile:
                tooltipPanel.AddCell()
                tooltipPanel.AddLabelMedium(text=localization.GetByLabel('Tooltips/Overview/TargetLock'), align=uiconst.CENTERLEFT, colSpan=tooltipPanel.columns - 1)
            iconHint = iconObj.iconHint
            if iconHint:
                tooltipPanel.AddCell()
                tooltipPanel.AddLabelMedium(text=iconHint, align=uiconst.CENTERLEFT, colSpan=tooltipPanel.columns - 1)
            flagStateHint = iconObj.flagStateHint
            if flagStateHint:
                tooltipPanel.AddCell()
                tooltipPanel.AddLabelMedium(text=flagStateHint, align=uiconst.CENTERLEFT, colSpan=tooltipPanel.columns - 1)
            colorHint = iconObj.iconColorHint
            if colorHint:
                tooltipPanel.AddCell()
                tooltipPanel.AddLabelMedium(text=colorHint, align=uiconst.CENTERLEFT, colSpan=tooltipPanel.columns - 1)

    def UpdateTooltipIconThread(self, iconObj):
        while not iconObj.destroyed:
            slimItem = self.sr.node.slimItem()
            ball = self.sr.node.ball()
            if not (slimItem and ball):
                break
            iconObj.UpdateSpaceObjectState(slimItem, ball)
            blue.synchro.Sleep(200)

    def GetIconTooltipPointer(self):
        currentColumns = self.sr.node.columns
        if currentColumns and currentColumns[0] == 'ICON':
            return uiconst.POINT_RIGHT_2

    def OnClick(self, *args):
        eve.Message('ListEntryClick')
        uicore.cmd.ExecuteCombatCommand(self.sr.node.itemID, uiconst.UI_CLICK)

    def OnMouseDown(self, *args):
        self.sr.node.scroll.SelectNode(self.sr.node)
        sm.GetService('menu').TryExpandActionMenu(self.itemID, self)

    def GetMenu(self, *args):
        return sm.GetService('menu').CelestialMenu(self.sr.node.itemID)

    def SetLabelAlpha(self, alpha):
        self.sr.label.color.a = alpha

    def UpdateTutorialHighlight(self, isActive):
        frame = getattr(self, 'tutorialHighlight', None)
        if isActive:
            from eve.client.script.ui.services.tutoriallib import TutorialColor
            if frame is None:
                self.tutorialHighlight = uiprimitives.Fill(parent=self, color=TutorialColor.HINT_FRAME, opacity=0.25)
        elif frame is not None:
            self.tutorialHighlight.Close()
            self.tutorialHighlight = None


class OverviewSettings(uicontrols.Window):
    __guid__ = 'form.OverviewSettings'
    __notifyevents__ = ['OnTacticalPresetChange',
     'OnOverviewPresetSaved',
     'OnRefreshOverviewTab',
     'OnReloadingOverviewProfile']
    default_windowID = 'overviewsettings'
    default_captionLabelPath = 'UI/Overview/OverviewSettings'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.overviewPresetSvc = sm.GetService('overviewPresetSvc')
        self.currentKey = None
        self.specialGroups = GetNPCGroups()
        self.scope = 'inflight'
        self.minWidth = 430
        self.SetWndIcon()
        self.SetHeaderIcon()
        settingsIcon = self.sr.headerIcon
        settingsIcon.state = uiconst.UI_NORMAL
        settingsIcon.GetMenu = self.GetPresetsMenu
        settingsIcon.expandOnLeft = 1
        settingsIcon.hint = ''
        self.sr.main = uiutil.GetChild(self, 'main')
        self.AddDraggableCont()
        self.settingCheckboxes = []
        self.statetop = statetop = uiprimitives.Container(name='statetop', parent=self.sr.main, align=uiconst.TOTOP)
        topText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/HintToggleDisplayState'), parent=statetop, align=uiconst.TOTOP, padding=(10, 3, 10, 0), state=uiconst.UI_NORMAL)
        topText.color.SetRGBA(1, 1, 1, 0.8)
        cb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/ApplyToShipsAndDronesOnly'), parent=statetop, configName='applyOnlyToShips', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('applyOnlyToShips', True), groupname=None, callback=self.CheckBoxChange, prefstype=('user', 'overview'), align=uiconst.TOTOP, padding=(9, 0, 0, 0))
        self.settingCheckboxes.append(cb)
        self.sr.applyOnlyToShips = cb
        cb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/UseSmallColortags'), parent=statetop, configName='useSmallColorTags', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('useSmallColorTags', False), groupname=None, callback=self.CheckBoxChange, prefstype=('user', 'overview'), align=uiconst.TOTOP, padding=(9, 0, 0, 0))
        self.settingCheckboxes.append(cb)
        self.sr.useSmallColorTags = cb
        self.sr.useSmallText = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/UseSmallFont'), parent=statetop, configName='useSmallText', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('useSmallText', False), callback=self.CheckBoxChange, prefstype=('user', 'overview'), align=uiconst.TOTOP, padding=(9, 0, 0, 0))
        self.settingCheckboxes.append(self.sr.useSmallText)
        statebtns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Commands/ResetAll'),
          self.ResetStateSettings,
          (),
          None]], parent=self.sr.main, idx=0)
        colLabel = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/HintToggleDisplayStateAndOrder'), parent=self.sr.main, align=uiconst.TOTOP, padding=(10, 3, 10, 2), state=uiconst.UI_DISABLED)
        colLabel.color.SetRGBA(1, 1, 1, 0.8)
        colbtns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Overview/ResetColumns'),
          self.ResetColumns,
          (),
          None]], parent=self.sr.main, idx=0)
        filtertop = uiprimitives.Container(name='filtertop', parent=self.sr.main, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=filtertop, align=uiconst.TOTOP, height=36, state=uiconst.UI_DISABLED)
        shiptop = uiprimitives.Container(name='filtertop', parent=self.sr.main, align=uiconst.TOTOP, height=57)
        presetMenu = uicontrols.MenuIcon()
        presetMenu.GetMenu = self.GetShipLabelMenu
        presetMenu.left = 6
        presetMenu.top = 10
        presetMenu.hint = ''
        shiptop.children.append(presetMenu)
        cb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/HideTickerIfInAlliance'), parent=shiptop, configName='hideCorpTicker', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('hideCorpTicker', False), groupname=None, callback=self.CheckBoxChange, prefstype=('user', 'overview'), align=uiconst.TOTOP, pos=(0, 30, 0, 16))
        cb.padLeft = 8
        self.settingCheckboxes.append(cb)
        self.sr.hideTickerIfInAlliance = cb
        historyCont = self.GetHistoryTab()
        misctop = uiprimitives.Container(name='misctop', parent=self.sr.main, align=uiconst.TOALL, left=const.defaultPadding, width=const.defaultPadding, top=const.defaultPadding)
        miscPadding = 4
        overviewBroadcastsToTop = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/MoveBroadcastersToTop'), parent=misctop, configName='overviewBroadcastsToTop', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('overviewBroadcastsToTop', False), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, padLeft=miscPadding)
        self.settingCheckboxes.append(overviewBroadcastsToTop)
        self.targetRangeSubCheckboxes = []
        btnCont = uiprimitives.Container(parent=misctop, height=20, align=uiconst.TOTOP)
        uicontrols.Button(parent=btnCont, label=localization.GetByLabel('UI/Overview/ResetOverview'), func=self.ResetAllOverviewSettings, left=miscPadding)
        uicontrols.EveHeaderSmall(text=localization.GetByLabel('UI/Overview/BracketAndTargetsHeader'), parent=misctop, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, top=14, padLeft=miscPadding + 2)
        dmgIndicatorCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/DisplayDamageIndications'), parent=misctop, configName='showBiggestDamageDealers', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('showBiggestDamageDealers', True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, callback=self.MiscCheckboxChange, padLeft=miscPadding)
        self.settingCheckboxes.append(dmgIndicatorCb)
        moduleHairlineCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/DisplayModuleLinks'), parent=misctop, configName='showModuleHairlines', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('showModuleHairlines', True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, padLeft=miscPadding)
        self.settingCheckboxes.append(moduleHairlineCb)
        targetCrosshairCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/ShowTargettingCrosshair'), parent=misctop, configName='targetCrosshair', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('targetCrosshair', True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, callback=self.MiscCheckboxChange, padLeft=miscPadding)
        self.settingCheckboxes.append(targetCrosshairCb)
        targetRangeCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/DisplayRangeBrackets'), parent=misctop, configName='showInTargetRange', retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName('showInTargetRange', True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, callback=self.MiscCheckboxChange, padLeft=miscPadding)
        self.settingCheckboxes.append(targetRangeCb)
        configName = 'showCategoryInTargetRange_%s' % const.categoryShip
        targetRangeShipsCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/Ships'), parent=misctop, configName=configName, retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName(configName, True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, callback=self.MiscCheckboxChange, padLeft=3 * miscPadding)
        self.settingCheckboxes.append(targetRangeShipsCb)
        self.targetRangeSubCheckboxes.append(targetRangeShipsCb)
        configName = 'showCategoryInTargetRange_%s' % const.categoryEntity
        targetRangeNPCsCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/NPCs'), parent=misctop, configName=configName, retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName(configName, True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, callback=self.MiscCheckboxChange, padLeft=3 * miscPadding)
        self.settingCheckboxes.append(targetRangeNPCsCb)
        self.targetRangeSubCheckboxes.append(targetRangeNPCsCb)
        configName = 'showCategoryInTargetRange_%s' % const.categoryDrone
        targetRangeDronesCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/Overview/Drones'), parent=misctop, configName=configName, retval=None, checked=self.overviewPresetSvc.GetSettingValueOrDefaultFromName(configName, True), groupname=None, prefstype=('user', 'overview'), align=uiconst.TOTOP, callback=self.MiscCheckboxChange, padLeft=3 * miscPadding)
        parentGrid = LayoutGrid(parent=misctop, columns=1, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP, top=10)
        uicontrols.Button(parent=parentGrid, label=localization.GetByLabel('UI/Overview/ImportOverviewSettings'), func=sm.GetService('tactical').ImportOverviewSettings, left=miscPadding)
        uicontrols.Button(parent=parentGrid, label=localization.GetByLabel('UI/Commands/ExportOverviewSettings'), func=sm.GetService('tactical').ExportOverviewSettings, left=miscPadding, top=4)
        self.settingCheckboxes.append(targetRangeDronesCb)
        self.targetRangeSubCheckboxes.append(targetRangeDronesCb)
        self.ChangeStateOfSubCheckboxes(targetRangeCb)
        overviewtabtop = self.AddTabForOverviewProfile()
        btns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Common/SelectAll'),
          self.SelectAll,
          (),
          None], [localization.GetByLabel('UI/Common/DeselectAll'),
          self.DeselectAll,
          (),
          None]], parent=self.sr.main, idx=0)
        parentGrid = LayoutGrid(parent=filtertop, columns=2, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPLEFT, left=10, top=3)
        l = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/CurrentPreset'))
        l.color.SetRGBA(1, 1, 1, 0.8)
        parentGrid.AddCell(cellObject=l, colSpan=2)
        currentPreset = self.overviewPresetSvc.GetActiveOverviewPresetName()
        currentPresetName = self.overviewPresetSvc.GetPresetDisplayName(currentPreset)
        self.sr.presetText = uicontrols.EveLabelSmall(text=currentPresetName, align=uiconst.CENTERLEFT)
        parentGrid.AddCell(cellObject=self.sr.presetText)
        self.savePresetButton = uicontrols.Button(label=localization.GetByLabel('UI/Common/Buttons/Save'), func=sm.GetService('overviewPresetSvc').SavePreset, align=uiconst.BOTTOMLEFT)
        parentGrid.AddCell(cellObject=self.savePresetButton, cellPadding=(20, 0, 0, 0))
        parentGrid.RefreshGridLayout()
        top = parentGrid.height + parentGrid.top
        self.groupQuickFilterCont = Container(parent=self.sr.main, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP)
        self.groupQuickFilter = uicls.QuickFilterEdit(parent=self.groupQuickFilterCont, pos=(5, 0, 150, 0), align=uiconst.TOPRIGHT)
        self.groupQuickFilter.ReloadFunction = self.LoadFilteredTypes
        self.groupQuickFilterCont.height = self.groupQuickFilter.height
        self.sr.scroll = uicontrols.Scroll(name='scroll', parent=self.sr.main, padding=const.defaultPadding)
        self.sr.scroll.multiSelect = 0
        self.sr.scroll.SelectAll = self.SelectAll
        self.sr.scroll.sr.content.OnDropData = self.MoveStuff
        self.Maximize()
        self.state = uiconst.UI_NORMAL
        stateTabs = [[localization.GetByLabel('UI/Overview/Colortag'),
          statebtns,
          self,
          'flag'], [localization.GetByLabel('UI/Overview/Background'),
          statebtns,
          self,
          'background']]
        self.sr.statetabs = uicontrols.TabGroup(name='overviewstatesTab', height=18, align=uiconst.TOBOTTOM, parent=statetop, idx=0, tabs=stateTabs, groupID='overviewstatesTab', autoselecttab=0)
        self.statesPanel = StatesPanel(parent=self.sr.main, onChangeFunc=self.OnFilteredStatesChange)
        filterTabs = [[localization.GetByLabel('UI/Generic/Types'),
          btns,
          self,
          'filtertypes'], [localization.GetByLabel('UI/Generic/States'),
          self.statesPanel,
          self,
          'filterstates']]
        self.sr.filtertabs = uicontrols.TabGroup(name='overviewstatesTab', height=18, align=uiconst.TOBOTTOM, parent=filtertop, tabs=filterTabs, groupID='overviewfilterTab', autoselecttab=0)
        filtertop.height = top + self.sr.filtertabs.height
        settingsTabs = [[localization.GetByLabel('UI/Overview/OverviewTabs'),
          [],
          self,
          'overviewTabs',
          overviewtabtop],
         [uiutil.FixedTabName('UI/Overview/TabPresetsTabName'),
          btns,
          self,
          'filters',
          filtertop],
         [uiutil.FixedTabName('UI/Generic/Appearance'),
          statebtns,
          self,
          'appearance',
          statetop],
         [uiutil.FixedTabName('UI/Generic/Columns'),
          colbtns,
          self,
          'columns',
          colLabel],
         [uiutil.FixedTabName('UI/Common/ItemTypes/Ships'),
          [],
          self,
          'ships',
          shiptop],
         [uiutil.FixedTabName('UI/Generic/Misc'),
          [],
          self,
          'misc',
          misctop],
         [uiutil.FixedTabName('UI/Overview/ProfileHistory'),
          [],
          self,
          'history',
          historyCont]]
        self.sr.tabs = uicontrols.TabGroup(name='overviewsettingsTab', height=18, align=uiconst.TOTOP, parent=self.sr.main, idx=0, tabs=settingsTabs, groupID='overviewsettingsTab', UIIDPrefix='overviewSettingsTab')
        self.sr.statetabs.align = uiconst.TOBOTTOM
        self.minHeight = top + self.sr.tabs.height + const.defaultPadding * 2 + self.sr.topParent.height + 10
        self.minHeight += sum([ c.height for c in misctop.children ])
        self.ResetMinSize()
        self.UpdateStateTopHeight()

    def GetHistoryTab(self):
        historyCont = uiprimitives.Container(name='historyCont', parent=self.sr.main, align=uiconst.TOALL)
        self.restoreCont = uicontrols.ContainerAutoSize(name='historyCont', parent=historyCont, align=uiconst.TOBOTTOM, left=const.defaultPadding, width=const.defaultPadding, alignMode=uiconst.TOTOP)
        Line(parent=historyCont, align=uiconst.TOBOTTOM, color=(1, 1, 1, 0.1))
        restoreButton = uicontrols.Button(parent=self.restoreCont, label=localization.GetByLabel('UI/Overview/RestoreProfile'), func=self.RestoreOldOverview, left=10, align=uiconst.CENTERRIGHT)
        restoreLabel = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/AutomaticallyStoredOverviewHeader'), parent=self.restoreCont, align=uiconst.TOTOP, padding=(10,
         3,
         restoreButton.width + 10,
         0), state=uiconst.UI_DISABLED)
        self.restoreOverviewNameLabel = uicontrols.EveLabelSmall(text='', parent=self.restoreCont, align=uiconst.TOTOP, padding=(10,
         0,
         restoreButton.width + 10,
         2), state=uiconst.UI_DISABLED)
        historyText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/HistoryText'), parent=historyCont, align=uiconst.TOTOP, padding=(10, 3, 10, 0), state=uiconst.UI_DISABLED)
        historyText.color.SetRGBA(1, 1, 1, 0.8)
        self.historyEdit = EditPlainText(setvalue='', parent=historyCont, align=uiconst.TOALL, readonly=True, pos=(10, -2, 10, 0))
        self.historyEdit.HideBackground()
        self.historyEdit.RemoveActiveFrame()
        return historyCont

    def RestoreOldOverview(self, *args):
        restoreData = settings.user.overview.Get('restoreData', {})
        if not restoreData:
            return
        data = restoreData['data']
        overviewName = restoreData['name']
        self.overviewPresetSvc.LoadSettingsFromDict(data, overviewName)
        settings.user.overview.Set('restoreData', {})
        self.LoadRestoreData()

    def AddDraggableCont(self):
        currentText = self.overviewPresetSvc.GetOverviewName()
        defaultText = localization.GetByLabel('UI/Overview/DefaultOverviewName', charID=session.charid)
        configName = 'overviewProfileName'
        shareContainer = DraggableShareContainer(parent=self.sr.topParent, currentText=currentText, defaultText=defaultText, configName=configName, getDragDataFunc=self.overviewPresetSvc.GetShareData, hintText=localization.GetByLabel('UI/Overview/SharableOverviewIconHint'))
        self.overviewNameEdit = shareContainer.sharedNameLabel
        self.SetTopparentHeight(self.overviewNameEdit.height + 10)

    def RefreshOverviewName(self):
        currentText = self.overviewPresetSvc.GetOverviewName()
        self.overviewNameEdit.SetValue(currentText)
        self.overviewNameEdit.OnEditFieldChanged()

    def AddTabForOverviewProfile(self):
        overviewtabtop = uiprimitives.Container(name='overviewtabtop', parent=self.sr.main, align=uiconst.TOALL, pos=(4, 0, 0, 0))
        parentGrid = LayoutGrid(parent=overviewtabtop, columns=3, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPLEFT, left=10, top=0, cellSpacing=(15, 8))
        bracketOptions, overviewOptions = self.GetBracketAndOverviewOptions()
        for i in xrange(parentGrid.columns):
            container = Container(pos=(0, 0, 115, 0), name='spacer', align=uiconst.TOPLEFT)
            parentGrid.AddCell(cellObject=container)

        nameText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/TabName'), state=uiconst.UI_DISABLED)
        nameText.color.SetRGBA(1, 1, 1, 0.8)
        nameTextWidth = max(nameText.textwidth, 120)
        parentGrid.AddCell(cellObject=nameText)
        overviewText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/OverviewPreset'), state=uiconst.UI_DISABLED)
        overviewText.color.SetRGBA(1, 1, 1, 0.8)
        widthOverview = max(overviewText.textwidth, 120)
        parentGrid.AddCell(cellObject=overviewText)
        bracketText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Overview/BracketPreset'), state=uiconst.UI_DISABLED)
        bracketText.color.SetRGBA(1, 1, 1, 0.8)
        widthBracket = max(bracketText.textwidth, 120)
        parentGrid.AddCell(cellObject=bracketText)
        self.tabedit = {}
        self.comboTabOverview = {}
        self.comboTabBracket = {}
        tabsettings = self.overviewPresetSvc.GetTabSettingsForOverview()
        for i in range(MAX_TAB_NUM):
            comboTabBracketVal, comboTabOverviewVal, newOverviewOptions, tabeditVal = self.GetTabInfoForCombos(i, overviewOptions, tabsettings)
            tabedit = uicontrols.SinglelineEdit(name='edit' + str(i), align=uiconst.TOPLEFT, pos=(0,
             0,
             nameTextWidth,
             0), setvalue=tabeditVal, OnFocusLost=self.ChangeTabText, OnReturn=self.UpdateOverviewTab)
            tabedit.originalValue = tabeditVal
            parentGrid.AddCell(cellObject=tabedit)
            self.tabedit[i] = tabedit
            comboTabOverview = uicontrols.Combo(label='', options=newOverviewOptions or overviewOptions, name='comboTabOverview', select=comboTabOverviewVal, align=uiconst.TOPLEFT, width=widthOverview, callback=self.OnProfileInTabChanged)
            self.comboTabOverview[i] = comboTabOverview
            parentGrid.AddCell(cellObject=comboTabOverview)
            comboTabBracket = uicontrols.Combo(label='', options=bracketOptions, name='comboTabBracket', select=comboTabBracketVal, width=widthBracket, align=uiconst.TOPLEFT, callback=self.OnProfileInTabChanged)
            self.comboTabBracket[i] = comboTabBracket
            parentGrid.AddCell(cellObject=comboTabBracket)

        return overviewtabtop

    def GetTabInfoForCombos(self, i, overviewOptions, tabsettings):
        tabeditVal = ''
        comboTabOverviewVal = None
        comboTabBracketVal = None
        newOverviewOptions = None
        if i in tabsettings:
            tabeditVal = tabsettings[i].get('name', None)
            comboTabBracketVal = tabsettings[i].get('bracket', None) or None
            comboTabOverviewVal = tabsettings[i].get('overview', None)
            if self.overviewPresetSvc.IsTempName(comboTabOverviewVal):
                displayName = self.overviewPresetSvc.GetPresetDisplayName(comboTabOverviewVal)
                newOverviewOptions = overviewOptions[:]
                newOverviewOptions.append((displayName, comboTabOverviewVal))
        return (comboTabBracketVal,
         comboTabOverviewVal,
         newOverviewOptions,
         tabeditVal)

    def OnProfileInTabChanged(self, *args):
        self.UpdateOverviewTab()

    def ChangeTabText(self, editField):
        currentValue = editField.GetValue()
        if currentValue != editField.originalValue:
            self.UpdateOverviewTab()

    def GetBracketAndOverviewOptions(self, includeEmpty = True):
        overviewOptions = []
        bracketOptions = []
        if includeEmpty:
            overviewOptions = [(' ', [' ', None])]
            bracketOptions = [('  ', [localization.GetByLabel('UI/Overview/ShowAllBrackets'), None])]
        presets = self.overviewPresetSvc.GetAllPresets()
        bothOptions = []
        for label in presets.keys():
            if self.overviewPresetSvc.IsTempName(label):
                continue
            elif label == 'ccp_notsaved':
                bothOptions.append(('   ', [localization.GetByLabel('UI/Overview/NotSaved'), label]))
            else:
                overviewName = self.overviewPresetSvc.GetDefaultOverviewName(label)
                lowerLabel = label.lower()
                if overviewName is not None:
                    bothOptions.append((lowerLabel, [overviewName, label]))
                else:
                    bothOptions.append((lowerLabel, [label, label]))

        overviewOptions = [ x[1] for x in localization.util.Sort(overviewOptions + bothOptions, key=operator.itemgetter(0)) ]
        bracketOptions = [ x[1] for x in localization.util.Sort(bracketOptions + bothOptions, key=operator.itemgetter(0)) ]
        return (bracketOptions, overviewOptions)

    def UpdateStateTopHeight(self):
        self.statetop.height = sum((c.height for c in self.statetop.children))

    def MoveStuff(self, dragObj, entries, idx = -1, *args):
        if self.currentKey is None:
            return
        if self.currentKey == 'columns':
            self.MoveColumn(idx)
        elif self.currentKey in ('flag', 'background'):
            self.Move(idx)
        elif self.currentKey == 'ships':
            self.MoveShipLabel(idx)

    def OnTacticalPresetChange(self, label, preset):
        presetName = self.overviewPresetSvc.GetPresetDisplayName(label)
        self.sr.presetText.text = presetName
        self.RefreshOverviewTab()
        if uiutil.IsVisible(self.sr.filtertabs) and self.sr.filtertabs.GetSelectedArgs() in ('filtertypes', 'filterstates'):
            self.sr.filtertabs.ReloadVisible()

    def OnOverviewPresetSaved(self):
        overviewOptions = [(' ', [' ', None])]
        bracketOptions = [(' ', [localization.GetByLabel('UI/Overview/ShowAllBrackets'), None])]
        tabsettings = self.overviewPresetSvc.GetTabSettingsForOverview()
        presets = self.overviewPresetSvc.GetAllPresets()
        for label in presets.keys():
            if label == 'ccp_notsaved':
                overviewOptions.append(('  ', [localization.GetByLabel('UI/Overview/NotSaved'), label]))
                bracketOptions.append(('  ', [localization.GetByLabel('UI/Overview/NotSaved'), label]))
            else:
                presetName = self.overviewPresetSvc.GetDefaultOverviewName(label)
                lowerLabel = label.lower()
                if presetName is not None:
                    overviewOptions.append((lowerLabel, [presetName, label]))
                    bracketOptions.append((lowerLabel, [presetName, label]))
                else:
                    overviewOptions.append((lowerLabel, [label, label]))
                    bracketOptions.append((lowerLabel, [label, label]))

        overviewOptions = [ x[1] for x in localization.util.Sort(overviewOptions, key=lambda x: x[0]) ]
        bracketOptions = [ x[1] for x in localization.util.Sort(bracketOptions, key=lambda x: x[0]) ]
        for i in range(MAX_TAB_NUM):
            comboTabOverviewVal = None
            comboTabBracketVal = None
            editFieldText = None
            if tabsettings.has_key(i):
                comboTabOverviewVal = tabsettings[i].get('overview', None)
                comboTabBracketVal = tabsettings[i].get('bracket', None)
                editFieldText = tabsettings[i].get('name', None)
            self.comboTabOverview[i].LoadOptions(overviewOptions, comboTabOverviewVal)
            self.comboTabBracket[i].LoadOptions(bracketOptions, comboTabBracketVal)
            if editFieldText:
                self.tabedit[i].SetText(editFieldText)
                self.tabedit[i].originalValue = editFieldText

    def ExportSettings(self, *args):
        pass

    def ResetAllOverviewSettings(self, *args):
        if eve.Message('ResetAllOverviewSettings', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        settings.user.overview.Set('presetHistoryKeys', {})
        self.overviewPresetSvc.ResetPresetsToDefault()
        self.overviewPresetSvc.ResetActivePresets()
        oldTabs = self.overviewPresetSvc.GetTabSettingsForOverview()
        values = settings.user.overview.GetValues()
        keys = values.keys()
        for key in keys:
            settings.user.overview.Delete(key)

        overviewWindow = OverView.GetIfOpen()
        if overviewWindow:
            newTabs = self.overviewPresetSvc.GetTabSettingsForOverview()
            overviewWindow.OnOverviewTabChanged(newTabs, oldTabs)
        stateSvc = sm.StartService('state')
        stateSvc.SetDefaultShipLabel('default')
        stateSvc.ResetColors()
        default = self.overviewPresetSvc.GetDefaultOverviewGroups('default')
        settings.user.overview.Set('overviewProfilePresets', {'default': default})
        self.CloseByUser()

    def DoFontChange(self):
        self.ResetMinSize()

    def ResetMinSize(self):
        maxBtnWidth = max([ uiutil.GetChild(wnd, 'btns').width for wnd in self.sr.main.children if wnd.name == 'btnsmainparent' ])
        margin = 12
        minWidth = max(self.minWidth, maxBtnWidth + margin * 2)
        self.SetMinSize((minWidth, self.minHeight))

    ResetMinSize = uiutil.ParanoidDecoMethod(ResetMinSize, ('sr', 'main'))

    def SelectAll(self, *args):
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        groups = []
        for entry in self.sr.scroll.GetNodes():
            if entry.__guid__ == 'listentry.Checkbox':
                entry.checked = 1
                if entry.panel:
                    entry.panel.Load(entry)
            if entry.__guid__ == 'listentry.Group':
                for item in entry.groupItems:
                    if type(item[0]) == list:
                        groups += item[0]
                    else:
                        groups.append(item[0])

        if groups:
            self.overviewPresetSvc.SetSettings('groups', groups)

    def DeselectAll(self, *args):
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        for entry in self.sr.scroll.GetNodes():
            if entry.__guid__ == 'listentry.Checkbox':
                entry.checked = 0
                if entry.panel:
                    entry.panel.Load(entry)

        self.overviewPresetSvc.SetSettings('groups', [])

    def GetPresetsMenu(self):
        p = self.overviewPresetSvc.GetAllPresets().keys()
        p.sort()
        for name in self.overviewPresetSvc.GetDefaultOverviewNameList():
            if name in p:
                p.remove(name)

        m = []
        m += [None, (uiutil.MenuLabel('UI/Commands/ExportOverviewSettings'), sm.GetService('tactical').ExportOverviewSettings), (uiutil.MenuLabel('UI/Overview/ImportOverviewSettings'), sm.GetService('tactical').ImportOverviewSettings)]
        dm = []
        for label in p:
            if self.overviewPresetSvc.IsTempName(label):
                continue
            dm.append((label.lower(), (label, self.overviewPresetSvc.DeletePreset, (label,))))

        if dm:
            m.append(None)
            dm = uiutil.SortListOfTuples(dm)
            m.append((uiutil.MenuLabel('UI/Common/Delete'), dm))
        return m

    def GetShipLabelMenu(self):
        return [(localization.GetByLabel('UI/Overview/ShipLabelFormatPilotCC'), self.SetDefaultShipLabel, ('default',)), (localization.GetByLabel('UI/Overview/ShipLabelFormatPilotCCAA'), self.SetDefaultShipLabel, ('ally',)), (localization.GetByLabel('UI/Overview/ShipLabelFormatCCPilotAA'), self.SetDefaultShipLabel, ('corpally',))]

    def SetDefaultShipLabel(self, setting):
        sm.GetService('state').SetDefaultShipLabel(setting)
        self.LoadShips()

    def Load(self, key):
        if self.currentKey is None or self.currentKey != key:
            self.cachedScrollPos = 0
        self.currentKey = key
        self.sr.scroll.state = uiconst.UI_NORMAL
        self.statesPanel.display = False
        self.groupQuickFilterCont.display = False
        if key == 'filtertypes':
            self.groupQuickFilterCont.display = True
            self.LoadTypes()
        elif key == 'filterstates':
            self.statesPanel.display = True
            self.sr.scroll.state = uiconst.UI_HIDDEN
            self.statesPanel.Load()
        elif key == 'columns':
            self.LoadColumns()
        elif key == 'appearance':
            self.sr.statetabs.AutoSelect()
        elif key == 'filters':
            self.sr.filtertabs.AutoSelect()
        elif key == 'ships':
            self.LoadShips()
        elif key == 'misc':
            self.sr.scroll.state = uiconst.UI_HIDDEN
        elif key == 'overviewTabs':
            self.sr.scroll.state = uiconst.UI_HIDDEN
        elif key == 'history':
            self.sr.scroll.state = uiconst.UI_HIDDEN
            self.LoadHistory()
        else:
            self.LoadFlags()

    def LoadFlags(self, selected = None):
        where = self.sr.statetabs.GetSelectedArgs()
        flagOrder = sm.GetService('state').GetStateOrder(where)
        scrolllist = []
        i = 0
        for flag in flagOrder:
            props = sm.GetService('state').GetStateProps(flag)
            data = KeyVal()
            data.label = props.text
            data.props = props
            data.checked = sm.GetService('state').GetStateState(where, flag)
            data.cfgname = where
            data.retval = flag
            data.flag = flag
            data.canDrag = True
            data.hint = props.hint
            data.OnChange = self.CheckBoxChange
            data.isSelected = selected == i
            scrolllist.append(listentry.Get('FlagEntry', data=data))
            i += 1

        self.sr.scroll.Load(contentList=scrolllist, scrollTo=getattr(self, 'cachedScrollPos', 0.0))

    def LoadShips(self, selected = None):
        shipLabels = sm.GetService('state').GetShipLabels()
        allLabels = sm.GetService('state').GetAllShipLabels()
        corpTickerHidden = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('hideCorpTicker', False)
        self.sr.hideTickerIfInAlliance.SetChecked(corpTickerHidden)
        hints = {None: '',
         'corporation': localization.GetByLabel('UI/Common/CorpTicker'),
         'alliance': localization.GetByLabel('UI/Shared/AllianceTicker'),
         'pilot name': localization.GetByLabel('UI/Common/PilotName'),
         'ship name': localization.GetByLabel('UI/Common/ShipName'),
         'ship type': localization.GetByLabel('UI/Common/ShipType')}
        comments = {None: localization.GetByLabel('UI/Overview/AdditionalTextForCorpTicker'),
         'corporation': localization.GetByLabel('UI/Overview/OnlyShownForPlayerCorps'),
         'alliance': localization.GetByLabel('UI/Overview/OnlyShownWhenAvailable')}
        newlabels = [ label for label in allLabels if label['type'] not in [ alabel['type'] for alabel in shipLabels ] ]
        shipLabels += newlabels
        scrolllist = []
        for i, flag in enumerate(shipLabels):
            data = KeyVal()
            data.label = hints[flag['type']]
            data.checked = flag['state']
            data.cfgname = 'shiplabels'
            data.retval = flag
            data.flag = flag
            data.canDrag = True
            data.hint = hints[flag['type']]
            data.comment = comments.get(flag['type'], '')
            data.OnChange = self.CheckBoxChange
            data.isSelected = selected == i
            scrolllist.append(listentry.Get('ShipEntry', data=data))

        self.sr.scroll.Load(contentList=scrolllist, scrollTo=getattr(self, 'cachedScrollPos', 0.0))
        maxLeft = 140
        for shipEntry in self.sr.scroll.GetNodes():
            if shipEntry.panel:
                postLeft = shipEntry.panel.sr.label.left + shipEntry.panel.sr.label.textwidth + 4
                maxLeft = max(maxLeft, postLeft)

        for shipEntry in self.sr.scroll.GetNodes():
            if shipEntry.panel:
                shipEntry.panel.postCont.left = maxLeft

    def Move(self, idx = None, *args):
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        selected = self.sr.scroll.GetSelected()
        if selected:
            selected = selected[0]
            if idx is not None:
                if idx != selected.idx:
                    if selected.idx < idx:
                        newIdx = idx - 1
                    else:
                        newIdx = idx
                else:
                    return
            else:
                newIdx = max(0, selected.idx - 1)
            sm.GetService('state').ChangeStateOrder(self.GetWhere(), selected.flag, newIdx)
            self.LoadFlags(newIdx)

    def GetWhere(self):
        where = self.sr.statetabs.GetSelectedArgs()
        return where

    def ResetStateSettings(self, *args):
        where = self.sr.statetabs.GetSelectedArgs()
        settings.user.overview.Set('flagOrder', None)
        settings.user.overview.Set('iconOrder', None)
        settings.user.overview.Set('backgroundOrder', None)
        settings.user.overview.Set('flagStates', None)
        settings.user.overview.Set('iconStates', None)
        settings.user.overview.Set('backgroundStates', None)
        settings.user.overview.Set('stateColors', {})
        sm.GetService('state').InitColors(1)
        settings.user.overview.Set('stateBlinks', {})
        defaultApplyOnlyToShips = sm.GetService('overviewPresetSvc').GetDefaultSettingValueFromName('applyOnlyToShips', True)
        settings.user.overview.Set('applyOnlyToShips', defaultApplyOnlyToShips)
        self.sr.applyOnlyToShips.SetChecked(defaultApplyOnlyToShips, 0)
        defaultUseSmallColorTags = sm.GetService('overviewPresetSvc').GetDefaultSettingValueFromName('useSmallColorTags', False)
        settings.user.overview.Set('useSmallColorTags', defaultUseSmallColorTags)
        self.sr.useSmallColorTags.SetChecked(defaultUseSmallColorTags, 0)
        self.LoadFlags()
        sm.GetService('state').NotifyOnStateSetupChance('reset')

    def LoadColumns(self, selected = None):
        userSet = sm.GetService('tactical').GetColumns()
        userSetOrder = sm.GetService('tactical').GetColumnOrder()
        missingColumns = [ col for col in sm.GetService('tactical').GetAllColumns() if col not in userSetOrder ]
        userSetOrder += missingColumns
        i = 0
        scrolllist = []
        for columnID in userSetOrder:
            data = KeyVal()
            data.label = sm.GetService('tactical').GetColumnLabel(columnID)
            data.checked = columnID in userSet
            data.cfgname = 'columns'
            data.retval = columnID
            data.canDrag = True
            data.isSelected = selected == i
            data.OnChange = self.CheckBoxChange
            scrolllist.append(listentry.Get('ColumnEntry', data=data))
            i += 1

        self.sr.scroll.Load(contentList=scrolllist, scrollTo=getattr(self, 'cachedScrollPos', 0.0))

    def LoadFilteredTypes(self, *args):
        self.LoadTypes()

    def LoadTypes(self):
        filterText = self.groupQuickFilter.GetValue()
        categoryList = self.GetListOfCategories(filterText=filterText.lower())
        sortCat = categoryList.keys()
        sortCat.sort()
        presetName = self.overviewPresetSvc.GetActiveOverviewPresetName()
        scrolllist = []
        userSettings = self.overviewPresetSvc.GetPresetGroupsFromKey(presetName)
        for catName in sortCat:
            checkedCounter = 0
            groupItems = categoryList[catName]
            for groupID, name in groupItems:
                if isinstance(groupID, list):
                    for each in groupID:
                        if each in userSettings:
                            checkedCounter += 1
                            break

                else:
                    checkedCounter += int(groupID in userSettings)

            posttext = '[%s/%s]' % (checkedCounter, len(groupItems))
            data = {'GetSubContent': self.GetCatSubContent,
             'label': catName,
             'MenuFunction': self.GetSubFolderMenu,
             'id': ('GroupSel', catName),
             'groupItems': groupItems,
             'showlen': 0,
             'sublevel': 0,
             'state': 'locked',
             'presetName': presetName,
             'showicon': 'hide',
             'posttext': posttext}
            scrolllist.append(listentry.Get('Group', data))

        self.sr.scroll.Load(contentList=scrolllist, scrolltotop=0, scrollTo=getattr(self, 'cachedScrollPos', 0.0))

    def GetListOfCategories(self, filterText = ''):
        categoryList = {}
        for groupID, name in sm.GetService('tactical').GetAvailableGroups():
            if filterText and name.lower().find(filterText) < 0:
                continue
            for cat, groupdict in self.specialGroups.iteritems():
                for group, groupIDs in groupdict.iteritems():
                    if groupID in groupIDs:
                        catName = cat
                        groupID = groupIDs
                        name = group
                        break
                else:
                    continue

                break
            else:
                catName = cfg.invcategories.Get(cfg.invgroups.Get(groupID).categoryID).name

            if catName not in categoryList:
                categoryList[catName] = [(groupID, name)]
            elif (groupID, name) not in categoryList[catName]:
                categoryList[catName].append((groupID, name))

        return categoryList

    def GetSubFolderMenu(self, node):
        m = [None, (localization.GetByLabel('UI/Common/SelectAll'), self.SelectGroup, (node, True)), (localization.GetByLabel('UI/Common/DeselectAll'), self.SelectGroup, (node, False))]
        return m

    def SelectGroup(self, node, isSelect):
        groups = []
        for entry in node.groupItems:
            if type(entry[0]) == list:
                for entry1 in entry[0]:
                    groups.append(entry1)

            else:
                groups.append(entry[0])

        chageList = [('groups', groups, isSelect)]
        sm.StartService('overviewPresetSvc').ChangeSettings(changeList=chageList)

    def GetCatSubContent(self, nodedata, newitems = 0):
        presetName = nodedata.presetName
        userSettings = self.overviewPresetSvc.GetPresetGroupsFromKey(presetName)
        scrolllist = []
        for groupID, name in nodedata.groupItems:
            if type(groupID) == list:
                for each in groupID:
                    if each in userSettings:
                        checked = 1
                        break
                else:
                    checked = 0

            else:
                name = cfg.invgroups.Get(groupID).groupName
                checked = groupID in userSettings
            data = KeyVal()
            data.label = name
            data.sublevel = 1
            data.checked = checked
            data.cfgname = 'groups'
            data.retval = groupID
            data.OnChange = self.CheckBoxChange
            scrolllist.append(listentry.Get('Checkbox', data=data))

        return scrolllist

    def LoadHistory(self):
        presetHistoryKeys = settings.user.overview.Get('presetHistoryKeys', {})
        textList = []
        for eachKey, eachValue in presetHistoryKeys.iteritems():
            overviewName = eachValue.get('overviewName', 'overview_name')
            presetKey = eachValue.get('presetKey')
            timestamp = eachValue.get('timestamp')
            overviewLink = '<a href="overviewPreset:%s//%s">%s</a>' % (presetKey[0], presetKey[1], overviewName)
            text = localization.GetByLabel('UI/Overview/ProfileLinkWithTimestamp', profileLink=overviewLink, timestamp=util.FmtDate(timestamp))
            textList.append((timestamp, text))

        textList = uiutil.SortListOfTuples(textList, reverse=True)
        allText = '<br>'.join(textList[:15])
        self.historyEdit.SetValue(allText)
        self.LoadRestoreData()

    def LoadRestoreData(self):
        restoreData = settings.user.overview.Get('restoreData', {})
        if not restoreData:
            self.restoreCont.display = False
            return
        self.restoreCont.display = True
        overviewName = restoreData['name']
        timestamp = restoreData['timestamp']
        self.restoreOverviewNameLabel.text = localization.GetByLabel('UI/Overview/StoredOverviewBasedOn', overviewName=overviewName, timestamp=util.FmtDate(timestamp))

    def MoveColumn(self, idx = None, *args):
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        selected = self.sr.scroll.GetSelected()
        if selected:
            selected = selected[0]
            if idx is not None:
                if idx != selected.idx:
                    if selected.idx < idx:
                        newIdx = idx - 1
                    else:
                        newIdx = idx
                else:
                    return
            else:
                newIdx = max(0, selected.idx - 1)
            column = selected.retval
            current = sm.GetService('tactical').GetColumnOrder()[:]
            while column in current:
                current.remove(column)

            if idx == -1:
                idx = len(current)
            current.insert(idx, column)
            settings.user.overview.Set('overviewColumnOrder', current)
            self.LoadColumns(newIdx)
            self.DoFullOverviewReload()

    def ResetColumns(self, *args):
        settings.user.overview.Set('overviewColumnOrder', None)
        settings.user.overview.Set('overviewColumns', None)
        self.LoadColumns()
        sm.GetService('state').NotifyOnStateSetupChance('column reset')

    def DoFullOverviewReload(self):
        overview = OverView.GetIfOpen()
        if overview:
            overview.FullReload()

    def CheckBoxChange(self, checkbox):
        if self and not self.destroyed:
            self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        if checkbox.data.has_key('config'):
            config = checkbox.data['config']
            if config == 'applyOnlyToShips':
                sm.GetService('tactical').SetNPCGroups()
                sm.GetService('state').InitFilter()
                sm.GetService('state').NotifyOnStateSetupChance('filter')
                self.DoFullOverviewReload()
                sm.GetService('bracket').Reload()
            elif config == 'hideCorpTicker':
                sm.GetService('bracket').UpdateLabels()
            elif config == 'useSmallColorTags':
                sm.GetService('state').NotifyOnStateSetupChance('filter')
            elif config == 'useSmallText':
                if checkbox.checked:
                    settings.user.overview.Set('useSmallText', 1)
                else:
                    settings.user.overview.Set('useSmallText', 0)
                self.DoFullOverviewReload()
        if checkbox.data.has_key('key'):
            key = checkbox.data['key']
            if key == 'groups':
                changeList = [(key, checkbox.data['retval'], checkbox.checked)]
                self.overviewPresetSvc.ChangeSettings(changeList=changeList)
            elif key == 'columns':
                checked = checkbox.checked
                column = checkbox.data['retval']
                current = sm.GetService('tactical').GetColumns()[:]
                while column in current:
                    current.remove(column)

                if checked:
                    current.append(column)
                settings.user.overview.Set('overviewColumns', current)
                self.DoFullOverviewReload()
            elif key == self.GetWhere():
                sm.GetService('state').ChangeStateState(self.GetWhere(), checkbox.data['retval'], checkbox.checked)
            elif key == 'shiplabels':
                sm.GetService('state').ChangeShipLabels(checkbox.data['retval'], checkbox.checked)
                return
        blue.pyos.synchro.Yield()
        uicore.registry.SetFocus(self.sr.scroll)

    def OnFilteredStatesChange(self, node, configToChange, *args):
        if node:
            selected = self.statesPanel.statesScroll.GetSelectedNodes(node)
        else:
            selected = self.statesPanel.statesScroll.GetSelected()
        flags = [ x.flag for x in selected ]
        addAlwaysShow = False
        addFilterOut = False
        if configToChange == 'alwaysShow':
            addAlwaysShow = True
        elif configToChange == 'filterOut':
            addFilterOut = True
        changeList = [('filteredStates', flags, addFilterOut), ('alwaysShownStates', flags, addAlwaysShow)]
        self.overviewPresetSvc.ChangeSettings(changeList=changeList)

    def MoveShipLabel(self, idx = None, *args):
        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        selected = self.sr.scroll.GetSelected()
        if selected:
            selected = selected[0]
            if idx is not None:
                if idx != selected.idx:
                    if selected.idx < idx:
                        newIdx = idx - 1
                    else:
                        newIdx = idx
                else:
                    return
            else:
                newIdx = max(0, selected.idx - 1)
            sm.GetService('state').ChangeLabelOrder(selected.idx, newIdx)
            self.LoadShips(newIdx)

    def OnRefreshOverviewTab(self):
        sm.GetService('bracket').UpdateLabels()
        self.RefreshOverviewTab()

    def OnReloadingOverviewProfile(self):
        self.RefreshOverviewName()
        self.LoadHistory()
        self.sr.tabs.AutoSelect()
        defaultSettings = self.overviewPresetSvc.GetSettingsNamesAndDefaults()
        for eachCb in self.settingCheckboxes:
            configName = eachCb.data['config']
            defaultValue = defaultSettings.get(configName, True)
            newValue = self.overviewPresetSvc.GetSettingValueOrDefaultFromName(configName, defaultValue)
            eachCb.SetChecked(newValue, report=0)

    def RefreshOverviewTab(self):
        tabSettings = self.overviewPresetSvc.GetTabSettingsForOverview()
        for key, editContainer in self.tabedit.iteritems():
            tSetting = tabSettings.get(key, {})
            if tSetting is None:
                continue
            comboTabOverviewContainer = self.comboTabOverview.get(key, None)
            comboTabBracketContainer = self.comboTabBracket.get(key, None)
            editField = self.tabedit.get(key, None)
            if None in (comboTabOverviewContainer, comboTabBracketContainer, editField):
                continue
            overviewSetting = tSetting.get('overview', None)
            bracketSetting = tSetting.get('bracket', None)
            tabName = tSetting.get('name', '')
            bracketOptions, overviewOptions = self.GetBracketAndOverviewOptions()
            newOverviewOptions = None
            if self.overviewPresetSvc.IsTempName(overviewSetting):
                currBracket, currOverview, newOverviewOptions, tabName = self.GetTabInfoForCombos(key, overviewOptions, tabSettings)
            comboTabOverviewContainer.LoadOptions(newOverviewOptions or overviewOptions)
            comboTabOverviewContainer.SelectItemByValue(overviewSetting)
            comboTabBracketContainer.SelectItemByValue(bracketSetting)
            editField.SetText(tabName)
            editField.originalValue = tabName

    def UpdateOverviewTab(self, *args):
        tabSettings = {}
        for key in self.tabedit.keys():
            editContainer = self.tabedit.get(key, None)
            comboTabBracketContainer = self.comboTabBracket.get(key, None)
            comboTabOverviewContainer = self.comboTabOverview.get(key, None)
            if not (editContainer and comboTabOverviewContainer and comboTabBracketContainer):
                continue
            if not editContainer.text:
                continue
            tabSettings[key] = {'name': editContainer.text,
             'bracket': comboTabBracketContainer.selectedValue,
             'overview': comboTabOverviewContainer.selectedValue}

        oldtabsettings = self.overviewPresetSvc.GetTabSettingsForOverview()
        sm.ScatterEvent('OnOverviewTabChanged', tabSettings, oldtabsettings)

    def _OnResize(self, *args):
        self.UpdateStateTopHeight()

    def MiscCheckboxChange(self, cb, *args):
        configName = cb.data.get('config', '')
        if configName == 'showInTargetRange':
            self.ChangeStateOfSubCheckboxes(cb)
        elif configName == 'showBiggestDamageDealers':
            if cb.checked:
                sm.GetService('bracket').EnableShowingDamageDealers()
            else:
                sm.GetService('bracket').DisableShowingDamageDealers()
        elif configName == 'targetCrosshair':
            sm.GetService('bracket').Reload()
        elif cb in self.targetRangeSubCheckboxes:
            sm.GetService('bracket').ShowInTargetRange()

    def ChangeStateOfSubCheckboxes(self, cb):
        if cb.checked:
            sm.GetService('bracket').EnableInTargetRange()
            for subCb in self.targetRangeSubCheckboxes:
                subCb.Enable()
                subCb.opacity = 1.0

        else:
            sm.GetService('bracket').DisableInTargetRange()
            for subCb in self.targetRangeSubCheckboxes:
                subCb.Disable()
                subCb.opacity = 0.3


class DraggableOverviewEntry(Checkbox):
    __guid__ = 'listentry.DraggableOverviewEntry'
    isDragObject = True

    def Startup(self, *args):
        listentry.Checkbox.Startup(self, args)
        self.sr.posIndicatorCont = uiprimitives.Container(name='posIndicator', parent=self, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, height=2)
        self.sr.posIndicator = uiprimitives.Fill(parent=self.sr.posIndicatorCont, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.posIndicator.state = uiconst.UI_HIDDEN
        self.canDrag = False

    def GetDragData(self, *args):
        if not self.sr.node.canDrag:
            return
        self.sr.node.scroll.SelectNode(self.sr.node)
        return [self.sr.node]

    def OnDropData(self, dragObj, nodes, *args):
        if GetAttrs(self, 'parent', 'OnDropData'):
            node = nodes[0]
            if GetAttrs(node, 'panel'):
                self.parent.OnDropData(dragObj, nodes, idx=self.sr.node.idx)

    def OnDragEnter(self, dragObj, nodes, *args):
        self.sr.posIndicator.state = uiconst.UI_DISABLED

    def OnDragExit(self, *args):
        self.sr.posIndicator.state = uiconst.UI_HIDDEN


class ColumnEntry(DraggableOverviewEntry):
    __guid__ = 'listentry.ColumnEntry'

    def Startup(self, *args):
        DraggableOverviewEntry.Startup(self, args)
        self.sr.checkbox.state = uiconst.UI_PICKCHILDREN
        diode = uiutil.GetChild(self, 'diode')
        diode.state = uiconst.UI_NORMAL
        diode.OnClick = self.ClickDiode

    def ClickDiode(self, *args):
        self.sr.checkbox.ToggleState()

    def OnClick(self, *args):
        listentry.Generic.OnClick(self, *args)


class FlagEntry(DraggableOverviewEntry):
    __guid__ = 'listentry.FlagEntry'

    def Startup(self, *args):
        DraggableOverviewEntry.Startup(self, args)
        self.sr.flag = None
        self.sr.checkbox.state = uiconst.UI_PICKCHILDREN
        diode = uiutil.GetChild(self, 'diode')
        diode.state = uiconst.UI_NORMAL
        diode.OnClick = self.ClickDiode

    def Load(self, node):
        Checkbox.Load(self, node)
        if self.sr.flag:
            f = self.sr.flag
            self.sr.flag = None
            f.Close()
        colorPicker = uiprimitives.Container(parent=self, pos=(0, 0, 25, 20), name='colorPicker', state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT, idx=0)
        if node.cfgname == 'flag':
            flagInfo = sm.GetService('state').GetStatePropsColorAndBlink(node.flag)
            self.sr.flag = FlagIconWithState(parent=colorPicker, top=4, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, flagInfo=flagInfo)
        else:
            backgroundBlink = sm.GetService('state').GetStateBlink(node.cfgname, node.flag)
            backgroundColor = sm.GetService('state').GetStateBackgroundColor(node.flag)
            self.sr.flag = Fill(color=backgroundColor, parent=colorPicker, pos=(0, 4, 9, 9), state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT)
            if backgroundBlink:
                uicore.animations.FadeTo(self.sr.flag, startVal=0.0, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
        arrow = uiprimitives.Sprite(parent=colorPicker, pos=(0, 0, 16, 16), name='arrow', align=uiconst.CENTERRIGHT, texturePath='res:/ui/texture/icons/38_16_229.png', color=(1, 1, 1, 0.5), state=uiconst.UI_DISABLED)
        colorPicker.LoadTooltipPanel = self.LoadColorTooltipPanel
        colorPicker.GetTooltipPointer = self.GetColorTooltipPointer
        colorPicker.GetTooltipDelay = self.GetTooltipDelay

    def ClickDiode(self, *args):
        self.sr.checkbox.ToggleState()

    def OnClick(self, *args):
        listentry.Generic.OnClick(self, *args)

    def GetMenu(self):
        if self.sr.node.GetMenu:
            return self.sr.node.GetMenu()
        m = [(uiutil.MenuLabel('UI/Overview/ToggleBlink'), self.ToggleBlink)]
        return m

    def ToggleBlink(self):
        current = sm.GetService('state').GetStateBlink(self.sr.node.cfgname, self.sr.node.flag)
        sm.GetService('state').SetStateBlink(self.sr.node.cfgname, self.sr.node.flag, not current)
        self.Load(self.sr.node)

    def GetColorTooltipPointer(self):
        return uiconst.POINT_LEFT_2

    def GetTooltipDelay(self):
        return 50

    def LoadColorTooltipPanel(self, tooltipPanel, *args):
        currentColor = self.sr.node.props.iconColor
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = (3, 3, 3, 3)

        def ChangeColor(color):
            self.ChangeColor(color, tooltipPanel)

        colors = sm.GetService('state').GetStateColors()
        colorList = [ x[0] for x in colors.values() ]
        currentColor = sm.GetService('state').GetStateColor(self.sr.node.flag, where=self.sr.node.cfgname)
        colorPanel = ColorPanel(callback=ChangeColor, currentColor=currentColor, colorList=colorList, addClear=False)
        tooltipPanel.AddLabelSmall(text=localization.GetByLabel('UI/Mail/Select Color'))
        tooltipPanel.AddCell(cellObject=colorPanel)

    def ChangeColor(self, color, tooltipPanel):
        sm.GetService('state').SetStateColor(self.sr.node.cfgname, self.sr.node.flag, color)
        tooltipPanel.Close()
        self.Load(self.sr.node)


class ShipEntry(DraggableOverviewEntry):
    __guid__ = 'listentry.ShipEntry'

    def Startup(self, *args):
        DraggableOverviewEntry.Startup(self, args)
        self.sr.checkbox.state = uiconst.UI_PICKCHILDREN
        diode = uiutil.GetChild(self, 'diode')
        diode.state = uiconst.UI_NORMAL
        diode.OnClick = self.ClickDiode
        self.sr.preEdit = uicontrols.SinglelineEdit(name='preEdit', parent=self, align=uiconst.TOPLEFT, pos=(32, 0, 20, 0), OnFocusLost=self.OnPreChange, OnReturn=self.OnPreChange)
        self.postCont = uiprimitives.Container(parent=self, align=uiconst.TOALL, pos=(140, 0, 20, 0))
        self.sr.postEdit = uicontrols.SinglelineEdit(name='postEdit', parent=self.postCont, align=uiconst.TOPLEFT, pos=(0, 0, 20, 0), OnFocusLost=self.OnPostChange, OnReturn=self.OnPostChange)
        self.sr.comment = uicontrols.EveLabelMedium(text='', parent=self.postCont, left=28, top=2, state=uiconst.UI_DISABLED)

    def Load(self, node):
        Checkbox.Load(self, node)
        self.sr.label.left = 60
        self.sr.preEdit.SetValue(self.sr.node.flag['pre'])
        self.sr.postEdit.SetValue(self.sr.node.flag['post'])
        if self.sr.node.flag['type'] is None:
            self.sr.postEdit.state = uiconst.UI_HIDDEN
        else:
            self.sr.postEdit.state = uiconst.UI_NORMAL
        self.sr.comment.text = self.sr.node.comment

    def ClickDiode(self, *args):
        self.sr.checkbox.ToggleState()

    def OnClick(self, *args):
        listentry.Generic.OnClick(self, *args)

    def OnPreChange(self, *args):
        text = self.sr.preEdit.GetValue()
        if self.sr.node.flag['pre'] != text:
            self.sr.node.flag['pre'] = text.replace('<', '&lt;').replace('>', '&gt;')
            self.sr.node.OnChange(self.sr.checkbox)

    def OnPostChange(self, *args):
        text = self.sr.postEdit.GetValue()
        if self.sr.node.flag['post'] != text:
            self.sr.node.flag['post'] = text.replace('<', '&lt;').replace('>', '&gt;')
            self.sr.node.OnChange(self.sr.checkbox)


class StatesPanel(Container):
    default_name = 'StatesPanel'
    default_padLeft = 4
    default_padTop = 4
    default_padRight = 4
    default_padBottom = 4

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.initialized = False
        self.onChangeFunc = attributes['onChangeFunc']

    def CreateIfNeeded(self):
        if self.initialized:
            return
        self.initialized = True
        self.iconCont = Container(parent=self, name='iconCont', align=uiconst.TOTOP, height=20, state=uiconst.UI_PICKCHILDREN)
        showSprite = uiprimitives.Sprite(parent=self.iconCont, pos=(64, 0, 16, 16), name='showSprite', state=uiconst.UI_NORMAL, texturePath='res:/ui/texture/icons/generic/visible_default_16.png', align=uiconst.CENTERRIGHT, hint=localization.GetByLabel('UI/Overview/FilterStateAlwaysShowLong'))
        showSprite.SetRGB(0.1, 1.0, 0.1, 0.75)
        showSprite.OnClick = (self.OnIconClicked, 'alwaysShow')
        hideSprite = uiprimitives.Sprite(parent=self.iconCont, pos=(34, 0, 16, 16), name='hideSprite', state=uiconst.UI_NORMAL, texturePath='res:/ui/texture/icons/generic/visible_dontshow_16.png', align=uiconst.CENTERRIGHT, hint=localization.GetByLabel('UI/Overview/FilterStateFilterOutLong'))
        hideSprite.OnClick = (self.OnIconClicked, 'filterOut')
        hideSprite.SetRGB(1.0, 0.05, 0.05, 0.75)
        neutralSprite = uiprimitives.Sprite(parent=self.iconCont, pos=(4, 0, 16, 16), name='neutralSprite', state=uiconst.UI_NORMAL, texturePath='res:/ui/texture/icons/generic/visible_matchstate_16.png', align=uiconst.CENTERRIGHT, hint=localization.GetByLabel('UI/Overview/FilterStateNotFilterOutLong'))
        neutralSprite.SetRGB(0.2, 0.4, 0.6, 0.75)
        neutralSprite.OnClick = (self.OnIconClicked, 'unfiltered')

        def ChangeOpaacity(sprite, opacity):
            sprite.opacity = opacity

        for sprite in (showSprite, hideSprite, neutralSprite):
            sprite.OnMouseEnter = (ChangeOpaacity, sprite, 1.2)
            sprite.OnMouseExit = (ChangeOpaacity, sprite, 1.0)

        self.statesScroll = uicontrols.Scroll(name='statesScroll', parent=self)

    def Load(self):
        self.CreateIfNeeded()
        includedList = []
        allFlagsAndProps = sm.GetService('state').GetStateProps()
        alwaysShow = sm.GetService('overviewPresetSvc').GetAlwaysShownStates() or []
        filtered = sm.GetService('overviewPresetSvc').GetFilteredStates() or []
        for flag, props in allFlagsAndProps.iteritems():
            data = KeyVal()
            data.label = props.text
            data.isAlwaysShow = flag in alwaysShow
            data.isFilterOut = flag in filtered
            data.flag = flag
            data.hint = props.hint
            data.props = props
            data.onChangeFunc = self.onChangeFunc
            entry = listentry.Get(entryType=None, data=data, decoClass=StateOverviewEntry)
            includedList.append(entry)

        includedList = localization.util.Sort(includedList, key=lambda x: x.label)
        self.statesScroll.Load(contentList=includedList, scrollTo=getattr(self, 'cachedScrollPos', 0.0))
        self.AdjustIcons()

    def _OnResize(self, *args):
        Container._OnResize(self)
        self.AdjustIcons()

    def OnIconClicked(self, configName, *args):
        self.onChangeFunc(None, configName)

    def AdjustIcons(self):
        scroll = getattr(self, 'statesScroll', None)
        if not scroll:
            return
        if scroll.sr.scrollcontrols.display:
            self.iconCont.padRight = scroll.sr.scrollcontrols.width
        else:
            self.iconCont.padRight = 0


class StateOverviewEntry(Generic):
    __guid__ = 'listentry.StateOverviewEntry'

    def Startup(self, *args):
        listentry.Generic.Startup(self, args)
        self.alwaysCb = uicontrols.Checkbox(parent=self, left=64, width=14, configName='alwaysShow', retval=None, checked=False, callback=self.OnCheckBoxChange, prefstype=('user', 'overview'), align=uiconst.CENTERRIGHT)
        self.alwaysCb.OnMouseEnter = self.OnMouseEnter
        self.alwaysCb.OnMouseExit = self.OnMouseExit
        self.alwaysCb.hint = localization.GetByLabel('UI/Overview/FilterStateAlwaysShowShort')
        self.filterOutCb = uicontrols.Checkbox(parent=self, left=34, width=14, configName='filterOut', retval=None, checked=False, callback=self.OnCheckBoxChange, prefstype=('user', 'overview'), align=uiconst.CENTERRIGHT)
        self.filterOutCb.OnMouseEnter = self.OnMouseEnter
        self.filterOutCb.OnMouseExit = self.OnMouseExit
        self.filterOutCb.hint = localization.GetByLabel('UI/Overview/FilterStateFilterOutShort')
        self.unfilteredCb = uicontrols.Checkbox(parent=self, left=4, width=14, configName='unfiltered', retval=None, checked=False, callback=self.OnCheckBoxChange, prefstype=('user', 'overview'), align=uiconst.CENTERRIGHT)
        self.unfilteredCb.OnMouseEnter = self.OnMouseEnter
        self.unfilteredCb.OnMouseExit = self.OnMouseExit
        self.unfilteredCb.hint = localization.GetByLabel('UI/Overview/FilterStateNotFilterOutShort')

    def Load(self, node):
        Generic.Load(self, node)
        self.onChangeFunc = node.onChangeFunc
        iconCont = Container(parent=self, pos=(3, 0, 9, 9), name='flag', state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, idx=0)
        iconRectLeft = (node.props.iconIndex + 1) * 10
        flagIcon = uiprimitives.Sprite(parent=iconCont, pos=(0, 0, 10, 10), name='icon', state=uiconst.UI_DISABLED, rectWidth=10, rectHeight=10, texturePath='res:/UI/Texture/classes/Bracket/flagIcons.png', align=uiconst.RELATIVE, color=node.props.iconColor)
        flagIcon.rectLeft = iconRectLeft
        col = sm.GetService('state').GetStateColor(node.flag, where='flag')
        flagBackground = uiprimitives.Fill(parent=iconCont, color=col)
        flagBackground.color.a *= 0.75
        self.sr.label.left = 16
        self.alwaysCb.SetGroup(node.props.label)
        self.filterOutCb.SetGroup(node.props.label)
        self.unfilteredCb.SetGroup(node.props.label)
        self.alwaysCb.width = 14
        self.filterOutCb.width = 14
        self.unfilteredCb.width = 14
        if node.isAlwaysShow:
            self.alwaysCb.SetChecked(True, report=0)
        elif node.isFilterOut:
            self.filterOutCb.SetChecked(True, report=0)
        else:
            self.unfilteredCb.SetChecked(True, report=0)

    def OnCheckBoxChange(self, cb, *args):
        self.onChangeFunc(self.sr.node, cb.data['config'])


class DraggableShareContainer(LayoutGrid):
    default_state = uiconst.UI_PICKCHILDREN
    default_align = uiconst.CENTERRIGHT
    default_name = 'draggableShareContainer'

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        self.columns = 2
        currentText = attributes.currentText
        defaultText = attributes.defaultText
        configName = attributes.configName
        hintText = attributes.hintText
        self.getDragDataFunc = attributes.getDragDataFunc
        self.sharedNameLabel = LabelEditable(name='%s_LabelEditable' % configName, parent=self, align=uiconst.CENTERRIGHT, pos=(0, 1, 0, 0), text=currentText, hint=localization.GetByLabel('UI/Overview/SharableOverviewTextHint'), configName=configName, maxLength=40, minLength=2, defaultText=defaultText)
        dragCont = Container(parent=self, name='dragCont', pos=(6, 0, 30, 21), align=uiconst.CENTERRIGHT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(bgParent=dragCont, color=(1, 1, 1, 0.15))
        f = uiprimitives.Fill(bgParent=dragCont, color=(1.0, 1.0, 1.0, 0.125))
        f.display = False
        dragSprite = Sprite(parent=dragCont, pos=(3, 0, 15, 15), align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Overview/shareableOverview_small.png')
        text = localization.GetByLabel('UI/Overview/ShareOverview')
        shareText = uicontrols.EveLabelMedium(text=text, parent=dragCont, left=20, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        dragCont.width = shareText.textwidth + shareText.left + 9
        dragCont.hint = hintText
        dragCont.cursor = uiconst.UICURSOR_DRAGGABLE

        def ChangeDisplayState(display, *args):
            f.display = display

        dragCont.OnMouseEnter = (ChangeDisplayState, True)
        dragCont.OnMouseExit = (ChangeDisplayState, False)
        for eachObject in (dragCont, self.sharedNameLabel.textLabel):
            eachObject.isDragObject = True
            eachObject.GetDragData = self.GetObjectDragData
            eachObject.PrepareDrag = self.PrepareObjectDrag

    def GetObjectDragData(self):
        return self.getDragDataFunc(self.sharedNameLabel.GetValue())

    def PrepareObjectDrag(self, dragContainer, dragSource):
        icon = DraggableIcon(align=uiconst.TOPLEFT, pos=(0, 0, 64, 64))
        icon.LoadIcon('res:/UI/Texture/classes/Overview/shareableOverview.png')
        dragContainer.children.append(icon)
        return (0, 0)
