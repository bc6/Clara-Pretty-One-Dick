#Embedded file name: eve/client/script/ui/shared/industry/views\outcomeItemContainer.py
from carbonui.const import CENTER
from carbonui.primitives.container import Container
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.sprite import Sprite, VideoSprite
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import EveLabelLargeBold
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay, FrameUnderlay
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.industryUIConst import GetJobColor
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.ui.shared.industry.views.industryTooltips import OutcomeTooltipPanel
from eve.client.script.ui.shared.preview import PreviewContainer
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
from eve.client.script.ui.util.uix import GetTechLevelIconPathAndHint
from eve.common.script.sys.eveCfg import IsPreviewable
import industry
import carbonui.const as uiconst
from utillib import KeyVal
import trinity
import blue
import uthread

class OutcomeItemContainer(Container):
    default_state = uiconst.UI_NORMAL
    default_clipChildren = True
    __notifyevents__ = ['OnIndustryViewExpandCollapse']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.jobData = attributes.jobData
        self.videoThread = None
        self.iconCont = Container(name='iconCont', parent=self, align=CENTER, state=uiconst.UI_NORMAL, width=64, height=64)
        self.errorFrame = ErrorFrame(parent=self, align=uiconst.CENTER, pos=(0, 0, 64, 64), state=uiconst.UI_HIDDEN)
        self.qtyLabel = EveLabelLargeBold(parent=self, align=CENTER, top=42)
        FrameUnderlay(name='bgVignette', parent=self, texturePath='res:/UI/Texture/Classes/Industry/Output/bgVignette.png', cornerSize=30)
        self.videoCont = Container(name='videoCont', parent=self, align=uiconst.CENTER, width=324, height=199)
        self.previewContFill = FillUnderlay(parent=self)
        self.previewCont = PreviewContainer(parent=self, align=uiconst.TOALL, state=uiconst.UI_HIDDEN)
        self.leftProbabilityGradient = GradientSprite(name='leftProbabilityGradient', parent=self, align=uiconst.CENTERLEFT, state=uiconst.UI_HIDDEN, pos=(0, 0, 160, 64), rgbData=((0, (1.0, 1.0, 1.0)),), alphaData=((0.0, 0.5), (1.0, 0.0)))
        self.rightProbabilityGradient = GradientSprite(name='rightProbabilityGradient', parent=self, align=uiconst.CENTERRIGHT, state=uiconst.UI_HIDDEN, pos=(0, 0, 160, 64), rgbData=((0, (1.0, 1.0, 1.0)),), alphaData=((0.0, 0.0), (1.0, 0.5)))
        self.previewCont.navigation.LoadTooltipPanel = self.LoadIconContTooltipPanel
        self.previewCont.navigation.GetTooltipDelay = self.GetIconContTooltipDelay
        self.previewCont.navigation.GetMenu = self.GetMenu
        self.iconCont.LoadTooltipPanel = self.LoadIconContTooltipPanel
        self.iconCont.GetTooltipDelay = self.GetIconContTooltipDelay
        self.iconCont.OnMouseEnter = self.OnIconContMouseEnter
        self.iconCont.OnMouseExit = self.OnIconContMouseExit
        self.iconCont.OnClick = self.OnIconContClick
        self.iconCont.GetMenu = self.GetMenu
        self.iconCont.GetDragData = self.GetIconContDragData
        self.iconCont.isDragObject = True
        self.techIcon = Sprite(name='techIcon', parent=self.iconCont, width=16, height=16)
        self.icon = Icon(parent=self.iconCont, align=CENTER, state=uiconst.UI_DISABLED)
        self.bgCont = Container(name='bgCont', parent=self, align=uiconst.CENTER, width=201, height=192)
        self.bg = Sprite(bgParent=self.bgCont, texturePath='res:/UI/Texture/Classes/Industry/Output/itemBg.png')
        self.itemPattern = Sprite(bgParent=self.bgCont, texturePath='res:/UI/Texture/Classes/Industry/Output/itemBgColor.png')
        self.UpdateState()
        self.AnimEntry()

    def OnIndustryViewExpandCollapse(self):
        if not self.previewCont:
            return
        isCollapsed = settings.user.ui.Get('industryWndIsViewCollapsed', False)
        if not isCollapsed:
            self.AnimFadeSceneContIn()
        else:
            self.previewCont.Hide()
            self.previewContFill.opacity = 1.0

    def AnimFadeSceneContIn(self):
        self.previewCont.Hide()
        self.previewContFill.opacity = 1.0
        blue.synchro.SleepWallclock(250)
        self.previewCont.Show()
        uicore.animations.FadeTo(self.previewContFill, 1.0, 0.0, duration=0.6)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.UpdateState()
        if self.jobData:
            self.jobData.on_updated.connect(self.UpdateState)
        self.AnimEntry()

    def UpdateState(self, *args):
        if not self.jobData:
            self.previewCont.Hide()
            return
        typeID = self.jobData.GetProductTypeID()
        if IsPreviewable(typeID) and self.jobData.activityID == industry.MANUFACTURING:
            self.previewCont.Show()
            self.iconCont.Hide()
            newModel = self.previewCont.PreviewType(typeID)
            if newModel:
                self.previewContFill.Show()
                self.previewContFill.opacity = 1.0
                self.previewCont.AnimEntry(1.5, 0.0, 0.5, -0.3)
                self.previewCont.sceneContainer.scene.sunDirection = (-0.5, -1.0, -1.0)
            self.bg.Hide()
            self.qtyLabel.top = 86
            self.leftProbabilityGradient.Hide()
            self.rightProbabilityGradient.Hide()
        else:
            self.iconCont.Show()
            self.previewCont.Hide()
            self.bg.Show()
            self.qtyLabel.top = 42
            if self.jobData.activityID == industry.RESEARCH_MATERIAL:
                self.icon.LoadIcon('res:/UI/Texture/Classes/Industry/iconME.png')
                self.icon.width = self.icon.height = 17
                self.techIcon.texturePath = None
            elif self.jobData.activityID == industry.RESEARCH_TIME:
                self.icon.LoadIcon('res:/UI/Texture/Classes/Industry/iconTE.png')
                self.techIcon.texturePath = None
                self.icon.width = self.icon.height = 16
            else:
                isCopy = self.jobData.activityID in (industry.COPYING, industry.INVENTION)
                oldTypeID = self.icon.typeID
                self.icon.LoadIconByTypeID(typeID, ignoreSize=True, isCopy=isCopy)
                self.icon.width = self.icon.height = 64
                texturePath, hint = GetTechLevelIconPathAndHint(typeID)
                self.techIcon.texturePath = texturePath
                self.techIcon.hint = hint
                if oldTypeID != typeID:
                    uicore.animations.FadeTo(self.icon, 0.0, 1.0, duration=0.6)
            if self.jobData.activityID == industry.INVENTION:
                width = self.jobData.probability * 160
                color = GetJobColor(self.jobData)
                for gradient in (self.leftProbabilityGradient, self.rightProbabilityGradient):
                    gradient.Show()
                    gradient.SetRGBA(*color)
                    uicore.animations.MorphScalar(gradient, 'width', gradient.width, width, duration=0.6)

            else:
                self.leftProbabilityGradient.Hide()
                self.rightProbabilityGradient.Hide()
        if self.jobData and self.jobData.product:
            self.iconCont.opacity = 1.0
            uicore.animations.FadeTo(self.bgCont, self.bgCont.opacity, 1.0, duration=0.3)
            self.errorFrame.Hide()
        else:
            self.iconCont.opacity = 0.0
            uicore.animations.FadeTo(self.bgCont, 0.3, 1.0, duration=2.0, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
            self.errorFrame.Show()
        self.UpdateOutputQty()
        self.StopVideo()
        if self.jobData.status == industry.STATUS_DELIVERED:
            self.PlayVideoDelivered()

    def PlayVideoDelivered(self):
        self.PlayVideo('res:/video/Industry/deliveredIntro.bk2', 'res:/video/Industry/deliveredOutro.bk2', industryUIConst.GetActivityColor(self.jobData.activityID))

    def PlayVideoFailed(self):
        self.PlayVideo('res:/video/Industry/failedIntro.bk2', 'res:/video/Industry/failedOutro.bk2', industryUIConst.COLOR_NOTREADY)

    def StopVideo(self):
        if self.videoThread:
            self.videoThread.kill()
            self.videoCont.Flush()

    def PlayVideo(self, introPath, outroPath, color):
        self.videoThread = uthread.new(self._PlayVideo, introPath, outroPath, color)

    def _PlayVideo(self, introPath, outroPath, color):
        self.videoCont.Flush()
        videoSprite = VideoSprite(parent=self.videoCont, align=uiconst.TOALL, spriteEffect=trinity.TR2_SFX_COPY, videoPath=introPath, color=color)
        while not videoSprite.isFinished:
            blue.synchro.Yield()

        blue.synchro.SleepWallclock(3000)
        videoSprite.Close()
        videoSprite = VideoSprite(parent=self.videoCont, align=uiconst.TOALL, spriteEffect=trinity.TR2_SFX_COPY, videoPath=outroPath, color=color)
        while not videoSprite.isFinished:
            blue.synchro.Yield()

        uicore.animations.FadeOut(videoSprite, callback=videoSprite.Close)

    def GetMenu(self):
        abstractInfo = KeyVal(bpData=self.GetBpData())
        return sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.jobData.product.typeID, ignoreMarketDetails=False, abstractInfo=abstractInfo)

    def LoadIconContTooltipPanel(self, tooltipPanel, *args):
        if self.jobData.activityID in (industry.RESEARCH_TIME, industry.RESEARCH_MATERIAL):
            return
        self.tooltipPanel = OutcomeTooltipPanel(jobData=self.jobData, tooltipPanel=tooltipPanel)

    def GetIconContTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def GetIconContDragData(self, *args):
        typeID = self.jobData.GetProductTypeID()
        if not typeID:
            return
        if isinstance(self.jobData.product, industry.Blueprint):
            bpData = self.jobData.product.GetCopy()
        else:
            bpData = None
        return [KeyVal(__guid__='uicls.GenericDraggableForTypeID', typeID=typeID, label=cfg.invtypes.Get(typeID).name, bpData=bpData)]

    def UpdateOutputQty(self):
        if not self.jobData or not self.jobData.product:
            self.qtyLabel.text = ''
            return
        self.qtyLabel.text = self.jobData.GetProductAmountLabel()

    def AnimEntry(self):
        if not self.jobData:
            return
        uicore.animations.FadeTo(self.itemPattern, 0.0, 1.0, duration=0.6, timeOffset=1.35)
        uicore.animations.FadeTo(self.previewContFill, self.previewContFill.opacity, 0.0, duration=0.6, timeOffset=0, callback=self.previewContFill.Hide)

    def GetBpData(self):
        if not isinstance(self.jobData.product, industry.Blueprint):
            return None
        return self.jobData.product.GetCopy()

    def OnIconContClick(self, *args):
        if not self.jobData:
            return
        if self.jobData.activityID in (industry.RESEARCH_MATERIAL, industry.RESEARCH_TIME):
            return
        typeID = self.jobData.GetProductTypeID()
        if not typeID:
            return
        sm.GetService('info').ShowInfo(typeID, abstractinfo=KeyVal(bpData=self.GetBpData()))
        sm.GetService('audio').SendUIEvent('ind_click')

    def OnIconContMouseEnter(self, *args):
        uicore.animations.FadeTo(self.bg, self.bg.opacity, 1.5, duration=0.15)
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')

    def OnIconContMouseExit(self, *args):
        uicore.animations.FadeTo(self.bg, self.bg.opacity, 1.0, duration=0.3)
