#Embedded file name: eve/common/script/paperDoll\paperDollCommonFunctions.py
"""
This file contains methods used both for client and common code base of paperDoll
Must be usable on a server so it is _strictly forbidden_ to ever **import trinity** in this file.
"""
import sys
import blue
import yaml
import telemetry
import log
import stackless

def WaitForAll(iterable, condition):
    """
    Yields while any item in the iterable matches the condition.
    Condition is a function that accepts an item in the iteratable and returns a boolean value.
    """
    while any(map(condition, iterable)):
        Yield(frameNice=False)

    BeFrameNice()


def Yield(frameNice = True, ms = 15):
    """
    Encapsulates blue.synchro.Yield for various instrumentation purposes
    Include being frameNice, which means, if current frame has exceed a given amount of time,
    yield again so the tasklet doesn't spike the current frame by resuming.
    """
    try:
        if not stackless.current.is_main:
            blue.synchro.Yield()
            if frameNice:
                return BeFrameNice(ms)
        else:
            return False
    except:
        raise


def BeFrameNice(ms = 15):
    """
    Yields if frametime has exceeded the given ms and doesn't resume execution until
    we're at a time within a frame that is less than ms.
    However, the more we yield, the higher the ms value gets so the tasklet gets eventually its
    time to run, even on crapspec machines.
    """
    try:
        if not stackless.current.is_main:
            if ms < 1.0:
                ms = 1.0
            while blue.os.GetWallclockTimeNow() - blue.os.GetWallclockTime() > ms * 10000:
                blue.synchro.Yield()
                ms *= 1.02

            return True
        return False
    except:
        raise


def AddToDictList(d, key, item):
    """
    Utility method that adds item to a list the belongs to key in the dict d.
    If key currently does not exist in d, the list is created, the item added to it
    and that list is set as the value of key in d.
    """
    l = d.get(key, [])
    l.append(item)
    d[key] = l


def GetFromDictList(d, key):
    """
    Utility method that always returns a list. If key exist and the value is a list in d
    then that list is returned, otherwise, an empty list is returned.
    """
    l = d.get(key, [])
    if type(l) != list:
        return []
    return l


@telemetry.ZONE_FUNCTION
def NastyYamlLoad(yamlStr):
    """
    Backwards compatiable load function that accepts persisted yaml files from the PaperDoll since
    before it was corified and moved to /Script.    
    """
    import paperDoll as PD
    sys.modules[PD.__name__] = PD
    instance = None
    try:
        blue.statistics.EnterZone('yaml.load')
        instance = yaml.load(yamlStr, Loader=yaml.CLoader)
    except Exception:
        log.LogError('PaperDoll: Yaml parsing failed for data', yamlStr)
    finally:
        blue.statistics.LeaveZone()
        del sys.modules[PD.__name__]

    return instance


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('paperDoll', globals())
