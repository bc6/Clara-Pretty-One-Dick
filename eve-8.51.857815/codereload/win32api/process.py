#Embedded file name: codereload/win32api\process.py
import ctypes
import ctypes.wintypes as wintypes

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = (('dwSize', wintypes.DWORD),
     ('cntUsage', wintypes.DWORD),
     ('th32ProcessID', wintypes.DWORD),
     ('th32DefaultHeapID', wintypes.POINTER(wintypes.ULONG)),
     ('th32ModuleID', wintypes.DWORD),
     ('cntThreads', wintypes.DWORD),
     ('th32ParentProcessID', wintypes.DWORD),
     ('pcPriClassBase', wintypes.LONG),
     ('dwFlags', wintypes.DWORD),
     ('szExeFile', wintypes.c_char * wintypes.MAX_PATH))


CreateToolhelp32Snapshot = wintypes.windll.kernel32.CreateToolhelp32Snapshot
CloseHandle = wintypes.windll.kernel32.CloseHandle
Process32First = wintypes.windll.kernel32.Process32First
Process32Next = wintypes.windll.kernel32.Process32Next

def getppid(pid):
    """the Windows version of os.getppid"""
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
    snapshot = CreateToolhelp32Snapshot(2, 0)
    try:
        if not Process32First(snapshot, ctypes.byref(pe)):
            raise WindowsError
        while pe.th32ProcessID != pid:
            if not Process32Next(snapshot, ctypes.byref(pe)):
                raise WindowsError('No process found with pid %s' % pid)

        result = pe.th32ParentProcessID
    finally:
        CloseHandle(snapshot)

    return result
