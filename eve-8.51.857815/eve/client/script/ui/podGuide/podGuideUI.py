#Embedded file name: eve/client/script/ui/podGuide\podGuideUI.py
"""
    Temporary window for the podGuide
"""
import carbonui.const as uiconst
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.fill import Fill
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.sprite import Sprite
from localization import GetByLabel, GetByMessageID
from eve.client.script.ui.control.buttons import NavigationButtons
from eve.client.script.ui.control.eveEditPlainText import EditPlainText
from eve.client.script.ui.control.eveLabel import EveLabelMedium, EveCaptionMedium, EveCaptionLarge, EveLabelLargeBold
from eve.client.script.ui.control.eveWindow import Window
from carbonui.primitives.container import Container
from eve.client.script.ui.podGuide.podGuideUtil import GetTerms, GetTermByID, GetCategories
from eve.client.script.ui.control.historyBuffer import HistoryBuffer

class PodGuideWindow(Window):
    default_windowID = 'PodGuideWindow'
    default_iconNum = 'res:/UI/Texture/icons/38_16_224.png'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.SetWndIcon(fullPath='res:/UI/Texture/icons/38_16_224.png', mainTop=-8)
        self.sr.clippedIcon = Sprite(parent=self.sr.iconClipper, name='windowIcon', pos=(-22, -36, 150, 150), texturePath='res:/ui/Texture/WindowIcons/help.png', opacity=0.1)
        self.SetTopparentHeight(0)
        termID = attributes.termID
        self.history = HistoryBuffer()
        self.headerCont = Container(name='headerCont', parent=self.sr.main, align=uiconst.TOTOP, height=70)
        categories = GetCategories()
        self.podGuideNavigation = PodGuideNavigation(name='podGuideNavigation', parent=self.headerCont, align=uiconst.TOALL, categories=categories, callback=self.LoadPanelByID)
        self.CustomizeHeader()
        self.contentCont = ScrollContainer(name='contentCont', parent=self.sr.main, align=uiconst.TOALL, padding=4)
        self.SetupContentPanel()
        self.InitializeData()
        if termID:
            self.LoadPanelByID(termID)

    def CustomizeHeader(self):
        self.sr.headerParent.display = False
        self.sr.caption = EveCaptionMedium(text='Pod Guide', parent=self.podGuideNavigation, left=18, top=22, state=uiconst.UI_DISABLED)

    def SetWndIcon(self, *args, **kw):
        return (None, None)

    def SetupContentPanel(self):
        self.podGuideContent = PodGuideContent(parent=self.contentCont, align=uiconst.TOTOP)
        self.navigationButtons = NavigationButtons(parent=self.podGuideContent, left=0, top=0, align=uiconst.TOPRIGHT, buttonSize=19, idx=0, backBtnFunc=self.OnBackButtonCallback, forwardBtnFunc=self.OnForwardButtonCallback, padTop=8)
        self.UpdateHistoryButtons()

    def UpdateHistoryButtons(self):
        historyBuffer = self.history
        if historyBuffer.IsBackEnabled():
            self.navigationButtons.EnableBackBtn()
        else:
            self.navigationButtons.DisableBackBtn()
        if historyBuffer.IsForwardEnabled():
            self.navigationButtons.EnableForwardBtn()
        else:
            self.navigationButtons.DisableForwardBtn()

    def InitializeData(self):
        self.allInfo = GetTerms()

    def LoadPanelByID(self, termID, storeInHistory = True):
        termInfo = GetTermByID(termID)
        self.LoadPanel(termInfo)
        if storeInHistory:
            self.history.Append(termInfo.termID)
        self.UpdateHistoryButtons()

    def LoadPanel(self, termInfo):
        self.podGuideContent.LoadContent(termInfo)

    def OnBack(self):
        wasClicked = self.navigationButtons.OnBackBtnClicked()
        if wasClicked:
            self.navigationButtons.AnimateBackBtn()

    def OnBackButtonCallback(self):
        previousTermID = self.history.GoBack()
        if previousTermID:
            self.LoadPanelByID(previousTermID, storeInHistory=False)

    def OnForward(self):
        wasClicked = self.navigationButtons.OnForwardBtnClicked()
        if wasClicked:
            self.navigationButtons.AnimateForwardBtn()

    def OnForwardButtonCallback(self):
        nextTermID = self.history.GoForward()
        if nextTermID:
            self.LoadPanelByID(nextTermID, storeInHistory=False)

    def UpdateHistoryData(self, termInfo):
        self.history.UpdateCurrent(termInfo.termID)


class PodGuideNavigation(Container):
    clipChildren = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        Fill(bgParent=self, color=(1, 1, 1, 0.03))
        categories = attributes.categories
        self.callback = attributes.callback
        self.flowCont = FlowContainer(name='flowCont', parent=self, align=uiconst.TOBOTTOM, autoHeight=True, centerContent=True, contentSpacing=(10, 0))
        self.LoadCategories(categories)

    def LoadCategories(self, categories, *args):
        self.flowCont.Flush()
        tempAllTerms = GetTerms()
        for eachCategorID, eachCategoryInfo in categories.iteritems():
            catInfo = eachCategoryInfo['categoryInfo']
            categoryNameID = catInfo.groupName
            categoryName = GetByMessageID(categoryNameID)
            megaMenuOptions = []
            for eachSubGroup in eachCategoryInfo.get('subgroups', []):
                groupNameID = eachSubGroup.groupName
                groupName = GetByMessageID(groupNameID)
                termsInGroup = tempAllTerms.get(eachSubGroup.groupID, [])
                termsInfoList = []
                for eachTerm in termsInGroup:
                    termTitleID = eachTerm.termTitleID
                    termName = GetByMessageID(termTitleID)
                    termsInfoList.append({'text': termName,
                     'callback': self.callback,
                     'args': eachTerm.termID})

                megaMenuGroup = {'headerInfo': {'groupName': groupName},
                 'entryInfoList': termsInfoList}
                megaMenuOptions.append(megaMenuGroup)

            NavigationButtonInWindow(parent=self.flowCont, megaMenuOptions=megaMenuOptions, categoryInfo={'categoryName': categoryName})

    def Close(self, *args):
        Container.Close(self, *args)
        uicore.megaMenuManager.CloseMegaMenu()


class NavigationButtonBase(Container):
    default_align = uiconst.NOALIGN
    default_height = 20
    textPadding = 10
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.categoryInfo = attributes.categoryInfo
        text = self.categoryInfo['categoryName']
        textLabel = EveLabelLargeBold(parent=self, text=str(text), align=uiconst.CENTER)
        self.width = textLabel.textwidth + 2 * self.textPadding
        self.hiliteFill = Fill(bgParent=self, opacity=0.0)


class NavigationButtonInWindow(NavigationButtonBase):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        NavigationButtonBase.ApplyAttributes(self, attributes)
        self.megaMenuOptions = attributes.megaMenuOptions

    def OnMouseEnter(self, *args):
        uicore.megaMenuManager.CloseMegaMenu()
        al, at, ah, aw = self.GetAbsolute()
        uicore.megaMenuManager.ShowMegaMenu(options=self.megaMenuOptions, categoryInfo=self.categoryInfo, pos=(al,
         at,
         0,
         0), openingButtonClass=NavigationButtonBase)

    def OnMouseExit(self, *args):
        self.hiliteFill.opacity = 0.0
        currentMegaMenu = uicore.megaMenuManager.GetCurrentMegaMenu()
        isMouseOverMegaMenu = currentMegaMenu.IsMouseOverMenu()
        if not isMouseOverMegaMenu:
            uicore.megaMenuManager.CloseMegaMenu()


class PodGuideContent(Container):
    MIN_RIGHT_SIDE_WIDTH = 100

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        padding = 30
        self.termHeaderLabel = EveCaptionLarge(name='termHeaderLabel', parent=self, align=uiconst.TOTOP, text='', padLeft=padding + 4, padTop=20)
        self.contentRightCont = Container(name='contentRightCont', parent=self, align=uiconst.TORIGHT, width=128, padRight=36)
        self.height = 300
        self.longTextEdit = EditPlainText(name='longTextEdit', parent=self, align=uiconst.TOTOP, readonly=True, setvalue='abc', padding=(padding,
         0,
         padding,
         0))
        self.longTextEdit.sr.maincontainer.padding = 0
        self.longTextEdit.DisableScrolling()
        self.longTextEdit.EnableAutoSize()
        self.longTextEdit.OnContentSizeChanged = self.OnContentChanged
        self.longTextEdit.HideBackground()
        self.longTextEdit.RemoveActiveFrame()
        self.termSpriteCont = Container(name='termSpriteCont', parent=self.contentRightCont, pos=(0, 0, 128, 128), align=uiconst.TOTOP)
        self.termSprite = Sprite(name='termSprite', parent=self.termSpriteCont, pos=(0, 0, 128, 128), texturePath='res:/UI/Texture/Classes/ShipTree/groupIcons/frigate.png', align=uiconst.CENTER)
        self.loreTextLabel = EveLabelMedium(name='termNameLabel', text='', parent=self.contentRightCont, align=uiconst.TOTOP)

    def LoadContent(self, termInfo):
        self.termHeaderLabel.text = GetByMessageID(termInfo.termTitleID)
        self.loreTextLabel.text = '<i>%s</i>' % GetByMessageID(termInfo.loreTextID)
        self.LoadAndWaitForIconSizeChange(termInfo.texturePath)
        self.longTextEdit.SetValue('<font size=14>%s</font>' % GetByMessageID(termInfo.longTextID))

    def OnContentChanged(self, width, height, *args):
        self.height = self.termHeaderLabel.padTop + self.termHeaderLabel.textheight + max(height, self.termSprite.height + self.loreTextLabel.textheight)

    def LoadAndWaitForIconSizeChange(self, texturePath):
        self.termSprite.LoadTexture(texturePath)
        if not texturePath:
            return
        import blue
        counter = 0
        while self.termSprite.renderObject.texturePrimary.atlasTexture.width == 0 and counter < 20:
            counter += 1
            blue.synchro.Yield()

        atlasTexture = self.termSprite.renderObject.texturePrimary.atlasTexture
        self.termSprite.width = atlasTexture.width
        self.termSprite.height = atlasTexture.height
        self.termSpriteCont.height = atlasTexture.height
        self.contentRightCont.width = max(self.MIN_RIGHT_SIDE_WIDTH, atlasTexture.width)
