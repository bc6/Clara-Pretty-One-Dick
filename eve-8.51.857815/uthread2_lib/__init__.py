#Embedded file name: uthread2_lib\__init__.py
import contextlib
import os
ENV_ALLOW_TASKLESS = 'ENV_ALLOW_TASKLESS'
__all__ = ['map',
 'get_implementation',
 'start_tasklet',
 'sleep',
 'sleep_sim',
 'yield_',
 'Event']
from uthread2_plugins import get_implementation

@contextlib.contextmanager
def _catch():
    try:
        yield
    except ImportError:
        pass


def _prime_plugins():
    with _catch():
        from uthread2_plugins import stacklessimpl
    with _catch():
        from uthread2_plugins import geventimpl
    if os.environ.get(ENV_ALLOW_TASKLESS):
        from uthread2_plugins import taskless


_prime_plugins()
impl = get_implementation()
map = impl.map
sleep = impl.sleep
sleep_sim = impl.sleep_sim
start_tasklet = impl.start_tasklet
yield_ = impl.yield_
get_current = impl.get_current
Event = impl.Event
Semaphore = impl.Semaphore
