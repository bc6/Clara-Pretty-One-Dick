#Embedded file name: carbon/client/script/sys\launcherService.py
"""
Simple wrapper service for the launcherapi module. This is simply so that it's easy for people 
to migrate to/understand.
"""
import service
import launcherapi

class LauncherService(service.Service):
    __guid__ = 'svc.launcher'
    __displayname__ = 'EVE Launcher Interface Service'

    def __init__(self):
        service.Service.__init__(self)
        self.shared = {}

    def Run(self, memStream = None):
        """Start the service. This also instantiates the shared memory. We can keep separate 
        memory objects, since they have different methods (some don't allow read, others 
        disallow write), even though they are actually accessing the same memory independently"""
        self.state = service.SERVICE_RUNNING
        self.shared['clientBoot'] = launcherapi.ClientBootManager()

    def SetClientBootProgress(self, percentage):
        """Write the percentage to the shared memory space."""
        progress = self.shared['clientBoot']
        progress.SetPercentage(percentage)
