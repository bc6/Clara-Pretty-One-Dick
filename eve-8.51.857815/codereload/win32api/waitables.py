#Embedded file name: codereload/win32api\waitables.py
import ctypes
from ctypes.wintypes import BOOL, DWORD, HANDLE
import weakref
QS_ALLEVENTS = 1215
QS_ALLINPUT = 1279
QS_RAWINPUT = 1024
MWMO_ALERTABLE = 2
STATUS_WAIT_0 = 0L
STATUS_ABANDONED_WAIT_0 = 128L
WAIT_OBJECT_0 = STATUS_WAIT_0 + 0
WAIT_IO_COMPLETION = 192L
WAIT_ABANDONED_0 = STATUS_ABANDONED_WAIT_0 + 0
WAIT_FAILED = 4294967295L
INFINITE = 4294967295L
WAIT_TIMEOUT = 258L

class Waitables(object):
    """Utility class to manage waitable objects. It has a list of waitable objects with
    optional callback function associated. Whenever an object is signaled, the callback
    function is called.
    """

    def __init__(self):
        self.waitables = weakref.WeakValueDictionary()

    def InsertHandle(self, handle, callback):
        """InsertHandle(handle, callback) -> handle
        Insert a handle to a waitable object.
        
        If 'handle' is None, a new event object will be created.
        
        The 'callback' is a class instance with the following function defined:
        def OnObjectSignaled(self, handle, abandoned)
        
        If 'abandoned' is False, the 'handle' is signaled.
        
        A weak reference to the callback is held, so if the  callback function is destroyed,
        the handle is removed from the waitables list as well.
        """
        if handle is None:
            CreateEventW = ctypes.windll.kernel32.CreateEventW
            CreateEventW.restype = HANDLE
            handle = CreateEventW(None, BOOL(), BOOL(), None)
            if not handle:
                raise ctypes.WinError()
        self.waitables[handle] = callback
        return handle

    def RemoveHandle(self, handle, close = False):
        """Remove handle from waitables.
        If 'close' is true, the handle is closed using Win32's CloseHandle().
        """
        del self.waitables[handle]
        if close:
            if not ctypes.windll.kernel32.CloseHandle(HANDLE(handle)):
                raise ctypes.WinError()

    def Wait(self, milliseconds = 1000):
        """Calls MsgWaitForMultipleObjectsEx for all objects in the list and calls the
        appropriate callback function for all signaled objects.
        
        The return value is the same as from the MsgWait call.
        
        In case of signaled or abandoned object, the appropriate callback function
        will be called and MsgWait called again.
        
        Please note that exceptions from callback functions are delegated upwards.
        """
        handles, callbacks = self.waitables.keys(), self.waitables.values()
        HandleArray = ctypes.c_void_p * len(handles)
        handles = HandleArray(*handles)
        MsgWaitForMultipleObjectsEx = ctypes.windll.user32.MsgWaitForMultipleObjectsEx
        MsgWaitForMultipleObjectsEx.restype = DWORD
        ret = MsgWaitForMultipleObjectsEx(len(handles), handles, milliseconds, QS_ALLINPUT, MWMO_ALERTABLE)
        if WAIT_OBJECT_0 <= ret <= WAIT_OBJECT_0 + len(handles) - 1:
            idx = ret - WAIT_OBJECT_0
            if handles[idx] in self.waitables:
                callbacks[idx].OnObjectSignaled(handles[idx], False)
            return self.Wait(0)
        if ret == WAIT_OBJECT_0 + len(handles):
            return ret
        if WAIT_ABANDONED_0 <= ret <= WAIT_ABANDONED_0 + len(handles) - 1:
            idx = ret - WAIT_OBJECT_0
            if handles[idx] in self.waitables:
                callbacks[idx].OnObjectSignaled(handles[idx], True)
            return self.Wait(0)
        if ret == WAIT_IO_COMPLETION:
            return ret
        if ret == WAIT_TIMEOUT:
            return ret
        if ret == WAIT_FAILED:
            raise ctypes.WinError()
        else:
            raise RuntimeError('Wait: Unknown return value from MsgWaitForMultipleObjectsEx:', ret)


def WaitForSingleObject(handle, milliseconds = 0):
    """Returns True if signaled, False if timeout occurred."""
    ret = ctypes.windll.kernel32.WaitForSingleObject(handle, milliseconds)
    if ret == WAIT_OBJECT_0:
        return True
    if ret == WAIT_TIMEOUT:
        return False
    if ret == WAIT_FAILED:
        raise ctypes.WinError()
    else:
        raise RuntimeError('WaitForSingleObject: Unknown return value from wait:', ret)


def WaitForMultipleObjects(handles, waitAll, milliseconds):
    HandleArray = ctypes.c_void_p * len(handles)
    handles = HandleArray(*handles)
    ctypes.WaitForMultipleObjects(len(handles), handles, bool(waitAll), milliseconds)


FILE_NOTIFY_CHANGE_FILE_NAME = 1
FILE_NOTIFY_CHANGE_DIR_NAME = 2
FILE_NOTIFY_CHANGE_ATTRIBUTES = 4
FILE_NOTIFY_CHANGE_SIZE = 8
FILE_NOTIFY_CHANGE_LAST_WRITE = 16
FILE_NOTIFY_CHANGE_LAST_ACCESS = 32
FILE_NOTIFY_CHANGE_CREATION = 64
FILE_NOTIFY_CHANGE_SECURITY = 256

def FindFirstChangeNotification(pathName, watchSubTree, notifyFilter):
    """The FindFirstChangeNotification function creates a change notification handle and
    sets up initial change notification filter conditions. A wait on a notification handle
    succeeds when a change matching the filter conditions occurs in the specified directory
    or subtree. The function does not report changes to the specified directory itself.
    """
    FindFirstChangeNotificationW = ctypes.windll.kernel32.FindFirstChangeNotificationW
    FindFirstChangeNotificationW.restype = HANDLE
    return FindFirstChangeNotificationW(unicode(pathName), bool(watchSubTree), notifyFilter)


def FindNextChangeNotification(handle):
    if not ctypes.windll.kernel32.FindNextChangeNotification(HANDLE(handle)):
        raise ctypes.WinError()


def FindCloseChangeNotification(handle):
    if not ctypes.windll.kernel32.FindCloseChangeNotification(HANDLE(handle)):
        raise ctypes.WinError()
