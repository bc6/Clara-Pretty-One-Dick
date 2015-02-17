#Embedded file name: eve/client/script/ui/shared/maps\navigation.py
from carbonui.primitives.line import Line
from eve.client.script.ui.control.eveHint import BubbleHint
import blue
import uthread
import uix
import uiutil
import service
import types
import base
import uicls
import carbonui.const as uiconst
import trinity
from mapcommon import STARMODE_SECURITY
import localization
import geo2
from eve.client.script.ui.shared.maps.palette import MapPalette
MOUSE_HOVER_REFRESH_TIME = 100

class StarMapLayer(uicls.LayerCore):
    __guid__ = 'uicls.StarMapLayer'
    __nonpersistvars__ = ['wnd']
    __update_on_reload__ = 0
    hoveringParticleID = None
    lastMouseXPick = None
    lastMouseYPick = None
    lastMousePickTime = None
    mouseStationary = False
    mouseMovedAfterMouseDown = False

    def __init__(self, *args, **kwargs):
        uicls.LayerCore.__init__(self, *args, **kwargs)
        self.smoothTranslateCameraTasklet = None
        self.smoothDollyCameraTasklet = None
        self.watchCameraTasklet = None

    def __del__(self):
        if self.watchCameraTasklet is not None:
            self.watchCameraTasklet.kill()

    def ApplyAttributes(self, attributes):
        uicls.LayerCore.ApplyAttributes(self, attributes)
        self.lastTimeLeftMouseWasPressed = blue.os.GetWallclockTime()
        self.cursor = uiconst.UICURSOR_SELECT
        self._isPicked = False
        self.lastPickTime = blue.os.GetWallclockTime()
        self.drag = False
        self.bubbleHint = None

    def Close(self, *args):
        uicls.LayerCore.Close(self, *args)
        self.pickThread = None

    def MoveTF(self, tf, dx, dy):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('starmap')
        X = float(dx) / float(trinity.device.width)
        Y = -float(dy) / float(trinity.device.height)
        viewVec = camera.viewVec
        upVec = geo2.Vec3Scale(camera.upVec, Y)
        rightVec = geo2.Vec3Scale(camera.rightVec, X)
        pos = geo2.Vec3Add(rightVec, upVec)
        pos = geo2.Vec3Scale(pos, pow(tf.cameraDistSq, 0.5) * 1.5)
        pos = geo2.QuaternionTransformVector(camera.rotationAroundParent, pos)
        tf.translation = geo2.Vec3Add(tf.translation, pos)

    def ScaleTF(self, tf, dy):
        tf.scaling.Scale(1.0 + 0.025 * float(dy))
        if tf.scaling.x < 80.0:
            tf.scaling.SetXYZ(80.0, 80.0, 80.0)

    def OnMouseEnter(self, *args):
        if not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN

    def SmoothTranslateCamera(self, dx, dy):
        """
        Translate the camera, and keep doing so until friction brings us to a stop.
        """
        dx *= 2.0
        dy *= 2.0

        def DoMove(dx, dy):
            lib = uicore.uilib
            friction = 0.9
            starmap = sm.GetService('starmap')
            while True:
                starmap.TranslateCamera(lib.x, lib.y, int(dx * 0.5), int(dy * 0.5))
                starmap.OnCameraMoved()
                dx = dx * friction
                dy = dy * friction
                if int(dx) == 0 and int(dy) == 0:
                    break
                blue.pyos.synchro.SleepWallclock(10)

        if self.smoothTranslateCameraTasklet is not None:
            self.smoothTranslateCameraTasklet.kill()
        self.smoothTranslateCameraTasklet = uthread.new(DoMove, dx, dy)

    def SmoothOrbitParent(self, dx, dy):
        """
        Orbit the parent; EveCamera has friction built in, so we just need to set
        a good value and we get free inertia. However, this also means that the
        camera will keep moving for a while, so the work we do in OnCameraMoved is
        out of date. So keep an eye on the camera's speed and while it's moving,
        call OnCameraMoved.
        To make sure we pick up curve driven changes, and that we don't exit too
        early because the camera hasn't _started_ moving yet after calling OrbitParent,
        keep the watchdog going at a low 20Hz.
        """

        def WatchCamera(camera):
            epsilon = 0.0001
            yaw = camera.yaw
            pitch = camera.pitch
            starmap = sm.GetService('starmap')
            while True:
                if abs(camera.yaw - yaw) > epsilon or abs(camera.pitch - pitch) > epsilon:
                    starmap.OnCameraMoved()
                    yaw = camera.yaw
                    pitch = camera.pitch
                blue.pyos.synchro.SleepWallclock(50)

        camera = sm.GetService('sceneManager').GetRegisteredCamera('starmap')
        fov = camera.fieldOfView
        camera.OrbitParent(-dx * fov * 0.2, dy * fov * 0.2)
        if self.watchCameraTasklet is None:
            self.watchCameraTasklet = uthread.new(WatchCamera, camera)

    def SmoothDollyCamera(self, dy):
        """
        Dolly the camera, and keep doing so until friction brings us to a stop.
        """
        dy *= 2.5

        def DoDolly(dy):
            friction = 0.9
            camera = sm.GetService('sceneManager').GetRegisteredCamera('starmap')
            if camera is None:
                return
            starmap = sm.GetService('starmap')
            while True:
                camera.Dolly(-dy * 0.002 * abs(camera.translationFromParent))
                camera.translationFromParent = sm.GetService('camera').CheckTranslationFromParent(camera.translationFromParent, source='starmap')
                starmap.OnCameraMoved()
                dy = dy * friction
                if int(dy) == 0:
                    break
                blue.pyos.synchro.SleepWallclock(10)

            starmap.CheckLabelDist()
            self.mouseStationary = False

        if self.smoothDollyCameraTasklet is not None:
            self.smoothDollyCameraTasklet.kill()
        self.smoothDollyCameraTasklet = uthread.new(DoDolly, dy)

    def OnMouseMove(self, *args):
        if not self._isPicked:
            return
        self.mouseMovedAfterMouseDown = True
        starmap = sm.GetService('starmap')
        lib = uicore.uilib
        dx = lib.dx
        dy = lib.dy
        camera = sm.GetService('sceneManager').GetRegisteredCamera('starmap')
        if camera is None:
            return
        ctrl = lib.Key(uiconst.VK_CONTROL)
        shift = lib.Key(uiconst.VK_SHIFT)
        self.mouseDownRegionID = None
        if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            if ctrl and shift and lib.leftbtn and not lib.rightbtn:
                if self.pickedTF is not None:
                    self.MoveTF(self.pickedTF, dx, dy)
                    return
            if ctrl and shift and not lib.leftbtn and lib.rightbtn:
                if self.pickedTF is not None:
                    self.ScaleTF(self.pickedTF, dy)
                    return
        drag = False
        if not lib.leftbtn and lib.rightbtn:
            drag = True
        elif lib.leftbtn and not lib.rightbtn:
            if starmap.IsFlat():
                drag = True
        if drag:
            self.SmoothTranslateCamera(dx, dy)
        elif lib.leftbtn and lib.rightbtn:
            self.SmoothDollyCamera(dy)
        elif lib.leftbtn and not lib.rightbtn:
            self.SmoothOrbitParent(dx, dy)
        else:
            regionID = self.PickRegionID()
            if regionID is not None:
                label = starmap.GetRegionLabel(regionID)
                starmap.UpdateLines(regionID)
        self.drag = drag

    def OverridePick(self, x, y):
        if uicore.uilib.leftbtn or uicore.uilib.rightbtn:
            return self
        mouseX = uicore.uilib.x
        mouseY = uicore.uilib.y
        if self.lastMouseXPick is None:
            self.lastMouseXPick = mouseX
            self.lastMouseYPick = mouseY
            self.mouseStationary = False
        if abs(mouseX - self.lastMouseXPick) + abs(mouseY - self.lastMouseYPick) == 0:
            if not self.mouseStationary:
                self.mouseStationary = True
                self.pickThread = base.AutoTimer(5, self.CheckPickNew, mouseX, mouseY)
        else:
            self.mouseStationary = False
        if not self.lastMousePickTime or blue.os.TimeDiffInMs(self.lastMousePickTime, blue.os.GetWallclockTime()) >= 100:
            self.lastMouseXPick = mouseX
            self.lastMouseYPick = mouseY
            self.lastMousePickTime = blue.os.GetWallclockTime()
        return self

    def CheckPickNew(self, mouseX, mouseY):
        self.pickThread = None
        if self.destroyed:
            return
        if (mouseX, mouseY) != (uicore.uilib.x, uicore.uilib.y):
            return
        starmap = sm.GetService('starmap')
        particleID = starmap.PickParticle()
        if particleID != None and self.hoveringParticleID != particleID:
            solarsystemID = starmap.GetItemIDFromParticleID(particleID)
            if solarsystemID:
                starmap.ShowCursorInterest(solarsystemID, particleID)
                uthread.new(starmap.UpdateLines, solarsystemID)
        self.hoveringParticleID = particleID

    def PickRegionID(self):
        """
        this checks to see if there is a region label in the way and if so, returns its regionID
        """
        scene = sm.GetService('sceneManager').GetRegisteredScene('starmap')
        if scene is None:
            return
        x, y = uicore.ScaleDpi(uicore.uilib.x), uicore.ScaleDpi(uicore.uilib.y)
        projection, view, viewport = uix.GetFullscreenProjectionViewAndViewport()
        pick = scene.PickObject(x, y, projection, view, viewport)
        if pick is not None:
            if hasattr(pick, 'regionID'):
                return pick.regionID
            if pick.name[:11] == '__regionDot':
                return int(pick.name[11:])

    def ShowBubbleHint(self, particleID, solarsystemID, mapColor = None, extended = 0):
        starmap = sm.GetService('starmap')
        if not extended:
            blue.pyos.synchro.SleepWallclock(25)
            if self.destroyed:
                return
            _particleID = starmap.PickParticle()
            if _particleID is None or _particleID != particleID:
                self.state = uiconst.UI_NORMAL
                return
        self.bubbleHint = (particleID,
         solarsystemID,
         mapColor,
         extended)
        eve.Message('click')
        mapData = sm.GetService('map').GetItem(solarsystemID)
        bubblehint = sm.GetService('systemmap').GetBubbleHint(solarsystemID, mapData=mapData, extended=extended)
        if self.destroyed:
            return
        hint = bubblehint or [mapData.itemName]
        data = starmap.GetStarData()
        if particleID in data:
            hint.append('<line>')
            hint.append(localization.GetByLabel('UI/Map/Navigation/hintStatistics'))
            hintFunc, hintArgs = data[particleID]
            particleData = hintFunc(*hintArgs)
            if type(particleData) == types.TupleType:
                for each in particleData:
                    hint += each

            else:
                hint.append(particleData)
        if hint:
            bubble = self.GetBubble()
            if extended:
                bubble.state = uiconst.UI_DISABLED
            else:
                bubble.state = uiconst.UI_HIDDEN
            bubble.ShowHint(hint, 0)
            uiutil.SetOrder(bubble.parent, 0)
            blue.pyos.synchro.Yield()
            if bubble.destroyed or self.destroyed:
                return
            bubble.state = uiconst.UI_NORMAL
            self.hoveringParticleID = particleID
        starmap.ShowCursorInterest(solarsystemID)
        self.state = uiconst.UI_NORMAL

    def ExpandBubbleHint(self, bubble, expand = 1):
        if not self.destroyed and self.bubbleHint:
            tple, regionID, mapColor, exp = self.bubbleHint
            if not exp:
                self.state = uiconst.UI_DISABLED
                uthread.new(self.ShowBubbleHint, tple, regionID, mapColor, 1)

    def GetBubble(self):
        mapUICursor = sm.GetService('starmap').GetUICursor()
        if mapUICursor:
            for each in mapUICursor.children[:]:
                if each.name == 'bubblehint':
                    each.Close()

        bubble = BubbleHint(parent=mapUICursor, name='bubblehint', align=uiconst.TOPLEFT, width=0, height=0, idx=0, state=uiconst.UI_PICKCHILDREN)
        bubble.sr.ExpandHint = self.ExpandBubbleHint
        return bubble

    def ResetHightlight(self):
        blue.pyos.synchro.SleepWallclock(400)
        if self.destroyed:
            return
        regionID = self.PickRegionID()
        sm.GetService('starmap').UpdateLines(regionID)

    def OnClick(self, *args):
        if self.destroyed:
            return
        if self.mouseMovedAfterMouseDown:
            return
        starmap = sm.GetService('starmap')
        particleID = starmap.PickParticle()
        if particleID:
            if particleID == self.hoveringParticleID:
                solarSystemID = starmap.GetItemIDFromParticleID(particleID)
                starmap.SetInterest(solarSystemID)
                return
        regionID = self.PickRegionID()
        if regionID is not None and getattr(self, 'mouseDownRegionID', None) == regionID:
            starmap.SetInterest(regionID)

    def OnMouseDown(self, button):
        self.mouseMovedAfterMouseDown = False
        self._isPicked = True
        scene = sm.GetService('sceneManager').GetRegisteredScene('starmap')
        self.pickedTF = None
        if scene is not None:
            projection, view, viewport = uix.GetFullscreenProjectionViewAndViewport()
            self.pickedTF = scene.PickObject(uicore.ScaleDpi(uicore.uilib.x), uicore.ScaleDpi(uicore.uilib.y), projection, view, viewport)
        self.mouseDownRegionID = self.PickRegionID()

    def OnMouseUp(self, button):
        if not (uicore.uilib.leftbtn or uicore.uilib.rightbtn):
            self._isPicked = False
        if not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN
        self.lastTimeLeftMouseWasPressed = blue.os.GetWallclockTime()
        self.pickedTF = None

    def OnMouseWheel(self, *args):
        self.ZoomBy(uicore.uilib.dz)
        return 1

    def ZoomBy(self, amount):
        if self.destroyed:
            return
        self.SmoothDollyCamera(-amount / 10)

    def OnDblClick(self, *args):
        if self.destroyed:
            return
        starmap = sm.GetService('starmap')
        solarSystemID = starmap.PickSolarSystemID()
        if solarSystemID is not None:
            starmap.SetInterest(solarSystemID)

    def GetMenu(self):
        if self.drag:
            self.drag = False
            return
        mapSvc = sm.GetService('map')
        starmapSvc = sm.GetService('starmap')
        solarsystemID = starmapSvc.PickSolarSystemID()
        if solarsystemID is not None:
            return starmapSvc.GetItemMenu(solarsystemID)
        regionID = self.PickRegionID()
        if regionID:
            return starmapSvc.GetItemMenu(regionID)
        if blue.os.GetWallclockTimeNow() - self.lastTimeLeftMouseWasPressed < 30000L:
            return
        loctations = [(uiutil.MenuLabel('UI/Map/Navigation/menuSolarSystem'), starmapSvc.SetInterest, (eve.session.solarsystemid2, 1)), (uiutil.MenuLabel('UI/Map/Navigation/menuConstellation'), starmapSvc.SetInterest, (eve.session.constellationid, 1)), (uiutil.MenuLabel('UI/Map/Navigation/menuRegion'), starmapSvc.SetInterest, (eve.session.regionid, 1))]
        panel = [(uiutil.MenuLabel('UI/Map/Navigation/menuSearch'), self.ShowPanel, (localization.GetByLabel('UI/Map/Navigation/menuSearch'),)), (uiutil.MenuLabel('UI/Map/Navigation/menuDisplayMapSettings'), self.ShowPanel, (localization.GetByLabel('UI/Map/Navigation/lblStarMap'),))]
        m = [(uiutil.MenuLabel('UI/Map/Navigation/menuSelectCurrent'), loctations)]
        waypoints = starmapSvc.GetWaypoints()
        if len(waypoints):
            waypointList = []
            wpCount = 1
            for waypointID in waypoints:
                waypointItem = mapSvc.GetItem(waypointID)
                caption = uiutil.MenuLabel('UI/Map/Navigation/menuWaypointEntry', {'itemName': waypointItem.itemName,
                 'wpCount': wpCount})
                waypointList += [(caption, starmapSvc.SetInterest, (waypointID, 1))]
                wpCount += 1

            m.append((uiutil.MenuLabel('UI/Map/Navigation/menuSelectWaypoint'), waypointList))
        m += [None, (uiutil.MenuLabel('UI/Map/Navigation/menuWorldControlPanel'), panel)]
        if len(starmapSvc.GetWaypoints()) > 0:
            m.append(None)
            m.append((uiutil.MenuLabel('UI/Map/Navigation/menuClearWaypoints'), starmapSvc.ClearWaypoints, (None,)))
            if starmapSvc.genericRoute:
                m.append((uiutil.MenuLabel('UI/Map/Navigation/menuClearRoute'), starmapSvc.RemoveGenericPath))
        if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            landmarkScales = [(uiutil.MenuLabel('UI/Map/Navigation/menuAllImportance'), starmapSvc.LM_DownloadLandmarks, ()),
             (uiutil.MenuLabel('UI/Map/Navigation/menuImportance', {'level': 0}), starmapSvc.LM_DownloadLandmarks, (0,)),
             (uiutil.MenuLabel('UI/Map/Navigation/menuImportance', {'level': 1}), starmapSvc.LM_DownloadLandmarks, (1,)),
             (uiutil.MenuLabel('UI/Map/Navigation/menuImportance', {'level': 2}), starmapSvc.LM_DownloadLandmarks, (2,)),
             (uiutil.MenuLabel('UI/Map/Navigation/menuImportance', {'level': 3}), starmapSvc.LM_DownloadLandmarks, (3,)),
             (uiutil.MenuLabel('UI/Map/Navigation/menuImportance', {'level': 4}), starmapSvc.LM_DownloadLandmarks, (4,)),
             (uiutil.MenuLabel('UI/Map/Navigation/menuImportance', {'level': 5}), starmapSvc.LM_DownloadLandmarks, (5,))]
            m.append(None)
            m.append((uiutil.MenuLabel('UI/Map/Navigation/menuGetLandmarks'), landmarkScales))
            if eve.session.role & service.ROLE_WORLDMOD:
                m.append((uiutil.MenuLabel('UI/Map/Navigation/menuUpdateLandmarks'), starmapSvc.LM_UploadLandmarks, ()))
            m.append((uiutil.MenuLabel('UI/Map/Navigation/menuHideLandmarks'), starmapSvc.LM_ClearLandmarks, ()))
        return m

    def ShowPanel(self, panelName):
        wnd = MapPalette.Open()
        if wnd:
            uthread.pool('MapNav::ShowPanel', wnd.ShowPanel, panelName)
