#Embedded file name: eve/client/script/environment/spaceObject\ship.py
from eveexceptions.exceptionEater import ExceptionEater
from inventorycommon.util import IsModularShip
import trinity
import uthread2
import uthread
import eve.common.lib.appConst as const
from eve.client.script.environment.model.turretSet import TurretSet
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
from eve.client.script.environment.spaceObject.spaceObject import BOOSTER_GFX_SND_RESPATHS
from eveSpaceObject import shipanimation
import eveSpaceObject.spaceobjaudio as spaceobjaudio
from uthread2.callthrottlers import CallCombiner
import destiny

class Ship(SpaceObject):
    __notifyevents__ = []
    _animationStates = shipanimation.shipAnimationStates

    def __init__(self):
        SpaceObject.__init__(self)
        self.activeTargetID = None
        self.fitted = False
        self.fittingThread = None
        self.turrets = []
        self.modules = {}
        self.stanceID = None
        self.lastStanceID = None
        self.cloakedCopy = None
        self.isT3LoadingLockHeld = False
        self.burning = False
        self.loadingModel = False
        self.LoadT3ShipWithThrottle = CallCombiner(self.LoadT3Ship, 1.0)

    def _LockT3Loading(self):
        uthread.Lock(self, 'LoadT3Model')
        self.isT3LoadingLockHeld = True

    def _UnlockT3Loading(self):
        if self.isT3LoadingLockHeld:
            uthread.UnLock(self, 'LoadT3Model')
            self.isT3LoadingLockHeld = False

    def LoadT3Ship(self):
        modules = self.typeData.get('slimItem').modules
        subsystems = {}
        self._LockT3Loading()
        self.loadingModel = True
        oldModel = self.model
        try:
            for _, typeID, _ in modules:
                group = cfg.invtypes.Get(typeID).Group()
                if group.categoryID == const.categorySubSystem:
                    subsystems[group.groupID] = typeID

            t3ShipSvc = self.sm.GetService('t3ShipSvc')
            model = t3ShipSvc.GetTech3ShipFromDict(self.typeID, subsystems, self.id)
            if model is not None:
                SpaceObject.LoadModel(self, None, loadedModel=model)
                self.Assemble()
            self.Display(1)
        finally:
            self.loadingModel = False
            self._UnlockT3Loading()

        if oldModel is not None:
            self.RemoveAndClearModel(oldModel)

    def IsModularShip(self):
        return IsModularShip(self.typeID)

    def LoadModel(self, fileName = None, loadedModel = None):
        if self.IsModularShip():
            uthread2.StartTasklet(self.LoadT3Ship)
        else:
            SpaceObject.LoadModel(self, fileName, loadedModel)
        self.Display(1)

    def OnSubSystemChanged(self, newSlim):
        self.typeData['slimItem'] = newSlim
        if self.model is None:
            self.LogError('OnSlimItemUpdated - no model to remove')
            return
        self.fitted = False
        uthread2.StartTasklet(self.LoadT3ShipWithThrottle)

    def GetStanceIDFromSlimItem(self, slimItem):
        if slimItem.shipStance is None:
            return
        _, _, stanceID = slimItem.shipStance
        return stanceID

    def OnSlimItemUpdated(self, slimItem):
        with ExceptionEater('ship::OnSlimItemUpdated failed'):
            self.typeData['slimItem'] = slimItem
            stanceID = self.GetStanceIDFromSlimItem(self.typeData['slimItem'])
            if stanceID != self.stanceID:
                self.lastStanceID = self.stanceID
                self.stanceID = stanceID
                if shipanimation.SetShipAnimationStance(self.model, stanceID):
                    self.TriggerAnimation('normal')

    def _SetInitialState(self):
        stanceID = self.GetStanceIDFromSlimItem(self.typeData['slimItem'])
        if stanceID is not None:
            self.stanceID = stanceID
            if shipanimation.SetShipAnimationStance(self.model, self.stanceID):
                self.TriggerAnimation('normal')
        if self.mode == destiny.DSTBALL_WARP:
            self.TriggerAnimation('warping')
            if session.shipid != self.id:
                self.sm.GetService('FxSequencer').OnSpecialFX(self.id, None, None, None, None, 'effects.WarpIn', 0, 1, 0)
        elif self.GetCurrentAnimationState() is None:
            self.TriggerAnimation('normal')

    def Assemble(self):
        if self.model is None:
            return
        self.UnSync()
        if len(self.model.damageLocators) == 0:
            self.LogError('Type', self.typeID, 'has no damage locators')
        if self.id == eve.session.shipid:
            self.FitHardpoints()
        self._SetInitialState()
        self.FitBoosters()

    def Release(self):
        self._UnlockT3Loading()
        if self.released:
            return
        if self.model is None:
            return
        self.modules = {}
        self.KillCloakedCopy()
        self.LoadT3ShipWithThrottle = None
        SpaceObject.Release(self, 'Ship')

    def KillCloakedCopy(self):
        if getattr(self, 'cloakedCopy', None) is not None:
            cloakedCopy = self.cloakedCopy
            scene = self.spaceMgr.GetScene()
            scene.objects.fremove(cloakedCopy)
            if hasattr(cloakedCopy, 'translationCurve'):
                cloakedCopy.translationCurve = None
            if hasattr(cloakedCopy, 'rotationCurve'):
                cloakedCopy.rotationCurve = None
            self.cloakedCopy = None
            self.LogInfo('Removed cloaked copy of ship')

    def LookAtMe(self):
        if not self.model:
            return
        if not self.fitted:
            self.FitHardpoints()
        audsvc = self.sm.GetServiceIfRunning('audio')
        if audsvc.active:
            lookedAt = audsvc.lastLookedAt
            if lookedAt is None:
                self.SetupAmbientAudio()
                audsvc.lastLookedAt = self
            elif lookedAt is not self:
                lookedAt.PlayGeneralAudioEvent('shipsounds_stop')
                self.SetupAmbientAudio()
                audsvc.lastLookedAt = self
            else:
                return

    def TriggerAnimation(self, state):
        if state == 'normal':
            state = shipanimation.GetAnimationStateFromStance(self.stanceID)
        SpaceObject.TriggerAnimation(self, state)
        if self.stanceID is not None and self.lastStanceID is not None:
            spaceobjaudio.PlayStateChangeAudio(self.stanceID, self.lastStanceID, self._GetGeneralAudioEntity())

    def FitBoosters(self, alwaysOn = False, enableTrails = True, isNPC = False):
        if self.typeID is None:
            return
        raceName = self.typeData.get('sofRaceName', None)
        if raceName is None:
            self.LogError('SpaceObject type %s has invaldi raceID (not set!) ' % self.typeID)
            raceName = 'generic'
        boosterSoundName = BOOSTER_GFX_SND_RESPATHS[raceName][1]
        boosterResPath = BOOSTER_GFX_SND_RESPATHS[raceName][0]
        if self.model is None:
            self.LogWarn('No model to fit boosters to on spaceobject with id = ' + str(self.id))
            return
        if not hasattr(self.model, 'boosters'):
            self.LogWarn('Model has no attribute boosters on spaceobject with id = ' + str(self.id))
            return
        if self.model.boosters is None:
            boosterFxObj = trinity.Load(boosterResPath)
            if boosterFxObj is not None:
                self.model.boosters = boosterFxObj
                self.model.RebuildBoosterSet()
        self.model.boosters.maxVel = self.maxVelocity
        self.model.boosters.alwaysOn = alwaysOn
        if not enableTrails:
            self.model.boosters.trails = None
        slimItem = self.typeData['slimItem']
        groupID = slimItem.groupID
        tmpEntity, boosterAudioEvent = spaceobjaudio.GetBoosterEmitterAndEvent(self.model, groupID, boosterSoundName)
        if tmpEntity:
            self._audioEntities.append(tmpEntity)
            dogmaAttr = const.attributeMaxVelocity
            if isNPC:
                dogmaAttr = const.attributeEntityCruiseSpeed
            velocity = self.sm.GetService('godma').GetTypeAttribute(self.typeID, dogmaAttr)
            if velocity is None:
                velocity = 1.0
            self.model.maxSpeed = velocity
            spaceobjaudio.SendEvent(tmpEntity, boosterAudioEvent)

    def EnterWarp(self):
        """
        Special behaviour when entering warp.
        """
        for t in self.turrets:
            t.EnterWarp()

        if self.stanceID is None:
            self.TriggerAnimation('warping')

    def ExitWarp(self):
        """
        Special behaviour when exiting warp.
        """
        for t in self.turrets:
            t.ExitWarp()

        if self.stanceID is None:
            self.TriggerAnimation('normal')

    def UnfitHardpoints(self):
        """
        Opposite to FitHardpoints(): it removes all turrets on this ship. Player's
        ships are the only spaceobject that need this functionality, cause they can
        re-fit at titans etc. in space!
        """
        if not self.fitted:
            return
        newModules = {}
        for key, val in self.modules.iteritems():
            if val not in self.turrets:
                newModules[key] = val

        self.modules = newModules
        del self.turrets[:]
        self.fitted = False

    def FitHardpoints(self, blocking = False):
        if getattr(self.fittingThread, 'alive', False):
            self.fitted = False
            self.fittingThread.kill()
        if blocking:
            self._FitHardpoints()
        else:
            self.fittingThread = uthread2.StartTasklet(self._FitHardpoints)

    def _FitHardpoints(self):
        if self.fitted:
            return
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        self.fitted = True
        newTurretSetDict = TurretSet.FitTurrets(self.id, self.model)
        self.turrets = []
        for key, val in newTurretSetDict.iteritems():
            self.modules[key] = val
            self.turrets.append(val)

    def Explode(self):
        explosionPath, (delay, scaling) = self.GetExplosionInfo()
        if not self.exploded:
            self.sm.ScatterEvent('OnShipExplode', self.GetModel())
        return SpaceObject.Explode(self, explosionURL=explosionPath, managed=True, delay=delay, scaling=scaling)
