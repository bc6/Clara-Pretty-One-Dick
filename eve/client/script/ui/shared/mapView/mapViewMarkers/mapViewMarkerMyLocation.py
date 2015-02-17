#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerMyLocation.py
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerIcon_TrackBall import MarkerIconTrackBall

class MarkerMyLocation(MarkerIconTrackBall):
    solarSystemID = None
    solarSystemMapPosition = None
    solarSystemObjectID = None
    distanceFadeAlpha = False

    def GetMenu(self):
        pass
