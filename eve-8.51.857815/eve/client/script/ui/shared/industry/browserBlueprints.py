#Embedded file name: eve/client/script/ui/shared/industry\browserBlueprints.py
from collections import defaultdict
from carbonui.const import TOTOP
from carbonui.primitives.container import Container
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.client.script.ui.quickFilter import QuickFilterEdit
from eve.client.script.ui.shared.industry.industryUIConst import CORP_DIVISIONS
import const
from eve.client.script.ui.shared.industry.viewModeButtons import ViewModeButtons
import industry
import localization
import carbonui.const as uiconst
from eve.client.script.ui.shared.industry.blueprintEntry import BlueprintEntry
import blue
FACILITY_CURRENT = -1
FACILITY_ALL = -2
OWNER_ME = 1
OWNER_CORP = 2
BLUEPRINTS_ALL = 1
BLUEPRINTS_ORIGINAL = 2
BLUEPRINTS_COPY = 3
GROUPS_ALL = (None, None)

class BrowserBlueprints(Container):
    default_name = 'BrowserBlueprints'
    default_isCorp = False
    __notifyevents__ = ['OnBlueprintReload', 'OnIndustryJob']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.callback = attributes.callback
        self.isInitialized = False
        self.jobData = None
        self.solarsystemIDbyFacilityID = {}

    def SetFocus(self, *args):
        if self.isInitialized:
            uicore.registry.SetFocus(self.scroll)

    def UpdateSelectedEntry(self):
        if self.jobData:
            self.OnActivitySelected(self.jobData.blueprintID, self.jobData.activityID)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        if self.isInitialized:
            self.UpdateSelectedEntry()

    def OnTabSelect(self):
        if self.isInitialized:
            self.UpdateOwnerCombo()
            self.UpdateScroll()
            return
        self.isInitialized = True
        self.topPanel = Container(name='topPanel', parent=self, align=TOTOP, height=20, padding=(0, 6, 0, 6))
        self.scroll = Scroll(parent=self, id='BlueprintBrowser')
        self.scroll.OnSelectionChange = self.OnScrollSelectionChange
        self.scroll.OnKeyDown = self.OnScrollKeyDown
        self.scroll.OnChar = self.OnScrollChar
        utilMenuCont = Container(align=uiconst.TOLEFT, parent=self.topPanel, width=20)
        UtilMenu(menuAlign=uiconst.BOTTOMLEFT, parent=utilMenuCont, align=uiconst.CENTERLEFT, GetUtilMenu=self.GetSettingsMenu, texturePath='res:/UI/Texture/SettingsCogwheel.png', width=16, height=16, iconSize=18)
        self.ownerCombo = Combo(name='ownerCombo', parent=self.topPanel, align=uiconst.TOLEFT, callback=self.OnOwnerCombo, width=120)
        self.facilityCombo = Combo(name='facilityCombo', parent=self.topPanel, align=uiconst.TOLEFT, callback=self.OnFacilityCombo, width=200, padLeft=5)
        self.invLocationCombo = Combo(name='invLocationCombo', parent=self.topPanel, align=uiconst.TOLEFT, callback=self.OnInvLocationCombo, padLeft=5, width=120, settingsID='IndustryBlueprintBrowserInvLocation')
        self.blueprintTypeCombo = Combo(name='blueprintTypeCombo', parent=self.topPanel, align=uiconst.TOLEFT, callback=self.OnBlueprintTypeCombo, padLeft=5, width=100, settingsID='IndustryBlueprintBrowserType', options=self.GetBlueprintTypeComboOptions())
        self.categoryGroupCombo = Combo(name='categoryGroupCombo ', parent=self.topPanel, align=uiconst.TOLEFT, callback=self.OnCategoryGroupCombo, padLeft=5, width=100)
        self.viewModeButtons = ViewModeButtons(parent=self.topPanel, align=uiconst.TORIGHT, controller=self, settingsID='IndustryBlueprintBrowserViewMode')
        self.filterEdit = QuickFilterEdit(name='searchField', parent=self.topPanel, hinttext=localization.GetByLabel('UI/Inventory/Filter'), maxLength=64, align=uiconst.TORIGHT, padRight=4)
        self.filterEdit.ReloadFunction = self.OnFilterEdit
        self.UpdateOwnerCombo()
        self.UpdateBlueprintTypeCombo()
        self.UpdateScroll()

    def GetSettingsMenu(self, menuParent):
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Industry/ShowBlueprintsInUse'), checked=self.IsBlueprintsInUseShown(), callback=self.ToggleShowBlueprintsInUse)

    def ToggleShowBlueprintsInUse(self):
        settings.user.ui.Set('industryShowBlueprintsInUse', not self.IsBlueprintsInUseShown())
        self.UpdateScroll()

    def OnActivitySelected(self, itemID, activityID = None):
        if not self.isInitialized or activityID is None:
            return
        for node in self.scroll.GetNodes():
            node.selected = node.bpData.blueprintID == itemID
            self.scroll.UpdateSelection(node)
            if node.panel is None:
                continue
            node.panel.OnActivitySelected(itemID, activityID)

    def OnBlueprintReload(self, ownerID):
        """
        Server notifying us that the blueprint state has changed
        """
        if self.destroyed or not self.isInitialized:
            return
        if self.isInitialized and self.display:
            self.UpdateScroll()

    def OnIndustryJob(self, jobID, ownerID, blueprintID, installerID, status, successfulRuns):
        if not self.isInitialized:
            return
        for node in self.scroll.GetNodes():
            if node.bpData.blueprintID == blueprintID:
                if status < industry.STATUS_COMPLETED:
                    node.bpData.jobID = jobID
                else:
                    node.bpData.jobID = None
                if node.panel:
                    node.panel.OnJobStateChanged(status)

    def OnFilterEdit(self):
        self.UpdateScroll()

    def OnViewModeChanged(self, viewMode):
        self.UpdateScroll()

    def UpdateFacilityCombo(self, facilities):
        options = [(localization.GetByLabel('UI/Industry/AllFacilities'), FACILITY_ALL)]
        defaultFacilityID = self.GetDefaultFacilitySelection()
        facilities.setdefault(defaultFacilityID, 0)
        for facilityID, blueprintCount in facilities.iteritems():
            try:
                facility = sm.GetService('facilitySvc').GetFacility(facilityID)
                if facility:
                    self.solarsystemIDbyFacilityID[facilityID] = facility.solarSystemID
                    options.append((self.GetFacilityLabel(facility, blueprintCount), facilityID))
            except UserError:
                pass

        options = sorted(options, key=self._GetFacilitySortKey)
        self.facilityCombo.LoadOptions(options, select=defaultFacilityID)

    def GetDefaultFacilitySelection(self):
        if self.IsCorpSelected():
            facilityID = settings.user.ui.Get('BrowserBlueprintsFacilitiesCorp', FACILITY_CURRENT)
        else:
            facilityID = settings.user.ui.Get('BrowserBlueprintsFacilities', FACILITY_CURRENT)
        if isinstance(facilityID, tuple) or facilityID is None:
            facilityID = FACILITY_CURRENT
        if facilityID == FACILITY_CURRENT:
            facilityID = session.stationid2
        return facilityID

    def GetDefaultInvLocationSelection(self):
        if self.IsCorpSelected():
            return settings.user.ui.Get('BrowserBlueprintsInvLocationCorp', None)
        else:
            return settings.user.ui.Get('BrowserBlueprintsInvLocation', None)

    def _GetFacilitySortKey(self, option):
        _, facilityID = option
        if facilityID == FACILITY_ALL:
            return FACILITY_ALL
        if facilityID == session.stationid2:
            return FACILITY_CURRENT
        solarsystemID = self.solarsystemIDbyFacilityID[facilityID]
        return self.GetJumpsTo(solarsystemID)

    def GetFacilityLabel(self, facility, blueprintCount):
        if session.stationid2 and facility.facilityID == session.stationid2:
            return localization.GetByLabel('UI/Industry/CurrentStation')
        return localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/LocationNumberOfBlueprintsNumberOfJumps', locationName=facility.GetName(), blueprints=blueprintCount, jumps=facility.distance)

    def GetJumpsTo(self, solarsystemID):
        return sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(solarsystemID) or 0

    def OnFacilityCombo(self, combo, key, value):
        if value == session.stationid2:
            value = FACILITY_CURRENT
        if self.IsCorpSelected():
            settings.user.ui.Set('BrowserBlueprintsFacilitiesCorp', value)
        else:
            settings.user.ui.Set('BrowserBlueprintsFacilities', value)
        self.UpdateScroll()

    def GetInvLocations(self, blueprints):
        locations = {}
        for bpData in blueprints:
            flagID = bpData.flagID
            if self.IsContainerFlag(flagID):
                flagID = const.flagHangar
            locations[bpData.locationID, flagID] = bpData

        locations = locations.items()
        locations = sorted(locations, cmp=self._CompareLocations)
        return locations

    def _CompareLocations(self, location1, location2):
        """
        Put item hangar and corp divisions at top, the rest sorted alphabetically
        """
        (locationID1, flagID1), bpData1 = location1
        (locationID2, flagID2), bpData2 = location2
        idx1 = CORP_DIVISIONS.index(flagID1) if flagID1 in CORP_DIVISIONS else None
        idx2 = CORP_DIVISIONS.index(flagID2) if flagID2 in CORP_DIVISIONS else None
        if idx1 is None and idx2 is None:
            return cmp(bpData1.GetLocationName(), bpData2.GetLocationName())
        elif idx1 is None and idx2 is not None:
            return 1
        elif idx1 is not None and idx2 is None:
            return -1
        else:
            return cmp(idx1, idx2)

    def GetSelectedFacilityID(self):
        facilityID = self.facilityCombo.GetValue()
        if facilityID == FACILITY_CURRENT:
            return session.stationid2
        return facilityID

    def UpdateInvLocationCombo(self, blueprints):
        facilityID = self.GetSelectedFacilityID()
        options = []
        if facilityID and facilityID != FACILITY_ALL:
            locations = self.GetInvLocations(blueprints)
            options.extend([ (bpData.GetLocationName(),
             key,
             None,
             bpData.location.GetIcon()) for key, bpData in locations ])
            options = sorted(options)
        if len(options) != 1:
            options.insert(0, (localization.GetByLabel('UI/Industry/AllInventoryLocations'), (None, None)))
        self.invLocationCombo.LoadOptions(options, select=self.GetDefaultInvLocationSelection())

    def OnOwnerCombo(self, combo, key, value):
        settings.user.ui.Set('IndustryBlueprintBrowserOwner', value)
        self.UpdateBlueprintTypeCombo()
        self.UpdateScroll()

    def OnInvLocationCombo(self, combo, key, value):
        if self.IsCorpSelected():
            settings.user.ui.Set('BrowserBlueprintsInvLocationCorp', value)
        else:
            settings.user.ui.Set('BrowserBlueprintsInvLocation', value)
        self.UpdateScroll()

    def UpdateBlueprintTypeCombo(self):
        value = self.GetDefaultBlueprintTypeSelection()
        self.blueprintTypeCombo.SelectItemByValue(value)

    def GetDefaultBlueprintTypeSelection(self):
        if self.IsCorpSelected():
            return settings.user.ui.Get('BrowserBlueprintsBlueprintTypeCorp', BLUEPRINTS_ALL)
        else:
            return settings.user.ui.Get('BrowserBlueprintsBlueprintType', BLUEPRINTS_ALL)

    def OnBlueprintTypeCombo(self, combo, key, value):
        if self.IsCorpSelected():
            settings.user.ui.Set('BrowserBlueprintsBlueprintTypeCorp', value)
        else:
            settings.user.ui.Set('BrowserBlueprintsBlueprintType', value)
        self.UpdateScroll()

    def GetBlueprintTypeComboOptions(self):
        return ((localization.GetByLabel('UI/Industry/AllBlueprints'), BLUEPRINTS_ALL), (localization.GetByLabel('UI/Industry/Originals'),
          BLUEPRINTS_ORIGINAL,
          None,
          'res:/UI/Texture/icons/bpo.png'), (localization.GetByLabel('UI/Industry/Copies'),
          BLUEPRINTS_COPY,
          None,
          'res:/UI/Texture/icons/bpc.png'))

    def OnCategoryGroupCombo(self, combo, key, value):
        if self.IsCorpSelected():
            settings.user.ui.Set('BrowserBlueprintsCategoryGroupCorp', value)
        else:
            settings.user.ui.Set('BrowserBlueprintsCategoryGroup', value)
        self.UpdateScroll()

    def GetDefaultCategoryGroup(self):
        if self.IsCorpSelected():
            return settings.user.ui.Get('BrowserBlueprintsCategoryGroupCorp', GROUPS_ALL)
        else:
            return settings.user.ui.Get('BrowserBlueprintsCategoryGroup', GROUPS_ALL)

    def UpdateCategoryGroupCombo(self, blueprints):
        groupsByCategories = self.GetGroupsByCategories(blueprints)
        options = [(localization.GetByLabel('UI/Industry/AllGroups'), GROUPS_ALL)]
        for (categoryName, categoryID), groups in groupsByCategories:
            options.append((categoryName, (categoryID, None)))
            for groupName, groupID in groups:
                options.append((groupName,
                 (categoryID, groupID),
                 '',
                 None,
                 1))

        self.categoryGroupCombo.LoadOptions(options, select=self.GetDefaultCategoryGroup())

    def GetGroupsByCategories(self, blueprints):
        ids = defaultdict(set)
        for bpData in blueprints:
            typeObj = bpData.GetProductTypeObj()
            ids[typeObj.Category().name, typeObj.categoryID].add((typeObj.Group().name, typeObj.groupID))

        ret = []
        for category, groups in ids.iteritems():
            ret.append((category, list(groups)))

        ret.sort()
        for category, groups in ret:
            groups.sort()

        return ret

    def IsCorpSelected(self):
        return self.ownerCombo.GetValue() == OWNER_CORP

    def UpdateScroll(self):
        if self.IsHidden() or self.destroyed:
            return None
        self.scroll.ShowLoading()
        facilityID = self.GetDefaultFacilitySelection()
        blueprints, facilities = self.GetBlueprintsData(facilityID)
        self.UpdateFacilityCombo(facilities)
        self.UpdateInvLocationCombo(blueprints)
        self.scroll.HideLoading()
        if not len(blueprints):
            self.scroll.LoadContent(noContentHint=localization.GetByLabel('UI/Industry/NoBlueprintsFound'))
            return None
        showFacility = facilityID == FACILITY_ALL
        showLocation = self.invLocationCombo.GetValue() == (None, None)
        scrollList = self.GetScrollList(blueprints, showFacility, showLocation)
        self.scroll.sr.defaultColumnWidth = BlueprintEntry.GetDefaultColumnWidth()
        self.scroll.sr.fixedColumns = BlueprintEntry.GetFixedColumns(self.viewModeButtons.GetViewMode())
        self.scroll.LoadContent(contentList=scrollList, headers=BlueprintEntry.GetHeaders(showFacility=showFacility, showLocation=showLocation), noContentHint=localization.GetByLabel('UI/Industry/NoBlueprintsFound'))
        self.UpdateSelectedEntry()

    def GetFilteredBlueprints(self, blueprints):
        jumpsCache = {}
        jumpsAndBlueprints = []
        for bpData in blueprints:
            if self.IsFilteredOut(bpData):
                continue
            jumpsAndBlueprints.append((jumpsCache.setdefault(bpData.facilityID, bpData.GetDistance()), bpData))
            blue.pyos.BeNice()

        self.UpdateCategoryGroupCombo([ bpData for _, bpData in jumpsAndBlueprints ])
        categoryID, groupID = self.categoryGroupCombo.GetValue()
        if (categoryID, groupID) == GROUPS_ALL:
            return jumpsAndBlueprints
        ret = []
        for jumps, bpData in jumpsAndBlueprints:
            typeObj = bpData.GetProductTypeObj()
            if groupID:
                if typeObj.groupID == groupID:
                    ret.append((jumps, bpData))
            elif typeObj.categoryID == categoryID:
                ret.append((jumps, bpData))

        return ret

    def GetScrollList(self, blueprints, showFacility = True, showLocation = True):
        scrollList = []
        jumpsAndBlueprints = self.GetFilteredBlueprints(blueprints)
        for jumps, bpData in jumpsAndBlueprints:
            node = Bunch(bpData=bpData, decoClass=BlueprintEntry, sortValues=BlueprintEntry.GetColumnSortValues(bpData, jumps, showFacility, showLocation), viewMode=self.viewModeButtons.GetViewMode(), jumps=jumps, activityCallback=self.SelectActivity, showFacility=showFacility, showLocation=showLocation, item=bpData.GetItem(), charIndex=bpData.GetLabel())
            scrollList.append(node)
            blue.pyos.BeNice()

        return scrollList

    def GetBlueprintsData(self, facilityID):
        facilityID = facilityID if facilityID != FACILITY_ALL else None
        if self.IsCorpSelected():
            return sm.GetService('blueprintSvc').GetCorporationBlueprints(facilityID)
        else:
            return sm.GetService('blueprintSvc').GetCharacterBlueprints(facilityID)

    def IsFilteredOut(self, bpData):
        filterText = self.filterEdit.GetValue().strip().lower()
        if filterText:
            productTypeObj = bpData.GetProductTypeObj()
            text = bpData.GetName() + bpData.GetFacilityName() + bpData.GetLocationName() + productTypeObj.Group().name + productTypeObj.Category().name
            if text.lower().find(filterText) == -1:
                return True
        locationID, flagID = self.invLocationCombo.GetValue()
        if locationID:
            if bpData.locationID != locationID:
                return True
            if bpData.flagID != flagID and not self.IsContainerFlag(bpData.flagID):
                return True
        bpType = self.blueprintTypeCombo.GetValue()
        if bpType != BLUEPRINTS_ALL:
            if bpData.original != (bpType == BLUEPRINTS_ORIGINAL):
                return True
        if not self.IsBlueprintsInUseShown():
            if bpData.jobID is not None:
                return True
        return False

    def IsBlueprintsInUseShown(self):
        return settings.user.ui.Get('industryShowBlueprintsInUse', True)

    def IsContainerFlag(self, flagID):
        """
        Does this inventory flag represent an item in a container
        """
        return flagID in (const.flagLocked, const.flagUnlocked)

    def OnScrollSelectionChange(self, entries):
        self.SelectActivity(entries[0].bpData)

    def OnScrollKeyDown(self, key, flag):
        Scroll.OnKeyDown(self.scroll, key, flag)
        if key in (uiconst.VK_LEFT, uiconst.VK_RIGHT):
            sm.ScatterEvent('OnIndustryLeftOrRightKey', key)

    def OnScrollChar(self, key, flag):
        if key >= uiconst.VK_0 and key <= uiconst.VK_9 or key == uiconst.VK_BACK:
            sm.ScatterEvent('OnBlueprintBrowserNumericInput', key, flag)

    def SelectActivity(self, bpData, activityID = None):
        self.callback(bpData, activityID)

    def UpdateOwnerCombo(self):
        options = [(localization.GetByLabel('UI/Industry/OwnedByMe'), OWNER_ME)]
        if sm.GetService('blueprintSvc').CanSeeCorpBlueprints():
            options.append((localization.GetByLabel('UI/Industry/OwnedByCorp'),
             OWNER_CORP,
             None,
             'res:/UI/Texture/classes/Industry/iconCorp.png'))
        select = settings.user.ui.Get('IndustryBlueprintBrowserOwner', OWNER_ME)
        self.ownerCombo.LoadOptions(options, select=select)
