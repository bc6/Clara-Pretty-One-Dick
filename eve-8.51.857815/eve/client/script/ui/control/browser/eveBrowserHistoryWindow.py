#Embedded file name: eve/client/script/ui/control/browser\eveBrowserHistoryWindow.py
"""
Extending BrowserHistoryWindowCore
"""
from carbonui.control.browser.browserHistoryWindow import BrowserHistoryWindowCore, BrowserHistoryWindowCoreOverride

class HistoryWindow(BrowserHistoryWindowCore):
    __guid__ = 'uicls.BrowserHistoryWindow'

    def ApplyAttributes(self, attributes):
        BrowserHistoryWindowCore.ApplyAttributes(self, attributes)
        self.SetWndIcon()
        self.SetTopparentHeight(0)


BrowserHistoryWindowCoreOverride.__bases__ = (HistoryWindow,)
