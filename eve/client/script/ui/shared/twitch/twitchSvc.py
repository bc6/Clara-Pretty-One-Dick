#Embedded file name: eve/client/script/ui/shared/twitch\twitchSvc.py
import service
import twitch
from localization import GetByLabel
import yaml
import uthread
import blue
FRAMERATE_OPTIONS = (10, 15, 20, 25, 30, 40, 50, 60)
FRAMERATE_DEFAULT = 30

class Twitch(service.Service):
    __update_on_reload__ = 1
    __guid__ = 'svc.twitch'
    __notifyevents__ = ('OnEndChangeDevice',)
    __dependencies__ = {'characterSettings'}

    def Run(self, *args):
        self.streamStartTime = None
        twitch.set_state_change_callback(self.OnTwitchStateChanged)

    def OnTwitchStateChanged(self, state):
        sm.ScatterEvent('OnTwitchStreamingStateChange', state)

    def GetResolutionOptions(self):

        def IsValidResolution(option):
            _, resolution = option
            return twitch.is_valid_windowsize(resolution)

        deviceSvc = sm.GetService('device')
        options, _ = deviceSvc.GetAdapterResolutionsAndRefreshRates(deviceSvc.GetSettings())
        options = filter(IsValidResolution, options)
        if (u'1024x768', (1024, 768)) not in options:
            options.append((u'1024x768', (1024, 768)))
        return options

    def GetFramerateOptions(self):
        return tuple(((str(fps), fps) for fps in FRAMERATE_OPTIONS))

    def GetSettings(self):
        setting = self.characterSettings.Get('twitch')
        if setting is None or isinstance(setting, dict):
            return setting
        return yaml.load(setting, Loader=yaml.CLoader)

    def GetSetting(self, settingName, default = None):
        twitchSettings = self.GetSettings()
        if twitchSettings is not None:
            return twitchSettings.get(settingName, default)

    def GetUsername(self):
        return self.GetSetting('username')

    def GetTitle(self):
        return self.GetSetting('title')

    def GetFPS(self):
        return self.GetSetting('fps', FRAMERATE_DEFAULT)

    def HasToken(self):
        return self.GetSetting('token') is not None

    def StartStream(self, username, password, title, fps):
        twitchInfo = sm.RemoteSvc('charMgr').GetTwitchInfo()
        clientID = twitchInfo['clientID']
        try:
            twitchSettings = self.GetSettings()
            if password is None and twitchSettings is not None and 'token' in twitchSettings:
                self.LogInfo('I have Twitch token, trying to login using the token for', username)
                token = twitchSettings['token']
                twitch.login_with_token(clientID, token)
            else:
                self.LogInfo('Login to Twitch with user/pass for', username)
                twitch.login(username, password, clientID, twitchInfo['clientSecret'])
                token = twitch.get_login_token()
        except Exception as e:
            if str(e) == 'TTV_EC_API_REQUEST_FAILED':
                sm.GetService('gameui').Say(GetByLabel('UI/Twitch/LoginFailed'))
            elif str(e) == 'TTV_EC_HTTPREQUEST_ERROR':
                sm.GetService('gameui').Say(GetByLabel('UI/Twitch/LoginFailedConnection'))
            else:
                sm.GetService('gameui').Say(GetByLabel('UI/Twitch/LoginFailedUnknown'))
            self.LogWarn('Error login into twitch', username)
            password = None
            raise

        try:
            twitch.start_stream(unicode(title), str(twitchInfo['gameName']), fps)
        except Exception as e:
            if e.message == 'TTV_EC_UNKNOWN_ERROR':
                sm.GetService('gameui').Say(GetByLabel('UI/Twitch/StoppedResolutionChange'))
            else:
                raise

        self._SaveSettings(username, token, title, fps)
        self.streamStartTime = blue.os.GetWallclockTime()
        self.LogTwitchEvent(['twitchUsername', 'title'], 'StreamStarted', username, title)

    def _SaveSettings(self, username, token, title, fps):
        twitchSettings = {'username': username,
         'title': title,
         'fps': fps}
        if token is not None:
            twitchSettings['token'] = token
        twitchSettings = yaml.safe_dump(twitchSettings)
        self.characterSettings.Save('twitch', twitchSettings)

    def StopStream(self):
        twitch.stop_stream()
        if self.streamStartTime is not None:
            streamTime = (blue.os.GetWallclockTime() - self.streamStartTime) / const.SEC
            self.LogTwitchEvent(['duration'], 'StreamStopped', streamTime)

    def OnEndChangeDevice(self, *args):
        if twitch.is_streaming():
            sm.GetService('gameui').Say(GetByLabel('UI/Twitch/StoppedResolutionChange'))
            self.StopStream()

    def LogTwitchEvent(self, columnNames, *args):
        uthread.new(self.DoLogTwitchEvent, columnNames, *args)

    def DoLogTwitchEvent(self, columnNames, *args):
        sm.ProxySvc('eventLog').LogClientEvent('twitch', columnNames, *args)
