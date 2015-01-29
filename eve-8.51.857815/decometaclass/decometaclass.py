#Embedded file name: decometaclass\decometaclass.py
"""
See documentation for metaclasses to understand.
It creates a class object with a custom class creation function that, instead
of creating instances of this objects, creates the underlying blue object with
a decorator hanging off of it.
"""
try:
    import blue
except:
    import binbootstrapper
    binbootstrapper.update_binaries(__file__, binbootstrapper.DLL_BLUE)
    import blue

import types
types.BlueType = type(blue.os)

class DecoMetaclass(type):
    """
    Metaclass that gets a blue class instance and returns it as a blue.BlueWrapper
    object.
    """

    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        cls.__persistvars__ = cls.CombineLists('__persistvars__')
        cls.__nonpersistvars__ = cls.CombineLists('__nonpersistvars__')
        return cls

    def __call__(cls, inst = None, initDict = None, *args, **kwargs):
        """
        Override Instance creation. We don't actually create an instance of cls,
        But rather attach a deco to a BlueWrapper of a blue object.
        inst and initDict arguments are used when unpickling
        """
        if not inst:
            inst = blue.classes.CreateInstance(cls.__cid__)
        inst.__klass__ = cls
        if initDict:
            for k, v in initDict.iteritems():
                setattr(inst, k, v)

        try:
            inst.__init__()
        except AttributeError:
            pass

        return inst

    def CombineLists(cls, name):
        """
        Combine attribute lists by walking over all parent classes
        """
        result = []
        for b in cls.__mro__:
            if hasattr(b, name):
                result += list(getattr(b, name))

        return result

    subclasses = {}


def GetDecoMetaclassInst(cid):

    class parentclass(object):
        __metaclass__ = DecoMetaclass
        __cid__ = cid

    return parentclass


BlueWrappedMetaclass = DecoMetaclass
WrapBlueClass = GetDecoMetaclassInst
