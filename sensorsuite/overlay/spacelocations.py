#Embedded file name: sensorsuite/overlay\spacelocations.py
import weakref
from utillib import KeyVal

class SpaceLocations:

    def __init__(self):
        self.locationsBySiteId = {}
        self.locationsByBallId = {}

    def Clear(self):
        self.locationsBySiteId.clear()
        self.locationsByBallId.clear()

    def AddLocation(self, ball, bracket, siteData):
        locationData = KeyVal(ballRef=weakref.ref(ball), bracket=bracket, siteData=siteData, ballID=ball.id)
        self.locationsBySiteId[siteData.siteID] = locationData
        self.locationsByBallId[ball.id] = locationData

    def RemoveLocation(self, siteID):
        locData = self.GetBySiteID(siteID)
        del self.locationsBySiteId[siteID]
        del self.locationsByBallId[locData.ballID]

    def GetBracketByBallID(self, ballID):
        locData = self.locationsByBallId.get(ballID)
        if locData:
            return locData.bracket
        else:
            return None

    def GetBracketBySiteID(self, siteID):
        locData = self.locationsBySiteId.get(siteID)
        if locData:
            return locData.bracket
        else:
            return None

    def GetBySiteID(self, siteID):
        return self.locationsBySiteId[siteID]

    def ContainsSite(self, siteID):
        return siteID in self.locationsBySiteId

    def GetLocations(self):
        return self.locationsBySiteId.values()

    def IterLocations(self):
        return self.locationsBySiteId.itervalues()
