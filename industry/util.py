#Embedded file name: industry\util.py
"""
Contains some basic helper classes and utility methods for the industry module.
"""
import fsdlite
import industry

def repr(obj, exclude = []):
    """
    A nice default repr implementation for classes that also works with slots.
    """
    exclude.append('__immutable__')
    if hasattr(obj, '__slots__'):
        return '<industry.{} {}>'.format(obj.__class__.__name__, ' '.join([ '{}={}'.format(key.strip('_'), getattr(obj, key, None)) for key in obj.__slots__ if key not in exclude ]))
    elif hasattr(obj, '__dict__'):
        return '<industry.{} {}>'.format(obj.__class__.__name__, ' '.join([ '{}={}'.format(key.strip('_'), value) for key, value in obj.__dict__.iteritems() if key not in exclude ]))
    else:
        return str(obj)


def mean(values):
    """
    Compute the mean of multiple values.
    """
    if len(values):
        return sum(values) / float(len(values))
    return 0


class Property(object):
    """
    Implements a replacement for property() which wraps a get / set
    pattern around an object attribute and emits a named signal when
    the value is changed.
    """

    def __init__(self, name, signal = None, getter = None):
        self.name = name
        self.signal = signal
        self.getter = getter

    def __get__(self, obj, objtype = None):
        if obj is None:
            return self
        elif self.getter:
            return self.getter(obj)
        else:
            return getattr(obj, self.name, None)

    def __set__(self, obj, value):
        existing = getattr(obj, self.name, None)
        setattr(obj, self.name, value)
        if value != existing and self.signal:
            signal = getattr(obj, self.signal, None)
            if signal:
                signal(obj)

    def __delete__(self, obj):
        raise AttributeError('Cannot delete attribute')


class ExceptionEater(object):
    """
    Catches all exceptions and logs them out instead of raising. Usage:
    
    with industry.ExceptionEater("Some message"):
        ...
    """

    def __init__(self, *args):
        self.args = args

    def __enter__(self):
        pass

    def __exit__(self, eType, eVal, tb):
        if eType is not None:
            industry.logger.exception(self.args)
        return True


class SlotBase(object):
    """
    Base class for all industry activities, defines a consistent interface for all
    activities to quack like a duck, and some helper methods.
    """
    __slots__ = []

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        for key in obj.__slots__:
            if not key.startswith('__'):
                setattr(obj, key, None)

        return obj

    def __init__(self, *args, **kwargs):
        object.__init__(self)
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        return industry.repr(self)

    @classmethod
    def extend(cls, mixin):
        fsdlite.extend_class(cls, mixin)


class Base(object):
    """
    Base class for all industry activities, defines a consistent interface for all
    activities to quack like a duck, and some helper methods.
    """

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        object.__init__(self)
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        return industry.repr(self)

    @classmethod
    def extend(cls, mixin):
        fsdlite.extend_class(cls, mixin)
