#Embedded file name: eve/common/lib\killRightTracker.py
from collections import defaultdict

class KillRightTracker(object):
    """
    This keeps track of kill rights that have been put up to sale. We keep track of the time
    we last updated it and if it has been longer than cache time we refetch it. This is used
    both on client and server. If the data isn't valid then the client fetches to the server
    and the server fetches to the DB.
    """

    def __init__(self, fetcher, getTimeFunc, cacheTime):
        self.killRightsByToID = {}
        self.FetchKillRights = fetcher
        self.GetTime = getTimeFunc
        self.cacheTime = cacheTime

    def GetInvalidKillRights(self, toIDs):
        return [ toID for toID in toIDs if not self.IsDataValid(toID) ]

    def GetKillRights(self, toIDs, *validIDs):
        toIDsToFetch = self.GetInvalidKillRights(toIDs)
        if toIDsToFetch:
            newKillRights = self.FetchKillRights(toIDsToFetch)
            self.CacheKillRights(newKillRights, toIDsToFetch)
        ret = []
        for toID in toIDs:
            try:
                ret.extend([ killRight for killRight in self.killRightsByToID[toID][1].itervalues() if killRight.restrictedTo is None or killRight.restrictedTo in validIDs ])
            except KeyError:
                pass

        return ret

    def CacheKillRights(self, newKillRights, toIDs):
        killRightsByToID = defaultdict(dict)
        for killRight in newKillRights:
            killRightsByToID[killRight.toID][killRight.killRightID] = killRight

        currentTime = self.GetTime()
        for toID in toIDs:
            self.killRightsByToID[toID] = (currentTime, killRightsByToID[toID])

    def OnKillRightAdded(self, killRight):
        if killRight.toID not in self.killRightsByToID:
            self.killRightsByToID[killRight.toID] = (self.GetTime(), {})
        self.killRightsByToID[killRight.toID][1][killRight.killRightID] = killRight

    def OnKillRightsAdded(self, killRights):
        for killRight in killRights:
            self.OnKillRightAdded(killRight)

    def IsDataValid(self, toID):
        if toID not in self.killRightsByToID:
            return False
        lastUpdateTime = self.killRightsByToID[toID][0]
        if lastUpdateTime + self.cacheTime < self.GetTime():
            return False
        return True

    def GetKillRightsFromCache(self, toID):
        try:
            return self.killRightsByToID[toID][1]
        except KeyError:
            return []

    def OnKillRightRemoved(self, toID, killRightID):
        try:
            del self.killRightsByToID[toID][1][killRightID]
        except KeyError:
            pass
