#Embedded file name: requests/packages/urllib3/contrib\pyopenssl.py
"""SSL with SNI_-support for Python 2.

This needs the following packages installed:

* pyOpenSSL (tested with 0.13)
* ndg-httpsclient (tested with 0.3.2)
* pyasn1 (tested with 0.1.6)

To activate it call :func:`~urllib3.contrib.pyopenssl.inject_into_urllib3`.
This can be done in a ``sitecustomize`` module, or at any other time before
your application begins using ``urllib3``, like this::

    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

Now you can use :mod:`urllib3` as you normally would, and it will support SNI
when the required modules are installed.

Activating this module also has the positive side effect of disabling SSL/TLS
encryption in Python 2 (see `CRIME attack`_).

If you want to configure the default list of supported cipher suites, you can
set the ``urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST`` variable.

Module Variables
----------------

:var DEFAULT_SSL_CIPHER_LIST: The list of supported SSL/TLS cipher suites.
    Default: ``EECDH+ECDSA+AESGCM EECDH+aRSA+AESGCM EECDH+ECDSA+SHA256
    EECDH+aRSA+SHA256 EECDH+aRSA+RC4 EDH+aRSA EECDH RC4 !aNULL !eNULL !LOW !3DES
    !MD5 !EXP !PSK !SRP !DSS'``

.. _sni: https://en.wikipedia.org/wiki/Server_Name_Indication
.. _crime attack: https://en.wikipedia.org/wiki/CRIME_(security_exploit)

"""
from ndg.httpsclient.ssl_peer_verification import SUBJ_ALT_NAME_SUPPORT
from ndg.httpsclient.subj_alt_name import SubjectAltName as BaseSubjectAltName
import OpenSSL.SSL
from pyasn1.codec.der import decoder as der_decoder
from pyasn1.type import univ, constraint
from socket import _fileobject
import ssl
import select
from cStringIO import StringIO
from .. import connection
from .. import util
__all__ = ['inject_into_urllib3', 'extract_from_urllib3']
HAS_SNI = SUBJ_ALT_NAME_SUPPORT
_openssl_versions = {ssl.PROTOCOL_SSLv23: OpenSSL.SSL.SSLv23_METHOD,
 ssl.PROTOCOL_SSLv3: OpenSSL.SSL.SSLv3_METHOD,
 ssl.PROTOCOL_TLSv1: OpenSSL.SSL.TLSv1_METHOD}
_openssl_verify = {ssl.CERT_NONE: OpenSSL.SSL.VERIFY_NONE,
 ssl.CERT_OPTIONAL: OpenSSL.SSL.VERIFY_PEER,
 ssl.CERT_REQUIRED: OpenSSL.SSL.VERIFY_PEER + OpenSSL.SSL.VERIFY_FAIL_IF_NO_PEER_CERT}
DEFAULT_SSL_CIPHER_LIST = 'EECDH+ECDSA+AESGCM EECDH+aRSA+AESGCM ' + 'EECDH+ECDSA+SHA256 EECDH+aRSA+SHA256 EECDH+aRSA+RC4 EDH+aRSA ' + 'EECDH RC4 !aNULL !eNULL !LOW !3DES !MD5 !EXP !PSK !SRP !DSS'
orig_util_HAS_SNI = util.HAS_SNI
orig_connection_ssl_wrap_socket = connection.ssl_wrap_socket

def inject_into_urllib3():
    """Monkey-patch urllib3 with PyOpenSSL-backed SSL-support."""
    connection.ssl_wrap_socket = ssl_wrap_socket
    util.HAS_SNI = HAS_SNI


def extract_from_urllib3():
    """Undo monkey-patching by :func:`inject_into_urllib3`."""
    connection.ssl_wrap_socket = orig_connection_ssl_wrap_socket
    util.HAS_SNI = orig_util_HAS_SNI


class SubjectAltName(BaseSubjectAltName):
    """ASN.1 implementation for subjectAltNames support"""
    sizeSpec = univ.SequenceOf.sizeSpec + constraint.ValueSizeConstraint(1, 1024)


def get_subj_alt_name(peer_cert):
    dns_name = []
    if not SUBJ_ALT_NAME_SUPPORT:
        return dns_name
    general_names = SubjectAltName()
    for i in range(peer_cert.get_extension_count()):
        ext = peer_cert.get_extension(i)
        ext_name = ext.get_short_name()
        if ext_name != 'subjectAltName':
            continue
        ext_dat = ext.get_data()
        decoded_dat = der_decoder.decode(ext_dat, asn1Spec=general_names)
        for name in decoded_dat:
            if not isinstance(name, SubjectAltName):
                continue
            for entry in range(len(name)):
                component = name.getComponentByPosition(entry)
                if component.getName() != 'dNSName':
                    continue
                dns_name.append(str(component.getComponent()))

    return dns_name


class fileobject(_fileobject):

    def read(self, size = -1):
        rbufsize = max(self._rbufsize, self.default_bufsize)
        buf = self._rbuf
        buf.seek(0, 2)
        if size < 0:
            self._rbuf = StringIO()
            while True:
                try:
                    data = self._sock.recv(rbufsize)
                except OpenSSL.SSL.WantReadError:
                    continue

                if not data:
                    break
                buf.write(data)

            return buf.getvalue()
        else:
            buf_len = buf.tell()
            if buf_len >= size:
                buf.seek(0)
                rv = buf.read(size)
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return rv
            self._rbuf = StringIO()
            while True:
                left = size - buf_len
                try:
                    data = self._sock.recv(left)
                except OpenSSL.SSL.WantReadError:
                    continue

                if not data:
                    break
                n = len(data)
                if n == size and not buf_len:
                    return data
                if n == left:
                    buf.write(data)
                    del data
                    break
                buf.write(data)
                buf_len += n
                del data

            return buf.getvalue()

    def readline(self, size = -1):
        buf = self._rbuf
        buf.seek(0, 2)
        if buf.tell() > 0:
            buf.seek(0)
            bline = buf.readline(size)
            if bline.endswith('\n') or len(bline) == size:
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return bline
            del bline
        if size < 0:
            if self._rbufsize <= 1:
                buf.seek(0)
                buffers = [buf.read()]
                self._rbuf = StringIO()
                data = None
                recv = self._sock.recv
                while True:
                    try:
                        while data != '\n':
                            data = recv(1)
                            if not data:
                                break
                            buffers.append(data)

                    except OpenSSL.SSL.WantReadError:
                        continue

                    break

                return ''.join(buffers)
            buf.seek(0, 2)
            self._rbuf = StringIO()
            while True:
                try:
                    data = self._sock.recv(self._rbufsize)
                except OpenSSL.SSL.WantReadError:
                    continue

                if not data:
                    break
                nl = data.find('\n')
                if nl >= 0:
                    nl += 1
                    buf.write(data[:nl])
                    self._rbuf.write(data[nl:])
                    del data
                    break
                buf.write(data)

            return buf.getvalue()
        else:
            buf.seek(0, 2)
            buf_len = buf.tell()
            if buf_len >= size:
                buf.seek(0)
                rv = buf.read(size)
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return rv
            self._rbuf = StringIO()
            while True:
                try:
                    data = self._sock.recv(self._rbufsize)
                except OpenSSL.SSL.WantReadError:
                    continue

                if not data:
                    break
                left = size - buf_len
                nl = data.find('\n', 0, left)
                if nl >= 0:
                    nl += 1
                    self._rbuf.write(data[nl:])
                    if buf_len:
                        buf.write(data[:nl])
                        break
                    else:
                        return data[:nl]
                n = len(data)
                if n == size and not buf_len:
                    return data
                if n >= left:
                    buf.write(data[:left])
                    self._rbuf.write(data[left:])
                    break
                buf.write(data)
                buf_len += n

            return buf.getvalue()


class WrappedSocket(object):
    """API-compatibility wrapper for Python OpenSSL's Connection-class."""

    def __init__(self, connection, socket):
        self.connection = connection
        self.socket = socket

    def fileno(self):
        return self.socket.fileno()

    def makefile(self, mode, bufsize = -1):
        return fileobject(self.connection, mode, bufsize)

    def settimeout(self, timeout):
        return self.socket.settimeout(timeout)

    def sendall(self, data):
        return self.connection.sendall(data)

    def close(self):
        return self.connection.shutdown()

    def getpeercert(self, binary_form = False):
        x509 = self.connection.get_peer_certificate()
        if not x509:
            return x509
        if binary_form:
            return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509)
        return {'subject': ((('commonName', x509.get_subject().CN),),),
         'subjectAltName': [ ('DNS', value) for value in get_subj_alt_name(x509) ]}


def _verify_callback(cnx, x509, err_no, err_depth, return_code):
    return err_no == 0


def ssl_wrap_socket(sock, keyfile = None, certfile = None, cert_reqs = None, ca_certs = None, server_hostname = None, ssl_version = None):
    ctx = OpenSSL.SSL.Context(_openssl_versions[ssl_version])
    if certfile:
        ctx.use_certificate_file(certfile)
    if keyfile:
        ctx.use_privatekey_file(keyfile)
    if cert_reqs != ssl.CERT_NONE:
        ctx.set_verify(_openssl_verify[cert_reqs], _verify_callback)
    if ca_certs:
        try:
            ctx.load_verify_locations(ca_certs, None)
        except OpenSSL.SSL.Error as e:
            raise ssl.SSLError('bad ca_certs: %r' % ca_certs, e)

    OP_NO_COMPRESSION = 131072
    ctx.set_options(OP_NO_COMPRESSION)
    ctx.set_cipher_list(DEFAULT_SSL_CIPHER_LIST)
    cnx = OpenSSL.SSL.Connection(ctx, sock)
    cnx.set_tlsext_host_name(server_hostname)
    cnx.set_connect_state()
    while True:
        try:
            cnx.do_handshake()
        except OpenSSL.SSL.WantReadError:
            select.select([sock], [], [])
            continue
        except OpenSSL.SSL.Error as e:
            raise ssl.SSLError('bad handshake', e)

        break

    return WrappedSocket(cnx, sock)
