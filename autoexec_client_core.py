#Embedded file name: autoexec_client_core.py
import __builtin__
import os
import sys
from . import autoexec_common
import blue
import bluepy
from . import builtinmangler
import carbon.common.script.util.numerical as numerical
from . import launcherapi
from . import whitelist
import everesourceprefetch
import logmodule
import trinity
import remotefilecache
import _winreg
bootWatchdog = launcherapi.ClientBootManager()
INLINE_SERVICES = ('DB2', 'machoNet', 'config', 'objectCaching', 'dataconfig', 'dogmaIM', 'device')

def Startup(appCacheDirs, userCacheDirs, servicesToRun):
    blue.os.sleeptime = 0
    _InitializeRemoteFileCacheIfNeeded()
    _PrepareRenderer()
    args = blue.pyos.GetArg()[1:]
    if '/thinclient' in args:
        import thinclients, thinclients.clientsetup
        if thinclients.HEADLESS in args:
            thinclients.clientsetup.patch_all()
        elif thinclients.HEADED in args:
            thinclients.clientsetup.enable_live_updates()
            thinclients.clientsetup.install_commands()
        else:
            raise RuntimeError('Bad params.')
    autoexec_common.LogStarting('Client')
    bootWatchdog.SetPercentage(10)
    if '/black' in args:
        blue.resMan.substituteBlackForRed = True
    if '/jessica' in args and '/localizationMonitor' in args:
        servicesToRun += ('localizationMonitor',)
    bootWatchdog.SetPercentage(20)
    builtinmangler.SmashNastyspaceBuiltinConflicts()
    whitelist.InitWhitelist()
    import localization
    localization.LoadLanguageData()
    errorMsg = {'resetsettings': [localization.GetByLabel('UI/ErrorDialog/CantClearSettings'), localization.GetByLabel('UI/ErrorDialog/CantClearSettingsHeader'), localization.GetByLabel('UI/ErrorDialog/CantClearSettings')],
     'clearcache': [localization.GetByLabel('UI/ErrorDialog/CantClearCache'), localization.GetByLabel('UI/ErrorDialog/CantClearCacheHeader'), localization.GetByLabel('UI/ErrorDialog/CantClearCache')]}
    if not getattr(prefs, 'disableLogInMemory', 0):
        blue.logInMemory.capacity = 1024
        blue.logInMemory.Start()
    bootWatchdog.SetPercentage(30)
    for clearType, clearPath in [('resetsettings', blue.paths.ResolvePath(u'settings:/')), ('clearcache', blue.paths.ResolvePath(u'cache:/'))]:
        if getattr(prefs, clearType, 0):
            if clearType == 'resetsettings':
                prefs.DeleteValue(clearType)
            if os.path.exists(clearPath):
                i = 0
                while 1:
                    newDir = clearPath[:-1] + '_backup%s' % i
                    if not os.path.isdir(newDir):
                        try:
                            os.makedirs(newDir)
                        except:
                            blue.win32.MessageBox(errorMsg[clearType][0], errorMsg[clearType][1], 272)
                            bluepy.Terminate(errorMsg[clearType][2])
                            return False

                        break
                    i += 1

                for filename in os.listdir(clearPath):
                    if filename != 'Settings':
                        try:
                            os.rename(clearPath + filename, '%s_backup%s/%s' % (clearPath[:-1], i, filename))
                        except:
                            blue.win32.MessageBox(errorMsg[clearType][0], errorMsg[clearType][1], 272)
                            bluepy.Terminate(errorMsg[clearType][2])
                            return False

                prefs.DeleteValue(clearType)

    mydocs = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL)
    paths = [blue.paths.ResolvePath(u'cache:/')]
    for dir in appCacheDirs:
        paths.append(blue.paths.ResolvePath(u'cache:/') + dir)

    for dir in userCacheDirs:
        paths.append(mydocs + dir)

    for path in paths:
        try:
            os.makedirs(path)
        except OSError as e:
            sys.exc_clear()

    import base
    import const
    session = base.CreateSession(None, const.session.SESSION_TYPE_GAME)
    __builtin__.session = session
    __builtin__.charsession = session
    base.EnableCallTimers(2)
    _InitializeEveBuiltin()
    autoexec_common.LogStarted('Client')
    bootWatchdog.SetPercentage(40)
    bluepy.frameClock = numerical.FrameClock()
    blue.os.frameClock = bluepy.frameClock
    import service
    srvMng = service.ServiceManager(startInline=INLINE_SERVICES)
    bootWatchdog.SetPercentage(50)
    if hasattr(prefs, 'http') and prefs.http:
        logmodule.general.Log('Running http', logmodule.LGINFO)
        srvMng.Run(('http',))
    srvMng.Run(servicesToRun)
    title = '[%s] %s %s %s.%s pid=%s' % (boot.region.upper(),
     boot.codename,
     boot.role,
     boot.version,
     boot.build,
     blue.os.pid)
    blue.os.SetAppTitle(title)
    try:
        blue.EnableBreakpad(prefs.GetValue('breakpadUpload', 1) == 1)
    except RuntimeError:
        pass

    blue.os.frameTimeTimeout = prefs.GetValue('frameTimeTimeout', 30000)
    if '/skiprun' not in args:
        if '/webtools' in args:
            ix = args.index('/webtools') + 1
            pr = args[ix]
            pr = pr.split(',')
            srvMng.StartService('webtools').SetVars(pr)
        srvMng.GetService('gameui').StartupUI(0)


def _InitializeEveBuiltin():
    import eve.client.script.sys.eveinit as eveinit
    eve = eveinit.Eve(__builtin__.session)
    __builtin__.eve = eve


def _GetResfileServerAndIndexFromArgs():
    resfileServer = None
    resfileIndex = None
    forceResFileServer = False
    if blue.pyos.packaged:
        if not blue.paths.exists('app:/res.stuff'):
            forceResFileServer = True
    if forceResFileServer or blue.os.HasStartupArg('resfileserver'):
        resfileServer = 'http://res.eveprobe.ccpgames.com/'
        argValue = blue.os.GetStartupArgValue('resfileserver')
        if argValue:
            params = argValue.split(',')
            resfileServer = params[0]
            if len(params) > 1:
                resfileIndex = params[1]
        if not resfileIndex:
            resfileIndex = 'app:/resfileindex.txt'
    if resfileServer:
        if not resfileServer.startswith('http'):
            resfileServer = str('http://%s' % resfileServer)
    return (resfileIndex, resfileServer)


def _GetSharedCacheFolderFromRegistry():
    """
    Look in the registry for the configured cache folder.
    If there is no entry, then we create one.
    :return:
    """
    _winreg.aReg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    try:
        key = _winreg.OpenKey(_winreg.aReg, 'SOFTWARE\\CCP\\EVEONLINE')
        path, _ = _winreg.QueryValueEx(key, 'CACHEFOLDER')
    except OSError:
        return

    return path


def _SetRemoteFileCacheFolderFromArgs():
    folder = blue.os.GetStartupArgValue('remotefilecachefolder')
    if not folder:
        shared_cache_folder = _GetSharedCacheFolderFromRegistry()
        if shared_cache_folder:
            folder = os.path.join(shared_cache_folder, 'ResFiles')
        else:
            folder = remotefilecache.get_default_cache_folder()
    remotefilecache.set_cache_folder(folder)


def _InitializeRemoteFileCache(resfileServer, resfileIndex):
    _SetRemoteFileCacheFolderFromArgs()
    remotefilecache.prepare(resfileIndex, resfileServer)


def _InitializeRemoteFileCacheIfNeeded():
    resfileIndex, resfileServer = _GetResfileServerAndIndexFromArgs()
    if resfileServer and resfileIndex:
        _InitializeRemoteFileCache(resfileServer, resfileIndex)
        logmodule.general.Log('Remote file caching enabled', logmodule.LGINFO)
        _ScheduleBackgroundDownloads()


def _PrepareRenderer():
    prefetch_set = set()
    remotefilecache.gather_files_to_prefetch('res:/graphics/shaders/compiled/' + trinity.platform, prefetch_set)
    if not blue.paths.FileExistsLocally(trinity.SHADERLIBRARYFILENAME):
        prefetch_set.add(trinity.SHADERLIBRARYFILENAME)
    remotefilecache.prefetch_files(prefetch_set)
    trinity.PopulateShaderLibrary()


def _ScheduleBackgroundDownloads():
    everesourceprefetch.PrepareFilesets()
    keys = ['staticdata',
     'ui_basics',
     'ui_classes',
     'low_detail_ships',
     'medium_detail_ships',
     'black_files',
     'ui_cc']
    for each in keys:
        everesourceprefetch.Schedule(each)


def StartClient(appCacheDirs, userCacheDirs, servicesToRun):
    t = blue.pyos.CreateTasklet(Startup, (appCacheDirs, userCacheDirs, servicesToRun), {})
    t.context = '^boot::autoexec_client'
