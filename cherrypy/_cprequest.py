#Embedded file name: cherrypy\_cprequest.py
import os
import sys
import time
import warnings
import cherrypy
from cherrypy._cpcompat import basestring, copykeys, ntob, unicodestr
from cherrypy._cpcompat import SimpleCookie, CookieError
from cherrypy import _cpreqbody, _cpconfig
from cherrypy._cperror import format_exc, bare_error
from cherrypy.lib import httputil, file_generator

class Hook(object):
    """A callback and its metadata: failsafe, priority, and kwargs."""
    callback = None
    failsafe = False
    priority = 50
    kwargs = {}

    def __init__(self, callback, failsafe = None, priority = None, **kwargs):
        self.callback = callback
        if failsafe is None:
            failsafe = getattr(callback, 'failsafe', False)
        self.failsafe = failsafe
        if priority is None:
            priority = getattr(callback, 'priority', 50)
        self.priority = priority
        self.kwargs = kwargs

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    def __call__(self):
        """Run self.callback(**self.kwargs)."""
        return self.callback(**self.kwargs)

    def __repr__(self):
        cls = self.__class__
        return '%s.%s(callback=%r, failsafe=%r, priority=%r, %s)' % (cls.__module__,
         cls.__name__,
         self.callback,
         self.failsafe,
         self.priority,
         ', '.join([ '%s=%r' % (k, v) for k, v in self.kwargs.items() ]))


class HookMap(dict):
    """A map of call points to lists of callbacks (Hook objects)."""

    def __new__(cls, points = None):
        d = dict.__new__(cls)
        for p in points or []:
            d[p] = []

        return d

    def __init__(self, *a, **kw):
        pass

    def attach(self, point, callback, failsafe = None, priority = None, **kwargs):
        """Append a new Hook made from the supplied arguments."""
        self[point].append(Hook(callback, failsafe, priority, **kwargs))

    def run(self, point):
        """Execute all registered Hooks (callbacks) for the given point."""
        exc = None
        hooks = self[point]
        hooks.sort()
        for hook in hooks:
            if exc is None or hook.failsafe:
                try:
                    hook()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except (cherrypy.HTTPError, cherrypy.HTTPRedirect, cherrypy.InternalRedirect):
                    exc = sys.exc_info()[1]
                except:
                    exc = sys.exc_info()[1]
                    cherrypy.log(traceback=True, severity=40)

        if exc:
            raise

    def __copy__(self):
        newmap = self.__class__()
        for k, v in self.items():
            newmap[k] = v[:]

        return newmap

    copy = __copy__

    def __repr__(self):
        cls = self.__class__
        return '%s.%s(points=%r)' % (cls.__module__, cls.__name__, copykeys(self))


def hooks_namespace(k, v):
    """Attach bare hooks declared in config."""
    hookpoint = k.split('.', 1)[0]
    if isinstance(v, basestring):
        v = cherrypy.lib.attributes(v)
    if not isinstance(v, Hook):
        v = Hook(v)
    cherrypy.serving.request.hooks[hookpoint].append(v)


def request_namespace(k, v):
    """Attach request attributes declared in config."""
    if k[:5] == 'body.':
        setattr(cherrypy.serving.request.body, k[5:], v)
    else:
        setattr(cherrypy.serving.request, k, v)


def response_namespace(k, v):
    """Attach response attributes declared in config."""
    if k[:8] == 'headers.':
        cherrypy.serving.response.headers[k.split('.', 1)[1]] = v
    else:
        setattr(cherrypy.serving.response, k, v)


def error_page_namespace(k, v):
    """Attach error pages declared in config."""
    if k != 'default':
        k = int(k)
    cherrypy.serving.request.error_page[k] = v


hookpoints = ['on_start_resource',
 'before_request_body',
 'before_handler',
 'before_finalize',
 'on_end_resource',
 'on_end_request',
 'before_error_response',
 'after_error_response']

class Request(object):
    """An HTTP request.
    
    This object represents the metadata of an HTTP request message;
    that is, it contains attributes which describe the environment
    in which the request URL, headers, and body were sent (if you
    want tools to interpret the headers and body, those are elsewhere,
    mostly in Tools). This 'metadata' consists of socket data,
    transport characteristics, and the Request-Line. This object
    also contains data regarding the configuration in effect for
    the given URL, and the execution plan for generating a response.
    """
    prev = None
    local = httputil.Host('127.0.0.1', 80)
    remote = httputil.Host('127.0.0.1', 1111)
    scheme = 'http'
    server_protocol = 'HTTP/1.1'
    base = ''
    request_line = ''
    method = 'GET'
    query_string = ''
    query_string_encoding = 'utf8'
    protocol = (1, 1)
    params = {}
    header_list = []
    headers = httputil.HeaderMap()
    cookie = SimpleCookie()
    rfile = None
    process_request_body = True
    methods_with_bodies = ('POST', 'PUT')
    body = None
    dispatch = cherrypy.dispatch.Dispatcher()
    script_name = ''
    path_info = '/'
    login = None
    app = None
    handler = None
    toolmaps = {}
    config = None
    is_index = None
    hooks = HookMap(hookpoints)
    error_response = cherrypy.HTTPError(500).set_response
    error_page = {}
    show_tracebacks = True
    show_mismatched_params = True
    throws = (KeyboardInterrupt, SystemExit, cherrypy.InternalRedirect)
    throw_errors = False
    closed = False
    stage = None
    namespaces = _cpconfig.NamespaceSet(**{'hooks': hooks_namespace,
     'request': request_namespace,
     'response': response_namespace,
     'error_page': error_page_namespace,
     'tools': cherrypy.tools})

    def __init__(self, local_host, remote_host, scheme = 'http', server_protocol = 'HTTP/1.1'):
        """Populate a new Request object.
        
        local_host should be an httputil.Host object with the server info.
        remote_host should be an httputil.Host object with the client info.
        scheme should be a string, either "http" or "https".
        """
        self.local = local_host
        self.remote = remote_host
        self.scheme = scheme
        self.server_protocol = server_protocol
        self.closed = False
        self.error_page = self.error_page.copy()
        self.namespaces = self.namespaces.copy()
        self.stage = None

    def close(self):
        """Run cleanup code. (Core)"""
        if not self.closed:
            self.closed = True
            self.stage = 'on_end_request'
            self.hooks.run('on_end_request')
            self.stage = 'close'

    def run(self, method, path, query_string, req_protocol, headers, rfile):
        """Process the Request. (Core)
        
        method, path, query_string, and req_protocol should be pulled directly
        from the Request-Line (e.g. "GET /path?key=val HTTP/1.0").
        
        path
            This should be %XX-unquoted, but query_string should not be.
            They both MUST be byte strings, not unicode strings.
        
        headers
            A list of (name, value) tuples.
        
        rfile
            A file-like object containing the HTTP request entity.
        
        When run() is done, the returned object should have 3 attributes:
        
          * status, e.g. "200 OK"
          * header_list, a list of (name, value) tuples
          * body, an iterable yielding strings
        
        Consumer code (HTTP servers) should then access these response
        attributes to build the outbound stream.
        
        """
        response = cherrypy.serving.response
        self.stage = 'run'
        try:
            self.error_response = cherrypy.HTTPError(500).set_response
            self.method = method
            path = path or '/'
            self.query_string = query_string or ''
            self.params = {}
            rp = (int(req_protocol[5]), int(req_protocol[7]))
            sp = (int(self.server_protocol[5]), int(self.server_protocol[7]))
            self.protocol = min(rp, sp)
            response.headers.protocol = self.protocol
            url = path
            if query_string:
                url += '?' + query_string
            self.request_line = '%s %s %s' % (method, url, req_protocol)
            self.header_list = list(headers)
            self.headers = httputil.HeaderMap()
            self.rfile = rfile
            self.body = None
            self.cookie = SimpleCookie()
            self.handler = None
            self.script_name = self.app.script_name
            self.path_info = pi = path[len(self.script_name):]
            self.stage = 'respond'
            self.respond(pi)
        except self.throws:
            raise
        except:
            if self.throw_errors:
                raise
            else:
                cherrypy.log(traceback=True, severity=40)
                if self.show_tracebacks:
                    body = format_exc()
                else:
                    body = ''
                r = bare_error(body)
                response.output_status, response.header_list, response.body = r

        if self.method == 'HEAD':
            response.body = []
        try:
            cherrypy.log.access()
        except:
            cherrypy.log.error(traceback=True)

        if response.timed_out:
            raise cherrypy.TimeoutError()
        return response

    def respond(self, path_info):
        """Generate a response for the resource at self.path_info. (Core)"""
        response = cherrypy.serving.response
        try:
            try:
                if self.app is None:
                    raise cherrypy.NotFound()
                self.stage = 'process_headers'
                self.process_headers()
                self.hooks = self.__class__.hooks.copy()
                self.toolmaps = {}
                self.stage = 'get_resource'
                self.get_resource(path_info)
                self.body = _cpreqbody.RequestBody(self.rfile, self.headers, request_params=self.params)
                self.namespaces(self.config)
                self.stage = 'on_start_resource'
                self.hooks.run('on_start_resource')
                self.stage = 'process_query_string'
                self.process_query_string()
                if self.process_request_body:
                    if self.method not in self.methods_with_bodies:
                        self.process_request_body = False
                self.stage = 'before_request_body'
                self.hooks.run('before_request_body')
                if self.process_request_body:
                    self.body.process()
                self.stage = 'before_handler'
                self.hooks.run('before_handler')
                if self.handler:
                    self.stage = 'handler'
                    response.body = self.handler()
                self.stage = 'before_finalize'
                self.hooks.run('before_finalize')
                response.finalize()
            except (cherrypy.HTTPRedirect, cherrypy.HTTPError):
                inst = sys.exc_info()[1]
                inst.set_response()
                self.stage = 'before_finalize (HTTPError)'
                self.hooks.run('before_finalize')
                response.finalize()
            finally:
                self.stage = 'on_end_resource'
                self.hooks.run('on_end_resource')

        except self.throws:
            raise
        except:
            if self.throw_errors:
                raise
            self.handle_error()

    def process_query_string(self):
        """Parse the query string into Python structures. (Core)"""
        try:
            p = httputil.parse_query_string(self.query_string, encoding=self.query_string_encoding)
        except UnicodeDecodeError:
            raise cherrypy.HTTPError(404, 'The given query string could not be processed. Query strings for this resource must be encoded with %r.' % self.query_string_encoding)

        for key, value in p.items():
            if isinstance(key, unicode):
                del p[key]
                p[key.encode(self.query_string_encoding)] = value

        self.params.update(p)

    def process_headers(self):
        """Parse HTTP header data into Python structures. (Core)"""
        headers = self.headers
        for name, value in self.header_list:
            name = name.title()
            value = value.strip()
            if '=?' in value:
                dict.__setitem__(headers, name, httputil.decode_TEXT(value))
            else:
                dict.__setitem__(headers, name, value)
            if name == 'Cookie':
                try:
                    self.cookie.load(value)
                except CookieError:
                    msg = 'Illegal cookie name %s' % value.split('=')[0]
                    raise cherrypy.HTTPError(400, msg)

        if not dict.__contains__(headers, 'Host'):
            if self.protocol >= (1, 1):
                msg = "HTTP/1.1 requires a 'Host' request header."
                raise cherrypy.HTTPError(400, msg)
        host = dict.get(headers, 'Host')
        if not host:
            host = self.local.name or self.local.ip
        self.base = '%s://%s' % (self.scheme, host)

    def get_resource(self, path):
        """Call a dispatcher (which sets self.handler and .config). (Core)"""
        dispatch = self.app.find_config(path, 'request.dispatch', self.dispatch)
        dispatch(path)

    def handle_error(self):
        """Handle the last unanticipated exception. (Core)"""
        try:
            self.hooks.run('before_error_response')
            if self.error_response:
                self.error_response()
            self.hooks.run('after_error_response')
            cherrypy.serving.response.finalize()
        except cherrypy.HTTPRedirect:
            inst = sys.exc_info()[1]
            inst.set_response()
            cherrypy.serving.response.finalize()

    def _get_body_params(self):
        warnings.warn('body_params is deprecated in CherryPy 3.2, will be removed in CherryPy 3.3.', DeprecationWarning)
        return self.body.params

    body_params = property(_get_body_params, doc='\n    If the request Content-Type is \'application/x-www-form-urlencoded\' or\n    multipart, this will be a dict of the params pulled from the entity\n    body; that is, it will be the portion of request.params that come\n    from the message body (sometimes called "POST params", although they\n    can be sent with various HTTP method verbs). This value is set between\n    the \'before_request_body\' and \'before_handler\' hooks (assuming that\n    process_request_body is True).\n    \n    Deprecated in 3.2, will be removed for 3.3 in favor of\n    :attr:`request.body.params<cherrypy._cprequest.RequestBody.params>`.')


class ResponseBody(object):
    """The body of the HTTP response (the response entity)."""

    def __get__(self, obj, objclass = None):
        if obj is None:
            return self
        else:
            return obj._body

    def __set__(self, obj, value):
        if isinstance(value, basestring):
            if value:
                value = [value]
            else:
                value = []
        elif hasattr(value, 'read'):
            value = file_generator(value)
        elif value is None:
            value = []
        obj._body = value


class Response(object):
    """An HTTP Response, including status, headers, and body."""
    status = ''
    header_list = []
    headers = httputil.HeaderMap()
    cookie = SimpleCookie()
    body = ResponseBody()
    time = None
    timeout = 300
    timed_out = False
    stream = False

    def __init__(self):
        self.status = None
        self.header_list = None
        self._body = []
        self.time = time.time()
        self.headers = httputil.HeaderMap()
        dict.update(self.headers, {'Content-Type': 'text/html',
         'Server': 'CherryPy/' + cherrypy.__version__,
         'Date': httputil.HTTPDate(self.time)})
        self.cookie = SimpleCookie()

    def collapse_body(self):
        """Collapse self.body to a single string; replace it and return it."""
        if isinstance(self.body, basestring):
            return self.body
        newbody = ''.join([ chunk for chunk in self.body ])
        self.body = newbody
        return newbody

    def finalize(self):
        """Transform headers (and cookies) into self.header_list. (Core)"""
        try:
            code, reason, _ = httputil.valid_status(self.status)
        except ValueError:
            raise cherrypy.HTTPError(500, sys.exc_info()[1].args[0])

        headers = self.headers
        self.output_status = ntob(str(code), 'ascii') + ntob(' ') + headers.encode(reason)
        if self.stream:
            if dict.get(headers, 'Content-Length') is None:
                dict.pop(headers, 'Content-Length', None)
        elif code < 200 or code in (204, 205, 304):
            dict.pop(headers, 'Content-Length', None)
            self.body = ntob('')
        elif dict.get(headers, 'Content-Length') is None:
            content = self.collapse_body()
            dict.__setitem__(headers, 'Content-Length', len(content))
        self.header_list = h = headers.output()
        cookie = self.cookie.output()
        if cookie:
            for line in cookie.split('\n'):
                if line.endswith('\r'):
                    line = line[:-1]
                name, value = line.split(': ', 1)
                if isinstance(name, unicodestr):
                    name = name.encode('ISO-8859-1')
                if isinstance(value, unicodestr):
                    value = headers.encode(value)
                h.append((name, value))

    def check_timeout(self):
        """If now > self.time + self.timeout, set self.timed_out.
        
        This purposefully sets a flag, rather than raising an error,
        so that a monitor thread can interrupt the Response thread.
        """
        if time.time() > self.time + self.timeout:
            self.timed_out = True
