#Embedded file name: watchdog/observers\winapi_common.py
from watchdog.utils import platform
from functools import reduce
if not platform.is_windows():
    raise ImportError
import ctypes
from watchdog.observers.winapi import FILE_FLAG_BACKUP_SEMANTICS, FILE_FLAG_OVERLAPPED, FILE_SHARE_READ, FILE_SHARE_WRITE, FILE_SHARE_DELETE, FILE_NOTIFY_CHANGE_FILE_NAME, FILE_NOTIFY_CHANGE_DIR_NAME, FILE_NOTIFY_CHANGE_ATTRIBUTES, FILE_NOTIFY_CHANGE_SIZE, FILE_NOTIFY_CHANGE_LAST_WRITE, FILE_NOTIFY_CHANGE_SECURITY, FILE_NOTIFY_CHANGE_LAST_ACCESS, FILE_NOTIFY_CHANGE_CREATION, FILE_ACTION_CREATED, FILE_ACTION_DELETED, FILE_ACTION_MODIFIED, FILE_LIST_DIRECTORY, OPEN_EXISTING, INVALID_HANDLE_VALUE, CreateFileW, ReadDirectoryChangesW, CreateIoCompletionPort, CancelIoEx
from watchdog.events import DirDeletedEvent, DirCreatedEvent, DirModifiedEvent, FileDeletedEvent, FileCreatedEvent, FileModifiedEvent
WATCHDOG_FILE_FLAGS = FILE_FLAG_BACKUP_SEMANTICS
WATCHDOG_FILE_FLAGS_ASYNC = FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED
WATCHDOG_FILE_SHARE_FLAGS = reduce(lambda x, y: x | y, [FILE_SHARE_READ, FILE_SHARE_WRITE, FILE_SHARE_DELETE])
WATCHDOG_FILE_NOTIFY_FLAGS = reduce(lambda x, y: x | y, [FILE_NOTIFY_CHANGE_FILE_NAME,
 FILE_NOTIFY_CHANGE_DIR_NAME,
 FILE_NOTIFY_CHANGE_ATTRIBUTES,
 FILE_NOTIFY_CHANGE_SIZE,
 FILE_NOTIFY_CHANGE_LAST_WRITE,
 FILE_NOTIFY_CHANGE_SECURITY,
 FILE_NOTIFY_CHANGE_LAST_ACCESS,
 FILE_NOTIFY_CHANGE_CREATION])
WATCHDOG_TRAVERSE_MOVED_DIR_DELAY = 1
BUFFER_SIZE = 2048
DIR_ACTION_EVENT_MAP = {FILE_ACTION_CREATED: DirCreatedEvent,
 FILE_ACTION_DELETED: DirDeletedEvent,
 FILE_ACTION_MODIFIED: DirModifiedEvent}
FILE_ACTION_EVENT_MAP = {FILE_ACTION_CREATED: FileCreatedEvent,
 FILE_ACTION_DELETED: FileDeletedEvent,
 FILE_ACTION_MODIFIED: FileModifiedEvent}

def get_directory_handle(path, file_flags):
    """Returns a Windows handle to the specified directory path."""
    handle = CreateFileW(path, FILE_LIST_DIRECTORY, WATCHDOG_FILE_SHARE_FLAGS, None, OPEN_EXISTING, file_flags, None)
    return handle


def close_directory_handle(handle):
    try:
        CancelIoEx(handle, None)
    except WindowsError:
        return


def read_directory_changes(handle, event_buffer, recursive):
    """Read changes to the directory using the specified directory handle.
    
    http://timgolden.me.uk/pywin32-docs/win32file__ReadDirectoryChangesW_meth.html
    """
    nbytes = ctypes.wintypes.DWORD()
    try:
        ReadDirectoryChangesW(handle, ctypes.byref(event_buffer), len(event_buffer), recursive, WATCHDOG_FILE_NOTIFY_FLAGS, ctypes.byref(nbytes), None, None)
    except WindowsError:
        return ([], 0)

    try:
        int_class = long
    except NameError:
        int_class = int

    return (event_buffer.raw, int_class(nbytes.value))


def create_io_completion_port():
    """
    http://timgolden.me.uk/pywin32-docs/win32file__CreateIoCompletionPort_meth.html
    """
    return CreateIoCompletionPort(INVALID_HANDLE_VALUE, None, 0, 0)
