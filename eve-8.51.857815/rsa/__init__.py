#Embedded file name: rsa\__init__.py
"""RSA module

Module for calculating large primes, and RSA encryption, decryption, signing
and verification. Includes generating public and private keys.

WARNING: this implementation does not use random padding, compression of the
cleartext input to prevent repetitions, or other common security improvements.
Use with care.

If you want to have a more secure implementation, use the functions from the
``rsa.pkcs1`` module.

"""
__author__ = 'Sybren Stuvel, Barry Mead and Yesudeep Mangalapilly'
__date__ = '2012-06-17'
__version__ = '3.1.1'
from rsa.key import newkeys, PrivateKey, PublicKey
from rsa.pkcs1 import encrypt, decrypt, sign, verify, DecryptionError, VerificationError
if __name__ == '__main__':
    import doctest
    doctest.testmod()
__all__ = ['newkeys',
 'encrypt',
 'decrypt',
 'sign',
 'verify',
 'PublicKey',
 'PrivateKey',
 'DecryptionError',
 'VerificationError']
