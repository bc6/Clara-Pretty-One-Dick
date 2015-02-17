#Embedded file name: workers\util.py
from collections import defaultdict
from operator import itemgetter
import random
import string
from workers import SPECIALIZATION_TREE, Specialization, SPE_LABELS
from workers.specializationGroups import SPECIALIZATION_GROUPS
from workers import AUCTION_DISTANCE_COST, AUCTION_WORMHOLE_COST
from inventorycommon.util import IsWormholeSystem

def GetSolarSystems():
    return cfg.mapSystemCache.keys()


def BuildTeamName(solarSystemID, activityID):
    randomName = ''.join((random.choice(string.ascii_uppercase) for x in range(3)))
    randomName += ''.join((str(random.randint(0, 9)) for x in range(2)))
    return randomName


def GetSpecialization(specializationID):
    node = SPECIALIZATION_TREE[specializationID]
    return Specialization(node.nodeID, 0, 0, node.childrenIDs, SPE_LABELS[node.nodeID], SPECIALIZATION_GROUPS[node.nodeID])


def GetBidsBySolarSystem(bids):
    solarSystemBids = defaultdict(float)
    for solarSystemID, systemBids in bids.iteritems():
        solarSystemBids[solarSystemID] += sum((amount for amount in systemBids.itervalues()))

    return solarSystemBids


def GetMyBidsBySolarSystem(charID, bids):
    solarSystemBids = defaultdict(float)
    for solarSystemID, systemBids in bids.GetBids().iteritems():
        for bidCharID, bid in systemBids.iteritems():
            if bidCharID == charID:
                solarSystemBids[solarSystemID] += sum((amount for amount in systemBids.itervalues()))

    return solarSystemBids


def GetHighestBid(bids):
    solarSystemBids = bids.GetBidsBySolarSystem()
    try:
        return max(solarSystemBids)[0]
    except ValueError:
        return 0


def GetGroupNamesFromSpeciality(specialityID):
    groupNames = []
    groups = SPECIALIZATION_GROUPS[specialityID]
    for groupID in groups:
        groupName = cfg.invgroups.Get(groupID).name
        groupNames.append(groupName)

    return '\n'.join(groupNames)


def GetBidsForLocalization(bids, labelGenerator, numBids):
    return '\n'.join((labelGenerator(charID, amount) for charID, amount in sorted(bids.iteritems(), key=itemgetter(1), reverse=True)[:numBids]))


def GetDistanceCost(pathfinder, fromSolarSystemID, toSolarSystemID):
    """
    Takes in server/client pathfinder and int: from/to solar systems.
    Returns set cost if system is a wormhole system.
    Else returns distance cost based on jump count distance.
    """
    if IsWormholeSystem(toSolarSystemID):
        return AUCTION_WORMHOLE_COST
    return AUCTION_DISTANCE_COST * pathfinder.GetJumpCount(fromSolarSystemID, toSolarSystemID)


def GetSpecializationForGroup(groupID):
    for specializationID in SPECIALIZATION_TREE[0].childrenIDs:
        for subSpecializationID in SPECIALIZATION_TREE[specializationID].childrenIDs:
            if groupID in SPECIALIZATION_GROUPS[subSpecializationID]:
                return (specializationID, subSpecializationID)

    return (None, None)


def GetBaseSpecializationForGroup(groupID):
    return GetSpecializationForGroup(groupID)[0]


def GetSubSpecializationForGroup(groupID):
    return GetSpecializationForGroup(groupID)[1]
