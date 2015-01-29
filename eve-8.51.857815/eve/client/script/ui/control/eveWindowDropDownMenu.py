#Embedded file name: eve/client/script/ui/control\eveWindowDropDownMenu.py
import carbonui.const as uiconst
from carbonui.primitives.fill import Fill
from carbonui.primitives.line import Line
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from carbonui.control.windowDropDownMenu import WindowDropDownMenuCore, WindowDropDownMenuCoreOverride

class WindowDropDownMenu(WindowDropDownMenuCore):
    __guid__ = 'uicls.WindowDropDownMenu'

    def PrepareLayout(self):
        Line(parent=self, align=uiconst.TORIGHT)
        self.textLabel = EveLabelSmall(text=self.name, parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.hilite = Fill(parent=self, state=uiconst.UI_HIDDEN, padding=1)
        self.width = self.textLabel.width + 10
        self.cursor = uiconst.UICURSOR_SELECT

    def GetTextHeight(self):
        return self.textLabel.textheight


WindowDropDownMenuCoreOverride.__bases__ = (WindowDropDownMenu,)
