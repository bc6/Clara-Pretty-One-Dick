#Embedded file name: probescanning\util.py
import operator
import geo2
import probescanning.const
EXPLORATION_SITES = (probescanning.const.probeScanGroupSignatures, probescanning.const.probeScanGroupAnomalies)

def IsIntersecting(pos1, radius1, pos2, radius2):
    distance = geo2.Vec3Distance(pos1, pos2)
    if distance < 0.0:
        return False
    if distance > radius1 + radius2:
        return False
    if radius1 > distance + radius2 or radius2 > distance + radius1:
        return False
    return True


def IsPerfectResult(result):
    return result.certainty >= probescanning.const.probeResultPerfect and isinstance(result.data, tuple)


def IsCacheable(result):
    return IsExplorationSite(result)


def IsExplorationSite(result):
    return result.scanGroupID in EXPLORATION_SITES


def ShouldCacheResult(result):
    return IsCacheable(result) and IsPerfectResult(result)


def GetCenter(positions):
    if not positions:
        return (0, 0, 0)
    accPos = geo2.Vector((0, 0, 0))
    for pos in positions:
        accPos += pos

    return geo2.Vec3Scale(accPos, 1.0 / len(positions))


def GetRangeStepAndSizeFromScanRange(desiredRange, scanRanges):
    """
        Gives you the index of the in scanRanges that is closest to the
        scanRange supplied and the associated scanRange
    """
    diffs = ((abs(desiredRange - scanRange), scanRange) for i, scanRange in enumerate(scanRanges))
    i, (_, scanRange) = min(enumerate(diffs), key=operator.itemgetter(1))
    return (i + 1, scanRange)


def GetOffsetPositions(positions):
    center = GetCenter(positions)
    return [ geo2.Vec3Subtract(pos, center) for pos in positions ]
