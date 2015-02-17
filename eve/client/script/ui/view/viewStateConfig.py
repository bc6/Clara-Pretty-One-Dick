#Embedded file name: eve/client/script/ui/view\viewStateConfig.py
from eve.client.script.ui.inflight.shipui import ShipUI
from eve.client.script.ui.services.viewStateSvc import ViewType
from eve.client.script.ui.shared.sidePanelsLayer import SidePanels
from eve.client.script.ui.view.aurumstore.aurumStoreView import AurumStoreView
from eve.client.script.ui.view.characterCustomizationView import CharacterCustomizationView
from eve.client.script.ui.view.characterSelectorView import CharacterSelectorView
from eve.client.script.ui.view.cqView import CQView
from eve.client.script.ui.view.fadeFromCQToSpaceTransition import FadeFromCQToSpaceTransition
from eve.client.script.ui.view.fadeFromCharRecustomToCQTransition import FadeFromCharRecustomToCQTransition
from eve.client.script.ui.view.fadeToCQTransition import FadeToCQTransition
from eve.client.script.ui.view.hangarView import HangarView
from eve.client.script.ui.view.introView import IntroView
from eve.client.script.ui.view.loginView import LoginView
from eve.client.script.ui.view.planetView import PlanetView
from eve.client.script.ui.view.shipTreeView import ShipTreeView
from eve.client.script.ui.view.spaceToSpaceTransition import SpaceToSpaceTransition
from eve.client.script.ui.view.spaceView import SpaceView
from eve.client.script.ui.view.starMapView import StarMapView
from eve.client.script.ui.view.dockPanelView import DockPanelView
from eve.client.script.ui.view.systemMapView import SystemMapView
from eve.client.script.ui.view.transitions import FadeToBlackTransition, SpaceToStationTransition, FadeToBlackLiteTransition
from eve.client.script.ui.view.viewStateConst import ViewState, ViewOverlay
from eve.client.script.ui.view.worldspaceView import WorldspaceView
import logging
logger = logging.getLogger(__name__)
VIEWS_TO_AND_FROM_AURUM_STORE = (ViewState.CharacterSelector,
 ViewState.Space,
 ViewState.Station,
 ViewState.Hangar,
 ViewState.WorldSpace,
 ViewState.StarMap,
 ViewState.SystemMap,
 ViewState.Planet,
 ViewState.ShipTree,
 ViewState.CharacterCreation,
 ViewState.DockPanel)

def SetupViewStates(viewSvc, rootViewLayer):
    """
    Setting up the available views and transitions between them
    """
    logger.debug('Configuring view states')
    logger.debug('Initializing view state service')
    viewSvc.Initialize(rootViewLayer)
    logger.debug('Adding primary views')
    viewSvc.AddView(ViewState.Login, LoginView())
    viewSvc.AddView(ViewState.Intro, IntroView())
    viewSvc.AddView(ViewState.CharacterSelector, CharacterSelectorView())
    viewSvc.AddView(ViewState.Space, SpaceView())
    viewSvc.AddView(ViewState.Station, CQView())
    viewSvc.AddView(ViewState.Hangar, HangarView())
    viewSvc.AddView(ViewState.WorldSpace, WorldspaceView())
    logger.debug('Adding secondary views')
    viewSvc.AddView(ViewState.DockPanel, DockPanelView(), viewType=ViewType.Secondary)
    viewSvc.AddView(ViewState.StarMap, StarMapView(), viewType=ViewType.Secondary)
    viewSvc.AddView(ViewState.SystemMap, SystemMapView(), viewType=ViewType.Secondary)
    viewSvc.AddView(ViewState.Planet, PlanetView(), viewType=ViewType.Secondary)
    viewSvc.AddView(ViewState.ShipTree, ShipTreeView(), viewType=ViewType.Secondary)
    viewSvc.AddView(ViewState.VirtualGoodsStore, AurumStoreView(), viewType=ViewType.Secondary)
    logger.debug('Adding dynamic views')
    viewSvc.AddView(ViewState.CharacterCreation, CharacterCustomizationView(), viewType=ViewType.Dynamic)
    logger.debug('Adding state transitions')
    viewSvc.AddTransition(None, ViewState.Login)
    viewSvc.AddTransitions((ViewState.Login, None), (ViewState.Intro, ViewState.CharacterSelector, ViewState.CharacterCreation), FadeToBlackTransition(fadeTimeMS=250))
    viewSvc.AddTransitions((ViewState.Intro,), (ViewState.CharacterSelector, ViewState.CharacterCreation), FadeToBlackLiteTransition(fadeTimeMS=500))
    viewSvc.AddTransitions((ViewState.CharacterSelector,), (ViewState.Space,
     ViewState.CharacterCreation,
     ViewState.Hangar,
     ViewState.VirtualGoodsStore), FadeToBlackTransition(fadeTimeMS=250))
    viewSvc.AddTransitions((ViewState.CharacterCreation,), (ViewState.Hangar, ViewState.CharacterSelector, ViewState.Space), FadeToBlackTransition(fadeTimeMS=250, allowReopen=False))
    viewSvc.AddTransitions((ViewState.Space,
     ViewState.Hangar,
     ViewState.StarMap,
     ViewState.SystemMap,
     ViewState.DockPanel,
     ViewState.Planet,
     ViewState.ShipTree), (ViewState.Space,
     ViewState.Hangar,
     ViewState.StarMap,
     ViewState.SystemMap,
     ViewState.DockPanel,
     ViewState.Planet,
     ViewState.ShipTree), FadeToBlackLiteTransition(fadeTimeMS=100))
    viewSvc.AddTransition(ViewState.Space, ViewState.Space, SpaceToSpaceTransition())
    viewSvc.AddTransition(ViewState.StarMap, ViewState.StarMap)
    viewSvc.AddTransition(ViewState.Hangar, ViewState.Hangar, FadeToBlackLiteTransition(fadeTimeMS=250, allowReopen=False))
    viewSvc.AddTransitions((ViewState.Station, ViewState.WorldSpace), (ViewState.Hangar,
     ViewState.StarMap,
     ViewState.SystemMap,
     ViewState.DockPanel,
     ViewState.Planet,
     ViewState.WorldSpace,
     ViewState.ShipTree), FadeToBlackLiteTransition(fadeTimeMS=100))
    viewSvc.AddTransitions((ViewState.Space,
     ViewState.CharacterSelector,
     ViewState.Hangar,
     ViewState.CharacterCreation,
     ViewState.Station,
     ViewState.WorldSpace,
     ViewState.ShipTree), (ViewState.Station, ViewState.WorldSpace), FadeToCQTransition(fadeTimeMS=200, fallbackView=ViewState.Hangar, allowReopen=False))
    viewSvc.AddTransition(ViewState.Space, ViewState.Hangar, SpaceToStationTransition())
    viewSvc.AddTransition(ViewState.Hangar, ViewState.Space, FadeToBlackTransition(fadeTimeMS=500))
    viewSvc.AddTransition(ViewState.Space, ViewState.Station, SpaceToStationTransition())
    viewSvc.AddTransition(ViewState.Hangar, ViewState.ShipTree, SpaceToStationTransition())
    viewSvc.AddTransitions((ViewState.StarMap,
     ViewState.Planet,
     ViewState.SystemMap,
     ViewState.DockPanel,
     ViewState.ShipTree), (ViewState.Station,), FadeToCQTransition(fadeTimeMS=200, fallbackView=ViewState.Hangar, allowReopen=True))
    viewSvc.AddTransitions((ViewState.Station,
     ViewState.Hangar,
     ViewState.StarMap,
     ViewState.SystemMap,
     ViewState.DockPanel,
     ViewState.WorldSpace), (ViewState.CharacterCreation,), FadeToBlackTransition(fadeTimeMS=200))
    viewSvc.AddTransition(ViewState.CharacterCreation, (ViewState.Station, ViewState.WorldSpace), FadeFromCharRecustomToCQTransition(fadeTimeMS=250))
    viewSvc.AddTransition(ViewState.Station, ViewState.Space, FadeFromCQToSpaceTransition(fadeTimeMS=250))
    viewSvc.AddTransitions((ViewState.VirtualGoodsStore,), VIEWS_TO_AND_FROM_AURUM_STORE, FadeToBlackTransition(fadeTimeMS=250))
    viewSvc.AddTransitions(VIEWS_TO_AND_FROM_AURUM_STORE, (ViewState.VirtualGoodsStore,), FadeToBlackTransition(fadeTimeMS=250))
    logger.debug('Adding view state controlled overlays')
    viewSvc.AddOverlay(ViewOverlay.Target, None)
    viewSvc.AddOverlay(ViewOverlay.SidePanels, SidePanels)
    viewSvc.AddOverlay(ViewOverlay.ShipUI, ShipUI)
    viewSvc.AddOverlay(ViewOverlay.StationEntityBrackets, None)
    logger.debug('Done configuring view states')
