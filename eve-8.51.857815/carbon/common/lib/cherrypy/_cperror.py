#Embedded file name: carbon/common/lib/cherrypy\_cperror.py
"""Exception classes for CherryPy.

CherryPy provides (and uses) exceptions for declaring that the HTTP response
should be a status other than the default "200 OK". You can ``raise`` them like
normal Python exceptions. You can also call them and they will raise themselves;
this means you can set an :class:`HTTPError<cherrypy._cperror.HTTPError>`
or :class:`HTTPRedirect<cherrypy._cperror.HTTPRedirect>` as the
:attr:`request.handler<cherrypy._cprequest.Request.handler>`.

.. _redirectingpost:

Redirecting POST
================

When you GET a resource and are redirected by the server to another Location,
there's generally no problem since GET is both a "safe method" (there should
be no side-effects) and an "idempotent method" (multiple calls are no different
than a single call).

POST, however, is neither safe nor idempotent--if you
charge a credit card, you don't want to be charged twice by a redirect!

For this reason, *none* of the 3xx responses permit a user-agent (browser) to
resubmit a POST on redirection without first confirming the action with the user:

=====    =================================    ===========
300      Multiple Choices                     Confirm with the user
301      Moved Permanently                    Confirm with the user
302      Found (Object moved temporarily)     Confirm with the user
303      See Other                            GET the new URI--no confirmation
304      Not modified                         (for conditional GET only--POST should not raise this error)
305      Use Proxy                            Confirm with the user
307      Temporary Redirect                   Confirm with the user
=====    =================================    ===========

However, browsers have historically implemented these restrictions poorly;
in particular, many browsers do not force the user to confirm 301, 302
or 307 when redirecting POST. For this reason, CherryPy defaults to 303,
which most user-agents appear to have implemented correctly. Therefore, if
you raise HTTPRedirect for a POST request, the user-agent will most likely
attempt to GET the new URI (without asking for confirmation from the user).
We realize this is confusing for developers, but it's the safest thing we
could do. You are of course free to raise ``HTTPRedirect(uri, status=302)``
or any other 3xx status if you know what you're doing, but given the
environment, we couldn't let any of those be the default.

Custom Error Handling
=====================

.. image:: /refman/cperrors.gif

Anticipated HTTP responses
--------------------------

The 'error_page' config namespace can be used to provide custom HTML output for
expected responses (like 404 Not Found). Supply a filename from which the output
will be read. The contents will be interpolated with the values %(status)s,
%(message)s, %(traceback)s, and %(version)s using plain old Python
`string formatting <http://www.python.org/doc/2.6.4/library/stdtypes.html#string-formatting-operations>`_.

::

    _cp_config = {'error_page.404': os.path.join(localDir, "static/index.html")}


Beginning in version 3.1, you may also provide a function or other callable as
an error_page entry. It will be passed the same status, message, traceback and
version arguments that are interpolated into templates::

    def error_page_402(status, message, traceback, version):
        return "Error %s - Well, I'm very sorry but you haven't paid!" % status
    cherrypy.config.update({'error_page.402': error_page_402})

Also in 3.1, in addition to the numbered error codes, you may also supply
"error_page.default" to handle all codes which do not have their own error_page entry.



Unanticipated errors
--------------------

CherryPy also has a generic error handling mechanism: whenever an unanticipated
error occurs in your code, it will call
:func:`Request.error_response<cherrypy._cprequest.Request.error_response>` to set
the response status, headers, and body. By default, this is the same output as
:class:`HTTPError(500) <cherrypy._cperror.HTTPError>`. If you want to provide
some other behavior, you generally replace "request.error_response".

Here is some sample code that shows how to display a custom error message and
send an e-mail containing the error::

    from cherrypy import _cperror

    def handle_error():
        cherrypy.response.status = 500
        cherrypy.response.body = ["<html><body>Sorry, an error occured</body></html>"]
        sendMail('error@domain.com', 'Error in your web app', _cperror.format_exc())

    class Root:
        _cp_config = {'request.error_response': handle_error}


Note that you have to explicitly set :attr:`response.body <cherrypy._cprequest.Response.body>`
and not simply return an error message as a result.
"""
from cgi import escape as _escape
from sys import exc_info as _exc_info
from traceback import format_exception as _format_exception
from cherrypy._cpcompat import basestring, iteritems, urljoin as _urljoin
from cherrypy.lib import httputil as _httputil

class CherryPyException(Exception):
    """A base class for CherryPy exceptions."""
    pass


class TimeoutError(CherryPyException):
    """Exception raised when Response.timed_out is detected."""
    pass


class InternalRedirect(CherryPyException):
    """Exception raised to switch to the handler for a different URL.
    
    This exception will redirect processing to another path within the site
    (without informing the client). Provide the new path as an argument when
    raising the exception. Provide any params in the querystring for the new URL.
    """

    def __init__(self, path, query_string = ''):
        import cherrypy
        self.request = cherrypy.serving.request
        self.query_string = query_string
        if '?' in path:
            path, self.query_string = path.split('?', 1)
        path = _urljoin(self.request.path_info, path)
        self.path = path
        CherryPyException.__init__(self, path, self.query_string)


class HTTPRedirect(CherryPyException):
    """Exception raised when the request should be redirected.
    
    This exception will force a HTTP redirect to the URL or URL's you give it.
    The new URL must be passed as the first argument to the Exception,
    e.g., HTTPRedirect(newUrl). Multiple URLs are allowed in a list.
    If a URL is absolute, it will be used as-is. If it is relative, it is
    assumed to be relative to the current cherrypy.request.path_info.
    
    If one of the provided URL is a unicode object, it will be encoded
    using the default encoding or the one passed in parameter.
    
    There are multiple types of redirect, from which you can select via the
    ``status`` argument. If you do not provide a ``status`` arg, it defaults to
    303 (or 302 if responding with HTTP/1.0).
    
    Examples::
    
        raise cherrypy.HTTPRedirect("")
        raise cherrypy.HTTPRedirect("/abs/path", 307)
        raise cherrypy.HTTPRedirect(["path1", "path2?a=1&b=2"], 301)
    
    See :ref:`redirectingpost` for additional caveats.
    """
    status = None
    urls = None
    encoding = 'utf-8'

    def __init__(self, urls, status = None, encoding = None):
        import cherrypy
        request = cherrypy.serving.request
        if isinstance(urls, basestring):
            urls = [urls]
        abs_urls = []
        for url in urls:
            if isinstance(url, unicode):
                url = url.encode(encoding or self.encoding)
            url = _urljoin(cherrypy.url(), url)
            abs_urls.append(url)

        self.urls = abs_urls
        if status is None:
            if request.protocol >= (1, 1):
                status = 303
            else:
                status = 302
        else:
            status = int(status)
            if status < 300 or status > 399:
                raise ValueError('status must be between 300 and 399.')
        self.status = status
        CherryPyException.__init__(self, abs_urls, status)

    def set_response(self):
        """Modify cherrypy.response status, headers, and body to represent self.
        
        CherryPy uses this internally, but you can also use it to create an
        HTTPRedirect object and set its output without *raising* the exception.
        """
        import cherrypy
        response = cherrypy.serving.response
        response.status = status = self.status
        if status in (300, 301, 302, 303, 307):
            response.headers['Content-Type'] = 'text/html;charset=utf-8'
            response.headers['Location'] = self.urls[0]
            msg = {300: "This resource can be found at <a href='%s'>%s</a>.",
             301: "This resource has permanently moved to <a href='%s'>%s</a>.",
             302: "This resource resides temporarily at <a href='%s'>%s</a>.",
             303: "This resource can be found at <a href='%s'>%s</a>.",
             307: "This resource has moved temporarily to <a href='%s'>%s</a>."}[status]
            msgs = [ msg % (u, u) for u in self.urls ]
            response.body = '<br />\n'.join(msgs)
            response.headers.pop('Content-Length', None)
        elif status == 304:
            for key in ('Allow', 'Content-Encoding', 'Content-Language', 'Content-Length', 'Content-Location', 'Content-MD5', 'Content-Range', 'Content-Type', 'Expires', 'Last-Modified'):
                if key in response.headers:
                    del response.headers[key]

            response.body = None
            response.headers.pop('Content-Length', None)
        elif status == 305:
            response.headers['Location'] = self.urls[0]
            response.body = None
            response.headers.pop('Content-Length', None)
        else:
            raise ValueError('The %s status code is unknown.' % status)

    def __call__(self):
        """Use this exception as a request.handler (raise self)."""
        raise self


def clean_headers(status):
    """Remove any headers which should not apply to an error response."""
    import cherrypy
    response = cherrypy.serving.response
    respheaders = response.headers
    for key in ['Accept-Ranges',
     'Age',
     'ETag',
     'Location',
     'Retry-After',
     'Vary',
     'Content-Encoding',
     'Content-Length',
     'Expires',
     'Content-Location',
     'Content-MD5',
     'Last-Modified']:
        if key in respheaders:
            del respheaders[key]

    if status != 416:
        if 'Content-Range' in respheaders:
            del respheaders['Content-Range']


class HTTPError(CherryPyException):
    """Exception used to return an HTTP error code (4xx-5xx) to the client.
    
    This exception can be used to automatically send a response using a http status
    code, with an appropriate error page. It takes an optional
    ``status`` argument (which must be between 400 and 599); it defaults to 500
    ("Internal Server Error"). It also takes an optional ``message`` argument,
    which will be returned in the response body. See
    `RFC 2616 <http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4>`_
    for a complete list of available error codes and when to use them.
    
    Examples::
        
        raise cherrypy.HTTPError(403)
        raise cherrypy.HTTPError("403 Forbidden", "You are not allowed to access this resource.")
    """
    status = None
    code = None
    reason = None

    def __init__(self, status = 500, message = None):
        self.status = status
        try:
            self.code, self.reason, defaultmsg = _httputil.valid_status(status)
        except ValueError as x:
            raise self.__class__(500, x.args[0])

        if self.code < 400 or self.code > 599:
            raise ValueError('status must be between 400 and 599.')
        self._message = message or defaultmsg
        CherryPyException.__init__(self, status, message)

    def set_response(self):
        """Modify cherrypy.response status, headers, and body to represent self.
        
        CherryPy uses this internally, but you can also use it to create an
        HTTPError object and set its output without *raising* the exception.
        """
        import cherrypy
        response = cherrypy.serving.response
        clean_headers(self.code)
        response.status = self.status
        tb = None
        if cherrypy.serving.request.show_tracebacks:
            tb = format_exc()
        response.headers['Content-Type'] = 'text/html;charset=utf-8'
        response.headers.pop('Content-Length', None)
        content = self.get_error_page(self.status, traceback=tb, message=self._message)
        response.body = content
        _be_ie_unfriendly(self.code)

    def get_error_page(self, *args, **kwargs):
        return get_error_page(*args, **kwargs)

    def __call__(self):
        """Use this exception as a request.handler (raise self)."""
        raise self


class NotFound(HTTPError):
    """Exception raised when a URL could not be mapped to any handler (404).
    
    This is equivalent to raising
    :class:`HTTPError("404 Not Found") <cherrypy._cperror.HTTPError>`.
    """

    def __init__(self, path = None):
        if path is None:
            import cherrypy
            request = cherrypy.serving.request
            path = request.script_name + request.path_info
        self.args = (path,)
        HTTPError.__init__(self, 404, "The path '%s' was not found." % path)


_HTTPErrorTemplate = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html>\n<head>\n    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"></meta>\n    <title>%(status)s</title>\n    <style type="text/css">\n    #powered_by {\n        margin-top: 20px;\n        border-top: 2px solid black;\n        font-style: italic;\n    }\n\n    #traceback {\n        color: red;\n    }\n    </style>\n</head>\n    <body>\n        <h2>%(status)s</h2>\n        <p>%(message)s</p>\n        <pre id="traceback">%(traceback)s</pre>\n    <div id="powered_by">\n    <span>Powered by <a href="http://www.cherrypy.org">CherryPy %(version)s</a></span>\n    </div>\n    </body>\n</html>\n'

def get_error_page(status, **kwargs):
    """Return an HTML page, containing a pretty error response.
    
    status should be an int or a str.
    kwargs will be interpolated into the page template.
    """
    import cherrypy
    try:
        code, reason, message = _httputil.valid_status(status)
    except ValueError as x:
        raise cherrypy.HTTPError(500, x.args[0])

    if kwargs.get('status') is None:
        kwargs['status'] = '%s %s' % (code, reason)
    if kwargs.get('message') is None:
        kwargs['message'] = message
    if kwargs.get('traceback') is None:
        kwargs['traceback'] = ''
    if kwargs.get('version') is None:
        kwargs['version'] = cherrypy.__version__
    for k, v in iteritems(kwargs):
        if v is None:
            kwargs[k] = ''
        else:
            kwargs[k] = _escape(kwargs[k])

    pages = cherrypy.serving.request.error_page
    error_page = pages.get(code) or pages.get('default')
    if error_page:
        try:
            if hasattr(error_page, '__call__'):
                return error_page(**kwargs)
            return open(error_page, 'rb').read() % kwargs
        except:
            e = _format_exception(*_exc_info())[-1]
            m = kwargs['message']
            if m:
                m += '<br />'
            m += 'In addition, the custom error page failed:\n<br />%s' % e
            kwargs['message'] = m

    return _HTTPErrorTemplate % kwargs


_ie_friendly_error_sizes = {400: 512,
 403: 256,
 404: 512,
 405: 256,
 406: 512,
 408: 512,
 409: 512,
 410: 256,
 500: 512,
 501: 512,
 505: 512}

def _be_ie_unfriendly(status):
    import cherrypy
    response = cherrypy.serving.response
    s = _ie_friendly_error_sizes.get(status, 0)
    if s:
        s += 1
        content = response.collapse_body()
        l = len(content)
        if l and l < s:
            content = content + ' ' * (s - l)
        response.body = content
        response.headers['Content-Length'] = str(len(content))


def format_exc(exc = None):
    """Return exc (or sys.exc_info if None), formatted."""
    if exc is None:
        exc = _exc_info()
    if exc == (None, None, None):
        return ''
    import traceback
    return ''.join(traceback.format_exception(*exc))


def bare_error(extrabody = None):
    """Produce status, headers, body for a critical error.
    
    Returns a triple without calling any other questionable functions,
    so it should be as error-free as possible. Call it from an HTTP server
    if you get errors outside of the request.
    
    If extrabody is None, a friendly but rather unhelpful error message
    is set in the body. If extrabody is a string, it will be appended
    as-is to the body.
    """
    body = 'Unrecoverable error in the server.'
    if extrabody is not None:
        if not isinstance(extrabody, str):
            extrabody = extrabody.encode('utf-8')
        body += '\n' + extrabody
    return ('500 Internal Server Error', [('Content-Type', 'text/plain'), ('Content-Length', str(len(body)))], [body])
