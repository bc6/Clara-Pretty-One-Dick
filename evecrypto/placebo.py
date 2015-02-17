#Embedded file name: evecrypto\placebo.py
import binascii
import blue

def get_random_bytes(byteCount):
    return '\x00' * byteCount


def crypto_hash(*args):
    return str(binascii.crc_hqx(blue.marshal.Save(args), 0))


def create_context():
    return PlaceboCryptoContext()


def sign(data):
    return (data, 0)


def verify(signedData):
    return (signedData[0], signedData[1] == 0)


class PlaceboCryptoContext(object):

    def Initialize(self, **_):
        return {}

    def SymmetricDecryption(self, cryptedPacket):
        return cryptedPacket

    def SymmetricEncryption(self, plainPacket):
        return plainPacket

    def OptionalSymmetricEncryption(self, plainPacket):
        return plainPacket


publicKey, publicKeyVersion = (None, None)
privateKey, privateKeyVersion = (None, None)
