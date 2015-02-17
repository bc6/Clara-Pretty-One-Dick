#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerMyHome.py
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Icon import MarkerIconBase

class MarkerMyHome(MarkerIconBase):
    distanceFadeAlpha = False

    def __init__(self, *args, **kwds):
        MarkerIconBase.__init__(self, *args, **kwds)
        self.stationInfo = kwds.get('stationInfo')

    def GetMenu(self):
        if self.stationInfo:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(self.stationInfo.stationID, self.stationInfo.stationTypeID, noTrace=1)
