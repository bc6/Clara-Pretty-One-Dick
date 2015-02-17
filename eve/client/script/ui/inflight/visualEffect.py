#Embedded file name: eve/client/script/ui/inflight\visualEffect.py
import blue
from carbon.common.script.sys.service import Service
import uthread
import logging
logger = logging.getLogger(__name__)

class VisualEffectSvc(Service):
    """
    service to manage in-space visual effects (god-rays etc)
    """
    __guid__ = 'svc.visualEffect'
    __notifyevents__ = []
    __startupdependencies__ = ['sceneManager']
    __notifyevents__ = ['OnSessionChanged']

    def Run(self, *args):
        Service.Run(self, *args)
        self.activeEffects = {}
        self.transitionLock = uthread.Semaphore('VisualEffectSvc transition lock')
        self.godRays = GodRays(self.sceneManager)

    def OnSessionChanged(self, isremote, sess, change):
        if 'solarsystemid' not in change:
            return
        oldSolarsystem, newSolarsystem = change['solarsystemid']
        if oldSolarsystem:
            self._StopStaticEffectsForSolarsystem(oldSolarsystem)
        if newSolarsystem:
            self._StartStaticEffectsForSolarsystem(newSolarsystem)

    def _StopStaticEffectsForSolarsystem(self, solarsystemID):
        visualEffect = self._GetSolarsystemStaticVisualEffect(solarsystemID)
        if visualEffect:
            self.DeactivateVisualEffect(visualEffect)
            self.DisableGodrays(solarsystemID)

    def _StartStaticEffectsForSolarsystem(self, solarsystemID):
        visualEffect = self._GetSolarsystemStaticVisualEffect(solarsystemID)
        if visualEffect:
            self.ActivateVisualEffect(visualEffect)
            self.EnableGodrays(solarsystemID)

    def _GetSolarsystemStaticVisualEffect(self, solarsystemID):
        solarsystemContent = cfg.mapSolarSystemContentCache[solarsystemID]
        return solarsystemContent['visualEffect']

    def ActivateVisualEffect(self, effectName):
        with self.transitionLock:
            if self._IsEffectActive(effectName):
                return
            effect = VisualEffect(self.sceneManager, effectName)
            effect.Activate()
            self.activeEffects[effectName] = effect

    def DeactivateVisualEffect(self, effectName):
        with self.transitionLock:
            if not self._IsEffectActive(effectName):
                return
            effect = self.activeEffects.pop(effectName)
            effect.Deactivate()

    def _ClearActiveEffects(self):
        for effectName in self.activeEffects.keys():
            self.DeactivateVisualEffect(effectName)

    def _IsEffectActive(self, effectName):
        return effectName in self.activeEffects

    def EnableGodrays(self, solarsystemID):
        self.godRays.Enable(solarsystemID)

    def DisableGodrays(self, solarsystemID):
        self.godRays.Disable(solarsystemID)

    def IsGodrayEnabled(self):
        return self.godRays.IsEnabled()


class VisualEffect:

    def __init__(self, sceneManager, effectName):
        self.sceneManager = sceneManager
        self.effectName = effectName

    def Activate(self):
        logger.debug('VisualEffect.Activate %s', self.effectName)
        ppJob = self.sceneManager.GetFiSPostProcessingJob()
        ppJob.AddPostProcess(self.effectName, key='default')

    def Deactivate(self):
        logger.debug('VisualEffect.Deactivate %s', self.effectName)
        ppJob = self.sceneManager.GetFiSPostProcessingJob()
        ppJob.RemovePostProcess(self.effectName)


class GodRays:

    def __init__(self, sceneManager):
        self.sceneManager = sceneManager
        self.enablingGodRays = False
        self.useGodRays = False

    def Enable(self, solarsystemID):
        self.useGodRays = True
        logger.debug('GodRays.Enable %s', solarsystemID)
        if not self.enablingGodRays:
            starID = cfg.mapSolarSystemContentCache[solarsystemID].star.id
            uthread.new(self._EnableGodRaysThread, starID)

    def Disable(self, solarsystemID):
        self.useGodRays = False
        logger.debug('GodRays.Disable %s', solarsystemID)
        scene = self.sceneManager.GetRegisteredScene('default')
        starID = cfg.mapSolarSystemContentCache[solarsystemID].star.id
        if getattr(scene, 'sunBall', None) is not None and scene.sunBall.id == starID:
            scene.sunBall.EnableGodRays(False)

    def IsEnabled(self):
        return self.useGodRays

    def SetIntensity(self, value):
        scene = self.sceneManager.GetRegisteredScene('default')
        if getattr(scene, 'sunBall', None) is not None:
            scene.sunBall.SetGodRaysIntensity(value)

    def _EnableGodRaysThread(self, starID):
        try:
            self.enablingGodRays = True
            count = 20
            while self.useGodRays and count:
                logger.debug('GodRays._EnableGodRaysThread %s attempt %s', starID, count)
                scene = self.sceneManager.GetRegisteredScene('default')
                if getattr(scene, 'sunBall', None) is not None and scene.sunBall.id == starID:
                    scene.sunBall.EnableGodRays(True)
                    break
                blue.pyos.synchro.SleepWallclock(250)
                count -= 1

        finally:
            self.enablingGodRays = False
