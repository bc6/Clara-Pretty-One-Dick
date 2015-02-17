#Embedded file name: eve/client/script/ui/services\facWarSvc.py
import carbonui.const as uiconst
import service
import blue
import util
import uiutil
import localization
import facwarCommon
import form
from eve.common.script.sys.rowset import IndexRowset

class FactionalWarfare(service.Service):
    __exportedcalls__ = {'IsEnemyCorporation': [],
     'JoinFactionAsAlliance': [],
     'JoinFactionAsCorporation': [],
     'JoinFactionAsCharacter': [],
     'LeaveFactionAsCorporation': [],
     'LeaveFactionAsAlliance': [],
     'WithdrawJoinFactionAsAlliance': [],
     'WithdrawJoinFactionAsCorporation': [],
     'WithdrawLeaveFactionAsAlliance': [],
     'WithdrawLeaveFactionAsCorporation': [],
     'GetFactionalWarStatus': [],
     'GetWarFactions': [],
     'GetCorporationWarFactionID': [],
     'GetFactionCorporations': [],
     'GetFactionMilitiaCorporation': [],
     'GetCharacterRankInfo': [],
     'GetEnemies': [],
     'GetStats_FactionInfo': [],
     'GetStats_Personal': [],
     'GetStats_Corp': [],
     'GetStats_Alliance': [],
     'GetStats_CorpPilots': [],
     'GetSystemsConqueredThisRun': [],
     'GetDistanceToEnemySystems': [],
     'GetMostDangerousSystems': [],
     'GetSystemStatus': [],
     'CheckForSafeSystem': [],
     'GetCurrentSystemVictoryPoints': [],
     'GetAllianceWarFactionID': []}
    __guid__ = 'svc.facwar'
    __servicename__ = 'facwar'
    __displayname__ = 'Factional Warfare'
    __notifyevents__ = ['OnNPCStandingChange',
     'ProcessSystemStatusChanged',
     'ProcessSessionChange',
     'OnSolarSystemLPChange',
     'OnSessionChanged']
    __exportedcalls__ = {'ShowRulesOfEngagementTab': [service.ROLE_IGB]}

    def __init__(self):
        service.Service.__init__(self)
        self.facWarSystemCount = {}
        self.warFactionByOwner = {}
        self.topStats = None
        self.statusBySystemID = {}
        self.remoteFacWarMgr = None
        self.solarSystemLPs = {}
        self.solarSystemVictoryPoints = None
        self.solarSystemVictoryPointThreshold = None
        self.FWSystems = None
        self.FWSystemOccupiers = None

    def Run(self, memStream = None):
        self.LogInfo('Starting Factional Warfare Svc')
        self.objectCaching = sm.GetService('objectCaching')

    @property
    def facWarMgr(self):
        if self.remoteFacWarMgr is None:
            self.remoteFacWarMgr = sm.RemoteSvc('facWarMgr')
        return self.remoteFacWarMgr

    def ProcessSystemStatusChanged(self, *args):
        """
            The 1st argument is number of victory points in this solarsystem
            The second argument is the victory point threshold in this solarsystem
        
            The third argument is expected to have 2 elements. The first one is a 2-tuple containing the new 
            system status (see GetSystemStatus()) as its first element. The second element is a
            possibly empty list of factionID this status applies to.
        
            The fourth argument is either None or a 2-tuple containing string and a dict which
            correspond to a msgId and associated dict to display to the user.
            In other words, encapsulating OnRemoteMessage calls from facWarMgr.
        """
        if args[3]:
            sm.ScatterEvent('OnRemoteMessage', args[3][0], args[3][1])
        self.LogInfo('ProcessSystemStatusChanged() called with stateinfo', args[0], args[1], args[2])
        self.solarSystemVictoryPoints = args[0]
        self.solarSystemVictoryPointThreshold = args[1]
        statusinfo = args[2]
        self.LogInfo('Updating state')
        self.statusBySystemID[session.solarsystemid2] = statusinfo[0]
        sm.GetService('infoPanel').UpdateFactionalWarfarePanel()
        sm.ScatterEvent('OnSystemStatusChanged')

    def ProcessSessionChange(self, isRemote, session, change):
        if 'solarsystemid' in change:
            lastSystem, newSystem = change['solarsystemid']
            if lastSystem and self.statusBySystemID.has_key(lastSystem):
                del self.statusBySystemID[lastSystem]
            if newSystem and self.statusBySystemID.has_key(newSystem):
                del self.statusBySystemID[newSystem]
            if newSystem in self.solarSystemLPs:
                self.solarSystemLPs = {}
                self.objectCaching.InvalidateCachedMethodCalls([('map', 'GetFacWarZoneInfo', (self.GetSystemOccupier(newSystem),))])

    def OnSolarSystemLPChange(self, oldpoints, newpoints):
        self.LogInfo('OnSolarSystemLPChange: ', oldpoints, newpoints)
        self.solarSystemLPs[session.solarsystemid2] = newpoints
        sm.GetService('infoPanel').UpdateFactionalWarfarePanel()

    def GetSolarSystemUpgradeLevel(self, solarsystemID):
        if solarsystemID in self.solarSystemLPs:
            points = self.solarSystemLPs[solarsystemID]
            thresholds = const.facwarSolarSystemUpgradeThresholds
            for i, threshold in enumerate(thresholds):
                if points < threshold:
                    return i

            return len(thresholds)
        else:
            factionID = self.GetSystemOccupier(solarsystemID)
            warZoneInfo = self.GetFacWarZoneInfo(factionID)
            return warZoneInfo.systemUpgradeLevel[solarsystemID]

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid2' in change:
            if session.solarsystemid2 in self.GetFacWarSystems():
                self.solarSystemVictoryPoints, self.solarSystemVictoryPointThreshold = self.facWarMgr.GetVictoryPointsAndThreshold()

    def IsEnemyCorporation(self, enemyID, factionID):
        """
            Determine whether a corporation is an enemy of a faction
        """
        return self.facWarMgr.IsEnemyCorporation(enemyID, factionID)

    def GetSystemsConqueredThisRun(self):
        """
            Return a list of (name,ID) tuples of systems which are scheduled 
            to change hands next downtime.
        """
        return self.facWarMgr.GetSystemsConqueredThisRun()

    def GetDistanceToEnemySystems(self):
        """
            returns an array of keyval's sorted by distance from current system where each system is 'occupied'
            by one of the current character's enemy factions. Each entry is in the following format:
            kv.solarSystemID, kv.occupierID, kv.jumJumps
            note: if you are in an enemy controlled system you will get that system as the first item
            note: systems that have changed hands during this run are not taken into account.
        """
        if session.warfactionid is None:
            return
        enemyFactions = self.GetEnemies(session.warfactionid)
        enemySystems = [ util.KeyVal(solarSystemID=k, occupierID=v, numJumps=0) for k, v in self.GetFacWarSystemsOccupiers().iteritems() if v in enemyFactions ]
        pathfinder = sm.GetService('clientPathfinderService')
        for s in enemySystems:
            s.numJumps = pathfinder.GetJumpCountFromCurrent(s.solarSystemID)
            blue.pyos.BeNice()

        enemySystems.sort(lambda x, y: cmp(x.numJumps, y.numJumps))
        return enemySystems

    def GetMostDangerousSystems(self):
        """
            Returns an array of keyval's sorted by number of kills in the last 24 hours where the victim is in factional warfare. 
            Each entry is in the following format: kv.solarSystemID, kv.numKills
            This list will have the same results as the map-mode: show militia kills for the last 24 hours 
            note: sm.RemoteSvc("map").GetHistory() is cached client-side for 15m and proxy for 5m
                  the actual data is written into the db on a kill no more than once every few minutes per system as dictated by
                  static settings ("Cache", "SystemKills-Minutes"), probably 5 minutes per system.
        """
        historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatFacWarKills, 24)
        dangerousSystems = []
        for each in historyDB:
            if each.value1 - each.value2 > 0:
                dangerousSystems.append(util.KeyVal(solarSystemID=each.solarSystemID, numKills=each.value1 - each.value2))

        dangerousSystems.sort(lambda x, y: cmp(y.numKills, x.numKills))
        return dangerousSystems

    def GetCorporationWarFactionID(self, corpID):
        """
            Get the war faction that the entity (char or corp) belongs to, or None if the entity is not (actively) in a faction
            May also be invoked with entity as a faction, in which case it simply returns the faction ID
        """
        if util.IsNPC(corpID):
            for factionID, militiaCorpID in self.GetWarFactions().iteritems():
                if militiaCorpID == corpID:
                    return factionID

            return None
        ret = self.facWarMgr.GetCorporationWarFactionID(corpID)
        if not ret:
            return None
        return ret

    def GetFactionCorporations(self, factionID):
        """
            Get the corporations that belong to the faction
        """
        return self.facWarMgr.GetFactionCorporations(factionID)

    def GetFacWarSystems(self):
        """
            returns a list of all factional warfare systems
        """
        if self.FWSystems is None:
            self.FWSystems = self.facWarMgr.GetFacWarSystems()
        return self.FWSystems

    def GetFacWarSystemsOccupiers(self):
        """
            returns a dict with all facwar systems, where the the keys are solarsystems and
            the value the factionID of the occupier
        """
        if self.FWSystemOccupiers is None:
            self.FWSystemOccupiers = self.facWarMgr.GetAllSystemOccupiers()
        return self.FWSystemOccupiers

    def GetAllianceWarFactionID(self, allianceID):
        return self.facWarMgr.GetAllianceWarFactionID(allianceID)

    def GetFactionIDByRaceID(self, raceID):
        if raceID == const.raceCaldari:
            return const.factionCaldariState
        if raceID == const.raceAmarr:
            return const.factionAmarrEmpire
        if raceID == const.raceGallente:
            return const.factionGallenteFederation
        if raceID == const.raceMinmatar:
            return const.factionMinmatarRepublic

    def GetSolarSystemsOccupiedByFactions(self, factionIDs):
        """
            Get all solar systems currently occupied by any of the faction IDs passed in
        """
        ret = {}
        systems = self.GetFacWarSystemsOccupiers()
        for systemID, occupierID in systems.iteritems():
            if occupierID in factionIDs:
                ret[systemID] = occupierID

        return ret

    def GetSystemOccupier(self, solarSystemID):
        """
            Get the occupier of a factionalwarfare system, returns None if this is not a facwar system
        """
        try:
            return self.GetFacWarSystemsOccupiers()[solarSystemID]
        except KeyError:
            return None

    def IsFacWarSystem(self, solarSystemID):
        return solarSystemID in self.GetFacWarSystems()

    def GetFactionWars(self, ownerID):
        factionWars = {}
        warFactionID = self.GetCorporationWarFactionID(ownerID)
        if warFactionID:
            factions = [ each for each in self.GetWarFactions() ]
            factionWars = IndexRowset(['warID',
             'declaredByID',
             'againstID',
             'timeDeclared',
             'timeFinished',
             'retracted',
             'retractedBy',
             'billID',
             'mutual'], [], 'warID')
            for i, faction in enumerate(factions):
                if facwarCommon.IsEnemyFaction(faction, warFactionID):
                    factionWars[i * -1] = [None,
                     faction,
                     warFactionID,
                     None,
                     None,
                     None,
                     None,
                     None,
                     True]

        return factionWars

    def GetFactionMilitiaCorporation(self, factionID):
        """
            Get the militia corporation for the faction
        """
        ret = self.facWarMgr.GetFactionMilitiaCorporation(factionID)
        if not ret:
            return None
        return ret

    def GetFacWarZoneInfo(self, factionID):
        return sm.RemoteSvc('map').GetFacWarZoneInfo(factionID)

    def GetSystemUpgradeLevelBenefits(self, systemUpgradeLevel):
        """
            Returns the upgrade types and values for a given system upgrade level, ranging from 0 to 5
        """
        return facwarCommon.BENEFITS_BY_LEVEL.get(systemUpgradeLevel, [])

    def GetActiveFactionID(self):
        """ Returns a sensible factionID for the UI for current character, depending location and state """
        if session.warfactionid:
            return session.warfactionid
        factionID = self.CheckStationElegibleForMilitia()
        if factionID:
            return factionID
        occupierID = self.GetSystemOccupier(session.solarsystemid2)
        if occupierID:
            return occupierID
        return self.GetFactionIDByRaceID(session.raceID)

    def GetSystemCaptureStatus(self, systemID):
        threshold, victoryPoints, occupier = sm.GetService('starmap').GetFacWarData()[systemID]
        if systemID == session.solarsystemid2:
            if self.GetSystemStatus() == const.contestionStateCaptured:
                return facwarCommon.STATE_CAPTURED
        else:
            capturedSystems = self.GetFacWarZoneInfo(self.GetActiveFactionID()).capturedSystems
            if systemID in capturedSystems:
                return facwarCommon.STATE_CAPTURED
        if victoryPoints == 0:
            return facwarCommon.STATE_STABLE
        if victoryPoints < threshold:
            return facwarCommon.STATE_CONTESTED
        return facwarCommon.STATE_VULNERABLE

    def GetSystemCaptureStatusTxt(self, systemID):
        state = self.GetSystemCaptureStatus(systemID)
        if state == facwarCommon.STATE_STABLE:
            return localization.GetByLabel('UI/FactionWarfare/StatusStable')
        if state == facwarCommon.STATE_CONTESTED:
            return localization.GetByLabel('UI/FactionWarfare/StatusContested', num='%04.1f' % self.GetSystemContestedPercentage(systemID))
        if state == facwarCommon.STATE_VULNERABLE:
            return localization.GetByLabel('UI/FactionWarfare/StatusVulnerable')
        if state == facwarCommon.STATE_CAPTURED:
            return '<color=red>' + localization.GetByLabel('UI/Neocom/SystemLost')

    def GetSystemContestedPercentage(self, systemID):
        threshold, victoryPoints, occupier = sm.GetService('starmap').GetFacWarData()[systemID]
        percent = victoryPoints / float(threshold) * 100
        if percent >= 100.0:
            percent = 100.0
        elif percent > 99.9:
            percent = 99.9
        return percent

    def GetCurrentSystemVictoryPoints(self):
        return self.solarSystemVictoryPoints

    def GetCurrentSystemVictoryPointThreshold(self):
        if self.solarSystemVictoryPointThreshold is None:
            _, self.solarSystemVictoryPointThreshold = self.facWarMgr.GetVictoryPointsAndThreshold()
        return self.solarSystemVictoryPointThreshold

    def GetCurrentSystemEffectOfHeldDistricts(self):
        """ Returns the amount the current system VP threshold is being affected by held districts as a percentage """
        base = float(const.facwarBaseVictoryPointsThreshold)
        curr = float(self.GetCurrentSystemVictoryPointThreshold())
        return (curr - base) / base * 100

    def JoinFactionAsCharacter(self, factionID, warfactionid):
        """
            Request from the current character to join a faction (moving him to the corresponding militia corp, effective immediately if accepted)
        """
        if warfactionid:
            alreadyInMilitiaLabel = localization.GetByLabel('UI/FactionWarfare/AlreadyInMilitia')
            eve.Message('CustomInfo', {'info': alreadyInMilitiaLabel})
            return
        ownerName = cfg.eveowners.Get(factionID).name
        headerLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationHeader')
        bodyLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationQuestionPlayer', factionName=ownerName)
        ret = eve.Message('CustomQuestion', {'header': headerLabel,
         'question': bodyLabel}, uiconst.YESNO)
        if ret == uiconst.ID_YES:
            sm.GetService('sessionMgr').PerformSessionChange('corp.joinmilitia', self.facWarMgr.JoinFactionAsCharacter, factionID)
            invalidate = [('facWarMgr', 'GetMyCharacterRankInfo', ()),
             ('facWarMgr', 'GetMyCharacterRankOverview', ()),
             ('facWarMgr', 'GetFactionalWarStatus', ()),
             ('corporationSvc', 'GetEmploymentRecord', (session.charid,))]
            self.objectCaching.InvalidateCachedMethodCalls(invalidate)

    def JoinFactionAsAlliance(self, factionID, warfactionid):
        """
            Request from the current character to enlist his alliance in a faction (must be director in the executor corp, becomes active on next startup)
        """
        ownerName = cfg.eveowners.Get(factionID).name
        headerLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationHeader')
        bodyLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationQuestionAlliance', factionName=ownerName)
        if warfactionid:
            alreadyInMilitiaLabel = localization.GetByLabel('UI/FactionWarfare/AlreadyInMilitia')
            eve.Message('CustomInfo', {'info': alreadyInMilitiaLabel})
            return
        ret = eve.Message('CustomQuestion', {'header': headerLabel,
         'question': bodyLabel}, uiconst.YESNO)
        if ret == uiconst.ID_YES:
            self.facWarMgr.JoinFactionAsAlliance(factionID)
            self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])
            sm.ScatterEvent('OnJoinMilitia')

    def JoinFactionAsCorporation(self, factionID, warfactionid):
        """
            Request from the current character to enlist his corp in a faction (must be director, becomes active on next startup)
        """
        ownerName = cfg.eveowners.Get(factionID).name
        headerLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationHeader')
        bodyLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationQuestionCorp', factionName=ownerName)
        if warfactionid:
            alreadyInMilitiaLabel = localization.GetByLabel('UI/FactionWarfare/AlreadyInMilitia')
            eve.Message('CustomInfo', {'info': alreadyInMilitiaLabel})
            return
        ret = eve.Message('CustomQuestion', {'header': headerLabel,
         'question': bodyLabel}, uiconst.YESNO)
        if ret == uiconst.ID_YES:
            self.facWarMgr.JoinFactionAsCorporation(factionID)
            self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])
            sm.ScatterEvent('OnJoinMilitia')

    def LeaveFactionAsAlliance(self, factionID):
        """
            Request from the current alliance to leave a faction (becomes active on next startup)
        """
        self.facWarMgr.LeaveFactionAsAlliance(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def LeaveFactionAsCorporation(self, factionID):
        """
            Request from the current corp to leave a faction (becomes active on next startup)
        """
        self.facWarMgr.LeaveFactionAsCorporation(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawJoinFactionAsAlliance(self, factionID):
        """
            Withdraw a request to join a faction from the current corp
        """
        self.facWarMgr.WithdrawJoinFactionAsAlliance(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawJoinFactionAsCorporation(self, factionID):
        """
            Withdraw a request to join a faction from the current corp
        """
        self.facWarMgr.WithdrawJoinFactionAsCorporation(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawLeaveFactionAsAlliance(self, factionID):
        """
            Withdraw a request to leave a faction from the current corp
        """
        self.facWarMgr.WithdrawLeaveFactionAsAlliance(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawLeaveFactionAsCorporation(self, factionID):
        """
            Withdraw a request to leave a faction from the current corp
        """
        self.facWarMgr.WithdrawLeaveFactionAsCorporation(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def GetFactionalWarStatus(self):
        """
            Get the current corp's factional warfare status. Only directors or CEOs get info
            pending requests, other members only see active status. Returns a keyval object
            where if result.factionID is not None, then result.status is one of: 
            [const.facwarCorporationJoining, const.facwarCorporationActive, const.facwarCorporationLeaving]
        """
        return self.facWarMgr.GetFactionalWarStatus()

    def GetWarFactions(self):
        """
            Get all the factions envolved in factional warfare
        """
        return self.facWarMgr.GetWarFactions()

    def GetCharacterRankInfo(self, charID, corpID = None):
        """
            Returns the characters factionID, currentRank (int) and highestRank ever gained (int) from faction if he is fw flagged otherwise None
        """
        if corpID is None or self.GetCorporationWarFactionID(corpID) is not None:
            if charID == session.charid:
                return self.facWarMgr.GetMyCharacterRankInfo()
            else:
                return self.facWarMgr.GetCharacterRankInfo(charID)

    def GetCharacterRankOverview(self, charID):
        """
            Returns the character factionId, currentRank and highestRank from all factions that the players has worked for
        """
        if not charID == session.charid:
            return None
        return self.facWarMgr.GetMyCharacterRankOverview()

    def RefreshCorps(self):
        return self.facWarMgr.RefreshCorps()

    def OnNPCStandingChange(self, fromID, newStanding, oldStanding):
        """
            This notification is sent from the standing service if a NPC standing change occured.
            If the standing change was from the militia corp then we compare the new standing with
            the old rank and if rank change seems to be in order then we ask the server.
        """
        if fromID == self.GetFactionMilitiaCorporation(session.warfactionid):
            oldrank = self.GetCharacterRankInfo(session.charid).currentRank
            if oldrank != min(max(int(newStanding), 0), 9):
                newrank = self.facWarMgr.CheckForRankChange()
                if newrank is not None and oldrank != newrank:
                    self.DoOnRankChange(oldrank, newrank)
        invalidate = [('facWarMgr', 'GetMyCharacterRankInfo', ()), ('facWarMgr', 'GetMyCharacterRankOverview', ())]
        self.objectCaching.InvalidateCachedMethodCalls(invalidate)

    def DoOnRankChange(self, oldrank, newrank):
        messageID = 'RankGained' if newrank > oldrank else 'RankLost'
        rankLabel, rankDescription = self.GetRankLabel(session.warfactionid, newrank)
        try:
            eve.Message(messageID, {'rank': rankLabel})
        except:
            sys.exc_clear()

        sm.ScatterEvent('OnRankChange', oldrank, newrank)

    def GetEnemies(self, factionID):
        """
            returns a list of the factions enemies
        """
        warFactions = self.GetWarFactions()
        enemies = []
        for each in warFactions.iterkeys():
            if facwarCommon.IsEnemyFaction(factionID, each):
                enemies.append(each)

        return enemies

    def GetStats_FactionInfo(self):
        """
            Returns a dictionary of keyval items. Dictionary key is factionid, keyval items
            have totalMembersCount, militiaMembersCount, corporationsCount and systemsCount
        """
        return self.facWarMgr.GetStats_FactionInfo()

    def GetStats_Personal(self):
        """
            Returns the header and data below :P
        """
        header = ['you', 'top', 'all']
        data = {'killsY': {'you': 0,
                    'top': 0,
                    'all': 0},
         'killsLW': {'you': 0,
                     'top': 0,
                     'all': 0},
         'killsTotal': {'you': 0,
                        'top': 0,
                        'all': 0},
         'vpY': {'you': 0,
                 'top': 0,
                 'all': 0},
         'vpLW': {'you': 0,
                  'top': 0,
                  'all': 0},
         'vpTotal': {'you': 0,
                     'top': 0,
                     'all': 0}}
        if not self.topStats:
            self.topStats = self.facWarMgr.GetStats_TopAndAllKillsAndVPs()
        for k in ('killsY', 'killsLW', 'killsTotal', 'vpY', 'vpLW', 'vpTotal'):
            data[k]['top'] = self.topStats[0][const.groupCharacter][k]
            data[k]['all'] = self.topStats[1][const.groupCharacter][k]

        for k, v in self.facWarMgr.GetStats_Character().items():
            data[k]['you'] = v

        return {'header': header,
         'data': data}

    def GetStats_Corp(self, corpID):
        """
            Behaves exactly like GetStats_Personal
        """
        header = ['your', 'top', 'all']
        data = {'killsY': {'your': 0,
                    'top': 0,
                    'all': 0},
         'killsLW': {'your': 0,
                     'top': 0,
                     'all': 0},
         'killsTotal': {'your': 0,
                        'top': 0,
                        'all': 0},
         'vpY': {'your': 0,
                 'top': 0,
                 'all': 0},
         'vpLW': {'your': 0,
                  'top': 0,
                  'all': 0},
         'vpTotal': {'your': 0,
                     'top': 0,
                     'all': 0}}
        if not self.topStats:
            self.topStats = self.facWarMgr.GetStats_TopAndAllKillsAndVPs()
        for k in ('killsY', 'killsLW', 'killsTotal', 'vpY', 'vpLW', 'vpTotal'):
            data[k]['top'] = self.topStats[0][const.groupCorporation][k]
            data[k]['all'] = self.topStats[1][const.groupCorporation][k]

        for k, v in self.facWarMgr.GetStats_Corp().items():
            data[k]['your'] = v

        return {'header': header,
         'data': data}

    def GetStats_Alliance(self, allianceID):
        """
            Behaves exactly like GetStats_Corp
        """
        header = ['your', 'top', 'all']
        data = {'killsY': {'your': 0,
                    'top': 0,
                    'all': 0},
         'killsLW': {'your': 0,
                     'top': 0,
                     'all': 0},
         'killsTotal': {'your': 0,
                        'top': 0,
                        'all': 0},
         'vpY': {'your': 0,
                 'top': 0,
                 'all': 0},
         'vpLW': {'your': 0,
                  'top': 0,
                  'all': 0},
         'vpTotal': {'your': 0,
                     'top': 0,
                     'all': 0}}
        if not self.topStats:
            self.topStats = self.facWarMgr.GetStats_TopAndAllKillsAndVPs()
        for k in ('killsY', 'killsLW', 'killsTotal', 'vpY', 'vpLW', 'vpTotal'):
            data[k]['top'] = self.topStats[0][const.groupAlliance][k]
            data[k]['all'] = self.topStats[1][const.groupAlliance][k]

        for k, v in self.facWarMgr.GetStats_Alliance().items():
            data[k]['your'] = v

        return {'header': header,
         'data': data}

    def GetStats_Militia(self):
        """
            returns a dictionary with the following keys:
                header
                data
                
            where header is a key to a list, and data a key to a dictionary
        
                header = [500001, 500002, 500003, 500004] 
        
                data is a dictionary with the following keys:
                    killsY
                    killsLW
                    killsTotal
                    vpY
                    vpLW
                    vpTotal
        
                each of them is a key to a dictionary
                {500001:X, 500002:Y, 500003:Z, 500004:A}  
        """
        return self.facWarMgr.GetStats_Militia()

    def GetStats_CorpPilots(self):
        return self.facWarMgr.GetStats_CorpPilots()

    def GetStats_Systems(self):
        """
            returns a list with dictionaries 
                [ {"solarsystemID":X,  "timeWon":Y, "occupierID":Z}, ... etc...]                
        """
        systemsThatWillSwitchNextDownTime = self.GetSystemsConqueredThisRun()
        cfg.evelocations.Prime([ d['solarsystemID'] for d in systemsThatWillSwitchNextDownTime ])
        cfg.eveowners.Prime([ d['occupierID'] for d in systemsThatWillSwitchNextDownTime ])
        tempList = []
        for each in systemsThatWillSwitchNextDownTime:
            tempList.append((each.get('taken'), each))

        systemsThatWillSwitchNextDownTime = uiutil.SortListOfTuples(tempList, reverse=1)
        return systemsThatWillSwitchNextDownTime

    def CheckOwnerInFaction(self, ownerID, factionID = None):
        factions = [ each for each in self.GetWarFactions() ]
        if not self.warFactionByOwner.has_key(ownerID):
            faction = sm.GetService('faction').GetFaction(ownerID)
            if faction and faction in factions:
                self.warFactionByOwner[ownerID] = faction
        return self.warFactionByOwner.get(ownerID, None)

    def GetSystemStatus(self):
        """
            Gets the conflict status for this sessions solarsystem.
            Returns:
              0 for  All-Is-Quiet,-Nothing-To-See,-Move-Along
              1 for  Contested (some faction has victory points in the system)
              2 for  Vulnerable (the control bunker in the system can be shot at by members of 'factionID')
              3 for  Lost (system bunker has been captured this run)
        
              We should use solarsystemid2, solarsystemid is not always present in the session
        """
        if self.statusBySystemID.has_key(session.solarsystemid2):
            self.LogInfo('GetSystemStatus: Returning cached status:', self.statusBySystemID[session.solarsystemid2])
            return self.statusBySystemID[session.solarsystemid2]
        status = self.facWarMgr.GetSystemStatus(session.solarsystemid2)
        self.statusBySystemID[session.solarsystemid2] = status
        self.LogInfo('GetSystemStatus: Returning status from server:', status)
        return status

    def CheckForSafeSystem(self, stationItem, factionID, solarSystemID = None):
        """
            Check for a safe system, if the owner of the station is currently in a solarsystem
            that is owned (not occupied, but sovereign owned) by an enemy faction, return False
            if it's not safe, return True if it's "safe".
            Only do this check for high sec, as there is no faction police in low sec.
        """
        ss = sm.GetService('map').GetSecurityClass(solarSystemID or session.solarsystemid2)
        if ss != const.securityClassHighSec:
            return True
        fosi = sm.GetService('faction').GetFaction(stationItem.ownerID)
        if fosi is None:
            return True
        foss = sm.GetService('faction').GetFactionOfSolarSystem(solarSystemID or session.solarsystemid2)
        eof = self.GetEnemies(factionID)
        if foss in eof:
            return False
        return True

    def CheckStationElegibleForMilitia(self):
        """
            station is elegible for militia button when:
            - currently in facwar
            - station's owner is affiliated with a faction at war
        """
        if session.warfactionid:
            return session.warfactionid
        if not session.stationid2:
            return False
        ownerID = eve.stationItem.ownerID
        if ownerID:
            check = self.CheckOwnerInFaction(ownerID)
            if check is not None:
                return check
        return False

    def GetRankLabel(self, factionID, rank):
        rank = min(9, rank)
        rankLabel, rankDescription = ('', '')
        if rank < 0:
            rankLabel = localization.GetByLabel('UI/FactionWarfare/Ranks/NoRank')
            rankDescription = ''
        else:
            rankPath, descPath = RankLabelsByFactionID.get((factionID, rank), ('UI/FactionWarfare/Ranks/NoRank', 'UI/FactionWarfare/Ranks/NoRank'))
            rankLabel = localization.GetByLabel(rankPath)
            rankDescription = localization.GetByLabel(descPath)
        return (rankLabel, rankDescription)

    def GetSolarSystemLPs(self):
        if not self.IsFacWarSystem(session.solarsystemid2):
            return 0
        if session.solarsystemid2 not in self.solarSystemLPs:
            self.solarSystemLPs[session.solarsystemid2] = self.facWarMgr.GetSolarSystemLPs()
        return self.solarSystemLPs[session.solarsystemid2]

    def DonateLPsToSolarSystem(self, pointsDonated, pointsToIhub):
        pointsDonated = max(pointsDonated, const.facwarMinLPDonation)
        militiaCorpID = self.GetFactionMilitiaCorporation(session.warfactionid)
        if militiaCorpID is None:
            raise RuntimeError("Don't know the militia corp for faction", session.warfactionid)
        pointsWithCorp = sm.GetService('lpstore').GetMyLPs(militiaCorpID)
        if pointsDonated > pointsWithCorp:
            militiaName = cfg.eveowners.Get(militiaCorpID).ownerName
            raise UserError('FacWarCantDonateSoMuch', {'militiaName': militiaName,
             'points': pointsWithCorp})
        solarSystemLPs = self.GetSolarSystemLPs()
        if pointsToIhub + solarSystemLPs > const.facwarSolarSystemMaxLPPool:
            militiaName = cfg.eveowners.Get(militiaCorpID).ownerName
            maxPointsToAdd = const.facwarSolarSystemMaxLPPool - solarSystemLPs
            raise UserError('FacWarPoolOverloaded', {'militiaName': militiaName,
             'points': maxPointsToAdd})
        return self.facWarMgr.DonateLPsToSolarSystem(pointsDonated, pointsToIhub)

    def ShowRulesOfEngagementTab(self):
        wnd = form.MilitiaWindow.GetIfOpen()
        if wnd:
            wnd.ShowRulesOfEngagementTab()


RankLabelsByFactionID = {(const.factionCaldariState, 0): ('UI/FactionWarfare/Ranks/RankCaldari0', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari0'),
 (const.factionCaldariState, 1): ('UI/FactionWarfare/Ranks/RankCaldari1', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari1'),
 (const.factionCaldariState, 2): ('UI/FactionWarfare/Ranks/RankCaldari2', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari2'),
 (const.factionCaldariState, 3): ('UI/FactionWarfare/Ranks/RankCaldari3', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari3'),
 (const.factionCaldariState, 4): ('UI/FactionWarfare/Ranks/RankCaldari4', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari4'),
 (const.factionCaldariState, 5): ('UI/FactionWarfare/Ranks/RankCaldari5', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari5'),
 (const.factionCaldariState, 6): ('UI/FactionWarfare/Ranks/RankCaldari6', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari6'),
 (const.factionCaldariState, 7): ('UI/FactionWarfare/Ranks/RankCaldari7', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari7'),
 (const.factionCaldariState, 8): ('UI/FactionWarfare/Ranks/RankCaldari8', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari8'),
 (const.factionCaldariState, 9): ('UI/FactionWarfare/Ranks/RankCaldari9', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari9'),
 (const.factionMinmatarRepublic, 0): ('UI/FactionWarfare/Ranks/RankMinmatar0', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar0'),
 (const.factionMinmatarRepublic, 1): ('UI/FactionWarfare/Ranks/RankMinmatar1', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar1'),
 (const.factionMinmatarRepublic, 2): ('UI/FactionWarfare/Ranks/RankMinmatar2', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar2'),
 (const.factionMinmatarRepublic, 3): ('UI/FactionWarfare/Ranks/RankMinmatar3', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar3'),
 (const.factionMinmatarRepublic, 4): ('UI/FactionWarfare/Ranks/RankMinmatar4', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar4'),
 (const.factionMinmatarRepublic, 5): ('UI/FactionWarfare/Ranks/RankMinmatar5', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar5'),
 (const.factionMinmatarRepublic, 6): ('UI/FactionWarfare/Ranks/RankMinmatar6', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar6'),
 (const.factionMinmatarRepublic, 7): ('UI/FactionWarfare/Ranks/RankMinmatar7', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar7'),
 (const.factionMinmatarRepublic, 8): ('UI/FactionWarfare/Ranks/RankMinmatar8', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar8'),
 (const.factionMinmatarRepublic, 9): ('UI/FactionWarfare/Ranks/RankMinmatar9', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar9'),
 (const.factionAmarrEmpire, 0): ('UI/FactionWarfare/Ranks/RankAmarr0', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr0'),
 (const.factionAmarrEmpire, 1): ('UI/FactionWarfare/Ranks/RankAmarr1', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr1'),
 (const.factionAmarrEmpire, 2): ('UI/FactionWarfare/Ranks/RankAmarr2', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr2'),
 (const.factionAmarrEmpire, 3): ('UI/FactionWarfare/Ranks/RankAmarr3', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr3'),
 (const.factionAmarrEmpire, 4): ('UI/FactionWarfare/Ranks/RankAmarr4', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr4'),
 (const.factionAmarrEmpire, 5): ('UI/FactionWarfare/Ranks/RankAmarr5', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr5'),
 (const.factionAmarrEmpire, 6): ('UI/FactionWarfare/Ranks/RankAmarr6', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr6'),
 (const.factionAmarrEmpire, 7): ('UI/FactionWarfare/Ranks/RankAmarr7', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr7'),
 (const.factionAmarrEmpire, 8): ('UI/FactionWarfare/Ranks/RankAmarr8', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr8'),
 (const.factionAmarrEmpire, 9): ('UI/FactionWarfare/Ranks/RankAmarr9', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr9'),
 (const.factionGallenteFederation, 0): ('UI/FactionWarfare/Ranks/RankGallente0', 'UI/FactionWarfare/Ranks/RankDescriptionGallente0'),
 (const.factionGallenteFederation, 1): ('UI/FactionWarfare/Ranks/RankGallente1', 'UI/FactionWarfare/Ranks/RankDescriptionGallente1'),
 (const.factionGallenteFederation, 2): ('UI/FactionWarfare/Ranks/RankGallente2', 'UI/FactionWarfare/Ranks/RankDescriptionGallente2'),
 (const.factionGallenteFederation, 3): ('UI/FactionWarfare/Ranks/RankGallente3', 'UI/FactionWarfare/Ranks/RankDescriptionGallente3'),
 (const.factionGallenteFederation, 4): ('UI/FactionWarfare/Ranks/RankGallente4', 'UI/FactionWarfare/Ranks/RankDescriptionGallente4'),
 (const.factionGallenteFederation, 5): ('UI/FactionWarfare/Ranks/RankGallente5', 'UI/FactionWarfare/Ranks/RankDescriptionGallente5'),
 (const.factionGallenteFederation, 6): ('UI/FactionWarfare/Ranks/RankGallente6', 'UI/FactionWarfare/Ranks/RankDescriptionGallente6'),
 (const.factionGallenteFederation, 7): ('UI/FactionWarfare/Ranks/RankGallente7', 'UI/FactionWarfare/Ranks/RankDescriptionGallente7'),
 (const.factionGallenteFederation, 8): ('UI/FactionWarfare/Ranks/RankGallente8', 'UI/FactionWarfare/Ranks/RankDescriptionGallente8'),
 (const.factionGallenteFederation, 9): ('UI/FactionWarfare/Ranks/RankGallente9', 'UI/FactionWarfare/Ranks/RankDescriptionGallente9')}
