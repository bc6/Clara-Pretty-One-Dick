#Embedded file name: carbon/common/script/net\loginManagementSvc.py
import sys
import service
import blue
import log
import carbon.common.script.util.logUtil as logUtil
import uthread
import string
import util

def _QueueTicker(queue, name, svc):
    """ Calls queue.Tick() every 60 seconds, optionally timing out items before each Tick(). """
    while queue.ticker is not None:
        svc.LogInfo('Started Login Queue Ticker task for queue ', name)
        blue.pyos.synchro.SleepWallclock(60000)
        if queue.ticker is not None:
            try:
                if queue.queueTimeout > 0:
                    l = queue.Timeout(queue.queueTimeout)
                    if len(l) > 0:
                        svc.LogWarn('Timed ', len(l), " clients out of login queue '", name, "' (timeout = ", queue.queueTimeout, ' sec)')
                queue.Tick()
            except:
                log.LogException('Exception in _QueueTicker tasklet')


class LoginManagementService(service.Service):
    """
    The Login queue manages login queues for all apps. Most queueing functionality provided by util.RateLimitedQueue.
    The service is a very simple access/naming point. It has no dependencies and can be freely depended upon.
    """
    __guid__ = 'svc.loginManagementSvc'
    __displayname__ = 'Login queues management system'
    __exportedcalls__ = {'CreateQueue': [service.ROLE_SERVICE],
     'GetQueue': [service.ROLE_SERVICE],
     'GetQueueStats': [service.ROLE_SERVICE],
     'GetQueueSettings': [service.ROLE_SERVICE],
     'SetQueueSettings': [service.ROLE_SERVICE],
     'QueuesDisabled': [service.ROLE_SERVICE]}
    __configvalues__ = {'enableQueuesInLocal': False}

    def Run(self, memStream = None):
        self.queuesByName = {}

    def Stop(self, memStream):
        """ Signal any queue tickers to stop """
        for q in self.queuesByName.itervalues():
            q.ticker = None

        service.Service.Stop(self, memStream)

    def CreateQueue(self, qname, defMaxCompleteItems, defMaxReadyItems, defMaxReadyRate = sys.maxint, defMaxReadyGrowth = 0, defMaxQueuedItems = sys.maxint, defTimeout = 180.0, numCompleteFunc = None):
        """
        Pre: qname is not None
        Creates a login queue whose Queue Name is 'qname', if one did not exist already.
        if prefs.clusterMode == "LOCAL" and not self.enableQueuesInLocal:
           ALL QUEUES ARE UNLIMITED, as not to get in developers' way, and nothing ever times out.
        Otherwise:
            The def*... settings are ONLY used for the corresponding rateLimitedQueue's max* parameters if those
            parameters are missing or invalid in prefs. A tasklet running every 60 seconds ticks the queue. It will
            throw items older than defTimeout seconds out of the queue / ready set, if defTimeout > 0.
        Returns the queue (the new or existing one).
        """
        if qname is None:
            raise RuntimeError("'qname' cannot be None")

        def GetOrSetPref(setting, defVal):
            """Get and error check queue setting 'setting'. If the pref doesn't exist we set it to 'defVal'"""
            prefKey = 'LoginQueue_' + qname + '_' + setting
            pref = prefs.GetValue(prefKey, None)
            if pref is None:
                self.LogWarn('Login Queue setting %s not in prefs, setting to default (%s)' % (prefKey, defVal))
                prefs.SetValue(prefKey, defVal)
                pref = prefs.GetValue(prefKey, defVal)
            try:
                return int(pref)
            except ValueError:
                self.LogError("Login Queue setting %s has invalid value '%s' in prefs, using default (%s)" % (prefKey, pref, defVal))
                return int(defVal)

        maxReadyItems = GetOrSetPref('MaxReady', defMaxReadyItems)
        maxReadyRate = GetOrSetPref('MaxLoginRate', defMaxReadyRate)
        maxReadyGrowth = GetOrSetPref('ReadyGrowth', defMaxReadyGrowth)
        maxQueuedItems = GetOrSetPref('MaxInQueue', defMaxQueuedItems)
        maxCompleteItems = GetOrSetPref('MaxLoggedIn', defMaxCompleteItems)
        timeout = GetOrSetPref('QueueTimeout', defTimeout)
        if self.QueuesDisabled():
            maxReadyItems = sys.maxint
            maxReadyRate = sys.maxint
            maxReadyGrowth = 0
            maxQueuedItems = sys.maxint
            maxCompleteItems = sys.maxint
            timeout = 0
        if qname in self.queuesByName:
            return self.queuesByName[qname]
        else:
            logUtil.LogInfo("Creating Login Queue '", qname, "'")
            queue = util.RateLimitedQueue(maxReadyItems=maxReadyItems, maxReadyRate=maxReadyRate, maxReadyGrowth=maxReadyGrowth, maxQueuedItems=maxQueuedItems, maxCompleteItems=maxCompleteItems, numCompleteFunc=numCompleteFunc)
            self.queuesByName[qname] = queue
            queue.queueTimeout = timeout
            queue.ticker = uthread.new(_QueueTicker, queue, qname, self)
            return queue

    def GetQueue(self, qname, default = None):
        """
        Returns the RateLimitedQueue for 'qname' or 'default' iff no queue has been QueuedCreated with that name
        The queue's NumQueued() == number of clients waiting for a login slot
        The queue's NumReady() == number of clients ready to log in (i.e. have a login slot)
        The queue's NumComplete() == number of fully logged in clients
        """
        return self.queuesByName.get(qname, default)

    def GetQueueStats(self, qname = None, default = None):
        """
        If 'qname' is None: returns a map from each queue qname to a dictionary containing that queue's dynamic stats
        Else: returns the stats dict for queue 'qname' or 'default' if queue 'qname' doesn't exist
        """
        if qname is None:
            return {qname:self._GetQueueStats(queue) for qname, queue in self.queuesByName.iteritems()}
        else:
            queue = self.queuesByName.get(qname, None)
            if queue is not None:
                return self._GetQueueStats(queue)
            return default

    def GetQueueSettings(self, qname = None, default = None):
        """
        If 'qname' is None: returns a map from each queue qname to a dictionary containing that queue's settings
        Else: returns the settings dict for queue 'Name' or 'default' if queue 'qname' doesn't exist
        """
        if qname is None:
            return {qname:self._GetQueueSettings(queue) for qname, queue in self.queuesByName.iteritems()}
        else:
            queue = self.queuesByName.get(qname, None)
            if queue is not None:
                return self._GetQueueSettings(queue)
            return default

    def SetQueueSettings(self, qname, **kwargs):
        """
        Pre:  self.GetQueueByName(qname) is not None, the keys of 'kwargs' are a subset of self.GetQueueSettings(qname).keys(),
              each value is an integer or None (meaning: no limit, no growth or no timeout).
              The new settings are persisted in prefs, so they'll be read back by future CreateQueue()s.
        """
        if qname is None:
            raise RuntimeError("'qname' cannot be None")
        if qname not in self.queuesByName:
            raise RuntimeError("There is no Login Queue named '" + str(qname) + "'")
        queue = self.queuesByName[qname]
        validKeys = self._GetQueueSettings(queue)
        for k in kwargs.iterkeys():
            if k not in validKeys:
                raise RuntimeError("Invalid Queue Setting: '" + str(k) + "'")

        def UpdatePref(setting, pref, blankValue):
            """ updates the setting and queue attribute if in kwargs, substituting blankValue for Nones """
            if setting in kwargs:
                attrname = string.lower(setting[0]) + setting[1:]
                value = kwargs[setting] if kwargs[setting] is not None else blankValue
                try:
                    value = int(value)
                except ValueError:
                    self.LogError("Queue Setting %s = '%s' is invalid (is not an integer)" % (setting, value))
                    return

                setattr(queue, attrname, value)
                prefKey = 'LoginQueue_' + qname + '_' + pref
                prefs.SetValue(prefKey, value)

        UpdatePref('MaxQueuedItems', 'MaxInQueue', sys.maxint)
        UpdatePref('MaxReadyItems', 'MaxReady', sys.maxint)
        UpdatePref('MaxReadyRate', 'MaxLoginRate', sys.maxint)
        UpdatePref('MaxCompleteItems', 'MaxLoggedIn', sys.maxint)
        UpdatePref('MaxReadyGrowth', 'ReadyGrowth', 0)
        UpdatePref('QueueTimeout', 'QueueTimeout', 0)

    def _GetQueueStats(self, queue):
        wait = queue.QueueFrontWaitTime()
        return {'NumQueued': queue.NumQueued(),
         'NumReady': queue.NumReady(),
         'NumComplete': queue.NumComplete(),
         'QueueFrontWaitTime': round(wait) if wait is not None else 0.0}

    def _GetQueueSettings(self, queue):
        return {'MaxQueuedItems': queue.maxQueuedItems,
         'MaxReadyItems': queue.maxReadyItems,
         'MaxReadyRate': queue.maxReadyRate,
         'MaxCompleteItems': queue.maxCompleteItems,
         'MaxReadyGrowth': queue.maxReadyGrowth,
         'QueueTimeout': queue.queueTimeout}

    def QueuesDisabled(self):
        """ True iff queues have been disabled in LOCAL mode """
        return prefs.clusterMode == 'LOCAL' and not self.enableQueuesInLocal

    def SignalTickerStop(self):
        """ If the queue had a ticker tasklet: it has been signalled to stop """
        self.ticker = None
