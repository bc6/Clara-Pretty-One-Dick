#Embedded file name: carbon/client/script/util\debug.py
"""
Stuff that is meant to be used during development, not in checked-in code.
"""
import pstats
import sys
import types
import log
import cProfile
from functools import wraps
import utillib as util

def Trace(fn):
    """      
    Decorate a function or method so it logs when it is called and returns.
    
    To see the output of the function you need to set logDbgTrace=1 in your 
    preferences.
    
    This logs out:
       - whether the function is beginning or ending;
       - the name of the current char (useful when debugging interactions);
       - the __guid__ of the object where the method lives, if any;
       - the name of the function;
       - a representation of the called values; and
       - the return value, when the function ends.
       
    Example output:
    (Note that the one in the middle is an arbitrary log which happened inside 
     the function).
    
       2006.11.06 13:50:17:640  BEGIN Duna: svc.map.OnStartTalk(150203683)
       2006.11.06 13:50:17:644  Now I would do something to Duna
       2006.11.06 13:50:17:645  END Duna: svc.map.OnStartTalk(150203683) -> None
    """

    @wraps(fn)
    def deco(*args, **kw):
        no_ret = []

        def logStuff(beginOrEnd, ret = no_ret):
            if not settings.generic.Get('logDbgTrace', False):
                return
            if args and hasattr(args[0], '__guid__'):
                meth = '.'.join((args[0].__guid__, fn.func_name))
                rest = args[1:]
            else:
                meth = fn.func_name
                rest = args
            spos = map(Prettify, rest)
            skw = [ '%s=%s' % (name, Prettify(val)) for name, val in kw.iteritems() ]
            sargs = ', '.join(spos + skw)
            if ret is no_ret:
                sret = ''
            else:
                sret = ' -> %s' % Prettify(ret)
            import dbg
            me = dbg.GetCharacterName()
            what = (beginOrEnd, me + ':', '%s(%s)%s' % (meth, sargs, sret))
            log.methodcalls.Log(' '.join(map(unicode, what)), log.LGNOTICE)

        logStuff('BEGIN')
        ret = fn(*args, **kw)
        logStuff('END', ret)
        return ret

    return deco


def TraceAll(locals, ignore = ()):
    for name, val in locals.items():
        if name not in ignore and callable(val):
            locals[name] = Trace(val)


def Prettify(o):
    if isinstance(o, util.KeyVal) and getattr(o, 'charID', None) is not None:
        import dbg
        name = dbg.GetCharacterName(o)
        return name
    elif hasattr(o, 'name') and hasattr(o, '__guid__'):
        return '%s (%s)' % (o.name, o.__guid__)
    else:
        return str(o)


def ImportHack(name):
    """
    Debug: module to export stuff to inspect in Jennifer's command line.
    """
    return sys.modules.setdefault(name, types.ModuleType(name))


def TraceLocals(locals, *varnames):
    """
    Log out the given varnames along with their value in the locals 
    environment, preceded with header.
    
    Logs are sent to the methodcalls channel.
    """

    def Eval(expr):
        try:
            return eval(expr, {}, locals)
        except:
            excType, exc = sys.exc_info()[:2]
            return '<exception: %s%s>' % (excType.__name__, exc.args)

    log.methodcalls.Log(' '.join(map(unicode, [ '%s=%r' % (name, Eval(name)) for name in varnames ])), log.LGNOTICE)


def WithLogStdout(f):
    """
    Decorate f so whatever it prints goes to the the methodcalls channel as LGNOTICE.
    """
    if not hasattr(WithLogStdout, 'logStream'):
        WithLogStdout.logStream = log.LogChannelStream(log.methodcalls, log.LGNOTICE)

    @wraps(f)
    def deco(*args, **kw):
        old = sys.stdout
        sys.stdout = WithLogStdout.logStream
        try:
            return f(*args, **kw)
        finally:
            sys.stdout = old

    return deco


@WithLogStdout
def Profile(fn, *args, **kw):
    """
    Call fn(*args, **kw) under the profiler, log out profile stats, return the
    return value of the call.
    
    Profile stats are logged out to the methodcalls channel
    does.
    """
    print 'Profile BEGIN -----------------------------------'
    p = cProfile.Profile()
    ret = p.runcall(fn, *args, **kw)
    pstats.Stats(p).sort_stats('time', 'cumulative').print_stats()
    print 'Profile END -------------------------------------'
    return ret


def Profiled(fn):
    """
    Return fn decorated so it gets profiled whenever it's called.
    """

    @wraps(fn)
    def deco(*args, **kw):
        return Profile(fn, *args, **kw)

    return deco


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('dbg', locals())
