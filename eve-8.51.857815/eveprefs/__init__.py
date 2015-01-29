#Embedded file name: eveprefs\__init__.py
"""
Contains serializers and accessors for EVE preferences,
usually accessed through the `prefs` builtin.

:class:`BaseIniFile` is the common interface for all preferences handlers.
To create a new preferences handler, subclass `BaseIniFile`
and override all abstract methods.
`FixKey` is optionally overridable,
and `_SpoofKey` can be overridden if spoof support is needed (it shouldn't be).

To use the test classes for a new handler,
you should mixin from `eveprefs.test.IniFileTestBase` and `unittest.TestCase`
override `makeIni` to return an instance of your `BaseIniFile` subclass,
and override `setUp` to call `IniFileTestBase._setUp`.
"""
import abc
import types
DEFAULT_ENCODING = 'cp1252'
_unsupplied = object()

def get_filename(blue, shortname, ext, root = None):
    """Return the filename for a prefs file.
    
    :param blue: Blue module. We don't want pyd imports in init files...
    :param shortname: Name of the config file,
      without path and dot.extention.
    :param ext: Extension, with leading dot.
    :param root: Location of the config file, if ommitted,
      blue.paths.ResolvePath(u"settings:/") is used.
    """
    if root is None:
        root = blue.paths.ResolvePath(u'settings:/')
    if root[-1] not in ('\\', '/'):
        root += '\\'
    if shortname[-len(ext):] != ext:
        filename = root + shortname + ext
    else:
        filename = root + shortname
    return filename


def strip_spaces(d):
    """Returns a new dictionary with all leading and trailing spaces stripped
    from the keys and values in dictionary d.
    
    `d` is assumed to have keys of all strings, and values of any type.
    """
    result = {}
    for k, v in d.iteritems():
        realv = v
        if isinstance(v, types.StringTypes):
            realv = v.strip()
        result[k.strip()] = realv

    return result


class BaseIniFile(object):
    __metaclass__ = abc.ABCMeta

    def HasKey(self, key):
        """
        Check for existence of key-value pair.
        
        :return: True if 'key' exists, False otherwise.
        """
        return self.FixKey(key) in self._GetKeySet()

    @abc.abstractmethod
    def _GetKeySet(self):
        """
        Return the keys of this instance.
        (something with a quick lookup and which can be iterated over).
        
        This data will not be mutated or exposed to clients so implementers
        can expose state, such as returning the full dictionary of keys/values.
        
        :rtype: collections.Set
        """
        pass

    def GetKeys(self, beginWith = None):
        """
        Gets a list of all keys that begin with the given string,
        or if no string is given,
        gets a list of all keys in the ini file.
        """
        if beginWith is None:
            keys = list(self._GetKeySet())
        else:
            beginWith = self.FixKey(beginWith)
            keys = [ key for key in self._GetKeySet() if key[:len(beginWith)] == beginWith ]
        return keys

    @abc.abstractmethod
    def _GetValue(self, key):
        """Return the value for an already fixed key."""
        pass

    def GetValue(self, key, default = _unsupplied, flushDef = False):
        """
        Returns the value associated with the key.
        
        If 'key' is not found and 'default' is NOT specified,
        KeyError is raised.
        
        If 'key' is not found and 'default' IS specified,
        then 'default' is returned.
        Additionally, if 'flushDef' is set,
        the default value will be saved.
        """
        key = self.FixKey(key)
        if key not in self._GetKeySet():
            if default is _unsupplied:
                raise KeyError(key)
            if flushDef:
                self.SetValue(key, default)
            return default
        return self._GetValue(key)

    @abc.abstractmethod
    def _SetValue(self, key, value, forcePickle):
        """Implementation of `SetValue` that takes a fixed key."""
        pass

    def SetValue(self, key, value, forcePickle = False):
        """
        Registers a value under a key.
        `key` must be a string.
        
        If 'key' already exists, the value is replaced.
        'value' can be any picklable python object.
        If 'forcePickle' is true, the value is always pickled.
        
        If `value` is different from the current value,
        also save the current state.
        """
        key = self.FixKey(key)
        self._SetValue(key, value, forcePickle)

    def _SpoofKey(self, key, value):
        """Implementation of `SpoofKey` that takes a fixed key.
        
        Optional for subclasses to implement as it is of very limited use.
        """
        raise NotImplementedError()

    def SpoofKey(self, key, value):
        """
        **This method should be deprecated and replaced with an in-memory
        prefs.**
        
        Change the value associated with the given key *in memory only*.
        The value will not be saved,
        and if the key didn't previously exist in the file,
        it will not be created.
        
        ***NOTE!**: After spoofing a key,
        it may not be possible to change it normally until after a restart.
        Generally only use this for cases where you want to ignore the
        setting in the file for the current session.
        """
        key = self.FixKey(key)
        self._SpoofKey(key, value)

    def FixKey(self, key):
        """
        Given a possible key string,
        make sure it is a valid key (ascii string),
        and translate it into one if necessary.
        
        :raise ValueError: If key is invalid.
        """
        try:
            key.decode('ascii')
        except UnicodeDecodeError:
            raise ValueError('key must be ascii')

        return str(key).strip()

    @abc.abstractmethod
    def _DeleteValue(self, key):
        """Implementation of `DeleteValue` for an already fixed key and
        which the key is actually present."""
        pass

    def DeleteValue(self, key):
        """Deletes the key and value, if exists, and saves the state."""
        key = self.FixKey(key)
        if key in self._GetKeySet():
            self._DeleteValue(key)


class Handler(object):
    """
    Magic getattr/setattr wrapper for convenience.
    Or inconvenience. Not sure which.
    
    :type inifile: BaseIniFile
    """

    def __init__(self, inifile):
        self.__dict__['ini'] = inifile

    def __getattr__(self, key):
        if hasattr(self.__dict__['ini'], key):
            return getattr(self.__dict__['ini'], key)
        try:
            return self.__dict__['ini'].GetValue(key)
        except KeyError:
            raise AttributeError, key

    def __setattr__(self, key, value):
        self.__dict__['ini'].SetValue(key, value)

    def __str__(self):
        ini = self.__dict__['ini']
        clsname = type(ini).__name__
        filename = ''
        if hasattr(ini, 'filename'):
            filename = ini.filename + ' '
        count = len(ini.GetKeys())
        return '%(clsname)s %(filename)swith %(count)s entries' % locals()

    def __eq__(self, _):
        return NotImplemented
