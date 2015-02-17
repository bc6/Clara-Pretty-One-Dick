#Embedded file name: ccpProfile\blueTaskletImplementation.py
import blue
from . import decorator
EnterTasklet = blue.pyos.taskletTimer.EnterTasklet
ReturnFromTasklet = blue.pyos.taskletTimer.ReturnFromTasklet
GetCurrent = blue.pyos.taskletTimer.GetCurrent

class Timer(object):
    __slots__ = ['ctxt']

    def __init__(self, context):
        self.ctxt = context

    def __enter__(self):
        self.ctxt = EnterTasklet(self.ctxt)

    def __exit__(self, *_):
        ReturnFromTasklet(self.ctxt)


class TimerPush(Timer):
    GetCurrent = blue.pyos.taskletTimer.GetCurrent

    def __init__(self, context):
        fullctx = '::'.join((self.GetCurrent(), context))
        Timer.__init__(self, fullctx)


def TimedFunction(context = None):

    def Wrapper(function, *args, **kwargs):
        newContext = EnterTasklet(context or repr(function))
        try:
            return function(*args, **kwargs)
        finally:
            ReturnFromTasklet(newContext)

    return decorator.decorator(Wrapper)


def PushTimer(context):
    return EnterTasklet(context)


def PopTimer(context):
    return ReturnFromTasklet(context)


def CurrentTimer():
    return GetCurrent()
