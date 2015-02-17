#Embedded file name: eve/common/script/dogma/dogmaItems\probeDogmaItem.py
from eve.common.script.dogma.dogmaItems.baseDogmaItem import BaseDogmaItem

class ProbeDogmaItem(BaseDogmaItem):
    __guid__ = 'dogmax.ProbeDogmaItem'

    def Load(self, item, instanceRow):
        super(ProbeDogmaItem, self).Load(item, instanceRow)
        self.ownerID = item.ownerID
