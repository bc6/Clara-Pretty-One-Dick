#Embedded file name: eve/common/script/util\notificationUtil.py
"""
Contains functions and mappings for the notification system that are used both on the client and on the server (or in ESP)
"""
import sys
import types
import yaml
import log
import utillib
import eve.common.script.mgt.entityConst as entities
import eve.common.script.util.eveFormat as evefmt
import carbon.common.script.util.format as fmtutil
import eve.common.script.sys.idCheckers as idCheckers
import localization
import eve.common.script.mgt.appLogConst as logConst
import eve.common.lib.appConst as const
from notificationconst import *
from workers.namegenerator import ConstructName
from workers.util import GetBidsForLocalization
securityLevelDescriptions = {-10: 'Notifications/SecurityStatus/SecurityDescription_-10',
 -9: 'Notifications/SecurityStatus/SecurityDescription_-9',
 -8: 'Notifications/SecurityStatus/SecurityDescription_-8',
 -7: 'Notifications/SecurityStatus/SecurityDescription_-7',
 -6: 'Notifications/SecurityStatus/SecurityDescription_-6',
 -5: 'Notifications/SecurityStatus/SecurityDescription_-5',
 -4: 'Notifications/SecurityStatus/SecurityDescription_-4',
 -3: 'Notifications/SecurityStatus/SecurityDescription_-3',
 -2: 'Notifications/SecurityStatus/SecurityDescription_-2',
 -1: 'Notifications/SecurityStatus/SecurityDescription_-1',
 0: 'Notifications/SecurityStatus/SecurityDescription_0',
 1: 'Notifications/SecurityStatus/SecurityDescription_1',
 2: 'Notifications/SecurityStatus/SecurityDescription_2',
 3: 'Notifications/SecurityStatus/SecurityDescription_3',
 4: 'Notifications/SecurityStatus/SecurityDescription_4',
 5: 'Notifications/SecurityStatus/SecurityDescription_5',
 6: 'Notifications/SecurityStatus/SecurityDescription_6',
 7: 'Notifications/SecurityStatus/SecurityDescription_7',
 8: 'Notifications/SecurityStatus/SecurityDescription_8',
 9: 'Notifications/SecurityStatus/SecurityDescription_9',
 10: 'Notifications/SecurityStatus/SecurityDescription_10'}
rankLost = {const.factionCaldariState: 'UI/FactionWarfare/Ranks/RankLostCaldari',
 const.factionMinmatarRepublic: 'UI/FactionWarfare/Ranks/RankLostMinmatar',
 const.factionAmarrEmpire: 'UI/FactionWarfare/Ranks/RankLostAmarr',
 const.factionGallenteFederation: 'UI/FactionWarfare/Ranks/RankLostGallente'}
rankGain = {const.factionCaldariState: 'UI/FactionWarfare/Ranks/RankGainCaldari',
 const.factionMinmatarRepublic: 'UI/FactionWarfare/Ranks/RankGainMinmatar',
 const.factionAmarrEmpire: 'UI/FactionWarfare/Ranks/RankGainAmarr',
 const.factionGallenteFederation: 'UI/FactionWarfare/Ranks/RankGainGallente'}

def CreateItemInfoLink(itemID):
    item = cfg.eveowners.Get(itemID)
    return '<a href="showinfo:%(typeID)s//%(itemID)s">%(itemName)s</a>' % {'typeID': item.typeID,
     'itemID': itemID,
     'itemName': item.name}


def CreateLocationInfoLink(locationID, locationTypeID = None):
    locationName = cfg.evelocations.Get(locationID).name
    if locationTypeID is None:
        if idCheckers.IsRegion(locationID):
            locationTypeID = const.typeRegion
        elif idCheckers.IsConstellation(locationID):
            locationTypeID = const.typeConstellation
        elif idCheckers.IsSolarSystem(locationID):
            locationTypeID = const.typeSolarSystem
        elif idCheckers.IsStation(locationID):
            if boot.role == 'client':
                stationinfo = sm.RemoteSvc('stationSvc').GetStation(locationID)
            else:
                stationinfo = sm.GetService('stationSvc').GetStation(locationID)
            locationTypeID = stationinfo.stationTypeID
    if locationTypeID is None:
        return locationName
    else:
        return '<a href="showinfo:%(typeID)s//%(locationID)s">%(locationName)s</a>' % {'typeID': locationTypeID,
         'locationID': locationID,
         'locationName': locationName}


def CreateTypeInfoLink(typeID):
    return '<a href="showinfo:%(typeID)s">%(typeName)s</a>' % {'typeID': typeID,
     'typeName': cfg.invtypes.Get(typeID).name}


def GetAgent(agentID):
    """
        Returns the agent info (as keyval) with corporationID, stationID and solarSystemID.
        Will return None if the agent is no longer available (all his missions have been disabled).
    """
    if boot.role == 'client':
        return sm.GetService('agents').GetAgentByID(agentID)
    else:
        agent = utillib.KeyVal(sm.GetService('agentMgr').GetAgentStaticInfo(agentID))
        if agent is None:
            return
        station = sm.GetService('stationSvc').GetStation(agent.stationID)
        if agent.corporationID is None:
            agent.corporationID = station.ownerID
        agent.factionID = sm.GetService('corporationSvc').GetFactionIDByCorpID(agent.corporationID)
        agent.solarsystemID = station.solarSystemID
        return agent


def GetAgentArgs(agentID):
    agentInfo = GetAgent(agentID)
    if not agentInfo:
        return {}
    agentArgs = {'agentID': agentInfo.agentID}
    agentArgs['agentCorpID'] = agentInfo.corporationID
    agentArgs['agentFactionID'] = agentInfo.factionID
    agentArgs['agentSolarSystemID'] = agentInfo.solarsystemID
    agentArgs['agentLocation'] = agentInfo.solarsystemID
    if getattr(agentInfo, 'stationID', None):
        agentArgs['agentStationID'] = agentInfo.stationID
        agentArgs['agentLocation'] = agentInfo.stationID
    if boot.role == 'client':
        mapSvc = sm.GetService('map')
        agentArgs['agentConstellationID'] = mapSvc.GetConstellationForSolarSystem(agentInfo.solarsystemID)
        agentArgs['agentRegionID'] = mapSvc.GetRegionForSolarSystem(agentInfo.solarsystemID)
    else:
        ss = sm.GetService('stationSvc').GetSolarSystem(agentInfo.solarsystemID)
        agentArgs['agentConstellationID'] = ss.constellationID
        agentArgs['agentRegionID'] = ss.regionID
    return agentArgs


def GetRelationshipName(level):
    if level == const.contactHighStanding:
        return localization.GetByLabel('Notifications/partRelationshipExcellent')
    if level == const.contactGoodStanding:
        return localization.GetByLabel('Notifications/partRelationshipGood')
    if level == const.contactNeutralStanding:
        return localization.GetByLabel('Notifications/partRelationshipNeutral')
    if level == const.contactBadStanding:
        return localization.GetByLabel('Notifications/partRelationshipBad')
    if level == const.contactHorribleStanding:
        return localization.GetByLabel('Notifications/partRelationshipHorrible')
    return level


def ParamCharacterTerminationNotification(notification):
    security = int(round(notification.data['security']))
    roleNameIDs = notification.data.get('roleNameIDs', None)
    if roleNameIDs is None or len(roleNameIDs) == 0:
        roleName = notification.data.get('roleName', localization.GetByLabel('UI/Generic/Person'))
    else:
        roleNames = [ localization.GetByMessageID(roleNameID) for roleNameID in roleNameIDs ]
        roleName = localization.formatters.FormatGenericList(roleNames, useConjunction=True)
    return {'securityDescription': localization.GetByLabel(securityLevelDescriptions[security], **notification.data),
     'corpName': CreateItemInfoLink(notification.data['corpID']),
     'roleName': roleName}


def ParamCharacterMedalNotification(notification):
    if boot.role == 'client':
        medalDetails = sm.GetService('medals').GetMedalDetails(notification.data['medalID'])
    else:
        medalDetails = sm.GetService('corporationSvc').GetMedalDetails(notification.data['medalID'])
    return {'issuerCorp': CreateItemInfoLink(notification.data['corpID']),
     'description': medalDetails.info[0].description,
     'title': medalDetails.info[0].title}


def ParamAllWarNotification(notification):
    return {'againstName': CreateItemInfoLink(notification.data['againstID']),
     'declaredByName': CreateItemInfoLink(notification.data['declaredByID'])}


def ParamAllWarNotificationWithCost(notification):
    return {'againstName': CreateItemInfoLink(notification.data['againstID']),
     'declaredByName': CreateItemInfoLink(notification.data['declaredByID']),
     'costText': localization.GetByLabel('Notifications/bodyWar', **notification.data) if notification.data['cost'] else ''}


def ParamSovFmtCorpID(notification):
    return {'corporation': CreateItemInfoLink(notification.data['corpID'])}


def ParamFmtFactionWarfareCorps(notification):
    return {'corporationName': CreateItemInfoLink(notification.data['corpID']),
     'factionName': CreateItemInfoLink(notification.data['factionID'])}


def ParamFmtFactionWarfareAlliances(notification):
    return {'allianceName': CreateItemInfoLink(notification.data['allianceID']),
     'factionName': CreateItemInfoLink(notification.data['factionID'])}


def ParamFmtSovDamagedNotification(notification):
    res = {'shieldValue': notification.data['shieldValue'] * 100.0,
     'armorValue': notification.data['armorValue'] * 100.0,
     'hullValue': notification.data['hullValue'] * 100.0}
    aggressorID = notification.data.get('aggressorID', None)
    if aggressorID is not None:
        res['aggressor'] = CreateItemInfoLink(aggressorID)
    else:
        res['aggressor'] = localization.GetByLabel('UI/Common/Unknown')
    aggressorCorpID = notification.data.get('aggressorCorpID', None)
    if aggressorCorpID is not None:
        res['aggressorCorp'] = CreateItemInfoLink(aggressorCorpID)
    else:
        res['aggressorCorp'] = localization.GetByLabel('UI/Common/Unknown')
    aggressorAllID = notification.data.get('aggressorAllianceID', None)
    if aggressorAllID is not None:
        res['aggressorAlliance'] = CreateItemInfoLink(aggressorAllID)
    else:
        res['aggressorAlliance'] = localization.GetByLabel('UI/Common/NoAlliance')
    return res


def ParamFmtCorpDividendNotification(notification):
    msgID = 'Notifications/bodyCorpPayoutDividendsNonMember'
    if 'isMembers' in notification.data and notification.data['isMembers']:
        msgID = 'Notifications/bodyCorpPayoutDividendsMember'
    corpName = CreateItemInfoLink(notification.data['corpID'])
    notification.data.update({'corporationName': corpName})
    return {'corporationName': corpName,
     'body': localization.GetByLabel(msgID, **notification.data)}


def ParamFmtInsurancePayout(notification):
    msg = ''
    if notification.data['payout']:
        msg = localization.GetByLabel('Notifications/bodyInsurancePayoutDefault')
    return {'defaultPayoutText': msg}


def ParamCorpOfficeExpiration(notification):
    if notification.data['typeID'] == const.typeOfficeFolder:
        whereText = localization.GetByLabel('Notifications/bodyCorpOfficeExpiresOffice', **notification.data)
    else:
        whereText = localization.GetByLabel('Notifications/bodyCorpOfficeExpiresItems', **notification.data)
    reasonText = ''
    if notification.data['errorText']:
        reasonText = localization.GetByLabel('Notifications/bodyCorpOfficeExpiresReason', **notification.data)
    return {'reasonText': reasonText,
     'whereText': whereText}


def PramCloneActivationNotification(notification):
    res = {}
    res['cloningServiceText'] = ''
    if notification.data['cloneStationID'] != notification.data['corpStationID']:
        res['cloningServiceText'] = localization.GetByLabel('Notifications/bodyCloneActivatedStationChange', **notification.data)
    res['lastCloneText'] = ''
    res['cloneBoughtText'] = ''
    res['spLostText'] = ''
    skillPointsLost = notification.data.get('skillPointsLost', None)
    if skillPointsLost is not None:
        res['spLostText'] = localization.GetByLabel('Notifications/bodyCloneActivatedSkillPointsLost', **notification.data)
        lastCloned = notification.data.get('lastCloned', None)
        if lastCloned is not None:
            res['lastCloneText'] = '<br><br>' + localization.GetByLabel('Notifications/bodyCloneActivatedLastCloned', **notification.data)
        cloneBought = notification.data.get('cloneBought', None)
        if cloneBought is not None:
            res['cloneBoughtText'] = '<br>' + localization.GetByLabel('Notifications/bodyCloneActivatedLastPurchased', **notification.data)
    return res


def ParamCloneActivation2Notification(notification):
    res = {}
    res['cloningServiceText'] = ''
    if notification.data['cloneStationID'] != notification.data['corpStationID']:
        res['cloningServiceText'] = localization.GetByLabel('Notifications/bodyCloneActivatedStationChange2', **notification.data)
    res['lastCloneText'] = ''
    lastCloned = notification.data.get('lastCloned', None)
    if lastCloned is not None:
        res['lastCloneText'] = '<br><br>' + localization.GetByLabel('Notifications/bodyCloneActivatedLastCloned2', **notification.data)
    return res


def ParamContainerPasswordNotification(notification):
    res = {}
    stationID = notification.data.get('stationID', None)
    if stationID is not None:
        res['locationName'] = localization.GetByLabel('Notifications/subjContainerLocation', **notification.data)
    else:
        res['locationName'] = CreateLocationInfoLink(notification.data['solarSystemID'])
    password = notification.data.get('password', None)
    if password is None:
        res['password'] = localization.GetByLabel('Notifications/bodyContainerPasswordChangedToBlank')
    if notification.data['passwordType'] == 'general':
        res['passwordType'] = localization.GetByLabel('UI/SystemMenu/GeneralSettings/General/Header')
    else:
        res['passwordType'] = localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/Header')
    return res


def ParamCustomsNotification(notification):
    standingPenaltySum = 0
    fineSum = 0
    res = {}
    res['factionName'] = CreateItemInfoLink(notification.data['factionID'])
    msg = ''
    for lost in notification.data['lostList']:
        standingPenaltySum += lost['penalty']
        fineSum += lost['fine']
        responseText = ''
        if notification.data['shouldAttack']:
            responseText = localization.GetByLabel('Notifications/bodyContrabandConfiscationResponseDeadly')
        elif notification.data['shouldConfiscate']:
            responseText = localization.GetByLabel('Notifications/bodyContrabandConfiscationResponseConfiscation')
        msg += localization.GetByLabel('Notifications/bodyContrabandConfiscationLostItems', responseText=responseText, **lost)

    res['confiscatedItems'] = msg
    res['summaryResponseText'] = ''
    if notification.data['shouldAttack']:
        res['summaryResponseText'] = localization.GetByLabel('Notifications/bodyContrabandConfiscationSummaryResponseDeadly')
    elif notification.data['shouldConfiscate']:
        res['summaryResponseText'] = localization.GetByLabel('Notifications/bodyContrabandConfiscationSummaryResponseConfiscation')
    res['ideal'] = standingPenaltySum
    res['actual'] = standingPenaltySum / notification.data['standingDivision']
    res['total'] = fineSum
    return res


def ParamInsuranceFirstShipNotification(notification):
    res = {}
    if notification.data.get('isHouseWarmingGift', 0):
        res['gift'] = CreateTypeInfoLink(const.deftypeHouseWarmingGift)
    else:
        res['gift'] = localization.GetByLabel('Notifications/bodyNoobShipNoGift')
    return res


def ParamInsuranceInvalidatedNotification(notification):
    res = {}
    reason = notification.data['reason']
    if reason == 1:
        res['reason'] = localization.GetByLabel('Notifications/bodyInsuranceInvalidNotOwnedByYou', **notification.data)
    elif reason == 2:
        res['reason'] = localization.GetByLabel('Notifications/bodyInsuranceInvalidHasExpired', **notification.data)
    elif reason == 3:
        res['reason'] = localization.GetByLabel('Notifications/bodyInsuranceInvalidNoValue', **notification.data)
    return res


def ParamSovAllClaimFailNotification(notification):
    reason = notification.data['reason']
    res = {'solarSystemID': notification.data['solarSystemID'],
     'corporation': CreateItemInfoLink(notification.data['corpID']),
     'alliance': CreateItemInfoLink(notification.data['allianceID'])}
    res['body'] = ''
    if reason == 1:
        res['body'] = localization.GetByLabel('Notifications/bodySovClaimFailedByOther', **res)
    elif reason == 2:
        res['body'] = localization.GetByLabel('Notifications/bodySovClaimFailedNoAlliance', **res)
    elif reason == 3:
        res['body'] = localization.GetByLabel('Notifications/bodySovClaimFailedBillNotPaid', **res)
    return res


def ParamAllAnchoringNotification(notification):
    res = {'corpName': CreateItemInfoLink(notification.data['corpID']),
     'allianceText': '',
     'otherTowersText': localization.GetByLabel('Notifications/bodyPOSAnchoredNoTowers')}
    allianceID = notification.data.get('allianceID', None)
    if allianceID is not None:
        allianceName = CreateItemInfoLink(notification.data['allianceID'])
        res['allianceText'] = localization.GetByLabel('Notifications/bodyPOSAnchoredAlliance', allianceName=allianceName)
    corpsPresent = notification.data.get('corpsPresent', None)
    if corpsPresent is not None and len(notification.data['corpsPresent']):
        otherTowers = localization.GetByLabel('Notifications/bodyPOSAnchoredOtherTowers')
        for corp in notification.data['corpsPresent']:
            if len(corp['towers']) > 0:
                allianceText = ''
                if corp['allianceID'] is not None:
                    allianceName = CreateItemInfoLink(corp['allianceID'])
                    allianceText = localization.GetByLabel('Notifications/bodyPOSAnchoredOthersTowerAlliance', allianceName=allianceName)
                otherTowers += localization.GetByLabel('Notifications/bodyPOSAnchoredTowersByCorp', towerCorp=CreateItemInfoLink(corp['corpID']), allianceText=allianceText)
                for tower in corp['towers']:
                    otherTowers += localization.GetByLabel('Notifications/bodyPOSAnchoredTower', **tower)

                otherTowers += '<br>'

        res['otherTowersText'] = otherTowers
    return res


def ParamJumpCloneDeleted1Notification(notification):
    res = {'destroyerID': notification.data['locationOwnerID']}
    implantListText = ''
    if len(notification.data['typeIDs']):
        implantListText += localization.GetByLabel('Notifications/bodyCloneJumpImplantDestructionHeader')
        for implantTypeID in notification.data['typeIDs']:
            msg = 'Notifications/bodyCloneJumpImplantDestructionImplantType'
            implantListText += localization.GetByLabel(msg, implantTypeID=int(implantTypeID))

    else:
        implantListText += localization.GetByLabel('Notifications/bodyCloneJumpImplantDestructionNone')
    res['implantListText'] = implantListText
    return res


def ParamJumpCloneDeleted2Notification(notification):
    res = ParamJumpCloneDeleted1Notification(notification)
    res['destroyerID'] = notification.data['destroyerID']
    return res


def ParamStoryLineMissionAvailableNotification(notification):
    agent = GetAgent(notification.senderID)
    if agent is None:
        res = notification.data
        res['body'] = localization.GetByLabel('Notifications/bodyAgentRetired')
        return res
    res = {'agent_corporationName': CreateItemInfoLink(agent.corporationID),
     'agent_agentID': agent.agentID,
     'agent_stationID': agent.stationID,
     'agent_solarsystemID': agent.solarsystemID}
    notification.data.update(res)
    if agent.stationID:
        res['body'] = localization.GetByLabel('Notifications/bodyStoryLineMissionAvilableStation', **notification.data)
    else:
        res['body'] = localization.GetByLabel('Notifications/bodyStoryLineMissionAvilableSpace', **notification.data)
    return res


def ParamStationAggression1Notification(notification):
    aggressorID = notification.data.get('aggressorID', None)
    res = {'shieldDamage': int(notification.data['shieldValue'] * 100),
     'agressorText': ''}
    if aggressorID is not None:
        ownerOb = cfg.eveowners.Get(aggressorID)
        if ownerOb.IsCharacter():
            notification.data['aggressorCorpName'] = CreateItemInfoLink(notification.data['aggressorCorpID'])
            res['agressorText'] = localization.GetByLabel('Notifications/bodyOutpostAgressionAgressorCharacter', **notification.data)
        else:
            res['agressorText'] = localization.GetByLabel('Notifications/bodyOutpostAgressionAgressorOwner', owner=ownerOb.name)
    return res


def ParamStationConquerNotification(notification):
    res = {'oldCorpName': CreateItemInfoLink(notification.data['oldOwnerID']),
     'newCorpName': CreateItemInfoLink(notification.data['newOwnerID'])}
    charID = notification.data.get('charID')
    if charID is not None:
        res['characterText'] = localization.GetByLabel('Notifications/bodyOutpostConqueredCharacter', **notification.data)
    return res


def ParamStationStateChangeNotification(notification):
    state = notification.data['state']
    if state == entities.STATE_IDLE:
        return {'subject': localization.GetByLabel('Notifications/subjOutpostServiceReenabled', **notification.data)}
    if state == entities.STATE_INCAPACITATED:
        return {'subject': localization.GetByLabel('Notifications/subjOutpostServiceDisabled', **notification.data)}
    return {'subject': ''}


def ParamStationAggression2Notification(notification):
    uknMsg = localization.GetByLabel('UI/Common/Unknown')
    res = {'shieldDamage': notification.data.get('shieldValue', 0.0) * 100.0,
     'armorDamage': notification.data.get('armorValue', 0.0) * 100.0,
     'hullDamage': notification.data.get('hullValue', 0.0) * 100.0,
     'aggressor': uknMsg,
     'aggressorCorp': uknMsg,
     'aggressorAlliance': uknMsg}
    aggressorID = notification.data.get('aggressorID', None)
    if aggressorID is not None:
        res['aggressor'] = CreateItemInfoLink(notification.data['aggressorID'])
    aggressorCorpID = notification.data.get('aggressorCorpID', None)
    if aggressorCorpID is not None:
        res['aggressorCorp'] = CreateItemInfoLink(notification.data['aggressorCorpID'])
    aggressorAllianceID = notification.data.get('aggressorAllianceID', None)
    if aggressorAllianceID is None:
        res['aggressorAlliance'] = localization.GetByLabel('UI/Common/CorporationNotInAlliance')
    elif aggressorAllianceID != 0:
        res['aggressorAlliance'] = CreateItemInfoLink(aggressorAllianceID)
    return res


def ParamIncursionCompletedNotification(notification):
    topTen = notification.data['topTen']
    charIDs, discarded = zip(*topTen)
    cfg.eveowners.Prime(charIDs)
    res = {'topTenString': ''}
    if boot.role == 'client':
        res['constellationID'] = sm.GetService('map').GetParent(notification.data['solarSystemID'])
    else:
        res['constellationID'] = cfg.mapSystemCache[notification.data['solarSystemID']].constellationID
    for index, (topTenCharacterID, topTenRewardAmount) in enumerate(topTen):
        topTenArgs = {'number': index + 1,
         'topTenCharacterID': topTenCharacterID,
         'LPAmount': topTenRewardAmount}
        res['topTenString'] += localization.GetByLabel('Notifications/bodyIncursionCompleteTopTenEntry', **topTenArgs)

    res['journalLink'] = '<b>' + localization.GetByLabel('UI/Neocom/JournalBtn') + '</b>'
    return res


def FormatFWCharRankLossNotification(notification):
    """ Can not use standard formating as the message string is depended on the faction"""
    factionID = notification.data['factionID']
    newRank = notification.data['newRank']
    rankLabel, rankDescription = sm.GetService('facwar').GetRankLabel(factionID, newRank)
    message = localization.GetByLabel(rankLost[factionID], rank=rankLabel)
    return (localization.GetByLabel('UI/Generic/FormatStandingTransactions/RankDemotion'), message)


def FormatFWCharRankGainNotification(notification):
    """ Can not use standard formating as the message string is depended on the faction"""
    factionID = notification.data['factionID']
    newRank = notification.data['newRank']
    rankLabel, rankDescription = sm.GetService('facwar').GetRankLabel(factionID, newRank)
    message = localization.GetByLabel(rankGain[factionID], rank=rankLabel)
    return (localization.GetByLabel('UI/Generic/FormatStandingTransactions/subjectFacwarPromotion'), message)


def FormatShipReimbursementMessage(notification):
    if 'body' in notification.data:
        return (localization.GetByLabel('Notifications/subjLegacy', subject=notification.data['subject']), localization.GetByLabel('Notifications/bodyLegacy', body=notification.data['body']))
    subject = localization.GetByLabel('Notifications/subjShipReimbursement')
    bodyPars = [localization.GetByLabel('Notifications/bodyShipReimbursement', **notification.data)]
    if notification.data['addCloneInfo']:
        bodyPars.append(localization.GetByLabel('Notifications/bodyShipReimbursementCloneInfo'))
    bodyPars.append(localization.GetByLabel('Notifications/bodyConcordSignOff'))
    return (subject, '\n\n'.join(bodyPars))


def FormatAllWarDeclared(notification):
    notification.data.update(ParamAllWarNotificationWithCost(notification))
    heading = localization.GetByLabel('Notifications/subjWarDeclare', **notification.data)
    if notification.data['hostileState']:
        message = localization.GetByLabel('Notifications/bodyWarLegal', **notification.data)
    else:
        message = localization.GetByLabel('Notifications/bodyWarDelayed', **notification.data)
    return (heading, message)


def FormatLocateCharNotification(notification):
    characterID = notification.data['characterID']
    messageIndex = notification.data['messageIndex']
    agentLocation = notification.data['agentLocation']
    agentSystem = agentLocation.get(const.groupSolarSystem, None)
    agentStation = agentLocation.get(const.groupStation, None)
    targetLocation = notification.data['targetLocation']
    targetRegion = targetLocation.get(const.groupRegion, None)
    targetConstellation = targetLocation.get(const.groupConstellation, None)
    targetSystem = targetLocation.get(const.groupSolarSystem, None)
    targetStation = targetLocation.get(const.groupStation, None)
    if isinstance(targetRegion, (int, long)):
        targetRegion = cfg.evelocations.Get(targetRegion).name
    if isinstance(targetConstellation, (int, long)):
        targetConstellation = cfg.evelocations.Get(targetConstellation).name
    if isinstance(targetSystem, (int, long)):
        targetSystem = cfg.evelocations.Get(targetSystem).name
    if isinstance(targetStation, (int, long)):
        targetStation = cfg.evelocations.Get(targetStation).name
    locationText = ''
    if agentStation == targetStation:
        locationText = localization.GetByLabel('UI/Agents/Locator/InYourStation', charID=characterID)
    elif targetStation != None and agentSystem == targetSystem and agentStation != targetStation:
        locationText = localization.GetByLabel('UI/Agents/Locator/InYourSystemInStation', charID=characterID, stationName=targetStation)
    elif agentSystem == targetSystem:
        locationText = localization.GetByLabel('UI/Agents/Locator/InYourSystem', charID=characterID)
    elif targetStation == None:
        if targetRegion != None:
            locationText = localization.GetByLabel('UI/Agents/Locator/InOtherRegion', charID=characterID, systemName=targetSystem, constellationName=targetConstellation, regionName=targetRegion)
        elif targetConstellation != None:
            locationText = localization.GetByLabel('UI/Agents/Locator/InOtherConstellation', charID=characterID, systemName=targetSystem, constellationName=targetConstellation)
        elif targetSystem != None:
            locationText = localization.GetByLabel('UI/Agents/Locator/InOtherSystem', charID=characterID, systemName=targetSystem)
    elif targetRegion != None:
        locationText = localization.GetByLabel('UI/Agents/Locator/InOtherRegionInStation', charID=characterID, stationName=targetStation, systemName=targetSystem, constellationName=targetConstellation, regionName=targetRegion)
    elif targetConstellation != None:
        locationText = localization.GetByLabel('UI/Agents/Locator/InOtherConstellationInStation', charID=characterID, stationName=targetStation, systemName=targetSystem, constellationName=targetConstellation)
    elif targetSystem != None:
        locationText = localization.GetByLabel('UI/Agents/Locator/InOtherSystemInStation', charID=characterID, stationName=targetStation, systemName=targetSystem)
    title = localization.GetByLabel('UI/Agents/Locator/LocatedEmailHeader', charID=characterID, linkdata=['showinfo', cfg.eveowners.Get(characterID).typeID, characterID])
    introLabel = ['UI/Agents/Locator/LocatedEmailIntro1', 'UI/Agents/Locator/LocatedEmailIntro2'][messageIndex]
    message = localization.GetByLabel(introLabel, charID=characterID, agentID=notification.senderID)
    message += '<br><br>'
    message += locationText
    message += '<br><br>'
    message += localization.GetByLabel('UI/Agents/Locator/LocatedEmailGoodbyeText', agentID=notification.senderID, linkdata=['showinfo', cfg.eveowners.Get(notification.senderID).typeID, notification.senderID])
    return (title, message)


def FormatMissionOfferExpiredNotification(notification):
    if 'missionKeywords' in notification.data:
        messageKeywords = notification.data['missionKeywords']
        messageKeywords.update(GetAgentArgs(notification.senderID))
        messageKeywords.update({'player': notification.receiverID})
    else:
        messageKeywords = {}
    retVal = {}
    for x in ['header', 'body']:
        msg = notification.data[x]
        if isinstance(msg, (list, tuple)):
            msgLbl, msgArgs = msg
            msgArgs.update(messageKeywords)
            retVal[x] = localization.GetByLabel(msgLbl, **msgArgs)
        elif isinstance(msg, (int, long)):
            retVal[x] = localization.GetByMessageID(msg, **messageKeywords)
        else:
            retVal[x] = msg

    return (retVal['header'], retVal['body'])


def FormatBillNotification(notification):
    billTypeID = notification.data['billTypeID']
    if 'currentDate' not in notification.data:
        notification.data['currentDate'] = notification.created
    notification.data['creditorsName'] = CreateItemInfoLink(notification.data['creditorID'])
    notification.data['debtorsName'] = CreateItemInfoLink(notification.data['debtorID'])
    if billTypeID == const.billTypeMarketFine:
        messagePath = 'Notifications/bodyBillMarketFine'
    elif billTypeID == const.billTypeRentalBill:
        messagePath = 'Notifications/bodyBillRental'
    elif billTypeID == const.billTypeBrokerBill:
        messagePath = 'Notifications/bodyBillBroker'
    elif billTypeID == const.billTypeWarBill:
        notification.data['against'] = CreateItemInfoLink(notification.data['externalID'])
        messagePath = 'Notifications/bodyBillWar'
    elif billTypeID == const.billTypeAllianceMaintainanceBill:
        notification.data['allianceName'] = CreateItemInfoLink(notification.data['externalID'])
        messagePath = 'Notifications/bodyBillAllianceMaintenance'
    elif billTypeID == const.billTypeSovereignityMarker:
        messagePath = 'Notifications/bodyBillSovereignty'
    message = localization.GetByLabel(messagePath, **notification.data)
    subject = localization.GetByLabel('Notifications/subjBill', **notification.data)
    return (subject, message)


def FormatCorpNewsNotification(notification):
    """ This is the formating for a corporate vote news message. It indicates 
        varying data about the details of a vote, declaring war, peace, creating shares, 
        and expelling a member
    """
    notification.data['corpName'] = CreateItemInfoLink(notification.data['corpID'])
    voteType = notification.data['voteType']
    if voteType == const.voteWar:
        notification.data['parameterCorpName'] = CreateItemInfoLink(notification.data['parameter'])
        if notification.data['inEffect']:
            title = localization.GetByLabel('Notifications/subjCorpNewsAtWar', **notification.data)
        else:
            title = localization.GetByLabel('Notifications/subjCorpNewsAtPeace', **notification.data)
    elif voteType == const.voteShares:
        title = localization.GetByLabel('Notifications/subjCorpNewsCreatedShares', **notification.data)
    elif voteType == const.voteKickMember:
        title = localization.GetByLabel('Notifications/subjCorpNewsExpelsMemeber', **notification.data)
    message = notification.data['body']
    if message == '':
        message = title
    return (title, message)


def FormatTowerAlertNotification(notification):
    """
        This is the tower damage alert notification
    """
    moonID = notification.data.get('moonID', None)
    if moonID is not None:
        notification.data['moonName'] = CreateLocationInfoLink(moonID)
    else:
        notification.data['moonName'] = localization.GetByLabel('Notifications/UnknownSystem')
    message = localization.GetByLabel('Notifications/bodyStarbaseDamageLocation', **notification.data)
    shieldValue = notification.data['shieldValue']
    armorValue = notification.data['armorValue']
    hullValue = notification.data['hullValue']
    if shieldValue is not None and armorValue is not None and hullValue is not None:
        notification.data['shieldDamage'] = int(shieldValue * 100)
        notification.data['armorDamage'] = int(armorValue * 100)
        notification.data['hullDamage'] = int(hullValue * 100)
        message += localization.GetByLabel('Notifications/bodyStarbaseDamageValues', **notification.data)
    else:
        message += localization.GetByLabel('Notifications/bodyStarbaseDamageMissing')
    if notification.data['aggressorID'] is not None:
        ownerOb = cfg.eveowners.Get(notification.data['aggressorID'])
        if ownerOb.IsCharacter():
            notification.data['agressorCorp'] = CreateItemInfoLink(notification.data['aggressorCorpID'])
            notification.data['agressorAlliance'] = '-'
            if notification.data['aggressorAllianceID'] is not None:
                notification.data['agressorAlliance'] = CreateItemInfoLink(notification.data['aggressorAllianceID'])
            message += localization.GetByLabel('Notifications/bodyStarbaseDamageAttacker', **notification.data)
        else:
            aggressorName = CreateItemInfoLink(notification.data['aggressorID'])
            message += localization.GetByLabel('Notifications/bodyStarbaseDamageAgressorNotCharacter', aggressorName=aggressorName)
    return (localization.GetByLabel('Notifications/subjStarbaseDamage', **notification.data), message)


def FormatTutorialNotification(notification):
    title = localization.GetByLabel('Notifications/subjTutorial')
    agent = GetAgent(notification.senderID)
    if agent is None:
        message = localization.GetByLabel('Notifications/bodyAgentRetired')
    else:
        notification.data['charID'] = notification.receiverID
        notification.data['corpName'] = CreateItemInfoLink(agent.corporationID)
        notification.data['stationID'] = agent.stationID
        notification.data['agentID'] = agent.agentID
        message = localization.GetByLabel('Notifications/bodyTutorial', **notification.data)
    return (title, message)


def FormatTowerResourceAlertNotification(notification):
    if notification.data['corpID']:
        corpName = CreateItemInfoLink(notification.data['corpID'])
        msg = localization.GetByLabel('Notifications/bodyStarbaseLowResourcesCorp', corpName=corpName)
        allianceID = notification.data.get('allianceID', None)
        if allianceID is not None:
            allianceName = CreateItemInfoLink(notification.data['allianceID'])
            msg += localization.GetByLabel('Notifications/bodyStarbaseLowResourcesAlliance', allianceName=allianceName)
        notification.data['corpAllianceText'] = msg
    else:
        notification.data['corpAllianceText'] = ''
    message = localization.GetByLabel('Notifications/bodyStarbaseLowResources', **notification.data)
    for want in notification.data['wants']:
        message += localization.GetByLabel('Notifications/bodyStarbaseLowResourcesWants', **want)

    return (localization.GetByLabel('Notifications/subjStarbaseLowResources', **notification.data), message)


def FormatOrbitalAttackedNotification(notification):
    uknMsg = localization.GetByLabel('UI/Common/Unknown')
    res = {'shieldValue': notification.data.get('shieldLevel', 0.0) * 100.0,
     'planetID': notification.data['planetID'],
     'planetLinkArgs': ['showinfo', notification.data['planetTypeID'], notification.data['planetID']],
     'typeID': notification.data['typeID'],
     'solarSystemID': notification.data['solarSystemID'],
     'aggressor': notification.data['aggressorID'],
     'aggressorCorp': uknMsg,
     'aggressorAlliance': uknMsg}
    if notification.data['aggressorCorpID'] is not None:
        res['aggressorCorp'] = CreateItemInfoLink(notification.data['aggressorCorpID'])
    aggressorAllianceID = notification.data.get('aggressorAllianceID', None)
    if aggressorAllianceID is None:
        res['aggressorAlliance'] = localization.GetByLabel('UI/Common/CorporationNotInAlliance')
    elif aggressorAllianceID != 0:
        res['aggressorAlliance'] = CreateItemInfoLink(aggressorAllianceID)
    return res


def FormatOrbitalReinforcedNotification(notification):
    uknMsg = localization.GetByLabel('UI/Common/Unknown')
    res = {'reinforceExitTime': notification.data['reinforceExitTime'],
     'planetID': notification.data['planetID'],
     'planetLinkArgs': ['showinfo', notification.data['planetTypeID'], notification.data['planetID']],
     'typeID': notification.data['typeID'],
     'solarSystemID': notification.data['solarSystemID'],
     'aggressor': notification.data['aggressorID'],
     'aggressorCorp': uknMsg,
     'aggressorAlliance': uknMsg}
    aggressorCorpID = notification.data.get('aggressorCorpID', None)
    if aggressorCorpID is not None:
        res['aggressorCorp'] = CreateItemInfoLink(notification.data['aggressorCorpID'])
    aggressorAllianceID = notification.data.get('aggressorAllianceID', None)
    if aggressorAllianceID is None:
        res['aggressorAlliance'] = localization.GetByLabel('UI/Common/CorporationNotInAlliance')
    elif aggressorAllianceID != 0:
        res['aggressorAlliance'] = CreateItemInfoLink(aggressorAllianceID)
    return res


def FormatFacWarLPPayout(notification):
    location = CreateLocationInfoLink(notification.data['locationID'], const.typeSolarSystem)
    corporation = CreateItemInfoLink(notification.data['corpID'])
    loyaltyPoints = notification.data['amount']
    eventType = notification.data['event']
    if loyaltyPoints > 0:
        title = localization.GetByLabel('Notifications/FacWar/subjLPPayout')
    else:
        title = localization.GetByLabel('Notifications/FacWar/subjNoLPPayout')
    if eventType == logConst.eventFacWarLPCapturePayout:
        bodyLabel = 'Notifications/FacWar/bodyLPCapturePayout'
    elif eventType == logConst.eventFacWarLPMissionPayout:
        bodyLabel = 'Notifications/FacWar/bodyLPMissionPayout'
    elif eventType == logConst.eventFacWarLPDungeonPayout:
        if loyaltyPoints > 0:
            bodyLabel = 'Notifications/FacWar/bodyLPDungeonPayout'
        else:
            bodyLabel = 'Notifications/FacWar/bodyNoLPDungeonPayout'
    elif eventType == logConst.eventFacWarLPDungeonDefensivePayout:
        if loyaltyPoints > 0:
            bodyLabel = 'Notifications/FacWar/bodyLPDungeonDefensivePayout'
        else:
            bodyLabel = 'Notifications/FacWar/bodyNoLPDungeonDefensivePayout'
    else:
        bodyLabel = 'Notifications/FacWar/bodyLPGenericPayout'
    body = localization.GetByLabel(bodyLabel, location=location, corporation=corporation, itemRefID=notification.data['itemRefID'], amount=loyaltyPoints)
    return (title, body)


def FormatFacWarLPDisqualified(notification):
    location = CreateLocationInfoLink(notification.data['locationID'], const.typeSolarSystem)
    corporation = CreateItemInfoLink(notification.data['corpID'])
    title = localization.GetByLabel('Notifications/FacWar/subjLPDisqualified')
    eventType = notification.data['event']
    if eventType == logConst.eventFacWarLPCapturePayout:
        bodyLabel = 'Notifications/FacWar/bodyLPCaptureDisqualified'
    elif eventType == logConst.eventFacWarLPDungeonPayout:
        bodyLabel = 'Notifications/FacWar/bodyLPDungeonDisqualified'
    elif eventType == logConst.eventFacWarLPDungeonDefensivePayout:
        bodyLabel = 'Notifications/FacWar/bodyLPDefensiveDungeonDisqualified'
    else:
        bodyLabel = 'Notifications/FacWar/bodyGenericLPDisqualified'
    disqType = notification.data['disqualificationType']
    if disqType == const.rewardIneligibleReasonInvalidGroup:
        disqLabel = 'Notifications/FacWar/DisqualifiedReasonInvalidGroup'
    elif disqType == const.rewardIneligibleReasonShipCloaked:
        disqLabel = 'Notifications/FacWar/DisqualifiedReasonShipCloaked'
    elif disqType == const.rewardIneligibleReasonNotInRange:
        disqLabel = 'Notifications/FacWar/DisqualifiedReasonNotInRange'
    elif disqType == const.rewardIneligibleReasonNoISKLost:
        disqLabel = 'Notifications/FacWar/DisqualifiedReasonNoISKLost'
    else:
        disqLabel = 'UI/Generic/Unknown'
    reason = localization.GetByLabel(disqLabel)
    body = localization.GetByLabel(bodyLabel, location=location, corporation=corporation, amount=notification.data['amount'], reason=reason)
    return (title, body)


def _GetIndustryTeamDict(d):
    numBids = 5
    return {'location': CreateLocationInfoLink(d.data['solarSystemID'], const.typeSolarSystem),
     'amount': evefmt.FmtISK(d.data['yourAmount'], 0),
     'totalAmount': evefmt.FmtISK(d.data['totalIsk'], 0),
     'teamName': ConstructName(*d.data['teamNameInfo']),
     'numBids': min(numBids, len(d.data['systemBids'])),
     'bids': GetBidsForLocalization(d.data['systemBids'], lambda charID, iskAmount: localization.GetByLabel('Notifications/IndustryTeamContributorItem', charID=charID, iskAmount=evefmt.FmtISK(iskAmount)), numBids)}


def _FormatFriendlyFireChangeStarted(d):
    return {'characterName': CreateItemInfoLink(d.data['charID']),
     'corporationName': CreateItemInfoLink(d.data['corpID']),
     'dueDate': d.data['timeFinished']}


def _FormatFriendlyFireCompleted(d):
    return {'corporationName': CreateItemInfoLink(d.data['corpID'])}


formatters = {notificationTypeOldLscMessages: ('Notifications/subjLegacy', 'Notifications/bodyLegacy'),
 notificationTypeCharTerminationMsg: ('Notifications/subjCharacterTermination', 'Notifications/bodyCharacterTermination', ParamCharacterTerminationNotification),
 notificationTypeCharMedalMsg: ('Notifications/subjCharacterMedal', 'Notifications/bodyCharacterMedal', ParamCharacterMedalNotification),
 notificationTypeAllMaintenanceBillMsg: ('Notifications/subjMaintenanceBill', 'Notifications/bodyMaintenanceBill', lambda d: {'allianceName': CreateItemInfoLink(d.data['allianceID'])}),
 notificationTypeAllWarDeclaredMsg: FormatAllWarDeclared,
 notificationTypeAllWarCorpJoinedAllianceMsg: ('Notifications/subjWarCorpJoinAlliance', 'Notifications/bodyWarCorpJoinAlliance', lambda d: {'alliance': CreateItemInfoLink(d.data['allianceID']),
                                                'corporation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeAllyJoinedWarDefenderMsg: ('Notifications/subjWarAllyJoinedWar', 'Notifications/bodyWarAllyJoinedWarDefender', lambda d: {'ally': CreateItemInfoLink(d.data['allyID']),
                                             'aggressor': CreateItemInfoLink(d.data['aggressorID']),
                                             'time': d.data['startTime']}),
 notificationTypeAllyJoinedWarAggressorMsg: ('Notifications/subjWarAllyJoinedWar', 'Notifications/bodyWarAllyJoinedWarAggressor', lambda d: {'ally': CreateItemInfoLink(d.data['allyID']),
                                              'defender': CreateItemInfoLink(d.data['defenderID']),
                                              'time': d.data['startTime']}),
 notificationTypeAllyJoinedWarAllyMsg: ('Notifications/subjWarAllyJoinedWar', 'Notifications/bodyWarAllyJoinedWarAlly', lambda d: {'ally': CreateItemInfoLink(d.data['allyID']),
                                         'defender': CreateItemInfoLink(d.data['defenderID']),
                                         'aggressor': CreateItemInfoLink(d.data['aggressorID']),
                                         'time': d.data['startTime']}),
 notificationTypeMercOfferedNegotiationMsg: ('Notifications/subjMercOfferedContract', 'Notifications/bodyMercOfferedContract', lambda d: {'merc': CreateItemInfoLink(d.data['mercID']),
                                              'defender': CreateItemInfoLink(d.data['defenderID']),
                                              'aggressor': CreateItemInfoLink(d.data['aggressorID']),
                                              'iskOffered': evefmt.FmtISK(d.data['iskValue'])}),
 notificationTypeWarSurrenderOfferMsg: ('Notifications/subjWarSurrenderOffer', 'Notifications/bodyWarSurrenderOffer', lambda d: {'owner1': CreateItemInfoLink(d.data['ownerID1']),
                                         'owner2': CreateItemInfoLink(d.data['ownerID1']),
                                         'iskOffered': evefmt.FmtISK(d.data['iskValue'])}),
 notificationTypeWarSurrenderDeclinedMsg: ('Notifications/subjWarSurrenderDeclined', 'Notifications/bodyWarSurrenderDeclined', lambda d: {'owner': CreateItemInfoLink(d.data['ownerID']),
                                            'iskOffered': evefmt.FmtISK(d.data['iskValue'])}),
 notificationTypeAllyContractCancelled: ('Notifications/subjWarAllyContractCancelled', 'Notifications/bodyWarAllyContractCancelled', lambda d: {'defender': CreateItemInfoLink(d.data['defenderID']),
                                          'aggressor': CreateItemInfoLink(d.data['aggressorID']),
                                          'time': fmtutil.FmtDate(d.data['timeFinished'])}),
 notificationTypeWarAllyOfferDeclinedMsg: ('Notifications/subjWarAllyOfferDeclined', 'Notifications/bodyWarAllyOfferDeclined', lambda d: {'defender': CreateItemInfoLink(d.data['defenderID']),
                                            'aggressor': CreateItemInfoLink(d.data['aggressorID']),
                                            'ally': CreateItemInfoLink(d.data['allyID']),
                                            'char': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeAllWarSurrenderMsg: ('Notifications/subjWarSurender', 'Notifications/bodyWarSunrender', ParamAllWarNotification),
 notificationTypeAllWarRetractedMsg: ('Notifications/subjWarRetracts', 'Notifications/bodyWarRetract', ParamAllWarNotification),
 notificationTypeAllWarInvalidatedMsg: ('Notifications/subjWarConcordInvalidates', 'Notifications/bodyWarConcordInvalidates', ParamAllWarNotification),
 notificationTypeCharBillMsg: FormatBillNotification,
 notificationTypeCorpAllBillMsg: FormatBillNotification,
 notificationTypeBillOutOfMoneyMsg: ('Notifications/subjBillOutOfMoney', 'Notifications/bodyBillOutOfMoney', lambda d: {'billType': cfg.billtypes.Get(d.data['billTypeID']).billTypeName}),
 notificationTypeBillPaidCharMsg: ('Notifications/subjBillPaid', 'Notifications/bodyBillPaid'),
 notificationTypeBillPaidCorpAllMsg: ('Notifications/subjBillPaid', 'Notifications/bodyBillPaid'),
 notificationTypeBountyClaimMsg: ('Notifications/subjBountyPayment', 'Notifications/bodyBountyPayment'),
 notificationTypeCloneActivationMsg: ('Notifications/subjCloneActivated', 'Notifications/bodyCloneActivated', PramCloneActivationNotification),
 notificationTypeCloneActivationMsg2: ('Notifications/subjCloneActivated2', 'Notifications/bodyCloneActivated2', ParamCloneActivation2Notification),
 notificationTypeCorpAppNewMsg: ('Notifications/subjCorpApplicationNew', 'Notifications/bodyApplicationNew'),
 notificationTypeCorpAppRejectMsg: ('Notifications/subjCorpAppRejected', 'Notifications/bodyCorpAppRejected', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpAppRejectCustomMsg: ('Notifications/subjCorpAppRejected', 'Notifications/bodyCorpAppCustomRejected', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID']),
                                           'customMessage': d.data['customMessage']}),
 notificationTypeCorpAppAcceptMsg: ('Notifications/subjCorpAppAccepted', 'Notifications/bodyCorpAppAccepted', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCharAppAcceptMsg: ('Notifications/subjCharAppAccepted', 'Notifications/bodyCharAppAccepted', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCharAppRejectMsg: ('Notifications/subjCharAppRejected', 'Notifications/bodyCharAppRejected', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCharAppWithdrawMsg: ('Notifications/subjCharAppWithdrawn', 'Notifications/bodyCharAppWithdrawn', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpAppInvitedMsg: ('Notifications/subjCorpAppInvited', 'Notifications/bodyCorpAppInvited', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeDustAppAcceptedMsg: ('Notifications/subjDustAppAccepted', 'Notifications/bodyDustAppAccepted', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpKicked: ('Notifications/Corporations/KickedTitle', 'Notifications/Corporations/KickedBody', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpTaxChangeMsg: ('Notifications/subjCorpTaxRateChange', 'Notifications/bodyCorpTaxRateChange', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpNewsMsg: FormatCorpNewsNotification,
 notificationTypeCharLeftCorpMsg: ('Notifications/subjCharLeftCorp', 'Notifications/bodyCharLeftCorp', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpNewCEOMsg: ('Notifications/subjCEOQuit', 'Notifications/bodyCEOQuit', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpLiquidationMsg: ('Notifications/subjCorpLiquidation', 'Notifications/bodyCorpLiquidation', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpDividendMsg: ('Notifications/subjCorpPayoutDividends', 'Notifications/bodyLegacy', ParamFmtCorpDividendNotification),
 notificationTypeCorpVoteMsg: ('Notifications/subjCorpVote', 'Notifications/bodyLegacy'),
 notificationTypeCorpVoteCEORevokedMsg: ('Notifications/subjCEORollRevoked', 'Notifications/bodyCEORollRevoked', lambda d: {'corporationName': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCorpWarDeclaredMsg: ('Notifications/subjWarDeclare', 'Notifications/bodyWarDeclare', ParamAllWarNotificationWithCost),
 notificationTypeCorpWarFightingLegalMsg: ('Notifications/subjWarDeclare', 'Notifications/bodyWarLegal', ParamAllWarNotificationWithCost),
 notificationTypeCorpWarSurrenderMsg: ('Notifications/subjWarSurender', 'Notifications/bodyWarSunrender', ParamAllWarNotification),
 notificationTypeCorpWarRetractedMsg: ('Notifications/subjWarRetracts', 'Notifications/bodyWarRetract', ParamAllWarNotification),
 notificationTypeCorpWarInvalidatedMsg: ('Notifications/subjWarConcordInvalidates', 'Notifications/bodyWarConcordInvalidates', ParamAllWarNotification),
 notificationTypeContainerPasswordMsg: ('Notifications/subjContainerPasswordChanged', 'Notifications/bodyContainerPasswordChanged', ParamContainerPasswordNotification),
 notificationTypeCustomsMsg: ('Notifications/subjContrabandConfiscation', 'Notifications/bodyContrabandConfiscation', ParamCustomsNotification),
 notificationTypeInsuranceFirstShipMsg: ('Notifications/subjNoobShip', 'Notifications/bodyNoobShip', ParamInsuranceFirstShipNotification),
 notificationTypeInsurancePayoutMsg: ('Notifications/subjInsurancePayout', 'Notifications/bodyInsurancePayout', ParamFmtInsurancePayout),
 notificationTypeInsuranceInvalidatedMsg: ('Notifications/subjInsuranceInvalid', 'Notifications/bodyInsuranceInvalid', ParamInsuranceInvalidatedNotification),
 notificationTypeSovAllClaimFailMsg: ('Notifications/subjSovClaimFailed', 'Notifications/bodyLegacy', ParamSovAllClaimFailNotification),
 notificationTypeSovCorpClaimFailMsg: ('Notifications/subjSovClaimFailed', 'Notifications/bodyLegacy', ParamSovAllClaimFailNotification),
 notificationTypeSovAllBillLateMsg: ('Notifications/subjSovBillLate', 'Notifications/bodySovBillLate', lambda d: {'corporation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeSovCorpBillLateMsg: ('Notifications/subjSovBillLate', 'Notifications/bodySovBillLate', lambda d: {'corporation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeSovAllClaimLostMsg: ('Notifications/subjSovAllianceClaimLost', 'Notifications/bodySovAllianceClaimLost'),
 notificationTypeSovCorpClaimLostMsg: ('Notifications/subjSovCorporationClaimLost', 'Notifications/bodySovCorporationClaimLost'),
 notificationTypeSovAllClaimAquiredMsg: ('Notifications/subjSovClaimAquiredAlliance', 'Notifications/bodySovClaimAquiredAlliance', lambda d: {'corporation': CreateItemInfoLink(d.data['corpID']),
                                          'alliance': CreateItemInfoLink(d.data['allianceID'])}),
 notificationTypeSovCorpClaimAquiredMsg: ('Notifications/subjSovClaimAquiredCorporation', 'Notifications/bodySovClaimAquiredCorporation', lambda d: {'corporation': CreateItemInfoLink(d.data['corpID']),
                                           'alliance': CreateItemInfoLink(d.data['allianceID'])}),
 notificationTypeAllAnchoringMsg: ('Notifications/subjPOSAnchored', 'Notifications/bodyPOSAnchored', ParamAllAnchoringNotification),
 notificationTypeAllStructVulnerableMsg: ('Notifications/subjSovVulnerable', 'Notifications/bodySovVulnerable'),
 notificationTypeAllStrucInvulnerableMsg: ('Notifications/subjSovNotVulnerable', 'Notifications/bodySovNotVulnerable'),
 notificationTypeSovDisruptorMsg: ('Notifications/subjSovDisruptionDetected', 'Notifications/bodySovDisruptionDetected'),
 notificationTypeCorpStructLostMsg: ('Notifications/subjInfraStructureLost', 'Notifications/bodyInfraStructureLost'),
 notificationTypeCorpOfficeExpirationMsg: ('Notifications/SubjCorpOfficeExpires', 'Notifications/bodyCorpOfficeExpires', ParamCorpOfficeExpiration),
 notificationTypeCloneRevokedMsg1: ('Notifications/subjClone', 'Notifications/bodyCloneRevoked1', lambda d: {'managerStation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCloneMovedMsg: ('Notifications/subjClone', 'Notifications/bodyCloneMoved', lambda d: {'corporation': CreateItemInfoLink(d.data['charsInCorpID']),
                                  'managerStation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeCloneRevokedMsg2: ('Notifications/subjClone', 'Notifications/bodyCloneRevoke2', lambda d: {'managerStation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeInsuranceExpirationMsg: ('Notifications/subjInsuranceExpired', 'Notifications/bodyInsuranceExpired'),
 notificationTypeInsuranceIssuedMsg: ('Notifications/subjInsuranceIssued', 'Notifications/bodyInsuranceIssued', lambda d: {'typeID2': d.data['typeID']}),
 notificationTypeJumpCloneDeletedMsg1: ('Notifications/subjCloneJumpImplantDestruction', 'Notifications/bodyCloneJumpImplantDestruction', ParamJumpCloneDeleted1Notification),
 notificationTypeJumpCloneDeletedMsg2: ('Notifications/subjCloneJumpImplantDestruction', 'Notifications/bodyCloneJumpImplantDestruction', ParamJumpCloneDeleted2Notification),
 notificationTypeFWCorpJoinMsg: ('Notifications/subjFacWarCorpJoin', 'Notifications/bodyFacWarCorpJoin', ParamFmtFactionWarfareCorps),
 notificationTypeFWCorpLeaveMsg: ('Notifications/subjFacWarCorpLeave', 'Notifications/bodyFacWarCorpLeave', ParamFmtFactionWarfareCorps),
 notificationTypeFWCorpKickMsg: ('Notifications/subjFacWarCorpKicked', 'Notifications/bodyFacWarCorpKicked', ParamFmtFactionWarfareCorps),
 notificationTypeFWCharKickMsg: ('Notifications/subjFacWarCharKicked', 'Notifications/bodyFacWarCharKicked', ParamFmtFactionWarfareCorps),
 notificationTypeFWAllianceKickMsg: ('Notifications/subjFacWarAllianceKicked', 'Notifications/bodyFacWarAllianceKicked', ParamFmtFactionWarfareAlliances),
 notificationTypeFWCorpWarningMsg: ('Notifications/subjFacWarCorpWarrning', 'Notifications/bodyFacWarCorpWarrning', ParamFmtFactionWarfareCorps),
 notificationTypeFWCharWarningMsg: ('Notifications/subjFacWarCharWarrning', 'Notifications/bodyFacWarCharWarrning', ParamFmtFactionWarfareCorps),
 notificationTypeFWAllianceWarningMsg: ('Notifications/subjFacWarCorpWarrning', 'Notifications/bodyFacWarAllianceWarrning', ParamFmtFactionWarfareAlliances),
 notificationTypeFWCharRankLossMsg: FormatFWCharRankLossNotification,
 notificationTypeFWCharRankGainMsg: FormatFWCharRankGainNotification,
 notificationTypeAgentMoveMsg: ('Notifications/subjLegacy', 'Notifications/bodyLegacy'),
 notificationTypeTransactionReversalMsg: ('Notifications/subjMassReversal', 'Notifications/bodyLegacy'),
 notificationTypeReimbursementMsg: FormatShipReimbursementMessage,
 notificationTypeLocateCharMsg: FormatLocateCharNotification,
 notificationTypeResearchMissionAvailableMsg: ('Notifications/subjResearchMissionAvailable', 'Notifications/bodyResearchMissionAvailable'),
 notificationTypeMissionOfferExpirationMsg: FormatMissionOfferExpiredNotification,
 notificationTypeMissionTimeoutMsg: ('Notifications/subjMissionTimeout', 'Notifications/bodyMissionTimeout'),
 notificationTypeStoryLineMissionAvailableMsg: ('Notifications/subjStoryLineMissionAvilable', 'Notifications/bodyLegacy', ParamStoryLineMissionAvailableNotification),
 notificationTypeTowerAlertMsg: FormatTowerAlertNotification,
 notificationTypeTowerResourceAlertMsg: FormatTowerResourceAlertNotification,
 notificationTypeStationAggressionMsg1: ('Notifications/subjOutpostAgression', 'Notifications/bodyOutpostAgression', ParamStationAggression1Notification),
 notificationTypeStationStateChangeMsg: ('Notifications/subjLegacy', 'Notifications/bodyOutpostService', ParamStationStateChangeNotification),
 notificationTypeStationConquerMsg: ('Notifications/subjOutpostConquered', 'Notifications/bodyOutpostConquered', ParamStationConquerNotification),
 notificationTypeStationAggressionMsg2: ('Notifications/subjOutpostAgressed', 'Notifications/bodyOutpostAgressed', ParamStationAggression2Notification),
 notificationTypeFacWarCorpJoinRequestMsg: ('Notifications/subjFacWarCorpJoinRequest', 'Notifications/bodyFacWarCorpJoinRequest', ParamFmtFactionWarfareCorps),
 notificationTypeFacWarCorpLeaveRequestMsg: ('Notifications/subjFacWarCorpLeaveRequest', 'Notifications/bodyFacWarCorpLeaveRequest', ParamFmtFactionWarfareCorps),
 notificationTypeFacWarCorpJoinWithdrawMsg: ('Notifications/subjFacWarCorpJoinWithdraw', 'Notifications/bodyFacWarCorpJoinWithdraw', ParamFmtFactionWarfareCorps),
 notificationTypeFacWarCorpLeaveWithdrawMsg: ('Notifications/subjFacWarCorpLeaveWithdraw', 'Notifications/bodyjFacWarCorpLeaveWithdraw', ParamFmtFactionWarfareCorps),
 notificationTypeSovereigntyTCUDamageMsg: ('Notifications/subjSovTCUDamaged', 'Notifications/bodySovTCUDamaged', ParamFmtSovDamagedNotification),
 notificationTypeSovereigntySBUDamageMsg: ('Notifications/subjSovSBUDamaged', 'Notifications/bodySovSBUDamaged', ParamFmtSovDamagedNotification),
 notificationTypeSovereigntyIHDamageMsg: ('Notifications/subjSovIHDamaged', 'Notifications/bodySovIHDamaged', ParamFmtSovDamagedNotification),
 notificationTypeContactAdd: ('Notifications/subjContactAdd', 'Notifications/bodyContactAdd', lambda d: {'messageText': d.data.get('message', ''),
                               'level': GetRelationshipName(d.data['level'])}),
 notificationTypeContactEdit: ('Notifications/subjContactEdit', 'Notifications/bodyContactEdit', lambda d: {'messageText': d.data.get('message', ''),
                                'level': GetRelationshipName(d.data['level'])}),
 notificationTypeIncursionCompletedMsg: ('Notifications/subjIncursionComplete', 'Notifications/bodyIncursionComplete', ParamIncursionCompletedNotification),
 notificationTypeTutorialMsg: FormatTutorialNotification,
 notificationTypeOrbitalAttacked: ('Notifications/subjOrbitalAttacked', 'Notifications/bodyOrbitalAttacked', FormatOrbitalAttackedNotification),
 notificationTypeOrbitalReinforced: ('Notifications/subjOrbitalReinforced', 'Notifications/bodyOrbitalReinforced', FormatOrbitalReinforcedNotification),
 notificationTypeOwnershipTransferred: ('Notifications/subjOwnershipTransferred', 'Notifications/bodyOwnershipTransferred'),
 notificationTypeFacWarLPPayoutKill: ('Notifications/FacWar/subjLPPayout', 'Notifications/FacWar/bodyLPPayoutKill', lambda d: {'location': CreateLocationInfoLink(d.data['locationID'], const.typeSolarSystem),
                                       'victim': CreateItemInfoLink(d.data['charRefID']),
                                       'corporation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeFacWarLPDisqualifiedKill: ('Notifications/FacWar/subjLPDisqualified', 'Notifications/FacWar/bodyLPDisqualifiedKill', lambda d: {'location': CreateLocationInfoLink(d.data['locationID'], const.typeSolarSystem),
                                             'victim': CreateItemInfoLink(d.data['charRefID']),
                                             'corporation': CreateItemInfoLink(d.data['corpID'])}),
 notificationTypeFacWarLPPayoutEvent: FormatFacWarLPPayout,
 notificationTypeFacWarLPDisqualifiedEvent: FormatFacWarLPDisqualified,
 notificationTypeBountyYourBountyClaimed: ('Notifications/subjBountyYourBountyClaimed', 'Notifications/bodyBountyYourBountyClaimed', lambda d: {'victim': CreateItemInfoLink(d.data['victimID']),
                                            'bountyPaid': evefmt.FmtISK(d.data['bounty'], 0)}),
 notificationTypeBountyPlacedChar: ('Notifications/subjBountyPlacedChar', 'Notifications/bodyBountyPlacedChar', lambda d: {'bountyPlacer': CreateItemInfoLink(d.data['bountyPlacerID']),
                                     'amount': evefmt.FmtISK(d.data['bounty'], 0)}),
 notificationTypeBountyPlacedCorp: ('Notifications/subjBountyPlacedCorp', 'Notifications/bodyBountyPlacedCorp', lambda d: {'bountyPlacer': CreateItemInfoLink(d.data['bountyPlacerID']),
                                     'amount': evefmt.FmtISK(d.data['bounty'], 0)}),
 notificationTypeBountyPlacedAlliance: ('Notifications/subjBountyPlacedAlliance', 'Notifications/bodyBountyPlacedAlliance', lambda d: {'bountyPlacer': CreateItemInfoLink(d.data['bountyPlacerID']),
                                         'amount': evefmt.FmtISK(d.data['bounty'], 0)}),
 notificationTypeKillRightAvailable: ('Notifications/subjKillRightSale', 'Notifications/bodyKillRightSale', lambda d: {'charName': CreateItemInfoLink(d.data['charID']),
                                       'amount': evefmt.FmtISK(d.data['price'], 0),
                                       'availableToName': CreateItemInfoLink(d.data['toEntityID'])}),
 notificationTypeKillRightAvailableOpen: ('Notifications/subjKillRightSaleOpen', 'Notifications/bodyKillRightSaleOpen', lambda d: {'charName': CreateItemInfoLink(d.data['charID']),
                                           'amount': evefmt.FmtISK(d.data['price'], 0)}),
 notificationTypeKillRightEarned: ('Notifications/subjKillRightEarned', 'Notifications/bodyKillRightEarned', lambda d: {'charName': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeKillRightUsed: ('Notifications/subjKillRightUsed', 'Notifications/bodyKillRightUsed', lambda d: {'charName': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeKillRightUnavailable: ('Notifications/subjKillRightUnavailable', 'Notifications/bodyKillRightUnavailable', lambda d: {'charName': CreateItemInfoLink(d.data['charID']),
                                         'availableToName': CreateItemInfoLink(d.data['toEntityID'])}),
 notificationTypeKillRightUnavailableOpen: ('Notifications/subjKillRightUnavailableAll', 'Notifications/bodyKillRightUnavailableAll', lambda d: {'charName': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeDeclareWar: ('Notifications/subjDeclareWar', 'Notifications/bodyDeclareWar', lambda d: {'defenderName': CreateItemInfoLink(d.data['defenderID']),
                               'entityName': CreateItemInfoLink(d.data['entityID']),
                               'charName': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeOfferedSurrender: ('Notifications/subjOfferedSurrender', 'Notifications/bodyOfferedSurrender', lambda d: {'entityName': CreateItemInfoLink(d.data['entityID']),
                                     'offeredName': CreateItemInfoLink(d.data['offeredID']),
                                     'charName': CreateItemInfoLink(d.data['charID']),
                                     'iskOffer': evefmt.FmtISK(d.data['iskValue'], 0)}),
 notificationTypeAcceptedSurrender: ('Notifications/subjAcceptedSurrender', 'Notifications/bodyAcceptedSurrender', lambda d: {'entityName': CreateItemInfoLink(d.data['entityID']),
                                      'offeringName': CreateItemInfoLink(d.data['offeringID']),
                                      'charName': CreateItemInfoLink(d.data['charID']),
                                      'iskOffer': evefmt.FmtISK(d.data['iskValue'], 0)}),
 notificationTypeMadeWarMutual: ('Notifications/subjMadeWarMutual', 'Notifications/bodyMadeWarMutual', lambda d: {'enemyName': CreateItemInfoLink(d.data['enemyID']),
                                  'charName': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeRetractsWar: ('Notifications/subjRetractsWar', 'Notifications/bodyRetractsWar', lambda d: {'enemyName': CreateItemInfoLink(d.data['enemyID']),
                                'charName': CreateItemInfoLink(d.data['charID'])}),
 notificationTypeOfferedToAlly: ('Notifications/subjOfferedToAlly', 'Notifications/bodyOfferedToAlly', lambda d: {'defenderName': CreateItemInfoLink(d.data['defenderID']),
                                  'enemyName': CreateItemInfoLink(d.data['enemyID']),
                                  'charName': CreateItemInfoLink(d.data['charID']),
                                  'iskOffer': evefmt.FmtISK(d.data['iskValue'], 0)}),
 notificationTypeAcceptedAlly: ('Notifications/subjAcceptedAlly', 'Notifications/bodyAcceptedAlly', lambda d: {'allyName': CreateItemInfoLink(d.data['allyID']),
                                 'enemyName': CreateItemInfoLink(d.data['enemyID']),
                                 'charName': CreateItemInfoLink(d.data['charID']),
                                 'iskOffer': evefmt.FmtISK(d.data['iskValue'], 0),
                                 'joinTime': fmtutil.FmtDate(d.data['time'])}),
 notificationTypeDistrictAttacked: ('Notifications/subjDistrictAttacked', 'Notifications/bodyDistrictAttacked', lambda d: {'DistrictName': localization.GetImportantByLabel('UI/Locations/LocationDistrictFormatter', solarSystemID=d.data['solarSystemID'], romanCelestialIndex=fmtutil.IntToRoman(d.data['celestialIndex']), districtIndex=d.data['districtIndex']),
                                     'BattleTime': fmtutil.FmtDate(d.data['startDate']),
                                     'AttackingCorporation': CreateItemInfoLink(d.data['attackerID'])}),
 notificationTypeBattlePunishFriendlyFire: ('Notifications/subjBattlePunishFriendlyFire', 'Notifications/bodyBattlePunishFriendlyFire', lambda d: {'corporationName': CreateItemInfoLink(d.data['corporationID']),
                                             'standingsChange': d.data['standingsChange'],
                                             'hours': d.data['hours']}),
 notificationTypeBountyESSTaken: ('Notifications/subjBountyESSTaken', 'Notifications/bodyBountyESSTaken', lambda d: {'charName': CreateItemInfoLink(d.data['charID']),
                                   'totalAmount': evefmt.FmtISK(d.data['totalIsk'], 0),
                                   'iskAmount': evefmt.FmtISK(d.data['myIsk'], 0)}),
 notificationTypeBountyESSShared: ('Notifications/subjBountyESSShared', 'Notifications/bodyBountyESSShared', lambda d: {'charName': CreateItemInfoLink(d.data['charID']),
                                    'totalAmount': evefmt.FmtISK(d.data['totalIsk'], 0),
                                    'iskAmount': evefmt.FmtISK(d.data['myIsk'], 0)}),
 notificationTypeIndustryTeamAuctionWon: ('Notifications/subjIndustryTeamAuctionWon', 'Notifications/bodyIndustryTeamAuctionWon', lambda d: _GetIndustryTeamDict(d)),
 notificationTypeIndustryTeamAuctionLost: ('Notifications/subjIndustryTeamAuctionLost', 'Notifications/bodyIndustryTeamAuctionLost', lambda d: _GetIndustryTeamDict(d)),
 notificationTypeCorpFriendlyFireEnableTimerStarted: ('Notifications/subjCorpFriendlyFireEnableTimerStarted', 'Notifications/bodyCorpFriendlyFireEnableTimerStarted', _FormatFriendlyFireChangeStarted),
 notificationTypeCorpFriendlyFireDisableTimerStarted: ('Notifications/subjCorpFriendlyFireDisableTimerStarted', 'Notifications/bodyCorpFriendlyFireDisableTimerStarted', _FormatFriendlyFireChangeStarted),
 notificationTypeCorpFriendlyFireEnableTimerCompleted: ('Notifications/subjCorpFriendlyFireEnableTimerCompleted', 'Notifications/bodyCorpFriendlyFireEnableTimerCompleted', _FormatFriendlyFireCompleted),
 notificationTypeCorpFriendlyFireDisableTimerCompleted: ('Notifications/subjCorpFriendlyFireDisableTimerCompleted', 'Notifications/bodyCorpFriendlyFireDisableTimerCompleted', _FormatFriendlyFireCompleted)}

def Format(notification):
    """
        Format the notification into a (subject, body) tuple
        Notification must contain at least typeID (as int) and data (as dict)
    """
    if notification.typeID in formatters:
        try:
            if type(notification.data) in types.StringTypes:
                notification.data = yaml.load(notification.data, Loader=yaml.CSafeLoader)
            if type(formatters[notification.typeID]) is types.TupleType:
                if type(notification.data) is types.DictType:
                    notification.data['notification_senderID'] = notification.senderID
                    notification.data['notification_receiverID'] = notification.receiverID
                    notification.data['notification_created'] = notification.created
                    if len(formatters[notification.typeID]) > 2:
                        funcDict = formatters[notification.typeID][2](notification)
                        if type(funcDict) is types.DictType:
                            notification.data.update(funcDict)
                        else:
                            log.LogException('Parameter Processor failed to return a Dic of data for formatter typeID=%s' % notification.typeID)
                    subject = localization.GetByLabel(formatters[notification.typeID][0], **notification.data)
                    body = localization.GetByLabel(formatters[notification.typeID][1], **notification.data)
                else:
                    log.LogException('No formatter found for typeID=%s %s' % (notification.typeID, type(notification.data)))
                    subject = localization.GetByLabel('Notifications/subjBadNotificationMessage')
                    body = localization.GetByLabel('Notifications/bodyBadNotificationMessage', id=notification.notificationID)
            else:
                subject, body = formatters[notification.typeID](notification)
        except Exception as e:
            log.LogException('Error processing notification=%s, error=%s' % (str(notification), e))
            sys.exc_clear()
            subject = localization.GetByLabel('Notifications/subjBadNotificationMessage')
            body = localization.GetByLabel('Notifications/bodyBadNotificationMessage', id=notification.notificationID)

        return (subject, body)
    else:
        log.LogException('No formatter found for typeID=%s' % notification.typeID)
        subject = localization.GetByLabel('Notifications/subjBadNotificationMessage')
        body = localization.GetByLabel('Notifications/bodyBadNotificationMessage', id=notification.notificationID)
        return (subject, body)
