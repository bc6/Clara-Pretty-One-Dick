#Embedded file name: reprocessing/ui\controller.py
from collections import defaultdict
from inventorycommon.groups import GetCategoryID
from reprocessing.ui.efficiencyCalculator import CalculateTheoreticalEfficiency

class Controller(object):
    __notifyevents__ = ['OnItemChange']

    def __init__(self, wnd, inputItems, inputGroups, quotes, outputItems, reprocessor, GetActiveShipID):
        self.window = wnd
        self.inputItems = inputItems
        self.inputGroups = inputGroups
        self.quotes = quotes
        self.outputItems = outputItems
        self.reprocessor = reprocessor
        self.GetActiveShipID = GetActiveShipID

    def AddItems(self, items):
        self.window.ShowInputLoading()
        try:
            itemsByGroup = defaultdict(list)
            for i in items:
                group = self.inputGroups.grouper.GetGroupID(i)
                itemsByGroup[group].append(i)

            for itemsInGroup in itemsByGroup.itervalues():
                self._AddItemsInGroup(itemsInGroup)

        finally:
            self.window.HideInputLoading()

    def _AddItemsInGroup(self, items):
        self.inputGroups.UpdateGroups(items)
        self.inputItems.AddItems(items)
        self.SetEfficiency()
        self.outputItems.UpdateItems()

    def RemoveItem(self, itemID):
        item = self.inputItems.RemoveItem(itemID)
        self.inputGroups.RemoveItem(item)
        self.quotes.RemoveItem(itemID)
        self.SetEfficiency()
        self.outputItems.UpdateItems()

    def Reprocess(self):
        self.reprocessor.Reprocess(self.inputItems.GetItems(), self.GetActiveShipID())
        self.inputItems.ClearItems()
        self.inputGroups.ClearAllGroups()

    def OnItemChange(self, item, change):
        """
        Checks if item that's getting trashed is in reprocessing window.
        Removes it from it if true.
        """
        if item.locationID != const.locationJunkyard:
            return
        if self.inputGroups.HasItem(item):
            self.RemoveItem(item.itemID)

    def SetEfficiency(self):
        typeIDs = self.inputItems.GetTypeIDsByGroup()
        if len(typeIDs):
            categoryID = typeIDs.keys()[0]
            for group in self.inputGroups.groups:
                efficiency = self.quotes.GetStationEfficiencyForCategoryID(categoryID)
                tax = self.quotes.stationTax
                self.inputGroups.SetEfficiency(group, CalculateTheoreticalEfficiency(typeIDs[group], tax, efficiency), typeIDs)
                self.inputGroups.SetTaxAndStationEfficiency(group, efficiency, tax)

    def GetOutputItems(self):
        return self.outputItems.GetItems()


def NodesToItems(nodes):
    ret = []
    for node in nodes:
        if node.__guid__ in ('xtriui.InvItem', 'listentry.InvItem'):
            itemID = getattr(node, 'itemID', None)
            if itemID is not None:
                ret.append(node.rec)

    return ret
