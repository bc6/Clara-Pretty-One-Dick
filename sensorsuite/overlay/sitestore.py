#Embedded file name: sensorsuite/overlay\sitestore.py
from collections import defaultdict
import itertools

class DuplicateSiteIdError(Exception):
    pass


class SiteMapStore:

    def __init__(self):
        self.siteMapsBySiteType = defaultdict(dict)

    def Clear(self):
        self.siteMapsBySiteType.clear()

    def GetSiteMapByKey(self, key):
        return self.siteMapsBySiteType[key]

    def ClearSiteMap(self, key):
        if key in self.siteMapsBySiteType:
            del self.siteMapsBySiteType[key]

    def IterAllSiteMaps(self):
        return self.siteMapsBySiteType.itervalues()

    def IterAllSites(self):
        for siteMap in self.IterAllSiteMaps():
            for siteData in siteMap.itervalues():
                yield siteData

    def AddSiteToMap(self, key, siteId, site):
        siteMap = self.siteMapsBySiteType[key]
        if siteId in siteMap:
            raise DuplicateSiteIdError('SiteMap %s already has an entry with id %s' % (key, siteId))
        siteMap[siteId] = site

    def IterSitesByKey(self, key):
        return self.siteMapsBySiteType[key].itervalues()

    def IterSitesByKeys(self, *keys):
        return itertools.chain(*(self.siteMapsBySiteType[key].itervalues() for key in keys))
