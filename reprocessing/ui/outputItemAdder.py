#Embedded file name: reprocessing/ui\outputItemAdder.py
from collections import defaultdict
import itertools
from itertoolsext import Bundle
from inventorycommon.types import GetAveragePrice, GetVolume
from reprocessing.util import CanBeReprocessed

class OutputItemAdder(object):
    """
    Updates the material container in the reprocessing window
    """

    def __init__(self, materialFetcher, outputContainer, itemCreator, grouper):
        self.materialFetcher = materialFetcher
        self.outputContainer = outputContainer
        self.itemCreator = itemCreator
        self.grouper = grouper
        self.items = {}
        self.groups = set()

    def UpdateItems(self):
        items = self._GetContainerInfo()
        self.outputContainer.ShowItems()
        self._RemoveContainers(items)
        groups = {self.grouper.GetGroupID(item) for item in items.itervalues()}
        self._RemoveGroups(groups)
        itemsToAdd, itemsToUpdate = self._GetItemsToAddAndUpdate(items)
        self._AddGroups(groups)
        self._AddContainers(itemsToAdd)
        self._UpdateContainers(itemsToUpdate)
        self._UpdateItemInfo(items)
        self.items = {i.typeID:i for i in items.itervalues()}
        self.groups = groups

    def _RemoveContainers(self, items):
        typeIDsToAdd = {i.typeID for i in items.itervalues()}
        for typeID, item in self.items.iteritems():
            if typeID not in typeIDsToAdd:
                self.outputContainer.RemoveItem(self.grouper.GetGroupID(item), typeID)

    def _AddContainers(self, itemsToAdd):
        containersToAdd = defaultdict(list)
        for item in itemsToAdd:
            containerInfo = GetAddParams(item, self.itemCreator.CreateOutputItems)
            containersToAdd[self.grouper.GetGroupID(item)].append(containerInfo)

        self.outputContainer.AddItems(containersToAdd)

    def _RemoveGroups(self, groups):
        for group in self.groups.difference(groups):
            self.outputContainer.RemoveGroup(group)

    def _AddGroups(self, groupIDs):
        groupIDsToAdd = groupIDs.difference(self.groups)
        if groupIDsToAdd:
            self.outputContainer.AddGroups([ (groupID, self.grouper.GetGroupName(groupID)) for groupID in groupIDsToAdd ])
        return groupIDs

    def _UpdateContainers(self, itemsToUpdate):
        for item in itemsToUpdate:
            self.outputContainer.UpdateInfo(self.grouper.GetGroupID(item), *GetUpdateParams(item))

    def _GetItemsToAddAndUpdate(self, items):
        itemsToUpdate = []
        itemsToAdd = []
        for item in items.itervalues():
            if item.typeID in self.items:
                itemsToUpdate.append(item)
            else:
                itemsToAdd.append(item)

        return (itemsToAdd, itemsToUpdate)

    def _GetContainerInfo(self):
        containerInfo = defaultdict(lambda : Bundle(typeID=None, fromTypeInfo=defaultdict(float), fromItemIDs=[], client=0, station=0, unrecoverable=0))
        for material in self.materialFetcher.GetMaterials():
            ci = containerInfo[material.typeID]
            ci.typeID = material.typeID
            ci.fromItemIDs.append(material.fromItemID)
            ci.fromTypeInfo[material.fromTypeID] = material.client + material.station + material.unrecoverable
            ci.client += material.client
            ci.station += material.station
            ci.unrecoverable += material.unrecoverable

        return containerInfo

    def _GetAveragePrice(self, typeID):
        price = GetAveragePrice(typeID)
        if price is None:
            return 0.0
        return price

    def _UpdateItemInfo(self, items):
        numItems = len(items)
        price = sum((self._GetAveragePrice(typeID) * ci.client for typeID, ci in itertools.chain(items.iteritems())))
        volume = sum((GetVolume(typeID) * ci.client for typeID, ci in items.iteritems()))
        self.outputContainer.UpdateItemInfo(price, numItems, volume)

    def GetItems(self):
        return self.items


def GetAddParams(item, createOutputItems):
    return (item.typeID, createOutputItems(item.typeID, (item.typeID,
      item.fromItemIDs,
      item.fromTypeInfo,
      (item.client, item.station, item.unrecoverable),
      CanBeReprocessed(item.typeID))))


def GetUpdateParams(item):
    return (item.typeID,
     (item.client, item.station, item.unrecoverable),
     item.fromItemIDs,
     item.fromTypeInfo)


class MaterialFetcher(object):
    """
    Fetches the material. It is mostly just taking stuff from the reprocessing quite it gets
    from the server and returns a list of Bundles
    """

    def __init__(self, quotes):
        self.quotes = quotes

    def IterQuotes(self):
        return self.quotes.GetRawQuotes().iteritems()

    def GetMaterials(self):
        ret = []
        for itemID, item in self.IterQuotes():
            for r in item.recoverables:
                ret.append(Bundle(typeID=r.typeID, fromTypeID=item.typeID, fromItemID=itemID, client=r.client, station=r.station, unrecoverable=r.unrecoverable))

        return ret
