#Embedded file name: watchdog/observers\read_directory_changes_async.py
from __future__ import with_statement
raise ImportError('Not implemented yet.')
from watchdog.utils import platform
if platform.is_windows():
    import threading
    from watchdog.observers.api import EventEmitter, BaseObserver, DEFAULT_OBSERVER_TIMEOUT, DEFAULT_EMITTER_TIMEOUT

    class WindowsApiAsyncEmitter(EventEmitter):
        """
        Platform-independent emitter that polls a directory to detect file
        system changes.
        """

        def __init__(self, event_queue, watch, timeout = DEFAULT_EMITTER_TIMEOUT):
            EventEmitter.__init__(self, event_queue, watch, timeout)
            self._lock = threading.Lock()

        def queue_events(self, timeout):
            with self._lock:
                pass


    class WindowsApiAsyncObserver(BaseObserver):
        """
        Observer thread that schedules watching directories and dispatches
        calls to event handlers.
        """

        def __init__(self, timeout = DEFAULT_OBSERVER_TIMEOUT):
            BaseObserver.__init__(self, emitter_class=WindowsApiAsyncEmitter, timeout=timeout)
