#Embedded file name: threadutils\__init__.py
"""
Things to make working with threading in Python easier.
Note, you should generally avoid using threads,
but sometimes you need them!
Check out :mod:`uthread2` for a tasklet based solution.

Contains useful Thread subclasses:

- :class:`ExceptionalThread`, which brings proper exceptions to threads.
- :class:`NotAThread`, which is useful for mocking threads because it runs
  synchronously when ``start()`` is called.
- :class:`TimerExt`: A cancellable/restartable :class:`threading.Timer`.

Some useful threading-related utilities:

- :class:`ChunkIter`, useful for chunking work on a background thread
  and reporting it to another thread in chunks (useful for UI).
- :func:`memoize`, a caching decorator that can be threadsafe
  (vital if you want a singleton that has some expensive
  global state to construct, for example).
  There is also :class:`expiring_memoize` for a time-based solution.
- :class:`token`, a simple threading token that can be set/queried,
  useful for inter-thread communication.
- :class:`Signal`, used for registering and signaling events in a process.
- :func:`join_timeout`, raises an error if a thread is alive after a join.

Members
=======
"""
import threading
import time
import warnings
from brennivin.threadutils import *
from brennivin.threadutils import ChunkIter as _ChunkIter
from brennivin.threadutils import Token as _Token
import uthread2 as uthread

class ChunkIter(_ChunkIter):

    @classmethod
    def start_thread(cls, target, name):
        try:
            import blue, stacklesslib.replacements.threading
            cls.threading = stacklesslib.replacements.threading
            cls.sleep = lambda sec: blue.synchro.Sleep(sec * 1000)
            cls.benice = blue.pyos.BeNice
        except ImportError:
            cls.threading = threading
            cls.benice = lambda : None

        thread = cls.threading.Thread(target=target, name=name)
        thread.daemon = True
        thread.start()
        return thread


class SimpleSignal(Signal):

    def __init__(self, *args, **kwargs):
        super(SimpleSignal, self).__init__(*args, **kwargs)
        warnings.warn('SimpleSignal is deprecated, use Signal instead.', DeprecationWarning)

    Connect = Signal.connect
    Disconnect = Signal.disconnect
    Emit = Signal.emit


class Token(_Token):

    def __init__(self):
        super(Token, self).__init__()
        self.Set = self.set
        self.IsSet = self.is_set


class throttle(object):
    """
    A class for wrapping calls to functions in order to throttle their calls.
    If a function gets called rapidly only the first and last calls within a
    timestep of the defined interval get through.
    
    Example:
    
    Letters a-h are function calls and STEP is a moment in time which occurs every interval_seconds seconds.
    ::
    
               STEP
                |
        a  b  c  d  e  f  g  h
    
    In this example calls a, c, d and h get through.
    """

    def __init__(self, f, interval_seconds, time_func = None):
        self.f = f
        self.wait_seconds = interval_seconds
        self.time_since_step = 0.0
        self.next_call = None
        self.next_call_args = None
        self.next_call_kwargs = None
        self._init_time_func(time_func)

    def _init_time_func(self, time_func):
        if time_func is None:
            self.time_func = time.time
        else:
            self.time_func = time_func

    def trigger_next_call_if_exists(self):
        uthread.sleep(self.wait_seconds)
        if self.next_call is not None:
            self.next_call(*self.next_call_args, **self.next_call_kwargs)
            self.next_call = None
            self.next_call_args = None
            self.next_call_kwargs = None

    def __call__(self, *args, **kwargs):
        dt = self.time_func() - self.time_since_step
        if dt > self.wait_seconds:
            self.time_since_step = 0.0
        if self.time_since_step == 0.0:
            self.f(*args, **kwargs)
            self.time_since_step = self.time_func()
            uthread.start_tasklet(self.trigger_next_call_if_exists)
            return
        self.next_call = self.f
        self.next_call_args = args
        self.next_call_kwargs = kwargs


Throttle = throttle

def throttled(interval_seconds, **kwargs):
    """
    Decorator for throttling a function.
    See :class:`throttle`.
    """

    def deco(func):
        t = throttle(func, interval_seconds, **kwargs)
        return t

    return deco


Throttled = throttled
try:
    import multiprocessing.pool
    _threadpool = multiprocessing.pool.ThreadPool()

    def PMapMaybe(func, iterable):
        """Usually a 'map' on a threadpool. Since ExeFile does not
        have multiprocessing available, we fall back to regular map.
        Interface is same as 'map'.
        """
        return _threadpool.map(func, iterable)


except ImportError:
    PMapMaybe = map

TimeoutJoin = join_timeout
Memoize = memoize
ExpiringMemoize = expiring_memoize
