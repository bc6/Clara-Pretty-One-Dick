#Embedded file name: eve/client/script/ui/control/browser\eveBrowserSettingsWindow.py
"""
Extending BrowserSettingsWindowCore
"""
import localization
from carbonui.control.browser.browserSettingsWindow import BrowserSettingsWindowCore, BrowserSettingsWindowCoreOverride
from eve.client.script.ui.control.eveLabel import WndCaptionLabel

class BrowserSettingsWindow(BrowserSettingsWindowCore):
    __guid__ = 'uicls.BrowserSettingsWindow'
    default_windowID = 'BrowserSettingsWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/browser.png'

    def ApplyAttributes(self, attributes):
        BrowserSettingsWindowCore.ApplyAttributes(self, attributes)
        self.SetWndIcon(self.iconNum)
        WndCaptionLabel(text=localization.GetByLabel('UI/Browser/BrowserSettings/BrowserSettingsCaption'), parent=self.sr.topParent)


BrowserSettingsWindowCoreOverride.__bases__ = (BrowserSettingsWindow,)
