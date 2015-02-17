#Embedded file name: carbon/client/script/util\misc.py
import os
import blue
import telemetry
import stackless
import sys
import types
import uthread
import log
import yaml
import functools

class _ResFileRaw(object):
    """A class that wraps a binary resfile"""
    __slots__ = ['resfile', 'closed']

    def __init__(self, respath):
        self.resfile = blue.ResFile()
        self.resfile.OpenAlways(respath)
        self.closed = False

    def read(self, size = -1):
        if self.closed:
            raise ValueError('file is closed')
        return self.resfile.Read(size)

    def seek(self, offset, whence = 0):
        if whence == 0:
            r = self.resfile.Seek(offset)
        elif whence == 1:
            r = self.resfile.Seek(offset + self.file.pos)
        elif whence == -1:
            r = self.resfile.Seek(self.file.size - offset)
        else:
            raise ValueError("'whence' must be 0, 1 or -1, not %s" % whence)

    def tell(self):
        return self.resfile.pos

    def close(self):
        if not self.closed:
            self.resfile.Close()
        self.closed = True


def ResFile(respath, mode = 'rb', bufsize = -1):
    """
    Open a resfile.  If in text mode, create a stringIO on a translated file 
    instead.    
    
    Default is rb, for backwards compatibility.
    """
    if mode.count('b'):
        return _ResFileRaw(respath)
    else:
        s = _ResFileRaw(respath).read().replace('\r\n', '\n')
        import StringIO
        return StringIO.StringIO(s)


def ResFileToCache(respath):
    """
    Open a resfile and place it in the cache directory(If it is not there 
    already). Returns you the path on disk.
    """
    try:
        filename = respath[respath.rfind('/') + 1:]
        targetName = blue.paths.ResolvePath(u'cache:/Temp/') + filename
        if not os.path.exists(targetName):
            resFile = blue.ResFile()
            resFile.Open(respath)
            rawData = resFile.read()
            resFile.close()
            outImage = file(targetName, 'wb')
            outImage.writelines(rawData)
            outImage.close()
        return targetName
    except:
        sys.exc_clear()
        return ''


def BlueFile(bluefilename, mode = 'r', bufsize = -1):
    """
    Auto function.  Tries regular open of translated name, otherwise resorts to 
    ResFile. 
    
    It has the same default values as "file()", i.e. defaults to text 
    processing.    
    """
    filename = blue.paths.ResolvePath(bluefilename)
    try:
        f = file(filename, mode, bufsize)
    except IOError:
        f = ResFile(bluefilename, mode, bufsize)
        sys.exc_clear()

    return f


def DelTree(path):

    def DelFiles(arg, dirname, fnames):
        for each in fnames:
            tmp = os.path.join(dirname, each)
            if not os.path.isdir(tmp):
                os.remove(tmp)

    os.path.walk(path, DelFiles, None)
    _RemoveDirs(path, 0)


def _RemoveDirs(path, nukebase):
    for each in os.listdir(path):
        _RemoveDirs(os.path.join(path, each), 1)

    if nukebase:
        os.rmdir(path)


def GetAttrs(obj, *names):
    """
    Chained getattr. Returns None if any of the attributes is missing or None.
    """
    for name in names:
        obj = getattr(obj, name, None)
        if obj is None:
            return

    return obj


def HasAttrs(obj, *names):
    """
    Chained hasattr. Returns False if any of ht attributes are missing, otherwise True
    """
    for name in names:
        if not hasattr(obj, name):
            return False
        obj = getattr(obj, name, None)

    return True


def TryDel(dictOrSet, key):
    """
    Try and delete a dictionary key, but don't make much of a fuss about it.
    """
    try:
        if isinstance(dictOrSet, set):
            dictOrSet.remove(key)
        else:
            del dictOrSet[key]
    except KeyError:
        sys.exc_clear()


def SecsFromBlueTimeDelta(t):
    return t / 10000000L


def HoursMinsSecsFromSecs(s):
    s = max(0, s)
    secs = int(s % 60)
    mins = int(s / 60 % 60)
    hours = int(s / 3600)
    return (hours, mins, secs)


def Clamp(val, min_, max_):
    """
    Return the given val, constrained to be not lesser than min_ and not 
    greater than max_.
    """
    return min(max_, max(min_, val))


def Doppleganger(wrap, original):
    """
    Return a function that is just like wrap, but with original's name.
    
    This is useful for debugging.
    """
    return types.FunctionType(wrap.func_code, wrap.func_globals, original.func_name, closure=wrap.func_closure)


def Decorator(f):
    """
    Metadecorator! Return a version of the given decorator which preserves the 
    original function names.
    """

    @functools.wraps(f)
    def deco(inner, *args, **kw):
        return Doppleganger(f(inner, *args, **kw), inner)

    return deco


Decorator = Decorator(Decorator)

def Uthreaded(f, name = None):
    if name is None:
        name = f.__name__

    def deco(*args, **kw):
        uthread.worker(name, lambda : f(*args, **kw))

    return deco


Uthreaded = Decorator(Uthreaded)

def RunOnceMethod(fn):
    runAlreadyName = '_run%s%sAlready' % (fn.__name__, id(fn))

    def deco(self, *args, **kw):
        if not hasattr(self, runAlreadyName):
            setattr(self, runAlreadyName, True)
            fn(self, *args, **kw)

    return deco


class Despammer:
    """
    A wrapper on the given function that ignores too frequent calls.
    
    You can set a delay (in milliseconds) for a coarser granularity.
    """
    ___guid__ = 'util.Despammer'

    def __init__(self, fn, delay = 0):
        self._fn = fn
        self._delay = delay
        self._channel = stackless.channel()
        uthread.worker('Despammed::%s' % self._fn.__name__, self._Receiver)
        self._running = True

    def Send(self, *args, **kw):
        """
        Call the original function, with the exception that if several calls are 
        made before one is completed (with a granularity of ms milliseconds), 
        intermediate calls are ignored.
        
        This function returns immediately; the original function is called in
        another thread.
        """
        if self._running:
            self._channel.send((args, kw))

    Send = Uthreaded(Send)

    def Stop(self):
        """
        Stop the worker thread of this despammer, clear references held.
        """
        if self._running:
            self._running = False
            self._channel.send_exception(self._StopExc)
            del self._channel
            del self._fn

    class _StopExc(Exception):
        pass

    def _Receiver(self):
        ch = self._channel
        while True:
            try:
                args, kw = ch.receive()
                blue.pyos.synchro.SleepWallclock(self._delay)
                while ch.balance != 0:
                    args, kw = ch.receive()

                self._fn(*args, **kw)
            except self._StopExc:
                sys.exc_clear()
                return
            except Exception:
                log.LogException()
                sys.exc_clear()


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', globals())
