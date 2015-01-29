#Embedded file name: abTestCore/client\experimentClientSvc.py
import service
import blue
from ..experimentClientMgr import ABTestClientManager
from carbonui.uicore import UICoreBase

class ExperimentClientService(service.Service):
    __guid__ = 'svc.experimentClientSvc'
    service = 'svc.experimentClientSvc'

    def __init__(self):
        service.Service.__init__(self)
        self.manager = ABTestClientManager()

    def Run(self, memStream = None):
        pass

    def Initialize(self, languageID):
        characterLogonTime = blue.os.GetWallclockTime()
        self.manager.Initialize(languageID=languageID, logonTime=characterLogonTime, infoGatheringSvc=sm.GetService('infoGatheringSvc'))

    def TearDown(self):
        self.manager.TearDown()
        self.manager = ABTestClientManager()

    def LogWindowOpenedActions(self, windowGuid):
        self.LogWindowOpenedCounter(windowGuid=windowGuid)
        self.LogFirstTimeActionTaken(action=windowGuid)

    def LogWindowOpenedCounter(self, windowGuid):
        self.manager.LogWindowOpenedCounter(windowGuid, session)

    def LogFirstTimeActionTaken(self, action):
        now = blue.os.GetWallclockTime()
        self.manager.LogFirstTimeActionTaken(action, session, now)
