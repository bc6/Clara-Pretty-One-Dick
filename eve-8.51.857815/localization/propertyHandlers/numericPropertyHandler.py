#Embedded file name: localization/propertyHandlers\numericPropertyHandler.py
import eveLocalization
import carbon.common.script.util.format as fmtutils
import eve.common.script.util.eveFormat as evefmtutils
from basePropertyHandler import BasePropertyHandler
from .. import const as locconst

class NumericPropertyHandler(BasePropertyHandler):
    """
    The property handler defines the actual methods to retrieve numeric quantity-specific property data.
    """
    PROPERTIES = {locconst.CODE_UNIVERSAL: ['quantity',
                               'isk',
                               'aur',
                               'distance']}

    def _GetQuantity(self, value, languageID, *args, **kwargs):
        """
        Return the quantity of this numeric value.  Despite simply returning its own value, it is necessary to define
        and register a property handler class to make quantity accessible via the "quantity" property.
        """
        return value

    def _GetIsk(self, value, languageID, *args, **kwargs):
        """
             This will return the value formated as ISK
        """
        return evefmtutils.FmtISK(value)

    def _GetAur(self, value, languageID, *args, **kwargs):
        """
             This will return the value formated as ISK
        """
        return evefmtutils.FmtAUR(value)

    def _GetDistance(self, value, languageID, *args, **kwargs):
        """
             This will return the value formated as distance
        """
        return fmtutils.FmtDist(value, maxdemicals=kwargs.get('decimalPlaces', 3))


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.NUMERIC, NumericPropertyHandler())
