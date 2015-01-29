#Embedded file name: eve/common/script/planet\planetSurfaceCommon.py
"""
    This file is meant to contain data structures and utility methods defining
    game logic utilized on both the planetSurfaceRegistry (server) and dustPinManager (client).
"""
pinTypeInstanceRestrictions = {const.typeTestSurfaceCommandCenter: 1}
pinTypeConstructionPrerequisitesSurface = {}
pinTypeConstructionPrerequisitesOrbit = {const.typeTestSurfaceCommandCenter: []}
pinTypePlanetRestrictions = {const.typeTestSurfaceCommandCenter: [const.typePlanetEarthlike]}

def GetMaximumPinInstances(pinTypeID):
    """
        Returns the maximum number of instances of a given pin type
        permissible on a planet. If unrestricted, returns None.
    """
    restriction = pinTypeInstanceRestrictions.get(pinTypeID, None)
    if restriction < 1:
        restriction = None
    return restriction


def GetSurfaceConstructionPrerequisites(pinTypeID):
    """
        Returns a list of typeIDs which must be present on the planet surface 
        in order for a pin to be constructed. If unrestricted, returns an empty list.
    """
    return pinTypeConstructionPrerequisitesSurface.get(pinTypeID, [])


def GetValidPlanetTypesForPinType(pinTypeID):
    """
        Returns a list of planet typeIDs onto which a given DUST pin type
        may be deployed. If unrestricted, returns None.
    """
    return pinTypePlanetRestrictions.get(pinTypeID, [])


def GetOrbitalConstructionPrerequisites(pinTypeID):
    """
        Returns a list of typeIDs which must be present in the planets orbit 
        in order for a pin to be constructed. If unrestricted, returns an empty list.
    """
    return pinTypeConstructionPrerequisitesOrbit.get(pinTypeID, [])


exports = {'planetSurfaceCommon.GetMaximumPinInstances': GetMaximumPinInstances,
 'planetSurfaceCommon.GetSurfaceConstructionPrerequisites': GetSurfaceConstructionPrerequisites,
 'planetSurfaceCommon.GetValidPlanetTypesForPinType': GetValidPlanetTypesForPinType,
 'planetSurfaceCommon.GetOrbitalConstructionPrerequisites': GetOrbitalConstructionPrerequisites}
