#Embedded file name: rsa\parallel.py
"""Functions for parallel computation on multiple cores.

Introduced in Python-RSA 3.1.

.. note::

    Requires Python 2.6 or newer.

"""
from __future__ import print_function
import multiprocessing as mp
import rsa.prime
import rsa.randnum

def _find_prime(nbits, pipe):
    while True:
        integer = rsa.randnum.read_random_int(nbits)
        integer |= 1
        if rsa.prime.is_prime(integer):
            pipe.send(integer)
            return


def getprime(nbits, poolsize):
    """Returns a prime number that can be stored in 'nbits' bits.
    
    Works in multiple threads at the same time.
    
    >>> p = getprime(128, 3)
    >>> rsa.prime.is_prime(p-1)
    False
    >>> rsa.prime.is_prime(p)
    True
    >>> rsa.prime.is_prime(p+1)
    False
    
    >>> from rsa import common
    >>> common.bit_size(p) == 128
    True
    
    """
    pipe_recv, pipe_send = mp.Pipe(duplex=False)
    procs = [ mp.Process(target=_find_prime, args=(nbits, pipe_send)) for _ in range(poolsize) ]
    [ p.start() for p in procs ]
    result = pipe_recv.recv()
    [ p.terminate() for p in procs ]
    return result


__all__ = ['getprime']
if __name__ == '__main__':
    print('Running doctests 1000x or until failure')
    import doctest
    for count in range(100):
        failures, tests = doctest.testmod()
        if failures:
            break
        if count and count % 10 == 0:
            print('%i times' % count)

    print('Doctests done')
