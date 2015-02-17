#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerRegion.py
from carbon.common.script.util.commonutils import StripTags
from carbonui.primitives.base import ScaleDpi
from carbonui.util.bunch import Bunch
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Label import MarkerLabelBase

class MarkerLabelRegion(MarkerLabelBase):
    fontSize = 10
    maxVisibleRange = 200000.0
    minVisibleRange = 1500.0
    letterSpace = 3

    def GetLabelText(self):
        return cfg.evelocations.Get(self.markerID).name.upper()

    def Load(self):
        MarkerLabelBase.Load(self)
        self.projectBracket.offsetY = -ScaleDpi(self.markerContainer.height - 20)

    def GetDragData(self, *args):
        dragDisplayText, url = cfg.evelocations.Get(self.markerID).name, 'showinfo:%d//%d' % (const.typeRegion, self.markerID)
        entry = Bunch()
        entry.__guid__ = 'TextLink'
        entry.url = url
        entry.dragDisplayText = dragDisplayText
        entry.displayText = StripTags(dragDisplayText)
        return [entry]
