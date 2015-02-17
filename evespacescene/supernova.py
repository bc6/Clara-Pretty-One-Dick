#Embedded file name: evespacescene\supernova.py
"""
Class and functions to handle the super nova effect for winter 2014.
"""
import util
import geo2
import blue
import trinity
import log
SUPERNOVA_SYSTEM_ID = 30000367

class Supernova(object):
    __notifyevents__ = ['OnLoadScene']

    def __init__(self):
        sm.RegisterNotify(self)
        self.effectPosition = None
        self.curveSet = None
        self.progress = 0.0
        self.farSize = 0.2
        self.nearSize = 4.0
        self.farDistance = 86.0
        self.nearDistance = 13.0
        self.model = None
        self.systemID = None

    def AddToScene(self, scene, systemID):
        """
        Adds the effect to the scene supplied.
        scene: A trinity.EveSpaceScene.
        systemID: the systemID of the scene. Used to prevent multiple adds by the QA tools.
        """
        if systemID != self.systemID:
            scene.backgroundObjects.append(self.model)
            self.systemID = systemID

    def _LoadModel(self):
        """
        Loads the model and sets up the proper transform hierarchy for camera relative positions.
        """
        graphic = cfg.graphics.get(20984, None)
        path = graphic.graphicFile
        model = blue.resMan.LoadObject(path)
        self.model = trinity.EveTransform()
        self.model.scaling = (10000.0, 10000.0, 10000.0)
        self.model.modifier = 2
        self.model.name = 'Supernova'
        self.model.children.append(model)

    def UpdatePosition(self, localPosition = None):
        """
        Updates the position and scale of the supernova.
        localPosition: An optional 3 tuple for the local position. If not passed in the session.solarsystemid is
        used to determine the position.
        """
        if not self.model:
            self._LoadModel()
        if not localPosition:
            localSystem = sm.StartService('map').GetItem(session.solarsystemid)
            localPosition = (localSystem.x, localSystem.y, localSystem.z)
        if not self.effectPosition:
            effectSystem = sm.StartService('map').GetItem(SUPERNOVA_SYSTEM_ID)
            self.effectPosition = (effectSystem.x, effectSystem.y, effectSystem.z)
        effect = self.model.children[0]
        direction = geo2.Vec3SubtractD(localPosition, self.effectPosition)
        direction = (direction[0], direction[1], -direction[2])
        distance = geo2.Vec3LengthD(direction) / 1e+16
        direction = geo2.Vec3Normalize(direction)
        if distance < self.nearDistance:
            scale = self.nearSize
        else:
            shift = (self.farSize * self.farDistance - self.nearSize * self.nearDistance) / (self.nearSize - self.farSize)
            baseSize = self.nearSize * (self.nearDistance + shift)
            scale = baseSize / (distance + shift)
        effect.scaling = (scale, scale, scale)
        effect.translation = geo2.Vec3Scale(direction, 15.0)

    def OnLoadScene(self, scene, key):
        if key != 'default':
            self.systemID = None
            return
        systemID = session.solarsystemid
        if util.IsWormholeSystem(systemID):
            return
        if not self.model:
            self._LoadModel()
        self.UpdatePosition()
        self.AddToScene(scene, systemID)
