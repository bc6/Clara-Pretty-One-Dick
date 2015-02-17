#Embedded file name: codereload\spy.py
"""
Code reloading integration.

This implements the ability to detect changes to source code and automatically
reload files when this happens.  The actual reloading logic is implemented in
the :mod:`codereload.xreload` module.

**Note**: At this time this module only supports the Windows platform.
"""
import inspect
import logging
import os
import sys
import time
import osutils
import threadutils
import uthread2 as uthread
import win32api
import zipfileutils
from .xreload import xreload
log = logging.getLogger(__name__)

class FolderReloaderSpy(object):
    """Spy on folder changes using Win32 notification mechanism and
    do automatic recompile and reload.
    
    - Register for when a file reloads by connecting to ``on_file_reloaded``.
    - Register for when a file fails to reload by connecting to
      ``on_file_reload_failed``.
    """

    def __init__(self, waitables, paths, translationPaths = None):
        self.on_file_reloaded = threadutils.Signal('(filename, module)')
        self.on_file_reload_failed = threadutils.Signal('(filename, exc_info)')
        self.runningCheckAt = 0
        self.startedAt = int(time.time())
        self.processed = {}
        self.waitables = waitables
        self.translationPaths = translationPaths or []
        if isinstance(paths, basestring):
            paths = [paths]
        self.handles = {}
        paths = map(os.path.abspath, paths)
        commonprefix = os.path.commonprefix(paths)
        if commonprefix:
            paths = [commonprefix]
        for path in paths:
            if not os.path.exists(path):
                log.warn("SpyFolder: Can't spy on non-existing folder %s" % path)
                continue
            handle = win32api.FindFirstChangeNotification(path, True, win32api.FILE_NOTIFY_CHANGE_LAST_WRITE)
            if handle == win32api.INVALID_HANDLE_VALUE:
                log.warn('SpyFolder: got invalid handle for  %s' % path)
                continue
            waitables.InsertHandle(handle, self)
            self.handles[handle] = path
            log.info('AutoCompiler: Now spying on %s using handle %s.', path, handle)

    def __del__(self):
        for handle in self.handles.keys():
            win32api.FindCloseChangeNotification(handle)

    def on_object_signaled(self, handle, abandoned):
        if abandoned:
            return
        win32api.FindNextChangeNotification(handle)
        self.process_folder(self.handles[handle])

    OnObjectSignaled = on_object_signaled

    def poll_for_changes(self):
        """If any file has been modified in the folder or subfolders, a recompile is triggered."""
        for handle, path in self.handles.items():
            if win32api.WaitForSingleObject(handle):
                win32api.FindNextChangeNotification(handle)
                self.process_folder(path)

    PollForChanges = poll_for_changes

    def reload_file(self, filename):
        """Reloads a file module given a file name."""
        filename = os.path.abspath(filename)
        filenameWoExt, extension = os.path.splitext(filename)
        filenameTargets = [filenameWoExt]
        for mapFrom, mapTo in self.translationPaths:
            if filenameWoExt.startswith(mapFrom):
                filenameTargets.append(filenameWoExt.replace(mapFrom, mapTo))

        for mname, module in sys.modules.items():
            if not module or not hasattr(module, '__file__'):
                continue
            try:
                modulefile = os.path.abspath(inspect.getfile(module)).rsplit('.', 1)[0]
            except TypeError:
                continue

            if modulefile in filenameTargets:
                with open(filename) as stream:
                    source = stream.read() + '\n'
                log.info('Compiling %s using source %s', module.__name__, filename)
                code = compile(source, filename, 'exec')
                log.info('Reloading %s', module)
                xreload(module, code)
                self.on_file_reloaded.emit(filename, module)

    ReloadFile = reload_file

    def process_folder(self, path):
        """Search the folder and subfolders for out of date .py files and compile
        them. If the module is loaded, the running code is fixed accordingly
        """
        toProcess = []
        filenames = []
        for modulename, moduleinfo in sys.modules.items():
            try:
                filenames.append(moduleinfo.__file__)
            except AttributeError:
                continue
            except ImportError as e:
                log.error('unable to monitor %s due to import error: %s', modulename, str(e))
                continue

        for filename in filenames:
            if not filename.lower().endswith('.py'):
                continue
            try:
                sourceFileDate = osutils.get_modified_time(filename)
            except WindowsError:
                if not zipfileutils.is_inside_zipfile(filename):
                    log.exception('Failed to find %s', filename)
                continue

            lastCompile = self.processed.get(filename, self.startedAt)
            if sourceFileDate > lastCompile:
                toProcess.append(filename)
                self.processed[filename] = sourceFileDate

        if toProcess:
            log.info('Reloading: %s', str(toProcess))
            for sourceFile in toProcess:
                try:
                    tstart = time.clock()
                    self.reload_file(sourceFile)
                    tdiff = time.clock() - tstart
                    log.info('Took %.3fs to reload %s', tdiff, os.path.basename(sourceFile))
                except Exception:
                    log.exception("ReloadFile failed for '%s'.", sourceFile)
                    self.on_file_reload_failed.emit(sourceFile, sys.exc_info())

    ProcessFolder = process_folder


def __reload_update__(old_module_dict):
    """Just to illustrate the callback function. ``old_module_dict`` is (a copy)
    of the module dict before reloading.
    """
    log.info('autocompile module got reloaded. old dict keys: %s', old_module_dict.keys())


def spy(paths, delay = 0.5):
    """Spy on vanilla python module folders for autoreloads.
    
    :param paths: Path or list of paths.
    :param delay: Time to wait before checking for changes.
      Shorter is less responsive, longer takes less resources.
    :return: :class:`FolderReloaderSpy` instance and polling :class:`uthread2.Tasklet`.
    """
    if isinstance(paths, basestring):
        paths = [paths]
    waitables = win32api.Waitables()
    folderspy = FolderReloaderSpy(waitables, paths)
    tasklet = uthread.start_tasklet(_poll_spy, folderspy, delay)
    return (folderspy, tasklet)


def _poll_spy(spyfolder, delay):
    while True:
        spyfolder.waitables.Wait(0)
        uthread.sleep(delay)
