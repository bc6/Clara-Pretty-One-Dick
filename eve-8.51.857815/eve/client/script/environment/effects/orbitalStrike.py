#Embedded file name: eve/client/script/environment/effects\orbitalStrike.py
from eve.client.script.environment.effects.GenericEffect import STOP_REASON_DEFAULT
from eve.client.script.environment.effects.turrets import StandardWeapon
import eve.client.script.environment.spaceObject.planet as planet
import uthread

class OrbitalStrike(StandardWeapon):
    __guid__ = 'effects.OrbitalStrike'
    TYPES = {const.typeTacticalEMPAmmoS: planet.ORBBOMB_IMPACT_FX_EM,
     const.typeTacticalHybridAmmoS: planet.ORBBOMB_IMPACT_FX_HYBRID,
     const.typeTacticalLaserAmmoS: planet.ORBBOMB_IMPACT_FX_LASER}

    def __init__(self, trigger, *args):
        StandardWeapon.__init__(self, trigger, *args)
        self.district = None
        if trigger.graphicInfo:
            districtSvc = sm.GetService('district')
            character = districtSvc.GetTargetBall(trigger.graphicInfo['characterID'])
            if character:
                self.district = districtSvc.GetDistrict(trigger.graphicInfo['districtID'])
                self.ballIDs = [trigger.shipID, character.id]

    def Start(self, duration):
        if not self.district:
            return
        StandardWeapon.Start(self, duration)

    def Stop(self, reason = STOP_REASON_DEFAULT):
        StandardWeapon.Stop(self)
        uthread.new(self._PlanetImpact)

    def _PlanetImpact(self):
        if self.otherTypeID not in self.TYPES:
            self.LogWarn('Ignoring orbital strike for unknown type: ', self.otherTypeID)
            return
        if self.district and self.district['planet']:
            self.district['planet'].AddExplosion(self.district['uniqueName'], self.TYPES[self.otherTypeID], 0.1)
