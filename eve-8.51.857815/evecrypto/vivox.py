#Embedded file name: evecrypto\vivox.py
"""
Provides a public key string for use in signing Vivox documents.
"""
import base64
import binascii
import blue
import cPickle
from . import settings
from .crypto import GetCryptoContext

def get_vivox_public_key():
    return '53225c7830365c7830325c7830305c7830305c7830305c7861345c7830305c783030525341315c7830305c7830325c7830305c7830305c7830315c7830305c7830315c783030476d2e5c7861345c786461375c7865625c786435355c7863345c7866626848643f584a5c7863615e5c78616553485c7861325c7862395c7862335c7864314a644a345c7830335c7831325c7839345c7864325c7866375c7839615c7838655c7838645c7861624a5c7866645c7838665c786335475c7865375c7861375c786465465c7866395c7830345c7830315c7839645c78616450275c7831315c7862375c7863665c7866335c7830655c7861615c783766785c786162220a70310a2e'


def vivox_sign(data):
    hashed = blue.crypto.CryptCreateHash(GetCryptoContext(), settings.cryptoAPI_CALG_hashMethod, None, 0)
    blue.crypto.CryptHashData(hashed, data, 0)
    sign = blue.crypto.CryptSignHash(hashed, blue.crypto.AT_KEYEXCHANGE, 0)
    return base64.encodestring(sign).replace('\n', '')


def vivox_verify(data, signature):
    cryptoContext = blue.crypto.CryptAcquireContext(None, blue.crypto.MS_ENHANCED_PROV, blue.crypto.PROV_RSA_FULL, blue.crypto.CRYPT_VERIFYCONTEXT | blue.crypto.CRYPT_SILENT)
    loadedkey = cPickle.loads(binascii.a2b_hex(get_vivox_public_key()))
    importedkey = blue.crypto.CryptImportKey(cryptoContext, loadedkey, None, 0)
    sign = base64.decodestring(signature)
    hashed = blue.crypto.CryptCreateHash(cryptoContext, blue.crypto.CALG_SHA, None, 0)
    blue.crypto.CryptHashData(hashed, data, 0)
    return blue.crypto.CryptVerifySignature(hashed, sign, importedkey, 0)
