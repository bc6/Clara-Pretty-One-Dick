#Embedded file name: carbon/client/script/util\cacheDirectoryLimitSvc.py
import service
import blue
import telemetry
import os
import stat
import datetime
import threading
import uthread

class AutoPrunedDirectory(object):

    def __init__(self, directory, maxDirectorySizeInMB, maxAgeInDays = None):
        self.directory = directory
        self.maxDirectorySizeInMB = maxDirectorySizeInMB
        self.maxAgeInDays = maxAgeInDays
        self.currentSize = 0
        self.lastChecked = None


def RemoveFileFromCache(filePath, lastAccessed = None):
    """
    Callback is used when a file is too old, or when a cache directory grows too much.
    """
    cacheSvc = sm.GetService('cacheDirectoryLimit')
    if lastAccessed is not None:
        cacheSvc.LogInfo('Removing ', filePath, ' from cache. It was last accessed:', lastAccessed)
    else:
        cacheSvc.LogInfo('Removing ', filePath, ' from cache.')
    os.remove(filePath)


@telemetry.ZONE_FUNCTION
def ProcessCacheDirectory(cacheSvc, rootPath, callback, d):
    """
    Callback for updating cache directory sizes.
    Only reprocesses a directory after a certain amount of time (5 minutes)
    
    Last Accessed time is either the creation time, or the last accessed time (to a resolution of 1 day)
    Updates to this number can be delayed by an hour after access
    """
    filesInDirectory = []
    now = datetime.datetime.now()
    five_minutes = datetime.timedelta(minutes=5)
    max_age = None if d.maxAgeInDays is None else datetime.timedelta(days=d.maxAgeInDays)
    if d.lastChecked is not None:
        if now - d.lastChecked < five_minutes:
            return
    d.lastChecked = now
    d.currentSize = 0
    for r, _, files in os.walk(rootPath):
        for f in files:
            fullpath = os.path.join(r, f)
            fileSize = os.stat(fullpath)[stat.ST_SIZE]
            lastAccessed = datetime.datetime.fromtimestamp(os.path.getmtime(fullpath))
            if max_age is not None and now - lastAccessed > max_age and callback is not None:
                callback(fullpath, lastAccessed)
            else:
                d.currentSize += fileSize
                filesInDirectory.append((lastAccessed, fileSize, fullpath))

    currentSize = d.currentSize
    maxSize = d.maxDirectorySizeInMB * 1024 * 1024
    if currentSize > maxSize:
        cacheSvc.LogNotice('Cache Directory', d.directory, 'is over the allocated file size (', d.maxDirectorySizeInMB, 'MB, currently', currentSize / 1048576.0, 'MB)')
        if callback is not None:
            filesInDirectory.sort(reverse=True)
            while currentSize > maxSize:
                fileToDelete = filesInDirectory.pop()
                if now - fileToDelete[0] < five_minutes:
                    break
                callback(fileToDelete[2], fileToDelete[0])
                currentSize -= fileToDelete[1]

    else:
        cacheSvc.LogInfo('Cache Directory', d.directory, 'is currently', currentSize / 1048576.0, 'MB (max', d.maxDirectorySizeInMB, 'MB)')


def SetUpDirectorySpy(cacheSvc, rootPath, func, d):
    """
    This has to be done in a function to make sure that the closure works correctly.
    """
    cacheSvc.LogNotice('Setting up cache directory watch on', rootPath)

    def FilesChangedClosure():

        def ProcessDirectoryInThreadClosure():
            ProcessCacheDirectory(cacheSvc, rootPath, func, d)

        now = datetime.datetime.now()
        five_minutes = datetime.timedelta(minutes=5)
        if d.lastChecked is not None:
            if now - d.lastChecked < five_minutes:
                return
        thread = threading.Thread(target=ProcessDirectoryInThreadClosure)
        thread.start()

    try:
        blue.pyos.SpyDirectory(rootPath, FilesChangedClosure)
    except WindowsError:
        pass


class CacheDirectoryLimitService(service.Service):
    """
    Used for accessing the cache directory (cache:/) and controlling the size of that directory and sub-directories on the disk
    """
    __guid__ = 'svc.cacheDirectoryLimit'
    __exportedcalls__ = {'PruneCache': {'role': service.ROLE_ANY},
     'RegisterCacheDirectory': {'role': service.ROLE_ANY}}

    def __init__(self):
        service.Service.__init__(self)

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        cacheDir = blue.paths.ResolvePath(u'cache:/')
        self.autoPruneDirectories = [AutoPrunedDirectory('Avatars', 1024, 5)]
        for d in self.autoPruneDirectories:
            rootPath = os.path.join(cacheDir, d.directory)
            SetUpDirectorySpy(self, rootPath, RemoveFileFromCache, d)

        self.PruneCache()

    def PruneCache(self):
        """
        Prune files from the cache folders that are watched immediately
        Starts a new tasklet
        """
        uthread.new(self.PruneCache_t)

    def PruneCache_t(self):
        """
        Prune files from the cache folders that are watched immediately
        """
        cacheDir = blue.paths.ResolvePath(u'cache:/')
        for d in self.autoPruneDirectories:
            rootPath = os.path.join(cacheDir, d.directory)
            uthread.CallOnThread(ProcessCacheDirectory, args=(self,
             rootPath,
             RemoveFileFromCache,
             d))

    def RegisterCacheDirectory(self, directory, maxSize, maxLastAccessedAgeInDays = None):
        """
        Register a directory in the cache with a maximum size in MB, and the maximum amount of time
        that files are kept around if they are not accessed.
        
        Any cache files that are added to this, must be updated when accessed using os.utime(filePath, None)
        """
        for d in self.autoPruneDirectories:
            if d.directory == directory:
                d.maxDirectorySizeInMB = maxSize
                d.maxAgeInDays = maxLastAccessedAgeInDays
                return

        cacheDir = blue.paths.ResolvePath(u'cache:/')
        rootPath = os.path.join(cacheDir, directory)
        d = AutoPrunedDirectory(directory, maxSize, maxLastAccessedAgeInDays)
        self.autoPruneDirectories.append(d)
        SetUpDirectorySpy(self, rootPath, RemoveFileFromCache, d)
