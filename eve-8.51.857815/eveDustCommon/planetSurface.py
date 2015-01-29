#Embedded file name: eveDustCommon\planetSurface.py
"""
    This file is meant to contain data structures and utility methods defining
    game logic utilized on both the planetSurfaceRegistry (server) and dustPinManager (client) and in the DUST client.

    This file is shared between EVE and DUST so make sure you only use functionality that works in both
"""
import appConst
import time
BLUE_SEC = 10000000L
EPOCH_BLUE_TIME = 116444736000000000L

def blue_os_GetTime(gmTime = None):
    """
    We want timestamps in GM time (or UTC).  So we take the number of
    seconds since the epoch, and convert that into a blue unit and
    add it to the blue time at the epoch.. and we get a blue time.
    """
    if gmTime is None:
        gmTime = time.time()
    return EPOCH_BLUE_TIME + long(gmTime * BLUE_SEC)


ATTACK_TIMEOUT = 9000000000L

def HasAttackTimedOut(attackTimestamp, now = None):
    """
        Checks to see if an attack has timed out.
    """
    if now is None:
        now = blue_os_GetTime()
    return now > attackTimestamp


def GetConflictState(conflicts, corpID = None):
    """
        Common method to return the conflict state of a given base.
        If a corpID is assigned only conflicts initiated by that corpID will be taken into account.
    """
    conflictState = appConst.objectiveStateCeasefire
    for conflict in conflicts:
        if (corpID is None or corpID == conflict.attackerID) and not HasAttackTimedOut(conflict.expiryTime):
            if conflict.endTime is None:
                conflictState = appConst.objectiveStateWar

    return conflictState
