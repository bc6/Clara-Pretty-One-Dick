#Embedded file name: eve/client/script/environment/spaceObject\billboard.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
import uthread
import sys

class Billboard(SpaceObject):

    def __init__(self):
        SpaceObject.__init__(self)

    def Assemble(self):
        self.UnSync()
        uthread.pool('Billboard::LateAssembleUpdate', self.LateAssembleUpdate)

    def LateAssembleUpdate(self):
        billboardSvc = self.sm.GetService('billboard')
        billboardSvc.Update(self)

    def SetMap(self, name, path, idx = 0):
        if path is None:
            return
        self.LogInfo('Setting', name, 'to', path)
        self.model.FreezeHighDetailMesh()
        try:
            textureParameters = self.model.Find('trinity.TriTexture2DParameter')
            texture = [ x for x in textureParameters if x.name == name ][idx]
            texture.resourcePath = path
        except (Exception,) as e:
            self.LogError('SetMap() - Error updating billboard map', name, path, e)
            sys.exc_clear()

    def UpdateBillboardContents(self, advertPath, facePath):
        self.LogInfo('UpdateBillboardWithPictureAndText:', advertPath, facePath)
        if self.model is None:
            return
        self.SetMap('FaceMap', facePath)
        self.SetMap('AdvertMap', advertPath)
        self.SetMap('DiffuseMap', 'cache:/Temp/headlines.dds', 1)
        self.SetMap('DiffuseMap', 'cache:/Temp/bounty_caption.dds')
