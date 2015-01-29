#Embedded file name: spacecomponents/common/components\bountyEscrow.py
from collections import OrderedDict, defaultdict
from itertoolsext import Bundle
from operator import itemgetter
from inventorycommon.types import GetBasePrice

def GetPriceByTagTypeID(typeIDs):
    return {typeID:GetBasePrice(typeID) for typeID in typeIDs}


class TagCalculator(object):

    def __init__(self, iskValueByTypeID):
        self.iskValueByTypeID = OrderedDict(sorted(((typeID, value) for typeID, value in iskValueByTypeID.iteritems()), key=itemgetter(1), reverse=True))

    def GetIskAsTags(self, bountyAmount):
        return {tagTypeID:tagCount for tagTypeID, tagCount, _ in self.GetTagInfo(bountyAmount)}

    def GetAllTagsAndAmount(self, bountyAmount):
        tagInfoByTypeID = {typeID:(tagCount, iskAmount) for typeID, tagCount, iskAmount in self.GetTagInfo(bountyAmount)}
        ret = []
        for typeID, iskValue in self.iskValueByTypeID.iteritems():
            if typeID in tagInfoByTypeID:
                tagCount, iskAmount = tagInfoByTypeID[typeID]
                ret.append((typeID, tagCount, iskValue))
            else:
                ret.append((typeID, 0, iskValue))

        return ret

    def GetTagInfo(self, bountyAmount):
        bountyLeft = bountyAmount
        tags = []
        for typeID, value in self.iskValueByTypeID.iteritems():
            if value <= bountyLeft:
                tagCount = int(bountyLeft) / int(value)
                iskAmount = tagCount * value
                tags.append((typeID, tagCount, iskAmount))
                bountyLeft -= iskAmount

        return tags


STATE_UNLOCKING = 'Unlocking'
STATE_UNLOCKED = 'Unlocked'
STATE_LOCKED = 'Locked'
STATE_SPAWNING_TAGS = 'SpawningTags'

def GetSlimStateForUnlocking(timeStamp, duration, shipID):
    return (STATE_UNLOCKING,
     timeStamp,
     duration,
     shipID)


def GetSlimStateForLocked():
    return (STATE_LOCKED,)


def IsUnlocking(state):
    return state[0] == STATE_UNLOCKING


def IsLocked(state):
    return state[0] == STATE_LOCKED


def GetUnlockingTimeStamp(state):
    return state[1]


def GetUnlockingDuration(state):
    return state[2]


def GetUnlockingShipID(state):
    return state[3]
