#Embedded file name: evewar\util.py
"""
Helper module for features related to wars.
"""
import blue

def GetWarEntity(corporationID, allianceID):
    """
    Gets list of wars for corporation based on whether it is in alliance or not.
    """
    if allianceID:
        return allianceID
    else:
        return corporationID


def HasActiveOrPendingWars(wars):
    """
    Returns true or false for corporation or alliance being at war or to be started.
    """
    for war in wars.itervalues():
        if war.timeFinished is None or war.timeFinished > blue.os.GetWallclockTime():
            return True

    return False


def IsWarInHostileState(row, currentTime):
    if row.timeFinished is None or currentTime < row.timeFinished:
        if currentTime > row.timeStarted:
            return 1
    return 0


def IsAtWar(wars, entities, currentTime):
    for war in wars:
        if war.declaredByID not in entities:
            continue
        if not IsWarInHostileState(war, currentTime):
            continue
        if war.againstID in entities:
            return war.warID
        for allyID, row in war.allies.iteritems():
            if allyID in entities:
                if row.timeStarted < currentTime < row.timeFinished:
                    return war.warID
                break

    return False
