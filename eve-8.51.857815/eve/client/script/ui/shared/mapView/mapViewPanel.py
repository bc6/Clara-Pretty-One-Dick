#Embedded file name: eve/client/script/ui/shared/mapView\mapViewPanel.py
from carbonui.primitives.container import Container
from carbonui.primitives.frame import Frame
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.shared.mapView.mapView import MapView
from eve.client.script.ui.shared.mapView.mapViewConst import MAPVIEW_OVERLAY_PADDING_FULLSCREEN, MAPVIEW_OVERLAY_PADDING_NONFULLSCREEN
from eve.client.script.ui.shared.mapView.mapViewSearch import MapViewSearchControl
from eve.client.script.ui.shared.mapView.mapViewSettings import MapViewSettingButtons
from eve.client.script.ui.shared.mapView.dockPanel import DockablePanel
import carbonui.const as uiconst
import uthread
import logging
log = logging.getLogger(__name__)
OVERLAY_SIDE_PADDING_FULLSCREEN = 280
OVERLAY_SIDE_PADDING_NONFULLSCREEN = 6

class MapViewPanel(DockablePanel):
    default_captionLabelPath = 'UI/Neocom/MapBtn'
    default_windowID = 'MapViewPanel'
    default_iconNum = 'res:/UI/Texture/windowIcons/map.png'
    panelID = default_windowID
    mapView = None
    overlayTools = None

    def ApplyAttributes(self, attributes):
        DockablePanel.ApplyAttributes(self, attributes)
        uthread.new(self.InitMapView)

    def Close(self, *args, **kwds):
        DockablePanel.Close(self, *args, **kwds)
        self.mapView = None

    def InitMapView(self):
        self.mapView = MapView(parent=self.GetMainArea(), isFullScreen=self.IsFullscreen())
        sidePadding = OVERLAY_SIDE_PADDING_FULLSCREEN if self.IsFullscreen() else OVERLAY_SIDE_PADDING_NONFULLSCREEN
        self.overlayTools = Container(parent=self.mapView, padding=(sidePadding,
         self.toolbarContainer.height + 6,
         sidePadding,
         6), name='overlayTools', idx=0)
        MapViewSettingButtons(parent=self.toolbarContainer, align=uiconst.CENTERLEFT, onSettingsChangedCallback=self.mapView.OnMapViewSettingChanged, left=4, idx=0)
        MapViewSearchControl(parent=self.overlayTools, mapView=self.mapView, align=uiconst.TOPRIGHT, idx=0)

    def OnDockModeChanged(self, *args, **kwds):
        if self.overlayTools and not self.overlayTools.destroyed:
            sidePadding = OVERLAY_SIDE_PADDING_FULLSCREEN if self.IsFullscreen() else OVERLAY_SIDE_PADDING_NONFULLSCREEN
            self.overlayTools.padLeft = self.overlayTools.padRight = sidePadding
        if self.mapView:
            self.mapView.OnDockModeChanged(self.IsFullscreen())

    def _OnResize(self, *args):
        DockablePanel._OnResize(self, *args)
        if self.mapView:
            self.mapView.UpdateViewPort()

    def SetActive(self, *args, **kwds):
        DockablePanel.SetActive(self, *args, **kwds)
        if self.mapView:
            self.mapView.SetFocusState(True)

    def OnSetInactive(self, *args, **kwds):
        DockablePanel.OnSetInactive(self, *args, **kwds)
        if self.mapView:
            self.mapView.SetFocusState(False)
