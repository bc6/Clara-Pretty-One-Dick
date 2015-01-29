#Embedded file name: carbon/client/script/graphics/graphicWrappers\tr2InteriorCylinderLight.py
"""
Tr2InteriorCylinderLight wrapper.
"""
import util
import weakref
import geo2

class Tr2InteriorCylinderLight(util.BlueClassNotifyWrap('trinity.Tr2InteriorCylinderLight')):
    """
    Wrapper for trinity interior cylinder light object.
    """
    __guid__ = 'graphicWrappers.Tr2InteriorCylinderLight'

    @staticmethod
    def Wrap(triObject, resPath):
        """
        Wraps trinity object.
        """
        Tr2InteriorCylinderLight(triObject)
        triObject.scene = None
        return triObject

    def AddToScene(self, scene):
        """
        Adds light source to the scene.
        """
        if self.scene and self.scene():
            scene.RemoveLight(self.scene())
        scene.AddLight(self)
        self.scene = weakref.ref(scene)

    def RemoveFromScene(self, scene):
        """
        Removes light source from the scene.
        """
        scene.RemoveLight(self)
        self.scene = None

    def _TransformChange(self, transform):
        """
        Called back on a transform change
        """
        self.OnTransformChange()

    def OnTransformChange(self):
        """
        Called back on a transform change
        """
        pass

    def SetPosition(self, position):
        """
        Assigns new position to the light source.
        """
        self.position = position

    def GetPosition(self):
        """
        Returns light source position.
        """
        return self.position

    def GetRotationYawPitchRoll(self):
        """
        Returns light source rotation as Euler angles.
        """
        return geo2.QuaternionRotationGetYawPitchRoll(self.rotation)

    def SetRotationYawPitchRoll(self, ypr):
        """
        Assigns light source rotation passed as Euler angles.
        """
        self.rotation = geo2.QuaternionRotationSetYawPitchRoll(*ypr)

    def GetRadius(self):
        """
        Returns light source radius.
        """
        return self.radius

    def SetRadius(self, radius):
        """
        Assigns light source radius.
        """
        self.radius = radius

    def GetLength(self):
        """
        Returns light source length.
        """
        return self.length

    def SetLength(self, length):
        """
        Assigns light source length.
        """
        self.length = length

    def GetColor(self):
        """
        Returns light source color.
        """
        return self.color[:3]

    def SetColor(self, color):
        """
        Assigns light source color.
        """
        self.color = (color[0],
         color[1],
         color[2],
         1)

    def GetFalloff(self):
        """
        Returns light source falloff power.
        """
        return self.falloff

    def SetFalloff(self, falloff):
        """
        Assigns light source falloff power.
        """
        self.falloff = falloff
