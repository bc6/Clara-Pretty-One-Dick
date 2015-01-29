#Embedded file name: eve/client/script/ui/view\cqView.py
"""
The view that is active when you are in your CQ
"""
import sys
from inventorycommon.util import IsModularShip
import log
import geo2
import math
import uiprimitives
import util
import blue
import uicls
import audio2
import trinity
import viewstate
import localization
import worldspaceCustomization
import carbonui.const as uiconst
import eveHangar.hangar as hangarUtil
import evegraphics.utils as gfxutils
from eve.client.script.ui.view.stationView import StationView
from yamlext.blueutil import ReadYamlFile
BACKGROUND_COLOR = (0, 0, 0, 0.6)

class CQView(StationView):
    """
    View for activating everything related to CQs
    """
    __guid__ = 'viewstate.CQView'
    __dependencies__ = StationView.__dependencies__[:]
    __dependencies__.extend(['worldSpaceClient',
     'entityClient',
     'cameraClient',
     'entitySpawnClient',
     'clientOnlyPlayerSpawnClient',
     'neocom'])
    __layerClass__ = uicls.CharControl
    __exclusiveOverlay__ = {'stationEntityBrackets'}

    def __init__(self):
        viewstate.StationView.__init__(self)
        self.cachedPlayerPos = None
        self.cachedPlayerRot = None
        self.cachedPlayerYaw = None
        self.cachedPlayerPitch = None
        self.cachedPlayerZoom = None
        self.hangarTraffic = hangarUtil.HangarTraffic()

    def LoadView(self, change = None, **kwargs):
        """
        Called when the view is loaded
        """
        settings.user.ui.Set('defaultDockingView', 'station')
        self.activeShip = None
        self.activeshipmodel = None
        self.hangarScene = None
        self.stationID = None
        self.loadingBackground = uiprimitives.Container(name='loadingBackground', bgColor=util.Color.BLACK, state=uiconst.UI_HIDDEN)
        height = uicore.desktop.height
        width = 1.6 * height
        uiprimitives.Sprite(name='aura', parent=self.loadingBackground, texturePath='res:/UI/Texture/Classes/CQLoadingScreen/IncarnaDisabled.png', align=uiconst.CENTER, width=width, height=height)
        self.loadingBackground.Show()
        self.loadingBackground.opacity = 1.0
        oldWorldSpaceID = newWorldSpaceID = session.worldspaceid
        if 'worldspaceid' in change:
            oldWorldSpaceID, newWorldSpaceID = change['worldspaceid']
        changes = change.copy()
        if 'stationid' not in changes:
            changes['stationid'] = (None, newWorldSpaceID)
        factory = sm.GetService('paperDollClient').dollFactory
        factory.compressTextures = True
        factory.allowTextureCache = True
        clothSimulation = sm.GetService('device').GetAppFeatureState('Interior.clothSimulation', False)
        factory.clothSimulationActive = clothSimulation
        scene = self.entityClient.LoadEntitySceneAndBlock(newWorldSpaceID)
        scene.WaitOnStartupEntities()
        if self.entityClient.IsClientSideOnly(newWorldSpaceID):
            if self.cachedPlayerPos is None or self.cachedPlayerRot is None:
                self.entitySpawnClient.SpawnClientOnlyPlayer(scene, changes)
            else:
                self.clientOnlyPlayerSpawnClient.SpawnClientSidePlayer(scene, self.cachedPlayerPos, self.cachedPlayerRot)
                if self.cachedCameraYaw is not None and self.cachedCameraPitch is not None and self.cachedCameraZoom is not None:
                    self.cameraClient.RegisterCameraStartupInfo(self.cachedCameraYaw, self.cachedCameraPitch, self.cachedCameraZoom)
                self.cachedPlayerPos = None
                self.cachedPlayerRot = None
                self.cachedPlayerYaw = None
                self.cachedPlayerPitch = None
                self.cachedPlayerZoom = None
        if util.IsStation(session.stationid):
            self._GoStation(changes)
        self.loading.ProgressWnd()
        self.loadingBackground.Hide()
        self.loadingBackground.Flush()

    def ShowView(self, **kwargs):
        self.ApplyStationGrime()
        worldspaceCustomization.ApplyWorldspaceCustomization()
        self.cameraClient.Enable()
        if util.GetActiveShip():
            self.ShowShip(util.GetActiveShip())

    def HideView(self):
        self.cameraClient.Disable()

    def UnloadView(self):
        """
        Used for cleaning up after the view has served its purpose
        """
        if self.stationID is not None:
            self.cameraClient.ExitWorldspace()
            self.worldSpaceClient.UnloadWorldSpaceInstance(self.stationID)
            self.entityClient.UnloadEntityScene(self.stationID)
            viewstate.StationView.UnloadView(self)
            self.hangarTraffic.CleanupScene()
        if hasattr(self.activeshipmodel, 'animationSequencer'):
            self.activeshipmodel.animationSequencer = None
        self.activeshipmodel = None
        self.hangarScene = None

    def _GoStation(self, change):
        if 'stationid' in change:
            enteringStationLabel = localization.GetByLabel('UI/Station/EnteringStation')
            clearingCurrentStateLabel = localization.GetByLabel('UI/Station/ClearingCurrentState')
            self.loading.ProgressWnd(enteringStationLabel, '', 1, 5)
            self.loading.ProgressWnd(enteringStationLabel, clearingCurrentStateLabel, 2, 5)
            fromstation, tostation = change['stationid']
            self.loading.ProgressWnd(enteringStationLabel, cfg.evelocations.Get(tostation).name, 3, 5)
            if tostation is not None and fromstation != tostation:
                self.stationID = tostation
                setupStationLabel = localization.GetByLabel('UI/Station/SetupStation', stationName=cfg.evelocations.Get(tostation).name)
                self.loading.ProgressWnd(enteringStationLabel, setupStationLabel, 4, 5)
                self.LoadHangarBackground()
                self.station.CleanUp()
                self.station.StopAllStationServices()
                self.station.Setup()
            elif tostation is None:
                self.station.CleanUp()
            doneLabel = localization.GetByLabel('UI/Common/Done')
            self.loading.ProgressWnd(enteringStationLabel, doneLabel, 5, 5)
        else:
            self.station.CheckSession(change)

    def ApplyStationGrime(self, secStatus = None):
        ranges = {'MaterialDiffuseIntensity': (0.9, 0.4),
         'MaterialGrimeIntensity': (0.9, 0.3)}
        if secStatus is None:
            solarSystem = cfg.mapSystemCache[session.solarsystemid2]
            secStatus = max(0.0, solarSystem.securityStatus)
        valueNames = ranges.keys()
        for parameter in self.hangarScene.Find('trinity.Tr2FloatParameter'):
            for valueName in valueNames:
                if parameter.name == valueName:
                    parameter.value = ranges[valueName][0] * (1.0 - secStatus) + ranges[valueName][1] * secStatus

    def LoadHangarBackground(self):
        stationTypeID = eve.stationItem.stationTypeID
        stationType = cfg.invtypes.Get(stationTypeID)
        stationRace = stationType['raceID']
        stationGraphicsID = hangarUtil.racialHangarScenes[8]
        if stationRace in hangarUtil.racialHangarScenes:
            stationGraphicsID = hangarUtil.racialHangarScenes[stationRace]
        g = cfg.graphics.GetIfExists(stationGraphicsID)
        if g is not None:
            scenePath = g.graphicFile
        if stationRace == const.raceAmarr:
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementAmarr.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/amarrbalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        elif stationRace == const.raceCaldari:
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementCaldari.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/caldaribalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        elif stationRace == const.raceGallente:
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementGallente.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/gallentebalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        elif stationRace == const.raceMinmatar:
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementMinmatar.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/minmatarbalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        else:
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementGallente.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/gallentebalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        self.hangarScene = blue.resMan.LoadObject(scenePath)
        self.hangarTraffic.SetupScene(self.hangarScene)
        self.hangarTraffic.RemoveAudio(self.hangarScene)
        self.sceneManager.SetupIncarnaBackground(self.hangarScene, self.sceneTranslation, self.sceneRotation)
        self.shipPositionMinDistance = shipPositionData['minDistance']
        self.shipPositionMaxDistance = shipPositionData['maxDistance']
        self.shipPositionMaxSize = shipPositionData['shipMaxSize']
        self.shipPositionMinSize = shipPositionData['shipMinSize']
        self.shipPositionTargetHeightMin = shipPositionData['shipTargetHeightMin']
        self.shipPositionTargetHeightMax = shipPositionData['shipTargetHeightMax']
        self.shipPositionCurveRoot = shipPositionData['curveRoot']
        self.shipPositionRotation = shipPositionData['rotation']
        if self.hangarScene is not None:
            stationModel = self.hangarScene.objects[0]
            stationModel.enableShadow = False

    def ShowActiveShip(self):
        if getattr(self, '__alreadyShowingActiveShip', False):
            log.LogTraceback("We're already in the process of showing the active ship")
            return
        self.__alreadyShowingActiveShip = True
        try:
            scene = getattr(self, 'hangarScene', None)
            if scene:
                for each in scene.objects:
                    if getattr(each, 'name', None) == str(self.activeShip):
                        scene.objects.remove(each)

            try:
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
            except Exception as e:
                log.LogException(str(e))
                sys.exc_clear()
                return

            newModel.FreezeHighDetailMesh()
            self.PositionShipModel(newModel)
            self.activeShip = self.activeShipItem.itemID
            self.SetupAnimation(newModel, self.activeShipItem)
            self.activeshipmodel = newModel
            newModel.display = 1
            newModel.name = str(self.activeShipItem.itemID)
            if self.clientDogmaIM.GetDogmaLocation().dogmaItems[util.GetActiveShip()].groupID != const.groupCapsule:
                scene.objects.append(newModel)
                self.generalAudioEntity.SendEvent(unicode('hangar_spin_switch_ship_play'))
            sm.ScatterEvent('OnActiveShipModelChange', newModel, self.activeShipItem.itemID)
        finally:
            self.__alreadyShowingActiveShip = False

    def PositionShipModel(self, model):
        trinity.WaitForResourceLoads()
        localBB = model.GetLocalBoundingBox()
        boundingCenter = model.boundingSphereCenter[1]
        radius = model.boundingSphereRadius - self.shipPositionMinSize
        val = radius / (self.shipPositionMaxSize - self.shipPositionMinSize)
        if val > 1.0:
            val = 1.0
        if val < 0:
            val = 0
        val = pow(val, 1.0 / self.shipPositionCurveRoot)
        shipDirection = (self.sceneTranslation[0], 0, self.sceneTranslation[2])
        shipDirection = geo2.Vec3Normalize(shipDirection)
        distancePosition = geo2.Lerp((self.shipPositionMinDistance, self.shipPositionTargetHeightMin), (self.shipPositionMaxDistance, self.shipPositionTargetHeightMax), val)
        y = distancePosition[1] - boundingCenter
        y = y + self.sceneTranslation[1]
        if y < -localBB[0][1] + 180:
            y = -localBB[0][1] + 180
        boundingBoxZCenter = localBB[0][2] + localBB[1][2]
        boundingBoxZCenter *= 0.5
        shipPos = geo2.Vec3Scale(shipDirection, -distancePosition[0])
        shipPos = geo2.Vec3Add(shipPos, self.sceneTranslation)
        shipPosition = (shipPos[0], y, shipPos[2])
        model.translationCurve = trinity.TriVectorCurve()
        model.translationCurve.value = shipPosition
        model.rotationCurve = trinity.TriRotationCurve()
        model.rotationCurve.value = geo2.QuaternionRotationSetYawPitchRoll(self.shipPositionRotation * math.pi / 180, 0, 0)
        model.modelTranslationCurve = blue.resMan.LoadObject('res:/dx9/scene/hangar/ship_modelTranslationCurve.red')
        model.modelTranslationCurve.ZCurve.offset -= boundingBoxZCenter
        scaleMultiplier = 0.35 + 0.65 * (1 - val)
        capitalShips = [const.groupDreadnought,
         const.groupSupercarrier,
         const.groupTitan,
         const.groupFreighter,
         const.groupJumpFreighter,
         const.groupCarrier,
         const.groupCapitalIndustrialShip,
         const.groupIndustrialCommandShip]
        dogmaLocation = self.clientDogmaIM.GetDogmaLocation()
        if getattr(dogmaLocation.GetDogmaItem(util.GetActiveShip()), 'groupID', None) in capitalShips:
            scaleMultiplier = 0.35 + 0.25 * (1 - val)
            model.modelRotationCurve = blue.resMan.LoadObject('res:/dx9/scene/hangar/ship_modelRotationCurve.red')
            model.modelRotationCurve.PitchCurve.speed *= scaleMultiplier
            model.modelRotationCurve.RollCurve.speed *= scaleMultiplier
            model.modelRotationCurve.YawCurve.speed *= scaleMultiplier
        else:
            if val > 0.6:
                val = 0.6
            scaleMultiplier = 0.35 + 0.65 * (1 - val / 0.6)
            model.modelRotationCurve = blue.resMan.LoadObject('res:/dx9/scene/hangar/ship_modelRotationCurveSpinning.red')
            model.modelRotationCurve.PitchCurve.speed *= scaleMultiplier
            model.modelRotationCurve.RollCurve.speed *= scaleMultiplier
            model.modelRotationCurve.YawCurve.start = blue.os.GetSimTime()
            model.modelRotationCurve.YawCurve.ScaleTime(6 * val + 1)
        yValues = [(0, model.translationCurve.value[1] - 20.0), (6.0, model.translationCurve.value[1] + 3.0), (9.0, model.translationCurve.value[1])]
        for time, yValue in yValues:
            k = trinity.TriVectorKey()
            k.value = (model.translationCurve.value[0], yValue, model.translationCurve.value[2])
            k.interpolation = trinity.TRIINT_HERMITE
            k.time = time
            model.translationCurve.keys.append(k)

        model.translationCurve.Sort()
        model.translationCurve.extrapolation = trinity.TRIEXT_CONSTANT
        model.translationCurve.start = blue.os.GetWallclockTimeNow()
