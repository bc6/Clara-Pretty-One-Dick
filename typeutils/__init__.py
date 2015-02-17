#Embedded file name: typeutils\__init__.py
"""
Utilities for type casting, checking, validation and so on as well as code
meant for extending the python basic types that don't have their own utils
(like datetimeutils and itertoolsex). Although if many such utilities for a
certain type start piling up here, consider moving them to their own file.

As a very generally rule of thumb, anything put in here should fulfill one of
these criteria:

    - cast one python type to another using other means than python supplies
    - this includes type-cast "forcing" and/or "safe casts" that ensure the
      return of a particular type even if conventional type-casting fails.
    - check for or validate a certain type that doesn't have it's own utils
      file
    - return the result of such processing
    - act as a mutator function on a temporal object
    - be independent, generic and "black-boxy". If your function would not be
      useable to anyone else either because of dependency on other packages or
      because of specialization bordering on "adhocyness", it probably doesn't
      belong here
    - you as a programmer feel very strongly it should be here

This code uses the PEP 8 python coding style guide in accordance with internal
CCP standards with a few things borrowed from the Google python coding
guidelines.

    - http://www.python.org/dev/peps/pep-0008/
    - http://eve/wiki/Python_Coding_Guidelines
    - http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

This code uses reStructuredText/Sphinx docstring markup mainly for parameter
and return value type hinting.

    - http://www.python.org/dev/peps/pep-0287/
    - http://sphinx-doc.org/markup/desc.html#info-field-lists
"""
from __future__ import print_function
import sys
import itertools
import collections
import re
REGEX_TYPE = type(re.compile(''))

class ComparableMixin(object):
    """
    Mixin class for types that should be comparable.
    Subclasses must implement `__lt__`.
    Other comparison functions can be overridden if desired.
    """

    def __new__(cls, *args):
        obj = object.__new__(cls, *args)
        if not hasattr(obj, '__lt__'):
            raise NotImplementedError('__lt__ must be overridden.')
        return obj

    def __eq__(self, other):
        return not self < other and not other < self

    def __ne__(self, other):
        return self < other or other < self

    def __gt__(self, other):
        return other < self

    def __ge__(self, other):
        return not self < other

    def __le__(self, other):
        return not other < self


def float_eval(value, default = 0.0):
    """Safe evaluation of any type to a float value. The optional default value
    will be returned on any parsing or casting error. You can also pass None as
    the default to check for failures.
    
    Useful shortcut where you have a string that you're know is a float value
    in string form like prefs entries, DB entries from varchar fields or HTTP
    GET/POST arguments
    
    :type value: any
    :type default: float or None
    :rtype: float or None
    """
    if isinstance(value, float):
        return value
    if isinstance(value, (int, long)):
        return float(value)
    if isinstance(value, basestring):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    else:
        return default


def int_eval(value, default = 0):
    """Safe evaluation of any type to an int value. The optional default value
    will be returned on any parsing or casting error. You can also pass None as
    the default to check for failures.
    
    Long values that contain values larger than ints can contain (or strings
    containing such values) will evaluate to a long.
    
    Useful shortcut where you have a string that you're know is an int value
    in string form like prefs entries, DB entries from varchar fields or HTTP
    GET/POST arguments
    
    :type value: any
    :type default: int or None
    :rtype: int or long or None
    """
    if isinstance(value, int):
        return value
    if isinstance(value, (long, float)):
        return int(value)
    if isinstance(value, basestring):
        try:
            if '.' in value:
                return int(float(value))
            return int(value)
        except (TypeError, ValueError):
            return default

    else:
        return default


def bool_eval(value):
    """Evaluates if a value should be interpreted as a boolean True value.
    That means a string that is "True" regardless of case and whitespace
    characters as well as any numerical value other than 0 and of course a
    boolean type of true. Anything else returns False, including all
    objects.
    
    Boolean types are return their same value.
    
    Strings and unicode strings of 'true' (case insensitive) evaluate to True.
    
    Strings and unicode strings that are longs, integers or floats evaluate to
    the same as their "pure" types (long, int, float) would evaluate to.
    
    Longs, Integers and Floating number evaluate to False if they are 0L, 0 and
    0.0 respectively, anything else is True.
    
    Any other type or object yield a False return.
    
    Very useful for evaluating values read from prefs.ini that can use
    different formats.
    
    :type value: any
    :rtype: bool
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, basestring):
        if value.strip().lower() == 'true':
            return True
        elif value.isdigit():
            return bool(int(value))
        else:
            neg = False
            if value.startswith('-'):
                value = value[1:]
                neg = True
                if value.isdigit():
                    return bool(-int(value))
            parts = value.split('.')
            if len(parts) == 2:
                if parts[0].isdigit() and parts[1].isdigit():
                    if neg:
                        return bool(-float(value))
                    else:
                        return bool(float(value))
            return False
    else:
        if isinstance(value, (int, long, float)):
            return bool(value)
        return False


def total_size(o, handlers = None, verbose = False):
    """ Returns the approximate memory footprint an object and all of its contents.
    
    From http://code.activestate.com/recipes/577504/
    
    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:
    
        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}
    
    
    
    """
    dict_handler = lambda d: itertools.chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
     list: iter,
     collections.deque: iter,
     dict: dict_handler,
     set: iter,
     frozenset: iter}
    handlers = handlers or {}
    all_handlers.update(handlers)
    seen = set()
    default_size = sys.getsizeof(0)

    def sizeof(o):
        if id(o) in seen:
            return 0
        seen.add(id(o))
        s = sys.getsizeof(o, default_size)
        if verbose:
            print(s, type(o), repr(o), file=sys.stderr)
        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break

        return s

    return sizeof(o)


def ip_to_int(ip):
    """
    
    :param ip:
    :type ip: str
    :return:
    :rtype: int
    :raises ValueError: If the given string is not a valid IP address
    """
    parts = ip.split('.')
    if len(parts) != 4:
        raise ValueError('Not a valid IP address')
    i = 0
    ii = int(parts[0])
    if ii < 0 or ii > 255:
        raise ValueError('Not a valid IP address')
    i += ii << 24
    ii = int(parts[1])
    if ii < 0 or ii > 255:
        raise ValueError('Not a valid IP address')
    i += ii << 16
    ii = int(parts[2])
    if ii < 0 or ii > 255:
        raise ValueError('Not a valid IP address')
    i += ii << 8
    ii = int(parts[3])
    if ii < 0 or ii > 255:
        raise ValueError('Not a valid IP address')
    i += ii
    return i


def int_to_ip(i):
    """
    
    :param i:
    :type i: int
    :return:
    :rtype: str
    """
    d = i & 255
    i >>= 8
    c = i & 255
    i >>= 8
    b = i & 255
    a = i >> 8
    return '%s.%s.%s.%s' % (a,
     b,
     c,
     d)
