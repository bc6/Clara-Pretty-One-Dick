#Embedded file name: eve/client/script/ui/shared/inventory\treeViewEntries.py
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.treeViewEntry import TreeViewEntry
import localization
import carbonui.const as uiconst
import util
COLOR_SELECTED = (0.1, 1.0, 0.1, 1.0)

def GetTreeViewEntryClassByDataType(treeData):
    """ Always use this function to get correct TreeEntry class to use for inventory"""
    treeEntryCls = TreeViewEntryInventory
    if treeData:
        clsName = getattr(treeData, 'clsName', None)
        if clsName in ('ShipMaintenanceBay', 'ShipFleetHangar') and treeData.invController.itemID == util.GetActiveShip():
            treeEntryCls = TreeViewEntryAccessConfig
        elif clsName in ('StationCorpHangar', 'POSCorpHangar', 'StationContainer'):
            treeEntryCls = TreeViewEntryAccessRestricted
    return treeEntryCls


class TreeViewEntryInventory(TreeViewEntry):
    default_name = 'TreeViewEntryInventory'

    def GetTreeViewEntryClassByTreeData(self, treeData):
        return GetTreeViewEntryClassByDataType(treeData)


class TreeViewEntryAccessConfig(TreeViewEntry):
    """
    A tree view entry that is used for active ship Fleet hangar and Ship maintenance bays,
    adding icons to configure corp and fleet member access
    """
    default_name = 'TreeViewEntryAccessConfig'

    def ApplyAttributes(self, attributes):
        self.iconCont = None
        TreeViewEntry.ApplyAttributes(self, attributes)
        self.iconCont = ContainerAutoSize(parent=self.topRightCont, align=uiconst.CENTERLEFT, height=16)
        self.fleetAccessBtn = ButtonIcon(name='fleetAccessBtn', parent=self.iconCont, align=uiconst.TOLEFT, width=14, iconSize=14, texturePath='res:/UI/Texture/classes/Inventory/fleetAccess.png', func=self.OnFleetAccessBtn, colorSelected=COLOR_SELECTED)
        self.corpAccessBtn = ButtonIcon(name='corpAccessBtn', parent=self.iconCont, align=uiconst.TOLEFT, width=14, padLeft=1, iconSize=12, texturePath='res:/UI/Texture/classes/Inventory/corpAccess.png', func=self.OnCorpAccessBtn, colorSelected=COLOR_SELECTED)
        self.UpdateFleetIcon()
        self.UpdateCorpIcon()

    def OnFleetAccessBtn(self, *args):
        if self.data.clsName == 'ShipMaintenanceBay':
            sm.GetService('shipConfig').ToggleShipMaintenanceBayFleetAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsShipMaintenanceBayFleetAccessAllowed())
        elif self.data.clsName == 'ShipFleetHangar':
            sm.GetService('shipConfig').ToggleFleetHangarFleetAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsFleetHangarFleetAccessAllowed())
        self.UpdateFleetIcon()

    def UpdateFleetIcon(self):
        if self.data.clsName == 'ShipMaintenanceBay':
            isAllowed = sm.GetService('shipConfig').IsShipMaintenanceBayFleetAccessAllowed()
        elif self.data.clsName == 'ShipFleetHangar':
            isAllowed = sm.GetService('shipConfig').IsFleetHangarFleetAccessAllowed()
        if isAllowed:
            hint = localization.GetByLabel('UI/Inventory/DisableAccessToFleetMembers')
        else:
            hint = localization.GetByLabel('UI/Inventory/EnableAccessToFleetMembers')
        self._UpdateButton(self.fleetAccessBtn, isAllowed, hint)

    def OnCorpAccessBtn(self, *args):
        if self.data.clsName == 'ShipMaintenanceBay':
            sm.GetService('shipConfig').ToggleShipMaintenanceBayCorpAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsShipMaintenanceBayCorpAccessAllowed())
        elif self.data.clsName == 'ShipFleetHangar':
            sm.GetService('shipConfig').ToggleFleetHangarCorpAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsFleetHangarCorpAccessAllowed())
        self.UpdateCorpIcon()

    def UpdateCorpIcon(self):
        if self.data.clsName == 'ShipMaintenanceBay':
            isAllowed = sm.GetService('shipConfig').IsShipMaintenanceBayCorpAccessAllowed()
        elif self.data.clsName == 'ShipFleetHangar':
            isAllowed = sm.GetService('shipConfig').IsFleetHangarCorpAccessAllowed()
        if isAllowed:
            hint = localization.GetByLabel('UI/Inventory/DisableAccessToCorpMembers')
        else:
            hint = localization.GetByLabel('UI/Inventory/EnableAccessToCorpMembers')
        self._UpdateButton(self.corpAccessBtn, isAllowed, hint)

    def _UpdateButton(self, button, isAllowed, hint):
        if isAllowed:
            button.SetSelected()
        else:
            button.SetDeselected()
        button.hint = hint

    def UpdateLabel(self):
        TreeViewEntry.UpdateLabel(self)
        if self.iconCont:
            self.iconCont.left = self.label.left + self.label.width + 3

    def PlayButtonSound(self, buttonState):
        if buttonState:
            sm.GetService('audio').SendUIEvent('msg_DiodeClick_play')
        else:
            sm.GetService('audio').SendUIEvent('msg_DiodeDeselect_play')


class TreeViewEntryAccessRestricted(TreeViewEntry):
    """
    A tree view entry that displays access restrictions
    """
    default_name = 'TreeViewEntryAccessRestricted'
    ICONSIZE = 16
    COLOR_RED = (0.867, 0.0, 0.0, 1.0)
    COLOR_YELLOW = (0.984, 0.702, 0.22, 1.0)

    def ApplyAttributes(self, attributes):
        self.iconCont = None
        TreeViewEntry.ApplyAttributes(self, attributes)
        canTake = self.data.CheckCanTake()
        canQuery = self.data.CheckCanQuery()
        if not canQuery:
            texturePath = 'res:/UI/Texture/classes/Inventory/restricted.png'
            hint = localization.GetByLabel('UI/Inventory/DropAccessOnly')
            color = self.COLOR_RED
        else:
            texturePath = 'res:/UI/Texture/classes/Inventory/readOnly.png'
            hint = localization.GetByLabel('UI/Inventory/ViewAccessOnly')
            color = self.COLOR_YELLOW
        if not canTake or not canQuery:
            self.iconCont = ContainerAutoSize(parent=self.topRightCont, align=uiconst.CENTERLEFT, height=self.ICONSIZE)
            Sprite(name='restrictedIcon', parent=self.iconCont, align=uiconst.TOLEFT, texturePath=texturePath, width=self.ICONSIZE, color=color, hint=hint)

    def UpdateLabel(self):
        TreeViewEntry.UpdateLabel(self)
        if self.iconCont:
            self.iconCont.left = self.topRightCont.width + self.label.left + self.label.width + 3
