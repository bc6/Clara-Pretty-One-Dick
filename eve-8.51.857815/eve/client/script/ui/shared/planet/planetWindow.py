#Embedded file name: eve/client/script/ui/shared/planet\planetWindow.py
"""
Code for the planet window
"""
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveWindow import Window
import const
import carbonui.const as uiconst
import listentry
from localization import GetByLabel
from localization.formatters import FormatNumeric
import service
import util

class PlanetWindow(Window):
    """
    This class draws the planets window
    """
    __guid__ = 'form.PlanetWindow'
    __notifyevents__ = ['OnPlanetCommandCenterDeployedOrRemoved',
     'OnPlanetPinsChanged',
     'OnColonyPinCountUpdated',
     'OnSessionChanged']
    default_width = 400
    default_height = 180
    default_minSize = (default_width, default_height)
    default_windowID = 'planetWindow'
    default_captionLabelPath = 'UI/ScienceAndIndustry/PlanetaryColonies'
    default_descriptionLabelPath = 'UI/ScienceAndIndustry/PlanetaryColoniesDesc'
    default_caption = GetByLabel('UI/ScienceAndIndustry/PlanetaryColonies')
    default_iconNum = 'res:/UI/Texture/WindowIcons/planets.png'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.SetTopparentHeight(0)
        mainCont = Container(name='mainCont', parent=self.sr.main, padding=const.defaultPadding)
        buttonCont = Container(name='buttonCont', parent=mainCont, align=uiconst.TOBOTTOM, height=26)
        scrollCont = Container(name='scrollCont', parent=mainCont)
        self.planetScroll = Scroll(name='planetsScroll', parent=scrollCont)
        self.planetScroll.multiSelect = False
        self.planetScroll.sr.id = 'planetscroll'
        self.planetScroll.OnSelectionChange = self.OnPlanetScrollSelectionChange
        self.planetClickID = None
        scrolllist, headers = self.GetPlanetScrollList()
        noCommandBuiltLabel = GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/NoCommandCenterBuilt')
        self.planetScroll.Load(contentList=scrolllist, headers=headers, noContentHint=noCommandBuiltLabel)
        viewPlanetLabel = GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/ViewPlanet')
        buttons = ButtonGroup(btns=[[viewPlanetLabel, self.ViewPlanet, ()]], parent=buttonCont, idx=0)
        viewPlanetLabel = GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/ViewPlanet')
        self.viewPlanetBtn = buttons.GetBtnByLabel(viewPlanetLabel)
        self.viewPlanetBtn.Disable()

    def GetPlanetScrollList(self):
        scrolllist = []
        rows = sm.GetService('planetSvc').GetMyPlanets()
        locationIDs = set()
        for row in rows:
            locationIDs.update([row.planetID, row.solarSystemID])

        cfg.evelocations.Prime(locationIDs)
        for row in rows:
            planetName = cfg.evelocations.Get(row.planetID).locationName
            planetInstallationsLabel = GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/PlanetHasInstallations', planetName=planetName, installations=row.numberOfPins)
            data = util.KeyVal(label='%s<t>%s<t>%s<t>%s' % (cfg.evelocations.Get(row.solarSystemID).locationName,
             cfg.invtypes.Get(row.typeID).typeName,
             planetName,
             FormatNumeric(row.numberOfPins, decimalPlaces=0, useGrouping=True)), GetMenu=self.GetPlanetEntryMenu, OnClick=self.OnPlanetEntryClick, planetID=row.planetID, typeID=row.typeID, hint=planetInstallationsLabel, solarSystemID=row.solarSystemID, OnDblClick=self.OnPlanetEntryDblClick)
            data.Set('sort_%s' % GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/PlanetName'), (cfg.evelocations.Get(row.solarSystemID).name, row.celestialIndex))
            scrolllist.append(listentry.Get('Generic', data=data))

        headers = [GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/SystemName'),
         GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/PlanetType'),
         GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/PlanetName'),
         GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/Installations')]
        return (scrolllist, headers)

    def OnPlanetScrollSelectionChange(self, selected):
        if selected:
            self.viewPlanetBtn.Enable()
        else:
            self.viewPlanetBtn.Disable()

    def OnPlanetCommandCenterDeployedOrRemoved(self):
        self.LoadPlanetScroll()

    def OnPlanetPinsChanged(self, planetID):
        self.LoadPlanetScroll()

    def OnColonyPinCountUpdated(self, planetID):
        self.LoadPlanetScroll()

    def OnSessionChanged(self, isRemote, sess, change):
        self.LoadPlanetScroll()

    def LoadPlanetScroll(self):
        scrolllist, headers = self.GetPlanetScrollList()
        self.planetScroll.Load(contentList=scrolllist, headers=headers)

    def GetPlanetEntryMenu(self, entry):
        node = entry.sr.node
        menu = []
        menuSvc = sm.GetService('menu')
        if node.solarSystemID != session.solarsystemid:
            mapItem = sm.StartService('map').GetItem(node.solarSystemID)
            if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
                gmExtrasLabel = MenuLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/GMWMExtrasCommand')
                menu += [(gmExtrasLabel, ('isDynamic', menuSvc.GetGMMenu, (node.planetID,
                    None,
                    None,
                    None,
                    mapItem)))]
            menu += menuSvc.MapMenu([node.solarSystemID])
            isOpen = sm.GetService('viewState').IsViewActive('planet') and sm.GetService('planetUI').planetID == node.planetID
            if isOpen:
                menu += [[MenuLabel('UI/PI/Common/ExitPlanetMode'), sm.GetService('viewState').CloseSecondaryView, ()]]
            else:
                openPlanet = lambda planetID: sm.GetService('viewState').ActivateView('planet', planetID=planetID)
                menu += [(MenuLabel('UI/PI/Common/ViewInPlanetMode'), sm.GetService('planetUI').Open, (node.planetID,))]
            menu += [(MenuLabel('UI/Commands/ShowInfo'), menuSvc.ShowInfo, (node.typeID,
               node.planetID,
               0,
               None,
               None))]
        else:
            menu += menuSvc.CelestialMenu(node.planetID)
        return menu

    def ViewPlanet(self):
        if self.planetClickID is None:
            return
        sm.GetService('viewState').ActivateView('planet', planetID=self.planetClickID)

    def OnPlanetEntryClick(self, entry):
        node = entry.sr.node
        self.planetClickID = node.planetID

    def OnPlanetEntryDblClick(self, entry):
        node = entry.sr.node
        sm.GetService('viewState').ActivateView('planet', planetID=node.planetID)
