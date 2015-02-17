#Embedded file name: evecrypto\cryptoapi.py
"""
Cryptography interface for macho that allows easy switching
between cryptoapi and unencrypted
"""
import blue
import binascii
import threading
import evecrypto.settings as settings
from .publickey import get_keystr as get_public_keystr
if settings.boot.role == 'client':

    def get_private_keystr():
        return None


else:
    from .restricted.privatekey import get_keystr as get_private_keystr
cryptoAPI_cryptoContext = None
_cryptoContextLock = threading.Lock()

def get_crypto_context():
    global cryptoAPI_cryptoContext
    if cryptoAPI_cryptoContext is not None:
        return cryptoAPI_cryptoContext
    with _cryptoContextLock:
        if cryptoAPI_cryptoContext is not None:
            return cryptoAPI_cryptoContext
        cryptoAPI_cryptoContext = blue.crypto.CryptAcquireContext(None, settings.cryptoAPI_cryptoProvider, settings.cryptoAPI_PROV_cryptoProviderType, blue.crypto.CRYPT_VERIFYCONTEXT | blue.crypto.CRYPT_SILENT)
    return cryptoAPI_cryptoContext


def crypto_hash(*args):
    hashed = blue.crypto.CryptCreateHash(cryptoAPI_cryptoContext, settings.cryptoAPI_CALG_hashMethod, None, 0)
    blue.crypto.CryptHashData(hashed, blue.marshal.Save(args), 0)
    return blue.crypto.CryptGetHashParam(hashed, blue.crypto.HP_HASHVAL, 0)


def sign(data):
    hashed = blue.crypto.CryptCreateHash(cryptoAPI_cryptoContext, settings.cryptoAPI_CALG_hashMethod, None, 0)
    packedData = blue.marshal.Save(data)
    blue.crypto.CryptHashData(hashed, packedData, 0)
    signed = blue.crypto.CryptSignHash(hashed, blue.crypto.AT_KEYEXCHANGE, 0)
    return (packedData, signed)


def verify(signedData):
    hashed = blue.crypto.CryptCreateHash(cryptoAPI_cryptoContext, settings.cryptoAPI_CALG_hashMethod, None, 0)
    blue.crypto.CryptHashData(hashed, signedData[0], 0)
    return (blue.marshal.Load(signedData[0]), blue.crypto.CryptVerifySignature(hashed, signedData[1], publicKey, 0))


def create_context():
    return CryptoApiCryptoContext()


def get_random_bytes(byteCount):
    return blue.crypto.CryptGenRandom(get_crypto_context(), byteCount)


class CryptoApiCryptoContext:

    def __init__(self):
        self.securityProviderType = settings.cryptoAPI_cryptoProviderType
        self.symmetricKey = None
        self.symmetricKeyCipher = None
        self.symmetricKeyMethod = settings.symmetricKeyMethod
        self.symmetricKeyLength = settings.symmetricKeyLength
        self.hashMethod = settings.hashMethod

    def __CreateActualCipher(self, unencryptedKey, symmetricKey):
        if unencryptedKey is None:
            return blue.crypto.CryptImportKey(get_crypto_context(), symmetricKey, privateKey, 0)
        else:
            return unencryptedKey

    def Initialize(self, request = None):
        unencryptedKey = None
        if request is not None:
            securityProviderType = request.get('crypting_securityprovidertype', None) or settings.cryptoAPI_cryptoProviderType
            requestedKey = request.get('crypting_sessionkey', None) or None
            keyLength = request.get('crypting_sessionkeylength', None) or settings.symmetricKeyLength
            keyMethod = request.get('crypting_sessionkeymethod', None) or settings.symmetricKeyMethod
            signingHashMethod = request.get('signing_hashmethod', None) or settings.hashMethod
        else:
            securityProviderType = settings.cryptoAPI_cryptoProviderType
            keyLength = settings.symmetricKeyLength
            keyMethod = settings.symmetricKeyMethod
            signingHashMethod = settings.hashMethod
            unencryptedKey = blue.crypto.CryptGenKey(get_crypto_context(), settings.cryptoAPI_CALG_symmetricKeyMethod, keyLength << 16 | blue.crypto.CRYPT_EXPORTABLE)
            if settings.symmetricKeyIVLength:
                keyIV = get_random_bytes(settings.symmetricKeyIVLength / 8)
                blue.crypto.CryptSetKeyParam(unencryptedKey, blue.crypto.KP_IV, keyIV)
            requestedKey = blue.crypto.CryptExportKey(unencryptedKey, publicKey, blue.crypto.SIMPLEBLOB, 0)
        if self.securityProviderType and securityProviderType and self.securityProviderType != securityProviderType:
            return 'Security Provider Type Unacceptable - Type is %s but should be %s' % (securityProviderType, self.securityProviderType)
        if securityProviderType:
            self.securityProviderType = securityProviderType
        if self.symmetricKeyLength and keyLength and self.symmetricKeyLength != keyLength:
            return 'Symmetric Key Length Unacceptable - Length is %s but should be %s' % (keyLength, self.symmetricKeyLength)
        if keyLength:
            self.symmetricKeyLength = keyLength
        if self.symmetricKeyMethod and keyMethod and self.symmetricKeyMethod != keyMethod:
            return 'Symmetric Key Method Unacceptable - Method is %s but should be %s' % (keyMethod, self.symmetricKeyMethod)
        if keyMethod:
            self.symmetricKeyMethod = keyMethod
        if self.hashMethod and signingHashMethod and self.hashMethod != signingHashMethod:
            return 'Hash Method Unacceptable - Hash is %s but should be %s' % (signingHashMethod, self.hashMethod)
        if settings.hashMethod:
            self.hashMethod = settings.hashMethod
        self.symmetricKey = requestedKey
        self.symmetricKeyCipher = self.__CreateActualCipher(unencryptedKey, self.symmetricKey)
        return {'crypting_securityprovidertype': securityProviderType,
         'crypting_sessionkey': requestedKey,
         'crypting_sessionkeylength': keyLength,
         'crypting_sessionkeymethod': keyMethod,
         'signing_hashmethod': signingHashMethod}

    def SymmetricDecryption(self, cryptedPacket):
        return blue.crypto.CryptDecrypt(self.symmetricKeyCipher, None, True, 0, cryptedPacket)

    def SymmetricEncryption(self, plainPacket):
        return blue.crypto.CryptEncrypt(self.symmetricKeyCipher, None, True, 0, plainPacket)

    def OptionalSymmetricEncryption(self, plainPacket):
        if self.symmetricKeyCipher is not None:
            return self.SymmetricEncryption(plainPacket)
        return plainPacket


def load_key_and_version(keystring):
    if keystring is None:
        return (None, None)
    loaded = blue.marshal.Load(binascii.a2b_hex(keystring))
    key = blue.crypto.CryptImportKey(get_crypto_context(), loaded, None, 0)
    version = crypto_hash(loaded)
    return (key, version)


publicKey, publicKeyVersion = load_key_and_version(get_public_keystr())
privateKey, privateKeyVersion = load_key_and_version(get_private_keystr())
