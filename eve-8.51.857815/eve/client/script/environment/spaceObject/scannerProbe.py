#Embedded file name: eve/client/script/environment/spaceObject\scannerProbe.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import blue
import uthread
import trinity
import random

class ScannerProbe(SpaceObject):

    def __init__(self):
        SpaceObject.__init__(self)

    def Release(self, origin = None):
        SpaceObject.Release(self)

    def FakeWarp(self):
        blue.pyos.synchro.SleepSim(random.randint(100, 1000))
        url = 'res:/Model/Effect3/ProbeWarp.red'
        gfx = trinity.Load(url)
        if gfx.__bluetype__ != 'trinity.EveRootTransform':
            root = trinity.EveRootTransform()
            root.children.append(gfx)
            root.name = url
            gfx = root
        gfx.translationCurve = self
        scene = self.spaceMgr.GetScene()
        if scene is not None:
            scene.objects.append(gfx)
        uthread.pool('ScannerProbe::HideBall', self.HideBall)
        uthread.pool('ScannerProbe::DelayedRemove', self.DelayedRemove, 3000, self.model)
        uthread.pool('ScannerProbe::DelayedRemove', self.DelayedRemove, 3000, gfx)

    def DelayedRemove(self, duration, gfx):
        if gfx is None:
            return
        if duration != 0:
            blue.pyos.synchro.SleepSim(duration)
        if hasattr(gfx, 'translationCurve'):
            gfx.translationCurve = None
        scene = self.spaceMgr.GetScene()
        if scene is not None:
            scene.objects.fremove(gfx)

    def HideBall(self):
        blue.pyos.synchro.SleepSim(500)
        if self.model:
            self.model.display = 0

    def OnSlimItemUpdated(self, newItem):
        if not getattr(newItem, 'warpingAway', 0):
            return
        uthread.pool('ScanProbe::FakeWarp', self.FakeWarp)

    def Assemble(self):
        SpaceObject.Assemble(self)
        warpDisruptionStartTime = self.typeData['slimItem'].warpDisruptionStartTime
        if warpDisruptionStartTime is None:
            return
        godmaStateManager = self.sm.GetService('godma').GetStateManager()
        godmaType = godmaStateManager.GetType(self.typeID)
        effectRadius = godmaType.warpScrambleRange
        if effectRadius:
            scale = self.model.scaling[0] / 20000.0 * effectRadius
            self.model.scaling = (scale, scale, scale)
        timeNow = blue.os.GetSimTime()
        if blue.os.TimeDiffInMs(warpDisruptionStartTime, timeNow) < 10000.0:
            for cs in self.model.curveSets:
                cs.Play()

    def Explode(self):
        explosionURL = 'res:/Emitter/explosion_end.blue'
        scale = 0.2 + random.random() * 0.1
        return SpaceObject.Explode(self, explosionURL, scaling=scale)
