#Embedded file name: requests\compat.py
"""
pythoncompat
"""
from .packages import chardet
import sys
_ver = sys.version_info
is_py2 = _ver[0] == 2
is_py3 = _ver[0] == 3
is_py30 = is_py3 and _ver[1] == 0
is_py31 = is_py3 and _ver[1] == 1
is_py32 = is_py3 and _ver[1] == 2
is_py33 = is_py3 and _ver[1] == 3
is_py34 = is_py3 and _ver[1] == 4
is_py27 = is_py2 and _ver[1] == 7
is_py26 = is_py2 and _ver[1] == 6
is_py25 = is_py2 and _ver[1] == 5
is_py24 = is_py2 and _ver[1] == 4
_ver = sys.version.lower()
is_pypy = 'pypy' in _ver
is_jython = 'jython' in _ver
is_ironpython = 'iron' in _ver
is_cpython = not any((is_pypy, is_jython, is_ironpython))
is_windows = 'win32' in str(sys.platform).lower()
is_linux = 'linux' in str(sys.platform).lower()
is_osx = 'darwin' in str(sys.platform).lower()
is_hpux = 'hpux' in str(sys.platform).lower()
is_solaris = 'solar==' in str(sys.platform).lower()
try:
    import simplejson as json
except ImportError:
    import json

if is_py2:
    from urllib import quote, unquote, quote_plus, unquote_plus, urlencode, getproxies, proxy_bypass
    from urlparse import urlparse, urlunparse, urljoin, urlsplit, urldefrag
    from urllib2 import parse_http_list
    import cookielib
    from Cookie import Morsel
    from StringIO import StringIO
    from .packages.urllib3.packages.ordered_dict import OrderedDict
    from httplib import IncompleteRead
    builtin_str = str
    bytes = str
    str = unicode
    basestring = basestring
    numeric_types = (int, long, float)
elif is_py3:
    from urllib.parse import urlparse, urlunparse, urljoin, urlsplit, urlencode, quote, unquote, quote_plus, unquote_plus, urldefrag
    from urllib.request import parse_http_list, getproxies, proxy_bypass
    from http import cookiejar as cookielib
    from http.cookies import Morsel
    from io import StringIO
    from collections import OrderedDict
    from http.client import IncompleteRead
    builtin_str = str
    str = str
    bytes = bytes
    basestring = (str, bytes)
    numeric_types = (int, float)
