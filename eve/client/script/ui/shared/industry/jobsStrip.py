#Embedded file name: eve/client/script/ui/shared/industry\jobsStrip.py
import math
from carbonui.primitives.container import Container
from carbonui.primitives.frame import Frame
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.util.color import Color
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.themeColored import FrameThemeColored
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.activitySelectionButtons import ActivitySelectionButtons
import carbonui.const as uiconst
from carbonui.primitives.gradientSprite import GradientSprite
from eve.client.script.ui.shared.industry.submitButton import SubmitButton
import telemetry
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.ui.shared.industry.views.industryTooltips import JobsSummaryTooltipPanel
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
import industry
import localization

class JobsStrip(Container):
    default_name = 'JobsStrip'
    default_height = 47

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        callback = attributes.callback
        submit = attributes.submit
        self.oldJobData = None
        self.jobData = attributes.jobData
        self.jobsSummary = JobsSummary(parent=self, align=uiconst.CENTERLEFT, left=10)
        self.activitySelectionButtons = ActivitySelectionButtons(parent=self, align=uiconst.CENTER, callback=callback, width=248, height=38)
        self.submitBtn = SubmitButton(parent=self, align=uiconst.CENTERRIGHT, fixedheight=30, fixedwidth=125, left=7)
        GradientSprite(bgParent=self, rotation=-math.pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.3), (1.0, 0.05)])
        FrameThemeColored(bgParent=self, colorType=uiconst.COLORTYPE_UIBASECONTRAST)
        self.UpdateState()

    @telemetry.ZONE_METHOD
    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.activitySelectionButtons.OnNewJobData(jobData)
        self.submitBtn.OnNewJobData(jobData)
        if jobData:
            self.jobData.on_updated.connect(self.UpdateState)
            self.jobsSummary.OnNewJobData(jobData)
        self.UpdateState()

    def UpdateState(self, *args):
        if self.jobData:
            self.submitBtn.Show()
            self.jobsSummary.Show()
        else:
            self.submitBtn.Hide()
            self.jobsSummary.Hide()


class JobsSummary(LayoutGrid):
    default_columns = 2
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        self.activityType = None
        self.jobData = None
        self.countCaption = Label(color=Color.GRAY, fontsize=10, top=2)
        self.AddCell(self.countCaption, cellPadding=(0, 0, 5, 0))
        self.countLabel = Label()
        cell = self.AddCell(self.countLabel, cellPadding=(5, 0, 5, 3))
        self.slotsErrorFrame = ErrorFrame(parent=cell, align=uiconst.TOALL, state=uiconst.UI_DISABLED, padBottom=3)
        label = Label(text=localization.GetByLabel('UI/Industry/ControlRange'), color=Color.GRAY, fontsize=10, top=2)
        self.AddCell(label, cellPadding=(0, 0, 5, 0))
        self.rangeLabel = Label()
        cell = self.AddCell(self.rangeLabel, cellPadding=(5, 0, 5, 0))
        self.rangeErrorFrame = ErrorFrame(parent=cell, align=uiconst.TOALL, state=uiconst.UI_DISABLED)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        if self.jobData:
            self.jobData.on_updated.connect(self.UpdateState)
        self.UpdateState()

    def UpdateState(self, *args):
        activityType = industryUIConst.GetActivityType(self.jobData.activityID)
        changed = self.activityType != activityType
        self.activityType = activityType
        if changed:
            uicore.animations.FadeOut(self, sleep=True, duration=0.1)
            if self.activityType == industryUIConst.MANUFACTURING:
                self.countCaption.text = localization.GetByLabel('UI/Industry/ManufacturingJobs')
            else:
                self.countCaption.text = localization.GetByLabel('UI/Industry/ScienceJobs')
        color = Color.RGBtoHex(*industryUIConst.GetActivityColor(self.activityType))
        self.countLabel.text = '%s / <color=%s>%s</color>' % (self.jobData.used_slots, color, self.jobData.max_slots)
        skillLabel = industryUIConst.GetControlRangeLabel(self.jobData.max_distance)
        self.rangeLabel.text = '<color=%s>%s' % (color, skillLabel)
        if changed:
            uicore.animations.FadeIn(self, duration=0.3)
        if self.jobData and self.jobData.HasError(industry.Error.SLOTS_FULL):
            self.slotsErrorFrame.Show()
        else:
            self.slotsErrorFrame.Hide()
        if self.jobData and self.jobData.HasError(industry.Error.FACILITY_DISTANCE):
            self.rangeErrorFrame.Show()
        else:
            self.rangeErrorFrame.Hide()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        JobsSummaryTooltipPanel(self.jobData, tooltipPanel)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def OnMouseEnter(self, *args):
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')
