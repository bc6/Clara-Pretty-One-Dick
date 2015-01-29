#Embedded file name: eve/client/script/util\jumpMonitor.py
"""
Monitors jump request and completion, submitting timing info 
"""
from service import *
import sys
import blue
import base
import uthread
import types
import util
MAXALLOWEDJUMPTIMEINMS = 600000

class jumpMonitor(Service):
    __guid__ = 'svc.jumpMonitor'
    __displayname__ = 'Jump Monitoring Service'
    __exportedcalls__ = {}
    __dependencies__ = []
    __notifyevents__ = ['OnSessionChanged',
     'DoBallsAdded',
     'OnChannelsJoined',
     'DoSessionChanging',
     'OnSessionMutated',
     'OnGlobalConfigChanged']

    def __init__(self):
        Service.__init__(self)

    def Run(self, memStream = None):
        Service.Run(self, memStream)
        self.useJumpMonitor = False
        self.jumping = False
        self.jumpStartTime = 0
        self.jumpType = None
        self.CheckJumpCompletedTimer = None
        self.checkBallpark = True
        self.state = SERVICE_RUNNING

    def Stop(self, stream):
        Service.Stop(self)
        self.state = SERVICE_STOPPED

    def OnGlobalConfigChanged(self, configVals):
        """
        Listen to global config value changes in order to see whether we
        should do our work.
        """
        self.useJumpMonitor = bool(configVals.get('useClientSideJumpMonitor'))

    def OnSessionMutated(self, isremote, session, change):
        """
            OnSessionMutated is called on the client, by the client when certain jump events
            are requested. The only way to differentiate between jump types is to observe the 
            change dictionnary and trap known patterns.    
            
            Current patterns of change are:
                wormhole jump: chnage contains a single value, the wormhole object. Which 
                    is a fake item not in the DB
                stargate jump: the clean one really, change contains 2 values, both stargates itemID
                cyno jump: 3 value tuple, of the form: character holding the cyno, cyno itemID 
                    (which is fakeItem too) and destination solarsystem
        """
        if not self.useJumpMonitor:
            return
        try:
            if type(session) == types.TupleType:
                if len(session) == 1 and session[0] >= const.minFakeItem:
                    self.jumpStartTime = blue.os.GetWallclockTime()
                    self.jumpType = 'wormhole %s' % session[0]
                    self.checkBallpark = True
                elif len(session) == 2 and util.IsStargate(session[0]) and util.IsStargate(session[1]):
                    self.jumpStartTime = blue.os.GetWallclockTime()
                    self.jumpType = 'stargate %d->%d' % (session[0], session[1])
                    self.checkBallpark = True
                elif len(session) == 2 and util.IsPlayerItem(session[0]) and util.IsSolarSystem(session[1]):
                    self.jumpStartTime = blue.os.GetWallclockTime()
                    self.jumpType = 'pos cyno array:%d' % (session[0],)
                    self.checkBallpark = True
                elif len(session) == 3 and util.IsPlayerItem(session[0]) and util.IsPlayerItem(session[1]) and util.IsSolarSystem(session[2]):
                    self.jumpStartTime = blue.os.GetWallclockTime()
                    self.jumpType = 'bridge src:%s dst:%d in:%d' % (session[0], session[1], session[2])
                    self.checkBallpark = True
                elif len(session) == 3 and util.IsCharacter(session[0]) and util.IsSolarSystem(session[2]):
                    self.jumpStartTime = blue.os.GetWallclockTime()
                    self.jumpType = 'cyno char:%s cyno:%d' % (session[0], session[1])
                    self.checkBallpark = True
                elif len(session) == 4 and util.IsCharacter(session[0]) and util.IsPlayerItem(session[1]) and util.IsSolarSystem(session[3]):
                    self.jumpStartTime = blue.os.GetWallclockTime()
                    self.jumpType = 'ship bridge char:%s-%s cyno:%d' % (session[0], session[1], session[2])
                    self.checkBallpark = True
        except:
            sys.exc_clear()

    def DoSessionChanging(self, isremote, session, change):
        """
            DoSessionChanging is the real jump detector, trigered by the server ack'ing our jump request. We 
            rely on OnSessionMutated to start the timer and detect type for the common jumps. pod kills, 
            clone jumps and /tr commands do not generate a OnSessionMutated so we trap them here and
            set the jumpType accordingly        
        """
        if not self.useJumpMonitor:
            return
        if 'locationid' not in change or change['locationid'][0] is None:
            return
        if 'solarsystemid2' not in change:
            return
        if self.CheckJumpCompletedTimer:
            self.LogError('JumpMonitor: Jump detected in DoSessionChanging but last jump not completed?')
            reportingString = 'JumpMonitor: OVERLAPPED JUMP %s->%s type[%s] start:%d,local:%d,sess:%d,ballpark:%d ' % (self.jumpOrigin,
             self.jumpDestination,
             self.jumpType,
             self.jumpStartTime,
             self.localLoadedEnd,
             self.sessionChangedEnd,
             self.ballparkLoadedEnd)
            reportingString += ' new jump: %s:%s ' % change['solarsystemid2']
            uthread.new(sm.ProxySvc('clientStatLogger').LogString, reportingString)
        if 'shipid' in change and change['shipid'][0] and not change['shipid'][1]:
            self.jumpStartTime = blue.os.GetWallclockTime()
            self.jumpType = 'podkill'
            self.checkBallpark = False
        elif 'stationid' in change and change['stationid'][0] and change['stationid'][1]:
            self.jumpStartTime = blue.os.GetWallclockTime()
            self.jumpType = 'clonejump'
            self.checkBallpark = False
        if self.jumpType is None:
            self.jumpStartTime = blue.os.GetWallclockTime()
            self.jumpType = '/tr'
            self.checkBallpark = not ('stationid' in change and change['stationid'][1])
        self.jumpOrigin = session.locationid
        self.jumpDestination = change['locationid'][1]
        self.jumping = True
        self.sessionChanged = False
        self.localLoaded = False
        self.ballparkLoaded = False
        self.localLoadedEnd = 0
        self.sessionChangedEnd = 0
        self.ballparkLoadedEnd = 0
        self.CheckJumpCompletedTimer = base.AutoTimer(1000, self.CheckJumpCompleted)

    def CheckJumpCompleted(self):
        """
            the end of jump detector. resets timer and log on the proxy the timing info for the completed jump        
        """
        if self.jumping and self.sessionChanged and self.localLoaded and (self.ballparkLoaded or not self.checkBallpark):
            self.CheckJumpCompletedTimer = None
            self.jumpEndTime = blue.os.GetWallclockTime()
            self.jumping = False
            reportingString = 'JumpMonitor: %s->%s type[%s] start:%d,local:%d,sess:%d,ballpark:%d\n' % (self.jumpOrigin,
             self.jumpDestination,
             self.jumpType,
             self.jumpStartTime,
             self.localLoadedEnd,
             self.sessionChangedEnd,
             self.ballparkLoadedEnd)
            sm.ProxySvc('clientStatLogger').LogString(reportingString)
            self.jumpType = None
        elif self.jumping and blue.os.TimeDiffInMs(self.jumpStartTime, blue.os.GetWallclockTime()) > MAXALLOWEDJUMPTIMEINMS:
            reportingString = 'JumpMonitor: INCOMPLETE %s->%s type[%s] start:%d,local:%d,sess:%d,ballpark:%d\n' % (self.jumpOrigin,
             self.jumpDestination,
             self.jumpType,
             self.jumpStartTime,
             self.localLoadedEnd,
             self.sessionChangedEnd,
             self.ballparkLoadedEnd)
            sm.ProxySvc('clientStatLogger').LogString(reportingString)
            self.jumpType = None
            self.CheckJumpCompletedTimer = None
            self.jumpEndTime = blue.os.GetWallclockTime()
            self.jumping = False

    def OnSessionChanged(self, isRemote, session, change):
        """
            detect the update to the session sent from the Sol
        """
        if self.jumping and not self.sessionChanged and ('locationid' in change or 'solarsystemid' in change or 'solarsystemid2' in change):
            self.sessionChanged = True
            self.sessionChangedEnd = blue.os.GetWallclockTime()
            uthread.new(self.CheckJumpCompleted)

    def DoBallsAdded(self, *args, **kw):
        """
            detects the AddBall event from the server, indicating we now have an active grid
        """
        if self.jumping and not self.ballparkLoaded:
            self.ballparkLoaded = True
            self.ballparkLoadedEnd = blue.os.GetWallclockTime()
            uthread.new(self.CheckJumpCompleted)

    def OnChannelsJoined(self, channelIDs):
        """
            detect when we join the new local chat channel
        """
        if self.jumping and not self.localLoaded:
            try:
                local = [ chan for chan in channelIDs if type(chan) == types.TupleType and type(chan[0]) == types.TupleType and 'solarsystemid2' == chan[0][0] ]
                if local:
                    self.localLoaded = True
                    self.localLoadedEnd = blue.os.GetWallclockTime()
                    uthread.new(self.CheckJumpCompleted)
            except:
                pass
