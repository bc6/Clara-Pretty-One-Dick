#Embedded file name: eve/client/script/ui/util\defaultRangeUtils.py
_RANGE_BY_TYPE_SETTING_FORMAT = 'defaultType%sDist'
_WARPTO_SETTING = 'WarpTo'
_GENERIC_TYPE_ID = 0
DEFAULT_RANGES = {_WARPTO_SETTING: const.minWarpEndDistance,
 'Orbit': 1000,
 'KeepAtRange': 1000}

def _GetCurrentShipTypeID():
    """
    This is a slightly involved process, so it's a helper function.
    Just fetches the current ship typeID, or None if something fails.
    """
    if session.shipid and session.solarsystemid:
        shipItem = sm.GetService('godma').GetItem(session.shipid)
        if shipItem:
            return shipItem.typeID


def UpdateRangeSetting(key, newRange):
    """
    Save a new range setting for this key, for my current ship type, to preferences.
    Parameters:
        key - string identifier, indicates which setting.  One of: ("WarpTo", "Orbit", "KeepAtRange")
        newRange - New default range in meters
    """
    typeRangeSettings = settings.char.ui.Get(_RANGE_BY_TYPE_SETTING_FORMAT % key, {})
    if key != _WARPTO_SETTING:
        typeID = _GetCurrentShipTypeID()
        if typeID is not None:
            typeRangeSettings[typeID] = newRange
    typeRangeSettings[_GENERIC_TYPE_ID] = newRange
    settings.char.ui.Set(_RANGE_BY_TYPE_SETTING_FORMAT % key, typeRangeSettings)
    sm.ScatterEvent('OnDistSettingsChange')


def FetchRangeSetting(key):
    """
    Fetch the range setting for this key, for my current ship type, from preferences.
    Parameters:
        key - string identifier, indicates which setting.  One of: ("WarpTo", "Orbit", "KeepAtRange")
    """
    if key not in DEFAULT_RANGES:
        return
    typeRangeSettings = settings.char.ui.Get(_RANGE_BY_TYPE_SETTING_FORMAT % key, {})
    if key != _WARPTO_SETTING:
        typeID = _GetCurrentShipTypeID()
        if typeID is not None and typeID in typeRangeSettings:
            return typeRangeSettings[typeID]
    if _GENERIC_TYPE_ID in typeRangeSettings:
        return typeRangeSettings[_GENERIC_TYPE_ID]
    return DEFAULT_RANGES[key]


exports = {'defaultRangeUtils.FetchRangeSetting': FetchRangeSetting,
 'defaultRangeUtils.UpdateRangeSetting': UpdateRangeSetting}
