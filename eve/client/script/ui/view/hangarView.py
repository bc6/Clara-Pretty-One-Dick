#Embedded file name: eve/client/script/ui/view\hangarView.py
"""
Includes the old EVE hangar view.
"""
from eve.client.script.ui.view.stationView import StationView
from inventorycommon.util import IsModularShip
import uiprimitives
import log
import sys
import blue
import telemetry
import util
import uicls
import audio2
import trinity
import uthread
import const
import geo2
import random
import eveHangar.hangar as hangarUtil
import evecamera.utils as camutils
import evegraphics.settings as gfxsettings
import evegraphics.utils as gfxutils
from sceneManager import SCENE_TYPE_SPACE

class StaticEnvironmentResource(object):
    """
    Takes care of recreating static background on device reset.
    """

    def __init__(self, hangarView):
        self.hangarView = hangarView
        self.isResetting = False
        trinity.device.RegisterResource(self)

    def OnInvalidate(self, level):
        pass

    def OnCreate(self, dev):
        if not self.isResetting:
            self.isResetting = True
            uthread.new(self.hangarView.ResetStaticEnvironment)


class HangarView(StationView):
    """
    Classic EVE hangar view where players can spin their ships.
    """
    __guid__ = 'viewstate.HangarView'
    __notifyevents__ = StationView.__notifyevents__[:]
    __notifyevents__.extend(['OnUIScalingChange'])
    __layerClass__ = uicls.HangarLayer

    @telemetry.ZONE_METHOD
    def LoadView(self, change = None, **kwargs):
        """
        Load up the hangar
        """
        self.hangarTraffic = hangarUtil.HangarTraffic()
        self.station.CleanUp()
        self.station.StopAllStationServices()
        self.station.Setup()
        self.staticEnv = not gfxsettings.Get(gfxsettings.MISC_LOAD_STATION_ENV)
        self.staticEnvResource = None
        StationView.LoadView(self, **kwargs)
        self.sceneManager.SetSceneType(SCENE_TYPE_SPACE)
        settings.user.ui.Set('defaultDockingView', 'hangar')
        oldWorldSpaceID = newWorldSpaceID = session.worldspaceid
        if 'worldspaceid' in change:
            oldWorldSpaceID, newWorldSpaceID = change['worldspaceid']
        changes = change.copy()
        if 'stationid' not in changes:
            changes['stationid'] = (None, newWorldSpaceID)
        fromstation, tostation = changes['stationid']
        self.activeShip = None
        self.activeshipmodel = None
        self.maxZoom = 750.0
        self.minZoom = 150.0
        self.lastShipzoomTo = 0.0
        self._SetStationRace()
        stationGraphicsID = hangarUtil.racialHangarScenes[8]
        if self.stationRace in hangarUtil.racialHangarScenes:
            stationGraphicsID = hangarUtil.racialHangarScenes[self.stationRace]
        g = cfg.graphics.GetIfExists(stationGraphicsID)
        if g is not None:
            self.scenePath = g.graphicFile
        self.sceneManager.LoadScene(self.scenePath, registerKey=self.name)
        random.seed()
        self.hangarScene = self.sceneManager.GetRegisteredScene(self.name)
        self.hangarTraffic.SetupScene(self.hangarScene)
        cyear, cmonth, cwd, cday, chour, cmin, csec, cms = util.GetTimeParts(blue.os.GetWallclockTime())
        hourlyChanging = []
        for obj in self.hangarScene.objects:
            for fx in obj.children:
                if fx.name.startswith('sfx_'):
                    fx.display = False
                    hourlyChanging.append(fx)

        if len(hourlyChanging) > 0:
            hourlyTimer = cyear + 1800 * cmonth + 24 * cday + chour
            sfxIdx = hourlyTimer % len(hourlyChanging)
            hourlyChanging[sfxIdx].display = True
        self.layer.camera = self.sceneManager.GetRegisteredCamera(self.name)
        self.layer.camera.SetOrbit(-0.75, -0.5)

    def _SetStationRace(self):
        stationTypeID = eve.stationItem.stationTypeID
        stationType = cfg.invtypes.Get(stationTypeID)
        self.stationRace = stationType['raceID']

    @telemetry.ZONE_METHOD
    def ShowView(self, **kwargs):
        """
        The view is actually being shown.
        """
        StationView.ShowView(self, **kwargs)
        self.sceneManager.SetRegisteredScenes(self.name)
        if util.GetActiveShip():
            self.ShowShip(util.GetActiveShip())
        elif self.staticEnv:
            self.RenderStaticEnvironment()
        else:
            self.RenderDynamicEnvironment()

    @telemetry.ZONE_METHOD
    def HideView(self):
        """
        The view is being hidden
        """
        self.staticEnvResource = None
        self.RemoveFullScreenSprite()
        StationView.HideView(self)

    @telemetry.ZONE_METHOD
    def UnloadView(self):
        """
        Unloads the hangar
        """
        self.layer.camera = None
        objs = []
        for obj in self.hangarScene.objects:
            objs.append(obj)

        for obj in objs:
            self.hangarScene.objects.remove(obj)

        self.hangarTraffic.CleanupScene()
        self.staticEnvResource = None
        self.RemoveFullScreenSprite()
        StationView.UnloadView(self)
        self.sceneManager.UnregisterCamera(self.name)
        self.sceneManager.UnregisterScene(self.name)
        sm.GetService('camera').ClearCameraParent(self.name)
        self.hangarScene = None
        if hasattr(self.activeshipmodel, 'animationSequencer'):
            self.activeshipmodel.animationSequencer = None
        self.activeshipmodel = None

    @telemetry.ZONE_METHOD
    def RenderDynamicEnvironment(self):
        self.hangarScene.enableShadows = False
        for obj in self.hangarScene.objects:
            if hasattr(obj, 'enableShadow'):
                obj.enableShadow = False

        self.SetupCamera()

    @telemetry.ZONE_METHOD
    def SetupCamera(self):
        camera = self.sceneManager.GetRegisteredCamera(self.name)
        for each in camera.zoomCurve.keys:
            each.value = 1.0

        camera.fieldOfView = 1.2
        camera.frontClip = 10.0
        camera.minPitch = -1.4
        camera.maxPitch = 0.0

    @telemetry.ZONE_METHOD
    def ShowActiveShip(self):
        if sm.GetService('viewState').IsCurrentViewSecondary():
            return
        if getattr(self, '__alreadyShowingActiveShip', False):
            return
        setattr(self, '__alreadyShowingActiveShip', True)
        try:
            modelToRemove = None
            if self.hangarScene:
                for each in self.hangarScene.objects:
                    if getattr(each, 'name', None) == str(self.activeShip):
                        modelToRemove = each

            if IsModularShip(self.activeShipItem.typeID):
                try:
                    dogmaItem = self.clientDogmaIM.GetDogmaLocation().dogmaItems.get(self.activeShipItem.itemID, None)
                    if dogmaItem is None:
                        log.LogTraceback('Trying to show t3 ship which is not in dogma')
                        return
                    subSystemIds = {}
                    for fittedItem in dogmaItem.GetFittedItems().itervalues():
                        if fittedItem.categoryID == const.categorySubSystem:
                            subSystemIds[fittedItem.groupID] = fittedItem.typeID

                    newModel = self.t3ShipSvc.GetTech3ShipFromDict(dogmaItem.typeID, subSystemIds)
                except:
                    log.LogException('failed bulding modular ship')
                    sys.exc_clear()
                    return

            else:
                shipDna = gfxutils.BuildSOFDNAFromTypeID(self.activeShipItem.typeID)
                if shipDna is not None:
                    sof = sm.GetService('sofService').spaceObjectFactory
                    newModel = sof.BuildFromDNA(shipDna)
            self.generalAudioEntity = None
            if newModel is not None and hasattr(newModel, 'observers'):
                triObserver = trinity.TriObserverLocal()
                self.generalAudioEntity = audio2.AudEmitter('spaceObject_' + str(self.activeShipItem.itemID) + '_general')
                triObserver.observer = self.generalAudioEntity
                newModel.observers.append(triObserver)
            sm.ScatterEvent('OnActiveShipModelChange', newModel, self.activeShipItem.itemID)
            newModel.FreezeHighDetailMesh()
            zoomTo = self.GetZoomValues(newModel, 0)
            self.activeShip = self.activeShipItem.itemID
            self.SetupAnimation(newModel, self.activeShipItem)
            self.activeshipmodel = newModel
            newModel.name = str(self.activeShipItem.itemID)
            if not self.staticEnv and zoomTo > self.lastShipzoomTo and self.hangarScene is not None and modelToRemove is not None:
                uthread.new(self.DelayedSwap, self.hangarScene, modelToRemove, newModel)
            else:
                newModel.display = 1
                if modelToRemove is not None:
                    self.hangarScene.objects.remove(modelToRemove)
                self.hangarScene.objects.append(newModel)
            self.generalAudioEntity.SendEvent(unicode('hangar_spin_switch_ship_play'))
            self.lastShipzoomTo = zoomTo
            self.Zoom(zoomTo)
            if self.staticEnv:
                self.RenderStaticEnvironment()
            else:
                self.RenderDynamicEnvironment()
        except Exception as e:
            log.LogException(str(e))
            sys.exc_clear()
        finally:
            delattr(self, '__alreadyShowingActiveShip')

    @telemetry.ZONE_METHOD
    def DelayedSwap(self, scene, oldModel, newModel):
        newModel.display = 0
        scene.objects.append(newModel)
        blue.pyos.synchro.SleepWallclock(1000)
        newModel.display = 1
        if oldModel in scene.objects:
            scene.objects.remove(oldModel)
        else:
            log.LogError('Could not remove old ship model ' + str(oldModel) + ' from scene object list! len=' + str(len(scene.objects)))

    @telemetry.ZONE_METHOD
    def AnimateTraffic(self, ship, area, shipClass):
        initialAdvance = random.random()
        while self.trafficActive:
            if shipClass == 'b':
                duration = random.uniform(40.0, 50.0)
            elif shipClass == 'bc':
                duration = random.uniform(20.0, 30.0)
            elif shipClass == 'c':
                duration = random.uniform(15.0, 20.0)
            elif shipClass == 'f':
                duration = random.uniform(10.0, 15.0)
            else:
                duration = random.uniform(15.0, 20.0)
            if ship.translationCurve and ship.rotationCurve and len(ship.translationCurve.keys) == 2:
                now = blue.os.GetSimTime()
                s01 = random.random()
                t01 = random.random()
                if ship.rotationCurve.value[1] < 0.0:
                    startPos = geo2.Vec3BaryCentric(area['Traffic_Start_1'], area['Traffic_Start_2'], area['Traffic_Start_3'], s01, t01)
                    endPos = geo2.Vec3BaryCentric(area['Traffic_End_1'], area['Traffic_End_2'], area['Traffic_End_3'], s01, t01)
                else:
                    startPos = geo2.Vec3BaryCentric(area['Traffic_End_1'], area['Traffic_End_2'], area['Traffic_End_3'], s01, t01)
                    endPos = geo2.Vec3BaryCentric(area['Traffic_Start_1'], area['Traffic_Start_2'], area['Traffic_Start_3'], s01, t01)
                startPos = geo2.Vec3Add(startPos, geo2.Vec3Scale(geo2.Vec3Subtract(endPos, startPos), initialAdvance))
                startKey = ship.translationCurve.keys[0]
                endKey = ship.translationCurve.keys[1]
                startKey.value = startPos
                startKey.time = 0.0
                startKey.interpolation = trinity.TRIINT_LINEAR
                endKey.value = endPos
                endKey.time = duration
                endKey.interpolation = trinity.TRIINT_LINEAR
                ship.translationCurve.extrapolation = trinity.TRIEXT_CONSTANT
                ship.translationCurve.Sort()
                ship.translationCurve.start = now
                ship.display = True
            delay = random.uniform(5.0, 15.0)
            initialAdvance = 0.0
            blue.pyos.synchro.SleepWallclock(1000.0 * (duration + delay))

    @telemetry.ZONE_METHOD
    def StartExitAnimation(self):
        if getattr(self, 'hangarScene', None) is not None:
            if self.hangarScene is not None:
                for curveSet in self.hangarScene.curveSets:
                    if curveSet.name == 'Undock':
                        curveSet.scale = 1.0
                        curveSet.PlayFrom(0.0)
                        break

    @telemetry.ZONE_METHOD
    def StopExitAnimation(self):
        if getattr(self, 'hangarScene', None) is not None:
            for curveSet in self.hangarScene.curveSets:
                if curveSet.name == 'Undock':
                    curveSet.scale = -1.0
                    curveSet.PlayFrom(curveSet.GetMaxCurveDuration())
                    break

    def StartExitAudio(self):
        """
            Get the raceID of the station, set the race state in the music
            system and playthe undock sound.
        
        """
        raceStates = {const.raceAmarr: 'music_switch_race_amarr',
         const.raceCaldari: 'music_switch_race_caldari',
         const.raceGallente: 'music_switch_race_gallente',
         const.raceMinmatar: 'music_switch_race_minmatar'}
        audioService = sm.GetService('audio')
        if not hasattr(self, 'stationRace'):
            self._SetStationRace()
        audioService.SendUIEvent(raceStates.get(self.stationRace, 'music_switch_race_norace'))
        audioService.SendUIEvent('transition_undock_play')

    def StopExitAudio(self):
        sm.GetService('audio').SendUIEvent('transition_undock_cancel')

    @telemetry.ZONE_METHOD
    def CheckScene(self):
        scene = self.sceneManager.GetRegisteredScene(self.name)
        if self.staticEnv:
            self.RenderStaticEnvironment()
            scene.display = False
        else:
            scene.display = True
            self.RemoveFullScreenSprite()

    def RemoveFullScreenSprite(self):
        for each in uicore.uilib.desktop.children:
            if each.name == 'fullScreenSprite':
                uicore.uilib.desktop.children.remove(each)

    def _WaitForFinishedRenderJob(self, rj):
        while rj.status != trinity.RJ_DONE:
            rj.ScheduleOnce()
            rj.WaitForFinish()

    def RenderStaticEnvironment(self):
        alphaFill = trinity.Tr2Effect()
        alphaFill.effectFilePath = 'res:/Graphics/Effect/Utility/Compositing/AlphaFill.fx'
        trinity.WaitForResourceLoads()
        if self.staticEnvResource is None:
            self.staticEnvResource = StaticEnvironmentResource(self)
        if self.hangarScene is None:
            return
        self.hangarScene.display = True
        self.hangarScene.update = True
        depthTexture = self.hangarScene.depthTexture
        distortionTexture = self.hangarScene.distortionTexture
        self.hangarScene.depthTexture = None
        self.hangarScene.distortionTexture = None
        clientWidth = trinity.device.width
        clientHeight = trinity.device.height
        renderTarget = trinity.Tr2RenderTarget(clientWidth, clientHeight, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        depthStencil = trinity.Tr2DepthStencil(clientWidth, clientHeight, trinity.DEPTH_STENCIL_FORMAT.AUTO)
        self.SetupCamera()
        camera = self.sceneManager.GetRegisteredCamera(self.name)
        camera.idleMove = False
        updateJob = trinity.CreateRenderJob('UpdateScene')
        updateJob.SetView(None)
        updateJob.Update(self.hangarScene)
        self._WaitForFinishedRenderJob(updateJob)
        view = trinity.TriView()
        view.SetLookAtPosition(camera.pos, camera.intr, (0.0, 1.0, 0.0))
        projection = trinity.TriProjection()
        fov = camera.fieldOfView
        aspectRatio = float(clientWidth) / clientHeight
        projection.PerspectiveFov(fov, aspectRatio, 1.0, 350000.0)
        renderJob = trinity.CreateRenderJob('StaticScene')
        renderJob.PushRenderTarget(renderTarget)
        renderJob.SetProjection(projection)
        renderJob.SetView(view)
        renderJob.PushDepthStencil(depthStencil)
        renderJob.Clear((0.0, 0.0, 0.0, 0.0), 1.0)
        renderJob.RenderScene(self.hangarScene)
        renderJob.SetStdRndStates(trinity.RM_FULLSCREEN)
        renderJob.RenderEffect(alphaFill)
        renderJob.PopDepthStencil()
        renderJob.PopRenderTarget()
        self._WaitForFinishedRenderJob(renderJob)
        self.hangarScene.display = False
        self.hangarScene.update = False
        try:
            rgbSource = trinity.Tr2HostBitmap(renderTarget)
        except Exception:
            log.LogException()
            sys.exc_clear()
            return

        self.RemoveFullScreenSprite()
        self.sprite = uiprimitives.Sprite(parent=uicore.uilib.desktop, width=uicore.uilib.desktop.width, height=uicore.uilib.desktop.height, left=0, top=0)
        self.sprite.name = 'fullScreenSprite'
        self.sprite.texture.atlasTexture = uicore.uilib.CreateTexture(rgbSource.width, rgbSource.height)
        self.sprite.texture.atlasTexture.CopyFromHostBitmap(rgbSource)
        self.hangarScene.display = False
        self.hangarScene.update = False
        self.hangarScene.depthTexture = depthTexture
        self.hangarScene.distortionTexture = distortionTexture
        self.staticEnvResource.isResetting = False

    def GetZoomValues(self, model, thread):
        rad = 300
        camera = self.sceneManager.GetRegisteredCamera(self.name)
        trinity.WaitForResourceLoads()
        rad = model.GetBoundingSphereRadius()
        center = model.boundingSphereCenter
        localBB = model.GetLocalBoundingBox()
        model.translationCurve = trinity.TriVectorCurve()
        negativeCenter = (-center[0], -localBB[0][1] + hangarUtil.SHIP_FLOATING_HEIGHT, -center[2])
        model.translationCurve.value = negativeCenter
        cameraparent = self.GetCameraParent()
        if cameraparent.translationCurve is not None:
            keyValue = cameraparent.translationCurve.keys[1].value
            if self.staticEnv:
                keyValue = (keyValue[0], negativeCenter[1], keyValue[2])
            cameraparent.translationCurve.keys[0].value = keyValue
            key1Value = cameraparent.translationCurve.keys[1].value
            key1Value = (key1Value[0], negativeCenter[1], key1Value[2])
            cameraparent.translationCurve.keys[1].value = key1Value
            cameraparent.translationCurve.start = blue.os.GetSimTime()
        zoomMultiplier = camutils.GetARZoomMultiplier(trinity.GetAspectRatio())
        self.minZoom = (rad + camera.frontClip + 50) * zoomMultiplier
        self.maxZoom = 2050.0
        self.layer.maxZoom = self.maxZoom
        self.layer.minZoom = self.minZoom
        return (rad + camera.frontClip) * 2

    def GetCameraParent(self):
        cp = sm.GetService('camera').GetCameraParent(self.name)
        if cp.translationCurve is not None:
            return cp
        c = trinity.TriVectorCurve()
        c.extrapolation = trinity.TRIEXT_CONSTANT
        for t in (0.0, 1.0):
            k = trinity.TriVectorKey()
            k.time = t
            k.interpolation = trinity.TRIINT_LINEAR
            c.keys.append(k)

        c.Sort()
        cp.translationCurve = c
        return cp

    def AnimateZoom(self, startVal, endVal, duration):
        camera = self.sceneManager.GetRegisteredCamera(self.name)
        startTime = blue.os.GetWallclockTimeNow()
        for t in range(101):
            elapsed = blue.os.GetWallclockTimeNow() - startTime
            elapsedSec = elapsed / float(const.SEC)
            perc = elapsedSec / duration
            if perc > 1.0:
                camera.translationFromParent = endVal
                break
            camera.translationFromParent = startVal * (1.0 - perc) + endVal * perc
            blue.pyos.synchro.SleepWallclock(1)

        camera.translationFromParent = endVal

    def Zoom(self, zoomto = None):
        camera = self.sceneManager.GetRegisteredCamera(self.name)
        if self.staticEnv:
            camera.translationFromParent = min(self.maxZoom, max(zoomto, self.minZoom))
        else:
            uthread.new(self.AnimateZoom, camera.translationFromParent, min(self.maxZoom, max(zoomto, self.minZoom)), 1.0)

    def ResetStaticEnvironment(self):
        if self.staticEnv:
            self.RenderStaticEnvironment()

    def OnUIScalingChange(self, changes):
        self.ResetStaticEnvironment()
