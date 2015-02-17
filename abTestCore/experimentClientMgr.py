#Embedded file name: abTestCore\experimentClientMgr.py
import carbon.common.lib.const as timeconst
import eve.common.lib.infoEventConst as infoConst
import gatekeeper

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

    def IsTutorialEnabled(self):
        return not gatekeeper.user.IsInCohort(gatekeeper.cohortPirateUnicornsNPETwo)

    def IsOpportunitiesEnabled(self):
        return gatekeeper.user.IsInCohort(gatekeeper.cohortPirateUnicornsNPETwo)

    def LogWindowOpenedCounter(self, windowGuid, session):
        self.infoGatheringSvc.LogInfoEvent(eventTypeID=infoConst.infoEventWndOpenedCounters, itemID=session.charid, itemID2=session.userid, int_1=1, char_1=windowGuid)

    def LogFirstTimeActionTaken(self, action, session, now):
        if action in self.actionsTaken:
            return
        self.actionsTaken.add(action)
        secsSinceCharacterLogon = (now - self.characterLogonTime) / timeconst.SEC
        self.infoGatheringSvc.LogInfoEvent(eventTypeID=infoConst.infoEventWndOpenedFirstTime, itemID=session.charid, itemID2=session.userid, int_1=secsSinceCharacterLogon, char_1=action)

    def ShouldEnableNewNPE(self):
        pass
