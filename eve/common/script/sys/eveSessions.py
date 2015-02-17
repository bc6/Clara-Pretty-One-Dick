#Embedded file name: eve/common/script/sys\eveSessions.py
import math
import blue
from eve.common.script.sys.eveCfg import IsSolarSystem, IsStation, IsCharacter
import carbon.common.script.net.machobase as macho
import carbon.common.script.sys.service as service
from carbon.common.script.sys.service import *
from inventorycommon.util import IsNPC
import const
import base
import logConst
import localization
eveSessionsByAttribute = {'regionid': {},
 'constellationid': {},
 'corpid': {},
 'fleetid': {},
 'wingid': {},
 'squadid': {},
 'shipid': {},
 'stationid': {},
 'stationid2': {},
 'worldspaceid': {},
 'locationid': {},
 'solarsystemid': {},
 'solarsystemid2': {},
 'allianceid': {},
 'warfactionid': {}}
base.sessionsByAttribute.update(eveSessionsByAttribute)

def GetCharLocation(charID):
    """returns a tuple (locationID, locationGroupID)"""
    return GetCharLocation2(charID)[0:2]


def GetCharLocation2(charID):
    """returns a tuple (locationID, locationGroupID, charLocationID)"""
    try:
        x, y, z = GetCharLocationEx(charID)
    except RuntimeError:
        y = None

    if y is None:
        charUnboundMgr = sm.services['charUnboundMgr']
        charMgr = sm.services['charMgr']
        charUnboundMgr.MoveCharacter(charID, charMgr.GetHomeStation(charID), 0)
        x, y, z = GetCharLocationEx(charID)
        if y is None:
            raise RuntimeError('Bogus character item state', charID, x, z)
    return (x, y, z)


def IsLocationNode(session):
    """
    Returns True if this node is the sessions current location node, that is, the the location of this session
    is handled on this node
    """
    if not macho.mode == 'server':
        return False
    machoNet = sm.GetService('machoNet')
    currentNodeID = machoNet.GetNodeID()
    return any((session.solarsystemid and currentNodeID == machoNet.GetNodeFromAddress(const.cluster.SERVICE_BEYONCE, session.solarsystemid), session.stationid and currentNodeID == machoNet.GetNodeFromAddress('station', session.stationid), session.worldspaceid and currentNodeID == machoNet.GetNodeFromAddress(const.cluster.SERVICE_WORLDSPACE, session.worldspaceid)))


def GetCharLocationEx(charID):
    """returns a tuple (locationID, locationGroupID, charLocationID)"""
    sessions = base.FindSessions('charid', [charID])
    if len(sessions) and IsLocationNode(sessions[0]):
        s = sessions[0]
        if s.solarsystemid:
            return (s.solarsystemid, const.groupSolarSystem, s.shipid)
        if s.stationid and s.shipid:
            return (s.stationid, const.groupStation, s.shipid)
        if s.stationid:
            return (s.stationid, const.groupStation, s.stationid)
        if s.worldspaceid:
            return (s.worldspaceid, const.groupWorldSpace, s.worldspaceid)
    else:
        while sm.services['DB2'].state != SERVICE_RUNNING:
            blue.pyos.synchro.SleepWallclock(100)

        rs = sm.services['DB2'].GetSchema('character').Characters_LocationInfo(charID)
        locationInfo = rs[0]
        if locationInfo.locationID is None:
            raise RuntimeError('No such locationID', locationInfo.locationID, 'for charID', charID)
        if locationInfo.locationGroupID in (const.groupStation, const.groupSolarSystem, const.groupWorldSpace):
            return (locationInfo.locationID, locationInfo.locationGroupID, locationInfo.characterLocationID)
        return (locationInfo.locationID, None, locationInfo.characterLocationID)


def IsUndockingSessionChange(session, change):
    """
    Returns true if the session-change represents an undocking action
    - ie starts in a station and ends in space
    """
    goingFromStation = change.has_key('stationid') and change.get('stationid')[0]
    goingToSpace = change.has_key('solarsystemid') and change.get('solarsystemid')[1]
    return goingFromStation and goingToSpace


class SessionMgr(base.SessionMgr):
    __guid__ = 'svc.eveSessionMgr'
    __displayname__ = 'Session manager'
    __replaceservice__ = 'sessionMgr'
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
     'CreateCrestSession': [ROLE_SERVICE],
     'GetInitialValuesFromCharID': [ROLE_SERVICE],
     'RemoveSessionsFromServer': [ROLE_SERVICE]}
    __dependencies__ = []
    __notifyevents__ = ['ProcessInventoryChange'] + base.SessionMgr.__notifyevents__

    def __init__(self):
        base.SessionMgr.__init__(self)
        if macho.mode == 'server':
            self.__dependencies__ += ['config',
             'station',
             'ship',
             'corporationSvc',
             'corpmgr',
             'i2',
             'stationSvc',
             'cache']
        self.sessionChangeShortCircuitReasons = ['autopilot']
        self.additionalAttribsAllowedToUpdate = ['allianceid', 'corpid']
        self.additionalStatAttribs = ['solarsystemid', 'solarsystemid2']
        self.additionalSessionDetailsAttribs = ['allianceid',
         'warfactionid',
         'corpid',
         'corprole',
         'shipid',
         'regionid',
         'constellationid',
         'solarsystemid2',
         'locationid',
         'solarsystemid',
         'stationid',
         'stationid2',
         'worldspaceid',
         'fleetid',
         'wingid',
         'squadid',
         'fleetrole',
         'fleetbooster',
         'corpAccountKey',
         'inDetention']

    def AppRun(self, memstream = None):
        if macho.mode == 'server':
            self.dbcharacter = self.DB2.GetSchema('character')

    def GetReason(self, oldReason, newReason, timeLeft):
        """ Get the application specific reason why we are not 
        willing to do a session change at this moment in time."""
        if timeLeft:
            seconds = int(math.ceil(max(1, timeLeft) / float(const.SEC)))
        reason = localization.GetByLabel('UI/Sessions/BaseReason')
        if oldReason == newReason or oldReason.startswith('fleet.') and newReason.startswith('fleet.') or oldReason.startswith('corp.') and newReason.startswith('corp.'):
            if oldReason.startswith('fleet.'):
                reason = localization.GetByLabel('UI/Sessions/FleetOperation')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EstimatedTimeLeft', reason=reason, seconds=seconds)
            elif oldReason.startswith('corp.'):
                reason = localization.GetByLabel('UI/Sessions/CorpOperation')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EstimatedTimeLeft', reason=reason, seconds=seconds)
            elif oldReason == 'undock':
                reason = localization.GetByLabel('UI/Sessions/Undocking')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EstimatedTimeLeft', reason=reason, seconds=seconds)
            elif oldReason == 'dock':
                reason = localization.GetByLabel('UI/Sessions/Docking')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EstimatedTimeLeft', reason=reason, seconds=seconds)
            elif oldReason == 'jump' and newReason == 'jump':
                reason = localization.GetByLabel('UI/Sessions/Jump')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EstimatedTimeLeft', reason=reason, seconds=seconds)
            elif oldReason == 'jump':
                reason = localization.GetByLabel('UI/Sessions/StartgateJump')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/StartgateJumpEstimatedTime', reason=reason, seconds=seconds)
            elif oldReason == 'eject':
                reason = localization.GetByLabel('UI/Sessions/Ejecting')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EjectingEstimatedTime', reason=reason, seconds=seconds)
            elif oldReason == 'evacuate':
                reason = localization.GetByLabel('UI/Sessions/Evacuation')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EvacuationsEstimatedTime', reason=reason, seconds=seconds)
            elif oldReason == 'board':
                reason = localization.GetByLabel('UI/Sessions/Boarding')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/BoardingEstimatedTime', reason=reason, seconds=seconds)
            elif oldReason == 'selfdestruct':
                reason = localization.GetByLabel('UI/Sessions/SelfDestruct')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/SelfDestructEstimatedTime', reason=reason, seconds=seconds)
            elif oldReason == 'charsel':
                reason = localization.GetByLabel('UI/Sessions/CharacterSelection')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/CharacterSelectionEstimatedTime', reason=reason, seconds=seconds)
            elif oldReason == 'storeVessel':
                reason = localization.GetByLabel('UI/Sessions/Embarkation')
                if timeLeft:
                    reason = localization.GetByLabel('UI/Sessions/EmbarkationEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'autopilot':
            reason = localization.GetByLabel('UI/Sessions/Autopilot')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AutopilotEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'undock':
            reason = localization.GetByLabel('UI/Sessions/AreUndocking')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreUndockingEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'dock':
            reason = localization.GetByLabel('UI/Sessions/AreDocking')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreDockingEstimmatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'jump':
            reason = localization.GetByLabel('UI/Sessions/AreJumping')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreJumpingEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'eject':
            reason = localization.GetByLabel('UI/Sessions/AreEjecting')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreEjectingEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'evacuate':
            reason = localization.GetByLabel('UI/Sessions/AreEvacuating')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreEvacuatingEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'board':
            reason = localization.GetByLabel('UI/Sessions/AreBoarding')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreBoardingEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'selfdestruct':
            reason = localization.GetByLabel('UI/Sessions/AreSelfDestructing')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreSelfDestructiongEstimateTime', reason=reason, seconds=seconds)
        elif oldReason == 'charsel':
            reason = localization.GetByLabel('UI/Sessions/AreSelectingCharacter')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreSelectingCharacterEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'accelerationgate':
            reason = localization.GetByLabel('UI/Sessions/AreUsingAccelerationGate')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreUsingAccelerationGateEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason.startswith('corp.'):
            reason = localization.GetByLabel('UI/Sessions/CorpActivity')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/CorpActivityEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason.startswith('fleet.'):
            reason = localization.GetByLabel('UI/Sessions/FleetOperations')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/FleetOperationsEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'storeVessel':
            reason = localization.GetByLabel('UI/Sessions/AreBoardingVessel')
            if timeLeft:
                reason = localization.GetByLabel('UI/Sessions/AreBoardingVesselEstimatedTime', reason=reason, seconds=seconds)
        elif oldReason == 'bookmarking':
            reason = localization.GetByLabel('UI/Sessions/Bookmarking')
        return reason

    def TypeAndNodeValidationHook(self, idType, id):
        if macho.mode == 'server' and idType in ('allianceid', 'corpid'):
            machoNet = sm.GetService('machoNet')
            if machoNet.GetNodeID() != machoNet.GetNodeFromAddress(const.cluster.SERVICE_CHATX, id % 200):
                raise RuntimeError('Horrid session change called on incorrect node.  You must at very least perform this abomination on the right node.')

    def ProcessInventoryChange(self, items, change, isRemote, inventory2):
        """Translate inventory changes into session changes"""
        if macho.mode != 'server':
            return
        if isRemote:
            return
        if const.ixLocationID not in change and const.ixFlag not in change:
            return
        locationID = locationGroupID = None
        if const.ixLocationID in change:
            locationID = change[const.ixLocationID][1]
            if IsSolarSystem(locationID):
                locationGroupID = const.groupSolarSystem
            elif IsStation(locationID):
                locationGroupID = const.groupStation
        chars = {}
        for item in items:
            if item.categoryID == const.categoryShip and None not in (locationID, locationGroupID):
                inv2 = self.i2.GetInventory(locationID, locationGroupID)
                for i in inv2.SelectItems(item.itemID):
                    if i.groupID == const.groupCharacter:
                        chars[i.itemID] = self.GetSessionValuesFromItemID(item.itemID, inventory2, item)

            elif item.groupID == const.groupCharacter:
                if const.ixLocationID in change and item.customInfo == logConst.eventMovementUndock:
                    continue
                chars[item.itemID] = self.GetSessionValuesFromItemID(item.itemID, inventory2, item)

        if len(chars) == 0:
            return
        for charID, updateDict in chars.iteritems():
            for sess in base.FindSessions('charid', [charID]):
                sess.LogSessionHistory('Transmogrifying OnInventoryChange to SetAttributes')
                sess.SetAttributes(updateDict)
                sess.LogSessionHistory('Transmogrified OnInventoryChange to SetAttributes')

    def GetSessionValuesFromItemID(self, itemID, inventory2 = None, theItem = None):
        """Reverse-engineers a character item into session state values"""
        if itemID == const.locationAbstract:
            raise RuntimeError('Invalid argument, itemID cannot be 0')

        def GetItem(id):
            return sm.services['i2'].GetItemMx(id)

        updateDict = {'shipid': None,
         'stationid': None,
         'stationid2': None,
         'solarsystemid': None,
         'solarsystemid2': None,
         'regionid': None,
         'constellationid': None,
         'worldspaceid': None}
        solsysID = None
        while 1:
            if inventory2 is None:
                item = GetItem(itemID)
            elif theItem and theItem.itemID == itemID:
                item = theItem
            elif itemID < const.minPlayerItem:
                if IsStation(itemID):
                    station = self.stationSvc.GetStation(itemID)
                    updateDict['stationid'] = itemID
                    updateDict['stationid2'] = itemID
                    solsysID = station.solarSystemID
                    break
                else:
                    item = inventory2.InvGetItem(itemID)
            else:
                item = inventory2.InvGetItem(itemID, 1)
            if item.categoryID == const.categoryShip:
                updateDict['shipid'] = itemID
            elif item.groupID == const.groupStation:
                updateDict['stationid'] = itemID
                updateDict['stationid2'] = itemID
                updateDict['worldspaceid'] = itemID
                solsysID = item.locationID
                break
            elif item.groupID == const.groupWorldSpace:
                updateDict['worldspaceid'] = itemID
                locationID = item.locationID
                if not IsStation(locationID):
                    raise RuntimeError('Setting stationid2 = %s which is not a station!' % locationID)
                updateDict['stationid2'] = locationID
                station = self.stationSvc.GetStation(locationID)
                solsysID = station.solarSystemID
                break
            elif item.typeID == const.typeSolarSystem:
                solsysID = item.itemID
                updateDict['solarsystemid'] = itemID
                break
            elif item.locationID == const.locationAbstract:
                break
            itemID = item.locationID

        if solsysID is not None:
            primeditems = sm.services['i2'].__primeditems__
            if solsysID in primeditems:
                updateDict['solarsystemid2'] = solsysID
                updateDict['constellationid'] = primeditems[solsysID].locationID
                updateDict['regionid'] = primeditems[updateDict['constellationid']].locationID
        return updateDict

    def GetSessionValuesFromRowset(self, si):
        """
        Builds and returns session dict out of a rowset,
        Used when rebuilding a session from db
        """
        sessValues = {'allianceid': si.allianceID,
         'warfactionid': si.warFactionID,
         'corpid': si.corporationID,
         'hqID': si.hqID,
         'baseID': si.baseID,
         'rolesAtAll': si.roles,
         'rolesAtHQ': si.rolesAtHQ,
         'rolesAtBase': si.rolesAtBase,
         'rolesAtOther': si.rolesAtOther,
         'fleetid': None,
         'fleetrole': None,
         'fleetbooster': None,
         'wingid': None,
         'squadid': None,
         'shipid': si.shipID,
         'stationid': None,
         'solarsystemid': None,
         'regionid': None,
         'constellationid': None,
         'genderID': si.genderID,
         'bloodlineID': si.bloodlineID,
         'raceID': cfg.bloodlines.Get(si.bloodlineID).raceID,
         'corpAccountKey': si.corpAccountKey}
        if si.zoneid:
            sessValues['worldspaceid'] = si.zoneid
            sessValues['stationid2'] = si.stationID
            station = self.stationSvc.GetStation(si.stationID)
            sessValues['solarsystemid2'] = station.solarSystemID
        elif si.stationID:
            sessValues['stationid'] = si.stationID
            sessValues['stationid2'] = si.stationID
            sessValues['worldspaceid'] = si.stationID
            station = self.stationSvc.GetStation(si.stationID)
            sessValues['solarsystemid2'] = station.solarSystemID
        elif si.solarSystemID:
            sessValues['solarsystemid'] = si.solarSystemID
            sessValues['solarsystemid2'] = si.solarSystemID
        if 'solarsystemid2' in sessValues:
            if sessValues['solarsystemid2'] is not None:
                primeditems = sm.services['i2'].__primeditems__
                if sessValues['solarsystemid2'] in primeditems:
                    sessValues['constellationid'] = primeditems[sessValues['solarsystemid2']].locationID
                    sessValues['regionid'] = primeditems[sessValues['constellationid']].locationID
        return sessValues

    def GetInitialValuesFromCharID(self, charID):
        if macho.mode != 'server':
            return {}
        rs = self.dbcharacter.Characters_Session2(charID)
        si = rs[0]
        return self.GetSessionValuesFromRowset(si)

    def IsPlayerCharacter(self, charID):
        return IsCharacter(charID) and not IsNPC(charID)

    def GetSession(self, charID):
        s = base.FindSessions('charid', [charID])
        if not s:
            return None
        return s[0]

    def GetUserSession(self, userid):
        foundSessions = base.FindSessions('userid', [userid])
        if not foundSessions:
            return
        for foundSession in foundSessions:
            if foundSession.charid is None:
                return foundSession

    def GetCharacterSession(self, charid):
        s = base.FindSessions('charid', [charid])
        if not s:
            return None
        return s[0]

    def CreateCrestSession(self, userID, charID, details, sessionID, clientID):
        sessionInit = {'userid': userID,
         'userType': 13,
         'role': service.ROLE_PLAYER,
         'languageID': 'EN',
         'maxSessionTime': None,
         'inDetention': None}
        if charID:
            sess = self.GetCharacterSession(charID)
        elif userID:
            sess = self.GetUserSession(userID)
        else:
            raise RuntimeError("CreateCrestSession can't create session without identifiers")
        if sess:
            raise RuntimeError('CreateCrestSession asked to create an existing session. This is not supported')
        s = base.CreateSession(sessionID, const.session.SESSION_TYPE_CREST, role=details.pop('role'))
        sm.GetService('machoNet').RegisterSessionWithTransport(s, clientID)
        changes = {k:v for k, v in details.iteritems()}
        sessionInit['role'] |= s.role
        if charID:
            initVals = self.session.ConnectToSolServerService('sessionMgr').GetInitialValuesFromCharID(charID)
            sessionInit.update(initVals)
            sessionInit.update({'charid': charID})
        s.LogSessionHistory('Character/User authenticated implicitely via direct call to sessionMgr')
        s.SetAttributes(sessionInit)
        s.LogSessionHistory('Applying initial session attribute directly via direct call to sessionMgr')
        s.SetAttributes(changes)
        return s

    def _AddToSessionStatistics(self):
        """ EVE Override: Adds EVE/DUST-specific "virtual attributes" classifying sessions """
        base.SessionMgr._AddToSessionStatistics(self)
        eve_online = eve_trial = eve_crest = dust_online = dust_battle = dust_crest = 0
        for sess in base.sessionsBySID.itervalues():
            if sess.sessionType == const.session.SESSION_TYPE_GAME:
                if sess.userType == const.userTypeTrial:
                    eve_trial += 1
                elif sess.charid:
                    eve_online += 1
            elif sess.sessionType == const.session.SESSION_TYPE_CREST:
                if sess.userType <= const.minDustUserType:
                    eve_crest += 1
                elif sess.userType == const.userTypeDustBattleServer:
                    dust_battle += 1
                elif sess.charid:
                    dust_online += 1
                else:
                    dust_crest += 1

        self.sessionStatistics['EVE:Online'] = (eve_online, {None: eve_online})
        self.sessionStatistics['EVE:Trial'] = (eve_trial, {None: eve_trial})
        self.sessionStatistics['EVE:CREST'] = (eve_crest, {None: eve_crest})
        self.sessionStatistics['DUST:Online'] = (dust_online, {None: dust_online})
        self.sessionStatistics['DUST:Battle'] = (dust_battle, {None: dust_battle})
        self.sessionStatistics['DUST:User'] = (dust_crest, {None: dust_crest})


exports = {'base.GetCharLocation': GetCharLocation,
 'base.GetCharLocationEx': GetCharLocationEx,
 'base.IsLocationNode': IsLocationNode,
 'base.IsUndockingSessionChange': IsUndockingSessionChange}
