#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerCelestial.py
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Icon import MarkerIconBase

class MarkerCelestial(MarkerIconBase):
    solarSystemID = None
    solarSystemMapPosition = None
    solarSystemObjectID = None
    maxVisibleRange = 500.0
    minVisibleRange = 0.0
    celestialData = None

    def __init__(self, *args, **kwds):
        MarkerIconBase.__init__(self, *args, **kwds)
        self.solarSystemID = kwds.get('solarSystemID', None)
        self.solarSystemMapPosition = kwds.get('solarSystemMapPosition', None)
        self.solarSystemObjectID = kwds.get('solarSystemObjectID', None)
        self.celestialData = kwds.get('celestialData', None)

    def GetMenu(self):
        return sm.GetService('menu').CelestialMenu(self.celestialData.itemID, typeID=self.celestialData.typeID, noTrace=1)
