#Embedded file name: eve/client/script/environment/spaceObject\satellite.py
"""
The satellite is a small object that appears in orbit around
planets whenever a player ship enters the space above a district.

We use this model for displaying a physical marker as well as controlling
the UI shown on the planet surface.
"""
import uthread
import eve.common.lib.appConst as const
from eve.client.script.environment.spaceObject.LargeCollidableStructure import LargeCollidableStructure

class Satellite(LargeCollidableStructure):

    def Assemble(self):
        """
        Called when the space object is brought into existance.
        """
        LargeCollidableStructure.Assemble(self)
        slimItem = self.typeData.get('slimItem')
        self.districtID = slimItem.districtID
        direction = self.FindClosestPlanetDir()
        self.AlignToDirection(direction)
        proximity = self.sm.GetService('godma').GetTypeAttribute(slimItem.typeID, const.attributeProximityRange)
        self.AddProximitySensor(proximity, 2, 0, False)

    def Release(self):
        LargeCollidableStructure.Release(self)
        uthread.new(self.sm.GetService('district').DisableDistrict, self.districtID)

    def DoProximity(self, violator, entered):
        """
        We use a proximity check to determine if we should open the district UI.
        """
        if violator == session.shipid and getattr(self, 'districtID', None) is not None:
            if entered:
                uthread.new(self.sm.GetService('district').EnableDistrict, self.districtID)
            else:
                uthread.new(self.sm.GetService('district').DisableDistrict, self.districtID)
