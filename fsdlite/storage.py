#Embedded file name: fsdlite\storage.py
import os
import time
import glob
import fnmatch
import fsdlite
import weakref
from UserDict import DictMixin

class Storage(DictMixin):
    """
    A dictionary like object which loads instances of fsd staticdata from disk and manages the
    state of the memory holding each file. Static objects can be loaded either directly
    from a raw list of YAML files OR from a sqlite database acting as a cache. This storage
    class will also monitor for filesystem changes and reload the files if neccesary.
    
    Data can exist in one of three places, which we search in order:
    
        [storage]           [format]
        memory              python object
        sqlite              json
        disk                yaml
    """

    def __init__(self, data = None, cache = None, mapping = None, indexes = None, monitor = False):
        self.on_update = fsdlite.Signal()
        self.pattern = data
        self.cache_path = cache
        self.mapping = mapping
        self.indexes = indexes
        self.monitor = monitor
        self.files = None
        self.objects = {}
        self.times = {}
        self.file_monitor = None
        self._cache = None
        self._file_init()

    def __del__(self):
        monitor = getattr(self, 'file_monitor', None)
        if monitor:
            fsdlite.stop_file_monitor(monitor)

    def __getitem__(self, key):
        """
        Fetch an item from the storage by key. If we have monitoring enabled we first
        check the file + cache modification dates
        """
        if self.monitor:
            file_time = self._file_time(key)
            cache_time = self._cache_time(key)
            object_time = self._object_time(key)
        else:
            file_time = cache_time = object_time = 0
        try:
            if object_time >= cache_time and object_time >= file_time:
                return self._object_load(key)
        except KeyError:
            pass

        try:
            if cache_time >= file_time:
                return self._cache_load(key)
        except KeyError:
            pass

        return self._file_load(key)

    def __setitem__(self, key, item):
        raise RuntimeError('FSD Storage is Immutable')

    def __delitem__(self, key):
        self.times.pop(self.objects.pop(key), None)

    def keys(self):
        if self.cache and not self.files:
            return self.cache.keys()
        elif not self.cache and self.files:
            return self.files.keys()
        else:
            return list(set(self.cache.keys() + self.files.keys()))

    def Get(self, key):
        return self[key]

    def prime(self, pattern = None):
        """
        Primes all the files in the index.
        """
        keys = set(self.cache.keys())
        for key, (filename, timestamp) in self.files.iteritems():
            if pattern is None or fnmatch.fnmatch(filename, pattern):
                keys.add(key)

        for key in keys:
            self[key]

    def filter_keys(self, name, key):
        """
        Returns the object keys matched by the filter name and value.
        """
        if self.cache:
            return self.cache.index('{}.{}'.format(name, key))
        return []

    def filter(self, name, key):
        """
        Returns all objects keys matched by the filter name and value.
        """
        return [ self[key] for key in self.filter_keys(name, key) ]

    def index(self, name, key):
        """
        Returns the first object from storage matching the index conditions.
        """
        try:
            return self.filter(name, key)[0]
        except IndexError:
            raise KeyError

    def _object_load(self, key):
        """
        Attempts to load the specified key from the in memory store.
        """
        return self.objects[key]

    def _object_save(self, key, obj):
        """
        Writes a plain python object into the in-memory store.
        """
        self.objects[key] = obj
        self.times[key] = time.time()

    def _object_time(self, key):
        """
        Returns the time this object was cached in memory, so we can compare
        to the other caches.
        """
        try:
            self.objects[key]
            return self.times[key]
        except KeyError:
            return 0

    def _cache_load(self, key):
        """
        If we have a cache enabled, load the JSON from the cache and unpack an object.
        """
        if self.cache:
            data = self.cache[key]
            obj = fsdlite.decode(data, mapping=self.mapping, json=True)
            self._object_save(key, obj)
            return obj
        raise KeyError('No Cache')

    def _cache_save(self, key, obj):
        """
        If we have a cache enabled, encode the object as JSON and store for later.
        """
        if self.cache:
            self.cache[key] = fsdlite.encode(obj, json=True)
            self.cache.index_clear(key)
            for indexName, indexKeys in fsdlite.index(obj, self.indexes).iteritems():
                for indexKey in indexKeys:
                    self.cache.index_set('{}.{}'.format(indexName, indexKey), key)

    def _cache_time(self, key):
        """
        Returns the cache time for this key.
        """
        if self.cache:
            try:
                return self.cache.time(key)
            except KeyError:
                pass

        return 0

    def _cache_init(self):
        """
        The static storage cache is a lazy loaded property, so we don't perform
        any file IO at import time. Also gives us a chance to reconfigure it before
        it is first loaded.
        """
        if self.cache_path and self._cache is None:
            self._cache = fsdlite.Cache(self.cache_path)
        return self._cache

    cache = property(_cache_init)

    def _file_init(self):
        """
        This keeps an in-memory index on first load, with an optional file monitoring
        mode which will look for changes in the pattern matched directory.
        """
        if self.files is None:
            self.files = {}
            if self.pattern:
                for filename in glob.glob(self.pattern):
                    self._file_index(filename)

            if self.monitor and not self.file_monitor:
                self.file_monitor = fsdlite.start_file_monitor(os.path.dirname(self.pattern), fsdlite.WeakMethod(self._file_changed))

    def _file_index(self, filename):
        """
        Given a filename, checks to see if this should be indexed and adds or removes
        the file from the index.
        """
        if fnmatch.fnmatch(filename, self.pattern):
            filename = os.path.abspath(filename)
            key = os.path.splitext(os.path.basename(filename))[0]
            if os.path.exists(filename):
                modified = os.path.getmtime(filename)
                self.files[key] = (filename, modified)
            else:
                self.files.pop(key, None)

    def _file_changed(self, event, filename):
        """
        Whenever a file is changed, just trigger a reindex on it.
        """
        self._file_index(filename)

    def _file_load(self, key):
        """
        If we have a raw static data directory, try and load the key from their.
        """
        if self.pattern:
            try:
                filepath, modified = self.files[str(key)]
                with open(filepath, 'r') as stream:
                    data = fsdlite.load(stream.read())
                    self._cache_save(key, data)
                    obj = fsdlite.decode(data, mapping=self.mapping)
                    self._object_save(key, obj)
                    return obj
            except IOError as exception:
                raise KeyError(exception)

        raise KeyError('No Static Data')

    def _file_time(self, key):
        """
        Returns the disk modification time for this key, for comparison against the cache.
        """
        if self.pattern:
            try:
                return self.files[str(key)][1]
            except KeyError:
                return time.time()

        return 0


class WeakStorage(Storage):
    """
    A variation of normal storage, except that the in memory object cache will weakref
    the objects it stores. This means we will get cache hits provided the object still
    exists in use in the application somewhere, but as soon as it is release we free it
    from the object store. Subsequent requests for the same object will go to the sql
    cache instead.
    """

    def __init__(self, *args, **kwargs):
        Storage.__init__(self, *args, **kwargs)
        self.objects = weakref.WeakValueDictionary()
