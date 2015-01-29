#Embedded file name: uthread2_plugins\stackless_sleep.py
"""
From https://bitbucket.org/nettok/useless/src/tip/useless/_sleeping.py

Author: Alejandro Castillo <pyalec@gmail.com>

Tasklet sleeping technique based on general purpose sleep
on http://www.stackless.com/wiki/Idioms

It uses another thread and a condition variable to not busy wait"""
__all__ = ['sleep', 'wake']
import threading
import stackless
import time
from weakref import WeakValueDictionary

class List(list):
    pass


lock = threading.Lock()
cond = threading.Condition(lock)
sleeping_tasklets = []
sleeping_tasklets_dict = WeakValueDictionary()
manager_running = False

def sleep(seconds):
    """current tasklet goes to sleep"""
    channel = stackless.channel()
    endtime = time.time() + seconds
    with lock:
        sleeping_tasklet = List([endtime, channel])
        sleeping_tasklets.append(sleeping_tasklet)
        sleeping_tasklets.sort()
        sleeping_tasklets_dict[stackless.current] = sleeping_tasklet
        cond.notify()
    while True:
        try:
            channel.receive()
            break
        except StopIteration:
            pass


def wake(t):
    """wakes a sleeping tasklet"""
    with lock:
        sleeping_tasklet = sleeping_tasklets_dict.get(t)
        if sleeping_tasklet is not None:
            channel = sleeping_tasklet[1]
            try:
                sleeping_tasklets.remove(sleeping_tasklet)
            except ValueError:
                return

        else:
            return
    channel.send(None)


def _manage():
    while True:
        with lock:
            if sleeping_tasklets:
                endtime = sleeping_tasklets[0][0]
                if endtime <= time.time():
                    channel = sleeping_tasklets[0][1]
                    del sleeping_tasklets[0]
                    channel.send(None)
            if sleeping_tasklets:
                cond.wait(sleeping_tasklets[0][0] - time.time())
            else:
                cond.wait()


if not manager_running:
    _manager_thread = threading.Thread(target=_manage)
    _manager_thread.daemon = True
    _manager_thread.start()
    manager_running = True
