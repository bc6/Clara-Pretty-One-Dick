#Embedded file name: carbon/common/script/sys\sessions.py
"""
    Sessions are a users first-order interface to the server.  Everything a user
    does goes through a session in one way or another.
"""
import blue
import uthread
import localization
import log
import copy
import types
from carbon.common.script.util.format import FmtDateEng
import carbon.common.script.net.machobase as machobase
from carbon.common.script.net.machoNetAddress import MachoAddress
import sys
import service
import base
import const
from markers import PopMark, PushMark
from collections import defaultdict
from service import *
from carbon.common.script.sys.basesession import *
import localstorage

def ThrottlePerMinute(max = 1, message = 'GenericStopSpamming'):

    def Helper(f):

        def Wrapper(*args, **kwargs):
            if session is not None and session.role & ROLE_PLAYER == ROLE_PLAYER:
                session.Throttle(f.__name__, max, const.MIN, message)
            return f(*args, **kwargs)

        return Wrapper

    return Helper


def ThrottlePer5Minutes(max = 1, message = 'GenericStopSpamming'):

    def Helper(f):

        def Wrapper(*args, **kwargs):
            if session is not None and session.role & ROLE_PLAYER == ROLE_PLAYER:
                session.Throttle(f.__name__, max, 5 * const.MIN, message)
            return f(*args, **kwargs)

        return Wrapper

    return Helper


def ThrottlePerSecond(max = 1, message = 'GenericStopSpamming'):

    def Helper(f):

        def Wrapper(*args, **kwargs):
            if session is not None and session.role & ROLE_PLAYER == ROLE_PLAYER:
                session.Throttle(f.__name__, max, const.SEC, message)
            return f(*args, **kwargs)

        return Wrapper

    return Helper


def SessionKillah(machoNet):
    """
    On servers: calls SessionMgr.RemoveSessionsFromServer() on the proxies of sessions that remain irrelevant
    """
    DEF_SESS_TIMEOUT = 120
    DEF_CTXSESS_TIMEOUT = 60
    DEF_SLEEPTIME = 30
    sleepTime = prefs.GetValue('sessionKillah.SleepTime', DEF_SLEEPTIME) * 1000
    while True:
        try:
            blue.pyos.synchro.SleepWallclock(sleepTime)
            killSessions = prefs.GetValue('sessionKillah.Enable', False)
            sessTimeout = prefs.GetValue('sessionKillah.SessionTimeout', DEF_SESS_TIMEOUT) * 1000
            ctxSessTimeout = prefs.GetValue('sessionKillah.ContextSessionTimeout', DEF_CTXSESS_TIMEOUT) * 1000
            sleepTime = prefs.GetValue('sessionKillah.SleepTime', DEF_SLEEPTIME) * 1000
            ReadContextSessionTypesPrefs()
            if killSessions:
                now = blue.os.GetWallclockTime()
                toRemove = defaultdict(list)
                for transport in machoNet.transportsByID.itervalues():

                    def AddIfIrrelevant(sess, timeout):
                        if sess.role & ROLE_SERVICE == 0 and not sess.connectedObjects and getattr(sess, 'charid', None):
                            if sess.contextOnly:
                                irrelevant = now - sess.lastRemoteCall >= timeout
                            else:
                                irrelevant = sess.irrelevanceTime is not None and now - sess.irrelevanceTime >= timeout
                            if irrelevant:
                                toRemove[transport].append(sess.sid)

                    for sess in transport.sessions.itervalues():
                        AddIfIrrelevant(sess, sessTimeout)

                    for sess in transport.contextSessions.itervalues():
                        AddIfIrrelevant(sess, ctxSessTimeout)

                myNodeID = machoNet.GetNodeID()
                for transport, sids in toRemove.iteritems():
                    try:
                        log.LogInfo('Asking proxy ', transport.nodeID, ' to remove ', len(sids), ' session(s)')
                        proxySessionMgr = machoNet.session.ConnectToRemoteService('sessionMgr', nodeID=transport.nodeID)
                        proxySessionMgr.RemoveSessionsFromServer(myNodeID, sids)
                    except StandardError:
                        log.LogException('While removing irrelevant session from serer')
                        sys.exc_clear()

        except Exception:
            log.LogException('In SessionKillah loop, caught to keep thread alive')
            sys.exc_clear()


def GetUndeadObjects():
    from util import allMonikers
    while 1:
        obs = []
        for each in allConnectedObjects.iterkeys():
            obs.append(each)

        break

    while 1:
        con = []
        for each in allObjectConnections.iterkeys():
            con.append(each)

        break

    while 1:
        ses = []
        for each in allSessionsBySID.itervalues():
            ses.append(each)

        break

    while 1:
        mon = []
        for each in allMonikers.iterkeys():
            mon.append(each)

        break

    zombies = []
    bombies = []
    for each in con:
        liveone = 0
        for other in ses:
            for yetanother in other.connectedObjects.itervalues():
                if each is yetanother[0]:
                    liveone = 1
                    break

        if not liveone:
            for other in mon:
                if other.boundObject is each:
                    liveone = 1
                    break

        if not liveone:
            zombies.append(each)

    for each in obs:
        liveone = 0
        for other in con:
            if other.__object__ is each:
                liveone = 1
                for yetanother in zombies:
                    if yetanother is other:
                        liveone = 2

                if liveone:
                    break

        if not liveone:
            zombies.append(each)
        elif liveone == 2:
            bombies.append(each)

    return (zombies, bombies)


def GetAllSessionInfo():
    return (allSessionsBySID, sessionsBySID, sessionsByAttribute)


def GetSessionMaps():
    return (sessionsBySID, sessionsByAttribute)


def CountSessions(attr, val):
    """
        Counts all sessions which have attribute 'attr' in val
    """
    cnt = 0
    for v in val:
        try:
            r = []
            for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
                if sid in sessionsBySID:
                    cnt += 1
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attr][v][each]

        except:
            srv = sm.services['sessionMgr']
            srv.LogError('Session map borked')
            srv.LogError('sessionsByAttribute=', sessionsByAttribute)
            srv.LogError('sessionsBySID=', sessionsBySID)
            log.LogTraceback()
            raise

    return cnt


def FindClients(attr, val):
    """
        Quicky function for macho, which requires clientID's, not sessions.
    """
    ret = []
    for v in val:
        try:
            r = []
            for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
                if sid in sessionsBySID:
                    s = sessionsBySID[sid]
                    if hasattr(s, 'clientID'):
                        ret.append(s.clientID)
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attr][v][each]

        except:
            srv = sm.services['sessionMgr']
            srv.LogError('Session map borked')
            srv.LogError('sessionsByAttribute=', sessionsByAttribute)
            srv.LogError('sessionsBySID=', sessionsBySID)
            log.LogTraceback()
            raise

    return ret


def FindSessionsAndHoles(attr, val, maxCount):
    ret = []
    nf = []
    attributes = attr.split('&')
    if len(attributes) > 1:
        if len(attributes) != len(val):
            raise RuntimeError('For a complex session query, the value must be a tuple of equal length to the complex query params')
        for i in range(len(val[0])):
            f = 0
            r = []
            for sid in sessionsByAttribute[attributes[0]].get(val[0][i], {}).iterkeys():
                if sid in sessionsBySID:
                    sess = sessionsBySID[sid]
                    k = 1
                    for j in range(1, len(val)):
                        if attributes[j] in ('corprole', 'rolesAtAll', 'rolesAtHQ', 'rolesAtBase', 'rolesAtOther'):
                            corprole = getattr(sess, attributes[j])
                            k = 0
                            for r2 in val[j]:
                                if r2 and r2 & corprole == r2:
                                    k = 1
                                    break

                        elif getattr(sess, attributes[j]) not in val[j]:
                            k = 0
                        if not k:
                            break

                    if k:
                        f = 1
                        clientID = getattr(sessionsBySID[sid], 'clientID', None)
                        if clientID is not None:
                            if maxCount is not None and len(ret) >= maxCount:
                                return (1, [], [])
                            ret.append(sessionsBySID[sid])
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attributes[0]][val[0][i]][each]

            if not f:
                nf.append(val[0][i])

        if len(nf):
            nf2 = list(copy.copy(val))
            nf2[0] = nf
            nf = nf2
        return (0, ret, nf)
    for v in val:
        f = 0
        r = []
        for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
            if sid in sessionsBySID:
                clientID = getattr(sessionsBySID[sid], 'clientID', None)
                if clientID is not None:
                    if maxCount is not None and len(ret) >= maxCount:
                        return (1, [], [])
                    ret.append(sessionsBySID[sid])
                    f = 1
            else:
                r.append(sid)

        for each in r:
            del sessionsByAttribute[attr][v][each]

        if not f:
            nf.append(v)

    return (0, ret, nf)


def GetSessions(sid = None):
    """
        For administrative purposes and stuff.  Returns all sessions, or the session specified
        by sid.
    """
    if sid is None:
        return sessionsBySID.values()
    else:
        return sessionsBySID.get(sid, None)


class SessionMgr(service.Service):
    __guid__ = 'svc.sessionMgr'
    __displayname__ = 'Session manager'
    __exportedcalls__ = {'GetSessionStatistics': [ROLE_SERVICE],
     'CloseUserSessions': [ROLE_SERVICE],
     'GetProxyNodeFromID': [ROLE_SERVICE],
     'GetClientIDsFromID': [ROLE_SERVICE],
     'UpdateSessionAttributes': [ROLE_SERVICE],
     'ConnectToClientService': [ROLE_SERVICE],
     'PerformSessionChange': [ROLE_SERVICE],
     'GetLocalClientIDs': [ROLE_SERVICE],
     'EndAllGameSessions': [ROLE_ADMIN | ROLE_SERVICE],
     'PerformHorridSessionAttributeUpdate': [ROLE_SERVICE],
     'BatchedRemoteCall': [ROLE_SERVICE],
     'GetSessionDetails': [ROLE_SERVICE],
     'TerminateClientConnections': [ROLE_SERVICE | ROLE_ADMIN],
     'RemoveSessionsFromServer': [ROLE_SERVICE]}
    __dependencies__ = []
    __notifyevents__ = ['ProcessSessionChange',
     'DoSessionChanging',
     'DoSimClockRebase',
     'OnGlobalConfigChanged']

    def __init__(self):
        service.Service.__init__(self)
        if machobase.mode == 'server':
            self.__dependencies__ += ['authentication', 'DB2']
        self.sessionClientIDCache = {'userid': {},
         'charid': {}}
        self.proxies = {}
        self.clientIDsByCharIDCache = {}
        self.sessionChangeShortCircuitReasons = []
        self.additionalAttribsAllowedToUpdate = []
        self.additionalStatAttribs = []
        self.additionalSessionDetailsAttribs = []
        self.sessionStatistics = None
        self.timeSessionStatsComputed = None
        if machobase.mode == 'server':
            uthread.new(SessionKillah, sm.GetService('machoNet')).context = 'sessions::SessionKillah'

    def GetProxySessionManager(self, nodeID):
        if nodeID not in self.proxies:
            self.proxies[nodeID] = self.session.ConnectToProxyServerService('sessionMgr', nodeID)
        return self.proxies[nodeID]

    def GetLocalClientIDs(self):
        ret = []
        for each in GetSessions():
            if hasattr(each, 'clientID'):
                ret.append(each.clientID)

        return ret

    def GetReason(self, oldReason, newReason, timeLeft):
        return localization.GetByLabel('/Carbon/UI/Sessions/SessionChangeInProgressBase')

    def __RaisePSCIP(self, oldReason, newReason, timeLeft = None):
        if oldReason is None:
            oldReason = ''
        if newReason is None:
            newReason = ''
        reason = self.GetReason(oldReason, newReason, timeLeft)
        self.LogInfo('raising a PerformSessionChangeInProgress user error with reason ', reason)
        raise UserError('PerformSessionChangeInProgress', {'reason': reason})

    def PerformSessionLockedOperation(self, *args, **keywords):
        return self.PerformSessionChange(*args, **keywords)

    def PerformSessionChange(self, sessionChangeReason, func, *args, **keywords):
        if 'hostileMutation' in keywords or 'violateSafetyTimer' in keywords or 'wait' in keywords:
            kw2 = copy.copy(keywords)
            hostile = keywords.get('hostileMutation', 0)
            wait = keywords.get('wait', 0)
            violateSafetyTimer = keywords.get('violateSafetyTimer', 0)
            if 'violateSafetyTimer' in kw2:
                del kw2['violateSafetyTimer']
            if 'hostileMutation' in kw2:
                del kw2['hostileMutation']
            if 'wait' in kw2:
                del kw2['wait']
        else:
            hostile = 0
            violateSafetyTimer = 0
            kw2 = keywords
            wait = 0
        self.LogInfo('Performing a locked session changing operation, reason=', sessionChangeReason)
        if machobase.mode == 'client':
            sess = session
            if not violateSafetyTimer and hostile in (0, 1) and sess.charid:
                if sess.nextSessionChange is not None and sess.nextSessionChange > blue.os.GetSimTime():
                    if wait > 0:
                        t = 1000 * (2 + (session.nextSessionChange - blue.os.GetSimTime()) / const.SEC)
                        self.LogInfo('PerformSessionChange is sleeping for %s ms' % t)
                        blue.pyos.synchro.SleepWallclock(t)
                if sess.nextSessionChange is not None and sess.nextSessionChange > blue.os.GetSimTime():
                    self.LogError("Too frequent session change attempts.  You'll just get yourself stuck doing this.  Ignoring.")
                    self.LogError('func=', func, ', args=', args, ', keywords=', keywords)
                    if sessionChangeReason in self.sessionChangeShortCircuitReasons:
                        return
                    self.__RaisePSCIP(sess.sessionChangeReason, sessionChangeReason, sess.nextSessionChange - blue.os.GetSimTime())
            else:
                self.LogInfo('Passing session change stuck prevention speedbump.  hostile=', hostile)
        else:
            raise RuntimeError('Not Yet Implemented')
        if sess.mutating and hostile in (0, 1):
            if sessionChangeReason in self.sessionChangeShortCircuitReasons:
                self.LogInfo('Ignoring session change attempt due to ' + sessionChangeReason + ' overzealousness')
                return
            self.__RaisePSCIP(sess.sessionChangeReason, sessionChangeReason)
        try:
            if hostile not in (2, 4):
                self.LogInfo('Incrementing the session mutation flag')
                sess.mutating += 1
            if sess.mutating == 1:
                self.LogInfo('Chaining ProcessSessionMutating event')
                sm.ChainEvent('ProcessSessionMutating', func, args, kw2)
                sess.sessionChangeReason = sessionChangeReason
            if hostile == 0:
                prev = sess.nextSessionChange
                if not violateSafetyTimer:
                    sess.nextSessionChange = blue.os.GetSimTime() + base.sessionChangeDelay
                localNextSessionChange = sess.nextSessionChange
                self.LogInfo('Pre-op updating next legal session change to ', FmtDateEng(sess.nextSessionChange))
                self.LogInfo('Executing the session modification method')
                try:
                    return apply(func, args, kw2)
                except:
                    if localNextSessionChange >= sess.nextSessionChange:
                        sess.nextSessionChange = prev
                        self.LogInfo('post-op exception handler reverting next legal session change to ', FmtDateEng(sess.nextSessionChange))
                    else:
                        self.LogInfo("post-op exception handler - Someone else has modified nextSessionChange, so DON'T revert it - modified value is ", FmtDateEng(sess.nextSessionChange))
                    raise

            elif hostile in (1, 3):
                self.LogInfo('Initiating Remote Mutation (local state change only), args=', args, ', keywords=', kw2)
            else:
                self.LogInfo('Finalizing Remote Mutation (local state change only), args=', args, ', keywords=', kw2)
        finally:
            self.LogInfo('Post-op updating next legal session change to ', FmtDateEng(sess.nextSessionChange))
            if hostile not in (1, 3):
                self.LogInfo('Decrementing the session mutation flag')
                sess.mutating -= 1
                if sess.mutating == 0:
                    self.LogInfo('Scattering OnSessionMutated event')
                    sm.ScatterEvent('OnSessionMutated', func, args, kw2)

    def GetProxyNodeFromID(self, idtype, theID, refresh = 0):
        if idtype != 'clientID':
            clientID = self.GetClientIDsFromID(idtype, theID, refresh)[0]
        else:
            clientID = theID
        return sm.services['machoNet'].GetProxyNodeIDFromClientID(clientID)

    def IsPlayerCharacter(self, charID):
        raise Exception('stub function not implemented')

    def GetClientIDsFromID(self, idtype, theID, refresh = 0):
        """
        Returns a list of clientIDs which match the given session filter
        """
        clientIDs = []
        if theID in sessionsByAttribute[idtype]:
            sids = sessionsByAttribute[idtype][theID]
            for sid in sids:
                if sid in sessionsBySID:
                    s = sessionsBySID[sid]
                    if getattr(s, 'clientID', 0):
                        if theID in self.sessionClientIDCache[idtype]:
                            del self.sessionClientIDCache[idtype][theID]
                        clientIDs.append(s.clientID)

        if not refresh and theID in self.sessionClientIDCache[idtype]:
            return self.sessionClientIDCache[idtype][theID]
        if not hasattr(self, 'dbzcluster'):
            self.dbzcluster = self.DB2.GetSchema('zcluster')
        clientID = None
        if idtype == 'charid':
            if self.IsPlayerCharacter(theID):
                if theID in self.clientIDsByCharIDCache:
                    clientID, lastTime = self.clientIDsByCharIDCache[theID]
                    if blue.os.GetWallclockTime() - lastTime > const.SEC:
                        clientID = None
                    else:
                        clientIDs.append(clientID)
                if clientID is None:
                    client = self.dbzcluster.Sessions_ByCharacterID(theID)
                    if len(client) and client[0].clientID:
                        clientID = client[0].clientID
                        clientIDs.append(clientID)
                self.clientIDsByCharIDCache[theID] = (clientID, blue.os.GetWallclockTime())
            else:
                log.LogTraceback('Thou shall only use GetClientIDsFromID for player characters', show_locals=1)
                clientID = None
        elif idtype == 'userid':
            for row in self.dbzcluster.Sessions_ByUserID(theID):
                if row.clientID:
                    clientIDs.append(row.clientID)

        else:
            raise RuntimeError('Can only currently characterID to locate a client through the DB')
        if not clientIDs:
            raise UnMachoDestination('The dude is not logged on')
        else:
            self.sessionClientIDCache[idtype][theID] = clientIDs
            return clientIDs

    def DoSessionChanging(self, *args):
        """
            Just here to remove annoying logs while nobody is listening.
        """
        pass

    def ProcessSessionChange(self, isRemote, sess, change):
        if 'userid' in change and change['userid'][0] in self.sessionClientIDCache['userid']:
            del self.sessionClientIDCache['userid'][change['userid'][0]]
        if 'charid' in change and change['charid'][0] in self.sessionClientIDCache['charid']:
            del self.sessionClientIDCache['charid'][change['charid'][0]]
        if machobase.mode == 'proxy':
            return -1

    def DoSimClockRebase(self, times):
        oldSimTime, newSimTime = times
        try:
            session.nextSessionChange += newSimTime - oldSimTime
        except:
            log.LogException('Exception while trying to rebase the session change timer')

    def OnGlobalConfigChanged(self, config):
        if 'sessionChangeDelay' in config:
            base.sessionChangeDelay = int(config['sessionChangeDelay']) * const.SEC

    def TypeAndNodeValidationHook(self, idType, id):
        pass

    def UpdateSessionAttributes(self, idtype, theID, dict):
        """
        Performs a session variable update on all sessions whose 'idtype' variable equals 'theID',
        sequentially for service sessions but otherwise in pseudo-parallel on a thread per session updated,
            updating the session on proxies but forwarding the call to the relevant proxy, on servers.
        """
        if idtype not in ['charid', 'userid'] + self.additionalAttribsAllowedToUpdate:
            raise RuntimeError("You shouldn't be calling this, as you obviously don't know what you're doing.  This is like one of the most sensitive things in the system, dude.")
        if machobase.mode == 'proxy' and theID not in sessionsByAttribute[idtype]:
            raise UnMachoDestination('Wrong proxy or client not connected')
        if machobase.mode == 'server' and idtype in ('userid', 'charid'):
            proxyNodeID = None
            try:
                proxyNodeID = self.GetProxyNodeFromID(idtype, theID, 1)
            except UnMachoDestination:
                sys.exc_clear()

            if proxyNodeID is not None:
                return self.GetProxySessionManager(proxyNodeID).UpdateSessionAttributes(idtype, theID, dict)
        sessions = FindSessions(idtype, [theID])
        if idtype == 'charid' and dict.has_key('flagRolesOnly') and sessions and len(sessions) > 0:
            sessioncorpid = sessions[0].corpid
            rolecorpid = dict['corpid']
            if sessioncorpid != rolecorpid:
                self.LogError('Character session is wrong!!! Character', theID, 'has session corp', sessioncorpid, 'but should be', rolecorpid, "I'll fix his session but please investigate why this occurred! Update dict:", dict, 'Session:', sessions[0])
        if dict.has_key('flagRolesOnly'):
            del dict['flagRolesOnly']
        self.TypeAndNodeValidationHook(idtype, theID)
        parallelCalls = []
        for each in sessions:
            if hasattr(each, 'clientID'):
                parallelCalls.append((self.PerformHorridSessionAttributeUpdate, (each.clientID, dict)))
            else:
                each.LogSessionHistory('Updating session information via sessionMgr::UpdateSessionAttributes')
                each.SetAttributes(dict)
                each.LogSessionHistory('Updated session information via sessionMgr::UpdateSessionAttributes')

        if len(parallelCalls) > 60:
            log.LogTraceback('Horrid session change going haywire.  Redesign the calling code!')
        uthread.parallel(parallelCalls)

    def PerformHorridSessionAttributeUpdate(self, clientID, dict):
        """
        Parallel thread method for UpdateSessionAttributes.
        On server forwards the call to client's proxy, otherwise sets the session's attributes.
        """
        try:
            if machobase.mode == 'server':
                proxyNodeID = self.GetProxyNodeFromID('clientID', clientID)
                return self.GetProxySessionManager(proxyNodeID).PerformHorridSessionAttributeUpdate(clientID, dict)
            s = sm.services['machoNet'].GetSessionByClientID(clientID)
            if s:
                s.LogSessionHistory('Updating session information via sessionMgr::UpdateSessionAttributes')
                s.SetAttributes(dict)
                s.LogSessionHistory('Updated session information via sessionMgr::UpdateSessionAttributes')
        except StandardError:
            log.LogException()
            sys.exc_clear()

    def GetSessionFromParams(self, idtype, theID):
        if idtype == 'clientID':
            s = sm.services['machoNet'].GetSessionByClientID(theID)
            if s is None:
                raise UnMachoDestination('Wrong proxy or client not connected, session not found by clientID=%s' % theID)
            return s
        if theID not in sessionsByAttribute[idtype]:
            raise UnMachoDestination('Wrong proxy or client not connected, session not found by %s=%s' % (idtype, theID))
        else:
            sids = sessionsByAttribute[idtype][theID].keys()
            if not len(sids) == 1:
                raise UnMachoDestination('Ambiguous idtype/id pair (%s/%s).  There are %d sessions that match them.' % (idtype, theID, len(sids)))
            else:
                sid = sids[0]
            if sid not in sessionsBySID:
                raise UnMachoDestination("The client's session is in an invalid or terminating state")
            return sessionsBySID[sid]

    def ConnectToClientService(self, svc, idtype, theID):
        if machobase.mode == 'proxy':
            s = self.GetSessionFromParams(idtype, theID)
            return sm.services['machoNet'].ConnectToRemoteService(svc, MachoAddress(clientID=s.clientID, service=svc), s)
        proxyNodeID = self.GetProxyNodeFromID(idtype, theID)
        try:
            return self.GetProxySessionManager(proxyNodeID).ConnectToClientService(svc, idtype, theID)
        except UnMachoDestination:
            sys.exc_clear()
            if not refreshed:
                return self.GetProxySessionManager(self.GetProxyNodeFromID(idtype, theID, 1)).ConnectToClientService(svc, idtype, theID)

    def GetSessionStatistics(self):
        """
        Returns a map: each session attribute ->
            [ num sessions on this node having that attribute, { each value of attribute -> num sessions having that value } ]
        for each of specially designated attributes: ["userid", "usertype"] + self.additionalStatAttribs
        as well as additional "virtual" attributes, see _AddToSessionStatistics()
        """
        now = blue.os.GetWallclockTime()
        statAttributes = ['userid', 'usertype'] + self.additionalStatAttribs
        if self.sessionStatistics is None or now - self.timeSessionStatsComputed > 5 * const.SEC:
            self.timeSessionStatsComputed = now
            self.sessionStatistics = {}
            for attribute, valuesOfAttribute in sessionsByAttribute.iteritems():
                if attribute in statAttributes:
                    attrValueCounts = {}
                    for attrValue, valueSessions in valuesOfAttribute.iteritems():
                        attrValueCounts[attrValue] = len(valueSessions)

                    self.sessionStatistics[attribute] = [len(valuesOfAttribute), attrValueCounts]

            self._AddToSessionStatistics()
        return self.sessionStatistics

    def _AddToSessionStatistics(self):
        """
        Adds the counts for Core "virtual attributes":
            "CARBON:{Game|CREST}{Char|User}" -> number of Game/CREST character/User sessions (session with charid)
        Virtual attr x appears in returned session stats map as: x ->
            [ num sessions having that attribute, None -> num sessions having that value ]
        For backwards compatibility with real session attribute stats in the map
        """
        machoChar = CRESTChar = machoUser = CRESTUser = 0
        for sess in base.sessionsBySID.itervalues():
            if sess.sessionType == const.session.SESSION_TYPE_GAME:
                if sess.charid:
                    machoChar += 1
                else:
                    machoUser += 1
            elif sess.sessionType == const.session.SESSION_TYPE_CREST:
                if sess.charid:
                    CRESTChar += 1
                else:
                    CRESTUser += 1

        self.sessionStatistics['CARBON:MachoChar'] = (machoChar, {None: machoChar})
        self.sessionStatistics['CARBON:MachoUser'] = (machoUser, {None: machoUser})
        self.sessionStatistics['CARBON:CRESTChar'] = (CRESTChar, {None: CRESTChar})
        self.sessionStatistics['CARBON:CRESTUser'] = (CRESTUser, {None: CRESTUser})

    def Run(self, memstream = None):
        service.Service.Run(self, memstream)
        self.AppRun(memstream)

    def AppRun(self, memstream = None):
        """Application override"""
        pass

    def BatchedRemoteCall(self, batchedCalls):
        """
            Forwarding method, used by ServiceCallGPCS to do cool shit.
        """
        retvals = []
        for callID, (service, method, args, keywords) in batchedCalls.iteritems():
            try:
                c = '%s::%s (Batched\\Server)' % (service, method)
                timer = PushMark(c)
                try:
                    with CallTimer(c):
                        retvals.append((0, callID, apply(getattr(sm.GetService(service), method), args, keywords)))
                finally:
                    PopMark(timer)

            except StandardError as e:
                if getattr(e, '__passbyvalue__', 0):
                    retvals.append((1, callID, strx(e)))
                else:
                    retvals.append((1, callID, e))
                sys.exc_clear()

        return retvals

    def GetSessionValuesFromRowset(self, si):
        return {}

    def GetInitialValuesFromCharID(self, charID):
        return {}

    def CloseUserSessions(self, userIDs, reason, clientID = None):
        """
            Closes all sessions owned by users in userIDs, except the one having clientID if specified.
            Causes a transport disconnect as well.
        """
        if type(userIDs) not in (types.ListType, types.TupleType):
            userIDs = [userIDs]
        for each in FindSessions('userid', userIDs):
            if clientID is None or not hasattr(each, 'clientID') or each.clientID != clientID:
                each.LogSessionHistory(reason)
                CloseSession(each)

    def TerminateClientConnections(self, reason, filter):
        """
            Performs a macho.TerminateClient on all clientID having a session with matching attr:value pairs
            as specified in the filter
        """
        if machobase.mode != 'proxy' or not isinstance(filter, types.DictType) or len(filter) == 0:
            raise RuntimeError('TerminateClientConnections should only be called on a proxy and with a non-empty filter dictionnary')
        numDisconnected = 0
        for clientSession in GetSessions():
            blue.pyos.BeNice()
            if hasattr(clientSession, 'clientID') and not clientSession.role & ROLE_SERVICE:
                clientID = getattr(clientSession, 'clientID')
                if clientID is None:
                    continue
                skip = False
                for attr, value in filter.iteritems():
                    if not (hasattr(clientSession, attr) and getattr(clientSession, attr) == value):
                        skip = True
                        break

                if not skip:
                    numDisconnected += 1
                    clientSession.LogSessionHistory('Connection terminated by administrator %s, reason is: %s' % (str(session.userid), reason))
                    sm.GetService('machoNet').TerminateClient(reason, clientID)

        return numDisconnected

    def EndAllGameSessions(self, remote = 0):
        if remote:
            self.session.ConnectToAllProxyServerServices('sessionMgr').EndAllGameSessions()
        else:
            txt = ''
            for s in GetSessions():
                blue.pyos.BeNice()
                if hasattr(s, 'clientID') and not s.role & ROLE_SERVICE:
                    sid = s.sid
                    s.LogSessionHistory('Session closed by administrator %s' % str(session.userid))
                    CloseSession(s, True)

    def RemoveSessionsFromServer(self, nodeID, sessionIDs):
        """
        On proxy: remove the sessions 'sessionIDs' from server node 'nodeID',
        by faking TransportClosed messages. This call comes from server 'nodeID', it having detected
        that the sessions are no longer relevant to the server. Note that the sessions are _not_ removed
        from the proxy and that "race conditions" are OK: in the worst-case a removed relevant session
        will be re-JITed to the server again, ahead of a notification or call.
        """
        if machobase.mode != 'proxy':
            raise RuntimeError('RemoveSessionsFromServer should only be called on a proxy')
        log.LogInfo('CTXSESS: RemoveSessionsFromServer(nodeID=', nodeID, '), with ', len(sessionIDs), ' session IDs')
        mn = sm.services['machoNet']
        serverTID = mn.transportIDbySolNodeID.get(nodeID, None)
        if serverTID is not None:
            serverTransport = mn.transportsByID[serverTID]
            for sid in sessionIDs:
                sess = sessionsBySID.get(sid, None)
                if sess is not None:
                    uthread.worker('SessionMgr::RemoveSesssionsFromServer', serverTransport.RemoveSessionFromServer, sess)

        else:
            log.LogWarning('RemoveSessionsFromServer() called with unknown or non-server nodeID ', nodeID)

    def GetSessionDetails(self, clientID, sid):
        import htmlwriter
        macho = sm.GetService('machoNet')
        if clientID:
            s = macho.GetSessionByClientID(clientID)
        else:
            s = GetSessions(sid)
        if s is None:
            return
        info = [['sid', s.sid],
         ['version', s.version],
         ['clientID', getattr(s, 'clientID', '')],
         ['userid', s.userid],
         ['userType', s.userType],
         ['role', s.role],
         ['charid', s.charid],
         ['lastRemoteCall', s.lastRemoteCall]]
        for each in self.additionalSessionDetailsAttribs:
            info.append([each, s.__dict__[each]])

        sessionsBySID, sessionsByAttribute = GetSessionMaps()
        for each in info:
            if each[0] == 'sid':
                if each[1] not in sessionsBySID:
                    each[1] = str(each[1]) + ' <b>(Not in sessionsBySID)</b>'
            elif each[0] in sessionsByAttribute:
                a = getattr(s, each[0])
                if a:
                    if a not in sessionsByAttribute[each[0]]:
                        each[1] = str(each[1]) + " <b>(Not in sessionsByAttribute['%s'])</b>" % each[0]
                    elif s.sid not in sessionsByAttribute[each[0]].get(a, {}):
                        each[1] = str(each[1]) + " <b>(Not in sessionsByAttribute['%s']['%s'])</b>" % (each[0], a)

        info.append(['IP Address', getattr(s, 'address', '?')])
        connectedObjects = []
        hd = ['ObjectID', 'References', 'Object']
        for k, v in s.machoObjectsByID.iteritems():
            tmp = [k, '%s.%s' % (FmtDateEng(v[0]), v[0] % const.SEC), htmlwriter.Swing(str(v[1]))]
            if isinstance(v[1], ObjectConnection):
                tmp[2] = str(tmp[2]) + ' (c2ooid=%s)' % str(v[1].__dict__['__c2ooid__'])
                if v[1].__dict__['__c2ooid__'] not in s.connectedObjects:
                    tmp[2] = str(tmp[2]) + ' <b>(Not in s.connectedObjects)</b>'
                else:
                    object = v[1].__dict__['__object__']
                    if s.sid not in object.sessionConnections:
                        tmp[2] = str(tmp[2]) + ' <b>(s.sid not in object.sessionConnections)</b>'
                    if s.sid not in object.objectConnections or v[1].__dict__['__c2ooid__'] not in object.objectConnections[s.sid]:
                        tmp[2] = str(tmp[2]) + ' <b>([s.sid][c2ooid]) not part of object.objectConnections)</b>'
            if k not in sessionsByAttribute['objectID']:
                tmp[2] = str(tmp[2]) + " <b>(Not in sessionsByAttribute['objectID'])</b>"
            elif s.sid not in sessionsByAttribute['objectID'][k]:
                tmp[2] = str(tmp[2]) + " <b>(Not in sessionsByAttribute['objectID']['%s'])</b>" % k
            connectedObjects.append(tmp)

        sessionHistory = []
        lastEntry = ''
        i = 0
        for each in s.sessionhist:
            tmp = each[2].replace('\n', '<br>')
            if tmp == lastEntry:
                txt = '< same >'
            else:
                txt = tmp
            lastEntry = tmp
            sessionHistory.append((each[0],
             i,
             each[1],
             htmlwriter.Swing(txt)))
            i += 1

        streamInfo = []
        try:
            streams = macho.transportsByID[macho.transportIDbySessionID[s.sid]].readers
            for stream in streams:
                streamInfo.append((stream.streamID,
                 stream.request.remote_addr,
                 stream.sequence_number,
                 stream.reconnects,
                 stream.GetActiveSetSize()))

        except KeyError:
            pass

        return (info,
         connectedObjects,
         sessionHistory,
         s.calltimes,
         s.sessionVariables,
         streamInfo)


def IsSessionChangeDisconnect(change, character = False):
    """
    Checks the change dict provided to ProcessSessionChange to see if this is a disconnect event,
    returns the userID for the disconnected user if it is.
    """
    key = 'charid' if character else 'userid'
    if key in change and change[key][0] is not None and change[key][1] is None:
        return change[key][0]
    else:
        return False


class ClientContext(localstorage.UpdatedLocalStorage):

    def __init__(self, applicationID = None, languageID = None):
        localstorage.UpdatedLocalStorage.__init__(self, {'base.ClientContext': True,
         'applicationID': applicationID,
         'languageID': languageID})


class MethodCachingContext(localstorage.UpdatedLocalStorage):

    def __init__(self, methodCachingScope):
        localstorage.UpdatedLocalStorage.__init__(self, {'base.MethodCachingContext': methodCachingScope})


def CachedMethodCalled(cacheKey, details):
    """
    A cached method was called, we should remember the caching details for it if we are in a CachePublic scope
    """
    try:
        cacheScope = localstorage.GetLocalStorage()['base.MethodCachingContext']
        if details:
            clientTimes = details['versionCheck']
            if clientTimes:
                clientTime = clientTimes[0]
                cacheScope[cacheKey] = (sm.GetService('objectCaching').__versionchecktimes__[clientTime], 'sessionInfo' in details)
    except KeyError:
        pass


sessionChangeDelay = SESSIONCHANGEDELAY
exports = {'base.CreateSession': CreateSession,
 'base.SessionMgr': SessionMgr,
 'base.GetServiceSession': GetServiceSession,
 'base.CloseSession': CloseSession,
 'base.GetSessions': GetSessions,
 'base.FindSessions': FindSessions,
 'base.CountSessions': CountSessions,
 'base.FindClientsAndHoles': FindClientsAndHoles,
 'base.FindSessionsAndHoles': FindSessionsAndHoles,
 'base.ObjectConnection': ObjectConnection,
 'base.GetCallTimes': GetCallTimes,
 'base.CallTimer': CallTimer,
 'base.EnableCallTimers': EnableCallTimers,
 'base.CallTimersEnabled': CallTimersEnabled,
 'base.FindClients': FindClients,
 'base.GetSessionMaps': GetSessionMaps,
 'base.GetAllSessionInfo': GetAllSessionInfo,
 'base.allObjectConnections': allObjectConnections,
 'base.allConnectedObjects': allConnectedObjects,
 'base.GetUndeadObjects': GetUndeadObjects,
 'base.GetObjectUUID': GetObjectUUID,
 'base.GetObjectByUUID': GetObjectByUUID,
 'base.sessionChangeDelay': sessionChangeDelay,
 'base.GetNewSid': GetNewSid,
 'base.sessionsBySID': sessionsBySID,
 'base.allSessionsBySID': allSessionsBySID,
 'base.sessionsByAttribute': sessionsByAttribute,
 'base.outstandingCallTimers': outstandingCallTimers,
 'base.dyingObjects': dyingObjects,
 'base.methodCallHistory': methodCallHistory,
 'base.IsInClientContext': IsInClientContext,
 'base.IsSessionChangeDisconnect': IsSessionChangeDisconnect,
 'base.ClientContext': ClientContext,
 'base.MethodCachingContext': MethodCachingContext,
 'base.CachedMethodCalled': CachedMethodCalled,
 'base.ThrottlePerMinute': ThrottlePerMinute,
 'base.ThrottlePer5Minutes': ThrottlePer5Minutes,
 'base.ThrottlePerSecond': ThrottlePerSecond}
