#Embedded file name: eve/client/script/ui/podGuide\podGuideService.py
import service
from eve.client.script.ui.podGuide.podGuideUI import PodGuideWindow

class PodGuideService(service.Service):
    __update_on_reload__ = 1
    __guid__ = 'svc.podguide'
    __displayname__ = 'Pod Guide service'
    __slashhook__ = True

    def Run(self, *args):
        service.Service.Run(self, *args)

    def cmd_podguide_show(self, p):
        PodGuideWindow.ToggleOpenClose()
