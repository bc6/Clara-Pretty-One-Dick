#Embedded file name: talecommon\__init__.py
"""
Functions and constants shared between client and server for the tale system
"""
import blue
from carbon.common.lib.const import MIN

def CalculateDecayedInfluence(info):
    """Calculate the current influence is based upon the time since last update"""
    currentTime = blue.os.GetWallclockTime()
    return CalculateDecayedInfluenceWithTime(info.influence, info.lastUpdated, currentTime, info.decayRate, info.graceTime)


def CalculateDecayedInfluenceWithTime(influence, lastUpdated, currentTime, decayRate, graceTime):
    """Calculate the current influence is based upon the time since last update"""
    if decayRate > 0.0 and currentTime - graceTime * MIN > lastUpdated:
        timePastGrace = (currentTime - lastUpdated) / MIN - graceTime
        hourPast = max(timePastGrace / 60.0, 0.0)
        decay = decayRate * hourPast
        influence = influence - decay
    else:
        influence = influence
    if influence < 0.0001:
        influence = 0.0
    return influence


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('taleCommon', locals())
