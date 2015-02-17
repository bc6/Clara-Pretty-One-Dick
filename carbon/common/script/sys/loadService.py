#Embedded file name: carbon/common/script/sys\loadService.py
"""
Loads the server with pseudo simulated load

 Alright, what type of load can we produce?
   - CPU Cycles; find prime numbers (takes up a small amount of memory as well)
   - Network latency; ping other nodes
"""
import math
import itertools
from time import clock
from carbon.common.script.sys.service import *
import const
import blue
import blue.win32
import uthread
import random
from test.pystone import pystones

class LoadService(Service):
    __guid__ = 'svc.loadService'
    __displayname__ = 'Load Service'
    __exportedcalls__ = {'Ping': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'GetTotalStats': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'GatherStats': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'StartLoad': [ROLE_PROGRAMMER],
     'StopLoad': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'StartLoadOnAllNodes': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'StopLoadOnAllNodes': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'GetConfig': [ROLE_PROGRAMMER],
     'SetConfig': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'IsRunning': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'RemainingTime': [ROLE_SERVICE | ROLE_PROGRAMMER],
     'Calibrate': [ROLE_SERVICE | ROLE_PROGRAMMER]}
    __dependencies__ = ['machoNet']
    __notifyevents__ = []

    def __init__(self):
        Service.__init__(self)
        self.configVariables = ['pyStoneTasklets',
         'pyStonesPerSec',
         'pyStonesPerUnit',
         'netTasklets',
         'packetsP2S',
         'packetsS2P',
         'packetsS2S']
        self.pyStoneTasklets = 10
        self.pyStonesPerSec = 20000
        self.pyStonesPerUnit = 500
        self.netTasklets = 5
        self.packetsP2S = 150
        self.packetsS2P = 75
        self.packetsS2S = 50
        self.running = False
        self.ResetCounters()

    def GetConfig(self):
        """
        Return a dict with configurable values
        """
        return dict([ (v, getattr(self, v)) for v in self.configVariables ])

    def SetConfig(self, conf, updateOtherNodes = True):
        """
        Get dict with config values and update class variables. By
        default it updates all other connected nodes.
        """
        for v in self.configVariables:
            if v in conf:
                setattr(self, v, conf[v])

        if updateOtherNodes:
            for node in self.machoNet.GetConnectedNodes():
                self.session.ConnectToRemoteService('loadService', node).SetConfig(conf, False)

    def IsRunning(self):
        """
        Return True if the service is creating load.
        """
        return self.running

    def RemainingTime(self):
        """
        Returns time remaining if running, None if infinite
        """
        if self.duration is not None:
            return self.duration - (blue.os.GetWallclockTime() * 1e-07 - self.startTime)

    def StartLoadOnAllNodes(self, duration = None):
        """
        Start load on all services, including myself
        """
        self.session.ConnectToAllServices('loadService').StartLoad(duration)

    def StopLoadOnAllNodes(self):
        """
        Stop load on all services, including myself
        """
        self.session.ConnectToAllServices('loadService').StopLoad()

    def TaskletWrap(self, func):

        def Wrapped(*args, **kwds):
            try:
                func(*args, **kwds)
            finally:
                self.nTasklets -= 1
                blue.pyos.synchro.SleepWallclock(0)

        self.nTasklets += 1
        return Wrapped

    def StartLoad(self, duration = None):
        """
        Start load on current node. Spawns CPU and network worker threads.
        Optionally starts a shutdown counter that stops the service after
        duration seconds.
        """
        self.running = True
        self.startProcessTime = blue.pyos.taskletTimer.GetProcessTimes()
        self.startThreadTime = blue.pyos.taskletTimer.GetThreadTimes()
        self.ResetCounters()
        self.nTasklets = 0
        for t in range(self.pyStoneTasklets):
            uthread.worker('loadServiceService::CpuLoad::%s' % t, self.TaskletWrap(self.CpuCycleWorker))

        for t in range(self.netTasklets):
            uthread.worker('loadServiceService::NetworkTraffic::%s' % t, self.TaskletWrap(self.Network))

        self.startTime = blue.os.GetWallclockTime() * 1e-07
        self.duration = duration
        if duration:
            uthread.worker('loadServiceService::ShutdownCounter', self.ShutdownCounter, duration)

    def ShutdownCounter(self, duration):
        """
        Wait for duration seconds and then stop service. Used when the
        service the service should load the cluster only for a given
        amount of time.
        """
        blue.pyos.synchro.SleepWallclock(int(duration * 1000))
        self.StopLoad()

    def StopLoad(self):
        """
        Stop load on current node.
        """
        self.running = False
        while self.nTasklets:
            self.LogInfo('Waiting for %d tasklets to finish' % self.nTasklets)
            blue.pyos.synchro.Yield()

        self.LogInfo('All tasklets finished')
        endProcessTime = blue.pyos.taskletTimer.GetProcessTimes()
        endThreadTime = blue.pyos.taskletTimer.GetThreadTimes()
        for k, v in self.startProcessTime.iteritems():
            endProcessTime[k] -= v

        for k, v in self.startThreadTime.iteritems():
            endThreadTime[k] -= v

        self.cpuStats['process'] = endProcessTime
        self.cpuStats['thread'] = endThreadTime

    def IntervalDispatcher(self, interval, stats, func):
        """
        Call func every interval ms. This is not the same as executing func
        and sleeping for ms nor sleeping for "ms - execution time" as this
        dispatcher tries execute func every real-time ms.
        """

        def times(dt):
            """a generator returning jittered times"""
            start = clock()
            for i in itertools.count():
                yield start + (i + random.random()) * dt

        loopCount = 0
        slowCount = 0
        if interval:
            i = times(interval)
            while self.running:
                now = clock()
                when = i.next()
                ms = int((when - now) * 1000)
                if ms > 0:
                    blue.pyos.synchro.SleepWallclock(ms)
                    now = clock()
                if now > when + interval:
                    slowCount += 1
                    while now > when + interval:
                        when = i.next()

                func()
                loopCount += 1

        else:
            while self.running:
                func()
                loopCount += 1

        stats['loopCount'] += loopCount
        stats['slowCount'] += slowCount
        self.LogInfo('IntervalDispatcher finished. %s of %s %s calls were slow (%s%%)' % (slowCount,
         loopCount,
         func.__name__,
         int(slowCount / float(loopCount) * 100)))

    def Calibrate(self, duration = 2):
        """
        See how many increments we can do per duration seconds.
        
        WARNING: This function will run for duration seconds without yield'ing !
        """
        startTime = blue.os.GetWallclockTimeNow()
        stepCount = 0
        while blue.os.GetWallclockTimeNow() - startTime < duration * 10000000:
            stepCount += 1
            pystones(self.pyStonesPerUnit)

        return int(stepCount * self.pyStonesPerUnit / duration)

    def CpuCycleWorker(self):
        """
        Calculate how many loop increments I should perform and
        dispatch work.
        """
        taskletLoad = float(self.pyStonesPerSec) / self.pyStoneTasklets
        interval = 1.0 / (taskletLoad / self.pyStonesPerUnit)
        self.LogInfo('CPU Tasklet. Will run %s pyStones every %ss' % (self.pyStonesPerUnit, interval))
        blue.pyos.synchro.SleepWallclock(int(random.random() * interval * 1000))

        def CpuWork():
            pystones(self.pyStonesPerUnit)

        self.IntervalDispatcher(interval, self.cpuStats, CpuWork)

    def Network(self):
        """
        Figure out how many packets we should send, and to whom.
        """
        if self.machoNet.GetNodeID() > const.maxNodeID:
            solPackets = float(self.packetsP2S) / self.netTasklets
            proxyPackets = 0
        else:
            proxyPackets = float(self.packetsS2P) / self.netTasklets
            solPackets = float(self.packetsS2S) / self.netTasklets
        if solPackets:
            nodes = self.machoNet.GetConnectedSolNodes()
            nodes = [ (node, self.session.ConnectToRemoteService('loadService', node)) for node in nodes ]
            randomNodes = self.NodeRandomizer(nodes)

            def func():
                self.NetworkSendPacket(randomNodes)

            interval = 1.0 / solPackets if solPackets > 0.0 else 0.0
            uthread.worker('loadServiceService::NetworkTraffic::ToSolServers', self.TaskletWrap(self.IntervalDispatcher), interval, self.netStats, func)
        if proxyPackets:
            nodes = self.machoNet.GetConnectedProxyNodes()
            nodes = [ (node, self.session.ConnectToRemoteService('loadService', node)) for node in nodes ]
            randomNodes = self.NodeRandomizer(nodes)

            def func():
                self.NetworkSendPacket(randomNodes)

            interval = 1.0 / proxyPackets if proxyPackets > 0.0 else 0.0
            uthread.worker('loadServiceService::NetworkTraffic::ToProxyServers', self.TaskletWrap(self.IntervalDispatcher), interval, self.netStats, func)

    def NetworkSendPacket(self, randomNodes):
        """
        Connect to a given node and play ping-pong. The packet is a list
        of integers, length determined by a gaussian distribution having
        mean PACKET_SIZE and variance PACKET_VAR
        """
        PACKET_SIZE = 20
        PACKET_VAR = 2
        packet = range(int(random.gauss(PACKET_SIZE, PACKET_VAR)))
        try:
            node, conn = randomNodes.next()
        except StopIteration:
            self.LogWarn('No nodes returned from randomNodes')
            return

        packetSendTime = blue.os.GetWallclockTimeNow()
        conn.Ping(packet)
        packetReceiveTime = blue.os.GetWallclockTimeNow()
        self.UpdateNetworkStats(node, packetReceiveTime - packetSendTime)

    def NodeRandomizer(self, nodes):
        """
        Randomizes a node list and yield forever. Should return all nodes
        the same number of times.
        """
        if not nodes:
            return
        nodes = nodes[:]
        while True:
            random.shuffle(nodes)
            for node in nodes:
                yield node

    def Ping(self, packet):
        """
        Play ping-pong. Receives a dummy packet and sends it back the round trip.
        """
        return packet

    def ResetCounters(self):
        """
        Resets both local and total counters
        """
        self.cpuStats = {'loopCount': 0,
         'slowCount': 0,
         'pyStonesPerSec': 0}
        self.netStats = {'loopCount': 0,
         'slowCount': 0}
        self.totalStats = {}

    def UpdateNetworkStats(self, node, latency):
        """
        Log packet info by adding to local stats. Called after every
        packet receive.
        """
        if node not in self.netStats:
            self.netStats[node] = {}
            self.netStats[node]['totalPackets'] = 0
            self.netStats[node]['totalLatency'] = 0
            self.netStats[node]['totalLatencySq'] = 0
            self.netStats[node]['maxLatency'] = None
            self.netStats[node]['minLatency'] = None
        stats = self.netStats[node]
        latency *= 1e-07
        stats['totalPackets'] += 1
        stats['totalLatency'] += latency
        stats['totalLatencySq'] += latency * latency
        if stats['maxLatency'] is None:
            stats['maxLatency'] = stats['minLatency'] = latency
        elif latency > stats['maxLatency']:
            stats['maxLatency'] = latency
        elif latency < stats['minLatency']:
            stats['minLatency'] = latency

    def GetNetworkStats(self):
        """
        Populates and returns local stats dict with average and stdev
        """
        for node in self.netStats:
            if node in ('loopCount', 'slowCount'):
                continue
            self.netStats[node]['average'] = self.netStats[node]['totalLatency'] / self.netStats[node]['totalPackets']
            self.netStats[node]['stdev'] = math.sqrt((self.netStats[node]['totalLatencySq'] - self.netStats[node]['totalLatency'] * self.netStats[node]['average']) / self.netStats[node]['totalPackets'])

        return self.netStats

    def GetCpuStats(self):
        """
        Populates and returns local stats dict with CPU usage percentage
        """
        for stats in self.cpuStats.values():
            if type(stats) is not dict:
                continue
            if 'cpu' in stats and 'wallclock' in stats:
                stats['cpuPercentage'] = float(stats['cpu']) / stats['wallclock'] * 100

        if 'loopCount' in self.cpuStats and 'process' in self.cpuStats:
            self.cpuStats['pyStonesPerSec'] = self.pyStonesPerUnit * self.cpuStats['loopCount'] / (self.cpuStats['process']['wallclock'] * 1e-07)
        return self.cpuStats

    def GetTotalStats(self):
        """
        Wrapper
        """
        return {'cpu': dict(self.GetCpuStats()),
         'net': dict(self.GetNetworkStats())}

    def GatherStats(self):
        """
        Calls all connected nodes; gathers, populates and returns total
        node network stats.
        """
        for node in self.machoNet.GetConnectedNodes():
            self.totalStats[node] = self.machoNet.ConnectToRemoteService('loadService', node).GetTotalStats()

        self.totalStats[self.machoNet.GetNodeID()] = self.GetTotalStats()
        return self.totalStats
