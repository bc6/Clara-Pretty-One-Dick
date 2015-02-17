#Embedded file name: requests/packages/urllib3\__init__.py
"""
urllib3 - Thread-safe connection pooling and re-using.
"""
__author__ = 'Andrey Petrov (andrey.petrov@shazow.net)'
__license__ = 'MIT'
__version__ = 'dev'
from .connectionpool import HTTPConnectionPool, HTTPSConnectionPool, connection_from_url
from . import exceptions
from .filepost import encode_multipart_formdata
from .poolmanager import PoolManager, ProxyManager, proxy_from_url
from .response import HTTPResponse
from .util import make_headers, get_host, Timeout
import logging
try:
    from logging import NullHandler
except ImportError:

    class NullHandler(logging.Handler):

        def emit(self, record):
            pass


logging.getLogger(__name__).addHandler(NullHandler())

def add_stderr_logger(level = logging.DEBUG):
    """
    Helper for quickly adding a StreamHandler to the logger. Useful for
    debugging.
    
    Returns the handler after adding it.
    """
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug('Added an stderr logging handler to logger: %s' % __name__)
    return handler


del NullHandler
