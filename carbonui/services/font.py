#Embedded file name: carbonui/services\font.py
import blue
import telemetry
import types
import fontConst
import trinity
import carbonui.const as uiconst
import carbonui.languageConst as languageConst
from carbonui.util.stringManip import GetAsUnicode
from carbonui.util.bunch import Bunch
from carbon.common.script.util.commonutils import StripTags
b = 1
i = 2
u = 4
exports = {'fontflags.b': b,
 'fontflags.i': i,
 'fontflags.u': u}

class GlyphStringBoundingBox(object):

    def __init__(self):
        self.xMin = 0
        self.xMax = 0
        self.yMin = 0
        self.yMax = 0

    def Width(self):
        return self.xMax - self.xMin

    def Height(self):
        return self.yMax - self.yMin


class Tr2GlyphString(list):
    __guid__ = 'font.Tr2GlyphString'

    def __init__(self, other = None):
        if other:
            list.__init__(self, other)
        self.Reset()

    def __iadd__(self, other):
        list.extend(self, other)
        self._textDirty = True
        return self

    def Reset(self):
        self.baseLine = 0
        self.baseHeight = 0
        self.last = (None, 0)
        self.asc = 0
        self.des = 0
        self.width = 0
        self.strong = 0
        self.shadow = None
        self.fontsize = 0
        self.text = u''
        self._textDirty = True
        while self:
            list.pop(self)

    @telemetry.ZONE_METHOD
    def Remove(self, startIdx, endIdx):
        self._textDirty = True
        for i in xrange(startIdx, endIdx):
            self.pop(startIdx)

    def FlushFromIndex(self, idx):
        self._textDirty = True
        while len(self) > idx:
            list.pop(self, -1)

    def FlushToIndex(self, idx):
        self._textDirty = True
        for i in xrange(idx):
            if len(self):
                list.pop(self, 0)

    @telemetry.ZONE_METHOD
    def Insert(self, params, text, idx, align = 0):
        if not text:
            return None
        self._textDirty = True
        color = params.color or -1
        if type(color) != types.IntType:
            tricol = trinity.TriColor(*color)
            color = tricol.AsInt()
        uicore.font.ResolveFontFamily(params)
        dpi_wordspace = int(params.wordspace * uicore.desktop.dpiScaling + 0.5)
        dpi_fontsize = int(params.fontsize * uicore.desktop.dpiScaling + 0.5)
        dpi_letterspace = int(params.letterspace * uicore.desktop.dpiScaling + 0.5)
        self.fontsize = dpi_fontsize
        lastFontIndex, lastGlyphIndex = (None, None)
        for char in text:
            if char == u'\xa0':
                rchar = u' '
            else:
                rchar = char
            fontIndex, glyphIndex = trinity.fontMan.LookupGlyphIndex(params.font, ord(rchar))
            if fontIndex != lastFontIndex:
                self.GetMetrics(fontIndex)
                self.baseLine = max(self.baseLine, self.asc)
                self.baseHeight = max(self.baseHeight, self.asc - self.des)
                kern = 0
            else:
                kern = trinity.fontMan.LookupKerningXP(fontIndex, glyphIndex, lastGlyphIndex)
            lastFontIndex, lastGlyphIndex = fontIndex, glyphIndex
            sbit = trinity.fontMan.LookupSBit(fontIndex, dpi_fontsize, dpi_fontsize, glyphIndex)
            advance = sbit.xadvance + dpi_letterspace + kern
            if rchar == u' ':
                advance += dpi_wordspace
            self.insert(idx, (advance,
             align,
             color,
             sbit,
             char,
             self.asc,
             self.des,
             params.Copy()))
            idx += 1
            self.width += advance

    @telemetry.ZONE_METHOD
    def GetText(self):
        if self._textDirty:
            self.text = ''.join([ charData[4] for charData in self ])
            self._textDirty = False
        return self.text

    @telemetry.ZONE_METHOD
    def Append(self, params, text, align = 0):
        idx = len(self)
        self.Insert(params, text, idx, align)

    @telemetry.ZONE_METHOD
    def Reload(self):
        data = [ (params, char) for advance, align, color, sbit, char, asc, des, params in self ]
        del self[:]
        for params, char in data:
            self.Append(params, char)

    @telemetry.ZONE_METHOD
    def DrawToBuf(self, buf, bx0, by0, checkUnderline = 1):
        x = 0
        for t in self:
            advance = t[0]
            sbit = t[3]
            params = t[7]
            color = params.color or -1
            if type(color) != types.IntType:
                tricol = trinity.TriColor(*color)
                color = tricol.AsInt()
            hasUnderline = bool(params.underline)
            if hasUnderline:
                extraSpace = advance - sbit.xadvance
                sbit.ToBufferWithUnderline(buf.data, buf.width, buf.height, buf.pitch, x + bx0, by0, color, extraSpace)
            else:
                sbit.ToBuffer(buf.data, buf.width, buf.height, buf.pitch, x + bx0, by0, color)
            x += t[0]

    @telemetry.ZONE_METHOD
    def GetMetrics(self, face_id):
        self.asc, self.des = trinity.fontMan.LookupMetrics(face_id, self.fontsize, self.fontsize)

    @telemetry.ZONE_METHOD
    def AddSpace(self, params, width = 0.0):
        uicore.font.ResolveFontFamily(params)
        fgi = trinity.fontMan.LookupGlyphIndex(params.font, ord(' '))
        sbit = trinity.fontMan.LookupSBit(fgi[0], self.fontsize, self.fontsize, fgi[1])
        self.append((width,
         0,
         -1,
         sbit,
         ' ',
         0,
         0,
         params))
        self.width = max(self.width, self.width + width)

    @telemetry.ZONE_METHOD
    def GetBBox(self):
        baseLine = baseHeight = 0
        bbox = GlyphStringBoundingBox()
        x = 0
        for t in self:
            sbit = t[3]
            bbox.xMin = min(sbit.x + sbit.xOffset + x, bbox.xMin)
            bbox.xMax = max(sbit.x + sbit.xOffset + x + sbit.width, bbox.xMax)
            bbox.yMin = min(sbit.y + sbit.yOffset, bbox.yMin)
            bbox.yMax = max(sbit.y + sbit.yOffset + sbit.height, bbox.yMax)
            baseLine = max(baseLine, t[5])
            baseHeight = max(baseHeight, t[5] - t[6])
            x += t[0]

        self.baseLine = baseLine
        self.baseHeight = baseHeight
        self.width = x
        return bbox

    def GetWidth(self):
        self.GetBBox()
        return self.width


import re
tag = re.compile('<color=0x.*?>|<right>|<center>|<left>')

class FontHandler(object):
    defaultLabelClass = None

    def __init__(self, *args, **kwds):
        self.Prime()

    def Prime(self):
        self.measureCache = {}
        self.textMeasureCache = {}
        self.textLanguageIDCache = {}
        regexes = []
        for languageID, windowsLanguageID, REGEX, isExclusive in (('JA',
          languageConst.LANG_JAPANESE,
          (uiconst.JA_CHARACTERS,),
          True),
         ('ZH',
          languageConst.LANG_CHINESE,
          (uiconst.REGEX_RANGE_CJK_IDEOGRAPHS,),
          False),
         ('JA',
          languageConst.LANG_JAPANESE,
          (uiconst.REGEX_RANGE_HIRAGANA,
           uiconst.REGEX_RANGE_KATAKANA,
           uiconst.REGEX_RANGE_KATAKANA_PHONETIC_EXTENSIONS,
           uiconst.REGEX_RANGE_HALF_WIDTH_KATAKANA),
          False),
         ('KO',
          languageConst.LANG_KOREAN,
          (uiconst.REGEX_RANGE_HANGUL,),
          False)):
            compiledRegex = re.compile(u'([' + u']+ *|['.join(REGEX) + u']+ *)', re.UNICODE)
            regexes.append((languageID,
             windowsLanguageID,
             compiledRegex,
             isExclusive))

        self.regexes = regexes

    def DeTag(self, s):
        return tag.sub('', s)

    @telemetry.ZONE_METHOD
    def GetTextHeight(self, strng, width = 0, font = None, fontsize = None, lineSpacing = 0.0, letterspace = 0, shadow = [(1, -1, -1090519040)], uppercase = 0, specialIndent = 0, getTextObj = 0, tabs = [], fontPath = None, fontStyle = None, fontFamily = None, linespace = None, maxLines = None, **kwds):
        if strng is None or strng == '':
            return 0
        fontsize = fontsize or fontConst.DEFAULT_FONTSIZE
        letterspace = letterspace or fontConst.DEFAULT_LETTERSPACE
        uppercase = uppercase or fontConst.DEFAULT_UPPERCASE
        if maxLines == 1:
            width = 0
            strng = u'\xd3gd'
        else:
            strng = GetAsUnicode(strng)
        cacheKey = (strng,
         width,
         font,
         fontsize,
         lineSpacing,
         letterspace,
         maxLines,
         uppercase,
         specialIndent,
         getTextObj,
         uicore.fontSizeFactor)
        cache = self.GetCache(cacheKey)
        if cache:
            return cache
        if self.defaultLabelClass is None:
            from carbonui.control.label import LabelCore
            self.defaultLabelClass = LabelCore
        t = self.defaultLabelClass(text=strng, parent=None, align=uiconst.TOPLEFT, width=width, tabs=tabs, fontsize=fontsize, lineSpacing=lineSpacing, letterspace=letterspace, maxLines=maxLines, uppercase=uppercase, specialIndent=specialIndent, fontPath=fontPath, fontStyle=fontStyle, fontFamily=fontFamily, shadow=shadow, measuringText=not getTextObj)
        if getTextObj:
            retval = t
        else:
            retval = t.textheight
        self.SetCache(cacheKey, retval)
        return retval

    @telemetry.ZONE_METHOD
    def GetTextWidth(self, strng, fontsize = 12, letterspace = 0, uppercase = 0, font = None, fontPath = None, fontStyle = None, fontFamily = None):
        if not strng:
            return 0
        font = font
        fontsize = fontsize or fontConst.DEFAULT_FONTSIZE
        letterspace = letterspace or fontConst.DEFAULT_LETTERSPACE
        uppercase = uppercase or fontConst.DEFAULT_UPPERCASE
        cacheKey = (strng,
         fontsize,
         letterspace,
         uppercase,
         font,
         uicore.fontSizeFactor)
        if cacheKey in self.textMeasureCache:
            return self.textMeasureCache[cacheKey]
        if '<br>' in strng:
            val = max([ self.GetTextWidth(line, fontsize, letterspace, uppercase, font) for line in strng.split('<br>') ])
        else:
            if self.defaultLabelClass is None:
                from carbonui.control.label import LabelCore
                self.defaultLabelClass = LabelCore
            textmeasurer = self.defaultLabelClass(text=StripTags(strng, ignoredTags=['b']), parent=None, align=uiconst.TOPLEFT, fontsize=fontsize, letterspace=letterspace, uppercase=uppercase, measuringText=True, fontPath=fontPath, fontStyle=fontStyle, fontFamily=fontFamily)
            val = textmeasurer.textwidth
        self.textMeasureCache[cacheKey] = val
        return val

    @telemetry.ZONE_METHOD
    def MeasureTabstops(self, stringsData, margin = None, minwidth = 32):
        if margin is None:
            margin = 6
        tabstops = []
        tabCount = 0
        for stringData in stringsData:
            if len(stringData) == 5:
                tabSeperatedColumns, fontsize, letterSpace, shift, uppercase = stringData
            else:
                tabSeperatedColumns, fontsize, letterSpace, shift = stringData
                uppercase = 0
            tabSeperatedColumns = GetAsUnicode(tabSeperatedColumns)
            columnTexts = tabSeperatedColumns.split('<t>')
            columnTextsCount = len(columnTexts)
            if columnTextsCount > tabCount:
                tabstops.extend([minwidth] * (columnTextsCount - tabCount))
                tabCount = columnTextsCount
            i = 0
            for columnText in columnTexts:
                width = max(0, shift - margin) + margin + self.GetTextWidth(columnText, fontsize, letterSpace, uppercase) + margin + 2
                if width > tabstops[i]:
                    tabstops[i] = width
                i += 1
                shift = 0

        i = 1
        while i < tabCount:
            tabstops[i] += tabstops[i - 1]
            i += 1

        return tabstops

    @telemetry.ZONE_METHOD
    def MergeTabstops(self, tabs1, tabs2):
        t1, t2 = self.GetTabstopsAsWidth(tabs1), self.GetTabstopsAsWidth(tabs2)
        if not len(t2) and len(t1):
            return tabs1
        if not len(t1) and len(t2):
            return tabs2
        if not len(t1) and not len(t2):
            return []
        newtabs = [max(t1[0], t2[0])]
        for i in xrange(len(t1) - 1):
            if len(t1) > i + 1:
                _t1 = t1[i + 1]
            else:
                _t1 = 0
            if len(t2) > i + 1:
                _t2 = t2[i + 1]
            else:
                _t2 = 0
            newtabs.append(newtabs[i] + max(_t1, _t2))

        return newtabs

    @telemetry.ZONE_METHOD
    def GetTabstopsAsWidth(self, tabs1):
        tabs = tabs1[:1]
        for i in xrange(len(tabs1) - 1):
            tabs.append(tabs1[i + 1] - tabs1[i])

        return tabs

    @telemetry.ZONE_METHOD
    def GetNodeCopyData(self, node, fromIdx, toIdx):
        glyphString = self.GetLineGlyphString(node)
        if glyphString:
            text = glyphString.GetText()
            if toIdx == -1:
                return text[fromIdx:]
            else:
                return text[fromIdx:toIdx]
        return ''

    def GetLineGlyphString(self, node):
        return node.get('glyphString', None)

    def GetLetterIdx(self, node, cursorXpos):
        i = 0
        glyphString = self.GetLineGlyphString(node)
        if glyphString:
            w = 0
            for glyph in glyphString:
                if w <= cursorXpos <= w + glyph[0]:
                    glyphCenter = glyph[0] / 2.0
                    if cursorXpos > w + glyphCenter:
                        return (i + 1, int(w + glyph[0]))
                    return (i, int(w))
                i += 1
                w += glyph[0]

            if cursorXpos > w:
                return (i, int(w))
        return (0, 0)

    def GetWidthToIdx(self, node, idx, getWidth = 0):
        glyphString = self.GetLineGlyphString(node)
        if glyphString:
            if idx < len(glyphString):
                w = sum([ t[0] for t in glyphString[:idx] ])
                if getWidth:
                    return (int(w), int(glyphString[idx][0]))
                else:
                    return int(w)
            else:
                w = sum([ t[0] for t in glyphString ])
                if getWidth:
                    return (int(w), 0)
                else:
                    return int(w)
        if getWidth:
            return (0, 0)
        else:
            return 0

    @telemetry.ZONE_METHOD
    def GetFontPathFromFontFamily(self, fontFamily, fontStyle = None, bold = False, italic = False):
        fontPath = None
        if type(fontFamily) == dict:
            fontStyle = fontStyle or fontConst.STYLE_DEFAULT
            if fontStyle in fontFamily:
                fontFamily = fontFamily[fontStyle]
            else:
                fontFamily = fontFamily[fontConst.STYLE_DEFAULT]
        if type(fontFamily) in types.StringTypes:
            fontPath = fontFamily
        elif type(fontFamily) in (tuple, list):
            variation = bold * 2 + italic * 1
            if len(fontFamily) > variation:
                fontPath = fontFamily[variation]
            else:
                fontPath = fontFamily[0]
        return fontPath

    @telemetry.ZONE_METHOD
    def ResolveFontFamily(self, params):
        if params.fontPath:
            params.font = params.fontPath
            return params.fontPath
        fontFamily = params.fontFamily
        if not fontFamily:
            fontFamily = self.GetFontFamilyBasedOnClientLanguageID()
        params.font = self.GetFontPathFromFontFamily(fontFamily, params.fontStyle, bool(params.bold), bool(params.italic))

    def GuessWindowsLanguageID(self, txt):
        if txt in self.textLanguageIDCache:
            return self.textLanguageIDCache[txt]
        matches = []
        for languageID, windowsLanguageID, regex, isExclusive in self.regexes:
            matchingLetters = len(txt) - len(regex.sub('', txt))
            if matchingLetters:
                if isExclusive:
                    matches = [(matchingLetters, languageID, windowsLanguageID)]
                    break
                else:
                    matches.append((matchingLetters, languageID, windowsLanguageID))
            if matchingLetters == len(txt):
                break

        matches.sort()
        if matches:
            self.textLanguageIDCache[txt] = matches[-1][-1]
            return matches[-1][-1]

    def GetWindowsLanguageIDForText(self, txt):
        if txt in self.textLanguageIDCache:
            return self.textLanguageIDCache[txt]
        isLatinBased = self.IsLatinBased(txt)
        if isLatinBased:
            self.textLanguageIDCache[txt] = languageConst.LANG_ENGLISH
            return languageConst.LANG_ENGLISH
        guessedLanguageID = self.GuessWindowsLanguageID(txt)
        self.textLanguageIDCache[txt] = guessedLanguageID
        return guessedLanguageID

    def IsLatinBased(self, txt):
        for codepage in ('windows-1252', 'windows-1251', 'windows-1253', 'windows-1254', 'windows-1257', 'windows-1250'):
            try:
                txt.encode(codepage)
                return True
            except:
                pass

    def GetFontDefault(self):
        """ Returns the default, regular font (full path), based on client language """
        family = self.GetFontFamilyBasedOnClientLanguageID()[fontConst.STYLE_DEFAULT]
        regular, bold, italic, boldItalic = family
        return regular

    @telemetry.ZONE_METHOD
    def GetFontFamilyBasedOnClientLanguageID(self):
        if session:
            languageID = session.languageID
        else:
            languageID = 'EN'
        if languageID == 'ZH':
            return self.GetFontFamilyBasedOnWindowsLanguageID(languageConst.LANG_CHINESE)
        elif languageID == 'JA':
            return self.GetFontFamilyBasedOnWindowsLanguageID(languageConst.LANG_JAPANESE)
        else:
            return self.GetFontFamilyBasedOnWindowsLanguageID(languageConst.LANG_ENGLISH)

    @telemetry.ZONE_METHOD
    def GetFontFamilyBasedOnWindowsLanguageID(self, windowsLanguageID):
        """Function to provide client specific set of fonts per langangeID.
        Family Sets should be provided through fontConst.FONTFAMILY_PER_WINDOWS_LANGUAGEID"""
        return fontConst.FONTFAMILY_PER_WINDOWS_LANGUAGEID.get(windowsLanguageID, None)

    def GetCache(self, key):
        cache = self.measureCache.get(key, None)
        if cache:
            return cache[1]

    def SetCache(self, key, value):
        ts = blue.os.GetWallclockTime()
        self.measureCache[key] = (ts, value)

    def InvalidateTextMeasureCache(self):
        t = blue.os.GetWallclockTime()
        ks = self.measureCache.keys()
        for k in ks:
            cacheTime = self.measureCache[k][0]
            if t - cacheTime > 300000000L:
                del self.measureCache[k]

    def GetParams(self):
        fontParams = Bunch()
        fontParams.__doc__ = 'Font Parameters'
        fontParams.fontStyle = None
        fontParams.fontFamily = None
        fontParams.fontPath = None
        fontParams.fontsize = fontConst.DEFAULT_FONTSIZE
        fontParams.letterspace = fontConst.DEFAULT_LETTERSPACE or 0
        fontParams.uppercase = fontConst.DEFAULT_UPPERCASE
        fontParams.lineSpacing = 0.0
        fontParams.wordspace = 0
        fontParams.color = -1
        fontParams.underline = 0
        fontParams.bold = 0
        fontParams.italic = 0
        fontParams.face = None
        return fontParams

    def GetGlyphString(self):
        return Tr2GlyphString()

    def AppGetSetting(self, setting, default):
        try:
            return settings.public.ui.Get(setting, default)
        except (AttributeError, NameError):
            return default

    def AppSetSetting(self, setting, value):
        try:
            settings.public.ui.Set(setting, value)
        except (AttributeError, NameError):
            pass
