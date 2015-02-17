#Embedded file name: spacecomponents/common\componentregistry.py
from collections import defaultdict
from componentmessenger import ComponentMessenger
from eveexceptions.exceptionEater import ExceptionEater

class UnregisteredComponentError(Exception):
    pass


class ComponentInstanceAlreadyExists(Exception):
    pass


def ExportCall(func):
    func.isExportedComponentCall = True
    return func


class ComponentRegistry(object):

    def __init__(self, attributeLoader, asyncFuncs, eventLogger):
        self.attributeLoader = attributeLoader
        self.asyncFuncs = asyncFuncs
        self.eventLogger = eventLogger
        self.componentClassTypes = {}
        self.typeIDToClassMapping = defaultdict(list)
        self.itemIDToComponentInstances = {}
        self.componentNameToItemIDs = defaultdict(dict)
        self.messenger = ComponentMessenger()

    def RegisterComponentClass(self, componentClass):
        self.componentClassTypes[componentClass.componentName] = componentClass
        for typeID in self.attributeLoader.GetTypeIDsForComponentName(componentClass.componentName):
            self.typeIDToClassMapping[typeID].append(componentClass)

    def GetComponentClassesForTypeID(self, typeID):
        return self.typeIDToClassMapping[typeID]

    def GetComponentsByItemID(self, itemID):
        return self.itemIDToComponentInstances[itemID]

    def CreateComponentInstances(self, itemID, typeID):
        if itemID in self.itemIDToComponentInstances:
            raise ComponentInstanceAlreadyExists('itemID %s already exists. TypeID was %s' % (itemID, typeID))
        componentClassesForTypeID = self.typeIDToClassMapping[typeID]
        components = {}
        self.itemIDToComponentInstances[itemID] = components
        for componentClass in componentClassesForTypeID:
            attributes = self.attributeLoader.GetAttributes(typeID, componentClass.componentName)
            with ExceptionEater('Error creating a component %s' % componentClass.componentName):
                instance = componentClass.factoryMethod(itemID, typeID, attributes, self)
                components[componentClass.componentName] = instance
            self.componentNameToItemIDs[componentClass.componentName][itemID] = instance

        return components

    def DeleteComponentInstances(self, itemID):
        self.messenger.DeleteSubscriptionsForItem(itemID)
        instance = self.itemIDToComponentInstances.pop(itemID)
        for componentName in instance:
            del self.componentNameToItemIDs[componentName][itemID]

    def GetInstancesWithComponentClass(self, componentName):
        return self.componentNameToItemIDs[componentName].values()

    def SendMessageToItem(self, itemID, messageName, *args, **kwargs):
        self.messenger.SendMessageToItem(itemID, messageName, *args, **kwargs)

    def SubscribeToItemMessage(self, itemID, messageName, messageHandler):
        self.GetComponentsByItemID(itemID)
        self.messenger.SubscribeToItemMessage(itemID, messageName, messageHandler)

    def GetComponentForItem(self, itemID, componentClassID):
        return self.itemIDToComponentInstances[itemID][componentClassID]

    def UnsubscribeFromItemMessage(self, itemID, messageName, messageHandler):
        self.messenger.UnsubscribeFromItemMessage(itemID, messageName, messageHandler)

    def CallComponent(self, session, itemID, componentClassName, methodName, *args, **kwargs):
        try:
            component = self.GetComponentForItem(itemID, componentClassName)
        except KeyError:
            return

        method = getattr(component, methodName)
        if not getattr(method, 'isExportedComponentCall', False):
            raise RuntimeError("The method '%s' is not exported on component '%s'" % (methodName, componentClassName))
        return method(session, *args, **kwargs)
