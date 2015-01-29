#Embedded file name: inifile.py
"""

   inifile.py

   Author:    Matthias Gudmundsson
   Created:   2002.09.25
   Project:   Framework

   Description:

       Does .ini file handling. By default, two handlers are created and
       added to builtins as the global variables 'boot' and 'prefs':

       'start' is bound to start.ini (previously boot.ini) file in the root directory.
       'prefs' is bound to prefs.ini file in the cache directory.


   Note! This file is executed by Blue very early on which means that the
   'boot' and 'prefs' variables are available before any other script is
   executed.

   'boot' contains the startup settings. By default it uses "boot.ini"
   file but that can be overridden by setting a command line argument
   like this: /config=alternative.ini

   The boot values are always read-only, but can be updated with
   new entries but the changes will not be written back to disk.

   'prefs' contains all other settings the app might want to store.
   The file used is always "prefs.ini" in the cache folder.

   (c) CCP 2000, 2001, 2002


   Revisions:

   2002.09.25   Created.

"""
import blue
import sys
blue.pyos.taskletTimer.active = True
sys.setmemcontextsactive(True)
import blue.win32
import os
import warnings
from eveprefs import DEFAULT_ENCODING, Handler
from eveprefs.iniformat import IniIniFile as IniFile
import whitelistpickle
import builtinmangler
builtinmangler.MangleBuiltins()
os.stat_float_times(False)
whitelistpickle.patch_cPickle()

class InstallWarningHandler(object):

    def __init__(self):
        self.oldhandler = warnings.showwarning
        warnings.showwarning = self.ShowWarning

    def __del__(self):
        if warnings:
            warnings.showwarning = self.oldhandler

    def ShowWarning(self, message, category, filename, lineno, file = None):
        import logmodule
        string = warnings.formatwarning(message, category, filename, lineno)
        logmodule.LogTraceback(extraText=string, severity=logmodule.LGWARN, nthParent=3)
        if not file:
            file = sys.stderr
        print >> file, string


warningHandler = InstallWarningHandler()

def SetClusterPrefs(prefsinst):
    if prefsinst.GetValue('clusterName', None) is None:
        prefsinst.clusterName = blue.pyos.GetEnv().get('COMPUTERNAME', 'LOCALHOST') + '@' + blue.pyos.GetEnv().get('USERDOMAIN', 'NODOMAIN')
    if prefsinst.GetValue('clusterMode', None) is None:
        prefsinst.clusterMode = 'LOCAL'
    prefsinst.clusterName = prefsinst.clusterName.upper()
    prefsinst.clusterMode = prefsinst.clusterMode.upper()


boot = None
prefs = None

def Init():
    global prefs
    global boot
    import __builtin__
    if hasattr(__builtin__, 'prefs'):
        return (boot, prefs)
    if blue.pyos.packaged and 'client' in blue.paths.ResolvePath(u'app:/'):
        handler = Handler(IniFile('start', blue.paths.ResolvePath(u'root:/'), 1))
    else:
        handler = Handler(IniFile('start', blue.paths.ResolvePath(u'app:/'), 1))
    __builtin__.boot = handler
    boot = handler
    packagedClient = blue.pyos.packaged and handler.role == 'client'
    commonPath = blue.paths.ResolvePath(u'root:/common/')
    if packagedClient:
        commonPath = blue.paths.ResolvePath(u'root:/')
    handler.keyval.update(IniFile('common', commonPath, 1).keyval)
    if '/LUA:OFF' in blue.pyos.GetArg() or boot.GetValue('role', None) != 'client':
        if boot.GetValue('role', None) == 'client':
            blue.paths.SetSearchPath('cache', blue.paths.ResolvePathForWriting(u'root:/cache'))
            blue.paths.SetSearchPath('settings', blue.paths.ResolvePathForWriting(u'root:/settings'))
        else:
            blue.paths.SetSearchPath('cache', blue.paths.ResolvePathForWriting(u'app:/cache'))
            blue.paths.SetSearchPath('settings', blue.paths.ResolvePathForWriting(u'app:/settings'))
        cachepath = blue.paths.ResolvePathForWriting(u'cache:/')
        settingspath = blue.paths.ResolvePathForWriting(u'cache:/')
        prefsfilepath = cachepath
        for path in (cachepath, settingspath):
            try:
                os.makedirs(path)
            except OSError:
                pass

    else:
        import utillib as util
        cachedir = util.GetClientUniqueFolderName()
        root = blue.win32.SHGetFolderPath(blue.win32.CSIDL_LOCAL_APPDATA) + u'\\CCP\\EVE\\'
        root = root.replace('\\', '/')
        root = root + cachedir + u'/'
        settingspath = root + u'settings/'
        cachepath = root + u'cache/'
        blue.paths.SetSearchPath('cache', cachepath)
        blue.paths.SetSearchPath('settings', settingspath)
        prefsfilepath = settingspath.replace('\\', '/')
        pre = blue.win32.SHGetFolderPath(blue.win32.CSIDL_LOCAL_APPDATA) + u'\\CCP\\EVE\\'
        oldsettingspath = pre + u'settings/'
        if os.path.exists(oldsettingspath) and not os.path.exists(settingspath):
            for path in (settingspath, cachepath):
                try:
                    os.makedirs(path)
                except OSError:
                    pass

            import shutil
            for dir in os.walk(oldsettingspath):
                for file in dir[2]:
                    src = dir[0] + u'\\' + file
                    dst = blue.os.settingspath + file
                    shutil.copyfile(src, dst)

        for path in (settingspath, cachepath):
            try:
                os.makedirs(path)
            except OSError:
                pass

    handler = Handler(IniFile('prefs', prefsfilepath))
    __builtin__.prefs = handler
    prefs = handler
    sys.setdefaultencoding(DEFAULT_ENCODING)
    if boot.role == 'server':
        if '/proxy' in blue.pyos.GetArg():
            boot.role = 'proxy'
    SetClusterPrefs(handler)
    if boot.role in ('proxy', 'server') and prefs.GetValue('mpi', False):
        import MPI
    return (boot, prefs)
