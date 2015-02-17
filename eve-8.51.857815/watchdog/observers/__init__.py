#Embedded file name: watchdog/observers\__init__.py
"""
:module: watchdog.observers
:synopsis: Observer that picks a native implementation if available.
:author: yesudeep@google.com (Yesudeep Mangalapilly)


Classes
=======
.. autoclass:: Observer
   :members:
   :show-inheritance:
   :inherited-members:

You can also import platform specific classes directly and use it instead
of :class:`Observer`.  Here is a list of implemented observer classes.:

============== ================================ ==============================
Class          Platforms                        Note
============== ================================ ==============================
|Inotify|      Linux 2.6.13+                    ``inotify(7)`` based observer
|FSEvents|     Mac OS X                         FSEvents based observer
|Kqueue|       Mac OS X and BSD with kqueue(2)  ``kqueue(2)`` based observer
|WinApi|       MS Windows                       Windows API-based observer
|Polling|      Any                              fallback implementation
============== ================================ ==============================

.. |Inotify|     replace:: :class:`.inotify.InotifyObserver`
.. |FSEvents|    replace:: :class:`.fsevents.FSEventsObserver`
.. |Kqueue|      replace:: :class:`.kqueue.KqueueObserver`
.. |WinApi|      replace:: :class:`.read_directory_changes.WindowsApiObserver`
.. |WinApiAsync| replace:: :class:`.read_directory_changes_async.WindowsApiAsyncObserver`
.. |Polling|     replace:: :class:`.polling.PollingObserver`

"""
from watchdog.utils.importlib2 import import_module
OBS_PROVIDERS = (('inotify', 'InotifyObserver'),
 ('fsevents', 'FSEventsObserver'),
 ('kqueue', 'KqueueObserver'),
 ('read_directory_changes_async', 'WindowsApiAsyncObserver'),
 ('read_directory_changes', 'WindowsApiObserver'),
 ('polling', 'PollingObserver'))

def _lookup_obs():
    c = None
    for mod, cls in OBS_PROVIDERS:
        m_name = 'watchdog.observers.%s' % mod
        try:
            c = import_module(cls, m_name)
        except (ImportError, AttributeError):
            continue

        return c


Observer = _lookup_obs()
