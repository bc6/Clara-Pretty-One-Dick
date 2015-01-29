#Embedded file name: eve/client/script/ui/shared/industry\viewModeButtons.py
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.shared.industry.industryUIConst import VIEWMODE_ICONLIST, VIEWMODE_LIST
import localization
import carbonui.const as uiconst

class ViewModeButtons(ContainerAutoSize):
    """
        invContainer control for switching between views
    """
    default_name = 'ViewModeButtons'
    default_viewMode = VIEWMODE_ICONLIST
    default_height = 16

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.settingsID = attributes.settingsID
        self.controller = attributes.controller
        self.viewMode = settings.user.ui.Get(self.settingsID, VIEWMODE_ICONLIST)
        self.btnViewModeIconList = ButtonIcon(texturePath='res:/UI/Texture/Icons/38_16_189.png', parent=self, align=uiconst.TOLEFT, width=self.height, func=self.SetViewModeIconList, hint=localization.GetByLabel('UI/Inventory/Details'))
        self.btnViewModeList = ButtonIcon(texturePath='res:/UI/Texture/Icons/38_16_190.png', parent=self, align=uiconst.TOLEFT, width=self.height, func=self.SetViewModeList, hint=localization.GetByLabel('UI/Inventory/List'))
        self.SetViewMode(self.viewMode)

    def SetViewModeIconList(self):
        self.SetViewMode(VIEWMODE_ICONLIST)
        self.controller.OnViewModeChanged(VIEWMODE_ICONLIST)

    def SetViewModeList(self):
        self.SetViewMode(VIEWMODE_LIST)
        self.controller.OnViewModeChanged(VIEWMODE_LIST)

    def SetViewMode(self, viewMode):
        self.viewMode = viewMode
        self.UpdateButtons(viewMode)
        settings.user.ui.Set(self.settingsID, viewMode)

    def GetViewMode(self):
        return self.viewMode

    def UpdateButtons(self, viewMode):
        self.btnViewModeIconList.SetActive(viewMode == VIEWMODE_ICONLIST)
        self.btnViewModeList.SetActive(viewMode == VIEWMODE_LIST)
