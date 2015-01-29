#Embedded file name: carbon/client/script/entities\entityClient.py
import locks
import entities
from carbon.common.script.entities.baseEntity import BaseEntityService
import util
import weakref
import GameWorld

class ClientEntityScene(entities.BaseEntityScene):
    __guid__ = 'entities.ClientEntityScene'

    def __init__(self, broker, sceneID):
        entities.BaseEntityScene.__init__(self, broker, sceneID)
        self.broker.LogInfo('Creating new ClientEntityScene', sceneID)

    def AddEntityToRegisteredList(self, entity):
        """
        Overrides to check if the entity added is the player entity
        """
        super(type(self), self).AddEntityToRegisteredList(entity)
        if entity.entityID == session.charid:
            self.broker.LogInfo('Setting player character')
            self.broker.SetPlayerEntity(entity)

    def RemoveEntityFromRegisteredList(self, entity):
        super(type(self), self).RemoveEntityFromRegisteredList(entity)
        if entity.entityID == session.charid:
            self.broker.LogInfo('Clearing player character')
            self.broker.SetPlayerEntity(None)


class EntityClient(BaseEntityService):
    __guid__ = 'svc.entityClient'
    __dependencies__ = []
    __notifyevents__ = []
    __entitySceneType__ = ClientEntityScene
    __entitysystems__ = ['simpleStaticSpawnClient',
     'actionObjectClientSvc',
     'aimingClient',
     'animationClient',
     'apertureClient',
     'boundingVolume',
     'boxLightClient',
     'collisionMeshClient',
     'decisionTreeClient',
     'directionalLightClient',
     'entityProcSvc',
     'entitySpawnClient',
     'gameWorldClient',
     'graphicClient',
     'interiorPlaceableClient',
     'interiorStaticClient',
     'lensFlareClient',
     'loadedLightClient',
     'movementClient',
     'occluderClient',
     'paperDollClient',
     'particleObjectClient',
     'perceptionClient',
     'physicalPortalClient',
     'playerComponentClient',
     'pointLightClient',
     'position',
     'proximity',
     'simpleTestClient',
     'spotLightClient',
     'UIDesktopComponentManager',
     'worldSpaceClient',
     'zactionClient',
     'LightAnimationComponentManager',
     'highlightClient',
     'genericProcClient',
     'uvPickingClient',
     'cameraClient',
     'uiProcSvc',
     'cylinderLightClient']

    def __init__(self):
        BaseEntityService.__init__(self)
        self.playerEntity = None
        self.playerEntityLoaded = locks.Event('playerEntityLoaded')

    def Run(self, *etc):
        BaseEntityService.Run(self, *etc)
        self.remoteEntityScenes = {}
        self.RegisterForSceneLifeCycle(self)

    def OnLoadEntityScene(self, sceneID):
        if self.IsClientSideOnly(sceneID):
            return
        if sceneID not in self.remoteEntityScenes:
            remoteScene = util.Moniker('entityServer', sceneID)
            remoteScene.Bind()
            self.remoteEntityScenes[sceneID] = remoteScene

    def OnEntitySceneUnloaded(self, sceneID):
        if sceneID in self.remoteEntityScenes:
            remoteScene = self.remoteEntityScenes.pop(sceneID)

    def CreateEntityFromServer(self, entityID, sceneID, initialComponentStates):
        """
        Takes care creating the entity based on the InitialComponent states recieved from the server
        """
        self.LogInfo('EntityClient creating server entity: ', entityID, 'with initial state:')
        self.LogInfo(initialComponentStates)
        GameWorld.GetNetworkEntityQueueManager().AddEntity(entityID)
        scene = self.LoadEntitySceneAndBlock(sceneID)
        scene.WaitOnStartupEntities()
        entity = entities.Entity(scene, entityID)
        for name, state in initialComponentStates.iteritems():
            componentFactory = self.componentFactories.get(name, None)
            if componentFactory:
                component = componentFactory.CreateComponent(name, state)
                entity.AddComponent(name, component)
            else:
                self.LogWarn("I don't have a componentFactory for:", name, 'but I have these', ', '.join(self.__entitysystems__))

        self.LogInfo('ClientEntityScene adding server entity: ', entity)
        scene.CreateAndRegisterEntity(entity)

    def GetPlayerEntity(self, canBlock = False):
        """
        Returns the current player entity
        """
        if canBlock:
            if self.playerEntity is None:
                self.LogInfo('Waiting for playering entity...')
                self.playerEntityLoaded.wait()
                self.LogInfo('Done waiting for playering entity')
        return self.playerEntity

    def SetPlayerEntity(self, entity):
        """
        Sets the current player entity
        """
        if entity:
            self.playerEntity = weakref.proxy(entity)
            self.LogInfo('Received player entity')
            self.playerEntityLoaded.set()
        else:
            self.playerEntity = None
            self.LogInfo('Player Entity Removed')
            self.playerEntityLoaded.clear()

    def PackUpEntityForSceneTransfer(self, entity, destinationSceneID):
        initialEntityState = {}
        for name, component in entity.components.iteritems():
            factory = self.componentFactories[name]
            if not hasattr(factory, 'PackUpForSceneTransfer'):
                self.LogError('Factory is lacking PackUpForSceneTransfer:', name)
                continue
            state = factory.PackUpForSceneTransfer(component, destinationSceneID)
            if state:
                initialEntityState[name] = state
                self.LogInfo('EntityClient packing up entity ', entity, ' component ', name, ' with state ', state)

        return initialEntityState

    def ServerReportState(self, entityID, componentName):
        """
        Gets the ReportState from the server
        """
        entityService = sm.RemoteSvc('entityServer')
        return entityService.GetServerComponentState(entityID, componentName)

    def FindEntityByID(self, entityID):
        entity = BaseEntityService.FindEntityByID(self, entityID)
        if entity is not None:
            return weakref.proxy(entity)
        else:
            return
