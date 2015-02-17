#Embedded file name: preferences\__init__.py
"""
Contains the :class:`Preferences` class for serializing preferences.
It is very simple (prefs are a dict of dicts)
and flexible (can be serialized using user-provided functions).

Members
=======
"""
import cPickle
import json
import logging
from brennivin.preferences import Preferences
logger = logging.getLogger(__name__)

class Pickled(Preferences):
    """`Preferences` subclass that uses cPickle, for backwards compat.
    Prefer to use the default instead,
    as prefs should be human-readable.
    """

    def __init__(self, filename, dump = None, load = None, onloaderror = None):
        if dump is None:
            dump = lambda obj, stream: cPickle.dump(obj, stream, -1)
        if load is None:
            load = cPickle.load
        self.dumper = lambda obj, fp: dump(obj, fp)
        self.loader = lambda fp: load(fp)
        Preferences.__init__(self, filename, onloaderror)
        self.GetValue = self.get
        self.SetValue = self.set
        self.GetOrSet = self.setdefault
        self.Save = self.save
        self.Load = self.load

    def remove(self, region, variable):
        """Remove the saved data."""
        if region not in self.prefs:
            raise KeyError("Preference does not have a '%s' region" % region)
        if variable not in self.prefs[region]:
            raise KeyError("Preference does not have a '%s.%s' variable" % (region, variable))
        del self.prefs[region][variable]
        self.Save()

    RemoveValue = remove


__ginstance__ = None

def Init(path):
    """
        Initilize a global singleton
    """
    global __ginstance__
    if __ginstance__ is None:
        __ginstance__ = Pickled(path, dump=json.dump, load=json.load)


def GetValue(region, variable, defaultValue):
    """
        Get a preference value from the pickled data.
        region      -   The parent group that owns the variable
        variable    -   The name of the stored variable
        defaultValue - If there is no data, we must give it some default value.
    """
    if __ginstance__ is None:
        return defaultValue
    else:
        return __ginstance__.GetValue(region, variable, defaultValue)


def SetValue(region, variable, value):
    """
        Register a value to be stored in a cPickle file.
        region  -   The parent group that owns the variable
        variable-   The name of the variable
        value   -   The value to be stored as region.variable
    """
    if __ginstance__ is not None:
        __ginstance__.SetValue(region, variable, value)


def SaveToPath(path):
    if __ginstance__ is None:
        raise 'Preference instance has not been set'
    oldFilePath = __ginstance__.filename
    __ginstance__.filename = path
    __ginstance__.Save()
    __ginstance__.filename = oldFilePath
