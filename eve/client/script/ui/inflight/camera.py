#Embedded file name: eve/client/script/ui/inflight\camera.py
from math import sin, cos
import mathUtil
import blue
import service
import trinity
import uthread
import state
import destiny
import geo2
import carbonui.const as uiconst
import localization
import telemetry
import audio2
import evecamera.shaker as shaker
import evecamera.dungeonhack as dungeonhack
import evecamera.utils as camutils
import evecamera.cameratarget as camtarget
import evecamera.tracking
import evecamera.animation as camanim
import evegraphics.settings as gfxsettings
import evespacescene
from mapcommon import ZOOM_MIN_STARMAP, ZOOM_MAX_STARMAP, ZOOM_NEAR_SYSTEMMAP, ZOOM_FAR_SYSTEMMAP
SIZEFACTOR = 1e-07

class CameraMgr(service.Service):
    __guid__ = 'svc.camera'
    __update_on_reload__ = 0
    __notifyevents__ = ['OnSpecialFX',
     'DoBallClear',
     'DoBallRemove',
     'OnSessionChanged',
     'OnSetDevice',
     'OnGraphicSettingsChanged',
     'DoBallsRemove',
     'DoSimClockRebase',
     'OnBallparkSetState']
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.clientToolsScene = None
        self.checkDistToEgoThread = None
        self.maxLookatRange = 100000.0
        self.cachedCameraTranslation = -1
        self.dungeonHack = dungeonhack.DungeonHack(self)
        self.targetTracker = evecamera.tracking.Tracker(self)
        self.shakeController = shaker.ShakeController(self)
        self.animationController = camanim.AnimationController(self)
        self.cameraParents = {}
        self.spaceCamera = None

    def Run(self, *args):
        self.Reset()
        self.pending = None
        self.busy = None

    def Stop(self, stream):
        self.Cleanup()

    def DisableFreeLook(self):
        if self.dungeonHack.IsFreeLook():
            self.dungeonHack.SetFreeLook(False)

    def DoBallClear(self, solitem):
        self.DisableFreeLook()
        cameraParent = self.GetCameraParent()
        if cameraParent is not None:
            cameraParent.parent = None

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if session.shipid is not None:
            lookingAtID = self.LookingAt()
            if lookingAtID is not None and ball.id == lookingAtID:
                uthread.new(self.AdjustLookAtTarget, ball)

    def DoSimClockRebase(self, times):
        self.animationController.DoSimClockRebase(times)

    def AdjustLookAtTarget(self, ball):
        if session.shipid is None:
            return
        cameraParent = self.GetCameraParent()
        lookingAtID = self.LookingAt()
        if cameraParent and cameraParent.parent and cameraParent.parent == ball.model:
            self.DisableFreeLook()
            cameraParent.parent = None
        if lookingAtID and ball.id == lookingAtID and lookingAtID != session.shipid:
            self.LookAt(session.shipid)

    def OnSpecialFX(self, shipID, moduleID, moduleTypeID, targetID, otherTypeID, guid, isOffensive, start, active, duration = -1, repeat = None, startTime = None, timeFromStart = 0, graphicInfo = None):
        if guid == 'effects.Warping':
            if shipID == session.shipid:
                self.DisableFreeLook()
                if self.LookingAt() is not None and self.LookingAt() != session.shipid:
                    self.LookAt(session.shipid)

    def OnSetDevice(self, *args):
        """
        We might have to alter the maximum zoom if the aspect ratio has changed.
        """
        if session.stationid:
            return
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        blue.synchro.Yield()
        self.boundingBoxCache = {}
        if camera is not None:
            camera.translationFromParent = self.CheckTranslationFromParent(camera.translationFromParent)

    def OnSessionChanged(self, isRemote, sess, change):
        """
        Make sure to turn off the free look camera if we are /tr'ing away.
        """
        if 'locationid' in change.iterkeys():
            self.DisableFreeLook()
        self.HandleShipSessionChange(change)

    def OnBallparkSetState(self, *args):
        self.LookAt(session.shipid, self.cachedCameraTranslation, smooth=False)

    def HandleShipSessionChange(self, change):
        if 'shipid' in change:
            oldID = change['shipid'][0]
            newID = change['shipid'][1]
            bp = sm.GetService('michelle').GetBallpark()
            if bp is None:
                return
            if newID is not None and newID not in bp.slimItems and oldID is not None:
                self.lookingAt = newID
            else:
                self.LookAt(newID, self.cachedCameraTranslation)

    def Cleanup(self):
        pass

    def Reset(self):
        self.inited = 0
        self.lookingAt = None
        self.boundingBoxCache = {}
        self.zoomFactor = None
        tm = sm.GetService('tactical').GetMain()
        if tm:
            for each in tm.children[:]:
                if each.name in ('camerastate', 'camlevels'):
                    each.Close()

        st = uicore.layer.station
        if st:
            for each in st.children[:]:
                if each.name in ('camerastate', 'camlevels'):
                    each.Close()

    def _GetTrackableCurve(self, itemID):
        item = sm.StartService('michelle').GetBall(itemID)
        if item is None or getattr(item, 'model', None) is None:
            return
        if item.model.__bluetype__ in evespacescene.EVESPACE_TRINITY_CLASSES:
            tracker = trinity.EveSO2ModelCenterPos()
            tracker.parent = item.model
            return tracker
        return item

    def SetCameraInterest(self, itemID):
        if self.dungeonHack.IsFreeLook():
            return
        cameraInterest = self.GetCameraInterest()
        camera = self.GetSpaceCamera()
        if camera is None:
            return
        trackable = self._GetTrackableCurve(itemID)
        cameraInterest.translationCurve = trackable

    def SetCameraParent(self, itemID):
        if self.dungeonHack.IsFreeLook():
            return
        cameraParent = self.GetCameraParent()
        if cameraParent is None:
            return
        camera = self.GetSpaceCamera()
        if camera is None:
            return
        trackable = self._GetTrackableCurve(itemID)
        if trackable is None:
            self.LookAt(session.shipid)
            return
        cameraParent.translationCurve = trackable

    def _AbortLookAtOther(self):
        self.ResetCamera()
        self.checkDistToEgoThread = None

    def _CheckDistanceToEgo(self):
        while self.checkDistToEgoThread is not None:
            if self.lookingAt is not None:
                lookingAtItem = sm.GetService('michelle').GetBall(self.lookingAt)
                if lookingAtItem is None or lookingAtItem.surfaceDist > self.maxLookatRange:
                    self._AbortLookAtOther()
            blue.synchro.Yield()

    def _LookingAtSelf(self):
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        if scene is not None and scene.dustfield is not None:
            scene.dustfield.display = True
        self.checkDistToEgoThread = None

    def _IsLookingAtOtherOK(self, item):
        obs = sm.GetService('target').IsObserving()
        if item is None:
            return False
        if item.mode == destiny.DSTBALL_WARP:
            return False
        if not obs and item.surfaceDist > self.maxLookatRange:
            sm.GetService('gameui').Say(localization.GetByLabel('UI/Camera/OutsideLookingRange'))
            return False
        return True

    def _LookingAtOther(self):
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        if scene is not None:
            if scene.dustfield is not None:
                scene.dustfield.display = False
        if self.checkDistToEgoThread is None:
            self.checkDistToEgoThread = uthread.pool('MenuSvc>checkDistToEgoThread', self._CheckDistanceToEgo)
        return True

    def _WaitForTech3Model(self, item):
        if item is None or getattr(item, 'model', None) is None:
            if hasattr(item, 'loadingModel'):
                while item.loadingModel:
                    blue.synchro.Yield()

    def LookAt(self, itemID, setZ = None, resetCamera = False, smooth = True):
        item = sm.StartService('michelle').GetBall(itemID)
        if not hasattr(item, 'GetModel') or item.GetModel() is None:
            return
        self._WaitForTech3Model(item)
        if self.dungeonHack.IsFreeLook():
            vec = item.GetVectorAt(blue.os.GetSimTime())
            self.GetCameraParent().translation = (vec.x, vec.y, vec.z)
            return
        if itemID == session.shipid:
            self._LookingAtSelf()
        elif self._IsLookingAtOtherOK(item):
            self._LookingAtOther()
        else:
            return
        camera = self.GetSpaceCamera()
        cameraParent = self.GetCameraParent()
        if camera is None or cameraParent is None:
            return
        self.GetCameraInterest().translationCurve = None
        sm.StartService('state').SetState(itemID, state.lookingAt, 1)
        self.lookingAt = itemID
        cache = itemID == session.shipid
        item.LookAtMe()
        sm.ScatterEvent('OnLookAt', itemID)
        trackableItem = self._GetTrackableCurve(itemID)
        if not smooth:
            self.animationController.Schedule(camutils.SetTranslationCurve(trackableItem))
            self.animationController.Schedule(camutils.LookAt_Pan(setZ, 0.0, cache=cache))
        else:
            self._DoAnimatedLookAt(item, setZ, resetCamera, trackableItem, cache=cache)

    def _DoAnimatedLookAt(self, item, setZ = None, resetCamera = False, trackableItem = None, cache = False):
        if item.model.__bluetype__ not in evespacescene.EVESPACE_TRINITY_CLASSES:
            self.animationController.Schedule(camutils.SetTranslationCurve(trackableItem))
            return
        tracker = trinity.EveSO2ModelCenterPos()
        tracker.parent = item.model
        self.animationController.Schedule(camutils.LookAt_Translation(tracker))
        self.animationController.Schedule(camutils.LookAt_FOV(resetCamera))
        self.animationController.Schedule(camutils.LookAt_Pan(setZ, cache=cache))

    def PanCameraBy(self, percentage, time = 0.0, source = 'default', cache = False):
        """
        Pans camera based on a percentage of current translationFromParent
        """
        camera = self.GetCameraByName(source)
        if camera is None:
            return
        beg = camera.translationFromParent
        end = beg + beg * percentage
        self.PanCamera(beg, end, time, source, cache)

    def PanCamera(self, cambeg = None, camend = None, time = 0.5, source = 'default', cache = False):
        if self.dungeonHack.IsFreeLook():
            return
        cacheTranslation = cache and self.LookingAt() == session.shipid and source == 'default'
        self.animationController.Schedule(camutils.PanCamera(cambeg, camend, time, source, cacheTranslation))

    def TranslateFromParentAccelerated(self, begin, end, durationSec, accelerationPower = 2.0):
        self.animationController.Schedule(camutils.PanCameraAccelerated(begin, end, durationSec, accelerationPower))

    def CacheCameraTranslation(self):
        camera = self.GetSpaceCamera()
        if camera is not None:
            self.cachedCameraTranslation = camera.translationFromParent

    def ClearCameraParent(self, source = 'default'):
        cameraParent = self.cameraParents.get(source, None)
        if cameraParent is None:
            return
        cameraParent.translationCurve = None
        del self.cameraParents[source]

    def GetCameraParent(self, source = 'default'):
        sceneManager = sm.services.get('sceneManager', None)
        if sceneManager is None or sceneManager.state != service.SERVICE_RUNNING:
            return
        camera = sceneManager.GetRegisteredCamera(source)
        if camera is None:
            return
        cameraParent = self.cameraParents.get(source, None)
        if cameraParent is None:
            cameraParent = camtarget.CameraTarget(camera)
            self.cameraParents[source] = cameraParent
        return cameraParent

    def GetCameraInterest(self, source = 'default'):
        cameraInterest = getattr(self, 'cameraInterest_%s' % source, None)
        if cameraInterest is None:
            camera = sm.GetService('sceneManager').GetRegisteredCamera(source)
            cameraInterest = camtarget.CameraTarget(camera, 'interest')
            setattr(self, 'cameraInterest_%s' % source, cameraInterest)
        return cameraInterest

    def ResetCamera(self, *args):
        self.LookAt(session.shipid, resetCamera=True)

    def LookingAt(self):
        return getattr(self, 'lookingAt', session.shipid)

    def GetTranslationFromParentForItem(self, itemID):
        camera = self.GetSpaceCamera()
        if camera is None:
            return
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            return
        ball = ballpark.GetBall(itemID)
        ball, model, ballRadius = ball, getattr(ball, 'model', None), getattr(ball, 'radius', None)
        if model is None:
            return
        rad = None
        if model.__bluetype__ in evespacescene.EVESPACE_TRINITY_CLASSES:
            rad = model.GetBoundingSphereRadius()
            zoomMultiplier = 1.1 * camutils.GetARZoomMultiplier(trinity.GetAspectRatio())
            return (rad + camera.frontClip) * zoomMultiplier + 2
        if len(getattr(model, 'children', [])) > 0:
            rad = ball.model.children[0].GetBoundingSphereRadius()
        if rad is None or rad <= 0.0:
            rad = ballRadius
        camangle = camera.fieldOfView * 0.5
        return max(15.0, rad / sin(camangle) * cos(camangle))

    def CheckTranslationFromParent(self, distance, getMinMax = 0, source = 'default', distanceIsScale = False):
        if source == 'starmap':
            mn, mx = ZOOM_MIN_STARMAP, ZOOM_MAX_STARMAP
        elif source == 'systemmap':
            mn, mx = ZOOM_NEAR_SYSTEMMAP, ZOOM_FAR_SYSTEMMAP
            mx *= camutils.GetARZoomMultiplier(trinity.device.viewport.GetAspectRatio())
        else:
            lookingAt = self.LookingAt() or session.shipid
            if lookingAt not in self.boundingBoxCache:
                mn = self.GetTranslationFromParentForItem(lookingAt)
                if mn is not None:
                    self.boundingBoxCache[lookingAt] = mn
            else:
                mn = self.boundingBoxCache[lookingAt]
            if distanceIsScale:
                distance = mn * distance
            mx = 1000000.0
        retval = max(mn, min(distance, mx))
        if getMinMax:
            return (retval, mn, mx)
        return retval

    def ClearBoundingInfoForID(self, itemID):
        if itemID in self.boundingBoxCache:
            del self.boundingBoxCache[itemID]

    def _ErrorListener(self, *args):

        def _threaded():
            lookat = self.LookingAt()
            ball = sm.GetService('michelle').GetBall(lookat)
            model = getattr(ball, 'model', None)
            if model is None:
                exceptionMessage = 'EveCamera: Lookat model is none. '
                exceptionMessage += str(lookat) + '/' + str(session.shipid)
                raise Exception(exceptionMessage)
            exceptionMessage = 'EveCamera: \n'
            exceptionMessage += 'Lookat: ' + str(lookat) + '/' + str(session.shipid) + '\n'
            exceptionMessage += 'WorldPos: ' + str(model.modelWorldPosition) + '\n'
            exceptionMessage += 'Curves: ' + str(model.translationCurve.GetVectorAt(blue.os.GetSimTime())) + ' / '
            exceptionMessage += str(model.rotationCurve.GetQuaternionAt(blue.os.GetSimTime())) + '\n'
            if hasattr(model.rotationCurve, 'startCurve'):
                startCurve = model.rotationCurve.startCurve
                exceptionMessage += 'Is wasd ball\n'
                exceptionMessage += 'start' + str(startCurve.GetVectorAt(blue.os.GetSimTime())) + ' / '
                exceptionMessage += str(startCurve.GetQuaternionAt(blue.os.GetSimTime())) + '\n'
                endCurve = model.rotationCurve.endCurve
                exceptionMessage += 'end' + str(endCurve.GetVectorAt(blue.os.GetSimTime())) + ' / '
                exceptionMessage += str(endCurve.GetQuaternionAt(blue.os.GetSimTime())) + '\n'
            self.ResetCamera()
            raise Exception(exceptionMessage)

        uthread.new(_threaded)

    def _CreateErrorHandler(self, camera):
        eventHandler = blue.BlueEventToPython()
        eventHandler.handler = self._ErrorListener
        camera.errorHandler = eventHandler

    def GetSpaceCamera(self):
        if self.spaceCamera is None:
            camera = blue.resMan.LoadObject('res:/dx9/scene/camera.red')
            self._CreateErrorHandler(camera)
            camera.noise = gfxsettings.Get(gfxsettings.UI_CAMERA_SHAKE_ENABLED)
            evecamera.ApplyCameraDefaults(camera)
            camera.audio2Listener = audio2.GetListener(0)
            self.spaceCamera = camera
        return self.spaceCamera

    def GetCameraByName(self, name):
        return sm.GetService('sceneManager').GetRegisteredCamera(name)

    def ShakeCamera(self, magnitude, position, key = None):
        camera = self.GetSpaceCamera()
        behavior = camutils.CreateBehaviorFromMagnitudeAndPosition(magnitude, position, camera)
        if behavior is None:
            return
        behavior.key = key
        self.shakeController.DoCameraShake(behavior)

    def OnGraphicSettingsChanged(self, changes):
        if gfxsettings.UI_CAMERA_SHAKE_ENABLED not in changes:
            return
        self.shakeController.Enable(gfxsettings.Get(gfxsettings.UI_CAMERA_SHAKE_ENABLED))
