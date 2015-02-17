#Embedded file name: eve/client/script/ui/services\tutorialsvc.py
import eve.common.lib.appConst as const
import service
import uicontrols
import uix
import uiutil
import carbonui.const as uiconst
import uthread
import util
import blue
import sys
from eve.common.script.entities.proximityOpenTutorialComponent import ProximityOpenTutorialComponent
import log
import geo2
from collections import defaultdict
import audio2
import localization
import re
import carbon.common.script.sys.serviceConst as serviceConst
from carbon.common.script.sys.serviceConst import ROLE_NEWBIE
from eve.client.script.ui.station.lobby import Lobby as LobbyWindow
from eve.client.script.ui.shared.inventory.invWindow import Inventory as InventoryWindow
from eve.client.script.ui.station.fitting.base_fitting import FittingWindow
from eve.client.script.ui.inflight.activeitem import ActiveItem as ActiveItemWindow
from eve.client.script.ui.station.agents.agentDialogueWindow import AgentDialogueWindow
from eve.client.script.ui.services.tutoriallib import TutorialPageState
from eve.client.script.ui.services.careerFunnelWindow import CareerFunnelWindow
from eve.client.script.ui.services.tutorialWindow import TutorialWindow
import gatekeeper
NUM_TUTORIAL_BLINK = 3

def _ProximityCallBack(tutorialID, entidList):
    if session.charid not in entidList:
        return
    sm.GetService('tutorial').OpenTutorialSequence_Check(tutorialID)


class TutorialSvc(service.Service):
    __guid__ = 'svc.tutorial'
    __update_on_reload__ = 0
    __exportedcalls__ = {'OpenTutorial': [service.ROLE_IGB],
     'OpenTutorialSequence_Check': [service.ROLE_IGB]}
    __notifyevents__ = ['OnSessionChanged',
     'OnClearTutorialCache',
     'OnServerTutorialRequest',
     'OnViewStateChanged']
    __dependencies__ = ['settings', 'michelle', 'uipointerSvc']
    __componentTypes__ = ['proximityOpenTutorial']

    def __init__(self):
        service.Service.__init__(self)
        self.criterias = None
        self.actions = None
        self.categories = None
        self.loadingTutorial = 0
        self.tutorials = None
        self.tutorialConnections = None
        self.tutorialInfos = {}
        self.sequences = {}
        self.waiting = None
        self.goodieIcons = None
        self.oldHeight = None
        self.waitingForWarpConfirm = False
        self.pageTime = blue.os.GetWallclockTime()
        self.shouldOfferTutorial = True
        try:
            self.numMouseClicks = uicore.uilib.GetGlobalClickCount()
            self.numKeyboardClicks = uicore.uilib.GetGlobalKeyDownCount()
        except:
            self.numMouseClicks = 0
            self.numKeyboardClicks = 0

        self.careerAgents = {}
        self.tutorialNoob = True

    def LogTutorialEvent(self, columnNames, *args):
        if not sm.GetService('machoNet').GetGlobalConfig().get('disableTutorialLogging', 0):
            uthread.new(self._DoLogTutorialEvent, columnNames, *args)

    def _DoLogTutorialEvent(self, columnNames, *args):
        try:
            sm.ProxySvc('eventLog').LogClientEvent('tutorial', columnNames, *args)
        except UserError:
            pass

    def Run(self, *etc):
        self.LogInfo('Starting Tutorial Service')
        service.Service.Run(self, *etc)
        self.audioEmitter = audio2.AudEmitter('Tutorial Audio')
        self.LogPageCompletion = None
        self.waitingForCriteria = None

    def Stop(self, memStream = None):
        if not sm.IsServiceRunning('window'):
            return
        tutorialBrowser = self.GetTutorialBrowser(create=0)
        if tutorialBrowser:
            tutorialBrowser.CloseByUser()
        else:
            self.Cleanup()
        self.LogInfo('Stopping Tutorial Service')

    def Cleanup(self):
        self.audioEmitter.SendEvent(u'fade_out')
        self.uipointerSvc.ClearPointers()
        self.uipointerSvc.RemoveSpaceObjectUiPointers()
        self.waitingForCriteria = None
        eve.SetRookieState(None)

    def CreateComponent(self, name, state):
        component = ProximityOpenTutorialComponent()
        component.tutorialID = int(state.get('tutorialID', None))
        component.radius = float(state.get('radius', None))
        return component

    def SetupComponent(self, entity, component):
        posComponent = entity.GetComponent('position')
        sm.GetService('proximity').AddCallbacks(instanceID=entity.scene.sceneID, pos=posComponent.position, range=component.radius, msToCheck=250, onEnterCallback=_ProximityCallBack, onExitCallback=lambda tutorialID, entidList: None, callbackArgs=component.tutorialID)

    def PackUpForClientTransfer(self, component):
        state = {}
        state['tutorialID'] = component.tutorialID
        state['radius'] = component.radius
        return state

    def PackUpForSceneTransfer(self, component, destinationSceneID = None):
        return self.PackUpForClientTransfer(component)

    def UnPackFromSceneTransfer(self, component, entity, state):
        component.tutorialID = state['tutorialID']
        component.radius = state['radius']
        return component

    def _GetSequenceDoneStatus(self, sequenceID):
        return settings.char.ui.Get('SequenceDoneStatus', {}).get(sequenceID, (None, None))

    def SetSequenceDoneStatus(self, sequenceID, tutorialID, pageNo):
        stat = settings.char.ui.Get('SequenceDoneStatus', {})
        if tutorialID is None:
            del stat[sequenceID]
        else:
            stat[sequenceID] = (tutorialID, pageNo)
        settings.char.ui.Set('SequenceDoneStatus', stat)

    def GetSequenceStatus(self, sequenceID):
        return settings.char.ui.Get('SequenceStatus', {}).get(sequenceID, None)

    def SetSequenceStatus(self, sequenceID, tutorialID, pageNo, status = None):
        tutorialBrowser = self.GetTutorialBrowser(create=0)
        if tutorialBrowser and hasattr(tutorialBrowser, 'startTime'):
            time = (blue.os.GetWallclockTime() - tutorialBrowser.startTime) / const.SEC
        else:
            time = 0
        stat = settings.char.ui.Get('SequenceStatus', {})
        if status == 'reset' and sequenceID in stat:
            tutorialBrowser = self.GetTutorialBrowser()
            tutorialBrowser.Close()
            self.uipointerSvc.ClearPointers()
            self.uipointerSvc.RemoveSpaceObjectUiPointers()
            if eve.session.solarsystemid2 and tutorialID != uix.tutorial:
                sm.GetService('neocom').BlinkStopAll()
            if eve.session.stationid:
                lobby = LobbyWindow.GetIfOpen()
                if lobby:
                    lobby.StopAllBlinkButtons()
            del stat[sequenceID]
        elif status == 'done':
            stat[sequenceID] = 'done'
            sm.RemoteSvc('tutorialSvc').LogCompleted(tutorialID, pageNo, int(time))
        elif status == 'aborted':
            stat[sequenceID] = 'done'
            sm.RemoteSvc('tutorialSvc').LogAborted(tutorialID, pageNo, int(time))
        else:
            stat[sequenceID] = (tutorialID, pageNo)
        saveSettings = False
        if stat.get(sequenceID, '') == 'done':
            saveSettings = True
            if sequenceID == uix.tutorialTutorials:
                settings.user.ui.Delete('doIntroTutorial%s' % session.charid)
                stat[uix.tutorialWorldspaceNavigation] = 'done'
        settings.char.ui.Set('SequenceStatus', stat)
        if saveSettings:
            sm.GetService('settings').SaveSettings()

    def _GetSequences(self):
        if not self.sequences:
            self._ResolveTutorialSequences()
        return self.sequences

    def _GetSequence(self, sequenceID):
        sequences = self._GetSequences()
        return sequences[sequenceID]

    def _GetSequenceIDForTutorial(self, tutorialID):
        sequences = self._GetSequences()
        for sequenceID, sequence in sequences.iteritems():
            if tutorialID in sequence:
                return sequenceID

    def GetNextInSequence(self, tutorialID, sequenceID, direction = 1):
        seq = self._GetSequence(sequenceID)
        if tutorialID in seq:
            if direction == 1 and tutorialID != seq[-1]:
                return seq[seq.index(tutorialID) + direction]
            if direction == -1 and tutorialID != seq[0]:
                return seq[seq.index(tutorialID) + direction]

    def GetOtherRookieFilter(self, key):
        return {'defaultchannels': 28.5}.get(key.lower(), 1000)

    def GetShipuiRookieFilter(self, buttonname):
        return {localization.GetByLabel('UI/Commands/ZoomIn'): 21,
         localization.GetByLabel('UI/Commands/ResetCamera'): 21,
         localization.GetByLabel('UI/Commands/ZoomOut'): 21,
         localization.GetByLabel('UI/Generic/Autopilot'): 35,
         localization.GetByLabel('UI/Generic/Tactical'): 21,
         localization.GetByLabel('UI/Generic/Scanner'): 21,
         localization.GetByLabel('UI/Generic/Cargo'): 21}.get(buttonname, 1000)

    def GetTutorialsByCategory(self):
        tutorials = self.GetTutorials()
        byCategs = {}
        for tutorialID, tutorialData in tutorials.iteritems():
            if tutorialData.categoryID not in byCategs:
                byCategs[tutorialData.categoryID] = []
            tutorialName = localization.GetByMessageID(tutorialData.tutorialNameID)
            data = util.KeyVal(tutorialData)
            data.otherRace = data.tutorialID in self.otherRacialTutorial
            byCategs[tutorialData.categoryID].append((tutorialName, data))

        for k, v in byCategs.iteritems():
            byCategs[k] = uiutil.SortListOfTuples(v)

        return byCategs

    def GetValidTutorials(self, newbie = True):
        validTutorials = []
        for categoryID, tutorials in self.GetTutorialsByCategory().iteritems():
            if categoryID is None:
                continue
            for tutorial in tutorials:
                validTutorials.append(tutorial.tutorialID)

        return validTutorials

    def _HasCurrentTutorial(self):
        pageState = self.GetCurrentTutorial()
        if pageState is None:
            return False
        return True

    def GetCurrentTutorial(self):
        tutorialBrowser = self.GetTutorialBrowser(create=0)
        pageState = None
        if tutorialBrowser is not None:
            pageState = getattr(tutorialBrowser, 'current', None)
        if pageState is None:
            pageState = settings.char.generic.Get('tutorialPageState', None)
            self.LogInfo('Loading tutorialPageState', pageState)
        if pageState is not None:
            pageState = TutorialPageState(*pageState)
            if tutorialBrowser is not None:
                tutorialBrowser.current = pageState
        return pageState

    def OpenCurrentTutorial(self):
        tut = self.GetCurrentTutorial()
        if tut is None:
            self.OpenTutorial(tutorialID=uix.tutorialTutorials)
        else:
            self.OpenTutorial(tutorialID=tut.tutorialID, pageNo=tut.pageNo, pageID=tut.pageID, VID=tut.VID, force=True)

    def _IsNewbie(self):
        return session.role & ROLE_NEWBIE == ROLE_NEWBIE or settings.user.ui.Get('bornDaysAgo%s' % session.charid, 0) < 30

    def _IsTutorialCompleted(self):
        return settings.char.generic.Get('tutorialCompleted', None)

    def _IsTutorialEnabled(self):
        return settings.char.ui.Get('showTutorials', True) and not gatekeeper.user.IsInCohort(gatekeeper.cohortPirateUnicornsNPETwo)

    def _StartupTutorial(self):
        if self.shouldOfferTutorial and self._IsTutorialEnabled() and self._IsNewbie():
            self.shouldOfferTutorial = False
            if not self._IsTutorialCompleted():
                self.OpenCurrentTutorial()

    def OnViewStateChanged(self, oldViewName, newViewName):
        """When we access the game we want to check if we should offer the tutorial"""
        if oldViewName in ('charsel', 'charactercreation') and newViewName in {'inflight', 'hangar', 'station'}:
            blue.pyos.synchro.SleepWallclock(3000)
            uthread.new(self._StartupTutorial)

    def OpenTutorialSequence_Check(self, tutorialID = None, force = 0, click = 0, pageNo = None, ignoreSettings = False):
        self.LogInfo('OpenTutorialSequence_Check', tutorialID, force, click, pageNo)
        if not sm.GetService('experimentClientSvc').IsTutorialEnabled():
            self.LogInfo('Will not open tutorial. Disabled by cohort')
            return
        if not ignoreSettings and not self._IsTutorialEnabled():
            self.LogInfo('Will not open tutorial. Disabled in settings')
            return
        if tutorialID not in self.GetValidTutorials():
            self.LogWarn('TutorialSvc: Attempting to open tutorial', tutorialID, 'which is not a valid tutorial ID')
            return
        tut = self.GetCurrentTutorial()
        if tut is not None:
            if tutorialID == tut.tutorialID and tut.sequenceID:
                tutorialBrowser = self.GetTutorialBrowser(create=0)
                if tutorialBrowser is not None:
                    if not tutorialBrowser.done:
                        self.LogInfo('Will not open tutorial. Tutorial already open')
                        return
        seqStat = self.GetSequenceStatus(tutorialID)
        if seqStat == 'done' and force:
            stat = settings.char.ui.Get('SequenceStatus', {})
            if tutorialID in stat:
                del stat[tutorialID]
                settings.char.ui.Set('SequenceStatus', stat)
                seqStat = self.GetSequenceStatus(tutorialID)
        if seqStat == 'done':
            self.LogInfo('Will not open tutorial. Sequence is completed')
            return
        if seqStat and not force:
            _tutorialID, pageNo = seqStat
            self.OpenTutorial(_tutorialID, pageNo, force=force, click=click)
        else:
            self.OpenTutorial(tutorialID, pageNo=pageNo, force=force, click=click)

    def _GetNextTutorial(self, tutorialID):
        tutorialConnections = self._GetTutorialConnections()
        if tutorialID in tutorialConnections:
            nextID = tutorialConnections[tutorialID].get(session.raceID, None)
            if not nextID:
                nextID = tutorialConnections[tutorialID].get(0, None)
            return nextID

    def GetTutorialBrowser(self, create = 1):
        if not sm.GetService('experimentClientSvc').IsTutorialEnabled():
            return None
        tutorialBrowser = TutorialWindow.GetIfOpen()
        if not tutorialBrowser and create:
            tutorialBrowser = TutorialWindow.Open(backFunc=self._Back, nextFunc=self._Next)
        return tutorialBrowser

    def GetCategory(self, categoryID):
        if self.categories is None:
            self.categories = {}
            try:
                categories = sm.RemoteSvc('tutorialSvc').GetCategories()
                for category in categories:
                    self.categories[category.categoryID] = category
                    self.categories[category.categoryID].categoryName = localization.GetByMessageID(category.categoryNameID)
                    self.categories[category.categoryID].description = localization.GetByMessageID(category.descriptionID)

            except:
                sys.exc_clear()

        if categoryID in self.categories:
            return self.categories[categoryID]

    def GetCriteria(self, criteriaID):
        if self.criterias is None:
            self.criterias = {}
            try:
                criterias = sm.RemoteSvc('tutorialSvc').GetCriterias()
                for criteria in criterias:
                    self.criterias[criteria.criteriaID] = criteria

            except:
                sys.exc_clear()

        if criteriaID in self.criterias:
            return self.criterias[criteriaID]

    def GetAction(self, actionID):
        if self.actions is None:
            self.actions = {}
            actions = sm.RemoteSvc('tutorialSvc').GetActions()
            for action in actions:
                self.actions[action.actionID] = action

        if actionID in self.actions:
            return self.actions[actionID]

    def __PopulateTutorialsAndConnections(self):
        """
            Helper method to populate local tutorial caches
        """
        try:
            t, tc = sm.RemoteSvc('tutorialSvc').GetTutorialsAndConnections()
            self.tutorials = t.Index('tutorialID')
            tc = tc.Filter('tutorialID')
            otherRacialTutorial = defaultdict(list)
            self.tutorialConnections = defaultdict(dict)
            for tutID, rows in tc.iteritems():
                for row in rows:
                    self.tutorialConnections[tutID][row.raceID] = row.nextTutorialID
                    if row.raceID != 0:
                        otherRacialTutorial[row.nextTutorialID].append(row.raceID)

            self.otherRacialTutorial = set()
            for tutorialID, races in otherRacialTutorial.iteritems():
                if session.raceID not in races:
                    self.otherRacialTutorial.add(tutorialID)

        except:
            sys.exc_clear()

    def GetTutorials(self):
        if self.tutorials is None:
            self.__PopulateTutorialsAndConnections()
        return self.tutorials

    def _GetTutorialConnections(self):
        if self.tutorialConnections is None:
            self.__PopulateTutorialsAndConnections()
        return self.tutorialConnections

    def _ResolveTutorialSequences(self):
        sequences = {}
        starters = self._ResolveSequenceStarterTutorials()
        for squenceID in starters:
            self.LogInfo('Setting up tutorial sequence', squenceID)
            sequence = []
            nextID = squenceID
            while nextID:
                if nextID in sequence:
                    self.LogError('Cannot resolve the tutorial sequence, its in loop', squenceID, nextID, sequence)
                    break
                sequence.append(nextID)
                nextID = self._GetNextTutorial(nextID)

            sequences[squenceID] = sequence

        counters = defaultdict(list)
        for sequenceID, sequence in self.sequences.iteritems():
            for tID in sequence:
                counters[tID].append(sequenceID)

        for tutorialID, sequenceIDs in counters:
            if len(sequenceIDs) > 1:
                self.LogError('The tutorialID', tutorialID, 'appearse in many sequences', sequenceIDs, 'Tutorial should only appear in one sequence.')

        self.sequences = sequences

    def _ResolveSequenceStarterTutorials(self):
        """
        Find all tutorialIDs that start a sequences of any length
        """
        tutorials = self.GetTutorials()
        connections = self._GetTutorialConnections()
        starters = []
        for tutorialID in tutorials:
            for connection in connections.itervalues():
                found = False
                for toID in connection.itervalues():
                    if toID == tutorialID:
                        found = True
                        break

                if found:
                    break
            else:
                starters.append(tutorialID)

        return starters

    def OnClearTutorialCache(self):
        self.tutorialInfos = {}

    def OnServerTutorialRequest(self, tutorialID):
        self.OpenTutorialFromOutside(tutorialID, force=1, fromServer=True)

    def OpenTutorialFromOutside(self, tutorialID, ask = 0, force = 1, ignoreSettings = False, fromServer = False):
        if not sm.GetService('experimentClientSvc').IsTutorialEnabled():
            if not fromServer:
                sm.GetService('experimentClientSvc').LogAttemptToClickTutorialLink(tutorialID)
                eve.Message('NewNPEClickOnTutorialLinkDisabled', {})
            return
        if ask:
            tutorialBrowser = self.GetTutorialBrowser(create=0)
            if tutorialBrowser:
                if eve.Message('AskIfCancelCurrentTutorial', {}, uiconst.YESNO) != uiconst.ID_YES:
                    return
        self.OpenTutorialSequence_Check(tutorialID, force=force, ignoreSettings=ignoreSettings)

    def GetTutorialInfo(self, tutorialID):
        if tutorialID in self.tutorialInfos:
            return self.tutorialInfos[tutorialID]
        try:
            tutData = sm.RemoteSvc('tutorialSvc').GetTutorialInfo(tutorialID)
        except KeyError:
            sys.exc_clear()
            return None

        self.tutorialInfos[tutorialID] = tutData
        return tutData

    def OnSessionChanged(self, isRemote, session, change):
        self.UnhideTutorialWindow()
        if 'charid' in change:
            oldCharID, newCharID = change['charid']
            if newCharID is not None:
                self.GetCharacterTutorialState()
        funnel = CareerFunnelWindow.GetIfOpen()
        if funnel:
            if util.IsWormholeSystem(eve.session.solarsystemid):
                eve.Message('NoAgentsInWormholes')
                funnel.CloseByUser()
                return
            funnel.RefreshEntries()

    def OnCloseApp(self):
        tutorialBrowser = self.GetTutorialBrowser(create=0)
        if tutorialBrowser and self._HasCurrentTutorial() and hasattr(tutorialBrowser, 'startTime'):
            time = (blue.os.GetWallclockTime() - tutorialBrowser.startTime) / const.SEC
            tutorialID = tutorialBrowser.current.tutorialID
            pageNo = tutorialBrowser.current.pageNo
            if tutorialID is not None and pageNo is not None:
                sm.RemoteSvc('tutorialSvc').LogAppClosed(tutorialID, pageNo, int(time))

    def OnCloseWnd(self, *args):
        uthread.new(self.Cleanup)

    def UnhideTutorialWindow(self):
        self.ChangeTutorialWndState(visible=True)

    def Reload(self, *args):
        tutorialBrowser = self.GetTutorialBrowser()
        self._ReloadTutorialBrowser(tutorialBrowser)

    def _ReloadTutorialBrowser(self, tutorialBrowser):
        if hasattr(tutorialBrowser, 'current'):
            tut = tutorialBrowser.current
            self.OpenTutorial(tutorialID=tut.tutorialID, pageNo=tut.pageNo, pageID=tut.pageID, force=True, VID=tut.VID)

    def _Back(self, *args):
        tut = self.GetCurrentTutorial()
        if tut is not None:
            tutorialID = tut.tutorialID
            pageNo = tut.pageNo
            VID = tut.VID
            pageID = tut.pageID
            sequenceID = tut.sequenceID
            timeSpent = (blue.os.GetWallclockTime() - self.pageTime) / const.SEC
            try:
                numClicks = uicore.uilib.GetGlobalClickCount() - self.numMouseClicks
                numKeys = uicore.uilib.GetGlobalKeyDownCount() - self.numKeyboardClicks
            except:
                numClicks = numKeys = 0

            if pageNo is not None and pageNo > 1:
                oldPageNo = pageNo
                pageNo -= 1
                with util.ExceptionEater('eventLog'):
                    self.LogTutorialEvent(['fromTutorialID',
                     'fromPageNo',
                     'toTutorialID',
                     'toPageNo',
                     'sequenceID',
                     'timeInPage',
                     'numMouseClicks',
                     'numKeyboardClicks'], 'PrevPage', tutorialID, oldPageNo, tutorialID, pageNo, sequenceID, timeSpent, numClicks, numKeys)
                self.OpenTutorial(tutorialID, pageNo, pageID, VID=VID, checkBack=1)
                return
            if sequenceID:
                tutorialBrowser = self.GetTutorialBrowser()
                nextTutorialID = self.GetNextInSequence(tutorialID, sequenceID, [-1, 1][tutorialBrowser.reverseBack])
                if nextTutorialID:
                    with util.ExceptionEater('eventLog'):
                        tutData = sm.GetService('tutorial').GetTutorialInfo(nextTutorialID)
                        if tutData is not None:
                            nextPageNo = len(tutData.pages)
                        else:
                            nextPageNo = -1
                        self.LogTutorialEvent(['fromTutorialID',
                         'fromPageNo',
                         'toTutorialID',
                         'toPageNo',
                         'sequenceID',
                         'timeInPage',
                         'numMouseClicks',
                         'numKeyboardClicks'], 'PrevPage', tutorialID, pageNo, nextTutorialID, nextPageNo, sequenceID, timeSpent, numClicks, numKeys)
                    self.OpenTutorial(nextTutorialID, [-1, None][tutorialBrowser.reverseBack], VID=VID, checkBack=1)
                    return

    def _Next(self, *args):
        tut = self.GetCurrentTutorial()
        if tut is not None:
            tutorialID = tut.tutorialID
            if tut.pageNo is not None:
                oldPageNo = tut.pageNo
                if self.LogPageCompletion is None:
                    self.LogPageCompletion = sm.GetService('infoGatheringSvc').GetEventIGSHandle(const.infoEventTutorialPageCompletion)
                timeSpent = (blue.os.GetWallclockTime() - self.pageTime) / const.SEC
                try:
                    numClicks = uicore.uilib.GetGlobalClickCount() - self.numMouseClicks
                    numKeys = uicore.uilib.GetGlobalKeyDownCount() - self.numKeyboardClicks
                except:
                    numClicks = numKeys = 0

                self.LogPageCompletion(itemID=eve.session.charid, itemID2=tutorialID, int_1=tut.pageNo, float_1=timeSpent)
                tutorialBrowser = self.GetTutorialBrowser()
                if tut.pageNo == 1:
                    if tutorialBrowser and hasattr(tutorialBrowser, 'startTime'):
                        time = (blue.os.GetWallclockTime() - tutorialBrowser.startTime) / const.SEC
                    else:
                        time = 0
                    sm.RemoteSvc('tutorialSvc').LogStarted(tutorialID, tut.pageNo, int(time))
                if tut.pageNo == tut.pageCount:
                    self._ExecutePageAction(tut.pageActionID)
                    if tut.sequenceID:
                        nextTutorialID = self.GetNextInSequence(tutorialID, tut.sequenceID)
                        if nextTutorialID:
                            with util.ExceptionEater('eventLog'):
                                self.LogTutorialEvent(['fromTutorialID',
                                 'fromPageNo',
                                 'toTutorialID',
                                 'toPageNo',
                                 'sequenceID',
                                 'timeInPage',
                                 'numMouseClicks',
                                 'numKeyboardClicks'], 'NextPage', tutorialID, oldPageNo, nextTutorialID, 1, tut.sequenceID, timeSpent, numClicks, numKeys)
                            self.OpenTutorial(nextTutorialID, VID=tut.VID)
                            return
                    if getattr(tutorialBrowser, 'done', False):
                        tutorialBrowser.showTutorialReminder = False
                        settings.char.generic.Set('tutorialCompleted', 1)
                    tutorialBrowser.CloseByUser()
                    return
                self._ExecutePageAction(tut.pageActionID)
                with util.ExceptionEater('eventLog'):
                    self.LogTutorialEvent(['fromTutorialID',
                     'fromPageNo',
                     'toTutorialID',
                     'toPageNo',
                     'sequenceID',
                     'timeInPage',
                     'numMouseClicks',
                     'numKeyboardClicks'], 'NextPage', tutorialID, oldPageNo, tutorialID, tut.pageNo + 1, tut.sequenceID, timeSpent, numClicks, numKeys)
                self.OpenTutorial(tutorialID, tut.pageNo + 1, tut.pageID, VID=tut.VID)

    def ShowCareerFunnel(self):
        CareerFunnelWindow.Open()

    def _ExecutePageAction(self, pageActionID):
        if pageActionID is None:
            return
        if int(pageActionID) == const.tutorialPagesActionOpenCareerFunnel:
            if not util.IsWormholeSystem(eve.session.solarsystemid):
                self.ShowCareerFunnel()

    def GiveGoodies(self, tutorialID, pageID, pageNo):
        retVal = self._GiveTutorialGoodies(tutorialID, pageID, pageNo)
        if retVal is not None:
            stationName = cfg.evelocations.Get(retVal).name
            eve.Message('TutorialGoodiesNotEnoughSpaceInCargo', {'stationName': stationName})

    def SlashCmd(self, slash):
        split = slash.split(' ')
        try:
            VID, pageNo = int(split[1]), int(split[2])
        except:
            log.LogError('Failed to resolve slash command data:', slash, 'Usage: /tutorial <tutvid> <pageno>')
            sys.exc_clear()
            return

        self.OpenTutorial(pageNo=pageNo, force=1, VID=VID, skipCriteria=True)

    def _IsShipWarping(self):
        import destiny
        bp = sm.GetService('michelle').GetBallpark()
        if not bp:
            return
        ship = bp.GetBall(eve.session.shipid)
        if ship is None:
            return
        elif ship.mode == destiny.DSTBALL_WARP:
            return True
        else:
            return False

    def __WarpToTutorial(self):
        errMsg = 'TutYouAreNotInANewbieSystem'
        if util.IsNewbieSystem(eve.session.solarsystemid2):
            if self.Precondition_Checkballpark('groupCloud') or self._IsShipWarping():
                return (1, None)
            self._ShowWarpToButton()
            return (1, None)
        return (2, errMsg)

    def _ShowWarpToButton(self):
        browser = self.GetTutorialBrowser()
        self.waitingForWarpConfirm = True
        browser.sr.next.state = uiconst.UI_NORMAL
        browser.sr.next.OnClick = self._WarpToBallpark
        browser.sr.next.SetLabel(localization.GetByLabel('UI/Commands/WarpTo'))
        browser.sr.text.text = ''

    def _WarpToBallpark(self, *args):
        bp = sm.GetService('michelle').GetRemotePark()
        if bp is None:
            raise RuntimeError('Remote park could not be retrieved.')
        bp.CmdWarpToStuff('tutorial', None)
        self.waitingForWarpConfirm = False
        self._RevertWarpToButton()

    def _RevertWarpToButton(self):
        browser = self.GetTutorialBrowser()
        browser.sr.next.state = uiconst.UI_NORMAL
        browser.sr.next.OnClick = self.Reload
        browser.sr.next.SetLabel(localization.GetByLabel('UI/Commands/Next'))
        browser.sr.text.text = ''

    def _GiveTutorialGoodies(self, tutorialID, pageID, pageNo):
        return sm.RemoteSvc('tutorialLocationSvc').GiveTutorialGoodies(tutorialID, pageID, pageNo)

    def OpenTutorial(self, tutorialID = None, pageNo = None, pageID = None, force = 0, VID = None, skipCriteria = False, checkBack = 0, click = 0):
        if not sm.GetService('experimentClientSvc').IsTutorialEnabled():
            return
        sequenceID = self._GetSequenceIDForTutorial(tutorialID)
        self.LogInfo('OpenTutorial', tutorialID, pageNo, pageID, sequenceID, force, VID, skipCriteria, checkBack, click)
        self.pageTime = blue.os.GetWallclockTime()
        try:
            oldNumMouseClicks = self.numMouseClicks
            oldNumKeyboardClicks = self.numKeyboardClicks
            self.numMouseClicks = uicore.uilib.GetGlobalClickCount()
            self.numKeyboardClicks = uicore.uilib.GetGlobalKeyDownCount()
            diffMouseClicks = self.numMouseClicks - oldNumMouseClicks
            diffKeyboardClicks = self.numKeyboardClicks - oldNumKeyboardClicks
        except:
            diffMouseClicks = diffKeyboardClicks = 0

        tutorialBrowser = self.GetTutorialBrowser()
        if self.loadingTutorial and tutorialBrowser:
            return
        c = self.GetCurrentTutorial()
        if not force and c and c.tutorialID == tutorialID and c.pageNo == pageNo and c.pageID == pageID:
            self.loadingTutorial = 0
            return
        self.loadingTutorial = 1
        try:
            self.uipointerSvc.ClearPointers()
            self.uipointerSvc.RemoveSpaceObjectUiPointers()
            tutorialBrowser.LoadTutorial(tutorialID=tutorialID, pageNo=pageNo, pageID=pageID, sequenceID=sequenceID, force=force, VID=VID, skipCriteria=skipCriteria, checkBack=checkBack, diffMouseClicks=diffMouseClicks, diffKeyboardClicks=diffKeyboardClicks)
        finally:
            self.loadingTutorial = 0

    def CheckTutorialDone(self, sequenceID, tutorialID):
        doneTutorialID = self._GetSequenceDoneStatus(sequenceID)[0]
        if doneTutorialID is None:
            return False
        seq = self._GetSequence(sequenceID)
        for _tutorialID in seq:
            if _tutorialID == tutorialID:
                return True
            if _tutorialID == doneTutorialID:
                return False

        return False

    def CheckAccelerationGateActivation(self):
        if getattr(self, 'nogateactivate', None):
            split_criteria = self.nogateactivate.criteriaName.split('.')
            if len(split_criteria) > 1:
                key = split_criteria[1]
                if self.Precondition_Checknameinballpark(key):
                    info = localization.GetByMessageID(self.nogateactivate.messageTextID)
                    eve.Message('CustomInfo', {'info': info})
                    return False
        return True

    def CheckWarpDriveActivation(self, currentSequenceID = None, currentTutorialID = None):
        if getattr(self, 'nowarpactive', None):
            split_criteria = self.nowarpactive.criteriaName.split('.')
            if len(split_criteria) > 1:
                key = split_criteria[1]
                tutorial_split_criteria = key.split(':')
                if len(tutorial_split_criteria) > 1:
                    sequenceID, tutorialID = tutorial_split_criteria
                    if currentSequenceID is None:
                        currentSequenceID = sequenceID
                    if currentTutorialID is None:
                        currentTutorialID = tutorialID
                    sequenceID, tutorialID = int(sequenceID), int(tutorialID)
                    if sequenceID == currentSequenceID and not self.CheckTutorialDone(sequenceID, tutorialID):
                        info = localization.GetByMessageID(self.nowarpactive.messageTextID)
                        eve.Message('CustomInfo', {'info': info})
                        return False
        return True

    def _IsInInventory(self, inventory, key, id, pre = '', flags = None):
        if not inventory:
            return False
        key = key.lower()
        func = getattr(inventory, 'List%s' % pre, None)
        for rec in func():
            if key.startswith('category') and rec.categoryID == id or key.startswith('group') and rec.groupID == id or key.startswith('type') and rec.typeID == id:
                if not flags:
                    return True
                if rec.flagID in flags:
                    return True

        return False

    def SetCriterias(self, criterias):
        self.nogateactivate = None
        self.nowarpactive = None
        for criteriaData in self._PrioritizeCriterias(criterias):
            split_criteria = criteriaData.criteriaName.split('.')
            if len(split_criteria) > 1:
                funcName, key = split_criteria
                if funcName.lower() == 'IfNameInBallparkThenNoGateActivation'.lower():
                    self.nogateactivate = criteriaData
                elif funcName.lower() == 'IfNotTutorialDoneThenNoWarp'.lower():
                    self.nowarpactive = criteriaData

    def ParseCriterias(self, criterias, what = '', tutorialBrowser = None, tutorialID = None):
        for criteriaData in self._PrioritizeCriterias(criterias):
            split_criteria = criteriaData.criteriaName.split('.')
            if len(split_criteria) > 1:
                funcName, key = split_criteria
                if funcName in ('stationsvc', 'stationbtnblink') and self.Precondition_Wndopen('map'):
                    funcName = 'Precondition_Wndclosed'
                    _func = getattr(self, funcName, None)
                    uthread.new(self._WaitForCriteria, 'map', funcName, _func, tutorialBrowser)
                    return self.GetCriteria(174)
                if funcName in 'IfNotTutorialDoneThenNoWarp':
                    if not session.stationid and bool(session.solarsystemid):
                        r = self.__WarpToTutorial()
                        if r[0] in (0, 2):
                            if r[0] == 0:
                                tutorialBrowser.CloseByUser()
                            if r[1] is not None:
                                ret = eve.Message(r[1])
                func = getattr(self, 'Precondition_%s' % funcName.capitalize(), None)
                if func:
                    ok = func(key)
                    if not ok:
                        if funcName.lower() in ('wndopen', 'wndclosed', 'session', 'stationsvc', 'checklocktarget', 'checkballpark', 'checknotinballpark', 'checkcomplex', 'checkactivemodule', 'checkcargo', 'checknotincargo', 'checkhangar', 'checknotinship', 'checknotinhangar', 'checkincargoorhangar', 'checknameinballpark', 'checknamenotinballpark', 'checkhasskill', 'checkskilltraining', 'checktutorialagent', 'checkdronebay', 'checknotindronebay', 'entityspawnproximity', 'inspaceorentityspawnproximity'):
                            uthread.new(self._WaitForCriteria, key, funcName, func, tutorialBrowser)
                        if funcName == 'checkBallpark' and key == 'groupCloud' and not self._IsShipWarping():
                            self._ShowWarpToButton()
                        if criteriaData.messageTextID:
                            return criteriaData
                        raise RuntimeError('ParseCriterias: Missing Criteria message!!!<br>Criteraname: (%s)' % criteriaData.criteriaName)
                else:
                    log.LogError('Unknown precondition', funcName, 'Precondition_%s' % funcName.capitalize())

    def _WaitForCriteria(self, key, funcName, func, tutorialBrowser):
        k = (funcName, key)
        if k == self.waitingForCriteria:
            self.LogWarn('Already waiting for', k)
            return
        self.waitingForCriteria = k
        self.waiting = tutorialBrowser
        while self.waiting and not self.waiting.destroyed and not func(key):
            blue.pyos.synchro.SleepWallclock(250)

        self.waitingForCriteria = None
        if self.waiting and not self.waiting.destroyed:
            if self.waiting and self.waiting.current:
                tut = self.waiting.current
                with util.ExceptionEater('eventLog'):
                    diffMouseClicks = uicore.uilib.GetGlobalClickCount() - self.numMouseClicks
                    diffKeyboardClicks = uicore.uilib.GetGlobalKeyDownCount() - self.numKeyboardClicks
                    self.LogTutorialEvent(['tutorialID',
                     'pageNo',
                     'sequenceID',
                     'numMouseClicks',
                     'numKeyboardClicks'], 'CriteriaMet', tut.tutorialID, tut.pageNo, tut.sequenceID, diffMouseClicks, diffKeyboardClicks)
            self._ReloadTutorialBrowser(self.waiting)

    def _PrioritizeCriterias(self, criterias):
        criteriaData = [ self.GetCriteria(criteria.criteriaID) for criteria in criterias ]
        other = []
        rookieCheck = []
        for i, cd in enumerate(criteriaData):
            if not cd:
                continue
            if cd.criteriaName.startswith('rookieState'):
                c = cd.criteriaName.split('.')[-1].replace('_', '.')
                if c != 'None':
                    rookieCheck.append((float(c), cd))
                else:
                    rookieCheck.append((0.0, cd))
            elif cd.criteriaName.startswith('IfNotTutorialDoneThenNoWarp') and cd not in other:
                other.append((0, cd))
            elif cd not in other:
                other.append((i, cd))

        rookieCheck = uiutil.SortListOfTuples(rookieCheck)
        other = uiutil.SortListOfTuples(other)
        return rookieCheck[-1:] + other

    def Precondition_Ifnameinballparkthennogateactivation(self, *args):
        return True

    def Precondition_Ifnottutorialdonethennowarp(self, *args):
        return True

    def Precondition_Rookiestate(self, key):
        if key == 'None':
            eve.SetRookieState(None)
        else:
            eve.SetRookieState(float(key.replace('_', '.')))
        return True

    def Precondition_Session(self, key):
        key = key.lower()
        if key == 'station':
            return bool(eve.session.stationid)
        if key == 'inflight':
            sol, bp = False, False
            sol = bool(eve.session.solarsystemid)
            if sol:
                bp = bool(sm.GetService('michelle').GetRemotePark())
            return sol and bp
        if key in ('station_inflight', 'inflight_station'):
            return bool(eve.session.stationid) or bool(eve.session.solarsystemid)

    def Precondition_Checkballpark(self, key):
        if eve.session.solarsystemid:
            id = getattr(const, key, None)
            if not id:
                log.LogWarn('Precondition_Checkballpark Failed:, %s not found in const' % key)
                return False
            ballpark = sm.GetService('michelle').GetBallpark()
            if ballpark is None:
                return False
            for itemID, ball in ballpark.balls.iteritems():
                if ballpark is None:
                    break
                slimItem = ballpark.GetInvItem(itemID)
                if not slimItem:
                    continue
                if key.startswith('category') and slimItem.categoryID == id:
                    return True
                if key.startswith('group') and slimItem.groupID == id:
                    return True
                if key.startswith('type') and slimItem.typeID == id:
                    return True

        return False

    def Precondition_Checknotinballpark(self, key):
        return not self.Precondition_Checkballpark(key)

    def Precondition_Checktutorialagent(self, key):
        if eve.session.stationid:
            agents = sm.GetService('agents').GetAgentsByStationID()[eve.session.stationid]
            tutAgents = sm.GetService('agents').GetTutorialAgentIDs()
            for agent in agents:
                if agent.agentID in tutAgents:
                    return True

        return False

    def Precondition_Checknameinballpark(self, key):
        if eve.session.solarsystemid:
            ballpark = sm.GetService('michelle').GetBallpark()
            if ballpark is None:
                return False
            for itemID, ball in ballpark.balls.iteritems():
                if ballpark is None:
                    break
                slimItem = ballpark.GetInvItem(itemID)
                if not slimItem:
                    continue
                if uix.GetSlimItemName(slimItem).replace(' ', '').lower() == key.replace(' ', '').lower():
                    return True

        return False

    def Precondition_Checknamenotinballpark(self, key):
        return not self.Precondition_Checknameinballpark(key)

    def Precondition_Checkcomplex(self, key):
        if eve.session.solarsystemid:
            return True
        return False

    def Precondition_Wndopen(self, key):
        self.LogInfo('Precondition_Wndopen key:', key)
        key = key.lower()
        if key == 'map':
            return sm.GetService('viewState').IsViewActive('systemmap', 'starmap')
        if key == 'tacticaloverlay':
            return not not settings.user.overview.Get('viewTactical', 0)
        if key in ('ships', 'items', 'cargo', 'dronebay'):
            wnd = InventoryWindow.GetIfOpen()
            if not wnd:
                return False
            if key == 'ships':
                return wnd.currInvID == ('StationShips', session.stationid)
            if key == 'items':
                return wnd.currInvID == ('StationItems', session.stationid)
            if key == 'cargo':
                return wnd.currInvID == ('ShipCargo', util.GetActiveShip())
            if key == 'dronebay':
                return wnd.currInvID == ('ShipDroneBay', util.GetActiveShip())
        if bool(uicontrols.Window.IsOpen(key)):
            return True
        if eve.session.stationid and sm.GetService('station').GetSvc(key) is not None:
            return True
        return False

    def Precondition_Wndclosed(self, key):
        return not self.Precondition_Wndopen(key)

    def Precondition_Stationsvc(self, key):
        self.LogInfo('Precondition_Stationsvc key:', key)
        key = key.lower()
        if eve.session.stationid:
            while not LobbyWindow.GetIfOpen():
                blue.pyos.synchro.SleepWallclock(1)

            if key == 'reprocessingplant':
                return sm.GetService('reprocessing').IsVisible()
            if key == 'fitting':
                wnd = FittingWindow.GetIfOpen()
                if wnd:
                    wnd.Maximize()
                    return wnd
            return not not sm.GetService('station').GetSvc(key)
        return False

    def Precondition_Expanded(self, key):
        if eve.session.solarsystemid2:
            return sm.GetService('tactical').IsExpanded(key)
        return False

    def Precondition_Checklocktarget(self, key):
        if eve.session.solarsystemid2:
            targets = sm.GetService('target').GetTargets()
            if key == '*':
                return not not targets
            if key == 'None':
                return not targets
            if not targets:
                return False
            groupID = getattr(const, 'group%s' % key, None)
            if not groupID:
                log.LogWarn('Precondition_Checklocktarget Failed; %s is not recognized as group')
                return False
            for targetID in targets:
                slimItem = uix.GetBallparkRecord(targetID)
                if not slimItem:
                    continue
                if slimItem.groupID == groupID:
                    return True

        return False

    def Precondition_Checkactivemodule(self, key):
        if eve.session.shipid:
            module = uicore.layer.shipui.GetModuleForFKey(key)
            if not module:
                return False
            return module.def_effect.isActive
        return False

    def Precondition_Checkship(self, key, condname = 'Precondition_Checkship'):
        if eve.session.shipid:
            id = getattr(const, key, None)
            if not id:
                log.LogWarn('%s Failed:, %s not found in const' % (condname, key))
                return False
            ship = sm.GetService('godma').GetItem(eve.session.shipid)
            key = key.lower()
            if key.startswith('category'):
                return ship.categoryID == id
            if key.startswith('group'):
                return ship.groupID == id
            if key.startswith('type'):
                return ship.typeID == id
        return False

    def Precondition_Checknotinship(self, key):
        return not self.Precondition_Checkship(key, 'Precondition_Checknotinship')

    def Precondition_Checkfitted(self, key, condname = 'Precondition_Checkfitted'):
        if eve.session.shipid:
            id = getattr(const, key, None)
            if not id:
                log.LogWarn('%s Failed: %s not found in const' % (condname, key))
                return False
            inventory = sm.GetService('invCache').GetInventoryFromId(eve.session.shipid)
            return self._IsInInventory(inventory, key, id, flags=uix.FittingFlags())
        return False

    def Precondition_Checknotfitted(self, key):
        return not self.Precondition_Checkfitted(key, 'Precondition_Checknotfitted')

    def Precondition_Checkhangar(self, key, condname = 'Precondition_Checkhangar'):
        if eve.session.stationid:
            id = getattr(const, key, None)
            if not id:
                log.LogWarn('%s Failed:, %s not found in const' % (condname, key))
                return False
            inventory = sm.GetService('invCache').GetInventory(const.containerHangar)
            return self._IsInInventory(inventory, key, id)
        return False

    def Precondition_Checknotinhangar(self, key):
        return not self.Precondition_Checkhangar(key, 'Precondition_Checknotinhangar')

    def Precondition_Checkcargo(self, key, condname = 'Precondition_Checkcargo'):
        if eve.session.shipid:
            id = getattr(const, key, None)
            if not id:
                log.LogWarn('%s Failed: %s not found in const' % (condname, key))
                return False
            inventory = sm.GetService('invCache').GetInventoryFromId(eve.session.shipid)
            return self._IsInInventory(inventory, key, id, 'Cargo')
        return False

    def Precondition_Checknotincargo(self, key):
        return not self.Precondition_Checkcargo(key, 'Precondition_Checknotincargo')

    def Precondition_Checkdronebay(self, key, condname = 'Precondition_Checkdronebay'):
        if eve.session.shipid:
            id = getattr(const, key, None)
            if not id:
                log.LogWarn('%s Failed: %s not found in const' % (condname, key))
                return False
            inventory = sm.GetService('invCache').GetInventoryFromId(eve.session.shipid)
            return self._IsInInventory(inventory, key, id, 'DroneBay')
        return False

    def Precondition_Checknotindronebay(self, key):
        return not self.Precondition_Checkdronebay(key, 'Precondition_Checknotindronebay')

    def Precondition_Checkincargoorhangar(self, key):
        return self.Precondition_Checkcargo(key, 'Precondition_Checkincargoorhangar') or self.Precondition_Checkhangar(key, 'Precondition_Checkincargoorhangar')

    def Precondition_Checkskilltraining(self, key):
        inTraining = sm.GetService('skills').SkillInTraining()
        if not inTraining:
            return False
        if key == '*':
            return True
        id = getattr(const, key, None)
        if not id:
            log.LogWarn('Precondition_Checkskilltraining Failed:, %s not found in const' % key)
            return False
        if inTraining.typeID == id:
            return True
        return False

    def Precondition_Checkhasskill(self, key):
        id = getattr(const, key, None)
        if not id:
            log.LogWarn('Precondition_Checkhasskill Failed:, %s not found in const' % key)
            return False
        return not not sm.GetService('skills').HasSkill(id)

    def Precondition_Stationbtnblink(self, key):
        if eve.session.stationid:
            while not LobbyWindow.GetIfOpen():
                blue.pyos.synchro.SleepWallclock(1)

            sm.GetService('station').BlinkButton(key)
        return True

    def Precondition_Shipuibtnblink(self, key):
        if eve.session.solarsystemid and uicore.layer.shipui.isopen:
            uicore.layer.shipui.BlinkButton(key)
        return True

    def Precondition_Headerblink(self, key):
        if eve.session.solarsystemid2:
            sm.GetService('tactical').BlinkHeader(key)
        return True

    def Precondition_Activeitembtnblink(self, key):
        if eve.session.solarsystemid2:
            selecteditem = ActiveItemWindow.GetIfOpen()
            if selecteditem:
                selecteditem.BlinkBtn(key)
        return True

    def Precondition_Neocombtnblink(self, key):
        if eve.session.solarsystemid2:
            sm.GetService('neocom').Blink(key, numBlinks=60)
        return True

    def Precondition_Mapbtnblink(self, key):
        self.LogError('This map blick method has been depricated')

    def Precondition_Tutorialbtnblink(self, key):
        key = key.lower()
        tutorialBrowser = self.GetTutorialBrowser()
        if not tutorialBrowser:
            return False
        blue.pyos.synchro.Yield()
        if key == 'ok' and tutorialBrowser.nextBtn:
            tutorialBrowser.nextBtn.Blink()
        elif key == 'back' and tutorialBrowser.backBtn:
            tutorialBrowser.backBtn.Blink()
        return True

    def Precondition_Tutorialdone(self, key):
        tutorialBrowser = self.GetTutorialBrowser()
        if not tutorialBrowser:
            return False
        tutorialBrowser.done = True
        return True

    def Precondition_Windowpos(self, key):
        key = key.replace('dw', str(uicore.desktop.width)).replace('dh', str(uicore.desktop.height))
        pos = key.split(',')
        if len(pos) != 2:
            return False
        tutorialBrowser = self.GetTutorialBrowser()
        if not tutorialBrowser:
            return False
        tutorialBrowser.left = eval(pos[0])
        tutorialBrowser.top = eval(pos[1])
        return True

    def Precondition_Agentdialogueopen(self, key):
        for window in uicore.registry.GetWindows():
            if isinstance(window, AgentDialogueWindow):
                return True

        return False

    def Precondition_Characterhasanyskillinjected(self, key):
        skillSvc = sm.GetService('skills')
        skillIDs = key.split(',')
        for skillID in skillIDs:
            skillIDNum = int(skillID)
            if skillSvc.HasSkill(skillIDNum) is not None:
                return True

        return False

    entitySpawnDict = {1: {const.typeAmarrCaptainsQuarters: 2594,
         const.typeCaldariCaptainsQuarters: 2596,
         const.typeGallenteCaptainsQuarters: 2597,
         const.typeMinmatarCaptainsQuarters: 4544}}

    def Precondition_Entityspawnproximity(self, key):
        """
            This tests if the character is in close proximity to the undock button. It needs
            to work with all 4 CQ's, which is why the information is basically hardcoded.
        """
        if not session.worldspaceid:
            return False
        spawnIDType, distance = key.split(':')
        spawnIDType = int(spawnIDType)
        distance = float(distance)
        worldspaceTypeID = sm.GetService('worldSpaceClient').GetWorldSpaceTypeIDFromWorldSpaceID(session.worldspaceid)
        spawnID = self.entitySpawnDict.get(spawnIDType, {}).get(worldspaceTypeID, None)
        if spawnID is None or spawnID not in cfg.entitySpawns:
            return False
        spawnRow = cfg.entitySpawns.Get(spawnID)
        spawnPosition = (spawnRow.spawnPointX, spawnRow.spawnPointY, spawnRow.spawnPointZ)
        playerEnt = sm.GetService('entityClient').GetPlayerEntity()
        if not playerEnt:
            return False
        playerPos = playerEnt.GetComponent('position').position
        return geo2.Vec3Distance(playerPos, spawnPosition) <= distance

    def Precondition_Inspaceorentityspawnproximity(self, key):
        if self.Precondition_Session('inflight'):
            return True
        if self.Precondition_Entityspawnproximity(key):
            return True
        return False

    def ParseActions(self, actions):
        for action in actions:
            actionName = const.actionTypes.get(action.actionTypeID)
            if actionName:
                function = getattr(self, 'Action_%s' % actionName, None)
                if function is None:
                    msg = 'Unable to match tutorial action with action function. '
                    msg += 'actionID: %s, actionTypeID: %s, actionType: %s.' % (action.actionID, action.actionTypeID, actionName)
                    log.LogError(msg)
                    return
                function(action.actionData)
            else:
                self.LogError('unable to find the requested tutorial action type', action)

    def _ActionWaitForCriteria(self, criteria, actionData, func):
        """
        Polls criteria until they all pass, and then executes a action.
        Note: Stops polling and dies silently when the tutorial window advances or
              is closed.
        """
        tasklet = uthread.new(self._ActionWaitForCriteriaTasklet, criteria, actionData, func)
        tasklet.context = 'tutorial::_ActionWaitForCriteria'

    def _ActionWaitForCriteriaTasklet(self, criteria, actionData, func):
        waiting = self.GetTutorialBrowser(create=False)
        while True:
            blue.pyos.synchro.SleepWallclock(250)
            if not waiting or waiting.destroyed or waiting is not self.GetTutorialBrowser(create=False):
                return
            for preconditionFunc, key in criteria:
                passed = preconditionFunc(key)
                if not passed:
                    break

            if passed:
                break

        func(actionData)

    def _ParseActionCriteria(self, actionData):
        actionData, junk, criteriaText = actionData.lower().partition('criteria=')
        criteriaText = criteriaText.strip().lstrip('[').rstrip(']')
        criteria = []
        for string in criteriaText.split('),'):
            criteriaFuncName, junk, key = string.partition('(')
            key = key.rstrip(')')
            criteriaFunc = getattr(self, 'Precondition_%s' % criteriaFuncName.capitalize(), None)
            if criteriaFunc:
                criteria.append((criteriaFunc, key))

        return (criteria, actionData)

    def Action_Open_MLS_Message(self, actionData):
        eve.Message(actionData)

    def Action_Neocom_Button_Blink(self, actionData):
        actionData = actionData.lower()
        splitData = actionData.split('.')
        if len(splitData) == 3:
            key, blinkcount, frequency = splitData
            sm.GetService('neocom').Blink(key, numBlinks=int(blinkcount))
        else:
            sm.GetService('neocom').Blink(actionData)

    def Action_Play_MLS_Audio(self, actionData):
        message = cfg.GetMessage(actionData)
        audioName = message.audio
        if not audioName:
            return
        if audioName.startswith('wise:/'):
            audioName = audioName[6:]
        self.audioEmitter.SendEvent(u'stop_all_sounds')
        self.audioEmitter.SendEvent(unicode(audioName))

    def Action_Poll_Criteria_Open_Tutorial(self, actionData):
        criteria, actionData = self._ParseActionCriteria(actionData)
        self._ActionWaitForCriteria(criteria, actionData, self._Action_Open_Tutorial)

    def _Action_Open_Tutorial(self, actionData):
        actionData = actionData.lower().lstrip('tutorialid=')
        tutorialID, junk, actionData = actionData.partition(',')
        pageNo = actionData.lstrip('pageno=').strip(',')
        tutorialID = int(tutorialID)
        pageNo = int(pageNo) if pageNo else None
        self.OpenTutorialSequence_Check(tutorialID=tutorialID, force=True, pageNo=pageNo)

    def RetrieveIsTutorialNoob(self):
        return blue.os.GetWallclockTime() < sm.RemoteSvc('userSvc').GetCreateDate() + 14 * const.DAY

    def IsTutorialWindowUnkillable(self):
        return session.role & serviceConst.ROLE_GML == 0 and self.tutorialNoob

    def GetCharacterTutorialState(self):
        self.tutorialNoob = self.RetrieveIsTutorialNoob()
        showTutorials = settings.char.ui.Get('showTutorials', None)
        sequenceStatus = settings.char.ui.Get('SequenceStatus', None)
        sequenceDoneStatus = settings.char.ui.Get('SequenceDoneStatus', None)
        if showTutorials is not None and sequenceStatus is not None and sequenceDoneStatus is not None:
            return
        rs = sm.RemoteSvc('tutorialSvc').GetCharacterTutorialState()
        if not rs or len(rs) == 0:
            return
        tutorials = self.GetTutorials()
        previousTutorialIdFromTutorialId = {}
        for tutorialID in tutorials.keys():
            tutorial = tutorials[tutorialID]
            nextTutorialID = self._GetNextTutorial(tutorialID)
            if not nextTutorialID:
                continue
            previousTutorialIdFromTutorialId[nextTutorialID] = tutorialID

        sequenceStatus = {}
        sequenceDoneStatus = {}
        for r in rs:
            showTutorials = int(r.eventTypeID != 158)
            if not showTutorials:
                continue
            sequence = []
            tutorialID = r.tutorialID
            i = 0
            while tutorialID not in self.GetValidTutorials():
                i += 1
                if i > 100:
                    break
                tutorialID = previousTutorialIdFromTutorialId.get(tutorialID, None)
                if tutorialID:
                    sequence.append(tutorialID)

            sequenceStatus[tutorialID] = [(r.tutorialID, r.pageID), 'done'][r.eventTypeID in (155, 158)]
            sequenceDoneStatus[tutorialID] = (r.tutorialID, 1)

        if showTutorials is not None:
            settings.char.ui.Set('showTutorials', showTutorials)
        if len(sequenceStatus):
            settings.char.ui.Set('SequenceStatus', sequenceStatus)
        if len(sequenceDoneStatus):
            settings.char.ui.Set('SequenceDoneStatus', sequenceDoneStatus)

    def ChangeTutorialWndState(self, visible = 0):
        tutorialWnd = TutorialWindow.GetIfOpen()
        if tutorialWnd:
            if tutorialWnd.IsMinimized():
                return
            if visible:
                tutorialWnd.display = True
            else:
                tutorialWnd.display = False

    def GetCareerFunnelAgents(self):
        if len(self.careerAgents):
            return self.careerAgents
        allCareerAgents = sm.GetService('agents').GetAgentsByType(const.agentTypeCareerAgent)
        for agent in allCareerAgents:
            if agent.divisionID not in self.careerAgents:
                self.careerAgents[agent.divisionID] = {}
                self.careerAgents[agent.divisionID]['agent'] = {}
                self.careerAgents[agent.divisionID]['station'] = {}
            self.careerAgents[agent.divisionID]['agent'][agent.agentID] = agent
            self.careerAgents[agent.divisionID]['station'][agent.agentID] = sm.GetService('map').GetStation(agent.stationID)

        return self.careerAgents

    def Action_SpaceObject_UI_Pointer(self, actionData):
        kwargs = self.ParseActionDataToDict(actionData)
        typeID = None
        groupID = None
        hint = None
        message = None
        if 'typeID' in kwargs:
            typeID = int(kwargs['typeID'])
        if 'groupID' in kwargs:
            groupID = int(kwargs['groupID'])
        if 'hint' in kwargs:
            hint = kwargs['hint']
        if 'message' in kwargs:
            message = kwargs['message']
        if typeID is not None or groupID is not None:
            self.uipointerSvc.AddSpaceObjectTypeUiPointer(typeID, groupID, message, hint, self.GetTutorialBrowser(create=False))
        else:
            self.LogWarn('Tutorial Dungeon UI Pointer did not find a typeID nor groupID', kwargs)

    def ParseActionDataToDict(self, actionData):
        kwargs = {}
        results = re.findall('([^ =]+) *= *("[^"]*"|[^ ]*)', actionData)
        for key, value in results:
            kwargs[key] = value.strip('"')

        return kwargs


class GoodieInfoHelper():

    def __init__(self, itemID):
        self.itemID = itemID

    def GetMenu(self, *args):
        return [(uiutil.MenuLabel('UI/Commands/ShowInfo'), sm.StartService('info').ShowInfo, (self.itemID,))]
