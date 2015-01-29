#Embedded file name: cherrypy\_cpreqbody.py
"""Request body processing for CherryPy.

.. versionadded:: 3.2

Application authors have complete control over the parsing of HTTP request
entities. In short, :attr:`cherrypy.request.body<cherrypy._cprequest.Request.body>`
is now always set to an instance of :class:`RequestBody<cherrypy._cpreqbody.RequestBody>`,
and *that* class is a subclass of :class:`Entity<cherrypy._cpreqbody.Entity>`.

When an HTTP request includes an entity body, it is often desirable to
provide that information to applications in a form other than the raw bytes.
Different content types demand different approaches. Examples:

 * For a GIF file, we want the raw bytes in a stream.
 * An HTML form is better parsed into its component fields, and each text field
   decoded from bytes to unicode.
 * A JSON body should be deserialized into a Python dict or list.

When the request contains a Content-Type header, the media type is used as a
key to look up a value in the
:attr:`request.body.processors<cherrypy._cpreqbody.Entity.processors>` dict.
If the full media
type is not found, then the major type is tried; for example, if no processor
is found for the 'image/jpeg' type, then we look for a processor for the 'image'
types altogether. If neither the full type nor the major type has a matching
processor, then a default processor is used
(:func:`default_proc<cherrypy._cpreqbody.Entity.default_proc>`). For most
types, this means no processing is done, and the body is left unread as a
raw byte stream. Processors are configurable in an 'on_start_resource' hook.

Some processors, especially those for the 'text' types, attempt to decode bytes
to unicode. If the Content-Type request header includes a 'charset' parameter,
this is used to decode the entity. Otherwise, one or more default charsets may
be attempted, although this decision is up to each processor. If a processor
successfully decodes an Entity or Part, it should set the
:attr:`charset<cherrypy._cpreqbody.Entity.charset>` attribute
on the Entity or Part to the name of the successful charset, so that
applications can easily re-encode or transcode the value if they wish.

If the Content-Type of the request entity is of major type 'multipart', then
the above parsing process, and possibly a decoding process, is performed for
each part.

For both the full entity and multipart parts, a Content-Disposition header may
be used to fill :attr:`name<cherrypy._cpreqbody.Entity.name>` and
:attr:`filename<cherrypy._cpreqbody.Entity.filename>` attributes on the
request.body or the Part.

.. _custombodyprocessors:

Custom Processors
=================

You can add your own processors for any specific or major MIME type. Simply add
it to the :attr:`processors<cherrypy._cprequest.Entity.processors>` dict in a
hook/tool that runs at ``on_start_resource`` or ``before_request_body``. 
Here's the built-in JSON tool for an example::

    def json_in(force=True, debug=False):
        request = cherrypy.serving.request
        def json_processor(entity):
            \"\"\"Read application/json data into request.json.\"\"\"
            if not entity.headers.get("Content-Length", ""):
                raise cherrypy.HTTPError(411)
            
            body = entity.fp.read()
            try:
                request.json = json_decode(body)
            except ValueError:
                raise cherrypy.HTTPError(400, 'Invalid JSON document')
        if force:
            request.body.processors.clear()
            request.body.default_proc = cherrypy.HTTPError(
                415, 'Expected an application/json content type')
        request.body.processors['application/json'] = json_processor

We begin by defining a new ``json_processor`` function to stick in the ``processors``
dictionary. All processor functions take a single argument, the ``Entity`` instance
they are to process. It will be called whenever a request is received (for those
URI's where the tool is turned on) which has a ``Content-Type`` of
"application/json".

First, it checks for a valid ``Content-Length`` (raising 411 if not valid), then
reads the remaining bytes on the socket. The ``fp`` object knows its own length, so
it won't hang waiting for data that never arrives. It will return when all data
has been read. Then, we decode those bytes using Python's built-in ``json`` module,
and stick the decoded result onto ``request.json`` . If it cannot be decoded, we
raise 400.

If the "force" argument is True (the default), the ``Tool`` clears the ``processors``
dict so that request entities of other ``Content-Types`` aren't parsed at all. Since
there's no entry for those invalid MIME types, the ``default_proc`` method of ``cherrypy.request.body``
is called. But this does nothing by default (usually to provide the page handler an opportunity to handle it.)
But in our case, we want to raise 415, so we replace ``request.body.default_proc``
with the error (``HTTPError`` instances, when called, raise themselves).

If we were defining a custom processor, we can do so without making a ``Tool``. Just add the config entry::

    request.body.processors = {'application/json': json_processor}

Note that you can only replace the ``processors`` dict wholesale this way, not update the existing one.
"""
import re
import sys
import tempfile
from urllib import unquote_plus
import cherrypy
from cherrypy._cpcompat import basestring, ntob, ntou
from cherrypy.lib import httputil

def process_urlencoded(entity):
    """Read application/x-www-form-urlencoded data into entity.params."""
    qs = entity.fp.read()
    for charset in entity.attempt_charsets:
        try:
            params = {}
            for aparam in qs.split(ntob('&')):
                for pair in aparam.split(ntob(';')):
                    if not pair:
                        continue
                    atoms = pair.split(ntob('='), 1)
                    if len(atoms) == 1:
                        atoms.append(ntob(''))
                    key = unquote_plus(atoms[0]).decode(charset)
                    try:
                        value = unquote_plus(atoms[1]).decode(charset)
                    except Exception:
                        value = unquote_plus(atoms[1])

                    if key in params:
                        if not isinstance(params[key], list):
                            params[key] = [params[key]]
                        params[key].append(value)
                    else:
                        params[key] = value

        except UnicodeDecodeError:
            pass
        else:
            entity.charset = charset
            break

    else:
        raise cherrypy.HTTPError(400, 'The request entity could not be decoded. The following charsets were attempted: %s' % repr(entity.attempt_charsets))

    for key, value in params.items():
        if key in entity.params:
            if not isinstance(entity.params[key], list):
                entity.params[key] = [entity.params[key]]
            entity.params[key].append(value)
        else:
            entity.params[key] = value


def process_multipart(entity):
    """Read all multipart parts into entity.parts."""
    ib = ''
    if 'boundary' in entity.content_type.params:
        ib = entity.content_type.params['boundary'].strip('"')
    if not re.match('^[ -~]{0,200}[!-~]$', ib):
        raise ValueError('Invalid boundary in multipart form: %r' % (ib,))
    ib = ('--' + ib).encode('ascii')
    while True:
        b = entity.readline()
        if not b:
            return
        b = b.strip()
        if b == ib:
            break

    while True:
        part = entity.part_class.from_fp(entity.fp, ib)
        entity.parts.append(part)
        part.process()
        if part.fp.done:
            break


def process_multipart_form_data(entity):
    """Read all multipart/form-data parts into entity.parts or entity.params."""
    process_multipart(entity)
    kept_parts = []
    for part in entity.parts:
        if part.name is None:
            kept_parts.append(part)
        else:
            if part.filename is None:
                value = part.fullvalue()
            else:
                value = part
            if part.name in entity.params:
                if not isinstance(entity.params[part.name], list):
                    entity.params[part.name] = [entity.params[part.name]]
                entity.params[part.name].append(value)
            else:
                entity.params[part.name] = value

    entity.parts = kept_parts


def _old_process_multipart(entity):
    """The behavior of 3.2 and lower. Deprecated and will be changed in 3.3."""
    process_multipart(entity)
    params = entity.params
    for part in entity.parts:
        if part.name is None:
            key = ntou('parts')
        else:
            key = part.name
        if part.filename is None:
            value = part.fullvalue()
        else:
            value = part
        if key in params:
            if not isinstance(params[key], list):
                params[key] = [params[key]]
            params[key].append(value)
        else:
            params[key] = value


class Entity(object):
    """An HTTP request body, or MIME multipart body.
    
    This class collects information about the HTTP request entity. When a
    given entity is of MIME type "multipart", each part is parsed into its own
    Entity instance, and the set of parts stored in
    :attr:`entity.parts<cherrypy._cpreqbody.Entity.parts>`.
    
    Between the ``before_request_body`` and ``before_handler`` tools, CherryPy
    tries to process the request body (if any) by calling
    :func:`request.body.process<cherrypy._cpreqbody.RequestBody.process`.
    This uses the ``content_type`` of the Entity to look up a suitable processor
    in :attr:`Entity.processors<cherrypy._cpreqbody.Entity.processors>`, a dict.
    If a matching processor cannot be found for the complete Content-Type,
    it tries again using the major type. For example, if a request with an
    entity of type "image/jpeg" arrives, but no processor can be found for
    that complete type, then one is sought for the major type "image". If a
    processor is still not found, then the
    :func:`default_proc<cherrypy._cpreqbody.Entity.default_proc>` method of the
    Entity is called (which does nothing by default; you can override this too).
    
    CherryPy includes processors for the "application/x-www-form-urlencoded"
    type, the "multipart/form-data" type, and the "multipart" major type.
    CherryPy 3.2 processes these types almost exactly as older versions.
    Parts are passed as arguments to the page handler using their
    ``Content-Disposition.name`` if given, otherwise in a generic "parts"
    argument. Each such part is either a string, or the
    :class:`Part<cherrypy._cpreqbody.Part>` itself if it's a file. (In this
    case it will have ``file`` and ``filename`` attributes, or possibly a
    ``value`` attribute). Each Part is itself a subclass of
    Entity, and has its own ``process`` method and ``processors`` dict.
    
    There is a separate processor for the "multipart" major type which is more
    flexible, and simply stores all multipart parts in
    :attr:`request.body.parts<cherrypy._cpreqbody.Entity.parts>`. You can
    enable it with::
    
        cherrypy.request.body.processors['multipart'] = _cpreqbody.process_multipart
    
    in an ``on_start_resource`` tool.
    """
    attempt_charsets = ['utf-8']
    charset = None
    content_type = None
    default_content_type = 'application/x-www-form-urlencoded'
    filename = None
    fp = None
    headers = None
    length = None
    name = None
    params = None
    processors = {'application/x-www-form-urlencoded': process_urlencoded,
     'multipart/form-data': process_multipart_form_data,
     'multipart': process_multipart}
    parts = None
    part_class = None

    def __init__(self, fp, headers, params = None, parts = None):
        self.processors = self.processors.copy()
        self.fp = fp
        self.headers = headers
        if params is None:
            params = {}
        self.params = params
        if parts is None:
            parts = []
        self.parts = parts
        self.content_type = headers.elements('Content-Type')
        if self.content_type:
            self.content_type = self.content_type[0]
        else:
            self.content_type = httputil.HeaderElement.from_str(self.default_content_type)
        dec = self.content_type.params.get('charset', None)
        if dec:
            self.attempt_charsets = [dec] + [ c for c in self.attempt_charsets if c != dec ]
        else:
            self.attempt_charsets = self.attempt_charsets[:]
        self.length = None
        clen = headers.get('Content-Length', None)
        if clen is not None and 'chunked' not in headers.get('Transfer-Encoding', ''):
            try:
                self.length = int(clen)
            except ValueError:
                pass

        self.name = None
        self.filename = None
        disp = headers.elements('Content-Disposition')
        if disp:
            disp = disp[0]
            if 'name' in disp.params:
                self.name = disp.params['name']
                if self.name.startswith('"') and self.name.endswith('"'):
                    self.name = self.name[1:-1]
            if 'filename' in disp.params:
                self.filename = disp.params['filename']
                if self.filename.startswith('"') and self.filename.endswith('"'):
                    self.filename = self.filename[1:-1]

    type = property(lambda self: self.content_type, doc='A deprecated alias for :attr:`content_type<cherrypy._cpreqbody.Entity.content_type>`.')

    def read(self, size = None, fp_out = None):
        return self.fp.read(size, fp_out)

    def readline(self, size = None):
        return self.fp.readline(size)

    def readlines(self, sizehint = None):
        return self.fp.readlines(sizehint)

    def __iter__(self):
        return self

    def next(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def read_into_file(self, fp_out = None):
        """Read the request body into fp_out (or make_file() if None). Return fp_out."""
        if fp_out is None:
            fp_out = self.make_file()
        self.read(fp_out=fp_out)
        return fp_out

    def make_file(self):
        """Return a file-like object into which the request body will be read.
        
        By default, this will return a TemporaryFile. Override as needed.
        See also :attr:`cherrypy._cpreqbody.Part.maxrambytes`."""
        return tempfile.TemporaryFile()

    def fullvalue(self):
        """Return this entity as a string, whether stored in a file or not."""
        if self.file:
            self.file.seek(0)
            value = self.file.read()
            self.file.seek(0)
        else:
            value = self.value
        return value

    def process(self):
        """Execute the best-match processor for the given media type."""
        proc = None
        ct = self.content_type.value
        try:
            proc = self.processors[ct]
        except KeyError:
            toptype = ct.split('/', 1)[0]
            try:
                proc = self.processors[toptype]
            except KeyError:
                pass

        if proc is None:
            self.default_proc()
        else:
            proc(self)

    def default_proc(self):
        """Called if a more-specific processor is not found for the ``Content-Type``."""
        pass


class Part(Entity):
    """A MIME part entity, part of a multipart entity."""
    attempt_charsets = ['us-ascii', 'utf-8']
    boundary = None
    default_content_type = 'text/plain'
    maxrambytes = 1000

    def __init__(self, fp, headers, boundary):
        Entity.__init__(self, fp, headers)
        self.boundary = boundary
        self.file = None
        self.value = None

    def from_fp(cls, fp, boundary):
        headers = cls.read_headers(fp)
        return cls(fp, headers, boundary)

    from_fp = classmethod(from_fp)

    def read_headers(cls, fp):
        headers = httputil.HeaderMap()
        while True:
            line = fp.readline()
            if not line:
                raise EOFError('Illegal end of headers.')
            if line == ntob('\r\n'):
                break
            if not line.endswith(ntob('\r\n')):
                raise ValueError('MIME requires CRLF terminators: %r' % line)
            if line[0] in ntob(' \t'):
                v = line.strip().decode('ISO-8859-1')
            else:
                k, v = line.split(ntob(':'), 1)
                k = k.strip().decode('ISO-8859-1')
                v = v.strip().decode('ISO-8859-1')
            existing = headers.get(k)
            if existing:
                v = ', '.join((existing, v))
            headers[k] = v

        return headers

    read_headers = classmethod(read_headers)

    def read_lines_to_boundary(self, fp_out = None):
        """Read bytes from self.fp and return or write them to a file.
        
        If the 'fp_out' argument is None (the default), all bytes read are
        returned in a single byte string.
        
        If the 'fp_out' argument is not None, it must be a file-like object that
        supports the 'write' method; all bytes read will be written to the fp,
        and that fp is returned.
        """
        endmarker = self.boundary + ntob('--')
        delim = ntob('')
        prev_lf = True
        lines = []
        seen = 0
        while True:
            line = self.fp.readline(65536)
            if not line:
                raise EOFError('Illegal end of multipart body.')
            if line.startswith(ntob('--')) and prev_lf:
                strippedline = line.strip()
                if strippedline == self.boundary:
                    break
                if strippedline == endmarker:
                    self.fp.finish()
                    break
            line = delim + line
            if line.endswith(ntob('\r\n')):
                delim = ntob('\r\n')
                line = line[:-2]
                prev_lf = True
            elif line.endswith(ntob('\n')):
                delim = ntob('\n')
                line = line[:-1]
                prev_lf = True
            else:
                delim = ntob('')
                prev_lf = False
            if fp_out is None:
                lines.append(line)
                seen += len(line)
                if seen > self.maxrambytes:
                    fp_out = self.make_file()
                    for line in lines:
                        fp_out.write(line)

            else:
                fp_out.write(line)

        if fp_out is None:
            result = ntob('').join(lines)
            for charset in self.attempt_charsets:
                try:
                    result = result.decode(charset)
                except UnicodeDecodeError:
                    pass
                else:
                    self.charset = charset
                    return result

            else:
                raise cherrypy.HTTPError(400, 'The request entity could not be decoded. The following charsets were attempted: %s' % repr(self.attempt_charsets))

        else:
            fp_out.seek(0)
            return fp_out

    def default_proc(self):
        """Called if a more-specific processor is not found for the ``Content-Type``."""
        if self.filename:
            self.file = self.read_into_file()
        else:
            result = self.read_lines_to_boundary()
            if isinstance(result, basestring):
                self.value = result
            else:
                self.file = result

    def read_into_file(self, fp_out = None):
        """Read the request body into fp_out (or make_file() if None). Return fp_out."""
        if fp_out is None:
            fp_out = self.make_file()
        self.read_lines_to_boundary(fp_out=fp_out)
        return fp_out


Entity.part_class = Part

class Infinity(object):

    def __cmp__(self, other):
        return 1

    def __sub__(self, other):
        return self


inf = Infinity()
comma_separated_headers = ['Accept',
 'Accept-Charset',
 'Accept-Encoding',
 'Accept-Language',
 'Accept-Ranges',
 'Allow',
 'Cache-Control',
 'Connection',
 'Content-Encoding',
 'Content-Language',
 'Expect',
 'If-Match',
 'If-None-Match',
 'Pragma',
 'Proxy-Authenticate',
 'Te',
 'Trailer',
 'Transfer-Encoding',
 'Upgrade',
 'Vary',
 'Via',
 'Warning',
 'Www-Authenticate']

class SizedReader:

    def __init__(self, fp, length, maxbytes, bufsize = 8192, has_trailers = False):
        self.fp = fp
        self.length = length
        self.maxbytes = maxbytes
        self.buffer = ntob('')
        self.bufsize = bufsize
        self.bytes_read = 0
        self.done = False
        self.has_trailers = has_trailers

    def read(self, size = None, fp_out = None):
        """Read bytes from the request body and return or write them to a file.
        
        A number of bytes less than or equal to the 'size' argument are read
        off the socket. The actual number of bytes read are tracked in
        self.bytes_read. The number may be smaller than 'size' when 1) the
        client sends fewer bytes, 2) the 'Content-Length' request header
        specifies fewer bytes than requested, or 3) the number of bytes read
        exceeds self.maxbytes (in which case, 413 is raised).
        
        If the 'fp_out' argument is None (the default), all bytes read are
        returned in a single byte string.
        
        If the 'fp_out' argument is not None, it must be a file-like object that
        supports the 'write' method; all bytes read will be written to the fp,
        and None is returned.
        """
        if self.length is None:
            if size is None:
                remaining = inf
            else:
                remaining = size
        else:
            remaining = self.length - self.bytes_read
            if size and size < remaining:
                remaining = size
        if remaining == 0:
            self.finish()
            if fp_out is None:
                return ntob('')
            else:
                return
        chunks = []
        if self.buffer:
            if remaining is inf:
                data = self.buffer
                self.buffer = ntob('')
            else:
                data = self.buffer[:remaining]
                self.buffer = self.buffer[remaining:]
            datalen = len(data)
            remaining -= datalen
            self.bytes_read += datalen
            if self.maxbytes and self.bytes_read > self.maxbytes:
                raise cherrypy.HTTPError(413)
            if fp_out is None:
                chunks.append(data)
            else:
                fp_out.write(data)
        while remaining > 0:
            chunksize = min(remaining, self.bufsize)
            try:
                data = self.fp.read(chunksize)
            except Exception:
                e = sys.exc_info()[1]
                if e.__class__.__name__ == 'MaxSizeExceeded':
                    raise cherrypy.HTTPError(413, 'Maximum request length: %r' % e.args[1])
                else:
                    raise

            if not data:
                self.finish()
                break
            datalen = len(data)
            remaining -= datalen
            self.bytes_read += datalen
            if self.maxbytes and self.bytes_read > self.maxbytes:
                raise cherrypy.HTTPError(413)
            if fp_out is None:
                chunks.append(data)
            else:
                fp_out.write(data)

        if fp_out is None:
            return ntob('').join(chunks)

    def readline(self, size = None):
        """Read a line from the request body and return it."""
        chunks = []
        while size is None or size > 0:
            chunksize = self.bufsize
            if size is not None and size < self.bufsize:
                chunksize = size
            data = self.read(chunksize)
            if not data:
                break
            pos = data.find(ntob('\n')) + 1
            if pos:
                chunks.append(data[:pos])
                remainder = data[pos:]
                self.buffer += remainder
                self.bytes_read -= len(remainder)
                break
            else:
                chunks.append(data)

        return ntob('').join(chunks)

    def readlines(self, sizehint = None):
        """Read lines from the request body and return them."""
        if self.length is not None:
            if sizehint is None:
                sizehint = self.length - self.bytes_read
            else:
                sizehint = min(sizehint, self.length - self.bytes_read)
        lines = []
        seen = 0
        while True:
            line = self.readline()
            if not line:
                break
            lines.append(line)
            seen += len(line)
            if seen >= sizehint:
                break

        return lines

    def finish(self):
        self.done = True
        if self.has_trailers and hasattr(self.fp, 'read_trailer_lines'):
            self.trailers = {}
            try:
                for line in self.fp.read_trailer_lines():
                    if line[0] in ntob(' \t'):
                        v = line.strip()
                    else:
                        try:
                            k, v = line.split(ntob(':'), 1)
                        except ValueError:
                            raise ValueError('Illegal header line.')

                        k = k.strip().title()
                        v = v.strip()
                    if k in comma_separated_headers:
                        existing = self.trailers.get(envname)
                        if existing:
                            v = ntob(', ').join((existing, v))
                    self.trailers[k] = v

            except Exception:
                e = sys.exc_info()[1]
                if e.__class__.__name__ == 'MaxSizeExceeded':
                    raise cherrypy.HTTPError(413, 'Maximum request length: %r' % e.args[1])
                else:
                    raise


class RequestBody(Entity):
    """The entity of the HTTP request."""
    bufsize = 8192
    default_content_type = ''
    maxbytes = None

    def __init__(self, fp, headers, params = None, request_params = None):
        Entity.__init__(self, fp, headers, params)
        if self.content_type.value.startswith('text/'):
            for c in ('ISO-8859-1', 'iso-8859-1', 'Latin-1', 'latin-1'):
                if c in self.attempt_charsets:
                    break
            else:
                self.attempt_charsets.append('ISO-8859-1')

        self.processors['multipart'] = _old_process_multipart
        if request_params is None:
            request_params = {}
        self.request_params = request_params

    def process(self):
        """Process the request entity based on its Content-Type."""
        h = cherrypy.serving.request.headers
        if 'Content-Length' not in h and 'Transfer-Encoding' not in h:
            raise cherrypy.HTTPError(411)
        self.fp = SizedReader(self.fp, self.length, self.maxbytes, bufsize=self.bufsize, has_trailers='Trailer' in h)
        super(RequestBody, self).process()
        request_params = self.request_params
        for key, value in self.params.items():
            if isinstance(key, unicode):
                key = key.encode('ISO-8859-1')
            if key in request_params:
                if not isinstance(request_params[key], list):
                    request_params[key] = [request_params[key]]
                request_params[key].append(value)
            else:
                request_params[key] = value
