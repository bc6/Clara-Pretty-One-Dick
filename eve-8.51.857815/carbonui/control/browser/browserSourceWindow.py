#Embedded file name: carbonui/control/browser\browserSourceWindow.py
"""
This is the browser window. It contains a browser pane that is renders html code and handles
all communication to that pane. It has various features that are typical to browsing like
Bookmarks, history,back and forward button and so on.
"""
import carbonui.const as uiconst
import uthread
import blue
import browser
import localization
from carbonui.primitives.fill import Fill
from carbonui.control.window import WindowCoreOverride as Window

class BrowserSourceWindowCore(Window):
    """
        Basic browser window that only contains a browser container, for purposes of showing a page's source code.
    """
    __guid__ = 'uicls.BrowserSourceWindowCore'
    default_windowID = 'BrowserSourceWindowCore'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.MakeUnstackable()
        mainArea = self.GetMainArea()
        bp = browser.BrowserPane(parent=mainArea, padding=6, align=uiconst.TOALL, state=uiconst.UI_NORMAL)
        bp.Startup()
        self.browserPane = bp
        Fill(parent=mainArea, padding=const.defaultPadding, color=(0.0, 0.0, 0.0, 1.0))
        self.browserSession = browser.BrowserSession()
        self.browserSession.Startup('viewSource', browserEventHandler=self)
        self.browserSession.SetBrowserSurface(bp.GetSurface(), self.browserPane._OnSurfaceReady)
        self.browserSession.SetViewSourceMode(True)
        self.browserPane.browserSession = self.browserSession
        self.sizeChanged = False
        self.browserPane.ResizeBrowser()
        url = attributes.browseTo
        if url is not None:
            self.BrowseTo(url)

    def BrowseTo(self, url = None, *args, **kwargs):
        try:
            self.SetCaption(localization.GetByLabel('UI/Browser/HTMLSourceOf', url=url))
        except:
            self.SetCaption(url)

        self.browserSession.BrowseTo(url=url, *args)

    def OnResizeUpdate(self, *args):
        if not self.sizeChanged:
            uthread.new(self.DoResizeBrowser)
            self.sizeChanged = True

    def DoResizeBrowser(self):
        blue.pyos.synchro.SleepWallclock(250)
        if getattr(self, 'browserPane', None):
            self.browserPane.ResizeBrowser()
        self.sizeChanged = False

    def _OnClose(self, *args):
        self.browserPane.browserSession = None
        self.browserSession.Cleanup()
        self.browserSession = None


class BrowserSourceWindowCoreOverride(BrowserSourceWindowCore):
    pass
