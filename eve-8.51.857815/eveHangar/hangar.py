#Embedded file name: eveHangar\hangar.py
"""
Contains utility methods to start and control animations in hangars, both FIS and WIS
"""
import geo2
import blue
import trinity
import uthread
import random
import math
racialHangarScenes = {1: 20271,
 2: 20272,
 4: 20273,
 8: 20274}
SHIP_FLOATING_HEIGHT = 360.0

class HangarTraffic:
    """
    constr
    """

    def __init__(self):
        self.threadList = []

    def AnimateTraffic(self, ship, area, shipClass):
        initialAdvance = random.random()
        while True:
            if shipClass == 'b':
                duration = random.uniform(40.0, 50.0)
            elif shipClass == 'bc':
                duration = random.uniform(20.0, 30.0)
            elif shipClass == 'c':
                duration = random.uniform(15.0, 20.0)
            elif shipClass == 'f':
                duration = random.uniform(10.0, 15.0)
            else:
                duration = random.uniform(15.0, 20.0)
            if ship.translationCurve and ship.rotationCurve and len(ship.translationCurve.keys) == 2:
                now = blue.os.GetSimTime()
                s01 = random.random()
                t01 = random.random()
                if ship.rotationCurve.value[1] < 0.0:
                    startPos = geo2.Vec3BaryCentric(area['Traffic_Start_1'], area['Traffic_Start_2'], area['Traffic_Start_3'], s01, t01)
                    endPos = geo2.Vec3BaryCentric(area['Traffic_End_1'], area['Traffic_End_2'], area['Traffic_End_3'], s01, t01)
                else:
                    startPos = geo2.Vec3BaryCentric(area['Traffic_End_1'], area['Traffic_End_2'], area['Traffic_End_3'], s01, t01)
                    endPos = geo2.Vec3BaryCentric(area['Traffic_Start_1'], area['Traffic_Start_2'], area['Traffic_Start_3'], s01, t01)
                startPos = geo2.Vec3Add(startPos, geo2.Vec3Scale(geo2.Vec3Subtract(endPos, startPos), initialAdvance))
                startKey = ship.translationCurve.keys[0]
                endKey = ship.translationCurve.keys[1]
                startKey.value = startPos
                startKey.time = 0.0
                startKey.interpolation = trinity.TRIINT_LINEAR
                endKey.value = endPos
                endKey.time = duration
                endKey.interpolation = trinity.TRIINT_LINEAR
                ship.translationCurve.extrapolation = trinity.TRIEXT_CONSTANT
                ship.translationCurve.Sort()
                ship.translationCurve.start = now
                ship.display = True
            delay = random.uniform(5.0, 15.0)
            initialAdvance = 0.0
            blue.pyos.synchro.SleepWallclock(1000.0 * (duration + delay))

    def SetupScene(self, hangarScene):
        for obj in hangarScene.objects:
            if hasattr(obj, 'PlayAnimationEx'):
                obj.PlayAnimationEx('NormalLoop', 0, 0.0, 1.0)

        for obj in hangarScene.objects:
            if '_Traffic_' in obj.name:
                obj.RebuildBoosterSet()

        trafficStartEndArea = {}
        for obj in hangarScene.objects:
            if obj.__bluetype__ == 'trinity.EveStation2':
                for loc in obj.locators:
                    if 'Traffic_Start_' in loc.name or 'Traffic_End_' in loc.name:
                        trafficStartEndArea[loc.name] = geo2.Vec3Transform((0.0, 0.0, 0.0), loc.transform)

        if len(trafficStartEndArea) == 6:
            for obj in hangarScene.objects:
                if '_Traffic_' in obj.name:
                    obj.display = False
                    obj.translationCurve = trinity.TriVectorCurve()
                    obj.translationCurve.keys.append(trinity.TriVectorKey())
                    obj.translationCurve.keys.append(trinity.TriVectorKey())
                    shipClass = ''
                    if len(obj.name) > 2:
                        shipClass = obj.name[1].lower()
                    obj.rotationCurve = trinity.TriRotationCurve()
                    if random.randint(0, 1) == 0:
                        obj.rotationCurve.value = geo2.QuaternionRotationSetYawPitchRoll(0.5 * math.pi, 0.0, 0.0)
                    else:
                        obj.rotationCurve.value = geo2.QuaternionRotationSetYawPitchRoll(-0.5 * math.pi, 0.0, 0.0)
                    uthreadObj = uthread.new(self.AnimateTraffic, obj, trafficStartEndArea, shipClass)
                    uthreadObj.context = 'HangarTraffic::SetupScene'
                    self.threadList.append(uthreadObj)

    def RemoveAudio(self, hangarScene):
        objectsToDelete = []
        for obj in hangarScene.objects:
            if obj.name.startswith('invisible_sound_locator'):
                objectsToDelete.append(obj)

        for objToDelete in objectsToDelete:
            hangarScene.objects.remove(objToDelete)

    def CleanupScene(self):
        for uthreadObj in self.threadList:
            uthreadObj.kill()

        self.threadList = []
