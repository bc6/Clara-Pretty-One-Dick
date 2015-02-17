#Embedded file name: probescanning\formations.py
import geo2
from math import cos, sin, pi, asin
from collections import namedtuple
from probescanning.const import AU
import probescanning.customFormations as customFormations
Formation = namedtuple('Formation', ['offsets', 'defaultSize'])
SPREAD_FORMATION = -1
PINPOINT_FORMATION = -2
CUSTOM_FORMATION = -3
MIN_PROBES_NEEDED = 8

def _GetSpreadFormation():
    vertDev = 0.25
    centerRadius = cos(asin(vertDev))
    offsets = [(0, vertDev, 0), (0, -vertDev, 0)]
    defaultSize = 16 * AU
    centerOffsetRadius = 0.75 + centerRadius
    getXValue = lambda i: centerOffsetRadius * cos(i * pi / 3)
    getZValue = lambda i: centerOffsetRadius * sin(i * pi / 3)
    for i in xrange(6):
        offsets.append((getXValue(i), 0, getZValue(i)))

    return [ (geo2.Vec3Scale(offset, defaultSize), defaultSize) for offset in offsets ]


def _GetPinPointFormation():
    offsets = [(0, 0, 0), (0, 0.5, 0), (0, -0.5, 0)]
    getXValue = lambda i: 0.5 * cos(i * 2 * pi / 5)
    getZValue = lambda i: 0.5 * sin(i * 2 * pi / 5)
    defaultSize = 4 * AU
    for i in xrange(5):
        offsets.append((getXValue(i), 0, getZValue(i)))

    return [ (geo2.Vec3Scale(offset, defaultSize), defaultSize) for offset in offsets ]


formations = {SPREAD_FORMATION: _GetSpreadFormation(),
 PINPOINT_FORMATION: _GetPinPointFormation()}

def GetFormation(formationID):
    """
        formationID can be either SPREAD_FORMATION or PINPOINT_FORMATION.
        Size is in AUs
        Returns list of tuples with the x, y and z coordinates.
    """
    if formationID < 0:
        return formations[formationID]
    else:
        return customFormations.GetCustomFormation(formationID)[1]


def GetProbeInfoInFormation(formationID, index):
    return GetFormation(formationID)[index]


def GetNumberOfProbesInFormation(formationID):
    return len(GetFormation(formationID))
