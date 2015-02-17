#Embedded file name: localization/settings\qaSettings.py
import __builtin__
_qaSettings = None
NO_REPLACEMENT = 0
DIACRITIC_REPLACEMENT = 1
CYRILLIC_REPLACEMENT = 2
FULL_WIDTH_REPLACEMENT = 3

def _GetSettingsDict():
    global _qaSettings
    if _qaSettings is None:
        _qaSettings = {'simulateTooltip': prefs.GetValue('simulateTooltip', False),
         'showHardcodedStrings': prefs.GetValue('showHardcodedStrings', False),
         'showMessageID': prefs.GetValue('showMessageID', False),
         'enableBoundaryMarkers': prefs.GetValue('enableBoundaryMarkers', False),
         'characterReplacementMethod': prefs.GetValue('characterReplacementMethod', NO_REPLACEMENT),
         'textExpansionAmount': prefs.GetValue('textExpansionAmount', 0.0)}
    return _qaSettings


def SetValue(key, value):
    settings = _GetSettingsDict()
    if key not in settings:
        raise KeyError('Unknown localization QA setting %s' % key)
    if key not in ('characterReplacementMethod', 'textExpansionAmount'):
        value = type(settings[key])(value)
    settings[key] = value


def GetValue(key):
    return _GetSettingsDict()[key]


def UpdateAndSaveSettings():
    for k, v in _GetSettingsDict().iteritems():
        if k:
            prefs.SetValue(k, v)
        else:
            prefs.DeleteValue(k)

    if hasattr(LocWrapSettingsActive, 'cachedValue'):
        del LocWrapSettingsActive.cachedValue
    if boot.role == 'client':
        sm.RemoteSvc('localizationServer').UpdateLocalizationQAWrap(LocWrapSettingsActive())


def LocWrapSettingsActive():
    if not hasattr(LocWrapSettingsActive, 'cachedValue'):
        if boot.role == 'server':
            if hasattr(__builtin__, 'session') and session:
                return session.GetSessionVariable('localizationQAWrap', False)
            return False
        settings = _GetSettingsDict()
        LocWrapSettingsActive.cachedValue = any([settings['showHardcodedStrings'],
         settings['showMessageID'],
         settings['enableBoundaryMarkers'],
         settings['characterReplacementMethod'] != NO_REPLACEMENT])
    return LocWrapSettingsActive.cachedValue


def PseudolocSettingsActive():
    return _GetSettingsDict()['characterReplacementMethod'] != NO_REPLACEMENT
