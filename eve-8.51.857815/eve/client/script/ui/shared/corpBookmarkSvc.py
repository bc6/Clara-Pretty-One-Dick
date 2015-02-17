#Embedded file name: eve/client/script/ui/shared\corpBookmarkSvc.py
import blue
import bookmarkUtil
from service import Service

class CorpBookmarkSvc(Service):
    __guid__ = 'svc.corpBookmarkSvc'

    def Run(self, memStream = None):
        Service.Run(self, memStream)
        self.remoteCorpBookmarkMgr = sm.RemoteSvc('corpBookmarkMgr')
        self.lastUpdateTime = None
        self.getFromBookmarkID = None
        self.GetBookmarks()

    def CopyBookmarks(self, bookmarkIDs):
        newBookmarks, message = self.remoteCorpBookmarkMgr.CopyBookmarks(bookmarkIDs)
        if message is not None:
            eve.Message(*message)
        self.bookmarkCache.update(newBookmarks)

    def DeleteBookmarks(self, bookmarkIDs):
        deletedBookmarkIDs = self.remoteCorpBookmarkMgr.DeleteBookmarks(bookmarkIDs)
        for bookmarkID in deletedBookmarkIDs:
            try:
                del self.bookmarkCache[bookmarkID]
            except KeyError:
                self.LogError('Failed to delete bookmark locally', bookmarkID)
                sys.exc_clear()

    def PickOutCorpBookmarksAndDelete(self, bookmarkIDs):
        isDirector = session.corprole & const.corpRoleDirector == const.corpRoleDirector
        corpBookmarkIDs = set()
        for bookmarkID, bookmark in self.bookmarkCache.iteritems():
            if bookmarkID not in bookmarkIDs:
                continue
            if not isDirector and bookmark.creatorID != session.charid:
                raise UserError('CantDeleteCorpBookmarksNotDirector')
            corpBookmarkIDs.add(bookmark.bookmarkID)

        self.LogInfo('Deleting corp bookmarks', corpBookmarkIDs)
        self.DeleteBookmarks(corpBookmarkIDs)
        return corpBookmarkIDs

    def GetBookmarks(self):
        if self.lastUpdateTime is None or blue.os.GetWallclockTime() - self.lastUpdateTime > 5 * const.MIN:
            self.bookmarkCache, self.folders = self.remoteCorpBookmarkMgr.GetBookmarks()
            self.lastUpdateTime = blue.os.GetWallclockTime()
        return self.bookmarkCache

    def GetBookmark(self, bookmarkID):
        return self.bookmarkCache[bookmarkID]

    def CreateFolder(self, folderName):
        folder = self.remoteCorpBookmarkMgr.CreateFolder(folderName)
        self.folders[folder.folderID] = folder

    def MoveBookmarksToFolder(self, folderID, bookmarkIDs):
        rows = self.remoteCorpBookmarkMgr.MoveBookmarksToFolder(folderID, bookmarkIDs)
        for row in rows:
            try:
                self.bookmarkCache[row.bookmarkID].folderID = row.folderID
            except KeyError:
                sys.exc_clear()

    def UpdateBookmark(self, bookmarkID, memo, note):
        bookmark = self.remoteCorpBookmarkMgr.UpdateBookmark(bookmarkID, memo, note)
        if bookmark is not None:
            self.bookmarkCache[bookmark.bookmarkID] = bookmark

    def GetBookmarkMenuForSystem(self):
        return bookmarkUtil.GetBookmarkMenuForSystem(self.bookmarkCache, self.folders)
