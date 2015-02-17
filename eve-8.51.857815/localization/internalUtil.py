#Embedded file name: localization\internalUtil.py
import localstorage
import crestUtil

def GetStandardizedLanguageID(languageID):
    if not hasattr(GetStandardizedLanguageID, 'cachedLanguages'):
        GetStandardizedLanguageID.cachedLanguages = {'en': 'en-us',
         'en-us': 'en-us',
         'es': 'es',
         'fr': 'fr',
         'it': 'it',
         'ja': 'ja',
         'ru': 'ru',
         'de': 'de',
         'zh': 'zh'}
    return GetStandardizedLanguageID.cachedLanguages.get(languageID.lower(), 'en-us')


_cachedLanguageId = None

def GetLanguageIDClient():
    """
    Returns the current language as an IETF language tag, with backwards compatibility from ISO 639 (used by MLS).
    """
    global _cachedLanguageId
    if _cachedLanguageId:
        return _cachedLanguageId
    try:
        _cachedLanguageId = GetStandardizedLanguageID(prefs.languageID)
        return _cachedLanguageId
    except (KeyError, AttributeError):
        return 'en-us'


def GetLanguageID():
    try:
        ret = None
        try:
            ls = localstorage.GetLocalStorage()
            ret = ls['languageID']
            crestUtil.SetTLSMarkerLocalized()
        except KeyError:
            pass

        if ret is None:
            ret = GetStandardizedLanguageID(session.languageID)
        return ret
    except (KeyError, AttributeError):
        return 'en-us'


if boot.role == 'client':
    GetLanguageID = GetLanguageIDClient

def ClearLanguageID():
    global _cachedLanguageId
    _cachedLanguageId = None


if boot.role == 'client':
    GetLanguageID = GetLanguageIDClient
