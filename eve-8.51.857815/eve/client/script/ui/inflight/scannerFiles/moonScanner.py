#Embedded file name: eve/client/script/ui/inflight/scannerFiles\moonScanner.py
"""
The UI code for the moon analysis window
"""
import carbonui.const as uiconst
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.inflight.moonscan import MoonScanView

class MoonScanner(Window):
    __notifyevents__ = ['OnSessionChanged']
    default_windowID = 'MoonScanner'
    default_width = 300
    default_height = 300
    default_minSize = (256, 128)
    default_captionLabelPath = 'UI/Inflight/Scanner/MoonAnalysis'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.scope = 'inflight'
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.HideMainIcon()
        self.sr.moonscanner = MoonScanView(name='moonparent', parent=self.sr.main, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.moonscanner.Startup()
        sm.GetService('moonScan').Refresh()

    def SetEntries(self, entries):
        self.sr.moonscanner.SetEntries(entries)

    def ClearMoons(self):
        self.sr.moonscanner.Clear()
