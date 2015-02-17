#Embedded file name: eve/client/script/ui/control\eveMenu.py
from eve.client.script.ui.control.eveWindowUnderlay import BumpedUnderlay, MenuUnderlay, ListEntryUnderlay
from eve.client.script.ui.control.themeColored import FillThemeColored
import uiprimitives
import uicontrols
import uicls
import carbonui.const as uiconst
import crimewatchConst
from carbonui.control.menu import DropDownMenuCore
from carbonui.util.mouseTargetObject import MouseTargetObject

class DropDownMenu(DropDownMenuCore):
    __guid__ = 'uicls.DropDownMenu'

    def ApplyAttributes(self, attributes):
        DropDownMenuCore.ApplyAttributes(self, attributes)
        MouseTargetObject(self)

    def Prepare_Background_(self, *args):
        self.sr.underlay = MenuUnderlay(bgParent=self, padding=-2)


class MenuEntryView(uicls.MenuEntryViewCore):
    __guid__ = 'uicls.MenuEntryView'

    def Prepare_Label_(self, *args):
        self.sr.label = uicontrols.EveLabelSmall(parent=self, left=8, top=1, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)

    def Prepare_Hilite_(self, *args):
        self.sr.hilite = ListEntryUnderlay(parent=self, padding=(1, 1, 0, 0))


class SuspectMenuEntryView(MenuEntryView):
    __guid__ = 'uicls.SuspectMenuEntryView'
    default_warningColor = crimewatchConst.Colors.Suspect.GetRGBA()

    def ApplyAttributes(self, attributes):
        MenuEntryView.ApplyAttributes(self, attributes)
        uiprimitives.Sprite(texturePath='res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal_Small.png', parent=self, pos=(4, 3, 9, 10), align=uiconst.RELATIVE, idx=0, state=uiconst.UI_DISABLED, color=self.default_warningColor)
        self.sr.label.left = 16
        self.sr.label.color.SetRGBA(*self.default_warningColor)


class CriminalMenuEntryView(SuspectMenuEntryView):
    __guid__ = 'uicls.CriminalMenuEntryView'
    default_warningColor = crimewatchConst.Colors.Criminal.GetRGBA()


from carbonui.control.menu import MenuEntryViewCoreOverride, DropDownMenuCoreOverride
MenuEntryViewCoreOverride.__bases__ = (MenuEntryView,)
DropDownMenuCoreOverride.__bases__ = (DropDownMenu,)
