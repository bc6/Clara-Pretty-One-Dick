#Embedded file name: reprocessing/ui\itemReprocessor.py
from eveexceptions import UserError
import inventorycommon.const as invconst
import sys

class ItemReprocessor(object):

    def __init__(self, reprocessingSvc, invCache, AskToContinue):
        self.reprocessingSvc = reprocessingSvc
        self.invCache = invCache
        self.AskToContinue = AskToContinue

    def Reprocess(self, items, activeShipID):
        fromLocation = self._GetFromLocationID(items)
        itemIDs = []
        try:
            for item in items:
                itemID = item.itemID
                self._CheckIsRefiningShip(activeShipID, itemID)
                if not self._IsInSameLocation(fromLocation, item):
                    continue
                self._LockItem(item, itemIDs)

            try:
                if len(itemIDs):
                    ownerID, flag = session.charid, invconst.flagHangar
                    skipChecks = []
                    while True:
                        try:
                            self._DoReprocess(itemIDs, ownerID, fromLocation, flag, skipChecks)
                        except UserError as e:
                            sys.exc_clear()
                            if self.AskToContinue(e):
                                skipChecks.append(e.msg)
                                continue

                        break

            except:
                sys.exc_clear()

        finally:
            self._UnlockItems(itemIDs)

    def _CheckIsRefiningShip(self, activeShipID, itemID):
        if itemID == activeShipID:
            raise UserError('CannotReprocessActive')

    def _GetFromLocationID(self, items):
        fromLocation = None
        for item in items:
            fromLocation = item.locationID
            break

        return fromLocation

    def _IsInSameLocation(self, locationID, item):
        return locationID == item.locationID

    def _LockItem(self, item, itemIDs):
        self.invCache.TryLockItem(item.itemID, 'lockReprocessing', {'itemType': item.typeID}, 1)
        itemIDs.append(item.itemID)

    def _UnlockItems(self, itemIDs):
        for itemID in itemIDs:
            self.invCache.UnlockItem(itemID)

    def _DoReprocess(self, itemIDs, ownerID, fromLocation, flag, skipChecks):
        self.reprocessingSvc.GetReprocessingSvc().Reprocess(itemIDs, fromLocation, ownerID, flag, True, skipChecks)
