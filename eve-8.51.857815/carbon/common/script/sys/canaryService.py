#Embedded file name: carbon/common/script/sys\canaryService.py
"""

Watches out for the main application loop getting blocked.  A canary tasklet is run on the main
thread, and a second python thread then watches that this is being updated regularly.

 Alright, what type of load can we produce?
   - CPU Cycles; find prime numbers (takes up a small amount of memory as well)
   - Network latency; ping other nodes
"""
from service import *
import threading
import time
import stackless
import uthread
import blue
import traceback2 as traceback
import log
import sys

class CanaryService(Service):
    __guid__ = 'svc.canaryService'
    __displayname__ = 'Canary Service'
    __exportedcalls__ = {}
    __dependencies__ = []
    __notifyevents__ = []
    __configvalues__ = {'interval': 10,
     'threshold': 10,
     'debugBreak': 0}

    def Run(self, memStream = None):
        self.timestamp = 0
        self.mainThread = threading.current_thread()
        self.canaryTasklet = uthread.worker('canarySvc.canary', self.Canary)
        self.minerThread = threading.Thread(target=self.Miner)
        self.minerThread.start()

    def Stop(self, stream):
        if self.canaryTasklet:
            self.canaryTasklet.kill()
            self.canaryTasklet = None
        self.minerThread = None

    def Canary(self):
        while self.canaryTasklet is stackless.getcurrent():
            self.timestamp = time.time()
            blue.pyos.synchro.SleepWallclock(self.interval * 1000)

    def Miner(self):
        try:
            while self.minerThread is threading.current_thread():
                time.sleep(self.threshold)
                now = time.time()
                self.minerTimestamp = now
                if not self.timestamp:
                    continue
                next_timestamp = self.timestamp + self.interval
                late = now - next_timestamp
                if late < self.threshold:
                    continue
                self.Report(late)

        except:
            log.LogException('canaryService.Miner thread errored out')

    def Report(self, delay):
        report = ['Main thread %ss late (%ss past threshold):\n' % (delay, delay - self.threshold)]
        for tid, frame in sys._current_frames().iteritems():
            if tid != threading.current_thread().ident:
                report.extend(self.ReportThread(tid, frame))

        self.logChannel.Log(''.join(report), flag=log.LGWARN)
        if self.debugBreak:
            blue.win32.DebugBreak()

    def ReportThread(self, tid, frame):
        report = ['Thread %d:\n' % tid]
        if hasattr(frame, 'f_lineno'):
            stack = traceback.extract_stack(frame)
            report.extend(traceback.format_list(stack))
        else:
            report.append('No stack\n')
        return report
