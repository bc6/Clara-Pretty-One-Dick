#Embedded file name: fsdlite\cache.py
import os
import time
import sqlite3
from contextlib import contextmanager
from UserDict import DictMixin

class Cache(DictMixin):
    """
    Implements a basic sqlite backed key / value store to cache serialized data to disk using sqlite.
    """
    _connections = {}
    _create = ['\n        CREATE TABLE IF NOT EXISTS cache\n        (\n          key TEXT PRIMARY KEY,\n          value TEXT,\n          time FLOAT\n        )\n        ',
     '\n        CREATE TABLE IF NOT EXISTS indexes\n        (\n          key TEXT,\n          value TEXT\n        )\n        ',
     '\n        CREATE INDEX IF NOT EXISTS key_index ON indexes(key)\n        ',
     '\n        CREATE INDEX IF NOT EXISTS value_index ON indexes(value)\n        ']
    _drop = ['DROP TABLE IF EXISTS cache', 'DROP TABLE IF EXISTS indexes']
    _cache_get = 'SELECT value, time FROM cache WHERE key = ?'
    _cache_del = 'DELETE FROM cache WHERE key = ?'
    _cache_set = 'REPLACE INTO cache (key, value, time) VALUES (?, ?, ?)'
    _cache_key = 'SELECT key FROM cache'
    _index_get = 'SELECT value FROM indexes WHERE key = ?'
    _index_del = 'DELETE FROM indexes WHERE value = ?'
    _index_set = 'REPLACE INTO indexes (key, value) VALUES (?, ?)'

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self._data = {}

    @contextmanager
    def connection(self):
        try:
            if self.path not in Cache._connections:
                connection = sqlite3.connect(self.path, check_same_thread=False)
                try:
                    [ connection.execute(sql) for sql in self._create ]
                    connection.commit()
                except sqlite3.OperationalError as exception:
                    if str(exception) != 'attempt to write a readonly database':
                        raise

                connection.execute('PRAGMA synchronous = OFF')
                connection.execute('PRAGMA journal_mode = MEMORY')
                Cache._connections[self.path] = connection
            connection = Cache._connections[self.path]
            yield connection
            connection.commit()
        except sqlite3.OperationalError as exception:
            if str(exception) != 'attempt to write a readonly database':
                raise

    def __nonzero__(self):
        return True

    def _row(self, key):
        with self.connection() as connection:
            item = connection.execute(self._cache_get, (key,)).fetchone()
            if item is None:
                raise KeyError('Not in cache')
            return item

    def __getitem__(self, key):
        return self._row(key)[0]

    def __setitem__(self, key, data):
        with self.connection() as connection:
            connection.execute(self._cache_set, (key, data, time.time()))

    def __delitem__(self, key):
        with self.connection() as connection:
            connection.execute(self._cache_del, (key,))

    def keys(self):
        with self.connection() as connection:
            rows = connection.execute(self._cache_key).fetchall()
            return [ row[0] for row in rows ]

    def time(self, key):
        return self._row(key)[1]

    def clear(self):
        with self.connection() as connection:
            [ connection.execute(sql) for sql in self._drop ]
            [ connection.execute(sql) for sql in self._create ]

    def index_clear(self, value):
        with self.connection() as connection:
            connection.execute(self._index_del, (value,))

    def index_set(self, key, value):
        with self.connection() as connection:
            connection.execute(self._index_set, (key, value))

    def index(self, key):
        with self.connection() as connection:
            return [ row[0] for row in connection.execute(self._index_get, (key,)).fetchall() ]
