#Embedded file name: eve/client/script/ui/control/browser\eveWebsiteTrustManagementWindowCore.py
"""
Extending WebsiteTrustManagementWindowCore
"""
import localization
from carbonui.control.browser.websiteTrustManagementWindow import WebsiteTrustManagementWindowCore, WebsiteTrustManagementWindowCoreOverride
from eve.client.script.ui.control.eveLabel import WndCaptionLabel

class WebsiteTrustManagementWindow(WebsiteTrustManagementWindowCore):
    __guid__ = 'uicls.WebsiteTrustManagementWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/browser.png'

    def ApplyAttributes(self, attributes):
        WebsiteTrustManagementWindowCore.ApplyAttributes(self, attributes)
        self.SetWndIcon(self.iconNum)
        WndCaptionLabel(text=localization.GetByLabel('UI/Browser/TrustedManagementHeader'), parent=self.sr.topParent)


WebsiteTrustManagementWindowCoreOverride.__bases__ = (WebsiteTrustManagementWindow,)
