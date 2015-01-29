#Embedded file name: carbonui\uiProcs.py
"""
Code required to create and manage ActionProcs for UI systems (camera, UI calls, audio).
Note: These may be split out further. This is a first pass, just to fix some stuff.
"""
import cameras
import GameWorld
import service
from carbon.common.script.zaction.zactionCommon import ProcTypeDef, ProcPropertyTypeDef

class UIProcSvc(service.Service):
    """
        Manages ActionProcs for UI systems (camera, audio, and UI).
    """
    __guid__ = 'svc.uiProcSvc'
    __machoresolve__ = 'location'
    __dependencies__ = ['cameraClient']

    def Run(self, *args):
        """
            Run the service. First calls into the base, then does local stuff.
        """
        service.Service.Run(self, *args)
        GameWorld.RegisterPythonActionProc('PerformPythonUICallback', self._PerformUICallback, ('callbackKey',))
        GameWorld.RegisterPythonActionProc('PlayEntityAudio', self._PlayEntityAudio, ('audioName', 'mls', 'TargetList'))
        GameWorld.RegisterPythonActionProc('PlayTutorialVoiceover', self._PlayTutorialVoiceOver, ('messageKey',))
        GameWorld.RegisterPythonActionProc('PushCameraWithTransition', self._PushCameraWithTransition, ('cameraName', 'behaviorNames', 'transitionSeconds', 'startHeight', 'TargetList'))
        GameWorld.RegisterPythonActionProc('PopCameraWithTransition', self._PopCameraWithTransition, ('transitionSeconds', 'retainYaw', 'retainPitch'))

    def _PushCameraWithTransition(self, cameraName, behaviorNames, transitionSeconds, startHeight, targetList):
        """
        Makes a certain camera the active camera with a transition between the old camera and the new camera
        """
        entity = self.entityService.FindEntityByID(targetList[0])
        cameraClass = getattr(cameras, cameraName)
        camera = cameraClass()
        camera.pushUp = startHeight
        if hasattr(camera, 'SetEntity'):
            camera.SetEntity(entity)
        names = behaviorNames.split(',')
        for name in names:
            name = name.replace(' ', '')
            if len(name):
                behaviorClass = getattr(cameras, name)
                behavior = behaviorClass()
                camera.AddBehavior(behavior)

        transition = cameras.LinearTransitionBehavior(transitionSeconds=float(transitionSeconds))
        self.cameraClient.PushActiveCamera(camera, transitionBehaviors=[transition])
        return True

    def _PopCameraWithTransition(self, transitionSeconds, retainYaw, retainPitch):
        activeCamera = self.cameraClient.GetActiveCamera()
        cameraStack = self.cameraClient.GetCameraStack()
        comingActiveCamera = None
        try:
            comingActiveCamera = cameraStack[-2]
        except IndexError:
            comingActiveCamera = None

        if comingActiveCamera:
            if retainYaw:
                comingActiveCamera.SetYaw(activeCamera.yaw)
            if retainPitch:
                comingActiveCamera.SetPitch(activeCamera.pitch)
        transition = cameras.LinearTransitionBehavior(transitionSeconds=float(transitionSeconds))
        self.cameraClient.PopActiveCamera(transitionBehaviors=[transition])
        return True

    def _PerformUICallback(self, callbackKey):
        raise NotImplementedError('Each game must implement a _PerformUICallback that works with its UI.')

    def _PlayEntityAudio(self, audioName, mls, targetList):
        """
        A proc function that playes sound from an entity.
        audioName: Name of the wise audio file, or mls message containing the wise audio file.
        mls: bool that determines if audioName is the name of a audio file, or name of a mls message with audio.
        targetList: list of entities that will play the audio.
        
        Note: Entities must have a audioEmitter component to play audio.
        """
        if mls:
            message = cfg.GetMessage(audioName)
            audioName = message.audio
            if audioName.startswith('wise:/'):
                audioName = audioName[6:]
        for entityID in targetList:
            entity = self.entityService.FindEntityByID(entityID)
            audioComponent = entity.GetComponent('audioEmitter')
            if audioComponent:
                audioComponent.emitter.SendEvent(unicode(audioName))
            else:
                self.LogWarn('Entity with ID %s has no audio component. Audio file %s cannot be played from this entity.' % (entityID, audioName))

        return True

    def _PlayTutorialVoiceOver(self, messageKey):
        sm.GetService('tutorial').Action_Play_MLS_Audio(messageKey)
        return True


PerformPythonUICallback = ProcTypeDef(isMaster=True, procCategory='UI', properties=[ProcPropertyTypeDef('callbackKey', 'S', userDataType=None, isPrivate=True)], description='Performs a UI callback (opens a UI window, etc.). These are set per-game.')
PlayEntityAudio = ProcTypeDef(isMaster=True, procCategory='Audio', properties=[ProcPropertyTypeDef('audioName', 'S', userDataType=None, isPrivate=True, displayName='Audio Name'), ProcPropertyTypeDef('mls', 'B', userDataType=None, isPrivate=True, displayName='MLS')], description='Plays location-based audio at the location of the *target* entity.')
PlayTutorialVoiceover = ProcTypeDef(isMaster=True, procCategory='Audio', properties=[ProcPropertyTypeDef('messageKey', 'S', userDataType=None, isPrivate=True, displayName='MLS Message Key')], description='Plays the specified tutorial voiceover.')
PushCameraWithTransition = ProcTypeDef(isMaster=True, procCategory='Camera', properties=[ProcPropertyTypeDef('cameraName', 'S', userDataType=None, isPrivate=True, displayName='Camera Class Name'),
 ProcPropertyTypeDef('behaviorNames', 'S', userDataType=None, isPrivate=True, displayName='Behavior Class Names (comma separ.)'),
 ProcPropertyTypeDef('transitionSeconds', 'F', userDataType=None, isPrivate=True, displayName='Transition Seconds'),
 ProcPropertyTypeDef('startHeight', 'F', userDataType=None, isPrivate=True, displayName='Start Height From Floor')], description='Pushes a new camera onto the camera stack. THIS MAY BE DEPRECATED.')
PopCameraWithTransition = ProcTypeDef(isMaster=True, procCategory='Camera', properties=[ProcPropertyTypeDef('transitionSeconds', 'F', userDataType=None, isPrivate=True, displayName='Transition Seconds'), ProcPropertyTypeDef('retainYaw', 'B', userDataType=None, isPrivate=True, displayName='Retain yaw between cameras'), ProcPropertyTypeDef('retainPitch', 'B', userDataType=None, isPrivate=True, displayName='Retain pitch between cameras')], description='Pops a camera off the camera stack with a transition. THIS MAY BE DEPRECATED.')
exports = {'actionProcTypes.PerformPythonUICallback': PerformPythonUICallback,
 'actionProcTypes.PlayEntityAudio': PlayEntityAudio,
 'actionProcTypes.PlayTutorialVoiceover': PlayTutorialVoiceover,
 'actionProcTypes.PushCameraWithTransition': PushCameraWithTransition,
 'actionProcTypes.PopCameraWithTransition': PopCameraWithTransition}
