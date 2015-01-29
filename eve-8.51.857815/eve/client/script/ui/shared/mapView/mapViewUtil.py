#Embedded file name: eve/client/script/ui/shared/mapView\mapViewUtil.py
from eve.client.script.ui.shared.mapView.mapViewConst import MARKERID_MYPOS, MARKERID_BOOKMARK, MARKER_TYPES
from eve.client.script.ui.shared.maps import mapcommon
import sys
import geo2
from math import sin, cos

def GetBoundingSphereRadiusCenter(vectors, isFlatten = False):
    minX = sys.maxint
    minY = sys.maxint
    minZ = sys.maxint
    maxX = -sys.maxint
    maxY = -sys.maxint
    maxZ = -sys.maxint
    for x, y, z in vectors:
        minX = min(minX, x)
        minY = min(minY, y)
        minZ = min(minZ, z)
        maxX = max(maxX, x)
        maxY = max(maxY, y)
        maxZ = max(maxZ, z)

    if isFlatten:
        minY = maxY = 0.0
    maxBound = (maxX, maxY, maxZ)
    minBound = (minX, minY, minZ)
    center = geo2.Vec3Scale(geo2.Vec3Add(minBound, maxBound), 0.5)
    offset = geo2.Vec3Scale(geo2.Vec3Subtract(minBound, maxBound), 0.5)
    return (center, geo2.Vec3Length(offset))


def GetTranslationFromParentWithRadius(radius, camera):
    camangle = camera.fieldOfView * 0.5
    translationFromParent = max(15.0, radius / sin(camangle) * cos(camangle))
    return translationFromParent


def SolarSystemPosToMapPos(position):
    x, y, z = position
    return (ScaleSolarSystemValue(x), ScaleSolarSystemValue(y), ScaleSolarSystemValue(z))


def WorldPosToMapPos(position):
    x, y, z = position
    return (x * -mapcommon.STARMAP_SCALE, y * -mapcommon.STARMAP_SCALE, z * mapcommon.STARMAP_SCALE)


def ScaledPosToMapPos(pos):
    x, y, z = pos
    return (x * -1, y * -1, z)


def ScaleSolarSystemValue(value):
    return value * mapcommon.STARMAP_SCALE * 100


def IsDynamicMarkerType(itemID):
    try:
        if itemID[0] in MARKER_TYPES:
            return True
    except:
        return False


def IsLandmark(itemID):
    return itemID and itemID < 0
