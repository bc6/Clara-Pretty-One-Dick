#Embedded file name: abTestCore\experimentClientMgr.py
import gatekeeper
import gatekeeper.gatekeeperConst as gkConst

class ABTestClientManager:

    def __init__(self):
        self.initialized = False

    def Initialize(self, languageID, logonTime, infoGatheringSvc):
        self.languageID = str(languageID).lower()
        self.initialized = True
        self.actionsTaken = set()
        self.characterLogonTime = logonTime
        self.infoGatheringSvc = infoGatheringSvc

    def TearDown(self):
        self.initialized = False
        self.languageID = None

    def LogWindowOpenedCounter(self, windowGuid, session):
        self.infoGatheringSvc.LogInfoEvent(eventTypeID=const.infoEventWndOpenedCounters, itemID=session.charid, itemID2=session.userid, int_1=1, char_1=windowGuid)

    def LogFirstTimeActionTaken(self, action, session, now):
        if action in self.actionsTaken:
            return
        self.actionsTaken.add(action)
        secsSinceCharacterLogon = (now - self.characterLogonTime) / const.SEC
        self.infoGatheringSvc.LogInfoEvent(eventTypeID=const.infoEventWndOpenedFirstTime, itemID=session.charid, itemID2=session.userid, int_1=secsSinceCharacterLogon, char_1=action)
