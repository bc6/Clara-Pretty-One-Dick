#Embedded file name: cherrypy/wsgiserver\ssl_builtin.py
"""A library for integrating Python's builtin ``ssl`` library with CherryPy.

The ssl module must be importable for SSL functionality.

To use this module, set ``CherryPyWSGIServer.ssl_adapter`` to an instance of
``BuiltinSSLAdapter``.
"""
try:
    import ssl
except ImportError:
    ssl = None

from cherrypy import wsgiserver

class BuiltinSSLAdapter(wsgiserver.SSLAdapter):
    """A wrapper for integrating Python's builtin ssl module with CherryPy."""
    certificate = None
    private_key = None

    def __init__(self, certificate, private_key, certificate_chain = None):
        if ssl is None:
            raise ImportError('You must install the ssl module to use HTTPS.')
        self.certificate = certificate
        self.private_key = private_key
        self.certificate_chain = certificate_chain

    def bind(self, sock):
        """Wrap and return the given socket."""
        return sock

    def wrap(self, sock):
        """Wrap and return the given socket, plus WSGI environ entries."""
        try:
            s = ssl.wrap_socket(sock, do_handshake_on_connect=True, server_side=True, certfile=self.certificate, keyfile=self.private_key, ssl_version=ssl.PROTOCOL_SSLv23)
        except ssl.SSLError as e:
            if e.errno == ssl.SSL_ERROR_EOF:
                return (None, {})
            if e.errno == ssl.SSL_ERROR_SSL:
                if e.args[1].endswith('http request'):
                    raise wsgiserver.NoSSLError
            raise

        return (s, self.get_environ(s))

    def get_environ(self, sock):
        """Create WSGI environ entries to be merged into each request."""
        cipher = sock.cipher()
        ssl_environ = {'wsgi.url_scheme': 'https',
         'HTTPS': 'on',
         'SSL_PROTOCOL': cipher[1],
         'SSL_CIPHER': cipher[0]}
        return ssl_environ

    def makefile(self, sock, mode = 'r', bufsize = -1):
        return wsgiserver.CP_fileobject(sock, mode, bufsize)
