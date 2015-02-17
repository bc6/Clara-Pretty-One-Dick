#Embedded file name: shipmode\shipstance.py
import uthread2

class ShipStance(object):

    def __init__(self, inventory, notifier, modifier_items):
        self.inventory = inventory
        self.notifier = notifier
        self._stance_to_type_id = modifier_items

    def set_stance(self, stance_id, switch_time):
        old_stance_id = self.get_current_stance()
        if old_stance_id == stance_id:
            return old_stance_id
        self.inventory.clear_items()
        self.inventory.create_item(self._get_type_id(stance_id))
        self.notifier.on_stance_changed(old_stance_id, stance_id)
        if switch_time:
            uthread2.sleep_sim(switch_time)
        return old_stance_id

    def get_current_stance(self):
        for item in self.inventory.list_items():
            fitted_type_id = item.typeID
            for mode, type_id in self._stance_to_type_id.iteritems():
                if type_id == fitted_type_id:
                    return mode

    def _get_type_id(self, stance_id):
        return self._stance_to_type_id[stance_id]

    def is_ship_in_stance(self, modifier_id):
        type_id = self._get_type_id(modifier_id)
        return type_id in (item.typeID for item in self.inventory.list_items())
