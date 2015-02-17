#Embedded file name: sensorsuite/overlay\staticsites.py
from eve.client.script.ui.shared.radialMenu.spaceRadialMenuFunctions import bookMarkOption
import localization
from sensorsuite.overlay.brackets import SensorSuiteBracket, INNER_ICON_COLOR
from sensorsuite.overlay.siteconst import SITE_COLOR_STATIC_SITE
from sensorsuite.overlay.sitedata import SiteData
from sensorsuite.overlay.sitehandler import SiteHandler
from sensorsuite.overlay.sitetype import STATIC_SITE
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import WarpToItem

class StaticSiteData(SiteData):
    """
    This is a data construct holding data we know about sites in a system for the sensor overlay
    """
    siteType = STATIC_SITE
    baseColor = SITE_COLOR_STATIC_SITE

    def __init__(self, siteID, position, dungeonNameID, factionID):
        SiteData.__init__(self, siteID, position)
        self.factionID = factionID
        self.dungeonNameID = dungeonNameID
        self.dungeonName = localization.GetByMessageID(dungeonNameID)

    def GetBracketClass(self):
        return StaticSiteBracket

    def GetName(self):
        return self.dungeonName

    def GetMenu(self):
        return sm.GetService('menu').CelestialMenu(self.siteID)

    def WarpToAction(self, _, distance, *args):
        return WarpToItem(self.siteID, warpRange=distance)

    def GetSecondaryActions(self):
        return [bookMarkOption]


class StaticSiteBracket(SensorSuiteBracket):
    outerColor = SITE_COLOR_STATIC_SITE.GetRGBA()
    outerTextures = ('res:/UI/Texture/classes/SensorSuite/bracket_landmark_1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_landmark_2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_landmark_3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_landmark_4.png')
    innerColor = INNER_ICON_COLOR.GetRGBA()
    innerIconResPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'

    def ApplyAttributes(self, attributes):
        SensorSuiteBracket.ApplyAttributes(self, attributes)

    def GetMenu(self):
        return self.data.GetMenu()


class StaticSiteHandler(SiteHandler):
    siteType = STATIC_SITE
    filterIconPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'
    filterLabel = 'UI/Inflight/Scanner/LandmarkSiteFilterLabel'
    color = SITE_COLOR_STATIC_SITE

    def GetSiteData(self, siteID, position, dungeonNameID, factionID):
        return StaticSiteData(siteID, position, dungeonNameID, factionID)
