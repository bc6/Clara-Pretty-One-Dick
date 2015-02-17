#Embedded file name: crimewatch\util.py
import hashlib
import const
import collections
import math

def CalculateTagRequirementsForSecIncrease(startSecStatus, requestedSecStatus):
    """
    Calculates the tag types and quantities required to increase a character's security status from startSecStatus to requestedSecStatus.
    Returns an OrderedDict of the form { tagTypeID : numTagsRequired }. Elements are ordered in the sequence in which they must be applied
    """
    if not const.characterSecurityStatusMin < requestedSecStatus <= const.characterSecurityStatusMax:
        raise RuntimeError('CalculateTagRequirementsForSecIncrease called with out-of-range requestedSecStatus', requestedSecStatus)
    if requestedSecStatus <= startSecStatus:
        raise RuntimeError('CalculateTagRequirementsForSecIncrease: requestedSecStatus must be higher than startSecStatus', requestedSecStatus, startSecStatus)
    requiredTags = collections.OrderedDict()
    secStatus = startSecStatus
    while secStatus < requestedSecStatus:
        for tagTypeID, (minSecStatus, maxSecStatus) in const.securityLevelsPerTagType.iteritems():
            if minSecStatus <= secStatus < maxSecStatus:
                numTagsRequired = int(math.ceil((min(requestedSecStatus, maxSecStatus) - secStatus) / const.securityGainPerTag))
                requiredTags[tagTypeID] = numTagsRequired
                secStatus += numTagsRequired * const.securityGainPerTag
                break
        else:
            raise RuntimeError('CalculateTagRequirementsForSecIncrease: No tags available for reaching requestedSecStatus', requestedSecStatus, secStatus, startSecStatus)

    return requiredTags


def IsItemFreeForAggression(targetGroupID):
    """
    Checks if group/category for item are flagged for free aggression.
    """
    return targetGroupID in const.targetGroupsWithNoPenalties


def GetKillReportHashValue(kill):
    string = '%s%s%s%s' % (kill.victimCharacterID,
     kill.finalCharacterID,
     kill.victimShipTypeID,
     kill.killTime)
    return hashlib.sha1(string).hexdigest()
