#Embedded file name: carbon/common/script/sys\counterService.py
"""
    This file contains the implementation of a counter service.  The idea is that
    users create a counter through the counterService and then update that counter
    through its member variables.

    The counter service will take care of flushing the counters to a file periodically
    The interval along with other settings can be controlled through ESP pages
    Users are able to create their own counters by subclassing the existing counters
    but will have to fullfill certain requirements documented in the code

"""
import blue
import service
import uthread
import util
import types
import log
from collections import defaultdict
from service import ROLE_SERVICE, ROLE_ADMIN, ROLE_PROGRAMMER
globals().update(service.consts)

def CurrentTimeString():
    """
        returns a string which should be used as a parameter in the flush call
        the format is: 7/26/2002 14:58:51.15
        Flush will append "     %d" where d is the Value() of the counter
    """
    year, month, weekday, day, hour, minute, second, ms = util.GetTimeParts(blue.os.GetWallclockTime())
    line = '%d/%d/%d %d:%d:%d.%d' % (month,
     day,
     year,
     hour,
     minute,
     second,
     ms)
    return line


class Counter:
    """
        Basic counter.
        Users must remember to Flush the counter a regular interval with a
        string parameter from the CurrentTimeString() function
    
    """

    def __init__(self, name, parent):
        self.counter = 0
        self.parent = parent
        self.name = name
        self.filename = ''
        import log
        self.logChannel = log.GetChannel('Counters.' + self.name)

    def Reset(self):
        self.counter = 0

    def Add(self, value = 1):
        self.counter += value

    def Dec(self, value = 1):
        self.counter -= value

    def Set(self, value):
        self.counter = value

    def Value(self):
        return self.counter

    def Flush(self):
        """ append value after line, insert         between """
        self.logChannel.Log(strx(self.Value()), log.LGINFO)


class TrafficCounter(Counter):
    """
        Traffic Counter
        Tracks "bytes", "packets", "min", and "max"
        Can track traffic sources with AddFrom() and PerSource()
    
    """

    def __init__(self, name, parent):
        Counter.__init__(self, name, parent)
        self.Reset()

    def Reset(self):
        self.currval = 0
        self.total = 0
        self.minval = 0
        self.maxval = 0
        self.lastcur = 0
        self.lasttot = 0
        self.perfrom = {}
        self.perfrom = defaultdict(lambda : 0)
        self.lastperfrom = {}
        self.lastperfrom = defaultdict(lambda : 0)

    def Add(self, value = 1):
        self.currval += value
        self.total += 1
        if value > self.maxval:
            self.maxval = value
        if (not self.minval or value < self.minval) and value:
            self.minval = value

    def AddFrom(self, nodeID, value = 1):
        """
            Tracks the source of traffic between nodes
        """
        self.perfrom[nodeID] += value
        self.Add(value)

    def Dec(self, value = 1):
        raise AttributeError('Dec is cwap on TrafficCounter')

    def Set(self, value):
        raise AttributeError('Set is cwap on TrafficCounter')

    def Current(self):
        return self.currval

    def Count(self):
        return self.total

    def LastFlow(self):
        return self.lastcur

    def LastCount(self):
        return self.lasttot

    def PerSource(self):
        return self.lastperfrom.items()

    def Min(self):
        return self.minval

    def Max(self):
        return self.maxval

    def Value(self):
        if type(self.currval) == types.FloatType:
            avg = 0.0
            if self.total != 0.0:
                avg = float(self.currval / self.total)
            return 'curr=%f, min=%f, max=%f, count=%d, avg=%f' % (self.currval,
             self.minval,
             self.maxval,
             self.total,
             avg)
        else:
            avg = 0
            if self.total != 0:
                avg = long(self.currval / self.total)
            out = 'curr=%d, min=%d, max=%d, count=%d, avg=%d' % (self.currval,
             self.minval,
             self.maxval,
             self.total,
             avg)
            for n in self.perfrom:
                out += ', %s from %s' % (self.perfrom[n], n)

            return out

    def Flush(self):
        """ append value after line, insert         between """
        self.logChannel.Log(strx(self.Value()), log.LGINFO)
        if self.name == 'dataSent' or self.name == 'dataReceived':
            self.lastcur = self.currval
            self.lasttot = self.total
            self.currval = 0
            self.total = 0
            self.lastperfrom.clear()
            self.lastperfrom = self.perfrom.copy()
            self.perfrom.clear()


class StatCounter(Counter):
    """
        Statistic gatherer counter
        Tracks last, min, max, avg, count
    """

    def __init__(self, name, parent):
        Counter.__init__(self, name, parent)
        self.Reset()

    def Reset(self):
        self.lastval = 0
        self.total = 0
        self.minval = 0
        self.maxval = 0
        self.count = 0

    def Add(self, value = 1):
        self.lastval = value
        self.total += value
        self.count += 1
        if value > self.maxval:
            self.maxval = value
        if (not self.minval or value < self.minval) and value:
            self.minval = value

    def Dec(self, value = 1):
        raise NotImplementedError

    def Set(self, value):
        raise NotImplementedError

    def Total(self):
        return self.total

    def Count(self):
        return self.count

    def Min(self):
        return self.minval

    def Max(self):
        return self.maxval

    def Avg(self):
        avg = 0.0
        if self.count > 0:
            avg = self.total / float(self.count)
        return avg

    def Value(self):
        return 'total=%f, last=%f, min=%f, max=%f, count=%f, avg=%f' % (self.total,
         self.lastval,
         self.minval,
         self.maxval,
         self.count,
         self.Avg())

    def Flush(self):
        pass


class ListCounter(Counter):
    """
        An abstract class for collecting counters...
        the behaviour of this counter (and it's children if they don't
        override Flush() is to clean the buffer in every flush..
        so for ex. if the Counter is Flush()ed every 15 seconds
        Value() will return avg, max or min value for the last 15 seconds
        and then the values will be reset.
        if you want to change this behaviour, inherit from this class (or it's children)
        and override Flush()
    """

    def __init__(self, name, parent):
        Counter.__init__(self, name, parent)
        self.counter = []

    def Reset(self):
        self.counter = []

    def Add(self, value = 1):
        if len(self.counter) == 0:
            self.counter.append(value)
        else:
            self.counter.append(self.counter[-1] + value)

    def Dec(self, value = 1):
        if len(self.counter) == 0:
            self.counter.append(value)
        else:
            self.counter.append(self.counter[-1] - value)

    def Flush(self):
        Counter.Flush(self)
        self.counter = []

    def Set(self, value):
        self.counter.append(value)

    def Value(self):
        raise RuntimeError('virtual method, must override')


class AvgCounter(ListCounter):

    def __init__(self, name, parent):
        ListCounter.__init__(self, name, parent)

    def Value(self):
        """ return the average of the values in self.counter """
        result = 0
        if len(self.counter) == 0:
            result = 0
        else:
            for s in self.counter:
                result += s

            result /= len(self.counter)
        return result


class MaxCounter(ListCounter):

    def __init__(self, name, parent):
        ListCounter.__init__(self, name, parent)

    def Value(self):
        """ return the max value in self.counter """
        if len(self.counter) == 0:
            return 0
        max = self.counter[0]
        for s in self.counter:
            if s > max:
                max = s

        return max


class MinCounter(ListCounter):

    def __init__(self, name, parent):
        ListCounter.__init__(self, name, parent)

    def Value(self):
        if len(self.counter) == 0:
            return 0
        min = self.counter[0]
        for s in self.counter:
            if s < min:
                min = s

        return min


class CoreCounterService(service.Service):
    """ The implementation of the actual Counter service """
    __exportedcalls__ = {'CreateCounter': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'DestroyCounter': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'GetCounter': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'SetFlushInterval': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'GetFlushInterval': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'StartLogging': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'StopLogging': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'GetCountersList': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER],
     'IsLogging': [ROLE_SERVICE | ROLE_ADMIN | ROLE_PROGRAMMER]}
    __guid__ = 'svc.counter'
    __configvalues__ = {'countersInterval': 15,
     'logStart': 0}

    def Run(self, memStream = None):
        self.counters = []
        self.timer = None
        if self.logStart:
            self.StartLogging()

    def GetHtmlStateDetails(self, k, v, detailed):
        import htmlwriter
        if k == 'socket':
            if detailed:
                hd = []
                li = []
                li.append(['Listen Port', 80])
                return (k, htmlwriter.GetTable(hd, li, useFilter=True))
        elif k == 'counters':
            if detailed:
                hd = ['Name',
                 'Value',
                 'Parent',
                 'Filename',
                 'Log Channel']
                li = []
                for each in self.counters:
                    li.append([each.name,
                     each.counter,
                     each.parent,
                     each.filename,
                     each.logChannel])

                return (k, htmlwriter.GetTable(hd, li, useFilter=True))
            else:
                v = ''
                comma = ''
                for each in self.counters:
                    v = v + comma + each.name + '=' + strx(each.counter)
                    comma = ', '

                return (k, v)
        else:
            if k == 'countersInterval':
                desc = 'The time in secounds between logging counter values, assuming that counter logging is started in the first place.'
                if self.logStart:
                    desc = 'Thus as the service is currently configured, %d seconds will pass between each log operation' % v
                else:
                    desc = 'Thus if you would enable counter logging, %d seconds would pass between each log operation as the service is currently configured.' % v
                return ('Counter Interval', desc)
            if k == 'logStart':
                desc = 'Whether or not counter logging should be started up when the service is started.  If 0, then logging will not be started, otherwise it will be.  '
                if v:
                    desc = desc + 'The counter service is currently configured in such a manner that logging will be started'
                else:
                    desc = desc + 'The counter service is currently configured in such a manner that logging will <b>not</b> be started'
                return ('Start Logging?', desc)

    def Stop(self, memStream):
        pass

    def Flush(self):
        """
            Flushes all counters tracked by this service
        """
        for s in self.counters:
            s.Flush()

    def FindCounter(self, name):
        """
            Returns the counter instance with the specified name.
            Returns None if it does not exists in the service.
        """
        for s in self.counters:
            if s.name == name:
                return s

    def CreateCounter(self, name, type = 'normal'):
        """
            Add a new counter to the counter service.
            The type parameter can be "normal", "traffic", "avg", "max". Default is "normal"
            If a counter with the name alredy exists, it is returned and a new one is not created
        """
        counter = self.FindCounter(name)
        if counter:
            return counter
        if type == 'normal':
            counter = Counter(name, self)
        elif type == 'traffic':
            counter = TrafficCounter(name, self)
        elif type == 'statistic':
            counter = StatCounter(name, self)
        elif type == 'avg':
            counter = AvgCounter(name, self)
        elif type == 'max':
            counter = MaxCounter(name, self)
        else:
            raise RuntimeError('Countertype %s not supported' % type)
        self.counters.append(counter)
        return counter

    def AddCounter(self, counter):
        """
            Add the counter instance to the counter service
        """
        self.counters.append(counter)

    def GetCounter(self, name):
        """
            Returns the counter instance with the specified name.
            Returns None if it does not exists in the service
        """
        for s in self.counters:
            if s.name == name:
                return s

    def DestroyCounter(self, name):
        """
            Removed the counter with the specified name from the counter service
        """
        found = None
        for s in self.counters:
            if s.name == name:
                found = s
                break

        if found != None:
            self.counters.remove(found)

    def StartLogging(self):
        """
            Starts periodic flushing of all the counters
        """
        uthread.new(self.StartLogging_thread).context = 'counterService::FlushDaemon'

    def StartLogging_thread(self):
        """
            Counter flushing worker thread function. Started with StartLogging
        """
        self.logStart = 1
        while 1:
            blue.pyos.synchro.SleepWallclock(self.countersInterval * 1000)
            if not self.logStart:
                return
            self.Flush()

    def StopLogging(self):
        """
            Terminates the counter flushing worker thread
        """
        self.logStart = 0

    def IsLogging(self):
        """
            Returns True if logging is enabled
        """
        return self.logStart

    def GetFlushInterval(self):
        """
            Returns how often the counters are flushed. The value returned is in seconds.
        """
        return self.countersInterval

    def SetFlushInterval(self, interval):
        """
            Sets how frequently the counters should be flushed. The value is in seconds.
        """
        self.countersInterval = interval

    def GetCountersList(self):
        """
            Returns a tuple of 2lists. The First one contains all the name of the counters, and the seconds contains the current value of the respective counter
        """
        titleList = []
        valueList = []
        for s in self.counters:
            titleList.append(s.name)
            valueList.append(s.Value())

        return (titleList, valueList)
