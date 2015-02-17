#Embedded file name: fsdlite\util.py
"""
Contains some basic helper classes and utility methods for the industry module.
"""
import weakref
import inspect
import types
import copy

def repr(obj, module = None, exclude = []):
    """
    A nice default repr implementation for classes that also works with slots.
    """
    module = '' if module else module + '.'
    if hasattr(obj, '__slots__'):
        return '<{}{} {}>'.format(module, obj.__class__.__name__, ' '.join([ '{}={}'.format(key, getattr(obj, key, None)) for key in obj.__slots__ if key not in exclude ]))
    elif hasattr(obj, '__dict__'):
        return '<{}{} {}>'.format(module, obj.__class__.__name__, ' '.join([ '{}={}'.format(key, value) for key, value in obj.__dict__.iteritems() if key not in exclude ]))
    else:
        return str(obj)


class Immutable(type):
    """
    MetaClass which prevents modifying any properties of said class after
    construction. Only during the __init__ can its data be modified. Usage:
    
        class MyClass(object):
            __metaclass__ = fsdlite.Immutable
    """

    def __new__(cls, name, bases, attributes):
        if '__slots__' in attributes:
            attributes['__slots__'].append('__immutable__')
        return type.__new__(cls, name, bases, attributes)

    def __init__(cls, name, bases, attributes):
        old_new = cls.__new__
        old_init = cls.__init__
        old_delattr = cls.__delattr__
        old_setattr = cls.__setattr__

        def new_new(klass, *args, **kwargs):
            immutable = not kwargs.pop('mutable', False)
            obj = old_new(klass, *args, **kwargs)
            old_setattr(obj, '__immutable__', immutable)
            return obj

        def new_init(self, *args, **kwargs):
            immutable = not kwargs.pop('mutable', False)
            old_setattr(self, '__immutable__', False)
            old_init(self, *args, **kwargs)
            if type(self) is cls:
                old_setattr(self, '__immutable__', immutable)

        def new_delattr(self, name):
            if getattr(self, '__immutable__', None) is True:
                raise TypeError('Immutable object')
            else:
                old_delattr(self, name)

        def new_setattr(self, name, value):
            if getattr(self, '__immutable__', None) is True and name != '__immutable__':
                raise TypeError('Immutable object')
            else:
                old_setattr(self, name, value)

        def new_enter(self):
            if getattr(self, '__immutable__', None) is True:
                old_setattr(self, '__immutable__', -1)

        def new_exit(self, exc, val, tb):
            if getattr(self, '__immutable__', None) == -1:
                old_setattr(self, '__immutable__', True)

        def new_copy(self):
            obj = self.__class__.__new__(self.__class__)
            old_setattr(obj, '__immutable__', False)
            if hasattr(self, '__dict__'):
                obj.__dict__ = copy.copy(self.__dict__)
            else:
                for name in self.__slots__:
                    if hasattr(self, name) and not name.startswith('__'):
                        old_setattr(obj, name, getattr(self, name))

            old_setattr(obj, '__immutable__', False)
            return obj

        def new_deepcopy(self, memo):
            obj = self.__class__.__new__(self.__class__)
            old_setattr(obj, '__immutable__', False)
            if hasattr(self, '__dict__'):
                obj.__dict__ = copy.deepcopy(self.__dict__)
            else:
                for name in self.__slots__:
                    if hasattr(self, name) and not name.startswith('__'):
                        old_setattr(obj, name, copy.deepcopy(getattr(self, name)))

            old_setattr(obj, '__immutable__', False)
            return obj

        def copy_helper(self):
            return copy.copy(self)

        def deepcopy_helper(self):
            return copy.deepcopy(self)

        cls.__new__ = staticmethod(new_new)
        cls.__init__ = new_init
        cls.__delattr__ = new_delattr
        cls.__setattr__ = new_setattr
        cls.__enter__ = new_enter
        cls.__exit__ = new_exit
        cls.__copy__ = new_copy
        cls.__deepcopy__ = new_deepcopy
        cls.copy = copy_helper
        cls.deepcopy = deepcopy_helper


class WeakMethod(object):
    """
    Implements a weak reference for a bound method, useful for passing callbacks
    when we don't want to increment a reference count for the object being called.
    """

    def __init__(self, f):
        self.f = f.im_func
        self.c = weakref.ref(f.im_self)

    def __call__(self, *args):
        if self.c() is None:
            raise TypeError('Method called on dead object')
        apply(self.f, (self.c(),) + args)


def extend_class(cls, mixin):
    """
    Copies the methods from one class type onto another. Allows ruby style extension of
    existing python classes at import time without changing bases or the original type name.
    """
    for name, member in inspect.getmembers(mixin):
        if inspect.ismethod(member):
            setattr(cls, name, types.MethodType(member.im_func, None, cls))


class Extendable(object):
    """
    Add the extend_class method to a type through inheritence so you can go:
    
    MyClass.extend(AnotherClass)
    """

    @classmethod
    def extend(cls, mixin):
        extend_class(cls, mixin)
