#Embedded file name: remotefilecache\__init__.py
__author__ = 'snorri.sturluson'
import logging
import os
import blue
import uthread2
import walk
from backgrounddownloadmanager import BackgroundDownloadManager
log = logging.getLogger('remotefilecache')

def get_default_cache_folder():
    """
    Returns a default path for where to cache res files on the local file system
    
    Note that an application may wish to use another location but this method is
    provided as a convenient sensible default for set_cache_folder. 
    """
    if blue.win32.IsTransgaming():
        program_data_folder = 'p:\\Local Settings\\Application Data'
    else:
        program_data_folder = os.getenv('ProgramData', '')
    if not program_data_folder:
        program_data_folder = 'C:\\'
    folder = os.path.join(program_data_folder, 'CCP', 'EVE', 'SharedCache', 'ResFiles')
    return folder


def prepare_for_package_tests():
    blue.paths.RegisterFileSystemBeforeLocal('Remote')
    set_cache_folder(get_default_cache_folder())
    prepare(os.path.join(os.path.dirname(__file__), '..', '..', 'eve', 'client', 'resfileindex.txt'))
    blue.resMan.substituteBlackForRed = True


def set_cache_folder(location):
    blue.remoteFileCache.cacheFolder = location
    for i in xrange(256):
        folder_name = os.path.join(location, '%2.2x' % i)
        if not os.path.isdir(folder_name):
            os.makedirs(folder_name)


def prepare(index, server = 'http://res.eveprobe.ccpgames.com/', prefix = ''):
    blue.remoteFileCache.server = server
    blue.remoteFileCache.prefix = prefix
    blue.remoteFileCache.backupServer = 'http://eve-probe-res.s3-website-eu-west-1.amazonaws.com/'
    if blue.paths.exists(index):
        log.debug('Loading index from %s' % index)
        stream = blue.paths.open(index, 'r')
        blue.remoteFileCache.SetFileIndex(stream.Read())
    else:
        log.debug('Downloading index %s from %s' % (index, server))
        succeeded = blue.remoteFileCache.DownloadFileIndex(index)
        if succeeded:
            log.debug('Index downloaded successfully')
        else:
            raise RuntimeError('Index download failed')


def gather_files_to_prefetch(folder, file_set):
    """
    Gathers files to prefetch from the given folder. Files that do not exist
    locally are added to the file_set.
    """
    for path, dirs, files in walk.walk(folder):
        for f in files:
            filename = path + '/' + f
            if not blue.paths.FileExistsLocally(filename):
                file_set.add(filename)


def add_file_if_needs_download(file_set, filename):
    if blue.remoteFileCache.FileExists(filename) and not blue.paths.FileExistsLocally(filename):
        file_set.add(filename)


def gather_files_conditionally_to_prefetch(folder, condition, file_set, dependency_map):
    """
    Gathers files to prefetch from the given folder. Files that do not exist
    locally are added to the file_set.
    """
    for path, dirs, files in walk.walk(folder):
        for f in files:
            if not condition(f):
                continue
            filename = path + '/' + f
            add_file_if_needs_download(file_set, filename)
            dependencies = dependency_map.get(filename, [])
            for each in dependencies:
                add_file_if_needs_download(filename, each)


def prefetch_single_file(filename):
    """
    Fetches a single file.
    
    Note that files with the .red extension are fetched as .black files,
    as the CDN is usually only populated with .black files.
    
    Yields until the download has finished.
    """
    basename, extension = os.path.splitext(filename)
    if blue.resMan.substituteBlackForRed and extension == '.red':
        filename = basename + '.black'
    if blue.remoteFileCache.FileExists(filename) and not blue.paths.FileExistsLocally(filename):
        blue.paths.GetFileContentsWithYield(filename)


def prefetch_files(file_set):
    """
    Prefetches all the files in the given set, blocking the calling tasklet
    until all files have been downloaded.
    
    Yields until all downloads have finished.
    """
    uthread2.map(prefetch_single_file, file_set)


def prefetch_folder(folder):
    """
    Prefetches all files in the given folder.
    
    Yields until all downloads have finished.
    """
    file_set = set()
    gather_files_to_prefetch(folder, file_set)
    prefetch_files(file_set)


_bgdm = BackgroundDownloadManager()

def schedule(key, file_set):
    """
    Schedules a file set for background download. The key can be used to
    cancel the request, or change its priority.
    """
    _bgdm.schedule(key, file_set)


def cancel(key):
    """
    Cancels a previously scheduled file set (see schedule).
    """
    _bgdm.cancel(key)


def pull_to_front(key):
    """
    Pulls the scheduled request with the given key to the front of the queue.
    """
    _bgdm.pull_to_front(key)


def push_to_back(key):
    """
    Pushes the scheduled request with the given key to the back of the queue.
    """
    _bgdm.push_to_back(key)


def get_queue():
    """
    Gets the background download manager queue.
    """
    return _bgdm.sets


def pause():
    """
    Pauses the download manager queue - primarily intended for debugging use.
    """
    _bgdm.stop()


def resume():
    """
    Resumes processing of the download manager queue.
    """
    _bgdm.start()
