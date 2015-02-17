#Embedded file name: eve/common/script/planet\basePlanet.py
"""
    Base planet object :
    This is the base planet object. It handles the simulation and various stuff that is
    shared between client and server.
"""
import blue.heapq as heapq
from .baseColony import BaseColony

class BasePlanet:
    __guid__ = 'planet.BasePlanet'
    __name__ = 'BasePlanet'

    def __init__(self, planetBroker, planetID):
        self.planetBroker = planetBroker
        self.planetID = planetID
        self.planetTypeID = None
        self.planetLogClass = ''
        self.planetCelestialID = None
        self.Init()

    def Init(self):
        self.ownersByPinID = {}
        self.colonies = {}

    def GetTypeID(self):
        raise NotImplementedError('GetPlanetTypeID must be defined for client and server')

    def GetColony(self, ownerID):
        if ownerID in self.colonies:
            return self.colonies[ownerID]
        else:
            return None

    def GetColonyByPinID(self, pinID):
        if pinID not in self.ownersByPinID:
            return None
        ownerID = self.ownersByPinID[pinID]
        if ownerID not in self.colonies:
            return None
        return self.colonies[ownerID]

    def GetPin(self, pinID):
        """
            This is largely here to help with porting. Do not use this.
            You should be fetching the colony, checking it, and then
            fetching the pin from there.
        """
        if pinID not in self.ownersByPinID:
            return None
        ownerID = self.ownersByPinID[pinID]
        if ownerID not in self.colonies:
            return None
        return self.colonies[ownerID].GetPin(pinID)

    def GetNewColony(self, ownerID):
        return BaseColony(self, ownerID)

    def GetCommandCenterLevel(self, ownerID):
        colony = self.GetColony(ownerID)
        return colony.colonyData.level

    def OnPinCreated(self, ownerID, pinID):
        self.ownersByPinID[pinID] = ownerID

    def OnPinRemoved(self, ownerID, pinID):
        pass

    def OnLinkCreated(self, ownerID, parentID, childID):
        pass

    def OnLinkRemoved(self, ownerID, parentID, childID):
        pass

    def OnRouteCreated(self, ownerID, routeID):
        pass

    def OnRouteRemoved(self, ownerID, routeID):
        pass

    def OnSchematicInstalled(self, ownerID, pinID, schematicID):
        pass

    def OnLinkUpgraded(self, ownerID, parentPinID, childPinID):
        pass

    def LogInfo(self, *args):
        self.planetBroker.LogInfo(self.planetLogClass, self.planetID, ' | ', *args)

    def LogWarn(self, *args):
        self.planetBroker.LogWarn(self.planetLogClass, self.planetID, ' | ', *args)

    def LogError(self, *args):
        self.planetBroker.LogError(self.planetLogClass, self.planetID, ' | ', *args)

    def LogNotice(self, *args):
        self.planetBroker.LogNotice(self.planetLogClass, self.planetID, ' | ', *args)
