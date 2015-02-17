#Embedded file name: eve/client/script/ui/shared/industry\installationActivityIcon.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.industryUIConst import ACTIVITY_ICONS_SMALL
from eve.client.script.ui.shared.industry.views.industryTooltips import FacilityActivityTooltip
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
import localization

class InstallationActivityIcon(Container):
    default_state = uiconst.UI_NORMAL
    default_iconColor = Color.WHITE

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.isEnabled = attributes.isEnabled
        self.activityID = attributes.activityID
        self.facilityData = attributes.facilityData
        systemCostIndex = attributes.systemCostIndex
        self.opacity = 1.0 if self.isEnabled else 0.05
        self.icon = Sprite(name='icon', parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath=ACTIVITY_ICONS_SMALL[self.activityID], opacity=0.75)
        if self.facilityData:
            if self.facilityData.HasFacilityModifiers(self.activityID):
                Sprite(name='plusIcon', parent=self, align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Icons/plus.png', color=Color.WHITE, pos=(-3, -1, 6, 6), idx=0)

    def LoadTooltipPanel(self, panel, *args):
        if self.facilityData:
            FacilityActivityTooltip(self.facilityData, self.activityID, panel)
        else:
            text = localization.GetByLabel(industryUIConst.ACTIVITY_NAMES.get(self.activityID))
            panel.AddLabelMedium(text=text, cellPadding=8)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY
