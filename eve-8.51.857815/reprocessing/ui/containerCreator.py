#Embedded file name: reprocessing/ui\containerCreator.py


class ContainerCreator(object):

    def __init__(self, inputContainers, outputContainers, quotes):
        self.inputContainers = inputContainers
        self.outputContainers = outputContainers
        self.quotes = quotes

    def CreateInputItem(self, itemID, args):
        container = self.inputContainers.CreateContainer(itemID, args)
        container.RegisterForHoverEvents(itemID, self.OnMouseEnterInputItem, self.OnMouseExitInputItem)
        return container

    def RemoveInputItem(self, itemID):
        self.inputContainers.RemoveItem(itemID)

    def CreateOutputItems(self, typeID, typeInfo):
        return self.outputContainers.CreateContainer(typeID, typeInfo)

    def FlushOutputItems(self):
        self.outputContainers.Flush()

    def OnMouseEnterInputItem(self, itemID):
        self.inputContainers.HiliteContainers(itemID)
        self.outputContainers.HiliteOutputContainerOnMouseEnter(*self.quotes.GetOutputTypesForItemID(itemID).keys())

    def OnMouseExitInputItem(self, itemID):
        self.inputContainers.StopHiliteContainers(itemID)
        self.outputContainers.StopHiliteContainers(*self.quotes.GetOutputTypesForItemID(itemID).keys())

    def GetInputItem(self, itemID):
        return self.inputContainers.GetContainer(itemID)


class Containers(object):

    def __init__(self, containerCreator):
        self.containerCreator = containerCreator
        self.containers = {}

    def GetContainer(self, ctrlID):
        return self.containers[ctrlID]

    def CreateContainer(self, ctrlID, args):
        container = self.containerCreator(*args)
        self.containers[ctrlID] = container
        return container

    def HiliteOutputContainerOnMouseEnter(self, *ctrlIDs):
        for ctrlID in ctrlIDs:
            container = self.containers[ctrlID]
            container.BlinkHilite()

    def HiliteContainers(self, *ctrlIDs):
        for ctrlID in ctrlIDs:
            container = self.containers[ctrlID]
            container.ShowHilited()

    def StopHiliteContainers(self, *ctrlIDs):
        for ctrlID in ctrlIDs:
            self.containers[ctrlID].ShowNotHilited()

    def Flush(self):
        self.containers.clear()

    def RemoveItem(self, ctrlID):
        container = self.containers.pop(ctrlID)
        container.Close()
