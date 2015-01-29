#Embedded file name: carbon/common/script/util\rateLimitedQueue.py
import sys
import time
import collections
QueueEntry = collections.namedtuple('QueueEntry', ['serialNumber', 'firstTime', 'queueTime'])

class RateLimitedQueue(object):
    """
    A queue in front of a set of "ready" items. Implements efficient queries for an item's state, that is:
    position in queue and Queued/Ready state. Ready items enter the Complete state by being removed from the
    RateLimitedQueue altogether. Items can move from queue to the ready state maximum rate readyRate.
    Has several parameters to suit the slightly different needs of EVE, DUST and third-party apps, see __init__.
    The queue automatically moves items from the queued to ready state as fast as permitted but things are
    only complete (removed from system) using the explicit Complete() call.
    """

    def __init__(self, maxReadyItems = sys.maxint, maxReadyRate = sys.maxint, maxReadyGrowth = 0, maxQueuedItems = sys.maxint, maxCompleteItems = sys.maxint, numCompleteFunc = None):
        """
        Initializes a queue with the given parameters (see comments for max... here below).
        Note: using all-default admits all items to ready-state right away, probably not what you want.
        
        Note: by default the queue allows unlimited items in the complete state (and self.NumComplete() yields the
        number of items having gone through the system). If 'numCompleteFunc' is passed it must be a callable
        returning the current number of items in the complete state. The value of this function is then returned
        from self.NumComplete(). A typical numComplete function returns len(_C_) for some set of complete items _C_
        maintained by the calling application.
        
        The number of Ready items is never allowed to surpass maxCompleteItems - self.NumComplete(), so if
        maxCompleteItems is set to a limiting value you probably want to set a 'numCompleteFunc' function too,
        whose value can go down as well as up. Otherwise only a finite number of items will ever go from
        Ready to Complete state.
        
        maxReadyGrowth provides an emulation of EVE's handling of rate and "stale" entries in the Ready set (in EVE's
        case: users at front of queue who don't log in; are AFK e.g.). EVE sets initial maxReadyItems=0 and
        maxReadyRate=infinity but allows maxReadyItems to grow over time, capping it to the total number of
        items in the system. CREST, by contrast, uses a leaky-bucket model (maxReadyRate=x) and uses time-outs to weed
        out stale entries from the ready set.
        
        The queue must be externally ticked (via its Tick() method) to move items to the ready state.
        
        The max-settings can be modified after queue creation but may only take effect gradually.
        For example: a lowering of maxQueueItems might block new items from being enqueued until the queue drains out.
        """
        self.maxReadyItems = maxReadyItems
        self.maxReadyRate = maxReadyRate
        self.maxReadyGrowth = maxReadyGrowth
        self.maxQueuedItems = maxQueuedItems
        self.maxCompleteItems = maxCompleteItems
        self.queue = collections.deque()
        self.queueMap = dict()
        self.nextSerialNumber = 0
        self.numReady = 0
        self.numReadied = 0
        self.maxReadyBoost = 0
        self.ticker = None
        if numCompleteFunc is None:
            self.numCompleteFunc = lambda : self.nextSerialNumber - len(self.queueMap)
        else:
            self.numCompleteFunc = numCompleteFunc

    NONE = 0
    QUEUED = 1
    READY = 2
    COMPLETE = NONE

    def State(self, key):
        """ Returns the queueing-system state of 'key' """
        queueEntry = self.queueMap.get(key, None)
        if queueEntry is None:
            return RateLimitedQueue.NONE
        if queueEntry.serialNumber == -1:
            return RateLimitedQueue.READY
        return RateLimitedQueue.QUEUED

    def NumQueued(self):
        """ Returns the number of items in QUEUED state """
        return len(self.queueMap) - self.numReady

    def NumReady(self):
        """ Returns the number of items in READY state """
        return self.numReady

    def NumTotal(self):
        """ Returns NumQueued() + NumReady() """
        return len(self.queueMap)

    def NumComplete(self):
        """ Returns the number of items in the Complete set """
        return self.numCompleteFunc()

    def GetQueue(self):
        """ Returns a list of the keys in the Queue """
        return [ k for k in self.queue if k in self.queueMap and self.queueMap[k].serialNumber != -1 ]

    def GetReadySet(self):
        """ Returns the set of keys in the Ready Set """
        return {k for k in self.queueMap if self.queueMap[k].serialNumber == -1}

    def QueuePosition(self, key):
        """
        If self.State(key) == QUEUED: returns a pair (_pos_, _wait_), where _pos_ is the approximate position of
            'key' in the queue (0 means head of queue, approximate position may be slightly larger than real position
            but never less than) and _wait_ is the number of seconds since entry 'key' was first enqueued
        Else: returns None
        """
        queueEntry = self.queueMap.get(key, None)
        if queueEntry is not None and queueEntry.serialNumber != -1:
            firstEntry = self.queueMap[self.queue[0]]
            return (queueEntry.serialNumber - firstEntry.serialNumber, time.clock() - queueEntry.firstTime)
        else:
            return

    def Enqueue(self, key, bypassQueue = False):
        """
        If bypassQueue: self.State(key) == READY (all limits are ignored)
        Else:
            If queue was full (self.NumQueued() >= self.maxQueuedItems), no effect, returns None,
            Else: if self.State(key) was NONE before call: self.State(key) == QUEUED or READY
            The time of last enqueuing for 'key' has been set to the current time.
        Returns self.State(key)
        """
        queueEntry = self.queueMap.get(key, None)
        now = time.clock()
        if bypassQueue:
            if queueEntry is not None:
                if queueEntry.serialNumber != -1:
                    self.Remove(key)
                else:
                    self.queueMap[key] = QueueEntry(serialNumber=-1, firstTime=queueEntry.firstTime, queueTime=now)
                    return RateLimitedQueue.READY
            else:
                self.nextSerialNumber += 1
            self.queueMap[key] = QueueEntry(serialNumber=-1, firstTime=now, queueTime=now)
            self.numReady += 1
            self.numReadied += 1
        else:
            if queueEntry is None:
                if self.NumQueued() >= self.maxQueuedItems:
                    return
                queueEntry = QueueEntry(serialNumber=self.nextSerialNumber, firstTime=now, queueTime=now)
                self.nextSerialNumber += 1
                self.queue.append(key)
                self.queueMap[key] = queueEntry
            else:
                self.queueMap[key] = QueueEntry(serialNumber=queueEntry.serialNumber, firstTime=queueEntry.firstTime, queueTime=now)
            self.MakeReady()
        return self.State(key)

    def Complete(self, key):
        """
        If self.State(key) != READY or self.NumComplete() >= self.maxCompleteItems: no effect, returns None,
        Else: self.State(key) == COMPLETE, self.NumReady() decremented by 1, returns the length of time
            'key' spent in the queueing system
        note: recall that COMPLETE is the same as NONE!
        """
        if self.State(key) != RateLimitedQueue.READY or self.numCompleteFunc() >= self.maxCompleteItems:
            return None
        delay = time.clock() - self.queueMap[key].firstTime
        del self.queueMap[key]
        self.numReady -= 1
        self.MakeReady()
        return delay

    def Process(self, key, bypassQueue = False):
        """
        If calling self.Enqueue(key) returned READY: returns COMPLETE if self.Complete(key) completed 'key';
        Else: returns self.Enqueue(key)
        note: just a shortcut for trying to enqueue and complete an item in one fell swoop
        """
        state = self.Enqueue(key, bypassQueue)
        if state == RateLimitedQueue.READY and self.Complete(key) is not None:
            return RateLimitedQueue.NONE
        return state

    def Remove(self, key):
        """
        Post: self.State(key) == NONE. Returns True if 'key' was present and therefore removed; else: returns False
        If the old state was READY: some item may have moved to READY state
        """
        state = self.State(key)
        if state != RateLimitedQueue.NONE:
            del self.queueMap[key]
            if state == RateLimitedQueue.READY:
                self.numReady -= 1
                self.MakeReady()
            elif len(self.queue) > 0 and self.queue[0] == key:
                self._ClearQueueJunk()
            return True
        return False

    def QueueFrontWaitTime(self, default = None):
        """ Returns the current wait-time of the frontmost queue Item or 'default' iff NumQueued() == 0"""
        if len(self.queue) > 0:
            return time.clock() - self.queueMap[self.queue[0]].firstTime
        else:
            return default

    def Timeout(self, olderThan, fromQueue = True, fromReady = True):
        """
        All items last (re)enqueued more than 'olderThan' seconds ago have been Remove()d.
        Returns a list of the keys timed out.
        """
        deadline = time.clock() - olderThan
        timedOut = [ k for k, q in self.queueMap.iteritems() if q.queueTime < deadline ]
        self.numReady -= len({k:q for k, q in self.queueMap.iteritems() if q.queueTime < deadline and q.serialNumber == -1})
        self.queueMap = {k:q for k, q in self.queueMap.items() if q.queueTime >= deadline}
        self._ClearQueueJunk()
        self.MakeReady()
        return timedOut

    def Tick(self):
        """ Admits the next up to self.maxReadyRate to the READY state """
        self.numReadied = 0
        effectiveMaxReadyItems = min(self.maxReadyItems + self.maxReadyBoost + self.maxReadyGrowth, self.NumTotal())
        self.maxReadyBoost = max(effectiveMaxReadyItems - self.maxReadyItems, 0)
        self.MakeReady()

    def MakeReady(self):
        """
        Move as many items to the Ready state as possible.
        This is called automatically as needed by other methods (Enqueue, Complete ...) but needs to be
        called explicitly if there's a chance of q.NumComplete() having gone down, allowing one or more
        items to now enter the Ready state.
        """
        maxItems = len(self.queue)
        maxItems = min(maxItems, self.maxReadyRate - self.numReadied)
        maxItems = min(maxItems, self.maxReadyItems + self.maxReadyBoost - self.numReady)
        maxItems = min(maxItems, self.maxCompleteItems - self.numCompleteFunc() - self.numReady)
        numItemsReadied = 0
        while numItemsReadied < maxItems and len(self.queue) > 0:
            key = self.queue.popleft()
            queueEntry = self.queueMap[key]
            self.queueMap[key] = QueueEntry(serialNumber=-1, firstTime=queueEntry.firstTime, queueTime=queueEntry.queueTime)
            numItemsReadied += 1
            self._ClearQueueJunk()

        self.numReady += numItemsReadied
        self.numReadied += numItemsReadied

    def _ClearQueueJunk(self):
        try:
            queueEntry = self.queueMap.get(self.queue[0], None)
            while queueEntry is None or queueEntry.serialNumber == -1:
                self.queue.popleft()
                queueEntry = self.queueMap.get(self.queue[0], None)

        except IndexError:
            pass


exports = {'util.RateLimitedQueue': RateLimitedQueue}
