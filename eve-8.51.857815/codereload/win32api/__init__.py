#Embedded file name: codereload/win32api\__init__.py
"""
Win32 API wrappers.

Wraps common Win32 API's and constants using ctypes.
Most functions return the same as their Win32 API equivalents,
but wrapped into more usable Python versions.

There is much more of the Win32 API implemented inside of the :mod:`win32api`
package, only the bits that are actively used are exposed.
If you need something new,
find it or add it, and expose it through the :mod:`win32api` module.
Do not force people to dig around into the large and nasty implementation modules.

And remember, in general, avoid using these.
Prefer more robust 3rd party wrappers that are cross-platform
and provide more Pythonic APIs.

Members
=======
"""
try:
    import ctypes.wintypes
    _IS_NT = True
except (ImportError, ValueError):
    _IS_NT = False

if _IS_NT:
    import ctypes
    from ctypes.wintypes import HANDLE, POINT
    INVALID_HANDLE_VALUE = HANDLE(-1).value
    ctypes.windll.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    ctypes.windll.user32 = ctypes.WinDLL('user32', use_last_error=True)
    ctypes.windll.shell32 = ctypes.WinDLL('shell32', use_last_error=True)
    ctypes.windll.version = ctypes.WinDLL('version', use_last_error=True)

    def SetConsoleTitle(title):
        if not ctypes.windll.kernel32.SetConsoleTitleW(unicode(title)):
            raise ctypes.WinError()


    from .fs import CloseHandle, CreateFile, CreateHardLink, DefineDosDevice, GetFileInformationByHandle, GetLogicalDrives, QueryDosDevice, Constants as Win32FileConstants
    from .process import getppid
    from .waitables import FindFirstChangeNotification, FindNextChangeNotification, FindCloseChangeNotification, WaitForSingleObject, WaitForMultipleObjects, Waitables, FILE_NOTIFY_CHANGE_LAST_WRITE
