#Embedded file name: eve/client/script/ui/services/wars\war_cso.py
from service import Service, SERVICE_START_PENDING, SERVICE_RUNNING
from builtinmangler import CreateInstance
import blue
import uthread
import moniker
import warObject
import log
import sys

def ReturnNone():
    return None


class Wars(Service):
    __exportedcalls__ = {'GetWars': [],
     'GetRelationship': [],
     'AreInAnyHostileWarStates': [],
     'GetCostOfWarAgainst': []}
    __guid__ = 'svc.war'
    __notifyevents__ = ['DoSessionChanging', 'OnWarChanged']
    __servicename__ = 'war'
    __displayname__ = 'War Client Service'
    __dependencies__ = []
    __functionalobjects__ = ['wars']

    def __init__(self):
        Service.__init__(self)

    def GetDependencies(self):
        return self.__dependencies__

    def GetObjectNames(self):
        return self.__functionalobjects__

    def Run(self, memStream = None):
        self.LogInfo('Starting War')
        self.state = SERVICE_START_PENDING
        self.__warMoniker = None
        self.__warMonikerOwnerID = None
        items = warObject.__dict__.items()
        for objectName in self.__functionalobjects__:
            if objectName == 'base':
                continue
            object = None
            classType = 'warObject.%s' % objectName
            for i in range(0, len(warObject.__dict__)):
                self.LogInfo('Processing', items[i])
                if len(items[i][0]) > 1:
                    if items[i][0][:2] == '__':
                        continue
                if items[i][1].__guid__ == classType:
                    object = CreateInstance(classType, (self,))
                    break

            if object is None:
                raise RuntimeError('FunctionalObject not found %s' % classType)
            setattr(self, objectName, object)

        for objectName in self.__functionalobjects__:
            object = getattr(self, objectName)
            object.DoObjectWeakRefConnections()

        self.state = SERVICE_RUNNING
        uthread.new(self.CheckForStartOrEndOfWar)

    def Stop(self, memStream = None):
        self.__warMoniker = None
        self.__warMonikerOwnerID = None

    def DoSessionChanging(self, isRemote, session, change):
        try:
            if 'charid' in change and change['charid'][0] or 'userid' in change and change['userid'][0]:
                sm.StopService(self.__guid__[4:])
        except:
            log.LogException()
            sys.exc_clear()

    def RefreshMoniker(self):
        if self.__warMoniker is not None:
            self.__warMoniker.UnBind()

    def GetMoniker(self):
        if self.__warMoniker is None:
            self.__warMoniker = moniker.GetWar()
            self.__warMonikerOwnerID = eve.session.allianceid or eve.session.corpid
        if self.__warMonikerOwnerID != (eve.session.allianceid or eve.session.corpid):
            if self.__warMoniker is not None:
                self.__warMoniker.Unbind()
            self.__warMoniker = moniker.GetWar()
            self.__warMonikerOwnerID = eve.session.allianceid or eve.session.corpid
        return self.__warMoniker

    def OnWarChanged(self, war, ownerIDs, change):
        try:
            warID = war.warID if war is not None else change['warID'][0]
            self.LogInfo('OnWarChanged warID:', warID, 'ownerIDs:', ownerIDs, 'change:', change)
            self.wars.OnWarChanged(war, ownerIDs, change)
        except:
            log.LogException()
            sys.exc_clear()

    def GetWars(self, ownerID, forceRefresh = 0):
        return self.wars.GetWars(ownerID, forceRefresh)

    def GetRelationship(self, ownerIDaskingAbout):
        return self.wars.GetRelationship(ownerIDaskingAbout)

    def AreInAnyHostileWarStates(self, ownerID):
        return self.wars.AreInAnyHostileWarStates(ownerID)

    def GetCostOfWarAgainst(self, ownerID):
        return self.wars.GetCostOfWarAgainst(ownerID)

    def CheckForStartOrEndOfWar(self):
        while self.state == SERVICE_RUNNING:
            if not session.charid:
                blue.pyos.synchro.SleepWallclock(10000)
                continue
            try:
                self.wars.CheckForStartOrEndOfWar()
            except Exception:
                log.LogException()
                sys.exc_clear()

            blue.pyos.synchro.SleepWallclock(10000)

    def GetAllyNegotiations(self):
        warMoniker = self.GetMoniker()
        return filter(lambda x: x.warNegotiationTypeID == const.WAR_NEGOTIATION_TYPE_ALLY_OFFER, warMoniker.GetNegotiations())

    def GetSurrenderNegotiations(self, warID):
        warMoniker = self.GetMoniker()
        return filter(lambda x: x.warNegotiationTypeID == const.WAR_NEGOTIATION_TYPE_SURRENDER_OFFER and x.warID == warID, warMoniker.GetNegotiations())

    def CreateWarAllyOffer(self, warID, iskValue, defenderID, message):
        warMoniker = self.GetMoniker()
        warMoniker.CreateWarAllyOffer(warID, iskValue, defenderID, message)

    def CreateSurrenderNegotiation(self, warID, iskValue, message):
        warMoniker = self.GetMoniker()
        warMoniker.CreateSurrenderNegotiation(warID, iskValue, message)

    def GetWarNegotiation(self, warNegotiationID):
        return self.GetMoniker().GetWarNegotiation(warNegotiationID)

    def AcceptAllyNegotiation(self, warNegotiationID):
        warMoniker = self.GetMoniker()
        warMoniker.AcceptAllyNegotiation(warNegotiationID)

    def DeclineAllyOffer(self, warNegotiationID):
        self.GetMoniker().DeclineAllyOffer(warNegotiationID)

    def RetractMutualWar(self, warID):
        warMoniker = self.GetMoniker()
        warMoniker.RetractMutualWar(warID)

    def AcceptSurrender(self, warNegotiationID):
        warMoniker = self.GetMoniker()
        warMoniker.AcceptSurrender(warNegotiationID)

    def DeclineSurrender(self, warNegotiationID):
        self.GetMoniker().DeclineSurrender(warNegotiationID)

    def SetOpenForAllies(self, warID, state):
        self.GetMoniker().SetOpenForAllies(warID, state)

    def GMJoinDefender(self, warID, entityID):
        warMoniker = self.GetMoniker()
        warEntityID = session.corpid if session.allianceid is None else session.allianceid
        warMoniker.GMJoinDefender(warID, entityID, warEntityID)

    def GMClearForcedPeace(self, warID):
        self.GetMoniker().GMClearForcedPeace(warID)

    def GMActivateDefender(self, warID, allyID):
        warMoniker = self.GetMoniker()
        warMoniker.GMActivateDefender(warID, allyID)

    def GMDeactivateDefender(self, warID, allyID):
        warMoniker = self.GetMoniker()
        warMoniker.GMDeactivateDefender(warID, allyID)

    def GMExtendAllyContract(self, warID, allyID, time):
        warMoniker = self.GetMoniker()
        warMoniker.GMExtendAllyContract(warID, allyID, time)

    def GMSetWarStartTime(self, warID, time):
        mon = self.GetMoniker()
        mon.GMSetWarStartTime(warID, time)

    def GMSetWarFinishTime(self, warID, time):
        mon = self.GetMoniker()
        mon.GMSetWarFinishTime(warID, time)

    def IsAllyInWar(self, warID):
        return self.wars.IsAllyInWar(warID)
