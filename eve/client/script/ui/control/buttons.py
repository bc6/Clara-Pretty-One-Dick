#Embedded file name: eve/client/script/ui/control\buttons.py
from carbonui.control.buttons import ButtonCore
from carbonui.util.color import Color
from eve.client.script.ui.control.eveFrame import Frame
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.eveLabel import EveLabelLargeUpper
from carbonui.primitives.container import Container
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import SpriteThemeColored, FrameThemeColored, FillThemeColored, LabelThemeColored
import localization
import uiutil
import base
import uthread
import carbonui.const as uiconst
import audioConst
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.fill import Fill
from eve.client.script.ui.control.eveWindowUnderlay import RaisedUnderlay
FRAME_COLOR = (0.15,
 0.15,
 0.15,
 1.0)
OPACITY_LABEL_IDLE = 1.0
OPACITY_LABEL_HOVER = 1.5
OPACITY_LABEL_MOUSEDOWN = 2.0

def GetIconColor(color):
    return Color(*color).SetBrightness(1.0).SetSaturation(0.3).GetRGBA()


class ToggleButtonGroup(Container):
    """ A button group with selection state. Can be used with or without panels. """
    __guid__ = 'uicls.ToggleButtonGroup'
    default_align = uiconst.RELATIVE
    default_idx = 0
    default_unisize = True
    default_height = 22

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.callback = attributes.Get('callback', None)
        self.selected = {}
        self.buttons = []
        self.isButtonSizeUpToDate = True

    def AddButton(self, btnID, label = '', panel = None, iconPath = None, iconSize = None, hint = None, isDisabled = False, colorSelected = None, btnClass = None, **kw):
        if btnClass is None:
            btnClass = ToggleButtonGroupButton
        btn = btnClass(name=('Button_%s' % btnID), parent=self, controller=self, btnID=btnID, panel=panel, label=label, iconPath=iconPath, iconSize=iconSize, hint=hint, isDisabled=isDisabled, colorSelected=colorSelected, **kw)
        self.buttons.append(btn)
        self.isButtonSizeUpToDate = False
        return btn

    def ClearButtons(self):
        for btn in self.buttons:
            btn.Close()

        self.buttons = []

    def UpdateAlignment(self, *args, **kwds):
        """ Update button size and alignment if needed """
        if not self.isButtonSizeUpToDate:
            numButtons = len(self.buttons)
            for i, button in enumerate(self.buttons):
                isLast = i == numButtons - 1
                button.align = uiconst.TOALL if isLast else uiconst.TOLEFT_PROP
                button.width = 0 if isLast else 1.0 / numButtons

            self.isButtonSizeUpToDate = True
        return Container.UpdateAlignment(self, *args, **kwds)

    def DeselectAll(self):
        for btn in self.buttons:
            btn.SetDeselected()
            if btn.panel:
                btn.panel.state = uiconst.UI_HIDDEN

    def GetSelected(self):
        for btn in self.buttons:
            if btn.IsSelected():
                return btn.btnID

    def SelectByID(self, btnID):
        for btn in self.buttons:
            if btn.btnID == btnID:
                self.Select(btn)

    def SetSelectedByID(self, btnID, animate = True):
        for btn in self.buttons:
            if btn.btnID == btnID:
                self.SetSelected(btn, animate=animate)

    def SelectFirst(self):
        for btn in self.buttons:
            if not btn.isDisabled:
                self.Select(btn)
                return

    def SetSelected(self, selectedBtn, animate = True):
        for btn in self.buttons:
            if btn == selectedBtn:
                btn.SetSelected(animate=animate)
                if btn.panel:
                    btn.panel.state = uiconst.UI_PICKCHILDREN
            else:
                btn.SetDeselected(animate=animate)
                if btn.panel and btn.panel != selectedBtn.panel:
                    btn.panel.state = uiconst.UI_HIDDEN

    def Select(self, selectedBtn, animate = True, *args):
        if selectedBtn.isDisabled:
            return
        self.SetSelected(selectedBtn, animate=animate)
        if self.callback is not None:
            self.callback(selectedBtn.btnID)

    def EnableButton(self, btnID):
        for button in self.buttons:
            if button.btnID == btnID:
                button.label.color.a = 1
                button.isDisabled = False

    def DisableButton(self, btnID):
        for button in self.buttons:
            if button.btnID == btnID:
                button.label.color.a = 0.4
                button.isDisabled = True


class ToggleButtonGroupButton(Container):
    OPACITY_SELECTED = 1.0
    OPACITY_HOVER = 0.125
    default_padRight = 1
    default_align = uiconst.TOLEFT_PROP
    default_state = uiconst.UI_NORMAL
    default_iconSize = 32
    default_colorSelected = None
    default_iconOpacity = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.controller = attributes.controller
        self.btnID = attributes.Get('btnID', None)
        self.panel = attributes.Get('panel', None)
        self.colorSelected = attributes.Get('colorSelected', self.default_colorSelected)
        label = attributes.Get('label', None)
        iconPath = attributes.Get('iconPath', None)
        iconSize = attributes.Get('iconSize', None)
        iconSize = iconSize or self.default_iconSize
        iconOpacity = attributes.get('iconOpacity', self.default_iconOpacity)
        self.hint = attributes.Get('hint', None)
        self.isSelected = False
        self.isDisabled = attributes.Get('isDisabled', False)
        if iconPath:
            self.icon = GlowSprite(parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=iconSize, height=iconSize, texturePath=iconPath, iconOpacity=iconOpacity, color=Color.GRAY6)
            self.label = None
        else:
            self.label = LabelThemeColored(text=label, parent=self, align=uiconst.CENTER, fontsize=10)
            self.icon = None
        self.selectedBG = RaisedUnderlay(bgParent=self, color=self.colorSelected, isGlowEdgeRotated=True)
        if self.isDisabled:
            self.SetDisabled()

    def SetDisabled(self):
        self.isDisabled = True
        if self.icon:
            self.icon.opacity = 0.1
        if self.label:
            self.label.opacity = 0.1
        self.selectedBG.SetDisabled()

    def SetEnabled(self):
        self.isDisabled = False
        self.selectedBG.SetEnabled()

    def OnMouseEnter(self, *args):
        if not self.isSelected and not self.isDisabled:
            self.selectedBG.OnMouseEnter()
            if self.icon:
                self.icon.OnMouseEnter()
            else:
                uicore.animations.FadeTo(self.label, self.label.opacity, OPACITY_LABEL_HOVER, duration=uiconst.TIME_ENTRY)

    def OnMouseExit(self, *args):
        if self.isDisabled:
            return
        if not self.isSelected:
            self.selectedBG.OnMouseExit()
        if self.icon:
            self.icon.OnMouseExit()
        elif not self.isSelected:
            uicore.animations.FadeTo(self.label, self.label.opacity, OPACITY_LABEL_IDLE, duration=uiconst.TIME_EXIT)

    def OnMouseDown(self, *args):
        if self.isDisabled:
            return
        if self.icon:
            self.icon.OnMouseDown()
        self.selectedBG.OnMouseDown()

    def OnMouseUp(self, *args):
        if self.isDisabled:
            return
        if self.icon:
            self.icon.OnMouseUp()
        self.selectedBG.OnMouseUp()

    def SetSelected(self, animate = True):
        self.isSelected = True
        self.selectedBG.Select()
        if self.label:
            self.label.opacity = OPACITY_LABEL_HOVER
        if self.icon:
            self.icon.OnMouseExit()

    def SetDeselected(self, animate = True):
        self.isSelected = False
        if self.label:
            self.label.opacity = 1.0
        if self.isDisabled:
            return
        self.selectedBG.Deselect()

    def IsSelected(self):
        return self.isSelected

    def OnClick(self, *args):
        if not self.isDisabled:
            self.controller.Select(self)


class Button(ButtonCore):
    """
    Standard UI button
    """
    __guid__ = 'uicontrols.Button'
    default_alwaysLite = False
    default_iconSize = 32
    default_icon = None
    default_color = None

    def ApplyAttributes(self, attributes):
        self.color = attributes.get('color', self.default_color)
        self.iconPath = attributes.get('icon', self.default_icon)
        self.iconSize = attributes.get('iconSize', self.default_iconSize)
        args = attributes.get('args', None)
        ButtonCore.ApplyAttributes(self, attributes)
        if args == 'self':
            self.args = self

    def Prepare_(self):
        self.sr.label = LabelThemeColored(parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=OPACITY_LABEL_IDLE, fontsize=10)
        if self.iconPath is not None:
            if self.iconSize:
                width = self.iconSize
                height = self.iconSize
            else:
                width = height = min(self.width, self.height)
            self.icon = GlowSprite(parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTER, pos=(0,
             0,
             width,
             height), texturePath=self.iconPath, color=self.color, iconOpacity=0.75)
            self.sr.label.state = uiconst.UI_HIDDEN
            self.width = width + 4
            self.height = height + 4
        else:
            self.icon = None
        self.sr.hilite = Fill(bgParent=self, color=(0.7, 0.7, 0.7, 0.5), state=uiconst.UI_HIDDEN)
        self.sr.activeframe = FrameThemeColored(parent=self, name='activeline', state=uiconst.UI_HIDDEN, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.1)
        self.underlay = RaisedUnderlay(name='backgroundFrame', bgParent=self, state=uiconst.UI_DISABLED, color=self.color)

    def Update_Size_(self):
        if self.iconPath is None:
            self.width = min(256, self.fixedwidth or max(40, self.sr.label.width + 20))
            self.height = self.fixedheight or max(18, min(32, self.sr.label.textheight + 4))

    def SetLabel_(self, label):
        if not self or self.destroyed:
            return
        text = self.text = label
        self.sr.label.text = text
        self.Update_Size_()

    def OnSetFocus(self, *args):
        if self.disabled:
            return
        if self and not self.destroyed and self.parent and self.parent.name == 'inlines':
            if self.parent.parent and self.parent.parent.sr.node:
                browser = uiutil.GetBrowser(self)
                if browser:
                    uthread.new(browser.ShowObject, self)
        if self and not self.destroyed and self.sr and self.sr.activeframe:
            self.sr.activeframe.state = uiconst.UI_DISABLED
        btns = self.GetDefaultBtnsInSameWnd()
        if btns:
            self.SetWndDefaultFrameState(btns, 0)

    def OnMouseEnter(self, *args):
        self.Blink(False)
        if not self.disabled:
            self.underlay.OnMouseEnter()
            if self.icon:
                self.icon.OnMouseEnter()
            else:
                uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, OPACITY_LABEL_HOVER, duration=uiconst.TIME_ENTRY)

    def OnMouseExit(self, *args):
        self.underlay.OnMouseExit()
        if self.icon:
            self.icon.OnMouseExit()
        else:
            uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, OPACITY_LABEL_IDLE, duration=uiconst.TIME_EXIT)

    def OnMouseDown(self, *args):
        if self.disabled:
            return
        if self.mousedownfunc:
            if type(self.args) == tuple:
                self.mousedownfunc(*self.args)
            else:
                self.mousedownfunc(self.args or self)
        self.underlay.OnMouseDown()
        if self.icon:
            self.icon.OnMouseDown()
        else:
            uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, OPACITY_LABEL_MOUSEDOWN, duration=0.3)

    def OnMouseUp(self, *args):
        if self.mouseupfunc:
            if type(self.args) == tuple:
                self.mouseupfunc(*self.args)
            else:
                self.mouseupfunc(self.args or self)
        if not self.disabled:
            self.underlay.OnMouseUp()
            if self.icon:
                self.icon.OnMouseUp()
            else:
                uicore.animations.FadeTo(self.sr.label, self.sr.label.opacity, OPACITY_LABEL_HOVER)

    def Confirm(self, *args):
        ButtonCore.Confirm(self)
        self.underlay.Blink()

    def SetColor(self, color):
        self.underlay.SetFixedColor(color)

    def Disable(self):
        ButtonCore.Disable(self)
        self.underlay.SetDisabled()

    def Enable(self):
        ButtonCore.Enable(self)
        self.underlay.SetEnabled()

    def Blink(self, on_off = 1, blinks = 1000, time = 800):
        self.blinking = on_off
        if on_off:
            self.underlay.Blink(blinks)
        else:
            self.underlay.StopBlink()


class BrowseButton(Container):
    """
        A browse button for paging, it's either prev or next and has arrow icons too
    """
    __guid__ = 'uicls.BrowseButton'
    default_width = 60
    default_align = uiconst.TOPLEFT
    default_height = 16
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        prev = attributes.prev
        icon = attributes.icon
        if prev:
            icon = '38_227'
            align = uiconst.CENTERLEFT
            text = localization.GetByLabel('UI/Common/Prev')
            self.backforth = -1
        else:
            icon = '38_228'
            align = uiconst.CENTERRIGHT
            text = localization.GetByLabel('UI/Common/Next')
            self.backforth = 1
        self.func = attributes.func
        self.args = attributes.args or ()
        self.alphaOver = 1.0
        self.alphaNormal = 0.8
        self.alphaDisabled = 0.4
        if self.state == uiconst.UI_DISABLED:
            self.disabled = True
        else:
            self.disabled = False
        iconCont = Container(parent=self, align=align, width=16, height=16)
        textCont = Container(parent=self, align=uiconst.TOALL)
        self.sr.icon = Icon(icon=icon, parent=iconCont, pos=(0, 0, 16, 16), align=align, idx=0, state=uiconst.UI_DISABLED)
        self.sr.label = EveLabelMedium(text=text, parent=textCont, align=align, state=uiconst.UI_DISABLED, left=16)
        self.SetOpacity(self.alphaNormal)

    def OnClick(self, *args):
        if self.destroyed or self.disabled:
            return
        if self.func:
            self.func(self, *self.args)

    def OnMouseEnter(self, *args):
        if self.destroyed or self.disabled:
            return
        if getattr(self, 'alphaOver', None):
            self.SetOpacity(self.alphaOver)

    def OnMouseExit(self, *args):
        if self.destroyed or self.disabled:
            return
        if getattr(self, 'alphaNormal', None):
            self.SetOpacity(self.alphaNormal)

    def LoadIcon(self, *args, **kw):
        self.sr.icon.LoadIcon(*args, **kw)

    def Disable(self):
        """
        We set the state to UI_NORMAL to enable hints for disabled buttons
        """
        self.opacity = self.alphaDisabled
        self.disabled = True

    def Enable(self):
        self.opacity = self.alphaNormal
        self.disabled = False


class ButtonIcon(Container):
    """
        A button that is only a white icon without background (until hovered over)
    """
    __guid__ = 'uicontrols.ButtonIcon'
    OPACITY_IDLE = 0.0
    OPACITY_INACTIVE = 0.0
    OPACITY_MOUSEHOVER = 1.1
    OPACITY_MOUSECLICK = 2.5
    OPACITY_SELECTED = 0.5
    COLOR_DEFAULT = (1, 1, 1, 1.0)
    OPACITY_GLOW_IDLE = 0.0
    OPACITY_GLOW_MOUSEHOVER = 0.3
    OPACITY_GLOW_MOUSECLICK = 0.6
    default_func = None
    default_args = None
    default_width = 32
    default_height = 32
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_texturePath = None
    default_isActive = True
    default_iconSize = 16
    default_rotation = 0
    default_noBgSize = 1
    default_iconColor = None
    default_colorSelected = None
    default_isHoverBGUsed = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.func = attributes.get('func', self.default_func)
        self.args = attributes.get('args', self.default_args)
        self.isActive = attributes.get('isActive', True)
        self.texturePath = attributes.get('texturePath', self.default_texturePath)
        self.iconSize = attributes.get('iconSize', self.default_iconSize)
        self.iconColor = attributes.get('iconColor', self.default_iconColor)
        self.isHoverBGUsed = attributes.Get('isHoverBGUsed', self.default_isHoverBGUsed)
        self.colorSelected = attributes.Get('colorSelected', self.default_colorSelected)
        self.rotation = attributes.Get('rotation', self.default_rotation)
        if self.isHoverBGUsed is None:
            if self.iconSize < self.default_noBgSize:
                self.isHoverBGUsed = True
            else:
                self.isHoverBGUsed = False
        self.isSelected = False
        self.enabled = True
        self.ConstructIcon()
        self.glowIcon = None
        width, height = self.GetAbsoluteSize()
        size = min(width, height)
        bgCont = Container(name='bgCont', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=size, height=size)
        self.bgContainer = bgCont
        self.selectedBG = None
        self.ConstructBackground()
        self.blinkBg = None
        self.SetActive(self.isActive, animate=False)

    def ConstructBackground(self):
        self.mouseEnterBG = SpriteThemeColored(name='mouseEnterBG', bgParent=self.bgContainer, texturePath='res:/UI/Texture/classes/ButtonIcon/mouseEnter.png', opacity=0.0, color=self.colorSelected)
        self.mouseDownBG = SpriteThemeColored(name='mouseEnterBG', bgParent=self.bgContainer, texturePath='res:/UI/Texture/classes/ButtonIcon/mouseDown.png', opacity=0.0, color=self.colorSelected)

    def ConstructIcon(self):
        self.icon = GlowSprite(name='icon', parent=self, align=uiconst.CENTER, width=self.iconSize, height=self.iconSize, texturePath=self.texturePath, state=uiconst.UI_DISABLED, color=self.iconColor, iconOpacity=0.5, gradientStrength=0.5, rotation=self.rotation)

    def SetTexturePath(self, texturePath):
        self.icon.SetTexturePath(texturePath)

    def SetColor(self, color):
        self.mouseEnterBG.SetFixedColor(color)
        self.mouseDownBG.SetFixedColor(color)

    def ConstructBlinkBackground(self):
        if self.blinkBg:
            return
        self.blinkBg = SpriteThemeColored(name='blinkBG', bgParent=self.bgContainer, texturePath='res:/UI/Texture/classes/ButtonIcon/mouseEnter.png', opacity=0.0)

    def ConstructSelectedBackground(self):
        if self.selectedBG:
            return
        self.selectedBG = FillThemeColored(name='selectedBG', bgParent=self.bgContainer, colorType=uiconst.COLORTYPE_UIHILIGHT, idx=0, color=self.colorSelected)

    def AccessIcon(self):
        return self.icon

    def AccessBackground(self):
        return self.bgContainer

    def Disable(self, opacity = 0.5):
        self.opacity = opacity
        self.enabled = 0
        if self.mouseEnterBG:
            self.mouseEnterBG.StopAnimations()
            self.mouseEnterBG.opacity = 0.0

    def Enable(self):
        self.opacity = 1.0
        self.enabled = 1

    def SetRotation(self, value):
        self.icon.SetRotation(value)

    def UpdateIconState(self, animate = True):
        if self.isSelected:
            glowAmount = 0.3
        elif uicore.uilib.mouseOver == self:
            if uicore.uilib.leftbtn:
                glowAmount = self.OPACITY_MOUSECLICK
            else:
                glowAmount = self.OPACITY_MOUSEHOVER
        elif self.isActive:
            glowAmount = self.OPACITY_IDLE
        else:
            glowAmount = self.OPACITY_INACTIVE
        if isinstance(self.icon, GlowSprite):
            if animate:
                uicore.animations.MorphScalar(self.icon, 'glowAmount', self.icon.glowAmount, glowAmount, duration=0.2)
            else:
                self.icon.glowAmount = glowAmount

    def SetActive(self, isActive, animate = True):
        self.UpdateIconState(animate)

    def SetSelected(self):
        self.isSelected = True
        self.ConstructSelectedBackground()
        self.selectedBG.opacity = self.OPACITY_SELECTED
        iconColor = GetIconColor(self.colorSelected)
        self.icon.SetRGBA(*iconColor)
        self.UpdateIconState()

    def SetDeselected(self):
        self.isSelected = False
        if self.selectedBG:
            self.selectedBG.opacity = 0.0
        self.icon.SetRGBA(*self.COLOR_DEFAULT)
        self.UpdateIconState()

    def Blink(self, duration = 0.8, loops = 1):
        self.ConstructBlinkBackground()
        uicore.animations.FadeTo(self.blinkBg, 0.0, 0.9, duration=duration, curveType=uiconst.ANIM_WAVE, loops=loops)

    def StopBlink(self):
        if self.blinkBg:
            uicore.animations.FadeOut(self.blinkBg, 0.3)

    def OnClick(self, *args):
        if not self.func or not self.enabled:
            return
        if audioConst.BTNCLICK_DEFAULT:
            uicore.Message(audioConst.BTNCLICK_DEFAULT)
        if type(self.args) == tuple:
            self.func(*self.args)
        elif self.args:
            self.func(self.args)
        else:
            self.func()

    def OnMouseEnter(self, *args):
        self.StopBlink()
        if not self.enabled or self.isSelected:
            return
        self.UpdateIconState()
        if self.isHoverBGUsed:
            uicore.animations.FadeIn(self.mouseEnterBG, 0.5, duration=0.2)

    def OnMouseExit(self, *args):
        self.SetActive(self.isActive)
        self.UpdateIconState()
        if self.isHoverBGUsed:
            uicore.animations.FadeOut(self.mouseEnterBG, duration=0.2)

    def OnMouseDown(self, *args):
        if not self.enabled:
            return
        self.SetActive(self.isActive)
        if self.isHoverBGUsed:
            uicore.animations.FadeTo(self.mouseDownBG, self.mouseDownBG.opacity, 1.0, duration=0.1)
            uicore.animations.FadeOut(self.mouseEnterBG, duration=0.1)
        self.UpdateIconState()

    def OnMouseUp(self, *args):
        if self.isHoverBGUsed:
            uicore.animations.FadeOut(self.mouseDownBG, duration=0.1)
        if not self.enabled:
            return
        self.UpdateIconState()
        if uicore.uilib.mouseOver == self:
            if self.isHoverBGUsed:
                uicore.animations.FadeIn(self.mouseEnterBG, 0.5, duration=0.1)

    def OnEndDrag(self, *args):
        if uicore.uilib.mouseOver != self:
            uicore.animations.FadeOut(self.mouseEnterBG, duration=0.2)
        elif self.isHoverBGUsed:
            uicore.animations.FadeIn(self.mouseEnterBG, duration=0.1)
        uicore.animations.FadeOut(self.mouseDownBG, duration=0.1)


class IconButton(Container):
    """
        DEPRICATED: Please use uicontrols.ButtonIcon instead
    """
    default_alphaNormal = 0.6
    default_alphaOver = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        icon = attributes.icon
        iconAlign = attributes.iconAlign
        if iconAlign is None:
            iconAlign = uiconst.TOALL
        self.func = attributes.func
        self.args = attributes.args or ()
        ignoreSize = attributes.ignoreSize or False
        iconPos = attributes.iconPos or (1, 2, 24, 24)
        self.alphaOver = attributes.alphaOver or self.default_alphaOver
        self.alphaNormal = attributes.alphaOver or self.default_alphaNormal
        self.state = attributes.state or uiconst.UI_NORMAL
        self.sr.icon = Icon(icon=icon, parent=self, pos=iconPos, align=iconAlign, idx=0, state=uiconst.UI_DISABLED, ignoreSize=ignoreSize)
        self.SetOpacity(self.default_alphaNormal)
        self.keepHighlight = False

    def OnClick(self, *args):
        if self.func:
            self.func(*self.args)

    def KeepHighlight(self, *args):
        self.keepHighlight = True
        self.SetOpacity(self.alphaOver)

    def RemoveHighlight(self, *args):
        self.keepHighlight = False
        self.SetOpacity(self.default_alphaNormal)

    def OnMouseEnter(self, *args):
        if not self.destroyed and getattr(self, 'alphaOver', None):
            self.SetOpacity(self.alphaOver)

    def OnMouseExit(self, *args):
        if not self.destroyed and getattr(self, 'default_alphaNormal', None) and not self.keepHighlight:
            self.SetOpacity(self.default_alphaNormal)

    def LoadIcon(self, *args, **kw):
        self.sr.icon.LoadIcon(*args, **kw)


class BaseButton(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.sr.preleft = None
        self.sr.pretop = None
        self.sr.selection = None
        self.sr.selected = 0
        self.sr.enterAlt = 0
        self.sr.hilite = None
        self.Click = None
        self.DblClick = None
        self.MouseEnter = None
        self.MouseExit = None
        self.enabled = 1
        self.clicks = 0

    def Select(self):
        if self is None or self.destroyed:
            return
        if self.sr.selection is None:
            self.sr.selection = Sprite(parent=self, padding=(-int(self.width * 0.5),
             -int(self.width * 0.5),
             -int(self.width * 0.5),
             -int(self.width * 0.5)), name='selection', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/selectionglow.dds', color=(0.75, 0.75, 0.75, 1.0), align=uiconst.TOALL)
        self.sr.selected = 1

    def Deselect(self):
        if self and self.sr and self.sr.selection is not None:
            self.sr.selection.state = uiconst.UI_HIDDEN
            self.sr.selected = 0

    def Disable(self):
        self.opacity = 0.5
        self.enabled = 0

    def Enable(self):
        self.opacity = 1.0
        self.enabled = 1

    def OnDblClick(self, *etc):
        if not self.enabled:
            return
        if self.DblClick:
            self.clicks += 1
        elif self.Click:
            self.Click(self)

    def OnClick(self, *etc):
        if not self.enabled:
            return
        self.clicks += 1
        if self.DblClick:
            self.sr.clickTimer = base.AutoTimer(250, self.ClickTimer)
        elif self.Click:
            self.Click(self)

    def ClickTimer(self, *args):
        if self.clicks == 1:
            if self.Click:
                self.Click(self)
        elif self.clicks >= 2:
            if self.DblClick:
                self.DblClick(self)
        if not self.destroyed:
            self.clicks = 0
            self.sr.clickTimer = None

    def OnMouseEnter(self, *etc):
        if not self.enabled:
            return
        eve.Message('CCCellEnter')
        if getattr(self, 'over', None):
            if not getattr(self, 'active', 0):
                self.rectTop = self.over
        else:
            if not self.sr.pretop:
                self.sr.pretop = self.top
                self.sr.preRectTop = self.rectTop
            self.rectTop += self.rectHeight
            self.top -= self.sr.enterAlt
        if self.MouseEnter:
            self.MouseEnter(self)

    def OnMouseExit(self, *etc):
        if getattr(self, 'idle', None):
            if not getattr(self, 'active', 0):
                self.rectTop = self.idle
        elif self.sr.pretop is not None:
            self.top = self.sr.pretop
            self.rectTop = self.sr.preRectTop
        if self.MouseExit:
            self.MouseExit(self)

    def OnMouseDown(self, *args):
        if not self.enabled:
            return
        self.top += self.sr.enterAlt

    def OnMouseUp(self, *args):
        if not self.enabled:
            return
        self.top -= self.sr.enterAlt


class BigButton(BaseButton):
    """ A big button to be used with large, graphical icons """
    __guid__ = 'xtriui.BigButton'
    default_align = uiconst.TOPLEFT
    default_width = 64
    default_height = 64
    default_name = 'bigButton'
    default_state = uiconst.UI_NORMAL
    OPACITY_IDLE = 0.0
    OPACITY_HOVER = 0.5
    OPACITY_MOUSEDOWN = 0.85

    def Startup(self, width, height, iconMargin = 0, iconOpacity = 0.75):
        self.sr.icon = GlowSprite(parent=self, pos=(0, 0, 0, 0), padding=(iconMargin,
         iconMargin,
         iconMargin,
         iconMargin), name='icon', state=uiconst.UI_DISABLED, align=uiconst.TOALL, filter=True, iconOpacity=iconOpacity)
        self.sr.hilite = Fill(bgParent=self, color=(0.7, 0.7, 0.7, 0.0), state=uiconst.UI_HIDDEN)
        self.setfocus = 0
        self.killfocus = 0
        self.width = width
        self.height = height
        self.sr.smallcaption = None
        self.sr.caption = None
        self.sr.activeHilite = Frame(bgParent=self, color=(1, 1, 1, 0.3), state=uiconst.UI_HIDDEN)
        self.AdjustSizeAndPosition(width, height)
        self.underlay = RaisedUnderlay(name='backgroundFrame', bgParent=self)

    def AdjustSizeAndPosition(self, width, height):
        self.sr.enterAlt = min(2, max(6, self.height / 16))

    def SetIconByIconID(self, iconID):
        if iconID is not None:
            self.sr.icon.LoadIcon(iconID)

    def SetTexturePath(self, texturePath):
        self.sr.icon.SetTexturePath(texturePath)

    def SetInCaption(self, capstr):
        if self.sr.caption:
            self.sr.caption.Close()
        if '&' in capstr and ';' in capstr:
            capstr = self.ParseHTML(capstr)
        caption = EveLabelLargeUpper(text=capstr, parent=self, idx=0, align=uiconst.CENTER)
        caption.state = uiconst.UI_DISABLED
        self.sr.caption = caption

    def SetCaption(self, capstr):
        self.SetSmallCaption(capstr)

    def SetSmallCaption(self, capstr, inside = 0, maxWidth = None):
        if not self.sr.smallcaption:
            self.sr.smallcaption = EveLabelSmall(text='', parent=self, state=uiconst.UI_DISABLED, idx=0, width=self.width)
        self.sr.smallcaption.busy = 1
        if inside:
            self.sr.smallcaption.SetAlign(uiconst.CENTER)
        else:
            self.sr.smallcaption.SetAlign(uiconst.CENTERTOP)
            self.sr.smallcaption.top = self.height + 2
        self.sr.smallcaption.width = maxWidth or self.width
        self.sr.smallcaption.busy = 0
        self.sr.smallcaption.text = '<center>' + capstr

    def ParseHTML(self, text):
        for k in translatetbl:
            text = text.replace(k, translatetbl[k])

        return text

    def OnMouseExit(self, *etc):
        self.underlay.OnMouseExit()
        if self.MouseExit:
            self.MouseExit(self)
        self.timer = None
        self.sr.icon.OnMouseExit()

    def OnMouseEnter(self, *etc):
        eve.Message('CCCellEnter')
        self.underlay.OnMouseEnter()
        if self.MouseEnter:
            self.MouseEnter(self)
        self.sr.icon.OnMouseEnter()

    def OnMouseDown(self, *args):
        if not self.enabled:
            return
        self.Blink(0)
        self.underlay.OnMouseDown()
        self.sr.icon.OnMouseDown()

    def OnMouseUp(self, *args):
        if uicore.uilib.mouseOver == self:
            self.underlay.OnMouseUp()
        self.sr.icon.OnMouseUp()

    def Blink(self, on_off = 1, blinks = 3):
        if on_off:
            uicore.animations.FadeTo(self.sr.hilite, 0.0, 0.3, duration=0.75, curveType=uiconst.ANIM_WAVE, loops=blinks)
        else:
            uicore.animations.FadeOut(self.sr.hilite, 0.0)

    def OnSetFocus(self, *args):
        if self.setfocus:
            self.sr.activeHilite.state = uiconst.UI_DISABLED

    def OnKillFocus(self, *args):
        if self.killfocus:
            self.sr.activeHilite.state = uiconst.UI_HIDDEN


class NavigationButtons(Container):
    default_height = 19
    default_width = 38
    default_buttonSize = 19
    default_align = uiconst.TOPLEFT
    default_alphaNormal = 0.7
    default_alphaOver = 1.0
    default_alphaDisabled = 0.1

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        buttonSize = attributes.get('buttonSize', self.default_buttonSize)
        self.alphaOver = attributes.alphaOver or self.default_alphaOver
        self.alphaNormal = attributes.alphaOver or self.default_alphaNormal
        self.alphaDisabled = attributes.get('alphaDisabled', self.default_alphaDisabled)
        backBtnHint = attributes.get('backBtnHint', localization.GetByLabel('UI/Control/EveWindow/Next'))
        forwardBtnHint = attributes.get('forwardBtnHint', localization.GetByLabel('UI/Control/EveWindow/Previous'))
        self.backBtnFunc = attributes.get('backBtnFunc')
        self.forwardBtnFunc = attributes.get('forwardBtnFunc')
        self.backBtn = backBtn = Sprite(name='backBtn', texturePath='res:/UI/Texture/classes/ButtonIcon/navigationPrevLarge.png', parent=self, pos=(0,
         0,
         buttonSize,
         buttonSize), align=uiconst.CENTERLEFT, hint=backBtnHint, opacity=self.default_alphaNormal)
        self.backBtn.OnClick = self.OnBackBtnClicked
        self.forwardBtn = forwardkBtn = Sprite(name='forwardkBtn', texturePath='res:/UI/Texture/classes/ButtonIcon/navigationNextLarge.png', parent=self, pos=(0,
         0,
         buttonSize,
         buttonSize), align=uiconst.CENTERRIGHT, hint=forwardBtnHint)
        self.forwardBtn.OnClick = self.OnForwardBtnClicked
        for eachBtn in (forwardkBtn, backBtn):
            eachBtn.OnMouseDown = (self.OnMouseDownOnBtn, eachBtn)
            eachBtn.OnMouseUp = (self.OnMouseUpOnBtn, eachBtn)
            eachBtn.OnMouseEnter = (self.OnMouseEnterButton, eachBtn)
            eachBtn.OnMouseExit = (self.OnMouseExitButton, eachBtn)

    def GetBackBtn(self):
        return self.backBtn

    def GetForwardBtn(self):
        return self.forwardBtn

    def OnBackBtnClicked(self, *args):
        if self.backBtn.state != uiconst.UI_DISABLED:
            self.backBtnFunc()
            return True
        return False

    def OnForwardBtnClicked(self, *args):
        if self.forwardBtn.state != uiconst.UI_DISABLED:
            self.forwardBtnFunc()
            return True
        return False

    def OnMouseDownOnBtn(self, button, mouseButton, *args):
        if mouseButton != uiconst.MOUSELEFT:
            return
        button.top = 2

    def OnMouseUpOnBtn(self, button, *args):
        button.top = 0

    def OnMouseEnterButton(self, button, *args):
        self.SetOpacity(self.alphaOver)

    def OnMouseExitButton(self, button, *args):
        self.SetOpacity(self.alphaNormal)

    def EnableBackBtn(self):
        return self.EnableBtn(btn=self.backBtn)

    def DisableBackBtn(self):
        return self.DisableBtn(btn=self.backBtn)

    def EnableForwardBtn(self):
        return self.EnableBtn(btn=self.forwardBtn)

    def DisableForwardBtn(self):
        return self.DisableBtn(btn=self.forwardBtn)

    def EnableBtn(self, btn):
        uicore.animations.BlinkIn(btn, startVal=btn.opacity, endVal=self.alphaNormal, duration=0.1, loops=1)
        btn.state = uiconst.UI_NORMAL

    def DisableBtn(self, btn):
        uicore.animations.BlinkIn(btn, startVal=btn.opacity, endVal=self.alphaDisabled, duration=0.1, loops=1)
        btn.state = uiconst.UI_DISABLED

    def AnimateBackBtn(self):
        return self.AnimateBtn(self.backBtn)

    def AnimateForwardBtn(self):
        return self.AnimateBtn(self.forwardBtn)

    def AnimateBtn(self, btn):
        uicore.animations.SpGlowFadeIn(btn, glowColor=(0.8, 0.8, 1.0, 0.3), glowFactor=0.1, glowExpand=0.5, duration=0.2, loops=1, curveType=uiconst.ANIM_WAVE)


translatetbl = {'&aring;': '\xe5',
 '&gt;': '>',
 '&yen;': '\xa5',
 '&ograve;': '\xd2',
 '&bull;': '\x95',
 '&trade;': '\x99',
 '&Ntilde;': '\xd1',
 '&Yacute;': '\xdd',
 '&Atilde;': '\xc3',
 '&aelig;': '\xc6',
 '&oelig;': '\x9c',
 '&auml;': '\xc4',
 '&Uuml;': '\xdc',
 '&Yuml;': '\x9f',
 '&lt;': '<',
 '&Icirc;': '\xce',
 '&shy;': '\xad',
 '&Oacute;': '\xd3',
 '&yacute;': '\xfd',
 '&acute;': '\xb4',
 '&atilde;': '\xc3',
 '&cedil;': '\xb8',
 '&Ecirc;': '\xca',
 '&not;': '\xac',
 '&AElig;': '\xc6',
 '&oslash;': '\xf8',
 '&iquest;': '\xbf',
 '&laquo;': '\xab',
 '&Igrave;': '\xcc',
 '&ccedil;': '\xc7',
 '&nbsp;': '\xa0',
 '&Auml;': '\xc4',
 '&brvbar;': '\xa6',
 '&Otilde;': '\xd5',
 '&szlig;': '\xdf',
 '&agrave;': '\xe0',
 '&Ocirc;': '\xd4',
 '&egrave;': '\xc8',
 '&iexcl;': '\xa1',
 '&frac12;': '\xbd',
 '&ordf;': '\xaa',
 '&ntilde;': '\xd1',
 '&ocirc;': '\xd4',
 '&Oslash;': '\xd8',
 '&THORN;': '\xde',
 '&yuml;': '\x9f',
 '&Eacute;': '\xc9',
 '&ecirc;': '\xca',
 '&times;': '\xd7',
 '&Aring;': '\xc5',
 '&tilde;': '~',
 '&mdash;': '-',
 '&Ugrave;': '\xd9',
 '&Agrave;': '\xc0',
 '&sup1;': '\xb9',
 '&eth;': '\xd0',
 '&iuml;': '\xcf',
 '&reg;': '\xae',
 '&Egrave;': '\xc8',
 '&divide;': '\xf7',
 '&Ouml;': '\xd6',
 '&igrave;': '\xcc',
 '&otilde;': '\xd5',
 '&pound;': '\xa3',
 '&frasl;': '/',
 '&ETH;': '\xd0',
 '&plusmn;': '\xb1',
 '&sup2;': '\xb2',
 '&frac34;': '\xbe',
 '&Aacute;': '\xc1',
 '&cent;': '\xa2',
 '&frac14;': '\xbc',
 '&euml;': '\xcb',
 '&iacute;': '\xcd',
 '&para;': '\xb6',
 '&ordm;': '\xba',
 '&uuml;': '\xdc',
 '&icirc;': '\xce',
 '&copy;': '\xa9',
 '&Iuml;': '\xcf',
 '&Ograve;': '\xd2',
 '&Ucirc;': '\xdb',
 '&Zeta;': 'Z',
 '&minus;': '-',
 '&deg;': '\xb0',
 '&and;': '&',
 '&curren;': '\xa4',
 '&ucirc;': '\xdb',
 '&ugrave;': '\xd9',
 '&sup3;': '\xb3',
 '&Acirc;': '\xc2',
 '&quot;': '"',
 '&Uacute;': '\xda',
 '&OElig;': '\x8c',
 '&uacute;': '\xda',
 '&acirc;': '\xc2',
 '&macr;': '\xaf',
 '&Euml;': '\xcb',
 '&Ccedil;': '\xc7',
 '&aacute;': '\xc1',
 '&micro;': '\xb5',
 '&eacute;': '\xc9',
 '&middot;': '\xb7',
 '&Iacute;': '\xcd',
 '&amp;': '&',
 '&uml;': '\xa8',
 '&thorn;': '\xde',
 '&ouml;': '\xd6',
 '&raquo;': '\xbb',
 '&sect;': '\xa7',
 '&oacute;': '\xd3'}
from carbonui.control.buttons import ButtonCoreOverride
ButtonCoreOverride.__bases__ = (Button,)
