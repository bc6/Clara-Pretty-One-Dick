#Embedded file name: eve/client/script/ui/shared/industry\submitButton.py
import math
from carbonui import const as uiconst, const
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.ui.shared.industry.views.industryTooltips import SubmitButtonTooltipPanel
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
import industry
import localization
import trinity
import uthread

class SubmitButton(Button):

    def ApplyAttributes(self, attributes):
        Button.ApplyAttributes(self, attributes)
        self.tooltipErrors = None
        self.jobData = attributes.jobData
        self.isStopPending = False
        self.isArrowsAnimating = False
        self.func = self.ClickFunc
        self.sr.label.uppercase = True
        self.sr.label.fontsize = 13
        self.sr.label.bold = True
        self.pattern = Sprite(name='bgGradient', bgParent=self, texturePath='res:/UI/Texture/Classes/Industry/CenterBar/buttonPattern.png', color=Color.GRAY2, idx=0)
        self.bg = Sprite(name='bg', bgParent=self, opacity=0.0, texturePath='res:/UI/Texture/Classes/Industry/CenterBar/buttonBg.png', color=Color.GRAY2, idx=0, state=uiconst.UI_HIDDEN)
        self.arrows = Sprite(bgParent=self, texturePath='res:/UI/Texture/Classes/Industry/CenterBar/arrowMask.png', textureSecondaryPath='res:/UI/Texture/Classes/Industry/CenterBar/arrows.png', spriteEffect=trinity.TR2_SFX_MODULATE, color=Color.GRAY2, idx=0)
        self.arrows.translationSecondary = (-0.16, 0)
        self.errorFrame = ErrorFrame(bgParent=self)
        self.errorFrame.Hide()

    def OnNewJobData(self, jobData):
        self.oldJobData = self.jobData
        self.jobData = jobData
        self.isStopPending = False
        if self.jobData:
            self.jobData.on_updated.connect(self.OnJobUpdated)
            self.jobData.on_errors.connect(self.OnJobUpdated)
        self.UpdateState()

    def OnJobUpdated(self, *args):
        self.UpdateState()

    def GetColor(self):
        if not self.jobData or self.jobData.status == industry.STATUS_DELIVERED:
            return Color.GRAY2
        if self.jobData.errors or self.isStopPending:
            return industryUIConst.COLOR_RED
        color = industryUIConst.GetJobColor(self.jobData)
        if self.jobData and self.jobData.status == industry.STATUS_UNSUBMITTED:
            color = Color(*color).SetAlpha(0.5).GetRGBA()
        return color

    def AnimateArrows(self):
        self.arrows.Show()
        if self.isArrowsAnimating:
            return
        uicore.animations.MorphVector2(self.arrows, 'translationSecondary', (0.16, 0.0), (-0.16, 0.0), duration=2.0, curveType=uiconst.ANIM_LINEAR, loops=uiconst.ANIM_REPEAT)
        self.isArrowsAnimating = True

    def StopAnimateArrows(self):
        if self.destroyed:
            return
        diff = math.fabs(-0.16 - self.arrows.translationSecondary[0])
        duration = diff / 0.16
        if diff:
            uicore.animations.MorphVector2(self.arrows, 'translationSecondary', self.arrows.translationSecondary, (-0.16, 0.0), duration=duration, curveType=uiconst.ANIM_LINEAR)
        self.isArrowsAnimating = False

    def HideArrows(self):
        self.StopAnimateArrows()
        self.arrows.Hide()

    def UpdateState(self):
        uicore.animations.FadeIn(self.sr.label)
        color = self.GetColor()
        underlayColor = Color(*color).SetBrightness(0.4).GetRGBA()
        self.underlay.SetFixedColor(underlayColor)
        blinkColor = Color(*color).SetSaturation(0.5).SetBrightness(0.9).GetRGBA()
        self.sr.hilite.SetRGBA(*blinkColor)
        for obj in (self.pattern, self.bg, self.arrows):
            uicore.animations.SpColorMorphTo(obj, obj.GetRGBA(), color, duration=0.3)

        self.UpdateLabel()
        if not self.jobData:
            return
        if self.jobData.errors:
            self.errorFrame.Show()
            self.HideArrows()
        else:
            self.errorFrame.Hide()
            self.arrows.Show()
        if self.jobData.status == industry.STATUS_INSTALLED:
            if not self.oldJobData or self.oldJobData.status != industry.STATUS_INSTALLED:
                self.AnimateArrows()
        elif self.jobData.status == industry.STATUS_DELIVERED:
            self.HideArrows()
        else:
            self.StopAnimateArrows()
        if self.jobData.status == industry.STATUS_READY:
            self.Blink(time=3000)
        else:
            self.Blink(False)
        if self.jobData and self.jobData.status > industry.STATUS_READY:
            self.Disable()
        else:
            self.Enable()

    def UpdateLabel(self):
        if not self.jobData or self.jobData.status == industry.STATUS_UNSUBMITTED:
            label = 'UI/Industry/Start'
        elif self.jobData.status in (industry.STATUS_INSTALLED, industry.STATUS_PAUSED):
            if self.isStopPending:
                label = 'UI/Common/Confirm'
            else:
                label = 'UI/Industry/Stop'
        elif self.jobData.status == industry.STATUS_READY:
            label = 'UI/Industry/Deliver'
        else:
            label = None
        if label:
            text = localization.GetByLabel(label)
            if self.text != text:
                self.SetLabelAnimated(text)
        else:
            self.SetLabel('')

    def SetLabelAnimated(self, text):
        uthread.new(self._SetLabelAnimated, text)

    def _SetLabelAnimated(self, text):
        uicore.animations.FadeOut(self.sr.label, duration=0.15, sleep=True)
        self.SetLabel(text)
        uicore.animations.FadeIn(self.sr.label, duration=0.3)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if self.tooltipErrors is not None:
            errors = self.tooltipErrors
            self.tooltipErrors = None
        else:
            errors = self.jobData.errors
        SubmitButtonTooltipPanel(status=self.jobData.status, errors=errors, tooltipPanel=tooltipPanel)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def ClickFunc(self, *args):
        if self.jobData.IsInstalled():
            if self.jobData.status == industry.STATUS_READY:
                sm.GetService('industrySvc').CompleteJob(self.jobData.jobID)
                sm.GetService('audio').SendUIEvent('ind_jobDelivered')
            elif self.isStopPending:
                try:
                    sm.GetService('industrySvc').CancelJob(self.jobData.jobID)
                finally:
                    self.isStopPending = False
                    self.UpdateState()

            else:
                self.isStopPending = True
                self.UpdateState()
        else:
            try:
                self.Disable()
                if not self.jobData.errors:
                    self.AnimateArrows()
                sm.GetService('industrySvc').InstallJob(self.jobData)
                sm.GetService('audio').SendUIEvent('ind_jobStarted')
            except UserError as exception:
                if getattr(exception, 'msg', None) == 'IndustryValidationError':
                    self.tooltipErrors = exception.args[1]['errors']
                    uicore.uilib.tooltipHandler.RefreshTooltipForOwner(self)
                raise
            finally:
                self.Enable()
                self.StopAnimateArrows()

    def OnMouseEnter(self, *args):
        Button.OnMouseEnter(self, *args)
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')
