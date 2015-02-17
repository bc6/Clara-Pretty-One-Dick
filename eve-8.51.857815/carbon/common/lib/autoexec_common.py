#Embedded file name: carbon/common/lib\autoexec_common.py
import os
import sys
import blue
import logmodule
import stdlogutils.logserver as stdlogserver
stdlogserver.InitLoggingToLogserver(stdlogserver.GetLoggingLevelFromPrefs())
try:
    import marshalstrings
except ImportError:
    pass

def ReturnFalse():
    return False


def LogStarting(mode):
    startedat = '%s %s version %s build %s starting %s %s' % (boot.appname,
     mode,
     boot.version,
     boot.build,
     blue.os.FormatUTC()[0],
     blue.os.FormatUTC()[2])
    print startedat
    logmodule.general.Log(startedat, logmodule.LGNOTICE)
    logmodule.general.Log('Python version: ' + sys.version, logmodule.LGNOTICE)
    if blue.win32.IsTransgaming():
        logmodule.general.Log('Transgaming? yes')
        try:
            blue.win32.TGGetOS()
            blue.win32.TGGetSystemInfo()
        except NotImplementedError:
            logmodule.general.Log('TG OS & TG SI: not implemented, pretending not to be TG')
            blue.win32.IsTransgaming = ReturnFalse

    else:
        logmodule.general.Log('Transgaming? no')
    if blue.win32.IsTransgaming():
        logmodule.general.Log('TG OS: ' + blue.win32.TGGetOS(), logmodule.LGNOTICE)
        logmodule.general.Log('TG SI: ' + repr(blue.win32.TGGetSystemInfo()), logmodule.LGNOTICE)
    logmodule.general.Log('Process bits: ' + repr(blue.win32.GetProcessBits()), logmodule.LGNOTICE)
    logmodule.general.Log('Wow64 process? ' + ('yes' if blue.win32.IsWow64Process() else 'no'), logmodule.LGNOTICE)
    logmodule.general.Log('System info: ' + repr(blue.win32.GetSystemInfo()), logmodule.LGNOTICE)
    if blue.win32.IsWow64Process():
        logmodule.general.Log('Native system info: ' + repr(blue.win32.GetNativeSystemInfo()), logmodule.LGNOTICE)


def LogStarted(mode):
    startedat = '%s %s version %s build %s started %s %s' % (boot.appname,
     mode,
     boot.version,
     boot.build,
     blue.os.FormatUTC()[0],
     blue.os.FormatUTC()[2])
    print strx(startedat)
    logmodule.general.Log(startedat, logmodule.LGINFO)
    logmodule.general.Log(startedat, logmodule.LGNOTICE)
    logmodule.general.Log(startedat, logmodule.LGWARN)
    logmodule.general.Log(startedat, logmodule.LGERR)


try:
    blue.SetBreakpadBuildNumber(int(boot.build))
    if blue.win32.IsTransgaming():
        blue.SetCrashKeyValues(u'OS', u'Mac')
    else:
        import ctypes
        try:
            wine = ctypes.windll.ntdll.wine_get_version
            blue.SetCrashKeyValues(u'OS', u'Linux')
        except AttributeError:
            blue.SetCrashKeyValues(u'OS', u'Win')

except RuntimeError:
    pass

logdestination = prefs.ini.GetValue('networkLogging', '')
if logdestination:
    networklogport = prefs.ini.GetValue('networkLoggingPort', 12201)
    networklogThreshold = prefs.ini.GetValue('networkLoggingThreshold', 1)
    blue.EnableNetworkLogging(logdestination, networklogport, boot.role, networklogThreshold)
fileLoggingDirectory = None
fileLoggingThreshold = 0
args = blue.pyos.GetArg()
for arg in args:
    if arg.startswith('/fileLogDirectory'):
        try:
            fileLoggingDirectory = arg.split('=')[1]
        except IndexError:
            fileLoggingDirectory = None

if not fileLoggingDirectory:
    fileLoggingDirectory = prefs.ini.GetValue('fileLogDirectory', None)
    fileLoggingThreshold = int(prefs.ini.GetValue('fileLoggingThreshold', 1))
if fileLoggingDirectory:
    if not hasattr(blue, 'EnableFileLogging'):
        print 'File Logging configured but not supported'
    else:
        fileLoggingDirectory = os.path.normpath(fileLoggingDirectory)
        blue.EnableFileLogging(fileLoggingDirectory, boot.role, fileLoggingThreshold)
