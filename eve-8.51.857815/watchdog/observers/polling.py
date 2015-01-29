#Embedded file name: watchdog/observers\polling.py
"""
:module: watchdog.observers.polling
:synopsis: Polling emitter implementation.
:author: yesudeep@google.com (Yesudeep Mangalapilly)

Classes
-------
.. autoclass:: PollingEmitter
   :members:
   :show-inheritance:
"""
from __future__ import with_statement
import time
import threading
from watchdog.utils.dirsnapshot import DirectorySnapshot, DirectorySnapshotDiff
from watchdog.observers.api import EventEmitter, BaseObserver, DEFAULT_OBSERVER_TIMEOUT, DEFAULT_EMITTER_TIMEOUT
from watchdog.events import DirMovedEvent, DirDeletedEvent, DirCreatedEvent, DirModifiedEvent, FileMovedEvent, FileDeletedEvent, FileCreatedEvent, FileModifiedEvent

class PollingEmitter(EventEmitter):
    """
    Platform-independent emitter that polls a directory to detect file
    system changes.
    """

    def __init__(self, event_queue, watch, timeout = DEFAULT_EMITTER_TIMEOUT):
        EventEmitter.__init__(self, event_queue, watch, timeout)
        self._snapshot = DirectorySnapshot(watch.path, watch.is_recursive)
        self._lock = threading.Lock()

    def on_thread_stop(self):
        with self._lock:
            self._snapshot = None

    def queue_events(self, timeout):
        time.sleep(timeout)
        with self._lock:
            if not self._snapshot:
                return
            new_snapshot = DirectorySnapshot(self.watch.path, self.watch.is_recursive)
            events = DirectorySnapshotDiff(self._snapshot, new_snapshot)
            self._snapshot = new_snapshot
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


class PollingObserver(BaseObserver):
    """
    Observer thread that schedules watching directories and dispatches
    calls to event handlers.
    """

    def __init__(self, timeout = DEFAULT_OBSERVER_TIMEOUT):
        BaseObserver.__init__(self, emitter_class=PollingEmitter, timeout=timeout)
