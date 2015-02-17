#Embedded file name: inittools.py
import blue
import bluepy
import logmodule
import os
import site
import sys
import traceback

def gettool():
    args = blue.pyos.GetArg()[1:]
    for each in iter(args):
        split = each.split('=')
        if split[0].strip() == '/tools' and len(split) > 1:
            tool = split[1].strip()
            return tool


def run_(tool):
    args = blue.pyos.GetArg()[1:]
    silent = False
    if '/silent' in args:
        silent = True
    isWin32 = '32 bit' in sys.version
    join = os.path.join
    binstr = 'win32' if isWin32 else 'x64'
    carbonTools = blue.paths.ResolvePath(u'root:/../carbon/tools')
    site.addsitedir(blue.paths.ResolvePath(u'root:/../packages'))
    sys.path.append(blue.paths.ResolvePath(u'root:/..'))
    eveTools = blue.paths.ResolvePath(u'root:/tools')
    sharedTools = blue.paths.ResolvePath(u'root:/../../../../shared_tools')
    sys.path.append(join(sharedTools, 'python', 'lib2x'))
    sys.path.append(join(sharedTools, 'python', 'lib27x'))
    if isWin32:
        sys.path.append(join(sharedTools, 'python', 'lib27vc100'))
    else:
        sys.path.append(join(sharedTools, 'python', 'lib2764vc100'))
    carbonToolsLib = os.path.join(carbonTools, 'lib')
    sys.path.append(carbonToolsLib)
    sys.path.append(join(carbonToolsLib, 'bin', binstr))
    lib27 = join(sharedTools, 'libs', 'lib27')
    sys.path.append(lib27)
    sys.path.append(join(lib27, 'bin', binstr))
    sys.path.append(join(lib27, 'wx_29'))
    sys.path.append(join(lib27, 'wx_29', 'bin', binstr))
    sys.path.append(join(lib27, 'wx_29', 'VC100.SP1.bin', 'bin', binstr))

    def execIfExists(toolPath):
        path = '%s/startup/%s.py' % (toolPath, tool)
        if os.path.exists(path):
            _ExecScript(path, tool)
            return True
        return False

    if os.path.exists(tool):
        _ExecScript(tool, tool)
    elif execIfExists(eveTools):
        pass
    elif execIfExists(carbonTools):
        pass
    else:
        errStr = 'The following file was not found on your machine: /tools/startup/%s.py' % tool
        _LogAndTerm(errStr, tool)


def _LogAndTerm(errstr, tool):
    silent = '/silent' in blue.pyos.GetArg()
    if not silent:
        blue.win32.MessageBox(errstr, 'Failed to initialize %s' % tool, 272)
        bluepy.Terminate(errstr)


def _ExecScript(path, tool):
    try:
        rf = blue.classes.CreateInstance('blue.ResFile')
        rf.OpenAlways(path)
        try:
            data = rf.Read()
        finally:
            rf.Close()

        data = data.replace('\r\n', '\n')
        codeObject = compile(data, path, 'exec')
        eval(codeObject, globals())
        runFunc = globals().get('run', None)
        if runFunc is not None:
            runFunc()
    except Exception as e:
        traceback.print_exc()
        logmodule.LogException()
        _LogAndTerm(str(e), tool)
