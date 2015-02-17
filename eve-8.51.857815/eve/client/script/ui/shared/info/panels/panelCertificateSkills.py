#Embedded file name: eve/client/script/ui/shared/info/panels\panelCertificateSkills.py
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from eve.client.script.ui.control.buttons import ToggleButtonGroup
import carbonui.const as uiconst
import localization
from eve.client.script.ui.control.eveScroll import Scroll
import const
import listentry

class PanelCertificateSkills(Container):
    __notifyevents__ = ['OnSkillLevelChanged']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.certificateID = attributes.certificateID
        self.masteryLevel = 0
        sm.RegisterNotify(self)

    def Load(self):
        self.Flush()
        toggleButtonCont = Container(name='btnGroupCont', parent=self, align=uiconst.TOTOP, height=45)
        btnGroup = ToggleButtonGroup(parent=toggleButtonCont, align=uiconst.CENTER, height=toggleButtonCont.height, width=330, padding=(10, 4, 10, 3), callback=self.LoadCertificateSkillsLevel)
        btns = ((1, 'res:/UI/Texture/icons/79_64_2.png'),
         (2, 'res:/UI/Texture/icons/79_64_3.png'),
         (3, 'res:/UI/Texture/icons/79_64_4.png'),
         (4, 'res:/UI/Texture/icons/79_64_5.png'),
         (5, 'res:/UI/Texture/icons/79_64_6.png'))
        for level, iconPath in btns:
            hint = localization.GetByLabel('UI/InfoWindow/CertificateLevelButtonHint', level=level)
            btnGroup.AddButton(btnID=level, iconPath=iconPath, iconSize=32, hint=hint)

        self.masteryTimeLabel = EveLabelMediumBold(name='masteryTimeLabel', parent=self, align=uiconst.TOTOP, top=10, left=10)
        self.scroll = Scroll(name='certSkillScroll', parent=self, padding=const.defaultPadding)
        cert = sm.GetService('certificates').GetCertificate(self.certificateID)
        btnGroup.SelectByID(max(1, cert.GetLevel()))

    def LoadCertificateSkillsLevel(self, level):
        if getattr(self, 'scroll', None) is None:
            return
        self.masteryLevel = level
        scrolllist = []
        entries = sm.GetService('certificates').GetCertificate(self.certificateID).SkillsByTypeAndLevel(level)
        skillScrollList = sm.GetService('info').GetReqSkillInfo(None, entries, showPrereqSkills=False)
        scrolllist += skillScrollList
        if not len(scrolllist):
            scrolllist.append(listentry.Get('Text', {'line': 0,
             'text': localization.GetByLabel('UI/Certificates/NoSkillRequirements')}))
        self.scroll.Load(contentList=scrolllist)
        self.UpdateTrainingTime(level)

    def UpdateTrainingTime(self, level):
        """
        Recalculates the training time required for the given mastery level, and redraws the label.
        """
        trainingTime = sm.GetService('certificates').GetCertificateTrainingTimeForMasteryLevel(self.certificateID, level)
        if trainingTime > 0:
            self.masteryTimeLabel.text = localization.GetByLabel('UI/SkillQueue/Skills/TotalTrainingTime', timeLeft=long(trainingTime))
        else:
            self.masteryTimeLabel.text = localization.GetByLabel('UI/InfoWindow/CertificateAcquired')

    def OnSkillLevelChanged(self, *args):
        self.LoadCertificateSkillsLevel(self.masteryLevel)
