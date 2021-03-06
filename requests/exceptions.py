#Embedded file name: requests\exceptions.py
"""
requests.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of Requests' exceptions.

"""
from .packages.urllib3.exceptions import HTTPError as BaseHTTPError

class RequestException(IOError):
    """There was an ambiguous exception that occurred while handling your
    request."""
    pass


class HTTPError(RequestException):
    """An HTTP error occurred."""

    def __init__(self, *args, **kwargs):
        """ Initializes HTTPError with optional `response` object. """
        self.response = kwargs.pop('response', None)
        super(HTTPError, self).__init__(*args, **kwargs)


class ConnectionError(RequestException):
    """A Connection error occurred."""
    pass


class ProxyError(ConnectionError):
    """A proxy error occurred."""
    pass


class SSLError(ConnectionError):
    """An SSL error occurred."""
    pass


class Timeout(RequestException):
    """The request timed out."""
    pass


class URLRequired(RequestException):
    """A valid URL is required to make a request."""
    pass


class TooManyRedirects(RequestException):
    """Too many redirects."""
    pass


class MissingSchema(RequestException, ValueError):
    """The URL schema (e.g. http or https) is missing."""
    pass


class InvalidSchema(RequestException, ValueError):
    """See defaults.py for valid schemas."""
    pass


class InvalidURL(RequestException, ValueError):
    """ The URL provided was somehow invalid. """
    pass


class ChunkedEncodingError(RequestException):
    """The server declared chunked encoding but sent an invalid chunk."""
    pass


class ContentDecodingError(RequestException, BaseHTTPError):
    """Failed to decode response content"""
    pass
