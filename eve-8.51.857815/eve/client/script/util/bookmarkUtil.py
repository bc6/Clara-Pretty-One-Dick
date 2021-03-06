#Embedded file name: eve/client/script/util\bookmarkUtil.py
import localization
import uiutil
from collections import defaultdict
BOOKMARK_RIGHTCLICK_GROUPING_THRESHOLD = 8

def GetMenuForBookmarks(bookmarks):
    CelestialMenu = lambda bookmark: sm.GetService('menu').CelestialMenu(bookmark.itemID, None, None, 0, None, None, bookmark)
    menu = []
    for bookmark in bookmarks:
        hint, comment = sm.GetService('addressbook').UnzipMemo(bookmark.memo)
        hint = hint if len(hint) < 25 else hint[:25]
        menu.append((hint, ('isDynamic', CelestialMenu, (bookmark,))))

    menu = localization.util.Sort(menu, key=lambda x: x[0])
    return menu


def GetFolderedMenu(bookmarksByFolder, folders, label, isSubMenu = True):
    ret = []
    nonFolderedBookmarks = []
    for folderID, bookmarks in bookmarksByFolder.iteritems():
        if folderID is None:
            continue
        subMenu = GetMenuForBookmarks(bookmarks)
        try:
            folderName = folders[folderID].folderName
        except KeyError:
            nonFolderedBookmarks.extend(GetMenuForBookmarks(bookmarks))
            continue

        ret.append((folderName, subMenu))

    ret = localization.util.Sort(ret, key=lambda x: x[0])
    nonFolderedBookmarks.extend(GetMenuForBookmarks(bookmarksByFolder[None]))
    ret.extend(nonFolderedBookmarks)
    if isSubMenu:
        ret = [None, (label, ret), None]
    else:
        ret = [None, (label, lambda *args: None)] + ret + [None]
    return ret


def GetBookmarkMenuForSystem(bookmarks, folders):
    ret = []
    validBookmarks = [ bookmark for bookmark in bookmarks.itervalues() if bookmark.locationID == session.locationid ]
    bookmarksByOwnerByFolder = defaultdict(lambda : defaultdict(set))
    for bookmark in validBookmarks:
        bookmarksByOwnerByFolder[bookmark.ownerID][bookmark.folderID].add(bookmark)

    if session.charid in bookmarksByOwnerByFolder:
        ret.extend(GetFolderedMenu(bookmarksByOwnerByFolder[session.charid], folders, uiutil.MenuLabel('UI/PeopleAndPlaces/PersonalLocations'), isSubMenu=False))
    if session.corpid in bookmarksByOwnerByFolder:
        bookmarksByFolder = bookmarksByOwnerByFolder[session.corpid]
        entryLength = len(bookmarksByFolder)
        if None in bookmarksByFolder:
            entryLength += len(bookmarksByFolder[None]) - 1
        ret.extend(GetFolderedMenu(bookmarksByOwnerByFolder[session.corpid], folders, localization.GetByLabel('UI/PeopleAndPlaces/CorporationLocations'), isSubMenu=entryLength > BOOKMARK_RIGHTCLICK_GROUPING_THRESHOLD))
    return ret


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('bookmarkUtil', globals())
