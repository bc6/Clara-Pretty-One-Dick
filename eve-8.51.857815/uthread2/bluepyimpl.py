#Embedded file name: uthread2\bluepyimpl.py
import blue
from stacklesslib import locks, main
from stackless import getcurrent
import weakref
import bluepy
from uthread2_plugins import BaseUthreadImpl, stacklessimpl, set_implementation

class BluepyTasklet(stacklessimpl.StacklessTasklet):

    def __init__(self, func, *args, **kwargs):

        def inner():
            getcurrent().localStorage['uthread2_tasklet'] = weakref.ref(self)
            func(*args, **kwargs)

        self.tasklet = bluepy.CreateTaskletExt(inner)


class _BluepyAutoTasklet(BluepyTasklet):

    def __init__(self, tasklet):
        self.tasklet = weakref.proxy(tasklet)
        if hasattr(tasklet, 'localStorage'):
            tasklet.localStorage['uthread2_tasklet'] = self


class _BluepyUthread(BaseUthreadImpl):

    def __init__(self):
        BaseUthreadImpl.__init__(self)

    def sleep(self, seconds):
        blue.synchro.Sleep(seconds * 1000)

    def sleep_sim(self, seconds):
        blue.synchro.SleepSim(seconds * 1000)

    def start_tasklet(self, func, *args, **kwargs):
        return BluepyTasklet(func, *args, **kwargs)

    def yield_(self):
        blue.synchro.Yield()
        main.mainloop.wakeup_tasklets(None)

    def get_current(self):
        current = getcurrent()
        result = getattr(current, 'localStorage', {}).get('uthread2_tasklet', None)
        if result:
            return result()
        return _BluepyAutoTasklet(current)

    def Event(self):
        return locks.Event()

    def Semaphore(self):
        return stacklessimpl.StacklessSemaphore()


BluepyImpl = _BluepyUthread()
set_implementation(BluepyImpl)
