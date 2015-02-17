#Embedded file name: carbonui/control\label.py
import blue
import telemetry
from carbonui.primitives.base import ScaleDpi, ReverseScaleDpi
import trinity
import mathUtil
from carbonui.control.baselink import BaseLinkCoreOverride as BaseLink
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import VisibleBase
from carbonui.primitives.fill import Fill
from carbonui.primitives.line import Line
from carbonui.util.stringManip import GetAsUnicode, UpperCase
from carbonui.util.bunch import Bunch
from carbon.common.script.util.commonutils import StripTags
from carbonui.util.various_unsorted import StringColorToHex
from carbonui.control.menuLabel import MenuLabel
import carbonui.const as uiconst
import fontConst
import sys
import log
import re
import localization
import localization.settings
from localization.pseudoloc import Pseudolocalize
import types
from carbon.common.script.util.timerstuff import AutoTimer
import eveLocalization
layoutCountStat = blue.statistics.Find('CarbonUI/labelLayout')
if not layoutCountStat:
    layoutCountStat = blue.CcpStatisticsEntry()
    layoutCountStat.name = 'CarbonUI/labelLayout'
    layoutCountStat.type = 1
    layoutCountStat.resetPerFrame = True
    layoutCountStat.description = 'The number of calls to LabelCore.Layout per frame'
    blue.statistics.Register(layoutCountStat)
TEXT_ALIGN_LEFT = 0
TEXT_ALIGN_RIGHT = 1
TEXT_ALIGN_CENTER = 2
ELLIPSIS = u'\u2026'
SINGLE_LINE_NEWLINE_PATTERN = re.compile('<br>|\r\n|\n')
STOPWRAP = -1
COLOR_WHITE_FULLALPHA = -1

class LabelCore(VisibleBase):
    __guid__ = 'uicontrols.LabelCore'
    __renderObject__ = trinity.Tr2Sprite2dTextObject
    __notifyevents__ = ['OnUIScalingChange']
    isDragObject = True
    busy = False
    linespace = 0
    default_name = 'label'
    default_state = uiconst.UI_DISABLED
    default_fontsize = None
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None
    default_linkStyle = uiconst.LINKSTYLE_SUBTLE
    default_color = None
    default_text = ''
    default_tabs = []
    default_tabMargin = uiconst.LABELTABMARGIN
    default_uppercase = False
    default_maxLines = None
    default_wrapMode = uiconst.WRAPMODE_FORCEWORD
    default_lineSpacing = 0.0
    default_letterspace = 0
    default_underline = 0
    default_bold = 0
    default_italic = 0
    default_specialIndent = 0
    default_autoDetectCharset = False
    default_showEllipsis = False
    default_autoUpdate = True
    default_dropShadow = False
    _underline = default_underline
    _bold = default_bold
    _italic = default_italic
    _uppercase = default_uppercase
    _letterspace = default_letterspace
    _lineSpacing = default_lineSpacing
    _wrapMode = default_wrapMode
    _maxLines = default_maxLines
    _tabs = default_tabs
    _setWidth = 0
    _setHeight = 0
    _minCursor = 0
    _alphaFadeLeft = None
    _alphaFadeRight = None
    _alphaFadeBottom = None
    _fontStyle = default_fontStyle
    _fontPath = default_fontPath
    _fontFamily = default_fontFamily
    _fontsize = default_fontsize
    _setText = ''
    _localizationText = None
    _parseDirty = False
    _layoutDirty = False
    _inlineObjects = None
    _inlineObjectsBuff = None
    _measurerProperties = None
    _lastAddTextData = None
    actualTextHeight = 0
    actualTextWidth = 0
    localizationWrapOn = False
    tooltipPosition = None
    auxTooltipPosition = None
    autoFitToText = False
    _resolvingAutoSizing = False
    _hilite = 0
    _mouseOverUrl = None
    _mouseOverUrlID = None
    _mouseOverTextBuff = None
    _lastAbs = None

    def ApplyAttributes(self, attributes):
        textcolor = attributes.get('color', self.default_color)
        attributes.color = None
        VisibleBase.ApplyAttributes(self, attributes)
        if self.default_fontsize is None:
            self.default_fontsize = fontConst.DEFAULT_FONTSIZE
        self.collectWordsInStack = attributes.get('collectWordsInStack', False)
        self.mouseOverWordCallback = attributes.get('mouseOverWordCallback', None)
        self.autoFitToText = attributes.get('autoFitToText', False)
        self.InitMeasurer()
        self.renderObject.fontMeasurer = self.measurer
        if self.align != uiconst.TOALL:
            self._setWidth = self.width
            self._setHeight = self.height
        self.busy = 1
        self.InitLocalizationFlag()
        self._tabMargin = attributes.get('tabMargin', self.default_tabMargin)
        self.dropShadow = attributes.get('dropShadow', self.default_dropShadow)
        self.autoUpdate = attributes.get('autoUpdate', self.default_autoUpdate)
        self.tabs = attributes.get('tabs', self.default_tabs)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        if not self.fontPath and not self.fontFamily:
            self.fontFamily = uicore.font.GetFontFamilyBasedOnClientLanguageID()
        self.linkStyle = attributes.get('linkStyle', self.default_linkStyle)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.underline = attributes.get('underline', self.default_underline)
        self.bold = attributes.get('bold', self.default_bold)
        self.italic = attributes.get('italic', self.default_italic)
        self.uppercase = attributes.get('uppercase', self.default_uppercase)
        self.wrapMode = attributes.get('wrapMode', self.default_wrapMode)
        self.showEllipsis = attributes.get('showEllipsis', self.default_showEllipsis)
        self.lineSpacing = attributes.get('lineSpacing', self.default_lineSpacing)
        self.letterspace = attributes.get('letterspace', self.default_letterspace)
        self.specialIndent = attributes.get('specialIndent', self.default_specialIndent)
        self.autoDetectCharset = attributes.get('autoDetectCharset', self.default_autoDetectCharset)
        if attributes.get('singleline', False):
            maxLines = 1
        else:
            maxLines = attributes.get('maxLines', self.default_maxLines)
        self.maxLines = maxLines
        self._measuringText = attributes.get('measuringText', False)
        if textcolor is not None:
            self.SetTextColor(textcolor)
        else:
            self.fontColor = COLOR_WHITE_FULLALPHA
        self.busy = 0
        self.text = attributes.get('text', self.default_text)
        try:
            sm.RegisterNotify(self)
        except:
            pass

    def InitMeasurer(self):
        self.measurer = trinity.Tr2FontMeasurer()
        self.renderObject.fontMeasurer = self.measurer

    def InitLocalizationFlag(self):
        self.localizationWrapOn = localization.settings.qaSettings.LocWrapSettingsActive()

    def Close(self):
        self._inlineObjects = None
        self._inlineObjectsBuff = None
        self._hiliteResetTimer = None
        if self.renderObject:
            self.renderObject.fontMeasurer = None
        self.measurer = None
        VisibleBase.Close(self)

    def OnUIScalingChange(self, *args):
        if self.destroyed or self.measurer is None:
            return
        self.measurer.fontSize = 0
        self.Layout('OnUIScalingChange')

    def ResolveAutoSizing(self):
        """ Figure out if we should adjust the width/height of this sprite
        based on the size of the text.
        The rule is if the user sets width or height we don't want to alter the w/h
        of this sprite. 
        Exception from this is if the alignment is in such way that 
        the userset w/h does not make sense, like if the alignment is TOTOP, setting width
        does not make sense cause the width would be defined by the size of the parent.
        This is to replace the autoWidth and autoHeight flags user could pass in prior to 
        CarbonUI but that method failed in many cases when the auto* flags didn't fit the 
        set alignment.
        """
        self._resolvingAutoSizing = True
        if self.autoFitToText:
            setWidth = None
            setHeight = None
        else:
            setWidth = self._setWidth
            setHeight = self._setHeight
        align = self.align
        if not self.isAffectedByPushAlignment:
            self.width = setWidth or self.textwidth
            self.height = setHeight or self.textheight
        elif align in (uiconst.TOLEFT,
         uiconst.TORIGHT,
         uiconst.TOLEFT_NOPUSH,
         uiconst.TORIGHT_NOPUSH):
            self.width = setWidth or self.textwidth
        elif align in (uiconst.TOBOTTOM,
         uiconst.TOTOP,
         uiconst.TOBOTTOM_NOPUSH,
         uiconst.TOTOP_NOPUSH):
            self.height = setHeight or self.textheight
        self._resolvingAutoSizing = False

    def SetLeftAlphaFade(self, fadeStart = 0, maxFadeWidth = 0):
        if maxFadeWidth:
            self._alphaFadeLeft = (fadeStart, maxFadeWidth)
            self._UpdateAlphaFade()
        else:
            self._alphaFadeLeft = None
            measurer = self.measurer
            if measurer:
                measurer.fadeLeftStart = 0
                measurer.fadeLeftEnd = 0

    def SetRightAlphaFade(self, fadeEnd = 0, maxFadeWidth = 0):
        """
        Fades the rightside of the text if fadeEnd is 
        less than textwidth. maxFadeWidth defines the maximum
        fade but the fade is capped if the difference between
        the fadeEnd and textwidth is less than maxFadeWidth.
        If maxFadeWidth is 0 (default) the fade is disabled.
        """
        if maxFadeWidth:
            self._alphaFadeRight = (fadeEnd, maxFadeWidth)
            self._UpdateAlphaFade()
        else:
            self._alphaFadeRight = None
            measurer = self.measurer
            if measurer:
                measurer.fadeRightStart = sys.maxint
                measurer.fadeRightEnd = sys.maxint

    def SetBottomAlphaFade(self, fadeEnd = 0, maxFadeHeight = 0):
        """
        Fades the bottom of the text if fadeEnd is 
        less than textheight. maxFadeHeight defines the maximum
        fade but the fade is capped if the difference between
        the fadeEnd and textheight is less than maxFadeHeight.
        If maxFadeHeight is 0 (default) the fade is disabled.        
        """
        if maxFadeHeight:
            self._alphaFadeBottom = (fadeEnd, maxFadeHeight)
            self._UpdateAlphaFade()
        else:
            self._alphaFadeBottom = None
            measurer = self.measurer
            if measurer:
                measurer.fadeBottomStart = sys.maxint
                measurer.fadeBottomEnd = sys.maxint

    def _UpdateAlphaFade(self):
        measurer = self.measurer
        if not measurer:
            return
        if self._alphaFadeLeft:
            fadeStart, length = self._alphaFadeLeft
            fadeStart = ScaleDpi(fadeStart - 0.5)
            length = ScaleDpi(length)
            measurer.fadeLeftStart = fadeStart
            measurer.fadeLeftEnd = fadeStart + length
        if self._alphaFadeRight:
            fadeEnd, length = self._alphaFadeRight
            if self.textwidth > fadeEnd:
                diff = self.textwidth - fadeEnd
                length = ScaleDpi(min(length, diff))
                fadeEnd = ScaleDpi(fadeEnd - 0.5)
                measurer.fadeRightStart = max(0, fadeEnd - length)
                measurer.fadeRightEnd = fadeEnd
            else:
                measurer.fadeRightStart = sys.maxint
                measurer.fadeRightEnd = sys.maxint
        if self._alphaFadeBottom:
            fadeEnd, length = self._alphaFadeRight
            if self.textheight > fadeEnd:
                diff = self.textheight - fadeEnd
                length = ScaleDpi(min(length, diff))
                fadeEnd = ScaleDpi(fadeEnd - 0.5)
                measurer.fadeBottomStart = max(0, fadeEnd - length)
                measurer.fadeBottomEnd = fadeEnd
            else:
                measurer.fadeBottomStart = sys.maxint
                measurer.fadeBottomEnd = sys.maxint

    @apply
    def mincommitcursor():

        def fset(self, value):
            pass

        def fget(self):
            if uicore.desktop.dpiScaling != 1.0:
                return ReverseScaleDpi(self._minCursor + 0.5)
            else:
                return self._minCursor

        return property(**locals())

    @apply
    def textwidth():

        def fset(self, value):
            pass

        def fget(self):
            if uicore.desktop.dpiScaling != 1.0:
                return ReverseScaleDpi(self.actualTextWidth + 0.5)
            else:
                return self.actualTextWidth

        return property(**locals())

    @apply
    def textheight():

        def fset(self, value):
            pass

        def fget(self):
            if uicore.desktop.dpiScaling != 1.0:
                return ReverseScaleDpi(self.actualTextHeight + 0.5)
            else:
                return self.actualTextHeight

        return property(**locals())

    @apply
    def displayRect():
        fget = VisibleBase.displayRect.fget

        def fset(self, value):
            VisibleBase.displayRect.fset(self, value)
            ro = self.renderObject
            if ro:
                if self.isAffectedByPushAlignment:
                    ro.textWidth = ro.displayWidth
                    ro.textHeight = ro.displayHeight
                else:
                    ro.textWidth = ScaleDpi(self.width)
                    ro.textHeight = ScaleDpi(self.height)

        return property(**locals())

    @apply
    def width():
        doc = 'Width of UI element'
        fget = VisibleBase.width.fget

        def fset(self, value):
            VisibleBase.width.fset(self, value)
            if not getattr(self, '_resolvingAutoSizing', False) and self.align != uiconst.TOALL:
                if value != self._setWidth:
                    self._layoutDirty = True
                self._setWidth = value
                if getattr(self, 'autoUpdate', False) and not self.isAffectedByPushAlignment:
                    self.Layout('width')

        return property(**locals())

    @apply
    def height():
        doc = 'Height of UI element'
        fget = VisibleBase.height.fget

        def fset(self, value):
            VisibleBase.height.fset(self, value)
            if not getattr(self, '_resolvingAutoSizing', False) and self.align != uiconst.TOALL:
                self._setHeight = value
                if getattr(self, 'autoUpdate', False) and not self.busy and not self.isAffectedByPushAlignment:
                    self.Layout('height')

        return property(**locals())

    @apply
    def hint():

        def fget(self):
            return getattr(self, '_hint', None)

        def fset(self, value):
            if not getattr(self, '_resolvingInlineHint', False):
                self._objectHint = value
            else:
                VisibleBase.hint.fset(self, value)

        return property(**locals())

    @apply
    def dropShadow():
        doc = 'Shadow on text'

        def fget(self):
            return self._dropShadow

        def fset(self, value):
            self._dropShadow = value
            ro = self.renderObject
            if ro:
                ro.dropShadow = value

        return property(**locals())

    def SetText(self, text):
        if self.localizationWrapOn:
            if self._localizationText == text:
                return
            self._localizationText = text
        if self._setText != text:
            self._parseDirty = True
            if self.localizationWrapOn and isinstance(text, basestring):
                if localization.settings.qaSettings.PseudolocSettingsActive() and localization.uiutil.IsLocalizationSafeString(text):
                    text = Pseudolocalize(text)
                try:
                    text = localization.uiutil.WrapStringForDisplay(text)
                except:
                    pass

            self._setText = text
            if self.autoUpdate:
                self.Layout('SetText')

    def GetText(self):
        return self._setText

    text = property(GetText, SetText)

    @apply
    def singleline():

        def fget(self):
            return self.maxLines == 1

        def fset(self, value):
            if value:
                self.maxLines = 1
            else:
                self.maxLines = None

        return property(**locals())

    def GetProperty(self, propertyName):
        return getattr(self, '_' + propertyName)

    def SetLayoutTriggerProperty(self, propertyName, value):
        if getattr(self, '_' + propertyName) != value:
            setattr(self, '_' + propertyName, value)
            self._layoutDirty = True
            if self.autoUpdate and not self.busy:
                self.Layout(propertyName)

    fontStyle = property(lambda self: self.GetProperty('fontStyle'), lambda self, value: self.SetLayoutTriggerProperty('fontStyle', value))
    fontFamily = property(lambda self: self.GetProperty('fontFamily'), lambda self, value: self.SetLayoutTriggerProperty('fontFamily', value))
    fontPath = property(lambda self: self.GetProperty('fontPath'), lambda self, value: self.SetLayoutTriggerProperty('fontPath', value))
    fontsize = property(lambda self: self.GetProperty('fontsize'), lambda self, value: self.SetLayoutTriggerProperty('fontsize', value))
    letterspace = property(lambda self: self.GetProperty('letterspace'), lambda self, value: self.SetLayoutTriggerProperty('letterspace', value))
    wrapMode = property(lambda self: self.GetProperty('wrapMode'), lambda self, value: self.SetLayoutTriggerProperty('wrapMode', value))
    uppercase = property(lambda self: self.GetProperty('uppercase'), lambda self, value: self.SetLayoutTriggerProperty('uppercase', value))
    lineSpacing = property(lambda self: self.GetProperty('lineSpacing'), lambda self, value: self.SetLayoutTriggerProperty('lineSpacing', value))
    underline = property(lambda self: self.GetProperty('underline'), lambda self, value: self.SetLayoutTriggerProperty('underline', value))
    bold = property(lambda self: self.GetProperty('bold'), lambda self, value: self.SetLayoutTriggerProperty('bold', value))
    italic = property(lambda self: self.GetProperty('italic'), lambda self, value: self.SetLayoutTriggerProperty('italic', value))
    maxLines = property(lambda self: self.GetProperty('maxLines'), lambda self, value: self.SetLayoutTriggerProperty('maxLines', value))
    tabs = property(lambda self: self.GetProperty('tabs'), lambda self, value: self.SetLayoutTriggerProperty('tabs', value))

    def SetTextColor(self, color):
        tricolor = trinity.TriColor()
        tricolor.SetRGB(*color)
        if len(color) != 4:
            tricolor.a = 1.0
        self.fontColor = tricolor.AsInt()
        if self.autoUpdate and not self.busy:
            self.Layout('SetTextColor')

    SetDefaultColor = SetTextColor

    def SetTabMargin(self, margin, refresh = 1):
        self._tabMargin = margin
        if refresh:
            self.Layout('SetTabMargin')

    def GetTab(self, idx, right = None):
        if len(self.tabs) > idx:
            return self.tabs[idx]
        if right is not None:
            return right

    def Update(self):
        if self._parseDirty or self._layoutDirty:
            self.Layout()

    def Layout(self, hint = 'None', absSize = None):
        if getattr(self, 'busy', 0):
            return
        self.busy = True
        layoutCountStat.Inc()
        self._layoutDirty = False
        if self.measurer:
            self.measurer.Reset()
        self.actualTextWidth = 0
        self.actualTextHeight = 0
        text = self.text
        if text is None or isinstance(text, basestring) and not text:
            self.busy = False
            return
        self._urlIDCounter = 0
        if self._parseDirty:
            textToParse = GetAsUnicode(text)
            if self.maxLines == 1:
                textToParse = SINGLE_LINE_NEWLINE_PATTERN.sub(' ', textToParse)
            parsePrepared = trinity.ParseLabelText(textToParse)
            self._parsePrepared = parsePrepared
            self._parseDirty = False
        else:
            parsePrepared = self._parsePrepared
        if not self.isAffectedByPushAlignment:
            if self._setWidth:
                width = self._setWidth
            else:
                width = self.GetMaxWidth()
        elif absSize:
            width, height = absSize
        else:
            width, height = self.GetAbsoluteSize()
        self._minCursor = None
        self.ResetTagStack()
        self._lastAddTextData = []
        self._inlineObjects = None
        self._inlineObjectsBuff = None
        vScrollshiftX = getattr(self, 'xShift', 0)
        margin = self._tabMargin
        self._numLines = 0
        self._commitCursorYScaled = 0
        self._textAlign = TEXT_ALIGN_LEFT
        self._canPushText = True
        maxLines = self.maxLines
        for lineData in parsePrepared:
            left = 0
            isTabbed = len(lineData) > 1
            lineStartCursorYScaled = self._commitCursorYScaled
            lineMaxCommitCursorYScaled = lineStartCursorYScaled
            for tabIndex, tabData in enumerate(lineData):
                self._commitCursorYScaled = lineStartCursorYScaled
                if self.measurer:
                    self.measurer.font = ''
                else:
                    return
                if isTabbed:
                    self._textAlign = TEXT_ALIGN_LEFT
                    self._canPushText = True
                    if width is None:
                        width = uicore.desktop.width
                    right = self.GetTab(tabIndex, width) - margin
                    elementWidth = right + vScrollshiftX - left
                else:
                    elementWidth = width
                self.ProcessLineData(tabData, left, elementWidth)
                if self._lastAddTextData:
                    self.CommitBuffer(doLineBreak=True)
                    if maxLines and self._numLines >= maxLines:
                        self._canPushText = False
                if isTabbed:
                    left = right + margin * 2 + vScrollshiftX
                lineMaxCommitCursorYScaled = max(lineMaxCommitCursorYScaled, self._commitCursorYScaled)

            self._commitCursorYScaled = lineStartCursorYScaled + (lineMaxCommitCursorYScaled - lineStartCursorYScaled)

        if not self._measuringText:
            self.ResolveAutoSizing()
            self._UpdateAlphaFade()
        self.busy = False

    def ResetTagStack(self):
        self._tagStack = {'font': [],
         'fontsize': [self.fontsize],
         'color': [self.fontColor],
         'letterspace': [self.letterspace],
         'hint': [],
         'link': [],
         'localized': [],
         'localizedQA': [],
         'u': self.underline,
         'b': self.bold,
         'i': self.italic,
         'uppercase': self.uppercase}

    def GetMaxWidth(self, *args):
        try:
            return trinity.adapters.GetMaxTextureSize(trinity.device.adapter)
        except:
            return 0

    def PushText(self, text, measurer, oneLiner, wrapModeForceAll, maxLines):
        if not measurer:
            return STOPWRAP
        textAdded = measurer.AddText(text)
        if textAdded >= len(text):
            self._lastAddTextData.append((text, self._measurerProperties))
            return
        if oneLiner:
            if self.showEllipsis:
                sliceBack = 0
                while textAdded > sliceBack:
                    tryFit = text[:textAdded - sliceBack] + ELLIPSIS
                    measurer.CancelLastText()
                    ellipsisFit = measurer.AddText(tryFit)
                    if ellipsisFit == len(tryFit):
                        break
                    sliceBack += 1

            self.CommitBuffer()
            return STOPWRAP
        measurer.CancelLastText()
        hasData = bool(self._lastAddTextData)
        if not hasData:
            if textAdded == 0:
                return STOPWRAP
        if not wrapModeForceAll:
            wrapPointInText = self.FindWrapPointInText(text, textAdded)
            if wrapPointInText is not None:
                textAdded = wrapPointInText
            elif hasData:
                lastText, lastMeasurerProperties = self._lastAddTextData[-1]
                wpl = eveLocalization.WrapPointList(lastText + text, session.languageID)
                combinedResult = wpl.GetLinebreakPoints()
                if len(lastText) in combinedResult:
                    self.CommitBuffer(doLineBreak=True)
                    if maxLines and self._numLines >= maxLines:
                        return STOPWRAP
                    return self.PushText(text, measurer, oneLiner, wrapModeForceAll, maxLines)
                lineText = u''.join([ addedData[0] for addedData in self._lastAddTextData ])
                wpl = eveLocalization.WrapPointList(lineText, session.languageID)
                lineWrapPoints = wpl.GetLinebreakPoints()
                if lineWrapPoints:
                    linePos = len(lineText)
                    moveToNextLine = []
                    breakAt = lineWrapPoints[-1]
                    while self._lastAddTextData:
                        addedData = self._lastAddTextData.pop()
                        addedText, addedMeasurerProperties = addedData
                        addedTextLength = len(addedText)
                        addedTextPos = linePos - addedTextLength
                        measurer.CancelLastText()
                        if addedTextPos <= breakAt <= linePos:
                            self.SetMeasurerProperties(*addedMeasurerProperties)
                            measurer.AddText(addedText[:breakAt - addedTextPos])
                            self._lastAddTextData.append((addedText[:breakAt - addedTextPos], addedMeasurerProperties))
                            rest = addedText[breakAt - addedTextPos:]
                            if rest:
                                moveToNextLine.insert(0, (rest, addedMeasurerProperties))
                            break
                        else:
                            moveToNextLine.insert(0, addedData)
                        linePos -= addedTextLength

                    self.CommitBuffer(doLineBreak=True)
                    if maxLines and self._numLines >= maxLines:
                        return STOPWRAP
                    for nextLineData in moveToNextLine:
                        addedText, addedMeasurerProperties = nextLineData
                        self.SetMeasurerProperties(*addedMeasurerProperties)
                        measurer.AddText(addedText)
                        self._lastAddTextData.append(nextLineData)

                    self.SetMeasurerProperties(*self._measurerProperties)
                    return self.PushText(text, measurer, oneLiner, wrapModeForceAll, maxLines)
        textSlice = text[:textAdded]
        measurer.AddText(textSlice)
        self._lastAddTextData.append((textSlice, self._measurerProperties))
        self.CommitBuffer(doLineBreak=True)
        if maxLines and self._numLines >= maxLines:
            return STOPWRAP
        moveToNext = text[textAdded:]
        return self.PushText(moveToNext, measurer, oneLiner, wrapModeForceAll, maxLines)

    def SetMeasurerProperties(self, fontsize, color, letterspace, underline, fontPath, register = False):
        measurer = self.measurer
        if not measurer:
            return
        measurer.fontSize = int(uicore.fontSizeFactor * fontsize)
        try:
            measurer.color = color
        except TypeError as err:
            log.LogError('Invalid color passed to text renderer, error: %s, color: %s' % (err, color))
            measurer.color = COLOR_WHITE_FULLALPHA

        measurer.letterSpace = letterspace
        measurer.underline = underline
        if fontPath is not None:
            measurer.font = str(fontPath)
        else:
            measurer.font = ''
        if register:
            self._measurerProperties = (fontsize,
             color,
             letterspace,
             underline,
             fontPath)

    def ProcessLineData(self, lineData, left, width):
        if width is not None:
            self._wrapWidthScaled = ScaleDpi(width)
        else:
            self._wrapWidthScaled = None
        self._commitCursorXScaled = ScaleDpi(left)
        measurer = self.measurer
        if not measurer:
            return False
        measurer.limit = self._wrapWidthScaled or 0
        measurer.cursorX = 0
        setHeight = self._setHeight
        maxLines = self.maxLines
        oneLiner = maxLines == 1
        wrapMode = self.wrapMode
        wrapModeForceAll = wrapMode == uiconst.WRAPMODE_FORCEALL
        tagStackDirty = True
        tagStack = self._tagStack
        thereWasText = False
        for element in lineData:
            type = element[0]
            if type == 0:
                text = element[1]
                if text:
                    thereWasText = True
                    if getattr(self, 'collectWordsInStack', False):
                        textList = re.split('([\\W]+)', text)
                        for eachWord in textList:
                            if eachWord != ' ':
                                tagStackDirty = self.ParseWordTag(eachWord) or tagStackDirty
                            tagStackDirty = self.DoTextPushing(tagStackDirty, measurer, tagStack, eachWord, oneLiner, wrapModeForceAll, maxLines)
                            if eachWord != ' ':
                                tagStackDirty = self.ParseWordClose() or tagStackDirty

                    else:
                        tagStackDirty = self.DoTextPushing(tagStackDirty, measurer, tagStack, text, oneLiner, wrapModeForceAll, maxLines)
                    linkStack = tagStack.get('link', None)
                    if linkStack:
                        linkStack[-1].textBuff.append(text)
            elif type == 1:
                tagStackDirty = self.tagIDToFunctionMapping[element[1]][0](self, element[2]) or tagStackDirty
            elif type == 2:
                tagStackDirty = self.tagIDToFunctionMapping[element[1]][1](self) or tagStackDirty
            elif type == 3:
                if element[1] != 'loc':
                    log.LogWarn('Unknown tag:', element[1])
            else:
                log.LogError('Unknown element type ID in ProcessLineData', type)

        if not thereWasText:
            if tagStackDirty:
                self.UpdateMeasurerProperties(measurer, tagStack, u' ')
                tagStackDirty = False
            ret = self.PushText(u' ', measurer, oneLiner, wrapModeForceAll, maxLines)
        return tagStackDirty

    def DoTextPushing(self, tagStackDirty, measurer, tagStack, myText, oneLiner, wrapModeForceAll, maxLines):
        if tagStackDirty:
            self.UpdateMeasurerProperties(measurer, tagStack, myText)
            tagStackDirty = False
        if self._canPushText:
            if tagStack['uppercase']:
                myText = UpperCase(myText)
            ret = self.PushText(myText, measurer, oneLiner, wrapModeForceAll, maxLines)
            if ret == STOPWRAP:
                self._canPushText = False
        return tagStackDirty

    def FindWrapPointInText(self, text, fromIndex):
        space = u' '
        if text[fromIndex] != space and text[fromIndex - 1] == space:
            return fromIndex
        totalLength = len(text)
        if text[fromIndex] == space:
            spaceIndex = fromIndex
            while spaceIndex < totalLength:
                if text[spaceIndex] != space:
                    break
                spaceIndex += 1

            return spaceIndex
        wpl = eveLocalization.WrapPointList(unicode(text), session.languageID)
        result = wpl.GetLinebreakPoints()
        if result:
            retIndex = [ each for each in result if each <= fromIndex ]
            if retIndex:
                return retIndex[-1]

    def UpdateMeasurerProperties(self, measurer, tagStack, words):
        fontsize = ScaleDpi(tagStack['fontsize'][-1])
        color = tagStack['color'][-1]
        letterspace = tagStack['letterspace'][-1]
        underline = bool(tagStack['u'])
        italic = bool(tagStack['i'])
        bold = bool(tagStack['b'])
        fontPath = self.fontPath
        fontFamily = self.fontFamily
        if fontPath is None:
            if self.autoDetectCharset:
                windowsLanguageID = uicore.font.GetWindowsLanguageIDForText(words)
                if windowsLanguageID:
                    fontFamily = uicore.font.GetFontFamilyBasedOnWindowsLanguageID(windowsLanguageID)
            fontPath = uicore.font.GetFontPathFromFontFamily(fontFamily, self.fontStyle, bold, italic)
        if self.localizationWrapOn and localization.settings.qaSettings.GetValue('showHardcodedStrings'):
            if not tagStack['localizedQA']:
                color = localization.uiutil.COLOR_HARDCODED
        self.SetMeasurerProperties(fontsize, color, letterspace, underline, fontPath, register=True)

    def GetIndexUnderPos(self, layoutPosition):
        index = self.measurer.GetIndexAtPos(ScaleDpi(layoutPosition))
        width = ReverseScaleDpi(self.measurer.GetWidthAtIndex(index))
        return (index, width)

    def GetWidthToIndex(self, index):
        """
        Returns the tuple (index,width), where the width of the text is measured
        up to and including the given index.
        An index of -1 is interpreted as the whole text, and the returned index
        in that case is the length of the string - otherwise the returned index
        is the same as the given index.
        """
        if self.destroyed:
            return
        if index == -1:
            maxLength = len(StripTags(self.text))
            index = maxLength
        width = ReverseScaleDpi(self.measurer.GetWidthAtIndex(index))
        return (index, width)

    def CommitBuffer(self, doLineBreak = False):
        measurer = self.measurer
        if not measurer:
            return
        buffWidth = measurer.cursorX
        cursorX = self._commitCursorXScaled
        textAlign = self._textAlign
        if textAlign != TEXT_ALIGN_LEFT:
            lastAddTextData = self._lastAddTextData
            while lastAddTextData:
                lastAddData = lastAddTextData.pop()
                lastText, lastMeasurerProperties = lastAddData
                if not lastText:
                    measurer.CancelLastText()
                    continue
                lastTextStriped = lastText.rstrip()
                if lastText != lastTextStriped:
                    measurer.CancelLastText()
                    self.SetMeasurerProperties(*lastMeasurerProperties)
                    measurer.AddText(lastTextStriped)
                    buffWidth = measurer.cursorX
                break

            if textAlign == TEXT_ALIGN_RIGHT:
                if self._wrapWidthScaled is None:
                    self._wrapWidthScaled = ScaleDpi(self.absoluteWidth)
                cursorX += self._wrapWidthScaled - buffWidth
            elif textAlign == TEXT_ALIGN_CENTER:
                if self._wrapWidthScaled is None:
                    self._wrapWidthScaled = ScaleDpi(self.absoluteWidth)
                cursorX += int((self._wrapWidthScaled - buffWidth) / 2)
        lineHeight = measurer.ascender - measurer.descender
        lineSpacing = int(self.lineSpacing * lineHeight)
        moveToNextLine = []
        if self._inlineObjectsBuff:
            for object in self._inlineObjectsBuff:
                registerObject = object.Copy()
                if object.inlineXEnd is None:
                    object.inlineX = 0
                    moveToNextLine.append(object)
                    registerObject.inlineXEnd = ReverseScaleDpi(measurer.cursorX)
                registerObject.inlineX += ReverseScaleDpi(cursorX)
                registerObject.inlineXEnd += ReverseScaleDpi(cursorX)
                registerObject.inlineY = ReverseScaleDpi(self._commitCursorYScaled)
                registerObject.inlineHeight = ReverseScaleDpi(lineHeight + lineSpacing)
                if self._inlineObjects is None:
                    self._inlineObjects = []
                self._inlineObjects.append(registerObject)

        measurer.CommitText(cursorX, self._commitCursorYScaled + measurer.ascender)
        if self._minCursor is None:
            self._minCursor = cursorX
        else:
            self._minCursor = min(self._minCursor, cursorX)
        self.actualTextWidth = max(self.actualTextWidth, cursorX + buffWidth)
        self.actualTextHeight = max(self.actualTextHeight, self._commitCursorYScaled + lineHeight)
        self._inlineObjectsBuff = moveToNextLine
        self._lastAddTextData = []
        if doLineBreak:
            self._commitCursorYScaled += lineSpacing + lineHeight
            measurer.cursorX = ScaleDpi(self.specialIndent)
            self._numLines += 1

    def ParseFontOpen(self, attribs):
        try:
            self.ParseColorTag(attribs[u'color'])
        except KeyError:
            pass

        try:
            self.ParseFontsizeTag(attribs[u'size'])
        except KeyError:
            pass

        self._tagStack['font'].append(attribs)
        return True

    def ParseFontClose(self):
        tagStack = self._tagStack['font']
        if tagStack:
            attribs = tagStack.pop()
            if u'color' in attribs:
                self.ParseColorClose()
            if u'size' in attribs:
                self.ParseFontsizeClose()
        return True

    def ParseUOpen(self, attribs):
        self._tagStack['u'] += 1
        return self._tagStack['u'] == 1

    def ParseIOpen(self, attribs):
        self._tagStack['i'] += 1
        return self._tagStack['i'] == 1

    def ParseBOpen(self, attribs):
        self._tagStack['b'] += 1
        return self._tagStack['b'] == 1

    def ParseUppercaseOpen(self, attribs):
        self._tagStack['uppercase'] += 1
        return self._tagStack['uppercase'] == 1

    def ParseUClose(self):
        retval = self._tagStack['u'] == 1
        self._tagStack['u'] = max(self._tagStack['u'] - 1, 0)
        return retval

    def ParseIClose(self):
        retval = self._tagStack['i'] == 1
        self._tagStack['i'] = max(self._tagStack['i'] - 1, 0)
        return retval

    def ParseBClose(self):
        retval = self._tagStack['b'] == 1
        self._tagStack['b'] = max(self._tagStack['b'] - 1, 0)
        return retval

    def ParseUppercaseClose(self):
        retval = self._tagStack['uppercase'] == 1
        self._tagStack['uppercase'] = max(self._tagStack['uppercase'] - 1, 0)
        return retval

    def ParseAOpen(self, attribs):
        try:
            url = attribs[u'href'].replace('&amp;', '&')
        except KeyError:
            log.LogError('Anchor tag missing href attribute, I have no idea what to do with this.  Attribs:', attribs)
            return False

        alt = attribs.get('alt', None)
        linkText = 'a href=' + attribs[u'href'] + (" alt='" + alt + "'" if alt is not None else '')
        currentTagStackSyntax = self.GetCurrentTagStackFormatSyntax()
        inlineObject = self.StartInline('link', linkText)
        inlineObject.url = url
        inlineObject.urlID = self._urlIDCounter
        inlineObject.alt = alt
        inlineObject.tagStackState = self._tagStack.copy()
        inlineObject.textBuff = [currentTagStackSyntax + '<' + linkText + '>']
        self._tagStack['link'].append(inlineObject)
        linkState = uiconst.LINK_IDLE
        if self._mouseOverUrl and url == self._mouseOverUrl and inlineObject.urlID == self._mouseOverUrlID:
            if uicore.uilib.leftbtn:
                linkState = uiconst.LINK_ACTIVE
            else:
                linkState = uiconst.LINK_HOVER
        linkFmt = self.GetLinkHandler().GetLinkFormat(url, linkState, self.linkStyle)
        linkColor = None
        if linkState == uiconst.LINK_IDLE:
            try:
                colorSyntax = attribs[u'color'].replace('#', '0x')
                hexColor = StringColorToHex(colorSyntax) or colorSyntax
                if hexColor:
                    linkColor = mathUtil.LtoI(long(hexColor, 0))
            except KeyError:
                pass

        inlineObject.bold = linkFmt.bold
        inlineObject.italic = linkFmt.italic
        inlineObject.underline = linkFmt.underline
        if linkFmt.bold:
            self.ParseBOpen({})
        if linkFmt.italic:
            self.ParseIOpen({})
        if linkFmt.underline:
            self.ParseUOpen({})
        self._tagStack['color'].append(linkColor or linkFmt.color or self.fontColor)
        self._urlIDCounter += 1
        return True

    def ParseLinkClose(self):
        self.EndInline('link')
        if self._tagStack['link']:
            closingLink = self._tagStack['link'].pop()
            if closingLink.bold:
                self.ParseBClose()
            if closingLink.italic:
                self.ParseIClose()
            if closingLink.underline:
                self.ParseUClose()
            self.ParseColorClose()
        return True

    def ParseLocalizedOpen(self, attribs):
        if self.localizationWrapOn:
            self._tagStack['localizedQA'].append(True)
            return True
        try:
            newText = attribs['hint']
            if len(self._tagStack.get('link', [])) < 1:
                self.renderObject.hasAuxiliaryTooltip = True
                inlineObject = self.StartInline('localized', newText)
                self._tagStack['localized'].append(inlineObject)
            else:
                for eachLink in self._tagStack.get('link', []):
                    eachLink['extraAlt'] = newText

        except KeyError:
            log.LogError('Localization tag without tooltip!')

        return True

    def ParseLocalizedClose(self):
        try:
            if self.localizationWrapOn:
                self._tagStack['localizedQA'].pop()
                return True
            self.EndInline('localized')
            if len(self._tagStack['localized']) > 0:
                self._tagStack['localized'].pop()
            return True
        except (KeyError, IndexError):
            pass

        return True

    def ParseLeftOpen(self, attribs):
        self._textAlign = TEXT_ALIGN_LEFT
        return True

    def ParseRightOpen(self, attribs):
        self._textAlign = TEXT_ALIGN_RIGHT
        return True

    def ParseCenterOpen(self, attribs):
        self._textAlign = TEXT_ALIGN_CENTER
        return True

    def ParseColorTag(self, value):
        color = StringColorToHex(value)
        if color is None:
            color = value.replace('#', '0x')
        try:
            col = mathUtil.LtoI(long(color, 0))
            self._tagStack['color'].append(col)
        except ValueError:
            log.LogWarn('Label got color value it cannot handle', value, self.text)
            return False

        return True

    def ParseColorClose(self):
        try:
            if len(self._tagStack['color']) > 1:
                self._tagStack['color'].pop()
            else:
                log.LogWarn('Label got ParseColorClose but doesnt have color to close', self.text)
                return False
            return True
        except (KeyError, IndexError):
            pass

        return False

    def ParseFontsizeTag(self, value):
        fs = int(value)
        if 'fontsize' not in self._tagStack:
            self._tagStack['fontsize'] = []
        self._tagStack['fontsize'].append(fs)
        return True

    def ParseFontsizeClose(self):
        try:
            if len(self._tagStack['fontsize']) > 1:
                self._tagStack['fontsize'].pop()
            else:
                log.LogWarn('Label got FontsizeClose but doesnt have fontsize to close', self.text)
                return False
            return True
        except (KeyError, IndexError):
            pass

        return False

    def ParseLetterspaceTag(self, value):
        ls = int(value)
        if 'letterspace' not in self._tagStack:
            self._tagStack['letterspace'] = []
        self._tagStack['letterspace'].append(fs)
        return True

    def ParseLetterspaceClose(self):
        try:
            if len(self._tagStack['letterspace']) > 1:
                self._tagStack['letterspace'].pop()
            else:
                log.LogWarn('Label got ParseLetterspaceClose but doesnt have letterspace to close', self.text)
                return False
            return True
        except (KeyError, IndexError):
            pass

        return False

    def ParseHintTag(self, value):
        inlineObject = self.StartInline('hint', value)
        self._tagStack['hint'].append(inlineObject)
        return True

    def ParseHintClose(self):
        self.EndInline('hint')
        try:
            self._tagStack['hint'].pop()
            return True
        except (KeyError, IndexError):
            pass

        return False

    def ParseWordTag(self, value):
        inlineObject = self.StartInline('words', value)
        if 'words' not in self._tagStack:
            self._tagStack['words'] = []
        self._tagStack['words'].append(inlineObject)
        return True

    def ParseWordClose(self):
        self.EndInline('words')
        try:
            self._tagStack['words'].pop()
            return True
        except (KeyError, IndexError):
            pass

        return False

    def ParseEmptyOpen(self, attribs):
        if attribs is None:
            log.LogWarn('Got None attribs into ParseEmptyOpen', self.text)
            return False
        if u'url' in attribs:
            attribs[u'href'] = attribs[u'url']
            del attribs[u'url']
        if u'href' in attribs:
            return self.ParseAOpen(attribs)
        stackDirty = False
        for attrib, value in attribs.iteritems():
            try:
                stackDirty = self.emptyTagHandlers[attrib](self, value) or stackDirty
            except KeyError:
                log.LogWarn('Empty tag attribute', attrib, 'not recognized')

        return stackDirty

    def ParseUnusedClose(self, tag):
        log.LogWarn('Unused close tag:', tag)

    def ParseUnusedOpen(self, tag):
        log.LogWarn('Unused open tag:', tag)

    tagIDToFunctionMapping = {1: (ParseFontOpen, ParseFontClose),
     2: (ParseUOpen, ParseUClose),
     3: (ParseUppercaseOpen, ParseUppercaseClose),
     4: (ParseIOpen, ParseIClose),
     5: (ParseBOpen, ParseBClose),
     6: (ParseAOpen, ParseLinkClose),
     7: (ParseLocalizedOpen, ParseLocalizedClose),
     100: (ParseLeftOpen, lambda self: self.ParseUnusedClose('left')),
     101: (ParseRightOpen, lambda self: self.ParseUnusedClose('right')),
     102: (ParseCenterOpen, lambda self: self.ParseUnusedClose('center')),
     200: (lambda self, attribs: self.ParseUnusedOpen('color'), ParseColorClose),
     201: (lambda self, attribs: self.ParseUnusedOpen('fontsize'), ParseFontsizeClose),
     202: (lambda self, attribs: self.ParseUnusedOpen('letterspace'), ParseLetterspaceClose),
     203: (lambda self, attribs: self.ParseUnusedOpen('hint'), ParseHintClose),
     204: (lambda self, attribs: self.ParseUnusedOpen('url'), ParseLinkClose),
     -48879: (ParseEmptyOpen, lambda self: self.ParseUnusedClose('empty?!?'))}
    emptyTagHandlers = {u'color': ParseColorTag,
     u'fontsize': ParseFontsizeTag,
     u'letterspace': ParseLetterspaceTag,
     u'hint': ParseHintTag}

    @classmethod
    def ExtractLocalizedTags(cls, text):
        ret = []
        tagID = 7
        parsePrepared = trinity.ParseLabelText(text)
        for lineData in parsePrepared:
            for tabData in lineData:
                for element in tabData:
                    type = element[0]
                    if type == 1 and element[1] == tagID:
                        ret.append(element[2])

        return ret

    def GetCurrentTagStackFormatSyntax(self, ignoreTags = ('link', 'localized', 'letterspace')):
        formatSyntax = ''
        for tag, stack in self._tagStack.iteritems():
            if tag in ignoreTags:
                continue
            if type(stack) == types.ListType:
                if stack:
                    value = stack[-1]
                    if tag == 'color':
                        value = self.IntColorToSyntax(value)
                    formatSyntax += '<%s=%s>' % (tag, value)
            elif stack:
                formatSyntax += '<%s>' % tag

        return formatSyntax

    def IntColorToSyntax(self, intColor):
        c = trinity.TriColor()
        c.FromInt(intColor)
        color = (c.r,
         c.g,
         c.b,
         c.a)
        return '#%02x%02x%02x%02x' % (color[3] * 255,
         color[0] * 255,
         color[1] * 255,
         color[2] * 255)

    def GetTooltipPosition(self):
        if self.tooltipPosition:
            return self.tooltipPosition
        l, t = self.GetAbsolutePosition()
        w, h = self.textwidth, self.textheight
        if self._alphaFadeLeft:
            fadeStart, length = self._alphaFadeLeft
            l += fadeStart
            w -= fadeStart
        if self._alphaFadeRight:
            fadeEnd, length = self._alphaFadeRight
            w = min(w, fadeEnd)
        return (l,
         t,
         w,
         h)

    def GetMouseOverUrl(self):
        return self._mouseOverUrl

    def StartInline(self, inlineType, data):
        inlineObject = Bunch()
        inlineObject.inlineType = inlineType
        inlineObject.data = data
        measurer = self.measurer
        inlineObject.inlineX = ReverseScaleDpi(measurer.cursorX)
        inlineObject.inlineXEnd = None
        if self._inlineObjectsBuff is None:
            self._inlineObjectsBuff = []
        self._inlineObjectsBuff.append(inlineObject)
        return inlineObject

    def EndInline(self, inlineType):
        if inlineType in self._tagStack and self._tagStack[inlineType]:
            inlineObject = self._tagStack[inlineType][-1]
            if inlineObject:
                measurer = self.measurer
                inlineObject.inlineXEnd = ReverseScaleDpi(measurer.cursorX)

    def GetLinkHandlerClass(self):
        return BaseLink

    def GetLinkHandler(self):
        handlerClass = self.GetLinkHandlerClass()
        return handlerClass()

    def GetMenu(self):
        m = []
        if self._mouseOverUrl:
            m = self.GetLinkHandler().GetLinkMenu(self, self._mouseOverUrl)
        m += [(MenuLabel('/Carbon/UI/Controls/Common/Copy'), self.CopyText)]
        if localization.UseImportantTooltip():
            if self.hint:
                m += [(localization.GetByLabel('UI/Common/CopyTooltip'), self.CopyHint, (self.hint,))]
        return m

    def GetAuxiliaryMenuOptions(self):
        m = [(MenuLabel('/Carbon/UI/Controls/Common/Copy'), self.CopyText)]
        if localization.UseImportantTooltip():
            locTooltip = self.GetAuxiliaryTooltip()
            if locTooltip:
                m += [(localization.GetByLabel('UI/Common/CopyTooltip'), self.CopyHint, (locTooltip,))]
        return m

    def GetAuxiliaryTooltip(self):
        """
            Used when generating the auxiliary hint for localization tooltips (in which case, the label is disabled,
            so CheckInlines is never called)
        """
        inlineHintObj = None
        if self._inlineObjects:
            mouseX = uicore.uilib.x
            mouseY = uicore.uilib.y
            left, top, width, height = self.GetAbsolute()
            for inline in self._inlineObjects:
                startX = inline.inlineX
                endX = inline.inlineXEnd
                startY = inline.inlineY
                endY = startY + inline.inlineHeight
                if left + startX < mouseX < left + endX and top + startY < mouseY < top + endY:
                    if inline.inlineType == 'localized':
                        self.auxTooltipPosition = (left + startX,
                         top + startY,
                         endX - startX,
                         inline.inlineHeight)
                        return inline.data

        self.auxTooltipPosition = None

    def GetAuxiliaryTooltipPosition(self):
        return self.auxTooltipPosition

    def CopyText(self):
        text = StripTags(self.text, stripOnly=['localized'])
        blue.pyos.SetClipboardData(text)

    def CopyHint(self, hint):
        if isinstance(hint, basestring):
            blue.pyos.SetClipboardData(hint)

    def OnMouseEnter(self, *args):
        self.CheckInlines()

    def OnMouseExit(self, *args):
        self.CheckInlines()

    def OnMouseHover(self, *args):
        self.CheckInlines()

    def CheckInlines(self):
        inlineLinkObj = None
        inlineHintObj = None
        inlineLocalizationHintObj = None
        if self._inlineObjects and uicore.uilib.mouseOver is self:
            mouseX = uicore.uilib.x
            mouseY = uicore.uilib.y
            left, top, width, height = self.GetAbsolute()
            for inline in self._inlineObjects:
                startX = inline.inlineX
                endX = inline.inlineXEnd
                startY = inline.inlineY
                endY = startY + inline.inlineHeight
                if left + startX < mouseX < left + endX and top + startY < mouseY < top + endY:
                    if inline.inlineType == 'link':
                        inlineLinkObj = inline
                    elif inline.inlineType == 'hint':
                        inlineHintObj = inline
                    elif inline.inlineType == 'localized' and isinstance(inline.data, basestring):
                        inlineLocalizationHintObj = inline
                    elif inline.inlineType == 'words':
                        self.MouseOverWordCallback(word=inline.data)

        self._resolvingInlineHint = True
        mouseOverUrl = None
        mouseOverUrlID = None
        mouseOverTextBuff = None
        inlineHint = None
        if inlineLinkObj:
            mouseOverUrl = inlineLinkObj.url
            mouseOverUrlID = inlineLinkObj.urlID
            mouseOverTextBuff = inlineLinkObj.textBuff
            if inlineLinkObj.alt:
                inlineHint = inlineLinkObj.alt
            else:
                standardHint = self.GetLinkHandler().GetStandardLinkHint(mouseOverUrl)
                if standardHint:
                    inlineHint = standardHint
            if inlineLinkObj.extraAlt:
                if inlineHint:
                    inlineHint = inlineHint + '<br>' + inlineLinkObj.extraAlt
                else:
                    inlineHint = inlineLinkObj.extraAlt
            x, y = self.GetAbsolutePosition()
            self.tooltipPosition = (x + inlineLinkObj.inlineX,
             y + inlineLinkObj.inlineY,
             inlineLinkObj.inlineXEnd - inlineLinkObj.inlineX,
             inlineLinkObj.inlineHeight)
        elif inlineHintObj:
            x, y = self.GetAbsolutePosition()
            self.tooltipPosition = (x + inlineHintObj.inlineX,
             y + inlineHintObj.inlineY,
             inlineHintObj.inlineXEnd - inlineHintObj.inlineX,
             inlineHintObj.inlineHeight)
        else:
            self.tooltipPosition = None
        if not inlineHint and inlineHintObj:
            inlineHint = inlineHintObj.data
        if inlineLocalizationHintObj:
            if inlineHint:
                inlineHint += '<br>' + inlineLocalizationHintObj.data
            else:
                inlineHint = inlineLocalizationHintObj.data
        hint = inlineHint or getattr(self, '_objectHint', None)
        if hint != self.hint:
            self.hint = hint
        self._resolvingInlineHint = False
        if mouseOverUrl != self._mouseOverUrl:
            self._mouseOverUrl = mouseOverUrl
            self._mouseOverUrlID = mouseOverUrlID
            self._mouseOverTextBuff = mouseOverTextBuff
            self.Layout()
            if mouseOverUrl:
                self._hiliteResetTimer = AutoTimer(50, self._ResetInlineHilite)

    def _ResetInlineHilite(self):
        if uicore.uilib.mouseOver is self:
            return
        self._hiliteResetTimer = None
        self.CheckInlines()

    def GetStandardLinkHint(self, url):
        """ Overwrite function for clients to provide hint on links"""
        return None

    def OnClick(self, *args):
        if self._mouseOverUrl:
            self.GetLinkHandler().ClickLink(self, self._mouseOverUrl.replace('&amp;', '&'))

    def Encode(self, text):
        return text.replace(u'&gt;', u'>').replace(u'&lt;', u'<').replace(u'&amp;', u'&').replace(u'&AMP;', u'&').replace(u'&GT;', u'>').replace(u'&LT;', u'<')

    def Decode(self, text):
        return text.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')

    def OnMouseDown(self, *args):
        if self._mouseOverUrl:
            self.OnMouseDownWithUrl(self._mouseOverUrl, *args)
        if getattr(self, '_mouseOverTextBuff', None) and self._mouseOverUrl:
            self._dragLinkData = (''.join(self._mouseOverTextBuff), self._mouseOverUrl)
        else:
            self._dragLinkData = None
        VisibleBase.OnMouseDown(self, *args)

    def OnMouseDownWithUrl(self, url, *args):
        """to be overridden in eve"""
        pass

    def OnMouseMove(self, *args):
        if not self._hilite:
            self.CheckInlines()
        VisibleBase.OnMouseMove(self, *args)

    def GetDragData(self, *args):
        if getattr(self, '_dragLinkData', None):
            dragDisplayText, url = getattr(self, '_dragLinkData', None)
            entry = Bunch()
            entry.__guid__ = 'TextLink'
            entry.url = url
            entry.dragDisplayText = dragDisplayText
            entry.displayText = StripTags(dragDisplayText)
            return [entry]

    def MouseOverWordCallback(self, word, *args):
        if getattr(self, 'mouseOverWordCallback', None):
            self.mouseOverWordCallback(word)

    @classmethod
    def PrepareDrag(cls, *args):
        return cls.GetLinkHandlerClass(cls).PrepareDrag(*args)

    def UpdateAlignment(self, budgetLeft = 0, budgetTop = 0, budgetWidth = 0, budgetHeight = 0, updateChildrenOnly = False):
        preWidth = self.displayWidth
        preHeight = self.displayHeight
        retBudgetLeft, retBudgetTop, retBudgetWidth, retBudgetHeight, sizeChanged = VisibleBase.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight)
        if not self._resolvingAutoSizing and self.isAffectedByPushAlignment and sizeChanged:
            self.Layout('UpdateAlignment', absSize=(ReverseScaleDpi(self.displayWidth), ReverseScaleDpi(self.displayHeight)))
            if preWidth != self.displayWidth or preHeight != self.displayHeight:
                retBudgetLeft, retBudgetTop, retBudgetWidth, retBudgetHeight, _sizeChanged = VisibleBase.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight)
        if sizeChanged and getattr(self, 'OnSizeChanged', None):
            self.OnSizeChanged()
        return (retBudgetLeft,
         retBudgetTop,
         retBudgetWidth,
         retBudgetHeight,
         sizeChanged)

    def GetTagStringValue(self, tagtofind, tagstring):
        start = tagstring.find(tagtofind)
        if start != -1:
            tagBegin = tagstring[start + len(tagtofind):]
            for checkQuote in ['"', "'"]:
                if tagBegin.startswith(checkQuote):
                    end = tagBegin.find(checkQuote, 1)
                    if end != -1:
                        return tagBegin[1:end]

    def GetTagValue(self, tagtofind, tagstring):
        start = tagstring.find(tagtofind)
        if start != -1:
            end = tagstring.find(' ', start)
            if end == start:
                end = tagstring.find(' ', start + 1)
            if end == -1:
                end = tagstring.find('>', start)
            if end == -1:
                end = len(tagstring)
            return tagstring[start + len(tagtofind):end]

    @classmethod
    def MeasureTextSize(cls, text, **customAttributes):
        """ Util function to get the size of the label before its rendered"""
        customAttributes['text'] = text
        customAttributes['parent'] = None
        customAttributes['measuringText'] = True
        customAttributes['align'] = uiconst.TOPLEFT
        label = cls(**customAttributes)
        return (label.textwidth, label.textheight)

    @classmethod
    def ClearComparsionTest(cls):
        for each in uicore.layer.abovemain.children[:]:
            if each.name == 'test':
                each.Close()

    @classmethod
    def CreateComparsionTest(cls):
        from carbonui.control.label import LabelOverride as Label
        cls.ClearComparsionTest()
        testParent = Container(parent=uicore.layer.abovemain, name='test')
        Fill(parent=testParent, idx=0, color=(0, 0, 0, 1))

        def DrawTabs(label):
            if label.tabs:
                for tab in label.tabs:
                    Line(parent=testParent, name='test', idx=0, align=uiconst.TOPLEFT, left=label.left + tab, top=label.top, width=1, height=label.height)

                width = label.tabs[-1]
            else:
                width = label.textwidth
                Line(parent=testParent, name='test', idx=0, align=uiconst.TOPLEFT, left=label.left + label.textwidth + 1, top=label.top, width=1, height=label.height)
            Line(parent=testParent, name='test', idx=0, align=uiconst.TOPLEFT, left=label.left - 1, top=label.top, width=1, height=label.height)
            Line(parent=testParent, name='test', idx=0, align=uiconst.TOPLEFT, top=label.top - 1, width=width + 2, left=label.left - 1, height=1)
            Line(parent=testParent, name='test', idx=0, align=uiconst.TOPLEFT, top=label.top + label.height, width=width + 2, left=label.left - 1, height=1)

        tabText = '<color=0xFF00FF00><fontsize=24>32GreenStarts<color=0xFFFF0000>Red/32Starts<i>ItalicStart Tab 1</fontsize><t>Tab Red Ends here</color> 2<t>Tab 3 GreenEnds</color>Italic</i><t><right>Tab 4 Right with some text for wrapping    <t><center>Tab 5 Center with some text <color=0xFFFF0000>RedStarts and changes to <color=0xFF0000FF>BLUE</color></color>'
        tabTextWeirdSpacing = '<color=0xFFFF0000>  RedStarts  <i>  ItalicStart  Tab  1  <t>  Tab  Red  Ends  here  </color>  2<t>  Tab  3  Italic  </i><t><right>  Tab  4  Right  '
        tl1 = Label(parent=testParent, name='test', text='', idx=0, left=64, top=64, tabs=[150,
         300,
         450,
         600,
         750])
        tl1.text = tabText
        DrawTabs(tl1)
        tl2 = Label(parent=testParent, name='test', text=tabText, idx=0, left=64, top=tl1.top + tl1.textheight + 4, tabs=[100,
         200,
         300,
         400,
         500])
        DrawTabs(tl2)
        tl3 = Label(parent=testParent, name='test', text=tabText, idx=0, left=64, top=tl2.top + tl2.textheight + 4, tabs=[80,
         160,
         240,
         320,
         400], maxLines=1)
        DrawTabs(tl3)
        tl4 = Label(parent=testParent, name='test', text=tabText, idx=0, left=64, top=tl3.top + tl3.textheight + 4, tabs=[80,
         160,
         240,
         320,
         400], maxLines=1, showEllipsis=True)
        DrawTabs(tl4)
        tl5 = Label(parent=testParent, name='test', text=tabText, idx=0, left=64, top=tl4.top + tl4.textheight + 4, tabs=[100,
         200,
         300,
         400], maxLines=2)
        DrawTabs(tl5)
        tl6 = Label(parent=testParent, name='test', text=tabTextWeirdSpacing, idx=0, left=64, top=tl5.top + tl5.textheight + 4, tabs=[100,
         200,
         300,
         400], maxLines=1)
        DrawTabs(tl6)
        tl7 = Label(parent=testParent, name='test', text=tabText, idx=0, left=64, top=tl6.top + tl6.textheight + 4, tabs=[80,
         160,
         240,
         320,
         400], maxLines=1, height=14, showEllipsis=True)
        DrawTabs(tl7)
        multilineTabbed = 'tab1 with long text so it wrapps within the tabstop<t>tab2<t>tab3<br>l2Tab1 some text to wrap<t>l2Tab2<br>l3Tab1 some text to wrap<t>l3Tab2<t>l3Tab3 sometext<br>l4Tab1 some text to wrap<t>l4Tab2<t>l4Tab3 sometext<t>l4 lasttab'
        tl8 = Label(parent=testParent, name='test', text=multilineTabbed, idx=0, left=64, top=tl7.top + tl7.height + 4, tabs=[80,
         160,
         280,
         320,
         400], showEllipsis=True)
        DrawTabs(tl8)
        blockText = "Lorem ipsum dolor sit amet, <b>consectetur adipiscing elit. Nunc eros nisi, link with formatted alt info <url=http://apple.com alt='hallo<br><i>italic in new line'>sollicitudin sit amet <fontsize=14>malesuada sit amet, tristique vel tortor. Cras arcu sem, pellentesque </url>eu ultricies sit amet, ultricies in dolor. Quisque dignissim arcu ut elit rhoncus non feugiat diam molestie. Aenean porttitor commodo nulla ac pellentesque.  "
        b1 = Label(parent=testParent, name='test', text=blockText, idx=0, left=tl1.left + tl1.width + 20, top=64, width=200, state=uiconst.UI_NORMAL)
        DrawTabs(b1)


class LabelOverride(LabelCore):
    pass
