#Embedded file name: spacecomponents/common\helper.py
from ccpProfile import TimedFunction
import componentConst

def TypeHasComponent(typeID, componentClassName):
    return cfg.spaceComponentStaticData.TypeHasComponentWithName(typeID, componentClassName)


@TimedFunction('SpaceComponent::Helper::HasScoopComponent')
def HasScoopComponent(typeID):
    return TypeHasComponent(typeID, componentConst.SCOOP_CLASS)


@TimedFunction('SpaceComponent::Helper::HasActivateComponent')
def HasActivateComponent(typeID):
    return TypeHasComponent(typeID, componentConst.ACTIVATE_CLASS)


@TimedFunction('SpaceComponent::Helper::HasDeployComponent')
def HasDeployComponent(typeID):
    return TypeHasComponent(typeID, componentConst.DEPLOY_CLASS)


@TimedFunction('SpaceComponent::Helper::HasDecayComponent')
def HasDecayComponent(typeID):
    return TypeHasComponent(typeID, componentConst.DECAY_CLASS)


@TimedFunction('SpaceComponent::Helper::HasDogmaticComponent')
def HasDogmaticComponent(typeID):
    return TypeHasComponent(typeID, componentConst.DOGMATIC_CLASS)


@TimedFunction('SpaceComponent::Helper::HasFittingComponent')
def HasFittingComponent(typeID):
    return TypeHasComponent(typeID, componentConst.FITTING_CLASS)


@TimedFunction('SpaceComponent::Helper::HasCargoBayComponent')
def HasCargoBayComponent(typeID):
    return TypeHasComponent(typeID, componentConst.CARGO_BAY)


@TimedFunction('SpaceComponent::Helper::HasReinforceComponent')
def HasReinforceComponent(typeID):
    return TypeHasComponent(typeID, componentConst.REINFORCE_CLASS)


@TimedFunction('SpaceComponent::Helper::HasPhysicsComponent')
def HasPhysicsComponent(typeID):
    return TypeHasComponent(typeID, componentConst.PHYSICS_CLASS)


@TimedFunction('SpaceComponent::Helper::HasBountyEscrowComponent')
def HasBountyEscrowComponent(typeID):
    return TypeHasComponent(typeID, componentConst.BOUNTYESCROW_CLASS)


@TimedFunction('SpaceComponent::Helper::HasSiphonComponent')
def HasSiphonComponent(typeID):
    return TypeHasComponent(typeID, componentConst.SIPHON_CLASS)


@TimedFunction('SpaceComponent::Helper::HasBountyEscrowComponent')
def HasBountyEscrowComponent(typeID):
    return TypeHasComponent(typeID, componentConst.BOUNTYESCROW_CLASS)


@TimedFunction('SpaceComponent::Helper::HasMicroJumpDriverComponent')
def HasMicroJumpDriverComponent(typeID):
    return TypeHasComponent(typeID, componentConst.MICRO_JUMP_DRIVER_CLASS)


@TimedFunction('SpaceComponent::Helper::IsActiveComponent')
def IsActiveComponent(componentRegistry, typeID, itemID):
    if HasActivateComponent(typeID):
        activateComponent = componentRegistry.GetComponentForItem(itemID, componentConst.ACTIVATE_CLASS)
        return activateComponent.IsActive()
    return True


@TimedFunction('SpaceComponent::Helper::IsReinforcedComponent')
def IsReinforcedComponent(componentRegistry, typeID, itemID):
    if HasReinforceComponent(typeID):
        reinforceComponent = componentRegistry.GetComponentForItem(itemID, componentConst.REINFORCE_CLASS)
        return reinforceComponent.IsReinforced()
    return False


@TimedFunction('SpaceComponent::Helper::HasWarpDisruptionComponent')
def HasWarpDisruptionComponent(typeID):
    return TypeHasComponent(typeID, componentConst.WARP_DISRUPTION_CLASS)


def HasBehaviorComponent(typeID):
    return TypeHasComponent(typeID, componentConst.BEHAVIOR)


def GetTypesWithBehaviorComponent():
    return cfg.spaceComponentStaticData.GetTypeIDsForComponentName(componentConst.BEHAVIOR)
