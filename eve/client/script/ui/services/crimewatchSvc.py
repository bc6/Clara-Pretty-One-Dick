#Embedded file name: eve/client/script/ui/services\crimewatchSvc.py
import service
import util
import moniker
import uicls
import uthread
import blue
from crimewatch.const import targetGroupsWithSuspectPenaltyInHighSec
from crimewatch.util import IsItemFreeForAggression

class CrimewatchService(service.Service):
    """
    Manages crimewatch related state and interactions
    Performs client-side updates to combat timers.
    This is a peer service to the combatTimers crimewatch component
    Keeps the safety level settings
    """
    __guid__ = 'svc.crimewatchSvc'
    __dependencies__ = ['michelle',
     'godma',
     'war',
     'facwar',
     'corp']
    __startupdependencies__ = []
    __notifyevents__ = ['ProcessSessionChange',
     'OnWeaponsTimerUpdate',
     'OnPvpTimerUpdate',
     'OnNpcTimerUpdate',
     'OnCriminalTimerUpdate',
     'OnSystemCriminalFlagUpdates',
     'OnCrimewatchEngagementCreated',
     'OnCrimewatchEngagementEnded',
     'OnCrimewatchEngagementStartTimeout',
     'OnCrimewatchEngagementStopTimeout',
     'OnDuelChallenge',
     'OnSecurityStatusUpdate',
     'OnGodmaItemChange',
     'OnJumpTimersUpdated',
     'OnCorpAggressionSettingsChange']

    def Run(self, *args):
        service.Service.Run(self, *args)
        self.weaponsTimerState = None
        self.weaponsTimerExpiry = None
        self.pvpTimerState = None
        self.pvpTimerExpiry = None
        self.npcTimerState = None
        self.npcTimerExpiry = None
        self.criminalTimerState = None
        self.criminalTimerExpiry = None
        self.criminalFlagsByCharID = {}
        self.myEngagements = {}
        self.safetyLevel = const.shipSafetyLevelFull
        self.duelWindow = None
        self.mySecurityStatus = None
        self.jumpTimers = None
        self.corpAggressionSettings = None

    def ProcessSessionChange(self, isRemote, session, change):
        if 'locationid' in change:
            myCombatTimers, myEngagements, flaggedCharacters, safetyLevel = moniker.CharGetCrimewatchLocation().GetClientStates()
            self.LogInfo('ProcessSessionChange', myCombatTimers, myEngagements, flaggedCharacters, safetyLevel)
            self.safetyLevel = safetyLevel
            weaponTimerState, pvpTimerState, npcTimerState, criminalTimerState = myCombatTimers
            self.weaponsTimerState, self.weaponsTimerExpiry = weaponTimerState
            self.pvpTimerState, self.pvpTimerExpiry = pvpTimerState
            self.npcTimerState, self.npcTimerExpiry = npcTimerState
            self.criminalTimerState, self.criminalTimerExpiry = criminalTimerState
            self.myEngagements = myEngagements
            sm.ScatterEvent('OnCombatTimersUpdated')
            criminals, suspects = flaggedCharacters
            self.criminalFlagsByCharID.clear()
            self.UpdateSuspectsAndCriminals(criminals, suspects)
            if self.duelWindow is not None:
                self.duelWindow.Close()
                self.duelWindow = None
        if 'corpid' in change:
            self.RefreshCorpAggressionSettings()

    def GetSlimItemDataForCharID(self, charID):
        """
        This is a utility function aimed at providing the engagement UI with display data on engaged targets
        TODO: this could use some optimization and caching
        """
        slimItem = None
        if session.solarsystemid is not None:
            ballpark = self.michelle.GetBallpark()
            for _slimItem in ballpark.slimItems.itervalues():
                if _slimItem.charID == charID:
                    slimItem = _slimItem
                    break

        if slimItem is None:
            pubInfo = sm.RemoteSvc('charMgr').GetPublicInfo(charID)
            info = cfg.eveowners.Get(charID)
            slimItem = util.KeyVal()
            slimItem.charID = charID
            slimItem.typeID = info.typeID
            slimItem.corpID = pubInfo.corporationID
            slimItem.warFactionID = sm.GetService('facwar').GetCorporationWarFactionID(pubInfo.corporationID)
            slimItem.allianceID = sm.GetService('corp').GetCorporation(pubInfo.corporationID).allianceID
            slimItem.securityStatus = self.GetCharacterSecurityStatus(charID)
            slimItem.groupID = const.groupCharacter
            slimItem.categoryID = const.categoryOwner
            slimItem.itemID = None
            slimItem.ownerID = charID
        return slimItem

    def UpdateSuspectsAndCriminals(self, criminals, suspects, decriminalizedCharIDs = ()):
        """
        criminals are ids for new criminal characters
        suspects are ids for new suspect characters
        decriminalizedCharIDs are ids for characters that had criminal or suspect status revoked
        """
        for charID in decriminalizedCharIDs:
            try:
                del self.criminalFlagsByCharID[charID]
            except KeyError:
                pass

        for charID in criminals:
            self.criminalFlagsByCharID[charID] = const.criminalTimerStateActiveCriminal

        for charID in suspects:
            self.criminalFlagsByCharID[charID] = const.criminalTimerStateActiveSuspect

        criminalizedCharIDs = set(self.criminalFlagsByCharID.iterkeys())
        sm.ScatterEvent('OnSuspectsAndCriminalsUpdate', criminalizedCharIDs, set(decriminalizedCharIDs))

    def OnWeaponsTimerUpdate(self, state, expiryTime):
        self.LogInfo('OnWeaponsTimerUpdate', state, expiryTime)
        self.weaponsTimerState = state
        self.weaponsTimerExpiry = expiryTime

    def OnPvpTimerUpdate(self, state, expiryTime):
        self.LogInfo('OnPvpTimerUpdate', state, expiryTime)
        self.pvpTimerState = state
        self.pvpTimerExpiry = expiryTime

    def OnNpcTimerUpdate(self, state, expiryTime):
        self.LogInfo('OnNpcTimerUpdate', state, expiryTime)
        self.npcTimerState = state
        self.npcTimerExpiry = expiryTime

    def OnCriminalTimerUpdate(self, state, expiryTime):
        self.LogInfo('OnCriminalTimerUpdate', state, expiryTime)
        self.criminalTimerState = state
        self.criminalTimerExpiry = expiryTime

    def OnSystemCriminalFlagUpdates(self, newIdles, newSuspects, newCriminals):
        self.LogInfo('OnSystemCriminalFlagUpdates', newIdles, newSuspects, newCriminals)
        self.UpdateSuspectsAndCriminals(newCriminals, newSuspects, newIdles)

    def OnCrimewatchEngagementCreated(self, otherCharId, timeout):
        self.LogInfo('OnCrimewatchEngagementCreated', otherCharId, timeout)
        self.myEngagements[otherCharId] = timeout
        sm.ScatterEvent('OnCrimewatchEngagementUpdated', otherCharId, timeout)
        if self.duelWindow is not None and self.duelWindow.charID == otherCharId:
            self.duelWindow.Close()
            self.duelWindow = None

    def OnCrimewatchEngagementEnded(self, otherCharId):
        self.LogInfo('OnCrimewatchEngagementEnded', otherCharId)
        if otherCharId in self.myEngagements:
            del self.myEngagements[otherCharId]
        sm.ScatterEvent('OnCrimewatchEngagementUpdated', otherCharId, None)

    def OnCrimewatchEngagementStartTimeout(self, otherCharId, timeout):
        self.LogInfo('OnCrimewatchEngagementStartTimeout', otherCharId, timeout)
        self.myEngagements[otherCharId] = timeout
        sm.ScatterEvent('OnCrimewatchEngagementUpdated', otherCharId, timeout)

    def OnCrimewatchEngagementStopTimeout(self, otherCharId):
        self.LogInfo('OnCrimewatchEngagementStopTimeout', otherCharId)
        self.myEngagements[otherCharId] = const.crimewatchEngagementTimeoutOngoing
        sm.ScatterEvent('OnCrimewatchEngagementUpdated', otherCharId, const.crimewatchEngagementTimeoutOngoing)

    def GetMyEngagements(self):
        """
        Get a copy of all active engagements
        """
        return self.myEngagements.copy()

    def GetMyBoosters(self):
        myGodmaItem = sm.GetService('godma').GetItem(session.charid)
        boosters = myGodmaItem.boosters
        return boosters

    def GetBoosterEffects(self, booster):
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        boosterEffectsNegative = []
        boosterEffectsPositive = []
        try:
            effectIDs = dogmaLocation.GetDogmaItem(booster.itemID).activeEffects
        except KeyError:
            boosterEffect = sm.GetService('godma').GetItem(booster.itemID)
            for effect in boosterEffect.effects.values():
                if not effect.isActive:
                    continue
                eff = cfg.dgmeffects.Get(effect.effectID)
                if eff.fittingUsageChanceAttributeID:
                    boosterEffectsNegative.append(eff)
                else:
                    boosterEffectsPositive.append(eff)

        else:
            for effectID in effectIDs:
                eff = cfg.dgmeffects.Get(effectID)
                if eff.fittingUsageChanceAttributeID:
                    boosterEffectsNegative.append(eff)
                else:
                    boosterEffectsPositive.append(eff)

        return {'negative': boosterEffectsNegative,
         'positive': boosterEffectsPositive}

    def GetWeaponsTimer(self):
        return (self.weaponsTimerState, self.weaponsTimerExpiry)

    def GetNpcTimer(self):
        return (self.npcTimerState, self.npcTimerExpiry)

    def GetPvpTimer(self):
        return (self.pvpTimerState, self.pvpTimerExpiry)

    def GetCriminalTimer(self):
        return (self.criminalTimerState, self.criminalTimerExpiry)

    def GetSafetyLevel(self):
        return self.safetyLevel

    def SetSafetyLevel(self, safetyLevel):
        """set the safety level on client and server"""
        moniker.CharGetCrimewatchLocation().SetSafetyLevel(safetyLevel)
        self.safetyLevel = safetyLevel
        sm.ScatterEvent('OnSafetyLevelChanged', self.safetyLevel)

    def IsCriminal(self, charID):
        """Check wether we know this character to be a criminal"""
        return self.criminalFlagsByCharID.get(charID) == const.criminalTimerStateActiveCriminal

    def IsSuspect(self, charID):
        """Check wether we know this character to be a suspect"""
        return self.criminalFlagsByCharID.get(charID) == const.criminalTimerStateActiveSuspect

    def IsCriminallyFlagged(self, charID):
        """Check wether we know this character to be a suspect or criminal"""
        return charID in self.criminalFlagsByCharID

    def HasLimitedEngagmentWith(self, charID):
        """Check whether player has a limited engagement active with a particular character"""
        return charID in self.myEngagements

    def GetRequiredSafetyLevelForAssistanc(self, targetID):
        if self.IsCriminal(targetID):
            return const.shipSafetyLevelNone
        elif self.IsSuspect(targetID):
            return const.shipSafetyLevelPartial
        else:
            return const.shipSafetyLevelFull

    def GetSafetyLevelRestrictionForAttackingTarget(self, targetID, effect = None):
        """
        Returns the minimum safety level require for attack against target
        arguments
          targetID: the itemID of a target, None if an effect is AOE (area of effect) 
          effect: required if the effect is AOE other wise not used
        """
        securityClass = sm.GetService('map').GetSecurityClass(session.solarsystemid)
        minSafetyLevel = const.shipSafetyLevelFull
        if securityClass > const.securityClassZeroSec:
            item = self.michelle.GetItem(targetID)
            if not item:
                if effect.rangeAttributeID is not None:
                    minSafetyLevel = const.shipSafetyLevelNone
            elif util.IsSystemOrNPC(item.ownerID):
                if item.ownerID == const.ownerCONCORD:
                    minSafetyLevel = const.shipSafetyLevelNone
                elif item.groupID in const.illegalTargetNpcOwnedGroups:
                    if securityClass == const.securityClassHighSec:
                        minSafetyLevel = const.shipSafetyLevelNone
                    else:
                        minSafetyLevel = const.shipSafetyLevelPartial
            elif not self.CanAttackFreely(item):
                if securityClass == const.securityClassHighSec:
                    if item.groupID in const.targetGroupsWithSuspectPenaltyInHighSec:
                        minSafetyLevel = const.shipSafetyLevelPartial
                    else:
                        minSafetyLevel = const.shipSafetyLevelNone
                elif item.groupID == const.groupCapsule:
                    minSafetyLevel = const.shipSafetyLevelNone
                else:
                    minSafetyLevel = const.shipSafetyLevelPartial
        return minSafetyLevel

    def GetSafetyLevelRestrictionForAidingTarget(self, targetID):
        """
        Returns the minimum safety level require for aiding a target
        """
        secClass = sm.GetService('map').GetSecurityClass(session.solarsystemid)
        minSafetyLevel = const.shipSafetyLevelFull
        if secClass > const.securityClassZeroSec:
            item = self.michelle.GetItem(targetID)
            if item and item.ownerID != session.charid:
                if self.IsCriminallyFlagged(item.ownerID):
                    if self.IsCriminal(item.ownerID):
                        minSafetyLevel = const.shipSafetyLevelNone
                    elif self.IsSuspect(item.ownerID):
                        minSafetyLevel = const.shipSafetyLevelPartial
                else:
                    minSafetyLevel = const.shipSafetyLevelFull
        return minSafetyLevel

    def CanAttackFreely(self, item):
        if util.IsSystem(item.ownerID) or item.ownerID == session.charid:
            return True
        securityClass = sm.GetService('map').GetSecurityClass(session.solarsystemid)
        if securityClass == const.securityClassZeroSec:
            return True
        if self.IsCriminallyFlagged(item.ownerID):
            return True
        if self.HasLimitedEngagmentWith(item.ownerID):
            return True
        if util.IsCharacter(item.ownerID) and util.IsOutlawStatus(item.securityStatus):
            return True
        if session.warfactionid:
            if hasattr(item, 'corpID') and self.facwar.IsEnemyCorporation(item.corpID, session.warfactionid):
                return True
        belongToPlayerCorp = not util.IsNPC(session.corpid)
        if belongToPlayerCorp:
            if item.ownerID == session.corpid:
                if self.GetCorpAggressionSettings().IsFriendlyFireLegalAtTime(blue.os.GetWallclockTime()):
                    return True
            otherCorpID = getattr(item, 'corpID', None)
            if otherCorpID is not None:
                if otherCorpID == session.corpid:
                    if self.GetCorpAggressionSettings().IsFriendlyFireLegalAtTime(blue.os.GetWallclockTime()):
                        return True
                if self.war.GetRelationship(otherCorpID) == const.warRelationshipAtWarCanFight:
                    return True
            otherAllianceID = getattr(item, 'allianceID', None)
            if otherAllianceID is not None:
                if self.war.GetRelationship(otherAllianceID) == const.warRelationshipAtWarCanFight:
                    return True
        if IsItemFreeForAggression(item.groupID):
            return True
        return False

    def GetRequiredSafetyLevelForEffect(self, effect, targetID = None):
        requiredSafetyLevel = const.shipSafetyLevelFull
        if effect is not None:
            if targetID is None and effect.effectCategory == const.dgmEffTarget:
                targetID = sm.GetService('target').GetActiveTargetID()
                if targetID is None:
                    return requiredSafetyLevel
            requiredSafetyLevel = const.shipSafetyLevelFull
            if effect.isOffensive:
                requiredSafetyLevel = self.GetSafetyLevelRestrictionForAttackingTarget(targetID, effect)
            elif effect.isAssistance:
                requiredSafetyLevel = self.GetSafetyLevelRestrictionForAidingTarget(targetID)
        return requiredSafetyLevel

    def CheckUnsafe(self, requiredSafetyLevel):
        """
        compare a safety requirement and determine if it is admissable with the current safety levels
        the method is meant to be used when trying a potentially unsafe action and will trigger
        """
        if requiredSafetyLevel < self.safetyLevel:
            return True
        else:
            return False

    def SafetyActivated(self, requiredSafetyLevel):
        """
        note the activation of safeties and to the proper notifications
        """
        self.LogInfo('Safeties activated', self.safetyLevel, requiredSafetyLevel)
        sm.ScatterEvent('OnCrimewatchSafetyCheckFailed')

    def CheckCanTakeItems(self, containerID):
        """
        test the criminality of the taking from this container with regards to securtity
        """
        if session.solarsystemid is None:
            return True
        if self.GetSafetyLevel() == const.shipSafetyLevelFull:
            bp = self.michelle.GetBallpark()
            item = bp.GetInvItem(containerID)
            if item is not None:
                if item.groupID in (const.groupWreck,
                 const.groupCargoContainer,
                 const.groupFreightContainer,
                 const.groupSpewContainer):
                    bp = self.michelle.GetBallpark()
                    if bp and not bp.HaveLootRight(containerID):
                        return False
        return True

    def GetRequiredSafetyLevelForEngagingDrones(self, droneIDs, targetID):
        safetyLevel = const.shipSafetyLevelFull
        if targetID is not None:
            isAttacking = False
            isAiding = False
            effectIDs = set()
            for droneID in droneIDs:
                item = self.michelle.GetItem(droneID)
                if item is not None:
                    for row in cfg.dgmtypeeffects.get(item.typeID, []):
                        effectID, isDefault = row.effectID, row.isDefault
                        if isDefault:
                            effectIDs.add(effectID)

            if effectIDs:
                effects = [ cfg.dgmeffects.Get(effectID) for effectID in effectIDs ]
                safetyLevels = [ self.GetRequiredSafetyLevelForEffect(effect, targetID) for effect in effects ]
                safetyLevel = min(safetyLevels)
        return safetyLevel

    def OnDuelChallenge(self, fromCharID, fromCorpID, fromAllianceID, expiryTime):
        self.LogInfo('OnDuelChallenge', fromCharID, fromCorpID, fromAllianceID, expiryTime)
        wnd = uicls.DuelInviteWindow(charID=fromCharID, corpID=fromCorpID, allianceID=fromAllianceID)
        try:
            self.duelWindow = wnd
            wnd.StartTimeout(expiryTime)
            result = wnd.ShowDialog(modal=False)
            accept = None
            if 'accept' in wnd.result:
                accept = True
            elif 'decline' in wnd.result:
                accept = False
            if 'block' in wnd.result:
                uthread.new(sm.GetService('addressbook').BlockOwner, fromCharID)
            if accept is not None:
                moniker.CharGetCrimewatchLocation().RespondToDuelChallenge(fromCharID, expiryTime, accept)
        finally:
            self.duelWindow = None

    def StartDuel(self, charID):
        """
        Wrapper around the moniker server call so we can make interventions when:
        - character is already engaged with us
        """
        if charID in self.myEngagements:
            self.LogInfo('The char', charID, 'is already in limited engagement with us. No duel request sent.')
        else:
            moniker.CharGetCrimewatchLocation().StartDuelChallenge(charID)

    def GetMySecurityStatus(self):
        if self.mySecurityStatus is None:
            self.mySecurityStatus = moniker.CharGetCrimewatchLocation().GetMySecurityStatus()
        return self.mySecurityStatus

    def GetCharacterSecurityStatus(self, charID):
        return moniker.CharGetCrimewatchLocation().GetCharacterSecurityStatus(charID)

    def OnSecurityStatusUpdate(self, newSecurityStatus):
        self.mySecurityStatus = newSecurityStatus

    def OnGodmaItemChange(self, item, change):
        if const.ixLocationID in change and item.categoryID == const.categoryImplant and item.flagID in [const.flagBooster]:
            sm.ScatterEvent('OnCrimeWatchBoosterUpdated')

    def GetSecurityStatusTransactions(self):
        return moniker.CharGetCrimewatchLocation().GetSecurityStatusTransactions()

    def GetJumpTimers(self):
        if self.jumpTimers is None:
            self.jumpTimers = sm.RemoteSvc('jumpTimers').GetTimers(session.charid)
        return self.jumpTimers

    def OnJumpTimersUpdated(self, *args):
        self.jumpTimers = args

    def RefreshCorpAggressionSettings(self):
        self.corpAggressionSettings = self.corp.GetCorpRegistry().GetAggressionSettings()

    def GetCorpAggressionSettings(self):
        if self.corpAggressionSettings is None:
            self.RefreshCorpAggressionSettings()
        return self.corpAggressionSettings

    def OnCorpAggressionSettingsChange(self, aggressionSettings):
        self.corpAggressionSettings = aggressionSettings
