#Embedded file name: carbonui\fontconst.py
import blue
import carbonui.const as uiconst
import os
import carbonui.languageConst as languageConst
DEFAULT_FONTSIZE = 10
DEFAULT_LINESPACE = 12
DEFAULT_LETTERSPACE = 0
DEFAULT_UPPERCASE = False
STYLE_DEFAULT = 'STYLE_DEFAULT'
FONTFAMILY_PER_WINDOWS_LANGUAGEID = {}
try:
    import fontConst
    FONTFAMILY_PER_WINDOWS_LANGUAGEID = fontConst.FONTFAMILY_PER_WINDOWS_LANGUAGEID
except:
    pass

SYSTEMFONTROOT = blue.win32.SHGetFolderPath(blue.win32.CSIDL_FONTS)
prioritizedFontPaths = ((languageConst.LANG_JAPANESE, STYLE_DEFAULT, ((SYSTEMFONTROOT + '\\msgothic.ttc',
    SYSTEMFONTROOT + '\\msgothic.ttc',
    SYSTEMFONTROOT + '\\msgothic.ttc',
    SYSTEMFONTROOT + '\\msgothic.ttc'),)), (languageConst.LANG_CHINESE, STYLE_DEFAULT, ((SYSTEMFONTROOT + '\\msyh.ttc',
    SYSTEMFONTROOT + '\\msyh.ttc',
    SYSTEMFONTROOT + '\\msyhbd.ttc',
    SYSTEMFONTROOT + '\\msyhbd.ttc'), (SYSTEMFONTROOT + '\\msyh.ttf',
    SYSTEMFONTROOT + '\\msyh.ttf',
    SYSTEMFONTROOT + '\\msyhbd.ttf',
    SYSTEMFONTROOT + '\\msyhbd.ttf'), (SYSTEMFONTROOT + '\\simsun.ttc',
    SYSTEMFONTROOT + '\\simsun.ttc',
    SYSTEMFONTROOT + '\\simsun.ttc',
    SYSTEMFONTROOT + '\\simsun.ttc'))))

def ResolvePriorityList(priorityListPerLanguage):
    for languageID, fontStyle, priorityList in priorityListPerLanguage:
        for each in priorityList:
            if type(each) == tuple:
                for variantPath in each:
                    isThere = os.path.exists(variantPath)
                    if not isThere:
                        break

                if isThere:
                    FONTFAMILY_PER_WINDOWS_LANGUAGEID[languageID] = {fontStyle: each}
                    break
            else:
                isThere = os.path.exists(each)
                if isThere:
                    FONTFAMILY_PER_WINDOWS_LANGUAGEID[languageID] = {fontStyle: each}
                    break


ResolvePriorityList(prioritizedFontPaths)
del ResolvePriorityList
del prioritizedFontPaths
import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('fontConst', locals())
