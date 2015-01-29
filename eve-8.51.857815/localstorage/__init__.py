#Embedded file name: localstorage\__init__.py
"""
    The UTLS for the main dude.


    LocalStorage is actually "session local storage" as currently used, with thread
        inheritance

"""
from stackless import getcurrent
import weakref
import __builtin__

class Sissy:
    """
        A Sissy is a wrapper for a uthread local storage object, kept in builtins,
        that forwards all the appropriate stuff to an internal object.
    """

    def __init__(self, what):
        self.__dict__['__sissywhat__'] = what

    def _Obj(self):
        try:
            obj = GetLocalStorage()[self.__sissywhat__]
            if type(obj) is weakref.ref:
                obj = obj()
            return obj
        except (KeyError, ReferenceError):
            return None

    def __nonzero__(self):
        return bool(self._Obj())

    def __repr__(self):
        return '<Sissy: ' + repr(self._Obj()) + ' >'

    def __getattr__(self, k):
        try:
            obj = GetLocalStorage()[self.__sissywhat__]
            if type(obj) is weakref.ref:
                obj = obj()
        except (KeyError, ReferenceError):
            obj = None

        return getattr(obj, k)

    def __setattr__(self, k, v):
        return setattr(self._Obj(), k, v)


mainLocalStorage = {}

def GetLocalStorage():
    """
        Gets the uthread local storage, whether this is the main tasklet or a taskletext
    """
    global mainLocalStorage
    return getattr(getcurrent(), 'localStorage', mainLocalStorage)


def GetOtherLocalStorage(t):
    """
        Gets the uthread local storage for t, whether this is the main tasklet or a taskletext
    """
    return getattr(t, 'localStorage', mainLocalStorage)


def SetLocalStorage(s):
    """
        Sets the uthread local storage, whether this is the main tasklet or a taskletext
    """
    global mainLocalStorage
    try:
        getcurrent().localStorage = s
    except AttributeError:
        mainLocalStorage = s


def UpdateLocalStorage(props):
    """
        Adds the given properties to the local storage, and returns a copy of the
        old storage, that you should restore to.
    """
    try:
        ls = getcurrent().localStorage
    except AttributeError:
        ls = mainLocalStorage

    ret = dict(ls)
    ls.update(props)
    return ret


class UpdatedLocalStorage(object):
    """
        A context manager for keeping temporary local storage around
        Usage:  with UpdatedLocalStorage({"foo":bar}): pass
    """

    def __init__(self, updatedDict):
        self.__store = updatedDict

    def __enter__(self):
        self.__store = UpdateLocalStorage(self.__store)

    def __exit__(self, e, v, tb):
        SetLocalStorage(self.__store)


__builtin__.charsession = Sissy('base.charsession')
__builtin__.currentcall = Sissy('base.currentcall')
__builtin__.session = Sissy('base.session')
__builtin__.caller = Sissy('base.caller')
