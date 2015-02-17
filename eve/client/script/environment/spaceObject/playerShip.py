#Embedded file name: eve/client/script/environment/spaceObject\playerShip.py
"""
the PlayerShip class handles ships that are controlled by players.
"""
import trinity
import math
from eve.client.script.parklife.states import lookingAt
from eve.client.script.environment.spaceObject.ship import Ship

class PlayerShip(Ship):

    def OnDamageState(self, damageState):
        """ damage state contains shield, armor and structural damage
        we will use the structural damage """
        if self.model is None:
            return
        self.SetDamageState(damageState[2])

    def IsLookedAt(self):
        return self.id == self.sm.GetService('state').GetExclState(lookingAt)

    def SetDamageState(self, health):
        effectPosition = trinity.TriVector()
        if health > 0.8:
            for each in list(self.model.children):
                if each.name == 'autoDamage':
                    self.model.children.remove(each)

            self.burning = False
        elif not self.burning and self.IsLookedAt():
            self.burning = True
            if len(self.model.damageLocators):
                furthestBack = self.model.damageLocators[0][0]
                for locator in self.model.damageLocators:
                    locatorTranslation = locator[0]
                    if locatorTranslation[2] < furthestBack[2]:
                        furthestBack = locatorTranslation

                effectPosition = furthestBack
            scale = math.sqrt(self.model.boundingSphereRadius / 30.0)
            effect = trinity.Load('res:/Emitter/Damage/fuel_low.red')
            effect.name = 'autoDamage'
            effect.translation = effectPosition
            effect.scaling = (1, 1, 1)
            prefix = 'owner.positionDelta'
            for curveSet in effect.curveSets:
                for binding in curveSet.bindings:
                    if binding.name.startswith(prefix):
                        binding.sourceObject = self.model.positionDelta

            generators = effect.Find('trinity.Tr2RandomUniformAttributeGenerator')
            for generator in generators:
                if generator.elementType == trinity.PARTICLE_ELEMENT_TYPE.LIFETIME:
                    generator.minRange = (generator.minRange[0],
                     generator.minRange[1] * scale,
                     0,
                     0)
                    generator.maxRange = (generator.maxRange[0],
                     generator.maxRange[1] * scale,
                     0,
                     0)
                elif generator.elementType == trinity.PARTICLE_ELEMENT_TYPE.CUSTOM and generator.customName == 'sizeDynamic':
                    generator.minRange = (generator.minRange[0] * scale,
                     generator.minRange[1] * scale,
                     0,
                     0)
                    generator.maxRange = (generator.maxRange[0] * scale,
                     generator.maxRange[1] * scale,
                     0,
                     0)

            generators = effect.Find('trinity.Tr2SphereShapeAttributeGenerator')
            for generator in generators:
                generator.minRadius = generator.minRadius * scale
                generator.maxRadius = generator.maxRadius * scale

            self.model.children.append(effect)
