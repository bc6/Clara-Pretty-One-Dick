#Embedded file name: carbon/common/lib\cdsuc.py
"""
This module collects useful, reusable data structures and debugging classes / mixins.
ATTN: The data structures are depdended on by game code.
"""
import types
import itertools

class EnumList(object):
    """
    Takes a list of strings that is becomes read only, every element in the list is
    accesible by [instance name].ELEMENT and the data is iteratable via the instance name.
    
    Example:
        FOODS_I_LIKE = EnumList( "pizza", "hamburger", "steak" )
        for each in FOODS_I_LIKE: print each >> "pizza", "hamburger", "steak"
        print FOODS_I_LIKE.PIZZA >> "pizza"
        print FOODS_I_LIKE.FISH >> AttributeError
    """

    def __init__(self, *data):
        __data = {}
        for each in iter(data):
            if type(each) in types.StringTypes:
                val = intern(each.lower())
                __data[val] = val
                self.__dict__[val.upper()] = val

        self.__data = __data

    def __getattr__(self, name):
        lname = str(name).lower()
        val = self.__data.get(lname, None)
        if val:
            return val
        raise AttributeError, name

    def __iter__(self):
        for each in self.__data:
            yield each

    def __add__(self, other):
        """
        Returns a new EnumList, combining elements in self and other
        """
        l = list(itertools.chain(self, other))
        return EnumList(*l)

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        """
        Returns iterator on items in self but not in other
        """
        return itertools.ifilter(lambda x: x not in iter(other), self)

    def __str__(self):
        sortedUpperCaseKeys = map(lambda x: x.upper(), self.__data.keys())
        sortedUpperCaseKeys.sort()
        return ', '.join(sortedUpperCaseKeys)


class SpyMixin(object):
    """
    Helper class for refactoring / debugging.
    Usage:
        class UnderDebug( SpyMixin, parentClass ):
            .
            .
            .
            __init__( self, ... ):
                .
                .
                .
                self.SetWatchAttributes( 'name0', 'name1', ..., 'nameN' )
                # nameX is attribute of class UnderDebug
    """

    def SetWatchAttributes(self, *args):
        object.__setattr__(self, 'attributesUnderWatch', [])
        for arg in args:
            self.attributesUnderWatch.append(arg)

    def __setattr__(self, name, value):
        if not hasattr(self, 'attributesUnderWatch'):
            object.__setattr__(self, 'attributesUnderWatch', [])
        if name in self.attributesUnderWatch:
            print 'Setting %s to value %s' % (name, repr(value))
        object.__setattr__(self, name, value)
