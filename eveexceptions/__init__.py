#Embedded file name: eveexceptions\__init__.py
"""Exception classes that are original CCP products."""
import __builtin__
import types
if not hasattr(__builtin__, 'strx'):
    strx = str

class UserError(StandardError):
    """User information"""
    __guid__ = 'exceptions.UserError'
    __persistvars__ = ['args', 'dict', 'msg']

    def __init__(self, msg = None, *args):
        if getattr(msg, '__class__', None) == UserError:
            self.msg = msg.msg
            self.dict = msg.dict
            self.args = (self.msg, self.dict)
            return
        if type(msg) not in [types.StringType, types.UnicodeType, types.NoneType]:
            raise RuntimeError('Invalid argument, msg must be a string', msg)
        self.msg = msg
        if len(args) and type(args[0]) == type({}):
            self.dict = args[0]
            self.args = (self.msg, self.dict)
        else:
            self.dict = None
            self.args = (self.msg,) + args

    def __str__(self):
        return 'User error, msg=%s, dict=%s' % (strx(self.msg), strx(self.dict))


class SQLError(RuntimeError):
    __guid__ = 'exceptions.SQLError'

    def __init__(self, *args):
        RuntimeError.__init__(self, *args)
        args = args + (None,) * (6 - len(args))
        args = args[:6]
        code, msg, rawErrorRecords, sql, paramErrors, colErrors = args
        self.code = code
        self.msg = msg
        self.colErrors = colErrors
        self.sql = sql
        self.rawErrorRecords = rawErrorRecords
        self.paramErrors = paramErrors
        self.errorRecords = []
        for r in rawErrorRecords or []:
            r = r + (None,) * (8 - len(r))
            self.errorRecords.append((r[1],
             None,
             r[2],
             r[6],
             r[7]))

    def __str__(self):
        return '\nCode:        %r\nMessage:     %r\nErrorRecs:   %r\nSQL:         %r\nParamErrors: %r\nColErrors:   %r' % (self.code,
         self.msg,
         self.rawErrorRecords,
         self.sql,
         self.paramErrors,
         self.colErrors)


class ConnectionError(RuntimeError):
    """
    This exception is thrown from db.dll when it determines (heuristically) that the connection
    to the database has been lost and the databsse session is thrown away.
    """
    __guid__ = 'exceptions.ConnectionError'


class UnmarshalError(StandardError):
    __guid__ = 'exceptions.SQLError'

    def __init__(self, exception = None, value = None, size = 0, pos = 0, crc = 0):
        self.exception = exception
        self.value = value
        self.size = size
        self.pos = pos
        self.crc = crc

    def __str__(self):
        return '\nException:  %s, %s\nPikl size:  %s\nPikl pos.:  %s\nCRC:        %s' % (strx(self.exception),
         strx(self.value),
         strx(self.size),
         strx(self.pos),
         strx(self.crc))


class RoleNotAssignedError(StandardError):
    __guid__ = 'exceptions.RoleNotAssignedError'

    def __init__(self, roles = None):
        self.roles = roles

    def __str__(self):
        return '\nRequired roles: %s' % (strx(self.roles),)


class ServiceNotFound(StandardError):
    __guid__ = 'exceptions.ServiceNotFound'
    __persistvars__ = ['serviceName']

    def __init__(self, serviceName = None):
        self.serviceName = serviceName
        StandardError.__init__(self, serviceName)

    def __repr__(self):
        return 'The service ' + unicode(self.serviceName) + ' was not found.'


class MethodNotCalledFromClient(StandardError):
    __guid__ = 'exception.MethodNotCalledFromClient'
    __persistvars__ = ['methodName']

    def __init__(self, methodName = None):
        self.methodName = methodName
        StandardError.__init__(self, methodName)

    def __repr__(self):
        return 'The method ' + unicode(self.methodName) + ' can be called from the client only.'
