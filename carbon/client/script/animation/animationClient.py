#Embedded file name: carbon/client/script/animation\animationClient.py
"""
Maintains notification of animation events to animation controllers.
"""
import os
import service
import yaml
import blue
import GameWorld
from eve.client.script.incarna.animation.playerAnimationController import PlayerAnimationController
from eve.client.script.incarna.animation.bipedAnimationController import BipedAnimationController
import collections
import remotefilecache
import stackless
EVENT_TRACK_SOUND_LOOKUP_PATH = 'res:/Audio/animationEventTracks.yaml'

def OnMorphemeDiscreteEvents(animRef, *args):
    """
        Respond to an animation-related event.
    """
    animationClient = sm.GetService('animationClient')
    for trackID, eventUserData, trackUserData in args:
        animationController = animationClient.GetAnimationControllerFromNetwork(animRef)
        if animationController:
            animationClient._ProcessMorphemeDiscreteEvent(animationController, animRef, trackID, eventUserData, trackUserData)


class AnimationComponent:
    __guid__ = 'animation.AnimationComponent'

    def __init__(self):
        self.isClientPlayer = False
        self.updater = None
        self.updaterWaitingChannel = None
        self.controller = None
        self.poseState = None
        self.inThrow = False
        self.preThrowMode = None
        self.armTargetBone = {}
        self.armTargetBone['Left'] = None
        self.armTargetBone['Right'] = None
        self.attachments = {}
        self.poseObject = None
        self.idlePose = 'None'

    def AttachObject(self, obj, boneName, curveSet):
        """
        Store a dict of all attached objects associated with this character.
        """
        if boneName in self.attachments:
            self.DetachObject(boneName)
        self.attachments[boneName] = {}
        self.attachments[boneName]['object'] = obj
        self.attachments[boneName]['curveSet'] = curveSet

    def DetachObject(self, boneName):
        del self.attachments[boneName]

    def GetAttachedCurveSet(self, boneName):
        return self.attachments[boneName]['curveSet']

    def GetAttachedObject(self, boneName):
        return self.attachments[boneName]['object']

    def GetUpdater(self):
        if self.updaterWaitingChannel:
            self.updaterWaitingChannel.receive()
            self.updaterWaitingChannel = None
        return self.updater


class AnimationClient(service.Service):
    """
        Maintains notification of animation events to animation controllers.
    """
    __guid__ = 'svc.animationClient'
    __exportedcalls__ = {}
    __notifyevents__ = []
    __componentTypes__ = ['animation']

    def __init__(self):
        service.Service.__init__(self)
        self.registeredControllers = {}
        self.networkToController = {}
        self.audioCueFiles = {}

    def Run(self, *etc):
        self.AnimManager = GameWorld.GetAnimationManager()
        service.Service.Run(self)

    def _GetEntity(self, entid):
        """
        # For WoD this is actually the entity object.
        return self.gameComponentClient._GetEntityByID(entid)
        
        # For WiS this is an avatar object.
        avatar = self._GetEntity(avatarID)
        """
        raise StandardError('Not implemented')

    def GetEntityModel(self, entityID):
        """
        # WoD specific example implementation.
        return self.dollClient.GetAvatar(ent.entid)
        
        # WiS specific example implementation.
        --
        """
        raise StandardError('Not implemented')

    def _GetAnimationInfoService(self):
        """
        Pointer to a service with a GetAnimInfoByName() function
        that conforms to the animTemplate dict format.
        """
        raise StandardError('Not implemented')

    def _EntityNeedsToLineup(self, entity):
        """
        Condition hook to determine whether the entity needs to lineup before a synced animation.
        """
        raise StandardError('Not implemented')

    def _SetEntityMovement(self, ent, pos, rot, vel):
        """
        Force an entity to a specific position, rotation, and velocity (on the client).
        """
        raise StandardError('Not implemented')

    def _SwitchPlayerToDirectControlMode(self, force = False, remainingFacingAngle = 0.0):
        """
        Set the player into a move mode that allows him to control his character after being unlocked.
        """
        raise StandardError('Not implemented')

    def _ProcessMorphemeDiscreteEvent(self, animationController, animRef, eventUserData, trackUserData):
        """
            Implemented in subclasses, process event track data coming in from Morpheme for client-side processing.
        """
        raise StandardError('Not implemented')

    def _GetAudioCueFile(self, audioCueFilePath):
        """
        Load up the file containing associations between event track names and the audio cues they trigger.
        Maintains a cache of previously loaded files as well.
        """
        if audioCueFilePath not in self.audioCueFiles:
            animEventFile = blue.ResFile()
            animEventFile.Open(audioCueFilePath)
            self.audioCueFiles[audioCueFilePath] = yaml.load(animEventFile)
            animEventFile.close()
        return self.audioCueFiles[audioCueFilePath]

    def GetAnimationControllerFromNetwork(self, networkReference):
        return self.networkToController.get(networkReference, None)

    def RegisterAnimationController(self, animationController, audioCueFile = EVENT_TRACK_SOUND_LOOKUP_PATH):
        """
        Begin listening to an entity's animation events.
        """
        if audioCueFile is not None:
            self.registeredControllers[animationController] = audioCueFile
            self._GetAudioCueFile(audioCueFile)
        self.networkToController[animationController.animationNetwork] = animationController
        animationController.animationNetwork.SetOnDiscreteEventCallback(OnMorphemeDiscreteEvents)

    def UnregisterAnimationController(self, animationController):
        """
        Remove this animation controller from receiving updates.  Keep the audio cue file in the cache, however.  
        """
        animationController.Stop(None)
        if animationController in self.registeredControllers:
            del self.registeredControllers[animationController]
        if animationController.animationNetwork in self.networkToController:
            del self.networkToController[animationController.animationNetwork]

    def PackUpForSceneTransfer(self, component, destinationSceneID):
        state = {'updater': component.updater,
         'controller': component.controller,
         'poseState': component.poseState,
         'resPath': component.resPath}
        return state

    def UnPackFromSceneTransfer(self, component, entity, state):
        return component

    def CreateComponent(self, name, state):
        component = AnimationComponent()
        component.updater = state.get('updater')
        component.controller = state.get('controller')
        component.poseState = state.get('poseState')
        component.poseStateControlParms = state.get('poseStateControlParms')
        component.resPath = state.get('resPath')
        return component

    def PrepareComponent(self, sceneID, entityID, component):
        if entityID == session.charid:
            component.isClientPlayer = True
        if component.updater is None:
            component.updater = GameWorld.GWAnimation(None)
            component.updater.updateMode = 0
            component.updaterWaitingChannel = stackless.channel()

    def SetupComponent(self, entity, component):
        """
        Gets called once all components have been prepared.
        Use this to setup stuff which references other components
        """
        if not entity.HasComponent('movement'):
            self.LogError('Animation component is missing a sibling movement component on entity', entity.entityID, '. Will not setup')
            return
        if component.updater.network is None:
            if component.resPath is not None:
                component.updater.InitMorpheme(component.resPath)
            else:
                if not entity.HasComponent('info'):
                    self.LogError('Animation component is missing a sibling info component on entity', entity.entityID, '. Will not setup')
                    return
                self._InitializeAnimationNetwork(component, entity)
        else:
            component.poseState = None
            component.poseStateControlParms = None
        if component.updaterWaitingChannel:
            component.updaterWaitingChannel.send(None)
        if component.controller is None:
            if component.isClientPlayer == True:
                component.controller = PlayerAnimationController(component.updater.network)
            else:
                component.controller = BipedAnimationController(component.updater.network)
            component.updater.SetUpdateCallback(component.controller.Update)
        component.controller.entityRef = entity
        self._AnimationSetupHook(entity, component)
        component.updater.positionComponent = entity.GetComponent('position')
        self.AnimManager.AddEntity(entity.entityID, component.updater)

    def RegisterComponent(self, entity, component):
        """
            Gets called in order to register a component. The component can be searched for prior to this point.
        """
        if not component.controller:
            self.LogError('Animation component', entity.entityID, 'missing controller. Not registering.')
            return
        if component.poseStateControlParms is not None:
            for key, value in component.poseStateControlParms.iteritems():
                component.controller.SetControlParameter(key, float(value))

            component.poseStateControlParms = None
        if component.poseState is not None:
            component.updater.SetPoseByName(component.poseState)
            component.poseState = None

    def _AnimationSetupHook(self, entity, component):
        pass

    def _InitializeAnimationNetwork(self, component, entity):
        gender = entity.GetComponent('info').gender
        if gender:
            morphemePath = const.MALE_MORPHEME_PATH
        else:
            morphemePath = const.FEMALE_MORPHEME_PATH
        self._PrefetchAnimations(morphemePath)
        component.updater.InitMorpheme(morphemePath)

    def _PrefetchAnimations(self, morphemePath):
        """
        Prefetch the animations for the given .mor file
        """
        remotefilecache.prefetch_folder(os.path.dirname(morphemePath))

    def UnRegisterComponent(self, entity, component):
        self.AnimManager.RemoveEntity(entity.entityID, component.updater)
        self.UnregisterAnimationController(component.controller)
        component.updater = None
        component.controller.entityRef = None
        component.controller = None

    def TearDownComponent(self, entity, component):
        pass

    def ReportState(self, component, entity):
        report = collections.OrderedDict()
        if component.controller:
            report['Current LOD'] = component.controller.currentLOD
            report['Updated By'] = {0: 'GameWorld',
             1: 'Trinity'}[component.updater.updateMode]
        return report
