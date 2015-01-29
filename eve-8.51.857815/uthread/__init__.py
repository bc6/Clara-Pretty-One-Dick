#Embedded file name: uthread\__init__.py
"""Python Microthread Library, version 0.1
Microthreads are useful when you want to program many behaviors
happening simultaneously. Simulations and games often want to model
the simultaneous and independent behavior of many people, many
businesses, many monsters, many physical objects, many spaceships, and
so forth. With microthreads, you can code these behaviors as Python
functions. Microthreads use Stackless Python. For more details, see
http://world.std.com/~wware/uthread.html"""
__version__ = '0.1'
__license__ = 'Python Microthread Library version 0.1\nCopyright (C)2000  Will Ware, Christian Tismer\n\nPermission to use, copy, modify, and distribute this software and its\ndocumentation for any purpose and without fee is hereby granted,\nprovided that the above copyright notice appear in all copies and that\nboth that copyright notice and this permission notice appear in\nsupporting documentation, and that the names of the authors not be\nused in advertising or publicity pertaining to distribution of the\nsoftware without specific, written prior permission.\n\nWILL WARE AND CHRISTIAN TISMER DISCLAIM ALL WARRANTIES WITH REGARD TO\nTHIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND\nFITNESS. IN NO EVENT SHALL WILL WARE OR CHRISTIAN TISMER BE LIABLE FOR\nANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES\nWHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN\nACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT\nOF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.'
import stackless
import sys
import blue
import bluepy
import weakref
import collections
import contextlib
import logmodule as log
import blue.heapq as heapq
import locks
import threading
from stacklesslib.util import atomic
SEC = 10000000L
MIN = 60 * SEC
tasks = []
schedule = stackless.schedule
stackless.globaltrace = True
ctxtfilter = bluepy.ctxtfilter

def new(func, *args, **kw):
    return bluepy.CreateTaskletExt(func, *args, **kw)


class TaskletExtTimeoutable(bluepy.TaskletExt):
    __slots__ = bluepy.TaskletExt.__slots__ + ['doneChannel', 'isTimedOut']


def newJoinable(func, *args, **kw):

    def wrapper(selfTasklet, *args, **kw):
        exce = None
        result = None
        try:
            result = func(*args, **kw)
        except Exception as e:
            exce = sys.exc_info()

        try:
            if not selfTasklet.isTimedOut:
                stackless.channel.send(selfTasklet.doneChannel, (result, exce))
            else:
                log.general.Log("newJoinable timed out on function '" + str(func) + "' with args '" + strx(args)[:2048] + "'", log.LGWARN)
        finally:
            exce = None

        return result

    ctx = ctxtfilter.sub('at (snip)', repr(func))
    ctx = blue.pyos.taskletTimer.GetCurrent().split('^')[-1] + '^' + ctx
    t = TaskletExtTimeoutable(ctx, wrapper)
    t.isTimedOut = False
    t.doneChannel = stackless.channel()
    t(t, *args, **kw)
    return t


def waitForJoinable(t, timeout):
    resultOk, data = ChannelWait(t.doneChannel, timeout=timeout)
    if resultOk:
        result, exce = data
        if exce is not None:
            try:
                raise exce[0], exce[1], exce[2]
            finally:
                exce = None

        return result
    t.isTimedOut = True
    raise TaskletWaitTimeout()


class TaskletWaitTimeout(Exception):
    pass


idIndex = 0

def uniqueId():
    """Microthread-safe way to get unique numbers, handy for
    giving things unique ID numbers"""
    global idIndex
    z = idIndex
    idIndex += 1
    return z


def irandom(n):
    """Microthread-safe version of random.randrange(0,n)"""
    import random
    n = random.randrange(0, n)
    return n


semaphores = weakref.WeakKeyDictionary()

def GetSemaphores():
    return semaphores


class Semaphore:
    """Semaphores protect globally accessible resources from
    the effects of context switching."""
    __guid__ = 'uthread.Semaphore'

    def __init__(self, semaphoreName = None, maxcount = 1, strict = True):
        self.semaphoreName = semaphoreName
        self.maxcount = maxcount
        self.count = maxcount
        self.waiting = stackless.channel()
        self.n_waiting = 0
        self.waiting.preference = 0
        self.threads = []
        self.lockedWhen = None
        self.strict = strict
        locks.Register(self)

    def IsCool(self):
        """
            returns true if and only if nobody has, or is waiting for, this lock
        """
        return self.count == self.maxcount and not self.n_waiting

    def __repr__(self):
        return '<Semaphore %r, t:%f at %#x>' % (self.semaphoreName, self.LockedFor(), id(self))

    def __del__(self):
        if not self.IsCool():
            log.general.Log("Semaphore '" + str(self.semaphoreName) + "' is being destroyed in a locked or waiting state", 4, 0)

    def acquire(self):
        with atomic():
            if self.strict:
                if self.count <= 0 and stackless.getcurrent() in self.threads:
                    raise RuntimeError, 'tasklet deadlock, acquiring tasklet holds strict semaphore'
            while self.count == 0:
                self.n_waiting += 1
                try:
                    self.waiting.receive()
                except:
                    self._safe_pump()
                    raise
                finally:
                    self.n_waiting -= 1

            self.count -= 1
            self.lockedWhen = blue.os.GetWallclockTime()
            self.threads.append(stackless.getcurrent())

    claim = acquire

    def try_acquire(self):
        with atomic():
            if self.strict:
                if self.count <= 0 and stackless.getcurrent() in self.threads:
                    raise RuntimeError, 'tasklet deadlock, acquiring tasklet holds strict semaphore'
            if self.count > 0:
                self.count -= 1
                self.lockedWhen = blue.os.GetWallclockTime()
                self.threads.append(stackless.getcurrent())
                return True
            return False

    def release(self, override = False):
        with atomic():
            if self.strict and not override:
                if stackless.getcurrent() not in self.threads:
                    raise RuntimeError, 'wrong tasklet releasing strict semaphore'
            self.count += 1
            self.threads.remove(stackless.getcurrent())
            self.lockedWhen = None
            self._pump()

    def _safe_pump(self):
        try:
            self._pump()
        except Exception:
            pass

    def _pump(self):
        for i in range(min(self.count, -self.waiting.balance)):
            self.waiting.send(None)

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc, val, tb):
        self.release()

    def WaitingTasklets(self):
        """return a list of all waiting tasklets"""
        r = []
        first = next = self.waiting.queue
        while next:
            r.append(next)
            next = next.next
            if next == first:
                break

        return r

    def HoldingTasklets(self):
        """return a list of all tasklets that own this semophore"""
        return self.threads[:]

    def LockedAt(self):
        return self.lockedWhen

    def LockedFor(self):
        if self.lockedWhen:
            return (blue.os.GetWallclockTime() - self.lockedWhen) * 1e-07
        else:
            return -1.0


class CriticalSection(Semaphore):
    __guid__ = 'uthread.CriticalSection'

    def __init__(self, semaphoreName = None, strict = True):
        Semaphore.__init__(self, semaphoreName)
        self.__reentrantRefs = 0

    def __repr__(self):
        return '<CriticalSection %r, t:%f at %#x>' % (self.semaphoreName, self.LockedFor(), id(self))

    def _owns(self):
        if stackless.getcurrent() in self.threads:
            return True
        for t in self.threads:
            if locks.Inherits(t):
                return True

        return False

    def acquire(self):
        if self.count <= 0 and self._owns():
            self.__reentrantRefs += 1
        else:
            Semaphore.acquire(self)

    def try_acquire(self):
        if self.count <= 0 and self._owns():
            self.__reentrantRefs += 1
            return True
        else:
            return Semaphore.try_acquire(self)

    def release(self):
        if self.__reentrantRefs:
            if not self._owns():
                raise RuntimeError, 'wrong tasklet releasing reentrant CriticalSection'
            self.__reentrantRefs -= 1
        else:
            Semaphore.release(self)


def FNext(f):
    first = stackless.getcurrent()
    try:
        cursor = first.next
        while cursor != first:
            if cursor.frame.f_back == f:
                return FNext(cursor.frame)
            cursor = cursor.next

        return f
    finally:
        first = None
        cursor = None


class RWLock(object):
    """
    A Reader-Writer lock.  Allows multiple readers at the same time but
    only one Writer.  Writers have preference over readers.
    A RWLock is reentrant in a limited fashion:  A thread holding the lock
    can always get another RDLock.  And a thread holding a WRLock can get another
    WRLock.  But in general, a thread holding a RDLock cannor recursively acquire a WRLock.
    Of course, any recursive lock (RDLock or WRLock) must be mathced with an Unlock.
    """
    __guid__ = 'uthread.RWLock'

    def __init__(self, lockName = ''):
        self.name = lockName
        self.rchan = stackless.channel()
        self.wchan = stackless.channel()
        self.rchan.preference = self.wchan.preference = 0
        self.state = 0
        self.tasklets = []
        self.lockedWhen = None
        locks.Register(self)

    def __repr__(self):
        return '<RWLock %r, state:%d, rdwait:%d, wrwait:%d, t:%f at %#x>' % (self.name,
         self.state,
         -self.rchan.balance,
         -self.wchan.balance,
         self.LockedFor(),
         id(self))

    def RDLock(self):
        if not self.TryRDLock():
            self.rchan.receive()

    def TryRDLock(self):
        if self.state >= 0:
            if self.wchan.balance == 0 or stackless.getcurrent() in self.tasklets:
                self.state += 1
                self._AddTasklet()
                return True
            return False
        else:
            return self.TryWRLock()

    def WRLock(self):
        if not self.TryWRLock():
            if stackless.getcurrent() in self.tasklets:
                raise RuntimeError('Deadlock. Trying to WRLock while holding a RDLock')
            self.wchan.receive()

    def TryWRLock(self):
        if self.state == 0 or self.state < 0 and stackless.getcurrent() == self.tasklets[0]:
            self.state -= 1
            self._AddTasklet()
            return True
        return False

    def Unlock(self, tasklet = None):
        if tasklet is None:
            tasklet = stackless.getcurrent()
        try:
            self.tasklets.remove(tasklet)
        except ValueError:
            raise RuntimeError('Trying to release a rwlock without a matching lock!')

        if self.state > 0:
            self.state -= 1
        else:
            self.state += 1
        if self.state == 0:
            self.lockedWhen = None
        self._Pump()

    def _AddTasklet(self, tasklet = None):
        """Add a tasklet to the list of HoldingTasklets and update lock time"""
        if not tasklet:
            tasklet = stackless.getcurrent()
        self.tasklets.append(tasklet)
        if not self.lockedWhen:
            self.lockedWhen = blue.os.GetWallclockTime()

    def _Pump(self):
        while True:
            chan = self.wchan
            if chan.balance:
                if self.state == 0:
                    self.state = -1
                    self._AddTasklet(chan.queue)
                    chan.send(None)
                    return
            else:
                chan = self.rchan
                if chan.balance and self.state >= 0:
                    self.state += 1
                    self._AddTasklet(chan.queue)
                    chan.send(None)
                    continue
            return

    def __enter__(self):
        self.RDLock()

    def __exit__(self, e, v, tb):
        self.Unlock()

    class WRCtxt(object):

        def __init__(self, lock):
            self.lock = lock

        def __enter__(self):
            self.lock.WRLock()

        def __exit__(self, e, v, tb):
            self.lock.Unlock()

    def WRLocked(self):
        return self.WRCtxt(self)

    def RDLocked(self):
        return self

    def IsCool(self):
        return self.state == 0

    @property
    def thread(self):
        """Return a thread holding the lock"""
        if self.tasklets:
            return self.tasklets[0]

    def WaitingTasklets(self):
        r = []
        for chan in (self.rchan, self.wchan):
            first = t = chan.queue
            while t:
                r.append(t)
                t = t.next
                if t is first:
                    break

        return r

    def HoldingTasklets(self):
        return list(self.tasklets)

    def LockedAt(self):
        return self.lockedWhen

    def IsWRLocked(self):
        return self.state < 0

    def IsRDLocked(self):
        return self.state > 0

    def LockedFor(self):
        if self.lockedWhen:
            return (blue.os.GetWallclockTime() - self.lockedWhen) * 1e-07
        else:
            return -1.0


channels = weakref.WeakKeyDictionary()

def GetChannels():
    global channels
    return channels


class Channel(stackless.channel):
    """
        A Channel is a stackless.channel() with administrative spunk
    """
    __guid__ = 'uthread.Channel'

    def __new__(cls, channelName = None):
        return stackless.channel.__new__(cls)

    def __init__(self, channelName = None):
        stackless.channel.__init__(self)
        self.channelName = channelName
        channels[self] = 1


class FIFO(object):
    """A fifo sports push() and pop() methods of O(1) complexity"""
    __slots__ = ('data',)

    def __init__(self):
        self.data = [[], []]

    def push(self, v):
        """Add an element onto the fifo"""
        self.data[1].append(v)

    def pop(self):
        """removes an element in first-in-first-out fashion"""
        d = self.data
        if not d[0]:
            d.reverse()
            d[0].reverse()
        return d[0].pop()

    def front(self):
        """returns the item that would be popped"""
        d = self.data
        if d[0]:
            return d[0][-1]
        return d[1][0]

    def __contains__(self, o):
        d = self.data
        return o in d[0] or o in d[1]

    def __len__(self):
        d = self.data
        return len(d[0]) + len(d[1])

    def clear(self):
        self.data = [[], []]

    def remove(self, o):
        """removes the first instance of element, or raise ValueError"""
        d = self.data
        if d[0]:
            d[0].reverse()
            d[1] = d[0] + d[1]
            d[0] = []
        d[1].remove(o)


class Queue(FIFO):
    """A Queue is similar to a channel, but sends don't block, rather the values are queued up."""
    __guid__ = 'uthread.Queue'
    __slots__ = 'chan'

    def __init__(self, preference = 0):
        FIFO.__init__(self)
        self.chan = stackless.channel()
        self.chan.preference = preference

    def put(self, x):
        """Put a value on the queue.  Doesn't block"""
        if self.chan.balance < 0:
            self.chan.send(x)
        else:
            self.push(x)

    non_blocking_put = put

    def get(self):
        """gets a value from the queue.  Blocks if it is empty"""
        if len(self):
            return self.pop()
        else:
            return self.chan.receive()


def LockCheck():
    while 1:
        each = None
        blue.pyos.synchro.SleepWallclock(60660)
        now = blue.os.GetWallclockTime()
        try:
            for each in locks.GetLocks():
                if each.LockedAt() and each.WaitingTasklets():
                    problem = now - each.LockedAt()
                    if problem >= 1 * MIN:
                        break
            else:
                problem = 0

            if not problem:
                continue
            with log.general.open(log.LGERR) as s:
                print >> s, 'Locks have been held for a long time (%ss). Locking conflict log' % (problem / SEC)
                foundCycles = locks.LockCycleReport(out=s, timeLimit=60)
                if not foundCycles:
                    print >> s, 'logical analysis found no cycles.'
                if not foundCycles:
                    print >> s, 'Full dump of locks with waiting tasklets:'
                    locks.OldLockReport(None, out=s)
                print >> s, 'End of locking conflict log'
        except StandardError:
            log.LogException()
            sys.exc_clear()


def PoolWorker(ctx, func, *args, **keywords):
    """
        Same as uthread.pool, but without copying local storage, thus resetting session, etc.
    
        Should be used for spawning worker threads.
    """
    return PoolWithoutTheStars(ctx, func, args, keywords, True)


def PoolWorkerWithoutTheStars(ctx, func, args, keywords):
    """
        Same as uthread.worker, but without copying local storage, thus resetting session, etc.
    
        Should be used for spawning worker threads.
    """
    return PoolWithoutTheStars(ctx, func, args, keywords, True)


def PoolWithoutTheStars(ctx, func, args, kw, notls = False):
    if not ctx:
        ctx = ctxtfilter.sub('at (snip)', repr(func))
    if ctx[0] != '^':
        prefix = blue.pyos.taskletTimer.GetCurrent().split('^')[-1]
        ctx = prefix + '^' + ctx
    tasklet = bluepy.TaskletExt(ctx, func)
    if notls:
        tasklet.localStorage.clear()
    tasklet(*args, **kw)
    return tasklet


def Pool(ctx, func, *args, **keywords):
    """
        executes apply(args,keywords) on a new uthread. ctx is used as the
        thread context.
    """
    return PoolWithoutTheStars(ctx, func, args, keywords)


def ParallelHelper(ch, idx, what):
    queue, parentTasklet = ch
    try:
        with locks.Inheritance(parentTasklet):
            if len(what) > 2:
                result = what[0](*what[1], **what[2])
            else:
                result = what[0](*what[1])
            ret = (1, (idx, result))
    except:
        ret = (0, sys.exc_info())

    queue.put(ret)


def Parallel(funcs, exceptionHandler = None, maxcount = 30, contextSuffix = None, funcContextSuffixes = None):
    """
        Executes in parallel all the function calls specified in the list/tuple 'funcs', but returns the
        return values in the order of the funcs list/tuple.  If an exception occurs, only the first exception
        will reach you.  The rest will dissapear in a puff of logic.  The function returns when all the
        parallel tasks have completed, with or without error.
    
        Each 'func' entry should be a tuple/list of:
        1.  a function to call
        2.  a tuple of arguments to call it with
        3.  optionally, a dict of keyword args to call it with.
    """
    if not funcs:
        return
    context = blue.pyos.taskletTimer.GetCurrent()
    if contextSuffix:
        context += '::' + contextSuffix
    ch = (Queue(preference=-1), stackless.getcurrent())
    n = len(funcs)
    ret = [None] * n
    if n > maxcount:
        n = maxcount
    for i in xrange(n):
        funcContext = context
        if funcContextSuffixes is not None:
            funcContext = funcContext + '::' + funcContextSuffixes[i]
        Pool(funcContext, ParallelHelper, ch, i, funcs[i])

    error = None
    try:
        for i in xrange(len(funcs)):
            ok, bunch = ch[0].get()
            if ok:
                idx, val = bunch
                ret[idx] = val
            else:
                error = bunch
            if n < len(funcs):
                funcContext = context
                if funcContextSuffixes is not None:
                    funcContext = funcContext + '::' + funcContextSuffixes[i]
                Pool(funcContext, ParallelHelper, ch, n, funcs[n])
                n += 1

        if error:
            if exceptionHandler:
                exceptionHandler(error[1])
            else:
                raise error[0], error[1], error[2]
        return ret
    finally:
        del error


class TaskletSequencer(object):
    """This class is to order tasklets coming in with monotonously rising sequence numbers.
       Use this to reorder, for example, network requests that may have gotten confused
       Note: Pass() assumes that we are running in non-interruptable context
    """

    def __init__(self, expected = None):
        self.queue = []
        self.expected = expected
        self.lastThrough = None
        self.closed = False

    def State(self):
        return [self.expected, self.lastThrough, self.closed]

    def IsClosed(self):
        return self.closed

    def close(self):
        self.closed = True
        while self.queue:
            heapq.heappop(self.queue)[1].insert()

    def Assert(self, expression):
        if not expression:
            raise AssertionError(expression)

    def Pass(self, sequenceNo):
        """SequenceNo must be a monotonously incrementing integer"""
        if self.closed:
            return
        if self.expected is None:
            self.expected = sequenceNo
        if sequenceNo < self.expected:
            return
        while sequenceNo > self.expected:
            me = (sequenceNo, stackless.getcurrent())
            heapq.heappush(self.queue, me)
            self.OnSleep(sequenceNo)
            stackless.schedule_remove()
            self.OnWakeUp(sequenceNo)
            if self.closed:
                return

        self.Assert(self.expected == sequenceNo)
        self.expected += 1
        expected = self.expected
        while self.queue and self.queue[0][0] == expected:
            self.OnWakingUp(sequenceNo, expected)
            expected += 1
            other = heapq.heappop(self.queue)
            other[1].insert()

        if self.lastThrough is not None:
            self.Assert(self.lastThrough + 1 == sequenceNo)
        self.lastThrough = sequenceNo

    def OnSleep(self, sequenceNo):
        pass

    def OnWakeUp(self, sequenceNo):
        pass

    def OnWakingUp(self, sequenceNo, target):
        pass


def CallOnThread(cmd, args = (), kwds = {}):
    """Run the given callable on a different thread and return the result
       This function blocks on a channel until the result is available.
       Ideal for performing OS type tasks, such as saving files or compressing
    """
    chan = stackless.channel()

    def Helper():
        try:
            r = cmd(*args, **kwds)
            chan.send(r)
        except:
            e, v = sys.exc_info()[:2]
            chan.send_exception(e, v)
        finally:
            blue.pyos.NextScheduledEvent(0)

    thread = threading.Thread(target=Helper)
    thread.start()
    return chan.receive()


namedlocks = collections.defaultdict(lambda : [None, 0])

def Lock(object, *args):
    t = (id(object), args)
    l = namedlocks[t]
    if not l[0]:
        l[0] = Semaphore(t, strict=False)
    l[1] += 1
    l[0].acquire()


def TryLock(object, *args):
    t = (id(object), args)
    l = namedlocks[t]
    if not l[0]:
        l[0] = Semaphore(t, strict=False)
    l[1] += 1
    if not l[0].try_acquire():
        l[1] -= 1
        return False
    return True


def ReentrantLock(object, *args):
    t = (id(object), args)
    l = namedlocks[t]
    if not l[0]:
        l[0] = CriticalSection(t)
    l[1] += 1
    l[0].acquire()


def UnLock(object, *args):
    t = (id(object), args)
    l = namedlocks[t]
    l[0].release()
    l[1] -= 1
    if not l[1]:
        del namedlocks[t]


def CheckLock(object, *args):
    t = (id(object), args)
    l = namedlocks[t]
    if not l[1]:
        del namedlocks[t]
        return False
    return True


@contextlib.contextmanager
def Locked(object, *args):
    Lock(object, *args)
    try:
        yield
    finally:
        UnLock(object, *args)


class BlockTrapSection(object):
    """
    This is a context mananger for blocktrapped sections of code
    """
    __guid__ = 'uthread.BlockTrapSection'

    def __init__(self):
        self.oldBlocktrap = False

    def __enter__(self):
        self.oldBlockTrap = stackless.getcurrent().block_trap
        stackless.getcurrent().block_trap = True

    def __exit__(self, exc, val, tb):
        stackless.getcurrent().block_trap = self.oldBlockTrap


def ChannelWait(chan, timeout = None):
    """Receive on a channel, but with a timeout.  The optional timeout is specified
       in seconds.  Returns (bool, result) with the bool being true if there
       was no timeout.
    """
    if timeout is None:
        return (True, chan.receive())
    waiting_tasklet = stackless.getcurrent()

    def break_wait():
        try:
            blue.pyos.synchro.SleepWallclock(int(timeout * 1000))
        except _TimeoutError:
            return

        with atomic():
            if waiting_tasklet and waiting_tasklet.blocked:
                waiting_tasklet.raise_exception(_TimeoutError)

    with atomic():
        breaker = new(break_wait)
        try:
            result = chan.receive()
            if breaker.blocked:
                breaker.raise_exception(_TimeoutError)
            return (True, result)
        except _TimeoutError:
            return (False, None)
        finally:
            waiting_tasklet = None


class _TimeoutError(Exception):
    pass


parallel = Parallel
worker = PoolWorker
workerWithoutTheStars = PoolWorkerWithoutTheStars
pool = Pool
exports = {'uthread.parallel': parallel,
 'uthread.worker': worker,
 'uthread.workerWithoutTheStars': workerWithoutTheStars,
 'uthread.new': new,
 'uthread.pool': Pool,
 'uthread.irandom': irandom,
 'uthread.uniqueId': uniqueId,
 'uthread.schedule': schedule,
 'uthread.GetChannels': GetChannels,
 'uthread.GetSemaphores': GetSemaphores,
 'uthread.FNext': FNext,
 'uthread.Lock': Lock,
 'uthread.TryLock': TryLock,
 'uthread.ReentrantLock': ReentrantLock,
 'uthread.UnLock': UnLock,
 'uthread.TaskletSequencer': TaskletSequencer,
 'uthread.CallOnThread': CallOnThread,
 'uthread.CheckLock': CheckLock,
 'uthread.BlockTrapSection': BlockTrapSection,
 'uthread.ChannelWait': ChannelWait,
 'uthread.newJoinable': newJoinable,
 'uthread.waitForJoinable': waitForJoinable,
 'uthread.TaskletWaitTimeout': TaskletWaitTimeout}
new(LockCheck).context = '^uthread::LockCheck'
locks.Startup(new)
