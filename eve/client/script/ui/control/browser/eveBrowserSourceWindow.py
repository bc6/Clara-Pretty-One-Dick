#Embedded file name: eve/client/script/ui/control/browser\eveBrowserSourceWindow.py
"""
Extending BrowserSourceWindowCore
"""
from carbonui.control.browser.browserSourceWindow import BrowserSourceWindowCore, BrowserSourceWindowCoreOverride

class BrowserSourceWindow(BrowserSourceWindowCore):
    __guid__ = 'uicls.BrowserSourceWindow'

    def ApplyAttributes(self, attributes):
        BrowserSourceWindowCore.ApplyAttributes(self, attributes)
        self.SetWndIcon()
        self.SetTopparentHeight(0)


BrowserSourceWindowCoreOverride.__bases__ = (BrowserSourceWindow,)
