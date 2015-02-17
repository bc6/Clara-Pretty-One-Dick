#Embedded file name: eve/client/script/ui/shared/mapView\mapViewMarkersHandler.py
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.shared.mapView.mapViewConst import PRIMARY_MARKER_TYPES
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase_Icon import MarkerIconBase
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerContellation import MarkerLabelConstellation
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerIcon_TrackBall import MarkerIconTrackBall
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerLandmark import MarkerLabelLandmark
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerRegion import MarkerLabelRegion
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerCelestial import MarkerCelestial
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerSolarSystem import MarkerLabelSolarSystem
from eve.client.script.ui.shared.mapView.mapViewUtil import IsDynamicMarkerType
import uthread
import blue
import sys
import carbonui.const as uiconst

def DoMarkersIntersect(marker1, marker2):
    marker1Bound = marker1.GetBoundaries()
    marker2Bound = marker2.GetBoundaries()
    l1, t1, r1, b1 = marker1Bound
    l2, t2, r2, b2 = marker2Bound
    overlapX = not (r1 <= l2 or l1 >= r2)
    overlapY = not (b1 <= t2 or t1 >= b2)
    return bool(overlapX and overlapY)


def FindOverlaps2(markers):
    isOverlapped = set()
    isOverlapping = {}
    for d1, marker1 in markers:
        if marker1.markerID in isOverlapped:
            continue
        for d2, marker2 in markers:
            if marker1 is marker2:
                continue
            if marker2.markerID in isOverlapped:
                continue
            intersect = DoMarkersIntersect(marker1, marker2)
            if intersect:
                isOverlapping.setdefault(marker1.markerID, []).append(marker2)
                isOverlapped.add(marker2.markerID)

    return (isOverlapping, isOverlapped)


class MapViewMarkersHandler(object):
    projectBrackets = None
    markerCurveSet = None
    markerLayer = None
    updateThread = None
    mapView = None
    disabledMarkers = None
    eventHandler = None
    clickTimer = None
    cameraTranslationFromParent = 1.0
    _yScaleFactor = 1.0

    def __init__(self, mapView, markerCurveSet, markerLayer, eventHandler = None):
        self.mapView = mapView
        self.projectBrackets = {}
        self.hilightMarkers = set()
        self.activeMarkers = set()
        self.overlapMarkers = set()
        self.markerCurveSet = markerCurveSet
        self.markerLayer = markerLayer
        self.eventHandler = eventHandler
        self.checkOverlapTimer = AutoTimer(250, self.CheckOverlaps)

    def __del__(self):
        self.StopHandler()

    def CheckOverlaps(self):
        markers = []
        for markerID in self.overlapMarkers:
            markerObject = self.projectBrackets.get(markerID, None)
            if markerObject and markerObject.markerContainer and not markerObject.markerContainer.destroyed:
                if markerID[0] in PRIMARY_MARKER_TYPES:
                    markers.append((0, markerObject))
                else:
                    markerObjectCameraDistance = markerObject.GetCameraDistance()
                    markers.append((markerObjectCameraDistance, markerObject))

        markersSorted = sorted(markers)
        isOverlapping, isOverlapped = FindOverlaps2(markersSorted)
        for d, markerObject in reversed(markersSorted):
            markerID = markerObject.markerID
            if markerID in isOverlapping:
                markerObject.MoveToFront()
                markerObject.RegisterOverlapMarkers(isOverlapping[markerID])
            elif markerID in isOverlapped:
                markerObject.SetOverlappedState(True)
            else:
                markerObject.MoveToFront()
                markerObject.SetOverlappedState(False)

        for marker in self.GetActiveAndHilightedMarkers():
            marker.MoveToFront()

    def GetExtraMouseOverInfoForMarker(self, markerID):
        if self.mapView:
            return self.mapView.GetExtraMouseOverInfoForItemID(markerID)

    def ReloadAll(self):
        for itemID, markerObject in self.projectBrackets.iteritems():
            if markerObject:
                markerObject.Reload()

    def SetDisplayStateOverrideFilter(self, markersToShow):
        filtering = bool(markersToShow)
        for itemID, markerObject in self.projectBrackets.iteritems():
            if IsDynamicMarkerType(markerObject.markerID):
                continue
            if not filtering or itemID in markersToShow:
                markerObject.displayStateOverride = None
            else:
                markerObject.displayStateOverride = False

    @apply
    def yScaleFactor():

        def fget(self):
            return self._yScaleFactor

        def fset(self, value):
            self._yScaleFactor = value
            for itemID, markerObject in self.projectBrackets.iteritems():
                markerObject.UpdatePosition()

        return property(**locals())

    def StopHandler(self):
        if self.updateThread:
            self.updateThread.kill()
        self.updateThread = None
        self.checkOverlapTimer = None
        if self.projectBrackets:
            for itemID, markerObject in self.projectBrackets.iteritems():
                markerObject.Close()

        self.projectBrackets = None
        self.mapView = None
        self.markerLayer = None
        self.markerCurveSet = None
        self.eventHandler = None

    def OnMarkerHilighted(self, marker):
        self.mapView.SetHilightItem(marker.markerID)

    def OnMarkerSelected(self, marker, zoomTo = False):
        self.mapView.SetActiveItem(marker.markerID, zoomToItem=zoomTo)

    def HilightMarkers(self, markerIDs):
        hilightMarkers = markerIDs
        for oldMarkerID in self.hilightMarkers:
            if oldMarkerID not in hilightMarkers:
                oldMarker = self.GetMarkerByID(oldMarkerID)
                if oldMarker:
                    oldMarker.SetHilightState(False)

        for newMarkerID in hilightMarkers:
            newMarker = self.GetMarkerByID(newMarkerID)
            if newMarker:
                newMarker.SetHilightState(True)

        self.hilightMarkers = set(hilightMarkers)

    def ActivateMarkers(self, markerIDs):
        activeMarkers = markerIDs
        for oldMarkerID in self.activeMarkers:
            if oldMarkerID not in activeMarkers:
                oldMarker = self.GetMarkerByID(oldMarkerID)
                if oldMarker:
                    oldMarker.SetActiveState(False)

        for newMarkerID in activeMarkers:
            newMarker = self.GetMarkerByID(newMarkerID)
            if newMarker:
                newMarker.SetActiveState(True)

        self.activeMarkers = set(activeMarkers)

    def RefreshActiveAndHilightedMarkers(self):
        for marker in self.GetActiveAndHilightedMarkers():
            marker.UpdateActiveAndHilightState()

    def GetActiveAndHilightedMarkers(self):
        ret = set()
        for markerID in self.hilightMarkers.union(self.activeMarkers):
            marker = self.GetMarkerByID(markerID)
            if marker:
                ret.add(marker)

        return ret

    def IsActiveOfHilighted(self, markerID):
        return markerID in self.activeMarkers or markerID in self.hilightMarkers

    def RemoveMarker(self, markerID, fadeOut = False):
        try:
            self.overlapMarkers.remove(markerID)
        except:
            pass

        markerObject = self.projectBrackets.pop(markerID, None)
        if markerObject:
            if fadeOut:
                markerObject.FadeOutAndClose()
            else:
                markerObject.Close()

    def GetMarkerByID(self, markerID):
        return self.projectBrackets.get(markerID, None)

    def _AddPositionMarker(self, **kwds):
        markerID = kwds.get('markerID', None)
        markerClass = kwds.get('markerClass', None)
        if markerID in self.projectBrackets:
            return self.projectBrackets[markerID]
        kwds['parentContainer'] = self.markerLayer
        kwds['curveSet'] = self.markerCurveSet
        kwds['selectionCallback'] = self.OnMarkerSelected
        kwds['hilightCallback'] = self.OnMarkerHilighted
        kwds['markerHandler'] = self
        kwds['eventHandler'] = self.eventHandler
        markerObject = markerClass(**kwds)
        self.projectBrackets[markerID] = markerObject
        return markerObject

    def RegisterMarker(self, markerObject):
        self.projectBrackets[markerObject.markerID] = markerObject

    def AddStarMarker(self, markerID, position):
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerLabelSolarSystem)

    def AddConstellationMarker(self, markerID, position):
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerLabelConstellation)

    def AddRegionMarker(self, markerID, position):
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerLabelRegion)

    def AddLandmarkMarker(self, markerID, position):
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerLabelLandmark)

    def AddGenericIconMarker(self, markerID, position, **kwds):
        self.overlapMarkers.add(markerID)
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerIconBase, **kwds)

    def AddIconTrackBallMarker(self, markerID, position, **kwds):
        self.overlapMarkers.add(markerID)
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerIconTrackBall, **kwds)

    def AddSolarSystemObjectMarker(self, markerID, position, **kwds):
        self.overlapMarkers.add(markerID)
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=MarkerCelestial, **kwds)

    def AddMarker(self, markerID, position, markerClass, **kwds):
        self.overlapMarkers.add(markerID)
        return self._AddPositionMarker(markerID=markerID, position=position, markerClass=markerClass, **kwds)

    def RegisterCameraTranslationFromParent(self, cameraTranslationFromParent):
        self.cameraTranslationFromParent = cameraTranslationFromParent
