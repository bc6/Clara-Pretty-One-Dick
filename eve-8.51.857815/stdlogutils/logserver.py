#Embedded file name: stdlogutils\logserver.py
"""Code for interfacing stdlib logging with CCP
logserver/shared memory logging.

Code of interest are the logging constants
(defined here as the authoritative place, please!)
and `InitLoggingToLogserver` (which uses `LogServerHandler`).
"""
import logging
import stdlogutils
from blue import LogChannel
LGINFO = 1
LGNOTICE = 32
LGWARN = 2
LGERR = 4
LOG_MAXMESSAGE = 252
INDENT_PREFIX = '  '
LEVEL_MAP = {logging.CRITICAL: LGERR,
 logging.ERROR: LGERR,
 logging.WARNING: LGWARN,
 logging.INFO: LGNOTICE,
 logging.DEBUG: LGINFO,
 logging.NOTSET: LGINFO}

def _LogChannelIsOpen(logChannel, flag):
    """`return LogChannel.IsOpen(logChannel, flag)`
    
    LogChannel.IsOpen depends on shared logging memory being available,
    so we need to pull this into a static helper so it can be mocked out
    (blue objects cannot be patched directly).
    """
    return LogChannel.IsOpen(logChannel, flag)


class ChannelWrapper(LogChannel):
    """Wrapper for `LogChannel` that has some additional functionality
    for closing and opening channels through Python.
    
    Use `channelDict` and class methods to modify state on all instances
    (generally this is the only thing you'll do in ExeFile),
    though you can modify individual instances as well,
    for example during testing.
    """
    channelDict = {LGINFO: 1,
     LGNOTICE: 1,
     LGWARN: 1,
     LGERR: 1}

    @classmethod
    def Suppress(cls, logflag):
        """Close individual channels."""
        cls.channelDict[logflag] = 0

    @classmethod
    def Unsuppress(cls, logflag):
        """Open individual channels"""
        cls.channelDict[logflag] = 1

    @classmethod
    def SuppressAllChannels(cls):
        """Close all channels for logging in python."""
        for k in cls.channelDict.keys():
            cls.Suppress(k)

    @classmethod
    def UnsuppressAllChannels(cls):
        """Open all channels for logging in python."""
        for k in cls.channelDict.keys():
            cls.Unsuppress(k)

    @classmethod
    def Initialize(cls, prefs):

        def setif(prefskey, level):
            if prefs.HasKey(prefskey):
                cls.channelDict.update({level: prefs.GetValue(prefskey)})

        setif('logInfo', LGINFO)
        setif('logNotice', LGNOTICE)
        setif('logWarning', LGWARN)
        setif('logError', LGERR)

    def IsOpen(self, logflag):
        return ChannelWrapper.channelDict.get(logflag, 1) and self.IsLogChannelOpen(logflag)

    def IsLogChannelOpen(self, logflag):
        """
        Returns whether the channel itself in the shared memory is open whereas
        `IsOpen` tells us whether that is that case
        *and* python is not suppressing.
        """
        return _LogChannelIsOpen(self, logflag)

    def Log(self, value, flag = LGINFO, backstack = 0, force = False):
        """Log the message"""
        if ChannelWrapper.channelDict.get(flag, 1) or force:
            LogChannel.Log(self, value, flag, backstack)

    def open(self, flag = LGINFO, bufsize = -1):
        """Return a file-like object for logging to.
        
        :rtype: LogChannelStream
        """
        return LogChannelStream(self, flag, bufsize)


class LogChannelStream(object):
    encoding = 'utf8'

    def __init__(self, channel, mode, bufsize = -1):
        self.channel, self.mode, self.bufsize = channel, mode, bufsize
        self.buff = []

    def __del__(self):
        self.close()

    def write(self, text):
        self.buff.append(text)
        if self.bufsize == 1 and '\n' in text:
            self.lineflush()
        elif self.bufsize == 0:
            self.flush()

    def writelines(self, lines):
        for each in lines:
            self.write(each)

    def close(self):
        if self.buff is not None:
            self.flush()
            self.buff = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def flush(self):
        out = ''.join(self.buff)
        self.buff = []
        if out:
            self.outputlines(out)

    def lineflush(self):
        out = ''.join(self.buff)
        lines = out.split('\n')
        self.buff = lines[-1:]
        self.outputlines(lines[:-1])

    def outputlines(self, lines):
        mode = self.mode
        self.channel.Log(lines, mode)


def GetLoggingLevelFromPrefs():
    logLevelPrefsNameToLoggingLevel = {'ERROR': logging.ERROR,
     'WARNING': logging.WARNING,
     'NOTICE': logging.INFO,
     'INFO': logging.DEBUG}
    prefsname = prefs.ini.GetValue('pythonLogLevel', 'INFO')
    level = logLevelPrefsNameToLoggingLevel.get(prefsname, logging.DEBUG)
    return level


class LogServerHandler(logging.Handler):
    """ A handler class which writes logging records to LogServer """

    def __init__(self):
        super(LogServerHandler, self).__init__()
        self.channels = {}

    def _makeChannel(self, record):
        if '.' in record.name:
            channel, object = record.name.split('.', 1)
        else:
            channel, object = record.name, 'General'
        return ChannelWrapper(channel, object)

    def emit(self, record):
        try:
            ch = self.channels.get(record.name)
            if ch is None:
                ch = self._makeChannel(record)
                self.channels[record.name] = ch
            severity = LEVEL_MAP.get(record.levelno, LEVEL_MAP[logging.INFO])
            msg = self.format(record)
            ch.Log(msg, severity)
        except Exception:
            self.handleError(record)


def InitLoggingToLogserver(logLevel):
    """Initializes logging to logserver (adds a `LogServerHandler`
    to the root logger, and sets its level to DEBUG.
    We need to set the root logger to DEBUG so it will output everything,
    like logserver does (filtering done through logserver app).
    
    If called more than once, raise a `RuntimeError`.
    """
    if hasattr(InitLoggingToLogserver, '_hasBeenInit'):
        raise RuntimeError('Already initialized.')
    logserver = LogServerHandler()
    logserver.setFormatter(stdlogutils.Fmt.FMT_EVE)
    logging.root.addHandler(logserver)
    logging.root.setLevel(logLevel)
    InitLoggingToLogserver._hasBeenInit = True
