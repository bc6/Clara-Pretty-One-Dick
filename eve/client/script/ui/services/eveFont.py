#Embedded file name: eve/client/script/ui/services\eveFont.py
import telemetry
import fontConst
import carbonui.languageConst as languageConst
from carbonui.services.font import FontHandler
from eve.client.script.ui.control.eveLabel import Label

class EveFontHandler(FontHandler):
    defaultLabelClass = Label
    __notifyevents__ = ['OnUIRefresh']

    def __init__(self, *args, **kwds):
        FontHandler.__init__(self, *args, **kwds)
        sm.RegisterNotify(self)

    @telemetry.ZONE_METHOD
    def GetFontFamilyBasedOnWindowsLanguageID(self, windowsLanguageID):
        """Core function overwrite. Function to provide client specific set of fonts per langangeID.
        Family Sets should be provided through fontConst.FONTFAMILY_PER_WINDOWS_LANGUAGEID"""
        if windowsLanguageID in fontConst.EVEFONTGROUP:
            return fontConst.FONTFAMILY_PER_WINDOWS_LANGUAGEID[languageConst.LANG_ENGLISH]
        return fontConst.FONTFAMILY_PER_WINDOWS_LANGUAGEID.get(windowsLanguageID, None)

    def OnUIRefresh(self):
        self.Prime()
