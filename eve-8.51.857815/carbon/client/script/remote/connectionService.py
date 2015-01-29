#Embedded file name: carbon/client/script/remote\connectionService.py
"""
Handles connection to the server and login along synchronizing the clock.

Also does application specific stuff related to the connection process. 
The logic of some of these is debatable though :|
"""
from service import Service
import blue
import telemetry
import uthread
import localization
import log
import const
import service
import sys
import base
from eve.common.script.util.utillib_bootstrap import GetServerName, GetServerPort, GetLoginCredentials
from carbon.common.script.util.exceptionEater import ExceptionEater
from carbon.common.script.util.format import FmtTime
import carbonui.const as uiconst
import serverInfo
DEFAULTLONGWAITWARNINGSECS = 300
LONGWAITWARNINGMETHODS = ['MachoBindObject', 'SelectCharacterID']
LoginProgressLabels = {'loginprogress::authenticating': '/Carbon/UI/Login/Progress/Authenticating',
 'loginprogress::connecting': '/Carbon/UI/Login/Progress/Connecting',
 'loginprogress::done': '/Carbon/UI/Login/Progress/Done',
 'loginprogress::gettingbulkdata': '/Carbon/UI/Login/Progress/GettingBulkData',
 'loginprogress::lowlevelversioncheck': '/Carbon/UI/Login/Progress/LowLevelVersionCheck',
 'loginprogress::miscinitdata': '/Carbon/UI/Login/Progress/MiscInitData',
 'loginprogress::processingInitialDataDone': '/Carbon/UI/Login/Progress/ProcessingInitialDataDone'}

class ConnectionService(Service):
    __guid__ = 'svc.connection'
    __servicename__ = 'connection'
    __displayname__ = 'Network Connection Service'
    __exportedcalls__ = {'Connect': [],
     'Disconnect': [],
     'IsConnected': [],
     'ConnectToService': [],
     'Login': []}
    __dependencies__ = ['machoNet']
    __notifyevents__ = ['OnProcessLoginProgress', 'OnClientStageChanged']

    def __init__(self):
        Service.__init__(self)
        self.shell = None
        self.reentrancyGaurd = 0
        self.processingBulkData = False
        self.clocksynchronizing = 0
        self.clocklastsynchronized = None
        self.lastLongCallTimestamp = 0
        blue.pyos.synchro.timesyncs.append(self.OnTimerResync)

    def Run(self, *args):
        Service.Run(self, *args)
        uthread.worker('ConnectionService::LongCallTimer', self.__LongCallTimer)

    def OnTimerResync(self, old, new):
        if session and session.nextSessionChange:
            diff = new - old
            log.general.Log('Readjusting next session change by %.3f seconds' % (diff / float(const.SEC)), log.LGINFO)
            session.nextSessionChange += diff

    @telemetry.ZONE_METHOD
    def Connect(self, host, port, userid, password, ct):
        try:
            self.LogInfo('calling connect')
            address = '%s:%d' % (str(host), port)
            response = self.machoNet.ConnectToServer(address, userid, password, ct)
            self.LogInfo('connect completed...')
        except GPSException as what:
            self.LogError('connect failed %s' % what)
            raise UserError('LoginConnectFailed', {'what': what})

        self.SynchronizeClock()
        uthread.new(self.ClockSyncDaemon)
        return response

    def ConnectSso(self, host, port, token, ct):
        try:
            self.LogInfo('calling connect')
            address = '%s:%d' % (str(host), port)
            response = self.machoNet.ConnectToServer(address, 'EVE-SSO-CONNECTION', 'fakePW', ct, token)
            self.LogInfo('connect completed...')
        except GPSException as what:
            self.LogError('connect failed %s' % what)
            raise UserError('LoginConnectFailed', {'what': what})

        self.SynchronizeClock()
        uthread.new(self.ClockSyncDaemon)
        return response

    @telemetry.ZONE_METHOD
    def OnProcessLoginProgress(self, what, prefix = None, current = 1, total = 1, response = None):
        if what not in LoginProgressLabels.keys():
            text = "Unexpected step in OnProcessLoginProgress, '%s'" % what
            log.LogTraceback(extraText=text, severity=log.LGERR)
            return
        self.processingBulkData = 0
        useMorph = 1
        args = {}
        if what == 'loginprogress::gettingbulkdata':
            self.processingBulkData = total
            args['current'] = current
            args['total'] = total
            useMorph = 0
        msg = localization.GetByLabel(LoginProgressLabels[what], **args)
        uthread.new(sm.GetService('loading').ProgressWnd, localization.GetByLabel('/Carbon/UI/Login/LoggingIn'), msg, current, total, useMorph=useMorph, autoTick=useMorph)
        blue.pyos.synchro.Yield()

    @telemetry.ZONE_METHOD
    def Login(self, loginparam, selchar = None):
        if self.reentrancyGaurd:
            return
        self.reentrancyGaurd = 1
        try:
            if loginparam is None:
                raise RuntimeError('loginparam can not be None anymore dude')
            if loginparam[4]:
                ct = 'udp'
            else:
                ct = 'tcp'
            response = self.Connect(loginparam[2], loginparam[3], loginparam[0], loginparam[1], ct)
            return response
        finally:
            self.reentrancyGaurd = 0

    def LoginSso(self, token):
        if self.reentrancyGaurd:
            return
        self.reentrancyGaurd = 1
        try:
            if token is None:
                raise RuntimeError('Trying to do an SSO log in without an SSO token')
            response = self.ConnectSso(serverInfo.GetServerIP(GetServerName()), GetServerPort(), token, 'tcp')
            ssoAccessToken = response['access_token']
            sm.GetService('crestConnectionService').SetSessionToken(ssoAccessToken)
            return response
        finally:
            self.reentrancyGaurd = 0

    def Disconnect(self, silently = 0):
        if self.reentrancyGaurd:
            return
        self.reentrancyGaurd = 1
        try:
            self.machoNet.DisconnectFromServer()
        finally:
            self.reentrancyGaurd = 0

    def ConnectToProxyService(self, serviceName):
        return session.ConnectToRemoteService(serviceName, sm.services['machoNet'].myProxyNodeID)

    def ConnectToService(self, serviceName):
        return session.ConnectToRemoteService(serviceName)

    def IsConnected(self):
        return self.machoNet.IsConnected()

    def ClockSyncDaemon(self):
        syncRateMS = 300000
        while self.IsConnected():
            with ExceptionEater('Exception during soft clock sync'):
                blue.synchro.SleepWallclock(syncRateMS)
                log.LogInfo('*** Soft Clock Sync Starting ***')
                results = []
                numPings = 5
                blue.os.timeSyncAdjust = 0
                for i in xrange(numPings):
                    myTime = blue.os.GetWallclockTimeNow()
                    serverTime = sm.ProxySvc('machoNet').GetTime()
                    now = blue.os.GetWallclockTimeNow()
                    elaps = now - myTime
                    serverTime += elaps / 2
                    diff = float(now - serverTime)
                    results.append((elaps, diff))
                    log.LogInfo('SoftClock:', elaps, diff)

                averageElaps = sum([ x[0] for x in results ]) / numPings
                results = filter(lambda x: x[0] < averageElaps * 1.2, results)
                log.LogInfo('SoftClock results:', results)
                avgDiff = sum([ x[1] for x in results ]) / len(results)
                log.LogInfo('*** Soft Clock Sync adjusting by', -avgDiff / const.SEC, 'seconds')
                blue.os.timeSyncAdjust = long(-avgDiff)
                if abs(avgDiff) > 3 * const.SEC:
                    log.LogError('Having to adjust more than 3 seconds in a single timesync interval! (%fs per %ds)' % (avgDiff / float(const.SEC), syncRateMS / 1000))
                    syncRateMS = max(60000, syncRateMS - 60000)
                else:
                    syncRateMS = min(300000, syncRateMS + 60000)
                driftFactor = abs(avgDiff) / float(syncRateMS * const.MSEC)
                driftFactor = min(0.95, max(0.02, driftFactor))
                blue.os.timeSyncAdjustFactor = driftFactor

    def SynchronizeClock(self, firstTime = 1, maxIterations = 5):
        log.general.Log('connection.synchronizeClock called', log.LGINFO)
        if not firstTime:
            if self.clocklastsynchronized is not None and blue.os.GetWallclockTime() - self.clocklastsynchronized < const.HOUR:
                return
        if self.clocksynchronizing:
            return
        self.clocklastsynchronized = blue.os.GetWallclockTime()
        self.clocksynchronizing = 1
        try:
            diff = 0
            goodCount = 0
            lastElaps = None
            log.general.Log('***   ***   ***   ***   Clock Synchronizing loop initiating      ***   ***   ***   ***', log.LGINFO)
            for i in range(maxIterations):
                myTime = blue.os.GetWallclockTimeNow()
                serverTime = sm.ProxySvc('machoNet').GetTime()
                now = blue.os.GetWallclockTimeNow()
                elaps = now - myTime
                serverTime += elaps / 2
                diff = float(now - serverTime) / float(const.SEC)
                if diff > 2.0 and not firstTime:
                    logflag = log.LGERR
                else:
                    logflag = log.LGINFO
                log.general.Log('Synchronizing clock diff %.3f sec elaps %f sec.' % (diff, elaps / float(const.SEC)), logflag)
                if lastElaps is None or elaps < lastElaps and elaps < const.SEC:
                    goodCount += 1
                    log.general.Log('Synchronizing clock:  iteration completed, setting time', logflag)
                    blue.pyos.synchro.ResetClock(serverTime)
                    lastElaps = elaps
                else:
                    log.general.Log('Synchronizing clock:  iteration ignored as it was less accurate (%f) than our current time (%f)' % (elaps / float(const.SEC), lastElaps / float(const.SEC)), log.LGINFO)
                if goodCount >= 3:
                    break
                firstTime = 0

            log.general.Log('***   ***   ***   ***   Clock Synchronizing loop completed       ***   ***   ***   ***', log.LGINFO)
        finally:
            self.clocksynchronizing = 0

    def IsClockSynchronizing(self):
        if self.clocksynchronizing:
            log.general.Log('Clock synchronization in progress', log.LGINFO)
        return self.clocksynchronizing

    def __LongCallTimer(self):
        """
        Notify the user if we have waited for a long time for a remote call to complete.
        We let him know every few minutes with a suppressable message and log out a warning every minute
        """
        longWarningSecs = prefs.GetValue('longOutstandingCallWarningSeconds', DEFAULTLONGWAITWARNINGSECS)
        sleepSecs = 60
        if longWarningSecs < sleepSecs:
            sleepSecs = longWarningSecs
        self.LogInfo('__LongCallTimer reporting warnings after', longWarningSecs, 'seconds and checking every', sleepSecs, 'seconds')

        def ShouldWarn(method):
            """
            There are methods that block for a very long time on purpose, such as ones that contact
            another player before returning. Therefore we cannot give the player warning on all methods
            Picking ones that are called when you attach to or log into a location
            """
            for w in LONGWAITWARNINGMETHODS:
                if w in repr(method):
                    return True

            return False

        while self.state == service.SERVICE_RUNNING:
            if sm.GetService('machoNet').GetGlobalConfig().get('disableLongCallWarning'):
                self.LogWarn('__LongCallTimer should not be running! Exiting.')
                return
            blue.pyos.synchro.SleepWallclock(sleepSecs * 1000)
            try:
                maxDiff = 0
                for ct in base.outstandingCallTimers:
                    method = ct[0]
                    t = ct[1]
                    diff = blue.os.GetWallclockTimeNow() - t
                    if diff > maxDiff and ShouldWarn(method):
                        maxDiff = diff
                    if diff > 60 * const.SEC:
                        self.LogWarn('Have waited', FmtTime(diff), 'for', method)

                if maxDiff > longWarningSecs * const.SEC and self.lastLongCallTimestamp < blue.os.GetWallclockTimeNow() - longWarningSecs * const.SEC:
                    modalWnd = uicore.registry.GetModalWindow()
                    if modalWnd:
                        modalWnd.SetModalResult(uiconst.ID_CLOSE)
                    uthread.new(uicore.Message, 'LongWaitForRemoteCall', {'time': int(maxDiff / const.MIN)})
                    self.lastLongCallTimestamp = blue.os.GetWallclockTimeNow()
            except:
                log.LogException()
                sys.exc_clear()

    def OnClientStageChanged(self, state):
        if state == 'login':
            self.TryAutomaticLogin()

    def TryAutomaticLogin(self):
        """
        Check if the login parameter is used and if that's the case, try to
        automatically log into the client.
        """
        if GetLoginCredentials() is None or session.userid is not None:
            return
        username, password = GetLoginCredentials()
        self.Login((username,
         password,
         GetServerName(),
         GetServerPort(),
         None))
