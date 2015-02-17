#Embedded file name: pytelemetry\zoning.py
from contextlib import contextmanager
import functools
import types
try:
    import blue
except ImportError:
    blue = None

__all__ = ['ZONE_FUNCTION',
 'ZONE_METHOD',
 'ZONE_METHOD_IN_WAITING',
 'ZONE_PER_METHOD',
 'APPEND_TO_ZONE',
 'TelemetryContext']
if not blue or not blue.pyos.markupZonesInPython:

    def ZONE_FUNCTION(func):
        return func


    def ZONE_METHOD(method):
        return method


    def ZONE_METHOD_IN_WAITING(name, method):
        return method


    class ZONE_PER_METHOD(type):
        pass


    def APPEND_TO_ZONE(label):
        pass


    @contextmanager
    def TelemetryContext(name):
        yield


else:

    def ZONE_FUNCTION(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                blue.statistics.EnterZone(func.__name__)
                res = func(*args, **kwargs)
            finally:
                blue.statistics.LeaveZone()

            return res

        return wrapper


    def ZONE_METHOD(method):
        zoneName = method.__name__

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                blue.statistics.EnterZone(zoneName)
                res = method(self, *args, **kwargs)
            finally:
                blue.statistics.LeaveZone()

            return res

        return wrapper


    def ZONE_METHOD_IN_WAITING(name, method):
        zoneName = name + '::' + method.__name__

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                blue.statistics.EnterZone(zoneName)
                res = method(self, *args, **kwargs)
            finally:
                blue.statistics.LeaveZone()

            return res

        return wrapper


    class ZONE_PER_METHOD(type):

        def __new__(mcs, name, bases, dct):
            for key in dct:
                if isinstance(dct[key], types.FunctionType):
                    dct[key] = ZONE_METHOD_IN_WAITING(name, dct[key])

            return type.__new__(mcs, name, bases, dct)


    def APPEND_TO_ZONE(label):
        blue.statistics.AppendToZone(str(label))


    @contextmanager
    def TelemetryContext(name):
        blue.statistics.EnterZone(name)
        try:
            yield
        finally:
            blue.statistics.LeaveZone()
