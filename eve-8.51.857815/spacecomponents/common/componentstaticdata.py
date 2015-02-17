#Embedded file name: spacecomponents/common\componentstaticdata.py
"""
This provides an API for querying static data related to space components
"""
import fsdSchemas.binaryLoader as fsdBinaryLoader
from ccpProfile import TimedFunction
from componentConst import ALL_COMPONENTS

class ComponentStaticData(object):

    def __init__(self, fsdResPath):
        self.componentDataByTypeID = fsdBinaryLoader.LoadFSDDataForCFG(fsdResPath)

    @TimedFunction('SpaceComponent::ComponentStaticData::GetAttributes')
    def GetAttributes(self, typeID, componentName):
        return getattr(self.componentDataByTypeID[typeID], componentName)

    def GetComponentNamesForType(self, typeID):
        componentContainer = self.componentDataByTypeID.get(typeID, None)
        return [ componentName for componentName in ALL_COMPONENTS if hasattr(componentContainer, componentName) ]

    def GetTypeIDsForComponentName(self, componentName):
        return [ typeID for typeID, componentContainer in self.componentDataByTypeID.iteritems() if hasattr(componentContainer, componentName) ]

    @TimedFunction('SpaceComponent::ComponentStaticData::TypeHasComponentWithName')
    def TypeHasComponentWithName(self, typeID, componentName):
        componentContainer = self.componentDataByTypeID.get(typeID, None)
        if componentContainer:
            return hasattr(componentContainer, componentName)
        else:
            return False
