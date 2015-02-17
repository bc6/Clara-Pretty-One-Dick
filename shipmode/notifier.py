#Embedded file name: shipmode\notifier.py


class Notifier(object):

    def __init__(self, char_id, ship_id, get_time, macho_net):
        self._char_id = char_id
        self._ship_id = ship_id
        self._macho_net = macho_net
        self._get_time = get_time

    def on_stance_changed(self, old_stance_id, new_stance_id):
        self._macho_net.SinglecastByCharID(self._char_id, 'OnStanceActive', self._ship_id, new_stance_id)


class SystemNotifier(Notifier):

    def __init__(self, char_id, ship_id, get_time, macho_net, ballpark):
        super(SystemNotifier, self).__init__(char_id, ship_id, get_time, macho_net)
        self._ballpark = ballpark

    def on_stance_changed(self, old_stance_id, new_stance_id):
        super(SystemNotifier, self).on_stance_changed(old_stance_id, new_stance_id)
        self._ballpark.UpdateSlimItemField(self._ship_id, *get_slim_item_field(self._get_time(), old_stance_id, new_stance_id))


def get_slim_item_field(time, old_stance_id, new_stance_id):
    return ('shipStance', (old_stance_id, time, new_stance_id))


class ShipStance(object):

    def __init__(self, slim_item):
        self.old_stance_id, self.switch_time, self.new_stance_id = slim_item.shipStance
