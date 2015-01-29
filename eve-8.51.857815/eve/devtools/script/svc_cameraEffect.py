#Embedded file name: eve/devtools/script\svc_cameraEffect.py
"""
Service for camera special effects, like playing back animation clips that controsl pst effects and the like.
"""
import blue
import service
import trinity
import uthread
import geo2
import random
import carbonui.const as uiconst
import os
import state
import uiprimitives
import uicontrols
animationFolder = 'res:/Animation/CameraAnimation/'
animationLibrary = {'flyby': [[animationFolder + 'LookAndZoom_camera.gr2', True], [animationFolder + 'FlybyBasicBehind_camera.gr2', True]],
 'flybywarp': [[animationFolder + 'LookAndZoom_camera.gr2', False],
               [animationFolder + 'FlybyWarpFollowStruggling_camera.gr2', True],
               [animationFolder + 'FlybyWarpFrontShaky_camera.gr2', True],
               [animationFolder + 'FlybyBasicPan_camera.gr2', True],
               [animationFolder + 'FlybyWarpFlyIntoDistance_camera.gr2', True]],
 'stargate': [[animationFolder + 'FlybyBasicPan_camera.gr2', True], [animationFolder + 'FlybyBasicPan_camera.gr2', True]],
 'idle': [[animationFolder + 'IdleBasicPanBack_camera.gr2', True],
          [animationFolder + 'IdleBasicPanFront_camera.gr2', True],
          [animationFolder + 'IdleCameraPanToBG_camera.gr2', True],
          [animationFolder + 'IdlePanAlongSide_camera.gr2', True]],
 'explode': [[animationFolder + 'LookAndZoom_camera.gr2', True], [animationFolder + 'FlybyBasicBehind_camera.gr2', True]],
 'twotargets': [[animationFolder + 'FixedBehindShipClose_camera.gr2', True], [animationFolder + 'IdleBasicPanBack_camera.gr2', True], [animationFolder + 'TwoTargetOTSrZoomTargetWeight_camera.gr2', True]]}
IDLE_TIMER = 5.0

def Msg(msg):
    eve.Message('CustomNotify', {'notify': msg})


class CameraEffectSvc(service.Service):
    """
    Class to run special camera effects, notably animation clips that run animations with
    special effects like blur and exposure controlled by the animation.
    """
    __guid__ = 'svc.cameraEffect'
    __update_on_reload__ = 1
    __startupdependencies__ = ['settings']
    __notifyevents__ = ['OnAutoPilotOff',
     'OnAutoPilotJump',
     'OnAutoPilotDock',
     'OnAutoPilotApproach',
     'OnAutoPilotWarp',
     'OnWarpStarted',
     'OnWarpStarted2',
     'OnWarpFinished',
     'OnWarpAlign',
     'OnObjectExplode',
     'OnShipExplode']

    def __init__(self):
        service.Service.__init__(self)
        self.vectorTracks = None
        self.resetCamera = False
        self.continuousType = None
        self.lastInputTime = None
        self.playingClip = False
        self.interrupt = False
        self.overrideRenderJob = None
        self.isRunning = False

    def Run(self, *args):
        self.Reset()
        self.pending = None
        self.busy = None

    def Stop(self, stream):
        pass

    def StartListener(self):
        self.isRunning = True

    def StopListener(self):
        self.isRunning = False

    def OnAutoPilotOff(self):
        self.TriggerCameraEvent('autoPilotOff')

    def OnAutoPilotJump(self):
        self.TriggerCameraEvent('autoPilotStarGate')

    def OnAutoPilotDock(self):
        self.TriggerCameraEvent('autoPilotDock')

    def OnAutoPilotApproach(self):
        self.TriggerCameraEvent('autoPilotApproach')

    def OnAutoPilotWarp(self):
        self.TriggerCameraEvent('autoPilotWarp')

    def OnWarpStarted(self):
        self.TriggerCameraEvent('warpStart')

    def OnWarpStarted2(self):
        self.TriggerCameraEvent('warpStart2')

    def OnWarpFinished(self):
        self.TriggerCameraEvent('warpStop')

    def OnWarpAlign(self):
        self.TriggerCameraEvent('warpAlign')

    def OnObjectExplode(self, model):
        self.TriggerCameraEvent('objectExplode', model)

    def OnShipExplode(self, model):
        self.TriggerCameraEvent('shipExplode', model)

    def Cleanup(self):
        pass

    def Reset(self):
        pass

    def ResisterEvents(self):
        self.inputCookie = uicore.event.RegisterForTriuiEvents((uiconst.UI_KEYUP, uiconst.UI_KEYDOWN, uiconst.UI_MOUSEDOWN), self.OnInputCallback)

    def OnInputCallback(self, *args):
        self.lastInputTime = blue.os.GetSimTime()
        self.ResetCamera()
        return True

    def SetRenderJob(self, rj):
        self.overrideRenderJob = rj

    def TargetCamera(self):
        targetService = sm.GetService('target')
        targetId = targetService.GetActiveTargetID()
        if targetId:
            ballpark = sm.GetService('michelle').GetBallpark()
            playerBall = ballpark.GetBall(eve.session.shipid)
            targetBall = ballpark.GetBall(targetId)
            self.PlayCameraAnimation(animationFolder + 'FixedBehindShipClose_camera.gr2', alignTargets=[playerBall, targetBall], loop=True)

    def FollowCamera(self, target, aimTarget = None):
        viewStep, proj = self.GetViewAndProjection()
        if viewStep:
            viewStep.view = trinity.TriView()
        camera = sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True)
        globalSceneScale = 1.0
        ballpark = sm.GetService('michelle').GetBallpark()
        ball = ballpark.GetBall(eve.session.shipid)
        self.resetCamera = False
        while not self.resetCamera and target:
            time = blue.os.GetSimTime()
            rot = target.rotationCurve
            if True:
                rotation = rot.GetQuaternionAt(time)
                translation = target.translationCurve.GetVectorAt(time)
                if ball:
                    targetPos = ball.model.worldPosition
                    targetVector = (targetPos[0] - translation.x, targetPos[0] - translation.x, targetPos[0] - translation.x)
                    targetVector = geo2.Vec3Normalize(targetVector)
                    dist = 100.0
                    elevation = 0.0
                    translation.x = translation.x - targetVector[0] * dist
                    translation.y = translation.y - targetVector[1] * dist + elevation
                    translation.z = translation.z - targetVector[2] * dist
                    lookat = geo2.MatrixLookAtRH((translation.x, translation.y, translation.z), targetPos, (0.0, 1.0, 0.0))
                trans = geo2.MatrixTranslation(translation.x * globalSceneScale, translation.y * globalSceneScale, translation.z * globalSceneScale)
                rot = geo2.MatrixRotationQuaternion((rotation.x,
                 rotation.y,
                 rotation.z,
                 rotation.w))
                if viewStep and viewStep.view:
                    viewStep.view.transform = lookat
            blue.synchro.Yield()

        if viewStep:
            viewStep.view = None
        proj.projection = camera.projectionMatrix
        self.resetCamera = False

    def TriggerCameraEvent(self, eventType, parent = None):
        """
        Tell the system something happened. This could run an animation, or change the way
        a camera sequence acts in response to an event. Example: When in autopilot, a warp
        gate event would run that kind of animation.
        """
        if not self.isRunning:
            return
        txt = 'Camera event: %s' % eventType
        self.LogNotice(txt)
        Msg(txt)
        if eventType == 'idle':
            self.PlayCameraAnimationType('idle', continuous=1)
        if eventType == 'warpAlign':
            self.PlayCameraAnimationType('idle', continuous=1)
        if eventType == 'warpStart2':
            self.PlayCameraAnimationType('flybywarp', continuous=1)
        if eventType == 'autoPilotApproach':
            self.PlayCameraAnimationType('flyby', continuous=1)
        if eventType == 'autoPilotStarGate':
            self.PlayCameraAnimationType('stargate')
        if eventType == 'warpStop' or eventType == 'autoPilotOff':
            self.ResetCamera()
        if eventType == 'objectExplode':
            self.PlayCameraAnimationType('explode', parent=parent)
        if eventType == 'followModel':
            self.FollowCamera(parent)
        if eventType == 'cockpit':
            self.PlayCameraAnimation(animationFolder + 'FixedCockpit_camera.gr2', alignToParent=True, loop=True)
        if eventType == 'fixed':
            self.PlayCameraAnimation(animationFolder + 'FixedBehindShip_camera.gr2', alignToParent=True, loop=True)

    def PlayCameraAnimationType(self, animationType, continuous = False, skipIndex = None, parent = None, alignTargets = None, overrideContinuous = False):
        if animationType not in animationLibrary:
            self.LogWarn('Invalid camera animation type:', animationType)
        candidates = animationLibrary[animationType]
        indexToPlay = random.randint(0, len(candidates) - 1)
        while len(candidates) > 1 and indexToPlay == skipIndex:
            indexToPlay = random.randint(0, len(candidates) - 1)

        animData = candidates[indexToPlay]
        self.PlayCameraAnimation(animData[0], alignToParent=animData[1], parent=parent, alignTargets=alignTargets)
        if continuous and not overrideContinuous:
            self.continuousType = [animationType, indexToPlay]

    def PlayCameraDirectedSequence(self, type):
        self.continuousType = ['directed', type]
        self.UpdateDirected()

    def ChooseAtRandom(self, array):
        index = random.randint(0, len(array) - 1)
        return array[index]

    def UpdateDirected(self):
        self.LogInfo('Director: Choosing')
        self.LogInfo(repr(self))
        ballpark = sm.GetService('michelle').GetBallpark()
        rand = random.random()
        targetService = sm.GetService('target')
        targets = targetService.targets
        if rand < 0.3 or len(targets) < 1:
            self.LogInfo('Idle clip')
            candidates = targets + [eve.session.shipid]
            target = self.ChooseAtRandom(candidates)
            ball = ballpark.GetBall(target)
            self.PlayCameraAnimationType('idle', True, parent=ball.model, overrideContinuous=True)
        else:
            self.LogInfo('Target clip')
            target = self.ChooseAtRandom(targets)
            targetBall = ballpark.GetBall(target)
            playerBall = ballpark.GetBall(eve.session.shipid)
            if random.random() > 0.5:
                self.LogInfo('Enemy to player')
                self.PlayCameraAnimationType('twotargets', True, alignTargets=[targetBall, playerBall], overrideContinuous=True)
            else:
                self.LogInfo('Player to enemy')
                self.PlayCameraAnimationType('twotargets', True, alignTargets=[playerBall, targetBall], overrideContinuous=True)

    def UpdateContinuous(self):
        if self.continuousType:
            if self.continuousType[0] == 'directed':
                self.UpdateDirected()
            else:
                self.PlayCameraAnimationType(self.continuousType[0], True, self.continuousType[1])

    def PlayCameraAnimation(self, resPath, alignToParent = False, alignTargets = None, loop = False, parent = None, reload = False):
        uthread.new(self._PlayCameraAnimation, resPath, alignToParent, alignTargets, loop, parent, reload)

    def GetAnimationLibrary(self):
        return animationLibrary

    def _PlayCameraAnimation(self, resPath, alignToParent = False, alignTargets = None, loop = False, parent = None, reload = False):
        if self.playingClip:
            self.interrupt = True
            blue.synchro.Yield()
        self.playingClip = True

        def RemoveCurveSetByName(scene, curveSetName):
            removeList = []
            for cset in scene.curveSets:
                if cset.name == curveSetName:
                    removeList.append(cset)

            for cset in removeList:
                scene.curveSets.remove(cset)

        curveSetName = 'AnimatedCamera'
        cset = trinity.TriCurveSet()
        cset.name = curveSetName
        cameraTransformTrack = trinity.Tr2GrannyTransformTrack()
        cameraTransformTrack.grannyResPath = str(resPath)
        cameraTransformTrack.name = 'camera1'
        cameraTransformTrack.group = 'camera1'
        cameraTransformTrack.cycle = True
        cset.curves.append(cameraTransformTrack)
        if alignTargets:
            t1 = alignTargets[0].model.worldPosition
            t2 = alignTargets[1].model.worldPosition
            distVector = geo2.Vec3Subtract(t1, t2)
            dist = geo2.Vec3Length(distVector)
            shakeSeq = trinity.TriXYZScalarSequencer()
            shakeSeq.XCurve = trinity.TriPerlinCurve()
            shakeSeq.YCurve = trinity.TriPerlinCurve()
            shakeSeq.ZCurve = trinity.TriPerlinCurve()
            for pCurve in [shakeSeq.XCurve, shakeSeq.YCurve, shakeSeq.ZCurve]:
                shake = dist / 50.0
                pCurve.scale = shake
                pCurve.offset = -shake / 2.0
                pCurve.speed = 0.8
                pCurve.alpha = 1.3

            cset.curves.append(shakeSeq)
        if reload:
            cameraTransformTrack.grannyRes.Reload()
        while cameraTransformTrack.grannyRes.isLoading:
            blue.synchro.Yield()

        numVecTracks = cameraTransformTrack.grannyRes.GetVectorTrackCount(0)
        if numVecTracks:
            self.vectorTracks = {}
        for trackNr in range(numVecTracks):
            vecTrack = trinity.Tr2GrannyVectorTrack()
            vecTrack.grannyResPath = str(resPath)
            vecTrack.group = 'camera1'
            vecTrack.name = cameraTransformTrack.grannyRes.GetVectorTrackName(0, trackNr)
            vecTrack.cycle = True
            cset.curves.append(vecTrack)
            self.vectorTracks[vecTrack.name] = vecTrack

        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        RemoveCurveSetByName(scene, curveSetName)
        scene.curveSets.append(cset)
        cset.Play()
        uthread.new(self._UpdateCameraAnimation, alignToParent, alignTargets, loop, clipName=resPath, parent=parent)

    def GetRenderJob(self):
        if self.overrideRenderJob:
            return self.overrideRenderJob
        for rj in trinity.renderJobs.recurring:
            if rj.name == 'BaseSceneRenderJob':
                return rj

    def GetViewAndProjection(self):
        viewStep = None
        proj = None
        rj = self.GetRenderJob()
        if rj:
            for step in rj.steps:
                if step.name == 'SET_VIEW':
                    viewStep = step
                if step.name == 'SET_PROJECTION':
                    proj = step

        return (viewStep, proj)

    def _UpdateCameraAnimation(self, alignToParent = False, alignTargets = None, loop = False, clipName = None, parent = None):

        def FindParametersInPostFx():
            blurScaleH = None
            blurScaleV = None
            blurFade = None
            exposure = None
            rj = self.GetRenderJob()
            if rj:
                for step in rj.steps:
                    if step.name == 'RJ_POSTPROCESSING':
                        if step.job:
                            for jobStep in step.job.steps:
                                if jobStep.name == 'PostProcess Blur':
                                    for fx in jobStep.PostProcess.stages:
                                        for param in fx.parameters:
                                            if param.name == 'ScalingFactor':
                                                if fx.name == 'Gaussian Horizontal Blur':
                                                    blurScaleH = param
                                                if fx.name == 'Gaussianl Vertical Blur':
                                                    blurScaleV = param
                                                if fx.name == '4x Up Filter and Add':
                                                    blurFade = param

                                if jobStep.name == 'PostProcess Exposure':
                                    for fx in jobStep.PostProcess.stages:
                                        for param in fx.parameters:
                                            if param.name == 'ScalingFactor':
                                                if fx.name == '4x Up Filter and Add':
                                                    exposure = param

            return (blurScaleH,
             blurScaleV,
             blurFade,
             exposure)

        transformTrack = None
        shakeSequencer = None
        duration = 0.0
        curveSetName = 'AnimatedCamera'
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        viewStep, proj = self.GetViewAndProjection()
        camera = viewStep.camera
        for cset in scene.curveSets:
            if cset.name == curveSetName:
                transformTrack = cset.curves[0]
                if len(cset.curves) > 1:
                    shakeSequencer = cset.curves[1]

        duration = transformTrack.duration - 1 / 10.0
        oldFov = camera.fieldOfView
        ppJob.AddPostProcess('Blur', 'res:/fisfx/postprocess/blur.red')
        ppJob.AddPostProcess('Exposure', 'res:/fisfx/postprocess/exposure.red')
        blurScaleH, blurScaleV, blurFade, exposure = FindParametersInPostFx()
        ballpark = sm.GetService('michelle').GetBallpark()
        ball = ballpark.GetBall(session.shipid)
        if parent:
            ball = parent.translationCurve
        if alignTargets:
            ball = alignTargets[0]
        if viewStep:
            viewStep.view = trinity.TriView()
        startTime = blue.os.GetSimTime()
        if loop:
            endTime = startTime + 36000000000L
        else:
            endTime = startTime + duration * 10000000
        time = startTime
        globalSceneScale = 4.0 / 30.0 * ball.model.boundingSphereRadius
        lastWorldPos = None
        lastWorldRot = None
        while time < endTime and not self.resetCamera and not self.interrupt:
            time = blue.os.GetSimTime()
            weight1 = 0.0
            weight2 = 0.0
            if self.vectorTracks:
                currentTime = trinity.device.animationTime
                for cvt in self.vectorTracks:
                    if cvt == 'targetWeight1' or cvt == 'targetWeight2':
                        vecTrack = self.vectorTracks[cvt]
                        if cvt == 'targetWeight1':
                            weight1 = vecTrack.value
                        else:
                            weight2 = vecTrack.value

            if viewStep:
                trans = geo2.MatrixTranslation(transformTrack.translation[0] * globalSceneScale, transformTrack.translation[1] * globalSceneScale, transformTrack.translation[2] * globalSceneScale)
                rot = geo2.MatrixRotationQuaternion(transformTrack.rotation)
                comp = geo2.MatrixMultiply(rot, trans)
                if alignToParent:
                    if not ball.model and lastWorldPos:
                        translation = lastWorldPos
                        rotation = lastWorldRot
                    else:
                        rotation = ball.GetQuaternionAt(time)
                        translation = ball.model.worldPosition
                    lastWorldPos = translation
                    lastWorldRot = rotation
                    transOffset = geo2.MatrixTranslation(translation[0], translation[1], translation[2])
                    rotOffset = geo2.MatrixRotationQuaternion((rotation.x,
                     rotation.y,
                     rotation.z,
                     rotation.w))
                    comp = geo2.MatrixMultiply(comp, rotOffset)
                    comp = geo2.MatrixMultiply(comp, transOffset)
                if alignTargets:
                    t1 = alignTargets[0].model.worldPosition
                    t2 = alignTargets[1].model.worldPosition
                    if True:
                        sphereOffset = alignTargets[1].model.boundingSphereCenter
                        qr = alignTargets[1].model.rotationCurve.GetQuaternionAt(time)
                        quatRotation = (qr.x,
                         qr.y,
                         qr.z,
                         qr.w)
                        correctedOffset = geo2.QuaternionTransformVector(quatRotation, sphereOffset)
                        t2 = geo2.Vec3Add(t2, correctedOffset)
                    rot = geo2.MatrixLookAtRH(t2, t1, (0.0, 1.0, 0.0))
                    rot = geo2.MatrixInverse(rot)
                    rot = (rot[0],
                     rot[1],
                     rot[2],
                     (t1[0],
                      t1[1],
                      t1[2],
                      1.0))
                    comp = geo2.MatrixMultiply(comp, rot)
                    if weight1 > 0.0001:
                        shake = shakeSequencer.value
                        pos = (comp[3][0], comp[3][1], comp[3][2])
                        targetPos = (t2[0] + shake.x, t2[1] + shake.y, t2[2] + shake.z)
                        lookat = geo2.MatrixLookAtRH(pos, targetPos, (0.0, 1.0, 0.0))
                        lookat = geo2.MatrixInverse(lookat)
                        qlookat = geo2.QuaternionRotationMatrix(lookat)
                        qorig = geo2.QuaternionRotationMatrix(comp)
                        qresult = geo2.Lerp(qorig, qlookat, weight1)
                        mresult = geo2.MatrixRotationQuaternion(qresult)
                        comp = (mresult[0],
                         mresult[1],
                         mresult[2],
                         comp[3])
                if viewStep.view:
                    viewStep.view.transform = geo2.MatrixInverse(comp)
            if self.vectorTracks:
                currentTime = trinity.device.animationTime
                for cvt in self.vectorTracks:
                    if cvt == 'fov':
                        vecTrack = self.vectorTracks['fov']
                        fovValue = vecTrack.value
                        camera.fieldOfView = fovValue
                        proj.projection.PerspectiveFov(fovValue, trinity.device.width / float(trinity.device.height), camera.frontClip, camera.backClip)
                    if cvt == 'blur':
                        vecTrack = self.vectorTracks['blur']
                        blurValue = vecTrack.value
                        if blurScaleH and blurScaleV and blurFade:
                            blurScaleH.value = blurValue
                            blurScaleV.value = blurValue
                            if blurValue > 0.01:
                                blurFade.value = 1.0
                            else:
                                blurFade.value = 0.0
                    if cvt == 'exposure':
                        vecTrack = self.vectorTracks['exposure']
                        exposureValue = vecTrack.value
                        if exposure:
                            exposure.value = exposureValue

                if 'fov' not in self.vectorTracks:
                    camera.fieldOfView = oldFov
                    proj.projection.PerspectiveFov(oldFov, trinity.device.width / float(trinity.device.height), camera.frontClip, camera.backClip)
            blue.synchro.Yield()

        if exposure and blurFade:
            exposure.value = 0.0
            blurFade.value = 0.0
        if viewStep:
            viewStep.view = None
        camera.fieldOfView = oldFov
        if not self.interrupt:
            if not camera.fieldOfView == 1.0:
                self.LogWarn('Warning: Camera fov not 1, correcting...')
                camera.fieldOfView = 1.0
            proj.projection = camera.projectionMatrix
        self.playingClip = False
        if self.continuousType and not self.interrupt and not self.resetCamera:
            self.interrupt = False
            self.UpdateContinuous()
        self.resetCamera = False
        self.interrupt = False
        if clipName:
            self.LogInfo('Camera clip done:', clipName)

    def ResetCamera(self):
        self.resetCamera = True
        self.continuousType = None


class EffectCameraWindow(uicontrols.Window):
    __guid__ = 'uicls.EffectCameraWindow'
    default_windowID = 'effectCamera'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon('41_13')
        self.HideMainIcon()
        self.SetTopparentHeight(0)
        self.SetCaption('Effect Camera')
        self.SetMinSize([460, 100])
        self.svc = sm.GetService('cameraEffect')
        self.mainCont = uiprimitives.Container(name='params', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(5, 5, 5, 5))
        top = 0
        actions = ['Listen',
         'Flyby',
         'Idle',
         'Fixed',
         'Fixed Close',
         'Target',
         'Reset',
         'Pip']
        buttons = []
        for act in actions:
            b = [act,
             getattr(self, 'Do%s' % act.replace(' ', '')),
             (),
             None]
            buttons.append(b)

        btns = uicontrols.ButtonGroup(btns=buttons, parent=self.mainCont, idx=0, unisize=0)
        data = self.svc.GetAnimationLibrary()
        opts = []
        for clipType in data:
            for clipData in data[clipType]:
                label = os.path.splitext(os.path.basename(clipData[0]))[0].replace('_camera', '')
                label = clipType + ': ' + label
                opts.append((label, (clipData, clipType)))

        self.animationCombo = uicontrols.Combo(label='Select Animation Clip', parent=self.mainCont, options=opts, name='fileselect', align=uiconst.TOPLEFT, pos=(0, 20, 0, 0), width=350)
        uicontrols.Button(label='Play', parent=self.mainCont, align=uiconst.TOPLEFT, pos=(360, 20, 0, 0), func=self.PlayClip)

    def BeginDrag(self):
        pass

    def PlayClip(self, *args):
        clip, clipType = self.animationCombo.GetValue()
        Msg('Playing: %s of type %s' % (clip[0], clipType))
        blue.motherLode.Delete(clip[0])
        if not clipType == 'twotargets':
            self.svc.PlayCameraAnimation(clip[0], alignToParent=clip[1], loop=False, reload=True)
        else:
            targetService = sm.GetService('target')
            targetId = targetService.GetActiveTargetID()
            if targetId:
                ballpark = sm.GetService('michelle').GetBallpark()
                playerBall = ballpark.GetBall(eve.session.shipid)
                targetBall = ballpark.GetBall(targetId)
                if random.random() > 0.5:
                    self.svc.PlayCameraAnimation(clip[0], alignTargets=[playerBall, targetBall], reload=True)
                else:
                    self.svc.PlayCameraAnimation(clip[0], alignTargets=[targetBall, playerBall], reload=True)

    def DoListen(self, *args):
        if not self.svc.isRunning:
            self.svc.StartListener()
            Msg('Started listening to events')
        else:
            self.svc.StopListener()
            Msg('Stopped listening to events')

    def DoFlyby(self, *args):
        self.svc.PlayCameraAnimationType('flyby', continuous=True)

    def DoIdle(self, *args):
        self.svc.PlayCameraAnimationType('idle', continuous=True)

    def DoFixed(self, *args):
        self.svc.PlayCameraAnimation(animationFolder + 'FixedBehindShip_camera.gr2', alignToParent=True, loop=True)

    def DoFixedClose(self, *args):
        self.svc.PlayCameraAnimation(animationFolder + 'FixedCockpit_camera.gr2', alignToParent=True, loop=True)

    def DoTarget(self, *args):
        self.svc.TargetCamera()

    def DoEventWarpGate(self, *args):
        self.svc.TriggerCameraEvent('warpgate')

    def DoReset(self, *args):
        self.svc.ResetCamera()

    def DoPip(self, *args):
        wnd = PipWnd.Open(windowID='PipWnd')
        wnd.OpenWindow()
        wnd.OnSetCameraMode('idle')


class PipWnd(uicontrols.Window):
    """
    Window to view the action through a different camera, like cinematic and target cameras.
    """
    __notifyevents__ = ['OnSetDevice', 'OnResizeUpdate']
    default_windowID = 'pipWnd'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        if self.destroyed:
            return
        self.polling = False
        self.interruptPolling = False
        caption = 'Camera: idle'
        self.SetCaption(caption)
        self.sr.bottomarea = uiprimitives.Container(name='bottomarea', align=uiconst.TOALL, parent=self.sr.main)
        self.sr.scenepar = uiprimitives.Container(name='scenepar', align=uiconst.TOALL, parent=self.sr.bottomarea, left=1, top=2, state=uiconst.UI_NORMAL)
        try:
            self.sr.scenepar.children.remove(self.sr.sceneContainer)
        except:
            pass

        from eve.client.script.ui.control.scenecontainer import SceneContainer
        sc = SceneContainer(align=uiconst.TOALL)
        sc.pickState = uiconst.TR2_SPS_OFF
        sc.SetAlign(uiconst.TOALL)
        self.sr.scenepar.children.append(sc)
        sc.PrepareCamera()
        ball = sm.GetService('michelle').GetBall(eve.session.shipid)
        sc.camera.parent.translationCurve = ball
        sc.camera.translationFromParent = ball.radius * 3
        sc.PrepareSpaceScene()
        s2 = sm.GetService('sceneManager').GetActiveScene()
        sc.renderJob.SetActiveScene(s2)
        self.sr.sceneContainer = sc
        sc.UpdateViewPort()

    def BeginDrag(self):
        pass

    def GetCameraModes(self):
        return ['idle',
         'cinematic',
         'target',
         'selected',
         'cockpit',
         'fixed',
         'targetlookat']

    def OnSetCameraMode(self, camera, *args):
        if self.polling:
            self.interruptPolling = True
            blue.synchro.Yield()
        cameraSvc = sm.GetService('cameraEffect')
        cameraSvc.SetRenderJob(self.sr.sceneContainer.renderJob)
        cameraSvc.isRunning = True
        if camera in ('idle', 'cockpit', 'fixed'):
            cameraSvc.TriggerCameraEvent(camera)
        elif camera == 'cinematic':
            cameraSvc.PlayCameraDirectedSequence('combat')
        elif camera == 'selected':
            uthread.new(self._UpdateTargetCamera, 'selected')
        elif camera == 'targetlookat':
            uthread.new(self._UpdateTargetCamera, 'targetlookat')
        elif camera == 'target':
            uthread.new(self._UpdateTargetCamera, 'target')
        caption = 'Camera: %s' % camera
        self.SetCaption(caption)

    def _UpdateTargetCamera(self, cameraType):
        cameraSvc = sm.GetService('cameraEffect')
        targetService = sm.GetService('target')
        stateService = sm.GetService('state')
        ballpark = sm.GetService('michelle').GetBallpark()
        currentTargetId = None
        self.polling = True
        while not self.interruptPolling:
            if cameraType == 'selected':
                targetId = stateService.GetExclState(state.selected)
            else:
                targetId = targetService.GetActiveTargetID()
            if targetId and targetId != currentTargetId:
                targetBall = ballpark.GetBall(targetId)
                if hasattr(targetBall, 'FitHardpoints'):
                    targetBall.FitHardpoints()
                if cameraType == 'target' or cameraType == 'selected':
                    cameraSvc.PlayCameraAnimation(animationFolder + 'FixedBehindShipClose_camera.gr2', parent=targetBall.model, loop=True, alignToParent=False)
                elif cameraType == 'targetlookat':
                    cameraSvc.TargetCamera()
                currentTargetId = targetId
            elif not targetId and currentTargetId != eve.session.shipid:
                cameraSvc.TriggerCameraEvent(cameraType)
                currentTargetId = eve.session.shipid
            blue.synchro.Yield()

        self.polling = False
        self.interruptPolling = False

    def GetMenu(self, *args):
        modes = self.GetCameraModes()
        m = []
        for mode in modes:
            m += [[mode, self.OnSetCameraMode, (mode,
               None,
               None,
               None)]]

        return m

    def OnSetDevice(self):
        uthread.new(self.sr.sceneContainer.UpdateViewPort)

    def OnResize_(self, *args):
        self.OnResizeUpdate()

    def OnResizeUpdate(self, *args):
        if getattr(self.sr, 'sceneContainer', None) is not None:
            self.sr.sceneContainer.UpdateViewPort()

    def OpenWindow(self):
        self.SetMinSize([420, 320])
        self.SetMaxSize([None, None])
