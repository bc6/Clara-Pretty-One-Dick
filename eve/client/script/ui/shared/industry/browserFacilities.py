#Embedded file name: eve/client/script/ui/shared/industry\browserFacilities.py
from carbonui.primitives.container import Container
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.quickFilter import QuickFilterEdit
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.industryUIConst import ACTIVITY_NAMES
from eve.client.script.ui.shared.industry.facilityEntry import FacilityEntry
from eve.client.script.ui.shared.industry.viewModeButtons import ViewModeButtons
from industry.const import ACTIVITIES
import localization
import carbonui.const as uiconst
import inventorycommon.util as util
OWNER_ANY = 1
OWNER_NPC = 2
OWNER_CORP = 3

class BrowserFacilities(Container):
    default_name = 'BrowserFacilities'
    __notifyevents__ = ['OnFacilityReload']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.callback = attributes.callback
        self.isInitialized = False

    def _OnClose(self, *args):
        sm.UnregisterNotify(self)

    def OnTabSelect(self):
        if self.isInitialized:
            self.UpdateScroll()
            return
        self.isInitialized = True
        self.topPanel = Container(name='topPanel', parent=self, align=uiconst.TOTOP, height=20, padding=(0, 6, 0, 6))
        self.scroll = Scroll(parent=self, id='InstallationBrowser')
        self.scroll.OnSelectionChange = self.OnScrollSelectionChange
        self.ownerCombo = Combo(name='ownerCombo', parent=self.topPanel, align=uiconst.TOLEFT, prefsKey='IndustryBlueprintOwner', callback=self.OnOwnerCombo, options=self.GetOwnerOptions(), width=120, padRight=4)
        self.activityCombo = Combo(name='activityCombo', parent=self.topPanel, align=uiconst.TOLEFT, prefsKey='IndustryBlueprintActivity', callback=self.OnActivityCombo, options=self.GetActivityOptions(), width=120, padRight=4)
        self.viewModeButtons = ViewModeButtons(parent=self.topPanel, align=uiconst.TORIGHT, controller=self, settingsID='IndustryBlueprintBrowserViewMode')
        self.filterEdit = QuickFilterEdit(name='searchField', parent=self.topPanel, hinttext=localization.GetByLabel('UI/Inventory/Filter'), maxLength=64, align=uiconst.TORIGHT, OnClearFilter=self.OnFilterEditCleared, padRight=4)
        self.filterEdit.ReloadFunction = self.OnFilterEdit
        self.UpdateScroll()

    def OnFacilityReload(self, *args):
        if self.isInitialized and self.display:
            self.UpdateScroll()

    def OnScrollSelectionChange(self, entries, activityID = None):
        self.callback(entries[0].facilityData)

    def OnFilterEdit(self):
        self.UpdateScroll()

    def OnFilterEditCleared(self):
        self.UpdateScroll()

    def UpdateScroll(self):
        installations = self.GetInstallationData()
        scrollList = self.GetScrollList(installations)
        self.scroll.sr.defaultColumnWidth = FacilityEntry.GetDefaultColumnWidth()
        self.scroll.sr.fixedColumns = FacilityEntry.GetFixedColumns(self.viewModeButtons.GetViewMode())
        self.scroll.LoadContent(contentList=scrollList, headers=FacilityEntry.GetHeaders(), noContentHint=localization.GetByLabel('UI/Industry/NoFacilitiesFound'))

    def GetInstallationData(self):
        installations = sm.GetService('facilitySvc').GetFacilities()
        cfg.evelocations.Prime((facilityData.facilityID for facilityData in installations))
        cfg.eveowners.Prime((facilityData.ownerID for facilityData in installations))
        return installations

    def GetScrollList(self, installations):
        scrollList = []
        for facilityData in installations:
            jumps = self.GetJumpsTo(facilityData.solarSystemID)
            if self.IsFilteredOut(facilityData):
                continue
            activityID = self.activityCombo.GetValue()
            node = Bunch(facilityData=facilityData, decoClass=FacilityEntry, sortValues=FacilityEntry.GetColumnSortValues(facilityData, jumps, activityID), viewMode=self.viewModeButtons.GetViewMode(), jumps=jumps, charIndex=facilityData.GetName(), activityID=activityID)
            scrollList.append(node)

        return scrollList

    def IsFilteredOut(self, facilityData):
        if not facilityData.activities:
            return True
        filterText = self.filterEdit.GetValue().strip().lower()
        if filterText:
            text = facilityData.GetName() + facilityData.GetOwnerName() + facilityData.GetTypeName()
            if text.lower().find(filterText) == -1:
                return True
        activityValue = self.activityCombo.GetValue()
        if activityValue and activityValue not in facilityData.activities:
            return True
        ownerValue = self.ownerCombo.GetValue()
        if ownerValue != OWNER_ANY:
            isCorporation = facilityData.ownerID == session.corpid
            if not isCorporation and ownerValue != OWNER_NPC:
                return True
            if isCorporation and ownerValue != OWNER_CORP:
                return True
        return False

    def GetJumpsTo(self, solarsystemID):
        return sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(solarsystemID)

    def OnViewModeChanged(self, viewMode):
        self.UpdateScroll()

    def OnActivityCombo(self, *args):
        self.UpdateScroll()

    def GetActivityOptions(self):
        ret = [ (localization.GetByLabel(ACTIVITY_NAMES[activityID]),
         activityID,
         None,
         industryUIConst.ACTIVITY_ICONS_SMALL[activityID]) for activityID in ACTIVITIES ]
        ret.insert(0, (localization.GetByLabel('UI/Industry/AllActivities'), 0))
        return ret

    def GetOwnerOptions(self):
        return [(localization.GetByLabel('UI/Industry/AllFacilities'), OWNER_ANY), (localization.GetByLabel('UI/Industry/PublicFacilities'),
          OWNER_NPC,
          None,
          'res:/UI/Texture/Classes/Inventory/readOnly.png'), (localization.GetByLabel('UI/Industry/CorpOwnedFacilities'),
          OWNER_CORP,
          None,
          'res:/UI/Texture/Classes/Industry/iconCorp.png')]

    def OnOwnerCombo(self, *args):
        self.UpdateScroll()
