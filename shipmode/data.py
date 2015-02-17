#Embedded file name: shipmode\data.py
import copy
import inventorycommon.types
shipStanceDefense = 1
shipStanceSpeed = 2
shipStanceSniper = 3
_DATA = {34317: [(shipStanceDefense,
          34319,
          'res:/UI/Texture/Icons/defence.png',
          'CmdSetDefenceStance'), (shipStanceSniper,
          34321,
          'res:/UI/Texture/Icons/target.png',
          'CmdSetSniperStance'), (shipStanceSpeed,
          34323,
          'res:/UI/Texture/Icons/speed.png',
          'CmdSetSpeedStance')],
 34562: [(shipStanceDefense,
          34564,
          'res:/UI/Texture/Icons/defence.png',
          'CmdSetDefenceStance'), (shipStanceSniper,
          34570,
          'res:/UI/Texture/Icons/target.png',
          'CmdSetSniperStance'), (shipStanceSpeed,
          34566,
          'res:/UI/Texture/Icons/speed.png',
          'CmdSetSpeedStance')]}

class ShipModeData(object):

    def __init__(self, key_id, type_id, icon_num, command_name):
        self._key_id = key_id
        self._type_id = type_id
        self._icon_num = icon_num
        self._command_name = command_name

    def get_name(self):
        return inventorycommon.types.GetName(self._type_id)

    def get_description(self):
        return inventorycommon.types.GetDescription(self._type_id)

    def get_key(self):
        return self._key_id

    def get_type_id(self):
        return self._type_id

    def get_icon_num(self):
        return self._icon_num

    def get_command_name(self):
        return self._command_name


def get_ship_modes_data(type_id):
    return [ ShipModeData(*args) for args in _DATA.get(type_id, []) ]


def get_stance_data(type_id, stance_id):
    for stance_data in get_ship_modes_data(type_id):
        if stance_data.get_key() == stance_id:
            return stance_data


def get_modes_by_type(type_id):
    return {sd.get_key():sd.get_type_id() for sd in get_ship_modes_data(type_id)}


def ship_has_stances(type_id):
    return type_id in _DATA


def get_default_stance(type_id):
    return 1


def get_stance_by_type(type_id):
    return {sd.get_type_id():sd.get_key() for sd in get_ship_modes_data(type_id)}


def get_mode_for_type(type_id, stance):
    for sd in get_ship_modes_data(type_id):
        if sd.get_key() == stance:
            return sd.get_type_id()
