#Embedded file name: eve/client/script/ui/shared/industry/views\OutputCont.py
from math import pi
import blue
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
from eve.client.script.ui.shared.industry.views.industryTooltips import TimeContainerTooltipPanel, CostContainerTooltipPanel
from eve.client.script.ui.shared.industry.views.outcomeContainer import OutcomeContainer
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GAMEPLAY
from localization import GetByLabel
from eve.client.script.ui.control.eveLabel import EveLabelLarge
from eve.client.script.ui.shared.industry.views.industryCaptionLabel import IndustryCaptionLabel
from eve.client.script.ui.shared.industry.views.outputFramedContainers import FacilityContainer, InventoryOutputContainer, InventoryInputContainer
from eve.common.script.util.eveFormat import FmtISK
import uthread

class OutputCont(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = attributes.jobData
        self.ConstructTop()
        self.ConstructBottom()
        self.ConstructCenter()
        self.ConstructCostAndTimeLabels()
        self.bg = StretchSpriteHorizontal(parent=self, state=uiconst.UI_DISABLED, align=uiconst.TORIGHT_PROP, width=0.5, height=402, leftEdgeSize=400, rightEdgeSize=10, texturePath='res:/UI/Texture/Classes/Industry/Input/bg1Groups.png', rotation=pi)
        self.UpdateState()
        self.AnimEntry()

    def ConstructCostAndTimeLabels(self):
        self.labelCont = Container(name='labelCont', parent=self, align=uiconst.BOTTOMRIGHT, pos=(13, 7, 304, 30), opacity=0.0)
        self.timeCont = TimeContainer(parent=self.labelCont, align=uiconst.TOLEFT_PROP, width=0.5, jobData=self.jobData)
        self.costCont = CostContainer(parent=self.labelCont, align=uiconst.TOLEFT_PROP, width=0.5, padLeft=2)

    def ConstructTop(self):
        self.topCont = Container(name='topCont', parent=self, align=uiconst.TOPRIGHT, pos=(13, 7, 377, 87), opacity=0.0)
        self.facilityCont = FacilityContainer(parent=self.topCont, align=uiconst.TOPRIGHT)
        self.invInputCont = InventoryInputContainer(parent=self.topCont, align=uiconst.BOTTOMRIGHT, opacity=0.0)

    def ConstructBottom(self):
        self.bottomCont = Container(name='bottomCont', parent=self, align=uiconst.BOTTOMRIGHT, pos=(0, 39, 377, 60), opacity=0.0)
        self.invOutputCont = InventoryOutputContainer(parent=self.bottomCont, align=uiconst.CENTERRIGHT, left=13)

    def ConstructCenter(self):
        self.outcomeCont = OutcomeContainer(name='outcomeCont', parent=self, align=uiconst.CENTERRIGHT, opacity=0.0)

    def OnRunsChanged(self):
        self.UpdateState()
        self.outcomeCont.OnRunsChanged()

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.facilityCont.OnNewJobData(jobData)
        self.invOutputCont.OnNewJobData(jobData)
        self.invInputCont.OnNewJobData(jobData)
        self.outcomeCont.OnNewJobData(jobData)
        self.timeCont.OnNewJobData(jobData)
        self.costCont.OnNewJobData(jobData)
        self.UpdateState()
        self.AnimEntry()

    def UpdateState(self):
        self.state = uiconst.UI_DISABLED if self.jobData is None else uiconst.UI_PICKCHILDREN
        self.costCont.UpdateState()
        self.timeCont.UpdateState()

    def AnimEntry(self):
        if self.jobData:
            toFadeIn = (self.outcomeCont,
             self.topCont,
             self.bottomCont,
             self.invInputCont,
             self.labelCont)
            for obj in toFadeIn:
                uicore.animations.FadeIn(obj)

            uicore.animations.FadeTo(self.bg, 0.0, 1.0, duration=0.6, timeOffset=0.1)
        else:
            toFadeOut = (self.outcomeCont,
             self.topCont,
             self.bottomCont,
             self.invInputCont,
             self.labelCont)
            for obj in toFadeOut:
                uicore.animations.FadeOut(obj)


class TimeContainer(Container):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = None
        self.updateTimeThread = None
        self.timeCaption = IndustryCaptionLabel(name='timeCaption', parent=self)
        self.timeLabel = EveLabelLarge(name='timeLabel', parent=self, top=13)
        self.errorFrame = ErrorFrame(bgParent=self, padding=(-2, -2, 0, -2))

    def UpdateState(self):
        if self.updateTimeThread:
            self.updateTimeThread.kill()
            self.updateTimeThread = None
        if not self.jobData:
            self.timeLabel.text = ''
            return
        if self.jobData.IsInstalled():
            self.timeCaption.text = GetByLabel('UI/Industry/TimeLeft')
            self.updateTimeThread = uthread.new(self.UpdateTimeThread)
        else:
            self.timeCaption.text = GetByLabel('UI/Industry/JobDuration')
            self.timeLabel.text = self.jobData.GetJobTimeLeftLabel()

    def UpdateTimeThread(self):
        while not self.destroyed:
            self.timeLabel.text = self.jobData.GetJobTimeLeftLabel()
            blue.synchro.SleepWallclock(200)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.UpdateState()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        TimeContainerTooltipPanel(jobData=self.jobData, tooltipPanel=tooltipPanel)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def GetTooltipPosition(self):
        return self.timeCaption.GetAbsolute()


WALLET_PERSONAL = 1
WALLET_CORP = 2

class CostContainer(Container):
    default_state = uiconst.UI_NORMAL
    default_padLeft = 4

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = None
        self.costCaption = IndustryCaptionLabel(name='costCaption', parent=self, align=uiconst.TOTOP, text=GetByLabel('UI/Industry/JobCost'))
        textCont = Container(parent=self)
        self.walletCombo = Combo(parent=textCont, align=uiconst.TOLEFT, state=uiconst.UI_HIDDEN, callback=self.OnWalletCombo, iconOnly=True, width=33, top=1)
        self.walletCombo.GetHint = self.GetWalletComboHint
        self.costLabel = EveLabelLarge(name='costLabel', parent=textCont, align=uiconst.TOTOP, padLeft=4)
        self.errorFrame = ErrorFrame(bgParent=self, padding=(0, -2, 0, -2))

    def UpdateWalletCombo(self):
        if not self.jobData or not self.jobData.accounts or len(self.jobData.accounts) <= 1:
            self.walletCombo.Hide()
            return
        self.walletCombo.Show()
        options = []
        for ownerID, divisionID in sorted(self.jobData.accounts):
            label = self.GetWalletName(ownerID, divisionID)
            texturePath = self.GetWalletIcon(ownerID)
            options.append((label,
             (ownerID, divisionID),
             None,
             texturePath))

        self.walletCombo.LoadOptions(options)
        if self.jobData:
            self.walletCombo.SelectItemByValue(self.jobData.account)

    def OnWalletCombo(self, combo, key, value):
        self.jobData.account = value

    def GetWalletName(self, ownerID, divisionID):
        if ownerID == session.charid:
            return GetByLabel('UI/Industry/PersonalWallet')
        else:
            divisionName = sm.GetService('wallet').GetDivisionName(divisionID)
            return GetByLabel('UI/Industry/CorporateWallet', divisionName=divisionName)

    def GetWalletIcon(self, ownerID):
        if ownerID == session.charid:
            return 'res:/UI/Texture/Classes/Industry/iconPersonal.png'
        else:
            return 'res:/UI/Texture/Classes/Industry/iconCorp.png'

    def GetWalletComboHint(self):
        ownerID, divisionID = self.jobData.account
        iskAmount = self.jobData.accounts[ownerID, divisionID]
        iskAmount = FmtISK(iskAmount)
        walletName = self.GetWalletName(ownerID, divisionID)
        return GetByLabel('UI/Industry/WalletSelectionHint', walletName=walletName, iskAmount=iskAmount)

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.UpdateState()

    def UpdateState(self):
        if not self.jobData:
            self.costLabel.text = ''
            self.walletCombo.Hide()
            return
        if self.jobData.facility and self.jobData.activityID in self.jobData.facility.activities:
            manufacturingCost = self.jobData.total_cost
            self.costLabel.text = FmtISK(manufacturingCost, showFractionsAlways=False)
        else:
            self.costLabel.text = '-'
        self.UpdateWalletCombo()

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if self.jobData.facility:
            CostContainerTooltipPanel(jobData=self.jobData, tooltipPanel=tooltipPanel)

    def GetTooltipDelay(self):
        return TOOLTIP_DELAY_GAMEPLAY

    def GetTooltipPosition(self):
        return self.costCaption.GetAbsolute()
