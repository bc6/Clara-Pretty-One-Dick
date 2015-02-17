#Embedded file name: codereload/win32api\fs.py
import ctypes
from ctypes.wintypes import BOOL, DWORD, HANDLE
_k32 = ctypes.windll.kernel32
_k32.DefineDosDeviceW.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.c_wchar_p]

def DefineDosDevice(flags, deviceName, targetPath):
    result = _k32.DefineDosDeviceW(flags, deviceName, targetPath)
    if result == 0:
        raise ctypes.WinError()


def GetLogicalDrives():
    return _k32.GetLogicalDrives()


def QueryDosDevice(drive_letter):
    """Returns the Windows 'native' path for a DOS drive letter."""
    devicename = ctypes.create_unicode_buffer(drive_letter)
    ucchMax = 4096
    result = ctypes.create_unicode_buffer(u'', ucchMax)
    size = ctypes.windll.kernel32.QueryDosDeviceW(ctypes.byref(devicename), ctypes.byref(result), ucchMax)
    if size == 0:
        raise ctypes.WinError()
    return result.value


_k32.CreateFileW.argtypes = [ctypes.c_wchar_p,
 DWORD,
 DWORD,
 ctypes.c_void_p,
 DWORD,
 DWORD,
 HANDLE]
_k32.CreateFileW.restype = HANDLE

def CreateFile(*args, **kwargs):
    result = _k32.CreateFileW(*args, **kwargs)
    if result is None:
        raise ctypes.WinError()
    return result


class FILETIME(ctypes.Structure):
    _fields_ = [('dwLowDateTime', DWORD), ('dwHighDateTime', DWORD)]


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [('dwFileAttributes', DWORD),
     ('ftCreationTime', FILETIME),
     ('ftLastAccessTime', FILETIME),
     ('ftLastWriteTime', FILETIME),
     ('dwVolumeSerialNumber', DWORD),
     ('nFileSizeHigh', DWORD),
     ('nFileSizeLow', DWORD),
     ('nNumberOfLinks', DWORD),
     ('nFileIndexHigh', DWORD),
     ('nFileIndexLow', DWORD)]


_k32.GetFileInformationByHandle.argtypes = [HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)]
_k32.GetFileInformationByHandle.restype = BOOL

def GetFileInformationByHandle(fileHandle):
    info = BY_HANDLE_FILE_INFORMATION()
    returnval = ctypes.windll.kernel32.GetFileInformationByHandle(fileHandle, info)
    if returnval == 0:
        raise ctypes.WinError()
    return info


_k32.CloseHandle.argtypes = [HANDLE]
_k32.CloseHandle.restype = BOOL

def CloseHandle(hnd):
    if _k32.CloseHandle(hnd) == 0:
        raise ctypes.WinError()


_k32.CreateHardLinkW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p]
_k32.CreateHardLinkW.restype = BOOL

def CreateHardLink(link_name, source):
    res = _k32.CreateHardLinkW(link_name, source, None)
    if res == 0:
        raise ctypes.WinError()


class Constants(object):
    """Constants, pulled from py32's win32file file."""
    CALLBACK_CHUNK_FINISHED = 0
    CALLBACK_STREAM_SWITCH = 1
    CBR_110 = 110
    CBR_115200 = 115200
    CBR_1200 = 1200
    CBR_128000 = 128000
    CBR_14400 = 14400
    CBR_19200 = 19200
    CBR_2400 = 2400
    CBR_256000 = 256000
    CBR_300 = 300
    CBR_38400 = 38400
    CBR_4800 = 4800
    CBR_56000 = 56000
    CBR_57600 = 57600
    CBR_600 = 600
    CBR_9600 = 9600
    CLRBREAK = 9
    CLRDTR = 6
    CLRRTS = 4
    COPY_FILE_ALLOW_DECRYPTED_DESTINATION = 8
    COPY_FILE_FAIL_IF_EXISTS = 1
    COPY_FILE_OPEN_SOURCE_FOR_WRITE = 4
    COPY_FILE_RESTARTABLE = 2
    CREATE_ALWAYS = 2
    CREATE_FOR_DIR = 2
    CREATE_FOR_IMPORT = 1
    CREATE_NEW = 1
    DRIVE_CDROM = 5
    DRIVE_FIXED = 3
    DRIVE_NO_ROOT_DIR = 1
    DRIVE_RAMDISK = 6
    DRIVE_REMOTE = 4
    DRIVE_REMOVABLE = 2
    DRIVE_UNKNOWN = 0
    DTR_CONTROL_DISABLE = 0
    DTR_CONTROL_ENABLE = 1
    DTR_CONTROL_HANDSHAKE = 2
    EVENPARITY = 2
    EV_BREAK = 64
    EV_CTS = 8
    EV_DSR = 16
    EV_ERR = 128
    EV_RING = 256
    EV_RLSD = 32
    EV_RXCHAR = 1
    EV_RXFLAG = 2
    EV_TXEMPTY = 4
    FD_ACCEPT = 8
    FD_ADDRESS_LIST_CHANGE = 512
    FD_CLOSE = 32
    FD_CONNECT = 16
    FD_GROUP_QOS = 128
    FD_OOB = 4
    FD_QOS = 64
    FD_READ = 1
    FD_ROUTING_INTERFACE_CHANGE = 256
    FD_WRITE = 2
    FILE_ALL_ACCESS = 2032127
    FILE_ATTRIBUTE_ARCHIVE = 32
    FILE_ATTRIBUTE_COMPRESSED = 2048
    FILE_ATTRIBUTE_DIRECTORY = 16
    FILE_ATTRIBUTE_HIDDEN = 2
    FILE_ATTRIBUTE_NORMAL = 128
    FILE_ATTRIBUTE_OFFLINE = 4096
    FILE_ATTRIBUTE_READONLY = 1
    FILE_ATTRIBUTE_SYSTEM = 4
    FILE_ATTRIBUTE_TEMPORARY = 256
    FILE_BEGIN = 0
    FILE_CURRENT = 1
    FILE_ENCRYPTABLE = 0
    FILE_END = 2
    FILE_FLAG_BACKUP_SEMANTICS = 33554432
    FILE_FLAG_DELETE_ON_CLOSE = 67108864
    FILE_FLAG_NO_BUFFERING = 536870912
    FILE_FLAG_OPEN_REPARSE_POINT = 2097152
    FILE_FLAG_OVERLAPPED = 1073741824
    FILE_FLAG_POSIX_SEMANTICS = 16777216
    FILE_FLAG_RANDOM_ACCESS = 268435456
    FILE_FLAG_SEQUENTIAL_SCAN = 134217728
    FILE_FLAG_WRITE_THROUGH = -0x80000000
    FILE_GENERIC_READ = 1179785
    FILE_GENERIC_WRITE = 1179926
    FILE_IS_ENCRYPTED = 1
    FILE_READ_ONLY = 8
    FILE_ROOT_DIR = 3
    FILE_SHARE_DELETE = 4
    FILE_SHARE_READ = 1
    FILE_SHARE_WRITE = 2
    FILE_SYSTEM_ATTR = 2
    FILE_SYSTEM_DIR = 4
    FILE_SYSTEM_NOT_SUPPORT = 6
    FILE_TYPE_CHAR = 2
    FILE_TYPE_DISK = 1
    FILE_TYPE_PIPE = 3
    FILE_TYPE_UNKNOWN = 0
    FILE_UNKNOWN = 5
    FILE_USER_DISALLOWED = 7
    GENERIC_EXECUTE = 536870912
    GENERIC_READ = -0x80000000
    GENERIC_WRITE = 1073741824
    GetFileExInfoStandard = 1
    INVALID_HANDLE_VALUE = -1
    MARKPARITY = 3
    MOVEFILE_COPY_ALLOWED = 2
    MOVEFILE_CREATE_HARDLINK = 16
    MOVEFILE_DELAY_UNTIL_REBOOT = 4
    MOVEFILE_FAIL_IF_NOT_TRACKABLE = 32
    MOVEFILE_REPLACE_EXISTING = 1
    MOVEFILE_WRITE_THROUGH = 8
    NOPARITY = 0
    ODDPARITY = 1
    ONE5STOPBITS = 1
    ONESTOPBIT = 0
    OPEN_ALWAYS = 4
    OPEN_EXISTING = 3
    OVERWRITE_HIDDEN = 4
    PROGRESS_CANCEL = 1
    PROGRESS_CONTINUE = 0
    PROGRESS_QUIET = 3
    PROGRESS_STOP = 2
    PURGE_RXABORT = 2
    PURGE_RXCLEAR = 8
    PURGE_TXABORT = 1
    PURGE_TXCLEAR = 4
    REPLACEFILE_IGNORE_MERGE_ERRORS = 2
    REPLACEFILE_WRITE_THROUGH = 1
    RTS_CONTROL_DISABLE = 0
    RTS_CONTROL_ENABLE = 1
    RTS_CONTROL_HANDSHAKE = 2
    RTS_CONTROL_TOGGLE = 3
    SCS_32BIT_BINARY = 0
    SCS_DOS_BINARY = 1
    SCS_OS216_BINARY = 5
    SCS_PIF_BINARY = 3
    SCS_POSIX_BINARY = 4
    SCS_WOW_BINARY = 2
    SECURITY_ANONYMOUS = 0
    SECURITY_CONTEXT_TRACKING = 262144
    SECURITY_DELEGATION = 196608
    SECURITY_EFFECTIVE_ONLY = 524288
    SECURITY_IDENTIFICATION = 65536
    SECURITY_IMPERSONATION = 131072
    SETBREAK = 8
    SETDTR = 5
    SETRTS = 3
    SETXOFF = 1
    SETXON = 2
    SO_CONNECT_TIME = 28684
    SO_UPDATE_ACCEPT_CONTEXT = 28683
    SO_UPDATE_CONNECT_CONTEXT = 28688
    SPACEPARITY = 4
    SYMBOLIC_LINK_FLAG_DIRECTORY = 1
    TF_DISCONNECT = 1
    TF_REUSE_SOCKET = 2
    TF_USE_DEFAULT_WORKER = 0
    TF_USE_KERNEL_APC = 32
    TF_USE_SYSTEM_THREAD = 16
    TF_WRITE_BEHIND = 4
    TRUNCATE_EXISTING = 5
    TWOSTOPBITS = 2
    UNICODE = 0
    WSAECONNABORTED = 10053
    WSAECONNRESET = 10054
    WSAEDISCON = 10101
    WSAEFAULT = 10014
    WSAEINPROGRESS = 10036
    WSAEINTR = 10004
    WSAEINVAL = 10022
    WSAEMSGSIZE = 10040
    WSAENETDOWN = 10050
    WSAENETRESET = 10052
    WSAENOTCONN = 10057
    WSAENOTSOCK = 10038
    WSAEOPNOTSUPP = 10045
    WSAESHUTDOWN = 10058
    WSAEWOULDBLOCK = 10035
    WSA_IO_PENDING = 997
    WSA_OPERATION_ABORTED = 995
