#Embedded file name: localization/formatters\listFormatters.py
import telemetry
from ..uiutil import PrepareLocalizationSafeString

@telemetry.ZONE_FUNCTION
def FormatGenericList(iterable, languageID = None, useConjunction = False):
    """
        Returns a formatted localization safe string representing a list of generic items.
        This list is intended for use outside of a sentence only, and selects punctuation
        appropriate to the target language.
    """
    import localization
    stringList = [ unicode(each) for each in iterable ]
    delimiter = localization.GetByLabel('UI/Common/Formatting/ListGenericDelimiter', languageID)
    if not useConjunction or len(stringList) < 2:
        listString = delimiter.join(stringList)
    elif len(stringList) == 2:
        listString = localization.GetByLabel('UI/Common/Formatting/SimpleGenericConjunction', languageID, A=stringList[0], B=stringList[1])
    else:
        listPart = delimiter.join(stringList[:-1])
        listString = localization.GetByLabel('UI/Common/Formatting/ListGenericConjunction', languageID, list=listPart, lastItem=stringList[-1])
    return PrepareLocalizationSafeString(listString, messageID='genericlist')
