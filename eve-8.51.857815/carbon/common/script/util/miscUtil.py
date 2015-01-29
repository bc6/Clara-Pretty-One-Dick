#Embedded file name: carbon/common/script/util\miscUtil.py
"""
some common functions between server and client
"""
import blue

def GetCommonResourcePath(path):
    return path


def GetCommonResource(path):
    """ return value:  blue.ResFile() or None
    Returns a resfile matching the path from either the current respath, or the common respath """
    resourceFile = blue.ResFile()
    path = GetCommonResourcePath(path)
    result = resourceFile.Open(path)
    if result:
        return resourceFile
    else:
        return None


def CommonResourceExists(path):
    """
    Checks for file in current respath and common respath.
    Returns true if the resource exists, false otherwise. 
    """
    path = GetCommonResourcePath(path)
    return blue.paths.exists(path)


def IsInstance_BlueType(obj, name):
    return hasattr(obj, '__bluetype__') and obj.__bluetype__.find(name) >= 0


def Flatten(l, ltypes = (list, tuple)):
    """
        Remove all nesting in a list/tuple to be one flat list.
    """
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]

        i += 1

    return ltype(l)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('miscUtil', locals())
