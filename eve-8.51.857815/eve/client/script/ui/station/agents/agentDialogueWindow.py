#Embedded file name: eve/client/script/ui/station/agents\agentDialogueWindow.py
import blue
from carbonui.primitives.flowcontainer import FlowContainer
from eve.client.script.ui.control.buttons import Button
import localization
import types
import uiprimitives
import uicontrols
import uix
import uicls
import carbonui.const as uiconst
import telemetry

class AgentDialogueWindow(uicontrols.Window):
    __guid__ = 'form.AgentDialogueWindow'
    __notifyevents__ = ['OnSessionChanged', 'OnAgentMissionChange']
    default_width = 835
    default_height = 545
    default_windowID = 'AgentDialogueWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/agent.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.htmlCache = {}
        self.buttonCache = []
        self.viewMode = None
        self.mainContainerHeight = 525
        self.mainContainerWidth = 825
        self.windowHeight = self.mainContainerHeight + 20
        self.windowWidth = self.mainContainerWidth + 10
        self.paneHeight = self.mainContainerHeight
        self.paneWidth = self.mainContainerWidth / 2 + 8
        self.rightPaneBottomHeight = 26
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.sr.agentID = None
        self.sr.agentMoniker = None
        agentID = attributes.agentID
        if agentID is not None:
            self.SetAgentID(agentID)

    def InitializeBrowsers(self):
        self.sr.briefingBrowser = uicontrols.Edit(parent=self.sr.leftPane, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), readonly=1)
        self.sr.briefingBrowser.sr.window = self
        self.sr.objectiveBrowser = uicontrols.Edit(parent=self.sr.rightPaneTop, readonly=1, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.objectiveBrowser.sr.window = self

    def SetAgentID(self, agentID):
        agentInfo = sm.GetService('agents').GetAgentByID(agentID)
        self.SetCaption(localization.GetByLabel('UI/Agents/Dialogue/AgentConversationWith', agentID=agentID))
        self.sr.agentID = agentID
        self.sr.agentMoniker = sm.GetService('agents').GetAgentMoniker(agentID)

    def OnSessionChanged(self, isRemote, sess, change):
        if not self.destroyed:
            self.sr.briefingBrowser.SessionChanged()
            self.sr.objectiveBrowser.SessionChanged()
        if 'stationid' in change:
            sm.StartService('agents').InteractWith(self.sr.agentID, maximize=False)
            self.RefreshBrowsers()

    def OnAgentMissionChange(self, action, agentID, tutorialID = None):
        """
        If you complete a dungeon, and you still have the agent dialogue window open for
        the agent who gave you that mission, make it auto-pop the same way the mission
        details journal does.
        """
        if not self.destroyed:
            if action == const.agentMissionModified and self.sr.agentID == agentID:
                sm.StartService('agents').InteractWith(self.sr.agentID)
                self.RefreshBrowsers()

    def DefineButtons(self, buttons, okLabel = None, okFunc = 'default', args = 'self', cancelLabel = None, cancelFunc = 'default', okModalResult = 'default', default = None):
        if okLabel is None:
            okLabel = localization.GetByLabel('UI/Generic/OK')
        if cancelLabel is None:
            cancelLabel = localization.GetByLabel('UI/Generic/Cancel')
        if okModalResult == 'default':
            okModalResult = uiconst.ID_OK
        if okFunc == 'default':
            okFunc = self.ConfirmFunction
        if cancelFunc == 'default':
            cancelFunc = self.ButtonResult
        if buttons == uiconst.OK:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0]]
        elif buttons == uiconst.OKCANCEL:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0], [cancelLabel,
              cancelFunc,
              args,
              None,
              uiconst.ID_CANCEL,
              0,
              1]]
        elif buttons == uiconst.OKCLOSE:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0], [localization.GetByLabel('UI/Common/Buttons/Close'),
              self.CloseByUser,
              args,
              None,
              uiconst.ID_CLOSE,
              0,
              1]]
        elif buttons == uiconst.YESNO:
            btns = [[localization.GetByLabel('UI/Common/Buttons/Yes'),
              self.ButtonResult,
              args,
              None,
              uiconst.ID_YES,
              1,
              0], [localization.GetByLabel('UI/Common/Buttons/No'),
              self.ButtonResult,
              args,
              None,
              uiconst.ID_NO,
              0,
              0]]
        elif buttons == uiconst.YESNOCANCEL:
            btns = [[localization.GetByLabel('UI/Common/Buttons/Yes'),
              self.ButtonResult,
              args,
              None,
              uiconst.ID_YES,
              1,
              0], [localization.GetByLabel('UI/Common/Buttons/No'),
              self.ButtonResult,
              args,
              None,
              uiconst.ID_NO,
              0,
              0], [cancelLabel,
              cancelFunc,
              args,
              None,
              uiconst.ID_CANCEL,
              0,
              1]]
        elif buttons == uiconst.CLOSE:
            btns = [[localization.GetByLabel('UI/Common/Buttons/Close'),
              self.CloseByUser,
              args,
              None,
              uiconst.ID_CANCEL,
              0,
              1]]
        elif type(okLabel) == types.ListType or type(okLabel) == types.TupleType:
            btns = []
            for index in xrange(len(okLabel)):
                label = okLabel[index]
                additionalArguments = {'Function': okFunc,
                 'Arguments': args,
                 'Cancel Label': cancelLabel,
                 'Cancel Function': cancelFunc,
                 'Modal Result': okModalResult,
                 'Default': default}
                for argName in additionalArguments:
                    if type(additionalArguments[argName]) in (types.ListType, types.TupleType) and len(additionalArguments[argName]) > index:
                        additionalArguments[argName] = additionalArguments[argName][index]

                cancel = additionalArguments['Modal Result'] == uiconst.ID_CANCEL
                btns.append([label,
                 additionalArguments['Function'],
                 additionalArguments['Arguments'],
                 None,
                 additionalArguments['Modal Result'],
                 additionalArguments['Default'],
                 cancel])

        else:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0]]
        if default is not None:
            for each in btns:
                each[5] = each[4] == default

        self.buttonCache = btns

    def _InsertButtons(self, buttons, where):
        for btnData in buttons:
            self.AddButton(*btnData)

        self.sr.rightPaneBottom.state = uiconst.UI_PICKCHILDREN

    def AddButton(self, label, func, args = None, fixedWidth = None, isModalResult = False, isDefault = False, isCancel = False, hint = None):
        Button(parent=self.sr.rightPaneBottom, align=uiconst.NOALIGN, label=label, func=func, args=args, btn_modalresult=isModalResult, btn_default=isDefault, btn_cancel=isCancel, name='%s_Btn' % label, hint=hint)

    def GetButtonByLabel(self, buttonLabel):
        for each in self.sr.rightPaneBottom.children:
            if each.name == '%s_Btn' % buttonLabel:
                return each

    def DisableButton(self, buttonName):
        button = self.GetButtonByLabel(buttonName)
        if button:
            button.Disable()

    def DisableButtons(self):
        for buttonName in [ button[0] for button in self.buttonCache ]:
            self.DisableButton(buttonName)

    def EnableButton(self, buttonName):
        button = self.GetButtonByLabel(buttonName)
        if button:
            button.Enable()

    def SetHTML(self, html, where):
        self.htmlCache[where] = html

    @telemetry.ZONE_METHOD
    def LoadHTML(self, html, where = 'briefingBrowser', hideBackground = 0, newThread = 1):
        if self.destroyed:
            return
        if not self.viewMode and where == 'objectiveBrowser':
            self.SetDoublePaneView()
        elif not self.viewMode:
            self.SetSinglePaneView()
        targetContainer = self.sr.Get(where, None)
        if not targetContainer:
            return
        self.ShowLoad()
        self.htmlCache[where] = html
        targetContainer.sr.hideBackground = hideBackground
        targetContainer.sr.scrollcontrols.state = uiconst.UI_DISABLED
        while targetContainer.IsLoading():
            blue.pyos.synchro.Yield()

        targetContainer.LoadHTML(html, newThread=newThread)

    @telemetry.ZONE_METHOD
    def SetSinglePaneView(self, briefingHtml = None):
        if self.viewMode == 'SinglePaneView':
            if briefingHtml:
                self.LoadHTML(briefingHtml, 'briefingBrowser')
            if self.buttonCache:
                uix.Flush(self.sr.rightPaneBottom)
                self._InsertButtons(self.buttonCache, self.sr.rightPaneBottom)
            return
        if briefingHtml:
            self.SetHTML(briefingHtml, 'briefingBrowser')
        uix.Flush(self.sr.main)
        self.sr.rightPaneBottom = FlowContainer(name='rightPaneBottom', parent=self.sr.main, align=uiconst.TOBOTTOM, contentSpacing=uiconst.BUTTONGROUPMARGIN, centerContent=True, padding=(6, 0, 6, 6))
        self.sr.leftPane = uiprimitives.Container(name='leftPane', parent=self.sr.main, align=uiconst.TOLEFT, height=self.paneHeight, width=self.paneWidth, left=0, top=0)
        self.sr.rightPaneTop = uiprimitives.Container(name='rightPaneTop', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.rightPaneTop.state = uiconst.UI_HIDDEN
        self.SetMinSize([self.mainContainerWidth / 2 + 10, self.windowHeight])
        self.LockWidth(self.mainContainerWidth / 2 + 10)
        self.viewMode = 'SinglePaneView'
        if self.buttonCache:
            self._InsertButtons(self.buttonCache, self.sr.rightPaneBottom)
        self.InitializeBrowsers()
        if 'briefingBrowser' in self.htmlCache:
            self.LoadHTML(self.htmlCache['briefingBrowser'], 'briefingBrowser')

    @telemetry.ZONE_METHOD
    def SetDoublePaneView(self, briefingHtml = None, objectiveHtml = None):
        if self.viewMode == 'DoublePaneView':
            if briefingHtml:
                self.LoadHTML(briefingHtml, 'briefingBrowser')
            if objectiveHtml:
                self.LoadHTML(objectiveHtml, 'objectiveBrowser')
            if self.buttonCache:
                uix.Flush(self.sr.rightPaneBottom)
                self._InsertButtons(self.buttonCache, self.sr.rightPaneBottom)
            return
        if briefingHtml:
            self.SetHTML(briefingHtml, 'briefingBrowser')
        if objectiveHtml:
            self.SetHTML(objectiveHtml, 'objectiveBrowser')
        uix.Flush(self.sr.main)
        self.sr.leftPane = uiprimitives.Container(name='leftPane', parent=self.sr.main, align=uiconst.TOLEFT, height=self.paneHeight, width=self.paneWidth, left=0, top=0)
        uiprimitives.Container(name='bottomBorder', parent=self.sr.leftPane, align=uiconst.TOBOTTOM, height=1)
        self.sr.rightPane = uiprimitives.Container(name='rightPane', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        uiprimitives.Line(parent=self.sr.rightPane, align=uiconst.TOLEFT)
        self.sr.rightPaneBottom = FlowContainer(name='rightPaneBottom', parent=self.sr.rightPane, align=uiconst.TOBOTTOM, contentSpacing=uiconst.BUTTONGROUPMARGIN, centerContent=True, padding=(6, 0, 6, 6))
        self.sr.rightPaneTop = uiprimitives.Container(name='rightPaneTop', parent=self.sr.rightPane, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.SetMinSize([self.windowWidth, self.windowHeight])
        self.LockWidth(self.windowWidth)
        self.viewMode = 'DoublePaneView'
        if self.buttonCache:
            self._InsertButtons(self.buttonCache, self.sr.rightPaneBottom)
        self.InitializeBrowsers()
        for browserName in self.htmlCache:
            self.LoadHTML(self.htmlCache[browserName], browserName)

    def RefreshBrowsers(self):
        """
        Update positions of the browser scrolls.
        """
        self.sr.briefingBrowser.UpdatePosition(fromWhere='AgentDialogueWindow.RefreshBrowsers')
        self.sr.objectiveBrowser.UpdatePosition(fromWhere='AgentDialogueWindow.RefreshBrowsers')

    def OnUIRefresh(self):
        pass
