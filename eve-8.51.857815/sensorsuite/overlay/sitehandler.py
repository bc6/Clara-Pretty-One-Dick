#Embedded file name: sensorsuite/overlay\sitehandler.py
from utillib import KeyVal
ENABLED_BY_SITE_TYPE = 'sensorSuiteFilterEnabledBySiteType'

class SiteHandler(object):
    siteType = None
    filterIconPath = None
    filterLabel = None
    color = None

    def __init__(self):
        self.siteController = None

    def SetSiteController(self, siteController):
        self.siteController = siteController

    def GetSites(self):
        return self.siteController.siteMaps.GetSiteMapByKey(self.siteType)

    def LoadSites(self, solarSystemID):
        rawSites = self.GetSitesForSolarSystem(solarSystemID)
        self.siteController.siteMaps.ClearSiteMap(self.siteType)
        for siteID, site in rawSites.iteritems():
            siteData = self.GetSiteData(siteID, *site)
            self.siteController.siteMaps.AddSiteToMap(self.siteType, siteID, siteData)

    def UpdateSites(self, solarSystemID):
        newRawSites = self.GetSitesForSolarSystem(solarSystemID)
        storedSites = self.GetSites()
        newSiteSet = set(newRawSites.iterkeys())
        oldSiteSet = set(storedSites.iterkeys())
        added = newSiteSet.difference(oldSiteSet)
        removedSites = oldSiteSet.difference(newSiteSet)
        addedSites = {siteId:newRawSites[siteId] for siteId in added}
        self.ProcessSiteUpdate(addedSites, removedSites)
        self.OnSitesUpdated(storedSites)

    def ProcessSiteUpdate(self, addedSites, removedSites):
        self.siteController.ProcessSiteDataUpdate(addedSites, removedSites, self.siteType, self.GetSiteData)

    def GetSiteData(self, *args):
        """
        Convert the raw data to a SiteData derived instance used by the sensor overlay
        :param siteID: the unique key for the site
        :param args: the raw data fields
        :return: a SiteData based instance
        """
        raise NotImplementedError('You must provide a conversion method for the raw data to a SiteData derived instance')

    def GetSitesForSolarSystem(self, solarSystemID):
        """
        Gets the raw site data used for the sites managed by the handler
        :param solarSystemID: the current solar system to get the sites for
        :return: a dict {key: tuple}
        """
        raise NotImplementedError('You need to implement this method to provide the sites to display')

    def GetFilterConfig(self):
        return KeyVal(iconPath=self.filterIconPath, label=self.filterLabel, enabled=self.IsFilterEnabled(), color=self.color.GetRGB(), siteType=self.siteType)

    def SetFilterEnabled(self, enable):
        filterEnabledBySiteType = settings.char.ui.Get(ENABLED_BY_SITE_TYPE, {})
        filterEnabledBySiteType[self.siteType] = enable
        settings.char.ui.Set(ENABLED_BY_SITE_TYPE, filterEnabledBySiteType)

    def IsFilterEnabled(self):
        filterEnabledBySiteType = settings.char.ui.Get(ENABLED_BY_SITE_TYPE, {})
        return filterEnabledBySiteType.get(self.siteType, True)

    def IsVisible(self, siteData):
        return True

    def OnSitesUpdated(self, sites):
        pass
