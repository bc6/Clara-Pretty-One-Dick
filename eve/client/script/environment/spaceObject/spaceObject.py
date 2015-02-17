#Embedded file name: eve/client/script/environment/spaceObject\spaceObject.py
import random
import math
import types
import blue
import geo2
import trinity
import decometaclass
import carbon.common.script.util.mathCommon as mathCommon
import carbon.client.script.util.timecurves as timecurves
from carbon.common.lib.builtinmangler import strx
import uthread2
import logging
import locks
import evegraphics.utils as gfxutils
import evegraphics.settings as gfxsettings
import eveSpaceObject
import eveSpaceObject.spaceobjaudio as spaceobjaudio
import eveSpaceObject.spaceobjanimation as spaceobjanimation
import eve.common.lib.appConst as const
from eve.client.script.environment.spaceObject.ExplosionManager import ExplosionManager
BOOSTER_GFX_SND_RESPATHS = {eveSpaceObject.gfxRaceAmarr: ('res:/dx9/model/ship/booster/booster_amarr.red', 'ship_booster_amarr'),
 eveSpaceObject.gfxRaceCaldari: ('res:/dx9/model/ship/booster/booster_caldari.red', 'ship_booster_caldari'),
 eveSpaceObject.gfxRaceGallente: ('res:/dx9/model/ship/booster/booster_gallente.red', 'ship_booster_gallente'),
 eveSpaceObject.gfxRaceMinmatar: ('res:/dx9/model/ship/booster/booster_minmatar.red', 'ship_booster_minmatar'),
 eveSpaceObject.gfxRaceJove: ('res:/dx9/model/ship/booster/booster_jove.red', 'ship_booster_jove'),
 eveSpaceObject.gfxRaceAngel: ('res:/dx9/model/ship/booster/booster_angel.red', 'ship_booster_angel'),
 eveSpaceObject.gfxRaceSleeper: ('res:/dx9/model/ship/booster/booster_sleeper.red', 'ship_booster_sleeper'),
 eveSpaceObject.gfxRaceORE: ('res:/dx9/model/ship/booster/booster_ORE.red', 'ship_booster_ORE'),
 eveSpaceObject.gfxRaceConcord: ('res:/dx9/model/ship/booster/booster_concord.red', 'ship_booster_concord'),
 eveSpaceObject.gfxRaceRogue: ('res:/dx9/model/ship/booster/booster_rogue.red', 'ship_booster_roguedrone'),
 eveSpaceObject.gfxRaceSansha: ('res:/dx9/model/ship/booster/booster_sansha.red', 'ship_booster_sansha'),
 eveSpaceObject.gfxRaceSOCT: ('res:/dx9/model/ship/booster/booster_soct.red', 'ship_booster_soct'),
 eveSpaceObject.gfxRaceTalocan: ('res:/dx9/model/ship/booster/booster_talocan.red', 'ship_booster_talocan'),
 eveSpaceObject.gfxRaceGeneric: ('res:/dx9/model/ship/booster/booster_generic.red', 'ship_booster_generic'),
 eveSpaceObject.gfxRaceSoE: ('res:/dx9/model/ship/booster/booster_soe.red', 'ship_booster_soe')}

class SpaceObject(decometaclass.WrapBlueClass('destiny.ClientBall')):
    __persistdeco__ = 0
    __update_on_reload__ = 1

    def __init__(self):
        self.explodeOnRemove = False
        self.exploded = False
        self.model = None
        self.animationSequencer = None
        self.released = False
        self.wreckID = None
        self._audioEntities = []
        self._audioEntity = None
        self.logger = logging.getLogger('spaceObject.' + self.__class__.__name__)
        self.modelLoadedEvent = locks.Event()
        self.explosionModel = None
        self.typeID = None
        self.typeData = {}
        self.explosionManager = ExplosionManager()

    def Log(self, level, *args):
        try:
            self.logger.log(level, ' '.join(map(strx, args)))
        except TypeError:
            self.logger.log('[X]'.join(map(strx, args)).replace('\x00', '\\0'))

    def LogInfo(self, *args):
        self.Log(logging.DEBUG, '[', self.id, ']', *args)

    def LogWarn(self, *args):
        self.Log(logging.WARN, '[', self.id, ']', *args)

    def LogError(self, *args):
        self.Log(logging.ERROR, '[', self.id, ']', *args)

    def SetServices(self, spaceMgr, serviceMgr):
        self.spaceMgr = spaceMgr
        self.sm = serviceMgr
        self.spaceObjectFactory = serviceMgr.GetService('sofService').spaceObjectFactory

    def Prepare(self):
        self.typeID = self.typeData.get('typeID', None)
        self.LoadModel()
        self.Assemble()

    def HasBlueInterface(self, obj, interfaceName):
        if hasattr(obj, 'TypeInfo'):
            return interfaceName in obj.TypeInfo()[1]
        return False

    def _GetComponentRegistry(self):
        return self.ballpark.componentRegistry

    def TriggerAnimation(self, state):
        if self.animationSequencer is None:
            return
        self.animationSequencer.GoToState(state)

    def GetCurrentAnimationState(self, stateMachineName):
        if self.animationSequencer is None:
            return
        for stateMachine in self.animationSequencer.stateMachines:
            if stateMachine.name == stateMachineName:
                if stateMachine.currentState is None:
                    return
                else:
                    return stateMachine.currentState.name

    def GetModel(self):
        if not self.model:
            self.modelLoadedEvent.wait()
        return self.model

    def _LoadModelResource(self, fileName):
        self.LogInfo('LoadModel', fileName)
        model = None
        sofDNA = gfxutils.BuildSOFDNAFromTypeID(self.typeData['typeID'])
        if sofDNA is not None:
            model = self.spaceObjectFactory.BuildFromDNA(sofDNA)
        elif fileName is not None and len(fileName):
            model = blue.resMan.LoadObject(fileName)
        if model is None:
            self.LogError('Error: Object type %s has invalid graphicFile, using graphicID: %s' % (self.typeData['typeID'], self.typeData['graphicID']))
        return model

    def LoadModel(self, fileName = None, loadedModel = None):
        if loadedModel:
            model = loadedModel
        else:
            if fileName is None:
                fileName = self.typeData.get('graphicFile')
            model = self._LoadModelResource(fileName)
        if self.released:
            return
        if not model:
            self.LogError('Could not load model for spaceobject. FileName:', fileName, ' id:', self.id, ' typeID:', getattr(self, 'typeID', '?'))
            return
        self.model = model
        if not hasattr(model, 'translationCurve'):
            self.LogError('LoadModel - Model in', fileName, "doesn't have a translationCurve.")
        elif isinstance(self, blue.BlueWrapper):
            model.translationCurve = self
            model.rotationCurve = self
        model.name = '%d' % self.id
        if hasattr(model, 'useCurves'):
            model.useCurves = 1
        if self.model is not None and self.HasBlueInterface(self.model, 'IEveSpaceObject2'):
            scene = self.spaceMgr.GetScene()
            if scene is not None:
                scene.objects.append(self.model)
        else:
            raise RuntimeError('Invalid object loaded by spaceObject: %s' % str(self.model))
        self._SetupAnimationStateMachines()
        self.sm.GetService('FxSequencer').NotifyModelLoaded(self.id)
        self.modelLoadedEvent.set()
        self._SetupAnimationUpdater()

    def _SetupAnimationStateMachines(self):
        animationStates = self.typeData['animationStates']
        if len(animationStates) == 0:
            return
        spaceobjanimation.LoadAnimationStates(animationStates, cfg.graphicStates, self.model, trinity)
        if self.model is not None:
            self.animationSequencer = self.model.animationSequencer

    def _SetupAnimationUpdater(self):
        if not hasattr(self.model, 'animationUpdater'):
            return
        if self._audioEntity is None:
            self._audioEntity = self._GetGeneralAudioEntity()
        if self.model is not None and self.model.animationUpdater is not None:
            self.model.animationUpdater.eventListener = self._audioEntity

    def Assemble(self):
        pass

    def SetStaticRotation(self):
        if self.model is None:
            return
        self.model.rotationCurve = None
        rot = self.typeData.get('dunRotation', None)
        if rot:
            yaw, pitch, roll = map(math.radians, rot)
            quat = geo2.QuaternionRotationSetYawPitchRoll(yaw, pitch, roll)
            if hasattr(self.model, 'rotation'):
                if type(self.model.rotation) == types.TupleType:
                    self.model.rotation = quat
                else:
                    self.model.rotation.SetYawPitchRoll(yaw, pitch, roll)
            else:
                self.model.rotationCurve = trinity.TriRotationCurve()
                self.model.rotationCurve.value = quat

    def _FindClosestBallDir(self, constgrp):
        bp = self.sm.StartService('michelle').GetBallpark()
        dist = 1e+100
        closestID = None
        for ballID, slimItem in bp.slimItems.iteritems():
            if slimItem.groupID == constgrp:
                test = bp.DistanceBetween(self.id, ballID)
                if test < dist:
                    dist = test
                    closestID = ballID

        if closestID is None:
            return (1.0, 0.0, 0.0)
        ball = bp.GetBall(closestID)
        direction = geo2.Vec3SubtractD((self.x, self.y, self.z), (ball.x, ball.y, ball.z))
        return direction

    def FindClosestMoonDir(self):
        return self._FindClosestBallDir(const.groupMoon)

    def FindClosestPlanetDir(self):
        """Locates the closet planet within reason and returns a direction to it"""
        return self._FindClosestBallDir(const.groupPlanet)

    def GetStaticDirection(self):
        """
            Override this method to define where an orbital object should
            align itself.
        
            I have ported the old ugly block of logic here to avoid having
            to perform trivial changes to a bunch of other objects.
        """
        return self.typeData.get('dunDirection', None)

    def SetStaticDirection(self):
        if self.model is None:
            return
        self.model.rotationCurve = None
        direction = self.GetStaticDirection()
        if direction is None:
            self.LogError('Space object', self.id, 'has no static direction defined - no rotation will be applied')
            return
        self.AlignToDirection(direction)

    def AlignToDirection(self, direction):
        """Align the space object to a direction."""
        if not self.model:
            return
        zaxis = direction
        if geo2.Vec3LengthSqD(zaxis) > 0.0:
            zaxis = geo2.Vec3NormalizeD(zaxis)
            xaxis = geo2.Vec3CrossD(zaxis, (0, 1, 0))
            if geo2.Vec3LengthSqD(xaxis) == 0.0:
                zaxis = geo2.Vec3AddD(zaxis, mathCommon.RandomVector(0.0001))
                zaxis = geo2.Vec3NormalizeD(zaxis)
                xaxis = geo2.Vec3CrossD(zaxis, (0, 1, 0))
            xaxis = geo2.Vec3NormalizeD(xaxis)
            yaxis = geo2.Vec3CrossD(xaxis, zaxis)
        else:
            self.LogError('Space object', self.id, 'has invalid direction (', direction, '). Unable to rotate it.')
            return
        mat = ((xaxis[0],
          xaxis[1],
          xaxis[2],
          0.0),
         (yaxis[0],
          yaxis[1],
          yaxis[2],
          0.0),
         (-zaxis[0],
          -zaxis[1],
          -zaxis[2],
          0.0),
         (0.0, 0.0, 0.0, 1.0))
        quat = geo2.QuaternionRotationMatrix(mat)
        if hasattr(self.model, 'modelRotationCurve'):
            if not self.model.modelRotationCurve:
                self.model.modelRotationCurve = trinity.TriRotationCurve(0.0, 0.0, 0.0, 1.0)
            self.model.modelRotationCurve.value = quat
        else:
            self.model.rotationCurve = None

    def UnSync(self):
        if self.model is None:
            return
        startTime = long(random.random() * 123456.0 * 1234.0)
        scaling = 0.95 + random.random() * 0.1
        curves = timecurves.ReadCurves(self.model)
        timecurves.ResetTimeCurves(curves, startTime, scaling)

    def Display(self, display = 1, canYield = True):
        if self.model is None:
            self.LogWarn('Display - No model')
            return
        if canYield:
            blue.synchro.Yield()
        if eve.session.shipid == self.id and display and self.IsCloaked():
            self.sm.StartService('FxSequencer').OnSpecialFX(self.id, None, None, None, None, 'effects.CloakNoAmim', 0, 1, 0, 5, 0)
            return
        if self.model:
            self.model.display = display

    def IsCloaked(self):
        return self.isCloaked

    def OnDamageState(self, damageState):
        pass

    def GetDamageState(self):
        return self.spaceMgr.ballpark.GetDamageState(self.id)

    def DoFinalCleanup(self):
        """
        This is our last chance to clean up anything from this ball, called from Destiny
        as it removes it from the ballpark
        """
        if not self.sm.IsServiceRunning('FxSequencer'):
            return
        self.sm.GetService('FxSequencer').RemoveAllBallActivations(self.id)
        self.ClearExplosion()
        if not self.released:
            self.explodeOnRemove = False
            self.Release()

    def ClearExplosion(self, model = None):
        """
        Called by the explosion manager in case there are special references
        in the explosion that need cleaning up.
        """
        if hasattr(self, 'gfx') and self.gfx is not None:
            self.RemoveAndClearModel(self.gfx)
            self.gfx = None
        if self.explosionModel is not None:
            if getattr(self, 'explosionDisplayBinding', False):
                self.explosionDisplayBinding.destinationObject = None
                self.explosionDisplayBinding = None
            self.RemoveAndClearModel(self.explosionModel)
            self.explosionModel = None

    def Release(self, origin = None):
        uthread2.StartTasklet(self._Release, origin)

    def _Release(self, origin = None):
        self.LogInfo('Release')
        if self.released:
            return
        self.released = True
        if self.explodeOnRemove:
            delay = self.Explode()
            if delay:
                delay = min(delay, 5000)
                blue.synchro.SleepSim(delay)
        self.Display(display=0, canYield=False)
        scene = self.spaceMgr.GetScene()
        uthread2.StartTasklet(self.RemoveAndClearModel, self.model, scene)
        if self.animationSequencer is not None:
            self.model.animationSequencer = None
            self.animationSequencer = None
        self._audioEntities = []
        self._audioEntity = None
        self.model = None

    def RemoveAndClearModel(self, model, scene = None):
        """Remove the model from the scene and clear the transforms on it.
        
        :param model: The trinity model to clear.
        :param scene: The scene to remove the object from.
          If None, use the sceneManager to get the registered 
          default scene.
        """
        if model:
            self._Clearcurves(model)
        else:
            self.released = True
            return
        self.RemoveFromScene(model, scene)

    def _Clearcurves(self, model):
        """Clean up any references to the translation and rotation curves.
        
        :param model: The trinity model to clear.
        :param scene: The scene to remove the object from.
          If None, use the sceneManager to get the registered 
          default scene.
        """
        if hasattr(model, 'translationCurve'):
            model.translationCurve = None
            model.rotationCurve = None
        if hasattr(model, 'observers'):
            for ob in model.observers:
                ob.observer = None

    def RemoveFromScene(self, model, scene):
        """Remove the model from the objects list of the scene.
        
        :param model: The trinity model to clear.
        :param scene: The scene to remove the object from.
          If None, use the sceneManager to get the registered 
          default scene.
        """
        if scene is None:
            scene = self.spaceMgr.GetScene()
        if scene:
            scene.objects.fremove(model)

    def GetExplosionInfo(self):
        """
        This method builds an explosion path using the race.
        """
        raceName = self.typeData.get('sofRaceName', None)
        return eveSpaceObject.GetDeathExplosionInfo(self.model, self.radius, raceName)

    def Explode(self, explosionURL = None, scaling = 1.0, managed = False, delay = 0.0):
        """
        Makes the spaceobject explode.
        Arguments:
            explosionURL is the path to the explosion asset
            scaling controls additionsl scaling of the explosion asset
            managed determines whether to use the explosionManager to manage the explosion
            delay is the delay with which to hide the exploding spaceobject during the explosion
        """
        self.LogInfo('Exploding')
        if self.exploded:
            return False
        self.sm.ScatterEvent('OnObjectExplode', self.GetModel())
        self.exploded = True
        delayedRemove = delay
        self.explodedTime = blue.os.GetTime()
        if gfxsettings.Get(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED):
            if managed:
                gfx = self.explosionManager.GetExplosion(explosionURL, callback=self.ClearExplosion)
            else:
                if explosionURL is None:
                    self.LogError('explosionURL not set when calling Explode. Possibly wrongly authored content. typeID:', self.typeID)
                    explosionURL, (delay, scaling) = self.GetExplosionInfo()
                explosionURL = explosionURL.replace('.blue', '.red').replace('/Effect/', '/Effect3/')
                gfx = trinity.Load(explosionURL)
                if not gfx:
                    self.LogError('Failed to load explosion: ', explosionURL, ' - using default')
                    gfx = trinity.Load('res:/Model/Effect3/Explosion/entityExplode_large.red')
                if gfx.__bluetype__ == 'trinity.EveEffectRoot':
                    msg = 'ExplosionManager circumvented, explosion not managed for %s. (Class:%s, Type:%s)'
                    self.LogWarn(msg % (explosionURL, self.__class__.__name__, self.typeID))
                    gfx.Start()
                elif gfx.__bluetype__ != 'trinity.EveRootTransform':
                    root = trinity.EveRootTransform()
                    root.children.append(gfx)
                    root.name = explosionURL
                    gfx = root
            gfx.translationCurve = self
            self.explosionModel = gfx
            scale = scaling
            gfx.scaling = (gfx.scaling[0] * scale, gfx.scaling[1] * scale, gfx.scaling[2] * scale)
            scene = self.spaceMgr.GetScene()
            scene.objects.append(gfx)
        if self.wreckID is not None:
            wreckBall = self.sm.StartService('michelle').GetBall(self.wreckID)
            if wreckBall is not None:
                uthread2.StartTasklet(wreckBall.DisplayWreck, delayedRemove)
        return delayedRemove

    def GetEventNameFromSlimItem(self, defaultSoundUrl):
        slimItem = self.typeData.get('slimItem')
        eventName = spaceobjaudio.GetSoundUrl(slimItem, defaultSoundUrl)
        return eventName

    def SetupAmbientAudio(self, defaultSoundUrl = None):
        """
            Prepares any ambient audio effects authored on the graphics data.
        """
        audioUrl = self.GetEventNameFromSlimItem(defaultSoundUrl)
        if audioUrl is None:
            return
        audentity = self._GetGeneralAudioEntity()
        if audentity is not None:
            spaceobjaudio.PlayAmbientAudio(audentity, audioUrl)

    def SetupSharedAmbientAudio(self, defaultSoundUrl = None):
        """
            Prepares shared ambient audio effects authored on the graphics data.
        :param defaultSoundUrl: An audio event used if nothing is found in FSD
        """
        eventName = self.GetEventNameFromSlimItem(defaultSoundUrl)
        if eventName is None or self.model is None:
            return
        spaceobjaudio.SetupSharedEmitterForAudioEvent(self.model, eventName)

    def LookAtMe(self):
        pass

    def _GetGeneralAudioEntity(self, recreate = False):
        if self.model is None:
            self._audioEntity = None
            self.LogWarn('model is None, cannot play audio.')
        elif recreate or self._audioEntity is None:
            self._audioEntity = spaceobjaudio.SetupAudioEntity(self.model)
            self._audioEntities.append(self._audioEntity)
        return self._audioEntity

    def PlayGeneralAudioEvent(self, eventName):
        audentity = self._GetGeneralAudioEntity()
        if audentity is not None:
            spaceobjaudio.SendEvent(audentity, eventName)

    def GetNamedAudioEmitterFromObservers(self, emitterName):
        if getattr(self, 'model', None) is None:
            return
        for triObserver in self.model.observers:
            if triObserver.observer.name.lower() == emitterName:
                return triObserver.observer
