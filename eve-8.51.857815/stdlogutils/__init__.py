#Embedded file name: stdlogutils\__init__.py
import __builtin__
import cStringIO
import logging
import os
import sys
import traceback2
import zlib
from brennivin.logutils import *
try:
    import devenv
except ImportError:
    devenv = None

def GetStack(exception_list, caught_list = None, show_locals = 0, show_lines = True):
    s = GetStackOnly(exception_list, caught_list, show_locals, show_lines)
    id = GetStackID(exception_list, caught_list)
    return (s, id)


def GetStackID(exception_list, caught_list = None):
    stack = GetStackOnly(exception_list, caught_list, show_locals=0, show_lines=False)
    stack = ''.join(stack)[-4000:]
    return (zlib.adler32(stack), stack)


def GetStackOnly(exception_list, caught_list = None, show_locals = 0, show_lines = True):
    """
    Construct a stack, pasting together the traceback, and the callstack from that frame
    """
    if caught_list is not None:
        stack = ['Caught at:\n']
        stack += FormatList(caught_list, show_locals=False, show_lines=show_lines)
        stack.append('Thrown at:\n')
    else:
        stack = []
    stack += FormatList(exception_list, show_locals=show_locals, show_lines=show_lines)
    return stack


def FormatList(extracted_list, show_locals = 0, show_lines = True):
    l = []
    for line in extracted_list:
        l2 = list(line)
        if not show_lines:
            l2[3] = ''
        l.append(l2)

    lines = traceback2.format_list(l, show_locals, format=traceback2.FORMAT_LOGSRV | traceback2.FORMAT_SINGLE)
    return lines


traceID = 0L

def NextTraceID():
    """
    We number our exception traces so need to keep count between eve logs and normal
    logging.
    """
    global traceID
    traceID += 1
    return traceID


class EveExceptionsFormatter(logging.Formatter):

    def _LogThreadLocals(self, file):
        file.write('Thread Locals:')
        if hasattr(__builtin__, 'session'):
            file.write('  session was ')
            file.write(str(session) + '\n')
        else:
            file.write('No session information available.\n')

    def _LogServerInfo(self, file):
        if hasattr(__builtin__, 'boot'):
            if boot.role != 'client':
                try:
                    import blue
                    ram = blue.win32.GetProcessMemoryInfo()['PagefileUsage'] / 1024 / 1024
                    cpuLoad = sm.GetService('machoNet').GetCPULoad()
                    m = blue.win32.GlobalMemoryStatus()
                    memLeft = m['AvailPhys'] / 1024 / 1024
                    txt = 'System Information: '
                    txt += ' Node ID: %s' % sm.GetService('machoNet').GetNodeID()
                    if boot.role == 'server':
                        txt += ' | Node Name: %s' % sm.GetService('machoNet').GetLocalHostName()
                    txt += ' | Total CPU load: %s%%%%' % int(cpuLoad)
                    txt += ' | Process memory in use: %s MB' % ram
                    txt += ' | Physical memory left: %s MB' % memLeft
                    file.write(txt + '\n')
                except Exception:
                    sys.exc_clear()

        else:
            file.write('No boot role available.\n')

    def format(self, record):
        """
        Format the specified record as text.
        
        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there is exception information,
        it is formatted using formatException() and appended to the message.
        
        CWP: This differs from the standard Formatter by logging exceptions with our
        format and additional information.
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self._fmt % record.__dict__
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            try:
                record.asctime = self.formatTime(record, self.datefmt)
                traceID = NextTraceID()
                exceptionString = 'EXCEPTION #%d' % traceID + ' logged at %(asctime)s ' + ' %(message)s\n%(exc_text)s\nEXCEPTION_END'
                s = exceptionString % record.__dict__
                sys.stderr.write('An exception has occurred. It has been logged in the log server as exception #{}\n'.format(traceID))
            except UnicodeError:
                s += record.exc_text.decode(sys.getfilesystemencoding(), 'replace')

        return s

    def formatException(self, ei):
        etype, exc, tb = ei
        exception_list = traceback2.extract_tb(tb, extract_locals=True)
        if tb:
            caught_list = traceback2.extract_stack(tb.tb_frame)
        else:
            caught_list = traceback2.extract_stack(up=2)
        formatted_exception = traceback2.format_exception_only(etype, exc)
        stack, stackID = GetStack(exception_list, caught_list, show_locals=True)
        sio = cStringIO.StringIO()
        for line in stack:
            sio.write(line)

        for line in formatted_exception:
            sio.write(line)

        self._LogThreadLocals(sio)
        self._LogServerInfo(sio)
        try:
            sio.write('Stackhash: {}\n'.format(stackID[0]))
        except Exception:
            pass

        s = sio.getvalue()
        sio.close()
        return s


class FmtExt(Fmt):
    EVETIME = '%d/%m/%y %H:%M:%S'
    FMT_EVE = EveExceptionsFormatter(None, EVETIME)


Fmt = FmtExt

def getLoggerExt(name = None, defaultHandler = None, defaultFormatter = None):
    """Returns a Logger from logging.getLogger(name).
    
    If no handlers exist for the logger and defaultHandler is not None,
    assign defaultHandler.
    
    If defaultHandler was assigned and defaultFormatter is not None,
    set defaultFormatter as defaultHandler's formatter.
    """
    lo = logging.getLogger(name)
    if not lo.handlers and defaultHandler:
        if defaultFormatter:
            defaultHandler.setFormatter(defaultFormatter)
        lo.addHandler(defaultHandler)
    return lo


GetTimestampedFilename = timestamped_filename
GetTimestamp = timestamp

def GetTimestampedFilename2(appname, basename = None, ext = '.log', fmt = '%Y-%m-%d-%H-%M-%S', timestruct = None, _getpid = os.getpid):
    """Using default keyword arguments
    return filename ``<appname>_<timestamp>_<pid>.log``
    in the app's folder in ccptechart prefs.
    
    :param appname: Specifies log folder by calling
      :py:meth:`devenv.GetAppFolder(appname)`. Also determines the
      log filename if ``basename`` is not specified.
    :param basename: If specified determines the prefix of the log filename,
      e.g. ``<basename>_<timestamp>_<pid>.log>``
    """
    if basename is None:
        basename = appname
    folder = devenv.GetAppFolder(appname, makedirs=True)
    return get_timestamped_logfilename(folder, basename, ext, fmt, timestruct, _getpid)


class _LogLevelDisplayInfo(object):

    def __init__(self):
        self.nameToLevel = {'Not Set': logging.NOTSET,
         'Debug': logging.DEBUG,
         'Info': logging.INFO,
         'Warn': logging.WARN,
         'Error': logging.ERROR,
         'Critical': logging.CRITICAL}
        self.levelToName = dict(zip(self.nameToLevel.values(), self.nameToLevel.keys()))
        sortedByLevel = sorted(self.nameToLevel.items(), key=lambda kvp: kvp[1])
        self.namesSortedByLevel = map(lambda kvp: kvp[0], sortedByLevel)


LogLevelDisplayInfo = _LogLevelDisplayInfo()
GetFilenamesFromLoggers = get_filenames_from_loggers
RemoveOldFiles = remove_old_files
_sentinel = object()

def AppLogConfig(appname, prefs = None, defaultUseStdOut = False, defaultLogLevelName = 'INFO'):
    """Sets up logging for an application.
    
    :param appname: The name of the application.
    :param prefs: A `preferences.Pickled` instance used to serialize the
      logging settings. If None, do not persist them.
    :param defaultUseStdOut: True to log to stdout if the setting is not
      in prefs.
    :param defaultLogLevelName: Default value if the log level name is not
      in prefs.
    :raise AssertionError: If called more than once in any process
      (should be used like `logging.basicConfig`.
    """
    if getattr(AppLogConfig, '__called', False):
        raise AssertionError('Should only be called once!')

    def getValue(reg, key):
        if prefs:
            return prefs.GetValue(reg, key, _sentinel)
        return _sentinel

    useStdOut = getValue('logging', 'usestdout')
    if useStdOut == _sentinel:
        useStdOut = defaultUseStdOut
        if prefs:
            prefs.SetValue('logging', 'usestdout', useStdOut)
    if useStdOut:
        sh = logging.StreamHandler()
        sh.setFormatter(Fmt.FMT_LM)
        logging.root.addHandler(sh)
    loglevelname = getValue('logging', 'loglevelname')
    if loglevelname == _sentinel:
        loglevelname = defaultLogLevelName
        if prefs:
            prefs.SetValue('logging', 'loglevelname', loglevelname)
    loglevel = getattr(logging, loglevelname)
    logging.root.setLevel(loglevel)
    logfilename = GetTimestampedFilename2(appname)
    fh = logging.FileHandler(logfilename)
    fh.setFormatter(Fmt.FMT_NTLM)
    logging.root.addHandler(fh)
    AppLogConfig.__called = True


LineWrap = wrap_line
