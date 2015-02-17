#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerSolarSystemObject.py
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase import MarkerIconBase

class MarkerSolarSystemObject(MarkerIconBase):
    solarSystemID = None
    solarSystemMapPosition = None
    solarSystemObjectID = None
    maxVisibleRange = 500.0
    minVisibleRange = 0.0

    def __init__(self, *args, **kwds):
        MarkerIconBase.__init__(self, *args, **kwds)
        self.solarSystemID = kwds.get('solarSystemID', None)
        self.solarSystemMapPosition = kwds.get('solarSystemMapPosition', None)
        self.solarSystemObjectID = kwds.get('solarSystemObjectID', None)

    def GetMenu(self):
        print 'solarSystemObjectID', self.solarSystemObjectID, self.markerID[2]
        return self.eventHandler.GetMenuForObjectID(self.markerID[2])
