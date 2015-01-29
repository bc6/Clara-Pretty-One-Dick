#Embedded file name: trinutils\boundingsphere.py
"""
Functions for dealing with object bounding spheres.
This allows us to have a consistent interface in our tools even though
the trinity objects have no unified interface whatsoever.
"""
import blue
import trinity
import devenv.respathutils as respathutils

class BoundingSphereRadiusZeroError(Exception):

    def __init__(self, geoResPath):
        msg = 'Bounding sphere is 0. It may have failed to rebuild properly.\n%s' % blue.paths.ResolvePath(geoResPath)
        Exception.__init__(self, msg)


def GetBoundingSphere(trinobj):
    """Returns a tuple (xyz center, radius) for the bounding
    sphere center and radius of trinobj.
    
    :raises: `AttributeError` if unsupported type.
    """
    try:
        return (trinobj.boundingSphereCenter, trinobj.boundingSphereRadius)
    except AttributeError:
        return (trinobj.boundingSphere[:3], trinobj.boundingSphere[3])


def RebuildBoundingSphere(trinobj):
    """Rebuilds the bounding sphere on a trinity object.
    
    Note, this will **mutate trinobj** by assigning the bounding sphere,
    as well as possibly changing some things about meshes/LoDs
    (meshes need to be frozen, etc.).
    
    On failure, function will raise.
    
    Also note, **trinobj even will be mutated on failure**,
    since temporary values must be assigned before regeneration.
    This includes things like the mutation above,
    as well as the bounding sphere center/radius.
    
    :return: GetBoundingSphere(trinobj).
    """
    bt = trinobj.__bluetype__
    if bt == 'trinity.EveShip2' or bt == 'trinity.EveStation2' or bt == 'trinity.EveMobile':
        _RebuildShip(trinobj)
    elif bt == 'trinity.EveTurretSet':
        _RebuildTurret(trinobj)
    elif bt == 'trinity.EveMissile':
        _RebuildMissile(trinobj)
    elif bt == 'trinity.EveSOFDataHull':
        _RebuildSofHull(trinobj)
    else:
        raise ValueError('Unsupported type: %s' % bt)
    return GetBoundingSphere(trinobj)


def _RebuildTurret(turret):
    turret.FreezeHighDetailLOD()
    trinity.WaitForResourceLoads()
    turret.boundingSphere = (-1, -1, -1, -1)
    turret.RebuildBoundingSphere()
    if turret.boundingSphere[3] <= 0:
        raise BoundingSphereRadiusZeroError(turret.geometryResPath)


def _RebuildShip(ship):
    ship.FreezeHighDetailMesh()
    trinity.WaitForResourceLoads()
    ship.boundingSphereRadius = -1
    ship.RebuildBoundingSphereInformation()
    if ship.boundingSphereRadius <= 0:
        respath = '<No mesh>'
        if ship.meshLod:
            respath = ship.meshLod.geometryRes.highDetailResPath
        raise BoundingSphereRadiusZeroError(respath)


def _RebuildSofHull(sofhull):
    expandedPath = respathutils.ExpandResPath(sofhull.geometryResFilePath)
    hullresource = blue.resMan.GetResource(expandedPath)
    trinity.WaitForResourceLoads()
    hullresource.RecalculateBoundingSphere()
    bSphereCenter, bSphereRad = hullresource.GetBoundingSphere(0)
    sofhull.boundingSphere = (bSphereCenter[0],
     bSphereCenter[1],
     bSphereCenter[2],
     bSphereRad)


def _RebuildMissile(missile):
    missile.FreezeHighDetailMesh()
    trinity.WaitForResourceLoads()
    missile.boundingSphereRadius = -1
    missile.RebuildMissileBoundingSphere()
    if missile.boundingSphereRadius <= 0:
        res = missile.warheads[0].mesh.geometryResPath
        raise BoundingSphereRadiusZeroError(res)
