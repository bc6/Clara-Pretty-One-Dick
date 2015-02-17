#Embedded file name: eve/client/script/ui/control\eveLabel.py
from carbonui.control.label import LabelCore
from eve.client.script.ui import eveFontConst as fontConst
import log
import carbonui.const as uiconst
import trinity
from eve.client.script.ui.control.eveBaseLink import BaseLink

class Label(LabelCore):
    """ Standard text label """
    __guid__ = 'uicontrols.Label'
    default_name = 'Label'
    default_fontsize = fontConst.EVE_MEDIUM_FONTSIZE
    default_color = (1.0, 1.0, 1.0, 0.75)
    default_align = uiconst.TOPLEFT
    default_allowpartialtext = 1
    default_shadowOffset = (0, 1)
    autoFadeSides = False

    def ApplyAttributes(self, attributes):
        LabelCore.ApplyAttributes(self, attributes)
        if 'autoFadeSides' in attributes:
            self.autoFadeSides = attributes.autoFadeSides

    def DoFontChange(self, *args):
        self.OnCreate(trinity.device)

    def GetLinkHandlerClass(self):
        return BaseLink

    def UpdateAlignment(self, *args, **kwds):
        ret = LabelCore.UpdateAlignment(self, *args, **kwds)
        if self.autoFadeSides and self.parent:
            length = self.autoFadeSides
            if uicore.ReverseScaleDpi(self.displayX) < length:
                fadeStart = uicore.ReverseScaleDpi(-self.displayX)
                self.SetLeftAlphaFade(fadeStart, min(length, fadeStart))
                self.renderObject.hasAuxiliaryTooltip = True
            else:
                self.SetLeftAlphaFade()
            if self.displayX + self.displayWidth > self.parent.displayWidth:
                fadeEnd = self.parent.displayWidth - self.displayX
                self.SetRightAlphaFade(uicore.ReverseScaleDpi(fadeEnd), length)
                self.renderObject.hasAuxiliaryTooltip = True
            else:
                self.SetRightAlphaFade()
        return ret

    def GetAuxiliaryTooltip(self):
        baseAuxiliaryTooltip = LabelCore.GetAuxiliaryTooltip(self)
        if baseAuxiliaryTooltip:
            return baseAuxiliaryTooltip
        if self.autoFadeSides and self._alphaFadeRight or self._alphaFadeLeft:
            return self.text

    def GetHint(self):
        baseHint = self.hint
        if baseHint:
            return baseHint
        if self.autoFadeSides and self._alphaFadeRight or self._alphaFadeLeft:
            return self.text


class EveStyleLabel(Label):
    default_name = 'EveStyleLabel'

    def ApplyAttributes(self, attributes):
        fontsize = attributes.get('fontsize', None)
        if fontsize is not None:
            attributes.fontsize = self.default_fontsize
            log.LogTraceback('You are not allowed to change fontsize of a font style - find another style to use or use uicontrols.Label for custom labels')
        uppercase = attributes.get('uppercase', None)
        if uppercase is not None:
            attributes.uppercase = self.default_uppercase
            log.LogTraceback('You are not allowed to change uppercase of a font style - find another style to use or use uicontrols.Label for custom labels')
        letterspace = attributes.get('letterspace', None)
        if letterspace is not None:
            attributes.letterspace = self.default_letterspace
            log.LogTraceback('You are not allowed to change letterspace of a font style - find another style to use or use uicontrols.Label for custom labels')
        Label.ApplyAttributes(self, attributes)


class EveLabelSmall(EveStyleLabel):
    '\n    This is a small eve font, fontsize=%s\n    ' % fontConst.EVE_SMALL_FONTSIZE
    __guid__ = 'uicontrols.EveLabelSmall'
    default_name = 'EveLabelSmall'
    default_fontsize = fontConst.EVE_SMALL_FONTSIZE
    default_fontStyle = fontConst.STYLE_SMALLTEXT
    default_shadowOffset = (0, 1)


class EveHeaderSmall(EveStyleLabel):
    """
    This is a small eve font in uppercase
    """
    __guid__ = 'uicontrols.EveHeaderSmall'
    default_name = 'EveHeaderSmall'
    default_fontStyle = fontConst.STYLE_SMALLTEXT
    default_fontsize = fontConst.EVE_SMALL_FONTSIZE
    default_uppercase = 1
    default_shadowOffset = (0, 1)


class EveLabelSmallBold(EveStyleLabel):
    """
    This is a small eve font in bold
    """
    __guid__ = 'uicontrols.EveLabelSmallBold'
    default_name = 'EveLabelSmallBold'
    default_fontStyle = fontConst.STYLE_SMALLTEXT
    default_fontsize = fontConst.EVE_SMALL_FONTSIZE
    default_bold = True
    default_shadowOffset = (0, 1)


class EveLabelMedium(EveStyleLabel):
    '\n    This is a medium eve font, fontsize=%s\n    ' % fontConst.EVE_MEDIUM_FONTSIZE
    __guid__ = 'uicontrols.EveLabelMedium'
    default_name = 'EveLabelMedium'
    default_fontsize = fontConst.EVE_MEDIUM_FONTSIZE
    default_shadowOffset = (0, 1)


class EveHeaderMedium(EveStyleLabel):
    """
    This is a medium eve font in uppercase
    """
    __guid__ = 'uicontrols.EveHeaderMedium'
    default_name = 'EveHeaderMedium'
    default_fontsize = fontConst.EVE_MEDIUM_FONTSIZE
    default_uppercase = 1
    default_shadowOffset = (0, 1)


class EveLabelMediumBold(EveStyleLabel):
    '\n    This is a bold medium eve font, fontsize=%s\n    ' % fontConst.EVE_MEDIUM_FONTSIZE
    __guid__ = 'uicontrols.EveLabelMediumBold'
    default_name = 'EveLabelMediumBold'
    default_fontsize = fontConst.EVE_MEDIUM_FONTSIZE
    default_bold = True
    default_shadowOffset = (0, 1)


class EveLabelLarge(EveStyleLabel):
    '\n    This is a large eve font, fontsize=%s\n    ' % fontConst.EVE_LARGE_FONTSIZE
    __guid__ = 'uicontrols.EveLabelLarge'
    default_name = 'EveLabelLarge'
    default_fontsize = fontConst.EVE_LARGE_FONTSIZE
    default_shadowOffset = (0, 1)


class EveHeaderLarge(EveStyleLabel):
    """
    This is a large eve font in uppercase
    """
    __guid__ = 'uicontrols.EveHeaderLarge'
    default_name = 'EveHeaderLarge'
    default_fontsize = fontConst.EVE_LARGE_FONTSIZE
    default_uppercase = 1
    default_fontStyle = fontConst.STYLE_HEADER
    default_shadowOffset = (0, 1)


class EveLabelLargeBold(EveStyleLabel):
    '\n    This is a bold large eve font, fontsize=%s\n    ' % fontConst.EVE_LARGE_FONTSIZE
    __guid__ = 'uicontrols.EveLabelLargeBold'
    default_name = 'EveLabelLargeBold'
    default_fontsize = fontConst.EVE_LARGE_FONTSIZE
    default_bold = True
    default_shadowOffset = (0, 1)


class EveLabelLargeUpper(EveLabelLarge):
    """
    This is a large eve font in forced uppercase
    """
    __guid__ = 'uicontrols.EveLabelLargeUpper'
    default_name = 'EveLabelLargeUpper'
    default_shadowOffset = (0, 1)


class EveCaptionSmall(EveStyleLabel):
    """
    This is a medium eve caption in fontsize=18
    """
    __guid__ = 'uicontrols.EveCaptionSmall'
    default_name = 'EveCaptionSmall'
    default_fontsize = 18
    default_bold = True
    default_fontStyle = fontConst.STYLE_HEADER
    default_lineSpacing = -0.12
    default_shadowOffset = (0, 1)


class EveCaptionMedium(EveStyleLabel):
    """
    This is a medium eve caption in fontsize=20
    """
    __guid__ = 'uicontrols.EveCaptionMedium'
    default_name = 'EveCaptionMedium'
    default_fontsize = 20
    default_bold = True
    default_fontStyle = fontConst.STYLE_HEADER
    default_lineSpacing = -0.12
    default_shadowOffset = (0, 1)


class EveCaptionLarge(EveStyleLabel):
    """
    This is a medium eve caption in fontsize=24
    """
    __guid__ = 'uicontrols.EveCaptionLarge'
    default_name = 'EveCaptionLarge'
    default_fontsize = 24
    default_bold = True
    default_fontStyle = fontConst.STYLE_HEADER
    default_lineSpacing = -0.12
    default_shadowOffset = (0, 1)


class CaptionLabel(Label):
    """
    This is an editable eve caption in uppercase, fontsize=20 and bold
    It's used with various fontsize and letterspace in the Eve UI
    """
    __guid__ = 'uicontrols.CaptionLabel'
    default_name = 'caption'
    default_fontsize = 20
    default_letterspace = 1
    default_align = uiconst.TOALL
    default_idx = -1
    default_state = uiconst.UI_DISABLED
    default_uppercase = True
    default_bold = True
    default_shadowOffset = (0, 1)


class WndCaptionLabel(EveCaptionMedium):
    __guid__ = 'uicontrols.WndCaptionLabel'
    default_left = 70
    default_top = 8
    default_subcaption = None

    def ApplyAttributes(self, attributes):
        LabelCore.ApplyAttributes(self, attributes)
        subcaption = attributes.get('subcaption', self.default_subcaption)
        self.subcapt = EveLabelSmall(text='', parent=self.parent, align=uiconst.TOPLEFT, left=self.left + 1, top=self.top + self.textheight - 2, state=uiconst.UI_HIDDEN, name='subcaption')
        if subcaption:
            self.SetSubcaption(subcaption)

    def SetSubcaption(self, text):
        self.subcapt.text = text
        self.subcapt.state = uiconst.UI_DISABLED


from carbonui.control.label import LabelOverride
LabelOverride.__bases__ = (Label,)
