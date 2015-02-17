#Embedded file name: eve/client/script/ui/shared/industry/views\baseView.py
from carbonui.const import CENTERTOP, UI_DISABLED, TOALL, CENTERBOTTOM, ANIM_WAVE
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.util.color import Color
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.client.script.ui.shared.industry import industryUIConst
import industry
from localization import GetByLabel
from eve.client.script.ui.control.eveLabel import EveHeaderMedium
from eve.client.script.ui.shared.industry.industryUIConst import GetJobColor, ACTIVITY_NAMES, ACTIVITY_AUDIOEVENTS
from eve.client.script.ui.shared.industry.views.OutputCont import OutputCont
from eve.client.script.ui.shared.industry.views.blueprintCenter import BlueprintCenter
from eve.client.script.ui.shared.industry.views.materialGroups import MaterialGroups
import carbonui.const as uiconst
import uthread
import telemetry

class BaseView(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = attributes.jobData
        if self.jobData:
            self.jobData.on_updated.connect(self.OnJobUpdated)
            self.jobData.on_errors.connect(self.OnJobErrors)
        self.oldJobData = None
        self.UpdateColor()
        self.bgGradientThread = None
        self.topCont = Container(name='topCont', parent=self, align=uiconst.TOTOP, height=18)
        self.mainCont = Container(parent=self, align=uiconst.TOTOP, height=400)
        UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.topCont, align=uiconst.TOPLEFT, GetUtilMenu=self.GetUtilMenuSettings, texturePath='res:/UI/Texture/SettingsCogwheel.png', iconSize=18, pos=(4, 0, 18, 18))
        self.topContLabel = EveHeaderMedium(name='topContLabel', parent=self.topCont, align=uiconst.TOPLEFT, top=2, left=24)
        self.blueprintCenter = BlueprintCenter(parent=self.mainCont, jobData=self.jobData)
        self.inputsCont = MaterialGroups(parent=self.mainCont, jobData=self.jobData, padLeft=4)
        self.outputCont = OutputCont(parent=self.mainCont, padRight=6, jobData=self.jobData)
        self.ConstructBackground()
        self.UpdateState()
        self.AnimEntry()

    def GetUtilMenuSettings(self, menuParent):
        menuParent.AddHeader(text=GetByLabel('UI/Industry/InputMaterialValues'))
        showTotalRequired = settings.char.ui.Get('inputMaterialShowTotalRequired', True)
        menuParent.AddRadioButton(text=GetByLabel('UI/Industry/ShowTotalRequired'), checked=showTotalRequired, callback=(self.OnInputMaterialValueSetting, True))
        menuParent.AddRadioButton(text=GetByLabel('UI/Industry/ShowMissing'), checked=not showTotalRequired, callback=(self.OnInputMaterialValueSetting, False))

    def OnInputMaterialValueSetting(self, value):
        settings.char.ui.Set('inputMaterialShowTotalRequired', value)
        sm.ScatterEvent('OnIndustryMaterialValueSettingChanged')

    def ConstructBackground(self):
        self.bgTransform = Transform(name='bgTransform', parent=self.mainCont, align=CENTERBOTTOM, state=UI_DISABLED, scalingCenter=(0.5, 0.5), width=400, height=400)
        Sprite(bgParent=self.bgTransform, align=TOALL, texturePath='res:/UI/Texture/classes/Industry/Center/bgCircle.png')
        self.bgBorder = Sprite(bgParent=self.bgTransform, align=TOALL, texturePath='res:/UI/Texture/classes/Industry/Center/bgCircleBorder.png', color=self.color)
        self.bgGradient = Sprite(parent=self.bgTransform, align=uiconst.CENTER, texturePath='res:/UI/Texture/classes/Industry/Center/bgGlowRing.png', color=self.color, opacity=0.0, width=432, height=432)

    def UpdateColor(self):
        self.color = GetJobColor(self.jobData)

    @telemetry.ZONE_METHOD
    def OnNewJobData(self, jobData):
        self.oldJobData = self.jobData
        if jobData:
            sm.GetService('audio').SendUIEvent(ACTIVITY_AUDIOEVENTS[jobData.activityID])
            jobData.on_updated.connect(self.OnJobUpdated)
            jobData.on_errors.connect(self.OnJobErrors)
        self.jobData = jobData
        self.UpdateColor()
        self.blueprintCenter.OnNewJobData(jobData)
        self.inputsCont.OnNewJobData(jobData)
        self.outputCont.OnNewJobData(jobData)
        self.UpdateState()
        self.AnimEntry()

    def AnimEntry(self):
        if self.bgGradientThread:
            self.bgGradientThread.kill()
            self.bgGradientThread = None
        if self.jobData:
            if self.jobData.IsInstalled():
                self.bgGradientThread = uthread.new(self.AnimFadeBgGradient)
            elif not self.oldJobData:
                uicore.animations.Tr2DScaleTo(self.bgTransform, self.bgTransform.scale, (1.0, 1.0), duration=0.5)
                uicore.animations.FadeTo(self.bgTransform, self.bgTransform.opacity, 1.0, duration=1.0)
            else:
                self.bgGradientThread = uthread.new(self.AnimFadeBgTransform)
            color = Color(*self.color).SetAlpha(0.3).GetRGBA()
            uicore.animations.SpColorMorphTo(self.bgBorder, endColor=color, duration=1.0)
            if not self.jobData.IsInstalled():
                uicore.animations.FadeOut(self.bgGradient, duration=0.3)
        else:
            uicore.animations.Tr2DScaleTo(self.bgTransform, (0.98, 0.98), (0.95, 0.95), duration=10.0, curveType=ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
            uicore.animations.FadeTo(self.bgTransform, 1.0, 0.1, duration=10.0, curveType=ANIM_WAVE)
            uicore.animations.FadeOut(self.bgGradient, duration=0.6)

    def AnimFadeBgTransform(self):
        uicore.animations.Tr2DScaleTo(self.bgTransform, self.bgTransform.scale, (1.0, 1.0), duration=0.3)
        uicore.animations.FadeTo(self.bgTransform, self.bgTransform.opacity, 1.0, duration=0.3, sleep=True)
        uicore.animations.Tr2DScaleTo(self.bgTransform, (1.0, 1.0), (0.99, 0.99), duration=1.0, curveType=ANIM_WAVE)
        uicore.animations.FadeTo(self.bgTransform, 1.0, 0.3, duration=1.0, curveType=ANIM_WAVE)

    def AnimFadeBgGradient(self):
        if self.jobData.activityID == industry.MANUFACTURING:
            color = industryUIConst.COLOR_MANUFACTURING
            color = Color(*color).SetAlpha(0.2).GetRGBA()
        else:
            color = industryUIConst.COLOR_SCIENCE
            color = Color(*color).SetAlpha(0.5).GetRGBA()
        uicore.animations.Tr2DScaleTo(self.bgTransform, self.bgTransform.scale, (1.0, 1.0), duration=0.3)
        if self.jobData.status == industry.STATUS_READY:
            opacity = 1.2
        else:
            opacity = 0.3
        uicore.animations.SpColorMorphTo(self.bgGradient, endColor=color, duration=0.9)
        uicore.animations.FadeTo(self.bgTransform, self.bgTransform.opacity, opacity, duration=0.3, sleep=True)
        if self.jobData.status == industry.STATUS_DELIVERED:
            uicore.animations.FadeTo(self.bgTransform, self.bgTransform.opacity, 1.2, duration=2.5)
        elif self.jobData.status >= industry.STATUS_READY:
            uicore.animations.FadeTo(self.bgTransform, self.bgTransform.opacity, 1.8, duration=2.5, curveType=ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
        else:
            uicore.animations.Tr2DScaleTo(self.bgTransform, (1.0, 1.0), (0.985, 0.985), duration=5.0, curveType=ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
            uicore.animations.FadeTo(self.bgTransform, 0.3, 1.0, duration=5.0, curveType=ANIM_WAVE, loops=uiconst.ANIM_REPEAT)

    def OnJobUpdated(self, job):
        self.OnRunsChanged()

    def OnJobErrors(self, job, errors):
        self.OnRunsChanged()

    def OnRunsChanged(self):
        self.outputCont.OnRunsChanged()
        self.blueprintCenter.OnRunsChanged()
        self.inputsCont.OnRunsChanged()

    def UpdateState(self):
        if not self.jobData:
            text = ''
        else:
            jobName = GetByLabel(ACTIVITY_NAMES[self.jobData.activityID])
            text = self.jobData.blueprint.GetName()
        self.topContLabel.text = text
