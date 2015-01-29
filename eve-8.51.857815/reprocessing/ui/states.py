#Embedded file name: reprocessing/ui\states.py
from inventorycommon.types import GetAveragePrice
from reprocessing.ui.const import STATE_RESTRICTED, STATE_SUSPICIOUS

class States(object):

    def __init__(self, quotes):
        """
        :param quotes:
        :type quotes: reprocessing.ui.quotes.Quotes
        """
        self.quotes = quotes

    def GetState(self, item):
        materials = self.quotes.GetClientMaterial(item.itemID)
        if not materials:
            return STATE_RESTRICTED
        valueOfInput = self._GetAveragePrice(item.typeID) * item.stacksize
        valueOfOutput = sum((self._GetAveragePrice(typeID) * qty for typeID, qty in materials.iteritems()))
        if valueOfOutput * 2 < valueOfInput:
            return STATE_SUSPICIOUS

    def _GetAveragePrice(self, typeID):
        price = GetAveragePrice(typeID)
        if price is None:
            return 0.0
        return price
