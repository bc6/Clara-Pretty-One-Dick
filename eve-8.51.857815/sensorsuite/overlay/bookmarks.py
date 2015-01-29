#Embedded file name: sensorsuite/overlay\bookmarks.py
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import WarpToBookmark
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SimpleRadialMenuAction
from eve.common.script.sys.eveCfg import IsSolarSystem
from inventorycommon.const import groupStation
from inventorycommon.types import GetGroupID
from sensorsuite.overlay.bookmarkvisibilitymanager import bookmarkVisibilityManager
from sensorsuite.overlay.brackets import SensorSuiteBracket, INNER_ICON_COLOR
from sensorsuite.overlay.siteconst import SITE_COLOR_BOOKMARK, SITE_COLOR_CORP_BOOKMARK
from sensorsuite.overlay.sitedata import SiteData
from sensorsuite.overlay.sitehandler import SiteHandler
from sensorsuite.overlay.sitetype import BOOKMARK, CORP_BOOKMARK
MAX_VISIBLE_NAME_LENGTH = 20

def CleanText(text):
    if text is None:
        text = ''
    else:
        text.strip()
    return text


def GetBookmarkPosition(bookmark):
    if bookmark.itemID is None or IsSolarSystem(bookmark.itemID):
        position = (bookmark.x, bookmark.y, bookmark.z)
    else:
        loc = cfg.evelocations.Get(bookmark.itemID)
        position = (loc.x, loc.y, loc.z)
    return position


def GetBookmarkSiteActions(bookmark):
    groupID = GetGroupID(bookmark.typeID)
    if groupID == groupStation:
        return [SimpleRadialMenuAction(option1='UI/Inflight/DockInStation')]
    else:
        return None


def ProcessBookmarkUpdate(sensorSuiteSvc, bookmarks, siteType, addSiteDataMethod):
    newBookmarks = {bm.bookmarkID:bm for bm in bookmarks}
    storedBookmarks = sensorSuiteSvc.siteMaps.GetSiteMapByKey(siteType)
    newBookmarkSet = set(newBookmarks.iterkeys())
    oldBookmarkSet = set(storedBookmarks.iterkeys())
    added = newBookmarkSet.difference(oldBookmarkSet)
    removedBookmarks = oldBookmarkSet.difference(newBookmarkSet)
    addedBookmarks = {bmId:(newBookmarks[bmId],) for bmId in added}
    sensorSuiteSvc.ProcessSiteDataUpdate(addedBookmarks, removedBookmarks, siteType, addSiteDataMethod)


class BookmarkSiteData(SiteData):
    siteType = BOOKMARK
    baseColor = SITE_COLOR_BOOKMARK

    def __init__(self, siteID, position, bookmark = None):
        SiteData.__init__(self, siteID, position)
        self.bookmark = bookmark
        self.name = CleanText(bookmark.memo)

    def GetBracketClass(self):
        return BookmarkBracket

    def GetName(self):
        return self.name

    def WarpToAction(self, itemID, distance, *args):
        WarpToBookmark(self.bookmark, warpRange=distance)

    def GetMenu(self):
        itemID = self.bookmark.itemID or self.bookmark.locationID
        typeID = self.bookmark.typeID
        return sm.GetService('menu').CelestialMenu(itemID, typeID=typeID, bookmark=self.bookmark)

    def GetSecondaryActions(self):
        return [SimpleRadialMenuAction(option1='UI/Inflight/EditBookmark')]

    def GetSiteActions(self):
        return GetBookmarkSiteActions(self.bookmark)


class BookmarkBracket(SensorSuiteBracket):
    outerColor = SITE_COLOR_BOOKMARK.GetRGBA()
    innerColor = INNER_ICON_COLOR.GetRGBA()
    innerIconResPath = 'res:/UI/Texture/Icons/38_16_150.png'
    outerTextures = ('res:/UI/Texture/classes/SensorSuite/bracket_bookmark_1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_bookmark_2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_bookmark_3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_bookmark_4.png')

    def ApplyAttributes(self, attributes):
        SensorSuiteBracket.ApplyAttributes(self, attributes)
        self.UpdateSiteName(CleanText(self.data.bookmark.note))

    def GetMenu(self):
        return self.data.GetMenu()


class CorpBookmarkSiteData(BookmarkSiteData):
    siteType = CORP_BOOKMARK
    baseColor = SITE_COLOR_CORP_BOOKMARK

    def GetBracketClass(self):
        return CorpBookmarkBracket


class CorpBookmarkBracket(BookmarkBracket):
    outerColor = SITE_COLOR_CORP_BOOKMARK.GetRGBA()
    innerColor = INNER_ICON_COLOR.GetRGBA()
    innerIconResPath = 'res:/UI/Texture/Icons/38_16_257.png'
    outerTextures = ('res:/UI/Texture/classes/SensorSuite/bracket_bookmark_corp_1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_bookmark_corp_2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_bookmark_corp_3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_bookmark_corp_4.png')

    def GetCaptionText(self):
        return self.data.GetName()


class BookmarkHandler(SiteHandler):
    siteType = BOOKMARK
    filterIconPath = 'res:/UI/Texture/Icons/38_16_150.png'
    filterLabel = 'UI/Inflight/Scanner/PersonalSiteFilterLabel'
    color = SITE_COLOR_BOOKMARK

    def __init__(self, sensorSuiteSvc, bookmarkSvc):
        SiteHandler.__init__(self)
        self.sensorSuiteSvc = sensorSuiteSvc
        self.bookmarkSvc = bookmarkSvc

    def GetSiteData(self, siteID, bookmark):
        return BookmarkSiteData(siteID, GetBookmarkPosition(bookmark), bookmark=bookmark)

    def GetSitesForSolarSystem(self, solarSystemID):
        bookmarks = self.bookmarkSvc.GetMyBookmarks()
        return {bmID:(bm,) for bmID, bm in bookmarks.iteritems() if bm.locationID == solarSystemID}

    def IsVisible(self, siteData):
        return bookmarkVisibilityManager.IsFolderVisible(siteData.bookmark.folderID)

    def OnSitesUpdated(self, sites):
        for siteID, siteData in sites.iteritems():
            bm = self.bookmarkSvc.GetBookmark(siteData.bookmark.bookmarkID)
            siteData.bookmark = bm
            siteData.name = CleanText(bm.memo)
            bracket = self.siteController.spaceLocations.GetBracketBySiteID(siteID)
            if bracket:
                bracket.UpdateSiteLabel()
                bracket.UpdateSiteName(CleanText(bm.note))


class CorpBookmarkHandler(BookmarkHandler):
    siteType = CORP_BOOKMARK
    filterIconPath = 'res:/UI/Texture/Icons/38_16_257.png'
    filterLabel = 'UI/Inflight/Scanner/CorporateSiteFilterLabel'
    color = SITE_COLOR_CORP_BOOKMARK

    def GetSiteData(self, siteID, bookmark):
        return CorpBookmarkSiteData(siteID, GetBookmarkPosition(bookmark), bookmark=bookmark)

    def GetSitesForSolarSystem(self, solarSystemID):
        corpBookmarks = self.bookmarkSvc.GetCorpBookmarks()
        return {bmID:(bm,) for bmID, bm in corpBookmarks.iteritems() if bm.locationID == solarSystemID}
