#Embedded file name: evespacescene\playerdeath.py
import blue
import trinity
import viewstate
import eve.client.script.environment.spaceObject.corpse as corpse
import eve.client.script.environment.spaceObject.spaceObject as spaceObject
import evegraphics.utils as gfxutils

class PlayerDeathHandler(object):
    __notifyevents__ = ['OnPlayerPodDeath']

    def __init__(self, sceneManager):
        self._sceneManager = sceneManager
        sm.RegisterNotify(self)

    def OnPlayerPodDeath(self):
        if session.solarsystemid is None:
            return
        sm.GetService('viewState').ActivateView('inflight')
        bp = sm.GetService('michelle').GetBallpark()
        if bp:
            shipBall = bp.GetBall(bp.ego)
            spaceObject.SpaceObject.Explode(shipBall, 'res:/Model/Effect/Explosion/entityExplode_large.red')
            shipBall.Display(0)
        else:
            return
        shakeMagnitude = max(blue.os.desiredSimDilation, 0.2) * 250
        sm.GetService('camera').ShakeCamera(shakeMagnitude, (0, 0, 0))
        sm.GetService('audio').SendUIEvent('transition_pod_play')
        self.CopyMyScene()
        activeTransition = sm.GetService('viewState').activeTransition
        if activeTransition and isinstance(activeTransition, viewstate.SpaceToStationTransition):
            return
        fadeTime = max(blue.os.desiredSimDilation, 0.3) * 2000
        sm.GetService('loading').FadeIn(fadeTime, color=(1.0, 1.0, 1.0, 1.0))

    def CopyMyScene(self):
        """
            copies the stuff I need from original scene to display when you have been podded
        """
        sceneOrg = self._sceneManager.GetRegisteredScene('default')
        if sceneOrg is None:
            return
        scene = trinity.EveSpaceScene()
        self.podDeathScene = scene
        scene.sunDiffuseColor = sceneOrg.sunDiffuseColor
        scene.ambientColor = sceneOrg.ambientColor
        scene.fogColor = sceneOrg.fogColor
        scene.backgroundRenderingEnabled = True
        scene.backgroundEffect = blue.classes.Copy(sceneOrg.backgroundEffect)
        for pathName in ['envMapResPath',
         'envMap1ResPath',
         'envMap2ResPath',
         'envMap3ResPath']:
            path = getattr(sceneOrg, pathName, '')
            setattr(scene, pathName, path)

        sunBall = trinity.TriVectorCurve()
        sunPos = sceneOrg.sunBall.GetVectorAt(blue.os.GetSimTime())
        sunBall.value = (sunPos.x, sunPos.y, sunPos.z)
        scene.sunBall = sunBall
        time = blue.os.GetSimTime()
        objectLists = [(sceneOrg.lensflares, scene.lensflares, trinity.EveLensflare), (sceneOrg.planets, scene.planets, trinity.EvePlanet), (sceneOrg.objects, scene.objects, trinity.EveStation2)]
        for eachList, destination, allowedTypes in objectLists:
            for obj in eachList:
                if session.solarsystemid is None:
                    return
                try:
                    if not isinstance(obj, allowedTypes):
                        continue
                    if not obj.display:
                        continue
                    if getattr(obj, 'translationCurve', None) is not None and obj.translationCurve.__bluetype__ == 'destiny.ClientBall':
                        pos = obj.translationCurve.GetVectorAt(time)
                        if getattr(obj.translationCurve, 'translationCurve', None):
                            obj.translationCurve.resourceCallback = None
                        obj.translationCurve.model = None
                        translationCurve = trinity.TriVectorCurve()
                        translationCurve.value = (pos.x, pos.y, pos.z)
                        obj.translationCurve = translationCurve
                    if getattr(obj, 'rotationCurve', None) is not None and obj.rotationCurve.__bluetype__ == 'destiny.ClientBall':
                        obj.rotationCurve = None
                    destination.append(obj)
                except Exception:
                    pass

    def GetCorpseModel(self):
        path = corpse.GetCorpsePathForCharacter(session.charid)
        return trinity.Load(path)

    def GetCapsuleModel(self):
        resPath = gfxutils.GetResPathFromGraphicID(const.graphicIDBrokenPod)
        return trinity.Load(resPath)
