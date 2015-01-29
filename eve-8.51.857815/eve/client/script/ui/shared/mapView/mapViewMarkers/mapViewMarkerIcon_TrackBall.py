#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerIcon_TrackBall.py
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Icon import MarkerIconBase
from eve.client.script.ui.shared.mapView.mapViewUtil import SolarSystemPosToMapPos
import geo2

class MarkerIconTrackBall(MarkerIconBase):
    trackObjectID = None
    solarSystemMapPosition = None

    def __init__(self, *args, **kwds):
        MarkerIconBase.__init__(self, *args, **kwds)
        self.trackObjectID = kwds.get('trackObjectID', None)
        self.solarSystemMapPosition = kwds.get('solarSystemMapPosition', None)
        self.UpdateTrackPosition()
        self.updateTick = AutoTimer(250, self.UpdateTrackPosition)

    def Close(self, *args, **kwds):
        MarkerIconBase.Close(self, *args, **kwds)
        self.updateTick = None

    def UpdateTrackPosition(self):
        mapPosition = self.solarSystemMapPosition
        bp = sm.GetService('michelle').GetBallpark()
        if bp is not None:
            ball = bp.GetBall(self.trackObjectID)
            if ball is not None:
                localPosition = SolarSystemPosToMapPos((ball.x, ball.y, ball.z))
                mapPosition = geo2.Vec3Add(mapPosition, localPosition)
        self.SetPosition(mapPosition)
