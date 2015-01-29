#Embedded file name: carbon/client/script/sys\infoGatheringSvc.py
""" 
This service handles the gathering and logging of research data
according to the settings from it's server side sibling.
"""
import service
import blue
import uthread
import copy
import log
import sys
import igsUtil
from functools import partial

class InformationGatheringSvc(service.Service):
    __guid__ = 'svc.infoGatheringSvc'
    serviceName = 'svc.infoGatheringSvc'
    __exportedcalls__ = {'LogInfoEvent': [],
     'GetEventIGSHandle': []}
    __dependencies__ = ['machoNet']

    def __init__(self):
        service.Service.__init__(self)
        self.isEnabled = None
        self.serverEvents = set()
        self.serverOncePerRunEvents = set()
        self.infoTypeParameters = set()
        self.logTypeAggregates = {}
        self.isEnabled = 0
        self.loggedEvents = {}
        self.loggedEventsEmpty = {}
        self.aggregateDict = {}
        self.clientWorkerInterval = 0

    def Run(self, memStream = None):
        stateAndConfig = sm.RemoteSvc('infoGatheringMgr').GetStateAndConfig()
        self.isEnabled = stateAndConfig.isEnabled
        self.serverEvents = stateAndConfig.infoTypes
        self.clientWorkerInterval = stateAndConfig.clientWorkerInterval
        self.serverOncePerRunEvents = stateAndConfig.infoTypesOncePerRun
        self.logTypeAggregates = stateAndConfig.infoTypeAggregates
        self.infoTypeParameters = stateAndConfig.infoTypeParameters
        self.loggedEvents = {}
        if self.isEnabled and self.clientWorkerInterval > 0:
            self.SendInfoWorkerThread = uthread.new(self.SendInfoWorker)
        self.state = service.SERVICE_RUNNING

    def GetEventIGSHandle(self, eventTypeID, **keywords):
        """
            This method will return a method call handle to log into the IGS. 
            Please input evenTypeID (as it is always constant) along with any other constant keywords.
        """
        return partial(self.LogInfoEvent, eventTypeID=eventTypeID, **keywords)

    def LogInfoEvent(self, eventTypeID, itemID = None, itemID2 = None, int_1 = None, int_2 = None, int_3 = None, char_1 = None, char_2 = None, char_3 = None, float_1 = None, float_2 = None, float_3 = None):
        r"""
            Logs a single event from the server of a given infoType.
            Refer to ESPs Admin\infoGatherer pages for information of what event types need which input parameters as well as
            what each value represents.
            
            evenTypeID      :=  This is the master key and it must exist in info.settings and should always be included in app const.
                                The entries for this eventType in info.settings will dictate what inputs will be accepted and what will be aggregated by.
            
            All other inputs are ONLY needed if their corresponding key in info.settings are set (and please, if they are set as characterID
            don't pass a corporationID in there).
            
            The lists will be handled if they are less than 3 in length.
        """
        try:
            if eventTypeID in self.serverEvents:
                if eventTypeID in self.serverOncePerRunEvents:
                    self.serverOncePerRunEvents.remove(eventTypeID)
                    self.serverEvents.remove(eventTypeID)
                if eventTypeID not in self.loggedEvents:
                    if eventTypeID in self.logTypeAggregates:
                        self.aggregateDict[eventTypeID] = {}
                    self.loggedEvents[eventTypeID] = []
                if eventTypeID in self.logTypeAggregates:
                    if itemID2 is not None:
                        itemID2 = long(itemID2)
                    ln = [blue.os.GetWallclockTime(),
                     long(itemID),
                     itemID2,
                     int_1,
                     int_2,
                     int_3,
                     char_1,
                     char_2,
                     char_3,
                     float_1,
                     float_2,
                     float_3]
                    valueIx = self.infoTypeParameters[eventTypeID].difference(self.logTypeAggregates[eventTypeID])
                    igsUtil.AggregateEvent(eventTypeID, ln, self.loggedEvents, self.aggregateDict[eventTypeID], self.logTypeAggregates[eventTypeID], valueIx)
                else:
                    self.loggedEvents[eventTypeID].append([blue.os.GetWallclockTime(),
                     itemID,
                     itemID2,
                     int_1,
                     int_2,
                     int_3,
                     char_1,
                     char_2,
                     char_3,
                     float_1,
                     float_2,
                     float_3])
        except Exception:
            log.LogException('Error logging IGS information')
            sys.exc_clear()

    def SendInfoWorker(self):
        while self.isEnabled:
            try:
                eventsToSend = copy.deepcopy(self.loggedEvents)
                self.loggedEvents = {}
                if len(eventsToSend):
                    self.LogInfo('Information Gatherer is shipping collected data over the wire... Interval = %d milliseconds.' % self.clientWorkerInterval)
                    ret = sm.RemoteSvc('infoGatheringMgr').LogInfoEventsFromClient(eventsToSend)
                    for eventTypeID, status in ret.iteritems():
                        if status == const.INFOSERVICE_OFFLINE:
                            self.isEnabled = 0
                            break
                        elif status == const.INFOTYPE_OFFLINE:
                            self.serverEvents.remove(eventTypeID)
                            self.infoTypeParameters.remove(eventTypeID)
                            if eventTypeID in self.serverOncePerRunEvents:
                                self.serverOncePerRunEvents.remove(eventTypeID)
                            if eventTypeID in self.logTypeAggregates:
                                self.logTypeAggregates.remove(eventTypeID)

            except Exception:
                log.LogException('Error while shipping data to server...')
                sys.exc_clear()

            blue.pyos.synchro.SleepWallclock(self.clientWorkerInterval)
