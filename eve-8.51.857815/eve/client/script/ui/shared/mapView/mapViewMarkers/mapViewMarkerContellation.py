#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerContellation.py
from carbonui.primitives.base import ReverseScaleDpi, ScaleDpi
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Label import MarkerLabelBase
import trinity

class MarkerLabelConstellation(MarkerLabelBase):
    maxVisibleRange = 7500.0
    minVisibleRange = 500.0

    def __init__(self, *args, **kwds):
        MarkerLabelBase.__init__(self, *args, **kwds)

    def Load(self):
        MarkerLabelBase.Load(self)
        self.textSprite.displayX = ScaleDpi(6)
        self.textSprite.displayY = ScaleDpi(2)
        self.markerContainer.pos = (0,
         0,
         ReverseScaleDpi(self.textSprite.textWidth + 12),
         ReverseScaleDpi(self.textSprite.textHeight + 4))
        self.projectBracket.offsetY = -ScaleDpi(self.markerContainer.height - 8)
        Frame(bgParent=self.markerContainer, color=self.fontColor, blendMode=trinity.TR2_SBM_ADD)
        Fill(bgParent=self.markerContainer, color=(0, 0, 0, 0.5))
