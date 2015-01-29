#Embedded file name: carbon/common/script/entities\position.py
import carbon.common.script.cef.componentViews.positionComponent as positionComponent
import collections
import geo2
import service
import GameWorld
import sys
STATE_CREATED = 0
STATE_UNREGISTERED = -1
STATE_REGISTERED = 1

class PositionService(service.Service):
    __guid__ = 'svc.position'
    __componentTypes__ = [positionComponent.PositionComponentView.GetComponentCodeName()]

    def CreateComponent(self, name, state):
        """
        Initializes the component with the provided state dict.
        If the dict is not provided you will still need to set the
        position, rotation and worldspaceID attributes explicitly in
        order for the component to behave correctly.
        
        The structure of the state dict should be as followed:
        "position" - position, 3 tuple describing (x,y,z)
        "rotation" - rotation, 4 tuple describing the rotation quaternion.
                     NOTE: Optionally, you can pass in a 3-tuple for
                           yaw/pitch/roll and this will be properly
                           converted to a quaternion.
        """
        c = GameWorld.PositionComponent()
        try:
            c.position = state['position']
        except KeyError:
            sys.exc_clear()

        try:
            r = state['rotation']
            if len(r) == 3:
                r = geo2.QuaternionRotationSetYawPitchRoll(*r)
            c.rotation = r
        except KeyError:
            sys.exc_clear()

        return c

    def PrepareComponent(self, sceneID, entityID, component):
        """
            Gets called in order to prepare a component. No other components can be referred to
        """
        self.entityService.entitySceneManager.PrepareComponent(entityID, sceneID, component)

    def SetupComponent(self, entity, component):
        """
            Gets called in order to setup a component. All other components can be referred to
        """
        pass

    def RegisterComponent(self, entity, component):
        """
            Gets called in order to register a component. The component can be searched for prior to this point.
        """
        component.state = STATE_REGISTERED

    def UnRegisterComponent(self, entity, component):
        component.state = STATE_UNREGISTERED

    def PackUpForClientTransfer(self, component):
        state = {}
        state['position'] = component.position
        state['rotation'] = component.rotation
        return state

    def PackUpForSceneTransfer(self, component, destinationSceneID = None):
        return self.PackUpForClientTransfer(component)

    def UnPackFromSceneTransfer(self, component, entity, state):
        component.position = state['position']
        component.rotation = state['rotation']
        return component

    def ReportState(self, component, entity):
        state = collections.OrderedDict()
        state['position'] = ', '.join([ '%.3f' % f for f in component.position ])
        state['rotation'] = component.rotation
        return state
