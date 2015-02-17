#Embedded file name: eve/client/script/ui/control/browser\browserHostManager.py
"""
This service provides singleton access to the ccpBrowserHost object, ensuring
that that object is properly initialized and shut down before/after usage.

Be warned, since this class attempts to act as a nearly-transparent proxy for CCPBrowserHost,
it does some funky internal Python Voodoo involving __dict__ and __getattr__.
"""
import corebrowserutil
import svc
try:
    import ccpBrowserHost
except ImportError:
    pass

class BrowserHostManager(svc.browserHostManager):
    __guid__ = 'svc.eveBrowserHostManager'
    __replaceservice__ = 'browserHostManager'
    __startupdependencies__ = ['settings']

    def AppRun(self, *args):
        pass

    def AppGetBrowserCachePath(self):
        return settings.public.generic.Get('BrowserCache', corebrowserutil.DefaultCachePath())
