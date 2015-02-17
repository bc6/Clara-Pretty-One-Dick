#Embedded file name: abTestCore/client\experimentClientSvc.py
import service
import blue
from ..experimentClientMgr import ABTestClientManager

class ExperimentClientService(service.Service):
    __guid__ = 'svc.experimentClientSvc'
    service = 'svc.experimentClientSvc'

    def __init__(self):
        service.Service.__init__(self)
        self.manager = ABTestClientManager()

    def Run(self, memStream = None):
        pass

    def OnUserLogon(self, languageID):
        userLogonTime = blue.os.GetWallclockTime()

    def OnCharacterLogon(self):
        characterLogonTime = blue.os.GetWallclockTime()

    def LogAttemptToClickTutorialLink(self, tutorialID):
        pass

    def Initialize(self, languageID):
        characterLogonTime = blue.os.GetWallclockTime()
        self.manager.Initialize(languageID=languageID, logonTime=characterLogonTime, infoGatheringSvc=sm.GetService('infoGatheringSvc'))

    def TearDown(self):
        self.manager.TearDown()
        self.manager = ABTestClientManager()

    def IsTutorialEnabled(self):
        return self.manager.IsTutorialEnabled()

    def OpportunitiesEnabled(self):
        return self.manager.IsOpportunitiesEnabled()

    def LogWindowOpenedActions(self, windowGuid):
        self.LogWindowOpenedCounter(windowGuid=windowGuid)
        self.LogFirstTimeActionTaken(action=windowGuid)

    def LogWindowOpenedCounter(self, windowGuid):
        self.manager.LogWindowOpenedCounter(windowGuid, session)

    def LogFirstTimeActionTaken(self, action):
        now = blue.os.GetWallclockTime()
        self.manager.LogFirstTimeActionTaken(action, session, now)
