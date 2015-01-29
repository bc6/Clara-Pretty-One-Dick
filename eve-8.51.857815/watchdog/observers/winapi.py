#Embedded file name: watchdog/observers\winapi.py
from __future__ import with_statement
from watchdog.utils import platform
if not platform.is_windows():
    raise ImportError
import ctypes.wintypes
import struct
try:
    LPVOID = ctypes.wintypes.LPVOID
except AttributeError:
    LPVOID = ctypes.c_void_p

INVALID_HANDLE_VALUE = 4294967295L
FILE_NOTIFY_CHANGE_FILE_NAME = 1
FILE_NOTIFY_CHANGE_DIR_NAME = 2
FILE_NOTIFY_CHANGE_ATTRIBUTES = 4
FILE_NOTIFY_CHANGE_SIZE = 8
FILE_NOTIFY_CHANGE_LAST_WRITE = 16
FILE_NOTIFY_CHANGE_LAST_ACCESS = 32
FILE_NOTIFY_CHANGE_CREATION = 64
FILE_NOTIFY_CHANGE_SECURITY = 256
FILE_FLAG_BACKUP_SEMANTICS = 33554432
FILE_FLAG_OVERLAPPED = 1073741824
FILE_LIST_DIRECTORY = 1
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
FILE_SHARE_DELETE = 4
OPEN_EXISTING = 3
FILE_ACTION_CREATED = 1
FILE_ACTION_DELETED = 2
FILE_ACTION_MODIFIED = 3
FILE_ACTION_RENAMED_OLD_NAME = 4
FILE_ACTION_RENAMED_NEW_NAME = 5
FILE_ACTION_OVERFLOW = 65535
FILE_ACTION_ADDED = FILE_ACTION_CREATED
FILE_ACTION_REMOVED = FILE_ACTION_DELETED
THREAD_TERMINATE = 1
WAIT_ABANDONED = 128
WAIT_IO_COMPLETION = 192
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258

class OVERLAPPED(ctypes.Structure):
    _fields_ = [('Internal', LPVOID),
     ('InternalHigh', LPVOID),
     ('Offset', ctypes.wintypes.DWORD),
     ('OffsetHigh', ctypes.wintypes.DWORD),
     ('Pointer', LPVOID),
     ('hEvent', ctypes.wintypes.HANDLE)]


def _errcheck_bool(value, func, args):
    if not value:
        raise ctypes.WinError()
    return args


def _errcheck_handle(value, func, args):
    if not value:
        raise ctypes.WinError()
    if value == INVALID_HANDLE_VALUE:
        raise ctypes.WinError()
    return args


def _errcheck_dword(value, func, args):
    if value == 4294967295L:
        raise ctypes.WinError()
    return args


try:
    ReadDirectoryChangesW = ctypes.windll.kernel32.ReadDirectoryChangesW
except AttributeError:
    raise ImportError('ReadDirectoryChangesW is not available')

ReadDirectoryChangesW.restype = ctypes.wintypes.BOOL
ReadDirectoryChangesW.errcheck = _errcheck_bool
ReadDirectoryChangesW.argtypes = (ctypes.wintypes.HANDLE,
 LPVOID,
 ctypes.wintypes.DWORD,
 ctypes.wintypes.BOOL,
 ctypes.wintypes.DWORD,
 ctypes.POINTER(ctypes.wintypes.DWORD),
 ctypes.POINTER(OVERLAPPED),
 LPVOID)
CreateFileW = ctypes.windll.kernel32.CreateFileW
CreateFileW.restype = ctypes.wintypes.HANDLE
CreateFileW.errcheck = _errcheck_handle
CreateFileW.argtypes = (ctypes.wintypes.LPCWSTR,
 ctypes.wintypes.DWORD,
 ctypes.wintypes.DWORD,
 LPVOID,
 ctypes.wintypes.DWORD,
 ctypes.wintypes.DWORD,
 ctypes.wintypes.HANDLE)
CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.restype = ctypes.wintypes.BOOL
CloseHandle.argtypes = (ctypes.wintypes.HANDLE,)
CancelIoEx = ctypes.windll.kernel32.CancelIoEx
CancelIoEx.restype = ctypes.wintypes.BOOL
CancelIoEx.errcheck = _errcheck_bool
CancelIoEx.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(OVERLAPPED))
CreateEvent = ctypes.windll.kernel32.CreateEventW
CreateEvent.restype = ctypes.wintypes.HANDLE
CreateEvent.errcheck = _errcheck_handle
CreateEvent.argtypes = (LPVOID,
 ctypes.wintypes.BOOL,
 ctypes.wintypes.BOOL,
 ctypes.wintypes.LPCWSTR)
SetEvent = ctypes.windll.kernel32.SetEvent
SetEvent.restype = ctypes.wintypes.BOOL
SetEvent.errcheck = _errcheck_bool
SetEvent.argtypes = (ctypes.wintypes.HANDLE,)
WaitForSingleObjectEx = ctypes.windll.kernel32.WaitForSingleObjectEx
WaitForSingleObjectEx.restype = ctypes.wintypes.DWORD
WaitForSingleObjectEx.errcheck = _errcheck_dword
WaitForSingleObjectEx.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD, ctypes.wintypes.BOOL)
CreateIoCompletionPort = ctypes.windll.kernel32.CreateIoCompletionPort
CreateIoCompletionPort.restype = ctypes.wintypes.HANDLE
CreateIoCompletionPort.errcheck = _errcheck_handle
CreateIoCompletionPort.argtypes = (ctypes.wintypes.HANDLE,
 ctypes.wintypes.HANDLE,
 LPVOID,
 ctypes.wintypes.DWORD)
GetQueuedCompletionStatus = ctypes.windll.kernel32.GetQueuedCompletionStatus
GetQueuedCompletionStatus.restype = ctypes.wintypes.BOOL
GetQueuedCompletionStatus.errcheck = _errcheck_bool
GetQueuedCompletionStatus.argtypes = (ctypes.wintypes.HANDLE,
 LPVOID,
 LPVOID,
 ctypes.POINTER(OVERLAPPED),
 ctypes.wintypes.DWORD)
PostQueuedCompletionStatus = ctypes.windll.kernel32.PostQueuedCompletionStatus
PostQueuedCompletionStatus.restype = ctypes.wintypes.BOOL
PostQueuedCompletionStatus.errcheck = _errcheck_bool
PostQueuedCompletionStatus.argtypes = (ctypes.wintypes.HANDLE,
 ctypes.wintypes.DWORD,
 ctypes.wintypes.DWORD,
 ctypes.POINTER(OVERLAPPED))

class FILE_NOTIFY_INFORMATION(ctypes.Structure):
    _fields_ = [('NextEntryOffset', ctypes.wintypes.DWORD),
     ('Action', ctypes.wintypes.DWORD),
     ('FileNameLength', ctypes.wintypes.DWORD),
     ('FileName', ctypes.c_char * 1)]


LPFNI = ctypes.POINTER(FILE_NOTIFY_INFORMATION)

def get_FILE_NOTIFY_INFORMATION(readBuffer, nBytes):
    results = []
    while nBytes > 0:
        fni = ctypes.cast(readBuffer, LPFNI)[0]
        ptr = ctypes.addressof(fni) + FILE_NOTIFY_INFORMATION.FileName.offset
        filename = ctypes.string_at(ptr, fni.FileNameLength)
        results.append((fni.Action, filename.decode('utf-16')))
        numToSkip = fni.NextEntryOffset
        if numToSkip <= 0:
            break
        readBuffer = readBuffer[numToSkip:]
        nBytes -= numToSkip

    return results


def get_FILE_NOTIFY_INFORMATION_alt(event_buffer, nBytes):
    """Extract the information out of a FILE_NOTIFY_INFORMATION structure."""
    pos = 0
    event_buffer = event_buffer[:nBytes]
    while pos < len(event_buffer):
        jump, action, namelen = struct.unpack('iii', event_buffer[pos:pos + 12])
        name = event_buffer[pos + 12:pos + 12 + namelen].decode('utf-16')
        yield (name, action)
        if not jump:
            break
        pos += jump
