#Embedded file name: carbon/common/script/entities\proximityTrigger.py
"""
Contains the trigger shape component.
"""
import collections
import GameWorld
import service
import geo2
import util

class ProximityTriggerComponent:
    """
    Component that enables an entity to get notified about triggers.
    """
    __guid__ = 'physics.ProximityTriggerComponent'


class ProximityTriggerScene:
    """
    Callback object for GameWorld.
    """

    def __init__(self):
        self.enterCallbacks = {}
        self.exitCallbacks = {}

    def OnEnter(self, causingEntityID, triggerEntityID):
        """
        Called whenever causingEntityID enters triggerEntityID
        """
        try:
            self.enterCallbacks[triggerEntityID](causingEntityID, triggerEntityID)
        except KeyError:
            pass

    def OnExit(self, causingEntityID, triggerEntityID):
        """
        Called whenever causingEntityID leaves triggerEntityID
        """
        try:
            self.exitCallbacks[triggerEntityID](causingEntityID, triggerEntityID)
        except KeyError:
            pass


class ProximityTriggerService(service.Service):
    __guid__ = 'svc.proximityTrigger'
    __componentTypes__ = ['proximityTrigger']

    def Run(self, *memStream):
        self.scenes = {}

    def OnLoadEntityScene(self, sceneID):
        """
        Creates the proximity trigger scene.
        """
        scene = ProximityTriggerScene()
        self.scenes[sceneID] = scene

    def OnEntitySceneLoaded(self, sceneID):
        """
        Ties the created proximity trigger scene to this gameworld instance.
        """
        gw = GameWorld.Manager.GetGameWorld(long(sceneID))
        gw.triggerReportHandler = self.scenes[sceneID]

    def OnUnloadEntityScene(self, sceneID):
        """
        Unloads proximity trigger scene.
        """
        gw = GameWorld.Manager.GetGameWorld(long(sceneID))
        if gw:
            gw.triggerReportHandler = None
        del self.scenes[sceneID]

    def CreateComponent(self, name, state):
        """
        Create component instance.
        """
        component = ProximityTriggerComponent()
        if 'radius' in state:
            component.radius = state['radius']
        elif 'dimensions' in state:
            if type(state['dimensions']) == type(str()):
                component.dimensions = util.UnpackStringToTuple(state['dimensions'], float)
            else:
                component.dimensions = state['dimensions']
        else:
            self.LogError('Unknown trigger shape')
            return None
        if 'relativepos' in state:
            if type(state['relativepos']) == type(str()):
                component.relativePosition = util.UnpackStringToTuple(state['relativepos'], float)
            else:
                component.relativePosition = state['relativepos']
        else:
            component.relativePosition = (0, 0, 0)
        return component

    def ReportState(self, component, entity):
        state = collections.OrderedDict()
        if hasattr(component, 'radius'):
            state['radius'] = component.radius
        elif hasattr(component, 'dimensions'):
            state['dimensions'] = component.dimensions
        else:
            raise RuntimeError('Unknown trigger shape')
        if hasattr(component, 'relativepos'):
            state['relativepos'] = component.relativepos
        return state

    def PackUpForSceneTransfer(self, component, destinationSceneID):
        return self.PackUpForClientTransfer(component)

    def PackUpForClientTransfer(self, component):
        state = {}
        if hasattr(component, 'radius'):
            state['radius'] = component.radius
        elif hasattr(component, 'dimensions'):
            state['dimensions'] = component.dimensions
        else:
            raise RuntimeError('Unknown trigger shape')
        state['relativepos'] = component.relativePosition
        return state

    def UnPackFromSceneTransfer(self, component, entity, state):
        if 'radius' in state:
            component.radius = state['radius']
        elif 'dimensions' in state:
            component.dimensions = state['dimensions']
        else:
            raise RuntimeError('Unknown trigger shape')
        component.relativePosition = state['relativepos']
        return component

    def SetupComponent(self, entity, component):
        """
        Sets up the component in gameworld.
        """
        self.LogInfo('Setting up component', component)
        gw = GameWorld.Manager.GetGameWorld(long(entity.scene.sceneID))
        if hasattr(component, 'radius'):
            gw.CreateTriggerSphere(entity.entityID, geo2.Add(entity.position.position, component.relativePosition), entity.position.rotation, component.radius)
        elif hasattr(component, 'dimensions'):
            gw.CreateTriggerAABB(entity.entityID, geo2.Add(entity.position.position, component.relativePosition), entity.position.rotation, component.dimensions)
        else:
            raise RuntimeError('Unknown trigger shape')
        self.LogInfo('Creating trigger shape for component', component)

    def PreTearDownComponent(self, entity, component):
        try:
            del self.scenes[entity.scene.sceneID].enterCallbacks[entity.entityID]
        except KeyError:
            pass

        try:
            del self.scenes[entity.scene.sceneID].exitCallbacks[entity.entityID]
        except KeyError:
            pass

        gw = GameWorld.Manager.GetGameWorld(long(entity.scene.sceneID))
        gw.RemoveTriggerShape(entity.entityID)

    def RegisterExitCallback(self, sceneID, triggerID, callback):
        """
        Allows a subsystem to register a callback for whenever an entity enters
        the trigger entity with ID triggerID.
        
        sceneID - the scene the triggerEntity belongs to
        triggerID - ID of the entity that has the proximity trigger
        callback - function that receives the ID of the causing entity as parameter
        """
        self.scenes[sceneID].exitCallbacks[triggerID] = callback

    def RegisterEnterCallback(self, sceneID, triggerID, callback):
        """
        Allows a subsystem to register a callback for whenever an entity enters
        the trigger entity with ID triggerID.
        
        sceneID - the scene the triggerEntity belongs to
        triggerID - ID of the entity that has the proximity trigger
        callback - function that receives the ID of the causing entity as parameter
        """
        self.scenes[sceneID].enterCallbacks[triggerID] = callback
