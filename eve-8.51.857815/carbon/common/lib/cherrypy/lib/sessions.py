#Embedded file name: carbon/common/lib/cherrypy/lib\sessions.py
"""Session implementation for CherryPy.

You need to edit your config file to use sessions. Here's an example::

    [/]
    tools.sessions.on = True
    tools.sessions.storage_type = "file"
    tools.sessions.storage_path = "/home/site/sessions"
    tools.sessions.timeout = 60

This sets the session to be stored in files in the directory /home/site/sessions,
and the session timeout to 60 minutes. If you omit ``storage_type`` the sessions
will be saved in RAM.  ``tools.sessions.on`` is the only required line for
working sessions, the rest are optional.

By default, the session ID is passed in a cookie, so the client's browser must
have cookies enabled for your site.

To set data for the current session, use
``cherrypy.session['fieldname'] = 'fieldvalue'``;
to get data use ``cherrypy.session.get('fieldname')``.

================
Locking sessions
================

By default, the ``'locking'`` mode of sessions is ``'implicit'``, which means
the session is locked early and unlocked late. If you want to control when the
session data is locked and unlocked, set ``tools.sessions.locking = 'explicit'``.
Then call ``cherrypy.session.acquire_lock()`` and ``cherrypy.session.release_lock()``.
Regardless of which mode you use, the session is guaranteed to be unlocked when
the request is complete.

=================
Expiring Sessions
=================

You can force a session to expire with :func:`cherrypy.lib.sessions.expire`.
Simply call that function at the point you want the session to expire, and it
will cause the session cookie to expire client-side.

===========================
Session Fixation Protection
===========================

If CherryPy receives, via a request cookie, a session id that it does not
recognize, it will reject that id and create a new one to return in the
response cookie. This `helps prevent session fixation attacks
<http://en.wikipedia.org/wiki/Session_fixation#Regenerate_SID_on_each_request>`_.
However, CherryPy "recognizes" a session id by looking up the saved session
data for that id. Therefore, if you never save any session data,
**you will get a new session id for every request**.

================
Sharing Sessions
================

If you run multiple instances of CherryPy (for example via mod_python behind
Apache prefork), you most likely cannot use the RAM session backend, since each
instance of CherryPy will have its own memory space. Use a different backend
instead, and verify that all instances are pointing at the same file or db
location. Alternately, you might try a load balancer which makes sessions
"sticky". Google is your friend, there.

================
Expiration Dates
================

The response cookie will possess an expiration date to inform the client at
which point to stop sending the cookie back in requests. If the server time
and client time differ, expect sessions to be unreliable. **Make sure the
system time of your server is accurate**.

CherryPy defaults to a 60-minute session timeout, which also applies to the
cookie which is sent to the client. Unfortunately, some versions of Safari
("4 public beta" on Windows XP at least) appear to have a bug in their parsing
of the GMT expiration date--they appear to interpret the date as one hour in
the past. Sixty minutes minus one hour is pretty close to zero, so you may
experience this bug as a new session id for every request, unless the requests
are less than one second apart. To fix, try increasing the session.timeout.

On the other extreme, some users report Firefox sending cookies after their
expiration date, although this was on a system with an inaccurate system time.
Maybe FF doesn't trust system time.
"""
import datetime
import os
import random
import time
import threading
import types
from warnings import warn
import cherrypy
from cherrypy._cpcompat import copyitems, pickle, random20
from cherrypy.lib import httputil
missing = object()

class Session(object):
    """A CherryPy dict-like Session object (one per request)."""
    _id = None
    id_observers = None

    def _get_id(self):
        return self._id

    def _set_id(self, value):
        self._id = value
        for o in self.id_observers:
            o(value)

    id = property(_get_id, _set_id, doc='The current session ID.')
    timeout = 60
    locked = False
    loaded = False
    clean_thread = None
    clean_freq = 5
    originalid = None
    missing = False
    regenerated = False
    debug = False

    def __init__(self, id = None, **kwargs):
        self.id_observers = []
        self._data = {}
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.originalid = id
        self.missing = False
        if id is None:
            if self.debug:
                cherrypy.log('No id given; making a new one', 'TOOLS.SESSIONS')
            self._regenerate()
        else:
            self.id = id
            if not self._exists():
                if self.debug:
                    cherrypy.log('Expired or malicious session %r; making a new one' % id, 'TOOLS.SESSIONS')
                self.id = None
                self.missing = True
                self._regenerate()

    def regenerate(self):
        """Replace the current session (with a new id)."""
        self.regenerated = True
        self._regenerate()

    def _regenerate(self):
        if self.id is not None:
            self.delete()
        old_session_was_locked = self.locked
        if old_session_was_locked:
            self.release_lock()
        self.id = None
        while self.id is None:
            self.id = self.generate_id()
            if self._exists():
                self.id = None

        if old_session_was_locked:
            self.acquire_lock()

    def clean_up(self):
        """Clean up expired sessions."""
        pass

    def generate_id(self):
        """Return a new session id."""
        return random20()

    def save(self):
        """Save session data."""
        try:
            if self.loaded:
                t = datetime.timedelta(seconds=self.timeout * 60)
                expiration_time = datetime.datetime.now() + t
                if self.debug:
                    cherrypy.log('Saving with expiry %s' % expiration_time, 'TOOLS.SESSIONS')
                self._save(expiration_time)
        finally:
            if self.locked:
                self.release_lock()

    def load(self):
        """Copy stored session data into this session instance."""
        data = self._load()
        if data is None or data[1] < datetime.datetime.now():
            if self.debug:
                cherrypy.log('Expired session, flushing data', 'TOOLS.SESSIONS')
            self._data = {}
        else:
            self._data = data[0]
        self.loaded = True
        cls = self.__class__
        if self.clean_freq and not cls.clean_thread:
            t = cherrypy.process.plugins.Monitor(cherrypy.engine, self.clean_up, self.clean_freq * 60, name='Session cleanup')
            t.subscribe()
            cls.clean_thread = t
            t.start()

    def delete(self):
        """Delete stored session data."""
        self._delete()

    def __getitem__(self, key):
        if not self.loaded:
            self.load()
        return self._data[key]

    def __setitem__(self, key, value):
        if not self.loaded:
            self.load()
        self._data[key] = value

    def __delitem__(self, key):
        if not self.loaded:
            self.load()
        del self._data[key]

    def pop(self, key, default = missing):
        """Remove the specified key and return the corresponding value.
        If key is not found, default is returned if given,
        otherwise KeyError is raised.
        """
        if not self.loaded:
            self.load()
        if default is missing:
            return self._data.pop(key)
        else:
            return self._data.pop(key, default)

    def __contains__(self, key):
        if not self.loaded:
            self.load()
        return key in self._data

    def has_key(self, key):
        """D.has_key(k) -> True if D has a key k, else False."""
        if not self.loaded:
            self.load()
        return key in self._data

    def get(self, key, default = None):
        """D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."""
        if not self.loaded:
            self.load()
        return self._data.get(key, default)

    def update(self, d):
        """D.update(E) -> None.  Update D from E: for k in E: D[k] = E[k]."""
        if not self.loaded:
            self.load()
        self._data.update(d)

    def setdefault(self, key, default = None):
        """D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D."""
        if not self.loaded:
            self.load()
        return self._data.setdefault(key, default)

    def clear(self):
        """D.clear() -> None.  Remove all items from D."""
        if not self.loaded:
            self.load()
        self._data.clear()

    def keys(self):
        """D.keys() -> list of D's keys."""
        if not self.loaded:
            self.load()
        return self._data.keys()

    def items(self):
        """D.items() -> list of D's (key, value) pairs, as 2-tuples."""
        if not self.loaded:
            self.load()
        return self._data.items()

    def values(self):
        """D.values() -> list of D's values."""
        if not self.loaded:
            self.load()
        return self._data.values()


class RamSession(Session):
    cache = {}
    locks = {}

    def clean_up(self):
        """Clean up expired sessions."""
        now = datetime.datetime.now()
        for id, (data, expiration_time) in copyitems(self.cache):
            if expiration_time <= now:
                try:
                    del self.cache[id]
                except KeyError:
                    pass

                try:
                    del self.locks[id]
                except KeyError:
                    pass

    def _exists(self):
        return self.id in self.cache

    def _load(self):
        return self.cache.get(self.id)

    def _save(self, expiration_time):
        self.cache[self.id] = (self._data, expiration_time)

    def _delete(self):
        self.cache.pop(self.id, None)

    def acquire_lock(self):
        """Acquire an exclusive lock on the currently-loaded session data."""
        self.locked = True
        self.locks.setdefault(self.id, threading.RLock()).acquire()

    def release_lock(self):
        """Release the lock on the currently-loaded session data."""
        self.locks[self.id].release()
        self.locked = False

    def __len__(self):
        """Return the number of active sessions."""
        return len(self.cache)


class FileSession(Session):
    """Implementation of the File backend for sessions
    
    storage_path
        The folder where session data will be saved. Each session
        will be saved as pickle.dump(data, expiration_time) in its own file;
        the filename will be self.SESSION_PREFIX + self.id.
    
    """
    SESSION_PREFIX = 'session-'
    LOCK_SUFFIX = '.lock'
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, id = None, **kwargs):
        kwargs['storage_path'] = os.path.abspath(kwargs['storage_path'])
        Session.__init__(self, id=id, **kwargs)

    def setup(cls, **kwargs):
        """Set up the storage system for file-based sessions.
        
        This should only be called once per process; this will be done
        automatically when using sessions.init (as the built-in Tool does).
        """
        kwargs['storage_path'] = os.path.abspath(kwargs['storage_path'])
        for k, v in kwargs.items():
            setattr(cls, k, v)

        lockfiles = [ fname for fname in os.listdir(cls.storage_path) if fname.startswith(cls.SESSION_PREFIX) and fname.endswith(cls.LOCK_SUFFIX) ]
        if lockfiles:
            plural = ('', 's')[len(lockfiles) > 1]
            warn('%s session lockfile%s found at startup. If you are only running one process, then you may need to manually delete the lockfiles found at %r.' % (len(lockfiles), plural, cls.storage_path))

    setup = classmethod(setup)

    def _get_file_path(self):
        f = os.path.join(self.storage_path, self.SESSION_PREFIX + self.id)
        if not os.path.abspath(f).startswith(self.storage_path):
            raise cherrypy.HTTPError(400, 'Invalid session id in cookie.')
        return f

    def _exists(self):
        path = self._get_file_path()
        return os.path.exists(path)

    def _load(self, path = None):
        if path is None:
            path = self._get_file_path()
        try:
            f = open(path, 'rb')
            try:
                return pickle.load(f)
            finally:
                f.close()

        except (IOError, EOFError):
            return

    def _save(self, expiration_time):
        f = open(self._get_file_path(), 'wb')
        try:
            pickle.dump((self._data, expiration_time), f, self.pickle_protocol)
        finally:
            f.close()

    def _delete(self):
        try:
            os.unlink(self._get_file_path())
        except OSError:
            pass

    def acquire_lock(self, path = None):
        """Acquire an exclusive lock on the currently-loaded session data."""
        if path is None:
            path = self._get_file_path()
        path += self.LOCK_SUFFIX
        while True:
            try:
                lockfd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
            except OSError:
                time.sleep(0.1)
            else:
                os.close(lockfd)
                break

        self.locked = True

    def release_lock(self, path = None):
        """Release the lock on the currently-loaded session data."""
        if path is None:
            path = self._get_file_path()
        os.unlink(path + self.LOCK_SUFFIX)
        self.locked = False

    def clean_up(self):
        """Clean up expired sessions."""
        now = datetime.datetime.now()
        for fname in os.listdir(self.storage_path):
            if fname.startswith(self.SESSION_PREFIX) and not fname.endswith(self.LOCK_SUFFIX):
                path = os.path.join(self.storage_path, fname)
                self.acquire_lock(path)
                try:
                    contents = self._load(path)
                    if contents is not None:
                        data, expiration_time = contents
                        if expiration_time < now:
                            os.unlink(path)
                finally:
                    self.release_lock(path)

    def __len__(self):
        """Return the number of active sessions."""
        return len([ fname for fname in os.listdir(self.storage_path) if fname.startswith(self.SESSION_PREFIX) and not fname.endswith(self.LOCK_SUFFIX) ])


class PostgresqlSession(Session):
    """ Implementation of the PostgreSQL backend for sessions. It assumes
        a table like this::
    
            create table session (
                id varchar(40),
                data text,
                expiration_time timestamp
            )
    
    You must provide your own get_db function.
    """
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, id = None, **kwargs):
        Session.__init__(self, id, **kwargs)
        self.cursor = self.db.cursor()

    def setup(cls, **kwargs):
        """Set up the storage system for Postgres-based sessions.
        
        This should only be called once per process; this will be done
        automatically when using sessions.init (as the built-in Tool does).
        """
        for k, v in kwargs.items():
            setattr(cls, k, v)

        self.db = self.get_db()

    setup = classmethod(setup)

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        self.db.commit()

    def _exists(self):
        self.cursor.execute('select data, expiration_time from session where id=%s', (self.id,))
        rows = self.cursor.fetchall()
        return bool(rows)

    def _load(self):
        self.cursor.execute('select data, expiration_time from session where id=%s', (self.id,))
        rows = self.cursor.fetchall()
        if not rows:
            return None
        pickled_data, expiration_time = rows[0]
        data = pickle.loads(pickled_data)
        return (data, expiration_time)

    def _save(self, expiration_time):
        pickled_data = pickle.dumps(self._data, self.pickle_protocol)
        self.cursor.execute('update session set data = %s, expiration_time = %s where id = %s', (pickled_data, expiration_time, self.id))

    def _delete(self):
        self.cursor.execute('delete from session where id=%s', (self.id,))

    def acquire_lock(self):
        """Acquire an exclusive lock on the currently-loaded session data."""
        self.locked = True
        self.cursor.execute('select id from session where id=%s for update', (self.id,))

    def release_lock(self):
        """Release the lock on the currently-loaded session data."""
        self.cursor.close()
        self.locked = False

    def clean_up(self):
        """Clean up expired sessions."""
        self.cursor.execute('delete from session where expiration_time < %s', (datetime.datetime.now(),))


class MemcachedSession(Session):
    mc_lock = threading.RLock()
    locks = {}
    servers = ['127.0.0.1:11211']

    def setup(cls, **kwargs):
        """Set up the storage system for memcached-based sessions.
        
        This should only be called once per process; this will be done
        automatically when using sessions.init (as the built-in Tool does).
        """
        for k, v in kwargs.items():
            setattr(cls, k, v)

        import memcache
        cls.cache = memcache.Client(cls.servers)

    setup = classmethod(setup)

    def _exists(self):
        self.mc_lock.acquire()
        try:
            return bool(self.cache.get(self.id))
        finally:
            self.mc_lock.release()

    def _load(self):
        self.mc_lock.acquire()
        try:
            return self.cache.get(self.id)
        finally:
            self.mc_lock.release()

    def _save(self, expiration_time):
        td = int(time.mktime(expiration_time.timetuple()))
        self.mc_lock.acquire()
        try:
            if not self.cache.set(self.id, (self._data, expiration_time), td):
                raise AssertionError('Session data for id %r not set.' % self.id)
        finally:
            self.mc_lock.release()

    def _delete(self):
        self.cache.delete(self.id)

    def acquire_lock(self):
        """Acquire an exclusive lock on the currently-loaded session data."""
        self.locked = True
        self.locks.setdefault(self.id, threading.RLock()).acquire()

    def release_lock(self):
        """Release the lock on the currently-loaded session data."""
        self.locks[self.id].release()
        self.locked = False

    def __len__(self):
        """Return the number of active sessions."""
        raise NotImplementedError


def save():
    """Save any changed session data."""
    if not hasattr(cherrypy.serving, 'session'):
        return
    request = cherrypy.serving.request
    response = cherrypy.serving.response
    if hasattr(request, '_sessionsaved'):
        return
    request._sessionsaved = True
    if response.stream:
        request.hooks.attach('on_end_request', cherrypy.session.save)
    else:
        if isinstance(response.body, types.GeneratorType):
            response.collapse_body()
        cherrypy.session.save()


save.failsafe = True

def close():
    """Close the session object for this request."""
    sess = getattr(cherrypy.serving, 'session', None)
    if getattr(sess, 'locked', False):
        sess.release_lock()


close.failsafe = True
close.priority = 90

def init(storage_type = 'ram', path = None, path_header = None, name = 'session_id', timeout = 60, domain = None, secure = False, clean_freq = 5, persistent = True, debug = False, **kwargs):
    """Initialize session object (using cookies).
    
    storage_type
        One of 'ram', 'file', 'postgresql'. This will be used
        to look up the corresponding class in cherrypy.lib.sessions
        globals. For example, 'file' will use the FileSession class.
    
    path
        The 'path' value to stick in the response cookie metadata.
    
    path_header
        If 'path' is None (the default), then the response
        cookie 'path' will be pulled from request.headers[path_header].
    
    name
        The name of the cookie.
    
    timeout
        The expiration timeout (in minutes) for the stored session data.
        If 'persistent' is True (the default), this is also the timeout
        for the cookie.
    
    domain
        The cookie domain.
    
    secure
        If False (the default) the cookie 'secure' value will not
        be set. If True, the cookie 'secure' value will be set (to 1).
    
    clean_freq (minutes)
        The poll rate for expired session cleanup.
    
    persistent
        If True (the default), the 'timeout' argument will be used
        to expire the cookie. If False, the cookie will not have an expiry,
        and the cookie will be a "session cookie" which expires when the
        browser is closed.
    
    Any additional kwargs will be bound to the new Session instance,
    and may be specific to the storage type. See the subclass of Session
    you're using for more information.
    """
    request = cherrypy.serving.request
    if hasattr(request, '_session_init_flag'):
        return
    request._session_init_flag = True
    id = None
    if name in request.cookie:
        id = request.cookie[name].value
        if debug:
            cherrypy.log('ID obtained from request.cookie: %r' % id, 'TOOLS.SESSIONS')
    storage_class = storage_type.title() + 'Session'
    storage_class = globals()[storage_class]
    if not hasattr(cherrypy, 'session'):
        if hasattr(storage_class, 'setup'):
            storage_class.setup(**kwargs)
    kwargs['timeout'] = timeout
    kwargs['clean_freq'] = clean_freq
    cherrypy.serving.session = sess = storage_class(id, **kwargs)
    sess.debug = debug

    def update_cookie(id):
        """Update the cookie every time the session id changes."""
        cherrypy.serving.response.cookie[name] = id

    sess.id_observers.append(update_cookie)
    if not hasattr(cherrypy, 'session'):
        cherrypy.session = cherrypy._ThreadLocalProxy('session')
    if persistent:
        cookie_timeout = timeout
    else:
        cookie_timeout = None
    set_response_cookie(path=path, path_header=path_header, name=name, timeout=cookie_timeout, domain=domain, secure=secure)


def set_response_cookie(path = None, path_header = None, name = 'session_id', timeout = 60, domain = None, secure = False):
    """Set a response cookie for the client.
    
    path
        the 'path' value to stick in the response cookie metadata.
    
    path_header
        if 'path' is None (the default), then the response
        cookie 'path' will be pulled from request.headers[path_header].
    
    name
        the name of the cookie.
    
    timeout
        the expiration timeout for the cookie. If 0 or other boolean
        False, no 'expires' param will be set, and the cookie will be a
        "session cookie" which expires when the browser is closed.
    
    domain
        the cookie domain.
    
    secure
        if False (the default) the cookie 'secure' value will not
        be set. If True, the cookie 'secure' value will be set (to 1).
    
    """
    cookie = cherrypy.serving.response.cookie
    cookie[name] = cherrypy.serving.session.id
    cookie[name]['path'] = path or cherrypy.serving.request.headers.get(path_header) or '/'
    if timeout:
        e = time.time() + timeout * 60
        cookie[name]['expires'] = httputil.HTTPDate(e)
    if domain is not None:
        cookie[name]['domain'] = domain
    if secure:
        cookie[name]['secure'] = 1


def expire():
    """Expire the current session cookie."""
    name = cherrypy.serving.request.config.get('tools.sessions.name', 'session_id')
    one_year = 31536000
    e = time.time() - one_year
    cherrypy.serving.response.cookie[name]['expires'] = httputil.HTTPDate(e)
