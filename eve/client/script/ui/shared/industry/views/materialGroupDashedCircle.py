#Embedded file name: eve/client/script/ui/shared/industry/views\materialGroupDashedCircle.py
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.views.dashedCircle import DashedCircle
from eve.client.script.ui.shared.industry.views.industryTooltips import MaterialGroupTooltipPanel
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
import localization
import blue

class MaterialGroupDashedCircle(DashedCircle):

    def ApplyAttributes(self, attributes):
        DashedCircle.ApplyAttributes(self, attributes)
        self.materialsByGroupID = attributes.materialsByGroupID
        self.jobData = attributes.jobData

    def UpdateMaterialsByGroup(self, materialsByGroupID):
        self.materialsByGroupID = materialsByGroupID

    def LoadTooltipPanel(self, tooltipPanel, *args):
        self.tooltipPanel = MaterialGroupTooltipPanel(materialsByGroupID=self.materialsByGroupID, tooltipPanel=tooltipPanel, jobData=self.jobData)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def GetMenu(self):
        return ((localization.GetByLabel('UI/Industry/CopyMaterialInformation'), self.CopyToClipboard, ()),)

    def CopyToClipboard(self):
        data = ''
        for materialGroupID, materials in self.materialsByGroupID:
            groupName = localization.GetByLabel(industryUIConst.LABEL_BY_INDUSTRYGROUP[materialGroupID])
            data += self.AddRow('%s' % groupName)
            data += self.AddRow('typeID', 'Item', 'Available', 'Required', 'Est. Unit price')
            for material in materials:
                if material.typeID is None:
                    data += self.AddRow('No item selected')
                else:
                    data += self.AddRow(material.typeID, material.GetName(), material.available, material.quantity, material.GetEstimatedUnitPrice())

            data += '\n'

        blue.win32.SetClipboardData(data)

    def AddRow(self, col1 = '', col2 = '', col3 = '', col4 = '', col5 = ''):
        return '%s\t%s\t%s\t%s\t%s\n' % (col1,
         col2,
         col3,
         col4,
         col5)

    def OnMouseEnter(self, *args):
        uicore.animations.FadeTo(self, self.opacity, 1.5, duration=0.3)

    def OnMouseExit(self, *args):
        uicore.animations.FadeTo(self, self.opacity, 1.0, duration=0.3)
