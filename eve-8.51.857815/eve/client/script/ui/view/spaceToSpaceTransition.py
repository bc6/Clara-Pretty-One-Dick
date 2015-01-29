#Embedded file name: eve/client/script/ui/view\spaceToSpaceTransition.py
"""
This module contains a transition from Space (inflight) to Space
"""
import geo2
import uthread
import viewstate

class SpaceToSpaceTransition(viewstate.Transition):
    """
    Controls transition when jumping between systems.
    """
    __guid__ = 'viewstate.SpaceToSpaceTransition'

    def __init__(self, sceneManager = None):
        self.sceneManager = sceneManager
        if self.sceneManager is None:
            self.sceneManager = sm.GetService('sceneManager')
        self.scene = None
        self.effect = None
        self.active = False
        viewstate.Transition.__init__(self)

    def _GetInflightCamera(self):
        return sm.GetService('camera').GetSpaceCamera()

    def _GetSolarSystemScene(self, destSolarSystemID):
        sceneRes = self.sceneManager.GetSceneForSystem(destSolarSystemID)
        return self.sceneManager.LoadScene(sceneRes, inflight=False, registerKey='default', setupCamera=True, applyScene=False)[0]

    def _GetClosest(self, position, rowSet, maxDist):
        closestDist = float('inf')
        closestPlanet = None
        for each in rowSet:
            pos = (each.x, each.y, each.z)
            dist = geo2.Vec3DistanceSq(position, pos)
            if dist < maxDist * maxDist and dist < closestDist:
                closestPlanet = each.itemID
                closestDist = dist

        return closestPlanet

    def _PrioritizeStargateLoads(self, stargateID, systemId):
        items = [stargateID]
        systemItems = sm.GetService('map').GetSolarsystemItems(systemId, False)
        stargateRow = systemItems.Filter('itemID')[stargateID][0]
        planet = self._GetClosest((stargateRow.x, stargateRow.y, stargateRow.z), systemItems.Filter('groupID')[const.groupPlanet], maxDist=const.AU * 0.5)
        if planet is not None:
            items.append(planet)
        sm.GetService('space').PrioritizeLoadingForIDs(items)

    def _GetSceneFromPath(self, path):
        return self.sceneManager.LoadScene(path, inflight=False, registerKey='default', setupCamera=True, applyScene=False)[0]

    def _ApplySceneInflightAttribs(self, scene, camera):
        self.sceneManager.ApplyScene(scene, camera, 'default')
        self.sceneManager.ApplySolarsystemAttributes(scene, camera)
        self.sceneManager.ApplySceneInflightAttributes(scene, camera)

    def _SetScene(self, scene):
        self.sceneManager.SetActiveScene(scene, 'default')

    def SetTransitionEffect(self, effect):
        self.effect = effect

    def InitializeGateTransition(self, destSolarSystemID, destObjectID = None):
        self.active = True
        self.destObjectID = destObjectID
        self.destSolarSystemID = destSolarSystemID
        self.camera = self._GetInflightCamera()
        self.scene = self._GetSolarSystemScene(destSolarSystemID)
        uthread.new(self._PrioritizeStargateLoads, destObjectID, destSolarSystemID)

    def InitializeCynoTransition(self, destSolarSystemID):
        self.active = True
        self.destSolarSystemID = destSolarSystemID
        self.camera = self._GetInflightCamera()
        self.scene = self._GetSolarSystemScene(destSolarSystemID)

    def InitializeWormholeTransition(self, scenePath):
        self.active = True
        self.camera = self._GetInflightCamera()
        self.scene = self._GetSceneFromPath(scenePath)

    def Finalize(self):
        self._ApplySceneInflightAttribs(self.scene, self.camera)
        self.effect.Stop()
        self.scene = None
        self.camera = None
        self.effect = None
        self.active = False

    def Abort(self):
        self._ApplySceneInflightAttribs(self.sceneManager.GetRegisteredScene('default'), self.camera)
        self.sceneManager.SetRegisteredScenes('default')
        self.scene = None
        self.camera = None
        self.effect = None
        self.active = False

    def ApplyDestinationScene(self):
        if self.effect is None:
            return
        self.effect.SetScene(self.scene)
        self._SetScene(self.scene)

    def StartTransition(self, fromView, toView):
        self.ApplyDestinationScene()

    def EndTransition(self, fromView, toView):
        pass
