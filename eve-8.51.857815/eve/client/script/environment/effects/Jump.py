#Embedded file name: eve/client/script/environment/effects\Jump.py
from eve.client.script.environment.effects.GenericEffect import GenericEffect, ShipEffect, STOP_REASON_DEFAULT
import blue
import uthread
import trinity
import geo2
import mathCommon
import random
import infoPanel
import carbonui.const as uiconst
import log
import util
import evecamera.shaker as shaker
import evefisfx.jumptransitioncamera as transitioncam

class JumpTransitionTunnel(object):
    __guid__ = 'effects.JumpTransitionTunnel'

    def __init__(self):
        self.destinationSceneApplied = False
        self.startCamDurationS = 1.0
        self.endCamDurationS = 1.0
        self.camOffsetStart = 1000000
        self.camOffsetEnd = 500000
        self.initToStartDelay = 850
        self.normDir = (0, 0, 1)
        self.effect = None
        self.effectRoot = None
        self.initCS = None
        self.startCS = None
        self.stopCS = None
        self.mainCS = None
        self.shakeDampCurve = None
        self.shakeScaleOut = None
        self.shakeScaleIn = None
        self.randomSoundNumber = 0
        self.cameraLookAnimation = None

    def _FindCurveSets(self, model):
        self.initCS = None
        self.startCS = None
        self.stopCS = None
        self.mainCS = None
        for each in model.curveSets:
            if each.name == 'init':
                self.initCS = each
            elif each.name == 'start':
                self.startCS = each
            elif each.name == 'stop':
                self.stopCS = each
            elif each.name == 'valuePropagation':

                def propValue(*args):
                    source, dest = args
                    dest.value = source.value

                each.bindings[2].copyValueCallable = propValue
            elif each.name == 'main':
                self.mainCS = each

    def SetScene(self, scene):
        self.scene = scene
        scene.warpTunnel = self.effectRoot

    def _ApplyTexturePath(self, effect, name, path):
        for each in effect.resources:
            if each.name == name:
                each.resourcePath = path

    def _CreateCameraShakeCurves(self):
        shakeScaleOut = trinity.TriScalarCurve()
        shakeScaleOut.AddKey(0.0, 0.125, 0.0, 0.0, 2)
        shakeScaleOut.AddKey(0.5, 4.0, 0.0, 0.0, 2)
        shakeScaleOut.AddKey(2.5, 1.0, 0.0, 0.0, 2)
        shakeScaleOut.extrapolation = 1
        shakeScaleIn = trinity.TriScalarCurve()
        shakeScaleIn.AddKey(0.0, 1.0, 0.0, 0.0, 2)
        shakeScaleIn.AddKey(0.4, 2.0, 0.0, 0.0, 2)
        shakeScaleIn.AddKey(0.6, 4.0, 0.0, 0.0, 2)
        shakeScaleIn.AddKey(0.8, 1.0, 0.0, 0.0, 2)
        shakeScaleIn.AddKey(1.1, 0.0, 0.0, 0.0, 2)
        shakeScaleIn.extrapolation = 1
        shakeDampCurve = trinity.TriPerlinCurve()
        shakeDampCurve.offset = 0.07
        shakeDampCurve.scale = 1
        shakeDampCurve.alpha = 0.75
        shakeDampCurve.speed = 4
        shakeDampCurve.N = 4
        self.shakeJumpInit = shaker.ShakeBehavior('JumpInit')
        self.shakeJumpInit.noiseScale = 0.125
        self.shakeJumpInit.dampCurve = shakeDampCurve
        self.shakeJumpOut = shaker.ShakeBehavior('JumpOut')
        self.shakeJumpOut.scaleCurve = shakeScaleOut
        self.shakeJumpOut.dampCurve = shakeDampCurve
        self.shakeJumpIn = shaker.ShakeBehavior('JumpIn')
        self.shakeJumpIn.scaleCurve = shakeScaleIn
        self.shakeJumpIn.dampCurve = shakeDampCurve

    def Prepare(self, shipBall, destSystem):
        self.shipBall = shipBall
        self.ending = False
        self.effectRoot = trinity.EveRootTransform()
        self.effect = blue.resMan.LoadObject('res:/fisfx/jump/jumpgates/tunnel.red')
        self.effectRoot.children.append(self.effect)
        self._FindCurveSets(self.effect)
        sceneManager = sm.GetService('sceneManager')
        self.camera = sceneManager.GetRegisteredCamera('default')
        self.camera.useExtraTranslation = True
        self.camera.extraTranslation = (0, 0, 0)
        transition = sm.GetService('viewState').GetTransitionByName('inflight', 'inflight')
        transition.SetTransitionEffect(self)
        self.transition = transition
        destNebulaPath = sceneManager.GetNebulaPathForSystem(destSystem)
        self._ApplyTexturePath(self.effect.mesh.transparentAreas[0].effect, 'NebulaMap', destNebulaPath)
        self._CreateCameraShakeCurves()

    def Start(self):
        uthread.new(self._DelayedStart)

    def _PlayInitSequence(self):
        self.StartGateEffectAudio()
        blue.synchro.SleepSim(850)
        if self.initCS is not None:
            self.initCS.Play()
            self.StartWarpTransitionAudio()
        blue.synchro.SleepSim(1500)
        sm.GetService('camera').shakeController.DoCameraShake(self.shakeJumpInit)

    def _PlayTunnelSequence(self):
        if self.ending:
            log.LogWarn('Jump Transition: Trying to play tunnel start sequence while ending.')
            return
        normDir = geo2.QuaternionTransformVector(self.effectRoot.rotation, (0, 0, 1))
        self.normDir = normDir
        cameraSvc = sm.GetService('camera')
        cameraSvc.shakeController.DoCameraShake(self.shakeJumpOut)
        if self.initCS is not None:
            self.initCS.Stop()
        if self.startCS is not None:
            self.startCS.Play()
        offset = geo2.Vec3Scale(normDir, self.camOffsetStart)
        cameraSvc.animationController.Schedule(transitioncam.OutExtraTransl(self.startCamDurationS, offset))
        cameraSvc.animationController.Schedule(transitioncam.OutFOV(self.startCamDurationS))
        blue.synchro.SleepSim(500)

    def _PlayMidTransitionCurves(self):
        self.transition.ApplyDestinationScene()
        self.destinationSceneApplied = True
        if self.mainCS is not None:
            self.mainCS.Play()
            self.StopWarpTransitionAudio()

    def _DelayedStart(self):
        with util.ExceptionEater('JumpTransitionTunnelStart'):
            self.DoCameraLookAnimation()
            self._PlayInitSequence()
            blue.synchro.SleepSim(self.initToStartDelay)
            self.FadeUIOut()
            self._PlayTunnelSequence()
            self._PlayMidTransitionCurves()

    def Stop(self):
        self.ending = True
        if self.cameraLookAnimation is not None:
            self.cameraLookAnimation.Stop()
        with util.ExceptionEater('JumpTransitionTunnelEnd'):
            if not self.destinationSceneApplied:
                self.transition.ApplyDestinationScene()
            camSvc = sm.GetService('camera')
            anim = camSvc.animationController
            offset = geo2.Vec3Scale(self.normDir, -self.camOffsetEnd)
            anim.Schedule(transitioncam.InExtraTransl(self.endCamDurationS, offset))
            anim.Schedule(transitioncam.InFOV(self.endCamDurationS))
            camSvc.shakeController.DoCameraShake(self.shakeJumpIn)
        if self.startCS is not None:
            self.startCS.Stop()
        if self.mainCS is not None:
            self.mainCS.Stop()
        if self.stopCS is not None:
            self.stopCS.Play()
        self.FadeUIIn()
        uthread.new(self.BlinkSystemName)
        uthread.new(self._DelayedCleanup)

    def _DelayedCleanup(self):
        blue.synchro.SleepSim(2000)
        if self.stopCS is not None:
            self.stopCS.Stop()
        if self.scene.warpTunnel == self.effectRoot:
            self.scene.warpTunnel = None
        self.effect = None
        self.effectRoot = None
        sm.GetService('camera').shakeController.EndCameraShake('JumpIn')

    def DoCameraLookAnimation(self):
        if self.cameraLookAnimation is not None:
            self.cameraLookAnimation.Start()

    def BlinkSystemName(self):
        blue.synchro.Sleep(1000)
        infoPanelSvc = sm.GetService('infoPanel')
        panel = infoPanelSvc.GetPanelByTypeID(infoPanel.PANEL_LOCATION_INFO)
        uicore.animations.FadeOut(panel.headerLabel, loops=4, duration=0.5, curveType=uiconst.ANIM_WAVE)

    def GetUIToFade(self):
        toFade = [uicore.layer.bracket]
        from eve.client.script.ui.inflight.overview import OverView
        overview = OverView.GetIfOpen()
        if overview is not None:
            try:
                toFade.append(overview.sr.scroll.sr.content)
            except:
                log.LogWarn('Failed to get overview contents to fade while jumping')

        return toFade

    def FadeUIOut(self):
        if self.ending:
            log.LogWarn('Jump Transition: Trying to fade out ui while ending.')
            return
        objs = self.GetUIToFade()
        for obj in objs:
            uicore.animations.FadeOut(obj, duration=1)

        blue.synchro.SleepSim(1000)
        if not self.ending:
            for obj in objs:
                obj.display = False

    def FadeUIIn(self):
        objs = self.GetUIToFade()
        for obj in objs:
            obj.display = True
            uicore.animations.FadeIn(obj, duration=1)

        blue.synchro.SleepSim(1000)
        for obj in objs:
            obj.opacity = 1.0
            obj.display = True

    def StartWarpTransitionAudio(self):
        eventName = 'transition_jump_play_%02d' % self.randomSoundNumber
        sm.GetService('audio').SendUIEvent(eventName)

    def StartGateEffectAudio(self):
        self.randomSoundNumber = random.randint(1, 10)
        eventName = 'jumpgate_new_play_%02d' % self.randomSoundNumber
        sm.GetService('audio').SendUIEvent(eventName)

    def StopWarpTransitionAudio(self):
        eventName = 'transition_jump_arrival_play_%02d' % self.randomSoundNumber
        sm.GetService('audio').SendUIEvent(eventName)


class JumpTransitionGate(JumpTransitionTunnel):
    """
    Effect for player transition when jumping through stargates
    """
    __guid__ = 'effects.JumpTransitionGate'

    def __init__(self):
        JumpTransitionTunnel.__init__(self)

    def Prepare(self, shipBall, stargateID, stargateBall):
        destStargate, destSystem = sm.GetService('michelle').GetBallpark().GetInvItem(stargateID).jumps[0]
        JumpTransitionTunnel.Prepare(self, shipBall, destSystem)
        self.effectRoot.rotation = stargateBall.model.rotationCurve.value
        self.transition.InitializeGateTransition(destSystem, destStargate)
        gateSize = stargateBall.model.boundingSphereRadius
        finalTranslation = self.shipBall.radius * 10
        self.cameraLookAnimation = transitioncam.LookAnimation(self.camera, self.effectRoot.rotation, startFocusID=stargateID, endFocusID=destStargate, startTranslation=gateSize * 3, endTranslation=finalTranslation)


class JumpTransitionCyno(JumpTransitionTunnel):
    """
    Effect for player transition when cyno jumping
    """
    __guid__ = 'effects.JumpTransitionCyno'

    def __init__(self):
        JumpTransitionTunnel.__init__(self)

    def Prepare(self, shipBall, destSystemID, rotation):
        JumpTransitionTunnel.Prepare(self, shipBall, destSystemID)
        self.effectRoot.rotation = rotation
        self.transition.InitializeCynoTransition(destSystemID)
        self.initToStartDelay = 0
        self.cameraLookAnimation = transitioncam.LookAnimation(self.camera, self.effectRoot.rotation)


class JumpTransitionWormhole(object):
    """
    Effect for player transition when going through wormholes
    """
    __guid__ = 'effect.JumpTransitionWormhole'

    def __init__(self):
        self.resPath = 'res:/fisfx/jump/wormholes/transition.red'
        self.model = None
        self.scene = None
        self.startCS = None
        self.stopCS = None
        self.midCS = None
        self.translationFromParent = None
        self.mainSequenceFinished = False
        self.translationFromWormhole = 6000.0

    def SetScene(self, scene):
        if self.model is None:
            return
        if self.scene is not None:
            self.scene.objects.fremove(self.model)
        scene.objects.append(self.model)
        self.scene = scene

    def Prepare(self, wormholeItem, destNebulaPath, srcNebulaPath):
        if self.resPath is not None:
            self.model = trinity.Load(self.resPath)
        transition = sm.GetService('viewState').GetTransitionByName('inflight', 'inflight')
        transition.InitializeWormholeTransition(cfg.graphics.Get(wormholeItem.nebulaType).graphicFile)
        self.transition = transition
        cubeParams = self.model.Find('trinity.TriTextureCubeParameter')
        for cube in cubeParams:
            if cube.name == 'SourceNebulaMap':
                cube.resourcePath = srcNebulaPath
            else:
                cube.resourcePath = destNebulaPath

        for each in self.model.curveSets:
            if each.name == 'start':
                self.startCS = each
            elif each.name == 'stop':
                self.stopCS = each
            elif each.name == 'middle':
                self.midCS = each

        transition.SetTransitionEffect(self)
        self.itemID = wormholeItem.itemID

    def _PlayMidCurves(self):
        blue.synchro.Sleep(500)
        if self.startCS is not None:
            self.startCS.Play()
        blue.synchro.Sleep(1000)
        self.transition.ApplyDestinationScene()
        if self.midCS is not None:
            self.midCS.Play()
        self.mainSequenceFinished = True

    def Start(self):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        self.translationFromParent = camera.translationFromParent
        camSvc = sm.GetService('camera')
        camSvc.LookAt(self.itemID)
        camSvc.TranslateFromParentAccelerated(self.translationFromParent, self.translationFromWormhole, 0.75, 0.25)
        uthread.new(self._PlayMidCurves)

    def Abort(self):
        self.transition.Abort()

        def _waitForFinish():
            while not self.mainSequenceFinished:
                blue.synchro.Yield()

            self.Stop()

        uthread.new(_waitForFinish)

    def Stop(self, reason = STOP_REASON_DEFAULT):
        uthread.new(self.BlinkSystemName)
        if self.model is None:
            return
        uthread.new(self._DelayedStop)

    def _DelayedStop(self):
        if self.startCS is not None:
            self.startCS.Stop()
        if self.stopCS is not None:
            self.stopCS.Play()
        blue.synchro.SleepSim(500)
        sm.GetService('camera').TranslateFromParentAccelerated(self.translationFromWormhole, self.translationFromParent, 0.75, 4.0)
        blue.synchro.SleepSim(1500)
        if self.scene is not None:
            self.scene.objects.fremove(self.model)
            self.scene = None
        self.model = None

    def BlinkSystemName(self):
        blue.synchro.Sleep(1000)
        infoPanelSvc = sm.GetService('infoPanel')
        panel = infoPanelSvc.GetPanelByTypeID(infoPanel.PANEL_LOCATION_INFO)
        uicore.animations.FadeOut(panel.headerLabel, loops=4, duration=0.5, curveType=uiconst.ANIM_WAVE)

    def FadeOut(self, obj):
        uicore.animations.FadeOut(obj, duration=1)

    def FadeIn(self, obj):
        uicore.animations.FadeIn(obj, duration=1)


class JumpDriveIn(ShipEffect):
    __guid__ = 'effects.JumpDriveIn'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        if shipBall is None:
            self.sfxMgr.LogError(self.__guid__, ' could not find a ball')
            return
        ShipEffect.Start(self, duration)

    def DelayedHide(self, shipBall, delay):
        blue.pyos.synchro.SleepSim(delay)
        if shipBall is not None and shipBall.model is not None:
            shipBall.model.display = False


class JumpDriveInBO(JumpDriveIn):
    __guid__ = 'effects.JumpDriveInBO'


class JumpDriveOut(JumpDriveIn):
    __guid__ = 'effects.JumpDriveOut'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        here = sm.GetService('map').GetItem(session.solarsystemid2)
        there = sm.GetService('map').GetItem(self.graphicInfo[0])
        yaw, pitch = mathCommon.GetYawAndPitchAnglesRad((here.x, here.y, here.z), (there.x, there.y, there.z))
        quat = geo2.QuaternionRotationSetYawPitchRoll(yaw, pitch, 0)
        self.gfxModel.rotation = quat
        if eve.session.shipid == shipID:
            self.playerEffect = JumpTransitionCyno()
            self.playerEffect.Prepare(shipBall, self.graphicInfo[0], quat)
            self.playerEffect.SetScene(self.fxSequencer.GetScene())
            self.playerEffect.Start()
        ShipEffect.Start(self, duration)
        uthread.new(self.DelayedHide, shipBall, 180)


class JumpDriveOutBO(JumpDriveOut):
    __guid__ = 'effects.JumpDriveOutBO'


class JumpIn(JumpDriveIn):
    __guid__ = 'effects.JumpIn'

    def Start(self, duration):
        scaling = self.gfxModel.scaling
        self.gfxModel.scaling = (scaling[0] * 0.005, scaling[1] * 0.005, scaling[2] * 0.005)
        JumpDriveIn.Start(self, duration)


class JumpOut(ShipEffect):
    __guid__ = 'effects.JumpOut'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        uthread.new(self.DelayedHide, shipBall)
        targetID = self.ballIDs[1]
        targetBall = self.fxSequencer.GetBall(targetID)
        if session.shipid == shipID:
            if hasattr(shipBall, 'KillBooster'):
                shipBall.KillBooster()
            self.playerEffect = JumpTransitionGate()
            self.playerEffect.Prepare(shipBall, targetID, targetBall)
            self.playerEffect.SetScene(self.fxSequencer.GetScene())
            self.playerEffect.Start()
        if hasattr(self.gfx, 'scaling'):
            radius = shipBall.radius
            self.gfx.scaling = (radius, radius, radius)
            self.gfxModel.scaling = (1, 1, 1)
        listener = None
        for obs in self.gfx.observers:
            if obs.observer.name.startswith('effect_'):
                listener = obs.observer

        for curveSet in targetBall.model.curveSets:
            if curveSet.name == 'GateActivation':
                for curve in curveSet.curves:
                    if curve.name == 'audioEvents':
                        curve.eventListener = listener

        targetBall.Activate()
        targetBall.JumpDeparture()

    def DelayedHide(self, shipBall):
        blue.pyos.synchro.SleepSim(880)
        self.fxSequencer.OnSpecialFX(shipBall.id, None, None, None, None, 'effects.Uncloak', 0, 0, 0)
        if shipBall is not None and shipBall.model is not None:
            shipBall.model.display = False


class JumpOutWormhole(JumpDriveIn):
    __guid__ = 'effects.JumpOutWormhole'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        if getattr(shipBall, 'model', None) is not None:
            self.fxSequencer.OnSpecialFX(shipID, None, None, None, None, 'effects.CloakRegardless', 0, 1, 0, -1, None)
        uthread.new(self.DelayedHide, shipBall, 2000)
        wormholeID = self.ballIDs[1]
        wormholeBall = self.fxSequencer.GetBall(wormholeID)
        if eve.session.shipid == shipID:
            if hasattr(shipBall, 'KillBooster'):
                shipBall.KillBooster()
            scene = self.fxSequencer.GetScene()
            self.playerEffect = JumpTransitionWormhole()
            srcNebula = scene.envMapResPath
            targetNebula = getattr(wormholeBall, 'targetNebulaPath', None)
            wormholeItem = self.fxSequencer.GetItem(wormholeID)
            self.playerEffect.Prepare(wormholeItem, targetNebula, srcNebula)
            self.playerEffect.SetScene(scene)
            self.playerEffect.Start()
        if hasattr(self.gfx, 'scaling'):
            radius = shipBall.radius
            self.gfx.scaling = (radius, radius, radius)
            self.gfxModel.scaling = (1, 1, 1)
        self.PlayNamedAnimations(wormholeBall.model, 'Activate')
        wormholeBall.PlaySound('worldobject_wormhole_jump_play')

    def Stop(self, reason = STOP_REASON_DEFAULT):
        if self.GetEffectShipID() == session.shipid and reason == STOP_REASON_DEFAULT:
            self.playerEffect.Abort()
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        if shipBall is not None and shipBall.model is not None:
            shipBall.model.display = True


class GateActivity(GenericEffect):
    __guid__ = 'effects.GateActivity'

    def Prepare(self):
        gateBall = self.GetEffectShipBall()
        self.gfx = gateBall.model
        self.AddSoundToEffect(2)

    def Start(self, duration):
        gateID = self.ballIDs[0]
        gateBall = self.fxSequencer.GetBall(gateID)
        if gateBall is None:
            self.sfxMgr.LogError('GateActivity could not find a gate ball')
            return
        if gateBall.model is None:
            self.sfxMgr.LogError('GateActivity could not find a gate ball')
            return
        gateBall.Activate()
        gateBall.JumpArrival()

    def Stop(self, reason = STOP_REASON_DEFAULT):
        self.gfx.observers.remove(self.observer)
        self.observer.observer = None


class WormholeActivity(GenericEffect):
    __guid__ = 'effects.WormholeActivity'

    def Start(self, duration):
        wormholeID = self.ballIDs[0]
        wormholeBall = self.fxSequencer.GetBall(wormholeID)
        if wormholeBall is None:
            self.sfxMgr.LogError('WormholeActivity could not find a wormhole ball')
            return
        if wormholeBall.model is None:
            self.sfxMgr.LogError('WormholeActivity could not find a wormhole ball')
            return
        self.PlayNamedAnimations(wormholeBall.model, 'Activate')
        wormholeBall.PlaySound('worldobject_wormhole_jump_play')
