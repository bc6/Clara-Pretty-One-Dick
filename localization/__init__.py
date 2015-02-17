#Embedded file name: localization\__init__.py
import formatters
import uiutil
import util
from . import const
import eveLocalization

def __GetLocalization():
    import localizationBase
    if not hasattr(__GetLocalization, 'cached'):
        __GetLocalization.cached = localizationBase.Localization()
    return __GetLocalization.cached


LOCALIZATION_REF = __GetLocalization()
LOCALIZATION_REF._GetByMessageID = eveLocalization.GetMessageByID
LOCALIZATION_REF._GetMetaData = eveLocalization.GetMetaDataByID
GetByMessageID = LOCALIZATION_REF.GetByMessageID
GetByLabel = LOCALIZATION_REF.GetByLabel
GetImportantByMessageID = LOCALIZATION_REF.GetImportantByMessageID
GetImportantByLabel = LOCALIZATION_REF.GetImportantByLabel
GetPlaceholderLabel = LOCALIZATION_REF.GetPlaceholderLabel
GetByMapping = LOCALIZATION_REF.GetByMapping
GetMetaData = LOCALIZATION_REF.GetMetaData
IsValidTypeAndProperty = LOCALIZATION_REF.IsValidTypeAndProperty
IsValidLabel = LOCALIZATION_REF.IsValidLabel
IsValidMessageID = LOCALIZATION_REF.IsValidMessageID
IsValidMapping = LOCALIZATION_REF.IsValidMessageID
LoadLanguageData = LOCALIZATION_REF.LoadLanguageData
LoadPrimaryLanguage = LOCALIZATION_REF.LoadPrimaryLanguage
GetLanguages = LOCALIZATION_REF.GetLanguages
UpdateTextCache = LOCALIZATION_REF.UpdateTextCache
GetMaxRevision = LOCALIZATION_REF.GetMaxRevision
GetHashDataDictionary = LOCALIZATION_REF.GetHashDataDictionary
IsPrimaryLanguage = LOCALIZATION_REF.IsPrimaryLanguage
ClearImportantNameSetting = LOCALIZATION_REF.ClearImportantNameSetting
SetTimeDelta = eveLocalization.SetTimeDelta

def GetTimeDeltaSeconds(*args, **kwargs):
    return eveLocalization.GetTimeDelta(*args, **kwargs)


UsePrimaryLanguageText = LOCALIZATION_REF.UsePrimaryLanguageText
UseImportantTooltip = LOCALIZATION_REF.UseImportantTooltip
HighlightImportant = LOCALIZATION_REF.HighlightImportant
FormatImportantString = LOCALIZATION_REF.FormatImportantString
CleanImportantMarkup = LOCALIZATION_REF.CleanImportantMarkup
_ReadLocalizationMainPickle = LOCALIZATION_REF._ReadLocalizationMainPickle
_ReadLocalizationLanguagePickles = LOCALIZATION_REF._ReadLocalizationLanguagePickles
_GetRawByMessageID = LOCALIZATION_REF._GetRawByMessageID
HIGHLIGHT_IMPORTANT_MARKER = const.HIGHLIGHT_IMPORTANT_MARKER
SYSTEM_LANGUAGE = ''
