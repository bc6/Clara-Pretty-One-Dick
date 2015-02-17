#Embedded file name: achievements/client\achievementGroupEntry.py
from achievements.client.achievementTaskEntry import AchievementTaskEntry
from achievements.client.auraAchievementWindow import AchievementAuraWindow
from carbonui.primitives.base import ReverseScaleDpi
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
from carbonui.util.color import Color
import carbonui.const as uiconst
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.eveLabel import EveLabelSmall, EveLabelLarge, EveHeaderLarge, EveCaptionLarge, EveCaptionMedium
from eve.client.script.ui.eveFontConst import EVE_LARGE_FONTSIZE
from eve.client.script.ui.shared.infoPanels.infoPanelControls import InfoPanelLabel
from localization import GetByLabel
POINTER_PADRIGHT = 7

class AchievementGroupEntry(ContainerAutoSize):
    __notifyevents__ = ['OnAchievementChanged']
    default_padTop = 0
    default_padBottom = 3
    default_state = uiconst.UI_NORMAL
    default_alignMode = uiconst.TOTOP
    texturePath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Explore.png'
    progressBackground = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesFillBar.png'
    fillBox = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesFillBox.png'
    checkmarkPath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesCheck.png'
    groupData = None

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.ConstructLayout()
        self.LoadGroupData(attributes.groupInfo, attributes.blinkAchievementID, attributes.animateIn)
        sm.RegisterNotify(self)

    def ConstructLayout(self):
        headerContainer = Container(parent=self, align=uiconst.TOTOP, height=28, padTop=4, padBottom=6)
        self.groupName = EveLabelLarge(parent=headerContainer, align=uiconst.CENTERLEFT, left=8)
        Frame(texturePath='res:/UI/Texture/classes/Achievements/pointRightHeaderFrame.png', cornerSize=16, offset=-14, parent=headerContainer, color=(1, 1, 1, 0.25), align=uiconst.TOALL)
        progressClipper = Container(parent=headerContainer, align=uiconst.TOALL, clipChildren=True, padRight=-POINTER_PADRIGHT)
        self.progress = Frame(texturePath='res:/UI/Texture/classes/Achievements/pointRightHeaderBackground.png', cornerSize=15, offset=-13, parent=progressClipper, color=(1, 1, 1, 0.25))
        self.progress.padRight = 400
        self.progress.opacity = 0.0
        self.tasksContainer = ContainerAutoSize(parent=self, name='tasksContainer', align=uiconst.TOTOP, state=uiconst.UI_NORMAL)

    def LoadGroupData(self, groupData, blinkAchievementID = None, animateIn = False):
        if not self.groupData or self.groupData.groupID != groupData.groupID:
            self.groupData = groupData
            self.groupName.text = self.groupData.groupName
            self.AddAchievementTasks(blinkAchievementID=blinkAchievementID, animateIn=animateIn)
        if animateIn:
            self.AnimateIn()
        self.UpdateState()

    def UpdateState(self):
        self.UpdateProgress()
        self.UpdateAchievementTasks()

    def OnAchievementChanged(self, achievement, *args, **kwds):
        if self.groupData.HasAchievement(achievement.achievementID):
            self.UpdateState()

    def UpdateProgress(self):
        progressProportion = self.groupData.GetProgressProportion()
        maxWidth = ReverseScaleDpi(self.displayWidth) - POINTER_PADRIGHT
        uicore.animations.MorphScalar(self.progress, 'padRight', startVal=self.progress.padRight, endVal=POINTER_PADRIGHT + maxWidth * (1 - progressProportion), curveType=uiconst.ANIM_SMOOTH, duration=0.33)
        uicore.animations.MorphScalar(self.progress, 'opacity', startVal=self.progress.opacity, endVal=min(progressProportion, 0.25), curveType=uiconst.ANIM_SMOOTH, duration=0.33)

    def OpenAchievementAuraWindow(self, *args):
        AchievementAuraWindow.Open()

    def UpdateAchievementTasks(self):
        detailsShown = False
        for each in self.tasksContainer.children:
            if not detailsShown and not each.achievementTask.completed:
                each.ShowDetails()
                detailsShown = True
            each.UpdateAchievementTaskState()

    def AddAchievementTasks(self, blinkAchievementID = None, animateIn = False):
        self.tasksContainer.Flush()
        for achievementTask in self.groupData.GetAchievementTasks():
            AchievementTaskEntry(parent=self.tasksContainer, align=uiconst.TOTOP, achievement=achievementTask, blinkIn=not animateIn and achievementTask.achievementID == blinkAchievementID, opacity=0.0 if animateIn else 1.0, achievementGroup=self.groupData, callbackTaskExpanded=self.OnTaskExpanded)

    def OnTaskExpanded(self, expandedTask, *args):
        for each in self.tasksContainer.children:
            if each is not expandedTask:
                each.HideDetails()

    def AnimateIn(self):
        to = 0.0
        for each in self.tasksContainer.children:
            uicore.animations.FadeIn(each, duration=0.08, timeOffset=to, curveType=uiconst.ANIM_OVERSHOT)
            if hasattr(each, 'ShowIntroAnimation'):
                each.ShowIntroAnimation()
            to += 0.05

    def LoadTooltipPanel(self, tooltipPanel, *args, **kwds):
        tooltipPanel.LoadGeneric2ColumnTemplate()
        if not self.groupData.extraInfo:
            return
        extraInfo = self.groupData.extraInfo
        tipsHeader = EveLabelSmall(text=GetByLabel('UI/Achievements/TipsAndInfoHeader'), width=200, bold=True)
        tooltipPanel.AddCell(tipsHeader, colSpan=tooltipPanel.columns)
        tipsText = EveLabelSmall(text=self.groupData.groupDescription, align=uiconst.TOTOP)
        tooltipPanel.AddCell(tipsText, colSpan=tooltipPanel.columns)
        for info in extraInfo:
            icon = Sprite(name='icon', parent=tooltipPanel, pos=(0,
             0,
             info['size'],
             info['size']), texturePath=info['path'], state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, color=info.get('color', None))
            label = EveLabelSmall(name='tipsHeader', text=info['text'], parent=tooltipPanel, width=180, align=uiconst.CENTERLEFT)
