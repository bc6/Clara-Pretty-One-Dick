#Embedded file name: eve/client/script/ui/shared/industry/views\industryTooltips.py
from collections import defaultdict
from carbonui import const as uiconst
from carbonui.control.menuLabel import MenuLabel
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
from eve.client.script.ui.control.eveIcon import ItemIcon
from eve.client.script.ui.control.eveLabel import EveLabelMedium, Label
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.systemCostIndexGauge import SystemCostIndexGauge
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.ui.shared.industry.views.industryCaptionLabel import IndustryCaptionLabel
from eve.client.script.ui.shared.industry.views.skillEntry import IndustrySkillEntry
from eve.common.script.util import industryCommon
from eve.common.script.util.eveFormat import FmtISK
import eve.client.script.ui.control.entries as listentry
import industry
from inventorycommon import const
import localization
from localization import GetByLabel
from localization.formatters import FormatNumeric
from utillib import KeyVal
MARGIN = (8, 8, 8, 0)
PADBOTTOM = (0, 0, 0, 8)

def AddMaterialGroupRow(materialGroupID, panel):
    cont = ContainerAutoSize(align=uiconst.TOPLEFT)
    icon = Sprite(parent=cont, align=uiconst.TOPLEFT, texturePath=industryUIConst.ICON_BY_INDUSTRYGROUP[materialGroupID], pos=(4, 0, 12, 12), color=industryUIConst.COLOR_FRAME)
    label = IndustryCaptionLabel(parent=cont, align=uiconst.TOPLEFT, text=localization.GetByLabel(industryUIConst.LABEL_BY_INDUSTRYGROUP[materialGroupID]), left=24)
    panel.AddCell(cont, colSpan=3, cellPadding=(0, 0, 0, 5))


def AddItemRow(panel, materialData):
    panel.AddCell(MaterialIconAndLabel(materialData=materialData), cellPadding=(0, 0, 0, 3))
    available = FormatNumeric(materialData.available, useGrouping=True)
    quantity = FormatNumeric(materialData.quantity, useGrouping=True)
    color = industryUIConst.COLOR_NOTREADY if materialData.errors else industryUIConst.COLOR_READY
    colorHex = Color.RGBtoHex(*color)
    label = EveLabelMedium(align=uiconst.CENTERRIGHT, text='<color=%s>%s / %s' % (colorHex, available, quantity))
    panel.AddCell(label, cellPadding=(8, 0, 0, 3))


def AddOutcomeRow(panel, product):
    panel.AddCell(MaterialIconAndLabel(materialData=product), cellPadding=(0, 0, 0, 0))
    label = EveLabelMedium(align=uiconst.CENTERRIGHT, text='x %s' % product.quantity)
    panel.AddCell(label, cellPadding=(8, 0, 0, 0))
    panel.AddSpacer(width=0, height=8, colSpan=2)


def AddPriceRow(panel, price):
    if not price:
        iskPrice = localization.GetByLabel('UI/Inventory/PriceUnavailable')
    else:
        iskPrice = FmtISK(price)
    label = EveLabelMedium(text=localization.GetByLabel('UI/Industry/TotalEstimatedPrice'), color=Color.GRAY)
    panel.AddCell(label)
    label = EveLabelMedium(align=uiconst.TOPRIGHT, text=iskPrice)
    panel.AddCell(label, cellPadding=(8, 0, 0, 0))
    panel.AddCell(cellPadding=PADBOTTOM, colSpan=2)


def AddTypeBonusRow(panel, text, bonusME = None, bonusTE = None):
    label = EveLabelMedium(text=text, color=Color.GRAY)
    panel.AddCell(label)
    if bonusME:
        label = EveLabelMedium(align=uiconst.TOPRIGHT, text=bonusME)
        panel.AddCell(label, cellPadding=(8, 0, 0, 0))
    if bonusTE:
        label = EveLabelMedium(align=uiconst.TOPRIGHT, text=bonusTE)
        panel.AddCell(label, cellPadding=(8, 0, 0, 0))
    panel.FillRow()
    panel.AddCell(cellPadding=PADBOTTOM, colSpan=2)


def AddDescriptionRow(panel, text, cellPadding = PADBOTTOM):
    if text:
        description = EveLabelMedium(text=text, color=Color.GRAY, align=uiconst.TOTOP)
        panel.AddCell(description, colSpan=2, cellPadding=cellPadding)


def AddSkillRow(panel, typeID, level = None, cellPadding = PADBOTTOM):
    if level is None:
        showLevel = False
        level = 1
    else:
        showLevel = True
    panel.AddRow(rowClass=IndustrySkillEntry, typeID=typeID, level=level, showLevel=showLevel)


def AddErrorRow(panel, error, errorArgs):
    text = industryCommon.GetErrorLabel(error, *errorArgs)
    if not text:
        text = error.name
    description = EveLabelMedium(text=text, align=uiconst.TOPLEFT)
    cell = panel.AddCell(description, colSpan=2, cellPadding=(8, 4, 8, 4))
    frame = ErrorFrame(bgParent=cell)
    frame.Show()


def AddModifierRow(name, value, panel):
    panel.AddLabelMedium(text=name, align=uiconst.TOPLEFT, cellPadding=(0, 0, 0, 2))
    panel.AddLabelMedium(text=value, align=uiconst.TOPRIGHT, cellPadding=(12, 0, 0, 2))


def AddModifierRows(caption, modifiers, panel):
    label = IndustryCaptionLabel(text=caption, width=220)
    panel.AddCell(label, colSpan=2, cellPadding=(0, 0, 0, 2))
    for modifier in modifiers:
        AddModifierRow(modifier.GetName(), modifier.GetPercentageLabel(), panel)


def AddJobModifierRows(panel, modifierCls, jobData):
    modifiers = jobData.GetModifiers(modifierCls)
    if not modifiers:
        return
    caption = jobData.GetModifierCaption(modifierCls)
    AddModifierRows(caption, modifiers, panel)
    panel.AddSpacer(0, 6, colSpan=2)


def AddSystemCostIndexRow(activityID, facilityData, tooltipPanel, cellPadding = (8, 0, 0, 8)):
    text = '<color=gray>' + localization.GetByLabel('UI/Industry/SystemCostIndex')
    tooltipPanel.AddLabelMedium(text=text, align=uiconst.TOPLEFT, cellPadding=(0, 0, 0, 0))
    height = 13
    gauge = SystemCostIndexGauge(gaugeHeight=height, align=uiconst.TOPRIGHT, pos=(0,
     2,
     50,
     height), facilityData=facilityData, activityID=activityID)
    tooltipPanel.AddCell(gauge, cellPadding=cellPadding)


class MaterialTooltipPanel:

    def __init__(self, jobData, materialData, tooltipPanel):
        self.jobData = jobData
        self.materialData = materialData
        self.tooltipPanel = tooltipPanel
        tooltipPanel.margin = MARGIN
        tooltipPanel.columns = 2
        self.Reconstruct()
        self.jobData.on_updated.connect(self.Reconstruct)

    def Reconstruct(self, *args):
        if self.tooltipPanel.destroyed:
            return
        self.tooltipPanel.Flush()
        AddItemRow(self.tooltipPanel, self.materialData)
        self.tooltipPanel.AddCell(cellPadding=(0, 0, 0, 4), colSpan=2)
        price = self.materialData.GetEstimatedUnitPrice() * self.materialData.quantity
        AddPriceRow(self.tooltipPanel, price)


class OutcomeTooltipPanel:

    def __init__(self, jobData, tooltipPanel):
        self.jobData = jobData
        self.tooltipPanel = tooltipPanel
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = MARGIN
        tooltipPanel.columns = 2
        if self.jobData.IsProductSelectable() and not self.jobData.IsInstalled():
            AddDescriptionRow(self.tooltipPanel, GetByLabel('UI/Industry/SelectOutcome'))
            scroll = Scroll(align=uiconst.TOPLEFT, width=250)
            scroll.OnSelectionChange = self.OnScrollSelectionChange
            scrollList = self.GetScrollContent()
            scroll.Load(contentList=scrollList)
            scroll.ScrollToSelectedNode()
            scroll.height = min(len(scrollList) * 29 + 2, 200)
            scroll.Confirm = self.Confirm
            self.tooltipPanel.AddCell(scroll, colSpan=3, cellPadding=PADBOTTOM)
        else:
            AddOutcomeRow(self.tooltipPanel, self.jobData.product)
            price = self.jobData.product.GetEstimatedUnitPrice() * self.jobData.product.quantity
            AddPriceRow(self.tooltipPanel, price)

    def GetScrollContent(self):
        entries = []
        for product in self.jobData.products:
            invType = cfg.invtypes.Get(product.typeID)
            data = KeyVal(typeID=product.typeID, label=invType.name, getIcon=True, isCopy=not product.original, hint=invType.description, isSelected=self.jobData.GetProductTypeID() == product.typeID, OnDblClick=self.OnNodeDblClick)
            entry = listentry.Get(decoClass=listentry.Item, data=data)
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
        self.jobData.product = nodes[0].typeID


class MaterialGroupTooltipPanel:

    def __init__(self, materialsByGroupID, tooltipPanel, jobData):
        tooltipPanel.margin = MARGIN
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.columns = 2
        self.materialsByGroupID = materialsByGroupID
        self.jobData = jobData
        self.tooltipPanel = tooltipPanel
        self.Reconstruct()
        self.jobData.on_updated.connect(self.Reconstruct)

    def Reconstruct(self, *args):
        if self.tooltipPanel.destroyed:
            return
        self.tooltipPanel.Flush()
        for materialGroupID, materials in self.materialsByGroupID:
            AddMaterialGroupRow(materialGroupID, self.tooltipPanel)
            materials = filter(lambda m: m.typeID is not None, materials)
            if materials:
                for materialData in materials:
                    AddItemRow(self.tooltipPanel, materialData)

                self.tooltipPanel.AddCell(cellPadding=(0, 0, 0, 10), colSpan=2)
            else:
                label = EveLabelMedium(align=uiconst.CENTERLEFT, left=16, text=localization.GetByLabel('UI/Industry/NoItemSelected'))
                self.tooltipPanel.AddCell(label, cellPadding=(8, 0, 0, 10), colSpan=2)

        AddPriceRow(self.tooltipPanel, self.GetTotalEstimatedPrice())
        AddJobModifierRows(self.tooltipPanel, industry.MaterialModifier, self.jobData)

    def GetTotalEstimatedPrice(self):
        total = 0.0
        for _, materials in self.materialsByGroupID:
            for material in materials:
                if material.typeID:
                    total += material.GetEstimatedUnitPrice() * material.quantity

        return total


class MaterialIconAndLabel(ContainerAutoSize):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.materialData = attributes.materialData
        if isinstance(self.materialData, industry.Blueprint):
            bpData = self.materialData
        else:
            bpData = None
        icon = ItemIcon(parent=self, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, pos=(0, 0, 20, 20), typeID=self.materialData.typeID, bpData=bpData)
        label = EveLabelMedium(parent=self, align=uiconst.CENTERLEFT, text=self.materialData.GetName(), left=24)

    def GetMenu(self):
        menu = sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.materialData.typeID, ignoreMarketDetails=0)
        menu.insert(0, (MenuLabel('UI/Inventory/ItemActions/BuyThisType'), sm.GetService('menu').QuickBuy, (self.materialData.typeID, self.materialData.missing)))
        return menu

    def GetHint(self):
        return cfg.invtypes.Get(self.materialData.typeID).description


class SkillTooltipPanel:

    def __init__(self, skills, tooltipPanel):
        tooltipPanel.margin = 8
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.columns = 2
        self.tooltipPanel = tooltipPanel
        if not skills:
            description = EveLabelMedium(text=localization.GetByLabel('UI/Industry/NoSkillRequirements'), color=Color.GRAY, align=uiconst.TOPLEFT)
            tooltipPanel.AddCell(description, colSpan=2, cellPadding=(0, 0, 0, 8))
            return
        AddDescriptionRow(tooltipPanel, localization.GetByLabel('UI/Industry/RequiredSkills'), cellPadding=(0, 0, 0, 2))
        for typeID, level in skills:
            AddSkillRow(tooltipPanel, typeID, level, cellPadding=(0, 0, 0, 1))


class SubmitButtonTooltipPanel:

    def __init__(self, status, errors, tooltipPanel):
        self.tooltipPanel = tooltipPanel
        self.Reconstruct(status, errors)

    def Reconstruct(self, status, errors):
        if self.tooltipPanel.destroyed:
            return
        self.tooltipPanel.margin = MARGIN
        self.tooltipPanel.columns = 2
        self.tooltipPanel.Flush()
        if status == industry.STATUS_INSTALLED:
            self.tooltipPanel.AddLabelMedium(text=localization.GetByLabel('UI/Industry/StopJobHint'), wrapWidth=200, cellPadding=4)
        else:
            if not errors:
                return
            errors = {error[0].value:error for error in errors}.values()
            self.tooltipPanel.cellSpacing = (0, 4)
            for error, errorArgs in errors:
                AddErrorRow(self.tooltipPanel, error, errorArgs)

        self.tooltipPanel.AddSpacer(width=0, height=4, colSpan=2)


class JobsSummaryTooltipPanel:

    def __init__(self, jobData, tooltipPanel):
        self.tooltipPanel = tooltipPanel
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = 8
        tooltipPanel.columns = 2
        rangeLabel = industryUIConst.GetControlRangeLabel(jobData.max_distance)
        if jobData.activityID == industry.MANUFACTURING:
            text = localization.GetByLabel('UI/Industry/JobSummaryManufacturing', used=jobData.used_slots, max=jobData.max_slots)
            tooltipPanel.AddLabelMedium(text=text, width=320, cellPadding=(0, 0, 0, 2), colSpan=2)
            AddSkillRow(tooltipPanel, const.typeMassProduction, cellPadding=(0, 0, 0, 1))
            AddSkillRow(tooltipPanel, const.typeAdvancedMassProduction, cellPadding=(0, 0, 0, 1))
            text = localization.GetByLabel('UI/Industry/ControlRangeManufacturing', range=rangeLabel)
            tooltipPanel.AddLabelMedium(text=text, width=320, cellPadding=(0, 8, 0, 2), colSpan=2)
            AddSkillRow(tooltipPanel, const.typeSupplyChainManagement, cellPadding=(0, 0, 0, 1))
        else:
            text = localization.GetByLabel('UI/Industry/JobSummaryScience', used=jobData.used_slots, max=jobData.max_slots)
            tooltipPanel.AddLabelMedium(text=text, width=320, cellPadding=(0, 0, 0, 2), colSpan=2)
            AddSkillRow(tooltipPanel, const.typeLaboratoryOperation, cellPadding=(0, 0, 0, 1))
            AddSkillRow(tooltipPanel, const.typeAdvancedLaboratoryOperation, cellPadding=(0, 0, 0, 1))
            text = localization.GetByLabel('UI/Industry/ControlRangeScience', range=rangeLabel)
            tooltipPanel.AddLabelMedium(text=text, width=320, cellPadding=(0, 8, 0, 2), colSpan=2)
            AddSkillRow(tooltipPanel, const.typeScientificNetworking, cellPadding=(0, 0, 0, 1))


class TimeContainerTooltipPanel:

    def __init__(self, jobData, tooltipPanel):
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = (8, 8, 8, 7)
        tooltipPanel.columns = 2
        AddJobModifierRows(tooltipPanel, industry.TimeModifier, jobData)
        for typeID in jobData.GetTimeSkillTypes() or []:
            AddSkillRow(tooltipPanel, typeID, cellPadding=(0, 0, 0, 1))


class CostContainerTooltipPanel:

    def __init__(self, jobData, tooltipPanel):
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = MARGIN
        tooltipPanel.columns = 2
        AddModifierRow('<color=gray>%s</color>' % localization.GetByLabel('UI/Industry/BaseItemCost'), FmtISK(jobData.base_cost, 0), tooltipPanel)
        AddSystemCostIndexRow(jobData.activityID, jobData.facility, tooltipPanel, cellPadding=(0, 0, 0, 4))
        tooltipPanel.AddSpacer(colSpan=2, width=0, height=6)
        modifiers = jobData.GetModifiers(industry.CostModifier)
        if modifiers or jobData.facility.tax:
            caption = jobData.GetModifierCaption(industry.CostModifier)
            label = IndustryCaptionLabel(text=caption, width=220)
            tooltipPanel.AddCell(label, colSpan=2, cellPadding=(0, 0, 0, 2))
            if modifiers:
                for modifier in modifiers:
                    AddModifierRow(modifier.GetName(), modifier.GetPercentageLabel(), tooltipPanel)

            if jobData.facility.tax is not None:
                taxLabel = '<color=red>+%s%%</color>' % FormatNumeric(jobData.facility.tax * 100, useGrouping=True, decimalPlaces=1)
                AddModifierRow(localization.GetByLabel('UI/Industry/FacilityTax'), taxLabel, tooltipPanel)
        tooltipPanel.AddSpacer(width=0, height=6)


class ProbabilityTooltipPanel:

    def __init__(self, jobData, tooltipPanel):
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = MARGIN
        tooltipPanel.columns = 2
        AddJobModifierRows(tooltipPanel, industry.ProbabilityModifier, jobData)
        if jobData.activityID == industry.INVENTION:
            for skill in jobData.activity.skills:
                AddSkillRow(tooltipPanel, skill.typeID, cellPadding=(0, 0, 0, 2))

            tooltipPanel.AddSpacer(width=0, height=6)


class FacilityActivityTooltip:

    def __init__(self, facilityData, activityID, tooltipPanel):
        tooltipPanel.margin = MARGIN
        tooltipPanel.columns = 2
        tooltipPanel.state = uiconst.UI_NORMAL
        text = localization.GetByLabel(industryUIConst.ACTIVITY_NAMES.get(activityID))
        tooltipPanel.AddLabelMedium(text=text, cellPadding=PADBOTTOM, colSpan=2, bold=True)
        if activityID not in facilityData.activities:
            text = localization.GetByLabel('UI/Industry/ActivityNotSupported')
            tooltipPanel.AddLabelMedium(text=text, cellPadding=PADBOTTOM, colSpan=2)
            return
        if activityID == industry.MANUFACTURING:
            activity = facilityData.activities[activityID]
            categoryGroupData = self.GetTypesSupportedWithModifiers(activity, facilityData.modifiers)
            if categoryGroupData:
                label = IndustryCaptionLabel(text=localization.GetByLabel('UI/Industry/ManufacturingTypesHint'))
                tooltipPanel.AddCell(label, colSpan=2)
                self.scroll = ScrollContainer(align=uiconst.TOTOP, showUnderlay=True)
                for text, modifierME, modifierTE in categoryGroupData:
                    Label(parent=self.scroll, align=uiconst.TOTOP, text=text, padding=2)
                    if modifierME:
                        Label(parent=self.scroll, align=uiconst.TOTOP, text='<color=gray>%s:</color> %s' % (localization.GetByLabel('UI/Industry/MaterialConsumption'), modifierME.GetPercentageLabel()), fontsize=10, padding=(2, 0, 2, 2))
                    if modifierTE:
                        Label(parent=self.scroll, align=uiconst.TOTOP, text='<color=gray>%s</color> %s' % (localization.GetByLabel('UI/Industry/JobDuration'), modifierTE.GetPercentageLabel()), fontsize=10, padding=(2, -3, 2, 3))

                self.scroll.height = min(150, len(categoryGroupData) * 20)
                tooltipPanel.AddCell(self.scroll, cellPadding=PADBOTTOM, colSpan=2)
        modifiers = facilityData.GetFacilityModifiersByActivityID().get(activityID, None)
        if modifiers:
            for modifierCls, label in ((industry.TimeModifier, 'UI/Industry/ModifierTimeCaption'), (industry.MaterialModifier, 'UI/Industry/ModifierMaterialCaption'), (industry.CostModifier, 'UI/Industry/ModifierCostCaption')):
                clsModifiers = [ modifier for modifier in modifiers if isinstance(modifier, modifierCls) ]
                if clsModifiers:
                    AddModifierRows(localization.GetByLabel(label), clsModifiers, tooltipPanel)
                    tooltipPanel.AddSpacer(0, 6, colSpan=2)

        costIndexes = facilityData.GetCostIndexByActivityID()
        costIndex = costIndexes.get(activityID, None)
        if costIndex:
            AddSystemCostIndexRow(activityID, facilityData, tooltipPanel)

    def GetMETEModifiers(self, modifiers):
        modifierME = modifierTE = None
        for modifier in modifiers:
            if isinstance(modifier, industry.TimeModifier):
                modifierTE = modifier
            elif isinstance(modifier, industry.MaterialModifier):
                modifierME = modifier

        return (modifierME, modifierTE)

    def GetTypesSupportedWithModifiers(self, activity, modifiers):
        ret = []
        modifiersByCategoryID = self.GetModifiersByCategoryID(modifiers)
        for categoryID in activity['categories']:
            if categoryID == const.categoryBlueprint:
                continue
            text = cfg.invcategories.Get(categoryID).name
            modifierME, modifierTE = self.GetMETEModifiers(modifiersByCategoryID.get(categoryID, []))
            ret.append((text, modifierME, modifierTE))

        modifiersByGroupID = self.GetModifiersByGroupID(modifiers)
        for groupID in activity['groups']:
            text = cfg.invgroups.Get(groupID).name
            modifierME, modifierTE = self.GetMETEModifiers(modifiersByGroupID.get(groupID, []))
            ret.append((text, modifierME, modifierTE))

        ret.sort()
        return ret

    def GetModifiersByCategoryID(self, modifiers):
        ret = defaultdict(list)
        for modifier in modifiers:
            if getattr(modifier, 'categoryID', None):
                ret[modifier.categoryID].append(modifier)

        return ret

    def GetModifiersByGroupID(self, modifiers):
        ret = defaultdict(list)
        for modifier in modifiers:
            if getattr(modifier, 'groupID', None):
                ret[modifier.groupID].append(modifier)

        return ret
