#Embedded file name: shipmode\__init__.py
import inventorycommon.const as invconst
from .data import get_ship_modes_data, get_modes_by_type, get_stance_by_type, ship_has_stances, get_stance_data
from .notifier import SystemNotifier, Notifier, get_slim_item_field
from .inventory import Inventory, InventoryClient
from .shipstance import ShipStance

def get_station_inventory(location_id, invbroker, i2, ship_id):
    return Inventory(i2.GetStationInventory(location_id), invbroker.GetStationInventoryMgr(location_id), ship_id, invconst.flagHiddenModifers)


def get_solar_system_inventory(location_id, invbroker, i2, ship_id):
    return Inventory(i2.GetSolarSystemInventory(location_id), invbroker.GetSolarSystemInventoryMgr(location_id), ship_id, invconst.flagHiddenModifers)


def get_current_ship_stance(type_id, items):
    stance_by_type = get_stance_by_type(type_id)
    for item in items:
        if item.typeID in stance_by_type:
            return stance_by_type[item.typeID]
