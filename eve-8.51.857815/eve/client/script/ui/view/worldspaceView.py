#Embedded file name: eve/client/script/ui/view\worldspaceView.py
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
import worldspaceCustomization
import carbonui.const as uiconst
from yamlext.blueutil import ReadYamlFile
BACKGROUND_COLOR = (0, 0, 0, 0.6)

class WorldspaceView(viewstate.StationView):
    """
    View for activating everything related to CQs
    """
    __guid__ = 'viewstate.WorldspaceView'
    __dependencies__ = viewstate.StationView.__dependencies__[:]
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

    def LoadView(self, change = None, **kwargs):
        """
        Called when the view is loaded
        """
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
        self.loading.ProgressWnd()
        self.loadingBackground.Hide()
        self.loadingBackground.Flush()

    def ShowView(self, **kwargs):
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

    def LoadHangarBackground(self):
        stationTypeID = eve.stationItem.stationTypeID
        stationType = cfg.invtypes.Get(stationTypeID)
        stationRace = stationType['raceID']
        if stationRace == const.raceAmarr:
            scenePath = 'res:/dx9/model/hangar/amarr/ah1/ah1_fis.red'
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementAmarr.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/amarrbalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        elif stationRace == const.raceCaldari:
            scenePath = 'res:/dx9/model/hangar/caldari/ch1/ch1_fis.red'
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementCaldari.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/caldaribalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        elif stationRace == const.raceGallente:
            scenePath = 'res:/dx9/model/hangar/gallente/gh1/gh1_fis.red'
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementGallente.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/gallentebalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        elif stationRace == const.raceMinmatar:
            scenePath = 'res:/dx9/model/hangar/minmatar/mh1/mh1_fis.red'
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementMinmatar.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/minmatarbalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        else:
            scenePath = 'res:/dx9/model/hangar/gallente/gh1/gh1_fis.red'
            shipPositionData = ReadYamlFile('res:/dx9/scene/hangar/shipPlacementGallente.yaml')
            positioning = ReadYamlFile('res:/dx9/scene/hangar/gallentebalconyplacement.yaml')
            self.sceneTranslation = positioning['position']
            self.sceneRotation = geo2.QuaternionRotationSetYawPitchRoll(positioning['orientation'], 0.0, 0.0)
        self.hangarScene = blue.resMan.LoadObject(scenePath)
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
                    modelPath = cfg.invtypes.Get(self.activeShipItem.typeID).GraphicFile()
                    newFilename = modelPath.lower().replace(':/model', ':/dx9/model')
                    newFilename = newFilename.replace('.blue', '.red')
                    newModel = trinity.Load(newFilename)
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
            if hasattr(newModel, 'ChainAnimationEx'):
                newModel.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
            self.activeShip = self.activeShipItem.itemID
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
        if localBB[0] is None or localBB[1] is None:
            log.LogError("Failed to get bounding info for ship. Odds are the ship wasn't loaded properly.")
            localBB = (trinity.TriVector(0, 0, 0), trinity.TriVector(0, 0, 0))
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
        if y < -localBB[0].y + 180:
            y = -localBB[0].y + 180
        boundingBoxZCenter = localBB[0].z + localBB[1].z
        boundingBoxZCenter *= 0.5
        shipPos = geo2.Vec3Scale(shipDirection, -distancePosition[0])
        shipPos = geo2.Vec3Add(shipPos, self.sceneTranslation)
        shipPosition = (shipPos[0], y, shipPos[2])
        model.translationCurve = trinity.TriVectorCurve()
        model.translationCurve.value.x = shipPosition[0]
        model.translationCurve.value.y = shipPosition[1]
        model.translationCurve.value.z = shipPosition[2]
        model.rotationCurve = trinity.TriRotationCurve()
        model.rotationCurve.value.YawPitchRoll(self.shipPositionRotation * math.pi / 180, 0, 0)
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
        yValues = [(0, model.translationCurve.value.y - 20.0), (6.0, model.translationCurve.value.y + 3.0), (9.0, model.translationCurve.value.y)]
        for time, yValue in yValues:
            k = trinity.TriVectorKey()
            k.value = trinity.TriVector(model.translationCurve.value.x, yValue, model.translationCurve.value.z)
            k.interpolation = trinity.TRIINT_HERMITE
            k.time = time
            model.translationCurve.keys.append(k)

        model.translationCurve.Sort()
        model.translationCurve.extrapolation = trinity.TRIEXT_CONSTANT
        model.translationCurve.start = blue.os.GetWallclockTimeNow()
