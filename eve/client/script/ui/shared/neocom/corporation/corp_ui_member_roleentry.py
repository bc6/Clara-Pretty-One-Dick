#Embedded file name: eve/client/script/ui/shared/neocom/corporation\corp_ui_member_roleentry.py
from carbonui.primitives.container import Container
from carbonui.primitives.gridcontainer import GridContainer
from eve.client.script.ui.control.checkbox import Checkbox
import carbonui.const as uiconst
from localization import GetByLabel
hangerAccessQueryHQ = 1
hangerAccessTakeHQ = 2
containerAccessTakeHQ = 3
hangerAccessQueryBase = 4
hangerAccessTakeBase = 5
containerAccessTakeBase = 6
hangerAccessQueryOther = 7
hangerAccessTakeOther = 8
containerAccessTakeOther = 9
ACCESS_TYPES = [hangerAccessQueryHQ,
 hangerAccessTakeHQ,
 containerAccessTakeHQ,
 hangerAccessQueryBase,
 hangerAccessTakeBase,
 containerAccessTakeBase,
 hangerAccessQueryOther,
 hangerAccessTakeOther,
 containerAccessTakeOther]
ACCESS_TYPES_INFO = {hangerAccessQueryHQ: 'hanger access query HQ',
 hangerAccessTakeHQ: 'hanger access take HQ',
 containerAccessTakeHQ: 'container acccess take HQ',
 hangerAccessQueryBase: 'hanger acces query base',
 hangerAccessTakeBase: 'hanger access take base',
 containerAccessTakeBase: 'container access take base',
 hangerAccessQueryOther: 'hanger access query other',
 hangerAccessTakeOther: 'hanger access take other',
 containerAccessTakeOther: 'container access take other'}

class RoleBoxes(Container):
    __guid__ = 'uicls.RoleBoxes'
    default_height = 60
    default_width = 60

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.checkBoxes = []
        self.myGridCont = GridContainer(name='myGridCont', parent=self, align=uiconst.TOALL)
        self.myGridCont.lines = 3
        self.myGridCont.columns = 3
        self.DrawCheckboxes()

    def DrawCheckboxes(self):
        for typeConst in ACCESS_TYPES:
            c = Container(parent=self.myGridCont, padding=1, state=uiconst.UI_NORMAL)
            cbName = 'cb_%i' % typeConst
            cb = Checkbox(name=cbName, parent=c, checked=False, align=uiconst.CENTER)
            cb.sr.diode.left = 3
            cb.LoadTooltipPanel = self.LoadCBTooltip
            self.checkBoxes.append(cb)

    def GetCheckboxes(self):
        return self.checkBoxes

    def LoadCBTooltip(self, tooltipPanel, *args):
        print 'heeeere'
        tooltipPanel.LoadGeneric2ColumnTemplate()
        tooltipPanel.AddIconLabel(icon='res:/UI/Texture/classes/RoleManagement/checkNone.png', label=GetByLabel('UI/Corporations/RoleManagement/None'), iconSize=16)
        tooltipPanel.AddIconLabel(icon='res:/UI/Texture/classes/RoleManagement/checkRoles.png', label=GetByLabel('UI/Corporations/RoleManagement/Role'), iconSize=16)
        tooltipPanel.AddIconLabel(icon='res:/UI/Texture/classes/RoleManagement/checkGrantable.png', label=GetByLabel('UI/Corporations/RoleManagement/GrantableRole'), iconSize=16)
