#Embedded file name: builtinmangler.py
"""
Contains most of the builtin mangling code for EVE.
This used to be in Nasty, or happen as a side effect during the imports
that'd happen during Nasty's precompilation step.
Since we don't precompile all code anymore,
we need to actually mangle builtins deliberately
(as much as possible).

Some things will mangle their own builtins but this should be avoided.

(Also maybe the most accurate technical term isn't 'mangle'
but it is certainly the most accurate emotional term).

MangleBuiltins is only effective the first time it's called.
"""
import __builtin__
import inspect
import logging
import sys
import stateholder
import stringutil
L = logging.getLogger(__name__)
L.addHandler(logging.NullHandler())
strx = stringutil.strx

class NamespaceFailedException(ImportError):

    def __init__(self, *args):
        ImportError.__init__(self, *args)

    def __repr__(self):
        return 'NamespaceFailed: The namespace ' + self.args[0] + ' was not found.'


def CreateInstance(cid, arguments = ()):
    """For blue to python marriage"""
    try:
        namespace, name = cid.split('.')
    except Exception as e:
        print e
        raise RuntimeError('InvalidClassID', cid)

    try:
        ns = __import__(namespace).__dict__
    except:
        raise NamespaceFailedException, namespace

    try:
        constructor = ns[name]
    except:
        raise AttributeError, 'namespace %s has no member %s' % (namespace, name)

    ret = apply(constructor, arguments)
    if hasattr(ret, '__persistvars__'):
        for each in ret.__persistvars__:
            if not hasattr(ret, each):
                setattr(ret, each, None)

    if hasattr(ret, '__nonpersistvars__'):
        for each in ret.__nonpersistvars__:
            if not hasattr(ret, each):
                setattr(ret, each, None)

    return ret


def _SmashConst(constmodule):
    """Code from nasty that smashes the guts of a const module into the
    module's object so it can be accessed in an 'expected' way.
    Puts `constmodule` as the builtin 'const' and the module 'const'.
    
    By the way, ALL of the guts of a module are exposed,
    so you can actually get a lot of blue's internal's from const.
    DERP!
    """
    __builtin__.const = constmodule
    sys.modules['const'] = constmodule
    for name, value in constmodule.__dict__.iteritems():
        if not name.startswith('__'):
            if name not in __builtin__.const.__dict__:
                __builtin__.const.__dict__[name] = value
            elif inspect.ismodule(value):
                for moduleKey, moduleValue in value.__dict__.iteritems():
                    if not moduleKey.startswith('__'):
                        setattr(__builtin__.const.__dict__[name], moduleKey, moduleValue)


def SmashNastyspaceBuiltinConflicts():
    """Smashes the nastyspace modules that conflict with builtins
    into their builtins home."""

    def trysmash(purename):
        xname = purename + '_extra'
        try:
            extras = __import__(xname)
        except ImportError:
            L.warn('Could not import %s to smash into %s', xname, purename)
            return

        pure = __import__(purename)
        for name, value in extras.__dict__.iteritems():
            setattr(pure, name, value)

        L.info('Smashed %s into %s', xname, purename)

    trysmash('sys')
    trysmash('exceptions')


def MangleBuiltins():
    if hasattr(stateholder, '_constsmangled'):
        return
    import eveexceptions
    __builtin__.UserError = eveexceptions.UserError
    __builtin__.SQLError = eveexceptions.SQLError
    __builtin__.ConnectionError = eveexceptions.ConnectionError
    __builtin__.UnmarshalError = eveexceptions.UnmarshalError
    __builtin__.RoleNotAssignedError = eveexceptions.RoleNotAssignedError
    __builtin__.CreateInstance = CreateInstance
    __builtin__.strx = stringutil.strx
    import eve.common.lib.appConst as appConst
    _SmashConst(appConst)
    __builtin__.SEC = const.SEC
    __builtin__.MIN = const.MIN
    __builtin__.HOUR = const.HOUR
    __builtin__.DAY = const.DAY
    __builtin__.WEEK = const.WEEK
    __builtin__.MONTH = const.MONTH30
    __builtin__.YEAR = const.YEAR360
    __builtin__.DATE = const.UE_DATE
    __builtin__.TIME = const.UE_TIME
    __builtin__.OWNERID = const.UE_OWNERID
    __builtin__.LOCID = const.UE_LOCID
    __builtin__.TYPEID = const.UE_TYPEID
    __builtin__.GROUPID = const.UE_GROUPID
    __builtin__.CATID = const.UE_CATID
    __builtin__.DIST = const.UE_DIST
    __builtin__.ISK = const.UE_ISK
    __builtin__.AUR = const.UE_AUR
    stateholder._constsmangled = True


def CreateInstance(guid, arguments = ()):
    """Nastyless-implementation of CreateInstance.
    
    DO NOT USE THIS FOR NEW CODE. It is only provided for legacy purposes.
    If you need to dynamically create instances of things,
    do it some other way.
    """
    try:
        namespace, typename = guid.split('.')
    except:
        raise RuntimeError("InvalidClassID (%s), should be like 'ns.Class'" % stringutil.strx(guid))

    module = __import__(namespace)
    ctor = getattr(module, typename)
    ret = ctor(*arguments)
    for each in getattr(ret, '__persistvars__', []):
        if not hasattr(ret, each):
            setattr(ret, each, None)

    for each in getattr(ret, '__nonpersistvars__', []):
        if not hasattr(ret, each):
            setattr(ret, each, None)

    return ret
