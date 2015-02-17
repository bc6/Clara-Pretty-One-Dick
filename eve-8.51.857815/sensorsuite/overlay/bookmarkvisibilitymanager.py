#Embedded file name: sensorsuite/overlay\bookmarkvisibilitymanager.py
import logging
from carbon.common.script.util.timerstuff import AutoTimer
logger = logging.getLogger(__name__)
FOLDER_VISIBILITY_SETTING = 'sensor_overlay_bookmark_folder_visibility'

class BookmarkFolderVisibilityManager:

    def __init__(self):
        self.bookmarkFolderIdsHiddenFromSensorOverlay = None

    def LoadFolderVisibility(self):
        logger.debug('Loading folder visibility settings')
        settingsString = sm.GetService('characterSettings').Get(FOLDER_VISIBILITY_SETTING) or ''
        self.bookmarkFolderIdsHiddenFromSensorOverlay = set({int(folderID) for folderID in settingsString.split(',') if folderID})

    def PersistVisibleFolders(self):
        logger.debug('Persisting folder visibility settings')
        settingsString = ','.join([ str(folderID) for folderID in self.bookmarkFolderIdsHiddenFromSensorOverlay ])
        sm.GetService('characterSettings').Save(FOLDER_VISIBILITY_SETTING, settingsString)
        self.persistVisibleFoldersTimer = None

    def IsFolderVisible(self, folderID):
        if self.bookmarkFolderIdsHiddenFromSensorOverlay is None:
            self.LoadFolderVisibility()
        return folderID not in self.bookmarkFolderIdsHiddenFromSensorOverlay

    def SetFolderVisibility(self, folderID, isVisible):
        logger.debug('Setting bookmark folder %s visibility to %s', folderID, isVisible)
        if isVisible:
            self.bookmarkFolderIdsHiddenFromSensorOverlay.discard(folderID)
        else:
            self.bookmarkFolderIdsHiddenFromSensorOverlay.add(folderID)
        self.persistVisibleFoldersTimer = AutoTimer(5000, self.PersistVisibleFolders)


bookmarkVisibilityManager = BookmarkFolderVisibilityManager()
