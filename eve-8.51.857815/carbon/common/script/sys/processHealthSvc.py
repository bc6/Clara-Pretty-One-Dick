#Embedded file name: carbon/common/script/sys\processHealthSvc.py
"""
Contains data collector service that periodiaclly collects status data and
stores for online retrieval Collected data is written to specified file every 10 minutes and when
service is shutdown
Prefs.ini variable
ProcessHealthLogPath=c: emp
"""
import _socket
import service
import base
import util
import blue
import bluepy
import uthread
import log
import sys
import os
import copy
import gpcs

class ProcessHealthSvc(service.Service):
    """
    ProcessHealthSvc monitoring class, runs collection functions periodically
    and delivers online through GetProcessInfo.
    Accumulated loglines are stored with a call to WriteLog (from machonet, and
    servicemanager)
    """
    __guid__ = 'svc.processHealth'
    __servicename__ = 'processHealth'
    __displayname__ = 'Process Health Service'
    __dependencies__ = ['machoNet']
    __notifyevents__ = ['ProcessShutdown']

    def ProcessShutdown(self):
        self.WriteLog(20, True)

    def CreateFakeData(self):
        import util
        import random
        import math
        data = util.KeyVal
        data.timeData = []
        data.procCpuData = []
        data.threadCpuData = []
        data.bluememData = []
        data.pymemData = []
        data.memData = []
        data.schedData = []
        data.crestRequests = []
        t0 = blue.os.GetWallclockTime() - 2 * const.DAY
        tp = t0
        delay = 0
        lag = 0
        for i in xrange(0, 5000):
            t0 += 10 * const.SEC
            if i % 400 == 10:
                lag = random.randint(0, 300)
            if lag:
                lag -= 1
            data.timeData.append(t0)
            data.procCpuData.append(math.sin(i / 20.0) * 100)
            data.threadCpuData.append(math.cos(i / 100.0) * 100)
            data.bluememData.append(i)
            data.pymemData.append(math.sin(i / 1000.0) * 1000)
            data.memData.append(i)
            data.schedData.append((math.sin(i * i / 100.0) * 1000,
             math.cos(i / 50.0) * 1000,
             math.sin(i / 10.0) * 100,
             math.sin(i / 100.0) * 100,
             i,
             i))
            data.crestRequests.append(math.cos(i / 100.0) * 100)
            if not lag:
                logline = {'pyDateTime': t0 + 5 * const.SEC,
                 'bytesReceived': i * 1000,
                 'bytesSent': i * 1000,
                 'packetsReceived': i * 10,
                 'packetsSent': i * 10,
                 'sessionCount': math.pow(math.sin(i * i / 100.0), 2) * 1000,
                 'serviceCalls': 10,
                 'tidiFactor': 1.0,
                 'crestRequests': math.cos(i / 100.0) * 100}
            self.data = data
            self.logLines.append(logline)

    def __init__(self, *args):
        service.Service.__init__(self, *args)
        self.logLines = []
        self.startDateTime = util.FmtDateEng(blue.os.GetWallclockTime(), 'ss')
        self.cache = util.KeyVal
        self.cache.cacheTime = 0
        self.cache.minutes = 0
        self.cache.cache = []
        self.lastLoggedLine = 0
        self.lastStartPos = 0
        self.columnNames = ('dateTime', 'pyDateTime', 'procCpu', 'threadCpu', 'blueMem', 'pyMem', 'virtualMem', 'runnable1', 'runnable2', 'watchdog time', 'spf', 'serviceCalls', 'callsFromClient', 'crestRequests')

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        uthread.new(self.RunWorkerProcesses).context = 'svc.processHealth'

    def GetSeriesNames(self):
        names = []
        if len(self.logLines) > 0:
            names = self.logLines[0].keys()
            if names.count('dateTime') > 0:
                names.remove('dateTime')
        names.extend(['procCpu',
         'threadCpu',
         'blueMem',
         'pyMem',
         'virtualMem',
         'runnable1',
         'runnable2',
         'watchdog time',
         'spf'])
        return names

    def GetSessionCount(self):
        """
        get number of client sessions
        """
        allsc = base.GetSessions()
        sc = len(filter(lambda x: x.userid is not None and hasattr(x, 'clientID'), allsc))
        return sc

    def FindClosestPythonLine(self, blueLine, startPos = 0):
        logLinesCopy = copy.copy(self.logLines[startPos:])
        if len(logLinesCopy) == 0:
            return (None, 0)
        if blueLine['dateTime'] <= logLinesCopy[0]['pyDateTime']:
            return (logLinesCopy[0], 0)
        if blueLine['dateTime'] >= logLinesCopy[-1]['pyDateTime']:
            return (logLinesCopy[-1], len(logLinesCopy) + startPos)
        for line in xrange(0, len(logLinesCopy) - 1):
            blue.pyos.BeNice()
            t1 = logLinesCopy[line]['pyDateTime']
            t2 = logLinesCopy[line + 1]['pyDateTime']
            if t1 <= blueLine['dateTime'] < t2:
                return (logLinesCopy[line], line + startPos)

        return (None, 0, 0)

    def GetBlueDataAsDictList(self, minutes = 0):
        data = bluepy.GetBlueInfo(minutes, isYield=False)
        ret = []
        for i in xrange(0, len(data.timeData)):
            fps, nrRunnable1, nrYielders, nrSleepWallclockers, watchDogTime, nrRunnable2 = data.schedData[i]
            spf = 1.0 / fps if fps > 0.1 else 0
            ret.append({'dateTime': data.timeData[i],
             'procCpu': data.procCpuData[i],
             'threadCpu': data.threadCpuData[i],
             'blueMem': data.bluememData[i],
             'pyMem': data.pymemData[i],
             'virtualMem': data.memData[i],
             'runnable1': nrRunnable1,
             'runnable2': nrRunnable2,
             'watchdog time': watchDogTime,
             'spf': spf})

        return ret

    def GetAllLogs(self, logAll = True):
        logs = self.GetProcessInfo()
        return self.FormatLog(logs, logAll)

    def GetProcessInfo(self, minutes = 0, useIncrementalStartPos = False):
        """
        returns cpu, memory and network statistics as list of dicts.
        """
        uthread.Lock(self)
        try:
            if blue.os.GetWallclockTime() - self.cache.cacheTime < 25 * const.SEC and self.cache.minutes == minutes:
                return self.cache.cache
            startTime = blue.os.GetWallclockTime()
            blueLines = self.GetBlueDataAsDictList(minutes)
            lastLine = {}
            if useIncrementalStartPos:
                startPos = self.lastStartPos
            else:
                startPos = 0
            for blueLine in blueLines:
                pyLine, startPos = self.FindClosestPythonLine(blueLine, startPos)
                if pyLine:
                    lastLine = pyLine
                    blueLine.update(pyLine)
                else:
                    blueLine.update(lastLine)

            diff = (blue.os.GetWallclockTime() - startTime) / float(const.SEC)
            self.lastStartPos = startPos
            self.cache.minutes = minutes
            self.cache.cacheTime = blue.os.GetWallclockTime()
            self.cache.cache = blueLines
            return blueLines
        finally:
            uthread.UnLock(self)

    def RunWorkerProcesses(self):
        seconds = 0
        while self.state == service.SERVICE_RUNNING:
            if prefs.GetValue('disableProcessHealthService', 0):
                self.LogWarn('Process Health Service is disabled in prefs. Disabling loop.')
                return
            blue.pyos.synchro.SleepWallclock(10000)
            try:
                seconds += 10
                self.DoOnceEvery10Secs()
                if seconds % 600 == 0:
                    self.DoOnceEvery10Minutes()
            except:
                log.LogException()
                sys.exc_clear()

    def LogCpuMemNet(self):
        """
        Collect cpu, memory and network statistics, results are added to the
        logLines dict.
        """
        stats = _socket.getstats()
        netBytesRead = stats['BytesReceived']
        netBytesWritten = stats['BytesSent']
        netReadCalls = stats['PacketsReceived']
        netWriteCalls = stats['PacketsSent']
        sessionCount = self.GetSessionCount()
        serviceCalls = sum(gpcs.CoreServiceCall.__recvServiceCallCount__.itervalues())
        callCounter = sm.GetService('machoNet').callCounter
        crestSvc = sm.GetServiceIfStarted('crestapiService')
        crestRequests = sum(crestSvc.GetRemoteHandlerUsageData()['returnCodeStats'].itervalues()) if crestSvc else 0
        callsFromClient = 0
        for k in callCounter.iterkeys():
            if k[0] == const.ADDRESS_TYPE_CLIENT:
                callsFromClient = callCounter[k]
                break

        logline = {'pyDateTime': blue.os.GetWallclockTime(),
         'bytesReceived': netBytesRead,
         'bytesSent': netBytesWritten,
         'packetsReceived': netReadCalls,
         'packetsSent': netWriteCalls,
         'sessionCount': sessionCount,
         'tidiFactor': blue.os.simDilation,
         'serviceCalls': serviceCalls,
         'callsFromClient': callsFromClient,
         'crestRequests': crestRequests}
        self.logLines.append(logline)

    def DoOnceEvery10Secs(self):
        self.LogCpuMemNet()

    def DoOnceEvery10Minutes(self):
        self.WriteLog(20, True)

    def FormatLog(self, logLines, logAll = False):
        """
        Generate the formatted log (tab-delimited).
        """
        txt = ''
        allColumnNames = self.columnNames + tuple(sorted(set(logLines[0].iterkeys()).difference(self.columnNames)))
        if self.lastLoggedLine == 0 or logAll:
            for name in allColumnNames:
                txt += '%s\t' % name

            txt += '\n'
        for l in xrange(0, len(logLines) - 1):
            logLine = logLines[l]
            if logLine['dateTime'] > self.lastLoggedLine or logAll:
                self.lastLoggedLine = logLine['dateTime']
                for name in allColumnNames:
                    if name in ('dateTime', 'pyDateTime'):
                        txt += '%s\t' % util.FmtDateEng(logLine[name])
                    elif round(logLine[name], 2).is_integer():
                        txt += '%s\t' % str(logLine[name])
                    else:
                        txt += '%.4f\t' % logLine[name]

                txt += '\n'

        return txt

    def WriteLog(self, minutes = 0, useIncrementalStartPos = False):
        dumpPath = prefs.GetValue('ProcessHealthLogPath', None)
        if dumpPath is None:
            self.LogInfo('Will not dump processhealth info since it is not configured in prefs (ProcessHealthLogPath)')
            return
        self.LogInfo('WriteLog', minutes, useIncrementalStartPos)
        startTime = blue.os.GetWallclockTime()
        computerName = blue.pyos.GetEnv().get('COMPUTERNAME', 'unknown')
        nodeID = sm.GetService('machoNet').GetNodeID()
        nodeIndex = sm.GetService('machoNet').nodeIndex
        if nodeID is None:
            nodeID = 0
        logLines = self.GetProcessInfo(minutes, useIncrementalStartPos)
        txt = self.FormatLog(logLines)
        if not os.path.exists(dumpPath):
            os.makedirs(dumpPath)
        fileName = 'PHS %s %s %s %s %s %s.txt' % (computerName,
         nodeIndex,
         nodeID,
         boot.role,
         blue.os.pid,
         self.startDateTime)
        fileName = os.path.join(dumpPath, fileName.replace(':', '.').replace(' ', '.'))
        f = open(fileName, 'a+')
        f.write(txt)
        f.close()
        diff = (blue.os.GetWallclockTime() - startTime) / float(const.SEC)
        self.LogInfo('Finished writing out %s entries from processHealth into %s in %.3f seconds' % (len(logLines), fileName, diff))
