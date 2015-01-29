#Embedded file name: notifications/client/controls\autoCloser.py
__author__ = 'aevar'
import uthread
import blue

class AutoCloser(object):

    def __init__(self, area, closeCallback, monitorObject = None, thresholdInSeconds = 1.0, buffer = 5):
        self.originalArea = area
        self.buffer = buffer
        if monitorObject:
            self.monitorObject = monitorObject
            self.UpdateMonitorObject()
        else:
            x, y, w, h = area
            b = self.buffer
            self.area = (x - b,
             y - b,
             x + w + b * 2,
             y + h + b * 2)
        self.lastOutOfAreaTime = 0
        self.lastInAreaTime = 0
        self.lastSeenInArea = True
        self.closeThreshold = thresholdInSeconds * 10000000
        self.shouldRun = True
        self.closeCallback = closeCallback

    def UpdateMonitorObject(self):
        if self.monitorObject:
            x, y, w, h = self.monitorObject.GetAbsolute()
            b = self.buffer
            self.area = (x - b,
             y - b,
             x + w + b * 2,
             y + h + b * 2)

    def monitor(self):
        self.lastInAreaTime = blue.os.GetWallclockTime()
        uthread.new(self.CheckBoundaries)

    def EndThis(self):
        self.shouldRun = False
        self.closeCallback(self)

    def IsMouseInArea(self):
        x, y, x2, y2 = self.area
        return x < uicore.uilib.x < x2 and y < uicore.uilib.y < y2

    def CheckBoundaries(self):
        while self.shouldRun:
            self.UpdateMonitorObject()
            if self.IsMouseInArea():
                self.lastInAreaTime = blue.os.GetWallclockTime()
                self.lastSeenInArea = True
            else:
                self.lastOutOfAreaTime = blue.os.GetWallclockTime()
                self.lastSeenInArea = False
            if not self.lastSeenInArea:
                diff = self.lastOutOfAreaTime - self.lastInAreaTime
                if diff > self.closeThreshold:
                    self.EndThis()
            blue.synchro.Yield()

        self.monitorObject = None

    def Abort(self):
        self.shouldRun = False
