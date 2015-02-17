#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelAchievements.py
from achievements.client.achievementGroupEntry import AchievementGroupEntry
from achievements.client.achievementTreeWindow import AchievementTreeWindow
from achievements.client.auraAchievementWindow import AchievementAuraWindow
from achievements.common.achievementGroups import GetAchievementGroup
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.util.color import Color
from eve.client.script.ui.eveFontConst import EVE_SMALL_FONTSIZE, EVE_LARGE_FONTSIZE
from eve.client.script.ui.shared.infoPanels import infoPanelConst
from eve.client.script.ui.shared.infoPanels.InfoPanelBase import InfoPanelBase
import carbonui.const as uiconst
from eve.client.script.ui.shared.infoPanels.infoPanelConst import PANEL_ACHIEVEMENTS, MODE_COLLAPSED, MODE_NORMAL
from eve.client.script.ui.shared.infoPanels.infoPanelControls import InfoPanelLabel
from localization import GetByLabel
from eve.client.script.ui.control.buttons import ButtonIcon

class InfoPanelAchievements(InfoPanelBase):
    __guid__ = 'uicls.InfoPanelAchievements'
    default_name = 'InfoPanelAchievements'
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesPanelIcon.png'
    default_state = uiconst.UI_PICKCHILDREN
    default_height = 120
    label = 'UI/Achievements/OpportunitiesHint'
    hasSettings = False
    panelTypeID = PANEL_ACHIEVEMENTS
    groupEntry = None
    achievementContent = None
    __notifyevents__ = ['OnAchievementsDataInitialized', 'OnAchievementActiveGroupChanged', 'OnAchievementChanged']

    def ApplyAttributes(self, attributes):
        InfoPanelBase.ApplyAttributes(self, attributes)
        self.titleLabel = self.headerCls(name='title', text='<color=white>' + GetByLabel('UI/Achievements/InfoPanelHeader'), parent=self.headerCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)

    @staticmethod
    def IsAvailable():
        """ Is this info panel currently available for viewing """
        return sm.GetService('achievementSvc').IsEnabled()

    def ConstructCompact(self):
        self.mainCont.Flush()
        self.achievementContent = None

    def ConstructNormal(self, blinkAchievementID = None):
        if not self.achievementContent or self.achievementContent.destroyed:
            self.mainCont.Flush()
            self.achievementContent = ContainerAutoSize(parent=self.mainCont, name='achievementContent', align=uiconst.TOTOP, alignMode=uiconst.TOTOP)
            grid = LayoutGrid(parent=self.mainCont, align=uiconst.TOTOP, columns=2, opacity=0.0)
            button = ButtonIcon(texturePath='res:/ui/Texture/Classes/InfoPanels/opportunitiesTreeIcon.png', align=uiconst.TOPLEFT, iconSize=16, parent=grid, func=self.OpenOpportunitiesTree, pos=(0, 0, 16, 16))
            subTextLabel = InfoPanelLabel(parent=grid, align=uiconst.CENTERLEFT, text='See all opportunities', state=uiconst.UI_NORMAL, fontsize=EVE_SMALL_FONTSIZE, bold=True, left=4)
            subTextLabel.OnClick = self.OpenOpportunitiesTree
            uicore.animations.FadeIn(grid)
        groupID = sm.GetService('achievementSvc').GetActiveAchievementGroupID()
        self.LoadContent(groupID, blinkAchievementID=blinkAchievementID)

    def LoadContent(self, groupID = None, blinkAchievementID = None):
        activeGroupData = GetAchievementGroup(groupID)
        if activeGroupData:
            if self.groupEntry is None or self.groupEntry.destroyed:
                self.achievementContent.Flush()
                self.groupEntry = AchievementGroupEntry(parent=self.achievementContent, align=uiconst.TOTOP, groupInfo=activeGroupData, blinkAchievementID=blinkAchievementID, animateIn=True)
            else:
                self.groupEntry.LoadGroupData(activeGroupData, blinkAchievementID=blinkAchievementID, animateIn=True)
            return
        self.achievementContent.Flush()
        self.groupEntry = None
        label = InfoPanelLabel(name='noActiveOpp', text=GetByLabel('Achievements/UI/noActiveOpp'), parent=self.achievementContent, fontsize=EVE_LARGE_FONTSIZE, padding=(0, 2, 0, 2), state=uiconst.UI_NORMAL, align=uiconst.TOTOP)

    def OpenAchievementAuraWindow(self, *args):
        AchievementAuraWindow.Open()

    def OpenOpportunitiesTree(self, *args):
        AchievementTreeWindow.Open()

    def OnAchievementActiveGroupChanged(self, groupID, emphasize):
        if self.mode != MODE_NORMAL:
            self.SetMode(MODE_NORMAL)
        self.Refresh()
        if emphasize:
            uicore.animations.BlinkIn(self, duration=0.4, loops=4)

    def OnAchievementChanged(self, achievement, *args, **kwds):
        if achievement:
            blinkAchievementID = achievement.achievementID
        else:
            blinkAchievementID = None
        self.Refresh(blinkAchievementID)

    def OnAchievementsDataInitialized(self):
        self.Refresh()

    def Refresh(self, blinkAchievementID = None):
        if self.mode != infoPanelConst.MODE_NORMAL:
            self.ConstructCompact()
        else:
            self.ConstructNormal(blinkAchievementID=blinkAchievementID)
