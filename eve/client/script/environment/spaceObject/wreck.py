#Embedded file name: eve/client/script/environment/spaceObject\wreck.py
import random
import blue
import uthread
import trinity
import geo2
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject

class Wreck(SpaceObject):

    def Assemble(self):
        self.UnSync()

    def SetRandomRotation(self):
        if hasattr(self.model, 'modelRotationCurve'):
            self.model.modelRotationCurve = trinity.TriRotationCurve()
            quat = geo2.QuaternionRotationSetYawPitchRoll(random.random() * 6.28, random.random() * 6.28, random.random() * 6.28)
            self.model.modelRotationCurve.value = quat
        else:
            self.model.rotationCurve = None
            self.model.rotation.SetYawPitchRoll(random.random() * 6.28, random.random() * 6.28, random.random() * 6.28)
        self.model.display = 1

    def SetBallRotation(self, ball):
        self.model.rotationCurve = None
        if getattr(ball.model, 'modelRotationCurve', None) is not None:
            self.model.modelRotationCurve = ball.model.modelRotationCurve
        else:
            self.model.modelRotationCurve = trinity.TriRotationCurve()
            quat = geo2.QuaternionRotationSetYawPitchRoll(ball.yaw, ball.pitch, ball.roll)
            self.model.modelRotationCurve.value = quat
        ball.wreckID = self.id
        self.model.display = 0
        uthread.pool('Wreck::DisplayWreck', self.DisplayWreck, 2000)

    def Prepare(self):
        SpaceObject.Prepare(self)
        michelle = self.sm.GetService('michelle')
        slimItem = self.typeData.get('slimItem')
        explodedShipBall = michelle.GetBall(slimItem.launcherID)
        if explodedShipBall is not None and getattr(explodedShipBall, 'model', None) is not None:
            self.SetBallRotation(explodedShipBall)
        else:
            self.SetRandomRotation()

    def Display(self, display = 1, canYield = True):
        if display and getattr(self, 'delayedDisplay', 0):
            return
        SpaceObject.Display(self, display, canYield)

    def DisplayWreck(self, duration = None):
        """
        Waits for duration and displays the model afet that time.
        
        @param duration: Time in ms to wait before displaying the model.
        """
        if duration:
            blue.pyos.synchro.SleepSim(duration)
        if self.model is not None and self.model.display == 0:
            self.model.display = 1

    def Explode(self):
        if self.exploded:
            return False
        self.exploded = True
        return 0.0
