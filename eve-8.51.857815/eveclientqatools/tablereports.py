#Embedded file name: eveclientqatools\tablereports.py
import blue
import trinity
import uicontrols
import uthread
import util

def CreateTableWindow(name, caption, contentFunction, minWidth = 340, updateFreq = 1000):
    """
    Returns a callable function taking no arguments that creates a table report in a window.
    
    name - name used to identify the window
    caption - the window's caption
    contentFunction - a function that's called to get content for the table. The function should
        return a tuple with three values, a list of values for each row of the table,
        a format string for the content values and a list of headers for each column.
    minWidth - minimum width of the window created
    updateFreq - how frequently the report should be updated in milliseconds.
    """

    def _closure():
        winID = 'Insider' + name + 'Window'
        uicontrols.Window.CloseIfOpen(windowID=winID)
        wnd = uicontrols.Window.Open(windowID=winID)
        wnd.SetTopparentHeight(0)
        wnd.SetMinSize([minWidth, 100])
        wnd.SetCaption(caption)
        main = wnd.GetMainArea()
        scroll = uicontrols.Scroll(parent=main)
        scroll.sr.id = 'insider' + name + 'Scroll'

        def _updateList():
            while uicontrols.Window.IsOpen(windowID=winID):
                contentList, layout, headers = contentFunction()
                scrolllist = []
                for entry in contentList:
                    label = layout % entry
                    scrolllist.append(uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, label=label))

                scroll.Load(contentList=scrolllist, headers=headers, fixedEntryHeight=18)
                blue.synchro.SleepWallclock(updateFreq)

        uthread.new(_updateList)

    return _closure


def ShowBlueResourceReport():

    def BlueResDebugCont():
        """ Generates content for warp effect debug report. See CreateTableWindow"""
        label = '%s<t>%s<t>%i'
        headers = ['type', 'path', 'memory(kB)']
        types = {'gr2': 'granny',
         'sm_': 'shader',
         'dds': 'texture'}
        memoryTotal = {'granny': 0,
         'shader': 0,
         'texture': 0,
         'other': 0,
         'all': 0}
        contentList = []
        for key in blue.motherLode.keys():
            obj = blue.motherLode.Lookup(key)
            mem = -1
            if hasattr(obj, 'GetMemoryUsage'):
                mem = obj.GetMemoryUsage()
            splitKey = key.split('.')
            resType = 'other'
            if len(splitKey[-1]) >= 3:
                resType = types.get(splitKey[-1][:3], 'other')
            if mem > -1:
                memoryTotal[resType] += mem
                memoryTotal['all'] += mem
            contentList.append((resType, key, mem / 1024))

        contentList.append(('TOTAL:', 'Total Memory Textures', memoryTotal['texture'] / 1024))
        contentList.append(('TOTAL:', 'Total Memory Shaders', memoryTotal['shader'] / 1024))
        contentList.append(('TOTAL:', 'Total Memory Granny', memoryTotal['granny'] / 1024))
        contentList.append(('TOTAL:', 'Total Memory Other', memoryTotal['other'] / 1024))
        contentList.append(('TOTAL:', 'Total Memory', memoryTotal['all'] / 1024))
        return (contentList, label, headers)

    CreateTableWindow('BlueResources', 'Blue Resources', BlueResDebugCont, updateFreq=10000)()


def ShowWarpEffectReport():

    def WarpEffectDebugCont():
        """ Generates content for warp effect debug report. See _CreateTableWindow"""
        fxs = sm.GetService('FxSequencer')
        label = '%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s'
        headers = ['myWarp',
         'gfx',
         'gfx.display',
         'gfxModel',
         'prepared',
         'started',
         'aligned',
         'stopRequested']
        contentList = []
        for actKey in fxs.activations:
            activation = fxs.activations[actKey]
            effect = activation.effect
            if getattr(effect, '__guid__', None) == 'effects.Warping':
                mine = str(effect.GetEffectShipID() == session.shipid)
                prepared = str(getattr(effect, 'debugPrepared', False))
                started = str(getattr(effect, 'debugStarted', False))
                gfx = str(getattr(effect.gfx, '__bluetype__', 'None'))
                gfxDisplay = str(getattr(effect.gfx, 'display', False))
                gfxModel = str(getattr(getattr(effect, 'gfxModel', None), '__bluetype__', None))
                stopRequested = str(getattr(effect, 'debugStopRequested', False))
                aligned = str(getattr(effect, 'debugAligned', False))
                contentList.append((mine,
                 gfx,
                 gfxDisplay,
                 gfxModel,
                 prepared,
                 started,
                 aligned,
                 stopRequested))

        return (contentList, label, headers)

    CreateTableWindow('WarpEffectDebug', 'Warp Debug', WarpEffectDebugCont)()


def ShowEffectActivationReport():

    def EffectActivationsCont():
        """ Generates content for effect activation table report. See _CreateTableWindow"""
        fxs = sm.GetService('FxSequencer')
        label = '%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s'
        headers = ['activation',
         'guid',
         'duration',
         'repeat',
         'targetID',
         'shipID',
         'moduleID',
         'moduleTypeID']
        contentList = []
        for actKey in fxs.activations:
            activation = fxs.activations[actKey]
            for trigger in activation.triggers:
                item = [actKey]
                for key in headers[1:]:
                    item.append(str(trigger[key]))

                contentList.append((item[0],
                 item[1],
                 item[2],
                 item[3],
                 item[4],
                 item[5],
                 item[6],
                 item[7]))

            if len(activation.triggers) == 0:
                item = [actKey]
                for key in headers[1:]:
                    item.append('invalid')

                contentList.append((item[0],
                 item[1],
                 item[2],
                 item[3],
                 item[4],
                 item[5],
                 item[6],
                 item[7]))

        return (contentList, label, headers)

    CreateTableWindow('EffectActivations', 'Effect Activations', EffectActivationsCont, updateFreq=5000)()


def ShowPlanetStatusReport():

    def PlanetStatusCont():
        """ Generates content for planet status table report. See _CreateTableWindow"""
        planets = sm.GetService('space').planetManager.planets
        contentList = []
        for planet in planets:
            model = planet.model
            mainItem = (planet.id,
             model.requiredTextureSize,
             model.currentTextureSize,
             model.warping,
             model.ready,
             model.forceResourceLoading)
            contentList.append(mainItem)

        label = '%i<t>%s<t>%i<t>%i<t>%s<t>%s'
        headers = ['planetID',
         'reqTextureSize',
         'curTextureSize',
         'warping',
         'res ready',
         'force load']
        return (contentList, label, headers)

    CreateTableWindow('PlanetStatus', 'Planet Status', PlanetStatusCont, updateFreq=2500)()


def ShowPlanetTextureReport():

    def PlanetTextureCont():
        """ Generates content for planet texture table report. See _CreateTableWindow"""
        planets = sm.GetService('space').planetManager.planets
        contentList = []
        for planet in planets:
            tex2DParams = [ param for param in planet.model.Find('trinity.TriTexture2DParameter') if param.resource is not None ]
            for param in tex2DParams:
                resID = str(param.resource).split('(')[1].split(')')[0]
                format = trinity.PIXEL_FORMAT.GetNameFromBitmask(param.resource.format)
                contentList.append((planet.id,
                 param.name,
                 param.resource.width,
                 param.resource.height,
                 resID,
                 format))

        label = '%i<t>%s<t>%i<t>%i<t>%s<t>%s'
        headers = ['planetID',
         'texture',
         'texWidth',
         'texHeight',
         'resource',
         'format']
        return (contentList, label, headers)

    CreateTableWindow('PlanetTextures', 'Planet Textures', PlanetTextureCont, updateFreq=5000)()


def ShowManagedRTReport():

    def ManagedRTReportCont():
        """ Generates content for Managed Render Target table report. See _CreateTableWindow"""
        rtm = trinity.renderTargetManager
        depthStencilFun = trinity.RenderTargetManager._CreateDepthStencilAL
        renderTargetFun = trinity.RenderTargetManager._CreateRenderTargetAL
        renderTargetMsaaFun = trinity.RenderTargetManager._CreateRenderTargetMsaaAL
        contentList = []
        for each in rtm.targets:
            targetName = rtm.targets[each].object.name
            if each[0] == depthStencilFun:
                fun, index, width, height, format, msaaType, msaaQuality = each
                fmt = trinity.DEPTH_STENCIL_FORMAT.GetNameFromBitmask(format)
            elif each[0] == renderTargetFun:
                fun, index, width, height, mipLevels, format = each
                msaaType = 0
                fmt = trinity.PIXEL_FORMAT.GetNameFromBitmask(format)
            else:
                fun, index, width, height, format, msaaType, msaaQuality = each
                fmt = trinity.PIXEL_FORMAT.GetNameFromBitmask(format)
            contentList.append((fmt,
             width,
             height,
             msaaType,
             index,
             targetName))

        label = '%s<t>%i<t>%i<t>%i<t>%i<t>%s'
        headers = ['format',
         'width',
         'height',
         'msaaType',
         'id',
         'name']
        return (contentList, label, headers)

    CreateTableWindow('ManagedRT', 'Managed RTs', ManagedRTReportCont, updateFreq=5000)()


def ShowLODOverviewReport():

    def SpaceLODOverviewCont():
        """ Generates content for LOD table report. See _CreateTableWindow"""
        scene = sm.GetService('sceneManager').GetActiveScene()
        content = []
        trackingDict = {'trinity.EveEffectRoot': {key:0 for key in range(-1, 4)},
         'trinity.EveShip2': {key:0 for key in range(-1, 4)},
         'trinity.EveStation2': {key:0 for key in range(-1, 4)},
         'trinity.EveRootTransform': {key:0 for key in range(-1, 4)},
         'trinity.EveTurretSet': {key:0 for key in range(-1, 4)}}
        label = '%s<t>%i<t>%i<t>%i<t>%i<t>%i'
        headers = ['key',
         'total',
         'invalid',
         'high',
         'medium',
         'low']
        if scene is None:
            return (content, label, headers)
        for each in scene.objects:
            if each.__bluetype__ not in trackingDict:
                continue
            trackingDict[each.__bluetype__][each.lodLevel] += 1
            for turretSet in getattr(each, 'turretSets', []):
                lod = 3
                if 2 == turretSet.lodLevel:
                    lod = 1
                trackingDict['trinity.EveTurretSet'][lod] += 1

        for each in trackingDict:
            entry = trackingDict[each]
            entryText = each.split('.')[1]
            count = reduce(lambda x, y: x + y, entry.values())
            content.append((entryText,
             count,
             entry[0],
             entry[1],
             entry[2],
             entry[3]))

        return (content, label, headers)

    CreateTableWindow('SpaceLOD', 'LOD Report', SpaceLODOverviewCont)()


def ShowExplosionPoolReport():

    def ExplosionPoolCont():
        """ Generates content for explosion pool table report. See _CreateTableWindow"""
        em = util.ExplosionManager()
        contentList = []
        for pool in em.pooledExplosions.values():
            poolID = pool.path.split('/')[-1]
            contentList.append((poolID,
             pool.total,
             pool.active,
             pool.inactive,
             pool.refCount,
             max(pool.maxRecentUsed),
             pool.totalLoads))

        label = '%s<t>%i<t>%i<t>%i<t>%i<t>%i<t>%i'
        headers = ['pool',
         'size',
         'active',
         'inactive',
         'refs',
         'maxRecent',
         'loads']
        return (contentList, label, headers)

    CreateTableWindow('ExplosionPools', 'Explosion Pools', ExplosionPoolCont)()
