#Embedded file name: carbonui/control\combo.py
from carbonui.control.basicDynamicScroll import BasicDynamicScrollOverride
from carbonui.control.menu import ClearMenuLayer
from carbonui.control.scroll import ScrollCoreOverride
from carbonui.control.scrollentries import SE_GenericCore, ScrollEntryNode
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.control.label import LabelOverride as Label
import carbonui.const as uiconst
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.glowSprite import GlowSprite
import uthread
import _weakref
import localization
import log
import fontConst
import blue
from carbonui.util.various_unsorted import GetAttrs, GetBrowser
from utillib import KeyVal
OPACITY_IDLE = 0.0
OPACITY_HOVER = 0.5
OPACITY_MOUSEDOWN = 0.85

class ComboCore(Container):
    __guid__ = 'uicontrols.ComboCore'
    default_name = 'combo'
    default_align = uiconst.TOTOP
    default_label = ''
    default_state = uiconst.UI_NORMAL
    default_fontsize = None
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None
    default_shadow = [(1, -1, -1090519040)]
    default_prefskey = None
    default_options = []
    default_select = None
    default_callback = None
    default_adjustWidth = False
    default_width = 100
    default_height = 20
    default_cursor = uiconst.UICURSOR_SELECT
    default_iconOnly = False
    default_noChoiceLabel = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        if self.default_fontsize is None:
            self.default_fontsize = fontConst.DEFAULT_FONTSIZE
        self.isTabStop = 1
        self.sr.label = None
        self.selectedValue = None
        self._expanding = False
        self._comboDropDown = None
        self.adjustWidth = attributes.get('adjustWidth', self.default_adjustWidth)
        self.prefskey = attributes.get('prefskey', self.default_prefskey)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.iconOnly = attributes.get('iconOnly', self.default_iconOnly)
        self.shadow = attributes.get('shadow', self.default_shadow)
        self.noChoiceLabel = attributes.Get('noChoiceLabel', self.default_noChoiceLabel)
        self.Prepare_()
        self.OnChange = attributes.get('callback', self.default_callback)
        self.SetLabel_(attributes.get('label', self.default_label))
        self.LoadOptions(attributes.get('options', self.default_options), attributes.get('select', self.default_select))
        if self.adjustWidth and self.align not in (uiconst.TOTOP, uiconst.TOBOTTOM):
            self.AutoAdjustWidth_()
        elif self.align == uiconst.TOALL:
            self.width = 0
        else:
            self.width = attributes.get('width', self.default_width)
        if self.align in (uiconst.TOLEFT, uiconst.TORIGHT, uiconst.TOALL):
            self.height = 0
        else:
            self.height = attributes.Get('height', self.default_height)

    def Prepare_(self):
        self.sr.content = Container(parent=self, name='__maincontent', padLeft=3)
        self.sr.iconParent = Container(parent=self.sr.content, name='iconParent', align=uiconst.TOLEFT, width=self.height, state=uiconst.UI_HIDDEN)
        self.sr.selectedIcon = Icon(name='icon', parent=self.sr.iconParent, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=16, height=16)
        self.sr.textclipper = Container(parent=self.sr.content, name='__textclipper', clipChildren=True)
        self.Prepare_SelectedText_()
        self.Prepare_Expander_()
        self.Prepare_Underlay_()
        self.Prepare_Label_()

    def Prepare_SelectedText_(self):
        self.sr.selected = Label(text='', fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize, parent=self.sr.textclipper, name='value', align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)

    def Prepare_Underlay_(self):
        self.sr.underlay = Frame(name='__underlay', color=(0.0, 0.0, 0.0, 0.5), frameConst=uiconst.FRAME_FILLED_CORNER0, parent=self)

    def Prepare_Expander_(self):
        self.sr.expanderParent = Container(parent=self.sr.content, align=uiconst.TORIGHT, pos=(0, 0, 16, 0), idx=0, state=uiconst.UI_DISABLED, name='__expanderParent')
        self.sr.expander = GlowSprite(parent=self.sr.expanderParent, align=uiconst.CENTER, texturePath='res:/UI/Texture/Icons/1_16_129.png', pos=(1, -1, 16, 16))

    def Prepare_Label_(self):
        self.sr.label = Label(text='', parent=self, name='label', align=uiconst.TOPLEFT, pos=(1, -13, 0, 0), fontsize=9, letterspace=2, state=uiconst.UI_DISABLED, idx=0)

    def HideText(self):
        self.sr.textclipper.state = uiconst.UI_HIDDEN

    def Close(self, *args, **kwds):
        self.Cleanup(0)
        Container.Close(self, *args, **kwds)

    def Confirm(self):
        if self.OnChange:
            val = self.GetValue()
            key = self.GetKey()
            self.OnChange(self, key, val)
        if not self.destroyed:
            self.Cleanup()

    def OnUp(self, *args):
        if not self._Expanded():
            self.Expand()
        if self._Expanded():
            self._comboDropDown().sr.scroll.BrowseNodes(1)

    def OnDown(self, *args):
        if not self._Expanded():
            self.Expand()
        if self._Expanded():
            self._comboDropDown().sr.scroll.BrowseNodes(0)

    def SetHint(self, hint):
        self.hint = hint

    def SetLabel_(self, label):
        pass

    def OnSetFocus(self, *args):
        if self and not self.destroyed and self.parent and self.parent.name == 'inlines':
            if self.parent.parent and self.parent.parent.sr.node:
                browser = GetBrowser(self)
                if browser:
                    uthread.new(browser.ShowObject, self)

    def LoadOptions(self, entries, select = None, hints = None):
        """
        entries is list of tuples, (label, returnValue, hint(optional))    
        select should be value of desired entry or string "__random__".
        The hints keyword is legacy from Eve 
        """
        screwed = [ each for each in entries if not isinstance(each[0], basestring) ]
        if screwed:
            raise RuntimeError('NonStringKeys', repr(screwed))
        entries = entries or [(localization.GetByLabel('/Carbon/UI/Controls/Combo/NoChoices'), None, None)]
        self.entries = entries
        self.hints = hints
        if select == '__random__':
            import random
            select = random.choice(entries)[1]
        elif select is None:
            select = self.entries[0][1]
        success = self.SelectItemByValue(select)
        if not success:
            self.SelectItemByValue(self.entries[0][1])
        self.AutoAdjustWidth_()

    def AutoAdjustWidth_(self):
        currentAlign = self.GetAlign()
        if self.adjustWidth and self.entries and currentAlign not in (uiconst.TOTOP, uiconst.TOBOTTOM, uiconst.TOALL):
            arrowContainerWidth = 25
            maxWidth = max([ self.GetTextWidth(each[0]) for each in self.entries ])
            self.width = max(20, maxWidth) + arrowContainerWidth

    def GetKey(self):
        """ Returns the selected caption, if any."""
        return self.sr.selected.text

    def GetValue(self):
        """ Returns the selected value, if any."""
        if self.selectedValue is not None:
            return self.selectedValue
        else:
            return

    def GetIndex(self):
        if self.sr.selected.text:
            i = 0
            for each in self.entries:
                label = each[0]
                if label == self.sr.selected.text:
                    return i
                i += 1

    def SelectItemByIndex(self, i):
        self.SelectItemByLabel(self.entries[i][0])

    def SelectItemByLabel(self, label):
        for each in self.entries:
            if each[0] == label:
                self.UpdateSelectedValue(each)
                return

        raise RuntimeError('LabelNotInEntries', label)

    def SelectItemByValue(self, val):
        for each in self.entries:
            if each[1] == val:
                self.UpdateSelectedValue(each)
                return True

        log.LogWarn('ValueNotInEntries', val)
        return False

    SetValue = SelectItemByValue

    def UpdateSelectedValue(self, entry):
        if not self.iconOnly:
            self.sr.selected.text = self.glowLabel.text = entry[0]
        if len(entry) >= 4 and entry[3]:
            self.sr.selectedIcon.LoadIcon(entry[3], ignoreSize=True)
            self.sr.iconParent.state = uiconst.UI_DISABLED
        else:
            self.sr.iconParent.state = uiconst.UI_HIDDEN
        self.selectedValue = entry[1]

    def UpdateSettings(self):
        prefskey = self.prefskey
        if prefskey is None:
            return
        config = prefskey[-1]
        prefstype = prefskey[:-1]
        s = GetAttrs(settings, *prefstype)
        if s:
            s.Set(config, self.GetValue())

    def _Expanded(self):
        return bool(self._comboDropDown and self._comboDropDown())

    def OnMouseEnter(self, *args):
        self.sr.backgroundFrame.OnMouseEnter()
        self.sr.expander.OnMouseEnter()
        uicore.animations.FadeTo(self.glowLabel, self.glowLabel.opacity, 0.5, duration=uiconst.TIME_ENTRY)
        uicore.animations.FadeTo(self.sr.selected, self.sr.selected.opacity, 1.5, duration=uiconst.TIME_ENTRY)

    def OnMouseExit(self, *args):
        self.sr.backgroundFrame.OnMouseExit()
        self.sr.expander.OnMouseExit()
        uicore.animations.FadeTo(self.glowLabel, self.glowLabel.opacity, 0.0, duration=uiconst.TIME_EXIT)
        uicore.animations.FadeTo(self.sr.selected, self.sr.selected.opacity, 1.0, duration=uiconst.TIME_EXIT)

    def OnMouseDown(self, *args):
        if not self._Expanded():
            uthread.new(self.Expand)
        self.sr.backgroundFrame.OnMouseDown()

    def OnMouseUp(self, *args):
        self.sr.backgroundFrame.OnMouseUp()

    def Prepare_OptionMenu_(self):
        ClearMenuLayer()
        menu = Container(parent=uicore.layer.menu, pos=(0, 0, 200, 200), align=uiconst.RELATIVE)
        menu.sr.scroll = BasicDynamicScrollOverride(parent=menu)
        menu.sr.scroll.OnKillFocus = self.OnScrollFocusLost
        menu.sr.scroll.OnSelectionChange = self.OnScrollSelectionChange
        menu.sr.scroll.Confirm = self.Confirm
        menu.sr.scroll.OnUp = self.OnUp
        menu.sr.scroll.OnDown = self.OnDown
        menu.sr.scroll.OnRight = self.Confirm
        menu.sr.scroll.OnLeft = self.Confirm
        Fill(parent=menu, color=(0.0, 0.0, 0.0, 1.0))
        return (menu, menu.sr.scroll)

    def GetEntryClass(self):
        return SE_GenericCore

    def GetTextWidth(self, text):
        return uicore.font.GetTextWidth(text, fontsize=self.fontsize, fontFamily=self.fontFamily, fontStyle=self.fontStyle, fontPath=self.fontPath)

    def GetEntryWidth(self, data):
        width = self.GetTextWidth(data['label'])
        if data['icon'] is not None:
            width += 16
        return width

    def GetScrollEntry(self, label, returnValue, hint = None, icon = None, indentLevel = None):
        if not hint and self.hints:
            hint = self.hints.get(label, '')
        data = KeyVal()
        data.OnClick = self.OnEntryClick
        data.data = (label, returnValue)
        data.label = unicode(label)
        data.fontStyle = self.fontStyle
        data.fontFamily = self.fontFamily
        data.fontPath = self.fontPath
        data.fontsize = self.fontsize
        data.shadow = (self.shadow,)
        data.decoClass = self.GetEntryClass()
        data.hideLines = True
        data.icon = icon
        data.indentLevel = indentLevel
        data.hint = hint
        if returnValue == self.selectedValue:
            data.isSelected = True
        return (data, returnValue)

    def GetMaxEntryWidth(self, scrollEntries, w):
        maxWidth = max([ self.GetEntryWidth(entry) for entry in scrollEntries ])
        return max(maxWidth + 24, w)

    def GetScrollList(self):
        scrolllist = []
        if self.noChoiceLabel and len(self.entries) == 1:
            data = KeyVal(label='<color=gray>%s' % self.noChoiceLabel, icon=None, selectable=False)
            scrollEntry = ScrollEntryNode(**data.__dict__)
            scrolllist.append(scrollEntry)
        else:
            for each in self.entries:
                label = each[0]
                if not label:
                    continue
                data, returnValue = self.GetScrollEntry(*each)
                scrollEntry = ScrollEntryNode(**data.__dict__)
                scrolllist.append(scrollEntry)

        return scrolllist

    def Expand(self, position = None):
        """
        Construct the drop-down scroll
        """
        if self._expanding:
            return
        try:
            self._expanding = True
            sm.GetService('audio').SendUIEvent('wise:/msg_ComboExpand_play')
            menu, scroll = self.Prepare_OptionMenu_()
            scrolllist = self.GetScrollList()
            scroll.LoadContent(contentList=scrolllist)
            if position:
                l, t, w, h = position
            else:
                l, t, w, h = self.GetAbsolute()
            menu.width = self.GetMaxEntryWidth(scrolllist, w)
            totalHeight = sum([ each.height for each in scroll.sr.nodes[:6] ])
            menu.height = totalHeight + 2 + scroll.padTop + scroll.padBottom
            menu.left = l
            menu.top = min(t + h + 1, uicore.desktop.height - menu.height - 8)
            self._comboDropDown = _weakref.ref(menu)
            uthread.new(self.ShowSelected)
            return scroll
        finally:
            self._expanding = False

    def GetExpanderIconWidth(self):
        if self.sr.expanderParent:
            return self.sr.expanderParent.width + self.sr.expanderParent.padLeft + self.sr.expanderParent.padRight
        return 0

    def ShowSelected(self, *args):
        blue.synchro.Yield()
        scroll = self._comboDropDown().sr.scroll
        uicore.registry.SetFocus(scroll)
        scroll.ScrollToSelectedNode()

    def OnEntryClick(self, entry, *args):
        uicore.Message('ComboEntrySelect')
        key, val = entry.sr.node.data
        self.SelectItemByValue(val)
        self.Cleanup()
        if self.OnChange:
            self.OnChange(self, key, val)
        log.LogInfo('Combo.OnEntryClick END')

    def OnComboClose(self, *args):
        self.Cleanup(0)

    def Cleanup(self, setfocus = 1):
        if self._comboDropDown:
            ClearMenuLayer()
        self._comboDropDown = None
        if setfocus:
            uicore.registry.SetFocus(self)

    def OnScrollFocusLost(self, *args):
        uthread.new(self.Confirm)

    def OnScrollSelectionChange(self, selected):
        if selected:
            self.SelectItemByLabel(selected[0].label)

    def OnChar(self, enteredChar, *args):
        if enteredChar < 32 and enteredChar != uiconst.VK_RETURN:
            return False
        if not self._Expanded():
            scroll = self.Expand()
            scroll.OnChar(enteredChar, *args)
        return True


class SelectCore(ScrollCoreOverride):
    __guid__ = 'uicls.SelectCore'

    def LoadEntries(self, entries):
        scrolllist = []
        for entryName, entryValue, selected in entries:
            scrolllist.append(ScrollEntryNode(label=entryName, value=entryValue, isSelected=selected))

        self.LoadContent(contentList=scrolllist)

    def GetValue(self):
        return [ node.value for node in self.GetSelected() ] or None

    def SetValue(self, val):
        if type(val) != list:
            val = [val]
        for node in self.GetNodes():
            if node.value in val:
                self._SelectNode(node)


class ComboCoreOverride(ComboCore):
    pass
