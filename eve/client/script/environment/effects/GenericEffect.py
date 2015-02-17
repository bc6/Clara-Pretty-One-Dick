#Embedded file name: eve/client/script/environment/effects\GenericEffect.py
import blue
import trinity
import audio2
import eve.client.script.environment.spaceObject.ship as ship
from eve.client.script.environment.effects.effectConsts import FX_TF_NONE, FX_TF_SCALE_SYMMETRIC, FX_TF_SCALE_RADIUS, FX_TF_SCALE_BOUNDING, FX_TF_ROTATION_BALL, FX_TF_POSITION_BALL, FX_TF_POSITION_MODEL, FX_TF_POSITION_TARGET
STOP_REASON_DEFAULT = 'STOP_REASON_DEFAULT'
STOP_REASON_BALL_REMOVED = 'STOP_REASON_BALL_REMOVED'

class GenericEffect:
    __guid__ = 'effects.GenericEffect'

    def __init__(self, trigger, transformFlags = [0], mergeFlags = [0], graphicFile = None, scaleTime = True, duration = 10000):
        self.ballIDs = [trigger.shipID, trigger.targetID]
        self.gfx = None
        self.gfxModel = None
        self.graphicFile = graphicFile
        self.transformFlags = transformFlags
        self.mergeFlags = mergeFlags
        self.duration = duration
        self.scaleTime = scaleTime
        self.graphicInfo = trigger.graphicInfo
        self.startTime = trigger.startTime
        self.timeFromStart = trigger.timeFromStart
        self.fxSequencer = sm.GetService('FxSequencer')

    def Prepare(self, addToScene = True):
        pass

    def Start(self, duration):
        pass

    def Stop(self, reason = STOP_REASON_DEFAULT):
        pass

    def Repeat(self, duration):
        pass

    def GetBalls(self):
        return self.ballIDs

    def GetEffectShipID(self):
        return self.ballIDs[0]

    def GetEffectShipBall(self):
        return self.fxSequencer.GetBall(self.GetEffectShipID())

    def GetEffectTargetID(self):
        return self.ballIDs[1]

    def GetEffectTargetBall(self):
        return self.fxSequencer.GetBall(self.GetEffectTargetID())

    def PlayOldAnimations(self, tf):
        curveTypes = ['trinity.TriScalarCurve',
         'trinity.TriVectorCurve',
         'trinity.TriRotationCurve',
         'trinity.TriColorCurve']
        curves = tf.Find(curveTypes)
        now = blue.os.GetSimTime()
        for curve in curves:
            curve.start = now

    def PlayNamedAnimations(self, model, animName):
        """ Activate all the curves on a model for the animations
            This is the Scene 2 version of playOld animations. 
        """
        if not model:
            return
        for each in model.curveSets:
            if each.name == animName:
                each.Play()

    def AddSoundToEffect(self, scaler):
        shipID = self.GetEffectShipID()
        entity = audio2.AudEmitter('effect_' + str(shipID) + '_' + self.__guid__)
        srcRadius = 100.0
        if self.gfx:
            effectBall = self.GetEffectShipBall()
            if effectBall is not None:
                srcRadius = effectBall.radius
        else:
            srcRadius = self.sourceObject.boundingSphereRadius
        attenuation = pow(srcRadius, 0.95) * 33 * scaler
        entity.SetAttenuationScalingFactor(attenuation)
        self.observer = trinity.TriObserverLocal()
        self.observer.observer = entity
        if self.gfx.__bluetype__ in ('trinity.EveTransform', 'trinity.EveStation2'):
            self.gfx.observers.append(self.observer)
        else:
            self.sourceObject.observers.append(self.observer)
        for curve in self.gfx.Find('trinity.TriEventCurve'):
            if curve.name == 'audioEvents':
                curve.eventListener = entity

    def GetEffectEmitter(self):
        """
        Searches the sourceObject for an existing emitter that is an effect as they
        are all scaled with ship size so that we don't need to create new emitter.
        """
        for emitter in self.sourceObject.observers:
            observerName = emitter.observer.name
            if observerName.startswith('effect_'):
                return emitter

    def SetupEffectEmitter(self):
        """
        Checks for an existing emitter, creates on if needed and sets the self.observer property if
        and emitter exists already on the sourceObject
        """
        observer = self.GetEffectEmitter()
        if observer is None:
            self.AddSoundToEffect(scaler=1.0)
        else:
            self.observer = observer

    def SendAudioEvent(self, eventName):
        """
        Sends an event through the Effect emitter if it is present and available.
        """
        triObserver = self.GetEffectEmitter()
        if triObserver is not None:
            triObserver.observer.SendEvent(eventName)

    def AddToScene(self, effect):
        scene = self.fxSequencer.GetScene()
        if scene is not None:
            scene.objects.append(effect)

    def RemoveFromScene(self, effect):
        scene = self.fxSequencer.GetScene()
        if scene is not None:
            scene.objects.fremove(effect)

    def RecycleOrLoad(self, resPath):
        return trinity.Load(resPath)

    def _SpawnClientBall(self, position):
        """
        Returns a client side destiny ball for the explosion.
        """
        bp = self.fxSequencer.GetBallpark()
        if bp is None:
            return
        egopos = bp.GetCurrentEgoPos()
        ballPosition = (position[0] + egopos[0], position[1] + egopos[1], position[2] + egopos[2])
        return bp.AddClientSideBall(ballPosition)

    def _DestroyClientBall(self, ball):
        """
        Do any neccessary cleanup for the explosion curve(remove from destiny)
        """
        bp = self.fxSequencer.GetBallpark()
        if bp is not None:
            bp.RemoveBall(ball.id)


class ShipEffect(GenericEffect):
    __guid__ = 'effects.ShipEffect'

    def Stop(self, reason = STOP_REASON_DEFAULT):
        if self.gfx is None:
            raise RuntimeError('ShipEffect: no effect defined:' + self.__guid__)
        self.RemoveFromScene(self.gfxModel)
        self.gfx = None
        if self.gfxModel:
            self.gfxModel.translationCurve = None
            self.gfxModel.rotationCurve = None
        self.gfxModel = None

    def Prepare(self, addToScene = True):
        shipBall = self.GetEffectShipBall()
        if shipBall is None:
            raise RuntimeError('ShipEffect: no ball found:' + self.__guid__)
        self.gfx = self.RecycleOrLoad(self.graphicFile)
        if self.gfx is None:
            raise RuntimeError('ShipEffect: no effect found:' + self.__guid__)
        self.AddSoundToEffect(2)
        self.gfxModel = trinity.EveRootTransform()
        if shipBall.model.__bluetype__ == 'trinity.EveShip2':
            self.gfxModel.modelRotationCurve = shipBall.model.modelRotationCurve
            self.gfxModel.modelTranslationCurve = shipBall.model.modelTranslationCurve
        self.gfxModel.children.append(self.gfx)
        effectBall = shipBall
        if FX_TF_POSITION_BALL in self.transformFlags:
            self.gfxModel.translationCurve = shipBall
        if FX_TF_POSITION_MODEL in self.transformFlags:
            self.gfxModel.translationCurve = trinity.EveSO2ModelCenterPos()
            self.gfxModel.translationCurve.parent = shipBall.model
        if FX_TF_POSITION_TARGET in self.transformFlags:
            effectBall = self.GetEffectTargetBall()
            self.gfxModel.translationCurve = effectBall
        if FX_TF_SCALE_BOUNDING in self.transformFlags:
            shipBBoxMin, shipBBoxMax = effectBall.model.GetLocalBoundingBox()
            bBox = (max(-shipBBoxMin[0], shipBBoxMax[0]) * 1.2, max(-shipBBoxMin[1], shipBBoxMax[1]) * 1.2, max(-shipBBoxMin[2], shipBBoxMax[2]) * 1.2)
            self.gfxModel.scaling = bBox
        elif FX_TF_SCALE_SYMMETRIC in self.transformFlags:
            radius = effectBall.model.GetBoundingSphereRadius()
            self.gfxModel.scaling = (radius, radius, radius)
            self.gfx.translation = (0, 0, 0)
        elif FX_TF_SCALE_RADIUS in self.transformFlags:
            radius = effectBall.model.GetBoundingSphereRadius()
            self.gfxModel.scaling = (radius, radius, radius)
        if FX_TF_ROTATION_BALL in self.transformFlags:
            self.gfxModel.rotationCurve = effectBall
        self.gfxModel.name = self.__guid__
        if addToScene:
            self.AddToScene(self.gfxModel)

    def Start(self, duration):
        if self.gfx is None:
            raise RuntimeError('ShipEffect: no effect defined:' + self.__guid__)
        curveSets = self.gfx.curveSets
        if len(curveSets) > 0:
            if self.scaleTime:
                length = self.gfx.curveSets[0].GetMaxCurveDuration()
                if length > 0.0:
                    scaleValue = length / (duration / 1000.0)
                    self.gfx.curveSets[0].scale = scaleValue
            curveSets[0].PlayFrom(self.timeFromStart / float(const.SEC))

    def Repeat(self, duration):
        if self.gfx is None:
            return
        if self.gfxModel is not None:
            gfxModelChildren = self.gfxModel.children
            if len(gfxModelChildren):
                curveSets = gfxModelChildren[0].curveSets
                if len(curveSets):
                    curveSets[0].Play()


class ShipRenderEffect(ShipEffect):
    __guid__ = 'effects.ShipRenderEffect'

    def Prepare(self):
        shipBall = self.GetEffectShipBall()
        self.sourceObject = shipBall.model
        path = self.graphicFile
        if hasattr(self.sourceObject, 'shadowEffect'):
            if self.sourceObject.shadowEffect is not None:
                if 'skinned_' in self.sourceObject.shadowEffect.effectFilePath.lower():
                    path = path.replace('.red', '_skinned.red')
        self.gfx = self.RecycleOrLoad(path)
        self.sourceObject.overlayEffects.append(self.gfx)
        self.AddSoundToEffect(1)

    def Start(self, duration):
        if self.gfx is None:
            raise RuntimeError('ShipEffect: no effect defined')
        if self.gfx.curveSet is not None:
            if self.scaleTime:
                length = self.gfx.curveSet.GetMaxCurveDuration()
                if length > 0.0:
                    scaleValue = length / (duration / 1000.0)
                    self.gfx.curveSet.scale = scaleValue
            self.gfx.curveSet.Play()

    def Stop(self, reason = STOP_REASON_DEFAULT):
        if self.gfx in self.sourceObject.overlayEffects:
            self.sourceObject.overlayEffects.remove(self.gfx)
        if self.observer in self.sourceObject.observers:
            self.sourceObject.observers.remove(self.observer)
        self.gfx = None
        self.gfxModel = None
        self.sourceObject = None

    def Repeat(self, duration):
        if self.gfx is None:
            return
        if self.gfx.curveSet:
            self.gfx.curveSet.Play()


def GetBoundingBox(shipBall, scale = 1.0):
    if not isinstance(shipBall, ship.Ship):
        return (shipBall.radius, shipBall.radius, shipBall.radius)
    if hasattr(shipBall, 'GetModel'):
        model = shipBall.GetModel()
    else:
        model = getattr(shipBall, 'model', None)
    if model is None:
        return (shipBall.radius, shipBall.radius, shipBall.radius)
    if hasattr(model, 'GetLocalBoundingBox'):
        shipBBoxMin, shipBBoxMax = model.GetLocalBoundingBox()
        if shipBBoxMin is None or shipBBoxMax is None:
            raise RuntimeError('StretchEffect: invalid LocalBoundingBox')
        else:
            return (scale * max(-shipBBoxMin[0], shipBBoxMax[0]), scale * max(-shipBBoxMin[1], shipBBoxMax[1]), scale * max(-shipBBoxMin[2], shipBBoxMax[2]))
    else:
        raise RuntimeError('StretchEffect: needs GetLocalBoundingBox')


class StretchEffect(GenericEffect):
    __guid__ = 'effects.StretchEffect'

    def Stop(self, reason = STOP_REASON_DEFAULT):
        if self.gfx is None:
            raise RuntimeError('ShipEffect: no effect defined: ' + str(getattr(self, 'graphicFile', 'None')))
        self.RemoveFromScene(self.gfxModel)
        self.gfx.source.parentPositionCurve = None
        self.gfx.source.parentRotationCurve = None
        self.gfx.source.alignPositionCurve = None
        self.gfx.dest.parentPositionCurve = None
        self.gfx.dest.parentRotationCurve = None
        self.gfx.dest.alignPositionCurve = None
        self.gfx = None
        self.gfxModel = None

    def Prepare(self):
        shipBall = self.GetEffectShipBall()
        targetBall = self.GetEffectTargetBall()
        if shipBall is None:
            raise RuntimeError('StretchEffect: no ball found')
        if not getattr(shipBall, 'model', None):
            raise RuntimeError('StretchEffect: no model found')
        if targetBall is None:
            raise RuntimeError('StretchEffect: no target ball found')
        if not getattr(targetBall, 'model', None):
            raise RuntimeError('StretchEffect: no target model found')
        self.gfx = self.RecycleOrLoad(self.graphicFile)
        if self.gfx is None:
            raise RuntimeError('StretchEffect: no effect found: ' + str(getattr(self, 'graphicFile', 'None')))
        self.AddSoundToEffect()
        self.gfxModel = self.gfx
        self.gfx.source = trinity.TriNearestBoundingPoint()
        self.gfx.dest = trinity.TriNearestBoundingPoint()
        self.gfx.source.parentPositionCurve = shipBall
        self.gfx.source.parentRotationCurve = shipBall
        self.gfx.source.alignPositionCurve = targetBall
        self.gfx.dest.parentPositionCurve = targetBall
        self.gfx.dest.parentRotationCurve = targetBall
        self.gfx.dest.alignPositionCurve = shipBall
        sourceScale = GetBoundingBox(shipBall, scale=1.2)
        self.gfx.source.boundingSize = sourceScale
        targetScale = GetBoundingBox(targetBall, scale=1.2)
        self.gfx.dest.boundingSize = targetScale
        self.AddToScene(self.gfxModel)

    def Start(self, duration):
        if self.gfx is None:
            raise RuntimeError('StretchEffect: no effect defined: ' + str(getattr(self, 'graphicFile', 'None')))
        if self.gfx.curveSets is not None and len(self.gfx.curveSets) > 0:
            if self.scaleTime:
                length = self.gfx.curveSets[0].GetMaxCurveDuration()
                if length > 0.0:
                    scaleValue = length / (duration / 1000.0)
                    self.gfx.curveSets[0].scale = scaleValue
            self.gfx.curveSets[0].Play()

    def Repeat(self, duration):
        if self.gfx is None:
            return
        if self.gfx.curveSets is not None and len(self.gfx.curveSets) > 0:
            self.gfx.curveSets[0].Play()

    def AddSoundToEffect(self):
        shipID = self.GetEffectShipID()
        shipBall = self.GetEffectShipBall()
        targetID = self.GetEffectTargetID()
        targetBall = self.GetEffectTargetBall()
        if shipBall is None or targetBall is None:
            return
        srcAudio = audio2.AudEmitter('effect_source_' + str(shipID))
        destAudio = audio2.AudEmitter('effect_dest_' + str(targetID))
        srcRadius = shipBall.radius
        destRadius = targetBall.radius
        srcAttenuation = pow(srcRadius, 0.95) * 33
        destAttenuation = pow(destRadius, 0.95) * 33
        srcAudio.SetAttenuationScalingFactor(srcAttenuation)
        destAudio.SetAttenuationScalingFactor(destAttenuation)
        if self.gfx.sourceObject:
            obs = trinity.TriObserverLocal()
            obs.front = (0.0, -1.0, 0.0)
            obs.observer = srcAudio
            self.gfx.sourceObject.observers.append(obs)
        if self.gfx.destObject:
            obs = trinity.TriObserverLocal()
            obs.front = (0.0, -1.0, 0.0)
            obs.observer = destAudio
            self.gfx.destObject.observers.append(obs)
        for eachSet in self.gfx.curveSets:
            for eachCurve in eachSet.curves:
                if eachCurve.__typename__ == 'TriEventCurve':
                    if eachCurve.name == 'audioEventsSource':
                        eachCurve.eventListener = srcAudio
                    elif eachCurve.name == 'audioEventsDest':
                        eachCurve.eventListener = destAudio
