#Embedded file name: notifications/client/generator\simpleRandomDistributor.py
import uthread
import random
import blue

class SimpleRandomDistributer(object):

    def __init__(self, mininterval, maxinterval, generateCallback, finishedCallback, nowTimeProviderFunction, step = 1000, oddsOfEventPerCheck = 10, generateMax = 100):
        self.mininterval = mininterval * 10000
        self.maxinterval = maxinterval * 10000
        self.timeSinceLastDistribution = 0
        self.lastDistributionTimeStamp = 0
        self.updateThread = None
        self.callback = generateCallback
        self.finishedCallback = finishedCallback
        self.nowTimeProviderFunction = nowTimeProviderFunction
        self.shouldRun = True
        self.stepCheckInMs = step
        self.oddOfEventPerCheck = 100 - oddsOfEventPerCheck
        self.generateMax = generateMax
        self.currentlyGenerated = 0

    def Start(self):
        uthread.new(self.Update)

    def _Generate(self):
        self.currentlyGenerated = self.currentlyGenerated + 1
        self.lastDistributionTimeStamp = self.nowTimeProviderFunction()
        self.callback(self.currentlyGenerated)

    def GetTimePassed(self):
        return self.nowTimeProviderFunction() - self.lastDistributionTimeStamp

    def _ShouldGenerate(self):
        return random.randint(0, 100) > self.oddOfEventPerCheck

    def Update(self):
        while self.shouldRun and self.currentlyGenerated < self.generateMax:
            timePassed = self.GetTimePassed()
            if timePassed > self.mininterval:
                if timePassed > self.maxinterval:
                    self._Generate()
                elif self._ShouldGenerate():
                    self._Generate()
            blue.synchro.Sleep(self.stepCheckInMs)

        self._deconstruct()

    def _deconstruct(self):
        if self.finishedCallback:
            self.finishedCallback()
        self.finishedCallback = None
        self.callback = None

    def Abort(self):
        self.shouldRun = False
