#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerLandmark.py
from carbonui.primitives.base import ScaleDpi
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Label import MarkerLabelBase
from eve.client.script.ui.shared.maps.maputils import GetNameFromMapCache

class MarkerLabelLandmark(MarkerLabelBase):
    maxVisibleRange = 25000.0
    landMarkData = None
    fontPath = 'res:/UI/Fonts/EveSansNeue-Italic.otf'
    letterSpace = 2

    def Load(self):
        MarkerLabelBase.Load(self)
        self.projectBracket.offsetY = -ScaleDpi(self.markerContainer.height - 20)

    def GetLabelText(self):
        return GetNameFromMapCache(self.landMarkData.landmarkNameID, 'landmark')

    def SetLandmarkData(self, landMarkData):
        self.landMarkData = landMarkData
