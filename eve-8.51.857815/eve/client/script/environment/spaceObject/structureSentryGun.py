#Embedded file name: eve/client/script/environment/spaceObject\structureSentryGun.py
import trinity
import eve.client.script.environment.model.turretSet as turretSet
from eve.client.script.environment.spaceObject.playerOwnedStructure import PlayerOwnedStructure
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import evegraphics.settings as gfxsettings
entityExplosionsS = ['res:/Emitter/tracerexplosion/NPCDeathS1.blue', 'res:/Emitter/tracerexplosion/NPCDeathS3.blue', 'res:/Emitter/tracerexplosion/NPCDeathS4.blue']
entityExplosionsM = ['res:/Emitter/tracerexplosion/NPCDeathM1.blue', 'res:/Emitter/tracerexplosion/NPCDeathM3.blue', 'res:/Emitter/tracerexplosion/NPCDeathM4.blue']
entityExplosionsL = ['res:/Emitter/tracerexplosion/NPCDeathL1.blue', 'res:/Emitter/tracerexplosion/NPCDeathL3.blue', 'res:/Emitter/tracerexplosion/NPCDeathL4.blue']

class StructureSentryGun(PlayerOwnedStructure):

    def __init__(self):
        PlayerOwnedStructure.__init__(self)
        self.modules = {}
        self.fitted = False
        self.turretTypeID = None
        self.typeID = None

    def Assemble(self):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        godmaStateManager = sm.StartService('godma').GetStateManager()
        godmaType = godmaStateManager.GetType(slimItem.typeID)
        self.turretTypeID = godmaType.gfxTurretID
        self.typeID = slimItem.typeID
        if gfxsettings.Get(gfxsettings.UI_TURRETS_ENABLED) and self.IsAnchored():
            self.FitHardpoints()

    def FitHardpoints(self, blocking = False):
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        if self.fitted:
            return
        if self.typeID is None:
            self.LogWarn('FitHardpoints - No typeID')
            return
        newTurretSet = turretSet.TurretSet.FitTurret(self.model, self.typeID, self.turretTypeID, 1)
        if newTurretSet is None:
            return
        self.fitted = True
        self.modules[self.id] = newTurretSet

    def SetBuiltStructureGraphics(self, animate = 0):
        PlayerOwnedStructure.SetBuiltStructureGraphics(self, animate)
        if gfxsettings.Get(gfxsettings.UI_TURRETS_ENABLED):
            self.FitHardpoints()

    def Release(self):
        PlayerOwnedStructure.Release(self, 'spaceObject.StructureSentryGun')

    def Explode(self):
        if not gfxsettings.Get(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED):
            return self.exploded
        if self.radius < 100.0:
            explosionURL = entityExplosionsS[self.typeID % 3]
        elif self.radius < 400.0:
            explosionURL = entityExplosionsM[self.typeID % 3]
        elif self.radius <= 900.0:
            explosionURL = entityExplosionsL[self.typeID % 3]
        if self.radius <= 900.0:
            return SpaceObject.Explode(self, explosionURL)
        if self.exploded:
            return False
        self.exploded = True
        exlosionBasePath = 'res:/Emitter/tracerexplosion/'
        if self.radius > 3000.0:
            extraPath = 'StructureDeathRadius1500.blue'
        elif self.radius > 1500.0:
            extraPath = 'StructureDeathRadius1000.blue'
        else:
            extraPath = 'StructureDeathRadius500.blue'
        explosionURL = exlosionBasePath + extraPath
        gfx = trinity.Load(explosionURL.replace('.blue', '.red'))
        if gfx is None:
            return False
        explodingObjectDisplay = [ x for x in gfx.curveSets if x.name == 'ExplodingObjectDisplay' ]
        if gfx.__bluetype__ != 'trinity.EveRootTransform':
            root = trinity.EveRootTransform()
            root.children.append(gfx)
            root.name = explosionURL
            gfx = root
        self.model.translationCurve = self
        self.model.rotationCurve = None
        gfx.translationCurve = self
        self.explosionModel = gfx
        scene = self.spaceMgr.GetScene()
        scene.objects.append(gfx)
        if len(explodingObjectDisplay):
            explodingObjectDisplay = explodingObjectDisplay[0]
            explodingObjectDisplay.bindings[0].destinationObject = self.model
            self.explosionDisplayBinding = explodingObjectDisplay.bindings[0]
        return True
