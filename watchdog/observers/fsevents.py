#Embedded file name: watchdog/observers\fsevents.py
"""
:module: watchdog.observers.fsevents
:synopsis: FSEvents based emitter implementation.
:author: yesudeep@google.com (Yesudeep Mangalapilly)
:platforms: Mac OS X
"""
from __future__ import with_statement
from watchdog.utils import platform
if not platform.is_darwin():
    raise ImportError
import sys
import threading
import unicodedata
import _watchdog_fsevents as _fsevents
from watchdog.events import FileDeletedEvent, FileModifiedEvent, FileCreatedEvent, FileMovedEvent, DirDeletedEvent, DirModifiedEvent, DirCreatedEvent, DirMovedEvent
from watchdog.utils.dirsnapshot import DirectorySnapshot
from watchdog.observers.api import BaseObserver, EventEmitter, DEFAULT_EMITTER_TIMEOUT, DEFAULT_OBSERVER_TIMEOUT

class FSEventsEmitter(EventEmitter):
    """
    Mac OS X FSEvents Emitter class.
    
    :param event_queue:
        The event queue to fill with events.
    :param watch:
        A watch object representing the directory to monitor.
    :type watch:
        :class:`watchdog.observers.api.ObservedWatch`
    :param timeout:
        Read events blocking timeout (in seconds).
    :type timeout:
        ``float``
    """

    def __init__(self, event_queue, watch, timeout = DEFAULT_EMITTER_TIMEOUT):
        EventEmitter.__init__(self, event_queue, watch, timeout)
        self._lock = threading.Lock()
        self.snapshot = DirectorySnapshot(watch.path, watch.is_recursive)

    def on_thread_stop(self):
        _fsevents.remove_watch(self.watch)
        _fsevents.stop(self)

    def queue_events(self, timeout):
        with self._lock:
            if not self.watch.is_recursive and self.watch.path not in self.pathnames:
                return
            new_snapshot = DirectorySnapshot(self.watch.path, self.watch.is_recursive)
            events = new_snapshot - self.snapshot
            self.snapshot = new_snapshot
            for src_path in events.files_deleted:
                self.queue_event(FileDeletedEvent(src_path))

            for src_path in events.files_modified:
                self.queue_event(FileModifiedEvent(src_path))

            for src_path in events.files_created:
                self.queue_event(FileCreatedEvent(src_path))

            for src_path, dest_path in events.files_moved:
                self.queue_event(FileMovedEvent(src_path, dest_path))

            for src_path in events.dirs_deleted:
                self.queue_event(DirDeletedEvent(src_path))

            for src_path in events.dirs_modified:
                self.queue_event(DirModifiedEvent(src_path))

            for src_path in events.dirs_created:
                self.queue_event(DirCreatedEvent(src_path))

            for src_path, dest_path in events.dirs_moved:
                self.queue_event(DirMovedEvent(src_path, dest_path))

    def run(self):
        try:

            def callback(pathnames, flags, emitter = self):
                emitter.queue_events(emitter.timeout)

            self.pathnames = [self.watch.path]
            _fsevents.add_watch(self, self.watch, callback, self.pathnames)
            _fsevents.read_events(self)
        except Exception as e:
            pass


class FSEventsObserver(BaseObserver):

    def __init__(self, timeout = DEFAULT_OBSERVER_TIMEOUT):
        BaseObserver.__init__(self, emitter_class=FSEventsEmitter, timeout=timeout)

    def schedule(self, event_handler, path, recursive = False):
        try:
            str_class = unicode
        except NameError:
            str_class = str

        if isinstance(path, str_class):
            path = unicodedata.normalize('NFC', path)
            if sys.version_info < (3,):
                path = path.encode('utf-8')
        return BaseObserver.schedule(self, event_handler, path, recursive)
