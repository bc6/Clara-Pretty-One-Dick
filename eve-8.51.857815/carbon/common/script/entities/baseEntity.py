#Embedded file name: carbon/common/script/entities\baseEntity.py
import bluepy
import carbon.common.script.sys.service as service
import uthread
import locks
import collections
import log
import sys
import entityCommon
import GameWorld
import blue
import stackless

def BeCefNice(ms = 40):
    """
    Yields if frametime has exceeded the given ms and doesn't resume execution until
    we're at a time within a frame that is less than ms.
    However, the more we yield, the higher the ms value gets so the tasklet gets eventually its
    time to run, even on crapspec machines.
    """
    if ms < 1.0:
        ms = 1.0
    if not stackless.current.is_main:
        while blue.os.GetWallclockTimeNow() - blue.os.GetWallclockTime() > ms * 10000:
            stackless.main.run()
            ms *= 1.05


def CEFParellelHelper(func, args):
    BeCefNice()
    func(*args)


class Entity:
    """
    Base Entity Class.
    This class contains almost nothing on it's own but a list of components
    """
    __guid__ = 'entities.Entity'

    def __init__(self, scene, entityID):
        self.scene = scene
        self.entityID = entityID
        self.components = {}
        self.componentStates = {}
        self.state = const.cef.ENTITY_STATE_UNINITIALIZED
        self.entityLock = uthread.CriticalSection()

    def AddComponent(self, name, component):
        """
        Add the specified component to the entity.
        """
        if name in self.components:
            msg = ('Adding a component:',
             name,
             "that's already on the entity:",
             self.entityID,
             ' Old component will be replaced')
            self.scene.service.LogError('Adding a component:', name, "that's already on the entity:", self.entityID, ' Old component will be replaced')
        if component is not None:
            self.components[name] = component
        else:
            log.LogWarn('Unable to add component', name, 'to entity', self.entityID)

    def HasComponent(self, name):
        """
        Returns if the named component exists withing the entity
        """
        return name in self.components

    def GetComponent(self, name):
        """
        Returns a component of the given type. Return None if it does not exists
        """
        return self.components.get(name, None)

    def GetComponents(self):
        """
        Returns the components dictionary
        """
        return self.components

    def AddComponentState(self, name, state):
        """
        Add the specified component state to the entity. These are the state of
        components that get transferred around but aren't created in this scene
        but potentially are when transferred (if the component exists).
        """
        if name in self.componentStates:
            msg = ('Adding a component state:',
             name,
             "that's already on the a entity:",
             self.entityID,
             ' Old component state will be replaced')
            self.scene.service.LogError('Adding a component state:', name, "that's already on the a entity:", self.entityID, ' Old component state will be replaced')
        self.componentStates[name] = state

    def __getattr__(self, attr):
        """
        Makes the dot operator look up first in the components dict
        That way you can access the components via entity.component
        """
        if self.components.has_key(attr):
            return self.components[attr]
        if self.__dict__.has_key(attr):
            return self.__dict__[attr]
        raise AttributeError(attr)

    def __repr__(self):
        return '<Entity id:%s state:%s sceneid:%s components:%s objectID:%s>' % (self.entityID,
         self.state,
         self.scene.sceneID,
         len(self.components),
         id(self))

    def __str__(self):
        return self.__repr__()


class EntitySceneState:
    UNINITIALIZED = 0
    LOADING = 1
    READY = 2
    UNLOADING = 3


class EventQueue(object):

    def __init__(self, emptyEvent = None):
        self._task = None
        self._queue = collections.deque()
        self._emptyEvent = emptyEvent

    def AddEvent(self, event, *args):
        semaphore = locks.Event('event_%s' % event)
        self._queue.append((event, args, semaphore))
        return semaphore

    def StartEvents(self):
        if self._task is None:
            self._task = uthread.new(self._PumpEvent)
            self._task.context = 'EventQueue update'

    def GetLastSemaphore(self):
        try:
            event, args, semaphore = self._queue[-1]
            return semaphore
        except:
            log.LogError('Missing semaphore')
            return None

    def _ProcessEvent(self, semaphore, event, *args):
        try:
            event(*args)
        except:
            log.LogException()
        finally:
            semaphore.set()

    def _PumpEvent(self):
        while len(self._queue) > 0:
            BeCefNice()
            event, args, semaphore = self._queue[0]
            self._ProcessEvent(semaphore, event, *args)
            self._queue.popleft()

        self._task = None
        if self._emptyEvent is not None:
            self._emptyEvent()


class BaseEntityScene(object):
    __guid__ = 'entities.BaseEntityScene'
    __exportedcalls__ = {'ReceiveRemoteEntity': {'role': service.ROLE_SERVICE}}

    def __init__(self, broker, sceneID):
        self.state = EntitySceneState.UNINITIALIZED
        self.sceneID = sceneID
        self.entities = {}
        self.broker = broker
        self.eventQueue = EventQueue()
        self._entityList = {}
        self._startupEntities = []

    def IsUnloading(self):
        return self.state == EntitySceneState.UNLOADING

    def _LoadScene(self, semaphore):
        self.broker.LogInfo('Asynch scene load started for scene', self.sceneID)
        if semaphore is not None:
            self.broker.LogError('Scene load waiting for previous unload for scene', self.sceneID)
            semaphore.wait()
        self.state = EntitySceneState.LOADING
        self.broker.LogInfo('Scene load starting registration for scene', self.sceneID)
        self.broker._RegisterScene(self, self.loadSemaphore)
        self._startupEntities = self._entityList.keys()
        self.broker.LogInfo('Asynch scene load finished for scene', self.sceneID)

    def _UnloadScene(self):
        self.broker.LogInfo('Asynch scene unload started for scene', self.sceneID)
        self.state = EntitySceneState.UNLOADING
        self.broker.LogInfo('Scene unload starting unregistration for scene', self.sceneID)
        self.broker._UnregisterScene(self)
        semaphores = []
        for entityID in self._entityList.iterkeys():
            queue = self.broker._entityQueues.get(entityID, None)
            if queue is not None:
                semaphore = queue.GetLastSemaphore()
                if semaphore is not None:
                    semaphores.append(semaphore)

        for semaphore in semaphores:
            semaphore.wait()

        semaphores = []
        for entity in self.entities.itervalues():
            semaphores.append(self.UnregisterAndDestroyEntity(entity))

        for semaphore in semaphores:
            semaphore.wait()

        self.broker.LogInfo('Scene unload starting TearDown for scene', self.sceneID)
        self.broker._TearDownScene(self)
        self.broker.LogInfo('Asynch scene unload finished for scene', self.sceneID)

    def LoadScene(self, scene):
        semaphore = None
        if scene is not None:
            self.broker.LogError('Scene', self.sceneID, 'waiting for unload of the same scene')
            semaphore = scene.eventQueue.GetLastSemaphore()
            if semaphore is None:
                self.broker.LogError('OMG predcessor scene has no semaphore ', self.sceneID)
        self.loadSemaphore = self.eventQueue.AddEvent(self._LoadScene, semaphore)
        self.eventQueue.StartEvents()
        return self.loadSemaphore

    def UnloadScene(self):
        semaphore = self.eventQueue.AddEvent(self._UnloadScene)
        self.eventQueue.StartEvents()
        return semaphore

    def WaitOnStartupEntities(self):
        if self._startupEntities is not None:
            self.broker.LogInfo('Waiting on startup entities for scene', self.sceneID)
            self.broker.LogInfo('The pending entity IDs are', self._startupEntities)
            for entID in self._startupEntities:
                self.broker.WaitOnEntityEvents(entID)

            self.broker.LogInfo('Done Waiting on startup entities for scene', self.sceneID)
            self._startupEntities = None
            self.broker.LogInfo('Finished waiting on startup entities for scene', self.sceneID)

    def CreateEntity(self, entity, initData = None):
        self._entityList[entity.entityID] = entity
        channel = self.broker._AddEvent(entity.entityID, self.broker._CreateEntity, entity, self.loadSemaphore, initData)
        self.broker._StartEvents(entity.entityID)
        return channel

    def RegisterEntity(self, entity, initData = None):
        channel = self.broker._AddEvent(entity.entityID, self.broker._RegisterEntity, entity, initData)
        self.broker._StartEvents(entity.entityID)
        return channel

    def UpdateEntity(self, entity, updateData = None):
        channel = self.broker._AddEvent(entity.entityID, self.broker._UpdateEntity, entity, updateData)
        self.broker._StartEvents(entity.entityID)
        return channel

    def UnregisterEntity(self, entity):
        channel = self.broker._AddEvent(entity.entityID, self.broker._UnregisterEntity, entity)
        self.broker._StartEvents(entity.entityID)
        return channel

    def DestroyEntity(self, entity):
        del self._entityList[entity.entityID]
        channel = self.broker._AddEvent(entity.entityID, self.broker._DestroyEntity, entity)
        self.broker._StartEvents(entity.entityID)
        return channel

    def CreateAndRegisterEntity(self, entity, initData = None):
        self._entityList[entity.entityID] = entity
        channel = self.broker._AddEvent(entity.entityID, self.broker._CreateEntityAndRegister, entity, self.loadSemaphore, initData)
        self.broker._StartEvents(entity.entityID)
        return channel

    def UnregisterAndDestroyEntity(self, entity):
        del self._entityList[entity.entityID]
        self.broker._AddEvent(entity.entityID, self.broker._UnregisterEntity, entity)
        channel = self.broker._AddEvent(entity.entityID, self.broker._DestroyEntity, entity)
        self.broker._StartEvents(entity.entityID)
        return channel

    def AddEntityToRegisteredList(self, entity):
        """
        """
        self.entities[entity.entityID] = entity

    def RemoveEntityFromRegisteredList(self, entity):
        """
        Takes care of un registering this entities components with the interested systems and
        removing the entity
        """
        del self.entities[entity.entityID]

    def GetAllEntityIds(self):
        return self.entities.keys()

    def ReceiveRemoteEntity(self, fromSceneID, entityID, packedState):
        """
        Receive remote entity and wait for it to be created.
        """
        semaphore = self.broker.ReceiveRemoteEntity(fromSceneID, entityID, self.sceneID, packedState)
        semaphore.wait()


class BaseEntityService(service.Service):
    __guid__ = 'svc.BaseEntityService'
    __exportedcalls__ = {'ReceiveRemoteEntity': {'role': service.ROLE_ANY}}
    __entitySceneType__ = None
    __entitysystems__ = []

    def __init__(self):
        service.Service.__init__(self)
        self.scenes = {}
        self.loadingScenes = {}
        self.unloadingScenes = {}
        self.loadingEntities = {}
        self.entityLocks = {}
        self.entityDestoryLocks = {}
        self.componentSystems = collections.defaultdict(set)
        self.componentFactories = {}
        self.sceneCreationSubscriptions = set()
        self._deadEntityList = {}
        self._entityQueues = {}
        self._entityProcessing = {}

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.entitySceneManager = GameWorld.GetEntitySceneManagerSingleton()
        self.sceneManager = GameWorld.GetSceneManagerSingleton()
        calls = []
        for entitySystem in set(self.__entitysystems__):
            calls.append((self.SetupEntitySystem, (entitySystem,)))

        try:
            uthread.parallel(calls)
        except:
            log.LogException()

    def SetupEntitySystem(self, entitySystem):
        system = sm.GetService(entitySystem)
        system.entityService = self
        self.RegisterForSceneLifeCycle(system)
        for componentType in getattr(system, '__componentTypes__', []):
            if hasattr(system, 'CreateComponent'):
                self.RegisterComponentFactory(componentType, system)
            self.RegisterForComponentType(componentType, system)

    def IsClientSideOnly(self, sceneID):
        """
        Default CEF is all networked. Override this with criterias for client side only scenes in your game
        """
        return False

    def LoadEntityScene(self, sceneID):
        """
        Load the scene by id. This will spin off a new tasklet to handle the load. 
        """
        if sceneID in self.scenes:
            return self.scenes[sceneID]
        scene = self.__entitySceneType__(self, sceneID)
        self.scenes[sceneID] = scene
        self.loadingScenes[sceneID] = scene.LoadScene(self.unloadingScenes.get(sceneID, None))
        return scene

    def LoadEntitySceneAndBlock(self, sceneID):
        """
        Load the scene by id. This will spin off a new tasklet to handle the load. 
        """
        self.LogInfo('Getting entity scene', sceneID)
        if sceneID in self.loadingScenes:
            self.LogInfo('Waiting for entity scene', sceneID, ' thats currently loading')
            self.loadingScenes[sceneID].wait()
            self.LogInfo('Done waiting for entity scene', sceneID, ' that just finished loading')
        if sceneID not in self.scenes:
            self.LogInfo('Starting to load up entity scene ', sceneID)
            self.LoadEntityScene(sceneID)
            self.loadingScenes[sceneID].wait()
            self.LogInfo('Done waiting for entity scene', sceneID, ' that just finished loading')
        return self.scenes[sceneID]

    def WaitForEntityScene(self, sceneID):
        """
        Waits till entity scene is in ready state.
        """
        if sceneID in self.loadingScenes:
            self.LogInfo('Waiting for entity scene', sceneID, ' thats currently loading')
            self.loadingScenes[sceneID].wait()
            self.LogInfo('Done waiting for entity scene', sceneID, ' that just finished loading')

    def UnloadEntityScene(self, sceneID):
        """
        Unload the scene by id. This will spin off a new tasklet to handle the unload. 
        """
        self.LogInfo('Unloading entity scene', sceneID)
        scene = self.scenes.get(sceneID, None)
        if scene is None:
            self.LogWarn("Requesting unload of entity scene I don't have")
            return
        self.LogInfo('Removing Scene reference for scene', sceneID)
        del self.scenes[sceneID]
        if sceneID in self.loadingScenes:
            del self.loadingScenes[sceneID]
        self.unloadingScenes[sceneID] = scene
        return scene.UnloadScene()

    def GetEntityScene(self, sceneID):
        return self.scenes.get(sceneID, None)

    def GetEntitySceneIDs(self):
        return self.scenes.keys()

    def RegisterForSceneLifeCycle(self, system):
        """
        Registers the given system for notifications about scene setup and teardown
        Allows the system to setup system wide stuff on the scene 
        """
        self.sceneCreationSubscriptions.add(system)
        self.LogInfo('Registered', system, ' for lifecycle')

    def _RegisterScene(self, scene, loadSemaphore):
        sceneID = scene.sceneID
        self.LogInfo('Registering entity scene ', sceneID)
        self.sceneManager.AddScene(scene.sceneID)

        def LogCall(callName, systemName, call, args):
            self.LogInfo(callName, 'start for', systemName)
            call(*args)
            self.LogInfo(callName, 'end for', systemName)

        registrationCalls = []
        for system in self.sceneCreationSubscriptions:
            if hasattr(system, 'OnLoadEntityScene'):
                registrationCalls.append((LogCall, ('OnLoadEntityScene',
                  system.__guid__,
                  system.OnLoadEntityScene,
                  (sceneID,))))

        try:
            uthread.parallel(registrationCalls)
        except:
            log.LogException()

        self.LogInfo('Calling OnEntitySceneLoaded ', sceneID)
        sceneLoadedCalls = []
        for system in self.sceneCreationSubscriptions:
            if hasattr(system, 'OnEntitySceneLoaded'):
                sceneLoadedCalls.append((LogCall, ('OnEntitySceneLoaded',
                  system.__guid__,
                  system.OnEntitySceneLoaded,
                  (sceneID,))))

        try:
            uthread.parallel(sceneLoadedCalls)
        except:
            log.LogException()

        scene.state = EntitySceneState.READY
        if self.loadingScenes.get(scene.sceneID) == loadSemaphore:
            del self.loadingScenes[scene.sceneID]
        self.LogInfo('Finished loading entity scene ', sceneID)

    def _UnregisterScene(self, scene):
        scene.state = EntitySceneState.UNLOADING
        self.LogInfo('Unloading entity Scene', scene.sceneID)
        sm.ChainEvent('ProcessEntitySceneUnloading', scene.sceneID)

    def _TearDownScene(self, scene):
        self.LogInfo('Tearing Down entity Scene', scene.sceneID)
        unloadCalls = []
        for system in self.sceneCreationSubscriptions:
            if hasattr(system, 'OnUnloadEntityScene'):
                unloadCalls.append((system.OnUnloadEntityScene, (scene.sceneID,)))

        self.LogInfo('Unloading Entity Scene from', len(unloadCalls), 'systems')
        try:
            uthread.parallel(unloadCalls)
            self.LogInfo('Done unloading Entity Scene from', len(unloadCalls), 'systems')
        except:
            log.LogException()
            self.LogWarn('Done unloading Entity Scene, but something threw an exception. Trying to continue execution.')

        unloadedCalls = []
        for system in self.sceneCreationSubscriptions:
            if hasattr(system, 'OnEntitySceneUnloaded'):
                unloadedCalls.append((system.OnEntitySceneUnloaded, (scene.sceneID,)))

        self.LogInfo('Notifying', len(unloadedCalls), 'systems about Entity Scene having been unloaded')
        try:
            uthread.parallel(unloadedCalls)
            self.LogInfo('Done notifying about successful unload')
        except:
            log.LogException()
            self.LogWarn('Done notifying about unload, but something errored. Trying to continue execution.')

        self.sceneManager.RemoveScene(scene.sceneID)
        del self.unloadingScenes[scene.sceneID]
        self.LogInfo('Done Unloading entity Scene', scene.sceneID)

    def CreateComponent(self, name, state):
        factory = self.componentFactories.get(name, None)
        if factory is not None:
            component = factory.CreateComponent(name, state)
            if component is None:
                self.LogInfo('Factory returned None for component: ', name)
            return component

    def GetComponentSystems(self, componentType):
        """
        Returns a list of system which have registered to get notified about the creation/deletion
        of the specified component type.
        Systems can register using the RegisterForComponentType function.
        """
        return self.componentSystems[componentType]

    def RegisterForComponentType(self, componentType, system):
        """
        Registers the system to be notified about the creation/deletion of the given component type
        """
        self.componentSystems[componentType].add(system)
        self.LogInfo('Registered', system, 'for components of type', componentType)

    def RegisterComponentFactory(self, componentType, factory):
        """
        Registers the factory as the factory for a given component type
        The Factory needs to implment the CreateComponent method
        """
        self.componentFactories[componentType] = factory
        self.LogInfo('Registered', factory, 'as factory for components of type', componentType)

    def GetComponentState(self, entity, componentName):
        """
        Returns the state dictionary for the given component on specified entity.
        Returns None if no such entity exists or the component's factory does not
        implement the ReportState interface.
        """
        try:
            ret = None
            factory = self.componentFactories[componentName]
            component = entity.components[componentName]
            ret = factory.ReportState(component, entity)
        except (KeyError, AttributeError):
            log.LogException()
            sys.exc_clear()
        finally:
            return ret

    def GetComponentStateByID(self, entityID, componentName):
        """
        Returns the state dictionary for the given component on specified entity.
        Returns None if no such entity exists or the component's factory does not
        implement the ReportState interface.
        """
        entity = self.FindEntityByID(entityID)
        return self.GetComponentState(entity, componentName)

    def _SetupComponents(self, entity, initData = None):
        """
        Called when all the components have been added to the entity for creation
        """
        entityAlreadyThere = entity.scene.entities.get(entity.entityID, None)
        if entityAlreadyThere:
            if session.charid and entity.entityID == session.charid:
                self.LogInfo('Double add of player entity because of playercomponent ack stuff')
            else:
                errorText = 'Adding a entity ' + str(entity) + ' that already in this scene. This one was here before ' + str(entityAlreadyThere) + ' Ignoring entity'
                log.LogTraceback(extraText=errorText)
            GameWorld.GetNetworkEntityQueueManager().ClearEntity(entity.entityID)
            return False
        with entity.entityLock:
            try:
                if entity.state == const.cef.ENTITY_STATE_UNINITIALIZED:
                    self.loadingEntities[entity.entityID] = entity
                    entity.state = const.cef.ENTITY_STATE_CREATING
                    self.entitySceneManager.Prepare(entity.entityID, entity.scene.sceneID)
                    preperationCalls = []
                    funcContexts = []
                    for name, component in entity.components.iteritems():
                        systems = self.GetComponentSystems(name)
                        if systems:
                            for system in systems:
                                f = getattr(system, 'PrepareComponent', None)
                                if f:
                                    preperationCalls.append((CEFParellelHelper, (f, (entity.scene.sceneID, entity.entityID, component))))
                                    funcContexts.append(system.__guid__)

                    if preperationCalls:
                        uthread.parallel(preperationCalls, contextSuffix='PrepareComponent', funcContextSuffixes=funcContexts)
                    setupCalls = []
                    funcContexts = []
                    for name, component in entity.components.iteritems():
                        systems = self.GetComponentSystems(name)
                        if systems:
                            for system in systems:
                                f = getattr(system, 'SetupComponent', None)
                                if f:
                                    setupCalls.append((CEFParellelHelper, (f, (entity, component))))
                                    funcContexts.append(system.__guid__)

                    if setupCalls:
                        uthread.parallel(setupCalls, contextSuffix='SetupComponent', funcContextSuffixes=funcContexts)
                    setupCalls = []
                    funcContexts = []
                    for name, component in entity.components.iteritems():
                        systems = self.GetComponentSystems(name)
                        if systems:
                            for system in systems:
                                f = getattr(system, 'NetworkSyncComponent', None)
                                if f:
                                    setupCalls.append((CEFParellelHelper, (f, (entity, component))))
                                    funcContexts.append(system.__guid__)

                    if setupCalls:
                        uthread.parallel(setupCalls, contextSuffix='NetworkSyncComponent', funcContextSuffixes=funcContexts)
                    entity.scene.entities[entity.entityID] = entity
                else:
                    self.LogError('SetupComponents: Entity state should be', const.cef.ENTITY_STATE_NAMES[const.cef.ENTITY_STATE_UNINITIALIZED], ', is instead ', const.cef.ENTITY_STATE_NAMES[entity.state], '. Entity is:', str(entity))
            except Exception as e:
                self._deadEntityList[entity.entityID] = entity
                log.LogException(e)
                return False

        return True

    def _RegisterComponents(self, entity, initData = None):
        """
        Called when the entity is registered with a scene
        """
        with uthread.BlockTrapSection():
            with entity.entityLock:
                try:
                    if entity.state == const.cef.ENTITY_STATE_CREATING:
                        entity.state = const.cef.ENTITY_STATE_READY
                        entity.scene.AddEntityToRegisteredList(entity)
                        registerCalls = []
                        for name, component in entity.components.iteritems():
                            systems = self.GetComponentSystems(name)
                            if systems:
                                for system in systems:
                                    f = getattr(system, 'RegisterComponent', None)
                                    if f:
                                        registerCalls.append((f, (entity, component)))

                        if registerCalls:
                            for f, args in registerCalls:
                                f(*args)

                        del self.loadingEntities[entity.entityID]
                    elif entity.state in (const.cef.ENTITY_STATE_UNINITIALIZED, const.cef.ENTITY_STATE_DEAD, const.cef.ENTITY_STATE_READY):
                        self.LogError('RegisterComponents: Entity state should be either', const.cef.ENTITY_STATE_NAMES[const.cef.ENTITY_STATE_CREATING], 'or', const.cef.ENTITY_STATE_NAMES[const.cef.ENTITY_STATE_DESTROYING], ', is instead', const.cef.ENTITY_STATE_NAMES[entity.state], '. Entity:', str(entity))
                    sm.ScatterEvent('OnEntityCreated', entity.entityID)
                    GameWorld.GetNetworkEntityQueueManager().ClearEntity(entity.entityID)
                except Exception as e:
                    log.LogException(e)
                    self._deadEntityList[entity.entityID] = entity
                    if entity.scene and entity.entityID in entity.scene.entities:
                        del entity.scene.entities[entity.entityID]
                        self.entitySceneManager.Unregister(entity.entityID)

    def _UnRegisterComponents(self, entity):
        """
        Called when the entity is unregistered with a scene
        """
        with uthread.BlockTrapSection():
            with entity.entityLock:
                try:
                    if entity.state == const.cef.ENTITY_STATE_READY:
                        registerCalls = []
                        for name, component in entity.components.iteritems():
                            systems = self.GetComponentSystems(name)
                            if systems:
                                for system in systems:
                                    f = getattr(system, 'UnRegisterComponent', None)
                                    if f:
                                        registerCalls.append((f, (entity, component)))

                        if registerCalls:
                            for f, args in registerCalls:
                                try:
                                    f(*args)
                                except Exception as e:
                                    self._deadEntityList[entity.entityID] = entity
                                    log.LogException(e)

                    elif entity.state in (const.cef.ENTITY_STATE_UNINITIALIZED, const.cef.ENTITY_STATE_DEAD, const.cef.ENTITY_STATE_DESTROYING):
                        self.LogError('UnRegisterComponents: Entity state should be either ', const.cef.ENTITY_STATE_NAMES[const.cef.ENTITY_STATE_CREATING], ' or ', const.cef.ENTITY_STATE_NAMES[const.cef.ENTITY_STATE_READY], ', is instead ', const.cef.ENTITY_STATE_NAMES[entity.state], '. Entity:', str(entity))
                    entity.scene.RemoveEntityFromRegisteredList(entity)
                    self.entitySceneManager.Unregister(entity.entityID)
                    entity.state = const.cef.ENTITY_STATE_DESTROYING
                except Exception as e:
                    self._deadEntityList[entity.entityID] = entity
                    if entity.scene and entity.entityID in entity.scene.entities:
                        del entity.scene.entities[entity.entityID]
                        self.entitySceneManager.Unregister(entity.entityID)
                    log.LogException(e)

    def _TearDownComponents(self, entity):
        """
        Tells each of the systems that it should tear down the component in its internal view
        """
        with entity.entityLock:
            try:
                if entity.state == const.cef.ENTITY_STATE_DESTROYING:
                    entity.state = const.cef.ENTITY_STATE_DEAD
                    preTearDownCalls = []
                    for name, component in entity.components.iteritems():
                        systems = self.GetComponentSystems(name)
                        if systems:
                            for system in systems:
                                f = getattr(system, 'PreTearDownComponent', None)
                                if f:
                                    preTearDownCalls.append((f, (entity, component)))

                    if preTearDownCalls:
                        uthread.parallel(preTearDownCalls)
                    tearDownCalls = []
                    for name, component in entity.components.iteritems():
                        systems = self.GetComponentSystems(name)
                        if systems:
                            for system in systems:
                                f = getattr(system, 'TearDownComponent', None)
                                if f:
                                    tearDownCalls.append((f, (entity, component)))

                    if tearDownCalls:
                        uthread.parallel(tearDownCalls)
                else:
                    self.LogError('SetupComponents: Entity state should be ', const.cef.ENTITY_STATE_NAMES[const.cef.ENTITY_STATE_DESTROYING], ', is instead ', const.cef.ENTITY_STATE_NAMES[entity.state], '. Entity:', str(entity))
                sm.ScatterEvent('OnEntityDeleted', entity.entityID, entity.scene.sceneID)
                GameWorld.GetNetworkEntityQueueManager().RemoveEntity(entity.entityID)
            except Exception as e:
                self._deadEntityList[entity.entityID] = entity
                log.LogException(e)

    def CreateEntityFromRecipe(self, scene, recipe, entityItemID):
        newEntity = Entity(scene, entityItemID)
        for componentID, initValues in recipe.iteritems():
            componentName = entityCommon.GetComponentName(componentID)
            component = self.CreateComponent(componentName, initValues)
            if component is not None:
                newEntity.AddComponent(componentName, component)
            else:
                newEntity.AddComponentState(componentName, initValues)

        return newEntity

    def CreateEntity(self, scene, entityID):
        """
        This is currently used for unit tests.
        """
        newEntity = Entity(scene, entityID)
        return newEntity

    def UnregisterAndDestroyEntityByID(self, entityID):
        for scene in self.scenes.itervalues():
            if entityID in scene._entityList:
                return scene.UnregisterAndDestroyEntity(scene._entityList[entityID])

        self.LogError("Attempting to destroy entity %s that doesn't exist even in the queue" % entityID)

    def ReceiveRemoteEntity(self, fromSceneID, entityID, sceneID, packedState):
        """
        Recieves an entity from another scene and creates it in this one
        It can be receiving it from another machonet node or the same one
        """
        GameWorld.GetNetworkEntityQueueManager().AddEntity(entityID)
        scene = self.GetEntityScene(sceneID)
        entity = Entity(scene, entityID)
        for componentName, state in packedState.iteritems():
            componentFactory = self.componentFactories.get(componentName, None)
            if componentFactory:
                component = componentFactory.CreateComponent(componentName, state)
                component = componentFactory.UnPackFromSceneTransfer(component, entity, state)
                entity.AddComponent(componentName, component)
            else:
                entity.AddComponentState(componentName, state)

        return scene.CreateAndRegisterEntity(entity)

    def FindEntityByID(self, entityID):
        """
        Returns a entity by entityID if we know about it in any of the entity scene we have loaded
        """
        with bluepy.Timer('EntityService::FindEntityByID'):
            for scene in self.scenes.itervalues():
                entity = scene.entities.get(entityID, None)
                if entity is not None:
                    return entity

            return

    def DestroyEntityByID(self, entid):
        entity = self.FindEntityByID(entid)
        if entity is not None:
            self.DestroyEntity(entity)

    def DestroyEntity(self, entity):
        if entity is not None:
            entity.scene.UnregisterAndDestroyEntity(entity)

    def GetEntityIdsInScene(self, sceneID):
        """
        Returns a list of all entity ids in the requested scene.
        """
        if sceneID in self.scenes:
            return self.scenes[sceneID].GetAllEntityIds()

    def GetEntityState(self, entity):
        """
        Returns the state dictionary for all components on the specified entity.
        Returns None if no such entity exists.
        """
        ret = {}
        components = entity.components
        for name, component in components.iteritems():
            try:
                factory = self.componentFactories[name]
                state = factory.ReportState(component, entity)
                if state is not None:
                    ret[name] = state
            except (KeyError, AttributeError):
                self.LogWarn('Component', name, 'I either have no factory or the factory does not report state.')
                sys.exc_clear()

        return ret

    def GetEntityStateByID(self, entityID):
        """
        Returns the state dictionary for all components on the specified entity.
        Returns None if no such entity exists.
        """
        entity = self.FindEntityByID(entityID)
        return self.GetEntityState(entity)

    def WaitOnEntityEvents(self, entityID):
        """
        Waits on the specified entityID event queue to be empty
        """
        eventQueue = self._entityQueues.get(entityID, None)
        while eventQueue is not None:
            eventQueue.GetLastSemaphore().wait()
            eventQueue = self._entityQueues.get(entityID, None)

    def _CreateEntity(self, entity, loadSemaphore, initData):
        if loadSemaphore is not None:
            loadSemaphore.wait()
        with bluepy.Timer('EntityService::_SetupComponents'):
            self._SetupComponents(entity, initData)

    def _CreateEntityAndRegister(self, entity, loadSemaphore, initData):
        with bluepy.Timer('EntityService::_CreateEntityAndRegister'):
            if loadSemaphore is not None:
                loadSemaphore.wait()
            createSuccess = self._SetupComponents(entity, initData)
            if createSuccess:
                self._RegisterEntity(entity, initData)

    def _RegisterEntity(self, entity, initData):
        self._RegisterComponents(entity, initData)

    def _UpdateEntity(self, entity, updateData):
        pass

    def _UnregisterEntity(self, entity):
        self._UnRegisterComponents(entity)

    def _DestroyEntity(self, entity):
        self._TearDownComponents(entity)
        entity.scene = None

    def _AddEvent(self, entityID, event, *args):
        queue = self._entityQueues.setdefault(entityID, EventQueue(lambda : self._RemoveEntityQueue(entityID)))
        return queue.AddEvent(event, *args)

    def _StartEvents(self, entityID):
        queue = self._entityQueues[entityID]
        queue.StartEvents()

    def _RemoveEntityQueue(self, entityID):
        del self._entityQueues[entityID]
