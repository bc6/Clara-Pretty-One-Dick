#Embedded file name: carbon/common/script/world\objectLightOverride.py
"""
provides a class for working with light overrides for world space objects
"""

class ObjectLightOverride(object):
    __guid__ = 'world.ObjectLightOverride'

    def __init__(self, worldSpaceTypeID, objectID, lightID, row):
        """
        note: all the optional parameters should be float values, other than color which should be
        a 4 -float tuple and direction should be a 3-float tuple
        """
        self.worldSpaceTypeID = worldSpaceTypeID
        self.objectID = objectID
        self.lightID = lightID
        self.mainRow = row

    def GetWorldSpaceTypeID(self):
        return self.worldSpaceTypeID

    def GetObjectID(self):
        return self.objectID

    def GetLightID(self):
        return self.lightID

    def GetRadius(self):
        return self.mainRow.radius

    def GetSpecularRadiusMultiplier(self):
        return self.mainRow.specularRadiusMultiplier

    def GetPointLight(self):
        return self.mainRow.pointLight

    def GetSpotlightConeAngle(self):
        return self.mainRow.spotlightConeAngle

    def GetDistanceFalloffKneeValue(self):
        return self.mainRow.distanceFalloffKneeValue

    def GetDistanceFalloffKneeRadius(self):
        return self.mainRow.distanceFalloffKneeRadius

    def GetColor(self):
        """
        returns color as a (r, g, b, a) tuple of floats
        """
        if self.mainRow.colorR is None or self.mainRow.colorG is None or self.mainRow.colorB is None or self.mainRow.colorA is None:
            return
        return (self.mainRow.colorR,
         self.mainRow.colorG,
         self.mainRow.colorB,
         self.mainRow.colorA)

    def GetDirection(self):
        """
        returns light direction as a (x, y, z) tuple
        """
        if self.mainRow.directionX is None or self.mainRow.directionY is None or self.mainRow.directionZ is None:
            return
        return (self.mainRow.directionX, self.mainRow.directionY, self.mainRow.directionZ)
