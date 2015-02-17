#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelMap.py
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.frame import Frame
from carbonui.primitives.line import Line
from carbonui.util.various_unsorted import SortListOfTuples
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.tabGroup import TabGroup
from eve.client.script.ui.shared.infoPanels.InfoPanelBase import InfoPanelBase
import carbonui.const as uiconst
from eve.common.script.sys.eveCfg import IsFaction, IsRegion
import infoPanelConst
import uthread
from utillib import KeyVal
BTNSIZE = 24
from eve.client.script.ui.control.buttons import Button, ButtonIcon
from eve.client.script.ui.shared.maps.maputils import GetHintsOnSolarsystemBrackets, GetSolarSystemOptions
import trinity
from eve.client.script.ui.control import entries as listentry
import types
import log
import mapcommon
import localization
import weakref

class MapSettings(Container):
    __notifyevents__ = ['OnMapModeChangeDone', 'OnLoadWMCPSettings']
    callback = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.callback = attributes.callback
        self.starColorGroups = []
        self.starColorByID = None
        self.loadedTab = None
        self.sr.scroll = Scroll(parent=self)
        self.sr.scroll.sr.id = 'mapspalletescroll'
        self.sr.scroll.OnSelectionChange = self.OnSelectionChange
        self.sr.scroll.HideBackground()
        self.sr.scroll.RemoveActiveFrame()
        starviewstabs = TabGroup(name='tabparent', parent=self, idx=0, padTop=4)
        starviewstabs.Startup([[localization.GetByLabel('UI/Map/MapPallet/tabStars'),
          self.sr.scroll,
          self,
          'starview_color'],
         [localization.GetByLabel('UI/Map/MapPallet/tabLabels'),
          self.sr.scroll,
          self,
          'mapsettings_labels'],
         [localization.GetByLabel('UI/Map/MapPallet/tabMapLines'),
          self.sr.scroll,
          self,
          'mapsettings_lines'],
         [localization.GetByLabel('UI/Map/MapPallet/tabSolarSystemMap'),
          self.sr.scroll,
          self,
          'mapsettings_solarsystem'],
         [localization.GetByLabel('UI/Map/MapPallet/tabTiles'),
          self.sr.scroll,
          self,
          'mapsettings_tiles'],
         [localization.GetByLabel('UI/Map/MapPallet/tabMapAnimation'),
          self.sr.scroll,
          self,
          'mapsettings_other']], 'starmaptabs', autoselecttab=1)

    def ClickToggleFlatten(self, btn, *args):
        sm.GetService('starmap').ToggleFlattenMode()

    def Load(self, key):
        self.SetHint()
        if key == 'mapsearchpanel':
            self.Search(0)
        elif key == 'options':
            self.sr.optionstabs.AutoSelect()
        elif key[:11] == 'mapsettings' or key[:8] == 'starview':
            if key == self.loadedTab:
                return
            self.LoadSettings(key)
        if self.destroyed:
            return
        self.loadedTab = key

    def OnMapModeChangeDone(self, mode):
        """Disabling the flatten button when in systemmap mode"""
        if self.destroyed or not hasattr(self, 'sr'):
            return
        btnMode = self.sr.flattenBtns.GetBtnByIdx(1)
        btnFlat = self.sr.flattenBtns.GetBtnByIdx(2)
        if mode == 'starmap':
            btnFlat.Enable()
            btnMode.SetLabel(localization.GetByLabel('UI/Map/MapPallet/tabSolarSystemMap'))
        elif mode == 'systemmap':
            btnFlat.Disable()
            btnMode.SetLabel(localization.GetByLabel('UI/Map/MapPallet/tabStarMap'))

    def OnReturnSearch(self, *args):
        self.Search(1)

    def Search(self, errorifnothing, *args):
        t = uthread.new(self.Search_thread, errorifnothing)
        t.context = 'mappalette::Search'

    def Search_thread(self, errorifnothing):
        if not self or self.destroyed:
            return
        self.searchresult = None
        search = self.sr.searchinput.GetValue().strip()
        if len(search) < 1:
            if errorifnothing:
                raise UserError('Min3Chars')
                return
        elif len(search) < 3 and not localization.util.IsSearchTextIdeographic(localization.util.GetLanguageID(), search):
            raise UserError('Min3Chars')
        else:
            self.SetHint()
            if self is not None and not self.destroyed:
                pass
            else:
                return
            self.searchresult = sm.GetService('map').FindByName(search)
        if self.destroyed:
            return
        self.ShowSearchResult()

    def ShowSearchResult(self, *args):
        self.listtype = 'location'
        mapSvc = sm.GetService('map')
        tmplst = []
        scrolllist = []
        if self.searchresult and len(self.searchresult):
            for each in self.searchresult:
                wasID = each.itemID
                found = [each.itemName]
                while wasID:
                    wasID = mapSvc.GetParent(wasID)
                    if wasID:
                        item = mapSvc.GetItem(wasID)
                        if item is not None:
                            found.append(item.itemName)

                if len(found) == 3:
                    trace = localization.GetByLabel('UI/Map/MapPallet/Trace3Locations', location1=found[0], location2=found[1], location3=found[2])
                elif len(found) == 2:
                    trace = localization.GetByLabel('UI/Map/MapPallet/Trace2Locations', location1=found[0], location2=found[1])
                else:
                    trace = '/'.join(found)
                data = {'itemID': each.itemID,
                 'typeID': each.typeID,
                 'genericDisplayLabel': found[0],
                 'label': '%s<t>%s' % (trace, cfg.invtypes.Get(each.typeID).name)}
                entry = listentry.Get(entryType=None, data=data, decoClass=LocationSearchItem)
                scrolllist.append(entry)

        if self is None or self.destroyed:
            return
        headers = [localization.GetByLabel('UI/Map/MapPallet/hdrSearchName'), localization.GetByLabel('UI/Map/MapPallet/hdrSearchType')]
        self.sr.scroll.Load(contentList=scrolllist, headers=headers)
        if not len(scrolllist):
            self.SetHint(localization.GetByLabel('UI/Map/MapPallet/lblSearchNothingFound'))

    def Confirm(self, *args):
        pass

    def Deselect(self, *args):
        pass

    def Select(self, selection, *args):
        sm.GetService('starmap').SetInterest(selection.id)

    def OnLoadWMCPSettings(self, tabName):
        if self.loadedTab == tabName:
            self.LoadSettings(tabName)

    def LoadSettings(self, what):
        scrolllist = []
        if what == 'mapsettings_lines':
            showlines = settings.user.ui.Get('showlines', 4)
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Map/MapPallet/hdrConnectionLines')}))
            for config in [['showlines',
              0,
              localization.GetByLabel('UI/Map/MapPallet/cbNoLines'),
              showlines == 0],
             ['showlines',
              1,
              localization.GetByLabel('UI/Map/MapPallet/cbSelectionLinesOnly'),
              showlines == 1],
             ['showlines',
              2,
              localization.GetByLabel('UI/Map/MapPallet/cbSelectionRegionLinesOnly'),
              showlines == 2],
             ['showlines',
              3,
              localization.GetByLabel('UI/Map/MapPallet/cbSelectionRegionNeighborLinesOnly'),
              showlines == 3],
             ['showlines',
              4,
              localization.GetByLabel('UI/Map/MapPallet/cbAllLinesOnly'),
              showlines == 4]]:
                self.AddCheckBox(config, scrolllist, 'showlines')

            for config in [['map_alliance_jump_lines',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbAllianceJumpLines'),
              settings.user.ui.Get('map_alliance_jump_lines', 1) == 1]]:
                self.AddCheckBox(config, scrolllist)

            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Map/MapPallet/hdrColorLinesBy')}))
            for config in [['mapcolorby',
              mapcommon.COLORMODE_UNIFORM,
              localization.GetByLabel('UI/Map/MapPallet/cbColorByJumpType'),
              settings.user.ui.Get('mapcolorby', mapcommon.COLORMODE_UNIFORM) == mapcommon.COLORMODE_UNIFORM], ['mapcolorby',
              mapcommon.COLORMODE_REGION,
              localization.GetByLabel('UI/Map/MapPallet/cbColorByRegion'),
              settings.user.ui.Get('mapcolorby', mapcommon.COLORMODE_UNIFORM) == mapcommon.COLORMODE_REGION], ['mapcolorby',
              mapcommon.COLORMODE_STANDINGS,
              localization.GetByLabel('UI/Map/MapPallet/cbColorByStanding'),
              settings.user.ui.Get('mapcolorby', mapcommon.COLORMODE_UNIFORM) == mapcommon.COLORMODE_STANDINGS]]:
                self.AddCheckBox(config, scrolllist, 'mapcolorby')

        if what == 'mapsettings_tiles':
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Map/MapPallet/hdrTileSettings')}))
            for config in [['map_tile_no_tiles',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbTilesNone'),
              settings.user.ui.Get('map_tile_no_tiles', 1) == 1],
             ['map_tile_activity',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbTilesSovChanges'),
              settings.user.ui.Get('map_tile_activity', 0) == 1],
             ['map_tile_show_unflattened',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbTilesSovChangesUnflattened'),
              settings.user.ui.Get('map_tile_show_unflattened', 0) == 1],
             ['map_tile_show_outlines',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbTilesSovChangesOutlined'),
              settings.user.ui.Get('map_tile_show_outlines', 1) == 1]]:
                self.AddCheckBox(config, scrolllist)

            activeTileMode = settings.user.ui.Get('map_tile_mode', 0)
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Map/MapPallet/hdrTileSovColorBy')}))
            for tileMode, text in [(0, localization.GetByLabel('UI/Map/MapPallet/cbTilesSovereignty')), (1, localization.GetByLabel('UI/Map/MapPallet/cbTilesStandings'))]:
                config = ['map_tile_mode',
                 tileMode,
                 text,
                 activeTileMode == tileMode]
                self.AddCheckBox(config, scrolllist, 'map_tile_mode')

        if what == 'mapsettings_legend':
            scrolllist += self.GetLegendGroups()
        if what == 'starview_color':
            scrolllist += self.GetStarColorGroups()
        if what == 'mapsettings_solarsystem':
            scrolllist += GetSolarSystemOptions()
        if what == 'mapsettings_other':
            self.AddCheckBox(['mapautoframe',
             None,
             localization.GetByLabel('UI/Map/MapPallet/cbAnimFrameSelect'),
             settings.user.ui.Get('mapautoframe', 1) == 1], scrolllist)
            if settings.user.ui.Get('mapautoframe', 1) == 1:
                self.AddCheckBox(['mapautozoom',
                 None,
                 localization.GetByLabel('UI/Map/MapPallet/cbAnimAutoZoom'),
                 settings.user.ui.Get('mapautozoom', 0) == 1], scrolllist)
        if what == 'mapsettings_labels':
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Map/MapPallet/hdrRegionLables')}))
            for config in [['rlabel_region',
              0,
              localization.GetByLabel('UI/Map/MapPallet/cbRegionNoLabel'),
              settings.user.ui.Get('rlabel_region', 1) == 0],
             ['rlabel_region',
              1,
              localization.GetByLabel('UI/Map/MapPallet/cbRegionSelected'),
              settings.user.ui.Get('rlabel_region', 1) == 1],
             ['rlabel_region',
              2,
              localization.GetByLabel('UI/Map/MapPallet/cbRegionAndNeigbour'),
              settings.user.ui.Get('rlabel_region', 1) == 2],
             ['rlabel_region',
              3,
              localization.GetByLabel('UI/Map/MapPallet/cbRegionAll'),
              settings.user.ui.Get('rlabel_region', 1) == 3]]:
                self.AddCheckBox(config, scrolllist, 'rlabel_region')

            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Map/MapPallet/hdrOtherLables')}))
            for config in [['label_constellation',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbOtherConstellation'),
              settings.user.ui.Get('label_constellation', 1) == 1], ['label_solarsystem',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbOtherSolarSysytem'),
              settings.user.ui.Get('label_solarsystem', 1) == 1], ['label_landmarknames',
              None,
              localization.GetByLabel('UI/Map/MapPallet/cbOtherLandmarks'),
              settings.user.ui.Get('label_landmarknames', 1) == 1]]:
                self.AddCheckBox(config, scrolllist)

        if self.destroyed:
            return
        self.sr.scroll.Load(contentList=scrolllist)

    def GetActiveStarColorMode(self):
        """
            This function will call functions that match Get*Options to pull in each
            sub folder of options
        """
        starscolorby = settings.user.ui.Get('starscolorby', mapcommon.STARMODE_SECURITY)
        if not self.starColorByID:
            self.starColorByID = {}
            groupList = ['Root'] + self.GetAllStarColorGroupLabels()
            try:
                groupList.remove('Sovereignty_Sovereignty')
            except ValueError:
                log.LogError('Error while removing a sov option from the prime list - a long load may be impending!')

            import eve.client.script.ui.shared.maps.maputils as maputils
            for groupName in groupList:
                func = getattr(maputils, 'Get%sOptions' % groupName, None)
                if func is None:
                    continue
                ops = func()
                for label, id in ops:
                    self.starColorByID[id] = (groupName, label)

        if starscolorby not in self.starColorByID:
            if type(starscolorby) == types.TupleType and starscolorby[0] in (mapcommon.STARMODE_FACTION, mapcommon.STARMODE_MILITIA, mapcommon.STARMODE_FACTIONEMPIRE):
                _starmode, factionID = starscolorby
                options = {mapcommon.STARMODE_FACTION: ('Sovereignty_Sovereignty', localization.GetByLabel('UI/Map/MapPallet/cbModeFactions')),
                 mapcommon.STARMODE_FACTIONEMPIRE: ('Sovereignty_Sovereignty', localization.GetByLabel('UI/Map/MapPallet/cbStarsByEmpireFactions'))}.get(_starmode, (None, None))
                colorBy, factionName = options
                if factionID >= 0:
                    factionName = cfg.eveowners.Get(factionID).name
                self.starColorByID[starscolorby] = (colorBy, factionName)
            elif starscolorby == mapcommon.STARMODE_SOV_STANDINGS:
                self.starColorByID[starscolorby] = ('Sovereignty_Sovereignty', localization.GetByLabel('UI/Map/MapPallet/cbStarsByStandings'))
        return self.starColorByID.get(starscolorby, (None, None))

    def GetStarColorEntries(self, forGroup):
        import eve.client.script.ui.shared.maps.maputils as maputils
        starscolorby = settings.user.ui.Get('starscolorby', mapcommon.STARMODE_SECURITY)
        func = getattr(maputils, 'Get%sOptions' % forGroup, None)
        if not func:
            log.LogError('Missing function to provide options for', forGroup)
            return []
        scrolllist = []
        sublevel = 2 if forGroup.find('_') > 0 else 1
        for label, flag in func():
            config = ['starscolorby',
             flag,
             label,
             starscolorby == flag]
            entry = self.AddCheckBox(config, None, 'starscolorby', sublevel=sublevel)
            scrolllist.append(entry)

        return scrolllist

    def GetAllStarColorGroupLabels(self):
        self.GetStarColorGroupsSorted()
        topLevel = [ each[0] for each in self.starColorGroups ]
        tmp = [ each[2] for each in self.starColorGroups if each[2] != [] ]
        subLevel = []
        for each in tmp:
            subLevel.extend([ yu[0] for yu in each ])

        return topLevel + subLevel

    def GetStarColorGroupsSorted(self):
        if not self.starColorGroups:
            starColorGroups = [('Personal', localization.GetByLabel('UI/Map/MapPallet/hdrStarsMyInformation'), []),
             ('Services', localization.GetByLabel('UI/Map/MapPallet/hdrStarsServices'), []),
             ('Statistics', localization.GetByLabel('UI/Map/MapPallet/hdrStarsStatistics'), []),
             ('Sovereignty', localization.GetByLabel('UI/Map/MapPallet/hdrStarsSovereignty'), [('Sovereignty_FactionalWarfare', localization.GetByLabel('UI/Map/MapPallet/hdrStarsSovereigntyFacWar'), []),
               ('Sovereignty_Sovereignty', localization.GetByLabel('UI/Map/MapPallet/hdrStarsSovereignty'), []),
               ('Sovereignty_Changes', localization.GetByLabel('UI/Map/MapPallet/hdrStarsSovereigntyChanges'), []),
               ('Sovereignty_Development_Indices', localization.GetByLabel('UI/Map/MapPallet/hdrStarsSovereigntyIndixes'), [])]),
             ('Autopilot', localization.GetByLabel('UI/Map/MapPallet/hdrStarsAutoPilot'), []),
             ('Planets', localization.GetByLabel('UI/Map/MapPallet/hdrStarsPlanets'), []),
             ('Industry', localization.GetByLabel('UI/Map/MapPallet/hdrStarsIndustry'), [('Industry_Jobs', localization.GetByLabel('UI/Map/MapPallet/hdrIndustryJobs'), []), ('Industry_CostModifier', localization.GetByLabel('UI/Map/MapPallet/hdrIndustryCostModifier'), [])])]
            for group, label, subitems in starColorGroups:
                if subitems:
                    temp = []
                    for _group, _label, _subitems in subitems:
                        temp.append((_label, (_group, _label, _subitems)))

                    temp = SortListOfTuples(temp)
                    subitems = temp
                self.starColorGroups.append((label, (group, label, subitems)))

            self.starColorGroups = SortListOfTuples(self.starColorGroups)
        return self.starColorGroups

    def GetStarColorGroups(self):
        self.GetStarColorGroupsSorted()
        scrolllist = self.GetStarColorEntries('Root')
        activeGroup, activeLabel = self.GetActiveStarColorMode()
        for groupName, groupLabel, subitems in self.starColorGroups:
            id = ('mappaletteX', groupName)
            data = {'GetSubContent': self.GetSubContent,
             'label': groupLabel,
             'id': id,
             'groupItems': subitems,
             'iconMargin': 32,
             'showlen': 0,
             'state': 'locked',
             'BlockOpenWindow': 1,
             'key': groupName}
            if activeGroup == groupName:
                data['posttext'] = localization.GetByLabel('UI/Map/MapPallet/lblActiveColorCategory', activeLabel=activeLabel)
            elif activeGroup is not None and activeGroup.startswith(groupName + '_'):
                for subgroupName, subgroupLabel, subsubitems in subitems:
                    if activeGroup == subgroupName:
                        data['posttext'] = localization.GetByLabel('UI/Map/MapPallet/lblActiveColorCategory', activeLabel=subgroupLabel)

            scrolllist.append(listentry.Get('Group', data))

        return scrolllist

    def GetStarColorSubGroups(self, subitems):
        scrolllist = []
        activeGroup, activeLabel = self.GetActiveStarColorMode()
        for groupName, groupLabel, subitems in subitems:
            id = ('mappaletteX', groupName)
            data = {'GetSubContent': self.GetSubContent,
             'label': groupLabel,
             'id': id,
             'groupItems': [],
             'iconMargin': 32,
             'showlen': 0,
             'state': 'locked',
             'BlockOpenWindow': 1,
             'key': groupName,
             'sublevel': 1}
            if activeGroup == groupName:
                data['posttext'] = localization.GetByLabel('UI/Map/MapPallet/lblActiveColorCategory', activeLabel=activeLabel)
            scrolllist.append(listentry.Get('Group', data))

        return scrolllist

    def GetSubContent(self, data, newitems = 0):
        if data.groupItems:
            return self.GetStarColorSubGroups(data.groupItems)
        if data.key in self.GetAllStarColorGroupLabels():
            return self.GetStarColorEntries(data.key)
        return []

    def UpdateActiveStarColor(self):
        activeGroup, activeLabel = self.GetActiveStarColorMode()
        for entry in self.sr.scroll.GetNodes():
            if entry.__guid__ != 'listentry.Group' or entry.key not in self.GetAllStarColorGroupLabels():
                continue
            post = ''
            if entry.key == activeGroup:
                post = localization.GetByLabel('UI/Map/MapPallet/lblActiveColorCategory', activeLabel=activeLabel)
            entry.posttext = post
            if entry.panel:
                entry.panel.UpdateLabel()

    def GetLegendGroups(self):
        common = {'groupItems': [],
         'iconMargin': 32,
         'showlen': 0,
         'state': 'locked',
         'BlockOpenWindow': 1}
        scrolllist = []
        forLst = [('star', localization.GetByLabel('UI/Map/MapPallet/tabStars')), ('tile', localization.GetByLabel('UI/Map/MapPallet/tabTiles'))]
        for groupName, groupLabel in forLst:
            id = ('mappaletteX', groupName)
            uicore.registry.SetListGroupOpenState(id, 0)
            data = common.copy()
            data.update({'GetSubContent': self.GetLegendEntries,
             'label': groupLabel,
             'id': id,
             'key': groupName})
            scrolllist.append(listentry.Get('Group', data))

        return scrolllist

    def GetLegendEntries(self, data):
        legendList = sm.GetService('starmap').GetLegend(data.key)
        legendList.sort()
        scrolllist = []
        for legendItem in legendList:
            kv = KeyVal()
            kv.label = legendItem.caption
            kv.key = data.key
            kv.editable = False
            kv.selectable = True
            kv.hilightable = False
            kv.legend = legendItem
            scrolllist.append(listentry.Get('LegendEntry', data=kv))

        return scrolllist

    def SetHint(self, hintstr = None):
        if self.sr.scroll:
            self.sr.scroll.ShowHint(hintstr)

    def AddCheckBox(self, config, scrolllist, group = None, usecharsettings = 0, sublevel = 0):
        cfgname, retval, desc, default = config
        data = KeyVal()
        data.label = desc
        data.checked = default
        data.cfgname = cfgname
        data.retval = retval
        data.group = group
        data.sublevel = sublevel
        data.OnChange = self.CheckBoxChange
        data.usecharsettings = usecharsettings
        data.hideLines = True
        if scrolllist is not None:
            scrolllist.append(listentry.Get('Checkbox', data=data))
        else:
            return listentry.Get('Checkbox', data=data)

    def CheckBoxChange(self, checkbox):
        starmapSvc = sm.GetService('starmap')
        key = checkbox.data['key']
        val = checkbox.data['retval']
        if val is None:
            val = checkbox.checked
        if checkbox.data.get('usecharsettings', 0):
            settings.char.ui.Set(key, val)
        else:
            settings.user.ui.Set(key, val)
        if key == 'mapautoframe':
            self.LoadSettings('mapsettings_other')
        if self.callback:
            self.callback(key)

    def AddSeperator(self, height, where):
        Container(name='push', align=uiconst.TOTOP, height=height, parent=where)

    def AddHeader(self, header, where, height = 12):
        EveLabelMedium(text=header, parent=where, align=uiconst.TOTOP, height=12, state=uiconst.UI_NORMAL)

    def OnSelectionChange(self, selected):
        dataList = []
        colorList = []
        for node in selected:
            if node.key == 'tile':
                if node.legend.data is not None:
                    dataList.append(node.legend.data)
                else:
                    colorList.append(node.legend.color)

        if sm.GetService('viewState').IsViewActive('starmap'):
            sm.GetService('starmap').HighlightTiles(dataList, colorList)


class LegendEntry(listentry.Generic):
    """
    This class is for legend entries in sov dashboard
    """

    def Startup(self, *args):
        listentry.Generic.Startup(self, args)
        Line(parent=self, align=uiconst.TOBOTTOM)
        self.sr.legendColor = Container(name='legendColor', parent=self, align=uiconst.TOPLEFT, pos=(2, 2, 12, 12), idx=0)
        self.sr.colorFill = Fill(parent=self.sr.legendColor)
        Frame(parent=self.sr.legendColor, color=(0.25, 0.25, 0.25), idx=0)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.label.left = 18
        node.legend.color.a = 1.0
        c = node.legend.color
        self.sr.colorFill.SetRGB(c.r, c.g, c.b, c.a)
        self.key = node.key
        self.legend = node.legend
        self.sr.label.Update()

    def GetMenu(self):
        """
        tiles can highlight, hopefully stars someday
        here we have to deal with different types of data
        factionID
        regionID
        allianceID
        and just color
        """
        m = []
        if self.legend.data is not None:
            m += sm.GetService('menu').GetGMMenu(itemID=self.legend.data)
        if self.legend.data is not None:
            if IsFaction(self.legend.data):
                m += sm.GetService('menu').GetMenuFormItemIDTypeID(self.legend.data, const.typeFaction)
            elif IsRegion(self.legend.data):
                m += sm.GetService('menu').CelestialMenu(self.legend.data)
            else:
                m += sm.GetService('menu').GetMenuFormItemIDTypeID(self.legend.data, const.typeAlliance)
        return m


class LocationSearchItem(listentry.Item):
    isDragObject = True
