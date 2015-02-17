#Embedded file name: carbonui/control/browser\browserImageSvc.py
"""Deals with loading of images for the in-game browser.  This functionality
originally crept into the photo service, but has been moved here for more
clarity.
"""
import os
import sys
import uthread
import blue
import trinity
import service
import corebrowserutil
import pychartdir
from carbonui.util.various_unsorted import GetBuffersize

class BrowserImage(service.Service):
    """This service is used to load images from URLs into a texture that
    can be used by the in game browser (or other similar windows)."""
    __guid__ = 'svc.browserImage'
    __exportedcalls__ = {}
    __startupdependencies__ = ['browserCache']

    def __init__(self):
        service.Service.__init__(self)
        self._urlloading = {}

    def GetTextureInfoFromURL(self, path, currentURL = None, fromWhere = None):
        if path.endswith('.blue'):
            return self._GetPic_blue(path)
        fullPath = corebrowserutil.ParseURL(path, currentURL)[0]
        cacheData = self.browserCache.GetFromCache(fullPath)
        if not cacheData:
            cacheData = self.GetTextureFromURL(path, currentURL, fromWhere=fromWhere, sizeonly=1)
        if cacheData and os.path.exists(cacheData[0].replace('cache:/', blue.paths.ResolvePath(u'cache:/'))):
            return cacheData

    def GetTextureFromURL(self, path, currentURL = None, ignoreCache = 0, dontcache = 0, fromWhere = None, sizeonly = 0, retry = 1):
        if path.endswith('.blue'):
            return self._GetPic_blue(path)
        dev = trinity.device
        fullPath = corebrowserutil.ParseURL(path, currentURL)[0]
        if path.startswith('res:'):
            try:
                bmp = trinity.Tr2HostBitmap()
                bmp.CreateFromFile(path)
                w, h = bmp.width, bmp.height
                bw, bh = GetBuffersize(w), GetBuffersize(h)
                if sizeonly:
                    return (path,
                     w,
                     h,
                     bw,
                     bh)
                return self._ReturnTexture(path, w, h, bw, bh)
            except:
                self.LogError('Failed to load image', path)
                if self._urlloading.has_key(fullPath):
                    del self.urlloading[fullPath]
                sys.exc_clear()
                return self._ErrorPic(sizeonly)

        if ignoreCache:
            self.browserCache.InvalidateImage(fullPath)
        while self._urlloading.has_key(fullPath):
            blue.pyos.BeNice()

        if not dontcache:
            cacheData = self.browserCache.GetFromCache(fullPath)
            if cacheData and os.path.exists(cacheData[0].replace('cache:/', blue.paths.ResolvePath(u'cache:/'))):
                if sizeonly:
                    return cacheData
                return self._ReturnTexture(*cacheData)
        try:
            self._urlloading[fullPath] = 1
            ret = corebrowserutil.GetStringFromURL(fullPath)
            cacheID = int(str(blue.os.GetWallclockTime()) + str(uthread.uniqueId() or uthread.uniqueId()))
            imagestream = ret.read()
            ext = None
            if 'content-type' in ret.headers.keys() and ret.headers['content-type'].startswith('image/'):
                ext = ret.headers['content-type'][6:]
            if ext == None or ext == 'png':
                header = imagestream[:16]
                for sig, sext in [('PNG', 'PNG'),
                 ('GIF', 'GIF'),
                 ('JFI', 'JPEG'),
                 ('BM8', 'BMP')]:
                    for i in xrange(0, 12):
                        if header[i:i + 3] == sig:
                            ext = sext
                            break

                if not ext:
                    header = imagestream[-16:]
                    for sig, sext in [('XFILE', 'TGA')]:
                        for i in xrange(0, 10):
                            if header[i:i + 5] == sig:
                                ext = sext
                                break

            if ext:
                filename = '%sBrowser/Img/%s.%s' % (blue.paths.ResolvePath(u'cache:/'), cacheID, ext)
                resfile = blue.classes.CreateInstance('blue.ResFile')
                if not resfile.Open(filename, 0):
                    resfile.Create(filename)
                resfile.Write(imagestream)
                resfile.Close()
                if ext.upper() == 'GIF':
                    g = pychartdir.DrawArea()
                    g.setBgColor(pychartdir.Transparent)
                    g.loadGIF(filename.replace(u'/', u'\\').encode('utf8'))
                    ext = 'PNG'
                    filename = u'%sBrowser/Img/%s.%s' % (blue.paths.ResolvePath(u'cache:/'), cacheID, ext)
                    g.outPNG(filename.replace(u'/', u'\\').encode('utf8'))
                bmp = trinity.Tr2HostBitmap()
                bmp.CreateFromFile(filename)
                w, h = bmp.width, bmp.height
                bw, bh = GetBuffersize(w), GetBuffersize(h)
                cachePath = 'cache:/Browser/Img/%s.%s' % (cacheID, ext)
                if 'pragma' not in ret.headers.keys() or ret.headers['Pragma'].find('no-cache') == -1:
                    self.browserCache.Cache(fullPath, (cachePath,
                     w,
                     h,
                     bw,
                     bh))
                del self._urlloading[fullPath]
                if sizeonly:
                    return (cachePath,
                     w,
                     h,
                     bw,
                     bh)
                return self._ReturnTexture(cachePath, w, h, bw, bh)
            del self._urlloading[fullPath]
            return self._ErrorPic(sizeonly)
        except Exception as e:
            if retry:
                sys.exc_clear()
                if fullPath in self._urlloading:
                    del self._urlloading[fullPath]
                return self.GetTextureFromURL(path, currentURL, ignoreCache, dontcache, fromWhere, sizeonly, 0)
            self.LogError(type(e), 'on line', sys.exc_traceback.tb_lineno, 'in browserImage service')
            self.LogError(e, 'Failed to load image', path)
            if fullPath in self._urlloading:
                del self._urlloading[fullPath]
            sys.exc_clear()
            return self._ErrorPic(sizeonly)

    def _ErrorPic(self, sizeonly = 0):
        if sizeonly:
            return ('res:/uicore/texture/none.dds', 32, 32, 32, 32)
        return self._ReturnTexture('res:/uicore/texture/none.dds', 32, 32, 32, 32)

    def _ReturnTexture(self, path, width, height, bufferwidth, bufferheight):
        tex = trinity.Tr2Sprite2dTexture()
        tex.resPath = str(path)
        return (tex, width, height)

    def _GetPic_blue(self, path):
        tex = blue.resMan.LoadObject(path)
        w = int(tex.pixelBuffer.width * (tex.scaling.x / (tex.texCoordIndex * 2 or 1))) or 32
        h = int(tex.pixelBuffer.height * (tex.scaling.y / (tex.texCoordIndex * 2 or 1))) or 32
        return (tex, w, h)
