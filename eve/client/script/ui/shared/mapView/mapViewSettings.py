#Embedded file name: eve/client/script/ui/shared/mapView\mapViewSettings.py
from carbon.common.script.sys.service import ROLE_GML
from carbonui.control.scrollentries import ScrollEntryNode, SE_BaseClassCore
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.primitives.fill import Fill
from carbonui.primitives.layoutGrid import LayoutGrid, LayoutGridRow
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.checkbox import Checkbox, RadioButtonUnderlay
from eve.client.script.ui.control.eveLabel import EveLabelMedium, EveLabelSmall
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.themeColored import FillThemeColored, LineThemeColored
from eve.client.script.ui.shared.mapView.mapViewConst import VIEWMODE_COLOR_SETTINGS, VIEWMODE_GROUP_REGIONS, VIEWMODE_GROUP_CONSTELLATIONS, VIEWMODE_GROUP_DEFAULT, VIEWMODE_GROUP_SETTINGS, DEFAULT_MAPVIEW_SETTINGS, VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS, VIEWMODE_LINES_ALL, VIEWMODE_LINES_SELECTION_REGION_NEIGHBOURS, VIEWMODE_LINES_SELECTION_REGION, VIEWMODE_LINES_SELECTION, VIEWMODE_LINES_NONE, VIEWMODE_LINES_SETTINGS, VIEWMODE_LAYOUT_SHOW_ABSTRACT_DEFAULT, VIEWMODE_GROUP_SOLARSYSTEM, VIEWMODE_MARKERS_SETTINGS, VIEWMODE_MARKERS_OPTIONS, VIEWMODE_FOCUS_SELF
from eve.client.script.ui.shared.maps.mapcommon import *
import localization
import listentry
import eve.client.script.ui.shared.maps.maputils as maputils
from utillib import KeyVal
import uthread
ICON_ROOT = 'res:/UI/Texture/classes/MapView/'
ICON_MAP_BY_ID = {VIEWMODE_LINES_ALL: ICON_ROOT + 'icon_all_lines.png',
 VIEWMODE_LINES_SELECTION: ICON_ROOT + 'icon_selectiononly_lines.png',
 VIEWMODE_LINES_SELECTION_REGION: ICON_ROOT + 'icon_region_lines.png',
 VIEWMODE_GROUP_SOLARSYSTEM: ICON_ROOT + 'icon_no_group.png',
 VIEWMODE_GROUP_CONSTELLATIONS: ICON_ROOT + 'icon_const_group.png',
 VIEWMODE_GROUP_REGIONS: ICON_ROOT + 'icon_reg_group.png'}
LABEL_MAP_BY_ID = {VIEWMODE_LINES_ALL: localization.GetByLabel('UI/Map/MapPallet/cbAllLinesOnly'),
 VIEWMODE_LINES_SELECTION: localization.GetByLabel('UI/Map/MapPallet/cbSelectionLinesOnly'),
 VIEWMODE_LINES_SELECTION_REGION: localization.GetByLabel('UI/Map/MapPallet/cbSelectionRegionLinesOnly'),
 VIEWMODE_GROUP_SOLARSYSTEM: 'No grouping',
 VIEWMODE_GROUP_CONSTELLATIONS: 'Group stars by constellation',
 VIEWMODE_GROUP_REGIONS: 'Group stars by region',
 VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS: 'Abstract layout'}
MV_GROUPS_BY_ID = {VIEWMODE_GROUP_SETTINGS: [VIEWMODE_GROUP_SOLARSYSTEM, VIEWMODE_GROUP_CONSTELLATIONS, VIEWMODE_GROUP_REGIONS],
 VIEWMODE_LINES_SETTINGS: [VIEWMODE_LINES_ALL, VIEWMODE_LINES_SELECTION_REGION, VIEWMODE_LINES_SELECTION]}

def GetMapViewSetting(settingGroupKey):
    return settings.user.ui.Get(settingGroupKey, DEFAULT_MAPVIEW_SETTINGS[settingGroupKey])


def SetMapViewSetting(settingGroupKey, settingValue):
    settings.user.ui.Set(settingGroupKey, settingValue)


class MapViewSettingButtons(LayoutGrid):
    onSettingsChangedCallback = None

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        self.columns = 4
        self.buttonIconByGroupKey = {}
        self.onSettingsChangedCallback = attributes.onSettingsChangedCallback
        MapViewCheckboxOptionButton(parent=self, settingGroupKeys=(VIEWMODE_GROUP_SETTINGS, VIEWMODE_LINES_SETTINGS, VIEWMODE_LAYOUT_SHOW_ABSTRACT_SETTINGS), callback=self.OnSettingsChanged)
        MapViewColorModeSettingButton(parent=self, settingGroupKey=VIEWMODE_COLOR_SETTINGS, callback=self.OnSettingsChanged)
        MapViewMarkersSettingButton(parent=self, callback=self.OnSettingsChanged)
        ButtonIcon(parent=self, width=26, height=26, iconSize=16, func=self.FocusSelf, texturePath='res:/UI/Texture/classes/MapView/focusIcon.png')

    def Close(self, *args):
        LayoutGrid.Close(self, *args)
        self.buttonIconByGroupKey = None
        self.onSettingsChangedCallback = None

    def FocusSelf(self, *args):
        if self.onSettingsChangedCallback:
            self.onSettingsChangedCallback(VIEWMODE_FOCUS_SELF, session.charid)

    def OnSettingsChanged(self, settingGroupKey, settingValue):
        button = self.buttonIconByGroupKey.get(settingGroupKey, None)
        if button:
            button.ReloadSettingValue()
        if self.onSettingsChangedCallback:
            self.onSettingsChangedCallback(settingGroupKey, settingValue)

    def UpdateButtons(self):
        for groupID, button in self.buttonIconByGroupKey.iteritems():
            button.ReloadSettingValue()


class MapViewSettingButton(ButtonIcon):
    default_iconSize = 24
    default_width = 26
    default_height = 26
    settingGroupKey = None
    callback = None

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)
        self.settingGroupKey = attributes.settingGroupKey
        self.callback = attributes.callback
        self.ReloadSettingValue()

    def ReloadSettingValue(self):
        currentActive = GetMapViewSetting(self.settingGroupKey)
        self.SetTexturePath(ICON_MAP_BY_ID[currentActive])
        uicore.animations.BlinkOut(self.icon, startVal=1.0, endVal=0.0, duration=0.2, loops=2, curveType=uiconst.ANIM_BOUNCE)

    def Close(self, *args):
        ButtonIcon.Close(self, *args)
        self.callback = None

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if uicore.uilib.leftbtn:
            return
        tooltipPanel.columns = 2
        tooltipPanel.margin = 2
        for settingsID in MV_GROUPS_BY_ID[self.settingGroupKey]:
            tooltipPanel.AddRow(rowClass=ButtonTooltipRow, settingValue=settingsID, settingGroupKey=self.settingGroupKey, callback=self.callback)

        tooltipPanel.state = uiconst.UI_NORMAL

    def GetTooltipPointer(self):
        return uiconst.POINT_TOP_1


class MapViewMarkersSettingButton(ButtonIcon):
    default_iconSize = 24
    default_width = 26
    default_height = 26
    settingGroupKey = None
    callback = None

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)
        self.settingGroupKey = VIEWMODE_MARKERS_SETTINGS
        self.callback = attributes.callback
        self.SetTexturePath(ICON_ROOT + 'markersIcon.png')

    def Close(self, *args):
        ButtonIcon.Close(self, *args)
        self.callback = None

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if uicore.uilib.leftbtn:
            return
        tooltipPanel.columns = 2
        tooltipPanel.margin = 2
        currentActive = GetMapViewSetting(self.settingGroupKey)
        sortList = []
        for groupID in VIEWMODE_MARKERS_OPTIONS:
            sortList.append((cfg.invgroups.Get(groupID).name, groupID))

        for groupName, groupID in sorted(sortList):
            checkBox = Checkbox(align=uiconst.TOPLEFT, text=groupName, checked=groupID in currentActive, wrapLabel=False, callback=self.OnCheckBoxChange, retval=groupID, prefstype=None)
            tooltipPanel.AddCell(cellObject=checkBox, colSpan=tooltipPanel.columns, cellPadding=(3, 0, 3, 0))

        tooltipPanel.state = uiconst.UI_NORMAL

    def GetTooltipPointer(self):
        return uiconst.POINT_TOP_1

    def GetTooltipDelay(self):
        return 5

    def OnCheckBoxChange(self, checkbox, *args, **kwds):
        currentActive = set(GetMapViewSetting(self.settingGroupKey))
        active = checkbox.GetValue()
        if active:
            currentActive.add(checkbox.data['value'])
        else:
            try:
                currentActive.remove(checkbox.data['value'])
            except KeyError:
                pass

        SetMapViewSetting(self.settingGroupKey, list(currentActive))
        if self.callback:
            self.callback(self.settingGroupKey, list(currentActive))


class ButtonTooltipRow(LayoutGridRow):
    default_state = uiconst.UI_NORMAL
    callback = None
    settingValue = None
    settingGroupKey = None

    def ApplyAttributes(self, attributes):
        LayoutGridRow.ApplyAttributes(self, attributes)
        self.callback = attributes.callback
        self.settingValue = attributes.settingValue
        self.settingGroupKey = attributes.settingGroupKey
        checkbox = RadioButtonUnderlay(pos=(0, 0, 16, 16))
        currentSetting = GetMapViewSetting(self.settingGroupKey)
        if currentSetting == self.settingValue:
            checkMark = Sprite(parent=checkbox, pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/Shared/checkboxCheckedOval.png', idx=0)
        self.AddCell(cellObject=checkbox, cellPadding=(0, 0, 3, 0))
        label = EveLabelMedium(text=LABEL_MAP_BY_ID[attributes.settingValue], align=uiconst.CENTERLEFT)
        self.AddCell(cellObject=label, cellPadding=(0, 0, 6, 0))
        self.highLight = Fill(bgParent=self, color=(1, 1, 1, 0.1), state=uiconst.UI_HIDDEN)

    def Close(self, *args):
        LayoutGridRow.Close(self, *args)
        self.callback = None

    def OnMouseEnter(self, *args):
        self.highLight.display = True

    def OnMouseExit(self, *args):
        self.highLight.display = False

    def OnClick(self, *args):
        SetMapViewSetting(self.settingGroupKey, self.settingValue)
        if self.callback:
            self.callback(self.settingGroupKey, self.settingValue)


class MapViewCheckboxOptionButton(ButtonIcon):
    default_iconSize = 24
    default_width = 26
    default_height = 26
    settingGroupKeys = None
    callback = None

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)
        self.settingGroupKeys = attributes.settingGroupKeys
        self.callback = attributes.callback
        self.SetTexturePath(ICON_ROOT + 'icon_const_group.png')

    def Close(self, *args):
        ButtonIcon.Close(self, *args)
        self.callback = None

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if uicore.uilib.leftbtn:
            return
        tooltipPanel.columns = 2
        tooltipPanel.margin = 2
        for settingsGroupKey in self.settingGroupKeys:
            if len(tooltipPanel.children):
                divider = LineThemeColored(align=uiconst.TOTOP, height=1)
                tooltipPanel.AddCell(cellObject=divider, colSpan=tooltipPanel.columns)
            if settingsGroupKey in MV_GROUPS_BY_ID:
                for settingsID in MV_GROUPS_BY_ID[settingsGroupKey]:
                    checked = settingsID == GetMapViewSetting(settingsGroupKey)
                    checkBox = Checkbox(align=uiconst.TOPLEFT, text=LABEL_MAP_BY_ID[settingsID], groupname=settingsGroupKey, checked=checked, wrapLabel=False, callback=self.OnCheckBoxChange, configName=settingsGroupKey, retval=settingsID)
                    tooltipPanel.AddCell(cellObject=checkBox, colSpan=tooltipPanel.columns, cellPadding=(3, 0, 3, 0))

            else:
                checked = bool(GetMapViewSetting(settingsGroupKey))
                checkBox = Checkbox(align=uiconst.TOPLEFT, text=LABEL_MAP_BY_ID[settingsGroupKey], checked=checked, wrapLabel=False, callback=self.OnCheckBoxChange, configName=settingsGroupKey)
                tooltipPanel.AddCell(cellObject=checkBox, colSpan=tooltipPanel.columns, cellPadding=(3, 0, 3, 0))

        tooltipPanel.state = uiconst.UI_NORMAL

    def OnCheckBoxChange(self, checkbox):
        key = checkbox.data['config']
        val = checkbox.data['value']
        if val is None:
            val = checkbox.checked
        if self.callback:
            self.callback(key, val)

    def _LocalCallback(self, *args, **kwds):
        if self.callback:
            self.callback(*args, **kwds)

    def GetTooltipDelay(self):
        return 5

    def GetTooltipPointer(self):
        return uiconst.POINT_TOP_1

    def GetTooltipPositionFallbacks(self):
        return [uiconst.POINT_TOP_2,
         uiconst.POINT_TOP_1,
         uiconst.POINT_TOP_3,
         uiconst.POINT_BOTTOM_2,
         uiconst.POINT_BOTTOM_1,
         uiconst.POINT_BOTTOM_3]


COLORMODE_MENU_WIDTH = 200
COLORMODE_MENU_HEIGHT = 280

class MapViewColorModeSettingButton(MapViewSettingButton):

    def ReloadSettingValue(self):
        self.SetTexturePath(ICON_ROOT + 'spectrumIcon.png')

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if uicore.uilib.leftbtn:
            return
        tooltipPanel.columns = 1
        tooltipPanel.cellPadding = 2
        tooltipPanel.state = uiconst.UI_NORMAL
        scrollPosition = settings.user.ui.Get('mapViewColorModeScrollPosition', 0.0)
        self.scroll = Scroll(parent=tooltipPanel, align=uiconst.TOPLEFT, width=COLORMODE_MENU_WIDTH, height=COLORMODE_MENU_HEIGHT)
        self.scroll.OnUpdatePosition = self.OnScrollPositionChanged
        scrollEntries = self.GetColorModeOptions()
        self.scroll.Load(contentList=scrollEntries, scrollTo=scrollPosition)

    def Close(self, *args):
        MapViewSettingButton.Close(self, *args)

    def OnScrollPositionChanged(self, *args, **kwargs):
        settings.user.ui.Set('mapViewColorModeScrollPosition', self.scroll.GetScrollProportion())

    def GetScrollEntries(self, options, settingsKey = None, sublevel = 0):
        currentActive = GetMapViewSetting(self.settingGroupKey)
        scrollList = []
        for label, settingValue in options:
            config = [self.settingGroupKey,
             settingValue,
             label,
             currentActive == settingValue]
            entry = self.AddCheckBox(config, None, self.settingGroupKey, sublevel=sublevel)
            scrollList.append(entry)

        return scrollList

    def GetGroupScrollEntry(self, groupID, groupLabel, groupData):
        id = ('mapviewsettings', groupID)
        data = {'GetSubContent': self.GetSubContent,
         'label': groupLabel,
         'id': id,
         'groupItems': groupData,
         'iconMargin': 32,
         'showlen': 0,
         'state': 'locked',
         'BlockOpenWindow': 1,
         'key': groupID,
         'showicon': 'hide'}
        return [listentry.Get('Group', data)]

    def GetSubContent(self, data, newitems = 0):
        for entry in self.scroll.GetNodes():
            if entry.__guid__ != 'listentry.Group' or entry.id == data.id:
                continue
            if entry.open:
                if entry.panel:
                    entry.panel.Toggle()
                else:
                    uicore.registry.SetListGroupOpenState(entry.id, 0)
                    entry.scroll.PrepareSubContent(entry)

        return self.GetScrollEntries(data.groupItems)

    def AddCheckBox(self, config, scrolllist, group = None, usecharsettings = 0, sublevel = 0):
        cfgname, retval, desc, default = config
        data = {}
        data['label'] = desc
        data['checked'] = default
        data['cfgname'] = cfgname
        data['retval'] = retval
        data['group'] = group
        data['OnChange'] = self.OnCheckBoxChange
        data['usecharsettings'] = usecharsettings
        data['entryWidth'] = COLORMODE_MENU_WIDTH
        data['decoClass'] = MapViewCheckbox
        scrollNode = ScrollEntryNode(**data)
        if scrolllist is not None:
            scrolllist.append(scrollNode)
        else:
            return scrollNode

    def OnCheckBoxChange(self, checkbox):
        key = checkbox.data['key']
        val = checkbox.data['retval']
        if val is None:
            val = checkbox.checked
        if checkbox.data.get('usecharsettings', 0):
            settings.char.ui.Set(key, val)
        else:
            settings.user.ui.Set(key, val)
        if self.callback:
            self.callback(self.settingGroupKey, val)

    def GetColorModeOptions(self):
        ret = [[localization.GetByLabel('UI/Map/MapPallet/cbStarsActual'), STARMODE_REAL],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsSecurity'), STARMODE_SECURITY],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsRegion'), STARMODE_REGION],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsDedDeadspace'), STARMODE_DUNGEONS],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsDedAgents'), STARMODE_DUNGEONSAGENTS],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsIncursion'), STARMODE_INCURSION],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsAdvoidance'), STARMODE_AVOIDANCE]]
        if eve.session.role & ROLE_GML:
            ret.append([localization.GetByLabel('UI/Map/MapPallet/cbStarsIncursionGM'), STARMODE_INCURSIONGM])
        ret.sort()
        scrollEntries = self.GetScrollEntries(ret)
        for groupLabel, groupID, loadFunction in self.GetColorModeGroups():
            scrollEntries += self.GetGroupScrollEntry(groupID, groupLabel, loadFunction())

        return scrollEntries

    def GetPersonalColorModeOptions(self):
        ret = [[localization.GetByLabel('UI/Map/MapPallet/cbStarsMyAssets'), STARMODE_ASSETS],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsIVisited'), STARMODE_VISITED],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsCargoLeagal'), STARMODE_CARGOILLEGALITY],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsPIScanRange'), STARMODE_PISCANRANGE]]
        if (const.corpRoleAccountant | const.corpRoleJuniorAccountant) & eve.session.corprole != 0:
            ret += [[localization.GetByLabel('UI/Map/MapPallet/cbStarsCorpOffices'), STARMODE_CORPOFFICES],
             [localization.GetByLabel('UI/Map/MapPallet/cbStarsCorpImpounded'), STARMODE_CORPIMPOUNDED],
             [localization.GetByLabel('UI/Map/MapPallet/cbStarsCorpProperty'), STARMODE_CORPPROPERTY],
             [localization.GetByLabel('UI/Map/MapPallet/cbStarsCorpDeliveries'), STARMODE_CORPDELIVERIES]]
        ret += [[localization.GetByLabel('UI/Map/MapPallet/cbStarsCorpMembers'), STARMODE_FRIENDS_CORP], [localization.GetByLabel('UI/Map/MapPallet/cbStarsFleetMembers'), STARMODE_FRIENDS_FLEET], [localization.GetByLabel('UI/Map/MapPallet/cbStarsMyAgents'), STARMODE_FRIENDS_AGENT]]
        ret.append([localization.GetByLabel('UI/Map/MapPallet/cbStarsMyColonies'), STARMODE_MYCOLONIES])
        ret.sort()
        return ret

    def GetPlanetsOptions(self):
        ret = []
        for planetTypeID in maputils.PLANET_TYPES:
            ret.append((cfg.invtypes.Get(planetTypeID).typeName, (STARMODE_PLANETTYPE, planetTypeID)))

        ret.sort()
        return ret

    def GetIndustryOptions(self):
        ret = [[localization.GetByLabel('UI/Map/MapPallet/cbStarsByJobsStartedLast24Hours'), STARMODE_JOBS24HOUR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByManufacturingJobsStartedLast24Hours'), STARMODE_MANUFACTURING_JOBS24HOUR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByResearchTimeJobsStartedLast24Hours'), STARMODE_RESEARCHTIME_JOBS24HOUR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByResearchMaterialJobsStartedLast24Hours'), STARMODE_RESEARCHMATERIAL_JOBS24HOUR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByCopyJobsStartedLast24Hours'), STARMODE_COPY_JOBS24HOUR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByInventionJobsStartedLast24Hours'), STARMODE_INVENTION_JOBS24HOUR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByManufacturingIndustryCostModifier'), STARMODE_INDUSTRY_MANUFACTURING_COST_INDEX],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByResearchTimeIndustryCostModifier'), STARMODE_INDUSTRY_RESEARCHTIME_COST_INDEX],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByResearchMaterialIndustryCostModifier'), STARMODE_INDUSTRY_RESEARCHMATERIAL_COST_INDEX],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByCopyIndustryCostModifier'), STARMODE_INDUSTRY_COPY_COST_INDEX],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsByInventionIndustryCostModifier'), STARMODE_INDUSTRY_INVENTION_COST_INDEX]]
        ret.sort()
        return ret

    def GetServicesOptions(self):
        ret = [[localization.GetByLabel('UI/Map/MapPallet/cbStarsClone'), STARMODE_SERVICE_Cloning],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsFactory'), STARMODE_SERVICE_Factory],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsFitting'), STARMODE_SERVICE_Fitting],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsInsurance'), STARMODE_SERVICE_Insurance],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsLaboratory'), STARMODE_SERVICE_Laboratory],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsRepair'), STARMODE_SERVICE_RepairFacilities],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsMilitia'), STARMODE_SERVICE_NavyOffices],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsRefinery'), STARMODE_SERVICE_ReprocessingPlant],
         [localization.GetByLabel('UI/Map/MapPallet/StarmodeSecurityOffices'), STARMODE_SERVICE_SecurityOffice]]
        ret.sort()
        return ret

    def GetStatisticsOptions(self):
        ret = [[localization.GetByLabel('UI/Map/MapPallet/cbStarsPilots30Min'), STARMODE_PLAYERCOUNT],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsPilotsDocked'), STARMODE_PLAYERDOCKED],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsJumps'), STARMODE_JUMPS1HR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsDestroyed'), STARMODE_SHIPKILLS1HR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsDestroyed24H'), STARMODE_SHIPKILLS24HR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsPoded1H'), STARMODE_PODKILLS1HR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsPoded24H'), STARMODE_PODKILLS24HR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsNPCDestroyed'), STARMODE_FACTIONKILLS1HR],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsStationCount'), STARMODE_STATIONCOUNT],
         [localization.GetByLabel('UI/Map/MapPallet/cbStarsCynosuarl'), STARMODE_CYNOSURALFIELDS]]
        ret.sort()
        return ret

    def GetColorModeGroups(self):
        colorModeGroups = [(localization.GetByLabel('UI/Map/MapPallet/hdrStarsMyInformation'), 'Personal', self.GetPersonalColorModeOptions),
         (localization.GetByLabel('UI/Map/MapPallet/hdrStarsServices'), 'Services', self.GetServicesOptions),
         (localization.GetByLabel('UI/Map/MapPallet/hdrStarsStatistics'), 'Statistics', self.GetStatisticsOptions),
         (localization.GetByLabel('UI/Map/MapPallet/hdrStarsPlanets'), 'Planets', self.GetPlanetsOptions),
         (localization.GetByLabel('UI/Map/MapPallet/hdrStarsIndustry'), 'Industry', self.GetIndustryOptions)]
        colorModeGroups.sort()
        return colorModeGroups


class MapViewCheckbox(SE_BaseClassCore):
    TEXTLEFT = 20
    TEXTRIGHT = 12
    TEXTTOPBOTTOM = 4

    def Startup(self, *args):
        self.label = EveLabelSmall(parent=self, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, left=self.TEXTLEFT, top=self.TEXTTOPBOTTOM)
        cbox = Checkbox(align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, parent=self, idx=0)
        cbox.left = 4
        cbox.top = 1
        cbox.width = 16
        cbox.height = 16
        cbox.data = {}
        cbox.OnChange = self.CheckBoxChange
        self.checkbox = cbox

    def Load(self, data):
        self.checkbox.SetGroup(data.Get('group', None))
        self.checkbox.SetChecked(data.checked, 0)
        self.checkbox.data.update({'key': data.cfgname,
         'retval': data.retval})
        self.label.width = data.entryWidth - self.TEXTLEFT - self.TEXTRIGHT
        self.label.text = data.label

    def CheckBoxChange(self, *args):
        self.sr.node.checked = self.checkbox.checked
        self.sr.node.OnChange(*args)

    def OnClick(self, *args):
        if not self or self.destroyed:
            return
        if self.checkbox.checked:
            eve.Message('DiodeDeselect')
        else:
            eve.Message('DiodeClick')
        if self.checkbox.groupName is None:
            self.checkbox.SetChecked(not self.checkbox.checked)
            return
        for node in self.sr.node.scroll.GetNodes():
            if issubclass(node.decoClass, MapViewCheckbox) and node.Get('group', None) == self.checkbox.groupName:
                if node.panel:
                    node.panel.checkbox.SetChecked(0, 0)
                    node.checked = 0
                else:
                    node.checked = 0

        if not self.destroyed:
            self.checkbox.SetChecked(1)

    def GetHeight(_self, node, width):
        textWidth, textHeight = EveLabelSmall.MeasureTextSize(node.label, width=node.entryWidth - MapViewCheckbox.TEXTLEFT - MapViewCheckbox.TEXTRIGHT)
        return max(20, textHeight + MapViewCheckbox.TEXTTOPBOTTOM * 2)

    def OnCharSpace(self, enteredChar, *args):
        uthread.pool('checkbox::OnChar', self.OnClick, self)
        return 1

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        self.checkbox.OnMouseEnter(*args)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        self.checkbox.OnMouseExit(*args)

    def OnMouseDown(self, *args):
        self.checkbox.OnMouseDown(*args)

    def OnMouseUp(self, *args):
        self.checkbox.OnMouseUp(*args)
