#Embedded file name: eve/client/script/ui/shared/mapView\mapViewNavigation.py
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
import carbonui.const as uiconst

class MapViewNavigation(Container):
    lastPickInfo = None
    isTabStop = True
    pickInfo = None
    pickPosition = None

    def Close(self, *args):
        Container.Close(self, *args)
        self.mapView = None
        self.pickTimer = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.mapView = attributes.mapView
        self.pickTimer = AutoTimer(20, self.CheckPick)

    def OnMouseMove(self, *args):
        if uicore.IsDragging():
            return
        camera = self.mapView.camera
        if camera is None:
            return
        self.doPick = False
        lib = uicore.uilib
        dx = lib.dx
        dy = lib.dy
        drag = False
        if drag:
            camera.PanMouseDelta(dx, dy)
        elif lib.leftbtn and lib.rightbtn:
            camera.ZoomMouseDelta(dx, dy)
        elif lib.leftbtn and not lib.rightbtn:
            camera.OrbitMouseDelta(dx, dy)

    def CheckPick(self):
        if uicore.uilib.mouseOver is not self or uicore.uilib.leftbtn or uicore.uilib.rightbtn:
            return
        mx, my = uicore.uilib.x, uicore.uilib.y
        if self.pickPosition:
            dX = abs(mx - self.pickPosition[0])
            dY = abs(my - self.pickPosition[1])
            picked = self.pickPosition[-1]
            if dX == 0 and dY == 0:
                if not picked:
                    pickInfo = self.mapView.GetPickObjects(mx, my, getMarkers=False)
                    if pickInfo:
                        self.mapView.SetHilightItem(pickInfo[0])
                    else:
                        self.mapView.SetHilightItem(None)
                    self.pickPosition = (mx, my, True)
                return
        self.pickPosition = (mx, my, False)

    def PickRegionID(self):
        """
        this checks to see if there is a region label in the way and if so, returns its regionID
        """
        return None

    def OnDblClick(self, *args):
        if self.destroyed:
            return
        self.ClickPickedObject(True, uicore.uilib.x, uicore.uilib.y)

    def OnClick(self, *args):
        if not self.doPick:
            return
        self.clickTimer = AutoTimer(250, self.ClickPickedObject, uicore.uilib.Key(uiconst.VK_CONTROL), uicore.uilib.x, uicore.uilib.y)

    def ClickPickedObject(self, zoomTo, mouseX, mouseY):
        self.clickTimer = None
        if self.destroyed:
            return
        pickInfo = self.mapView.GetPickObjects(mouseX, mouseY)
        if pickInfo:
            self.mapView.SetActiveItem(pickInfo[0][0], zoomToItem=zoomTo)

    def OnMouseDown(self, button):
        self.doPick = button in (uiconst.MOUSELEFT, uiconst.MOUSERIGHT)

    def OnMouseUp(self, button):
        pass

    def OnMouseWheel(self, *args):
        camera = self.mapView.camera
        if camera:
            camera.ZoomMouseWheelDelta(uicore.uilib.dz)
        return 1

    def GetMenuForObjectID(self, objectID):
        return self.mapView.GetItemMenu(objectID)

    def GetMenu(self):
        if not self.doPick:
            return
        mapSvc = sm.GetService('map')
        pickInfo = self.mapView.GetPickObjects(uicore.uilib.x, uicore.uilib.y)
        if pickInfo and len(pickInfo) == 1:
            return self.GetMenuForObjectID(pickInfo[0][0])
        loctations = [(MenuLabel('UI/Map/Navigation/menuSolarSystem'), self.mapView.SetActiveItem, (session.solarsystemid2, 1)), (MenuLabel('UI/Map/Navigation/menuConstellation'), self.mapView.SetActiveItem, (session.constellationid, 1)), (MenuLabel('UI/Map/Navigation/menuRegion'), self.mapView.SetActiveItem, (session.regionid, 1))]
        m = [(MenuLabel('UI/Map/Navigation/menuSelectCurrent'), loctations)]
        waypoints = sm.StartService('starmap').GetWaypoints()
        if len(waypoints):
            waypointList = []
            wpCount = 1
            for waypointID in waypoints:
                waypointItem = mapSvc.GetItem(waypointID)
                caption = MenuLabel('UI/Map/Navigation/menuWaypointEntry', {'itemName': waypointItem.itemName,
                 'wpCount': wpCount})
                waypointList += [(caption, self.mapView.SetActiveItem, (waypointID, 1))]
                wpCount += 1

            m.append((MenuLabel('UI/Map/Navigation/menuSelectWaypoint'), waypointList))
        if len(sm.StartService('starmap').GetWaypoints()) > 0:
            m.append(None)
            m.append((MenuLabel('UI/Map/Navigation/menuClearWaypoints'), sm.StartService('starmap').ClearWaypoints, (None,)))
            if self.mapView.genericRoute:
                m.append((MenuLabel('UI/Map/Navigation/menuClearRoute'), sm.StartService('starmap').RemoveGenericPath))
        return m
