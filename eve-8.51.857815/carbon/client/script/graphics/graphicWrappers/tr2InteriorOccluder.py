#Embedded file name: carbon/client/script/graphics/graphicWrappers\tr2InteriorOccluder.py
import util
import weakref
import carbon.client.script.graphics.graphicWrappers.baseGraphicWrapper as graphicWrappers

class Tr2InteriorOccluder(util.BlueClassNotifyWrap('trinity.Tr2InteriorOccluder'), graphicWrappers.TrinityTransformMatrixMixinWrapper):
    __guid__ = 'graphicWrappers.Tr2InteriorOccluder'

    @staticmethod
    def Wrap(triObject, resPath):
        Tr2InteriorOccluder(triObject)
        triObject.InitTransformMatrixMixinWrapper()
        triObject.AddNotify('transform', triObject._TransformChange)
        triObject.cellName = ''
        triObject.scene = None
        return triObject

    def SetCell(self, cellName):
        if self.cellName != cellName:
            self.cellName = cellName
            if self.scene and self.scene():
                self.AddToScene(self.scene())

    def AddToScene(self, scene):
        if self.scene and self.scene():
            scene.RemoveOccluder(self)
        scene.AddOccluder(self, self.cellName)
        self.scene = weakref.ref(scene)

    def RemoveFromScene(self, scene):
        scene.RemoveOccluder(self)
        self.scene = None
        self.cellName = None

    def _TransformChange(self, transform):
        self.OnTransformChange()

    def OnTransformChange(self):
        pass

    def OnPositionChange(self):
        pass

    def OnRotationChange(self):
        pass

    def OnScaleChange(self):
        """
        # TODO: Ensure we don't get negative scale
        xvec = geo2.Vector(self.transform[0][0], self.transform[0][1], self.transform[0][2])
        yvec = geo2.Vector(self.transform[1][0], self.transform[1][1], self.transform[1][2])
        zvec = geo2.Vector(self.transform[2][0], self.transform[2][1], self.transform[2][2])
        
        lx = xvec.Vec3Length(xvec)
        ly = xvec.Vec3Length(xvec)
        lz = xvec.Vec3Length(xvec)
        print lx, ly, lz
        # TODO: Ensure we don't get negative scale
        """
        pass
