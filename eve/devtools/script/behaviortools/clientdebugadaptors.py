#Embedded file name: eve/devtools/script/behaviortools\clientdebugadaptors.py
import logging
from brennivin.messenger import Messenger
import eve.common.script.net.eveMoniker as moniker
from eve.devtools.script.behaviortools.debugwindow import BehaviorDebugWindow
import uthread2
logger = logging.getLogger(__name__)
EVENT_BEHAVIOR_DEBUG_UPDATE = 'OnBehaviorDebugUpdate'
EVENT_BEHAVIOR_DEBUG_CONNECT_REQUEST = 'OnBehaviorDebugConnectRequest'
EVENT_BEHAVIOR_DEBUG_DISCONNECT_REQUEST = 'OnBehaviorDebugDisconnectRequest'

class UpdateListener(object):

    def __init__(self):
        self.messenger = Messenger()
        self.behaviorDebuggersByItemId = {}
        sm.RegisterForNotifyEvent(self, EVENT_BEHAVIOR_DEBUG_UPDATE)
        sm.RegisterForNotifyEvent(self, EVENT_BEHAVIOR_DEBUG_CONNECT_REQUEST)
        sm.RegisterForNotifyEvent(self, EVENT_BEHAVIOR_DEBUG_DISCONNECT_REQUEST)

    def AddObserverForItemId(self, itemId, handler):
        if itemId in self.messenger.signalsByMessageName:
            self.messenger.signalsByMessageName[itemId].clear()
        self.messenger.SubscribeToMessage(itemId, handler)

    def RemoveObserverForItemId(self, itemId, handler):
        try:
            self.messenger.UnsubscribeFromMessage(itemId, handler)
        except:
            logger.error('Failed to remove observer itemID=%s handler=%s', itemId, handler)

    def OnBehaviorDebugUpdate(self, itemID, *args, **kwargs):
        self.messenger.SendMessage(itemID, *args, **kwargs)

    def TryConnectDebugger(self, itemID):
        try:
            debugger = ClientBehaviorDebugger(itemID)
            debugger.Connect()
            self.behaviorDebuggersByItemId[itemID] = debugger
        except:
            logger.exception('failed to connect to debugger for itemID=%s', itemID)

    def OnBehaviorDebugConnectRequest(self, itemIDs):
        itemIDs = sorted(itemIDs)
        for itemID in itemIDs:
            self.TryConnectDebugger(itemID)

    def TryDisconnectDebugger(self, itemID):
        try:
            debugger = self.behaviorDebuggersByItemId.pop(itemID)
            debugger.Disconnect()
        except:
            logger.exception('failed to disconnect to debugger for itemID=%s', itemID)

    def OnBehaviorDebugDisconnectRequest(self, itemIDs):
        for itemID in itemIDs:
            self.TryDisconnectDebugger(itemID)

    def HasDebugger(self, itemID):
        return itemID in self.behaviorDebuggersByItemId


updateListener = UpdateListener()

class ClientBehaviorDebugger(object):

    def __init__(self, itemID):
        self.itemID = itemID
        self.tree = []
        self.treeMap = {}
        self.events = []
        self.debugWindow = None
        self.isConnected = False

    def Connect(self):
        logger.debug('Debugger connecting to behavior of entity %s', self.itemID)
        updateListener.AddObserverForItemId(self.itemID, self.OnBehaviorDebugUpdate)
        entityLocation = moniker.GetEntityLocation()
        treeData = entityLocation.EnableBehaviorDebugging(self.itemID)
        self.isConnected = True
        uthread2.StartTasklet(self.SetupDebugTree, treeData)

    def Disconnect(self):
        logger.debug('Debugger disconnecting from behavior of entity %s', self.itemID)
        try:
            updateListener.RemoveObserverForItemId(self.itemID, self.OnBehaviorDebugUpdate)
            entityLocation = moniker.GetEntityLocation()
            entityLocation.DisableBehaviorDebugging(self.itemID)
            self.isConnected = False
            if self.debugWindow is not None:
                self.debugWindow.Close()
            sm.UnregisterForNotifyEvent(self, 'OnSessionChanged')
        except:
            logger.exception('Failed while disconnecting :(')

    def OnBehaviorDebugUpdate(self, events, taskStatuses, tasksSeen, blackboards, *args, **kwargs):
        if self.debugWindow is None:
            return
        self.debugWindow.LoadEvents(events)
        self.debugWindow.UpdateStatuses(taskStatuses)
        self.debugWindow.UpdateTasksSeen(tasksSeen)
        self.debugWindow.LoadBlackboard(blackboards)

    def SetupDebugTree(self, treeData):
        self.debugWindow = BehaviorDebugWindow.Open(windowID='BehaviorDebugWindow_%d' % self.itemID)
        self.debugWindow.SetController(self)
        self.debugWindow.LoadBehaviorTree(treeData)
        sm.RegisterForNotifyEvent(self, 'OnSessionChanged')

    def IsConnected(self):
        return self.isConnected

    def OnSessionChanged(self, isRemote, sess, change):
        if 'solarsystemid2' in change:
            if self.debugWindow is not None:
                self.debugWindow.Close()
