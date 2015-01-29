#Embedded file name: carbonui/control\singlelineedit.py
import math
from carbonui.control.menu import ClearMenuLayer
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.primitives.frame import FrameCoreOverride as Frame
from carbonui.control.label import LabelOverride as Label
from carbonui.control.combo import ComboCoreOverride as Combo
import carbonui.languageConst as languageConst
from eve.client.script.ui.control.buttons import ButtonIcon
import uthread
import blue
import sys
import weakref
import fontConst
import carbonui.const as uiconst
import localization
import trinity
import eveLocalization
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.line import Line
from carbon.common.script.util.timerstuff import AutoTimer
from carbon.common.script.util.commonutils import StripTags
from carbonui.control.menuLabel import MenuLabel
from carbonui.util.various_unsorted import GetWindowAbove, GetBrowser, GetClipboardData

class SinglelineEditCore(Container):
    __guid__ = 'uicontrols.SinglelineEditCore'
    default_name = 'edit_singleline'
    default_align = uiconst.TOTOP
    default_width = 100
    default_height = 20
    default_state = uiconst.UI_NORMAL
    default_maxLength = None
    default_label = ''
    default_setvalue = ''
    default_hinttext = ''
    default_passwordCharacter = None
    default_autoselect = False
    default_adjustWidth = False
    default_dynamicHistoryWidth = False
    default_readonly = False
    default_OnChange = None
    default_OnSetFocus = None
    default_OnFocusLost = None
    default_OnReturn = None
    default_OnAnyChar = None
    default_OnInsert = None
    default_fontsize = None
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None
    TEXTLEFTMARGIN = 4
    TEXTRIGHTMARGIN = 4
    registerHistory = True

    def ApplyAttributes(self, attributes):
        if self.default_fontsize is None:
            self.default_fontsize = fontConst.DEFAULT_FONTSIZE
        self.DECIMAL = '.'
        Container.ApplyAttributes(self, attributes)
        self.rightAlignedButtons = weakref.WeakSet()
        self._clearButton = None
        self.hinttext = ''
        self.isTabStop = 1
        self.integermode = None
        self.floatmode = None
        self.passwordchar = None
        self.caretIndex = (0, 0)
        self.selFrom = None
        self.selTo = None
        self.value = None
        self.text = ''
        self.suffix = ''
        self.maxletters = None
        self.historyMenu = None
        self.historySaveLast = None
        self.displayHistory = False
        self.allowHistoryInnerMatches = False
        self.maxHistoryShown = 5
        self.numericControlsCont = None
        self.updateNumericInputThread = None
        self.OnChange = None
        self.OnFocusLost = None
        self.OnReturn = None
        self.OnInsert = None
        self.readonly = attributes.get('readonly', self.default_readonly)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self._textClipper = Container(name='_textClipper', parent=self, clipChildren=True, padding=(1, 0, 1, 0))
        self._textClipper._OnSizeChange_NoBlock = self.OnClipperSizeChange
        self.Prepare_()
        self.autoselect = attributes.get('autoselect', self.default_autoselect)
        self.adjustWidth = attributes.get('adjustWidth', self.default_adjustWidth)
        self.dynamicHistoryWidth = attributes.get('dynamicHistoryWidth', self.default_dynamicHistoryWidth)
        self.sr.text.shadow = self.sr.hinttext.shadow = attributes.get('shadow', None)
        fontcolor = attributes.get('fontcolor', (1.0, 1.0, 1.0, 1.0))
        if fontcolor is not None:
            self.SetTextColor(fontcolor)
        if attributes.get('ints', None):
            self.IntMode(*attributes.ints)
        elif attributes.get('floats', None):
            self.FloatMode(*attributes.floats)
        self.SetPasswordChar(attributes.get('passwordCharacter', self.default_passwordCharacter))
        self.SetMaxLength(attributes.get('maxLength', self.default_maxLength))
        self.SetLabel(attributes.get('label', self.default_label))
        self.SetHintText(attributes.get('hinttext', self.default_hinttext))
        self.SetValue(attributes.get('setvalue', self.default_setvalue))
        self.height = 20
        self.OnChange = attributes.get('OnChange', self.default_OnChange)
        self.__OnSetFocus = attributes.get('OnSetFocus', self.default_OnSetFocus)
        self.OnFocusLost = attributes.get('OnFocusLost', self.default_OnFocusLost)
        self.OnReturn = attributes.get('OnReturn', self.default_OnReturn)
        self.OnInsert = attributes.get('OnInsert', self.default_OnInsert)
        OnAnyChar = attributes.get('OnAnyChar', self.default_OnAnyChar)
        if OnAnyChar:
            self.OnAnyChar = OnAnyChar

    def Prepare_(self):
        self.Prepare_Background_()
        self.sr.text = Label(text='', parent=self._textClipper, name='value', align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, maxLines=1, left=self.TEXTLEFTMARGIN, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize)
        self.sr.hinttext = Label(text='', parent=self._textClipper, name='hinttext', align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, maxLines=1, left=self.TEXTLEFTMARGIN, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize)

    def SetHintText(self, hint):
        self.hinttext = hint
        self.CheckHintText()

    def AutoFitToText(self, text = None, minWidth = None):
        """Adjusts the width of the control to fit 'text' or currently set text"""
        if self.align in (uiconst.TOTOP, uiconst.TOBOTTOM, uiconst.TOALL):
            raise RuntimeError('Incorrect alignment for SingleLine.AutoFitToText')
        if text is not None:
            textwidth, textheight = self.sr.text.MeasureTextSize(text)
            autoWidth = textwidth + self.TEXTLEFTMARGIN * 2 + 2
        else:
            autoWidth = self.sr.text.textwidth + self.TEXTLEFTMARGIN * 2 + 2
        if minWidth:
            autoWidth = max(minWidth, autoWidth)
        self.width = autoWidth
        self.sr.text.left = self.TEXTLEFTMARGIN

    def CheckHintText(self):
        if self.GetText():
            self.sr.hinttext.display = False
        else:
            self.sr.hinttext.display = True
        self.sr.hinttext.text = self.hinttext

    def SetTextColor(self, color):
        self.sr.text.SetRGB(*color)
        self.sr.hinttext.SetRGB(*color)
        self.sr.hinttext.SetAlpha(self.sr.hinttext.GetAlpha() * 0.5)

    def Prepare_Background_(self):
        if not self.sr.underlay:
            self.sr.underlay = Frame(name='__underlay', frameConst=('ui_1_16_161', 7, -2), bgParent=self)

    def Prepare_Caret_(self):
        self.sr.caret = Fill(parent=self._textClipper, name='caret', align=uiconst.TOPLEFT, color=(1.0, 1.0, 1.0, 0.75), pos=(self.TEXTLEFTMARGIN,
         1,
         1,
         1), idx=0, state=uiconst.UI_HIDDEN)

    def ShowClearButton(self, icon = None, hint = None, showOnLetterCount = 1):
        if self._clearButton:
            self._clearButton.Close()
        icon = icon or 'res:/UI/Texture/Icons/73_16_210.png'
        clearButton = self.AddIconButton(icon, hint)
        clearButton.OnClick = self.OnClearButtonClick
        clearButton.Hide()
        clearButton._showOnLetterCount = showOnLetterCount
        self._clearButton = clearButton
        return clearButton

    def OnClearButtonClick(self):
        self.SetValue(u'')

    def AddIconButton(self, texturePath, hint = None):
        from eve.client.script.ui.control.buttons import ButtonIcon
        rightAlignedButton = ButtonIcon(texturePath=texturePath, pos=(0, 0, 16, 16), align=uiconst.CENTERRIGHT, parent=self, hint=hint, idx=0)
        self.rightAlignedButtons.add(rightAlignedButton)
        return rightAlignedButton

    def RefreshTextClipper(self):
        if self._clearButton:
            if len(self.text) >= self._clearButton._showOnLetterCount:
                self._clearButton.Show()
            else:
                self._clearButton.Hide()
        padRight = 1
        iconLeft = 1
        for each in self.rightAlignedButtons:
            if not each.destroyed and each.display:
                padRight += each.width
                each.left = iconLeft
                iconLeft += each.width

        self._textClipper.padRight = padRight
        w, h = self._textClipper.GetAbsoluteSize()
        self.sr.text.SetRightAlphaFade(-self.sr.text.left + w - 3, 8)

    def OnClipperSizeChange(self, newWidth, newHeight):
        if newWidth:
            self.RefreshCaretPosition()
            self.RefreshSelectionDisplay()
            self.RefreshTextClipper()

    def LoadCombo(self, id, options, callback = None, setvalue = None, comboIsTabStop = 1):
        for each in self.children[:]:
            if each.name == 'combo':
                each.Close()

        combo = Combo(parent=self, label='', options=options, name=id, select=setvalue, callback=self.OnComboChange, pos=(0, 0, 16, 16), align=uiconst.BOTTOMRIGHT)
        combo.sr.inputCallback = callback
        combo.isTabStop = comboIsTabStop
        combo.name = 'combo'
        combo.Confirm = self.ComboConfirm
        combo.Hide()
        self.sr.combo = combo
        comboButton = self.AddIconButton('res:/UI/Texture/Icons/38_16_229.png')
        comboButton.name = 'combo'
        comboButton.OnMouseDown = (self.ExpandCombo, combo)

    def ExpandCombo(self, combo, *args, **kwds):
        if not combo._Expanded():
            uthread.new(combo.Expand, self.GetAbsolute())

    def ComboConfirm(self, *args):
        if self.sr.combo and not self.sr.combo.destroyed:
            self.OnComboChange(self.sr.combo, self.sr.combo.GetKey(), self.sr.combo.GetValue())
        self.sr.combo.Cleanup(setfocus=0)

    def OnUp(self, *args):
        if self.sr.combo:
            if not self.sr.combo._Expanded():
                uthread.new(self.sr.combo.Expand, self.GetAbsolute())
            else:
                self.sr.combo.OnUp()

    def OnDown(self, *args):
        if self.sr.combo:
            if not self.sr.combo._Expanded():
                uthread.new(self.sr.combo.Expand, self.GetAbsolute())
            else:
                self.sr.combo.OnDown()

    def GetComboValue(self):
        if self.sr.combo:
            return self.sr.combo.GetValue()

    def OnComboChange(self, combo, label, value, *args):
        self.SetValue(label, updateIndex=0)
        if combo.sr.inputCallback:
            combo.sr.inputCallback(combo, label, value)

    def ClearHistory(self, *args):
        id, mine, all = self.GetHistory(getAll=1)
        if id in all:
            del all[id]
            settings.user.ui.Set('editHistory', all)

    def RegisterHistory(self, value = None):
        if self.integermode or self.floatmode or self.passwordchar is not None or not self.registerHistory:
            return
        id, mine, all = self.GetHistory(getAll=1)
        current = (value or self.GetValue(registerHistory=0)).rstrip()
        if current not in mine:
            mine.append(current)
        all[id] = mine
        settings.user.ui.Set('editHistory', all)

    def CheckHistory(self):
        if self.integermode or self.floatmode or self.passwordchar is not None or self.displayHistory == 0:
            return
        if self.readonly:
            return
        valid = self.GetValid()
        if valid:
            self.ShowHistoryMenu(valid[:5])
            return 1
        self.CloseHistoryMenu()
        return 0

    def GetValid(self):
        current = self.GetValue(registerHistory=0)
        id, mine = self.GetHistory()
        valid = [ each for each in mine if each.lower().startswith(current.lower()) and each != current ]
        valid.sort(key=lambda x: len(x))
        return valid

    def ShowHistoryMenu(self, history):
        hadMenu = 0
        if self.historyMenu and self.historyMenu():
            hadMenu = 1
        self.CloseHistoryMenu()
        if not history:
            return
        l, t, w, h = self.GetAbsolute()
        mp = Container(name='historyMenuParent', parent=uicore.layer.menu, pos=(l,
         t + h + 2,
         w,
         0), align=uiconst.TOPLEFT)
        if not hadMenu:
            mp.opacity = 0.0
        Frame(parent=mp, frameConst=uiconst.FRAME_BORDER1_CORNER0, color=(1.0, 1.0, 1.0, 0.2))
        Frame(parent=mp, frameConst=uiconst.FRAME_FILLED_CORNER0, color=(0.0, 0.0, 0.0, 0.75))
        mps = Container(name='historyMenuSub', parent=mp, idx=0)
        self.PopulateHistoryMenu(mps, mp, history)
        mp.sr.entries = mps
        self.historyMenu = weakref.ref(mp)
        if not hadMenu:
            uicore.effect.MorphUI(mp, 'opacity', 1.0, 250.0, float=1)

    def PopulateHistoryMenu(self, mps, mp, history):
        for entry in history:
            displayText, editText = entry if isinstance(entry, tuple) else (entry, entry)
            self.GetHistoryMenuEntry(displayText, editText, mps, mp)

    def GetHistoryMenuEntry(self, displayText, text, menuSub, mp, info = None):
        ep = Container(name='entryParent', parent=menuSub, clipChildren=1, pos=(0, 0, 0, 16), align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        ep.OnMouseEnter = (self.HEMouseEnter, ep)
        ep.OnMouseDown = (self.HEMouseDown, ep)
        ep.OnMouseUp = (self.HEMouseUp, ep)
        Line(parent=ep, align=uiconst.TOBOTTOM)
        t = Label(text=displayText, parent=ep, left=6, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)
        ep.height = t.textheight + 4
        ep.sr.hilite = Fill(parent=ep, color=(1.0, 1.0, 1.0, 0.25), pos=(1, 1, 1, 1), state=uiconst.UI_HIDDEN)
        ep.selected = 0
        ep.sr.menu = mp
        ep.string = text
        mp.height += ep.height
        if self.dynamicHistoryWidth:
            mp.width = max(mp.width, t.width + 12)
        ep.info = info

    def HEMouseDown(self, entry, mouseButton, *args):
        if mouseButton == uiconst.MOUSELEFT:
            self.SetValue(entry.string, updateIndex=1)
            self.OnHistoryClick(entry.string)

    def HEMouseUp(self, entry, mouseButton, *args):
        if mouseButton == uiconst.MOUSELEFT:
            self.CloseHistoryMenu()

    def HEMouseEnter(self, entry, *args):
        if not (self.historyMenu and self.historyMenu()):
            return
        hm = self.historyMenu()
        for _entry in hm.sr.entries.children:
            _entry.sr.hilite.state = uiconst.UI_HIDDEN
            _entry.selected = 0

        entry.sr.hilite.state = uiconst.UI_DISABLED
        entry.selected = 1

    def GetHistory(self, getAll = 0):
        id = self.GetHistoryID()
        all = settings.user.ui.Get('editHistory', {})
        if type(all) == list:
            log.LogError('Singlelineedit error: all:', all)
            log.LogTraceback('Singlelineedit error: all: %s' % all, severity=log.LGERR)
            settings.user.ui.Delete('editHistory')
            all = {}
        if getAll:
            return (id, all.get(id, []), all)
        return (id, all.get(id, []))

    def OnHistoryClick(self, clickedString, *args):
        """ overwriteable - called when an item in the history is clicked """
        pass

    def CloseHistoryMenu(self):
        if not (self.historyMenu and self.historyMenu()):
            return
        self.active = None
        ClearMenuLayer()
        self.historyMenu = None

    def BrowseHistory(self, down):
        """
        Moving up/down in the list of entries in the historymenu
        """
        justopened = 0
        if not (self.historyMenu and self.historyMenu()):
            if not self.CheckHistory():
                return
            justopened = 1
        hm = self.historyMenu()
        currentIdx = None
        i = 0
        for entry in hm.sr.entries.children:
            if entry.selected:
                currentIdx = i
            entry.sr.hilite.state = uiconst.UI_HIDDEN
            entry.selected = 0
            i += 1

        if justopened:
            return
        if currentIdx is None:
            if down:
                currentIdx = 0
            else:
                currentIdx = len(hm.sr.entries.children) - 1
        elif down:
            currentIdx += 1
            if currentIdx >= len(hm.sr.entries.children):
                currentIdx = 0
        else:
            currentIdx -= 1
            if currentIdx < 0:
                currentIdx = len(hm.sr.entries.children) - 1
        self.active = active = hm.sr.entries.children[currentIdx]
        active.sr.hilite.state = uiconst.UI_DISABLED
        active.selected = 1
        if not getattr(self, 'blockSetValue', 0):
            self.SetValue(active.string, updateIndex=1)

    def GetHistoryID(self):
        id = ''
        item = self
        while item.parent:
            id = '/' + item.name + id
            if isinstance(item, Window):
                break
            item = item.parent

        return id

    def SetReadOnly(self, state):
        self.readonly = state

    def SetMaxLength(self, maxLength):
        self.maxletters = maxLength

    def SetHistoryVisibility(self, status):
        self.displayHistory = status

    def SetPasswordChar(self, char):
        self.passwordchar = char

    def OnSetFocus(self, *args):
        if self.pickState != uiconst.TR2_SPS_ON:
            return
        if not self.readonly and uicore.imeHandler:
            uicore.imeHandler.SetFocus(self)
        if self and not self.destroyed and self.parent and self.parent.name == 'inlines':
            if self.parent.parent and getattr(self.parent.parent.sr, 'node', None):
                browser = GetBrowser(self)
                if browser:
                    uthread.new(browser.ShowObject, self)
        self.sr.background.AnimEntry()
        if self.integermode or self.floatmode:
            self.SetText(self.text)
            self.caretIndex = self.GetCursorFromIndex(-1)
        self.ShowCaret()
        if self.autoselect:
            self.SelectAll()
        else:
            self.RefreshSelectionDisplay()
        if self.__OnSetFocus:
            self.__OnSetFocus(*args)

    def OnKillFocus(self, *args):
        if not self.readonly and uicore.imeHandler:
            uicore.imeHandler.KillFocus(self)
        if self.autoselect:
            self.SelectNone()
        self.sr.background.AnimExit()
        if self.integermode or self.floatmode:
            ret = self.CheckBounds(self.text, 1, allowEmpty=bool(self.hinttext), returnNoneIfOK=1)
            if ret is not None:
                text = ret
            else:
                text = self.text
            self.SetText(text, 1)
        self.HideCaret()
        self.CloseHistoryMenu()
        if self.OnFocusLost:
            uthread.new(self.OnFocusLost, self)

    def SetValue(self, text, add = 0, keepSelection = 0, updateIndex = 1, docallback = 1):
        text = text or ''
        isString = isinstance(text, basestring)
        if isString:
            text = StripTags(text, stripOnly=['localized'])
        if self.floatmode:
            if isString:
                text = self.PrepareFloatString(text)
            text = self.CheckBounds(text, 0, bool(self.hinttext))
        elif self.integermode:
            text = self.CheckBounds(text, 0, bool(self.hinttext))
        else:
            text = text.replace('&lt;', '<').replace('&gt;', '>')
            if self.maxletters:
                text = text[:self.maxletters]
        if updateIndex:
            self.SetText(text, 0)
            self.caretIndex = self.GetCursorFromIndex(-1)
        self.SetText(text, 1)
        self.selFrom = self.selTo = None
        self.RefreshSelectionDisplay()
        self.OnTextChange(docallback)

    def GetValue(self, refreshDigits = 1, raw = 0, registerHistory = 1):
        ret = self.text
        if refreshDigits and (self.integermode or self.floatmode):
            ret = self.CheckBounds(ret, 0)
        if self.integermode:
            ret = ret or 0
            try:
                ret = int(ret)
            except:
                ret = 0
                sys.exc_clear()

        elif self.floatmode:
            ret = ret or 0
            floatdigits = self.floatmode[2]
            try:
                ret = round(float(ret), floatdigits)
            except:
                ret = 0.0
                sys.exc_clear()

        elif not raw:
            ret = ret.replace('<', '&lt;').replace('>', '&gt;')
        if registerHistory:
            self.RegisterHistory()
        return ret

    def IntMode(self, minint = None, maxint = None):
        if maxint is None:
            maxint = sys.maxint
        self.integermode = (minint, min(sys.maxint, maxint))
        self.floatmode = None
        self.OnMouseWheel = self.MouseWheel
        if minint and not self.text:
            self.SetValue(minint)
        self.ShowNumericControls()

    def FloatMode(self, minfloat = None, maxfloat = None, digits = 1):
        self.floatmode = (minfloat, maxfloat, int(digits))
        self.integermode = None
        self.OnMouseWheel = self.MouseWheel
        if minfloat and not self.text:
            self.SetValue(minfloat)
        self.ShowNumericControls()

    def ShowNumericControls(self):
        if self.numericControlsCont:
            return
        self.numericControlsCont = Container(name='numericControlsCont', parent=self, align=uiconst.TORIGHT, idx=0, width=10, padding=(0, 1, 1, 1), opacity=0.75)
        self.upButton = ButtonIcon(name='upButton', parent=self.numericControlsCont, align=uiconst.CENTER, pos=(0, -4, 9, 9), iconSize=7, texturePath='res:/UI/Texture/Shared/up.png')
        self.upButton.OnMouseDown = self.OnNumericUpButtonMouseDown
        self.upButton.OnMouseUp = self.OnNumericUpButtonMouseUp
        self.downButton = ButtonIcon(name='downButton', parent=self.numericControlsCont, align=uiconst.CENTER, pos=(0, 4, 9, 9), iconSize=7, texturePath='res:/UI/Texture/Shared/down.png')
        self.downButton.OnMouseDown = self.OnNumericDownButtonMouseDown
        self.downButton.OnMouseUp = self.OnNumericDownButtonMouseUp

    def OnNumericUpButtonMouseDown(self, *args):
        ButtonIcon.OnMouseDown(self.upButton, *args)
        self.updateNumericInputThread = uthread.new(self.UpdateNumericInputThread, 1)

    def OnNumericDownButtonMouseDown(self, *args):
        ButtonIcon.OnMouseDown(self.downButton, *args)
        self.updateNumericInputThread = uthread.new(self.UpdateNumericInputThread, -1)

    def KillNumericInputThread(self):
        if self.updateNumericInputThread:
            self.updateNumericInputThread.kill()
            self.updateNumericInputThread = None

    def OnNumericUpButtonMouseUp(self, *args):
        ButtonIcon.OnMouseUp(self.upButton, *args)
        self.KillNumericInputThread()

    def OnNumericDownButtonMouseUp(self, *args):
        ButtonIcon.OnMouseUp(self.downButton, *args)
        self.KillNumericInputThread()

    def UpdateNumericInputThread(self, diff):
        sleepTime = 500
        while uicore.uilib.leftbtn:
            self.ChangeNumericValue(diff)
            blue.synchro.SleepWallclock(sleepTime)
            sleepTime -= 0.5 * sleepTime
            sleepTime = max(10, sleepTime)

    def MouseWheel(self, *args):
        if self.readonly:
            return
        self.ChangeNumericValue((uicore.uilib.dz / 120) ** 3)

    def ChangeNumericValue(self, val):
        if uicore.uilib.Key(uiconst.VK_CONTROL):
            val *= 10
        if self.integermode:
            if val > 0:
                val = max(1, long(val))
            else:
                val = min(-1, long(val))
            errorValue = self.integermode[0] or 0
        elif self.floatmode:
            val *= 1 / float(10 ** self.floatmode[2])
            errorValue = self.floatmode[0] or 0
        else:
            return
        if val > 0:
            self.upButton.Blink(0.2)
        else:
            self.downButton.Blink(0.2)
        self.ClampMinMaxValue(val)

    def ClampMinMaxValue(self, change = 0):
        if not (self.integermode or self.floatmode):
            return
        try:
            current = self.GetValue(registerHistory=0)
        except ValueError:
            current = errorValue
            sys.exc_clear()

        text = self.CheckBounds(repr(current + change), 0)
        if self.floatmode:
            floatdigits = self.floatmode[2]
            text = '%%.%df' % floatdigits % float(text)
        if uicore.registry.GetFocus() is self:
            self.SetText(text)
        else:
            self.SetText(text, format=True)
        self.caretIndex = self.GetCursorFromIndex(-1)
        self.selFrom = None
        self.selTo = None
        self.RefreshSelectionDisplay()
        self.OnTextChange()

    def OnDblClick(self, *args):
        self.caretIndex = self.GetIndexUnderCursor()
        self.selFrom = self.GetCursorFromIndex(0)
        self.selTo = self.caretIndex = self.GetCursorFromIndex(-1)
        self.RefreshCaretPosition()
        self.RefreshSelectionDisplay()
        self.RefreshTextClipper()

    def OnMouseDown(self, button, *etc):
        if uicore.uilib.mouseTravel > 10:
            return
        if hasattr(self, 'RegisterFocus'):
            self.RegisterFocus(self)
        gettingFocus = uicore.registry.GetFocus() != self
        if gettingFocus:
            uicore.registry.SetFocus(self)
        leftClick = button == uiconst.MOUSELEFT
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            if self.selFrom is None:
                self.selFrom = self.caretIndex
            self.selTo = self.caretIndex = self.GetIndexUnderCursor()
            self.RefreshCaretPosition()
            self.RefreshSelectionDisplay()
            self.RefreshTextClipper()
        elif leftClick:
            self.caretIndex = self.mouseDownCaretIndex = self.GetIndexUnderCursor()
            self.selFrom = None
            self.selTo = None
            self.RefreshCaretPosition()
            self.RefreshSelectionDisplay()
            self.RefreshTextClipper()
            if self.autoselect and gettingFocus:
                self.SelectAll()
            else:
                self.sr.selectionTimer = AutoTimer(50, self.UpdateSelection)

    def SetSelection(self, start, end):
        """
        Set the selection to the given character range.
        """
        if start < 0:
            start = len(self.text)
        self.selFrom = self.GetCursorFromIndex(start)
        if end < 0:
            end = -1
        self.selTo = self.caretIndex = self.GetCursorFromIndex(end)
        self.RefreshCaretPosition()
        self.RefreshSelectionDisplay()
        self.RefreshTextClipper()

    def UpdateSelection(self):
        oldCaretIndex = self.mouseDownCaretIndex
        newCaretIndex = self.GetIndexUnderCursor()
        self.selFrom = oldCaretIndex
        self.selTo = newCaretIndex
        self.caretIndex = newCaretIndex
        self.RefreshCaretPosition()
        self.RefreshSelectionDisplay()
        self.RefreshTextClipper()

    def SelectNone(self):
        self.selFrom = (None, None)
        self.selTo = (None, None)
        self.RefreshSelectionDisplay()

    def OnMouseUp(self, *args):
        self.mouseDownCaretIndex = None
        self.sr.selectionTimer = None

    def GetIndexUnderCursor(self):
        l, t = self.sr.text.GetAbsolutePosition()
        cursorXpos = uicore.uilib.x - l
        return self.sr.text.GetIndexUnderPos(cursorXpos)

    def GetCursorFromIndex(self, index):
        return self.sr.text.GetWidthToIndex(index)

    def RefreshCaretPosition(self):
        if self.destroyed:
            return
        self.GetCaret()
        self.sr.caret.left = self.sr.text.left + self.caretIndex[1] - 1
        if not (self.integermode or self.floatmode):
            w, h = self._textClipper.GetAbsoluteSize()
            if self.sr.text.textwidth < w - self.TEXTLEFTMARGIN - self.TEXTRIGHTMARGIN:
                self.sr.text.left = self.TEXTLEFTMARGIN
            else:
                if self.sr.text.left + self.sr.text.textwidth < w - self.TEXTLEFTMARGIN - self.TEXTRIGHTMARGIN:
                    self.sr.text.left = w - self.TEXTLEFTMARGIN - self.TEXTRIGHTMARGIN - self.sr.text.textwidth
                if self.sr.caret.left > w - self.TEXTRIGHTMARGIN:
                    diff = self.sr.caret.left - w + self.TEXTRIGHTMARGIN
                    self.sr.text.left -= diff
                elif self.sr.caret.left < self.TEXTLEFTMARGIN:
                    diff = -self.sr.caret.left + self.TEXTLEFTMARGIN
                    self.sr.text.left += diff
            self.sr.caret.left = self.sr.text.left + self.caretIndex[1] - 1

    def ShowCaret(self):
        self.GetCaret()
        self.RefreshCaretPosition()
        w, h = self.GetAbsoluteSize()
        self.sr.caret.height = h - 4
        self.sr.caret.top = 2
        self.sr.caret.state = uiconst.UI_DISABLED
        self.sr.caretTimer = AutoTimer(400, self.BlinkCaret)

    ShowCursor = ShowCaret

    def HideCaret(self):
        self.sr.caretTimer = None
        if self.sr.get('caret', None):
            self.sr.caret.state = uiconst.UI_HIDDEN

    HideCursor = HideCaret

    def GetCaret(self):
        if not self.sr.get('caret', None) and not self.destroyed:
            self.Prepare_Caret_()

    def BlinkCaret(self):
        if self.destroyed:
            self.sr.caretTimer = None
            return
        if self.sr.get('caret', None):
            if not trinity.app.IsActive():
                self.sr.caret.state = uiconst.UI_HIDDEN
                return
            self.sr.caret.state = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED][self.sr.caret.state == uiconst.UI_HIDDEN]

    def OnChar(self, char, flag):
        if self.floatmode:
            if unichr(char) in ',.':
                return False
        if self.OnAnyChar(char):
            isLatinBased = uicore.font.IsLatinBased(unichr(char))
            if isLatinBased or not uicore.imeHandler:
                keyboardLanguageID = languageConst.LANG_ENGLISH
            else:
                keyboardLanguageID = uicore.imeHandler.GetKeyboardLanguageID()
            fontFamily = uicore.font.GetFontFamilyBasedOnWindowsLanguageID(keyboardLanguageID)
            if fontFamily != self.sr.text.fontFamily:
                self.sr.text.fontFamily = fontFamily
                self.sr.hinttext.fontFamily = fontFamily
            if char in [127, uiconst.VK_BACK]:
                if self.GetSelectionBounds() != (None, None):
                    self.DeleteSelected()
                else:
                    self.Delete(0)
                self.CheckHistory()
                if self.OnInsert:
                    self.OnInsert(char, flag)
                return True
            if char != uiconst.VK_RETURN:
                self.Insert(char)
                self.CheckHistory()
                if self.OnInsert:
                    self.OnInsert(char, flag)
                return True
        return False

    def OnAnyChar(self, char, *args):
        return True

    def Confirm(self, *args):
        if self.OnReturn:
            self.CloseHistoryMenu()
            return uthread.new(self.OnReturn)
        searchFrom = GetWindowAbove(self)
        if searchFrom:
            wnds = [ w for w in searchFrom.Find('trinity.Tr2Sprite2dContainer') + searchFrom.Find('trinity.Tr2Sprite2d') if getattr(w, 'btn_default', 0) == 1 ]
            if len(wnds):
                for wnd in wnds:
                    if self == wnd:
                        continue
                    if wnd.IsVisible():
                        if hasattr(wnd, 'OnClick'):
                            uthread.new(wnd.OnClick, wnd)
                        return True

        return False

    def OnKeyDown(self, vkey, flag):
        if self.floatmode:
            if vkey in (uiconst.VK_DECIMAL, uiconst.VK_OEM_PERIOD, uiconst.VK_OEM_COMMA):
                self.Insert(self.DECIMAL)
                return
        HOME = uiconst.VK_HOME
        END = uiconst.VK_END
        CTRL = uicore.uilib.Key(uiconst.VK_CONTROL)
        SHIFT = uicore.uilib.Key(uiconst.VK_SHIFT)
        if self.destroyed:
            return
        oldCaretIndex = self.caretIndex
        selection = self.GetSelectionBounds()
        index = self.caretIndex[0]
        if vkey == uiconst.VK_LEFT:
            if CTRL:
                index = self.text.rfind(' ', 0, max(index - 1, 0)) + 1 or 0
            else:
                index = max(index - 1, 0)
        elif vkey == uiconst.VK_RIGHT:
            if CTRL:
                index = self.text.find(' ', index) + 1 or len(self.text)
            else:
                index = index + 1
            index = min(index, len(self.text))
        elif vkey == HOME:
            index = 0
        elif vkey == END:
            index = len(self.text)
        elif vkey in (uiconst.VK_DELETE,):
            if self.GetSelectionBounds() != (None, None):
                self.DeleteSelected()
                return
            self.Delete(1)
        else:
            if vkey in (uiconst.VK_UP, uiconst.VK_DOWN):
                self.BrowseHistory(vkey == uiconst.VK_DOWN)
                if vkey == uiconst.VK_UP:
                    self.ChangeNumericValue(1)
                elif vkey == uiconst.VK_DOWN:
                    self.ChangeNumericValue(-1)
            else:
                self.OnUnusedKeyDown(self, vkey, flag)
            return
        self.caretIndex = self.GetCursorFromIndex(index)
        if vkey in (uiconst.VK_LEFT,
         uiconst.VK_RIGHT,
         HOME,
         END):
            if SHIFT:
                if self.selTo is not None:
                    self.selTo = self.caretIndex
                elif self.selTo is None:
                    self.selFrom = oldCaretIndex
                    self.selTo = self.caretIndex
            elif selection != (None, None):
                if vkey == uiconst.VK_LEFT:
                    index = selection[0][0]
                elif vkey == uiconst.VK_RIGHT:
                    index = selection[1][0]
                self.caretIndex = self.GetCursorFromIndex(index)
            if not SHIFT or self.selFrom == self.selTo:
                self.selFrom = self.selTo = None
            self.CloseHistoryMenu()
        self.RefreshCaretPosition()
        self.RefreshSelectionDisplay()
        self.RefreshTextClipper()

    def OnUnusedKeyDown(self, *args):
        """ Overwriteable """
        pass

    def StripNumberString(self, numberString):
        if self.integermode:
            return filter(lambda x: x in '-0123456789', numberString)
        if self.floatmode:
            return filter(lambda x: x in '-0123456789e.', numberString)
        return numberString

    def PrepareFloatString(self, numberString):
        """
        Converts strings which are supposed to be floats
        to convertable(to float) string. This is to deal with
        strings which might have been formatted outside of the client
        and dont match our locale setup.
        """
        commasInString = numberString.count(',')
        periodsInString = numberString.count('.')
        if commasInString and periodsInString:
            haveDecimal = False
            stripped = u''
            legalFloats = '-0123456789e,.'
            for each in reversed(unicode(numberString)):
                if each in legalFloats:
                    if each in u',.':
                        if haveDecimal:
                            continue
                        haveDecimal = True
                        stripped = '.' + stripped
                    else:
                        stripped = each + stripped

            return stripped
        if commasInString >= 2:
            numberString = filter(lambda x: x in '-0123456789e.', numberString)
            return numberString
        if periodsInString >= 2:
            numberString = filter(lambda x: x in '-0123456789e,', numberString)
            numberString = numberString.replace(',', self.DECIMAL)
            return numberString
        numberString = filter(lambda x: x in '-0123456789e,.', numberString)
        numberString = numberString.replace(',', self.DECIMAL)
        return numberString

    def Insert(self, ins):
        if self.readonly:
            return None
        if not isinstance(ins, basestring):
            text = unichr(ins)
        else:
            text = ins
        text = text.replace(u'\r', u' ').replace(u'\n', u'')
        current = self.GetText()
        if self.GetSelectionBounds() != (None, None):
            self.DeleteSelected()
        if (self.integermode or self.floatmode) and text:
            if self.floatmode:
                if self.DECIMAL in text and self.DECIMAL in self.text:
                    uicore.Message('uiwarning03')
                    return None
            if text == u'-':
                newvalue = self.text[:self.caretIndex[0]] + text + self.text[self.caretIndex[0]:]
                if newvalue != u'-':
                    newvalue = self.StripNumberString(newvalue)
                    try:
                        if self.integermode:
                            long(newvalue)
                        else:
                            float(newvalue)
                    except ValueError as e:
                        uicore.Message('uiwarning03')
                        sys.exc_clear()
                        return None

            elif text != self.DECIMAL:
                text = self.StripNumberString(text)
                try:
                    if self.integermode:
                        long(text)
                    else:
                        float(text)
                except ValueError as e:
                    uicore.Message('uiwarning03')
                    sys.exc_clear()
                    return None

            elif text not in '0123456789' and self.integermode:
                uicore.Message('uiwarning03')
                return None
        before = self.text[:self.caretIndex[0]]
        after = self.text[self.caretIndex[0]:]
        become = before + text + after
        if self.maxletters and len(become) > self.maxletters:
            become = become[:self.maxletters]
            uicore.Message('uiwarning03')
        self.autoselect = False
        if (self.integermode or self.floatmode) and become and become[-1] not in (self.DECIMAL, '-'):
            become = self.StripNumberString(become)
        self.SetText(become)
        index = self.caretIndex[0] + len(text)
        self.caretIndex = self.GetCursorFromIndex(index)
        self.OnTextChange()

    def GetMenu(self):
        m = []
        start, end = self.GetSelectionBounds()
        if start is not None:
            start = start[0]
        if end is not None:
            end = end[0]
        m += [(MenuLabel('/Carbon/UI/Controls/Common/Copy'), self.Copy, (start, end))]
        if not self.readonly:
            if uicore.imeHandler:
                uicore.imeHandler.GetMenuDelegate(self, None, m)
            paste = GetClipboardData()
            if paste:
                m += [(MenuLabel('/Carbon/UI/Controls/Common/Paste'), self.Paste, (paste,
                   start,
                   end,
                   True))]
            if self.displayHistory and self.passwordchar is None:
                m += [(MenuLabel('/Carbon/UI/Controls/Common/ClearHistory'), self.ClearHistory, (None,))]
        return m

    def OnTextChange(self, docallback = 1):
        """This one is not for overwrite..."""
        self.CheckHintText()
        self.RefreshCaretPosition()
        self.RefreshTextClipper()
        if docallback and self.OnChange:
            self.OnChange(self.text)

    def CheckBounds(self, qty, warnsnd = 0, allowEmpty = 1, returnNoneIfOK = 0):
        if allowEmpty and not qty:
            return ''
        if qty == '-' or qty is None:
            qty = 0
        isInt = self.integermode is not None
        isFloat = self.floatmode is not None
        if isFloat:
            minbound, maxbound = self.floatmode[:2]
        elif isInt:
            minbound, maxbound = self.integermode
        else:
            return str(qty)
        pQty = self.StripNumberString(repr(qty))
        minusIndex = pQty.find('-')
        if minusIndex > 0 and pQty[minusIndex - 1] != 'e':
            uicore.Message('uiwarning03')
            if minbound is not None:
                return minbound
            return ''
        if isFloat:
            if pQty == self.DECIMAL:
                uicore.Message('uiwarning03')
                if minbound is not None:
                    return minbound
                return ''
            qty = float(pQty or 0)
        else:
            qty = long(pQty or 0)
        warn = 0
        ret = qty
        if maxbound is not None and qty > maxbound:
            warn = 1
            ret = maxbound
        elif minbound is not None and qty < minbound:
            warn = 1
            ret = minbound
        elif returnNoneIfOK:
            return
        if warn and warnsnd:
            uicore.Message('uiwarning03')
        return ret

    def RefreshSelectionDisplay(self):
        selection = self.GetSelectionBounds()
        if selection != (None, None):
            self.GetSelectionLayer()
            f, t = selection
            self.sr.selection.left = self.sr.text.left + f[1]
            self.sr.selection.width = t[1] - f[1]
            self.sr.selection.state = uiconst.UI_DISABLED
        elif self.sr.selection:
            self.sr.selection.state = uiconst.UI_HIDDEN

    def GetSelectionBounds(self):
        if self.selFrom and self.selTo and self.selFrom[0] != self.selTo[0]:
            return (min(self.selFrom, self.selTo), max(self.selFrom, self.selTo))
        return (None, None)

    def GetSelectionLayer(self):
        w, h = self.GetAbsoluteSize()
        if not self.sr.selection:
            self.sr.selection = Fill(parent=self._textClipper, name='selection', align=uiconst.TOPLEFT, pos=(0,
             1,
             0,
             h - 2), idx=1)

    def DeleteSelected(self):
        if self.readonly:
            return
        start, end = self.GetSelectionBounds()
        self.selFrom = self.selTo = None
        self.RefreshSelectionDisplay()
        text = self.GetText()
        self.SetText(text[:start[0]] + text[end[0]:])
        self.caretIndex = start
        self.OnTextChange()

    def SelectAll(self):
        self.selFrom = self.GetCursorFromIndex(0)
        self.selTo = self.GetCursorFromIndex(-1)
        self.RefreshSelectionDisplay()

    def Cut(self, *args):
        if self.GetSelectionBounds() != (None, None):
            self.Copy()
            self.DeleteSelected()

    def Copy(self, selectStart = None, selectEnd = None):
        if self.passwordchar is None:
            text = self.GetText()
            if self.floatmode:
                text = text.replace(self.DECIMAL, self.GetLocalizedDecimal())
        else:
            text = self.passwordchar * len(self.GetText())
        if selectStart is not None and selectEnd is not None:
            blue.pyos.SetClipboardData(text[selectStart:selectEnd])
        else:
            start, end = self.GetSelectionBounds()
            if not start and not end:
                blue.pyos.SetClipboardData(text)
            else:
                blue.pyos.SetClipboardData(text[start[0]:end[0]])

    def GetLocalizedDecimal(self):
        if session:
            localizedDecimal = eveLocalization.GetDecimalSeparator(localization.SYSTEM_LANGUAGE)
        else:
            localizedDecimal = prefs.GetValue('decimal', '.')
        return localizedDecimal

    def Paste(self, paste, deleteStart = None, deleteEnd = None, forceFocus = False):
        if self.floatmode:
            haveIllegalChar = False
            legalChars = '-0123456789e,.'
            for char in paste:
                if char in legalChars:
                    if haveIllegalChar:
                        uicore.Message('uiwarning03')
                        return
                else:
                    haveIllegalChar = True

            if haveIllegalChar:
                uicore.Message('uiwarning03')
            paste = self.PrepareFloatString(paste)
        hadFocus = uicore.registry.GetFocus() is self
        if deleteStart is None or deleteEnd is None:
            start, end = self.GetSelectionBounds()
            if start is not None and end is not None:
                self.DeleteSelected()
        else:
            text = self.GetText()
            self.SetText(text[:deleteStart] + text[deleteEnd:])
            self.caretIndex = self.GetCursorFromIndex(deleteStart)
            self.OnTextChange()
        self.Insert(paste)
        if (hadFocus or forceFocus) and not uicore.registry.GetFocus() == self:
            uicore.registry.SetFocus(self)

    def EncodeOutput(self, otext):
        if not otext:
            return ''
        if self.integermode or self.floatmode:
            elem = [ each for each in otext if each not in ('-', '.') ]
            if not len(elem):
                return ''
        if self.integermode:
            return localization.formatters.FormatNumeric(long(float(otext)), useGrouping=True)
        if self.floatmode:
            decimalPlaces = self.floatmode[2]
            return localization.formatters.FormatNumeric(float(otext), useGrouping=True, decimalPlaces=decimalPlaces)
        if not isinstance(otext, basestring):
            otext = str(otext)
        return otext

    def GetText(self):
        return self.text

    def SetText(self, text, format = 0):
        if not isinstance(text, basestring):
            if self.integermode:
                text = repr(int(text))
            elif self.floatmode:
                text = '%.*f' % (self.floatmode[2], float(text))
            else:
                text = str(text)
        text = StripTags(text, stripOnly=['localized'])
        if self.passwordchar is not None:
            displayText = self.passwordchar * len(text.replace('<br>', ''))
        elif format:
            displayText = self.EncodeOutput(text) + self.suffix
        elif self.floatmode:
            displayText = text.replace(self.DECIMAL, self.GetLocalizedDecimal())
        else:
            displayText = text
        displayText = StripTags(displayText, stripOnly=['localized'])
        self.sr.text.text = displayText.replace('<', '&lt;').replace('>', '&gt;')
        self.text = text

    def Delete(self, direction = 1):
        if self.readonly:
            return
        if direction:
            begin = self.caretIndex[0]
            newCaretIndex = self.caretIndex[0]
            end = min(self.caretIndex[0] + 1, len(self.text))
        else:
            end = self.caretIndex[0]
            begin = max(self.caretIndex[0] - 1, 0)
            newCaretIndex = begin
        become = self.text[:begin] + self.text[end:]
        if not become and (self.floatmode or self.integermode):
            if self.floatmode:
                minbound, maxbound = self.floatmode[:2]
            if self.integermode:
                minbound, maxbound = self.integermode
            if minbound <= 0 <= maxbound:
                become = ''
        self.SetText(become)
        newCaretIndex = min(newCaretIndex, len(self.text))
        self.caretIndex = self.GetCursorFromIndex(newCaretIndex)
        self.OnTextChange()

    def Disable(self):
        Container.Disable(self)
        self.opacity = 0.3

    def Enable(self):
        Container.Enable(self)
        self.opacity = 1.0


class SinglelineEditCoreOverride(SinglelineEditCore):
    pass
