#Embedded file name: carbon/common/script/entities/AI\aimingCommon.py
"""
Contains base class for the AI aiming service thats used on both server and client.
"""
import GameWorld
from carbon.common.script.sys.service import Service
import collections

class aimingCommon(Service):
    """
    Base class for aimingServer and aimingClient.
    """
    __guid__ = 'AI.aimingCommon'
    sceneManagers = {}
    __componentTypes__ = ['aiming']

    def CreateComponent(self, name, state):
        """ 
        Creates a new aiming component 
        """
        component = GameWorld.AimingComponent()
        component.entityTypeString = state[const.aiming.AIMING_COMPONENT_ENTITY_TYPE]
        return component

    def PrepareComponent(self, sceneID, entityID, component):
        """
        Gets called in order to prepare a component. No other components can be referred to
        """
        if sceneID not in self.sceneManagers:
            self.LogError('SceneID in prepare aiming component has no previous manager ', sceneID, entityID)
            return
        component.entityID = entityID
        component.entityTypeID = const.aiming.AIMING_ENTITY_TYPE_TO_ID.get(component.entityTypeString)
        if component.entityTypeID == -1:
            self.LogError('entity in prepare aimingperception component has missing type', entityID)
            return

    def SetupComponent(self, entity, component):
        """
        Gets called in order to setup a component. All other components can be referred to
        """
        if entity.scene.sceneID not in self.sceneManagers:
            self.LogError('Trying to register a aiming component thats doesnt have a valid scene', entity.entityID, entity.scene.sceneID)
            return
        aimingManager = self.sceneManagers[entity.scene.sceneID]
        aimingManager.AddEntity(component)

    def RegisterComponent(self, entity, component):
        """
        Gets called in order to register a component. The component can be searched for prior to this point.
        """
        pass

    def UnRegisterComponent(self, entity, component):
        """
        Gets called in order to unregister a component. The component cannot be searched for after to this point.
        """
        if entity.scene.sceneID not in self.sceneManagers:
            self.LogError("Trying to remove a aiming entity who's scene doesn't have a manager", entity.entityID, entity.scene.sceneID)
            return
        aimingManager = self.sceneManagers[entity.scene.sceneID]
        aimingManager.RemoveEntity(entity.entityID)

    def TearDownComponent(self, entity, component):
        """
        Destroys component as its now no longer used
        """
        pass

    def ReportState(self, component, entity):
        report = collections.OrderedDict()
        report['Entity Type'] = component.entityTypeString
        return report

    def GetAimingManager(self, sceneID):
        """
        Returns the scene's aiming manager
        """
        return self.sceneManagers[sceneID]

    def MakeAimingManager(self):
        """
        Overridden function to make a aiming manager of the correct type (server or client)
        """
        raise NotImplementedError('This is a pure virtual function to create a aiming manager')

    def OnLoadEntityScene(self, sceneID):
        """
        New scene is created so create a new aiming manager for it
        """
        self.LogInfo('Registering a new aiming system for scene ', sceneID)
        if sceneID in self.sceneManagers:
            self.LogError('Duplicate scene passed to aiming system Register from entityService ', sceneID)
            return
        aimingManager = self.MakeAimingManager()
        self.sceneManagers[sceneID] = aimingManager
        aimingManager.SetStaticSettings((self.GetValidTargets(),))
        gw = self.gameWorldService.GetGameWorld(sceneID)
        aimingManager.SetGameWorld(gw)
        GameWorld.GetSceneManagerSingleton().AddComponentManager(sceneID, aimingManager)
        self.LogInfo('Done Creating a new aiming system for scene ', sceneID)

    def OnUnloadEntityScene(self, sceneID):
        """
        Scene is being removed, so remove its aiming manager
        """
        self.LogInfo('Unloading aiming system for scene ', sceneID)
        gw = self.gameWorldService.GetGameWorld(sceneID)
        if sceneID in self.sceneManagers:
            del self.sceneManagers[sceneID]
        else:
            self.LogError('Non-existent scene passed to aiming system Unload from entityService ', sceneID)
        self.LogInfo('Done Unloading aiming system for scene ', sceneID)

    def GetValidTargets(self):
        """
        Get valid target types
        """
        validTargets = []
        for aimTarget in const.aiming.AIMING_VALID_TARGETS.values():
            if self.IsTargetClientServerValid(aimTarget[const.aiming.AIMING_VALID_TARGETS_FIELD_CLIENTSERVER_FLAG]):
                validTargets.append((aimTarget[const.aiming.AIMING_VALID_TARGETS_FIELD_ID], aimTarget[const.aiming.AIMING_VALID_TARGETS_FIELD_NAME], aimTarget[const.aiming.AIMING_VALID_TARGETS_FIELD_RESELECTDELAY]))

        return tuple(validTargets)
