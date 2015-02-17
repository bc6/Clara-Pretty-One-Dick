#Embedded file name: eve/client/script/ui/services\evePhotosvc.py
"""
This file contains functions for rendering out portraits for characters and items
"""
import uiprimitives
import service
import uiutil
import blue
import trinity
import sys
import util
import localization
import uthread
import carbonui.const as uiconst
import corebrowserutil
import time
import urllib2
import os
import datetime
import log
import shutil
import numbers
import yaml
import iconrendering
import iconrendering.photo as photo
import iconrendering.camera_util as camera_util
from iconrendering import BLUEPRINT_NONE, BLUEPRINT_NORMAL, BLUEPRINT_COPY, BLUEPRINT_RELIC, BLUEPRINT_DUST
from eve.client.script.ui.shared.maps.map2D import Map2D
from eve.client.script.environment.spaceObject.planet import Planet
from pychartdir import DrawArea, Transparent
from collections import defaultdict, namedtuple
NONE_PATH = 'res:/UI/Texture/none.dds'
NOT_AVAILABLE_PATH = 'res:/UI/Texture/notavailable.dds'
MAX_PORTRAIT_THREADS = 5
MAX_CACHE_AGE = 60 * 60 * 1
DEFAULT_PORTRAIT_SIZE = 512
DEFAULT_PORTRAIT_SAVE_SIZE = 1024
PORTRAIT_SIZES = [32,
 64,
 128,
 256,
 512]
BLUEPRINT_RESPATH = 'res:/UI/Texture/Icons/BPO.png'
BLUEPRINT_OVERLAY_PATH = 'res:/UI/Texture/Icons/bpo_overlay.png'
BLUEPRINT_COPY_RESPATH = 'res:/UI/Texture/Icons/BPC.png'
BLUEPRINT_COPY_OVERLAY_PATH = 'res:/UI/Texture/Icons/bpc_overlay.png'
BLUEPRINT_RELIC_RESPATH = 'res:/UI/Texture/Icons/relic.png'
BLUEPRINT_RELIC_OVERLAY_PATH = 'res:/UI/Texture/Icons/relic_overlay.png'
BLUEPRINT_DUST_RESPATH = 'res:/UI/Texture/Icons/BPD.png'
BLUEPRINT_SCENE = 'res:/dx9/scene/blueprint/original.red'
DEFAULT_MARKETING_TEST_IMAGE_SERVER = 'http://cdn1.eveonline.com/marketing/InGameVirtualGoodsStore/TestServersImages/'

def TypeIsRenderable(typeID, groupID, categoryID):
    """
    Determines whether a type is to be rendered or an icon file used.
    """
    return (typeID == const.typePlanetaryLaunchContainer or groupID not in iconrendering.ICON_GROUPS_INGAME) and (groupID in iconrendering.NON_ICON_GROUPS or categoryID in iconrendering.NON_ICON_CATEGORIES)


def GetPictureFileName(typeinfo, size):
    """
    Returns a filename in the form shaderModel_graphicID_icondID_raceID_size.dds
    """
    shaderModel = trinity.GetShaderModel()
    name = '%s_%s_%s_%s_%s.dds' % (shaderModel,
     typeinfo.graphicID or 0,
     typeinfo.iconID or 0,
     typeinfo.raceID or 0,
     size)
    return name


def GetCachePath(typeinfo, size, itemID, blueprint = BLUEPRINT_NONE):
    """
    Returns the cache path for the given type.
    """
    if typeinfo.groupID in [const.groupSun, const.groupPlanet, const.groupMoon]:
        return u'cache:/Pictures/Planets/%s_%s_%s.dds' % (trinity.GetShaderModel(), itemID, size)
    elif blueprint == BLUEPRINT_COPY:
        return u'cache:/Pictures/Blueprints/bpc_%s' % GetPictureFileName(typeinfo, size)
    elif blueprint == BLUEPRINT_RELIC:
        return u'cache:/Pictures/Blueprints/relic_%s' % GetPictureFileName(typeinfo, size)
    elif blueprint == BLUEPRINT_NORMAL:
        return u'cache:/Pictures/Blueprints/bp_%s' % GetPictureFileName(typeinfo, size)
    elif blueprint == BLUEPRINT_DUST:
        return u'cache:/Pictures/Blueprints/dust_%s_%s_%s.dds' % (trinity.GetShaderModel(), typeinfo.typeID, size)
    else:
        return u'cache:/Pictures/Gids/' + GetPictureFileName(typeinfo, size)


def GetRenderPath(graphicID, size, blueprint, raceID):
    """
    Returns the path to the UI texture for the type.
    """
    if size > 64:
        size = 128
    else:
        size = 64
    if not raceID:
        raceID = 0
    if blueprint == BLUEPRINT_COPY:
        fileName = '%s_%s_%s_%s.png' % (graphicID,
         64,
         0,
         'BPC')
    elif blueprint == BLUEPRINT_NORMAL:
        fileName = '%s_%s_%s_%s.png' % (graphicID,
         64,
         0,
         'BP')
    else:
        fileName = '%s_%s_%s.png' % (graphicID, size, raceID)
    fileName = os.path.join('res:/UI/Texture/Icons/renders/', fileName)
    return fileName


def DoLogIt(path):
    if not util.IsFullLogging() and 'portrait' in path.lower():
        return False
    return True


class EvePhoto(service.Service):
    __guid__ = 'svc.photo'
    __exportedcalls__ = {'GetPortrait': [],
     'AddPortrait': [],
     'GetAllianceLogo': [],
     'OrderByTypeID': [],
     'GetPhoto': [],
     'CheckAvail': [],
     'GetPlanetPhoto': [],
     'GetSunPhoto': [],
     'GetTextureFromURL': [],
     'CheckDates': [],
     'GetScenePicture': [],
     'GetIconByType': [],
     'SavePortraits': []}
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.notavail = {}
        self.imageServerQueue = defaultdict(list)
        self.currentlyFetching = defaultdict(list)
        self.fetchingFromImageServer = 0
        self.portraitregistrations = {}
        self.byTypeIDQue = []
        self.byTypeID_IsRunning = 0
        self.types = {}
        self.gidque = []
        self.gidrunning = 0
        self.gidcount = 0
        self.faceoptions = {}
        self.chappcache = None
        self.photoscene = None
        self.CheckDates(blue.paths.ResolvePathForWriting(u'cache:/Browser/Img'))
        self.CheckDates(blue.paths.ResolvePathForWriting(u'cache:/Pictures/Portraits'))
        self.CheckDates(blue.paths.ResolvePathForWriting(u'cache:/Pictures/Gids'))
        self.urlloading = {}
        self.pendingPI = {}
        self.portraits = None
        self.allianceLogos = None
        self.storeBannerImages = None
        self.pendingPortraitGeneration = set()
        self.defaultImageServerForUser = None
        self.defaultMarketingImages = None
        if not blue.pyos.packaged:
            username = os.environ.get('USERNAME')
            if username is None:
                username = os.environ.get('USER')
            if username is not None:
                self.defaultImageServerForUser = 'http://%s.dev.image/' % username.replace('.', '_').lower()
                self.LogInfo('Guessing ImageServer url as we are not in a build client: ', self.defaultImageServerForUser)
                self.defaultMarketingImages = DEFAULT_MARKETING_TEST_IMAGE_SERVER

    def CheckAvail(self, path):
        pathLog = path if DoLogIt(path) else ''
        self.LogInfo('CheckAvail ', pathLog)
        if path in self.notavail:
            self.LogInfo('CheckAvail ', pathLog, ' is in notavail')
            return None
        elif blue.paths.exists(path):
            self.LogInfo('CheckAvail ', pathLog, ' exists')
            return path
        else:
            self.LogInfo('CheckAvail ', pathLog, " doesn't exist, and has been added to notavail")
            self.notavail[path] = 1
            return None

    def GetValidBlueprintPath(self, sprite, typeID, size = 64, blueprint = BLUEPRINT_NORMAL):
        """Returns a valid blueprint path.  Will create the icon and save the path if required"""
        typeinfo = cfg.invtypes.Get(typeID)
        cachePath = GetCachePath(typeinfo, size, None, blueprint)
        resFile = blue.ResFile()
        try:
            if resFile.Open(cachePath):
                self.LogInfo('GetValidBlueprintPath ', cachePath, ' exists')
                return cachePath
        finally:
            del resFile

        graphic = typeinfo.Icon()
        if graphic and graphic.iconFile:
            iconPath = graphic.iconFile.strip()
            iconPath = photo.GetIconFileFromSheet(iconPath)
        else:
            iconPath = sprite.texture.resPath
        if blueprint == BLUEPRINT_DUST:
            backgroundPath = BLUEPRINT_DUST_RESPATH
            overlayPath = None
        elif blueprint == BLUEPRINT_COPY:
            backgroundPath = BLUEPRINT_COPY_RESPATH
            overlayPath = BLUEPRINT_COPY_OVERLAY_PATH
        elif blueprint == BLUEPRINT_RELIC:
            backgroundPath = BLUEPRINT_RELIC_RESPATH
            overlayPath = BLUEPRINT_RELIC_OVERLAY_PATH
        else:
            backgroundPath = BLUEPRINT_RESPATH
            overlayPath = BLUEPRINT_OVERLAY_PATH
        uthread.new(self.RenderBlueprint, sprite, cachePath, size, iconPath, backgroundPath, overlayPath)
        self._RemovePathFromNotAvailList(cachePath)
        return cachePath

    def RenderBlueprint(self, sprite, cachePath, size, iconPath, backgroundPath, overlayPath):
        """
        Render the blueprint on a thread to make sure the parent thread doesn't yield as it can cause unexpected issues
        during UI construction
        """
        photo.RenderIcon(cachePath, size=size, iconPath=iconPath, backgroundPath=backgroundPath, overlayPath=overlayPath)
        sprite.ReloadTexture()

    def DoBlueprint(self, sprite, typeID, size = 64, blueprint = BLUEPRINT_NORMAL):
        """
        Creates a blueprint from a pre-existing icon.
        """
        if not sprite.texture:
            return
        texture = sprite.texture.resPath
        bpPath = self.GetValidBlueprintPath(sprite, typeID, size, blueprint)
        if sprite.texture.resPath == texture:
            sprite.texture.resPath = bpPath
            sprite.rectLeft = 0
            sprite.rectWidth = 0
            sprite.rectTop = 0
            sprite.rectHeight = 0

    def GetScenePicture(self, res = 128, blur = 0):
        scene = sm.GetService('sceneManager').GetRegisteredScene(None, defaultOnActiveScene=True)
        camera = sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True)
        depthTexture = scene.depthTexture
        scene.depthTexture = None
        renderTarget = trinity.Tr2RenderTarget(res, res, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        depthStencil = trinity.Tr2DepthStencil(res, res, trinity.DEPTH_STENCIL_FORMAT.AUTO)
        view = trinity.TriView()
        view.transform = camera.viewMatrix.transform
        projection = camera.projectionMatrix
        renderJob = trinity.CreateRenderJob('StaticScene')
        renderJob.PushRenderTarget(renderTarget)
        renderJob.PushDepthStencil(depthStencil)
        renderJob.SetProjection(projection)
        renderJob.SetView(view)
        renderJob.Clear((0.0, 0.0, 0.0, 0.0), 1.0)
        renderJob.RenderScene(scene)
        renderJob.PopDepthStencil()
        renderJob.PopRenderTarget()
        renderJob.ScheduleOnce()
        renderJob.WaitForFinish()
        scene.depthTexture = depthTexture
        hostCopy = trinity.Tr2HostBitmap(renderTarget)
        hostCopy.name = 'hostCopy'
        if blur:
            gaussBlur = trinity.TriConvolutionMatrix5(2.0, 3.0, 5.0, 3.0, 2.0, 3.0, 4.0, 8.0, 5.0, 3.0, 5.0, 7.0, 13.0, 7.0, 5.0, 3.0, 4.0, 8.0, 5.0, 3.0, 2.0, 3.0, 5.0, 3.0, 2.0)
            blurCopy = trinity.Tr2HostBitmap(res, res, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
            blurCopy.name = 'blurCopy'
            blurCopy.ApplyConvFilter(hostCopy, gaussBlur, 0)
            hostCopy = blurCopy
        pic = uiprimitives.Sprite(align=uiconst.TOALL)
        pic.texture.atlasTexture = uicore.uilib.CreateTexture(res, res)
        pic.texture.atlasTexture.CopyFromHostBitmap(hostCopy)
        return pic

    def GetTextureFromURL(self, path, currentURL = None, ignoreCache = 0, dontcache = 0, fromWhere = None, sizeonly = 0, retry = 1):
        """
        Returns a Tr2Sprite2dTexture object from the given path. The path can be a res:
        path, or a url from the web.
        
        If 'path' is a url from the web the image is fetched and stored in the cache folder
        (unless 'dontcache' is set).
        """
        if path.endswith('.blue'):
            return self.GetPic_blue(path)
        fullPath = corebrowserutil.ParseURL(path, currentURL)[0]
        if path.startswith('res:'):
            try:
                surface = trinity.Tr2HostBitmap()
                surface.CreateFromFile(path)
                w, h = surface.width, surface.height
                bw, bh = uiutil.GetBuffersize(w), uiutil.GetBuffersize(h)
                if sizeonly:
                    return (path,
                     w,
                     h,
                     bw,
                     bh)
                return self.ReturnTexture(path, w, h, bw, bh)
            except:
                self.LogError('Failed to load image', path)
                if self.urlloading.has_key(fullPath):
                    del self.urlloading[fullPath]
                sys.exc_clear()
                return self.ErrorPic(sizeonly)

        if ignoreCache:
            sm.GetService('browserCache').InvalidateImage(fullPath)
        while self.urlloading.has_key(fullPath):
            blue.pyos.BeNice()

        if not dontcache:
            cacheData = sm.GetService('browserCache').GetFromCache(fullPath)
            if cacheData and os.path.exists(cacheData[0].replace('cache:/', blue.paths.ResolvePath(u'cache:/'))):
                if sizeonly:
                    return cacheData
                return self.ReturnTexture(*cacheData)
        try:
            self.urlloading[fullPath] = 1
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
                    g = DrawArea()
                    g.setBgColor(Transparent)
                    g.loadGIF(filename.replace(u'/', u'\\').encode('utf8'))
                    ext = 'PNG'
                    filename = u'%sBrowser/Img/%s.%s' % (blue.paths.ResolvePath(u'cache:/'), cacheID, ext)
                    g.outPNG(filename.replace(u'/', u'\\').encode('utf8'))
                surface = trinity.Tr2HostBitmap()
                surface.CreateFromFile(filename)
                w, h = surface.width, surface.height
                bw, bh = uiutil.GetBuffersize(w), uiutil.GetBuffersize(h)
                cachePath = 'cache:/Browser/Img/%s.%s' % (cacheID, ext)
                if 'pragma' not in ret.headers.keys() or ret.headers['Pragma'].find('no-cache') == -1:
                    sm.GetService('browserCache').Cache(fullPath, (cachePath,
                     w,
                     h,
                     bw,
                     bh))
                del self.urlloading[fullPath]
                if sizeonly:
                    return (cachePath,
                     w,
                     h,
                     bw,
                     bh)
                return self.ReturnTexture(cachePath, w, h, bw, bh)
            del self.urlloading[fullPath]
            return self.ErrorPic(sizeonly)
        except Exception as e:
            if retry:
                sys.exc_clear()
                if self.urlloading.has_key(fullPath):
                    del self.urlloading[fullPath]
                return self.GetTextureFromURL(path, currentURL, ignoreCache, dontcache, fromWhere, sizeonly, 0)
            self.LogError(e, 'Failed to load image', repr(path))
            if self.urlloading.has_key(fullPath):
                del self.urlloading[fullPath]
            sys.exc_clear()
            return self.ErrorPic(sizeonly)

    def ErrorPic(self, sizeonly = 0):
        if sizeonly:
            return (NONE_PATH,
             32,
             32,
             32,
             32)
        tex = trinity.Tr2Sprite2dTexture()
        tex.resPath = NONE_PATH
        return (tex, 32, 32)

    def CleanExt(self, ext):
        validNot3Letters = ('jpeg',)
        for _ext in validNot3Letters:
            if ext.lower().startswith(_ext):
                return _ext

        return ext[:3]

    def ReturnTexture(self, path, width, height, bufferwidth, bufferheight):
        tex = trinity.Tr2Sprite2dTexture()
        tex.resPath = path
        return (tex, width, height)

    def CheckDates(self, path):
        now = long(time.time())
        rem = []
        for fileName in os.listdir(path):
            if fileName.split('.')[-1] in ('blue', 'dat', 'txt'):
                continue
            lastRead = os.path.getatime(path + '/' + fileName)
            age = now - lastRead
            if age / 2592000:
                rem.append(fileName)

        for each in rem:
            os.remove(path + '/' + each)

    def InitializePortraits(self):
        """
            This can't be in the constructor, as the image server url hadn't been fetched
            from the server at that point.
        """
        if self.portraits is None:
            imageServer = self.GetImageServerURL('imageserverurl', self.defaultImageServerForUser)
            self.portraits = RemoteImageCacher('Character', self, '.jpg', imageServer)
            self.pendingPortraitGeneration = settings.user.ui.Get('pendingPortraitGeneration', set())
            for charID in self.pendingPortraitGeneration:
                self.LogInfo('Character', charID, 'is marked as newly customized.')
                self.portraits.AddToWatchList(charID, self.PortraitDownloaded)
                for size in PORTRAIT_SIZES:
                    if size == DEFAULT_PORTRAIT_SIZE:
                        continue
                    self.portraits.RemoveFromCache(charID, size)

    def PortraitDownloaded(self, charID):
        """ 
        Callback that removes character from pendingPortraitGeneration on download 
        """
        self.pendingPortraitGeneration = settings.user.ui.Get('pendingPortraitGeneration', set())
        if charID in self.pendingPortraitGeneration:
            self.pendingPortraitGeneration.discard(charID)
            settings.user.ui.Set('pendingPortraitGeneration', self.pendingPortraitGeneration)

    def GetPortrait(self, charID, size, sprite = None, orderIfMissing = True, callback = False, allowServerTrip = False):
        """
        Get character portraits
        Returns the path to the portrait if it has already been fetched, else returns None
        
        If the portrait isn't cached, it will get the portrait from the image server and
        either add it on to the sprite if there is a sprite present, or do a callback if
        sprite is None, meaning that OnPortraitCreated event will be scattered. 
        """
        self.InitializePortraits()
        if size > 64:
            defaultIcon = 'res:/UI/Texture/silhouette.png'
        else:
            defaultIcon = 'res:/UI/Texture/silhouette_64.png'
        if charID in self.pendingPortraitGeneration:
            size = DEFAULT_PORTRAIT_SIZE
        callback = 'OnPortraitCreated' if callback else None
        return self.GetImage(charID, size, self.portraits, sprite, orderIfMissing, callback, defaultIcon)

    def SavePortraits(self, charIDs):
        if type(charIDs) != list:
            charIDs = [charIDs]
        uthread.new(self._SavePortraits, charIDs)

    def GetPortraitSaveSize(self):
        """
            return the size that we should save portraits to the HD at
        """
        portraitSize = sm.GetService('machoNet').GetGlobalConfig().get('defaultPortraitSaveSize')
        if portraitSize is None:
            portraitSize = DEFAULT_PORTRAIT_SAVE_SIZE
        self.LogInfo('Portrait will be saved at', portraitSize)
        return int(portraitSize)

    def _SavePortraits(self, charIDs):
        length = len(charIDs)
        sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Shared/GeneratingPicture'), '', 0, length)
        portraitSaveSize = self.GetPortraitSaveSize()
        for i, charID in enumerate(charIDs):
            imagePath = self.portraits.GetImage(charID, portraitSaveSize, forceUpdate=True)
            if imagePath:
                cacheFile = blue.paths.ResolvePath(imagePath)
                try:
                    shutil.copy2(cacheFile, blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '/EVE/capture/Portraits/%s.jpg' % charID)
                except WindowsError as e:
                    log.LogTraceback('Failed to copy character image')
                    self.LogError(e, 'Failed to copy character image')

            sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Shared/GeneratingPicture'), '', i + 1, length)

        sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Shared/GeneratingPicture'), '', length, length)

    def GetAllianceLogo(self, allianceID, size, sprite = None, orderIfMissing = True, callback = False):
        if self.allianceLogos is None:
            imageServer = self.GetImageServerURL('imageserverurl', self.defaultImageServerForUser)
            self.allianceLogos = RemoteImageCacher('Alliance', self, '.png', imageServer)
        callback = 'OnAllianceLogoReady' if callback else None
        return self.GetImage(allianceID, size, self.allianceLogos, sprite, orderIfMissing, callback, 'res:/UI/Texture/defaultAlliance.dds', isAlliance=True)

    def GetImage(self, itemID, size, handler, sprite = None, orderIfMissing = True, callback = None, defaultIcon = 'res:/UI/Texture/notavailable.dds', isAlliance = False):
        """
        Get character portraits
        Returns the path to the portrait if it has already been fetched, else returns None
        
        If the portrait isn't cached, it will get the portrait from the image server and
        either add it on to the sprite if there is a sprite present, or do a callback if
        sprite is None, meaning that OnPortraitCreated event will be scattered. 
        
        If there did exist a cached version of this item, we will use that until we have
        a fresh version of it. 
        """
        if uicore.desktop.dpiScaling > 1.0 and not isAlliance:
            size = size * 2
        if not isinstance(itemID, numbers.Integral):
            return defaultIcon
        if util.IsDustCharacter(itemID):
            try:
                character = cfg.eveowners.Get(itemID)
                path = const.dustCharacterPortraits[int(character.gender)][cfg.invtypes.Get(character.typeID).raceID]
                isFresh = True
            except KeyError:
                return defaultIcon

        else:
            path, isFresh = handler.GetCachedImage(itemID, size)
        if sprite is not None:
            sprite.LoadTexture(path or defaultIcon)
        if not isFresh and orderIfMissing and not handler.MissingFromServer(itemID):
            if (itemID, size, handler) in self.currentlyFetching:
                self.currentlyFetching[itemID, size, handler].append([sprite, callback])
            else:
                self.imageServerQueue[itemID, size, handler].append([sprite, callback])
            if len(self.imageServerQueue) > self.fetchingFromImageServer and self.fetchingFromImageServer < MAX_PORTRAIT_THREADS:
                self.fetchingFromImageServer += 1
                uthread.pool('photo::FetchRemoteImages', self.__FetchFromImageServer)
        elif handler.MissingFromServer(itemID) and path is None:
            return defaultIcon
        if isFresh:
            return path

    def __FetchFromImageServer(self):
        self.LogInfo('Starting a image server thread')
        try:
            while len(self.imageServerQueue) > 0:
                (itemID, size, handler), orders = self.imageServerQueue.popitem()
                image = handler.GetImage(itemID, size)
                self.currentlyFetching[itemID, size, handler] = []
                if image is None:
                    continue
                orders += self.currentlyFetching.pop((itemID, size, handler))
                for sprite, callback in orders:
                    if callback:
                        sm.ScatterEvent(callback, itemID)
                    elif sprite is not None:
                        try:
                            sprite.LoadTexture(image)
                        except:
                            log.LogException('Error adding portrait to sprite')
                            sys.exc_clear()

        finally:
            self.fetchingFromImageServer -= 1

    def AddPortrait(self, portraitPath, charID):
        """
            Add a rendered portrait to image cache.
             - This copies the temp portrait to the cache directory
             - It marks the character as just customized, so this image will always be used in the client
              - That causes all cached images to be removed on portrait handling startup
        """
        self.LogInfo('Adding portrait of', charID, 'from path', portraitPath)
        try:
            shutil.copy2(portraitPath, blue.paths.ResolvePathForWriting(u'cache:/Pictures/Characters/%s_%s.jpg' % (charID, DEFAULT_PORTRAIT_SIZE)))
        except WindowsError as e:
            log.LogTraceback('Failed to copy default size character image')
            self.LogError(e, 'Failed to copy default size character image')

        try:
            shutil.copy2(portraitPath, blue.paths.ResolvePathForWriting(u'cache:/Pictures/Characters/%s_%s.jpg' % (charID, 256)))
        except WindowsError as e:
            log.LogTraceback('Failed to copy 256 px character image')
            self.LogError(e, 'Failed to copy 256 px character image')

        portraitCachePath = 'cache:/Pictures/Characters/%s_%s.jpg' % (charID, DEFAULT_PORTRAIT_SIZE)
        res = blue.resMan.GetResource(portraitCachePath, 'atlas')
        res.Reload()
        portraitCachePath_256 = 'cache:/Pictures/Characters/%s_%s.jpg' % (charID, 256)
        res = blue.resMan.GetResource(portraitCachePath_256, 'atlas')
        res.Reload()
        self.pendingPortraitGeneration = settings.user.ui.Get('pendingPortraitGeneration', set())
        self.pendingPortraitGeneration.add(charID)
        settings.user.ui.Set('pendingPortraitGeneration', self.pendingPortraitGeneration)
        if self.portraits is not None:
            self.portraits.missingImages.pop(charID, None)
            self.portraits.AddToWatchList(charID, self.PortraitDownloaded)

    def _RemovePathFromNotAvailList(self, cachename):
        try:
            del self.notavail[cachename]
            self.LogInfo('Deleted ', cachename, ' from not avail list')
        except:
            self.LogInfo(cachename, ' was not in the not avail list')

    def Do2DMap(self, sprite, ids, idLevel, drawLevel, size = 256):
        ssmap = Map2D()
        ssmap.Draw(ids, idLevel, drawLevel, size, sprite)

    def GetIconByType(self, sprite, typeID, itemID = None, size = None, ignoreSize = False, isCopy = False):
        invType = cfg.invtypes.GetIfExists(typeID)
        if not invType:
            return
        actSize = size or 64
        typeID = invType.id
        group = invType.Group()
        blueprint = BLUEPRINT_NONE
        if group.categoryID == const.categoryBlueprint:
            if isCopy:
                blueprint = BLUEPRINT_COPY
            else:
                blueprint = BLUEPRINT_NORMAL
            try:
                typeID = cfg.blueprints.Get(typeID).productTypeID
            except KeyError:
                return sprite.LoadIcon(icon=NOT_AVAILABLE_PATH, ignoreSize=ignoreSize)

            invType = cfg.invtypes.Get(typeID)
            group = invType.Group()
        elif group.categoryID == const.categoryInfantry:
            blueprint = BLUEPRINT_DUST
        elif group.categoryID == const.categoryAncientRelic:
            blueprint = BLUEPRINT_RELIC
        if itemID and group.id in (const.groupRegion, const.groupConstellation, const.groupSolarSystem):
            if not (util.IsSolarSystem(itemID) or util.IsConstellation(itemID) or util.IsRegion(itemID)):
                log.LogError('Not valid itemID for 2D map, itemID: ', itemID, ', typeID: ', typeID)
                log.LogTraceback()
            level = [const.groupRegion, const.groupConstellation, const.groupSolarSystem].index(group.id) + 1
            return self.Do2DMap(sprite, [itemID], level, level + 1, actSize)
        if TypeIsRenderable(typeID, group.id, group.categoryID):
            if group.id == const.groupCharacter:
                return self.GetPortrait(itemID, actSize, sprite)
            else:
                return self.OrderByTypeID([[typeID,
                  sprite,
                  actSize,
                  itemID,
                  blueprint]])
        else:
            iconInfo = invType.Icon()
            if iconInfo and iconInfo.iconFile:
                icon = iconInfo.iconFile.strip()
                if icon:
                    if blueprint != BLUEPRINT_NONE:
                        return self.DoBlueprint(sprite, typeID, size=actSize, blueprint=blueprint)
                    else:
                        return sprite.LoadIcon(icon=icon, ignoreSize=ignoreSize)

    def OrderByTypeID(self, orderlist):
        for each in orderlist:
            if len(each) == 4:
                typeID, wnd, size, itemID = each
                blueprint = BLUEPRINT_NONE
            else:
                typeID, wnd, size, itemID, blueprint = each
            if uicore.desktop.dpiScaling > 1.0:
                size = size * 2
            if wnd is None or wnd.destroyed:
                orderlist.remove(each)
                continue
            t = cfg.invtypes.Get(typeID)
            foundPath = self.ExistsInCacheOrRenders(t, size, itemID, blueprint)
            if foundPath:
                wnd.LoadTexture(foundPath)
                orderlist.remove(each)
                continue
            wnd.LoadTexture('res:/UI/Texture/notavailable.dds')

        for each in orderlist:
            self.byTypeIDQue.append(each)

        if not self.byTypeID_IsRunning:
            uthread.pool('photo::OrderByTypeID', self.ProduceTypeIDs)
            self.byTypeID_IsRunning = 1

    def ExistsInCacheOrRenders(self, invType, size, itemID, blueprint):
        """
        Checks whether the requested icon exists in cache or UI textures.
        :return: The path to the icon found.
        """
        graphicID = invType.GraphicID()
        if invType.Group().id == const.groupStation:
            npcStation = cfg.mapSolarSystemContentCache.npcStations.get(itemID, None)
            if npcStation:
                graphicID = npcStation.graphicID
        renderPath = GetRenderPath(graphicID, size, blueprint, invType.raceID)
        if blue.paths.exists(renderPath):
            return renderPath
        cachePath = GetCachePath(invType, size, itemID, blueprint)
        if self.CheckAvail(cachePath) is not None:
            return cachePath

    def ProduceTypeIDs(self):
        while self.byTypeIDQue:
            for order in self.byTypeIDQue:
                if len(order) == 4:
                    typeID, wnd, size, itemID = order
                    blueprint = BLUEPRINT_NONE
                else:
                    typeID, wnd, size, itemID, blueprint = order
                if wnd is None or wnd.destroyed:
                    self.byTypeIDQue.remove(order)
                    continue
                if uicore.desktop.dpiScaling > 1.0:
                    size = size * 2
                typeinfo = cfg.invtypes.Get(typeID)
                foundPath = self.ExistsInCacheOrRenders(typeinfo, size, itemID, blueprint)
                if foundPath:
                    wnd.LoadTexture(foundPath)
                    self.byTypeIDQue.remove(order)
                    continue
                try:
                    group = typeinfo.Group()
                    if group.categoryID == const.categoryPlanetaryInteraction and group.id != const.groupPlanetaryLinks:
                        photopath = self.GetPinPhoto(typeID, typeinfo=typeinfo, size=size)
                    elif group.id == const.groupSun:
                        photopath = self.GetSunPhoto(itemID, typeID, typeinfo, size)
                    elif group.id in [const.groupPlanet, const.groupMoon]:
                        photopath = self.GetPlanetPhoto(itemID, typeID, typeinfo, size)
                    elif group.id == const.groupStation and itemID:
                        photopath = self.GetStationPhoto(itemID, typeinfo, size=size, blueprint=blueprint)
                    else:
                        photopath = self.GetPhoto(typeID, typeinfo=typeinfo, size=size, blueprint=blueprint)
                except Exception:
                    self.byTypeIDQue.remove(order)
                    log.LogException('ProduceTypeIDs: Error in getPhoto for %s' % typeID)
                    sys.exc_clear()
                    continue

                if wnd is None or wnd.destroyed:
                    self.byTypeIDQue.remove(order)
                    continue
                if wnd.texture and wnd.texture.resPath[-16:] != 'notavailable.dds':
                    self.byTypeIDQue.remove(order)
                    continue
                wnd.LoadTexture(photopath)
                if photopath[-16:] == 'notavailable.dds':
                    self.byTypeIDQue.remove(order)
                    continue
                self.byTypeIDQue.remove(order)
                blue.pyos.synchro.Yield()

        self.byTypeID_IsRunning = 0

    def GetPlanetScene(self):
        """
        This method gives us a scene that uses the same backgroundEffect as the current space scene.
        It adds the starfield.
        """
        scenepath = sm.GetService('sceneManager').GetScene()
        scene = trinity.Load(scenepath)
        scene.backgroundEffect = trinity.Load('res:/dx9/scene/starfield/starfieldNebula.red')
        if scene.backgroundEffect is not None:
            for node in scene.backgroundEffect.resources.Find('trinity.TriTexture2DParameter'):
                if node.name == 'NebulaMap':
                    node.resourcePath = scene.envMap1ResPath

        scene.backgroundRenderingEnabled = True
        return scene

    def GetPlanetPhoto(self, itemID, typeID, typeinfo, size = 512):
        outPath = GetCachePath(typeinfo, size, itemID)
        planet = Planet()
        planet.GetPlanetByID(itemID, typeID)
        if planet.model is None or planet.model.highDetail is None:
            return NOT_AVAILABLE_PATH
        planetTransform = trinity.EveTransform()
        planetTransform.scaling = (100.0, 100.0, 100.0)
        planetTransform.children.append(planet.model.highDetail)
        scene = self.GetPlanetScene()
        try:
            planet.DoPreProcessEffectForPhotoSvc(size)
        except:
            del planetTransform.children[:]
            return NOT_AVAILABLE_PATH

        trinity.WaitForResourceLoads()
        scene.sunDirection = (-1.0, 0.0, 0.0)
        scene.sunDiffuseColor = (1.0, 1.0, 1.0, 1.0)
        scene.objects.append(planetTransform)
        scene.dynamicClipPlanes = False
        view, projection = camera_util.GetViewAndProjectionUsingBoundingSphere(boundingSphereRadius=130)
        bitmap = photo.RenderToSurface(view, projection, size, scene, transparent=False)
        bitmap.Save(outPath)
        del planetTransform.children[:]
        self._RemovePathFromNotAvailList(outPath)
        return outPath

    def GetSunPhoto(self, itemID, typeID, typeinfo, size = 512):
        outPath = GetCachePath(typeinfo, size, itemID)
        scenePath = sm.GetService('sceneManager').GetScene()
        graphicFile = cfg.invtypes.Get(typeID).GraphicFile()
        photo.RenderSun(outPath, graphicFile, scenePath, size)
        return outPath

    def GetScenePath(self, raceID):
        scenePaths = {const.raceCaldari: 'res:/dx9/Scene/preview/ship_caldari.red',
         const.raceMinmatar: 'res:/dx9/Scene/preview/ship_minmatar.red',
         const.raceGallente: 'res:/dx9/Scene/preview/ship_gallente.red',
         const.raceAmarr: 'res:/dx9/Scene/preview/ship_amarr.red'}
        return scenePaths.get(raceID, 'res:/dx9/Scene/preview/ship_other.red')

    def GetPinPhoto(self, typeID, typeinfo, size = 128):
        """
        Takes a picture of a Planetary Interaction UI model. Given a typeID this function
        will load the objects model and place it within a scene. A picture will be taken
        and saved to disk.
        """
        self.LogInfo('Getting Photo with typeID: ', typeID)
        outputPath = GetCachePath(typeinfo, size, 0)
        graphicFile = typeinfo.GraphicFile()
        size = int(size)
        photo.RenderPin(outputPath, graphicFile, size, freezeTime=False)
        return outputPath

    def GetStationPhoto(self, itemID, typeinfo, size = 128, blueprint = BLUEPRINT_NONE):
        """
        NPC stations have a faction name which needs to be added.
        """
        npcStation = cfg.mapSolarSystemContentCache.npcStations.get(itemID, None)
        if npcStation:
            graphicID = npcStation.graphicID
            objectPath = cfg.graphics.Get(graphicID).graphicFile
        else:
            graphicID = typeinfo.graphicID
            objectPath = typeinfo.GraphicFile()
        scenePath = self.GetScenePath(typeinfo.raceID)
        Info = namedtuple('Info', ['graphicID',
         'iconID',
         'raceID',
         'typeID',
         'groupID'])
        fakeTypeInfo = Info(graphicID, typeinfo.iconID, typeinfo.raceID, typeinfo.typeID, typeinfo.groupID)
        return self.RenderScene(fakeTypeInfo, scenePath, objectPath, size, blueprint)

    def GetPhoto(self, typeID, typeinfo = None, size = 128, blueprint = BLUEPRINT_NONE):
        """
        Renders a picture of a space object from the type info.
        """
        self.LogError('The type', typeID, 'should have a pre rendered icon!')
        typeinfo = typeinfo or cfg.invtypes.Get(typeID, None)
        size = int(size)
        scenePath = self.GetScenePath(typeinfo.raceID)
        objectPath = typeinfo.GraphicFile()
        if not objectPath:
            self.LogError('PhotoService: The type', typeID, 'has an invalid (or none) graphicID!')
            return NOT_AVAILABLE_PATH
        return self.RenderScene(typeinfo, scenePath, objectPath, size, blueprint)

    def RenderScene(self, typeinfo, scenePath, objectPath, size, blueprint):
        cachePath = GetCachePath(typeinfo, size, None, blueprint)
        outPath = blue.paths.ResolvePath(cachePath)
        backgroundPath = None
        overlayPath = None
        if blueprint == BLUEPRINT_COPY:
            backgroundPath = BLUEPRINT_COPY_RESPATH
            overlayPath = BLUEPRINT_COPY_OVERLAY_PATH
            scenePath = BLUEPRINT_SCENE
        elif blueprint == BLUEPRINT_RELIC:
            backgroundPath = BLUEPRINT_RELIC_RESPATH
            overlayPath = BLUEPRINT_RELIC_OVERLAY_PATH
            scenePath = BLUEPRINT_SCENE
        elif blueprint == BLUEPRINT_NORMAL:
            backgroundPath = BLUEPRINT_RESPATH
            overlayPath = BLUEPRINT_OVERLAY_PATH
            scenePath = BLUEPRINT_SCENE
        elif blueprint == BLUEPRINT_DUST:
            backgroundPath = BLUEPRINT_DUST_RESPATH
        techPath = None
        photo.RenderSpaceObject(outPath, scenePath=scenePath, objectPath=objectPath, size=size, bgColor=None, transparent=False, backgroundPath=backgroundPath, overlayPath=overlayPath, techPath=techPath, freezeTime=False)
        self._RemovePathFromNotAvailList(cachePath)
        return cachePath

    def GetImageServerURL(self, clientCfgValue = 'imageserverurl', defaultServer = None):
        """
            get the global config value with fall back for unpackaged servers.
        """
        imageServer = sm.GetService('machoNet').GetGlobalConfig().get(clientCfgValue)
        if imageServer is None:
            imageServer = defaultServer
        return imageServer


NOT_MODIFIED = 304
TEMP_REDIRECT = 302

class CustomRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        """
            Special handling of temp redirect so we don't follow it 
        """
        return None


class RemoteImageCacher(object):
    """
    This class fetches and caches images from the external image server via http
    """

    def __init__(self, cacheItem, logger, suffix, imageServer):
        """
        Create a new RemoteImageCacher
         - The cacheitem should be the singular form of the cached item, matching the image
           server url for that item. 
        - It will be cached in the cache directory under cache/picture/{cachItem}s
        
        F.ex: if cacheItem = "Character", and we ask for itemid 1050239 and size 256 we fetch 
            http://image.evegate.com/Character/1050239_256.jpg
        and store that under         
            "cache:/Pictures/Characters/1050239_256.jpg"
        """
        self.initialized = False
        self.LogInfo = logger.LogInfo
        self.LogError = logger.LogError
        self.LogInfo('Initializing Remote Image service for', cacheItem)
        self.opener = urllib2.build_opener(CustomRedirectHandler())
        self.cacheItem = cacheItem
        self.cacheBasePath = 'cache:/Pictures/%ss/' % self.cacheItem
        self.cacheFile = '%s_%s' + suffix
        self.missingImages = {}
        self.watchList = {}
        if imageServer == '':
            imageServer = 'http://xxx.dev.image/'
        if imageServer is None:
            self.LogError('RemoteImageCacher can not operate without a server URL!', imageServer)
            return
        imageServer = imageServer.strip().encode('ascii')
        self.imageUri = imageServer
        if not imageServer.endswith('/'):
            self.imageUri += '/'
        self.imageUri += cacheItem + '/%s_%s' + suffix
        self.LogInfo('RemoteImageCacher initialized with imageUri', self.imageUri)
        self.initialized = True

    def Initialized(self):
        return self.initialized

    def AddToWatchList(self, itemID, callback):
        """ 
         Add itemIDs to watchlist, the supplied callback function is called with
         itemID as a parameter when this item is downloaded.
        """
        self.watchList[itemID] = callback

    def GetCachePath(self, itemID, size, createPath = False):
        basePath = self.cacheBasePath
        if self.cacheItem == 'Character' and size in (32, 64):
            basePath = '%sChat/%s/' % (self.cacheBasePath, itemID % 100)
        if createPath:
            pathToFile = blue.paths.ResolvePath(basePath)
            if not os.path.exists(pathToFile):
                os.makedirs(pathToFile)
        return basePath + self.cacheFile % (itemID, size)

    def GetCachedImage(self, itemID, size):
        """
        Returns path if we have a cached version of this photo and a flag that indicates
        if it is recent enough to use.
        """
        if not self.Initialized():
            return (None, False)
        cachePath = self.GetCachePath(itemID, size)
        fileSystemPath = blue.paths.ResolvePath(cachePath)
        if os.path.exists(fileSystemPath):
            return (cachePath, self.__IsFresh(cachePath))
        return (None, False)

    def MissingFromServer(self, itemID):
        """
        Return true if images for this item are missing from the remote server, so that 
        we only try downloading missing images once per every hour.
        """
        lastTry = self.missingImages.get(itemID, None)
        if lastTry is not None:
            if time.time() - lastTry > 3600:
                del self.missingImages[itemID]
                return False
            return True
        return False

    def GetImage(self, itemID, size, forceUpdate = False):
        """
        Gets an image of the item from the remote service in the given size 
        """
        if not self.Initialized() or self.MissingFromServer(itemID) and not forceUpdate:
            return
        uthread.Lock(self, itemID)
        try:
            try:
                cachePath = self.GetCachePath(itemID, size, createPath=True)
            except Exception as e:
                self.LogError('Failed to get image cache folder', repr(e))
                self.initialized = False
                return

            cacheFile = blue.paths.ResolvePath(cachePath)
            lastModified = self.GetLastModified(cachePath)
            if forceUpdate or not self.__IsFresh(cachePath):
                self.LogInfo('Get image for', itemID, 'is fetching/refreshing image. Forced = ', forceUpdate)
                image, headerLastModifiedTime = self.__GetImageFromUrl(itemID, size, lastModified)
                if image is None:
                    self.LogInfo('No image found for', itemID, 'adding to missing images')
                    self.missingImages[itemID] = time.time()
                    return
                if image == NOT_MODIFIED:
                    self.LogInfo('Image has not been modified, updating cached image')
                    self.UpdateLastCheckedTime(cacheFile)
                else:
                    resfile = blue.classes.CreateInstance('blue.ResFile')
                    try:
                        if not resfile.Open(cachePath, 0):
                            try:
                                resfile.Create(cachePath)
                            except Exception as e:
                                self.LogError('Failed to get image cache folder', repr(e))
                                self.initialized = False
                                return

                        resfile.Write(image)
                        resfile.Close()
                        self.InvalidateResManagerForResource(cachePath)
                        self.FetchedCacheFile(cachePath, headerLastModifiedTime)
                    except Exception as e:
                        self.LogError('Failed to update cached image', repr(e))
                        return

                    if itemID in self.watchList:
                        self.LogInfo('RemoteImageCached removed item ', itemID, 'was an item in the watchlist.')
                        self.watchList[itemID](itemID)
                        del self.watchList[itemID]
        finally:
            uthread.UnLock(self, itemID)

        return cachePath

    def __GetImageFromUrl(self, charID, size, lastModified = None):
        if not self.Initialized():
            return (None, None)
        url = (self.imageUri % (charID, size)).strip().encode('ascii')
        request = urllib2.Request(url, None)
        self.LogInfo('Getting image from', url)
        if lastModified:
            cacheTime = datetime.datetime.utcfromtimestamp(lastModified)
            cacheStamp = cacheTime.strftime('%a, %d %b %Y %H:%M:%S GMT')
            request.add_header('If-Modified-Since', cacheStamp)
            self.LogInfo('adding If-Modified-Since header for', cacheStamp)
        try:
            ret = self.opener.open(request)
        except urllib2.HTTPError as e:
            if e.code == NOT_MODIFIED:
                self.LogInfo('Not Modified', url, 'since', lastModified, time.ctime(lastModified))
                return (NOT_MODIFIED, None)
            if e.code == TEMP_REDIRECT:
                self.LogInfo('Temp Redirect while getting image', str(e))
                return (None, None)
            self.LogError('Error while fetching remote image', str(e))
            sys.exc_clear()
            return (None, None)
        except urllib2.URLError as e:
            self.LogError('Error while fetching remote image', str(e))
            sys.exc_clear()
            return (None, None)

        try:
            if 'content-type' not in ret.headers.keys() or not ret.headers['content-type'].startswith('image/'):
                self.LogError(url, 'was not an actual image')
                return (None, None)
            lastModifiedTime = time.time()
            if 'last-modified' in ret.headers.keys():
                try:
                    t = datetime.datetime.strptime(ret.headers['last-modified'], '%a, %d %b %Y %H:%M:%S GMT')
                    lastModifiedTime = time.mktime(t.timetuple())
                except:
                    sys.exc_clear()

            return (ret.read(), lastModifiedTime)
        finally:
            ret.close()

    def GetLastModified(self, cachePath):
        """
            The will return the modified time of the file of None if the file doesn't 
            exist.
        """
        filepath = blue.paths.ResolvePath(cachePath)
        if os.path.exists(filepath):
            return os.path.getmtime(filepath)

    def GetLastChecked(self, cachePath):
        """
            Return the last time that we checked to see if there is a new version. 
            For this class we use the modified time of the cache file. 
        """
        return self.GetLastModified(cachePath)

    def InvalidateResManagerForResource(self, cacheFile):
        try:
            self.LogInfo('Reloading blue res', cacheFile)
            res = blue.resMan.GetResource(str(cacheFile), 'atlas')
            if res:
                res.Reload()
        except SystemError:
            sys.exc_clear()

    def FetchedCacheFile(self, cacheFile, headerLastModifiedTime):
        """
            The web get has just downloaded a cache file
        """
        pass

    def UpdateLastCheckedTime(self, cacheFile):
        """
            The base class uses the last modified time to track when was the last time we
            Fetched the file
        """
        self.UpdateFileTimeStamp(cacheFile, None)

    def UpdateFileTimeStamp(self, cacheFile, timeStamp):
        """
            Wrap the OS file call into a function that 
            passes in the file name and time stamp data
        """
        try:
            with file(cacheFile, 'a'):
                os.utime(cacheFile, timeStamp)
        except Exception as e:
            pass

    def __IsFresh(self, cachePath):
        lastModified = self.GetLastChecked(cachePath)
        if lastModified is None:
            return False
        delta = time.time() - lastModified
        return delta < MAX_CACHE_AGE

    def RemoveFromCache(self, itemID, size):
        cachePath = self.GetCachePath(itemID, size)
        filepath = blue.paths.ResolvePath(cachePath)
        if os.path.exists(filepath):
            os.remove(filepath)
