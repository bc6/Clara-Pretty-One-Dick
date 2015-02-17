#Embedded file name: bluepy\__init__.py
import atexit
import blue
import re
import stackless
import sys
import traceback
import weakref
import cStringIO
import utillib as util
import ccpProfile
tasklet_id = 0

class TaskletExt(stackless.tasklet):
    __slots__ = ['context',
     'localStorage',
     'storedContext',
     'startTime',
     'endTime',
     'runTime',
     'tasklet_id']

    @staticmethod
    def GetWrapper(method):
        if not callable(method):
            raise TypeError('TaskletExt::__new__ argument "method" must be callable.')

        def CallWrapper(*args, **kwds):
            current = stackless.getcurrent()
            current.startTime = blue.os.GetWallclockTimeNow()
            oldtimer = PushTimer(current.context)
            exc = None
            try:
                try:
                    return method(*args, **kwds)
                except TaskletExit as e:
                    import logmodule as log
                    t = stackless.getcurrent()
                    log.general.Log('tasklet (%s) %s exiting with %r' % (t.tasklet_id, t, e), log.LGINFO)
                except SystemExit as e:
                    import logmodule as log
                    log.general.Log('system %s exiting with %r' % (stackless.getcurrent(), e), log.LGINFO)
                except Exception:
                    import logmodule as log
                    print >> debugFile, 'Unhandled exception in tasklet', repr(stackless.getcurrent())
                    traceback.print_exc(file=debugFile)
                    exc = sys.exc_info()
                    log.LogException('Unhandled exception in %r' % stackless.getcurrent())

                return
            except:
                traceback.print_exc()
                traceback.print_exc(file=debugFile)
                if exc:
                    traceback.print_exception(exc[0], exc[1], exc[2])
                    traceback.print_exception(exc[0], exc[1], exc[2], file=debugFile)
            finally:
                exc = None
                PopTimer(oldtimer)
                current.endTime = blue.os.GetWallclockTimeNow()

        return CallWrapper

    def __new__(self, ctx, method = None):
        global tasklet_id
        tid = tasklet_id
        tasklet_id += 1
        self.tasklet_id = tid
        if method:
            t = stackless.tasklet.__new__(self, self.GetWrapper(method))
        else:
            t = stackless.tasklet.__new__(self)
        c = stackless.getcurrent()
        ls = getattr(c, 'localStorage', None)
        if ls is None:
            t.localStorage = {}
        else:
            t.localStorage = dict(ls)
        t.storedContext = t.context = ctx
        t.runTime = 0.0
        tasklets[t] = True
        return t

    def bind(self, callableObject):
        return stackless.tasklet.bind(self, self.CallWrapper(callableObject))

    def __repr__(self):
        abps = [ getattr(self, attr) for attr in ['alive',
         'blocked',
         'paused',
         'scheduled'] ]
        abps = ''.join((str(int(flag)) for flag in abps))
        return '<TaskletExt object at %x, abps=%s, ctxt=%r>' % (id(self), abps, getattr(self, 'storedContext', None))

    def __reduce__(self):
        """we don't support pickling of tasklets.  Intead, just return a special repr of it, so that
        they can be marshaled over for debugging purposes
        """
        return (str, ("__reduce__()'d " + repr(self),))

    def PushTimer(self, ctxt):
        blue.pyos.taskletTimer.EnterTasklet(ctxt)

    def PopTimer(self, ctxt):
        blue.pyos.taskletTimer.ReturnFromTasklet(ctxt)

    def GetCurrent(self):
        blue.pyos.taskletTimer.GetCurrent()

    def GetWallclockTime(self):
        """Return the wallclock time in seconds since this tasklet was started"""
        return (blue.os.GetWallclockTimeNow() - self.startTime) * 1e-07

    def GetRunTime(self):
        """Return the accumulated run time in seconds of this tasklet"""
        return self.runTime + blue.pyos.GetTimeSinceSwitch()


tasklets = weakref.WeakKeyDictionary()
ctxtfilter = re.compile('at 0x[0-9A-F]+')

def CreateTaskletExt(func, *args, **kw):
    ctx = ctxtfilter.sub('at (snip)', repr(func))
    ctx = blue.pyos.taskletTimer.GetCurrent().split('^')[-1] + '^' + ctx
    t = TaskletExt(ctx, func)
    t(*args, **kw)
    return t


def Shutdown(exitprocs):

    def RunAll():
        stackless.getcurrent().block_trap = True
        for proc in exitprocs:
            try:
                proc()
            except Exception:
                import logmodule as log
                log.LogException('exitproc ' + repr(proc), toAlertSvc=False)
                sys.exc_clear()

    if exitprocs:
        TaskletExt('Shutdown', RunAll)()
        intr = stackless.run(1000000)
        if intr:
            log.general.Log('ExitProcs interrupted at tasklet ' + repr(intr), log.LGERR)
    GetTaskletDump(True)
    if len(tasklets):
        KillTasklets()
        GetTaskletDump(True)


def GetTaskletDump(logIt = True):
    import logmodule as log
    lines = []
    lines.append('GetTaskletDump:  %s TaskletExt objects alive' % len(tasklets))
    lines.append('[context] - [code] - [stack depth] - [creation context]')
    for t in tasklets.keys():
        try:
            if t.frame:
                stack = traceback.extract_stack(t.frame, 1)
                depth = len(stack)
                f = stack[-1]
                code = '%s(%s)' % (f[0], f[1])
            else:
                code, depth = ('<no frame>', 0)
        except Exception as e:
            code, depth = repr(e), 0

        ctx = (getattr(t, 'context', '(unknown)'),)
        sctx = getattr(t, 'storedContext', '(unknown)')
        l = '%s - %s - %s - %s' % (sctx,
         code,
         depth,
         ctx)
        lines.append(l)

    lines.append('End TaskletDump')
    if logIt:
        for l in lines:
            log.general.Log(l, log.LGINFO)

    return '\n'.join(lines) + '\n'


def KillTasklets():
    t = TaskletExt('KillTasklets', KillTasklets_)
    t()
    t.run()


def KillTasklets_():
    import logmodule as log
    log.general.Log('killing all %s TaskletExt objects' % len(tasklets), log.LGINFO)
    for i in range(3):
        for t in tasklets.keys():
            if t is stackless.getcurrent():
                continue
            try:
                if t.frame:
                    log.general.Log('killing %s' % t, log.LGINFO)
                    t.kill()
                else:
                    log.general.Log('ignoring %r, no frame.' % t, log.LGINFO)
            except RuntimeError as e:
                log.general.Log("couldn't kill %r: %r" % (t, e), log.LGWARN)

    log.general.Log('killing done', log.LGINFO)


class DebugFile(object):
    """A simple file like object for writing to the Debug stream"""

    def __init__(self):
        import blue
        self.ODS = blue.win32.OutputDebugString

    def close(self):
        pass

    def flush(self):
        pass

    def write(self, str):
        self.ODS(str)

    def writelines(self, lines):
        for l in lines:
            self.ODS(l)


debugFile = DebugFile()

class PyResFile(object):
    """constructs file objects that can read from the 'res' paths"""
    __slots__ = ['rf',
     'name',
     'mode',
     'softspace']

    def __init__(self, path, mode = 'r', bufsize = -1):
        self.rf = blue.ResFile()
        self.mode = mode
        self.name = path
        if 'w' in mode:
            try:
                self.rf.Create(path)
            except:
                raise IOError, 'could not create ' + path

        else:
            readonly = 'a' not in mode and '+' not in mode
            try:
                self.rf.OpenAlways(path, readonly, mode)
            except:
                raise IOError, 'could not open ' + path

    def read(self, count = 0):
        try:
            return self.rf.read(count)
        except:
            raise IOError, 'could not read %d bytes from %s' % (count, self.rf.filename)

    def write(self, data):
        raise NotImplemented

    def readline(self, size = 0):
        raise NotImplemented

    def readlines(self, sizehint = 0):
        r = []
        while True:
            l = self.readline()
            if not l:
                return r
            r.append(l)

    def writelines(self, iterable):
        for i in iterable:
            self.write(i)

    def seek(self, where, whence = 0):
        if whence == 1:
            where += self.rf.pos
        elif whence == 2:
            where += self.rf.size
        try:
            self.rf.Seek(where)
        except:
            raise IOError, 'could not seek to pos %d in %s' % (where, self.rf.filename)

    def tell(self):
        return self.rf.pos

    def truncate(self, size = None):
        if size is None:
            size = self.rf.pos
        try:
            self.rf.SetSize(size)
        except:
            raise IOError, 'could not trucated file %s to %d bytes' % (self.rf.filename, size)

    def flush():
        pass

    def isatty():
        return False

    def close(self):
        self.rf.close()
        del self.rf

    def next(self):
        l = self.readline()
        if l:
            return l
        raise StopIteration

    def __iter__(self):
        return self


PushTimer = ccpProfile.PushTimer
PopTimer = ccpProfile.PopTimer
CurrentTimer = ccpProfile.CurrentTimer
EnterTasklet = ccpProfile.EnterTasklet
ReturnFromTasklet = ccpProfile.ReturnFromTasklet
Timer = ccpProfile.Timer
TimerPush = ccpProfile.TimerPush
TimedFunction = ccpProfile.TimedFunction
blue.TaskletExt = TaskletExt
blue.tasklets = tasklets
stackless.taskletext = TaskletExt

def GetBlueInfo(numMinutes = None, isYield = True):
    if numMinutes:
        trend = blue.pyos.cpuUsage[-numMinutes * 60 / 10:]
    else:
        trend = blue.pyos.cpuUsage[:]
    mega = 1.0 / 1024.0 / 1024.0
    ret = util.KeyVal()
    ret.memData = []
    ret.pymemData = []
    ret.bluememData = []
    ret.othermemData = []
    ret.threadCpuData = []
    ret.procCpuData = []
    ret.threadKerData = []
    ret.procKerData = []
    ret.timeData = []
    ret.latenessData = []
    ret.schedData = []
    latenessBase = 100000000.0
    if len(trend) >= 1:
        ret.actualmin = int((trend[-1][0] - trend[0][0]) / 10000000.0 / 60.0)
        t1 = trend[0][0]
    benice = blue.pyos.BeNice
    mem = 0
    for t, cpu, mem, sched in trend:
        if isYield:
            benice()
        elap = t - t1
        t1 = t
        p_elap = 100.0 / elap if elap else 0.0
        mem, pymem, workingset, pagefaults, bluemem = mem
        ret.memData.append(mem * mega)
        ret.pymemData.append(pymem * mega)
        ret.bluememData.append(bluemem * mega)
        othermem = (mem - pymem - bluemem) * mega
        if othermem < 0:
            othermem = 0
        ret.othermemData.append(othermem)
        thread_u, proc_u = cpu[:2]
        thread_k, proc_k = cpu[2:4] if len(cpu) >= 4 else (0, 0)
        thread_cpupct = thread_u * p_elap
        proc_cpupct = proc_u * p_elap
        thread_kerpct = thread_k * p_elap
        proc_kerpct = proc_k * p_elap
        ret.threadCpuData.append(thread_cpupct)
        ret.procCpuData.append(proc_cpupct)
        ret.threadKerData.append(thread_kerpct)
        ret.procKerData.append(proc_kerpct)
        ret.schedData.append(sched)
        ret.timeData.append(t)
        late = 0.0
        if elap:
            late = (elap - latenessBase) / latenessBase * 100
        ret.latenessData.append(late)

    ret.proc_cpupct = proc_cpupct
    ret.mem = mem
    return ret


def Terminate(reason = ''):
    """Calls some cleanup functions and then blue.os.Terminate.
    
    Calls sm.ChainEvent('ProcessShutdown') and then the
    atexit exit handlers.
    """
    import logmodule as log
    log.general.Log('bluepy.Terminate - Reason: %s' % reason, log.LGNOTICE)
    try:
        if 'sm' in __builtins__:
            sm.ChainEvent('ProcessShutdown')
    except:
        log.LogException()

    atexit._run_exitfuncs()
    blue.os.Terminate(0)


def pythonstatus():
    """
    Log out the state of the program at this time. Note that this gets called on
    a background thread so we minimize file operations to try to hang on to the
    GIL for the duration of this function. The background thread may otherwise
    time out.
    """
    file = cStringIO.StringIO()
    file.write('Tasklets\n')
    file.write('========\n')
    for t in tasklets.keys():
        if not t.alive:
            continue
        id = t.tasklet_id
        ctx = (getattr(t, 'context', '(unknown)'),)
        file.write('Tasklet ID: %d %s\n' % (id, ctx))
        file.write('%s\n' % repr(t))
        traceback.print_stack(t.frame, file=file)
        file.write('\n')

    file.write('\n')
    file.write('Threads\n')
    file.write('=======\n')
    for id, frame in sys._current_frames().iteritems():
        file.write('Thread ID: %d\n' % id)
        traceback.print_stack(frame, file=file)

    path = blue.paths.ResolvePathForWriting('cache:/pythonstatus.txt')
    with open(path, 'w+b') as f:
        f.write(file.getvalue())
    return path
