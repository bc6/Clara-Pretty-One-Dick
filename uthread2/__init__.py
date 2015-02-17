#Embedded file name: uthread2\__init__.py
"""uthread2 adds a bluepy stackless implementation on top of
uthread2_lib's existing uthread implementations.

First our bluepy impl plugin is registered to uthread (via bluepyimpl.py),
and in this file we re-implement all methods that uthread implements,
using ``get_implementation`` to make sure our implementation is used.

Using uthread2_lib.uthread directly should be avoided
as your code would not work in ExeFile.
"""
from uthread2_plugins import get_implementation
import uthread2_lib
try:
    from . import bluepyimpl
except ImportError:
    pass

impl = get_implementation()
map = impl.map
Map = map
sleep = impl.sleep
Sleep = sleep
sleep_sim = impl.sleep_sim
SleepSim = sleep_sim
start_tasklet = impl.start_tasklet
StartTasklet = start_tasklet
yield_ = impl.yield_
Yield = yield_
get_current = impl.get_current
Event = impl.Event
Semaphore = impl.Semaphore
