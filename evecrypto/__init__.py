#Embedded file name: evecrypto\__init__.py
"""
Cryptography wrapper for `blue.crypto`.
Ripped from the old `carbon.common.script.net.Crypto.py`
and `carbon.common.scrypt.sys.lowdown.py` files.

:mod:`evecrypto.crypto`: Provides a wrapper for switching between encrypted
and unecrypted versions.
Provides the general public interface,
callers should not need to dig around into implementations.

:mod:`evecrypto.vivox`: Sign and verify functions for vivox using the included
public key.

:mod:`evecrypto.restricted.gen_bluekey_and_goldlencd`:
Generates the bluekey.h and goldencd.pikl files.
Run as a CLI under Python 2.7.

:mod:`evecrypto.restricted.gen_pykeys`:
Generates the :mod:`evecrypto.publickey` and
:mod:`evecrypto.restricted.privatekey` files.
Run a server ExeFile with the `/generatekeys` argument to generate the files.
It isn't runnable under pure Python because `blue.marshal` isn't available.

The :mod:`evecrypto.restricted` namespace contains the private key and
generation utilities. They should not be available on clients.
"""
pass
