#Embedded file name: eve/client/script/ui/shared/industry/views\skillIcon.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.themeColored import FillThemeColored
from eve.client.script.ui.shared.industry.industryUIConst import GetJobColor
from eve.client.script.ui.shared.industry.views.industryTooltips import SkillTooltipPanel
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY

class SkillIcon(Container):
    default_name = 'SkillIcon'
    default_state = uiconst.UI_NORMAL
    default_width = 67
    default_height = 46
    default_bgTexturePath = 'res:/UI/Texture/classes/Industry/Center/skillFrame.png'

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = attributes.jobData
        self.skills = []
        self.skillIcon = Sprite(name='skillIcon', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, pos=(0, -1, 33, 33))
        self.patternSprite = Sprite(name='patternSprite', bgParent=self, texturePath='res:/UI/Texture/classes/Industry/Center/skillFramePattern.png')
        FillThemeColored(bgParent=self, padding=3)
        self.UpdateState()

    def UpdateState(self, *args):
        if not self.jobData:
            return
        self.jobData.on_updated.connect(self.UpdateState)
        texturePath, _ = sm.GetService('skills').GetRequiredSkillsLevelTexturePathAndHint(self.skills)
        self.skillIcon.SetTexturePath(texturePath)
        color = GetJobColor(self.jobData)
        uicore.animations.SpColorMorphTo(self.patternSprite, self.patternSprite.GetRGBA(), color, duration=0.3)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        if not self.jobData:
            self.skills = []
            return
        skills = self.jobData.required_skills
        self.skills = [ (skill.typeID, skill.level) for skill in skills if skill.typeID is not None ]
        self.UpdateState()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        self.tooltipPanel = SkillTooltipPanel(skills=self.skills, tooltipPanel=tooltipPanel)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def GetTooltipPointer(self):
        return uiconst.POINT_LEFT_2

    def OnMouseEnter(self, *args):
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')
        uicore.animations.FadeTo(self, self.opacity, 1.5, duration=0.3)

    def OnMouseExit(self, *args):
        uicore.animations.FadeTo(self, self.opacity, 1.0, duration=0.3)
