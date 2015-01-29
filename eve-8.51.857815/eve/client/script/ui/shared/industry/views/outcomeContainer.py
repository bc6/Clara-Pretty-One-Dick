#Embedded file name: eve/client/script/ui/shared/industry/views\outcomeContainer.py
from carbonui import const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import Frame
from carbonui.util.color import Color
from eve.client.script.ui.control.eveLabel import EveHeaderMedium, EveHeaderSmall, EveLabelMediumBold
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay
from eve.client.script.ui.shared.industry.industryUIConst import GetJobColor
from eve.client.script.ui.shared.industry.views.containersMETE import ContainerTE, ContainerME
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.ui.shared.industry.views.industryCaptionLabel import IndustryCaptionLabel
from eve.client.script.ui.shared.industry.views.industryTooltips import ProbabilityTooltipPanel
from eve.client.script.ui.shared.industry.views.outcomeItemContainer import OutcomeItemContainer
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
import industry
from localization import GetByLabel
import localization

class OutcomeContainer(Container):
    default_width = 327
    default_height = 202

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = None
        foregroundCont = Container(bgTexturePath='res:/UI/Texture/Classes/Industry/Output/outputContBg.png', parent=self, align=uiconst.CENTER, width=self.width, height=self.height, state=uiconst.UI_DISABLED)
        self.bgPattern = Frame(bgParent=foregroundCont, texturePath='res:/UI/Texture/Classes/Industry/Output/bgPattern.png', cornerSize=12)
        self.captionCont = ContainerAutoSize(name='captionCont', parent=self, align=uiconst.TOPLEFT, pos=(14, 10, 300, 0))
        self.outcomeCaption = EveHeaderMedium(name='outcomeCaption', parent=self.captionCont, align=uiconst.TOTOP, bold=True, text=GetByLabel('UI/Industry/Outcome'))
        self.outcomeLabel = EveHeaderSmall(name='outcomeLabel', parent=self.captionCont, align=uiconst.TOTOP, bold=True)
        self.probabilityLabel = EveHeaderSmall(name='probabilityLabel', parent=self.captionCont, align=uiconst.TOTOP, bold=False, state=uiconst.UI_HIDDEN)
        self.probabilityLabel.LoadTooltipPanel = self.LoadProbabilityTooltipPanel
        self.probabilityLabel.GetTooltipDelay = self.GetProbabilityTooltipDelay
        self.copyInfoCont = Container(name='copyInfoCont', parent=self, align=uiconst.CENTERBOTTOM, pos=(0, 8, 300, 32), state=uiconst.UI_HIDDEN)
        self.containerME = ContainerME(parent=self.copyInfoCont, align=uiconst.TOPLEFT, width=71, height=30)
        self.runsPerCopyCont = ContainerAutoSize(name='runsPerCopyCont', parent=self.copyInfoCont, align=uiconst.CENTERTOP)
        self.containerTE = ContainerTE(parent=self.copyInfoCont, align=uiconst.TOPRIGHT, width=71, height=30)
        IndustryCaptionLabel(parent=self.runsPerCopyCont, text=localization.GetByLabel('UI/Industry/Runs'), align=uiconst.CENTERTOP)
        self.bpRunsLabel = EveLabelMediumBold(parent=self.runsPerCopyCont, align=uiconst.CENTERTOP, top=12)
        self.errorFrame = ErrorFrame(bgParent=self, padding=1)
        self.outcomeItem = OutcomeItemContainer(parent=self)
        FillUnderlay(bgParent=self, opacity=0.5)

    def LoadProbabilityTooltipPanel(self, tooltipPanel, *args):
        if not self.jobData:
            return
        self.tooltipPanel = ProbabilityTooltipPanel(jobData=self.jobData, tooltipPanel=tooltipPanel)

    def GetProbabilityTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def AnimEntry(self):
        if self.jobData:
            color = GetJobColor(self.jobData)
            for pattern in (self.bgPattern, self.outcomeCaption):
                uicore.animations.SpColorMorphTo(pattern, pattern.GetRGBA(), color, duration=0.3)

        self.errorFrame.Hide()

    def UpdateState(self):
        if self.jobData:
            self.outcomeLabel.text = self.jobData.GetProductLabel()
            self.UpdateCopyInfo()
            if self.jobData.activityID == industry.INVENTION:
                self.probabilityLabel.Show()
                color = Color.RGBtoHex(*GetJobColor(self.jobData))
                self.probabilityLabel.text = localization.GetByLabel('UI/Industry/SuccessProbabilityPerRun', probability=self.jobData.probability * 100, color=color)
            else:
                self.probabilityLabel.Hide()
        else:
            self.outcomeLabel.text = ''
            self.probabilityLabel.Hide()

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.UpdateState()
        self.outcomeItem.OnNewJobData(jobData)
        self.AnimEntry()

    def OnRunsChanged(self):
        self.UpdateState()

    def UpdateCopyInfo(self):
        bpData = self.jobData.GetProductNewBlueprint()
        if not bpData:
            self.copyInfoCont.Hide()
            return
        self.copyInfoCont.Show()
        self.containerME.SetValue(bpData.materialEfficiency)
        self.containerTE.SetValue(bpData.timeEfficiency)
        if bpData.original:
            self.runsPerCopyCont.Hide()
        else:
            self.runsPerCopyCont.Show()
            self.bpRunsLabel.text = '%s' % bpData.runsRemaining
