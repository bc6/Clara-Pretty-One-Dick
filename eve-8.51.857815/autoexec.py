#Embedded file name: autoexec.py
import inifile
inifile.Init()
import blue
if blue.pyos.packaged:
    blue.paths.RegisterFileSystemBeforeLocal('Remote')
    blue.paths.RegisterFileSystemBeforeLocal('Stuff')
else:
    blue.paths.RegisterFileSystemAfterLocal('Remote')
    blue.paths.RegisterFileSystemAfterLocal('Stuff')
import __builtin__
import iocp
import _slsocket as _socket
import os
import sys
import codereloading
if iocp.UsingIOCP():
    import carbonio
    select = None
    _socket.use_carbonio(True)
    carbonio._socket = _socket
    print 'Network layer using: CarbonIO'
    if iocp.LoggingCarbonIO():
        import blue
        print 'installing CarbonIO logging callbacks'
        blue.net.InstallLoggingCallbacks()
else:
    import stacklessio
    import slselect as select
    _socket.use_carbonio(False)
    stacklessio._socket = _socket
sys.modules['_socket'] = _socket
sys.modules['select'] = select
from stacklesslib import monkeypatch
monkeypatch.patch_ssl()
if not blue.pyos.packaged:
    import debuggingutils.pydevdebugging as pydevdebugging
    __builtin__.GOPYCHARM = pydevdebugging.ConnectExeFileToDebugger
    if not blue.win32.IsTransgaming() and '/jessica' not in blue.pyos.GetArg():
        import devenv
        sys.path.append(os.path.join(devenv.SHARED_TOOLS_PYTHONDIR, 'lib27xccp'))
        import packageaddwatcher
        packageaddwatcher.guard_metapath(boot.role)
    from debuggingutils.coverageutils import start_coverage_if_enabled
    start_coverage_if_enabled(prefs, blue, boot.role)
if prefs.ini.GetValue('GOPYCHARM', False):
    GOPYCHARM()
try:
    blue.SetCrashKeyValues(u'role', unicode(boot.role))
    blue.SetCrashKeyValues(u'build', unicode(boot.build))
    orgArgs = blue.pyos.GetArg()
    args = ''
    for each in orgArgs:
        if not each.startswith('/path'):
            args += each
            args += ' '

    blue.SetCrashKeyValues(u'startupArgs', unicode(args))
    bitCount = 32
    if blue.win32.GetNativeSystemInfo().get('ProcessorArchitecture', '') == 'PROCESSOR_ARCHITECTURE_AMD64':
        bitCount = 64
    computerInfo = {'memoryPhysical': blue.os.GlobalMemoryStatus()[1][1] / 1024,
     'cpuArchitecture': blue.pyos.GetEnv().get('PROCESSOR_ARCHITECTURE', None),
     'cpuIdentifier': blue.pyos.GetEnv().get('PROCESSOR_IDENTIFIER', None),
     'cpuLevel': int(blue.pyos.GetEnv().get('PROCESSOR_LEVEL', 0)),
     'cpuRevision': int(blue.pyos.GetEnv().get('PROCESSOR_REVISION', 0), 16),
     'cpuCount': int(blue.pyos.GetEnv().get('NUMBER_OF_PROCESSORS', 0)),
     'cpuMHz': int(round(blue.os.GetCycles()[1] / 1000.0, 1)),
     'cpuBitCount': bitCount,
     'osMajorVersion': blue.os.osMajor,
     'osMinorVersion': blue.os.osMinor,
     'osBuild': blue.os.osBuild,
     'osPatch': blue.os.osPatch,
     'osPlatform': blue.os.osPlatform}
    for key, val in computerInfo.iteritems():
        blue.SetCrashKeyValues(unicode(key), unicode(val))

except RuntimeError:
    pass

if '/disableSake' not in blue.pyos.GetArg():
    codereloading.InstallSakeAutocompiler()
import inittools
tool = inittools.gettool()
if tool is None:
    __import__('autoexec_%s' % boot.role)
else:

    def run():
        inittools.run_(tool)
