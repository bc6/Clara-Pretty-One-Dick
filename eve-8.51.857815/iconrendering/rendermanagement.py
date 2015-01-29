#Embedded file name: iconrendering\rendermanagement.py
import contextlib
import os
import time
import itertoolsext
import threadutils
import iconrendering
import iconrendering.photo as photo
import iconrendering.rendersetup as rendersetup
from iconrendering import USAGE_IEC_ICON, USAGE_IEC_RENDER, USAGE_INGAME_ICON
import inventorycommon.const as invconst
from fsdhelpers import LoadFSDFromResFile

class RenderCancelledError(iconrendering.IconRenderingException):
    pass


class RenderManager(object):
    """Manages the high-level rendering of images.
    
    Embodies the highly-specific logic of how renders are managed
    (file paths, sizes, progress reporting, etc.).
    
    Calling ``Stop`` stops the rendering at the next earliest opportunity.
    The manager is **not** reusable afterwards and must be fully reinitialized.
    
    Subclasses can customize behavior (for example, supporting parallelization)
    by overriding the following:
    
    - `_Invoke`, which invokes the render function with the provided args.
    - `_OnRenderError`, which is called when `_Invoke` errors.
    
    :param takeonly: Number of items of each type to render
      (so 10 would render 10 'Renders', 10 Type32, 10 Type64, and all icons).
    """

    def __init__(self, resmapper, inventorymapper, logger, outdir, takeonly = None, renderCB = None):
        self.logger = logger
        self.outdir = outdir
        self.takeonly = takeonly
        self.resmapper = resmapper
        self.inventoryMapper = inventorymapper
        self.renderCB = renderCB
        self.stopToken = threadutils.Token()
        logger.info('Starting %s', iconrendering.APPNAME)
        logger.info('Output: %s', outdir)

    def RenderAll(self):
        with self._TimeIt('All Renderings'):
            self.RenderRenders()
            self.RenderTypes32()
            self.RenderTypes64()
            self.CopyIcons()

    def RenderInGameIcons(self):
        with self._TimeIt('In Game Icon Renderings'):
            self._RenderAll('', 128, filterFunc=rendersetup.FilterForIngameIconsNoBluePrints, usage=USAGE_INGAME_ICON)
            self._RenderAll('', 64, filterFunc=rendersetup.FilterForIngameIcons, usage=USAGE_INGAME_ICON)

    def RenderTypes32(self):
        self._RenderTypes(32)

    def RenderTypes64(self):
        self._RenderTypes(64)

    def _RenderTypes(self, size):
        with self._TimeIt('Types%s' % size):
            self._RenderAll('Types', size, filterFunc=rendersetup.FilterForTypes, usage=USAGE_IEC_ICON)

    def RenderRenders(self):
        with self._TimeIt('Renders'):
            self._RenderAll('Renders', 512, filterFunc=rendersetup.FilterForRenders, usage=USAGE_IEC_RENDER)

    def CopyIcons(self):
        with self._TimeIt('Icons'):
            rendersetup.CopyIconDirs(self.outdir)

    def RenderNPCStations(self):
        with self._TimeIt('In Game Icon NPC Stations'):
            self._RenderNPCStations()

    def _RenderNPCStations(self):
        resPath = 'res:/../../autobuild/staticData/client/solarSystemContent.static'
        self.logger.debug('Loading Universe FSD data for NPC stations')
        solarSystems = LoadFSDFromResFile(resPath)
        self.logger.debug('Done loading Universe FSD data for NPC stations')
        stationData = solarSystems.npcStations
        uniqueRenders = set()
        for stationID, stationInfo in stationData.iteritems():
            graphicID = stationInfo.graphicID
            typeID = stationInfo.typeID
            typeData = self.inventoryMapper.GetTypeData(typeID)
            raceID = typeData[2]
            uniqueRenders.add((graphicID,
             typeID,
             raceID,
             128))
            uniqueRenders.add((graphicID,
             typeID,
             raceID,
             64))

        uniqueRenders = list(uniqueRenders)
        uniqueRenders.sort()
        for graphicID, typeID, raceID, size in uniqueRenders:
            func, funcargs = rendersetup.GetNPCStationRenderFuncAndArgs(self.resmapper, typeID, graphicID, raceID, size, self.outdir)
            funcname = getattr(func, '__name__', 'no func name')
            if self.stopToken.IsSet():
                raise RenderCancelledError()
            try:
                if os.path.exists(funcargs[0]):
                    self.logger.debug('File exists! %s' % funcargs[0])
                else:
                    self.logger.debug('Invoking: %s, %s', funcname, funcargs)
                    self._Invoke(func, funcargs, size)
            except Exception:
                self._OnRenderError(size, funcname, funcargs)

    def _RenderAll(self, subdir, size, **yieldKwargs):
        outdir = os.path.join(self.outdir, subdir)
        for vals in self._YieldRenderFuncAndArgs(outdir, size, **yieldKwargs):
            if vals is None:
                continue
            func, funcargs = vals
            funcname = getattr(func, '__name__', 'no func name')
            if self.stopToken.IsSet():
                raise RenderCancelledError()
            try:
                if os.path.exists(funcargs[0]):
                    self.logger.debug('File exists! %s' % funcargs[0])
                else:
                    self.logger.debug('Invoking: %s, %s', funcname, funcargs)
                    self._Invoke(func, funcargs, size)
            except Exception:
                self._OnRenderError(size, funcname, funcargs)

            if self.renderCB is not None:
                self.renderCB(func, funcargs, size)

    def _YieldRenderFuncAndArgs(self, outdir, size, **kwargs):
        getargs = rendersetup.YieldAllRenderFuncsAndArgs(self.resmapper, self.inventoryMapper, outdir, size, self.logger, **kwargs)
        if self.takeonly:
            self.logger.warn('Rendering only %s images.', self.takeonly)
            getargs = itertoolsext.take(getargs, self.takeonly)
        return getargs

    def RenderSingle(self, resPath = None, dnaString = None):
        if resPath is None and dnaString is None:
            self.logger.warn('Neither resPath nor dna was supplied!')
            return
        with self._TimeIt('RenderSingle'):
            self._RenderSingle(128, filterFunc=rendersetup.FilterForIngameIconsNoBluePrints, usage=USAGE_INGAME_ICON, resPath=resPath, dnaString=dnaString)
            self._RenderSingle(64, filterFunc=rendersetup.FilterForIngameIcons, usage=USAGE_INGAME_ICON, resPath=resPath, dnaString=dnaString)

    def _RenderSingle(self, size, resPath = None, dnaString = None, **yieldKwargs):
        types = self.resmapper.GetTypesForResPath(resPath)
        types += self.resmapper.GetTypesForSOFData(dnaString)
        typeDatas = self.inventoryMapper.GetTypesData(types)
        filteredTypeData = [ x for x in typeDatas if x[2] != invconst.categoryBlueprint ]
        blueprintTypes = map(self.inventoryMapper.GetBlueprintThatMakesType, types)
        blueprintTypes = filter(None, blueprintTypes)
        blueprintTypeData = self.inventoryMapper.GetTypesData(blueprintTypes)
        filteredTypeData.extend(blueprintTypeData)
        for vals in self._YieldRenderFuncAndArgs(self.outdir, size, typeDatas=filteredTypeData, **yieldKwargs):
            if vals is None:
                continue
            func, funcargs = vals
            funcname = getattr(func, '__name__', 'no func name')
            if self.stopToken.IsSet():
                raise RenderCancelledError()
            try:
                if os.path.exists(funcargs[0]):
                    self.logger.debug('File exists! %s' % funcargs[0])
                else:
                    self.logger.debug('Invoking: %s, %s', funcname, funcargs)
                    self._Invoke(func, funcargs, size)
            except Exception:
                self._OnRenderError(size, funcname, funcargs)

            if self.renderCB is not None:
                self.renderCB(func, funcargs, size)

    def Stop(self):
        self.logger.info('Stop requested.')
        self.stopToken.Set()

    def _Invoke(self, func, funcargs, size = None):
        return func(*funcargs)

    def _OnRenderError(self, size, funcname, funcargs):
        self.logger.error('Error: %s, %s', funcname, funcargs)
        self.logger.debug('Fallback: RenderIcon(%s size=%s)', funcargs[0], size)
        photo.RenderIcon(funcargs[0], size=size, iconPath=rendersetup.FALLBACK_ICON)

    @contextlib.contextmanager
    def _TimeIt(self, name):
        t = time.clock()
        self.logger.info('Starting %s', name)
        yield
        self.logger.info('Finished %s in %ds', name, time.clock() - t)
