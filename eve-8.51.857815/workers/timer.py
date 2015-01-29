#Embedded file name: workers\timer.py
from carbon.common.lib.const import MSEC

class Timer(object):

    def __init__(self, GetTime, Sleep, maxSleepTime):
        self.maxSleepTime = maxSleepTime
        self.GetTime = GetTime
        self.Sleep = Sleep

    def SleepUntil(self, wakeUpTime, minSleep = 5000):
        sleepTime = wakeUpTime - self.GetTime()
        if sleepTime > 0:
            while True:
                sleepTime = wakeUpTime - self.GetTime()
                if sleepTime <= self.maxSleepTime:
                    self.Sleep(sleepTime / MSEC)
                    break
                else:
                    self.Sleep(self.maxSleepTime / MSEC)

        else:
            self.Sleep(minSleep)
