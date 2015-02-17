#Embedded file name: uthread2_plugins\geventimpl.py
import gevent
import gevent.event as gevents
from gevent.coros import Semaphore
import weakref
from . import BaseUthreadImpl, Tasklet, BaseSemaphore

class GeventTasklet(Tasklet):

    def __init__(self, func, *args, **kwargs):

        def inner():
            gevent.getcurrent().uthread2_tasklet = weakref.ref(self)
            func(*args, **kwargs)

        self.tasklet = gevent.spawn(inner)

    def is_alive(self):
        return not self.tasklet.ready()

    def kill(self):
        self.tasklet.kill()


class GeventSemaphore(BaseSemaphore):

    def __init__(self):
        self.__semaphore = Semaphore()

    def acquire(self):
        self.__semaphore.acquire()

    def release(self):
        self.__semaphore.release()


class _GeventAutoTasklet(GeventTasklet):

    def __init__(self, tasklet):
        self.tasklet = weakref.proxy(tasklet)
        self.tasklet.uthread2_tasklet = lambda : self

    def is_alive(self):
        return not self.tasklet.dead


class _GeventUthread(BaseUthreadImpl):

    def sleep(self, seconds):
        gevent.sleep(seconds)

    def start_tasklet(self, func, *args, **kwargs):
        return GeventTasklet(func, *args, **kwargs)

    def yield_(self):
        gevent.sleep(0)

    def get_current(self):
        current = gevent.getcurrent()
        try:
            return current.uthread2_tasklet()
        except AttributeError:
            return _GeventAutoTasklet(current)

    def Event(self):
        return gevents.Event()

    def Semaphore(self):
        return GeventSemaphore()


GeventImpl = _GeventUthread()
