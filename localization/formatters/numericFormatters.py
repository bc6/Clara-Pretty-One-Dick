#Embedded file name: localization/formatters\numericFormatters.py
import telemetry
from .. import uiutil
from .. import internalUtil
import eveLocalization

@telemetry.ZONE_FUNCTION
def FormatNumeric(value, useGrouping = False, decimalPlaces = None, leadingZeroes = None):
    result = eveLocalization.FormatNumeric(value, internalUtil.GetLanguageID(), useGrouping=useGrouping, decimalPlaces=decimalPlaces, leadingZeroes=leadingZeroes)
    return uiutil.PrepareLocalizationSafeString(result, messageID='numeric')
