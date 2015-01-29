#Embedded file name: uthread2_plugins\stacklessimpl.py
import stackless
import sys
import time
import weakref
import uthread
from stacklesslib import locks, main
from . import BaseUthreadImpl, Tasklet, stackless_sleep, BaseSemaphore

def is_main():
    return stackless.getcurrent() == stackless.getmain()


_tasklets = weakref.WeakKeyDictionary()

class StacklessTasklet(Tasklet):

    def __init__(self, func, *args, **kwargs):

        def inner():
            _tasklets[stackless.getcurrent()] = self
            func(*args, **kwargs)

        self.tasklet = stackless.tasklet(inner)()

    def is_alive(self):
        return self.tasklet.alive

    def kill(self):
        self.tasklet.kill()


class StacklessSemaphore(BaseSemaphore):

    def __init__(self):
        self.__semaphore = uthread.Semaphore()

    def acquire(self):
        self.__semaphore.acquire()

    def release(self):
        self.__semaphore.release()


class StacklessEvent(locks.Event):

    def wait(self, timeout = None):
        if not is_main():
            res = locks.Event.wait(self, timeout)
            return res
        if self.is_set():
            return True
        if timeout is None:
            timeout = sys.maxint
        endtime = time.time() + timeout
        while not self.is_set() and time.time() < endtime:
            stackless_sleep.sleep(0.005)

        return self.is_set()


class _StacklessUthread(BaseUthreadImpl):

    def sleep(self, seconds):
        stackless_sleep.sleep(seconds)

    def start_tasklet(self, func, *args, **kwargs):
        return StacklessTasklet(func, *args, **kwargs)

    def yield_(self):
        main.mainloop.wakeup_tasklets(None)
        if stackless.getcurrent() == stackless.getmain():
            stackless.run()

    def get_current(self):
        return _tasklets.get(stackless.getcurrent(), None)

    def Event(self):
        return StacklessEvent()

    def Semaphore(self):
        return StacklessSemaphore()


StacklessImpl = _StacklessUthread()
