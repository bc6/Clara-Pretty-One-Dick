#Embedded file name: spacecomponents/common/components\physics.py
from spacecomponents.common.components.component import Component
from spacecomponents.common.componentConst import PHYSICS_CLASS

class Physics(Component):
    """
    Component that defines in-space physics behavior (Destiny).
    """

    def __init__(self, itemID, typeID, attributes, componentRegistry):
        Component.__init__(self, itemID, typeID, attributes, componentRegistry)
        self.isAlwaysGlobal = attributes.isAlwaysGlobal


def IsAlwaysGlobal(typeID):
    """
    Takes in typeID.
    Returns true/false for if the type should always have a globally visible bracket.
    """
    return cfg.spaceComponentStaticData.GetAttributes(typeID, PHYSICS_CLASS).isAlwaysGlobal
