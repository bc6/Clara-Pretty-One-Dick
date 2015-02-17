#Embedded file name: rsa\randnum.py
"""Functions for generating random numbers."""
import os
from rsa import common, transform
from rsa._compat import byte

def read_random_bits(nbits):
    """Reads 'nbits' random bits.
    
    If nbits isn't a whole number of bytes, an extra byte will be appended with
    only the lower bits set.
    """
    nbytes, rbits = divmod(nbits, 8)
    randomdata = os.urandom(nbytes)
    if rbits > 0:
        randomvalue = ord(os.urandom(1))
        randomvalue >>= 8 - rbits
        randomdata = byte(randomvalue) + randomdata
    return randomdata


def read_random_int(nbits):
    """Reads a random integer of approximately nbits bits.
    """
    randomdata = read_random_bits(nbits)
    value = transform.bytes2int(randomdata)
    value |= 1 << nbits - 1
    return value


def randint(maxvalue):
    """Returns a random integer x with 1 <= x <= maxvalue
    
    May take a very long time in specific situations. If maxvalue needs N bits
    to store, the closer maxvalue is to (2 ** N) - 1, the faster this function
    is.
    """
    bit_size = common.bit_size(maxvalue)
    tries = 0
    while True:
        value = read_random_int(bit_size)
        if value <= maxvalue:
            break
        if tries and tries % 10 == 0:
            bit_size -= 1
        tries += 1

    return value
