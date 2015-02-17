#Embedded file name: notifications/client/generator\notificationGenerator.py
from notifications.common.notification import Notification
from notifications.client.generator.simpleRandomDistributor import SimpleRandomDistributer
import blue

class NotificationGenerator:

    def __init__(self):
        self.currentIndex = 0
        self.fakeThisSequence = [0,
         0,
         1,
         1,
         2,
         2,
         0,
         0,
         1,
         1,
         1,
         1]
        self.internalSequence = 0
        self.isGenerating = False

    def loadConfig(self, config):
        pass

    def Start(self):
        self.distributer = SimpleRandomDistributer(10, 20000, generateCallback=self.MakeFakeNotification, finishedCallback=self.OnDistributerFinished, nowTimeProviderFunction=blue.os.GetWallclockTime, step=10, oddsOfEventPerCheck=0.1, generateMax=100)
        self.distributer.Start()
        self.isGenerating = True

    def Stop(self):
        print 'Aborting Generator'
        self.distributer.Abort()
        self.isGenerating = False

    def OnDistributerFinished(self):
        print 'Generator finished'
        self.isGenerating = False

    def MakeFakeNotification(self, sequence):
        self.internalSequence = self.internalSequence + 1
        actualSequence = sequence + self.internalSequence
        self.currentIndex = self.currentIndex + 1
        type = self.fakeThisSequence[actualSequence % len(self.fakeThisSequence)]
        if type is 0:
            template = FakeNormalNotification()
        elif type is 2:
            template = FakeSkillNotification(sequence)
        else:
            template = FakeCharacterNotification()
        template.generate(actualSequence)


class FakeSkillNotification:

    def __init__(self, sequenceNr):
        self.sequence = sequenceNr

    def generate(self, sequence):
        skillsvc = sm.StartService('skills')
        skillsvc.ShowSkillNotification([3300 + self.sequence], 10, True)


class FakeCharacterNotification:
    flipbit = False

    def generate(self, sequence):
        FakeCharacterNotification.flipbit = not FakeCharacterNotification.flipbit
        if FakeCharacterNotification.flipbit:
            sm.ScatterEvent('OnContactLoggedOn', 90000001)
        else:
            sm.ScatterEvent('OnContactLoggedOff', 90000001)


class FakeNormalNotification:

    def generate(self, sequence):
        newNotification = Notification(notificationID=-1, typeID=Notification.NORMAL_NOTIFICATION, senderID=90000001, receiverID=90000001, processed=False, created=blue.os.GetWallclockTime(), data={})
        newNotification.subject = 'Subject:' + str(sequence)
        newNotification.body = 'Body:' + str(sequence)
        sm.ScatterEvent('OnNewNotificationReceived', newNotification)
