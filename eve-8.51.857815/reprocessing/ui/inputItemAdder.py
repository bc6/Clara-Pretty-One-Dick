#Embedded file name: reprocessing/ui\inputItemAdder.py
from collections import defaultdict
from inventorycommon.types import GetAveragePrice

class InputItemAdder(object):

    def __init__(self, inputContainer, containerCreator, quotes, states, grouper, GetActiveShip):
        self.inputContainer = inputContainer
        self.containerCreator = containerCreator
        self.quotes = quotes
        self.states = states
        self.GetActiveShip = GetActiveShip
        self.items = {}
        self.grouper = grouper
        self.itemsByMarketGroupID = defaultdict(list)

    def _GetItemsToUpdate(self, items):
        itemsToUpdate = []
        for item in items:
            if item.itemID not in self.items:
                self.items[item.itemID] = item
                itemsToUpdate.append(item)

        return itemsToUpdate

    def AddItems(self, items):
        itemsToUpdate = self._GetItemsToUpdate(items)
        self.GetQuotes()
        if itemsToUpdate:
            self.UpdateItems(itemsToUpdate)
        self._UpdateItemInfo(self.items)

    def _GetContainer(self, item):
        return self.containerCreator.CreateInputItem(item.itemID, (item, self.quotes.GetHint(item.itemID, item.typeID), self.states.GetState(item)))

    def UpdateItems(self, items):
        containers = defaultdict(list)
        for item in items:
            containers[self.grouper.GetGroupID(item)].append((item.itemID, self._GetContainer(item)))

        self.inputContainer.AddItems(containers)

    def RemoveItem(self, itemID):
        item = self.items.pop(itemID)
        self.containerCreator.RemoveInputItem(itemID)
        self.inputContainer.RemoveItem(self.grouper.GetGroupID(item), itemID)
        self._UpdateItemInfo(self.items)
        return item

    def GetItemIDs(self):
        return self.items.keys()

    def GetItems(self):
        return self.items.values()

    def GetItemIDsByGroup(self):
        itemsByGroup = defaultdict(list)
        for item in self.items.itervalues():
            itemsByGroup[self.grouper.GetGroupID(item)].append(item.itemID)

        return itemsByGroup

    def GetTypeIDsByGroup(self):
        itemsByGroup = defaultdict(list)
        for item in self.items.itervalues():
            itemsByGroup[self.grouper.GetGroupID(item)].append(item.typeID)

        return itemsByGroup

    def _GetAveragePrice(self, typeID):
        price = GetAveragePrice(typeID)
        if price is None:
            return 0.0
        return price

    def _UpdateItemInfo(self, items):
        numItems = len(items)
        price = sum((self._GetAveragePrice(item.typeID) * item.stacksize for item in items.itervalues()))
        self.inputContainer.UpdateItemInfo(price, numItems)

    def GetQuotes(self):
        self.materials = self.quotes.GetQuotes(self.items, self.GetActiveShip())

    def ClearItems(self):
        self.items.clear()
        self.inputContainer.ClearAllItems()
        self._UpdateItemInfo(self.items)
