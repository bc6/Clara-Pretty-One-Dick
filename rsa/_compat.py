#Embedded file name: rsa\_compat.py
"""Python compatibility wrappers."""
from __future__ import absolute_import
import sys
from struct import pack
try:
    MAX_INT = sys.maxsize
except AttributeError:
    MAX_INT = sys.maxint

MAX_INT64 = 9223372036854775807L
MAX_INT32 = 2147483647L
MAX_INT16 = 32767
if MAX_INT == MAX_INT64:
    MACHINE_WORD_SIZE = 64
elif MAX_INT == MAX_INT32:
    MACHINE_WORD_SIZE = 32
else:
    MACHINE_WORD_SIZE = 64
try:
    unicode_type = unicode
    have_python3 = False
except NameError:
    unicode_type = str
    have_python3 = True

if str is unicode_type:

    def byte_literal(s):
        return s.encode('latin1')


else:

    def byte_literal(s):
        return s


try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)

b = byte_literal
try:
    bytes_type = bytes
except NameError:
    bytes_type = str

ZERO_BYTE = b('\x00')
EMPTY_BYTE = b('')

def is_bytes(obj):
    """
    Determines whether the given value is a byte string.
    
    :param obj:
        The value to test.
    :returns:
        ``True`` if ``value`` is a byte string; ``False`` otherwise.
    """
    return isinstance(obj, bytes_type)


def is_integer(obj):
    """
    Determines whether the given value is an integer.
    
    :param obj:
        The value to test.
    :returns:
        ``True`` if ``value`` is an integer; ``False`` otherwise.
    """
    return isinstance(obj, integer_types)


def byte(num):
    """
    Converts a number between 0 and 255 (both inclusive) to a base-256 (byte)
    representation.
    
    Use it as a replacement for ``chr`` where you are expecting a byte
    because this will work on all current versions of Python::
    
    :param num:
        An unsigned integer between 0 and 255 (both inclusive).
    :returns:
        A single byte.
    """
    return pack('B', num)


def get_word_alignment(num, force_arch = 64, _machine_word_size = MACHINE_WORD_SIZE):
    """
    Returns alignment details for the given number based on the platform
    Python is running on.
    
    :param num:
        Unsigned integral number.
    :param force_arch:
        If you don't want to use 64-bit unsigned chunks, set this to
        anything other than 64. 32-bit chunks will be preferred then.
        Default 64 will be used when on a 64-bit machine.
    :param _machine_word_size:
        (Internal) The machine word size used for alignment.
    :returns:
        4-tuple::
    
            (word_bits, word_bytes,
             max_uint, packing_format_type)
    """
    max_uint64 = 18446744073709551615L
    max_uint32 = 4294967295L
    max_uint16 = 65535
    max_uint8 = 255
    if force_arch == 64 and _machine_word_size >= 64 and num > max_uint32:
        return (64,
         8,
         max_uint64,
         'Q')
    elif num > max_uint16:
        return (32,
         4,
         max_uint32,
         'L')
    elif num > max_uint8:
        return (16,
         2,
         max_uint16,
         'H')
    else:
        return (8,
         1,
         max_uint8,
         'B')
