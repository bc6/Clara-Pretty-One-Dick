#Embedded file name: eve/client/script/util\settings.py
SETTING_SHIP_TOP_ALIGNED = 'shipuialigntop'

def IsShipHudTopAligned():
    return settings.user.ui.Get(SETTING_SHIP_TOP_ALIGNED, False)


def SetShipHudTopAligned(isHudTopAligned):
    settings.user.ui.Set(SETTING_SHIP_TOP_ALIGNED, isHudTopAligned)
