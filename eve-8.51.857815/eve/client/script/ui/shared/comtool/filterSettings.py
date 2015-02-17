#Embedded file name: eve/client/script/ui/shared/comtool\filterSettings.py
"""
The UI for the chat filter setup
"""
import localization
import carbonui.const as uiconst
from carbonui.primitives.line import Line
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveEditPlainText import EditPlainText
from carbonui.control.dragResizeCont import DragResizeCont
from carbonui.primitives.container import Container
from carbon.common.script.util.commonutils import StripTags
SPLITTER = ','

class ChatFilterSettings(Window):
    """
        Window where you can set which words to hightlight and filter out in chat
    """
    default_width = 380
    default_height = 300
    default_minSize = (default_width, default_height)
    default_windowID = 'ChatFilterSettings'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.updateChatFiltersFunc = attributes.get('updateChatFiltersFunc')
        bannedWordsList = attributes.get('bannedWords', [])
        highlightWordsList = attributes.get('highlightWords', [])
        blinkOnHighlightWords = attributes.get('blinkOnHighlightWords', False)
        self.SetTopparentHeight(0)
        self.SetCaption(localization.GetByLabel('UI/Chat/ChannelWindow/ChatWordFilters'))
        self.SetMinSize([self.default_width, self.default_height])
        btnGroup = ButtonGroup(btns=[], parent=self.sr.main, idx=0, line=True)
        btnGroup.AddButton(label=localization.GetByLabel('UI/Common/Buttons/Save'), func=self.Save, args=(), isDefault=True)
        btnGroup.AddButton(label=localization.GetByLabel('UI/Common/Buttons/Cancel'), func=self.Cancel, isDefault=False)
        padding = 4
        bannedWordsCont = DragResizeCont(name='bannedWordsCont', parent=self.sr.main, align=uiconst.TOTOP_PROP, minSize=0.3, maxSize=0.7, defaultSize=0.45, padding=padding)
        Line(parent=bannedWordsCont.dragArea, align=uiconst.TOTOP, padLeft=-3, padRight=-3, color=(1, 1, 1, 0.15))
        Line(parent=bannedWordsCont.dragArea, align=uiconst.TOBOTTOM, padLeft=-3, padRight=-3, color=(1, 1, 1, 0.15))
        self.bannedWordsLabel = EveLabelMedium(parent=bannedWordsCont, name='bannedWordsLabel', align=uiconst.TOTOP, state=uiconst.UI_DISABLED, text=localization.GetByLabel('UI/Chat/ChannelWindow/BannedWordText'), padTop=2, padLeft=2)
        bannedWords = SPLITTER.join(bannedWordsList)
        self.bannedWordsField = EditPlainText(name='bannedWordsField', parent=bannedWordsCont, align=uiconst.TOALL, ignoreTags=True, setvalue=bannedWords, padBottom=8, hintText=localization.GetByLabel('UI/Chat/ChannelWindow/WordSeparatorText'))
        lowerCont = Container(parent=self.sr.main, name='lowerCont', align=uiconst.TOALL, padLeft=padding, padRight=padding, padTop=8, padBottom=6)
        self.highlightWordsLabel = EveLabelMedium(parent=lowerCont, name='highlightWordsLabel', align=uiconst.TOTOP, state=uiconst.UI_DISABLED, text=localization.GetByLabel('UI/Chat/ChannelWindow/HighlightWordText'), padLeft=2)
        self.blinkOnHighlightWordsCb = Checkbox(parent=lowerCont, name='blinkCb', checked=blinkOnHighlightWords, align=uiconst.TOBOTTOM, text=localization.GetByLabel('UI/Chat/ChannelWindow/AlwaysBlink'))
        highlightWords = SPLITTER.join(highlightWordsList)
        self.highlightWordsField = EditPlainText(name='highlightWordsField', parent=lowerCont, align=uiconst.TOALL, ignoreTags=True, setvalue=highlightWords, hintText=localization.GetByLabel('UI/Chat/ChannelWindow/WordSeparatorText'))

    def Save(self):

        def GetTextParts(editField):
            text = editField.GetValue()
            text = StripTags(text)
            textParts = text.strip(SPLITTER).split(SPLITTER)
            textParts = filter(None, (word.strip() for word in textParts))
            return textParts

        bannedWords = GetTextParts(self.bannedWordsField)
        hightlightWords = GetTextParts(self.highlightWordsField)
        blinkOnHighlightWords = self.blinkOnHighlightWordsCb.checked
        self.updateChatFiltersFunc(bannedWords, hightlightWords, blinkOnHighlightWords)
        self.CloseByUser()

    def Cancel(self, btn):
        self.CloseByUser()
