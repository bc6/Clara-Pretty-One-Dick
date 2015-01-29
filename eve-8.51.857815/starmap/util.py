#Embedded file name: starmap\util.py
from collections import namedtuple
StarmapInterest = namedtuple('StarmapInterest', ['regionID', 'constellationID', 'solarSystemID'])

def OverrideColour(initial, override):
    """
    takes as many elements as there are in override
    and overlays them on initial
    """
    i = list(initial)
    i[:len(override)] = override
    return tuple(i)


def OverrideAlpha(initial, alpha):
    return (initial[0],
     initial[1],
     initial[2],
     alpha)


def ScaleColour(initial, scale):
    return (scale * initial[0],
     scale * initial[1],
     scale * initial[2],
     initial[3])


def SelectiveIndexedIterItems(indexable, indexes):
    """
    For either a list, or a dict, yield the (index, value)
    for a given subset of valid indexes
     -> (index, indexable[index]), ...
    """
    for idx in indexes:
        yield (idx, indexable[idx])


def Pairwise(l):
    """
    takes an iterable [ 1, 2, 3 ] -> [(1,2),(2,3)]
    """
    first = True
    last = None
    for i in l:
        if not first:
            yield (last, i)
        first = False
        last = i


class SolarSystemMapInfo(object):
    __slots__ = ('regionID', 'constellationID', 'star', 'center', 'scaledCenter', 'factionID', 'neighbours', 'planetCountByType')


class RegionMapInfo(object):
    __slots__ = ('scaledCenter', 'neighbours', 'solarSystemIDs', 'constellationIDs')


class ConstellationMapInfo(object):
    __slots__ = ('regionID', 'neighbours', 'scaledCenter', 'solarSystemIDs')


class MapJumpInfo(object):
    __slots__ = ('jumpType', 'fromSystemID', 'toSystemID', 'adjustedFromVector', 'adjustedToVector')
