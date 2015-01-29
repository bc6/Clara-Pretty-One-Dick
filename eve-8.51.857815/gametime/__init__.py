#Embedded file name: gametime\__init__.py
"""
a layer that provides drop in replacements for blue time methods that can be easily mocked and imported
"""
from carbon.common.lib.const import SEC

class BlueTimeImplementation(object):

    def __init__(self):
        import blue
        self.GetSimTime = blue.os.GetSimTime
        self.GetWallclockTime = blue.os.GetWallclockTime
        self.GetWallclockTimeNow = blue.os.GetWallclockTimeNow


class PythonTimeImplementation(object):

    def __init__(self):
        import time
        GetTime = lambda : long(time.time() * SEC)
        self.GetSimTime = GetTime
        self.GetWallclockTime = GetTime
        self.GetWallclockTimeNow = GetTime


try:
    implementation = BlueTimeImplementation()
except ImportError:
    implementation = PythonTimeImplementation()

GetSimTime = implementation.GetSimTime
GetWallclockTime = implementation.GetWallclockTime
GetWallclockTimeNow = implementation.GetWallclockTimeNow

def GetTimeDiff(a, b):
    return b - a


def GetSecondsSinceSimTime(time):
    return float(GetSimTime() - time) / SEC


def GetSecondsUntilSimTime(time):
    return -GetSecondsSinceSimTime(time)


def GetSimTimeAfterSeconds(seconds):
    return GetSimTime() + long(seconds * SEC)
