#Embedded file name: eve/client/script/environment/spaceObject\wormhole.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import blue
import uthread
import const
DESTINATION_SUBPART_NAME = 'otherside'
MAXSHIPMASS_SUBPART_START = 'shipmass_'
MAXSHIPMASS_SUBPART_END = {const.WH_SLIM_MAX_SHIP_MASS_SMALL: 'small',
 const.WH_SLIM_MAX_SHIP_MASS_MEDIUM: 'medium',
 const.WH_SLIM_MAX_SHIP_MASS_LARGE: 'large',
 const.WH_SLIM_MAX_SHIP_MASS_VERYLARGE: 'extralarge'}

class Wormhole(SpaceObject):

    def __init__(self):
        SpaceObject.__init__(self)
        self.targetNebulaPath = None
        self.wormholeSize = 1.0
        self.wormholeAge = 1

    def Release(self, origin = None):
        SpaceObject.Release(self)

    def OnSlimItemUpdated(self, newItem):
        self.typeData['slimItem'] = newItem
        if self.wormholeSize != newItem.wormholeSize:
            self.LogInfo('Wormhole size has changed. Updating graphics')
            uthread.pool('wormhole:SetWormholeSize', self.SetWormholeSize, newItem.wormholeSize)
        if self.wormholeAge != newItem.wormholeAge:
            self.SetWobbleSpeed()

    def SetWormholeSize(self, newSize):
        self.PlaySound('worldobject_wormhole_shrinking_play')

        def Lerp(min, max, s):
            return min + s * (max - min)

        self.SetWobbleSpeed(10.0)
        self.LogInfo('Setting wormhole size from', self.wormholeSize, 'to', newSize)
        blue.pyos.synchro.SleepSim(1000)
        if self.model is None:
            return
        i = 0
        time = 2000.0
        start, ndt = blue.os.GetSimTime(), 0.0
        while ndt < 1.0:
            ndt = max(ndt, min(blue.os.TimeDiffInMs(start, blue.os.GetSimTime()) / time, 1.0))
            val = Lerp(self.wormholeSize, newSize, ndt)
            sz = val
            self.model.scaling = (sz, sz, sz)
            blue.pyos.synchro.Yield()
            i += 1
            if self.model is None:
                return

        self.wormholeSize = newSize
        blue.pyos.synchro.SleepSim(2000)
        self.SetWobbleSpeed()

    def SetWobbleSpeed(self, spd = None):
        if self.model is None:
            return
        curve = self.FindCurveSet('Wobble')
        slimItem = self.typeData.get('slimItem')
        if curve is None or slimItem is None:
            return
        defaultWobble = 1.0
        if slimItem.wormholeAge == 2:
            defaultWobble += 4.0
        elif slimItem.wormholeAge == 1:
            defaultWobble += 1.0
        spd = spd or defaultWobble
        self.LogInfo('Setting Wobble speed to', spd)
        curve.scale = spd

    def Assemble(self):
        slimItem = self.typeData.get('slimItem')
        self.wormholeSize = slimItem.wormholeSize
        self.model.scaling = (self.wormholeSize, self.wormholeSize, self.wormholeSize)
        self.targetNebulaPath = self.spaceMgr.GetNebulaTextureForType(slimItem.nebulaType)
        for subPart in self.model.children:
            if subPart.name.lower().startswith(DESTINATION_SUBPART_NAME):
                cubeTextureList = subPart.Find('trinity.TriTextureCubeParameter')
                if len(cubeTextureList) > 0:
                    cubeTextureList[0].resourcePath = self.targetNebulaPath

        self.maxShipJumpSize = int(slimItem.maxShipJumpMass)
        for subPart in self.model.children:
            if subPart.name.lower().startswith(MAXSHIPMASS_SUBPART_START):
                subPart.display = subPart.name.lower() == MAXSHIPMASS_SUBPART_START + MAXSHIPMASS_SUBPART_END.get(self.maxShipJumpSize, '')

        self.SetWobbleSpeed()
        self.LogInfo('Wormhole - Assemble : wormholeSize=', slimItem.wormholeSize, ', nebulaType=', slimItem.nebulaType, ', wormholeAge=', slimItem.wormholeAge, ', maxShipJumpMass=', slimItem.maxShipJumpMass)
        self.LogInfo('I will hand this wormhole the following texture:', self.targetNebulaPath)
        self.model.boundingSphereRadius = self.radius
        isCloseToCollapse = self.wormholeSize < 1.0
        if isCloseToCollapse:
            ambient = 'worldobject_wormhole_unstable_play'
        else:
            ambient = 'worldobject_wormhole_ambience_play'
        self.SetupAmbientAudio(unicode(ambient))

    def FindCurveSet(self, name):
        if self.model is None:
            return
        for b in self.model.Find('trinity.TriCurveSet'):
            if b.name == name:
                return b

    def Explode(self):
        if self.exploded:
            return False
        self.exploded = True
        if self.model is None:
            return False
        uthread.worker('wormhole:PlayDeath', self.PlayDeath)
        return 4000

    def PlayDeath(self):
        self.PlaySound('worldobject_wormhole_collapse_play')
        self.SetWobbleSpeed(20.0)
        blue.pyos.synchro.SleepSim(1000)
        collapse = self.FindCurveSet('Collapse')
        if collapse:
            collapse.Play()

    def PlaySound(self, event):
        if self.model is None:
            return
        if hasattr(self.model, 'observers'):
            for obs in self.model.observers:
                obs.observer.SendEvent(unicode(event))
                return

        self.LogError("Wormhole can't play sound. Sound observer not found")
