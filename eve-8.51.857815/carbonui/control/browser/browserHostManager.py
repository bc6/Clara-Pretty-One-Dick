#Embedded file name: carbonui/control/browser\browserHostManager.py
"""
This service provides singleton access to the ccpBrowserHost object, ensuring
that that object is properly initialized and shut down before/after usage.

It also provides instance-counting, so that ccpBrowser.exe can be shut down
when there are no longer any browserSession instances extant.
"""
import blue
import service
import os
import errno
import log
import shutil
import sys
import corebrowserutil
import trinity
import uthread
try:
    import ccpBrowserHost
except ImportError:
    pass

class CoreBrowserHostManager(service.Service):
    __guid__ = 'svc.browserHostManager'

    def Run(self, *args):
        self._browserHost = None
        self.liveBrowserViews = []
        self.AppRun()

    def _InitializeCCPBrowser(self):
        browserCache = self.AppGetBrowserCachePath()
        cookies = ''
        cache = ''
        if not os.path.exists(browserCache):
            self.LogInfo('BrowserHostManager::_InitializeCCPBrowser creating cache path', browserCache)
            try:
                os.makedirs(browserCache)
                cookies = os.path.join(browserCache, 'Cookies')
                cache = os.path.join(browserCache, 'Files')
            except OSError as oserr:
                if oserr.errno != errno.EEXIST:
                    log.LogException('BrowserHostManager::_InitializeCCPBrowser unable to create cache path - will cache to memory only', severity=log.LGWARN)
                    cookies = ''
                    cache = ''

        else:
            cookies = os.path.join(browserCache, 'Cookies')
            cache = os.path.join(browserCache, 'Files')
        exePath = blue.paths.ResolvePath('bin:/ccpBrowser.exe')
        ccpBrowserHost.BrowserInit(exePath, unicode(cookies), unicode(cache), False)
        self._browserHost = ccpBrowserHost
        self.liveBrowserViews = []
        uthread.new(self.TickBrowser).context = 'TickBrowser'

    def TickBrowser(self):
        while True:
            ccpBrowserHost.Tick()
            blue.synchro.Yield()

    def RestartBrowserHost(self, clearCache = False):
        self._browserHost = None
        self.liveBrowserViews = []
        ccpBrowserHost.BrowserShutdown(True)
        blue.pyos.synchro.Yield()
        if clearCache:
            cachePath = self.AppGetBrowserCachePath()
            if cachePath is not None:
                cachePath = cachePath.strip()
                if cachePath != '':
                    if os.path.exists(cachePath):
                        successfullyDeleted = False
                        errorText = ''
                        try:
                            filePath = os.path.join(cachePath, 'Files')
                            cookiePath = os.path.join(cachePath, 'Cookies')
                            if os.path.exists(filePath):
                                shutil.rmtree(filePath)
                            if os.path.exists(cookiePath):
                                shutil.rmtree(cookiePath)
                            successfullyDeleted = True
                        except WindowsError as e:
                            self.LogError('Error occurred clearing cache', e)
                            sys.exc_clear()

                        if successfullyDeleted:
                            uicore.Message('BrowserCacheCleared')
                        else:
                            raise UserError('BrowserCacheClearFailed')
        self._InitializeCCPBrowser()

    def GetBrowserHost(self):
        if self._browserHost is None:
            self._InitializeCCPBrowser()
        return self._browserHost

    def Stop(self, *args):
        service.Service.Stop(self, args)
        if self._browserHost is not None:
            self._browserHost = None
            self.liveBrowserViews = []
            ccpBrowserHost.BrowserShutdown()

    def GetNewBrowserView(self):
        if self._browserHost is None:
            self._InitializeCCPBrowser()
        newView = self._browserHost.BrowserViewHost(trinity.app.GetHwndAsLong())
        self.liveBrowserViews.append(newView)
        return newView

    def ReleaseBrowserView(self, browserView):
        if browserView is None:
            return
        if self._browserHost is None:
            self.LogWarn('Attempting to release browserView object', browserView, 'but Browser Host is already dead')
            return
        if browserView not in self.liveBrowserViews:
            self.LogWarn('Attempting to release browserView object', browserView, 'which is not managed by BrowserHostManager')
            del browserView
            return
        self.liveBrowserViews.remove(browserView)
        del browserView
        if len(self.liveBrowserViews) < 1:
            self.LogInfo('BrowserHostManager is shutting down CCPBrowserHost as all active views have been closed')
            self._browserHost = None
            ccpBrowserHost.BrowserShutdown()

    def AppRun(self):
        """
            This method is run after BrowserHostManager has initialized its 
            base class. Use this for initialization. 
        """
        pass

    def AppGetBrowserCachePath(self):
        """
            This method retrieves the path at which the browser should store
            its cache files; two directories will be created by ccpBrowser.exe
            under this directory: Files and Images.
        
            The return value must be a valid path; if the path does not exist 
            and cannot be created, then ccpBrowser.exe will be configured to
            only use in-memory caching.
            
            ARGUMENTS
                None
        
            RETURNS
                A string containing a filesystem path. 
        """
        return corebrowserutil.DefaultCachePath()
