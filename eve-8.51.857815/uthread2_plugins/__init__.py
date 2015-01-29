#Embedded file name: uthread2_plugins\__init__.py
import sys
_all_implementations = []

class BaseUthreadImpl(object):

    def __init__(self):
        _all_implementations.append(self)

    def map(self, func, sequence):
        sequence = list(sequence)
        resultmap = [None] * len(sequence)
        exc_infos = []

        def inner(ind_and_item):
            ind, item = ind_and_item
            try:
                result = func(item)
            except Exception:
                exc_infos.append(sys.exc_info())
                return

            resultmap[ind] = result

        tasklets = [ self.start_tasklet(inner, o) for o in enumerate(sequence) ]
        while tasklets:
            self.yield_()
            while tasklets and not tasklets[-1].is_alive():
                tasklets.pop()

            if any(exc_infos):
                ei = exc_infos[0]
                raise ei[0], ei[1], ei[2]

        return resultmap

    def sleep(self, seconds):
        raise NotImplementedError()

    def sleep_sim(self, seconds):
        return self.sleep(seconds)

    def start_tasklet(self, func, *args, **kwargs):
        raise NotImplementedError()

    def yield_(self):
        raise NotImplementedError()

    def get_current(self):
        raise NotImplementedError()

    def Event(self):
        raise NotImplementedError()


class BaseSemaphore(object):

    def acquire(self):
        raise NotImplementedError()

    def release(self):
        raise NotImplementedError()


class Tasklet(object):

    def is_alive(self):
        raise NotImplementedError()

    def kill(self):
        raise NotImplementedError()

    def IsAlive(self, *args, **kwargs):
        return self.is_alive(*args, **kwargs)

    def Kill(self, *args, **kwargs):
        return self.kill(*args, **kwargs)


_main_impl = None

def set_implementation(impl):
    global _main_impl
    _main_impl = impl


def get_implementation():
    if _main_impl is not None:
        return _main_impl
    if _all_implementations:
        return _all_implementations[0]
    raise RuntimeError('No uthread implementations registered.')


def get_all_implementations():
    return list(_all_implementations)
