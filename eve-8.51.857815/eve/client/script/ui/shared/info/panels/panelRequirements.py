#Embedded file name: eve/client/script/ui/shared/info/panels\panelRequirements.py
from carbonui.primitives.container import Container
import const
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
import carbonui.const as uiconst
import localization

class PanelRequirements(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.skillTimeLabel = EveLabelMediumBold(name='skillTimeLabel', parent=self, align=uiconst.TOTOP, padding=(8, 4, 0, 0))
        self.scroll = Scroll(name='scroll', parent=self, padding=const.defaultPadding)
        self.scroll.ignoreTabTrimming = True

    @classmethod
    def RequirementsVisible(cls, typeID):
        return bool(sm.GetService('skills').GetRequiredSkills(typeID))

    def Load(self):
        scrollList = sm.GetService('info').GetReqSkillInfo(self.typeID)
        self.scroll.Load(contentList=scrollList)
        totalTime = sm.GetService('skills').GetSkillTrainingTimeLeftToUseType(self.typeID)
        if totalTime > 0:
            totalTimeText = localization.GetByLabel('UI/SkillQueue/Skills/TotalTrainingTime', timeLeft=long(totalTime))
            self.skillTimeLabel.text = totalTimeText
            self.skillTimeLabel.Show()
        else:
            self.skillTimeLabel.Hide()
