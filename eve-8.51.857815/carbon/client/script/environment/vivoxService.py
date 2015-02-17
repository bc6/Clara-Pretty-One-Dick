#Embedded file name: carbon/client/script/environment\vivoxService.py
import uthread
import service
import hashlib
import blue
import types
import sys
import vivox
import vivoxConstants
import log
import os

class VivoxService(service.Service):
    """ The VivoxService handles all communication and event handling with the vivox voice server.
        
        Has been corified to a point where there should be any duplicates, that is overrides of 
        methods in child services that are clones of the one in this one. If you need to have different
        functionality the rules are like this.
            1. Create a function with the same name as the function to be changed with an App prepended
               Example: App specific run function would be called AppRun
            2. App specific parts of the function body should be moved to AppFuncName in child services
            3. Call AppFuncName in FuncName in this service.
        Also feel free to check the end of this file, there is a list of methods for application specific
        functionality that has to be implemented.
            
        So, what is app specific functionality? This is a good question which is not easy to answer,
        but a few good hints are:
         - it is required for a very game specific feature (f.e. eve's fleet/gang channels)
         - it involves user interaction (f.e. showing a message on the screen, setting channel icons)
         
        And what should not be app specific functionality? Again, we can only provide some hints:
         - if it is about channel management it is most likely supposed to be in here
         - if it is about connection handling, it is also most likely supposed to be in here
    """
    __guid__ = 'svc.vivox'
    __servicename__ = 'vivox'
    __exportedcalls__ = {}
    __notifyevents__ = ['OnVoiceChannelURI']
    __startupdependencies__ = ['settings']

    def Run(self, ms):
        self.LogInfo('vivox service starting')
        self.vivoxServer = ''
        self.vivoxStatus = vivoxConstants.VIVOX_NONE
        self.vivoxLoginState = vivoxConstants.VXCLOGINSTATE_LOGGEDOUT
        self.subscriber = None
        self.intensityCallback = None
        self.echo = False
        self.gagged = 0
        self.members = {}
        self.gaggedAt = {}
        self.speakingChannel = None
        self.pushToTalkEnabled = True
        self.logLevel = vivoxConstants.VXLOGLEVEL_NONE
        args = blue.pyos.GetArg()
        for arg in args:
            if arg.startswith('/vivoxlog'):
                try:
                    params = arg.split('=')
                    logLevel = range(vivoxConstants.VXLOGLEVEL_NONE, 1 + vivoxConstants.VXLOGLEVEL_DEBUG)[params[1]]
                except:
                    logLevel = vivoxConstants.VXLOGLEVEL_DEBUG

                self.LogInfo('Enabling vivox logging with log level ', logLevel)
                self.logLevel = logLevel
                break

        self.voiceFontList = None
        self.speakingChannel = None
        self.accountCreationAttempts = 0
        self.defaultMicrophoneVolume = 0.5
        self.secureLogging = 1
        self.autoJoinQueue = []
        self.addToAclQueue = []
        self.audioTestRunning = False
        self.previousSpeakingChannel = None
        self.voiceMgr = sm.RemoteSvc('voiceMgr')
        self.AppRun(ms)
        self.LogInfo('vivox service started')

    def Enabled(self):
        if hasattr(settings.user, 'audio'):
            return settings.user.audio.Get('voiceenabled', 1) == 1
        else:
            return True

    def LoggedIn(self):
        return self.vivoxLoginState == vivoxConstants.VXCLOGINSTATE_LOGGEDIN

    def Subscriber(self):
        if not session.charid:
            return
        if boot.region == 'optic':
            return
        if self.subscriber is None:
            self.subscriber = sm.RemoteSvc('voiceMgr').VoiceEnabled()
        return self.subscriber

    def Init(self):
        if getattr(self, 'vivoxStatus', vivoxConstants.VIVOX_NONE) != vivoxConstants.VIVOX_NONE:
            self.LogInfo('Init vivoxStatus was: ', self.vivoxStatus)
            return
        if boot.region == 'optic':
            self.LogInfo('Vivox is not supported in optic')
            self.vivoxStatus = vivoxConstants.VIVOX_OPTIC
            return
        if not self.Enabled():
            self.LogInfo('Vivox has been disabled in settings')
            return
        if not self.subscriber:
            self.LogWarn('This character is not voice enabled on the server, this might be related to a server-side error.')
            return
        userid = session.userid
        self.charid = session.charid
        self.vivoxStatus = vivoxConstants.VIVOX_INITIALIZING
        self.password = self.voiceMgr.GetPassword()
        self.vivoxServer = self.voiceMgr.GetServer()
        self.LogNotice('Using VivoxServer', self.vivoxServer)
        hashValue = hashlib.md5(str(userid) + str(self.charid))
        self.vivoxUserName = str(self.charid) + 'U' + hashValue.hexdigest()
        self.LogInfo('Init vivoxStatus was: ', self.vivoxStatus)
        self.connector = vivox.Connector()
        self.connector.callback = self
        self.LogInfo('vivoxService: Initializing application specific settings')
        uthread.pool('vivox::Init', self._Init)

    def _Init(self):
        self.echoChannelURI = 'sip:confctl-2@' + self.vivoxServer + '.vivox.com'
        certPath = os.path.normpath(os.path.join(blue.paths.ResolvePath(u'app:/')))
        cachePath = os.path.normpath(os.path.join(blue.paths.ResolvePathForWriting(u'cache:/vivox/')))
        self.LogInfo('Vivox cache path:', cachePath)
        self.LogInfo('Vivox certificate path:', certPath)
        self.connector.InitializeEx(self.vivoxServer, self.secureLogging, cachePath, 'vivoxlog', '.txt', self.logLevel, certPath)
        self.LogInfo('Vivox intializing (', self.vivoxServer, self.logLevel, ')')

    def GetCharIdFromUri(self, vivoxName):
        charid = vivoxName.split('U')
        if charid[0].find(':') > -1:
            charid = charid[0].split(':')
            charid = int(charid[1])
        else:
            self.LogError('VivoxSvc: Possible malformed vivoxName detected. vivoxName is', vivoxName)
        return charid

    def GetAvailableVoiceFonts(self):
        if self.LoggedIn():
            if self.voiceFontList is None:
                self.LogInfo('Requesting Voice Fonts from server')
                uthread.pool('vivox::GetAvailableVoiceFontseve', self._GetAvailableVoiceFonts)
            else:
                sm.ScatterEvent('OnVoiceFontsReceived', self.voiceFontList)

    def _GetAvailableVoiceFonts(self):
        self.connector.GetAvailableVoiceFonts()

    def GetVivoxChannelName(self, channelID):
        """ Returns the channel name as str.  If the channel name is a tuple then it return tuple pair appended as string"""
        if channelID == 'Echo':
            return channelID
        if type(channelID) == types.IntType:
            return str(channelID)
        if type(channelID) == types.TupleType:
            if type(channelID[0]) == types.TupleType:
                return str(channelID[0][0]) + str(channelID[0][1])
            else:
                return str(channelID[0]) + str(channelID[1])
        else:
            return str(channelID)

    def GetCcpChannelName(self, vivoxChannelID):
        """ Return int if vivox channel name is only int and created compatible tuple if it contians letters in the channel name"""
        if vivoxChannelID == 'Echo':
            return 'Echo'
        elif vivoxChannelID:
            if vivoxChannelID.isdigit() or vivoxChannelID[0] == '-' and vivoxChannelID[1:].isdigit():
                channelID = int(vivoxChannelID)
            else:
                identityName = ''
                for i in vivoxChannelID:
                    if not i.isdigit():
                        identityName += i

                try:
                    channelNum = int(vivoxChannelID.replace(identityName, ''))
                except ValueError:
                    channelNum = 0

                channelID = (identityName, channelNum)
            return channelID
        else:
            return 0

    def GetJoinedChannels(self):
        channels = []
        for each in self.members.keys():
            channels.append(self.GetCcpChannelName(each))

        return channels

    def GetJoinedChannelsByType(self, typeName):
        channels = []
        for each in self.members.iterkeys():
            channelName = self.GetCcpChannelName(each)
            if type(channelName) is types.TupleType:
                if channelName[0] == typeName:
                    channels.append(channelName)

        return channels

    def IsVoiceChannel(self, channelID, vivoxNamed = 0):
        """ returns true if the channel being checked is the current vivox channel"""
        if not vivoxNamed:
            vivoxChannelID = self.GetVivoxChannelName(channelID)
        else:
            vivoxChannelID = channelID
        if vivoxChannelID in self.members:
            return True
        else:
            return False

    def GetMemberVoiceStatus(self, channelID):
        ret = {}
        if self.LoggedIn():
            vivoxChannelName = self.GetVivoxChannelName(channelID)
            status = self.members.get(vivoxChannelName, None)
            if status:
                for charID, voiceStatus, sip in status:
                    if type(charID) in (types.IntType, types.StringType):
                        ret[int(charID)] = voiceStatus

        return ret

    def Login(self):
        """ Try to log in to the voice chat service.
        
        This will initialize the connector if that had not happened yet.
        Additionally this will fail if we are already logging in.
        """
        self.LogInfo('vivox Login')
        if self.vivoxStatus == vivoxConstants.VIVOX_NONE:
            self.LogWarn('vivox was not initialized, initializing')
            self.Init()
            return
        initialized = self.vivoxStatus == vivoxConstants.VXCCONNECTORSTATE_INITIALIZED
        loggingIn = self.vivoxLoginState == vivoxConstants.VXCLOGINSTATE_LOGGINGIN
        if initialized and not loggingIn and not self.LoggedIn():
            self.vivoxLoginState = vivoxConstants.VXCLOGINSTATE_LOGGINGIN
            uthread.pool('vivox::Login', self._Login)

    def _Login(self):
        self.SetMicrophoneVolume(self.GetMicrophoneVolume())
        self.connector.Login(self.vivoxUserName, self.password)

    def LogOut(self):
        """ Log out from the voice chat service.
        
            This does exactly what it says on the tin.
        """
        if self.LoggedIn():
            self.LogInfo('Vivox is currently logged in, logging out...')
            joinedChannels = list(self.members)
            for each in joinedChannels:
                self._OnLeftChannel(each)

            self.connector.Logout()

    def JoinChannel(self, channelID, suppress = False, persist = True):
        """
            Joins a voice chat channel channel after requesting its URI from 
            the server.
        
            If the channel does not exist yet, the server will create it.
            By default the created channel will be persistant, which may
            not be desired in all cases - for example when creating a private
            chat conversation between two players. In that case we have to
            explicitely set the persist parameter to false.
        """
        if not self.Enabled():
            if suppress:
                return
            if not self.Enabled():
                raise UserError('VoiceNotEnabledInSettings')
            else:
                raise UserError('VoiceNotEnabled')
        self.LogInfo('JoinChannel', channelID)
        if not self.LoggedIn():
            if self.vivoxLoginState != vivoxConstants.VXCLOGINSTATE_LOGGINGIN:
                if channelID not in self.autoJoinQueue:
                    self.autoJoinQueue.append(channelID)
                self.LogInfo('Not logged in calling login')
                self.Login()
            return
        if self.members.has_key('Echo') and channelID != 'Echo':
            self.LeaveEchoChannel()
        if self.AppCanJoinChannel(channelID, suppress):
            uthread.pool('vivox::JoinChannel', self._JoinChannel, self.GetVivoxChannelName(channelID))

    def _JoinChannel(self, vivoxChannelName):
        self.connector.JoinChannelEx(vivoxChannelName)

    def LeaveChannel(self, channelID):
        if self.members:
            self.LogInfo('Leaving Channel', channelID)
            uthread.pool('vivox::LeaveChannel', self._LeaveChannel, self.GetVivoxChannelName(channelID))

    def _LeaveChannel(self, vivoxChannelName):
        self.LogInfo('_LeaveChannel(', vivoxChannelName, ')')
        self.connector.LeaveChannel(vivoxChannelName)

    def CreateChannel(self, vivoxChannelName):
        uthread.pool('vivox::CreateChannel', self._CreateChannel, vivoxChannelName)

    def _CreateChannel(self, vivoxChannelName):
        self.LogInfo('Requesting Creation of channel with name', vivoxChannelName)
        try:
            isPersistent = self.IsChannelPersistent(vivoxChannelName)
            isProtected = self.IsChannelProtected(vivoxChannelName)
            uri = self.voiceMgr.CreateChannel(vivoxChannelName, isPersistent, isProtected)
        except:
            log.LogException()
            sys.exc_clear()
        finally:
            if len(uri) > 0:
                uthread.pool('vivox::JoinChannel', self._JoinChannel, vivoxChannelName)
            else:
                raise UserError('VivoxError42')

    def IsChannelPersistent(self, vivoxChannelName):
        """
            Overwrite this method in your subclass in order to determine whether a channel
            is supposed to be persistent or not. Normally you do not want them to be it
            persistent. Exceptions are EVE specific at the moment (Corporation and Alliance)
        """
        return False

    def IsChannelProtected(self, vivoxChannelName):
        """
            Overwrite this method in your subclass in order to determine whether a channel
            is supposed to be protected or not. Protected channels will be handled by an
            ACL.
        """
        return False

    def LeaveInstantChannel(self):
        self.LogInfo('LeaveInstantChannel')
        self.LeaveChannelByType('inst')

    def LeaveChannelByType(self, typeName):
        self.LogInfo('Leaving all channels of type:', typeName)
        for each in self.members.keys():
            channelName = self.GetCcpChannelName(each)
            if type(channelName) is types.TupleType:
                if channelName[0] == typeName:
                    self.LeaveChannel(channelName)

    def SetSpeakingChannel(self, channelID):
        """ Implemented in derived classes."""
        self.AppSetSpeakingChannel(channelID)

    def GetSpeakingChannel(self):
        return self.GetCcpChannelName(self.speakingChannel)

    def Gag(self, charID, channelID, time):
        """ Client gags himslelf untill notified that he should ungang """
        self.AppGag(charID, channelID, time)

    def UnGag(self, charID, channelID):
        self.AppUnGag(charID, channelID)

    def GetParticipants(self, vivoxChannelName):
        """
        GetParticipants gets the list of participants in the current session.
        It uses the passed in channelName as a key in the member dict and stores the participants as list under that key if it already exists in the dict.
        GetParticipant also makes the call to LSC to update the UI
        """
        self.LogInfo('GetParticipants channel:', vivoxChannelName)
        blue.pyos.synchro.SleepWallclock(5000)
        p = self.connector.GetParticipants(vivoxChannelName)
        participants = []
        for each in p:
            charid = self.GetCharIdFromUri(each[0])
            participants.append([charid, 0, each[0]])
            if charid in self.mutedParticipants:
                self.MuteParticipantForMe(charid, 1, vivoxChannelName)

        if vivoxChannelName in self.members:
            self.members[vivoxChannelName] = participants

    def CreateAccount(self):
        """ Creates vivox account using information received from the server"""
        self.AppCreateAccountSendNotifyMessage()
        if self.voiceMgr == None:
            self.LogInfo('CreateAccount failed voiceMgr is None')
            self.voiceMgr = sm.RemoteSvc('voiceMgr')
        else:
            self.LogInfo('CreateAccount voiceMgr is ready')
        if self.voiceMgr.CreateAccount():
            self.AppAccountCreated()
            uthread.pool('vivox::Login', self._Login)
        else:
            self.AppCreateAccountFailed()

    def SetVoiceFont(self, voiceFontID):
        """ Sets the voice font for this user """
        self.connector.SetVoiceFont(voiceFontID)
        try:
            settings.char.ui.Set('voiceFontID', voiceFontID)
        except:
            self.LogError('Could not set voiceFontID')
            sys.exc_clear()

    def GetVoiceFont(self):
        try:
            return settings.char.ui.Get('voiceFontID', 0)
        except:
            self.LogError('Could not retrieve voiceFontID')
            sys.exc_clear()
            return 0

    def GetAudioInputDevices(self):
        audioDevices = self.connector.GetAudioInputDevices()
        return audioDevices

    def GetPreferredAudioInputDevice(self):
        preferedInputDevice = self.connector.GetPreferredAudioInputDevice()
        return preferedInputDevice

    def SetPreferredAudioInputDevice(self, device, restartAudioTest = 0):
        """Takes int as input """
        self.connector.SetPreferredAudioInputDevice(device)
        if restartAudioTest:
            self.RestartAudioTest()

    def GetPreferredAudioInputDeviceLineNumber(self):
        preferedInputDeviceLineNumber = self.connector.GetPreferredAudioInputDeviceLineNumber()
        return preferedInputDeviceLineNumber

    def GetAudioOutputDevices(self):
        audioDevices = self.connector.GetAudioOutputDevices()
        return audioDevices

    def GetPreferredAudioOutputDevice(self):
        preferredOutputDevice = self.connector.GetPreferredAudioOutputDevice()
        return preferredOutputDevice

    def SetPreferredAudioOutputDevice(self, device, restartAudioTest = 0):
        """ Takes int as input"""
        self.connector.SetPreferredAudioOutputDevice(device)
        if restartAudioTest:
            self.RestartAudioTest()

    def SetMicrophoneVolume(self, volume, restartAudioTest = 0):
        volume = vivoxConstants.VXVOLUME_MIN + int(volume * (vivoxConstants.VXVOLUME_MAX - vivoxConstants.VXVOLUME_MIN))
        self.connector.SetMicrophoneVolume(volume)
        if restartAudioTest:
            self.RestartAudioTest()

    def GetMicrophoneVolume(self):
        if hasattr(settings.user, 'audio'):
            return settings.user.audio.Get('TalkMicrophoneVolume', self.defaultMicrophoneVolume)
        else:
            return 0

    def EnableGlobalPushToTalkMode(self, binding, key = None):
        self.AppEnableGlobalPushToTalkMode(binding, key)

    def DisableGlobalPushToTalkMode(self):
        self.AppDisableGlobalPushToTalkMode()

    def GetAvailableKeyBindings(self):
        return self.AppGetAvailableKeyBindings()

    def StartAudioTest(self):
        if self.LoggedIn() and not self.audioTestRunning and self.members == {} and self.connector.ChannelJoinInProgressCount() == 0:
            self.connector.StartAudioTest()
            self.audioTestRunning = True

    def StopAudioTest(self):
        if self.audioTestRunning:
            self.connector.StopAudioTest()
            self.audioTestRunning = False

    def RestartAudioTest(self):
        self.connector.StopAudioTest()
        uthread.pool('vivox::RestartAudioTest', self.DelayedStartAudioTest)

    def DelayedStartAudioTest(self):
        blue.pyos.synchro.SleepWallclock(1000)
        if len(self.members) == 0:
            self.connector.StartAudioTest()

    def JoinEchoChannel(self):
        self.LogInfo('JoinEchoChannel')
        if self.LoggedIn():
            if len(self.members.keys()) == 0:
                if self.connector.ChannelJoinInProgressCount() == 0 and self.echo == False:
                    self.echo = True
                    uthread.pool('vivox::JoinChannel', self._JoinEchoChannel)
                    return
        elif self.vivoxLoginState != vivoxConstants.VXCLOGINSTATE_LOGGINGIN:
            self.autoJoinQueue = ['Echo']
            self.LogInfo('Not logged in calling login')
            self.Login()
            return
        if 'Echo' in self.members:
            self.LeaveEchoChannel()
            return
        if self.AppCanJoinEchoChannel():
            for channel in self.members.keys():
                self._LeaveChannel(channel)

            if 'Echo' not in self.autoJoinQueue:
                self.autoJoinQueue = ['Echo']
            else:
                self.LogError('Wait a second, I already have the echo channel in my autoJoinQueue!')
        else:
            sm.ScatterEvent('OnEchoChannel', False)

    def _JoinEchoChannel(self):
        self.StopAudioTest()
        self.connector.JoinChannelEx('Echo')

    def LeaveEchoChannel(self):
        if self.members.has_key('Echo'):
            self.LogInfo('LeaveEchoChannel')
            self._LeaveChannel('Echo')

    def MuteParticipantForMe(self, charID, mute, vivoxChannelName = None):
        channels = self.members
        if vivoxChannelName is not None:
            if type(vivoxChannelName) in (types.TupleType, types.ListType):
                channels = vivoxChannelName
            else:
                channels = [vivoxChannelName]
        for channel in channels:
            for participant in self.members[channel]:
                if charID == participant[0]:
                    self.LogInfo('Setting mute status for participant', participant[2], 'to', mute, 'in channel', channel)
                    self.connector.MuteParticipantForMe(channel, participant[2], mute)

        if mute:
            self.mutedParticipants[charID] = charID
        elif self.mutedParticipants.has_key(charID):
            self.mutedParticipants.pop(charID)

    def GetMutedParticipants(self):
        return self.mutedParticipants

    def SetChannelOutputVolume(self, channelID, volume):
        self.connector.SetChannelOutputVolume(channelID, volume)

    def ModeratorMuteAll(self, channelID, mute):
        self.connector.ModeratorMuteAll(self.GetVivoxChannelName(channelID), mute)

    def ModeratorMute(self, channelID, charID, mute):
        self.connector.ModeratorMute(self.GetVivoxChannelName(channelID), charID, mute)

    def OnConnectorEvent(self, eventType, statusCode, state):
        for k, v in globals().items():
            if k.startswith('VXCEVENT_') and v == eventType:
                self.LogWarn('Unhandled connector event of type', k, 'with statuscode', statusCode, 'and status string', state)

    def RegisterIntensityCallback(self, object):
        self.intensityCallback = object

    def UnregisterIntensityCallback(self):
        self.intensityCallback = None

    def OnInitialized(self, statusCode):
        if statusCode != 0:
            self.LogError('OnIntialized, failed', statusCode)
        else:
            self.LogInfo('OnIntialized, done initalizing, logging in')
            self.vivoxStatus = vivoxConstants.VXCCONNECTORSTATE_INITIALIZED
            self.OnKeyEvent('talk', 0)
            self.Login()

    def FailedJoinChannel(self, errorCode, errorMessage, channelName):
        if errorCode in (vivoxConstants.VX_NOTONACL, vivoxConstants.VX_ACCESSDENIED, vivoxConstants.VX_NOTFOUND):
            if channelName not in self.addToAclQueue:
                self.addToAclQueue.append(channelName)
                uthread.pool('Vivox::FailedJoinChannel', self.AppAddToACL, channelName)
                return
        if channelName in self.autoJoinQueue:
            self.autoJoinQueue.remove(channelName)
        self.LogInfo('Failed to join channel ', channelName, errorMessage, errorCode, self.autoJoinQueue)

    def FailedChannelCreate(self, errorCode, uri):
        self.LogInfo('Failed to create channel ', uri, errorCode)

    def AppAccountCreated(self):
        """ Implemented in derived classes."""
        pass

    def AppCreateAccountFailed(self):
        """ Implemented in derived classes. """
        pass

    def OnShutDown(self):
        self.LogInfo('Connector is shutting down')

    def FailedOnLogin(self, statusCode, statusText):
        self.LogInfo('FailedOnLogin ', statusCode, statusText)

    def OnAccountNotFound(self):
        self.LogInfo('OnAccountNotFound')
        if self.accountCreationAttempts < vivoxConstants.VXACCOUNT_MAXCREATIONATTEMPTS:
            self.accountCreationAttempts = self.accountCreationAttempts + 1
            uthread.pool('vivox::OnAccountNotFound', self.CreateAccount)

    def OnLoggedIn(self, state):
        self.vivoxLoginState = state
        if self.LoggedIn():
            self.GetAvailableVoiceFonts()
            self.LogInfo('OnLoggedIn.LOGGEDIN')
            sm.ScatterEvent('OnVoiceChatLoggedIn')
            self.AppOnLoggedIn()
            for each in self.autoJoinQueue:
                if each == 'Echo':
                    uthread.pool('vivox::JoinChannel', self.JoinEchoChannel)
                else:
                    uthread.pool('vivox::JoinChannel', self.JoinChannel, each)

            self.autoJoinQueue = []
        elif state == vivoxConstants.VXCLOGINSTATE_LOGGEDOUT:
            self.LogInfo('OnLoggedIn.LOGGEDOUT')
            sm.ScatterEvent('OnVoiceChatLoggedOut')
            self.AppOnLoggedOut()
        elif state == vivoxConstants.VXCLOGINSTATE_LOGGINGIN:
            self.LogInfo('OnLoggedIn.LOGGINGIN')
        elif state == vivoxConstants.VXCLOGINSTATE_LOGGINGOUT:
            self.LogInfo('OnLoggedIn.LOGGINGOUT')
        else:
            self.LogInfo('OnLoggedIn.UNKNOWN')

    def OnVoiceChannelURI(self, channelName, channelURI):
        self.LogInfo('URI for channel', channelName, 'is', channelURI)
        self.connector.JoinChannelEx(channelName, str(channelURI))

    def OnJoinedChannel(self, channelName):
        if channelName in self.addToAclQueue:
            self.addToAclQueue.remove(channelName)
        uthread.pool('vivox::OnJoinedChannel', self._OnJoinedChannel, channelName)

    def OnLeftChannel(self, channelName):
        self.LogInfo('OnLeftChannel')
        uthread.pool('vivox::OnLeftChannel', self._OnLeftChannel, channelName)

    def OnVoiceFontsReceived(self, voiceFontList):
        self.SetVoiceFont(self.GetVoiceFont())
        self.voiceFontList = voiceFontList
        sm.ScatterEvent('OnVoiceFontsReceived', voiceFontList)

    def OnParticipantJoined(self, uri, channelName):
        self.LogInfo('OnParticipantJoined', uri, channelName)
        charid = self.GetCharIdFromUri(uri)
        if channelName != 'Echo' and self.members.has_key(channelName):
            participants = self.members[channelName]
            if participants.count([charid, 0]) == 0 and participants.count([charid, 1]) == 0 and participants.count([charid, 2]) == 0:
                if len(uri) == 0:
                    self.LogError('Participant with charid', charid, 'was returned from OnParticipantJoined with empty uri. Not adding to participant list.')
                elif type(charid) not in (types.IntType, types.StringType):
                    self.LogError('Malformed charid for uri', uri)
                else:
                    participants.append([charid, 0, uri])
                    self.members[channelName] = participants
        else:
            self.LogInfo('OnParticipantJoined missing channel name', channelName)
        if 'inst' in channelName:
            p = self.connector.GetParticipants(channelName)
            if len(p) == 2:
                if self.speakingChannel is not None:
                    self.previousSpeakingChannel = self.GetCcpChannelName(self.speakingChannel)
                else:
                    self.previousSpeakingChannel = None
                self.SetSpeakingChannel(self.GetCcpChannelName(channelName))
                self.LogInfo('Instant Channel Ready')
                sm.ScatterEvent('OnInstantVoiceChannelReady')
        if charid in self.mutedParticipants:
            self.MuteParticipantForMe(charid, 1, channelName)
        self.AppOnParticipantJoined(charid, channelName)

    def OnParticipantLeft(self, uri, channelName):
        """ Implemented in derived classes."""
        charid = self.GetCharIdFromUri(uri)
        self.LogInfo('OnParticipantLeft', channelName, charid)
        if channelName in self.members and charid != self.charid:
            self.LogInfo('OnParticipantLeft channelName is in self.members')
            participants = self.members[channelName]
            index = None
            for each in participants:
                if charid == each[0]:
                    participants.remove(each)
                    break

        self.AppOnParticipantLeft(uri, channelName)

    def OnParticipantStateChanged(self, uri, channelName, isSpeaking, isLocallyMuted, energy):
        """ Implemented in derived classes."""
        pass

    def OnKeyEvent(self, name, pressed):
        """ This is a callback triggered from the connector.
        
        """
        if name == 'talk' and self.pushToTalkEnabled:
            muted = 0
            if pressed == 0:
                muted = 1
            self.connector.Talk(muted)
        self.AppOnKeyEvent(name, pressed)

    def AppRun(self):
        r""" This is called when the service is being started up.
        
            \sa Service documentation on trac
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppOnLoggedIn(self):
        """ Interface for providing application specific event handling
        
            This allows the application to provide specific functionality when a player has logged in to the voice chat.
            For example here we can apply the user settings, or display a message that the user logged in to voice chat.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppOnKeyEvent(self, name, pressed):
        """ Interface to allow an application to perform additional key handling.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def _OnJoinedChannel(self, channelName = 0):
        """ Implemented in derived classes."""
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def _OnLeftChannel(self, channelName):
        """Implemented in derived classes."""
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppOnParticipantLeft(self, uri, channelName):
        """ Tells the application that uri has left channelName
        
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppOnParticipantJoined(self, uri, channelName):
        """ Tells the application that uri has joined channelName
        
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppCanJoinChannel(self, channelID, suppress = False):
        """ Allows application specific decisions.
        
            Must return True if the vivox service is actually allowed to perform
            joining a channel. Return False if the channel should not be joined.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppCanJoinEchoChannel(self, suppress = False):
        """ Allows application specific decisions regarding joining the echo channel.
        
            Must return True if the vivox service is actually allowed to perform
            joining a channel. Return False if the channel should not be joined.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppGetAvailableKeyBindings(self):
        """ Returns the available Keybindings offered by the application.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppOnAccountNotFound(self):
        """ Informs the application that a voice chat account was not found.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppGag(self, charID, eveChannelID, time):
        """ Client gags himslelf untill notified that he should ungang """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppUnGag(self, charID, eveChannelID):
        """ Client ungangs himself
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppCreateAccountSendNotifyMessage(self):
        """ Notification that account for voice chat is created.
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppSetSpeakingChannel(self, eveChannelID):
        """ Set the currently active speaking channel
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppEnableGlobalPushToTalkMode(self, binding, key):
        """ Enable global push to talk mode
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppDisableGlobalPushToTalkMode(self):
        """ Disable global push to talk mode
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")

    def AppAddToACL(self, vivoxChannelName):
        """ Add someone to a channel Access Control List
        """
        raise NotImplementedError("This is application specific functionality and must be implemented in your application's voice chat service.")
