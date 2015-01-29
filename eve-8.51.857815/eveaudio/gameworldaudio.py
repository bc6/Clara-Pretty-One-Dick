#Embedded file name: eveaudio\gameworldaudio.py
import collections
import weakref
import audio
import audio2
import blue
try:
    import GameWorld
except NameError as ex:
    raise ImportError('GameWorld failed to import: %s' % str(ex))

import geo2
import uthread
DEFAULT_OBSTRUCTION_POLL_INTERVAL = 250
PAPERDOLL_SWITCH_GROUPS = ['Jacket', 'Pants', 'Boots']

class GameworldAudioMixin(object):
    """
    Functionality for the audio service that is only needed by Incarna.
    Moving this here so it doesn't clutter up AudioService,
    so we can refactor it easier (and then easily delete this class
    when Incarna is dead).
    """

    def __init__(self):
        self.audioEmitterComponentsByScene = collections.defaultdict(dict)
        self.audioEmitterPositionsByComponent = {}
        self.audioEmitterComponentGroupsByScene = collections.defaultdict(lambda : collections.defaultdict(list))
        self.obstructionPollThreadWR = None

    def StartPolling(self, pollInterval = DEFAULT_OBSTRUCTION_POLL_INTERVAL):
        if self.obstructionPollThreadWR and self.obstructionPollThreadWR():
            return
        pollingTasklet = uthread.new(self._PollAudioPositions, pollInterval)
        pollingTasklet.context = 'AudioService::_PollAudioPositions'
        self.obstructionPollThreadWR = weakref.ref(pollingTasklet)

    def StopPolling(self):
        if self.obstructionPollThreadWR and self.obstructionPollThreadWR():
            self.obstructionPollThreadWR().kill()
            self.obstructionPollThreadWR = None

    def _PollAudioPositions(self, pollInterval = DEFAULT_OBSTRUCTION_POLL_INTERVAL):
        entityClient = sm.GetService('entityClient')
        gameWorldClient = sm.GetService('gameWorldClient')
        while True:
            gameWorld = None
            playerPos = None
            sceneID = None
            player = entityClient.GetPlayerEntity()
            if player and player.HasComponent('position') and session.worldspaceid:
                playerPos = player.GetComponent('position').position
                gameWorld = gameWorldClient.GetGameWorld(session.worldspaceid)
                sceneID = player.scene.sceneID
            if playerPos and gameWorld and sceneID:
                audioEntities = set(self.audioEmitterPositionsByComponent.values()).intersection(self.audioEmitterComponentsByScene[sceneID].values())
                for audioEntity in audioEntities:
                    src = self.audioEmitterPositionsByComponent[audioEntity].position
                    p = None
                    if geo2.Vec3DistanceSq(src, playerPos) > 1e-05:
                        p = gameWorld.MultiHitLineTestWithMaterials(src, playerPos)
                    if p:
                        obstruction = len(p) * (1 / 5.0)
                        if obstruction > 1.0:
                            obstruction = 1.0
                        audioEntity.emitter.SetObstructionAndOcclusion(0, obstruction, 0.0)
                    else:
                        audioEntity.emitter.SetObstructionAndOcclusion(0, 0.0, 0.0)

            blue.pyos.synchro.SleepWallclock(pollInterval)

    def CreateComponent(self, name, state):
        component = audio.AudioEmitterComponent()
        component.initialEventName = state.get(audio.INITIAL_EVENT_NAME, None)
        component.initialSoundID = state.get(audio.INITIAL_SOUND_ID, None)
        component.groupName = state.get(audio.EMITTER_GROUP_NAME, None)
        if component.groupName == '':
            component.groupName = None
        component.emitter = None
        return component

    def PackUpForSceneTransfer(self, component, destinationSceneID):
        state = {}
        if component.initialEventName:
            state[audio.INITIAL_EVENT_NAME] = component.initialEventName
        if component.initialSoundID:
            state[audio.INITIAL_SOUND_ID] = component.initialSoundID
        if component.groupName:
            state[audio.EMITTER_GROUP_NAME] = component.groupName
        return True

    def UnPackFromSceneTransfer(self, component, entity, state):
        component.initialEventName = state.get(audio.INITIAL_EVENT_NAME, None)
        component.initialSoundID = state.get(audio.INITIAL_SOUND_ID, None)
        component.groupName = state.get(audio.EMITTER_GROUP_NAME, None)
        if component.groupName == '':
            component.groupName = None
        return component

    def SetupComponent(self, entity, component):
        self.audioEmitterComponentsByScene[entity.scene.sceneID][entity.entityID] = component
        component.positionObserver = None
        if component.groupName is None:
            component.emitter = audio2.AudEmitter('AudEmitter_' + str(entity.entityID))
            positionComponent = entity.GetComponent('position')
            if positionComponent:
                self.audioEmitterPositionsByComponent[component] = positionComponent
                component.positionObserver = GameWorld.PlacementObserverWrapper(component.emitter)
                positionComponent.RegisterPlacementObserverWrapper(component.positionObserver)
        else:
            groupedEntities = self.audioEmitterComponentGroupsByScene[entity.scene.sceneID][component.groupName]
            if len(groupedEntities) == 0:
                component.emitter = audio2.AudEmitterMulti('Multi_' + str(component.groupName))
                component.positionObserver = GameWorld.MultiPlacementObserverWrapper(component.emitter)
            else:
                component.emitter = groupedEntities[0].emitter
                component.positionObserver = groupedEntities[0].positionObserver
            groupedEntities.append(component)
            positionComponent = entity.GetComponent('position')
            if positionComponent:
                component.positionObserver.AddPositionComponent(positionComponent)
        if component.initialEventName:
            component.emitter.SendEvent(unicode(component.initialEventName))
        if component.initialSoundID:
            sound = cfg.sounds.GetIfExists(component.initialSoundID)
            if sound:
                component.emitter.SendEvent(unicode(sound.soundFile[6:]))

    def RegisterComponent(self, entity, component):
        paperdollComponent = entity.GetComponent('paperdoll')
        if paperdollComponent and paperdollComponent.doll and paperdollComponent.doll.GetDoll():

            def OnPaperdollUpdateDoneClosure():
                if component and paperdollComponent and paperdollComponent.doll:
                    self.UpdateComponentSwitchesWithDoll(component, paperdollComponent.doll)

            paperdollComponent.doll.GetDoll().AddUpdateDoneListener(OnPaperdollUpdateDoneClosure)

    def UpdateComponentSwitchesWithDoll(self, audioEmitter, doll):
        newSwitches = {}
        for switchGroup in PAPERDOLL_SWITCH_GROUPS:
            newSwitches[switchGroup] = 'None'

        for switchID in doll.GetDoll().buildDataManager.GetSoundTags():
            switch = cfg.sounds.GetIfExists(switchID)
            if switch and switch.soundFile.find('state:/') == 0:
                switchNames = switch.soundFile[7:].split('_')
                switchGroup = switchNames[0]
                switchType = switchNames[1]
                newSwitches[switchGroup] = switchType

        for switchGroup, switchType in newSwitches.iteritems():
            audioEmitter.emitter.SetSwitch(unicode(switchGroup), unicode(switchType))

    def UnRegisterComponent(self, entity, component):
        del self.audioEmitterComponentsByScene[entity.scene.sceneID][entity.entityID]
        if component in self.audioEmitterPositionsByComponent:
            del self.audioEmitterPositionsByComponent[component]
        if component.groupName is None:
            positionComponent = entity.GetComponent('position')
            if positionComponent and component.positionObserver:
                positionComponent.UnRegisterPlacementObserverWrapper(component.positionObserver)
            component.emitter.SendEvent(u'fade_out')
            component.emitter = None
        else:
            groupedEntities = self.audioEmitterComponentGroupsByScene[entity.scene.sceneID][component.groupName]
            if component in groupedEntities:
                groupedEntities.remove(component)
            if len(groupedEntities) == 0:
                positionComponent = entity.GetComponent('position')
                if positionComponent and component.positionObserver:
                    component.positionObserver.RemovePositionComponent(positionComponent)
                component.emitter.SendEvent(u'fade_out')
                component.emitter = None
                del self.audioEmitterComponentGroupsByScene[entity.scene.sceneID][component.groupName]

    def OnEntitySceneLoaded(self, sceneID):
        uthread.new(self.SetupPlayerListener)
        self.StartPolling()

    def SetupPlayerListener(self):
        camera = sm.GetService('cameraClient').GetActiveCamera()
        if camera:
            camera.audio2Listener = audio2.GetListener(0)

    def OnEntitySceneUnloaded(self, sceneID):
        for component in self.audioEmitterComponentsByScene[sceneID]:
            component.emitter.SendEvent(u'fade_out')
            component.emitter = None

        if sceneID in self.audioEmitterComponentGroupsByScene:
            del self.audioEmitterComponentGroupsByScene[sceneID]
        if sceneID in self.audioEmitterComponentsByScene:
            del self.audioEmitterComponentsByScene[sceneID]
        self.StopPolling()

    def ReportState(self, component, entity):
        state = collections.OrderedDict()
        state['Initial Sound ID'] = component.initialSoundID
        state['Initial Event Name'] = component.initialEventName
        state['Group Name'] = component.groupName
        return state
