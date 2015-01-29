#Embedded file name: eve/client/script/environment/spaceObject\stargate.py
import uthread
import blue
import eve.common.lib.appConst as const
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject

class Stargate(SpaceObject):

    def __init__(self):
        SpaceObject.__init__(self)
        self.lastActivationTime = 0
        self.activeStateDuration = 15 * const.SEC
        self.isDeactivationThreadRunning = False
        self.isActive = False
        self.deactivationCurve = None
        self.activationCurve = None
        self.lightningTransform = None
        self.arrivalCurve = None
        self.departureCurve = None

    def _SetupStargateEffects(self, model):
        gateStateChild = None
        for child in model.children:
            if child.name == 'FX_JUMPGATE':
                for each in child.children:
                    if each.name == 'GATE_STATE':
                        gateStateChild = each
                    elif each.name == 'FX_DEPARTURE':
                        self.departureCurve = each.curveSets[0]
                    elif each.name == 'FX_ARRIVAL':
                        self.arrivalCurve = each.curveSets[0]

            elif child.name == 'BOLTS':
                self.lightningTransform = child

        if gateStateChild is None:
            return
        for each in gateStateChild.curveSets:
            if each.name == 'ACTIVATE_STATE':
                self.activationCurve = each
            elif each.name == 'DEACTIVATE_STATE':
                self.deactivationCurve = each

    def LoadModel(self, fileName = None, loadedModel = None):
        filename = self.typeData.get('graphicFile')
        model = self._LoadModelResource(filename)
        if model is not None:
            self._SetupStargateEffects(model)
        SpaceObject.LoadModel(self, loadedModel=model)
        self.SetStaticRotation()

    def Assemble(self):
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        self.SetupAmbientAudio(u'worldobject_jumpgate_atmo_play')

    def _ActivationCooldown(self):
        """ Jumpgates should deactivate some time after they were last activated """

        def _deactivateThread():
            timeNow = blue.os.GetSimTime()
            while not self.released and timeNow < self.lastActivationTime + self.activeStateDuration:
                blue.synchro.SleepUntilSim(self.lastActivationTime + self.activeStateDuration)
                timeNow = blue.os.GetSimTime()

            self.isDeactivationThreadRunning = False
            self.isActive = False
            if not self.released:
                if self.lightningTransform is not None:
                    self.lightningTransform.display = False
                if self.deactivationCurve is not None:
                    self.deactivationCurve.Play()
                    self.deactivationCurve.StopAfter(self.deactivationCurve.GetMaxCurveDuration())

        if not self.isDeactivationThreadRunning:
            self.isDeactivationThreadRunning = True
            uthread.new(_deactivateThread)

    def Activate(self):
        """ Play activation animation """
        self.lastActivationTime = blue.os.GetSimTime()
        if self.activationCurve is not None and not self.isActive:
            self.activationCurve.Play()
            self.activationCurve.StopAfter(self.activationCurve.GetMaxCurveDuration())
        if self.lightningTransform is not None:
            self.lightningTransform.display = True
        self.isActive = True
        self._ActivationCooldown()

    def JumpDeparture(self):
        """ Play jump animation """
        if self.departureCurve is not None:
            self.departureCurve.Play()
            self.departureCurve.StopAfter(self.departureCurve.GetMaxCurveDuration())

    def JumpArrival(self):
        """ Play jump animation """
        if self.arrivalCurve is not None:
            self.arrivalCurve.Play()
            self.arrivalCurve.StopAfter(self.arrivalCurve.GetMaxCurveDuration())
