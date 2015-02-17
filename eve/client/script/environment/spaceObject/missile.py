#Embedded file name: eve/client/script/environment/spaceObject\missile.py
import math
import random
import audio2
import blue
import trinity
import telemetry
import geo2
import uthread
import evegraphics.settings as gfxsettings
import carbon.common.script.util.logUtil as log
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
SECOND = 10000000

class GlobalsGlob(object):
    """
    Interface for all calls to globals on the Missile class. This allows
    us to provide a mock object, to remove client dependencies.
    """

    def GetMissilesEnabled(self):
        """Returns True if missiles are enabled and the scene is being updated frequently."""
        missilesDesired = gfxsettings.Get(gfxsettings.UI_MISSILES_ENABLED)
        if missilesDesired:
            scene = self.GetSceneNonBlocking()
            if scene is None:
                return False
            updateTime = scene.updateTime
            now = blue.os.GetSimTime()
            if now < updateTime:
                return False
            delta = blue.os.TimeDiffInMs(updateTime, now)
            return delta < 2000
        return missilesDesired

    def Get_FileName_OwnerID_SourceShipID_SourceModuleIDList(self, missileID):
        """
        For a given missileID, return a tuple
        (The graphicFile for the missile object, associated with
        the typeID of the slimItem for this missile, slimItem.ownerID,
        slimItem.sourceShipID, slimItem.launchModules).
        
        All but the first value can be mocked out to return 1 or some other
        ID.
        """
        bp = sm.StartService('michelle').GetBallpark()
        slimItem = bp.GetInvItem(missileID)
        fileName = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        ownerID = slimItem.ownerID
        sourceShipID = slimItem.sourceShipID
        sourceAllModulesID = slimItem.launchModules
        if fileName == '':
            log.LogError('missile::LoadModel failed to get red filename for missile typeID ' + str(slimItem.typeID) + ' missileID : ' + str(missileID) + ' sourceShipID: ' + str(sourceShipID))
            return None
        return (fileName,
         ownerID,
         sourceShipID,
         sourceAllModulesID)

    def GetScene(self):
        """Returns the registered default scene."""
        return sm.StartService('sceneManager').GetRegisteredScene('default')

    def GetSceneNonBlocking(self):
        """
        Returns the registered default scene, without blocking if 
        if is still loading. Can return None if scene not yet registered,
        and the scene is potentially not in a valid state for adding
        objects etc.
        """
        return sm.StartService('sceneManager').registeredScenes.get('default', None)

    def GetTargetBall(self, targetId):
        """Returns a destinyball in the current ballpark with a given ID."""
        bp = sm.StartService('michelle').GetBallpark()
        if bp is None:
            return
        targetBall = bp.GetBallById(targetId)
        return targetBall

    def GetTransCurveForBall(self, targetBall):
        """
        Returns the translation curve for a given destinyball, usually
        the ball itself.
        """
        return targetBall

    def SpawnClientBall(self, position):
        """
        Returns a client side destiny ball for the explosion.
        """
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            return
        egopos = bp.GetCurrentEgoPos()
        explosionPosition = (position[0] + egopos[0], position[1] + egopos[1], position[2] + egopos[2])
        return bp.AddClientSideBall(explosionPosition)

    def DestroyClientBall(self, ball):
        """
        Do any neccessary cleanup for the explosion curve(remove from destiny)
        """
        bp = sm.GetService('michelle').GetBallpark()
        if bp is not None:
            bp.RemoveBall(ball.id)

    def GetFallbackDuration(self):
        return 8 * SECOND

    def PrepExplosionModel(self, explosionModel):
        pass

    def GetExplosionOverride(self, missileFilename):
        return None

    def GetTargetId(self, missile):
        return missile.followId

    def ShakeCamera(self, shakeMagnitude, explosionPosition):
        sm.GetService('camera').ShakeCamera(shakeMagnitude, explosionPosition, 'Missile')


_globalsGlob = GlobalsGlob()

def EstimateTimeToTarget(mslPos, targetPos, targetRadius, velocity):
    """
    Returns the number of seconds that it will take an object traveling
    at maxVelocity to start as mslPos to reach targetPos.
    """
    offset = mslPos - targetPos
    collisionTime = (offset.Length() - targetRadius) / velocity
    return collisionTime


def GetTransformedDamageLocator(eveship, locatorInd = -1):
    """Returns ``eveship.GetTransformedDamageLocator(locatorInd)``.
    
    If locatorInd is -1, chooses a random damage locator if any
    damage locators exist.
    """
    loccnt = eveship.GetDamageLocatorCount()
    if loccnt > 0 and locatorInd == -1:
        locatorInd = random.randint(0, loccnt - 1)
    return eveship.GetTransformedDamageLocator(locatorInd)


class Missile(SpaceObject):
    """
    The missile spaceobject itself. Holds to a trinity object of type
    EveMissile, which is in the scene and is the actual graphics.
    
    The client dependencies can all be mocked by providing a ``globalsGlob``
    parameter into init, and overriding protected methods.
    """
    __guid__ = 'spaceObject.Missile'

    def __init__(self):
        SpaceObject.__init__(self)
        self.exploded = False
        self.collided = False
        self.targetId = None
        self.ownerID = None
        self.sourceShipID = None
        self.sourceModuleIDList = []
        self.delayedBall = None
        self.explosionPath = ''
        self.globalsGlob = _globalsGlob
        self.trinUseNonCached = False
        self.warheadsReleased = 0
        self.totalWarheadCount = 0
        self.delayedBall = None
        self.enabled = self.globalsGlob.GetMissilesEnabled()

    def _GetExplosionPath(self, missileFilename, append = ''):
        """
        Returns the corresponding explosion res path for the given
        missile respath, or can be overridden to return an explicit path.
        
        TODO: This stuff needs to be data driven!
        """
        override = self.globalsGlob.GetExplosionOverride(missileFilename)
        if override is not None:
            return override
        result = missileFilename.lower().replace('_missile_', '_impact_')
        result = result.replace('_t1.red', append + '.red')
        return result

    @telemetry.ZONE_METHOD
    def LoadModel(self, fileName = None, loadedModel = None):
        if not self.enabled:
            return
        temp = self.globalsGlob.Get_FileName_OwnerID_SourceShipID_SourceModuleIDList(self.id)
        if temp is None:
            return
        self.missileFileName, self.ownerID, self.sourceShipID, self.sourceModuleIDList = temp
        self.targetId = self.globalsGlob.GetTargetId(self)
        self.model = blue.recycler.RecycleOrLoad(self.missileFileName)
        self.explosionPath = self._GetExplosionPath(self.missileFileName)
        if self.model is None:
            self.LogError('missile::LoadModel failed to load a model ' + str(self.missileFileName))
            return
        curves = self._GetModelTransRotCurves()
        self.model.translationCurve, self.model.rotationCurve = curves
        self.model.name = 'Missile in %s' % self.id
        scene = self.globalsGlob.GetScene()
        scene.objects.append(self.model)

    def _GetModelTransRotCurves(self):
        """Returns a translation curve and rotation curve to use for the
        missile model. Returns self, self to use the destinyball as the
        curves, or can be overridden to return arbitrary curves.
        """
        return (self, self)

    def _GetModelTurret(self, moduleIdx):
        """Returns the turret python object
        """
        if getattr(self, 'sourceModuleIDList', None) is None:
            return
        if len(self.sourceModuleIDList) <= moduleIdx:
            log.LogWarn('moduleIdx: + ' + str(moduleIdx) + ' is too high to index into list!')
            return
        slimItemID = self.sourceModuleIDList[moduleIdx]
        sourceShipBall = self.globalsGlob.GetTargetBall(self.sourceShipID)
        if sourceShipBall is not None:
            if not hasattr(sourceShipBall, 'modules'):
                return
            if sourceShipBall.modules is None:
                return
            if slimItemID in sourceShipBall.modules:
                return sourceShipBall.modules[slimItemID]

    def _GetModelStartTransformAndSpeed(self, muzzleID, moduleIdx):
        """Returns a tuple of the missile model's start transform and the
        starting speed. Does a lot of complex logic that only works in a full
        client environment. Override it to provide a constant transform and speed.
        
        :returns: transform, speed. Use an identity matrix for transform
          to start the missile at the destinyball's origin. Returns None, None
          if the values cannot be calculated (because self.model is None).
        """
        if not self.model:
            self.LogError('Missile::_GetModelStart with no model')
            return (None, None)
        now = blue.os.GetSimTime()
        q = self.model.rotationCurve.GetQuaternionAt(now)
        v = self.model.translationCurve.GetVectorAt(now)
        missileBallWorldTransform = geo2.MatrixAffineTransformation(1.0, (0.0, 0.0, 0.0), (q.x,
         q.y,
         q.z,
         q.w), (v.x, v.y, v.z))
        sourceShipBallWorldTransform = missileBallWorldTransform
        firingPosWorldTransform = missileBallWorldTransform
        sourceShipBallSpeed = (0.0, 0.0, 0.0)
        sourceTurretSet = self._GetModelTurret(moduleIdx)
        sourceShipBall = self.globalsGlob.GetTargetBall(self.sourceShipID)
        if sourceShipBall is not None:
            q = sourceShipBall.GetQuaternionAt(now)
            v = sourceShipBall.GetVectorAt(now)
            sourceShipBallWorldTransform = geo2.MatrixAffineTransformation(1.0, (0.0, 0.0, 0.0), (q.x,
             q.y,
             q.z,
             q.w), (v.x, v.y, v.z))
            s = sourceShipBall.GetVectorDotAt(now)
            sourceShipBallSpeed = (s.x, s.y, s.z)
            if sourceTurretSet is not None and len(sourceTurretSet.turretSets) > 0:
                gfxTS = sourceTurretSet.turretSets[0]
                firingPosWorldTransform = gfxTS.GetFiringBoneWorldTransform(gfxTS.currentCyclingFiresPos + muzzleID)
        invMissileBallWorldTransform = geo2.MatrixInverse(missileBallWorldTransform)
        startTransform = geo2.MatrixMultiply(firingPosWorldTransform, invMissileBallWorldTransform)
        startSpeed = geo2.Vec3TransformNormal(sourceShipBallSpeed, invMissileBallWorldTransform)
        return (startTransform, startSpeed)

    @telemetry.ZONE_METHOD
    def Prepare(self):
        if not self.enabled:
            return
        if self.collided:
            return
        SpaceObject.Prepare(self)
        if self.model is None:
            return
        if getattr(self, 'sourceModuleIDList', None) is None:
            self.sourceModuleIDList = [0]
        moduleCount = len(self.sourceModuleIDList)
        moduleCount = max(moduleCount, 1)
        timeToTarget = self.EstimateTimeToTarget()
        doSpread = True
        if timeToTarget < 1.6:
            self.DoCollision(self.targetId, 0, 0, 0)
            doSpread = False
        timeToTargetCenter = max(0.5, self.EstimateTimeToTarget(toCenter=True))
        if timeToTarget > 0:
            timeToTarget = (timeToTarget + timeToTargetCenter) * 0.5
        else:
            timeToTarget = timeToTargetCenter * 0.5
        if len(self.model.warheads) != 1:
            log.LogError('There must be one and only one warhead per missile in: ' + str(self.model.name))
            return
        warheadPrime = self.model.warheads[0]
        curvePrime = None
        bindingPrime = None
        curveSetPrime = None
        for cs in self.model.curveSets:
            for bindingToPrime in cs.bindings:
                if bindingToPrime.destinationObject == warheadPrime:
                    bindingToPrime.destinationObject = None
                    bindingPrime = bindingToPrime.CopyTo()
                    curveSetPrime = cs
                    curvePrime = bindingToPrime.sourceObject
                    cs.curves.remove(curvePrime)
                    cs.bindings.remove(bindingToPrime)
                    break

        del self.model.warheads[:]
        for moduleIdx in range(0, moduleCount):
            turret = self._GetModelTurret(moduleIdx)
            if turret is not None:
                turret.StartShooting()
            turretSet = None
            if turret is not None:
                if len(turret.turretSets) > 0:
                    turretSet = turret.turretSets[0]
            firingDelay = 0.0
            if turretSet is not None:
                firingDelay = turretSet.randomFiringDelay
            firingEffect = None
            if turretSet is not None:
                firingEffect = turretSet.firingEffect
            syncWarheadsCount = 1
            if turretSet is not None:
                if not turretSet.hasCyclingFiringPos:
                    if turretSet.firingEffect is not None:
                        syncWarheadsCount = turretSet.firingEffect.GetPerMuzzleEffectCount()
            whKey = self.missileFileName + ':warhead'
            for i in range(0, syncWarheadsCount):
                wh = blue.recycler.RecycleOrCopy(whKey, warheadPrime)
                if bindingPrime is not None:
                    bd = bindingPrime.CopyTo()
                    bd.destinationObject = wh
                    curve = curvePrime.CopyTo()
                    bd.sourceObject = curve
                    curveSetPrime.curves.append(curve)
                    curveSetPrime.bindings.append(bd)
                startTransform, startSpeed = self._GetModelStartTransformAndSpeed(i, moduleIdx)
                wh.doSpread = doSpread
                muzzleDelay = getattr(firingEffect, 'firingDelay' + str(i + 1), 0.0)
                wh.PrepareLaunch()
                uthread.new(self._StartWarhead, wh, firingDelay + muzzleDelay, i, moduleIdx)
                wh.id = int(moduleIdx * syncWarheadsCount + i)
                self.model.warheads.append(wh)

            if self.targetId:
                targetBall = self.globalsGlob.GetTargetBall(self.targetId)
                if targetBall is not None:
                    self.model.target = targetBall.model
                    self.model.targetRadius = targetBall.radius
            self.model.explosionCallback = self.ExplosionCallback
            self.model.Start(startSpeed, timeToTarget)
            self.totalWarheadCount = syncWarheadsCount * moduleCount

        self.explosionManager.Preload(self.explosionPath, self.totalWarheadCount)

    @telemetry.ZONE_METHOD
    def RemoveAndClearModel(self, model, scene = None):
        """
        Clears warheads and curve bindings added in Prepare, returning the
        model to its initial state so we can recycle it. Calls the base method
        to do the normal cleanup from the scene.
        """
        if model is None:
            return
        if type(model) == trinity.EveMissile:
            del model.warheads[1:]
            whPrime = model.warheads[0]
            for cs in model.curveSets:
                toKeep = []
                for binding in cs.bindings:
                    if type(binding.destinationObject) != trinity.EveMissileWarhead:
                        toKeep.append(binding)
                    elif binding.destinationObject == whPrime:
                        toKeep.append(binding)

                del cs.bindings[:]
                cs.bindings.extend(toKeep)

        SpaceObject.RemoveAndClearModel(self, model, scene=scene)

    def _StartWarhead(self, warhead, delay, warheadIdx, moduleIdx):
        blue.synchro.SleepSim(1000.0 * delay)
        if self.model is None:
            return
        startTransform, startSpeed = self._GetModelStartTransformAndSpeed(warheadIdx, moduleIdx)
        if startTransform is not None:
            warhead.Launch(startTransform)

    def EstimateTimeToTarget(self, toCenter = False):
        """Estimates the number of seconds until the missile hits its target,
        or 5.0 if there is no target.
        """
        targetBall = self.globalsGlob.GetTargetBall(self.targetId)
        if targetBall is None:
            return 5.0
        now = blue.os.GetSimTime()
        myPos = self.model.translationCurve.GetVectorAt(now)
        targetPos = targetBall.GetVectorAt(now)
        if toCenter:
            targetRadius = 0
        else:
            targetRadius = targetBall.radius
        return EstimateTimeToTarget(myPos, targetPos, targetRadius, self.maxVelocity)

    def DoCollision(self, targetId, fx, fy, fz, fake = False):
        if self.collided:
            return
        self.collided = True
        if self.model is None:
            return
        uthread.new(self._DoCollision)

    def _DoCollision(self):
        if self.model is None:
            return
        if self.model.translationCurve is None:
            self.LogError('Missile::_DoCollision no translation curve')
            return
        pos = self.model.translationCurve.GetVectorAt(blue.os.GetSimTime())
        self.delayedBall = self.globalsGlob.SpawnClientBall((pos.x, pos.y, pos.z))
        self.model.translationCurve = self.delayedBall

    def Expire(self):
        """
        Called when a missile does not reach it's destination. Release and DoFinalCleanup will
        make sure nothing gets left behind in the scene or memory.
        """
        self.exploded = True

    def _GetAudioPath(self, missileFilename):
        """
        Returns the path to the wwise audio command for the given missile.
        """
        missileAudio = missileFilename.split('/')[-1:][0][8:-5]
        missileAudio = 'effects_missile_mexplosion_' + missileAudio.lower() + '_play'
        return missileAudio

    def ExplosionCallback(self, warheadIdx):
        """
        Spawns an explosion for the specified warhead
        """
        uthread.new(self._SpawnExplosion, warheadIdx)

    def _GetExplosionPosition(self, warheadIdx):
        if warheadIdx < len(self.model.warheads):
            warheadPosition = self.model.warheads[warheadIdx].explosionPosition
        else:
            warheadPosition = self.model.worldPosition
        return warheadPosition

    @telemetry.ZONE_METHOD
    def _SpawnExplosion(self, warheadIdx):
        if not self.model:
            self.LogWarn('Missile::_SpawnExplosion no model')
            return
        explosionPosition = self._GetExplosionPosition(warheadIdx)
        self.warheadsReleased += 1
        if self.exploded:
            return
        if self.warheadsReleased == self.totalWarheadCount:
            if self.model:
                self.model.target = None
                self.model.explosionCallback = None
                self.RemoveAndClearModel(self.model, self.globalsGlob.GetScene())
                self.model = None
            if self.delayedBall:
                self.globalsGlob.DestroyClientBall(self.delayedBall)
                self.delayedBall = None
            self.exploded = True
        actualModel = self.explosionManager.GetExplosion(self.explosionPath, preloaded=True, callback=self.CleanupExplosion)
        if actualModel is None:
            self.LogError('missile::LoadModel failed to get explosion ' + str(self.explosionPath))
            self.explosionManager.Cancel(self.explosionPath, 1)
            return
        explosionBall = None
        if self.enabled:
            explosionBall = self.globalsGlob.SpawnClientBall(explosionPosition)
            actualModel.translationCurve = explosionBall
            rndRotation = geo2.QuaternionRotationSetYawPitchRoll(random.random() * 2.0 * math.pi, random.random() * 2.0 * math.pi, random.random() * 2.0 * math.pi)
            actualModel.rotation = rndRotation
            scene = self.globalsGlob.GetScene()
            if scene is not None:
                scene.objects.append(actualModel)
                audio = audio2.AudEmitter('effect_source_%s' % str(id(self)))
                obs = trinity.TriObserverLocal()
                obs.front = (0.0, -1.0, 0.0)
                obs.observer = audio
                del actualModel.observers[:]
                actualModel.observers.append(obs)

                def AudioSetup(*args):
                    for eachSet in actualModel.active.curveSets:
                        for eachCurve in eachSet.curves:
                            if eachCurve.__typename__ == 'TriEventCurve':
                                audio.SendEvent(eachCurve.GetKeyValue(0))
                                break

                loadedEventHandler = blue.BlueEventToPython()
                loadedEventHandler.handler = AudioSetup
                actualModel.loadedCallback = loadedEventHandler
            shakeMagnitude = min(actualModel.boundingSphereRadius, 250)
            shakeMagnitude = max(shakeMagnitude, 50)
            self.globalsGlob.ShakeCamera(shakeMagnitude, explosionPosition)

    @telemetry.ZONE_METHOD
    def CleanupExplosion(self, model):
        if model.translationCurve is not None:
            self.globalsGlob.DestroyClientBall(model.translationCurve)
        self.RemoveAndClearModel(model, self.globalsGlob.GetScene())
        if self.warheadsReleased == self.totalWarheadCount:
            self.ReleaseAll()

    def Explode(self):
        return self.collided

    @telemetry.ZONE_METHOD
    def Release(self, origin = None):
        if not self.collided and self.explodeOnRemove and self.enabled:
            self.Expire()
            self.ReleaseAll()

    def DoFinalCleanup(self):
        SpaceObject.DoFinalCleanup(self)
        self.ReleaseAll()

    def ReleaseAll(self):
        if self.model:
            self.model.target = None
            self.model.explosionCallback = None
            SpaceObject.Release(self, 'Missile')
        if self.delayedBall:
            self.globalsGlob.DestroyClientBall(self.delayedBall)
            self.delayedBall = None
        warheadsLeft = self.totalWarheadCount - self.warheadsReleased
        self.warheadsReleased = self.totalWarheadCount
        if warheadsLeft != 0:
            self.explosionManager.Cancel(self.explosionPath, count=warheadsLeft)

    def Display(self, display = 1, canYield = True):
        if self.enabled:
            SpaceObject.Display(self, display, canYield)


class Bomb(Missile):
    """
    The Bomb spaceobject. Extends Missile with a Release method.
    """

    def Release(self):
        self._SpawnExplosion(0)
        SpaceObject.Release(self, 'Bomb')

    def EstimateTimeToTarget(self, toCenter = False):
        return 20.0

    def _GetExplosionPosition(self, warheadIdx):
        return self.model.worldPosition
