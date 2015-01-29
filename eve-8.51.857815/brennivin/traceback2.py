#Embedded file name: brennivin\traceback2.py
"""
Utility functions for better traceback
It has the same interface as the good old ``traceback`` module.

Appropriate functions have the additional ``show_locals`` argument
which will cause us to try to display local variables for each frame.

Also, the stack extraction functions such as :func:`print_stack` have an
``up`` argument used to trim the deepest levels of a callstack,
such as when they are called from a utility function in which we aren't interested.
"""
import linecache as _linecache
import pprint as _pprint
import sys as _sys
from traceback import format_exception_only as _format_exception_only
from . import compat as _compat
FORMAT_NORMAL = 0
FORMAT_LOGSRV = 1
FORMAT_SINGLE = 2

def print_exc(limit = None, file = None, show_locals = 0, format = FORMAT_NORMAL):
    _getfile(file).write(format_exc(limit, show_locals, format))


def format_exc(limit = None, show_locals = 0, format = FORMAT_NORMAL):
    etype, value, tb = _sys.exc_info()
    try:
        return ''.join(format_exception(etype, value, tb, limit, show_locals, format))
    finally:
        del etype
        del value
        del tb


def print_exception(etype, value, tb, limit = None, file = None, show_locals = 0, format = FORMAT_NORMAL):
    _getfile(file).write(''.join(format_exception(etype, value, tb, limit, show_locals, format)))


def format_exception(etype, value, tb, limit = None, show_locals = 0, format = FORMAT_NORMAL):
    lst = []
    if tb:
        lst.append('Traceback (most recent call last):\n')
        lst.extend(format_tb(tb, limit, show_locals, format))
    return lst + _format_exception_only(etype, value)


def print_stack(f = None, limit = None, up = 0, show_locals = 0, format = FORMAT_NORMAL, file = None):
    if f is None:
        up += 1
    _getfile(file).write(''.join(format_stack(f, limit, up, show_locals, format)))


def format_stack(f = None, limit = None, up = 0, show_locals = 0, format = FORMAT_NORMAL):
    if f is None:
        up += 1
    return format_list(extract_stack(f, limit, up, show_locals), show_locals, format)


def print_tb(tb, limit = None, file = None, show_locals = 0, format = FORMAT_NORMAL):
    _getfile(file).write(''.join(format_tb(tb, limit, show_locals, format)))


def format_tb(tb, limit = None, show_locals = 0, format = FORMAT_NORMAL):
    return format_list(extract_tb(tb, limit, show_locals), show_locals, format)


def format_list(extracted_list, show_locals = 0, format = FORMAT_NORMAL):
    if show_locals < 0:
        start_locals = 0
    else:
        start_locals = len(extracted_list) - show_locals
    data = []
    for i, (filename, lineno, name, line, f_locals) in enumerate(extracted_list):
        if format & FORMAT_NORMAL == FORMAT_NORMAL:
            item = '  File "%s", line %d, in %s\n' % (filename, lineno, name)
            if line:
                item += '    %s\n' % line.strip()
        if format & FORMAT_LOGSRV:
            item = '%s(%s) %s' % (filename, lineno, name)
        else:
            item = '  File "%s", line %d, in %s' % (filename, lineno, name)
        if line:
            if format & FORMAT_SINGLE:
                item += ' : %s\n' % (line.strip(),)
            else:
                item += '\n    %s\n' % (line.strip(),)
        else:
            item += '\n'
        if i >= start_locals:
            item += ''.join(_format_locals(f_locals, format))
        data.append(item)

    return data


def _format_locals(f_locals, format):
    lines = []
    if f_locals is None:
        return lines
    for key, value in sorted(f_locals.items()):
        if format & FORMAT_LOGSRV:
            extra = '        %s = ' % (key,)
        else:
            extra = '%20s = ' % (key,)
        try:
            width = 253 - len(extra)
            val = _pprint.pformat(value, depth=1, width=width)
            if len(val) > 1024:
                val = val[:1024] + '...'
            vlines = val.splitlines()
            if len(vlines) > 4:
                vlines[4:] = ['...']
            for i in _compat.xrange(1, len(vlines)):
                vlines[i] = ' ' * 23 + vlines[i]

            extra += '\n'.join(vlines) + '\n'
        except Exception as e:
            try:
                extra += '<error printing value: %r>' % (e,)
            except Exception:
                extra += '<error printing value>'

        lines.append(extra)

    return lines


def extract_tb(tb, limit = None, extract_locals = 0):
    frames = []
    n = 1
    while tb is not None and (limit is None or n < limit):
        frames.append((tb.tb_frame, tb.tb_lineno))
        tb = tb.tb_next
        n += 1

    return _extract_frames(frames, extract_locals)


def extract_stack(f = None, limit = None, up = 0, extract_locals = 0):
    if f is None:
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            f = _sys.exc_info()[2].tb_frame.f_back

    frames = []
    n = 0
    while f is not None and (limit is None or n < limit + up):
        frames.append((f, f.f_lineno))
        f = f.f_back
        n += 1

    frames.reverse()
    if up > 0:
        del frames[-up:]
    return _extract_frames(frames, extract_locals)


def _extract_frames(frames, extract_locals = 0):
    result = []
    if extract_locals >= 0:
        j = len(frames) - extract_locals
    else:
        j = 0
    for i, (f, lineno) in enumerate(frames):
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        _linecache.checkcache(filename)
        line = _linecache.getline(filename, lineno, f.f_globals)
        if line:
            line = line.strip()
        else:
            line = None
        locals = f.f_locals if i >= j else None
        result.append((filename,
         lineno,
         name,
         line,
         locals))

    return result


def _getfile(file):
    if file is None:
        file = _sys.stderr
    return file
