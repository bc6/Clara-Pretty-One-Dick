#Embedded file name: watchdog/observers\kqueue.py
"""
:module: watchdog.observers.kqueue
:synopsis: ``kqueue(2)`` based emitter implementation.
:author: yesudeep@google.com (Yesudeep Mangalapilly)
:platforms: Mac OS X and BSD with kqueue(2).

.. WARNING:: kqueue is a very heavyweight way to monitor file systems.
             Each kqueue-detected directory modification triggers
             a full directory scan. Traversing the entire directory tree
             and opening file descriptors for all files will create
             performance problems. We need to find a way to re-scan
             only those directories which report changes and do a diff
             between two sub-DirectorySnapshots perhaps.

.. ADMONITION:: About ``select.kqueue`` and Python versions

    * Python 2.5 does not ship with ``select.kqueue``
    * Python 2.6 ships with a broken ``select.kqueue`` that cannot take
      multiple events in the event list passed to ``kqueue.control``.
    * Python 2.7 ships with a working ``select.kqueue``
      implementation.

    I have backported the Python 2.7 implementation to Python 2.5 and 2.6
    in the ``select_backport`` package available on PyPI.

.. ADMONITION:: About OS X performance guidelines

    Quote from the `Mac OS X File System Performance Guidelines`_:

        "When you only want to track changes on a file or directory, be sure to
        open it using the ``O_EVTONLY`` flag. This flag prevents the file or
        directory from being marked as open or in use. This is important
        if you are tracking files on a removable volume and the user tries to
        unmount the volume. With this flag in place, the system knows it can
        dismiss the volume. If you had opened the files or directories without
        this flag, the volume would be marked as busy and would not be
        unmounted."

    ``O_EVTONLY`` is defined as ``0x8000`` in the OS X header files.
    More information here: http://www.mlsite.net/blog/?p=2312

Classes
-------
.. autoclass:: KqueueEmitter
   :members:
   :show-inheritance:

Collections and Utility Classes
-------------------------------
.. autoclass:: KeventDescriptor
   :members:
   :show-inheritance:

.. autoclass:: KeventDescriptorSet
   :members:
   :show-inheritance:

.. _Mac OS X File System Performance Guidelines: http://developer.apple.com/library/ios/#documentation/Performance/Conceptual/FileSystem/Articles/TrackingChanges.html#//apple_ref/doc/uid/20001993-CJBJFIDD

"""
from __future__ import with_statement
from watchdog.utils import platform
if not platform.is_bsd() and not platform.is_darwin():
    raise ImportError
import threading
import errno
import sys
import stat
import os
if sys.version_info < (2, 7, 0):
    import select_backport as select
else:
    import select
from pathtools.path import absolute_path
from watchdog.observers.api import BaseObserver, EventEmitter, DEFAULT_OBSERVER_TIMEOUT, DEFAULT_EMITTER_TIMEOUT
from watchdog.utils.dirsnapshot import DirectorySnapshot
from watchdog.events import DirMovedEvent, DirDeletedEvent, DirCreatedEvent, DirModifiedEvent, FileMovedEvent, FileDeletedEvent, FileCreatedEvent, FileModifiedEvent, EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED
MAX_EVENTS = 4096
O_EVTONLY = 32768
if platform.is_darwin():
    WATCHDOG_OS_OPEN_FLAGS = O_EVTONLY
else:
    WATCHDOG_OS_OPEN_FLAGS = os.O_RDONLY | os.O_NONBLOCK
WATCHDOG_KQ_FILTER = select.KQ_FILTER_VNODE
WATCHDOG_KQ_EV_FLAGS = select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR
WATCHDOG_KQ_FFLAGS = select.KQ_NOTE_DELETE | select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_ATTRIB | select.KQ_NOTE_LINK | select.KQ_NOTE_RENAME | select.KQ_NOTE_REVOKE

def is_deleted(kev):
    """Determines whether the given kevent represents deletion."""
    return kev.fflags & select.KQ_NOTE_DELETE


def is_modified(kev):
    """Determines whether the given kevent represents modification."""
    fflags = kev.fflags
    return fflags & select.KQ_NOTE_EXTEND or fflags & select.KQ_NOTE_WRITE


def is_attrib_modified(kev):
    """Determines whether the given kevent represents attribute modification."""
    return kev.fflags & select.KQ_NOTE_ATTRIB


def is_renamed(kev):
    """Determines whether the given kevent represents movement."""
    return kev.fflags & select.KQ_NOTE_RENAME


class KeventDescriptorSet(object):
    """
    Thread-safe kevent descriptor collection.
    """

    def __init__(self):
        self._descriptors = set()
        self._descriptor_for_path = dict()
        self._descriptor_for_fd = dict()
        self._kevents = list()
        self._lock = threading.Lock()

    @property
    def kevents(self):
        """
        List of kevents monitored.
        """
        with self._lock:
            return self._kevents

    @property
    def paths(self):
        """
        List of paths for which kevents have been created.
        """
        with self._lock:
            return list(self._descriptor_for_path.keys())

    def get_for_fd(self, fd):
        """
        Given a file descriptor, returns the kevent descriptor object
        for it.
        
        :param fd:
            OS file descriptor.
        :type fd:
            ``int``
        :returns:
            A :class:`KeventDescriptor` object.
        """
        with self._lock:
            return self._descriptor_for_fd[fd]

    def get(self, path):
        """
        Obtains a :class:`KeventDescriptor` object for the specified path.
        
        :param path:
            Path for which the descriptor will be obtained.
        """
        with self._lock:
            path = absolute_path(path)
            return self._get(path)

    def __contains__(self, path):
        """
        Determines whether a :class:`KeventDescriptor has been registered
        for the specified path.
        
        :param path:
            Path for which the descriptor will be obtained.
        """
        with self._lock:
            path = absolute_path(path)
            return self._has_path(path)

    def add(self, path, is_directory):
        """
        Adds a :class:`KeventDescriptor` to the collection for the given
        path.
        
        :param path:
            The path for which a :class:`KeventDescriptor` object will be
            added.
        :param is_directory:
            ``True`` if the path refers to a directory; ``False`` otherwise.
        :type is_directory:
            ``bool``
        """
        with self._lock:
            path = absolute_path(path)
            if not self._has_path(path):
                self._add_descriptor(KeventDescriptor(path, is_directory))

    def remove(self, path):
        """
        Removes the :class:`KeventDescriptor` object for the given path
        if it already exists.
        
        :param path:
            Path for which the :class:`KeventDescriptor` object will be
            removed.
        """
        with self._lock:
            path = absolute_path(path)
            if self._has_path(path):
                self._remove_descriptor(self._get(path))

    def clear(self):
        """
        Clears the collection and closes all open descriptors.
        """
        with self._lock:
            for descriptor in self._descriptors:
                descriptor.close()

            self._descriptors.clear()
            self._descriptor_for_fd.clear()
            self._descriptor_for_path.clear()
            self._kevents = []

    def _get(self, path):
        """Returns a kevent descriptor for a given path."""
        return self._descriptor_for_path[path]

    def _has_path(self, path):
        """Determines whether a :class:`KeventDescriptor` for the specified
        path exists already in the collection."""
        return path in self._descriptor_for_path

    def _add_descriptor(self, descriptor):
        """
        Adds a descriptor to the collection.
        
        :param descriptor:
            An instance of :class:`KeventDescriptor` to be added.
        """
        self._descriptors.add(descriptor)
        self._kevents.append(descriptor.kevent)
        self._descriptor_for_path[descriptor.path] = descriptor
        self._descriptor_for_fd[descriptor.fd] = descriptor

    def _remove_descriptor(self, descriptor):
        """
        Removes a descriptor from the collection.
        
        :param descriptor:
            An instance of :class:`KeventDescriptor` to be removed.
        """
        self._descriptors.remove(descriptor)
        del self._descriptor_for_fd[descriptor.fd]
        del self._descriptor_for_path[descriptor.path]
        self._kevents.remove(descriptor.kevent)
        descriptor.close()


class KeventDescriptor(object):
    """
    A kevent descriptor convenience data structure to keep together:
    
        * kevent
        * directory status
        * path
        * file descriptor
    
    :param path:
        Path string for which a kevent descriptor will be created.
    :param is_directory:
        ``True`` if the path refers to a directory; ``False`` otherwise.
    :type is_directory:
        ``bool``
    """

    def __init__(self, path, is_directory):
        self._path = absolute_path(path)
        self._is_directory = is_directory
        self._fd = os.open(path, WATCHDOG_OS_OPEN_FLAGS)
        self._kev = select.kevent(self._fd, filter=WATCHDOG_KQ_FILTER, flags=WATCHDOG_KQ_EV_FLAGS, fflags=WATCHDOG_KQ_FFLAGS)

    @property
    def fd(self):
        """OS file descriptor for the kevent descriptor."""
        return self._fd

    @property
    def path(self):
        """The path associated with the kevent descriptor."""
        return self._path

    @property
    def kevent(self):
        """The kevent object associated with the kevent descriptor."""
        return self._kev

    @property
    def is_directory(self):
        """Determines whether the kevent descriptor refers to a directory.
        
        :returns:
            ``True`` or ``False``
        """
        return self._is_directory

    def close(self):
        """
        Closes the file descriptor associated with a kevent descriptor.
        """
        try:
            os.close(self.fd)
        except OSError:
            pass

    @property
    def key(self):
        return (self.path, self.is_directory)

    def __eq__(self, descriptor):
        return self.key == descriptor.key

    def __ne__(self, descriptor):
        return self.key != descriptor.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return '<KeventDescriptor: path=%s, is_directory=%s>' % (self.path, self.is_directory)


class KqueueEmitter(EventEmitter):
    """
    kqueue(2)-based event emitter.
    
    .. ADMONITION:: About ``kqueue(2)`` behavior and this implementation
    
              ``kqueue(2)`` monitors file system events only for
              open descriptors, which means, this emitter does a lot of
              book-keeping behind the scenes to keep track of open
              descriptors for every entry in the monitored directory tree.
    
              This also means the number of maximum open file descriptors
              on your system must be increased **manually**.
              Usually, issuing a call to ``ulimit`` should suffice::
    
                  ulimit -n 1024
    
              Ensure that you pick a number that is larger than the
              number of files you expect to be monitored.
    
              ``kqueue(2)`` does not provide enough information about the
              following things:
    
              * The destination path of a file or directory that is renamed.
              * Creation of a file or directory within a directory; in this
                case, ``kqueue(2)`` only indicates a modified event on the
                parent directory.
    
              Therefore, this emitter takes a snapshot of the directory
              tree when ``kqueue(2)`` detects a change on the file system
              to be able to determine the above information.
    
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
        self._kq = select.kqueue()
        self._lock = threading.RLock()
        self._descriptors = KeventDescriptorSet()

        def walker_callback(path, stat_info, self = self):
            self._register_kevent(path, stat.S_ISDIR(stat_info.st_mode))

        self._snapshot = DirectorySnapshot(watch.path, watch.is_recursive, walker_callback)

    def _register_kevent(self, path, is_directory):
        """
        Registers a kevent descriptor for the given path.
        
        :param path:
            Path for which a kevent descriptor will be created.
        :param is_directory:
            ``True`` if the path refers to a directory; ``False`` otherwise.
        :type is_directory:
            ``bool``
        """
        try:
            self._descriptors.add(path, is_directory)
        except OSError as e:
            if e.errno == errno.ENOENT:
                pass
            else:
                raise

    def _unregister_kevent(self, path):
        """
        Convenience function to close the kevent descriptor for a
        specified kqueue-monitored path.
        
        :param path:
            Path for which the kevent descriptor will be closed.
        """
        self._descriptors.remove(path)

    def queue_event(self, event):
        """
        Handles queueing a single event object.
        
        :param event:
            An instance of :class:`watchdog.events.FileSystemEvent`
            or a subclass.
        """
        EventEmitter.queue_event(self, event)
        if event.event_type == EVENT_TYPE_CREATED:
            self._register_kevent(event.src_path, event.is_directory)
        elif event.event_type == EVENT_TYPE_MOVED:
            self._unregister_kevent(event.src_path)
            self._register_kevent(event.dest_path, event.is_directory)
        elif event.event_type == EVENT_TYPE_DELETED:
            self._unregister_kevent(event.src_path)

    def _queue_dirs_modified(self, dirs_modified, ref_snapshot, new_snapshot):
        """
        Queues events for directory modifications by scanning the directory
        for changes.
        
        A scan is a comparison between two snapshots of the same directory
        taken at two different times. This also determines whether files
        or directories were created, which updated the modified timestamp
        for the directory.
        """
        if dirs_modified:
            for dir_modified in dirs_modified:
                self.queue_event(DirModifiedEvent(dir_modified))

            diff_events = new_snapshot - ref_snapshot
            for file_created in diff_events.files_created:
                self.queue_event(FileCreatedEvent(file_created))

            for directory_created in diff_events.dirs_created:
                self.queue_event(DirCreatedEvent(directory_created))

    def _queue_events_except_renames_and_dir_modifications(self, event_list):
        """
        Queues events from the kevent list returned from the call to
        :meth:`select.kqueue.control`.
        
        .. NOTE:: Queues only the deletions, file modifications,
                  attribute modifications. The other events, namely,
                  file creation, directory modification, file rename,
                  directory rename, directory creation, etc. are
                  determined by comparing directory snapshots.
        """
        files_renamed = set()
        dirs_renamed = set()
        dirs_modified = set()
        for kev in event_list:
            descriptor = self._descriptors.get_for_fd(kev.ident)
            src_path = descriptor.path
            if is_deleted(kev):
                if descriptor.is_directory:
                    self.queue_event(DirDeletedEvent(src_path))
                else:
                    self.queue_event(FileDeletedEvent(src_path))
            elif is_attrib_modified(kev):
                if descriptor.is_directory:
                    self.queue_event(DirModifiedEvent(src_path))
                else:
                    self.queue_event(FileModifiedEvent(src_path))
            elif is_modified(kev):
                if descriptor.is_directory:
                    dirs_modified.add(src_path)
                else:
                    self.queue_event(FileModifiedEvent(src_path))
            elif is_renamed(kev):
                if descriptor.is_directory:
                    dirs_renamed.add(src_path)
                else:
                    files_renamed.add(src_path)

        return (files_renamed, dirs_renamed, dirs_modified)

    def _queue_renamed(self, src_path, is_directory, ref_snapshot, new_snapshot):
        """
        Compares information from two directory snapshots (one taken before
        the rename operation and another taken right after) to determine the
        destination path of the file system object renamed, and adds
        appropriate events to the event queue.
        """
        try:
            ref_stat_info = ref_snapshot.stat_info(src_path)
        except KeyError:
            if is_directory:
                self.queue_event(DirCreatedEvent(src_path))
                self.queue_event(DirDeletedEvent(src_path))
            else:
                self.queue_event(FileCreatedEvent(src_path))
                self.queue_event(FileDeletedEvent(src_path))
            return

        try:
            dest_path = absolute_path(new_snapshot.path_for_inode(ref_stat_info.st_ino))
            if is_directory:
                event = DirMovedEvent(src_path, dest_path)
                if self.watch.is_recursive:
                    for sub_event in event.sub_moved_events():
                        self.queue_event(sub_event)

                self.queue_event(event)
            else:
                self.queue_event(FileMovedEvent(src_path, dest_path))
        except KeyError:
            if is_directory:
                self.queue_event(DirDeletedEvent(src_path))
            else:
                self.queue_event(FileDeletedEvent(src_path))

    def _read_events(self, timeout = None):
        """
        Reads events from a call to the blocking
        :meth:`select.kqueue.control()` method.
        
        :param timeout:
            Blocking timeout for reading events.
        :type timeout:
            ``float`` (seconds)
        """
        return self._kq.control(self._descriptors.kevents, MAX_EVENTS, timeout)

    def queue_events(self, timeout):
        """
        Queues events by reading them from a call to the blocking
        :meth:`select.kqueue.control()` method.
        
        :param timeout:
            Blocking timeout for reading events.
        :type timeout:
            ``float`` (seconds)
        """
        with self._lock:
            try:
                event_list = self._read_events(timeout)
                files_renamed, dirs_renamed, dirs_modified = self._queue_events_except_renames_and_dir_modifications(event_list)
                new_snapshot = DirectorySnapshot(self.watch.path, self.watch.is_recursive)
                ref_snapshot = self._snapshot
                self._snapshot = new_snapshot
                if files_renamed or dirs_renamed or dirs_modified:
                    for src_path in files_renamed:
                        self._queue_renamed(src_path, False, ref_snapshot, new_snapshot)

                    for src_path in dirs_renamed:
                        self._queue_renamed(src_path, True, ref_snapshot, new_snapshot)

                    self._queue_dirs_modified(dirs_modified, ref_snapshot, new_snapshot)
            except OSError as e:
                if e.errno == errno.EBADF:
                    pass
                else:
                    raise

    def on_thread_stop(self):
        with self._lock:
            self._descriptors.clear()
            self._kq.close()


class KqueueObserver(BaseObserver):
    """
    Observer thread that schedules watching directories and dispatches
    calls to event handlers.
    """

    def __init__(self, timeout = DEFAULT_OBSERVER_TIMEOUT):
        BaseObserver.__init__(self, emitter_class=KqueueEmitter, timeout=timeout)
