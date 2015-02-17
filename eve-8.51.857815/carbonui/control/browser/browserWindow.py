#Embedded file name: carbonui/control/browser\browserWindow.py
"""
This is the browser window. It contains a browser pane that is renders html code and handles
all communication to that pane. It has various features that are typical to browsing like
Bookmarks, history,back and forward button and so on.
"""
import uicls
import carbonui.const as uiconst
import uthread
import blue
import urlparse
import browserutil
import browser
import log
import cgi
import localization
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.control.menuLabel import MenuLabel
from carbonui.util.bunch import Bunch
from carbon.common.script.util.commonutils import StripTags
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.label import LabelOverride as Label
from carbonui.control.singlelineedit import SinglelineEditCoreOverride as SinglelineEdit
from carbonui.control.buttons import ButtonCoreOverride as Button
from carbonui.control.windowDropDownMenu import WindowDropDownMenuCoreOverride as WindowDropDownMenu
from carbonui.control.browser.browserSourceWindow import BrowserSourceWindowCoreOverride as BrowserSourceWindow
from carbonui.control.browser.browserHistoryWindow import BrowserHistoryWindowCoreOverride as BrowserHistoryWindow
from carbonui.control.browser.browserSettingsWindow import BrowserSettingsWindowCoreOverride as BrowserSettingsWindow
from carbonui.control.browser.browserEditBookMarksWindow import EditBookmarksWindowCoreOverride as EditBookmarksWindow
from carbonui.control.browser.websiteTrustManagementWindow import WebsiteTrustManagementWindowCoreOverride as WebsiteTrustManagementWindow

class BrowserWindowCore(Window):
    __guid__ = 'uicls.BrowserWindowCore'
    __notifyevents__ = ['OnTrustedSitesChange',
     'OnSessionChanged',
     'OnClientBrowserLockdownChange',
     'OnClientFlaggedListsChange',
     'OnEndChangeDevice',
     'OnBrowserShowStatusBarChange',
     'OnBrowserShowNavigationBarChange',
     'OnBrowserHistoryCleared']
    default_width = 600
    default_height = 600
    default_iconNum = 'res:/ui/Texture/WindowIcons/browser.png'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        initialUrl = attributes.initialUrl
        self.reloadingTrustedSites = False
        self.awaitingTitle = False
        self.nextTabID = 1
        self.currentTab = None
        self.browserHostManager = sm.GetService('browserHostManager').GetBrowserHost()
        self.tabs = []
        self.browserButtons = (('Back',
          self.HistoryBack,
          20,
          'back',
          'UI/Browser/Back'),
         ('Forward',
          self.HistoryForward,
          60,
          'next',
          'UI/Browser/Forward'),
         (None, None, None, None, None),
         ('Reload',
          self.ReloadPage,
          -40,
          'reload',
          'UI/Browser/Reload'),
         ('Stop',
          self.StopLoading,
          20,
          'stop',
          'UI/Browser/Stop'),
         (None, None, None, None, None),
         ('Home',
          self.GoHome,
          0,
          'home',
          'UI/Browser/Home'))
        self.MakeUnstackable()
        self.SetMinSize([260, 180])
        self.SetMaxSize([uicore.desktop.width, uicore.desktop.height])
        self.PrepareMenuBar()
        self.PrepareNavigationBar()
        self.PrepareNavigationButtons()
        self.PrepareTabBar()
        self.PrepareStatusBar()
        mainArea = self.GetMainArea()
        if not settings.user.ui.Get('browserShowNavBar', True):
            self.navigationBar.state = uiconst.UI_HIDDEN
        if not settings.user.ui.Get('browserShowStatusBar', True):
            self.statusBar.state = uiconst.UI_HIDDEN
        for name, GetMenu in [(localization.GetByLabel('UI/Browser/View'), lambda : [(localization.GetByLabel('UI/Browser/Reload'), self.ReloadPage, ()), (localization.GetByLabel('UI/Browser/ViewSource'), self.DocumentSource, ()), (localization.GetByLabel('UI/Browser/BrowserHistory/BrowserHistoryCaption'), self.OpenBrowserHistory, ())]), (localization.GetByLabel('UI/Browser/Bookmarks'), self.GetBookmarkMenu), (localization.GetByLabel('UI/Browser/Options'), lambda : [(localization.GetByLabel('UI/Browser/GeneralSettings'), self.EditGeneralSettings, ()), None, (localization.GetByLabel('UI/Browser/TrustedSites'), self.EditSites, ('trusted',))])]:
            opt = WindowDropDownMenu(name='menuoption', parent=self.menuBar)
            opt.Setup(name, GetMenu)

        self.crashNotifierContainer = Container(name='crashNotifierContainer', parent=mainArea, align=uiconst.CENTER, state=uiconst.UI_HIDDEN, width=240, height=80, idx=0)
        crashText = Label(text=localization.GetByLabel('UI/Browser/Crashed'), parent=self.crashNotifierContainer, width=220, left=10, top=10, fontsize=16, letterspace=1)
        Fill(parent=self.crashNotifierContainer, color=(0.0, 0.0, 0.0, 1.0))
        self.crashNotifierContainer.height = max(80, crashText.textheight + 20)
        bp = browser.BrowserPane(parent=mainArea, align=uiconst.TOALL, state=uiconst.UI_NORMAL, padLeft=const.defaultPadding + 6, padRight=const.defaultPadding + 6, padTop=6, padBottom=6)
        bp.Startup()
        self.browserPane = bp
        Fill(parent=mainArea, color=(0.0, 0.0, 0.0, 1.0), padLeft=const.defaultPadding, padRight=const.defaultPadding)
        self.OnClientFlaggedListsChange()
        browseToUrl = initialUrl
        if browseToUrl is None or browseToUrl == 'home':
            browseToUrl = str(settings.user.ui.Get('HomePage2', browserutil.DefaultHomepage()))
        self.AddTab(browseToUrl)

    def PrepareMenuBar(self):
        mainArea = self.GetMainArea()
        self.menuBar = Container(name='menuBar', parent=mainArea, align=uiconst.TOTOP, height=16, padBottom=2)
        Line(parent=self.menuBar, align=uiconst.TOBOTTOM)

    def PrepareTabBar(self):
        mainArea = self.GetMainArea()
        self.tabBar = Container(name='tabParent', parent=mainArea, align=uiconst.TOTOP, height=24)
        self.addTabBtn = Button(parent=self.tabBar, label=localization.uiutil.PrepareLocalizationSafeString('+'), align=uiconst.TOPRIGHT, fixedwidth=22, func=self.AddTabButton, alwaysLite=True, hint=localization.GetByLabel('UI/Browser/NewTab'), left=const.defaultPadding)

    def PrepareStatusBar(self):
        mainArea = self.GetMainArea()
        self.statusBar = Container(name='statusBar', parent=mainArea, align=uiconst.TOBOTTOM, height=22, clipChildren=1, idx=0)
        iconContainer = Container(name='trustIndicator', parent=self.statusBar, align=uiconst.TORIGHT, width=24, left=4)
        icon = Sprite(name='trustIndicatorIcon', parent=iconContainer, texturePath='res:/UI/Texture/classes/Browser/trustIndicatorIcon.png', pos=(0, -3, 24, 24), hint=localization.GetByLabel('UI/Browser/TrustedSite'), ignoreSize=True, state=uiconst.UI_DISABLED)
        self.trustIndicatorIcon = icon
        self.trustIndicatorIcon.state = uiconst.UI_HIDDEN
        iconContainer = Container(name='lockdownIndicator', parent=self.statusBar, align=uiconst.TOLEFT, width=28)
        Sprite(name='lockdownIndicatorIcon', parent=iconContainer, texturePath='res:/UI/Texture/classes/Browser/lockdownIndicatorIcon.png', pos=(2, -3, 24, 24), hint=localization.GetByLabel('UI/Browser/LockdownEnabled'), ignoreSize=True, state=uiconst.UI_NORMAL)
        self.lockdownIconContainer = iconContainer
        self.statusText = Label(text='', parent=self.statusBar, maxLines=1, state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT)

    def PrepareNavigationBar(self):
        mainArea = self.GetMainArea()
        self.navigationBar = Container(name='navBar', parent=mainArea, align=uiconst.TOTOP, height=24, padBottom=4)
        buttonParent = Container(name='buttonParent', parent=self.navigationBar, align=uiconst.TORIGHT, padRight=const.defaultPadding)
        goBtn = Button(parent=buttonParent, label=localization.GetByLabel('UI/Browser/Go'), func=self.OnGoBtn, align=uiconst.CENTER)
        buttonParent.width = goBtn.width
        iconContainer = Container(name='sslIndicator', parent=self.navigationBar, align=uiconst.TORIGHT, width=20, padRight=const.defaultPadding)
        Sprite(name='sslIcon', texturePath='res:/UI/Texture/classes/Browser/sslIcon.png', parent=iconContainer, pos=(-2, -1, 24, 24), hint=localization.GetByLabel('UI/Browser/SecureConnection'), ignoreSize=True, state=uiconst.UI_NORMAL)
        self.sslIconContainer = iconContainer
        self.urlInput = SinglelineEdit(name='urlInput', parent=self.navigationBar, padTop=1, padRight=const.defaultPadding, maxLength=1630, autoselect=True, align=uiconst.TOTOP)
        self.urlInput.OnReturn = self.BrowseTo
        self.urlInput.OnHistoryClick = self.OnHistoryClicked

    def PrepareNavigationButtons(self):
        buttonTop = Container(name='buttonTop', parent=self.navigationBar, padRight=const.defaultPadding, align=uiconst.TOLEFT, idx=0)
        for btnLabel, btnFunc, btnRectLeft, btnName, localizationLabel in self.browserButtons:
            if btnLabel is None:
                buttonTop.width += 6
                continue
            if localization.IsValidLabel(localizationLabel):
                thehint = localization.GetByLabel(localizationLabel)
            else:
                thehint = ''
            button = uicls.ImageButton(parent=buttonTop, name=btnLabel, width=20, height=20, align=uiconst.RELATIVE, top=2, left=buttonTop.width, idleIcon='res:/UI/Texture/classes/Browser/%sIdle.png' % btnName, mouseoverIcon='res:/UI/Texture/classes/Browser/%sMouseOver.png' % btnName, mousedownIcon='res:/UI/Texture/classes/Browser/%sIdle.png' % btnName, onclick=btnFunc, hint=thehint)
            button.flag = btnLabel
            setattr(self.sr, '%sButton' % btnLabel, button)
            buttonTop.width += 20

    def _OnClose(self, *args):
        sm.GetService('urlhistory').SaveHistory()
        ct = getattr(self, 'currentTab', None)
        if ct is not None:
            ct.Cleanup()
            ct = None
        if self.browserPane:
            self.browserPane.browserSession = None
            del self.browserPane
        if getattr(self, 'tabs', None):
            for tab in self.tabs[:]:
                tab.Cleanup()
                del tab

            self.tabs = []

    def PopulateWhitelistAndBlacklist(self):
        self.browserHostManager.ClearSiteList('Blacklist')
        self.browserHostManager.ClearSiteList('Whitelist')
        l = sm.GetService('sites').GetBrowserBlacklist()
        for url in l:
            self.browserHostManager.AddToSiteList('Blacklist', url)

        l = sm.GetService('sites').GetBrowserWhitelist()
        for url in l:
            self.browserHostManager.AddToSiteList('Whitelist', url)

    def OnClientFlaggedListsChange(self, *args):
        self.PopulateWhitelistAndBlacklist()
        self.browserHostManager.UpdateDynamicData()
        self.OnClientBrowserLockdownChange()
        self.OnTrustedSitesChange()

    def OnClientBrowserLockdownChange(self, *args):
        for tab in self.tabs:
            tab._OnClientBrowserLockdownChange(args)

        if sm.GetService('sites').IsBrowserInLockdown():
            self.lockdownIconContainer.state = uiconst.UI_PICKCHILDREN
            self.statusText.left = 0
        else:
            self.lockdownIconContainer.state = uiconst.UI_HIDDEN
            self.statusText.left = 6

    def OnEndChangeDevice(self, change, *args):
        """
            This method is called when the graphics device has finished applying a
            change in its settings - e.g. a change in graphics resolution
        """
        self.SetMaxSize([uicore.desktop.width, uicore.desktop.height])

    def OnBrowserShowStatusBarChange(self, *args):
        show = settings.user.ui.Get('browserShowStatusBar', True)
        self.DisplayStatusBar(show)

    def OnBrowserShowNavigationBarChange(self, *args):
        show = settings.user.ui.Get('browserShowNavBar', True)
        self.DisplayNavigationBar(show)

    def OnBrowserHistoryCleared(self, *args):
        if self and not self.destroyed:
            self.urlInput.ClearHistory()

    def AddToAllOtherSites(self, header, value):
        """
            For adding default headers to all sites visited through the IGB, except those
            on the trusted list. The "other" key must be kept in sync with the Awesomium
            implementation in WebViewProxy::WillSendRequest.
        """
        self.browserHostManager.SetHeader('other', header, unicode(value))

    def AddToAllTrustedSites(self, header, value):
        value = self.CleanHeaderValue(value)
        self.browserHostManager.SetHeader('CCP', header, unicode(value))
        self.browserHostManager.SetHeader('COMMUNITY', header, unicode(value))
        self.browserHostManager.SetHeader('trusted', header, unicode(value))

    def RemoveFromAllTrustedSites(self, header):
        self.browserHostManager.DelHeader('CCP', header)
        self.browserHostManager.DelHeader('COMMUNITY', header)
        self.browserHostManager.DelHeader('trusted', header)

    def AddToCCPTrustedSites(self, header, value):
        value = self.CleanHeaderValue(value)
        self.browserHostManager.SetHeader('CCP', header, unicode(value))
        self.browserHostManager.SetHeader('COMMUNITY', header, unicode(value))

    def CleanHeaderValue(self, value):
        if value and isinstance(value, basestring):
            value = localization.CleanImportantMarkup(value)
        return value

    def OnSessionChanged(self, isRemote, sess, change):
        """
            The browser must listen for changes to any of the values it has in its
            trusted header list. If any of those values change, it must erase the header value
            and reinject it into ccpBrowserHost.
        """
        pass

    def SetupTrustedSiteHeaders(self):
        self.browserHostManager.ClearSiteList('trusted')
        self.browserHostManager.ClearSiteList('CCP')
        self.browserHostManager.ClearSiteList('COMMUNITY')

        def SiteMatch(siteA, siteB):
            if not siteA or not siteB:
                return siteA == siteB
            if siteA.find('://') == -1:
                siteA = 'http://' + siteA
            if siteB.find('://') == -1:
                siteB = 'http://' + siteB
            parsedSiteA = urlparse.urlsplit(siteA)
            parsedSiteB = urlparse.urlsplit(siteB)
            return parsedSiteA[1] == parsedSiteB[1]

        trusted = sm.GetService('sites').GetTrustedSites()
        userTrustedSites = []
        autoTrustedSites = []
        communitySites = []
        for site, flags in trusted.iteritems():
            try:
                if flags.auto == 0:
                    userTrustedSites.append(str(site))
                elif flags.community == 0:
                    autoTrustedSites.append(str(site))
                else:
                    communitySites.append(str(site))
            except:
                log.LogException('Error loading trusted sites, flags = %s' % flags)

        for site in userTrustedSites:
            cnt = False
            for siteB in autoTrustedSites:
                if SiteMatch(site, siteB):
                    cnt = True
                    break

            if cnt:
                continue
            cnt = False
            for siteB in communitySites:
                if SiteMatch(site, siteB):
                    cnt = True
                    break

            if cnt:
                continue
            self.browserHostManager.AddToSiteList('trusted', site)

        for site in autoTrustedSites:
            if site.startswith('.'):
                site = '*%s' % site
            if site.endswith('/'):
                site += '*'
            self.browserHostManager.AddToSiteList('CCP', site)

        for site in communitySites:
            if site.startswith('.'):
                site = '*%s' % site
            if site.endswith('/'):
                site += '*'
            self.browserHostManager.AddToSiteList('COMMUNITY', site)

        self.AddTrustedHeaderData()
        self.browserHostManager.UpdateDynamicData()

    def AddTrustedHeaderData(self):
        """
            Override this to set custom headers and site lists for trusted sites
        """
        pass

    def _OnResize(self, *args):
        if self.GetState() != uiconst.RELATIVE:
            return
        if self.browserPane:
            self.browserPane.ResizeBrowser()

    def OnEndMaximize(self, *args):
        self.OnResizeUpdate()

    def GoHome(self, *args):
        if self.currentTab:
            self.currentTab.GoHome(*args)

    def BrowseTo(self, url = None, *args, **kwargs):
        if self.currentTab is None:
            return
        if url is None:
            url = self.urlInput.GetValue().encode('cp1252', 'ignore')
        if type(url) is not str:
            url = url.encode('cp1252', 'ignore')
        if url.find(':/') == -1 and url != 'about:blank':
            url = 'http://' + url
        self.browserPane.OnBrowseTo()
        self.currentTab.BrowseTo(url=url, *args)

    def OnHistoryClicked(self, historyString, *args, **kwargs):
        self.BrowseTo(historyString)

    def OnGoBtn(self, *args):
        url = None
        self.BrowseTo(url)

    def ReloadPage(self, *args):
        self.browserPane.OnBrowseTo()
        self.currentTab.ReloadPage(*args)

    def HistoryBack(self, *args):
        self.browserPane.OnBrowseTo()
        self.currentTab.HistoryBack(*args)

    def HistoryForward(self, *args):
        self.browserPane.OnBrowseTo()
        self.currentTab.HistoryForward(*args)

    def StopLoading(self, *args):
        self.currentTab.StopLoading(*args)

    def GetBookmarkMenu(self, startAt = 0):
        m = []
        if startAt < 1:
            m.append((MenuLabel('UI/Browser/AddRemove'), self.EditBookmarks))
        allMarks = sm.GetService('sites').GetBookmarks()
        myMarks = allMarks[startAt:startAt + 20]
        if len(myMarks) >= 20 and len(allMarks) > startAt + 20:
            m.append((MenuLabel('UI/Common/More'), ('isDynamic', self.GetBookmarkMenu, (startAt + 20,))))
        if len(m) > 0:
            m.append(None)
        for each in myMarks:
            if each is not None:
                if each.url.find(':/') == -1:
                    each.url = 'http://' + each.url
                m.append((each.name, self.BrowseTo, (each.url,)))

        return m

    def ViewSourceOfUrl(self, url):
        BrowserSourceWindow.Open(browseTo=url)

    def DocumentSource(self):
        url = self.currentTab.GetCurrentURL()
        self.ViewSourceOfUrl(url)

    def OpenBrowserHistory(self):
        if not self.destroyed:
            BrowserHistoryWindow.Open()

    def EditGeneralSettings(self):
        if not self.destroyed:
            wnd = BrowserSettingsWindow.Open()
            wnd.ShowModal()

    def EditBookmarks(self):
        if not self.destroyed:
            wnd = EditBookmarksWindow.Open(bookmarkName=self.sr.caption.text, url=self.urlInput.GetValue())
            wnd.ShowModal()

    def EditSites(self, what):
        inputUrl = ''
        if self.currentTab is not None:
            inputUrl = self.currentTab.GetCurrentURL()
        WebsiteTrustManagementWindow.Open(initialUrl=inputUrl)

    def DisplayNavigationBar(self, display):
        """
            Toggles the display of the navigation bar - nav buttons & url input field
            ARGUMENTS:
                display     Boolean. Displays input & go button if true, else hide.
            RETURNS:
                None
        """
        if display:
            self.navigationBar.state = uiconst.UI_NORMAL
        else:
            self.navigationBar.state = uiconst.UI_HIDDEN

    def DisplayStatusBar(self, display):
        """
            Toggles the display of the status bar.
            ARGUMENTS:
                display     Boolean. Displays status bar if true, else hide.
            RETURNS:
                None
        """
        if display:
            self.statusBar.state = uiconst.UI_NORMAL
        else:
            self.statusBar.state = uiconst.UI_HIDDEN

    def DisplayTrusted(self, display):
        """
            Sets whether the site is displayed as trusted or not.
            ARGUMENTS:
                display     Boolean. If true, makes text yellow & read "trusted".
                            Otherwise, text is white & reads "untrusted".
            RETURNS:
                None
        """
        if display:
            self.trustIndicatorIcon.state = uiconst.UI_NORMAL
        else:
            self.trustIndicatorIcon.state = uiconst.UI_HIDDEN

    def IsTrusted(self, url):
        """
            Calls the Sites service to query whether the input URL is trusted.
            ARGUMENTS:
                url     - A url to validate trust on.
            RETURNS:
                True if the url is trusted, false otherwise.
        """
        return sm.GetService('sites').IsTrusted(url)

    def OnTrustedSitesChange(self, *args):
        if self.reloadingTrustedSites:
            return
        try:
            self.reloadingTrustedSites = True
            self.SetupTrustedSiteHeaders()
        finally:
            self.reloadingTrustedSites = False

    def OnReattachBrowserSession(self, browserSession):
        self.SetupTrustedSiteHeaders()
        self.OnClientFlaggedListsChange()
        if browserSession == self.currentTab:
            self.crashNotifierContainer.state = uiconst.UI_HIDDEN
            self.browserPane.browserSession = browserSession
            browserSession.SetBrowserSurface(self.browserPane.GetSurface(), self.browserPane._OnSurfaceReady)
            self.browserPane.SetCursor(browserSession.cursorType)
            self.browserPane.ResizeBrowser()

    def _OnBrowserViewCrash(self, tabSession):
        if tabSession == self.currentTab:
            self.crashNotifierContainer.state = uiconst.UI_NORMAL

    def _OnBeginNavigation(self, tabSession, url, frameName):
        """
        This event is fired when a WebView begins navigating to a new URL.
        """
        tabSession.hint = ''
        if tabSession == self.currentTab:
            self.statusText.text = localization.GetByLabel('/Carbon/UI/Browser/BrowsingTo', url=url)
            self.ShowLoad(doBlock=False)
            self.browserPane.state = uiconst.UI_HIDDEN if self.currentTab.hidden else uiconst.UI_NORMAL

    def _OnBeginLoading(self, tabSession, url, frameName, status, mimeType):
        """
        This event is fired when a WebView begins to actually receive data from a server.
        """
        if frameName is None or frameName == '' or frameName == 'main':
            if tabSession == self.currentTab:
                self.urlInput.SetValue(url)
                if uicore.registry.GetFocus() is self.urlInput:
                    self.urlInput.SelectAll()
                self.DisplayTrusted(self.IsTrusted(url))

    def _OnProcessSecurityInfo(self, tabSession, securityInfo):
        if tabSession == self.currentTab:
            self.ProcessSecurityInfo(securityInfo)

    def _OnChangeCursor(self, tabSession, cursorType):
        if tabSession == self.currentTab:
            self.browserPane.SetCursor(cursorType)

    def ProcessSecurityInfo(self, securityInfo):
        """
        This function should be called to process the security string returned in the OnBeginLoading function.
        Currently, the browser only displays a notification if the main frame is secure. Future iterations 
        will have to show a notification for mixed content (possibly by making  securityInfo a list of values, 
        indicating each elements security), as well as fine-tuning how exactly we indicate a secure site is 
        being viewed.
        """
        try:
            secInfoInt = int(securityInfo)
        except:
            secInfoInt = 0

        if secInfoInt >= 80:
            self.sslIconContainer.state = uiconst.UI_NORMAL
        else:
            self.sslIconContainer.state = uiconst.UI_HIDDEN

    def _OnFinishLoading(self, tabSession):
        """
        This event is fired when all loads have finished for a WebView.
        """
        if tabSession == self.currentTab:
            self.statusText.text = tabSession.statusText
            self.SetCaption(tabSession.title)
            self.HideLoad()

    def _OnReceiveTitle(self, tabSession, title, frameName):
        """
        This event is fired when a page title is received.
        """
        if frameName is None or frameName == '' or frameName == 'main':
            if tabSession.logToHistory:
                uthread.new(self.AddToHistory, tabSession.GetCurrentURL(), tabSession.title, blue.os.GetWallclockTime())
                tabSession.logToHistory = False
            for tabObject in self.tabGroup.sr.tabs:
                if tabObject.sr.args == tabSession:
                    title = localization.uiutil.PrepareLocalizationSafeString(title)
                    tabObject.SetLabel(title, hint=title)
                    break

            if tabSession == self.currentTab:
                self.SetCaption(title)

    def SetCaption(self, caption):
        captionString = localization.uiutil.PrepareLocalizationSafeString(StripTags(caption)[:50])
        Window.SetCaption(self, captionString)

    def AddToHistory(self, url, title, ts):
        sm.GetService('urlhistory').AddToHistory(url, title, ts)
        w = BrowserHistoryWindow.GetIfOpen()
        if w:
            w.LoadHistory()

    def _OnChangeTooltip(self, tabSession, tooltip):
        """
        This event is fired when a tooltip has changed state.
        """
        self.browserPane.hint = tooltip

    def _OnChangeTargetURL(self, tabSession, url):
        """
        This event is fired when the target URL has changed. This is usually the result of 
        hovering over a link on the page.
        """
        if tabSession == self.currentTab:
            self.statusText.text = url

    def _OnJavascriptPrompt(self, tabSession, messageText):
        """
        This event is fired when a javascript prompt is invoked.
        """
        uthread.new(self._ShowAlert, messageText)

    def _ShowAlert(self, messageText):
        escapedText = cgi.escape(unicode(messageText))
        sm.GetService('gameui').MessageBox(str(escapedText), title=localization.GetByLabel('UI/Browser/JavaScriptAlert'), buttons=uiconst.OK, modal=True)

    def SetBrowserFocus(self):
        uicore.registry.SetFocus(self.browserPane)

    def AddTab(self, tabUrl = None):
        """
            Create a new tab, optionally browsing to a given URL.
            
            ARGUMENTS:
                tabUrl      A URL to browse to. If None or blank, the tab will just be blank.
                
            RETURNS:
                None
        """
        newTab = browser.BrowserSession()
        newTab.Startup('%s_%d' % (self.name, self.nextTabID), initialUrl=tabUrl, browserEventHandler=self)
        self.nextTabID += 1
        urlToBrowseTo = newTab.GetCurrentURL()
        newTab.BrowseTo(urlToBrowseTo)
        self.tabs.append(newTab)
        self.ReloadTabs(selectTab=-1)

    def AddTabButton(self, *args):
        self.AddTab()

    def CloseTab(self, tabID):
        """
            Close a given tab, denoted by a unique tab name.
            
            ARGUMENTS:
                tabID       A string containing the unique tab name of the tab to be closed.
        
            RETURNS:
                None
        """
        if len(self.tabs) < 2:
            return
        dyingTab = None
        selectTab = -1
        for i in xrange(len(self.tabs)):
            if self.tabs[i].name == tabID:
                if self.tabs[i].name == self.currentTab.name:
                    nextIdx = i if i < len(self.tabs) - 1 else i - 1
                    selectTab = nextIdx
                dyingTab = self.tabs.pop(i)
                dyingTab.Cleanup()
                break

        self.ReloadTabs(selectTab=selectTab)

    def CloseTabButton(self, *args):
        if self.currentTab is not None:
            self.CloseTab(self.currentTab.name)

    def ReloadTabs(self, selectTab = None):
        """
            Reloads the tab list. This is necessary because the TabGroup object does not
            support dynamic addition/removal of tabs.
        
            If this is the first time that tabs are being created, it will autoselect
            the first tab in the tabgroup.
        
            ARGUMENTS:
                selectTab       An integer representing the index of the tab to be
                                selected in the self.tabs list.
                                Defaults to None. If None, it will not change the
                                tab selection.
            RETURNS:
                None
        """
        if not self.tabs or len(self.tabs) < 1:
            return
        tabs = []
        for tab in self.tabs:
            tabData = Bunch()
            tabData.label = tab.title
            tabData.hint = tab.title
            tabData.code = self
            tabData.args = tab
            tabData.panel = None
            tabs.append(tabData)

        if getattr(self, 'tabGroup', None):
            tabGroup = self.tabGroup
        else:
            import uicontrols
            tabGroup = uicontrols.TabGroup(name='tabparent', parent=self.tabBar, minTabsize=50, maxTabsize=200, tabMenuMargin=8, align=uiconst.TOBOTTOM)
            self.tabGroup = tabGroup
        tabGroup.LoadTabs(tabs, autoselecttab=0)
        if self.currentTab is None:
            self.currentTab = self.tabs[0]
        else:
            self.currentTab.SetBrowserSurface(None, None)
            if selectTab is not None:
                self.currentTab = self.tabs[selectTab]
        tabGroup.ShowPanelByName(self.currentTab.title)

    def GetTabMenu(self, uiTab, *args):
        """
            Simple method that returns a list of menu options when a user right-clicks
            on one of our tabs.
        """
        tabSession = uiTab.sr.args
        ops = [(localization.GetByLabel('UI/Browser/NewTab'), self.AddTab, [])]
        if len(self.tabs) > 1:
            ops.append((localization.GetByLabel('UI/Browser/CloseTab'), self.CloseTab, (tabSession.name,)))
        return ops

    def LoadTabPanel(self, tabBrowserSession, container, tabgroup):
        """
            This is called by the TabGroup object when a tab is selected and brought to the
            foreground.
            We hijack this event and use it to restore UI text and displays to their
            appropriate state for viewing this tab.
        """
        if self.currentTab is not None:
            self.currentTab.SetBrowserSurface(None, None)
        self.statusText.text = tabBrowserSession.statusText
        self.urlInput.SetValue(tabBrowserSession.GetCurrentURL())
        self.ProcessSecurityInfo(tabBrowserSession.securityInfo)
        self.SetCaption(tabBrowserSession.title)
        if tabBrowserSession.loading:
            self.ShowLoad(doBlock=False)
        else:
            self.HideLoad()
        self.DisplayTrusted(self.IsTrusted(tabBrowserSession.GetCurrentURL()))
        self.currentTab = tabBrowserSession
        self.browserPane.browserSession = tabBrowserSession
        tabBrowserSession.SetBrowserSurface(self.browserPane.GetSurface(), self.browserPane._OnSurfaceReady)
        self.browserPane.SetCursor(self.currentTab.cursorType)
        self.browserPane.ResizeBrowser()
        self.browserPane.state = uiconst.UI_HIDDEN if self.currentTab.hidden else uiconst.UI_NORMAL
        if self.currentTab.IsAlive():
            self.crashNotifierContainer.state = uiconst.UI_HIDDEN
        else:
            self.crashNotifierContainer.state = uiconst.UI_NORMAL
