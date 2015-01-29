#Embedded file name: carbon/common/script/util\logUtil.py
"""
Written By: Paul Gilmore (Swiped most of this code from service.py)
Date: July 2008

Definition of the logMixin class, and global log functions.

My hope is that if I define it here, as generic and clean as possible,
we don't end up with 2 dozen hard coded versions of these functions everywhere.

On the other hand, I make no claim on the ugly copy pasting in this file, I just moved it from service to here.
I'm trying to clean up the interface to the logging, not the internal workings of the logging.
I did try to clean it up a little, but I don't understand all of what's happening,
so I only touched stuff that I know how it works.
"""
import logging
import logmodule
import sys
from stdlogutils import LineWrap
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def supersafestr(o):
    """Super-safe strx for logging.
    With the removal of Nasty, we've ended up with unexpected items coming
    from modules (builtins, etc) that weren't exposed before,
    causing errors when logging.
    """
    try:
        return strx(o)
    except Exception as ex:
        default = '<UNFORMATABLE>'
        logger.exception('Error formatting an argument to strx2. Obviously it cannot be printed but you should be able to figure it out from the stacktrace. Returning %s', default)
        return default


class LogMixin():
    """
        Logging utility mixin class.
        This class is a mixin which adds self.LogError, self.LogInfo, etc to a class quickly and easilly.
    """

    def __init__(self, logChannel = None, bindObject = None):
        """
            Parameters:
                - logChannelName should be a string, which is usually (but not always)
                the guid of the service/object that is deriving from the mixin.
                - bindObject is an object which already has a logserver channel defined
                If provided this object will link it's logserver calls to the same channel as the other object.
                (This functionality seemed to be a hack in some places, but in others I am fairly certain it was deliberate)
            Parameter Restrictions:
                - logChannelName should be a string or None.  No other types accepted.
                - bindObject should be an object which has the member variable (__guid__ or __logname__) defined.
                - You can ONLY provide one or the other.  If you provide both, an exception will be thrown.
                    You shouldn't be trying to log to two channels at once, each of these parameters are
                    meant for deciding which channel to log on.  Providing two separate channels is a conflict.
        """
        logChannelName = self.GetLogChannelName(logChannel, bindObject)
        self.__logname__ = self.GetLogName(logChannelName)
        self.logChannel = logmodule.GetChannel(logChannelName)
        self.LoadPrefs()
        self.logContexts = {}
        for each in ('Info', 'Notice', 'Warn', 'Error'):
            self.logContexts[each] = 'Logging::' + each

    def GetLogChannelName(self, logChannelName = None, bindObject = None):
        """ This function determines the logChannel.
        The logChannel is either the given logChannel parameter, the bindObject guid, or the self guid.
        If all of those are None, it returns "nonsvc.General" """
        if type(logChannelName) not in [str, type(None)]:
            raise Exception('logChannelName must be a string!')
        if logChannelName and bindObject:
            raise Exception('Conflicting log channel, provide logChannelName or bindObject, not both')
        bindguid = getattr(bindObject, '__guid__', None)
        bindLogName = getattr(bindObject, '__logname__', None)
        selfguid = getattr(self, '__guid__', None)
        return logChannelName or bindguid or bindLogName or selfguid or 'nonsvc.General'

    def GetLogName(self, logChannelName):
        """ logChannelName parameter is the string result of self.GetLogChannel """
        tokens = logChannelName.split('.')
        if len(tokens) == 1:
            return tokens[0]
        else:
            return tokens[1]

    def ArrangeArguments(self, *args, **keywords):
        """ Take the given arguements and arrange them into a single list. """
        self.DeprecateKeywords(**keywords)
        argsList = []
        prefix = self.GetLogPrefix()
        if prefix:
            argsList.append(prefix)
        for item in args:
            argsList.append(item)

        return argsList

    def DeprecateKeywords(self, **keywords):
        """
            Keyword arguements in Log functions are ignored
            It seems silly to accept them if we're not doing anything with them.
            On the other hand, my current goal is not to change functionality.
        
            Compromise:
            Print a traceback whenever somebody uses keyword arguements in a log function.
            Continue ignoring them.
            In the future, remove **keywords functionality entirely from this file (and subsequently all logging functions)
        
            For now, if you find this traceback, go to the log function that called it, and REMOVE the keyworded arguements
            passed into the log function, because they're being ignored anyway.
        """
        if len(keywords):
            self.LogError('ERROR: keyword arguements passed into a log function')
            logmodule.LogTraceback()

    def GetLogPrefix(self):
        """
            This function is meant to be overridden by children classes
            which wish to prefix a tag to the begining of every logmodule.
            - To use
                - create a function of this name in your subclass
                - return the appropriate string prefix.
        """
        return None

    def DudLogger(self, *args, **keywords):
        """ Used to block a channel. """
        pass

    def ShouldLogMethodCalls(self):
        if not getattr(self, 'isLogInfo', 0):
            return False
        if not prefs.GetValue('logMethodCalls', boot.role != 'client'):
            return False
        return self.logChannel.IsLogChannelOpen(logmodule.LGINFO)

    def LogMethodCall(self, *args, **keywords):
        """
        Add the prefix, and the keywords (previously only handled args).
        Logs out to the INFO severity onto the [branch].[nodeType]::MethodCalls channel.
        For performance reasons, this assumes that method-call logging has been enabled. The caller is responsible
        for not calling this function in the first place if logging should be disabled.
        """
        argsList = self.ArrangeArguments(*args, **keywords)
        logChannel = logmodule.methodcalls
        try:
            if len(argsList) == 1:
                s = supersafestr(argsList[0])
            else:
                s = ' '.join(map(supersafestr, argsList))
            logChannel.Log(s, logmodule.LGINFO, 1, force=True)
        except TypeError:
            logChannel.Log('[X]'.join(map(supersafestr, argsList)).replace('\x00', '\\0'), logmodule.LGINFO, 1, force=True)
            sys.exc_clear()
        except UnicodeEncodeError:
            logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList))), logmodule.LGINFO, 1, force=True)
            sys.exc_clear()

    def LogInfo(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if getattr(self, 'isLogInfo', 0) and self.logChannel.IsLogChannelOpen(logmodule.LGINFO):
            try:
                if len(argsList) == 1:
                    s = supersafestr(argsList[0])
                else:
                    s = ' '.join(map(supersafestr, argsList))
                self.logChannel.Log(s, logmodule.LGINFO, 1, force=True)
            except TypeError:
                self.logChannel.Log('[X]'.join(map(supersafestr, argsList)).replace('\x00', '\\0'), logmodule.LGINFO, 1, force=True)
                sys.exc_clear()
            except UnicodeEncodeError:
                self.logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList))), logmodule.LGINFO, 1, force=True)
                sys.exc_clear()

    def LogWarn(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if self.isLogWarning and self.logChannel.IsLogChannelOpen(logmodule.LGWARN) or charsession and not boot.role == 'client':
            try:
                if len(argsList) == 1:
                    s = supersafestr(argsList[0])
                else:
                    s = ' '.join(map(supersafestr, argsList))
                if self.logChannel.IsOpen(logmodule.LGWARN):
                    self.logChannel.Log(s, logmodule.LGWARN, 1, force=True)
                for x in LineWrap(s, 10):
                    if charsession and not boot.role == 'client':
                        charsession.LogSessionHistory(x, None, 1)

            except TypeError:
                sys.exc_clear()
                x = '[X]'.join(map(supersafestr, argsList)).replace('\x00', '\\0')
                if self.logChannel.IsOpen(logmodule.LGWARN):
                    self.logChannel.Log(x, logmodule.LGWARN, 1, force=True)
                if charsession and not boot.role == 'client':
                    charsession.LogSessionHistory(x, None, 1)
            except UnicodeEncodeError:
                sys.exc_clear()
                x = '[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList)))
                if self.logChannel.IsOpen(logmodule.LGWARN):
                    self.logChannel.Log(x, logmodule.LGWARN, 1, force=True)
                if charsession and not boot.role == 'client':
                    charsession.LogSessionHistory(x, None, 1)

    def LogError(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if self.logChannel.IsOpen(logmodule.LGERR) or charsession:
            try:
                if len(argsList) == 1:
                    s = supersafestr(argsList[0])
                else:
                    s = ' '.join(map(supersafestr, argsList))
                if self.logChannel.IsOpen(logmodule.LGERR):
                    self.logChannel.Log(s, logmodule.LGERR, 1)
                for x in LineWrap(s, 40):
                    if charsession:
                        charsession.LogSessionHistory(x, None, 1)

            except TypeError:
                sys.exc_clear()
                x = '[X]'.join(map(supersafestr, argsList)).replace('\x00', '\\0')
                if self.logChannel.IsOpen(logmodule.LGERR):
                    self.logChannel.Log(x, logmodule.LGERR, 1)
                if charsession:
                    charsession.LogSessionHistory(x, None, 1)
            except UnicodeEncodeError:
                sys.exc_clear()
                x = '[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList)))
                if self.logChannel.IsOpen(logmodule.LGERR):
                    self.logChannel.Log(x, logmodule.LGERR, 1)
                if charsession and not boot.role == 'client':
                    charsession.LogSessionHistory(x, None, 1)

    def LogNotice(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if getattr(self, 'isLogInfo', 0) and self.logChannel.IsLogChannelOpen(logmodule.LGNOTICE):
            try:
                if len(argsList) == 1:
                    s = supersafestr(argsList[0])
                else:
                    s = ' '.join(map(supersafestr, argsList))
                self.logChannel.Log(s, logmodule.LGNOTICE, 1, force=True)
            except TypeError:
                self.logChannel.Log('[X]'.join(map(supersafestr, argsList)).replace('\x00', '\\0'), logmodule.LGNOTICE, 1, force=True)
                sys.exc_clear()
            except UnicodeEncodeError:
                self.logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList))), logmodule.LGNOTICE, 1, force=True)
                sys.exc_clear()

    def LoadPrefs(self):
        """ This was pulled over from the service version.
            Not sure what it is for, and I've never seen them turned off.
        """
        self.isLogInfo = bool(prefs.GetValue('logInfo', 1))
        self.isLogWarning = bool(prefs.GetValue('logWarning', 1))
        self.isLogNotice = bool(prefs.GetValue('logNotice', 1))

    def SetLogInfo(self, b):
        if not b and self.isLogInfo:
            self.LogInfo('*** LogInfo stopped for ', self.__guid__)
        old = self.isLogInfo
        self.isLogInfo = b
        if b and not old:
            self.LogInfo('*** LogInfo started for ', self.__guid__)

    def SetLogNotice(self, b):
        if not b and self.isLogNotice:
            self.LogInfo('*** LogNotice stopped for ', self.__guid__)
        old = self.isLogNotice
        self.isLogNotice = b
        if b and not old:
            self.LogInfo('*** LogNotice started for ', self.__guid__)

    def SetLogWarning(self, b):
        if not b and self.isLogWarning:
            self.LogWarn('*** LogWarn stopped for ', self.__guid__)
        old = self.isLogWarning
        self.isLogWarning = b
        if b and not old:
            self.LogWarn('*** LogWarn started for ', self.__guid__)


def _Log(severity, what):
    try:
        s = ' '.join(map(str, what))
    except UnicodeEncodeError:

        def conv(what):
            if isinstance(what, unicode):
                return what.encode('ascii', 'replace')
            return str(what)

        s = ' '.join(map(conv, what))

    logmodule.general.Log(s.replace('\x00', '\\0'), severity)


def LogInfo(*what):
    _Log(logmodule.LGINFO, what)


def LogNotice(*what):
    _Log(logmodule.LGNOTICE, what)


def LogWarn(*what):
    _Log(logmodule.LGWARN, what)


def LogError(*what):
    _Log(logmodule.LGERR, what)


LogException = logmodule.LogException
import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('log', locals())
