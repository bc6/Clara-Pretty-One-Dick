#Embedded file name: carbonui/control/browser\browserCacheSvc.py
import service
import blue
import os.path
import sys
from carbonui.util.settings import SettingSection

class BrowserCache(service.Service):
    """
    The BrowserCache stores information about images cached locally, originating
    from urls.
    
    This is effectively a dictionary with the full url path as the key, and the
    value a tuple (cachePath, width, height, bufferWidth, bufferHeight).
    
    GetFromCache is used for looking up in the cache.
    
    Cache is used to add entries to the cache.
    """
    __guid__ = 'svc.browserCache'

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.imgindex = None
        paths = [blue.paths.ResolvePath(u'cache:/'), blue.paths.ResolvePathForWriting(u'cache:/Browser'), blue.paths.ResolvePathForWriting(u'cache:/Browser/Img')]
        for path in paths:
            try:
                os.makedirs(path)
            except OSError as e:
                sys.exc_clear()

        self.Load()

    def Stop(self, *etc):
        service.Service.Stop(self, *etc)
        self.Save()

    def GetFromCache(self, cacheID):
        if self.imgindex is None:
            self.Load()
        f = self.imgindex.img.Get(cacheID, None)
        if f:
            if os.path.exists(f[0].replace('cache:/', blue.paths.ResolvePath(u'cache:/'))):
                return f
            self.ClearCache(cacheID)

    def Cache(self, cacheID, cacheData, fromWhere = None):
        if not self.imgindex:
            self.Load()
        self.ClearCache(cacheID)
        self.imgindex.img.Set(cacheID, cacheData)

    def ClearCache(self, cacheID):
        if not self.imgindex:
            self.Load()
        self.imgindex.img.Delete(cacheID)

    def InvalidateImage(self, url):
        self.CheckForIndexFile()
        self.ClearCache(url)

    def Load(self):
        if self.imgindex:
            self.imgindex.Unload()
            self.imgindex = None
        self.imgindex = SettingSection('cache', blue.paths.ResolvePathForWriting(u'cache:/Browser/Img/index.dat'), 62, service=self)
        self.imgindex.CreateGroup('img')
        cachefiles = [ self.imgindex.img.Get(each, None)[0].replace('cache:/', blue.paths.ResolvePath(u'cache:/')) for each in self.imgindex.img.keys() ]
        for f in os.listdir(blue.paths.ResolvePathForWriting(u'cache:/Browser/Img')):
            if f == 'index.dat':
                continue
            f1 = blue.paths.ResolvePathForWriting(u'cache:/Browser/Img') + f
            if f1 not in cachefiles:
                try:
                    if os.path.exists(f1):
                        os.unlink(f1)
                except:
                    sys.exc_clear()

    def GetImgIndex(self):
        return self.imgindex

    def Save(self):
        self.imgindex.Unload()
        self.imgindex = None

    def CheckForIndexFile(self):
        file = blue.ResFile()
        if not file.Open(blue.paths.ResolvePathForWriting(u'cache:/Browser/Img/index.dat')):
            self.Load()
        else:
            file.Close()
