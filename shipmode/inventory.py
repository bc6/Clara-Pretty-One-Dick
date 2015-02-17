#Embedded file name: shipmode\inventory.py


class Inventory(object):

    def __init__(self, inventory2, invmgr, ship_id, flag_id):
        self._inventory2 = inventory2
        self._invmgr = invmgr
        self._ship_id = ship_id
        self._flag_id = flag_id

    def create_item(self, type_id):
        self._inventory2.CreateItem(type_id, self._ship_id, self._flag_id)

    def clear_items(self):
        for item in self.list_items():
            self._invmgr.DestroyItem(item.itemID)

    def remove_item(self, item_id):
        self._invmgr.DestroyItem(item_id)

    def list_items(self):
        return self._inventory2.SelectItems(locationID=self._ship_id, flag=self._flag_id)

    def get_type_id(self, item_id):
        return self._inventory2.GetItem(item_id).typeID


class InventoryClient(object):

    def __init__(self, inv_cache, ship_id, flag_id):
        self._inv_cache = inv_cache
        self._ship_id = ship_id
        self._flag_id = flag_id

    def list_items(self):
        inv = self._inv_cache.GetInventoryFromId(self._ship_id)
        return inv.List(self._flag_id)
