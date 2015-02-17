#Embedded file name: eve/client/script/ui/shared/industry/views\material.py
from math import pi
from carbonui.const import UI_NORMAL, CENTERTOP, UI_DISABLED, CENTERBOTTOM, TOALL, BOTTOMLEFT
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbon.common.script.util.format import FmtAmt
from eve.client.script.ui.control.entries import Item
from eve.client.script.ui.control.eveIcon import Icon, ItemIcon
from eve.client.script.ui.control.eveLabel import Label, EveLabelMedium
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay
from eve.client.script.ui.control.gauge import Gauge
from eve.client.script.ui.shared.industry.industryUIConst import COLOR_READY, COLOR_FRAME, COLOR_NOTREADY
import carbonui.const as uiconst
from eve.client.script.ui.shared.industry.views.industryTooltips import MaterialTooltipPanel
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
import listentry
import localization
import trinity
from utillib import KeyVal
OPACITY_DEFAULT = 0.5
OPACITY_HOVER = 1.5

class MaterialBase(Container):
    __notifyevents__ = ['OnIndustryMaterialValueSettingChanged']
    default_name = 'Material'
    default_state = UI_NORMAL
    default_width = 45
    default_height = 60
    isDragObject = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.jobData = attributes.jobData
        self.materialData = attributes.materialData
        self.materialData.on_updated.connect(self.OnMaterialUpdated)
        self.materialData.on_errors.connect(self.OnMaterialErrors)
        self.isReady = None
        self.icon = ItemIcon(parent=self, typeID=self.materialData.typeID, align=CENTERTOP, state=UI_DISABLED, pos=(0, 6, 32, 32))
        self.label = Label(parent=self, align=CENTERBOTTOM, top=-1, fontsize=10)
        self.bgGlow = Sprite(name='bgGlow', parent=self, align=TOALL, state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/bgGlow.png', color=COLOR_READY, opacity=OPACITY_DEFAULT)
        self.bgFrame = Sprite(name='bgFrame', parent=self, align=TOALL, state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/bgFrame.png', color=COLOR_FRAME)
        FillUnderlay(bgParent=self, opacity=0.5)
        Sprite(name='valueBg', parent=self, align=TOALL, state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/valueBg.png', color=COLOR_FRAME, opacity=0.1)
        self.gauge = Gauge(parent=self, align=BOTTOMLEFT, state=UI_DISABLED, pos=(0,
         13,
         self.width + 1,
         0), gaugeHeight=3, gradientBrightnessFactor=1.0, backgroundColor=(0, 0, 0, 0))
        self.bgFill = Sprite(name='bgFill', parent=self, align=TOALL, state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/bg.png', color=COLOR_FRAME, opacity=0.1)
        self.ConstructBackground()
        self.UpdateState()

    def ConstructBackground(self):
        pass

    def OnMaterialUpdated(self, material):
        self.UpdateState()

    def OnMaterialErrors(self, material, errors):
        self.UpdateState()

    def UpdateState(self):
        pass

    def IsReady(self):
        return self.materialData.valid

    def OnMouseEnter(self, *args):
        uicore.animations.FadeIn(self.bgGlow, OPACITY_HOVER, duration=0.15)
        sm.GetService('audio').SendUIEvent('ind_mouseEnter')

    def OnMouseExit(self, *args):
        uicore.animations.FadeIn(self.bgGlow, OPACITY_DEFAULT, duration=0.3)

    def GetDragData(self):
        return self.icon.GetDragData()

    def OnIndustryMaterialValueSettingChanged(self):
        self.UpdateLabel()

    def UpdateLabel(self):
        if settings.char.ui.Get('inputMaterialShowTotalRequired', True):
            value = self.materialData.quantity
        else:
            value = self.materialData.missing
        self.label.text = FmtAmt(value, 'ss')


class Material(MaterialBase):

    def ConstructBackground(self):
        self.patternNotReady = Sprite(name='patternNotReady', parent=self, align=TOALL, state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/bgNotReady.png', color=COLOR_NOTREADY, opacity=0.0)

    def UpdateState(self):
        self.ratio = self.materialData.ratio
        self.gauge.SetValue(self.ratio)
        self.UpdateLabel()
        duration = 0.3
        wasReady = self.isReady
        color = COLOR_FRAME if self.IsReady() else COLOR_NOTREADY
        uicore.animations.SpColorMorphTo(self.bgFrame, self.bgFrame.GetRGBA(), color, duration=duration, includeAlpha=False)
        if wasReady is not None and wasReady != self.isReady:
            uicore.animations.FadeTo(self.bgFill, 0.8, 0.1, duration=0.3)
        color = COLOR_READY if self.IsReady() else COLOR_NOTREADY
        uicore.animations.SpColorMorphTo(self.bgGlow, self.bgGlow.GetRGBA(), color, duration=duration, includeAlpha=False)
        self.gauge.SetColor(color, animDuration=duration)
        opacity = 0.0 if self.IsReady() else 1.0
        uicore.animations.FadeIn(self.patternNotReady, opacity, duration=duration)
        if wasReady and not self.isReady:
            sm.GetService('audio').SendUIEvent('ind_insufficientMaterials')
        elif not wasReady and self.isReady:
            sm.GetService('audio').SendUIEvent('ind_sufficientMaterials')

    def LoadTooltipPanel(self, tooltipPanel, *args):
        self.tooltipPanel = MaterialTooltipPanel(jobData=self.jobData, materialData=self.materialData, tooltipPanel=tooltipPanel)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def GetMenu(self):
        menu = sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.materialData.typeID, ignoreMarketDetails=False)
        menu.insert(0, (MenuLabel('UI/Inventory/ItemActions/BuyThisType'), sm.GetService('menu').QuickBuy, (self.materialData.typeID, self.materialData.missing)))
        return menu

    def OnClick(self, *args):
        bpData = sm.GetService('blueprintSvc').GetBlueprintByProduct(self.materialData.typeID)
        if bpData:
            from eve.client.script.ui.shared.industry.industryWnd import Industry
            Industry.OpenOrShowBlueprint(blueprintTypeID=bpData.blueprintTypeID)
        else:
            sm.GetService('info').ShowInfo(self.materialData.typeID)
        sm.GetService('audio').SendUIEvent('ind_click')


class OptionalMaterial(MaterialBase):

    def ApplyAttributes(self, attributes):
        MaterialBase.ApplyAttributes(self, attributes)
        self.gauge.Hide()

    def ConstructBackground(self):
        self.patternNotReady = Sprite(name='patternNotReady', parent=self, align=CENTERTOP, pos=(0, 0, 45, 45), state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/bgNotReadyOptional.png', textureSecondaryPath='res:/UI/Texture/Classes/Industry/Input/bgNotReadyOptionalGradient.png', spriteEffect=trinity.TR2_SFX_MODULATE, color=COLOR_FRAME, opacity=0.0)
        uicore.animations.MorphScalar(self.patternNotReady, 'rotationSecondary', 2 * pi, 0.0, duration=3.0, curveType=uiconst.ANIM_LINEAR, loops=uiconst.ANIM_REPEAT)
        self.bgOptional = Sprite(name='bgOptional', parent=self, align=TOALL, state=UI_DISABLED, texturePath='res:/UI/Texture/Classes/Industry/Input/bgOptional.png', opacity=0.3)

    def UpdateState(self):
        duration = 0.3
        self.UpdateLabel()
        opacity = 1.0 if self.materialData.valid else 0.5
        uicore.animations.FadeTo(self.bgFrame, self.bgFrame.opacity, opacity, duration=duration)
        opacity = 0.4 if self.materialData.valid else 0.25
        uicore.animations.FadeTo(self.bgOptional, self.bgOptional.opacity, opacity, duration=duration)
        uicore.animations.FadeTo(self.icon, 0.0, 1.0, duration=1.0)
        color = COLOR_READY if self.materialData.valid else (0.2, 0.2, 0.2, 1.0)
        uicore.animations.SpColorMorphTo(self.bgGlow, self.bgGlow.GetRGBA(), color, duration=duration, includeAlpha=False)
        if self.materialData.typeID:
            self.icon.SetTypeID(self.materialData.typeID)
            self.icon.Show()
        else:
            self.icon.Hide()
        opacity = 0.0 if self.materialData.typeID else 2.5
        uicore.animations.FadeIn(self.patternNotReady, opacity, duration=duration)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.margin = 4
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.width = 250
        OptionalItemTooltipPanel(materialData=self.materialData, callback=self.OnOptionalItemSelected, tooltipPanel=tooltipPanel)

    def OnClick(self, *args):
        sm.GetService('audio').SendUIEvent('ind_click')

    def OnOptionalItemSelected(self, typeID):
        self.materialData.select(typeID)


class OptionalItemTooltipPanel:

    def __init__(self, materialData, callback, tooltipPanel):
        tooltipPanel.margin = 8
        self.materialData = materialData
        self.callback = callback
        self.tooltipPanel = tooltipPanel
        if materialData.IsSelectable():
            text = localization.GetByLabel('UI/Industry/SelectInputMaterial')
        else:
            text = localization.GetByLabel('UI/Industry/SelectOptionalMaterial')
        label = EveLabelMedium(align=uiconst.TOTOP, text=text, padBottom=3)
        tooltipPanel.AddCell(label)
        scroll = Scroll(align=uiconst.TOPLEFT, width=250)
        scroll.OnSelectionChange = self.OnScrollSelectionChange
        scrollList = self.GetScrollContent()
        scroll.Load(contentList=scrollList)
        scroll.ScrollToSelectedNode()
        scroll.height = min(len(scrollList) * 29 + 2, 200)
        scroll.Confirm = self.Confirm
        tooltipPanel.AddCell(scroll)

    def GetScrollContent(self):
        entries = []
        for material in self.materialData.options:
            if material.typeID is None:
                data = KeyVal(label=localization.GetByLabel('UI/Industry/UseNoOptionalItem'), OnDblClick=self.OnNodeDblClick, typeID=None, height=29)
                entries.append(listentry.Get(decoClass=listentry.Generic, data=data))
            else:
                invType = cfg.invtypes.Get(material.typeID)
                data = KeyVal(typeID=material.typeID, label=invType.name, getIcon=True, hint=invType.description, isSelected=material.typeID == self.materialData.typeID, OnDblClick=self.OnNodeDblClick, isItemOwned=not material.missing)
                entry = listentry.Get(decoClass=OptionalMaterialEntry, data=data)
                entries.append(entry)

        entries = sorted(entries, key=lambda x: (x.typeID is not None, x.label))
        return entries

    def Confirm(self, *args):
        self.tooltipPanel.Close()

    def OnNodeDblClick(self, node):
        self.tooltipPanel.Close()

    def OnScrollSelectionChange(self, nodes):
        if not nodes:
            return
        self.callback(nodes[0].typeID)


class OptionalMaterialEntry(Item):

    def Load(self, node):
        Item.Load(self, node)
        if not node.isItemOwned:
            self.sr.icon.opacity = self.sr.label.opacity = 0.25
