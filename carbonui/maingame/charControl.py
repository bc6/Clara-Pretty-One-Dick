#Embedded file name: carbonui/maingame\charControl.py
import carbonui.const as uiconst
from carbonui.control.layer import LayerCore

class CoreCharControl(LayerCore):
    __guid__ = 'uicls.CharControlCore'

    def ApplyAttributes(self, *args, **kw):
        LayerCore.ApplyAttributes(self, *args, **kw)
        self.opened = 0
        self.cursor = uiconst.UICURSOR_CROSS

    def GetConfigValue(self, data, name, default):
        """
        Returns the specified configration value using the app specific config systems
        """
        return default

    def OnOpenView(self):
        """
        called when the layer view is opened
        """
        self.isTabStop = True
        self.state = uiconst.UI_NORMAL
        self.OnSetFocus()

    def OnCloseView(self):
        """
        called when the layer view is closed
        """
        self.OnKillFocus()
        self.isTabStop = False

    def OnKillFocus(self, *args):
        nav = sm.GetService('navigation')
        nav.controlLayer = None
        nav.hasFocus = False
        nav.RecreatePlayerMovement()

    def OnSetFocus(self, *args):
        nav = sm.GetService('navigation')
        nav.controlLayer = self
        nav.hasFocus = True
        nav.RecreatePlayerMovement()
