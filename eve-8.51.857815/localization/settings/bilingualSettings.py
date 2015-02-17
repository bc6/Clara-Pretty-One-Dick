#Embedded file name: localization/settings\bilingualSettings.py
_bilingualSettings = None
IMPORTANT_NAME_NO_SETTING = 0
IMPORTANT_NAME_ENGLISH = 1
IMPORTANT_NAME_ORIGINAL = 2

def _GetSettingsDict():
    global _bilingualSettings
    if _bilingualSettings is None:
        _bilingualSettings = {'localizationImportantNames': prefs.GetValue('localizationImportantNames', IMPORTANT_NAME_NO_SETTING),
         'languageTooltip': prefs.GetValue('languageTooltip', True),
         'localizationHighlightImportant': prefs.GetValue('localizationHighlightImportant', True)}
    return _bilingualSettings


def SetValue(key, value):
    settings = _GetSettingsDict()
    if key not in settings:
        raise KeyError('Unknown bilingual localization setting %s' % key)
    settings[key] = value


def GetValue(key):
    return _GetSettingsDict()[key]


def UpdateAndSaveSettings():
    for k, v in _GetSettingsDict().iteritems():
        if k:
            prefs.SetValue(k, v)
        else:
            prefs.DeleteValue(k)
