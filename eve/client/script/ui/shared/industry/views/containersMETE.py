#Embedded file name: eve/client/script/ui/shared/industry/views\containersMETE.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
from carbonui.util.color import Color
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.gauge import Gauge
from eve.client.script.ui.control.themeColored import FillThemeColored
from eve.client.script.ui.shared.industry.industryUIConst import COLOR_NOTREADY, COLOR_FRAME, COLOR_READY, GetJobColor
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
import industry
from industry.const import MIN_MATERIAL_EFFICIENCY, MIN_TIME_EFFICIENCY, MAX_TIME_EFFICIENCY, MAX_MATERIAL_EFFICIENCY
import localization

class BaseContainerMETE(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.value = 0.0
        iconPath = attributes.iconPath
        iconSize = attributes.iconSize
        minValue = attributes.minValue
        maxValue = attributes.maxValue
        showBG = attributes.get('showBG', True)
        isCompact = attributes.get('isCompact', False)
        self.jobData = attributes.jobData
        self.gauge = Gauge(parent=self, align=uiconst.TOBOTTOM, state=uiconst.UI_DISABLED, height=6, gaugeHeight=6, padTop=1, backgroundColor=(1.0, 1.0, 1.0, 0.05))
        if isCompact:
            self.icon = None
            self.valueLabel = None
            return
        mainCont = Container(name='mainCont', parent=self)
        if showBG:
            self.bg = StretchSpriteHorizontal(bgParent=mainCont, texturePath='res:/UI/Texture/Classes/Industry/Center/bgMETE.png')
            FillThemeColored(bgParent=self, opacity=0.5)
        else:
            self.bg = None
        left = 8 if showBG else 2
        self.icon = Sprite(name='icon', parent=mainCont, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, pos=(left,
         3,
         self.ICONSIZE,
         self.ICONSIZE), texturePath=self.ICONPATH, opacity=0.6)
        self.valueLabel = EveLabelMediumBold(parent=mainCont, align=uiconst.TOPRIGHT, top=4, left=left)
        self.removeIcon = Sprite(parent=mainCont, align=uiconst.CENTERRIGHT, state=uiconst.UI_HIDDEN, texturePath='res:/ui/texture/icons/73_16_45.png', pos=(0, 0, 12, 12), color=Color.RED, hint=localization.GetByLabel('UI/Industry/PreviewModeHint'))
        self.removeIcon.OnClick = self.OnRemoveIconClick
        self.previewEdit = SinglelineEdit(name='previewEdit', parent=mainCont, align=uiconst.CENTERRIGHT, state=uiconst.UI_HIDDEN, ints=(0, self.MAXVAL), OnChange=self.OnPreviewEdit, pos=(12, 0, 34, 20))
        self.errorFrame = ErrorFrame(bgParent=self, padding=(1, 1, 1, 8))

    def SetValue(self, value):
        if self.value * (value or 1) < 0.0:
            self.gauge.SetValueInstantly(0.0)
        self.value = value
        if value < 0:
            self.gauge.SetGaugeAlign(uiconst.TORIGHT_PROP)
            self.gauge.SetValue(float(value) / self.MINVAL)
            self.gauge.SetColor(COLOR_NOTREADY)
        else:
            self.gauge.SetGaugeAlign(uiconst.TOLEFT_PROP)
            self.gauge.SetValue(float(value) / self.MAXVAL)
            self.gauge.SetColor(COLOR_READY)
        if not self.valueLabel:
            return
        if value < 0:
            self.valueLabel.text = '<color=%s>%s%%' % (Color.RGBtoHex(*COLOR_NOTREADY), value)
        elif value == 0:
            self.valueLabel.text = '<color=%s>%s%%' % (Color.RGBtoHex(*COLOR_FRAME), value)
        else:
            self.valueLabel.text = '<color=%s>%s%%' % (Color.RGBtoHex(*COLOR_READY), value)

    def OnMouseEnter(self, *args):
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')

    def OnRemoveIconClick(self):
        self.ExitPreviewMode()

    def EnterPreviewMode(self):
        if not self.IsPreviewEnabled():
            return
        self.previewEdit.Show()
        self.previewEdit.SetValue(self.GetPreviewEditValue())
        self.valueLabel.Hide()
        self.errorFrame.Show()
        self.removeIcon.Show()
        uicore.registry.SetFocus(self.previewEdit)

    def ExitPreviewMode(self):
        self.previewEdit.Hide()
        self.valueLabel.Show()
        self.errorFrame.Hide()
        self.removeIcon.Hide()
        if self.jobData:
            self.jobData.timeEfficiency = None
            self.jobData.materialEfficiency = None
            self.jobData.update(self.jobData)

    def OnClick(self, *args):
        self.EnterPreviewMode()

    def OnMouseEnter(self, *args):
        if self.bg and self.IsPreviewEnabled():
            uicore.animations.FadeTo(self.bg, self.bg.opacity, 1.5, duration=0.3)

    def OnMouseExit(self, *args):
        if self.bg:
            uicore.animations.FadeTo(self.bg, self.bg.opacity, 1.0, duration=0.3)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.ExitPreviewMode()

    def IsPreviewEnabled(self):
        if not self.jobData or self.jobData.activityID != industry.MANUFACTURING or self.jobData.jobID:
            return False
        return True

    def IsPreviewActive(self):
        return self.errorFrame.display

    def GetHint(self):
        if self.IsPreviewEnabled() and not self.IsPreviewActive():
            return '<br><br>' + localization.GetByLabel('UI/Industry/EnterPreviewModeHint')
        return ''


class ContainerTE(BaseContainerMETE):
    ICONPATH = 'res:/UI/Texture/Classes/Industry/iconTE.png'
    ICONSIZE = 16
    MINVAL = MIN_TIME_EFFICIENCY
    MAXVAL = MAX_TIME_EFFICIENCY

    def GetHint(self):
        hint = '<b>%s</b><br>%s' % (localization.GetByLabel('UI/Industry/TimeEfficiency'), localization.GetByLabel('UI/Industry/TimeEfficiencyHint'))
        hint += BaseContainerMETE.GetHint(self)
        return hint

    def OnPreviewEdit(self, *args):
        self.jobData.timeEfficiency = int(self.previewEdit.GetValue())
        self.jobData.update(self.jobData)

    def GetPreviewEditValue(self):
        return self.jobData.timeEfficiency


class ContainerME(BaseContainerMETE):
    ICONPATH = 'res:/UI/Texture/Classes/Industry/iconME.png'
    ICONSIZE = 17
    MINVAL = MIN_MATERIAL_EFFICIENCY
    MAXVAL = MAX_MATERIAL_EFFICIENCY

    def GetHint(self):
        hint = '<b>%s</b><br>%s' % (localization.GetByLabel('UI/Industry/MaterialEfficiency'), localization.GetByLabel('UI/Industry/MaterialEfficiencyHint'))
        hint += BaseContainerMETE.GetHint(self)
        return hint

    def OnPreviewEdit(self, *args):
        self.jobData.materialEfficiency = int(self.previewEdit.GetValue())
        self.jobData.update(self.jobData)

    def GetPreviewEditValue(self):
        return self.jobData.materialEfficiency
