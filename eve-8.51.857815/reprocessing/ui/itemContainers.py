#Embedded file name: reprocessing/ui\itemContainers.py
from carbon.common.script.util.format import FmtAmt
from localization import GetByLabel
from eve.common.script.util.eveFormat import FmtISKAndRound

class ItemContainerInterface(object):

    def __init__(self, container):
        self.container = container

    def AddGroups(self, groups):
        for groupID, groupName in groups:
            self.container.AddGroup(groupID, groupName)

    def AddItems(self, items):
        for groupID, items in items.iteritems():
            for ctrlID, item in items:
                self.container.AddItem(groupID, (ctrlID, item))

    def UpdateItemInfo(self, outputPrice, numberOfItems, volume = None):
        self.container.totalPriceLabel.text = GetByLabel('UI/Inventory/EstIskPrice', iskString=FmtISKAndRound(outputPrice, False))
        self.container.numItemsLabel.text = GetByLabel('UI/Inventory/NumItems', numItems=numberOfItems, numFilteredTxt='')
        if volume is not None:
            self.container.volumeLabel.text = GetByLabel('UI/Reprocessing/ReprocessingWindow/TotalVolume', volume=FmtAmt(volume, showFraction=2))

    def UpdateInfo(self, group, *args):
        self.container.groupContainers[group].UpdateInfo(*args)

    def RemoveGroup(self, group):
        self.container.RemoveGroup(group)

    def RemoveItem(self, group, ctrlID):
        self.container.groupContainers[group].tilePlacer.RemoveItem(ctrlID)

    def ClearAllItems(self):
        self.container.ClearAllItems()

    def ShowItems(self):
        self.container.ShowItems()


class InputItemContainerInterface(ItemContainerInterface):

    def AddItems(self, items):
        ItemContainerInterface.AddItems(self, items)
        self.container.overlayCont.display = False

    def ClearAllItems(self):
        self.container.AnimateItems()
        ItemContainerInterface.ClearAllItems(self)
        self.container.overlayCont.display = True

    def SetEfficiency(self, group, efficiency, typeIDs):
        self.container.SetEfficiency(group, efficiency, typeIDs)

    def SetTaxAndStationEfficiency(self, group, efficiency, tax):
        self.container.SetTaxAndStationEfficiency(group, efficiency, tax)
