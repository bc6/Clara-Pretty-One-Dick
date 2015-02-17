#Embedded file name: carbonui/control/browser\browserSession.py
"""
This is a backend object that is used to manage a single logical browser session.
It has no UI associated with it whatsoever - it must, instead, be attached to
of a BrowserPane object, where it will be associated with a surface when
it is visible.
"""
import corebrowserutil
import blue
import carbonui.const as uiconst
import localization

class CoreBrowserSession():

    def Startup(self, sessionName, initialUrl = None, browserEventHandler = None, autoHandleLockdown = True, *args):
        """
            sessionName:        A unique string ID for this BrowserSession.
                                Primarily used for tabbing.
        
            browserEventHandler:
                An object that can handle a number of browser-event callbacks sourced from
                Awesomium/Chromium. These are items that include page-begin-loading,
                loading-complete, etc.
        
            Note! You must also call SetBrowserSurfaceManager with a valid argument before
            a browserPane will be functional!
        """
        self.name = sessionName
        self.statusText = ''
        self.securityInfo = 0
        self.awaitingTitle = True
        self.loading = False
        self.logToHistory = False
        self.cursorType = 0
        self.isViewSourceMode = False
        self.hint = ''
        self.surfaceDirty = False
        self.currentUrl = initialUrl
        if self.currentUrl is None:
            self.currentUrl = 'about:blank'
        self.hidden = self.currentUrl == 'about:blank'
        self.browserEventHandler = browserEventHandler
        self.autoHandleLockdown = autoHandleLockdown
        self.AppStartup(sessionName, initialUrl, browserEventHandler, autoHandleLockdown)
        self.SetupBrowserSession(autoHandleLockdown=autoHandleLockdown)
        stat = blue.statistics.Find('browser/numRequests')
        if stat is None:
            stat = blue.CcpStatisticsEntry()
            stat.name = 'browser/numRequests'
            stat.resetPerFrame = False
            stat.type = 1
            blue.statistics.Register(stat)
        self.numRequestsStat = stat

    def SetupBrowserSession(self, autoHandleLockdown = True):
        """
            Things that need to be called for a new browser session or a revived browser session
        """
        self.browserHostManager = sm.GetService('browserHostManager').GetBrowserHost()
        self.browser = sm.GetService('browserHostManager').GetNewBrowserView()
        self.AttachBrowserCallbacks()
        if autoHandleLockdown:
            self.SetBrowserLockdown(sm.GetService('sites').IsBrowserInLockdown())
        self.AppSetupBrowserSession()

    def Cleanup(self):
        self.browserEventHandler = None
        self.browserHostManager = None
        if self.browser is not None:
            self.browser.OnChangeTargetURL = None
            self.browser.OnReceiveTitle = None
            self.browser.OnBeginNavigation = None
            self.browser.OnFinishLoading = None
            self.browser.OnBlockLoading = None
            self.browser.OnChangeCursor = None
            self.browser.OnBeginLoading = None
            self.browser.OnProcessSecurityInfo = None
            self.browser.OnChangeTooltip = None
            self.browser.OnChangeKeyboardFocus = None
            self.browser.OnJavascriptPrompt = None
            self.browser.OnOpenContextMenu = None
            self.browser.OnBrowserViewCrash = None
        sm.GetService('browserHostManager').ReleaseBrowserView(self.browser)
        self.browser = None
        self.surface = None
        self.surfaceDirty = False
        self.surfaceReadyCallback = None
        self.AppCleanup()

    def _OnClientBrowserLockdownChange(self, *args):
        self.SetBrowserLockdown(sm.GetService('sites').IsBrowserInLockdown())

    def BrowseTo(self, url = None, *args, **kwargs):
        """
            This method is used to browse to a given site; this is most often used in 
            response to user input, such as clicking a "home" button or typing something
            into a navigation input bar.
            
            If the browserSession is connected to a dead browserViewHost (e.g. in the 
            case that ccpBrowser.exe has crashed), then calling this method will 
            automatically attempt to spawn a fresh ccpBrowser.exe process and create a
            fresh browserViewHost.
            
            ARGUMENTS:
                url     A string. The URL to which the browserSession will initially navigate. 
                        If None, defaults to "about:blank", an auto-generated placeholder page.
        
            RETURNS:
                None
        """
        actualUrl = url
        if actualUrl is None:
            actualUrl = 'about:blank'
        if not self.IsAlive():
            self.ReattachBrowserSession()
        if type(actualUrl) is not str:
            actualUrl = actualUrl.encode('cp1252', 'ignore')
        self.browser.BrowseTo(actualUrl)

    def SetViewSourceMode(self, mode):
        """
            This method toggles Chromium's source-mode browsing feature. If set to True,
            then all further webpages visited will be rendered as colorized source text
            instead of a parsed web page. 
            
            ARGUMENTS
                mode    If true, View Source mode will be on. Off otherwise.
        """
        self.isViewSourceMode = mode
        self.browser.SetViewSourceMode(mode)

    def HistoryBack(self, *args):
        """
            This method instructs the browserViewHost to navigate one page back in its
            internal browsing history. Should there be no pages farther backward in the
            history, then this operation does nothing.
        """
        if not self.IsAlive():
            self.ReattachBrowserSession()
        self.browser.HistoryOffset(-1)

    def HistoryForward(self, *args):
        """
            This method instructs the browserViewHost to navigate one page forward in its
            internal browsing history. Should there be no pages farther forward in the
            history, then this operation does nothing.
        """
        if not self.IsAlive():
            self.ReattachBrowserSession()
        self.browser.HistoryOffset(1)

    def ReloadPage(self, *args):
        """
          This method is a simple wrapper for BrowseTo; it retrieves the current URL
          known to the browserSession and calls BrowseTo with that URL.
        
          NOTE: This does not work with HTTP POST calls.
        
          TODO: We may want to just put a smarter Reload() function into awesomium.
        """
        if self.currentUrl:
            if not self.IsAlive():
                self.ReattachBrowserSession()
        self.browser.BrowseTo(self.currentUrl)

    def StopLoading(self, *args):
        """
            This method orders the attached browserViewHost to halt any loading operations
            it is currently engaged in; this will stop the loading of pages, frames, 
            images and all other content that is either not yet loaded or in the process of loading. 
        """
        self.browser.Stop()

    def GoHome(self, *args):
        """
            This method is a simple wrapper for BrowseTo; it retrieves the user's homepage
            from the settings cache (via the override method AppGetHomepage) and calls
            BrowseTo with that URL.
        """
        url = self.AppGetHomepage()
        self.BrowseTo(url)

    def GetCurrentURL(self):
        return self.currentUrl

    def OnSetFocus(self, *args):
        if self.browser and self.browser.alive:
            self.browser.Focus()

    def OnKillFocus(self, *args):
        if self.browser and self.browser.alive:
            self.browser.Unfocus()

    def _OnBeginNavigation(self, url, frameName):
        """
            This callback is invoked when a browserView begins navigating to a new URL; 
            it is not triggered on redirects, but it is triggered when individual frames
            are loaded. This method is invoked prior to any HTTP request is made to 
            the remote web server. 
            
            ARGUMENTS
                url             The URL which the browserView has begun loading.
        
                framename       The name of the frame which the browserView has begun
                                loading from; the top-level "main" frame can be denoted
                                as None, an empty string or the string "main".
        """
        if frameName == '_blank':
            if self.browserEventHandler and hasattr(self.browserEventHandler, 'AddTab'):
                self.browserEventHandler.AddTab(tabUrl=url)
                return
        self.statusText = localization.GetByLabel('/Carbon/UI/Browser/BrowsingTo', url=url)
        self.loading = True
        self.numRequestsStat.Inc()
        if not frameName or frameName == 'main':
            self.awaitingTitle = True
            self.hidden = url == 'about:blank'
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnBeginNavigation'):
            self.browserEventHandler._OnBeginNavigation(self, url, frameName)

    def _OnBeginLoading(self, url, frameName, status, mimeType):
        """
            This callback is invoked when a browserView object begins to receive data
            from the remote web server. 
        
            ARGUMENTS
                url         The URL which the browserView has begun loading from; this may
                            be different from the URL received in _OnBeginNavigation if 
                            there was a server-side redirect in effect.
                            
                framename   The name of the frame which the browserView has begun receiving
                            data for; the top-level "main" frame can be denoted as None,
                            an empty string or the string "main".
        
                status      The HTTP status code associated with this request. In most 
                            cases this will be 200 (OK); a full list of HTTP status 
                            codes can be found in the HTTP RFC, RFC 2616, Section 10.
        
                mimeType    A string containing the MIME type of the incoming data.
        """
        if not frameName or frameName == 'main':
            self.currentUrl = url
            if status > 0:
                self.logToHistory = True
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnBeginLoading'):
            self.browserEventHandler._OnBeginLoading(self, url, frameName, status, mimeType)

    def _OnProcessSecurityInfo(self, securityInfo):
        """
            This callback is invoked when the browserView object receives security
            information from Chromium; this generally happens while a page is loading.
            
            The security information is an integer indicating the strength of the
            encryption used to encrypt the page being loaded; most modern web browsers
            consider 80-bit encryption to be the minimum required for deeming a site "secure".
            Completely unsecured sites may either pass None or 0 as their security information.
            
            ARGUMENTS
                securityInfo    An integer indicating the strength of the encryption used 
                                to transmit this webpage.
        """
        self.securityInfo = securityInfo
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnProcessSecurityInfo'):
            self.browserEventHandler._OnProcessSecurityInfo(self, securityInfo)

    def _OnFinishLoading(self):
        """
            This event is fired when all loads have finished for a WebView.
        """
        self.statusText = localization.GetByLabel('UI/Browser/FinishedLoading')
        self.loading = False
        if self.awaitingTitle:
            self._OnReceiveTitle(localization.GetByLabel('UI/Browser/UntitledPage'), '')
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnFinishLoading'):
            self.browserEventHandler._OnFinishLoading(self)

    def _OnBlockLoading(self, statusCode):
        """
            This callback is invoked when a webpage has stopped loading for an unusual
            reason; these reasons can include user intervention (e.g. calling StopLoading)
            or automatic intervention (e.g. the site was on a blacklist).
        
            This method, instead of forwarding a callback up to the browserEventManager,
            instead invokes the apphack override method AppOnBlockLoading.
        
            ARGUMENTS
                statusCode      An integer status code. A list of status codes can be
                                found in CoreBrowserUtil, under LoadErrors.
        """
        if statusCode == corebrowserutil.LoadErrors.ABORTED:
            return
        if statusCode == corebrowserutil.LoadErrors.BLACKLIST:
            self.AppOnBlockBlacklistSite()
            return
        if statusCode == corebrowserutil.LoadErrors.WHITELIST:
            self.AppOnBlockNonWhitelistSite()
            return
        self.AppOnBlockLoading(statusCode)

    def _OnReceiveTitle(self, title, frameName):
        """
            This callback is invoked when Chromium has read a TITLE tag from a web 
            page's HTML. It will not be invoked if the page has no TITLE tag.
            
            ARGUMENTS
                title       A string indicating the title of the incoming webpage.
        
                frameName   The name of the frame which the browserView has received a 
                            title for; the top-level "main" frame can be denoted as 
                            None, an empty string or the string "main".
        """
        if frameName == '' or frameName == 'main':
            self.title = title
            self.awaitingTitle = False
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnReceiveTitle'):
            self.browserEventHandler._OnReceiveTitle(self, title, frameName)

    def _OnChangeTooltip(self, tooltip):
        """
            This callback is invoked whenever cursor movement over the browsing area 
            would result in the display of a tooltip message in a standard browser.
        """
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnChangeTooltip'):
            self.browserEventHandler._OnChangeTooltip(self, tooltip)

    def _OnChangeKeyboardFocus(self, focus):
        """
            This callback is invoked whenever keyboard or mouse activity changes the
            current element of the webpage that has keyboard focus.
        """
        pass

    def _OnChangeTargetURL(self, url):
        """
        This event is fired when the target URL has changed. This is usually the result of 
        hovering over a link on the page.
        """
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnChangeTargetURL'):
            self.browserEventHandler._OnChangeTargetURL(self, url)

    def _OnJavascriptPrompt(self, messageText):
        """
            This callback is invoked whenever a script on the current web page calls 
            Javascript's alert() method.
            
            ARGUMENTS
                messageText     A string containing the argument passed to the alert()
                                method in Javascript. None if no argument was passed.
        """
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnJavascriptPrompt'):
            self.browserEventHandler._OnJavascriptPrompt(self, messageText)

    def _OnOpenContextMenu(self, nodeType, linkUrl, imageUrl, pageUrl, frameUrl, editFlags):
        """
            This callback is invoked whenever the user right-clicks in the browser area.
        
        ARGUMENTS
            nodeType    Integer bitvector; the type of item being right-clicked. 
                        Bits are defined in browserConst.py: browserConst.selected*
        
            linkUrl     A string containing the URL to which the selected node links
                        May be None if the selected node does not link elsewhere.
                        
            imageUrl    A string containing the URL from which the selected image is loaded
                        May be None if the selected node is not an image.
                        
            pageUrl     A string containing the URL of the page which is being right-clicked
                        May be None if the selected node is not a page.
            
            frameUrl    String containing the URL of the frame which is being right-clicked.
                        May be None if the selected node is not in a frame.
            
            editFlags   Integer bitvector; operations the browser may perform on the right-clicked node.
                        Bits defined in browserConst.py: browserConst.flagCan*
        """
        if not self.browser:
            return
        self.AppOnOpenContextMenu(nodeType, linkUrl, imageUrl, pageUrl, frameUrl, editFlags)

    def _OnChangeCursor(self, cursorType):
        """
            This callback is invoked when mouse activity changes what the 
            browser's desired cursor shape is.
        
            ARGUMENTS
                cursorType  Integer; this is a windows resource ID, which is reinterpreted
                            by Blue into an EVE cursor resource. The Windows IDs are the
                            same integers as used by the Win32 method LoadIconInfo.
        """
        self.cursorType = cursorType
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnChangeCursor'):
            self.browserEventHandler._OnChangeCursor(self, cursorType)

    def _OnBrowserViewCrash(self):
        """
            This callback is invoked when the browserViewHost detects that its associated
            browserView has crashed. The browserSession will automatically replace the
            browserViewHost with a dummy crashedBrowserViewHost and release its old
            browserViewHost.
        """
        sm.GetService('browserHostManager').ReleaseBrowserView(self.browser)
        self.browser = corebrowserutil.CrashedBrowserViewHost()
        if self.browserEventHandler and hasattr(self.browserEventHandler, '_OnBrowserViewCrash'):
            self.browserEventHandler._OnBrowserViewCrash(self)

    def _ProcessPaintRect(self, rect, size, flags, buffer):
        if self.surface:
            pitch = (rect[2] - rect[0]) * 4
            self.surface.UpdateSubresource(rect, buffer, pitch)
        if self.surfaceDirty and self.surfaceReadyCallback:
            self.surfaceReadyCallback()
            self.surfaceDirty = False

    def IsAlive(self):
        return self.browser is not None and self.browser.alive

    def SetBrowserLockdown(self, mode):
        self.browser.SetBrowserLockdown(mode)

    def AttachBrowserCallbacks(self):
        """
            This method must be called whenever a new browserViewHost is created; that 
            is, at startup, and when a crashed viewHost is replaced by a live one.
        """
        if self.browser is None:
            return
        self.browser.OnChangeTargetURL = self._OnChangeTargetURL
        self.browser.OnReceiveTitle = self._OnReceiveTitle
        self.browser.OnBeginNavigation = self._OnBeginNavigation
        self.browser.OnFinishLoading = self._OnFinishLoading
        self.browser.OnBlockLoading = self._OnBlockLoading
        self.browser.OnChangeCursor = self._OnChangeCursor
        self.browser.OnBeginLoading = self._OnBeginLoading
        self.browser.OnProcessSecurityInfo = self._OnProcessSecurityInfo
        self.browser.OnChangeTooltip = self._OnChangeTooltip
        self.browser.OnChangeKeyboardFocus = self._OnChangeKeyboardFocus
        self.browser.OnJavascriptPrompt = self._OnJavascriptPrompt
        self.browser.OnOpenContextMenu = self._OnOpenContextMenu
        self.browser.OnBrowserViewCrash = self._OnBrowserViewCrash
        self.browser.ProcessPaintRect = self._ProcessPaintRect
        self.surfaceReadyCallback = None

    def ReattachBrowserSession(self):
        if self.browser is None or not self.browser.alive:
            self.SetupBrowserSession()
            if self.browserEventHandler and hasattr(self.browserEventHandler, 'OnReattachBrowserSession'):
                self.browserEventHandler.OnReattachBrowserSession(self)

    def PerformCommand(self, cmd):
        """
            Used to invoke commands within the browserView object itself. These commands 
            are generally OS-related, such as copy and paste.
            
            ARGUMENTS
                cmd     Integer indicating which command to execute. 
                        Constants for these commands are in browserConst.py.
        """
        self.browser.PerformCommand(cmd)
        if self.browserEventHandler is not None and hasattr(self.browserEventHandler, 'SetBrowserFocus'):
            self.browserEventHandler.SetBrowserFocus()

    def ViewSourceOfUrl(self, url):
        if self.browserEventHandler is not None and hasattr(self.browserEventHandler, 'ViewSourceOfUrl'):
            self.browserEventHandler.ViewSourceOfUrl(url)

    def LaunchNewTab(self, url):
        if self.browserEventHandler is not None and hasattr(self.browserEventHandler, 'AddTab'):
            self.browserEventHandler.AddTab(tabUrl=url)

    def CopyText(self, textToCopy):
        blue.pyos.SetClipboardData(textToCopy)

    def AddJavascriptCallback(self, callbackName, callbackFunction):
        """
            Allows the window creating a Browser Pane to register custom JS functions.
            These functions will only be available when the browser is used from that window.
            This is especially useful for creating sensitive callbacks that should only
            be used on trusted sites.
            
            ARGUMENTS:
                callbackName - Name of the callback function. Will be available via JS as
                                Client.callbackName(...)
                callbackFunction - The actual python function to handle the callback.
                
            RETURNS:
                None
        """
        if not self:
            return
        if not hasattr(self, 'browser') or self.browser is None:
            return
        self.browser.RegisterJavaScriptCallback(self.AppGetJavascriptObjectName(), callbackName, callbackFunction)

    def SetBrowserSize(self, width, height):
        if self.IsAlive():
            self.browser.SetSize(width, height)

    def SetBrowserSurface(self, browserSurface, browserSurfaceCallback):
        """
            This method assigns the surface referenced in newSurface to the wbrowser Browser View
            object attached to this browserPane. This method is only operational when the browserPane
            is not set to manage its own texture.
            
            ARGUMENTS:
                browserSurface  - A Trinity surface object which will be used to set the surface on 
                                  the Browser View object. This may also be None.
                browserSurfaceCallback  - A zero argument callback that is triggered when the new 
                                          surface is ready to be displayed.  Can be None.
        
            RETURNS:
                Nothing. Throws exceptions on errors.
        """
        if self.IsAlive():
            self.surface = browserSurface
            self.surfaceDirty = True
            self.surfaceReadyCallback = browserSurfaceCallback
            self.browser.SetDirty()

    def OnKeyDown(self, vkey, flag):
        if self.browser is not None and self.browser.alive:
            if vkey == uiconst.VK_RETURN:
                return
            self.browser.InjectKeyDown(vkey, flag)

    def OnKeyUp(self, vkey, flag):
        if self.browser is not None and self.browser.alive:
            self.browser.InjectKeyUp(vkey, flag)

    def OnChar(self, char, flag):
        if self.browser is not None and self.browser.alive:
            if char == uiconst.VK_RETURN:
                self.browser.InjectKeyDown(char, flag)
            self.browser.InjectChar(char, flag)
            return True

    def OnMouseMove(self, x, y, *args):
        if self.browser is not None and self.browser.alive:
            self.browser.InjectMouseMove(x, y)

    def OnMouseDown(self, *args):
        if self.browser is not None and self.browser.alive:
            self.browser.InjectMouseDown(args[0])

    def OnMouseUp(self, *args):
        if self.browser is not None and self.browser.alive:
            self.browser.InjectMouseUp(args[0])

    def OnMouseWheel(self, *args):
        if self.browser is not None and self.browser.alive:
            self.browser.InjectMouseWheel(uicore.uilib.dz)

    def AppStartup(self, sessionName, initialUrl, browserEventHandler, autoHandleLockdown):
        """
            Invoked upon the completion of the main Startup function. 
            
            ARGUMENTS
                sessionName             The unique string ID of this browser session.
                initialUrl              The url to which the browser will initially be pointed; may be None.
                browserEventHandler     A reference to the object which will receive
                                        forwarded callback events; may be None.
                autoHandleLockdown      A boolean; if True, the browser will automatically attempt
                                        to fetch its initial lockdown state from the SitesService.
        """
        pass

    def AppCleanup(self):
        """
            Invoked upon the completion of the main Cleanup function, which is called 
            when a browserSession is destroyed. 
        """
        pass

    def AppGetJavascriptObjectName(self):
        """
            Invoked to retrieve the name of the object to which Javascript hook methods
            should be registered; that is, a Javascript hook named "MyHook" will be
            registered as "<this method's return value>.MyHook()".
        """
        return 'CCPBrowser'

    def AppSetupBrowserSession(self):
        """
            Invoked upon the completion of the SetupBrowserSession method, which is called
            whenever a browserViewHost has been freshly attached to this browserSession.
            
            This occurs both at the end of Startup and when a crashed browserViewHost
            is replaced by a fresh one.
        """
        pass

    def AppGetHomepage(self):
        """
            Invoked whenever the session needs to know what the user's current homepage
            is; should be overridden to return something from your game's settings store. 
            
            NOTE: Calls browserutil.DefaultHomepage. If you provide that method in a module
                  named browserutil, you do not need to override this one.
        """
        return corebrowserutil.DefaultHomepage()

    def AppOnBlockLoading(self, statusCode):
        """
            Invoked whenever the browser abnormally terminates the loading of a page.
            Status codes are from CoreBrowserUtil.
        
            ARGUMENTS
                statusCode      An integer containing a status code from CoreBrowserUtil.
        """
        pass

    def AppOnBlockBlacklistSite(self):
        """
            Invoked whenever the browser abnormally terminates the loading of a page
            because it is on the CCP Blacklist.
        """
        pass

    def AppOnBlockNonWhitelistSite(self):
        """
            Invoked whenever the browser abnormally terminates the loading of a page
            because the browser is in lockdown, and the site is NOT on the CCP Whitelist.
        """
        pass

    def AppOnOpenContextMenu(self, nodeType, linkUrl, imageUrl, pageUrl, frameUrl, editFlags):
        """
            Invoked whenever the user right-clicks in the browser area.
        
            ARGUMENTS
                nodeType    Integer bitvector; the type of item being right-clicked. 
                            Bits are defined in browserConst.py: browserConst.selected*
        
                linkUrl     A string containing the URL to which the selected node links
                            May be None if the selected node does not link elsewhere.
        
                imageUrl    A string containing the URL from which the selected image is loaded
                            May be None if the selected node is not an image.
        
                pageUrl     A string containing the URL of the page which is being right-clicked
                            May be None if the selected node is not a page.
        
                frameUrl    String containing the URL of the frame which is being right-clicked.
                            May be None if the selected node is not in a frame.
        
                editFlags   Integer bitvector; operations the browser may perform on the right-clicked node.
                            Bits defined in browserConst.py: browserConst.flagCan*
        """
        pass


exports = {'browser.CoreBrowserSession': CoreBrowserSession}
