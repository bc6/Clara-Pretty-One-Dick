#Embedded file name: eve/client/script/ui/inflight\dungeoneditor.py
import uicontrols
import copy
import uiprimitives
from eve.common.script.util.eveCommonUtils import ComputeRadiusFromQuantity
import uthread
import uix
import uiutil
from eve.client.script.ui.control import entries as listentry
import trinity
import util
import blue
import dungeonHelper
import sys
import carbonui.const as uiconst
import uicls
import localization
import localizationBSD
pi = 3.141592653589793

def GetMessageFromLocalization(messageID):
    if '/jessica' in blue.pyos.GetArg():
        return localizationBSD.MessageText.Get(messageID).text
    else:
        return localization.GetByMessageID(messageID)


class DungeonEditor(uicontrols.Window):
    __guid__ = 'form.DungeonEditor'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnJessicaOpenDungeon',
     'OnJessicaOpenRoom',
     'OnDESelectionChanged',
     'OnDEObjectPaletteChanged',
     'OnDEObjectListChanged',
     'OnSelectObject',
     'OnDungeonEdit',
     'OnDungeonSelectionGroupRotation',
     'OnBSDTablesChanged']
    default_windowID = 'dungeoneditor'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.loadedTab = None
        self.roomTabSelected = 'Objects'
        self.loadingThread = None
        self.scope = 'inflight'
        self.SetCaption('Dungeon Editor')
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.LoadPanels()
        self.SetMinSize([350, 400])
        self.prevDungeonResults = None
        self.prevFactionID = None
        self.prevArchetypeID = None
        self.filterText = ''
        self.objectGroups = {}
        self.groupNameToIDMap = {}
        self.scenario = sm.GetService('scenario')
        self._navigation = sm.GetService('camera').dungeonHack
        if '/jessica' in blue.pyos.GetArg():
            self.cache = sm.GetService('cache')
        else:
            self.cache = sm.RemoteSvc('cache')
        self.hidePlacementGrid = settings.user.ui.Get('hidePlacementGrid', 0)
        uicore.layer.inflight.dungeonEditorSelectionEnabled = True
        self.oldRadialMenuTime = settings.user.ui.Get('actionMenuExpandTime', 150)
        settings.user.ui.Set('actionMenuExpandTime', 5000)

    def LoadPanels(self):
        panel = uiprimitives.Container(name='panel', parent=self.sr.main, left=const.defaultPadding, top=const.defaultPadding, width=const.defaultPadding, height=const.defaultPadding)
        self.sr.panel = panel
        self.sr.roomobjecttabs = uicontrols.TabGroup(name='tabparent', parent=self.sr.main, idx=0, tabs=[['Objects',
          panel,
          self,
          'RoomObjectTab'], ['Groups',
          panel,
          self,
          'RoomGroupTab']], groupID='roomobjectstab')
        self.sr.maintabs = uicontrols.TabGroup(name='tabparent', parent=self.sr.main, idx=0, tabs=[['Dungeons',
          panel,
          self,
          'DungeonTab'],
         ['Room objects',
          panel,
          self,
          'RoomTab'],
         ['Transform',
          panel,
          self,
          'AlignTab'],
         ['Settings',
          panel,
          self,
          'SettingTab'],
         ['Palette',
          panel,
          self,
          'PaletteTab'],
         ['Templates',
          panel,
          self,
          'TemplateTab']], groupID='tabgroupid')

    def Load(self, tabid):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        camera.idleMove = 0
        if self.loadingThread and self.loadingThread.alive:
            self.loadingThread.kill()
        self.UnloadPanel()
        self.loadedTab = None
        tabName = 'Load_%s' % tabid
        if hasattr(self, tabName):
            if tabName in ('Load_RoomTab', 'Load_RoomObjectTab', 'Load_RoomGroupTab'):
                self.sr.roomobjecttabs.display = True
            else:
                self.sr.roomobjecttabs.display = False
            self.loadedTab = tabid
            self.loadingThread = uthread.new(getattr(self, tabName))
            self.loadingThread.context = 'DungeonEditor::%s' % tabName
            if tabid != 'PaletteTab':
                self._navigation.SetGridState(not self.hidePlacementGrid)
                self._navigation.SetDrawAxis(not self.hidePlacementGrid)
            else:
                self._navigation.SetGridState(True)
                self._navigation.SetDrawAxis(True)

    def IsTabLoaded(self, tabId):
        return tabId == self.loadedTab

    def Refresh(self):
        self.Load(self.loadedTab)

    def UnloadPanel(self):
        self.sr.panel.Flush()
        self.sr.palettescroll = None
        self.sr.templatescroll = None

    def _GetDungeons(self):
        archetypeID = settings.user.ui.Get('dungeonArchetypeID', None)
        factionID = settings.user.ui.Get('dungeonFactionID', None)
        if self.prevDungeonResults is None or self.prevArchetypeID != archetypeID or self.prevFactionID != factionID:
            comboOptions = []
            dungeons = sm.RemoteSvc('dungeon').DEGetDungeons(archetypeID=archetypeID, factionID=factionID)
            for dungeon in dungeons:
                if dungeon.dungeonNameID is not None:
                    name = GetMessageFromLocalization(dungeon.dungeonNameID)
                else:
                    name = ''
                if dungeon.factionID:
                    factionName = cfg.eveowners.Get(dungeon.factionID).name
                    name = '%s (%s) [%d]' % (name, factionName, dungeon.dungeonID)
                else:
                    name = '%s [%d]' % (name, dungeon.dungeonID)
                comboOptions.append((name, dungeon.dungeonID))

            comboOptions.sort()
            comboOptions.insert(0, [' - Select Dungeon - ', None])
            self.prevArchetypeID = archetypeID
            self.prevFactionID = factionID
            self.prevDungeonResults = comboOptions
        comboOptions = self.prevDungeonResults
        filterText = self.filterText.lower()
        optionsFilter = lambda option: filterText in option[0].lower()
        comboOptions = filter(optionsFilter, comboOptions)
        availableDungeons = map(lambda option: option[1], comboOptions)
        return (comboOptions, availableDungeons)

    def _CreateCombo(self, comboOptions, comboID):
        comboSetval = settings.user.ui.Get(comboID, None)
        if comboSetval == 'All':
            settings.user.ui.Set(comboID, None)
            comboSetval = None
        return uicontrols.Combo(parent=self.sr.panel, label='', options=comboOptions, name=comboID, select=comboSetval, callback=self.OnComboChange, align=uiconst.TOTOP)

    def OnFilterDungeon(self, *args):
        self.filterText = self.dungeonFilter.GetValue()
        self.sr.maintabs.ReloadVisible()

    def OnGodMode(self, *args):
        settings.user.ui.Set('dungeonGodMode', self.godModeCheckbox.GetValue())

    def Load_DungeonTab(self):
        uicontrols.EveLabelMedium(text='Search Dungeons:', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        sb = uicontrols.Button(parent=row, label='Search', func=self.OnFilterDungeon, align=uiconst.CENTERRIGHT, left=2)
        self.dungeonFilter = uicontrols.SinglelineEdit(name='dungeonFilter', parent=row, setvalue=self.filterText, align=uiconst.TOALL, padRight=sb.width + 4, OnReturn=self.OnFilterDungeon)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        uicontrols.EveLabelMedium(text='Optional Filters:', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        uicontrols.EveLabelMedium(text='Archetype:', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        archetypes = sm.RemoteSvc('dungeon').GetArchetypes()
        archetypeOptions = [ (archetype.archetypeName, archetype.archetypeID) for archetype in archetypes ]
        archetypeOptions.sort()
        archetypeOptions.insert(0, ('All', None))
        self._CreateCombo(archetypeOptions, 'dungeonArchetypeID')
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        uicontrols.EveLabelMedium(text='Faction:', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        factions = sm.RemoteSvc('dungeon').DEGetFactions()
        factionOptions = [ (cfg.eveowners.Get(faction.factionID).name, faction.factionID) for faction in factions ]
        factionOptions.sort()
        factionOptions.insert(0, ('All', None))
        self._CreateCombo(factionOptions, 'dungeonFactionID')
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=24, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Select Dungeon:', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        comboOptions, availableDungeons = self._GetDungeons()
        comboID = 'dungeonDungeon'
        dungeonID = settings.user.ui.Get(comboID, 'All')
        uicontrols.Combo(parent=self.sr.panel, label='', options=comboOptions, name=comboID, select=dungeonID, callback=self.OnComboChange, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=16, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Select Room:', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        if dungeonID not in availableDungeons:
            uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding * 2)
            uicontrols.EveLabelMedium(text=' - No dungeon selected - ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
            return
        seldungeon = sm.RemoteSvc('dungeon').DEGetDungeons(dungeonID=dungeonID)[0]
        uicontrols.EveLabelMedium(text=GetMessageFromLocalization(seldungeon.dungeonNameID) + ' - Version ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOBOTTOM, height=16, padTop=4)
        godMode = settings.user.ui.Get('dungeonGodMode', 1)
        self.godModeCheckbox = uicontrols.Checkbox(text='God Mode', parent=row, configName='dungeonGodMode', retval=0, checked=godMode, callback=self.OnGodMode)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOBOTTOM, height=16, padTop=4)
        uicontrols.Button(parent=row, label='Play Dungeon', func=self.PlayDungeon, align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Go to selected room', func=self.GotoRoom, args=(), align=uiconst.TOLEFT, padLeft=4)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOBOTTOM, height=16)
        uicontrols.Button(parent=row, label='Edit Room', func=self.EditRoom, align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Save Room', func=self.SaveRoom, align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Reset', func=self.ResetDungeon, args=(), align=uiconst.TORIGHT, padLeft=4)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOBOTTOM, height=const.defaultPadding)
        rooms = sm.RemoteSvc('dungeon').DEGetRooms(dungeonID=seldungeon.dungeonID)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        self.scrollOptions = []
        for i, room in enumerate(rooms):
            self.scrollOptions.append(listentry.Get('Generic', {'label': '[%d] %s' % (room.roomID, room.roomName),
             'id': i + 1,
             'roomID': room.roomID,
             'OnClick': self.OnGotoSelectedRoomClicked}))

        self.sr.objscrollbox = uicontrols.Scroll(parent=self.sr.panel, name='scrollID')
        self.sr.objscrollbox.LoadContent(contentList=self.scrollOptions)
        if settings.user.ui.Get('selectedRoomID', None):
            rooms = self.sr.objscrollbox.GetNodes()
            for room in rooms:
                if room.roomID == settings.user.ui.Get('selectedRoomID', None):
                    self.sr.objscrollbox.SelectNode(room)
                    break

    def OnJessicaOpenDungeon(self, dungeonID, defaultRoomID = None):
        self.OnJessicaOpenRoom(dungeonID, defaultRoomID)

    def OnJessicaOpenRoom(self, dungeonID, roomID):
        settings.user.ui.Set('dungeonDungeon', dungeonID)
        self.loadedTab = 'DungeonTab'
        for tab in self.sr.maintabs.sr.tabs:
            if tab.sr.args == self.loadedTab:
                tab.Select()

        settings.user.ui.Set('selectedRoomID', roomID)
        if roomID:
            self.EditRoom()

    def ResetDungeon(self):
        sm.GetService('scenario').ResetDungeon()

    def PlayDungeon(self, *args):
        self._navigation.SetFreeLook(False)
        dungeonID = settings.user.ui.Get('dungeonDungeon', None)
        if dungeonID is None or dungeonID == 'All':
            return
        roomID = settings.user.ui.Get('selectedRoomID', None)
        if not roomID:
            objectList = self.sr.objscrollbox.GetNodes()
            if len(objectList) > 0:
                roomID = objectList[0].roomID
            else:
                return
        godMode = settings.user.ui.Get('dungeonGodMode', 1)
        sm.GetService('scenario').PlayDungeon(dungeonID, roomID, godmode=godMode)

    def EditRoom(self, *args):
        dungeonID = settings.user.ui.Get('dungeonDungeon', None)
        if dungeonID is None or dungeonID == 'All':
            return
        if not settings.user.ui.Get('selectedRoomID', None):
            objectList = self.sr.objscrollbox.GetNodes()
            if len(objectList) > 0:
                settings.user.ui.Set('selectedRoomID', objectList[0].roomID)
            else:
                return
        sm.GetService('scenario').EditRoom(dungeonID, settings.user.ui.Get('selectedRoomID', None))

    def SaveRoom(self, *args):
        """
        Forces a save of any unsaved object changes.
        """
        sm.StartService('scenario').SaveAllChanges()

    def GotoRoom(self, *args):
        roomID = settings.user.ui.Get('selectedRoomID', None)
        if roomID:
            sm.GetService('scenario').GotoRoom(roomID)

    def OnDungeonEdit(self, dungeonID, roomID, roomPos):
        self.InitializeSelectionGroups(roomID)

    def OnBSDTablesChanged(self, tables):
        if 'dungeon.dungeons' in tables or 'dungeon.rooms' in tables:
            self.prevDungeonResults = None
            if self.loadedTab == 'DungeonTab':
                self.Refresh()

    def InitializeSelectionGroups(self, roomID):
        """
        Initialize in-memory data structures for the currently selected group based on 
        what groups are defined in the database for what is the currently selected room.
        Note: persisted groups only work if jessica/backend are available.  Otherwise
        this will just clear the data structures.
        
        If no room is selected, then clear them. 
        """
        scenario = sm.StartService('scenario')
        self.objectGroups = {}
        self.groupNameToIDMap = {}
        scenario.RemoveAllHardGroups()
        if roomID and '/jessica' in blue.pyos.GetArg():
            import dungeon
            room = dungeon.Room.Get(roomID)
            if not room:
                import log
                log.LogError('Cannot load persisted selection groups for room', roomID, 'which does not appear to exist.')
                return
            objectIDsInRoom = [ obj.objectID for obj in room.GetObjects() ]
            MAX_SLEEP_TIME = 10000
            SLEEP_TIME = 250
            waitTime = 0
            while True:
                blue.synchro.SleepWallclock(SLEEP_TIME)
                waitTime += SLEEP_TIME
                objIsMissing = False
                dunObjects = scenario.GetDunObjects()
                dunObjectIDs = [ dunObj.dunObjectID for dunObj in dunObjects ]
                for objectID in objectIDsInRoom:
                    if objectID not in dunObjectIDs:
                        objIsMissing = True

                if not objIsMissing or waitTime > MAX_SLEEP_TIME:
                    break

            objectIDToSlimItem = {}
            for dunObj in dunObjects:
                objectIDToSlimItem[dunObj.dunObjectID] = dunObj

            sgList = room.GetSelectionGroups()
            for sg in sgList:
                objectList = [ objectIDToSlimItem[obj.objectID] for obj in sg.GetObjects() ]
                self.CreateGroupForEditor(sg.selectionGroupName, objectList, sg.GetOrientationQuaternion())
                self.groupNameToIDMap[sg.selectionGroupName] = sg.selectionGroupID

    def GetCurrentRoomID(self):
        """Get the roomID of the room currently being edited (if any)."""
        return sm.RemoteSvc('keeper').GetLevelEditor().GetCurrentlyEditedRoomID()

    def Load_RoomTab(self):
        dunObjs = self.scenario.GetDunObjects()
        if len(dunObjs) == 0:
            uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=28)
            uicontrols.EveLabelMedium(text='No dungeon objects found', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
            return
        if hasattr(self, 'Load_%sTab' % self.roomTabSelected):
            getattr(self, 'Load_%sTab' % self.roomTabSelected)()
        self.loadedTab = 'RoomTab'

    def Load_RoomObjectTab(self):
        self.roomTabSelected = 'Objects'
        self.Load_RoomTab()

    def Load_RoomGroupTab(self):
        self.roomTabSelected = 'Groups'
        self.Load_RoomTab()

    def Load_ObjectsTab(self):
        self.roomTabSelected = 'Objects'
        dunObjs = sm.GetService('scenario').GetDunObjects()
        scrollOptions = []
        boxItems = []
        for slimItem in dunObjs:
            if getattr(slimItem, 'dunObjectID', None) is not None:
                typeName = cfg.invtypes.Get(slimItem.typeID).name
                objName = cfg.evelocations.Get(slimItem.itemID).name
                entryName = typeName + ' : ' + objName
                boxItems.append([entryName,
                 slimItem.dunObjectID,
                 sm.GetService('scenario').IsSelectedByObjID(slimItem.dunObjectID),
                 slimItem.itemID,
                 slimItem.typeID])

        boxItems.sort()
        for objName, objID, selected, itemID, typeID in boxItems:
            scrollOptions.append(listentry.Get('Generic', {'label': objName,
             'id': objID,
             'itemID': itemID,
             'typeID': typeID,
             'OnClick': self.OnObjectClicked,
             'isSelected': selected,
             'GetMenu': self.GetItemMenu}))

        self.sr.objscrollbox = uicontrols.Scroll(parent=self.sr.panel, name='scrollID', align=uiconst.TOTOP, height=256)
        self.sr.objscrollbox.LoadContent(contentList=scrollOptions)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.Button(parent=row, label='Select All', func=self.ObjSelectAll, args=(), align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Invert selection', func=self.ObjInverseSel, args=(), align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Clear selection', func=self.ObjClearSel, args=(), align=uiconst.TOLEFT, padLeft=4)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Duplicate: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        for each in 'XYZ':
            checkbox1ID = 'duplicateOffset%s' % each
            curVal = 0
            uicontrols.EveLabelMedium(text=each, parent=row, left=50 + counter * 52, state=uiconst.UI_NORMAL)
            ed = uicontrols.SinglelineEdit(name='duplicateOffset%s' % each, parent=row, setvalue=curVal, pos=(60 + counter * 52,
             0,
             38,
             0), ints=(-30000, 30000))
            counter = counter + 1
            setattr(self, checkbox1ID, ed)

        uicontrols.EveLabelMedium(text='Offset: ', parent=row, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=32)
        self.duplicateAmount = uicontrols.SinglelineEdit(name='duplicateAmount', parent=row, setvalue=1, pos=(60, 0, 38, 0), ints=(1, 100))
        uicontrols.Button(parent=row, label='Duplicate', func=self.OnDuplicateClicked, args=('btn1',), pos=(112, 0, 0, 0))
        uicontrols.EveLabelMedium(text='Amount: ', parent=row, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.Button(parent=row, label='Create Group', func=self.OnCreateGroup, args=(), align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Create Template', func=self.OnCreateTemplateFromSelection, args=(), align=uiconst.TOLEFT, padLeft=4)
        uicontrols.Button(parent=row, label='Delete selected', func=self.OnDeleteSelected, args=(), align=uiconst.TORIGHT, padLeft=4)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20, padTop=4)
        uicontrols.Button(parent=row, label='Save Room', func=self.SaveRoom, align=uiconst.TOLEFT, padLeft=4)

    def Load_GroupsTab(self):
        self.roomTabSelected = 'Groups'
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        dunObjs = sm.GetService('scenario').GetDunObjects()
        scrollOptions = []
        selectedGroups = self.GetSelectedGroups()
        groups = self.objectGroups.items()
        groups.sort()
        boxItems = [ [index,
         groupName,
         groupItems,
         groupName in selectedGroups] for index, (groupName, groupItems) in enumerate(groups) ]
        for index, groupName, groupItems, selected in boxItems:
            scrollOptions.append(listentry.Get('ObjectGroupListEntry', {'label': groupName,
             'id': index,
             'groupItems': groupItems,
             'OnClick': self.OnObjectGroupClicked,
             'isSelected': selected,
             'locked': False,
             'form': self}))

        self.sr.objgroupscrollbox = uicontrols.Scroll(parent=self.sr.panel, name='scrollID', align=uiconst.TOTOP, height=256)
        self.sr.objgroupscrollbox.LoadContent(contentList=scrollOptions)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='Rename Group', func=self.OnRenameGroup, args=(), align=uiconst.TOLEFT)
        uicontrols.Button(parent=row, label='Remove Group', func=self.OnRemoveGroup, args=(), align=uiconst.TOLEFT)
        uicontrols.Button(parent=row, label='Delete Group Objects', func=self.OnDeleteSelectedGroup, args=(), align=uiconst.TOLEFT)

    def GetItemMenu(self, entry):
        info = entry.sr.node
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(info.itemID, info.typeID)
        return m

    def OnDuplicateClicked(self, *args):
        X = getattr(self, 'duplicateOffsetX').GetValue()
        Y = getattr(self, 'duplicateOffsetY').GetValue()
        Z = getattr(self, 'duplicateOffsetZ').GetValue()
        amount = self.duplicateAmount.GetValue()
        sm.StartService('scenario').DuplicateSelection(amount, X, Y, Z)

    def OnObjectClicked(self, entry, *args):
        if self.sr.objscrollbox:
            ids = self.GetCurrentlySelectedObjects()
            sm.StartService('scenario').SetSelectionByID(ids)

    def OnObjectGroupClicked(self, entry, *args):
        self.SelectObjectGroup(entry.sr.node.label)

    def IsGroupSelected(self, groupName):
        return self.scenario.AreAllSelected(self.objectGroups[groupName])

    def GetSelectedGroups(self):
        return filter(self.IsGroupSelected, self.objectGroups.iterkeys())

    def SelectObjectGroup(self, label):
        if label not in self.objectGroups:
            return
        scenarioSvc = sm.StartService('scenario')
        selectedGroup = self.objectGroups[label]
        ids = []
        dungeonObjects = scenarioSvc.GetDunObjects()
        for slimItem in selectedGroup:
            if slimItem.dunObjectID in [ dungeonObject.dunObjectID for dungeonObject in dungeonObjects ]:
                ids.append(slimItem.dunObjectID)

        for node in self.sr.objgroupscrollbox.GetNodes():
            if node.panel.sr.label.text == label:
                self.sr.objgroupscrollbox.SelectNode(node)
                scenarioSvc.SetSelectionByID(ids)
                scenarioSvc.SetActiveHardGroup(label)

    def ObjSelectAll(self):
        dunObjs = sm.GetService('scenario').GetDunObjects()
        selItems = []
        for slimItem in dunObjs:
            selItems.append(slimItem.dunObjectID)

        sm.GetService('scenario').SetSelectionByID(selItems)
        if self.IsTabLoaded('RoomTab'):
            self.Refresh()

    def ObjClearSel(self):
        sm.GetService('scenario').SetSelectionByID([])
        if self.IsTabLoaded('RoomTab'):
            self.Refresh()

    def ObjInverseSel(self):
        curSel = self.sr.objscrollbox.GetSelected()
        ids = []
        for each in curSel:
            ids.append(each.id)

        dunObjs = sm.GetService('scenario').GetDunObjects()
        selItems = []
        for slimItem in dunObjs:
            if not sm.GetService('scenario').IsSelectedByObjID(slimItem.dunObjectID):
                selItems.append(slimItem.dunObjectID)

        sm.GetService('scenario').SetSelectionByID(selItems)
        if self.IsTabLoaded('RoomTab'):
            self.Refresh()

    def OnDESelectionChanged(self):
        if self.IsTabLoaded('RoomTab') and not self.IsSelectionUpToDate():
            self.Refresh()

    def OnDEObjectListChanged(self):
        if self.IsTabLoaded('RoomTab'):
            self.Refresh()

    def IsSelectionUpToDate(self):
        """
        Return true if the editor has the same selection as the scenarioMgr,
        otherwise false.
        """
        remoteSelection = copy.copy(sm.StartService('scenario').selectionObjs)
        localSelection = self.GetCurrentlySelectedObjects()
        remoteSelection.sort()
        localSelection.sort()
        return remoteSelection == localSelection

    def GetCurrentlySelectedObjects(self):
        """
        Get the currently selected objects.
        """
        if self.destroyed or self.sr.objscrollbox.destroyed:
            selectedEntries = []
        else:
            selectedEntries = self.sr.objscrollbox.GetSelected()
        selectedObjects = []
        for entry in selectedEntries:
            selectedObjects.append(entry.id)

        return selectedObjects

    def OnSelectObject(self, selectedList, id):
        if id == 'In Game':
            return
        selectedObj = selectedList[0]
        if hasattr(selectedObj, 'selectTypeString'):
            if getattr(selectedObj, 'selectTypeString', 'unknown') == 'SelectDungeon':
                settings.user.ui.Set('dungeonFactionID', None)
                settings.user.ui.Set('dungeonArchetypeID', None)
                settings.user.ui.Set('dungeonDungeon', selectedObj.dungeonID)
                self.sr.maintabs.ReloadVisible()
            elif getattr(selectedObj, 'selectTypeString', 'unknown') == 'SelectDungeonRoom':
                if self.IsTabLoaded('DungeonTab'):
                    settings.user.ui.Set('selectedRoomID', selectedObj.roomID)
            elif getattr(selectedObj, 'selectTypeString', 'unknown') == 'SelectDungeonObject':
                sm.GetService('scenario').SetSelectionByID([selectedObj.objectID])
                if self.IsTabLoaded('RoomTab'):
                    objectList = self.sr.objscrollbox.GetNodes()
                    for objectEntry in objectList:
                        if objectEntry.id == selectedObj.objectID:
                            self.sr.objscrollbox.SetSelected(objectEntry.idx)
                            break

            elif getattr(selectedObj, 'selectTypeString', 'unknown') == 'SelectDungeonEntity':
                pass
            elif getattr(selectedObj, 'selectTypeString', 'unknown') == 'SelectDungeonEntityGroup':
                pass
            elif selectedObj:
                import log
                log.LogWarn('dungeoneditor::OnSelectObject: Unknown selection:', selectedObj.selectTypeString)

    def Load_AlignTab(self):
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=4)
        uicontrols.EveLabelMedium(text='Align: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='  Align centres  ', func=self.OnAlignCentres, args=('btn1',), align=uiconst.TOLEFT)
        for each in 'XYZ':
            checkbox1ID = 'alignCentre%s' % each
            checkbox1Setval = settings.user.ui.Get(checkbox1ID, 0)
            cb = uicontrols.Checkbox(text=each, parent=row, configName=checkbox1ID, retval=None, checked=checkbox1Setval, callback=self.OnCheckboxChange, align=uiconst.TOLEFT, pos=(0, 0, 28, 0))

        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='Distribute centres', func=self.OnDistributeCentres, args=('btn1',), align=uiconst.TOLEFT)
        for each in 'XYZ':
            checkbox1ID = 'distributeCentre%s' % each
            checkbox1Setval = settings.user.ui.Get(checkbox1ID, 0)
            cb = uicontrols.Checkbox(text=each, parent=row, configName=checkbox1ID, retval=None, checked=checkbox1Setval, callback=self.OnCheckboxChange, align=uiconst.TOLEFT, pos=(0, 0, 28, 0))

        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Jitter: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        for counter, each in enumerate('XYZ'):
            checkbox1ID = 'jitterOffset%s' % each
            curVal = 0
            ed = uicontrols.SinglelineEdit(name='jitterOffset%s' % each, parent=row, setvalue=curVal, pos=(60 + counter * 52,
             0,
             38,
             0), ints=(0, 30000))
            setattr(self, checkbox1ID, ed)

        uicontrols.EveLabelMedium(text='Offset: ', parent=row, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL).name = 'Pos Text'
        uicontrols.Button(parent=row, label='Jitter Position', func=self.OnJitterClicked, args=('btn1',), pos=(220, 0, 0, 0))
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        for counter, each in enumerate(('Yaw', 'Pitch', 'Roll')):
            checkbox1ID = 'jitterOffset%s' % each
            curVal = 0
            ed = uicontrols.SinglelineEdit(name='jitterOffset%s' % each, parent=row, setvalue=curVal, pos=(60 + counter * 52,
             0,
             38,
             0), ints=(0, 30000))
            setattr(self, checkbox1ID, ed)

        uicontrols.EveLabelMedium(text='Rotation: ', parent=row, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL).name = 'Rot Text'
        uicontrols.Button(parent=row, label='Jitter Rotation', func=self.OnJitterRotationClicked, pos=(220, 0, 0, 0))
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Arrange: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        uicontrols.Button(parent=row, label='Arrange', func=self.OnArrangeClicked, args=('btn1',), pos=(220, 0, 0, 0))
        for each in 'XYZ':
            checkbox1ID = 'arrangeOffset%s' % each
            curVal = 0
            uicontrols.EveLabelMedium(text=each, parent=row, left=50 + counter * 52, state=uiconst.UI_NORMAL)
            ed = uicontrols.SinglelineEdit(name='arrangeOffset%s' % each, parent=row, setvalue=curVal, pos=(60 + counter * 52,
             0,
             38,
             0), ints=(-30000, 30000))
            counter = counter + 1
            setattr(self, checkbox1ID, ed)

        uicontrols.EveLabelMedium(text='Offset: ', parent=row, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Quantity: (Only works on asteroids and clouds)', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        uicontrols.Button(parent=row, label='Set Quantity', func=self.OnSetQuantityClicked, args=('btn1',), pos=(220, 0, 0, 0))
        minMaxQuantity = self.GetSelectedObjectsMinMaxQuantity()
        minQuantity = minMaxQuantity[0]
        maxQuantity = minMaxQuantity[1]
        uicontrols.EveLabelMedium(text='Min.', parent=row, left=40, width=32, height=14, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text='Max.', parent=row, left=130, width=32, height=14, state=uiconst.UI_NORMAL)
        self.quantityMin = uicontrols.SinglelineEdit(name='quantityMin', parent=row, setvalue=int(minQuantity), pos=(60, 0, 64, 0), ints=(0, sys.maxint))
        self.quantityMax = uicontrols.SinglelineEdit(name='quantityMax', parent=row, setvalue=int(maxQuantity), pos=(154, 0, 64, 0), ints=(0, sys.maxint))
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Radius: (Only works on asteroids and clouds)', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        uicontrols.Button(parent=row, label='Set Radius', func=self.OnSetRadiusClicked, args=('btn1',), pos=(220, 0, 0, 0))
        uicontrols.EveLabelMedium(text='Min.', parent=row, left=40, width=32, height=14, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text='Max.', parent=row, left=130, width=32, height=14, state=uiconst.UI_NORMAL)
        minMaxRadius = self.GetSelectedObjectsMinMaxRadius()
        minRadius = minMaxRadius[0]
        maxRadius = minMaxRadius[1]
        self.radiusMin = uicontrols.SinglelineEdit(name='radiusMin', parent=row, setvalue=int(minRadius), pos=(60, 0, 64, 0), ints=(0, sys.maxint))
        self.radiusMax = uicontrols.SinglelineEdit(name='radiusMax', parent=row, setvalue=int(maxRadius), pos=(154, 0, 64, 0), ints=(0, sys.maxint))
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Rotate objects: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        uicontrols.Button(parent=row, label='Rotate ', func=self.OnRotateClicked, args=('btn1',), pos=(220, 0, 0, 0))
        for each in ['Y', 'P', 'R']:
            checkbox1ID = 'rotate_%s' % each
            curVal = 0
            uicontrols.EveLabelMedium(text=each, parent=row, left=50 + counter * 52, height=14, state=uiconst.UI_NORMAL)
            ed = uicontrols.SinglelineEdit(name='rotate_%s' % each, parent=row, setvalue=curVal, pos=(60 + counter * 52,
             0,
             38,
             0), ints=(-30000, 30000))
            counter = counter + 1
            setattr(self, checkbox1ID, ed)

        uicontrols.EveLabelMedium(text='ROTATION: ', parent=row, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Set rotation: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        uicontrols.Button(parent=row, label='Set rotation', func=self.OnSetRotateClicked, args=('btn1',), pos=(220, 0, 0, 0))
        for each in ['Y', 'P', 'R']:
            checkbox1ID = 'rotateset_%s' % each
            curVal = 0
            uicontrols.EveLabelMedium(text=each, parent=row, left=50 + counter * 52, height=14, state=uiconst.UI_NORMAL)
            ed = uicontrols.SinglelineEdit(name='rotateset_%s' % each, parent=row, setvalue=curVal, pos=(60 + counter * 52,
             0,
             38,
             0), ints=(-30000, 30000))
            counter = counter + 1
            setattr(self, checkbox1ID, ed)

        uicontrols.EveLabelMedium(text='ROTATION: ', parent=row, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)

    def GetSelectedObjectsMinMaxQuantity(self):
        minQuantity = 1
        maxQuantity = 1
        selObjs = sm.GetService('scenario').GetSelObjects()
        for slimItem in selObjs:
            if slimItem.dunRadius is not None:
                if slimItem.dunRadius > 1:
                    if minQuantity == 1:
                        minQuantity = slimItem.dunRadius
                    else:
                        minQuantity = min(minQuantity, slimItem.dunRadius)
                    maxQuantity = max(maxQuantity, slimItem.dunRadius)

        return (minQuantity, maxQuantity)

    def GetSelectedObjectsMinMaxRadius(self):
        minRadius = 1
        maxRadius = 1
        selObjs = sm.GetService('scenario').GetSelObjects()
        godma = sm.GetService('godma')
        for slimItem in selObjs:
            if slimItem.dunRadius is not None:
                if slimItem.dunRadius > 1:
                    if minRadius == 1:
                        minRadius = ComputeRadiusFromQuantity(slimItem.categoryID, slimItem.groupID, slimItem.typeID, slimItem.dunRadius, godma)
                    else:
                        minRadius = min(minRadius, ComputeRadiusFromQuantity(slimItem.categoryID, slimItem.groupID, slimItem.typeID, slimItem.dunRadius, godma))
                    maxRadius = max(maxRadius, ComputeRadiusFromQuantity(slimItem.categoryID, slimItem.groupID, slimItem.typeID, slimItem.dunRadius, godma))

        return (minRadius, maxRadius)

    def OnSetQuantityClicked(self, *args):
        minQuantity = self.quantityMin.GetValue()
        maxQuantity = self.quantityMax.GetValue()
        if maxQuantity < minQuantity:
            eve.Message('MinRadiusHigherThenMax')
            return
        sm.GetService('scenario').SetSelectedQuantity(minQuantity, maxQuantity)
        newMinMaxRadius = self.GetSelectedObjectsMinMaxRadius()
        newMinRadius = int(round(newMinMaxRadius[0]))
        newMaxRadius = int(round(newMinMaxRadius[1]))
        self.radiusMin.SetValue(newMinRadius)
        self.radiusMax.SetValue(newMaxRadius)

    def OnSetRadiusClicked(self, *args):
        minRadius = self.radiusMin.GetValue()
        maxRadius = self.radiusMax.GetValue()
        if maxRadius < minRadius:
            eve.Message('MinRadiusHigherThenMax')
            return
        sm.GetService('scenario').SetSelectedRadius(minRadius, maxRadius)
        newMinMaxQuantity = self.GetSelectedObjectsMinMaxQuantity()
        newMinQuantity = int(round(newMinMaxQuantity[0]))
        newMaxQuantity = int(round(newMinMaxQuantity[1]))
        self.quantityMin.SetValue(newMinQuantity)
        self.quantityMax.SetValue(newMaxQuantity)

    def OnSetRotateClicked(self, *args):
        y = getattr(self, 'rotateset_Y').GetValue()
        p = getattr(self, 'rotateset_P').GetValue()
        r = getattr(self, 'rotateset_R').GetValue()
        sm.GetService('scenario').SetRotate(y, p, r)

    def OnRotateClicked(self, *args):
        slimItems = sm.GetService('scenario').GetSelObjects()
        if len(slimItems) == 0:
            return
        yaw = getattr(self, 'rotate_Y').GetValue()
        pitch = getattr(self, 'rotate_P').GetValue()
        roll = getattr(self, 'rotate_R').GetValue()
        sm.GetService('scenario').RotateSelected(yaw, pitch, roll)

    def OnJitterClicked(self, *args):
        X = getattr(self, 'jitterOffsetX').GetValue()
        Y = getattr(self, 'jitterOffsetY').GetValue()
        Z = getattr(self, 'jitterOffsetZ').GetValue()
        sm.GetService('scenario').JitterSelection(X, Y, Z)

    def OnJitterRotationClicked(self, *args):
        yaw = self.jitterOffsetYaw.GetValue()
        pitch = self.jitterOffsetPitch.GetValue()
        roll = self.jitterOffsetRoll.GetValue()
        sm.StartService('scenario').JitterRotationSelection(yaw, pitch, roll)

    def OnArrangeClicked(self, *args):
        X = getattr(self, 'arrangeOffsetX').GetValue()
        Y = getattr(self, 'arrangeOffsetY').GetValue()
        Z = getattr(self, 'arrangeOffsetZ').GetValue()
        sm.GetService('scenario').ArrangeSelection(X, Y, Z)

    def OnCreateTemplateFromSelection(self):
        selObjs = sm.GetService('scenario').GetSelObjects()
        if not len(selObjs):
            sm.GetService('gameui').Say('ERROR: Cannot create a new template because no objects are selected.')
            return
        wnd = CreateDungeonTemplateWindow.Open()
        wnd.ShowModal()

    def OnCreateGroup(self):
        self.CreateGroup()

    def CreateGroup(self):
        """
        Create the hard group in the dungeon editor window and in the database.
        """
        groupName, selectedObjSlimItems = self.CreateGroupForEditor()
        self.CreateGroupForDatabase(groupName, selectedObjSlimItems)
        return groupName

    def CreateGroupForEditor(self, groupName = None, selectedObjSlimItems = None, orientation = None):
        """
        This creates a selection group for the dungeon editor window.  It does not
        affect the database in any way.
        
        If a selectionGroup object is specified, use the data from that object.
        Otherwise, make up a name and use the current selection.
        """
        scenario = sm.StartService('scenario')
        if selectedObjSlimItems is None:
            selectedObjSlimItems = scenario.GetSelObjects()
        if not selectedObjSlimItems:
            sm.GetService('gameui').Say('ERROR: Cannot create a new group because no objects are selected.')
            return
        if not groupName:
            maxUntitledGroupIndex = 0
            for groupName in self.objectGroups:
                if groupName.startswith('Untitled'):
                    try:
                        value = int(groupName[len('Untitled'):])
                        if value > maxUntitledGroupIndex:
                            maxUntitledGroupIndex = value
                    except ValueError:
                        pass

            groupName = 'Untitled' + '%02i' % (maxUntitledGroupIndex + 1)
        while groupName in self.objectGroups:
            groupName += 'x'

        self.objectGroups[groupName] = selectedObjSlimItems
        scenario.AddHardGroup(groupName, orientation)
        return (groupName, selectedObjSlimItems)

    def CreateGroupForDatabase(self, groupName, selectedObjSlimItems):
        """
        This creates a selection group for the database.  It does not affect the 
        in game editor windows.
        
        Note that if jessica is not enabled (and thus we do not have backend),
        this method will do nothing.
        """
        if '/jessica' in blue.pyos.GetArg():
            import dungeon
            newSelGroup = dungeon.SelectionGroup.Create(selectionGroupName=groupName)
            newSelGroup.roomID = self.GetCurrentRoomID()
            self.groupNameToIDMap[newSelGroup.selectionGroupName] = newSelGroup.selectionGroupID
            for obj in selectedObjSlimItems:
                newSelGroup.AddObject(obj.dunObjectID)

    def OnDungeonSelectionGroupRotation(self, groupName, x, y, z, w):
        """
        Message from the scenarioMgr that orientation of a selection group has changed.
        It doesn't have all of the structures we do here, so it's easier for it to just
        tell us to deal with the situation.
        """
        if '/jessica' in blue.pyos.GetArg():
            import dungeon
            selectionGroupID = self.groupNameToIDMap[groupName]
            selectionGroup = dungeon.SelectionGroup.Get(selectionGroupID)
            selectionGroup.SetOrientationQuaternion(x, y, z, w)

    def OnRenameGroup(self):
        selectedGroups = self.sr.objgroupscrollbox.GetSelected()
        for each in selectedGroups:
            self.OpenRenameGroupDialog(each.label)
            return

    def OpenRenameGroupDialog(self, key = ''):
        oldGroupName = key
        format = [{'type': 'btline'},
         {'type': 'push',
          'height': 8,
          'frame': 1},
         {'type': 'edit',
          'setvalue': key,
          'maxLength': 64,
          'labelwidth': len('Group Name:') * 7,
          'label': 'Group Name:',
          'key': 'newGroupName',
          'required': 1,
          'frame': 1},
         {'type': 'push',
          'height': 8,
          'frame': 1},
         {'type': 'btline'},
         {'type': 'data',
          'data': {'oldGroupName': oldGroupName}},
         {'type': 'errorcheck',
          'errorcheck': self.RenameGroupErrorCheck}]
        retval = uix.HybridWnd(format, 'Rename Group', 1, buttons=uiconst.OKCANCEL, minW=300, minH=50)
        if retval and retval['newGroupName'] and len(retval['newGroupName']) > 1:
            self.RenameGroup(retval['oldGroupName'], retval['newGroupName'])

    def RenameGroupErrorCheck(self, retval):
        """
        Confirm that changing the old name to the new one will not create two entries with the same name.
        """
        oldGroupName = retval['oldGroupName']
        newGroupName = retval['newGroupName']
        if oldGroupName == newGroupName:
            return ''
        if newGroupName in self.objectGroups:
            return 'Cannot rename %s: A group with the name you specified already exists. Specify a new group name.' % oldGroupName

    def RenameGroup(self, oldGroupName, newGroupName):
        if oldGroupName == newGroupName:
            return
        sm.GetService('scenario').RenameHardGroup(oldGroupName, newGroupName)
        self.objectGroups[newGroupName] = self.objectGroups[oldGroupName]
        del self.objectGroups[oldGroupName]
        if '/jessica' in blue.pyos.GetArg():
            import dungeon
            selGroup = dungeon.SelectionGroup.Get(self.groupNameToIDMap[oldGroupName])
            selGroup.selectionGroupName = newGroupName
            self.groupNameToIDMap[newGroupName] = self.groupNameToIDMap[oldGroupName]
            del self.groupNameToIDMap[oldGroupName]
        self.Refresh()

    def OnRemoveGroup(self):
        self.RemoveSelectedGroups()

    def _RemoveGroup(self, groupName):
        del self.objectGroups[groupName]
        self.scenario.RemoveHardGroup(groupName)
        if '/jessica' in blue.pyos.GetArg():
            import dungeon
            dungeon.SelectionGroup.Get(self.groupNameToIDMap[groupName]).Delete()
            del self.groupNameToIDMap[groupName]

    def RemoveGroup(self, groupName):
        self._RemoveGroup(groupName)
        self.Refresh()

    def RemoveSelectedGroups(self):
        selectedGroups = self.GetSelectedGroups()
        for groupName in selectedGroups:
            self._RemoveGroup(groupName)

        self.Refresh()

    def OnDeleteSelected(self):
        uthread.new(self.DeleteSelected).context = 'svc.scenario.OnDeleteSelected'

    def OnDeleteSelectedGroup(self):
        uthread.new(self.DeleteSelectedGroups).context = 'svc.scenario.OnDeleteSelectedGroup'

    def DeleteSelected(self):
        self.RemoveSelectedGroups()
        self.scenario.DeleteSelected()

    def DeleteGroup(self, groupName):
        self.scenario.DeleteObjects(self.objectGroups[groupName])
        self.RemoveGroup(groupName)

    def DeleteSelectedGroups(self):
        selectedGroups = self.GetSelectedGroups()
        for groupName in selectedGroups:
            self.scenario.DeleteObjects(self.objectGroups[groupName])
            self._RemoveGroup(groupName)

        self.Refresh()

    def OnAlignCentres(self, *args):
        selObjs = sm.GetService('scenario').GetSelObjects()
        if len(selObjs) == 0:
            return
        centreAxis = trinity.TriVector()
        for slimItem in selObjs:
            centreAxis.x = centreAxis.x + slimItem.dunX
            centreAxis.y = centreAxis.y + slimItem.dunY
            centreAxis.z = centreAxis.z + slimItem.dunZ

        centreAxis.Scale(1.0 / len(selObjs))
        for slimItem in selObjs:
            newX = slimItem.dunX
            newY = slimItem.dunY
            newZ = slimItem.dunZ
            if settings.user.ui.Get('alignCentreX', 0):
                newX = int(centreAxis.x)
            if settings.user.ui.Get('alignCentreY', 0):
                newY = int(centreAxis.y)
            if settings.user.ui.Get('alignCentreZ', 0):
                newZ = int(centreAxis.z)
            dungeonHelper.SetObjectPosition(slimItem.dunObjectID, newX, newY, newZ)

    def OnDistributeCentres(self, *args):
        selObjs = sm.GetService('scenario').GetSelObjects()
        if len(selObjs) < 2:
            return
        centreAxis = trinity.TriVector()
        minV = trinity.TriVector(selObjs[0].dunX, selObjs[0].dunY, selObjs[0].dunZ)
        maxV = minV.CopyTo()
        for slimItem in selObjs:
            minV.x = min(minV.x, slimItem.dunX)
            minV.y = min(minV.y, slimItem.dunY)
            minV.z = min(minV.z, slimItem.dunZ)
            maxV.x = max(maxV.x, slimItem.dunX)
            maxV.y = max(maxV.y, slimItem.dunY)
            maxV.z = max(maxV.z, slimItem.dunZ)

        dMinMaxV = maxV - minV
        dStepSize = dMinMaxV.CopyTo()
        dStepSize.Scale(1.0 / (len(selObjs) - 1))
        if len(selObjs) == 0:
            return
        counter = 0
        for slimItem in selObjs:
            newX = slimItem.dunX
            newY = slimItem.dunY
            newZ = slimItem.dunZ
            if settings.user.ui.Get('distributeCentreX', 0):
                newX = minV.x + dStepSize.x * counter
            if settings.user.ui.Get('distributeCentreY', 0):
                newY = minV.y + dStepSize.y * counter
            if settings.user.ui.Get('distributeCentreZ', 0):
                newZ = minV.z + dStepSize.z * counter
            dungeonHelper.SetObjectPosition(slimItem.dunObjectID, newX, newY, newZ)
            counter = counter + 1

    def Load_SettingTab(self):
        uicontrols.EveLabelMedium(text='Cursor size clamping', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        counter = 0
        uicontrols.Button(parent=row, label='Set min and max', func=self.OnSetCursorRadiusClicked, args=('btn1',), pos=(220, 0, 0, 0))
        minRadius = settings.user.ui.Get('cursorMin', 1.0)
        maxRadius = settings.user.ui.Get('cursorMax', 100000.0)
        selObjs = sm.GetService('scenario').GetSelObjects()
        for slimItem in selObjs:
            if slimItem.radius > 1:
                if minRadius == 1:
                    minRadius = slimItem.radius
                else:
                    minRadius = min(minRadius, slimItem.radius)
                maxRadius = max(maxRadius, slimItem.radius)

        uicontrols.EveLabelMedium(text='Min.', parent=row, left=40, width=32, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text='Max.', parent=row, left=130, width=32, state=uiconst.UI_NORMAL)
        self.cursorMin = uicontrols.SinglelineEdit(name='cursorMin', parent=row, setvalue=int(minRadius), pos=(60, 0, 64, 0), ints=(0, 60000))
        self.cursorMax = uicontrols.SinglelineEdit(name='cursorMax', parent=row, setvalue=int(maxRadius), pos=(154, 0, 64, 0), ints=(0, 60000))
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=6, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Aggression radius: ', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        checkbox1ID = 'showAggrRadius'
        checkbox1Setval = settings.user.ui.Get(checkbox1ID, 0)
        self.aggrSettings = uicontrols.Checkbox(text='Aggression radius', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=settings.user.ui.Get('showAggrRadius', 0), callback=self.OnDisplaySettingsChange)
        self.aggrSettingsAll = uicontrols.Checkbox(text='Show agression radius of all objects', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=settings.user.ui.Get('aggrSettingsAll', 0), callback=self.OnDisplaySettingsChange)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=7, parent=self.sr.panel)
        self.freeLookCheckbox = uicontrols.Checkbox(text='Free Look Camera', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=self._navigation.IsFreeLook(), callback=self.OnDisplaySettingsChange)
        uicontrols.EveLabelMedium(text='Free Look Camera Controls', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' CTRL + WASD - Moves forward, left, backwards, and right', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' CTRL + RF - Moves up and down', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' ALT + Left Mouse Button - Rotate camera around focus point', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' ALT + Middle Mouse Button - Moves camera focus point in screen space.', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' ALT + Right Mouse Button - Zooms camera in and out of focus point', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' Double Click on Object - Changes focus point to that object.', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text=' Can also use "Look At" to set the focus point to an object.', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        self.axisCheckbox = uicontrols.Checkbox(text='Draw Axis Lines', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=self._navigation.IsDrawingAxis(), callback=self.OnDisplaySettingsChange)
        self.gridCheckbox = uicontrols.Checkbox(text='Draw Grid Lines', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=self._navigation.IsGridEnabled(), callback=self.OnDisplaySettingsChange)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=7, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Palette Placement Grid', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        gridSizeOptions = [('20x20m', 20.0),
         ('200x200m', 200.0),
         ('2x2km', 2000.0),
         ('20x20km', 20000.0),
         ('200x200km', 200000.0)]
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=14, parent=self.sr.panel)
        self.gridSizeDropdown = uicontrols.Combo(parent=self.sr.panel, label='Grid Size', options=gridSizeOptions, name='', select=self._navigation.GetGridLength(), callback=self.OnDisplaySettingsChange, align=uiconst.TOTOP, adjustWidth=True)
        gridSpacingOptions = [('1x1m', 1.0),
         ('10x10m', 10.0),
         ('100x100m', 100.0),
         ('1x1km', 1000.0),
         ('10x10km', 10000.0)]
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=14, parent=self.sr.panel)
        self.gridSpacingDropdown = uicontrols.Combo(parent=self.sr.panel, label='Unit Size', options=gridSpacingOptions, name='', select=self._navigation.GetGridSpacing(), callback=self.OnDisplaySettingsChange, align=uiconst.TOTOP, adjustWidth=True)
        self.gridCheckbox = uicontrols.Checkbox(text='Hide Placement Grid when not in Palette View', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=settings.user.ui.Get('hidePlacementGrid', 0), callback=self.OnDisplaySettingsChange)
        uiprimitives.Container(name='pusher', align=uiconst.TOTOP, height=14, parent=self.sr.panel)
        uicontrols.EveLabelMedium(text='Free Look Camera must be enabled to use the placement grid.', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text='Red Axis Line = X Axis', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text='Green Axis Line = Y Axis', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        uicontrols.EveLabelMedium(text='Blue Axis Line = Z Axis', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)

    def OnDisplaySettingsChange(self, *args):
        desiredSpacingValue = self.gridSpacingDropdown.GetValue()
        settings.user.ui.Set('showAggrRadius', self.aggrSettings.GetValue())
        settings.user.ui.Set('aggrSettingsAll', self.aggrSettingsAll.GetValue())
        self._navigation.SetFreeLook(self.freeLookCheckbox.GetValue())
        settings.user.ui.Set('hidePlacementGrid', self.gridCheckbox.GetValue())
        self.hidePlacementGrid = self.gridCheckbox.GetValue()
        self._navigation.SetGridState(not self.hidePlacementGrid)
        self._navigation.SetDrawAxis(not self.hidePlacementGrid)
        self._navigation.SetGridSpacing(self.gridSpacingDropdown.GetValue())
        self._navigation.SetGridLength(self.gridSizeDropdown.GetValue())
        if desiredSpacingValue != self._navigation.GetGridSpacing():
            self.gridSpacingDropdown.SetValue(self._navigation.GetGridSpacing())
        sm.GetService('scenario').RefreshSelection()

    def OnSetCursorRadiusClicked(self, *args):
        minRadius = self.cursorMin.GetValue()
        maxRadius = self.cursorMax.GetValue()
        if maxRadius < minRadius:
            eve.Message('MinRadiusHigherThenMax')
            return
        settings.user.ui.Set('cursorMin', minRadius)
        settings.user.ui.Set('cursorMax', maxRadius)
        sm.GetService('scenario').RefreshSelection()

    def Load_tab4(self):
        comboOptions = [('combo_label1', 'combo_retval1'), ('combo_label2', 'combo_retval2')]
        comboID = 'det_comboID'
        comboSetval = settings.user.ui.Get(comboID, 'combo_retval1')
        uicontrols.Combo(label='', parent=self.sr.panel, options=comboOptions, name=comboID, select=comboSetval, callback=self.OnComboChange, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=self.sr.panel, align=uiconst.TOTOP, height=const.defaultPadding)
        uicontrols.EveLabelMedium(text='Label 1', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        scrollOptions = self.GetScrollOptions(comboSetval)
        scrollbox = uicontrols.Scroll(parent=self.sr.panel, name='scrollID', align=uiconst.TOTOP, height=256)
        scrollbox.LoadContent(contentList=scrollOptions)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='button label 1', func=self.OnClickButton, args=('btn1',), align=uiconst.TOLEFT)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='button label 1', func=self.OnClickButton, args=('btn1',), align=uiconst.TOLEFT, fixedwidth=128)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='button label 2', func=self.OnClickButton, args=('btn2',), align=uiconst.TOLEFT)
        uicontrols.Button(parent=row, label='button label 3', func=self.OnClickButton, args=('btn3',), align=uiconst.TOLEFT)
        grp = uicontrols.ButtonGroup(btns=[['Reset',
          self.OnClickButton,
          (),
          51], ['Reset',
          self.OnClickButton,
          (),
          51]], parent=self.sr.panel, line=0)
        grp.SetAlign(uiconst.TOTOP)
        checkbox1ID = 'det_checkbox1'
        checkbox1Setval = settings.user.ui.Get(checkbox1ID, 1)
        uicontrols.Checkbox(text='checkbox 1', parent=self.sr.panel, configName=checkbox1ID, retval=None, checked=checkbox1Setval, callback=self.OnCheckboxChange)
        radiobox1ID = 'det_radiobox1'
        radiobox1Setval = settings.user.ui.Get(radiobox1ID, 'radiobox1Retval')
        uicontrols.Checkbox(text='radiobox 1', parent=self.sr.panel, configName=radiobox1ID, retval='radiobox1Retval', checked='radiobox1Retval' == radiobox1Setval, groupname=radiobox1ID, callback=self.OnCheckboxChange)
        uicontrols.Checkbox(text='radiobox 2', parent=self.sr.panel, configName=radiobox1ID, retval='radiobox2Retval', checked='radiobox2Retval' == radiobox1Setval, groupname=radiobox1ID, callback=self.OnCheckboxChange)
        uicontrols.Checkbox(text='radiobox 3', parent=self.sr.panel, configName=radiobox1ID, retval='radiobox3Retval', checked='radiobox3Retval' == radiobox1Setval, groupname=radiobox1ID, callback=self.OnCheckboxChange)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='button label 1', func=self.OnClickButton, args=('btn1',), align=uiconst.TOLEFT)
        for each in 'XYZ':
            checkbox1ID = 'someID1_%s' % each
            checkbox1Setval = settings.user.ui.Get(checkbox1ID, 1)
            cb = uicontrols.Checkbox(text=each, parent=row, configName=checkbox1ID, retval=None, checked=checkbox1Setval, callback=self.OnCheckboxChange, align=uiconst.TOPLEFT, pos=(0, 0, 28, 0))

        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=16)
        uicontrols.Button(parent=row, label='button label 1', func=self.OnClickButton, args=('btn1',), align=uiconst.TOLEFT)
        for each in 'XYZ':
            checkbox1ID = 'someID2_%s' % each
            checkbox1Setval = settings.user.ui.Get(checkbox1ID, 1)
            cb = uicontrols.Checkbox(text=each, parent=row, configName=checkbox1ID, retval=None, checked=checkbox1Setval, callback=self.OnCheckboxChange, align=uiconst.TOPLEFT, pos=(0, 0, 28, 0))

        uicontrols.SinglelineEdit(name='someeditID', parent=row, setvalue=50, pos=(200, 0, 32, 0), ints=(1, 100))

    def GetScrollOptions(self, key):
        data = []
        if key == 'combo_retval1':
            data = [ ('1 label %s' % i, i) for i in xrange(100) ]
        elif key == 'combo_retval2':
            data = [ ('2 label %s' % i, i) for i in xrange(100) ]
        return [ listentry.Get('Generic', {'label': label,
         'id': id}) for label, id in data ]

    def OnGotoSelectedRoomClicked(self, entry, *args):
        settings.user.ui.Set('selectedRoomID', entry.sr.node.roomID)
        dungeonID = settings.user.ui.Get('dungeonDungeon', None)
        sm.ScatterEvent('OnSelectObjectInGame', 'SelectDungeonRoom', dungeonID=dungeonID, roomID=entry.sr.node.roomID)

    def OnComboChange(self, combo, newHeader, newValue, *args):
        settings.user.ui.Set(combo.name, newValue)
        self.sr.maintabs.ReloadVisible()
        if combo.name == 'dungeonDungeon':
            sm.ScatterEvent('OnSelectObjectInGame', 'SelectDungeon', dungeonID=newValue)

    def OnClickButton(self, *args):
        self.sr.maintabs.ReloadVisible()

    def OnCheckboxChange(self, checkbox, *args):
        config = checkbox.data['config']
        if checkbox.data.has_key('value'):
            if checkbox.data['value'] is None:
                settings.user.ui.Set(config, checkbox.checked)
            else:
                settings.user.ui.Set(config, checkbox.data['value'])

    def Load_TemplateTab(self):
        scrollOptions = []
        self.templateRows = sm.RemoteSvc('dungeon').DEGetTemplates()
        for row in self.templateRows:
            data = {'label': row.templateName,
             'hint': row.description != row.templateName and row.description or '',
             'id': row.templateID,
             'form': self}
            scrollOptions.append(listentry.Get('DungeonTemplateEntry', data))

        text = uicontrols.EveLabelMedium(text='Drag templates onto the grid to add their contents to the room', parent=self.sr.panel, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.sr.templatescroll = uicontrols.Scroll(name='scroll', parent=self.sr.panel, align=uiconst.TOALL)
        self.sr.templatescroll.Load(contentList=scrollOptions, scrolltotop=0)
        autoCreateGroupings = settings.user.ui.Get('dungeonTemplateGroupings', 1)
        checkbox = uicontrols.Checkbox(text='Automatically create grouping for added objects', parent=self.sr.panel, configName='dungeonTemplateGroupings', retval=None, checked=autoCreateGroupings, callback=self.OnCheckboxChange, align=uiconst.TOBOTTOM)
        self.sr.templatescroll.padBottom = checkbox.height + const.defaultPadding
        self.sr.templatescroll.multiSelect = 0

    def Load_PaletteTab(self):
        """
        Gets the palette data from the server and loads it up into the scroll
        """
        roomObjectGroups = sm.RemoteSvc('dungeon').DEGetRoomObjectPaletteData()
        kv = util.KeyVal()
        kv.groupItems = roomObjectGroups
        scrollOptions = self.GetGroupTypes(kv)
        self.sr.palettescroll = uicontrols.Scroll(name='scroll', parent=self.sr.panel, align=uiconst.TOALL)
        self.sr.palettescroll.Load(contentList=scrollOptions, scrolltotop=0)
        button = uicontrols.Button(parent=self.sr.panel, label='Add to Room', func=self.OnAddObjectToRoom, align=uiconst.TOBOTTOM)
        self.sr.palettescroll.padBottom = button.height + const.defaultPadding * 5
        self.sr.palettescroll.multiSelect = 0

    def GetGroupTypes(self, nodeData, *args):
        """
        Returns the scroll list data that is under the specified nodeData on the scroll
        The data is always being sorted by name
        """
        sublevel = nodeData.Get('sublevel', -1) + 1
        scrollOptions = []
        if type(nodeData.groupItems) == list:
            nodeData.groupItems.sort(lambda x, y: cmp(x[1], y[1]))
            for id, name in nodeData.groupItems:
                data = {'label': name,
                 'id': id,
                 'sublevel': sublevel}
                scrollOptions.append(listentry.Get('PaletteEntry', data))

        elif type(nodeData.groupItems) == dict:
            keys = nodeData.groupItems.keys()
            keys.sort(lambda x, y: cmp(x[1], y[1]))
            for key in keys:
                groupID, groupName = key
                data = {'label': groupName,
                 'id': ('group', groupID),
                 'groupItems': nodeData.groupItems[key],
                 'showlen': 1,
                 'sublevel': sublevel,
                 'GetSubContent': self.GetGroupTypes}
                scrollOptions.append(listentry.Get('Group', data))

        return scrollOptions

    def OnAddObjectToRoom(self, *args):
        """
        Perform some checks to make sure that we are actually editing a room and that we have something 
        selected in the scroll list. Then go ahead and add the object to the room.
        """
        if not self.sr.Get('palettescroll'):
            return
        scenarioSvc = sm.services['scenario']
        roomID = scenarioSvc.GetEditingRoomID()
        if roomID is None:
            sm.GetService('gameui').Say('You need to be editing a room to be able to add an object')
            return
        curSel = self.sr.palettescroll.GetSelected()
        if curSel:
            id = curSel[0].id
            name = curSel[0].label
        else:
            sm.GetService('gameui').Say('You need to select an object type from the palette before adding it to the room')
            return
        roomPos = scenarioSvc.GetEditingRoomPosition()
        ship = sm.services['michelle'].GetBall(eve.session.shipid)
        camera = sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True)
        objectX = ship.x - roomPos[0] + camera.parent.translation.x
        objectY = ship.y - roomPos[1] + camera.parent.translation.y
        objectZ = ship.z - roomPos[2] + camera.parent.translation.z
        dungeonHelper.CreateObject(roomID, id, name, objectX, objectY, objectZ, None, None, None, None)

    def OnDEObjectPaletteChanged(self):
        """
        If the dungeon room object palette list changes and if current tab is the palette tab, reload it.
        """
        if self.sr.Get('palettescroll') and self.sr.palettescroll is not None:
            self.UnloadPanel()
            self.Refresh()

    def _OnClose(self, *args):
        settings.user.ui.Set('actionMenuExpandTime', self.oldRadialMenuTime)
        uicore.layer.inflight.dungeonEditorSelectionEnabled = False
        self.scenario.ClearSelection()
        self._navigation.SetFreeLook(False)


class DungeonDragEntry(listentry.Generic):
    __guid__ = 'listentry.DungeonDragEntry'
    __nonpersistvars__ = []
    isDragObject = True
    DROPDISTANCE = 10000

    def GetDragData(self, *args):
        return self.sr.node.scroll.GetSelectedNodes(self.sr.node)

    def OnEndDrag(self, *args):
        uthread.new(self.OnEndDragFunc)

    def OnEndDragFunc(self):
        """
        When a palette entry is dragged onto space, we add that as a new object into the room that
        we are currently editing.
        """
        where = uicore.uilib.mouseOver
        if where and type(where) is uicls.InflightLayer:
            scenarioSvc = sm.services['scenario']
            roomID = scenarioSvc.GetEditingRoomID()
            if roomID is None:
                sm.GetService('gameui').Say('You need to be editing a room to be able to add an object')
                return
            proj, view, vp = uix.GetFullscreenProjectionViewAndViewport()
            ray, startingPosition = trinity.device.GetPickRayFromViewport(uicore.uilib.x, uicore.uilib.y, vp, view.transform, proj.transform)
            ray = trinity.TriVector(*ray)
            roomPos = scenarioSvc.GetEditingRoomPosition()
            ship = sm.services['michelle'].GetBall(eve.session.shipid)
            camera = sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True)
            cameraParent = sm.GetService('camera').GetCameraParent()
            cameraPosition = trinity.TriVector(ship.x - roomPos[0] + camera.pos[0], ship.y - roomPos[1] + camera.pos[1], ship.z - roomPos[2] + camera.pos[2])
            focusPoint = cameraParent.translation
            focusPoint = trinity.TriVector(ship.x - roomPos[0] + focusPoint[0], ship.y - roomPos[1] + focusPoint[1], ship.z - roomPos[2] + focusPoint[2])
            dist = (focusPoint.y - cameraPosition.y) / ray.y
            if dist < 0:
                sm.GetService('gameui').Say('This item can only be dragged onto the grid')
                return
            posInRoom = cameraPosition + ray * dist
            gridLength = sm.StartService('camera').dungeonHack.GetGridLength()
            minGrid = -gridLength / 2.0
            maxGrid = gridLength / 2.0
            if minGrid + focusPoint.x > posInRoom.x or maxGrid + focusPoint.x < posInRoom.x or minGrid + focusPoint.z > posInRoom.z or maxGrid + focusPoint.z < posInRoom.z:
                sm.GetService('gameui').Say('You can only drag Palette entries onto the grid')
                return
            self.DropIntoDungeonRoom(roomID, posInRoom)
        elif where and where.__guid__ not in (self.__guid__, 'form.DungeonEditor'):
            sm.GetService('gameui').Say('This item can only be dragged onto the grid')

    def DropIntoDungeonRoom(self, roomID, posInRoom):
        pass


class PaletteEntry(DungeonDragEntry):
    __guid__ = 'listentry.PaletteEntry'

    def DropIntoDungeonRoom(self, roomID, posInRoom):
        dungeonHelper.CreateObject(roomID, self.sr.node.id, self.sr.node.label, posInRoom.x, posInRoom.y, posInRoom.z, None, None, None, None)


class DungeonTemplateEntry(DungeonDragEntry):
    __guid__ = 'listentry.DungeonTemplateEntry'

    def DropIntoDungeonRoom(self, roomID, posInRoom):
        scenario = sm.GetService('scenario')
        dungeonEditorForm = self.sr.node.form
        objectIDs = sm.RemoteSvc('dungeon').AddTemplateObjects(roomID, self.sr.node.id, (posInRoom.x, posInRoom.y, posInRoom.z))
        scenario.WaitForObjectCreationByID(objectIDs)
        scenario.SetSelectionByID(objectIDs)
        if settings.user.ui.Get('dungeonTemplateGroupings', 1):
            groupName = dungeonEditorForm.CreateGroup(selectedObjSlimItems=[ slimItem for slimItem in scenario.GetDunObjects() if slimItem.dunObjectID in objectIDs ])
            sm.GetService('gameui').Say("Template objects successfully added (group '%s' created)" % groupName)
        else:
            sm.GetService('gameui').Say('Template objects successfully added')

    def GetMenu(self):
        return [('Edit details', self.OnEditDetails), ('Delete', self.OnDeleteTemplate)]

    def OnClick(self, *otherBits):
        sm.ScatterEvent('OnSelectObjectInGame', 'SelectDungeonTemplate', templateID=self.sr.node.id)

    def OnDeleteTemplate(self):
        dungeonEditorForm = self.sr.node.form
        indexedRows = dungeonEditorForm.templateRows.Index('templateID')
        row = indexedRows[self.sr.node.id]
        if row.userID != session.userid:
            sm.GetService('gameui').Say('Can only delete templates you have created yourself.<br>This template was created by: %s' % row.userName)
            return None
        if eve.Message('DeleteEntry', {}, uiconst.YESNO) == uiconst.ID_YES:
            sm.RemoteSvc('dungeon').TemplateRemove(self.sr.node.id)
            uthread.new(self.sr.node.form.Load, ('TemplateTab', None)).context = 'UI.DungeonEditor.OnDeleteTemplate'

    def OnEditDetails(self):
        dungeonEditorForm = self.sr.node.form
        indexedRows = dungeonEditorForm.templateRows.Index('templateID')
        row = indexedRows[self.sr.node.id]
        if row.userID != session.userid:
            sm.GetService('gameui').Say('Can only edit templates you have created yourself.<br>This template was created by: %s' % row.userName)
            return
        wnd = EditDungeonTemplateWindow.Open(templateRow=row, dungeonEditorForm=dungeonEditorForm)
        wnd.ShowModal()


class DungeonObjectProperties(uicontrols.Window):
    __guid__ = 'form.DungeonObjectProperties'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnBSDRevisionChange', 'OnDungeonObjectProperties', 'OnSelectObjectInGame']
    _windowHeight = 200
    default_windowID = 'dungeonObjectProperties'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'inflight'
        self.SetCaption('Object Properties')
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.width = 300
        self.height = self._windowHeight
        self.SetHeight(self._windowHeight)
        self.bsdTable = sm.StartService('bsdTable')
        self.inventoryTypesTable = self.bsdTable.GetTable('inventory', 'types')
        self.objectTable = self.bsdTable.GetTable('dungeon', 'objects')
        self.bsdTable.GetTable(localizationBSD.MessageText.__primaryTable__.tableName)
        self.bsdTable.GetTable(localizationBSD.Message.__primaryTable__.tableName)
        self.objectRow = None
        self.noObjects = uicontrols.EveLabelMedium(text='No Objects Selected', parent=self.sr.main, left=5, top=4, state=uiconst.UI_NORMAL)
        panel = uiprimitives.Container(name='panel', parent=self.sr.main, left=const.defaultPadding, top=const.defaultPadding, width=const.defaultPadding, height=const.defaultPadding)
        self.sr.panel = panel
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=18)
        uicontrols.EveLabelMedium(text='Selected:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        self.selectedCombo = uicontrols.Combo(label='', parent=row, options=(('Nothing', 0),), name='combo', select=0, callback=self.OnComboChange, pos=(80, 0, 0, 0), align=uiconst.TOPLEFT)
        self.selectedCombo.width = 202
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='Object Name:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        self.objectName = uicontrols.SinglelineEdit(name='objectName', parent=row, setvalue='', pos=(80, 0, 202, 16))
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='Object Type:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        self.objectType = uicontrols.EveLabelMedium(text='', parent=row, left=80, top=4, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='Quantity:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        self.quantity = uicontrols.SinglelineEdit(name='quantity', parent=row, setvalue=0, pos=(80, 0, 202, 0), ints=(0, sys.maxint))
        self.oldQuantity = 0
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='Radius:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        self.radius = uicontrols.SinglelineEdit(name='radius', parent=row, setvalue=0, pos=(80, 0, 202, 16), ints=(0, sys.maxint))
        self.oldRadius = 0
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='Position:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        for i, each in enumerate('XYZ'):
            editId = 'position%s' % each
            curVal = 0
            editBox = uicontrols.SinglelineEdit(name=editId, parent=row, setvalue=0, pos=(80 + i * 69,
             0,
             64,
             16), floats=(-100000.0, 100000.0))
            setattr(self, editId, editBox)

        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='Rotation:', parent=row, left=2, top=4, state=uiconst.UI_NORMAL)
        for i, each in enumerate(['Yaw', 'Pitch', 'Roll']):
            editId = 'rotation%s' % each
            curVal = 0
            editBox = uicontrols.SinglelineEdit(name=editId, parent=row, setvalue=0, pos=(80 + i * 69,
             0,
             64,
             16), floats=(-100000.0, 100000.0))
            setattr(self, editId, editBox)

        spacer = uiprimitives.Container(name='spacer', parent=self.sr.panel, align=uiconst.TOTOP, height=5)
        uiprimitives.Line(parent=self.sr.panel, align=uiconst.TOTOP)
        spacer = uiprimitives.Container(name='spacer', parent=self.sr.panel, align=uiconst.TOTOP, height=5)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.Button(parent=row, label='Change Type', func=self.OnChangeType, align=uiconst.TOLEFT).width = 87
        uicontrols.Button(parent=row, label='Save', func=self.OnSave, align=uiconst.TOLEFT).width = 87
        uicontrols.Button(parent=row, label='Revert', func=self.OnRevert, align=uiconst.TOLEFT).width = 87
        self.scenario = sm.StartService('scenario')
        self.OnSelectObjectInGame('SelectDungeonObject')
        self.Show()

    def LoadObjectID(self, objectID = None):
        if objectID is None:
            self.sr.panel.state = uiconst.UI_HIDDEN
            self.noObjects.state = uiconst.UI_DISABLED
            self.objectRow = None
            self.SetCaption('Object Properties')
            return
        self.ShowLoad()
        self.objectRow = self.objectTable.GetRowByKey(objectID)
        if self.objectRow is None:
            self.sr.panel.state = uiconst.UI_HIDDEN
            self.noObjects.state = uiconst.UI_DISABLED
            self.objectRow = None
            self.HideLoad()
            return
        self.sr.panel.state = uiconst.UI_PICKCHILDREN
        self.noObjects.state = uiconst.UI_HIDDEN
        self.SetHeight(self._windowHeight)
        self.UpdateDisplay()

    def UpdateDisplay(self):
        self.ShowLoad()
        self.SetCaption('Object Properties: %d' % self.objectRow.objectID)
        objectName = ''
        if self.objectRow.objectNameID is not None:
            objectName = GetMessageFromLocalization(self.objectRow.objectNameID)
        self.objectName.SetValue(objectName)
        typeRow = self.inventoryTypesTable.GetRowByKey(self.objectRow.typeID)
        if typeRow:
            typeName = typeRow.typeName
        else:
            typeName = '<No Type Set>'
        self.objectType.text = typeName
        quantity = dungeonHelper.GetObjectQuantity(self.objectRow.objectID)
        if quantity is None:
            self.quantity.integermode = None
            self.quantity.SetValue('Quantity Invalid For This Type')
            self.quantity.state = uiconst.UI_DISABLED
        else:
            self.quantity.integermode = (0, sys.maxint)
            self.quantity.state = uiconst.UI_NORMAL
            self.quantity.SetValue(int(quantity))
            self.oldQuantity = int(quantity)
        radius = dungeonHelper.GetObjectRadius(self.objectRow.objectID)
        if radius is None:
            self.radius.integermode = None
            self.radius.SetValue('Radius Invalid For This Type')
            self.radius.state = uiconst.UI_DISABLED
        else:
            self.radius.integermode = (0, sys.maxint)
            self.radius.state = uiconst.UI_NORMAL
            self.radius.SetValue(int(radius))
            self.oldRadius = int(radius)
        x, y, z = dungeonHelper.GetObjectPosition(self.objectRow.objectID)
        self.positionX.SetValue(x)
        self.positionY.SetValue(y)
        self.positionZ.SetValue(z)
        yaw, pitch, roll = dungeonHelper.GetObjectRotation(self.objectRow.objectID)
        self.rotationYaw.SetValue(yaw)
        self.rotationPitch.SetValue(pitch)
        self.rotationRoll.SetValue(roll)
        self.HideLoad()

    def OnSelectObjectInGame(self, selectType, *args, **kwargs):
        if selectType == 'SelectDungeonObject':
            self._HandleSelection(self.scenario.GetSelectedObjIDs())

    def _HandleSelection(self, objectIds):
        if objectIds:
            scenarioSvc = sm.StartService('scenario')
            for objectID in objectIds:
                ball, slimItem = scenarioSvc.GetBallAndSlimItemFromObjectID(objectID)
                sleepTime = 0
                while ball is None or slimItem is None and sleepTime < 5000:
                    sleepTime += 200
                    blue.synchro.SleepWallclock(200)
                    ball, slimItem = scenarioSvc.GetBallAndSlimItemFromObjectID(objectID)

                if ball is None or slimItem is None:
                    sm.StartService('scenario').LogError('DungeonObjectProperties._HandleSelection could not load balls and slimItems')

            if self.objectRow is None or self.objectRow.objectID not in objectIds:
                self.LoadObjectID(objectIds[0])
            options = []
            for objectId in objectIds:
                objectRow = self.objectTable.GetRowByKey(objectId)
                typeRow = self.inventoryTypesTable.GetRowByKey(objectRow.typeID)
                name = '%s(%d)' % (typeRow.typeName, objectId)
                options.append((name, objectId))

            self.selectedCombo.LoadOptions(options, select=self.objectRow.objectID)
        else:
            self.LoadObjectID()

    def OnBSDRevisionChange(self, action, schemaName, tableName, rowKeys, columnValues, reverting, _source = 'local'):
        if schemaName == 'dungeon' and tableName == 'objectsTx' and self.objectRow and self.objectRow.objectID == rowKeys[0]:
            self.UpdateDisplay()

    def OnDungeonObjectProperties(self, objectID):
        if self.objectRow and objectID == self.objectRow.objectID:
            self.UpdateDisplay()

    def OnChangeType(self, *args, **kwargs):
        ObjectTypeChooser.Open(objectRow=self.objectRow)

    def OnSave(self, *args, **kwargs):
        dungeonID = settings.user.ui.Get('dungeonDungeon', None)
        if dungeonID is None or dungeonID == 'All':
            return
        selDungeon = sm.RemoteSvc('dungeon').DEGetDungeons(dungeonID=dungeonID)[0]
        dungeonNameID = selDungeon.dungeonNameID
        if dungeonNameID is not None:
            dungeonName = GetMessageFromLocalization(dungeonNameID)
        else:
            dungeonName = selDungeon.dungeonName
        quantity = self.quantity.GetValue()
        if quantity != 'Quantity Invalid For This Type' and quantity != self.oldQuantity:
            self.oldQuantity = quantity
            dungeonHelper.SetObjectQuantity(self.objectRow.objectID, quantity)
        radius = self.radius.GetValue()
        if radius != 'Radius Invalid For This Type' and radius != self.oldRadius:
            self.oldRadius = radius
            dungeonHelper.SetObjectRadius(self.objectRow.objectID, radius)
        x = self.positionX.GetValue()
        y = self.positionY.GetValue()
        z = self.positionZ.GetValue()
        dungeonHelper.SetObjectPosition(self.objectRow.objectID, x, y, z)
        yaw = self.rotationYaw.GetValue()
        pitch = self.rotationPitch.GetValue()
        roll = self.rotationRoll.GetValue()
        dungeonHelper.SetObjectRotation(self.objectRow.objectID, yaw, pitch, roll)
        objectName = self.objectName.GetValue()
        if not objectName:
            if self.objectRow.objectNameID:
                localizationBSD.MessageText.Get(self.objectRow.objectNameID).text = ''
            objectName = None
        if objectName is not None:
            objectNameID = self.objectRow.objectNameID
            if objectNameID is not None and objectName == GetMessageFromLocalization(objectNameID):
                return
            if objectNameID is not None and unicode(objectNameID) in objectName:
                msgText = 'Do you really want to name this object %s?'
                msgText += " Selecting 'No' will save other changes you have made to the object, but will not change the name."
                ret = eve.Message('CustomQuestion', {'header': 'Rename Object?',
                 'question': msgText % objectName}, uiconst.YESNO)
                if ret == uiconst.ID_NO:
                    return
            import localizationBSD.localizationTableToMessageUtil as messageUtil
            self.objectRow.objectNameID = messageUtil.UpdateMessage('DUNGEON-OBJECTS', dungeonID, objectNameID, objectName, 'dungeon.objects', 'objectNameID', self.objectRow.revisionID, None, dungeonID, dungeonName)
        self.UpdateDisplay()

    def OnRevert(self, *args, **kwargs):
        self.UpdateDisplay()

    def OnComboChange(self, *args, **kwargs):
        selected = self.selectedCombo.GetValue()
        if selected != self.objectRow.objectID:
            self.LoadObjectID(selected)


class ObjectTypeChooser(uicontrols.Window):

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        objectRow = attributes.objectRow
        self.scope = 'inflight'
        self.SetCaption('Object Type Chooser - %d' % objectRow.objectID)
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.SetMinSize([350, 400])
        self.objectRow = objectRow
        panel = uiprimitives.Container(name='panel', parent=self.sr.main, left=const.defaultPadding, top=const.defaultPadding, width=const.defaultPadding, height=const.defaultPadding)
        self.sr.panel = panel
        roomObjectGroups = sm.RemoteSvc('dungeon').DEGetRoomObjectPaletteData()
        kv = util.KeyVal()
        kv.groupItems = roomObjectGroups
        scrollOptions = self.GetGroupTypes(kv)
        self.sr.palettescroll = uicontrols.Scroll(name='scroll', parent=self.sr.panel, align=uiconst.TOALL)
        self.sr.palettescroll.Load(contentList=scrollOptions, scrolltotop=0)
        button = uicontrols.Button(parent=self.sr.panel, label='Change Type', func=self.OnChangeType, align=uiconst.TOBOTTOM)
        self.sr.palettescroll.padBottom = const.defaultPadding * 7
        self.sr.palettescroll.multiSelect = 0
        self.Show()

    def OnChangeType(self, *args, **kwargs):
        curSel = self.sr.palettescroll.GetSelected()
        if curSel:
            id = curSel[0].id
            name = curSel[0].label
        else:
            sm.GetService('gameui').Say('You need to select an object type from the chooser before you can change the object type')
            return
        self.objectRow.typeID = id

    def GetGroupTypes(self, nodeData, *args):
        """
        Returns the scroll list data that is under the specified nodeData on the scroll
        The data is always being sorted by name
        """
        sublevel = nodeData.Get('sublevel', -1) + 1
        scrollOptions = []
        if type(nodeData.groupItems) == list:
            nodeData.groupItems.sort(lambda x, y: cmp(x[1], y[1]))
            for id, name in nodeData.groupItems:
                data = {'label': name,
                 'id': id,
                 'sublevel': sublevel}
                scrollOptions.append(listentry.Get('PaletteEntry', data))

        elif type(nodeData.groupItems) == dict:
            keys = nodeData.groupItems.keys()
            keys.sort(lambda x, y: cmp(x[1], y[1]))
            for key in keys:
                groupID, groupName = key
                data = {'label': groupName,
                 'id': ('group', groupID),
                 'groupItems': nodeData.groupItems[key],
                 'showlen': 1,
                 'sublevel': sublevel,
                 'GetSubContent': self.GetGroupTypes}
                scrollOptions.append(listentry.Get('Group', data))

        return scrollOptions


class ObjectGroupListEntry(listentry.Generic):
    __guid__ = 'listentry.ObjectGroupListEntry'
    __nonpersistvars__ = []

    def Startup(self, *args):
        listentry.Generic.Startup(self, args)
        self.sr.lock = uicontrols.Icon(icon='ui_22_32_30', parent=self, size=24, align=uiconst.CENTERRIGHT, state=uiconst.UI_HIDDEN, hint='You can not change this shortcut')

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.form = node.form
        self.sr.isLocked = node.locked
        self.sr.lock.state = [uiconst.UI_HIDDEN, uiconst.UI_NORMAL][node.locked]

    def GetMenu(self):
        if self.sr.isLocked:
            return []
        m = [('Rename Group', self.RenameGroup), ('Remove Group', self.RemoveGroup), ('Delete Group Objects', self.DeleteGroupObjects)]
        return m

    def OnDblClick(self, *args):
        if not self.sr.isLocked:
            self.RenameGroup()

    def RenameGroup(self):
        self.Deselect()
        self.sr.form.OpenRenameGroupDialog(key=self.sr.label.text)

    def RemoveGroup(self):
        self.Deselect()
        self.sr.form.RemoveGroup(self.sr.label.text)

    def DeleteGroupObjects(self):
        self.Deselect()
        uthread.new(self.sr.form.DeleteGroup, self.sr.label.text).context = 'svc.scenario.OnDeleteSelected'

    def RefreshCallback(self, *args):
        if self.sr.node.Get('refreshcallback', None):
            self.sr.node.refreshcallback()


class CreateDungeonTemplateWindow(uicontrols.Window):
    default_windowID = 'dungeonTemplateCreator'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetScope('station_inflight')
        self.SetCaption('Create Template')
        self.MakeUnResizeable()
        self.SetMinSize([300, 280], 1)
        self.SetTopparentHeight(64)
        self.MakeUnpinable()
        self.HideHeader()
        newCaption = uicontrols.CaptionLabel(text='Create Template', parent=self.sr.topParent, align=uiconst.CENTERLEFT, left=70)
        outerPanel = uiprimitives.Container(name='panel', parent=self.sr.main, left=const.defaultPadding, top=const.defaultPadding, width=const.defaultPadding, height=const.defaultPadding)
        panel = uiprimitives.Container(name='subpar', parent=outerPanel, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.panel = outerPanel
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='NAME', parent=row, left=6, top=8, state=uiconst.UI_NORMAL)
        self.templateName = uicontrols.SinglelineEdit(name='templateName', parent=row, setvalue='', pos=(60, 8, 202, 16))
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='DESCRIPTION', parent=row, left=6, top=8, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=self.sr.topParent.height)
        self.templateDescription = uicls.EditPlainText(setvalue='', parent=row, top=8, align=uiconst.TOALL)
        self.DefineButtons(uiconst.OKCANCEL, okLabel='Submit', okFunc=self.OnSubmit)
        uicontrols.Frame(parent=panel)

    def OnSubmit(self, someValue):
        templateName = self.templateName.GetValue().strip()
        if not len(templateName):
            sm.GetService('gameui').Say('Please enter a template name')
            return
        templateDescription = self.templateDescription.GetValue(html=0).strip()
        if not len(templateDescription):
            sm.GetService('gameui').Say('Please enter a template description')
            return
        selObjs = sm.GetService('scenario').GetSelObjects()
        objectIDList = [ slimItem.dunObjectID for slimItem in selObjs if slimItem.dunObjectID ]
        if not len(objectIDList):
            sm.GetService('gameui').Say('You need to select objects for the template')
            return
        sm.GetService('gameui').Say('Creating the template with %d objects' % len(objectIDList))
        dungeonSvc = sm.RemoteSvc('dungeon')
        templateID = dungeonSvc.TemplateAdd(templateName, templateDescription)
        dungeonSvc.TemplateObjectAddDungeonList(templateID, objectIDList)
        sm.GetService('gameui').Say('Created the template')
        self.Close()

    def _OnClose(self, *args):
        pass


class EditDungeonTemplateWindow(uicontrols.Window):
    default_windowID = 'dungeonTemplateDetailEditor'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        templateRow = attributes.templateRow
        dungeonEditorForm = attributes.dungeonEditorForm
        self.templateRow = templateRow
        self.dungeonEditorForm = dungeonEditorForm
        self.sr.main = uiutil.GetChild(self, 'main')
        self.SetScope('station_inflight')
        self.SetCaption('EDIT')
        self.MakeUnResizeable()
        self.SetMinSize([300, 280], 1)
        self.SetTopparentHeight(64)
        self.MakeUnpinable()
        self.HideHeader()
        newCaption = uicontrols.CaptionLabel(text='EDIT', parent=self.sr.topParent, align=uiconst.CENTERLEFT, left=70)
        outerPanel = uiprimitives.Container(name='panel', parent=self.sr.main, left=const.defaultPadding, top=const.defaultPadding, width=const.defaultPadding, height=const.defaultPadding)
        panel = uiprimitives.Container(name='subpar', parent=outerPanel, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.panel = outerPanel
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='NAME', parent=row, left=6, top=8, state=uiconst.UI_NORMAL)
        self.templateName = uicontrols.SinglelineEdit(name='templateName', parent=row, setvalue=templateRow.templateName, pos=(60, 8, 202, 16))
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=20)
        uicontrols.EveLabelMedium(text='DESCRIPTION', parent=row, left=6, top=8, state=uiconst.UI_NORMAL)
        row = uiprimitives.Container(name='row', parent=self.sr.panel, align=uiconst.TOTOP, height=self._windowHeight)
        self.templateDescription = uicls.EditPlainText(setvalue=templateRow.description, parent=row, top=8, align=uiconst.TOALL)
        self.DefineButtons(uiconst.OKCANCEL, okLabel='Submit', okFunc=self.OnSubmit)
        uicontrols.Frame(parent=panel, state=uiconst.UI_PICKCHILDREN)

    def OnSubmit(self, someValue):
        templateName = self.templateName.GetValue().strip()
        if not len(templateName):
            sm.GetService('gameui').Say('Please enter a template name')
            return None
        templateDescription = self.templateDescription.GetValue(html=0).strip()
        if not len(templateDescription):
            sm.GetService('gameui').Say('Please enter a template description')
            return None
        dungeonSvc = sm.RemoteSvc('dungeon')
        dungeonSvc.TemplateEdit(self.templateRow.templateID, templateName, templateDescription)
        uthread.new(self.dungeonEditorForm.Load, ('TemplateTab', None)).context = 'UI.DungeonEditor.OnEditTemplateDetails'
        self.Close()

    def _OnClose(self, *args):
        pass


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('dungeonEditorTools', locals())
