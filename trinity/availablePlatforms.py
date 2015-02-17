#Embedded file name: trinity\availablePlatforms.py
import sys
import os
import blue
import logging
logger = logging.getLogger(__name__)
try:
    import d3dinfo
except ImportError:
    d3dinfo = None

def IsD3D9Valid():
    """
    Returns True if Direct3D9 is available.
    """
    if not d3dinfo:
        return True
    isOK = False
    d3d = d3dinfo.D3D9Info()
    try:
        d3d.InitializeD3D()
        adapterCount = d3d.GetAdapterCount()
        if adapterCount > 0:
            isOK = True
        if not d3dinfo.IsD3DXVersionAvailable(42, 9):
            isOK = False
        d3d.ShutdownD3D()
    except RuntimeError:
        pass

    return isOK


def IsD3D11Valid():
    """
    Returns True if Direct3D11 is available.
    """
    if not d3dinfo:
        return True
    isOK = False
    d3d = d3dinfo.D3D11Info()
    try:
        d3d.InitializeD3D()
        adapterCount = d3d.GetAdapterCount()
        if adapterCount > 0:
            isOK = True
        if not d3dinfo.IsD3DXVersionAvailable(42, 11):
            isOK = False
        d3d.ShutdownD3D()
    except RuntimeError:
        pass

    return isOK


def GetAvailablePlatforms():
    """
    Returns a list of available platforms for Trinity.
    """
    platforms = []
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        platforms.append('gles2')
    else:
        if IsD3D9Valid():
            platforms.append('dx9')
        if IsD3D11Valid():
            platforms.append('dx11')
        if not blue.pyos.packaged:
            platforms.append('gles2')
        platforms.append('stub')
    return platforms


def InstallSystemBinaries(fileName):
    installMsg = 'Executing %s ...' % fileName
    print installMsg
    logger.info(installMsg)
    oldDir = os.getcwdu()
    os.chdir(blue.paths.ResolvePath(u'bin:/'))
    exitStatus = os.system(fileName)
    os.chdir(oldDir)
    retString = 'Execution of ' + fileName
    if exitStatus:
        retString += ' failed (exit code %d)' % exitStatus
        logger.error(retString)
    else:
        retString += ' succeeded'
        logger.info(retString)


def InstallDirectXIfNeeded():
    if not IsD3D9Valid():
        import imp
        if imp.get_suffixes()[0][0] == '_d.pyd':
            InstallSystemBinaries('DirectXRedistForDebug.exe')
        else:
            InstallSystemBinaries('DirectXRedist.exe')
