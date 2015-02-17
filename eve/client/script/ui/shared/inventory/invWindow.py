#Embedded file name: eve/client/script/ui/shared/inventory\invWindow.py
from math import pi
import blue
import bracketUtils
from carbonui.primitives.container import Container
from carbonui.util.various_unsorted import IsUnder
import const
from eve.client.script.ui.control.eveWindowUnderlay import ListEntryUnderlay
from eve.client.script.ui.control.historyBuffer import HistoryBuffer
from eve.client.script.ui.control.themeColored import FillThemeColored
from eve.client.script.ui.shared.inventory.treeData import TreeDataInv, TreeDataInvFolder, GetTreeDataClassByInvName
from eve.client.script.ui.shared.inventory.treeViewEntries import GetTreeViewEntryClassByDataType
import invCtrl
import localization
import service
import state
import telemetry
import uicls
import carbonui.const as uiconst
import uicontrols
import uiprimitives
import uthread
import util
import blue
import invCtrl
import uthread
import localization
import state
import service
import telemetry
import bracketUtils
import invCont
import uix
from spacecomponents.common.componentConst import CARGO_BAY
from spacecomponents.common.helper import HasCargoBayComponent
from eve.client.script.ui.control.historyBuffer import HistoryBuffer
from eve.client.script.ui.shared.inventory.invCommon import CONTAINERGROUPS
HISTORY_LENGTH = 50
TREE_DEFAULT_WIDTH = 160

class Inventory(uicontrols.Window):
    __guid__ = 'form.Inventory'
    __notifyevents__ = ['OnSessionChanged',
     'OnItemNameChange',
     'OnMultipleItemChange',
     'ProcessActiveShipChanged',
     'OnBeforeActiveShipChanged',
     'OnOfficeRentalChanged',
     'OnStateChange',
     'OnInvContDragEnter',
     'OnInvContDragExit',
     'DoBallsAdded',
     'DoBallRemove',
     'ProcessTempInvLocationAdded',
     'ProcessTempInvLocationRemoved',
     'OnSlimItemChange',
     'OnInvFiltersChanged',
     'OnInvContRefreshed',
     'OnCapacityChange',
     'OnWreckLootAll',
     'OnShowFullInvTreeChanged',
     'DoBallsRemove']
    default_windowID = ('Inventory', None)
    default_width = 600
    default_height = 450
    default_topParentHeight = 0
    default_minSize = (100, 140)
    default_iconNum = 'res:/UI/Texture/WindowIcons/items.png'
    default_isCompactable = True
    default_caption = None

    def ApplyAttributes(self, attributes):
        self.currInvID = attributes.Get('invID', None)
        self.rootInvID = attributes.Get('rootInvID', self.currInvID)
        self.invController = invCtrl.GetInvCtrlFromInvID(self.currInvID)
        uicontrols.Window.ApplyAttributes(self, attributes)
        sm.GetService('inv').Register(self)
        self.treeEntryByID = {}
        self.tempTreeEntryByID = {}
        self.dragHoverThread = None
        self.refreshTreeThread = None
        self.updateSelectedItemsThread = None
        self.updateSelectedItemsPending = None
        self.invCont = None
        self.filterEntries = []
        self.loadingTreeView = False
        self.loadingInvCont = False
        self.dragOpenNewWindowCookie = None
        self.treeData = None
        self.treeDataTemp = None
        self.containersInRangeUpdater = None
        self.history = HistoryBuffer(HISTORY_LENGTH)
        self.breadcrumbInvIDs = []
        if session.stationid2:
            invCtrl.StationItems().GetItems()
        self.dividerCont = uicontrols.DragResizeCont(name='dividerCont', settingsID='invTreeViewWidth_%s' % self.GetWindowSettingsID(), parent=self.sr.main, align=uiconst.TOLEFT, minSize=50, defaultSize=TREE_DEFAULT_WIDTH, clipChildren=True, onResizeCallback=self.OnDividerContResize, padLeft=4)
        uthread.new(self.OnDividerContResize)
        self.treeTopCont = uiprimitives.Container(name='treeTopCont', parent=self.dividerCont.mainCont, align=uiconst.TOTOP, height=20, padBottom=1)
        uiprimitives.Line(parent=self.treeTopCont, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.1))
        uiprimitives.Fill(parent=self.treeTopCont, color=(0.5, 0.5, 0.5, 0.1))
        uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.treeTopCont, align=uiconst.CENTERLEFT, GetUtilMenu=self.InventorySettings, texturePath='res:/UI/Texture/SettingsCogwheel.png', iconSize=18, pos=(4, 0, 18, 18))
        uicontrols.Label(parent=self.treeTopCont, text=localization.GetByLabel('UI/Inventory/Index'), align=uiconst.CENTERLEFT, left=22, color=(0.5, 0.5, 0.5, 1.0))
        self.treeBottomCont = uicontrols.DragResizeCont(name='treeBottomCont', parent=self.dividerCont.mainCont, settingsID='invFiltersHeight_%s' % self.GetWindowSettingsID(), align=uiconst.TOBOTTOM, state=uiconst.UI_PICKCHILDREN, minSize=100, maxSize=0.5, defaultSize=150, padBottom=4)
        self.filterHeaderCont = uiprimitives.Container(name='filterHeaderCont', parent=self.treeBottomCont, align=uiconst.TOTOP, height=22, state=uiconst.UI_NORMAL)
        self.filterHeaderCont.OnDblClick = self.OnExpandFiltersBtn
        FillThemeColored(bgParent=self.filterHeaderCont, colorType=uiconst.COLORTYPE_UIHEADER)
        filtersEnabledBtn = uiprimitives.Container(name='filtersEnabledBtn', parent=self.filterHeaderCont, align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, width=24, pickRadius=7)
        self.createFilterBtn = uicontrols.ButtonIcon(name='createFilterBtn', parent=self.filterHeaderCont, align=uiconst.TORIGHT, width=self.filterHeaderCont.height, iconSize=9, texturePath='res:/UI/Texture/Icons/Plus.png', func=self.OnCreateFilterBtn)
        filtersEnabledBtn.OnClick = self.OnFiltersEnabledBtnClicked
        self.filtersEnabledBtnColor = uiprimitives.Sprite(bgParent=filtersEnabledBtn, texturePath='res:/UI/Texture/CharacterCreation/radiobuttonColor.dds', color=(0, 1.0, 0, 0.0))
        uiprimitives.Sprite(bgParent=filtersEnabledBtn, texturePath='res:/UI/Texture/CharacterCreation/radiobuttonBack.dds', opacity=0.4)
        uiprimitives.Sprite(bgParent=filtersEnabledBtn, texturePath='res:/UI/Texture/CharacterCreation/radiobuttonShadow.dds', color=(0.4, 0.4, 0.4, 0.4))
        labelCont = uiprimitives.Container(name='labelCont', parent=self.filterHeaderCont, clipChildren=True)
        uicontrols.Label(left=22, parent=labelCont, text=localization.GetByLabel('UI/Inventory/MyFilters'), align=uiconst.CENTERLEFT)
        self.expandFiltersBtn = uicontrols.ButtonIcon(name='expandFiltersBtn', parent=labelCont, align=uiconst.TOLEFT, iconSize=7, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', width=22, func=self.OnExpandFiltersBtn)
        self.filterCont = uicls.ScrollContainer(name='filterCont', parent=self.treeBottomCont, align=uiconst.TOALL, height=0.2, showUnderlay=True)
        uicontrols.GradientSprite(bgParent=self.filterCont, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.2), (0.7, 0.2), (0.9, 0)])
        self.tree = uicls.ScrollContainer(name='tree', parent=self.dividerCont.mainCont, padTop=1, showUnderlay=True)
        self.tree.GetMenu = self.GetMenu
        uicontrols.GradientSprite(bgParent=self.tree, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.2), (0.7, 0.2), (0.9, 0)])
        self.tree.Paste = self.Paste
        self.rightCont = uiprimitives.Container(name='rightCont', parent=self.sr.main, padRight=const.defaultPadding, clipChildren=True)
        self.noInventoryLabel = uicontrols.EveCaptionMedium(name='noInventoryLabel', parent=self.rightCont, state=uiconst.UI_HIDDEN, text=localization.GetByLabel('UI/Inventory/NoInventoryLocationSelected'), pos=(17, 78, 0, 0), opacity=0.5)
        self.topRightCont1 = uiprimitives.Container(name='topRightcont1', parent=self.rightCont, align=uiconst.TOTOP, height=20, clipChildren=True)
        uiprimitives.Line(parent=self.topRightCont1, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.1), padLeft=-4)
        uicontrols.GradientSprite(parent=self.topRightCont1, align=uiconst.TOALL, state=uiconst.UI_DISABLED, rgbData=[(0, (0.5, 0.5, 0.5))], alphaData=[(0, 0.0), (0.1, 0.1)])
        self.topRightCont2 = uiprimitives.Container(name='topRightCont2', parent=self.rightCont, align=uiconst.TOTOP, height=24, padBottom=1, clipChildren=True)
        self.bottomRightCont = uiprimitives.Container(name='bottomRightcont', parent=self.rightCont, align=uiconst.TOBOTTOM, height=40, clipChildren=True)
        self.specialActionsCont = uicontrols.ContainerAutoSize(name='specialActionsCont', parent=self.bottomRightCont, align=uiconst.TOLEFT, padding=(1, 10, 2, 10))
        self.bottomRightLabelCont = uiprimitives.Container(name='bottomRightLabelCont', parent=self.bottomRightCont, clipChildren=True)
        self.expandTreeBtn = uicontrols.ButtonIcon(name='expandTreeBtn', parent=self.topRightCont1, align=uiconst.TOLEFT, width=20, iconSize=7, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', func=self.OnExpandTreeBtn)
        cont = uiprimitives.Container(parent=self.topRightCont1, clipChildren=True)
        self.viewBtns = uicls.InvContViewBtns(parent=cont, top=2, align=uiconst.TORIGHT, controller=self)
        self.goForwardBtn = uicontrols.ButtonIcon(name='goForwardBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=16, padRight=5, texturePath='res:/UI/Texture/icons/38_16_224.png', func=self.OnForward, hint=localization.GetByLabel('UI/Control/EveWindow/Next'))
        self.goBackBtn = uicontrols.ButtonIcon(name='goBackBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=16, texturePath='res:/UI/Texture/icons/38_16_223.png', func=self.OnBack, hint=localization.GetByLabel('UI/Control/EveWindow/Previous'))
        self.UpdateHistoryButtons()
        self.subCaptionCont = uiprimitives.Container(name='subCaptionCont', parent=cont, clipChildren=True)
        self.subCaptionLabel = uicontrols.Label(name='subCaptionLabel', parent=self.subCaptionCont, align=uiconst.CENTERLEFT, fontsize=11, state=uiconst.UI_NORMAL)
        self.subCaptionLabel.isDragObject = False
        self.subCaptionCont._OnResize = self.UpdateSubCaptionLabel
        self.quickFilter = uicls.InvContQuickFilter(parent=self.topRightCont2, align=uiconst.TORIGHT, width=120)
        self.capacityGauge = uicls.InvContCapacityGauge(parent=self.topRightCont2, align=uiconst.TOALL, padding=(2, 5, 4, 4))
        self.totalPriceLabel = uicontrols.Label(name='totalPriceLabel', parent=self.bottomRightLabelCont, align=uiconst.BOTTOMRIGHT, left=5, top=4)
        self.numItemsLabel = uicontrols.Label(name='numItemsLabel', parent=self.bottomRightLabelCont, align=uiconst.BOTTOMRIGHT, left=5, top=20)
        isExpanded = self.IsInvTreeExpanded(getDefault=False)
        self.isTreeExpandedStateDetermined = False if isExpanded is None else True
        if not isExpanded:
            self.CollapseTree(animate=False)
        else:
            self.ExpandTree(animate=False)
        if not settings.user.ui.Get('invFiltersExpanded_%s' % self.GetWindowSettingsID(), False):
            self.CollapseFilters(animate=False)
        else:
            self.ExpandFilters(animate=False)
        if not self.currInvID:
            self.currInvID = settings.user.ui.Get('invLastOpenContainerData_%s' % self.GetWindowSettingsID(), None)
        self.ShowInvContLoadingWheel()
        uthread.new(self.ConstructFilters)
        uthread.new(self.RefreshTree)

    def InventorySettings(self, menuParent):
        openSecondary = settings.user.ui.Get('openSecondaryInv', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Inventory/AlwaysOpenSeparate'), checked=openSecondary, callback=(self.OnSettingChangedSecondaryWnd, not openSecondary))
        keepQuickFilterInput = settings.user.ui.Get('keepInvQuickFilterInput', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Inventory/KeepQuickFilterValue'), checked=keepQuickFilterInput, callback=(self.OnSettingChangedKeepQuickFilter, not keepQuickFilterInput))
        alwaysShowFullTree = settings.user.ui.Get('alwaysShowFullInvTree', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Inventory/AlwaysShowFullTree'), checked=alwaysShowFullTree, callback=(self.OnSettingChangedAlwaysShowFullTree, not alwaysShowFullTree))

    def OnSettingChangedSecondaryWnd(self, openSecondary, *args):
        settings.user.ui.Set('openSecondaryInv', openSecondary)

    def OnSettingChangedKeepQuickFilter(self, keepQuickFilterInput, *args):
        settings.user.ui.Set('keepInvQuickFilterInput', keepQuickFilterInput)

    def OnSettingChangedAlwaysShowFullTree(self, alwaysShowFullTree, *args):
        settings.user.ui.Set('alwaysShowFullInvTree', alwaysShowFullTree)
        sm.ScatterEvent('OnShowFullInvTreeChanged')

    def OnShowFullInvTreeChanged(self):
        self.RefreshTree()

    def GetRegisteredPositionAndSize(self):
        return self.GetRegisteredPositionAndSizeByClass(self.windowID)

    def RegisterPositionAndSize(self, key = None, windowID = None):
        windowID = self.windowID[0]
        uicontrols.Window.RegisterPositionAndSize(self, key, windowID)

    def OnCreateFilterBtn(self, *args):
        sm.GetService('itemFilter').CreateFilter()

    def ShowTreeLoadingWheel(self):
        if self.loadingTreeView:
            return
        self.loadingTreeView = True
        uthread.new(self._ShowTreeLoadingWheel)

    def _ShowTreeLoadingWheel(self):
        blue.synchro.SleepWallclock(500)
        wheelCont = uiprimitives.Container(parent=self.dividerCont.mainCont)
        uicls.LoadingWheel(parent=wheelCont, align=uiconst.CENTER)
        while self.loadingTreeView:
            blue.synchro.Yield()

        wheelCont.Close()

    def HideTreeLoadingWheel(self):
        self.loadingTreeView = False

    def ShowInvContLoadingWheel(self):
        if self.loadingInvCont:
            return
        self.loadingInvCont = True
        uthread.new(self._ShowInvContLoadingWheel)

    def _ShowInvContLoadingWheel(self):
        blue.synchro.SleepWallclock(500)
        wheel = uicls.LoadingWheel(parent=self.rightCont, align=uiconst.CENTER)
        while self.loadingInvCont:
            blue.synchro.Yield()

        wheel.Close()

    def HideInvContLoadingWheel(self):
        self.loadingInvCont = False

    def OnInvFiltersChanged(self):
        self.ConstructFilters()
        self.UpdateFilters()

    @telemetry.ZONE_METHOD
    def ConstructFilters(self):
        for filterEntry in self.filterEntries:
            filterEntry.Close()

        self.filterEntries = []
        for filt in sm.GetService('itemFilter').GetFilters():
            filterEntry = FilterEntry(parent=self.filterCont, filter=filt, eventListener=self)
            self.filterEntries.append(filterEntry)

    def RemoveTreeEntry(self, entry, byUser = False, checkRemoveParent = False):
        parent = entry.data.GetParent()
        if entry.childCont:
            for childEntry in entry.childCont.children[:]:
                self.RemoveTreeEntry(childEntry)

        invID = entry.data.GetID()
        sm.GetService('inv').RemoveTemporaryInvLocation(invID, byUser)
        if invID == self.rootInvID:
            self.Close()
            return
        if invID in self.treeEntryByID:
            self.treeEntryByID.pop(invID)
        if invID in self.tempTreeEntryByID:
            self.tempTreeEntryByID.pop(invID)
        if entry.data in self.treeData.GetChildren():
            self.treeData.RemoveChild(entry.data)
        if invID == self.currInvID:
            if not self.IsInvTreeExpanded():
                self.Close()
                return
            self.ShowInvContainer(self.GetDefaultInvID())
        entry.Close()
        if checkRemoveParent and isinstance(parent, TreeDataInvFolder) and not parent.GetChildren():
            parEntry = self.treeEntryByID.get(parent.GetID(), None)
            if parEntry:
                self.RemoveTreeEntry(parEntry, checkRemoveParent=True)

    def OnInvContScrollSelectionChanged(self, nodes):
        items = []
        for node in nodes:
            items.append(node.rec)

        self.UpdateSelectedItems(items)

    @telemetry.ZONE_METHOD
    def UpdateSelectedItems(self, items = None):
        """ 
        Update capacity gauge, number of items, isk price, etc. based on either items passed in, or all items
        This method is throttled to never execute more than once every 500ms 
        """
        if not session.IsItSafe():
            return
        if not self.invCont:
            return
        self.updateSelectedItemsPending = items or []
        if self.updateSelectedItemsThread:
            return
        self.updateSelectedItemsThread = uthread.new(self._UpdateSelectedItems)

    @telemetry.ZONE_METHOD
    def _UpdateSelectedItems(self):
        if self.destroyed:
            return
        try:
            while self.updateSelectedItemsPending is not None:
                if session.mutating:
                    break
                items = self.updateSelectedItemsPending
                if not items and self.invCont:
                    iskItems = self.invCont.items
                    self.UpdateIskPriceLabel(iskItems)
                else:
                    self.UpdateIskPriceLabel(items)
                self.capacityGauge.SetSecondaryVolume(items)
                self.capacityGauge.SetAdditionalVolume()
                self.UpdateNumberOfItems(items)
                self.updateSelectedItemsPending = None
                blue.synchro.SleepWallclock(500)

        finally:
            self.updateSelectedItemsThread = None

    def SetInvContViewMode(self, value):
        """ Called by InvContViewBtns when view mode is changed """
        if self.invCont:
            self.invCont.ChangeViewMode(value)
        self.UpdateSelectedItems()

    @telemetry.ZONE_METHOD
    def UpdateNumberOfItems(self, items = None):
        items = items or []
        numFiltered = self.invCont.numFilteredItems
        if numFiltered:
            text = '<color=#FF00FF00>'
            numFilteredTxt = localization.GetByLabel('UI/Inventory/NumFiltered', numFiltered=numFiltered)
        else:
            text = numFilteredTxt = ''
        numTotal = len(self.invCont.invController.GetItems()) - numFiltered
        numSelected = len(items)
        if numSelected:
            text += localization.GetByLabel('UI/Inventory/NumItemsAndSelected', numItems=numTotal, numSelected=numSelected, numFilteredTxt=numFilteredTxt)
        else:
            text += localization.GetByLabel('UI/Inventory/NumItems', numItems=numTotal, numFilteredTxt=numFilteredTxt)
        self.numItemsLabel.text = text

    def OnInvContDragEnter(self, invID, nodes):
        if not session.IsItSafe():
            return
        if invID != self.currInvID or self.invCont is None:
            return
        items = []
        for node in nodes:
            if getattr(node, 'item', None):
                if self.invController.IsItemHereVolume(node.item):
                    return
                items.append(node.item)

        self.capacityGauge.SetAdditionalVolume(items)

    def OnInvContDragExit(self, invID, nodes):
        if not session.IsItSafe():
            return
        self.capacityGauge.SetAdditionalVolume()

    @telemetry.ZONE_METHOD
    def UpdateIskPriceLabel(self, items):
        total = 0
        for item in items:
            if item is None:
                continue
            price = util.GetAveragePrice(item)
            if price:
                total += price * item.stacksize

        text = localization.GetByLabel('UI/Inventory/EstIskPrice', iskString=util.FmtISKAndRound(total, False))
        self.totalPriceLabel.text = text

    def UpdateSpecialActionButtons(self):
        self.specialActionsCont.Flush()
        actions = self.invCont.invController.GetSpecialActions()
        for label, func, name in actions:
            button = uicontrols.Button(parent=self.specialActionsCont, label=label, func=func, align=uiconst.TOLEFT, name=name)
            self.invCont.RegisterSpecialActionButton(button)

    def RegisterID(self, entry, invID):
        if id in self.treeEntryByID:
            raise ValueError('Duplicate inventory location ids: %s' % repr(invID))
        self.treeEntryByID[invID] = entry

    def UnregisterID(self, invID):
        if id in self.treeEntryByID:
            self.treeEntryByID.pop(invID)

    def OnTreeViewClick(self, entry, *args):
        if session.solarsystemid and hasattr(entry.data, 'GetItemID'):
            itemID = entry.data.GetItemID()
            bp = sm.GetService('michelle').GetBallpark()
            if bp and itemID in bp.slimItems:
                sm.GetService('state').SetState(itemID, state.selected, 1)
                if uicore.cmd.ExecuteCombatCommand(itemID, uiconst.UI_CLICK):
                    return
        if hasattr(entry.data, 'OpenNewWindow') and uicore.uilib.Key(uiconst.VK_SHIFT) and entry.canAccess:
            entry.data.OpenNewWindow()
        elif isinstance(entry.data, TreeDataInv) and entry.data.HasInvCont():
            self.ShowInvContainer(entry.data.GetID())
        elif entry.data.HasChildren():
            entry.ToggleChildren()

    def OnTreeViewDblClick(self, entry, *args):
        if isinstance(entry.data, TreeDataInv) and entry.data.HasInvCont():
            if settings.user.ui.Get('openSecondaryInv', False) and entry.canAccess:
                entry.data.OpenNewWindow()
            else:
                entry.ToggleChildren()

    def OnTreeViewMouseEnter(self, entry, *args):
        if not session.solarsystemid:
            return
        if hasattr(entry.data, 'GetItemID'):
            sm.GetService('state').SetState(entry.data.GetItemID(), state.mouseOver, 1)

    def OnTreeViewMouseExit(self, entry, *args):
        if not session.solarsystemid:
            return
        if hasattr(entry.data, 'GetItemID'):
            sm.GetService('state').SetState(entry.data.GetItemID(), state.mouseOver, 0)

    def OnTreeViewDragEnter(self, entry, dragObj, nodes):
        self.dragHoverThread = uthread.new(self._OnTreeViewDragEnter, entry, dragObj, nodes)

    def OnTreeViewDragExit(self, entry, dragObj, nodes):
        sm.ScatterEvent('OnInvContDragExit', dragObj, nodes)
        if self.dragHoverThread:
            self.dragHoverThread.kill()
            self.dragHoverThread = None

    def _OnTreeViewDragEnter(self, entry, dragObj, nodes):
        blue.synchro.SleepWallclock(1000)
        if uicore.uilib.mouseOver == entry and uicore.uilib.leftbtn:
            entry.ToggleChildren(True)

    def OnTreeViewGetDragData(self, entry):
        self.dragOpenNewWindowCookie = uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEMOVEDRAG, self.OnGlobalDragExit, entry)

    def OnGlobalDragExit(self, entry, *args):
        """ Open up a new secondary window by dragging a tree entry outside of the inventory window """
        if not uicore.IsDragging():
            return False
        else:
            mo = uicore.uilib.mouseOver
            if IsUnder(mo, self) or mo == self:
                return True
            if entry.canAccess and hasattr(entry.data, 'OpenNewWindow'):
                entry.CancelDrag()
                windowID = Inventory.GetWindowIDFromInvID(entry.data.GetID())
                wnd = uicore.registry.GetWindow(windowID)
                if wnd and wnd.InStack():
                    wnd.GetStack().RemoveWnd(wnd, (0, 5), dragging=True)
                elif wnd:
                    uthread.new(wnd._OpenDraggingThread)
                else:
                    uthread.new(entry.data.OpenNewWindow, True)
            return False

    @telemetry.ZONE_METHOD
    def ShowInvContainer(self, invID, branchHistory = True):
        if invID and not self.IsInvIDLegit(invID):
            invID = self.GetDefaultInvID(startFromInvID=invID)
            if invID not in self.treeEntryByID:
                invID = None
        if invID is None:
            if self.invCont:
                self.invCont.Close()
                self.invCont = None
            self.noInventoryLabel.Show()
            self.HideInvContLoadingWheel()
            self.ExpandTree(animate=False)
            return
        self.noInventoryLabel.Hide()
        if self.invCont is not None and invID == self.invCont.invController.GetInvID():
            return
        entry = self.treeEntryByID.get(invID, None)
        if entry is None:
            return
        try:
            entry.data.invController.GetItems()
        except UserError:
            self.HideInvContLoadingWheel()
            if not self.invCont:
                self.ShowInvContainer(self.GetDefaultInvID())
            raise

        if self.invCont:
            self.invCont.Close()
        self.ShowInvContLoadingWheel()
        if settings.user.ui.Get('keepInvQuickFilterInput', False):
            quickFilterInput = self.quickFilter.GetQuickFilterInput()
        else:
            quickFilterInput = None
        self.invCont = entry.data.GetInvCont(parent=self.rightCont, activeFilters=self.GetActiveFilters(), name=self.GetWindowSettingsID(), quickFilterInput=quickFilterInput)
        self.invController = self.invCont.invController
        self.HideInvContLoadingWheel()
        self.capacityGauge.SetInvCont(self.invCont)
        self.invCont.scroll.OnSelectionChange = self.OnInvContScrollSelectionChanged
        self.UpdateIskPriceLabel(self.invCont.invController.GetItems())
        self.UpdateSpecialActionButtons()
        self.quickFilter.SetInvCont(self.invCont)
        self.viewBtns.UpdateButtons(['icons', 'details', 'list'].index(self.invCont.viewMode))
        if branchHistory:
            self.history.Append(invID)
            self.UpdateHistoryButtons()
        self.currInvID = invID
        self.RegisterLastOpenInvID(invID)
        self.UpdateSelectedState()
        self.UpdateSubCaptionLabel()
        self.UpdateNumberOfItems()
        self.UpdateCapacityGaugeCompactMode()

    def GetMenu(self):
        m = []
        if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            m.append(('GM / WM Extras', ('isDynamic', self.GetGMMenu, ())))
        m.extend(uicontrols.Window.GetMenu(self))
        return m

    def GetGMMenu(self):
        return [('Clear client inventory cache', sm.GetService('invCache').InvalidateCache, ()), ('Toggle inventory priming debug mode (Red means primed)', self.ToggleInventoryPrimingDebug, ())]

    def ToggleInventoryPrimingDebug(self):
        isOn = settings.user.ui.Get('invPrimingDebugMode', False)
        settings.user.ui.Set('invPrimingDebugMode', not isOn)

    def OnBack(self):
        invID = self.history.GoBack()
        if invID:
            if invID in self.treeEntryByID:
                if uicore.uilib.mouseOver != self.goBackBtn:
                    self.goBackBtn.Blink()
                self.ShowInvContainer(invID, branchHistory=False)
            else:
                self.history.GoForward()
            self.UpdateHistoryButtons()

    def OnForward(self):
        invID = self.history.GoForward()
        if invID:
            if invID in self.treeEntryByID:
                if uicore.uilib.mouseOver != self.goForwardBtn:
                    self.goForwardBtn.Blink()
                self.ShowInvContainer(invID, branchHistory=False)
            else:
                self.history.GoBack()
            self.UpdateHistoryButtons()

    def UpdateHistoryButtons(self):
        if self.history.IsBackEnabled():
            self.goBackBtn.Enable()
        else:
            self.goBackBtn.Disable()
        if self.history.IsForwardEnabled():
            self.goForwardBtn.Enable()
        else:
            self.goForwardBtn.Disable()

    def OnResize_(self, *args):
        if self.InStack():
            width = self.GetStack().width
        else:
            width = self.width
        self.dividerCont.SetMaxSize(width - 10)
        self.treeBottomCont.UpdateSize()

    def OnDividerContResize(self):
        minWidth, minHeight = self.default_minSize
        minWidth = max(self.dividerCont.width + 10, minWidth)
        minSize = (minWidth, minHeight)
        self.SetMinSize(minSize)

    def RegisterLastOpenInvID(self, invID):
        settings.user.ui.Set('invLastOpenContainerData_%s' % self.GetWindowSettingsID(), invID)

    def SetSingleFilter(self, selectedEntry):
        for entry in self.filterEntries:
            if entry != selectedEntry:
                entry.checkbox.SetChecked(False)

    def DeselectAllFilters(self):
        for entry in self.filterEntries:
            entry.checkbox.SetChecked(False)

    def UpdateFilters(self):
        if self.invCont:
            self.SetActiveFilters(self.GetActiveFilters())

    def SetActiveFilters(self, filters):
        self.invCont.SetFilters(filters)
        if filters:
            uicore.animations.FadeIn(self.filtersEnabledBtnColor, 0.9, curveType=uiconst.ANIM_OVERSHOT)
        else:
            uicore.animations.FadeOut(self.filtersEnabledBtnColor)

    def OnInvContRefreshed(self, invCont):
        if self.invCont == invCont:
            self.UpdateSelectedItems()

    def GetActiveFilters(self):
        filters = []
        for filterEntry in self.filterEntries:
            flt = filterEntry.GetFilter()
            if flt:
                filters.append(flt)

        return filters

    def UpdateSubCaptionLabel(self, *args):
        entry = self.treeEntryByID.get(self.currInvID, None)
        if not entry:
            return
        currData = entry.data
        dataList = currData.GetAncestors()
        dataList.append(currData)
        self.breadcrumbInvIDs = []
        text = ''
        for i, data in enumerate(dataList[1:]):
            if data != currData:
                text += '<url=localsvc:service=inv&method=OnBreadcrumbTextClicked&linkNum=%d&windowID1=%s&windowID2=%s>' % (i, self.windowID[0], self.windowID[1])
                text += '<color=#55FFFFFF>' + data.GetLabel() + ' > </color></url>'
                self.breadcrumbInvIDs.append(data.GetID())
            else:
                text += data.GetLabel()

        w, _ = self.subCaptionCont.GetAbsoluteSize()
        lw, _ = uicontrols.Label.MeasureTextSize(text)
        if w < lw:
            text = entry.data.GetLabel()
        self.subCaptionLabel.SetText(text)

    def OnBreadcrumbLinkClicked(self, linkNum):
        invID = self.breadcrumbInvIDs[linkNum]
        if self.IsInvIDLegit(invID):
            self.ShowInvContainer(invID)

    def GetNeocomGroupIcon(self):
        return 'res:/UI/Texture/WindowIcons/folder_cargo.png'

    def GetNeocomGroupLabel(self):
        return localization.GetByLabel('UI/Neocom/InventoryBtn')

    def GetDefaultWndIcon(self):
        if self.invController:
            return self.invController.GetIconName()
        return self.default_iconNum

    def GetWindowSettingsID(self):
        if isinstance(self.windowID, tuple):
            return self.windowID[0]
        else:
            return self.windowID

    @staticmethod
    def GetWindowIDFromInvID(invID = None):
        """ 
        Returns a windowID for a given invID. Note that tuple windowIDs are used
        as such that the first value is used to persist window settings, and the entire tuple as a unique ID 
        """
        if invID is None:
            if session.stationid2:
                return ('InventoryStation', None)
            else:
                return ('InventorySpace', None)
        else:
            invCtrlName = invID[0]
            if invID == ('ShipCargo', util.GetActiveShip()):
                return ('ActiveShipCargo', None)
            if invCtrlName in ('StationContainer', 'ShipCargo', 'ShipDroneBay'):
                return ('%s_%s' % invID, invID[1])
            if invCtrlName in ('StationCorpHangar', 'POSCorpHangar'):
                return ('%s_%s_%s' % invID, None)
            if invCtrlName in 'StationCorpHangars':
                return ('%s_%s' % invID, None)
            return ('%s' % invID[0], invID[1])

    @staticmethod
    def OpenOrShow(invID = None, usePrimary = True, toggle = False, openFromWnd = None, **kw):
        """ 
        Open an inventory location, defined by invID, in an already open or new window
        All inventory windows should be opened up through this method
        
        invID: a 2 or 3 tuple on the form (clsName, ID, {ID2}) where clsName represents one of the classes of the invCtrl namespace
        usePrimary: Use the primary inventory window to display given invID
        toggle: Toggle open/close window
        openFromWnd: If defined, we attempt to show inventory within the given window  
        """
        if uicore.uilib.Key(uiconst.VK_SHIFT) or settings.user.ui.Get('openSecondaryInv', False):
            usePrimary = False
            openFromWnd = None
        if usePrimary and (not Inventory.IsPrimaryInvTreeExpanded() or Inventory.IsPrimaryInvCompacted()):
            usePrimary = False
        if openFromWnd:
            if not isinstance(openFromWnd, Inventory):
                openFromWnd = None
            else:
                usePrimary = False
        if invID:
            invController = invCtrl.GetInvCtrlFromInvID(invID)
            if invController and not invController.IsPrimed():
                if not invController.IsInRange():
                    raise UserError('FakeItemNotFound')
                try:
                    invController.GetItems()
                except RuntimeError:
                    raise UserError('FakeItemNotFound')
                    return

        if invID and not usePrimary:
            if invID == ('ShipCargo', util.GetActiveShip()):
                cls = ActiveShipCargo
            else:
                import form
                cls = getattr(form, invID[0], Inventory)
            windowID = Inventory.GetWindowIDFromInvID(invID)
            scope = None
            rootInvID = invID
        else:
            cls = InventoryPrimary
            windowID = Inventory.GetWindowIDFromInvID(None)
            if session.stationid2:
                scope = 'station'
            else:
                scope = 'inflight'
            rootInvID = None
        if toggle:
            wnd = cls.ToggleOpenClose(windowID=windowID, scope=scope, invID=invID, rootInvID=rootInvID, **kw)
        else:
            if openFromWnd:
                wnd = openFromWnd
            else:
                wnd = cls.GetIfOpen(windowID=windowID)
            if wnd:
                wnd.Maximize()
                if wnd.currInvID != invID:
                    if invID not in wnd.treeEntryByID:
                        wnd.RefreshTree(invID)
                    else:
                        wnd.ShowInvContainer(invID)
            else:
                wnd = cls.Open(windowID=windowID, scope=scope, invID=invID, rootInvID=rootInvID, **kw)
        if wnd:
            wnd.ScrollToActiveEntry()
        return wnd

    def ScrollToActiveEntry(self):
        uthread.new(self._ScrollToActiveEntry)

    def _ScrollToActiveEntry(self):
        blue.synchro.Yield()
        _, h = self.tree.GetAbsoluteSize()
        if h <= 0:
            return
        entry = self.treeEntryByID.get(self.currInvID, None)
        if not entry:
            return
        _, topEntry = entry.GetAbsolutePosition()
        _, topScroll, _, height = self.tree.mainCont.GetAbsolute()
        denum = height - entry.topRightCont.height
        if denum:
            fraction = float(topEntry - topScroll) / denum
            self.tree.ScrollToVertical(fraction)

    def OnDropData(self, dragObj, nodes):
        if self.invCont:
            return self.invCont.OnDropData(dragObj, nodes)

    def OnTreeViewDropData(self, entry, obj, nodes):
        if self.dragHoverThread:
            self.dragHoverThread.kill()
            self.dragHoverThread = None
        if self.dragOpenNewWindowCookie:
            uicore.uilib.UnregisterForTriuiEvents(self.dragOpenNewWindowCookie)
            self.dragOpenNewWindowCookie = None
        if isinstance(entry.data, TreeDataInv):
            sm.ScatterEvent('OnInvContDragExit', obj, nodes)
            uthread.new(self._MoveItems, entry, nodes)

    def _MoveItems(self, entry, nodes):
        if not nodes:
            return
        if isinstance(nodes[0], TreeDataInv):
            item = nodes[0].invController.GetInventoryItem()
        else:
            item = getattr(nodes[0], 'item', None)
        if item and entry.data.invController.IsItemHere(item):
            return
        if isinstance(nodes[0], TreeDataInv) and not nodes[0].invController.IsMovable():
            return
        if entry.data.invController.OnDropData(nodes):
            entry.Blink()

    def GetTreeEntryByItemID(self, itemID):
        ret = []
        for _, entry in self.treeEntryByID.iteritems():
            if hasattr(entry.data, 'GetItemID') and entry.data.GetItemID() == itemID:
                ret.append(entry)

        return ret

    def ProcessTempInvLocationAdded(self, invID):
        if invID in self.treeEntryByID:
            return
        if self.rootInvID in sm.GetService('inv').GetTemporaryInvLocations():
            return
        invName, itemID = invID
        cls = GetTreeDataClassByInvName(invName)
        data = cls(invName, parent=self.treeDataTemp, itemID=itemID, isRemovable=True)
        cls = GetTreeViewEntryClassByDataType(data)
        entry = cls(parent=self.tree, level=0, eventListener=self, data=data, settingsID=self.GetWindowSettingsID())
        self.UpdateCelestialEntryStatus(entry)

    def ProcessTempInvLocationRemoved(self, invID, byUser):
        if invID == self.currInvID and not byUser:
            self.Close()
        else:
            entry = self.treeEntryByID.get(invID, None)
            if entry:
                if self.treeDataTemp:
                    self.treeDataTemp.RemoveChild(entry.data)
                if entry.data.IsRemovable():
                    self.RemoveTreeEntry(entry)

    def OnSessionChanged(self, isRemote, sess, change):
        if change.keys() == ['shipid']:
            return
        self.RefreshTree()

    def _IsInventoryItem(self, item):
        if item.groupID in CONTAINERGROUPS:
            return True
        if item.categoryID == const.categoryShip:
            return True
        return False

    @telemetry.ZONE_METHOD
    def OnMultipleItemChange(self, items, change):
        self.UpdateSelectedItems()

    @telemetry.ZONE_METHOD
    def OnInvChangeAny(self, item = None, change = None):
        """ Called by the inv service. Refresh tree view only if needed """
        if not self._IsInventoryItem(item):
            return
        if item.itemID == util.GetActiveShip():
            return
        if item.categoryID == const.categoryShip and session.solarsystemid:
            return
        if const.ixSingleton in change:
            self.RefreshTree()
            return
        if not item.singleton:
            return
        if const.ixLocationID in change or const.ixFlag in change:
            if session.stationid and item.categoryID == const.categoryShip:
                if session.charid in (item.ownerID, change.get(const.ixOwnerID, None)):
                    self.RefreshTree()
            elif session.solarsystemid and item.groupID in CONTAINERGROUPS:
                ownerIDs = (item.ownerID, change.get(const.ixOwnerID, None))
                if ownerIDs[0] == ownerIDs[1] == session.corpid:
                    return
                if session.corpid in ownerIDs and session.charid not in ownerIDs:
                    return
                self.RefreshTree()
            else:
                self.RefreshTree()
        if const.ixOwnerID in change and item.typeID == const.typePlasticWrap:
            self.RefreshTree()

    def GetSlimItem(self):
        itemID = self.invController.itemID
        bp = sm.GetService('michelle').GetBallpark()
        if bp:
            return bp.slimItems.get(itemID, None)

    @telemetry.ZONE_METHOD
    def RemoveItem(self, item):
        """ An item has been removed from active container """
        if session.solarsystemid and not self.invController.GetItems():
            slimItem = self.GetSlimItem()
            if slimItem is not None and slimItem.groupID in invCtrl.LOOT_GROUPS:
                self.RemoveWreckEntryOrClose()

    def OnWreckLootAll(self, invID, items):
        if invID == self.currInvID:
            self.RemoveWreckEntryOrClose()
        treeEntry = self.treeEntryByID.get(('ShipCargo', util.GetActiveShip()))
        if treeEntry and items:
            treeEntry.Blink()

    def RemoveWreckEntryOrClose(self):
        if self.IsInvTreeExpanded():
            entry = self.treeEntryByID.get(self.currInvID, None)
            if entry:
                self.SwitchToOtherLootable(entry)
                if entry.data.IsRemovable():
                    self.RemoveTreeEntry(entry, byUser=True)
        else:
            slimItem = self.GetSlimItem()
            if slimItem is not None and slimItem.groupID not in invCtrl.LOOT_GROUPS_NOCLOSE:
                self.CloseByUser()

    def SwitchToOtherLootable(self, oldEntry):
        """ Switch over to another other open wreck if any """
        lootableData = [ data for data in self.treeDataTemp.GetChildren() if data.GetID()[0] in ('ItemWreck', 'ItemFloatingCargo') ]
        if oldEntry.data not in lootableData:
            return
        idx = lootableData.index(oldEntry.data)
        lootableData.remove(oldEntry.data)
        if lootableData:
            newIdx = min(len(lootableData) - 1, idx)
            invID = lootableData[newIdx].GetID()
            self.ShowInvContainer(invID)

    def OnStateChange(self, itemID, flag, isSet, *args):
        """  Handle "Loot all" action by closing wreck """
        if flag == state.flagWreckEmpty:
            entries = self.GetTreeEntryByItemID(itemID)
            for entry in entries:
                self.RemoveTreeEntry(entry)

    def OnSlimItemChange(self, oldSlim, newSlim):
        if util.IsStructure(newSlim.categoryID):
            if oldSlim.posState != newSlim.posState:
                self.RefreshTree()

    def OnCapacityChange(self, itemID):
        if self.invController and itemID == self.invController.itemID:
            self.UpdateSelectedItems()
            self.capacityGauge.RefreshCapacity()

    def DoBallsAdded(self, data):
        for _, slimItem in data:
            if slimItem.categoryID == const.categoryStructure:
                self.RefreshTree()
                return

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        uthread.new(self._DoBallRemove, ball, slimItem, terminal)

    def _DoBallRemove(self, ball, slimItem, terminal):
        invID = ('ShipCargo', util.GetActiveShip())
        for entry in self.GetTreeEntryByItemID(slimItem.itemID):
            if entry.data.GetID() == invID:
                continue
            if entry.data.IsDescendantOf(invID):
                continue
            self.RemoveTreeEntry(entry, checkRemoveParent=True)

    def OnFiltersEnabledBtnClicked(self, *args):
        for filterEntry in self.filterEntries:
            filterEntry.checkbox.SetChecked(False)

    def OnItemNameChange(self, *args):
        self.RefreshTree()

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.RefreshTree()

    def Compact(self):
        uicontrols.Window.Compact(self)
        for cont in self.GetCompactToggleContainers():
            cont.Hide()

        if self.IsInvTreeExpanded():
            self.sr.main.padding = (3, 3, 0, 4)
        else:
            self.sr.main.padding = (-1, 3, 0, 4)
        self.UpdateCapacityGaugeCompactMode()
        self.DeselectAllFilters()
        if self.invCont:
            self.quickFilter.ClearFilter()

    def UnCompact(self):
        uicontrols.Window.UnCompact(self)
        for cont in self.GetCompactToggleContainers():
            cont.Show()

        self.sr.main.padding = 1
        self.UpdateCapacityGaugeCompactMode()

    def UpdateCapacityGaugeCompactMode(self):
        if self.invController is None:
            return
        if self.IsCompact():
            if self.invController.hasCapacity:
                self.topRightCont2.Show()
                self.capacityGauge.padding = (1, 0, 0, 0)
                self.capacityGauge.HideLabel()
                self.topRightCont2.height = 5
            else:
                self.topRightCont2.Hide()
        else:
            self.topRightCont2.Show()
            if self.invController.hasCapacity:
                self.capacityGauge.padding = (2, 5, 4, 4)
                self.capacityGauge.ShowLabel()
                self.topRightCont2.height = 24

    def GetCompactToggleContainers(self):
        return (self.topRightCont1,
         self.quickFilter,
         self.dividerCont,
         self.bottomRightCont)

    def OnExpandFiltersBtn(self, *args):
        if self.filterCont.pickState == uiconst.TR2_SPS_ON:
            self.CollapseFilters()
        else:
            self.ExpandFilters()

    def ExpandFilters(self, animate = True):
        self.expandFiltersBtn.SetRotation(0)
        self.expandFiltersBtn.Disable()
        self.treeBottomCont.EnableDragResize()
        self.treeBottomCont.minSize = 100
        self.treeBottomCont.maxSize = 0.5
        if animate:
            self.tree.DisableScrollbars()
            height = settings.user.ui.Get('invFiltersHeight_%s' % self.GetWindowSettingsID(), 150)
            height = max(self.treeBottomCont.GetMinSize(), min(self.treeBottomCont.GetMaxSize(), height))
            uicore.animations.MorphScalar(self.treeBottomCont, 'height', self.treeBottomCont.height, height, duration=0.3)
            uicore.animations.FadeIn(self.filterCont, duration=0.3, sleep=True)
            self.tree.EnableScrollbars()
        self.expandFiltersBtn.Enable()
        self.filterCont.EnableScrollbars()
        self.filterCont.Enable()
        settings.user.ui.Set('invFiltersExpanded_%s' % self.GetWindowSettingsID(), True)

    def CollapseFilters(self, animate = True):
        self.filterCont.Disable()
        self.expandFiltersBtn.Disable()
        self.expandFiltersBtn.SetRotation(pi)
        self.treeBottomCont.DisableDragResize()
        height = self.filterHeaderCont.height + 6
        self.treeBottomCont.minSize = self.treeBottomCont.maxSize = height
        self.filterCont.DisableScrollbars()
        if animate:
            self.tree.DisableScrollbars()
            uicore.animations.MorphScalar(self.treeBottomCont, 'height', self.treeBottomCont.height, height, duration=0.3)
            uicore.animations.FadeOut(self.filterCont, duration=0.3, sleep=True)
            self.tree.EnableScrollbars()
        self.treeBottomCont.height = height
        self.filterCont.opacity = 0.0
        self.expandFiltersBtn.Enable()
        settings.user.ui.Set('invFiltersExpanded_%s' % self.GetWindowSettingsID(), False)

    def Paste(self, value):
        if self.invCont:
            self.invCont.Paste(value)

    def OnOfficeRentalChanged(self, *args):
        self.RefreshTree()

    @telemetry.ZONE_METHOD
    def RefreshTree(self, invID = None):
        if invID:
            self.currInvID = invID
        if self.refreshTreeThread:
            self.refreshTreeThread.kill()
        self.refreshTreeThread = uthread.new(self._RefreshTree)

    @telemetry.ZONE_METHOD
    def _RefreshTree(self):
        if self.destroyed:
            return
        if self.invCont:
            self.invCont.Disable()
        self.tree.Disable()
        try:
            self.ConstructTree()
        finally:
            self.tree.Enable()
            if self.invCont:
                self.invCont.Enable()

        self.UpdateRangeUpdater()
        self.UpdateSubCaptionLabel()

    def IsInvIDLegit(self, invID):
        """ Is invID available and does it represent an actual inventory location """
        data = self.treeData.GetDescendants().get(invID, None)
        if data is None:
            data = self.treeDataTemp.GetDescendants().get(invID, None)
        if invID == self.treeData.GetID():
            data = self.treeData
        return data is not None and isinstance(data, TreeDataInv) and data.HasInvCont()

    def GetDefaultInvID(self, startFromInvID = None):
        """ 
        Returns the first inventory location tree data found to use as default. 
        We search from root, unless startFromInvID is defined
        """
        treeData = None
        if startFromInvID:
            treeData = self.treeData.GetChildByID(startFromInvID) or self.treeData
        else:
            treeData = self.treeData
        invID = self._GetDefaultInvID([treeData])
        if startFromInvID and invID is None:
            return self.GetDefaultInvID()
        else:
            return invID

    def _IsValidDefaultInvID(self, data):
        """ Can we use this data node for a default invID """
        if isinstance(data, TreeDataInv) and data.HasInvCont():
            invController = invCtrl.GetInvCtrlFromInvID(data.GetID())
            if invController.IsInRange():
                return True
        return False

    def _GetDefaultInvID(self, dataNodes):
        """ Find (depth first) the first acceptable invID and return it """
        settingsInvID = settings.user.ui.Get('invLastOpenContainerData_%s' % self.GetWindowSettingsID(), None)
        if settingsInvID:
            for data in dataNodes:
                if data.GetID() == settingsInvID and self._IsValidDefaultInvID(data):
                    return data.GetID()

        for data in dataNodes:
            if self._IsValidDefaultInvID(data):
                return data.GetID()
            if data.HasChildren():
                ret = self._GetDefaultInvID(data.GetChildren())
                if ret:
                    return ret

    def ConstructTree(self):
        self.treeEntryByID = {}
        self.tree.Flush()
        self.ShowTreeLoadingWheel()
        try:
            self.treeData = sm.GetService('inv').GetInvLocationTreeData(self.rootInvID)
        except RuntimeError as e:
            if e.args[0] == 'CharacterNotAtStation':
                return
            raise

        self.treeDataTemp = sm.GetService('inv').GetInvLocationTreeDataTemp(self.rootInvID)
        if not self._caption and self.rootInvID:
            data = self.GetTreeDataByInvID(self.rootInvID)
            if data:
                self.SetCaption(data.GetLabel())
        if self.currInvID is None or not self.IsInvIDLegit(self.currInvID):
            self.currInvID = self.GetDefaultInvID(self.currInvID)
            if self.currInvID:
                invCtrl.GetInvCtrlFromInvID(self.currInvID).GetItems()
                self.treeData = sm.GetService('inv').GetInvLocationTreeData(self.rootInvID)
        if self.rootInvID and not settings.user.ui.Get('alwaysShowFullInvTree', False):
            tempData = self.treeDataTemp.GetChildByID(self.rootInvID)
            rootNodes = []
            if tempData:
                self.treeData = tempData
                rootNodes.append(self.treeData)
            else:
                childData = self.treeData.GetChildByID(self.rootInvID)
                if childData:
                    self.treeData = childData
                rootNodes.append(self.treeData)
                rootNodes.extend(self.treeDataTemp.GetChildren())
        else:
            rootNodes = self.treeData.GetChildren()
            rootNodes.extend(self.treeDataTemp.GetChildren())
        if not self.isTreeExpandedStateDetermined:
            self.isTreeExpandedStateDetermined = True
            if self.IsInvTreeExpanded():
                self.ExpandTree(animate=False)
        self.tree.opacity = 0.0
        for data in rootNodes:
            cls = GetTreeViewEntryClassByDataType(data)
            cls(parent=self.tree, level=0, eventListener=self, data=data, settingsID=self.GetWindowSettingsID())

        self.HideTreeLoadingWheel()
        uicore.animations.FadeIn(self.tree, duration=0.2)
        if self.currInvID:
            self.UpdateSelectedState()
            self.ScrollToActiveEntry()
        if self.rootInvID is not None and self.rootInvID not in self.treeEntryByID:
            self.Close()
        else:
            self.ShowInvContainer(self.currInvID)

    def UpdateSelectedState(self):
        selectedIDs = self.treeData.GetPathToDescendant(self.currInvID) or self.treeDataTemp.GetPathToDescendant(self.currInvID) or []
        selectedIDs = [ node.GetID() for node in selectedIDs ]
        if selectedIDs:
            for entry in self.treeEntryByID.values():
                entry.UpdateSelectedState(selectedIDs=selectedIDs)

    def UpdateRangeUpdater(self):
        if session.solarsystemid is None and self.containersInRangeUpdater:
            self.containersInRangeUpdater.kill()
            self.containersInRangeUpdater = None
        elif not self.containersInRangeUpdater:
            self.containersInRangeUpdater = uthread.new(self.UpdateTreeViewEntriesInRange)

    def UpdateTreeViewEntriesInRange(self):
        while not self.destroyed:
            if session.solarsystemid is None:
                self.containersInRangeUpdater = None
                return
            self._UpdateTreeViewEntriesInRange()

    def _UpdateTreeViewEntriesInRange(self):
        for entry in self.treeEntryByID.values():
            if not entry.display or entry.IsClippedBy(self.tree):
                continue
            self.UpdateCelestialEntryStatus(entry)
            blue.pyos.BeNice()

        blue.synchro.Sleep(500)

    def UpdateCelestialEntryStatus(self, entry):
        """ Update label and color of a celestial entry depending on it's distance from player """
        if hasattr(entry.data, 'GetLabelWithDistance'):
            entry.label.text = entry.data.GetLabelWithDistance()
        invController = getattr(entry.data, 'invController', None)
        if invController is None:
            canAccess = True
        else:
            canAccess = invController.IsInRange()
            if isinstance(entry.data.invController, (invCtrl.ItemWreck, invCtrl.ItemFloatingCargo)):
                data = entry.data
                entry.icon.LoadIcon(data.GetIcon(), ignoreSize=True)
                slimItem = sm.GetService('michelle').GetBallpark().slimItems[data.invController.itemID]
                entry.iconColor = bracketUtils.GetIconColor(slimItem)
        entry.SetAccessability(canAccess)

    def OnExpandTreeBtn(self, *args):
        if self.dividerCont.pickState:
            self.CollapseTree()
        else:
            self.ExpandTree()
        self.OnDividerContResize()

    def GetTreeDataByInvID(self, invID):
        for root in (self.treeData, self.treeDataTemp):
            data = root.GetChildByID(invID)
            if data:
                return data

    def SetInvTreeExpandedSetting(self, isExpanded):
        if self.isTreeExpandedStateDetermined:
            settings.user.ui.Set('invTreeExpanded_%s' % self.GetWindowSettingsID(), isExpanded)

    def IsInvTreeExpanded(self, getDefault = True):
        return settings.user.ui.Get('invTreeExpanded_%s' % self.GetWindowSettingsID(), self.GetDefaultInvTreeExpanded())

    @staticmethod
    def IsPrimaryInvTreeExpanded():
        """ Is the tree of the primary inventory window configured to be expanded? """
        windowID = Inventory.GetWindowIDFromInvID(None)
        return bool(settings.user.ui.Get('invTreeExpanded_%s' % windowID[0], True))

    @staticmethod
    def IsPrimaryInvCompacted():
        """ Is the primary window configured to be in compact mode """
        windowID = Inventory.GetWindowIDFromInvID(None)
        return uicore.registry.GetRegisteredWindowState(windowID[0], 'compact')

    def GetDefaultInvTreeExpanded(self):
        """ Is the inventory tree expanded by default for this window """
        if not self.rootInvID:
            return True
        if not self.treeData:
            return None
        data = self.treeData.GetChildByID(self.rootInvID)
        if data:
            return data.HasChildren()

    def ExpandTree(self, animate = True):
        self.expandTreeBtn.SetRotation(-pi / 2)
        self.expandTreeBtn.Disable()
        width = settings.user.ui.Get('invTreeViewWidth_%s' % self.GetWindowSettingsID(), TREE_DEFAULT_WIDTH)
        if animate:
            uicore.animations.MorphScalar(self.dividerCont, 'width', self.dividerCont.width, width, duration=0.3)
            uicore.animations.MorphScalar(self.rightCont, 'padLeft', 4, 0, duration=0.3)
            uicore.animations.FadeIn(self.dividerCont, duration=0.3, sleep=True)
        else:
            self.dividerCont.width = width
            self.rightCont.padLeft = 4
        self.rightCont.padLeft = 0
        self.expandTreeBtn.Enable()
        self.dividerCont.Enable()
        self.SetInvTreeExpandedSetting(True)

    def CollapseTree(self, animate = True):
        self.dividerCont.Disable()
        self.expandTreeBtn.Disable()
        self.expandTreeBtn.SetRotation(pi / 2)
        if animate:
            uicore.animations.MorphScalar(self.dividerCont, 'width', self.dividerCont.width, 0.0, duration=0.3)
            uicore.animations.MorphScalar(self.rightCont, 'padLeft', 0, 4, duration=0.3)
            uicore.animations.FadeOut(self.dividerCont, duration=0.3, sleep=True)
        else:
            self.rightCont.padLeft = 4
            self.dividerCont.width = 0
        self.expandTreeBtn.Enable()
        self.SetInvTreeExpandedSetting(False)


class InventoryPrimary(Inventory):
    __guid__ = 'form.InventoryPrimary'
    default_windowID = ('InventoryPrimary', None)
    default_caption = 'UI/Neocom/InventoryBtn'

    def GetDefaultWndIcon(self):
        return self.default_iconNum

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        """" Change the initial invID as we want the window to stay open with new ship """
        if self.currInvID == ('ShipCargo', oldShipID):
            invID = ('ShipCargo', shipID)
        else:
            invID = None
        self.RefreshTree(invID)


class StationItems(Inventory):
    __guid__ = 'form.StationItems'
    default_windowID = ('StationItems', None)
    default_scope = 'station'
    default_iconNum = invCtrl.StationItems.iconName

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.StationItems().OnDropData(nodes)


class StationShips(Inventory):
    __guid__ = 'form.StationShips'
    default_windowID = ('StationShips', None)
    default_scope = 'station'
    default_iconNum = invCtrl.StationShips.iconName

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.StationShips().OnDropData(nodes)

    def ShowInvContainer(self, invID, *args, **kw):
        if invID[1] == util.GetActiveShip():
            Inventory.OpenOrShow(invID, usePrimary=False)
        else:
            Inventory.ShowInvContainer(self, invID, *args, **kw)


class StationCorpHangars(Inventory):
    __guid__ = 'form.StationCorpHangars'
    default_windowID = ('StationCorpHangars', None)
    default_scope = 'station'
    default_iconNum = 'res:/ui/Texture/WindowIcons/corpHangar.png'

    def GetDefaultWndIcon(self):
        return self.default_iconNum


class StationCorpDeliveries(Inventory):
    __guid__ = 'form.StationCorpDeliveries'
    default_windowID = ('StationCorpDeliveries', None)
    default_scope = 'station'
    default_iconNum = invCtrl.StationCorpDeliveries.iconName

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.StationCorpDeliveries().OnDropData(nodes)


class ActiveShipCargo(Inventory):
    __guid__ = 'form.ActiveShipCargo'
    default_windowID = ('ActiveShipCargo', None)
    default_iconNum = 'res:/UI/Texture/WindowIcons/cargo.png'
    default_caption = 'UI/Neocom/ActiveShipCargoBtn'

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        """" Change the initial invID as we want the window to stay open with new ship """
        self.rootInvID = ('ShipCargo', shipID)
        self.RefreshTree()

    def GetDefaultWndIcon(self):
        return self.default_iconNum

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.ShipCargo(util.GetActiveShip()).OnDropData(nodes)


class FilterEntry(Container):
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_height = 22

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.eventListener = attributes.eventListener
        self.filter = attributes.filter
        filtName, _, _ = self.filter
        self.checkbox = uicontrols.Checkbox(name='checkbox', parent=self, checked=False, callback=self.OnCheckbox, align=uiconst.CENTERLEFT, left=5)
        self.label = uicontrols.Label(parent=self, text=filtName, align=uiconst.CENTERLEFT, left=22)
        self.hoverBG = ListEntryUnderlay(bgParent=self)

    def OnClick(self):
        self.checkbox.ToggleState()

    def OnDblClick(self):
        self.eventListener.SetSingleFilter(self)

    def OnMouseEnter(self, *args):
        self.hoverBG.ShowHilite()

    def OnMouseExit(self, *args):
        self.hoverBG.HideHilite()

    def GetFilter(self):
        if self.checkbox.checked:
            return self.filter

    def OnCheckbox(self, checkbox):
        self.eventListener.UpdateFilters()

    def GetMenu(self):
        m = []
        m.append((localization.GetByLabel('UI/Inventory/Filters/Edit'), self.EditFilter, [self.label.text]))
        m.append((localization.GetByLabel('UI/Commands/Remove'), sm.GetService('itemFilter').RemoveFilter, [self.label.text]))
        return m

    def EditFilter(self, filterName):
        self.eventListener.DeselectAllFilters()
        sm.GetService('itemFilter').EditFilter(filterName)
