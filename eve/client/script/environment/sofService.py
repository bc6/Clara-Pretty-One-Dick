#Embedded file name: eve/client/script/environment\sofService.py
"""
Contains the Space Object Factory service, used to load customized space ships
"""
import service
import trinity
import evegraphics.utils as gfxutils

class sofService(service.Service):
    __guid__ = 'svc.sofService'
    __displayname__ = 'Space Object Factory'
    __servicename__ = 'sofService'

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        self.spaceObjectFactory = trinity.EveSOF()
        self.spaceObjectFactory.dataMgr.LoadData('res:/dx9/model/spaceobjectfactory/data.red')

    def Stop(self, stream):
        service.Service.Stop(self)
        self.spaceObjectFactory = None
