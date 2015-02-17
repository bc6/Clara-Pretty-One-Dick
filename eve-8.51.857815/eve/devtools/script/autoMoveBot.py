#Embedded file name: eve/devtools/script\autoMoveBot.py
"""
Contains the EVE Auto-move-bot for moving people, who enter a certain channel and type
a certain phrase, to a specific system.
There is a UI element which can be used for changing the default-values of the
automovebot.
"""
from service import Service, ROLE_GMH
import blue
import types
import chat
import uthread
import locks
import uiutil
import carbonui.const as uiconst
import const
import uiprimitives
import uicontrols

class AutoMoveBot(Service):
    """
    The AutoMoveBot Service.
    It sits on a channel where it watches and waits for a specific phrase from a user
    and then moves that user to a speicific system.
    This bot expects to run under a user-account with elevated privileges.
    This allows it to kick users from the moveme-channel without having to be the owner
    or moderator on that channel.
    """
    __guid__ = 'svc.automovebot'
    __notifyevents__ = ['OnChannelsJoined', 'OnLSC']
    CHANNEL_NAME = 'moveme'
    MOVE_PHRASE = 'moveme'
    DESTINATION_ID = 30003280

    def __init__(self):
        Service.__init__(self)
        self.lscService = sm.GetService('LSC')
        self.slashRemote = sm.RemoteSvc('slash')
        self.channelID = None
        self.waitingList = []
        self.moveRunning = False
        self.channelName = self.CHANNEL_NAME
        self.movePhrase = self.MOVE_PHRASE
        self.destinationID = self.DESTINATION_ID

    def Stop(self, memStream = None):
        """
        Stop the service and force the move-thread to terminate.
        """
        self.StopBot()

    def StartBot(self):
        """
        Start the automove-bot.
        """
        self.waitingList = []
        sm.ScatterEvent('OnAutoMoveBotQueueChange', 0)
        uthread.new(self.PrepareMoveChannel)
        self.moveRunning = True
        uthread.new(self.MoveCharacterThread)
        sm.ScatterEvent('OnAutoMoveBotStateChanged', 'start')

    def StopBot(self):
        """
        Stop the automove-bot.
        Leave the move-channel and kill the move-thread.
        """
        self.moveRunning = False
        self.lscService.LeaveChannel(self.GetChannelIDFromName(self.channelName), unsubscribe=1)
        sm.ScatterEvent('OnAutoMoveBotStateChanged', 'stop')

    def GetChannelIDFromName(self, name):
        """
        Helper for getting channelID by using the name of the channel.
        
        Params:
            name - Channel name used for resolving the channel id.
        """
        for channel in self.lscService.GetChannels():
            if type(channel) == blue.DBRow:
                if channel[4] == name.lower():
                    return channel[0]

    @staticmethod
    def GetCharacterIDFromLSC(fullID):
        """
        Internal helper for getting the integer charID from the LSC Service CharID.
        
        Params:
            fullID - The full character ID as it comes from the LSC system.
        """
        if type(fullID) == types.IntType:
            return fullID
        return fullID[2][0]

    def PrepareMoveChannel(self):
        """
        Tries to join the move channel and create it if it doesn't exist.
        """
        channelID = self.GetChannelIDFromName(self.channelName)
        if channelID:
            self.lscService.JoinChannel(channelID)
            self.channelID = channelID
        else:
            self.lscService.CreateOrJoinChannel(self.channelName)

    def OnChannelsJoined(self, channelIDs):
        """
        Handler for catching when we've joined the Move-channel so we can enable our
        move-mechanism.
        
        Params:
            channelIDs - List of channel IDs joined.
        """
        if type(channelIDs) != types.ListType:
            return
        for channelID in channelIDs:
            channelInfo = self.lscService.GetChannelInfo(channelID).Get('info')
            if channelInfo is None:
                continue
            name = channelInfo[2]
            if self.channelName.lower() == name:
                self.channelID = channelID
                break

    def OnLSC(self, channelID, estimatedMembercount, method, who, *args):
        """
        React to a Large-Scale Chat Event.
        
        Monitors the chat on the Move-channel. Moving users that speak the phrase
        defined by self.movePhrase.
        
        Params:
            channelID - The id of the channel. Tuple or integer.
            estimatedMembercount - Estimated member count of the channel.
            method - The method used on the channel.
            who - The character using the method.
            *args - Arguments of the method used.
        """
        if self.channelID is None:
            return
        if channelID != self.channelID:
            return
        charID = self.GetCharacterIDFromLSC(who)
        if charID == session.charid or charID in self.waitingList:
            return
        if method == 'SendMessage':
            if len(args[0]) == 0:
                return
            message = args[0][0]
            if message.lower() == self.movePhrase.lower():
                with locks.TempLock('waitingList', locks.RLock):
                    self.waitingList.insert(0, charID)
                    sm.ScatterEvent('OnAutoMoveBotQueueChange', len(self.waitingList))

    def MoveCharacterThread(self):
        """
        Thread wrapper for the MoveCharacter mechanism.        
        This thread will run while self.moveRunning is True.
        """
        while self.moveRunning is True:
            if len(self.waitingList) > 0:
                charID = None
                with locks.TempLock('waitingList', locks.RLock):
                    charID = self.waitingList.pop()
                    sm.ScatterEvent('OnAutoMoveBotQueueChange', len(self.waitingList))
                self.MoveCharacter(charID)
            else:
                blue.pyos.synchro.SleepWallclock(2000)

    def MoveCharacter(self, charID):
        """
        Mechanism for moving a character to the destination-system.
        
        Params:
            charID -- The id of the character to move.
        """
        retriesLeft = 10
        while retriesLeft > 0:
            try:
                self.slashRemote.SlashCmd('/tr %s %s' % (charID, self.destinationID))
                self.lscService.AccessControl(self.channelID, charID, chat.CHTMODE_DISALLOWED, None, None)
                self.lscService.AccessControl(self.channelID, charID, chat.CHTMODE_NOTSPECIFIED, None, None)
                break
            except (UserError, RuntimeError):
                retriesLeft -= 1
                blue.pyos.synchro.SleepSim(2000)


class AutoMoveBotWnd(uicontrols.Window):
    """
    The Window for the Automove bot.
    """
    __guid__ = 'form.autoMoveBot'
    __neocommenuitem__ = (('AutoMoveBot', 'autoMoveBot'), True, ROLE_GMH)
    __notifyevents__ = ['OnAutoMoveBotQueueChange', 'OnAutoMoveBotStateChanged']

    def ApplyAttributes(self, attributes):
        """
        Apply Attributes to the window.
        
        Params:
            attributes -- Attributes to apply to the UI Window.
        """
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetMinSize([320, 150])
        self.SetWndIcon(None)
        self.SetCaption('AutoMoveBot Control')
        self.MakeUnResizeable()
        self.SetTopparentHeight(0)
        self.Begin()

    def Begin(self):
        """
        Main UI creation and layout.
        """
        autoMoveBotSvc = sm.GetService('automovebot')
        main = uiprimitives.Container(name='main', parent=self.sr.main, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.GenerateInputLine(main, 'channelInput', 'Channel name:', autoMoveBotSvc.CHANNEL_NAME).Disable()
        self.GenerateInputLine(main, 'phraseInput', 'Trigger-phrase:', autoMoveBotSvc.MOVE_PHRASE).Disable()
        self.GenerateInputLine(main, 'destInput', 'Destination ID:', autoMoveBotSvc.DESTINATION_ID).Disable()
        queueContainer = uiprimitives.Container(parent=main, align=uiconst.TOALL, height=16, top=const.defaultPadding)
        self.queueLabel = uicontrols.Label(text='Queue Size:', name='txtQueue', parent=queueContainer, align=uiconst.TOALL, height=12, top=10, left=25, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        buttons = [['Start',
          self.StartBot,
          None,
          81], ['Stop',
          self.StopBot,
          None,
          81], ['Close',
          self.Hide,
          None,
          81]]
        self.btns = uicontrols.ButtonGroup(btns=buttons, line=1, parent=main)
        self.SetRunning(False)

    @staticmethod
    def GenerateInputLine(parent, name, title, defaultValue):
        """
        Method wrapping toggether actions needed to create a Label-TextField combo.
        
        Params:
            parent -- The parent UI element.
            name -- Unique name of the UI element.
            title -- The title to be used in the label.
            defaultValue -- The default input value.
        """
        container = uiprimitives.Container(parent=parent, align=uiconst.TOTOP, height=16, top=const.defaultPadding)
        container.padLeft = 5
        container.padRight = 5
        label = uicontrols.Label(text=title, name='txt%s' % name, parent=container, align=uiconst.TOLEFT, height=12, top=5, left=8, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        label.rectTop = -2
        inputField = uicontrols.SinglelineEdit(name=name, parent=container, setvalue=str(defaultValue), left=5, width=200, height=20, align=uiconst.TORIGHT)
        return inputField

    def Hide(self, *args):
        """
        Hide the Automove-bot window.
        """
        self.Close()

    def StartBot(self, *args):
        """
        Event-handler for the Start button.
        Starts the bot and changes the button states.
        
        Params:
            *args -- Extra arguments from the UI.
        """
        autoMoveBotSvc = sm.GetService('automovebot')
        autoMoveBotSvc.StartBot()
        main = uiutil.GetChild(self.sr.main, 'main')
        autoMoveBotSvc.channelName = uiutil.GetChild(main, 'channelInput').GetValue()
        autoMoveBotSvc.movePhrase = uiutil.GetChild(main, 'phraseInput').GetValue()
        autoMoveBotSvc.destinationID = uiutil.GetChild(main, 'destInput').GetValue()
        self.SetRunning(True)

    def StopBot(self, *args):
        """
        Event-handler for the Stop button.
        Stops the bot and changes the button states.
        
        Params:
            *args -- Extra arguments from the UI.
        """
        sm.GetService('automovebot').StopBot()
        self.SetRunning(False)

    def SetRunning(self, state):
        """
        Set the state of the Start and Stop buttons of the Automovebot UI.
        
        Params:
            state -- The state (bool) to set the buttons to.
        """
        main = uiutil.GetChild(self.sr.main, 'main')
        channelInput = uiutil.GetChild(main, 'channelInput')
        phraseInput = uiutil.GetChild(main, 'phraseInput')
        destInput = uiutil.GetChild(main, 'destInput')
        startBtn = uiutil.GetChild(self.btns, 'Start_Btn')
        stopBtn = uiutil.GetChild(self.btns, 'Stop_Btn')
        if state is True:
            startBtn.Disable()
            stopBtn.Enable()
            channelInput.Disable()
            phraseInput.Disable()
            destInput.Disable()
        else:
            startBtn.Enable()
            stopBtn.Disable()
            channelInput.Enable()
            phraseInput.Enable()
            destInput.Enable()

    def OnAutoMoveBotQueueChange(self, size):
        """
        Event-handler for queue changes in the automovebot service.
        Updates the UI with the Queue size.
        
        Params:
            size -- The new size of the move-queue.
        """
        self.queueLabel.SetText('Queue Size: %s' % str(size))

    def OnAutoMoveBotStateChanged(self, state):
        """
        Event-handler for state changes of the automove-bot service.
        Updates the UI with the service state.
        
        Params:
            state -- The new state of the automovebot service.
        """
        if state == 'start':
            self.SetRunning(True)
        elif state == 'stop':
            self.SetRunning(False)
