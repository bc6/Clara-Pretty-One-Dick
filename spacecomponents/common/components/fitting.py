#Embedded file name: spacecomponents/common/components\fitting.py
from ..componentConst import FITTING_CLASS
from spacecomponents.common.helper import HasFittingComponent
from spacecomponents.common.helper import IsActiveComponent
from spacecomponents.common.helper import IsReinforcedComponent

def IsShipWithinFittingRange(spaceComponentStaticData, shipSlimItem, componentSlimItem, ballPark):
    if shipSlimItem is None:
        return False
    if not hasattr(componentSlimItem, 'typeID'):
        return False
    ball = ballPark.GetBall(componentSlimItem.itemID)
    itemIsDead = not ball or ball.isMoribund
    componentTypeID = componentSlimItem.typeID
    if shipSlimItem.ownerID != componentSlimItem.ownerID:
        return False
    if itemIsDead:
        return False
    if not HasFittingComponent(componentTypeID):
        return False
    if not IsActiveComponent(ballPark.componentRegistry, componentTypeID, componentSlimItem.itemID):
        return False
    if IsReinforcedComponent(ballPark.componentRegistry, componentTypeID, componentSlimItem.itemID):
        return False
    fittingRange = spaceComponentStaticData.GetAttributes(componentTypeID, FITTING_CLASS).range
    shipDistanceFromComponent = ballPark.GetSurfaceDist(shipSlimItem.itemID, componentSlimItem.itemID)
    return shipDistanceFromComponent <= fittingRange
