#Embedded file name: eve/common/script/dogma/dogmaItems\fittableDogmaItem.py
from eve.common.script.dogma.dogmaItems.baseDogmaItem import BaseDogmaItem

class FittableDogmaItem(BaseDogmaItem):
    __guid__ = 'dogmax.FittableDogmaItem'

    def Unload(self):
        super(FittableDogmaItem, self).Unload()
        if self.location and self.itemID in self.location.fittedItems:
            del self.location.fittedItems[self.itemID]
