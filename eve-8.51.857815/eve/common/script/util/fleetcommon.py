#Embedded file name: eve/common/script/util\fleetcommon.py
"""
This file contains declarations and common helper functions for the
Fleet system for use in both the client and the server
"""
from evefleet.const import *

def IsSuperior(member, myself):
    if member.charID == myself.charID:
        return True
    if myself.role == const.fleetRoleLeader:
        return False
    if member.role == const.fleetRoleLeader:
        return True
    if myself.squadID > 0:
        if member.role != const.fleetRoleMember and member.wingID == myself.wingID:
            return True
    return False


def IsSubordinateOrEqual(member, myself):
    if member.charID == myself.charID:
        return True
    if myself.role == const.fleetRoleLeader:
        return True
    if myself.squadID > 0:
        if member.squadID == myself.squadID:
            return True
    if myself.role == const.fleetRoleWingCmdr:
        if member.wingID == myself.wingID:
            return True
    return False


def ShouldSendBroadcastTo(member, myself, scope):
    if scope == BROADCAST_ALL:
        return True
    if scope == BROADCAST_UP and IsSuperior(member, myself):
        return True
    if scope == BROADCAST_DOWN and IsSubordinateOrEqual(member, myself):
        return True
    return False


def LogBroadcast(messageName, scope, itemID):
    """
    Write a broadcast event into the info gathering service including intended recipients
    """
    for idx in range(len(ALL_BROADCASTS)):
        if ALL_BROADCASTS[idx] == messageName:
            break

    sm.GetService('infoGatheringMgr').LogInfoEventFromServer(const.infoEventFleetBroadcast, idx, int_1=1, int_2=scope)
    sm.GetService('fleetObjectHandler').LogPlayerEvent('Broadcast', messageName, scope, itemID)
    sm.GetService('fleetObjectHandler').LogPlayerEventJson('Broadcast', broadcastName=messageName, scope=scope, targetID=itemID)


def IsOpenToCorp(fleet):
    return fleet.get('inviteScope', 0) & INVITE_CORP == INVITE_CORP


def IsOpenToAlliance(fleet):
    return fleet.get('inviteScope', 0) & INVITE_ALLIANCE == INVITE_ALLIANCE


def IsOpenToMilitia(fleet):
    return fleet.get('inviteScope', 0) & INVITE_MILITIA == INVITE_MILITIA


def IsOpenToPublic(fleet):
    return fleet.get('inviteScope', 0) & INVITE_PUBLIC == INVITE_PUBLIC


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('fleetcommon', locals())
