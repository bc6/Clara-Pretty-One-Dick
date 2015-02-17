#Embedded file name: functoolsext\__init__.py
"""
Like the :mod:`functools` module but contains even more stuff!
Also puts :mod:`functools` namespace into this module
so you can safely just use :mod:`functoolsext` instead of :mod:`functools`.

Contains a back port of the LRU Caching decorator from 3.3, original code:
http://code.activestate.com/recipes/578078-py26-and-py30-backport-of-python-33s-lru-cache/

Members
=======
"""
from collections import namedtuple
from functools import *
import inspect
from threading import RLock
_CacheInfo = namedtuple('CacheInfo', ['hits',
 'misses',
 'maxsize',
 'currsize'])

class _HashedSeq(list):
    __slots__ = 'hashvalue'

    def __init__(self, tup, hash = hash):
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self):
        return self.hashvalue


def _make_key(args, kwds, typed, kwd_mark = (object(),), fasttypes = set([int,
 str,
 frozenset,
 type(None)]), sorted = sorted, tuple = tuple, type = type, len = len):
    """Make a cache key from optionally typed positional and keyword arguments"""
    key = args
    if kwds:
        sorted_items = sorted(kwds.items())
        key += kwd_mark
        for item in sorted_items:
            key += item

    if typed:
        key += tuple((type(v) for v in args))
        if kwds:
            key += tuple((type(v) for k, v in sorted_items))
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)


def lru_cache(maxsize = 128, typed = False):
    """Least-recently-used cache decorator.
    
    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.
    
    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.
    
    Arguments to the cached function must be hashable.
    
    View the cache statistics named tuple (hits, misses, maxsize, currsize) with
    f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.
    
    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used
    
    """

    def decorating_function(user_function):
        cache = dict()
        stats = [0, 0]
        HITS, MISSES = (0, 1)
        make_key = _make_key
        cache_get = cache.get
        _len = len
        lock = RLock()
        root = []
        root[:] = [root,
         root,
         None,
         None]
        nonlocal_root = [root]
        PREV, NEXT, KEY, RESULT = (0, 1, 2, 3)
        if maxsize == 0:

            def wrapper(*args, **kwds):
                result = user_function(*args, **kwds)
                stats[MISSES] += 1
                return result

        elif maxsize is None:

            def wrapper(*args, **kwds):
                key = make_key(args, kwds, typed)
                result = cache_get(key, root)
                if result is not root:
                    stats[HITS] += 1
                    return result
                result = user_function(*args, **kwds)
                cache[key] = result
                stats[MISSES] += 1
                return result

        else:

            def wrapper(*args, **kwds):
                key = make_key(args, kwds, typed) if kwds or typed else args
                with lock:
                    link = cache_get(key)
                    if link is not None:
                        root, = nonlocal_root
                        link_prev, link_next, key, result = link
                        link_prev[NEXT] = link_next
                        link_next[PREV] = link_prev
                        last = root[PREV]
                        last[NEXT] = root[PREV] = link
                        link[PREV] = last
                        link[NEXT] = root
                        stats[HITS] += 1
                        return result
                result = user_function(*args, **kwds)
                with lock:
                    root, = nonlocal_root
                    if key in cache:
                        pass
                    elif _len(cache) >= maxsize:
                        oldroot = root
                        oldroot[KEY] = key
                        oldroot[RESULT] = result
                        root = nonlocal_root[0] = oldroot[NEXT]
                        oldkey = root[KEY]
                        oldvalue = root[RESULT]
                        root[KEY] = root[RESULT] = None
                        del cache[oldkey]
                        cache[key] = oldroot
                    else:
                        last = root[PREV]
                        link = [last,
                         root,
                         key,
                         result]
                        last[NEXT] = root[PREV] = cache[key] = link
                    stats[MISSES] += 1
                return result

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(stats[HITS], stats[MISSES], maxsize, len(cache))

        def cache_clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                root = nonlocal_root[0]
                root[:] = [root,
                 root,
                 None,
                 None]
                stats[:] = [0, 0]

        wrapper.__wrapped__ = user_function
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return update_wrapper(wrapper, user_function)

    return decorating_function


def func_takes_arguments(f):
    """Return True if ``f`` takes any arguments,
    inluding * args and ** kwargs.
    
    :raise AttributeError: If ``f`` is a built-in (i.e. a C++ method) there's
      no way to inspect it. You can wrap it in a lambda.
    """
    try:
        fc = f.func_code
    except AttributeError:
        raise AttributeError('Cannot inspect built-ins: %s.' % f)

    arguments, varargs, keywords = inspect.getargs(fc)
    if inspect.ismethod(f):
        arguments.pop(0)
    if any([arguments, varargs, keywords]):
        return True
    return False
