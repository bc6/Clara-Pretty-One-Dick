#Embedded file name: eve/devtools/script/localizationUtil\localization_window.py
"""
A view for the insider tool for editing of EVE localization strings.
"""
import uicontrols
import uicls
import uiprimitives
import carbonui.const as uiconst
from eve.devtools.script.localizationUtil.localization_handler import LocalizationHandler

class LocalizationWindow(uicontrols.Window):
    __guid__ = 'form.UILocalizationWindow'
    default_windowID = 'UILocalizationWindow'
    default_width = 675
    default_height = 600
    default_topParentHeight = 0
    default_minSize = (default_width, default_height)
    default_caption = 'Localization Window'
    maxLabelLength = 500
    maxTextLength = 5000

    def __init__(self):
        try:
            import fsdLocalizationCache
        except ImportError:
            raise UserError('CustomError', {'error': "Localization editor can't be run on this client!"})
        else:
            super(LocalizationWindow, self).__init__()

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.localizationHandler = LocalizationHandler()
        self.localizationHandler.SelectMessage = self.SelectMessage
        self.localizationHandler.CreateMessage = self.CreateMessage
        self.localizationHandler.DeleteEntry = self.DeleteEntry
        self.ConstructLeftContainer()
        self.ConstructRightContainer()

    def ConstructLeftContainer(self):
        self.leftContainer = uiprimitives.Container(parent=self.sr.main, name='left main', pos=(0, 0, 200, 0), padding=(5, 5, 5, 5), align=uiconst.TOLEFT)
        self.ConstructSearchContainer()
        self.ConstructTreeContainer()
        self.radioButtons[0].SetChecked(1)

    def ConstructSearchContainer(self):
        self.searchContainer = uiprimitives.Container(parent=self.leftContainer, name='search container', pos=(0, 0, 0, 100), padding=(5, 5, 15, 5), align=uiconst.TOBOTTOM)
        self.ConstructRadioButtons()
        self.searchLabel = uicontrols.Label(parent=self.searchContainer, name='search label', text='Search:', pos=(0, 0, 0, 0), align=uiconst.CENTERTOP)
        self.searchEdit = uicontrols.SinglelineEdit(parent=self.searchContainer, name='search edit', pos=(0, 0, 0, 0), padding=(5, 5, 5, 10), align=uiconst.TOTOP, OnChange=self.UpdateFromEdit)

    def ConstructTreeContainer(self):
        self.treeContainerMain = uiprimitives.Container(parent=self.leftContainer, name='tree container', pos=(0, 0, 0, 0), padding=(5, 5, 15, 5), align=uiconst.TOALL)
        self.ConstructTreeScroll()
        self.UpdateScroll()

    def ConstructTreeScroll(self):
        self.leftScroll = uicontrols.Scroll(parent=self.treeContainerMain, align=uiconst.TOALL, id='scrollListContainer')

    def ConstructRadioButtons(self):
        self.searchRadioButtonsContainer = uicls.GridContainer(parent=self.searchContainer, name='search radio buttons', align=uiconst.TOTOP, height=50, columns=2)
        radioButtonConstructor = [('Label', self.localizationHandler.GetSearchedMessagesByLabel),
         ('ID', self.localizationHandler.GetSearchedMessagesByID),
         ('Text', self.localizationHandler.GetSearchedMessagesByText),
         ('Path', self.localizationHandler.GetSearchedMessagesByPath)]
        self.radioButtons = []
        for text, searchFunc in radioButtonConstructor:
            radioButton = uicontrols.Checkbox(parent=self.searchRadioButtonsContainer, text=text, groupname='searchGroup', padding=(25, 5, 5, 5), callback=self.UpdateFromEdit)
            radioButton.searchFunc = searchFunc
            self.radioButtons.append(radioButton)

    def ConstructRightContainer(self):
        self.messageContainerMain = uiprimitives.Container(parent=self.sr.main, name='right main', pos=(0, 0, 0, 0), padding=(5, 5, 5, 5), align=uiconst.TOALL)
        self.ConstructMessageIdContainer()
        self.ConstructMessageLabelContainer()
        self.ConstructMessagePathContainer()
        self.ConstructMessageDescriptionContainer()
        self.ConstructMessageSubmitContainer()
        self.ConstructMessageTextContainer()
        self.ConstructRightContainerLines()
        self.ConstructFormattingButtons()
        self.HideMessageContainer()

    def ConstructMessageIdContainer(self):
        self.msgIdContainer = uiprimitives.Container(parent=self.messageContainerMain, name='message id', pos=(0, 0, 0, 50), padding=(5, 5, 5, 5), align=uiconst.TOTOP)
        self.msgIdLabel = uicontrols.Label(parent=self.msgIdContainer, name='message id label', text='ID:', pos=(0, 0, 0, 0), align=uiconst.CENTERTOP)
        self.msgIdEdit = uicontrols.SinglelineEdit(parent=self.msgIdContainer, name='message id edit', pos=(0, 0, 0, 0), padding=(5, 25, 5, 10), align=uiconst.TOTOP, readonly=True)

    def ConstructMessageLabelContainer(self):
        self.msgLabelContainer = uiprimitives.Container(parent=self.messageContainerMain, name='right title', pos=(0, 0, 0, 50), padding=(5, 5, 5, 5), align=uiconst.TOTOP)
        self.msgLabelLabel = uicontrols.Label(parent=self.msgLabelContainer, name='label text label', text='Label:', pos=(0, 0, 0, 0), align=uiconst.CENTERTOP)
        self.msgLabelEdit = uicontrols.SinglelineEdit(parent=self.msgLabelContainer, name='label edit', pos=(0, 0, 0, 0), padding=(5, 25, 5, 10), align=uiconst.TOTOP, maxLength=self.maxLabelLength)

    def ConstructMessagePathContainer(self):
        self.msgPathContainer = uiprimitives.Container(parent=self.messageContainerMain, name='right path', pos=(0, 0, 0, 50), padding=(5, 5, 5, 5), align=uiconst.TOTOP)
        self.msgPathLabel = uicontrols.Label(parent=self.msgPathContainer, name='path text label', text='Path:', pos=(0, 0, 0, 0), align=uiconst.CENTERTOP)
        self.msgPathEdit = uicontrols.SinglelineEdit(parent=self.msgPathContainer, name='path edit', pos=(0, 0, 0, 0), padding=(5, 25, 5, 10), align=uiconst.TOTOP, readonly=True)

    def ConstructMessageDescriptionContainer(self):
        self.msgDescriptionContainer = uiprimitives.Container(parent=self.messageContainerMain, name='right description', pos=(0, 0, 0, 150), padding=(5, 5, 5, 5), align=uiconst.TOTOP)
        self.msgDescriptionLabel = uicontrols.Label(parent=self.msgDescriptionContainer, name='description text label', text='Description:', pos=(0, 0, 0, 0), align=uiconst.CENTERTOP)
        self.msgDescriptionEdit = uicls.EditPlainText(parent=self.msgDescriptionContainer, name='description edit', value='test', pos=(0, 0, 0, 0), padding=(5, 25, 5, 10), maxLength=self.maxTextLength)

    def ConstructMessageSubmitContainer(self):
        self.rightSubmit = uiprimitives.Container(parent=self.messageContainerMain, name='right submit', pos=(0, 0, 0, 10), padding=(5, 5, 5, 5), align=uiconst.TOBOTTOM)
        self.submitButton = uicontrols.Button(parent=self.rightSubmit, label='SUBMIT', align=uiconst.CENTER, func=self.Submit)

    def ConstructMessageTextContainer(self):
        self.msgTextContainer = uiprimitives.Container(parent=self.messageContainerMain, name='right text', pos=(0, 0, 0, 0), padding=(5, 5, 5, 5), align=uiconst.TOALL)
        self.msgTextLabel = uicontrols.Label(parent=self.msgTextContainer, name='message text label', text='Message:', pos=(0, 0, 0, 0), align=uiconst.CENTERTOP)
        self.msgTextEdit = uicls.EditPlainText(parent=self.msgTextContainer, name='text edit', pos=(0, 0, 0, 0), padding=(5, 25, 5, 10), maxLength=self.maxTextLength)

    def ConstructFormattingButtons(self):
        """
            Creates storage container and adds buttons into it for formatting text.
        """
        self.textFormatting = uiprimitives.Container(parent=self.messageContainerMain, name='text formatting', pos=(10, 5, 10, 15), align=uiconst.TOBOTTOM)
        self.addDateButton = uicontrols.Button(parent=self.textFormatting, label='Add Date', pos=(5, 5, 0, 0), align=uiconst.TOLEFT, func=self.AddDate)
        self.addTimeIntervalButton = uicontrols.Button(parent=self.textFormatting, label='Add TimeInterval', pos=(5, 5, 0, 0), align=uiconst.TOLEFT, func=self.AddTimeInterval)
        self.addNumericButton = uicontrols.Button(parent=self.textFormatting, label='Add Numeric', pos=(5, 5, 0, 0), align=uiconst.TOLEFT, func=self.AddNumeric)
        self.addLocationButton = uicontrols.Button(parent=self.textFormatting, label='Add Location', pos=(5, 5, 0, 0), align=uiconst.TOLEFT, func=self.AddLocation)
        self.addItemButton = uicontrols.Button(parent=self.textFormatting, label='Add Item', pos=(5, 5, 0, 0), align=uiconst.TOLEFT, func=self.AddItem)

    def ConstructRightContainerLines(self):
        uiprimitives.Line(parent=self.msgIdContainer, align=uiconst.TOBOTTOM)
        uiprimitives.Line(parent=self.msgLabelContainer, align=uiconst.TOBOTTOM)
        uiprimitives.Line(parent=self.msgPathContainer, align=uiconst.TOBOTTOM)
        uiprimitives.Line(parent=self.msgDescriptionContainer, align=uiconst.TOBOTTOM)

    def ShowMessageContainer(self):
        self.messageContainerMain.state = uiconst.UI_PICKCHILDREN

    def HideMessageContainer(self):
        self.messageContainerMain.state = uiconst.UI_HIDDEN

    def UpdateScroll(self, localizationData = None):
        if localizationData is None:
            localizationData = self.localizationHandler.GetScrollList()
        self.leftScroll.Load(contentList=localizationData)

    def Submit(self, *args):
        label = self.msgLabelEdit.GetValue()
        text = self.msgTextEdit.GetValue()
        context = self.msgDescriptionEdit.GetValue()
        if self.newMessage == True:
            newMessageID = self.groupForNewMessage.CreateNewMessage(self.groupForNewMessage, label, text, context)
        if self.newMessage == True and self.groupForNewMessage is not None:
            self.UpdateScroll()
            self.SelectMessageByID(newMessageID)
        else:
            self.selectedMessage.UpdateMessage(self.selectedMessage, label, text, context)
            self.UpdateScroll()

    def AddDate(self, *args):
        """
            Adds date formatting to text field.
        """
        self.AddFormatting('{[datetime]', ', date=medium, time=short}')

    def AddNumeric(self, *args):
        """
            Adds numeric formatting to text field.
        """
        self.AddFormatting('{[numeric]', ', decimalPlaces=0, leadingZeroes=0, useGrouping=False}')

    def AddTimeInterval(self, *args):
        """
            Adds time interval to text field.
        """
        self.AddFormatting('{[timeinterval]', 'from=hour, to=second}')

    def AddLocation(self, *args):
        """
            Adds time interval to text field.
        """
        self.AddFormatting('{[location]', '.name}')

    def AddItem(self, *args):
        """
            Adds item name to text field.
        """
        self.AddFormatting('{[item]', '.name}')

    def AddFormatting(self, text1, text2):
        """
            Takes in text string and inserts into text field.
            If text was selected it deletes it and applies it into the formatted text.
        """
        selectedText = self.msgTextEdit.GetSelectedText()
        self.msgTextEdit.DeleteSelected()
        text = text1 + selectedText + text2
        self.msgTextEdit.InsertText(text)

    def SelectMessage(self, messageEntry):
        self.ShowMessageContainer()
        self.newMessage = False
        messageNode = messageEntry.sr.node
        self.selectedMessage = messageNode
        message = messageNode.GetMessage(messageNode.messageID)
        self.msgIdEdit.SetValue(str(message.messageID))
        self.msgLabelEdit.SetValue(message.label)
        path = message.localizationPath.split('EVE/')[1]
        self.msgPathEdit.SetValue(path)
        self.msgDescriptionEdit.SetValue(message.context)
        self.msgTextEdit.SetValue(message.GetText('en-us'))

    def SetEmptyMessage(self):
        self.msgIdEdit.SetValue('')
        self.msgLabelEdit.SetValue('')
        self.msgDescriptionEdit.SetValue('')
        self.msgTextEdit.SetValue('')

    def CreateMessage(self, groupNode):
        self.ShowMessageContainer()
        self.SetEmptyMessage()
        self.newMessage = True
        self.groupForNewMessage = groupNode
        group = groupNode.GetGroup(groupNode.groupID)
        self.msgPathEdit.SetValue(group.localizationPath)

    def SelectMessageByID(self, newMessageID):
        for listEntry in self.leftScroll.GetNodes():
            if listEntry.type == 'message' and listEntry.messageID == newMessageID:
                self.SelectMessage(listEntry.panel)
                break

    def DeleteEntry(self, message):
        message.DeleteMessage(message)
        self.UpdateScroll()
        self.SetEmptyMessage()
        self.HideMessageContainer()

    def UpdateFromEdit(self, *args):
        """
        Updates the scroll based on text field and checkbox checks.
        """
        if len(self.searchEdit.text) < 3:
            self.UpdateScroll()
            return
        for radioButton in self.radioButtons:
            if radioButton.checked:
                searchList = radioButton.searchFunc(str(self.searchEdit.text))
                self.UpdateScroll(searchList)
                return
