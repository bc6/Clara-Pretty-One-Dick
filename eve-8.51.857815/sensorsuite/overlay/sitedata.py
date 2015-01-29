#Embedded file name: sensorsuite/overlay\sitedata.py


class SiteData:
    """
    This is a data construct holding data we know about sites in a system for the sensor overlay
    """
    siteType = None
    baseColor = None
    hoverSoundEvent = None

    def __init__(self, siteID, position):
        self.siteID = siteID
        self.position = position
        self.ballID = None

    def IsAccurate(self):
        """is the data accurate"""
        return True

    def GetBracketClass(self):
        raise NotImplementedError('GetBracketClass is not implemented')

    def GetSiteType(self):
        return self.siteType

    def GetName(self):
        raise NotImplementedError('You need to provide a name for site')

    def GetSortKey(self):
        return (self.GetSiteType(), self.GetName())

    def GetMenu(self):
        return []

    def WarpToAction(self, *args):
        pass

    def GetSecondaryActions(self):
        """provide the radial menu secondary actions action"""
        return []

    def GetSiteActions(self):
        """
        provide the radial menu a particular preferred main action
        return a list of one action or None
        """
        return None
