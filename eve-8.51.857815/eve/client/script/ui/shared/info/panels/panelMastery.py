#Embedded file name: eve/client/script/ui/shared/info/panels\panelMastery.py
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from eve.client.script.ui.control.buttons import ToggleButtonGroup
import carbonui.const as uiconst
import localization
from eve.client.script.ui.control.eveScroll import Scroll
import const
import listentry
import uiutil
import uicls
BUTTONS = ((1, 'res:/UI/Texture/classes/Mastery/MasterySmall1.png'),
 (2, 'res:/UI/Texture/classes/Mastery/MasterySmall2.png'),
 (3, 'res:/UI/Texture/classes/Mastery/MasterySmall3.png'),
 (4, 'res:/UI/Texture/classes/Mastery/MasterySmall4.png'),
 (5, 'res:/UI/Texture/classes/Mastery/MasterySmall5.png'))

class PanelMastery(Container):
    __notifyevents__ = ['OnSkillLevelChanged']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.masteryLevel = 0
        sm.RegisterNotify(self)

    def Load(self):
        self.Flush()
        toggleButtonCont = Container(name='btnGroupCont', parent=self, align=uiconst.TOTOP, height=45)
        btnGroup = ToggleButtonGroup(parent=toggleButtonCont, align=uiconst.CENTER, height=toggleButtonCont.height, width=330, padding=(10, 4, 10, 3), callback=self.LoadMasteryLevel)
        for level, iconPath in BUTTONS:
            hint = localization.GetByLabel('UI/InfoWindow/MasteryLevelButtonHint', level=level)
            btnGroup.AddButton(btnID=level, iconPath=iconPath, iconSize=45, hint=hint)

        self.masteryHeader = Container(name='masteryHeader', parent=self, align=uiconst.TOTOP, height=25)
        self.settingsMenu = uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.masteryHeader, align=uiconst.BOTTOMLEFT, left=4, GetUtilMenu=self.GetSettingsMenu, texturePath='res:/UI/Texture/SettingsCogwheel.png', width=16, height=16, iconSize=18)
        self.masteryTimeLabel = EveLabelMediumBold(name='masteryTimeLabel', parent=self.masteryHeader, align=uiconst.BOTTOMLEFT, left=24)
        self.masteryScroll = Scroll(name='masteryScroll', parent=self, padding=const.defaultPadding)
        level = sm.GetService('certificates').GetCurrCharMasteryLevel(self.typeID)
        level = max(level, 1)
        btnGroup.SelectByID(level)

    def LoadMasteryLevel(self, btnID):
        if getattr(self, 'masteryScroll', None) is None:
            return
        if btnID is None:
            return
        self.masteryLevel = btnID
        entries = self.GetMasteryScrollEntries(btnID)
        self.masteryScroll.Load(contentList=entries)
        self.UpdateTrainingTime(btnID)

    def GetMasteryScrollEntries(self, level):
        certificates = sm.GetService('certificates').GetCertificatesForShipByMasteryLevel(self.typeID, level)
        scrolllist = []
        for cert in certificates:
            data = sm.GetService('info').GetCertEntry(cert, level)
            scrolllist.append((data.get('label', ''), listentry.Get(settings=data, decoClass=listentry.CertEntry)))

        return uiutil.SortListOfTuples(scrolllist)

    def UpdateTrainingTime(self, level):
        """
        Recalculates the training time required for the given mastery level, and redraws the label.
        """
        trainingTime = sm.GetService('certificates').GetShipTrainingTimeForMasteryLevel(self.typeID, level)
        if trainingTime > 0:
            self.masteryTimeLabel.text = localization.GetByLabel('UI/SkillQueue/Skills/TotalTrainingTime', timeLeft=long(trainingTime))
        else:
            self.masteryTimeLabel.text = localization.GetByLabel('UI/InfoWindow/MasteryAcquired')

    def GetSettingsMenu(self, parent):
        """
        Populates the settings menu with some toggleable options.
        """
        parent.AddCheckBox(text=localization.GetByLabel('UI/InfoWindow/MasteryFilterAcquired'), checked=bool(settings.user.ui.Get('masteries_filter_acquired', False)), callback=self.ToggleFilterAcquired)
        parent.AddCheckBox(text=localization.GetByLabel('UI/InfoWindow/MasteryDisplaySkillCounter'), checked=bool(settings.user.ui.Get('masteries_skill_counter', True)), callback=self.ToggleSkillCounter)

    def ToggleFilterAcquired(self, *args):
        settings.user.ui.Set('masteries_filter_acquired', not settings.user.ui.Get('masteries_filter_acquired', False))
        self.LoadMasteryLevel(self.masteryLevel)

    def ToggleSkillCounter(self, *args):
        settings.user.ui.Set('masteries_skill_counter', not settings.user.ui.Get('masteries_skill_counter', True))
        self.LoadMasteryLevel(self.masteryLevel)

    def OnSkillLevelChanged(self, *args):
        self.LoadMasteryLevel(self.masteryLevel)
