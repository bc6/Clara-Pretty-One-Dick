#Embedded file name: scriber\httputils.py
"""
HTTP Utilities
"""
import datetime as pydt
import urllib
import urlparse
import pprint
import typeutils
import datetimeutils
from scriber import const
from scriber import log

class Url(object):

    def __init__(self, full_url):
        self.raw = full_url
        self.scheme = ''
        self.auth_user = ''
        self.auth_pass = ''
        self.host = ''
        self.port = 0
        self.path = ''
        self.query_string = ''
        self.fragment_id = ''
        self.path_list = []
        self.file = ''
        self.file_ext = ''
        self.file_path = ''
        self._parse()

    def _parse(self):
        """
        :param full_url:
        :type full_url: str
        """
        if self.raw:
            match = const.URL_MATCHER.match(self.raw)
            if match:
                d = match.groupdict()
                self.scheme = d.get('scheme', '')
                self.host = d.get('host', '')
                self.path = d.get('path', '')
                self.query_string = d.get('querystr', '')
                self.fragment_id = d.get('fragment', '')
                if self.host:
                    match = const.HOST_MATCHER.match(self.host)
                    if match:
                        d = match.groupdict()
                        self.auth_user = d.get('user', '')
                        self.auth_pass = d.get('pass', '')
                        self.host = d.get('host', '')
                        self.port = typeutils.int_eval(d.get('port', None), 80)
                if self.path:
                    self.path_list = self.path.split('/')
                    self.file_path = self.path_list[:-1]
                    self.file = self.path_list[-1]
                    if self.file:
                        self.file_ext = self.file.split('.')[-1]

    def __str__(self):
        return self.raw

    def __repr__(self):
        buff = []
        if self.scheme:
            buff.append('[schema=%s]' % self.scheme)
        buff.append('//')
        if self.auth_user:
            buff.append('[user=%s]' % self.auth_user)
            if self.auth_pass:
                buff.append(':[pass=***]' % self.auth_pass)
            buff.append('@')
        if self.host:
            buff.append('[host=%s]' % self.host)
        if self.port:
            buff.append(':[port=%s]' % self.port)
        buff.append('/')
        if self.path:
            buff.append('[path=%s]' % self.path)
        if self.query_string:
            buff.append('?[querystr=%s]' % self.query_string)
        if self.fragment_id:
            buff.append('#[fragment=%s]' % self.fragment_id)
        return ''.join(buff)

    def __dump__(self):
        print '<Url __dump__>'
        pprint.pprint(self.__dict__)
        print '</Url>'


class MethodParams(object):

    def __init__(self, data):
        self.raw = data
        self.data = {}
        self._parse_data()

    def _parse_data(self):
        self.data = self.raw

    def getitem(self, name):
        return self.str(name)

    def __getitem__(self, item):
        return self.getitem(item)

    def contains(self, name):
        return name in self.data

    def __contains__(self, item):
        return self.contains(item)

    def raw(self, name, default = ''):
        if self.contains(name):
            return self.data[name]
        return default

    def str(self, name, default = ''):
        if self.contains(name):
            return urllib.unquote(self.data[name])
        return default

    def int(self, name, default = 0):
        if self.contains(name):
            return typeutils.int_eval(self.data[name], default)
        return default

    def float(self, name, default = 0.0):
        if self.contains(name):
            return typeutils.float_eval(self.data[name])
        return default

    def bool(self, name, default = False):
        if self.contains(name):
            return typeutils.bool_eval(self.data[name])
        return default

    def datetime(self, name, default = pydt.datetime.now()):
        if self.contains(name) and self.data[name]:
            return datetimeutils.any_to_datetime(self.data[name], default)
        return default

    def date(self, name, default = pydt.datetime.now().date()):
        if self.contains(name) and self.data[name]:
            val = datetimeutils.any_to_datetime(self.data[name], default)
            if isinstance(val, pydt.datetime):
                return val.date()
        return default

    def time(self, name, default = pydt.datetime.now().time()):
        if self.contains(name) and self.data[name]:
            val = datetimeutils.any_to_datetime(self.data[name], default)
            if isinstance(val, pydt.datetime):
                return val.time()
        return default

    def is_list(self, name):
        if self.contains(name):
            if isinstance(self.data[name], (list, tuple)):
                return True
        return False

    def list(self, name, default = ()):
        if self.contains(name):
            if isinstance(self.data[name], (list, tuple)):
                return self.data[name]
            else:
                return [self.data[name]]
        return default

    def str_list(self, name, default = ()):
        if self.contains(name):
            if isinstance(self.data[name], (list, tuple)):
                return [ urllib.unquote(i) for i in self.data[name] ]
            else:
                return [urllib.unquote(self.data[name])]
        return default

    def int_list(self, name, default = (), item_default = 0):
        if self.contains(name):
            if isinstance(self.data[name], (list, tuple)):
                return [ typeutils.int_eval(i, item_default) for i in self.data[name] ]
            else:
                return [typeutils.int_eval(self.data[name], item_default)]
        return default

    def float_list(self, name, default = (), item_default = 0.0):
        if self.contains(name):
            if isinstance(self.data[name], (list, tuple)):
                return [ typeutils.float_eval(i, item_default) for i in self.data[name] ]
            else:
                return [typeutils.float_eval(self.data[name], item_default)]
        return default

    def bool_list(self, name, default = ()):
        if self.contains(name):
            if isinstance(self.data[name], (list, tuple)):
                return [ typeutils.bool_eval(i) for i in self.data[name] ]
            else:
                return [typeutils.bool_eval(self.data[name])]
        return default

    def __repr__(self):
        return '%r' % self.data

    def __len__(self):
        return len(self.data)

    def __nonzero__(self):
        return bool(self.data)

    def __dump__(self):
        classname = self.__class__.__name__
        print '<%s __dump__>' % classname
        pprint.pprint(self.__dict__)
        print '</%s>' % classname


class UnifiedParams(object):

    def __init__(self, get_data, post_data):
        self.get_data = get_data
        self.post_data = post_data

    def getitem(self, name):
        return self.str(name)

    def contains(self, name):
        if self.post_data.contains(name):
            return True
        if self.get_data.contains(name):
            return True
        return False

    def raw(self, name, default = ''):
        if self.post_data.contains(name):
            return self.post_data.raw(name)
        if self.get_data.contains(name):
            return self.get_data.raw(name)
        return default

    def str(self, name, default = ''):
        if self.post_data.contains(name):
            return self.post_data.str(name)
        if self.get_data.contains(name):
            return self.get_data.str(name)
        return default

    def int(self, name, default = 0):
        if self.post_data.contains(name):
            return self.post_data.int(name)
        if self.get_data.contains(name):
            return self.get_data.int(name)
        return default

    def float(self, name, default = 0.0):
        if self.post_data.contains(name):
            return self.post_data.float(name)
        if self.get_data.contains(name):
            return self.get_data.float(name)
        return default

    def bool(self, name, default = False):
        if self.post_data.contains(name):
            return self.post_data.bool(name)
        if self.get_data.contains(name):
            return self.get_data.bool(name)
        return default

    def datetime(self, name, default = pydt.datetime.now()):
        if self.post_data.contains(name):
            return self.post_data.datetime(name, default)
        if self.get_data.contains(name):
            return self.get_data.datetime(name, default)
        return default

    def date(self, name, default = pydt.datetime.now().date()):
        if self.post_data.contains(name):
            return self.post_data.date(name, default)
        if self.get_data.contains(name):
            return self.get_data.date(name, default)
        return default

    def time(self, name, default = pydt.datetime.now().time()):
        if self.post_data.contains(name):
            return self.post_data.time(name, default)
        if self.get_data.contains(name):
            return self.get_data.time(name, default)
        return default

    def is_list(self, name):
        if self.post_data.contains(name):
            if isinstance(self.post_data[name], (list, tuple)):
                return True
        if self.get_data.contains(name):
            if isinstance(self.get_data[name], (list, tuple)):
                return True
        return False

    def list(self, name, default = ()):
        if self.post_data.contains(name):
            return self.post_data.list(name)
        if self.get_data.contains(name):
            return self.get_data.list(name)
        return default

    def str_list(self, name, default = ()):
        if self.post_data.contains(name):
            return self.post_data.str_list(name)
        if self.get_data.contains(name):
            return self.get_data.str_list(name)
        return default

    def int_list(self, name, default = (), item_default = 0):
        if self.post_data.contains(name):
            return self.post_data.int_list(name, item_default=item_default)
        if self.get_data.contains(name):
            return self.get_data.int_list(name, item_default=item_default)
        return default

    def float_list(self, name, default = (), item_default = 0.0):
        if self.post_data.contains(name):
            return self.post_data.float_list(name, item_default=item_default)
        if self.get_data.contains(name):
            return self.get_data.float_list(name, item_default=item_default)
        return default

    def bool_list(self, name, default = ()):
        if self.post_data.contains(name):
            return self.post_data.bool_list(name)
        if self.get_data.contains(name):
            return self.get_data.bool_list(name)
        return default


class AbstractRequest(object):

    def __init__(self, request):
        self.original = request
        self.raw = ''
        self.post = MethodParams({})
        self.get = MethodParams({})
        self.cookies = MethodParams({})
        self.url = Url('')
        self.headers = {}
        self.body = ''
        self.method = ''
        self.client_ip = ''
        self._parse_data()
        self.p = UnifiedParams(self.get, self.post)

    def _parse_data(self):
        raise NotImplementedError('AbstractRequest is Abstract!')

    def __dump__(self):
        classname = self.__class__.__name__
        print '<%s __dump__>' % classname
        pprint.pprint(self.__dict__)
        print '</%s>' % classname


class MoonshineRequest(AbstractRequest):

    def _parse_data(self):
        self.raw = self.original.raw
        self.post = MethodParams(self.original.form)
        self.get = MethodParams(self.original.query)
        self.cookies = MethodParams(self.original.cookie)
        self.headers = dict(zip([ str(k).lower() for k in self.original.header.keys() ], self.original.header.values()))
        self.client_ip = self.original.ep.address
        self.method = self.original.method
        if ':' in self.client_ip:
            parts = self.client_ip.split(':')
            if parts and len(parts) > 0:
                self.client_ip = parts[0]
        if self.original.path.startswith('/'):
            path = self.original.path[1:]
        else:
            path = self.original.path
        self.url = Url('%s/%s' % (self.headers.get('host', ''), path))
        try:
            body = self.raw.replace('\r', '')
            self.body = body[body.index('\n\n') + 2:]
        except (ValueError, IndexError):
            self.body = ''


class DjangoRequest(AbstractRequest):

    def _parse_data(self):
        self.raw = str(self.original.body)
        self.method = self.original.method
        self.post = MethodParams(self.original.POST)
        self.get = MethodParams(self.original.GET)
        self.cookies = MethodParams(self.original.COOKIES)
        self.url = Url(self.original.get_full_path())
        self.client_ip = self.original.META['REMOTE_ADDR']
        self.body = self.original.body
        self.headers['content-length'] = self.original.META['CONTENT_LENGTH']
        self.headers['content-type'] = self.original.META['CONTENT_TYPE']
        for k, v in self.original.META.iteritems():
            if k.startswith('HTTP_'):
                self.headers[k[5:].lower().replace('_', '-')] = v


class CherryPyRequest(AbstractRequest):

    def _parse_data(self):
        self.raw = str(self.original.body)
        self.post = MethodParams(self.original.body.params)
        self.client_ip = self.original.remote.ip
        qs_params = urlparse.parse_qs(self.original.query_string, keep_blank_values=True)
        for k in qs_params.keys():
            if isinstance(qs_params[k], list):
                if len(qs_params[k]) < 1:
                    qs_params[k] = ''
                elif len(qs_params[k]) == 1:
                    qs_params[k] = qs_params[k][0]

        self.get = MethodParams(qs_params)
        self.cookies = dict([ (k, v) for k, v in self.original.cookie.iteritems() ])
        self.method = self.original.method
        self.headers = dict([ (k.lower(), v) for k, v in self.original.header_list ])
        self.url = Url('%s%s?%s' % (self.original.base, self.original.path_info, self.original.query_string))
        self.body = self.original.body


def parse_request(request):
    """Takes an unspecific http request object and wraps it with the
    appropriate implementation of AbstractRequest.
    
    Failing to find an appropriate AbstractRequest, the same object is
    returned, untouched.
    
    :param request: The request to parse
    :type request: object
    :return: A server-specific instance of AbstractRequest or the same object
             passed to begin with
    :rtype: AbstractRequest or object
    """
    if isinstance(request, AbstractRequest):
        return request
    request_class = getattr(request, '__class__', None)
    if request_class:
        class_name = str(request_class)
        if class_name.endswith('.net.httpService.Request'):
            return MoonshineRequest(request)
        if class_name.startswith('cherrypy.'):
            return CherryPyRequest(request)
        if class_name.startswith("<class 'django."):
            return DjangoRequest(request)
        log.error('Unknown class_name: %s=' % class_name)
    log.error('Unknown http request type: %s=%r' % (request_class, request))
    return request


def url_append_qs(url, **kwargs):
    if not kwargs:
        return url
    req_url = [url]
    if '?' in url:
        if url[-1] not in ('?', '&'):
            req_url.append('&')
    else:
        req_url.append('?')
    req_url.append(urllib.urlencode(kwargs))
    return ''.join(req_url)
