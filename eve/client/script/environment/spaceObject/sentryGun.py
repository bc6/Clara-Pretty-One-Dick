#Embedded file name: eve/client/script/environment/spaceObject\sentryGun.py
import random
import timecurves
import eve.client.script.environment.spaceObject.spaceObject as spaceObject
import eve.client.script.environment.model.turretSet as turretSet
import eveSpaceObject
import evegraphics.settings as gfxsettings
entityExplosionsS = ['res:/Emitter/tracerexplosion/NPCDeathS1.blue', 'res:/Emitter/tracerexplosion/NPCDeathS3.blue', 'res:/Emitter/tracerexplosion/NPCDeathS4.blue']
entityExplosionsM = ['res:/Emitter/tracerexplosion/NPCDeathM1.blue', 'res:/Emitter/tracerexplosion/NPCDeathM3.blue', 'res:/Emitter/tracerexplosion/NPCDeathM4.blue']
entityExplosionsL = ['res:/Emitter/tracerexplosion/NPCDeathL1.blue', 'res:/Emitter/tracerexplosion/NPCDeathL3.blue', 'res:/Emitter/tracerexplosion/NPCDeathL4.blue']
TURRET_TYPE_ID = {eveSpaceObject.gfxRaceAmarr: 462,
 eveSpaceObject.gfxRaceGallente: 569,
 eveSpaceObject.gfxRaceCaldari: 574,
 eveSpaceObject.gfxRaceMinmatar: 498,
 eveSpaceObject.gfxRaceAngel: 462,
 eveSpaceObject.gfxRaceSleeper: 4049,
 eveSpaceObject.gfxRaceJove: 4049}
TURRET_FALLBACK_TYPE_ID = 462

class SentryGun(spaceObject.SpaceObject):

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        self.modules = {}
        self.fitted = False
        self.typeID = None
        self.turretTypeID = TURRET_FALLBACK_TYPE_ID

    def Assemble(self):
        timecurves.ScaleTime(self.model, 0.9 + random.random() * 0.2)
        self.SetStaticRotation()
        raceName = self.typeData.get('sofRaceName', None)
        if raceName is not None:
            self.turretTypeID = TURRET_TYPE_ID.get(raceName, TURRET_FALLBACK_TYPE_ID)
        if gfxsettings.Get(gfxsettings.UI_TURRETS_ENABLED):
            self.FitHardpoints()
        self.SetupSharedAmbientAudio()

    def FitHardpoints(self, blocking = False):
        if self.fitted:
            return
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        if self.typeID is None:
            self.LogWarn('FitHardpoints - No typeID')
            return
        self.fitted = True
        self.modules = {}
        ts = turretSet.TurretSet.FitTurret(self.model, self.typeID, self.turretTypeID, 1)
        if ts is not None:
            self.modules[self.id] = ts

    def LookAtMe(self):
        if not self.model:
            return
        if not self.fitted:
            self.FitHardpoints()

    def Release(self):
        if self.released:
            return
        self.modules = None
        spaceObject.SpaceObject.Release(self)

    def Explode(self):
        explosionURL, (delay, scaling) = self.GetExplosionInfo()
        return spaceObject.SpaceObject.Explode(self, explosionURL=explosionURL, managed=True, delay=delay, scaling=scaling)
