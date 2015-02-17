#Embedded file name: jwt\__init__.py
u""" JSON Web Token implementation

Minimum implementation based on this spec:
http://self-issued.info/docs/draft-jones-json-web-token-01.html
"""
from __future__ import unicode_literals
import base64
import binascii
import hashlib
import hmac
import sys
from datetime import datetime
from calendar import timegm
from collections import Mapping
try:
    import json
except ImportError:
    import simplejson as json

if sys.version_info >= (3, 0, 0):
    unicode = str
    basestring = str
__version__ = u'0.3.0'
__all__ = [u'encode', u'decode', u'DecodeError']

class DecodeError(Exception):
    pass


class ExpiredSignature(Exception):
    pass


class InvalidAudience(Exception):
    pass


class InvalidIssuer(Exception):
    pass


signing_methods = {u'none': lambda msg, key: '',
 u'HS256': lambda msg, key: hmac.new(key, msg, hashlib.sha256).digest(),
 u'HS384': lambda msg, key: hmac.new(key, msg, hashlib.sha384).digest(),
 u'HS512': lambda msg, key: hmac.new(key, msg, hashlib.sha512).digest()}
verify_methods = {u'HS256': lambda msg, key: hmac.new(key, msg, hashlib.sha256).digest(),
 u'HS384': lambda msg, key: hmac.new(key, msg, hashlib.sha384).digest(),
 u'HS512': lambda msg, key: hmac.new(key, msg, hashlib.sha512).digest()}

def prepare_HS_key(key):
    if not isinstance(key, basestring) and not isinstance(key, bytes):
        raise TypeError(u'Expecting a string- or bytes-formatted key.')
    if isinstance(key, unicode):
        key = key.encode(u'utf-8')
    return key


prepare_key_methods = {u'none': lambda key: None,
 u'HS256': prepare_HS_key,
 u'HS384': prepare_HS_key,
 u'HS512': prepare_HS_key}
try:
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.Hash import SHA256
    from Crypto.Hash import SHA384
    from Crypto.Hash import SHA512
    from Crypto.PublicKey import RSA
    signing_methods.update({u'RS256': lambda msg, key: PKCS1_v1_5.new(key).sign(SHA256.new(msg)),
     u'RS384': lambda msg, key: PKCS1_v1_5.new(key).sign(SHA384.new(msg)),
     u'RS512': lambda msg, key: PKCS1_v1_5.new(key).sign(SHA512.new(msg))})
    verify_methods.update({u'RS256': lambda msg, key, sig: PKCS1_v1_5.new(key).verify(SHA256.new(msg), sig),
     u'RS384': lambda msg, key, sig: PKCS1_v1_5.new(key).verify(SHA384.new(msg), sig),
     u'RS512': lambda msg, key, sig: PKCS1_v1_5.new(key).verify(SHA512.new(msg), sig)})

    def prepare_RS_key(key):
        if isinstance(key, RSA._RSAobj):
            return key
        if isinstance(key, basestring):
            if isinstance(key, unicode):
                key = key.encode(u'utf-8')
            key = RSA.importKey(key)
        else:
            raise TypeError(u'Expecting a PEM- or RSA-formatted key.')
        return key


    prepare_key_methods.update({u'RS256': prepare_RS_key,
     u'RS384': prepare_RS_key,
     u'RS512': prepare_RS_key})
except ImportError:
    pass

try:
    import ecdsa
    from Crypto.Hash import SHA256
    from Crypto.Hash import SHA384
    from Crypto.Hash import SHA512
    signing_methods.update({u'ES256': lambda msg, key: key.sign(msg, hashfunc=hashlib.sha256, sigencode=ecdsa.util.sigencode_der),
     u'ES384': lambda msg, key: key.sign(msg, hashfunc=hashlib.sha384, sigencode=ecdsa.util.sigencode_der),
     u'ES512': lambda msg, key: key.sign(msg, hashfunc=hashlib.sha512, sigencode=ecdsa.util.sigencode_der)})
    verify_methods.update({u'ES256': lambda msg, key, sig: key.verify(sig, msg, hashfunc=hashlib.sha256, sigdecode=ecdsa.util.sigdecode_der),
     u'ES384': lambda msg, key, sig: key.verify(sig, msg, hashfunc=hashlib.sha384, sigdecode=ecdsa.util.sigdecode_der),
     u'ES512': lambda msg, key, sig: key.verify(sig, msg, hashfunc=hashlib.sha512, sigdecode=ecdsa.util.sigdecode_der)})

    def prepare_ES_key(key):
        if isinstance(key, ecdsa.SigningKey) or isinstance(key, ecdsa.VerifyingKey):
            return key
        if isinstance(key, basestring):
            if isinstance(key, unicode):
                key = key.encode(u'utf-8')
            try:
                key = ecdsa.VerifyingKey.from_pem(key)
            except ecdsa.der.UnexpectedDER:
                try:
                    key = ecdsa.SigningKey.from_pem(key)
                except:
                    raise

        else:
            raise TypeError(u'Expecting a PEM-formatted key.')
        return key


    prepare_key_methods.update({u'ES256': prepare_ES_key,
     u'ES384': prepare_ES_key,
     u'ES512': prepare_ES_key})
except ImportError:
    pass

def constant_time_compare(val1, val2):
    u"""
    Returns True if the two strings are equal, False otherwise.
    
    The time taken is independent of the number of characters that match.
    """
    if len(val1) != len(val2):
        return False
    result = 0
    if sys.version_info >= (3, 0, 0):
        for x, y in zip(val1, val2):
            result |= x ^ y

    else:
        for x, y in zip(val1, val2):
            result |= ord(x) ^ ord(y)

    return result == 0


def base64url_decode(input):
    rem = len(input) % 4
    if rem > 0:
        input += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input)


def base64url_encode(input):
    return base64.urlsafe_b64encode(input).replace('=', '')


def header(jwt):
    header_segment = jwt.split('.', 1)[0]
    try:
        header_data = base64url_decode(header_segment).decode(u'utf-8')
        return json.loads(header_data)
    except (ValueError, TypeError):
        raise DecodeError(u'Invalid header encoding')


def encode(payload, key, algorithm = u'HS256', headers = None):
    segments = []
    if algorithm is None:
        algorithm = u'none'
    if not isinstance(payload, Mapping):
        raise TypeError(u'Expecting a mapping object, as json web token onlysupport json objects.')
    header = {u'typ': u'JWT',
     u'alg': algorithm}
    if headers:
        header.update(headers)
    json_header = json.dumps(header, separators=(u',', u':')).encode(u'utf-8')
    segments.append(base64url_encode(json_header))
    for time_claim in [u'exp', u'iat', u'nbf']:
        if isinstance(payload.get(time_claim), datetime):
            payload[time_claim] = timegm(payload[time_claim].utctimetuple())

    json_payload = json.dumps(payload, separators=(u',', u':')).encode(u'utf-8')
    segments.append(base64url_encode(json_payload))
    signing_input = '.'.join(segments)
    try:
        key = prepare_key_methods[algorithm](key)
        signature = signing_methods[algorithm](signing_input, key)
    except KeyError:
        raise NotImplementedError(u'Algorithm not supported')

    segments.append(base64url_encode(signature))
    return '.'.join(segments)


def decode(jwt, key = u'', verify = True, **kwargs):
    payload, signing_input, header, signature = load(jwt)
    if verify:
        verify_expiration = kwargs.pop(u'verify_expiration', True)
        leeway = kwargs.pop(u'leeway', 0)
        verify_signature(payload, signing_input, header, signature, key, verify_expiration, leeway, **kwargs)
    return payload


def load(jwt):
    if isinstance(jwt, unicode):
        jwt = jwt.encode(u'utf-8')
    try:
        signing_input, crypto_segment = jwt.rsplit('.', 1)
        header_segment, payload_segment = signing_input.split('.', 1)
    except ValueError:
        raise DecodeError(u'Not enough segments')

    try:
        header_data = base64url_decode(header_segment)
    except (TypeError, binascii.Error):
        raise DecodeError(u'Invalid header padding')

    try:
        header = json.loads(header_data.decode(u'utf-8'))
    except ValueError as e:
        raise DecodeError(u'Invalid header string: %s' % e)

    try:
        payload_data = base64url_decode(payload_segment)
    except (TypeError, binascii.Error):
        raise DecodeError(u'Invalid payload padding')

    try:
        payload = json.loads(payload_data.decode(u'utf-8'))
    except ValueError as e:
        raise DecodeError(u'Invalid payload string: %s' % e)

    try:
        signature = base64url_decode(crypto_segment)
    except (TypeError, binascii.Error):
        raise DecodeError(u'Invalid crypto padding')

    return (payload,
     signing_input,
     header,
     signature)


def verify_signature(payload, signing_input, header, signature, key = u'', verify_expiration = True, leeway = 0, **kwargs):
    try:
        algorithm = header[u'alg'].upper()
        key = prepare_key_methods[algorithm](key)
        if algorithm.startswith(u'HS'):
            expected = verify_methods[algorithm](signing_input, key)
            if not constant_time_compare(signature, expected):
                raise DecodeError(u'Signature verification failed')
        elif not verify_methods[algorithm](signing_input, key, signature):
            raise DecodeError(u'Signature verification failed')
    except KeyError:
        raise DecodeError(u'Algorithm not supported')

    if u'nbf' in payload and verify_expiration:
        utc_timestamp = timegm(datetime.utcnow().utctimetuple())
        if payload[u'nbf'] > utc_timestamp + leeway:
            raise ExpiredSignature(u'Signature not yet valid')
    if u'exp' in payload and verify_expiration:
        utc_timestamp = timegm(datetime.utcnow().utctimetuple())
        if payload[u'exp'] < utc_timestamp - leeway:
            raise ExpiredSignature(u'Signature has expired')
    audience = kwargs.get(u'audience')
    if audience:
        if isinstance(audience, list):
            audiences = audience
        else:
            audiences = [audience]
        if payload.get(u'aud') not in audiences:
            raise InvalidAudience(u'Invalid audience')
    issuer = kwargs.get(u'issuer')
    if issuer:
        if payload.get(u'iss') != issuer:
            raise InvalidIssuer(u'Invalid issuer')
