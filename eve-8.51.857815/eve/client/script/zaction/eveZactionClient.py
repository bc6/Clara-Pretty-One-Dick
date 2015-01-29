#Embedded file name: eve/client/script/zaction\eveZactionClient.py
import svc
import yaml
import const
import blue

class eveZactionClient(svc.zactionClient):
    __guid__ = 'svc.eveZactionClient'
    __replaceservice__ = 'zactionClient'
    __displayname__ = 'Eve ZActionTree Service'
    __exportedcalls__ = svc.zactionClient.__exportedcalls__.copy()
    __dependencies__ = svc.zactionClient.__dependencies__[:]
    __notifyevents__ = svc.zactionClient.__notifyevents__[:]

    def __init__(self):
        svc.zactionClient.__init__(self)
        self.clientProperties['TargetList'] = []

    def Run(self, *etc):
        svc.zactionClient.Run(self, *etc)
        self.mouseInputService = sm.GetService('mouseInput')
        if self.mouseInputService is not None:
            self.mouseInputService.RegisterCallback(const.INPUT_TYPE_LEFTCLICK, self.OnClick)
        self._LoadAnimationData()

    def _LoadAnimationData(self):
        """
        Loads the AnimInfo.yaml file.  This should eventually move to an animation server 
        or something like staticActionDataServer.py
        """
        ANIMATION_METADATA_PATH = 'res:/Animation/animInfo.yaml'
        resourceFile = blue.ResFile()
        openResults = resourceFile.Open(ANIMATION_METADATA_PATH)
        self._animTypeData = yaml.load(resourceFile)
        resourceFile.close()
        self.ProcessAnimationDictionary(self.GetAnimationData())

    def OnClick(self, entityID):
        if self.mouseInputService.GetSelectedEntityID() is not None:
            targetList = [self.mouseInputService.GetSelectedEntityID()]
        else:
            targetList = []
        self.clientProperties['TargetList'] = targetList

    def GetAnimationData(self):
        """ Get the animation data from the yaml file. """
        return self._animTypeData
