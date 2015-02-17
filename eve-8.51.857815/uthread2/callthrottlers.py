#Embedded file name: uthread2\callthrottlers.py
from . import sleep

class CallCombiner(object):
    """
    Takes consecutive calls and combines them to one by sleeping initially and ignore
    other calls until it has slept. Note that this can only be used for specific use
    cases where multiple calls will give the exact same result
    """

    def __init__(self, func, throttleTime):
        self.isBeingCalled = False
        self.func = func
        self.throttleTime = throttleTime

    def __call__(self, *args, **kwargs):
        if self.isBeingCalled:
            return
        self.isBeingCalled = True
        try:
            sleep(self.throttleTime)
            return self.func(*args, **kwargs)
        finally:
            self.isBeingCalled = False
