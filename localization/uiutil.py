#Embedded file name: localization\uiutil.py
import mathUtil
import settings
import re

def PrepareLocalizationSafeString(textString, messageID = None):
    if settings.qaSettings.LocWrapSettingsActive():
        return '<localized messageID=%s>%s</localized>' % (messageID, textString)
    return textString


def IsLocalizationSafeString(textString):
    return textString.startswith('<localized') and textString.endswith('localized>')


localizedStringRE = re.compile('(<localized.*?>|</localized>)')
messageIDSearchRE = re.compile('(?<=messageID=).*?(?=[ >])', re.I)
COLOR_HARDCODED = mathUtil.LtoI(2868838655L)
_isWrapModeOn = False

def WrapStringForDisplay(textString):
    """
    used to wrap displayed localized content with qa extras
    """
    if not settings.qaSettings.LocWrapSettingsActive():
        return textString
    parts = localizedStringRE.split(textString)
    for index, part in enumerate(parts):
        if part == u'</localized>':
            if settings.qaSettings.GetValue('showMessageID') or settings.qaSettings.GetValue('enableBoundaryMarkers'):
                parts[index] = '<color=0xaa999999>]</color>' + part
        if part.startswith(u'<localized'):
            messageID = messageIDSearchRE.findall(part)[0]
            boundaryText = ''
            messageIDText = ''
            if settings.qaSettings.GetValue('showMessageID') or settings.qaSettings.GetValue('enableBoundaryMarkers'):
                boundaryText = '<color=0xaa999999>[</color>'
            if settings.qaSettings.GetValue('showMessageID'):
                messageIDText = '<color=0xaa6dcff6>%s: </color>' % messageID
            parts[index] = part + boundaryText + messageIDText

    return ''.join(parts)
