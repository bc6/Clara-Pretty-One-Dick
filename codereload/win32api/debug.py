#Embedded file name: codereload/win32api\debug.py
import ctypes
from ctypes import byref, c_ulonglong, Structure
from ctypes.wintypes import DWORD

def DebugBreak():
    ctypes.windll.kernel32.DebugBreak()


def OutputDebugString(s):
    try:
        ctypes.windll.kernel32.OutputDebugStringW(unicode(s))
    except Exception:
        ctypes.windll.kernel32.OutputDebugStringA(str(s))


def QueryPerformanceFrequency():
    freq = ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(freq)):
        raise ctypes.WinError()
    return freq.value


def QueryPerformanceCounter():
    counter = ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(counter)):
        raise ctypes.WinError()
    return counter.value


def GlobalMemoryStatusEx():
    """
    Returns memory load
    """

    class _MEMORYSTATUSEX(Structure):
        """
        Get memory load form windows.
        """
        _fields_ = [('dwLength', DWORD),
         ('dwMemoryLoad', DWORD),
         ('ullTotalPhys', c_ulonglong),
         ('ullAvailPhys', c_ulonglong),
         ('ullTotalPageFile', c_ulonglong),
         ('ullAvailPageFile', c_ulonglong),
         ('ullTotalVirtual', c_ulonglong),
         ('ullAvailVirtual', c_ulonglong),
         ('ullAvailExtendedVirtual', c_ulonglong)]

    memstatus = _MEMORYSTATUSEX()
    ctypes.windll.kernel32.GlobalMemoryStatusEx(byref(memstatus))
    return memstatus
