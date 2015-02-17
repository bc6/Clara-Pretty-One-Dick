#Embedded file name: eve/common/script/planet/entities\baseRoute.py
"""
    Routes are templates which define a transit path for a potential
    packet of a commodity. While the packet must strictly follow the
    defined path, the actual commodity quantity contained in the packet
    may be smaller than the ideal size defined here.
"""
import weakref
import util
import eve.common.script.util.planetCommon as planetCommon

class BaseRoute(object):
    __guid__ = 'planet.BaseRoute'
    __name__ = 'BaseRoute'
    __slots__ = ['colony',
     'routeID',
     'charID',
     'commodityTypeID',
     'commodityQuantity',
     'path']

    def __init__(self, colony, routeID, charID, typeID, qty):
        self.colony = weakref.proxy(colony)
        self.routeID = routeID
        self.charID = charID
        self.commodityTypeID = typeID
        self.commodityQuantity = qty
        self.path = []

    def __str__(self):
        return 'PI Route <ID:%d> <Owner:%d> <Path:%s> <Type:%s>' % (self.routeID,
         self.charID,
         self.path,
         self.commodityTypeID)

    def GetSourcePinID(self):
        if len(self.path) < 1:
            return None
        return self.path[0]

    def GetDestinationPinID(self):
        if len(self.path) < 1:
            return None
        return self.path[-1]

    def SetSourcePin(self, sourcePin):
        self.path = [sourcePin.id]

    def SetPath(self, newPath):
        self.path = newPath[:]

    def GetType(self):
        return self.commodityTypeID

    def GetQuantity(self):
        return self.commodityQuantity

    def TransitsLink(self, endpoint1id, endpoint2id):
        if len(self.path) < 2:
            return False
        if endpoint1id not in self.path or endpoint2id not in self.path:
            return False
        prevID = self.path[0]
        for pinID in self.path[1:]:
            if prevID == endpoint1id and pinID == endpoint2id:
                return True
            if prevID == endpoint2id and pinID == endpoint1id:
                return True
            prevID = pinID

        return False

    def GetRoutingInfo(self):
        return (self.path[0],
         self.path[-1],
         self.commodityTypeID,
         self.commodityQuantity)

    def GetBandwidthUsage(self):
        """
            Gets the bandwidth usage of the route in cubic-meters-per-hour.
        """
        bwth = cfg.invtypes.Get(self.GetType()).volume * self.GetQuantity()
        cycleTime = self.GetRouteCycleTime()
        if cycleTime == 0.0 or cycleTime is None:
            return bwth
        else:
            return planetCommon.GetBandwidth(bwth, cycleTime)

    def GetRouteCycleTime(self):
        """
            A route's cycle time is defined by how often we expect to execute it.
            For routes leading from producers, it's the producer's time. For
            routes leading from storage pins, it's the consumer's time.
            For all other routes, it's undefined at the moment.
        """
        sourcePin = self.colony.GetPin(self.GetSourcePinID())
        if sourcePin.IsProducer():
            return sourcePin.GetCycleTime()
        if sourcePin.IsStorage():
            destinationPin = self.colony.GetPin(self.GetDestinationPinID())
            if destinationPin.IsConsumer():
                return destinationPin.GetCycleTime()
            return 0.0
        return 0.0

    def Serialize(self):
        """
            This method returns a slim keyval containing all the data
            necessary to replicate this route.
        """
        ret = util.KeyVal(routeID=self.routeID, charID=self.charID, path=self.path, commodityTypeID=self.commodityTypeID, commodityQuantity=self.commodityQuantity)
        return ret
