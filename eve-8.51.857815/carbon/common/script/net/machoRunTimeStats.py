#Embedded file name: carbon/common/script/net\machoRunTimeStats.py
import sys
import blue
import uthread
import collections
import string
BASE_SAMPLE_RATE = 1000
GLOBAL_SAMPLE_PERIODS = 5
SAMPLE_RATE = GLOBAL_SAMPLE_PERIODS * BASE_SAMPLE_RATE
HISTORY_LENGHT = 2000

class MachoRunTimeStats:
    """
    Tracks runtime statistics about machonet.
    """
    __guid__ = 'macho.MachoRunTimeStats'

    def __init__(self, transportsByID):
        """
        pre:
            transportsByID maps from IDs to transport objects, each having a 'transport' field referring
            to a (GPCS SocketTransport-derived) object with 'stats...' statistics fields.
        """
        self.stop = False
        self.worker = None
        self.transportsByID = transportsByID
        self.socketStatsEnabled = prefs.GetValue('socketStatsEnabled', False)

    def Enable(self):
        self.stop = False
        self.last = [0,
         0,
         0,
         0,
         0,
         0,
         0,
         0]
        self.maxValues = [0,
         0,
         0,
         0,
         0,
         0,
         0,
         0]
        self.history = collections.deque(maxlen=HISTORY_LENGHT)
        self.packetsSendPerSecond = 0
        self.packetsReceivedPerSecond = 0
        self.totalPacketsPerSecond = 0
        self.KBIn = 0
        self.KBOut = 0
        self.movementPacketsReceived = 0
        self.movementPacketsSent = 0
        self.movementPacketsReceivedSize = 0
        self.movementPacketsSentSize = 0
        self.maxPacketsSendPerSecond = 0
        self.maxPacketsReceivedPerSecond = 0
        self.maxTotalPacketsPerSecond = 0
        self.maxKBIn = 0
        self.maxKBOut = 0
        self.maxMovementPacketsReceived = 0
        self.maxMovementPacketsSent = 0
        self.maxMovementPacketsReceivedSize = 0
        self.maxMovementPacketsSentSize = 0
        self.lastupdate = blue.os.GetWallclockTime()
        self.worker = uthread.new(self.Worker, self.transportsByID)

    def Disable(self):
        self.stop = True
        if self.worker:
            self.worker.kill()
            self.worker = None

    def Worker(self, transportsByID):
        numSamplePeriods = 0
        while not self.stop:
            delta = blue.os.TimeDiffInMs(self.lastupdate, blue.os.GetWallclockTime()) / 1000L
            self.lastupdate = blue.os.GetWallclockTime()
            if numSamplePeriods % GLOBAL_SAMPLE_PERIODS == 0:
                values = self.last[:]
                mn = sm.services['machoNet']
                self.last[0] = mn.dataSent.Count()
                self.last[1] = mn.dataReceived.Count()
                self.last[2] = mn.dataSent.Current()
                self.last[3] = mn.dataReceived.Current()
                self.last[4] = blue.statistics.GetSingleStat('Aperture/PacketsSent')
                self.last[5] = blue.statistics.GetSingleStat('Aperture/PacketsReceived')
                self.last[6] = blue.statistics.GetSingleStat('Aperture/PacketsSentSize')
                self.last[7] = blue.statistics.GetSingleStat('Aperture/PacketsReceivedSize')
                if delta != 0:
                    self.packetsSendPerSecond = float(self.last[0] - values[0]) / delta
                    self.packetsReceivedPerSecond = float(self.last[1] - values[1]) / delta
                    self.totalPacketsPerSecond = self.packetsSendPerSecond + self.packetsReceivedPerSecond
                    self.KBIn = float(self.last[2] - values[2]) / delta
                    self.KBOut = float(self.last[3] - values[3]) / delta
                    self.movementPacketsSent = float(self.last[4] - values[4]) / delta
                    self.movementPacketsReceived = float(self.last[5] - values[5]) / delta
                    self.movementPacketsSentSize = float(self.last[6] - values[6]) / delta
                    self.movementPacketsReceivedSize = float(self.last[7] - values[7]) / delta
                    self.maxPacketsSendPerSecond = max(self.maxPacketsSendPerSecond, self.packetsSendPerSecond)
                    self.maxPacketsReceivedPerSecond = max(self.maxPacketsReceivedPerSecond, self.packetsReceivedPerSecond)
                    self.maxTotalPacketsPerSecond = max(self.maxTotalPacketsPerSecond, self.totalPacketsPerSecond)
                    self.maxKBIn = max(self.maxKBIn, self.KBIn)
                    self.maxKBOut = max(self.maxKBOut, self.KBOut)
                    self.maxMovementPacketsReceived = max(self.maxMovementPacketsReceived, self.movementPacketsReceived)
                    self.maxMovementPacketsSent = max(self.maxMovementPacketsSent, self.movementPacketsSent)
                    self.maxMovementPacketsReceivedSize = max(self.maxMovementPacketsReceivedSize, self.movementPacketsReceivedSize)
                    self.maxMovementPacketsSentSize = max(self.maxMovementPacketsSentSize, self.movementPacketsSentSize)
                    self.history.append((blue.os.GetWallclockTime(),
                     self.packetsSendPerSecond,
                     self.packetsReceivedPerSecond,
                     self.KBIn,
                     self.KBOut,
                     self.movementPacketsReceived,
                     self.movementPacketsSent,
                     self.movementPacketsReceivedSize,
                     self.movementPacketsSentSize))
            numSamplePeriods += 1
            if self.socketStatsEnabled:
                for id, machoTransport in transportsByID.iteritems():
                    try:
                        tsp = machoTransport.transport
                        if tsp is not None:
                            tsp.statsBytesRead.Sample()
                            tsp.statsBytesWritten.Sample()
                            tsp.statsPacketsRead.Sample()
                            tsp.statsPacketsWritten.Sample()
                    except AttributeError:
                        sys.exc_clear()

            blue.pyos.synchro.SleepWallclock(BASE_SAMPLE_RATE)


class EWMA(object):
    """
    Defines a set of exponential weighted moving averages, each initialized with its own _smoothing factor_, a
    number between 0 and 1. When a new sample _v_ is added to the EWMA, the n-th average _avgn_ is updated to
    the value _v_*_factorn_ + (1-_factorn_) * _avgn_, where _factorn_ is the n-th smoothing factor. The higher
    the smoothing factor, the greater the influence of the latest sample. Lower factors yield a less
    rapidly changing, "smoother" average. In any case, the influence of older samples decreases
    exponentially, hence the name of the statistic.
    
    The constructor takes the value to use as the initial average value. For higher smoothness factors,
    this value will "fade away" quickly, but for lower smoothness factors a more applicable initial
    value should be chosen.
    
    >>> avg = EWMA([0.05, 0.2, 0.5])
    >>> avg.averages
    [0.0, 0.0, 0.0]
    >>> avg.factors
    [0.05, 0.2, 0.5]
    >>> avg.Averages()
    [(0.0, 0.05), (0.0, 0.2), (0.0, 0.5)]
    >>> avg.AddSample(10)
    >>> avg.AddSample(20)
    >>> avg.averages
    [1.475, 5.6, 12.5]
    >>> avg.AddSample(-50)
    >>> avg.averages
    [-1.09875, -5.5200000000000005, -18.75]
    
    To get the factor that yields the approximate average for the last _N_ samples, use smoothing
    factor 2 / (_N_+1), for example: 0.18 to get the average for the last 10 samples. The
    FromSampleCounts() class method creates an EWMA by converting sample counts
    into smoothing factors in this manner.
    
    >>> x = EWMA.FromSampleCounts([1, 10, 100])
    >>> x.factors
    [1.0, 0.18181818181818182, 0.019801980198019802]
    
    The preceding example added samples directly to the EMWA.
    A more complex usage mode separates the accumulation of a running total of sample data
    and the sampling of the current running total into methods Add() and Sample(),
    respectively. This makes it easy to "bucket" and sample data at a lower rate than
    the individual samples are generated, f.ex. to sample events in time intervals.
    
    >>> x = EWMA([0.5], 20)
    >>> x.Add(5.0)
    >>> x.Add(2.5)
    >>> x.Add(2.5)
    >>> x.averages
    [20.0]
    >>> x.Sample()
    >>> x.averages
    [15.0]
    >>> x.Add(5.0)
    >>> x.Sample()
    >>> x.averages
    [10.0]
    
    inv:
        # all factors in [0, 1.0] (and factors are comparable to floats)
        all(0.0 <= f <= 1.0 for f in self.factors)
        # one average computed per factor
        len(self.averages) == len(self.factors)
    """
    __guid__ = 'macho.EWMA'

    def __init__(self, factors = None, initialAverage = 0.0, reprFormat = '%.2f'):
        """
        New EWMA with each factor average set to an initial value
        
        pre:
            all(0.0 <= f <= 1.0 for f in factors)
            all(isinstance(f, float) for f in factors)
            isinstance(reprFormat, string)                   # reprFormat string used in __repr__
            isinstance(initialAverage, (int,long,float)) # initialAverage gets converted to float
        post[self]:
            self.factors == factors
            all(avg == initialAverage for avg in self.averages)
        """
        self.factors = factors if factors else [0.1]
        self.averages = [ float(initialAverage) for n in range(0, len(self.factors)) ]
        self.runningTotal = 0
        self.reprFormat = reprFormat

    @classmethod
    def FromSampleCounts(cls, sampleCounts = None, initialAverage = 0.0):
        """
        Alternate constructor taking sample counts instead of smoothing factors,
        e.g. [5, 10] means: track the approximate average of the last 5 and the last
        10 samples.
        
        pre:
            isinstance(initialAverage, (int,long,float))
            all(cnt >= 1 for cnt in sampleCounts)
        """
        return EWMA([ 2.0 / (cnt + 1) for cnt in (sampleCounts if sampleCounts else [1]) ], initialAverage)

    def AddSample(self, v = 1):
        """
        Update each average in 'self' with the new measurement value 'v'
        pre:
            isinstance(v, (int,long,float))
        """
        self.averages = [ v * f + (1 - f) * avg for f, avg in zip(self.factors, self.averages) ]

    def Add(self, v = 1):
        """
        Adds 'v' to the current running total. Does _not_ affect the current average,
        the current running total is sampled using the Sample() method.
        pre:
            isinstance(v, (int,long,float))
        """
        if self.runningTotal is not None:
            self.runningTotal += v
        else:
            self.runningTotal = v

    def Sample(self, defaultRunningTotal = 0.0):
        """
        Updates each average in 'self' with the running total if not None, or
        else uses the 'defaultRunningTotal' as the effective running total,
        or does nothing if 'defaultRunningTotal' is None.
        
        pre:
            isinstance(defaultRunningTotal, (None,int,long,float))
        """
        if self.runningTotal is not None:
            self.AddSample(self.runningTotal)
            self.runningTotal = None
        elif defaultRunningTotal is not None:
            self.AddSample(defaultRunningTotal)

    def Averages(self):
        """
        Return a list of tuples (avg, f) for each factor and the corresponding average
        """
        return zip(self.averages, self.factors)

    def __repr__(self):
        """
        Returns a comma-separated list of current averages, with 
        """
        return string.join([ self.reprFormat % avg for avg in self.averages ], ', ')
