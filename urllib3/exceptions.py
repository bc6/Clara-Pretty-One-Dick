#Embedded file name: urllib3\exceptions.py


class HTTPError(Exception):
    """Base exception used by this module."""
    pass


class PoolError(HTTPError):
    """Base exception for errors caused within a pool."""

    def __init__(self, pool, message):
        self.pool = pool
        HTTPError.__init__(self, '%s: %s' % (pool, message))


class SSLError(HTTPError):
    """Raised when SSL certificate fails in an HTTPS connection."""
    pass


class MaxRetryError(PoolError):
    """Raised when the maximum number of retries is exceeded."""

    def __init__(self, pool, url):
        message = 'Max retries exceeded with url: %s' % url
        PoolError.__init__(self, pool, message)
        self.url = url


class HostChangedError(PoolError):
    """Raised when an existing pool gets a request for a foreign host."""

    def __init__(self, pool, url, retries = 3):
        message = 'Tried to open a foreign host with url: %s' % url
        PoolError.__init__(self, pool, message)
        self.url = url
        self.retries = retries


class TimeoutError(PoolError):
    """Raised when a socket timeout occurs."""
    pass


class EmptyPoolError(PoolError):
    """Raised when a pool runs out of connections and no more are allowed."""
    pass


class LocationParseError(ValueError, HTTPError):
    """Raised when get_host or similar fails to parse the URL input."""

    def __init__(self, location):
        message = 'Failed to parse: %s' % location
        super(LocationParseError, self).__init__(self, message)
        self.location = location
