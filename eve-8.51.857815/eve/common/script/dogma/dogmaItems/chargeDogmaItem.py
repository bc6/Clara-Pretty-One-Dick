#Embedded file name: eve/common/script/dogma/dogmaItems\chargeDogmaItem.py
from eve.common.script.dogma.dogmaItems.shipFittableDogmaItem import ShipFittableDogmaItem
import util

class ChargeDogmaItem(ShipFittableDogmaItem):
    __guid__ = 'dogmax.ChargeDogmaItem'

    def GetEnvironmentInfo(self):
        otherID = None
        if self.location is not None:
            otherID = self.dogmaLocation.GetSlotOther(self.location.itemID, self.flagID)
        return util.KeyVal(itemID=self.itemID, shipID=self.GetShipID(), charID=self.GetPilot(), otherID=otherID, targetID=None, effectID=None)

    def IsValidFittingCategory(self, categoryID):
        return categoryID in (const.categoryShip, const.categoryStructure)
