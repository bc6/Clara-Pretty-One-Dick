#Embedded file name: eve/client/script/ui/shared/info/panels\panelIndustry.py
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.util.various_unsorted import SortListOfTuples
import const
import carbonui.const as uiconst
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.activitySelectionButtons import ActivityToggleButtonGroupButton
import industry
import listentry
import localization
from carbonui.primitives.container import Container
from eve.client.script.ui.control.buttons import ToggleButtonGroup
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from eve.client.script.ui.control.eveScroll import Scroll
import service
from utillib import KeyVal

class PanelIndustry(Container):
    """
    Show info tab panel for industry data on blueprints, displays activities that can be
    performed with this blueprint and what the skill / material requirements are for it.
    """

    def ApplyAttributes(self, attributes):
        """
        Just read and hold onto the type and item information.
        """
        Container.ApplyAttributes(self, attributes)
        self.bpData = attributes.bpData

    def Load(self):
        self.Flush()
        topCont = ContainerAutoSize(parent=self, align=uiconst.TOTOP, padding=(0, 2, 0, 2))
        btnGroup = ToggleButtonGroup(parent=topCont, align=uiconst.CENTER, height=38, width=248, callback=self.LoadActivity)
        for activityID in industry.ACTIVITIES:
            isDisabled = activityID not in self.bpData.activities
            color = industryUIConst.GetActivityColor(activityID)
            color = color[:3] + (0.5,)
            btnGroup.AddButton(activityID, iconPath=industryUIConst.ACTIVITY_ICONS_LARGE[activityID], iconSize=26, colorSelected=color, isDisabled=isDisabled, btnClass=ActivityToggleButtonGroupButton, activityID=activityID)

        self.activityNameLabel = EveLabelMediumBold(name='label', parent=self, align=uiconst.TOTOP, padding=(6, 0, 0, 0))
        self.scroll = Scroll(parent=self, padding=const.defaultPadding)
        activityID = self.GetSelectedActivityID(activityID)
        btnGroup.SelectByID(activityID)

    def GetSelectedActivityID(self, activityID):
        activityID = settings.char.ui.Get('blueprintShowInfoActivityID', 0)
        if activityID not in self.bpData.activities:
            activityID = sorted(self.bpData.activities.keys())[0]
        return activityID

    def LoadActivity(self, activityID):
        """
        Loads the scroll area with the skill and material requirements for this activity.
        TODO: Add time information.
        """
        settings.char.ui.Set('blueprintShowInfoActivityID', activityID)
        self.job = industry.Job(self.bpData, activityID)
        self.activityNameLabel.text = self.job.activity.GetHint()
        entries = []
        entries.append(listentry.Get(decoClass=listentry.LabelTextSides, data=KeyVal(line=1, label=localization.GetByLabel('UI/Industry/TimePerRun'), text=self.job.GetJobTimeLeftLabel())))
        if self.job.activityID == industry.COPYING:
            entries.append(listentry.Get(decoClass=listentry.LabelTextSides, data=KeyVal(line=1, label=localization.GetByLabel('UI/Industry/MaxRunsPerCopy'), text=self.bpData.maxProductionLimit)))
        if self.job.activityID == industry.INVENTION:
            entries.append(listentry.Get(decoClass=listentry.LabelTextSides, data=KeyVal(line=1, label=localization.GetByLabel('UI/Industry/JobSuccessProbability'), text='%s%%' % (self.job.probability * 100))))
        entries.append(listentry.Get(decoClass=listentry.Group, data=KeyVal(GetSubContent=self.LoadOutcome, label=self.GetOutcomeCaption(), groupItems=self.job.products, id='outcome', showicon='hide', showlen=False, state='locked', BlockOpenWindow=True)))
        entries.append(listentry.Get(decoClass=listentry.Group, data=KeyVal(GetSubContent=self.LoadSkills, label=localization.GetByLabel('UI/Industry/RequiredSkills'), groupItems=[ (skill.typeID, skill.level, skill.GetHint()) for skill in self.job.required_skills ], id='skills', showicon='hide', noItemText=localization.GetByLabel('UI/Common/None'), state='locked', BlockOpenWindow=True)))
        materialsData = self.job.GetMaterialsByGroups()
        entries.append(listentry.Get(decoClass=listentry.Group, data=KeyVal(GetSubContent=self.LoadMaterialGroups, label=localization.GetByLabel('UI/Industry/RequiredInputMaterials'), groupItems=materialsData, id='materialGroups', showicon='hide', noItemText=localization.GetByLabel('UI/Common/None'), state='locked', BlockOpenWindow=True)))
        self.scroll.Load(contentList=entries)

    def GetOutcomeCaption(self):
        if len(self.job.products) > 1:
            if self.job.activityID == industry.INVENTION:
                return localization.GetByLabel('UI/Industry/OutcomeOptions')
        return localization.GetByLabel('UI/Industry/Outcome')

    def LoadOutcome(self, nodedata, *args):
        scrolllist = []
        if self.job.activityID == industry.MANUFACTURING:
            for product in nodedata.groupItems:
                entry = listentry.Get('Item', KeyVal(itemID=None, typeID=product.typeID, label=product.GetHint(), getIcon=1))
                scrolllist.append(entry)

        elif self.job.activityID == industry.RESEARCH_MATERIAL:
            label = localization.GetByLabel('UI/Industry/StepMaterialEfficiency', stepSize=industry.STEP_MATERIAL_EFFICIENCY)
            entry = listentry.Get('Generic', KeyVal(label=label, sublevel=1))
            scrolllist.append(entry)
        elif self.job.activityID == industry.RESEARCH_TIME:
            label = localization.GetByLabel('UI/Industry/StepTimeEfficiency', stepSize=industry.STEP_TIME_EFFICIENCY)
            entry = listentry.Get('Generic', KeyVal(label=label, sublevel=1))
            scrolllist.append(entry)
        elif self.job.activityID == industry.COPYING:
            typeID = self.bpData.blueprintTypeID
            label = cfg.invtypes.Get(typeID).name
            entry = listentry.Get(decoClass=listentry.Item, data=KeyVal(itemID=None, typeID=typeID, label=label, getIcon=1, isCopy=True))
            scrolllist.append(entry)
        elif self.job.activityID == industry.INVENTION:
            for product in nodedata.groupItems:
                entry = listentry.Get('Item', KeyVal(itemID=None, typeID=product.typeID, label=product.GetName(), getIcon=1, isCopy=True))
                scrolllist.append(entry)

        return scrolllist

    def LoadSkills(self, nodedata, *args):
        scrolllist = []
        infoSvc = sm.GetService('info')
        skills = []
        for typeID, level, hint in nodedata.groupItems:
            skills.append((typeID, level))

        if skills:
            skills = sorted(skills)
            skillScrollList = infoSvc.GetReqSkillInfo(None, skills)
            scrolllist += skillScrollList
        return scrolllist

    def LoadMaterialGroups(self, nodeData, *args):
        scrollList = []
        for industryGroupID, materials in nodeData.groupItems:
            label = industryUIConst.LABEL_BY_INDUSTRYGROUP.get(industryGroupID, None)
            scrollList.append(listentry.Get(decoClass=listentry.Group, data=KeyVal(GetSubContent=self.LoadMaterialGroup, label=localization.GetByLabel(label), groupItems=[ (material.typeID, material.quantity, material.GetHint()) for material in materials ], id='materials_%s' % industryGroupID, sublevel=1, iconID=industryUIConst.ICON_BY_INDUSTRYGROUP[industryGroupID], hint=localization.GetByLabel(industryUIConst.HINT_BY_INDUSTRYGROUP[industryGroupID]), state='locked', BlockOpenWindow=True)))

        if self.job.materials and eve.session.role & service.ROLE_GML == service.ROLE_GML:
            items = [ (material.typeID, material.quantity) for material in self.job.materials ]
            infoSvc = sm.GetService('info')
            scrollList.append(listentry.Get('Button', {'label': 'GM: Give me these materials',
             'caption': 'Give',
             'OnClick': infoSvc.DoCreateMaterials,
             'args': (items, '', 10)}))
        return scrollList

    def LoadMaterialGroup(self, nodedata, *args):
        scrolllist = []
        for typeID, quantity, hint in nodedata.groupItems:
            entry = listentry.Get('Item', {'itemID': None,
             'typeID': typeID,
             'label': hint,
             'getIcon': 1,
             'sublevel': 1})
            scrolllist.append((typeID, entry))

        scrolllist = SortListOfTuples(scrolllist)
        return scrolllist
