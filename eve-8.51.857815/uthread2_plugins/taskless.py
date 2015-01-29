#Embedded file name: uthread2_plugins\taskless.py
import time
from . import BaseUthreadImpl, Tasklet

class _Event(object):

    def __init__(self):
        self._isset = False

    def is_set(self):
        return self._isset

    isSet = is_set

    def set(self):
        self._isset = True

    def clear(self):
        self._isset = False

    def wait(self, timeout = None):
        if self.is_set():
            return True
        return False


class _Semaphore(object):

    def __init__(self):
        pass

    def acquire(self):
        pass

    def release(self):
        pass


_current_tasklet = []

class _TasklessTasklet(Tasklet):

    def __init__(self, func, *args, **kwargs):
        _current_tasklet.append(self)
        try:
            self.result = func(*args, **kwargs)
        finally:
            _current_tasklet.pop()

    def is_alive(self):
        return False

    def kill(self):
        pass


class _TasklessRootTasklet(_TasklessTasklet):

    def __init__(self):
        pass

    def is_alive(self):
        return True


_current_tasklet.append(_TasklessRootTasklet())

class _TasklessImpl(BaseUthreadImpl):

    def sleep(self, seconds):
        time.sleep(seconds)

    def sleep_sim(self, seconds):
        time.sleep(seconds)

    def start_tasklet(self, func, *args, **kwargs):
        return _TasklessTasklet(func, *args, **kwargs)

    def yield_(self):
        pass

    def get_current(self):
        return _current_tasklet[-1]

    def Event(self):
        return _Event()

    def Semaphore(self):
        return _Semaphore()


TasklessImpl = _TasklessImpl()
