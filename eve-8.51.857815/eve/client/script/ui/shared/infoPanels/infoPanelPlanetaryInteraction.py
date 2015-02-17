#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelPlanetaryInteraction.py
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import uicls
import util
import localization
import infoPanelConst
import uthread
import eve.client.script.ui.shared.planet.planetCommon as planetCommon
from eve.client.script.ui.shared.planet.resourceController import ResourceController
from eve.client.script.ui.shared.planet.planetEditModeContainer import PlanetEditModeContainer
from eve.client.script.ui.shared.planet.pinContainers.BasePinContainer import CaptionAndSubtext
EDITMODECONTAINER_HEIGHT = 105

class InfoPanelPlanetaryInteraction(uicls.InfoPanelBase):
    __guid__ = 'uicls.InfoPanelPlanetaryInteraction'
    default_name = 'InfoPanelPlanetaryInteraction'
    panelTypeID = infoPanelConst.PANEL_PLANETARY_INTERACTION
    label = 'UI/Chat/ChannelNames/PlanetaryInteraction'
    hasSettings = False
    isCollapsable = False
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/PlanetaryInteraction.png'
    __notifyevents__ = ['OnEditModeChanged', 'OnEditModeBuiltOrDestroyed', 'OnPlanetCommandCenterDeployedOrRemoved']

    def ApplyAttributes(self, attributes):
        uicls.InfoPanelBase.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.inEditMode = False
        self.editModeContainer = uiprimitives.Container(parent=self.mainCont, name='buttonContainer', align=uiconst.TOTOP, state=uiconst.UI_HIDDEN, padding=(0, 0, 0, 5))
        self.editModeContent = uiprimitives.Container(parent=self.editModeContainer, name='editModeContent', align=uiconst.TOALL, padding=(10, 6, 10, 6))
        uiprimitives.Fill(parent=self.editModeContainer, color=util.Color.GetGrayRGBA(0.0, 0.3))
        uicontrols.Frame(parent=self.editModeContainer, color=util.Color.GetGrayRGBA(0.0, 0.2))
        self.tabPanelContainer = uicontrols.ContainerAutoSize(parent=self.mainCont, name='tabPanelContainer', align=uiconst.TOTOP)
        self.planetName = self.headerCls(parent=self.headerCont, state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT)
        self.resourceControllerTab = ResourceController(parent=self.tabPanelContainer)
        self.editModeTab = PlanetEditModeContainer(parent=self.tabPanelContainer)
        self.modeButtonGroup = uicls.ToggleButtonGroup(parent=self.mainCont, align=uiconst.TOTOP, callback=self.OnButtonSelected, padBottom=4)
        for btnID, label, panel in (('editModeTab', localization.GetByLabel('UI/Common/Build'), self.editModeTab), ('resourceControllerTab', localization.GetByLabel('UI/PI/Common/Scan'), self.resourceControllerTab)):
            self.modeButtonGroup.AddButton(btnID, label, panel)

        self.modeButtonGroup.SelectByID('editModeTab')
        BTNSIZE = 24
        exitBtn = uicontrols.Button(parent=self.headerCont, align=uiconst.CENTERRIGHT, pos=(0,
         0,
         BTNSIZE,
         BTNSIZE), icon='res:/UI/Texture/Icons/73_16_45.png', iconSize=16, func=self.ExitPlanetMode, alwaysLite=True, hint=localization.GetByLabel('UI/PI/Common/ExitPlanetMode'))
        homeBtn = uicontrols.Button(parent=self.headerCont, align=uiconst.CENTERRIGHT, pos=(exitBtn.left + exitBtn.width + 2,
         0,
         BTNSIZE,
         BTNSIZE), icon='res:/UI/Texture/Icons/73_16_46.png', iconSize=16, func=self.ViewCommandCenter, alwaysLite=True, hint=localization.GetByLabel('UI/PI/Common/ViewPlanetaryCommandCenter'))
        self.sr.homeBtn = homeBtn
        self.UpdatePlanetText()
        self.UpdateHomeButton()
        self.CreateEditModeContainer()
        planetUISvc = sm.GetService('planetUI')
        planetUISvc.SetModeController(self)
        uthread.new(self.OnEditModeChanged, planetUISvc.inEditMode)

    @staticmethod
    def IsAvailable():
        """ Is this info panel currently available for viewing """
        viewState = sm.GetService('viewState').GetCurrentView()
        if viewState and viewState.name == 'planet':
            return True
        return False

    def UpdatePlanetText(self):
        planetUI = sm.GetService('planetUI')
        planetID = planetUI.planetID
        planetData = sm.GetService('map').GetPlanetInfo(planetID)
        self.planetName.text = '<color=white url=showinfo:%s//%s>%s</url>' % (planetData.typeID, planetID, cfg.evelocations.Get(planetID).locationName)

    def OnButtonSelected(self, mode):
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_general_switch_play')
        if mode == 'resourceControllerTab':
            sm.GetService('planetUI').planetAccessRequired = True

    def ExitPlanetMode(self, *args):
        sm.GetService('viewState').CloseSecondaryView('planet')

    def ViewCommandCenter(self, *args):
        sm.GetService('planetUI').FocusCameraOnCommandCenter()

    def OnPlanetCommandCenterDeployedOrRemoved(self, *args):
        self.UpdateHomeButton()

    def UpdateHomeButton(self):
        if session.charid in sm.GetService('planetUI').planet.colonies:
            self.sr.homeBtn.state = uiconst.UI_NORMAL
        else:
            self.sr.homeBtn.state = uiconst.UI_HIDDEN

    def CreateEditModeContainer(self):
        uicontrols.EveHeaderLarge(parent=self.editModeContent, text=localization.GetByLabel('UI/PI/Common/EditsPending'), align=uiconst.RELATIVE)
        self.powerGauge = uicls.Gauge(parent=self.editModeContent, pos=(0, 22, 115, 34), color=planetCommon.PLANET_COLOR_POWER, label=localization.GetByLabel('UI/PI/Common/PowerUsage'))
        self.cpuGauge = uicls.Gauge(parent=self.editModeContent, pos=(130, 22, 115, 34), color=planetCommon.PLANET_COLOR_CPU, label=localization.GetByLabel('UI/PI/Common/CpuUsage'))
        self.UpdatePowerAndCPUGauges()
        btns = [[localization.GetByLabel('UI/Common/Submit'), self.Submit, ()], [localization.GetByLabel('UI/Common/Cancel'), self.Cancel, ()]]
        bottom = uiprimitives.Container(parent=self.editModeContent, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 40))
        btns = uicontrols.ButtonGroup(btns=btns, subalign=uiconst.CENTERRIGHT, parent=bottom, line=False, alwaysLite=True)
        self.costText = CaptionAndSubtext(parent=bottom, align=uiconst.TOPLEFT, top=13, caption=localization.GetByLabel('UI/Common/Cost'), subtext='')

    def UpdatePowerAndCPUGauges(self):
        """
        Set the white marker to a position according to the actual usage (planet) and the
        gauge to reflect the outcome should the current edit be submitted (simPlanet)
        """
        colony = sm.GetService('planetUI').GetCurrentPlanet().GetColony(session.charid)
        if not colony or colony.colonyData is None:
            return
        originalData = sm.GetService('planetUI').GetCurrentPlanet().GetEditModeData()
        if originalData is None:
            origCpu = 0
            origPower = 0
        else:
            origCpu = originalData.GetColonyCpuUsage()
            origPower = originalData.GetColonyPowerUsage()
        cpuOutput = float(colony.colonyData.GetColonyCpuSupply())
        powerOutput = float(colony.colonyData.GetColonyPowerSupply())
        cpu = colony.colonyData.GetColonyCpuUsage()
        power = colony.colonyData.GetColonyPowerUsage()
        cpuDiff = cpu - origCpu
        powerDiff = power - origPower
        self.cpuGauge.SetValue(cpu / cpuOutput if cpuOutput > 0 else 0)
        self.cpuGauge.HideAllMarkers()
        self.cpuGauge.ShowMarker(origCpu / cpuOutput if cpuOutput > 0 else 0)
        self.powerGauge.SetValue(power / powerOutput if powerOutput > 0 else 0)
        self.powerGauge.HideAllMarkers()
        self.powerGauge.ShowMarker(origPower / powerOutput if powerOutput > 0 else 0)
        if cpuDiff >= 0:
            localization.GetByLabel('UI/PI/Common/TeraFlopsAmountIncrease', amount=cpuDiff)
        else:
            localization.GetByLabel('UI/PI/Common/TeraFlopsAmount', amount=cpuDiff)
        if powerDiff >= 0:
            localization.GetByLabel('UI/PI/Common/MegaWattsAmountIncrease', amount=powerDiff)
        else:
            localization.GetByLabel('UI/PI/Common/MegaWattsAmount', amount=powerDiff)
        self.cpuGauge.hint = localization.GetByLabel('UI/PI/Common/TeraFlopsDiff', current=origCpu, after=cpu, maximum=cpuOutput)
        self.powerGauge.hint = localization.GetByLabel('UI/PI/Common/MegaWattsDiff', current=origPower, after=power, maximum=powerOutput)

    def UpdateCostOfCurrentChanges(self):
        cost = sm.GetService('planetUI').GetCurrentPlanet().GetCostOfCurrentEdits()
        import util
        self.costText.SetSubtext(util.FmtISK(cost, showFractionsAlways=0))

    def Submit(self):
        sm.GetService('planetUI').planet.SubmitChanges()
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_build_submit_play')

    def Cancel(self):
        sm.GetService('planetUI').planet.RevertChanges()
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_build_cancel_play')

    def OnEditModeChanged(self, isEdit):
        if not isEdit:
            uicore.animations.FadeOut(self.editModeContainer, duration=0.3, sleep=True)
            uicore.animations.MorphScalar(self.editModeContainer, 'height', self.editModeContainer.height, 0, duration=0.3, sleep=True)
            self.editModeContainer.state = uiconst.UI_HIDDEN
            self.inEditMode = False
        else:
            self.UpdatePowerAndCPUGauges()
            self.UpdateCostOfCurrentChanges()
            self.editModeContainer.state = uiconst.UI_NORMAL
            uicore.animations.MorphScalar(self.editModeContainer, 'height', 0, EDITMODECONTAINER_HEIGHT, duration=0.3, sleep=True)
            uicore.animations.FadeTo(self.editModeContainer, 0.0, 1.0, duration=0.3, sleep=True)
            self.inEditMode = True

    def OnEditModeBuiltOrDestroyed(self):
        if not self.inEditMode:
            self.editModeContainer.state = uiconst.UI_NORMAL
            uicore.animations.MorphScalar(self.editModeContainer, 'height', 0, EDITMODECONTAINER_HEIGHT, duration=0.3, sleep=True)
            uicore.animations.FadeTo(self.editModeContainer, 0.0, 1.0, duration=0.3, sleep=True)
            self.inEditMode = True
        self.UpdatePowerAndCPUGauges()
        self.UpdateCostOfCurrentChanges()
